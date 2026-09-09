"""Run multi-agency migration (Lubumbashi / Kolwezi)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.connection import init_connection
from database.init_db import init_database


def main() -> None:
    print("Migration multi-agences en cours...")
    init_database()
    print("Migration terminée.")
    print("Comptes admin :")
    print("  - admin_lubumbashi (agence Lubumbashi)")
    print("  - admin_kolwezi / Kolwezi2026! (agence Kolwezi)")


if __name__ == "__main__":
    main()
