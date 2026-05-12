"""
StaffScreen — staff management page for the Vehicle Service POS.
"""

import logging

import tkinter as tk
from tkinter import ttk, messagebox

from ui.theme import (
    COLOR_APP_BG, COLOR_PANEL_BG, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_BORDER, COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR,
    COLOR_INFO, FONT_FAMILY, FONT_PAGE_TITLE, FONT_SECTION_TITLE,
    FONT_BODY, FONT_BUTTON, FONT_SMALL,
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG,
    BUTTON_HEIGHT, INPUT_HEIGHT, status_badge_colors,
)
from ui.components import PageHeader, DataTable, FormPanel, ActionBar, StatusBadge
from controllers.staff_controller import StaffController

logger = logging.getLogger(__name__)


class StaffScreen(tk.Frame):
    """Staff management screen with table, action bar, and CRUD dialogs."""

    def __init__(self, session, stacked_widget=None, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=COLOR_APP_BG)

        self._session = session
        self._stacked_widget = stacked_widget
        self._controller = StaffController()

        # ── Main layout ──
        layout = tk.Frame(self, bg=COLOR_APP_BG)
        layout.pack(fill="both", expand=True, padx=SPACING_LG, pady=SPACING_LG)

        # ── Page header ──
        self._header = PageHeader("Staff", subtitle="Manage users and permissions", parent=layout)
        self._header.add_action("Add Staff", self._on_add_staff, "btn_primary")

        # ── Data table ──
        self._table = DataTable(
            columns=[
                ("ID", 50),
                ("Name", 150),
                ("Username", 120),
                ("Role", 100),
                ("Phone", 120),
                ("Active", 60),
            ],
            parent=layout,
        )

        # ── Action bar ──
        self._action_bar = ActionBar(parent=layout)
        self._action_bar.add_button("Edit", self._on_edit_staff, "btn_secondary")
        self._action_bar.add_button("Toggle Active", self._on_toggle_active, "btn_primary")
        self._action_bar.add_button("Change Password", self._on_change_password, "btn_secondary")
        self._action_bar.add_button("Delete", self._on_delete_staff, "btn_danger")

        # ── Initial data load ──
        self.refresh()

    # ── Data loading ────────────────────────────────────────────────

    def refresh(self):
        """Reload staff list into the table."""
        staff_list = self._controller.get_all_staff()
        rows = []
        for s in staff_list:
            active_text = "Active" if s.is_active else "Inactive"
            rows.append([
                s.id,
                s.full_name or "",
                s.username or "",
                s.role or "",
                getattr(s, "phone", "") or "",
                active_text,
            ])
        self._table.load_data(rows)

    # ── Add staff ───────────────────────────────────────────────────

    def _on_add_staff(self):
        dialog = StaffDialog(parent=self)
        self.wait_window(dialog)
        if dialog.result is not None:
            data = dialog.result
            if not data["username"].strip() or not data["password"].strip() or not data["full_name"].strip():
                messagebox.showwarning("Validation Error", "Username, Password, and Full Name are required.")
                return
            result = self._controller.create_staff(
                username=data["username"].strip(),
                password=data["password"].strip(),
                full_name=data["full_name"].strip(),
                role=data["role"],
            )
            if result:
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to create staff member. Username may already exist.")

    # ── Edit staff ──────────────────────────────────────────────────

    def _on_edit_staff(self):
        row = self._table.get_selected_row()
        if row < 0:
            messagebox.showinfo("No Selection", "Please select a staff member to edit.")
            return

        staff_id = self._table.get_selected_data(0)
        if not staff_id:
            return

        staff_list = self._controller.get_all_staff()
        staff_member = None
        for s in staff_list:
            if str(s.id) == staff_id:
                staff_member = s
                break

        if not staff_member:
            messagebox.showerror("Error", "Staff member not found.")
            return

        dialog = StaffDialog(parent=self, staff=staff_member)
        self.wait_window(dialog)
        if dialog.result is not None:
            data = dialog.result
            if not data["full_name"].strip():
                messagebox.showwarning("Validation Error", "Full Name is required.")
                return

            kwargs = {
                "full_name": data["full_name"].strip(),
                "role": data["role"],
            }

            # Only update password if a new one was provided
            if data["password"].strip():
                self._controller.change_password(int(staff_id), data["password"].strip())

            result = self._controller.update_staff(int(staff_id), **kwargs)
            if result:
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to update staff member.")

    # ── Toggle active ───────────────────────────────────────────────

    def _on_toggle_active(self):
        row = self._table.get_selected_row()
        if row < 0:
            messagebox.showinfo("No Selection", "Please select a staff member.")
            return

        staff_id = self._table.get_selected_data(0)
        staff_name = self._table.get_selected_data(1)
        current_status = self._table.get_selected_data(5)
        if not staff_id:
            return

        new_status = "inactive" if current_status == "Active" else "active"
        reply = messagebox.askyesno(
            "Confirm Toggle",
            f"Are you sure you want to set '{staff_name}' as {new_status}?",
            default="no",
        )
        if reply:
            result = self._controller.toggle_active(int(staff_id))
            if result:
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to toggle staff status.")

    # ── Change password ─────────────────────────────────────────────

    def _on_change_password(self):
        row = self._table.get_selected_row()
        if row < 0:
            messagebox.showinfo("No Selection", "Please select a staff member.")
            return

        staff_id = self._table.get_selected_data(0)
        staff_name = self._table.get_selected_data(1)
        if not staff_id:
            return

        dialog = ChangePasswordDialog(staff_name=staff_name, parent=self)
        self.wait_window(dialog)
        if dialog.result is not None:
            new_password = dialog.result
            if not new_password:
                messagebox.showwarning("Validation Error", "Password cannot be empty.")
                return
            success = self._controller.change_password(int(staff_id), new_password)
            if success:
                messagebox.showinfo("Success", f"Password changed for '{staff_name}'.")
            else:
                messagebox.showerror("Error", "Failed to change password.")

    # ── Delete staff ────────────────────────────────────────────────

    def _on_delete_staff(self):
        row = self._table.get_selected_row()
        if row < 0:
            messagebox.showinfo("No Selection", "Please select a staff member to delete.")
            return

        staff_id = self._table.get_selected_data(0)
        staff_name = self._table.get_selected_data(1)
        if not staff_id:
            return

        reply = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete staff member '{staff_name}'?\n"
            "This will deactivate their account.",
            default="no",
        )
        if reply:
            result = self._controller.toggle_active(int(staff_id))
            if result:
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to delete staff member.")


# ─── Staff Dialog ──────────────────────────────────────────────────────

class StaffDialog(tk.Toplevel):
    """Dialog for creating or editing a staff member."""

    def __init__(self, parent=None, staff=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.result = None
        self._staff = staff
        self._is_edit = staff is not None

        self.title("Edit Staff" if self._is_edit else "Add Staff")
        self.configure(bg=COLOR_APP_BG)
        self.grab_set()
        self.transient(parent)
        self.minsize(480, 400)

        # ── Main layout ──
        outer = tk.Frame(self, bg=COLOR_APP_BG, padx=SPACING_LG, pady=SPACING_LG)
        outer.pack(fill="both", expand=True)

        form = FormPanel("Staff Details", parent=outer)

        # Full Name *
        self._fullname_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Full Name *", self._fullname_input)

        # Username *
        self._username_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        if self._is_edit:
            self._username_input.config(state="disabled")
        form.add_row("Username *", self._username_input)

        # Password * (required for new, optional for edit)
        self._password_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY), show="*")
        placeholder_text = "New password (leave blank to keep)" if self._is_edit else "Password *"
        form.add_row("Password *" if not self._is_edit else "Password", self._password_input)

        # Role
        self._role_combo = ttk.Combobox(
            form, values=["ADMIN", "MANAGER", "MECHANIC", "RECEPTIONIST"],
            state="readonly", width=18,
        )
        self._role_combo.set("MECHANIC")
        form.add_row("Role", self._role_combo)

        # Phone
        self._phone_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY))
        form.add_row("Phone", self._phone_input)

        # Is Active
        self._is_active_var = tk.BooleanVar(value=True)
        self._is_active_check = tk.Checkbutton(
            form, text="Active", variable=self._is_active_var,
            font=(FONT_FAMILY, FONT_SMALL), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG,
            selectcolor=COLOR_PANEL_BG, activebackground=COLOR_PANEL_BG,
        )
        form.add_row("Active", self._is_active_check)

        # ── Dialog buttons ──
        btn_frame = tk.Frame(outer, bg=COLOR_APP_BG)
        btn_frame.pack(fill="x", pady=(SPACING_MD, 0))
        tk.Frame(btn_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                    style="Secondary.TButton").pack(side="right", padx=(SPACING_SM, 0))
        save_text = "Save" if self._is_edit else "Create"
        ttk.Button(btn_frame, text=save_text, command=self._on_save,
                    style="Primary.TButton").pack(side="right")

        # ── Pre-fill for edit ──
        if self._is_edit:
            self._username_input.config(state="normal")
            self._username_input.insert(0, staff.username or "")
            self._username_input.config(state="disabled")
            self._fullname_input.insert(0, staff.full_name or "")
            # Set combo to current role
            role = staff.role or "MECHANIC"
            self._role_combo.set(role)
            self._phone_input.insert(0, getattr(staff, "phone", "") or "")
            self._is_active_var.set(staff.is_active)

        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    # ── Private ─────────────────────────────────────────────────────

    def _on_save(self):
        full_name = self._fullname_input.get().strip()
        username = self._username_input.get().strip()
        password = self._password_input.get().strip()

        if not username and not self._is_edit:
            messagebox.showwarning("Validation", "Username is required.", parent=self)
            self._username_input.focus_set()
            return
        if not self._is_edit and not password:
            messagebox.showwarning("Validation", "Password is required for new staff.", parent=self)
            self._password_input.focus_set()
            return
        if not full_name:
            messagebox.showwarning("Validation", "Full Name is required.", parent=self)
            self._fullname_input.focus_set()
            return

        self.result = {
            "username": username,
            "password": password,
            "full_name": full_name,
            "role": self._role_combo.get(),
            "phone": self._phone_input.get().strip(),
            "is_active": self._is_active_var.get(),
        }
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


# ─── Change Password Dialog ────────────────────────────────────────────

class ChangePasswordDialog(tk.Toplevel):
    """Dialog for changing a staff member's password."""

    def __init__(self, staff_name: str = "", parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.result = None
        self._staff_name = staff_name

        self.title("Change Password")
        self.configure(bg=COLOR_APP_BG)
        self.grab_set()
        self.transient(parent)
        self.minsize(420, 260)

        # ── Main layout ──
        outer = tk.Frame(self, bg=COLOR_APP_BG, padx=SPACING_LG, pady=SPACING_LG)
        outer.pack(fill="both", expand=True)

        title_text = f"Change Password — {staff_name}" if staff_name else "Change Password"
        form = FormPanel(title_text, parent=outer)

        # New Password
        self._new_password_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY), show="*")
        form.add_row("New Password *", self._new_password_input)

        # Confirm Password
        self._confirm_password_input = tk.Entry(form, font=(FONT_FAMILY, FONT_BODY), show="*")
        form.add_row("Confirm Password *", self._confirm_password_input)

        # ── Dialog buttons ──
        btn_frame = tk.Frame(outer, bg=COLOR_APP_BG)
        btn_frame.pack(fill="x", pady=(SPACING_MD, 0))
        tk.Frame(btn_frame, bg=COLOR_APP_BG).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                    style="Secondary.TButton").pack(side="right", padx=(SPACING_SM, 0))
        ttk.Button(btn_frame, text="Change Password", command=self._on_save,
                    style="Primary.TButton").pack(side="right")

        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    # ── Private ─────────────────────────────────────────────────────

    def _on_save(self):
        new_pw = self._new_password_input.get().strip()
        confirm_pw = self._confirm_password_input.get().strip()

        if not new_pw:
            messagebox.showwarning("Validation", "New password is required.", parent=self)
            self._new_password_input.focus_set()
            return

        if new_pw != confirm_pw:
            messagebox.showwarning("Validation", "Passwords do not match.", parent=self)
            self._confirm_password_input.focus_set()
            return

        if len(new_pw) < 4:
            messagebox.showwarning("Validation", "Password must be at least 4 characters.", parent=self)
            self._new_password_input.focus_set()
            return

        self.result = new_pw
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()
