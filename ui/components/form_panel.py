"""
FormPanel — a white card panel with QFormLayout and optional section title.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLabel,
    QFrame,
    QVBoxLayout,
)
from PyQt6.QtCore import Qt

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


class FormPanel(QWidget):
    """A styled card panel containing a QFormLayout.

    Parameters
    ----------
    title : str, optional
        Section title displayed at the top of the panel.
    parent : QWidget, optional
    """

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)

        self.setObjectName("panel")
        self.setStyleSheet(
            f"QWidget#panel {{ "
            f"background-color: {COLOR_PANEL_BG}; "
            f"border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 6px; "
            f"}}"
        )

        # ── Outer layout (for title + form) ──
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        self._outer.setSpacing(SPACING_SM)

        # ── Optional title ──
        if title:
            self._title_label = QLabel(title)
            self._title_label.setObjectName("section_title")
            self._title_label.setStyleSheet(
                f"font-size: {FONT_SECTION_TITLE}px; font-weight: bold; "
                f"color: {COLOR_TEXT_PRIMARY}; background: transparent; border: none;"
            )
            self._outer.addWidget(self._title_label)
        else:
            self._title_label = None

        # ── Form layout ──
        self._form = QFormLayout()
        self._form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._form.setHorizontalSpacing(SPACING_MD)
        self._form.setVerticalSpacing(SPACING_XS)

        self._outer.addLayout(self._form)

        # ── Label styling (applied to the FormPanel widget itself) ──
        # QFormLayout labels are QLabels inside this widget, so we scope
        # the rule to descendants of this panel.
        base_qss = self.styleSheet()
        label_qss = (
            f"QWidget#panel QLabel {{ "
            f"color: {COLOR_TEXT_SECONDARY}; "
            f"font-size: {FONT_SMALL}px; "
            f"}}"
        )
        self.setStyleSheet(base_qss + label_qss)

    # ── Public API ────────────────────────────────────────────────

    def add_row(self, label: str, widget: QWidget) -> None:
        """Add a labeled row to the form.

        Parameters
        ----------
        label : str
            Text displayed on the left side.
        widget : QWidget
            Input widget displayed on the right side.
        """
        self._form.addRow(label, widget)

    def add_separator(self) -> None:
        """Add a horizontal separator line to the form."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(
            f"background-color: {COLOR_BORDER}; border: none; max-height: 1px; "
            f"margin-top: {SPACING_XS}px; margin-bottom: {SPACING_XS}px;"
        )
        # Span both columns
        self._form.addRow(line)
