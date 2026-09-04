"""
Pydantic schemas for patient profile onboarding and retrieval.
Mirrors models/patient_profile.py but shaped for the API surface.
"""

import uuid

from pydantic import BaseModel, Field

from app.models.patient_profile import DiabetesType, ActivityLevel, Sex


class PatientOnboarding(BaseModel):
    full_name: str | None = None
    diabetes_type: DiabetesType
    diagnosis_duration_months: int | None = None
    sex: Sex
    age: int = Field(gt=0, lt=130)
    height_cm: float = Field(gt=0)
    weight_kg: float = Field(gt=0)
    activity_level: ActivityLevel
    medications: str | None = None
    dietary_prefs: str | None = None
    family_history: bool = False


class PatientProfileOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str | None = None
    diabetes_type: DiabetesType
    diagnosis_duration_months: int | None
    
    sex: Sex
    age: int = Field(gt=0, lt=130)
    height_cm: float
    weight_kg: float
    activity_level: ActivityLevel
    medications: str | None
    dietary_prefs: str | None
    family_history: bool

    class Config:
        from_attributes = True


class PatientProfileUpdate(BaseModel):
    """All fields optional — only what's provided gets updated."""

    full_name: str | None = None
    diabetes_type: DiabetesType | None = None
    diagnosis_duration_months: int | None = None
    age: int | None = Field(default=None, gt=0, lt=130)
    height_cm: float | None = Field(default=None, gt=0)
    weight_kg: float | None = Field(default=None, gt=0)
    activity_level: ActivityLevel | None = None
    medications: str | None = None
    dietary_prefs: str | None = None
    family_history: bool | None = None