"""Initialize schema via SQLAlchemy metadata."""
from __future__ import annotations

import logging

from database.connection import init_connection
from database.migrate import migrate_schema
from database.session import Base, get_session

import models  # noqa: F401
from services.settings_service import ensure_default_settings
from services.auth_service import ensure_default_admin

logger = logging.getLogger(__name__)


def init_database() -> None:
    """Create all tables, migrate columns, seed admin and settings."""
    engine = init_connection()
    Base.metadata.create_all(bind=engine)
    migrate_schema(engine)
    logger.info("All tables created/verified.")
    session = get_session()
    try:
        ensure_default_settings(session)
        ensure_default_admin(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
