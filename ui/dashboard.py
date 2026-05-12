"""
DashboardScreen — main overview screen for the Vehicle Service Center POS.
Displays summary cards, recent job cards, and quick revenue stats.
"""

import tkinter as tk
from tkinter import ttk

from ui.theme import *
from ui.components import PageHeader, SummaryCard, DataTable, StatusBadge
from controllers.dashboard_controller import DashboardController
from config import cents_to_display

# ── Page indices in the stacked widget (sync with main window) ──────────
PAGE_JOB_CARDS = 1

# ── Month name map for revenue display ──────────────────────────────────
_MONTH_NAMES = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}


class DashboardScreen(tk.Frame):
    """Dashboard overview screen with summary cards, recent jobs, and stats."""

    def __init__(self, session, stacked_widget=None, parent=None, **kwargs):
        super().__init__(parent, bg=COLOR_APP_BG, **kwargs)

        self._session = session
        self._stacked_widget = stacked_widget
        self._controller = DashboardController()

        # ── Keep references to SummaryCards for refresh ──
        self._cards: dict[str, SummaryCard] = {}

        # ── Keep references to revenue row widgets for refresh ──
        self._revenue_widgets: list[tk.Frame] = []

        # ── Main container ──
        main_frame = tk.Frame(self, bg=COLOR_APP_BG)
        main_frame.pack(fill="both", expand=True,
                        padx=SPACING_LG, pady=SPACING_LG)

        # ── Page header ──
        self._header = PageHeader(
            "Dashboard", subtitle="Overview of your service center",
            parent=main_frame,
        )

        # ── Summary cards row ──
        cards_frame = tk.Frame(main_frame, bg=COLOR_APP_BG)
        cards_frame.pack(fill="x", pady=(0, SPACING_MD))

        card_defs = [
            ("today_jobs",      "Today's Jobs",      COLOR_ACCENT),
            ("pending_jobs",    "Pending Jobs",      COLOR_WARNING),
            ("in_progress",     "In Progress",       COLOR_INFO),
            ("today_revenue",   "Today's Revenue",   COLOR_SUCCESS),
            ("unpaid_invoices", "Unpaid Invoices",   COLOR_ERROR),
            ("low_stock",       "Low Stock Items",   COLOR_WARNING),
        ]

        for key, title, accent in card_defs:
            card = SummaryCard(
                title, value="0", accent_color=accent,
                parent=cards_frame,
            )
            self._cards[key] = card
            card.pack(side="left", padx=(0, SPACING_SM))

        # ── Split view: recent jobs (left) | revenue stats (right) ──
        split_frame = tk.Frame(main_frame, bg=COLOR_APP_BG)
        split_frame.pack(fill="both", expand=True)
        split_frame.columnconfigure(0, weight=3)
        split_frame.columnconfigure(1, weight=2)
        split_frame.rowconfigure(0, weight=1)

        # -- LEFT: Recent Job Cards panel --
        left_panel = self._build_recent_jobs_panel(split_frame)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING_XS))

        # -- RIGHT: Monthly Revenue panel --
        right_panel = self._build_revenue_panel(split_frame)
        right_panel.grid(row=0, column=1, sticky="nsew")

        # ── Initial data load ──
        self.refresh()

    # ── Panel builders ───────────────────────────────────────────────

    def _build_recent_jobs_panel(self, parent) -> tk.Frame:
        """Build the left panel containing the recent job cards table."""
        panel = tk.Frame(
            parent, bg=COLOR_PANEL_BG,
            highlightbackground=COLOR_BORDER, highlightthickness=1,
        )

        layout = tk.Frame(panel, bg=COLOR_PANEL_BG)
        layout.pack(fill="both", expand=True,
                    padx=SPACING_MD, pady=SPACING_MD)

        # Section title
        title_label = tk.Label(
            layout, text="Recent Job Cards",
            font=(FONT_FAMILY, FONT_SECTION_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, anchor="w",
        )
        title_label.pack(fill="x", pady=(0, SPACING_SM))

        # Table columns: (header_text, column_width_px)
        self._jobs_table = DataTable(
            columns=[
                ("Job #",   100),
                ("Vehicle", 160),
                ("Customer", 150),
                ("Status",   120),
                ("Date",     110),
            ],
            parent=layout,
        )
        self._jobs_table.set_double_click_handler(self._on_job_double_clicked)
        self._jobs_table.pack(fill="both", expand=True)

        return panel

    def _build_revenue_panel(self, parent) -> tk.Frame:
        """Build the right panel showing monthly revenue stats."""
        panel = tk.Frame(
            parent, bg=COLOR_PANEL_BG,
            highlightbackground=COLOR_BORDER, highlightthickness=1,
        )

        layout = tk.Frame(panel, bg=COLOR_PANEL_BG)
        layout.pack(fill="both", expand=True,
                    padx=SPACING_MD, pady=SPACING_MD)

        # Section title
        title_label = tk.Label(
            layout, text="Monthly Revenue",
            font=(FONT_FAMILY, FONT_SECTION_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, anchor="w",
        )
        title_label.pack(fill="x", pady=(0, SPACING_XS))

        # Subtitle
        subtitle_label = tk.Label(
            layout, text="Last 6 months",
            font=(FONT_FAMILY, FONT_SMALL),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, anchor="w",
        )
        subtitle_label.pack(fill="x", pady=(0, SPACING_SM))

        # Revenue rows will be populated dynamically in this container
        self._revenue_container = tk.Frame(layout, bg=COLOR_PANEL_BG)
        self._revenue_container.pack(fill="both", expand=True)

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

        rows = []
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

        self._jobs_table.load_data(rows)

    def _load_monthly_revenue(self) -> None:
        """Populate the monthly revenue rows."""
        # Clear existing revenue rows
        for widget in self._revenue_widgets:
            widget.destroy()
        self._revenue_widgets.clear()

        try:
            revenue_data = self._controller.get_monthly_revenue(months=6)
        except Exception:
            revenue_data = []

        for entry in revenue_data:
            month_key = entry.get("month", "")
            revenue_cents = entry.get("revenue_cents", 0)

            # Parse "YYYY-MM" → "Mon YYYY"
            display_month = month_key
            if len(month_key) == 7 and "-" in month_key:
                year_part, mon_part = month_key.split("-", 1)
                display_month = f"{_MONTH_NAMES.get(mon_part, mon_part)} {year_part}"

            # Row frame
            row_frame = tk.Frame(self._revenue_container, bg=COLOR_PANEL_BG)
            row_frame.pack(fill="x", pady=SPACING_XS)

            # Month label
            month_label = tk.Label(
                row_frame, text=display_month,
                font=(FONT_FAMILY, FONT_BODY),
                fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, anchor="w",
                width=12,
            )
            month_label.pack(side="left")

            # Accent dot
            dot_label = tk.Label(
                row_frame, text="\u25CF",
                font=(FONT_FAMILY, 10),
                fg=COLOR_ACCENT, bg=COLOR_PANEL_BG,
            )
            dot_label.pack(side="left", padx=(SPACING_XS, SPACING_XS))

            # Revenue label
            revenue_label = tk.Label(
                row_frame, text=cents_to_display(revenue_cents),
                font=(FONT_FAMILY, FONT_BODY, "bold"),
                fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, anchor="w",
            )
            revenue_label.pack(side="left")

            self._revenue_widgets.append(row_frame)

    # ── Event handlers ───────────────────────────────────────────────

    def _on_job_double_clicked(self, row_index: int) -> None:
        """Handle double-click on a job row — navigate to Job Cards screen."""
        # In Tkinter version, navigation is handled by MainWindow._switch_page
        # The stacked_widget is the content frame, not a QStackedWidget
        pass
