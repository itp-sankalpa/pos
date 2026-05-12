"""
SettingsScreen — application configuration for the Vehicle Service POS.
"""

import json
import logging

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtPrintSupport import QPrinter, QPrinterInfo

from ui.theme import (
    COLOR_APP_BG,
    COLOR_PANEL_BG,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_BORDER,
    COLOR_ACCENT,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_ERROR,
    COLOR_INFO,
    COLOR_SIDEBAR_BG,
    COLOR_SIDEBAR_TEXT,
    FONT_FAMILY,
    FONT_PAGE_TITLE,
    FONT_SECTION_TITLE,
    FONT_BODY,
    FONT_BUTTON,
    FONT_SMALL,
    FONT_MONO,
    SPACING_XS,
    SPACING_SM,
    SPACING_MD,
    SPACING_LG,
    BUTTON_HEIGHT,
    INPUT_HEIGHT,
)
from ui.components import (
    PageHeader,
    FormPanel,
)
from config import (
    APP_NAME,
    APP_VERSION,
    DATA_DIR,
    PRINTER_SETTINGS,
    RECEIPT_CHARS_80MM,
    RECEIPT_CHARS_58MM,
)

import os

logger = logging.getLogger(__name__)

# ─── Settings file path ────────────────────────────────────────────────
SETTINGS_FILE = os.path.join(DATA_DIR, "app_settings.json")


def _load_settings() -> dict:
    """Load settings from the JSON config file, returning defaults if missing."""
    defaults = {
        "business_name": "",
        "business_address": "",
        "business_phone": "",
        "thermal_paper_width": 80,
        "a4_printer_name": "",
        "thermal_printer_name": "",
        "thermal_chars_per_line": RECEIPT_CHARS_80MM,
        "thermal_auto_cut": True,
        "thermal_cash_drawer": False,
    }
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                defaults.update(saved)
    except Exception:
        logger.exception("Error loading settings, using defaults")
    return defaults


def _save_settings(settings: dict) -> bool:
    """Save settings to the JSON config file. Returns True on success."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        logger.exception("Error saving settings")
        return False


class SettingsScreen(QWidget):
    """Settings screen with General, Printer, and About tabs."""

    def __init__(self, session, stacked_widget=None, parent=None):
        super().__init__(parent)

        self._session = session
        self._stacked_widget = stacked_widget

        # Load saved settings
        self._settings = _load_settings()

        # ── Main layout ──
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # ── Page header ──
        self._header = PageHeader("Settings", subtitle="Application configuration")
        layout.addWidget(self._header)

        # ── Tab widget ──
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs, stretch=1)

        # Build tabs
        self._build_general_tab()
        self._build_printer_tab()
        self._build_about_tab()

    # ═══════════════════════════════════════════════════════════════
    #  GENERAL TAB
    # ═══════════════════════════════════════════════════════════════

    def _build_general_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        # ── Form panel ──
        form = FormPanel("Business Information")

        # Business Name
        self._business_name_input = QLineEdit()
        self._business_name_input.setPlaceholderText("Business name")
        self._business_name_input.setFixedHeight(INPUT_HEIGHT)
        self._business_name_input.setText(self._settings.get("business_name", ""))
        form.add_row("Business Name", self._business_name_input)

        # Business Address
        self._business_address_input = QTextEdit()
        self._business_address_input.setPlaceholderText("Business address")
        self._business_address_input.setFixedHeight(72)
        self._business_address_input.setPlainText(self._settings.get("business_address", ""))
        form.add_row("Business Address", self._business_address_input)

        # Business Phone
        self._business_phone_input = QLineEdit()
        self._business_phone_input.setPlaceholderText("Business phone")
        self._business_phone_input.setFixedHeight(INPUT_HEIGHT)
        self._business_phone_input.setText(self._settings.get("business_phone", ""))
        form.add_row("Business Phone", self._business_phone_input)

        form.add_separator()

        # Thermal Paper Width
        self._thermal_width_combo = QComboBox()
        self._thermal_width_combo.addItems(["58mm", "80mm"])
        self._thermal_width_combo.setFixedHeight(INPUT_HEIGHT)
        self._thermal_width_combo.setMinimumWidth(120)
        # Set current from saved settings
        saved_width = self._settings.get("thermal_paper_width", 80)
        width_index = 0 if saved_width == 58 else 1
        self._thermal_width_combo.setCurrentIndex(width_index)
        form.add_row("Thermal Paper Width", self._thermal_width_combo)

        layout.addWidget(form)

        # ── Save button ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("btn_primary")
        save_btn.setFixedHeight(BUTTON_HEIGHT)
        save_btn.setMinimumWidth(120)
        save_btn.clicked.connect(self._save_general_settings)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

        self._tabs.addTab(tab, "General")

    def _save_general_settings(self):
        """Save general settings to the config file."""
        width_text = self._thermal_width_combo.currentText()
        thermal_width = 58 if width_text == "58mm" else 80

        self._settings["business_name"] = self._business_name_input.text().strip()
        self._settings["business_address"] = self._business_address_input.toPlainText().strip()
        self._settings["business_phone"] = self._business_phone_input.text().strip()
        self._settings["thermal_paper_width"] = thermal_width

        # Also update chars per line based on paper width
        if thermal_width == 58:
            self._settings["thermal_chars_per_line"] = RECEIPT_CHARS_58MM
        else:
            self._settings["thermal_chars_per_line"] = RECEIPT_CHARS_80MM

        if _save_settings(self._settings):
            QMessageBox.information(self, "Settings Saved", "General settings have been saved successfully.")
        else:
            QMessageBox.critical(self, "Error", "Failed to save settings.")

    # ═══════════════════════════════════════════════════════════════
    #  PRINTER TAB
    # ═══════════════════════════════════════════════════════════════

    def _build_printer_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        # ── Form panel ──
        form = FormPanel("Printer Configuration")

        # Get available printers
        printer_names = [pi.printerName() for pi in QPrinterInfo.availablePrinters()]
        printer_options = ["None"] + printer_names

        # A4 Printer
        self._a4_printer_combo = QComboBox()
        self._a4_printer_combo.addItems(printer_options)
        self._a4_printer_combo.setFixedHeight(INPUT_HEIGHT)
        self._a4_printer_combo.setMinimumWidth(200)
        # Set current from saved settings
        saved_a4 = self._settings.get("a4_printer_name", "")
        a4_index = self._a4_printer_combo.findText(saved_a4)
        if a4_index >= 0:
            self._a4_printer_combo.setCurrentIndex(a4_index)
        else:
            self._a4_printer_combo.setCurrentIndex(0)  # "None"
        form.add_row("A4 Printer", self._a4_printer_combo)

        # Thermal Printer
        self._thermal_printer_combo = QComboBox()
        self._thermal_printer_combo.addItems(printer_options)
        self._thermal_printer_combo.setFixedHeight(INPUT_HEIGHT)
        self._thermal_printer_combo.setMinimumWidth(200)
        # Set current from saved settings
        saved_thermal = self._settings.get("thermal_printer_name", "")
        thermal_index = self._thermal_printer_combo.findText(saved_thermal)
        if thermal_index >= 0:
            self._thermal_printer_combo.setCurrentIndex(thermal_index)
        else:
            self._thermal_printer_combo.setCurrentIndex(0)  # "None"
        form.add_row("Thermal Printer", self._thermal_printer_combo)

        form.add_separator()

        # Paper Width: 58mm / 80mm radio buttons
        paper_width_row = QHBoxLayout()
        paper_width_row.setSpacing(SPACING_SM)
        self._paper_58_radio = QRadioButton("58mm")
        self._paper_80_radio = QRadioButton("80mm")
        self._paper_width_group = QButtonGroup(self)
        self._paper_width_group.addButton(self._paper_58_radio)
        self._paper_width_group.addButton(self._paper_80_radio)

        saved_pw = self._settings.get("thermal_paper_width", 80)
        if saved_pw == 58:
            self._paper_58_radio.setChecked(True)
        else:
            self._paper_80_radio.setChecked(True)

        paper_width_row.addWidget(self._paper_58_radio)
        paper_width_row.addWidget(self._paper_80_radio)
        paper_width_row.addStretch()

        form.add_row("Paper Width", paper_width_row)

        # Characters Per Line
        self._chars_per_line_spin = QSpinBox()
        self._chars_per_line_spin.setRange(20, 60)
        self._chars_per_line_spin.setValue(self._settings.get("thermal_chars_per_line", RECEIPT_CHARS_80MM))
        self._chars_per_line_spin.setFixedHeight(INPUT_HEIGHT)
        self._chars_per_line_spin.setMinimumWidth(100)
        form.add_row("Chars Per Line", self._chars_per_line_spin)

        # Auto Cut
        self._auto_cut_check = QCheckBox("Auto cut after printing")
        self._auto_cut_check.setChecked(self._settings.get("thermal_auto_cut", True))
        form.add_row("Auto Cut", self._auto_cut_check)

        # Open Cash Drawer
        self._cash_drawer_check = QCheckBox("Open cash drawer after printing")
        self._cash_drawer_check.setChecked(self._settings.get("thermal_cash_drawer", False))
        form.add_row("Cash Drawer", self._cash_drawer_check)

        layout.addWidget(form)

        # ── Radio button: auto-set chars per line ──
        self._paper_58_radio.toggled.connect(self._on_paper_width_changed)
        self._paper_80_radio.toggled.connect(self._on_paper_width_changed)

        # ── Button row: Test Print + Save ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING_SM)
        btn_row.addStretch()

        test_btn = QPushButton("Test Print")
        test_btn.setObjectName("btn_secondary")
        test_btn.setFixedHeight(BUTTON_HEIGHT)
        test_btn.setMinimumWidth(120)
        test_btn.clicked.connect(self._test_print)
        btn_row.addWidget(test_btn)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("btn_primary")
        save_btn.setFixedHeight(BUTTON_HEIGHT)
        save_btn.setMinimumWidth(120)
        save_btn.clicked.connect(self._save_printer_settings)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)
        layout.addStretch()

        self._tabs.addTab(tab, "Printer")

    def _on_paper_width_changed(self, _checked: bool):
        """Auto-set characters per line based on paper width selection."""
        if self._paper_58_radio.isChecked():
            self._chars_per_line_spin.setValue(RECEIPT_CHARS_58MM)
        else:
            self._chars_per_line_spin.setValue(RECEIPT_CHARS_80MM)

    def _save_printer_settings(self):
        """Save printer settings to the config file."""
        self._settings["a4_printer_name"] = self._a4_printer_combo.currentText()
        self._settings["thermal_printer_name"] = self._thermal_printer_combo.currentText()
        self._settings["thermal_paper_width"] = 58 if self._paper_58_radio.isChecked() else 80
        self._settings["thermal_chars_per_line"] = self._chars_per_line_spin.value()
        self._settings["thermal_auto_cut"] = self._auto_cut_check.isChecked()
        self._settings["thermal_cash_drawer"] = self._cash_drawer_check.isChecked()

        if _save_settings(self._settings):
            QMessageBox.information(self, "Settings Saved", "Printer settings have been saved successfully.")
        else:
            QMessageBox.critical(self, "Error", "Failed to save printer settings.")

    def _test_print(self):
        """Print a small test receipt/text to the selected thermal printer."""
        printer_name = self._thermal_printer_combo.currentText()
        if printer_name == "None":
            # Try A4 printer instead
            printer_name = self._a4_printer_combo.currentText()
            if printer_name == "None":
                QMessageBox.warning(self, "No Printer", "Please select a printer first.")
                return

        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPrinterName(printer_name)

            # Configure for thermal if applicable
            paper_width = 58 if self._paper_58_radio.isChecked() else 80
            if paper_width == 58:
                printer.setPageSize(QPrinter.PageSize.Custom)
                printer.setPageSizeMM(
                    __import__("PyQt6.QtCore").QtCore.QSizeF(58, 100)
                )
            elif paper_width == 80:
                printer.setPageSize(QPrinter.PageSize.Custom)
                printer.setPageSizeMM(
                    __import__("PyQt6.QtCore").QtCore.QSizeF(80, 100)
                )

            from PyQt6.QtGui import QTextDocument
            doc = QTextDocument()

            business = self._business_name_input.text().strip() or APP_NAME
            chars = self._chars_per_line_spin.value()
            separator = "-" * chars

            test_text = (
                f"{separator}\n"
                f"  ** TEST PRINT **\n"
                f"{separator}\n"
                f"  {business}\n"
                f"  Printer: {printer_name}\n"
                f"  Paper Width: {paper_width}mm\n"
                f"  Chars Per Line: {chars}\n"
                f"{separator}\n"
                f"  If you can read this, your\n"
                f"  printer is configured correctly.\n"
                f"{separator}\n\n\n"
            )

            doc.setPlainText(test_text)
            doc.print(printer)

            QMessageBox.information(self, "Test Print", f"Test page sent to '{printer_name}'.")
        except Exception:
            logger.exception("Error during test print")
            QMessageBox.critical(self, "Print Error", f"Failed to print to '{printer_name}'.\nPlease check the printer connection.")

    # ═══════════════════════════════════════════════════════════════
    #  ABOUT TAB
    # ═══════════════════════════════════════════════════════════════

    def _build_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        # ── About panel ──
        about_panel = FormPanel("About")

        # App name
        name_label = QLabel(f"{APP_NAME} v{APP_VERSION}")
        name_label.setStyleSheet(
            f"font-size: {FONT_PAGE_TITLE}px; font-weight: bold; "
            f"color: {COLOR_TEXT_PRIMARY}; background: transparent; border: none;"
        )
        about_panel.add_row("Application", name_label)

        # Version
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_SECONDARY}; "
            f"background: transparent; border: none;"
        )
        about_panel.add_row("Version", version_label)

        # Description
        desc_label = QLabel("A desktop POS application for vehicle service centers")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(
            f"font-size: {FONT_BODY}px; color: {COLOR_TEXT_SECONDARY}; "
            f"background: transparent; border: none;"
        )
        about_panel.add_row("Description", desc_label)

        about_panel.add_separator()

        # Config directory
        config_label = QLabel(DATA_DIR)
        config_label.setStyleSheet(
            f"font-size: {FONT_SMALL}px; color: {COLOR_TEXT_SECONDARY}; "
            f"font-family: {FONT_MONO}; background: transparent; border: none;"
        )
        about_panel.add_row("Data Directory", config_label)

        layout.addWidget(about_panel)
        layout.addStretch()

        self._tabs.addTab(tab, "About")
