"""Ventes module — three columns matching 9.png."""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

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
    QDialog,
    QDialogButtonBox,
    QProgressBar,
    QFileDialog,
)

from database.session import get_session
from resources import theme as T
from services.bus_service import list_active_routes, reactivate_bus
from services.sale_service import occupied_seats, sell_ticket, search_tickets
from services.session_store import current_session
from services.print_service import print_ticket
from utils.formatters import format_fc
from utils.icons import fa_icon, apply_button_icon, ICONS
from utils.sounds import play_success, play_error, play_warning, play_click, play_print, play_bus_full
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


class BusFullDialog(QDialog):
    """Confirmation dialog shown when the last seat of a bus is sold."""

    def __init__(self, bus_code: str, route_label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Bus Complet !")
        self.setModal(True)
        self.setMinimumWidth(460)
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {T.BG_CARD};
                border-radius: 16px;
            }}
            QLabel {{
                color: {T.TEXT_PRIMARY};
            }}
            """
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(14)

        # Icon + title
        icon_lbl = QLabel()
        icon_lbl.setPixmap(fa_icon(ICONS["bus"], color="#EF5350").pixmap(52, 52))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(icon_lbl)

        title = QLabel("Bus Complet !")
        title.setStyleSheet("font-size:22px; font-weight:800; color:#EF5350;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        info = QLabel(
            f"<b>{bus_code}</b> — <i>{route_label}</i><br>"
            "Tous les sièges sont maintenant occupés.<br><br>"
            "Voulez-vous <b>désactiver ce bus et son trajet</b> pour<br>"
            "signaler qu'il est prêt à partir ?"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setWordWrap(True)
        info.setStyleSheet("font-size:13px; color:#555; line-height:1.5;")
        lay.addWidget(info)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_deactivate = QPushButton(" Oui, désactiver pour le départ")
        self.btn_deactivate.setMinimumHeight(44)
        self.btn_deactivate.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_button_icon(self.btn_deactivate, ICONS["check"], color="#FFFFFF", size=16)
        self.btn_deactivate.setStyleSheet(
            f"""
            QPushButton {{
                background: #EF5350; color: white;
                border: none; border-radius: 10px;
                font-size: 13px; font-weight: 700; padding: 0 16px;
            }}
            QPushButton:hover {{ background: #E53935; }}
            """
        )

        self.btn_keep = QPushButton(" Non, garder actif")
        self.btn_keep.setMinimumHeight(44)
        self.btn_keep.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_button_icon(self.btn_keep, "lock-open", color=T.TEXT_PRIMARY, size=16)
        self.btn_keep.setStyleSheet(
            f"""
            QPushButton {{
                background: {T.BG_INPUT}; color: {T.TEXT_PRIMARY};
                border: 1px solid {T.BORDER}; border-radius: 10px;
                font-size: 13px; font-weight: 600; padding: 0 16px;
            }}
            QPushButton:hover {{ background: {T.BORDER}; }}
            """
        )

        btn_layout.addWidget(self.btn_keep)
        btn_layout.addWidget(self.btn_deactivate)
        lay.addLayout(btn_layout)

        self.btn_deactivate.clicked.connect(self.accept)
        self.btn_keep.clicked.connect(self.reject)


class VentesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.routes = []
        # State for post-sale export
        self._last_full_bus_id: int | None = None
        self._last_full_route_id: int | None = None
        self._last_full_travel_date: date | None = None
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

        # Fill progress bar (updates with each seat selection)
        self._fill_bar_widget = QWidget()
        self._fill_bar_widget.setStyleSheet(
            f"background:{T.BG_INPUT}; border-radius:10px; padding:6px 10px;"
        )
        fbl = QVBoxLayout(self._fill_bar_widget)
        fbl.setContentsMargins(0, 0, 0, 0)
        fbl.setSpacing(4)
        fb_header = QHBoxLayout()
        self._fill_label = QLabel("Remplissage")
        self._fill_label.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:11px;")
        self._fill_pct_label = QLabel("0%")
        self._fill_pct_label.setStyleSheet(f"color:{T.TEXT_PRIMARY}; font-size:11px; font-weight:700;")
        fb_header.addWidget(self._fill_label)
        fb_header.addStretch()
        fb_header.addWidget(self._fill_pct_label)
        self._fill_bar = QProgressBar()
        self._fill_bar.setRange(0, 100)
        self._fill_bar.setValue(0)
        self._fill_bar.setTextVisible(False)
        self._fill_bar.setFixedHeight(6)
        self._fill_bar.setStyleSheet(
            f"""
            QProgressBar {{
                background: {T.BG_CARD};
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: #66BB6A;
                border-radius: 3px;
            }}
            """
        )
        fbl.addLayout(fb_header)
        fbl.addWidget(self._fill_bar)
        left.layout.addWidget(self._fill_bar_widget)

        # Action buttons
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
        self.btn_cancel.clicked.connect(lambda: (play_click(), self._reset()))
        left.layout.addWidget(self.btn_cancel)

        # Reactivate bus button (shown when a route is inactive)
        self.btn_reactivate = QPushButton("  Réactiver ce bus")
        self.btn_reactivate.setMinimumHeight(T.BUTTON_HEIGHT)
        self.btn_reactivate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reactivate.setVisible(False)
        apply_button_icon(self.btn_reactivate, "lock-open", color="#FFFFFF", size=18)
        self.btn_reactivate.setStyleSheet(
            f"""
            QPushButton {{
                background: #388E3C; color: white;
                border: none; border-radius: {T.RADIUS_BUTTON}px;
                font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: #2E7D32; }}
            """
        )
        self.btn_reactivate.clicked.connect(self._reactivate_bus)
        left.layout.addWidget(self.btn_reactivate)

        # Export manifest button (shown below reactivate button for full/inactive bus)
        self.btn_export = QPushButton("  Exporter Liste des Passagers (Excel)")
        self.btn_export.setMinimumHeight(T.BUTTON_HEIGHT)
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setVisible(False)
        apply_button_icon(self.btn_export, ICONS["upload"], color="#FFFFFF", size=18)
        self.btn_export.setStyleSheet(
            f"""
            QPushButton {{
                background: #1E40AF; color: white;
                border: none; border-radius: {T.RADIUS_BUTTON}px;
                font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: #1E3A8A; }}
            """
        )
        self.btn_export.clicked.connect(self._export_manifest)
        left.layout.addWidget(self.btn_export)

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
            # Load ALL routes (active + inactive) so we can show reactivate button
            from models.route import Route
            from services.agency_context import current_agency_id
            from sqlalchemy.orm import joinedload

            aid = current_agency_id()
            q = (
                session.query(Route)
                .options(joinedload(Route.bus))
            )
            if aid:
                q = q.filter(Route.agency_id == aid)
            all_routes = q.order_by(Route.ville_depart, Route.heure_depart).all()
            self.routes = all_routes

            self.route_combo.blockSignals(True)
            self.route_combo.clear()
            if not all_routes:
                self.route_combo.addItem("Aucun trajet disponible", None)
            else:
                for r in all_routes:
                    suffix = " [COMPLET]" if r.statut == "inactif" else ""
                    self.route_combo.addItem(r.label + suffix, r.id)
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

        # Show/hide reactivate & export buttons based on route status
        is_inactive = route is not None and route.statut == "inactif"
        self.btn_reactivate.setVisible(is_inactive)
        has_export = is_inactive or (route is not None and self._last_full_route_id == route.id)
        self.btn_export.setVisible(has_export)
        self.btn_save.setEnabled(not is_inactive)
        self.btn_save.setStyleSheet(
            f"""
            QPushButton {{
                background: {'#9E9E9E' if is_inactive else T.PRIMARY};
                color: white; border: none;
                border-radius: {T.RADIUS_BUTTON}px;
                font-size: 15px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {'#757575' if is_inactive else T.HOVER}; }}
            """
        )

        self._update_totals()

    def _update_totals(self) -> None:
        price = Decimal(int(self.price.value()))
        self.ticket_price_val.setText(format_fc(price))
        self.total_amount.setText(format_fc(price))
        self._update_fill_bar()

    def _update_fill_bar(self) -> None:
        """Recompute and display the current bus fill percentage."""
        route = self._current_route()
        if not route or not route.bus:
            self._fill_bar.setValue(0)
            self._fill_pct_label.setText("0%")
            return

        capacity = route.bus.capacite or 1
        occupied_count = sum(
            1 for btn in self.seat_map.buttons.values() if btn.state == "occupied"
        )
        pct = int(occupied_count / capacity * 100)
        self._fill_bar.setValue(pct)
        self._fill_pct_label.setText(f"{pct}%")

        if pct >= 100:
            colour = "#EF5350"
        elif pct >= 80:
            colour = "#FF9800"
        elif pct >= 50:
            colour = "#FDD835"
        else:
            colour = "#66BB6A"

        self._fill_bar.setStyleSheet(
            f"""
            QProgressBar {{
                background: {T.BG_CARD};
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {colour};
                border-radius: 3px;
            }}
            """
        )

    def _reset(self) -> None:
        self.name.clear()
        self.phone.clear()
        self.price.setValue(0)
        self.seat_map.clear_selection()
        self.travel_date.setDate(QDate.currentDate())
        self._last_full_bus_id = None
        self._last_full_route_id = None
        self._last_full_travel_date = None
        self.btn_export.setVisible(False)
        self._on_route_changed()

    def _save(self) -> None:
        route = self._current_route()
        if not route:
            play_warning()
            QMessageBox.warning(self, "Vente", "Aucun trajet disponible.")
            return
        if route.statut == "inactif":
            play_warning()
            QMessageBox.warning(
                self, "Vente",
                "Ce trajet est désactivé (bus complet ou en route).\n"
                "Utilisez le bouton Réactiver si nécessaire."
            )
            return
        if not self.name.text().strip() or not self.phone.text().strip():
            play_warning()
            QMessageBox.warning(self, "Vente", "Renseignez le nom et le téléphone.")
            return
        if not self.seat_map.selected:
            play_warning()
            QMessageBox.warning(self, "Vente", "Sélectionnez un siège.")
            return
        if self.price.value() <= 0:
            play_warning()
            QMessageBox.warning(self, "Vente", "Saisissez le prix du billet.")
            return
        user = current_session.user
        if not user:
            play_error()
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

            is_full = getattr(ticket, "is_bus_full", False)
            seats_remaining = getattr(ticket, "seats_remaining", None)

            try:
                path = print_ticket(ticket, user_id=user.id if user else None)
                print_info = f"Imprimé : {path.name}"
            except Exception:
                print_info = "Impression échouée"

            # ── Alert when few seats remain (not full yet) ────────────────────
            if not is_full and seats_remaining is not None and seats_remaining <= 5:
                play_warning()
                QMessageBox.information(
                    self,
                    "Sièges limités",
                    f"Billet {ticket.numero} enregistré.\n{print_info}\n\n"
                    f"Il ne reste plus que {seats_remaining} siège(s) disponible(s) !"
                )
                self._reset()
                self.refresh()
                return

            play_print()
            QMessageBox.information(
                self,
                "Billet enregistré",
                f"Billet {ticket.numero} enregistré.\n{print_info}",
            )

            if is_full:
                # ── Bus is full: play special alert + ask for confirmation ────
                play_bus_full()
                bus_obj = getattr(ticket, "_bus", None) or ticket.bus
                route_obj = getattr(ticket, "_route", None) or ticket.route
                bus_code = bus_obj.code if bus_obj else "?"
                route_label = route_obj.short_label if route_obj else "?"

                dlg = BusFullDialog(bus_code, route_label, self)
                if dlg.exec() == QDialog.DialogCode.Accepted:
                    # User confirmed: deactivate bus + route
                    _session = get_session()
                    try:
                        from models.bus import Bus
                        from models.route import Route
                        db_bus = _session.get(Bus, ticket.bus_id)
                        db_route = _session.get(Route, ticket.route_id)
                        if db_bus:
                            db_bus.statut = "inactif"
                        if db_route:
                            db_route.statut = "inactif"
                        _session.commit()
                    finally:
                        _session.close()

                    # Store context for manifest export
                    self._last_full_bus_id = ticket.bus_id
                    self._last_full_route_id = ticket.route_id
                    self._last_full_travel_date = travel
                    self.btn_export.setVisible(True)

            self._reset()
            self.refresh()
        except Exception as e:
            session.rollback()
            play_error()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _reactivate_bus(self) -> None:
        """Reactivate the currently selected bus and route."""
        play_click()
        route = self._current_route()
        if not route:
            return
        confirm = QMessageBox.question(
            self,
            "Réactiver le bus",
            f"Voulez-vous réactiver le bus et le trajet\n"
            f"<b>{route.label}</b> ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        session = get_session()
        try:
            user = current_session.user
            uid = user.id if user else None
            from models.route import Route
            db_route = session.get(Route, route.id)
            if db_route:
                reactivate_bus(session, db_route.bus, uid)
                db_route.statut = "actif"
                session.commit()
            play_success()
            QMessageBox.information(self, "Réactivé", "Bus et trajet réactivés avec succès.")
            self.btn_reactivate.setVisible(False)
            self.btn_export.setVisible(False)
            self.refresh()
        except Exception as e:
            session.rollback()
            play_error()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _export_manifest(self) -> None:
        """Export an executive Excel passenger manifest for the selected or completed bus."""
        route = self._current_route()
        qd = self.travel_date.date()
        current_travel_date = date(qd.year(), qd.month(), qd.day())

        bus_id = None
        route_id = None
        travel_dt = current_travel_date

        if self._last_full_bus_id and self._last_full_route_id and (not route or self._last_full_route_id == route.id):
            bus_id = self._last_full_bus_id
            route_id = self._last_full_route_id
            travel_dt = self._last_full_travel_date or current_travel_date
        elif route:
            bus_id = route.bus_id
            route_id = route.id
            travel_dt = current_travel_date

        if not bus_id or not route_id:
            play_warning()
            QMessageBox.warning(self, "Export", "Aucune donnée de bus disponible pour le manifeste.")
            return

        session = get_session()
        try:
            from sqlalchemy.orm import joinedload
            from models.ticket import Ticket
            from models.route import Route
            from models.bus import Bus
            from services.export_service import export_bus_manifest_excel

            tickets = (
                session.query(Ticket)
                .options(joinedload(Ticket.cashier))
                .filter(
                    Ticket.bus_id == bus_id,
                    Ticket.route_id == route_id,
                    Ticket.travel_date == travel_dt,
                    Ticket.statut == "vendu",
                )
                .order_by(Ticket.seat_number)
                .all()
            )

            if not tickets:
                play_warning()
                QMessageBox.warning(
                    self,
                    "Export",
                    f"Aucun billet vendu trouvé pour ce trajet le {travel_dt.strftime('%d/%m/%Y')}."
                )
                return

            route_obj = session.get(Route, route_id)
            route_label = route_obj.short_label if route_obj else "trajet"

            bus_obj = session.get(Bus, bus_id)
            bus_code = bus_obj.code if bus_obj else "BUS"
            bus_capacity = bus_obj.capacite if bus_obj else 0

            travel_str = travel_dt.strftime("%Y-%m-%d") if travel_dt else "date"
            from config.settings import settings
            default_dir = Path(settings.ROOT) / "exports"
            default_dir.mkdir(parents=True, exist_ok=True)
            default_filename = str(default_dir / f"Manifeste_{bus_code}_{travel_str}.xlsx")

            file_path_str, _ = QFileDialog.getSaveFileName(
                self,
                "Choisir la destination de la liste des passagers",
                default_filename,
                "Fichier Excel (*.xlsx);;Tous les fichiers (*.*)",
            )

            if not file_path_str:
                return  # Annulé par l'utilisateur

            out_path = Path(file_path_str)

            export_bus_manifest_excel(
                tickets,
                bus_code=bus_code,
                route_label=route_label,
                travel_date=travel_dt,
                path=out_path,
                bus_capacity=bus_capacity,
            )

            play_success()
            ret = QMessageBox.information(
                self,
                "Export réussi",
                f"Le manifeste des passagers a été exporté avec un design soigné :\n\n📁 {out_path}\n\nVoulez-vous l'ouvrir maintenant ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if ret == QMessageBox.StandardButton.Yes:
                _open_file(out_path)

        except Exception as e:
            play_error()
            QMessageBox.critical(self, "Erreur export", str(e))
        finally:
            session.close()


def _open_file(path: Path) -> None:
    """Open a file with the default OS application."""
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])
    except Exception:
        pass
