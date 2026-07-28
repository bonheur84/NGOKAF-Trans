"""NGOKAF TRANS — entry point."""
from __future__ import annotations

import sys
import logging

from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor, QFont

from config.settings import settings, RESOURCE_ROOT
from utils.runtime_bootstrap import show_bootstrap_errors, verify_critical_resources
from utils.logging_setup import setup_logging
from utils.fonts import load_fonts
from utils.styles import global_stylesheet
from database.init_db import init_database
from services.session_store import current_session
from services.auto_backup_service import get_auto_backup_service


logger = logging.getLogger(__name__)


def _make_splash(app: QApplication, font_family: str) -> QSplashScreen:
    """Create a branded splash screen shown while the app initialises."""
    # Build a simple pixmap — 480×260 matching brand colours
    from PySide6.QtGui import QPainter, QLinearGradient, QPen
    pm = QPixmap(480, 260)
    pm.fill(QColor("#0A0F1E"))

    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Subtle gradient bar at the bottom
    grad = QLinearGradient(0, 220, 480, 260)
    grad.setColorAt(0, QColor("#1B6CA8"))
    grad.setColorAt(1, QColor("#0A0F1E"))
    painter.fillRect(0, 220, 480, 40, grad)

    # Logo
    logo_path = settings.logo_path
    if logo_path.exists():
        logo_pm = QPixmap(str(logo_path)).scaled(
            80, 60,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(200, 50, logo_pm)

    # Title
    f = QFont(font_family, 18, QFont.Weight.Bold)
    painter.setFont(f)
    painter.setPen(QColor("#FFFFFF"))
    painter.drawText(pm.rect().adjusted(0, 120, 0, -60), Qt.AlignmentFlag.AlignHCenter, "NGOKAF TRANS")

    # Sub-title
    f2 = QFont(font_family, 10)
    painter.setFont(f2)
    painter.setPen(QColor("#8FA4BF"))
    painter.drawText(pm.rect().adjusted(0, 150, 0, -30), Qt.AlignmentFlag.AlignHCenter, "Système de Gestion de Billets de Bus")

    # Loading text
    f3 = QFont(font_family, 9)
    painter.setFont(f3)
    painter.setPen(QColor("#1B6CA8"))
    painter.drawText(pm.rect().adjusted(0, 0, 0, -10), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, "Chargement en cours…")

    painter.end()

    splash = QSplashScreen(pm, Qt.WindowType.WindowStaysOnTopHint)
    splash.setFont(QFont(font_family, 9))
    return splash


class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("NGOKAF TRANS")
        self.app.setOrganizationName("NGOKAF")
        family = load_fonts()
        self.app.setStyleSheet(global_stylesheet(family))
        self._font_family = family
        self.login = None
        self.main = None
        self.admin = None
        # Start auto-backup service
        get_auto_backup_service()

    def bootstrap(self) -> bool:
        issues = verify_critical_resources(RESOURCE_ROOT)
        if issues:
            show_bootstrap_errors(issues)
        try:
            init_database()
            return True
        except Exception as e:
            logger.exception("Database init failed")
            QMessageBox.critical(
                None,
                "Erreur base de données",
                f"Impossible d'initialiser MySQL.\n\n{e}\n\n"
                "Vérifiez que MySQL tourne et que le fichier .env "
                f"({settings.ROOT / '.env'}) est correctement configuré.",
            )
            return False

    def start(self) -> int:
        # Show splash immediately so the user sees something right away
        splash = _make_splash(self.app, self._font_family)
        splash.show()
        self.app.processEvents()   # paint it now, before any heavy work

        if not self.bootstrap():
            splash.close()
            return 1

        # Done loading — hide splash and show login
        splash.close()
        self.show_login()
        return self.app.exec()

    def show_login(self) -> None:
        old_main = self.main
        old_admin = self.admin
        self.main = None
        self.admin = None
        current_session.clear()

        # Import lazily so the module isn't loaded at Python startup
        from views.login.login_view import LoginView
        self.login = LoginView()
        self.login.login_success.connect(self._after_auth)
        self.login.showMaximized()

        if old_main:
            old_main.close()
        if old_admin:
            old_admin.close()

    def _after_auth(self) -> None:
        user = current_session.user
        old_login = self.login

        # Show a brief splash while the main window builds
        splash = _make_splash(self.app, self._font_family)
        splash.show()
        self.app.processEvents()

        try:
            if user and user.is_admin:
                from views.admin.admin_window import AdminWindow
                self.admin = AdminWindow()
                self.admin.logout_requested.connect(self.show_login)
                self.admin.showMaximized()
            else:
                from views.main_window.main_window import MainWindow
                self.main = MainWindow()
                self.main.logout_requested.connect(self.show_login)
                self.main.showMaximized()

            splash.close()

            # Close old login AFTER new window is shown so Qt never sees 0 open windows
            if old_login:
                old_login.close()
                self.login = None
        except Exception as e:
            logger.exception("Erreur lors de l'ouverture de la fenêtre principale")
            splash.close()
            QMessageBox.critical(
                None,
                "Erreur",
                f"Impossible d'ouvrir la fenêtre principale.\n\n{e}",
            )
            if old_login:
                old_login.showMaximized()


def main() -> None:
    setup_logging()
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    try:
        app = Application()
        sys.exit(app.start())
    except Exception as e:
        logging.exception("Fatal startup error")
        try:
            QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "NGOKAF TRANS",
                f"Impossible de démarrer l'application.\n\n{e}",
            )
        except Exception:
            print(f"Fatal: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
