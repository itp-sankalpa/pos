"""Customer controller — bridges the UI and customer_service layer."""

import logging
from typing import Optional, List

from services.customer_service import (
    get_all_customers,
    get_customer_by_id,
    create_customer,
    update_customer,
    delete_customer,
    get_customer_count,
)
from models.customer import Customer

logger = logging.getLogger(__name__)


class CustomerController:
    """Delegates customer operations to customer_service."""

    def __init__(self):
        """No-argument constructor."""
        pass

    # ── Read operations ─────────────────────────────────────────────

    def get_customers(self, search: Optional[str] = None) -> List[Customer]:
        """Return all active customers, optionally filtered by search term.

        Search matches against name or phone (case-insensitive).
        """
        return get_all_customers(search=search)

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """Return a single Customer by ID, or None if not found."""
        return get_customer_by_id(customer_id)

    def get_customer_count(self) -> int:
        """Return the count of active customers."""
        return get_customer_count()

    # ── Write operations ────────────────────────────────────────────

    def create_customer(self, name: str, phone: str, **kwargs) -> Optional[Customer]:
        """Create a new customer record.

        Accepted kwargs: email, address, nic, notes.
        Returns the created Customer, or None on error.
        """
        return create_customer(name=name, phone=phone, **kwargs)

    def update_customer(self, customer_id: int, **kwargs) -> Optional[Customer]:
        """Update the given customer's fields.

        Accepted kwargs: name, phone, email, address, nic, notes, is_active.
        Returns the updated Customer, or None on error.
        """
        return update_customer(customer_id, **kwargs)

    def delete_customer(self, customer_id: int) -> bool:
        """Soft-delete a customer by setting is_active=False.

        Returns True on success, False on error or not found.
        """
        return delete_customer(customer_id)
