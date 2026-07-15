"""Ticket sales and seat occupation."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models.ticket import Ticket, TicketCancellation
from models.sequence import Sequence
from models.route import Route
from models.bus import Bus
from models.user import User
from services.audit_service import log_audit


def next_ticket_number(session: Session, sale_date: date | None = None) -> str:
    sale_date = sale_date or date.today()
    seq = (
        session.query(Sequence)
        .filter(Sequence.name == "ticket", Sequence.seq_date == sale_date)
        .with_for_update()
        .first()
    )
    if not seq:
        seq = Sequence(name="ticket", seq_date=sale_date, value=0)
        session.add(seq)
        session.flush()
    seq.value += 1
    session.flush()
    return f"TK-{seq.value:04d}"


def occupied_seats(
    session: Session,
    bus_id: int,
    route_id: int,
    travel_date: date,
) -> set[int]:
    rows = (
        session.query(Ticket.seat_number)
        .filter(
            Ticket.bus_id == bus_id,
            Ticket.route_id == route_id,
            Ticket.travel_date == travel_date,
            Ticket.statut == "vendu",
        )
        .all()
    )
    return {r[0] for r in rows}


def build_qr_payload(
    numero: str,
    passenger: str,
    phone: str,
    route_label: str,
    bus_code: str,
    travel_date: date,
    heure: str,
    seat: int,
    price: Decimal,
    cashier_name: str,
) -> str:
    return (
        f"BILLET:{numero}|PASSAGER:{passenger}|TEL:{phone}|TRAJET:{route_label}"
        f"|BUS:{bus_code}|DATE:{travel_date.isoformat()}|HEURE:{heure}"
        f"|SIEGE:{seat}|PRIX:{price}|CAISSIER:{cashier_name}"
    )


def sell_ticket(
    session: Session,
    *,
    passenger_name: str,
    phone: str,
    route_id: int,
    seat_number: int,
    price: Decimal,
    travel_date: date,
    cashier: User,
) -> Ticket:
    route = session.get(Route, route_id)
    if not route:
        raise ValueError("Trajet introuvable.")
    bus = session.get(Bus, route.bus_id)
    if not bus:
        raise ValueError("Bus introuvable.")
    if seat_number < 1 or seat_number > bus.capacite:
        raise ValueError("Numéro de siège invalide.")
    occupied = occupied_seats(session, bus.id, route.id, travel_date)
    if seat_number in occupied:
        raise ValueError("Ce siège est déjà occupé.")

    sale_date = date.today()
    numero = next_ticket_number(session, sale_date)
    heure = route.heure_depart.strftime("%H:%M")
    qr = build_qr_payload(
        numero,
        passenger_name.strip(),
        phone.strip(),
        route.short_label,
        bus.code,
        travel_date,
        heure,
        seat_number,
        price,
        cashier.full_name,
    )
    ticket = Ticket(
        numero=numero,
        date_vente=sale_date,
        passenger_name=passenger_name.strip(),
        phone=phone.strip(),
        route_id=route.id,
        bus_id=bus.id,
        seat_number=seat_number,
        price=price,
        travel_date=travel_date,
        qr_payload=qr,
        cashier_id=cashier.id,
        statut="vendu",
    )
    session.add(ticket)
    session.flush()
    log_audit(
        session,
        "sale",
        "ticket",
        ticket.id,
        cashier.id,
        {"numero": numero, "seat": seat_number, "price": str(price)},
    )
    session.commit()
    session.refresh(ticket)
    return ticket


def cancel_ticket(
    session: Session,
    ticket_id: int,
    cashier: User,
    reason: str | None = None,
) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        raise ValueError("Billet introuvable.")
    if ticket.statut == "annule":
        raise ValueError("Billet déjà annulé.")
    ticket.statut = "annule"
    session.add(
        TicketCancellation(
            ticket_id=ticket.id,
            reason=reason,
            cancelled_by=cashier.id,
        )
    )
    log_audit(
        session,
        "cancel",
        "ticket",
        ticket.id,
        cashier.id,
        {"numero": ticket.numero, "reason": reason},
    )
    session.commit()
    session.refresh(ticket)
    return ticket


def search_tickets(
    session: Session,
    *,
    query: str = "",
    date_from: date | None = None,
    date_to: date | None = None,
    bus_id: int | None = None,
    cashier_id: int | None = None,
    phone: str | None = None,
    numero: str | None = None,
    limit: int = 200,
) -> list[Ticket]:
    q = session.query(Ticket).options(
        joinedload(Ticket.route),
        joinedload(Ticket.bus),
        joinedload(Ticket.cashier),
    )
    if query:
        like = f"%{query}%"
        q = q.filter(
            (Ticket.passenger_name.ilike(like))
            | (Ticket.phone.ilike(like))
            | (Ticket.numero.ilike(like))
        )
    if date_from:
        q = q.filter(Ticket.date_vente >= date_from)
    if date_to:
        q = q.filter(Ticket.date_vente <= date_to)
    if bus_id:
        q = q.filter(Ticket.bus_id == bus_id)
    if cashier_id:
        q = q.filter(Ticket.cashier_id == cashier_id)
    if phone:
        q = q.filter(Ticket.phone.ilike(f"%{phone}%"))
    if numero:
        q = q.filter(Ticket.numero.ilike(f"%{numero}%"))
    return q.order_by(Ticket.created_at.desc()).limit(limit).all()


def today_sales_stats(session: Session) -> dict:
    today = date.today()
    q = session.query(Ticket).filter(Ticket.date_vente == today, Ticket.statut == "vendu")
    count = q.count()
    total = session.query(func.coalesce(func.sum(Ticket.price), 0)).filter(
        Ticket.date_vente == today, Ticket.statut == "vendu"
    ).scalar()
    return {"billets": count, "recettes": Decimal(total or 0)}
