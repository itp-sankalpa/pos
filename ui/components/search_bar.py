"""
SearchBar — search input with optional filter combo and debounced callback.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QComboBox
from PyQt6.QtCore import QTimer, Qt

from ui.theme import (
    COLOR_BORDER,
    COLOR_ACCENT,
    COLOR_PANEL_BG,
    COLOR_TEXT_PRIMARY,
    INPUT_HEIGHT,
    SPACING_SM,
    FONT_BODY,
)


class SearchBar(QWidget):
    """Horizontal search bar with an optional filter dropdown.

    Parameters
    ----------
    placeholder : str
        Placeholder text for the search input.
    filters : list[str], optional
        List of filter options shown in a QComboBox. The first item
        should typically be an "All" / default option.
    parent : QWidget, optional
    """

    def __init__(self, placeholder: str = "Search...", filters: list[str] = None, parent=None):
        super().__init__(parent)

        self._search_callback = None
        self._filter_callback = None

        # ── Layout ──
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING_SM)

        # ── Search input ──
        self._input = QLineEdit()
        self._input.setPlaceholderText(placeholder)
        self._input.setFixedHeight(INPUT_HEIGHT)
        self._input.setStyleSheet(
            f"QLineEdit {{ "
            f"border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 4px; "
            f"padding: 5px 10px; "
            f"min-height: {INPUT_HEIGHT}px; "
            f"background-color: {COLOR_PANEL_BG}; "
            f"font-size: {FONT_BODY}px; "
            f"color: {COLOR_TEXT_PRIMARY}; "
            f"}}"
            f"QLineEdit:focus {{ border-color: {COLOR_ACCENT}; }}"
        )
        layout.addWidget(self._input, stretch=1)

        # ── Debounce timer ──
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)
        self._debounce_timer.timeout.connect(self._fire_search)

        self._input.textChanged.connect(self._on_text_changed)

        # ── Filter combo (optional) ──
        self._combo: QComboBox | None = None
        if filters:
            self._combo = QComboBox()
            self._combo.addItems(filters)
            self._combo.setFixedHeight(INPUT_HEIGHT)
            self._combo.setMinimumWidth(140)
            self._combo.currentTextChanged.connect(self._on_filter_changed)
            layout.addWidget(self._combo)

    # ── Private ───────────────────────────────────────────────────

    def _on_text_changed(self, _text: str) -> None:
        """Restart debounce timer on every keystroke."""
        self._debounce_timer.start()

    def _fire_search(self) -> None:
        """Emit the debounced search callback with current text."""
        if self._search_callback:
            self._search_callback(self._input.text())

    def _on_filter_changed(self, text: str) -> None:
        """Forward filter changes to the registered callback."""
        if self._filter_callback:
            self._filter_callback(text)

    # ── Public API ────────────────────────────────────────────────

    def text(self) -> str:
        """Return the current search text."""
        return self._input.text()

    def filter_text(self) -> str:
        """Return the current filter selection, or empty string if no combo."""
        if self._combo is not None:
            return self._combo.currentText()
        return ""

    def set_search_callback(self, callback) -> None:
        """Register *callback(text)* — called after 300 ms debounce."""
        self._search_callback = callback

    def set_filter_callback(self, callback) -> None:
        """Register *callback(filter_text)* — called on combo change."""
        self._filter_callback = callback
