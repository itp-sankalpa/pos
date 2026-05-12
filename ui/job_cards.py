"""
JobCardsScreen — Track and manage service/repair job cards.

Provides listing, creation, editing, status updates, and deletion
of job cards for the Vehicle Service Center POS.
"""

import logging
from datetime import datetime
from typing import Optional, List

import tkinter as tk
from tkinter import ttk, messagebox

from ui.theme import *
from ui.components import PageHeader, SearchBar, DataTable, FormPanel, StatusBadge, ActionBar
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

class JobCardsScreen(tk.Frame):
    """Job Cards listing screen with CRUD operations."""

    def __init__(self, session, stacked_widget=None, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=COLOR_APP_BG)

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

        # Cached data
        self._job_cards_data: List = []

        self._build_ui()
        self.refresh()

    # ── UI Construction ──────────────────────────────────────────

    def _build_ui(self):
        layout = tk.Frame(self, bg=COLOR_APP_BG)
        layout.pack(fill="both", expand=True, padx=SPACING_LG, pady=SPACING_LG)

        # ── Header ──
        self._header = PageHeader(
            "Job Cards", subtitle="Track and manage service/repair jobs", parent=layout
        )
        self._header.add_action("New Job Card", self._on_new_job_card, "btn_primary")

        # ── Search bar ──
        self._search_bar = SearchBar(
            placeholder="Search job cards...",
            filters=["All", "Pending", "In Progress", "Completed", "Cancelled"],
            parent=layout,
        )
        self._search_bar.set_search_callback(self._on_search)
        self._search_bar.set_filter_callback(self._on_filter)

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
            ],
            parent=layout,
        )
        self._table.set_double_click_handler(self._on_double_click)

        # ── Action bar ──
        self._action_bar = ActionBar(parent=layout)
        self._action_bar.add_button("Edit", self._on_edit, "btn_secondary")
        self._action_bar.add_button("Update Status", self._on_update_status, "btn_secondary")
        self._action_bar.add_button("Delete", self._on_delete, "btn_danger")

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

    def _on_double_click(self, row_index):
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
        self.wait_window(dlg)
        if dlg.result is not None:
            self.refresh()

    def _on_edit(self):
        jc = self._get_selected_job_card()
        if not jc:
            messagebox.showinfo("No Selection", "Please select a job card to edit.")
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
        self.wait_window(dlg)
        if dlg.result is not None:
            self.refresh()

    def _on_update_status(self):
        jc = self._get_selected_job_card()
        if not jc:
            messagebox.showinfo("No Selection", "Please select a job card to update status.")
            return
        dlg = UpdateStatusDialog(job_card=jc, jc_ctrl=self._jc_ctrl, parent=self)
        self.wait_window(dlg)
        if dlg.result is not None:
            self.refresh()

    def _on_delete(self):
        jc = self._get_selected_job_card()
        if not jc:
            messagebox.showinfo("No Selection", "Please select a job card to delete.")
            return

        reply = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete job card {jc.job_number}?\n"
            "This action cannot be undone.",
            default="no",
        )
        if reply:
            try:
                for item in jc.items:
                    self._jc_ctrl.remove_job_card_item(item.id)
                self._jc_ctrl.update_job_card(jc.id, status="CANCELLED")
                self.refresh()
            except Exception:
                logger.exception("Error deleting job card")
                messagebox.showerror("Error", "Failed to delete job card.")


# ═══════════════════════════════════════════════════════════════════
#  Job Card Dialog (New / Edit)
# ═══════════════════════════════════════════════════════════════════

class JobCardDialog(tk.Toplevel):
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
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self.result = None
        self._session = session
        self._jc_ctrl = jc_ctrl
        self._veh_ctrl = veh_ctrl
        self._cust_ctrl = cust_ctrl
        self._inv_ctrl = inv_ctrl
        self._staff_ctrl = staff_ctrl
        self._job_card = job_card
        self._is_edit = job_card is not None

        # Item data for the items table (list of dicts)
        self._items_data: List[dict] = []

        # Cache for lookups
        self._customers_cache: List = []
        self._vehicles_cache: List = []
        self._mechanics_cache: List = []
        self._inventory_cache: List = []

        # Customer combo data
        self._customer_ids: List = []
        self._vehicle_ids: List = []
        self._mechanic_ids: List = []
        self._inventory_ids: List = []

        if self._is_edit:
            self.title(f"Edit Job Card — {self._job_card.job_number}")
        else:
            self.title("New Job Card")

        self.configure(bg=COLOR_APP_BG)
        self.grab_set()
        self.transient(parent)
        self.minsize(800, 680)

        self._build_ui()
        self._load_initial_data()

        if self._is_edit:
            self._populate_for_edit()

        # Center dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    # ── UI Construction ──────────────────────────────────────────

    def _build_ui(self):
        # Scrollable content
        canvas = tk.Canvas(self, bg=COLOR_APP_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self._scroll_frame = tk.Frame(canvas, bg=COLOR_APP_BG)

        self._scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        main = self._scroll_frame
        pad = dict(padx=SPACING_LG, pady=SPACING_MD)

        # ── Top section: Customer + Vehicle ──
        top_frame = tk.LabelFrame(
            main, text=" Customer & Vehicle ", font=(FONT_FAMILY, FONT_SECTION_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, padx=SPACING_MD, pady=SPACING_MD,
        )
        top_frame.pack(fill="x", **pad)

        # Customer row
        cust_row = tk.Frame(top_frame, bg=COLOR_PANEL_BG)
        cust_row.pack(fill="x", pady=SPACING_XS)
        tk.Label(cust_row, text="Customer:", font=(FONT_FAMILY, FONT_SMALL),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, width=14, anchor="e").pack(side="left")
        self._customer_combo = ttk.Combobox(cust_row, state="readonly", width=35)
        self._customer_combo.pack(side="left", padx=(SPACING_SM, 0))
        self._customer_combo.bind("<<ComboboxSelected>>", self._on_customer_changed)
        self._btn_new_customer = ttk.Button(
            cust_row, text="New Customer", command=self._on_new_customer_inline,
            style="Secondary.TButton",
        )
        self._btn_new_customer.pack(side="left", padx=(SPACING_SM, 0))

        # Vehicle row
        veh_row = tk.Frame(top_frame, bg=COLOR_PANEL_BG)
        veh_row.pack(fill="x", pady=SPACING_XS)
        tk.Label(veh_row, text="Vehicle:", font=(FONT_FAMILY, FONT_SMALL),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, width=14, anchor="e").pack(side="left")
        self._vehicle_combo = ttk.Combobox(veh_row, state="readonly", width=35)
        self._vehicle_combo.pack(side="left", padx=(SPACING_SM, 0))

        # ── Middle section: Details ──
        details_frame = tk.LabelFrame(
            main, text=" Details ", font=(FONT_FAMILY, FONT_SECTION_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, padx=SPACING_MD, pady=SPACING_MD,
        )
        details_frame.pack(fill="x", **pad)

        # Complaint
        comp_row = tk.Frame(details_frame, bg=COLOR_PANEL_BG)
        comp_row.pack(fill="x", pady=SPACING_XS)
        tk.Label(comp_row, text="Complaint:", font=(FONT_FAMILY, FONT_SMALL),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, width=14, anchor="e").pack(side="left")
        self._complaint_edit = tk.Text(comp_row, font=(FONT_FAMILY, FONT_BODY), height=3, wrap="word")
        self._complaint_edit.pack(side="left", fill="x", expand=True, padx=(SPACING_SM, 0))

        # Mechanic
        mech_row = tk.Frame(details_frame, bg=COLOR_PANEL_BG)
        mech_row.pack(fill="x", pady=SPACING_XS)
        tk.Label(mech_row, text="Assigned Mechanic:", font=(FONT_FAMILY, FONT_SMALL),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, width=14, anchor="e").pack(side="left")
        self._mechanic_combo = ttk.Combobox(mech_row, state="readonly", width=30)
        self._mechanic_combo.pack(side="left", padx=(SPACING_SM, 0))

        # Mileage
        mil_row = tk.Frame(details_frame, bg=COLOR_PANEL_BG)
        mil_row.pack(fill="x", pady=SPACING_XS)
        tk.Label(mil_row, text="Mileage In:", font=(FONT_FAMILY, FONT_SMALL),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, width=14, anchor="e").pack(side="left")
        self._mileage_var = tk.IntVar(value=0)
        self._mileage_in_spin = ttk.Spinbox(
            mil_row, from_=0, to=9999999, textvariable=self._mileage_var, width=14,
        )
        self._mileage_in_spin.pack(side="left", padx=(SPACING_SM, 0))
        tk.Label(mil_row, text="km", font=(FONT_FAMILY, FONT_SMALL),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG).pack(side="left", padx=(SPACING_XS, 0))

        # ── Items section ──
        items_frame = tk.LabelFrame(
            main, text=" Items (Parts / Services / Labor) ",
            font=(FONT_FAMILY, FONT_SECTION_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, padx=SPACING_MD, pady=SPACING_MD,
        )
        items_frame.pack(fill="both", expand=True, **pad)

        # Items toolbar
        toolbar = tk.Frame(items_frame, bg=COLOR_PANEL_BG)
        toolbar.pack(fill="x", pady=(0, SPACING_SM))

        tk.Label(toolbar, text="From Inventory:", font=(FONT_FAMILY, FONT_SMALL),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG).pack(side="left")
        self._inventory_combo = ttk.Combobox(toolbar, state="readonly", width=30)
        self._inventory_combo.pack(side="left", padx=(SPACING_SM, 0))

        ttk.Button(toolbar, text="Add from Inventory", command=self._on_add_inventory_item,
                    style="Secondary.TButton").pack(side="left", padx=(SPACING_SM, 0))
        ttk.Button(toolbar, text="Add Custom Item", command=self._on_add_custom_item,
                    style="Secondary.TButton").pack(side="left", padx=(SPACING_SM, 0))

        # Items table
        self._items_table = DataTable(
            columns=[
                ("Description", 200),
                ("Type", 80),
                ("Qty", 60),
                ("Unit Price", 110),
                ("Line Total", 110),
            ],
            parent=items_frame,
        )

        # Remove item button
        rm_frame = tk.Frame(items_frame, bg=COLOR_PANEL_BG)
        rm_frame.pack(fill="x", pady=(SPACING_XS, 0))
        ttk.Button(rm_frame, text="Remove Selected Item", command=self._on_remove_item,
                    style="Danger.TButton").pack(side="right")

        # ── Bottom section: Labor + Summary ──
        bottom_frame = tk.Frame(main, bg=COLOR_APP_BG)
        bottom_frame.pack(fill="x", **pad)

        # Labor charge
        labor_frame = tk.Frame(bottom_frame, bg=COLOR_APP_BG)
        labor_frame.pack(side="left", padx=(0, SPACING_LG))
        tk.Label(labor_frame, text="Labor Charge:", font=(FONT_FAMILY, FONT_SMALL),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_APP_BG).pack(side="left")
        self._labor_var = tk.StringVar(value="0.00")
        self._labor_input = tk.Entry(
            labor_frame, textvariable=self._labor_var, font=(FONT_FAMILY, FONT_BODY), width=12,
        )
        self._labor_input.pack(side="left", padx=(SPACING_SM, 0))
        self._labor_input.bind("<KeyRelease>", lambda e: self._recalculate_totals())

        # Spacer
        tk.Frame(bottom_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)

        # Summary panel
        summary_frame = tk.Frame(
            bottom_frame, bg=COLOR_PANEL_BG, padx=SPACING_MD, pady=SPACING_SM,
            highlightbackground=COLOR_BORDER, highlightthickness=1,
        )
        summary_frame.pack(side="right")

        self._subtotal_label = tk.Label(
            summary_frame, text="Subtotal: Rs. 0.00", font=(FONT_FAMILY, FONT_BODY),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, anchor="e",
        )
        self._subtotal_label.pack(anchor="e")

        self._labor_label = tk.Label(
            summary_frame, text="Labor: Rs. 0.00", font=(FONT_FAMILY, FONT_BODY),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, anchor="e",
        )
        self._labor_label.pack(anchor="e")

        self._total_label = tk.Label(
            summary_frame, text="Total: Rs. 0.00",
            font=(FONT_FAMILY, FONT_PAGE_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, anchor="e",
        )
        self._total_label.pack(anchor="e")

        # ── Dialog buttons ──
        btn_frame = tk.Frame(main, bg=COLOR_APP_BG)
        btn_frame.pack(fill="x", padx=SPACING_LG, pady=SPACING_MD)

        tk.Frame(btn_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                    style="Secondary.TButton").pack(side="right", padx=(SPACING_SM, 0))
        ttk.Button(btn_frame, text="Save Job Card", command=self._on_save,
                    style="Primary.TButton").pack(side="right")

    # ── Data Loading ─────────────────────────────────────────────

    def _load_initial_data(self):
        """Load customers, mechanics, and inventory into combos."""
        # Customers
        try:
            self._customers_cache = self._cust_ctrl.get_customers()
        except Exception:
            self._customers_cache = []

        customer_display = ["— Select Customer —"]
        self._customer_ids = [None]
        for c in self._customers_cache:
            customer_display.append(f"{c.name} ({c.phone})")
            self._customer_ids.append(c.id)
        self._customer_combo["values"] = customer_display
        if customer_display:
            self._customer_combo.current(0)

        # Mechanics
        try:
            all_staff = self._staff_ctrl.get_all_staff()
            self._mechanics_cache = [s for s in all_staff if s.is_active]
        except Exception:
            self._mechanics_cache = []

        mech_display = ["— Unassigned —"]
        self._mechanic_ids = [None]
        for m in self._mechanics_cache:
            mech_display.append(m.full_name)
            self._mechanic_ids.append(m.id)
        self._mechanic_combo["values"] = mech_display
        if mech_display:
            self._mechanic_combo.current(0)

        # Inventory items
        try:
            self._inventory_cache = self._inv_ctrl.get_items()
        except Exception:
            self._inventory_cache = []

        inv_display = ["— Select Item —"]
        self._inventory_ids = [None]
        for inv in self._inventory_cache:
            price = cents_to_display(inv.sell_price_cents)
            inv_display.append(f"{inv.name} ({inv.item_code}) — {price}")
            self._inventory_ids.append(inv.id)
        self._inventory_combo["values"] = inv_display
        if inv_display:
            self._inventory_combo.current(0)

        # Vehicles: initially empty until customer is selected
        self._vehicle_combo["values"] = ["— Select Vehicle —"]
        self._vehicle_ids = [None]
        self._vehicle_combo.current(0)

    # ── Customer changed → refresh vehicles ──────────────────────

    def _on_customer_changed(self, event=None):
        idx = self._customer_combo.current()
        cust_id = self._customer_ids[idx] if idx < len(self._customer_ids) else None
        self._load_vehicles_for_customer(cust_id)

    def _load_vehicles_for_customer(self, customer_id):
        self._vehicle_combo["values"] = ["— Select Vehicle —"]
        self._vehicle_ids = [None]
        self._vehicles_cache = []

        if not customer_id:
            self._vehicle_combo.current(0)
            return

        try:
            self._vehicles_cache = self._veh_ctrl.get_vehicles_by_customer(customer_id)
        except Exception:
            self._vehicles_cache = []

        veh_display = ["— Select Vehicle —"]
        self._vehicle_ids = [None]
        for v in self._vehicles_cache:
            label = v.registration_no
            if v.make or v.model:
                label += f" — {v.make or ''} {v.model or ''}".strip()
            veh_display.append(label)
            self._vehicle_ids.append(v.id)
        self._vehicle_combo["values"] = veh_display
        if veh_display:
            self._vehicle_combo.current(0)

    # ── Add items ────────────────────────────────────────────────

    def _on_add_inventory_item(self):
        idx = self._inventory_combo.current()
        inv_id = self._inventory_ids[idx] if idx < len(self._inventory_ids) else None
        if not inv_id:
            messagebox.showinfo("No Item", "Please select an inventory item first.", parent=self)
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
                messagebox.showinfo(
                    "Already Added",
                    f"'{inv_item.name}' is already in the items list.",
                    parent=self,
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
        self._inventory_combo.current(0)

    def _on_add_custom_item(self):
        dlg = CustomItemDialog(parent=self)
        self.wait_window(dlg)
        if dlg.result is not None:
            self._items_data.append(dlg.result)
            self._refresh_items_table()
            self._recalculate_totals()

    def _on_remove_item(self):
        row = self._items_table.get_selected_row()
        if row < 0:
            messagebox.showinfo("No Selection", "Please select an item to remove.", parent=self)
            return
        if 0 <= row < len(self._items_data):
            del self._items_data[row]
            self._refresh_items_table()
            self._recalculate_totals()

    # ── Items table refresh ──────────────────────────────────────

    def _refresh_items_table(self):
        rows = []
        for item in self._items_data:
            rows.append([
                item.get("description", ""),
                item.get("item_type", "PART"),
                str(item.get("quantity", 1)),
                cents_to_display(item.get("unit_price_cents", 0)),
                cents_to_display(item.get("line_total_cents", 0)),
            ])
        self._items_table.load_data(rows)

    # ── Totals ───────────────────────────────────────────────────

    def _recalculate_totals(self):
        subtotal = sum(item.get("line_total_cents", 0) for item in self._items_data)
        try:
            labor_cents = int(round(float(self._labor_var.get()) * 100))
        except (ValueError, tk.TclError):
            labor_cents = 0
        total = subtotal + labor_cents

        self._subtotal_label.config(text=f"Subtotal: {cents_to_display(subtotal)}")
        self._labor_label.config(text=f"Labor: {cents_to_display(labor_cents)}")
        self._total_label.config(text=f"Total: {cents_to_display(total)}")

    # ── Inline New Customer ──────────────────────────────────────

    def _on_new_customer_inline(self):
        dlg = InlineCustomerDialog(cust_ctrl=self._cust_ctrl, parent=self)
        self.wait_window(dlg)
        if dlg.result is not None:
            new_cust = dlg.result
            if new_cust:
                # Reload customer combo and select the new one
                try:
                    self._customers_cache = self._cust_ctrl.get_customers()
                except Exception:
                    self._customers_cache = []

                customer_display = ["— Select Customer —"]
                self._customer_ids = [None]
                for c in self._customers_cache:
                    customer_display.append(f"{c.name} ({c.phone})")
                    self._customer_ids.append(c.id)
                self._customer_combo["values"] = customer_display

                # Select the new customer
                if new_cust.id in self._customer_ids:
                    idx = self._customer_ids.index(new_cust.id)
                    self._customer_combo.current(idx)
                    self._on_customer_changed()

    # ── Populate for Edit ────────────────────────────────────────

    def _populate_for_edit(self):
        jc = self._job_card
        if not jc:
            return

        # Select customer
        if jc.customer_id:
            if jc.customer_id in self._customer_ids:
                idx = self._customer_ids.index(jc.customer_id)
                self._customer_combo.current(idx)
                self._load_vehicles_for_customer(jc.customer_id)

        # Select vehicle
        if jc.vehicle_id:
            if jc.vehicle_id in self._vehicle_ids:
                idx = self._vehicle_ids.index(jc.vehicle_id)
                self._vehicle_combo.current(idx)

        # Complaint
        if jc.complaint:
            self._complaint_edit.insert("1.0", jc.complaint)

        # Mechanic
        if jc.assigned_mechanic:
            if jc.assigned_mechanic in self._mechanic_ids:
                idx = self._mechanic_ids.index(jc.assigned_mechanic)
                self._mechanic_combo.current(idx)

        # Mileage in
        if jc.mileage_in is not None:
            self._mileage_var.set(jc.mileage_in)

        # Labor charge
        labor_value = (jc.labor_charge_cents or 0) / 100.0
        self._labor_var.set(f"{labor_value:.2f}")

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
        cust_idx = self._customer_combo.current()
        customer_id = self._customer_ids[cust_idx] if cust_idx < len(self._customer_ids) else None
        veh_idx = self._vehicle_combo.current()
        vehicle_id = self._vehicle_ids[veh_idx] if veh_idx < len(self._vehicle_ids) else None

        if not customer_id:
            messagebox.showwarning("Validation", "Please select a customer.", parent=self)
            return
        if not vehicle_id:
            messagebox.showwarning("Validation", "Please select a vehicle.", parent=self)
            return

        complaint = self._complaint_edit.get("1.0", "end-1c").strip()
        mech_idx = self._mechanic_combo.current()
        mechanic_id = self._mechanic_ids[mech_idx] if mech_idx < len(self._mechanic_ids) else None
        mileage_in = self._mileage_var.get() or None
        try:
            labor_cents = int(round(float(self._labor_var.get()) * 100))
        except (ValueError, tk.TclError):
            labor_cents = 0

        try:
            if self._is_edit:
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
                new_jc = self._jc_ctrl.create_job_card(
                    vehicle_id=vehicle_id,
                    customer_id=customer_id,
                    complaint=complaint,
                    assigned_mechanic=mechanic_id,
                    mileage_in=mileage_in,
                    labor_charge_cents=labor_cents,
                )

                if not new_jc:
                    messagebox.showerror("Error", "Failed to create job card.", parent=self)
                    return

                for item_data in self._items_data:
                    self._jc_ctrl.add_job_card_item(
                        job_card_id=new_jc.id,
                        description=item_data["description"],
                        quantity=item_data["quantity"],
                        unit_price_cents=item_data["unit_price_cents"],
                        item_type=item_data["item_type"],
                        inventory_item_id=item_data.get("inventory_item_id"),
                    )

            self.result = True
            self.destroy()

        except Exception:
            logger.exception("Error saving job card")
            messagebox.showerror("Error", "Failed to save job card.", parent=self)

    def _on_cancel(self):
        self.result = None
        self.destroy()


# ═══════════════════════════════════════════════════════════════════
#  Custom Item Dialog
# ═══════════════════════════════════════════════════════════════════

class CustomItemDialog(tk.Toplevel):
    """Sub-dialog for adding a custom line item (part/service/labor)."""

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.result = None
        self.title("Add Custom Item")
        self.configure(bg=COLOR_APP_BG)
        self.grab_set()
        self.transient(parent)
        self.minsize(420, 320)

        outer = tk.Frame(self, bg=COLOR_APP_BG, padx=SPACING_LG, pady=SPACING_LG)
        outer.pack(fill="both", expand=True)

        form = FormPanel("Custom Item", parent=outer)

        self._desc_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Description:", self._desc_input)

        self._type_combo = ttk.Combobox(
            form, values=["PART", "SERVICE", "LABOR"], state="readonly", width=15,
        )
        self._type_combo.set("PART")
        form.add_row("Type:", self._type_combo)

        self._qty_var = tk.IntVar(value=1)
        self._qty_spin = ttk.Spinbox(form, from_=1, to=99999, textvariable=self._qty_var, width=10)
        form.add_row("Quantity:", self._qty_spin)

        self._price_var = tk.StringVar(value="0.00")
        self._price_input = tk.Entry(form, textvariable=self._price_var, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Unit Price (Rs.):", self._price_input)

        # Buttons
        btn_frame = tk.Frame(outer, bg=COLOR_APP_BG)
        btn_frame.pack(fill="x", pady=(SPACING_MD, 0))
        tk.Frame(btn_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                    style="Secondary.TButton").pack(side="right", padx=(SPACING_SM, 0))
        ttk.Button(btn_frame, text="Add", command=self._validate_and_accept,
                    style="Primary.TButton").pack(side="right")

        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _validate_and_accept(self):
        if not self._desc_input.get().strip():
            messagebox.showwarning("Validation", "Please enter a description.", parent=self)
            return

        qty = self._qty_var.get()
        try:
            unit_price_cents = int(round(float(self._price_var.get()) * 100))
        except (ValueError, tk.TclError):
            unit_price_cents = 0

        line_total_cents = qty * unit_price_cents
        self.result = {
            "description": self._desc_input.get().strip(),
            "item_type": self._type_combo.get(),
            "quantity": qty,
            "unit_price_cents": unit_price_cents,
            "line_total_cents": line_total_cents,
        }
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


# ═══════════════════════════════════════════════════════════════════
#  Update Status Dialog
# ═══════════════════════════════════════════════════════════════════

class UpdateStatusDialog(tk.Toplevel):
    """Dialog for updating a job card's status."""

    def __init__(self, job_card, jc_ctrl, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.result = None
        self._job_card = job_card
        self._jc_ctrl = jc_ctrl

        self.title(f"Update Status — {job_card.job_number}")
        self.configure(bg=COLOR_APP_BG)
        self.grab_set()
        self.transient(parent)
        self.minsize(400, 220)

        outer = tk.Frame(self, bg=COLOR_APP_BG, padx=SPACING_LG, pady=SPACING_LG)
        outer.pack(fill="both", expand=True)

        form = FormPanel("Update Job Card Status", parent=outer)

        # Current status
        current_badge = StatusBadge(job_card.status or "PENDING", parent=form)
        form.add_row("Current Status:", current_badge)

        # New status
        self._status_combo = ttk.Combobox(
            form, values=["PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED"],
            state="readonly", width=18,
        )
        self._status_combo.set(job_card.status or "PENDING")
        form.add_row("New Status:", self._status_combo)

        # Buttons
        btn_frame = tk.Frame(outer, bg=COLOR_APP_BG)
        btn_frame.pack(fill="x", pady=(SPACING_MD, 0))
        tk.Frame(btn_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                    style="Secondary.TButton").pack(side="right", padx=(SPACING_SM, 0))
        ttk.Button(btn_frame, text="Update", command=self._on_save,
                    style="Primary.TButton").pack(side="right")

        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _on_save(self):
        new_status = self._status_combo.get()
        if new_status == self._job_card.status:
            self.result = None
            self.destroy()
            return

        try:
            result = self._jc_ctrl.update_status(self._job_card.id, new_status)
            self.result = result
        except Exception:
            logger.exception("Error updating status")
            messagebox.showerror("Error", "Failed to update status.", parent=self)
            self.result = None

        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


# ═══════════════════════════════════════════════════════════════════
#  Inline Customer Dialog
# ═══════════════════════════════════════════════════════════════════

class InlineCustomerDialog(tk.Toplevel):
    """Compact dialog to quickly create a customer."""

    def __init__(self, cust_ctrl, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.result = None
        self._cust_ctrl = cust_ctrl

        self.title("New Customer")
        self.configure(bg=COLOR_APP_BG)
        self.grab_set()
        self.transient(parent)
        self.minsize(380, 200)

        outer = tk.Frame(self, bg=COLOR_APP_BG, padx=SPACING_LG, pady=SPACING_LG)
        outer.pack(fill="both", expand=True)

        form = FormPanel("Quick Add Customer", parent=outer)

        self._name_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Name *:", self._name_input)

        self._phone_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Phone *:", self._phone_input)

        # Buttons
        btn_frame = tk.Frame(outer, bg=COLOR_APP_BG)
        btn_frame.pack(fill="x", pady=(SPACING_MD, 0))
        tk.Frame(btn_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                    style="Secondary.TButton").pack(side="right", padx=(SPACING_SM, 0))
        ttk.Button(btn_frame, text="Create", command=self._on_save,
                    style="Primary.TButton").pack(side="right")

        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _on_save(self):
        name = self._name_input.get().strip()
        phone = self._phone_input.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Name is required.", parent=self)
            return
        if not phone:
            messagebox.showwarning("Validation", "Phone is required.", parent=self)
            return

        customer = self._cust_ctrl.create_customer(name=name, phone=phone)
        self.result = customer
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()
