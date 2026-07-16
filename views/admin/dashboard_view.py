"""Admin dashboard — KPIs + interactive matplotlib charts from MySQL."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QComboBox,
    QGridLayout,
    QCheckBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
)

from database.session import get_session
from resources import theme as T
from services import admin_stats_service as stats
from utils.formatters import format_fc
from utils.icons import ICONS
from views.admin.charts import (
    ChartCanvas,
    plot_line_revenue,
    plot_donut,
    plot_bars,
    plot_heatmap,
    plot_horizontal_bars,
)
from views.admin.widgets import kpi_card, set_kpi
from views.widgets.card import Card


class CashierRow(QWidget):
    def __init__(self, name: str, amount: str, count: int, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setSpacing(10)

        # Initials circle avatar
        initials = "".join([p[0] for p in name.split()[:2]]).upper() or "?"
        avatar = QLabel(initials)
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            f"""
            background-color: {T.PRIMARY}22;
            color: {T.PRIMARY};
            border-radius: 16px;
            font-size: 12px;
            font-weight: bold;
            """
        )
        layout.addWidget(avatar)

        # Details: Name & tickets count
        details = QVBoxLayout()
        details.setSpacing(2)
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {T.TEXT_PRIMARY};")
        count_lbl = QLabel(f"{count} billet{'s' if count > 1 else ''}")
        count_lbl.setStyleSheet(f"font-size: 11px; color: {T.TEXT_SECONDARY};")
        details.addWidget(name_lbl)
        details.addWidget(count_lbl)
        layout.addLayout(details)

        layout.addStretch()

        # Amount
        amount_lbl = QLabel(amount)
        amount_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {T.PRIMARY_ALT};")
        layout.addWidget(amount_lbl)


class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

        # Setup Auto-Refresh QTimer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.toggle_auto_refresh()

        # Initial load
        self.refresh()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

        # Keep a reference to the body widget for PNG export grab
        self.body_widget = QWidget()
        lay = QVBoxLayout(self.body_widget)
        lay.setSpacing(14)
        lay.setContentsMargins(0, 0, 4, 0)

        # Header controls
        head = QHBoxLayout()
        title = QLabel("Tableau de bord")
        title.setStyleSheet(
            f"color:{T.PRIMARY_ALT}; font-size:{T.SIZE_CARD_TITLE}px; font-weight:700;"
        )
        head.addWidget(title)
        head.addStretch()

        # Auto-Refresh controls
        head.addWidget(QLabel("Rafraîchissement :"))
        self.auto_refresh_chk = QCheckBox("Activer")
        self.auto_refresh_chk.setChecked(True)
        self.auto_refresh_chk.toggled.connect(self.toggle_auto_refresh)
        head.addWidget(self.auto_refresh_chk)

        self.refresh_interval = QComboBox()
        self.refresh_interval.addItem("30 secondes", 30)
        self.refresh_interval.addItem("1 minute", 60)
        self.refresh_interval.addItem("5 minutes", 300)
        self.refresh_interval.setCurrentIndex(1)
        self.refresh_interval.currentIndexChanged.connect(self.toggle_auto_refresh)
        head.addWidget(self.refresh_interval)

        # Simple period combo
        head.addWidget(QLabel(" Période :"))
        self.period = QComboBox()
        self.period.addItem("7 jours", 7)
        self.period.addItem("30 jours", 30)
        self.period.addItem("90 jours", 90)
        self.period.setCurrentIndex(1)
        self.period.currentIndexChanged.connect(lambda: self.refresh())
        head.addWidget(self.period)

        # Export PNG button
        self.export_btn = QPushButton("Exporter PNG")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_dashboard_png)
        head.addWidget(self.export_btn)

        lay.addLayout(head)

        # KPI Grid (2x5 Layout)
        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(10)
        self.k_recette = kpi_card("Recettes du jour", "0 FC", ICONS["money"])
        self.k_billets = kpi_card("Billets du jour", "0", ICONS["ventes"])
        self.k_hebdo = kpi_card("Recettes hebdo", "0 FC", ICONS["calendar"])
        self.k_annuel = kpi_card("Recettes annuel", "0 FC", ICONS["reports"])
        self.k_voy = kpi_card("Voyageurs", "0", ICONS["users"])
        self.k_bag = kpi_card("Bagages", "0", ICONS["bagages"])
        self.k_bus = kpi_card("Bus actifs", "0", ICONS["bus"])
        self.k_drv = kpi_card("Conducteurs", "0", ICONS["driver"])
        self.k_trj = kpi_card("Trajets", "0", ICONS["route"])
        self.k_cai = kpi_card("Caissiers", "0", ICONS["user"])

        # Row 0
        self.kpi_grid.addWidget(self.k_recette, 0, 0)
        self.kpi_grid.addWidget(self.k_billets, 0, 1)
        self.kpi_grid.addWidget(self.k_hebdo, 0, 2)
        self.kpi_grid.addWidget(self.k_annuel, 0, 3)
        self.kpi_grid.addWidget(self.k_voy, 0, 4)

        # Row 1
        self.kpi_grid.addWidget(self.k_bag, 1, 0)
        self.kpi_grid.addWidget(self.k_bus, 1, 1)
        self.kpi_grid.addWidget(self.k_drv, 1, 2)
        self.kpi_grid.addWidget(self.k_trj, 1, 3)
        self.kpi_grid.addWidget(self.k_cai, 1, 4)

        lay.addLayout(self.kpi_grid)

        # Charts Section
        # Row 1: Line Chart (Revenues) + Donut Chart (Breakdown)
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        c1 = Card(padding=10)
        c1.setMinimumHeight(320)
        self.line_chart = ChartCanvas(width=6, height=3)
        c1.layout.addWidget(self.line_chart)
        row1.addWidget(c1, 3)

        c2 = Card(padding=10)
        c2.setMinimumHeight(320)
        self.donut_chart = ChartCanvas(width=4, height=3)
        c2.layout.addWidget(self.donut_chart)
        row1.addWidget(c2, 2)
        lay.addLayout(row1)

        # Row 2: Bar Chart (Sales by route) + Heatmap
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        c3 = Card(padding=10)
        c3.setMinimumHeight(320)
        self.bar_chart = ChartCanvas(width=6, height=3)
        c3.layout.addWidget(self.bar_chart)
        row2.addWidget(c3, 3)

        c_heat = Card(padding=10)
        c_heat.setMinimumHeight(320)
        self.heatmap_chart = ChartCanvas(width=6, height=3)
        c_heat.layout.addWidget(self.heatmap_chart)
        row2.addWidget(c_heat, 3)
        lay.addLayout(row2)

        # Row 3: Cashiers Sales Horizontal Graph + Top cashiers list
        row3 = QHBoxLayout()
        row3.setSpacing(12)
        c_cai_graph = Card(padding=10)
        c_cai_graph.setMinimumHeight(320)
        self.cashiers_chart = ChartCanvas(width=6, height=3)
        c_cai_graph.layout.addWidget(self.cashiers_chart)
        row3.addWidget(c_cai_graph, 3)

        c4 = Card(padding=10)
        c4.setMinimumHeight(320)
        self.top_title = QLabel("Top caissiers (liste)")
        self.top_title.setStyleSheet(f"font-weight:700; font-size:14px; color:{T.TEXT_PRIMARY}; margin-bottom: 4px;")
        c4.layout.addWidget(self.top_title)
        self.top_box = QVBoxLayout()
        self.top_box.setSpacing(4)
        c4.layout.addLayout(self.top_box)
        row3.addWidget(c4, 2)
        lay.addLayout(row3)

        lay.addStretch()

        scroll.setWidget(self.body_widget)
        outer.addWidget(scroll)

    def toggle_auto_refresh(self) -> None:
        if self.auto_refresh_chk.isChecked():
            secs = self.refresh_interval.currentData()
            self.refresh_timer.start(secs * 1000)
        else:
            self.refresh_timer.stop()

    def refresh(self) -> None:
        days = self.period.currentData() or 30
        session = get_session()
        try:
            # 1) Set KPIs
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

            # 2) Revenues line chart
            series = stats.revenue_by_day(session, days)
            plot_line_revenue(
                self.line_chart,
                [d for d, _ in series],
                [v for _, v in series],
                title=f"Évolution des Revenus ({days} j)",
            )

            # 3) Donut Chart
            br = stats.revenue_breakdown(session, days)
            plot_donut(
                self.donut_chart,
                list(br.keys()),
                list(br.values()),
                title="Billets vs Bagages",
            )

            # 4) Heatmap Sales
            hdata = stats.sales_heatmap(session, days)
            plot_heatmap(self.heatmap_chart, hdata, title="Intensité des Ventes (heure × jour)")

            # 5) Sales by Route Chart
            by_route = stats.sales_by_route(session, days, limit=8)
            route_labels = [r[0][:18] for r in by_route]
            route_vals = [float(r[2]) for r in by_route]
            plot_bars(self.bar_chart, route_labels, route_vals, title="Recettes par trajet")

            # 6) Top Cashiers
            tops = stats.top_cashiers(session, days, limit=5)

            # Update Horizontal Chart
            cashier_names = [t[0][:15] for t in tops]
            cashier_sales = [float(t[1]) for t in tops]
            plot_horizontal_bars(self.cashiers_chart, cashier_names, cashier_sales, title="Performance des Caissiers (graphique)")

            # Update List widget
            while self.top_box.count():
                item = self.top_box.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            if not tops:
                empty = QLabel("Aucune vente sur la période.")
                empty.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-style: italic; padding: 10px;")
                self.top_box.addWidget(empty)
            for name, amount, count in tops:
                row = CashierRow(name, format_fc(amount), count)
                self.top_box.addWidget(row)
            self.top_box.addStretch()

        finally:
            session.close()

    def export_dashboard_png(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le tableau de bord",
            f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "Images (*.png)"
        )
        if not path:
            return

        pixmap = self.body_widget.grab()
        if pixmap.save(path, "PNG"):
            QMessageBox.information(self, "Export réussi", f"Le tableau de bord a été enregistré avec succès :\n{path}")
        else:
            QMessageBox.warning(self, "Échec de l'export", "Impossible d'enregistrer l'image du tableau de bord.")
