"""
Explain Layer — decides whether a raw statistical result is meaningful 
enough to show the user, and structures it into a standard format.
"""

from typing import Optional


def build_correlation_insight(raw_data: Optional[dict]) -> Optional[dict]:
    if not raw_data or not raw_data.get("significant"):
        return None

    return {
        "insight_type": "correlation",
        "source_model": "carb_glucose",
        "confidence_score": raw_data.get("confidence_score", 0.8),
        "raw_data": {
            "avg_glucose_increase": raw_data["glucose_difference"],
            "high_carb_avg": raw_data["high_carb_avg_glucose"],
            "low_carb_avg": raw_data["low_carb_avg_glucose"],
            "threshold_g": raw_data["high_carb_threshold_g"],
            "sample_count": raw_data["sample_size"],
        }
    }


def build_adherence_insight(raw_data: dict) -> Optional[dict]:
    """
    Evaluates logging adherence.
    """
    glucose_pct = raw_data.get("glucose_adherence_pct", 0)
    meal_pct = raw_data.get("meal_adherence_pct", 0)
    
    return {
        "insight_type": "adherence",
        "source_model": "adherence",
        "confidence_score": 1.0,
        "raw_data": {
            "window_days": raw_data.get("window_days", 7),
            "glucose_days_logged": raw_data.get("days_with_glucose_log", 0),
            "meal_days_logged": raw_data.get("days_with_meal_log", 0),
            "glucose_adherence_pct": glucose_pct,
            "meal_adherence_pct": meal_pct,
        }
    }


def build_activity_insight(raw_data: Optional[dict]) -> Optional[dict]:
    if not raw_data or not raw_data.get("significant"):
        return None

    return {
        "insight_type": "activity_impact",
        "source_model": "activity_glucose",
        "confidence_score": raw_data.get("confidence_score", 0.8),
        "raw_data": {
            "avg_glucose_high_activity": raw_data["avg_glucose_high_activity"],
            "avg_glucose_low_activity": raw_data["avg_glucose_low_activity"],
            "glucose_difference": raw_data["glucose_difference"],
            "step_threshold": raw_data["step_threshold"],
            "sample_count": raw_data["sample_count"],
        }
    }


def build_spike_insight(raw_data: Optional[dict]) -> Optional[dict]:
    """
    Specific, dated glucose-spike call-outs (e.g. "Tuesday lunch, 90g
    carbs -> 172 mg/dL"), distinct from the aggregate correlation
    insight. Always shown if any spikes were found — no significance
    gate needed since each event already passed the 20 mg/dL
    deviation threshold inside analyze_spike_events().
    """
    if not raw_data or not raw_data.get("events"):
        return None

    return {
        "insight_type": "spike_events",
        "source_model": "spike_detection",
        "confidence_score": raw_data.get("confidence_score", 0.8),
        "raw_data": {
            "baseline_avg_glucose": raw_data["baseline_avg_glucose"],
            "events": raw_data["events"],
            "total_spikes_found": raw_data["total_spikes_found"],
            "sample_count": raw_data["sample_count"],
        }
    }