"""Customer management service."""

import logging
from typing import Optional, List

from sqlalchemy import select, func, or_

from database import SessionContext
from models.customer import Customer

logger = logging.getLogger(__name__)


def get_all_customers(search: Optional[str] = None) -> List[Customer]:
    """
    Return all active customers, optionally filtered by a search term
    that matches against name or phone (case-insensitive, LIKE).
    """
    try:
        with SessionContext() as session:
            stmt = select(Customer).where(Customer.is_active == True)  # noqa: E712

            if search:
                pattern = f"%{search}%"
                stmt = stmt.where(
                    or_(
                        Customer.name.ilike(pattern),
                        Customer.phone.ilike(pattern),
                    )
                )

            stmt = stmt.order_by(Customer.name)
            customers = list(session.execute(stmt).scalars().all())
            for c in customers:
                session.expunge(c)
            return customers

    except Exception:
        logger.exception("Error fetching customers (search='%s').", search)
        return []


def get_customer_by_id(customer_id: int) -> Optional[Customer]:
    """Return a Customer by primary key, or None if not found."""
    try:
        with SessionContext() as session:
            customer = session.get(Customer, customer_id)
            if customer is not None:
                session.expunge(customer)
            return customer

    except Exception:
        logger.exception("Error fetching customer id %d.", customer_id)
        return None


def create_customer(
    name: str,
    phone: str,
    email: Optional[str] = None,
    address: Optional[str] = None,
    nic: Optional[str] = None,
    notes: Optional[str] = None,
) -> Optional[Customer]:
    """
    Create a new customer record.

    Returns the created Customer object, or None on error.
    """
    try:
        with SessionContext() as session:
            customer = Customer(
                name=name,
                phone=phone,
                email=email,
                address=address,
                nic=nic,
                notes=notes,
            )
            session.add(customer)
            session.flush()
            session.expunge(customer)
            return customer

    except Exception:
        logger.exception("Error creating customer '%s'.", name)
        return None


def update_customer(customer_id: int, **kwargs) -> Optional[Customer]:
    """
    Update the given customer's fields.

    Accepted keyword args correspond to Customer columns:
        name, phone, email, address, nic, notes, is_active

    Returns the updated Customer, or None on error.
    """
    try:
        with SessionContext() as session:
            customer = session.get(Customer, customer_id)
            if customer is None:
                logger.warning("Cannot update: customer id %d not found.", customer_id)
                return None

            allowed_fields = {
                "name", "phone", "email", "address", "nic", "notes", "is_active"
            }
            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(customer, key, value)
                else:
                    logger.warning("Ignoring unknown field '%s' in customer update.", key)

            session.flush()
            session.expunge(customer)
            return customer

    except Exception:
        logger.exception("Error updating customer id %d.", customer_id)
        return None


def delete_customer(customer_id: int) -> bool:
    """
    Soft-delete a customer by setting is_active=False.

    Returns True on success, False on error or not found.
    """
    try:
        with SessionContext() as session:
            customer = session.get(Customer, customer_id)
            if customer is None:
                logger.warning("Cannot delete: customer id %d not found.", customer_id)
                return False

            customer.is_active = False
            return True

    except Exception:
        logger.exception("Error deleting customer id %d.", customer_id)
        return False


def get_customer_count() -> int:
    """Return the count of active customers."""
    try:
        with SessionContext() as session:
            stmt = select(func.count()).select_from(Customer).where(
                Customer.is_active == True  # noqa: E712
            )
            count = session.execute(stmt).scalar()
            return count or 0

    except Exception:
        logger.exception("Error counting customers.")
        return 0
