"""
BillingScreen — integrated billing and payments workflow.

Merges invoice listing, detail viewing, payment recording, and receipt
generation into a single POS-style screen using a QSplitter layout.
"""

import logging
import os
from datetime import datetime
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
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
    QPlainTextEdit,
    QRadioButton,
    QButtonGroup,
    QScrollArea,
    QSpacerItem,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.theme import (
    COLOR_APP_BG,
    COLOR_PANEL_BG,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_BORDER,
    COLOR_ACCENT,
    COLOR_SUCCESS,
    COLOR_SUCCESS_BG,
    COLOR_WARNING,
    COLOR_ERROR,
    COLOR_ERROR_BG,
    COLOR_INFO,
    COLOR_SELECTED_ROW_BG,
    FONT_FAMILY,
    FONT_PAGE_TITLE,
    FONT_SECTION_TITLE,
    FONT_BODY,
    FONT_BUTTON,
    FONT_SMALL,
    FONT_GRAND_TOTAL,
    FONT_MONO,
    FONT_RECEIPT,
    SPACING_XS,
    SPACING_SM,
    SPACING_MD,
    SPACING_LG,
    SPACING_XL,
    BUTTON_HEIGHT,
    INPUT_HEIGHT,
    TABLE_ROW_HEIGHT,
    TABLE_HEADER_HEIGHT,
    RECEIPT_CHARS_80MM,
    RECEIPT_CHARS_58MM,
    status_badge_qss,
)
from ui.components import (
    PageHeader,
    SearchBar,
    DataTable,
    FormPanel,
    StatusBadge,
    ActionBar,
    SummaryCard,
)
from controllers.billing_controller import BillingController
from controllers.job_card_controller import JobCardController
from config import cents_to_display, display_to_cents, INVOICE_PREFIX
from services.print_service import (
    generate_thermal_receipt_text,
    generate_a4_invoice_pdf,
    save_thermal_receipt,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
#  Main Screen
# ═══════════════════════════════════════════════════════════════════

class BillingScreen(QWidget):
    """Integrated billing & payments screen — POS-style workflow."""

    def __init__(self, session, stacked_widget=None, parent=None):
        super().__init__(parent)

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
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        outer_layout.setSpacing(SPACING_MD)

        # ── Header ──
        self._header = PageHeader(
            "Billing & Payments", subtitle="Create invoices, record payments, print receipts"
        )
        self._header.add_action(
            "Generate Invoice", self._on_generate_invoice, "btn_primary"
        )
        outer_layout.addWidget(self._header)

        # ── Splitter ──
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(1)

        self._build_left_panel()
        self._build_right_panel()

        self._splitter.addWidget(self._left_panel)
        self._splitter.addWidget(self._right_panel)
        self._splitter.setStretchFactor(0, 40)
        self._splitter.setStretchFactor(1, 60)

        outer_layout.addWidget(self._splitter, stretch=1)

    # ── Left Panel (Invoice List) ────────────────────────────────

    def _build_left_panel(self):
        self._left_panel = QWidget()
        left_layout = QVBoxLayout(self._left_panel)
        left_layout.setContentsMargins(0, 0, SPACING_SM, 0)
        left_layout.setSpacing(SPACING_SM)

        # ── Search bar ──
        self._search_bar = SearchBar(
            placeholder="Search invoices…",
            filters=["All", "Unpaid", "Partial", "Paid", "Cancelled"],
        )
        self._search_bar.set_search_callback(self._on_search)
        self._search_bar.set_filter_callback(self._on_filter)
        left_layout.addWidget(self._search_bar)

        # ── Data table ──
        self._table = DataTable(
            columns=[
                ("Invoice #", 130),
                ("Customer", 150),
                ("Vehicle", 100),
                ("Total", 100),
                ("Paid", 100),
                ("Due", 100),
                ("Status", 90),
                ("Date", 100),
            ]
        )
        self._table.set_double_click_handler(self._on_double_click)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self._table, stretch=1)

    # ── Right Panel (Invoice Detail) ─────────────────────────────

    def _build_right_panel(self):
        self._right_panel = QWidget()
        self._right_layout = QVBoxLayout(self._right_panel)
        self._right_layout.setContentsMargins(SPACING_SM, 0, 0, 0)
        self._right_layout.setSpacing(0)

        # Scroll area for the detail content
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._detail_container = QWidget()
        self._detail_layout = QVBoxLayout(self._detail_container)
        self._detail_layout.setContentsMargins(0, 0, 0, 0)
        self._detail_layout.setSpacing(SPACING_MD)

        self._scroll_area.setWidget(self._detail_container)
        self._right_layout.addWidget(self._scroll_area, stretch=1)

        # Show the empty state initially
        self._show_empty_state()

    # ── Empty State ──────────────────────────────────────────────

    def _show_empty_state(self):
        """Clear the right panel and show a placeholder message."""
        self._clear_detail_panel()

        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("📋")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"font-size: 48px; background: transparent;")

        msg_label = QLabel("Select an invoice to view details")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setStyleSheet(
            f"font-size: {FONT_SECTION_TITLE}px; "
            f"color: {COLOR_TEXT_SECONDARY}; "
            f"background: transparent; "
            f"padding: {SPACING_LG}px;"
        )

        empty_layout.addWidget(icon_label)
        empty_layout.addWidget(msg_label)
        self._detail_layout.addWidget(empty_widget)

        self._current_invoice = None
        self._current_invoice_id = None

    # ── Clear Detail Panel ───────────────────────────────────────

    def _clear_detail_panel(self):
        """Remove all widgets from the detail layout."""
        while self._detail_layout.count():
            item = self._detail_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            layout = item.layout()
            if layout:
                # Recursively clear sub-layouts
                while layout.count():
                    sub_item = layout.takeAt(0)
                    sub_w = sub_item.widget()
                    if sub_w:
                        sub_w.deleteLater()

    # ── Show Invoice Detail ──────────────────────────────────────

    def _show_invoice_detail(self, invoice_id: int):
        """Load and display invoice detail in the right panel."""
        try:
            invoice = self._billing_ctrl.get_invoice(invoice_id)
        except Exception:
            logger.exception("Error loading invoice %s", invoice_id)
            QMessageBox.critical(self, "Error", "Failed to load invoice details.")
            return

        if not invoice:
            QMessageBox.warning(self, "Not Found", "Invoice not found.")
            self._show_empty_state()
            return

        self._current_invoice = invoice
        self._current_invoice_id = invoice_id

        self._clear_detail_panel()

        # ── Invoice Header ──
        self._build_invoice_header(invoice)

        # ── Items Table ──
        self._build_items_table(invoice)

        # ── Summary Panel ──
        self._build_summary_panel(invoice)

        # ── Action Buttons ──
        self._build_action_buttons(invoice)

        # Push everything up
        self._detail_layout.addStretch()

    # ── Invoice Header Section ───────────────────────────────────

    def _build_invoice_header(self, invoice):
        header_frame = QFrame()
        header_frame.setObjectName("panel")
        header_frame.setStyleSheet(
            f"QFrame#panel {{ background-color: {COLOR_PANEL_BG}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; }}"
        )
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        header_layout.setSpacing(SPACING_XS)

        # Row 1: Invoice # and Date
        top_row = QHBoxLayout()
        top_row.setSpacing(SPACING_MD)

        inv_label = QLabel(f"Invoice: {invoice.invoice_number}")
        inv_label.setStyleSheet(
            f"font-size: {FONT_PAGE_TITLE}px; font-weight: bold; "
            f"color: {COLOR_TEXT_PRIMARY}; background: transparent; border: none;"
        )
        top_row.addWidget(inv_label)

        top_row.addStretch()

        date_str = invoice.created_at.strftime("%Y-%m-%d %H:%M") if invoice.created_at else "—"
        date_label = QLabel(f"Date: {date_str}")
        date_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_SECONDARY}; "
            f"background: transparent; border: none;"
        )
        top_row.addWidget(date_label)

        # Status badge
        status_badge = StatusBadge(invoice.status or "UNPAID")
        top_row.addWidget(status_badge)

        header_layout.addLayout(top_row)

        # Row 2: Customer and Vehicle info
        info_row = QHBoxLayout()
        info_row.setSpacing(SPACING_XL)

        customer_name = ""
        if invoice.customer_obj:
            customer_name = invoice.customer_obj.name or ""

        vehicle_reg = ""
        vehicle_desc = ""
        if invoice.vehicle_obj:
            vehicle_reg = invoice.vehicle_obj.registration_no or ""
            parts = [vehicle_reg]
            if invoice.vehicle_obj.make:
                parts.append(invoice.vehicle_obj.make)
            if invoice.vehicle_obj.model:
                parts.append(invoice.vehicle_obj.model)
            vehicle_desc = " — ".join(parts) if len(parts) > 1 else vehicle_reg

        cust_label = QLabel(f"Customer: {customer_name}")
        cust_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_PRIMARY}; "
            f"background: transparent; border: none;"
        )
        info_row.addWidget(cust_label)

        veh_label = QLabel(f"Vehicle: {vehicle_desc}")
        veh_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_PRIMARY}; "
            f"background: transparent; border: none;"
        )
        info_row.addWidget(veh_label)

        info_row.addStretch()
        header_layout.addLayout(info_row)

        # Job card reference
        jc_number = ""
        if invoice.job_card:
            jc_number = invoice.job_card.job_number or ""
        if jc_number:
            jc_label = QLabel(f"Job Card: {jc_number}")
            jc_label.setStyleSheet(
                f"font-size: {FONT_SMALL}px; color: {COLOR_TEXT_SECONDARY}; "
                f"background: transparent; border: none;"
            )
            header_layout.addWidget(jc_label)

        self._detail_layout.addWidget(header_frame)

    # ── Items Table ──────────────────────────────────────────────

    def _build_items_table(self, invoice):
        items_frame = QFrame()
        items_frame.setObjectName("panel")
        items_frame.setStyleSheet(
            f"QFrame#panel {{ background-color: {COLOR_PANEL_BG}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; }}"
        )
        items_layout = QVBoxLayout(items_frame)
        items_layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        items_layout.setSpacing(SPACING_SM)

        # Section title
        title = QLabel("Items")
        title.setStyleSheet(
            f"font-size: {FONT_SECTION_TITLE}px; font-weight: bold; "
            f"color: {COLOR_TEXT_PRIMARY}; background: transparent; border: none;"
        )
        items_layout.addWidget(title)

        # Items QTableWidget
        items_table = QTableWidget(0, 5)
        items_table.setHorizontalHeaderLabels(
            ["#", "Description", "Qty", "Unit Price", "Line Total"]
        )
        items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        items_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        items_table.setAlternatingRowColors(True)
        items_table.verticalHeader().setVisible(False)
        items_table.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)
        items_table.horizontalHeader().setFixedHeight(TABLE_HEADER_HEIGHT)

        header = items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        items_table.setColumnWidth(0, 40)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        items_table.setColumnWidth(2, 60)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        items_table.setColumnWidth(3, 120)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        items_table.setColumnWidth(4, 120)

        # Populate items
        items = invoice.items or []
        items_table.setRowCount(len(items))
        for row_idx, item in enumerate(items):
            # #
            num_item = QTableWidgetItem(str(row_idx + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            items_table.setItem(row_idx, 0, num_item)

            # Description
            desc_item = QTableWidgetItem(item.description or "")
            desc_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            items_table.setItem(row_idx, 1, desc_item)

            # Qty
            qty_item = QTableWidgetItem(str(item.quantity or 1))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            items_table.setItem(row_idx, 2, qty_item)

            # Unit Price
            price_str = cents_to_display(item.unit_price_cents or 0)
            price_item = QTableWidgetItem(price_str)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            items_table.setItem(row_idx, 3, price_item)

            # Line Total
            total_str = cents_to_display(item.line_total_cents or 0)
            total_item = QTableWidgetItem(total_str)
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            items_table.setItem(row_idx, 4, total_item)

        items_table.setMinimumHeight(min(120, max(80, len(items) * TABLE_ROW_HEIGHT + TABLE_HEADER_HEIGHT + 4)))

        items_layout.addWidget(items_table)
        self._detail_layout.addWidget(items_frame)

    # ── Summary Panel ────────────────────────────────────────────

    def _build_summary_panel(self, invoice):
        summary_frame = QFrame()
        summary_frame.setObjectName("panel")
        summary_frame.setStyleSheet(
            f"QFrame#panel {{ background-color: {COLOR_PANEL_BG}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; }}"
        )
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        summary_layout.setSpacing(SPACING_XS)

        # Subtotal
        subtotal_row = QHBoxLayout()
        subtotal_label = QLabel("Subtotal:")
        subtotal_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_SECONDARY}; "
            f"background: transparent; border: none;"
        )
        subtotal_value = QLabel(cents_to_display(invoice.subtotal_cents or 0))
        subtotal_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        subtotal_value.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_PRIMARY}; "
            f"background: transparent; border: none;"
        )
        subtotal_row.addWidget(subtotal_label)
        subtotal_row.addStretch()
        subtotal_row.addWidget(subtotal_value)
        summary_layout.addLayout(subtotal_row)

        # Labor
        if (invoice.labor_charge_cents or 0) > 0:
            labor_row = QHBoxLayout()
            labor_label = QLabel("Labor:")
            labor_label.setStyleSheet(
                f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_SECONDARY}; "
                f"background: transparent; border: none;"
            )
            labor_value = QLabel(cents_to_display(invoice.labor_charge_cents or 0))
            labor_value.setAlignment(Qt.AlignmentFlag.AlignRight)
            labor_value.setStyleSheet(
                f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_PRIMARY}; "
                f"background: transparent; border: none;"
            )
            labor_row.addWidget(labor_label)
            labor_row.addStretch()
            labor_row.addWidget(labor_value)
            summary_layout.addLayout(labor_row)

        # Discount
        if (invoice.discount_cents or 0) > 0:
            discount_row = QHBoxLayout()
            discount_label = QLabel("Discount:")
            discount_label.setStyleSheet(
                f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_SECONDARY}; "
                f"background: transparent; border: none;"
            )
            discount_value = QLabel(f"-{cents_to_display(invoice.discount_cents or 0)}")
            discount_value.setAlignment(Qt.AlignmentFlag.AlignRight)
            discount_value.setStyleSheet(
                f"font-size: {FONT_BODY}px; color: {COLOR_ERROR}; "
                f"background: transparent; border: none;"
            )
            discount_row.addWidget(discount_label)
            discount_row.addStretch()
            discount_row.addWidget(discount_value)
            summary_layout.addLayout(discount_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(2)
        sep.setStyleSheet(f"background-color: {COLOR_BORDER}; border: none;")
        summary_layout.addWidget(sep)

        # TOTAL (large bold)
        total_row = QHBoxLayout()
        total_label = QLabel("TOTAL:")
        total_label.setStyleSheet(
            f"font-size: {FONT_GRAND_TOTAL}px; font-weight: bold; "
            f"color: {COLOR_TEXT_PRIMARY}; background: transparent; border: none;"
        )
        total_value = QLabel(cents_to_display(invoice.total_cents or 0))
        total_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_value.setObjectName("grand_total")
        total_value.setStyleSheet(
            f"font-size: {FONT_GRAND_TOTAL}px; font-weight: bold; "
            f"color: {COLOR_TEXT_PRIMARY}; background: transparent; border: none;"
        )
        total_row.addWidget(total_label)
        total_row.addStretch()
        total_row.addWidget(total_value)
        summary_layout.addLayout(total_row)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background-color: {COLOR_BORDER}; border: none;")
        summary_layout.addWidget(sep2)

        # Paid
        paid_row = QHBoxLayout()
        paid_label = QLabel("Paid:")
        paid_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_SUCCESS}; "
            f"font-weight: bold; background: transparent; border: none;"
        )
        paid_value = QLabel(cents_to_display(invoice.paid_cents or 0))
        paid_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        paid_value.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_SUCCESS}; "
            f"font-weight: bold; background: transparent; border: none;"
        )
        paid_row.addWidget(paid_label)
        paid_row.addStretch()
        paid_row.addWidget(paid_value)
        summary_layout.addLayout(paid_row)

        # Due
        due_row = QHBoxLayout()
        due_cents = invoice.due_cents or 0
        due_color = COLOR_ERROR if due_cents > 0 else COLOR_SUCCESS
        due_label = QLabel("Due:")
        due_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {due_color}; "
            f"font-weight: bold; background: transparent; border: none;"
        )
        due_value = QLabel(cents_to_display(due_cents))
        due_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        due_value.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {due_color}; "
            f"font-weight: bold; background: transparent; border: none;"
        )
        due_row.addWidget(due_label)
        due_row.addStretch()
        due_row.addWidget(due_value)
        summary_layout.addLayout(due_row)

        self._detail_layout.addWidget(summary_frame)

    # ── Action Buttons ───────────────────────────────────────────

    def _build_action_buttons(self, invoice):
        action_frame = QFrame()
        action_frame.setStyleSheet(
            f"QFrame {{ background: transparent; border: none; }}"
        )
        action_layout = QHBoxLayout(action_frame)
        action_layout.setContentsMargins(0, SPACING_SM, 0, 0)
        action_layout.setSpacing(SPACING_SM)

        is_cancelled = (invoice.status or "").upper() == "CANCELLED"

        # Generate Invoice button (from job card)
        self._btn_generate = QPushButton("Generate Invoice")
        self._btn_generate.setObjectName("btn_primary")
        self._btn_generate.setFixedHeight(BUTTON_HEIGHT)
        self._btn_generate.clicked.connect(self._on_generate_invoice)
        action_layout.addWidget(self._btn_generate)

        # Record Payment
        self._btn_payment = QPushButton("Record Payment")
        self._btn_payment.setObjectName("btn_success")
        self._btn_payment.setFixedHeight(BUTTON_HEIGHT)
        self._btn_payment.clicked.connect(self._on_record_payment)
        if is_cancelled:
            self._btn_payment.setEnabled(False)
        action_layout.addWidget(self._btn_payment)

        # Print Thermal
        self._btn_thermal = QPushButton("Print Thermal")
        self._btn_thermal.setObjectName("btn_secondary")
        self._btn_thermal.setFixedHeight(BUTTON_HEIGHT)
        self._btn_thermal.clicked.connect(self._on_print_thermal)
        action_layout.addWidget(self._btn_thermal)

        # Print A4
        self._btn_a4 = QPushButton("Print A4")
        self._btn_a4.setObjectName("btn_secondary")
        self._btn_a4.setFixedHeight(BUTTON_HEIGHT)
        self._btn_a4.clicked.connect(self._on_print_a4)
        action_layout.addWidget(self._btn_a4)

        action_layout.addStretch()

        # Cancel Invoice (right-aligned, danger)
        self._btn_cancel = QPushButton("Cancel Invoice")
        self._btn_cancel.setObjectName("btn_danger")
        self._btn_cancel.setFixedHeight(BUTTON_HEIGHT)
        self._btn_cancel.clicked.connect(self._on_cancel_invoice)
        if is_cancelled:
            self._btn_cancel.setEnabled(False)
        action_layout.addWidget(self._btn_cancel)

        self._detail_layout.addWidget(action_frame)

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

            vehicle_display = ""
            if inv.vehicle_obj:
                vehicle_display = inv.vehicle_obj.registration_no or ""

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
                vehicle_display,
                total_display,
                paid_display,
                due_display,
                status_text,
                date_display,
            ])

        self._table.load_data(rows)

        # Insert StatusBadge widgets into the Status column (col 6)
        for row_idx, inv in enumerate(invoices):
            status_text = inv.status or ""
            badge = StatusBadge(status_text)
            self._table.setCellWidget(row_idx, 6, badge)

        # Re-select the current invoice if it's still in the list
        if self._current_invoice_id is not None:
            found = False
            for row_idx, inv in enumerate(invoices):
                if inv.id == self._current_invoice_id:
                    self._table.selectRow(row_idx)
                    found = True
                    break
            if not found:
                self._show_empty_state()

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

    # ── Selection Changed ────────────────────────────────────────

    def _on_selection_changed(self):
        """When the user selects a row in the invoice list, show its detail."""
        inv = self._get_selected_invoice()
        if inv:
            self._show_invoice_detail(inv.id)

    # ── Double-click ─────────────────────────────────────────────

    def _on_double_click(self, row, col):
        inv = self._get_selected_invoice()
        if inv:
            self._show_invoice_detail(inv.id)

    # ── Action: Generate Invoice from Job Card ───────────────────

    def _on_generate_invoice(self):
        """Open the job card selector dialog to generate an invoice."""
        dlg = JobCardSelectorDialog(
            jc_ctrl=self._jc_ctrl,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            job_card_id = dlg.get_selected_job_card_id()
            if job_card_id:
                try:
                    new_invoice = self._billing_ctrl.create_invoice_from_job_card(job_card_id)
                    if new_invoice:
                        self.refresh()
                        # Select the new invoice in the list
                        for row_idx, inv in enumerate(self._invoices_data):
                            if inv.id == new_invoice.id:
                                self._table.selectRow(row_idx)
                                break
                        self._show_invoice_detail(new_invoice.id)
                        QMessageBox.information(
                            self, "Success",
                            f"Invoice {new_invoice.invoice_number} created successfully."
                        )
                    else:
                        QMessageBox.warning(
                            self, "Error",
                            "Failed to create invoice. The job card may already have an invoice."
                        )
                except Exception:
                    logger.exception("Error creating invoice from job card")
                    QMessageBox.critical(self, "Error", "Failed to create invoice from job card.")

    # ── Action: Record Payment ───────────────────────────────────

    def _on_record_payment(self):
        """Open the payment dialog for the selected invoice."""
        inv = self._get_selected_invoice()
        if not inv:
            QMessageBox.information(self, "No Selection", "Please select an invoice first.")
            return

        if (inv.status or "").upper() == "CANCELLED":
            QMessageBox.warning(self, "Cancelled", "Cannot record payment on a cancelled invoice.")
            return

        if (inv.due_cents or 0) <= 0:
            QMessageBox.information(self, "Fully Paid", "This invoice is already fully paid.")
            return

        dlg = PaymentDialog(invoice=inv, billing_ctrl=self._billing_ctrl, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Refresh both the list and detail
            self.refresh()
            if self._current_invoice_id:
                self._show_invoice_detail(self._current_invoice_id)

    # ── Action: Print Thermal ────────────────────────────────────

    def _on_print_thermal(self):
        """Open the thermal receipt preview dialog."""
        inv = self._get_selected_invoice()
        if not inv:
            QMessageBox.information(self, "No Selection", "Please select an invoice first.")
            return

        invoice_data = self._build_invoice_data_dict(inv)
        dlg = ThermalReceiptPreviewDialog(invoice_data=invoice_data, parent=self)
        dlg.exec()

    # ── Action: Print A4 ─────────────────────────────────────────

    def _on_print_a4(self):
        """Generate A4 invoice PDF and show save dialog."""
        inv = self._get_selected_invoice()
        if not inv:
            QMessageBox.information(self, "No Selection", "Please select an invoice first.")
            return

        invoice_data = self._build_invoice_data_dict(inv)

        try:
            filepath = generate_a4_invoice_pdf(invoice_data)
            if filepath:
                QMessageBox.information(
                    self, "PDF Generated",
                    f"A4 Invoice PDF saved to:\n{filepath}"
                )
                # Try to open the PDF
                try:
                    if os.name == "nt":
                        os.startfile(filepath)
                    else:
                        import subprocess
                        opener = "xdg-open" if os.name != "darwin" else "open"
                        subprocess.Popen([opener, filepath])
                except Exception:
                    pass
            else:
                QMessageBox.warning(
                    self, "Error",
                    "Failed to generate A4 PDF. Ensure ReportLab is installed."
                )
        except Exception:
            logger.exception("Error generating A4 PDF")
            QMessageBox.critical(self, "Error", "Failed to generate A4 invoice PDF.")

    # ── Action: Cancel Invoice ───────────────────────────────────

    def _on_cancel_invoice(self):
        """Cancel the selected invoice after confirmation."""
        inv = self._get_selected_invoice()
        if not inv:
            QMessageBox.information(self, "No Selection", "Please select an invoice to cancel.")
            return

        if (inv.status or "").upper() == "CANCELLED":
            QMessageBox.information(self, "Already Cancelled", "This invoice is already cancelled.")
            return

        if (inv.paid_cents or 0) > 0:
            reply = QMessageBox.warning(
                self, "Warning",
                f"This invoice has payments recorded ({cents_to_display(inv.paid_cents)}).\n"
                f"Are you sure you want to cancel invoice <b>{inv.invoice_number}</b>?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        else:
            reply = QMessageBox.question(
                self, "Confirm Cancel",
                f"Are you sure you want to cancel invoice <b>{inv.invoice_number}</b>?\n"
                "This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            result = self._billing_ctrl.cancel_invoice(inv.id)
            if result:
                self.refresh()
                self._show_invoice_detail(inv.id)
                QMessageBox.information(self, "Cancelled", "Invoice has been cancelled.")
            else:
                QMessageBox.warning(self, "Error", "Failed to cancel invoice.")
        except Exception:
            logger.exception("Error cancelling invoice")
            QMessageBox.critical(self, "Error", "Failed to cancel invoice.")

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

        # Get latest payment method
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
#  Thermal Receipt Preview Dialog
# ═══════════════════════════════════════════════════════════════════

class ThermalReceiptPreviewDialog(QDialog):
    """Dialog showing thermal receipt preview with width selector."""

    def __init__(self, invoice_data: dict, parent=None):
        super().__init__(parent)
        self._invoice_data = invoice_data
        self._current_width = RECEIPT_CHARS_80MM

        self.setWindowTitle("Thermal Receipt Preview")
        self.setMinimumSize(520, 600)

        self._build_ui()
        self._refresh_preview()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_SM)

        # ── Width selector ──
        width_row = QHBoxLayout()
        width_row.setSpacing(SPACING_MD)

        width_label = QLabel("Paper Width:")
        width_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; font-weight: bold; "
            f"color: {COLOR_TEXT_PRIMARY}; background: transparent; border: none;"
        )
        width_row.addWidget(width_label)

        self._radio_80 = QRadioButton("80mm (48 chars)")
        self._radio_80.setChecked(True)
        self._radio_80.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_PRIMARY};"
        )
        width_row.addWidget(self._radio_80)

        self._radio_58 = QRadioButton("58mm (32 chars)")
        self._radio_58.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_PRIMARY};"
        )
        width_row.addWidget(self._radio_58)

        self._width_group = QButtonGroup(self)
        self._width_group.addButton(self._radio_80, RECEIPT_CHARS_80MM)
        self._width_group.addButton(self._radio_58, RECEIPT_CHARS_58MM)
        self._width_group.idClicked.connect(self._on_width_changed)

        width_row.addStretch()
        layout.addLayout(width_row)

        # ── Receipt preview ──
        self._preview = QPlainTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setFont(QFont("Consolas", 10))
        self._preview.setStyleSheet(
            f"QPlainTextEdit {{ "
            f"background-color: #FAFAFA; "
            f"border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 4px; "
            f"padding: {SPACING_SM}px; "
            f"font-family: {FONT_MONO}; "
            f"font-size: {FONT_RECEIPT}px; "
            f"}}"
        )
        layout.addWidget(self._preview, stretch=1)

        # ── Action buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING_SM)

        btn_print = QPushButton("Print")
        btn_print.setObjectName("btn_primary")
        btn_print.setFixedHeight(BUTTON_HEIGHT)
        btn_print.clicked.connect(self._on_print)
        btn_row.addWidget(btn_print)

        btn_save = QPushButton("Save to File")
        btn_save.setObjectName("btn_secondary")
        btn_save.setFixedHeight(BUTTON_HEIGHT)
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)

        btn_row.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setObjectName("btn_secondary")
        btn_close.setFixedHeight(BUTTON_HEIGHT)
        btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)

    def _on_width_changed(self, button_id: int):
        self._current_width = button_id
        self._refresh_preview()

    def _refresh_preview(self):
        text = generate_thermal_receipt_text(self._invoice_data, width=self._current_width)
        self._preview.setPlainText(text)

    def _on_print(self):
        """Send the receipt to the configured thermal printer."""
        from services.print_service import print_thermal
        try:
            filepath = print_thermal(self._invoice_data, width=self._current_width)
            if filepath:
                QMessageBox.information(
                    self, "Printed",
                    f"Receipt sent to printer.\nSaved: {filepath}"
                )
            else:
                QMessageBox.warning(self, "Error", "Failed to print receipt.")
        except Exception:
            logger.exception("Error printing thermal receipt")
            QMessageBox.critical(self, "Error", "Failed to print receipt.")

    def _on_save(self):
        """Save the receipt text to a file."""
        try:
            filepath = save_thermal_receipt(self._invoice_data, width=self._current_width)
            if filepath:
                QMessageBox.information(
                    self, "Saved",
                    f"Receipt saved to:\n{filepath}"
                )
            else:
                QMessageBox.warning(self, "Error", "Failed to save receipt.")
        except Exception:
            logger.exception("Error saving thermal receipt")
            QMessageBox.critical(self, "Error", "Failed to save receipt.")


# ═══════════════════════════════════════════════════════════════════
#  Payment Dialog
# ═══════════════════════════════════════════════════════════════════

class PaymentDialog(QDialog):
    """Dialog for recording a payment against an invoice."""

    def __init__(self, invoice, billing_ctrl: BillingController, parent=None):
        super().__init__(parent)
        self._invoice = invoice
        self._billing_ctrl = billing_ctrl

        self.setWindowTitle(f"Record Payment — {invoice.invoice_number}")
        self.setMinimumWidth(440)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # ── Invoice Summary ──
        summary_frame = QFrame()
        summary_frame.setObjectName("panel")
        summary_frame.setStyleSheet(
            f"QFrame#panel {{ background-color: {COLOR_PANEL_BG}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; }}"
        )
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        summary_layout.setSpacing(SPACING_XS)

        total_cents = self._invoice.total_cents or 0
        paid_cents = self._invoice.paid_cents or 0
        due_cents = self._invoice.due_cents or 0

        total_label = QLabel(f"Total:  {cents_to_display(total_cents)}")
        total_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_PRIMARY}; "
            f"background: transparent; border: none;"
        )
        summary_layout.addWidget(total_label)

        paid_label = QLabel(f"Paid:   {cents_to_display(paid_cents)}")
        paid_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_SUCCESS}; "
            f"font-weight: bold; background: transparent; border: none;"
        )
        summary_layout.addWidget(paid_label)

        due_label = QLabel(f"Due:    {cents_to_display(due_cents)}")
        due_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_ERROR}; "
            f"font-weight: bold; background: transparent; border: none;"
        )
        summary_layout.addWidget(due_label)

        layout.addWidget(summary_frame)

        # ── Payment Form ──
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(SPACING_MD)
        form.setVerticalSpacing(SPACING_SM)

        # Amount
        self._amount_spin = QDoubleSpinBox()
        self._amount_spin.setRange(0.01, due_cents / 100.0 if due_cents > 0 else 9999999.99)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setPrefix("Rs. ")
        self._amount_spin.setValue(due_cents / 100.0 if due_cents > 0 else 0)
        self._amount_spin.setFixedHeight(INPUT_HEIGHT)
        self._amount_spin.selectAll()
        form.addRow("Amount:", self._amount_spin)

        # Payment method
        self._method_combo = QComboBox()
        self._method_combo.addItems(["Cash", "Card", "Bank Transfer", "Cheque"])
        self._method_combo.setFixedHeight(INPUT_HEIGHT)
        self._method_combo.setMinimumWidth(200)
        form.addRow("Method:", self._method_combo)

        # Reference
        self._reference_edit = QLineEdit()
        self._reference_edit.setPlaceholderText("Optional reference / cheque #")
        self._reference_edit.setFixedHeight(INPUT_HEIGHT)
        form.addRow("Reference:", self._reference_edit)

        # Notes
        self._notes_edit = QLineEdit()
        self._notes_edit.setPlaceholderText("Optional notes")
        self._notes_edit.setFixedHeight(INPUT_HEIGHT)
        form.addRow("Notes:", self._notes_edit)

        layout.addLayout(form)

        # ── Quick amount buttons ──
        quick_row = QHBoxLayout()
        quick_row.setSpacing(SPACING_XS)

        quick_label = QLabel("Quick:")
        quick_label.setStyleSheet(
            f"font-size: {FONT_SMALL}px; color: {COLOR_TEXT_SECONDARY}; "
            f"background: transparent; border: none;"
        )
        quick_row.addWidget(quick_label)

        due_value = due_cents / 100.0

        btn_full = QPushButton("Full Amount")
        btn_full.setObjectName("btn_secondary")
        btn_full.setFixedHeight(BUTTON_HEIGHT - 4)
        btn_full.clicked.connect(lambda: self._amount_spin.setValue(due_value))
        quick_row.addWidget(btn_full)

        if due_value > 0:
            half_val = round(due_value / 2, 2)
            btn_half = QPushButton("Half")
            btn_half.setObjectName("btn_secondary")
            btn_half.setFixedHeight(BUTTON_HEIGHT - 4)
            btn_half.clicked.connect(lambda: self._amount_spin.setValue(half_val))
            quick_row.addWidget(btn_half)

        quick_row.addStretch()
        layout.addLayout(quick_row)

        # ── Dialog buttons ──
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.button(QDialogButtonBox.StandardButton.Save).setText("Record Payment")
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_save(self):
        amount_cents = int(round(self._amount_spin.value() * 100))
        if amount_cents <= 0:
            QMessageBox.warning(self, "Validation", "Please enter a valid amount.")
            return

        due_cents = self._invoice.due_cents or 0
        if amount_cents > due_cents:
            reply = QMessageBox.warning(
                self, "Overpayment",
                f"The entered amount ({cents_to_display(amount_cents)}) exceeds the due "
                f"amount ({cents_to_display(due_cents)}).\nContinue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        method_text = self._method_combo.currentText().upper().replace(" ", "_")
        reference = self._reference_edit.text().strip()
        notes = self._notes_edit.text().strip()

        kwargs = {
            "method": method_text,
        }
        if reference:
            kwargs["reference"] = reference
        if notes:
            kwargs["notes"] = notes

        try:
            payment = self._billing_ctrl.record_payment(
                invoice_id=self._invoice.id,
                amount_cents=amount_cents,
                **kwargs,
            )
            if payment:
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to record payment.")
        except Exception:
            logger.exception("Error recording payment")
            QMessageBox.critical(self, "Error", "Failed to record payment. Please try again.")


# ═══════════════════════════════════════════════════════════════════
#  Job Card Selector Dialog (Generate Invoice from Job Card)
# ═══════════════════════════════════════════════════════════════════

class JobCardSelectorDialog(QDialog):
    """Dialog listing completed job cards that don't have invoices yet."""

    def __init__(self, jc_ctrl: JobCardController, parent=None):
        super().__init__(parent)
        self._jc_ctrl = jc_ctrl
        self._selected_job_card_id = None
        self._job_cards_data: List = []

        self.setWindowTitle("Select Job Card — Generate Invoice")
        self.setMinimumSize(750, 480)

        self._build_ui()
        self._load_job_cards()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # ── Info label ──
        info_label = QLabel("Select a completed job card to generate an invoice:")
        info_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_SECONDARY}; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(info_label)

        # ── Table ──
        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            ["Job #", "Vehicle", "Customer", "Items", "Labor", "Total", "Date"]
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)
        self._table.horizontalHeader().setFixedHeight(TABLE_HEADER_HEIGHT)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 90)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(1, 110)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(3, 60)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(4, 100)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(5, 110)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(6, 100)

        self._table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table, stretch=1)

        # ── Dialog buttons ──
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("Generate Invoice")
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _load_job_cards(self):
        """Load completed job cards that don't have invoices."""
        try:
            # Get completed job cards
            all_completed = self._jc_ctrl.get_job_cards(status="COMPLETED")
        except Exception:
            logger.exception("Error loading completed job cards")
            all_completed = []

        # Filter out those that already have invoices
        self._job_cards_data = []
        for jc in all_completed:
            if not jc.invoice:
                self._job_cards_data.append(jc)

        self._table.setRowCount(len(self._job_cards_data))
        for row_idx, jc in enumerate(self._job_cards_data):
            vehicle_display = ""
            if jc.vehicle:
                vehicle_display = jc.vehicle.registration_no or ""

            customer_display = ""
            if jc.customer_obj:
                customer_display = jc.customer_obj.name or ""

            items_count = len(jc.items) if jc.items else 0
            labor_display = cents_to_display(jc.labor_charge_cents or 0)
            total_display = cents_to_display(jc.total_cents or 0)
            date_display = ""
            if jc.completed_at:
                date_display = jc.completed_at.strftime("%Y-%m-%d")
            elif jc.created_at:
                date_display = jc.created_at.strftime("%Y-%m-%d")

            num_item = QTableWidgetItem(jc.job_number or "")
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row_idx, 0, num_item)

            veh_item = QTableWidgetItem(vehicle_display)
            veh_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row_idx, 1, veh_item)

            cust_item = QTableWidgetItem(customer_display)
            cust_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row_idx, 2, cust_item)

            count_item = QTableWidgetItem(str(items_count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row_idx, 3, count_item)

            labor_item = QTableWidgetItem(labor_display)
            labor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row_idx, 4, labor_item)

            total_item = QTableWidgetItem(total_display)
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row_idx, 5, total_item)

            date_item = QTableWidgetItem(date_display)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row_idx, 6, date_item)

        if not self._job_cards_data:
            info_label = self.findChild(QLabel)
            if info_label:
                info_label.setText("No completed job cards without invoices found.")

    def _on_double_click(self):
        """Double-click selects and accepts."""
        self._on_accept()

    def _on_accept(self):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._job_cards_data):
            QMessageBox.information(self, "No Selection", "Please select a job card.")
            return

        jc = self._job_cards_data[row]
        self._selected_job_card_id = jc.id
        self.accept()

    def get_selected_job_card_id(self) -> Optional[int]:
        return self._selected_job_card_id
