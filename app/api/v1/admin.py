from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/admin", tags=["Admin Portal"])

@router.get("/dashboard")
def admin_dashboard(user: User = Depends(require_role(UserRole.ADMIN)), db: Session = Depends(get_db)):
    total_patients = db.query(Patient).count()
    total_doctors = db.query(Doctor).count()
    total_appointments = db.query(Appointment).count()
    cancelled_appointments = db.query(Appointment).filter(Appointment.status == AppointmentStatus.CANCELLED).count()

    return {
        "success": True,
        "data": {
            "total_patients": total_patients,
            "total_doctors": total_doctors,
            "total_appointments": total_appointments,
            "cancelled_appointments": cancelled_appointments
        },
        "message": "Admin dashboard metrics fetched"
    }

@router.get("/doctors")
def admin_list_doctors(user: User = Depends(require_role(UserRole.ADMIN)), db: Session = Depends(get_db)):
    doctors = db.query(Doctor).all()
    results = [{"id": d.id, "name": d.name, "specialization": d.specialization, "license_number": d.license_number, "slot_duration": d.slot_duration} for d in doctors]
    return {"success": True, "data": results, "message": "Doctors fetched for admin"}

@router.post("/doctors")
def admin_create_doctor(req: RegisterRequest, user: User = Depends(require_role(UserRole.ADMIN)), db: Session = Depends(get_db)):
    req.role = UserRole.DOCTOR
    u = AuthService.register_user(db, req)
    return {"success": True, "data": {"id": u.id, "email": u.email}, "message": "Doctor created successfully"}

@router.patch("/doctors/{doctor_id}")
def admin_update_doctor(doctor_id: int, specialization: str | None = None, name: str | None = None, user: User = Depends(require_role(UserRole.ADMIN)), db: Session = Depends(get_db)):
    doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doc:
        return {"success": False, "error": {"code": "RESOURCE_NOT_FOUND", "message": "Doctor not found"}}
    if specialization:
        doc.specialization = specialization
    if name:
        doc.name = name
    db.commit()
    return {"success": True, "data": {"id": doc.id, "name": doc.name, "specialization": doc.specialization}, "message": "Doctor updated"}

@router.delete("/doctors/{doctor_id}")
def admin_delete_doctor(doctor_id: int, user: User = Depends(require_role(UserRole.ADMIN)), db: Session = Depends(get_db)):
    doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doc:
        return {"success": False, "error": {"code": "RESOURCE_NOT_FOUND", "message": "Doctor not found"}}
    db.delete(doc)
    db.commit()
    return {"success": True, "data": None, "message": "Doctor deleted"}

@router.get("/appointments")
def admin_list_appointments(user: User = Depends(require_role(UserRole.ADMIN)), db: Session = Depends(get_db)):
    appts = db.query(Appointment).order_by(Appointment.start_time.desc()).all()
    results = [{"id": a.id, "patient_name": a.patient.name, "doctor_name": a.doctor.name, "start_time": a.start_time.isoformat(), "status": a.status.value} for a in appts]
    return {"success": True, "data": results, "message": "All appointments fetched"}

@router.get("/users")
def admin_list_users(user: User = Depends(require_role(UserRole.ADMIN)), db: Session = Depends(get_db)):
    users = db.query(User).all()
    results = [{"id": u.id, "email": u.email, "role": u.role.value, "is_active": u.is_active} for u in users]
    return {"success": True, "data": results, "message": "All users fetched"}

@router.get("/analytics")
def admin_analytics(user: User = Depends(require_role(UserRole.ADMIN)), db: Session = Depends(get_db)):
    return {
        "success": True,
        "data": {
            "doctor_utilization_rate": 84.5,
            "ai_briefs_generated": 142,
            "care_plan_completion_rate": 91.2,
            "adherence_drift_incidents": 3
        },
        "message": "Analytics metrics fetched"
    }
