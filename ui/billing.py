"""
BillingScreen — integrated billing and payments workflow.

Merges invoice listing, payment recording, and receipt
generation into a single POS-style screen.
"""

import logging
import os
from datetime import datetime
from typing import Optional, List

import tkinter as tk
from tkinter import ttk, messagebox

from ui.theme import *
from ui.components import PageHeader, SearchBar, DataTable, FormPanel, StatusBadge, ActionBar
from controllers.billing_controller import BillingController
from controllers.job_card_controller import JobCardController
from config import cents_to_display, display_to_cents, INVOICE_PREFIX

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
#  Main Screen
# ═══════════════════════════════════════════════════════════════════

class BillingScreen(tk.Frame):
    """Integrated billing & payments screen — POS-style workflow."""

    def __init__(self, session, stacked_widget=None, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=COLOR_APP_BG)

        self._session = session
        self._stacked_widget = stacked_widget

        # Controllers
        self._billing_ctrl = BillingController()
        self._jc_ctrl = JobCardController()

        # Current filter state
        self._current_search = ""
        self._current_status_filter = "All"

        # Currently displayed invoice
        self._current_invoice = None
        self._current_invoice_id = None

        # Invoice list data cache
        self._invoices_data: List = []

        self._build_ui()
        self.refresh()

    # ── UI Construction ──────────────────────────────────────────

    def _build_ui(self):
        layout = tk.Frame(self, bg=COLOR_APP_BG)
        layout.pack(fill="both", expand=True, padx=SPACING_LG, pady=SPACING_LG)

        # ── Header ──
        self._header = PageHeader(
            "Billing & Payments", subtitle="Create invoices, record payments, print receipts",
            parent=layout,
        )
        self._header.add_action("Generate Invoice", self._on_generate_invoice, "btn_primary")

        # ── Search bar ──
        self._search_bar = SearchBar(
            placeholder="Search invoices...",
            filters=["All", "Unpaid", "Partial", "Paid", "Overdue"],
            parent=layout,
        )
        self._search_bar.set_search_callback(self._on_search)
        self._search_bar.set_filter_callback(self._on_filter)

        # ── Data table ──
        self._table = DataTable(
            columns=[
                ("Invoice #", 100),
                ("Customer", 150),
                ("Total", 100),
                ("Paid", 100),
                ("Balance", 100),
                ("Status", 100),
                ("Date", 100),
            ],
            parent=layout,
        )
        self._table.set_double_click_handler(self._on_double_click)

        # ── Action bar ──
        self._action_bar = ActionBar(parent=layout)
        self._action_bar.add_button("Record Payment", self._on_record_payment, "btn_primary")
        self._action_bar.add_button("Print Receipt", self._on_print_thermal, "btn_secondary")
        self._action_bar.add_button("Cancel Invoice", self._on_cancel_invoice, "btn_danger")

    # ── Data Loading ─────────────────────────────────────────────

    def refresh(self):
        """Reload invoice list data into the table."""
        status = None
        if self._current_status_filter and self._current_status_filter != "All":
            status = self._current_status_filter.upper()

        search = self._current_search or None

        try:
            invoices = self._billing_ctrl.get_invoices(status=status, search=search)
        except Exception:
            logger.exception("Error loading invoices")
            invoices = []

        self._invoices_data = invoices

        rows = []
        for inv in invoices:
            customer_display = ""
            if inv.customer_obj:
                customer_display = inv.customer_obj.name or ""

            total_display = cents_to_display(inv.total_cents or 0)
            paid_display = cents_to_display(inv.paid_cents or 0)
            due_display = cents_to_display(inv.due_cents or 0)
            status_text = inv.status or ""

            date_display = ""
            if inv.created_at:
                date_display = inv.created_at.strftime("%Y-%m-%d")

            rows.append([
                inv.invoice_number or "",
                customer_display,
                total_display,
                paid_display,
                due_display,
                status_text,
                date_display,
            ])

        self._table.load_data(rows)

    # ── Selection Helpers ────────────────────────────────────────

    def _get_selected_invoice(self):
        """Return the Invoice object for the currently selected row, or None."""
        row = self._table.get_selected_row()
        if row < 0 or row >= len(self._invoices_data):
            return None
        return self._invoices_data[row]

    # ── Search / Filter Callbacks ────────────────────────────────

    def _on_search(self, text: str):
        self._current_search = text
        self.refresh()

    def _on_filter(self, filter_text: str):
        self._current_status_filter = filter_text
        self.refresh()

    # ── Double-click ─────────────────────────────────────────────

    def _on_double_click(self, row_index):
        inv = self._get_selected_invoice()
        if inv:
            self._show_invoice_detail(inv)

    # ── Show Invoice Detail (simple messagebox summary) ──────────

    def _show_invoice_detail(self, invoice):
        """Show invoice details in a dialog."""
        dlg = InvoiceDetailDialog(invoice=invoice, parent=self)
        self.wait_window(dlg)

    # ── Action: Generate Invoice from Job Card ───────────────────

    def _on_generate_invoice(self):
        """Open the job card selector dialog to generate an invoice."""
        dlg = JobCardSelectorDialog(jc_ctrl=self._jc_ctrl, parent=self)
        self.wait_window(dlg)
        if dlg.result is not None:
            job_card_id = dlg.result
            if job_card_id:
                try:
                    new_invoice = self._billing_ctrl.create_invoice_from_job_card(job_card_id)
                    if new_invoice:
                        self.refresh()
                        messagebox.showinfo(
                            "Success",
                            f"Invoice {new_invoice.invoice_number} created successfully.",
                        )
                    else:
                        messagebox.showwarning(
                            "Error",
                            "Failed to create invoice. The job card may already have an invoice.",
                        )
                except Exception:
                    logger.exception("Error creating invoice from job card")
                    messagebox.showerror("Error", "Failed to create invoice from job card.")

    # ── Action: Record Payment ───────────────────────────────────

    def _on_record_payment(self):
        """Open the payment dialog for the selected invoice."""
        inv = self._get_selected_invoice()
        if not inv:
            messagebox.showinfo("No Selection", "Please select an invoice first.")
            return

        if (inv.status or "").upper() == "CANCELLED":
            messagebox.showwarning("Cancelled", "Cannot record payment on a cancelled invoice.")
            return

        if (inv.due_cents or 0) <= 0:
            messagebox.showinfo("Fully Paid", "This invoice is already fully paid.")
            return

        dlg = PaymentDialog(invoice=inv, billing_ctrl=self._billing_ctrl, parent=self)
        self.wait_window(dlg)
        if dlg.result is not None:
            self.refresh()

    # ── Action: Print Thermal ────────────────────────────────────

    def _on_print_thermal(self):
        """Open the thermal receipt preview dialog."""
        inv = self._get_selected_invoice()
        if not inv:
            messagebox.showinfo("No Selection", "Please select an invoice first.")
            return

        invoice_data = self._build_invoice_data_dict(inv)
        dlg = ThermalReceiptPreviewDialog(invoice_data=invoice_data, parent=self)
        self.wait_window(dlg)

    # ── Action: Cancel Invoice ───────────────────────────────────

    def _on_cancel_invoice(self):
        """Cancel the selected invoice after confirmation."""
        inv = self._get_selected_invoice()
        if not inv:
            messagebox.showinfo("No Selection", "Please select an invoice to cancel.")
            return

        if (inv.status or "").upper() == "CANCELLED":
            messagebox.showinfo("Already Cancelled", "This invoice is already cancelled.")
            return

        reply = messagebox.askyesno(
            "Confirm Cancel",
            f"Are you sure you want to cancel invoice {inv.invoice_number}?\n"
            "This action cannot be undone.",
            default="no",
        )
        if not reply:
            return

        try:
            result = self._billing_ctrl.cancel_invoice(inv.id)
            if result:
                self.refresh()
                messagebox.showinfo("Cancelled", "Invoice has been cancelled.")
            else:
                messagebox.showwarning("Error", "Failed to cancel invoice.")
        except Exception:
            logger.exception("Error cancelling invoice")
            messagebox.showerror("Error", "Failed to cancel invoice.")

    # ── Build Invoice Data Dict (for print service) ──────────────

    def _build_invoice_data_dict(self, invoice) -> dict:
        """Convert an Invoice ORM object to the dict expected by print_service."""
        customer_name = ""
        phone = ""
        if invoice.customer_obj:
            customer_name = invoice.customer_obj.name or ""
            phone = invoice.customer_obj.phone or ""

        vehicle_reg = ""
        if invoice.vehicle_obj:
            parts = [invoice.vehicle_obj.registration_no or ""]
            if invoice.vehicle_obj.make:
                parts.append(invoice.vehicle_obj.make)
            if invoice.vehicle_obj.model:
                parts.append(invoice.vehicle_obj.model)
            vehicle_reg = " ".join(parts)

        items = []
        for item in (invoice.items or []):
            items.append({
                "description": item.description or "",
                "qty": item.quantity or 1,
                "unit_price": item.unit_price_cents or 0,
                "line_total": item.line_total_cents or 0,
            })

        payment_method = ""
        if invoice.payments:
            latest = invoice.payments[-1]
            payment_method = latest.method or ""

        return {
            "invoice_number": invoice.invoice_number or "",
            "date": invoice.created_at.strftime("%Y-%m-%d %H:%M") if invoice.created_at else "",
            "customer_name": customer_name,
            "phone": phone,
            "vehicle_reg": vehicle_reg,
            "items": items,
            "subtotal": invoice.subtotal_cents or 0,
            "labor_charge": invoice.labor_charge_cents or 0,
            "discount": invoice.discount_cents or 0,
            "total": invoice.total_cents or 0,
            "paid": invoice.paid_cents or 0,
            "due": invoice.due_cents or 0,
            "payment_method": payment_method,
            "business_name": "Vehicle Service Center",
            "business_address": "",
            "business_phone": "",
        }


# ═══════════════════════════════════════════════════════════════════
#  Invoice Detail Dialog
# ═══════════════════════════════════════════════════════════════════

class InvoiceDetailDialog(tk.Toplevel):
    """Dialog showing invoice detail summary."""

    def __init__(self, invoice, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.result = None
        self.title(f"Invoice — {invoice.invoice_number}")
        self.configure(bg=COLOR_APP_BG)
        self.transient(parent)
        self.minsize(520, 450)

        outer = tk.Frame(self, bg=COLOR_APP_BG, padx=SPACING_LG, pady=SPACING_LG)
        outer.pack(fill="both", expand=True)

        # Header info
        header_frame = tk.Frame(outer, bg=COLOR_PANEL_BG, padx=SPACING_MD, pady=SPACING_MD,
                                highlightbackground=COLOR_BORDER, highlightthickness=1)
        header_frame.pack(fill="x", pady=(0, SPACING_MD))

        # Row 1: Invoice # and Status
        top_row = tk.Frame(header_frame, bg=COLOR_PANEL_BG)
        top_row.pack(fill="x")
        tk.Label(top_row, text=f"Invoice: {invoice.invoice_number}",
                 font=(FONT_FAMILY, FONT_PAGE_TITLE, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG).pack(side="left")
        status_badge = StatusBadge(invoice.status or "UNPAID", parent=top_row)
        status_badge.pack(side="right")

        # Customer & Vehicle
        customer_name = invoice.customer_obj.name if invoice.customer_obj else ""
        vehicle_reg = invoice.vehicle_obj.registration_no if invoice.vehicle_obj else ""

        info_row = tk.Frame(header_frame, bg=COLOR_PANEL_BG)
        info_row.pack(fill="x", pady=(SPACING_SM, 0))
        tk.Label(info_row, text=f"Customer: {customer_name}",
                 font=(FONT_FAMILY, FONT_BODY), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG
                 ).pack(side="left", padx=(0, SPACING_XL))
        tk.Label(info_row, text=f"Vehicle: {vehicle_reg}",
                 font=(FONT_FAMILY, FONT_BODY), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG
                 ).pack(side="left")

        # Date
        date_str = invoice.created_at.strftime("%Y-%m-%d %H:%M") if invoice.created_at else ""
        tk.Label(header_frame, text=f"Date: {date_str}",
                 font=(FONT_FAMILY, FONT_SMALL), fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG
                 ).pack(anchor="w", pady=(SPACING_XS, 0))

        # Items table
        items_frame = tk.LabelFrame(
            outer, text=" Items ", font=(FONT_FAMILY, FONT_SECTION_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, padx=SPACING_MD, pady=SPACING_MD,
        )
        items_frame.pack(fill="both", expand=True, pady=(0, SPACING_MD))

        items_table = DataTable(
            columns=[
                ("#", 40),
                ("Description", 200),
                ("Qty", 60),
                ("Unit Price", 120),
                ("Line Total", 120),
            ],
            parent=items_frame,
        )

        items = invoice.items or []
        rows = []
        for row_idx, item in enumerate(items):
            rows.append([
                str(row_idx + 1),
                item.description or "",
                str(item.quantity or 1),
                cents_to_display(item.unit_price_cents or 0),
                cents_to_display(item.line_total_cents or 0),
            ])
        items_table.load_data(rows)

        # Summary
        summary_frame = tk.Frame(outer, bg=COLOR_PANEL_BG, padx=SPACING_MD, pady=SPACING_SM,
                                  highlightbackground=COLOR_BORDER, highlightthickness=1)
        summary_frame.pack(fill="x")

        # Total
        total_row = tk.Frame(summary_frame, bg=COLOR_PANEL_BG)
        total_row.pack(fill="x")
        tk.Label(total_row, text="TOTAL:", font=(FONT_FAMILY, FONT_GRAND_TOTAL, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG).pack(side="left")
        tk.Label(total_row, text=cents_to_display(invoice.total_cents or 0),
                 font=(FONT_FAMILY, FONT_GRAND_TOTAL, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG).pack(side="right")

        # Paid
        paid_row = tk.Frame(summary_frame, bg=COLOR_PANEL_BG)
        paid_row.pack(fill="x")
        tk.Label(paid_row, text="Paid:", font=(FONT_FAMILY, FONT_BODY, "bold"),
                 fg=COLOR_SUCCESS, bg=COLOR_PANEL_BG).pack(side="left")
        tk.Label(paid_row, text=cents_to_display(invoice.paid_cents or 0),
                 font=(FONT_FAMILY, FONT_BODY, "bold"),
                 fg=COLOR_SUCCESS, bg=COLOR_PANEL_BG).pack(side="right")

        # Due
        due_cents = invoice.due_cents or 0
        due_color = COLOR_ERROR if due_cents > 0 else COLOR_SUCCESS
        due_row = tk.Frame(summary_frame, bg=COLOR_PANEL_BG)
        due_row.pack(fill="x")
        tk.Label(due_row, text="Due:", font=(FONT_FAMILY, FONT_BODY, "bold"),
                 fg=due_color, bg=COLOR_PANEL_BG).pack(side="left")
        tk.Label(due_row, text=cents_to_display(due_cents),
                 font=(FONT_FAMILY, FONT_BODY, "bold"),
                 fg=due_color, bg=COLOR_PANEL_BG).pack(side="right")

        # Close button
        ttk.Button(outer, text="Close", command=self.destroy,
                    style="Secondary.TButton").pack(pady=(SPACING_MD, 0))

        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")


# ═══════════════════════════════════════════════════════════════════
#  Payment Dialog
# ═══════════════════════════════════════════════════════════════════

class PaymentDialog(tk.Toplevel):
    """Dialog for recording a payment against an invoice."""

    def __init__(self, invoice, billing_ctrl, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.result = None
        self._invoice = invoice
        self._billing_ctrl = billing_ctrl

        self.title(f"Record Payment — {invoice.invoice_number}")
        self.configure(bg=COLOR_APP_BG)
        self.grab_set()
        self.transient(parent)
        self.minsize(420, 320)

        outer = tk.Frame(self, bg=COLOR_APP_BG, padx=SPACING_LG, pady=SPACING_LG)
        outer.pack(fill="both", expand=True)

        form = FormPanel("Payment Details", parent=outer)

        # Invoice summary
        tk.Label(form, text=f"Invoice: {invoice.invoice_number}",
                 font=(FONT_FAMILY, FONT_BODY, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG).grid(
            row=form._row_count, column=0, columnspan=2, sticky="w", pady=SPACING_XS)
        form._row_count += 1

        total_text = cents_to_display(invoice.total_cents or 0)
        tk.Label(form, text=f"Total: {total_text}",
                 font=(FONT_FAMILY, FONT_BODY),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG).grid(
            row=form._row_count, column=0, columnspan=2, sticky="w", pady=SPACING_XS)
        form._row_count += 1

        due_text = cents_to_display(invoice.due_cents or 0)
        due_color = COLOR_ERROR if (invoice.due_cents or 0) > 0 else COLOR_SUCCESS
        tk.Label(form, text=f"Balance Due: {due_text}",
                 font=(FONT_FAMILY, FONT_BODY, "bold"),
                 fg=due_color, bg=COLOR_PANEL_BG).grid(
            row=form._row_count, column=0, columnspan=2, sticky="w", pady=SPACING_XS)
        form._row_count += 1

        form.add_separator()

        # Payment Amount
        self._amount_var = tk.StringVar(value=f"{(invoice.due_cents or 0) / 100:.2f}")
        self._amount_input = tk.Entry(form, textvariable=self._amount_var, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Payment Amount (Rs.):", self._amount_input)

        # Payment Method
        self._method_combo = ttk.Combobox(
            form, values=["CASH", "CARD", "BANK_TRANSFER", "OTHER"],
            state="readonly", width=18,
        )
        self._method_combo.set("CASH")
        form.add_row("Payment Method:", self._method_combo)

        # Reference (optional)
        self._ref_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Reference:", self._ref_input)

        # Buttons
        btn_frame = tk.Frame(outer, bg=COLOR_APP_BG)
        btn_frame.pack(fill="x", pady=(SPACING_MD, 0))
        tk.Frame(btn_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                    style="Secondary.TButton").pack(side="right", padx=(SPACING_SM, 0))
        ttk.Button(btn_frame, text="Record Payment", command=self._on_save,
                    style="Success.TButton").pack(side="right")

        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _on_save(self):
        try:
            amount_cents = int(round(float(self._amount_var.get()) * 100))
        except (ValueError, tk.TclError):
            messagebox.showwarning("Validation", "Please enter a valid payment amount.", parent=self)
            return

        if amount_cents <= 0:
            messagebox.showwarning("Validation", "Payment amount must be greater than zero.", parent=self)
            return

        method = self._method_combo.get()
        reference = self._ref_input.get().strip() or None

        try:
            payment = self._billing_ctrl.record_payment(
                invoice_id=self._invoice.id,
                amount_cents=amount_cents,
                method=method,
                reference=reference,
            )
            if payment:
                self.result = True
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to record payment.", parent=self)
        except Exception:
            logger.exception("Error recording payment")
            messagebox.showerror("Error", "Failed to record payment.", parent=self)

    def _on_cancel(self):
        self.result = None
        self.destroy()


# ═══════════════════════════════════════════════════════════════════
#  Job Card Selector Dialog
# ═══════════════════════════════════════════════════════════════════

class JobCardSelectorDialog(tk.Toplevel):
    """Dialog for selecting a completed job card to generate an invoice."""

    def __init__(self, jc_ctrl, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.result = None
        self._jc_ctrl = jc_ctrl
        self._job_cards_data: List = []

        self.title("Select Job Card for Invoice")
        self.configure(bg=COLOR_APP_BG)
        self.grab_set()
        self.transient(parent)
        self.minsize(700, 400)

        outer = tk.Frame(self, bg=COLOR_APP_BG, padx=SPACING_LG, pady=SPACING_LG)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text="Select a completed job card to generate an invoice:",
                 font=(FONT_FAMILY, FONT_BODY), fg=COLOR_TEXT_SECONDARY, bg=COLOR_APP_BG
                 ).pack(anchor="w", pady=(0, SPACING_SM))

        self._table = DataTable(
            columns=[
                ("Job #", 100),
                ("Vehicle", 120),
                ("Customer", 150),
                ("Status", 100),
                ("Total", 120),
                ("Created", 100),
            ],
            parent=outer,
        )
        self._table.set_double_click_handler(self._on_select)

        # Buttons
        btn_frame = tk.Frame(outer, bg=COLOR_APP_BG)
        btn_frame.pack(fill="x", pady=(SPACING_MD, 0))
        tk.Frame(btn_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                    style="Secondary.TButton").pack(side="right", padx=(SPACING_SM, 0))
        ttk.Button(btn_frame, text="Generate Invoice", command=self._on_generate,
                    style="Primary.TButton").pack(side="right")

        self._load_job_cards()

        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _load_job_cards(self):
        try:
            job_cards = self._jc_ctrl.get_job_cards(status="COMPLETED")
        except Exception:
            job_cards = []

        self._job_cards_data = job_cards
        rows = []
        for jc in job_cards:
            vehicle_display = jc.vehicle.registration_no if jc.vehicle else ""
            customer_display = jc.customer_obj.name if jc.customer_obj else ""
            total_display = cents_to_display(jc.total_cents or 0)
            created_display = jc.created_at.strftime("%Y-%m-%d") if jc.created_at else ""
            rows.append([
                jc.job_number or "",
                vehicle_display,
                customer_display,
                jc.status or "",
                total_display,
                created_display,
            ])
        self._table.load_data(rows)

    def _on_select(self, row_index):
        self._on_generate()

    def _on_generate(self):
        row = self._table.get_selected_row()
        if row < 0 or row >= len(self._job_cards_data):
            messagebox.showinfo("No Selection", "Please select a job card.", parent=self)
            return
        jc = self._job_cards_data[row]
        self.result = jc.id
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


# ═══════════════════════════════════════════════════════════════════
#  Thermal Receipt Preview Dialog
# ═══════════════════════════════════════════════════════════════════

class ThermalReceiptPreviewDialog(tk.Toplevel):
    """Dialog showing thermal receipt preview with text display."""

    def __init__(self, invoice_data: dict, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.result = None
        self._invoice_data = invoice_data
        self._current_width = RECEIPT_CHARS_80MM

        self.title("Thermal Receipt Preview")
        self.configure(bg=COLOR_APP_BG)
        self.transient(parent)
        self.minsize(540, 600)

        outer = tk.Frame(self, bg=COLOR_APP_BG, padx=SPACING_MD, pady=SPACING_MD)
        outer.pack(fill="both", expand=True)

        # Paper width selector
        width_row = tk.Frame(outer, bg=COLOR_APP_BG)
        width_row.pack(fill="x", pady=(0, SPACING_SM))
        tk.Label(width_row, text="Paper Width:", font=(FONT_FAMILY, FONT_BODY, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_APP_BG).pack(side="left")

        self._width_var = tk.IntVar(value=80)
        ttk.Radiobutton(width_row, text="80mm", variable=self._width_var,
                         value=80, command=self._refresh_preview).pack(side="left", padx=SPACING_SM)
        ttk.Radiobutton(width_row, text="58mm", variable=self._width_var,
                         value=58, command=self._refresh_preview).pack(side="left")

        # Receipt text display
        self._receipt_text = tk.Text(
            outer, font=(FONT_MONO, FONT_RECEIPT),
            bg="#FFFFF0", fg=COLOR_TEXT_PRIMARY,
            wrap="none", padx=10, pady=10,
            relief="solid", bd=1,
        )
        self._receipt_text.pack(fill="both", expand=True)

        # Buttons
        btn_frame = tk.Frame(outer, bg=COLOR_APP_BG)
        btn_frame.pack(fill="x", pady=(SPACING_SM, 0))
        tk.Frame(btn_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_frame, text="Close", command=self.destroy,
                    style="Secondary.TButton").pack(side="right")

        self._refresh_preview()

        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _refresh_preview(self):
        """Generate and display receipt text."""
        chars = RECEIPT_CHARS_80MM if self._width_var.get() == 80 else RECEIPT_CHARS_58MM
        try:
            from services.print_service import generate_thermal_receipt_text
            text = generate_thermal_receipt_text(self._invoice_data, chars_per_line=chars)
        except ImportError:
            # Fallback: simple receipt text
            text = self._generate_simple_receipt(chars)

        self._receipt_text.delete("1.0", "end")
        self._receipt_text.insert("1.0", text)

    def _generate_simple_receipt(self, chars: int) -> str:
        """Generate a simple receipt text as fallback."""
        d = self._invoice_data
        sep = "-" * chars
        center = lambda s: s.center(chars)

        lines = [
            sep,
            center(d.get("business_name", "Vehicle Service Center")),
            center(d.get("business_address", "")),
            center(d.get("business_phone", "")),
            sep,
            f"Invoice: {d.get('invoice_number', '')}",
            f"Date: {d.get('date', '')}",
            f"Customer: {d.get('customer_name', '')}",
            f"Vehicle: {d.get('vehicle_reg', '')}",
            sep,
        ]

        for item in d.get("items", []):
            desc = item.get("description", "")
            qty = item.get("qty", 1)
            total = item.get("line_total", 0)
            lines.append(f"{desc[:30]:<30} {qty:>3} {cents_to_display(total):>12}")

        lines.append(sep)
        lines.append(f"{'Subtotal':.<30} {cents_to_display(d.get('subtotal', 0)):>12}")
        if d.get("labor_charge", 0) > 0:
            lines.append(f"{'Labor':.<30} {cents_to_display(d.get('labor_charge', 0)):>12}")
        lines.append(f"{'TOTAL':.<30} {cents_to_display(d.get('total', 0)):>12}")
        lines.append(sep)
        lines.append(f"{'Paid':.<30} {cents_to_display(d.get('paid', 0)):>12}")
        lines.append(f"{'Due':.<30} {cents_to_display(d.get('due', 0)):>12}")
        lines.append(sep)
        lines.append(center("Thank you!"))
        lines.append("")

        return "\n".join(lines)
