from pydantic import BaseModel, Field
from app.models.ai_summary import UrgencyLevel

class AdaptiveIntakeRequest(BaseModel):
    appointment_id: int | None = None
    raw_symptoms: str
    previous_answers: list[dict] = []

class SymptomIntakeAnalysis(BaseModel):
    urgency: UrgencyLevel = UrgencyLevel.LOW
    chief_complaint: str = ""
    symptoms: list[str] = []
    duration: str = ""
    severity: str = ""
    adaptive_questions: list[str] = []
    clinical_context: str = ""

class DoctorBriefEvidence(BaseModel):
    category: str
    source_date: str
    summary: str

class DoctorBrief(BaseModel):
    chief_complaint: str
    symptom_timeline: str
    urgency: UrgencyLevel
    relevant_history: list[str] = []
    current_medications: list[str] = []
    suggested_questions: list[str] = []
    evidence: list[DoctorBriefEvidence] = []

class VisitSummaryRequest(BaseModel):
    appointment_id: int | None = None
    clinical_notes: str
    prescriptions_raw: str | None = None

class PatientFriendlyVisitSummary(BaseModel):
    patient_friendly_summary: str
    doctor_instructions: list[str] = []
    medication_guidance: list[str] = []
    lifestyle_and_recovery: list[str] = []
    when_to_seek_urgent_care: str = ""

class CarePlanPhase(BaseModel):
    day_range: str
    action_items: list[str]

class CarePlanData(BaseModel):
    title: str
    overview: str
    phases: list[CarePlanPhase] = []
    warning_signs: list[str] = []
    follow_up_timeline: str = ""

class DoctorQueryRequest(BaseModel):
    patient_id: int
    query: str
