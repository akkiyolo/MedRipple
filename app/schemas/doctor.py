from datetime import time, date, datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserOut

class DoctorScheduleBase(BaseModel):
    day_of_week: int  # 0-6
    start_time: time
    end_time: time
    is_active: bool = True

class DoctorScheduleOut(DoctorScheduleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    doctor_id: int

class DoctorLeaveBase(BaseModel):
    start_date: date
    end_date: date
    reason: str | None = None

class DoctorLeaveOut(DoctorLeaveBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    doctor_id: int

class DoctorBase(BaseModel):
    name: str
    specialization: str
    license_number: str | None = None
    bio: str | None = None
    slot_duration: int = 30

class DoctorUpdate(BaseModel):
    name: str | None = None
    specialization: str | None = None
    license_number: str | None = None
    bio: str | None = None
    slot_duration: int | None = None

class DoctorOut(DoctorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user: UserOut | None = None
    created_at: datetime
    schedules: list[DoctorScheduleOut] = []
