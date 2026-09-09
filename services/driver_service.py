"""Driver CRUD service."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session, joinedload

from models.driver import Driver
from services.agency_context import current_agency_id, require_agency_id
from services.audit_service import log_audit
from services.notification_service import notify


def list_drivers(
    session: Session,
    *,
    search: str = "",
    statut: str | None = None,
    agency_id: int | None = None,
) -> list[Driver]:
    aid = agency_id if agency_id is not None else current_agency_id()
    q = session.query(Driver).options(joinedload(Driver.bus))
    if aid is not None:
        q = q.filter(Driver.agency_id == aid)
    if statut:
        q = q.filter(Driver.statut == statut)
    if search.strip():
        s = f"%{search.strip()}%"
        q = q.filter(
            (Driver.nom.ilike(s))
            | (Driver.prenom.ilike(s))
            | (Driver.telephone.ilike(s))
            | (Driver.numero_permis.ilike(s))
        )
    return q.order_by(Driver.nom, Driver.prenom).all()


def get_driver(session: Session, driver_id: int, agency_id: int | None = None) -> Driver | None:
    driver = session.get(Driver, driver_id)
    if not driver:
        return None
    aid = agency_id if agency_id is not None else current_agency_id()
    if aid is not None and driver.agency_id != aid:
        return None
    return driver


def create_driver(
    session: Session,
    *,
    nom: str,
    prenom: str,
    telephone: str | None = None,
    adresse: str | None = None,
    numero_permis: str | None = None,
    date_expiration_permis: date | None = None,
    photo_path: str | None = None,
    bus_id: int | None = None,
    statut: str = "actif",
    disponibilite: str = "disponible",
    user_id: int | None = None,
    agency_id: int | None = None,
) -> Driver:
    aid = agency_id if agency_id is not None else require_agency_id()
    if bus_id:
        from services.bus_service import get_bus
        if not get_bus(session, bus_id, aid):
            raise ValueError("Bus introuvable dans votre agence.")
    d = Driver(
        nom=nom.strip(),
        prenom=prenom.strip(),
        telephone=(telephone or "").strip() or None,
        adresse=(adresse or "").strip() or None,
        numero_permis=(numero_permis or "").strip() or None,
        date_expiration_permis=date_expiration_permis,
        photo_path=photo_path,
        bus_id=bus_id,
        statut=statut,
        disponibilite=disponibilite,
        agency_id=aid,
    )
    session.add(d)
    session.flush()
    log_audit(session, "create", "driver", d.id, user_id, {"name": d.full_name})
    notify(session, f"Conducteur créé : {d.full_name}", user_id, agency_id=aid)
    return d


def update_driver(session: Session, driver: Driver, user_id: int | None = None, **fields) -> Driver:
    aid = current_agency_id()
    if aid is not None and driver.agency_id != aid:
        raise ValueError("Conducteur hors de votre agence.")
    if fields.get("bus_id"):
        from services.bus_service import get_bus
        if not get_bus(session, fields["bus_id"], driver.agency_id):
            raise ValueError("Bus introuvable dans votre agence.")
    for k, v in fields.items():
        if hasattr(driver, k):
            if isinstance(v, str) and k in ("nom", "prenom", "telephone", "adresse", "numero_permis"):
                v = v.strip() or None if k not in ("nom", "prenom") else v.strip()
            setattr(driver, k, v)
    session.flush()
    log_audit(session, "update", "driver", driver.id, user_id)
    return driver


def set_driver_statut(
    session: Session, driver: Driver, statut: str, user_id: int | None = None
) -> Driver:
    aid = current_agency_id()
    if aid is not None and driver.agency_id != aid:
        raise ValueError("Conducteur hors de votre agence.")
    driver.statut = statut
    session.flush()
    log_audit(session, "update", "driver", driver.id, user_id, {"statut": statut})
    return driver


def delete_driver(session: Session, driver: Driver, user_id: int | None = None) -> None:
    aid = current_agency_id()
    if aid is not None and driver.agency_id != aid:
        raise ValueError("Conducteur hors de votre agence.")
    did = driver.id
    name = driver.full_name
    session.delete(driver)
    log_audit(session, "delete", "driver", did, user_id, {"name": name})
    notify(session, f"Conducteur supprimé : {name}", user_id, agency_id=driver.agency_id)
