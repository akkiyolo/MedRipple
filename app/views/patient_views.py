from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.medication_schedule import MedicationSchedule, ReminderStatus
from app.models.followup import FollowUp
from app.models.care_plan import CarePlan
from app.services.patient_service import PatientService
from app.services.image_service import ImageService

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/patient", tags=["Web Views Patient"])

def check_patient(request: Request, db: Session):
    token = request.cookies.get("session_token")
    if not token:
        return None, None
    try:
        from app.core.security import decode_access_token
        payload = decode_access_token(token)
        if not payload: return None, None
        user = db.query(User).filter(User.id == int(payload.get("sub"))).first()
        if not user or user.role != UserRole.PATIENT: return None, None
        patient = db.query(Patient).filter(Patient.user_id == user.id).first()
        return user, patient
    except Exception:
        return None, None

@router.get("/dashboard", response_class=HTMLResponse)
def patient_dashboard(request: Request, db: Session = Depends(get_db)):
    user, patient = check_patient(request, db)
    if not user or not patient:
        return RedirectResponse(url="/login")

    now_utc = datetime.now(timezone.utc)
    appointments = db.query(Appointment).filter(Appointment.patient_id == patient.id).order_by(Appointment.start_time.desc()).all()
    next_appt = db.query(Appointment).filter(Appointment.patient_id == patient.id, Appointment.start_time >= now_utc).order_by(Appointment.start_time.asc()).first()
    rxs_count = db.query(Prescription).join(Appointment).filter(Appointment.patient_id == patient.id).count()
    fups_count = db.query(FollowUp).join(Appointment).filter(Appointment.patient_id == patient.id).count()

    avatar_url = ImageService.get_profile_image_url(user)

    return templates.TemplateResponse(request=request, name="patient/dashboard.html", context={
        "current_user": user,
        "patient": patient,
        "appointments": appointments,
        "next_appointment": next_appt,
        "active_medications_count": rxs_count,
        "upcoming_followups_count": fups_count,
        "memory_records_count": len(appointments) * 2,
        "user_avatar_url": avatar_url,
        "active_page": "dashboard"
    })

@router.get("/doctors", response_class=HTMLResponse)
def patient_doctors(request: Request, db: Session = Depends(get_db)):
    user, patient = check_patient(request, db)
    if not user:
        return RedirectResponse(url="/login")

    doctors = db.query(Doctor).all()
    for doctor in doctors:
        doctor.profile_image_url = ImageService.get_profile_image_url(doctor.user)
    avatar_url = ImageService.get_profile_image_url(user)

    return templates.TemplateResponse(request=request, name="patient/doctors.html", context={
        "current_user": user,
        "doctors": doctors,
        "user_avatar_url": avatar_url,
        "active_page": "doctors"
    })

@router.get("/intake/{appointment_id}", response_class=HTMLResponse)
def patient_intake(appointment_id: int, request: Request, db: Session = Depends(get_db)):
    user, patient = check_patient(request, db)
    if not user:
        return RedirectResponse(url="/login")

    avatar_url = ImageService.get_profile_image_url(user)

    return templates.TemplateResponse(request=request, name="patient/intake.html", context={
        "current_user": user,
        "appointment_id": appointment_id,
        "user_avatar_url": avatar_url,
        "active_page": "appointments"
    })

@router.get("/timeline", response_class=HTMLResponse)
def patient_timeline(request: Request, db: Session = Depends(get_db)):
    user, patient = check_patient(request, db)
    if not user or not patient:
        return RedirectResponse(url="/login")

    timeline = PatientService.get_longitudinal_timeline(db, patient.id)
    avatar_url = ImageService.get_profile_image_url(user)

    return templates.TemplateResponse(request=request, name="patient/timeline.html", context={
        "current_user": user,
        "timeline": timeline,
        "user_avatar_url": avatar_url,
        "active_page": "timeline"
    })

@router.get("/medications", response_class=HTMLResponse)
def patient_medications(request: Request, db: Session = Depends(get_db)):
    user, patient = check_patient(request, db)
    if not user or not patient:
        return RedirectResponse(url="/login")

    prescriptions = db.query(Prescription).join(Appointment).filter(Appointment.patient_id == patient.id).all()
    schedules = db.query(MedicationSchedule).join(Prescription).join(Appointment).filter(
        Appointment.patient_id == patient.id,
        MedicationSchedule.status == ReminderStatus.PENDING
    ).all()
    avatar_url = ImageService.get_profile_image_url(user)

    return templates.TemplateResponse(request=request, name="patient/medications.html", context={
        "current_user": user,
        "prescriptions": prescriptions,
        "upcoming_schedules": schedules,
        "user_avatar_url": avatar_url,
        "active_page": "medications"
    })

@router.get("/care-plan", response_class=HTMLResponse)
def patient_care_plan(request: Request, db: Session = Depends(get_db)):
    user, patient = check_patient(request, db)
    if not user or not patient:
        return RedirectResponse(url="/login")

    cp = db.query(CarePlan).filter(CarePlan.patient_id == patient.id).order_by(CarePlan.created_at.desc()).first()
    plan_data = cp.plan_data if cp else None
    avatar_url = ImageService.get_profile_image_url(user)

    return templates.TemplateResponse(request=request, name="patient/care_plan.html", context={
        "current_user": user,
        "care_plan": plan_data,
        "user_avatar_url": avatar_url,
        "active_page": "care_plan"
    })
