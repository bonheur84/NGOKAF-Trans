"""Audit / logging helpers."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from models.audit import AuditLog, LoginLog


def log_audit(
    session: Session,
    action: str,
    entity: str,
    entity_id: int | None = None,
    user_id: int | None = None,
    details: dict[str, Any] | str | None = None,
) -> None:
    if isinstance(details, dict):
        details = json.dumps(details, ensure_ascii=False, default=str)
    session.add(
        AuditLog(
            action=action,
            entity=entity,
            entity_id=entity_id,
            user_id=user_id,
            details=details,
        )
    )


def log_login(
    session: Session,
    username: str,
    success: bool,
    user_id: int | None = None,
    info: str | None = None,
) -> None:
    session.add(
        LoginLog(user_id=user_id, username=username, success=success, info=info)
    )
