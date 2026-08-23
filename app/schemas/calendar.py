from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.calendar_event import CalendarSyncStatus

class CalendarEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    google_event_id: str | None = None
    status: CalendarSyncStatus
    last_synced_at: datetime | None = None
