"""Bagages module — dashboard + registration form matching 10.png / 10.5.png."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFileDialog,
    QDoubleSpinBox,
    QScrollArea,
    QMenu,
)

from database.session import get_session
from resources import theme as T
from services.bus_service import list_active_routes
from services.luggage_service import (
    today_luggage_stats,
    list_luggage_for_bus,
    list_recent_luggage,
    register_luggage,
    update_luggage_status,
    reset_daily_luggage_links,
)
from services.session_store import current_session
from services.print_service import print_luggage
from services.export_service import (
    export_luggage_csv,
    export_luggage_excel,
    export_luggage_pdf,
)
from utils.formatters import format_fc
from utils.icons import fa_icon, apply_button_icon, ICONS
from views.widgets.card import Card


class BagagesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.routes = []
        self.selected_route_id: int | None = None
        self._items = []
        self._last_checked_date = date.today()
        self._build()
        self.refresh()

        # Timer checking for date change (midnight reset) every 30s
        self._timer = QTimer(self)
        self._timer.setInterval(30_000)
        self._timer.timeout.connect(self._check_midnight_reset)
        self._timer.start()

    def _check_midnight_reset(self) -> None:
        today = date.today()
        if today != self._last_checked_date:
            self._last_checked_date = today
            self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(T.GAP_COMPONENT)

        # Stats
        stats = QHBoxLayout()
        stats.setSpacing(T.GAP_COMPONENT)
        self.stat_count, self.stat_count_val, self.stat_count_sub = self._stat_card(
            "BAGAGES DU JOUR", "0", ""
        )
        self.stat_weight, self.stat_weight_val, self.stat_weight_sub = self._stat_card(
            "POIDS TOTAL CHARGÉ", "0 kg", ""
        )
        stats.addWidget(self.stat_count)
        stats.addWidget(self.stat_weight)
        root.addLayout(stats)

        body = QHBoxLayout()
        body.setSpacing(T.GAP_COMPONENT)

        # Left column
        left = QVBoxLayout()
        left.setSpacing(T.GAP_COMPONENT)

        trip_card = Card(padding=14)
        head = QHBoxLayout()
        ht = QLabel("Sélectionner un Trajet")
        ht.setStyleSheet(f"font-size:15px; font-weight:700; color:{T.TEXT_PRIMARY};")
        head.addWidget(ht)
        head.addStretch()
        trip_card.layout.addLayout(head)

        self.trip_list = QVBoxLayout()
        self.trip_list.setSpacing(6)
        trip_wrap = QWidget()
        trip_wrap.setLayout(self.trip_list)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(120)
        scroll.setWidget(trip_wrap)
        scroll.setStyleSheet("QScrollArea{border:none; background:transparent;}")
        trip_card.layout.addWidget(scroll)
        left.addWidget(trip_card)

        # --- Nouvel Enregistrement (scrollable, aéré) ---
        form_outer = Card(padding=0)
        form_outer.layout.setContentsMargins(0, 0, 0, 0)
        form_outer.layout.setSpacing(0)

        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.Shape.NoFrame)
        form_scroll.setStyleSheet("QScrollArea{background:transparent; border:none;}")
        form_inner = QWidget()
        form_inner.setStyleSheet(f"background:{T.BG_CARD};")
        form = QVBoxLayout(form_inner)
        form.setContentsMargins(20, 18, 20, 18)
        form.setSpacing(12)

        # Header with green + icon box
        ft_row = QHBoxLayout()
        ft_row.setSpacing(10)
        icon_box = QFrame()
        icon_box.setFixedSize(28, 28)
        icon_box.setStyleSheet(
            "background:#E8F5E9; border-radius:8px;"
        )
        ib_lay = QHBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ft_icon = QLabel()
        ft_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ft_icon.setPixmap(fa_icon(ICONS["plus"], color="#2E7D32").pixmap(QSize(14, 14)))
        ib_lay.addWidget(ft_icon)
        ft = QLabel("Nouvel Enregistrement")
        ft.setStyleSheet(f"font-size:18px; font-weight:700; color:{T.TEXT_PRIMARY};")
        ft_row.addWidget(icon_box)
        ft_row.addWidget(ft)
        ft_row.addStretch()
        form.addLayout(ft_row)
        form.addSpacing(4)

        field_ss = (
            f"background:{T.BG_INPUT}; border:1px solid {T.BORDER};"
            f"border-radius:{T.RADIUS_INPUT}px; padding:8px 12px; font-size:14px;"
            f"min-height:{T.FIELD_HEIGHT - 4}px;"
        )
        label_ss = f"color:{T.TEXT_LABEL}; font-size:13px; font-weight:600; margin-bottom:2px;"

        def labeled(label: str, widget: QWidget) -> QVBoxLayout:
            box = QVBoxLayout()
            box.setSpacing(6)
            lbl = QLabel(label)
            lbl.setStyleSheet(label_ss)
            box.addWidget(lbl)
            box.addWidget(widget)
            return box

        # Colis voyageur sur place : nom, téléphone, description, montant
        self.sender = QLineEdit()
        self.sender.setPlaceholderText("Ex: Jean Dupont")
        self.sender_phone = QLineEdit()
        self.sender_phone.setPlaceholderText("+237 ...")
        self.description = QTextEdit()
        self.description.setPlaceholderText(
            "Ex: Sac de voyage, valise, carton..."
        )
        self.description.setMinimumHeight(80)
        self.description.setMaximumHeight(110)

        for w in (self.sender, self.sender_phone):
            w.setStyleSheet(field_ss)
            w.setMinimumHeight(T.FIELD_HEIGHT)
        self.description.setStyleSheet(field_ss)

        form.addLayout(labeled("Nom du voyageur", self.sender))
        form.addLayout(labeled("Téléphone", self.sender_phone))
        form.addLayout(labeled("Description du colis", self.description))

        r3 = QHBoxLayout()
        r3.setSpacing(12)
        self.poids = QDoubleSpinBox()
        self.poids.setRange(0, 500)
        self.poids.setDecimals(1)
        self.poids.setSuffix("  KG")
        self.poids.setMinimumHeight(T.FIELD_HEIGHT)
        self.poids.setStyleSheet(field_ss)

        self.montant = QDoubleSpinBox()
        self.montant.setRange(0, 50_000_000)
        self.montant.setDecimals(0)
        self.montant.setSingleStep(500)
        self.montant.setSuffix("  FC")
        self.montant.setMinimumHeight(T.FIELD_HEIGHT)
        self.montant.setStyleSheet(field_ss)
        self.montant.valueChanged.connect(self._update_montant_display)

        r3.addLayout(labeled("Poids (kg)", self.poids), 1)
        r3.addLayout(labeled("Montant (estimation caissier)", self.montant), 1)
        form.addLayout(r3)

        cost = QFrame()
        cost.setStyleSheet(f"background:{T.BG_SELECTION}; border-radius:12px;")
        cl = QVBoxLayout(cost)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(6)
        tip = QLabel("Le caissier fixe lui-même le prix du bagage.")
        tip.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:12px;")
        cl.addWidget(tip)
        total_row = QHBoxLayout()
        tl = QLabel("TOTAL À PAYER")
        tl.setStyleSheet(f"font-weight:700; font-size:13px; color:{T.TEXT_PRIMARY};")
        self.total_lbl = QLabel("0 FC")
        self.total_lbl.setStyleSheet(
            f"color:{T.PRIMARY_ALT}; font-size:28px; font-weight:800;"
        )
        total_row.addWidget(tl)
        total_row.addStretch()
        total_row.addWidget(self.total_lbl)
        cl.addLayout(total_row)
        form.addWidget(cost)

        btn = QPushButton("Enregistrer & Imprimer Étiquette")
        btn.setMinimumHeight(46)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_button_icon(btn, ICONS["print"], color="#FFFFFF", size=16)
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background:{T.PRIMARY}; color:white; border:none;
                border-radius:{T.RADIUS_BUTTON}px; font-size:15px; font-weight:600;
                padding:10px 16px;
            }}
            QPushButton:hover {{ background:{T.HOVER}; }}
            """
        )
        btn.clicked.connect(self._save)
        form.addWidget(btn)
        form.addStretch()

        form_scroll.setWidget(form_inner)
        form_outer.layout.addWidget(form_scroll)
        left.addWidget(form_outer, 1)

        # Right table
        right = Card()
        rh = QHBoxLayout()
        self.table_title = QLabel("Bagages Récents")
        self.table_title.setStyleSheet(
            f"font-size:16px; font-weight:700; color:{T.TEXT_PRIMARY};"
        )
        rh.addWidget(self.table_title)
        rh.addStretch()
        export_btn = QPushButton("Exporter Manifeste")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_button_icon(export_btn, ICONS["upload"], color=T.TEXT_PRIMARY, size=14)
        export_btn.clicked.connect(self._export_menu)
        export_btn.setStyleSheet(
            f"QPushButton{{background:#EDE6DC;border:none;border-radius:10px;"
            f"padding:8px 14px;color:{T.TEXT_PRIMARY};font-weight:600;}}"
        )
        rh.addWidget(export_btn)
        right.layout.addLayout(rh)
        self.table_sub = QLabel("0 bagages enregistrés")
        self.table_sub.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:12px;")
        right.layout.addWidget(self.table_sub)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["ID BAGAGE", "VOYAGEUR", "POIDS", "STATUS", "ACTION"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(f"background:{T.BG_CARD}; border:none;")
        right.layout.addWidget(self.table, 1)

        body.addLayout(left, 5)
        body.addWidget(right, 6)
        root.addLayout(body, 1)
        self._update_montant_display()

    def _stat_card(self, label: str, value: str, sub: str) -> tuple:
        card = Card()
        l = QLabel(label)
        l.setStyleSheet(f"color:{T.TEXT_SECONDARY}; font-size:12px; font-weight:600;")
        v = QLabel(value)
        v.setStyleSheet(
            f"color:{T.PRIMARY_ALT}; font-size:26px; font-weight:800;"
        )
        s = QLabel(sub)
        s.setStyleSheet(f"color:{T.PRIMARY_ALT}; font-size:12px;")
        card.layout.addWidget(l)
        card.layout.addWidget(v)
        card.layout.addWidget(s)
        return card, v, s

    def refresh(self) -> None:
        session = get_session()
        try:
            reset_daily_luggage_links(session)
            stats = today_luggage_stats(session)
            self.stat_count_val.setText(str(stats["count"]))
            self.stat_count_sub.setText(stats["growth_label"])
            self.stat_weight_val.setText(
                f"{float(stats['weight']):,.0f} kg".replace(",", " ")
            )

            self.routes = list_active_routes(session)
            self._rebuild_trips()
            self._update_montant_display()
            self._reload_table(session)
        finally:
            session.close()

    def apply_search(self, text: str) -> None:
        return

    def _filter_trips(self, text: str = "") -> None:
        self._rebuild_trips()

    def _rebuild_trips(self, filter_text: str = "") -> None:
        while self.trip_list.count():
            item = self.trip_list.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for r in self.routes:
            label = (
                f"{r.short_label}  ·  Bus #{r.bus.code if r.bus else '?'}  ·  "
                f"{r.heure_depart.strftime('%H:%M')}"
            )
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            active = self.selected_route_id == r.id
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    text-align:left; padding:12px;
                    background:{"#F5E6B8" if active else T.BG_INPUT};
                    border:none; border-left:4px solid {"#8A6A00" if active else "transparent"};
                    border-radius:10px; font-size:14px; font-weight:600;
                }}
                """
            )
            btn.clicked.connect(lambda checked=False, rid=r.id: self._select_route(rid))
            self.trip_list.addWidget(btn)
        self.trip_list.addStretch()

    def _select_route(self, route_id: int) -> None:
        self.selected_route_id = route_id
        self._rebuild_trips()
        session = get_session()
        try:
            self._reload_table(session)
        finally:
            session.close()

    def _reload_table(self, session) -> None:
        route = next((r for r in self.routes if r.id == self.selected_route_id), None)
        if route:
            self._items = list_luggage_for_bus(session, route.bus_id)
            self.table_title.setText(f"Bagages Récents : Bus #{route.bus.code if route.bus else ''}")
        else:
            self._items = list_recent_luggage(session, 50)
            self.table_title.setText("Bagages Récents")
        self.table_sub.setText(f"{len(self._items)} bagages enregistrés pour ce trajet")
        self._fill_table()

    def _fill_table(self) -> None:
        self.table.setRowCount(0)
        status_map = {
            "enregistre": ("ENREGISTRÉ", T.BADGE_ACTIVE, "#2E2E2E"),
            "charge": ("CHARGÉ", T.BADGE_CHARGED, "#FFFFFF"),
            "livre": ("LIVRÉ", T.BADGE_DELIVERED, "#2E2E2E"),
            "annule": ("ANNULÉ", "#AA4444", "#FFFFFF"),
        }
        for item in self._items:
            r = self.table.rowCount()
            self.table.insertRow(r)
            id_item = QTableWidgetItem(f"#{item.numero}")
            id_item.setForeground(Qt.GlobalColor.darkYellow)
            id_item.setData(Qt.ItemDataRole.UserRole, item.id)
            self.table.setItem(r, 0, id_item)
            exp = QTableWidgetItem(f"{item.sender_name}\n{item.description[:40]}")
            self.table.setItem(r, 1, exp)
            self.table.setItem(r, 2, QTableWidgetItem(f"{float(item.poids):.1f} kg"))
            st_text, bg, fg = status_map.get(item.statut, (item.statut, "#ccc", "#000"))
            st = QTableWidgetItem(st_text)
            st.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 3, st)
            action = QPushButton()
            action.setIcon(fa_icon(ICONS["ellipsis"], color=T.TEXT_SECONDARY))
            action.setIconSize(QSize(16, 16))
            action.setFixedWidth(40)
            action.setStyleSheet("QPushButton{border:none;background:transparent;}")
            menu = QMenu(action)
            for lab, key in [
                ("Marquer Chargé", "charge"),
                ("Marquer Livré", "livre"),
                ("Annuler", "annule"),
                ("Réimprimer", "print"),
            ]:
                menu.addAction(lab, lambda k=key, i=item.id: self._action(i, k))
            action.setMenu(menu)
            self.table.setCellWidget(r, 4, action)

    def _update_montant_display(self) -> None:
        total = Decimal(str(int(self.montant.value())))
        self.total_lbl.setText(format_fc(total))

    def _action(self, luggage_id: int, key: str) -> None:
        session = get_session()
        try:
            user = current_session.user
            if key == "print":
                from models.luggage import Luggage
                from sqlalchemy.orm import joinedload

                item = (
                    session.query(Luggage)
                    .options(joinedload(Luggage.route), joinedload(Luggage.bus))
                    .filter_by(id=luggage_id)
                    .one()
                )
                path = print_luggage(item, user.id if user else None)
                QMessageBox.information(self, "Impression", str(path))
            else:
                update_luggage_status(session, luggage_id, key, user.id if user else None)
                self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _save(self) -> None:
        if not self.selected_route_id:
            QMessageBox.warning(self, "Bagages", "Sélectionnez un trajet.")
            return
        if not self.sender.text().strip():
            QMessageBox.warning(self, "Bagages", "Indiquez le nom du voyageur.")
            return
        if not self.sender_phone.text().strip():
            QMessageBox.warning(self, "Bagages", "Indiquez le téléphone du voyageur.")
            return
        if not self.description.toPlainText().strip():
            QMessageBox.warning(self, "Bagages", "Décrivez le colis.")
            return
        if self.montant.value() <= 0:
            QMessageBox.warning(self, "Bagages", "Saisissez le montant estimé.")
            return
        user = current_session.user
        if not user:
            return
        session = get_session()
        try:
            name = self.sender.text().strip()
            phone = self.sender_phone.text().strip()
            montant = Decimal(str(int(self.montant.value())))
            poids = Decimal(str(self.poids.value() or 0))
            # Destination = ville d'arrivée du trajet (colis voyageur sur place)
            route = next((r for r in self.routes if r.id == self.selected_route_id), None)
            dest = route.ville_arrivee if route else name
            item = register_luggage(
                session,
                sender_name=name,
                sender_phone=phone,
                recipient_name=dest,
                recipient_phone=phone,
                description=self.description.toPlainText().strip(),
                poids=poids if poids > 0 else Decimal("1"),
                valeur_declaree=None,
                route_id=self.selected_route_id,
                frais_base=montant,
                supplement_poids=Decimal("0"),
                total=montant,
                fragile=False,
                cashier=user,
            )
            from models.luggage import Luggage
            from sqlalchemy.orm import joinedload

            item = (
                session.query(Luggage)
                .options(joinedload(Luggage.route), joinedload(Luggage.bus))
                .filter_by(id=item.id)
                .one()
            )
            path = print_luggage(item, user.id)
            QMessageBox.information(
                self,
                "Bagage enregistré",
                f"{item.numero} enregistré.\n{path}",
            )
            self.sender.clear()
            self.sender_phone.clear()
            self.description.clear()
            self.poids.setValue(0)
            self.montant.setValue(0)
            self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _export_menu(self) -> None:
        if not self._items:
            QMessageBox.information(self, "Export", "Aucun bagage à exporter.")
            return
        path, filt = QFileDialog.getSaveFileName(
            self,
            "Exporter manifeste",
            "manifeste_bagages",
            "PDF (*.pdf);;Excel (*.xlsx);;CSV (*.csv)",
        )
        if not path:
            return
        p = Path(path)
        if filt.startswith("PDF") or p.suffix.lower() == ".pdf":
            export_luggage_pdf(self._items, p if p.suffix else p.with_suffix(".pdf"))
        elif filt.startswith("Excel") or p.suffix.lower() == ".xlsx":
            export_luggage_excel(self._items, p if p.suffix else p.with_suffix(".xlsx"))
        else:
            export_luggage_csv(self._items, p if p.suffix else p.with_suffix(".csv"))
        QMessageBox.information(self, "Export", f"Exporté : {path}")
