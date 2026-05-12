"""Vehicle management service."""

import logging
from typing import Optional, List

from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload, contains_eager

from database import SessionContext
from models.vehicle import Vehicle
from models.customer import Customer

logger = logging.getLogger(__name__)


def get_all_vehicles(search: Optional[str] = None) -> List[Vehicle]:
    """
    Return all vehicles with their customer eagerly loaded.

    Optionally filter by a search term matching registration_no, make,
    model, or customer name (case-insensitive, LIKE).
    """
    try:
        with SessionContext() as session:
            stmt = (
                select(Vehicle)
                .options(joinedload(Vehicle.customer))
                .order_by(Vehicle.registration_no)
            )

            if search:
                pattern = f"%{search}%"
                stmt = (
                    select(Vehicle)
                    .join(Vehicle.customer)  # explicit join to avoid cartesian product
                    .options(contains_eager(Vehicle.customer))
                    .where(
                        or_(
                            Vehicle.registration_no.ilike(pattern),
                            Vehicle.make.ilike(pattern),
                            Vehicle.model.ilike(pattern),
                            Customer.name.ilike(pattern),
                        )
                    )
                    .order_by(Vehicle.registration_no)
                )

            # Use unique() to avoid duplicates from joinedload
            vehicles = list(session.execute(stmt).unique().scalars().all())
            for v in vehicles:
                session.expunge(v)
            return vehicles

    except Exception:
        logger.exception("Error fetching vehicles (search='%s').", search)
        return []


def get_vehicle_by_id(vehicle_id: int) -> Optional[Vehicle]:
    """Return a Vehicle by primary key with customer eagerly loaded, or None."""
    try:
        with SessionContext() as session:
            stmt = (
                select(Vehicle)
                .options(joinedload(Vehicle.customer))
                .where(Vehicle.id == vehicle_id)
            )
            vehicle = session.execute(stmt).unique().scalar_one_or_none()
            if vehicle is not None:
                session.expunge(vehicle)
            return vehicle

    except Exception:
        logger.exception("Error fetching vehicle id %d.", vehicle_id)
        return None


def get_vehicles_by_customer(customer_id: int) -> List[Vehicle]:
    """Return all vehicles belonging to the given customer."""
    try:
        with SessionContext() as session:
            stmt = (
                select(Vehicle)
                .options(joinedload(Vehicle.customer))
                .where(Vehicle.customer_id == customer_id)
                .order_by(Vehicle.registration_no)
            )
            vehicles = list(session.execute(stmt).unique().scalars().all())
            for v in vehicles:
                session.expunge(v)
            return vehicles

    except Exception:
        logger.exception("Error fetching vehicles for customer id %d.", customer_id)
        return []


def create_vehicle(
    customer_id: int,
    registration_no: str,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    color: Optional[str] = None,
    engine_no: Optional[str] = None,
    chassis_no: Optional[str] = None,
    mileage: Optional[int] = None,
    notes: Optional[str] = None,
) -> Optional[Vehicle]:
    """
    Create a new vehicle record.

    Returns the created Vehicle object, or None on error (e.g. duplicate registration).
    """
    try:
        with SessionContext() as session:
            # Validate customer exists
            customer = session.get(Customer, customer_id)
            if customer is None:
                logger.warning("Cannot create vehicle: customer id %d not found.", customer_id)
                return None

            vehicle = Vehicle(
                customer_id=customer_id,
                registration_no=registration_no.upper().strip(),
                make=make,
                model=model,
                year=year,
                color=color,
                engine_no=engine_no,
                chassis_no=chassis_no,
                mileage=mileage,
                notes=notes,
            )
            session.add(vehicle)
            session.flush()
            session.expunge(vehicle)
            return vehicle

    except Exception:
        logger.exception("Error creating vehicle '%s'.", registration_no)
        return None


def update_vehicle(vehicle_id: int, **kwargs) -> Optional[Vehicle]:
    """
    Update the given vehicle's fields.

    Accepted keyword args correspond to Vehicle columns:
        customer_id, registration_no, make, model, year, color,
        engine_no, chassis_no, mileage, notes

    Returns the updated Vehicle, or None on error.
    """
    try:
        with SessionContext() as session:
            vehicle = session.get(Vehicle, vehicle_id)
            if vehicle is None:
                logger.warning("Cannot update: vehicle id %d not found.", vehicle_id)
                return None

            allowed_fields = {
                "customer_id", "registration_no", "make", "model", "year",
                "color", "engine_no", "chassis_no", "mileage", "notes",
            }
            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(vehicle, key, value)
                else:
                    logger.warning("Ignoring unknown field '%s' in vehicle update.", key)

            # Auto-normalise registration number
            if "registration_no" in kwargs and vehicle.registration_no:
                vehicle.registration_no = vehicle.registration_no.upper().strip()

            session.flush()
            session.expunge(vehicle)
            return vehicle

    except Exception:
        logger.exception("Error updating vehicle id %d.", vehicle_id)
        return None


def delete_vehicle(vehicle_id: int) -> bool:
    """
    Delete a vehicle record (hard delete, since the model has no is_active flag).

    Returns True on success, False on error or not found.
    """
    try:
        with SessionContext() as session:
            vehicle = session.get(Vehicle, vehicle_id)
            if vehicle is None:
                logger.warning("Cannot delete: vehicle id %d not found.", vehicle_id)
                return False

            session.delete(vehicle)
            return True

    except Exception:
        logger.exception("Error deleting vehicle id %d.", vehicle_id)
        return False


def get_vehicle_by_registration(reg_no: str) -> Optional[Vehicle]:
    """Return a Vehicle by registration number (case-insensitive), or None."""
    try:
        with SessionContext() as session:
            stmt = (
                select(Vehicle)
                .options(joinedload(Vehicle.customer))
                .where(Vehicle.registration_no == reg_no.upper().strip())
            )
            vehicle = session.execute(stmt).unique().scalar_one_or_none()
            if vehicle is not None:
                session.expunge(vehicle)
            return vehicle

    except Exception:
        logger.exception("Error fetching vehicle by registration '%s'.", reg_no)
        return None
