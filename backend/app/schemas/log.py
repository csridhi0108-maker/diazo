"""
Pydantic schemas for the three logging types. Kept in one file since
they're small and always touched together in api/logs.py.
"""

import uuid
import datetime

from pydantic import BaseModel, Field, model_validator


# ---------- Meal ----------

class MealLogCreate(BaseModel):
    meal_type: str  # "breakfast" | "lunch" | "dinner" | "snack"
    food_items: list[dict] | None = None
    estimated_carbs: float | None = Field(default=None, ge=0)
    estimated_calories: float | None = Field(default=None, ge=0)
    photo_url: str | None = None

    # Meal-scale flow only. When both are present, the backend
    # recalculates carbs/protein/calories/status itself from food_id +
    # weight_g (never trusting client-supplied numbers for a
    # scale-logged meal) and estimated_carbs/estimated_calories above
    # are ignored. Leave both unset for a manual/free-text meal log —
    # existing behavior is unchanged.
    food_id: uuid.UUID | None = None
    weight_g: float | None = Field(default=None, gt=0, le=5000)
    scale_device_id: str | None = Field(default=None, min_length=3, max_length=100)

    @model_validator(mode="after")
    def validate_scale_fields(self):
        """A measured food needs both inputs; manual logs need neither."""
        if (self.food_id is None) != (self.weight_g is None):
            raise ValueError("food_id and weight_g must be provided together")
        if self.scale_device_id is not None and self.food_id is None:
            raise ValueError("scale_device_id requires food_id and weight_g")
        return self


class MealLogOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    timestamp: datetime.datetime
    meal_type: str
    food_items: list[dict] | None
    estimated_carbs: float | None
    estimated_protein: float | None
    estimated_calories: float | None
    nutrition_status: str | None
    photo_url: str | None

    class Config:
        from_attributes = True


# ---------- Glucose ----------

class GlucoseLogCreate(BaseModel):
    value: float = Field(gt=0, lt=1000)  # mg/dL — sanity bounds, not clinical validation
    context_tag: str | None = None


class GlucoseLogOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    timestamp: datetime.datetime
    value: float
    context_tag: str | None

    class Config:
        from_attributes = True


# ---------- Activity ----------

class ActivityLogUpsert(BaseModel):
    """Used for both creating today's entry and updating it later in
    the day (e.g. step count refreshed) — see the upsert logic in
    api/logs.py for why this isn't a plain create."""

    date: datetime.date
    steps: int = Field(ge=0)
    calories_burned: float = Field(ge=0)


class ActivityLogOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    date: datetime.date
    steps: int
    calories_burned: float

    class Config:
        from_attributes = True
