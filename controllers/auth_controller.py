"""Auth controller."""
from __future__ import annotations

from database.session import get_session
from services import auth_service
from services.agency_service import get_agency
from services.session_store import current_session
from config.settings import settings


class AuthController:
    def login(self, username: str, password: str):
        if settings.uses_remote_api:
            from models.agency import Agency
            from models.user import User
            from services.api_client import ApiClient

            result = ApiClient().login(username, password)
            payload = result.user
            user = User(
                id=payload["id"],
                username=payload["username"],
                nom=payload["nom"],
                prenom=payload["prenom"],
                role=payload["role"],
                agency_id=payload.get("agency_id"),
                password_hash="",
                statut="actif",
            )
            current_session.user = user
            current_session.access_token = result.token
            if result.agency:
                current_session.agency = Agency(
                    id=result.agency["id"],
                    name=result.agency["name"],
                    code=result.agency["code"],
                    city="",
                    statut="actif",
                )
            else:
                current_session.agency = None
            return user
        session = get_session()
        try:
            user = auth_service.authenticate(session, username, password)
            if user:
                current_session.user = user
                if user.agency_id:
                    current_session.agency = get_agency(session, user.agency_id)
                else:
                    current_session.agency = None
            return user
        finally:
            session.close()

    def logout(self) -> None:
        current_session.clear()

    def needs_setup(self) -> bool:
        if settings.uses_remote_api:
            return False
        session = get_session()
        try:
            return auth_service.count_users(session) == 0
        finally:
            session.close()
