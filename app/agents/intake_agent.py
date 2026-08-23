from app.schemas.ai import SymptomIntakeAnalysis
from app.models.ai_summary import UrgencyLevel
from app.prompts.intake import INTAKE_SYSTEM_PROMPT
from app.services.ai_service import ai_service

class IntakeAgent:
    @staticmethod
    def process_intake(raw_symptoms: str, previous_answers: list[dict] = None) -> SymptomIntakeAnalysis:
        user_prompt = f"Patient Symptoms:\n{raw_symptoms}\n"
        if previous_answers:
            user_prompt += f"\nPrevious Clarifications:\n{previous_answers}\n"

        def fallback():
            return SymptomIntakeAnalysis(
                urgency=UrgencyLevel.LOW,
                chief_complaint=raw_symptoms[:100] if raw_symptoms else "General Health Consultation",
                symptoms=[raw_symptoms] if raw_symptoms else [],
                duration="Not specified",
                severity="Unspecified",
                adaptive_questions=["How long have you experienced these symptoms?", "Are you experiencing any other discomfort?"],
                clinical_context=f"Patient intake recorded: {raw_symptoms}"
            )

        return ai_service.generate_structured_output(
            system_prompt=INTAKE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=SymptomIntakeAnalysis,
            fallback_factory=fallback
        )
