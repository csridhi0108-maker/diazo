"""
Pydantic schema for reading back a patient's AI plan. No "create"
schema needed here — plans are only ever generated internally by
plan_service.py, never submitted directly by a client.
"""

import uuid
import datetime

from pydantic import BaseModel


class AIPlanOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    target_weight_kg: float | None
    daily_calorie_target: int
    macro_targets: dict
    daily_step_goal: int
    updated_at: datetime.datetime

    class Config:
        from_attributes = True