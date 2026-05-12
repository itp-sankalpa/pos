"""
FormPanel — a white card panel with grid layout and optional section title.
"""

import tkinter as tk
from tkinter import ttk
from ui.theme import (
    COLOR_PANEL_BG,
    COLOR_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_SECTION_TITLE,
    FONT_SMALL,
    SPACING_MD,
    SPACING_SM,
    SPACING_XS,
)


class FormPanel(ttk.Frame):
    """A styled card panel containing a form grid.

    Parameters
    ----------
    title : str, optional
        Section title displayed at the top of the panel.
    parent : Widget, optional
    """

    def __init__(self, title: str = "", parent=None, **kwargs):
        super().__init__(parent, style="Panel.TFrame", **kwargs)

        self._row_count = 0

        # Outer padding
        self.configure(padding=(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD))

        # Optional title
        if title:
            title_label = tk.Label(
                self, text=title, font=("Segoe UI", FONT_SECTION_TITLE, "bold"),
                fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, anchor="w",
            )
            title_label.grid(row=self._row_count, column=0, columnspan=2,
                           sticky="w", pady=(0, SPACING_SM))
            self._row_count += 1

        # Configure columns: label on left, widget on right
        self.columnconfigure(1, weight=1)

        # Border
        self.configure(relief="solid", borderwidth=1)

    # ── Public API ────────────────────────────────────────────────

    def add_row(self, label: str, widget: tk.Widget) -> None:
        """Add a labeled row to the form.

        Parameters
        ----------
        label : str
            Text displayed on the left side.
        widget : tk.Widget
            Input widget displayed on the right side.
        """
        lbl = tk.Label(
            self, text=label, font=("Segoe UI", FONT_SMALL),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, anchor="e",
        )
        lbl.grid(row=self._row_count, column=0, sticky="e", padx=(0, SPACING_MD), pady=SPACING_XS)

        widget.grid(row=self._row_count, column=1, sticky="ew", pady=SPACING_XS)
        self._row_count += 1

    def add_separator(self) -> None:
        """Add a horizontal separator line to the form."""
        sep = ttk.Separator(self, orient="horizontal")
        sep.grid(row=self._row_count, column=0, columnspan=2, sticky="ew", pady=SPACING_SM)
        self._row_count += 1
