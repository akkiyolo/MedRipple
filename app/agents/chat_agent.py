import json
from typing import List, Dict, Any
from groq import Groq
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.patient_service import PatientService
from app.models.user import User, UserRole

client = Groq(api_key=settings.GROQ_API_KEY)

class ChatAgent:
    @staticmethod
    def _build_patient_context(db: Session, patient_id: int) -> str:
        timeline = PatientService.get_longitudinal_timeline(db, patient_id)
        
        context = "PATIENT HEALTH CONTEXT:\n"
        
        # Add Demographics (if we have them, otherwise just generic)
        context += f"Patient ID: {patient_id}\n\n"
        
        # Add active medications
        if "active_medications" in timeline and timeline["active_medications"]:
            context += "ACTIVE MEDICATIONS:\n"
            for med in timeline["active_medications"]:
                context += f"- {med['medication_name']} ({med['dosage']}, {med['frequency']})\n"
            context += "\n"
            
        # Add recent events
        if "timeline_events" in timeline and timeline["timeline_events"]:
            context += "RECENT EVENTS:\n"
            for event in timeline["timeline_events"][:5]: # Last 5 events
                context += f"- {event['date']}: {event['event_type']} - {event.get('description', '')}\n"
            context += "\n"
            
        return context

    @staticmethod
    def _clean_response(text: str) -> str:
        import re
        # Qwen models often prepend their chain of thought with "Here's a thinking process:" and end it with a checkmark
        cleaned = re.sub(r"(?s)^Here's a thinking process:.*?✅\s*", "", text)
        return cleaned.strip()

    @staticmethod
    def chat_with_patient_agent(db: Session, user: User, message: str, history: List[Dict[str, str]]) -> str:
        if not user.patient_profile:
            return "I'm sorry, but I couldn't find your patient profile."
            
        context = ChatAgent._build_patient_context(db, user.patient_profile.id)
        
        system_prompt = (
            "You are MedRipple's Personal Health Assistant, an empathetic, helpful, and highly knowledgeable AI. "
            "You are talking directly to the patient. "
            "Use the provided patient health context to give personalized, safe, and relevant answers. "
            "Always advise the patient to consult their doctor for serious medical decisions or emergencies. "
            "Keep your responses clear, supportive, and formatted cleanly. "
            "IMPORTANT: Do not include your internal thinking process, reasoning, or 'Here's a thinking process' block. Just output the final response directly.\n\n"
            f"{context}"
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        messages.append({"role": "user", "content": message})
        
        try:
            response = client.chat.completions.create(
                messages=messages,
                model="qwen/qwen3.6-27b",
                temperature=0.5,
                max_tokens=500
            )
            return ChatAgent._clean_response(response.choices[0].message.content)
        except Exception as e:
            from app.core.logging import logger
            logger.error(f"Error in Patient Chat Agent: {e}")
            return "I am currently experiencing technical difficulties. Please try again later."

    @staticmethod
    def chat_with_doctor_agent(db: Session, doctor_user: User, patient_id: int, message: str, history: List[Dict[str, str]]) -> str:
        context = ChatAgent._build_patient_context(db, patient_id)
        
        system_prompt = (
            "You are MedRipple's Clinical Copilot, an advanced AI designed to assist doctors with clinical decision support, "
            "chart review, and care planning. "
            "You are talking to a Doctor. Be concise, professional, and data-driven. "
            "Use the provided patient context to answer the doctor's questions accurately. "
            "If summarizing, use bullet points. "
            "IMPORTANT: Do not include your internal thinking process, reasoning, or 'Here's a thinking process' block. Just output the final response directly.\n\n"
            f"{context}"
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        messages.append({"role": "user", "content": message})
        
        try:
            response = client.chat.completions.create(
                messages=messages,
                model="qwen/qwen3.6-27b", # Updated model
                temperature=0.3,
                max_tokens=800
            )
            return ChatAgent._clean_response(response.choices[0].message.content)
        except Exception as e:
            from app.core.logging import logger
            logger.error(f"Error in Doctor Chat Agent: {e}")
            return "I am currently experiencing technical difficulties. Please try again later."
