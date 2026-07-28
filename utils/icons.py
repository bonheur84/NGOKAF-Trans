"""Font Awesome 6 Solid icons via qtawesome."""
from __future__ import annotations

import qtawesome as qta
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QPushButton, QLabel, QToolButton
from PySide6.QtCore import QSize, Qt

from resources import theme as T


def fa_icon(name: str, color: str | None = None, scale: float = 1.0) -> QIcon:
    """
    Return a Font Awesome Solid QIcon.
    name: without 'fa-solid ' prefix, e.g. 'ticket', 'box', 'right-from-bracket'
    """
    color = color or T.PRIMARY_ALT
    # qtawesome FA6 solid uses 'fa6s.' prefix
    return qta.icon(f"fa6s.{name}", color=color, scale_factor=scale)


def icon_button(
    parent,
    name: str,
    *,
    color: str | None = None,
    size: int = 20,
    tooltip: str = "",
    checkable: bool = False,
) -> QToolButton:
    btn = QToolButton(parent)
    btn.setIcon(fa_icon(name, color=color or T.TEXT_PRIMARY))
    btn.setIconSize(QSize(size, size))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setAutoRaise(True)
    if tooltip:
        btn.setToolTip(tooltip)
    btn.setCheckable(checkable)
    btn.setStyleSheet("QToolButton { border: none; background: transparent; padding: 4px; }")
    return btn


def apply_button_icon(
    button: QPushButton,
    name: str,
    *,
    color: str = "#FFFFFF",
    size: int = 18,
) -> None:
    button.setIcon(fa_icon(name, color=color))
    button.setIconSize(QSize(size, size))


def label_with_icon(
    text: str,
    name: str,
    *,
    color: str | None = None,
    icon_size: int = 22,
    stylesheet: str = "",
) -> QLabel:
    """QLabel showing an FA solid icon as pixmap + text via rich layout alternative."""
    color = color or T.PRIMARY_ALT
    lbl = QLabel()
    icon = fa_icon(name, color=color)
    pix = icon.pixmap(QSize(icon_size, icon_size))
    lbl.setPixmap(pix)
    lbl.setToolTip(text)
    if stylesheet:
        lbl.setStyleSheet(stylesheet)
    return lbl


# Common icon names used in the app (FA6 solid)
ICONS = {
    "ventes": "ticket",
    "bagages": "box",
    "logout": "right-from-bracket",
    "user": "user",
    "user_plus": "user-plus",
    "users": "users",
    "lock": "lock",
    "eye": "eye",
    "eye_slash": "eye-slash",
    "login": "right-to-bracket",
    "print": "print",
    "seat": "chair",
    "bell": "bell",
    "search": "magnifying-glass",
    "plus": "plus",
    "bus": "bus",
    "route": "route",
    "dashboard": "chart-line",
    "reports": "chart-column",
    "settings": "gear",
    "driver": "id-card",
    "edit": "pen-to-square",
    "trash": "trash",
    "ellipsis": "ellipsis-vertical",
    "upload": "file-export",
    "calendar": "calendar-days",
    "check": "circle-check",
    "warning": "triangle-exclamation",
    "money": "coins",
    "save": "floppy-disk",
    "expense": "money-bill-wave",
    "trending_up": "arrow-trend-up",
    "download": "download",
    "file": "file",
    "chart": "chart-pie",
}
