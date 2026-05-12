"""
StaffScreen — staff management page for the Vehicle Service POS.
"""

import logging

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QLabel,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QPushButton,
)
from PyQt6.QtCore import Qt

from ui.theme import (
    COLOR_APP_BG,
    COLOR_PANEL_BG,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_BORDER,
    COLOR_ACCENT,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_ERROR,
    COLOR_INFO,
    FONT_FAMILY,
    FONT_PAGE_TITLE,
    FONT_SECTION_TITLE,
    FONT_BODY,
    FONT_BUTTON,
    FONT_SMALL,
    SPACING_XS,
    SPACING_SM,
    SPACING_MD,
    SPACING_LG,
    BUTTON_HEIGHT,
    INPUT_HEIGHT,
)
from ui.components import (
    PageHeader,
    DataTable,
    FormPanel,
    ActionBar,
    StatusBadge,
)
from controllers.staff_controller import StaffController

logger = logging.getLogger(__name__)


class StaffScreen(QWidget):
    """Staff management screen with table, action bar, and CRUD dialogs."""

    def __init__(self, session, stacked_widget=None, parent=None):
        super().__init__(parent)

        self._session = session
        self._stacked_widget = stacked_widget
        self._controller = StaffController()

        # ── Main layout ──
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # ── Page header ──
        self._header = PageHeader("Staff", subtitle="Manage users and permissions")
        self._header.add_action("Add Staff", self._on_add_staff, "btn_primary")
        layout.addWidget(self._header)

        # ── Data table ──
        self._table = DataTable(
            columns=[
                ("ID", 50),
                ("Username", 120),
                ("Full Name", 180),
                ("Role", 120),
                ("Active", 70),
                ("Created", 110),
            ]
        )
        layout.addWidget(self._table, stretch=1)

        # ── Action bar ──
        self._action_bar = ActionBar()
        self._action_bar.add_button("Edit", self._on_edit_staff, "btn_secondary")
        self._action_bar.add_button("Toggle Active", self._on_toggle_active, "btn_warning")
        self._action_bar.add_button("Change Password", self._on_change_password, "btn_secondary")
        self._action_bar.add_button("Delete", self._on_delete_staff, "btn_danger")
        layout.addWidget(self._action_bar)

        # ── Initial data load ──
        self.refresh()

    # ── Data loading ────────────────────────────────────────────────

    def refresh(self):
        """Reload staff list into the table."""
        staff_list = self._controller.get_all_staff()
        rows = []
        for s in staff_list:
            active_text = "Active" if s.is_active else "Inactive"
            created = ""
            if s.created_at:
                created = s.created_at.strftime("%Y-%m-%d")
            rows.append([
                s.id,
                s.username or "",
                s.full_name or "",
                s.role or "",
                active_text,
                created,
            ])
        self._table.load_data(rows)

        # Apply StatusBadge styling to the "Active" column (column 4)
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 4)
            if item:
                badge = StatusBadge(item.text())
                self._table.setCellWidget(row, 4, badge)

    # ── Add staff ───────────────────────────────────────────────────

    def _on_add_staff(self):
        """Open the Add Staff dialog."""
        dialog = StaffDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["username"].strip() or not data["password"].strip() or not data["full_name"].strip():
                QMessageBox.warning(self, "Validation Error", "Username, Password, and Full Name are required.")
                return
            result = self._controller.create_staff(
                username=data["username"].strip(),
                password=data["password"].strip(),
                full_name=data["full_name"].strip(),
                role=data["role"],
            )
            if result:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to create staff member. Username may already exist.")

    # ── Edit staff ──────────────────────────────────────────────────

    def _on_edit_staff(self):
        """Open the Edit Staff dialog for the selected row."""
        row = self._table.get_selected_row()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a staff member to edit.")
            return

        staff_id = self._table.get_selected_data(0)
        if not staff_id:
            return

        staff_list = self._controller.get_all_staff()
        staff_member = None
        for s in staff_list:
            if str(s.id) == staff_id:
                staff_member = s
                break

        if not staff_member:
            QMessageBox.critical(self, "Error", "Staff member not found.")
            return

        dialog = StaffDialog(parent=self, staff=staff_member)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["full_name"].strip():
                QMessageBox.warning(self, "Validation Error", "Full Name is required.")
                return

            kwargs = {
                "full_name": data["full_name"].strip(),
                "role": data["role"],
            }

            # Only update password if a new one was provided
            if data["password"].strip():
                self._controller.change_password(int(staff_id), data["password"].strip())

            result = self._controller.update_staff(int(staff_id), **kwargs)
            if result:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to update staff member.")

    # ── Toggle active ───────────────────────────────────────────────

    def _on_toggle_active(self):
        """Confirm and toggle the active status of the selected staff member."""
        row = self._table.get_selected_row()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a staff member.")
            return

        staff_id = self._table.get_selected_data(0)
        staff_name = self._table.get_selected_data(2)
        current_status = self._table.get_selected_data(4)
        if not staff_id:
            return

        new_status = "inactive" if current_status == "Active" else "active"
        reply = QMessageBox.question(
            self,
            "Confirm Toggle",
            f"Are you sure you want to set '{staff_name}' as {new_status}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            result = self._controller.toggle_active(int(staff_id))
            if result:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to toggle staff status.")

    # ── Change password ─────────────────────────────────────────────

    def _on_change_password(self):
        """Open the Change Password dialog for the selected staff member."""
        row = self._table.get_selected_row()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a staff member.")
            return

        staff_id = self._table.get_selected_data(0)
        staff_name = self._table.get_selected_data(2)
        if not staff_id:
            return

        dialog = ChangePasswordDialog(staff_name=staff_name, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_password = dialog.get_password()
            if not new_password:
                QMessageBox.warning(self, "Validation Error", "Password cannot be empty.")
                return
            success = self._controller.change_password(int(staff_id), new_password)
            if success:
                QMessageBox.information(self, "Success", f"Password changed for '{staff_name}'.")
            else:
                QMessageBox.critical(self, "Error", "Failed to change password.")

    # ── Delete staff ────────────────────────────────────────────────

    def _on_delete_staff(self):
        """Confirm and deactivate the selected staff member."""
        row = self._table.get_selected_row()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a staff member to delete.")
            return

        staff_id = self._table.get_selected_data(0)
        staff_name = self._table.get_selected_data(2)
        if not staff_id:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete staff member '{staff_name}'?\n"
            "This will deactivate their account.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Deactivate by toggling active to False
            result = self._controller.toggle_active(int(staff_id))
            if result:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete staff member.")


# ─── Staff Dialog ──────────────────────────────────────────────────────

class StaffDialog(QDialog):
    """Dialog for creating or editing a staff member."""

    def __init__(self, parent=None, staff=None):
        super().__init__(parent)

        self._staff = staff
        self._is_edit = staff is not None

        self.setWindowTitle("Edit Staff" if self._is_edit else "Add Staff")
        self.setMinimumWidth(460)
        self.setModal(True)

        # ── Main layout ──
        outer = QVBoxLayout(self)
        outer.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        outer.setSpacing(SPACING_MD)

        # ── Form panel ──
        form = FormPanel("Staff Details")

        # Username *
        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("Username *")
        self._username_input.setFixedHeight(INPUT_HEIGHT)
        if self._is_edit:
            self._username_input.setReadOnly(True)
        form.add_row("Username *", self._username_input)

        # Password * (required for new, optional for edit)
        self._password_input = QLineEdit()
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        placeholder = "New password (leave blank to keep)" if self._is_edit else "Password *"
        self._password_input.setPlaceholderText(placeholder)
        self._password_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Password *" if not self._is_edit else "Password", self._password_input)

        # Full Name *
        self._fullname_input = QLineEdit()
        self._fullname_input.setPlaceholderText("Full name *")
        self._fullname_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Full Name *", self._fullname_input)

        # Role
        self._role_combo = QComboBox()
        self._role_combo.addItems(["ADMIN", "MANAGER", "CASHIER", "MECHANIC"])
        self._role_combo.setFixedHeight(INPUT_HEIGHT)
        self._role_combo.setMinimumWidth(160)
        form.add_row("Role", self._role_combo)

        outer.addWidget(form)

        # ── Dialog buttons ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(SPACING_SM)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btn_secondary")
        cancel_btn.setFixedHeight(BUTTON_HEIGHT)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save" if self._is_edit else "Create")
        save_btn.setObjectName("btn_primary")
        save_btn.setFixedHeight(BUTTON_HEIGHT)
        save_btn.setMinimumWidth(100)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        outer.addLayout(btn_layout)

        # ── Pre-fill for edit ──
        if self._is_edit:
            self._username_input.setText(staff.username or "")
            self._fullname_input.setText(staff.full_name or "")
            # Set combo to current role
            role_index = self._role_combo.findText(staff.role or "CASHIER")
            if role_index >= 0:
                self._role_combo.setCurrentIndex(role_index)

    # ── Private ─────────────────────────────────────────────────────

    def _on_save(self):
        """Validate and accept the dialog."""
        username = self._username_input.text().strip()
        full_name = self._fullname_input.text().strip()
        password = self._password_input.text().strip()

        if not username:
            QMessageBox.warning(self, "Validation", "Username is required.")
            self._username_input.setFocus()
            return
        if not self._is_edit and not password:
            QMessageBox.warning(self, "Validation", "Password is required for new staff.")
            self._password_input.setFocus()
            return
        if not full_name:
            QMessageBox.warning(self, "Validation", "Full Name is required.")
            self._fullname_input.setFocus()
            return

        self.accept()

    # ── Public API ──────────────────────────────────────────────────

    def get_data(self) -> dict:
        """Return a dict of all form field values."""
        return {
            "username": self._username_input.text(),
            "password": self._password_input.text(),
            "full_name": self._fullname_input.text(),
            "role": self._role_combo.currentText(),
        }


# ─── Change Password Dialog ────────────────────────────────────────────

class ChangePasswordDialog(QDialog):
    """Dialog for changing a staff member's password."""

    def __init__(self, staff_name: str = "", parent=None):
        super().__init__(parent)

        self._staff_name = staff_name

        self.setWindowTitle("Change Password")
        self.setMinimumWidth(400)
        self.setModal(True)

        # ── Main layout ──
        outer = QVBoxLayout(self)
        outer.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        outer.setSpacing(SPACING_MD)

        # ── Form panel ──
        form = FormPanel(f"Change Password — {staff_name}" if staff_name else "Change Password")

        # New Password
        self._new_password_input = QLineEdit()
        self._new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._new_password_input.setPlaceholderText("New password *")
        self._new_password_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("New Password *", self._new_password_input)

        # Confirm Password
        self._confirm_password_input = QLineEdit()
        self._confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_password_input.setPlaceholderText("Confirm new password *")
        self._confirm_password_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Confirm Password *", self._confirm_password_input)

        outer.addWidget(form)

        # ── Dialog buttons ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(SPACING_SM)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btn_secondary")
        cancel_btn.setFixedHeight(BUTTON_HEIGHT)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Change Password")
        save_btn.setObjectName("btn_primary")
        save_btn.setFixedHeight(BUTTON_HEIGHT)
        save_btn.setMinimumWidth(130)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        outer.addLayout(btn_layout)

    # ── Private ─────────────────────────────────────────────────────

    def _on_save(self):
        """Validate passwords match and accept the dialog."""
        new_pw = self._new_password_input.text().strip()
        confirm_pw = self._confirm_password_input.text().strip()

        if not new_pw:
            QMessageBox.warning(self, "Validation", "New password is required.")
            self._new_password_input.setFocus()
            return

        if new_pw != confirm_pw:
            QMessageBox.warning(self, "Validation", "Passwords do not match.")
            self._confirm_password_input.setFocus()
            return

        if len(new_pw) < 4:
            QMessageBox.warning(self, "Validation", "Password must be at least 4 characters.")
            self._new_password_input.setFocus()
            return

        self.accept()

    # ── Public API ──────────────────────────────────────────────────

    def get_password(self) -> str:
        """Return the new password entered by the user."""
        return self._new_password_input.text().strip()
