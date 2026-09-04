import uuid
import datetime

from pydantic import BaseModel

from app.models.notification import NotificationType


class NotificationOut(BaseModel):
    id: uuid.UUID
    recipient_id: uuid.UUID
    patient_id: uuid.UUID
    type: NotificationType
    message: str
    read: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True