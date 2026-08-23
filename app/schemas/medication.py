from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.medication_schedule import ReminderStatus

class PrescriptionCreate(BaseModel):
    medication: str
    dosage: str
    frequency: str
    duration: str
    instructions: str | None = None

class PrescriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    medication: str
    dosage: str
    frequency: str
    duration: str
    instructions: str | None = None
    created_at: datetime

class MedicationScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prescription_id: int
    scheduled_time: datetime
    status: ReminderStatus
    created_at: datetime
    medication_name: str | None = None
    dosage: str | None = None

class AdherenceReport(BaseModel):
    prescription_id: int
    medication: str
    total_reminders: int
    acknowledged: int
    missed: int
    pending: int
    adherence_rate_pct: float
    care_drift_flag: bool
    drift_message: str | None = None
