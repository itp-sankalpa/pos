"""
SearchBar — search input with optional filter combo and debounced callback.
"""

import tkinter as tk
from tkinter import ttk
from ui.theme import (
    COLOR_BORDER,
    COLOR_ACCENT,
    COLOR_PANEL_BG,
    COLOR_TEXT_PRIMARY,
    INPUT_HEIGHT,
    SPACING_SM,
    FONT_BODY,
)


class SearchBar(ttk.Frame):
    """Horizontal search bar with an optional filter dropdown.

    Parameters
    ----------
    placeholder : str
        Placeholder text for the search input.
    filters : list[str], optional
        List of filter options shown in a Combobox. The first item
        should typically be an "All" / default option.
    parent : Widget, optional
    """

    def __init__(self, placeholder: str = "Search...", filters: list[str] = None, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self._search_callback = None
        self._filter_callback = None
        self._debounce_id = None

        # Search input
        self._input_var = tk.StringVar()
        self._input = tk.Entry(
            self, textvariable=self._input_var, font=("Segoe UI", FONT_BODY),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief="solid", bd=1,
        )
        self._input.insert(0, placeholder)
        self._input.config(fg="#999999")
        self._input.bind("<FocusIn>", self._on_focus_in)
        self._input.bind("<FocusOut>", self._on_focus_out)
        self._input.bind("<KeyRelease>", self._on_key_release)
        self._placeholder = placeholder
        self._is_placeholder = True

        self._input.pack(side="left", fill="x", expand=True, padx=(0, SPACING_SM))

        # Filter combo (optional)
        self._combo: ttk.Combobox | None = None
        if filters:
            self._combo_var = tk.StringVar(value=filters[0])
            self._combo = ttk.Combobox(
                self, textvariable=self._combo_var, values=filters,
                state="readonly", width=18,
            )
            self._combo.pack(side="right")
            self._combo.bind("<<ComboboxSelected>>", self._on_filter_changed)

    # ── Private ───────────────────────────────────────────────────

    def _on_focus_in(self, event):
        if self._is_placeholder:
            self._input.delete(0, "end")
            self._input.config(fg=COLOR_TEXT_PRIMARY)
            self._is_placeholder = False

    def _on_focus_out(self, event):
        if not self._input.get().strip():
            self._input.insert(0, self._placeholder)
            self._input.config(fg="#999999")
            self._is_placeholder = True

    def _on_key_release(self, event):
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(300, self._fire_search)

    def _fire_search(self):
        if self._search_callback:
            text = self.text()
            self._search_callback(text)

    def _on_filter_changed(self, event):
        if self._filter_callback and self._combo:
            self._filter_callback(self._combo.get())

    # ── Public API ────────────────────────────────────────────────

    def text(self) -> str:
        """Return the current search text (empty if placeholder is shown)."""
        if self._is_placeholder:
            return ""
        return self._input.get()

    def filter_text(self) -> str:
        """Return the current filter selection, or empty string if no combo."""
        if self._combo:
            return self._combo.get()
        return ""

    def set_search_callback(self, callback) -> None:
        """Register *callback(text)* — called after 300 ms debounce."""
        self._search_callback = callback

    def set_filter_callback(self, callback) -> None:
        """Register *callback(filter_text)* — called on combo change."""
        self._filter_callback = callback
