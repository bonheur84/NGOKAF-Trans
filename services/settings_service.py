"""App settings service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from config.settings import settings
from models.app_setting import AppSetting


DEFAULTS = {
    "agency_name": settings.AGENCY_NAME,
    "agency_address": settings.AGENCY_ADDRESS,
    "agency_phone": settings.AGENCY_PHONE,
    "terminal_name": settings.TERMINAL_NAME,
    "luggage_base_fee": str(settings.LUGGAGE_BASE_FEE),
    "luggage_weight_rate": str(settings.LUGGAGE_WEIGHT_RATE),
    "session_timeout_minutes": str(settings.SESSION_TIMEOUT_MINUTES),
    "currency": "FC",
    "tva_percent": "0",
    "ticket_prefix": "TK-",
    "ticket_width_mm": "80",
    "luggage_width_mm": "58",
}


def ensure_default_settings(session: Session) -> None:
    for key, value in DEFAULTS.items():
        existing = session.query(AppSetting).filter_by(key=key).first()
        if not existing:
            session.add(AppSetting(key=key, value=value))


def get_setting(session: Session, key: str, default: str = "") -> str:
    row = session.query(AppSetting).filter_by(key=key).first()
    return row.value if row else default


def set_setting(session: Session, key: str, value: str) -> None:
    row = session.query(AppSetting).filter_by(key=key).first()
    if row:
        row.value = value
    else:
        session.add(AppSetting(key=key, value=value))
