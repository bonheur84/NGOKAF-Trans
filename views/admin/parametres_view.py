"""Admin Paramètres — agence, sauvegarde, MDP."""
from __future__ import annotations



from PySide6.QtCore import Qt
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,

    QMessageBox,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QSpacerItem,
)

from config.settings import settings
from database.session import get_session
from resources import theme as T
from services import settings_service, user_admin_service, notification_service
from services.session_store import current_session
from utils.icons import fa_icon
from views.widgets.card import Card


def _section_title(fa_name: str, text: str) -> QWidget:
    container = QWidget()
    h = QHBoxLayout(container)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(8)
    icon_lbl = QLabel()
    icon_lbl.setPixmap(fa_icon(fa_name, color=T.PRIMARY_ALT).pixmap(QSize(15, 15)))
    h.addWidget(icon_lbl)
    txt = QLabel(text)
    txt.setStyleSheet(
        f"color:{T.PRIMARY_ALT}; font-size:13px; font-weight:700;"
    )
    h.addWidget(txt)
    h.addStretch()
    # Underline separator below
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet(f"color:{T.PRIMARY}33; margin-top:2px;")
    wrap = QWidget()
    v = QVBoxLayout(wrap)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(4)
    v.addWidget(container)
    v.addWidget(sep)
    return wrap


def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:11px; font-weight:600;")
    lbl.setFixedWidth(160)
    return lbl


def _row(label: str, widget: QWidget) -> QHBoxLayout:
    h = QHBoxLayout()
    h.setSpacing(12)
    h.addWidget(_field_label(label))
    h.addWidget(widget, 1)
    return h


def _input(placeholder: str = "", readonly: bool = False) -> QLineEdit:
    w = QLineEdit()
    w.setPlaceholderText(placeholder)
    if readonly:
        w.setReadOnly(True)
    return w


def _pwd_input(placeholder: str = "") -> QLineEdit:
    w = QLineEdit()
    w.setPlaceholderText(placeholder)
    w.setEchoMode(QLineEdit.EchoMode.Password)
    return w


def _separator() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color:{T.BORDER}; margin:4px 0;")
    return f


class ParametresView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;")

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(24, 20, 24, 24)
        lay.setSpacing(18)

        # ── Page header ──────────────────────────────────────────────
        header = QLabel("Paramètres")
        header.setStyleSheet(
            f"color:{T.PRIMARY_ALT}; font-size:22px; font-weight:700; margin-bottom:4px;"
        )
        lay.addWidget(header)

        sub = QLabel("Configurez le profil de votre agence, la sécurité et les sauvegardes.")
        sub.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:12px;")
        lay.addWidget(sub)

        lay.addWidget(_separator())

        # ── 1. Profil agence ─────────────────────────────────────────
        agency_card = Card(padding=18)
        agency_card.layout.setSpacing(12)
        agency_card.layout.addWidget(_section_title("building", "Profil agence"))

        self.agency_name    = _input("Ex: NGOKAF TRANS")
        self.agency_address = _input("Ex: Douala, Cameroun")
        self.agency_phone   = _input("Ex: +237 6XX XXX XXX")
        self.terminal_name  = _input("Ex: TERMINAL PRINCIPAL")
        self.currency       = _input(readonly=True)
        self.prefix         = _input("Ex: TK-")

        for label, widget in [
            ("Nom de l'agence",  self.agency_name),
            ("Adresse",          self.agency_address),
            ("Téléphone",        self.agency_phone),
            ("Terminal",         self.terminal_name),
            ("Devise",           self.currency),
            ("Préfixe tickets",  self.prefix),
        ]:
            agency_card.layout.addLayout(_row(label, widget))

        lay.addWidget(agency_card)

        # ── 2. Mot de passe administrateur ──────────────────────────
        pwd_card = Card(padding=18)
        pwd_card.layout.setSpacing(12)
        pwd_card.layout.addWidget(_section_title("lock", "Sécurité"))

        self.old_pwd  = _pwd_input("Mot de passe actuel")
        self.new_pwd  = _pwd_input("Nouveau mot de passe")
        self.new_pwd2 = _pwd_input("Confirmer le mot de passe")

        for label, widget in [
            ("Mot de passe actuel",   self.old_pwd),
            ("Nouveau mot de passe",  self.new_pwd),
            ("Confirmer",             self.new_pwd2),
        ]:
            pwd_card.layout.addLayout(_row(label, widget))

        change_pwd_btn = QPushButton("Changer le mot de passe")
        change_pwd_btn.setObjectName("secondaryBtn")
        change_pwd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        change_pwd_btn.clicked.connect(self._change_pwd)
        pwd_card.layout.addWidget(change_pwd_btn, alignment=Qt.AlignmentFlag.AlignRight)

        lay.addWidget(pwd_card)



        # ── Save button ──────────────────────────────────────────────
        lay.addItem(QSpacerItem(0, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        save_btn = QPushButton("  Enregistrer les paramètres")
        save_btn.setObjectName("primaryBtn")
        save_btn.setFixedHeight(42)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        lay.addWidget(save_btn)

        lay.addStretch()

        scroll.setWidget(body)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        session = get_session()
        try:
            g = settings_service.get_setting
            self.agency_name.setText(g(session, "agency_name", settings.AGENCY_NAME))
            self.agency_address.setText(g(session, "agency_address", settings.AGENCY_ADDRESS))
            self.agency_phone.setText(g(session, "agency_phone", settings.AGENCY_PHONE))
            self.terminal_name.setText(g(session, "terminal_name", settings.TERMINAL_NAME))
            self.currency.setText(g(session, "currency", "FC"))
            self.prefix.setText(g(session, "ticket_prefix", "TK-"))
        finally:
            session.close()

    def _actor(self):
        return current_session.user.id if current_session.user else None

    def _save(self) -> None:
        session = get_session()
        try:
            pairs = {
                "agency_name":    self.agency_name.text().strip(),
                "agency_address": self.agency_address.text().strip(),
                "agency_phone":   self.agency_phone.text().strip(),
                "terminal_name":  self.terminal_name.text().strip(),
                "currency":       "FC",
                "ticket_prefix":  self.prefix.text().strip() or "TK-",
            }
            for k, v in pairs.items():
                settings_service.set_setting(session, k, v)
            notification_service.notify(
                session,
                "Paramètres mis à jour",
                "Les paramètres ont été enregistrés avec succès.",
                self._actor(),
            )
            session.commit()
            QMessageBox.information(self, "Paramètres", "Enregistré avec succès ✓")
            self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _change_pwd(self) -> None:
        if self.new_pwd.text() != self.new_pwd2.text():
            QMessageBox.warning(self, "Mot de passe", "Les mots de passe ne correspondent pas.")
            return
        if len(self.new_pwd.text()) < 6:
            QMessageBox.warning(self, "Mot de passe", "Le mot de passe doit contenir au moins 6 caractères.")
            return
        user = current_session.user
        if not user:
            return
        session = get_session()
        try:
            admin = user_admin_service.get_user(session, user.id)
            user_admin_service.change_admin_password(
                session, admin, self.old_pwd.text(), self.new_pwd.text()
            )
            session.commit()
            self.old_pwd.clear()
            self.new_pwd.clear()
            self.new_pwd2.clear()
            QMessageBox.information(self, "Mot de passe", "Mot de passe modifié avec succès ✓")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

