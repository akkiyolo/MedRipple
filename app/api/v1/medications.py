from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.prescription import Prescription
from app.models.medication_schedule import MedicationSchedule
from app.services.medication_service import MedicationService
from app.services.patient_service import PatientService

router = APIRouter(prefix="/medications", tags=["Medication Engine"])

def _require_prescription_owner(db: Session, user: User, prescription_id: int) -> Prescription:
    rx = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not rx:
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("Prescription not found")
    patient = PatientService.get_patient_by_user_id(db, user.id)
    if rx.appointment.patient_id != patient.id:
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("Prescription access forbidden")
    return rx

@router.get("")
def list_medications(user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    patient = PatientService.get_patient_by_user_id(db, user.id)
    rxs = db.query(Prescription).join(Prescription.appointment).filter(Prescription.appointment.has(patient_id=patient.id)).all()
    results = [{"id": r.id, "medication": r.medication, "dosage": r.dosage, "frequency": r.frequency, "duration": r.duration, "instructions": r.instructions} for r in rxs]
    return {"success": True, "data": results, "message": "Prescriptions fetched"}

@router.post("/{prescription_id}/generate-schedule")
def generate_schedule(prescription_id: int, user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    _require_prescription_owner(db, user, prescription_id)
    schedules = MedicationService.generate_reminder_schedule(db, prescription_id)
    results = [{"id": s.id, "scheduled_time": s.scheduled_time.isoformat(), "status": s.status.value} for s in schedules]
    return {"success": True, "data": results, "message": "Reminder schedule generated"}

@router.post("/{schedule_id}/acknowledge")
def acknowledge_reminder(schedule_id: int, user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    schedule = db.query(MedicationSchedule).filter(MedicationSchedule.id == schedule_id).first()
    if not schedule:
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("Medication schedule not found")
    _require_prescription_owner(db, user, schedule.prescription_id)
    sched = MedicationService.acknowledge_reminder(db, schedule_id)
    return {"success": True, "data": {"id": sched.id, "status": sched.status.value}, "message": "Reminder acknowledged"}

@router.get("/{prescription_id}/adherence")
def get_adherence_report(prescription_id: int, user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    _require_prescription_owner(db, user, prescription_id)
    report = MedicationService.calculate_adherence(db, prescription_id)
    return {"success": True, "data": report.model_dump(), "message": "Adherence report generated"}

@router.patch("/{prescription_id}")
def update_prescription(prescription_id: int, medication: str | None = None, dosage: str | None = None, user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)), db: Session = Depends(get_db)):
    rx = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not rx:
        return {"success": False, "error": {"code": "RESOURCE_NOT_FOUND", "message": "Prescription not found"}}
    if user.role == UserRole.DOCTOR and (not user.doctor_profile or rx.appointment.doctor_id != user.doctor_profile.id):
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("Prescription access forbidden")
    if medication:
        rx.medication = medication
    if dosage:
        rx.dosage = dosage
    db.commit()
    db.refresh(rx)
    return {"success": True, "data": {"id": rx.id, "medication": rx.medication, "dosage": rx.dosage}, "message": "Prescription updated"}
