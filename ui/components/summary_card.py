"""
SummaryCard — compact metric card with colored accent border.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

from ui.theme import (
    COLOR_PANEL_BG,
    COLOR_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_ACCENT,
    FONT_SECTION_TITLE,
    FONT_SMALL,
    SPACING_XS,
    SPACING_SM,
)


class SummaryCard(QWidget):
    """A compact card displaying a single metric value.

    Parameters
    ----------
    title : str
        Short label shown above the value (e.g. "Today's Revenue").
    value : str
        The displayed value (e.g. "Rs. 25,000.00").
    accent_color : str
        Color for the 4 px left-border accent strip.
    parent : QWidget, optional
    """

    def __init__(self, title: str, value: str = "0", accent_color: str = COLOR_ACCENT, parent=None):
        super().__init__(parent)

        self._accent_color = accent_color

        self.setFixedWidth(160)
        self.setStyleSheet(
            f"SummaryCard {{ "
            f"background-color: {COLOR_PANEL_BG}; "
            f"border: 1px solid {COLOR_BORDER}; "
            f"border-left: 4px solid {accent_color}; "
            f"border-radius: 6px; "
            f"}}"
        )

        # ── Inner layout ──
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_SM, SPACING_SM, SPACING_SM, SPACING_SM)
        layout.setSpacing(SPACING_XS)

        # ── Title label ──
        self._title_label = QLabel(title)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._title_label.setStyleSheet(
            f"color: {COLOR_TEXT_SECONDARY}; "
            f"font-size: {FONT_SMALL}px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._title_label)

        # ── Value label ──
        self._value_label = QLabel(value)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._value_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; "
            f"font-size: {FONT_SECTION_TITLE}px; "
            f"font-weight: bold; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._value_label)

    # ── Public API ────────────────────────────────────────────────

    def set_value(self, value: str) -> None:
        """Update the displayed value."""
        self._value_label.setText(value)

    def set_title(self, title: str) -> None:
        """Update the card title."""
        self._title_label.setText(title)
