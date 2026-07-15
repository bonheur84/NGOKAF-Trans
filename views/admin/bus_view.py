"""Admin Bus CRUD."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, QDate
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
    QSpinBox,
    QDateEdit,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QLabel,
    QHeaderView,
)

from database.session import get_session
from resources import theme as T
from services import bus_service
from services.session_store import current_session
from views.admin.widgets import style_table, page_toolbar, secondary_btn


class BusDialog(QDialog):
    def __init__(self, parent=None, bus=None):
        super().__init__(parent)
        self.bus = bus
        self.photo_path = bus.photo_path if bus else None
        self.setWindowTitle("Modifier le bus" if bus else "Nouveau bus")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"background:{T.BG_MAIN};")
        form = QFormLayout(self)

        self.code = QLineEdit()
        self.plaque = QLineEdit()
        self.marque = QLineEdit()
        self.modele = QLineEdit()
        self.annee = QSpinBox()
        self.annee.setRange(1990, 2100)
        self.annee.setValue(2020)
        self.couleur = QLineEdit()
        self.capacite = QSpinBox()
        self.capacite.setRange(10, 80)
        self.capacite.setValue(60)
        self.layout_c = QComboBox()
        self.layout_c.addItems(["2-2", "2-1", "1-2"])
        self.date_achat = QDateEdit()
        self.date_achat.setCalendarPopup(True)
        self.date_achat.setDate(QDate.currentDate())
        self.statut = QComboBox()
        self.statut.addItems(["actif", "maintenance", "inactif"])
        self.photo_lbl = QLabel("Aucune photo")
        photo_btn = secondary_btn("Choisir photo…")
        photo_btn.clicked.connect(self._pick_photo)

        if bus:
            self.code.setText(bus.code)
            self.plaque.setText(bus.plaque or "")
            self.marque.setText(bus.marque or "")
            self.modele.setText(bus.modele or "")
            if bus.annee:
                self.annee.setValue(bus.annee)
            self.couleur.setText(bus.couleur or "")
            self.capacite.setValue(bus.capacite)
            self.layout_c.setCurrentText(bus.layout or "2-2")
            if bus.date_achat:
                self.date_achat.setDate(
                    QDate(bus.date_achat.year, bus.date_achat.month, bus.date_achat.day)
                )
            self.statut.setCurrentText(bus.statut)
            if bus.photo_path:
                self.photo_lbl.setText(bus.photo_path)

        form.addRow("Code", self.code)
        form.addRow("Plaque", self.plaque)
        form.addRow("Marque", self.marque)
        form.addRow("Modèle", self.modele)
        form.addRow("Année", self.annee)
        form.addRow("Couleur", self.couleur)
        form.addRow("Capacité", self.capacite)
        form.addRow("Layout sièges", self.layout_c)
        form.addRow("Date achat", self.date_achat)
        form.addRow("Statut", self.statut)
        form.addRow("Photo", photo_btn)
        form.addRow("", self.photo_lbl)

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

    def _pick_photo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Photo bus", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self.photo_path = path
            self.photo_lbl.setText(path)

    def values(self) -> dict:
        qd = self.date_achat.date()
        return {
            "code": self.code.text().strip(),
            "plaque": self.plaque.text().strip() or None,
            "marque": self.marque.text().strip() or None,
            "modele": self.modele.text().strip() or None,
            "annee": self.annee.value(),
            "couleur": self.couleur.text().strip() or None,
            "capacite": self.capacite.value(),
            "layout": self.layout_c.currentText(),
            "date_achat": date(qd.year(), qd.month(), qd.day()),
            "photo_path": self.photo_path,
            "statut": self.statut.currentText(),
        }


class BusView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        toolbar, self.search, _ = page_toolbar(
            "Parc de bus",
            search_placeholder="Code, plaque, marque…",
            on_search=lambda _t: self.refresh(),
            add_label="Nouveau bus",
            on_add=self._add,
        )
        lay.addLayout(toolbar)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Statut"))
        self.statut = QComboBox()
        self.statut.addItem("Tous", None)
        self.statut.addItem("Actifs", "actif")
        self.statut.addItem("Maintenance", "maintenance")
        self.statut.addItem("Inactifs", "inactif")
        self.statut.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.statut)
        filters.addStretch()
        lay.addLayout(filters)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Code", "Plaque", "Marque / Modèle", "Capacité", "Layout", "Statut", "Actions"]
        )
        style_table(self.table)
        self.table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.ResizeToContents
        )
        lay.addWidget(self.table, 1)

    def refresh(self) -> None:
        session = get_session()
        try:
            buses = bus_service.list_buses(
                session,
                search=self.search.text() if self.search else "",
                statut=self.statut.currentData(),
            )
            self.table.setRowCount(0)
            for b in buses:
                row = self.table.rowCount()
                self.table.insertRow(row)
                mm = " / ".join(filter(None, [b.marque, b.modele])) or "—"
                vals = [b.code, b.plaque or "—", mm, str(b.capacite), b.layout, b.statut]
                for col, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setData(Qt.ItemDataRole.UserRole, b.id)
                    self.table.setItem(row, col, item)
                self.table.setCellWidget(row, 6, self._actions(b.id, b.statut))
        finally:
            session.close()

    def _actions(self, bus_id: int, statut: str) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(4)
        edit = secondary_btn("Édit.")
        edit.clicked.connect(lambda: self._edit(bus_id))
        toggle = secondary_btn("Off" if statut == "actif" else "On")
        toggle.clicked.connect(lambda: self._toggle(bus_id, statut))
        delete = secondary_btn("Suppr.")
        delete.clicked.connect(lambda: self._delete(bus_id))
        h.addWidget(edit)
        h.addWidget(toggle)
        h.addWidget(delete)
        return w

    def _actor(self) -> int | None:
        return current_session.user.id if current_session.user else None

    def _add(self) -> None:
        dlg = BusDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.values()
        if not data["code"]:
            QMessageBox.warning(self, "Bus", "Le code est obligatoire.")
            return
        session = get_session()
        try:
            bus_service.create_bus_with_seats(session, user_id=self._actor(), **data)
            session.commit()
            self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _edit(self, bus_id: int) -> None:
        session = get_session()
        try:
            bus = bus_service.get_bus(session, bus_id)
            if not bus:
                return
            dlg = BusDialog(self, bus)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            data = dlg.values()
            bus_service.update_bus(session, bus, user_id=self._actor(), **data)
            session.commit()
            self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _toggle(self, bus_id: int, statut: str) -> None:
        new_s = "inactif" if statut == "actif" else "actif"
        session = get_session()
        try:
            bus = bus_service.get_bus(session, bus_id)
            if bus:
                bus_service.set_bus_statut(session, bus, new_s, self._actor())
                session.commit()
                self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _delete(self, bus_id: int) -> None:
        if QMessageBox.question(self, "Supprimer", "Supprimer ce bus ?") != QMessageBox.StandardButton.Yes:
            return
        session = get_session()
        try:
            bus = bus_service.get_bus(session, bus_id)
            if bus:
                bus_service.delete_bus(session, bus, self._actor())
                session.commit()
                self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()
