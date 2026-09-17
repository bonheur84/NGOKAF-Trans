"""Luggage registration service."""
from __future__ import annotations

import random
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models.luggage import Luggage
from models.sequence import Sequence
from models.route import Route
from models.bus import Bus
from models.ticket import Ticket
from models.user import User
from services.agency_context import current_agency_id
from services.audit_service import log_audit
from services.settings_service import get_setting


def next_luggage_number(session: Session, agency_id: int | None = None) -> str:
    """Generate a professional unique luggage code: NG-YYMMDD-XXXXX.

    Format: NG-{date}-{5-digit random} ensuring uniqueness via DB check.
    The internal Sequence is still incremented for ordering purposes.
    """
    today = date.today()
    aid = agency_id
    q = session.query(Sequence).filter(Sequence.name == "luggage", Sequence.seq_date == today)
    if aid is not None:
        q = q.filter(Sequence.agency_id == aid)
    seq = q.with_for_update().first()
    if not seq:
        seq = Sequence(name="luggage", seq_date=today, value=0, agency_id=aid)
        session.add(seq)
        session.flush()
    seq.value += 1
    session.flush()

    date_part = today.strftime("%y%m%d")
    # Generate a unique random 5-digit suffix; retry on collision
    for _ in range(20):
        suffix = random.randint(10000, 99999)
        candidate = f"NG-{date_part}-{suffix}"
        exists = session.query(Luggage.id).filter(Luggage.numero == candidate).first()
        if not exists:
            return candidate
    # Fallback: use sequential counter if all randoms collide (extremely rare)
    return f"NG-{date_part}-{seq.value:05d}"


def calculate_fees(
    session: Session,
    poids: Decimal,
    frais_base: Decimal | None = None,
    weight_rate: Decimal | None = None,
    agency_id: int | None = None,
) -> tuple[Decimal, Decimal, Decimal]:
    if frais_base is None:
        frais_base = Decimal(get_setting(session, "luggage_base_fee", "2500", agency_id=agency_id))
    if weight_rate is None:
        weight_rate = Decimal(get_setting(session, "luggage_weight_rate", "200", agency_id=agency_id))
    # Free allowance 5 kg then surcharge per kg
    free = Decimal("5")
    over = max(Decimal("0"), poids - free)
    supplement = (over * weight_rate).quantize(Decimal("0.01"))
    total = (frais_base + supplement).quantize(Decimal("0.01"))
    return frais_base, supplement, total


def register_luggage(
    session: Session,
    *,
    sender_name: str,
    sender_phone: str,
    recipient_name: str,
    recipient_phone: str,
    description: str,
    poids: Decimal,
    valeur_declaree: Decimal | None,
    route_id: int,
    frais_base: Decimal | None,
    supplement_poids: Decimal | None,
    total: Decimal | None,
    fragile: bool,
    cashier: User,
    ticket: Ticket | None = None,
) -> Luggage:
    if not cashier.agency_id:
        raise ValueError("Caissier sans agence assignée.")
    route = session.get(Route, route_id)
    if not route:
        raise ValueError("Trajet introuvable.")
    if route.agency_id != cashier.agency_id:
        raise ValueError("Ce trajet n'appartient pas à votre agence.")
    bus = session.get(Bus, route.bus_id)
    if not bus:
        raise ValueError("Bus introuvable.")
    if bus.agency_id != cashier.agency_id:
        raise ValueError("Ce bus n'appartient pas à votre agence.")
    if ticket is None:
        raise ValueError("Recherchez le billet du client avant d'enregistrer le bagage.")
    if ticket.agency_id != cashier.agency_id or ticket.statut != "vendu":
        raise ValueError("Billet invalide pour l'enregistrement du bagage.")
    if ticket.route_id != route.id or ticket.bus_id != bus.id:
        raise ValueError("Le billet ne correspond pas au trajet sélectionné.")

    base, supp, calc_total = calculate_fees(session, poids, frais_base, agency_id=cashier.agency_id)
    if supplement_poids is not None:
        supp = Decimal(supplement_poids)
    if total is not None:
        calc_total = Decimal(total)
    elif frais_base is not None:
        calc_total = (Decimal(frais_base) + supp).quantize(Decimal("0.01"))
        base = Decimal(frais_base)

    numero = next_luggage_number(session, cashier.agency_id)
    barcode = f"{date.today().strftime('%d%m%Y')}-{numero.split('-')[-1]}"
    qr = (
        f"BAGAGE:{numero}|EXP:{sender_name}|DEST:{recipient_name}"
        f"|TEL_EXP:{sender_phone}|TEL_DEST:{recipient_phone}"
        f"|POIDS:{poids}|TRAJET:{route.short_label}|BUS:{bus.code}"
        f"|TOTAL:{calc_total}|DATE:{datetime.now().isoformat()}"
    )
    item = Luggage(
        numero=numero,
        sender_name=sender_name.strip(),
        sender_phone=sender_phone.strip(),
        recipient_name=recipient_name.strip(),
        recipient_phone=recipient_phone.strip(),
        description=description.strip(),
        poids=poids,
        valeur_declaree=valeur_declaree,
        ticket_id=ticket.id,
        ticket_numero=ticket.numero,
        route_id=route.id,
        bus_id=bus.id,
        route_label=route.short_label,
        bus_code=bus.code,
        frais_base=base,
        supplement_poids=supp,
        total=calc_total,
        barcode=barcode,
        qr_payload=qr,
        cashier_id=cashier.id,
        agency_id=cashier.agency_id,
        statut="enregistre",
        fragile=fragile,
    )
    session.add(item)
    session.flush()
    log_audit(session, "create", "luggage", item.id, cashier.id, {"numero": numero})
    session.commit()
    session.refresh(item)
    return item


def find_ticket_for_luggage(
    session: Session, ticket_number: str, agency_id: int | None = None
) -> Ticket | None:
    """Find a sold ticket for baggage check-in, including inactive trip records.

    A bus can be deactivated once its departure is closed.  That operational
    status must never hide the tickets already sold for the trip, because their
    passengers may still check in luggage.  The ticket number is also accepted
    as a fallback when the printed baggage code is unavailable.
    """
    aid = agency_id if agency_id is not None else current_agency_id()
    code = ticket_number.strip()
    if not code:
        return None
    q = session.query(Ticket).options(
        joinedload(Ticket.route), joinedload(Ticket.bus), joinedload(Ticket.cashier)
    ).filter(
        (Ticket.luggage_code == code.upper()) | (Ticket.numero == code.upper()),
        Ticket.statut == "vendu",
    )
    if aid is not None:
        q = q.filter(Ticket.agency_id == aid)
    return q.order_by(Ticket.created_at.desc()).first()


def update_luggage_status(
    session: Session,
    luggage_id: int,
    statut: str,
    user_id: int | None = None,
) -> Luggage:
    allowed = {"enregistre", "charge", "livre", "annule"}
    if statut not in allowed:
        raise ValueError("Statut invalide.")
    item = session.get(Luggage, luggage_id)
    if not item:
        raise ValueError("Bagage introuvable.")
    aid = current_agency_id()
    if aid is not None and item.agency_id != aid:
        raise ValueError("Bagage hors de votre agence.")
    item.statut = statut
    log_audit(session, "status", "luggage", item.id, user_id, {"statut": statut})
    session.commit()
    session.refresh(item)
    return item


from datetime import date, datetime, time
from sqlalchemy import func, text


def reset_daily_luggage_links(session: Session) -> int:
    """Archive past routing values before detaching deleted/live relationships."""
    today_start = datetime.combine(date.today(), time.min)
    items = (
        session.query(Luggage)
        .options(joinedload(Luggage.route), joinedload(Luggage.bus))
        .filter(
            Luggage.created_at < today_start,
            (Luggage.route_id.is_not(None)) | (Luggage.bus_id.is_not(None)),
        )
        .all()
    )
    for item in items:
        if item.route and not item.route_label:
            item.route_label = item.route.short_label
        if item.bus and not item.bus_code:
            item.bus_code = item.bus.code
        item.route_id = None
        item.bus_id = None
    session.commit()
    return len(items)


def list_luggage_for_bus(
    session: Session,
    bus_id: int,
    query: str = "",
    limit: int = 100,
    agency_id: int | None = None,
) -> list[Luggage]:
    aid = agency_id if agency_id is not None else current_agency_id()
    today_start = datetime.combine(date.today(), time.min)
    q = (
        session.query(Luggage)
        .options(joinedload(Luggage.route), joinedload(Luggage.bus))
        .filter(Luggage.bus_id == bus_id, Luggage.created_at >= today_start)
    )
    if aid is not None:
        q = q.filter(Luggage.agency_id == aid)
    if query:
        like = f"%{query}%"
        q = q.filter(
            (Luggage.numero.ilike(like))
            | (Luggage.sender_name.ilike(like))
            | (Luggage.recipient_name.ilike(like))
            | (Luggage.sender_phone.ilike(like))
        )
    return q.order_by(Luggage.created_at.desc()).limit(limit).all()


def list_recent_luggage(session: Session, limit: int = 50, agency_id: int | None = None) -> list[Luggage]:
    """Returns today's luggage items created after 00:00."""
    aid = agency_id if agency_id is not None else current_agency_id()
    today_start = datetime.combine(date.today(), time.min)
    q = (
        session.query(Luggage)
        .options(joinedload(Luggage.route), joinedload(Luggage.bus))
        .filter(Luggage.created_at >= today_start)
    )
    if aid is not None:
        q = q.filter(Luggage.agency_id == aid)
    return q.order_by(Luggage.created_at.desc()).limit(limit).all()


def today_luggage_stats(session: Session, agency_id: int | None = None) -> dict:
    aid = agency_id if agency_id is not None else current_agency_id()
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    count_q = session.query(Luggage).filter(Luggage.created_at >= start, Luggage.statut != "annule")
    weight_q = session.query(func.coalesce(func.sum(Luggage.poids), 0)).filter(
        Luggage.created_at >= start, Luggage.statut != "annule"
    )
    if aid is not None:
        count_q = count_q.filter(Luggage.agency_id == aid)
        weight_q = weight_q.filter(Luggage.agency_id == aid)
    count = count_q.count()
    weight = weight_q.scalar()
    yesterday = today.fromordinal(today.toordinal() - 1)
    y_start = datetime.combine(yesterday, datetime.min.time())
    y_count_q = session.query(Luggage).filter(
        Luggage.created_at >= y_start,
        Luggage.created_at < start,
        Luggage.statut != "annule",
    )
    if aid is not None:
        y_count_q = y_count_q.filter(Luggage.agency_id == aid)
    y_count = y_count_q.count()
    if y_count > 0:
        growth = ((count - y_count) / y_count) * 100.0
        sign = "+" if growth >= 0 else ""
        growth_label = f"{sign}{growth:.0f}% vs hier ({y_count})"
    elif count > 0:
        growth = 100.0
        growth_label = f"+{count} aujourd'hui (0 hier)"
    else:
        growth = 0.0
        growth_label = "0% vs hier"
    return {
        "count": count,
        "weight": Decimal(weight or 0),
        "growth": growth,
        "yesterday": y_count,
        "growth_label": growth_label,
    }
