"""Admin dashboard / reports aggregations from MySQL."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session, Query

from models.bus import Bus
from models.driver import Driver
from models.luggage import Luggage
from models.route import Route
from models.ticket import Ticket
from models.user import User
from services.agency_context import current_agency_id

REVENUE_TICKET_STATUSES = ("vendu", "termine")


def _money(v) -> Decimal:
    if v is None:
        return Decimal("0")
    return Decimal(v)


def _aid(agency_id: int | None) -> int | None:
    return agency_id if agency_id is not None else current_agency_id()


def _filter_agency(q: Query, model, agency_id: int | None) -> Query:
    aid = _aid(agency_id)
    if aid is not None and hasattr(model, "agency_id"):
        return q.filter(model.agency_id == aid)
    return q


def dashboard_kpis(session: Session, agency_id: int | None = None) -> dict:
    aid = _aid(agency_id)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    year_start = date(today.year, 1, 1)

    tq = session.query(func.coalesce(func.sum(Ticket.price), 0), func.count(Ticket.id)).filter(
        Ticket.date_vente == today, Ticket.statut.in_(REVENUE_TICKET_STATUSES)
    )
    tq = _filter_agency(tq, Ticket, aid)
    tickets_today = tq.one()

    lq = session.query(func.coalesce(func.sum(Luggage.total), 0)).filter(
        func.date(Luggage.created_at) == today
    )
    lq = _filter_agency(lq, Luggage, aid)
    luggage_today = lq.scalar()

    wq = session.query(func.coalesce(func.sum(Ticket.price), 0)).filter(
        Ticket.date_vente >= week_start, Ticket.statut.in_(REVENUE_TICKET_STATUSES)
    )
    wq = _filter_agency(wq, Ticket, aid)
    week_rev = wq.scalar()

    wlq = session.query(func.coalesce(func.sum(Luggage.total), 0)).filter(
        func.date(Luggage.created_at) >= week_start
    )
    wlq = _filter_agency(wlq, Luggage, aid)
    week_lug = wlq.scalar()

    yq = session.query(func.coalesce(func.sum(Ticket.price), 0)).filter(
        Ticket.date_vente >= year_start, Ticket.statut.in_(REVENUE_TICKET_STATUSES)
    )
    yq = _filter_agency(yq, Ticket, aid)
    year_rev = yq.scalar()

    ylq = session.query(func.coalesce(func.sum(Luggage.total), 0)).filter(
        func.date(Luggage.created_at) >= year_start
    )
    ylq = _filter_agency(ylq, Luggage, aid)
    year_lug = ylq.scalar()

    voy_q = session.query(Ticket).filter(Ticket.statut.in_(REVENUE_TICKET_STATUSES))
    bag_q = session.query(Luggage)
    bus_q = session.query(Bus).filter(Bus.statut == "actif")
    drv_q = session.query(Driver).filter(Driver.statut == "actif")
    route_q = session.query(Route).filter(Route.statut == "actif")
    cai_q = session.query(User).filter(User.role == "caissier", User.statut == "actif")

    return {
        "recettes_jour": _money(tickets_today[0]) + _money(luggage_today),
        "billets_jour": int(tickets_today[1] or 0),
        "recettes_hebdo": _money(week_rev) + _money(week_lug),
        "recettes_annuel": _money(year_rev) + _money(year_lug),
        "voyageurs": _filter_agency(voy_q, Ticket, aid).count(),
        "bagages": _filter_agency(bag_q, Luggage, aid).count(),
        "bus": _filter_agency(bus_q, Bus, aid).count(),
        "conducteurs": _filter_agency(drv_q, Driver, aid).count(),
        "trajets": _filter_agency(route_q, Route, aid).count(),
        "caissiers": _filter_agency(cai_q, User, aid).count(),
    }


def revenue_by_day(
    session: Session,
    days: int = 30,
    *,
    end: date | None = None,
    agency_id: int | None = None,
) -> list[tuple[date, Decimal]]:
    aid = _aid(agency_id)
    end = end or date.today()
    start = end - timedelta(days=days - 1)
    tq = session.query(Ticket.date_vente, func.coalesce(func.sum(Ticket.price), 0)).filter(
        Ticket.date_vente >= start,
        Ticket.date_vente <= end,
        Ticket.statut.in_(REVENUE_TICKET_STATUSES),
    )
    ticket_rows = _filter_agency(tq, Ticket, aid).group_by(Ticket.date_vente).all()

    lq = session.query(
        func.date(Luggage.created_at),
        func.coalesce(func.sum(Luggage.total), 0),
    ).filter(
        func.date(Luggage.created_at) >= start,
        func.date(Luggage.created_at) <= end,
    )
    luggage_rows = _filter_agency(lq, Luggage, aid).group_by(func.date(Luggage.created_at)).all()

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


def revenue_breakdown(session: Session, days: int = 30, agency_id: int | None = None) -> dict[str, Decimal]:
    aid = _aid(agency_id)
    start = date.today() - timedelta(days=days - 1)
    tq = session.query(func.coalesce(func.sum(Ticket.price), 0)).filter(
        Ticket.date_vente >= start, Ticket.statut.in_(REVENUE_TICKET_STATUSES)
    )
    tickets = _filter_agency(tq, Ticket, aid).scalar()
    lq = session.query(func.coalesce(func.sum(Luggage.total), 0)).filter(
        func.date(Luggage.created_at) >= start
    )
    luggage = _filter_agency(lq, Luggage, aid).scalar()
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
    agency_id: int | None = None,
) -> list[tuple[str, int, Decimal]]:
    aid = _aid(agency_id)
    end = end or date.today()
    start = start or (end - timedelta(days=days - 1))
    q = (
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
            Ticket.statut.in_(REVENUE_TICKET_STATUSES),
        )
    )
    if aid is not None:
        q = q.filter(Ticket.agency_id == aid, Route.agency_id == aid)
    rows = (
        q.group_by(Route.id, Route.ville_depart, Route.ville_arrivee)
        .order_by(func.sum(Ticket.price).desc())
        .limit(limit)
        .all()
    )
    return [(f"{a} → {b}", int(c or 0), _money(s)) for a, b, c, s in rows]


def top_cashiers(
    session: Session, days: int = 30, limit: int = 5, agency_id: int | None = None
) -> list[tuple[str, Decimal, int]]:
    aid = _aid(agency_id)
    start = date.today() - timedelta(days=days - 1)
    q = (
        session.query(
            User.prenom,
            User.nom,
            func.coalesce(func.sum(Ticket.price), 0),
            func.count(Ticket.id),
        )
        .join(Ticket, Ticket.cashier_id == User.id)
        .filter(Ticket.date_vente >= start, Ticket.statut.in_(REVENUE_TICKET_STATUSES))
    )
    if aid is not None:
        q = q.filter(User.agency_id == aid, Ticket.agency_id == aid)
    rows = (
        q.group_by(User.id, User.prenom, User.nom)
        .order_by(func.sum(Ticket.price).desc())
        .limit(limit)
        .all()
    )
    return [(f"{p} {n}".strip(), _money(s), int(c or 0)) for p, n, s, c in rows]


def period_kpis(session: Session, start: date, end: date, agency_id: int | None = None) -> dict:
    aid = _aid(agency_id)
    tq = session.query(func.coalesce(func.sum(Ticket.price), 0), func.count(Ticket.id)).filter(
        Ticket.date_vente >= start,
        Ticket.date_vente <= end,
        Ticket.statut.in_(REVENUE_TICKET_STATUSES),
    )
    tickets = _filter_agency(tq, Ticket, aid).one()
    lq = session.query(func.coalesce(func.sum(Luggage.total), 0), func.count(Luggage.id)).filter(
        func.date(Luggage.created_at) >= start,
        func.date(Luggage.created_at) <= end,
    )
    luggage = _filter_agency(lq, Luggage, aid).one()
    return {
        "recettes_billets": _money(tickets[0]),
        "nb_billets": int(tickets[1] or 0),
        "recettes_bagages": _money(luggage[0]),
        "nb_bagages": int(luggage[1] or 0),
        "recettes_total": _money(tickets[0]) + _money(luggage[0]),
    }


def fleet_revenue(session: Session, agency_id: int | None = None) -> Decimal:
    aid = _aid(agency_id)
    tq = session.query(func.coalesce(func.sum(Ticket.price), 0)).filter(
        Ticket.statut.in_(REVENUE_TICKET_STATUSES)
    )
    lq = session.query(func.coalesce(func.sum(Luggage.total), 0))
    t = _filter_agency(tq, Ticket, aid).scalar()
    l = _filter_agency(lq, Luggage, aid).scalar()
    return _money(t) + _money(l)


def sales_heatmap(session: Session, days: int = 30, agency_id: int | None = None) -> list[tuple[int, int, int]]:
    aid = _aid(agency_id)
    start = date.today() - timedelta(days=days - 1)
    q = session.query(
        func.dayofweek(Ticket.date_vente),
        func.hour(Ticket.created_at),
        func.count(Ticket.id),
    ).filter(Ticket.date_vente >= start, Ticket.statut.in_(REVENUE_TICKET_STATUSES))
    rows = _filter_agency(q, Ticket, aid).group_by(
        func.dayofweek(Ticket.date_vente), func.hour(Ticket.created_at)
    ).all()
    return [(int(d), int(h), int(c)) for d, h, c in rows]


def filling_rate_by_route(session: Session, agency_id: int | None = None) -> list[tuple[str, float]]:
    from sqlalchemy import distinct

    aid = _aid(agency_id)
    q = (
        session.query(
            Route.ville_depart,
            Route.ville_arrivee,
            func.count(Ticket.id),
            Bus.capacite,
            func.count(distinct(Ticket.travel_date)),
        )
        .join(Bus, Route.bus_id == Bus.id)
        .outerjoin(Ticket, Ticket.route_id == Route.id)
        .filter(Route.statut == "actif")
    )
    if aid is not None:
        q = q.filter(Route.agency_id == aid)
    rows = q.group_by(Route.id, Route.ville_depart, Route.ville_arrivee, Bus.capacite).all()
    out = []
    for dep, arr, t_count, cap, date_count in rows:
        date_count = max(1, int(date_count or 1))
        cap = max(1, int(cap or 60))
        rate = (t_count / (cap * date_count)) * 100.0
        out.append((f"{dep} → {arr}", min(100.0, rate)))
    return out


def comparative_revenue(
    session: Session, days: int = 30, agency_id: int | None = None
) -> tuple[list[Decimal], list[Decimal]]:
    today = date.today()
    start_curr = today - timedelta(days=days - 1)
    curr_rev = revenue_by_day(session, days, end=today, agency_id=agency_id)
    end_prev = start_curr - timedelta(days=1)
    prev_rev = revenue_by_day(session, days, end=end_prev, agency_id=agency_id)
    curr_vals = [v for _, v in curr_rev]
    prev_vals = [v for _, v in prev_rev]
    return curr_vals, prev_vals
