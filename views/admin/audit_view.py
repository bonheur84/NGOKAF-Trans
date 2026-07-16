"""Admin Audit Logs view (Journal d'activité)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QComboBox,
    QHeaderView,
)

from database.session import get_session
from resources import theme as T
from services import audit_service
from views.admin.widgets import style_table, page_toolbar


class AuditView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        
        toolbar, self.search, _ = page_toolbar(
            "Journal d'activité",
            search_placeholder="Rechercher utilisateur, action, détails…",
            on_search=lambda _t: self.refresh(),
            add_label=None,
            on_add=None,
        )
        lay.addLayout(toolbar)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Action :"))
        self.action_filter = QComboBox()
        self.action_filter.addItem("Toutes", None)
        self.action_filter.addItem("Créations (create)", "create")
        self.action_filter.addItem("Modifications (update)", "update")
        self.action_filter.addItem("Suppressions (delete)", "delete")
        self.action_filter.addItem("Connexions (login)", "login")
        self.action_filter.addItem("Ventes (sell/create)", "sell")
        self.action_filter.addItem("Sauvegardes (backup)", "backup")
        self.action_filter.addItem("Restaurations (restore)", "restore")
        self.action_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.action_filter)
        filters.addStretch()
        lay.addLayout(filters)

        # 5 columns: Date & heure, Utilisateur, Action, Entité, Détails
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Date & Heure", "Utilisateur", "Action", "Entité", "Détails"]
        )
        style_table(self.table)
        
        # Sizing rules
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        
        lay.addWidget(self.table, 1)

    def refresh(self) -> None:
        session = get_session()
        try:
            logs = audit_service.get_audit_logs(
                session,
                search=self.search.text() if self.search else "",
                action=self.action_filter.currentData(),
            )
            self.table.setRowCount(0)
            for log, user in logs:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                date_str = log.created_at.strftime("%d/%m/%Y %H:%M:%S")
                user_str = user.full_name if user else f"Utilisateur ID {log.user_id}" if log.user_id else "Système"
                action_str = log.action
                entity_str = log.entity
                details_str = log.details or "—"
                
                # Create table items
                i_date = QTableWidgetItem(date_str)
                i_user = QTableWidgetItem(user_str)
                i_action = QTableWidgetItem(action_str)
                i_entity = QTableWidgetItem(entity_str)
                i_details = QTableWidgetItem(details_str)
                
                # Apply read-only styling
                for item in (i_date, i_user, i_action, i_entity, i_details):
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                self.table.setItem(row, 0, i_date)
                self.table.setItem(row, 1, i_user)
                self.table.setItem(row, 2, i_action)
                self.table.setItem(row, 3, i_entity)
                self.table.setItem(row, 4, i_details)
        finally:
            session.close()
