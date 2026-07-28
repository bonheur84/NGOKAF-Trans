"""Admin Rapports — KPIs, charts, styled exports & period presets."""
from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDateEdit,
    QComboBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QScrollArea,
    QHeaderView,
    QAbstractItemView,
)

from config.settings import settings
from database.session import get_session
from resources import theme as T
from services import admin_stats_service as stats
from services import export_service
from utils.formatters import format_fc
from utils.icons import fa_icon, ICONS, apply_button_icon
from views.admin.charts import ChartCanvas, plot_line_revenue, plot_bars, plot_donut
from views.admin.widgets import kpi_card, set_kpi
from views.widgets.card import Card


# ─── Style constants ───────────────────────────────────────────────────────────
_COL_HEADER_BG  = "#8C6A00"
_COL_HEADER_FG  = "#FFFFFF"
_COL_ROW_ODD    = "#FFFDF9"
_COL_ROW_EVEN   = "#FFF6E8"
_COL_BORDER     = "#E4D8C3"
_COL_TOTAL_BG   = "#F2EADF"

_ALIGN_RIGHT  = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
_ALIGN_CENTER = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter
_ALIGN_LEFT   = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft


def _apply_table_style(table: QTableWidget, row_height: int = 36) -> None:
    table.setAlternatingRowColors(False)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(row_height)
    table.setShowGrid(False)
    table.setStyleSheet(f"""
        QTableWidget {{
            background: {_COL_ROW_ODD};
            border: 1px solid {_COL_BORDER};
            border-radius: 10px;
            gridline-color: transparent;
            outline: 0;
        }}
        QHeaderView::section {{
            background: {_COL_HEADER_BG};
            color: {_COL_HEADER_FG};
            font-weight: 700;
            font-size: 12px;
            padding: 8px 10px;
            border: none;
            border-right: 1px solid rgba(255,255,255,0.15);
        }}
        QHeaderView::section:last {{ border-right: none; }}
        QTableWidget::item {{
            padding: 6px 10px;
            border-bottom: 1px solid {_COL_BORDER};
            color: {T.TEXT_PRIMARY};
        }}
        QTableWidget::item:selected {{
            background: {T.BG_SELECTION};
            color: {T.TEXT_PRIMARY};
        }}
    """)


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
        self._on_preset_changed(2)  # Default: Ce mois
        self.refresh()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setSpacing(14)
        lay.setContentsMargins(2, 4, 6, 8)

        # ── Header
        head = QHBoxLayout()
        head.setSpacing(10)
        ic = QLabel()
        ic.setPixmap(fa_icon(ICONS["reports"], color=T.PRIMARY_ALT).pixmap(26, 26))
        head.addWidget(ic)

        title = QLabel("Rapports d'Activité & Statistiques")
        title.setStyleSheet(f"color:{T.PRIMARY_ALT}; font-size:{T.SIZE_CARD_TITLE}px; font-weight:700;")
        head.addWidget(title)
        head.addStretch()
        lay.addLayout(head)

        # ── Filter toolbar
        filter_card = Card(padding=12)
        filters = QHBoxLayout()
        filters.setSpacing(10)

        f_ic = QLabel()
        f_ic.setPixmap(fa_icon(ICONS["calendar"], color=T.TEXT_SECONDARY).pixmap(15, 15))
        filters.addWidget(f_ic)

        filters.addWidget(QLabel("Période :"))
        self.period_preset = QComboBox()
        self.period_preset.addItem("Aujourd'hui", "day")
        self.period_preset.addItem("Cette semaine", "week")
        self.period_preset.addItem("Ce mois (30j)", "month")
        self.period_preset.addItem("Cette année", "year")
        self.period_preset.addItem("Personnalisé", "custom")
        self.period_preset.setFixedWidth(145)
        self.period_preset.setStyleSheet(f"""
            QComboBox {{
                background: {T.BG_INPUT};
                border: 1px solid {_COL_BORDER};
                border-radius: 8px;
                padding: 5px 10px;
                color: {T.TEXT_PRIMARY};
                font-size: 13px;
                min-height: 32px;
            }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.period_preset.currentIndexChanged.connect(self._on_preset_changed)
        filters.addWidget(self.period_preset)

        filters.addWidget(QLabel("Du"))
        self.start = QDateEdit()
        self.start.setCalendarPopup(True)
        self.start.setDate(QDate.currentDate().addDays(-30))
        self.start.setStyleSheet(f"""
            QDateEdit {{
                background: {T.BG_INPUT};
                border: 1px solid {_COL_BORDER};
                border-radius: 8px;
                padding: 4px 8px;
                color: {T.TEXT_PRIMARY};
                font-size: 13px;
                min-height: 32px;
            }}
        """)
        filters.addWidget(self.start)

        filters.addWidget(QLabel("Au"))
        self.end = QDateEdit()
        self.end.setCalendarPopup(True)
        self.end.setDate(QDate.currentDate())
        self.end.setStyleSheet(f"""
            QDateEdit {{
                background: {T.BG_INPUT};
                border: 1px solid {_COL_BORDER};
                border-radius: 8px;
                padding: 4px 8px;
                color: {T.TEXT_PRIMARY};
                font-size: 13px;
                min-height: 32px;
            }}
        """)
        filters.addWidget(self.end)

        apply_btn = QPushButton("  Actualiser")
        apply_button_icon(apply_btn, ICONS["search"], color="#FFFFFF", size=14)
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T.PRIMARY};
                border: none;
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 700;
                min-height: 34px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: {T.HOVER}; }}
        """)
        apply_btn.clicked.connect(self.refresh)
        filters.addWidget(apply_btn)

        filters.addStretch()

        # Export buttons
        excel_btn = QPushButton("  Export Excel")
        apply_button_icon(excel_btn, ICONS["download"], color="#FFFFFF", size=14)
        excel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        excel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T.SUCCESS};
                border: none;
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 700;
                min-height: 34px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: #218838; }}
        """)
        excel_btn.clicked.connect(lambda: self._export("xlsx"))
        filters.addWidget(excel_btn)

        pdf_btn = QPushButton("  Export PDF")
        apply_button_icon(pdf_btn, ICONS["file"], color="#FFFFFF", size=14)
        pdf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pdf_btn.setStyleSheet(f"""
            QPushButton {{
                background: #DC3545;
                border: none;
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 700;
                min-height: 34px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: #C82333; }}
        """)
        pdf_btn.clicked.connect(lambda: self._export("pdf"))
        filters.addWidget(pdf_btn)

        filter_card.layout.addLayout(filters)
        lay.addWidget(filter_card)

        # ── KPIs
        kpis_layout = QHBoxLayout()
        kpis_layout.setSpacing(12)
        self.k_total   = kpi_card("Recettes Totales", "0 FC", ICONS["money"])
        self.k_billets = kpi_card("Billets Vendus", "0", ICONS["ventes"])
        self.k_bag     = kpi_card("Bagages Enregistrés", "0", ICONS["bagages"])
        self.k_tb      = kpi_card("Recettes Billets", "0 FC", ICONS["ventes"])
        self.k_lg      = kpi_card("Recettes Bagages", "0 FC", ICONS["bagages"])
        for k in (self.k_total, self.k_billets, self.k_bag, self.k_tb, self.k_lg):
            kpis_layout.addWidget(k)
        lay.addLayout(kpis_layout)

        # ── Charts Row 1
        charts1 = QHBoxLayout()
        charts1.setSpacing(12)

        c1 = Card(padding=12)
        c1.setMinimumHeight(320)
        self.line = ChartCanvas(width=5.5, height=2.8)
        c1.layout.addWidget(self.line)
        charts1.addWidget(c1, 3)

        c2 = Card(padding=12)
        c2.setMinimumHeight(320)
        self.donut = ChartCanvas(width=3.5, height=2.8)
        c2.layout.addWidget(self.donut)
        charts1.addWidget(c2, 2)
        lay.addLayout(charts1)

        # ── Charts Row 2
        c3 = Card(padding=12)
        c3.setMinimumHeight(300)
        self.bars = ChartCanvas(width=8, height=2.8)
        c3.layout.addWidget(self.bars)
        lay.addWidget(c3)

        # ── Table : Performance par trajet
        table_card = Card(padding=16)
        t_inner = QVBoxLayout()
        t_inner.setSpacing(10)

        t_title = QLabel("Performance par Trajet")
        t_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {T.PRIMARY_ALT};")
        t_inner.addWidget(t_title)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Trajet", "Billets Vendus", "Recettes Totales (FC)"])
        _apply_table_style(self.table, row_height=38)
        self.table.setMinimumHeight(200)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        t_inner.addWidget(self.table)
        table_card.layout.addLayout(t_inner)
        lay.addWidget(table_card)

        scroll.setWidget(body)
        outer.addWidget(scroll)

    def _on_preset_changed(self, index: int) -> None:
        key = self.period_preset.itemData(index)
        today = QDate.currentDate()

        if key == "day":
            self.start.setDate(today)
            self.end.setDate(today)
        elif key == "week":
            self.start.setDate(today.addDays(-7))
            self.end.setDate(today)
        elif key == "month":
            self.start.setDate(today.addDays(-30))
            self.end.setDate(today)
        elif key == "year":
            self.start.setDate(QDate(today.year(), 1, 1))
            self.end.setDate(today)
        elif key == "custom":
            pass

        self.refresh()

    def _range(self) -> tuple[date, date]:
        s = self.start.date()
        e = self.end.date()
        return date(s.year(), s.month(), s.day()), date(e.year(), e.month(), e.day())

    def refresh(self) -> None:
        start, end = self._range()
        if end < start:
            QMessageBox.warning(self, "Rapports", "La date de fin doit être supérieure ou égale à la date de début.")
            return

        days = (end - start).days + 1
        session = get_session()
        try:
            k = stats.period_kpis(session, start, end)
            self._last_kpis = k

            set_kpi(self.k_total,   format_fc(k["recettes_total"]))
            set_kpi(self.k_billets, str(k["nb_billets"]))
            set_kpi(self.k_bag,     str(k["nb_bagages"]))
            set_kpi(self.k_tb,      format_fc(k["recettes_billets"]))
            set_kpi(self.k_lg,      format_fc(k["recettes_bagages"]))

            chart_days = min(max(days, 1), 90)
            series = stats.revenue_by_day(session, chart_days, end=end)
            dates = [d for d, _ in series]
            vals  = [v for _, v in series]

            plot_line_revenue(self.line, dates, vals, title="Évolution des Revenus sur la Période")
            plot_donut(
                self.donut,
                ["Billets", "Bagages"],
                [k["recettes_billets"], k["recettes_bagages"]],
                title="Répartition des Recettes",
            )

            by_route = stats.sales_by_route(session, max(days, 1), limit=10, start=start, end=end)
            self._last_routes = by_route

            plot_bars(
                self.bars,
                [r[0][:18] for r in by_route],
                [float(r[2]) for r in by_route],
                title="Recettes par Trajet (Top 10)",
            )

            self.table.setRowCount(0)
            tot_tickets = 0
            tot_amount = 0.0

            for idx, (label, count, amount) in enumerate(by_route):
                cnt_val = int(count)
                amt_val = float(amount)
                tot_tickets += cnt_val
                tot_amount += amt_val

                row = self.table.rowCount()
                self.table.insertRow(row)

                it_lbl = QTableWidgetItem(f"  {label}")
                it_cnt = QTableWidgetItem(str(cnt_val))
                it_cnt.setTextAlignment(_ALIGN_CENTER)
                it_amt = QTableWidgetItem(format_fc(amt_val))
                it_amt.setTextAlignment(_ALIGN_RIGHT)

                f = it_amt.font()
                f.setBold(True)
                it_amt.setFont(f)
                it_amt.setForeground(QBrush(QColor(T.PRIMARY_ALT)))

                self.table.setItem(row, 0, it_lbl)
                self.table.setItem(row, 1, it_cnt)
                self.table.setItem(row, 2, it_amt)

                bg = QColor(_COL_ROW_EVEN if row % 2 == 1 else _COL_ROW_ODD)
                for col in range(3):
                    self.table.item(row, col).setBackground(QBrush(bg))

            # Total row
            if len(by_route) > 0:
                t_row = self.table.rowCount()
                self.table.insertRow(t_row)
                it_tlbl = QTableWidgetItem("  TOTAL TRAJETS")
                it_tcnt = QTableWidgetItem(str(tot_tickets))
                it_tcnt.setTextAlignment(_ALIGN_CENTER)
                it_tamt = QTableWidgetItem(format_fc(tot_amount))
                it_tamt.setTextAlignment(_ALIGN_RIGHT)

                for item in (it_tlbl, it_tcnt, it_tamt):
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                    item.setBackground(QBrush(QColor(_COL_TOTAL_BG)))

                it_tamt.setForeground(QBrush(QColor(T.PRIMARY_ALT)))

                self.table.setItem(t_row, 0, it_tlbl)
                self.table.setItem(t_row, 1, it_tcnt)
                self.table.setItem(t_row, 2, it_tamt)

            # Adapt height
            header_h = self.table.horizontalHeader().height()
            rows_h = sum(self.table.rowHeight(i) for i in range(self.table.rowCount()))
            self.table.setFixedHeight(min(header_h + rows_h + 4, 340))

        finally:
            session.close()

    def _export(self, kind: str) -> None:
        self.refresh()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        start, end = self._range()
        p_label = self.period_preset.currentText()
        k = self._last_kpis
        routes = self._last_routes

        if kind == "csv":
            path_str, _ = QFileDialog.getSaveFileName(
                self, "Export CSV", f"rapport_{stamp}.csv", "Fichiers CSV (*.csv)"
            )
            if not path_str:
                return
            path = Path(path_str)
            path.parent.mkdir(parents=True, exist_ok=True)
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
            QMessageBox.information(self, "Export réussi", f"✅  Fichier CSV enregistré :\n\n{path_str}")

        elif kind == "xlsx":
            path_str, _ = QFileDialog.getSaveFileName(
                self, "Export Excel", f"rapport_activite_{stamp}.xlsx", "Fichiers Excel (*.xlsx)"
            )
            if not path_str:
                return
            try:
                export_service.export_activity_report_excel(k, routes, start, end, Path(path_str), period_label=p_label)
                QMessageBox.information(self, "Export réussi", f"✅  Fichier Excel enregistré :\n\n{path_str}")
            except Exception as e:
                QMessageBox.warning(self, "Erreur d'export", f"Erreur lors de l'export :\n{str(e)}")

        elif kind == "pdf":
            path_str, _ = QFileDialog.getSaveFileName(
                self, "Export PDF", f"rapport_activite_{stamp}.pdf", "Fichiers PDF (*.pdf)"
            )
            if not path_str:
                return
            try:
                export_service.export_activity_report_pdf(k, routes, start, end, Path(path_str), period_label=p_label)
                QMessageBox.information(self, "Export réussi", f"✅  Rapport PDF enregistré :\n\n{path_str}")
            except Exception as e:
                QMessageBox.warning(self, "Erreur d'export", f"Erreur lors de l'export :\n{str(e)}")
