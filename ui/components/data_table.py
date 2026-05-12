"""
DataTable — reusable QTableWidget wrapper for the Vehicle Service POS.
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt

from ui.theme import TABLE_ROW_HEIGHT, TABLE_HEADER_HEIGHT


class DataTable(QTableWidget):
    """A styled, read-only data table with single-row selection.

    Parameters
    ----------
    columns : list[tuple[str, int]]
        Each tuple is (header_text, column_width_px). Width 0 means the
        column stretches to fill remaining space.
    parent : QWidget, optional
    """

    def __init__(self, columns: list[tuple[str, int]], parent=None):
        super().__init__(parent)

        self._columns = columns

        # --- Basic table setup ---
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels([col[0] for col in columns])
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)

        # Read-only
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Single-row selection
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # Header stretch for zero-width columns
        header = self.horizontalHeader()
        for idx, (_, width) in enumerate(columns):
            if width == 0:
                header.setSectionResizeMode(idx, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(idx, QHeaderView.ResizeMode.Fixed)
                self.setColumnWidth(idx, width)

        # Row / header heights
        self.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setFixedHeight(TABLE_HEADER_HEIGHT)

        # Hide grid for cleaner look (global QSS handles border)
        self.setShowGrid(True)

        # Scroll hints
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        # Object name so global QSS targets QTableWidget properly
        self.setObjectName("data_table")

    # ── Public API ────────────────────────────────────────────────

    def load_data(self, rows: list[list]) -> None:
        """Clear existing rows and populate the table with new data.

        Each inner list should have the same length as *columns*.
        Items are converted to strings via ``str()``.
        """
        self.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                # Store the raw value in the UserRole for potential retrieval
                item.setData(Qt.ItemDataRole.UserRole, value)
                self.setItem(row_idx, col_idx, item)
        self.setRowCount(len(rows))

    def get_selected_row(self) -> int:
        """Return the index of the currently selected row, or -1 if none."""
        rows = self.selectionModel().selectedRows()
        if rows:
            return rows[0].row()
        return -1

    def get_selected_data(self, col: int) -> str:
        """Return the text from *col* of the currently selected row.

        Returns an empty string if nothing is selected.
        """
        row = self.get_selected_row()
        if row < 0:
            return ""
        item = self.item(row, col)
        return item.text() if item else ""

    def set_double_click_handler(self, callback) -> None:
        """Connect *callback* to ``cellDoubleClicked`` signal."""
        self.cellDoubleClicked.connect(callback)
