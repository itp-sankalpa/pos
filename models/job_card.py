"""Job Card and Job Card Item models."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, Integer, Text, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class JobCard(Base):
    __tablename__ = "job_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    assigned_mechanic: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    complaint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mileage_in: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mileage_out: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    labor_charge_cents: Mapped[int] = mapped_column(Integer, default=0)  # stored as cents
    discount_cents: Mapped[int] = mapped_column(Integer, default=0)
    stock_deducted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship(back_populates="job_cards")
    customer_obj: Mapped["Customer"] = relationship()
    assigned_mechanic_obj: Mapped[Optional["User"]] = relationship(back_populates="job_cards", foreign_keys=[assigned_mechanic])
    items: Mapped[List["JobCardItem"]] = relationship(back_populates="job_card", cascade="all, delete-orphan")
    invoice: Mapped[Optional["Invoice"]] = relationship(back_populates="job_card", uselist=False)

    def __repr__(self):
        return f"<JobCard(id={self.id}, job_number='{self.job_number}', status='{self.status}')>"

    @property
    def total_items_cents(self) -> int:
        return sum(item.line_total_cents for item in self.items)

    @property
    def total_cents(self) -> int:
        return self.total_items_cents + self.labor_charge_cents - self.discount_cents


class JobCardItem(Base):
    __tablename__ = "job_card_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_card_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_cards.id"), nullable=False, index=True)
    inventory_item_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("inventory_items.id"), nullable=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price_cents: Mapped[int] = mapped_column(Integer, default=0)  # stored as cents
    line_total_cents: Mapped[int] = mapped_column(Integer, default=0)
    item_type: Mapped[str] = mapped_column(String(20), default="PART")  # PART, SERVICE, LABOR

    # Relationships
    job_card: Mapped["JobCard"] = relationship(back_populates="items")
    inventory_item: Mapped[Optional["InventoryItem"]] = relationship()

    def __repr__(self):
        return f"<JobCardItem(id={self.id}, desc='{self.description}', qty={self.quantity})>"
