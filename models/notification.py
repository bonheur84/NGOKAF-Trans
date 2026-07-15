"""Notification model with types and icons."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.session import Base


class NotificationType:
    """Notification types with icons."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    BUS_FULL = "bus_full"
    SEATS_LOW = "seats_low"
    BACKUP_SUCCESS = "backup_success"
    BACKUP_FAILED = "backup_failed"
    TICKET_CANCELLED = "ticket_cancelled"
    BAGAGE_REGISTERED = "bagage_registered"
    TRAJET_CANCELLED = "trajet_cancelled"
    CONDUCTEUR_UNAVAILABLE = "conducteur_unavailable"
    CRITICAL_ERROR = "critical_error"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notif_type: Mapped[str] = mapped_column(String(50), default=NotificationType.INFO, nullable=False)
    icon: Mapped[str] = mapped_column(String(50), default="bell", nullable=False)
    lu: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
