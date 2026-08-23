from pydantic import BaseModel
from app.prompts.followup import FOLLOWUP_SYSTEM_PROMPT
from app.services.ai_service import ai_service
from app.models.ai_summary import UrgencyLevel

class FollowUpAnalysis(BaseModel):
    recommended_due_days: int = 14
    reason: str = "Routine follow-up evaluation"
    key_check_points: list[str] = []
    urgency_level: UrgencyLevel = UrgencyLevel.LOW

class FollowUpAgent:
    @staticmethod
    def analyze_followup(clinical_notes: str) -> FollowUpAnalysis:
        user_prompt = f"Clinical Notes:\n{clinical_notes}\n"

        def fallback():
            return FollowUpAnalysis(
                recommended_due_days=14,
                reason="Standard follow-up to evaluate treatment efficacy.",
                key_check_points=["Symptom resolution", "Medication tolerance"],
                urgency_level=UrgencyLevel.LOW
            )

        return ai_service.generate_structured_output(
            system_prompt=FOLLOWUP_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=FollowUpAnalysis,
            fallback_factory=fallback
        )
