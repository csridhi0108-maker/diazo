"""
Machine Learning / Intelligence API

Pipeline:

    analytics_engine
          ↓
       explain
          ↓
     llm_explain
          ↓
   Recommendation DB
          ↓
       Frontend

The analytics engine is responsible for calculating deterministic
statistics.

The explain layer decides which computed results are meaningful
enough to expose.

The LLM only converts those already-computed results into
patient-friendly language.

The LLM must never calculate numbers, diagnose conditions, or invent
medical claims.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_authorized_patient_id

from app.models.user import User
from app.models.recommendation import Recommendation

from app.schemas.recommendation import RecommendationOut

from app.intelligence.analytics_engine import (
    analyze_carb_glucose_correlation,
    analyze_adherence,
    analyze_activity_impact,
    analyze_spike_events,
)

from app.intelligence.explain import (
    build_correlation_insight,
    build_adherence_insight,
    build_activity_insight,
    build_spike_insight,
)

from app.intelligence.llm_explain import phrase_insight


router = APIRouter(
    prefix="/api/v1/ml",
    tags=["ml"],
)


# =========================================================
# SAVE RECOMMENDATION
# =========================================================

def _save_recommendation(
    db: Session,
    patient_id: uuid.UUID,
    insight: dict,
    language: str = "en",
) -> Recommendation:
    """
    Saves a recommendation only when its underlying raw data has
    changed.

    This prevents duplicate Recommendation rows and unnecessary
    Groq calls every time the dashboard is refreshed.

    IMPORTANT:

    The raw_data stored here is the exact deterministic analytics
    output used to generate the recommendation. This preserves the
    audit trail.
    """

    insight_type = insight["insight_type"]

    latest = (
        db.query(Recommendation)
        .filter(
            Recommendation.patient_id == patient_id,
            Recommendation.insight_type == insight_type,
        )
        .order_by(
            Recommendation.created_at.desc()
        )
        .first()
    )

    # -----------------------------------------------------
    # Nothing changed
    # -----------------------------------------------------

    if latest and latest.raw_data == insight["raw_data"]:
        return latest

    # -----------------------------------------------------
    # Something changed
    #
    # Generate a new patient-facing explanation.
    # -----------------------------------------------------

    phrased_text = phrase_insight(
        insight,
        language=language,
    )

    recommendation = Recommendation(
        patient_id=patient_id,

        insight_type=insight_type,

        source_model=insight.get(
            "source_model"
        ),

        confidence_score=insight.get(
            "confidence_score"
        ),

        raw_data=insight["raw_data"],

        llm_phrased_text=phrased_text,
    )

    db.add(
        recommendation
    )

    db.commit()

    db.refresh(
        recommendation
    )

    return recommendation


# =========================================================
# GET /recommendations/{patient_id}
# =========================================================

@router.get(
    "/recommendations/{patient_id}",
    response_model=list[RecommendationOut],
)
def get_recommendations(
    patient_id: uuid.UUID = Depends(
        get_authorized_patient_id
    ),
    db: Session = Depends(
        get_db
    ),
):
    """
    Compute fresh patient insights.

    Current insight pipeline:

    1. Carb / glucose correlation
    2. Logging adherence
    3. Activity / glucose relationship
    4. Specific glucose spike events

    Every insight follows:

        analytics
            ↓
        explain layer
            ↓
        LLM phrasing
            ↓
        recommendation storage
    """

    # -----------------------------------------------------
    # Patient / language
    # -----------------------------------------------------

    patient = (
        db.query(User)
        .filter(
            User.id == patient_id
        )
        .first()
    )

    language = (
        patient.preferred_language
        if patient
        else "en"
    )

    recommendations = []

    # =====================================================
    # 1. CARB / GLUCOSE CORRELATION
    # =====================================================

    correlation_raw = (
        analyze_carb_glucose_correlation(
            db,
            patient_id,
        )
    )

    correlation_insight = (
        build_correlation_insight(
            correlation_raw
        )
    )

    if correlation_insight:

        recommendations.append(
            _save_recommendation(
                db,
                patient_id,
                correlation_insight,
                language,
            )
        )

    # =====================================================
    # 2. ADHERENCE
    # =====================================================

    adherence_raw = (
        analyze_adherence(
            db,
            patient_id,
        )
    )

    adherence_insight = (
        build_adherence_insight(
            adherence_raw
        )
    )

    if adherence_insight:

        recommendations.append(
            _save_recommendation(
                db,
                patient_id,
                adherence_insight,
                language,
            )
        )

    # =====================================================
    # 3. ACTIVITY / GLUCOSE
    # =====================================================

    activity_raw = (
        analyze_activity_impact(
            db,
            patient_id,
        )
    )

    activity_insight = (
        build_activity_insight(
            activity_raw
        )
    )

    if activity_insight:

        recommendations.append(
            _save_recommendation(
                db,
                patient_id,
                activity_insight,
                language,
            )
        )

    # =====================================================
    # 4. SPECIFIC GLUCOSE SPIKE EVENTS
    # =====================================================

    spike_raw = (
        analyze_spike_events(
            db,
            patient_id,
            days=30,
            top_n=3,
        )
    )

    spike_insight = (
        build_spike_insight(
            spike_raw
        )
    )

    if spike_insight:

        recommendations.append(
            _save_recommendation(
                db,
                patient_id,
                spike_insight,
                language,
            )
        )

    return recommendations


# =========================================================
# GET RECOMMENDATION HISTORY
# =========================================================

@router.get(
    "/recommendations/{patient_id}/history",
    response_model=list[RecommendationOut],
)
def get_recommendation_history(
    patient_id: uuid.UUID = Depends(
        get_authorized_patient_id
    ),
    db: Session = Depends(
        get_db
    ),
):
    """
    Returns previously saved recommendations.

    Most recent recommendations are returned first.

    This is useful for:

    - historical insight viewing
    - caregiver dashboards
    - report generation
    - auditing
    """

    return (
        db.query(
            Recommendation
        )
        .filter(
            Recommendation.patient_id
            == patient_id
        )
        .order_by(
            Recommendation.created_at.desc()
        )
        .limit(50)
        .all()
    )