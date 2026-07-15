"""Bus and seat models."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class Bus(Base):
    __tablename__ = "buses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    plaque: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    marque: Mapped[str | None] = mapped_column(String(80), nullable=True)
    modele: Mapped[str | None] = mapped_column(String(80), nullable=True)
    annee: Mapped[int | None] = mapped_column(Integer, nullable=True)
    couleur: Mapped[str | None] = mapped_column(String(40), nullable=True)
    capacite: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    layout: Mapped[str] = mapped_column(String(10), default="2-2", nullable=False)
    photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    date_achat: Mapped[date | None] = mapped_column(Date, nullable=True)
    statut: Mapped[str] = mapped_column(String(20), default="actif", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    seats = relationship("Seat", back_populates="bus", cascade="all, delete-orphan")
    routes = relationship("Route", back_populates="bus")
    tickets = relationship("Ticket", back_populates="bus")
    luggage_items = relationship("Luggage", back_populates="bus")
    drivers = relationship("Driver", back_populates="bus")


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("bus_id", "numero", name="uq_bus_seat"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bus_id: Mapped[int] = mapped_column(
        ForeignKey("buses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    numero: Mapped[int] = mapped_column(Integer, nullable=False)

    bus = relationship("Bus", back_populates="seats")
