"""
Application configuration for Vehicle Service Center POS.
"""

import os
import sys

# ─── Application Info ──────────────────────────────────────────
APP_NAME = "Vehicle Service POS"
APP_VERSION = "1.0.0"

# ─── Path Helpers ──────────────────────────────────────────────
def get_base_path():
    """Return the base path of the application (works in dev and PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()
DATA_DIR = os.path.join(BASE_PATH, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ─── Database ──────────────────────────────────────────────────
DB_PATH = os.path.join(DATA_DIR, "vehicle_pos.db")
DB_URL = f"sqlite:///{DB_PATH}"

# ─── Default Admin ─────────────────────────────────────────────
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

# ─── Invoice Settings ─────────────────────────────────────────
INVOICE_PREFIX = "INV"
JOB_CARD_PREFIX = "JC"

# ─── Money (integer cents: 1 LKR = 100 cents) ────────────────
CURRENCY_CODE = "LKR"
CURRENCY_SYMBOL = "Rs."
CENTS_PER_UNIT = 100

def cents_to_display(cents: int) -> str:
    """Convert integer cents to display string like 'Rs. 1,250.00'."""
    amount = cents / CENTS_PER_UNIT
    return f"{CURRENCY_SYMBOL} {amount:,.2f}"

def display_to_cents(display: str) -> int:
    """Convert display string like '1250.00' to integer cents."""
    cleaned = display.replace(CURRENCY_SYMBOL, "").replace(",", "").strip()
    try:
        return int(round(float(cleaned) * CENTS_PER_UNIT))
    except ValueError:
        return 0

# ─── Receipt Dimensions ────────────────────────────────────────
RECEIPT_CHARS_80MM = 48
RECEIPT_CHARS_58MM = 32

# ─── Printer Settings ─────────────────────────────────────────
PRINTER_SETTINGS = {
    "a4_printer_name": "",
    "thermal_printer_name": "",
    "thermal_paper_width": 80,       # mm: 58 or 80
    "thermal_chars_per_line": RECEIPT_CHARS_80MM,
    "thermal_auto_cut": True,
    "thermal_cash_drawer": False,
}

# ─── Session ───────────────────────────────────────────────────
SESSION_TIMEOUT_MINUTES = 30
