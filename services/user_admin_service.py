"""Admin user / cashier management."""
from __future__ import annotations

from sqlalchemy.orm import Session

from models.user import User
from services.auth_service import hash_password
from services.audit_service import log_audit
from services.notification_service import notify


def list_users(
    session: Session,
    *,
    role: str | None = None,
    search: str = "",
    statut: str | None = None,
) -> list[User]:
    q = session.query(User)
    if role:
        q = q.filter(User.role == role)
    if statut:
        q = q.filter(User.statut == statut)
    if search.strip():
        s = f"%{search.strip()}%"
        q = q.filter(
            (User.nom.ilike(s))
            | (User.prenom.ilike(s))
            | (User.username.ilike(s))
            | (User.telephone.ilike(s))
            | (User.email.ilike(s))
        )
    return q.order_by(User.role.desc(), User.nom).all()


def get_user(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)


def create_user(
    session: Session,
    *,
    nom: str,
    prenom: str,
    username: str,
    password: str,
    role: str = "caissier",
    telephone: str | None = None,
    email: str | None = None,
    adresse: str | None = None,
    photo_path: str | None = None,
    actor_id: int | None = None,
) -> User:
    if session.query(User).filter(User.username == username.strip()).first():
        raise ValueError(f"Le nom d'utilisateur « {username} » existe déjà.")
    user = User(
        nom=nom.strip(),
        prenom=prenom.strip(),
        username=username.strip(),
        password_hash=hash_password(password),
        role=role,
        telephone=(telephone or "").strip() or None,
        email=(email or "").strip() or None,
        adresse=(adresse or "").strip() or None,
        photo_path=photo_path,
        statut="actif",
    )
    session.add(user)
    session.flush()
    log_audit(
        session,
        "create",
        "user",
        user.id,
        actor_id,
        {"username": user.username, "role": role},
    )
    notify(session, f"Compte créé : {user.username} ({role})", actor_id)
    return user


def update_user(session: Session, user: User, actor_id: int | None = None, **fields) -> User:
    if "username" in fields and fields["username"]:
        other = (
            session.query(User)
            .filter(User.username == fields["username"].strip(), User.id != user.id)
            .first()
        )
        if other:
            raise ValueError(f"Le nom d'utilisateur « {fields['username']} » existe déjà.")
        fields["username"] = fields["username"].strip()
    for k, v in fields.items():
        if k == "password":
            continue
        if hasattr(user, k):
            if isinstance(v, str) and k in ("nom", "prenom", "telephone", "email", "adresse"):
                v = v.strip() or None if k not in ("nom", "prenom") else v.strip()
            setattr(user, k, v)
    session.flush()
    log_audit(session, "update", "user", user.id, actor_id)
    return user


def reset_password(
    session: Session, user: User, new_password: str, actor_id: int | None = None
) -> None:
    user.password_hash = hash_password(new_password)
    session.flush()
    log_audit(session, "reset_password", "user", user.id, actor_id)
    notify(session, f"Mot de passe réinitialisé pour {user.username}", actor_id)


def set_user_statut(
    session: Session, user: User, statut: str, actor_id: int | None = None
) -> User:
    user.statut = statut
    session.flush()
    log_audit(session, "update", "user", user.id, actor_id, {"statut": statut})
    label = "bloqué" if statut != "actif" else "réactivé"
    notify(session, f"Utilisateur {user.username} {label}", actor_id)
    return user


def delete_user(session: Session, user: User, actor_id: int | None = None) -> None:
    if user.role == "administrateur":
        admins = session.query(User).filter(User.role == "administrateur").count()
        if admins <= 1:
            raise ValueError("Impossible de supprimer le dernier administrateur.")
    uid = user.id
    uname = user.username
    session.delete(user)
    log_audit(session, "delete", "user", uid, actor_id, {"username": uname})
    notify(session, f"Utilisateur supprimé : {uname}", actor_id)


def change_admin_password(
    session: Session, admin: User, old_password: str, new_password: str
) -> None:
    from services.auth_service import verify_password

    if not verify_password(old_password, admin.password_hash):
        raise ValueError("Mot de passe actuel incorrect.")
    admin.password_hash = hash_password(new_password)
    session.flush()
    log_audit(session, "change_password", "user", admin.id, admin.id)
