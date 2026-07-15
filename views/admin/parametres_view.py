"""Admin Paramètres — agence, impression, backup, MDP."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QFormLayout,
    QScrollArea,
    QGroupBox,
)

from config.settings import settings
from database.session import get_session
from models.audit import AuditLog
from resources import theme as T
from services import settings_service, backup_service, user_admin_service, notification_service
from services.audit_service import log_audit
from services.session_store import current_session
from views.admin.widgets import secondary_btn, style_table
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem


class ParametresView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;")
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setSpacing(14)

        title = QLabel("Paramètres")
        title.setStyleSheet(
            f"color:{T.PRIMARY_ALT}; font-size:{T.SIZE_CARD_TITLE}px; font-weight:700;"
        )
        lay.addWidget(title)

        agency = QGroupBox("Profil agence")
        form = QFormLayout(agency)
        self.agency_name = QLineEdit()
        self.agency_address = QLineEdit()
        self.agency_phone = QLineEdit()
        self.terminal_name = QLineEdit()
        self.currency = QLineEdit("FC")
        self.currency.setReadOnly(True)
        self.tva = QLineEdit()
        self.prefix = QLineEdit()
        form.addRow("Nom agence", self.agency_name)
        form.addRow("Adresse", self.agency_address)
        form.addRow("Téléphone", self.agency_phone)
        form.addRow("Terminal", self.terminal_name)
        form.addRow("Devise", self.currency)
        form.addRow("TVA (%)", self.tva)
        form.addRow("Préfixe tickets", self.prefix)
        lay.addWidget(agency)

        print_box = QGroupBox("Impression")
        pf = QFormLayout(print_box)
        self.ticket_width = QComboBox()
        self.ticket_width.addItems(["80", "58"])
        self.luggage_width = QComboBox()
        self.luggage_width.addItems(["58", "80"])
        pf.addRow("Largeur ticket (mm)", self.ticket_width)
        pf.addRow("Largeur étiquette bagage (mm)", self.luggage_width)
        lay.addWidget(print_box)

        session_box = QGroupBox("Session & bagages")
        sf = QFormLayout(session_box)
        self.timeout = QSpinBox()
        self.timeout.setRange(5, 240)
        self.timeout.setSuffix(" min")
        self.luggage_base = QLineEdit()
        self.luggage_rate = QLineEdit()
        sf.addRow("Timeout session", self.timeout)
        sf.addRow("Frais base bagage (FC)", self.luggage_base)
        sf.addRow("Tarif / kg (FC)", self.luggage_rate)
        lay.addWidget(session_box)

        pwd_box = QGroupBox("Mot de passe administrateur")
        pwd_f = QFormLayout(pwd_box)
        self.old_pwd = QLineEdit()
        self.old_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pwd2 = QLineEdit()
        self.new_pwd2.setEchoMode(QLineEdit.EchoMode.Password)
        pwd_f.addRow("Actuel", self.old_pwd)
        pwd_f.addRow("Nouveau", self.new_pwd)
        pwd_f.addRow("Confirmer", self.new_pwd2)
        change_pwd = QPushButton("Changer le mot de passe")
        change_pwd.setObjectName("secondaryBtn")
        change_pwd.clicked.connect(self._change_pwd)
        pwd_f.addRow(change_pwd)
        lay.addWidget(pwd_box)

        backup_box = QGroupBox("Sauvegarde MySQL")
        bf = QHBoxLayout(backup_box)
        bak = QPushButton("Créer une sauvegarde")
        bak.setObjectName("primaryBtn")
        bak.clicked.connect(self._backup)
        rest = secondary_btn("Restaurer…")
        rest.clicked.connect(self._restore)
        bf.addWidget(bak)
        bf.addWidget(rest)
        bf.addStretch()
        lay.addWidget(backup_box)

        save = QPushButton("Enregistrer les paramètres")
        save.setObjectName("primaryBtn")
        save.clicked.connect(self._save)
        lay.addWidget(save)

        lay.addWidget(QLabel("Journal d'audit récent"))
        self.audit = QTableWidget(0, 5)
        self.audit.setHorizontalHeaderLabels(["Date", "Action", "Entité", "ID", "Détails"])
        style_table(self.audit)
        self.audit.setMaximumHeight(220)
        lay.addWidget(self.audit)

        scroll.setWidget(body)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        session = get_session()
        try:
            g = settings_service.get_setting
            self.agency_name.setText(g(session, "agency_name", settings.AGENCY_NAME))
            self.agency_address.setText(g(session, "agency_address", settings.AGENCY_ADDRESS))
            self.agency_phone.setText(g(session, "agency_phone", settings.AGENCY_PHONE))
            self.terminal_name.setText(g(session, "terminal_name", settings.TERMINAL_NAME))
            self.tva.setText(g(session, "tva_percent", "0"))
            self.prefix.setText(g(session, "ticket_prefix", "TK-"))
            self.ticket_width.setCurrentText(g(session, "ticket_width_mm", "80"))
            self.luggage_width.setCurrentText(g(session, "luggage_width_mm", "58"))
            self.timeout.setValue(int(g(session, "session_timeout_minutes", "30") or "30"))
            self.luggage_base.setText(g(session, "luggage_base_fee", str(settings.LUGGAGE_BASE_FEE)))
            self.luggage_rate.setText(g(session, "luggage_weight_rate", str(settings.LUGGAGE_WEIGHT_RATE)))

            logs = (
                session.query(AuditLog)
                .order_by(AuditLog.created_at.desc())
                .limit(40)
                .all()
            )
            self.audit.setRowCount(0)
            for log in logs:
                row = self.audit.rowCount()
                self.audit.insertRow(row)
                vals = [
                    log.created_at.strftime("%d/%m/%Y %H:%M"),
                    log.action,
                    log.entity,
                    str(log.entity_id or ""),
                    (log.details or "")[:80],
                ]
                for c, v in enumerate(vals):
                    self.audit.setItem(row, c, QTableWidgetItem(v))
        finally:
            session.close()

    def _actor(self):
        return current_session.user.id if current_session.user else None

    def _save(self) -> None:
        session = get_session()
        try:
            pairs = {
                "agency_name": self.agency_name.text().strip(),
                "agency_address": self.agency_address.text().strip(),
                "agency_phone": self.agency_phone.text().strip(),
                "terminal_name": self.terminal_name.text().strip(),
                "currency": "FC",
                "tva_percent": self.tva.text().strip() or "0",
                "ticket_prefix": self.prefix.text().strip() or "TK-",
                "ticket_width_mm": self.ticket_width.currentText(),
                "luggage_width_mm": self.luggage_width.currentText(),
                "session_timeout_minutes": str(self.timeout.value()),
                "luggage_base_fee": self.luggage_base.text().strip(),
                "luggage_weight_rate": self.luggage_rate.text().strip(),
            }
            for k, v in pairs.items():
                settings_service.set_setting(session, k, v)
            log_audit(session, "update", "settings", None, self._actor(), pairs)
            notification_service.notify(session, "Paramètres mis à jour", "Les paramètres ont été enregistrés avec succès.", self._actor())
            session.commit()
            QMessageBox.information(self, "Paramètres", "Enregistré.")
            self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _change_pwd(self) -> None:
        if self.new_pwd.text() != self.new_pwd2.text():
            QMessageBox.warning(self, "Mot de passe", "Confirmation différente.")
            return
        if len(self.new_pwd.text()) < 6:
            QMessageBox.warning(self, "Mot de passe", "Au moins 6 caractères.")
            return
        user = current_session.user
        if not user:
            return
        session = get_session()
        try:
            # Re-fetch bound instance
            admin = user_admin_service.get_user(session, user.id)
            user_admin_service.change_admin_password(
                session, admin, self.old_pwd.text(), self.new_pwd.text()
            )
            session.commit()
            self.old_pwd.clear()
            self.new_pwd.clear()
            self.new_pwd2.clear()
            QMessageBox.information(self, "Mot de passe", "Mot de passe modifié.")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _backup(self) -> None:
        session = get_session()
        try:
            path = backup_service.backup_database()
            log_audit(session, "backup", "database", None, self._actor(), {"path": str(path)})
            notification_service.notify_backup_success(session, path.name, self._actor())
            session.commit()
            QMessageBox.information(self, "Backup", f"Sauvegarde créée :\n{path}")
        except Exception as e:
            session.rollback()
            notification_service.notify_backup_failed(session, str(e), self._actor())
            QMessageBox.critical(self, "Backup", str(e))
        finally:
            session.close()

    def _restore(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Restaurer backup", str(settings.BACKUPS), "SQL (*.sql)"
        )
        if not path:
            return
        if QMessageBox.question(
            self,
            "Restaurer",
            "Cette opération écrase la base actuelle. Continuer ?",
        ) != QMessageBox.StandardButton.Yes:
            return
        session = get_session()
        try:
            backup_service.restore_database(Path(path))
            log_audit(session, "restore", "database", None, self._actor(), {"path": path})
            notification_service.notify(session, "Restauration terminée", "La base de données a été restaurée avec succès.", self._actor())
            session.commit()
            QMessageBox.information(self, "Restore", "Restauration terminée. Redémarrez l'application.")
        except Exception as e:
            session.rollback()
            notification_service.notify_critical_error(session, f"Échec restauration : {str(e)}", self._actor())
            QMessageBox.critical(self, "Restore", str(e))
        finally:
            session.close()
