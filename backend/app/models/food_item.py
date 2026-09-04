"""
Reference table of foods and their nutrition per 100g. Used by the
meal-scale feature: patient selects a food, ESP32/scale provides the
weight, and nutrition_service multiplies (nutrient_per_100g * weight_g
/ 100) to get the actual carbs/protein/calories for that portion.

Deliberately a DB table (not a hardcoded dict) so the food list can be
expanded later — by a seed script for now, by an admin UI eventually —
without a code change.
"""

import uuid

from sqlalchemy import Column, Float, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)

    carbs_g_per_100g = Column(Float, nullable=False)
    protein_g_per_100g = Column(Float, nullable=False)
    calories_per_100g = Column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<FoodItem {self.name} carbs={self.carbs_g_per_100g}/100g>"
