"""
ActionBar — horizontal button bar for page-level actions.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QFrame,
)
from PyQt6.QtCore import Qt

from ui.theme import (
    COLOR_BORDER,
    SPACING_SM,
    SPACING_MD,
)


class ActionBar(QWidget):
    """Bottom-aligned horizontal bar holding action buttons.

    Buttons are added from left to right, with an optional stretch
    spacer to push them apart.

    Parameters
    ----------
    parent : QWidget, optional
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Outer vertical layout: top-border + button row ──
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(0)

        # ── Top border line ──
        self._border = QFrame()
        self._border.setFrameShape(QFrame.Shape.HLine)
        self._border.setFixedHeight(1)
        self._border.setStyleSheet(
            f"background-color: {COLOR_BORDER}; border: none;"
        )
        self._outer.addWidget(self._border)

        # ── Button row container ──
        self._btn_container = QWidget()
        self._btn_layout = QHBoxLayout(self._btn_container)
        self._btn_layout.setContentsMargins(0, SPACING_SM, SPACING_MD, SPACING_SM)
        self._btn_layout.setSpacing(SPACING_SM)
        # Trailing spacer pushes buttons to the right
        self._btn_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self._outer.addWidget(self._btn_container)

    # ── Public API ────────────────────────────────────────────────

    def add_button(self, text: str, callback, button_id: str = "btn_primary") -> QPushButton:
        """Add a button to the action bar.

        Parameters
        ----------
        text : str
            Button label.
        callback : callable
            Invoked on click.
        button_id : str
            QSS object-name id — ``btn_primary`` (default), ``btn_secondary``,
            ``btn_danger``, ``btn_success``.

        Returns
        -------
        QPushButton
        """
        btn = QPushButton(text)
        btn.setObjectName(button_id)
        btn.clicked.connect(callback)
        # Insert before the trailing spacer (last item)
        self._btn_layout.insertWidget(self._btn_layout.count() - 1, btn)
        return btn

    def add_stretch(self) -> None:
        """Add a horizontal spacer between button groups."""
        self._btn_layout.insertSpacerItem(
            self._btn_layout.count() - 1,
            QSpacerItem(SPACING_MD, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum),
        )
