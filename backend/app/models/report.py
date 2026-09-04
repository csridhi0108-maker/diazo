"""
Persisted weekly report snapshots. Generated on-demand (not on a
schedule yet — that's the scheduler/ module, still to come) and
saved so a patient can look back at past reports, not just the
current week.
"""

import uuid
import datetime

from sqlalchemy import Column, Date, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # {"avg_glucose": ..., "glucose_trend": ..., "adherence_pct": ...,
    #  "weight_change_kg": ..., ...} — kept as JSON since this is
    # always read/written as one unit, and its shape may evolve.
    summary_data = Column(JSONB, nullable=False)

    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Report patient={self.patient_id} {self.period_start} to {self.period_end}>"