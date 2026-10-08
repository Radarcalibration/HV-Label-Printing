# Battery Management System (BMS) — Label Generation & Printing Tool

A desktop application (Tkinter) used on the production line to scan, validate,
and print labels for battery packs, modules, and BMS units. Each label is
generated as ZPL and sent directly to a dedicated Zebra ZD421 printer.

---

## Overview

The application has three main screens, each tied to its own scanner and
its own physical Zebra printer:

| Screen                  | Purpose                                                                 | Label Size   | Printer                                  |
|--------------------------|--------------------------------------------------------------------------|--------------|-------------------------------------------|
| **Battery Pack Dummy ID** | Scan all 4 module IDs (M1–M4), validate variant match, confirm integration, generate the pack QR, print the pack QR label, then auto-reset for the next pack | 50 x 25 mm   | `ZDesigner ZD421-300dpi ZPL`               |
| **Battery Pack ID**       | Scan the pack serial QR, auto-fill battery parameters (capacity, voltage, model, TAC, etc.), print the full battery pack ID label, then auto-reset | 80 x 40 mm   | `ZDesigner ZD421-300dpi ZPL1`           |
| **BMS ID**                | Scan the BMS QR code, print the BMS ID label, then auto-reset            | 40 x 20 mm   | `ZDesigner ZD421-300dpi ZPL (Copy 1)`      |

All three screens are accessible from `main.py`, which also displays the
ULTRAVIOLETTE logo and provides admin login for editing locked fields.

---

## Nomenclature Formats

### Module ID (scanned on the Battery Pack Dummy screen)

Module model numbers depend on the cell manufacturer, e.g. `VX156610-E1611109G260076`
for a Ten Power 24P module or `VQ150060-E1311109G260076` for BAK:

### Pack Serial Number / Pack QR (scanned on the Battery Pack ID screen)

Pack QR format: `{type_of_reess}:{serial_number}`. The REESS prefix identifies
the cell manufacturer as well as the variant.

Examples: `VX156060:A12026060806875` (Ten Power 24P) and
`VQ150020:A12026060806875` (BAK 24P).

- `type_of_reess` → the REESS number for the cell-manufacturer/variant pair
- `serial_number` → e.g. `A12026060806875` (plant, line, date, 5-digit count)

Scanning this auto-fills the cell manufacturer, variant, and serial number, and refreshes all
battery parameters (Rated Capacity, Max Voltage, RS Version, Model Number,
TAC Number). Revision is no longer encoded in the QR data.

| Variant | Ten Power model / REESS | BAK model / REESS |
|---------|-------------------------|------------------|
| 12P | VX156590 / VX156080 | VQ150040 / VQ150000 |
| 16P | VX156600 / VX156070 | VQ150050 / VQ150010 |
| 24P | VX156610 / VX156060 | VQ150060 / VQ150020 |
| 27P | VX155480 / VX155800 | VQ150070 / VQ150030 |

---

## Workflow per Screen

### Battery Pack Dummy ID
1. Configure plant, line, variant, revision, region (admin-only).
2. Scan M1, M2, M3, M4 module ID QR codes — each scan auto-clears the
   scanner box for the next scan.
3. If a scanned module's variant doesn't match M1, the scan is rejected.
4. Once all 4 modules are scanned and variants match, **INTEGRATION OK** is
   shown, the pack QR is generated and previewed, and the label is
   **printed automatically**.
5. The pack serial count auto-increments by 1 and the screen resets
   (module slots cleared) — ready for the next group of 4 modules.
6. Admins can manually correct the serial count; the stored serial number
   is patched (only the last 6 digits change) and subsequent auto-increments
   continue from the corrected value.

### Battery Pack ID
1. Scan the pack serial QR (`VX...:A...`).
2. Variant, revision, serial number, and battery parameters
   (Rated Capacity, Max Voltage, RS Version, Model Number, TAC Number,
   SRB code, Made-in region, Mfg date) are auto-populated.
3. The full battery pack ID label is **printed automatically**.
4. Fields reset automatically, ready for the next scan.

### BMB/CMB ID
1. Scan the Pack Qr Data (Dummy ID).
2. Scan both BMB and CMB if
3. If a full QR is scanned, the S/W version field updates from the scanned value.
4. The BMS ID label (QR + BMS ID + S/W version) is **printed automatically**.
5. Fields reset automatically, ready for the next scan.

---

## Printing

Labels are generated as raw ZPL (`printing/zpl.py`) and sent directly to the
Windows print spooler via `ctypes` (`printing/spooler.py`), bypassing the
normal print dialog (`pDatatype = "RAW"`).

Each screen targets a specific printer name (`printing/constants.py`):

```python
PRINTER_NAME    = "ZDesigner ZD421-300dpi ZPL"

PRINTER_DUMMY   = "ZDesigner ZD421-300dpi ZPL"
PRINTER_PACK_ID = "ZDesigner ZD421-300dpi ZPL (1)"
PRINTER_BMS_ID  = "ZDesigner ZD421-300dpi ZPL (Copy 1)"
(use these different names when you are testing all in one laptop or pc)
```

If a named printer isn't found, the spooler falls back to a fuzzy
case-insensitive match against installed printers, and raises a clear error
listing available printers if none match.

A `print` / `pdf` mode toggle on each screen lets the operator save the ZPL
to a file instead of sending it to the printer (useful for testing or
offline review).

### Printer setup notes (Windows)

- The printer's **Print Processor** must be set to `winprint` with default
  datatype `RAW` (Printer Properties → Advanced → Print Processor).
- The ZDesigner driver must be configured for **ZPL** language, not EPL2.
- If printing fails with error 1905 (`ERROR_UNKNOWN_PRINTER_DRIVER`),
  restart the Print Spooler service or reinstall the Zebra ZD421 ZPL driver.

## Dataverse integration

The `models/hv/dataverse/` package provides an isolated Web API client and
environment configuration. It is not yet connected to the production screens:
scan, serial, and print-history persistence still use the existing local
storage. Authentication and table-specific operations must be configured
before enabling Dataverse writes.

Set `HV_DATAVERSE_URL` to the HTTPS organization origin or full Web API endpoint
(for example, `https://<organization>.api.crm8.dynamics.com/api/data/v9.2`).
Optionally set `HV_ENTRA_TENANT_ID` and `HV_DATAVERSE_TIMEOUT_SECONDS`.
Authentication is not wired yet; no access tokens, client secrets, or other
credentials belong in source files.

### Backend service layer (development)

`models/hv/backend/` defines application-facing service workflows and
repository protocols independently of Tkinter, ZPL, and printer drivers.
`create_mock_services()` supplies a thread-safe in-memory repository for local
development without Entra registration or Dataverse access. Its data exists
only for the lifetime of the process and is not production persistence.

`create_shared_file_services()` supplies an interim shared-folder repository.
Set `HV_SHARED_DATA_DIR` to an approved UNC path that every production PC can
read and write. The repository serializes operations with an OS-level lock and
replaces a JSON snapshot atomically. All clients must use the same share and
the share must honor byte-range locks and same-directory atomic rename. It
fails on corrupt or incompatible data rather than silently initializing over
it. Back up the share and pilot concurrency/recovery with IT before production.
This design is for low-volume interim use; it does not provide database-grade
availability, transaction recovery, or large-scale reporting. Do not use a
synced consumer folder as a substitute for a file server.

The current services cover scoped/idempotent serial reservation, scan and pack
traceability, BMB/CMB traceability, label-instance creation, and print-attempt
history. Production
repositories can implement the same protocols later: a Dataverse serial
repository should delegate atomic counter allocation to a server-side
operation. Print history should record spooler submission rather than claim
physical output. These services are not yet wired into the existing GUI
workflows; local JSON and Excel persistence remain active until integration is
deliberately enabled and tested. Future Power BI service refresh from an
on-premises share would require an approved on-premises data gateway; Dataverse
or database-backed reporting remains the more robust long-term path.

---

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
│   │   
│   ├───auth
│   │   │   machine_lock.py               # Machine Authorization
│   │   │   session.py                    # Login session state
│   │   │   user_store.py                 # Admin user credentials
│   │   │   __init__.py           
│   │           
│   ├───data
│   │       .gitkeep
│   │       users.json                    # user Credientials
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
│   │   │       pack_session.json
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
