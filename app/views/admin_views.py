from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus
from app.services.image_service import ImageService

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/admin", tags=["Web Views Admin"])

def check_admin(request: Request, db: Session):
    token = request.cookies.get("session_token")
    if not token: return None
    try:
        from app.core.security import decode_access_token
        payload = decode_access_token(token)
        if not payload: return None
        user = db.query(User).filter(User.id == int(payload.get("sub"))).first()
        if not user or user.role != UserRole.ADMIN: return None
        return user
    except Exception:
        return None

@router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = check_admin(request, db)
    if not user:
        return RedirectResponse(url="/login")

    patients_count = db.query(Patient).count()
    doctors = db.query(Doctor).all()
    appts_count = db.query(Appointment).count()
    cancelled_count = db.query(Appointment).filter(Appointment.status == AppointmentStatus.CANCELLED).count()
    avatar_url = ImageService.get_profile_image_url(user)

    return templates.TemplateResponse(request=request, name="admin/dashboard.html", context={
        "current_user": user,
        "total_patients": patients_count,
        "total_doctors": len(doctors),
        "doctors": doctors,
        "total_appointments": appts_count,
        "cancelled_appointments": cancelled_count,
        "user_avatar_url": avatar_url,
        "active_page": "admin"
    })
