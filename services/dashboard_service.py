"""Dashboard service — aggregate queries for the main dashboard view."""

import logging
from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy import select, func, case, and_

from database import SessionContext
from models.job_card import JobCard
from models.invoice import Invoice
from models.payment import Payment
from models.customer import Customer
from models.vehicle import Vehicle
from models.inventory import InventoryItem

logger = logging.getLogger(__name__)


def get_dashboard_stats() -> dict:
    """Return a dict of aggregate statistics for the dashboard.

    Keys:
        today_jobs, pending_jobs, in_progress_jobs, completed_jobs,
        today_revenue_cents, unpaid_invoices_count, unpaid_total_cents,
        low_stock_count, total_customers, total_vehicles
    """
    try:
        with SessionContext() as session:
            today_start = datetime.combine(date.today(), datetime.min.time())
            today_end = datetime.combine(date.today(), datetime.max.time())

            # ── Job card counts ────────────────────────────────────
            today_jobs = session.execute(
                select(func.count(JobCard.id)).where(
                    JobCard.created_at >= today_start,
                    JobCard.created_at <= today_end,
                )
            ).scalar() or 0

            pending_jobs = session.execute(
                select(func.count(JobCard.id)).where(JobCard.status == "PENDING")
            ).scalar() or 0

            in_progress_jobs = session.execute(
                select(func.count(JobCard.id)).where(JobCard.status == "IN_PROGRESS")
            ).scalar() or 0

            completed_jobs = session.execute(
                select(func.count(JobCard.id)).where(JobCard.status == "COMPLETED")
            ).scalar() or 0

            # ── Today's revenue (sum of payments received today) ──
            today_revenue_cents = session.execute(
                select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(
                    Payment.created_at >= today_start,
                    Payment.created_at <= today_end,
                )
            ).scalar() or 0

            # ── Unpaid invoices ────────────────────────────────────
            unpaid_result = session.execute(
                select(
                    func.count(Invoice.id),
                    func.coalesce(func.sum(Invoice.due_cents), 0),
                ).where(
                    Invoice.status.in_(["UNPAID", "PARTIAL"])
                )
            ).one()

            unpaid_invoices_count = unpaid_result[0] or 0
            unpaid_total_cents = unpaid_result[1] or 0

            # ── Low stock items ────────────────────────────────────
            low_stock_count = session.execute(
                select(func.count(InventoryItem.id)).where(
                    InventoryItem.is_active == True,
                    InventoryItem.quantity_in_stock <= InventoryItem.reorder_level,
                )
            ).scalar() or 0

            # ── Total customers and vehicles ───────────────────────
            total_customers = session.execute(
                select(func.count(Customer.id))
            ).scalar() or 0

            total_vehicles = session.execute(
                select(func.count(Vehicle.id))
            ).scalar() or 0

            return {
                "today_jobs": today_jobs,
                "pending_jobs": pending_jobs,
                "in_progress_jobs": in_progress_jobs,
                "completed_jobs": completed_jobs,
                "today_revenue_cents": today_revenue_cents,
                "unpaid_invoices_count": unpaid_invoices_count,
                "unpaid_total_cents": unpaid_total_cents,
                "low_stock_count": low_stock_count,
                "total_customers": total_customers,
                "total_vehicles": total_vehicles,
            }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            "today_jobs": 0,
            "pending_jobs": 0,
            "in_progress_jobs": 0,
            "completed_jobs": 0,
            "today_revenue_cents": 0,
            "unpaid_invoices_count": 0,
            "unpaid_total_cents": 0,
            "low_stock_count": 0,
            "total_customers": 0,
            "total_vehicles": 0,
        }


def get_recent_job_cards(limit: int = 10) -> list:
    """Return the most recent job cards with vehicle and customer info pre-loaded."""
    try:
        with SessionContext() as session:
            from sqlalchemy.orm import selectinload

            stmt = (
                select(JobCard)
                .options(
                    selectinload(JobCard.vehicle),
                    selectinload(JobCard.customer_obj),
                    selectinload(JobCard.assigned_mechanic_obj),
                )
                .order_by(JobCard.created_at.desc())
                .limit(limit)
            )
            result = session.execute(stmt)
            return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error getting recent job cards: {e}")
        return []


def get_monthly_revenue(months: int = 6) -> list:
    """Return a list of {month, revenue_cents} dicts for the last N months.

    Uses SQLite's strftime for month grouping. Suitable for chart rendering.
    """
    try:
        with SessionContext() as session:
            # Calculate the start date for the range
            today = date.today()
            start_date = today.replace(day=1) - timedelta(days=(months - 1) * 31)
            # Normalize to first of the month
            start_date = start_date.replace(day=1)
            start_datetime = datetime.combine(start_date, datetime.min.time())

            # Group payments by month using SQLite strftime
            rows = session.execute(
                select(
                    func.strftime("%Y-%m", Payment.created_at).label("month"),
                    func.coalesce(func.sum(Payment.amount_cents), 0).label(
                        "revenue_cents"
                    ),
                )
                .where(Payment.created_at >= start_datetime)
                .group_by(func.strftime("%Y-%m", Payment.created_at))
                .order_by(func.strftime("%Y-%m", Payment.created_at))
            ).all()

            # Build a complete list covering all months in the range (fill gaps with 0)
            result = []
            current = start_date
            revenue_map = {row[0]: row[1] for row in rows}

            for _ in range(months):
                month_key = current.strftime("%Y-%m")
                result.append(
                    {
                        "month": month_key,
                        "revenue_cents": revenue_map.get(month_key, 0),
                    }
                )
                # Advance to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

            return result
    except Exception as e:
        logger.error(f"Error getting monthly revenue: {e}")
        return []
