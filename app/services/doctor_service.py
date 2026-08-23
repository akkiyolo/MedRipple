from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.doctor import Doctor
from app.models.doctor_schedule import DoctorSchedule
from app.models.doctor_leave import DoctorLeave
from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.doctor import DoctorLeaveBase, DoctorUpdate
from app.services.schedule_service import ScheduleService
from app.services.audit_service import AuditService
from app.core.exceptions import ResourceNotFoundError

class DoctorService:
    @staticmethod
    def list_doctors(db: Session, specialization: str | None = None) -> list[Doctor]:
        query = db.query(Doctor)
        if specialization:
            query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
        return query.all()

    @staticmethod
    def get_doctor(db: Session, doctor_id: int) -> Doctor:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise ResourceNotFoundError(f"Doctor with ID {doctor_id} not found")
        return doctor

    @staticmethod
    def update_doctor_profile(db: Session, doctor_id: int, update_data: DoctorUpdate) -> Doctor:
        doctor = DoctorService.get_doctor(db, doctor_id)
        if update_data.name:
            doctor.name = update_data.name
        if update_data.specialization:
            doctor.specialization = update_data.specialization
        if update_data.license_number is not None:
            doctor.license_number = update_data.license_number
        if update_data.bio is not None:
            doctor.bio = update_data.bio
        if update_data.slot_duration:
            doctor.slot_duration = update_data.slot_duration
        db.commit()
        db.refresh(doctor)
        AuditService.log(db, action="DOCTOR_PROFILE_UPDATED", resource_type="Doctor", resource_id=str(doctor.id))
        return doctor

    @classmethod
    def apply_leave(cls, db: Session, doctor_id: int, leave_data: DoctorLeaveBase) -> DoctorLeave:
        doctor = cls.get_doctor(db, doctor_id)
        leave = DoctorLeave(
            doctor_id=doctor.id,
            start_date=leave_data.start_date,
            end_date=leave_data.end_date,
            reason=leave_data.reason
        )
        db.add(leave)
        db.commit()
        db.refresh(leave)

        # Handle leave conflicts
        cls.handle_leave_conflicts(db, doctor, leave)
        AuditService.log(db, action="DOCTOR_LEAVE_CREATED", resource_type="DoctorLeave", resource_id=str(leave.id))
        return leave

    @classmethod
    def handle_leave_conflicts(cls, db: Session, doctor: Doctor, leave: DoctorLeave):

        start_dt = datetime.combine(leave.start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(leave.end_date, datetime.max.time(), tzinfo=timezone.utc)

        affected_appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor.id,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED, AppointmentStatus.HELD]),
            Appointment.start_time >= start_dt,
            Appointment.end_time <= end_dt
        ).all()

        for appt in affected_appointments:
            appt.status = AppointmentStatus.RESCHEDULED
            # Find ranked alternative slots
            alternative_slots = cls.find_alternative_slots(db, doctor, appt)
            # Dispatch event / notification task for rescheduling
            from app.services.notification_service import NotificationService
            NotificationService.send_leave_reschedule_notification(db, appt, alternative_slots)

        db.commit()

    @classmethod
    def find_alternative_slots(cls, db: Session, doctor: Doctor, appt: Appointment) -> list[dict]:
        alternatives = []
        target_date = leave_end = appt.start_time.date() + timedelta(days=1)

        # 1. Search next 7 days for same doctor
        for d in range(1, 8):
            test_date = target_date + timedelta(days=d)
            slots = ScheduleService.get_available_slots(db, doctor.id, test_date)
            for s in slots:
                alternatives.append({"doctor_id": doctor.id, "doctor_name": doctor.name, "start_time": s["start_time"], "rank": 1})
                if len(alternatives) >= 3:
                    break
            if len(alternatives) >= 3:
                break

        # 2. Search other doctors in same specialization if needed
        if len(alternatives) < 3:
            other_doctors = db.query(Doctor).filter(
                Doctor.specialization == doctor.specialization,
                Doctor.id != doctor.id
            ).all()
            for od in other_doctors:
                for d in range(1, 4):
                    test_date = appt.start_time.date() + timedelta(days=d)
                    slots = ScheduleService.get_available_slots(db, od.id, test_date)
                    for s in slots:
                        alternatives.append({"doctor_id": od.id, "doctor_name": od.name, "start_time": s["start_time"], "rank": 2})
                        if len(alternatives) >= 5:
                            break
                    if len(alternatives) >= 5:
                        break

        return alternatives
