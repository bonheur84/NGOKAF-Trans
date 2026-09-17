"""Read-only connectivity check for a managed MySQL database.

Usage: python scripts/cloud_db_preflight.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text

from config.settings import settings
from database.connection import get_engine


def main() -> None:
    if settings.DB_HOST in {"", "localhost", "127.0.0.1"}:
        print("[ATTENTION] DB_HOST est local : configurez .env avant le test cloud.")
    if settings.DB_SSL_MODE == "verify_ca" and not settings.DB_SSL_CA:
        raise SystemExit("[ERREUR] DB_SSL_CA est requis pour verify_ca.")

    engine = get_engine()
    with engine.connect() as conn:
        server_version = conn.execute(text("SELECT VERSION()")).scalar_one()
        database = conn.execute(text("SELECT DATABASE()")).scalar_one()
        tls = conn.execute(text("SHOW STATUS LIKE 'Ssl_cipher'")).first()

    tls_cipher = tls[1] if tls and tls[1] else "non chiffré"
    print("[OK] Connexion MySQL établie")
    print(f"     Hôte : {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"     Base : {database}")
    print(f"     MySQL : {server_version}")
    print(f"     TLS : {tls_cipher}")
    if settings.DB_SSL_MODE not in {"", "disabled", "false", "off", "none"} and not tls_cipher:
        raise SystemExit("[ERREUR] TLS demandé mais non actif.")


if __name__ == "__main__":
    main()
