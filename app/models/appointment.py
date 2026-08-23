from datetime import datetime, timezone
import enum
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class AppointmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    HELD = "HELD"
    CONFIRMED = "CONFIRMED"
    RESCHEDULED = "RESCHEDULED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    symptoms = relationship("Symptom", back_populates="appointment", cascade="all, delete-orphan")
    ai_summaries = relationship("AISummary", back_populates="appointment", cascade="all, delete-orphan")
    clinical_notes = relationship("ClinicalNote", back_populates="appointment", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="appointment", cascade="all, delete-orphan")
    followups = relationship("FollowUp", back_populates="appointment", cascade="all, delete-orphan")
    care_plans = relationship("CarePlan", back_populates="appointment", cascade="all, delete-orphan")
    calendar_event = relationship("CalendarEvent", back_populates="appointment", uselist=False, cascade="all, delete-orphan")

__table_args__ = (
    Index("idx_appointment_doctor_time", "doctor_id", "start_time"),
    Index("idx_appointment_patient_time", "patient_id", "start_time"),
)
