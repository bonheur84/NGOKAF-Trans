"""Cashier desktop window backed exclusively by the central HTTPS API."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QSpinBox, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget,
)

from resources import theme as T
from reports.luggage_58mm import print_luggage_label
from reports.ticket_80mm import print_ticket_windows
from services.api_client import ApiError, current_api_client
from services.session_store import current_session


class RemoteCashierWindow(QMainWindow):
    """Minimal operational desk for installations that never access MySQL."""

    logout_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NGOKAF TRANS — Caisse connectée")
        self.resize(1050, 700)
        self._routes: list[dict] = []
        self._build()
        self.refresh_routes()

    def _build(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 22, 28, 22)

        header = QHBoxLayout()
        user = current_session.user
        header.addWidget(QLabel(f"<h2>NGOKAF TRANS — Caisse en ligne</h2>"))
        header.addStretch()
        header.addWidget(QLabel(user.full_name if user else ""))
        logout = QPushButton("Déconnexion")
        logout.clicked.connect(self.logout_requested.emit)
        header.addWidget(logout)
        layout.addLayout(header)

        self.status = QLabel("Connexion au serveur central…")
        self.status.setStyleSheet(f"color:{T.TEXT_SECONDARY};")
        layout.addWidget(self.status)

        tabs = QTabWidget()
        tabs.addTab(self._ticket_tab(), "Ventes")
        tabs.addTab(self._luggage_tab(), "Bagages")
        layout.addWidget(tabs)

    def _ticket_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.ticket_route = QComboBox()
        self.ticket_route.currentIndexChanged.connect(self._route_changed)
        self.ticket_date = QDateEdit(QDate.currentDate())
        self.ticket_date.setCalendarPopup(True)
        self.ticket_name = QLineEdit()
        self.ticket_phone = QLineEdit()
        self.ticket_seat = QSpinBox(); self.ticket_seat.setMinimum(1)
        self.ticket_price = QDoubleSpinBox(); self.ticket_price.setMaximum(99_999_999); self.ticket_price.setDecimals(0)
        self.ticket_occupied = QLabel("—")
        refresh = QPushButton("Actualiser les sièges")
        refresh.clicked.connect(self.refresh_occupied)
        save = QPushButton("Enregistrer et imprimer le billet")
        save.setStyleSheet(f"background:{T.PRIMARY}; color:white; padding:10px; font-weight:600;")
        save.clicked.connect(self.create_ticket)
        form.addRow("Trajet", self.ticket_route)
        form.addRow("Date de voyage", self.ticket_date)
        form.addRow("Passager", self.ticket_name)
        form.addRow("Téléphone", self.ticket_phone)
        form.addRow("Siège", self.ticket_seat)
        form.addRow("Prix (FC)", self.ticket_price)
        form.addRow("Sièges occupés", self.ticket_occupied)
        form.addRow("", refresh)
        form.addRow("", save)
        return page

    def _luggage_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.luggage_code = QLineEdit(); self.luggage_code.setPlaceholderText("Code NG imprimé sur le billet")
        self.luggage_route = QComboBox()
        self.luggage_sender = QLineEdit()
        self.luggage_sender_phone = QLineEdit()
        self.luggage_recipient = QLineEdit()
        self.luggage_recipient_phone = QLineEdit()
        self.luggage_description = QTextEdit(); self.luggage_description.setFixedHeight(70)
        self.luggage_weight = QDoubleSpinBox(); self.luggage_weight.setMaximum(9999); self.luggage_weight.setDecimals(1)
        self.luggage_fragile = QComboBox(); self.luggage_fragile.addItem("Non", False); self.luggage_fragile.addItem("Oui", True)
        save = QPushButton("Enregistrer et imprimer l'étiquette")
        save.setStyleSheet(f"background:{T.PRIMARY}; color:white; padding:10px; font-weight:600;")
        save.clicked.connect(self.create_luggage)
        form.addRow("Code billet", self.luggage_code)
        form.addRow("Trajet", self.luggage_route)
        form.addRow("Expéditeur", self.luggage_sender)
        form.addRow("Tél. expéditeur", self.luggage_sender_phone)
        form.addRow("Destinataire", self.luggage_recipient)
        form.addRow("Tél. destinataire", self.luggage_recipient_phone)
        form.addRow("Description", self.luggage_description)
        form.addRow("Poids (kg)", self.luggage_weight)
        form.addRow("Fragile", self.luggage_fragile)
        form.addRow("", save)
        return page

    def refresh_routes(self) -> None:
        try:
            self._routes = current_api_client().routes()
            for combo in (self.ticket_route, self.luggage_route):
                combo.blockSignals(True)
                combo.clear()
                for route in self._routes:
                    bus = route["bus"]
                    combo.addItem(
                        f"{route['departure']} → {route['arrival']} — {bus['code']} ({route['departure_time']})",
                        route["id"],
                    )
                combo.blockSignals(False)
            self._route_changed()
            self.status.setText("Connecté au serveur central. Les données restent sur le serveur.")
        except ApiError as exc:
            self.status.setText(str(exc))
            QMessageBox.critical(self, "Serveur central", str(exc))

    def _selected_route(self, combo: QComboBox) -> dict | None:
        route_id = combo.currentData()
        return next((route for route in self._routes if route["id"] == route_id), None)

    def _travel_date(self) -> str:
        qdate = self.ticket_date.date()
        return date(qdate.year(), qdate.month(), qdate.day()).isoformat()

    def _route_changed(self) -> None:
        route = self._selected_route(self.ticket_route)
        if route:
            self.ticket_seat.setMaximum(route["bus"]["capacity"])
            self.ticket_price.setValue(float(route["price"] or 0))
            self.refresh_occupied()

    def refresh_occupied(self) -> None:
        route = self._selected_route(self.ticket_route)
        if not route:
            return
        try:
            seats = current_api_client().occupied_seats(route["id"], self._travel_date())
            self.ticket_occupied.setText(", ".join(map(str, sorted(seats))) if seats else "Aucun")
        except ApiError as exc:
            self.status.setText(str(exc))

    def create_ticket(self) -> None:
        route = self._selected_route(self.ticket_route)
        if not route or not self.ticket_name.text().strip() or not self.ticket_phone.text().strip() or self.ticket_price.value() <= 0:
            QMessageBox.warning(self, "Vente", "Renseignez le trajet, le passager, le téléphone et le prix.")
            return
        try:
            payload = {
                "passenger_name": self.ticket_name.text().strip(), "phone": self.ticket_phone.text().strip(),
                "route_id": route["id"], "seat_number": self.ticket_seat.value(),
                "price": str(int(self.ticket_price.value())), "travel_date": self._travel_date(),
            }
            data = current_api_client().create_ticket(payload)
            ticket = self._ticket_object(data, route)
            print_ticket_windows(ticket)
            QMessageBox.information(self, "Vente", f"Billet {ticket.numero} enregistré et envoyé à l'impression.")
            self.ticket_name.clear(); self.ticket_phone.clear(); self.refresh_occupied()
        except ApiError as exc:
            QMessageBox.warning(self, "Vente", str(exc))
        except Exception as exc:
            QMessageBox.warning(self, "Impression", f"Billet enregistré, mais impression impossible : {exc}")

    def _ticket_object(self, data: dict, route: dict):
        user = current_session.user
        record = dict(data)
        record["price"] = Decimal(data["price"])
        record["travel_date"] = date.fromisoformat(data["travel_date"])
        record["created_at"] = datetime.fromisoformat(data["created_at"])
        record["agency_id"] = getattr(user, "agency_id", None)
        record["route"] = SimpleNamespace(ville_depart=route["departure"], ville_arrivee=route["arrival"])
        record["bus"] = SimpleNamespace(code=route["bus"]["code"], plaque=None)
        record["cashier"] = user
        return SimpleNamespace(
            **record,
        )

    def create_luggage(self) -> None:
        route = self._selected_route(self.luggage_route)
        required = [self.luggage_code.text().strip(), self.luggage_sender.text().strip(), self.luggage_sender_phone.text().strip(), self.luggage_recipient.text().strip(), self.luggage_recipient_phone.text().strip(), self.luggage_description.toPlainText().strip()]
        if not route or not all(required) or self.luggage_weight.value() <= 0:
            QMessageBox.warning(self, "Bagages", "Renseignez tous les champs et sélectionnez un trajet.")
            return
        try:
            data = current_api_client().create_luggage({
                "luggage_code": self.luggage_code.text().strip(), "route_id": route["id"],
                "sender_name": self.luggage_sender.text().strip(), "sender_phone": self.luggage_sender_phone.text().strip(),
                "recipient_name": self.luggage_recipient.text().strip(), "recipient_phone": self.luggage_recipient_phone.text().strip(),
                "description": self.luggage_description.toPlainText().strip(), "poids": str(self.luggage_weight.value()),
                "fragile": bool(self.luggage_fragile.currentData()),
            })
            record = dict(data)
            record["poids"] = Decimal(data["poids"])
            record["total"] = Decimal(data["total"])
            record["created_at"] = datetime.fromisoformat(data["created_at"])
            record["route"] = SimpleNamespace(ville_depart=route["departure"], ville_arrivee=route["arrival"])
            record["bus"] = SimpleNamespace(code=route["bus"]["code"])
            item = SimpleNamespace(**record)
            print_luggage_label(item)
            QMessageBox.information(self, "Bagages", f"Bagage {item.numero} enregistré et envoyé à l'impression.")
            for field in (self.luggage_code, self.luggage_sender, self.luggage_sender_phone, self.luggage_recipient, self.luggage_recipient_phone): field.clear()
            self.luggage_description.clear(); self.luggage_weight.setValue(0)
        except ApiError as exc:
            QMessageBox.warning(self, "Bagages", str(exc))
        except Exception as exc:
            QMessageBox.warning(self, "Impression", f"Bagage enregistré, mais impression impossible : {exc}")
