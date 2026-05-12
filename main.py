"""
Vehicle Service Center POS — Main Entry Point (Tkinter version)
"""

import sys
import logging

import tkinter as tk
from tkinter import messagebox

from database import init_db, get_session
from services.auth_service import seed_admin
from ui.theme import apply_app_theme
from ui.login import LoginScreen
from ui.main_window import MainWindow
from controllers.auth_controller import AuthController

# ─── Logging Setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    # ── Initialize Database ─────────────────────────────────────
    try:
        init_db()
        logger.info("Database initialized successfully.")
        seed_admin()
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}")
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Database Error",
            f"Could not initialize the database:\n{e}\n\n"
            "Please check that the data directory is writable and try again.",
        )
        sys.exit(1)

    # ── Login Flow ──────────────────────────────────────────────
    session = get_session()
    auth = AuthController()

    def on_login_success(user):
        # Close the login window
        login_screen.destroy()

        auth.set_current_user(user)
        logger.info(f"User logged in: {user.username} (role: {user.role})")

        # Open main window
        main_window = MainWindow(session)
        main_window.set_current_user(user)
        main_window.mainloop()

    login_screen = LoginScreen(on_login_success=on_login_success)
    login_screen.mainloop()


if __name__ == "__main__":
    main()
