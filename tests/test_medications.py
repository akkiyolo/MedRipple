from datetime import datetime, timezone
from app.models.prescription import Prescription
from app.models.appointment import Appointment, AppointmentStatus
from app.services.medication_service import MedicationService

def test_medication_adherence_and_drift(db_session, test_patient_user, test_doctor_user):
    doctor_id = test_doctor_user.doctor_profile.id
    patient_id = test_patient_user.patient_profile.id

    # Create appointment
    appt = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        status=AppointmentStatus.COMPLETED
    )
    db_session.add(appt)
    db_session.flush()

    # Create prescription
    rx = Prescription(
        appointment_id=appt.id,
        medication="Inhaler Albuterol",
        dosage="2 puffs",
        frequency="Daily",
        duration="7 days"
    )
    db_session.add(rx)
    db_session.commit()

    # Generate schedule
    schedules = MedicationService.generate_reminder_schedule(db_session, rx.id)
    assert len(schedules) > 0

    # Calculate adherence
    report = MedicationService.calculate_adherence(db_session, rx.id)
    assert report.total_reminders == len(schedules)
    assert report.adherence_rate_pct == 0.0
