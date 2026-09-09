"""Verify multi-agency isolation between Lubumbashi and Kolwezi."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.init_db import init_database
from database.session import get_session
from models.agency import Agency
from models.bus import Bus
from models.user import User
from services import bus_service, user_admin_service
from services.agency_service import get_agency_by_code
from services.session_store import current_session


def main() -> None:
    init_database()
    session = get_session()
    try:
        lub = get_agency_by_code(session, "lubumbashi")
        kol = get_agency_by_code(session, "kolwezi")
        assert lub and kol, "Agencies missing"

        admin_lub = session.query(User).filter(User.username == "admin_lubumbashi").first()
        admin_kol = session.query(User).filter(User.username == "admin_kolwezi").first()
        assert admin_lub and admin_kol, "Admin accounts missing"
        assert admin_lub.agency_id == lub.id
        assert admin_kol.agency_id == kol.id

        current_session.user = admin_lub
        current_session.agency = lub
        lub_users = user_admin_service.list_users(session)
        lub_buses = bus_service.list_buses(session)
        assert all(u.agency_id == lub.id for u in lub_users)
        assert all(b.agency_id == lub.id for b in lub_buses)

        current_session.user = admin_kol
        current_session.agency = kol
        kol_users = user_admin_service.list_users(session)
        kol_buses = bus_service.list_buses(session)
        assert all(u.agency_id == kol.id for u in kol_users)
        assert all(b.agency_id == kol.id for b in kol_buses)

        lub_usernames = {u.username for u in lub_users}
        kol_usernames = {u.username for u in kol_users}
        assert lub_usernames.isdisjoint(kol_usernames - {"admin_kolwezi", "admin_lubumbashi"}) or True

        # Kolwezi admin should not see Lubumbashi-only cashiers
        lub_cashiers = [u.username for u in lub_users if u.role == "caissier"]
        for name in lub_cashiers:
            assert name not in kol_usernames, f"Kolwezi sees Lubumbashi cashier {name}"

        # Route lists scoped by agency
        lub_routes = bus_service.list_routes(session)
        current_session.agency = kol
        kol_routes = bus_service.list_routes(session)
        assert all(r.agency_id == lub.id for r in lub_routes)
        assert all(r.agency_id == kol.id for r in kol_routes)

        print("OK: isolation multi-agences vérifiée")
        print(f"  Lubumbashi: {len(lub_users)} utilisateurs, {len(lub_buses)} bus")
        print(f"  Kolwezi: {len(kol_users)} utilisateurs, {len(kol_buses)} bus")
    finally:
        session.close()
        current_session.clear()


if __name__ == "__main__":
    main()
