import uuid
import datetime

from pydantic import BaseModel


class ReportOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    period_start: datetime.date
    period_end: datetime.date
    summary_data: dict
    generated_at: datetime.datetime

    class Config:
        from_attributes = True