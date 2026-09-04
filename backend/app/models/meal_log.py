"""
Meal logs — the input side of glucose correlation. Every log ties
carbs/calories to a specific patient and timestamp so the analytics
engine can later match it against glucose readings taken afterward.
"""

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    meal_type = Column(String, nullable=False)  # "breakfast" | "lunch" | "dinner" | "snack"

    # Flexible list of items, e.g. [{"name": "rice", "portion": "1 cup"}, ...]
    # Kept as JSON rather than a separate table since food items are
    # display/context only — the ML layer only reads the aggregate
    # estimated_carbs/estimated_calories below.
    food_items = Column(JSONB, nullable=True)

    estimated_carbs = Column(Float, nullable=True)      # grams
    estimated_protein = Column(Float, nullable=True)    # grams — populated when logged via the meal scale
    estimated_calories = Column(Float, nullable=True)

    # Set only when this meal was logged through the food-scale flow:
    # which reference food was selected and where it landed against
    # the patient's daily macro target at the moment of logging.
    # "WITHIN_TARGET" | "ABOVE_TARGET" | None (manual entries have no status).
    scale_food_id = Column(UUID(as_uuid=True), ForeignKey("food_items.id"), nullable=True)
    nutrition_status = Column(String, nullable=True)

    photo_url = Column(String, nullable=True)  # stretch goal — photo-based logging

    def __repr__(self) -> str:
        return f"<MealLog patient={self.patient_id} {self.meal_type} @ {self.timestamp}>"