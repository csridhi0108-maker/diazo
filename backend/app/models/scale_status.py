"""Latest LED instruction for each meal-scale device."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class ScaleStatus(Base):
    """A device polls this row after a patient confirms a scaled meal."""

    __tablename__ = "scale_statuses"

    device_id = Column(String, primary_key=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    # PENDING until a selected food has been evaluated; GREEN/RED are LED commands.
    status = Column(String, nullable=False, default="PENDING")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

