"""Contracts for the meal-scale food/nutrition endpoints."""

import uuid

from pydantic import BaseModel, Field


class FoodItemOut(BaseModel):
    id: uuid.UUID
    name: str
    carbs_g_per_100g: float
    protein_g_per_100g: float
    calories_per_100g: float | None

    class Config:
        from_attributes = True


class NutritionCalculateIn(BaseModel):
    """What the frontend sends once the patient has picked a food and
    a scale weight is available (real or simulated)."""

    food_id: uuid.UUID
    weight_g: float = Field(gt=0, le=5000)


class NutritionCalculateOut(BaseModel):
    """Preview response — NOT persisted. The frontend shows this to the
    patient before they hit "Log meal"; the actual meal_logs row is
    only created when POST /api/v1/logs/meals is called."""

    food: str
    weight_g: float
    carbs_g: float
    protein_g: float
    calories: float | None
    status: str | None  # "WITHIN_TARGET" | "ABOVE_TARGET" | null if no AI plan yet
