"""Vehicle model."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    registration_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    make: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    engine_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    chassis_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mileage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="vehicles")
    job_cards: Mapped[list["JobCard"]] = relationship(back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle(id={self.id}, reg='{self.registration_no}')>"

    @property
    def display_name(self):
        parts = [self.registration_no]
        if self.make:
            parts.append(self.make)
        if self.model:
            parts.append(self.model)
        return " - ".join(parts)
