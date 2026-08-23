from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus
from app.services.booking_service import BookingService
from app.services.schedule_service import ScheduleService
from app.services.patient_service import PatientService
from app.schemas.appointment import AppointmentCreate, SlotHoldRequest, AppointmentReschedule

router = APIRouter(prefix="/appointments", tags=["Appointments Engine"])

def _can_access_appointment(db: Session, user: User, appt: Appointment) -> bool:
    if user.role == UserRole.ADMIN:
        return True
    if user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == user.id).first()
        return bool(patient and appt.patient_id == patient.id)
    if user.role == UserRole.DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
        return bool(doctor and appt.doctor_id == doctor.id)
    return False

@router.get("/slots")
def get_appointment_slots(doctor_id: int = Query(...), target_date: date = Query(...), db: Session = Depends(get_db)):
    slots = ScheduleService.get_available_slots(db, doctor_id, target_date)
    return {"success": True, "data": slots, "message": "Available slots fetched"}

@router.post("/hold")
def hold_appointment_slot(req: SlotHoldRequest, user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    patient = PatientService.get_patient_by_user_id(db, user.id)
    hold = BookingService.hold_slot(db, patient.id, req.doctor_id, req.start_time)
    return {
        "success": True,
        "data": {
            "id": hold.id,
            "doctor_id": hold.doctor_id,
            "patient_id": hold.patient_id,
            "start_time": hold.start_time.isoformat(),
            "end_time": hold.end_time.isoformat(),
            "hold_expires_at": hold.hold_expires_at.isoformat(),
            "status": hold.status.value
        },
        "message": "Slot held for 5 minutes"
    }

@router.post("")
def create_appointment(req: AppointmentCreate, user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    patient = PatientService.get_patient_by_user_id(db, user.id)
    appt = BookingService.book_appointment(
        db,
        patient_id=patient.id,
        doctor_id=req.doctor_id,
        start_time=req.start_time,
        reason=req.reason,
        hold_id=req.hold_id,
        symptoms_raw=req.symptoms
    )
    return {
        "success": True,
        "data": {
            "id": appt.id,
            "patient_id": appt.patient_id,
            "doctor_id": appt.doctor_id,
            "start_time": appt.start_time.isoformat(),
            "end_time": appt.end_time.isoformat(),
            "status": appt.status.value
        },
        "message": "Appointment booked successfully"
    }

@router.get("/{appointment_id}")
def get_appointment_by_id(appointment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        return {"success": False, "error": {"code": "RESOURCE_NOT_FOUND", "message": "Appointment not found"}}
    if not _can_access_appointment(db, current_user, appt):
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("You cannot access this appointment")
    return {
        "success": True,
        "data": {
            "id": appt.id,
            "patient_id": appt.patient_id,
            "doctor_id": appt.doctor_id,
            "patient_name": appt.patient.name,
            "doctor_name": appt.doctor.name,
            "start_time": appt.start_time.isoformat(),
            "end_time": appt.end_time.isoformat(),
            "status": appt.status.value,
            "reason": appt.reason
        },
        "message": "Appointment details fetched"
    }

@router.post("/{appointment_id}/cancel")
def cancel_appointment(appointment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        return {"success": False, "error": {"code": "RESOURCE_NOT_FOUND", "message": "Appointment not found"}}
    if not _can_access_appointment(db, current_user, appt):
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("You cannot cancel this appointment")
    appt = BookingService.cancel_appointment(db, appointment_id, current_user.id)
    return {"success": True, "data": {"id": appt.id, "status": appt.status.value}, "message": "Appointment cancelled"}

@router.post("/{appointment_id}/reschedule")
def reschedule_appointment(appointment_id: int, req: AppointmentReschedule, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        return {"success": False, "error": {"code": "RESOURCE_NOT_FOUND", "message": "Appointment not found"}}
    if not _can_access_appointment(db, current_user, appt):
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("You cannot reschedule this appointment")
    duration = appt.end_time - appt.start_time
    appt.start_time = req.new_start_time
    appt.end_time = req.new_start_time + duration
    appt.status = AppointmentStatus.RESCHEDULED
    db.commit()
    db.refresh(appt)
    return {"success": True, "data": {"id": appt.id, "start_time": appt.start_time.isoformat(), "status": appt.status.value}, "message": "Appointment rescheduled"}

@router.post("/{appointment_id}/complete")
def complete_appointment(appointment_id: int, current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)), db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        return {"success": False, "error": {"code": "RESOURCE_NOT_FOUND", "message": "Appointment not found"}}
    if not _can_access_appointment(db, current_user, appt):
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("You cannot complete this appointment")
    appt.status = AppointmentStatus.COMPLETED
    db.commit()
    db.refresh(appt)
    return {"success": True, "data": {"id": appt.id, "status": appt.status.value}, "message": "Appointment completed"}

@router.get("/{appointment_id}/timeline")
def get_appointment_timeline(appointment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        return {"success": False, "error": {"code": "RESOURCE_NOT_FOUND", "message": "Appointment not found"}}
    if not _can_access_appointment(db, current_user, appt):
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("You cannot access this appointment timeline")
    return {"success": True, "data": PatientService.get_longitudinal_timeline(db, appt.patient_id), "message": "Appointment timeline fetched"}

@router.delete("/{appointment_id}")
def delete_appointment(appointment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        return {"success": False, "error": {"code": "RESOURCE_NOT_FOUND", "message": "Appointment not found"}}
    if not _can_access_appointment(db, current_user, appt):
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("You cannot delete this appointment")
    if appt.status != AppointmentStatus.COMPLETED:
        return {"success": False, "error": {"code": "INVALID_STATUS", "message": "Only completed appointments can be deleted"}}
    
    db.delete(appt)
    db.commit()
    return {"success": True, "data": None, "message": "Appointment deleted successfully"}
