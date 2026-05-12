"""Payment service — CRUD and business logic for payments."""

import logging
from datetime import datetime, date
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database import SessionContext
from models.invoice import Invoice
from models.payment import Payment

logger = logging.getLogger(__name__)


def get_payments_by_invoice(invoice_id: int) -> list:
    """Return all payments for a given invoice, newest first."""
    try:
        with SessionContext() as session:
            stmt = (
                select(Payment)
                .where(Payment.invoice_id == invoice_id)
                .order_by(Payment.created_at.desc())
            )
            result = session.execute(stmt)
            return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error getting payments for invoice {invoice_id}: {e}")
        return []


def create_payment(
    invoice_id: int,
    amount_cents: int,
    method: str = "CASH",
    reference: Optional[str] = None,
    notes: Optional[str] = None,
    received_by: Optional[int] = None,
) -> Optional[Payment]:
    """Record a payment against an invoice.

    - Updates the invoice's paid_cents and due_cents.
    - Updates invoice status to PAID (if fully paid) or PARTIAL (if partially paid).
    """
    try:
        with SessionContext() as session:
            # Load the invoice
            stmt = select(Invoice).where(Invoice.id == invoice_id)
            result = session.execute(stmt)
            invoice = result.scalars().first()

            if not invoice:
                logger.warning(f"Invoice {invoice_id} not found for payment")
                return None

            if invoice.status == "CANCELLED":
                logger.warning(f"Cannot add payment to cancelled invoice {invoice_id}")
                return None

            if amount_cents <= 0:
                logger.warning(f"Invalid payment amount: {amount_cents}")
                return None

            payment = Payment(
                invoice_id=invoice_id,
                amount_cents=amount_cents,
                method=method,
                reference=reference,
                notes=notes,
                received_by=received_by,
            )
            session.add(payment)

            # Update invoice paid and due amounts
            invoice.paid_cents += amount_cents
            invoice.due_cents = invoice.total_cents - invoice.paid_cents

            # Cap due at zero — no overpayment credit tracking
            if invoice.due_cents < 0:
                invoice.due_cents = 0

            # Update invoice status
            if invoice.due_cents <= 0:
                invoice.status = "PAID"
            else:
                invoice.status = "PARTIAL"

            invoice.updated_at = datetime.utcnow()
            session.flush()

            logger.info(
                f"Recorded payment of {amount_cents} cents for invoice "
                f"{invoice.invoice_number} via {method}"
            )
            return payment
    except Exception as e:
        logger.error(f"Error creating payment for invoice {invoice_id}: {e}")
        return None


def get_total_payments_for_invoice(invoice_id: int) -> int:
    """Return the total cents paid across all payments for a given invoice."""
    try:
        with SessionContext() as session:
            result = session.execute(
                select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(
                    Payment.invoice_id == invoice_id
                )
            ).scalar()
            return result or 0
    except Exception as e:
        logger.error(f"Error getting total payments for invoice {invoice_id}: {e}")
        return 0


def get_daily_payments(target_date: Optional[date] = None) -> list:
    """Return all payments for a given date (defaults to today), newest first."""
    try:
        if target_date is None:
            target_date = date.today()

        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())

        with SessionContext() as session:
            stmt = (
                select(Payment)
                .options(
                    selectinload(Payment.invoice),
                )
                .where(
                    Payment.created_at >= start_datetime,
                    Payment.created_at <= end_datetime,
                )
                .order_by(Payment.created_at.desc())
            )
            result = session.execute(stmt)
            return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error getting daily payments for {target_date}: {e}")
        return []


def get_payment_methods_summary(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> dict:
    """Return a dict mapping payment method -> total cents for the given date range.

    If no dates are provided, returns summary for today.
    """
    try:
        if date_from is None:
            date_from = date.today()
        if date_to is None:
            date_to = date.today()

        start_datetime = datetime.combine(date_from, datetime.min.time())
        end_datetime = datetime.combine(date_to, datetime.max.time())

        with SessionContext() as session:
            result = session.execute(
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

            return {row[0]: row[1] for row in result}
    except Exception as e:
        logger.error(f"Error getting payment methods summary: {e}")
        return {}
