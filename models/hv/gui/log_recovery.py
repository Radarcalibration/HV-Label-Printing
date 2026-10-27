from collections.abc import Callable

import tkinter as tk
from tkinter import ttk


def show_log_recovery_dialog(
    parent: tk.Misc,
    error: Exception,
    *,
    retry_save: Callable[[], None],
    on_saved: Callable[[], None],
    on_continue: Callable[[], None],
    title: str = "Log Error",
) -> None:
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.transient(parent.winfo_toplevel())
    dialog.resizable(False, False)
    dialog.grab_set()

    message = tk.StringVar(
        master=dialog,
        value=f"Could not save the Excel log:\n{error}\n\n"
        "Scanned values are retained. Retrying will not repeat a label already printed. "
        "Acknowledge & Continue skips this local log entry.",
    )
    frame = ttk.Frame(dialog, padding=16)
    frame.pack(fill=tk.BOTH, expand=True)
    ttk.Label(frame, textvariable=message, justify=tk.LEFT, wraplength=480).pack(fill=tk.X, pady=(0, 14))

    def _retry() -> None:
        try:
            retry_save()
        except Exception as exc:
            message.set(
                f"Could not save the Excel log:\n{exc}\n\n"
                "Scanned values are retained. Retrying will not repeat a label already printed. "
                "Acknowledge & Continue skips this local log entry."
            )
            return
        dialog.destroy()
        on_saved()

    def _continue() -> None:
        dialog.destroy()
        on_continue()

    buttons = ttk.Frame(frame)
    buttons.pack(fill=tk.X)
    ttk.Button(buttons, text="Acknowledge & Continue", command=_continue).pack(side=tk.RIGHT)
    ttk.Button(buttons, text="Retry Log Save", command=_retry).pack(side=tk.RIGHT, padx=(0, 8))
    dialog.protocol("WM_DELETE_WINDOW", lambda: None)
