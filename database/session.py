"""SQLAlchemy base and session helpers."""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False)


def get_session():
    """Create a new DB session (ensures engine is bound)."""
    from database.connection import get_engine

    get_engine()
    return SessionLocal()
