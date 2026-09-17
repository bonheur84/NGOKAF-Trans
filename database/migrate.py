"""Schema migration helper for adding columns to existing tables."""
from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# table -> list of (column, DDL fragment without column name)
ALTERS: dict[str, list[tuple[str, str]]] = {
    "users": [
        ("email", "VARCHAR(150) NULL"),
        ("adresse", "VARCHAR(255) NULL"),
        ("agency_id", "INT NULL"),
    ],
    "buses": [
        ("plaque", "VARCHAR(40) NULL"),
        ("marque", "VARCHAR(80) NULL"),
        ("modele", "VARCHAR(80) NULL"),
        ("annee", "INT NULL"),
        ("couleur", "VARCHAR(40) NULL"),
        ("photo_path", "VARCHAR(512) NULL"),
        ("date_achat", "DATE NULL"),
        ("agency_id", "INT NULL"),
    ],
    "routes": [
        ("heure_arrivee", "TIME NULL"),
        ("distance_km", "DECIMAL(10,2) NULL"),
        ("driver_id", "INT NULL"),
        ("agency_id", "INT NULL"),
    ],
    "notifications": [
        ("title", "VARCHAR(200) NULL"),
        ("notif_type", "VARCHAR(50) NULL DEFAULT 'info'"),
        ("icon", "VARCHAR(50) NULL DEFAULT 'bell'"),
        ("agency_id", "INT NULL"),
    ],
    "expenses": [
        ("piece_jointe", "VARCHAR(500) NULL"),
        ("agency_id", "INT NULL"),
    ],
    "drivers": [
        ("agency_id", "INT NULL"),
    ],
    "tickets": [
        ("agency_id", "INT NULL"),
        ("luggage_code", "VARCHAR(30) NULL"),
    ],
    "luggage": [
        ("agency_id", "INT NULL"),
        ("ticket_id", "INT NULL"),
        ("ticket_numero", "VARCHAR(20) NULL"),
        ("route_label", "VARCHAR(255) NULL"),
        ("bus_code", "VARCHAR(50) NULL"),
    ],
    "sequences": [
        ("agency_id", "INT NULL"),
    ],
    "app_settings": [
        ("agency_id", "INT NULL"),
    ],
}


def _column_exists(engine: Engine, table: str, column: str) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = :table
                  AND COLUMN_NAME = :column
                """
            ),
            {"table": table, "column": column},
        ).scalar()
        return bool(row)


def migrate_schema(engine: Engine) -> None:
    """Add missing columns on existing MySQL tables."""
    with engine.begin() as conn:
        for table, cols in ALTERS.items():
            for col, ddl in cols:
                if _column_exists(engine, table, col):
                    continue
                try:
                    conn.execute(text(f"ALTER TABLE `{table}` ADD COLUMN `{col}` {ddl}"))
                    logger.info("Added column %s.%s", table, col)
                except Exception as e:
                    logger.warning("Could not add %s.%s: %s", table, col, e)
        # FK for routes.driver_id if column exists and FK missing
        try:
            if _column_exists(engine, "routes", "driver_id"):
                conn.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME = 'routes'
                          AND CONSTRAINT_NAME = 'fk_routes_driver'
                        """
                    )
                )
                # Best-effort: ignore if already exists
                try:
                    conn.execute(
                        text(
                            """
                            ALTER TABLE `routes`
                            ADD CONSTRAINT `fk_routes_driver`
                            FOREIGN KEY (`driver_id`) REFERENCES `drivers`(`id`)
                            """
                        )
                    )
                except Exception:
                    pass
        except Exception:
            pass

        # Query paths used continuously by sales, baggage check-in, and KPI cards.
        # Each statement is idempotent in practice: duplicate-index errors are ignored.
        indexes = [
            "CREATE UNIQUE INDEX uq_tickets_luggage_code ON tickets (luggage_code)",
            "CREATE INDEX ix_tickets_agency_date_status ON tickets (agency_id, date_vente, statut)",
            "CREATE INDEX ix_tickets_agency_created ON tickets (agency_id, created_at)",
            "CREATE INDEX ix_tickets_seat_availability ON tickets (bus_id, route_id, travel_date, statut, seat_number)",
            "CREATE INDEX ix_luggage_agency_created_status ON luggage (agency_id, created_at, statut)",
            "CREATE INDEX ix_luggage_ticket_lookup ON luggage (ticket_id)",
        ]
        for statement in indexes:
            try:
                conn.execute(text(statement))
            except Exception:
                pass
        # FK for luggage.ticket_id if the link column exists and the FK is missing.
        try:
            if _column_exists(engine, "luggage", "ticket_id"):
                try:
                    conn.execute(
                        text(
                            """
                            ALTER TABLE `luggage`
                            ADD CONSTRAINT `fk_luggage_ticket`
                            FOREIGN KEY (`ticket_id`) REFERENCES `tickets`(`id`)
                            """
                        )
                    )
                except Exception:
                    pass
        except Exception:
            pass



# Columns to modify (make nullable) — format: (table, column, new DDL)
MODIFY_NULLABLE: list[tuple[str, str, str]] = [
    ("luggage", "route_id", "INT NULL"),
    ("luggage", "bus_id", "INT NULL"),
    ("luggage", "cashier_id", "INT NULL"),
    ("tickets", "cashier_id", "INT NULL"),
]


def _column_is_nullable(engine: Engine, table: str, column: str) -> bool:
    """Return True if the column already allows NULL."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT IS_NULLABLE FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = :table
                  AND COLUMN_NAME = :column
                """
            ),
            {"table": table, "column": column},
        ).fetchone()
        if row is None:
            return True  # column doesn't exist, skip
        return row[0] == "YES"


def migrate_nullable(engine: Engine) -> None:
    """Make specific columns nullable if they are currently NOT NULL."""
    with engine.begin() as conn:
        for table, col, ddl in MODIFY_NULLABLE:
            if _column_is_nullable(engine, table, col):
                continue
            try:
                conn.execute(text(f"ALTER TABLE `{table}` MODIFY COLUMN `{col}` {ddl}"))
                logger.info("Made nullable: %s.%s", table, col)
            except Exception as e:
                logger.warning("Could not modify %s.%s: %s", table, col, e)
