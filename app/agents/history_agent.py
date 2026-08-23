from sqlalchemy.orm import Session
from app.services.rag_service import RAGService

class HistoryAgent:
    @staticmethod
    def retrieve_context(db: Session, patient_id: int, query: str = "") -> list[dict]:
        return RAGService.query_patient_history(db, patient_id=patient_id, query=query, limit=5)
