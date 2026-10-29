import tkinter as tk
from tkinter import messagebox, ttk
import requests

from api.Client import get_machine_details, send_pack_id_scan
from models.hv.gui.battery_parameters import build_battery_parameters_panel, set_battery_parameters
from models.hv.gui.category_controls import add_category_field, bind_category_variant
from models.hv.gui.constants import (
    CELL_MFR_OPTIONS,
    VARIANT_OPTIONS,
    format_pack_qr_data,
    get_type_of_reess,
    get_variant_params,
)
from models.hv.gui.layout import FIELD_FONT, FIELD_IPADY, HEADING_FONT, LABEL_FONT, configure_equal_columns
from models.hv.gui.log_recovery import show_log_recovery_dialog
from models.hv.gui.permissions import set_combobox_enabled
from models.hv.gui.print_actions import dispatch_zpl
from models.hv.gui.scan_history import open_scan_history
from models.hv.gui.scanner import setup_hardware_scanner
from models.hv.nomenclature.scan_handler import ScanType, identify_scan
from models.hv.nomenclature.serial_number import (
    ParsedSerialNumber,
    build_serial_number,
    parse_serial_number,
)
from models.hv.printing.constants import PRINTER_PACK_ID
from models.hv.printing.labels import build_hv_pack_id_label
from datetime import datetime

from models.hv.session.pack_store import load_pack_serial, save_pack_serial
from models.hv.session.pack_id_scan_log import PackIdScanRecord
from models.hv.session.pack_id_scan_log import append_scan_record as append_pack_id_scan_record


class BatteryPackIdGUI:

    def __init__(self, parent: tk.Misc | None = None, *, is_admin: bool = False, session=None) -> None:
        self.is_admin = is_admin
        self._session = session
        if parent is None:
            self.root = tk.Tk()
            self.host = self.root
            self.root.title("Battery Pack ID")
            self.root.geometry("1100x520")
        elif isinstance(parent, (tk.Tk, tk.Toplevel)):
            self.root = parent
            self.host = parent
            self.root.title("Battery Pack ID")
        else:
            self.root = parent.winfo_toplevel()
            self.host = parent

        self._param_labels: dict[str, ttk.Label] = {}
        self._category_combo: ttk.Combobox | None = None
        self._variant_combo: ttk.Combobox | None = None
        self._cell_mfr_combo: ttk.Combobox | None = None
        self._serial_number_entry: ttk.Entry | None = None
        self._suppress_config_update = False
        self.category_var = tk.StringVar(value="Domestic")
        self.variant_var = tk.StringVar(value=VARIANT_OPTIONS[-1])
        self.cell_mfr_var = tk.StringVar(value="--Waiting for Scan--")
        self.scanner_var = tk.StringVar()
        self.print_var = tk.StringVar(value="print")

        self._build_ui()
        self.cell_mfr_var.trace_add("write", self._on_variant_change)
        self._restore_saved_serial()
        self._on_variant_change()
        for variable in (self.category_var, self.variant_var, self.cell_mfr_var):
            variable.trace_add("write", self._on_configuration_change)
        self._apply_permissions()


    def _build_ui(self) -> None:
        container = ttk.Frame(self.host, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text="Battery Pack ID",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor=tk.W, pady=(0, 14))

        self._build_config_row(container)
        self._build_scanner_section(container)
        self._param_labels, self.serial_number_var, self._serial_number_entry, self._captions = (
            build_battery_parameters_panel(container, plain_labels=True)
        )
        self.serial_number_var.set("--Waiting for Scan--")
        self._param_labels["model_number"].configure(text="--Waiting for Scan--")

    def _build_config_row(self, parent: ttk.Frame) -> None:
        config_frame = ttk.Frame(parent, padding=(0, 0, 0, 10))
        config_frame.pack(fill=tk.X)

        ttk.Label(config_frame, text="Configuration", font=HEADING_FONT).pack(anchor=tk.W, pady=(0, 6))

        row = ttk.Frame(config_frame)
        row.pack(fill=tk.X)
        configure_equal_columns(row, 3)

        self._category_combo = add_category_field(row, self.category_var, grid_column=0)
        self._variant_combo = self._add_config_dropdown(
            row, 1, "Variant", self.variant_var, VARIANT_OPTIONS
        )
        manufacturer_frame = ttk.Frame(row)
        manufacturer_frame.grid(row=0, column=2, sticky="nsew", padx=(0, 10))
        ttk.Label(manufacturer_frame, text="Cell Manufacturer", font=LABEL_FONT).pack(anchor=tk.W)
        self._cell_mfr_combo = ttk.Combobox(
            manufacturer_frame,
            textvariable=self.cell_mfr_var,
            values=CELL_MFR_OPTIONS,
            state="disabled",
            font=FIELD_FONT,
        )
        self._cell_mfr_combo.pack(fill=tk.X, pady=(5, 0), ipady=FIELD_IPADY)

        if self._variant_combo is not None:
            bind_category_variant(
                self.category_var,
                self.variant_var,
                self._variant_combo,
                self._on_variant_change,
            )
        self.variant_var.trace_add("write", self._on_variant_change)

    def _add_config_dropdown(
        self,
        parent: ttk.Frame,
        column: int,
        label: str,
        variable: tk.StringVar,
        values: list[str],
    ) -> ttk.Combobox:
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, sticky="nsew", padx=(0, 10))
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text=label, font=LABEL_FONT).pack(anchor=tk.W)
        combo = ttk.Combobox(
            frame,
            textvariable=variable,
            values=values,
            state="readonly",
            font=FIELD_FONT,
        )
        combo.pack(fill=tk.X, pady=(5, 0), ipady=FIELD_IPADY)
        return combo

    def _on_variant_change(self, *_args: object) -> None:
        if not self._param_labels:
            return

        variant = self.variant_var.get()
        params = get_variant_params(variant) or get_variant_params(VARIANT_OPTIONS[-1])

        category = self.category_var.get()
        cell_mfr = self.cell_mfr_var.get()

        set_battery_parameters(
            self._param_labels,
            rated_capacity=params["rated_capacity"],
            max_voltage=params["max_voltage"],
            model_number=(
                get_type_of_reess(variant, cell_mfr)
                if cell_mfr
                else ""
            ),
            tac_number=params["tac_number"],
            emark=params["emark"],
            category=category,
            captions=self._captions,
            show_emark_for_export=False,
        )

    def _restore_saved_serial(self) -> None:
        parsed = parse_serial_number(load_pack_serial())
        if parsed is None:
            return

        normalized_serial = build_serial_number(
            plant=parsed.plant,
            line=parsed.line,
            when=parsed.as_date,
            serial_count=parsed.serial_count,
            variant=parsed.variant,
            cell_mfr=parsed.cell_mfr,
            category=parsed.category,
        )
        if normalized_serial != parsed.raw:
            save_pack_serial(normalized_serial)
            parsed = parse_serial_number(normalized_serial)
            if parsed is None:
                return
        self._apply_serial_configuration(parsed)

    def _apply_serial_configuration(self, parsed: ParsedSerialNumber) -> None:
        self._suppress_config_update = True
        try:
            self.category_var.set(parsed.category.capitalize())
            self.variant_var.set(parsed.variant)
            self.cell_mfr_var.set(parsed.cell_mfr)
            self.serial_number_var.set(parsed.raw)
        finally:
            self._suppress_config_update = False
        self._on_variant_change()

    def _on_configuration_change(self, *_args: object) -> None:
        self._on_variant_change()
        if self._suppress_config_update:
            return

        current = self.serial_number_var.get().strip()
        parsed = parse_serial_number(current) or parse_serial_number(load_pack_serial())
        if parsed is None:
            return

        try:
            variant = self.variant_var.get()
            cell_mfr = self.cell_mfr_var.get()
            if cell_mfr not in CELL_MFR_OPTIONS:
                cell_mfr = parsed.cell_mfr
            updated = build_serial_number(
                plant=parsed.plant,
                line=parsed.line,
                when=parsed.as_date,
                serial_count=parsed.serial_count,
                variant=variant,
                cell_mfr=cell_mfr,
                category=self.category_var.get(),
            )
        except ValueError:
            return

        save_pack_serial(updated)
        self._suppress_config_update = True
        try:
            self.serial_number_var.set(updated)
        finally:
            self._suppress_config_update = False

    def _build_scanner_section(self, parent: ttk.Frame) -> None:
        bar = ttk.Frame(parent, padding=(0, 0, 0, 10))
        bar.pack(fill=tk.X)
        bar.columnconfigure(0, weight=1)

        ttk.Label(bar, text="Scanner", font=HEADING_FONT).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 6)
        )

        scanner_entry = ttk.Entry(bar, textvariable=self.scanner_var, font=FIELD_FONT)
        scanner_entry.grid(row=1, column=0, sticky="ew", ipady=FIELD_IPADY + 1)
        setup_hardware_scanner(scanner_entry, self.scanner_var, self._on_scan)

        controls = ttk.Frame(bar)
        controls.grid(row=1, column=1, sticky=tk.E, padx=(10, 0))
        ttk.Combobox(
            controls, textvariable=self.print_var, values=["print", "pdf"],
            state="readonly", width=8, justify="center",
        ).pack(side=tk.LEFT, ipady=FIELD_IPADY, padx=(0, 8))
        ttk.Button(controls, text="Clear", command=self._on_clear, width=8).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(controls, text="History", command=self._open_history, width=10).pack(side=tk.LEFT, padx=(0, 8))

    def _on_clear(self) -> None:
        """Clear only the scanner input."""
        self.scanner_var.set("")

    def _open_history(self) -> None:
        open_scan_history(
            self.root,
            print_mode=self.print_var.get(),
            variant=self.variant_var.get(),
            origin="pack_id",
        )

    def _apply_permissions(self) -> None:
        
        if self._category_combo is not None:
            set_combobox_enabled(self._category_combo, self.is_admin)
        if self._variant_combo is not None:
            set_combobox_enabled(self._variant_combo, self.is_admin)
        if self._cell_mfr_combo is not None:
            set_combobox_enabled(self._cell_mfr_combo, self.is_admin)

    def _param_value(self, key: str) -> str:
        widget = self._param_labels.get(key)
        if widget is None:
            return "NA"
        return str(widget.cget("text"))

    def _mfg_date_for_serial(self, serial_number: str) -> str:
        parsed = parse_serial_number(serial_number)
        if parsed is None:
            return ""
        return parsed.format_date()

    def _label_mfg_date_for_serial(self, serial_number: str) -> str:
        parsed = parse_serial_number(serial_number)
        if parsed is None:
            return ""
        date_format = "%Y" if self.category_var.get().strip().lower() == "export" else "%d %m %Y"
        return parsed.as_date.strftime(date_format)

    def _store_serial_if_present(self) -> None:
        serial_number = self.serial_number_var.get().strip()
        if serial_number:
            save_pack_serial(serial_number)

    def _print_label(self, serial_number: str) -> bool:
        category = self.category_var.get()

        pack_qr_data = format_pack_qr_data(
            variant=self.variant_var.get(),
            serial_number=serial_number,
            cell_mfr=self.cell_mfr_var.get(),
        )

        zpl = build_hv_pack_id_label(
            serial_number=serial_number,
            rated_capacity=self._param_value("rated_capacity"),
            max_voltage=self._param_value("max_voltage"),
            type_of_reess=self._param_value("model_number"),
            tac_number=self._param_value("tac_number"),
            variant=self.variant_var.get(),
            category=category,
            mfg_date=self._label_mfg_date_for_serial(serial_number),
            pack_qr_data=pack_qr_data,
            cell_mfr=self.cell_mfr_var.get(),
        )
        self._store_serial_if_present()
        dispatch_zpl(
            self.root,
            zpl,
            self.print_var.get(),
            default_name=f"pack_no_{serial_number}.zpl",
            printer_name=PRINTER_PACK_ID,
        )
    
        now = datetime.now()
        machine = get_machine_details()
        pw = self._session.excel_password if hasattr(self, "_session") and self._session else "06082003"
        record = PackIdScanRecord(
            date=self._mfg_date_for_serial(serial_number),
            time=now.strftime("%I:%M:%S %p"),
            serial_number=serial_number,
            variant=self.variant_var.get(),
            pack_qr_data=pack_qr_data,
            machine_name=machine["machine_name"],
            machine_id=machine["machine_id"],
        )
        try:
            append_pack_id_scan_record(record, excel_password=pw)
        except Exception as exc:
            try:
                send_pack_id_scan(record)
            except requests.exceptions.RequestException as api_exc:
                print("Request failed:", api_exc, parent=self.root)
            show_log_recovery_dialog(
                self.root,
                exc,
                retry_save=lambda: append_pack_id_scan_record(record, excel_password=pw),
                on_saved=lambda: self.root.after(1000, self._reset_fields),
                on_continue=lambda: self.root.after(1000, self._reset_fields),
            )
            return False
        try:
            send_pack_id_scan(record)
        except requests.exceptions.RequestException as e:
                print("Request failed:", e, parent=self.root)
        return True

    def _reset_fields(self) -> None:
        self.scanner_var.set("")

    def _on_scan(self, raw: str) -> None:
        if not raw:
            return

        result = identify_scan(raw)
        self.scanner_var.set(result.raw)

        if result.scan_type == ScanType.SERIAL_NUMBER and result.serial is not None: # serial number is accepted, only dummy pack id is accepted
            # if result.pack_variant is None or result.cell_mfr is None:
            #     self.scanner_var.set("")
            #     messagebox.showwarning(
            #         "Scan", "Serial Number scanned. Expecting a Pack QR or bmb_cmb code.", parent=self.root
            #     )
            #     return

            self.scanner_var.set("")  
            self._apply_serial_configuration(result.serial)
            # Always trigger a parameter refresh (covers bare serial scans too)
            self.scanner_var.set("")

            # Auto-print the label, then reset fields after a brief preview delay
            if self._print_label(result.serial.raw):
                self.root.after(1000, self._reset_fields)
            return

        # if result.scan_type == ScanType.MODULE_ID:
        #     messagebox.showwarning(
        #         "Scan",
        #         "This is Module id, Scan Dummy Pack id.",
        #         parent=self.root,
        #     )
        #     return
        
        else:
            messagebox.showwarning(
                "Scan",
                "Unrecognized code. Scan the Dummy Pack id.",
                parent=self.root,
            )
            self.scanner_var.set("") # resets Scan box for invalid entry
            

    def run(self) -> None:
        self.root.mainloop()


def open_battery_pack_id(parent: tk.Tk | tk.Toplevel | None = None) -> BatteryPackIdGUI:
    return BatteryPackIdGUI(parent)


if __name__ == "__main__":
    BatteryPackIdGUI().run()