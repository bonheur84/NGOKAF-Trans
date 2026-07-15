"""Reusable card frame."""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor

from resources import theme as T


class Card(QFrame):
    def __init__(self, parent=None, padding: int = T.PAD_CARD):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(
            f"""
            QFrame#card {{
                background-color: {T.BG_CARD};
                border-radius: {T.RADIUS_CARD}px;
                border: none;
            }}
            """
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(padding, padding, padding, padding)
        self.layout.setSpacing(T.GAP_FIELD)
