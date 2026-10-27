import tkinter as tk
from collections.abc import Callable
from tkinter import ttk


def setup_hardware_scanner(
    entry: ttk.Entry,
    variable: tk.StringVar,
    on_scan: Callable[[str], None],
) -> None:
    """
    Scanner must be configured to send ENTER after the barcode.
    When ENTER is received, the scanned value is submitted immediately.
    """

    entry.configure(font=("Consolas", 11))

    def _process_scan(_event: tk.Event | None = None) -> str:
        scanned = variable.get().strip()

        if scanned:
            on_scan(scanned)

        # Clear for next scan
        variable.set("")

        # Keep focus on scanner field
        entry.focus_set()

        return "break"

    # Submit when scanner sends ENTER
    entry.bind("<Return>", _process_scan)

    # Keep scanner field focused
    entry.focus_set()