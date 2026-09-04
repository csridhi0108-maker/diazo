"""
Schema for the single aggregated dashboard response — combines plan,
recent logs, latest recommendations, and adherence into one payload
so the frontend doesn't need 4-5 separate calls to render one screen.
"""

import uuid

from pydantic import BaseModel

from app.schemas.plan import AIPlanOut
from app.schemas.log import GlucoseLogOut, MealLogOut, ActivityLogOut
from app.schemas.recommendation import RecommendationOut


class DashboardOut(BaseModel):
    patient_id: uuid.UUID
    plan: AIPlanOut | None
    recent_glucose_logs: list[GlucoseLogOut]
    recent_meal_logs: list[MealLogOut]
    recent_activity_logs: list[ActivityLogOut]
    recommendations: list[RecommendationOut]