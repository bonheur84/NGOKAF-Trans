"""Admin dashboard / reports aggregations from MySQL."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.bus import Bus
from models.driver import Driver
from models.luggage import Luggage
from models.route import Route
from models.ticket import Ticket
from models.user import User


def _money(v) -> Decimal:
    if v is None:
        return Decimal("0")
    return Decimal(v)


def dashboard_kpis(session: Session) -> dict:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    year_start = date(today.year, 1, 1)

    tickets_today = (
        session.query(func.coalesce(func.sum(Ticket.price), 0), func.count(Ticket.id))
        .filter(Ticket.date_vente == today, Ticket.statut == "vendu")
        .one()
    )
    luggage_today = (
        session.query(func.coalesce(func.sum(Luggage.total), 0))
        .filter(func.date(Luggage.created_at) == today)
        .scalar()
    )
    week_rev = (
        session.query(func.coalesce(func.sum(Ticket.price), 0))
        .filter(Ticket.date_vente >= week_start, Ticket.statut == "vendu")
        .scalar()
    )
    week_lug = (
        session.query(func.coalesce(func.sum(Luggage.total), 0))
        .filter(func.date(Luggage.created_at) >= week_start)
        .scalar()
    )
    year_rev = (
        session.query(func.coalesce(func.sum(Ticket.price), 0))
        .filter(Ticket.date_vente >= year_start, Ticket.statut == "vendu")
        .scalar()
    )
    year_lug = (
        session.query(func.coalesce(func.sum(Luggage.total), 0))
        .filter(func.date(Luggage.created_at) >= year_start)
        .scalar()
    )

    return {
        "recettes_jour": _money(tickets_today[0]) + _money(luggage_today),
        "billets_jour": int(tickets_today[1] or 0),
        "recettes_hebdo": _money(week_rev) + _money(week_lug),
        "recettes_annuel": _money(year_rev) + _money(year_lug),
        "voyageurs": session.query(Ticket)
        .filter(Ticket.statut == "vendu")
        .count(),
        "bagages": session.query(Luggage).count(),
        "bus": session.query(Bus).filter(Bus.statut == "actif").count(),
        "conducteurs": session.query(Driver).filter(Driver.statut == "actif").count(),
        "trajets": session.query(Route).filter(Route.statut == "actif").count(),
        "caissiers": session.query(User)
        .filter(User.role == "caissier", User.statut == "actif")
        .count(),
    }


def revenue_by_day(
    session: Session,
    days: int = 30,
    *,
    end: date | None = None,
) -> list[tuple[date, Decimal]]:
    end = end or date.today()
    start = end - timedelta(days=days - 1)
    ticket_rows = (
        session.query(Ticket.date_vente, func.coalesce(func.sum(Ticket.price), 0))
        .filter(
            Ticket.date_vente >= start,
            Ticket.date_vente <= end,
            Ticket.statut == "vendu",
        )
        .group_by(Ticket.date_vente)
        .all()
    )
    luggage_rows = (
        session.query(
            func.date(Luggage.created_at),
            func.coalesce(func.sum(Luggage.total), 0),
        )
        .filter(
            func.date(Luggage.created_at) >= start,
            func.date(Luggage.created_at) <= end,
        )
        .group_by(func.date(Luggage.created_at))
        .all()
    )
    totals: dict[date, Decimal] = {}
    for d, amt in ticket_rows:
        totals[d] = totals.get(d, Decimal("0")) + _money(amt)
    for d, amt in luggage_rows:
        if isinstance(d, datetime):
            d = d.date()
        elif isinstance(d, str):
            d = date.fromisoformat(d)
        totals[d] = totals.get(d, Decimal("0")) + _money(amt)
    out = []
    for i in range(days):
        d = start + timedelta(days=i)
        out.append((d, totals.get(d, Decimal("0"))))
    return out


def revenue_breakdown(session: Session, days: int = 30) -> dict[str, Decimal]:
    start = date.today() - timedelta(days=days - 1)
    tickets = (
        session.query(func.coalesce(func.sum(Ticket.price), 0))
        .filter(Ticket.date_vente >= start, Ticket.statut == "vendu")
        .scalar()
    )
    luggage = (
        session.query(func.coalesce(func.sum(Luggage.total), 0))
        .filter(func.date(Luggage.created_at) >= start)
        .scalar()
    )
    return {
        "Billets": _money(tickets),
        "Bagages": _money(luggage),
    }


def sales_by_route(
    session: Session,
    days: int = 30,
    limit: int = 8,
    *,
    start: date | None = None,
    end: date | None = None,
) -> list[tuple[str, int, Decimal]]:
    end = end or date.today()
    start = start or (end - timedelta(days=days - 1))
    rows = (
        session.query(
            Route.ville_depart,
            Route.ville_arrivee,
            func.count(Ticket.id),
            func.coalesce(func.sum(Ticket.price), 0),
        )
        .join(Ticket, Ticket.route_id == Route.id)
        .filter(
            Ticket.date_vente >= start,
            Ticket.date_vente <= end,
            Ticket.statut == "vendu",
        )
        .group_by(Route.id, Route.ville_depart, Route.ville_arrivee)
        .order_by(func.sum(Ticket.price).desc())
        .limit(limit)
        .all()
    )
    return [
        (f"{a} → {b}", int(c or 0), _money(s)) for a, b, c, s in rows
    ]


def top_cashiers(session: Session, days: int = 30, limit: int = 5) -> list[tuple[str, Decimal, int]]:
    start = date.today() - timedelta(days=days - 1)
    rows = (
        session.query(
            User.prenom,
            User.nom,
            func.coalesce(func.sum(Ticket.price), 0),
            func.count(Ticket.id),
        )
        .join(Ticket, Ticket.cashier_id == User.id)
        .filter(Ticket.date_vente >= start, Ticket.statut == "vendu")
        .group_by(User.id, User.prenom, User.nom)
        .order_by(func.sum(Ticket.price).desc())
        .limit(limit)
        .all()
    )
    return [(f"{p} {n}".strip(), _money(s), int(c or 0)) for p, n, s, c in rows]


def period_kpis(session: Session, start: date, end: date) -> dict:
    tickets = (
        session.query(func.coalesce(func.sum(Ticket.price), 0), func.count(Ticket.id))
        .filter(
            Ticket.date_vente >= start,
            Ticket.date_vente <= end,
            Ticket.statut == "vendu",
        )
        .one()
    )
    luggage = (
        session.query(func.coalesce(func.sum(Luggage.total), 0), func.count(Luggage.id))
        .filter(
            func.date(Luggage.created_at) >= start,
            func.date(Luggage.created_at) <= end,
        )
        .one()
    )
    return {
        "recettes_billets": _money(tickets[0]),
        "nb_billets": int(tickets[1] or 0),
        "recettes_bagages": _money(luggage[0]),
        "nb_bagages": int(luggage[1] or 0),
        "recettes_total": _money(tickets[0]) + _money(luggage[0]),
    }


def fleet_revenue(session: Session) -> Decimal:
    t = session.query(func.coalesce(func.sum(Ticket.price), 0)).filter(
        Ticket.statut == "vendu"
    ).scalar()
    l = session.query(func.coalesce(func.sum(Luggage.total), 0)).scalar()
    return _money(t) + _money(l)
