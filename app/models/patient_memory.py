from datetime import datetime, timezone
import enum
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, Enum, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class MemoryType(str, enum.Enum):
    SYMPTOM = "SYMPTOM"
    MEDICATION = "MEDICATION"
    VISIT = "VISIT"
    FOLLOWUP = "FOLLOWUP"
    CARE_PLAN = "CARE_PLAN"
    CLINICAL_NOTE = "CLINICAL_NOTE"

class PatientMemory(Base):
    __tablename__ = "patient_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[MemoryType] = mapped_column(Enum(MemoryType), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding = mapped_column(Vector(384), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("Patient", back_populates="memories")

__table_args__ = (
    Index("idx_patient_memory_patient_type", "patient_id", "memory_type"),
)
