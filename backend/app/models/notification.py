"""
Notifications sent to caregivers/doctors (meal logged, missed-log
alert, emergency SOS). Patients don't receive notifications about
themselves in this table — this is specifically the caregiver/doctor
-facing alert feed.
"""

import uuid
import enum

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class NotificationType(str, enum.Enum):
    meal_logged = "meal_logged"
    missed_log = "missed_log"
    emergency = "emergency"  # approved Emergency SOS extension


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who sees this notification — always a caregiver or doctor
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    # Which patient this notification is about
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    type = Column(Enum(NotificationType), nullable=False)
    message = Column(String, nullable=False)
    read = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Notification to={self.recipient_id} type={self.type}>"