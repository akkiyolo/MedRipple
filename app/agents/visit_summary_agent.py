from app.schemas.ai import PatientFriendlyVisitSummary
from app.prompts.visit_summary import VISIT_SUMMARY_SYSTEM_PROMPT
from app.services.ai_service import ai_service

class VisitSummaryAgent:
    @staticmethod
    def generate_summary(clinical_notes: str, prescriptions_str: str | None = None) -> PatientFriendlyVisitSummary:
        user_prompt = f"Doctor Clinical Notes:\n{clinical_notes}\n"
        if prescriptions_str:
            user_prompt += f"\nPrescriptions:\n{prescriptions_str}\n"

        def fallback():
            return PatientFriendlyVisitSummary(
                patient_friendly_summary=f"During your visit, your doctor reviewed your symptoms and noted: {clinical_notes}",
                doctor_instructions=["Follow all prescribed instructions.", "Get adequate rest and hydration."],
                medication_guidance=[prescriptions_str] if prescriptions_str else [],
                lifestyle_and_recovery=["Monitor your symptoms over the next several days."],
                when_to_seek_urgent_care="If you experience severe difficulty breathing, high fever, or sudden pain worsening, seek emergency medical care immediately."
            )

        return ai_service.generate_structured_output(
            system_prompt=VISIT_SUMMARY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=PatientFriendlyVisitSummary,
            fallback_factory=fallback
        )
