"""Auth controller."""
from __future__ import annotations

from database.session import get_session
from services import auth_service
from services.session_store import current_session


class AuthController:
    def login(self, username: str, password: str):
        session = get_session()
        try:
            user = auth_service.authenticate(session, username, password)
            if user:
                current_session.user = user
            return user
        finally:
            session.close()

    def logout(self) -> None:
        current_session.clear()

    def needs_setup(self) -> bool:
        session = get_session()
        try:
            return auth_service.count_users(session) == 0
        finally:
            session.close()
