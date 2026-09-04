"""
BMI and BMR calculations — pure functions, no DB/side effects, so
they're easy to test and reuse across plan_service.py and (later)
risk_model.py.
"""


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Standard BMI formula: weight(kg) / height(m)^2"""
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def calculate_bmr(weight_kg: float, height_cm: float, age: int, is_male: bool | None = None) -> float:
    """
    Mifflin-St Jeor equation — the most widely used, clinically
    validated BMR formula. `is_male` should always be provided now
    that onboarding collects sex; the None branch is kept only as a
    safe fallback (average of the male/female constants) in case this
    function is ever called without it.
    """
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)

    if is_male is True:
        return base + 5
    elif is_male is False:
        return base - 161
    else:
        # Fallback only — should not normally be hit now that sex is
        # a required onboarding field.
        return base - 78