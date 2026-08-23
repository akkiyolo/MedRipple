from app.schemas.ai import CarePlanData, CarePlanPhase
from app.prompts.care_plan import CARE_PLAN_SYSTEM_PROMPT
from app.services.ai_service import ai_service

class CarePlanAgent:
    @staticmethod
    def generate_care_plan(clinical_notes: str, prescriptions_str: str | None = None) -> CarePlanData:
        user_prompt = f"Clinical Context:\n{clinical_notes}\n"
        if prescriptions_str:
            user_prompt += f"Prescriptions:\n{prescriptions_str}\n"

        def fallback():
            return CarePlanData(
                title="Personalized Care Strategy",
                overview="Comprehensive treatment and recovery plan outlined by your physician.",
                phases=[
                    CarePlanPhase(day_range="Days 1–3", action_items=["Initiate prescribed medications.", "Rest and track symptoms."]),
                    CarePlanPhase(day_range="Days 4–7", action_items=["Continue medication course.", "Gradually resume routine light activity."])
                ],
                warning_signs=["Persistent high fever", "Difficulty breathing", "Sudden increase in pain"],
                follow_up_timeline="Schedule follow-up evaluation in 14 days."
            )

        return ai_service.generate_structured_output(
            system_prompt=CARE_PLAN_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=CarePlanData,
            fallback_factory=fallback
        )
