"""Initialize schema via SQLAlchemy metadata."""
from __future__ import annotations

import logging

from database.connection import init_connection
from database.migrate import migrate_schema, migrate_nullable
from database.migrate_agencies import run_agency_migration
from database.session import Base, get_session

import models  # noqa: F401
from services.settings_service import ensure_default_settings
from services.auth_service import ensure_default_admin
from services.sale_service import ensure_ticket_luggage_codes

logger = logging.getLogger(__name__)


def init_database() -> None:
    """Create all tables, migrate columns, seed admin and settings."""
    engine = init_connection()
    Base.metadata.create_all(bind=engine)
    migrate_schema(engine)
    migrate_nullable(engine)
    logger.info("All tables created/verified.")
    session = get_session()
    try:
        run_agency_migration(engine, session)
        ensure_default_admin(session)
        ensure_ticket_luggage_codes(session)
        ensure_default_settings(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
