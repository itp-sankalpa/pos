"""Models package — import all models so they register on Base.metadata."""

from models.base import Base
from models.user import User
from models.customer import Customer
from models.vehicle import Vehicle
from models.job_card import JobCard, JobCardItem
from models.invoice import Invoice, InvoiceItem
from models.payment import Payment
from models.inventory import InventoryItem, StockTransaction

__all__ = [
    "Base",
    "User",
    "Customer",
    "Vehicle",
    "JobCard",
    "JobCardItem",
    "Invoice",
    "InvoiceItem",
    "Payment",
    "InventoryItem",
    "StockTransaction",
]
