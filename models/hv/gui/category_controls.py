import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from models.hv.gui.constants import CATEGORY_OPTIONS, variants_for_category
from models.hv.gui.layout import FIELD_FONT, FIELD_IPADY, LABEL_FONT


def add_category_field(
    parent: ttk.Frame,
    category_var: tk.StringVar,
    *,
    grid_column: int | None = None,
    compact: bool = False,
    padx: tuple[int, int] = (0, 10),
) -> ttk.Combobox:
    """Add a Category field using the same sizing as its neighboring controls."""
    frame = ttk.Frame(parent)
    frame.grid(row=0, column=grid_column, sticky="nsew", padx=padx)

    frame.columnconfigure(0, weight=1)
    ttk.Label(frame, text="Category", font=LABEL_FONT).pack(anchor=tk.W)
    combo = ttk.Combobox(
        frame, textvariable=category_var, values=CATEGORY_OPTIONS,
        state="readonly", font=FIELD_FONT,
    )
    combo.pack(
        fill=tk.X,
        pady=(2 if compact else 5, 0),
        ipady=2 if compact else FIELD_IPADY,
    )
    return combo


def bind_category_variant(
    category_var: tk.StringVar,
    variant_var: tk.StringVar,
    variant_widget: ttk.Combobox,
    on_variant_update: Callable[[], None],
) -> None:

    def _apply_category_rules(*_args: object) -> None:
        options = variants_for_category(category_var.get())
        variant_widget.configure(values=options)
        if variant_var.get() not in options:
            variant_var.set(options[0])
        on_variant_update()

    category_var.trace_add("write", _apply_category_rules)
    _apply_category_rules()