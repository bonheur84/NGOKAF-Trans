"""Admin Trajets CRUD."""
from __future__ import annotations

from datetime import time
from decimal import Decimal

from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QTimeEdit,
    QDoubleSpinBox,
    QPushButton,
    QMessageBox,
    QLabel,
    QHeaderView,
)

from database.session import get_session
from resources import theme as T
from services import bus_service, driver_service
from services.session_store import current_session
from utils.formatters import format_fc
from views.admin.widgets import (
    style_table, page_toolbar, secondary_btn,
    edit_action_btn, delete_action_btn, toggle_action_btn
)


class RouteDialog(QDialog):
    def __init__(self, parent=None, route=None):
        super().__init__(parent)
        self.route = route
        self.setWindowTitle("Modifier le trajet" if route else "Nouveau trajet")
        self.setMinimumWidth(420)
        form = QFormLayout(self)
        form.setSpacing(10)

        self.depart = QLineEdit()
        self.arrivee = QLineEdit()
        self.prix = QDoubleSpinBox()
        self.prix.setRange(0, 10_000_000)
        self.prix.setSuffix(" FC")
        self.prix.setDecimals(0)
        self.prix.setSingleStep(500)
        self.bus = QComboBox()
        self.driver = QComboBox()
        self.driver.addItem("— Aucun —", None)
        self.statut = QComboBox()
        self.statut.addItems(["actif", "inactif"])

        session = get_session()
        try:
            for b in bus_service.list_buses(session, statut="actif"):
                self.bus.addItem(f"{b.code} ({b.capacite} pl.)", b.id)
            for d in driver_service.list_drivers(session, statut="actif"):
                self.driver.addItem(d.full_name, d.id)
        finally:
            session.close()

        if route:
            self.depart.setText(route.ville_depart)
            self.arrivee.setText(route.ville_arrivee)
            if route.prix_indicatif is not None:
                self.prix.setValue(float(route.prix_indicatif))
            idx = self.bus.findData(route.bus_id)
            if idx >= 0:
                self.bus.setCurrentIndex(idx)
            idx = self.driver.findData(route.driver_id)
            if idx >= 0:
                self.driver.setCurrentIndex(idx)
            self.statut.setCurrentText(route.statut)

        form.addRow("Ville départ", self.depart)
        form.addRow("Ville arrivée", self.arrivee)
        form.addRow("Prix", self.prix)
        form.addRow("Bus", self.bus)
        form.addRow("Conducteur", self.driver)
        form.addRow("Statut", self.statut)

        # Auto-assign driver based on bus selection
        self.bus.currentIndexChanged.connect(self._on_bus_changed)

        row = QHBoxLayout()
        cancel = secondary_btn("Annuler")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Enregistrer")
        ok.setObjectName("primaryBtn")
        ok.clicked.connect(self.accept)
        row.addStretch()
        row.addWidget(cancel)
        row.addWidget(ok)
        form.addRow(row)

    def _on_bus_changed(self) -> None:
        bus_id = self.bus.currentData()
        if not bus_id:
            self.driver.setCurrentIndex(0)
            return

        from models.driver import Driver
        session = get_session()
        try:
            d = session.query(Driver).filter(Driver.bus_id == bus_id, Driver.statut == "actif").first()
            if d:
                idx = self.driver.findData(d.id)
                if idx >= 0:
                    self.driver.setCurrentIndex(idx)
            else:
                self.driver.setCurrentIndex(0)
        finally:
            session.close()

    def values(self) -> dict:
        return {
            "ville_depart": self.depart.text().strip(),
            "ville_arrivee": self.arrivee.text().strip(),
            "heure_depart": time(0, 0),
            "heure_arrivee": None,
            "distance_km": None,
            "prix_indicatif": Decimal(str(int(self.prix.value()))),
            "bus_id": self.bus.currentData(),
            "driver_id": self.driver.currentData(),
            "statut": self.statut.currentText(),
        }


class TrajetsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        toolbar, self.search, _ = page_toolbar(
            "Trajets",
            search_placeholder="Rechercher une ville…",
            on_search=lambda _t: self.refresh(),
            add_label="Nouveau trajet",
            on_add=self._add,
        )
        lay.addLayout(toolbar)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Statut"))
        self.statut = QComboBox()
        self.statut.addItem("Tous", None)
        self.statut.addItem("Actifs", "actif")
        self.statut.addItem("Inactifs", "inactif")
        self.statut.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.statut)
        filters.addStretch()
        lay.addLayout(filters)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Départ", "Arrivée", "Prix", "Bus", "Conducteur", "Statut", "Actions"]
        )
        style_table(self.table)
        self.table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.Interactive
        )
        self.table.setColumnWidth(6, 220)
        lay.addWidget(self.table, 1)

    def refresh(self) -> None:
        session = get_session()
        try:
            routes = bus_service.list_routes(
                session,
                search=self.search.text() if self.search else "",
                statut=self.statut.currentData(),
            )
            self.table.setRowCount(0)
            for r in routes:
                row = self.table.rowCount()
                self.table.insertRow(row)
                vals = [
                    r.ville_depart,
                    r.ville_arrivee,
                    format_fc(r.prix_indicatif),
                    r.bus.code if r.bus else "—",
                    r.driver.full_name if r.driver else "—",
                    r.statut,
                ]
                for col, v in enumerate(vals):
                    item = QTableWidgetItem(str(v))
                    item.setData(Qt.ItemDataRole.UserRole, r.id)
                    self.table.setItem(row, col, item)
                self.table.setCellWidget(row, 6, self._actions(r.id, r.statut))
        finally:
            session.close()

    def _actions(self, route_id: int, statut: str) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(4)
        edit = edit_action_btn("Édit.")
        edit.clicked.connect(lambda: self._edit(route_id))
        btn_label = "Désactiver" if statut == "actif" else "Réactiver"
        toggle = toggle_action_btn(btn_label, active=(statut == "actif"))
        toggle.clicked.connect(lambda: self._toggle(route_id, statut))
        delete = delete_action_btn("Suppr.")
        delete.clicked.connect(lambda: self._delete(route_id))
        h.addWidget(edit)
        h.addWidget(toggle)
        h.addWidget(delete)
        return w

    def _actor(self) -> int | None:
        return current_session.user.id if current_session.user else None

    def _add(self) -> None:
        dlg = RouteDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.values()
        if not data["ville_depart"] or not data["ville_arrivee"] or not data["bus_id"]:
            QMessageBox.warning(self, "Trajet", "Villes et bus sont obligatoires.")
            return
        session = get_session()
        try:
            bus_service.create_route(session, user_id=self._actor(), **data)
            session.commit()
            self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _edit(self, route_id: int) -> None:
        session = get_session()
        try:
            route = bus_service.get_route(session, route_id)
            if not route:
                return
            dlg = RouteDialog(self, route)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            data = dlg.values()
            bus_service.update_route(session, route, user_id=self._actor(), **data)
            session.commit()
            self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _toggle(self, route_id: int, statut: str) -> None:
        new_s = "inactif" if statut == "actif" else "actif"
        session = get_session()
        try:
            route = bus_service.get_route(session, route_id)
            if route:
                bus_service.set_route_statut(session, route, new_s, self._actor())
                session.commit()
                self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _delete(self, route_id: int) -> None:
        if QMessageBox.question(self, "Supprimer", "Supprimer ce trajet ?") != QMessageBox.StandardButton.Yes:
            return
        session = get_session()
        try:
            route = bus_service.get_route(session, route_id)
            if route:
                bus_service.delete_route(session, route, self._actor())
                self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()
