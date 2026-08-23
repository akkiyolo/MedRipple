from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.appointment import Appointment, AppointmentStatus
from app.models.appointment_hold import AppointmentHold, HoldStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.symptom import Symptom
from app.core.exceptions import SlotUnavailableError, AppointmentConflictError, ResourceNotFoundError
from app.services.audit_service import AuditService

HOLD_DURATION_MINUTES = 5

def ensure_utc(dt: datetime) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

class BookingService:
    @staticmethod
    def hold_slot(db: Session, patient_id: int, doctor_id: int, start_time: datetime) -> AppointmentHold:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise ResourceNotFoundError(f"Doctor {doctor_id} not found")

        start_time = ensure_utc(start_time)
        end_time = start_time + timedelta(minutes=doctor.slot_duration)
        now_utc = datetime.now(timezone.utc)

        # Lock doctor row to serialize concurrent hold/booking requests for the same doctor
        db.query(Doctor).filter(Doctor.id == doctor_id).with_for_update().first()

        # Check existing appointments for overlap
        conflicting_appt = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.HELD, AppointmentStatus.CONFIRMED, AppointmentStatus.RESCHEDULED]),
            Appointment.start_time < end_time,
            Appointment.end_time > start_time
        ).first()

        if conflicting_appt:
            raise SlotUnavailableError("The selected appointment slot is already booked.")

        # Check existing active holds for overlap
        conflicting_hold = db.query(AppointmentHold).filter(
            AppointmentHold.doctor_id == doctor_id,
            AppointmentHold.status == HoldStatus.HELD,
            AppointmentHold.hold_expires_at > now_utc,
            AppointmentHold.start_time < end_time,
            AppointmentHold.end_time > start_time,
            AppointmentHold.patient_id != patient_id
        ).first()

        if conflicting_hold:
            raise SlotUnavailableError("The selected slot is currently being held by another patient.")

        # Create hold
        hold_expires_at = now_utc + timedelta(minutes=HOLD_DURATION_MINUTES)
        hold = AppointmentHold(
            doctor_id=doctor_id,
            patient_id=patient_id,
            start_time=start_time,
            end_time=end_time,
            hold_expires_at=hold_expires_at,
            status=HoldStatus.HELD
        )
        db.add(hold)
        db.commit()
        db.refresh(hold)

        AuditService.log(db, action="SLOT_HELD", resource_type="AppointmentHold", user_id=patient_id, resource_id=str(hold.id))
        return hold

    @staticmethod
    def book_appointment(
        db: Session,
        patient_id: int,
        doctor_id: int,
        start_time: datetime,
        reason: str | None = None,
        hold_id: int | None = None,
        symptoms_raw: str | None = None
    ) -> Appointment:
        now_utc = datetime.now(timezone.utc)
        start_time = ensure_utc(start_time)
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise ResourceNotFoundError(f"Doctor {doctor_id} not found")

        end_time = start_time + timedelta(minutes=doctor.slot_duration)

        # Critical: Postgres Row Locking on Doctor to prevent race conditions
        db.query(Doctor).filter(Doctor.id == doctor_id).with_for_update().first()

        # Check existing conflicting appointments
        conflicting_appt = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.HELD, AppointmentStatus.CONFIRMED, AppointmentStatus.RESCHEDULED]),
            Appointment.start_time < end_time,
            Appointment.end_time > start_time
        ).first()

        if conflicting_appt:
            raise SlotUnavailableError("The selected slot is no longer available.")

        # Validate hold if hold_id provided
        if hold_id:
            hold = db.query(AppointmentHold).filter(AppointmentHold.id == hold_id).first()
            if hold:
                if hold.status == HoldStatus.HELD and ensure_utc(hold.hold_expires_at) >= now_utc:
                    hold.status = HoldStatus.CONFIRMED

        # Create appointment
        appt = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            start_time=start_time,
            end_time=end_time,
            status=AppointmentStatus.CONFIRMED,
            reason=reason
        )
        db.add(appt)
        db.flush()

        if symptoms_raw:
            symptom_entry = Symptom(
                appointment_id=appt.id,
                raw_text=symptoms_raw
            )
            db.add(symptom_entry)

        db.commit()
        db.refresh(appt)

        # Trigger background event workflow (email, calendar sync, AI doctor brief)
        from app.services.notification_service import NotificationService
        NotificationService.trigger_appointment_created_event(db, appt)
        
        # Sync to Google Calendar if configured
        from app.services.calendar_service import GoogleCalendarService
        GoogleCalendarService.create_event(db, appt.patient.user, appt)
        GoogleCalendarService.create_event(db, appt.doctor.user, appt)

        AuditService.log(db, action="APPOINTMENT_BOOKED", resource_type="Appointment", user_id=patient_id, resource_id=str(appt.id))
        return appt

    @staticmethod
    def cancel_appointment(db: Session, appointment_id: int, user_id: int) -> Appointment:
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            raise ResourceNotFoundError("Appointment not found")
        appt.status = AppointmentStatus.CANCELLED
        db.commit()
        db.refresh(appt)

        from app.services.notification_service import NotificationService
        NotificationService.trigger_appointment_cancelled_event(db, appt)

        AuditService.log(db, action="APPOINTMENT_CANCELLED", resource_type="Appointment", user_id=user_id, resource_id=str(appt.id))
        return appt

    @staticmethod
    def cleanup_expired_holds(db: Session) -> int:
        now_utc = datetime.now(timezone.utc)
        expired_holds = db.query(AppointmentHold).filter(
            AppointmentHold.status == HoldStatus.HELD,
            AppointmentHold.hold_expires_at < now_utc
        ).all()

        count = len(expired_holds)
        for h in expired_holds:
            h.status = HoldStatus.EXPIRED
        db.commit()
        return count
