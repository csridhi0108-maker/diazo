"""
Single aggregated dashboard endpoint. Reuses get_authorized_patient_id
so it works identically whether called by the patient themself, an
approved caregiver, or an approved doctor — the same consent check
that gates every other patient-scoped route in the app.

This does NOT recompute recommendations (that's a heavier call, left
to GET /ml/recommendations/{id} on its own) — it reads back the most
recent already-saved ones instead, keeping this endpoint fast enough
to call every time a dashboard loads.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_authorized_patient_id
from app.models.ai_plan import AIPlan
from app.models.glucose_log import GlucoseLog
from app.models.meal_log import MealLog
from app.models.activity_log import ActivityLog
from app.models.recommendation import Recommendation
from app.schemas.dashboard import DashboardOut

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/{patient_id}", response_model=DashboardOut)
def get_dashboard(
    patient_id: uuid.UUID = Depends(get_authorized_patient_id),
    db: Session = Depends(get_db),
):
    plan = db.query(AIPlan).filter(AIPlan.patient_id == patient_id).first()

    recent_glucose = (
        db.query(GlucoseLog)
        .filter(GlucoseLog.patient_id == patient_id)
        .order_by(GlucoseLog.timestamp.desc())
        .limit(10)
        .all()
    )
    recent_meals = (
        db.query(MealLog)
        .filter(MealLog.patient_id == patient_id)
        .order_by(MealLog.timestamp.desc())
        .limit(10)
        .all()
    )
    recent_activity = (
        db.query(ActivityLog)
        .filter(ActivityLog.patient_id == patient_id)
        .order_by(ActivityLog.date.desc())
        .limit(7)
        .all()
    )
    recommendations = (
        db.query(Recommendation)
        .filter(Recommendation.patient_id == patient_id)
        .order_by(Recommendation.created_at.desc())
        .limit(5)
        .all()
    )

    return DashboardOut(
        patient_id=patient_id,
        plan=plan,
        recent_glucose_logs=recent_glucose,
        recent_meal_logs=recent_meals,
        recent_activity_logs=recent_activity,
        recommendations=recommendations,
    )