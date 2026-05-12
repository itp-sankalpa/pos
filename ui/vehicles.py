"""
VehiclesScreen — vehicle management page for the Vehicle Service POS.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QMessageBox,
    QPushButton,
    QSizePolicy,
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
from controllers.vehicle_controller import VehicleController
from controllers.customer_controller import CustomerController


class VehiclesScreen(QWidget):
    """Vehicle management screen with search, table, and CRUD dialogs."""

    def __init__(self, session, stacked_widget=None, parent=None):
        super().__init__(parent)

        self._session = session
        self._stacked_widget = stacked_widget
        self._vehicle_controller = VehicleController()
        self._customer_controller = CustomerController()

        # ── Main layout ──
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # ── Page header ──
        self._header = PageHeader("Vehicles", subtitle="Manage vehicle records")
        self._header.add_action("Add Vehicle", self._on_add_vehicle, "btn_primary")
        layout.addWidget(self._header)

        # ── Search bar ──
        self._search_bar = SearchBar(placeholder="Search by registration, make, or model...")
        self._search_bar.set_search_callback(self._on_search)
        layout.addWidget(self._search_bar)

        # ── Data table ──
        self._table = DataTable(
            columns=[
                ("ID", 50),
                ("Registration", 120),
                ("Make", 100),
                ("Model", 120),
                ("Year", 60),
                ("Color", 80),
                ("Customer", 160),
                ("Phone", 120),
            ]
        )
        self._table.set_double_click_handler(self._on_double_click_row)
        layout.addWidget(self._table, stretch=1)

        # ── Action bar ──
        self._action_bar = ActionBar()
        self._action_bar.add_button("Edit", self._on_edit_vehicle, "btn_secondary")
        self._action_bar.add_button("Delete", self._on_delete_vehicle, "btn_danger")
        layout.addWidget(self._action_bar)

        # ── Initial data load ──
        self.refresh()

    # ── Data loading ────────────────────────────────────────────────

    def refresh(self):
        """Reload vehicle data (with customer names) into the table."""
        vehicles = self._vehicle_controller.get_vehicles()
        rows = []
        for v in vehicles:
            customer_name = ""
            customer_phone = ""
            if v.customer:
                customer_name = v.customer.name or ""
                customer_phone = v.customer.phone or ""
            rows.append([
                v.id,
                v.registration_no or "",
                v.make or "",
                v.model or "",
                v.year or "",
                v.color or "",
                customer_name,
                customer_phone,
            ])
        self._table.load_data(rows)

    # ── Search ──────────────────────────────────────────────────────

    def _on_search(self, text: str):
        """Debounced search callback — filter vehicles and reload table."""
        vehicles = self._vehicle_controller.get_vehicles(search=text.strip() or None)
        rows = []
        for v in vehicles:
            customer_name = ""
            customer_phone = ""
            if v.customer:
                customer_name = v.customer.name or ""
                customer_phone = v.customer.phone or ""
            rows.append([
                v.id,
                v.registration_no or "",
                v.make or "",
                v.model or "",
                v.year or "",
                v.color or "",
                customer_name,
                customer_phone,
            ])
        self._table.load_data(rows)

    # ── Add vehicle ─────────────────────────────────────────────────

    def _on_add_vehicle(self):
        """Open the Add Vehicle dialog."""
        dialog = VehicleDialog(
            customer_controller=self._customer_controller,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["customer_id"]:
                QMessageBox.warning(self, "Validation Error", "Customer is required.")
                return
            if not data["registration_no"].strip():
                QMessageBox.warning(self, "Validation Error", "Registration No is required.")
                return
            kwargs = {}
            if data["make"].strip():
                kwargs["make"] = data["make"].strip()
            if data["model"].strip():
                kwargs["model"] = data["model"].strip()
            if data["year"]:
                kwargs["year"] = data["year"]
            if data["color"].strip():
                kwargs["color"] = data["color"].strip()
            if data["engine_no"].strip():
                kwargs["engine_no"] = data["engine_no"].strip()
            if data["chassis_no"].strip():
                kwargs["chassis_no"] = data["chassis_no"].strip()
            if data["mileage"] is not None:
                kwargs["mileage"] = data["mileage"]
            if data["notes"].strip():
                kwargs["notes"] = data["notes"].strip()

            result = self._vehicle_controller.create_vehicle(
                customer_id=data["customer_id"],
                registration_no=data["registration_no"].strip(),
                **kwargs,
            )
            if result:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to create vehicle.")

    # ── Edit vehicle ────────────────────────────────────────────────

    def _on_edit_vehicle(self):
        """Open the Edit Vehicle dialog for the selected row."""
        row = self._table.get_selected_row()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a vehicle to edit.")
            return
        vehicle_id = self._table.get_selected_data(0)
        if not vehicle_id:
            return
        vehicle = self._vehicle_controller.get_vehicle(int(vehicle_id))
        if not vehicle:
            QMessageBox.critical(self, "Error", "Vehicle not found.")
            return
        self._open_edit_dialog(vehicle)

    def _on_double_click_row(self, row, _col):
        """Double-click handler — open edit dialog for clicked row."""
        item = self._table.item(row, 0)
        if not item:
            return
        vehicle_id = int(item.text())
        vehicle = self._vehicle_controller.get_vehicle(vehicle_id)
        if vehicle:
            self._open_edit_dialog(vehicle)

    def _open_edit_dialog(self, vehicle):
        """Open the Edit Vehicle dialog pre-filled with *vehicle* data."""
        dialog = VehicleDialog(
            customer_controller=self._customer_controller,
            parent=self,
            vehicle=vehicle,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["customer_id"]:
                QMessageBox.warning(self, "Validation Error", "Customer is required.")
                return
            if not data["registration_no"].strip():
                QMessageBox.warning(self, "Validation Error", "Registration No is required.")
                return

            kwargs = {
                "customer_id": data["customer_id"],
                "registration_no": data["registration_no"].strip(),
            }
            if data["make"].strip():
                kwargs["make"] = data["make"].strip()
            else:
                kwargs["make"] = None
            if data["model"].strip():
                kwargs["model"] = data["model"].strip()
            else:
                kwargs["model"] = None
            kwargs["year"] = data["year"] if data["year"] else None
            if data["color"].strip():
                kwargs["color"] = data["color"].strip()
            else:
                kwargs["color"] = None
            if data["engine_no"].strip():
                kwargs["engine_no"] = data["engine_no"].strip()
            else:
                kwargs["engine_no"] = None
            if data["chassis_no"].strip():
                kwargs["chassis_no"] = data["chassis_no"].strip()
            else:
                kwargs["chassis_no"] = None
            kwargs["mileage"] = data["mileage"] if data["mileage"] is not None else None
            if data["notes"].strip():
                kwargs["notes"] = data["notes"].strip()
            else:
                kwargs["notes"] = None

            result = self._vehicle_controller.update_vehicle(vehicle.id, **kwargs)
            if result:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to update vehicle.")

    # ── Delete vehicle ──────────────────────────────────────────────

    def _on_delete_vehicle(self):
        """Confirm and delete the selected vehicle."""
        row = self._table.get_selected_row()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a vehicle to delete.")
            return
        vehicle_id = self._table.get_selected_data(0)
        vehicle_reg = self._table.get_selected_data(1)
        if not vehicle_id:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete vehicle '{vehicle_reg}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = self._vehicle_controller.delete_vehicle(int(vehicle_id))
            if success:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete vehicle.")


# ─── Vehicle Dialog ─────────────────────────────────────────────────

class VehicleDialog(QDialog):
    """Dialog for creating or editing a vehicle, with inline customer creation."""

    def __init__(self, customer_controller, parent=None, vehicle=None):
        super().__init__(parent)

        self._customer_controller = customer_controller
        self._vehicle = vehicle
        self._is_edit = vehicle is not None

        self.setWindowTitle("Edit Vehicle" if self._is_edit else "Add Vehicle")
        self.setMinimumWidth(520)
        self.setModal(True)

        # ── Main layout ──
        outer = QVBoxLayout(self)
        outer.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        outer.setSpacing(SPACING_MD)

        # ── Form panel ──
        form = FormPanel("Vehicle Details")

        # ── Customer selector row: combo + Add New button ──
        customer_row = QHBoxLayout()
        customer_row.setSpacing(SPACING_SM)

        self._customer_combo = QComboBox()
        self._customer_combo.setFixedHeight(INPUT_HEIGHT)
        self._customer_combo.setMinimumWidth(280)
        self._customer_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        customer_row.addWidget(self._customer_combo, stretch=1)

        add_customer_btn = QPushButton("+ New")
        add_customer_btn.setObjectName("btn_secondary")
        add_customer_btn.setFixedSize(BUTTON_HEIGHT, BUTTON_HEIGHT)
        add_customer_btn.setToolTip("Add a new customer inline")
        add_customer_btn.clicked.connect(self._toggle_inline_customer_form)
        customer_row.addWidget(add_customer_btn)

        form.add_row("Customer *", customer_row)

        # ── Inline customer creation panel (hidden by default) ──
        self._inline_customer_panel = QWidget()
        inline_layout = QVBoxLayout(self._inline_customer_panel)
        inline_layout.setContentsMargins(0, SPACING_XS, 0, 0)
        inline_layout.setSpacing(SPACING_XS)

        inline_header = QLabel("New Customer")
        inline_header.setStyleSheet(
            f"font-size: {FONT_SMALL}px; font-weight: bold; color: {COLOR_ACCENT}; "
            f"background: transparent; border: none;"
        )
        inline_layout.addWidget(inline_header)

        # Name
        name_row = QHBoxLayout()
        name_row.setSpacing(SPACING_SM)
        name_label = QLabel("Name *")
        name_label.setFixedWidth(80)
        name_label.setStyleSheet(
            f"color: {COLOR_TEXT_SECONDARY}; font-size: {FONT_SMALL}px; "
            f"background: transparent; border: none;"
        )
        self._inline_name = QLineEdit()
        self._inline_name.setPlaceholderText("Full name *")
        self._inline_name.setFixedHeight(INPUT_HEIGHT)
        name_row.addWidget(name_label)
        name_row.addWidget(self._inline_name, stretch=1)
        inline_layout.addLayout(name_row)

        # Phone
        phone_row = QHBoxLayout()
        phone_row.setSpacing(SPACING_SM)
        phone_label = QLabel("Phone *")
        phone_label.setFixedWidth(80)
        phone_label.setStyleSheet(
            f"color: {COLOR_TEXT_SECONDARY}; font-size: {FONT_SMALL}px; "
            f"background: transparent; border: none;"
        )
        self._inline_phone = QLineEdit()
        self._inline_phone.setPlaceholderText("Phone number *")
        self._inline_phone.setFixedHeight(INPUT_HEIGHT)
        phone_row.addWidget(phone_label)
        phone_row.addWidget(self._inline_phone, stretch=1)
        inline_layout.addLayout(phone_row)

        # Save inline customer button
        inline_btn_row = QHBoxLayout()
        inline_btn_row.addStretch()
        self._inline_save_btn = QPushButton("Save Customer")
        self._inline_save_btn.setObjectName("btn_success")
        self._inline_save_btn.setFixedHeight(BUTTON_HEIGHT - 4)
        self._inline_save_btn.setMinimumWidth(110)
        self._inline_save_btn.setStyleSheet(
            f"font-size: {FONT_SMALL}px; font-weight: bold;"
        )
        self._inline_save_btn.clicked.connect(self._save_inline_customer)
        inline_btn_row.addWidget(self._inline_save_btn)
        inline_layout.addLayout(inline_btn_row)

        self._inline_customer_panel.setVisible(False)
        form.add_row("", self._inline_customer_panel)

        form.add_separator()

        # Registration No *
        self._reg_input = QLineEdit()
        self._reg_input.setPlaceholderText("Registration number *")
        self._reg_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Registration No *", self._reg_input)

        # Make
        self._make_input = QLineEdit()
        self._make_input.setPlaceholderText("e.g. Toyota")
        self._make_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Make", self._make_input)

        # Model
        self._model_input = QLineEdit()
        self._model_input.setPlaceholderText("e.g. Corolla")
        self._model_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Model", self._model_input)

        # Year
        self._year_spin = QSpinBox()
        self._year_spin.setRange(1900, 2030)
        self._year_spin.setValue(2024)
        self._year_spin.setFixedHeight(INPUT_HEIGHT)
        self._year_spin.setPrefix("")
        form.add_row("Year", self._year_spin)

        # Color
        self._color_input = QLineEdit()
        self._color_input.setPlaceholderText("e.g. Silver")
        self._color_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Color", self._color_input)

        form.add_separator()

        # Engine No
        self._engine_input = QLineEdit()
        self._engine_input.setPlaceholderText("Engine number")
        self._engine_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Engine No", self._engine_input)

        # Chassis No
        self._chassis_input = QLineEdit()
        self._chassis_input.setPlaceholderText("Chassis number")
        self._chassis_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Chassis No", self._chassis_input)

        # Mileage
        self._mileage_spin = QSpinBox()
        self._mileage_spin.setRange(0, 9_999_999)
        self._mileage_spin.setValue(0)
        self._mileage_spin.setFixedHeight(INPUT_HEIGHT)
        self._mileage_spin.setSuffix(" km")
        form.add_row("Mileage", self._mileage_spin)

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

        # ── Populate customer combo ──
        self._load_customers()

        # ── Pre-fill for edit ──
        if self._is_edit:
            self._reg_input.setText(vehicle.registration_no or "")
            self._make_input.setText(vehicle.make or "")
            self._model_input.setText(vehicle.model or "")
            if vehicle.year:
                self._year_spin.setValue(vehicle.year)
            else:
                self._year_spin.setValue(1900)
            self._color_input.setText(vehicle.color or "")
            self._engine_input.setText(vehicle.engine_no or "")
            self._chassis_input.setText(vehicle.chassis_no or "")
            if vehicle.mileage is not None:
                self._mileage_spin.setValue(vehicle.mileage)
            self._notes_input.setPlainText(vehicle.notes or "")
            # Select the current customer in the combo
            if vehicle.customer_id:
                self._select_customer_by_id(vehicle.customer_id)

    # ── Customer combo helpers ──────────────────────────────────────

    def _load_customers(self):
        """Populate the customer combo box with all active customers."""
        self._customer_combo.clear()
        self._customer_combo.addItem("-- Select Customer --", userData=None)
        customers = self._customer_controller.get_customers()
        for c in customers:
            display = f"{c.name}  ({c.phone})"
            self._customer_combo.addItem(display, userData=c.id)

    def _select_customer_by_id(self, customer_id: int):
        """Select the combo item matching *customer_id*."""
        for i in range(self._customer_combo.count()):
            if self._customer_combo.itemData(i) == customer_id:
                self._customer_combo.setCurrentIndex(i)
                return
        # Not found — reload and try again
        self._load_customers()
        for i in range(self._customer_combo.count()):
            if self._customer_combo.itemData(i) == customer_id:
                self._customer_combo.setCurrentIndex(i)
                return

    # ── Inline customer creation ────────────────────────────────────

    def _toggle_inline_customer_form(self):
        """Show or hide the inline customer creation form."""
        visible = self._inline_customer_panel.isVisible()
        self._inline_customer_panel.setVisible(not visible)
        if not visible:
            self._inline_name.setFocus()

    def _save_inline_customer(self):
        """Create a new customer from the inline form and auto-select them."""
        name = self._inline_name.text().strip()
        phone = self._inline_phone.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation", "Customer name is required.")
            self._inline_name.setFocus()
            return
        if not phone:
            QMessageBox.warning(self, "Validation", "Customer phone is required.")
            self._inline_phone.setFocus()
            return

        customer = self._customer_controller.create_customer(
            name=name,
            phone=phone,
        )
        if not customer:
            QMessageBox.critical(self, "Error", "Failed to create customer.")
            return

        # Reload combo and select the new customer
        self._load_customers()
        self._select_customer_by_id(customer.id)

        # Clear inline form and hide it
        self._inline_name.clear()
        self._inline_phone.clear()
        self._inline_customer_panel.setVisible(False)

    # ── Save vehicle ────────────────────────────────────────────────

    def _on_save(self):
        """Validate and accept the dialog."""
        customer_id = self._customer_combo.currentData()
        reg_no = self._reg_input.text().strip()

        if not customer_id:
            QMessageBox.warning(self, "Validation", "Please select a customer.")
            return
        if not reg_no:
            QMessageBox.warning(self, "Validation", "Registration No is required.")
            self._reg_input.setFocus()
            return

        self.accept()

    # ── Public API ──────────────────────────────────────────────────

    def get_data(self) -> dict:
        """Return a dict of all form field values."""
        year_val = self._year_spin.value()
        # If year is still at the minimum and user never changed it, treat as None
        # (but allow 1900 if that's genuinely intended)
        year = year_val if self._year_spin.value() > 1900 else None

        mileage_val = self._mileage_spin.value()

        return {
            "customer_id": self._customer_combo.currentData(),
            "registration_no": self._reg_input.text(),
            "make": self._make_input.text(),
            "model": self._model_input.text(),
            "year": year,
            "color": self._color_input.text(),
            "engine_no": self._engine_input.text(),
            "chassis_no": self._chassis_input.text(),
            "mileage": mileage_val if mileage_val > 0 else None,
            "notes": self._notes_input.toPlainText(),
        }
