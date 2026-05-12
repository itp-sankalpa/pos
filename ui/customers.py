"""
CustomersScreen — customer management page for the Vehicle Service POS.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
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
    TABLE_ROW_HEIGHT,
)
from ui.components import (
    PageHeader,
    SearchBar,
    DataTable,
    FormPanel,
    ActionBar,
)
from controllers.customer_controller import CustomerController


class CustomersScreen(QWidget):
    """Customer management screen with search, table, and CRUD dialogs."""

    def __init__(self, session, stacked_widget=None, parent=None):
        super().__init__(parent)

        self._session = session
        self._stacked_widget = stacked_widget
        self._controller = CustomerController()

        # ── Main layout ──
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # ── Page header ──
        self._header = PageHeader("Customers", subtitle="Manage your customer database")
        self._header.add_action("Add Customer", self._on_add_customer, "btn_primary")
        layout.addWidget(self._header)

        # ── Search bar ──
        self._search_bar = SearchBar(placeholder="Search by name or phone...")
        self._search_bar.set_search_callback(self._on_search)
        layout.addWidget(self._search_bar)

        # ── Data table ──
        self._table = DataTable(
            columns=[
                ("ID", 50),
                ("Name", 200),
                ("Phone", 130),
                ("Email", 180),
                ("NIC", 120),
                ("Address", 200),
            ]
        )
        self._table.set_double_click_handler(self._on_double_click_row)
        layout.addWidget(self._table, stretch=1)

        # ── Action bar ──
        self._action_bar = ActionBar()
        self._action_bar.add_button("Edit", self._on_edit_customer, "btn_secondary")
        self._action_bar.add_button("Delete", self._on_delete_customer, "btn_danger")
        layout.addWidget(self._action_bar)

        # ── Initial data load ──
        self.refresh()

    # ── Data loading ────────────────────────────────────────────────

    def refresh(self):
        """Reload customer data into the table."""
        customers = self._controller.get_customers()
        rows = []
        for c in customers:
            rows.append([
                c.id,
                c.name or "",
                c.phone or "",
                c.email or "",
                c.nic or "",
                c.address or "",
            ])
        self._table.load_data(rows)

    # ── Search ──────────────────────────────────────────────────────

    def _on_search(self, text: str):
        """Debounced search callback — filter customers and reload table."""
        customers = self._controller.get_customers(search=text.strip() or None)
        rows = []
        for c in customers:
            rows.append([
                c.id,
                c.name or "",
                c.phone or "",
                c.email or "",
                c.nic or "",
                c.address or "",
            ])
        self._table.load_data(rows)

    # ── Add customer ────────────────────────────────────────────────

    def _on_add_customer(self):
        """Open the Add Customer dialog."""
        dialog = CustomerDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["name"].strip() or not data["phone"].strip():
                QMessageBox.warning(self, "Validation Error", "Name and Phone are required.")
                return
            result = self._controller.create_customer(
                name=data["name"].strip(),
                phone=data["phone"].strip(),
                email=data["email"].strip() or None,
                address=data["address"].strip() or None,
                nic=data["nic"].strip() or None,
                notes=data["notes"].strip() or None,
            )
            if result:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to create customer.")

    # ── Edit customer ───────────────────────────────────────────────

    def _on_edit_customer(self):
        """Open the Edit Customer dialog for the selected row."""
        row = self._table.get_selected_row()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a customer to edit.")
            return
        customer_id = self._table.get_selected_data(0)
        if not customer_id:
            return
        customer = self._controller.get_customer(int(customer_id))
        if not customer:
            QMessageBox.critical(self, "Error", "Customer not found.")
            return
        self._open_edit_dialog(customer)

    def _on_double_click_row(self, row, _col):
        """Double-click handler — open edit dialog for clicked row."""
        item = self._table.item(row, 0)
        if not item:
            return
        customer_id = int(item.text())
        customer = self._controller.get_customer(customer_id)
        if customer:
            self._open_edit_dialog(customer)

    def _open_edit_dialog(self, customer):
        """Open the Edit Customer dialog pre-filled with *customer* data."""
        dialog = CustomerDialog(parent=self, customer=customer)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["name"].strip() or not data["phone"].strip():
                QMessageBox.warning(self, "Validation Error", "Name and Phone are required.")
                return
            result = self._controller.update_customer(
                customer.id,
                name=data["name"].strip(),
                phone=data["phone"].strip(),
                email=data["email"].strip() or None,
                address=data["address"].strip() or None,
                nic=data["nic"].strip() or None,
                notes=data["notes"].strip() or None,
            )
            if result:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to update customer.")

    # ── Delete customer ─────────────────────────────────────────────

    def _on_delete_customer(self):
        """Confirm and soft-delete the selected customer."""
        row = self._table.get_selected_row()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a customer to delete.")
            return
        customer_id = self._table.get_selected_data(0)
        customer_name = self._table.get_selected_data(1)
        if not customer_id:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete customer '{customer_name}'?\n"
            "This will deactivate the customer record.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = self._controller.delete_customer(int(customer_id))
            if success:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete customer.")


# ─── Customer Dialog ────────────────────────────────────────────────

class CustomerDialog(QDialog):
    """Dialog for creating or editing a customer."""

    def __init__(self, parent=None, customer=None):
        super().__init__(parent)

        self._customer = customer
        self._is_edit = customer is not None

        self.setWindowTitle("Edit Customer" if self._is_edit else "Add Customer")
        self.setMinimumWidth(480)
        self.setModal(True)

        # ── Main layout ──
        outer = QVBoxLayout(self)
        outer.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        outer.setSpacing(SPACING_MD)

        # ── Form panel ──
        form = FormPanel("Customer Details")

        # Name *
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Full name *")
        self._name_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Name *", self._name_input)

        # Phone *
        self._phone_input = QLineEdit()
        self._phone_input.setPlaceholderText("Phone number *")
        self._phone_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Phone *", self._phone_input)

        # Email
        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText("Email address")
        self._email_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Email", self._email_input)

        # Address
        self._address_input = QTextEdit()
        self._address_input.setPlaceholderText("Address")
        self._address_input.setFixedHeight(72)
        form.add_row("Address", self._address_input)

        # NIC
        self._nic_input = QLineEdit()
        self._nic_input.setPlaceholderText("NIC / ID number")
        self._nic_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("NIC", self._nic_input)

        form.add_separator()

        # Notes
        self._notes_input = QTextEdit()
        self._notes_input.setPlaceholderText("Additional notes")
        self._notes_input.setFixedHeight(72)
        form.add_row("Notes", self._notes_input)

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
            self._name_input.setText(customer.name or "")
            self._phone_input.setText(customer.phone or "")
            self._email_input.setText(customer.email or "")
            self._address_input.setPlainText(customer.address or "")
            self._nic_input.setText(customer.nic or "")
            self._notes_input.setPlainText(customer.notes or "")

    # ── Private ─────────────────────────────────────────────────────

    def _on_save(self):
        """Validate and accept the dialog."""
        name = self._name_input.text().strip()
        phone = self._phone_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation", "Name is required.")
            self._name_input.setFocus()
            return
        if not phone:
            QMessageBox.warning(self, "Validation", "Phone is required.")
            self._phone_input.setFocus()
            return

        self.accept()

    # ── Public API ──────────────────────────────────────────────────

    def get_data(self) -> dict:
        """Return a dict of all form field values."""
        return {
            "name": self._name_input.text(),
            "phone": self._phone_input.text(),
            "email": self._email_input.text(),
            "address": self._address_input.toPlainText(),
            "nic": self._nic_input.text(),
            "notes": self._notes_input.toPlainText(),
        }
