"""Luggage controller."""
from __future__ import annotations

from database.session import get_session
from services import luggage_service
from services.print_service import print_luggage


class BagagesController:
    def stats_today(self):
        session = get_session()
        try:
            return luggage_service.today_luggage_stats(session)
        finally:
            session.close()

    def register(self, **kwargs):
        session = get_session()
        try:
            return luggage_service.register_luggage(session, **kwargs)
        finally:
            session.close()

    def update_status(self, luggage_id: int, statut: str, user_id=None):
        session = get_session()
        try:
            return luggage_service.update_luggage_status(session, luggage_id, statut, user_id)
        finally:
            session.close()

    def print_label(self, item, user_id=None, preview_only=False):
        return print_luggage(item, user_id, preview_only)
