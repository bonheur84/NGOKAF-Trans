"""Application settings loaded from .env and config.ini."""
from __future__ import annotations

import configparser
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus


def _project_root() -> Path:
    """Writable install / project directory (.env, logs, backups)."""
    if getattr(sys, "frozen", False):
        # Use AppData for writable data when installed in Program Files
        appdata = os.environ.get("LOCALAPPDATA")
        if appdata:
            return Path(appdata) / "NGOKAF_TRANS"
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _resource_root() -> Path:
    """Bundled read-only resources (PyInstaller _MEIPASS or project root)."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return _project_root()


ROOT = _project_root()
RESOURCE_ROOT = _resource_root()

from utils.runtime_bootstrap import ensure_runtime  # noqa: E402

ensure_runtime(ROOT, RESOURCE_ROOT)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

_cfg = configparser.ConfigParser()
_cfg_path = ROOT / "config.ini"
if _cfg_path.exists():
    _cfg.read(_cfg_path, encoding="utf-8")


def reload_config() -> None:
    """Re-read .env and config.ini into process env / parser."""
    load_dotenv(ROOT / ".env", override=True)
    _cfg.clear()
    if _cfg_path.exists():
        _cfg.read(_cfg_path, encoding="utf-8")


def _get(section: str, key: str, env_key: str, default: str = "") -> str:
    env_val = os.getenv(env_key)
    if env_val is not None and env_val != "":
        return env_val
    if _cfg.has_option(section, key):
        return _cfg.get(section, key)
    return default


class Settings:
    """Central configuration."""

    ROOT = ROOT
    RESOURCE_ROOT = RESOURCE_ROOT
    ASSETS = RESOURCE_ROOT / "assets"
    IMAGES = ASSETS / "images"
    FONTS = ASSETS / "fonts"
    ICONS = ASSETS / "icons"
    LOGS = ROOT / "logs"
    BACKUPS = ROOT / "backups"
    TEMP_DIR = ROOT / "temp"
    REPORTS_DIR = ROOT / "reports"
    REMEMBER_FILE = ROOT / "config" / ".remember"

    DB_HOST = _get("database", "host", "DB_HOST", "localhost")
    DB_PORT = int(_get("database", "port", "DB_PORT", "3306"))
    DB_USER = _get("database", "user", "DB_USER", "root")
    DB_PASSWORD = _get("database", "password", "DB_PASSWORD", "")
    DB_NAME = _get("database", "name", "DB_NAME", "ngokaf_trans")

    AGENCY_NAME = _get("agency", "name", "AGENCY_NAME", "NGOKAF TRANS")
    AGENCY_ADDRESS = _get("agency", "address", "AGENCY_ADDRESS", "Douala, Cameroun")
    AGENCY_PHONE = _get("agency", "phone", "AGENCY_PHONE", "")
    TERMINAL_NAME = _get("agency", "terminal", "TERMINAL_NAME", "TERMINAL PRINCIPAL")

    SESSION_TIMEOUT_MINUTES = int(
        _get("session", "timeout_minutes", "SESSION_TIMEOUT_MINUTES", "30")
    )
    LUGGAGE_BASE_FEE = float(_get("luggage", "base_fee", "LUGGAGE_BASE_FEE", "2500"))
    LUGGAGE_WEIGHT_RATE = float(
        _get("luggage", "weight_rate", "LUGGAGE_WEIGHT_RATE", "200")
    )

    @property
    def database_url(self) -> str:
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+pymysql://{user}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def server_url(self) -> str:
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+pymysql://{user}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/?charset=utf8mb4"
        )

    @property
    def logo_path(self) -> Path:
        png = self.IMAGES / "logo.png"
        jpg = self.IMAGES / "logo.jpg"
        if png.exists():
            return png
        return jpg


settings = Settings()
