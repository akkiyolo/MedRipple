from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.notification_service import NotificationService
from app.core.logging import logger

@celery_app.task(name="app.workers.email_tasks.process_notification_retry_queue")
def process_notification_retry_queue():
    db = SessionLocal()
    try:
        count = NotificationService.retry_pending_notifications(db)
        logger.info(f"[Celery] Retried {count} pending email notifications.")
        return count
    finally:
        db.close()
