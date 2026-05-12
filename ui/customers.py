"""
CustomersScreen — customer management page for the Vehicle Service POS.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ui.theme import (
    COLOR_APP_BG,
    COLOR_PANEL_BG,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_BORDER,
    COLOR_ACCENT,
    FONT_FAMILY,
    FONT_BODY,
    FONT_BUTTON,
    FONT_SMALL,
    FONT_SECTION_TITLE,
    SPACING_XS,
    SPACING_SM,
    SPACING_MD,
    SPACING_LG,
    BUTTON_HEIGHT,
    INPUT_HEIGHT,
)
from ui.components import PageHeader, SearchBar, DataTable, FormPanel, ActionBar
from controllers.customer_controller import CustomerController


class CustomersScreen(tk.Frame):
    """Customer management screen with search, table, and CRUD dialogs."""

    def __init__(self, session, stacked_widget=None, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self._session = session
        self._stacked_widget = stacked_widget
        self._controller = CustomerController()

        # ── Main layout ──
        self.configure(bg=COLOR_APP_BG)

        # Page header
        self._header = PageHeader("Customers", subtitle="Manage your customer database", parent=self)
        self._header.pack(fill="x", padx=SPACING_LG, pady=(SPACING_LG, 0))
        self._header.add_action("Add Customer", self._on_add_customer, "btn_primary")

        # Search bar
        self._search_bar = SearchBar(
            placeholder="Search by name or phone...",
            parent=self,
        )
        self._search_bar.pack(fill="x", padx=SPACING_LG, pady=(SPACING_MD, 0))
        self._search_bar.set_search_callback(self._on_search)

        # Data table
        self._table = DataTable(
            columns=[
                ("ID", 50),
                ("Name", 200),
                ("Phone", 130),
                ("Email", 180),
                ("NIC", 120),
                ("Address", 200),
            ],
            parent=self,
        )
        self._table.pack(fill="both", expand=True, padx=SPACING_LG, pady=(SPACING_MD, 0))
        self._table.set_double_click_handler(self._on_double_click_row)

        # Action bar
        self._action_bar = ActionBar(parent=self)
        self._action_bar.pack(fill="x", padx=SPACING_LG, pady=(SPACING_MD, SPACING_LG))
        self._action_bar.add_button("Edit", self._on_edit_customer, "btn_secondary")
        self._action_bar.add_button("Delete", self._on_delete_customer, "btn_danger")

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
        self.wait_window(dialog)
        if dialog.result is not None:
            data = dialog.result
            if not data["name"].strip() or not data["phone"].strip():
                messagebox.showwarning("Validation Error", "Name and Phone are required.", parent=self)
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
                messagebox.showerror("Error", "Failed to create customer.", parent=self)

    # ── Edit customer ───────────────────────────────────────────────

    def _on_edit_customer(self):
        """Open the Edit Customer dialog for the selected row."""
        row = self._table.get_selected_row()
        if row < 0:
            messagebox.showinfo("No Selection", "Please select a customer to edit.", parent=self)
            return
        customer_id = self._table.get_selected_data(0)
        if not customer_id:
            return
        customer = self._controller.get_customer(int(customer_id))
        if not customer:
            messagebox.showerror("Error", "Customer not found.", parent=self)
            return
        self._open_edit_dialog(customer)

    def _on_double_click_row(self, row_index):
        """Double-click handler — open edit dialog for clicked row."""
        # Re-fetch the ID from the table at the given row index
        customer_id = self._table.get_selected_data(0)
        if not customer_id:
            return
        customer = self._controller.get_customer(int(customer_id))
        if customer:
            self._open_edit_dialog(customer)

    def _open_edit_dialog(self, customer):
        """Open the Edit Customer dialog pre-filled with *customer* data."""
        dialog = CustomerDialog(parent=self, customer=customer)
        self.wait_window(dialog)
        if dialog.result is not None:
            data = dialog.result
            if not data["name"].strip() or not data["phone"].strip():
                messagebox.showwarning("Validation Error", "Name and Phone are required.", parent=self)
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
                messagebox.showerror("Error", "Failed to update customer.", parent=self)

    # ── Delete customer ─────────────────────────────────────────────

    def _on_delete_customer(self):
        """Confirm and soft-delete the selected customer."""
        row = self._table.get_selected_row()
        if row < 0:
            messagebox.showinfo("No Selection", "Please select a customer to delete.", parent=self)
            return
        customer_id = self._table.get_selected_data(0)
        customer_name = self._table.get_selected_data(1)
        if not customer_id:
            return

        reply = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete customer '{customer_name}'?\n"
            "This will deactivate the customer record.",
            parent=self,
        )
        if reply:
            success = self._controller.delete_customer(int(customer_id))
            if success:
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to delete customer.", parent=self)


# ─── Customer Dialog ────────────────────────────────────────────────


class CustomerDialog(tk.Toplevel):
    """Dialog for creating or editing a customer.

    Uses the ``result`` pattern for Tkinter modality:
    - ``self.result = None`` initially
    - On Save: sets ``self.result = self.get_data()`` then ``self.destroy()``
    - On Cancel: just ``self.destroy()``
    - The caller uses ``self.wait_window(dialog)`` then checks ``dialog.result``
    """

    def __init__(self, parent=None, customer=None):
        super().__init__(parent)

        self._customer = customer
        self._is_edit = customer is not None
        self.result = None

        self.title("Edit Customer" if self._is_edit else "Add Customer")
        self.minimum_width = 480
        self.minsize(self.minimum_width, 200)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.geometry(f"+{parent.winfo_rootx() + 80}+{parent.winfo_rooty() + 60}")

        # ── Main layout ──
        outer = tk.Frame(self, bg=COLOR_PANEL_BG, padx=SPACING_LG, pady=SPACING_LG)
        outer.pack(fill="both", expand=True)

        # ── Form panel ──
        form = FormPanel("Customer Details", parent=outer)

        # Name *
        self._name_input = tk.Entry(
            form, font=(FONT_FAMILY, FONT_BODY),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_APP_BG,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief="solid", bd=1,
        )
        self._name_input.configure(height=INPUT_HEIGHT // 4)  # approximate
        form.add_row("Name *", self._name_input)

        # Phone *
        self._phone_input = tk.Entry(
            form, font=(FONT_FAMILY, FONT_BODY),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_APP_BG,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief="solid", bd=1,
        )
        form.add_row("Phone *", self._phone_input)

        # Email
        self._email_input = tk.Entry(
            form, font=(FONT_FAMILY, FONT_BODY),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_APP_BG,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief="solid", bd=1,
        )
        form.add_row("Email", self._email_input)

        # Address (Text widget)
        self._address_input = tk.Text(
            form, font=(FONT_FAMILY, FONT_BODY),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_APP_BG,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief="solid", bd=1, height=3, wrap="word",
        )
        form.add_row("Address", self._address_input)

        # NIC
        self._nic_input = tk.Entry(
            form, font=(FONT_FAMILY, FONT_BODY),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_APP_BG,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief="solid", bd=1,
        )
        form.add_row("NIC", self._nic_input)

        form.add_separator()

        # Notes (Text widget)
        self._notes_input = tk.Text(
            form, font=(FONT_FAMILY, FONT_BODY),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_APP_BG,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief="solid", bd=1, height=3, wrap="word",
        )
        form.add_row("Notes", self._notes_input)

        form.pack(fill="both", expand=True)

        # ── Dialog buttons ──
        btn_frame = tk.Frame(outer, bg=COLOR_PANEL_BG)
        btn_frame.pack(fill="x", pady=(SPACING_MD, 0))

        # Spacer to push buttons right
        spacer = tk.Frame(btn_frame, bg=COLOR_PANEL_BG)
        spacer.pack(side="left", fill="x", expand=True)

        cancel_btn = ttk.Button(
            btn_frame, text="Cancel", command=self._on_cancel, style="Secondary.TButton",
        )
        cancel_btn.pack(side="right", padx=(SPACING_SM, 0))

        save_label = "Save" if self._is_edit else "Create"
        save_btn = ttk.Button(
            btn_frame, text=save_label, command=self._on_save, style="Primary.TButton",
        )
        save_btn.pack(side="right", padx=(SPACING_SM, 0))

        # ── Pre-fill for edit ──
        if self._is_edit:
            self._name_input.insert(0, customer.name or "")
            self._phone_input.insert(0, customer.phone or "")
            self._email_input.insert(0, customer.email or "")
            self._address_input.insert("1.0", customer.address or "")
            self._nic_input.insert(0, customer.nic or "")
            self._notes_input.insert("1.0", customer.notes or "")

        # Bind Escape and Enter
        self.bind("<Escape>", lambda e: self._on_cancel())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    # ── Private ─────────────────────────────────────────────────────

    def _on_save(self):
        """Validate and close the dialog with result data."""
        name = self._name_input.get().strip()
        phone = self._phone_input.get().strip()

        if not name:
            messagebox.showwarning("Validation", "Name is required.", parent=self)
            self._name_input.focus_set()
            return
        if not phone:
            messagebox.showwarning("Validation", "Phone is required.", parent=self)
            self._phone_input.focus_set()
            return

        self.result = self.get_data()
        self.destroy()

    def _on_cancel(self):
        """Close the dialog without saving."""
        self.result = None
        self.destroy()

    # ── Public API ──────────────────────────────────────────────────

    def get_data(self) -> dict:
        """Return a dict of all form field values."""
        return {
            "name": self._name_input.get(),
            "phone": self._phone_input.get(),
            "email": self._email_input.get(),
            "address": self._address_input.get("1.0", "end-1c"),
            "nic": self._nic_input.get(),
            "notes": self._notes_input.get("1.0", "end-1c"),
        }
