# HV Label Printing Project

## 1. Project overview

This repository contains a Windows desktop application for generating and printing battery label IDs used in a high-voltage battery production workflow. The system is built in Python using Tkinter for the user interface and uses raw Zebra ZPL commands to send labels directly to Zebra ZD421 printers.

The project is designed for production-line use, where operators scan battery module IDs, pack QR codes, and BMS IDs, validate production data, and print labels automatically. It also stores local session data, serial counters, and scan logs so the application can continue to function without a central database.

At a high level, the application does three core things:

- validates production scan data and serial numbers
- builds label content from QR / serial / variant / electrical data
- prints to specific Zebra printers using Windows print APIs

---

## 2. Purpose of the application

The application is used to manage the labeling process for battery pack production, including:

- Battery pack dummy ID scanning
- Battery pack ID generation and printing
- BMS / CMB / BMB label printing
- scan history recording
- serial number tracking and pack generation
- admin-controlled configuration for plant, line, and variant

This is not a generic barcode app. It is a specialized manufacturing label system for ULTRAVIOLETTE high-voltage packs and associated battery management units.

---

## 3. Main screens / user workflows

The app exposes multiple label workflows through a single main screen selector.

### A. Battery Pack Dummy ID
This screen is used to scan all four module IDs (M1 to M4) for a pack.

Workflow:

1. Select plant, line, variant, serial count, and date
2. Scan four module QR codes
3. Validate that each scanned module matches the expected variant and pack configuration
4. If valid, generate the pack QR and print the pack label
5. Reset the screen for the next pack

The application auto-generates serial numbers and increments count values for each pack.

### B. Battery Pack ID
This screen scans the generated pack serial QR and automatically fills in battery parameters.

Workflow:

1. Scan the pack QR code
2. Extract serial information and variant identity
3. Fill in rated capacity, max voltage, model number, TAC, etc.
4. Generate the full battery pack ID label
5. Print it automatically

### C. BMS ID
This screen handles BMB / CMB label production.

Workflow:

1. Scan the pack QR
2. Scan the BMB and CMB IDs
3. Validate the data
4. Print the BMS label with the correct IDs and software version
5. Reset for the next scanning cycle

### D. Dummy ID (manual)
This is a manual or fallback entry screen for serial / ID input when the standard flow is not appropriate.

---

## 4. Technology stack

### Core
- Python 3
- Tkinter for the desktop GUI
- Windows-specific APIs for printer access
- Zebra ZPL label language

### Local persistence
- SQLite databases for credentials and pack serial state
- Excel files for scan logs and history

### Operating model
- designed for Windows desktop deployment
- machine lock / authorization using a hashed Windows machine GUID
- admin/operator role-based access

---

## 5. High-level application structure

The project is organized into two major areas:

### common/
Shared application utilities used across screens.

Examples:

- `common/auth/machine_lock.py` — validates whether the machine is approved
- `common/auth/session.py` — stores login/session state and role
- `common/auth/user_store.py` — user role / credential definitions
- `common/login_screen.py` — login UI support
- `common/storage.py` — SQLite persistence shared by the user store and pack session
- `common/data/app_data.db` — local user accounts
- `models/hv/data/pack_session.db` — local pack serial state

### models/hv/
Main production application logic and screen implementations.

Examples:

- `models/hv/app.py` — main app frame and screen selector
- `models/hv/gui/*` — Tkinter screens and widgets
- `models/hv/printing/*` — ZPL generation and Windows print spooler interaction
- `models/hv/nomenclature/*` — serial number parsing and validation logic
- `models/hv/session/*` — local session data, pack counters, scan logs

---

## 6. Entry point

The application begins in `main.py`.

Important startup behavior:

- it checks whether the current machine is authorized
- if unauthorized, it shows a warning and exits
- it creates the root Tkinter window
- it loads the application session
- it initializes `HVApp`, which renders the main screen selection UI

The app sets the window to full-screen / maximized mode and loads the UV brand logo.

---

## 7. Machine authorization

The project includes a machine-lock layer to restrict usage to approved PCs.

`common/auth/machine_lock.py` gets the Windows machine GUID, hashes it, and compares it against a stored list of authorized hashes.

This prevents the tool from being used on unapproved systems and is a basic production-control safeguard.

---

## 8. User roles and sessions

The `Session` class manages:

- current username
- role (admin / operator / user)
- password information for Excel log access
- admin permission state

The project treats admin access as a special permission layer that enables editing of configuration values and locked fields.

The UI uses session state to determine whether a user is allowed to adjust plant/line/variant data or manage protected settings.

---

## 9. Serial number logic

The serial numbering system is central to the project.

### Example serial format

Typical pack serial numbers include a plant/line/date structure and a running counter:

- `VX156060:A12026060806875` (Ten Power 24P)
- `VQ150020:A12026060806875` (BAK 24P)
- `VX...:A...`

This pattern combines:

- REESS / type information
- serial number
- date
- cell manufacturer / variant / category metadata

The new serial format uses the cell-manufacturer character after category: Molical=P, Samsung=Q, BAK=R, EVE=S, LG=T, and Ten Power=U. Existing shift-coded serials remain supported for parsing.

The serial number handling is implemented in:

- `models/hv/nomenclature/serial_number.py`
- `models/hv/session/pack_store.py`

The app stores the current pack serial and latest serial count in `models/hv/data/pack_session.db` so that the next pack continues sequentially. Existing `pack_session.json` and pack state in the previous shared `app_data.db` are imported once on first use. `users.json` is imported into `common/data/app_data.db`.

---

## 10. QR / scan recognition

The application has a scan-identification layer in:

- `models/hv/nomenclature/scan_handler.py`

This classifies incoming scan data as one of several types, such as:

- module ID
- pack serial / QR
- BMB ID
- CMB ID
- unknown or invalid input

The scan system normalizes and validates raw scanner inputs before the app decides what to do next.

---

## 11. Printing system

The printing architecture is one of the most important parts of the project.

### Label generation
The label content is built using label templates and raw ZPL (Zebra Programming Language).

Relevant files:

- `models/hv/printing/labels.py`
- `models/hv/printing/zpl.py`
- `models/hv/printing/constants.py`

These modules generate the actual barcode / text label payload used by Zebra printers.

### Print dispatch
The project sends ZPL directly to the Windows print spooler instead of relying on a normal print dialog.

Important behavior:

- the app resolves the correct installed printer name
- it calls the Windows spooler API through `ctypes`
- it sends raw ZPL in `RAW` datatype mode
- it can also save output as PDF or ZPL if the operator chooses a non-print mode

The logic is implemented in:

- `models/hv/printing/spooler.py`

### Printer configuration
Printer names are defined in:

- `models/hv/printing/constants.py`

Examples include:

- dummy pack label printer
- battery pack ID printer
- BMS ID printer

The code attempts to match printers by exact name first, then by fuzzy case-insensitive matching if necessary.

---

## 12. GUI design and organization

The interface is a collection of reusable Tkinter components and screens.

### Shared UI helpers
- `layout.py` — fonts, spacing, column helpers
- `permissions.py` — enables/disables fields based on user role
- `print_actions.py` — dispatches labels to printer or file
- `scanner.py` — binds hardware scanner input to entry fields
- `scan_history.py` — opens scan history windows

### Screen modules
- `battery_pack_dummy.py` — pack dummy assembly and validation screen
- `battery_pack_id.py` — pack ID scanning and parameter population
- `bms_id.py` — BMB/CMB scan and rework logic
- `dummy_id.py` — manual or fallback ID input flow
- `battery_parameters.py` — battery metadata display panel
- `category_controls.py` — domestic/export category controls and variant bindings
- `auth_dialog.py` / `auth_bar.py` — login and auth UI

---

## 13. Local data and persistence model

The application stores user accounts in `common/data/app_data.db` and pack serial state in `models/hv/data/pack_session.db`. Older JSON files are imported once on first use and are left in place.

### Pack serial state
Stored in the `app_state` table in `models/hv/data/pack_session.db`.

This keeps the last-used serial number and count so production continues without reset.

### Scan logs
Dummy pack scan records are stored in `models/hv/data/scan_log.db`; the app imports existing records from `scan_log.xlsx` once and leaves that workbook unchanged. Other scan logs remain in Excel workbooks:

- `models/hv/data/pack_id_scan_log.xlsx`
- `models/hv/data/bms_scan_log.xlsx`

The original `models/hv/data/scan_log.xlsx` is retained as-is as the pre-migration copy.

### User store
Stored in the `users` table in `common/data/app_data.db`.

The app reads these accounts to determine login access.

---

## 14. Admin and production controls

The app supports admin-level features such as:

- modifying configuration fields
- overriding serial count or serial values
- editing production parameters
- managing locked or restricted fields

The admin controls are implemented by tracking session role and calling permission helpers across the UI.

---

## 15. Current architectural boundary

The project is intentionally still local-first. It persists to JSON and Excel files rather than a central database. That makes it easy to deploy on the factory floor but also means it is not a distributed, multi-terminal relational system.

The `README.md` includes a forward-looking architecture section discussing a future integration with Dataverse / Microsoft backend services. It describes a backend layer that could sit between the existing Tkinter GUI and a central storage system while preserving the current label print process.

That proposed future design includes:

- serial reservation and allocation records
- label master and version tracking
- print-attempt history
- reprint policy enforcement
- user / workstation / plant metadata
- centralized audit trails

The current project has not yet fully connected those backend services, but the design is clearly planned.

---

## 16. What the project is best at

This project is best understood as a manufacturing label system for battery associated operations. It is excellent at:

- validating scan data from production equipment
- enforcing variant and pack matching rules
- generating serial numbers and pack QR data
- creating battery labels in ZPL format
- printing directly to Zebra printers
- preserving local production traceability records

---

## 17. Limitations and operational notes

The current implementation has several important practical considerations:

- it is Windows-specific
- it depends on hardware scanner input and Zebra printers
- it relies on local file persistence rather than a central database
- it uses explicitly configured printer names and local file locations
- it assumes a controlled production environment with approved machines and authorized users

The code does include logic for machine authorization and session roles, but the overall system should still be considered a plant-floor manufacturing tool rather than a general enterprise application.

---

## 18. Summary

The HV Label Printing project is a specialized desktop application for battery pack and BMS label creation in a manufacturing workflow. It combines:

- Python + Tkinter interface
- production scanning workflows
- serial number generation
- QR / barcode validation
- Zebra ZPL label building
- direct Windows print spooler submission
- local history and configuration storage

The project is designed for reliability on the factory floor, with a clear path toward more formal backend integration in the future if production requirements expand to multi-site or enterprise-level traceability.