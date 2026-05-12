"""Billing controller — bridges the UI and invoice_service / payment_service layers."""

import logging
from typing import Optional, List

from services.invoice_service import (
    get_all_invoices,
    get_invoice_by_id,
    create_invoice_from_job_card,
    add_invoice_item,
    remove_invoice_item,
    recalculate_invoice,
    cancel_invoice,
)
from services.payment_service import (
    create_payment,
    get_payments_by_invoice,
)
from models.invoice import Invoice, InvoiceItem
from models.payment import Payment

logger = logging.getLogger(__name__)


class BillingController:
    """Delegates billing operations to invoice_service and payment_service."""

    def __init__(self):
        """No-argument constructor."""
        pass

    # ── Invoice read operations ─────────────────────────────────────

    def get_invoices(
        self, status: Optional[str] = None, search: Optional[str] = None
    ) -> List[Invoice]:
        """Return all invoices, optionally filtered by status and search term.

        Search matches against invoice_number, vehicle registration_no, or
        customer name.
        """
        return get_all_invoices(status=status, search=search)

    def get_invoice(self, invoice_id: int) -> Optional[Invoice]:
        """Return a single Invoice by ID with relationships loaded, or None."""
        return get_invoice_by_id(invoice_id)

    # ── Invoice write operations ────────────────────────────────────

    def create_invoice_from_job_card(self, job_card_id: int) -> Optional[Invoice]:
        """Create an invoice from a completed job card.

        Copies all job card items, calculates subtotal, labor, discount,
        total, and due amounts.
        Returns the created Invoice, or None on error.
        """
        return create_invoice_from_job_card(job_card_id)

    def add_invoice_item(
        self, invoice_id: int, description: str, **kwargs
    ) -> Optional[InvoiceItem]:
        """Add a line item to an invoice and recalculate totals.

        Accepted kwargs: quantity, unit_price_cents, item_type.
        Returns the created InvoiceItem, or None on error.
        """
        return add_invoice_item(
            invoice_id=invoice_id,
            description=description,
            **kwargs,
        )

    def remove_invoice_item(self, item_id: int) -> bool:
        """Remove an invoice item by ID and recalculate totals.

        Returns True on success, False on error or not found.
        """
        return remove_invoice_item(item_id)

    def recalculate_invoice(self, invoice_id: int) -> Optional[Invoice]:
        """Recalculate subtotal, total, and due from items + labor - discount.

        Also updates invoice status (PAID / PARTIAL / UNPAID) based on
        payment amounts.
        Returns the updated Invoice, or None on error.
        """
        return recalculate_invoice(invoice_id)

    def cancel_invoice(self, invoice_id: int) -> Optional[Invoice]:
        """Cancel an invoice by setting its status to CANCELLED.

        Returns the updated Invoice, or None on error.
        """
        return cancel_invoice(invoice_id)

    # ── Payment operations ──────────────────────────────────────────

    def record_payment(
        self, invoice_id: int, amount_cents: int, **kwargs
    ) -> Optional[Payment]:
        """Record a payment against an invoice.

        Updates invoice paid_cents, due_cents, and status accordingly.
        Accepted kwargs: method, reference, notes, received_by.
        Returns the created Payment, or None on error.
        """
        return create_payment(
            invoice_id=invoice_id,
            amount_cents=amount_cents,
            **kwargs,
        )

    def get_invoice_payments(self, invoice_id: int) -> List[Payment]:
        """Return all payments for the given invoice, newest first."""
        return get_payments_by_invoice(invoice_id)
