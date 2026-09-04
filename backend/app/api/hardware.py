"""Hardware-facing endpoints. These do not use browser JWTs."""

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.ws_manager import manager
from app.models.meal_weight_reading import MealWeightReading
from app.models.scale_status import ScaleStatus
from app.models.user import User, UserRole
from app.schemas.hardware import MealWeightReadingIn, MealWeightReadingOut, ScaleStatusOut

router = APIRouter(prefix="/api/v1/hardware", tags=["hardware"])


def verify_device_key(x_device_key: str | None = Header(default=None)):
    """Reject unauthenticated device traffic before it reaches patient data."""
    expected_key = settings.ESP32_DEVICE_API_KEY
    if not expected_key or not x_device_key or not hmac.compare_digest(x_device_key, expected_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device credentials")


@router.post(
    "/meal-weight-readings",
    response_model=MealWeightReadingOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_device_key)],
)
async def ingest_meal_weight_reading(payload: MealWeightReadingIn, db: Session = Depends(get_db)):
    """
    Receive a reading from an ESP32 meal scale and immediately relay it to the
    patient's browser over the existing authenticated notification WebSocket.

    The shared device key belongs only on the ESP32 and backend configuration,
    never in browser code or a public repository.
    """
    patient = db.query(User).filter(User.id == payload.patient_id).first()
    if patient is None or patient.role != UserRole.patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    reading = MealWeightReading(**payload.model_dump())
    db.add(reading)
    # A new measurement must not keep showing the result of the previous meal.
    device_status = db.get(ScaleStatus, payload.device_id)
    if device_status is None:
        db.add(ScaleStatus(device_id=payload.device_id, patient_id=payload.patient_id, status="PENDING"))
    else:
        device_status.patient_id = payload.patient_id
        device_status.status = "PENDING"
    db.commit()
    db.refresh(reading)

    await manager.push_to_user(
        payload.patient_id,
        {
            "type": "meal_weight_reading",
            "reading_id": str(reading.id),
            "device_id": reading.device_id,
            "weight_g": reading.weight_g,
            "received_at": reading.received_at.isoformat(),
        },
    )
    return reading


@router.get(
    "/scale-status/{device_id}",
    response_model=ScaleStatusOut,
    dependencies=[Depends(verify_device_key)],
)
def get_scale_status(device_id: str, db: Session = Depends(get_db)):
    """Return the latest LED command for an ESP32 scale.

    ``PENDING`` means a weight was received but the patient has not yet
    selected/logged a food, so neither LED should be lit.
    """
    device_status = db.get(ScaleStatus, device_id)
    if device_status is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scale not found")
    return device_status
