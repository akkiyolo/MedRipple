from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from app.models.followup import FollowUp, FollowUpStatus
from app.schemas.followup import FollowUpCreate
from app.core.exceptions import ResourceNotFoundError
from app.services.audit_service import AuditService

class FollowUpService:
    @staticmethod
    def create_followup(db: Session, req: FollowUpCreate) -> FollowUp:
        fup = FollowUp(
            appointment_id=req.appointment_id,
            due_date=req.due_date,
            reason=req.reason,
            status=FollowUpStatus.PENDING
        )
        db.add(fup)
        db.commit()
        db.refresh(fup)
        AuditService.log(db, action="FOLLOWUP_CREATED", resource_type="FollowUp", resource_id=str(fup.id))
        return fup

    @staticmethod
    def complete_followup(db: Session, followup_id: int) -> FollowUp:
        fup = db.query(FollowUp).filter(FollowUp.id == followup_id).first()
        if not fup:
            raise ResourceNotFoundError(f"Follow-up {followup_id} not found")
        fup.status = FollowUpStatus.COMPLETED
        db.commit()
        db.refresh(fup)
        AuditService.log(db, action="FOLLOWUP_COMPLETED", resource_type="FollowUp", resource_id=str(fup.id))
        return fup

    @staticmethod
    def update_overdue_status(db: Session) -> int:
        today = date.today()
        overdue_items = db.query(FollowUp).filter(
            FollowUp.status == FollowUpStatus.PENDING,
            FollowUp.due_date < today
        ).all()
        for item in overdue_items:
            item.status = FollowUpStatus.OVERDUE
        db.commit()
        return len(overdue_items)
