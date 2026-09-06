"""
Meal-scale nutrition logic: turns (food, weight_g) into actual grams of
carbs/protein/calories, and decides whether logging that portion would
keep the patient WITHIN_TARGET or push them ABOVE_TARGET for the day.

Deliberately never says "safe" or "dangerous" — this is a configured-
target comparison against the patient's existing AI plan, not a
medical judgment. See calculate_macro_targets() in utils/macros.py for
how that daily target itself is derived.
"""

import datetime
import uuid

from sqlalchemy.orm import Session

from app.models.ai_plan import AIPlan
from app.models.food_item import FoodItem
from app.models.meal_log import MealLog


def calculate_nutrition(food: FoodItem, weight_g: float) -> dict:
    """
    Scales a food's per-100g nutrition to the actual measured weight.
    Rounded to 1 decimal place — these are estimates from a reference
    table, not lab measurements, so extra precision would be false
    confidence.
    """
    factor = weight_g / 100.0
    return {
        "carbs_g": round(food.carbs_g_per_100g * factor, 1),
        "protein_g": round(food.protein_g_per_100g * factor, 1),
        "calories": round(food.calories_per_100g * factor, 1) if food.calories_per_100g is not None else None,
    }


def get_todays_logged_carbs(db: Session, patient_id: uuid.UUID) -> float:
    """
    Sums estimated_carbs across every meal already logged today for
    this patient (local-server-time day boundary — fine for a
    prototype; a timezone-aware boundary would be the production fix).
    Used to compare against the *remaining* daily carb budget rather
    than a flat per-meal slice, since a patient's earlier meals count
    against today's target too.
    """
    start_of_day = datetime.datetime.combine(datetime.date.today(), datetime.time.min)

    todays_meals = (
        db.query(MealLog)
        .filter(MealLog.patient_id == patient_id, MealLog.timestamp >= start_of_day)
        .all()
    )
    return sum(meal.estimated_carbs or 0 for meal in todays_meals)


def evaluate_target_status(db: Session, patient_id: uuid.UUID, new_meal_carbs: float) -> str | None:
    """
    Returns "WITHIN_TARGET" or "ABOVE_TARGET" for this meal's carbs
    added on top of everything already logged today, compared against
    the patient's daily carb target from their AI plan.

    Returns None if the patient has no AI plan yet (e.g. onboarding
    incomplete) — callers should treat that as "no status available"
    rather than defaulting to either target state.
    """
    plan = db.query(AIPlan).filter(AIPlan.patient_id == patient_id).first()
    if plan is None:
        return None

    daily_carb_target = plan.macro_targets.get("carbs_g")
    if daily_carb_target is None:
        return None

    already_logged = get_todays_logged_carbs(db, patient_id)
    projected_total = already_logged + new_meal_carbs

    return "WITHIN_TARGET" if projected_total <= daily_carb_target else "ABOVE_TARGET"
