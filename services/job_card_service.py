"""Job Card service — CRUD and business logic for job cards and job card items."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from config import JOB_CARD_PREFIX
from database import SessionContext
from models.job_card import JobCard, JobCardItem
from models.vehicle import Vehicle
from models.customer import Customer

logger = logging.getLogger(__name__)


def _generate_job_number(session) -> str:
    """Auto-generate the next job number as JC-XXXX (4-digit sequential)."""
    result = session.execute(
        select(func.max(JobCard.id))
    ).scalar()
    next_seq = (result or 0) + 1
    return f"{JOB_CARD_PREFIX}-{next_seq:04d}"


def get_all_job_cards(status: Optional[str] = None, search: Optional[str] = None) -> list:
    """Return all job cards, optionally filtered by status and search term.

    Search matches against job_number, vehicle registration_no, or customer name.
    Results are returned newest-first with vehicle and customer relationships loaded.
    """
    try:
        with SessionContext() as session:
            stmt = (
                select(JobCard)
                .options(
                    selectinload(JobCard.vehicle),
                    selectinload(JobCard.customer_obj),
                    selectinload(JobCard.assigned_mechanic_obj),
                    selectinload(JobCard.items),
                )
                .order_by(JobCard.created_at.desc())
            )

            if status:
                stmt = stmt.where(JobCard.status == status)

            if search:
                search_pattern = f"%{search}%"
                stmt = stmt.join(JobCard.vehicle, isouter=True).join(
                    JobCard.customer_obj, isouter=True
                ).where(
                    or_(
                        JobCard.job_number.ilike(search_pattern),
                        Vehicle.registration_no.ilike(search_pattern),
                        Customer.name.ilike(search_pattern),
                    )
                )

            result = session.execute(stmt)
            return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error getting all job cards: {e}")
        return []


def get_job_card_by_id(job_card_id: int) -> Optional[JobCard]:
    """Return a single job card by its primary key, or None if not found."""
    try:
        with SessionContext() as session:
            stmt = (
                select(JobCard)
                .options(
                    selectinload(JobCard.vehicle),
                    selectinload(JobCard.customer_obj),
                    selectinload(JobCard.assigned_mechanic_obj),
                    selectinload(JobCard.items),
                )
                .where(JobCard.id == job_card_id)
            )
            result = session.execute(stmt)
            return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting job card by id {job_card_id}: {e}")
        return None


def get_job_card_by_number(job_number: str) -> Optional[JobCard]:
    """Return a single job card by its job number, or None if not found."""
    try:
        with SessionContext() as session:
            stmt = (
                select(JobCard)
                .options(
                    selectinload(JobCard.vehicle),
                    selectinload(JobCard.customer_obj),
                    selectinload(JobCard.assigned_mechanic_obj),
                    selectinload(JobCard.items),
                )
                .where(JobCard.job_number == job_number)
            )
            result = session.execute(stmt)
            return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting job card by number {job_number}: {e}")
        return None


def create_job_card(
    vehicle_id: int,
    customer_id: int,
    complaint: Optional[str] = None,
    assigned_mechanic: Optional[int] = None,
    mileage_in: Optional[int] = None,
    labor_charge_cents: int = 0,
) -> Optional[JobCard]:
    """Create a new job card with an auto-generated job number (JC-XXXX)."""
    try:
        with SessionContext() as session:
            job_number = _generate_job_number(session)

            job_card = JobCard(
                job_number=job_number,
                vehicle_id=vehicle_id,
                customer_id=customer_id,
                complaint=complaint,
                assigned_mechanic=assigned_mechanic,
                mileage_in=mileage_in,
                labor_charge_cents=labor_charge_cents,
                status="PENDING",
                discount_cents=0,
                stock_deducted=False,
            )
            session.add(job_card)
            session.flush()

            # Load relationships before the session closes
            session.refresh(job_card)
            _ = job_card.vehicle
            _ = job_card.customer_obj
            _ = job_card.items

            logger.info(f"Created job card {job_number}")
            return job_card
    except Exception as e:
        logger.error(f"Error creating job card: {e}")
        return None


def update_job_card(job_card_id: int, **kwargs) -> Optional[JobCard]:
    """Update a job card's fields given by kwargs. Returns the updated JobCard or None."""
    try:
        with SessionContext() as session:
            stmt = select(JobCard).where(JobCard.id == job_card_id)
            result = session.execute(stmt)
            job_card = result.scalars().first()

            if not job_card:
                logger.warning(f"Job card {job_card_id} not found for update")
                return None

            # Prevent updating protected fields via kwargs
            protected_fields = {"id", "job_number"}
            for key, value in kwargs.items():
                if key in protected_fields:
                    continue
                if hasattr(job_card, key):
                    setattr(job_card, key, value)

            job_card.updated_at = datetime.utcnow()
            session.flush()

            session.refresh(job_card)
            _ = job_card.vehicle
            _ = job_card.customer_obj
            _ = job_card.items

            logger.info(f"Updated job card {job_card.job_number}")
            return job_card
    except Exception as e:
        logger.error(f"Error updating job card {job_card_id}: {e}")
        return None


def add_job_card_item(
    job_card_id: int,
    description: str,
    quantity: int = 1,
    unit_price_cents: int = 0,
    item_type: str = "PART",
    inventory_item_id: Optional[int] = None,
) -> Optional[JobCardItem]:
    """Add a line item to a job card. Calculates line_total_cents = quantity * unit_price_cents."""
    try:
        with SessionContext() as session:
            # Verify the job card exists
            stmt = select(JobCard).where(JobCard.id == job_card_id)
            result = session.execute(stmt)
            job_card = result.scalars().first()

            if not job_card:
                logger.warning(f"Job card {job_card_id} not found for adding item")
                return None

            line_total_cents = quantity * unit_price_cents

            item = JobCardItem(
                job_card_id=job_card_id,
                description=description,
                quantity=quantity,
                unit_price_cents=unit_price_cents,
                line_total_cents=line_total_cents,
                item_type=item_type,
                inventory_item_id=inventory_item_id,
            )
            session.add(item)
            session.flush()

            logger.info(
                f"Added item '{description}' to job card {job_card.job_number}"
            )
            return item
    except Exception as e:
        logger.error(f"Error adding item to job card {job_card_id}: {e}")
        return None


def remove_job_card_item(item_id: int) -> bool:
    """Remove a job card item by its id. Returns True on success."""
    try:
        with SessionContext() as session:
            stmt = select(JobCardItem).where(JobCardItem.id == item_id)
            result = session.execute(stmt)
            item = result.scalars().first()

            if not item:
                logger.warning(f"Job card item {item_id} not found for removal")
                return False

            session.delete(item)
            logger.info(f"Removed job card item {item_id}")
            return True
    except Exception as e:
        logger.error(f"Error removing job card item {item_id}: {e}")
        return False


def update_job_card_status(
    job_card_id: int,
    status: str,
    mileage_out: Optional[int] = None,
) -> Optional[JobCard]:
    """Update the status of a job card. If status is COMPLETED, set completed_at."""
    try:
        with SessionContext() as session:
            stmt = select(JobCard).where(JobCard.id == job_card_id)
            result = session.execute(stmt)
            job_card = result.scalars().first()

            if not job_card:
                logger.warning(f"Job card {job_card_id} not found for status update")
                return None

            job_card.status = status

            if status == "COMPLETED":
                job_card.completed_at = datetime.utcnow()

            if mileage_out is not None:
                job_card.mileage_out = mileage_out

            job_card.updated_at = datetime.utcnow()
            session.flush()

            session.refresh(job_card)
            _ = job_card.vehicle
            _ = job_card.customer_obj
            _ = job_card.items

            logger.info(
                f"Updated job card {job_card.job_number} status to {status}"
            )
            return job_card
    except Exception as e:
        logger.error(f"Error updating job card {job_card_id} status: {e}")
        return None


def delete_job_card(job_card_id: int) -> bool:
    """Delete a job card by its id.

    A job card that has an associated invoice cannot be deleted — the invoice
    must be cancelled first.  Returns True on success, False otherwise.
    """
    try:
        with SessionContext() as session:
            stmt = (
                select(JobCard)
                .options(selectinload(JobCard.invoice))
                .where(JobCard.id == job_card_id)
            )
            result = session.execute(stmt)
            job_card = result.scalars().first()

            if not job_card:
                logger.warning(f"Job card {job_card_id} not found for deletion")
                return False

            # Prevent deletion if an invoice exists for this job card
            if job_card.invoice is not None:
                logger.warning(
                    f"Cannot delete job card {job_card_id}: "
                    f"invoice {job_card.invoice.invoice_number} exists"
                )
                return False

            session.delete(job_card)
            logger.info(f"Deleted job card {job_card_id}")
            return True
    except Exception as e:
        logger.error(f"Error deleting job card {job_card_id}: {e}")
        return False
