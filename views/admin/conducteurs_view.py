"""Admin Conducteurs CRUD + exports."""
from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap
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
    QDateEdit,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QLabel,
    QHeaderView,
    QScrollArea,
    QFrame,
    QGridLayout,
)

from config.settings import settings
from database.session import get_session
from resources import theme as T
from services import driver_service, bus_service
from services.session_store import current_session
from utils.formatters import format_fc
from views.admin.widgets import style_table, page_toolbar, secondary_btn, kpi_card, set_kpi
from views.widgets.card import Card


class DriverDialog(QDialog):
    def __init__(self, parent=None, driver=None):
        super().__init__(parent)
        self.driver = driver
        self.photo_path = driver.photo_path if driver else None
        self.setWindowTitle("Modifier conducteur" if driver else "Nouveau conducteur")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"background:{T.BG_MAIN};")
        form = QFormLayout(self)

        self.nom = QLineEdit()
        self.prenom = QLineEdit()
        self.telephone = QLineEdit()
        self.adresse = QLineEdit()
        self.permis = QLineEdit()
        self.exp = QDateEdit()
        self.exp.setCalendarPopup(True)
        self.exp.setDate(QDate.currentDate().addYears(2))
        self.bus = QComboBox()
        self.bus.addItem("— Aucun —", None)
        self.statut = QComboBox()
        self.statut.addItems(["actif", "inactif"])
        self.dispo = QComboBox()
        self.dispo.addItems(["disponible", "en_route", "indisponible"])
        self.photo_lbl = QLabel("Aucune photo")
        photo_btn = secondary_btn("Choisir photo…")
        photo_btn.clicked.connect(self._pick)

        session = get_session()
        try:
            for b in bus_service.list_buses(session, statut="actif"):
                self.bus.addItem(b.code, b.id)
        finally:
            session.close()

        if driver:
            self.nom.setText(driver.nom)
            self.prenom.setText(driver.prenom)
            self.telephone.setText(driver.telephone or "")
            self.adresse.setText(driver.adresse or "")
            self.permis.setText(driver.numero_permis or "")
            if driver.date_expiration_permis:
                d = driver.date_expiration_permis
                self.exp.setDate(QDate(d.year, d.month, d.day))
            idx = self.bus.findData(driver.bus_id)
            if idx >= 0:
                self.bus.setCurrentIndex(idx)
            self.statut.setCurrentText(driver.statut)
            self.dispo.setCurrentText(driver.disponibilite)
            if driver.photo_path:
                self.photo_lbl.setText(driver.photo_path)

        form.addRow("Nom", self.nom)
        form.addRow("Prénom", self.prenom)
        form.addRow("Téléphone", self.telephone)
        form.addRow("Adresse", self.adresse)
        form.addRow("N° permis", self.permis)
        form.addRow("Expiration permis", self.exp)
        form.addRow("Bus assigné", self.bus)
        form.addRow("Statut", self.statut)
        form.addRow("Disponibilité", self.dispo)
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

    def _pick(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Photo", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self.photo_path = path
            self.photo_lbl.setText(path)

    def values(self) -> dict:
        qd = self.exp.date()
        return {
            "nom": self.nom.text().strip(),
            "prenom": self.prenom.text().strip(),
            "telephone": self.telephone.text().strip() or None,
            "adresse": self.adresse.text().strip() or None,
            "numero_permis": self.permis.text().strip() or None,
            "date_expiration_permis": date(qd.year(), qd.month(), qd.day()),
            "bus_id": self.bus.currentData(),
            "statut": self.statut.currentText(),
            "disponibilite": self.dispo.currentText(),
            "photo_path": self.photo_path,
        }


class ConducteursView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drivers_cache: list = []
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        toolbar, self.search, _ = page_toolbar(
            "Conducteurs",
            search_placeholder="Nom, téléphone, permis…",
            on_search=lambda _t: self.refresh(),
            add_label="Nouveau conducteur",
            on_add=self._add,
        )
        lay.addLayout(toolbar)

        top = QHBoxLayout()
        self.kpi_total = kpi_card("Total conducteurs", "0", "id-card")
        top.addWidget(self.kpi_total)
        top.addStretch()
        export_csv = secondary_btn("CSV")
        export_xlsx = secondary_btn("Excel")
        export_pdf = secondary_btn("PDF")
        export_csv.clicked.connect(lambda: self._export("csv"))
        export_xlsx.clicked.connect(lambda: self._export("xlsx"))
        export_pdf.clicked.connect(lambda: self._export("pdf"))
        top.addWidget(export_csv)
        top.addWidget(export_xlsx)
        top.addWidget(export_pdf)
        lay.addLayout(top)

        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setMaximumHeight(160)
        self.cards_scroll.setStyleSheet("border:none;")
        self.cards_host = QWidget()
        self.cards_lay = QHBoxLayout(self.cards_host)
        self.cards_lay.setSpacing(10)
        self.cards_scroll.setWidget(self.cards_host)
        lay.addWidget(self.cards_scroll)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Nom", "Téléphone", "Permis", "Expiration", "Bus", "Dispo", "Actions"]
        )
        style_table(self.table)
        self.table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.ResizeToContents
        )
        lay.addWidget(self.table, 1)

    def refresh(self) -> None:
        session = get_session()
        try:
            drivers = driver_service.list_drivers(
                session, search=self.search.text() if self.search else ""
            )
            self._drivers_cache = drivers
            set_kpi(self.kpi_total, str(len(drivers)))

            while self.cards_lay.count():
                item = self.cards_lay.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            for d in drivers[:8]:
                card = Card(padding=10)
                card.setFixedWidth(160)
                name = QLabel(d.full_name)
                name.setStyleSheet(f"font-weight:700; color:{T.TEXT_PRIMARY};")
                name.setWordWrap(True)
                bus = QLabel(d.bus.code if d.bus else "Sans bus")
                bus.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:11px;")
                dispo = QLabel(d.disponibilite)
                dispo.setStyleSheet(f"color:{T.PRIMARY_ALT}; font-size:11px; font-weight:600;")
                card.layout.addWidget(name)
                card.layout.addWidget(bus)
                card.layout.addWidget(dispo)
                self.cards_lay.addWidget(card)
            self.cards_lay.addStretch()

            self.table.setRowCount(0)
            for d in drivers:
                row = self.table.rowCount()
                self.table.insertRow(row)
                exp = (
                    d.date_expiration_permis.strftime("%d/%m/%Y")
                    if d.date_expiration_permis
                    else "—"
                )
                vals = [
                    d.full_name,
                    d.telephone or "—",
                    d.numero_permis or "—",
                    exp,
                    d.bus.code if d.bus else "—",
                    d.disponibilite,
                ]
                for col, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setData(Qt.ItemDataRole.UserRole, d.id)
                    self.table.setItem(row, col, item)
                self.table.setCellWidget(row, 6, self._actions(d.id))
        finally:
            session.close()

    def _actions(self, driver_id: int) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 2, 4, 2)
        edit = secondary_btn("Édit.")
        edit.clicked.connect(lambda: self._edit(driver_id))
        delete = secondary_btn("Suppr.")
        delete.clicked.connect(lambda: self._delete(driver_id))
        h.addWidget(edit)
        h.addWidget(delete)
        return w

    def _actor(self):
        return current_session.user.id if current_session.user else None

    def _add(self) -> None:
        dlg = DriverDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.values()
        if not data["nom"] or not data["prenom"]:
            QMessageBox.warning(self, "Conducteur", "Nom et prénom obligatoires.")
            return
        session = get_session()
        try:
            driver_service.create_driver(session, user_id=self._actor(), **data)
            session.commit()
            self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _edit(self, driver_id: int) -> None:
        session = get_session()
        try:
            d = driver_service.get_driver(session, driver_id)
            if not d:
                return
            dlg = DriverDialog(self, d)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            driver_service.update_driver(session, d, user_id=self._actor(), **dlg.values())
            session.commit()
            self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _delete(self, driver_id: int) -> None:
        if QMessageBox.question(self, "Supprimer", "Supprimer ce conducteur ?") != QMessageBox.StandardButton.Yes:
            return
        session = get_session()
        try:
            d = driver_service.get_driver(session, driver_id)
            if d:
                driver_service.delete_driver(session, d, self._actor())
                session.commit()
                self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _export(self, kind: str) -> None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if kind == "csv":
            path, _ = QFileDialog.getSaveFileName(
                self, "Export CSV", str(settings.ROOT / f"conducteurs_{stamp}.csv"), "CSV (*.csv)"
            )
            if not path:
                return
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["Nom", "Prenom", "Telephone", "Permis", "Expiration", "Bus", "Dispo", "Statut"])
                for d in self._drivers_cache:
                    w.writerow(
                        [
                            d.nom,
                            d.prenom,
                            d.telephone or "",
                            d.numero_permis or "",
                            d.date_expiration_permis or "",
                            d.bus.code if d.bus else "",
                            d.disponibilite,
                            d.statut,
                        ]
                    )
        elif kind == "xlsx":
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Excel", str(settings.ROOT / f"conducteurs_{stamp}.xlsx"), "Excel (*.xlsx)"
            )
            if not path:
                return
            wb = Workbook()
            ws = wb.active
            ws.title = "Conducteurs"
            ws.append(["Nom", "Prenom", "Telephone", "Permis", "Expiration", "Bus", "Dispo", "Statut"])
            for d in self._drivers_cache:
                ws.append(
                    [
                        d.nom,
                        d.prenom,
                        d.telephone or "",
                        d.numero_permis or "",
                        str(d.date_expiration_permis or ""),
                        d.bus.code if d.bus else "",
                        d.disponibilite,
                        d.statut,
                    ]
                )
            wb.save(path)
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "Export PDF", str(settings.ROOT / f"conducteurs_{stamp}.pdf"), "PDF (*.pdf)"
            )
            if not path:
                return
            c = canvas.Canvas(path, pagesize=A4)
            width, height = A4
            y = height - 40
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Registre des conducteurs")
            y -= 24
            c.setFont("Helvetica", 9)
            for d in self._drivers_cache:
                line = f"{d.full_name} | {d.telephone or '-'} | {d.numero_permis or '-'} | {d.disponibilite}"
                if y < 40:
                    c.showPage()
                    y = height - 40
                    c.setFont("Helvetica", 9)
                c.drawString(40, y, line[:110])
                y -= 14
            c.save()
        QMessageBox.information(self, "Export", f"Fichier enregistré :\n{path}")
