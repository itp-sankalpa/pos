"""Invoice service — CRUD and business logic for invoices and invoice items."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from config import INVOICE_PREFIX
from database import SessionContext
from models.job_card import JobCard, JobCardItem
from models.invoice import Invoice, InvoiceItem
from models.customer import Customer
from models.vehicle import Vehicle

logger = logging.getLogger(__name__)


def _generate_invoice_number(session) -> str:
    """Auto-generate the next invoice number as INV-YYYYMMDD-XXXX.

    XXXX is a 4-digit sequential counter that resets each day.
    """
    today_str = datetime.utcnow().strftime("%Y%m%d")
    today_prefix = f"{INVOICE_PREFIX}-{today_str}-"

    # Count invoices created today to determine the next sequence number
    result = session.execute(
        select(func.count(Invoice.id)).where(
            Invoice.invoice_number.like(f"{today_prefix}%")
        )
    ).scalar()
    next_seq = (result or 0) + 1

    return f"{today_prefix}{next_seq:04d}"


def get_all_invoices(status: Optional[str] = None, search: Optional[str] = None) -> list:
    """Return all invoices, optionally filtered by status and search term.

    Search matches against invoice_number, vehicle registration_no, or customer name.
    Results are returned newest-first with relationships loaded.
    """
    try:
        with SessionContext() as session:
            stmt = (
                select(Invoice)
                .options(
                    selectinload(Invoice.customer_obj),
                    selectinload(Invoice.vehicle_obj),
                    selectinload(Invoice.items),
                    selectinload(Invoice.payments),
                )
                .order_by(Invoice.created_at.desc())
            )

            if status:
                stmt = stmt.where(Invoice.status == status)

            if search:
                search_pattern = f"%{search}%"
                stmt = stmt.join(Invoice.customer_obj, isouter=True).join(
                    Invoice.vehicle_obj, isouter=True
                ).where(
                    or_(
                        Invoice.invoice_number.ilike(search_pattern),
                        Vehicle.registration_no.ilike(search_pattern),
                        Customer.name.ilike(search_pattern),
                    )
                )

            result = session.execute(stmt)
            return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error getting all invoices: {e}")
        return []


def get_invoice_by_id(invoice_id: int) -> Optional[Invoice]:
    """Return a single invoice by its primary key, or None if not found."""
    try:
        with SessionContext() as session:
            stmt = (
                select(Invoice)
                .options(
                    selectinload(Invoice.customer_obj),
                    selectinload(Invoice.vehicle_obj),
                    selectinload(Invoice.job_card),
                    selectinload(Invoice.items),
                    selectinload(Invoice.payments),
                )
                .where(Invoice.id == invoice_id)
            )
            result = session.execute(stmt)
            return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting invoice by id {invoice_id}: {e}")
        return None


def get_invoice_by_number(invoice_number: str) -> Optional[Invoice]:
    """Return a single invoice by its invoice number, or None if not found."""
    try:
        with SessionContext() as session:
            stmt = (
                select(Invoice)
                .options(
                    selectinload(Invoice.customer_obj),
                    selectinload(Invoice.vehicle_obj),
                    selectinload(Invoice.job_card),
                    selectinload(Invoice.items),
                    selectinload(Invoice.payments),
                )
                .where(Invoice.invoice_number == invoice_number)
            )
            result = session.execute(stmt)
            return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting invoice by number {invoice_number}: {e}")
        return None


def create_invoice_from_job_card(job_card_id: int) -> Optional[Invoice]:
    """Create an invoice from a job card.

    - Auto-generates invoice_number as INV-YYYYMMDD-XXXX.
    - Copies all items from the job card items.
    - Calculates subtotal, labor, discount, total, and due.
    """
    try:
        with SessionContext() as session:
            # Load the job card with its items
            stmt = (
                select(JobCard)
                .options(selectinload(JobCard.items))
                .where(JobCard.id == job_card_id)
            )
            result = session.execute(stmt)
            job_card = result.scalars().first()

            if not job_card:
                logger.warning(f"Job card {job_card_id} not found for invoice creation")
                return None

            # Check if an invoice already exists for this job card
            existing = session.execute(
                select(Invoice).where(Invoice.job_card_id == job_card_id)
            ).scalars().first()
            if existing:
                logger.warning(
                    f"Invoice already exists for job card {job_card_id}: "
                    f"{existing.invoice_number}"
                )
                return None

            invoice_number = _generate_invoice_number(session)

            # Copy items from job card and compute subtotal
            subtotal_cents = 0
            invoice_items = []
            for jc_item in job_card.items:
                inv_item = InvoiceItem(
                    description=jc_item.description,
                    quantity=jc_item.quantity,
                    unit_price_cents=jc_item.unit_price_cents,
                    line_total_cents=jc_item.line_total_cents,
                    item_type=jc_item.item_type,
                )
                invoice_items.append(inv_item)
                subtotal_cents += jc_item.line_total_cents

            total_cents = subtotal_cents + job_card.labor_charge_cents - job_card.discount_cents
            due_cents = total_cents  # no payments yet

            invoice = Invoice(
                invoice_number=invoice_number,
                job_card_id=job_card_id,
                customer_id=job_card.customer_id,
                vehicle_id=job_card.vehicle_id,
                status="UNPAID",
                subtotal_cents=subtotal_cents,
                labor_charge_cents=job_card.labor_charge_cents,
                discount_cents=job_card.discount_cents,
                total_cents=total_cents,
                paid_cents=0,
                due_cents=due_cents,
                items=invoice_items,
            )
            session.add(invoice)
            session.flush()

            session.refresh(invoice)
            _ = invoice.customer_obj
            _ = invoice.vehicle_obj
            _ = invoice.items
            _ = invoice.payments

            logger.info(f"Created invoice {invoice_number} from job card {job_card.job_number}")
            return invoice
    except Exception as e:
        logger.error(f"Error creating invoice from job card {job_card_id}: {e}")
        return None


def update_invoice(invoice_id: int, **kwargs) -> Optional[Invoice]:
    """Update an invoice's fields given by kwargs. Returns the updated Invoice or None."""
    try:
        with SessionContext() as session:
            stmt = select(Invoice).where(Invoice.id == invoice_id)
            result = session.execute(stmt)
            invoice = result.scalars().first()

            if not invoice:
                logger.warning(f"Invoice {invoice_id} not found for update")
                return None

            protected_fields = {"id", "invoice_number"}
            for key, value in kwargs.items():
                if key in protected_fields:
                    continue
                if hasattr(invoice, key):
                    setattr(invoice, key, value)

            invoice.updated_at = datetime.utcnow()
            session.flush()

            session.refresh(invoice)
            _ = invoice.customer_obj
            _ = invoice.vehicle_obj
            _ = invoice.items
            _ = invoice.payments

            logger.info(f"Updated invoice {invoice.invoice_number}")
            return invoice
    except Exception as e:
        logger.error(f"Error updating invoice {invoice_id}: {e}")
        return None


def add_invoice_item(
    invoice_id: int,
    description: str,
    quantity: int,
    unit_price_cents: int,
    item_type: str = "PART",
) -> Optional[InvoiceItem]:
    """Add a line item to an invoice and recalculate totals."""
    try:
        with SessionContext() as session:
            stmt = select(Invoice).where(Invoice.id == invoice_id)
            result = session.execute(stmt)
            invoice = result.scalars().first()

            if not invoice:
                logger.warning(f"Invoice {invoice_id} not found for adding item")
                return None

            line_total_cents = quantity * unit_price_cents

            item = InvoiceItem(
                invoice_id=invoice_id,
                description=description,
                quantity=quantity,
                unit_price_cents=unit_price_cents,
                line_total_cents=line_total_cents,
                item_type=item_type,
            )
            session.add(item)

            # Update subtotal on the invoice
            invoice.subtotal_cents += line_total_cents
            invoice.total_cents = (
                invoice.subtotal_cents
                + invoice.labor_charge_cents
                - invoice.discount_cents
            )
            invoice.due_cents = invoice.total_cents - invoice.paid_cents
            invoice.updated_at = datetime.utcnow()

            session.flush()

            logger.info(f"Added item to invoice {invoice.invoice_number}")
            return item
    except Exception as e:
        logger.error(f"Error adding item to invoice {invoice_id}: {e}")
        return None


def remove_invoice_item(item_id: int) -> bool:
    """Remove an invoice item by its id and recalculate totals. Returns True on success."""
    try:
        with SessionContext() as session:
            stmt = select(InvoiceItem).where(InvoiceItem.id == item_id)
            result = session.execute(stmt)
            item = result.scalars().first()

            if not item:
                logger.warning(f"Invoice item {item_id} not found for removal")
                return False

            invoice_id = item.invoice_id
            line_total = item.line_total_cents
            session.delete(item)

            # Recalculate the invoice totals
            _recalculate_invoice_in_session(session, invoice_id)

            logger.info(f"Removed invoice item {item_id}")
            return True
    except Exception as e:
        logger.error(f"Error removing invoice item {item_id}: {e}")
        return False


def _recalculate_invoice_in_session(session, invoice_id: int) -> None:
    """Internal helper to recalculate invoice totals within an existing session."""
    stmt = select(Invoice).where(Invoice.id == invoice_id)
    result = session.execute(stmt)
    invoice = result.scalars().first()
    if not invoice:
        return

    # Sum all remaining items
    items_result = session.execute(
        select(func.coalesce(func.sum(InvoiceItem.line_total_cents), 0)).where(
            InvoiceItem.invoice_id == invoice_id
        )
    ).scalar()

    invoice.subtotal_cents = items_result
    invoice.total_cents = (
        invoice.subtotal_cents
        + invoice.labor_charge_cents
        - invoice.discount_cents
    )
    invoice.due_cents = invoice.total_cents - invoice.paid_cents
    invoice.updated_at = datetime.utcnow()

    # Update status based on payment
    if invoice.due_cents <= 0:
        invoice.status = "PAID"
    elif invoice.paid_cents > 0:
        invoice.status = "PARTIAL"
    else:
        invoice.status = "UNPAID"


def recalculate_invoice(invoice_id: int) -> Optional[Invoice]:
    """Recalculate subtotal, total, and due from items + labor - discount."""
    try:
        with SessionContext() as session:
            _recalculate_invoice_in_session(session, invoice_id)

            stmt = (
                select(Invoice)
                .options(
                    selectinload(Invoice.items),
                    selectinload(Invoice.payments),
                )
                .where(Invoice.id == invoice_id)
            )
            result = session.execute(stmt)
            invoice = result.scalars().first()

            if invoice:
                logger.info(f"Recalculated invoice {invoice.invoice_number}")

            return invoice
    except Exception as e:
        logger.error(f"Error recalculating invoice {invoice_id}: {e}")
        return None


def cancel_invoice(invoice_id: int) -> Optional[Invoice]:
    """Cancel an invoice by setting its status to CANCELLED."""
    try:
        with SessionContext() as session:
            stmt = select(Invoice).where(Invoice.id == invoice_id)
            result = session.execute(stmt)
            invoice = result.scalars().first()

            if not invoice:
                logger.warning(f"Invoice {invoice_id} not found for cancellation")
                return None

            invoice.status = "CANCELLED"
            invoice.updated_at = datetime.utcnow()
            session.flush()

            session.refresh(invoice)
            _ = invoice.customer_obj
            _ = invoice.vehicle_obj
            _ = invoice.items
            _ = invoice.payments

            logger.info(f"Cancelled invoice {invoice.invoice_number}")
            return invoice
    except Exception as e:
        logger.error(f"Error cancelling invoice {invoice_id}: {e}")
        return None
