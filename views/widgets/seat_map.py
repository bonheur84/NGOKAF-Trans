"""Seat map 2-2 layout sized to the selected bus capacity."""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
)

from resources import theme as T


class SeatButton(QPushButton):
    def __init__(self, number: int, parent=None):
        super().__init__(str(number), parent)
        self.number = number
        self.state = "available"  # available | occupied | selected
        self.setFixedSize(T.SEA_SIZE, T.SEA_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply()

    def set_state(self, state: str) -> None:
        self.state = state
        self.setEnabled(state != "occupied")
        self._apply()

    def _apply(self) -> None:
        if self.state == "occupied":
            bg, fg, border = T.SEAT_OCCUPIED, T.TEXT_WHITE, T.SEAT_OCCUPIED
        elif self.state == "selected":
            bg, fg, border = T.SEAT_SELECTED, T.TEXT_WHITE, T.SEAT_SELECTED
        else:
            bg, fg, border = T.SEAT_AVAILABLE, T.TEXT_PRIMARY, T.BORDER
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: {T.RADIUS_SEAT}px;
                font-size: 13px;
                font-weight: 600;
            }}
            """
        )


class SeatMapWidget(QWidget):
    seat_selected = Signal(int)

    def __init__(self, capacity: int = 60, parent=None):
        super().__init__(parent)
        self.capacity = max(0, int(capacity))
        self.selected: int | None = None
        self.buttons: dict[int, SeatButton] = {}
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(8)
        self._build()

    def _build(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        inner = QFrame()
        inner.setStyleSheet(f"background-color: #FFFDF9; border-radius: 10px;")
        grid = QGridLayout(inner)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        # 2-2 layout: seats left 0,1 aisle, right 2,3 — sequential 1..60
        row = 0
        n = 1
        while n <= self.capacity:
            for col_map, col in [(0, 0), (1, 1), (2, 3), (3, 4)]:
                if n > self.capacity:
                    break
                btn = SeatButton(n)
                btn.clicked.connect(lambda checked=False, num=n: self._on_click(num))
                self.buttons[n] = btn
                grid.addWidget(btn, row, col)
                n += 1
            spacer = QWidget()
            spacer.setFixedWidth(12)
            grid.addWidget(spacer, row, 2)
            row += 1

        scroll.setWidget(inner)
        self._root.addWidget(scroll, 1)

        legend = QHBoxLayout()
        legend.setSpacing(12)
        for label, color, border in [
            ("DISPO", T.SEAT_AVAILABLE, T.BORDER),
            ("CHOISI", T.SEAT_SELECTED, T.SEAT_SELECTED),
            ("OCCUPÉ", T.SEAT_OCCUPIED, T.SEAT_OCCUPIED),
        ]:
            box = QFrame()
            box.setFixedSize(14, 14)
            box.setStyleSheet(
                f"background:{color}; border:1px solid {border}; border-radius:3px;"
            )
            legend.addWidget(box)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:#4A3A1B; font-size:11px; font-weight:700;")
            legend.addWidget(lbl)
        legend.addStretch()
        self._root.addLayout(legend)

        sel = QFrame()
        sel.setStyleSheet(
            f"background:{T.BG_SELECTION}; border-radius:10px; padding:4px;"
        )
        sel_l = QHBoxLayout(sel)
        sel_l.setContentsMargins(10, 6, 10, 6)
        t = QLabel("Siège sélectionné :")
        t.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:13px;")
        self.sel_value = QLabel("--")
        self.sel_value.setStyleSheet(
            f"color:{T.PRIMARY_ALT}; font-size:20px; font-weight:700;"
        )
        sel_l.addWidget(t)
        sel_l.addStretch()
        sel_l.addWidget(self.sel_value)
        self._root.addWidget(sel)

    def set_capacity(self, capacity: int) -> None:
        """Rebuild the map so it contains exactly the bus's seats."""
        capacity = max(0, int(capacity or 0))
        if capacity == self.capacity:
            self.clear_selection()
            return

        self.clear_selection()
        while self._root.count():
            item = self._root.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self._delete_layout(child_layout)

        self.capacity = capacity
        self.buttons.clear()
        self._build()

    @staticmethod
    def _delete_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                SeatMapWidget._delete_layout(child_layout)
        layout.deleteLater()

    def _on_click(self, number: int) -> None:
        btn = self.buttons.get(number)
        if not btn or btn.state == "occupied":
            return
        if self.selected is not None and self.selected in self.buttons:
            prev = self.buttons[self.selected]
            if prev.state == "selected":
                prev.set_state("available")
        self.selected = number
        btn.set_state("selected")
        self.sel_value.setText(str(number))
        self.seat_selected.emit(number)

    def set_occupied(self, seats: set[int]) -> None:
        for num, btn in self.buttons.items():
            if num in seats:
                btn.set_state("occupied")
            elif self.selected == num:
                btn.set_state("selected")
            else:
                btn.set_state("available")
        if self.selected in seats:
            self.selected = None
            self.sel_value.setText("--")

    def clear_selection(self) -> None:
        if self.selected and self.selected in self.buttons:
            if self.buttons[self.selected].state != "occupied":
                self.buttons[self.selected].set_state("available")
        self.selected = None
        self.sel_value.setText("--")
