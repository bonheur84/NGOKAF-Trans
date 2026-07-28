"""Expense model for financial tracking."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date_paiement: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    categorie: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    montant: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    mode_paiement: Mapped[str] = mapped_column(String(20), nullable=False, default="especes")
    fournisseur: Mapped[str] = mapped_column(String(150), nullable=True)
    piece_jointe: Mapped[str] = mapped_column(String(500), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    creator = relationship("User", backref="expenses")

    CATEGORIES = [
        "carburant",
        "entretien_bus",
        "frais_administratifs",
        "salaires",
        "location",
        "assurance",
        "autres",
    ]

    MODES_PAIEMENT = ["especes", "virement", "cheque", "carte"]
