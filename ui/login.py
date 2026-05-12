"""
Login screen for the Vehicle Service Center POS application (Tkinter version).
Displays a centered login card on a grey background.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from ui.theme import (
    COLOR_APP_BG, COLOR_PANEL_BG, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_BORDER, FONT_FAMILY, FONT_PAGE_TITLE, FONT_BODY,
    FONT_BUTTON, FONT_SMALL, SPACING_SM, SPACING_MD,
    SPACING_LG, SPACING_XL, BUTTON_HEIGHT, INPUT_HEIGHT,
)
from controllers.auth_controller import AuthController


class LoginScreen(tk.Tk):
    """Centered login form with app branding, username/password fields, and login button."""

    def __init__(self, on_login_success=None):
        super().__init__()
        self._auth = AuthController()
        self._on_login_success = on_login_success

        self.title("Vehicle Service POS — Login")
        self.geometry(f"500x600")
        self.resizable(False, False)
        self.configure(bg=COLOR_APP_BG)

        self._build_ui()

        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 600) // 2
        self.geometry(f"+{x}+{y}")

    # ── UI Construction ──────────────────────────────────────────────

    def _build_ui(self):
        # Outer container - centres the card
        outer = tk.Frame(self, bg=COLOR_APP_BG)
        outer.pack(fill="both", expand=True)

        # Vertical spacer above the card
        spacer_top = tk.Frame(outer, bg=COLOR_APP_BG)
        spacer_top.pack(fill="both", expand=True)

        # Card container (centered)
        card_container = tk.Frame(outer, bg=COLOR_APP_BG)
        card_container.pack()

        # Card
        card = tk.Frame(
            card_container, bg=COLOR_PANEL_BG,
            padx=SPACING_XL, pady=SPACING_XL,
            highlightbackground=COLOR_BORDER, highlightthickness=1,
        )
        card.pack()

        # App title
        title = tk.Label(
            card, text="Vehicle Service POS",
            font=(FONT_FAMILY, FONT_PAGE_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
        )
        title.pack(pady=(0, SPACING_SM))

        # Subtitle
        subtitle = tk.Label(
            card, text="Sign in to your account",
            font=(FONT_FAMILY, FONT_SMALL),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG,
        )
        subtitle.pack(pady=(0, SPACING_LG))

        # Username label
        user_label = tk.Label(
            card, text="Username",
            font=(FONT_FAMILY, FONT_SMALL, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, anchor="w",
        )
        user_label.pack(fill="x")

        # Username input
        self.username_input = tk.Entry(
            card, font=(FONT_FAMILY, FONT_BODY),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief="solid", bd=1, highlightthickness=1,
            highlightcolor=COLOR_ACCENT, highlightbackground=COLOR_BORDER,
        )
        self.username_input.pack(fill="x", ipady=6, pady=(SPACING_XS, 0))
        self.username_input.insert(0, "Enter your username")
        self.username_input.config(fg="#999999")
        self._user_placeholder = True
        self.username_input.bind("<FocusIn>", self._user_focus_in)
        self.username_input.bind("<FocusOut>", self._user_focus_out)
        self.username_input.bind("<Return>", lambda e: self.password_input.focus_set())

        # Password label
        pass_label = tk.Label(
            card, text="Password",
            font=(FONT_FAMILY, FONT_SMALL, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, anchor="w",
        )
        pass_label.pack(fill="x", pady=(SPACING_MD, 0))

        # Password input
        self.password_input = tk.Entry(
            card, font=(FONT_FAMILY, FONT_BODY),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
            insertbackground=COLOR_TEXT_PRIMARY,
            show="•", relief="solid", bd=1, highlightthickness=1,
            highlightcolor=COLOR_ACCENT, highlightbackground=COLOR_BORDER,
        )
        self.password_input.pack(fill="x", ipady=6, pady=(SPACING_XS, 0))
        self.password_input.bind("<Return>", lambda e: self._on_login())

        # Login button
        self.login_button = tk.Button(
            card, text="Sign In",
            font=(FONT_FAMILY, FONT_BUTTON, "bold"),
            fg="#FFFFFF", bg=COLOR_ACCENT,
            activeforeground="#FFFFFF", activebackground=COLOR_ACCENT_HOVER,
            relief="flat", bd=0,
            cursor="hand2", pady=8,
            command=self._on_login,
        )
        self.login_button.pack(fill="x", pady=(SPACING_LG, 0))

        # Vertical spacer below the card
        spacer_bottom = tk.Frame(outer, bg=COLOR_APP_BG)
        spacer_bottom.pack(fill="both", expand=True)

    # ── Placeholder handling ────────────────────────────────────────

    def _user_focus_in(self, event):
        if self._user_placeholder:
            self.username_input.delete(0, "end")
            self.username_input.config(fg=COLOR_TEXT_PRIMARY)
            self._user_placeholder = False

    def _user_focus_out(self, event):
        if not self.username_input.get().strip():
            self.username_input.insert(0, "Enter your username")
            self.username_input.config(fg="#999999")
            self._user_placeholder = True

    # ── Handlers ─────────────────────────────────────────────────────

    def _on_login(self):
        """Validate inputs and attempt authentication via AuthController."""
        # Get username (handle placeholder)
        if self._user_placeholder:
            username = ""
        else:
            username = self.username_input.get().strip()

        password = self.password_input.get()

        if not username:
            messagebox.showwarning("Login Failed", "Please enter your username.")
            self.username_input.focus_set()
            return

        if not password:
            messagebox.showwarning("Login Failed", "Please enter your password.")
            self.password_input.focus_set()
            return

        # Disable button while authenticating
        self.login_button.config(state="disabled", text="Signing in…")
        self.update_idletasks()

        user = self._auth.login(username, password)

        if user is not None:
            # Success — clear sensitive fields
            self.password_input.delete(0, "end")
            self._reset_button()
            if self._on_login_success:
                self._on_login_success(user)
        else:
            self._reset_button()
            messagebox.showwarning(
                "Login Failed",
                "Invalid username or password.\nPlease try again.",
            )
            self.password_input.focus_set()

    def _reset_button(self):
        """Restore the login button to its default enabled state."""
        self.login_button.config(state="normal", text="Sign In")
