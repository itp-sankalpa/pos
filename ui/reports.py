"""
ReportsScreen — business analytics and reports for the Vehicle Service POS.
"""

import csv
import logging
from datetime import date

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QDateEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QHeaderView,
)
from PyQt6.QtCore import Qt, QDate

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
    FONT_MONO,
    SPACING_XS,
    SPACING_SM,
    SPACING_MD,
    SPACING_LG,
    BUTTON_HEIGHT,
    INPUT_HEIGHT,
)
from ui.components import (
    PageHeader,
    DataTable,
    SummaryCard,
)
from controllers.report_controller import ReportController
from config import cents_to_display

logger = logging.getLogger(__name__)


class ReportsScreen(QWidget):
    """Reports screen with five analytical tabs."""

    def __init__(self, session, stacked_widget=None, parent=None):
        super().__init__(parent)

        self._session = session
        self._stacked_widget = stacked_widget
        self._controller = ReportController()

        # ── Main layout ──
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # ── Page header ──
        self._header = PageHeader("Reports", subtitle="Business analytics and reports")
        layout.addWidget(self._header)

        # ── Tab widget ──
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs, stretch=1)

        # Build each tab
        self._build_revenue_tab()
        self._build_job_cards_tab()
        self._build_payments_tab()
        self._build_inventory_tab()
        self._build_customers_tab()

        # ── Connect tab change to auto-generate ──
        self._tabs.currentChanged.connect(self._on_tab_changed)

        # ── Default date range: current month ──
        today = QDate.currentDate()
        self._default_from = QDate(today.year(), today.month(), 1)
        self._default_to = today

    # ── Helpers ─────────────────────────────────────────────────────

    def _date_from_qdate(self, qdate: QDate) -> date:
        """Convert QDate to Python date."""
        return date(qdate.year(), qdate.month(), qdate.day())

    def _create_filter_row(self, include_status=False, include_generate=True):
        """Create a horizontal filter bar with date pickers and optional status combo.

        Returns (layout, date_from, date_to, status_combo_or_None, generate_btn_or_None).
        """
        row = QHBoxLayout()
        row.setSpacing(SPACING_SM)

        # Date From
        row.addWidget(QLabel("From:"))
        date_from = QDateEdit()
        date_from.setCalendarPopup(True)
        date_from.setDisplayFormat("yyyy-MM-dd")
        date_from.setFixedHeight(INPUT_HEIGHT)
        date_from.setDate(self._default_from if hasattr(self, "_default_from") else QDate.currentDate())
        row.addWidget(date_from)

        # Date To
        row.addWidget(QLabel("To:"))
        date_to = QDateEdit()
        date_to.setCalendarPopup(True)
        date_to.setDisplayFormat("yyyy-MM-dd")
        date_to.setFixedHeight(INPUT_HEIGHT)
        date_to.setDate(self._default_to if hasattr(self, "_default_to") else QDate.currentDate())
        row.addWidget(date_to)

        # Status filter (optional)
        status_combo = None
        if include_status:
            row.addWidget(QLabel("Status:"))
            status_combo = QComboBox()
            status_combo.addItems(["All", "PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED"])
            status_combo.setFixedHeight(INPUT_HEIGHT)
            status_combo.setMinimumWidth(130)
            row.addWidget(status_combo)

        generate_btn = None
        if include_generate:
            generate_btn = QPushButton("Generate")
            generate_btn.setObjectName("btn_primary")
            generate_btn.setFixedHeight(BUTTON_HEIGHT)
            generate_btn.setMinimumWidth(100)
            row.addWidget(generate_btn)

        row.addStretch()
        return row, date_from, date_to, status_combo, generate_btn

    def _create_summary_row(self, cards: list[SummaryCard]) -> QHBoxLayout:
        """Create a horizontal row of SummaryCards."""
        row = QHBoxLayout()
        row.setSpacing(SPACING_MD)
        for card in cards:
            row.addWidget(card)
        row.addStretch()
        return row

    # ═══════════════════════════════════════════════════════════════
    #  REVENUE TAB
    # ═══════════════════════════════════════════════════════════════

    def _build_revenue_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        # Filter row
        filter_row, self._rev_date_from, self._rev_date_to, _, generate_btn = \
            self._create_filter_row(include_status=False, include_generate=True)
        generate_btn.clicked.connect(self._generate_revenue)
        layout.addLayout(filter_row)

        # Summary cards
        self._rev_card_revenue = SummaryCard("Total Revenue", "Rs. 0.00", COLOR_ACCENT)
        self._rev_card_jobs = SummaryCard("Total Jobs", "0", COLOR_INFO)
        self._rev_card_avg = SummaryCard("Avg Job Value", "Rs. 0.00", COLOR_SUCCESS)
        layout.addLayout(self._create_summary_row([
            self._rev_card_revenue, self._rev_card_jobs, self._rev_card_avg,
        ]))

        # Data table
        self._rev_table = DataTable(columns=[
            ("Date", 120),
            ("Revenue", 150),
            ("Jobs Count", 100),
            ("Invoices Count", 120),
        ])
        layout.addWidget(self._rev_table, stretch=1)

        self._tabs.addTab(tab, "Revenue")

    def _generate_revenue(self):
        """Fetch and display the revenue report."""
        date_from = self._date_from_qdate(self._rev_date_from.date())
        date_to = self._date_from_qdate(self._rev_date_to.date())

        try:
            report = self._controller.get_revenue_report(date_from, date_to)
        except Exception:
            logger.exception("Error generating revenue report")
            QMessageBox.critical(self, "Error", "Failed to generate revenue report.")
            return

        if not report:
            return

        # Update summary cards
        self._rev_card_revenue.set_value(cents_to_display(report.get("total_revenue_cents", 0)))
        self._rev_card_jobs.set_value(str(report.get("total_jobs", 0)))
        self._rev_card_avg.set_value(cents_to_display(report.get("avg_job_value_cents", 0)))

        # Update table
        rows = []
        for day in report.get("by_day", []):
            rows.append([
                str(day.get("date", "")),
                cents_to_display(day.get("revenue_cents", 0)),
                str(day.get("jobs", 0)),
                str(day.get("invoices", 0)),
            ])
        self._rev_table.load_data(rows)

    # ═══════════════════════════════════════════════════════════════
    #  JOB CARDS TAB
    # ═══════════════════════════════════════════════════════════════

    def _build_job_cards_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        # Filter row
        filter_row, self._jc_date_from, self._jc_date_to, self._jc_status_combo, generate_btn = \
            self._create_filter_row(include_status=True, include_generate=True)
        generate_btn.clicked.connect(self._generate_job_cards)
        layout.addLayout(filter_row)

        # Data table
        self._jc_table = DataTable(columns=[
            ("Job #", 80),
            ("Vehicle", 130),
            ("Customer", 150),
            ("Status", 110),
            ("Items", 80),
            ("Labor", 100),
            ("Total", 120),
            ("Created", 110),
        ])
        layout.addWidget(self._jc_table, stretch=1)

        self._tabs.addTab(tab, "Job Cards")

    def _generate_job_cards(self):
        """Fetch and display the job card report."""
        date_from = self._date_from_qdate(self._jc_date_from.date())
        date_to = self._date_from_qdate(self._jc_date_to.date())
        status_text = self._jc_status_combo.currentText()
        status = None if status_text == "All" else status_text

        try:
            jobs = self._controller.get_job_card_report(date_from, date_to, status=status)
        except Exception:
            logger.exception("Error generating job card report")
            QMessageBox.critical(self, "Error", "Failed to generate job card report.")
            return

        rows = []
        for jc in jobs:
            vehicle_str = ""
            if hasattr(jc, "vehicle") and jc.vehicle:
                vehicle_str = f"{jc.vehicle.registration_number or ''} - {jc.vehicle.make or ''} {jc.vehicle.model or ''}".strip(" -")
            customer_str = ""
            if hasattr(jc, "customer") and jc.customer:
                customer_str = jc.customer.name or ""
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
        self._jc_table.load_data(rows)

    # ═══════════════════════════════════════════════════════════════
    #  PAYMENTS TAB
    # ═══════════════════════════════════════════════════════════════

    def _build_payments_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        # Filter row
        filter_row, self._pay_date_from, self._pay_date_to, _, generate_btn = \
            self._create_filter_row(include_status=False, include_generate=True)
        generate_btn.clicked.connect(self._generate_payments)
        layout.addLayout(filter_row)

        # Summary cards
        self._pay_card_total = SummaryCard("Total Payments", "Rs. 0.00", COLOR_ACCENT)
        self._pay_card_cash = SummaryCard("Cash", "Rs. 0.00", COLOR_SUCCESS)
        self._pay_card_card = SummaryCard("Card", "Rs. 0.00", COLOR_INFO)
        self._pay_card_bank = SummaryCard("Bank Transfer", "Rs. 0.00", COLOR_WARNING)
        layout.addLayout(self._create_summary_row([
            self._pay_card_total, self._pay_card_cash, self._pay_card_card, self._pay_card_bank,
        ]))

        # Data table
        self._pay_table = DataTable(columns=[
            ("Date", 110),
            ("Invoice #", 100),
            ("Customer", 150),
            ("Amount", 120),
            ("Method", 110),
            ("Reference", 130),
        ])
        layout.addWidget(self._pay_table, stretch=1)

        self._tabs.addTab(tab, "Payments")

    def _generate_payments(self):
        """Fetch and display the payment report."""
        date_from = self._date_from_qdate(self._pay_date_from.date())
        date_to = self._date_from_qdate(self._pay_date_to.date())

        try:
            report = self._controller.get_payment_report(date_from, date_to)
        except Exception:
            logger.exception("Error generating payment report")
            QMessageBox.critical(self, "Error", "Failed to generate payment report.")
            return

        if not report:
            return

        # Summary cards
        self._pay_card_total.set_value(cents_to_display(report.get("total_cents", 0)))
        by_method = report.get("by_method", {})
        self._pay_card_cash.set_value(cents_to_display(by_method.get("CASH", 0)))
        self._pay_card_card.set_value(cents_to_display(by_method.get("CARD", 0)))
        self._pay_card_bank.set_value(cents_to_display(by_method.get("BANK_TRANSFER", 0)))

        # Table
        rows = []
        for day in report.get("daily_breakdown", []):
            day_date = str(day.get("date", ""))
            day_by_method = day.get("by_method", {})
            for method, amount_cents in day_by_method.items():
                rows.append([
                    day_date,
                    "",
                    "",
                    cents_to_display(amount_cents),
                    method,
                    "",
                ])
        self._pay_table.load_data(rows)

    # ═══════════════════════════════════════════════════════════════
    #  INVENTORY TAB
    # ═══════════════════════════════════════════════════════════════

    def _build_inventory_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        # Summary cards
        self._inv_card_total = SummaryCard("Total Items", "0", COLOR_ACCENT)
        self._inv_card_value = SummaryCard("Total Stock Value", "Rs. 0.00", COLOR_SUCCESS)
        self._inv_card_low = SummaryCard("Low Stock Count", "0", COLOR_ERROR)
        layout.addLayout(self._create_summary_row([
            self._inv_card_total, self._inv_card_value, self._inv_card_low,
        ]))

        # Data table
        self._inv_table = DataTable(columns=[
            ("Code", 100),
            ("Name", 180),
            ("Category", 120),
            ("In Stock", 90),
            ("Reorder Level", 110),
        ])
        layout.addWidget(self._inv_table, stretch=1)

        # Export CSV button row
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._export_csv_btn = QPushButton("Export to CSV")
        self._export_csv_btn.setObjectName("btn_secondary")
        self._export_csv_btn.setFixedHeight(BUTTON_HEIGHT)
        self._export_csv_btn.clicked.connect(self._export_inventory_csv)
        btn_row.addWidget(self._export_csv_btn)
        layout.addLayout(btn_row)

        self._tabs.addTab(tab, "Inventory")

    def _generate_inventory(self):
        """Fetch and display the inventory report."""
        try:
            report = self._controller.get_inventory_report()
        except Exception:
            logger.exception("Error generating inventory report")
            QMessageBox.critical(self, "Error", "Failed to generate inventory report.")
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
        """Export the current inventory table data to a CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Inventory Report", "inventory_report.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        try:
            headers = []
            for col in range(self._inv_table.columnCount()):
                headers.append(self._inv_table.horizontalHeaderItem(col).text())

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in range(self._inv_table.rowCount()):
                    row_data = []
                    for col in range(self._inv_table.columnCount()):
                        item = self._inv_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            QMessageBox.information(self, "Export Successful", f"Inventory report saved to:\n{file_path}")
        except Exception:
            logger.exception("Error exporting inventory CSV")
            QMessageBox.critical(self, "Export Error", "Failed to export inventory report to CSV.")

    # ═══════════════════════════════════════════════════════════════
    #  CUSTOMERS TAB
    # ═══════════════════════════════════════════════════════════════

    def _build_customers_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        # Summary cards
        self._cust_card_total = SummaryCard("Total Customers", "0", COLOR_ACCENT)
        self._cust_card_vehicles = SummaryCard("With Vehicles", "0", COLOR_INFO)
        self._cust_card_active = SummaryCard("With Active Jobs", "0", COLOR_WARNING)
        layout.addLayout(self._create_summary_row([
            self._cust_card_total, self._cust_card_vehicles, self._cust_card_active,
        ]))

        # Data table
        self._cust_table = DataTable(columns=[
            ("ID", 50),
            ("Name", 180),
            ("Phone", 130),
            ("Email", 180),
            ("Vehicles Count", 110),
            ("Active Jobs", 100),
        ])
        layout.addWidget(self._cust_table, stretch=1)

        self._tabs.addTab(tab, "Customers")

    def _generate_customers(self):
        """Fetch and display the customer report."""
        try:
            report = self._controller.get_customer_report()
        except Exception:
            logger.exception("Error generating customer report")
            QMessageBox.critical(self, "Error", "Failed to generate customer report.")
            return

        if not report:
            return

        # Summary cards
        self._cust_card_total.set_value(str(report.get("total_customers", 0)))
        self._cust_card_vehicles.set_value(str(report.get("with_vehicles", 0)))
        self._cust_card_active.set_value(str(report.get("with_active_jobs", 0)))

        # If the report returns a customers list, populate the table
        customers = report.get("customers", [])
        rows = []
        for c in customers:
            rows.append([
                getattr(c, "id", ""),
                getattr(c, "name", ""),
                getattr(c, "phone", "") or "",
                getattr(c, "email", "") or "",
                str(getattr(c, "vehicles_count", 0)),
                str(getattr(c, "active_jobs_count", 0)),
            ])
        self._cust_table.load_data(rows)

    # ═══════════════════════════════════════════════════════════════
    #  TAB CHANGE HANDLER
    # ═══════════════════════════════════════════════════════════════

    def _on_tab_changed(self, index: int):
        """Auto-generate report when a tab is selected."""
        tab_name = self._tabs.tabText(index)
        if tab_name == "Revenue":
            self._generate_revenue()
        elif tab_name == "Job Cards":
            self._generate_job_cards()
        elif tab_name == "Payments":
            self._generate_payments()
        elif tab_name == "Inventory":
            self._generate_inventory()
        elif tab_name == "Customers":
            self._generate_customers()
