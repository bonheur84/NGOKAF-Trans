"""Shared admin UI helpers."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QHeaderView,
    QAbstractItemView,
)

from resources import theme as T
from utils.icons import fa_icon, ICONS, apply_button_icon
from views.widgets.card import Card


def style_table(table: QTableWidget) -> None:
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(36)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.setShowGrid(False)
    table.setStyleSheet(
        f"""
        QTableWidget {{
            background: {T.BG_CARD};
            border: 1px solid {T.BORDER};
            border-radius: 10px;
            gridline-color: transparent;
        }}
        QHeaderView::section {{
            background: {T.BG_SELECTION};
            color: {T.TEXT_LABEL};
            font-weight: 600;
            padding: 8px;
            border: none;
            border-bottom: 1px solid {T.BORDER};
        }}
        QTableWidget::item {{
            padding: 6px;
            border-bottom: 1px solid {T.BORDER};
        }}
        QTableWidget::item:selected {{
            background: {T.BG_SELECTION};
            color: {T.TEXT_PRIMARY};
        }}
        """
    )


def kpi_card(title: str, value: str, icon_name: str | None = None) -> Card:
    card = Card(padding=14)
    card.setMinimumHeight(88)
    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:12px; font-weight:600;")
    val = QLabel(value)
    val.setObjectName("kpiValue")
    val.setStyleSheet(
        f"color:{T.PRIMARY_ALT}; font-size:22px; font-weight:700;"
    )
    top = QHBoxLayout()
    top.addWidget(title_lbl, 1)
    if icon_name:
        resolved_icon = ICONS.get(icon_name, icon_name)
        ic = QLabel()
        ic.setPixmap(fa_icon(resolved_icon, color=T.PRIMARY_ALT).pixmap(20, 20))
        top.addWidget(ic)
    card.layout.addLayout(top)
    card.layout.addWidget(val)
    card._value_label = val  # type: ignore[attr-defined]
    return card


def set_kpi(card: Card, value: str) -> None:
    getattr(card, "_value_label").setText(value)


def page_toolbar(
    title: str,
    *,
    search_placeholder: str = "Rechercher…",
    on_search=None,
    add_label: str | None = "Ajouter",
    on_add=None,
) -> tuple[QHBoxLayout, QLineEdit | None, QPushButton | None]:
    row = QHBoxLayout()
    lbl = QLabel(title)
    lbl.setObjectName("cardTitle")
    lbl.setStyleSheet(
        f"color:{T.PRIMARY_ALT}; font-size:{T.SIZE_CARD_TITLE}px; font-weight:700;"
    )
    row.addWidget(lbl)
    row.addStretch()
    search = None
    if on_search is not None:
        search = QLineEdit()
        search.setPlaceholderText(search_placeholder)
        search.setFixedWidth(220)
        search.setClearButtonEnabled(True)
        search.textChanged.connect(on_search)
        row.addWidget(search)
    add_btn = None
    if on_add is not None and add_label:
        add_btn = QPushButton(f"  {add_label}")
        add_btn.setObjectName("primaryBtn")
        apply_button_icon(add_btn, ICONS["plus"], color="#FFFFFF", size=14)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(on_add)
        row.addWidget(add_btn)
    return row, search, add_btn


def status_badge(text: str, active: bool = True) -> QLabel:
    lbl = QLabel(text)
    bg = T.BADGE_ACTIVE if active else T.BADGE_DELIVERED
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(
        f"""
        background:{bg}; color:{T.TEXT_PRIMARY};
        border-radius:10px; padding:3px 10px; font-size:11px; font-weight:600;
        """
    )
    return lbl


def secondary_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setObjectName("secondaryBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def action_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setObjectName("actionBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def filter_bar() -> QFrame:
    f = QFrame()
    f.setStyleSheet(
        f"QFrame {{ background:{T.BG_CARD}; border-radius:10px; border:1px solid {T.BORDER}; }}"
    )
    return f


def edit_action_btn(text: str = "Édit.") -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(
        f"""
        QPushButton {{
            background-color: {T.PRIMARY}18;
            color: {T.PRIMARY_ALT};
            border: 1px solid {T.PRIMARY}55;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            padding: 2px 8px;
            min-height: 24px;
        }}
        QPushButton:hover {{
            background-color: {T.PRIMARY}33;
        }}
        """
    )
    return btn


def delete_action_btn(text: str = "Suppr.") -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(
        """
        QPushButton {
            background-color: #FEF2F2;
            color: #EF4444;
            border: 1px solid #FCA5A5;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            padding: 2px 8px;
            min-height: 24px;
        }
        QPushButton:hover {
            background-color: #FEE2E2;
        }
        """
    )
    return btn


def toggle_action_btn(text: str, active: bool = True) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    color = "#F97316" if active else "#10B981"
    bg = "#FFF7ED" if active else "#ECFDF5"
    border = "#FED7AA" if active else "#A7F3D0"
    hover = "#FFEDD5" if active else "#D1FAE5"
    btn.setStyleSheet(
        f"""
        QPushButton {{
            background-color: {bg};
            color: {color};
            border: 1px solid {border};
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            padding: 2px 8px;
            min-height: 24px;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
        """
    )
    return btn


def normal_action_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(
        f"""
        QPushButton {{
            background-color: {T.BG_CARD};
            color: {T.TEXT_PRIMARY};
            border: 1px solid {T.BORDER};
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            padding: 2px 8px;
            min-height: 24px;
        }}
        QPushButton:hover {{
            background-color: {T.BG_INPUT};
        }}
        """
    )
    return btn

