 

import tkinter as tk
from tkinter import messagebox, ttk

from api.Client import get_api_urls, is_valid_api_url, save_api_urls
from models.hv.gui.auth_dialog import ManageUsersFrame


class AdminSettingsDialog(tk.Toplevel):

    def __init__(self, parent: tk.Misc, *, current_user: str) -> None:
        super().__init__(parent)
        self.title("Admin Settings")
        self.geometry("1200x600")
        self.minsize(900, 460)
        self.transient(parent.winfo_toplevel())

        self._current_user = current_user

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        manage_tab = ttk.Frame(notebook)
        api_urls_tab = ttk.Frame(notebook)

        notebook.add(manage_tab, text="Manage Users")
        notebook.add(api_urls_tab, text="API URLs")

        self._build_manage_tab(manage_tab)
        self._build_api_urls_tab(api_urls_tab)

    # ── Manage Users tab 
    def _build_manage_tab(self, parent: ttk.Frame) -> None:
        ManageUsersFrame(parent, self._current_user).pack()

    def _build_api_urls_tab(self, parent: ttk.Frame) -> None:
        urls = get_api_urls()
        form = ttk.Frame(parent, padding=(12, 16))
        form.pack(fill=tk.X, anchor=tk.N)
        form.columnconfigure(1, weight=1)

        self._dummy_api_url_var = tk.StringVar(value=urls["dummy_api_url"])
        self._pack_id_api_url_var = tk.StringVar(value=urls["pack_id_api_url"])
        self._bms_api_url_var = tk.StringVar(value=urls["bms_api_url"])

        ttk.Label(form, text="Dummy API URL:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10), pady=6
        )
        ttk.Entry(form, textvariable=self._dummy_api_url_var).grid(
            row=0, column=1, sticky=tk.EW, pady=6
        )
        ttk.Label(form, text="Pack ID API URL:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 10), pady=6
        )
        ttk.Entry(form, textvariable=self._pack_id_api_url_var).grid(
            row=1, column=1, sticky=tk.EW, pady=6
        )
        ttk.Label(form, text="BMS API URL:").grid(
            row=2, column=0, sticky=tk.W, padx=(0, 10), pady=6
        )
        ttk.Entry(form, textvariable=self._bms_api_url_var).grid(
            row=2, column=1, sticky=tk.EW, pady=6
        )
        ttk.Button(form, text="Save", command=self.save_api_urls_button).grid(
            row=3, column=1, sticky=tk.E, pady=(10, 0)
        )

    def save_api_urls_button(self) -> None:
        dummy_url = self._dummy_api_url_var.get().strip()
        pack_id_url = self._pack_id_api_url_var.get().strip()
        bms_url = self._bms_api_url_var.get().strip()
        if not all(map(is_valid_api_url, (dummy_url, pack_id_url, bms_url))):
            messagebox.showerror(
                "Invalid API URL",
                "Enter a valid URL beginning with http:// or https:// for all endpoints.",
                parent=self,
            )
            return

        try:
            save_api_urls(dummy_url, pack_id_url, bms_url)
        except Exception as exc:
            messagebox.showerror(
                "Save error", f"Could not save API URLs:\n{exc}", parent=self
            )
            return
        messagebox.showinfo(
            "API URLs saved", "The API endpoints have been updated.", parent=self
        )


def open_admin_settings(parent: tk.Misc, *, current_user: str) -> None:
    AdminSettingsDialog(parent, current_user=current_user)