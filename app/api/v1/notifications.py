from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.notification import Notification, NotificationStatus
from app.services.notification_service import NotificationService
from app.core.dependencies import require_role
from app.models.user import User, UserRole

router = APIRouter(prefix="/notifications", tags=["Notifications Reliability"])

@router.get("")
def list_notifications(user: User = Depends(require_role(UserRole.ADMIN)), db: Session = Depends(get_db)):
    notifs = db.query(Notification).order_by(Notification.created_at.desc()).limit(50).all()
    results = [{
        "id": n.id,
        "recipient": n.recipient,
        "channel": n.channel.value,
        "type": n.type,
        "status": n.status.value,
        "attempt_count": n.attempt_count,
        "last_attempt_at": n.last_attempt_at.isoformat() if n.last_attempt_at else None,
        "error_message": n.error_message
    } for n in notifs]
    return {"success": True, "data": results, "message": "Notifications fetched"}

@router.post("/{notification_id}/retry")
def retry_notification(notification_id: int, user: User = Depends(require_role(UserRole.ADMIN)), db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        return {"success": False, "error": {"code": "RESOURCE_NOT_FOUND", "message": "Notification not found"}}
    notif.attempt_count += 1
    success = NotificationService.send_email(notif.recipient, f"Retry: {notif.type}", f"Notification message body for {notif.type}")
    notif.status = NotificationStatus.SENT if success else NotificationStatus.RETRYING
    db.commit()
    return {"success": True, "data": {"id": notif.id, "status": notif.status.value}, "message": "Notification retry executed"}

@router.get("/status")
def get_notification_system_status(user: User = Depends(require_role(UserRole.ADMIN)), db: Session = Depends(get_db)):
    pending = db.query(Notification).filter(Notification.status == NotificationStatus.PENDING).count()
    sent = db.query(Notification).filter(Notification.status == NotificationStatus.SENT).count()
    failed = db.query(Notification).filter(Notification.status == NotificationStatus.FAILED).count()
    retrying = db.query(Notification).filter(Notification.status == NotificationStatus.RETRYING).count()
    return {
        "success": True,
        "data": {
            "pending": pending,
            "sent": sent,
            "failed": failed,
            "retrying": retrying
        },
        "message": "Notification status metrics fetched"
    }
