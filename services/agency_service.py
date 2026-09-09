"""Agency management and seed helpers."""
from __future__ import annotations

from sqlalchemy.orm import Session

from models.agency import Agency

AGENCY_DEFINITIONS = [
    {
        "code": "lubumbashi",
        "name": "NGOKAF TRANS Lubumbashi",
        "city": "Lubumbashi",
        "address": "Lubumbashi, RDC",
        "phone": "",
    },
    {
        "code": "kolwezi",
        "name": "NGOKAF TRANS Kolwezi",
        "city": "Kolwezi",
        "address": "Kolwezi, RDC",
        "phone": "",
    },
]


def get_agency_by_code(session: Session, code: str) -> Agency | None:
    return session.query(Agency).filter(Agency.code == code.strip().lower()).first()


def get_agency(session: Session, agency_id: int) -> Agency | None:
    return session.get(Agency, agency_id)


def ensure_agencies(session: Session) -> dict[str, Agency]:
    """Ensure Lubumbashi and Kolwezi agencies exist. Returns code -> Agency map."""
    result: dict[str, Agency] = {}
    for spec in AGENCY_DEFINITIONS:
        agency = get_agency_by_code(session, spec["code"])
        if not agency:
            agency = Agency(
                code=spec["code"],
                name=spec["name"],
                city=spec["city"],
                address=spec["address"],
                phone=spec["phone"],
                statut="actif",
            )
            session.add(agency)
            session.flush()
        result[spec["code"]] = agency
    return result


def validate_route_cities(agency: Agency, ville_depart: str, ville_arrivee: str) -> None:
    """Ensure route direction matches agency city."""
    depart = ville_depart.strip()
    arrivee = ville_arrivee.strip()
    expected_dest = agency.destination_city
    if depart.lower() != agency.city.lower():
        raise ValueError(
            f"La ville de départ doit être « {agency.city} » pour l'agence {agency.name}."
        )
    if expected_dest and arrivee.lower() != expected_dest.lower():
        raise ValueError(
            f"La ville d'arrivée doit être « {expected_dest} » pour l'agence {agency.name}."
        )
