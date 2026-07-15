"""Authentication service with bcrypt."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import bcrypt
from sqlalchemy.orm import Session

from config.settings import settings
from models.user import User
from services.audit_service import log_audit, log_login


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def count_users(session: Session) -> int:
    return session.query(User).count()


def create_cashier(
    session: Session,
    nom: str,
    prenom: str,
    telephone: str,
    username: str,
    password: str,
    photo_path: str | None = None,
) -> User:
    user = User(
        nom=nom.strip(),
        prenom=prenom.strip(),
        telephone=telephone.strip() or None,
        username=username.strip(),
        password_hash=hash_password(password),
        photo_path=photo_path,
        role="caissier",
        statut="actif",
    )
    session.add(user)
    session.flush()
    log_audit(
        session,
        "create",
        "user",
        user.id,
        user.id,
        {"username": user.username},
    )
    return user


def authenticate(session: Session, username: str, password: str) -> User | None:
    user = (
        session.query(User)
        .filter(User.username == username.strip(), User.statut == "actif")
        .first()
    )
    if not user or not verify_password(password, user.password_hash):
        log_login(session, username, False, user.id if user else None, "Identifiants invalides")
        session.commit()
        return None
    user.last_login = datetime.now()
    log_login(session, username, True, user.id, "Connexion réussie")
    log_audit(session, "login", "user", user.id, user.id)
    session.commit()
    return user


def save_remember_username(username: str) -> None:
    settings.REMEMBER_FILE.parent.mkdir(parents=True, exist_ok=True)
    settings.REMEMBER_FILE.write_text(username, encoding="utf-8")


def load_remember_username() -> str:
    path: Path = settings.REMEMBER_FILE
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def clear_remember_username() -> None:
    path: Path = settings.REMEMBER_FILE
    if path.exists():
        path.unlink()


def ensure_default_admin(session: Session) -> User | None:
    """Create default admin/admin123 if no administrator exists."""
    admin = (
        session.query(User)
        .filter(User.role == "administrateur")
        .first()
    )
    if admin:
        return admin
    user = User(
        nom="Admin",
        prenom="Système",
        telephone=None,
        email="admin@ngokaf.local",
        username="admin",
        password_hash=hash_password("admin123"),
        role="administrateur",
        statut="actif",
    )
    session.add(user)
    session.flush()
    log_audit(session, "seed", "user", user.id, user.id, {"username": "admin"})
    return user


def count_admins(session: Session) -> int:
    return session.query(User).filter(User.role == "administrateur").count()
