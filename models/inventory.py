"""Inventory Item and Stock Transaction models."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, Integer, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), default="PCS")  # PCS, LTR, KG, SET
    cost_price_cents: Mapped[int] = mapped_column(Integer, default=0)
    sell_price_cents: Mapped[int] = mapped_column(Integer, default=0)
    quantity_in_stock: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=5)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions: Mapped[List["StockTransaction"]] = relationship(back_populates="item", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<InventoryItem(id={self.id}, code='{self.item_code}', name='{self.name}')>"

    @property
    def is_low_stock(self) -> bool:
        return self.quantity_in_stock <= self.reorder_level


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("inventory_items.id"), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # IN, OUT, ADJUSTMENT
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # job card number, PO number, etc.
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    item: Mapped["InventoryItem"] = relationship(back_populates="transactions")

    def __repr__(self):
        return f"<StockTransaction(id={self.id}, type='{self.transaction_type}', qty={self.quantity})>"
