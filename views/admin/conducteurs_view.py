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
from views.admin.widgets import (
    style_table, page_toolbar, secondary_btn,
    edit_action_btn, delete_action_btn,
    kpi_card, set_kpi
)
from views.widgets.card import Card


class DriverDialog(QDialog):
    def __init__(self, parent=None, driver=None):
        super().__init__(parent)
        self.driver = driver
        self.photo_path = driver.photo_path if driver else None
        self.setWindowTitle("Modifier conducteur" if driver else "Nouveau conducteur")
        self.setMinimumWidth(420)
        form = QFormLayout(self)

        self.nom = QLineEdit()
        self.prenom = QLineEdit()
        self.telephone = QLineEdit()
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
        return {
            "nom": self.nom.text().strip(),
            "prenom": self.prenom.text().strip(),
            "telephone": self.telephone.text().strip() or None,
            "adresse": None,
            "numero_permis": None,
            "date_expiration_permis": None,
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
        self.cards_scroll.setFixedHeight(230)
        self.cards_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cards_scroll.setStyleSheet("border:none; background:transparent;")
        self.cards_host = QWidget()
        self.cards_host.setStyleSheet("background:transparent;")
        self.cards_lay = QHBoxLayout(self.cards_host)
        self.cards_lay.setContentsMargins(2, 2, 2, 2)
        self.cards_lay.setSpacing(10)
        self.cards_scroll.setWidget(self.cards_host)
        lay.addWidget(self.cards_scroll)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Nom", "Téléphone", "Bus", "Dispo", "Actions"]
        )
        style_table(self.table)
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Interactive
        )
        self.table.setColumnWidth(4, 160)
        lay.addWidget(self.table, 1)

    def refresh(self) -> None:
        session = get_session()
        try:
            drivers = driver_service.list_drivers(
                session, search=self.search.text() if self.search else ""
            )
            self._drivers_cache = drivers
            set_kpi(self.kpi_total, str(len(drivers)))

            from PySide6.QtGui import QPixmap, QPainter, QPainterPath

            while self.cards_lay.count():
                item = self.cards_lay.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            for d in drivers:
                card = Card(padding=12)
                card.setFixedWidth(180)
                card.setFixedHeight(190)
                card.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # Avatar container (Round image or Initials)
                avatar_lbl = QLabel()
                avatar_lbl.setFixedSize(70, 70)
                avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

                has_photo = False
                if d.photo_path:
                    src = QPixmap(d.photo_path)
                    if not src.isNull():
                        dst = QPixmap(70, 70)
                        dst.fill(Qt.GlobalColor.transparent)
                        painter = QPainter(dst)
                        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                        path = QPainterPath()
                        path.addEllipse(0, 0, 70, 70)
                        painter.setClipPath(path)
                        scaled = src.scaled(
                            70, 70,
                            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        painter.drawPixmap(0, 0, scaled)
                        painter.end()
                        avatar_lbl.setPixmap(dst)
                        has_photo = True

                if not has_photo:
                    initials = "".join([p[0] for p in d.full_name.split()[:2]]).upper() or "?"
                    avatar_lbl.setText(initials)
                    avatar_lbl.setStyleSheet(
                        f"""
                        background-color: {T.PRIMARY}18;
                        color: {T.PRIMARY_ALT};
                        border-radius: 35px;
                        font-size: 22px;
                        font-weight: bold;
                        border: 2px solid {T.PRIMARY}33;
                        """
                    )

                card.layout.addWidget(avatar_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

                # Name
                name = QLabel(d.full_name)
                name.setStyleSheet(f"font-weight:700; color:{T.TEXT_PRIMARY}; font-size:12px;")
                name.setWordWrap(True)
                name.setAlignment(Qt.AlignmentFlag.AlignCenter)
                card.layout.addWidget(name)

                # Bus
                bus = QLabel(d.bus.code if d.bus else "Sans bus")
                bus.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:11px;")
                bus.setAlignment(Qt.AlignmentFlag.AlignCenter)
                card.layout.addWidget(bus)

                # Status Badge
                dispo = QLabel(d.disponibilite.upper().replace("_", " "))
                if d.disponibilite == "disponible":
                    dispo.setStyleSheet(
                        "color: #10B981; background-color: #ECFDF5; border: 1px solid #A7F3D0; "
                        "border-radius: 10px; padding: 2px 8px; font-size: 9px; font-weight: 700;"
                    )
                elif d.disponibilite == "en_route":
                    dispo.setStyleSheet(
                        "color: #3B82F6; background-color: #EFF6FF; border: 1px solid #BFDBFE; "
                        "border-radius: 10px; padding: 2px 8px; font-size: 9px; font-weight: 700;"
                    )
                else:
                    dispo.setStyleSheet(
                        "color: #EF4444; background-color: #FEF2F2; border: 1px solid #FCA5A5; "
                        "border-radius: 10px; padding: 2px 8px; font-size: 9px; font-weight: 700;"
                    )
                dispo.setAlignment(Qt.AlignmentFlag.AlignCenter)
                card.layout.addWidget(dispo, alignment=Qt.AlignmentFlag.AlignCenter)

                self.cards_lay.addWidget(card)
            self.cards_lay.addStretch()

            self.table.setRowCount(0)
            for d in drivers:
                row = self.table.rowCount()
                self.table.insertRow(row)
                vals = [
                    d.full_name,
                    d.telephone or "—",
                    d.bus.code if d.bus else "—",
                    d.disponibilite,
                ]
                for col, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setData(Qt.ItemDataRole.UserRole, d.id)
                    self.table.setItem(row, col, item)
                self.table.setCellWidget(row, 4, self._actions(d.id))
        finally:
            session.close()

    def _actions(self, driver_id: int) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(4)
        edit = edit_action_btn("Édit.")
        edit.clicked.connect(lambda: self._edit(driver_id))
        delete = delete_action_btn("Suppr.")
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
                w.writerow(["Nom", "Prenom", "Telephone", "Bus", "Dispo", "Statut"])
                for d in self._drivers_cache:
                    w.writerow(
                        [
                            d.nom,
                            d.prenom,
                            d.telephone or "",
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
            ws.append(["Nom", "Prenom", "Telephone", "Bus", "Dispo", "Statut"])
            for d in self._drivers_cache:
                ws.append(
                    [
                        d.nom,
                        d.prenom,
                        d.telephone or "",
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
                line = f"{d.full_name} | {d.telephone or '-'} | {d.disponibilite}"
                if y < 40:
                    c.showPage()
                    y = height - 40
                    c.setFont("Helvetica", 9)
                c.drawString(40, y, line[:110])
                y -= 14
            c.save()
        QMessageBox.information(self, "Export", f"Fichier enregistré :\n{path}")
