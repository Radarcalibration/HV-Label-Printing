from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from pymongo.errors import PyMongoError

from common.auth.session import Session
from models.hv.gui.admin_settings_dialog import open_admin_settings
from models.hv.gui.auth_dialog import open_login_dialog
from models.hv.session.scan_log import load_unacknowledged_issues


class AuthBar(ttk.Frame):

    def __init__(
        self,
        parent: ttk.Frame,
        session: Session,
        on_auth_change: Callable[[], None],
    ) -> None:
        super().__init__(parent)
        self.session = session
        self._on_auth_change = on_auth_change
        self._notified_this_session = False

        self.status_var = tk.StringVar()
        self._status_label = ttk.Label(self, textvariable=self.status_var, font=("Segoe UI", 9))
        self._status_label.pack(side=tk.RIGHT, padx=(0, 10))

        self._logout_btn = ttk.Button(self, text="Logout", command=self._logout)
        self._settings_btn = ttk.Button(self, text="Settings", command=self._open_admin_settings)
        self._login_btn = ttk.Button(self, text="Login", command=self._open_login)

        self.refresh()

    def refresh(self) -> None:
        for widget in (self._login_btn, self._settings_btn, self._logout_btn):
            widget.pack_forget()

        if self.session.username is not None:
            self.status_var.set(f"{self.session.role_label}: {self.session.username}")
            self._logout_btn.pack(side=tk.RIGHT)
            if self.session.is_main_admin:
                self._settings_btn.pack(side=tk.RIGHT, padx=(0, 8))
                self._maybe_notify_unacknowledged()
        else:
            self.status_var.set("User")
            self._login_btn.pack(side=tk.RIGHT, padx=(8, 0))

    def _maybe_notify_unacknowledged(self) -> None:
        # One popup per login, not one per screen switch/rebuild.
        if self._notified_this_session:
            return
        self._notified_this_session = True
        try:
            count = len(load_unacknowledged_issues())
        except PyMongoError as exc:
            from tkinter import messagebox
            messagebox.showerror(
                "MongoDB Sync",
                f"Could not load issue notifications:\n{exc}",
                parent=self.winfo_toplevel(),
            )
            return
        if count:
            from tkinter import messagebox
            plural = "entry" if count == 1 else "entries"
            messagebox.showinfo(
                "Unacknowledged issues",
                f"{count} unacknowledged issue {plural}.\n\n",
                parent=self.winfo_toplevel(),
            )

    def _open_login(self) -> None:
        open_login_dialog(self.winfo_toplevel(), self._handle_login)

    def _open_admin_settings(self) -> None:
        if self.session.username is not None:
            open_admin_settings(
                self.winfo_toplevel(),
                current_user=self.session.username,
                excel_password=self.session.excel_password,
            )

    def _handle_login(self, username: str, password: str, role: str) -> bool:
        try:
            self.session.login(username, password, role)
        except (PyMongoError, RuntimeError, ValueError) as exc:
            from tkinter import messagebox
            messagebox.showerror(
                "Login Session",
                f"Could not record the login session in MongoDB:\n{exc}",
                parent=self.winfo_toplevel(),
            )
            return False
        self._notified_this_session = False
        self.refresh()
        self._on_auth_change()
        return True

    def _logout(self) -> None:
        try:
            self.session.logout()
        except (PyMongoError, RuntimeError, ValueError) as exc:
            from tkinter import messagebox
            messagebox.showerror(
                "Logout Session",
                f"Could not record the logout in MongoDB:\n{exc}",
                parent=self.winfo_toplevel(),
            )
            return
        self._notified_this_session = False
        self.refresh()
        self._on_auth_change()