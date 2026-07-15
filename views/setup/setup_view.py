"""First-run setup: create first cashier + optional bus/route."""
from __future__ import annotations

from datetime import time
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QFormLayout,
    QCheckBox,
    QTimeEdit,
    QScrollArea,
    QMessageBox,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import QTime

from config.settings import settings
from resources import theme as T
from database.session import get_session
from services import auth_service
from services.bus_service import create_bus_with_seats, create_route
from services.session_store import current_session


class SetupView(QWidget):
    setup_complete = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {T.BG_MAIN};")
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        container = QWidget()
        scroll_lay = QVBoxLayout(container)
        scroll_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setFixedWidth(480)
        card.setStyleSheet(
            f"QFrame{{background:{T.BG_CARD}; border-radius:{T.RADIUS_CARD}px;}}"
        )
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 30))
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(12)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if settings.logo_path.exists():
            logo.setPixmap(
                QPixmap(str(settings.logo_path)).scaled(
                    100, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            )
        lay.addWidget(logo)

        title = QLabel("Première configuration")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size:22px; font-weight:700; color:{T.TEXT_PRIMARY};")
        lay.addWidget(title)

        sub = QLabel("Créez le compte du premier caissier pour démarrer.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"font-size:15px; color:{T.TEXT_SECONDARY};")
        lay.addWidget(sub)

        form = QFormLayout()
        form.setSpacing(10)
        self.nom = QLineEdit()
        self.prenom = QLineEdit()
        self.telephone = QLineEdit()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password2 = QLineEdit()
        self.password2.setEchoMode(QLineEdit.EchoMode.Password)
        for w in (
            self.nom,
            self.prenom,
            self.telephone,
            self.username,
            self.password,
            self.password2,
        ):
            w.setMinimumHeight(T.FIELD_HEIGHT)
            w.setStyleSheet(
                f"background:{T.BG_INPUT}; border:1px solid {T.BORDER};"
                f"border-radius:{T.RADIUS_INPUT}px; padding:8px 12px; font-size:14px;"
            )
        form.addRow("Nom", self.nom)
        form.addRow("Prénom", self.prenom)
        form.addRow("Téléphone", self.telephone)
        form.addRow("Nom d'utilisateur", self.username)
        form.addRow("Mot de passe", self.password)
        form.addRow("Confirmer", self.password2)
        lay.addLayout(form)

        self.add_bus = QCheckBox("Créer aussi un bus et un trajet initial")
        self.add_bus.setChecked(True)
        self.add_bus.setStyleSheet(f"color:{T.TEXT_PRIMARY}; font-size:15px; font-weight:600;")
        lay.addWidget(self.add_bus)

        self.bus_box = QFrame()
        bb = QFormLayout(self.bus_box)
        self.bus_code = QLineEdit()
        self.bus_code.setPlaceholderText("Ex: NGK-201")
        self.ville_dep = QLineEdit()
        self.ville_dep.setPlaceholderText("Ex: Douala")
        self.ville_arr = QLineEdit()
        self.ville_arr.setPlaceholderText("Ex: Yaoundé")
        self.heure = QTimeEdit()
        self.heure.setDisplayFormat("HH:mm")
        self.heure.setTime(QTime(7, 0))
        self.prix = QLineEdit()
        self.prix.setPlaceholderText("Prix indicatif (optionnel)")
        for w in (self.bus_code, self.ville_dep, self.ville_arr, self.prix, self.heure):
            w.setMinimumHeight(T.FIELD_HEIGHT)
            w.setStyleSheet(
                f"background:{T.BG_INPUT}; border:1px solid {T.BORDER};"
                f"border-radius:{T.RADIUS_INPUT}px; padding:8px 12px; font-size:16px;"
            )
        bb.addRow("Code bus", self.bus_code)
        bb.addRow("Ville départ", self.ville_dep)
        bb.addRow("Ville arrivée", self.ville_arr)
        bb.addRow("Heure départ", self.heure)
        bb.addRow("Prix indicatif", self.prix)
        lay.addWidget(self.bus_box)
        self.add_bus.toggled.connect(self.bus_box.setVisible)

        self.error = QLabel("")
        self.error.setStyleSheet("color:#D21F1F; font-size:14px;")
        self.error.setWordWrap(True)
        lay.addWidget(self.error)

        btn = QPushButton("Créer et démarrer")
        btn.setMinimumHeight(T.BUTTON_HEIGHT)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background:{T.PRIMARY}; color:white; border:none;
                border-radius:{T.RADIUS_BUTTON}px; font-size:15px; font-weight:600;
            }}
            QPushButton:hover {{ background:{T.HOVER}; }}
            """
        )
        btn.clicked.connect(self._submit)
        lay.addWidget(btn)

        scroll_lay.addWidget(card)
        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _submit(self) -> None:
        self.error.setText("")
        if not all(
            [
                self.nom.text().strip(),
                self.prenom.text().strip(),
                self.username.text().strip(),
                self.password.text(),
            ]
        ):
            self.error.setText("Remplissez nom, prénom, identifiant et mot de passe.")
            return
        if self.password.text() != self.password2.text():
            self.error.setText("Les mots de passe ne correspondent pas.")
            return
        if len(self.password.text()) < 4:
            self.error.setText("Le mot de passe doit contenir au moins 4 caractères.")
            return

        if self.add_bus.isChecked():
            if not all(
                [
                    self.bus_code.text().strip(),
                    self.ville_dep.text().strip(),
                    self.ville_arr.text().strip(),
                ]
            ):
                self.error.setText("Renseignez le code bus et les villes du trajet.")
                return

        session = get_session()
        try:
            if auth_service.count_users(session) > 0:
                self.error.setText("Un utilisateur existe déjà.")
                return
            user = auth_service.create_cashier(
                session,
                nom=self.nom.text(),
                prenom=self.prenom.text(),
                telephone=self.telephone.text(),
                username=self.username.text(),
                password=self.password.text(),
            )
            if self.add_bus.isChecked():
                bus = create_bus_with_seats(
                    session, self.bus_code.text(), capacite=60, user_id=user.id
                )
                prix = None
                if self.prix.text().strip():
                    try:
                        prix = Decimal(self.prix.text().replace(" ", "").replace(",", "."))
                    except InvalidOperation:
                        self.error.setText("Prix indicatif invalide.")
                        session.rollback()
                        return
                qt = self.heure.time()
                create_route(
                    session,
                    self.ville_dep.text(),
                    self.ville_arr.text(),
                    time(qt.hour(), qt.minute()),
                    bus.id,
                    prix,
                    user.id,
                )
            session.commit()
            current_session.user = user
            QMessageBox.information(self, "Succès", "Premier caissier créé avec succès.")
            self.setup_complete.emit()
        except Exception as e:
            session.rollback()
            self.error.setText(str(e))
        finally:
            session.close()
