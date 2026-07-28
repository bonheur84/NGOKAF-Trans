"""Luggage registration service."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models.luggage import Luggage
from models.sequence import Sequence
from models.route import Route
from models.bus import Bus
from models.user import User
from services.audit_service import log_audit
from services.settings_service import get_setting


def next_luggage_number(session: Session) -> str:
    today = date.today()
    seq = (
        session.query(Sequence)
        .filter(Sequence.name == "luggage", Sequence.seq_date == today)
        .with_for_update()
        .first()
    )
    if not seq:
        # Determine starting value from existing luggage numbers to avoid duplicates
        last = session.query(Luggage.numero).order_by(Luggage.id.desc()).first()
        start_value = 0
        if last:
            try:
                # numero format is BG-XXXXXX, extract the numeric part
                start_value = int(last[0].split("-")[-1])
            except (ValueError, IndexError):
                start_value = 0
        seq = Sequence(name="luggage", seq_date=today, value=start_value)
        session.add(seq)
        session.flush()
    seq.value += 1
    session.flush()
    # Format BG-002490 style with globally incrementing counter padded
    return f"BG-{seq.value:06d}"


def calculate_fees(
    session: Session,
    poids: Decimal,
    frais_base: Decimal | None = None,
    weight_rate: Decimal | None = None,
) -> tuple[Decimal, Decimal, Decimal]:
    if frais_base is None:
        frais_base = Decimal(get_setting(session, "luggage_base_fee", "2500"))
    if weight_rate is None:
        weight_rate = Decimal(get_setting(session, "luggage_weight_rate", "200"))
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
) -> Luggage:
    route = session.get(Route, route_id)
    if not route:
        raise ValueError("Trajet introuvable.")
    bus = session.get(Bus, route.bus_id)
    if not bus:
        raise ValueError("Bus introuvable.")

    base, supp, calc_total = calculate_fees(session, poids, frais_base)
    if supplement_poids is not None:
        supp = Decimal(supplement_poids)
    if total is not None:
        calc_total = Decimal(total)
    elif frais_base is not None:
        calc_total = (Decimal(frais_base) + supp).quantize(Decimal("0.01"))
        base = Decimal(frais_base)

    numero = next_luggage_number(session)
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
        route_id=route.id,
        bus_id=bus.id,
        frais_base=base,
        supplement_poids=supp,
        total=calc_total,
        barcode=barcode,
        qr_payload=qr,
        cashier_id=cashier.id,
        statut="enregistre",
        fragile=fragile,
    )
    session.add(item)
    session.flush()
    log_audit(session, "create", "luggage", item.id, cashier.id, {"numero": numero})
    session.commit()
    session.refresh(item)
    return item


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
    item.statut = statut
    log_audit(session, "status", "luggage", item.id, user_id, {"statut": statut})
    session.commit()
    session.refresh(item)
    return item


from datetime import date, datetime, time
from sqlalchemy import func, text


def reset_daily_luggage_links(session: Session) -> int:
    """Detach route_id and bus_id from past days' luggage so past routes/buses can be deleted/cleaned safely."""
    today_start = datetime.combine(date.today(), time.min)
    res = session.execute(
        text("UPDATE luggage SET route_id = NULL, bus_id = NULL WHERE created_at < :today_start AND (route_id IS NOT NULL OR bus_id IS NOT NULL)"),
        {"today_start": today_start},
    )
    session.commit()
    return res.rowcount


def list_luggage_for_bus(
    session: Session,
    bus_id: int,
    query: str = "",
    limit: int = 100,
) -> list[Luggage]:
    today_start = datetime.combine(date.today(), time.min)
    q = (
        session.query(Luggage)
        .options(joinedload(Luggage.route), joinedload(Luggage.bus))
        .filter(Luggage.bus_id == bus_id, Luggage.created_at >= today_start)
    )
    if query:
        like = f"%{query}%"
        q = q.filter(
            (Luggage.numero.ilike(like))
            | (Luggage.sender_name.ilike(like))
            | (Luggage.recipient_name.ilike(like))
            | (Luggage.sender_phone.ilike(like))
        )
    return q.order_by(Luggage.created_at.desc()).limit(limit).all()


def list_recent_luggage(session: Session, limit: int = 50) -> list[Luggage]:
    """Returns today's luggage items created after 00:00."""
    today_start = datetime.combine(date.today(), time.min)
    return (
        session.query(Luggage)
        .options(joinedload(Luggage.route), joinedload(Luggage.bus))
        .filter(Luggage.created_at >= today_start)
        .order_by(Luggage.created_at.desc())
        .limit(limit)
        .all()
    )


def today_luggage_stats(session: Session) -> dict:
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    count = (
        session.query(Luggage)
        .filter(Luggage.created_at >= start, Luggage.statut != "annule")
        .count()
    )
    weight = (
        session.query(func.coalesce(func.sum(Luggage.poids), 0))
        .filter(Luggage.created_at >= start, Luggage.statut != "annule")
        .scalar()
    )
    yesterday = today.fromordinal(today.toordinal() - 1)
    y_start = datetime.combine(yesterday, datetime.min.time())
    y_count = (
        session.query(Luggage)
        .filter(
            Luggage.created_at >= y_start,
            Luggage.created_at < start,
            Luggage.statut != "annule",
        )
        .count()
    )
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
