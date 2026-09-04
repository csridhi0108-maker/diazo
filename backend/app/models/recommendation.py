"""
Stores every recommendation shown to a patient, with the raw data that
produced it — this is what makes recommendations traceable rather
than opaque (per the architecture: every recommendation must trace
back to real computed data, never an unverifiable LLM claim).
"""

import uuid

from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    insight_type = Column(String, nullable=False)  # "correlation" | "adherence" | "risk"
    source_model = Column(String, nullable=True)     # e.g. "analytics_engine", "risk_model"
    confidence_score = Column(Float, nullable=True)  # only set for ML-derived insights

    raw_data = Column(JSONB, nullable=False)           # exact analytics/ML output — the audit trail
    llm_phrased_text = Column(String, nullable=False)  # what the patient actually sees

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Recommendation patient={self.patient_id} type={self.insight_type}>"