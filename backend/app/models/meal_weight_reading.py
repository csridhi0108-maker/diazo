"""Meal-scale readings received from paired hardware devices."""

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class MealWeightReading(Base):
    __tablename__ = "meal_weight_readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String, nullable=False, index=True)
    weight_g = Column(Float, nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

