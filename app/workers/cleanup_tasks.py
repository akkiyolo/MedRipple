from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.booking_service import BookingService
from app.services.followup_service import FollowUpService
from app.core.logging import logger

@celery_app.task(name="app.workers.cleanup_tasks.purge_expired_holds_and_update_overdues")
def purge_expired_holds_and_update_overdues():
    db = SessionLocal()
    try:
        holds_cleaned = BookingService.cleanup_expired_holds(db)
        overdues_marked = FollowUpService.update_overdue_status(db)
        logger.info(f"[Celery Cleanup] Expired holds cleaned: {holds_cleaned}, Overdues marked: {overdues_marked}")
        return {"holds_cleaned": holds_cleaned, "overdues_marked": overdues_marked}
    finally:
        db.close()
