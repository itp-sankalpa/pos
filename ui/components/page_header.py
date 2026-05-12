"""
PageHeader — title + subtitle + action buttons for each screen.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt

from ui.theme import (
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_PAGE_TITLE,
    FONT_SMALL,
    SPACING_MD,
    SPACING_SM,
)


class PageHeader(QWidget):
    """Horizontal header bar with title, optional subtitle, and action buttons.

    Parameters
    ----------
    title : str
        Page title text (displayed in FONT_PAGE_TITLE, bold).
    subtitle : str, optional
        Secondary descriptive text below/next to the title.
    parent : QWidget, optional
    """

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)

        self._title_text = title
        self._subtitle_text = subtitle

        # ── Main layout ──
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, SPACING_MD)  # bottom margin
        self._layout.setSpacing(SPACING_SM)

        # ── Left: title + subtitle ──
        self._title_label = QLabel(title)
        self._title_label.setObjectName("page_title")
        self._title_label.setStyleSheet(
            f"font-size: {FONT_PAGE_TITLE}px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};"
        )
        self._layout.addWidget(self._title_label)

        if subtitle:
            self._subtitle_label = QLabel(subtitle)
            self._subtitle_label.setObjectName("secondary")
            self._subtitle_label.setStyleSheet(
                f"font-size: {FONT_SMALL}px; color: {COLOR_TEXT_SECONDARY};"
            )
            self._layout.addWidget(self._subtitle_label)
        else:
            self._subtitle_label = None

        # ── Spacer pushes buttons to the right ──
        self._layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

    # ── Public API ────────────────────────────────────────────────

    def add_action(self, button_text: str, callback, button_id: str = "btn_primary") -> QPushButton:
        """Add an action button on the right side of the header.

        Parameters
        ----------
        button_text : str
            Label shown on the button.
        callback : callable
            Function invoked when the button is clicked.
        button_id : str
            QSS object-name id — ``btn_primary`` (default), ``btn_secondary``,
            ``btn_danger``, ``btn_success``.

        Returns
        -------
        QPushButton
            The newly created button.
        """
        btn = QPushButton(button_text)
        btn.setObjectName(button_id)
        btn.clicked.connect(callback)
        self._layout.addWidget(btn)
        return btn
