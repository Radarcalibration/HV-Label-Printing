import tkinter as tk
from tkinter import messagebox, ttk
from requests.exceptions import RequestException

from api.Client import (
    get_api_keys,
    get_api_call_settings,
    get_api_urls,
    is_valid_api_key,
    is_valid_api_url,
    save_api_keys,
    save_api_urls,
    save_machine_details,
    set_api_call_enabled,
    get_machine_details,
    validate_api_key,
)
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
        notebook.add(api_urls_tab, text="API Settings")

        self._build_manage_tab(manage_tab)
        self._build_api_urls_keys_tab(api_urls_tab)

    # ── Manage Users tab 
    def _build_manage_tab(self, parent: ttk.Frame) -> None:
        ManageUsersFrame(parent, self._current_user).pack()

    def _build_api_urls_keys_tab(self, parent: ttk.Frame) -> None:
        urls = get_api_urls()
        form = ttk.Frame(parent, padding=(12, 16))
        form.pack(fill=tk.X, anchor=tk.N)
        form.columnconfigure(1, weight=1)

        keys = get_api_keys()
        call_settings = get_api_call_settings()

        self._dummy_api_url_var = tk.StringVar(value=urls["dummy_api_url"])
        self._pack_id_api_url_var = tk.StringVar(value=urls["pack_id_api_url"])
        self._bms_api_url_var = tk.StringVar(value=urls["bms_api_url"])

        self._dummy_api_key_var = tk.StringVar(value=keys["dummy_api_key"])
        self._pack_id_api_key_var = tk.StringVar(value=keys["pack_id_api_key"])
        self._bms_api_key_var = tk.StringVar(value=keys["bms_api_key"])
        self._api_call_vars = {
            endpoint: tk.BooleanVar(value=enabled)
            for endpoint, enabled in call_settings.items()
        }

        machine = get_machine_details()

        self._machine_name = tk.StringVar(value=machine["machine_name"])
        self._machine_id = tk.StringVar(value=machine["machine_id"])

        ttk.Label(form,text="Machine Name:").grid(row=5, column=0, sticky=tk.W, padx=(0, 10), pady=6)
        ttk.Entry(form,textvariable=self._machine_name).grid(row=5, column=1, sticky=tk.EW, pady=6)

        ttk.Label(form,text="Machine ID:").grid(row=5, column=2, sticky=tk.W, padx=(0, 10), pady=6)
        ttk.Entry(form,textvariable=self._machine_id).grid(row=5, column=3, sticky=tk.EW, pady=6)

        ttk.Label(form,text="Dummy API URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=6)
        ttk.Entry(form,textvariable=self._dummy_api_url_var).grid(row=0, column=1, sticky=tk.EW, pady=6)

        ttk.Label(form,text="Dummy API KEY:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10), pady=6)
        ttk.Entry(form,textvariable=self._dummy_api_key_var,show="*").grid(row=0, column=3, sticky=tk.EW, pady=6)

        ttk.Checkbutton(
            form,
            text="Enable server call",
            variable=self._api_call_vars["dummy"],
            command=lambda: self._save_api_call_setting("dummy"),
        ).grid(row=0, column=4, sticky=tk.W, padx=(10, 0), pady=6)

        ttk.Label(form,text="Pack ID API URL:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=6)
        ttk.Entry(form,textvariable=self._pack_id_api_url_var).grid(row=1, column=1, sticky=tk.EW, pady=6)

        ttk.Label(form,text="Pack ID API KEY:").grid(row=1, column=2, sticky=tk.W, padx=(0, 10), pady=6)
        ttk.Entry(form,textvariable=self._pack_id_api_key_var,show="*").grid(row=1, column=3, sticky=tk.EW, pady=6)

        ttk.Checkbutton(
            form,
            text="Enable server call",
            variable=self._api_call_vars["pack_id"],
            command=lambda: self._save_api_call_setting("pack_id"),
        ).grid(row=1, column=4, sticky=tk.W, padx=(10, 0), pady=6)

        ttk.Label(form,text="BMS API URL:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=6)
        ttk.Entry(form,textvariable=self._bms_api_url_var).grid(row=2, column=1, sticky=tk.EW, pady=6)

        ttk.Label(form,text="BMS API KEY:").grid(row=2, column=2, sticky=tk.W, padx=(0, 10), pady=6)
        ttk.Entry(form,textvariable=self._bms_api_key_var,show="*").grid(row=2, column=3, sticky=tk.EW, pady=6)

        ttk.Checkbutton(
            form,
            text="Enable server call",
            variable=self._api_call_vars["bms"],
            command=lambda: self._save_api_call_setting("bms"),
        ).grid(row=2, column=4, sticky=tk.W, padx=(10, 0), pady=6)

        self._status_label = ttk.Label(form,text="Pending",foreground="red")
        self._status_label.grid(row=10,column=0,columnspan=2,sticky=tk.W,pady=(10, 0))

        ttk.Button(form,text="Save",command=self.save_all_settings,).grid(row=10,column=4,sticky=tk.E,pady=(10, 0))

    def save_all_settings(self) -> None:
        if not self.save_api_urls_button():
            self._status_label.config(text="Pending", foreground="red")
            return
        if not self.save_api_keys_button():
            self._status_label.config(text="Pending", foreground="red")
            return
        if not self.save_machine_details_button():
            self._status_label.config(text="Pending",foreground="red")
            return

        self._status_label.config(text="All Parameters Saved",foreground="green")

        messagebox.showinfo("Success","All parameters have been saved successfully.",parent=self)

    def save_machine_details_button(self) -> bool:
        try:
            save_machine_details(
                self._machine_name.get(),
                self._machine_id.get(),
            )
            return True

        except Exception as exc:
            messagebox.showerror("Save error",f"Could not save machine details:\n{exc}",parent=self)
            return False

    def _save_api_call_setting(self, endpoint: str) -> None:
        set_api_call_enabled(endpoint,self._api_call_vars[endpoint].get())

    def save_api_urls_button(self) -> bool:

        dummy_url = self._dummy_api_url_var.get().strip()
        pack_id_url = self._pack_id_api_url_var.get().strip()
        bms_url = self._bms_api_url_var.get().strip()

        if not all(
            map(
                is_valid_api_url,
                (dummy_url, pack_id_url, bms_url),
            )
        ):
            messagebox.showerror("Invalid API URL","Enter a valid URL beginning with http:// or https:// for all endpoints.",parent=self)
            return False

        try:
            save_api_urls(dummy_url,pack_id_url,bms_url)
            return True

        except Exception as exc:
            messagebox.showerror("Save error",f"Could not save API URLs:\n{exc}",parent=self)
            return False

    def save_api_keys_button(self) -> bool:

        endpoint_settings = {
            "dummy": (
                self._dummy_api_url_var.get().strip(),
                self._dummy_api_key_var.get().strip(),
            ),
            "pack_id": (
                self._pack_id_api_url_var.get().strip(),
                self._pack_id_api_key_var.get().strip(),
            ),
            "bms": (
                self._bms_api_url_var.get().strip(),
                self._bms_api_key_var.get().strip(),
            ),
        }

        enabled = {
            endpoint: variable.get()
            for endpoint, variable in self._api_call_vars.items()
        }

        for endpoint, (url, key) in endpoint_settings.items():

            if not enabled[endpoint]:
                continue

            if not is_valid_api_url(url) or not is_valid_api_key(key):
                messagebox.showerror(
                    "Invalid API settings",f"Enter a valid URL and API key for the enabled {endpoint} endpoint.",parent=self)
                return False

            try:
                key_matches = validate_api_key(url, key)

            except RequestException as exc:
                messagebox.showerror("API key validation failed",f"Could not validate the {endpoint} API key:\n{exc}",parent=self)
                return False

            if not key_matches:
                messagebox.showerror("Invalid API keys",f"The {endpoint} API key does not match the server key.",parent=self)
                return False

        try:
            save_api_keys(
                endpoint_settings["dummy"][1],
                endpoint_settings["pack_id"][1],
                endpoint_settings["bms"][1],
            )
            return True

        except Exception as exc:
            messagebox.showerror("Save error",f"Could not save API keys:\n{exc}",parent=self)
            return False


def open_admin_settings(parent: tk.Misc,*,current_user: str) -> None:
    AdminSettingsDialog(parent,current_user=current_user)