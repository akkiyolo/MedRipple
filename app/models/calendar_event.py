from datetime import datetime, timezone
import enum
from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class CalendarSyncStatus(str, enum.Enum):
    SYNCED = "SYNCED"
    SYNC_PENDING = "SYNC_PENDING"
    FAILED = "FAILED"
    DELETED = "DELETED"

class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    appointment_id: Mapped[int] = mapped_column(Integer, ForeignKey("appointments.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    google_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[CalendarSyncStatus] = mapped_column(Enum(CalendarSyncStatus), default=CalendarSyncStatus.SYNC_PENDING, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    appointment = relationship("Appointment", back_populates="calendar_event")
