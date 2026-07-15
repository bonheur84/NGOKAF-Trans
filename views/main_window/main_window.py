"""Main cashier window — sidebar + header + stacked pages."""
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
from resources import theme as T
from services.session_store import current_session
from utils.formatters import format_long_date
from utils.icons import fa_icon, ICONS
from views.ventes.ventes_view import VentesView
from views.bagages.bagages_view import BagagesView
from views.ventes.historique_dialog import HistoriqueDialog


class SidebarButton(QPushButton):
    def __init__(self, text: str, icon_name: str, parent=None):
        super().__init__(f"  {text}", parent)
        self._icon_name = icon_name
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setIconSize(QSize(18, 18))
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
                    padding-left: 16px;
                    font-size: {T.SIZE_MENU}px;
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
                    padding-left: 16px;
                    font-size: {T.SIZE_MENU}px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: rgba(255,255,255,0.06);
                }}
                """
            )


class MainWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{settings.AGENCY_NAME} — Terminal")
        self.resize(1440, 900)
        self.setMinimumSize(1200, 720)
        self.setStyleSheet(f"QMainWindow {{ background: {T.BG_MAIN}; }}")
        self._idle_ms = settings.SESSION_TIMEOUT_MINUTES * 60 * 1000
        self._build()
        self._setup_idle_timer()
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

    def _build(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(T.SIDEBAR_WIDTH)
        sidebar.setStyleSheet(f"background-color: {T.BG_SIDEBAR};")
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(12, 16, 12, 16)
        sb.setSpacing(12)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(
            f"background:white; border-radius:12px; padding:8px;"
        )
        if settings.logo_path.exists():
            logo.setPixmap(
                QPixmap(str(settings.logo_path)).scaled(
                    110, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            )
        sb.addWidget(logo)

        brand = QLabel("Ngokaf Trans")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setStyleSheet(f"color:{T.PRIMARY_ALT}; font-size:17px; font-weight:700;")
        sb.addWidget(brand)
        term = QLabel(settings.TERMINAL_NAME)
        term.setAlignment(Qt.AlignmentFlag.AlignCenter)
        term.setStyleSheet(f"color:{T.PRIMARY_ALT}; font-size:11px; letter-spacing:1px;")
        sb.addWidget(term)
        sb.addSpacing(28)

        self.btn_ventes = SidebarButton("VENTES", ICONS["ventes"])
        self.btn_bagages = SidebarButton("BAGAGES", ICONS["bagages"])
        self.btn_ventes.clicked.connect(lambda: self._navigate(0))
        self.btn_bagages.clicked.connect(lambda: self._navigate(1))
        sb.addWidget(self.btn_ventes)
        sb.addWidget(self.btn_bagages)
        sb.addStretch()

        self.btn_logout = SidebarButton("DÉCONNEXION", ICONS["logout"])
        self.btn_logout.clicked.connect(self._logout)
        sb.addWidget(self.btn_logout)
        layout.addWidget(sidebar)

        # Main column
        main = QWidget()
        main.setStyleSheet(f"background:{T.BG_MAIN};")
        ml = QVBoxLayout(main)
        ml.setContentsMargins(T.MARGIN_MAIN, 10, T.MARGIN_MAIN, T.MARGIN_MAIN)
        ml.setSpacing(16)

        # Header
        header = QHBoxLayout()
        self.page_title = QLabel("Vente de Billet")
        self.page_title.setStyleSheet(
            f"font-size:22px; font-weight:700; color:{T.TEXT_PRIMARY};"
        )
        header.addWidget(self.page_title)

        self.date_lbl = QLabel()
        self.date_lbl.setStyleSheet(f"font-size:14px; color:{T.TEXT_SECONDARY}; margin-left:16px;")
        header.addWidget(self.date_lbl)
        header.addStretch()

        # Notification bell
        notif = QPushButton()
        notif.setIcon(fa_icon(ICONS["bell"], color=T.PRIMARY_ALT))
        notif.setIconSize(QSize(18, 18))
        notif.setFixedSize(34, 34)
        notif.setCursor(Qt.CursorShape.PointingHandCursor)
        notif.setStyleSheet("QPushButton{background:transparent;border:none;}")
        notif.clicked.connect(self._show_history)
        header.addWidget(notif)

        user_box = QVBoxLayout()
        user_box.setSpacing(0)
        user = current_session.user
        name = user.full_name if user else "—"
        self.user_name = QLabel(name)
        self.user_name.setStyleSheet(
            f"font-size:{T.SIZE_CASHIER_NAME}px; font-weight:600; color:{T.TEXT_PRIMARY};"
        )
        self.user_role = QLabel("Caissier")
        self.user_role.setStyleSheet(
            f"font-size:{T.SIZE_ROLE}px; color:{T.TEXT_SECONDARY};"
        )
        user_box.addWidget(self.user_name)
        user_box.addWidget(self.user_role)
        header.addLayout(user_box)

        avatar = QLabel()
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet(
            f"background:{T.BORDER}; border-radius:20px; color:{T.TEXT_PRIMARY};"
        )
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if user and user.photo_path:
            avatar.setPixmap(
                QPixmap(user.photo_path).scaled(
                    40, 40, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            initials = "".join([p[0] for p in name.split()[:2]]).upper() or "?"
            avatar.setText(initials)
            avatar.setStyleSheet(
                f"background:{T.PRIMARY}; color:white; border-radius:20px; font-weight:700;"
            )
        header.addWidget(avatar)
        ml.addLayout(header)

        self.stack = QStackedWidget()
        self.ventes = VentesView()
        self.bagages = BagagesView()
        self.stack.addWidget(self.ventes)
        self.stack.addWidget(self.bagages)
        ml.addWidget(self.stack, 1)

        layout.addWidget(main, 1)
        self._navigate(0)

    def _navigate(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.btn_ventes.set_active(index == 0)
        self.btn_bagages.set_active(index == 1)
        if index == 0:
            self.page_title.setText("Vente de Billet")
            self.page_title.setStyleSheet(
                f"font-size:22px; font-weight:700; color:{T.TEXT_PRIMARY};"
            )
            self.ventes.refresh()
        else:
            self.page_title.setText("Gestion des Bagages")
            self.page_title.setStyleSheet(
                f"font-size:22px; font-weight:700; color:{T.PRIMARY_ALT};"
            )
            self.bagages.refresh()

    def _show_history(self) -> None:
        dlg = HistoriqueDialog(self)
        dlg.exec()

    def _tick_clock(self) -> None:
        self.date_lbl.setText(format_long_date(datetime.now()))

    def _setup_idle_timer(self) -> None:
        self._idle = QTimer(self)
        self._idle.setSingleShot(True)
        self._idle.timeout.connect(self._on_idle)
        self._idle.start(self._idle_ms)

    def _on_idle(self) -> None:
        QMessageBox.warning(
            self,
            "Session expirée",
            "Déconnexion automatique après inactivité.",
        )
        self._logout()

    def _logout(self) -> None:
        current_session.clear()
        self.logout_requested.emit()
        self.close()

    def eventFilter(self, obj, event):
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        self._idle.start(self._idle_ms)
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self._idle.start(self._idle_ms)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self._idle.start(self._idle_ms)
        super().mouseMoveEvent(event)
