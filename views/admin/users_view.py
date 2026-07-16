"""Admin Utilisateurs / caissiers CRUD."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QLabel,
    QHeaderView,
    QInputDialog,
)

from database.session import get_session
from resources import theme as T
from services import user_admin_service, admin_stats_service
from services.session_store import current_session
from utils.formatters import format_fc
from views.admin.widgets import (
    style_table, page_toolbar, secondary_btn,
    edit_action_btn, delete_action_btn, toggle_action_btn, normal_action_btn,
    kpi_card, set_kpi
)


class UserDialog(QDialog):
    def __init__(self, parent=None, user=None, *, creating: bool = True):
        super().__init__(parent)
        self.user = user
        self.creating = creating
        self.photo_path = user.photo_path if user else None
        self.setWindowTitle("Modifier utilisateur" if user else "Nouvel utilisateur")
        self.setMinimumWidth(420)
        form = QFormLayout(self)

        self.nom = QLineEdit()
        self.prenom = QLineEdit()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.telephone = QLineEdit()
        self.email = QLineEdit()
        self.adresse = QLineEdit()
        self.role = QComboBox()
        self.role.addItems(["caissier", "administrateur"])
        self.statut = QComboBox()
        self.statut.addItems(["actif", "bloque"])
        photo_btn = secondary_btn("Choisir photo…")
        photo_btn.clicked.connect(self._pick)
        self.photo_lbl = QLabel("Aucune photo")

        if user:
            self.nom.setText(user.nom)
            self.prenom.setText(user.prenom)
            self.username.setText(user.username)
            self.telephone.setText(user.telephone or "")
            self.email.setText(user.email or "")
            self.adresse.setText(user.adresse or "")
            self.role.setCurrentText(user.role)
            self.statut.setCurrentText(user.statut if user.statut != "inactif" else "bloque")
            if user.photo_path:
                self.photo_lbl.setText(user.photo_path)
            self.password.setPlaceholderText("Laisser vide pour ne pas changer")

        form.addRow("Nom", self.nom)
        form.addRow("Prénom", self.prenom)
        form.addRow("Identifiant", self.username)
        form.addRow("Mot de passe", self.password)
        form.addRow("Téléphone", self.telephone)
        form.addRow("Email", self.email)
        form.addRow("Adresse", self.adresse)
        form.addRow("Rôle", self.role)
        form.addRow("Statut", self.statut)
        form.addRow("Photo", photo_btn)
        form.addRow("", self.photo_lbl)

        row = QHBoxLayout()
        cancel = secondary_btn("Annuler")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Enregistrer")
        ok.setObjectName("primaryBtn")
        ok.clicked.connect(self.accept)
        row.addStretch()
        row.addWidget(cancel)
        row.addWidget(ok)
        form.addRow(row)

    def _pick(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Photo", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self.photo_path = path
            self.photo_lbl.setText(path)

    def values(self) -> dict:
        return {
            "nom": self.nom.text().strip(),
            "prenom": self.prenom.text().strip(),
            "username": self.username.text().strip(),
            "password": self.password.text(),
            "telephone": self.telephone.text().strip() or None,
            "email": self.email.text().strip() or None,
            "adresse": self.adresse.text().strip() or None,
            "role": self.role.currentText(),
            "statut": "actif" if self.statut.currentText() == "actif" else "bloque",
            "photo_path": self.photo_path,
        }


class UsersView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        toolbar, self.search, _ = page_toolbar(
            "Utilisateurs",
            search_placeholder="Nom, login, téléphone…",
            on_search=lambda _t: self.refresh(),
            add_label="Nouveau caissier",
            on_add=self._add,
        )
        lay.addLayout(toolbar)

        kpis = QHBoxLayout()
        self.k_cai = kpi_card("Caissiers actifs", "0", "users")
        self.k_rev = kpi_card("Revenu flotte", "0 FC", "coins")
        kpis.addWidget(self.k_cai)
        kpis.addWidget(self.k_rev)
        kpis.addStretch()
        lay.addLayout(kpis)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Rôle"))
        self.role = QComboBox()
        self.role.addItem("Tous", None)
        self.role.addItem("Caissiers", "caissier")
        self.role.addItem("Admins", "administrateur")
        self.role.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.role)
        filters.addStretch()
        lay.addLayout(filters)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Nom", "Identifiant", "Téléphone", "Rôle", "Statut", "Dernière connexion", "Actions"]
        )
        style_table(self.table)
        self.table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.Interactive
        )
        self.table.setColumnWidth(6, 280)
        lay.addWidget(self.table, 1)

    def refresh(self) -> None:
        session = get_session()
        try:
            users = user_admin_service.list_users(
                session,
                role=self.role.currentData(),
                search=self.search.text() if self.search else "",
            )
            active_c = sum(1 for u in users if u.role == "caissier" and u.statut == "actif")
            if self.role.currentData() is None:
                active_c = sum(
                    1
                    for u in user_admin_service.list_users(session, role="caissier")
                    if u.statut == "actif"
                )
            set_kpi(self.k_cai, str(active_c))
            set_kpi(self.k_rev, format_fc(admin_stats_service.fleet_revenue(session)))

            self.table.setRowCount(0)
            for u in users:
                row = self.table.rowCount()
                self.table.insertRow(row)
                last = u.last_login.strftime("%d/%m/%Y %H:%M") if u.last_login else "—"
                vals = [u.full_name, u.username, u.telephone or "—", u.role, u.statut, last]
                for col, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setData(Qt.ItemDataRole.UserRole, u.id)
                    self.table.setItem(row, col, item)
                self.table.setCellWidget(row, 6, self._actions(u.id, u.statut, u.role))
        finally:
            session.close()

    def _actions(self, user_id: int, statut: str, role: str) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(4)
        edit = edit_action_btn("Édit.")
        edit.clicked.connect(lambda: self._edit(user_id))
        reset = normal_action_btn("MDP")
        reset.clicked.connect(lambda: self._reset_pwd(user_id))
        block = toggle_action_btn("Bloquer" if statut == "actif" else "Activer", active=(statut == "actif"))
        block.clicked.connect(lambda: self._toggle(user_id, statut))
        delete = delete_action_btn("Suppr.")
        delete.clicked.connect(lambda: self._delete(user_id))
        h.addWidget(edit)
        h.addWidget(reset)
        h.addWidget(block)
        h.addWidget(delete)
        return w

    def _actor(self):
        return current_session.user.id if current_session.user else None

    def _add(self) -> None:
        dlg = UserDialog(self, creating=True)
        dlg.role.setCurrentText("caissier")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.values()
        if not data["nom"] or not data["prenom"] or not data["username"] or not data["password"]:
            QMessageBox.warning(self, "Utilisateur", "Champs obligatoires manquants.")
            return
        session = get_session()
        try:
            pwd = data.pop("password")
            statut = data.pop("statut", "actif")
            user = user_admin_service.create_user(
                session, password=pwd, actor_id=self._actor(), **data
            )
            if statut != "actif":
                user_admin_service.set_user_statut(session, user, statut, actor_id=self._actor())
            session.commit()
            self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _edit(self, user_id: int) -> None:
        session = get_session()
        try:
            user = user_admin_service.get_user(session, user_id)
            if not user:
                return
            dlg = UserDialog(self, user, creating=False)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            data = dlg.values()
            pwd = data.pop("password")
            user_admin_service.update_user(session, user, actor_id=self._actor(), **data)
            if pwd:
                user_admin_service.reset_password(session, user, pwd, self._actor())
            session.commit()
            self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _reset_pwd(self, user_id: int) -> None:
        pwd, ok = QInputDialog.getText(
            self, "Réinitialiser MDP", "Nouveau mot de passe :", QLineEdit.EchoMode.Password
        )
        if not ok or not pwd:
            return
        session = get_session()
        try:
            user = user_admin_service.get_user(session, user_id)
            if user:
                user_admin_service.reset_password(session, user, pwd, self._actor())
                session.commit()
                QMessageBox.information(self, "OK", "Mot de passe mis à jour.")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _toggle(self, user_id: int, statut: str) -> None:
        new_s = "bloque" if statut == "actif" else "actif"
        session = get_session()
        try:
            user = user_admin_service.get_user(session, user_id)
            if user:
                if user.id == self._actor() and new_s != "actif":
                    QMessageBox.warning(self, "Utilisateur", "Vous ne pouvez pas vous bloquer vous-même.")
                    return
                user_admin_service.set_user_statut(session, user, new_s, self._actor())
                session.commit()
                self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()

    def _delete(self, user_id: int) -> None:
        if user_id == self._actor():
            QMessageBox.warning(self, "Utilisateur", "Vous ne pouvez pas supprimer votre compte.")
            return
        if QMessageBox.question(self, "Supprimer", "Supprimer cet utilisateur ?") != QMessageBox.StandardButton.Yes:
            return
        session = get_session()
        try:
            user = user_admin_service.get_user(session, user_id)
            if user:
                user_admin_service.delete_user(session, user, self._actor())
                session.commit()
                self.refresh()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()
