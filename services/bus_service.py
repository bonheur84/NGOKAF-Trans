"""Bus / route / seat helpers."""
from __future__ import annotations

from datetime import date, time
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from models.bus import Bus, Seat
from models.route import Route
from services.audit_service import log_audit
from services.notification_service import notify


def create_bus_with_seats(
    session: Session,
    code: str,
    capacite: int = 60,
    layout: str = "2-2",
    user_id: int | None = None,
    *,
    plaque: str | None = None,
    marque: str | None = None,
    modele: str | None = None,
    annee: int | None = None,
    couleur: str | None = None,
    photo_path: str | None = None,
    date_achat: date | None = None,
    statut: str = "actif",
) -> Bus:
    bus = Bus(
        code=code.strip().upper(),
        capacite=capacite,
        layout=layout,
        statut=statut,
        plaque=(plaque or "").strip() or None,
        marque=(marque or "").strip() or None,
        modele=(modele or "").strip() or None,
        annee=annee,
        couleur=(couleur or "").strip() or None,
        photo_path=photo_path,
        date_achat=date_achat,
    )
    session.add(bus)
    session.flush()
    for n in range(1, capacite + 1):
        session.add(Seat(bus_id=bus.id, numero=n))
    log_audit(session, "create", "bus", bus.id, user_id, {"code": bus.code})
    notify(session, f"Bus créé : {bus.code}", user_id)
    return bus


def regenerate_seats(session: Session, bus: Bus, capacite: int) -> None:
    session.query(Seat).filter(Seat.bus_id == bus.id).delete()
    bus.capacite = capacite
    for n in range(1, capacite + 1):
        session.add(Seat(bus_id=bus.id, numero=n))
    session.flush()


def update_bus(session: Session, bus: Bus, user_id: int | None = None, **fields) -> Bus:
    cap = fields.pop("capacite", None)
    for k, v in fields.items():
        if hasattr(bus, k):
            if isinstance(v, str) and k in ("code", "plaque", "marque", "modele", "couleur"):
                v = v.strip().upper() if k == "code" else (v.strip() or None)
            setattr(bus, k, v)
    if cap is not None and int(cap) != bus.capacite:
        regenerate_seats(session, bus, int(cap))
    session.flush()
    log_audit(session, "update", "bus", bus.id, user_id)
    return bus


def set_bus_statut(session: Session, bus: Bus, statut: str, user_id: int | None = None) -> Bus:
    bus.statut = statut
    session.flush()
    log_audit(session, "update", "bus", bus.id, user_id, {"statut": statut})
    if statut != "actif":
        notify(session, f"Bus désactivé : {bus.code}", user_id)
    return bus


def delete_bus(session: Session, bus: Bus, user_id: int | None = None) -> None:
    if bus.routes:
        raise ValueError("Ce bus est lié à des trajets. Désactivez-le plutôt.")
    bid = bus.id
    code = bus.code
    session.delete(bus)
    log_audit(session, "delete", "bus", bid, user_id, {"code": code})
    notify(session, f"Bus supprimé : {code}", user_id)


def list_buses(
    session: Session,
    *,
    search: str = "",
    statut: str | None = None,
) -> list[Bus]:
    q = session.query(Bus)
    if statut:
        q = q.filter(Bus.statut == statut)
    if search.strip():
        s = f"%{search.strip()}%"
        q = q.filter(
            (Bus.code.ilike(s))
            | (Bus.plaque.ilike(s))
            | (Bus.marque.ilike(s))
            | (Bus.modele.ilike(s))
        )
    return q.order_by(Bus.code).all()


def get_bus(session: Session, bus_id: int) -> Bus | None:
    return session.get(Bus, bus_id)


def create_route(
    session: Session,
    ville_depart: str,
    ville_arrivee: str,
    heure_depart: time,
    bus_id: int,
    prix_indicatif: Decimal | None = None,
    user_id: int | None = None,
    *,
    heure_arrivee: time | None = None,
    distance_km: Decimal | None = None,
    driver_id: int | None = None,
    statut: str = "actif",
) -> Route:
    route = Route(
        ville_depart=ville_depart.strip(),
        ville_arrivee=ville_arrivee.strip(),
        heure_depart=heure_depart,
        heure_arrivee=heure_arrivee,
        distance_km=distance_km,
        prix_indicatif=prix_indicatif,
        bus_id=bus_id,
        driver_id=driver_id,
        statut=statut,
    )
    session.add(route)
    session.flush()
    log_audit(session, "create", "route", route.id, user_id)
    notify(
        session,
        f"Trajet créé : {route.ville_depart} → {route.ville_arrivee}",
        user_id,
    )
    return route


def update_route(session: Session, route: Route, user_id: int | None = None, **fields) -> Route:
    for k, v in fields.items():
        if hasattr(route, k):
            if isinstance(v, str) and k in ("ville_depart", "ville_arrivee"):
                v = v.strip()
            setattr(route, k, v)
    session.flush()
    log_audit(session, "update", "route", route.id, user_id)
    return route


def set_route_statut(
    session: Session, route: Route, statut: str, user_id: int | None = None
) -> Route:
    route.statut = statut
    session.flush()
    log_audit(session, "update", "route", route.id, user_id, {"statut": statut})
    if statut != "actif":
        notify(
            session,
            f"Trajet désactivé : {route.ville_depart} → {route.ville_arrivee}",
            user_id,
        )
    return route


def delete_route(session: Session, route: Route, user_id: int | None = None) -> None:
    rid = route.id
    label = f"{route.ville_depart} → {route.ville_arrivee}"
    session.delete(route)
    log_audit(session, "delete", "route", rid, user_id, {"label": label})
    notify(session, f"Trajet supprimé : {label}", user_id)


def list_routes(
    session: Session,
    *,
    search: str = "",
    statut: str | None = None,
    ville: str = "",
) -> list[Route]:
    q = (
        session.query(Route)
        .options(joinedload(Route.bus), joinedload(Route.driver))
    )
    if statut:
        q = q.filter(Route.statut == statut)
    if ville.strip():
        v = f"%{ville.strip()}%"
        q = q.filter(
            (Route.ville_depart.ilike(v)) | (Route.ville_arrivee.ilike(v))
        )
    if search.strip():
        s = f"%{search.strip()}%"
        q = q.filter(
            (Route.ville_depart.ilike(s))
            | (Route.ville_arrivee.ilike(s))
        )
    return q.order_by(Route.ville_depart, Route.heure_depart).all()


def list_active_routes(session: Session) -> list[Route]:
    return (
        session.query(Route)
        .options(joinedload(Route.bus))
        .filter(Route.statut == "actif")
        .order_by(Route.ville_depart, Route.heure_depart)
        .all()
    )


def get_route(session: Session, route_id: int) -> Route | None:
    return session.get(Route, route_id)
