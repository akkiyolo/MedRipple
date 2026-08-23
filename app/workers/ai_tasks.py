from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.appointment import Appointment
from app.agents.doctor_brief_agent import DoctorBriefAgent
from app.models.ai_summary import AISummary, AISummaryType
from app.core.logging import logger

@celery_app.task(name="app.workers.ai_tasks.generate_doctor_brief_background")
def generate_doctor_brief_background(appointment_id: int):
    db = SessionLocal()
    try:
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            return False

        brief = DoctorBriefAgent.generate_brief(db, appt)
        ai_summary = AISummary(
            appointment_id=appt.id,
            summary_type=AISummaryType.DOCTOR_BRIEF,
            content=brief.model_dump(),
            urgency=brief.urgency
        )
        db.add(ai_summary)
        db.commit()
        logger.info(f"[Celery] Generated doctor brief for appointment {appointment_id}")
        return True
    except Exception as e:
        logger.error(f"[Celery] Error generating doctor brief for appt {appointment_id}: {e}")
        return False
    finally:
        db.close()
