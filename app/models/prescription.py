from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    appointment_id: Mapped[int] = mapped_column(Integer, ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False, index=True)
    medication: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Twice daily", "Every 8 hours"
    duration: Mapped[str] = mapped_column(String(100), nullable=False)   # e.g., "7 days"
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    appointment = relationship("Appointment", back_populates="prescriptions")
    schedules = relationship("MedicationSchedule", back_populates="prescription", cascade="all, delete-orphan")
