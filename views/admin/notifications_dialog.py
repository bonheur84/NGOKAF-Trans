"""Notifications popup for admin header with icons and actions."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QFrame,
)

from database.session import get_session
from resources import theme as T
from services import notification_service
from services.session_store import current_session
from utils.icons import fa_icon, ICONS


class NotificationsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notifications")
        self.resize(450, 520)
        lay = QVBoxLayout(self)
        
        # Header with title and actions
        header = QHBoxLayout()
        title = QLabel("Notifications")
        title.setStyleSheet(f"font-size:18px; font-weight:700; color:{T.TEXT_PRIMARY};")
        header.addWidget(title)
        header.addStretch()
        
        delete_read = QPushButton("Supprimer lues")
        delete_read.setObjectName("secondaryBtn")
        delete_read.clicked.connect(self._delete_read)
        header.addWidget(delete_read)
        lay.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border:none;")
        self.body = QWidget()
        self.body_lay = QVBoxLayout(self.body)
        self.body_lay.setSpacing(8)
        self.scroll.setWidget(self.body)
        lay.addWidget(self.scroll, 1)

        row = QHBoxLayout()
        row.addStretch()
        mark = QPushButton("Tout marquer lu")
        mark.setObjectName("secondaryBtn")
        mark.clicked.connect(self._mark_all)
        close = QPushButton("Fermer")
        close.setObjectName("primaryBtn")
        close.clicked.connect(self.accept)
        row.addWidget(mark)
        row.addWidget(close)
        lay.addLayout(row)
        self.refresh()

    def refresh(self) -> None:
        while self.body_lay.count():
            item = self.body_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        session = get_session()
        try:
            uid = current_session.user.id if current_session.user else None
            items = notification_service.list_notifications(session, user_id=uid, limit=50)
            if not items:
                empty = QLabel("Aucune notification.")
                empty.setStyleSheet(f"color:{T.TEXT_SECONDARY};")
                self.body_lay.addWidget(empty)
            for n in items:
                card = self._create_notification_card(n)
                self.body_lay.addWidget(card)
            self.body_lay.addStretch()
        finally:
            session.close()

    def _create_notification_card(self, n) -> QFrame:
        """Create a notification card with icon, title, message, and actions."""
        card = QFrame()
        card.setStyleSheet(
            f"""
            QFrame {{
                background:{T.BG_CARD};
                border:1px solid {T.BORDER};
                border-radius:10px;
                padding:10px;
            }}
            """
        )
        
        layout = QHBoxLayout(card)
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(fa_icon(ICONS.get(n.icon, "bell"), color=T.PRIMARY_ALT).pixmap(24, 24))
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Content
        content = QVBoxLayout()
        content.setSpacing(4)
        
        title = QLabel(n.title or "Notification")
        title.setStyleSheet(f"color:{T.TEXT_PRIMARY}; font-weight:{'700' if not n.lu else '500'}; font-size:14px;")
        content.addWidget(title)
        
        msg = QLabel(n.message)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:12px;")
        content.addWidget(msg)
        
        when = QLabel(n.created_at.strftime("%d/%m/%Y %H:%M"))
        when.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:10px;")
        content.addWidget(when)
        
        layout.addLayout(content, 1)
        
        # Actions
        actions = QVBoxLayout()
        actions.setSpacing(4)
        
        if not n.lu:
            mark_btn = QPushButton()
            mark_btn.setIcon(fa_icon(ICONS["check"], color=T.PRIMARY))
            mark_btn.setFixedSize(24, 24)
            mark_btn.setStyleSheet("QPushButton{border:none;background:transparent;}")
            mark_btn.setToolTip("Marquer comme lu")
            mark_btn.clicked.connect(lambda: self._mark_read(n.id))
            actions.addWidget(mark_btn)
        
        delete_btn = QPushButton()
        delete_btn.setIcon(fa_icon(ICONS["trash"], color="#dc3545"))
        delete_btn.setFixedSize(24, 24)
        delete_btn.setStyleSheet("QPushButton{border:none;background:transparent;}")
        delete_btn.setToolTip("Supprimer")
        delete_btn.clicked.connect(lambda: self._delete(n.id))
        actions.addWidget(delete_btn)
        
        layout.addLayout(actions)
        
        return card

    def _mark_all(self) -> None:
        session = get_session()
        try:
            uid = current_session.user.id if current_session.user else None
            notification_service.mark_all_read(session, uid)
            session.commit()
            self.refresh()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _mark_read(self, notif_id: int) -> None:
        session = get_session()
        try:
            notification_service.mark_read(session, notif_id)
            session.commit()
            self.refresh()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _delete(self, notif_id: int) -> None:
        session = get_session()
        try:
            notification_service.delete_notification(session, notif_id)
            session.commit()
            self.refresh()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _delete_read(self) -> None:
        session = get_session()
        try:
            uid = current_session.user.id if current_session.user else None
            notification_service.delete_all_read(session, uid)
            session.commit()
            self.refresh()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
