"""Admin shell — sidebar + header + stacked modules."""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QFrame,
    QMessageBox,
)

from config.settings import settings
from database.session import get_session
from resources import theme as T
from services import notification_service
from services.session_store import current_session
from utils.formatters import format_long_date
from utils.icons import fa_icon, ICONS
# Views are imported lazily inside _get_page() to avoid loading all modules at startup


class SidebarButton(QPushButton):
    def __init__(self, text: str, icon_name: str, parent=None):
        super().__init__(f"  {text}", parent)
        self._icon_name = icon_name
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setMinimumHeight(42)
        self.setIconSize(QSize(16, 16))
        self._apply(False)

    def set_active(self, active: bool) -> None:
        self.setChecked(active)
        self._apply(active)

    def _apply(self, active: bool) -> None:
        if active:
            self.setIcon(fa_icon(self._icon_name, color=T.PRIMARY_ALT))
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {T.BG_MENU_ACTIVE};
                    color: {T.PRIMARY_ALT};
                    border: none;
                    border-radius: 10px;
                    text-align: left;
                    padding-left: 14px;
                    font-size: 14px;
                    font-weight: 600;
                }}
                """
            )
        else:
            self.setIcon(fa_icon(self._icon_name, color="#FFFFFF"))
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    color: {T.TEXT_WHITE};
                    border: none;
                    border-radius: 10px;
                    text-align: left;
                    padding-left: 14px;
                    font-size: 14px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: rgba(255,255,255,0.06);
                }}
                """
            )


class AdminWindow(QMainWindow):
    logout_requested = Signal()

    MENU = [
        ("Tableau de bord", "dashboard", "Tableau de bord"),
        ("Trajets", "route", "Gestion des Trajets"),
        ("Bus", "bus", "Gestion des Bus"),
        ("Conducteurs", "driver", "Gestion des Conducteurs"),
        ("Utilisateurs", "users", "Gestion des Utilisateurs"),
        ("Finance", "expense", "Gestion Financière"),
        ("Rapports", "reports", "Rapports"),
        ("Paramètres", "settings", "Paramètres"),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{settings.AGENCY_NAME} — Administration")
        self.resize(1440, 900)
        self.setMinimumSize(1200, 720)
        self.setStyleSheet(f"QMainWindow {{ background: {T.BG_MAIN}; }}")
        self._nav_buttons: list[SidebarButton] = []
        # _page_cache holds already-instantiated page widgets by index
        self._page_cache: dict[int, QWidget] = {}
        self._build()
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()
        self._notif_timer = QTimer(self)
        self._notif_timer.timeout.connect(self._refresh_notif_badge)
        self._notif_timer.start(15000)
        self._navigate(0)

    def _build(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(T.SIDEBAR_WIDTH)
        sidebar.setStyleSheet(f"background-color: {T.BG_SIDEBAR};")
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(12, 16, 12, 12)
        sb.setSpacing(8)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background:white; border-radius:12px; padding:8px;")
        if settings.logo_path.exists():
            logo.setPixmap(
                QPixmap(str(settings.logo_path)).scaled(
                    110,
                    70,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        sb.addWidget(logo)

        brand = QLabel("Ngokaf Trans")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setStyleSheet(f"color:{T.PRIMARY_ALT}; font-size:17px; font-weight:700;")
        sb.addWidget(brand)
        admin_lbl = QLabel("ADMINISTRATION")
        admin_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        admin_lbl.setStyleSheet(
            f"color:{T.PRIMARY_ALT}; font-size:11px; letter-spacing:1px;"
        )
        sb.addWidget(admin_lbl)
        sb.addSpacing(18)

        for i, (label, icon_key, _title) in enumerate(self.MENU):
            btn = SidebarButton(label.upper(), ICONS[icon_key])
            btn.clicked.connect(lambda checked=False, idx=i: self._navigate(idx))
            sb.addWidget(btn)
            self._nav_buttons.append(btn)

        sb.addStretch()
        self.btn_logout = SidebarButton("DÉCONNEXION", ICONS["logout"])
        self.btn_logout.clicked.connect(self._logout)
        sb.addWidget(self.btn_logout)
        layout.addWidget(sidebar)

        main = QWidget()
        main.setObjectName("mainAdminArea")
        main.setStyleSheet(f"QWidget#mainAdminArea {{ background-color: {T.BG_MAIN}; }}")
        ml = QVBoxLayout(main)
        ml.setContentsMargins(T.MARGIN_MAIN, 10, T.MARGIN_MAIN, T.MARGIN_MAIN)
        ml.setSpacing(12)

        header = QHBoxLayout()
        self.page_title = QLabel("Tableau de bord")
        self.page_title.setStyleSheet(
            f"font-size:22px; font-weight:700; color:{T.TEXT_PRIMARY};"
        )
        header.addWidget(self.page_title)
        self.date_lbl = QLabel()
        self.date_lbl.setStyleSheet(
            f"font-size:14px; color:{T.TEXT_SECONDARY}; margin-left:16px;"
        )
        header.addWidget(self.date_lbl)
        header.addStretch()

        self.notif_btn = QPushButton()
        self.notif_btn.setIcon(fa_icon(ICONS["bell"], color=T.PRIMARY_ALT))
        self.notif_btn.setIconSize(QSize(18, 18))
        self.notif_btn.setFixedSize(34, 34)
        self.notif_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notif_btn.setStyleSheet("QPushButton{background:transparent;border:none;}")
        self.notif_btn.clicked.connect(self._show_notifications)
        header.addWidget(self.notif_btn)

        self.notif_dot = QLabel()
        self.notif_dot.setFixedSize(10, 10)
        self.notif_dot.setStyleSheet(
            f"background:{T.NOTIF_DOT}; border-radius:5px;"
        )
        self.notif_dot.hide()
        header.addWidget(self.notif_dot)

        user = current_session.user
        name = user.full_name if user else "—"
        user_box = QVBoxLayout()
        user_box.setSpacing(0)
        self.user_name = QLabel(name)
        self.user_name.setStyleSheet(
            f"font-size:{T.SIZE_CASHIER_NAME}px; font-weight:600; color:{T.TEXT_PRIMARY};"
        )
        self.user_role = QLabel("Administrateur")
        self.user_role.setStyleSheet(
            f"font-size:{T.SIZE_ROLE}px; color:{T.TEXT_SECONDARY};"
        )
        user_box.addWidget(self.user_name)
        user_box.addWidget(self.user_role)
        header.addLayout(user_box)

        avatar = QLabel()
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if user and user.photo_path:
            avatar.setPixmap(
                QPixmap(user.photo_path).scaled(
                    40,
                    40,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            initials = "".join([p[0] for p in name.split()[:2]]).upper() or "A"
            avatar.setText(initials)
            avatar.setStyleSheet(
                f"background:{T.PRIMARY}; color:white; border-radius:20px; font-weight:700;"
            )
        header.addWidget(avatar)
        ml.addLayout(header)

        self.stack = QStackedWidget()
        # Add placeholder widgets for each menu item; real pages are lazy-loaded
        for _ in self.MENU:
            placeholder = QWidget()
            self.stack.addWidget(placeholder)
        ml.addWidget(self.stack, 1)
        layout.addWidget(main, 1)

    def _get_page(self, index: int) -> QWidget:
        """Return the real page widget for *index*, creating it on first call."""
        if index in self._page_cache:
            return self._page_cache[index]

        # Lazy imports + instantiation
        if index == 0:
            from views.admin.dashboard_view import DashboardView
            page: QWidget = DashboardView()
        elif index == 1:
            from views.admin.trajets_view import TrajetsView
            page = TrajetsView()
        elif index == 2:
            from views.admin.bus_view import BusView
            page = BusView()
        elif index == 3:
            from views.admin.conducteurs_view import ConducteursView
            page = ConducteursView()
        elif index == 4:
            from views.admin.users_view import UsersView
            page = UsersView()
        elif index == 5:
            from views.admin.finances_view import FinancesView
            page = FinancesView()
        elif index == 6:
            from views.admin.rapports_view import RapportsView
            page = RapportsView()
        elif index == 7:
            from views.admin.parametres_view import ParametresView
            page = ParametresView()
        else:
            page = QWidget()

        self._page_cache[index] = page
        # Replace placeholder with real widget
        old = self.stack.widget(index)
        self.stack.insertWidget(index, page)
        self.stack.removeWidget(old)
        old.deleteLater()
        return page

    def _navigate(self, index: int) -> None:
        page = self._get_page(index)
        self.stack.setCurrentWidget(page)
        for i, btn in enumerate(self._nav_buttons):
            btn.set_active(i == index)
        self.page_title.setText(self.MENU[index][2])
        if hasattr(page, "refresh"):
            page.refresh()
        self._refresh_notif_badge()

    def _show_notifications(self) -> None:
        from views.admin.notifications_dialog import NotificationsDialog
        dlg = NotificationsDialog(self)
        dlg.exec()
        self._refresh_notif_badge()

    def _refresh_notif_badge(self) -> None:
        session = get_session()
        try:
            uid = current_session.user.id if current_session.user else None
            n = notification_service.unread_count(session, uid)
            self.notif_dot.setVisible(n > 0)
        finally:
            session.close()

    def _tick_clock(self) -> None:
        self.date_lbl.setText(format_long_date(datetime.now()))

    def _logout(self) -> None:
        current_session.clear()
        self.logout_requested.emit()
        self.close()
