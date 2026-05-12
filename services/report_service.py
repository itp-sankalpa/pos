"""Report service — aggregate queries for business reports."""

import logging
from datetime import datetime, date
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database import SessionContext
from models.job_card import JobCard
from models.invoice import Invoice
from models.payment import Payment
from models.customer import Customer
from models.vehicle import Vehicle
from models.inventory import InventoryItem

logger = logging.getLogger(__name__)


def get_revenue_report(date_from: date, date_to: date) -> dict:
    """Return a revenue report for the given date range.

    Returns:
        {
            total_revenue_cents: int,
            total_jobs: int,
            total_invoices: int,
            avg_job_value_cents: int,
            by_day: [{date: str, revenue_cents: int, jobs: int, invoices: int}, ...]
        }
    """
    try:
        start_datetime = datetime.combine(date_from, datetime.min.time())
        end_datetime = datetime.combine(date_to, datetime.max.time())

        with SessionContext() as session:
            # ── Aggregate totals from payments ──────────────────────
            total_revenue_cents = session.execute(
                select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(
                    Payment.created_at >= start_datetime,
                    Payment.created_at <= end_datetime,
                )
            ).scalar() or 0

            total_jobs = session.execute(
                select(func.count(JobCard.id)).where(
                    JobCard.created_at >= start_datetime,
                    JobCard.created_at <= end_datetime,
                )
            ).scalar() or 0

            total_invoices = session.execute(
                select(func.count(Invoice.id)).where(
                    Invoice.created_at >= start_datetime,
                    Invoice.created_at <= end_datetime,
                )
            ).scalar() or 0

            avg_job_value_cents = (
                total_revenue_cents // total_jobs if total_jobs > 0 else 0
            )

            # ── Daily breakdown ────────────────────────────────────
            # Payments grouped by day
            payment_rows = session.execute(
                select(
                    func.strftime("%Y-%m-%d", Payment.created_at).label("day"),
                    func.coalesce(func.sum(Payment.amount_cents), 0).label(
                        "revenue_cents"
                    ),
                )
                .where(
                    Payment.created_at >= start_datetime,
                    Payment.created_at <= end_datetime,
                )
                .group_by(func.strftime("%Y-%m-%d", Payment.created_at))
            ).all()
            revenue_by_day = {row[0]: row[1] for row in payment_rows}

            # Jobs grouped by day
            job_rows = session.execute(
                select(
                    func.strftime("%Y-%m-%d", JobCard.created_at).label("day"),
                    func.count(JobCard.id).label("jobs"),
                )
                .where(
                    JobCard.created_at >= start_datetime,
                    JobCard.created_at <= end_datetime,
                )
                .group_by(func.strftime("%Y-%m-%d", JobCard.created_at))
            ).all()
            jobs_by_day = {row[0]: row[1] for row in job_rows}

            # Invoices grouped by day
            invoice_rows = session.execute(
                select(
                    func.strftime("%Y-%m-%d", Invoice.created_at).label("day"),
                    func.count(Invoice.id).label("invoices"),
                )
                .where(
                    Invoice.created_at >= start_datetime,
                    Invoice.created_at <= end_datetime,
                )
                .group_by(func.strftime("%Y-%m-%d", Invoice.created_at))
            ).all()
            invoices_by_day = {row[0]: row[1] for row in invoice_rows}

            # Merge into unified day list
            all_days = sorted(
                set(revenue_by_day.keys())
                | set(jobs_by_day.keys())
                | set(invoices_by_day.keys())
            )

            by_day = [
                {
                    "date": day,
                    "revenue_cents": revenue_by_day.get(day, 0),
                    "jobs": jobs_by_day.get(day, 0),
                    "invoices": invoices_by_day.get(day, 0),
                }
                for day in all_days
            ]

            return {
                "total_revenue_cents": total_revenue_cents,
                "total_jobs": total_jobs,
                "total_invoices": total_invoices,
                "avg_job_value_cents": avg_job_value_cents,
                "by_day": by_day,
            }
    except Exception as e:
        logger.error(f"Error getting revenue report: {e}")
        return {
            "total_revenue_cents": 0,
            "total_jobs": 0,
            "total_invoices": 0,
            "avg_job_value_cents": 0,
            "by_day": [],
        }


def get_job_card_report(
    date_from: date,
    date_to: date,
    status: Optional[str] = None,
) -> list:
    """Return a list of job cards in the given period, optionally filtered by status.

    Each job card has vehicle and customer relationships pre-loaded.
    """
    try:
        start_datetime = datetime.combine(date_from, datetime.min.time())
        end_datetime = datetime.combine(date_to, datetime.max.time())

        with SessionContext() as session:
            stmt = (
                select(JobCard)
                .options(
                    selectinload(JobCard.vehicle),
                    selectinload(JobCard.customer_obj),
                    selectinload(JobCard.assigned_mechanic_obj),
                    selectinload(JobCard.items),
                )
                .where(
                    JobCard.created_at >= start_datetime,
                    JobCard.created_at <= end_datetime,
                )
                .order_by(JobCard.created_at.desc())
            )

            if status:
                stmt = stmt.where(JobCard.status == status)

            result = session.execute(stmt)
            return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error getting job card report: {e}")
        return []


def get_inventory_report() -> dict:
    """Return a comprehensive inventory report.

    Returns:
        {
            total_items: int,
            total_value_cents: int,
            low_stock_items: [InventoryItem, ...],
            by_category: {category: {count: int, value_cents: int}, ...}
        }
    """
    try:
        with SessionContext() as session:
            # ── Total active items ─────────────────────────────────
            total_items = session.execute(
                select(func.count(InventoryItem.id)).where(
                    InventoryItem.is_active == True
                )
            ).scalar() or 0

            # ── Total inventory value (sell_price * qty) ───────────
            total_value_cents = session.execute(
                select(
                    func.coalesce(
                        func.sum(
                            InventoryItem.sell_price_cents
                            * InventoryItem.quantity_in_stock
                        ),
                        0,
                    )
                ).where(InventoryItem.is_active == True)
            ).scalar() or 0

            # ── Low stock items ────────────────────────────────────
            low_stock_stmt = (
                select(InventoryItem)
                .where(
                    InventoryItem.is_active == True,
                    InventoryItem.quantity_in_stock <= InventoryItem.reorder_level,
                )
                .order_by(InventoryItem.quantity_in_stock.asc())
            )
            low_stock_result = session.execute(low_stock_stmt)
            low_stock_items = list(low_stock_result.scalars().all())

            # ── By category ────────────────────────────────────────
            category_rows = session.execute(
                select(
                    func.coalesce(InventoryItem.category, "Uncategorized").label(
                        "category"
                    ),
                    func.count(InventoryItem.id).label("count"),
                    func.coalesce(
                        func.sum(
                            InventoryItem.sell_price_cents
                            * InventoryItem.quantity_in_stock
                        ),
                        0,
                    ).label("value_cents"),
                )
                .where(InventoryItem.is_active == True)
                .group_by(InventoryItem.category)
            ).all()

            by_category = {
                row[0]: {"count": row[1], "value_cents": row[2]}
                for row in category_rows
            }

            return {
                "total_items": total_items,
                "total_value_cents": total_value_cents,
                "low_stock_items": low_stock_items,
                "by_category": by_category,
            }
    except Exception as e:
        logger.error(f"Error getting inventory report: {e}")
        return {
            "total_items": 0,
            "total_value_cents": 0,
            "low_stock_items": [],
            "by_category": {},
        }


def get_payment_report(date_from: date, date_to: date) -> dict:
    """Return a payment report for the given date range.

    Returns:
        {
            total_cents: int,
            by_method: {method: total_cents, ...},
            daily_breakdown: [{date: str, total_cents: int, by_method: {method: cents}}, ...]
        }
    """
    try:
        start_datetime = datetime.combine(date_from, datetime.min.time())
        end_datetime = datetime.combine(date_to, datetime.max.time())

        with SessionContext() as session:
            # ── Total ──────────────────────────────────────────────
            total_cents = session.execute(
                select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(
                    Payment.created_at >= start_datetime,
                    Payment.created_at <= end_datetime,
                )
            ).scalar() or 0

            # ── By method ──────────────────────────────────────────
            method_rows = session.execute(
                select(
                    Payment.method,
                    func.coalesce(func.sum(Payment.amount_cents), 0),
                )
                .where(
                    Payment.created_at >= start_datetime,
                    Payment.created_at <= end_datetime,
                )
                .group_by(Payment.method)
            ).all()

            by_method = {row[0]: row[1] for row in method_rows}

            # ── Daily breakdown ────────────────────────────────────
            daily_rows = session.execute(
                select(
                    func.strftime("%Y-%m-%d", Payment.created_at).label("day"),
                    Payment.method,
                    func.coalesce(func.sum(Payment.amount_cents), 0).label("total"),
                )
                .where(
                    Payment.created_at >= start_datetime,
                    Payment.created_at <= end_datetime,
                )
                .group_by(
                    func.strftime("%Y-%m-%d", Payment.created_at),
                    Payment.method,
                )
            ).all()

            # Organize: {date: {method: total_cents}}
            daily_map: dict[str, dict[str, int]] = {}
            for row in daily_rows:
                day_key = row[0]
                method = row[1]
                total = row[2]
                if day_key not in daily_map:
                    daily_map[day_key] = {}
                daily_map[day_key][method] = total

            daily_breakdown = [
                {
                    "date": day,
                    "total_cents": sum(methods.values()),
                    "by_method": methods,
                }
                for day, methods in sorted(daily_map.items())
            ]

            return {
                "total_cents": total_cents,
                "by_method": by_method,
                "daily_breakdown": daily_breakdown,
            }
    except Exception as e:
        logger.error(f"Error getting payment report: {e}")
        return {
            "total_cents": 0,
            "by_method": {},
            "daily_breakdown": [],
        }


def get_customer_report() -> dict:
    """Return a customer report with summary statistics.

    Returns:
        {
            total_customers: int,
            with_vehicles: int,
            with_active_jobs: int
        }
    """
    try:
        with SessionContext() as session:
            # Total customers
            total_customers = session.execute(
                select(func.count(Customer.id))
            ).scalar() or 0

            # Customers that have at least one vehicle
            with_vehicles = session.execute(
                select(func.count(func.distinct(Vehicle.customer_id)))
            ).scalar() or 0

            # Customers that have at least one active (PENDING or IN_PROGRESS) job card
            with_active_jobs = session.execute(
                select(func.count(func.distinct(JobCard.customer_id))).where(
                    JobCard.status.in_(["PENDING", "IN_PROGRESS"])
                )
            ).scalar() or 0

            return {
                "total_customers": total_customers,
                "with_vehicles": with_vehicles,
                "with_active_jobs": with_active_jobs,
            }
    except Exception as e:
        logger.error(f"Error getting customer report: {e}")
        return {
            "total_customers": 0,
            "with_vehicles": 0,
            "with_active_jobs": 0,
        }
