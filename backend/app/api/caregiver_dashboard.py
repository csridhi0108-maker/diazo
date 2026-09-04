"""
Caregiver dashboard endpoints — allows approved caregivers to view
their patients' health data in a read-only manner.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.models.caregiver_link import CareLink, LinkStatus
from app.models.glucose_log import GlucoseLog
from app.models.meal_log import MealLog
from app.models.activity_log import ActivityLog

router = APIRouter(prefix="/api/v1/caregiver", tags=["caregiver-dashboard"])


@router.get("/patient/{patient_id}/dashboard")
def get_patient_dashboard(
    patient_id: str,
    current_user: User = Depends(require_role(UserRole.caregiver, UserRole.doctor)),
    db: Session = Depends(get_db),
):
    """
    Fetch a patient's dashboard data for an approved caregiver.
    Only returns data if the caregiver has an approved link to this patient.
    """
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid patient ID")

    # Verify the caregiver has an approved link to this patient
    link = db.query(CareLink).filter(
        CareLink.linked_user_id == current_user.id,
        CareLink.patient_id == patient_uuid,
        CareLink.status == LinkStatus.approved,
    ).first()

    if not link:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view this patient's data",
        )

    # Fetch patient
    patient = db.query(User).filter(User.id == patient_uuid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Fetch patient profile
    profile = patient.patient_profile
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    # Safely extract macro targets (handles both dict and object types)
    macros = getattr(profile, 'macro_targets', None)
    
    if isinstance(macros, dict):
        carbs = macros.get('carbs_g', 0)
        protein = macros.get('protein_g', 0)
        fat = macros.get('fat_g', 0)
    elif macros is not None:
        carbs = getattr(macros, 'carbs_g', 0)
        protein = getattr(macros, 'protein_g', 0)
        fat = getattr(macros, 'fat_g', 0)
    else:
        # Fallback to direct columns if they exist
        carbs = getattr(profile, 'carbs_g', 0)
        protein = getattr(profile, 'protein_g', 0)
        fat = getattr(profile, 'fat_g', 0)

    # Fetch recent logs (last 10 of each)
    # NOTE: Using patient_id (not user_id) as per the actual model definitions
    glucose_logs = (
        db.query(GlucoseLog)
        .filter(GlucoseLog.patient_id == patient_uuid)  # FIXED: patient_id
        .order_by(GlucoseLog.timestamp.desc())
        .limit(10)
        .all()
    )
    glucose_logs.reverse()  # Chronological order

    meal_logs = (
        db.query(MealLog)
        .filter(MealLog.patient_id == patient_uuid)  # FIXED: patient_id
        .order_by(MealLog.timestamp.desc())
        .limit(10)
        .all()
    )

    activity_logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.patient_id == patient_uuid)  # FIXED: patient_id
        .order_by(ActivityLog.date.desc())
        .limit(10)
        .all()
    )

    # Build dashboard response
    return {
        "patient_id": str(patient.id),
        "patient_name": patient.full_name,
        "plan": {
            "daily_calorie_target": getattr(profile, 'daily_calorie_target', 2000),
            "macro_targets": {
                "carbs_g": carbs,
                "protein_g": protein,
                "fat_g": fat,
            },
            "daily_step_goal": getattr(profile, 'daily_step_goal', 10000),
        },
        "recent_glucose_logs": [
            {
                "id": str(log.id),
                "value": log.value,
                "timestamp": log.timestamp.isoformat(),
                "unit": getattr(log, 'unit', 'mg/dL'),
            }
            for log in glucose_logs
        ],
        "recent_meal_logs": [
            {
                "id": str(log.id),
                "meal_type": log.meal_type,
                "logged_at": log.timestamp.isoformat(),  # FIXED: MealLog uses timestamp
                "estimated_carbs": getattr(log, 'estimated_carbs', 0),
            }
            for log in meal_logs
        ],
        "recent_activity_logs": [
            {
                "id": str(log.id),
                "date": log.date.isoformat() if hasattr(log.date, 'isoformat') else str(log.date),
                "steps": getattr(log, 'steps', 0),
            }
            for log in activity_logs
        ],
        "recommendations": [],
    }