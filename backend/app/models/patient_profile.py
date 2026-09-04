"""
Patient-specific onboarding data. Separated from `users` because this
data only exists for patients, not caregivers/admins/doctors, and it's
exactly the feature set the AI plan + analytics/ML layers read from.

Every field here should map to a real downstream use — see
PROJECT_SPEC.md "Phase 1" and "why each field exists" reasoning:
  - age/height/weight        -> BMI, calorie targets (plan_service.py)
  - diabetes_type             -> switches management vs. risk-assessment mode
  - activity_level             -> baseline calorie/step targets
  - medications                -> safety context only, no dosage advice
  - family_history               -> feeds risk_model.py for non-diagnosed users
"""

import enum
import uuid

from sqlalchemy import Column, String, Integer, Float, Boolean, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DiabetesType(str, enum.Enum):
    type1 = "type1"
    type2 = "type2"
    prediabetic = "prediabetic"
    none = "none"  # no diagnosis — patient uses the risk-assessment flow instead

class Sex(str, enum.Enum):
    male = "male"
    female = "female"

class ActivityLevel(str, enum.Enum):
    sedentary = "sedentary"
    moderate = "moderate"
    active = "active"


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    diabetes_type = Column(Enum(DiabetesType), nullable=False, default=DiabetesType.none)
    diagnosis_duration_months = Column(Integer, nullable=True)  # null if diabetes_type == none

    sex = Column(Enum(Sex), nullable=False)
    age = Column(Integer, nullable=False)
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    activity_level = Column(Enum(ActivityLevel), nullable=False, default=ActivityLevel.sedentary)

    medications = Column(String, nullable=True)      # free text, context only
    dietary_prefs = Column(String, nullable=True)     # free text, optional
    family_history = Column(Boolean, default=False)  # feeds risk_model.py

    user = relationship("User", back_populates="patient_profile")

    def __repr__(self) -> str:
        return f"<PatientProfile user_id={self.user_id} type={self.diabetes_type}>"