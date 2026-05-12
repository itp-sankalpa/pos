"""
DataTable — reusable ttk.Treeview wrapper for the Vehicle Service POS.
"""

import tkinter as tk
from tkinter import ttk
from ui.theme import TABLE_ROW_HEIGHT, TABLE_HEADER_HEIGHT, COLOR_PANEL_BG, COLOR_SELECTED_ROW_BG


class DataTable(ttk.Frame):
    """A styled, read-only data table with single-row selection.

    Parameters
    ----------
    columns : list[tuple[str, int]]
        Each tuple is (header_text, column_width_px). Width 0 means the
        column stretches to fill remaining space.
    parent : Widget, optional
    """

    def __init__(self, columns: list[tuple[str, int]], parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._columns = columns
        self._col_ids = [f"col{i}" for i in range(len(columns))]
        self._double_click_callback = None

        # Create treeview
        self._tree = ttk.Treeview(
            self,
            columns=self._col_ids,
            show="headings",
            selectmode="browse",
            height=15,
        )

        for idx, (header, width) in enumerate(columns):
            col_id = self._col_ids[idx]
            self._tree.heading(col_id, text=header)
            if width == 0:
                self._tree.column(col_id, width=200, stretch=True)
            else:
                self._tree.column(col_id, width=width, stretch=False, minwidth=width)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        # Pack
        self._tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind double-click
        self._tree.bind("<Double-1>", self._on_double_click)

    # ── Private ───────────────────────────────────────────────────

    def _on_double_click(self, event):
        if self._double_click_callback:
            selected = self._tree.selection()
            if selected:
                item_id = selected[0]
                index = self._tree.index(item_id)
                self._double_click_callback(index)

    # ── Public API ────────────────────────────────────────────────

    def load_data(self, rows: list[list]) -> None:
        """Clear existing rows and populate the table with new data.

        Each inner list should have the same length as *columns*.
        Items are converted to strings via ``str()``.
        """
        self._tree.delete(*self._tree.get_children())
        for row_idx, row_data in enumerate(rows):
            str_data = [str(v) for v in row_data]
            tag = "even" if row_idx % 2 == 0 else "odd"
            self._tree.insert("", "end", values=str_data, tags=(tag,))
        self._tree.tag_configure("even", background=COLOR_PANEL_BG)
        self._tree.tag_configure("odd", background="#F8F9FA")

    def get_selected_row(self) -> int:
        """Return the index of the currently selected row, or -1 if none."""
        selected = self._tree.selection()
        if not selected:
            return -1
        return self._tree.index(selected[0])

    def get_selected_data(self, col: int) -> str:
        """Return the text from *col* of the currently selected row.

        Returns an empty string if nothing is selected.
        """
        selected = self._tree.selection()
        if not selected:
            return ""
        item = self._tree.item(selected[0])
        values = item.get("values", [])
        if col < len(values):
            return str(values[col])
        return ""

    def set_double_click_handler(self, callback) -> None:
        """Connect *callback* to double-click on a row.

        callback receives the row index as its argument.
        """
        self._double_click_callback = callback

    def set_cell_widget(self, row: int, col: int, widget) -> None:
        """Not supported in Treeview — status badges handled differently."""
        pass
