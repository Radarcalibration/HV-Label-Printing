# HV Label Printing.

# main.py
Functions:
- `_base_dir()`: finds the working directory for the app so files and resources resolve correctly.
- `_install_error_dialog()`: shows a message in specified format if the app fails to start because of missing printer or runtime setup.
- `_report()`: prints startup errors to the console or log output for debugging.
- `main()`: creates the window, runs the auth check, and starts the HV application loop.

# install_fonts.py
Functions:
- `_build_du_payload(font_bytes, printer_filename)`: converts font bytes into a Zebra printer upload payload with the ~DU command format.
- `send_zpl_bytes(payload, printer_name)`: sends the generated font package to the target Zebra printer.
- `main()`: runs the one-time printer font installation flow.

# common/paths.py
Functions:
- `get_common_base_dir()`: resolves the shared project path for data files, logs, and local database files.

# common/storage.py
Functions:
- `connect_db()`: creates or opens the SQLite database and creates the users and app_state tables if they do not exist.

# common/nomenclature/serial_number.py
Classes:
- `ParsedSerialNumber`: stores a parsed serial number and its extracted fields such as plant, model, date, category, and cell manufacturer.
Functions:
- `is_export()`: detects export category values.
- `as_date()`: converts the embedded date into a Python date object.
- `format_date()`: returns a readable date string for labels and logs.
- `build_serial_number()`: creates a serial number from component values.
- `build_serial_number_for_model()`: builds a serial number for a specific model and letter code.
- `_parse_serial_number()`: extracts the serial number fields.
- `parse_serial_number()`: entry point that reads a raw serial string and returns a ParsedSerialNumber object.

# common/auth/__init__.py
- Package marker for auth-related code.
- No logic by itself. It helps import the auth modules cleanly.

# common/auth/machine_lock.py
Functions:
- `_raw_machine_id()`: reads the Windows machine identifier from the system.
- `get_machine_hash()`: hashes that value so it can be compared safely against allowed machines.
- `is_authorized()`: checks the current machine against the allowed list and blocks unauthorized startup.

# common/auth/session.py
Class:
- `Session`: stores the current login state. It keeps the username, password, role, and whether the session is admin.
Functions:
- `__init__()`: creates the session object with default empty values.
- `is_admin()`: checks if the logged-in user has admin rights.
- `is_main_admin()`: checks if the user is the default or primary admin account.
- `role_label()`: returns a readable label for display in the UI.
- `excel_password()`: resolves the workbook password used for Excel log reads and writes.
- `login()`: sets the active user and role after a successful login.
- `logout()`: clears the active user state.

# common/auth/user_store.py
Functions:
- `_hash_password(password, salt)`: creates a salted hash for storing passwords securely.
- `_import_legacy_users()`: reads older user records into the new format so upgrades do not break existing accounts.
- `_seed_default_admin_if_empty()`: creates an initial admin user when no users exist yet.
- `authenticate_user(username, password)`: verifies login details and returns the matched user or None.
- `list_users()`: returns all local users for the admin management screen.
- `get_user_role(username)`: reads the role assigned to a account.
- `add_user(username, password, role)`: creates a new user record.
- `delete_user(username)`: removes a user record.

# common/login_screen.py
Class:
- `LoginScreen`: builds the login form used at startup.
Functions:
- `__init__()`: creates the Tk widgets for username, password, and login action.
- `_submit()`: validates entered credentials and starts the active session if valid.

# models/hv/app.py
Class:
- `HVApp`: is the main application shell.
Functions:
- `__init__()`: sets up the main window, session state, and top-level screen container.
- `open_lv_printer()`: opens the LV printer screen flow when the user selects it.
- `open_shockwave_printer()`: opens the shockwave label flow.
- `open_tesseract_printer()`: opens the tesseract-related screen flow.
- `_resource_path()`: resolves resource paths for the packaged app.
- `_show_screen()`: swaps the visible screen inside the main app window.
- `_on_auth_change()`: reacts when login state changes and refreshes the top bar and allowed actions.

# models/hv/gui/__init__.py
- Package marker for the GUI screens.
- No logic on its own. It keeps the screen modules grouped together.

# models/hv/gui/auth_bar.py
Class:
- `AuthBar`: shows login status, logout, and admin controls in the app bar.
Functions:
- `__init__()`: builds the top bar and binds it to session state.
- `refresh()`: redraws the current login status after change.
- `_maybe_notify_unacknowledged()`: warns the user when a log has unacknowledged issue records.
- `_open_login()`: opens the login dialog.
- `_open_admin_settings()`: opens the admin settings screen.
- `_handle_login()`: handles successful login and refreshes the UI.
- `_logout()`: logs out the current user and resets UI access.

# models/hv/gui/auth_dialog.py
Classes:
- `_CenteredDialog`: helper base class used to center pop-up windows over the parent form.
- `LoginDialog`: login popup window.
- `ManageUsersDialog`: popup for creating and deleting users.
Functions:
- `__init__()`: creates the dialog window and its fields.
- `_center_over_parent()`: positions the dialog in the center of the main app.
- `_submit()`: validates the credentials entered in the login panel.
- `_refresh_users()`: updates the user list in the management dialog.
- `_on_add()`: creates a new user from the dialog form.
- `_on_delete()`: deletes the selected user account.
- `open_login_dialog()`: helper for the app to open the login dialog from any screen.

# models/hv/gui/admin_settings_dialog.py
Class:
- `AdminSettingsDialog`: admin panel for logs, user management, and issue acknowledgement.
Functions:
- `__init__()`: builds the tabs and reads current log data.
- `_build_manage_tab()`: creates the user management tab.
- `_open_manage_users()`: opens the manage-users popup.
- `_build_bms_log_tab()`: loads the BMS log sheet for review.
- `_build_pack_id_log_tab()`: loads the pack-ID log sheet for review.
- `_build_readonly_log_section()`: creates the read-only log display used by admin review.
- `_populate_readonly()`: fills the log table with the records from Excel.
- `_open_excel_safe()`: opens the workbook file safely, with error handling.
- `_build_defect_section()`: creates the issue review area for the dummy and defect tracking log.
- `_on_select()`: reacts when a user selects an entry from the log tree.
- `_populate()`: loads item details into the selected record screen.
- `_refresh_all()`: reloads all admin views after a change.
- `_save_ack()`: writes acknowledgement updates back to the workbook.
- `open_admin_settings()`: helper to open the dialog from the app.

# models/hv/gui/battery_parameters.py
Functions:
- `build_battery_parameters_panel()`: creates the shared battery parameter area with labels and editable values.
- `set_battery_parameters()`: fills the values into the UI after a pack or module scan.

# models/hv/gui/battery_pack_dummy.py
Class:
- `BatteryPackDummyGUI`: GUI for the dummy pack flow.
Functions:
- `__init__()`: creates the screen and binds it to the session.
- `_init_serial()`: initializes the serial-number rules for the selected screen.
- `_serial_number_kwargs()`: maps serial fields into the accepted arguments for pack creation.
- `_rebuild_and_store_serial()`: rebuilds the serial and stores it back into the database.
- `_build_ui()`: creates the main layout.
- `_build_config_rows()`: builds the row of configuration values shown to the operator.
- `_add_field()`: adds a single input field row.
- `_build_modules_and_integration()`: creates the module scan and integration section.
- `_build_scan_row()`: adds the field for scanning each module.
- `_build_qr_preview()`: shows the generated QR preview.
- `_all_modules_scanned()`: checks whether all required module scans are complete.
- `_m1_variant(), _m1_plant(), _m1_part_number()`: parse module fields used to validate the pack.
- `_clear_modules()`: clears the module fields after a reset.
- `_on_scan()`: handles the scanner event when a QR or serial is scanned.
- `_reset_integration()`: clears integration status after a failed or reset action.
- `_try_complete_integration()`: validates the collected module data and completes the dummy pack result.
- `_collect_extra_fields_then_print()`: gathers extra fields before creating the final label.
- `_on_ok()`: confirms the dummy pack details and prints the label.
- `_on_skip()`: allows skipping a module or validation step.
- `_auto_print_and_reset()`: prints and then resets the screen after a successful scan.
- `_open_history()`: opens the scan-history dialog for this screen.
- `_auto_reset()`: reset timer for the screen after printing.
- `_on_date_edited()`: handles edited date values.
- `_on_variant_or_revision_change()`: rebuilds the serial data when variant or revision changes.
- `_validate_serial_count()`: checks whether a serial count is valid.
- `_on_serial_count_commit()`: commits the serial count and updates the serial line.
- `_on_serial_number_typed()`: handles typing while entering a serial number.
- `_on_serial_number_commit()`: finalizes manual serial entry.
- `_current_date_str()`: returns the current date string for display.
- `_update_vars_from_serial()`: fills the UI values from the parsed serial record.
- `_refresh_datetime()`: refreshes date and time info in the UI.
- `_apply_permissions()`: applies user-role restrictions to sensitive controls.
- `run()`: starts the Tk main loop.
- `open_battery_pack_dummy()`: factory function to create the screen.

# models/hv/gui/battery_pack_id.py
Class:
- `BatteryPackIdGUI`: GUI for the battery pack ID print flow.
Functions:
- `__init__()`: sets up the screen, fields, and print mode.
- `_build_ui()`: creates the pack ID fields and the scanner row.
- `_build_config_row()`: makes the configuration field section for variants and values.
- `_add_config_dropdown()`: adds a combobox for a configuration field.
- `_on_variant_change()`: refreshes battery max voltage, capacity, and labels when the pack variant changes.
- `_build_scanner_section()`: creates a scanner entry and buttons.
- `_on_clear()`: clears the user fields between scans.
- `_open_history()`: opens the scan-history dialog for pack ID records.
- `_apply_permissions()`: restricts controls for the current user role.
- `_param_value()`: reads the value for a battery parameter.
- `_mfg_date_for_serial()`: calculates the date from the serial number.
- `_store_serial_if_present()`: stores the pack serial value when a valid serial is scanned.
- `_print_label()`: builds and sends the label to the printer, then logs the record.
- `_reset_fields()`: clears the screen after printing.
- `_on_scan()`: accepts raw scan input, parses it, and decides whether to print or reject it.
- `run()`: starts the Tk event loop.
- `open_battery_pack_id()`: factory function for the screen.
- `main()`: runs the screen standalone.

# models/hv/gui/bms_id.py
Class:
- `BmsIdGUI`: handles BMB/CMB recording and rework labels.
Functions:
- `__init__()`: sets up fields for pack QR, BMB, and CMB IDs plus rework mode.
- `_build_ui()`: lays out the display and scanner controls.
- `_open_history()`: opens the BMS scan history.
- `_on_rework_toggle()`: turns rework mode on and off.
- `_apply_rework_visibility()`: shows or hides the rework fields.
- `_is_rework()`: returns whether the current flow is rework mode.
- `_on_scan()`: handles pack QR and BMB/CMB scans.
- `_save_rework()`: patches the original log entry with a rework value and prints the corrected label.
- `_check_and_print()`: validates pack QR plus BMB/CMB and sends the combined print job.
- `_reset_display()`: clears all BMS fields after a successful action.
- `run()`: starts the GUI loop.
- `main()`: standalone run helper.

# models/hv/gui/category_controls.py
Functions:
- `add_category_field()`: adds the category selector dropdown to a form.
- `bind_category_variant()`: binds category and variant controls so they update each other.
- `_apply_category_rules()`: updates the allowed variant list when category changes.

# models/hv/gui/constants.py
Functions:
- `year_code()`: converts a year to its code used in serials.
- `year_from_code()`: reads the year back from the code.
- `get_range()`: returns the valid range for a model category.
- `variants_for_category()`: returns the valid variants for the selected category.
- `format_pack_qr_data()`: builds the QR payload for the pack label.
- `get_model_number()`: resolves the model number for a variant.
- `get_part_number()`: returns the part number for the pack.
- `get_full_model_number()`: creates the complete battery model string.
- `get_type_of_reess()`: maps the variant to REESS type information.
- `get_cell_mfr_from_reess()`: reads the cell maker from the REESS code.
- `get_variant_from_reess()`: reverses the REESS mapping.
- `get_tac_number()`: reads the TAC code.
- `get_emark()`: reads the E-mark code.
- `get_rated_capacity()`: resolves the rated capacity.
- `get_max_voltage()`: resolves the max voltage.
- `get_emark_res_code()`: resolves the E-mark resistor code.
- `get_srb_code()`: resolves SRB information.

# models/hv/gui/dummy_id.py
Class:
- `DummyIdGUI`: manual fallback screen for printing dummy pack labels when the full scan flow is not available.
Functions:
- `__init__()`: creates the form and sets up the serial entry field.
- `_build_ui()`: creates the main layout and battery parameter panel.
- `_build_serial_row()`: adds the scan entry and print mode options.
- `_on_serial_submitted()`: validates the scanned serial and opens the detail popup.
- `_open_details_popup()`: asks the operator for manufacturer, variant, and reference number before printing.
- `_on_ok()`: validates the popup values and triggers the print action.
- `_on_cancel()`: clears the popup and resets the scan field.
- `_print_dummy_label()`: builds the dummy label, sends it to the printer, and saves the log record.
- `_open_history()`: opens the dummy scan-history window.
- `open_dummy_id()`: factory function for the GUI.

# models/hv/gui/layout.py
Functions:
- `configure_styles()`: sets a common Tk theme for entries, comboboxes, and spacing.
- `configure_equal_columns()`: makes columns line up evenly inside a frame.
- `add_field_cell()`: creates a labeled widget cell used across screens.

# models/hv/gui/permissions.py
Functions:
- `set_combobox_enabled()`: toggles a combobox between editable and disabled states.
- `set_entry_enabled()`: toggles an entry widget on or off.
- `set_button_enabled()`: toggles a button state for user-role control.

# models/hv/gui/print_actions.py
Functions:
- `add_print_controls()`: adds print and PDF-save controls to a form.
- `dispatch_zpl()`: sends a ZPL label to the printer or saves it as a text file if the user chooses save mode.
- `dispatch_zpl_batch()`: sends multiple ZPL labels in a batch or saves them as one file.

# models/hv/gui/scan_apply.py
Functions:
- `format_date_display()`: turns a date object or serial date into a readable display string.
- `apply_serial_fields()`: fills serial fields into a form after parsing.
- `apply_module_fields()`: fills module fields in a form after parsing.

# models/hv/gui/scan_history.py
Class:
- `ScanHistoryDialog`: reprint and log viewer for packaged labels.
Functions:
- `__init__()`: creates the history window and configures columns per origin.
- `_build_ui()`: builds the tree table, buttons, and status bar.
- `_log_file_for_origin()`: resolves which Excel log belongs to the selected screen.
- `_load_records()`: reads the records and fills the display table.
- `_attr_for()`: maps column IDs to model attribute names.
- `_start_auto_refresh()`: starts a periodic check for new rows in the log file.
- `_check_file_modified()`: compares file timestamps and refreshes the table when new data arrives.
- `_on_close()`: cleans up the refresh timer when the dialog closes.
- `_on_reprint()`: handles selecting a row and choosing which reprint mode to use.
- `_reprint_dummy()`: reprints a dummy pack label from the saved QR data.
- `_reprint_pack_id()`: reprints a pack ID label from the saved pack QR.
- `_reprint_bmb_cmb()`: reprints a BMB/CMB combined label from its saved record.
- `_open_excel()`: opens the log workbook in Excel for support review.
- `_center_over_parent()`: centers the dialog over the parent window.
- `open_scan_history()`: helper to open the dialog from any screen.

# models/hv/gui/scanner.py
Functions:
- `setup_hardware_scanner()`: attaches scanner behavior to a text entry so a scan is submitted after a brief idle delay.
- `_cancel_pending_scan()`: clears the timed submission.
- `_submit_scan()`: sends the raw scanned text to the screen callback.
- `_submit_after_idle()`: fires when inactivity indicates the scan has ended.
- `_schedule_scan()`: listens for key events and decides when to trigger the scanner callback.
- `_ignore_enter()`: blocks the Enter key from inserting a newline in the scan field.

# models/hv/nomenclature/__init__.py
- Package marker for scan and serial-naming logic.
- It groups parser and identifier code into one namespace.

# models/hv/nomenclature/bms_id.py
Classes:
- `ParsedBmbCmbId`: stores BMB or CMB values and short ID versions.
- `ParsedBmsQr`: stores the parsed BMS QR payload.
Functions:
- `parse_bmb_cmb_id()`: reads a raw BMB or CMB identifier and extracts its fields.
- `short_bmb_cmb_id()`: creates the short display ID used on labels.

# models/hv/nomenclature/module_id.py
Class:
- `ParsedModuleId`: stores a parsed module identifier.
Functions:
- `as_date(): converts a module date code into a date object.
- `build_module_sub_id()`: creates the sub-part of the module ID.
- `build_full_module_id()`: assembles the full module code used in QR labels.
- `build_all_module_ids()`: generates all module IDs for a battery pack flow.
- `parse_module_id()`: reads a module QR or code and returns the parsed object.

# models/hv/nomenclature/scan_handler.py
Enum:
- `ScanType`: identifies the type of scanned input: serial number, module ID, BMB ID, CMB ID, or unknown.
Class:
- `ScanResult`: holds the parsed result and optional nested values.
Functions:
- `identify_scan(raw)`: inspects the raw scan and sends it to the correct parser. This is the core router for all scanner input in the app.

# models/hv/nomenclature/serial_number.py
- Thin re-export file for the shared serial-number parser.
- Keeps import paths stable across screens.

# models/hv/printing/__init__.py
- Package marker for printer and ZPL label code.
- No logic itself; it exposes the label modules as a package.

# models/hv/printing/constants.py
- Stores printer names and label-specific constants used across the app.
- Keeps the screen code from hard-coding printer names in multiple places.

# models/hv/printing/labels.py
Functions:
- `_reess_for_pack_qr()`: resolves REESS data while building a pack QR label.
- `build_hv_module_label()`: creates the label for a module scan.
- `build_hv_pack_label()`: creates a pack label for the main HV flow.
- `build_pack_qr_label()`: builds a pack QR label using serial, model, and date data.
- `build_bmb_cmb_combined_label()`: builds the combined BMB/CMB label used in the BMS screen.
- `build_bmb_cmb_label()`: builds a simpler BMB/CMB label when needed.
- `_emark_res()`: resolves the E-mark resistor details for the label.
- `build_battery_pack_id_label()`: builds the battery pack ID label for the dedicated screen.
- `build_scanned_module_label()`: builds a scanned-module label output.
- `get_model_number_for_label()`: resolves the model number for display on the label.

# models/hv/printing/spooler.py
Class:
- `DOCINFO1`: Windows print document metadata used by the print spooler.
Functions:
- `_list_installed_printers()`: lists printers available on the local machine.
- `_resolve_printer_name()`: chooses the right printer name for the active job.
- `send_zpl(zpl, printer_name)`: sends raw ZPL text to the selected Windows printer using the spooler API.
- `save_zpl(zpl, path)`: writes the label data to a file for saving or backup.

# models/hv/printing/zpl.py
Functions:
- `_header()`: adds the common ZPL header and start command.
- `_footer()`: adds the final ZPL end command.
- `_fd()`: formats field data for label text blocks.
- `_type_code_from_model()`: derives the type code for a model.
- `build_hv_module_label_domestic()`: builds a domestic module label.
- `build_hv_module_label_export()`: builds an export module label.
- `build_hv_pack_label_domestic()`: builds the domestic HV pack label.
- `build_bmb_cmb_combined_zpl()`: builds the combined BMB/CMB ZPL string.
- `build_bmb_cmb_zpl()`: builds the BMB/CMB label text.
- `build_pack_qr_zpl()`: builds the raw pack-QR label string.
- `build_battery_pack_id_zpl_unified()`: builds the unified battery pack ID label.
- `build_hv_pack_label_export()`: builds the export HV pack label.

# models/hv/session/__init__.py
- Package marker for session log and storage modules.
- No logic of its own; it keeps the logs and record helpers grouped together.

# models/hv/session/bms_scan_log.py
Class:
- `BmsScanRecord`: stores the BMS log row for one scanned pack and its BMB/CMB values.
Functions:
- `is_reworked()`: checks if a row contains a rework value.
- `as_row()`: converts the record into the dictionary format written to Excel.
- `_ensure_writable()`: makes sure the workbook is writable and protected correctly.
- `_protection()`: returns the password used for workbook protection.
- `_build_header()`: creates the sheet header row for the BMS log.
- `_get_sheet()`: gets or creates the working sheet for the BMS log.
- `_ensure_workbook()`: creates the workbook structure if the log file does not exist.
- `_find_row_by_pack_qr()`: finds an existing row by pack QR so rework data can be patched.
- `append_scan_record()`: writes a new BMS scan record to the Excel log.
- `patch_rework()`: updates a historical row with the corrected BMB or CMB ID.
- `load_all_records()`: returns all BMS records from the Excel log.
- `load_all_records_with_rows()`: returns structured rows with metadata for processing.
- `find_record_by_pack_qr()`: finds a record by pack QR data.
- `load_rework_records()`: loads only rows that were reworked.
- `open_log_file()`: opens the BMS log workbook in Excel.

# models/hv/session/pack_id_scan_log.py
Class:
- `PackIdScanRecord`: stores one pack ID log row.
Functions:
- `as_row()`: converts the record into the row dictionary for Excel.
- `_ensure_writable()`: ensures the workbook is writable before updating it.
- `_protection()`: returns the workbook protection password.
- `_build_header()`: creates the headers for the pack ID sheet.
- `_get_sheet()`: gets the active sheet or creates it.
- `_ensure_workbook()`: makes sure the workbook and sheet exist.
- `append_scan_record()`: writes a pack ID record to Excel.
- `load_all_records()`: reads all saved pack ID records.
- `open_log_file()`: opens the pack-ID log workbook.

# models/hv/session/pack_store.py
Functions:
- `_migration_completed()`: checks whether the SQLite serial migration has already run.
- `_mark_migration_completed()`: marks the migration as finished.
- `_import_shared_database_state()`: imports shared state values from the common database.
- `_import_legacy_json()`: imports legacy JSON serial data if the old format still exists.
- `_connect_db()`: creates a dedicated SQLite connection for serial storage.
- `_load_value()`: reads a stored serial value from the database.
- `_save_values()`: writes a serial value to the database.
- `save_pack_serial(serial)`: stores the newest scanned pack serial.
- `load_pack_serial()`: reads the last saved serial number.
- `load_pack_serial_count()`: reads the numeric serial count from storage.
- `save_pack_serial_count()`: writes the serial count state.
- `increment_pack_serial()`: increases the serial count for the next printed label.

# models/hv/session/paths.py
Functions:
- `get_base_dir()`: resolves the folder used for local session data, logs, and user files.

# models/hv/session/scan_log.py
Class:
- `ScanRecord`: stores a dummy-pack scan record and all defect and issue fields.
Functions:
- `has_issue()`: checks whether the record has an issue description.
- `is_unacknowledged()`: checks whether an admin has not yet acknowledged the issue.
- `as_row()`: returns the Excel row structure for the log.
- `_ensure_writable()`: ensures the workbook can be updated.
- `_protection()`: returns the workbook protection password.
- `_build_header()`: creates the header row for the log table.
- `_get_scan_log_sheet()`: gets or creates the scan log sheet.
- `_ensure_workbook()`: creates the workbook if required.
- `append_scan_record()`: writes a new dummy pack record into Excel.
- `load_all_records_with_rows()`: reads records together with their raw row data.
- `load_all_records()`: reads the saved dummy-pack log records.
- `load_unacknowledged_issues()`: returns only records that still need admin acknowledgement.
- `patch_admin_ack()`: updates the acknowledgment or admin note fields in a record.
- `add_sheet()`: adds an extra sheet if the workbook structure requires it.
- `open_log_file()`: opens the dummy log workbook in Excel.

End