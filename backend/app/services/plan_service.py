"""
Orchestrates the pure calculation functions in utils/ into an actual
AIPlan row. This is the only place that touches the DB for plan
generation — utils/ stays pure/testable, this handles persistence.
"""

from sqlalchemy.orm import Session

from app.models.ai_plan import AIPlan
from app.models.patient_profile import PatientProfile
from app.utils.calories import calculate_daily_calorie_target, calculate_target_weight
from app.utils.macros import calculate_macro_targets, calculate_step_goal


def generate_plan_for_patient(profile: PatientProfile, db: Session) -> AIPlan:
    """
    Computes a fresh plan from the patient's current profile and
    upserts it into ai_plans. Called once right after onboarding, and
    can be re-called later (e.g. after a weight update) to recalculate.
    """
    daily_calories = calculate_daily_calorie_target(
        weight_kg=profile.weight_kg,
        height_cm=profile.height_cm,
        age=profile.age,
        sex=profile.sex.value,
        activity_level=profile.activity_level,
        diabetes_type=profile.diabetes_type,
    )
    target_weight = calculate_target_weight(profile.weight_kg, profile.height_cm)
    macros = calculate_macro_targets(daily_calories, profile.diabetes_type)
    step_goal = calculate_step_goal(profile.activity_level)

    existing_plan = (
        db.query(AIPlan).filter(AIPlan.patient_id == profile.user_id).first()
    )

    if existing_plan:
        existing_plan.target_weight_kg = target_weight
        existing_plan.daily_calorie_target = daily_calories
        existing_plan.macro_targets = macros
        existing_plan.daily_step_goal = step_goal
        plan = existing_plan
    else:
        plan = AIPlan(
            patient_id=profile.user_id,
            target_weight_kg=target_weight,
            daily_calorie_target=daily_calories,
            macro_targets=macros,
            daily_step_goal=step_goal,
        )
        db.add(plan)

    db.commit()
    db.refresh(plan)
    return plan