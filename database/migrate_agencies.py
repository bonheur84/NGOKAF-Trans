"""Data migration for multi-agency support (Lubumbashi / Kolwezi)."""
from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from models.agency import Agency
from models.app_setting import AppSetting
from models.user import User
from services.agency_service import ensure_agencies
from services.auth_service import hash_password
from services.settings_service import DEFAULTS, ensure_agency_settings

logger = logging.getLogger(__name__)

TABLES_WITH_AGENCY = [
    "users",
    "buses",
    "drivers",
    "routes",
    "tickets",
    "luggage",
    "expenses",
    "sequences",
    "notifications",
]


def _table_exists(engine: Engine, table: str) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table
                """
            ),
            {"table": table},
        ).scalar()
        return bool(row)


def _constraint_exists(engine: Engine, table: str, name: str) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = :table
                  AND CONSTRAINT_NAME = :name
                """
            ),
            {"table": table, "name": name},
        ).scalar()
        return bool(row)


def _index_exists(engine: Engine, table: str, name: str) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = :table
                  AND INDEX_NAME = :name
                """
            ),
            {"table": table, "name": name},
        ).scalar()
        return bool(row)


def migrate_agency_constraints(engine: Engine) -> None:
    """Adjust unique constraints for per-agency scoping."""
    alters = [
        ("buses", "code", "uq_bus_agency_code", "UNIQUE KEY `uq_bus_agency_code` (`agency_id`, `code`)"),
        ("luggage", "numero", "uq_luggage_agency_numero", "UNIQUE KEY `uq_luggage_agency_numero` (`agency_id`, `numero`)"),
        ("app_settings", "key", "uq_setting_agency_key", "UNIQUE KEY `uq_setting_agency_key` (`agency_id`, `key`)"),
        ("sequences", "name", "uq_sequence_agency_day", "UNIQUE KEY `uq_sequence_agency_day` (`agency_id`, `name`, `seq_date`)"),
        ("tickets", "numero", "uq_ticket_agency_day_number", "UNIQUE KEY `uq_ticket_agency_day_number` (`agency_id`, `date_vente`, `numero`)"),
    ]
    drop_constraints = [
        ("buses", "code"),
        ("luggage", "numero"),
        ("app_settings", "key"),
        ("sequences", "name"),
        ("tickets", "numero"),
    ]
    old_unique_names = [
        ("buses", "code"),
        ("luggage", "numero"),
        ("app_settings", "key"),
        ("app_settings", "ix_app_settings_key"),
        ("sequences", "uq_sequence_day"),
        ("tickets", "uq_ticket_day_number"),
    ]
    with engine.begin() as conn:
        for table, col in drop_constraints:
            if not _table_exists(engine, table):
                continue
            idx = col
            if _index_exists(engine, table, idx):
                try:
                    conn.execute(text(f"ALTER TABLE `{table}` DROP INDEX `{idx}`"))
                    logger.info("Dropped index %s.%s", table, idx)
                except Exception as e:
                    logger.warning("Could not drop index %s.%s: %s", table, idx, e)
        for table, cname in old_unique_names:
            if _constraint_exists(engine, table, cname):
                try:
                    conn.execute(text(f"ALTER TABLE `{table}` DROP INDEX `{cname}`"))
                except Exception:
                    pass
        for table, _col, cname, ddl in alters:
            if not _table_exists(engine, table):
                continue
            if _index_exists(engine, table, cname):
                continue
            try:
                conn.execute(text(f"ALTER TABLE `{table}` ADD {ddl}"))
                logger.info("Added constraint %s on %s", cname, table)
            except Exception as e:
                logger.warning("Could not add %s on %s: %s", cname, table, e)


def migrate_agency_data(session: Session) -> None:
    """Seed agencies, attach existing data to Lubumbashi, create Kolwezi admin."""
    agencies = ensure_agencies(session)
    lubumbashi = agencies["lubumbashi"]
    kolwezi = agencies["kolwezi"]

    admin_kol = session.query(User).filter(User.username == "admin_kolwezi").first()
    already_migrated = bool(admin_kol and admin_kol.agency_id == kolwezi.id)

    if not already_migrated:
        for table in TABLES_WITH_AGENCY:
            session.execute(
                text(f"UPDATE `{table}` SET agency_id = :aid WHERE agency_id IS NULL"),
                {"aid": lubumbashi.id},
            )

        # app_settings: avoid unique (agency_id, key) conflicts
        orphans = session.query(AppSetting).filter(AppSetting.agency_id.is_(None)).all()
        for row in orphans:
            exists = (
                session.query(AppSetting)
                .filter(AppSetting.key == row.key, AppSetting.agency_id == lubumbashi.id)
                .first()
            )
            if exists:
                session.delete(row)
            else:
                row.agency_id = lubumbashi.id

        session.query(User).filter(User.agency_id.is_(None)).update(
            {"agency_id": lubumbashi.id}, synchronize_session=False
        )

    # Ensure admin_lubumbashi exists and is linked to Lubumbashi
    admin_lub = session.query(User).filter(User.username == "admin_lubumbashi").first()
    if admin_lub:
        admin_lub.agency_id = lubumbashi.id
        admin_lub.role = "administrateur"
    else:
        legacy = session.query(User).filter(User.username == "admin").first()
        if legacy and legacy.role == "administrateur":
            legacy.username = "admin_lubumbashi"
            legacy.agency_id = lubumbashi.id
            legacy.nom = legacy.nom or "Admin"
            legacy.prenom = legacy.prenom or "Lubumbashi"
        else:
            session.add(
                User(
                    nom="Admin",
                    prenom="Lubumbashi",
                    username="admin_lubumbashi",
                    password_hash=hash_password("Lubumbashi2026!"),
                    role="administrateur",
                    statut="actif",
                    agency_id=lubumbashi.id,
                )
            )

    if not admin_kol:
        session.add(
            User(
                nom="Admin",
                prenom="Kolwezi",
                username="admin_kolwezi",
                password_hash=hash_password("Kolwezi2026!"),
                role="administrateur",
                statut="actif",
                agency_id=kolwezi.id,
            )
        )
    else:
        admin_kol.agency_id = kolwezi.id
        admin_kol.role = "administrateur"

    ensure_agency_settings(session, lubumbashi.id)
    ensure_agency_settings(session, kolwezi.id, defaults={
        "agency_name": kolwezi.name,
        "agency_address": kolwezi.address or "Kolwezi, RDC",
        "agency_phone": kolwezi.phone or "",
        "terminal_name": f"TERMINAL {kolwezi.city.upper()}",
    })

    session.flush()
    logger.info("Agency data migration complete (Lubumbashi id=%s, Kolwezi id=%s)", lubumbashi.id, kolwezi.id)


def run_agency_migration(engine: Engine, session: Session) -> None:
    migrate_agency_constraints(engine)
    migrate_agency_data(session)
