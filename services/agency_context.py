"""Current agency context from logged-in session."""
from __future__ import annotations

from services.session_store import current_session


def current_agency_id() -> int | None:
    if current_session.agency is not None:
        return current_session.agency.id
    if current_session.user is not None and current_session.user.agency_id is not None:
        return current_session.user.agency_id
    return None


def require_agency_id() -> int:
    agency_id = current_agency_id()
    if agency_id is None:
        raise RuntimeError("Aucune agence active dans la session.")
    return agency_id


def agency_display_name(fallback: str = "NGOKAF TRANS") -> str:
    if current_session.agency is not None:
        return current_session.agency.name
    return fallback
