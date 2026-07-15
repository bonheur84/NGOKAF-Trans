"""Simple input validators."""
from __future__ import annotations

import re


def require_non_empty(value: str, label: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{label} est obligatoire.")
    return text


def normalize_phone(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").strip())
