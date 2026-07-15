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
    ],
    "buses": [
        ("plaque", "VARCHAR(40) NULL"),
        ("marque", "VARCHAR(80) NULL"),
        ("modele", "VARCHAR(80) NULL"),
        ("annee", "INT NULL"),
        ("couleur", "VARCHAR(40) NULL"),
        ("photo_path", "VARCHAR(512) NULL"),
        ("date_achat", "DATE NULL"),
    ],
    "routes": [
        ("heure_arrivee", "TIME NULL"),
        ("distance_km", "DECIMAL(10,2) NULL"),
        ("driver_id", "INT NULL"),
    ],
    "notifications": [
        ("title", "VARCHAR(200) NULL"),
        ("notif_type", "VARCHAR(50) NULL DEFAULT 'info'"),
        ("icon", "VARCHAR(50) NULL DEFAULT 'bell'"),
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
