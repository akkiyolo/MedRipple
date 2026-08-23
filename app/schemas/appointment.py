from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.appointment import AppointmentStatus
from app.models.appointment_hold import HoldStatus

class SlotHoldRequest(BaseModel):
    doctor_id: int
    start_time: datetime

class SlotHoldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    doctor_id: int
    patient_id: int
    start_time: datetime
    end_time: datetime
    hold_expires_at: datetime
    status: HoldStatus

class AppointmentCreate(BaseModel):
    doctor_id: int
    start_time: datetime
    reason: str | None = None
    hold_id: int | None = None
    symptoms: str | None = None

class AppointmentReschedule(BaseModel):
    new_start_time: datetime

class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    doctor_id: int
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus
    reason: str | None = None
    created_at: datetime

    patient_name: str | None = None
    doctor_name: str | None = None
    doctor_specialization: str | None = None
