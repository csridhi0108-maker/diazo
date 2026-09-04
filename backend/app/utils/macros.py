"""
Macro (carb/protein/fat) split and step goal calculation. Split ratios
are diabetes-aware: lower-carb / higher-protein for diagnosed patients
is standard dietary guidance for glucose management, not an arbitrary
choice — this is where "AI plan" reflects real clinical dietary
patterns rather than a generic macro split.
"""

from app.models.patient_profile import DiabetesType, ActivityLevel


def calculate_macro_targets(daily_calories: float, diabetes_type: DiabetesType) -> dict:
    """
    Returns target grams of carbs/protein/fat for the day.
    1g carbs = 4 kcal, 1g protein = 4 kcal, 1g fat = 9 kcal.
    """
    if diabetes_type in (DiabetesType.type1, DiabetesType.type2, DiabetesType.prediabetic):
        # Lower-carb split — standard diabetes dietary guidance to
        # reduce glucose spikes: ~40% carbs / 30% protein / 30% fat
        carb_pct, protein_pct, fat_pct = 0.40, 0.30, 0.30
    else:
        # No diagnosis — standard balanced split, no restriction needed
        carb_pct, protein_pct, fat_pct = 0.50, 0.25, 0.25

    return {
        "carbs_g": round((daily_calories * carb_pct) / 4),
        "protein_g": round((daily_calories * protein_pct) / 4),
        "fat_g": round((daily_calories * fat_pct) / 9),
    }


def calculate_step_goal(activity_level: ActivityLevel) -> int:
    """
    Baseline daily step goal by current activity level — starts
    patients slightly above their current baseline rather than
    jumping straight to a generic 10,000, which is more realistic
    and achievable for a sedentary patient.
    """
    return {
        ActivityLevel.sedentary: 6000,
        ActivityLevel.moderate: 8000,
        ActivityLevel.active: 10000,
    }[activity_level]