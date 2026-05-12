"""
VehiclesScreen — vehicle management page for the Vehicle Service POS.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from ui.theme import (
    COLOR_APP_BG, COLOR_PANEL_BG, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_BORDER, COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR,
    COLOR_INFO, COLOR_SELECTED_ROW_BG, FONT_FAMILY, FONT_PAGE_TITLE,
    FONT_SECTION_TITLE, FONT_BODY, FONT_BUTTON, FONT_SMALL,
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG,
    BUTTON_HEIGHT, INPUT_HEIGHT, status_badge_colors,
)
from ui.components import PageHeader, SearchBar, DataTable, FormPanel, ActionBar, StatusBadge
from controllers.vehicle_controller import VehicleController
from controllers.customer_controller import CustomerController


class VehiclesScreen(tk.Frame):
    """Vehicle management screen with search, table, and CRUD dialogs."""

    def __init__(self, session, stacked_widget=None, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=COLOR_APP_BG)

        self._session = session
        self._stacked_widget = stacked_widget
        self._vehicle_controller = VehicleController()
        self._customer_controller = CustomerController()

        # ── Main layout ──
        layout = tk.Frame(self, bg=COLOR_APP_BG)
        layout.pack(fill="both", expand=True, padx=SPACING_LG, pady=SPACING_LG)

        # ── Page header ──
        self._header = PageHeader("Vehicles", subtitle="Manage vehicle records", parent=layout)
        self._header.add_action("Add Vehicle", self._on_add_vehicle, "btn_primary")

        # ── Search bar ──
        self._search_bar = SearchBar(
            placeholder="Search by registration, make, or model...", parent=layout
        )
        self._search_bar.set_search_callback(self._on_search)

        # ── Data table ──
        self._table = DataTable(
            columns=[
                ("ID", 50),
                ("Registration", 120),
                ("Make", 100),
                ("Model", 100),
                ("Year", 60),
                ("Color", 80),
                ("Customer", 150),
            ],
            parent=layout,
        )
        self._table.set_double_click_handler(self._on_double_click_row)

        # ── Action bar ──
        self._action_bar = ActionBar(parent=layout)
        self._action_bar.add_button("Edit", self._on_edit_vehicle, "btn_secondary")
        self._action_bar.add_button("Delete", self._on_delete_vehicle, "btn_danger")

        # ── Initial data load ──
        self.refresh()

    # ── Data loading ────────────────────────────────────────────────

    def refresh(self):
        """Reload vehicle data (with customer names) into the table."""
        vehicles = self._vehicle_controller.get_vehicles()
        rows = []
        for v in vehicles:
            customer_name = ""
            if v.customer:
                customer_name = v.customer.name or ""
            rows.append([
                v.id,
                v.registration_no or "",
                v.make or "",
                v.model or "",
                v.year or "",
                v.color or "",
                customer_name,
            ])
        self._table.load_data(rows)

    # ── Search ──────────────────────────────────────────────────────

    def _on_search(self, text: str):
        vehicles = self._vehicle_controller.get_vehicles(search=text.strip() or None)
        rows = []
        for v in vehicles:
            customer_name = ""
            if v.customer:
                customer_name = v.customer.name or ""
            rows.append([
                v.id,
                v.registration_no or "",
                v.make or "",
                v.model or "",
                v.year or "",
                v.color or "",
                customer_name,
            ])
        self._table.load_data(rows)

    # ── Add vehicle ─────────────────────────────────────────────────

    def _on_add_vehicle(self):
        dialog = VehicleDialog(
            customer_controller=self._customer_controller,
            parent=self,
        )
        self.wait_window(dialog)
        if dialog.result is not None:
            data = dialog.result
            if not data["customer_id"]:
                messagebox.showwarning("Validation Error", "Customer is required.")
                return
            if not data["registration_no"].strip():
                messagebox.showwarning("Validation Error", "Registration No is required.")
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
                messagebox.showerror("Error", "Failed to create vehicle.")

    # ── Edit vehicle ────────────────────────────────────────────────

    def _on_edit_vehicle(self):
        row = self._table.get_selected_row()
        if row < 0:
            messagebox.showinfo("No Selection", "Please select a vehicle to edit.")
            return
        vehicle_id = self._table.get_selected_data(0)
        if not vehicle_id:
            return
        vehicle = self._vehicle_controller.get_vehicle(int(vehicle_id))
        if not vehicle:
            messagebox.showerror("Error", "Vehicle not found.")
            return
        self._open_edit_dialog(vehicle)

    def _on_double_click_row(self, row_index):
        vehicle_id = self._table.get_selected_data(0)
        if not vehicle_id:
            return
        vehicle = self._vehicle_controller.get_vehicle(int(vehicle_id))
        if vehicle:
            self._open_edit_dialog(vehicle)

    def _open_edit_dialog(self, vehicle):
        dialog = VehicleDialog(
            customer_controller=self._customer_controller,
            parent=self,
            vehicle=vehicle,
        )
        self.wait_window(dialog)
        if dialog.result is not None:
            data = dialog.result
            if not data["customer_id"]:
                messagebox.showwarning("Validation Error", "Customer is required.")
                return
            if not data["registration_no"].strip():
                messagebox.showwarning("Validation Error", "Registration No is required.")
                return

            kwargs = {
                "customer_id": data["customer_id"],
                "registration_no": data["registration_no"].strip(),
            }
            kwargs["make"] = data["make"].strip() or None
            kwargs["model"] = data["model"].strip() or None
            kwargs["year"] = data["year"] if data["year"] else None
            kwargs["color"] = data["color"].strip() or None
            kwargs["engine_no"] = data["engine_no"].strip() or None
            kwargs["chassis_no"] = data["chassis_no"].strip() or None
            kwargs["mileage"] = data["mileage"] if data["mileage"] is not None else None
            kwargs["notes"] = data["notes"].strip() or None

            result = self._vehicle_controller.update_vehicle(vehicle.id, **kwargs)
            if result:
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to update vehicle.")

    # ── Delete vehicle ──────────────────────────────────────────────

    def _on_delete_vehicle(self):
        row = self._table.get_selected_row()
        if row < 0:
            messagebox.showinfo("No Selection", "Please select a vehicle to delete.")
            return
        vehicle_id = self._table.get_selected_data(0)
        vehicle_reg = self._table.get_selected_data(1)
        if not vehicle_id:
            return

        reply = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete vehicle '{vehicle_reg}'?",
            default="no",
        )
        if reply:
            success = self._vehicle_controller.delete_vehicle(int(vehicle_id))
            if success:
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to delete vehicle.")


# ─── Vehicle Dialog ─────────────────────────────────────────────────

class VehicleDialog(tk.Toplevel):
    """Dialog for creating or editing a vehicle, with inline customer creation."""

    def __init__(self, customer_controller, parent=None, vehicle=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.result = None
        self._customer_controller = customer_controller
        self._vehicle = vehicle
        self._is_edit = vehicle is not None

        self.title("Edit Vehicle" if self._is_edit else "Add Vehicle")
        self.configure(bg=COLOR_APP_BG)
        self.grab_set()
        self.transient(parent)
        self.minsize(540, 600)

        # ── Main layout ──
        outer = tk.Frame(self, bg=COLOR_APP_BG, padx=SPACING_LG, pady=SPACING_LG)
        outer.pack(fill="both", expand=True)

        # ── Form panel ──
        form = FormPanel("Vehicle Details", parent=outer)

        # ── Customer selector row ──
        cust_frame = tk.Frame(form, bg=COLOR_PANEL_BG)
        self._customer_combo = ttk.Combobox(cust_frame, state="readonly", width=35)
        self._customer_combo.pack(side="left", fill="x", expand=True)
        self._customer_data = []  # list of (display_text, customer_id)

        add_customer_btn = ttk.Button(
            cust_frame, text="+ New", command=self._toggle_inline_customer_form,
            style="Secondary.TButton",
        )
        add_customer_btn.pack(side="left", padx=(SPACING_SM, 0))
        form.add_row("Customer *", cust_frame)

        # ── Inline customer creation panel (hidden by default) ──
        self._inline_panel = tk.Frame(form, bg=COLOR_PANEL_BG)
        inline_header = tk.Label(
            self._inline_panel, text="New Customer",
            font=(FONT_FAMILY, FONT_SMALL, "bold"), fg=COLOR_ACCENT, bg=COLOR_PANEL_BG,
        )
        inline_header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(SPACING_XS, 0))

        tk.Label(
            self._inline_panel, text="Name *", font=(FONT_FAMILY, FONT_SMALL),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG,
        ).grid(row=1, column=0, sticky="e", padx=(0, SPACING_SM))
        self._inline_name = tk.Entry(self._inline_panel, font=(FONT_FAMILY, FONT_BODY))
        self._inline_name.grid(row=1, column=1, sticky="ew", pady=SPACING_XS)

        tk.Label(
            self._inline_panel, text="Phone *", font=(FONT_FAMILY, FONT_SMALL),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG,
        ).grid(row=2, column=0, sticky="e", padx=(0, SPACING_SM))
        self._inline_phone = tk.Entry(self._inline_panel, font=(FONT_FAMILY, FONT_BODY))
        self._inline_phone.grid(row=2, column=1, sticky="ew", pady=SPACING_XS)

        self._inline_save_btn = ttk.Button(
            self._inline_panel, text="Save Customer", command=self._save_inline_customer,
            style="Success.TButton",
        )
        self._inline_save_btn.grid(row=3, column=0, columnspan=2, sticky="e", pady=(SPACING_XS, 0))

        self._inline_panel.columnconfigure(1, weight=1)
        # Initially hidden
        form.add_row("", self._inline_panel)

        form.add_separator()

        # Registration No *
        self._reg_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Registration No *", self._reg_input)

        # Make
        self._make_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Make", self._make_input)

        # Model
        self._model_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Model", self._model_input)

        # Year
        self._year_var = tk.IntVar(value=2024)
        self._year_spin = ttk.Spinbox(
            form, from_=1900, to=2030, textvariable=self._year_var, width=10,
        )
        form.add_row("Year", self._year_spin)

        # Color
        self._color_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Color", self._color_input)

        form.add_separator()

        # Engine No
        self._engine_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Engine No", self._engine_input)

        # Chassis No
        self._chassis_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Chassis No", self._chassis_input)

        # Mileage
        self._mileage_var = tk.IntVar(value=0)
        self._mileage_spin = ttk.Spinbox(
            form, from_=0, to=9999999, textvariable=self._mileage_var, width=12,
        )
        form.add_row("Mileage (km)", self._mileage_spin)

        # Notes
        self._notes_input = tk.Text(form, font=(FONT_FAMILY, FONT_BODY), height=3, wrap="word")
        form.add_row("Notes", self._notes_input)

        # ── Dialog buttons ──
        btn_frame = tk.Frame(outer, bg=COLOR_APP_BG)
        btn_frame.pack(fill="x", pady=(SPACING_MD, 0))

        tk.Frame(btn_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)

        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self._on_cancel, style="Secondary.TButton")
        cancel_btn.pack(side="right", padx=(SPACING_SM, 0))

        save_text = "Save" if self._is_edit else "Create"
        save_btn = ttk.Button(btn_frame, text=save_text, command=self._on_save, style="Primary.TButton")
        save_btn.pack(side="right")

        # ── Populate customer combo ──
        self._load_customers()

        # ── Pre-fill for edit ──
        if self._is_edit:
            self._reg_input.insert(0, vehicle.registration_no or "")
            self._make_input.insert(0, vehicle.make or "")
            self._model_input.insert(0, vehicle.model or "")
            if vehicle.year:
                self._year_var.set(vehicle.year)
            else:
                self._year_var.set(2024)
            self._color_input.insert(0, vehicle.color or "")
            self._engine_input.insert(0, vehicle.engine_no or "")
            self._chassis_input.insert(0, vehicle.chassis_no or "")
            if vehicle.mileage is not None:
                self._mileage_var.set(vehicle.mileage)
            else:
                self._mileage_var.set(0)
            self._notes_input.insert("1.0", vehicle.notes or "")
            if vehicle.customer_id:
                self._select_customer_by_id(vehicle.customer_id)

        # Center dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    # ── Customer combo helpers ──────────────────────────────────────

    def _load_customers(self):
        """Populate the customer combo box with all active customers."""
        self._customer_data = []
        customers = self._customer_controller.get_customers()
        display_list = ["-- Select Customer --"]
        self._customer_data.append(None)
        for c in customers:
            display = f"{c.name}  ({c.phone})"
            display_list.append(display)
            self._customer_data.append(c.id)
        self._customer_combo["values"] = display_list
        if display_list:
            self._customer_combo.current(0)

    def _get_selected_customer_id(self):
        idx = self._customer_combo.current()
        if idx < 0 or idx >= len(self._customer_data):
            return None
        return self._customer_data[idx]

    def _select_customer_by_id(self, customer_id: int):
        for i, cid in enumerate(self._customer_data):
            if cid == customer_id:
                self._customer_combo.current(i)
                return
        self._load_customers()
        for i, cid in enumerate(self._customer_data):
            if cid == customer_id:
                self._customer_combo.current(i)
                return

    # ── Inline customer creation ────────────────────────────────────

    def _toggle_inline_customer_form(self):
        if self._inline_panel.winfo_ismapped():
            self._inline_panel.grid_remove()
        else:
            self._inline_panel.grid()
            self._inline_name.focus_set()

    def _save_inline_customer(self):
        name = self._inline_name.get().strip()
        phone = self._inline_phone.get().strip()

        if not name:
            messagebox.showwarning("Validation", "Customer name is required.", parent=self)
            self._inline_name.focus_set()
            return
        if not phone:
            messagebox.showwarning("Validation", "Customer phone is required.", parent=self)
            self._inline_phone.focus_set()
            return

        customer = self._customer_controller.create_customer(name=name, phone=phone)
        if not customer:
            messagebox.showerror("Error", "Failed to create customer.", parent=self)
            return

        self._load_customers()
        self._select_customer_by_id(customer.id)

        self._inline_name.delete(0, "end")
        self._inline_phone.delete(0, "end")
        self._inline_panel.grid_remove()

    # ── Save vehicle ────────────────────────────────────────────────

    def _on_save(self):
        customer_id = self._get_selected_customer_id()
        reg_no = self._reg_input.get().strip()

        if not customer_id:
            messagebox.showwarning("Validation", "Please select a customer.", parent=self)
            return
        if not reg_no:
            messagebox.showwarning("Validation", "Registration No is required.", parent=self)
            self._reg_input.focus_set()
            return

        year_val = self._year_var.get()
        year = year_val if year_val > 1900 else None
        mileage_val = self._mileage_var.get()

        self.result = {
            "customer_id": customer_id,
            "registration_no": self._reg_input.get(),
            "make": self._make_input.get(),
            "model": self._model_input.get(),
            "year": year,
            "color": self._color_input.get(),
            "engine_no": self._engine_input.get(),
            "chassis_no": self._chassis_input.get(),
            "mileage": mileage_val if mileage_val > 0 else None,
            "notes": self._notes_input.get("1.0", "end-1c"),
        }
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()
