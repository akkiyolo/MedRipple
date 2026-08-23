from datetime import datetime, timezone, date as date_type
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription
from app.models.medication_schedule import MedicationSchedule
from app.models.doctor_leave import DoctorLeave
from app.models.ai_summary import AISummary, AISummaryType
from app.schemas.medication import PrescriptionCreate
from app.schemas.doctor import DoctorLeaveBase

from app.services.booking_service import BookingService
from app.services.schedule_service import ScheduleService
from app.services.medication_service import MedicationService
from app.services.doctor_service import DoctorService

from app.agents.intake_agent import IntakeAgent
from app.agents.doctor_brief_agent import DoctorBriefAgent
from app.agents.visit_summary_agent import VisitSummaryAgent
from app.agents.care_plan_agent import CarePlanAgent

router = APIRouter(tags=["Frontend Compatibility APIs"])

# Pydantic Request Models
class BookAppointmentCompatRequest(BaseModel):
    doctor_id: int
    slot_id: Optional[str] = None
    start_time: Optional[str] = None
    hold_id: Optional[int] = None
    symptoms: Optional[str] = None
    reason: Optional[str] = None

class IntakeCompatRequest(BaseModel):
    symptoms: Optional[str] = None
    raw_symptoms: Optional[str] = None

class FinalizeConsultationRequest(BaseModel):
    clinical_notes: str
    medication: Optional[Dict[str, Any]] = None

class DoctorLeaveCompatRequest(BaseModel):
    start_date: str
    end_date: str
    reason: Optional[str] = None

# Helper to get current user from token or cookie
def get_user_from_request(request: Request, db: Session) -> Optional[User]:
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    if not token:
        return None
    try:
        from app.core.security import decode_access_token
        payload = decode_access_token(token)
        if not payload:
            return None
        user_id = int(payload.get("sub"))
        return db.query(User).filter(User.id == user_id).first()
    except Exception:
        return None

def require_appointment_user(request: Request, db: Session, appointment_id: int, role: UserRole) -> Appointment:
    user = get_user_from_request(request, db)
    if not user or user.role != role:
        raise HTTPException(status_code=401, detail="Authentication required")
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if role == UserRole.PATIENT and (not user.patient_profile or appt.patient_id != user.patient_profile.id):
        raise HTTPException(status_code=403, detail="Appointment access forbidden")
    if role == UserRole.DOCTOR and (not user.doctor_profile or appt.doctor_id != user.doctor_profile.id):
        raise HTTPException(status_code=403, detail="Appointment access forbidden")
    return appt

def require_prescription_patient(request: Request, db: Session, prescription_id: int) -> Prescription:
    user = get_user_from_request(request, db)
    if not user or user.role != UserRole.PATIENT or not user.patient_profile:
        raise HTTPException(status_code=401, detail="Patient authentication required")
    rx = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not rx:
        raise HTTPException(status_code=404, detail="Prescription not found")
    if rx.appointment.patient_id != user.patient_profile.id:
        raise HTTPException(status_code=403, detail="Prescription access forbidden")
    return rx

# 1. Appointment Slots Compatibility Endpoint
@router.get("/api/appointments/slots")
@router.get("/api/v1/appointments/slots")
def get_slots_compat(
    doctor_id: int,
    date: Optional[str] = None,
    target_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query_date_str = date or target_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        q_date = date_type.fromisoformat(query_date_str)
    except ValueError:
        q_date = datetime.now(timezone.utc).date()

    slots_data = ScheduleService.get_available_slots(db, doctor_id=doctor_id, target_date=q_date)
    formatted_slots = []
    for s in slots_data:
        formatted_slots.append({
            "id": s["start_time"],
            "start_time": s["start_time"],
            "time": s["formatted_time"],
            "display": s["formatted_time"]
        })
    return {
        "success": True,
        "data": formatted_slots,
        "slots": formatted_slots,
        "message": "Slots retrieved"
    }

# 2. Appointment Booking Compatibility Endpoint
@router.post("/api/appointments/book")
@router.post("/api/v1/appointments/book")
def book_appointment_compat(
    req: BookAppointmentCompatRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_user_from_request(request, db)
    if not user or not user.patient_profile:
        raise HTTPException(status_code=401, detail="Patient authentication required")

    start_time_val = req.slot_id or req.start_time
    if not start_time_val:
        raise HTTPException(status_code=400, detail="Missing slot or start_time")

    try:
        dt_val = datetime.fromisoformat(start_time_val.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid start_time format")

    try:
        appt = BookingService.book_appointment(
            db,
            patient_id=user.patient_profile.id,
            doctor_id=req.doctor_id,
            start_time=dt_val,
            hold_id=req.hold_id,
            reason=req.reason,
            symptoms_raw=req.symptoms
        )
        return {
            "success": True,
            "data": {"id": appt.id, "status": appt.status.value, "start_time": appt.start_time.isoformat()},
            "appointment_id": appt.id,
            "message": "Appointment booked successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 3. AI Intake Compatibility Endpoint
@router.post("/api/intake/{appointment_id}")
@router.post("/api/v1/intake/{appointment_id}")
def intake_compat(
    appointment_id: int,
    req: IntakeCompatRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    require_appointment_user(request, db, appointment_id, UserRole.PATIENT)
    symptoms_text = req.symptoms or req.raw_symptoms or ""
    result = IntakeAgent.process_intake(symptoms_text)
    res_dict = result.model_dump()
    res_dict["questions"] = res_dict.get("adaptive_questions", [])
    res_dict["summary"] = res_dict.get("chief_complaint", "")

    ai_summary = AISummary(
        appointment_id=appointment_id,
        summary_type=AISummaryType.INTAKE_SUMMARY,
        content=res_dict,
        urgency=result.urgency
    )
    db.add(ai_summary)
    db.commit()

    return {
        "success": True,
        "data": res_dict,
        **res_dict,
        "message": "Intake processed"
    }

# 4. Doctor AI Copilot Brief Compatibility Endpoint
@router.get("/api/doctor/copilot/{appointment_id}")
@router.get("/api/v1/doctor/copilot/{appointment_id}")
def doctor_copilot_compat(
    appointment_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    appt = require_appointment_user(request, db, appointment_id, UserRole.DOCTOR)

    brief_data = DoctorBriefAgent.generate_brief(db, appt)
    b_dict = brief_data.model_dump()
    b_dict["history"] = b_dict.get("relevant_history", [])
    b_dict["questions"] = b_dict.get("suggested_questions", [])

    ai_summary = AISummary(
        appointment_id=appt.id,
        summary_type=AISummaryType.DOCTOR_BRIEF,
        content=b_dict,
        urgency=brief_data.urgency
    )
    db.add(ai_summary)
    db.commit()

    return {
        "success": True,
        "data": b_dict,
        **b_dict,
        "message": "Doctor brief fetched"
    }

# 5. Finalize Consultation Compatibility Endpoint
@router.post("/api/doctor/consultation/{appointment_id}/finalize")
@router.post("/api/v1/doctor/consultation/{appointment_id}/finalize")
def finalize_consultation_compat(
    appointment_id: int,
    req: FinalizeConsultationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    appt = require_appointment_user(request, db, appointment_id, UserRole.DOCTOR)

    med_raw = None
    if req.medication and req.medication.get("name"):
        m = req.medication
        rx_create = PrescriptionCreate(
            medication=m["name"],
            dosage=m.get("dosage") or "500mg",
            frequency=m.get("frequency") or "Twice daily",
            duration=m.get("duration") or "7 days",
            instructions=m.get("instructions") or None
        )
        med_obj = MedicationService.create_prescription(
            db,
            appointment_id=appointment_id,
            req=rx_create
        )
        med_raw = f"{med_obj.medication} ({med_obj.dosage})"

    summary = VisitSummaryAgent.generate_summary(req.clinical_notes, med_raw)
    ai_summary = AISummary(
        appointment_id=appointment_id,
        summary_type=AISummaryType.VISIT_SUMMARY,
        content=summary.model_dump()
    )
    db.add(ai_summary)

    appt.status = AppointmentStatus.COMPLETED
    db.commit()

    return {
        "success": True,
        "data": summary.model_dump(),
        "message": "Consultation finalized"
    }

# 6. Medication Adherence Compatibility Endpoint
@router.get("/api/medications/{prescription_id}/adherence")
def get_adherence_compat(
    prescription_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    require_prescription_patient(request, db, prescription_id)
    adh_data = MedicationService.calculate_adherence(db, prescription_id)
    res = adh_data.model_dump() if hasattr(adh_data, "model_dump") else dict(adh_data)
    pct = res.get("adherence_rate_pct", 100.0)
    res["adherence_percentage"] = pct
    res["percentage"] = pct
    res["taken"] = res.get("acknowledged", 0)
    return {
        "success": True,
        "data": res,
        **res,
        "message": "Adherence data fetched"
    }

# 7. Acknowledge Medication Schedule Compatibility Endpoint
@router.post("/api/medications/schedule/{schedule_id}/ack")
def ack_schedule_compat(
    schedule_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    schedule = db.query(MedicationSchedule).filter(MedicationSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Medication schedule not found")
    require_prescription_patient(request, db, schedule.prescription_id)
    sched = MedicationService.acknowledge_reminder(db, schedule_id)
    return {
        "success": True,
        "data": {"id": sched.id, "status": sched.status.value},
        "message": "Dose acknowledged"
    }

# 8. Doctor Leave Compatibility Endpoint
@router.post("/api/doctor/leave")
def doctor_leave_compat(
    req: DoctorLeaveCompatRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_user_from_request(request, db)
    if not user or user.role != UserRole.DOCTOR or not user.doctor_profile:
        raise HTTPException(status_code=401, detail="Doctor authentication required")

    from datetime import date
    try:
        s_date = date.fromisoformat(req.start_date)
        e_date = date.fromisoformat(req.end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")

    if e_date < s_date:
        raise HTTPException(status_code=400, detail="End date cannot be before start date")
    leave = DoctorService.apply_leave(
        db,
        user.doctor_profile.id,
        DoctorLeaveBase(start_date=s_date, end_date=e_date, reason=req.reason)
    )

    return {
        "success": True,
        "data": {"id": leave.id, "start_date": str(leave.start_date), "end_date": str(leave.end_date)},
        "message": "Leave submitted successfully"
    }

# 9. Admin Delete Doctor Compatibility Endpoint
@router.delete("/api/admin/doctors/{doctor_id}")
def admin_delete_doctor_compat(
    doctor_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_user_from_request(request, db)
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=401, detail="Admin authentication required")

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    db.delete(doctor)
    db.commit()

    return {
        "success": True,
        "data": None,
        "message": "Doctor removed successfully"
    }
