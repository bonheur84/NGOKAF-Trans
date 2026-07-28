"""Luggage model."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class Luggage(Base):
    __tablename__ = "luggage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    sender_name: Mapped[str] = mapped_column(String(150), nullable=False)
    sender_phone: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    recipient_name: Mapped[str] = mapped_column(String(150), nullable=False)
    recipient_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    poids: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    valeur_declaree: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    route_id: Mapped[int | None] = mapped_column(ForeignKey("routes.id"), nullable=True, index=True)
    bus_id: Mapped[int | None] = mapped_column(ForeignKey("buses.id"), nullable=True, index=True)
    frais_base: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    supplement_poids: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    barcode: Mapped[str] = mapped_column(String(64), nullable=False)
    qr_payload: Mapped[str] = mapped_column(Text, nullable=False)
    cashier_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    statut: Mapped[str] = mapped_column(String(20), default="enregistre", nullable=False, index=True)
    fragile: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, index=True)

    route = relationship("Route", back_populates="luggage_items")
    bus = relationship("Bus", back_populates="luggage_items")
    cashier = relationship("User", back_populates="luggage_items")
