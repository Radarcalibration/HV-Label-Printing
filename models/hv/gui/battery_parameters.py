import tkinter as tk
from tkinter import ttk

from models.hv.gui.constants import BATTERY_PARAM_ROWS
from models.hv.gui.layout import HEADING_FONT, LABEL_FONT, VALUE_FONT, configure_styles


def build_battery_parameters_panel(
    parent: ttk.Frame,
    *,
    dense: bool = False,
    plain_labels: bool = True,
) -> tuple[dict[str, ttk.Label], tk.StringVar, ttk.Entry | None, dict[str, tk.StringVar]]:
   
    configure_styles(parent)

    frame_pad = (8, 6) if dense else (12, 10)
    row_pady = 2 if dense else 4
    label_width = 16

    section = ttk.Frame(parent, padding=frame_pad)
    section.pack(fill=tk.X)

    ttk.Label(section, text="Battery Parameters", font=HEADING_FONT).pack(anchor=tk.W, pady=(0, 6))

    params_frame = ttk.Frame(section)
    params_frame.pack(fill=tk.X)

    param_labels: dict[str, ttk.Label] = {}
    captions: dict[str, tk.StringVar] = {}
    serial_number_var = tk.StringVar()
    serial_number_entry: ttk.Entry | None = None

    for label_text, key, _editable in BATTERY_PARAM_ROWS:
        row = ttk.Frame(params_frame)
        row.pack(fill=tk.X, pady=row_pady)
        row.columnconfigure(1, weight=1)

        caption_var = tk.StringVar(value=label_text) #labels for values in battery parameters 
        captions[key] = caption_var
        ttk.Label(row, textvariable=caption_var, font=LABEL_FONT, width=label_width, anchor=tk.W).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 12)
        )

        if key == "serial_number":
            value_label = ttk.Label(
                row,
                textvariable=serial_number_var,
                anchor=tk.W,
                font=VALUE_FONT,
            )
        else:
            value_label = ttk.Label(
                row,
                text="",
                anchor=tk.W,
                font=VALUE_FONT,
            )
        value_label.grid(row=0, column=1, sticky="ew", padx=(0, 4))
        param_labels[key] = value_label

    return param_labels, serial_number_var, serial_number_entry, captions


def set_battery_parameters(
    param_labels: dict[str, ttk.Label],
    *,
    rated_capacity: str = "",
    max_voltage: str = "",
    model_number: str = "",
    tac_number: str = "",
    emark: str = "",
    category: str = "domestic",
    captions: dict[str, tk.StringVar] | None = None,
    show_emark_for_export: bool = True,
) -> None:
    use_emark = show_emark_for_export and category.strip().lower() == "export"

    if captions is not None and "tac_number" in captions:
        captions["tac_number"].set("E-Marking No" if use_emark else "TAC Number")

    values = {
        "rated_capacity": rated_capacity,
        "max_voltage": max_voltage,
        "model_number": model_number,
        "tac_number": emark if use_emark else tac_number,
    }
    for key, text in values.items():
        if key in param_labels:
            param_labels[key].configure(text=text)