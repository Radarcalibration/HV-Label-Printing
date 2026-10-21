 

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

_SCAN_IDLE_MS = 500


def setup_hardware_scanner(
    entry: ttk.Entry,
    variable: tk.StringVar,
    on_scan: Callable[[str], None],
) -> None:
    """Submit scanner input after its keystroke burst, or immediately on Enter."""
    entry.configure(font=("Consolas", 11))
    pending_scan: str | None = None

    def _cancel_pending_scan() -> None:
        nonlocal pending_scan
        if pending_scan is not None:
            entry.after_cancel(pending_scan)
            pending_scan = None

    def _submit_scan() -> None:
        scanned = variable.get().strip()
        if scanned:
            on_scan(scanned)

    def _submit_after_idle() -> None:
        nonlocal pending_scan
        pending_scan = None
        _submit_scan()

    def _schedule_scan(event: tk.Event) -> None:
        nonlocal pending_scan
        if event.keysym == "Return":
            _cancel_pending_scan()
            return
        _cancel_pending_scan()
        if variable.get().strip():
            pending_scan = entry.after(_SCAN_IDLE_MS, _submit_after_idle)

    def _ignore_enter(_event: tk.Event) -> str:
        _cancel_pending_scan()
        return "break"

    entry.bind("<KeyRelease>", _schedule_scan)
    entry.bind("<Return>", _ignore_enter)
    entry.focus_set()