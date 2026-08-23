from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from app.models.followup import FollowUpStatus

class FollowUpCreate(BaseModel):
    appointment_id: int
    due_date: date
    reason: str

class FollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    due_date: date
    reason: str
    status: FollowUpStatus
    created_at: datetime
    patient_name: str | None = None
    doctor_name: str | None = None
