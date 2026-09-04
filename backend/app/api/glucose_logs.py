"""Glucose log endpoints for tracking patient blood sugar readings."""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.models.glucose_log import GlucoseLog

router = APIRouter(prefix="/api/v1/glucose-logs", tags=["glucose-logs"])


class GlucoseLogCreate(BaseModel):
    value: float = Field(..., gt=0, le=600, description="Glucose value in mg/dL")
    context_tag: Optional[str] = Field(None, description="Context: fasting, before_meal, after_meal, bedtime, random")
    timestamp: Optional[datetime] = None


class GlucoseLogOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    value: float
    context_tag: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[GlucoseLogOut])
async def get_my_glucose_logs(
    current_user: User = Depends(require_role(UserRole.patient)),
    db: Session = Depends(get_db)
):
    """Get all glucose logs for the current patient, ordered by timestamp descending."""
    logs = (
        db.query(GlucoseLog)
        .filter(GlucoseLog.patient_id == current_user.id)
        .order_by(GlucoseLog.timestamp.desc())
        .all()
    )
    return logs


@router.post("", response_model=GlucoseLogOut, status_code=status.HTTP_201_CREATED)
async def create_glucose_log(
    payload: GlucoseLogCreate,
    current_user: User = Depends(require_role(UserRole.patient)),
    db: Session = Depends(get_db)
):
    """Create a new glucose log entry for the current patient."""
    new_log = GlucoseLog(
        patient_id=current_user.id,
        value=payload.value,
        context_tag=payload.context_tag,
        timestamp=payload.timestamp or datetime.utcnow()
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log