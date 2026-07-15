"""Application logging setup."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from config.settings import settings


def setup_logging() -> None:
    settings.LOGS.mkdir(parents=True, exist_ok=True)
    log_file = settings.LOGS / "ngokaf.log"
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(fh)
    root.addHandler(sh)
