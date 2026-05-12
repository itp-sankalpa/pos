"""
StatusBadge — a QLabel styled as a pill/badge for status display.
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

from ui.theme import status_badge_qss


class StatusBadge(QLabel):
    """A pill-shaped badge that displays a status string.

    The style is derived automatically via ``status_badge_qss()`` from
    the theme module.

    Parameters
    ----------
    status : str
        Status text (e.g. "PENDING", "PAID", "IN_PROGRESS").
    parent : QWidget, optional
    """

    def __init__(self, status: str, parent=None):
        super().__init__(parent)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(80)
        self._apply_status(status)

    # ── Private ───────────────────────────────────────────────────

    def _apply_status(self, status: str) -> None:
        """Set the text and apply matching QSS for the given status."""
        self.setText(status)
        self.setStyleSheet(status_badge_qss(status))

    # ── Public API ────────────────────────────────────────────────

    def set_status(self, status: str) -> None:
        """Update the badge text and re-apply the appropriate style."""
        self._apply_status(status)
