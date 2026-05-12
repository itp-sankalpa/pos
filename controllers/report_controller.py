"""Report controller — bridges the UI and report_service layer."""

import logging
from datetime import date
from typing import Optional, List

from services.report_service import (
    get_revenue_report,
    get_job_card_report,
    get_inventory_report,
    get_payment_report,
    get_customer_report,
)

logger = logging.getLogger(__name__)


class ReportController:
    """Delegates report operations to report_service."""

    def __init__(self):
        """No-argument constructor."""
        pass

    # ── Report endpoints ────────────────────────────────────────────

    def get_revenue_report(self, date_from: date, date_to: date) -> dict:
        """Return a revenue report for the given date range.

        Returns:
            {
                total_revenue_cents: int,
                total_jobs: int,
                total_invoices: int,
                avg_job_value_cents: int,
                by_day: [{date, revenue_cents, jobs, invoices}, ...]
            }
        """
        return get_revenue_report(date_from, date_to)

    def get_job_card_report(
        self,
        date_from: date,
        date_to: date,
        status: Optional[str] = None,
    ) -> list:
        """Return a list of job cards in the given period.

        Optionally filter by status. Each job card has vehicle, customer,
        and items pre-loaded.
        """
        return get_job_card_report(date_from, date_to, status=status)

    def get_inventory_report(self) -> dict:
        """Return a comprehensive inventory report.

        Returns:
            {
                total_items: int,
                total_value_cents: int,
                low_stock_items: [InventoryItem, ...],
                by_category: {category: {count, value_cents}, ...}
            }
        """
        return get_inventory_report()

    def get_payment_report(self, date_from: date, date_to: date) -> dict:
        """Return a payment report for the given date range.

        Returns:
            {
                total_cents: int,
                by_method: {method: total_cents, ...},
                daily_breakdown: [{date, total_cents, by_method}, ...]
            }
        """
        return get_payment_report(date_from, date_to)

    def get_customer_report(self) -> dict:
        """Return a customer report with summary statistics.

        Returns:
            {
                total_customers: int,
                with_vehicles: int,
                with_active_jobs: int
            }
        """
        return get_customer_report()
