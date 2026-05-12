"""
ReportsScreen — business analytics and reports for the Vehicle Service POS.
"""

import csv
import logging
from datetime import date, datetime

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from ui.theme import *
from ui.components import PageHeader, DataTable, SummaryCard
from controllers.report_controller import ReportController
from config import cents_to_display

logger = logging.getLogger(__name__)


class ReportsScreen(tk.Frame):
    """Reports screen with analytical tabs: Daily Summary, Monthly Revenue, Inventory Report."""

    def __init__(self, session, stacked_widget=None, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=COLOR_APP_BG)

        self._session = session
        self._stacked_widget = stacked_widget
        self._controller = ReportController()

        # ── Main layout ──
        layout = tk.Frame(self, bg=COLOR_APP_BG)
        layout.pack(fill="both", expand=True, padx=SPACING_LG, pady=SPACING_LG)

        # ── Page header ──
        self._header = PageHeader("Reports", subtitle="Business analytics and reports", parent=layout)

        # ── Tab-like buttons ──
        tab_bar = tk.Frame(layout, bg=COLOR_APP_BG)
        tab_bar.pack(fill="x", pady=(0, SPACING_MD))

        self._tab_buttons = {}
        self._tab_container = tk.Frame(layout, bg=COLOR_APP_BG)

        tabs = [
            ("daily", "Daily Summary"),
            ("monthly", "Monthly Revenue"),
            ("inventory", "Inventory Report"),
        ]

        for tab_id, tab_label in tabs:
            btn = tk.Button(
                tab_bar, text=tab_label,
                font=(FONT_FAMILY, FONT_BUTTON),
                fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
                activeforeground=COLOR_TEXT_PRIMARY, activebackground=COLOR_ACCENT,
                relief="flat", bd=0, padx=20, pady=8,
                cursor="hand2",
                command=lambda tid=tab_id: self._switch_tab(tid),
            )
            btn.pack(side="left", padx=(0, SPACING_XS))
            self._tab_buttons[tab_id] = btn

        # Tab content area
        self._tab_container.pack(fill="both", expand=True)

        # Build each tab's content
        self._tab_frames = {}
        self._build_daily_tab()
        self._build_monthly_tab()
        self._build_inventory_tab()

        # Default date range: current month
        today = date.today()
        self._default_from = date(today.year, today.month, 1)
        self._default_to = today

        # Show first tab
        self._switch_tab("daily")

    # ── Tab Switching ─────────────────────────────────────────────

    def _switch_tab(self, tab_id: str):
        """Show the selected tab and update button styling."""
        for tid, frame in self._tab_frames.items():
            frame.pack_forget()
        for tid, btn in self._tab_buttons.items():
            if tid == tab_id:
                btn.config(bg=COLOR_ACCENT, fg="#FFFFFF")
            else:
                btn.config(bg=COLOR_PANEL_BG, fg=COLOR_TEXT_PRIMARY)

        if tab_id in self._tab_frames:
            self._tab_frames[tab_id].pack(fill="both", expand=True)

    # ── Helpers ───────────────────────────────────────────────────

    def _parse_date_entry(self, entry_widget, default: date) -> date:
        """Parse a date string from an entry widget, falling back to default."""
        text = entry_widget.get().strip()
        if not text:
            return default
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            return default

    def _create_date_filter_row(self, parent, include_status=False):
        """Create a horizontal filter bar with date entries and optional status combo.

        Returns (frame, date_from_entry, date_to_entry, status_combo_or_None, generate_btn).
        """
        row = tk.Frame(parent, bg=COLOR_APP_BG)
        row.pack(fill="x", pady=(0, SPACING_MD))

        tk.Label(row, text="From:", font=(FONT_FAMILY, FONT_SMALL),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_APP_BG).pack(side="left")
        date_from = tk.Entry(row, font=(FONT_FAMILY, FONT_BODY), width=12)
        date_from.insert(0, self._default_from.strftime("%Y-%m-%d"))
        date_from.pack(side="left", padx=(SPACING_XS, SPACING_SM))

        tk.Label(row, text="To:", font=(FONT_FAMILY, FONT_SMALL),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_APP_BG).pack(side="left")
        date_to = tk.Entry(row, font=(FONT_FAMILY, FONT_BODY), width=12)
        date_to.insert(0, self._default_to.strftime("%Y-%m-%d"))
        date_to.pack(side="left", padx=(SPACING_XS, SPACING_SM))

        status_combo = None
        if include_status:
            tk.Label(row, text="Status:", font=(FONT_FAMILY, FONT_SMALL),
                     fg=COLOR_TEXT_SECONDARY, bg=COLOR_APP_BG).pack(side="left")
            status_combo = ttk.Combobox(
                row, values=["All", "PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED"],
                state="readonly", width=15,
            )
            status_combo.set("All")
            status_combo.pack(side="left", padx=(SPACING_XS, SPACING_SM))

        generate_btn = ttk.Button(row, text="Generate", style="Primary.TButton")
        generate_btn.pack(side="left", padx=(SPACING_SM, 0))

        return row, date_from, date_to, status_combo, generate_btn

    # ═══════════════════════════════════════════════════════════════
    #  DAILY SUMMARY TAB
    # ═══════════════════════════════════════════════════════════════

    def _build_daily_tab(self):
        tab = tk.Frame(self._tab_container, bg=COLOR_APP_BG)

        # Filter row
        filter_row, self._daily_date_from, self._daily_date_to, _, generate_btn = \
            self._create_date_filter_row(tab, include_status=False)
        generate_btn.config(command=self._generate_daily)

        # Summary cards
        cards_row = tk.Frame(tab, bg=COLOR_APP_BG)
        cards_row.pack(fill="x", pady=(0, SPACING_MD))

        self._daily_card_revenue = SummaryCard("Total Revenue", "Rs. 0.00", COLOR_ACCENT, parent=cards_row)
        self._daily_card_jobs = SummaryCard("Total Jobs", "0", COLOR_INFO, parent=cards_row)
        self._daily_card_avg = SummaryCard("Avg Job Value", "Rs. 0.00", COLOR_SUCCESS, parent=cards_row)

        # Data table
        self._daily_table = DataTable(
            columns=[
                ("Date", 120),
                ("Revenue", 150),
                ("Jobs Count", 100),
                ("Invoices Count", 120),
            ],
            parent=tab,
        )

        # Export button
        btn_row = tk.Frame(tab, bg=COLOR_APP_BG)
        btn_row.pack(fill="x", pady=(SPACING_SM, 0))
        ttk.Button(btn_row, text="Export to CSV", command=self._export_daily_csv,
                    style="Secondary.TButton").pack(side="right")

        self._tab_frames["daily"] = tab

    def _generate_daily(self):
        date_from = self._parse_date_entry(self._daily_date_from, self._default_from)
        date_to = self._parse_date_entry(self._daily_date_to, self._default_to)

        try:
            report = self._controller.get_revenue_report(date_from, date_to)
        except Exception:
            logger.exception("Error generating revenue report")
            messagebox.showerror("Error", "Failed to generate revenue report.")
            return

        if not report:
            return

        # Update summary cards
        self._daily_card_revenue.set_value(cents_to_display(report.get("total_revenue_cents", 0)))
        self._daily_card_jobs.set_value(str(report.get("total_jobs", 0)))
        self._daily_card_avg.set_value(cents_to_display(report.get("avg_job_value_cents", 0)))

        # Update table
        rows = []
        for day in report.get("by_day", []):
            rows.append([
                str(day.get("date", "")),
                cents_to_display(day.get("revenue_cents", 0)),
                str(day.get("jobs", 0)),
                str(day.get("invoices", 0)),
            ])
        self._daily_table.load_data(rows)

    def _export_daily_csv(self):
        self._export_table_csv(self._daily_table, "daily_report.csv")

    # ═══════════════════════════════════════════════════════════════
    #  MONTHLY REVENUE TAB
    # ═══════════════════════════════════════════════════════════════

    def _build_monthly_tab(self):
        tab = tk.Frame(self._tab_container, bg=COLOR_APP_BG)

        # Filter row
        filter_row, self._monthly_date_from, self._monthly_date_to, self._monthly_status_combo, generate_btn = \
            self._create_date_filter_row(tab, include_status=True)
        generate_btn.config(command=self._generate_monthly)

        # Data table
        self._monthly_table = DataTable(
            columns=[
                ("Job #", 80),
                ("Vehicle", 130),
                ("Customer", 150),
                ("Status", 110),
                ("Items", 80),
                ("Labor", 100),
                ("Total", 120),
                ("Created", 110),
            ],
            parent=tab,
        )

        # Export button
        btn_row = tk.Frame(tab, bg=COLOR_APP_BG)
        btn_row.pack(fill="x", pady=(SPACING_SM, 0))
        ttk.Button(btn_row, text="Export to CSV", command=self._export_monthly_csv,
                    style="Secondary.TButton").pack(side="right")

        self._tab_frames["monthly"] = tab

    def _generate_monthly(self):
        date_from = self._parse_date_entry(self._monthly_date_from, self._default_from)
        date_to = self._parse_date_entry(self._monthly_date_to, self._default_to)
        status_text = self._monthly_status_combo.get()
        status = None if status_text == "All" else status_text

        try:
            jobs = self._controller.get_job_card_report(date_from, date_to, status=status)
        except Exception:
            logger.exception("Error generating job card report")
            messagebox.showerror("Error", "Failed to generate job card report.")
            return

        rows = []
        for jc in jobs:
            vehicle_str = ""
            if hasattr(jc, "vehicle") and jc.vehicle:
                vehicle_str = f"{jc.vehicle.registration_no or ''} - {jc.vehicle.make or ''} {jc.vehicle.model or ''}".strip(" -")
            customer_str = ""
            if hasattr(jc, "customer_obj") and jc.customer_obj:
                customer_str = jc.customer_obj.name or ""
            items_total = 0
            if hasattr(jc, "items"):
                items_total = sum(
                    (it.quantity * it.unit_price_cents) if hasattr(it, "quantity") and hasattr(it, "unit_price_cents") else 0
                    for it in (jc.items or [])
                )
            labor_total = getattr(jc, "labor_charge_cents", 0) or 0
            total = items_total + labor_total
            status_val = getattr(jc, "status", "")
            created_val = ""
            if hasattr(jc, "created_at") and jc.created_at:
                created_val = jc.created_at.strftime("%Y-%m-%d")
            rows.append([
                getattr(jc, "job_number", ""),
                vehicle_str,
                customer_str,
                status_val,
                cents_to_display(items_total),
                cents_to_display(labor_total),
                cents_to_display(total),
                created_val,
            ])
        self._monthly_table.load_data(rows)

    def _export_monthly_csv(self):
        self._export_table_csv(self._monthly_table, "monthly_report.csv")

    # ═══════════════════════════════════════════════════════════════
    #  INVENTORY TAB
    # ═══════════════════════════════════════════════════════════════

    def _build_inventory_tab(self):
        tab = tk.Frame(self._tab_container, bg=COLOR_APP_BG)

        # Summary cards
        cards_row = tk.Frame(tab, bg=COLOR_APP_BG)
        cards_row.pack(fill="x", pady=(0, SPACING_MD))

        self._inv_card_total = SummaryCard("Total Items", "0", COLOR_ACCENT, parent=cards_row)
        self._inv_card_value = SummaryCard("Total Stock Value", "Rs. 0.00", COLOR_SUCCESS, parent=cards_row)
        self._inv_card_low = SummaryCard("Low Stock Count", "0", COLOR_ERROR, parent=cards_row)

        # Generate button
        btn_row = tk.Frame(tab, bg=COLOR_APP_BG)
        btn_row.pack(fill="x", pady=(0, SPACING_MD))
        ttk.Button(btn_row, text="Generate Inventory Report", command=self._generate_inventory,
                    style="Primary.TButton").pack(side="left")
        ttk.Button(btn_row, text="Export to CSV", command=self._export_inventory_csv,
                    style="Secondary.TButton").pack(side="right")

        # Data table
        self._inv_table = DataTable(
            columns=[
                ("Code", 100),
                ("Name", 180),
                ("Category", 120),
                ("In Stock", 90),
                ("Reorder Level", 110),
            ],
            parent=tab,
        )

        self._tab_frames["inventory"] = tab

    def _generate_inventory(self):
        try:
            report = self._controller.get_inventory_report()
        except Exception:
            logger.exception("Error generating inventory report")
            messagebox.showerror("Error", "Failed to generate inventory report.")
            return

        if not report:
            return

        # Summary cards
        self._inv_card_total.set_value(str(report.get("total_items", 0)))
        self._inv_card_value.set_value(cents_to_display(report.get("total_value_cents", 0)))

        low_stock = report.get("low_stock_items", [])
        self._inv_card_low.set_value(str(len(low_stock)))

        # Table — show low stock items
        rows = []
        for item in low_stock:
            rows.append([
                getattr(item, "item_code", ""),
                getattr(item, "name", ""),
                getattr(item, "category", "") or "",
                str(getattr(item, "quantity_in_stock", 0)),
                str(getattr(item, "reorder_level", 0)),
            ])
        self._inv_table.load_data(rows)

    def _export_inventory_csv(self):
        self._export_table_csv(self._inv_table, "inventory_report.csv")

    # ═══════════════════════════════════════════════════════════════
    #  CSV Export Helper
    # ═══════════════════════════════════════════════════════════════

    def _export_table_csv(self, table: DataTable, default_filename: str):
        """Export the current table data to a CSV file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_filename,
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        try:
            # Get headers and data from the table
            headers = [header for header, _ in table._columns]
            data_rows = []
            for item_id in table._tree.get_children():
                values = table._tree.item(item_id, "values")
                data_rows.append(list(values))

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(data_rows)

            messagebox.showinfo("Export Successful", f"Report saved to:\n{file_path}")
        except Exception:
            logger.exception("Error exporting CSV")
            messagebox.showerror("Export Error", "Failed to export report to CSV.")
