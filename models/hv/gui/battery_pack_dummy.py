import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
import requests

from api.Client import send_dummy_scan, get_machine_details
from models.hv.gui.battery_parameters import build_battery_parameters_panel, set_battery_parameters
from models.hv.gui.category_controls import add_category_field, bind_category_variant
from models.hv.gui.constants import (
    CELL_MFR_OPTIONS,
    VARIANT_OPTIONS,
    format_pack_qr_data,
    get_cell_mfr_options,
    get_module_count,
    get_pack_variant,
    get_serial_model,
    get_pack_part_number,
    get_variant_params,
    variants_for_category,
)
from models.hv.gui.layout import DISPLAY_FONT, FIELD_FONT, HEADING_FONT, LABEL_FONT, configure_equal_columns
from models.hv.gui.permissions import set_combobox_enabled, set_entry_enabled
from models.hv.gui.print_actions import dispatch_zpl
from models.hv.gui.scan_apply import apply_module_fields, format_date_display
from models.hv.gui.scanner import setup_hardware_scanner
from models.hv.nomenclature.module_id import parse_module_id
from models.hv.nomenclature.serial_number import (
    ParsedSerialNumber,
    build_serial_number,
    parse_serial_number,
)
from models.hv.nomenclature.scan_handler import ScanType, identify_scan
from models.hv.printing.constants import PRINTER_DUMMY
from common.auth.session import Session
from models.hv.gui.scan_history import open_scan_history 
from models.hv.printing.labels import build_hv_dummy_id_label
from models.hv.session.pack_store import (
    increment_pack_serial,
    load_pack_serial,
    load_pack_serial_count,
    save_pack_serial,
    save_pack_serial_count,
)
from models.hv.session.scan_log import ScanRecord, append_scan_record

COMPACT_IPADY = 2
_RESET_DELAY_MS = 1000


def _format_time(dt: datetime) -> str:
    return dt.strftime("%I/%M/%S %p")


class BatteryPackDummyGUI:

    def __init__(self, parent: tk.Misc | None = None, *, is_admin: bool = False, session: Session | None = None) -> None:
        self.is_admin = is_admin
        self._session = session
        if parent is None:
            self.root = tk.Tk()
            self.host = self.root
            self.root.title("Battery Pack Dummy ID")
            self.root.geometry("1200x820")
            self.root.minsize(1000, 700)
        elif isinstance(parent, (tk.Tk, tk.Toplevel)):
            self.root = parent
            self.host = parent
            self.root.title("Battery Pack Dummy ID")
        else:
            self.root = parent.winfo_toplevel()
            self.host = parent

        self._param_labels: dict[str, ttk.Label] = {}
        self._module_vars: list[tk.StringVar] = []
        self._widgets: dict[str, tk.Widget] = {}
        self._category_combo: ttk.Combobox | None = None
        self._serial_number_entry: ttk.Entry | None = None
        self._integration_ok = False
        self._suppress_traces = False
        self._vars_ready = False
        self.integration_status_var = tk.StringVar(value="--Waiting for Module Integration--")
        self.pack_qr_var = tk.StringVar(value="--Waiting for Module Integration--")
        self.print_var = tk.StringVar(value="print")


        self._true_date = datetime.now().date()
        self._last_refresh_date = self._true_date

        self._build_ui()
        self._refresh_datetime()
        self._on_variant_or_revision_change()
        self._init_serial()
        self._apply_permissions()
        self._vars_ready = True
        self.serial_number_var.trace_add("write", self._on_serial_number_typed)
        if "date" in self.vars:
            self.vars["date"].trace_add("write", self._on_date_edited)


    def _init_serial(self) -> None:
        stored = load_pack_serial()
        if stored:
            parsed = parse_serial_number(stored)
            if parsed is not None:
                if parsed.cell_mfr not in get_cell_mfr_options(parsed.variant):
                    messagebox.showwarning(
                        "Cell Manufacturer",
                        f"{parsed.variant} is only configured for BAK cells.",
                        parent=self.root,
                    )
                    return
                serial = build_serial_number(
                    plant=parsed.plant,
                    line=parsed.line,
                    when=parsed.as_date,
                    serial_count=parsed.serial_count,
                    variant=parsed.variant,
                    cell_mfr=parsed.cell_mfr,
                    category=parsed.category,
                )
                if serial != parsed.raw:
                    save_pack_serial(serial)
                    parsed = parse_serial_number(serial)
                if parsed is None:
                    return
                self._apply_serial_configuration(parsed)
                self.serial_number_var.set(parsed.raw)
            else:
                self.serial_number_var.set(stored)
                stored_count = load_pack_serial_count()
                if stored_count:
                    self.vars["serial_count"].set(stored_count)
        else:
            self._rebuild_and_store_serial()


    def _serial_number_kwargs(self) -> dict:
        
        return {
            "variant": self.vars["variant"].get(),
            "cell_mfr": self.vars["cell_mfr"].get(),
            "category": self.vars["category"].get(),
        }

    def _rebuild_and_store_serial(self) -> None:
        try:
            count = self.vars.get("serial_count")
            pad = 5
            count_str = count.get() if count is not None else "000001".zfill(pad)
            count_str = (count_str or "1").zfill(pad)
            extra = self._serial_number_kwargs()
            serial = build_serial_number(
                plant=self.vars["plant"].get(),
                line=self.vars["line"].get(),
                when=self._true_date,
                serial_count=count_str,
                **extra,
            )
            save_pack_serial(serial)
            save_pack_serial_count(count_str.zfill(pad))
            if hasattr(self, "serial_number_var"):
                self.serial_number_var.set(serial)
        except (ValueError, KeyError):
            pass


    def _build_ui(self) -> None:
        container = ttk.Frame(self.host, padding=(12, 6))
        container.pack(fill=tk.BOTH, expand=True)

        self._build_config_rows(container)

        self._param_labels, self.serial_number_var, self._serial_number_entry, self._captions = (
            build_battery_parameters_panel(container, dense=True, plain_labels=True)
        )
        if self._serial_number_entry is not None:
            self._serial_number_entry.bind("<FocusOut>", self._on_serial_number_commit)
            self._serial_number_entry.bind("<Return>", self._on_serial_number_commit)

        self._build_modules_and_integration(container)
        self._build_scan_row(container)
        self._build_qr_preview(container)

    def _build_config_rows(self, parent: ttk.Frame) -> None:
        config_frame = ttk.Frame(parent, padding=(0, 0, 0, 6))
        config_frame.pack(fill=tk.X)

        ttk.Label(config_frame, text="Configuration", font=HEADING_FONT).pack(anchor=tk.W, pady=(0, 6))


        visible_row1 = [
            ("Plant",    "plant",    ["Jigani", "Domlur"]),
            ("Line",     "line",     ["1", "2", "3"]),
            ("Variant",  "variant",  VARIANT_OPTIONS),
            ("Cell Manufacturer", "cell_mfr", CELL_MFR_OPTIONS),
        ]


        visible_row2 = [
            ("Serial Count", "serial_count", None),
            ("Date",         "date",         None),
            ("Time",         "time",         None),
        ]


        hidden_fields = [
            ("machine",      ["1", "2"]),
        ]
        hidden_string_fields = [
            ("ref_no",        ""),
        ]

        self.vars: dict[str, tk.Variable] = {}


        row1 = ttk.Frame(config_frame) #row 1 variables
        row1.pack(fill=tk.X, pady=(0, 4))
        configure_equal_columns(row1, 5)

        self.vars["category"] = tk.StringVar(value="Domestic")
        self._category_combo = add_category_field(
            row1,
            self.vars["category"],
            grid_column=0,
            compact=True,
            padx=(0, 8),
        )

        for column, (label, key, values) in enumerate(visible_row1, start=1):
            self._add_field(row1, column, label, key, values)


        row2 = ttk.Frame(config_frame) #row 2 variables
        row2.pack(fill=tk.X, pady=(0, 4))
        configure_equal_columns(row2, 3)
        for column, (label, key, values) in enumerate(visible_row2):
            self._add_field(row2, column, label, key, values)


        for key, values in hidden_fields:
            self.vars[key] = tk.StringVar(value="" if key == "cell_mfr" else values[0])
            stub = ttk.Combobox(self.host, textvariable=self.vars[key], values=values, state="readonly")
            self._widgets[key] = stub


        for key, default in hidden_string_fields:
            self.vars[key] = tk.StringVar(value=default)

        bind_category_variant(
            self.vars["category"],
            self.vars["variant"],
            self._widgets["variant"],
            self._on_variant_or_revision_change,
        )
        for key in ("variant", "category", "plant", "line", "cell_mfr"):
            self.vars[key].trace_add("write", self._on_variant_or_revision_change)



        serial_var: tk.StringVar = self.vars["serial_count"]
        serial_entry = self._widgets["serial_count"]
        serial_entry.configure(validate="key", validatecommand=(self.root.register(self._validate_serial_count), "%P"))

        serial_entry.bind("<FocusOut>", self._on_serial_count_commit) # click anywhere to submit
        serial_entry.bind("<Return>", self._on_serial_count_commit) # click enter to submit
        serial_var.set("000001") #initial count (can be editable)

    def _add_field(self, parent: ttk.Frame, column: int, label: str, key: str, values: list[str] | None) -> None:
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, sticky="nsew", padx=(0, 8))
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text=label, font=LABEL_FONT).pack(anchor=tk.W)

        if values is not None:
            var = tk.StringVar(value=values[0])
            widget = ttk.Combobox(frame, textvariable=var, values=values, state="readonly", font=FIELD_FONT)
        elif key == "serial_count":
            var = tk.StringVar()
            widget = ttk.Entry(frame, textvariable=var, font=FIELD_FONT)
            
        elif key == "date":
            var = tk.StringVar(value=self._current_date_str())
            widget = ttk.Entry(frame, textvariable=var, font=FIELD_FONT)
        elif key == "time":
            var = tk.StringVar()
            widget = ttk.Entry(frame, textvariable=var, state="readonly", font=FIELD_FONT)
        else:
            var = tk.StringVar()
            widget = ttk.Entry(frame, textvariable=var, font=FIELD_FONT)

        widget.pack(fill=tk.X, pady=(2, 0), ipady=COMPACT_IPADY)
        self.vars[key] = var
        self._widgets[key] = widget

    def _build_modules_and_integration(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent, padding=(0, 6, 0, 0))
        row.pack(fill=tk.X)
        row.columnconfigure(0, weight=3)
        row.columnconfigure(1, weight=2)

        modules_col = ttk.Frame(row)
        modules_col.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ttk.Label(modules_col, text="Modules", font=HEADING_FONT).pack(anchor=tk.W, pady=(0, 6))

        modules_row = ttk.Frame(modules_col)
        modules_row.pack(fill=tk.X)
        configure_equal_columns(modules_row, 4, uniform="module")

        for column, module_id in enumerate(("M1", "M2", "M3", "M4")):
            box = ttk.Frame(modules_row)
            box.grid(row=0, column=column, sticky="nsew", padx=(0, 6))
            box.columnconfigure(0, weight=1)
            ttk.Label(box, text=module_id, font=LABEL_FONT).pack(anchor=tk.W)
            module_var = tk.StringVar()
            ttk.Label(box, textvariable=module_var, anchor=tk.W, font=DISPLAY_FONT).pack(fill=tk.X, pady=(2, 0))
            self._module_vars.append(module_var)

        integration_col = ttk.Frame(row)
        integration_col.grid(row=0, column=1, sticky="nsew")
        integration_col.columnconfigure(1, weight=1)

        ttk.Label(integration_col, text="Integration", font=HEADING_FONT).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 6)
        )
        ttk.Label(integration_col, text="Status:", font=LABEL_FONT).grid(row=1, column=0, sticky=tk.W)
        ttk.Label(
            integration_col,
            textvariable=self.integration_status_var,
            font=("Segoe UI", 11, "bold"),
            foreground="#511595",
        ).grid(row=1, column=1, sticky=tk.W, padx=(6, 0))

        ttk.Label(integration_col, text="Pack QR:", font=LABEL_FONT).grid(row=2, column=0, sticky=tk.W, pady=(6, 0))
        ttk.Label(
            integration_col,
            textvariable=self.pack_qr_var,
            font=("Segoe UI", 11, "bold"),
            foreground="#23824E",
            anchor=tk.W,
        ).grid(row=2, column=1, sticky="ew", padx=(6, 0), pady=(6, 0))

    def _build_scan_row(self, parent: ttk.Frame) -> None:
        bar = ttk.Frame(parent, padding=(0, 6, 0, 0))
        bar.pack(fill=tk.X)
        bar.columnconfigure(0, weight=1)

        ttk.Label(bar, text="Scanner", font=HEADING_FONT).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))

        self.scan_var = tk.StringVar()
        scan_entry = ttk.Entry(bar, textvariable=self.scan_var, font=FIELD_FONT)
        scan_entry.grid(row=1, column=0, sticky="ew", ipady=COMPACT_IPADY + 1)
        setup_hardware_scanner(scan_entry, self.scan_var, self._on_scan)

        controls = ttk.Frame(bar)
        controls.grid(row=1, column=1, sticky=tk.E, padx=(10, 0))
        ttk.Combobox(
            controls, textvariable=self.print_var, values=["print", "pdf"],
            state="readonly", width=8, justify="center",
        ).pack(side=tk.LEFT, ipady=COMPACT_IPADY, padx=(0, 8))
        ttk.Button(controls, text="Clear", command=self._clear_modules, width=8).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(controls, text="History", command=self._open_history, width=10).pack(side=tk.LEFT, padx=(0, 8))
    

    def _build_qr_preview(self, parent: ttk.Frame) -> None:
        preview_frame = ttk.Frame(parent, padding=(0, 6, 0, 0))
        preview_frame.pack(fill=tk.X)
        ttk.Label(preview_frame, text="Pack QR Preview", font=HEADING_FONT).pack(anchor=tk.W, pady=(0, 6))
        self.preview_var = tk.StringVar(value="--Waiting for Module Integration--")
        ttk.Label(
            preview_frame, textvariable=self.preview_var,
            font=("Segoe UI", 11), foreground="#0a5c9e", anchor=tk.W, wraplength=1000,
        ).pack(fill=tk.X)



    def _all_modules_scanned(self) -> bool:
        m1 = parse_module_id(self._module_vars[0].get().strip())
        if m1 is None:
            return False
        required_count = get_module_count(m1.variant, m1.cell_mfr)
        return required_count > 0 and all(
            self._module_vars[index].get().strip()
            for index in range(required_count)
        )

    def _m1_variant(self) -> str | None:
        m1_raw = self._module_vars[0].get().strip()
        if not m1_raw:
            return None
        parsed = parse_module_id(m1_raw)
        return parsed.variant if parsed is not None else None

    def _m1_plant(self) -> str | None:
        m1_raw = self._module_vars[0].get().strip()
        if not m1_raw:
            return None
        parsed = parse_module_id(m1_raw)
        return parsed.plant if parsed is not None else None

    def _m1_part_number(self) -> str | None:
        m1_raw = self._module_vars[0].get().strip()
        if not m1_raw:
            return None
        parsed = parse_module_id(m1_raw)
        return parsed.part_number if parsed is not None else None

    def _clear_modules(self) -> None:
        self.scan_var.set("")
        for module_var in self._module_vars:
            module_var.set("")
        self._on_variant_or_revision_change()
        self._reset_integration()
        self.preview_var.set("--Waiting for Module Integration--")

    def _on_scan(self, raw: str) -> None:
        result = identify_scan(raw)
        self.scan_var.set("")

        if result.scan_type == ScanType.SERIAL_NUMBER:
            messagebox.showwarning("Scan format", "Scan the required module IDs for this battery pack.", parent=self.root)
            return

        if result.scan_type == ScanType.MODULE_ID and result.module is not None: # module ids validation logic
            existing_slot = next(
                (i for i, v in enumerate(self._module_vars) if v.get().strip() == result.raw),
                None,
            )
            if existing_slot is not None:
                messagebox.showinfo(
                    "scanned",
                    f"This module is already in M{existing_slot + 1}.",
                    parent=self.root,
                )
                return

            first_module = parse_module_id(self._module_vars[0].get().strip())
            required_count = (
                get_module_count(first_module.variant, first_module.cell_mfr)
                if first_module is not None
                else get_module_count(result.module.variant, result.module.cell_mfr)
            )
            empty_slots = [
                i for i in range(required_count)
                if not self._module_vars[i].get().strip()
            ]
            if not empty_slots:
                messagebox.showwarning(
                    "Scan order",
                    f"All {required_count} required modules are already scanned. Clear before the next pack.",
                    parent=self.root,
                )
                return
            slot = empty_slots[0]
            module_number = slot + 1

            incoming_variant = result.module.variant
            incoming_plant = result.module.plant
            incoming_part_number = result.module.part_number
            m1_plant = self._m1_plant()
            m1_part_number = self._m1_part_number()
            m1_cell_mfr = first_module.cell_mfr if first_module is not None else None
            category = self.vars["category"].get().strip().lower()

            if category == "export" and incoming_variant not in variants_for_category("Export"): #1
                messagebox.showerror(
                    "Variant error",
                    f"Export does not support {incoming_variant} modules.",
                    parent=self.root,
                )
                return
            if module_number > 1 and m1_cell_mfr != result.module.cell_mfr:
                messagebox.showerror(
                    "Cell manufacturer mismatch",
                    f"M{module_number} is {result.module.cell_mfr} but M1 is {m1_cell_mfr}.",
                    parent=self.root,
                )
                return
            if module_number > 1 and first_module is not None:
                first_pack_variant = get_pack_variant(first_module.variant, first_module.cell_mfr)
                incoming_pack_variant = get_pack_variant(incoming_variant, result.module.cell_mfr)
                if first_pack_variant != incoming_pack_variant:
                    messagebox.showerror(
                        "Variant mismatch",
                        f"M{module_number} belongs to {incoming_pack_variant}, but M1 belongs to {first_pack_variant}.",
                        parent=self.root,
                    )
                    return
                if (
                    get_serial_model(first_module.variant, first_module.cell_mfr) == "shockwave"
                    and first_module.part_number == incoming_part_number
                ):
                    messagebox.showerror(
                        "Module mismatch",
                        "Shockwave M1 and M2 must have different module part numbers.",
                        parent=self.root,
                    )
                    return
            if module_number > 1 and m1_plant is not None and incoming_plant != m1_plant:
                messagebox.showerror(
                    "Plant mismatch",
                    f"M{module_number} is from {incoming_plant} but M1 is from {m1_plant}.",
                    parent=self.root,
                )
                return

            self._module_vars[slot].set(result.raw)
            apply_module_fields(self.vars, result.module) 
            self._on_variant_or_revision_change()
            self._try_complete_integration()
            return

        messagebox.showwarning("Scan", "Unrecognized code. Scan a Module QR Code.", parent=self.root)


    def _reset_integration(self) -> None:
        self._integration_ok = False
        self.integration_status_var.set("--Waiting for Module Integration--")
        self.pack_qr_var.set("--Waiting for Module Integration--")

    def _try_complete_integration(self) -> None:
        if not self._all_modules_scanned():
            self._reset_integration()
            return

        first_module = parse_module_id(self._module_vars[0].get().strip())
        if first_module is None:
            self._reset_integration()
            return
        required_count = get_module_count(first_module.variant, first_module.cell_mfr)
        modules = []
        plants: list[str] = []
        cell_mfrs: list[str] = []
        for mv in self._module_vars[:required_count]:
            p = parse_module_id(mv.get().strip())
            if p is None:
                self._reset_integration()
                return
            modules.append(p)
            plants.append(p.plant)
            cell_mfrs.append(p.cell_mfr)

        pack_variants = {
            get_pack_variant(module.variant, module.cell_mfr)
            for module in modules
        }
        part_numbers = {module.part_number for module in modules}
        if len(pack_variants) != 1:
            messagebox.showerror("Variants mismatch", "Scanned modules do not belong to the same pack variant.", parent=self.root)
            self._reset_integration()
            return
        if (
            get_serial_model(first_module.variant, first_module.cell_mfr) == "shockwave"
            and len(part_numbers) != required_count
        ):
            messagebox.showerror("Module mismatch", "Shockwave M1 and M2 must have different module part numbers.", parent=self.root)
            self._reset_integration()
            return

        if len(set(plants)) > 1:
            messagebox.showerror("plants mismatch", "All modules must be from the same plant.", parent=self.root)
            self._reset_integration()
            return
        if len(set(cell_mfrs)) > 1:
            messagebox.showerror("cell manufacturer mismatch", "All modules must use the same cell manufacturer.", parent=self.root)
            self._reset_integration()
            return

        variant = next(iter(pack_variants))
        cell_mfr = cell_mfrs[0]
        self._suppress_traces = True
        self.vars["cell_mfr"].set(cell_mfr)
        self.vars["variant"].set(variant)
        self._suppress_traces = False
        self._on_variant_or_revision_change()
        serial = load_pack_serial()
        self.serial_number_var.set(serial)

        pack_qr = format_pack_qr_data(variant=variant, serial_number=serial, cell_mfr=cell_mfr)
        self.pack_qr_var.set(pack_qr)
        self.integration_status_var.set("INTEGRATION OK")
        self._integration_ok = True
        self.preview_var.set(f"QR Data: {pack_qr}")
        self._collect_extra_fields_then_print()

    def _collect_extra_fields_then_print(self) -> None:
        popup = tk.Toplevel(self.root)
        popup.title("Pack Details")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        frame = ttk.Frame(popup, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Enter Pack Details", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        ttk.Label(frame, text="Variant").grid(row=1, column=0, sticky=tk.W, pady=3, padx=(0, 10))
        ttk.Label(frame, text=self.vars["variant"].get(), font=("Segoe UI", 10, "bold")).grid(
            row=1, column=1, sticky=tk.W, pady=3
        )

        fields = []
        fields.append(("Ref No", "ref_no", None))
        local_vars: dict[str, tk.StringVar] = {}
        for row_idx, (label, key, options) in enumerate(fields, start=2):
            ttk.Label(frame, text=label).grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=(0, 10))
            default_value = "--Select--" if key == "cell_mfr" else self.vars[key].get()
            var = tk.StringVar(value=default_value)
            local_vars[key] = var
            if options:
                w = ttk.Combobox(frame, textvariable=var, values=options, state="readonly", width=22)
            else:
                w = ttk.Entry(frame, textvariable=var, width=24)
            w.grid(row=row_idx, column=1, sticky=tk.EW, pady=3)

        def _continue_to_print() -> None:
            for key, var in local_vars.items():
                self.vars[key].set(var.get())
            popup.destroy()
            self.root.after(50, self._auto_print_and_reset)

        def _on_ok() -> None:
            _continue_to_print()

        def _on_skip() -> None:
            _continue_to_print()
            
        btn_row = ttk.Frame(frame)
        btn_row.grid(row=len(fields) + 2, column=0, columnspan=2, sticky=tk.E, pady=(12, 0))
        ttk.Button(btn_row, text="Skip", command=_on_skip, width=8).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="OK", command=_on_ok, width=8).pack(side=tk.LEFT)

        frame.columnconfigure(1, weight=1)
        popup.bind("<Return>", lambda _e: _on_ok())
        popup.protocol("WM_DELETE_WINDOW", lambda: None)

        # Centre over main window
        popup.update_idletasks()
        rx = self.root.winfo_rootx() + (self.root.winfo_width() - popup.winfo_width()) // 2
        ry = self.root.winfo_rooty() + (self.root.winfo_height() - popup.winfo_height()) // 2
        popup.geometry(f"+{max(0,rx)}+{max(0,ry)}")

    def _auto_print_and_reset(self) -> None:
        variant = self.vars["variant"].get()
        cell_mfr = self.vars["cell_mfr"].get()
        serial = self.serial_number_var.get().strip()
        pack_qr = self.pack_qr_var.get().strip()
        params = get_variant_params(variant, cell_mfr)

        _parsed = parse_serial_number(serial)
        if _parsed is None:
            messagebox.showerror(
                "Invalid Serial Number",
                "The current serial number is invalid, so it cannot be logged or incremented.",
                parent=self.root,
            )
            return
        save_pack_serial(serial)
        mfg_date = _parsed.format_date()
        category = self.vars["category"].get()
        label_mfg_date = ""
        date_format = "%Y" if category.strip().lower() == "export" else "%d %b %Y"
        label_mfg_date = _parsed.as_date.strftime(date_format)
        serial_count = _parsed.serial_count
        
        now = datetime.now()
        machine = get_machine_details()
        mfg_time = now.strftime("%I:%M:%S %p")
        
        # category = self.vars["category"].get().strip().lower()

        ref_no = self.vars["ref_no"].get().strip()

        dummy_status = "INTEGRATION OK" if self._integration_ok else "INTEGRATION FAILED"

        record = ScanRecord(
            date=mfg_date,
            time=mfg_time,
            serial_count=serial_count,
            ref_no=ref_no,
            variant=variant,
            m1=self._module_vars[0].get(),
            m2=self._module_vars[1].get(),
            m3=self._module_vars[2].get(),
            m4=self._module_vars[3].get(),
            dummy_pack_status=dummy_status,
            dummy_pack_qr=pack_qr,
            serial_number=serial,
            machine_name=machine["machine_name"],
            machine_id=machine["machine_id"],
        )

        excel_pw = self._session.excel_password if self._session else "06082003"
        log_saved = False
        try:
            append_scan_record(record, excel_password=excel_pw)
            log_saved = True
        except Exception as exc:
            messagebox.showerror("Log Error", f"Could not able to write scan log:\n{exc}", parent=self.root)
        serial_advanced = False
        if log_saved:
            serial_advanced = self._advance_serial_count(serial)

        try:
            send_dummy_scan(record) # client side post
        except requests.exceptions.RequestException as e:
                print("Request failed:", e, parent=self.root)

        zpl = build_hv_dummy_id_label(
            pack_qr_data=pack_qr,
            serial_number=serial,
            tac_number=params["tac_number"],
            mfg_date=label_mfg_date,
            variant=variant,
            category=category,
            cell_mfr=cell_mfr,
        )
        print_succeeded = dispatch_zpl(
            self.root,
            zpl,
            self.print_var.get(),
            default_name=f"pack_{serial}.zpl",
            printer_name=PRINTER_DUMMY,
        )

        if not log_saved and self.print_var.get() == "print" and print_succeeded:
            serial_advanced = self._advance_serial_count(serial)

        if log_saved or serial_advanced:
            self.root.after(_RESET_DELAY_MS, self._auto_reset) # resets essential fields after 1s
        else: # for log save faild
            for module_var in self._module_vars:
                module_var.set("") # resets label if log save failed
            self.vars["cell_mfr"].set("")
            self._on_variant_or_revision_change()
            self._reset_integration()
            self.preview_var.set("--Waiting for Module Integration--")

    def _advance_serial_count(self, serial: str) -> bool:
        try:
            next_serial = increment_pack_serial(serial)
        except ValueError as exc:
            messagebox.showerror("Serial Count Limit", str(exc), parent=self.root)
            return False

        next_parsed = parse_serial_number(next_serial)
        if next_parsed is None:
            messagebox.showerror(
                "Serial Count Error",
                "The next serial number could not be parsed.",
                parent=self.root,
            )
            return False

        self._suppress_traces = True
        try:
            self.vars["serial_count"].set(next_parsed.serial_count)
            self.serial_number_var.set(next_serial)
        finally:
            self._suppress_traces = False
        return True

    def _open_history(self) -> None:
        open_scan_history(self.root, print_mode=self.print_var.get(), variant=self.vars["variant"].get(), origin="dummy")

    def _auto_reset(self) -> None:
        for module_var in self._module_vars:
            module_var.set("")
        self._suppress_traces = True
        try:
            self.vars["cell_mfr"].set("")
        finally:
            self._suppress_traces = False
        self._reset_integration()
        self.preview_var.set("--Waiting for Module Integration--")
        self._true_date = datetime.now().date()
        new_serial = load_pack_serial() # new serial 
        self.serial_number_var.set(new_serial)
        _parsed = parse_serial_number(new_serial)
        if _parsed:
            self.vars["serial_count"].set(_parsed.serial_count)
        self._on_variant_or_revision_change()


    def _on_date_edited(self, *_args: object) -> None:
        if self._suppress_traces:
            return
        date_str = self.vars["date"].get().strip()
        if not date_str:
            return
        from datetime import date as _date, datetime as _dt
        _when = None
        # year_only = False
        for fmt in ("%d/%B/%Y", "%d %b %Y", "%d-%b-%Y", "%d/%m/%Y"):
            try:
                _when = _dt.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue
        if _when is None and date_str.isdigit() and len(date_str) == 4:
            try:
                _when = self._true_date.replace(year=int(date_str))
                # year_only = True
            except ValueError:
                return
        if _when is None:
            return  
        if _when > _date.today():
            return  
        self._true_date = _when
        current = load_pack_serial()
        parsed = parse_serial_number(current) if current else None
        default_count = "1".zfill(5)
        serial_count = parsed.serial_count if parsed is not None else self.vars.get("serial_count", tk.StringVar(value=default_count)).get()
        extra = self._serial_number_kwargs()
        try:
            new_serial = build_serial_number(
                plant=self.vars["plant"].get(),
                line=self.vars["line"].get(),
                when=self._true_date,
                serial_count=serial_count,
                **extra,
            )
            self._suppress_traces = True
            save_pack_serial(new_serial)
            if hasattr(self, "serial_number_var"):
                self.serial_number_var.set(new_serial)
            self._suppress_traces = False
        except ValueError:
            pass

    def _on_variant_or_revision_change(self, *_args: object) -> None:
        variant = self.vars["variant"].get()
        cell_mfr = self.vars["cell_mfr"].get()
        supported_cell_mfrs = get_cell_mfr_options(variant)
        cell_mfr_combo = self._widgets.get("cell_mfr")
        if isinstance(cell_mfr_combo, ttk.Combobox):
            cell_mfr_combo.configure(values=supported_cell_mfrs)
        if supported_cell_mfrs and cell_mfr not in supported_cell_mfrs:
            was_suppressing = self._suppress_traces
            self._suppress_traces = True
            self.vars["cell_mfr"].set(supported_cell_mfrs[0])
            self._suppress_traces = was_suppressing
            cell_mfr = supported_cell_mfrs[0]
        params = get_variant_params(variant, cell_mfr)

        if self._param_labels:
            set_battery_parameters(
                self._param_labels,
                rated_capacity=params.get("rated_capacity", ""),
                max_voltage=params.get("max_voltage", ""),
                model_number=get_pack_part_number(variant, cell_mfr) if cell_mfr else "Waiting...",
                tac_number=params.get("tac_number", ""),
                emark=params.get("emark_number", ""),
                category=self.vars["category"].get(),
                captions=self._captions,
            )

        if "date" in self.vars:
            self._suppress_traces = True
            self.vars["date"].set(self._current_date_str())
            self._suppress_traces = False

        if self._vars_ready and not self._suppress_traces:
            self._rebuild_and_store_serial()


    def _validate_serial_count(self, proposed: str) -> bool:
        if proposed == "":
            return True
        if not proposed.isdigit():
            return False
        max_len = 5
        return len(proposed) <= max_len

    def _on_serial_count_commit(self, _event: object = None) -> None:
        raw = self.vars["serial_count"].get().strip()
        if not raw or not raw.isdigit():
            return

        pad = 5
        max_value = 99999

        value = int(raw)
        if value < 1:
            value = 1
        if value > max_value:
            value = max_value

        padded = str(value).zfill(pad)

        self._suppress_traces = True
        try:
            self.vars["serial_count"].set(padded)
        finally:
            self._suppress_traces = False

        current = load_pack_serial()
        parsed = parse_serial_number(current) if current else None
        if parsed is not None:
            extra = {
                "variant": parsed.variant,
                "cell_mfr": parsed.cell_mfr,
                "category": parsed.category,
            }
            plant, line, when = parsed.plant, parsed.line, parsed.as_date
        else:
            extra = self._serial_number_kwargs()
            plant, line, when = self.vars["plant"].get(), self.vars["line"].get(), datetime.now().date()
        try:
            new_serial = build_serial_number(
                plant=plant,
                line=line,
                when=when,
                serial_count=padded,
                **extra,
            )
        except (ValueError, KeyError) as exc:
            messagebox.showerror("Invalid serial settings", str(exc), parent=self.root)
            return

        save_pack_serial(new_serial)
        save_pack_serial_count(padded)

        self.serial_number_var.set(new_serial)

    def _on_serial_number_typed(self, *_args: object) -> None:
        if self._suppress_traces:
            return
        serial = self.serial_number_var.get().strip()
        if len(serial) ==20 : # exact 20 digit serial number (fixed)
            self._suppress_traces = True
            try:
                self._update_vars_from_serial(serial)
            finally:
                self._suppress_traces = False

    def _on_serial_number_commit(self, _event: object = None) -> None:
        if self._suppress_traces:
            return
        serial = self.serial_number_var.get().strip()

        if len(serial)!=20:
            messagebox.showerror(
                "Invalid serial number ",
                "Serial number must be exactly 20 characters.",
                parent=self.root,
            )
            self._suppress_traces = True
            self.serial_number_var.set(load_pack_serial())
            self._suppress_traces = False
            return

        parsed = parse_serial_number(serial)
        if parsed is None:
            messagebox.showerror(
                "Invalid Serial Number",
                "Could not be able parse this serial number. Reverting to last valid value.",
                parent=self.root,
            )
            self._suppress_traces = True
            self.serial_number_var.set(load_pack_serial())
            self._suppress_traces = False
            return

        self._suppress_traces = True
        try:
            self._update_vars_from_serial(serial)
        finally:
            self._suppress_traces = False

    def _current_date_str(self) -> str:
        cat = self.vars.get("category")
        is_export = cat and cat.get().lower() == "export"
        return str(self._true_date.year) if is_export else format_date_display(self._true_date)

    def _update_vars_from_serial(self, serial: str) -> None:
        parsed = parse_serial_number(serial.strip())
        if parsed is None:
            return
        if parsed.cell_mfr not in get_cell_mfr_options(parsed.variant):
            messagebox.showwarning(
                "Cell Manufacturer",
                f"{parsed.variant} is only configured for BAK cells.",
                parent=self.root,
            )
            return
        from datetime import date as _date
        is_export = self.vars["category"].get().strip().lower() == "export"
        if not is_export and parsed.as_date > _date.today():
            messagebox.showwarning("Invalid Date", "Future dates are not allowed.", parent=self.root)
            return

        save_pack_serial(serial.strip())
        save_pack_serial_count(parsed.serial_count)
        self._apply_serial_configuration(parsed)

    def _apply_serial_configuration(self, parsed: ParsedSerialNumber) -> None:
        self._true_date = parsed.as_date
        self._suppress_traces = True
        try:
            self.vars["category"].set(parsed.category.capitalize())
            self.vars["plant"].set(parsed.plant)
            self.vars["line"].set(parsed.line)
            self.vars["serial_count"].set(parsed.serial_count)
            self.vars["cell_mfr"].set(parsed.cell_mfr)
            self.vars["variant"].set(parsed.variant)
            if "date" in self.vars:
                self.vars["date"].set(self._current_date_str())
        finally:
            self._suppress_traces = False
        self._on_variant_or_revision_change()
        self.serial_number_var.set(parsed.raw)

    
    def _refresh_datetime(self) -> None:
        now = datetime.now()
        self.vars["time"].set(_format_time(now))
        rebuild_required = False
        current_date = now.date()

        if current_date != self._last_refresh_date:
            self._last_refresh_date = current_date
            self._true_date = current_date

            if "date" in self.vars:
                self._suppress_traces = True
                try:
                    self.vars["date"].set(self._current_date_str())
                finally:
                    self._suppress_traces = False

            rebuild_required = True


        # Rebuild serial only when needed
        if rebuild_required:
            self._rebuild_and_store_serial()

        self.root.after(1000, self._refresh_datetime)
    
    def _apply_permissions(self) -> None:
        if self._category_combo is not None:
            set_combobox_enabled(self._category_combo, self.is_admin)
        for key, widget in self._widgets.items():
            if key == "time":
                if isinstance(widget, ttk.Entry):
                    widget.configure(state="readonly")
                continue
            if key == "date":
                if isinstance(widget, ttk.Entry):
                    widget.configure(state="readonly") 
                    # set_entry_enabled(widget, True) # uncomment to make date editable to everyone
                continue #editable to none
            
            if isinstance(widget, ttk.Combobox):
                set_combobox_enabled(widget, self.is_admin)
            elif isinstance(widget, ttk.Entry):
                set_entry_enabled(widget, self.is_admin)
            

        if self._serial_number_entry is not None:
            set_entry_enabled(self._serial_number_entry, True)

    def run(self) -> None:
        self.root.mainloop()


def open_battery_pack_dummy(parent: tk.Tk | tk.Toplevel | None = None) -> BatteryPackDummyGUI:
    return BatteryPackDummyGUI(parent)



if __name__ == "__main__":
    BatteryPackDummyGUI().run()