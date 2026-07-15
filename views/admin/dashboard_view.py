"""Admin dashboard — KPIs + matplotlib charts from MySQL."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QComboBox,
    QGridLayout,
)

from database.session import get_session
from resources import theme as T
from services import admin_stats_service as stats
from utils.formatters import format_fc
from utils.icons import ICONS
from views.admin.charts import ChartCanvas, plot_line_revenue, plot_donut, plot_bars
from views.admin.widgets import kpi_card, set_kpi
from views.widgets.card import Card


class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._period = 30
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setSpacing(14)
        lay.setContentsMargins(0, 0, 4, 0)

        head = QHBoxLayout()
        title = QLabel("Tableau de bord")
        title.setStyleSheet(
            f"color:{T.PRIMARY_ALT}; font-size:{T.SIZE_CARD_TITLE}px; font-weight:700;"
        )
        head.addWidget(title)
        head.addStretch()
        head.addWidget(QLabel("Période graphiques :"))
        self.period = QComboBox()
        self.period.addItem("7 jours", 7)
        self.period.addItem("30 jours", 30)
        self.period.setCurrentIndex(1)
        self.period.currentIndexChanged.connect(self.refresh)
        head.addWidget(self.period)
        lay.addLayout(head)

        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(10)
        self.k_recette = kpi_card("Recettes du jour", "0 FC", ICONS["money"])
        self.k_billets = kpi_card("Billets du jour", "0", ICONS["ventes"])
        self.k_hebdo = kpi_card("Recettes hebdo", "0 FC", ICONS["calendar"])
        self.k_annuel = kpi_card("Recettes annuel", "0 FC", ICONS["reports"])
        self.kpi_grid.addWidget(self.k_recette, 0, 0)
        self.kpi_grid.addWidget(self.k_billets, 0, 1)
        self.kpi_grid.addWidget(self.k_hebdo, 0, 2)
        self.kpi_grid.addWidget(self.k_annuel, 0, 3)

        self.k_voy = kpi_card("Voyageurs", "0", ICONS["users"])
        self.k_bag = kpi_card("Bagages", "0", ICONS["bagages"])
        self.k_bus = kpi_card("Bus actifs", "0", ICONS["bus"])
        self.k_drv = kpi_card("Conducteurs", "0", ICONS["driver"])
        self.k_trj = kpi_card("Trajets", "0", ICONS["route"])
        self.k_cai = kpi_card("Caissiers", "0", ICONS["user"])
        self.kpi_grid.addWidget(self.k_voy, 1, 0)
        self.kpi_grid.addWidget(self.k_bag, 1, 1)
        self.kpi_grid.addWidget(self.k_bus, 1, 2)
        self.kpi_grid.addWidget(self.k_drv, 1, 3)
        self.kpi_grid.addWidget(self.k_trj, 2, 0)
        self.kpi_grid.addWidget(self.k_cai, 2, 1)
        lay.addLayout(self.kpi_grid)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)
        c1 = Card(padding=10)
        self.line_chart = ChartCanvas(width=6, height=3)
        c1.layout.addWidget(self.line_chart)
        charts_row.addWidget(c1, 3)

        c2 = Card(padding=10)
        self.donut_chart = ChartCanvas(width=4, height=3)
        c2.layout.addWidget(self.donut_chart)
        charts_row.addWidget(c2, 2)
        lay.addLayout(charts_row)

        charts_row2 = QHBoxLayout()
        charts_row2.setSpacing(12)
        c3 = Card(padding=10)
        self.bar_chart = ChartCanvas(width=6, height=3)
        c3.layout.addWidget(self.bar_chart)
        charts_row2.addWidget(c3, 3)

        c4 = Card(padding=10)
        self.top_title = QLabel("Top caissiers")
        self.top_title.setStyleSheet(f"font-weight:700; color:{T.TEXT_PRIMARY};")
        c4.layout.addWidget(self.top_title)
        self.top_box = QVBoxLayout()
        c4.layout.addLayout(self.top_box)
        charts_row2.addWidget(c4, 2)
        lay.addLayout(charts_row2)
        lay.addStretch()

        scroll.setWidget(body)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        days = self.period.currentData() or 30
        session = get_session()
        try:
            k = stats.dashboard_kpis(session)
            set_kpi(self.k_recette, format_fc(k["recettes_jour"]))
            set_kpi(self.k_billets, str(k["billets_jour"]))
            set_kpi(self.k_hebdo, format_fc(k["recettes_hebdo"]))
            set_kpi(self.k_annuel, format_fc(k["recettes_annuel"]))
            set_kpi(self.k_voy, str(k["voyageurs"]))
            set_kpi(self.k_bag, str(k["bagages"]))
            set_kpi(self.k_bus, str(k["bus"]))
            set_kpi(self.k_drv, str(k["conducteurs"]))
            set_kpi(self.k_trj, str(k["trajets"]))
            set_kpi(self.k_cai, str(k["caissiers"]))

            series = stats.revenue_by_day(session, days)
            plot_line_revenue(
                self.line_chart,
                [d for d, _ in series],
                [v for _, v in series],
                title=f"Revenus ({days} j)",
            )
            br = stats.revenue_breakdown(session, days)
            plot_donut(
                self.donut_chart,
                list(br.keys()),
                list(br.values()),
                title="Billets / Bagages",
            )
            by_route = stats.sales_by_route(session, days)
            labels = [r[0][:18] for r in by_route]
            vals = [float(r[2]) for r in by_route]
            plot_bars(self.bar_chart, labels, vals, title="Recettes par trajet")

            while self.top_box.count():
                item = self.top_box.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            tops = stats.top_cashiers(session, days)
            if not tops:
                empty = QLabel("Aucune vente sur la période.")
                empty.setStyleSheet(f"color:{T.TEXT_SECONDARY};")
                self.top_box.addWidget(empty)
            for name, amount, count in tops:
                row = QLabel(f"{name}  —  {format_fc(amount)}  ({count} billets)")
                row.setStyleSheet(f"color:{T.TEXT_PRIMARY}; padding:4px 0;")
                self.top_box.addWidget(row)
            self.top_box.addStretch()
        finally:
            session.close()
