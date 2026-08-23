from sqlalchemy.orm import Session
from app.models.appointment import Appointment
from app.models.ai_summary import UrgencyLevel
from app.schemas.ai import DoctorBrief, DoctorBriefEvidence
from app.prompts.doctor_brief import DOCTOR_BRIEF_SYSTEM_PROMPT
from app.services.ai_service import ai_service
from app.agents.history_agent import HistoryAgent

class DoctorBriefAgent:
    @staticmethod
    def generate_brief(db: Session, appointment: Appointment) -> DoctorBrief:
        symptoms_str = "No initial intake recorded."
        if appointment.symptoms:
            symptoms_str = "\n".join([s.raw_text for s in appointment.symptoms])

        patient_history = HistoryAgent.retrieve_context(db, appointment.patient_id, query=symptoms_str)
        history_str = "\n".join([f"- [{h['created_at']}] ({h['memory_type']}): {h['content']}" for h in patient_history])

        user_prompt = f"""
Patient Name: {appointment.patient.name}
Current Symptoms Intake:
{symptoms_str}

Relevant Patient Historical Context:
{history_str if history_str else "No prior recorded visits."}
"""

        def fallback():
            return DoctorBrief(
                chief_complaint=appointment.reason or symptoms_str[:80],
                symptom_timeline=symptoms_str,
                urgency=UrgencyLevel.LOW,
                relevant_history=[h['content'] for h in patient_history[:2]],
                current_medications=[],
                suggested_questions=[
                    "How long have you experienced these symptoms?",
                    "Have you noticed any factors that relieve or worsen the condition?"
                ],
                evidence=[
                    DoctorBriefEvidence(
                        category="Intake",
                        source_date="Current Visit",
                        summary=symptoms_str[:150]
                    )
                ]
            )

        return ai_service.generate_structured_output(
            system_prompt=DOCTOR_BRIEF_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=DoctorBrief,
            fallback_factory=fallback
        )
