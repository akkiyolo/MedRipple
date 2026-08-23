from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.core.logging import logger

class AuditService:
    @staticmethod
    def log(
        db: Session,
        action: str,
        resource_type: str,
        user_id: int | None = None,
        resource_id: str | None = None,
        metadata: dict | None = None
    ) -> AuditLog:
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_=metadata
        )
        db.add(audit_entry)
        try:
            db.commit()
            db.refresh(audit_entry)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record audit log: {e}")
        return audit_entry
