"""
PageHeader — title + subtitle + action buttons for each screen.
"""

import tkinter as tk
from tkinter import ttk
from ui.theme import (
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_APP_BG,
    FONT_PAGE_TITLE,
    FONT_SMALL,
    SPACING_MD,
    SPACING_SM,
)


class PageHeader(ttk.Frame):
    """Horizontal header bar with title, optional subtitle, and action buttons.

    Parameters
    ----------
    title : str
        Page title text (displayed in FONT_PAGE_TITLE, bold).
    subtitle : str, optional
        Secondary descriptive text below the title.
    parent : Widget, optional
    """

    def __init__(self, title: str, subtitle: str = "", parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._title_text = title
        self._buttons = []

        # Configure grid: title on left, buttons on right
        self.columnconfigure(1, weight=1)  # spacer stretches

        # Title
        self._title_label = tk.Label(
            self, text=title, font=("Segoe UI", FONT_PAGE_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_APP_BG,
            anchor="w",
        )
        self._title_label.grid(row=0, column=0, sticky="w", padx=(0, SPACING_SM))

        # Subtitle
        if subtitle:
            self._subtitle_label = tk.Label(
                self, text=subtitle, font=("Segoe UI", FONT_SMALL),
                fg=COLOR_TEXT_SECONDARY, bg=COLOR_APP_BG, anchor="w",
            )
            # Put subtitle below title
            self._title_label.grid(row=0, column=0, sticky="w")
            self._subtitle_label.grid(row=1, column=0, sticky="w")
            self.rowconfigure(1, minsize=FONT_SMALL + 4)

        # Spacer
        spacer = ttk.Frame(self)
        spacer.grid(row=0, column=1, rowspan=2, sticky="ew")

        # Button container
        self._btn_frame = ttk.Frame(self)
        self._btn_frame.grid(row=0, column=2, rowspan=2, sticky="e")

        self._btn_col = 0

        # Bottom margin
        self.grid(pady=(0, SPACING_MD), sticky="ew")

    # ── Public API ────────────────────────────────────────────────

    def add_action(self, button_text: str, callback, button_id: str = "btn_primary") -> ttk.Button:
        """Add an action button on the right side of the header.

        Parameters
        ----------
        button_text : str
            Label shown on the button.
        callback : callable
            Function invoked when the button is clicked.
        button_id : str
            Style identifier — ``btn_primary`` (default), ``btn_secondary``,
            ``btn_danger``, ``btn_success``.

        Returns
        -------
        ttk.Button
            The newly created button.
        """
        style_map = {
            "btn_primary": "Primary.TButton",
            "btn_secondary": "Secondary.TButton",
            "btn_danger": "Danger.TButton",
            "btn_success": "Success.TButton",
        }
        style_name = style_map.get(button_id, "Primary.TButton")

        btn = ttk.Button(self._btn_frame, text=button_text, command=callback, style=style_name)
        btn.grid(row=0, column=self._btn_col, padx=(SPACING_SM, 0))
        self._btn_col += 1
        self._buttons.append(btn)
        return btn
