"""
Calorie target calculation — combines BMR with activity level (TDEE)
and applies diabetes-aware adjustments. Used once at onboarding to
set the initial daily_calorie_target in ai_plans.
"""

from app.models.patient_profile import ActivityLevel, DiabetesType
from app.utils.bmi import calculate_bmr, calculate_bmi

# Standard activity multipliers (used to go from BMR -> TDEE)
ACTIVITY_MULTIPLIERS = {
    ActivityLevel.sedentary: 1.2,
    ActivityLevel.moderate: 1.55,
    ActivityLevel.active: 1.725,
}


def calculate_daily_calorie_target(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str,  # "male" or "female"
    activity_level: ActivityLevel,
    diabetes_type: DiabetesType,
) -> float:
    """
    TDEE (Total Daily Energy Expenditure) = BMR * activity multiplier.
    A mild deficit is applied only when BMI indicates overweight,
    since unnecessary calorie restriction isn't appropriate for
    every diabetic patient (e.g. Type 1 patients are often not
    overweight) — this ties the deficit to an actual measured
    indicator (BMI) rather than assuming from diabetes_type alone.
    """
    bmr = calculate_bmr(weight_kg, height_cm, age, is_male=(sex == "male"))
    tdee = bmr * ACTIVITY_MULTIPLIERS[activity_level]

    bmi = calculate_bmi(weight_kg, height_cm)
    if bmi >= 25:  # overweight threshold (standard WHO cutoff)
        tdee -= 300  # mild, sustainable deficit — not aggressive restriction

    return round(tdee)


def calculate_target_weight(weight_kg: float, height_cm: float) -> float | None:
    """
    Returns a target weight only if BMI indicates overweight (>= 25);
    otherwise None, meaning "maintain current weight" — the frontend
    should treat None as no weight-loss goal, not an error.
    """
    bmi = calculate_bmi(weight_kg, height_cm)
    if bmi < 25:
        return None

    height_m = height_cm / 100
    # Target the top of the "normal" BMI range (24.9) rather than an
    # aggressive ideal — a realistic, achievable target.
    target = 24.9 * (height_m ** 2)
    return round(target, 1)