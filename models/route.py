"""Route (trajet) model."""
from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ville_depart: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ville_arrivee: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    heure_depart: Mapped[time] = mapped_column(Time, nullable=False)
    heure_arrivee: Mapped[time | None] = mapped_column(Time, nullable=True)
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    prix_indicatif: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    bus_id: Mapped[int] = mapped_column(ForeignKey("buses.id"), nullable=False, index=True)
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"), nullable=True, index=True)
    statut: Mapped[str] = mapped_column(String(20), default="actif", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    bus = relationship("Bus", back_populates="routes")
    driver = relationship("Driver", back_populates="routes")
    tickets = relationship("Ticket", back_populates="route")
    luggage_items = relationship("Luggage", back_populates="route")

    @property
    def label(self) -> str:
        h = self.heure_depart.strftime("%H:%M")
        price = ""
        if self.prix_indicatif is not None:
            price = f" - {int(self.prix_indicatif):,} FC".replace(",", " ")
        return f"{self.ville_depart} -> {self.ville_arrivee} ({h}){price}"

    @property
    def short_label(self) -> str:
        return f"{self.ville_depart} → {self.ville_arrivee}"
