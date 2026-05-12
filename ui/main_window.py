"""
Main application window for the Vehicle Service Center POS (Tkinter version).

Contains the sidebar navigation and a frame container that hosts all screen pages.
"""

import logging

import tkinter as tk
from tkinter import ttk, messagebox

from ui.theme import *
from controllers.auth_controller import AuthController

logger = logging.getLogger(__name__)

# ── Navigation definition (order matters) ────────────────────────────
# (label, icon_char, module_path, class_name)
_NAV_ITEMS = [
    ("Dashboard",  "⌂", "ui.dashboard",   "DashboardScreen"),
    ("Customers",  "☺", "ui.customers",   "CustomersScreen"),
    ("Vehicles",   "⛽", "ui.vehicles",     "VehiclesScreen"),
    ("Job Cards",  "☰", "ui.job_cards",    "JobCardsScreen"),
    ("Billing",    "⚡", "ui.billing",      "BillingScreen"),
    ("Inventory",  "⛭", "ui.inventory",    "InventoryScreen"),
    ("Reports",    "⚶", "ui.reports",      "ReportsScreen"),
    ("Staff",      "⚙", "ui.staff",        "StaffScreen"),
    ("Settings",   "⚙", "ui.settings",     "SettingsScreen"),
    ("Logout",     "⏻", None,              None),  # special handler
]


class MainWindow(tk.Tk):
    """Application shell: sidebar navigation + stacked content area."""

    def __init__(self, session):
        super().__init__()
        self.session = session
        self._nav_buttons: list[tuple[int, tk.Button]] = []
        self._active_index: int = -1
        self.screens: dict[str, tk.Frame] = {}

        self._setup_window()
        self._build_ui()
        self._switch_page(0)  # start on Dashboard

    # ── Window Setup ─────────────────────────────────────────────────

    def _setup_window(self):
        self.title("Vehicle Service POS")
        self.geometry(f"{DEFAULT_WINDOW_W}x{DEFAULT_WINDOW_H}")
        self.minsize(MIN_WINDOW_W, MIN_WINDOW_H)
        self.configure(bg=COLOR_APP_BG)

    # ── UI Construction ──────────────────────────────────────────────

    def _build_ui(self):
        # Main container: sidebar | content
        self._main_frame = tk.Frame(self, bg=COLOR_APP_BG)
        self._main_frame.pack(fill="both", expand=True)

        # Sidebar
        self._build_sidebar()

        # Content container
        self._content_frame = tk.Frame(self._main_frame, bg=COLOR_APP_BG)
        self._content_frame.pack(side="left", fill="both", expand=True, padx=(0, 0))

        self._create_screens()

    def _build_sidebar(self):
        sidebar = tk.Frame(self._main_frame, bg=COLOR_SIDEBAR_BG, width=SIDEBAR_WIDTH)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # App brand at top
        brand = tk.Label(
            sidebar, text="  Vehicle Service POS",
            font=(FONT_FAMILY, 15, "bold"),
            fg=COLOR_ACCENT, bg=COLOR_SIDEBAR_BG,
            anchor="w", pady=16, padx=16,
        )
        brand.pack(fill="x")

        # Separator
        sep = tk.Frame(sidebar, bg=COLOR_BORDER, height=1)
        sep.pack(fill="x")

        # Navigation buttons
        for idx, (label, icon_char, module_path, class_name) in enumerate(_NAV_ITEMS):
            btn = tk.Button(
                sidebar,
                text=f"  {icon_char}   {label}",
                font=(FONT_FAMILY, FONT_BODY),
                fg=COLOR_SIDEBAR_TEXT,
                bg=COLOR_SIDEBAR_BG,
                activeforeground=COLOR_SIDEBAR_TEXT,
                activebackground=COLOR_SIDEBAR_HOVER,
                bd=0, relief="flat",
                anchor="w",
                padx=17, pady=10,
                cursor="hand2",
            )
            btn.pack(fill="x")

            if module_path is None:
                btn.config(command=self._handle_logout)
            else:
                btn.config(command=lambda i=idx: self._switch_page(i))

            self._nav_buttons.append((idx, btn))

        # Spacer
        spacer = tk.Frame(sidebar, bg=COLOR_SIDEBAR_BG)
        spacer.pack(fill="both", expand=True)

        # Bottom separator
        sep2 = tk.Frame(sidebar, bg=COLOR_BORDER, height=1)
        sep2.pack(fill="x")

        # Current user info
        self._user_label = tk.Label(
            sidebar, text="  Not logged in",
            font=(FONT_FAMILY, FONT_SMALL),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_SIDEBAR_BG,
            anchor="w", padx=16, pady=12,
        )
        self._user_label.pack(fill="x")

        self._refresh_user_label()

    # ── Screen Creation ──────────────────────────────────────────────

    def _create_screens(self):
        """Instantiate each screen and add it to the content frame."""
        screen_specs = [
            ("Dashboard",  "ui.dashboard",  "DashboardScreen"),
            ("Customers",  "ui.customers",  "CustomersScreen"),
            ("Vehicles",   "ui.vehicles",   "VehiclesScreen"),
            ("Job Cards",  "ui.job_cards",  "JobCardsScreen"),
            ("Billing",    "ui.billing",    "BillingScreen"),
            ("Inventory",  "ui.inventory",  "InventoryScreen"),
            ("Reports",    "ui.reports",    "ReportsScreen"),
            ("Staff",      "ui.staff",      "StaffScreen"),
            ("Settings",   "ui.settings",   "SettingsScreen"),
        ]

        for key, module_path, class_name in screen_specs:
            screen_cls = self._import_screen(module_path, class_name)
            if screen_cls is not None:
                try:
                    screen = screen_cls(self.session, self._content_frame, parent=self._content_frame)
                except TypeError:
                    try:
                        screen = screen_cls(self.session, parent=self._content_frame)
                    except Exception as exc:
                        logger.debug("Could not create %s: %s", key, exc)
                        screen = self._make_placeholder(key)
            else:
                screen = self._make_placeholder(key)

            self.screens[key] = screen

        # Show the first screen
        self._show_screen("Dashboard")

    def _make_placeholder(self, title: str) -> tk.Frame:
        """Create a placeholder frame for unimplemented screens."""
        frame = tk.Frame(self._content_frame, bg=COLOR_APP_BG)
        lbl = tk.Label(
            frame, text=f"{title} — screen not yet implemented",
            font=(FONT_FAMILY, FONT_BODY), fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_APP_BG,
        )
        lbl.pack(pady=SPACING_LG)
        return frame

    @staticmethod
    def _import_screen(module_path: str, class_name: str):
        """Dynamically import a screen class; return None on failure."""
        try:
            import importlib
            mod = importlib.import_module(module_path)
            return getattr(mod, class_name)
        except Exception as exc:
            logger.debug("Could not import %s.%s: %s", module_path, class_name, exc)
            return None

    # ── Navigation ───────────────────────────────────────────────────

    def _switch_page(self, index: int):
        """Update the sidebar active state and switch the visible screen."""
        # Update active button styling
        self._active_index = index
        for idx, btn in self._nav_buttons:
            if idx == index:
                btn.config(
                    bg=COLOR_SIDEBAR_ACTIVE,
                    fg=COLOR_SIDEBAR_ACTIVE_TEXT,
                    font=(FONT_FAMILY, FONT_BODY, "bold"),
                )
            else:
                btn.config(
                    bg=COLOR_SIDEBAR_BG,
                    fg=COLOR_SIDEBAR_TEXT,
                    font=(FONT_FAMILY, FONT_BODY),
                )

        # Map nav index to screen key
        nav_keys = [item[0] for item in _NAV_ITEMS if item[2] is not None]
        if index < len(nav_keys):
            self._show_screen(nav_keys[index])

    def _show_screen(self, key: str):
        """Hide all screens, then show the one matching *key*."""
        for skey, screen in self.screens.items():
            screen.pack_forget()

        if key in self.screens:
            screen = self.screens[key]
            screen.pack(fill="both", expand=True, padx=SPACING_LG, pady=SPACING_LG)
            # Call refresh if available
            if hasattr(screen, 'refresh'):
                try:
                    screen.refresh()
                except Exception:
                    pass

    # ── Logout ───────────────────────────────────────────────────────

    def _handle_logout(self):
        """Confirm logout, then clear session and close window."""
        reply = messagebox.askyesno(
            "Confirm Logout",
            "Are you sure you want to log out?",
            default="no",
        )
        if not reply:
            return

        logger.info("User logged out from MainWindow.")
        AuthController().logout()
        self.destroy()

    # ── Helpers ──────────────────────────────────────────────────────

    def _refresh_user_label(self):
        """Update the sidebar user label from the current AuthController state."""
        user = AuthController().get_current_user()
        if user is not None:
            self._user_label.config(text=f"  {user.full_name}\n  {user.role_display}")
        else:
            self._user_label.config(text="  Not logged in")

    def set_current_user(self, user):
        """Public helper so the caller (main.py) can push user info after login."""
        AuthController().set_current_user(user)
        self._refresh_user_label()
