# Code Logic Documentation

This document explains the main coding logic in the project file by file.

---

## File: `main.py`

Purpose:
- Application entry point.
- Validates machine authorization.
- Launches the Tkinter root window and loads the main screen selector.

Main logic:
- `is_authorized()` checks whether the current Windows machine is in the allowed list.
- If not authorized, the app hides the main window and shows a warning dialog, then exits.
- `root = tk.Tk()` creates the UI root.
- `root.title("HV Label Printer — ULTRAVIOLETTE AUTOMATIVE")` sets the window title.
- `Session()` creates the login/session object.
- `HVApp(root, session=session).pack(fill=tk.BOTH, expand=False)` loads the main app frame.
- `_install_error_dialog(root)` attaches a global exception handler for debug crash reporting.

Why it matters:
- This file controls startup security and initial app bootstrapping.

---

## File: `common/auth/machine_lock.py`

Purpose:
- Machine-level authorization using the Windows machine GUID.

Main logic:
- `_raw_machine_id()` reads the Windows registry value `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography\MachineGuid`.
- `get_machine_hash()` hashes the machine GUID using SHA-256.
- `is_authorized()` compares the hash against `AUTHORIZED_HASHES`.
- If the current machine hash is present, the app is allowed to run.

Why it matters:
- This prevents the software from running on unauthorized devices.

---

## File: `common/auth/session.py`

Purpose:
- Maintains the current login session and user access state.

Main logic:
- `Session.__init__` initializes `username`, `role`, and internal password storage.
- `is_admin` returns `True` if the user role is admin/operator in this app design.
- `is_main_admin` is true only for the real admin role.
- `role_label` converts the role into human-readable text.
- `login(username, password, role)` stores user session details.
- `logout()` clears the active session.

Why it matters:
- All screen permissions and admin actions rely on this session instance.

---

## File: `common/auth/user_store.py`

Purpose:
- Local credential and role management for app users.

Main logic:
- Uses `common/data/app_data.db` for local SQLite storage.
- Imports existing users from `users.json` once on first use.
- `_hash_password(password, salt)` creates a salted SHA-256 hash.
- `_seed_default_admin_if_empty()` creates a default admin account if no users remain after migration.
- `authenticate_user(username, password)` validates username/password and returns `(success, message, role)`.
- `add_user(...)` creates a new user with a hashed password and role.
- `delete_user(...)` removes users while protecting the last admin account.

Why it matters:
- All login and user management actions in the UI rely on this module.

---

## File: `common/login_screen.py`

Purpose:
- Basic login form widget.

Main logic:
- `LoginScreen` extends `ttk.Frame`.
- It creates username/password entries and a login button.
- `_submit()` calls `authenticate_user(...)`.
- On success, it triggers `on_success(username, password, role)` and closes the form.

Why it matters:
- This is a reusable login UI for local authentication.

---

## File: `common/paths.py`

Purpose:
- Common base path resolution for repository resources.

Main logic:
- `get_common_base_dir()` returns the project root when running from source, or the executable folder when frozen.

Why it matters:
- Prevents path issues across packaging and local execution.

---

## File: `common/nomenclature/serial_number.py`

Purpose:
- Defines the serial-number generation and parsing logic for the project’s active new format only.

Main logic:
- `NEW_PLANT_CODES`, `MODEL_CODES`, `CATEGORY_CODES_NEW`, and `CELL_MFR_CODES_NEW` define the production code maps used by the new format.
- New serials encode the cell manufacturer as P=Molical, Q=Samsung, R=BAK, S=EVE, T=LG, and U=Ten Power; legacy shift-coded serials remain parseable.
- `ParsedSerialNumber` stores plant, line, date, serial count, and the model/variant/category/cell-manufacturer metadata specific to the new scheme.
- `build_serial_number(...)` generates serials in the project’s current format using plant, model, variant, category, cell manufacturer, and serial count.
- `parse_serial_number(value)` validates and parses only the active new format for the current workflow.
- Validation ensures plant, line, date, category, cell manufacturer, and serial count are consistent.

Why it matters:
- This is the backbone of all pack serial generation and validation under the current production rules.

---

## File: `models/hv/app.py`

Purpose:
- Main application window and screen router.

Main logic:
- `SCREENS = { ... }` maps screen names to GUI classes:
  - `Battery Pack Dummy ID`
  - `Battery Pack ID`
  - `BMS ID`
  - `Dummy ID (manual)`
- `HVApp.__init__` builds the top navigation bar, logo, auth bar, screen selector, and content host.
- `_show_screen()` destroys the current frame and instantiates the selected screen class.
- `_on_auth_change()` rebuilds the UI when the user logs in or logs out.

Why it matters:
- This is the controller for screen switching and session-driven UI refresh.

---

## File: `models/hv/gui/constants.py`

Purpose:
- Central lookup tables for variants, model numbers, REESS codes, battery params, and QR-building logic.

Main logic:
- `VARIANT_OPTIONS = ["12P", "16P", "24P", "27P"]`
- `VARIANT_TO_MODEL_BY_CELL_MFR` and `REESS_BY_MODEL_BY_CELL_MFR` select model and REESS numbers by cell manufacturer and variant; BAK and Ten Power have separate mappings.
- `format_pack_qr_data(variant, serial_number, cell_mfr)` builds a manufacturer-specific `REESS:SERIAL` payload.
- `get_type_of_reess(variant, cell_mfr)` returns the REESS number for that manufacturer and variant.
- `variants_for_category(category)` returns valid variants for Domestic vs Export.
- `SRB_BY_VARIANT` and `get_srb_code(...)` supply SRB values for label text.

Why it matters:
- Almost every screen and label generator depends on this file for configuration values.

---

## File: `models/hv/gui/layout.py`

Purpose:
- Shared font, spacing, and Tkinter style configuration.

Main logic:
- Defines constants like `LABEL_FONT`, `FIELD_FONT`, `DISPLAY_FONT`, `HEADING_FONT`.
- `configure_styles(root)` customizes themed widget appearance and `Plain.TEntry` styling.
- `configure_equal_columns(frame, count)` ensures uniform column sizing.
- `add_field_cell(...)` simplifies layout for forms.

Why it matters:
- This keeps the UI consistent across all screens.

---

## File: `models/hv/gui/permissions.py`

Purpose:
- Enabling/disabling widgets based on admin rights.

Main logic:
- `set_combobox_enabled(combo, enabled)` toggles a combobox between readonly and disabled states.
- `set_entry_enabled(entry, enabled)` toggles manual entry availability.
- `set_button_enabled(button, enabled)` toggles button state.

Why it matters:
- Important for role-based restrictions.

---

## File: `models/hv/gui/scanner.py`

Purpose:
- Binds scanner input to a Tkinter entry field.

Main logic:
- `setup_hardware_scanner(entry, variable, on_scan)` assigns a Return key callback.
- When the user scans and presses Enter, the code reads `variable.get()`, strips spaces, and calls `on_scan(scanned)`.
- It returns `"break"` to stop the event from doing default behavior.

Why it matters:
- This is how the production scanner feeds data into the app.

---

## File: `models/hv/gui/print_actions.py`

Purpose:
- Wraps label printing and saving logic.

Main logic:
- `dispatch_zpl(parent, zpl, mode, ...)` either:
  - sends the raw ZPL to the printer via `send_zpl(...)` if mode is `print`
  - opens a save-as dialog if mode is `pdf`
- `save_zpl(...)` writes the ZPL text to a file.
- `dispatch_zpl_batch(...)` handles multiple labels in one batch.

Why it matters:
- This ensures the app can either print directly or save label data for verification.

---

## File: `models/hv/gui/category_controls.py`

Purpose:
- Category-based variant filtering.

Main logic:
- `add_category_field(...)` creates the Category combobox.
- `bind_category_variant(category_var, variant_var, variant_widget, on_variant_update)` listens to changes in category.
- It updates the list of valid variants for the selected category and resets the variant if needed.
- Calls `on_variant_update()` so dependent fields refresh automatically.

Why it matters:
- Domestic/export rules are enforced centrally here.

---

## File: `models/hv/gui/battery_parameters.py`

Purpose:
- Creates the shared battery metadata panel for several screens.

Main logic:
- `build_battery_parameters_panel(...)` builds a section showing key battery fields.
- It creates labels for values such as:
  - Rated Capacity
  - Max Voltage
  - Model Number
  - TAC Number
- `set_battery_parameters(...)` fills the values into the labels.
- It switches the label text for export categories if `E-Marking` is used instead of TAC.

Why it matters:
- Battery metadata display is reused across multiple screens.

---

## File: `models/hv/gui/auth_bar.py`

Purpose:
- Shows login/logout/status and admin controls in the app top bar.

Main logic:
- `AuthBar.refresh()` changes the visible controls based on the session.
- If logged in, it shows Logout and optional Settings for admin.
- `_maybe_notify_unacknowledged()` triggers a one-time popup when an admin has unacknowledged issue entries.
- `_handle_login()` stores the session and triggers the app refresh.

Why it matters:
- This is the user state switchboard for the whole application.

---

## File: `models/hv/gui/auth_dialog.py`

Purpose:
- Login dialog and user-management dialog.

Main logic:
- `LoginDialog` collects username/password and calls `authenticate_user(...)`.
- `ManageUsersDialog` lists existing users and allows add/remove actions.
- It uses `add_user`, `delete_user`, and `list_users` from the credential store.

Why it matters:
- Admins can manage local operator accounts without editing JSON files directly.

---

## File: `models/hv/gui/admin_settings_dialog.py`

Purpose:
- Central admin dashboard for defect logs, messages, BMS scan log, and pack ID scan log.

Main logic:
- Builds tabs for:
  - Manage Users
  - Defect Log
  - Messages
  - BMS Scan Log
  - Pack ID Scan Log
- `_populate(...)` loads records and displays them in a `ttk.Treeview`.
- `_save_ack(...)` writes admin acknowledgment into the Excel defect log.
- It calls `load_unacknowledged_issues()`, `load_all_records_with_rows()`, and log openers for Excel files.

Why it matters:
- This is the management console for production issue tracking and user administration.

---

## File: `models/hv/gui/battery_pack_dummy.py`

Purpose:
- Main dummy-pack assembly workflow: scan four module IDs, validate, build QR, and print the pack label.

Main logic:
- The screen maintains four module slots: `M1` to `M4`.
- `setup_hardware_scanner(...)` captures raw scanner input.
- `_on_scan(raw)` detects module IDs using `identify_scan()`.
- It validates:
  - variant consistency
  - plant consistency
  - part number consistency
  - export category constraints
- `_try_complete_integration()` runs when all four modules are scanned and checks whether all are the same variant and plant.
- It creates the generated pack QR using `format_pack_qr_data(...)` with the active new serial scheme.
- `_auto_print_and_reset()` logs the record, prints the label, increments the serial, and resets the module slots.
- It persists the current serial in the project’s local session storage.

Why it matters:
- This is the main production pack-building and validation workflow.

---

## File: `models/hv/gui/battery_pack_id.py`

Purpose:
- Battery Pack ID scanning and label generation.

Main logic:
- Builds configuration row for category and variant.
- `setup_hardware_scanner` listens for a pack QR scan.
- `_on_scan(...)` identifies the input as a serial/pack QR and populates the label fields.
- The program calls `build_battery_pack_id_label(...)` to generate a pack ID label.
- It saves the serial to local storage and logs the scan result.
- `dispatch_zpl(...)` sends the label to the correct printer or saves as text if mode is PDF.

Why it matters:
- This handles the full battery pack identification print flow.

---

## File: `models/hv/gui/bms_id.py`

Purpose:
- BMB/CMB scan and rework logic.

Main logic:
- The screen captures pack QR, BMB ID, and CMB ID.
- `_on_scan(raw)` classifies incoming values using `identify_scan()`.
- If a pack QR is recognized, it initializes the pack context.
- If the app is in rework mode, it patches the existing record and updates the rework fields.
- `_check_and_print()` prints the BMS label once both BMB and CMB IDs are valid.
- `patch_rework(...)` updates the Excel log for rework records.

Why it matters:
- This screen handles a second production label flow and rework corrections.

---

## File: `models/hv/gui/dummy_id.py`

Purpose:
- Manual fallback flow for pack ID scanning and dummy-label generation.

Main logic:
- `DummyIdGUI._on_serial_submitted(...)` validates a serial number and pops a details dialog.
- `_print_dummy_label(...)` creates a dummy label using the parsed serial data.
- It builds battery parameters and logs the entry in the scan log.
- This flow is a manual alternative to the main pack dummy process.

Why it matters:
- Useful when a full module-scan workflow is not needed or is unavailable.

---

## File: `models/hv/gui/scan_apply.py`

Purpose:
- Mapping parsed scan results into Tkinter variables.

Main logic:
- `apply_serial_fields(vars_map, parsed)` writes plant, line, serial_count, and date to widgets.
- `apply_module_fields(vars_map, parsed)` writes variant, plant, line, shift, and cell manufacturer.
- `format_date_display(value)` converts a Python date into a user-friendly display string.

Why it matters:
- Keeps UI state synchronized with parsed QR/serial data.

---

## File: `models/hv/gui/scan_history.py`

Purpose:
- Display and reprint previous scan records.

Main logic:
- Loads records from dummy, pack ID, and BMS logs.
- Displays them in a `ttk.Treeview` table with reprint buttons.
- `_on_reprint()` picks the selected row and recreates the original ZPL label using saved values.
- `_check_file_modified()` auto-refreshes the table when the Excel log file changes.

Why it matters:
- This gives operators a traceability and reprint interface.

---

## File: `models/hv/nomenclature/serial_number.py`

Purpose:
- Project-level re-export of the serial-number logic.

Main logic:
- Imports the actual parsing functions from `common/nomenclature/serial_number.py`.
- Re-exposes them as part of the `models.hv.nomenclature` namespace for easier access across screens.

Why it matters:
- It acts as a compatibility wrapper for the serial logic module.

---

## File: `common/nomenclature/serial_number.py`

Purpose:
- Actual serial-number generation/parsing engine for the project’s current production format.

Main logic:
- Contains code maps for plants, models, categories, cell manufacturers, and the active new-format rules.
- `build_serial_number(...)` builds serials using the project’s active new scheme.
- `parse_serial_number(...)` validates and parses the active format used by the app.
- Date checks and code conversion logic are embedded here.

Why it matters:
- This is the actual root logic for the serial-number rules used in production.

---

## File: `models/hv/nomenclature/module_id.py`

Purpose:
- Parse and build module ID strings.

Main logic:
- Uses a regex to decode module format patterns like `VX156610-E1611109G260076`.
- `ParsedModuleId` stores fields such as `variant`, `group`, `cell_mfr`, `plant`, `line`, `shift`, and `serial`.
- `build_module_sub_id(...)` and `build_full_module_id(...)` generate QR/module strings from parameters.
- `parse_module_id(value)` validates and extracts structured details.

Why it matters:
- This is what converts a scanned module QR into structured data for validation and comparison.

---

## File: `models/hv/nomenclature/bms_id.py`

Purpose:
- Handles BMB/CMB ID parsing and BMS QR parsing.

Main logic:
- `parse_bmb_cmb_id(value)` recognizes BMB/CMB IDs like `VQ150720-...` and `VQ150710-...`.
- `short_bmb_cmb_id(raw)` extracts the final 9-digit identifier.
- `parse_bms_id(value)` validates numeric BMS IDs.
- `parse_bms_qr(value)` parses combined BMS QR payloads.

Why it matters:
- This allows scanning and validation of BMS-related codes.

---

## File: `models/hv/nomenclature/scan_handler.py`

Purpose:
- Central classifier for all scanner inputs.

Main logic:
- `ScanType` enumerates recognized input types: serial number, module ID, BMB ID, CMB ID, BMS ID, unknown.
- `identify_scan(value)` inspects a raw code and returns a structured result with fields like `serial`, `module`, `bmb_cmb`, `bms_id`.
- It validates pack QR patterns of the form `REESS:serial` and maps them to a variant.

Why it matters:
- This file is the gateway that decides what type of input the app is receiving.

---

## File: `models/hv/printing/constants.py`

Purpose:
- Printer configuration constants.

Main logic:
- Defines printer names used for label output:
  - `PRINTER_NAME`
  - `PRINTER_DUMMY`
  - `PRINTER_PACK_ID`
  - `PRINTER_BMS_ID`
- Contains label dimensions and print geometry constants.

Why it matters:
- All ZPL printing targets a configured printer.

---

## File: `models/hv/printing/spooler.py`

Purpose:
- Raw Windows print submission through the WinSpool API.

Main logic:
- `_resolve_printer_name(printer_name)` finds the actual installed printer name, with a fuzzy fallback.
- `send_zpl(zpl, printer_name)` uses `ctypes.WinDLL("winspool.drv")` to open the printer and write raw ZPL bytes.
- It calls `StartDocPrinterW`, `StartPagePrinter`, `WritePrinter`, `EndPagePrinter`, `EndDocPrinter`, and `ClosePrinter`.
- `save_zpl(zpl, path)` writes label data to a file.

Why it matters:
- This is the low-level communication layer between Python and Zebra printers.

---

## File: `models/hv/printing/labels.py`

Purpose:
- High-level label builder that selects the correct ZPL function for each label type.

Main logic:
- `build_hv_module_label(...)` chooses domestic/export module label generation.
- `build_pack_qr_label(...)` builds a QR label with pack metadata.
- `build_battery_pack_id_label(...)` creates the battery pack ID label with capacity, voltage, QR, and serial info.
- `build_bmb_cmb_combined_label(...)` and `build_bms_id_label(...)` route to the BMS-specific ZPL builders.

Why it matters:
- It abstracts raw ZPL generation into clean application-level label functions.

---

## File: `models/hv/printing/zpl.py`

Purpose:
- Raw ZPL string generation for all label templates.

Main logic:
- Uses Zebra commands such as:
  - `^XA`, `^XZ` for label boundaries
  - `^FO` for field origin
  - `^A` for text
  - `^BQN` for QR barcodes
  - `^GB` and `^GFA` for graphics and shapes
- Helper functions sanitize data and format labels.
- Each function generates a complete label string for a specific type, such as:
  - module label
  - pack label
  - BMB/CMB label
  - BMS label
  - battery pack ID label

Why it matters:
- This is the actual code that creates Zebra-printable label commands.

---

## File: `models/hv/session/paths.py`

Purpose:
- Base path resolver for app runtime data folders.

Main logic:
- `get_base_dir()` resolves the local application data directory from the project path or frozen executable path.

Why it matters:
- Used by Excel log and JSON session persistence modules.

---

## File: `models/hv/session/pack_store.py`

Purpose:
- Save and load pack serial state using SQLite.

Main logic:
- Stores pack serial state in `models/hv/data/pack_session.db`.
- Imports existing state from `pack_session.json` and the previous shared `app_data.db` once on first use.
- `save_pack_serial(...)` stores the latest serial.
- `load_pack_serial()` reads the last serial used.
- `increment_pack_serial()` increases the serial count and writes the next serial.
- This turns serial generation into a persistent, stateful production counter.

Why it matters:
- The project keeps the current production count and next serial in a dedicated local SQLite database.

---

## File: `models/hv/session/scan_log.py`

Purpose:
- Dummy pack history / defect log stored in Excel.

Main logic:
- Defines `ScanRecord` dataclass containing all pack fields.
- `append_scan_record(...)` appends new records to `scan_log.xlsx`.
- `_ensure_workbook(...)` creates and repairs the workbook structure.
- `load_all_records_with_rows()` and `load_unacknowledged_issues()` read the sheet back for admin review.
- `patch_admin_ack(...)` updates the admin acknowledgment field.

Why it matters:
- This is the audit trail and operational defect log for the dummy pack flow.

---

## File: `models/hv/session/pack_id_scan_log.py`

Purpose:
- Stores battery pack ID scans in Excel.

Main logic:
- `PackIdScanRecord` dataclass captures date, time, serial number, variant, and pack QR.
- `append_scan_record(...)` writes a row to `pack_id_scan_log.xlsx`.
- `load_all_records()` reads all records back for history or reprint.
- `open_log_file()` opens the workbook in Excel.

Why it matters:
- This gives traceability for the pack ID label flow.

---

## File: `models/hv/session/bms_scan_log.py`

Purpose:
- Stores BMB/CMB scan log and rework entries.

Main logic:
- `BmsScanRecord` tracks pack QR, BMB, CMB, and any rework IDs.
- `append_scan_record(...)` writes the record to `bms_scan_log.xlsx`.
- `patch_rework(pack_qr_data, kind, value)` updates the rework fields for an existing log entry.
- `find_record_by_pack_qr(...)` locates the record by pack QR.
- `load_rework_records()` filters only reworked entries.

Why it matters:
- This allows rework tracking and corrected printing of BMS labels.

---

## Minor utility files

The following files mainly expose package imports and do not contain significant standalone logic:

- `common/auth/__init__.py`
- `common/__init__.py` (if present)
- `models/hv/__init__.py`
- `models/hv/gui/__init__.py`
- `models/hv/nomenclature/__init__.py`
- `models/hv/printing/__init__.py`
- `models/hv/session/__init__.py`

These files are mostly package markers for Python imports and do not define business logic.

---

## Overall architecture summary

The project is organized around a few core ideas:

1. UI layer
   - Tkinter screens in `models/hv/gui/`
2. Business logic layer
   - scan parsing and validation in `models/hv/nomenclature/`
   - serial generation logic in `common/nomenclature/serial_number.py`
3. Printing layer
   - label generation in `models/hv/printing/labels.py` and `models/hv/printing/zpl.py`
   - raw Windows printer submission in `models/hv/printing/spooler.py`
4. Persistence layer
   - JSON state in `models/hv/session/pack_store.py`
   - Excel logs in `models/hv/session/*.py`
5. Security and session layer
   - machine lock and user authentication in `common/auth/`

This is a specialized production-floor battery label tool built for controlled local Windows operation, barcode scanning, printer dispatch, and traceability logging.
