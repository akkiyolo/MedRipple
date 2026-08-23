from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.followup import FollowUp
from app.models.appointment import Appointment
from app.services.followup_service import FollowUpService
from app.schemas.followup import FollowUpCreate

router = APIRouter(prefix="/followups", tags=["Follow-up Engine"])

def _require_followup_access(user: User, fup: FollowUp) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.PATIENT and user.patient_profile and fup.appointment.patient_id == user.patient_profile.id:
        return
    if user.role == UserRole.DOCTOR and user.doctor_profile and fup.appointment.doctor_id == user.doctor_profile.id:
        return
    from app.core.exceptions import AuthorizationError
    raise AuthorizationError("Follow-up access forbidden")

@router.get("")
def list_followups(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fups = db.query(FollowUp).order_by(FollowUp.due_date.asc()).all()
    fups = [f for f in fups if user.role == UserRole.ADMIN or (user.role == UserRole.PATIENT and user.patient_profile and f.appointment.patient_id == user.patient_profile.id) or (user.role == UserRole.DOCTOR and user.doctor_profile and f.appointment.doctor_id == user.doctor_profile.id)]
    results = [{"id": f.id, "appointment_id": f.appointment_id, "due_date": str(f.due_date), "reason": f.reason, "status": f.status.value} for f in fups]
    return {"success": True, "data": results, "message": "Follow-ups fetched"}

@router.post("")
def create_followup(req: FollowUpCreate, user: User = Depends(require_role(UserRole.DOCTOR)), db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == req.appointment_id).first()
    if not appt or not user.doctor_profile or appt.doctor_id != user.doctor_profile.id:
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("Follow-up access forbidden")
    fup = FollowUpService.create_followup(db, req)
    return {"success": True, "data": {"id": fup.id, "due_date": str(fup.due_date), "reason": fup.reason, "status": fup.status.value}, "message": "Follow-up created"}

@router.get("/{followup_id}")
def get_followup_by_id(followup_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fup = db.query(FollowUp).filter(FollowUp.id == followup_id).first()
    if not fup:
        return {"success": False, "error": {"code": "RESOURCE_NOT_FOUND", "message": "Follow-up not found"}}
    _require_followup_access(user, fup)
    return {"success": True, "data": {"id": fup.id, "due_date": str(fup.due_date), "reason": fup.reason, "status": fup.status.value}, "message": "Follow-up details fetched"}

@router.post("/{followup_id}/complete")
def complete_followup(followup_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fup = db.query(FollowUp).filter(FollowUp.id == followup_id).first()
    if not fup:
        return {"success": False, "error": {"code": "RESOURCE_NOT_FOUND", "message": "Follow-up not found"}}
    _require_followup_access(user, fup)
    fup = FollowUpService.complete_followup(db, followup_id)
    return {"success": True, "data": {"id": fup.id, "status": fup.status.value}, "message": "Follow-up completed"}
