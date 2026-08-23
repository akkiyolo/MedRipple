from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserOut

class PatientBase(BaseModel):
    name: str
    date_of_birth: date | None = None
    phone: str | None = None
    gender: str | None = None
    preferences: dict | None = None

class PatientUpdate(BaseModel):
    name: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None
    gender: str | None = None
    preferences: dict | None = None

class PatientOut(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user: UserOut | None = None
    created_at: datetime
