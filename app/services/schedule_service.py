from datetime import datetime, date, time, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.doctor import Doctor
from app.models.doctor_schedule import DoctorSchedule
from app.models.doctor_leave import DoctorLeave
from app.models.appointment import Appointment, AppointmentStatus
from app.models.appointment_hold import AppointmentHold, HoldStatus

class ScheduleService:
    @staticmethod
    def get_available_slots(db: Session, doctor_id: int, target_date: date) -> list[dict]:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            return []

        # 1. Check if doctor is on leave on target_date
        leave = db.query(DoctorLeave).filter(
            DoctorLeave.doctor_id == doctor_id,
            DoctorLeave.start_date <= target_date,
            DoctorLeave.end_date >= target_date
        ).first()
        if leave:
            return []  # On leave

        # 2. Get schedule for day of week (0=Monday, 6=Sunday)
        weekday = target_date.weekday()
        schedules = db.query(DoctorSchedule).filter(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.day_of_week == weekday,
            DoctorSchedule.is_active == True
        ).all()

        if not schedules:
            return []

        slot_duration = timedelta(minutes=doctor.slot_duration)
        now_utc = datetime.now(timezone.utc)

        # 3. Fetch existing appointments for doctor on target_date
        start_of_day = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        end_of_day = datetime.combine(target_date, time.max, tzinfo=timezone.utc)

        existing_appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.HELD, AppointmentStatus.CONFIRMED, AppointmentStatus.RESCHEDULED]),
            Appointment.start_time >= start_of_day,
            Appointment.end_time <= end_of_day
        ).all()

        # 4. Fetch active holds
        active_holds = db.query(AppointmentHold).filter(
            AppointmentHold.doctor_id == doctor_id,
            AppointmentHold.status == HoldStatus.HELD,
            AppointmentHold.hold_expires_at > now_utc,
            AppointmentHold.start_time >= start_of_day,
            AppointmentHold.end_time <= end_of_day
        ).all()

        # Build list of unavailable time ranges
        blocked_ranges = []
        for appt in existing_appointments:
            blocked_ranges.append((appt.start_time, appt.end_time))
        for hold in active_holds:
            blocked_ranges.append((hold.start_time, hold.end_time))

        available_slots = []
        for sched in schedules:
            slot_start = datetime.combine(target_date, sched.start_time, tzinfo=timezone.utc)
            sched_end = datetime.combine(target_date, sched.end_time, tzinfo=timezone.utc)

            while slot_start + slot_duration <= sched_end:
                slot_end = slot_start + slot_duration

                # Skip past slots if target_date is today
                if slot_start > now_utc:
                    # Check overlap with blocked ranges
                    is_blocked = False
                    for b_start, b_end in blocked_ranges:
                        if not (slot_end <= b_start or slot_start >= b_end):
                            is_blocked = True
                            break

                    if not is_blocked:
                        available_slots.append({
                            "doctor_id": doctor_id,
                            "start_time": slot_start.isoformat(),
                            "end_time": slot_end.isoformat(),
                            "formatted_time": slot_start.strftime("%H:%M") + " - " + slot_end.strftime("%H:%M")
                        })

                slot_start = slot_end

        return available_slots
