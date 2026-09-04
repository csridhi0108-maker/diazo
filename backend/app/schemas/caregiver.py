"""
Schemas for the caregiver/doctor <-> patient linking flow.
"""

import uuid
import datetime

from pydantic import BaseModel, EmailStr

from app.models.caregiver_link import LinkType, LinkStatus


class LinkRequestCreate(BaseModel):
    """A caregiver/doctor sends this to request access to a patient,
    identified by the patient's email (not their UUID — a caregiver
    wouldn't know a patient's internal ID, but would know their email,
    matching how the spec describes this: 'invite code or patient
    email')."""

    patient_email: EmailStr
    link_type: LinkType


class LinkRespond(BaseModel):
    """A patient sends this to approve or revoke a pending/existing
    link request."""

    approve: bool  # True = approve, False = revoke/reject


class CareLinkOut(BaseModel):
    id: uuid.UUID
    linked_user_id: uuid.UUID
    patient_id: uuid.UUID
    link_type: LinkType
    status: LinkStatus
    created_at: datetime.datetime
    responded_at: datetime.datetime | None

    class Config:
        from_attributes = True