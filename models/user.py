"""User model — caissier & administrateur."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    telephone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    adresse: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    role: Mapped[str] = mapped_column(String(30), default="caissier", nullable=False, index=True)
    statut: Mapped[str] = mapped_column(String(20), default="actif", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    tickets = relationship("Ticket", back_populates="cashier")
    luggage_items = relationship("Luggage", back_populates="cashier")

    @property
    def full_name(self) -> str:
        return f"{self.prenom} {self.nom}".strip()

    @property
    def is_admin(self) -> bool:
        return self.role == "administrateur"
