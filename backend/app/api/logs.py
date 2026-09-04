"""
Logging endpoints: meals, glucose, activity. Every route here is
patient-scoped via get_authorized_patient_id, which means a patient
can log their own data, and a caregiver/doctor can only ever READ
(never write) another patient's logs — enforced by which routes even
accept a patient_id other than "me".
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_authorized_patient_id
from app.models.user import User, UserRole
from app.models.meal_log import MealLog
from app.models.glucose_log import GlucoseLog
from app.models.activity_log import ActivityLog
from app.models.food_item import FoodItem
from app.models.scale_status import ScaleStatus
from app.schemas.log import (
    MealLogCreate, MealLogOut,
    GlucoseLogCreate, GlucoseLogOut,
    ActivityLogUpsert, ActivityLogOut,
)
from app.models.notification import NotificationType
from app.services.notification_service import notify_linked_caregivers
from app.services.nutrition_service import calculate_nutrition, evaluate_target_status

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


# ---------- Meal logs ----------

@router.post("/meals", response_model=MealLogOut, status_code=status.HTTP_201_CREATED)
async def create_meal_log(
    payload: MealLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Only patients log their own meals — writes are never delegated
    # to a caregiver/doctor, matching the read-only access rule.
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="Only patients can log meals")

    data = payload.model_dump()
    food_id = data.pop("food_id")
    weight_g = data.pop("weight_g")
    scale_device_id = data.pop("scale_device_id")

    if food_id is not None and weight_g is not None:
        # Meal-scale flow: recompute from the reference table rather
        # than trusting whatever the client sent for carbs/calories —
        # the frontend only ever showed a preview, this is the
        # authoritative calculation.
        food = db.query(FoodItem).filter(FoodItem.id == food_id).first()
        if food is None:
            raise HTTPException(status_code=404, detail="Food not found")

        nutrition = calculate_nutrition(food, weight_g)
        data["estimated_carbs"] = nutrition["carbs_g"]
        data["estimated_protein"] = nutrition["protein_g"]
        data["estimated_calories"] = nutrition["calories"]
        data["nutrition_status"] = evaluate_target_status(
            db, current_user.id, nutrition["carbs_g"], nutrition["protein_g"]
        )

        # Keep a human-readable record in food_items too, same shape
        # the frontend already renders in meal history.
        data["food_items"] = [{
            "name": food.name,
            "measured_weight_g": weight_g,
            "carbs_g": nutrition["carbs_g"],
            "protein_g": nutrition["protein_g"],
        }]

    log = MealLog(patient_id=current_user.id, scale_food_id=food_id, **data)
    db.add(log)

    if scale_device_id:
        # Store a device-specific command so a scale never sees another
        # patient's result. Unknown targets intentionally remain PENDING.
        led_status = {
            "WITHIN_TARGET": "GREEN",
            "ABOVE_TARGET": "RED",
        }.get(log.nutrition_status, "PENDING")
        device_status = db.get(ScaleStatus, scale_device_id)
        if device_status is None:
            db.add(ScaleStatus(device_id=scale_device_id, patient_id=current_user.id, status=led_status))
        elif device_status.patient_id == current_user.id:
            device_status.status = led_status
        else:
            raise HTTPException(status_code=403, detail="Scale belongs to another patient")
    db.commit()
    db.refresh(log)

    # Notify linked caregivers/doctors — the "Mom just had lunch ✅"
    # reassurance feature from the original spec.
    await notify_linked_caregivers(
        db, current_user.id, NotificationType.meal_logged,
        f"Patient logged a {log.meal_type}.",
    )

    return log


@router.get("/meals/{patient_id}", response_model=list[MealLogOut])
def list_meal_logs(
    patient_id: uuid.UUID = Depends(get_authorized_patient_id),
    db: Session = Depends(get_db),
):
    # get_authorized_patient_id already confirmed the caller is either
    # this patient themself or an approved caregiver/doctor — no
    # further permission check needed here.
    return (
        db.query(MealLog)
        .filter(MealLog.patient_id == patient_id)
        .order_by(MealLog.timestamp.desc())
        .all()
    )


# ---------- Glucose logs ----------

@router.post("/glucose", response_model=GlucoseLogOut, status_code=status.HTTP_201_CREATED)
def create_glucose_log(
    payload: GlucoseLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="Only patients can log glucose readings")

    log = GlucoseLog(patient_id=current_user.id, **payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/glucose/{patient_id}", response_model=list[GlucoseLogOut])
def list_glucose_logs(
    patient_id: uuid.UUID = Depends(get_authorized_patient_id),
    db: Session = Depends(get_db),
):
    return (
        db.query(GlucoseLog)
        .filter(GlucoseLog.patient_id == patient_id)
        .order_by(GlucoseLog.timestamp.desc())
        .all()
    )


# ---------- Activity logs ----------

@router.put("/activity", response_model=ActivityLogOut)
def upsert_activity_log(
    payload: ActivityLogUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    PUT (not POST) because activity is one row per patient per day —
    calling this again for today updates the existing row (e.g. step
    count refreshed through the day) rather than creating a duplicate.
    This is what the UniqueConstraint on the model enforces at the DB
    level; this upsert logic is what makes that work smoothly instead
    of throwing a constraint-violation error on the second call.
    """
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="Only patients can log activity")

    existing = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.patient_id == current_user.id,
            ActivityLog.date == payload.date,
        )
        .first()
    )

    if existing:
        existing.steps = payload.steps
        existing.calories_burned = payload.calories_burned
        db.commit()
        db.refresh(existing)
        return existing

    log = ActivityLog(patient_id=current_user.id, **payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/activity/{patient_id}", response_model=list[ActivityLogOut])
def list_activity_logs(
    patient_id: uuid.UUID = Depends(get_authorized_patient_id),
    db: Session = Depends(get_db),
):
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.patient_id == patient_id)
        .order_by(ActivityLog.date.desc())
        .all()
    )
