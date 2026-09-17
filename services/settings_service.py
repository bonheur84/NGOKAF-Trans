"""App settings service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from config.settings import settings
from models.app_setting import AppSetting
from services.agency_context import current_agency_id


DEFAULTS = {
    "agency_name": settings.AGENCY_NAME,
    "agency_address": settings.AGENCY_ADDRESS,
    "agency_phone": settings.AGENCY_PHONE,
    "terminal_name": settings.TERMINAL_NAME,
    "luggage_base_fee": str(settings.LUGGAGE_BASE_FEE),
    "luggage_weight_rate": str(settings.LUGGAGE_WEIGHT_RATE),
    "luggage_label_printer": "",
    "session_timeout_minutes": str(settings.SESSION_TIMEOUT_MINUTES),
    "currency": "FC",
    "tva_percent": "0",
    "ticket_prefix": "TK-",
    "ticket_width_mm": "80",
    "luggage_width_mm": "58",
}


def ensure_default_settings(session: Session) -> None:
    """Legacy global settings bootstrap — skip if per-agency settings exist."""
    from models.agency import Agency

    if session.query(Agency).count() > 0:
        for agency in session.query(Agency).all():
            ensure_agency_settings(session, agency.id)
        return
    for key, value in DEFAULTS.items():
        existing = (
            session.query(AppSetting)
            .filter(AppSetting.key == key, AppSetting.agency_id.is_(None))
            .first()
        )
        if not existing:
            session.add(AppSetting(key=key, value=value, agency_id=None))


def ensure_agency_settings(
    session: Session,
    agency_id: int,
    defaults: dict[str, str] | None = None,
) -> None:
    values = {**DEFAULTS, **(defaults or {})}
    for key, value in values.items():
        existing = (
            session.query(AppSetting)
            .filter(AppSetting.key == key, AppSetting.agency_id == agency_id)
            .first()
        )
        if not existing:
            session.add(AppSetting(key=key, value=value, agency_id=agency_id))
    session.flush()


def get_setting(
    session: Session,
    key: str,
    default: str = "",
    agency_id: int | None = None,
) -> str:
    aid = agency_id if agency_id is not None else current_agency_id()
    q = session.query(AppSetting).filter(AppSetting.key == key)
    if aid is not None:
        q = q.filter(AppSetting.agency_id == aid)
    else:
        q = q.filter(AppSetting.agency_id.is_(None))
    row = q.first()
    if row:
        return row.value
    if aid is not None:
        fallback = (
            session.query(AppSetting)
            .filter(AppSetting.key == key, AppSetting.agency_id.is_(None))
            .first()
        )
        if fallback:
            return fallback.value
    return default


def set_setting(
    session: Session,
    key: str,
    value: str,
    agency_id: int | None = None,
) -> None:
    aid = agency_id if agency_id is not None else current_agency_id()
    if aid is None:
        raise RuntimeError("Impossible d'enregistrer un paramètre sans agence active.")
    row = (
        session.query(AppSetting)
        .filter(AppSetting.key == key, AppSetting.agency_id == aid)
        .first()
    )
    if row:
        row.value = value
    else:
        session.add(AppSetting(key=key, value=value, agency_id=aid))
