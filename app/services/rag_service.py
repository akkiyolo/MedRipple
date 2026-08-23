import json
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.patient_memory import PatientMemory, MemoryType
from app.models.appointment import Appointment
from app.models.symptom import Symptom
from app.models.prescription import Prescription
from app.models.clinical_note import ClinicalNote

class RAGService:
    @staticmethod
    def add_patient_memory(
        db: Session,
        patient_id: int,
        content: str,
        memory_type: MemoryType,
        source_id: str | None = None,
        metadata: dict | None = None
    ) -> PatientMemory:
        # Simple local vector representation (384 floats) or zero-vector placeholder
        # Can compute embedding using light hash vector or sentence transformers if present
        mock_embedding = [0.01 * ((i + len(content)) % 10) for i in range(384)]

        memory = PatientMemory(
            patient_id=patient_id,
            content=content,
            memory_type=memory_type,
            source_id=source_id,
            embedding=mock_embedding,
            metadata_=metadata
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory

    @staticmethod
    def query_patient_history(db: Session, patient_id: int, query: str, limit: int = 5) -> list[dict]:
        """
        Retrieves relevant historical patient records strictly filtered by patient_id.
        """
        # Strictly filter by patient_id to prevent cross-patient data leakage
        memories = db.query(PatientMemory).filter(
            PatientMemory.patient_id == patient_id
        ).order_by(PatientMemory.created_at.desc()).limit(limit).all()

        results = []
        for mem in memories:
            results.append({
                "id": mem.id,
                "memory_type": mem.memory_type.value,
                "content": mem.content,
                "created_at": mem.created_at.isoformat(),
                "source_id": mem.source_id
            })

        # Also pull recent clinical notes & prescriptions if memories table is sparse
        if len(results) < limit:
            appts = db.query(Appointment).filter(Appointment.patient_id == patient_id).order_by(Appointment.start_time.desc()).limit(3).all()
            for appt in appts:
                for note in appt.clinical_notes:
                    results.append({
                        "id": f"note_{note.id}",
                        "memory_type": "CLINICAL_NOTE",
                        "content": note.notes,
                        "created_at": note.created_at.isoformat(),
                        "source_id": str(appt.id)
                    })
                for rx in appt.prescriptions:
                    results.append({
                        "id": f"rx_{rx.id}",
                        "memory_type": "MEDICATION",
                        "content": f"{rx.medication} ({rx.dosage}, {rx.frequency})",
                        "created_at": rx.created_at.isoformat(),
                        "source_id": str(appt.id)
                    })

        return results[:limit]
