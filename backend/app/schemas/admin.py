"""
Schemas for the admin dashboard — system-wide oversight endpoints.
"""

import uuid
import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserSummary(BaseModel):
    """Lightweight user info for admin lists."""
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    role: UserRole
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class PatientWithCaregivers(UserSummary):
    """Patient with their approved caregiver links."""
    caregiver_count: int = 0
    caregivers: List[str] = []  # list of caregiver emails


class CaregiverWithPatients(UserSummary):
    """Caregiver with their approved patient links."""
    patient_count: int = 0
    patients: List[str] = []  # list of patient emails


class SystemStats(BaseModel):
    """High-level system metrics for the admin dashboard."""
    total_users: int
    total_patients: int
    total_caregivers: int
    total_doctors: int
    total_admins: int
    active_links: int  # approved care_links
    pending_links: int  # pending care_links
    recent_registrations_7d: int


class CreateAdminRequest(BaseModel):
    """Used to bootstrap the very first admin account."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class AssignCaregiverRequest(BaseModel):
    """Admin can directly link a caregiver to a patient (bypasses consent)."""
    caregiver_id: uuid.UUID
    patient_id: uuid.UUID
    link_type: str = "family"  # or "doctor"