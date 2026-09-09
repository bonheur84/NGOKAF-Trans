"""Agency (agence) model — Lubumbashi, Kolwezi, etc."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class Agency(Base):
    __tablename__ = "agencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    statut: Mapped[str] = mapped_column(String(20), default="actif", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    users = relationship("User", back_populates="agency")
    buses = relationship("Bus", back_populates="agency")
    drivers = relationship("Driver", back_populates="agency")
    routes = relationship("Route", back_populates="agency")

    @property
    def destination_city(self) -> str:
        """Return the other city for inter-agency routes."""
        if self.city.lower() == "lubumbashi":
            return "Kolwezi"
        if self.city.lower() == "kolwezi":
            return "Lubumbashi"
        return ""
