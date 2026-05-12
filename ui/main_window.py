"""
Main application window for the Vehicle Service Center POS.

Contains the sidebar navigation and a QStackedWidget that hosts all screen pages.
"""

import logging

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QSizePolicy, QMessageBox, QSpacerItem,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from ui.theme import (
    COLOR_APP_BG, COLOR_PANEL_BG, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_BORDER, COLOR_ACCENT,
    COLOR_SIDEBAR_BG, COLOR_SIDEBAR_ACTIVE, COLOR_SIDEBAR_HOVER,
    COLOR_SIDEBAR_TEXT, COLOR_SIDEBAR_ACTIVE_TEXT,
    FONT_FAMILY, FONT_BODY, FONT_SMALL, FONT_BUTTON,
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG,
    SIDEBAR_WIDTH, SIDEBAR_ICON_SIZE,
    DEFAULT_WINDOW_W, DEFAULT_WINDOW_H,
    MIN_WINDOW_W, MIN_WINDOW_H,
    BUTTON_HEIGHT, INPUT_HEIGHT,
)
from controllers.auth_controller import AuthController

logger = logging.getLogger(__name__)

# ── Navigation definition (order matters) ────────────────────────────
# (label, icon_unicode, module_path, class_name)
_NAV_ITEMS = [
    ("Dashboard",  "\u2302", "ui.dashboard",   "DashboardScreen"),
    ("Customers",  "\u263A", "ui.customers",   "CustomersScreen"),
    ("Vehicles",   "\u26FD", "ui.vehicles",     "VehiclesScreen"),
    ("Job Cards",  "\u2630", "ui.job_cards",    "JobCardsScreen"),
    ("Billing",    "\u26A1", "ui.billing",      "BillingScreen"),
    ("Inventory",  "\u2637", "ui.inventory",    "InventoryScreen"),
    ("Reports",    "\u2635", "ui.reports",      "ReportsScreen"),
    ("Staff",      "\u2699", "ui.staff",        "StaffScreen"),
    ("Settings",   "\u2699", "ui.settings",     "SettingsScreen"),
    ("Logout",     "\u23FB", None,              None),  # special handler
]


class _PlaceholderScreen(QWidget):
    """Minimal placeholder shown when a real screen module is not yet available."""

    def __init__(self, title: str, session, stacked_widget, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        lbl = QLabel(f"{title} — screen not yet implemented")
        lbl.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_SECONDARY};"
        )
        layout.addWidget(lbl)
        layout.addStretch()


def _import_screen(module_path: str, class_name: str):
    """Dynamically import a screen class; return None on failure."""
    try:
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, class_name)
    except Exception as exc:
        logger.debug("Could not import %s.%s: %s", module_path, class_name, exc)
        return None


# ─── Sidebar Navigation Button ───────────────────────────────────────

class _NavButton(QPushButton):
    """A single sidebar navigation button with active-state styling."""

    def __init__(self, label: str, icon_char: str, index: int, parent=None):
        super().__init__(parent)
        self._index = index
        self._active = False

        self.setText(f"  {icon_char}   {label}")
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setObjectName("navBtn")

        # Base style (inactive)
        self._apply_style()

    @property
    def index(self) -> int:
        return self._index

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool):
        self._active = value
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self.setStyleSheet(
                f"""
                QPushButton#navBtn {{
                    background-color: {COLOR_SIDEBAR_ACTIVE};
                    color: {COLOR_SIDEBAR_ACTIVE_TEXT};
                    border: none;
                    border-left: 3px solid {COLOR_ACCENT};
                    border-radius: 0;
                    text-align: left;
                    padding: 0 12px 0 17px;
                    font-size: {FONT_BODY}px;
                    font-weight: bold;
                }}
                """
            )
        else:
            self.setStyleSheet(
                f"""
                QPushButton#navBtn {{
                    background-color: {COLOR_SIDEBAR_BG};
                    color: {COLOR_SIDEBAR_TEXT};
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0;
                    text-align: left;
                    padding: 0 12px 0 17px;
                    font-size: {FONT_BODY}px;
                    font-weight: normal;
                }}
                QPushButton#navBtn:hover {{
                    background-color: {COLOR_SIDEBAR_HOVER};
                }}
                """
            )


# ─── Main Window ─────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """Application shell: sidebar navigation + stacked content area."""

    def __init__(self, session):
        super().__init__()
        self.session = session
        self._nav_buttons: list[_NavButton] = []
        self.screens: dict[str, QWidget] = {}

        self._setup_window()
        self._build_ui()
        self._switch_page(0)          # start on Dashboard

    # ── Window Setup ─────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle("Vehicle Service POS")
        self.resize(DEFAULT_WINDOW_W, DEFAULT_WINDOW_H)
        self.setMinimumSize(MIN_WINDOW_W, MIN_WINDOW_H)

    # ── UI Construction ──────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────
        sidebar = self._build_sidebar()
        root.addWidget(sidebar)

        # ── Stacked Content ──────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(
            f"QStackedWidget {{ background-color: {COLOR_APP_BG}; }}"
        )
        self._create_screens()
        root.addWidget(self.stack, 1)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(
            f"""
            QFrame#sidebar {{
                background-color: {COLOR_SIDEBAR_BG};
                border-right: 1px solid {COLOR_BORDER};
            }}
            """
        )

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App brand at top
        brand = QLabel("  Vehicle Service POS")
        brand.setFixedHeight(56)
        brand.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        brand.setStyleSheet(
            f"""
            QLabel {{
                font-size: 15px;
                font-weight: bold;
                color: {COLOR_ACCENT};
                padding-left: 16px;
                background: transparent;
                border: none;
                border-bottom: 1px solid {COLOR_BORDER};
            }}
            """
        )
        layout.addWidget(brand)

        layout.addSpacing(SPACING_SM)

        # Navigation buttons
        for idx, (label, icon_char, module_path, class_name) in enumerate(_NAV_ITEMS):
            btn = _NavButton(label, icon_char, idx)
            if module_path is None:
                # Logout — special handler
                btn.clicked.connect(self._handle_logout)
            else:
                btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        # Spacer pushes user info to the bottom
        layout.addStretch(1)

        # Separator line
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(
            f"background-color: {COLOR_BORDER}; border: none;"
        )
        layout.addWidget(sep)

        # Current user info
        self._user_label = QLabel("  Not logged in")
        self._user_label.setFixedHeight(48)
        self._user_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        self._user_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: {FONT_SMALL}px;
                color: {COLOR_TEXT_SECONDARY};
                padding-left: 16px;
                background: transparent;
                border: none;
            }}
            """
        )
        layout.addWidget(self._user_label)

        # Populate user label from AuthController
        self._refresh_user_label()

        return sidebar

    # ── Screen Creation ──────────────────────────────────────────────

    def _create_screens(self):
        """Instantiate each screen and add it to the stacked widget."""
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
            screen_cls = _import_screen(module_path, class_name)
            if screen_cls is not None:
                try:
                    screen = screen_cls(self.session, self.stack)
                except TypeError:
                    # Fallback: screen may not accept stacked_widget yet
                    try:
                        screen = screen_cls(self.session)
                    except Exception:
                        screen = _PlaceholderScreen(key, self.session, self.stack)
            else:
                screen = _PlaceholderScreen(key, self.session, self.stack)

            self.screens[key] = screen
            self.stack.addWidget(screen)

    # ── Navigation ───────────────────────────────────────────────────

    def _switch_page(self, index: int):
        """Update the sidebar active state and switch the stacked widget."""
        # Update active button styling
        for btn in self._nav_buttons:
            btn.active = (btn.index == index)

        # Map nav index → stack index (logout has no page, so adjust)
        # Nav items 0..8 → stack pages 0..8, nav item 9 is logout (no page)
        stack_index = min(index, self.stack.count() - 1)
        self.stack.setCurrentIndex(stack_index)

    # ── Logout ───────────────────────────────────────────────────────

    def _handle_logout(self):
        """Confirm logout, then clear session and restart to login screen."""
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to log out?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        logger.info("User logged out from MainWindow.")

        # Clear the AuthController session
        AuthController().logout()

        # Close this window — the application loop in main.py
        # should detect the closure and return to the login screen.
        self.close()

    # ── Helpers ──────────────────────────────────────────────────────

    def _refresh_user_label(self):
        """Update the sidebar user label from the current AuthController state."""
        user = AuthController().get_current_user()
        if user is not None:
            self._user_label.setText(
                f"  {user.full_name}\n  {user.role_display}"
            )
        else:
            self._user_label.setText("  Not logged in")

    def set_current_user(self, user):
        """Public helper so the caller (main.py) can push user info after login."""
        AuthController().set_current_user(user)
        self._refresh_user_label()
