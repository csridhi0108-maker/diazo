"""
Glucose logs — the output side of the correlation model. Each reading
is tagged with a context (e.g. "before_lunch") since raw glucose
numbers are only meaningful relative to when they were taken, matching
how real glucometer logging works clinically.
"""

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class GlucoseLog(Base):
    __tablename__ = "glucose_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    value = Column(Float, nullable=False)  # mg/dL

    # e.g. "before_breakfast", "after_lunch", "before_bed" — free text
    # for now, kept simple rather than a rigid enum since real patients
    # log context inconsistently and the analytics engine just needs
    # "before" vs "after" + rough meal association, not exact matching.
    context_tag = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<GlucoseLog patient={self.patient_id} {self.value} @ {self.timestamp}>"