## Project Structure

```
HV_LABEL_NEW
│   .gitignore
│   hv_main.spec                          # PyInstaller spec (.exe build, icon = assets/logo.ico)
│   install_fonts.py
│   main.py                               # Application entry point (logo, navigation, login)
│   README.md
│   test.py
│   updates.md
│                
├───common
│   │   login_screen.py
│   │   paths.py
│   │   storage.py                       # Local SQLite database
│   │   
│   ├───auth
│   │   │      machine_lock.py               # Machine Authorization
│   │   │   session.py                    # Login session state
│   │   │   user_store.py                 # Admin user credentials
│   │   │   __init__.py           
│   │           
│   ├───data
│   │       .gitkeep
│   │       app_data.db                   # User accounts
│   │       
│   ├───nomenclature
│   │   │   serial_number.py              # Common Serial number nomenclature (applicable to all)
├───models
│   ├───hv
│   │   │   app.py                        # main application Window (HV) 
│   │   │   
│   │   ├───assets
│   │   │       logo.ico                  # Header logo           
│   │   │       logo.png                  # .exe / window icon
│   │   │       
│   │   ├───data
│   │   │       .gitkeep
│   │   │       bms_scan_log.xlsx
│   │   │       pack_id_scan_log.xlsx
│   │       pack_session.db
│   │   │       scan_log.xlsx
│   │   │       
│   │   ├───gui
│   │   │   │   admin_settings_dialog.py
│   │   │   │   auth_bar.py
│   │   │   │   auth_dialog.py
│   │   │   │   battery_pack_dummy.py     # Battery Pack Dummy ID screen
│   │   │   │   battery_pack_id.py        # Battery Pack ID screen
│   │   │   │   battery_parameters.py     # Shared battery parameters panel
│   │   │   │   bms_id.py                 # BMS ID screen
│   │   │   │   category_controls.py      # Domestic/export category + variant binding
│   │   │   │   constants.py              # Variant params, model prefixes, pack QR builder
│   │   │   │   dummy_id.py               # Dummy id Manual Screen (Serial number only)
│   │   │   │   layout.py                 # Shared fonts, spacing helpers
│   │   │   │   permissions.py            # Enable/disable widgets based on admin role
│   │   │   │   print_actions.py          # Print/save ZPL dispatch
│   │   │   │   scanner.py                # Hardware scanner input binding
│   │   │   │   scan_apply.py             # Apply parsed module ID fields to GUI vars
│   │   │   │   scan_history.py           # Scanned Entries History Screen
│   │   │   │   __init__.py
│   │   │           
│   │   ├───nomenclature
│   │   │   │   bms_id.py                 # BMS ID / BMS QR parsing
│   │   │   │   module_id.py              # Module ID parsing/building
│   │   │   │   scan_handler.py           # Unified scan classifier (module/serial/BMS)
│   │   │   │   serial_number.py          # Pack serial number parsing/building
│   │   │   │   __init__.py
│   │   │           
│   │   ├───printing
│   │   │   │   constants.py              # Printer names, label sizes, DPI
│   │   │   │   labels.py                 # High-level label builders
│   │   │   │   spooler.py                # Raw ZPL → Windows printer (ctypes/winspool)
│   │   │   │   zpl.py                    # ZPL label templates (3 fixed sizes)
│   │   │   │   __init__.py
│   │   │           
│   │   ├───session
│   │   │   │   bms_scan_log.py           # BMS ID excel sheet with scan history
│   │   │   │   pack_id_scan_log.py       # Pack ID Excel with Scan history
│   │   │   │   pack_store.py             # Persisted pack serial number + auto-increment
│   │   │   │   paths.py                  # file paths
│   │   │   │   scan_log.py               # scan log entry file for all screens
│   │   │   │   __init__.py
```

---

## Building the .exe

```
pyinstaller hv_main.spec
```

Produces `dist/HV_LABEL_PRINTER.exe` with the ULTRAVIOLETTE logo as the application
icon, bundling `assets/` and `data/`.

---

## Requirements

- Windows (raw ZPL printing uses the Windows print spooler API)
- Python 3.14
- Tkinter (bundled with standard Python on Windows)
- Pillow (for logo image handling, if regenerating `assets/logo.ico`)
- Three Zebra ZD421 printers installed with ZPL drivers, named as above

# created by Anil D