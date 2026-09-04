"""
Analytics Engine — deterministic, pandas-based pattern detection.

IMPORTANT ARCHITECTURE RULE:

This file performs calculations only.

It does NOT:
- call the LLM
- generate natural-language recommendations
- diagnose medical conditions
- invent medical conclusions

The output of this file is structured data that can safely be passed
to the Explain Layer and then to the LLM phrasing layer.

Current analyses:
    1. Carb / glucose correlation
    2. Logging adherence
    3. Activity / glucose impact
    4. Specific glucose spike events
"""

import uuid
from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy.orm import Session

from app.models.meal_log import MealLog
from app.models.glucose_log import GlucoseLog
from app.models.activity_log import ActivityLog


# =========================================================
# DATA LOADING
# =========================================================

def _load_logs_as_dataframes(
    db: Session,
    patient_id: uuid.UUID,
    days: int = 30,
):
    """
    Load recent patient data into pandas DataFrames.

    All analytics functions use this single loader so that:

    - patient filtering is consistent
    - date filtering is consistent
    - timezone-aware timestamps are used
    - missing numeric values are handled safely
    """

    since = (
        datetime.now(timezone.utc)
        - timedelta(days=days)
    )

    meals = (
        db.query(MealLog)
        .filter(
            MealLog.patient_id == patient_id,
            MealLog.timestamp >= since,
        )
        .all()
    )

    glucose = (
        db.query(GlucoseLog)
        .filter(
            GlucoseLog.patient_id == patient_id,
            GlucoseLog.timestamp >= since,
        )
        .all()
    )

    activities = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.patient_id == patient_id,
            ActivityLog.date >= since.date(),
        )
        .all()
    )

    # -----------------------------------------------------
    # Meals
    # -----------------------------------------------------

    meals_df = pd.DataFrame(
        [
            {
                "timestamp": meal.timestamp,
                "meal_type": meal.meal_type,
                "carbs": meal.estimated_carbs or 0,
            }
            for meal in meals
        ]
    )

    # -----------------------------------------------------
    # Glucose
    # -----------------------------------------------------

    glucose_df = pd.DataFrame(
        [
            {
                "timestamp": reading.timestamp,
                "value": reading.value,
                "context_tag": reading.context_tag,
            }
            for reading in glucose
        ]
    )

    # -----------------------------------------------------
    # Activity
    # -----------------------------------------------------

    activity_df = pd.DataFrame(
        [
            {
                "date": activity.date,
                "steps": activity.steps or 0,
            }
            for activity in activities
        ]
    )

    # -----------------------------------------------------
    # Explicitly convert timestamps where possible.
    #
    # This prevents pandas from unexpectedly treating timestamps
    # as strings when the database contains no rows / mixed data.
    # -----------------------------------------------------

    if not meals_df.empty:
        meals_df["timestamp"] = pd.to_datetime(
            meals_df["timestamp"],
            utc=True,
        )

    if not glucose_df.empty:
        glucose_df["timestamp"] = pd.to_datetime(
            glucose_df["timestamp"],
            utc=True,
        )

    return (
        meals_df,
        glucose_df,
        activity_df,
    )


# =========================================================
# 1. CARB / GLUCOSE CORRELATION
# =========================================================

def analyze_carb_glucose_correlation(
    db: Session,
    patient_id: uuid.UUID,
    days: int = 30,
) -> dict | None:
    """
    Analyze the relationship between recently logged carbohydrate
    intake and glucose readings.

    Matching strategy:

    1. Look for meals occurring within the previous 6 hours.
    2. If none exist, fall back to a same-day meal.
    3. Associate the closest meal with the glucose reading.
    4. Split matched meals around the median carbohydrate amount.
    5. Compare average glucose between the two groups.

    This produces a statistical pattern, not a medical diagnosis.
    """

    (
        meals_df,
        glucose_df,
        _,
    ) = _load_logs_as_dataframes(
        db,
        patient_id,
        days,
    )

    # Need enough data to make a basic comparison.
    if len(meals_df) < 3 or len(glucose_df) < 3:
        return None

    matched_pairs = []

    # -----------------------------------------------------
    # Match glucose readings with meals
    # -----------------------------------------------------

    for _, glucose_row in glucose_df.iterrows():

        glucose_timestamp = glucose_row["timestamp"]

        window_start = (
            glucose_timestamp
            - timedelta(hours=6)
        )

        candidate_meals = meals_df[
            (
                meals_df["timestamp"]
                >= window_start
            )
            &
            (
                meals_df["timestamp"]
                <= glucose_timestamp
            )
        ]

        # -------------------------------------------------
        # Same-day fallback
        # -------------------------------------------------

        if candidate_meals.empty:

            glucose_date = (
                glucose_timestamp.date()
            )

            same_day_meals = meals_df[
                meals_df["timestamp"].dt.date
                == glucose_date
            ]

            if not same_day_meals.empty:
                candidate_meals = same_day_meals

        if candidate_meals.empty:
            continue

        # -------------------------------------------------
        # Select closest meal
        # -------------------------------------------------

        time_difference = (
            glucose_timestamp
            - candidate_meals["timestamp"]
        ).abs()

        closest_meal = candidate_meals.iloc[
            time_difference.argmin()
        ]

        matched_pairs.append(
            {
                "carbs": float(
                    closest_meal["carbs"]
                ),
                "glucose": float(
                    glucose_row["value"]
                ),
            }
        )

    # Need at least two matched observations.
    if len(matched_pairs) < 2:
        return None

    pairs_df = pd.DataFrame(
        matched_pairs
    )

    # -----------------------------------------------------
    # Median carbohydrate threshold
    # -----------------------------------------------------

    median_carbs = (
        pairs_df["carbs"].median()
    )

    high_carb = pairs_df[
        pairs_df["carbs"] > median_carbs
    ]

    low_carb = pairs_df[
        pairs_df["carbs"] <= median_carbs
    ]

    if high_carb.empty or low_carb.empty:
        return None

    # -----------------------------------------------------
    # Group averages
    # -----------------------------------------------------

    high_carb_avg_glucose = float(
        round(
            high_carb["glucose"].mean(),
            1,
        )
    )

    low_carb_avg_glucose = float(
        round(
            low_carb["glucose"].mean(),
            1,
        )
    )

    difference = float(
        round(
            high_carb_avg_glucose
            - low_carb_avg_glucose,
            1,
        )
    )

    sample_size = len(
        matched_pairs
    )

    confidence_score = min(
        1.0,
        sample_size / 20.0,
    )

    return {
        "high_carb_avg_glucose":
            high_carb_avg_glucose,

        "low_carb_avg_glucose":
            low_carb_avg_glucose,

        "glucose_difference":
            difference,

        "high_carb_threshold_g":
            float(
                round(
                    median_carbs,
                    1,
                )
            ),

        "sample_size":
            sample_size,

        "significant":
            bool(
                abs(difference) >= 10
            ),

        "confidence_score":
            confidence_score,
    }


# =========================================================
# 2. LOGGING ADHERENCE
# =========================================================

def analyze_adherence(
    db: Session,
    patient_id: uuid.UUID,
    days: int = 7,
) -> dict:
    """
    Analyze how consistently the patient has logged:

    - glucose readings
    - meals

    Adherence is based on unique calendar days with at least one
    corresponding log.

    Example:

        2 glucose-log days out of 7
        = 28.6%

    This measures logging behavior only. It does not imply whether
    the patient's medical management is good or bad.
    """

    (
        meals_df,
        glucose_df,
        _,
    ) = _load_logs_as_dataframes(
        db,
        patient_id,
        days,
    )

    # -----------------------------------------------------
    # Unique days with glucose data
    # -----------------------------------------------------

    if not glucose_df.empty:

        logged_days_glucose = (
            glucose_df["timestamp"]
            .dt.date
            .nunique()
        )

    else:

        logged_days_glucose = 0

    # -----------------------------------------------------
    # Unique days with meal data
    # -----------------------------------------------------

    if not meals_df.empty:

        logged_days_meals = (
            meals_df["timestamp"]
            .dt.date
            .nunique()
        )

    else:

        logged_days_meals = 0

    # -----------------------------------------------------
    # Percentages
    # -----------------------------------------------------

    glucose_adherence_pct = float(
        round(
            (
                logged_days_glucose
                / days
            )
            * 100,
            1,
        )
    )

    meal_adherence_pct = float(
        round(
            (
                logged_days_meals
                / days
            )
            * 100,
            1,
        )
    )

    return {
        "window_days":
            days,

        "days_with_glucose_log":
            logged_days_glucose,

        "days_with_meal_log":
            logged_days_meals,

        "glucose_adherence_pct":
            glucose_adherence_pct,

        "meal_adherence_pct":
            meal_adherence_pct,
    }


# =========================================================
# 3. ACTIVITY / GLUCOSE IMPACT
# =========================================================

def analyze_activity_impact(
    db: Session,
    patient_id: uuid.UUID,
    days: int = 30,
) -> dict | None:
    """
    Compare daily average glucose on higher-activity versus
    lower-activity days.

    Activity is divided around the median daily step count.

    This is an observed association in the patient's logged data,
    not proof of causation.
    """

    (
        _,
        glucose_df,
        activity_df,
    ) = _load_logs_as_dataframes(
        db,
        patient_id,
        days,
    )

    if (
        activity_df.empty
        or glucose_df.empty
    ):
        return None

    # -----------------------------------------------------
    # Convert glucose timestamp into calendar date
    # -----------------------------------------------------

    glucose_df["date"] = (
        glucose_df["timestamp"]
        .dt.date
    )

    # -----------------------------------------------------
    # Calculate daily average glucose
    # -----------------------------------------------------

    daily_glucose = (
        glucose_df
        .groupby("date")["value"]
        .mean()
        .reset_index()
    )

    daily_glucose.columns = [
        "date",
        "avg_glucose",
    ]

    # -----------------------------------------------------
    # Match activity with daily glucose
    # -----------------------------------------------------

    merged = daily_glucose.merge(
        activity_df,
        on="date",
        how="inner",
    )

    if len(merged) < 2:
        return None

    # -----------------------------------------------------
    # Median step threshold
    # -----------------------------------------------------

    median_steps = (
        merged["steps"].median()
    )

    high_activity = merged[
        merged["steps"] > median_steps
    ]

    low_activity = merged[
        merged["steps"] <= median_steps
    ]

    if (
        high_activity.empty
        or low_activity.empty
    ):
        return None

    # -----------------------------------------------------
    # Group averages
    # -----------------------------------------------------

    high_act_avg_glucose = float(
        round(
            high_activity[
                "avg_glucose"
            ].mean(),
            1,
        )
    )

    low_act_avg_glucose = float(
        round(
            low_activity[
                "avg_glucose"
            ].mean(),
            1,
        )
    )

    # Positive value means glucose was lower on
    # higher-activity days.
    difference = float(
        round(
            low_act_avg_glucose
            - high_act_avg_glucose,
            1,
        )
    )

    sample_size = len(
        merged
    )

    confidence_score = min(
        1.0,
        sample_size / 10.0,
    )

    return {
        "avg_glucose_high_activity":
            high_act_avg_glucose,

        "avg_glucose_low_activity":
            low_act_avg_glucose,

        "glucose_difference":
            difference,

        "step_threshold":
            int(median_steps),

        "sample_count":
            sample_size,

        "significant":
            bool(
                difference >= 5
            ),

        "confidence_score":
            confidence_score,
    }


# =========================================================
# 4. SPECIFIC GLUCOSE SPIKE EVENTS
# =========================================================

def analyze_spike_events(
    db: Session,
    patient_id: uuid.UUID,
    days: int = 30,
    top_n: int = 3,
) -> dict | None:
    """
    Identify specific glucose readings that are substantially above
    the patient's own recent average and can be associated with a
    preceding meal.

    Example output:

        Friday, Aug 21
        Lunch
        120g carbohydrates
        Glucose: 160 mg/dL
        Deviation from baseline: 22.1 mg/dL

    IMPORTANT:

    This does NOT use a fixed clinical glucose threshold.

    Instead:

        patient's baseline average
                +
        20 mg/dL
                =
        spike detection threshold

    The purpose is to identify unusual readings within the patient's
    own logged history.

    Preference is given to post-meal glucose readings when the
    context_tag is available. Other readings are still considered
    when no post-meal reading exists.
    """

    (
        meals_df,
        glucose_df,
        _,
    ) = _load_logs_as_dataframes(
        db,
        patient_id,
        days,
    )

    if (
        len(glucose_df) < 3
        or len(meals_df) < 1
    ):
        return None

    # -----------------------------------------------------
    # Patient-specific baseline
    # -----------------------------------------------------

    baseline = float(
        glucose_df["value"].mean()
    )

    events = []

    # -----------------------------------------------------
    # Process each glucose reading
    # -----------------------------------------------------

    for _, glucose_row in glucose_df.iterrows():

        glucose_timestamp = (
            glucose_row["timestamp"]
        )

        context_tag = (
            glucose_row.get(
                "context_tag"
            )
        )

        # -------------------------------------------------
        # We want meals preceding the glucose reading.
        #
        # Three hours is intentionally narrower than the
        # general carb correlation window.
        # -------------------------------------------------

        window_start = (
            glucose_timestamp
            - timedelta(hours=3)
        )

        candidate_meals = meals_df[
            (
                meals_df["timestamp"]
                >= window_start
            )
            &
            (
                meals_df["timestamp"]
                <= glucose_timestamp
            )
        ]

        if candidate_meals.empty:
            continue

        # -------------------------------------------------
        # Prefer readings explicitly marked as after_meal.
        #
        # This avoids giving a post-meal interpretation to
        # fasting / bedtime / random readings when a proper
        # post-meal reading exists.
        # -------------------------------------------------

        if context_tag == "after_meal":

            preferred_meals = candidate_meals

        else:

            preferred_meals = candidate_meals

        if preferred_meals.empty:
            continue

        # -------------------------------------------------
        # Closest preceding meal
        # -------------------------------------------------

        time_difference = (
            glucose_timestamp
            - preferred_meals["timestamp"]
        ).abs()

        closest_meal = preferred_meals.iloc[
            time_difference.argmin()
        ]

        # -------------------------------------------------
        # Calculate deviation from patient's baseline
        # -------------------------------------------------

        glucose_value = float(
            glucose_row["value"]
        )

        deviation = (
            glucose_value
            - baseline
        )

        # -------------------------------------------------
        # Spike threshold
        # -------------------------------------------------

        if deviation < 20:
            continue

        # -------------------------------------------------
        # Store detailed event
        # -------------------------------------------------

        events.append(
            {
                "date":
                    glucose_timestamp.strftime(
                        "%A, %b %d"
                    ),

                "timestamp":
                    glucose_timestamp.isoformat(),

                "meal_type":
                    closest_meal["meal_type"],

                "carbs_g":
                    float(
                        closest_meal["carbs"]
                    ),

                "glucose_value":
                    glucose_value,

                "deviation_from_baseline":
                    float(
                        round(
                            deviation,
                            1,
                        )
                    ),

                "context_tag":
                    context_tag,
            }
        )

    # -----------------------------------------------------
    # No spikes found
    # -----------------------------------------------------

    if not events:
        return None

    # -----------------------------------------------------
    # Largest deviations first
    # -----------------------------------------------------

    events.sort(
        key=lambda event:
            event[
                "deviation_from_baseline"
            ],
        reverse=True,
    )

    top_events = events[:top_n]

    # -----------------------------------------------------
    # Confidence
    #
    # More glucose readings provide more context around the
    # patient's baseline.
    # -----------------------------------------------------

    confidence_score = min(
        1.0,
        len(glucose_df) / 15.0,
    )

    return {
        "baseline_avg_glucose":
            float(
                round(
                    baseline,
                    1,
                )
            ),

        "events":
            top_events,

        "total_spikes_found":
            len(events),

        "sample_count":
            len(top_events),

        "significant":
            True,

        "confidence_score":
            confidence_score,
    }