from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.prescription import Prescription
from app.models.medication_schedule import MedicationSchedule, ReminderStatus
from app.schemas.medication import PrescriptionCreate, AdherenceReport
from app.core.exceptions import ResourceNotFoundError
from app.services.audit_service import AuditService

class MedicationService:
    @staticmethod
    def create_prescription(db: Session, appointment_id: int, req: PrescriptionCreate) -> Prescription:
        rx = Prescription(
            appointment_id=appointment_id,
            medication=req.medication,
            dosage=req.dosage,
            frequency=req.frequency,
            duration=req.duration,
            instructions=req.instructions
        )
        db.add(rx)
        db.commit()
        db.refresh(rx)

        # Automatically generate initial reminder schedule
        MedicationService.generate_reminder_schedule(db, rx.id)
        AuditService.log(db, action="PRESCRIPTION_CREATED", resource_type="Prescription", resource_id=str(rx.id))
        return rx

    @staticmethod
    def generate_reminder_schedule(db: Session, prescription_id: int) -> list[MedicationSchedule]:
        rx = db.query(Prescription).filter(Prescription.id == prescription_id).first()
        if not rx:
            raise ResourceNotFoundError(f"Prescription {prescription_id} not found")

        now = datetime.now(timezone.utc)
        schedules = []

        # Parse duration (default 7 days)
        days = 7
        if "day" in rx.duration.lower():
            try:
                days = int(''.join(filter(str.isdigit, rx.duration)))
            except ValueError:
                days = 7

        # Determine daily times based on frequency
        daily_times = [8]  # Default 08:00
        freq_lower = rx.frequency.lower()
        if "twice" in freq_lower or "2" in freq_lower or "12 hour" in freq_lower:
            daily_times = [8, 20]
        elif "three" in freq_lower or "3" in freq_lower or "8 hour" in freq_lower:
            daily_times = [8, 14, 20]
        elif "four" in freq_lower or "4" in freq_lower or "6 hour" in freq_lower:
            daily_times = [6, 12, 18, 22]

        for day_offset in range(days):
            target_date = (now + timedelta(days=day_offset)).date()
            for hour in daily_times:
                sched_dt = datetime.combine(target_date, datetime.min.time().replace(hour=hour), tzinfo=timezone.utc)
                if sched_dt > now:
                    sched = MedicationSchedule(
                        prescription_id=rx.id,
                        scheduled_time=sched_dt,
                        status=ReminderStatus.PENDING
                    )
                    db.add(sched)
                    schedules.append(sched)

        db.commit()
        return schedules

    @staticmethod
    def acknowledge_reminder(db: Session, schedule_id: int) -> MedicationSchedule:
        sched = db.query(MedicationSchedule).filter(MedicationSchedule.id == schedule_id).first()
        if not sched:
            raise ResourceNotFoundError(f"Medication schedule {schedule_id} not found")
        sched.status = ReminderStatus.ACKNOWLEDGED
        db.commit()
        db.refresh(sched)

        AuditService.log(db, action="REMINDER_ACKNOWLEDGED", resource_type="MedicationSchedule", resource_id=str(sched.id))
        return sched

    @staticmethod
    def calculate_adherence(db: Session, prescription_id: int) -> AdherenceReport:
        rx = db.query(Prescription).filter(Prescription.id == prescription_id).first()
        if not rx:
            raise ResourceNotFoundError(f"Prescription {prescription_id} not found")

        schedules = db.query(MedicationSchedule).filter(MedicationSchedule.prescription_id == prescription_id).all()
        total = len(schedules)
        acknowledged = sum(1 for s in schedules if s.status == ReminderStatus.ACKNOWLEDGED)
        missed = sum(1 for s in schedules if s.status == ReminderStatus.MISSED)
        pending = sum(1 for s in schedules if s.status == ReminderStatus.PENDING)

        rate = (acknowledged / total * 100.0) if total > 0 else 100.0

        # Care Drift Detection
        drift_flag = False
        drift_msg = None
        if missed >= 2:
            drift_flag = True
            drift_msg = f"Reminder acknowledgment gap detected: {missed} scheduled medication reminders were not acknowledged."

        return AdherenceReport(
            prescription_id=rx.id,
            medication=rx.medication,
            total_reminders=total,
            acknowledged=acknowledged,
            missed=missed,
            pending=pending,
            adherence_rate_pct=round(rate, 1),
            care_drift_flag=drift_flag,
            drift_message=drift_msg
        )
