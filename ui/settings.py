"""
SettingsScreen — application configuration for the Vehicle Service POS.
"""

import json
import logging
import os

import tkinter as tk
from tkinter import ttk, messagebox

from ui.theme import (
    COLOR_APP_BG, COLOR_PANEL_BG, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_BORDER, COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR,
    COLOR_INFO, COLOR_SIDEBAR_BG, COLOR_SIDEBAR_TEXT,
    FONT_FAMILY, FONT_PAGE_TITLE, FONT_SECTION_TITLE, FONT_BODY,
    FONT_BUTTON, FONT_SMALL, FONT_MONO,
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG,
    BUTTON_HEIGHT, INPUT_HEIGHT,
)
from ui.components import PageHeader, FormPanel
from config import (
    APP_NAME, APP_VERSION, DATA_DIR, PRINTER_SETTINGS,
    RECEIPT_CHARS_80MM, RECEIPT_CHARS_58MM,
)

logger = logging.getLogger(__name__)

# ─── Settings file path ────────────────────────────────────────────────
SETTINGS_FILE = os.path.join(DATA_DIR, "app_settings.json")


def _load_settings() -> dict:
    """Load settings from the JSON config file, returning defaults if missing."""
    defaults = {
        "business_name": "",
        "business_address": "",
        "business_phone": "",
        "invoice_prefix": "INV",
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


class SettingsScreen(tk.Frame):
    """Settings screen with Invoice Settings, Printer Settings, and Database Backup sections."""

    def __init__(self, session, stacked_widget=None, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=COLOR_APP_BG)

        self._session = session
        self._stacked_widget = stacked_widget

        # Load saved settings
        self._settings = _load_settings()

        # ── Main layout ──
        layout = tk.Frame(self, bg=COLOR_APP_BG)
        layout.pack(fill="both", expand=True, padx=SPACING_LG, pady=SPACING_LG)

        # ── Page header ──
        self._header = PageHeader("Settings", subtitle="Application configuration", parent=layout)

        # ── Scrollable content ──
        canvas = tk.Canvas(layout, bg=COLOR_APP_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(layout, orient="vertical", command=canvas.yview)
        self._scroll_frame = tk.Frame(canvas, bg=COLOR_APP_BG)

        self._scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Build sections
        self._build_invoice_section()
        self._build_printer_section()
        self._build_backup_section()
        self._build_about_section()

        # ── Save All button ──
        btn_frame = tk.Frame(self._scroll_frame, bg=COLOR_APP_BG)
        btn_frame.pack(fill="x", pady=SPACING_LG)
        tk.Frame(btn_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_frame, text="Save All Settings", command=self._save_all_settings,
                    style="Primary.TButton").pack(side="right")

    # ═══════════════════════════════════════════════════════════════
    #  INVOICE SETTINGS
    # ═══════════════════════════════════════════════════════════════

    def _build_invoice_section(self):
        section = tk.LabelFrame(
            self._scroll_frame, text=" Invoice Settings ",
            font=(FONT_FAMILY, FONT_SECTION_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
            padx=SPACING_MD, pady=SPACING_MD,
        )
        section.pack(fill="x", pady=(0, SPACING_MD))

        form = FormPanel("Business Information", parent=section)

        # Business Name
        self._business_name_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        self._business_name_input.insert(0, self._settings.get("business_name", ""))
        form.add_row("Business Name", self._business_name_input)

        # Business Address
        self._business_address_input = tk.Text(form, font=(FONT_FAMILY, FONT_BODY), height=3, wrap="word")
        self._business_address_input.insert("1.0", self._settings.get("business_address", ""))
        form.add_row("Business Address", self._business_address_input)

        # Business Phone
        self._business_phone_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        self._business_phone_input.insert(0, self._settings.get("business_phone", ""))
        form.add_row("Business Phone", self._business_phone_input)

        form.add_separator()

        # Invoice Prefix
        self._invoice_prefix_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        self._invoice_prefix_input.insert(0, self._settings.get("invoice_prefix", "INV"))
        form.add_row("Invoice Prefix", self._invoice_prefix_input)

        # Save section button
        btn_row = tk.Frame(section, bg=COLOR_PANEL_BG)
        btn_row.pack(fill="x", pady=(SPACING_SM, 0))
        ttk.Button(btn_row, text="Save Invoice Settings", command=self._save_invoice_settings,
                    style="Primary.TButton").pack(side="right")

    def _save_invoice_settings(self):
        self._settings["business_name"] = self._business_name_input.get().strip()
        self._settings["business_address"] = self._business_address_input.get("1.0", "end-1c").strip()
        self._settings["business_phone"] = self._business_phone_input.get().strip()
        self._settings["invoice_prefix"] = self._invoice_prefix_input.get().strip() or "INV"

        if _save_settings(self._settings):
            messagebox.showinfo("Settings Saved", "Invoice settings have been saved successfully.")
        else:
            messagebox.showerror("Error", "Failed to save settings.")

    # ═══════════════════════════════════════════════════════════════
    #  PRINTER SETTINGS
    # ═══════════════════════════════════════════════════════════════

    def _build_printer_section(self):
        section = tk.LabelFrame(
            self._scroll_frame, text=" Printer Settings ",
            font=(FONT_FAMILY, FONT_SECTION_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
            padx=SPACING_MD, pady=SPACING_MD,
        )
        section.pack(fill="x", pady=(0, SPACING_MD))

        form = FormPanel("Printer Configuration", parent=section)

        # A4 Printer Name
        self._a4_printer_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        self._a4_printer_input.insert(0, self._settings.get("a4_printer_name", ""))
        form.add_row("A4 Printer Name", self._a4_printer_input)

        # Thermal Printer Name
        self._thermal_printer_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        self._thermal_printer_input.insert(0, self._settings.get("thermal_printer_name", ""))
        form.add_row("Thermal Printer Name", self._thermal_printer_input)

        form.add_separator()

        # Paper Width: 58mm / 80mm
        width_frame = tk.Frame(form, bg=COLOR_PANEL_BG)
        self._paper_width_var = tk.IntVar(value=self._settings.get("thermal_paper_width", 80))
        tk.Radiobutton(
            width_frame, text="58mm", variable=self._paper_width_var, value=58,
            font=(FONT_FAMILY, FONT_SMALL), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
            selectcolor=COLOR_PANEL_BG, activebackground=COLOR_PANEL_BG,
            command=self._on_paper_width_changed,
        ).pack(side="left", padx=(0, SPACING_MD))
        tk.Radiobutton(
            width_frame, text="80mm", variable=self._paper_width_var, value=80,
            font=(FONT_FAMILY, FONT_SMALL), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
            selectcolor=COLOR_PANEL_BG, activebackground=COLOR_PANEL_BG,
            command=self._on_paper_width_changed,
        ).pack(side="left")
        form.add_row("Paper Width", width_frame)

        # Characters Per Line
        self._chars_per_line_var = tk.IntVar(
            value=self._settings.get("thermal_chars_per_line", RECEIPT_CHARS_80MM)
        )
        self._chars_per_line_spin = ttk.Spinbox(
            form, from_=20, to=60, textvariable=self._chars_per_line_var, width=8,
        )
        form.add_row("Chars Per Line", self._chars_per_line_spin)

        # Auto Cut
        self._auto_cut_var = tk.BooleanVar(value=self._settings.get("thermal_auto_cut", True))
        self._auto_cut_check = tk.Checkbutton(
            form, text="Auto cut after printing", variable=self._auto_cut_var,
            font=(FONT_FAMILY, FONT_SMALL), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
            selectcolor=COLOR_PANEL_BG, activebackground=COLOR_PANEL_BG,
        )
        form.add_row("Auto Cut", self._auto_cut_check)

        # Open Cash Drawer
        self._cash_drawer_var = tk.BooleanVar(value=self._settings.get("thermal_cash_drawer", False))
        self._cash_drawer_check = tk.Checkbutton(
            form, text="Open cash drawer after printing", variable=self._cash_drawer_var,
            font=(FONT_FAMILY, FONT_SMALL), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
            selectcolor=COLOR_PANEL_BG, activebackground=COLOR_PANEL_BG,
        )
        form.add_row("Cash Drawer", self._cash_drawer_check)

        # Save section button
        btn_row = tk.Frame(section, bg=COLOR_PANEL_BG)
        btn_row.pack(fill="x", pady=(SPACING_SM, 0))
        ttk.Button(btn_row, text="Save Printer Settings", command=self._save_printer_settings,
                    style="Primary.TButton").pack(side="right")

    def _on_paper_width_changed(self):
        """Auto-set characters per line based on paper width selection."""
        if self._paper_width_var.get() == 58:
            self._chars_per_line_var.set(RECEIPT_CHARS_58MM)
        else:
            self._chars_per_line_var.set(RECEIPT_CHARS_80MM)

    def _save_printer_settings(self):
        self._settings["a4_printer_name"] = self._a4_printer_input.get().strip()
        self._settings["thermal_printer_name"] = self._thermal_printer_input.get().strip()
        self._settings["thermal_paper_width"] = self._paper_width_var.get()
        self._settings["thermal_chars_per_line"] = self._chars_per_line_var.get()
        self._settings["thermal_auto_cut"] = self._auto_cut_var.get()
        self._settings["thermal_cash_drawer"] = self._cash_drawer_var.get()

        if _save_settings(self._settings):
            messagebox.showinfo("Settings Saved", "Printer settings have been saved successfully.")
        else:
            messagebox.showerror("Error", "Failed to save printer settings.")

    # ═══════════════════════════════════════════════════════════════
    #  DATABASE BACKUP
    # ═══════════════════════════════════════════════════════════════

    def _build_backup_section(self):
        section = tk.LabelFrame(
            self._scroll_frame, text=" Database Backup ",
            font=(FONT_FAMILY, FONT_SECTION_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
            padx=SPACING_MD, pady=SPACING_MD,
        )
        section.pack(fill="x", pady=(0, SPACING_MD))

        form = FormPanel("Backup & Restore", parent=section)

        # Database path display
        from config import DB_PATH
        db_path_label = tk.Label(
            form, text=DB_PATH, font=(FONT_FAMILY, FONT_SMALL),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, anchor="w",
        )
        form.add_row("Database Path", db_path_label)

        # Data directory display
        data_dir_label = tk.Label(
            form, text=DATA_DIR, font=(FONT_FAMILY, FONT_SMALL),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, anchor="w",
        )
        form.add_row("Data Directory", data_dir_label)

        form.add_separator()

        # Backup button row
        backup_row = tk.Frame(section, bg=COLOR_PANEL_BG)
        backup_row.pack(fill="x", pady=(SPACING_SM, 0))

        ttk.Button(
            backup_row, text="Backup Database", command=self._on_backup,
            style="Secondary.TButton",
        ).pack(side="right", padx=(SPACING_SM, 0))

        self._backup_status_label = tk.Label(
            backup_row, text="", font=(FONT_FAMILY, FONT_SMALL),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG,
        )
        self._backup_status_label.pack(side="right")

    def _on_backup(self):
        """Create a backup copy of the SQLite database."""
        import shutil
        from datetime import datetime

        from config import DB_PATH

        if not os.path.exists(DB_PATH):
            messagebox.showwarning("No Database", "Database file not found.", parent=self)
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"vehicle_pos_backup_{timestamp}.db"

        backup_path = tk.filedialog.asksaveasfilename(
            defaultextension=".db",
            initialfile=default_name,
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
            title="Save Database Backup",
        )

        if not backup_path:
            return

        try:
            shutil.copy2(DB_PATH, backup_path)
            self._backup_status_label.config(
                text=f"Backup saved: {os.path.basename(backup_path)}",
                fg=COLOR_SUCCESS,
            )
            messagebox.showinfo("Backup Complete", f"Database backed up to:\n{backup_path}")
        except Exception:
            logger.exception("Error backing up database")
            self._backup_status_label.config(text="Backup failed!", fg=COLOR_ERROR)
            messagebox.showerror("Backup Error", "Failed to create database backup.")

    # ═══════════════════════════════════════════════════════════════
    #  ABOUT SECTION
    # ═══════════════════════════════════════════════════════════════

    def _build_about_section(self):
        section = tk.LabelFrame(
            self._scroll_frame, text=" About ",
            font=(FONT_FAMILY, FONT_SECTION_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
            padx=SPACING_MD, pady=SPACING_MD,
        )
        section.pack(fill="x", pady=(0, SPACING_MD))

        form = FormPanel("Application Info", parent=section)

        # App name
        name_label = tk.Label(
            form, text=f"{APP_NAME} v{APP_VERSION}",
            font=(FONT_FAMILY, FONT_PAGE_TITLE, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, anchor="w",
        )
        form.add_row("Application", name_label)

        # Version
        version_label = tk.Label(
            form, text=f"v{APP_VERSION}",
            font=(FONT_FAMILY, FONT_BODY),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, anchor="w",
        )
        form.add_row("Version", version_label)

        # Description
        desc_label = tk.Label(
            form, text="A desktop POS application for vehicle service centers",
            font=(FONT_FAMILY, FONT_BODY),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, anchor="w", wraplength=400,
        )
        form.add_row("Description", desc_label)

        form.add_separator()

        # Config directory
        config_label = tk.Label(
            form, text=DATA_DIR,
            font=(FONT_MONO, FONT_SMALL),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, anchor="w",
        )
        form.add_row("Data Directory", config_label)

    # ═══════════════════════════════════════════════════════════════
    #  SAVE ALL
    # ═══════════════════════════════════════════════════════════════

    def _save_all_settings(self):
        """Collect all form values and save them at once."""
        self._settings["business_name"] = self._business_name_input.get().strip()
        self._settings["business_address"] = self._business_address_input.get("1.0", "end-1c").strip()
        self._settings["business_phone"] = self._business_phone_input.get().strip()
        self._settings["invoice_prefix"] = self._invoice_prefix_input.get().strip() or "INV"
        self._settings["a4_printer_name"] = self._a4_printer_input.get().strip()
        self._settings["thermal_printer_name"] = self._thermal_printer_input.get().strip()
        self._settings["thermal_paper_width"] = self._paper_width_var.get()
        self._settings["thermal_chars_per_line"] = self._chars_per_line_var.get()
        self._settings["thermal_auto_cut"] = self._auto_cut_var.get()
        self._settings["thermal_cash_drawer"] = self._cash_drawer_var.get()

        if _save_settings(self._settings):
            messagebox.showinfo("Settings Saved", "All settings have been saved successfully.")
        else:
            messagebox.showerror("Error", "Failed to save settings.")
