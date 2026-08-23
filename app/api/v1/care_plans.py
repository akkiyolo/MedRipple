from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.care_plan import CarePlan
from app.services.care_plan_service import CarePlanService
from app.schemas.care_plan import CarePlanCreate
from app.services.patient_service import PatientService

router = APIRouter(prefix="/care-plans", tags=["Care Plan Engine"])

@router.get("")
def list_care_plans(user: User = Depends(require_role(UserRole.PATIENT)), db: Session = Depends(get_db)):
    patient = PatientService.get_patient_by_user_id(db, user.id)
    plans = db.query(CarePlan).filter(CarePlan.patient_id == patient.id).all()
    results = [{"id": p.id, "appointment_id": p.appointment_id, "plan_data": p.plan_data, "created_at": p.created_at.isoformat()} for p in plans]
    return {"success": True, "data": results, "message": "Care plans fetched"}

@router.post("")
def create_care_plan(req: CarePlanCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    patient = PatientService.get_patient_by_user_id(db, user.id)
    cp = CarePlanService.create_care_plan(db, patient.id, req)
    return {"success": True, "data": {"id": cp.id, "plan_data": cp.plan_data}, "message": "Care plan created"}

@router.get("/{care_plan_id}")
def get_care_plan_by_id(care_plan_id: int, db: Session = Depends(get_db)):
    cp = db.query(CarePlan).filter(CarePlan.id == care_plan_id).first()
    if not cp:
        return {"success": False, "error": {"code": "RESOURCE_NOT_FOUND", "message": "Care plan not found"}}
    return {"success": True, "data": {"id": cp.id, "plan_data": cp.plan_data}, "message": "Care plan fetched"}
