"""In-app notifications with types and icons."""
from __future__ import annotations

from sqlalchemy.orm import Session

from models.notification import Notification, NotificationType


def notify(
    session: Session,
    title: str,
    message: str,
    user_id: int | None = None,
    notif_type: str = NotificationType.INFO,
    icon: str = "bell",
) -> Notification:
    """Create a new notification with type and icon."""
    n = Notification(
        title=title,
        message=message,
        user_id=user_id,
        notif_type=notif_type,
        icon=icon,
        lu=False
    )
    session.add(n)
    session.flush()
    return n


def notify_bus_full(session: Session, bus_id: int, bus_name: str, user_id: int | None = None) -> Notification:
    """Notify when a bus is full (100% occupied)."""
    return notify(
        session,
        title="Bus complet",
        message=f"Le bus {bus_name} est maintenant complet (100% des sièges occupés).",
        user_id=user_id,
        notif_type=NotificationType.BUS_FULL,
        icon="bus"
    )


def notify_seats_low(session: Session, bus_id: int, bus_name: str, seats_remaining: int, user_id: int | None = None) -> Notification:
    """Notify when only a few seats remain (5 or less)."""
    return notify(
        session,
        title="Sièges limités",
        message=f"Le bus {bus_name} n'a plus que {seats_remaining} sièges disponibles.",
        user_id=user_id,
        notif_type=NotificationType.SEATS_LOW,
        icon="chair"
    )


def notify_backup_success(session: Session, backup_name: str, user_id: int | None = None) -> Notification:
    """Notify when backup succeeds."""
    return notify(
        session,
        title="Sauvegarde réussie",
        message=f"La sauvegarde {backup_name} a été créée avec succès.",
        user_id=user_id,
        notif_type=NotificationType.BACKUP_SUCCESS,
        icon="check-circle"
    )


def notify_backup_failed(session: Session, error: str, user_id: int | None = None) -> Notification:
    """Notify when backup fails."""
    return notify(
        session,
        title="Échec sauvegarde",
        message=f"La sauvegarde a échoué : {error}",
        user_id=user_id,
        notif_type=NotificationType.BACKUP_FAILED,
        icon="alert-circle"
    )


def notify_ticket_cancelled(session: Session, ticket_number: str, user_id: int | None = None) -> Notification:
    """Notify when a ticket is cancelled."""
    return notify(
        session,
        title="Billet annulé",
        message=f"Le billet {ticket_number} a été annulé.",
        user_id=user_id,
        notif_type=NotificationType.TICKET_CANCELLED,
        icon="x-circle"
    )


def notify_bagage_registered(session: Session, bagage_number: str, user_id: int | None = None) -> Notification:
    """Notify when baggage is registered."""
    return notify(
        session,
        title="Bagage enregistré",
        message=f"Le bagage {bagage_number} a été enregistré.",
        user_id=user_id,
        notif_type=NotificationType.BAGAGE_REGISTERED,
        icon="package"
    )


def notify_trajet_cancelled(session: Session, trajet_name: str, user_id: int | None = None) -> Notification:
    """Notify when a route is cancelled."""
    return notify(
        session,
        title="Trajet annulé",
        message=f"Le trajet {trajet_name} a été annulé.",
        user_id=user_id,
        notif_type=NotificationType.TRAJET_CANCELLED,
        icon="map"
    )


def notify_conducteur_unavailable(session: Session, conducteur_name: str, user_id: int | None = None) -> Notification:
    """Notify when a driver is unavailable."""
    return notify(
        session,
        title="Conducteur indisponible",
        message=f"Le conducteur {conducteur_name} est marqué comme indisponible.",
        user_id=user_id,
        notif_type=NotificationType.CONDUCTEUR_UNAVAILABLE,
        icon="user-x"
    )


def notify_critical_error(session: Session, error: str, user_id: int | None = None) -> Notification:
    """Notify when a critical error occurs."""
    return notify(
        session,
        title="Erreur critique",
        message=f"Une erreur critique est survenue : {error}",
        user_id=user_id,
        notif_type=NotificationType.CRITICAL_ERROR,
        icon="alert-triangle"
    )


def list_notifications(
    session: Session,
    user_id: int | None = None,
    unread_only: bool = False,
    limit: int = 50,
) -> list[Notification]:
    q = session.query(Notification)
    if user_id is not None:
        Q = q.filter(
            (Notification.user_id == user_id) | (Notification.user_id.is_(None))
        )
    if unread_only:
        q = q.filter(Notification.lu.is_(False))
    return q.order_by(Notification.created_at.desc()).limit(limit).all()


def unread_count(session: Session, user_id: int | None = None) -> int:
    q = session.query(Notification).filter(Notification.lu.is_(False))
    if user_id is not None:
        q = q.filter(
            (Notification.user_id == user_id) | (Notification.user_id.is_(None))
        )
    return q.count()


def mark_all_read(session: Session, user_id: int | None = None) -> None:
    q = session.query(Notification).filter(Notification.lu.is_(False))
    if user_id is not None:
        q = q.filter(
            (Notification.user_id == user_id) | (Notification.user_id.is_(None))
        )
    for n in q.all():
        n.lu = True


def mark_read(session: Session, notif_id: int) -> None:
    n = session.get(Notification, notif_id)
    if n:
        n.lu = True


def delete_notification(session: Session, notif_id: int) -> None:
    n = session.get(Notification, notif_id)
    if n:
        session.delete(n)


def delete_all_read(session: Session, user_id: int | None = None) -> None:
    q = session.query(Notification).filter(Notification.lu.is_(True))
    if user_id is not None:
        q = q.filter(
            (Notification.user_id == user_id) | (Notification.user_id.is_(None))
        )
    for n in q.all():
        session.delete(n)
