"""Contracts for ESP32 meal-scale ingestion."""

import uuid

from pydantic import BaseModel, Field


class MealWeightReadingIn(BaseModel):
    """The ESP32 sends a stable device identifier and the current scale value."""

    patient_id: uuid.UUID
    device_id: str = Field(min_length=3, max_length=100)
    weight_g: float = Field(gt=0, le=5000)


class MealWeightReadingOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    device_id: str
    weight_g: float

    class Config:
        from_attributes = True

