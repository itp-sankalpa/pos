"""
Login screen for the Vehicle Service Center POS application.
Displays a centered login card on a grey background.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.theme import (
    COLOR_APP_BG, COLOR_PANEL_BG, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_BORDER, FONT_FAMILY, FONT_PAGE_TITLE, FONT_BODY,
    FONT_BUTTON, FONT_SMALL, SPACING_SM, SPACING_MD,
    SPACING_LG, SPACING_XL, BUTTON_HEIGHT, INPUT_HEIGHT,
)
from controllers.auth_controller import AuthController


class LoginScreen(QWidget):
    """Centered login form with app branding, username/password fields, and login button."""

    # Emitted with the authenticated User object on successful login
    login_successful = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auth = AuthController()
        self._build_ui()

    # ── UI Construction ──────────────────────────────────────────────

    def _build_ui(self):
        # Outer layout fills the entire widget, centres the card
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Grey background
        self.setAutoFillBackground(True)
        self.setStyleSheet(f"background-color: {COLOR_APP_BG};")

        # Vertical spacer above the card
        outer.addStretch(1)

        # ── Card ─────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(400)
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        card.setStyleSheet(
            f"""
            QFrame#loginCard {{
                background-color: {COLOR_PANEL_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 10px;
            }}
            """
        )

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(SPACING_XL, SPACING_XL, SPACING_XL, SPACING_XL)
        card_layout.setSpacing(SPACING_MD)

        # App title
        title = QLabel("Vehicle Service POS")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"font-size: {FONT_PAGE_TITLE}px; "
            f"font-weight: bold; "
            f"color: {COLOR_TEXT_PRIMARY}; "
            f"background: transparent; border: none;"
        )
        card_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Sign in to your account")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            f"font-size: {FONT_SMALL}px; "
            f"color: {COLOR_TEXT_SECONDARY}; "
            f"background: transparent; border: none;"
        )
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(SPACING_LG)

        # Username label
        user_label = QLabel("Username")
        user_label.setStyleSheet(
            f"font-size: {FONT_SMALL}px; "
            f"font-weight: bold; "
            f"color: {COLOR_TEXT_PRIMARY}; "
            f"background: transparent; border: none;"
        )
        card_layout.addWidget(user_label)

        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setFixedHeight(INPUT_HEIGHT)
        self.username_input.setStyleSheet(
            f"""
            QLineEdit {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 5px;
                padding: 6px 12px;
                font-size: {FONT_BODY}px;
                background-color: {COLOR_PANEL_BG};
                color: {COLOR_TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {COLOR_ACCENT};
            }}
            """
        )
        card_layout.addWidget(self.username_input)

        card_layout.addSpacing(SPACING_SM)

        # Password label
        pass_label = QLabel("Password")
        pass_label.setStyleSheet(
            f"font-size: {FONT_SMALL}px; "
            f"font-weight: bold; "
            f"color: {COLOR_TEXT_PRIMARY}; "
            f"background: transparent; border: none;"
        )
        card_layout.addWidget(pass_label)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(INPUT_HEIGHT)
        self.password_input.setStyleSheet(
            f"""
            QLineEdit {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 5px;
                padding: 6px 12px;
                font-size: {FONT_BODY}px;
                background-color: {COLOR_PANEL_BG};
                color: {COLOR_TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {COLOR_ACCENT};
            }}
            """
        )
        card_layout.addWidget(self.password_input)

        card_layout.addSpacing(SPACING_LG)

        # Login button
        self.login_button = QPushButton("Sign In")
        self.login_button.setFixedHeight(BUTTON_HEIGHT + 6)
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: {FONT_BUTTON}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #1449B8;
            }}
            QPushButton:disabled {{
                background-color: #B0BEC5;
                color: #ECEFF1;
            }}
            """
        )
        card_layout.addWidget(self.login_button)

        # ── Signals ──────────────────────────────────────────────
        self.login_button.clicked.connect(self._on_login)
        self.password_input.returnPressed.connect(self._on_login)
        self.username_input.returnPressed.connect(self.password_input.setFocus)

        # Centre the card horizontally in the outer layout
        card_row = QHBoxLayout()
        card_row.addStretch(1)
        card_row.addWidget(card)
        card_row.addStretch(1)
        outer.addLayout(card_row)

        # Vertical spacer below the card
        outer.addStretch(1)

    # ── Handlers ─────────────────────────────────────────────────────

    def _on_login(self):
        """Validate inputs and attempt authentication via AuthController."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username:
            self._show_error("Please enter your username.")
            self.username_input.setFocus()
            return

        if not password:
            self._show_error("Please enter your password.")
            self.password_input.setFocus()
            return

        # Disable button while authenticating
        self.login_button.setEnabled(False)
        self.login_button.setText("Signing in…")

        user = self._auth.login(username, password)

        if user is not None:
            # Success — clear sensitive fields and emit signal
            self.password_input.clear()
            self.username_input.clear()
            self._reset_button()
            self.login_successful.emit(user)
        else:
            self._reset_button()
            self._show_error("Invalid username or password.\nPlease try again.")
            self.password_input.selectAll()
            self.password_input.setFocus()

    def _reset_button(self):
        """Restore the login button to its default enabled state."""
        self.login_button.setEnabled(True)
        self.login_button.setText("Sign In")

    def _show_error(self, message: str):
        """Display an error QMessageBox with the given message."""
        QMessageBox.warning(
            self,
            "Login Failed",
            message,
            QMessageBox.StandardButton.Ok,
        )
