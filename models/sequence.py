"""Daily sequence counters."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.session import Base


class Sequence(Base):
    __tablename__ = "sequences"
    __table_args__ = (UniqueConstraint("name", "seq_date", name="uq_sequence_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    seq_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
