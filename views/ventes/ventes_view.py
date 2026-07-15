"""Ventes module — three columns matching 9.png."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QDateEdit,
    QMessageBox,
    QDoubleSpinBox,
)

from database.session import get_session
from resources import theme as T
from services.bus_service import list_active_routes
from services.sale_service import occupied_seats, sell_ticket, search_tickets
from services.session_store import current_session
from services.print_service import print_ticket
from utils.formatters import format_fc
from utils.icons import fa_icon, apply_button_icon, ICONS
from views.widgets.card import Card
from views.widgets.seat_map import SeatMapWidget


def _title_row(icon_name: str, text: str) -> QWidget:
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(10)
    icon = QLabel()
    icon.setPixmap(fa_icon(icon_name, color=T.PRIMARY_ALT).pixmap(QSize(18, 18)))
    title = QLabel(text)
    title.setStyleSheet(
        f"color:{T.PRIMARY_ALT}; font-size:{T.SIZE_CARD_TITLE}px; font-weight:700;"
    )
    lay.addWidget(icon)
    lay.addWidget(title)
    lay.addStretch()
    return w


class VentesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.routes = []
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(T.GAP_COMPONENT)

        # --- Passenger card ---
        left = Card()
        left.layout.addWidget(_title_row(ICONS["user_plus"], "Détails du Passager"))

        for label, attr, placeholder in [
            ("NOM du passager", "name", "Ex: Jean Dupont"),
            ("TÉLÉPHONE", "phone", "+237 ..."),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"color:{T.TEXT_LABEL}; font-size:{T.SIZE_LABEL}px; font-weight:600;"
            )
            left.layout.addWidget(lbl)
            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            edit.setMinimumHeight(T.FIELD_HEIGHT)
            edit.textChanged.connect(self._update_totals)
            setattr(self, attr, edit)
            left.layout.addWidget(edit)

        lbl = QLabel("TRAJET & HORAIRE")
        lbl.setStyleSheet(
            f"color:{T.TEXT_LABEL}; font-size:{T.SIZE_LABEL}px; font-weight:600;"
        )
        left.layout.addWidget(lbl)
        self.route_combo = QComboBox()
        self.route_combo.setMinimumHeight(T.FIELD_HEIGHT)
        self.route_combo.currentIndexChanged.connect(self._on_route_changed)
        left.layout.addWidget(self.route_combo)

        lbl = QLabel("DATE DE VOYAGE")
        lbl.setStyleSheet(
            f"color:{T.TEXT_LABEL}; font-size:{T.SIZE_LABEL}px; font-weight:600;"
        )
        left.layout.addWidget(lbl)
        self.travel_date = QDateEdit()
        self.travel_date.setCalendarPopup(True)
        self.travel_date.setDate(QDate.currentDate())
        self.travel_date.setDisplayFormat("dd/MM/yyyy")
        self.travel_date.setMinimumHeight(T.FIELD_HEIGHT)
        self.travel_date.dateChanged.connect(self._on_route_changed)
        left.layout.addWidget(self.travel_date)

        lbl = QLabel("PRIX DU TRAJET (FC)")
        lbl.setStyleSheet(
            f"color:{T.TEXT_LABEL}; font-size:{T.SIZE_LABEL}px; font-weight:600;"
        )
        left.layout.addWidget(lbl)
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 10_000_000)
        self.price.setDecimals(0)
        self.price.setSingleStep(500)
        self.price.setSuffix("  FC")
        self.price.setMinimumHeight(T.FIELD_HEIGHT)
        self.price.setReadOnly(True)
        self.price.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.price.setToolTip("Prix défini sur le trajet sélectionné")
        self.price.valueChanged.connect(self._update_totals)
        left.layout.addWidget(self.price)

        # Price summary
        summary = QWidget()
        summary.setStyleSheet(
            f"background:{T.BG_INPUT}; border-radius:12px; padding:8px;"
        )
        sl = QVBoxLayout(summary)
        row = QHBoxLayout()
        self.ticket_price_lbl = QLabel("Ticket")
        self.ticket_price_val = QLabel("0 FC")
        self.ticket_price_val.setStyleSheet("font-weight:600;")
        row.addWidget(self.ticket_price_lbl)
        row.addStretch()
        row.addWidget(self.ticket_price_val)
        sl.addLayout(row)
        total_lbl = QLabel("TOTAL À PAYER")
        total_lbl.setStyleSheet("font-weight:700; font-size:14px;")
        sl.addWidget(total_lbl)
        self.total_amount = QLabel("0 FC")
        self.total_amount.setStyleSheet(
            f"color:{T.PRIMARY_ALT}; font-size:28px; font-weight:800;"
        )
        sl.addWidget(self.total_amount)
        left.layout.addWidget(summary)

        self.btn_save = QPushButton("Enregistrer & Imprimer")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.setMinimumHeight(T.BUTTON_HEIGHT)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_button_icon(self.btn_save, ICONS["print"], color="#FFFFFF", size=18)
        self.btn_save.setStyleSheet(
            f"""
            QPushButton {{
                background:{T.PRIMARY}; color:white; border:none;
                border-radius:{T.RADIUS_BUTTON}px; font-size:15px; font-weight:600;
            }}
            QPushButton:hover {{ background:{T.HOVER}; }}
            """
        )
        self.btn_save.clicked.connect(self._save)
        left.layout.addWidget(self.btn_save)

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setMinimumHeight(T.BUTTON_HEIGHT)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet(
            f"""
            QPushButton {{
                background:{T.BG_CARD}; color:{T.TEXT_PRIMARY};
                border:1px solid {T.BORDER}; border-radius:{T.RADIUS_BUTTON}px;
                font-size:15px; font-weight:600;
            }}
            """
        )
        self.btn_cancel.clicked.connect(self._reset)
        left.layout.addWidget(self.btn_cancel)
        left.layout.addStretch()

        # --- Seats ---
        center = Card()
        center.layout.addWidget(_title_row(ICONS["seat"], "Sélection du Siège"))
        self.seat_map = SeatMapWidget(60)
        self.seat_map.seat_selected.connect(lambda _: self._update_totals())
        center.layout.addWidget(self.seat_map, 1)

        root.addWidget(left, 2)
        root.addWidget(center, 3)

    def refresh(self) -> None:
        session = get_session()
        try:
            self.routes = list_active_routes(session)
            self.route_combo.blockSignals(True)
            self.route_combo.clear()
            if not self.routes:
                self.route_combo.addItem("Aucun trajet disponible", None)
            else:
                for r in self.routes:
                    self.route_combo.addItem(r.label, r.id)
            self.route_combo.blockSignals(False)
            self._on_route_changed()
        finally:
            session.close()

    def apply_search(self, text: str) -> None:
        return

    def _current_route(self):
        rid = self.route_combo.currentData()
        if rid is None:
            return None
        for r in self.routes:
            if r.id == rid:
                return r
        return None

    def _on_route_changed(self) -> None:
        route = self._current_route()
        self.price.blockSignals(True)
        if route and route.prix_indicatif is not None:
            self.price.setValue(float(route.prix_indicatif))
        else:
            self.price.setValue(0)
        self.price.blockSignals(False)
        session = get_session()
        try:
            if route:
                qd = self.travel_date.date()
                travel = date(qd.year(), qd.month(), qd.day())
                occupied = occupied_seats(session, route.bus_id, route.id, travel)
                self.seat_map.set_occupied(occupied)
            else:
                self.seat_map.set_occupied(set())
        finally:
            session.close()
        self._update_totals()

    def _update_totals(self) -> None:
        price = Decimal(int(self.price.value()))
        self.ticket_price_val.setText(format_fc(price))
        self.total_amount.setText(format_fc(price))

    def _reset(self) -> None:
        self.name.clear()
        self.phone.clear()
        self.price.setValue(0)
        self.seat_map.clear_selection()
        self.travel_date.setDate(QDate.currentDate())
        self._on_route_changed()

    def _save(self) -> None:
        route = self._current_route()
        if not route:
            QMessageBox.warning(self, "Vente", "Aucun trajet disponible.")
            return
        if not self.name.text().strip() or not self.phone.text().strip():
            QMessageBox.warning(self, "Vente", "Renseignez le nom et le téléphone.")
            return
        if not self.seat_map.selected:
            QMessageBox.warning(self, "Vente", "Sélectionnez un siège.")
            return
        if self.price.value() <= 0:
            QMessageBox.warning(self, "Vente", "Saisissez le prix du billet.")
            return
        user = current_session.user
        if not user:
            QMessageBox.critical(self, "Vente", "Session expirée.")
            return
        qd = self.travel_date.date()
        travel = date(qd.year(), qd.month(), qd.day())
        session = get_session()
        try:
            ticket = sell_ticket(
                session,
                passenger_name=self.name.text(),
                phone=self.phone.text(),
                route_id=route.id,
                seat_number=self.seat_map.selected,
                price=Decimal(int(self.price.value())),
                travel_date=travel,
                cashier=user,
            )
            # reload with relations
            from sqlalchemy.orm import joinedload
            from models.ticket import Ticket

            ticket = (
                session.query(Ticket)
                .options(
                    joinedload(Ticket.route),
                    joinedload(Ticket.bus),
                    joinedload(Ticket.cashier),
                )
                .filter_by(id=ticket.id)
                .one()
            )
            path = print_ticket(ticket, user.id, preview_only=False)
            QMessageBox.information(
                self,
                "Billet enregistré",
                f"Billet {ticket.numero} enregistré.\nImpression : {path}",
            )
            self._reset()
            self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()
