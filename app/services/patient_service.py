from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.symptom import Symptom
from app.models.prescription import Prescription
from app.models.followup import FollowUp
from app.models.care_plan import CarePlan
from app.models.clinical_note import ClinicalNote
from app.models.ai_summary import AISummary
from app.core.exceptions import ResourceNotFoundError

class PatientService:
    @staticmethod
    def get_patient_by_user_id(db: Session, user_id: int) -> Patient:
        patient = db.query(Patient).filter(Patient.user_id == user_id).first()
        if not patient:
            raise ResourceNotFoundError("Patient profile not found")
        return patient

    @classmethod
    def get_longitudinal_timeline(cls, db: Session, patient_id: int) -> list[dict]:
        timeline_events = []

        # 1. Appointments & Symptoms
        appointments = db.query(Appointment).filter(Appointment.patient_id == patient_id).order_by(Appointment.start_time.desc()).all()
        for appt in appointments:
            timeline_events.append({
                "timestamp": appt.start_time.isoformat(),
                "event_type": "APPOINTMENT",
                "title": f"Appointment with Dr. {appt.doctor.name}",
                "description": f"Status: {appt.status.value}. Reason: {appt.reason or 'N/A'}",
                "data": {"appointment_id": appt.id, "doctor_id": appt.doctor_id, "status": appt.status.value}
            })

            for symptom in appt.symptoms:
                timeline_events.append({
                    "timestamp": symptom.created_at.isoformat(),
                    "event_type": "SYMPTOM_INTAKE",
                    "title": "Symptom Intake Recorded",
                    "description": symptom.raw_text,
                    "data": {"symptom_id": symptom.id, "structured": symptom.structured_data}
                })

            for note in appt.clinical_notes:
                timeline_events.append({
                    "timestamp": note.created_at.isoformat(),
                    "event_type": "CLINICAL_NOTE",
                    "title": "Doctor Clinical Notes",
                    "description": note.notes[:150] + "..." if len(note.notes) > 150 else note.notes,
                    "data": {"note_id": note.id}
                })

            for rx in appt.prescriptions:
                timeline_events.append({
                    "timestamp": rx.created_at.isoformat(),
                    "event_type": "PRESCRIPTION",
                    "title": f"Prescribed {rx.medication}",
                    "description": f"Dosage: {rx.dosage}, Frequency: {rx.frequency}, Duration: {rx.duration}",
                    "data": {"prescription_id": rx.id}
                })

            for fup in appt.followups:
                timeline_events.append({
                    "timestamp": fup.created_at.isoformat(),
                    "event_type": "FOLLOWUP_CREATED",
                    "title": f"Follow-up Scheduled (Due: {fup.due_date})",
                    "description": fup.reason,
                    "data": {"followup_id": fup.id, "status": fup.status.value}
                })

            for cp in appt.care_plans:
                timeline_events.append({
                    "timestamp": cp.created_at.isoformat(),
                    "event_type": "CARE_PLAN",
                    "title": "Care Plan Established",
                    "description": cp.plan_data.get("overview", "Structured Care Plan"),
                    "data": {"care_plan_id": cp.id}
                })

        # Sort all timeline events by timestamp descending
        timeline_events.sort(key=lambda x: x["timestamp"], reverse=True)
        return timeline_events
