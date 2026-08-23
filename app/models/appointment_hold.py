from datetime import datetime, timezone
import enum
from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class HoldStatus(str, enum.Enum):
    HELD = "HELD"
    EXPIRED = "EXPIRED"
    RELEASED = "RELEASED"
    CONFIRMED = "CONFIRMED"

class AppointmentHold(Base):
    __tablename__ = "appointment_holds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hold_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[HoldStatus] = mapped_column(Enum(HoldStatus), default=HoldStatus.HELD, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

__table_args__ = (
    Index("idx_hold_doctor_time", "doctor_id", "start_time", "status"),
)
