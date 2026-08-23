from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.doctor_schedule import DoctorSchedule
from app.services.doctor_service import DoctorService
from app.services.schedule_service import ScheduleService
from app.schemas.doctor import DoctorLeaveBase, DoctorUpdate

router = APIRouter(prefix="/doctors", tags=["Doctors Portal"])

@router.get("")
def list_doctors(specialization: str | None = Query(default=None), db: Session = Depends(get_db)):
    doctors = DoctorService.list_doctors(db, specialization=specialization)
    results = [{"id": d.id, "name": d.name, "specialization": d.specialization, "bio": d.bio, "slot_duration": d.slot_duration} for d in doctors]
    return {"success": True, "data": results, "message": "Doctors fetched"}

@router.get("/me")
def get_my_doctor_profile(user: User = Depends(require_role(UserRole.DOCTOR)), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    return {"success": True, "data": {"id": doctor.id, "name": doctor.name, "specialization": doctor.specialization, "license_number": doctor.license_number, "slot_duration": doctor.slot_duration}, "message": "Doctor profile fetched"}

@router.patch("/me")
def update_my_doctor_profile(update_data: DoctorUpdate, user: User = Depends(require_role(UserRole.DOCTOR)), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    updated = DoctorService.update_doctor_profile(db, doctor.id, update_data)
    return {"success": True, "data": {"id": updated.id, "name": updated.name, "specialization": updated.specialization}, "message": "Doctor profile updated"}

@router.get("/me/appointments")
def get_doctor_appointments(user: User = Depends(require_role(UserRole.DOCTOR)), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    appts = db.query(Appointment).filter(Appointment.doctor_id == doctor.id).order_by(Appointment.start_time.asc()).all()
    results = [{
        "id": a.id,
        "patient_id": a.patient_id,
        "patient_name": a.patient.name,
        "start_time": a.start_time.isoformat(),
        "end_time": a.end_time.isoformat(),
        "status": a.status.value,
        "reason": a.reason
    } for a in appts]
    return {"success": True, "data": results, "message": "Doctor appointments fetched"}

@router.get("/me/schedule")
def get_doctor_schedule(user: User = Depends(require_role(UserRole.DOCTOR)), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    schedules = db.query(DoctorSchedule).filter(DoctorSchedule.doctor_id == doctor.id).all()
    results = [{"id": s.id, "day_of_week": s.day_of_week, "start_time": str(s.start_time), "end_time": str(s.end_time), "is_active": s.is_active} for s in schedules]
    return {"success": True, "data": results, "message": "Doctor schedule fetched"}

@router.post("/me/leave")
def apply_leave(leave_data: DoctorLeaveBase, user: User = Depends(require_role(UserRole.DOCTOR)), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    leave = DoctorService.apply_leave(db, doctor.id, leave_data)
    return {"success": True, "data": {"id": leave.id, "start_date": str(leave.start_date), "end_date": str(leave.end_date)}, "message": "Doctor leave created and conflicts processed"}

@router.get("/{doctor_id}/slots")
def get_doctor_available_slots(doctor_id: int, target_date: date = Query(...), db: Session = Depends(get_db)):
    slots = ScheduleService.get_available_slots(db, doctor_id, target_date)
    return {"success": True, "data": slots, "message": "Slots fetched"}

@router.get("/{doctor_id}")
def get_doctor_by_id(doctor_id: int, db: Session = Depends(get_db)):
    doctor = DoctorService.get_doctor(db, doctor_id)
    return {"success": True, "data": {"id": doctor.id, "name": doctor.name, "specialization": doctor.specialization, "bio": doctor.bio}, "message": "Doctor fetched"}
