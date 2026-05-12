"""
StatusBadge — a tk.Label styled as a pill/badge for status display.
"""

import tkinter as tk
from ui.theme import status_badge_colors, FONT_SMALL, COLOR_TEXT_PRIMARY


class StatusBadge(tk.Label):
    """A pill-shaped badge that displays a status string.

    The colors are derived automatically via ``status_badge_colors()``
    from the theme module.

    Parameters
    ----------
    status : str
        Status text (e.g. "PENDING", "PAID", "IN_PROGRESS").
    parent : Widget, optional
    """

    def __init__(self, status: str, parent=None, **kwargs):
        colors = status_badge_colors(status)
        super().__init__(
            parent, text=status,
            font=("Segoe UI", FONT_SMALL, "bold"),
            fg=colors["fg"], bg=colors["bg"],
            padx=10, pady=3,
            anchor="center",
            **kwargs,
        )
        self._status = status

    # ── Public API ────────────────────────────────────────────────

    def set_status(self, status: str) -> None:
        """Update the badge text and re-apply the appropriate style."""
        colors = status_badge_colors(status)
        self.config(text=status, fg=colors["fg"], bg=colors["bg"])
        self._status = status
