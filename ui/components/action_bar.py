"""
ActionBar — horizontal button bar for page-level actions.
"""

import tkinter as tk
from tkinter import ttk
from ui.theme import COLOR_BORDER, SPACING_SM, SPACING_MD


class ActionBar(ttk.Frame):
    """Bottom-aligned horizontal bar holding action buttons.

    Buttons are added from right to left, with an optional stretch
    spacer to push them apart.

    Parameters
    ----------
    parent : Widget, optional
    """

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        # Top border
        sep = ttk.Separator(self, orient="horizontal")
        sep.pack(fill="x", pady=(0, SPACING_SM))

        # Button container (right-aligned)
        self._btn_frame = ttk.Frame(self)
        self._btn_frame.pack(fill="x", padx=(0, SPACING_MD))

        # Buttons will be packed from right
        self._buttons = []

    # ── Public API ────────────────────────────────────────────────

    def add_button(self, text: str, callback, button_id: str = "btn_primary") -> ttk.Button:
        """Add a button to the action bar.

        Parameters
        ----------
        text : str
            Button label.
        callback : callable
            Invoked on click.
        button_id : str
            Style identifier — ``btn_primary`` (default), ``btn_secondary``,
            ``btn_danger``, ``btn_success``.

        Returns
        -------
        ttk.Button
        """
        style_map = {
            "btn_primary": "Primary.TButton",
            "btn_secondary": "Secondary.TButton",
            "btn_danger": "Danger.TButton",
            "btn_success": "Success.TButton",
        }
        style_name = style_map.get(button_id, "Primary.TButton")

        btn = ttk.Button(self._btn_frame, text=text, command=callback, style=style_name)
        btn.pack(side="right", padx=(SPACING_SM, 0))
        self._buttons.append(btn)
        return btn

    def add_stretch(self) -> None:
        """Add spacer between button groups."""
        spacer = ttk.Frame(self._btn_frame)
        spacer.pack(side="right", padx=SPACING_MD)
