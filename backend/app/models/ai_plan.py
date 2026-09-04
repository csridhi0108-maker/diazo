"""
Stores each patient's current AI-generated plan. One row per patient
(overwritten/updated as the plan adjusts over time), not a history
table — if plan history becomes useful later, this can be changed to
append-only with a timestamp, but for now the frontend only ever
needs "what's my plan right now."
"""

import uuid

from sqlalchemy import Column, Float, ForeignKey, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class AIPlan(Base):
    __tablename__ = "ai_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    target_weight_kg = Column(Float, nullable=True)  # null = maintain current weight
    daily_calorie_target = Column(Integer, nullable=False)

    # {"carbs_g": ..., "protein_g": ..., "fat_g": ...} — kept as JSON
    # since it's always read/written as one unit, never queried by
    # individual macro value.
    macro_targets = Column(JSONB, nullable=False)

    daily_step_goal = Column(Integer, nullable=False)

    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self) -> str:
        return f"<AIPlan patient={self.patient_id} calories={self.daily_calorie_target}>"