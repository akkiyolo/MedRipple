from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.appointment import Appointment
from app.services.calendar_service import CalendarService
from app.core.logging import logger

@celery_app.task(name="app.workers.calendar_tasks.sync_calendar_event_background")
def sync_calendar_event_background(appointment_id: int):
    db = SessionLocal()
    try:
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if appt:
            CalendarService.sync_appointment_event(db, appt)
            logger.info(f"[Celery] Synced calendar event for appointment {appointment_id}")
            return True
        return False
    finally:
        db.close()
