"""Admin Rapports — KPIs, charts, exports."""
from __future__ import annotations

import csv
from datetime import date, datetime, timedelta

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDateEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QScrollArea,
)

from config.settings import settings
from database.session import get_session
from resources import theme as T
from services import admin_stats_service as stats
from utils.formatters import format_fc
from views.admin.charts import ChartCanvas, plot_line_revenue, plot_bars, plot_donut
from views.admin.widgets import kpi_card, set_kpi, style_table, secondary_btn
from views.widgets.card import Card


class RapportsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_kpis = {
            "recettes_total": 0,
            "nb_billets": 0,
            "nb_bagages": 0,
            "recettes_billets": 0,
            "recettes_bagages": 0,
        }
        self._last_routes: list = []
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;")
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setSpacing(12)

        title = QLabel("Rapports")
        title.setStyleSheet(
            f"color:{T.PRIMARY_ALT}; font-size:{T.SIZE_CARD_TITLE}px; font-weight:700;"
        )
        lay.addWidget(title)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Du"))
        self.start = QDateEdit()
        self.start.setCalendarPopup(True)
        self.start.setDate(QDate.currentDate().addDays(-30))
        filters.addWidget(self.start)
        filters.addWidget(QLabel("Au"))
        self.end = QDateEdit()
        self.end.setCalendarPopup(True)
        self.end.setDate(QDate.currentDate())
        filters.addWidget(self.end)
        apply = QPushButton("Actualiser")
        apply.setObjectName("primaryBtn")
        apply.clicked.connect(self.refresh)
        filters.addWidget(apply)
        filters.addStretch()
        for label, kind in (("CSV", "csv"), ("Excel", "xlsx"), ("PDF", "pdf")):
            btn = secondary_btn(label)
            btn.clicked.connect(lambda checked=False, k=kind: self._export(k))
            filters.addWidget(btn)
        lay.addLayout(filters)

        kpis = QHBoxLayout()
        self.k_total = kpi_card("Recettes totales", "0 FC", "coins")
        self.k_billets = kpi_card("Billets", "0", "ticket")
        self.k_bag = kpi_card("Bagages", "0", "box")
        self.k_tb = kpi_card("Recettes billets", "0 FC", "ticket")
        self.k_lg = kpi_card("Recettes bagages", "0 FC", "box")
        for k in (self.k_total, self.k_billets, self.k_bag, self.k_tb, self.k_lg):
            kpis.addWidget(k)
        lay.addLayout(kpis)

        charts = QHBoxLayout()
        c1 = Card(padding=8)
        self.line = ChartCanvas(width=5.5, height=2.8)
        c1.layout.addWidget(self.line)
        charts.addWidget(c1, 3)
        c2 = Card(padding=8)
        self.donut = ChartCanvas(width=3.5, height=2.8)
        c2.layout.addWidget(self.donut)
        charts.addWidget(c2, 2)
        lay.addLayout(charts)

        c3 = Card(padding=8)
        self.bars = ChartCanvas(width=8, height=2.8)
        c3.layout.addWidget(self.bars)
        lay.addWidget(c3)

        lay.addWidget(QLabel("Performance par trajet"))
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Trajet", "Billets", "Recettes"])
        style_table(self.table)
        self.table.setMaximumHeight(220)
        lay.addWidget(self.table)

        scroll.setWidget(body)
        outer.addWidget(scroll)

    def _range(self) -> tuple[date, date]:
        s = self.start.date()
        e = self.end.date()
        return date(s.year(), s.month(), s.day()), date(e.year(), e.month(), e.day())

    def refresh(self) -> None:
        start, end = self._range()
        if end < start:
            QMessageBox.warning(self, "Rapports", "La date de fin doit être ≥ début.")
            return
        days = (end - start).days + 1
        session = get_session()
        try:
            k = stats.period_kpis(session, start, end)
            self._last_kpis = k
            set_kpi(self.k_total, format_fc(k["recettes_total"]))
            set_kpi(self.k_billets, str(k["nb_billets"]))
            set_kpi(self.k_bag, str(k["nb_bagages"]))
            set_kpi(self.k_tb, format_fc(k["recettes_billets"]))
            set_kpi(self.k_lg, format_fc(k["recettes_bagages"]))

            chart_days = min(max(days, 1), 90)
            series = stats.revenue_by_day(session, chart_days, end=end)
            dates = [d for d, _ in series]
            vals = [v for _, v in series]
            plot_line_revenue(self.line, dates, vals, title="Revenus période")
            plot_donut(
                self.donut,
                ["Billets", "Bagages"],
                [k["recettes_billets"], k["recettes_bagages"]],
                title="Répartition",
            )
            by_route = stats.sales_by_route(
                session, max(days, 1), limit=10, start=start, end=end
            )
            self._last_routes = by_route
            plot_bars(
                self.bars,
                [r[0][:16] for r in by_route],
                [float(r[2]) for r in by_route],
                title="Recettes par trajet",
            )
            self.table.setRowCount(0)
            for label, count, amount in by_route:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(label))
                self.table.setItem(row, 1, QTableWidgetItem(str(count)))
                self.table.setItem(row, 2, QTableWidgetItem(format_fc(amount)))
        finally:
            session.close()

    def _export(self, kind: str) -> None:
        self.refresh()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        start, end = self._range()
        k = self._last_kpis
        routes = self._last_routes
        if kind == "csv":
            path, _ = QFileDialog.getSaveFileName(
                self, "Export CSV", str(settings.ROOT / f"rapport_{stamp}.csv"), "CSV (*.csv)"
            )
            if not path:
                return
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["Periode", f"{start} - {end}"])
                w.writerow(["Recettes totales", float(k["recettes_total"])])
                w.writerow(["Billets", k["nb_billets"], float(k["recettes_billets"])])
                w.writerow(["Bagages", k["nb_bagages"], float(k["recettes_bagages"])])
                w.writerow([])
                w.writerow(["Trajet", "Billets", "Recettes"])
                for label, count, amount in routes:
                    w.writerow([label, count, float(amount)])
        elif kind == "xlsx":
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Excel", str(settings.ROOT / f"rapport_{stamp}.xlsx"), "Excel (*.xlsx)"
            )
            if not path:
                return
            wb = Workbook()
            ws = wb.active
            ws.title = "Rapport"
            ws.append(["Période", f"{start} - {end}"])
            ws.append(["Recettes totales", float(k["recettes_total"])])
            ws.append(["Billets", k["nb_billets"], float(k["recettes_billets"])])
            ws.append(["Bagages", k["nb_bagages"], float(k["recettes_bagages"])])
            ws.append([])
            ws.append(["Trajet", "Billets", "Recettes"])
            for label, count, amount in routes:
                ws.append([label, count, float(amount)])
            wb.save(path)
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "Export PDF", str(settings.ROOT / f"rapport_{stamp}.pdf"), "PDF (*.pdf)"
            )
            if not path:
                return
            c = canvas.Canvas(path, pagesize=A4)
            _width, height = A4
            y = height - 40
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Rapport NGOKAF TRANS")
            y -= 20
            c.setFont("Helvetica", 10)
            c.drawString(40, y, f"Période : {start} — {end}")
            y -= 18
            c.drawString(40, y, f"Recettes totales : {format_fc(k['recettes_total'])}")
            y -= 14
            c.drawString(40, y, f"Billets : {k['nb_billets']} ({format_fc(k['recettes_billets'])})")
            y -= 14
            c.drawString(40, y, f"Bagages : {k['nb_bagages']} ({format_fc(k['recettes_bagages'])})")
            y -= 24
            c.setFont("Helvetica-Bold", 10)
            c.drawString(40, y, "Par trajet")
            y -= 14
            c.setFont("Helvetica", 9)
            for label, count, amount in routes:
                if y < 40:
                    c.showPage()
                    y = height - 40
                    c.setFont("Helvetica", 9)
                c.drawString(40, y, f"{label[:40]} | {count} | {format_fc(amount)}")
                y -= 12
            c.save()
        QMessageBox.information(self, "Export", f"Fichier enregistré :\n{path}")
