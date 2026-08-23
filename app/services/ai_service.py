import json
import os
import time
from typing import TypeVar, Type, Optional
from pydantic import BaseModel
import groq
from app.core.config import settings
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)

class AIService:
    def __init__(self):
        self._groq_client = None
        if settings.GROQ_API_KEY:
            try:
                self._groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                logger.warning(f"Groq API client initialization warning: {e}")

        # Configure LangSmith environment if set
        if settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
            os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT

    def generate_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        fallback_factory: callable,
        max_retries: int = 2
    ) -> T:
        trace_id = f"trace_{int(time.time()*1000)}"

        if not self._groq_client:
            logger.info(f"[{trace_id}] Groq client not configured or key missing. Returning fallback response.")
            return fallback_factory()

        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                completion = self._groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    timeout=15.0
                )
                latency = time.time() - start_time
                raw_content = completion.choices[0].message.content
                logger.info(f"[{trace_id}] Groq call success in {latency:.2f}s (model={settings.GROQ_MODEL})")

                # Parse JSON into Pydantic model
                data_dict = json.loads(raw_content)
                parsed_model = response_model.model_validate(data_dict)
                return parsed_model
            except Exception as e:
                logger.warning(f"[{trace_id}] Groq structured output attempt {attempt+1}/{max_retries+1} failed: {e}")
                if attempt == max_retries:
                    logger.error(f"[{trace_id}] Max retries reached. Triggering AI graceful fallback.")
                    return fallback_factory()
                time.sleep(0.5)

ai_service = AIService()
