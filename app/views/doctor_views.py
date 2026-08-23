from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.services.image_service import ImageService

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/doctor", tags=["Web Views Doctor"])

def check_doctor(request: Request, db: Session):
    token = request.cookies.get("session_token")
    if not token: return None, None
    try:
        from app.core.security import decode_access_token
        payload = decode_access_token(token)
        if not payload: return None, None
        user = db.query(User).filter(User.id == int(payload.get("sub"))).first()
        if not user or user.role != UserRole.DOCTOR: return None, None
        doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
        return user, doctor
    except Exception:
        return None, None

@router.get("/dashboard", response_class=HTMLResponse)
def doctor_dashboard(request: Request, db: Session = Depends(get_db)):
    user, doctor = check_doctor(request, db)
    if not user or not doctor:
        return RedirectResponse(url="/login")

    appointments = db.query(Appointment).filter(Appointment.doctor_id == doctor.id).order_by(Appointment.start_time.asc()).all()
    avatar_url = ImageService.get_profile_image_url(user)

    return templates.TemplateResponse(request=request, name="doctor/dashboard.html", context={
        "current_user": user,
        "doctor": doctor,
        "appointments": appointments,
        "today_appointments_count": len(appointments),
        "pending_briefs_count": len(appointments),
        "user_avatar_url": avatar_url,
        "active_page": "dashboard"
    })

@router.get("/copilot/{appointment_id}", response_class=HTMLResponse)
def doctor_copilot(appointment_id: int, request: Request, db: Session = Depends(get_db)):
    user, doctor = check_doctor(request, db)
    if not user or not doctor:
        return RedirectResponse(url="/login")

    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        return RedirectResponse(url="/doctor/dashboard")

    avatar_url = ImageService.get_profile_image_url(user)

    return templates.TemplateResponse(request=request, name="doctor/copilot.html", context={
        "current_user": user,
        "appointment": appt,
        "user_avatar_url": avatar_url,
        "active_page": "appointments"
    })

@router.get("/leave", response_class=HTMLResponse)
def doctor_leave(request: Request, db: Session = Depends(get_db)):
    user, doctor = check_doctor(request, db)
    if not user or not doctor:
        return RedirectResponse(url="/login")

    avatar_url = ImageService.get_profile_image_url(user)

    return templates.TemplateResponse(request=request, name="doctor/leave.html", context={
        "current_user": user,
        "doctor": doctor,
        "user_avatar_url": avatar_url,
        "active_page": "leave"
    })
