"""Dashboard controller — bridges the UI and dashboard_service layer."""

import logging
from typing import List

from services.dashboard_service import (
    get_dashboard_stats,
    get_recent_job_cards,
    get_monthly_revenue,
)

logger = logging.getLogger(__name__)


class DashboardController:
    """Delegates dashboard operations to dashboard_service."""

    def __init__(self):
        """No-argument constructor."""
        pass

    # ── Dashboard data ──────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Return a dict of aggregate statistics for the dashboard.

        Keys: today_jobs, pending_jobs, in_progress_jobs, completed_jobs,
        today_revenue_cents, unpaid_invoices_count, unpaid_total_cents,
        low_stock_count, total_customers, total_vehicles.
        """
        return get_dashboard_stats()

    def get_recent_jobs(self, limit: int = 10) -> list:
        """Return the most recent job cards with vehicle and customer info.

        Args:
            limit: Maximum number of job cards to return (default 10).
        """
        return get_recent_job_cards(limit=limit)

    def get_monthly_revenue(self, months: int = 6) -> list:
        """Return monthly revenue data for the last N months.

        Returns a list of dicts: [{month: str, revenue_cents: int}, ...]
        Suitable for chart rendering.
        """
        return get_monthly_revenue(months=months)
