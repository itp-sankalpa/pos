"""
InventoryScreen — inventory management page for the Vehicle Service POS.
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
    QDoubleSpinBox,
    QMessageBox,
    QPushButton,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

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
    SearchBar,
    DataTable,
    FormPanel,
    SummaryCard,
    StatusBadge,
    ActionBar,
)
from controllers.inventory_controller import InventoryController
from config import cents_to_display, display_to_cents


# ── Column indices for the data table ───────────────────────────────
COL_CODE = 0
COL_NAME = 1
COL_CATEGORY = 2
COL_BRAND = 3
COL_UNIT = 4
COL_COST = 5
COL_SELL = 6
COL_STOCK = 7
COL_REORDER = 8
COL_STATUS = 9


class InventoryScreen(QWidget):
    """Inventory management screen with search, summary cards, data table, and CRUD dialogs."""

    def __init__(self, session, stacked_widget=None, parent=None):
        super().__init__(parent)

        self._session = session
        self._stacked_widget = stacked_widget
        self._controller = InventoryController()
        self._items: list = []  # Cached InventoryItem list (same order as table rows)

        # ── Main layout ──
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # ── Page header ──
        self._header = PageHeader("Inventory", subtitle="Manage parts and stock levels")
        self._header.add_action("Add Item", self._on_add_item, "btn_primary")
        layout.addWidget(self._header)

        # ── Top row: SearchBar + SummaryCards ──
        top_row = QHBoxLayout()
        top_row.setSpacing(SPACING_MD)

        # Search bar with category filter
        categories = self._controller.get_categories()
        filter_options = ["All Categories"] + categories
        self._search_bar = SearchBar(
            placeholder="Search by code, name, or brand...",
            filters=filter_options,
        )
        self._search_bar.set_search_callback(self._on_search)
        self._search_bar.set_filter_callback(self._on_filter_change)
        top_row.addWidget(self._search_bar, stretch=1)

        # Summary cards
        self._card_total = SummaryCard("Total Items", "0", COLOR_ACCENT)
        self._card_low_stock = SummaryCard("Low Stock", "0", COLOR_ERROR)
        self._card_stock_value = SummaryCard("Stock Value", "Rs. 0.00", COLOR_SUCCESS)

        top_row.addWidget(self._card_total)
        top_row.addWidget(self._card_low_stock)
        top_row.addWidget(self._card_stock_value)

        layout.addLayout(top_row)

        # ── Data table ──
        self._table = DataTable(
            columns=[
                ("Code", 80),
                ("Name", 200),
                ("Category", 100),
                ("Brand", 100),
                ("Unit", 50),
                ("Cost", 90),
                ("Sell Price", 90),
                ("In Stock", 70),
                ("Reorder", 60),
                ("Status", 80),
            ]
        )
        self._table.set_double_click_handler(self._on_double_click_row)
        layout.addWidget(self._table, stretch=1)

        # ── Action bar ──
        self._action_bar = ActionBar()
        self._action_bar.add_button("Edit", self._on_edit_item, "btn_secondary")
        self._action_bar.add_button("Adjust Stock", self._on_adjust_stock, "btn_secondary")
        self._action_bar.add_button("Delete", self._on_delete_item, "btn_danger")
        layout.addWidget(self._action_bar)

        # ── Initial data load ──
        self.refresh()

    # ── Data loading ────────────────────────────────────────────────

    def refresh(self):
        """Reload inventory data and summary cards."""
        self._load_items()

    def _load_items(self, search=None, category=None):
        """Load items from the controller and populate the table."""
        # Normalize "All Categories" filter
        cat = category if category and category != "All Categories" else None
        items = self._controller.get_items(search=search, category=cat)
        self._items = items

        rows = []
        for item in items:
            status_text = "Low Stock" if item.is_low_stock else "In Stock"
            rows.append([
                item.item_code or "",
                item.name or "",
                item.category or "",
                item.brand or "",
                item.unit or "",
                cents_to_display(item.cost_price_cents),
                cents_to_display(item.sell_price_cents),
                item.quantity_in_stock,
                item.reorder_level,
                status_text,
            ])
        self._table.load_data(rows)
        self._apply_table_formatting()
        self._update_summary_cards()

    def _apply_table_formatting(self):
        """Apply custom formatting to table cells after data load."""
        for row_idx, item in enumerate(self._items):
            # Red text for low stock in "In Stock" column
            stock_item = self._table.item(row_idx, COL_STOCK)
            if stock_item and item.is_low_stock:
                stock_item.setForeground(QColor(COLOR_ERROR))

            # Replace status text with a StatusBadge widget
            status_text = "Low Stock" if item.is_low_stock else "In Stock"
            badge = StatusBadge(status_text)
            badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self._table.setCellWidget(row_idx, COL_STATUS, badge)

    def _update_summary_cards(self):
        """Update the three summary cards with current data."""
        total = len(self._items)
        low_stock = sum(1 for item in self._items if item.is_low_stock)
        stock_value = sum(
            item.quantity_in_stock * item.cost_price_cents for item in self._items
        )
        self._card_total.set_value(str(total))
        self._card_low_stock.set_value(str(low_stock))
        self._card_stock_value.set_value(cents_to_display(stock_value))

    # ── Search & Filter ─────────────────────────────────────────────

    def _on_search(self, text: str):
        """Debounced search callback — reload with current filters."""
        category = self._search_bar.filter_text()
        self._load_items(search=text.strip() or None, category=category)

    def _on_filter_change(self, filter_text: str):
        """Category filter changed — reload with current search text."""
        search = self._search_bar.text().strip() or None
        self._load_items(search=search, category=filter_text)

    # ── Add Item ────────────────────────────────────────────────────

    def _on_add_item(self):
        """Open the Add Item dialog."""
        categories = self._controller.get_categories()
        dialog = ItemDialog(parent=self, categories=categories)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["item_code"].strip() or not data["name"].strip():
                QMessageBox.warning(
                    self, "Validation Error",
                    "Item Code and Name are required.",
                )
                return
            result = self._controller.create_item(
                item_code=data["item_code"].strip(),
                name=data["name"].strip(),
                description=data["description"].strip() or None,
                category=data["category"] or None,
                brand=data["brand"].strip() or None,
                unit=data["unit"],
                cost_price_cents=data["cost_price_cents"],
                sell_price_cents=data["sell_price_cents"],
                quantity_in_stock=data["quantity_in_stock"],
                reorder_level=data["reorder_level"],
            )
            if result:
                self.refresh()
            else:
                QMessageBox.critical(
                    self, "Error",
                    "Failed to create item. Item code may already exist.",
                )

    # ── Edit Item ───────────────────────────────────────────────────

    def _on_edit_item(self):
        """Open the Edit Item dialog for the selected row."""
        row = self._table.get_selected_row()
        if row < 0:
            QMessageBox.information(
                self, "No Selection", "Please select an item to edit.",
            )
            return
        if row >= len(self._items):
            return
        self._open_edit_dialog(self._items[row])

    def _on_double_click_row(self, row, _col):
        """Double-click handler — open edit dialog for clicked row."""
        if row < 0 or row >= len(self._items):
            return
        self._open_edit_dialog(self._items[row])

    def _open_edit_dialog(self, item):
        """Open the Edit Item dialog pre-filled with *item* data."""
        categories = self._controller.get_categories()
        dialog = ItemDialog(parent=self, categories=categories, item=item)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["item_code"].strip() or not data["name"].strip():
                QMessageBox.warning(
                    self, "Validation Error",
                    "Item Code and Name are required.",
                )
                return
            result = self._controller.update_item(
                item.id,
                item_code=data["item_code"].strip(),
                name=data["name"].strip(),
                description=data["description"].strip() or None,
                category=data["category"] or None,
                brand=data["brand"].strip() or None,
                unit=data["unit"],
                cost_price_cents=data["cost_price_cents"],
                sell_price_cents=data["sell_price_cents"],
                reorder_level=data["reorder_level"],
            )
            if result:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to update item.")

    # ── Adjust Stock ────────────────────────────────────────────────

    def _on_adjust_stock(self):
        """Open the Adjust Stock dialog for the selected item."""
        row = self._table.get_selected_row()
        if row < 0:
            QMessageBox.information(
                self, "No Selection", "Please select an item to adjust stock.",
            )
            return
        if row >= len(self._items):
            return
        item = self._items[row]
        dialog = AdjustStockDialog(parent=self, item=item)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            result = self._controller.adjust_stock(
                item_id=item.id,
                qty=data["quantity"],
                txn_type=data["txn_type"],
                reference=data["reference"].strip() or None,
                notes=data["notes"].strip() or None,
            )
            if result:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to adjust stock.")

    # ── Delete Item ─────────────────────────────────────────────────

    def _on_delete_item(self):
        """Confirm and soft-delete the selected item."""
        row = self._table.get_selected_row()
        if row < 0:
            QMessageBox.information(
                self, "No Selection", "Please select an item to delete.",
            )
            return
        if row >= len(self._items):
            return
        item = self._items[row]

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{item.name}' ({item.item_code})?\n"
            "This will deactivate the item.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = self._controller.delete_item(item.id)
            if success:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete item.")


# ─── Item Dialog (Add / Edit) ───────────────────────────────────────

class ItemDialog(QDialog):
    """Dialog for creating or editing an inventory item."""

    UNIT_OPTIONS = ["PCS", "LTR", "KG", "SET", "M", "PAIR"]

    def __init__(self, parent=None, categories=None, item=None):
        super().__init__(parent)

        self._item = item
        self._is_edit = item is not None
        categories = categories or []

        self.setWindowTitle("Edit Item" if self._is_edit else "Add Item")
        self.setMinimumWidth(520)
        self.setModal(True)

        # ── Main layout ──
        outer = QVBoxLayout(self)
        outer.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        outer.setSpacing(SPACING_MD)

        # ── Form panel ──
        form = FormPanel("Item Details")

        # Item Code *
        self._item_code_input = QLineEdit()
        self._item_code_input.setPlaceholderText("Unique item code *")
        self._item_code_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Item Code *", self._item_code_input)

        # Name *
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Item name *")
        self._name_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Name *", self._name_input)

        # Description
        self._description_input = QTextEdit()
        self._description_input.setPlaceholderText("Description")
        self._description_input.setFixedHeight(72)
        form.add_row("Description", self._description_input)

        # Category
        self._category_combo = QComboBox()
        self._category_combo.setEditable(True)
        self._category_combo.setFixedHeight(INPUT_HEIGHT)
        self._category_combo.addItem("")  # blank default
        self._category_combo.addItems(categories)
        form.add_row("Category", self._category_combo)

        # Brand
        self._brand_input = QLineEdit()
        self._brand_input.setPlaceholderText("Brand")
        self._brand_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Brand", self._brand_input)

        # Unit
        self._unit_combo = QComboBox()
        self._unit_combo.setFixedHeight(INPUT_HEIGHT)
        self._unit_combo.addItems(self.UNIT_OPTIONS)
        form.add_row("Unit", self._unit_combo)

        form.add_separator()

        # Cost Price (displays LKR, saves as cents)
        self._cost_spin = QDoubleSpinBox()
        self._cost_spin.setPrefix("Rs. ")
        self._cost_spin.setDecimals(2)
        self._cost_spin.setRange(0.00, 9_999_999.99)
        self._cost_spin.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Cost Price", self._cost_spin)

        # Sell Price (displays LKR, saves as cents)
        self._sell_spin = QDoubleSpinBox()
        self._sell_spin.setPrefix("Rs. ")
        self._sell_spin.setDecimals(2)
        self._sell_spin.setRange(0.00, 9_999_999.99)
        self._sell_spin.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Sell Price", self._sell_spin)

        # Initial Stock
        self._stock_spin = QSpinBox()
        self._stock_spin.setRange(0, 999_999)
        self._stock_spin.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Initial Stock", self._stock_spin)

        # Reorder Level
        self._reorder_spin = QSpinBox()
        self._reorder_spin.setRange(0, 999_999)
        self._reorder_spin.setValue(5)
        self._reorder_spin.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Reorder Level", self._reorder_spin)

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

        # ── Pre-fill for edit mode ──
        if self._is_edit:
            self._item_code_input.setText(item.item_code or "")
            self._name_input.setText(item.name or "")
            self._description_input.setPlainText(item.description or "")

            # Set category combo to existing value
            cat_text = item.category or ""
            cat_idx = self._category_combo.findText(cat_text)
            if cat_idx >= 0:
                self._category_combo.setCurrentIndex(cat_idx)
            else:
                self._category_combo.setEditText(cat_text)

            self._brand_input.setText(item.brand or "")

            # Set unit combo
            unit_idx = self._unit_combo.findText(item.unit or "PCS")
            if unit_idx >= 0:
                self._unit_combo.setCurrentIndex(unit_idx)

            # Convert cents to LKR for spin boxes
            self._cost_spin.setValue(item.cost_price_cents / 100.0)
            self._sell_spin.setValue(item.sell_price_cents / 100.0)

            # In edit mode, stock is managed via Adjust Stock dialog
            self._stock_spin.setValue(item.quantity_in_stock)
            self._stock_spin.setEnabled(False)

            self._reorder_spin.setValue(item.reorder_level)

    # ── Private ─────────────────────────────────────────────────────

    def _on_save(self):
        """Validate required fields and accept the dialog."""
        item_code = self._item_code_input.text().strip()
        name = self._name_input.text().strip()

        if not item_code:
            QMessageBox.warning(self, "Validation", "Item Code is required.")
            self._item_code_input.setFocus()
            return
        if not name:
            QMessageBox.warning(self, "Validation", "Name is required.")
            self._name_input.setFocus()
            return

        self.accept()

    # ── Public API ──────────────────────────────────────────────────

    def get_data(self) -> dict:
        """Return a dict of all form field values with prices converted to cents."""
        return {
            "item_code": self._item_code_input.text(),
            "name": self._name_input.text(),
            "description": self._description_input.toPlainText(),
            "category": self._category_combo.currentText().strip(),
            "brand": self._brand_input.text(),
            "unit": self._unit_combo.currentText(),
            "cost_price_cents": int(round(self._cost_spin.value() * 100)),
            "sell_price_cents": int(round(self._sell_spin.value() * 100)),
            "quantity_in_stock": self._stock_spin.value(),
            "reorder_level": self._reorder_spin.value(),
        }


# ─── Adjust Stock Dialog ────────────────────────────────────────────

class AdjustStockDialog(QDialog):
    """Dialog for adjusting stock levels on an inventory item."""

    TXN_TYPES = ["IN", "OUT", "ADJUSTMENT"]

    def __init__(self, parent=None, item=None):
        super().__init__(parent)

        self._item = item

        self.setWindowTitle(f"Adjust Stock — {item.item_code}")
        self.setMinimumWidth(440)
        self.setModal(True)

        # ── Main layout ──
        outer = QVBoxLayout(self)
        outer.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        outer.setSpacing(SPACING_MD)

        # ── Current stock display ──
        info_layout = QHBoxLayout()
        info_layout.setSpacing(SPACING_SM)

        code_label = QLabel(f"Item: {item.item_code} — {item.name}")
        code_label.setStyleSheet(
            f"font-weight: bold; font-size: {FONT_BODY}px; "
            f"color: {COLOR_TEXT_PRIMARY}; background: transparent; border: none;"
        )
        info_layout.addWidget(code_label)
        info_layout.addStretch()

        stock_color = COLOR_ERROR if item.is_low_stock else COLOR_SUCCESS
        self._current_stock_label = QLabel(f"Current Stock: {item.quantity_in_stock}")
        self._current_stock_label.setStyleSheet(
            f"font-weight: bold; font-size: {FONT_BODY}px; "
            f"color: {stock_color}; background: transparent; border: none;"
        )
        info_layout.addWidget(self._current_stock_label)

        outer.addLayout(info_layout)

        # ── Form panel ──
        form = FormPanel("Stock Adjustment")

        # Transaction Type
        self._txn_type_combo = QComboBox()
        self._txn_type_combo.setFixedHeight(INPUT_HEIGHT)
        self._txn_type_combo.addItems(self.TXN_TYPES)
        form.add_row("Transaction Type", self._txn_type_combo)

        # Quantity
        self._qty_spin = QSpinBox()
        self._qty_spin.setRange(1, 10000)
        self._qty_spin.setValue(1)
        self._qty_spin.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Quantity", self._qty_spin)

        form.add_separator()

        # Reference (optional)
        self._reference_input = QLineEdit()
        self._reference_input.setPlaceholderText("Reference (optional)")
        self._reference_input.setFixedHeight(INPUT_HEIGHT)
        form.add_row("Reference", self._reference_input)

        # Notes (optional)
        self._notes_input = QTextEdit()
        self._notes_input.setPlaceholderText("Notes (optional)")
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

        save_btn = QPushButton("Save Adjustment")
        save_btn.setObjectName("btn_primary")
        save_btn.setFixedHeight(BUTTON_HEIGHT)
        save_btn.setMinimumWidth(120)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        outer.addLayout(btn_layout)

    # ── Private ─────────────────────────────────────────────────────

    def _on_save(self):
        """Validate and accept the dialog."""
        qty = self._qty_spin.value()
        if qty <= 0:
            QMessageBox.warning(self, "Validation", "Quantity must be at least 1.")
            return

        # Warn on OUT if quantity exceeds current stock
        if self._txn_type_combo.currentText() == "OUT":
            if qty > self._item.quantity_in_stock:
                reply = QMessageBox.warning(
                    self,
                    "Insufficient Stock",
                    f"Quantity ({qty}) exceeds current stock ({self._item.quantity_in_stock}).\n"
                    "Continue anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

        self.accept()

    # ── Public API ──────────────────────────────────────────────────

    def get_data(self) -> dict:
        """Return a dict of the adjustment form values."""
        return {
            "txn_type": self._txn_type_combo.currentText(),
            "quantity": self._qty_spin.value(),
            "reference": self._reference_input.text(),
            "notes": self._notes_input.toPlainText(),
        }
