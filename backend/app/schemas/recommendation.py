import uuid
import datetime

from pydantic import BaseModel


class RecommendationOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    insight_type: str
    source_model: str | None
    confidence_score: float | None
    raw_data: dict
    llm_phrased_text: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True