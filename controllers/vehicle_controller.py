"""Vehicle controller — bridges the UI and vehicle_service layer."""

import logging
from typing import Optional, List

from services.vehicle_service import (
    get_all_vehicles,
    get_vehicle_by_id,
    get_vehicles_by_customer,
    create_vehicle,
    update_vehicle,
    delete_vehicle,
)
from models.vehicle import Vehicle

logger = logging.getLogger(__name__)


class VehicleController:
    """Delegates vehicle operations to vehicle_service."""

    def __init__(self):
        """No-argument constructor."""
        pass

    # ── Read operations ─────────────────────────────────────────────

    def get_vehicles(self, search: Optional[str] = None) -> List[Vehicle]:
        """Return all vehicles with customer eagerly loaded.

        Optionally filter by search term matching registration_no, make,
        model, or customer name.
        """
        return get_all_vehicles(search=search)

    def get_vehicle(self, vehicle_id: int) -> Optional[Vehicle]:
        """Return a single Vehicle by ID with customer eagerly loaded, or None."""
        return get_vehicle_by_id(vehicle_id)

    def get_vehicles_by_customer(self, customer_id: int) -> List[Vehicle]:
        """Return all vehicles belonging to the given customer."""
        return get_vehicles_by_customer(customer_id)

    # ── Write operations ────────────────────────────────────────────

    def create_vehicle(
        self, customer_id: int, registration_no: str, **kwargs
    ) -> Optional[Vehicle]:
        """Create a new vehicle record.

        Accepted kwargs: make, model, year, color, engine_no, chassis_no,
        mileage, notes.
        Returns the created Vehicle, or None on error.
        """
        return create_vehicle(
            customer_id=customer_id,
            registration_no=registration_no,
            **kwargs,
        )

    def update_vehicle(self, vehicle_id: int, **kwargs) -> Optional[Vehicle]:
        """Update the given vehicle's fields.

        Accepted kwargs: customer_id, registration_no, make, model, year,
        color, engine_no, chassis_no, mileage, notes.
        Returns the updated Vehicle, or None on error.
        """
        return update_vehicle(vehicle_id, **kwargs)

    def delete_vehicle(self, vehicle_id: int) -> bool:
        """Delete a vehicle record (hard delete).

        Returns True on success, False on error or not found.
        """
        return delete_vehicle(vehicle_id)
