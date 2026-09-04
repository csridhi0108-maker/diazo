"""
Plan retrieval endpoint. Plan generation itself happens automatically
in api/patients.py right after onboarding — this route is read-only
and also usable by an approved caregiver/doctor to view the plan.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_authorized_patient_id
from app.models.ai_plan import AIPlan
from app.schemas.plan import AIPlanOut

router = APIRouter(prefix="/api/v1/plans", tags=["plans"])


@router.get("/{patient_id}", response_model=AIPlanOut)
def get_plan(
    patient_id: uuid.UUID = Depends(get_authorized_patient_id),
    db: Session = Depends(get_db),
):
    plan = db.query(AIPlan).filter(AIPlan.patient_id == patient_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No plan found — complete onboarding first (plans are generated automatically).",
        )
    return plan