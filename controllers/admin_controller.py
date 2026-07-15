"""Thin admin controller helpers (optional facade)."""
from __future__ import annotations

from database.session import get_session
from services import admin_stats_service, bus_service, driver_service, user_admin_service


class AdminController:
    """Session-scoped helpers used by admin views when needed."""

    def with_session(self, fn):
        session = get_session()
        try:
            result = fn(session)
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
