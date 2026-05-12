"""
SummaryCard — compact metric card with colored accent border.
"""

import tkinter as tk
from ui.theme import (
    COLOR_PANEL_BG,
    COLOR_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_ACCENT,
    FONT_SECTION_TITLE,
    FONT_SMALL,
    SPACING_SM,
    SPACING_XS,
)


class SummaryCard(tk.Frame):
    """A compact card displaying a single metric value.

    Parameters
    ----------
    title : str
        Short label shown above the value (e.g. "Today's Revenue").
    value : str
        The displayed value (e.g. "Rs. 25,000.00").
    accent_color : str
        Color for the 4 px left-border accent strip.
    parent : Widget, optional
    """

    def __init__(self, title: str, value: str = "0", accent_color: str = COLOR_ACCENT, parent=None, **kwargs):
        super().__init__(parent, bg=COLOR_PANEL_BG, highlightbackground=accent_color,
                        highlightthickness=4, padx=SPACING_SM, pady=SPACING_SM, **kwargs)

        self._accent_color = accent_color
        self.configure(width=160)
        self.pack_propagate(False)

        # Title
        self._title_label = tk.Label(
            self, text=title, font=("Segoe UI", FONT_SMALL),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, anchor="w",
        )
        self._title_label.pack(fill="x")

        # Value
        self._value_label = tk.Label(
            self, text=value, font=("Segoe UI", FONT_SECTION_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, anchor="w",
        )
        self._value_label.pack(fill="x", pady=(SPACING_XS, 0))

    # ── Public API ────────────────────────────────────────────────

    def set_value(self, value: str) -> None:
        """Update the displayed value."""
        self._value_label.config(text=value)

    def set_title(self, title: str) -> None:
        """Update the card title."""
        self._title_label.config(text=title)
