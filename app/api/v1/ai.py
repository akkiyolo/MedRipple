from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.appointment import Appointment
from app.schemas.ai import AdaptiveIntakeRequest, VisitSummaryRequest, DoctorQueryRequest
from app.agents.intake_agent import IntakeAgent
from app.agents.doctor_brief_agent import DoctorBriefAgent
from app.agents.visit_summary_agent import VisitSummaryAgent
from app.agents.care_plan_agent import CarePlanAgent
from app.agents.followup_agent import FollowUpAgent
from app.models.ai_summary import AISummary, AISummaryType
from app.services.rag_service import RAGService

router = APIRouter(prefix="/ai", tags=["AI Copilot & Longitudinal Agents"])

def _require_appointment_access(db: Session, user: User, appointment_id: int, role: UserRole | None = None) -> Appointment:
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("Appointment not found")
    if user.role == UserRole.ADMIN:
        return appt
    if role and user.role != role:
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("Appointment access forbidden")
    if user.role == UserRole.PATIENT and (not user.patient_profile or appt.patient_id != user.patient_profile.id):
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("Appointment access forbidden")
    if user.role == UserRole.DOCTOR and (not user.doctor_profile or appt.doctor_id != user.doctor_profile.id):
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("Appointment access forbidden")
    return appt

@router.post("/intake")
def process_ai_intake(req: AdaptiveIntakeRequest, user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    if req.appointment_id is not None:
        _require_appointment_access(db, user, req.appointment_id, UserRole.PATIENT)
    result = IntakeAgent.process_intake(req.raw_symptoms, req.previous_answers)
    if req.appointment_id is not None:
        ai_summary = AISummary(
            appointment_id=req.appointment_id,
            summary_type=AISummaryType.INTAKE_SUMMARY,
            content=result.model_dump(),
            urgency=result.urgency
        )
        db.add(ai_summary)
        db.commit()
    return {"success": True, "data": result.model_dump(), "message": "AI Intake analysis complete"}

@router.post("/symptom-summary")
def generate_symptom_summary(req: AdaptiveIntakeRequest, user: User = Depends(require_role(UserRole.PATIENT))):
    result = IntakeAgent.process_intake(req.raw_symptoms)
    return {"success": True, "data": result.model_dump(), "message": "Symptom summary generated"}

@router.post("/doctor-brief")
def generate_doctor_brief(appointment_id: int, user: User = Depends(require_role(UserRole.DOCTOR)), db: Session = Depends(get_db)):
    appt = _require_appointment_access(db, user, appointment_id, UserRole.DOCTOR)
    brief = DoctorBriefAgent.generate_brief(db, appt)
    ai_summary = AISummary(
        appointment_id=appt.id,
        summary_type=AISummaryType.DOCTOR_BRIEF,
        content=brief.model_dump(),
        urgency=brief.urgency
    )
    db.add(ai_summary)
    db.commit()
    return {"success": True, "data": brief.model_dump(), "message": "Doctor brief generated"}

@router.post("/visit-summary")
def generate_visit_summary(req: VisitSummaryRequest, user: User = Depends(require_role(UserRole.DOCTOR)), db: Session = Depends(get_db)):
    if req.appointment_id is not None:
        _require_appointment_access(db, user, req.appointment_id, UserRole.DOCTOR)
    summary = VisitSummaryAgent.generate_summary(req.clinical_notes, req.prescriptions_raw)
    if req.appointment_id is not None:
        ai_summary = AISummary(
            appointment_id=req.appointment_id,
            summary_type=AISummaryType.VISIT_SUMMARY,
            content=summary.model_dump()
        )
        db.add(ai_summary)
        db.commit()
    return {"success": True, "data": summary.model_dump(), "message": "Patient-friendly visit summary generated"}

@router.post("/care-plan")
def generate_care_plan_ai(req: VisitSummaryRequest, user: User = Depends(require_role(UserRole.DOCTOR)), db: Session = Depends(get_db)):
    if req.appointment_id is None:
        from app.core.exceptions import MedRippleException
        raise MedRippleException("appointment_id is required", code="VALIDATION_ERROR", status_code=422)
    _require_appointment_access(db, user, req.appointment_id, UserRole.DOCTOR)
    plan = CarePlanAgent.generate_care_plan(req.clinical_notes, req.prescriptions_raw)
    ai_summary = AISummary(
        appointment_id=req.appointment_id,
        summary_type=AISummaryType.CARE_PLAN_SUMMARY,
        content=plan.model_dump()
    )
    db.add(ai_summary)
    db.commit()
    return {"success": True, "data": plan.model_dump(), "message": "AI Care Plan generated"}

@router.post("/followup-analysis")
def analyze_followup_ai(req: VisitSummaryRequest, user: User = Depends(require_role(UserRole.DOCTOR))):
    analysis = FollowUpAgent.analyze_followup(req.clinical_notes)
    return {"success": True, "data": analysis.model_dump(), "message": "Follow-up analysis generated"}

@router.get("/appointments/{appointment_id}/insights")
def get_appointment_insights(appointment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_appointment_access(db, user, appointment_id)
    summaries = db.query(AISummary).filter(AISummary.appointment_id == appointment_id).all()
    results = [{"id": s.id, "type": s.summary_type.value, "content": s.content, "urgency": s.urgency.value} for s in summaries]
    return {"success": True, "data": results, "message": "AI insights fetched"}

from pydantic import BaseModel
class ChatMessage(BaseModel):
    message: str
    history: list[dict[str, str]] = []
    patient_id: int | None = None # Required for doctor

@router.post("/chat/patient")
def patient_chat_agent(req: ChatMessage, user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    from app.agents.chat_agent import ChatAgent
    response = ChatAgent.chat_with_patient_agent(db, user, req.message, req.history)
    return {"success": True, "data": {"reply": response}, "message": "Chat response generated"}

@router.post("/chat/doctor")
def doctor_chat_agent(req: ChatMessage, user: User = Depends(require_role(UserRole.DOCTOR)), db: Session = Depends(get_db)):
    if not req.patient_id:
        from app.core.exceptions import MedRippleException
        raise MedRippleException("patient_id is required for doctor chat", code="VALIDATION_ERROR", status_code=422)
    from app.agents.chat_agent import ChatAgent
    response = ChatAgent.chat_with_doctor_agent(db, user, req.patient_id, req.message, req.history)
    return {"success": True, "data": {"reply": response}, "message": "Clinical copilot response generated"}
