from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.ai import CarePlanData

class CarePlanCreate(BaseModel):
    appointment_id: int
    plan_data: CarePlanData

class CarePlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    patient_id: int
    plan_data: dict
    created_at: datetime
    updated_at: datetime
