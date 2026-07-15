"""Ticket and cancellation models."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("date_vente", "numero", name="uq_ticket_day_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    date_vente: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    passenger_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), nullable=False, index=True)
    bus_id: Mapped[int] = mapped_column(ForeignKey("buses.id"), nullable=False, index=True)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    travel_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    qr_payload: Mapped[str] = mapped_column(Text, nullable=False)
    cashier_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    statut: Mapped[str] = mapped_column(String(20), default="vendu", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    route = relationship("Route", back_populates="tickets")
    bus = relationship("Bus", back_populates="tickets")
    cashier = relationship("User", back_populates="tickets")
    cancellation = relationship("TicketCancellation", back_populates="ticket", uselist=False)


class TicketCancellation(Base):
    __tablename__ = "ticket_cancellations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), unique=True, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cancelled_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    cancelled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    ticket = relationship("Ticket", back_populates="cancellation")
