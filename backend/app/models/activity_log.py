"""
Activity logs — daily steps/calories burned, tracked against the
AI plan's daily_step_goal. One row per patient per day (not per
event), since step counts are cumulative through the day.
"""

import uuid

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    __table_args__ = (
        # One row per patient per day — logging steps again on the same
        # day should update the existing row, not create a duplicate.
        UniqueConstraint("patient_id", "date", name="uq_activity_patient_date"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    date = Column(Date, nullable=False)
    steps = Column(Integer, default=0)
    calories_burned = Column(Float, default=0)

    def __repr__(self) -> str:
        return f"<ActivityLog patient={self.patient_id} {self.date} steps={self.steps}>"