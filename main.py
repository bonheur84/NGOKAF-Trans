"""NGOKAF TRANS — entry point."""
from __future__ import annotations

import sys
import logging

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from config.settings import settings, RESOURCE_ROOT
from utils.runtime_bootstrap import show_bootstrap_errors, verify_critical_resources
from utils.logging_setup import setup_logging
from utils.fonts import load_fonts
from utils.styles import global_stylesheet
from database.init_db import init_database
from services.session_store import current_session
from services.auto_backup_service import get_auto_backup_service
from views.login.login_view import LoginView
from views.main_window.main_window import MainWindow
from views.admin.admin_window import AdminWindow


logger = logging.getLogger(__name__)


class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("NGOKAF TRANS")
        self.app.setOrganizationName("NGOKAF")
        family = load_fonts()
        self.app.setStyleSheet(global_stylesheet(family))
        self.login: LoginView | None = None
        self.main: MainWindow | None = None
        self.admin: AdminWindow | None = None
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
        if not self.bootstrap():
            return 1
        self.show_login()
        return self.app.exec()

    def show_login(self) -> None:
        if self.main:
            self.main.close()
            self.main = None
        if self.admin:
            self.admin.close()
            self.admin = None
        current_session.clear()
        self.login = LoginView()
        self.login.login_success.connect(self._after_auth)
        self.login.showMaximized()

    def _after_auth(self) -> None:
        if self.login:
            self.login.close()
            self.login = None
        user = current_session.user
        if user and user.is_admin:
            self.admin = AdminWindow()
            self.admin.logout_requested.connect(self.show_login)
            self.admin.showMaximized()
        else:
            self.main = MainWindow()
            self.main.logout_requested.connect(self.show_login)
            self.main.showMaximized()


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
