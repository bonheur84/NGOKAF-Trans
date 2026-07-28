"""Login view — pixel-perfect vs 1.png."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QMessageBox,
)

from config.settings import settings
from resources import theme as T
from services import auth_service
from database.session import get_session
from services.session_store import current_session
from utils.icons import fa_icon, apply_button_icon, ICONS


class LoginView(QWidget):
    login_success = Signal()


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {T.BG_MAIN};")
        self._build()
        remembered = auth_service.load_remember_username()
        if remembered:
            self.username.setText(remembered)
            self.remember.setChecked(True)

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setFixedWidth(420)
        card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {T.BG_CARD};
                border-radius: {T.RADIUS_CARD}px;
            }}
            """
        )
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 30))
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(32, 24, 32, 24)
        lay.setSpacing(0)

        # Logo
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        path = settings.logo_path
        if path.exists():
            pix = QPixmap(str(path)).scaled(
                90, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            logo.setPixmap(pix)
        lay.addWidget(logo)
        lay.addSpacing(16)

        title = QLabel("Système de Gestion de Billets de Bus")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"font-size:22px; font-weight:700; color:{T.TEXT_PRIMARY};"
        )
        lay.addWidget(title)
        lay.addSpacing(8)

        sub = QLabel("Connectez-vous à votre compte")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"font-size:13px; color:{T.TEXT_SECONDARY};")
        lay.addWidget(sub)
        lay.addSpacing(32)

        # Username
        ul = QLabel("NOM D'UTILISATEUR")
        ul.setStyleSheet(f"font-size:{T.SIZE_LABEL}px; font-weight:600; color:{T.TEXT_LABEL};")
        lay.addWidget(ul)
        lay.addSpacing(8)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Entrez votre nom d'utilisateur")
        self.username.setMinimumHeight(T.FIELD_HEIGHT + 4)
        self.username.setStyleSheet(self._input_style() + "QLineEdit { padding-left: 42px; }")
        self.username.addAction(
            fa_icon(ICONS["user"], color=T.TEXT_SECONDARY),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        lay.addWidget(self.username)
        lay.addSpacing(18)

        # Password
        pl = QLabel("MOT DE PASSE")
        pl.setStyleSheet(f"font-size:{T.SIZE_LABEL}px; font-weight:600; color:{T.TEXT_LABEL};")
        lay.addWidget(pl)
        lay.addSpacing(8)

        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(0)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("••••••••")
        self.password.setMinimumHeight(T.FIELD_HEIGHT + 4)
        self.password.addAction(
            fa_icon(ICONS["lock"], color=T.TEXT_SECONDARY),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        pwd_row.addWidget(self.password)

        self.toggle_pwd = QPushButton()
        self.toggle_pwd.setIcon(fa_icon(ICONS["eye"], color=T.TEXT_SECONDARY))
        self.toggle_pwd.setIconSize(QSize(20, 20))
        self.toggle_pwd.setFixedSize(42, 42)
        self.toggle_pwd.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_pwd.setStyleSheet(
            f"""
            QPushButton {{
                background: {T.BG_INPUT};
                border: 1px solid {T.BORDER};
                border-left: none;
                border-top-right-radius: {T.RADIUS_INPUT}px;
                border-bottom-right-radius: {T.RADIUS_INPUT}px;
            }}
            """
        )
        self.toggle_pwd.clicked.connect(self._toggle_password)
        self.password.setStyleSheet(
            self._input_style()
            + "QLineEdit { border-top-right-radius:0; border-bottom-right-radius:0; padding-left: 42px; }"
        )
        pwd_row.addWidget(self.toggle_pwd)
        lay.addLayout(pwd_row)
        lay.addSpacing(14)

        # Options
        opts = QHBoxLayout()
        self.remember = QCheckBox("Se souvenir de moi")
        self.remember.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:13px;")
        forgot = QPushButton("Mot de passe oublié ?")
        forgot.setObjectName("linkBtn")
        forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        forgot.setStyleSheet(
            f"QPushButton {{ background:transparent; border:none; color:{T.PRIMARY_ALT}; font-size:13px; }}"
        )
        forgot.clicked.connect(self._forgot)
        opts.addWidget(self.remember)
        opts.addStretch()
        opts.addWidget(forgot)
        lay.addLayout(opts)
        lay.addSpacing(24)

        self.error = QLabel("")
        self.error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error.setStyleSheet("color:#D21F1F; font-size:14px;")
        self.error.setWordWrap(True)
        lay.addWidget(self.error)
        lay.addSpacing(8)

        self.btn = QPushButton("Connexion")
        self.btn.setObjectName("primaryBtn")
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setMinimumHeight(T.BUTTON_HEIGHT + 6)
        apply_button_icon(self.btn, ICONS["login"], color="#FFFFFF", size=20)
        self.btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {T.PRIMARY};
                color: white;
                border: none;
                border-radius: {T.RADIUS_BUTTON}px;
                font-size: 15px;
                font-weight: 600;
                padding-left: 16px;
            }}
            QPushButton:hover {{ background-color: {T.HOVER}; }}
            """
        )
        self.btn.clicked.connect(self._login)
        self.password.returnPressed.connect(self._login)
        self.username.returnPressed.connect(self._login)
        lay.addWidget(self.btn)

        outer.addWidget(card)

    def _input_style(self) -> str:
        return f"""
        QLineEdit {{
            background-color: {T.BG_INPUT};
            border: 1px solid {T.BORDER};
            border-radius: {T.RADIUS_INPUT}px;
            padding: 10px 14px;
            font-size: {T.SIZE_INPUT}px;
            color: {T.TEXT_INPUT};
        }}
        """

    def _toggle_password(self) -> None:
        if self.password.echoMode() == QLineEdit.EchoMode.Password:
            self.password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_pwd.setIcon(fa_icon(ICONS["eye_slash"], color=T.TEXT_SECONDARY))
        else:
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_pwd.setIcon(fa_icon(ICONS["eye"], color=T.TEXT_SECONDARY))

    def _forgot(self) -> None:
        QMessageBox.information(
            self,
            "Mot de passe oublié",
            "Contactez l'administrateur.",
        )

    def _login(self) -> None:
        self.error.setText("")
        user = self.username.text().strip()
        pwd = self.password.text()
        if not user or not pwd:
            self.error.setText("Veuillez saisir le nom d'utilisateur et le mot de passe.")
            return
        session = get_session()
        try:
            account = auth_service.authenticate(session, user, pwd)
            if not account:
                self.error.setText("Identifiants incorrects.")
                return
            current_session.user = account
            if self.remember.isChecked():
                auth_service.save_remember_username(user)
            else:
                auth_service.clear_remember_username()
            # Defer to next event loop cycle so this method finishes cleanly
            # before the window transition (login close + new window open)
            QTimer.singleShot(0, self.login_success.emit)
        finally:
            session.close()
