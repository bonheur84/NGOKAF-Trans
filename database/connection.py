"""MySQL connection bootstrap — creates database if missing."""
from __future__ import annotations

import logging
import re

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config.settings import settings
from database.session import SessionLocal

logger = logging.getLogger(__name__)

_engine: Engine | None = None


def create_database_if_needed() -> None:
    """Ensure the target MySQL database exists."""
    if not settings.DB_CREATE_DATABASE:
        return
    if not re.fullmatch(r"[A-Za-z0-9_]+", settings.DB_NAME):
        raise ValueError("DB_NAME ne doit contenir que des lettres, chiffres et _.")
    server_engine = create_engine(
        settings.server_url,
        pool_pre_ping=True,
        isolation_level="AUTOCOMMIT",
        connect_args=settings.database_connect_args,
    )
    db_name = settings.DB_NAME
    with server_engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    server_engine.dispose()
    logger.info("Database ready: %s", db_name)


def get_engine() -> Engine:
    """Return the shared SQLAlchemy engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20,
            pool_timeout=settings.DB_CONNECT_TIMEOUT,
            connect_args=settings.database_connect_args,
            echo=False,
        )
        SessionLocal.configure(bind=_engine)
    return _engine


def init_connection() -> Engine:
    """Create DB if needed and return engine bound to it."""
    create_database_if_needed()
    return get_engine()
