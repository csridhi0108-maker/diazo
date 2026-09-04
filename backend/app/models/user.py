"""
User table — the single source of identity for all three roles
(patient, caregiver, admin, and later doctor). Role-specific data
(diabetes type, age, etc.) lives in patient_profiles, NOT here —
this table only holds what's needed for authentication and routing.
"""

import enum
import uuid

from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserRole(str, enum.Enum):
    patient = "patient"
    caregiver = "caregiver"
    admin = "admin"
    doctor = "doctor"  # added per the approved "Doctor Dashboard" extension


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(100), nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)

    # Multi-language support (approved extension) — defaults to English,
    # used by intelligence/llm_explain.py to phrase recommendations and
    # by the frontend to pick the UI locale.
    preferred_language = Column(String, default="en", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # One-to-one: only present if role == "patient"
    patient_profile = relationship(
        "PatientProfile", back_populates="user", uselist=False
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"