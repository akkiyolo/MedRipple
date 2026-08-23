from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.patient_service import PatientService
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.followup import FollowUp
from app.models.care_plan import CarePlan
from app.schemas.patient import PatientUpdate

router = APIRouter(prefix="/patients", tags=["Patient Portal"])

@router.get("/me")
def get_my_patient_profile(user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    patient = PatientService.get_patient_by_user_id(db, user.id)
    return {"success": True, "data": {"id": patient.id, "name": patient.name, "dob": str(patient.date_of_birth), "phone": patient.phone, "gender": patient.gender}, "message": "Patient profile fetched"}

@router.patch("/me")
def update_my_patient_profile(update_data: PatientUpdate, user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    patient = PatientService.get_patient_by_user_id(db, user.id)
    if update_data.name:
        patient.name = update_data.name
    if update_data.date_of_birth:
        patient.date_of_birth = update_data.date_of_birth
    if update_data.phone:
        patient.phone = update_data.phone
    if update_data.gender:
        patient.gender = update_data.gender
    if update_data.preferences:
        patient.preferences = update_data.preferences
    db.commit()
    db.refresh(patient)
    return {"success": True, "data": {"id": patient.id, "name": patient.name}, "message": "Patient profile updated"}

@router.get("/me/appointments")
def get_my_appointments(user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    patient = PatientService.get_patient_by_user_id(db, user.id)
    appts = db.query(Appointment).filter(Appointment.patient_id == patient.id).order_by(Appointment.start_time.desc()).all()
    results = []
    for a in appts:
        results.append({
            "id": a.id,
            "doctor_name": a.doctor.name,
            "specialization": a.doctor.specialization,
            "start_time": a.start_time.isoformat(),
            "end_time": a.end_time.isoformat(),
            "status": a.status.value,
            "reason": a.reason
        })
    return {"success": True, "data": results, "message": "Appointments fetched"}

@router.get("/me/timeline")
def get_my_longitudinal_timeline(user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    patient = PatientService.get_patient_by_user_id(db, user.id)
    timeline = PatientService.get_longitudinal_timeline(db, patient.id)
    return {"success": True, "data": timeline, "message": "Patient timeline fetched"}

@router.get("/me/medications")
def get_my_medications(user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    patient = PatientService.get_patient_by_user_id(db, user.id)
    rxs = db.query(Prescription).join(Appointment).filter(Appointment.patient_id == patient.id).all()
    results = [{"id": rx.id, "medication": rx.medication, "dosage": rx.dosage, "frequency": rx.frequency, "duration": rx.duration, "instructions": rx.instructions} for rx in rxs]
    return {"success": True, "data": results, "message": "Medications fetched"}

@router.get("/me/care-plan")
def get_my_care_plan(user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    patient = PatientService.get_patient_by_user_id(db, user.id)
    cp = db.query(CarePlan).filter(CarePlan.patient_id == patient.id).order_by(CarePlan.created_at.desc()).first()
    data = cp.plan_data if cp else None
    return {"success": True, "data": data, "message": "Care plan fetched"}

@router.get("/me/followups")
def get_my_followups(user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    patient = PatientService.get_patient_by_user_id(db, user.id)
    fups = db.query(FollowUp).join(Appointment).filter(Appointment.patient_id == patient.id).all()
    results = [{"id": f.id, "due_date": str(f.due_date), "reason": f.reason, "status": f.status.value} for f in fups]
    return {"success": True, "data": results, "message": "Follow-ups fetched"}
