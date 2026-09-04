"""
Links a patient to a caregiver or doctor. Many-to-many by design:
one caregiver/doctor can be linked to multiple patients, and (in
principle) one patient could have multiple caregivers/doctors later.

Consent is enforced here, not just assumed: a link only grants read
access once the patient has approved it (status == "approved").
This is the single gate that every caregiver/doctor-facing endpoint
checks before returning any patient data — see core/dependencies.py.
"""

import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class LinkStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    revoked = "revoked"


class LinkType(str, enum.Enum):
    family = "family"   # caregiver dashboard — simplified view
    doctor = "doctor"    # doctor dashboard — full clinical detail
    # (approved "Doctor Dashboard" extension: same linking mechanism,
    # link_type is what changes which dashboard/data the linked
    # account is allowed to see, not the permission model itself)


class CareLink(Base):
    __tablename__ = "care_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    linked_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    link_type = Column(Enum(LinkType), nullable=False, default=LinkType.family)
    status = Column(Enum(LinkStatus), nullable=False, default=LinkStatus.pending)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    responded_at = Column(DateTime(timezone=True), nullable=True)  # when patient approved/revoked

    linked_user = relationship("User", foreign_keys=[linked_user_id])
    patient = relationship("User", foreign_keys=[patient_id])

    def __repr__(self) -> str:
        return f"<CareLink {self.linked_user_id} -> {self.patient_id} ({self.link_type}, {self.status})>"