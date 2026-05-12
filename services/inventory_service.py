"""Inventory and stock management service."""

import logging
from typing import Optional, List

from sqlalchemy import select, func, distinct, or_

from database import SessionContext
from models.inventory import InventoryItem, StockTransaction
from models.job_card import JobCard, JobCardItem

logger = logging.getLogger(__name__)


def get_all_items(
    search: Optional[str] = None,
    category: Optional[str] = None,
) -> List[InventoryItem]:
    """
    Return all active inventory items.

    Optional filters:
        search  – matches item_code, name, or brand (case-insensitive, LIKE)
        category – exact match on category
    """
    try:
        with SessionContext() as session:
            stmt = select(InventoryItem).where(
                InventoryItem.is_active == True  # noqa: E712
            )

            if search:
                pattern = f"%{search}%"
                stmt = stmt.where(
                    or_(
                        InventoryItem.item_code.ilike(pattern),
                        InventoryItem.name.ilike(pattern),
                        InventoryItem.brand.ilike(pattern),
                    )
                )

            if category:
                stmt = stmt.where(InventoryItem.category == category)

            stmt = stmt.order_by(InventoryItem.name)
            items = list(session.execute(stmt).scalars().all())
            for item in items:
                session.expunge(item)
            return items

    except Exception:
        logger.exception("Error fetching inventory items (search='%s', category='%s').", search, category)
        return []


def get_item_by_id(item_id: int) -> Optional[InventoryItem]:
    """Return an InventoryItem by primary key, or None if not found."""
    try:
        with SessionContext() as session:
            item = session.get(InventoryItem, item_id)
            if item is not None:
                session.expunge(item)
            return item

    except Exception:
        logger.exception("Error fetching inventory item id %d.", item_id)
        return None


def get_item_by_code(code: str) -> Optional[InventoryItem]:
    """Return an InventoryItem by item_code, or None if not found."""
    try:
        with SessionContext() as session:
            stmt = select(InventoryItem).where(
                InventoryItem.item_code == code.strip()
            )
            item = session.execute(stmt).scalar_one_or_none()
            if item is not None:
                session.expunge(item)
            return item

    except Exception:
        logger.exception("Error fetching inventory item by code '%s'.", code)
        return None


def create_item(
    item_code: str,
    name: str,
    description: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    unit: str = "PCS",
    cost_price_cents: int = 0,
    sell_price_cents: int = 0,
    quantity_in_stock: int = 0,
    reorder_level: int = 5,
) -> Optional[InventoryItem]:
    """
    Create a new inventory item.

    Returns the created InventoryItem object, or None on error (e.g. duplicate item_code).
    """
    try:
        with SessionContext() as session:
            # Check for duplicate item_code
            existing = session.execute(
                select(InventoryItem).where(InventoryItem.item_code == item_code.strip())
            ).scalar_one_or_none()
            if existing is not None:
                logger.warning("Cannot create item: item_code '%s' already exists.", item_code)
                return None

            item = InventoryItem(
                item_code=item_code.strip(),
                name=name,
                description=description,
                category=category,
                brand=brand,
                unit=unit,
                cost_price_cents=cost_price_cents,
                sell_price_cents=sell_price_cents,
                quantity_in_stock=quantity_in_stock,
                reorder_level=reorder_level,
            )
            session.add(item)
            session.flush()
            session.expunge(item)
            return item

    except Exception:
        logger.exception("Error creating inventory item '%s'.", item_code)
        return None


def update_item(item_id: int, **kwargs) -> Optional[InventoryItem]:
    """
    Update the given inventory item's fields.

    Accepted keyword args correspond to InventoryItem columns:
        item_code, name, description, category, brand, unit,
        cost_price_cents, sell_price_cents, quantity_in_stock,
        reorder_level, is_active

    Returns the updated InventoryItem, or None on error.
    """
    try:
        with SessionContext() as session:
            item = session.get(InventoryItem, item_id)
            if item is None:
                logger.warning("Cannot update: inventory item id %d not found.", item_id)
                return None

            allowed_fields = {
                "item_code", "name", "description", "category", "brand", "unit",
                "cost_price_cents", "sell_price_cents", "quantity_in_stock",
                "reorder_level", "is_active",
            }
            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(item, key, value)
                else:
                    logger.warning("Ignoring unknown field '%s' in inventory item update.", key)

            session.flush()
            session.expunge(item)
            return item

    except Exception:
        logger.exception("Error updating inventory item id %d.", item_id)
        return None


def delete_item(item_id: int) -> bool:
    """
    Soft-delete an inventory item by setting is_active=False.

    Returns True on success, False on error or not found.
    """
    try:
        with SessionContext() as session:
            item = session.get(InventoryItem, item_id)
            if item is None:
                logger.warning("Cannot delete: inventory item id %d not found.", item_id)
                return False

            item.is_active = False
            return True

    except Exception:
        logger.exception("Error deleting inventory item id %d.", item_id)
        return False


def adjust_stock(
    item_id: int,
    quantity: int,
    transaction_type: str,
    reference: Optional[str] = None,
    notes: Optional[str] = None,
    created_by: Optional[int] = None,
) -> Optional[StockTransaction]:
    """
    Adjust stock for an inventory item and record the transaction.

    transaction_type: "IN", "OUT", or "ADJUSTMENT"
    quantity: positive integer representing the magnitude of the change

    For "IN"  — stock increases by quantity
    For "OUT" — stock decreases by quantity
    For "ADJUSTMENT" — quantity can be positive (increase) or negative (decrease)

    Returns the created StockTransaction, or None on error.
    """
    try:
        with SessionContext() as session:
            item = session.get(InventoryItem, item_id)
            if item is None:
                logger.warning("Cannot adjust stock: item id %d not found.", item_id)
                return None

            transaction_type = transaction_type.upper().strip()

            if transaction_type == "IN":
                item.quantity_in_stock += abs(quantity)
            elif transaction_type == "OUT":
                deduct = abs(quantity)
                if item.quantity_in_stock < deduct:
                    logger.warning(
                        "Insufficient stock for item '%s': have %d, need %d.",
                        item.item_code, item.quantity_in_stock, deduct,
                    )
                    return None
                item.quantity_in_stock -= deduct
            elif transaction_type == "ADJUSTMENT":
                # quantity can be positive or negative for adjustments
                new_qty = item.quantity_in_stock + quantity
                if new_qty < 0:
                    logger.warning(
                        "Adjustment would result in negative stock for item '%s'.", item.item_code,
                    )
                    return None
                item.quantity_in_stock = new_qty
            else:
                logger.error("Unknown transaction_type '%s'.", transaction_type)
                return None

            txn = StockTransaction(
                item_id=item_id,
                transaction_type=transaction_type,
                quantity=quantity,
                unit_cost_cents=item.cost_price_cents,
                reference=reference,
                notes=notes,
                created_by=created_by,
            )
            session.add(txn)
            session.flush()
            session.expunge(txn)
            return txn

    except Exception:
        logger.exception("Error adjusting stock for item id %d.", item_id)
        return None


def deduct_stock_for_job(job_card_id: int) -> bool:
    """
    Two-phase stock deduction for a job card:
      Phase 1: Validate that all PART items have sufficient stock.
      Phase 2: Deduct stock for each PART item and record OUT transactions,
               then set job_card.stock_deducted = True.

    Returns True on success, False on error or insufficient stock.
    """
    try:
        with SessionContext() as session:
            job_card = session.get(JobCard, job_card_id)
            if job_card is None:
                logger.warning("Cannot deduct stock: job card id %d not found.", job_card_id)
                return False

            if job_card.stock_deducted:
                logger.warning("Stock already deducted for job card id %d.", job_card_id)
                return False

            # Load only PART items that reference an inventory item
            stmt = (
                select(JobCardItem)
                .where(
                    JobCardItem.job_card_id == job_card_id,
                    JobCardItem.item_type == "PART",
                    JobCardItem.inventory_item_id.isnot(None),
                )
            )
            part_items = list(session.execute(stmt).scalars().all())

            if not part_items:
                # No PART items to deduct — just mark as deducted
                job_card.stock_deducted = True
                return True

            # Phase 1: Validate stock availability
            for jci in part_items:
                inv_item = session.get(InventoryItem, jci.inventory_item_id)
                if inv_item is None:
                    logger.warning(
                        "Inventory item id %d referenced in job card %d not found.",
                        jci.inventory_item_id, job_card_id,
                    )
                    return False
                if inv_item.quantity_in_stock < jci.quantity:
                    logger.warning(
                        "Insufficient stock for item '%s': have %d, need %d.",
                        inv_item.item_code, inv_item.quantity_in_stock, jci.quantity,
                    )
                    return False

            # Phase 2: Deduct stock and record transactions
            for jci in part_items:
                inv_item = session.get(InventoryItem, jci.inventory_item_id)
                inv_item.quantity_in_stock -= jci.quantity

                txn = StockTransaction(
                    item_id=inv_item.id,
                    transaction_type="OUT",
                    quantity=jci.quantity,
                    unit_cost_cents=inv_item.cost_price_cents,
                    reference=job_card.job_number,
                    notes=f"Auto-deducted for job card {job_card.job_number}",
                    created_by=None,
                )
                session.add(txn)

            job_card.stock_deducted = True
            return True

    except Exception:
        logger.exception("Error deducting stock for job card id %d.", job_card_id)
        return False


def get_low_stock_items() -> List[InventoryItem]:
    """Return all active inventory items where quantity_in_stock <= reorder_level."""
    try:
        with SessionContext() as session:
            stmt = (
                select(InventoryItem)
                .where(
                    InventoryItem.is_active == True,  # noqa: E712
                    InventoryItem.quantity_in_stock <= InventoryItem.reorder_level,
                )
                .order_by(InventoryItem.quantity_in_stock)
            )
            items = list(session.execute(stmt).scalars().all())
            for item in items:
                session.expunge(item)
            return items

    except Exception:
        logger.exception("Error fetching low stock items.")
        return []


def get_categories() -> List[str]:
    """Return a list of distinct category strings from active inventory items."""
    try:
        with SessionContext() as session:
            stmt = (
                select(distinct(InventoryItem.category))
                .where(
                    InventoryItem.is_active == True,  # noqa: E712
                    InventoryItem.category.isnot(None),
                    InventoryItem.category != "",
                )
                .order_by(InventoryItem.category)
            )
            categories = list(session.execute(stmt).scalars().all())
            return categories

    except Exception:
        logger.exception("Error fetching inventory categories.")
        return []
