"""
JobCardsScreen — Track and manage service/repair job cards.

Provides listing, creation, editing, status updates, and deletion
of job cards for the Vehicle Service Center POS.
"""

import logging
from datetime import datetime
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTextEdit,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QSizePolicy,
    QMessageBox,
    QSplitter,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

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
    COLOR_SELECTED_ROW_BG,
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
    SPACING_XL,
    BUTTON_HEIGHT,
    INPUT_HEIGHT,
    status_badge_qss,
)
from ui.components import (
    PageHeader,
    SearchBar,
    DataTable,
    FormPanel,
    StatusBadge,
    ActionBar,
)
from controllers.job_card_controller import JobCardController
from controllers.vehicle_controller import VehicleController
from controllers.customer_controller import CustomerController
from controllers.inventory_controller import InventoryController
from controllers.staff_controller import StaffController
from config import cents_to_display, display_to_cents, JOB_CARD_PREFIX

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
#  Main Screen
# ═══════════════════════════════════════════════════════════════════

class JobCardsScreen(QWidget):
    """Job Cards listing screen with CRUD operations."""

    def __init__(self, session, stacked_widget=None, parent=None):
        super().__init__(parent)

        self._session = session
        self._stacked_widget = stacked_widget

        # Controllers
        self._jc_ctrl = JobCardController()
        self._veh_ctrl = VehicleController()
        self._cust_ctrl = CustomerController()
        self._inv_ctrl = InventoryController()
        self._staff_ctrl = StaffController()

        # Current filter state
        self._current_search = ""
        self._current_status_filter = "All"

        self._build_ui()
        self.refresh()

    # ── UI Construction ──────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # ── Header ──
        self._header = PageHeader(
            "Job Cards", subtitle="Track and manage service/repair jobs"
        )
        self._header.add_action(
            "New Job Card", self._on_new_job_card, "btn_primary"
        )
        layout.addWidget(self._header)

        # ── Search bar ──
        self._search_bar = SearchBar(
            placeholder="Search job cards…",
            filters=["All", "Pending", "In Progress", "Completed", "Cancelled"],
        )
        self._search_bar.set_search_callback(self._on_search)
        self._search_bar.set_filter_callback(self._on_filter)
        layout.addWidget(self._search_bar)

        # ── Data table ──
        self._table = DataTable(
            columns=[
                ("Job #", 100),
                ("Vehicle", 120),
                ("Customer", 150),
                ("Mechanic", 120),
                ("Status", 100),
                ("Complaint", 200),
                ("Labor", 90),
                ("Total", 100),
                ("Created", 100),
            ]
        )
        self._table.set_double_click_handler(self._on_double_click)
        layout.addWidget(self._table, stretch=1)

        # ── Action bar ──
        self._action_bar = ActionBar()
        self._action_bar.add_button(
            "Edit", self._on_edit, "btn_secondary"
        )
        self._action_bar.add_button(
            "Update Status", self._on_update_status, "btn_secondary"
        )
        self._action_bar.add_button(
            "Delete", self._on_delete, "btn_danger"
        )
        layout.addWidget(self._action_bar)

    # ── Data Loading ─────────────────────────────────────────────

    def refresh(self):
        """Reload job cards data into the table."""
        status = None
        if self._current_status_filter and self._current_status_filter != "All":
            status = self._current_status_filter.upper().replace(" ", "_")

        search = self._current_search or None

        try:
            job_cards = self._jc_ctrl.get_job_cards(status=status, search=search)
        except Exception:
            logger.exception("Error loading job cards")
            job_cards = []

        rows = []
        for jc in job_cards:
            vehicle_display = ""
            if jc.vehicle:
                vehicle_display = jc.vehicle.registration_no or ""

            customer_display = ""
            if jc.customer_obj:
                customer_display = jc.customer_obj.name or ""

            mechanic_display = ""
            if jc.assigned_mechanic_obj:
                mechanic_display = jc.assigned_mechanic_obj.full_name or ""

            status_text = jc.status or ""
            complaint_text = (jc.complaint or "")[:50]
            labor_display = cents_to_display(jc.labor_charge_cents or 0)
            total_display = cents_to_display(jc.total_cents or 0)

            created_display = ""
            if jc.created_at:
                created_display = jc.created_at.strftime("%Y-%m-%d")

            rows.append([
                jc.job_number or "",
                vehicle_display,
                customer_display,
                mechanic_display,
                status_text,
                complaint_text,
                labor_display,
                total_display,
                created_display,
            ])

        self._table.load_data(rows)

        # Insert StatusBadge widgets into the Status column (col 4)
        for row_idx, jc in enumerate(job_cards):
            status_text = jc.status or ""
            badge = StatusBadge(status_text)
            self._table.setCellWidget(row_idx, 4, badge)

        # Store full job card objects for selection lookup
        self._job_cards_data = job_cards

    # ── Selection Helpers ────────────────────────────────────────

    def _get_selected_job_card(self):
        """Return the JobCard object for the currently selected row, or None."""
        row = self._table.get_selected_row()
        if row < 0 or row >= len(self._job_cards_data):
            return None
        return self._job_cards_data[row]

    # ── Search / Filter Callbacks ────────────────────────────────

    def _on_search(self, text: str):
        self._current_search = text
        self.refresh()

    def _on_filter(self, filter_text: str):
        self._current_status_filter = filter_text
        self.refresh()

    # ── Double-click ─────────────────────────────────────────────

    def _on_double_click(self, row, col):
        jc = self._get_selected_job_card()
        if jc:
            self._open_edit_dialog(jc)

    # ── Action Handlers ──────────────────────────────────────────

    def _on_new_job_card(self):
        dlg = JobCardDialog(
            session=self._session,
            jc_ctrl=self._jc_ctrl,
            veh_ctrl=self._veh_ctrl,
            cust_ctrl=self._cust_ctrl,
            inv_ctrl=self._inv_ctrl,
            staff_ctrl=self._staff_ctrl,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_edit(self):
        jc = self._get_selected_job_card()
        if not jc:
            QMessageBox.information(self, "No Selection", "Please select a job card to edit.")
            return
        self._open_edit_dialog(jc)

    def _open_edit_dialog(self, jc):
        dlg = JobCardDialog(
            session=self._session,
            jc_ctrl=self._jc_ctrl,
            veh_ctrl=self._veh_ctrl,
            cust_ctrl=self._cust_ctrl,
            inv_ctrl=self._inv_ctrl,
            staff_ctrl=self._staff_ctrl,
            job_card=jc,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_update_status(self):
        jc = self._get_selected_job_card()
        if not jc:
            QMessageBox.information(self, "No Selection", "Please select a job card to update status.")
            return
        dlg = UpdateStatusDialog(job_card=jc, jc_ctrl=self._jc_ctrl, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_delete(self):
        jc = self._get_selected_job_card()
        if not jc:
            QMessageBox.information(self, "No Selection", "Please select a job card to delete.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete job card <b>{jc.job_number}</b>?\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Delete items first, then the job card
                for item in jc.items:
                    self._jc_ctrl.remove_job_card_item(item.id)
                self._jc_ctrl.update_job_card(jc.id, status="CANCELLED")
                self.refresh()
            except Exception:
                logger.exception("Error deleting job card")
                QMessageBox.critical(self, "Error", "Failed to delete job card.")


# ═══════════════════════════════════════════════════════════════════
#  Job Card Dialog (New / Edit)
# ═══════════════════════════════════════════════════════════════════

class JobCardDialog(QDialog):
    """Dialog for creating or editing a job card."""

    def __init__(
        self,
        session,
        jc_ctrl: JobCardController,
        veh_ctrl: VehicleController,
        cust_ctrl: CustomerController,
        inv_ctrl: InventoryController,
        staff_ctrl: StaffController,
        job_card=None,
        parent=None,
    ):
        super().__init__(parent)
        self._session = session
        self._jc_ctrl = jc_ctrl
        self._veh_ctrl = veh_ctrl
        self._cust_ctrl = cust_ctrl
        self._inv_ctrl = inv_ctrl
        self._staff_ctrl = staff_ctrl
        self._job_card = job_card  # None = new, otherwise edit
        self._is_edit = job_card is not None

        # Item data for the items table (list of dicts)
        self._items_data: List[dict] = []

        # Cache for lookups
        self._customers_cache: List = []
        self._vehicles_cache: List = []
        self._mechanics_cache: List = []
        self._inventory_cache: List = []

        self._build_ui()
        self._load_initial_data()

        if self._is_edit:
            self._populate_for_edit()
            self.setWindowTitle(f"Edit Job Card — {self._job_card.job_number}")
        else:
            self.setWindowTitle("New Job Card")

        self.setMinimumWidth(780)
        self.setMinimumHeight(640)

    # ── UI Construction ──────────────────────────────────────────

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        main_layout.setSpacing(SPACING_MD)

        # ── Top section: Customer + Vehicle selection ──
        top_group = QGroupBox("Customer & Vehicle")
        top_group.setStyleSheet(
            f"QGroupBox {{ font-weight: bold; font-size: {FONT_SECTION_TITLE}px; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; "
            f"margin-top: 12px; padding-top: 18px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; "
            f"padding: 0 8px; color: {COLOR_TEXT_PRIMARY}; }}"
        )
        top_form = QFormLayout(top_group)
        top_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top_form.setHorizontalSpacing(SPACING_MD)
        top_form.setVerticalSpacing(SPACING_XS)

        # Customer row with combo + New Customer button
        cust_row = QHBoxLayout()
        cust_row.setSpacing(SPACING_SM)
        self._customer_combo = QComboBox()
        self._customer_combo.setMinimumWidth(300)
        self._customer_combo.currentIndexChanged.connect(self._on_customer_changed)
        cust_row.addWidget(self._customer_combo, stretch=1)

        self._btn_new_customer = QPushButton("New Customer")
        self._btn_new_customer.setObjectName("btn_secondary")
        self._btn_new_customer.setFixedHeight(BUTTON_HEIGHT)
        self._btn_new_customer.clicked.connect(self._on_new_customer_inline)
        cust_row.addWidget(self._btn_new_customer)
        top_form.addRow("Customer:", cust_row)

        # Vehicle combo (filtered by selected customer)
        self._vehicle_combo = QComboBox()
        self._vehicle_combo.setMinimumWidth(300)
        top_form.addRow("Vehicle:", self._vehicle_combo)

        main_layout.addWidget(top_group)

        # ── Middle section: Form fields ──
        form_group = QGroupBox("Details")
        form_group.setStyleSheet(
            f"QGroupBox {{ font-weight: bold; font-size: {FONT_SECTION_TITLE}px; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; "
            f"margin-top: 12px; padding-top: 18px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; "
            f"padding: 0 8px; color: {COLOR_TEXT_PRIMARY}; }}"
        )
        form_layout = QFormLayout(form_group)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setHorizontalSpacing(SPACING_MD)
        form_layout.setVerticalSpacing(SPACING_XS)

        self._complaint_edit = QTextEdit()
        self._complaint_edit.setFixedHeight(70)
        self._complaint_edit.setPlaceholderText("Describe the customer's complaint…")
        form_layout.addRow("Complaint:", self._complaint_edit)

        self._mechanic_combo = QComboBox()
        self._mechanic_combo.setMinimumWidth(250)
        form_layout.addRow("Assigned Mechanic:", self._mechanic_combo)

        self._mileage_in_spin = QSpinBox()
        self._mileage_in_spin.setRange(0, 9999999)
        self._mileage_in_spin.setSuffix(" km")
        self._mileage_in_spin.setFixedHeight(INPUT_HEIGHT)
        form_layout.addRow("Mileage In:", self._mileage_in_spin)

        main_layout.addWidget(form_group)

        # ── Items section ──
        items_group = QGroupBox("Items (Parts / Services / Labor)")
        items_group.setStyleSheet(
            f"QGroupBox {{ font-weight: bold; font-size: {FONT_SECTION_TITLE}px; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; "
            f"margin-top: 12px; padding-top: 18px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; "
            f"padding: 0 8px; color: {COLOR_TEXT_PRIMARY}; }}"
        )
        items_layout = QVBoxLayout(items_group)
        items_layout.setSpacing(SPACING_SM)

        # Items toolbar
        items_toolbar = QHBoxLayout()
        items_toolbar.setSpacing(SPACING_SM)

        # Inventory picker
        items_toolbar.addWidget(QLabel("From Inventory:"))
        self._inventory_combo = QComboBox()
        self._inventory_combo.setMinimumWidth(250)
        self._inventory_combo.currentIndexChanged.connect(self._on_inventory_selected)
        items_toolbar.addWidget(self._inventory_combo, stretch=1)

        self._btn_add_inventory = QPushButton("Add from Inventory")
        self._btn_add_inventory.setObjectName("btn_secondary")
        self._btn_add_inventory.setFixedHeight(BUTTON_HEIGHT)
        self._btn_add_inventory.clicked.connect(self._on_add_inventory_item)
        items_toolbar.addWidget(self._btn_add_inventory)

        self._btn_add_custom = QPushButton("Add Custom Item")
        self._btn_add_custom.setObjectName("btn_secondary")
        self._btn_add_custom.setFixedHeight(BUTTON_HEIGHT)
        self._btn_add_custom.clicked.connect(self._on_add_custom_item)
        items_toolbar.addWidget(self._btn_add_custom)

        items_toolbar.addStretch()
        items_layout.addLayout(items_toolbar)

        # Items table
        self._items_table = QTableWidget(0, 6)
        self._items_table.setHorizontalHeaderLabels(
            ["Description", "Type", "Qty", "Unit Price", "Line Total", ""]
        )
        self._items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._items_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._items_table.setAlternatingRowColors(True)
        self._items_table.verticalHeader().setVisible(False)
        self._items_table.setMinimumHeight(120)

        header = self._items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._items_table.setColumnWidth(1, 80)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._items_table.setColumnWidth(2, 60)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._items_table.setColumnWidth(3, 110)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._items_table.setColumnWidth(4, 110)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._items_table.setColumnWidth(5, 60)

        items_layout.addWidget(self._items_table)

        main_layout.addWidget(items_group, stretch=1)

        # ── Bottom section: Labor charge + Summary ──
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(SPACING_LG)

        # Labor charge
        labor_form = QFormLayout()
        labor_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        labor_form.setHorizontalSpacing(SPACING_SM)

        self._labor_input = QDoubleSpinBox()
        self._labor_input.setRange(0, 9999999.99)
        self._labor_input.setDecimals(2)
        self._labor_input.setPrefix("Rs. ")
        self._labor_input.setFixedHeight(INPUT_HEIGHT)
        self._labor_input.valueChanged.connect(self._recalculate_totals)
        labor_form.addRow("Labor Charge:", self._labor_input)

        bottom_row.addLayout(labor_form)

        # Spacer
        bottom_row.addStretch()

        # Summary panel
        summary_frame = QFrame()
        summary_frame.setObjectName("panel")
        summary_frame.setStyleSheet(
            f"QFrame#panel {{ background-color: {COLOR_PANEL_BG}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; "
            f"padding: {SPACING_SM}px; }}"
        )
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(SPACING_MD, SPACING_SM, SPACING_MD, SPACING_SM)
        summary_layout.setSpacing(SPACING_XS)

        self._subtotal_label = QLabel("Subtotal: Rs. 0.00")
        self._subtotal_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_SECONDARY};"
        )
        summary_layout.addWidget(self._subtotal_label)

        self._labor_label = QLabel("Labor: Rs. 0.00")
        self._labor_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_SECONDARY};"
        )
        summary_layout.addWidget(self._labor_label)

        self._total_label = QLabel("Total: Rs. 0.00")
        self._total_label.setStyleSheet(
            f"font-size: {FONT_PAGE_TITLE}px; font-weight: bold; "
            f"color: {COLOR_TEXT_PRIMARY};"
        )
        summary_layout.addWidget(self._total_label)

        bottom_row.addWidget(summary_frame)
        main_layout.addLayout(bottom_row)

        # ── Dialog buttons ──
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.button(QDialogButtonBox.StandardButton.Save).setText("Save Job Card")
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box)

    # ── Data Loading ─────────────────────────────────────────────

    def _load_initial_data(self):
        """Load customers, mechanics, and inventory into combos."""
        # Customers
        try:
            self._customers_cache = self._cust_ctrl.get_customers()
        except Exception:
            logger.exception("Error loading customers")
            self._customers_cache = []

        self._customer_combo.blockSignals(True)
        self._customer_combo.clear()
        self._customer_combo.addItem("— Select Customer —", None)
        for c in self._customers_cache:
            self._customer_combo.addItem(f"{c.name} ({c.phone})", c.id)
        self._customer_combo.blockSignals(False)

        # Mechanics (staff with MECHANIC role, or all staff)
        try:
            all_staff = self._staff_ctrl.get_all_staff()
            self._mechanics_cache = [
                s for s in all_staff if s.is_active
            ]
        except Exception:
            logger.exception("Error loading staff")
            self._mechanics_cache = []

        self._mechanic_combo.clear()
        self._mechanic_combo.addItem("— Unassigned —", None)
        for m in self._mechanics_cache:
            self._mechanic_combo.addItem(m.full_name, m.id)

        # Inventory items
        try:
            self._inventory_cache = self._inv_ctrl.get_items()
        except Exception:
            logger.exception("Error loading inventory")
            self._inventory_cache = []

        self._inventory_combo.clear()
        self._inventory_combo.addItem("— Select Item —", None)
        for inv in self._inventory_cache:
            price = cents_to_display(inv.sell_price_cents)
            self._inventory_combo.addItem(
                f"{inv.name} ({inv.item_code}) — {price}",
                inv.id,
            )

        # Vehicles: initially empty until customer is selected
        self._vehicle_combo.clear()
        self._vehicle_combo.addItem("— Select Vehicle —", None)

    # ── Customer changed → refresh vehicles ──────────────────────

    def _on_customer_changed(self, index: int):
        cust_id = self._customer_combo.currentData()
        self._load_vehicles_for_customer(cust_id)

    def _load_vehicles_for_customer(self, customer_id):
        self._vehicle_combo.clear()
        self._vehicle_combo.addItem("— Select Vehicle —", None)
        self._vehicles_cache = []

        if not customer_id:
            return

        try:
            self._vehicles_cache = self._veh_ctrl.get_vehicles_by_customer(customer_id)
        except Exception:
            logger.exception("Error loading vehicles for customer %s", customer_id)
            self._vehicles_cache = []

        for v in self._vehicles_cache:
            label = v.registration_no
            if v.make or v.model:
                label += f" — {v.make or ''} {v.model or ''}".strip()
            self._vehicle_combo.addItem(label, v.id)

    # ── Inventory selection auto-fill ────────────────────────────

    def _on_inventory_selected(self, index: int):
        """Just a hook — the actual logic is in _on_add_inventory_item."""
        pass

    # ── Add items ────────────────────────────────────────────────

    def _on_add_inventory_item(self):
        """Add a selected inventory item to the items table."""
        inv_id = self._inventory_combo.currentData()
        if not inv_id:
            QMessageBox.information(self, "No Item", "Please select an inventory item first.")
            return

        inv_item = None
        for inv in self._inventory_cache:
            if inv.id == inv_id:
                inv_item = inv
                break

        if not inv_item:
            return

        # Check if already added
        for existing in self._items_data:
            if existing.get("inventory_item_id") == inv_id:
                QMessageBox.information(
                    self, "Already Added",
                    f"'{inv_item.name}' is already in the items list."
                )
                return

        item_dict = {
            "description": inv_item.name,
            "item_type": "PART",
            "quantity": 1,
            "unit_price_cents": inv_item.sell_price_cents,
            "line_total_cents": inv_item.sell_price_cents,
            "inventory_item_id": inv_id,
        }
        self._items_data.append(item_dict)
        self._refresh_items_table()
        self._recalculate_totals()

        # Reset inventory combo
        self._inventory_combo.setCurrentIndex(0)

    def _on_add_custom_item(self):
        """Open a sub-dialog to add a custom line item."""
        dlg = CustomItemDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item_dict = dlg.get_item_data()
            self._items_data.append(item_dict)
            self._refresh_items_table()
            self._recalculate_totals()

    def _on_remove_item(self):
        """Remove the selected item from the items table."""
        row = self._items_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select an item to remove.")
            return

        if 0 <= row < len(self._items_data):
            del self._items_data[row]
            self._refresh_items_table()
            self._recalculate_totals()

    # ── Items table refresh ──────────────────────────────────────

    def _refresh_items_table(self):
        self._items_table.setRowCount(0)
        for i, item in enumerate(self._items_data):
            row = self._items_table.rowCount()
            self._items_table.insertRow(row)

            desc_item = QTableWidgetItem(item.get("description", ""))
            desc_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._items_table.setItem(row, 0, desc_item)

            type_item = QTableWidgetItem(item.get("item_type", "PART"))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self._items_table.setItem(row, 1, type_item)

            qty_item = QTableWidgetItem(str(item.get("quantity", 1)))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self._items_table.setItem(row, 2, qty_item)

            unit_price = cents_to_display(item.get("unit_price_cents", 0))
            price_item = QTableWidgetItem(unit_price)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._items_table.setItem(row, 3, price_item)

            line_total = cents_to_display(item.get("line_total_cents", 0))
            total_item = QTableWidgetItem(line_total)
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._items_table.setItem(row, 4, total_item)

            # Remove button
            remove_btn = QPushButton("✕")
            remove_btn.setObjectName("btn_danger")
            remove_btn.setFixedSize(30, 26)
            remove_btn.setToolTip("Remove this item")
            # Capture index via default argument
            remove_btn.clicked.connect(lambda checked, idx=i: self._remove_item_at(idx))
            self._items_table.setCellWidget(row, 5, remove_btn)

    def _remove_item_at(self, index: int):
        """Remove item at the given index from _items_data."""
        if 0 <= index < len(self._items_data):
            del self._items_data[index]
            self._refresh_items_table()
            self._recalculate_totals()

    # ── Totals ───────────────────────────────────────────────────

    def _recalculate_totals(self):
        subtotal = sum(item.get("line_total_cents", 0) for item in self._items_data)
        labor_cents = int(round(self._labor_input.value() * 100))
        total = subtotal + labor_cents

        self._subtotal_label.setText(f"Subtotal: {cents_to_display(subtotal)}")
        self._labor_label.setText(f"Labor: {cents_to_display(labor_cents)}")
        self._total_label.setText(f"Total: {cents_to_display(total)}")

    # ── Inline New Customer ──────────────────────────────────────

    def _on_new_customer_inline(self):
        """Open a compact dialog to quickly create a customer."""
        dlg = InlineCustomerDialog(cust_ctrl=self._cust_ctrl, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_cust = dlg.get_created_customer()
            if new_cust:
                # Reload customer combo and select the new one
                try:
                    self._customers_cache = self._cust_ctrl.get_customers()
                except Exception:
                    self._customers_cache = []

                self._customer_combo.blockSignals(True)
                self._customer_combo.clear()
                self._customer_combo.addItem("— Select Customer —", None)
                for c in self._customers_cache:
                    self._customer_combo.addItem(f"{c.name} ({c.phone})", c.id)
                self._customer_combo.blockSignals(False)

                # Select the new customer
                idx = self._customer_combo.findData(new_cust.id)
                if idx >= 0:
                    self._customer_combo.setCurrentIndex(idx)
                    self._on_customer_changed(idx)

    # ── Populate for Edit ────────────────────────────────────────

    def _populate_for_edit(self):
        jc = self._job_card
        if not jc:
            return

        # Select customer
        if jc.customer_id:
            idx = self._customer_combo.findData(jc.customer_id)
            if idx >= 0:
                self._customer_combo.setCurrentIndex(idx)
                self._load_vehicles_for_customer(jc.customer_id)

        # Select vehicle
        if jc.vehicle_id:
            idx = self._vehicle_combo.findData(jc.vehicle_id)
            if idx >= 0:
                self._vehicle_combo.setCurrentIndex(idx)

        # Complaint
        if jc.complaint:
            self._complaint_edit.setPlainText(jc.complaint)

        # Mechanic
        if jc.assigned_mechanic:
            idx = self._mechanic_combo.findData(jc.assigned_mechanic)
            if idx >= 0:
                self._mechanic_combo.setCurrentIndex(idx)

        # Mileage in
        if jc.mileage_in is not None:
            self._mileage_in_spin.setValue(jc.mileage_in)

        # Labor charge
        labor_value = (jc.labor_charge_cents or 0) / 100.0
        self._labor_input.setValue(labor_value)

        # Items
        self._items_data = []
        for item in jc.items:
            self._items_data.append({
                "id": item.id,
                "description": item.description,
                "item_type": item.item_type,
                "quantity": item.quantity,
                "unit_price_cents": item.unit_price_cents,
                "line_total_cents": item.line_total_cents,
                "inventory_item_id": item.inventory_item_id,
            })
        self._refresh_items_table()
        self._recalculate_totals()

    # ── Save ─────────────────────────────────────────────────────

    def _on_save(self):
        # Validate
        customer_id = self._customer_combo.currentData()
        vehicle_id = self._vehicle_combo.currentData()

        if not customer_id:
            QMessageBox.warning(self, "Validation", "Please select a customer.")
            return
        if not vehicle_id:
            QMessageBox.warning(self, "Validation", "Please select a vehicle.")
            return

        complaint = self._complaint_edit.toPlainText().strip()
        mechanic_id = self._mechanic_combo.currentData()
        mileage_in = self._mileage_in_spin.value() or None
        labor_cents = int(round(self._labor_input.value() * 100))

        try:
            if self._is_edit:
                # Update existing job card
                self._jc_ctrl.update_job_card(
                    self._job_card.id,
                    vehicle_id=vehicle_id,
                    customer_id=customer_id,
                    complaint=complaint,
                    assigned_mechanic=mechanic_id,
                    mileage_in=mileage_in,
                    labor_charge_cents=labor_cents,
                )

                # Remove items that were deleted
                existing_ids = {item.get("id") for item in self._items_data if item.get("id")}
                for old_item in self._job_card.items:
                    if old_item.id not in existing_ids:
                        self._jc_ctrl.remove_job_card_item(old_item.id)

                # Add/update items
                for item_data in self._items_data:
                    if item_data.get("id"):
                        # Item already exists — remove and re-add for simplicity
                        self._jc_ctrl.remove_job_card_item(item_data["id"])
                        self._jc_ctrl.add_job_card_item(
                            job_card_id=self._job_card.id,
                            description=item_data["description"],
                            quantity=item_data["quantity"],
                            unit_price_cents=item_data["unit_price_cents"],
                            item_type=item_data["item_type"],
                            inventory_item_id=item_data.get("inventory_item_id"),
                        )
                    else:
                        # New item
                        self._jc_ctrl.add_job_card_item(
                            job_card_id=self._job_card.id,
                            description=item_data["description"],
                            quantity=item_data["quantity"],
                            unit_price_cents=item_data["unit_price_cents"],
                            item_type=item_data["item_type"],
                            inventory_item_id=item_data.get("inventory_item_id"),
                        )
            else:
                # Create new job card
                new_jc = self._jc_ctrl.create_job_card(
                    vehicle_id=vehicle_id,
                    customer_id=customer_id,
                    complaint=complaint,
                    assigned_mechanic=mechanic_id,
                    mileage_in=mileage_in,
                    labor_charge_cents=labor_cents,
                )

                if not new_jc:
                    QMessageBox.critical(self, "Error", "Failed to create job card.")
                    return

                # Add items
                for item_data in self._items_data:
                    self._jc_ctrl.add_job_card_item(
                        job_card_id=new_jc.id,
                        description=item_data["description"],
                        quantity=item_data["quantity"],
                        unit_price_cents=item_data["unit_price_cents"],
                        item_type=item_data["item_type"],
                        inventory_item_id=item_data.get("inventory_item_id"),
                    )

            self.accept()

        except Exception:
            logger.exception("Error saving job card")
            QMessageBox.critical(self, "Error", "Failed to save job card. Please check the data and try again.")


# ═══════════════════════════════════════════════════════════════════
#  Custom Item Dialog
# ═══════════════════════════════════════════════════════════════════

class CustomItemDialog(QDialog):
    """Sub-dialog for adding a custom line item (part/service/labor)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Custom Item")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_SM)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(SPACING_MD)
        form.setVerticalSpacing(SPACING_XS)

        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Item description")
        self._desc_edit.setFixedHeight(INPUT_HEIGHT)
        form.addRow("Description:", self._desc_edit)

        self._type_combo = QComboBox()
        self._type_combo.addItems(["PART", "SERVICE", "LABOR"])
        self._type_combo.setFixedHeight(INPUT_HEIGHT)
        form.addRow("Type:", self._type_combo)

        self._qty_spin = QSpinBox()
        self._qty_spin.setRange(1, 99999)
        self._qty_spin.setValue(1)
        self._qty_spin.setFixedHeight(INPUT_HEIGHT)
        form.addRow("Quantity:", self._qty_spin)

        self._price_spin = QDoubleSpinBox()
        self._price_spin.setRange(0, 9999999.99)
        self._price_spin.setDecimals(2)
        self._price_spin.setPrefix("Rs. ")
        self._price_spin.setFixedHeight(INPUT_HEIGHT)
        form.addRow("Unit Price:", self._price_spin)

        layout.addLayout(form)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._validate_and_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _validate_and_accept(self):
        if not self._desc_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Please enter a description.")
            return
        self.accept()

    def get_item_data(self) -> dict:
        qty = self._qty_spin.value()
        unit_price_cents = int(round(self._price_spin.value() * 100))
        line_total_cents = qty * unit_price_cents
        return {
            "description": self._desc_edit.text().strip(),
            "item_type": self._type_combo.currentText(),
            "quantity": qty,
            "unit_price_cents": unit_price_cents,
            "line_total_cents": line_total_cents,
            "inventory_item_id": None,
        }


# ═══════════════════════════════════════════════════════════════════
#  Update Status Dialog
# ═══════════════════════════════════════════════════════════════════

class UpdateStatusDialog(QDialog):
    """Dialog for updating the status of a job card."""

    def __init__(self, job_card, jc_ctrl: JobCardController, parent=None):
        super().__init__(parent)
        self._job_card = job_card
        self._jc_ctrl = jc_ctrl

        self.setWindowTitle(f"Update Status — {job_card.job_number}")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        # Current status display
        current_row = QHBoxLayout()
        current_row.addWidget(QLabel("Current Status:"))
        current_badge = StatusBadge(job_card.status)
        current_row.addWidget(current_badge)
        current_row.addStretch()
        layout.addLayout(current_row)

        # New status
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(SPACING_MD)
        form.setVerticalSpacing(SPACING_XS)

        self._status_combo = QComboBox()
        self._status_combo.addItems(["PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED"])
        self._status_combo.setFixedHeight(INPUT_HEIGHT)

        # Set current status as default
        current_idx = self._status_combo.findText(job_card.status)
        if current_idx >= 0:
            self._status_combo.setCurrentIndex(current_idx)

        form.addRow("New Status:", self._status_combo)

        self._mileage_out_spin = QSpinBox()
        self._mileage_out_spin.setRange(0, 9999999)
        self._mileage_out_spin.setSuffix(" km")
        self._mileage_out_spin.setFixedHeight(INPUT_HEIGHT)

        # Pre-fill mileage out if exists
        if job_card.mileage_out is not None:
            self._mileage_out_spin.setValue(job_card.mileage_out)

        form.addRow("Mileage Out:", self._mileage_out_spin)

        layout.addLayout(form)

        # Info label
        info_label = QLabel("Mileage Out is typically set when status changes to COMPLETED.")
        info_label.setObjectName("secondary")
        info_label.setStyleSheet(
            f"font-size: {FONT_SMALL}px; color: {COLOR_TEXT_SECONDARY};"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_save(self):
        new_status = self._status_combo.currentText()
        mileage_out = self._mileage_out_spin.value() or None

        kwargs = {}
        if mileage_out is not None:
            kwargs["mileage_out"] = mileage_out

        try:
            result = self._jc_ctrl.update_status(
                self._job_card.id,
                new_status,
                **kwargs,
            )
            if result:
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to update job card status.")
        except Exception:
            logger.exception("Error updating job card status")
            QMessageBox.critical(self, "Error", "Failed to update status.")


# ═══════════════════════════════════════════════════════════════════
#  Inline Customer Creation Dialog
# ═══════════════════════════════════════════════════════════════════

class InlineCustomerDialog(QDialog):
    """Compact dialog for quickly creating a new customer."""

    def __init__(self, cust_ctrl: CustomerController, parent=None):
        super().__init__(parent)
        self._cust_ctrl = cust_ctrl
        self._created_customer = None

        self.setWindowTitle("New Customer")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_SM)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(SPACING_MD)
        form.setVerticalSpacing(SPACING_XS)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Full name")
        self._name_edit.setFixedHeight(INPUT_HEIGHT)
        form.addRow("Name *:", self._name_edit)

        self._phone_edit = QLineEdit()
        self._phone_edit.setPlaceholderText("Phone number")
        self._phone_edit.setFixedHeight(INPUT_HEIGHT)
        form.addRow("Phone *:", self._phone_edit)

        self._email_edit = QLineEdit()
        self._email_edit.setPlaceholderText("Email (optional)")
        self._email_edit.setFixedHeight(INPUT_HEIGHT)
        form.addRow("Email:", self._email_edit)

        self._address_edit = QLineEdit()
        self._address_edit.setPlaceholderText("Address (optional)")
        self._address_edit.setFixedHeight(INPUT_HEIGHT)
        form.addRow("Address:", self._address_edit)

        self._nic_edit = QLineEdit()
        self._nic_edit.setPlaceholderText("NIC (optional)")
        self._nic_edit.setFixedHeight(INPUT_HEIGHT)
        form.addRow("NIC:", self._nic_edit)

        layout.addLayout(form)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_save(self):
        name = self._name_edit.text().strip()
        phone = self._phone_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation", "Customer name is required.")
            return
        if not phone:
            QMessageBox.warning(self, "Validation", "Phone number is required.")
            return

        kwargs = {}
        email = self._email_edit.text().strip()
        if email:
            kwargs["email"] = email
        address = self._address_edit.text().strip()
        if address:
            kwargs["address"] = address
        nic = self._nic_edit.text().strip()
        if nic:
            kwargs["nic"] = nic

        try:
            self._created_customer = self._cust_ctrl.create_customer(
                name=name, phone=phone, **kwargs
            )
            if self._created_customer:
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to create customer.")
        except Exception:
            logger.exception("Error creating customer")
            QMessageBox.critical(self, "Error", "Failed to create customer.")

    def get_created_customer(self):
        return self._created_customer
