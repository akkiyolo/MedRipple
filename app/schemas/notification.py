from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.notification import NotificationChannel, NotificationStatus

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str | None = None
    recipient: str
    channel: NotificationChannel
    type: str
    status: NotificationStatus
    attempt_count: int
    last_attempt_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
