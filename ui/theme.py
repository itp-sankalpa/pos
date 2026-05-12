"""
Centralized theme constants and global QSS stylesheet for the Vehicle Service POS.
All UI screens must use these constants — do NOT hardcode colors/fonts/spacing.
"""

# ─── Color System ──────────────────────────────────────────────
COLOR_APP_BG           = "#F0F0F0"
COLOR_PANEL_BG         = "#FFFFFF"
COLOR_TEXT_PRIMARY      = "#222222"
COLOR_TEXT_SECONDARY    = "#666666"
COLOR_BORDER           = "#DADADA"
COLOR_TABLE_HEADER_BG  = "#E9ECEF"
COLOR_SELECTED_ROW_BG  = "#DDEBFF"
COLOR_ACCENT           = "#2F6FED"
COLOR_ACCENT_HOVER     = "#1B5CD6"
COLOR_SUCCESS          = "#2E7D32"
COLOR_SUCCESS_BG       = "#E8F5E9"
COLOR_WARNING          = "#F59E0B"
COLOR_WARNING_BG       = "#FFF8E1"
COLOR_ERROR            = "#C62828"
COLOR_ERROR_BG         = "#FFEBEE"
COLOR_INFO             = "#1565C0"
COLOR_INFO_BG          = "#E3F2FD"
COLOR_SIDEBAR_BG       = "#FFFFFF"
COLOR_SIDEBAR_ACTIVE   = "#DDEBFF"
COLOR_SIDEBAR_HOVER    = "#F5F5F5"
COLOR_SIDEBAR_TEXT     = "#333333"
COLOR_SIDEBAR_ACTIVE_TEXT = "#2F6FED"
COLOR_BUTTON_DANGER    = "#C62828"
COLOR_BUTTON_DANGER_HOVER = "#B71C1C"

# ─── Typography ────────────────────────────────────────────────
FONT_FAMILY       = "'Segoe UI', Arial, sans-serif"
FONT_MONO         = "'Consolas', 'Courier New', monospace"

FONT_PAGE_TITLE   = 22   # bold
FONT_SECTION_TITLE = 15  # bold
FONT_BODY         = 13
FONT_TABLE        = 13
FONT_BUTTON       = 13
FONT_SMALL        = 12
FONT_GRAND_TOTAL  = 22   # bold
FONT_RECEIPT      = 11   # mono

# ─── Spacing (8px grid) ───────────────────────────────────────
SPACING_XXS = 4
SPACING_XS  = 8
SPACING_SM  = 12
SPACING_MD  = 16
SPACING_LG  = 24
SPACING_XL  = 32
SPACING_XXL = 48

# ─── Layout Dimensions ────────────────────────────────────────
SIDEBAR_WIDTH       = 210
SIDEBAR_ICON_SIZE   = 20
PAGE_MARGIN         = 24
DEFAULT_WINDOW_W    = 1280
DEFAULT_WINDOW_H    = 800
MIN_WINDOW_W        = 1100
MIN_WINDOW_H        = 700

BUTTON_HEIGHT       = 34
BUTTON_PRIMARY_W    = 150
INPUT_HEIGHT        = 32
TABLE_ROW_HEIGHT    = 32
TABLE_HEADER_HEIGHT = 36

# ─── Receipt Dimensions ────────────────────────────────────────
RECEIPT_CHARS_80MM  = 48
RECEIPT_CHARS_58MM  = 32

# ─── Global QSS Stylesheet ────────────────────────────────────
GLOBAL_STYLESHEET = f"""
/* ── Application ── */
QMainWindow, QWidget {{
    background-color: {COLOR_APP_BG};
    color: {COLOR_TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
    font-size: {FONT_BODY}px;
}}

/* ── Panels / Frames ── */
QFrame#panel {{
    background-color: {COLOR_PANEL_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
}}

/* ── Labels ── */
QLabel {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: {FONT_BODY}px;
}}
QLabel#page_title {{
    font-size: {FONT_PAGE_TITLE}px;
    font-weight: bold;
    color: {COLOR_TEXT_PRIMARY};
}}
QLabel#section_title {{
    font-size: {FONT_SECTION_TITLE}px;
    font-weight: bold;
    color: {COLOR_TEXT_PRIMARY};
}}
QLabel#secondary {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_SMALL}px;
}}
QLabel#grand_total {{
    font-size: {FONT_GRAND_TOTAL}px;
    font-weight: bold;
    color: {COLOR_TEXT_PRIMARY};
}}

/* ── Buttons ── */
QPushButton {{
    background-color: {COLOR_ACCENT};
    color: #FFFFFF;
    border: none;
    border-radius: 5px;
    padding: 6px 16px;
    min-height: {BUTTON_HEIGHT}px;
    font-size: {FONT_BUTTON}px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}
QPushButton:pressed {{
    background-color: #1449B8;
}}
QPushButton:disabled {{
    background-color: #B0BEC5;
    color: #ECEFF1;
}}
QPushButton#btn_secondary {{
    background-color: {COLOR_PANEL_BG};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
}}
QPushButton#btn_secondary:hover {{
    background-color: {COLOR_SIDEBAR_HOVER};
    border-color: {COLOR_ACCENT};
}}
QPushButton#btn_danger {{
    background-color: {COLOR_BUTTON_DANGER};
    color: #FFFFFF;
}}
QPushButton#btn_danger:hover {{
    background-color: {COLOR_BUTTON_DANGER_HOVER};
}}
QPushButton#btn_success {{
    background-color: {COLOR_SUCCESS};
    color: #FFFFFF;
}}
QPushButton#btn_success:hover {{
    background-color: #1B5E20;
}}
QPushButton#btn_warning {{
    background-color: {COLOR_WARNING};
    color: #FFFFFF;
}}
QPushButton#btn_warning:hover {{
    background-color: #D97706;
}}

/* ── Line Edits ── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 5px 10px;
    min-height: {INPUT_HEIGHT}px;
    background-color: {COLOR_PANEL_BG};
    font-size: {FONT_BODY}px;
    color: {COLOR_TEXT_PRIMARY};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {COLOR_ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_PANEL_BG};
    border: 1px solid {COLOR_BORDER};
    selection-background-color: {COLOR_SELECTED_ROW_BG};
}}

/* ── Tables ── */
QTableView, QTableWidget {{
    background-color: {COLOR_PANEL_BG};
    alternate-background-color: #F8F9FA;
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    gridline-color: {COLOR_BORDER};
    selection-background-color: {COLOR_SELECTED_ROW_BG};
    selection-color: {COLOR_TEXT_PRIMARY};
    font-size: {FONT_TABLE}px;
    outline: none;
}}
QTableView::item, QTableWidget::item {{
    padding: 4px 8px;
    min-height: {TABLE_ROW_HEIGHT}px;
}}
QHeaderView::section {{
    background-color: {COLOR_TABLE_HEADER_BG};
    color: {COLOR_TEXT_PRIMARY};
    font-weight: bold;
    font-size: {FONT_TABLE}px;
    padding: 6px 8px;
    min-height: {TABLE_HEADER_HEIGHT}px;
    border: none;
    border-bottom: 2px solid {COLOR_BORDER};
}}
QTableWidget QTableCornerButton::section {{
    background-color: {COLOR_TABLE_HEADER_BG};
    border: none;
}}

/* ── Scroll Bars ── */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #C0C0C0;
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #A0A0A0;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: #C0C0C0;
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: #A0A0A0;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ── Tabs ── */
QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    background-color: {COLOR_PANEL_BG};
}}
QTabBar::tab {{
    background-color: {COLOR_APP_BG};
    border: 1px solid {COLOR_BORDER};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 20px;
    min-height: 28px;
    font-size: {FONT_BUTTON}px;
}}
QTabBar::tab:selected {{
    background-color: {COLOR_PANEL_BG};
    font-weight: bold;
}}
QTabBar::tab:hover {{
    background-color: {COLOR_SIDEBAR_HOVER};
}}

/* ── Group Boxes ── */
QGroupBox {{
    font-weight: bold;
    font-size: {FONT_SECTION_TITLE}px;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 18px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {COLOR_TEXT_PRIMARY};
}}

/* ── Dialogs ── */
QDialog {{
    background-color: {COLOR_APP_BG};
}}

/* ── Text Edit ── */
QTextEdit, QPlainTextEdit {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 6px 10px;
    background-color: {COLOR_PANEL_BG};
    font-size: {FONT_BODY}px;
    color: {COLOR_TEXT_PRIMARY};
}}
QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLOR_ACCENT};
}}

/* ── CheckBox ── */
QCheckBox {{
    spacing: 8px;
    font-size: {FONT_BODY}px;
    color: {COLOR_TEXT_PRIMARY};
}}

/* ── Date Edit ── */
QDateEdit {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 5px 10px;
    min-height: {INPUT_HEIGHT}px;
    background-color: {COLOR_PANEL_BG};
    font-size: {FONT_BODY}px;
}}
QDateEdit:focus {{
    border-color: {COLOR_ACCENT};
}}

/* ── Menu ── */
QMenu {{
    background-color: {COLOR_PANEL_BG};
    border: 1px solid {COLOR_BORDER};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px;
    font-size: {FONT_BODY}px;
}}
QMenu::item:selected {{
    background-color: {COLOR_SELECTED_ROW_BG};
}}

/* ── Tooltips ── */
QToolTip {{
    background-color: {COLOR_TEXT_PRIMARY};
    color: {COLOR_PANEL_BG};
    border: none;
    padding: 4px 8px;
    font-size: {FONT_SMALL}px;
}}

/* ── Splitter ── */
QSplitter::handle {{
    background-color: {COLOR_BORDER};
}}
"""


def apply_app_theme(app):
    """Apply the global stylesheet to the QApplication instance."""
    app.setStyleSheet(GLOBAL_STYLESHEET)


def status_badge_qss(status: str) -> str:
    """Return inline QSS for a status badge label based on status string."""
    status_colors = {
        "PENDING":    (COLOR_WARNING, COLOR_WARNING_BG),
        "IN_PROGRESS": (COLOR_INFO, COLOR_INFO_BG),
        "COMPLETED":  (COLOR_SUCCESS, COLOR_SUCCESS_BG),
        "CANCELLED":  (COLOR_ERROR, COLOR_ERROR_BG),
        "PAID":       (COLOR_SUCCESS, COLOR_SUCCESS_BG),
        "PARTIAL":    (COLOR_WARNING, COLOR_WARNING_BG),
        "UNPAID":     (COLOR_ERROR, COLOR_ERROR_BG),
        "OVERDUE":    (COLOR_ERROR, COLOR_ERROR_BG),
        "ACTIVE":     (COLOR_SUCCESS, COLOR_SUCCESS_BG),
        "INACTIVE":   (COLOR_TEXT_SECONDARY, "#E0E0E0"),
        "LOW STOCK":  (COLOR_ERROR, COLOR_ERROR_BG),
        "IN STOCK":   (COLOR_SUCCESS, COLOR_SUCCESS_BG),
    }
    text_color, bg_color = status_colors.get(
        status.upper(), (COLOR_TEXT_SECONDARY, "#E0E0E0")
    )
    return (
        f"color: {text_color}; background-color: {bg_color}; "
        f"padding: 3px 10px; border-radius: 10px; "
        f"font-weight: bold; font-size: {FONT_SMALL}px;"
    )
