"""
Centralized theme constants and ttk.Style configuration for the Vehicle Service POS.
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
FONT_FAMILY       = "Segoe UI"
FONT_FAMILY_ALT   = "Arial"
FONT_MONO         = "Consolas"
FONT_PAGE_TITLE   = 22
FONT_SECTION_TITLE = 15
FONT_BODY         = 13
FONT_TABLE        = 13
FONT_BUTTON       = 13
FONT_SMALL        = 12
FONT_GRAND_TOTAL  = 22
FONT_RECEIPT      = 11

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

# ─── Helper font tuples ────────────────────────────────────────

def font_body():
    return (FONT_FAMILY, FONT_BODY)

def font_small():
    return (FONT_FAMILY, FONT_SMALL)

def font_bold(size=FONT_BODY):
    return (FONT_FAMILY, size, "bold")

def font_page_title():
    return (FONT_FAMILY, FONT_PAGE_TITLE, "bold")

def font_section_title():
    return (FONT_FAMILY, FONT_SECTION_TITLE, "bold")

def font_button():
    return (FONT_FAMILY, FONT_BUTTON, "bold")

def font_mono():
    return (FONT_MONO, FONT_RECEIPT)


def apply_app_theme(root):
    """Configure ttk.Style for the application."""
    import tkinter as tk
    from tkinter import ttk

    style = ttk.Style(root)
    style.theme_use("clam")

    # General
    style.configure(".", background=COLOR_APP_BG, foreground=COLOR_TEXT_PRIMARY,
                     font=(FONT_FAMILY, FONT_BODY))
    style.configure("TFrame", background=COLOR_APP_BG)
    style.configure("Panel.TFrame", background=COLOR_PANEL_BG)
    style.configure("Sidebar.TFrame", background=COLOR_SIDEBAR_BG)

    # Labels
    style.configure("TLabel", background=COLOR_APP_BG, foreground=COLOR_TEXT_PRIMARY,
                     font=(FONT_FAMILY, FONT_BODY))
    style.configure("PageTitle.TLabel", font=(FONT_FAMILY, FONT_PAGE_TITLE, "bold"),
                     foreground=COLOR_TEXT_PRIMARY, background=COLOR_APP_BG)
    style.configure("SectionTitle.TLabel", font=(FONT_FAMILY, FONT_SECTION_TITLE, "bold"),
                     foreground=COLOR_TEXT_PRIMARY, background=COLOR_PANEL_BG)
    style.configure("Secondary.TLabel", font=(FONT_FAMILY, FONT_SMALL),
                     foreground=COLOR_TEXT_SECONDARY, background=COLOR_APP_BG)
    style.configure("Panel.TLabel", background=COLOR_PANEL_BG, foreground=COLOR_TEXT_PRIMARY)

    # Buttons
    style.configure("Primary.TButton", font=(FONT_FAMILY, FONT_BUTTON, "bold"),
                     background=COLOR_ACCENT, foreground="#FFFFFF", padding=(16, 8))
    style.map("Primary.TButton",
              background=[("active", COLOR_ACCENT_HOVER), ("disabled", "#B0BEC5")])

    style.configure("Secondary.TButton", font=(FONT_FAMILY, FONT_BUTTON),
                     background=COLOR_PANEL_BG, foreground=COLOR_TEXT_PRIMARY, padding=(16, 8))
    style.map("Secondary.TButton", background=[("active", COLOR_SIDEBAR_HOVER)])

    style.configure("Danger.TButton", font=(FONT_FAMILY, FONT_BUTTON, "bold"),
                     background=COLOR_BUTTON_DANGER, foreground="#FFFFFF", padding=(16, 8))
    style.map("Danger.TButton", background=[("active", COLOR_BUTTON_DANGER_HOVER)])

    style.configure("Success.TButton", font=(FONT_FAMILY, FONT_BUTTON, "bold"),
                     background=COLOR_SUCCESS, foreground="#FFFFFF", padding=(16, 8))
    style.map("Success.TButton", background=[("active", "#1B5E20")])

    # Sidebar nav buttons
    style.configure("Nav.TButton", font=(FONT_FAMILY, FONT_BODY),
                     background=COLOR_SIDEBAR_BG, foreground=COLOR_SIDEBAR_TEXT,
                     padding=(17, 10), anchor="w")
    style.map("Nav.TButton",
              background=[("active", COLOR_SIDEBAR_HOVER)],
              foreground=[("active", COLOR_SIDEBAR_TEXT)])
    style.configure("NavActive.TButton", font=(FONT_FAMILY, FONT_BODY, "bold"),
                     background=COLOR_SIDEBAR_ACTIVE, foreground=COLOR_SIDEBAR_ACTIVE_TEXT,
                     padding=(17, 10), anchor="w")

    # Entry
    style.configure("TEntry", fieldbackground=COLOR_PANEL_BG, foreground=COLOR_TEXT_PRIMARY,
                     padding=(10, 5))

    # Combobox
    style.configure("TCombobox", fieldbackground=COLOR_PANEL_BG, foreground=COLOR_TEXT_PRIMARY,
                     padding=(10, 5))

    # Treeview (tables)
    style.configure("Treeview", background=COLOR_PANEL_BG, foreground=COLOR_TEXT_PRIMARY,
                     fieldbackground=COLOR_PANEL_BG, font=(FONT_FAMILY, FONT_TABLE),
                     rowheight=TABLE_ROW_HEIGHT)
    style.configure("Treeview.Heading", background=COLOR_TABLE_HEADER_BG,
                     foreground=COLOR_TEXT_PRIMARY, font=(FONT_FAMILY, FONT_TABLE, "bold"),
                     padding=(8, 6))
    style.map("Treeview", background=[("selected", COLOR_SELECTED_ROW_BG)])

    # Scrollbar
    style.configure("TScrollbar", background="#C0C0C0", troughcolor=COLOR_APP_BG,
                     arrowcolor="#666666")

    # Notebook (tabs)
    style.configure("TNotebook", background=COLOR_APP_BG)
    style.configure("TNotebook.Tab", font=(FONT_FAMILY, FONT_BUTTON),
                     padding=(20, 8))
    style.map("TNotebook.Tab",
              background=[("selected", COLOR_PANEL_BG), ("!selected", COLOR_APP_BG)])

    # Labelframe (group boxes)
    style.configure("TLabelframe", background=COLOR_PANEL_BG, foreground=COLOR_TEXT_PRIMARY,
                     font=(FONT_FAMILY, FONT_SECTION_TITLE, "bold"))
    style.configure("TLabelframe.Label", background=COLOR_PANEL_BG,
                     foreground=COLOR_TEXT_PRIMARY, font=(FONT_FAMILY, FONT_SECTION_TITLE, "bold"))

    # Spinbox
    style.configure("TSpinbox", fieldbackground=COLOR_PANEL_BG, foreground=COLOR_TEXT_PRIMARY,
                     padding=(10, 5))

    root.configure(bg=COLOR_APP_BG)


def status_badge_colors(status: str) -> dict:
    """Return {fg, bg} colors for a status badge based on status string."""
    status_map = {
        "PENDING":     (COLOR_WARNING, COLOR_WARNING_BG),
        "IN_PROGRESS": (COLOR_INFO,    COLOR_INFO_BG),
        "COMPLETED":   (COLOR_SUCCESS, COLOR_SUCCESS_BG),
        "CANCELLED":   (COLOR_ERROR,   COLOR_ERROR_BG),
        "PAID":        (COLOR_SUCCESS, COLOR_SUCCESS_BG),
        "PARTIAL":     (COLOR_WARNING, COLOR_WARNING_BG),
        "UNPAID":      (COLOR_ERROR,   COLOR_ERROR_BG),
        "OVERDUE":     (COLOR_ERROR,   COLOR_ERROR_BG),
        "ACTIVE":      (COLOR_SUCCESS, COLOR_SUCCESS_BG),
        "INACTIVE":    (COLOR_TEXT_SECONDARY, "#E0E0E0"),
        "LOW STOCK":   (COLOR_ERROR,   COLOR_ERROR_BG),
        "IN STOCK":    (COLOR_SUCCESS, COLOR_SUCCESS_BG),
    }
    fg, bg = status_map.get(status.upper(), (COLOR_TEXT_SECONDARY, "#E0E0E0"))
    return {"fg": fg, "bg": bg}
