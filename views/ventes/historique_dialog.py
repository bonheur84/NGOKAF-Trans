"""Sales history dialog with filters and exports."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QDateEdit,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QComboBox,
)

from database.session import get_session
from models.ticket import Ticket
from resources import theme as T
from services.sale_service import search_tickets, cancel_ticket
from services.session_store import current_session
from services.export_service import export_tickets_csv, export_tickets_excel, export_tickets_pdf
from services.audit_service import log_audit
from models.audit import AuditLog, LoginLog
from sqlalchemy.orm import joinedload


class HistoriqueDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historique des ventes & journaux")
        self.resize(1000, 640)
        self.setStyleSheet(f"background:{T.BG_MAIN};")
        self._build()
        self.reload()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        title = QLabel("Historique des ventes")
        title.setStyleSheet(
            f"font-size:24px; font-weight:700; color:{T.PRIMARY_ALT};"
        )
        lay.addWidget(title)

        filters = QHBoxLayout()
        self.q = QLineEdit()
        self.q.setPlaceholderText("Passager, téléphone, n° billet...")
        self.q.setMinimumHeight(40)
        self.q.textChanged.connect(self.reload)
        filters.addWidget(self.q, 2)

        self.d_from = QDateEdit(QDate.currentDate().addDays(-7))
        self.d_from.setCalendarPopup(True)
        self.d_from.setDisplayFormat("dd/MM/yyyy")
        self.d_to = QDateEdit(QDate.currentDate())
        self.d_to.setCalendarPopup(True)
        self.d_to.setDisplayFormat("dd/MM/yyyy")
        self.d_from.dateChanged.connect(self.reload)
        self.d_to.dateChanged.connect(self.reload)
        filters.addWidget(QLabel("Du"))
        filters.addWidget(self.d_from)
        filters.addWidget(QLabel("Au"))
        filters.addWidget(self.d_to)
        lay.addLayout(filters)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["N°", "Date", "Passager", "Tél", "Trajet", "Siège", "Prix", "Statut"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setStyleSheet(
            f"QTableWidget{{background:{T.BG_CARD}; border-radius:12px;}}"
        )
        lay.addWidget(self.table, 1)

        actions = QHBoxLayout()
        btn_cancel = QPushButton("Annuler le billet sélectionné")
        btn_cancel.clicked.connect(self._cancel_selected)
        btn_csv = QPushButton("Export CSV")
        btn_xlsx = QPushButton("Export Excel")
        btn_pdf = QPushButton("Export PDF")
        btn_logs = QPushButton("Voir journaux")
        for b in (btn_cancel, btn_csv, btn_xlsx, btn_pdf, btn_logs):
            b.setMinimumHeight(40)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton{{background:{T.PRIMARY};color:white;border:none;"
                f"border-radius:10px;padding:8px 14px;font-weight:600;}}"
                f"QPushButton:hover{{background:{T.HOVER};}}"
            )
            actions.addWidget(b)
        btn_csv.clicked.connect(lambda: self._export("csv"))
        btn_xlsx.clicked.connect(lambda: self._export("xlsx"))
        btn_pdf.clicked.connect(lambda: self._export("pdf"))
        btn_logs.clicked.connect(self._show_logs)
        lay.addLayout(actions)
        self._tickets = []

    def reload(self) -> None:
        session = get_session()
        try:
            df = self.d_from.date()
            dt = self.d_to.date()
            self._tickets = search_tickets(
                session,
                query=self.q.text().strip(),
                date_from=date(df.year(), df.month(), df.day()),
                date_to=date(dt.year(), dt.month(), dt.day()),
            )
            self.table.setRowCount(0)
            for t in self._tickets:
                r = self.table.rowCount()
                self.table.insertRow(r)
                vals = [
                    t.numero,
                    t.date_vente.isoformat(),
                    t.passenger_name,
                    t.phone,
                    t.route.short_label if t.route else "",
                    str(t.seat_number),
                    f"{float(t.price):.0f}",
                    t.statut,
                ]
                for c, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setData(Qt.ItemDataRole.UserRole, t.id)
                    self.table.setItem(r, c, item)
        finally:
            session.close()

    def _selected_ticket_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _cancel_selected(self) -> None:
        tid = self._selected_ticket_id()
        if not tid:
            QMessageBox.information(self, "Annulation", "Sélectionnez un billet.")
            return
        user = current_session.user
        if not user:
            return
        session = get_session()
        try:
            cancel_ticket(session, tid, user, reason="Annulation caissier")
            QMessageBox.information(self, "Annulation", "Billet annulé. Siège libéré.")
            self.reload()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _export(self, kind: str) -> None:
        if not self._tickets:
            QMessageBox.information(self, "Export", "Aucune donnée à exporter.")
            return
        if kind == "csv":
            path, _ = QFileDialog.getSaveFileName(self, "CSV", "ventes.csv", "CSV (*.csv)")
            if path:
                export_tickets_csv(self._tickets, Path(path))
        elif kind == "xlsx":
            path, _ = QFileDialog.getSaveFileName(self, "Excel", "ventes.xlsx", "Excel (*.xlsx)")
            if path:
                export_tickets_excel(self._tickets, Path(path))
        else:
            path, _ = QFileDialog.getSaveFileName(self, "PDF", "ventes.pdf", "PDF (*.pdf)")
            if path:
                export_tickets_pdf(self._tickets, Path(path))
        if path:
            QMessageBox.information(self, "Export", f"Fichier enregistré :\n{path}")

    def _show_logs(self) -> None:
        session = get_session()
        try:
            audits = (
                session.query(AuditLog)
                .order_by(AuditLog.created_at.desc())
                .limit(100)
                .all()
            )
            logins = (
                session.query(LoginLog)
                .order_by(LoginLog.created_at.desc())
                .limit(50)
                .all()
            )
            lines = ["=== AUDIT ==="]
            for a in audits:
                lines.append(
                    f"{a.created_at:%Y-%m-%d %H:%M} | {a.action} | {a.entity}#{a.entity_id} | {a.details or ''}"
                )
            lines.append("\n=== CONNEXIONS ===")
            for l in logins:
                lines.append(
                    f"{l.created_at:%Y-%m-%d %H:%M} | {l.username} | {'OK' if l.success else 'KO'}"
                )
            QMessageBox.information(self, "Journaux", "\n".join(lines[:80]))
        finally:
            session.close()
