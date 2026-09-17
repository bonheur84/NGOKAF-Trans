"""Polished loading states shared by the NGOKAF desktop views."""
from __future__ import annotations

from math import cos, pi, sin

from PySide6.QtCore import QObject, QEvent, QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from resources import theme as T


class OrbitSpinner(QWidget):
    """A compact orbit spinner with a soft fading trail."""

    def __init__(self, parent=None, size: int = 40) -> None:
        super().__init__(parent)
        self._step = 0
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.setInterval(65)
        self._timer.timeout.connect(self._advance)

    def start(self) -> None:
        self._timer.start()
        self.show()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _advance(self) -> None:
        self._step = (self._step + 1) % 12
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = min(self.width(), self.height()) * 0.31
        dot_radius = max(2.0, self.width() * 0.075)
        base = QColor(T.PRIMARY_ALT)
        painter.setPen(Qt.PenStyle.NoPen)
        for index in range(12):
            distance = (index - self._step) % 12
            alpha = max(35, 255 - distance * 19)
            color = QColor(base)
            color.setAlpha(alpha)
            painter.setBrush(color)
            angle = (index / 12) * 2 * pi - pi / 2
            point = QPointF(center.x() + cos(angle) * radius, center.y() + sin(angle) * radius)
            painter.drawEllipse(point, dot_radius, dot_radius)


class LoadingOverlay(QWidget):
    """Non-intrusive overlay used while a view reloads its data."""

    def __init__(self, parent: QWidget, message: str = "Chargement des données…") -> None:
        super().__init__(parent)
        self._parent = parent
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(248, 242, 233, 185);")
        self._parent.installEventFilter(self)

        panel = QFrame(self)
        panel.setStyleSheet(
            f"background:{T.BG_CARD}; border:1px solid {T.BORDER}; "
            f"border-radius:14px;"
        )
        panel.setFixedWidth(230)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 18, 24, 18)
        panel_layout.setSpacing(9)

        self.spinner = OrbitSpinner(panel, 38)
        spinner_row = QHBoxLayout()
        spinner_row.addStretch()
        spinner_row.addWidget(self.spinner)
        spinner_row.addStretch()
        panel_layout.addLayout(spinner_row)

        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet(
            f"font-size:13px; font-weight:600; color:{T.TEXT_PRIMARY};"
        )
        panel_layout.addWidget(self.message_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(panel)
        row.addStretch()
        layout.addLayout(row)
        layout.addStretch()
        self.hide()

    def eventFilter(self, watched, event):  # noqa: N802 - Qt API
        if watched is self._parent and event.type() in (QEvent.Type.Resize, QEvent.Type.Move):
            self.setGeometry(self._parent.rect())
        return super().eventFilter(watched, event)

    def show_loading(self, message: str | None = None) -> None:
        if message:
            self.message_label.setText(message)
        self.setGeometry(self._parent.rect())
        self.spinner.start()
        self.raise_()
        self.show()

    def hide_loading(self) -> None:
        self.spinner.stop()
        self.hide()


class TableSkeleton(QObject):
    """Animated placeholder rows for a QTableWidget during data refreshes."""

    def __init__(self, table: QTableWidget, rows: int = 5) -> None:
        super().__init__(table)
        self.table = table
        self.rows = rows
        self._phase = 0
        self._timer = QTimer(self)
        self._timer.setInterval(110)
        self._timer.timeout.connect(self._shimmer)

    def show(self) -> None:
        self.table.clearContents()
        self.table.setRowCount(self.rows)
        for row in range(self.rows):
            self.table.setRowHeight(row, 42)
            for column in range(self.table.columnCount()):
                item = QTableWidgetItem("")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.table.setItem(row, column, item)
        self._phase = 0
        self._paint()
        self._timer.start()

    def hide(self) -> None:
        self._timer.stop()

    def _shimmer(self) -> None:
        self._phase = (self._phase + 1) % 8
        self._paint()

    def _paint(self) -> None:
        for row in range(self.table.rowCount()):
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                if item is None:
                    continue
                wave = (row + column + self._phase) % 8
                color = QColor("#EEE3D3" if wave in (0, 1) else "#F7EFE4")
                item.setBackground(color)

