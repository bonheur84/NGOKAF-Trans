"""Bus status widget — real-time fill progress bars for active routes."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QFrame,
    QScrollArea,
)

from database.session import get_session
from resources import theme as T


from utils.icons import fa_icon

class BusStatusWidget(QWidget):
    """Compact panel showing fill percentage for each active bus/route today."""

    REFRESH_INTERVAL_MS = 30_000  # 30 secondes

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(self.REFRESH_INTERVAL_MS)
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        title_box = QHBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(6)

        bus_icon_lbl = QLabel()
        bus_icon_lbl.setPixmap(fa_icon("bus", color=T.PRIMARY_ALT).pixmap(14, 14))
        title_box.addWidget(bus_icon_lbl)

        title = QLabel("État des Bus")
        title.setStyleSheet(
            f"color:{T.PRIMARY_ALT}; font-size:12px; font-weight:700;"
        )
        title_box.addWidget(title)
        title_box.addStretch()
        root.addLayout(title_box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none; background:transparent;}")

        self._container = QWidget()
        self._container.setStyleSheet("background:transparent;")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._layout.addStretch()

        scroll.setWidget(self._container)
        root.addWidget(scroll, 1)

    def refresh(self) -> None:
        """Reload bus occupation data and redraw all progress rows."""
        # Clear existing rows (keep the stretch at the end)
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        session = get_session()
        try:
            from models.route import Route
            from models.bus import Bus
            from models.ticket import Ticket
            from services.agency_context import current_agency_id
            from sqlalchemy.orm import joinedload

            aid = current_agency_id()
            today = date.today()

            q = (
                session.query(Route)
                .options(joinedload(Route.bus))
                .filter(Route.statut == "actif")
            )
            if aid:
                q = q.filter(Route.agency_id == aid)
            routes = q.all()

            if not routes:
                empty = QLabel("Aucun trajet actif")
                empty.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:11px;")
                self._layout.insertWidget(0, empty)
                return

            for route in routes:
                bus = route.bus
                if not bus:
                    continue

                # Count sold tickets for today
                sold = (
                    session.query(Ticket)
                    .filter(
                        Ticket.bus_id == bus.id,
                        Ticket.route_id == route.id,
                        Ticket.travel_date == today,
                        Ticket.statut == "vendu",
                    )
                    .count()
                )
                capacity = bus.capacite or 1
                pct = int(sold / capacity * 100)
                remaining = max(0, capacity - sold)

                row = self._make_row(bus.code, route.short_label, sold, capacity, pct, remaining)
                self._layout.insertWidget(self._layout.count() - 1, row)

        except Exception:
            pass
        finally:
            session.close()

    def _make_row(
        self,
        bus_code: str,
        route_label: str,
        sold: int,
        capacity: int,
        pct: int,
        remaining: int,
    ) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame{{background:{T.BG_CARD}; border-radius:8px; "
            f"border:1px solid {T.BORDER}; padding:4px 8px;}}"
        )
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(6, 4, 6, 4)
        fl.setSpacing(3)

        # Top row: bus code + seat counts
        top = QHBoxLayout()
        top.setSpacing(4)

        code_lbl = QLabel(f"<b>{bus_code}</b>")
        code_lbl.setStyleSheet(f"color:{T.TEXT_PRIMARY}; font-size:11px;")
        route_lbl = QLabel(route_label)
        route_lbl.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:10px;")
        top.addWidget(code_lbl)
        top.addWidget(route_lbl)
        top.addStretch()

        # Colour indicator based on fill level
        if pct >= 100:
            pct_color = "#EF5350"   # red — full
            seats_text = "COMPLET"
        elif pct >= 80:
            pct_color = "#FF9800"   # orange — almost full
            seats_text = f"{remaining} siège{'s' if remaining > 1 else ''} restant"
        elif pct >= 50:
            pct_color = "#FDD835"   # yellow — half
            seats_text = f"{remaining} restants"
        else:
            pct_color = "#66BB6A"   # green — plenty
            seats_text = f"{remaining} restants"

        pct_lbl = QLabel(f"{pct}%")
        pct_lbl.setStyleSheet(
            f"color:{pct_color}; font-size:11px; font-weight:700;"
        )
        seats_lbl = QLabel(seats_text)
        seats_lbl.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:10px;")
        top.addWidget(seats_lbl)
        top.addWidget(pct_lbl)
        fl.addLayout(top)

        # Progress bar
        bar = QProgressBar()
        bar.setRange(0, capacity)
        bar.setValue(sold)
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        bar.setStyleSheet(
            f"""
            QProgressBar {{
                background: {T.BG_INPUT};
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {pct_color};
                border-radius: 3px;
            }}
            """
        )
        fl.addWidget(bar)
        return frame
