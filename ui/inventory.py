"""
InventoryScreen — inventory management page for the Vehicle Service POS.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from ui.theme import *
from ui.components import PageHeader, SearchBar, DataTable, FormPanel, SummaryCard, StatusBadge, ActionBar
from controllers.inventory_controller import InventoryController
from config import cents_to_display, display_to_cents


class InventoryScreen(tk.Frame):
    """Inventory management screen with search, table, and CRUD dialogs."""

    def __init__(self, session, stacked_widget=None, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=COLOR_APP_BG)

        self._session = session
        self._stacked_widget = stacked_widget
        self._controller = InventoryController()
        self._items: list = []  # Cached InventoryItem list (same order as table rows)

        # ── Main layout ──
        layout = tk.Frame(self, bg=COLOR_APP_BG)
        layout.pack(fill="both", expand=True, padx=SPACING_LG, pady=SPACING_LG)

        # ── Page header ──
        self._header = PageHeader("Inventory", subtitle="Manage parts and stock levels", parent=layout)
        self._header.add_action("Add Item", self._on_add_item, "btn_primary")

        # ── Top row: SearchBar + SummaryCards ──
        top_row = tk.Frame(layout, bg=COLOR_APP_BG)
        top_row.pack(fill="x")

        # Search bar with category filter
        categories = self._controller.get_categories()
        filter_options = ["All Categories"] + categories
        self._search_bar = SearchBar(
            placeholder="Search by code, name, or brand...",
            filters=filter_options,
            parent=top_row,
        )
        self._search_bar.set_search_callback(self._on_search)
        self._search_bar.set_filter_callback(self._on_filter_change)

        # Summary cards
        self._card_total = SummaryCard("Total Items", "0", COLOR_ACCENT, parent=top_row)
        self._card_low_stock = SummaryCard("Low Stock", "0", COLOR_ERROR, parent=top_row)
        self._card_stock_value = SummaryCard("Stock Value", "Rs. 0.00", COLOR_SUCCESS, parent=top_row)

        # ── Data table ──
        self._table = DataTable(
            columns=[
                ("Code", 80),
                ("Name", 180),
                ("Category", 100),
                ("Qty", 60),
                ("Buy Price", 100),
                ("Sell Price", 100),
                ("Status", 80),
            ],
            parent=layout,
        )
        self._table.set_double_click_handler(self._on_double_click_row)

        # ── Action bar ──
        self._action_bar = ActionBar(parent=layout)
        self._action_bar.add_button("Edit", self._on_edit_item, "btn_secondary")
        self._action_bar.add_button("Adjust Stock", self._on_adjust_stock, "btn_secondary")
        self._action_bar.add_button("Delete", self._on_delete_item, "btn_danger")

        # ── Initial data load ──
        self.refresh()

    # ── Data loading ────────────────────────────────────────────────

    def refresh(self):
        """Reload inventory data and summary cards."""
        self._load_items()

    def _load_items(self, search=None, category=None):
        """Load items from the controller and populate the table."""
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
                item.quantity_in_stock,
                cents_to_display(item.cost_price_cents),
                cents_to_display(item.sell_price_cents),
                status_text,
            ])
        self._table.load_data(rows)
        self._update_summary_cards()

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
        category = self._search_bar.filter_text()
        self._load_items(search=text.strip() or None, category=category)

    def _on_filter_change(self, filter_text: str):
        search = self._search_bar.text().strip() or None
        self._load_items(search=search, category=filter_text)

    # ── Add Item ────────────────────────────────────────────────────

    def _on_add_item(self):
        categories = self._controller.get_categories()
        dialog = ItemDialog(parent=self, categories=categories)
        self.wait_window(dialog)
        if dialog.result is not None:
            data = dialog.result
            if not data["item_code"].strip() or not data["name"].strip():
                messagebox.showwarning("Validation Error", "Item Code and Name are required.")
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
                messagebox.showerror("Error", "Failed to create item. Item code may already exist.")

    # ── Edit Item ───────────────────────────────────────────────────

    def _on_edit_item(self):
        row = self._table.get_selected_row()
        if row < 0:
            messagebox.showinfo("No Selection", "Please select an item to edit.")
            return
        if row >= len(self._items):
            return
        self._open_edit_dialog(self._items[row])

    def _on_double_click_row(self, row_index):
        if row_index < 0 or row_index >= len(self._items):
            return
        self._open_edit_dialog(self._items[row_index])

    def _open_edit_dialog(self, item):
        categories = self._controller.get_categories()
        dialog = ItemDialog(parent=self, categories=categories, item=item)
        self.wait_window(dialog)
        if dialog.result is not None:
            data = dialog.result
            if not data["item_code"].strip() or not data["name"].strip():
                messagebox.showwarning("Validation Error", "Item Code and Name are required.")
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
                messagebox.showerror("Error", "Failed to update item.")

    # ── Adjust Stock ────────────────────────────────────────────────

    def _on_adjust_stock(self):
        row = self._table.get_selected_row()
        if row < 0:
            messagebox.showinfo("No Selection", "Please select an item to adjust stock.")
            return
        if row >= len(self._items):
            return
        item = self._items[row]
        dialog = AdjustStockDialog(parent=self, item=item)
        self.wait_window(dialog)
        if dialog.result is not None:
            data = dialog.result
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
                messagebox.showerror("Error", "Failed to adjust stock.")

    # ── Delete Item ─────────────────────────────────────────────────

    def _on_delete_item(self):
        row = self._table.get_selected_row()
        if row < 0:
            messagebox.showinfo("No Selection", "Please select an item to delete.")
            return
        if row >= len(self._items):
            return
        item = self._items[row]

        reply = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{item.name}' ({item.item_code})?\n"
            "This will deactivate the item.",
            default="no",
        )
        if reply:
            success = self._controller.delete_item(item.id)
            if success:
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to delete item.")


# ─── Item Dialog (Add / Edit) ───────────────────────────────────────

class ItemDialog(tk.Toplevel):
    """Dialog for creating or editing an inventory item."""

    UNIT_OPTIONS = ["PCS", "LTR", "KG", "SET", "M", "PAIR"]

    def __init__(self, parent=None, categories=None, item=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.result = None
        self._item = item
        self._is_edit = item is not None
        categories = categories or []

        self.title("Edit Item" if self._is_edit else "Add Item")
        self.configure(bg=COLOR_APP_BG)
        self.grab_set()
        self.transient(parent)
        self.minsize(540, 620)

        # ── Main layout ──
        outer = tk.Frame(self, bg=COLOR_APP_BG, padx=SPACING_LG, pady=SPACING_LG)
        outer.pack(fill="both", expand=True)

        form = FormPanel("Item Details", parent=outer)

        # Item Code *
        self._item_code_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Item Code *", self._item_code_input)

        # Name *
        self._name_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Name *", self._name_input)

        # Description
        self._description_input = tk.Text(form, font=(FONT_FAMILY, FONT_BODY), height=3, wrap="word")
        form.add_row("Description", self._description_input)

        # Category
        cat_values = [""] + categories
        self._category_combo = ttk.Combobox(form, values=cat_values, width=18)
        self._category_combo.set("")
        form.add_row("Category", self._category_combo)

        # Brand
        self._brand_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Brand", self._brand_input)

        # Unit
        self._unit_combo = ttk.Combobox(form, values=self.UNIT_OPTIONS, state="readonly", width=10)
        self._unit_combo.set("PCS")
        form.add_row("Unit", self._unit_combo)

        form.add_separator()

        # Cost Price
        self._cost_var = tk.StringVar(value="0.00")
        self._cost_input = tk.Entry(form, textvariable=self._cost_var, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Cost Price (Rs.)", self._cost_input)

        # Sell Price
        self._sell_var = tk.StringVar(value="0.00")
        self._sell_input = tk.Entry(form, textvariable=self._sell_var, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Sell Price (Rs.)", self._sell_input)

        # Initial Stock
        self._stock_var = tk.IntVar(value=0)
        self._stock_spin = ttk.Spinbox(form, from_=0, to=999999, textvariable=self._stock_var, width=10)
        form.add_row("Initial Stock", self._stock_spin)

        # Reorder Level
        self._reorder_var = tk.IntVar(value=5)
        self._reorder_spin = ttk.Spinbox(form, from_=0, to=999999, textvariable=self._reorder_var, width=10)
        form.add_row("Reorder Level", self._reorder_spin)

        # ── Dialog buttons ──
        btn_frame = tk.Frame(outer, bg=COLOR_APP_BG)
        btn_frame.pack(fill="x", pady=(SPACING_MD, 0))
        tk.Frame(btn_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                    style="Secondary.TButton").pack(side="right", padx=(SPACING_SM, 0))
        save_text = "Save" if self._is_edit else "Create"
        ttk.Button(btn_frame, text=save_text, command=self._on_save,
                    style="Primary.TButton").pack(side="right")

        # ── Pre-fill for edit mode ──
        if self._is_edit:
            self._item_code_input.insert(0, item.item_code or "")
            self._name_input.insert(0, item.name or "")
            self._description_input.insert("1.0", item.description or "")

            cat_text = item.category or ""
            if cat_text in cat_values:
                self._category_combo.set(cat_text)
            else:
                self._category_combo.set(cat_text)

            self._brand_input.insert(0, item.brand or "")

            unit_text = item.unit or "PCS"
            self._unit_combo.set(unit_text)

            self._cost_var.set(f"{item.cost_price_cents / 100.0:.2f}")
            self._sell_var.set(f"{item.sell_price_cents / 100.0:.2f}")

            self._stock_var.set(item.quantity_in_stock)
            self._stock_spin.config(state="disabled")

            self._reorder_var.set(item.reorder_level)

        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    # ── Private ─────────────────────────────────────────────────────

    def _on_save(self):
        item_code = self._item_code_input.get().strip()
        name = self._name_input.get().strip()

        if not item_code:
            messagebox.showwarning("Validation", "Item Code is required.", parent=self)
            self._item_code_input.focus_set()
            return
        if not name:
            messagebox.showwarning("Validation", "Name is required.", parent=self)
            self._name_input.focus_set()
            return

        try:
            cost_cents = int(round(float(self._cost_var.get()) * 100))
        except (ValueError, tk.TclError):
            cost_cents = 0

        try:
            sell_cents = int(round(float(self._sell_var.get()) * 100))
        except (ValueError, tk.TclError):
            sell_cents = 0

        self.result = {
            "item_code": self._item_code_input.get(),
            "name": self._name_input.get(),
            "description": self._description_input.get("1.0", "end-1c"),
            "category": self._category_combo.get().strip(),
            "brand": self._brand_input.get(),
            "unit": self._unit_combo.get(),
            "cost_price_cents": cost_cents,
            "sell_price_cents": sell_cents,
            "quantity_in_stock": self._stock_var.get(),
            "reorder_level": self._reorder_var.get(),
        }
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


# ─── Adjust Stock Dialog ────────────────────────────────────────────

class AdjustStockDialog(tk.Toplevel):
    """Dialog for adjusting stock levels on an inventory item."""

    TXN_TYPES = ["IN", "OUT", "ADJUSTMENT"]

    def __init__(self, parent=None, item=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.result = None
        self._item = item

        self.title(f"Adjust Stock — {item.item_code}")
        self.configure(bg=COLOR_APP_BG)
        self.grab_set()
        self.transient(parent)
        self.minsize(460, 380)

        # ── Main layout ──
        outer = tk.Frame(self, bg=COLOR_APP_BG, padx=SPACING_LG, pady=SPACING_LG)
        outer.pack(fill="both", expand=True)

        # ── Current stock display ──
        info_frame = tk.Frame(outer, bg=COLOR_APP_BG)
        info_frame.pack(fill="x", pady=(0, SPACING_MD))

        tk.Label(
            info_frame, text=f"Item: {item.item_code} — {item.name}",
            font=(FONT_FAMILY, FONT_BODY, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_APP_BG,
        ).pack(side="left")

        stock_color = COLOR_ERROR if item.is_low_stock else COLOR_SUCCESS
        tk.Label(
            info_frame, text=f"Current Stock: {item.quantity_in_stock}",
            font=(FONT_FAMILY, FONT_BODY, "bold"), fg=stock_color, bg=COLOR_APP_BG,
        ).pack(side="right")

        # ── Form panel ──
        form = FormPanel("Stock Adjustment", parent=outer)

        # Transaction Type
        self._txn_type_combo = ttk.Combobox(
            form, values=self.TXN_TYPES, state="readonly", width=15,
        )
        self._txn_type_combo.set("IN")
        form.add_row("Transaction Type", self._txn_type_combo)

        # Quantity
        self._qty_var = tk.IntVar(value=1)
        self._qty_spin = ttk.Spinbox(form, from_=1, to=10000, textvariable=self._qty_var, width=10)
        form.add_row("Quantity", self._qty_spin)

        form.add_separator()

        # Reference (optional)
        self._reference_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Reference", self._reference_input)

        # Notes (optional)
        self._notes_input = tk.Text(form, font=(FONT_FAMILY, FONT_BODY), height=3, wrap="word")
        form.add_row("Notes", self._notes_input)

        # ── Dialog buttons ──
        btn_frame = tk.Frame(outer, bg=COLOR_APP_BG)
        btn_frame.pack(fill="x", pady=(SPACING_MD, 0))
        tk.Frame(btn_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                    style="Secondary.TButton").pack(side="right", padx=(SPACING_SM, 0))
        ttk.Button(btn_frame, text="Save Adjustment", command=self._on_save,
                    style="Primary.TButton").pack(side="right")

        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    # ── Private ─────────────────────────────────────────────────────

    def _on_save(self):
        qty = self._qty_var.get()
        if qty <= 0:
            messagebox.showwarning("Validation", "Quantity must be at least 1.", parent=self)
            return

        # Warn on OUT if quantity exceeds current stock
        if self._txn_type_combo.get() == "OUT":
            if qty > self._item.quantity_in_stock:
                reply = messagebox.askyesno(
                    "Insufficient Stock",
                    f"Quantity ({qty}) exceeds current stock ({self._item.quantity_in_stock}).\n"
                    "Continue anyway?",
                    default="no",
                    parent=self,
                )
                if not reply:
                    return

        self.result = {
            "txn_type": self._txn_type_combo.get(),
            "quantity": qty,
            "reference": self._reference_input.get(),
            "notes": self._notes_input.get("1.0", "end-1c"),
        }
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()
