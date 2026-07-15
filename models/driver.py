"""Driver (conducteur) model."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    telephone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    adresse: Mapped[str | None] = mapped_column(String(255), nullable=True)
    numero_permis: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    date_expiration_permis: Mapped[date | None] = mapped_column(Date, nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bus_id: Mapped[int | None] = mapped_column(ForeignKey("buses.id"), nullable=True, index=True)
    statut: Mapped[str] = mapped_column(String(20), default="actif", nullable=False, index=True)
    disponibilite: Mapped[str] = mapped_column(String(30), default="disponible", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    bus = relationship("Bus", back_populates="drivers")
    routes = relationship("Route", back_populates="driver")

    @property
    def full_name(self) -> str:
        return f"{self.prenom} {self.nom}".strip()
