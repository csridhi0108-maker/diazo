"""
Synthetic data generator for DIAZO.

Creates fully separate "synthetic" patient accounts (email pattern:
synthetic_patient_N@diazo.demo) with realistic, deliberately-correlated
meal/glucose/activity history — so the analytics/correlation layer has
real patterns to detect during development and demos.

Because synthetic patients are ordinary user accounts (not a special
table or flag), they:
  - go through the exact same code paths as real users (no special-
    casing needed in the analytics/ML layer)
  - can be wiped at any time with one query, without touching real
    user data:
      DELETE FROM users WHERE email LIKE 'synthetic_%@diazo.demo';
    (cascades to patient_profiles, logs, ai_plans, etc. via FKs)

Usage:
    python scripts/synthetic_data_generator.py --patients 5 --days 30
    python scripts/synthetic_data_generator.py --wipe   # removes all synthetic data
"""

import argparse
import random
import uuid
from datetime import datetime, timedelta, date

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.patient_profile import PatientProfile, DiabetesType, ActivityLevel, Sex
from app.models.meal_log import MealLog
from app.models.glucose_log import GlucoseLog
from app.models.activity_log import ActivityLog
from app.services.plan_service import generate_plan_for_patient

SYNTHETIC_EMAIL_DOMAIN = "diazo.demo"
SYNTHETIC_PASSWORD = "synthetic-not-a-real-login"  # never used to actually log in

MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"]

# (name, typical carbs in grams) — enough variety to produce a real
# spread of carb levels across meals, which is what the correlation
# model needs to detect a pattern at all.
FOOD_OPTIONS = [
    ("oats + fruit", 45), ("eggs + toast", 35), ("rice + dal", 70),
    ("chapati + sabzi", 50), ("salad + grilled chicken", 20),
    ("pasta", 80), ("biryani", 90), ("fruit bowl", 30),
    ("nuts + yogurt", 15), ("sandwich", 40), ("soup + bread", 35),
]


def wipe_synthetic_data(db):
    deleted = (
        db.query(User)
        .filter(User.email.like(f"synthetic_%@{SYNTHETIC_EMAIL_DOMAIN}"))
        .delete(synchronize_session=False)
    )
    db.commit()
    print(f"Wiped {deleted} synthetic user(s) and all their cascaded data.")


def create_synthetic_patient(db, index: int) -> User:
    email = f"synthetic_patient_{index}@{SYNTHETIC_EMAIL_DOMAIN}"

    user = User(
        email=email,
        password_hash=hash_password(SYNTHETIC_PASSWORD),
        role=UserRole.patient,
        preferred_language="en",
    )
    db.add(user)
    db.flush()  # get user.id without a full commit yet

    profile = PatientProfile(
        user_id=user.id,
        diabetes_type=random.choice([DiabetesType.type2, DiabetesType.prediabetic]),
        diagnosis_duration_months=random.randint(1, 60),
        sex=random.choice([Sex.male, Sex.female]),
        age=random.randint(30, 70),
        height_cm=round(random.uniform(155, 185), 1),
        weight_kg=round(random.uniform(60, 100), 1),
        activity_level=random.choice(list(ActivityLevel)),
        medications="metformin",
        dietary_prefs=None,
        family_history=random.choice([True, False]),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    generate_plan_for_patient(profile, db)

    return user


def generate_logs_for_patient(db, patient_id: uuid.UUID, days: int):
    """
    The key part: glucose readings are generated AS A FUNCTION OF the
    meal that preceded them, with realistic noise — this is what
    makes the correlation model find a genuine (synthetic-but-true)
    pattern later, rather than random unconnected numbers.
    """
    today = date.today()

    for day_offset in range(days):
        log_date = today - timedelta(days=day_offset)

        # Activity — one row per day, per the model's design
        steps = random.randint(2000, 12000)
        activity = ActivityLog(
            patient_id=patient_id,
            date=log_date,
            steps=steps,
            calories_burned=round(steps * 0.04, 1),
        )
        db.add(activity)

        for meal_type in MEAL_TYPES:
            food_name, base_carbs = random.choice(FOOD_OPTIONS)
            carbs = base_carbs + random.randint(-10, 10)
            carbs = max(carbs, 5)
            calories = carbs * 4 + random.randint(50, 200)

            meal_time = datetime.combine(
                log_date, datetime.min.time()
            ) + timedelta(hours=random.choice([8, 13, 19, 16]), minutes=random.randint(0, 59))

            meal = MealLog(
                patient_id=patient_id,
                timestamp=meal_time,
                meal_type=meal_type,
                food_items=[{"name": food_name, "portion": "1 serving"}],
                estimated_carbs=carbs,
                estimated_calories=calories,
            )
            db.add(meal)

            # The actual correlation: glucose rise scales with carbs,
            # with mild random noise. Higher activity that day slightly
            # blunts the spike (also a real physiological pattern).
            baseline = 100
            carb_effect = carbs * 0.6
            activity_offset = -0.002 * steps  # more steps -> lower spike
            noise = random.uniform(-15, 15)
            glucose_value = round(baseline + carb_effect + activity_offset + noise, 1)
            glucose_value = max(glucose_value, 70)  # keep it physiologically sane

            glucose_time = meal_time + timedelta(hours=2)
            glucose = GlucoseLog(
                patient_id=patient_id,
                timestamp=glucose_time,
                value=glucose_value,
                context_tag=f"after_{meal_type}",
            )
            db.add(glucose)

    db.commit()


def main():
    parser = argparse.ArgumentParser(description="DIAZO synthetic data generator")
    parser.add_argument("--patients", type=int, default=5, help="Number of synthetic patients to create")
    parser.add_argument("--days", type=int, default=30, help="Days of history to generate per patient")
    parser.add_argument("--wipe", action="store_true", help="Delete all synthetic data instead of generating")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.wipe:
            wipe_synthetic_data(db)
            return

        print(f"Generating {args.patients} synthetic patients with {args.days} days of history each...")
        for i in range(1, args.patients + 1):
            user = create_synthetic_patient(db, i)
            generate_logs_for_patient(db, user.id, args.days)
            print(f"  Created {user.email}")

        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()