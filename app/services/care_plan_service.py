from sqlalchemy.orm import Session
from app.models.care_plan import CarePlan
from app.schemas.care_plan import CarePlanCreate
from app.core.exceptions import ResourceNotFoundError
from app.services.audit_service import AuditService

class CarePlanService:
    @staticmethod
    def create_care_plan(db: Session, patient_id: int, req: CarePlanCreate) -> CarePlan:
        cp = CarePlan(
            appointment_id=req.appointment_id,
            patient_id=patient_id,
            plan_data=req.plan_data.model_dump()
        )
        db.add(cp)
        db.commit()
        db.refresh(cp)
        AuditService.log(db, action="CARE_PLAN_CREATED", resource_type="CarePlan", user_id=patient_id, resource_id=str(cp.id))
        return cp

    @staticmethod
    def get_patient_care_plan(db: Session, patient_id: int) -> CarePlan | None:
        return db.query(CarePlan).filter(CarePlan.patient_id == patient_id).order_by(CarePlan.created_at.desc()).first()
