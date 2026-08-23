from datetime import datetime, timezone
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.medication_schedule import MedicationSchedule, ReminderStatus
from app.services.notification_service import NotificationService
from app.core.logging import logger

@celery_app.task(name="app.workers.reminder_tasks.dispatch_due_medication_reminders")
def dispatch_due_medication_reminders():
    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        due_schedules = db.query(MedicationSchedule).filter(
            MedicationSchedule.status == ReminderStatus.PENDING,
            MedicationSchedule.scheduled_time <= now_utc
        ).all()

        dispatched = 0
        for sched in due_schedules:
            sched.status = ReminderStatus.SENT
            # Send notification
            rx = sched.prescription
            if rx and rx.appointment and rx.appointment.patient and rx.appointment.patient.user:
                NotificationService.create_and_dispatch_notification(
                    db,
                    recipient=rx.appointment.patient.user.email,
                    type_="MEDICATION_REMINDER",
                    subject=f"Medication Reminder: Take {rx.medication}",
                    body=f"Reminder to take {rx.medication} ({rx.dosage}) - {rx.instructions or 'As directed by physician'}.",
                    event_id=f"med_sched_{sched.id}"
                )
            dispatched += 1

        db.commit()
        logger.info(f"[Celery] Dispatched {dispatched} medication reminders.")
        return dispatched
    finally:
        db.close()
