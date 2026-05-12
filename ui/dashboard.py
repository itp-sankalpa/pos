"""
DashboardScreen — main overview screen for the Vehicle Service Center POS.
Displays summary cards, recent job cards, and quick revenue stats.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QFrame,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt

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
    FONT_SECTION_TITLE,
    FONT_BODY,
    FONT_SMALL,
    SPACING_XS,
    SPACING_SM,
    SPACING_MD,
    SPACING_LG,
)
from ui.components import PageHeader, SummaryCard, DataTable, StatusBadge
from controllers.dashboard_controller import DashboardController
from config import cents_to_display

# ── Page indices in the stacked widget (sync with main window) ──────────
PAGE_JOB_CARDS = 1


class DashboardScreen(QWidget):
    """Dashboard overview screen with summary cards, recent jobs, and stats."""

    def __init__(self, session, stacked_widget=None, parent=None):
        super().__init__(parent)

        self._session = session
        self._stacked_widget = stacked_widget
        self._controller = DashboardController()

        # ── Keep references to SummaryCards for refresh ──
        self._cards: dict[str, SummaryCard] = {}

        # ── Main layout ──
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        main_layout.setSpacing(SPACING_MD)

        # ── Page header ──
        self._header = PageHeader("Dashboard", subtitle="Overview of your service center")
        main_layout.addWidget(self._header)

        # ── Summary cards row ──
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(SPACING_SM)

        card_defs = [
            ("today_jobs",      "Today's Jobs",      COLOR_ACCENT),
            ("pending_jobs",    "Pending Jobs",      COLOR_WARNING),
            ("in_progress",     "In Progress",       COLOR_INFO),
            ("today_revenue",   "Today's Revenue",   COLOR_SUCCESS),
            ("unpaid_invoices", "Unpaid Invoices",   COLOR_ERROR),
            ("low_stock",       "Low Stock Items",   COLOR_WARNING),
        ]

        for key, title, accent in card_defs:
            card = SummaryCard(title, value="0", accent_color=accent)
            self._cards[key] = card
            cards_layout.addWidget(card)

        # Push cards to the left; absorb extra horizontal space
        cards_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        main_layout.addLayout(cards_layout)

        # ── Splitter: recent jobs (left) | quick stats (right) ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(SPACING_XS)

        # -- LEFT: Recent Job Cards panel --
        left_panel = self._build_recent_jobs_panel()
        splitter.addWidget(left_panel)

        # -- RIGHT: Quick Stats panel --
        right_panel = self._build_quick_stats_panel()
        splitter.addWidget(right_panel)

        # Initial sizes: 60 % left, 40 % right
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter, stretch=1)

        # ── Initial data load ──
        self.refresh()

    # ── Panel builders ───────────────────────────────────────────────

    def _build_recent_jobs_panel(self) -> QFrame:
        """Build the left panel containing the recent job cards table."""
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setStyleSheet(
            f"QFrame#panel {{ background-color: {COLOR_PANEL_BG}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; }}"
        )

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_SM)

        # Section title
        title_label = QLabel("Recent Job Cards")
        title_label.setObjectName("section_title")
        title_label.setStyleSheet(
            f"font-size: {FONT_SECTION_TITLE}px; font-weight: bold; "
            f"color: {COLOR_TEXT_PRIMARY}; background: transparent; border: none;"
        )
        layout.addWidget(title_label)

        # Table columns: (header_text, column_width_px) — 0 means stretch
        self._jobs_table = DataTable(
            columns=[
                ("Job #",  100),
                ("Vehicle", 160),
                ("Customer", 150),
                ("Status",  120),
                ("Date",    110),
            ]
        )
        self._jobs_table.set_double_click_handler(self._on_job_double_clicked)
        layout.addWidget(self._jobs_table)

        return panel

    def _build_quick_stats_panel(self) -> QFrame:
        """Build the right panel showing monthly revenue stats."""
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setStyleSheet(
            f"QFrame#panel {{ background-color: {COLOR_PANEL_BG}; "
            f"border: 1px solid {COLOR_BORDER}; border-radius: 6px; }}"
        )

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_SM)

        # Section title
        title_label = QLabel("Quick Stats")
        title_label.setObjectName("section_title")
        title_label.setStyleSheet(
            f"font-size: {FONT_SECTION_TITLE}px; font-weight: bold; "
            f"color: {COLOR_TEXT_PRIMARY}; background: transparent; border: none;"
        )
        layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Monthly Revenue (last 6 months)")
        subtitle_label.setStyleSheet(
            f"font-size: {FONT_SMALL}px; color: {COLOR_TEXT_SECONDARY}; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(subtitle_label)

        # Revenue rows will be populated dynamically
        self._revenue_container = QVBoxLayout()
        self._revenue_container.setSpacing(SPACING_XS)
        layout.addLayout(self._revenue_container)

        # Push content to top
        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        return panel

    # ── Data loading ─────────────────────────────────────────────────

    def refresh(self) -> None:
        """Reload all dashboard data from the controller."""
        self._load_stats()
        self._load_recent_jobs()
        self._load_monthly_revenue()

    def _load_stats(self) -> None:
        """Update summary cards from controller stats."""
        try:
            stats = self._controller.get_stats()
        except Exception:
            stats = {
                "today_jobs": 0,
                "pending_jobs": 0,
                "in_progress_jobs": 0,
                "today_revenue_cents": 0,
                "unpaid_invoices_count": 0,
                "low_stock_count": 0,
            }

        self._cards["today_jobs"].set_value(str(stats.get("today_jobs", 0)))
        self._cards["pending_jobs"].set_value(str(stats.get("pending_jobs", 0)))
        self._cards["in_progress"].set_value(str(stats.get("in_progress_jobs", 0)))
        self._cards["today_revenue"].set_value(
            cents_to_display(stats.get("today_revenue_cents", 0))
        )
        self._cards["unpaid_invoices"].set_value(
            str(stats.get("unpaid_invoices_count", 0))
        )
        self._cards["low_stock"].set_value(str(stats.get("low_stock_count", 0)))

    def _load_recent_jobs(self) -> None:
        """Populate the recent job cards table."""
        try:
            jobs = self._controller.get_recent_jobs(limit=10)
        except Exception:
            jobs = []

        # Build row data (status column will be replaced with StatusBadge)
        status_col = 3  # index of the Status column
        rows = []
        statuses = []

        for job in jobs:
            vehicle_display = ""
            if job.vehicle:
                vehicle_display = job.vehicle.display_name

            customer_display = ""
            if job.customer_obj:
                customer_display = job.customer_obj.name

            date_display = ""
            if job.created_at:
                date_display = job.created_at.strftime("%Y-%m-%d")

            rows.append([
                job.job_number,
                vehicle_display,
                customer_display,
                job.status,
                date_display,
            ])
            statuses.append(job.status)

        self._jobs_table.load_data(rows)

        # Replace status column cells with StatusBadge widgets
        for row_idx, status_text in enumerate(statuses):
            badge = StatusBadge(status_text)
            self._jobs_table.setCellWidget(row_idx, status_col, badge)

    def _load_monthly_revenue(self) -> None:
        """Populate the quick stats revenue rows."""
        # Clear existing revenue rows
        while self._revenue_container.count():
            item = self._revenue_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            # Also handle layout items
            if item.layout():
                # Recursively clear sub-layouts
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        try:
            revenue_data = self._controller.get_monthly_revenue(months=6)
        except Exception:
            revenue_data = []

        # Map short month keys to friendlier display (e.g. "2025-01" → "Jan 2025")
        month_names = {
            "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
            "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
            "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
        }

        for entry in revenue_data:
            month_key = entry.get("month", "")
            revenue_cents = entry.get("revenue_cents", 0)

            # Parse "YYYY-MM" → "Mon YYYY"
            display_month = month_key
            if len(month_key) == 7 and "-" in month_key:
                year_part, mon_part = month_key.split("-", 1)
                display_month = f"{month_names.get(mon_part, mon_part)} {year_part}"

            row_layout = QHBoxLayout()
            row_layout.setSpacing(SPACING_SM)

            month_label = QLabel(display_month)
            month_label.setStyleSheet(
                f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_SECONDARY}; "
                f"background: transparent; border: none;"
            )
            month_label.setMinimumWidth(90)
            row_layout.addWidget(month_label)

            # Accent dot
            dot_label = QLabel("●")
            dot_label.setStyleSheet(
                f"font-size: 10px; color: {COLOR_ACCENT}; "
                f"background: transparent; border: none;"
            )
            row_layout.addWidget(dot_label)

            revenue_label = QLabel(cents_to_display(revenue_cents))
            revenue_label.setStyleSheet(
                f"font-size: {FONT_BODY}px; font-weight: bold; "
                f"color: {COLOR_TEXT_PRIMARY}; background: transparent; border: none;"
            )
            row_layout.addWidget(revenue_label)

            row_layout.addStretch()
            self._revenue_container.addLayout(row_layout)

    # ── Event handlers ───────────────────────────────────────────────

    def _on_job_double_clicked(self, row: int, column: int) -> None:
        """Handle double-click on a job row — navigate to Job Cards screen."""
        if self._stacked_widget is not None:
            self._stacked_widget.setCurrentIndex(PAGE_JOB_CARDS)
