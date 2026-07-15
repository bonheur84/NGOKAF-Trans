"""Print service facade."""
from __future__ import annotations

from pathlib import Path

from reports.ticket_80mm import generate_ticket_pdf, print_ticket_windows
from reports.luggage_58mm import generate_luggage_label_pdf, print_luggage_label
from services.audit_service import log_audit
from database.session import get_session


def print_ticket(ticket, user_id: int | None = None, preview_only: bool = False) -> Path:
    if preview_only:
        path = generate_ticket_pdf(ticket)
    else:
        path = print_ticket_windows(ticket)
    session = get_session()
    try:
        log_audit(session, "print", "ticket", ticket.id, user_id, {"path": str(path)})
        session.commit()
    finally:
        session.close()
    return path


def print_luggage(item, user_id: int | None = None, preview_only: bool = False) -> Path:
    if preview_only:
        path = generate_luggage_label_pdf(item)
    else:
        path = print_luggage_label(item)
    session = get_session()
    try:
        log_audit(session, "print", "luggage", item.id, user_id, {"path": str(path)})
        session.commit()
    finally:
        session.close()
    return path
