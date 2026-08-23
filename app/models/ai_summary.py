from datetime import datetime, timezone
import enum
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class AISummaryType(str, enum.Enum):
    INTAKE_SUMMARY = "INTAKE_SUMMARY"
    DOCTOR_BRIEF = "DOCTOR_BRIEF"
    VISIT_SUMMARY = "VISIT_SUMMARY"
    CARE_PLAN_SUMMARY = "CARE_PLAN_SUMMARY"

class UrgencyLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AISummary(Base):
    __tablename__ = "ai_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    appointment_id: Mapped[int] = mapped_column(Integer, ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False, index=True)
    summary_type: Mapped[AISummaryType] = mapped_column(Enum(AISummaryType), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    urgency: Mapped[UrgencyLevel] = mapped_column(Enum(UrgencyLevel), default=UrgencyLevel.LOW, nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    appointment = relationship("Appointment", back_populates="ai_summaries")
