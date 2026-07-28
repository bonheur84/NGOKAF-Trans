"""Finance view — expense tracking, financial reports, and charts."""
from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QComboBox,
    QGridLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QDateEdit,
    QLineEdit,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QFrame,
    QDialog,
    QSizePolicy,
    QAbstractItemView,
)

from controllers.finances_controller import FinanceController
from resources import theme as T
from services import export_service
from utils.formatters import format_fc
from utils.icons import fa_icon, ICONS, apply_button_icon
from views.admin.widgets import kpi_card, set_kpi, delete_action_btn
from views.widgets.card import Card


# ─── Palette locale ────────────────────────────────────────────────────────────
_COL_HEADER_BG  = "#8C6A00"
_COL_HEADER_FG  = "#FFFFFF"
_COL_ROW_ODD    = "#FFFDF9"
_COL_ROW_EVEN   = "#FFF6E8"
_COL_BORDER     = "#E4D8C3"
_COL_TOTAL_BG   = "#F2EADF"
_COL_TOTAL_FG   = "#5A4100"
_COL_AMOUNT     = "#8C6A00"

_ALIGN_RIGHT  = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
_ALIGN_CENTER = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter
_ALIGN_LEFT   = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft


# ─── Style commun pour toutes les tables ──────────────────────────────────────
def _apply_table_style(table: QTableWidget, row_height: int = 38) -> None:
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
            padding: 10px 8px;
            border: none;
            border-right: 1px solid rgba(255,255,255,0.15);
        }}
        QHeaderView::section:last {{
            border-right: none;
        }}
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


def _set_row_color(table: QTableWidget, row: int, is_even: bool, is_total: bool = False) -> None:
    if is_total:
        bg, fg = QColor(_COL_TOTAL_BG), QColor(_COL_TOTAL_FG)
    else:
        bg, fg = QColor(_COL_ROW_EVEN if is_even else _COL_ROW_ODD), QColor(T.TEXT_PRIMARY)
    for col in range(table.columnCount()):
        item = table.item(row, col)
        if item:
            item.setBackground(QBrush(bg))
            item.setForeground(QBrush(fg))


def _make_item(text: str,
               align: Qt.AlignmentFlag = _ALIGN_LEFT,
               bold: bool = False,
               color: str | None = None) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setTextAlignment(align)
    if bold:
        f = QFont()
        f.setBold(True)
        item.setFont(f)
    if color:
        item.setForeground(QBrush(QColor(color)))
    return item


def _separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"background-color: {_COL_BORDER}; max-height: 1px;")
    return line


def _section_title(text: str, icon_key: str | None = None) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(8)
    if icon_key:
        ic = QLabel()
        ic.setPixmap(fa_icon(ICONS[icon_key], color=T.PRIMARY_ALT).pixmap(18, 18))
        row.addWidget(ic)
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {T.PRIMARY_ALT};")
    row.addWidget(lbl)
    row.addStretch()
    return row


def _green_btn(label: str, icon_key: str) -> QPushButton:
    btn = QPushButton(f"  {label}")
    apply_button_icon(btn, ICONS[icon_key], color="#FFFFFF", size=14)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {T.SUCCESS};
            border: none;
            border-radius: 8px;
            color: #FFFFFF;
            font-size: 12px;
            font-weight: 700;
            min-height: 32px;
            padding: 0 14px;
        }}
        QPushButton:hover {{ background: #218838; }}
    """)
    return btn


# ══════════════════════════════════════════════════════════════════════════════
#  Dialog Ajout de dépense
# ══════════════════════════════════════════════════════════════════════════════
class AddExpenseDialog(QDialog):
    """Dialog for adding a new expense."""

    def __init__(self, controller: FinanceController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Ajouter une dépense")
        self.setMinimumWidth(540)
        self.setStyleSheet(f"""
            QDialog {{ background: {T.BG_MAIN}; }}
            QLabel {{
                color: {T.TEXT_LABEL};
                font-size: 13px;
                font-weight: 600;
            }}
            QLineEdit, QDateEdit, QComboBox, QTextEdit {{
                background: {T.BG_INPUT};
                border: 1px solid {_COL_BORDER};
                border-radius: 8px;
                padding: 6px 10px;
                color: {T.TEXT_PRIMARY};
                font-size: 13px;
                min-height: 34px;
            }}
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus {{
                border: 1px solid {T.PRIMARY};
            }}
        """)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Titre du dialog
        title_row = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(fa_icon(ICONS["expense"], color=T.PRIMARY_ALT).pixmap(20, 20))
        title_row.addWidget(ic)
        title_lbl = QLabel("Nouvelle Dépense")
        title_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {T.PRIMARY_ALT};")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        layout.addLayout(title_row)
        layout.addWidget(_separator())

        def _row(label_text: str, widget) -> QHBoxLayout:
            h = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(165)
            h.addWidget(lbl)
            h.addWidget(widget)
            return h

        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        layout.addLayout(_row("Date de paiement :", self.date_edit))

        # Catégorie
        self.category_combo = QComboBox()
        for cat in self.controller.get_categories():
            self.category_combo.addItem(cat.replace("_", " ").title(), cat)
        layout.addLayout(_row("Catégorie :", self.category_combo))

        # Montant
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        layout.addLayout(_row("Montant (FC) :", self.amount_input))

        # Mode de paiement
        self.payment_combo = QComboBox()
        for mode in self.controller.get_payment_modes():
            self.payment_combo.addItem(mode.replace("_", " ").title(), mode)
        layout.addLayout(_row("Mode de paiement :", self.payment_combo))

        # Fournisseur
        self.supplier_input = QLineEdit()
        self.supplier_input.setPlaceholderText("Nom du fournisseur...")
        layout.addLayout(_row("Fournisseur :", self.supplier_input))

        # Pièce justificative — texte libre (ex: facture, reçu, bon de caisse...)
        self.attachment_input = QLineEdit()
        self.attachment_input.setPlaceholderText("ex: Facture, Reçu, Bon de caisse...")
        layout.addLayout(_row("Pièce justificative :", self.attachment_input))

        # Description
        layout.addWidget(QLabel("Description :"))
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Détails de la dépense...")
        layout.addWidget(self.description_input)

        layout.addWidget(_separator())

        # ── Boutons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T.BG_SELECTION};
                border: 1px solid {_COL_BORDER};
                border-radius: 8px;
                color: {T.TEXT_LABEL};
                font-size: 13px;
                font-weight: 600;
                min-width: 100px;
                min-height: 38px;
            }}
            QPushButton:hover {{ background: {_COL_BORDER}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton("  Enregistrer")
        apply_button_icon(ok_btn, ICONS["save"], color="#FFFFFF", size=15)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T.PRIMARY};
                border: none;
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 700;
                min-width: 130px;
                min-height: 38px;
            }}
            QPushButton:hover {{ background: {T.HOVER}; }}
        """)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self._accept)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    def _accept(self):
        try:
            montant = Decimal(self.amount_input.text() or "0")
            if montant <= 0:
                QMessageBox.warning(self, "Erreur", "Le montant doit être supérieur à 0")
                return

            date_paiement = self.date_edit.date().toPython()
            categorie     = self.category_combo.currentData()
            description   = self.description_input.toPlainText() or None
            mode_paiement = self.payment_combo.currentData()
            fournisseur   = self.supplier_input.text() or None
            piece_jointe  = self.attachment_input.text() or None

            from services.session_store import current_session
            created_by = current_session.user.id if (current_session and current_session.user and getattr(current_session.user, "id", None)) else None

            success, message, expense = self.controller.add_expense(
                date_paiement, categorie, montant, description,
                mode_paiement, fournisseur, piece_jointe, created_by
            )

            if success:
                QMessageBox.information(self, "Succès", message)
                self.accept()
            else:
                QMessageBox.warning(self, "Erreur", message)
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Montant invalide")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
#  Vue principale Finances
# ══════════════════════════════════════════════════════════════════════════════
class FinancesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = FinanceController()
        self._build()
        self.refresh()

    # ── Construction ─────────────────────────────────────────────────────────
    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setSpacing(16)
        lay.setContentsMargins(2, 4, 6, 8)

        lay.addLayout(self._build_header())
        lay.addLayout(self._build_kpi_grid())

        # ── Onglets (Vue d'ensemble + Dépenses uniquement) ────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {_COL_BORDER};
                border-radius: 10px;
                background: {T.BG_CARD};
            }}
            QTabBar::tab {{
                background: {T.BG_SELECTION};
                color: {T.TEXT_SECONDARY};
                font-size: 13px;
                font-weight: 600;
                padding: 10px 22px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {T.PRIMARY};
                color: #FFFFFF;
            }}
            QTabBar::tab:hover:!selected {{
                background: {_COL_BORDER};
                color: {T.TEXT_PRIMARY};
            }}
        """)

        self.tabs.addTab(self._build_overview_tab(), "  Vue d'ensemble  ")
        self.tabs.addTab(self._build_expenses_tab(), "  Dépenses  ")

        lay.addWidget(self.tabs)
        lay.addStretch()

        scroll.setWidget(body)
        outer.addWidget(scroll)

    # ── En-tête ───────────────────────────────────────────────────────────────
    def _build_header(self) -> QHBoxLayout:
        head = QHBoxLayout()
        head.setSpacing(10)

        ic = QLabel()
        ic.setPixmap(fa_icon(ICONS["money"], color=T.PRIMARY_ALT).pixmap(26, 26))
        head.addWidget(ic)

        title = QLabel("Gestion Financière")
        title.setStyleSheet(f"color:{T.PRIMARY_ALT}; font-size:{T.SIZE_CARD_TITLE}px; font-weight:700;")
        head.addWidget(title)
        head.addStretch()

        # Filtre période
        period_lbl = QLabel("Période :")
        period_lbl.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:13px;")
        head.addWidget(period_lbl)

        self.period_combo = QComboBox()
        self.period_combo.addItem("Aujourd'hui",  "day")
        self.period_combo.addItem("Cette semaine", "week")
        self.period_combo.addItem("Ce mois",       "month")
        self.period_combo.addItem("Cette année",   "year")
        self.period_combo.setCurrentIndex(2)
        self.period_combo.setFixedWidth(150)
        self.period_combo.setStyleSheet(f"""
            QComboBox {{
                background: {T.BG_INPUT};
                border: 1px solid {_COL_BORDER};
                border-radius: 8px;
                padding: 6px 10px;
                color: {T.TEXT_PRIMARY};
                font-size: 13px;
                min-height: 34px;
            }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.period_combo.currentIndexChanged.connect(self.refresh)
        head.addWidget(self.period_combo)

        # Nouvelle dépense
        add_btn = QPushButton("  Nouvelle Dépense")
        apply_button_icon(add_btn, ICONS["plus"], color="#FFFFFF", size=14)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T.PRIMARY};
                border: none;
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 700;
                min-height: 38px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background: {T.HOVER}; }}
        """)
        add_btn.clicked.connect(self._add_expense)
        head.addWidget(add_btn)

        return head

    # ── Grille KPI ────────────────────────────────────────────────────────────
    def _build_kpi_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(12)
        self.k_revenue  = kpi_card("Revenus Totaux", "0 FC", ICONS["money"])
        self.k_tickets  = kpi_card("Ventes Billets", "0 FC", ICONS["ventes"])
        self.k_luggage  = kpi_card("Ventes Bagages", "0 FC", ICONS["bagages"])
        self.k_expenses = kpi_card("Total Dépenses", "0 FC", ICONS["expense"])
        self.k_profit   = kpi_card("Bénéfice Net",   "0 FC", ICONS["trending_up"])
        grid.addWidget(self.k_revenue,  0, 0)
        grid.addWidget(self.k_tickets,  0, 1)
        grid.addWidget(self.k_luggage,  0, 2)
        grid.addWidget(self.k_expenses, 0, 3)
        grid.addWidget(self.k_profit,   0, 4)
        return grid

    # ══ Onglet Vue d'ensemble ═════════════════════════════════════════════════
    def _build_overview_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background: {T.BG_CARD};")
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── 1. Détail des Revenus ─────────────────────────────────────────────
        rev_card = Card(padding=16)
        rev_inner = QVBoxLayout()
        rev_inner.setSpacing(10)
        rev_inner.addLayout(_section_title("Détail des Revenus", "money"))

        self.revenue_table = QTableWidget()
        self.revenue_table.setColumnCount(3)
        self.revenue_table.setHorizontalHeaderLabels(["Source", "Quantité", "Montant (FC)"])
        _apply_table_style(self.revenue_table, row_height=44)
        hh = self.revenue_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.revenue_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        rev_inner.addWidget(self.revenue_table)

        rev_card.layout.addLayout(rev_inner)
        layout.addWidget(rev_card)

        # ── 2. Total des Dépenses par Catégorie ───────────────────────────────
        cat_card = Card(padding=16)
        cat_inner = QVBoxLayout()
        cat_inner.setSpacing(10)

        cat_title_row = _section_title("Total des Dépenses par Catégorie", "expense")
        # Bouton export dépenses dans le titre
        self._export_expenses_btn = _green_btn("Exporter Dépenses (Excel)", "download")
        self._export_expenses_btn.clicked.connect(self._export_expenses)
        cat_title_row.addWidget(self._export_expenses_btn)
        cat_inner.addLayout(cat_title_row)

        self.category_table = QTableWidget()
        self.category_table.setColumnCount(3)
        self.category_table.setHorizontalHeaderLabels(["Catégorie", "Nb. opérations", "Total (FC)"])
        _apply_table_style(self.category_table, row_height=40)
        hh2 = self.category_table.horizontalHeader()
        hh2.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh2.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh2.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.category_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        cat_inner.addWidget(self.category_table)

        cat_card.layout.addLayout(cat_inner)
        layout.addWidget(cat_card)

        # ── 3. Total Général (Revenus - Dépenses) ─────────────────────────────
        total_card = Card(padding=16)
        total_inner = QVBoxLayout()
        total_inner.setSpacing(10)

        total_title_row = _section_title("Total Général", "trending_up")
        # Bouton export rapport complet
        self._export_full_btn = _green_btn("Exporter Rapport Complet (Excel)", "file")
        self._export_full_btn.clicked.connect(self._export_full_report)
        total_title_row.addWidget(self._export_full_btn)
        total_inner.addLayout(total_title_row)

        self.total_table = QTableWidget()
        self.total_table.setColumnCount(3)
        self.total_table.setHorizontalHeaderLabels(["Description", "Montant (FC)", ""])
        _apply_table_style(self.total_table, row_height=44)
        hh3 = self.total_table.horizontalHeader()
        hh3.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh3.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh3.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.total_table.setColumnWidth(2, 0)
        self.total_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        total_inner.addWidget(self.total_table)

        total_card.layout.addLayout(total_inner)
        layout.addWidget(total_card)
        layout.addStretch()

        return tab

    # ══ Onglet Dépenses ═══════════════════════════════════════════════════════
    def _build_expenses_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background: {T.BG_CARD};")
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Barre de filtres
        filter_card = Card(padding=12)
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        ic = QLabel()
        ic.setPixmap(fa_icon("filter", color=T.TEXT_SECONDARY).pixmap(14, 14))
        filter_row.addWidget(ic)

        filter_lbl = QLabel("Filtrer par catégorie :")
        filter_lbl.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:13px; font-weight:600;")
        filter_row.addWidget(filter_lbl)

        self.category_filter = QComboBox()
        self.category_filter.addItem("Toutes les catégories", None)
        for cat in self.controller.get_categories():
            self.category_filter.addItem(cat.replace("_", " ").title(), cat)
        self.category_filter.setFixedWidth(210)
        self.category_filter.setStyleSheet(f"""
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
        self.category_filter.currentIndexChanged.connect(self._refresh_expenses_table)
        filter_row.addWidget(self.category_filter)
        filter_row.addStretch()

        filter_card.layout.addLayout(filter_row)
        layout.addWidget(filter_card)

        # ── Table des dépenses
        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(8)
        self.expenses_table.setHorizontalHeaderLabels([
            "Date", "Catégorie", "Description", "Montant (FC)",
            "Mode paiement", "Fournisseur", "Justificatif", "Action"
        ])
        _apply_table_style(self.expenses_table, row_height=40)
        hh = self.expenses_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.expenses_table)

        return tab

    # ── Refresh principal ─────────────────────────────────────────────────────
    def refresh(self) -> None:
        period = self.period_combo.currentData()
        summary = self.controller.get_financial_summary(period)
        revenue = summary["revenue"]

        set_kpi(self.k_revenue,  format_fc(revenue["total"]))
        set_kpi(self.k_tickets,  f"{format_fc(revenue['tickets']['amount'])} ({revenue['tickets']['count']})")
        set_kpi(self.k_luggage,  f"{format_fc(revenue['luggage']['amount'])} ({revenue['luggage']['count']})")
        set_kpi(self.k_expenses, format_fc(summary["expenses"]))

        profit = summary["profit"]
        profit_color = T.SUCCESS if profit >= 0 else T.DANGER
        self.k_profit.setStyleSheet(f"""
            background-color: {T.BG_CARD};
            border-radius: 12px;
            padding: 16px;
            border-left: 4px solid {profit_color};
        """)
        set_kpi(self.k_profit, format_fc(profit))

        self._refresh_revenue_table(revenue)
        self._refresh_category_totals_table(period)
        self._refresh_total_general_table(revenue, summary["expenses"], summary["profit"])
        self._refresh_expenses_table()

    # ── Table : Détail des revenus ────────────────────────────────────────────
    def _refresh_revenue_table(self, revenue: dict) -> None:
        tickets_amount = revenue["tickets"]["amount"]
        luggage_amount = revenue["luggage"]["amount"]
        total = revenue["total"]

        rows_data = [
            ("Ventes de billets", str(revenue["tickets"]["count"]), tickets_amount),
            ("Ventes de bagages", str(revenue["luggage"]["count"]), luggage_amount),
        ]

        self.revenue_table.setRowCount(len(rows_data) + 1)

        for row, (source, qty, amount) in enumerate(rows_data):
            self.revenue_table.setItem(row, 0, _make_item(f"  {source}"))
            self.revenue_table.setItem(row, 1, _make_item(qty, _ALIGN_CENTER))
            self.revenue_table.setItem(row, 2, _make_item(format_fc(amount), _ALIGN_RIGHT, color=_COL_AMOUNT))
            _set_row_color(self.revenue_table, row, row % 2 == 1)

        # Ligne total
        total_row = len(rows_data)
        total_qty = str(revenue["tickets"]["count"] + revenue["luggage"]["count"])
        self.revenue_table.setItem(total_row, 0, _make_item("  TOTAL REVENUS", bold=True))
        self.revenue_table.setItem(total_row, 1, _make_item(total_qty, _ALIGN_CENTER, bold=True))
        self.revenue_table.setItem(total_row, 2, _make_item(format_fc(total), _ALIGN_RIGHT, bold=True, color=T.PRIMARY_ALT))
        _set_row_color(self.revenue_table, total_row, False, is_total=True)

        header_h = self.revenue_table.horizontalHeader().height()
        rows_h = sum(self.revenue_table.rowHeight(i) for i in range(self.revenue_table.rowCount()))
        self.revenue_table.setFixedHeight(header_h + rows_h + 4)

    # ── Table : Total dépenses par catégorie ──────────────────────────────────
    def _refresh_category_totals_table(self, period: str) -> None:
        category_data = self.controller.get_expenses_by_category(period)
        sorted_cats = sorted(category_data.items(), key=lambda x: x[1], reverse=True)
        grand_total = sum(category_data.values())

        expenses_all = self.controller.get_expenses(period)
        count_by_cat: dict[str, int] = {}
        for exp in expenses_all:
            count_by_cat[exp.categorie] = count_by_cat.get(exp.categorie, 0) + 1

        n = len(sorted_cats)
        self.category_table.setRowCount(n + 1 if n > 0 else 1)

        if n == 0:
            self.category_table.setItem(0, 0, _make_item("Aucune dépense pour cette période", _ALIGN_CENTER))
            self.category_table.setItem(0, 1, _make_item(""))
            self.category_table.setItem(0, 2, _make_item(""))
            _set_row_color(self.category_table, 0, False)
            self.category_table.setFixedHeight(self.category_table.horizontalHeader().height() + 44)
            return

        for row, (category, total) in enumerate(sorted_cats):
            count = count_by_cat.get(category, 0)
            self.category_table.setItem(row, 0, _make_item(f"  {category.replace('_', ' ').title()}"))
            self.category_table.setItem(row, 1, _make_item(str(count), _ALIGN_CENTER))
            self.category_table.setItem(row, 2, _make_item(format_fc(total), _ALIGN_RIGHT, color=T.DANGER))
            _set_row_color(self.category_table, row, row % 2 == 1)

        total_row = n
        total_count = sum(count_by_cat.values())
        self.category_table.setItem(total_row, 0, _make_item("  TOTAL DÉPENSES", bold=True))
        self.category_table.setItem(total_row, 1, _make_item(str(total_count), _ALIGN_CENTER, bold=True))
        self.category_table.setItem(total_row, 2, _make_item(format_fc(grand_total), _ALIGN_RIGHT, bold=True, color=T.DANGER))
        _set_row_color(self.category_table, total_row, False, is_total=True)

        header_h = self.category_table.horizontalHeader().height()
        visible_rows = min(n + 1, 8)
        rows_h = sum(self.category_table.rowHeight(i) for i in range(visible_rows))
        self.category_table.setFixedHeight(header_h + rows_h + 4)

    # ── Table : Total Général (Revenus - Dépenses) ────────────────────────────
    def _refresh_total_general_table(self, revenue: dict, total_expenses, profit) -> None:
        """Table synthétique : revenus totaux, dépenses totales, bénéfice net."""
        rev_total = revenue["total"]
        rows = [
            ("Total Revenus",   rev_total,      _COL_AMOUNT,  False),
            ("Total Dépenses",  total_expenses, T.DANGER,     False),
            ("Bénéfice Net",    profit,         T.SUCCESS if profit >= 0 else T.DANGER, True),
        ]

        self.total_table.setRowCount(len(rows))

        for row, (label, value, color, is_total) in enumerate(rows):
            self.total_table.setItem(row, 0, _make_item(f"  {label}", bold=is_total))
            self.total_table.setItem(row, 1, _make_item(format_fc(value), _ALIGN_RIGHT, bold=is_total, color=color))
            self.total_table.setItem(row, 2, _make_item(""))
            _set_row_color(self.total_table, row, row % 2 == 1, is_total=is_total)

        header_h = self.total_table.horizontalHeader().height()
        rows_h = sum(self.total_table.rowHeight(i) for i in range(len(rows)))
        self.total_table.setFixedHeight(header_h + rows_h + 4)

    # ── Table : Liste des dépenses ────────────────────────────────────────────
    def _refresh_expenses_table(self) -> None:
        period   = self.period_combo.currentData()
        category = self.category_filter.currentData()
        expenses = self.controller.get_expenses(period, categorie=category)

        self.expenses_table.setRowCount(len(expenses))

        for row, exp in enumerate(expenses):
            self.expenses_table.setItem(row, 0, _make_item(exp.date_paiement.strftime("%d/%m/%Y"), _ALIGN_CENTER))
            self.expenses_table.setItem(row, 1, _make_item(exp.categorie.replace("_", " ").title()))
            self.expenses_table.setItem(row, 2, _make_item(exp.description or "—"))
            self.expenses_table.setItem(row, 3, _make_item(format_fc(exp.montant), _ALIGN_RIGHT, color=T.DANGER))
            self.expenses_table.setItem(row, 4, _make_item(exp.mode_paiement.replace("_", " ").title(), _ALIGN_CENTER))
            self.expenses_table.setItem(row, 5, _make_item(exp.fournisseur or "—"))
            self.expenses_table.setItem(row, 6, _make_item(exp.piece_jointe or "—"))
            _set_row_color(self.expenses_table, row, row % 2 == 1)

            del_btn = delete_action_btn("Suppr.")
            del_btn.clicked.connect(lambda checked, eid=exp.id: self._delete_expense(eid))
            self.expenses_table.setCellWidget(row, 7, del_btn)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _add_expense(self) -> None:
        dialog = AddExpenseDialog(self.controller, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _delete_expense(self, expense_id: int) -> None:
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer cette dépense ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.controller.delete_expense(expense_id)
            if success:
                QMessageBox.information(self, "Succès", message)
                self.refresh()
            else:
                QMessageBox.warning(self, "Erreur", message)

    # ── Exports ───────────────────────────────────────────────────────────────
    def _export_expenses(self) -> None:
        """Export les dépenses de la période courante en Excel."""
        period   = self.period_combo.currentData()
        cat_val  = getattr(self, "category_filter", None)
        cat      = cat_val.currentData() if cat_val else None
        expenses = self.controller.get_expenses(period, categorie=cat)

        if not expenses:
            QMessageBox.information(self, "Information", "Aucune dépense à exporter pour cette période.")
            return

        default_name = f"depenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Exporter les dépenses", default_name, "Fichiers Excel (*.xlsx)"
        )
        if not path_str:
            return
        try:
            export_service.export_expenses_excel(expenses, Path(path_str))
            QMessageBox.information(self, "Export réussi", f"Fichier enregistré :\n{path_str}")
        except Exception as e:
            QMessageBox.warning(self, "Erreur d'export", f"Erreur lors de l'export :\n{str(e)}")

    def _export_full_report(self) -> None:
        """Export le rapport complet (revenus + dépenses + total général) en un seul fichier Excel."""
        period       = self.period_combo.currentData()
        period_label = self.period_combo.currentText()
        summary      = self.controller.get_financial_summary(period)
        expenses     = self.controller.get_expenses(period)

        financial_data = {
            "period":   period_label,
            "revenue":  summary["revenue"],
            "expenses": summary["expenses"],
            "profit":   summary["profit"],
        }

        default_name = f"rapport_financier_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Exporter le rapport financier", default_name, "Fichiers Excel (*.xlsx)"
        )
        if not path_str:
            return
        try:
            export_service.export_complete_financial_report(financial_data, expenses, Path(path_str))
            QMessageBox.information(self, "Export réussi", f"Rapport enregistré :\n{path_str}")
        except Exception as e:
            QMessageBox.warning(self, "Erreur d'export", f"Erreur lors de l'export :\n{str(e)}")
