"""Job Card controller — bridges the UI and job_card_service layer."""

import logging
from typing import Optional, List

from services.job_card_service import (
    get_all_job_cards,
    get_job_card_by_id,
    create_job_card,
    update_job_card,
    add_job_card_item,
    remove_job_card_item,
    update_job_card_status,
)
from models.job_card import JobCard, JobCardItem

logger = logging.getLogger(__name__)


class JobCardController:
    """Delegates job card operations to job_card_service."""

    def __init__(self):
        """No-argument constructor."""
        pass

    # ── Read operations ─────────────────────────────────────────────

    def get_job_cards(
        self, status: Optional[str] = None, search: Optional[str] = None
    ) -> List[JobCard]:
        """Return all job cards, optionally filtered by status and search term.

        Search matches against job_number, vehicle registration_no, or
        customer name.
        """
        return get_all_job_cards(status=status, search=search)

    def get_job_card(self, job_card_id: int) -> Optional[JobCard]:
        """Return a single JobCard by ID with relationships loaded, or None."""
        return get_job_card_by_id(job_card_id)

    # ── Write operations ────────────────────────────────────────────

    def create_job_card(
        self, vehicle_id: int, customer_id: int, **kwargs
    ) -> Optional[JobCard]:
        """Create a new job card with an auto-generated job number.

        Accepted kwargs: complaint, assigned_mechanic, mileage_in,
        labor_charge_cents.
        Returns the created JobCard, or None on error.
        """
        return create_job_card(
            vehicle_id=vehicle_id,
            customer_id=customer_id,
            **kwargs,
        )

    def update_job_card(self, job_card_id: int, **kwargs) -> Optional[JobCard]:
        """Update a job card's fields.

        Accepted kwargs correspond to JobCard columns (except id and
        job_number which are protected).
        Returns the updated JobCard, or None on error.
        """
        return update_job_card(job_card_id, **kwargs)

    # ── Job card items ──────────────────────────────────────────────

    def add_job_card_item(
        self, job_card_id: int, description: str, **kwargs
    ) -> Optional[JobCardItem]:
        """Add a line item to a job card.

        Accepted kwargs: quantity, unit_price_cents, item_type,
        inventory_item_id.
        Returns the created JobCardItem, or None on error.
        """
        return add_job_card_item(
            job_card_id=job_card_id,
            description=description,
            **kwargs,
        )

    def remove_job_card_item(self, item_id: int) -> bool:
        """Remove a job card item by its ID.

        Returns True on success, False on error or not found.
        """
        return remove_job_card_item(item_id)

    # ── Status transitions ──────────────────────────────────────────

    def update_status(
        self, job_card_id: int, status: str, **kwargs
    ) -> Optional[JobCard]:
        """Update the status of a job card.

        Accepted kwargs: mileage_out (set when status is COMPLETED).
        Returns the updated JobCard, or None on error.
        """
        return update_job_card_status(job_card_id, status, **kwargs)
