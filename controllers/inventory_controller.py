"""Inventory controller — bridges the UI and inventory_service layer."""

import logging
from typing import Optional, List

from services.inventory_service import (
    get_all_items,
    get_item_by_id,
    create_item,
    update_item,
    delete_item,
    adjust_stock,
    get_low_stock_items,
    get_categories,
)
from models.inventory import InventoryItem, StockTransaction

logger = logging.getLogger(__name__)


class InventoryController:
    """Delegates inventory operations to inventory_service."""

    def __init__(self):
        """No-argument constructor."""
        pass

    # ── Read operations ─────────────────────────────────────────────

    def get_items(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[InventoryItem]:
        """Return all active inventory items, optionally filtered.

        search  – matches item_code, name, or brand (case-insensitive).
        category – exact match on category.
        """
        return get_all_items(search=search, category=category)

    def get_item(self, item_id: int) -> Optional[InventoryItem]:
        """Return a single InventoryItem by ID, or None if not found."""
        return get_item_by_id(item_id)

    def get_low_stock_items(self) -> List[InventoryItem]:
        """Return items where quantity_in_stock <= reorder_level."""
        return get_low_stock_items()

    def get_categories(self) -> List[str]:
        """Return a list of distinct category strings from active items."""
        return get_categories()

    # ── Write operations ────────────────────────────────────────────

    def create_item(
        self, item_code: str, name: str, **kwargs
    ) -> Optional[InventoryItem]:
        """Create a new inventory item.

        Accepted kwargs: description, category, brand, unit,
        cost_price_cents, sell_price_cents, quantity_in_stock,
        reorder_level.
        Returns the created InventoryItem, or None on error.
        """
        return create_item(item_code=item_code, name=name, **kwargs)

    def update_item(self, item_id: int, **kwargs) -> Optional[InventoryItem]:
        """Update the given inventory item's fields.

        Accepted kwargs: item_code, name, description, category, brand,
        unit, cost_price_cents, sell_price_cents, quantity_in_stock,
        reorder_level, is_active.
        Returns the updated InventoryItem, or None on error.
        """
        return update_item(item_id, **kwargs)

    def delete_item(self, item_id: int) -> bool:
        """Soft-delete an inventory item by setting is_active=False.

        Returns True on success, False on error or not found.
        """
        return delete_item(item_id)

    def adjust_stock(
        self, item_id: int, qty: int, txn_type: str, **kwargs
    ) -> Optional[StockTransaction]:
        """Adjust stock for an inventory item and record the transaction.

        txn_type: "IN", "OUT", or "ADJUSTMENT".
        qty: positive integer (magnitude). For ADJUSTMENT, can be negative.
        Accepted kwargs: reference, notes, created_by.
        Returns the created StockTransaction, or None on error.
        """
        return adjust_stock(
            item_id=item_id,
            quantity=qty,
            transaction_type=txn_type,
            **kwargs,
        )
