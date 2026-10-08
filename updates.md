#1

Recommended architecture

Keep the existing Tkinter screens, scan flow, ZPL builders, and printer calls. Add a backend service layer between the existing workflows and Dataverse: GUI code continues to collect input and show results, while the service layer handles identity, serial allocation, record creation, print-event tracking, and reporting data.

The project currently keeps serial state in  pack_session.json , scan history in Excel workbooks, and user accounts in  users.json . Moving those records to Dataverse would provide centralized, concurrent access and an auditable source of truth. The existing label workflow should still generate ZPL locally and send it to the same printer.

Important boundary: a successful WinSpool call confirms the label was submitted to the Windows print queue; it does not confirm that a physical label came out. Record that outcome as Submitted, not Printed, unless printer-status integration is added separately.

Feature designs

┌──────────────┬───────────────────────────────────────────┬─────────────────┬──────────────────────────────┬─────────────────┐
│ Feature      │ Dataverse tables and required fields      │ Relationships   │ Workflow                     │ Benefits        │
├──────────────┼───────────────────────────────────────────┼─────────────────┼──────────────────────────────┼─────────────────┤
│ Serial       │ Serial Counter: plant, line, variant,     │ Counter → many  │ Before a new pack label is   │ Prevents        │
│ number       │ series key, last-issued count. Serial     │ allocations;    │ generated, call a            │ duplicate       │
│ management   │ Allocation: serial number, count, status, │ allocation →    │ server-side Dataverse Custom │ serials across  │
│              │ idempotency key, reserved/consumed/void   │ one pack.       │ API/plugin to reserve a      │ workstations;   │
│              │ timestamps.                               │                 │ unique count and create an   │ provides a      │
│              │                                           │                 │ allocation atomically. Keep  │ traceable       │
│              │                                           │                 │ the existing Python serial   │ record of       │
│              │                                           │                 │ formatter to build the       │ reserved, used, │
│              │                                           │                 │ serial string.               │ and voided      │
│              │                                           │                 │                              │ numbers.        │
├──────────────┼───────────────────────────────────────────┼─────────────────┼──────────────────────────────┼─────────────────┤
│ Label master │ Label Master: label type, name, label     │ Master → many   │ When creating a label        │ Establishes     │
│ records      │ size, active status. Label Version:       │ versions; each  │ record, capture the          │ which approved  │
│              │ version, effective dates, template        │ label instance  │ applicable master/version    │ label           │
│              │ identifier, checksum, approved-by,        │ references the  │ and its checksum. Keep the   │ definition was  │
│              │ approved-on.                              │ version used.   │ current ZPL generation code  │ associated with │
│              │                                           │                 │ and templates unchanged.     │ each output     │
│              │                                           │                 │                              │ without moving  │
│              │                                           │                 │                              │ ZPL generation  │
│              │                                           │                 │                              │ into Dataverse. │
├──────────────┼───────────────────────────────────────────┼─────────────────┼──────────────────────────────┼─────────────────┤
│ Print        │ Label Instance: label type, QR payload,   │ Pack/BMS unit → │ Create the label instance    │ Central print   │
│ history      │ subject reference, creation time, label   │ label           │ when the app has its label   │ history across  │
│              │ version. Print Attempt: attempt number,   │ instances;      │ data. Wrap the existing      │ workstations,   │
│              │ mode, status, printer/workstation, user,  │ label instance  │ print dispatch with attempt  │ with failed     │
│              │ start/completion time, error details.     │ → many print    │ creation and outcome         │ submissions     │
│              │                                           │ attempts;       │ updates; keep the existing   │ distinguishable │
│              │                                           │ attempts → user │ ZPL and spooler calls.       │ from successful │
│              │                                           │ and printer.    │                              │ queue           │
│              │                                           │                 │                              │ submissions.    │
├──────────────┼───────────────────────────────────────────┼─────────────────┼──────────────────────────────┼─────────────────┤
│ Reprint      │ Fields on Print Attempt: reprint flag,    │ New attempt →   │ Before a repeat submission,  │ Controls        │
│ control      │ original attempt, reason, authorization   │ original        │ validate the role and        │ repeated output │
│              │ result. Optional Reprint Policy: label    │ attempt; policy │ required reason in the       │ while           │
│              │ type, allowed roles, reason-required,     │ applies to a    │ backend; create a new        │ preserving the  │
│              │ limit.                                    │ label type.     │ attempt linked to the        │ full history.   │
│              │                                           │                 │ original. Never overwrite    │                 │
│              │                                           │                 │ the original attempt or      │                 │
│              │                                           │                 │ label record.                │                 │
├──────────────┼───────────────────────────────────────────┼─────────────────┼──────────────────────────────┼─────────────────┤
│ User         │ Use Dataverse/Entra ID users (systemuser) │ User → many     │ Authenticate the desktop     │ Central account │
│ management   │ and Dataverse security roles. Optional    │ scans,          │ user through Microsoft Entra │ lifecycle and   │
│              │ Operator Profile: employee/badge ID,      │ allocations,    │ ID and use delegated         │ role-based      │
│              │ plant, active status.                     │ print attempts, │ Dataverse access. Assign     │ authorization   │
│              │                                           │ and audit       │ permissions through          │ across users    │
│              │                                           │ events; profile │ Dataverse roles/teams, not   │ and stations.   │
│              │                                           │ → user.         │ an application-managed       │                 │
│              │                                           │                 │ password file.               │                 │
├──────────────┼───────────────────────────────────────────┼─────────────────┼──────────────────────────────┼─────────────────┤
│ Audit trail  │ Enable native Dataverse auditing on       │ Events          │ Record meaningful events     │ Supports        │
│              │ operational tables and sensitive columns. │ reference the   │ such as serial reserved,     │ traceability of │
│              │ Optional append-only Production Event:    │ actor and       │ pack completed, reprint      │ both business   │
│              │ event type, timestamp, actor,             │ workstation;    │ approved, and print          │ events and      │
│              │ workstation, correlation ID, target       │ business        │ submission failed. Restrict  │ changes to      │
│              │ table/record ID, details.                 │ records retain  │ event-table updates/deletes  │ stored records. │
│              │                                           │ native audit    │ and configure Dataverse      │                 │
│              │                                           │ history.        │ audit retention.             │                 │
├──────────────┼───────────────────────────────────────────┼─────────────────┼──────────────────────────────┼─────────────────┤
│ QR           │ Scan Event: raw/normalized value,         │ Pack → four     │ Store accepted and rejected  │ Enables forward │
│ traceability │ classified scan type, accepted/rejected   │ pack-module     │ scans. On pack completion,   │ and backward    │
│              │ result, reason, timestamp, user,          │ links; each     │ persist the pack and its     │ traceability    │
│              │ workstation, correlation ID. Production   │ link → one      │ four module links; link the  │ from a pack QR  │
│              │ Pack: serial, variant, QR payload,        │ module. Scan    │ pack QR and later label      │ to its modules, │
│              │ status. Module Unit: module serial,       │ events link to  │ scans to that record.        │ scans, label,   │
│              │ variant. Pack Module: pack, module, slot  │ the relevant    │ Enforce slot and module      │ and print       │
│              │ (M1–M4). BMS Unit: BMS ID, software       │ pack/module/BMS │ uniqueness server-side.      │ attempts.       │
│              │ version.                                  │ unit when       │                              │                 │
│              │                                           │ identified.     │                              │                 │
├──────────────┼───────────────────────────────────────────┼─────────────────┼──────────────────────────────┼─────────────────┤
│ Production   │ Production Order: order/reference,        │ Plant → lines;  │ Populate reporting           │ Enables counts  │
│ reporting    │ product, planned quantity, status. Work   │ line →          │ dimensions during the        │ by plant, line, │
│              │ Shift: shift name, start/end. Production  │ workstations;   │ existing production          │ shift, variant, │
│              │ fields also live on Production Pack:      │ order/shift →   │ workflow; use Dataverse      │ order, and      │
│              │ plant, line, shift, order, completion     │ many packs.     │ views or the Power BI        │ date, plus      │
│              │ time, variant, status.                    │                 │ Dataverse connector for      │ rejection and   │
│              │                                           │                 │ aggregated metrics.          │ reprint trends. │
├──────────────┼───────────────────────────────────────────┼─────────────────┼──────────────────────────────┼─────────────────┤
│ Multi-user   │ Plant, Production Line, Workstation, and  │ Plant → lines → │ Associate each transaction   │ Supports        │
│ access       │ Printer configuration tables, with active │ workstations;   │ with the authenticated user  │ concurrent      │
│              │ status and stable identifiers.            │ workstation →   │ and configured workstation.  │ stations and    │
│              │                                           │ printer         │ Use Dataverse business       │ centrally       │
│              │                                           │ configuration.  │ units, teams, and security   │ managed         │
│              │                                           │                 │ roles to scope access.       │ configuration   │
│              │                                           │                 │                              │ without sharing │
│              │                                           │                 │                              │ local files.    │
└──────────────┴───────────────────────────────────────────┴─────────────────┴──────────────────────────────┴─────────────────┘

Complete Dataverse schema

Use a publisher prefix such as  hv_ . Configure lookups as Dataverse relationships, timestamps as Date and Time, and identifiers as GUIDs. “Required” below means required for the application’s core record-creation path; optional reporting dimensions can remain empty when not available.

┌───────────────────────┬─────────────────────────────────────────────────────────────────┬───────────────────────────────────┐
│ Table                 │ Core fields                                                     │ Keys and relationships            │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Plant (hv_plant)      │ name (required), code (required), active                        │ Alternate key: code. Parent of    │
│                       │                                                                 │ Production Line and Workstation.  │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Production Line       │ name (required), code (required), active, plant (required       │ Alternate key: plant + code.      │
│ (hv_productionline)   │ lookup)                                                         │ Parent of Workstation and Serial  │
│                       │                                                                 │ Counter.                          │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Workstation           │ name (required), station_code (required), active, plant,        │ Alternate key: station_code.      │
│ (hv_workstation)      │ production_line, default_printer                                │ Referenced by scan events and     │
│                       │                                                                 │ print attempts.                   │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Printer (hv_printer)  │ name (required), printer_code, queue_name, active, workstation  │ Referenced by print attempts.     │
│                       │                                                                 │ Store the configured queue name;  │
│                       │                                                                 │ do not change the existing        │
│                       │                                                                 │ printer dispatch.                 │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Product Variant       │ name, variant_code (required), REESS_code, model number, rated  │ Alternate key: variant_code.      │
│ (hv_productvariant)   │ capacity, max voltage, RS version, TAC number, region, active   │ Referenced by counters, packs,    │
│                       │                                                                 │ modules, and label masters where  │
│                       │                                                                 │ applicable.                       │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Label Master          │ name (required), label_type (required Choice), width, height,   │ Parent of Label Version and Label │
│ (hv_labelmaster)      │ unit, active                                                    │ Instance.                         │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Label Version         │ version (required), effective-from, effective-to, template      │ Alternate key: label master +     │
│ (hv_labelversion)     │ identifier, checksum, approved-by, approved-on, active          │ version. Referenced by Label      │
│                       │                                                                 │ Instance. Store                   │
│                       │                                                                 │ metadata/checksum; keep ZPL       │
│                       │                                                                 │ generation unchanged.             │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Serial Counter        │ plant, production line, variant, series key, last-issued count, │ Alternate key: plant + line +     │
│ (hv_serialcounter)    │ updated-on                                                      │ variant + series key. Updated     │
│                       │                                                                 │ only through the atomic           │
│                       │                                                                 │ server-side allocation operation. │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Serial Allocation     │ serial number (required), serial count (required), status       │ Alternate key: serial number;     │
│ (hv_serialallocation) │ (required Choice: Reserved/Consumed/Voided), idempotency key    │ unique idempotency key. One       │
│                       │ (required), reserved-on, consumed-on, void reason, counter,     │ counter has many allocations.     │
│                       │ pack                                                            │                                   │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Production Order      │ order/reference number (required), product/variant, planned     │ Alternate key: order/reference    │
│ (hv_productionorder)  │ quantity, status, start/end dates                               │ number. Optional parent of        │
│                       │                                                                 │ Production Pack.                  │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Work Shift            │ name (required), code (required), start time, end time, active  │ Alternate key: code. Referenced   │
│ (hv_workshift)        │                                                                 │ by Production Pack.               │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Production Pack       │ serial number (required), variant (required), QR payload        │ Alternate key: serial number.     │
│ (hv_productionpack)   │ (required), status, plant, line, shift, production order,       │ Parent of Pack Module, Label      │
│                       │ completed-on, serial allocation                                 │ Instance, and related scan        │
│                       │                                                                 │ events.                           │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Module Unit           │ module serial (required), variant (required), status,           │ Alternate key: module serial.     │
│ (hv_moduleunit)       │ scanned-on                                                      │ Linked to packs through Pack      │
│                       │                                                                 │ Module.                           │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Pack Module           │ pack (required), module (required), slot (required Choice:      │ Alternate keys: pack + slot and   │
│ (hv_packmodule)       │ M1/M2/M3/M4), linked-on                                         │ module, enforced by server-side   │
│                       │                                                                 │ validation. Junction linking      │
│                       │                                                                 │ packs to modules.                 │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ BMS Unit (hv_bmsunit) │ BMS ID (required), software version, status, last-scanned-on    │ Alternate key: BMS ID. Parent of  │
│                       │                                                                 │ BMS Label Instances and related   │
│                       │                                                                 │ scan events.                      │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Scan Event            │ scanned value, normalized value, scan type, accepted            │ Append-oriented operational       │
│ (hv_scanevent)        │ (required), rejection reason, scanned-on (required), user,      │ record. Use a unique              │
│                       │ workstation, correlation ID, production pack, module unit, BMS  │ event/idempotency key to prevent  │
│                       │ unit                                                            │ duplicate ingestion on retries.   │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Label Instance        │ label type (required), QR payload (required), created-on, label │ Link to the pack or BMS unit      │
│ (hv_labelinstance)    │ master, label version, production pack, BMS unit, payload       │ being labeled; validate that the  │
│                       │ checksum                                                        │ correct subject reference is      │
│                       │                                                                 │ populated. Parent of Print        │
│                       │                                                                 │ Attempt.                          │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Print Attempt         │ label instance (required), attempt number, mode (Print/Save),   │ Each attempt belongs to one label │
│ (hv_printattempt)     │ status (Requested/Submitted/Failed/Cancelled), submitted-on,    │ instance. A reprint is a new      │
│                       │ completed-on, printer, workstation, user, error code/details,   │ record linked to the original     │
│                       │ is-reprint, original attempt, reprint reason                    │ attempt.                          │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Operator Profile      │ user (required), employee/badge ID, home plant, active          │ Link to systemuser. Do not store  │
│ (hv_operatorprofile,  │                                                                 │ passwords or password hashes      │
│ optional)             │                                                                 │ here.                             │
├───────────────────────┼─────────────────────────────────────────────────────────────────┼───────────────────────────────────┤
│ Production Event      │ event type, timestamp, actor, workstation, correlation ID,      │ Append-only operational event     │
│ (hv_productionevent,  │ target table name, target record ID, details                    │ log. Use alongside—not instead    │
│ optional)             │                                                                 │ of—native Dataverse auditing.     │
└───────────────────────┴─────────────────────────────────────────────────────────────────┴───────────────────────────────────┘

Use Dataverse’s built-in  systemuser  references and native auditing rather than creating custom user or audit replacements. Configure role privileges so operators can create operational records and view what their role requires, while only authorized roles can manage master data, approve label versions, or authorize reprints.

Data flow

Scanner
  │
  ▼
Existing Tkinter screen ──► Existing parser/validation
  │                               │
  │                               ├──► Dataverse: Scan Event
  │                               │
  │                               └──► Existing ZPL builder (unchanged)
  │                                         │
  │                                         ├──► Dataverse: Label Instance
  │                                         └──► Existing print dispatch (unchanged)
  │                                                    │
  │                                                    ▼
  │                                              Windows spooler
  │                                                    │
  └── Dataverse service layer ◄───────────────────────┘
          ├── Serial allocation Custom API/plugin
          ├── Print Attempt outcome
          └── Pack/module/BMS traceability

Dataverse ──► Power BI Dataverse connector ──► Production dashboards

Python integration approach

1. Add a backend adapter, not a new UI. Introduce a Dataverse client/repository layer for serial allocation, scans, packs, labels, print attempts, and configuration. Keep existing screen layouts and operator steps.
2. Use Entra ID delegated authentication. Treat the Tkinter application as a public desktop client; use an interactive OAuth flow and do not embed a client secret. Apply Dataverse security roles to the authenticated user.
3. Allocate serials atomically. Implement a Dataverse Custom API backed by a synchronous plugin or equivalent server-side transaction. It should enforce the counter’s alternate key, accept an idempotency key, increment the counter, and create the allocation. The existing Python serial-number builder can format the reserved count.
4. Instrument the print boundary. Create/update a Print Attempt around the existing dispatch call. Keep the existing ZPL string and  send_zpl  invocation unchanged. Report queue submission or error—not physical print confirmation.
5. Keep network work off the Tk event loop. Use a worker thread and marshal results back using Tkinter’s event mechanism, so requests do not freeze the application.
6. Define outage behavior explicitly. Serial allocation and reprint authorization require connectivity if they are to be globally enforced. Non-critical telemetry can be queued locally with stable idempotency IDs and retried. Do not silently present a queued event as a successful Dataverse write.
7. Use Power BI on Dataverse data. Connect Power BI to the operational tables, model the plant/line/shift/variant dimensions, and apply appropriate row-level security.

Implementation phases

1. Dataverse foundation: create the environment, publisher, tables, relationships, alternate keys, choice sets, security roles, auditing, and retention settings.
2. Master data and identity: load plants, lines, variants, label masters/versions, printers, and shifts; configure Entra ID authentication and role assignments.
3. Serial allocation: implement and concurrency-test the Custom API/plugin, idempotency, counter scoping, and allocation lifecycle.
4. Traceability migration: add the Python service layer and write scan, pack/module, BMS, label-instance, and production-event records. Migrate historical Excel logs as historical records with clear source metadata.
5. Print history and reprint control: instrument the existing print boundary, add submission/failure recording, then enforce reprint authorization without changing the print or ZPL behavior.
6. Reporting and rollout: validate Power BI metrics against production records, pilot with multiple workstations, monitor API failures and retries, then roll out and retire local files only after migration and reconciliation are verified.


#2

HV Label Printer: Technical Roadmap to Production

1. Current maturity assessment

Maturity: Dataverse foundation established; integration and production controls remain. The environment, solution, and five core tables are in place, with metadata configured. That is a meaningful design/build milestone, but it does not yet demonstrate that the desktop app can safely use Dataverse under concurrent production workloads.

The main production gates are: an agreed authentication model, server-side serial allocation, reliable write semantics for print history, security configuration, integration testing, deployment controls, and operational support. Until those are complete and tested, the Dataverse design should be considered configured, not production-ready.

2. What is already complete

Based on the status provided:

• A Dataverse environment and the HV Label Management solution exist, using publisher prefix  hv .
• The core tables exist:  hv_serialcounter ,  hv_serialallocation ,  hv_productionpack ,  hv_labelinstance , and  hv_printattempt .
• Relationships, alternate keys, choices, required fields, lookups, searchable/reporting fields, and multi-workstation metadata have been configured.
• The desktop application remains Python/Tkinter, with local ZPL generation and Zebra communication retained.
• The constraints rule out UI changes, ZPL changes, printer changes, Power Apps, and Power Automate.

This confirms the initial schema work, but not yet that keys are active, access is correctly secured, or the serial allocation design is concurrency-safe.

3. What is still missing

Before production, close the following gaps:

• Dataverse access and identity: Entra application registration, delegated permissions, role mapping, consent, and token lifecycle.
• Atomic serial allocation: a server-side operation that reserves a unique serial count and records its allocation in one transaction.
• Python integration layer: an isolated client/repository boundary, configuration, error handling, timeouts, retries, and correlation IDs.
• Record lifecycle and failure semantics: defined statuses for allocations, packs, labels, and print attempts, including uncertain outcomes after an app or network failure.
• Security and audit: Dataverse roles, least-privilege table access, auditing configuration, retention, and operational review.
• Environment and release management: development/test/production environments, managed solution promotion, configuration separation, and rollback procedure.
• Data migration and reconciliation: decision on importing existing JSON/Excel records, mapping historical records, and validating counts and duplicates.
• Operational readiness: monitoring, support ownership, backup/recovery expectations, production acceptance criteria, and workstation rollout.

If reporting dimensions or master records such as plants, lines, variants, printers, or shifts are not already available elsewhere in Dataverse, confirm whether they are required for the initial release or can be introduced with the reporting phase.

4. Recommended next steps in exact order

1. Confirm the operational contract. Document the record lifecycle, serial scope, idempotency behavior, print-attempt statuses, online requirements, and what the app may do during a Dataverse outage. Keep this limited to backend behavior; do not change the operator workflow.
2. Create and validate separate non-production environments. Establish development and test environments, verify the solution publisher and ownership, and ensure the existing schema can be promoted between environments.
3. Finalize the schema and security model. Validate alternate keys are active and unique, required fields match the app’s available data, relationships support the needed lookups, and roles enforce least privilege.
4. Design the Entra authentication path. Register the desktop app as a public client, configure delegated Dataverse access, define user consent/admin consent, and test sign-in and token renewal on a managed workstation.
5. Implement and test atomic serial reservation. Add a Dataverse Custom API and synchronous plug-in for allocation; test simultaneous requests, retries with the same idempotency key, counter boundaries, and failed requests.
6. Build the Python Dataverse adapter. Keep it separate from UI and printing code. Add authentication, API calls, serialization, timeouts, retry rules, and consistent error reporting. Preserve the existing screen flow and local ZPL/printer behavior.
7. Integrate transaction boundaries. Persist scan/pack/label records at defined points and create a print-attempt record around the existing print dispatch. Treat spooler acceptance as submission—not proof of physical printing.
8. Test end-to-end and failure cases. Validate normal operation, multi-PC concurrency, duplicate requests, expired tokens, API throttling, network loss, Dataverse errors, and process termination during a print attempt.
9. Decide and execute historical data migration. Reconcile existing records before importing; retain source and import timestamps, avoid inventing missing relationships, and compare totals and duplicates after migration.
10. Set up deployment and support. Promote a managed solution to production, deploy a signed application package, configure workstation access, establish monitoring/support procedures, and roll out in a controlled pilot.
11. Enable reporting after operational data is stable. Connect Power BI to Dataverse, validate measures against source records, and apply reporting access controls before publishing production dashboards.

5. Azure components required

┌────────────────────────┬─────────────────────────────────┬──────────────────────────────────────────────────────────────────┐
│ Component              │ Purpose                         │ Recommendation                                                   │
├────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ Microsoft Entra ID app │ OAuth identity for the          │ Required. Configure as a native/public client using delegated    │
│ registration           │ installed Python desktop        │ access; do not embed a client secret in the desktop app.         │
│                        │ application                     │                                                                  │
├────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ Entra enterprise       │ Controls user assignment and    │ Required as dictated by tenant policy. Restrict access to the    │
│ application / consent  │ consent for the registered      │ intended operator population.                                    │
│ configuration          │ client                          │                                                                  │
├────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ Conditional Access and │ Apply organizational sign-in    │ Use existing company policy; coordinate with the identity team   │
│ identity policies      │ requirements                    │ before production rollout.                                       │
├────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ Azure DevOps or GitHub │ Build, package, sign, and       │ Recommended if an existing CI/CD standard is available; not a    │
│ Actions                │ release the desktop app and     │ runtime dependency.                                              │
│                        │ solution artifacts              │                                                                  │
├────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ Azure Key Vault        │ Protect secrets used by         │ Not needed for a public desktop client with delegated auth. Use  │
│                        │ server-side components          │ only if a future trusted backend needs secrets or certificates.  │
├────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ Azure Monitor /        │ Central service telemetry and   │ Not required for direct desktop-to-Dataverse architecture.       │
│ Application Insights   │ alerts                          │ Consider only if a backend API is introduced or approved desktop │
│                        │                                 │ telemetry is needed.                                             │
└────────────────────────┴─────────────────────────────────┴──────────────────────────────────────────────────────────────────┘

No Azure Function or separate API service is required for the proposed initial architecture. Avoid adding a middle tier without a concrete need, such as centralized policy enforcement that cannot be handled in Dataverse.

6. Dataverse components required

• Existing solution and core tables: retain the five tables and confirm their columns, keys, relationships, and choices match the final lifecycle.
• Custom API and synchronous plug-in: perform atomic serial reservation and allocation creation. Package both in the solution and test concurrency before release.
• Security roles and teams: grant operators only the necessary record-level and table privileges; restrict counter, schema, and master-data administration.
• Auditing: enable auditing on important operational tables and fields, define retention, and validate that audit access is appropriately restricted.
• Environment variables and connection references: use environment-specific values for Dataverse URLs and other deployment configuration; never hardcode environment-specific endpoints in source.
• Duplicate and idempotency controls: use alternate keys and server-side validation to safely handle retried requests and prevent duplicate allocations.
• Optional supporting tables: add plant, line, workstation, printer, variant, shift, or production-order tables only where the reporting and traceability requirements need them and no suitable master data already exists.

Power BI can later read operational data from Dataverse. It does not need to be part of the initial production cutover.

7. Python components required

Add backend capabilities without changing the Tkinter layout or the existing ZPL and printer implementations:

• Dataverse client: communicates with the Dataverse Web API and handles request/response conversion.
• Authentication provider: obtains and renews delegated Entra tokens.
• Repository/service layer: exposes application-level operations such as reserve serial, persist pack, create label record, and record print attempt. GUI modules should not construct raw Web API requests.
• Configuration: supplies the environment URL and client ID from deployment configuration, not source-code secrets.
• Reliability handling: bounded timeouts, selective retries for transient errors, idempotency keys, correlation IDs, and explicit errors.
• Local token cache: use an OS-protected user token cache where supported; do not store passwords or client secrets in application files.
• Thread-safe request execution: avoid blocking Tkinter’s event loop while requests are in flight. Keep existing operator-facing steps unchanged.

Serial allocation and reprint authorization, if enforced centrally, require connectivity. Any offline queue should be limited to operations that can safely be retried; it must not claim a serial was reserved or a print record was persisted when that has not been confirmed.

8. Authentication architecture

Use Microsoft Entra ID delegated authentication for the desktop application:

1. Register the desktop app as a public/native client.
2. Request delegated access to the Dataverse environment for the signed-in user.
3. Apply Entra and Dataverse access controls to the operator population.
4. Use the user’s Dataverse security role to authorize operations.
5. Cache tokens only in an OS-protected user context and handle expiry through the normal OAuth renewal flow.

Do not use a shared operator account, embedded client secret, or custom password store for Dataverse authentication. A service principal or confidential client would be appropriate only behind a trusted backend, not inside a distributed desktop executable.

9. Dataverse integration architecture

Python Tkinter application
  ├─ Existing scan and validation logic
  ├─ Existing ZPL generation (unchanged)
  ├─ Existing printer communication (unchanged)
  └─ Dataverse adapter
       ├─ Entra delegated authentication
       ├─ Dataverse Web API
       └─ Server-side serial allocation Custom API
              └─ Synchronous plug-in
                   └─ Serial Counter + Serial Allocation

Existing printer dispatch ──► Print Attempt outcome update
Dataverse operational records ──► Future Power BI reporting

The Dataverse adapter owns persistence and API concerns; it should not become a second implementation of label generation or printer communication. Use server-side atomic allocation because separate desktop processes cannot safely coordinate a shared counter with client-only read/increment/write logic.

For print history, create an attempt before dispatch and update it after the existing call returns. Use statuses that distinguish requested, submitted, failed, and outcome unknown. A crash after the spooler accepts a job but before Dataverse is updated cannot be reliably resolved by the desktop alone; the record must not falsely assert physical print success.

10. Deployment architecture

Environments: maintain development, test/UAT, and production Dataverse environments. Promote a managed solution to production; keep environment-specific settings outside the application code.

Desktop rollout: package and sign the existing Python application using the organization’s Windows deployment process. Install it on each authorized workstation with the correct Dataverse environment configuration. Keep printer drivers, queue names, and local printing configuration as they are today.

Release controls: version application and solution artifacts together, document compatibility, pilot with a small number of workstations, and define a rollback path. Production promotion should be repeatable and should not depend on manually recreating tables or plug-ins.

Operations: define ownership for Dataverse access failures, serial allocation failures, print-attempt reconciliation, user onboarding, and schema changes. Establish a support path before increasing workstation count.

11. Risks and mitigation

┌────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────┐
│ Risk                           │ Mitigation                                                                                 │
├────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Duplicate serials under        │ Allocate through a server-side transaction; test parallel reservations and idempotent      │
│ concurrent workstation use     │ retries.                                                                                   │
├────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Duplicate records after API    │ Use stable idempotency keys and alternate keys; make retry behavior explicit.              │
│ timeout and retry              │                                                                                            │
├────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Dataverse outage blocks        │ Treat allocation as online-only if uniqueness is mandatory; define an approved outage      │
│ production allocation          │ procedure rather than silently falling back to local counters.                             │
├────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Print is submitted but status  │ Track pending/unknown outcomes, preserve attempt history, and provide a reconciliation     │
│ update fails                   │ process. Do not report physical print confirmation from spooler submission.                │
├────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Excessive permissions or       │ Use individual Entra identities and least-privilege Dataverse roles; do not distribute     │
│ shared credentials             │ secrets in the executable.                                                                 │
├────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ API latency freezes the        │ Run backend calls outside the Tk event loop and use bounded timeouts while keeping the     │
│ desktop                        │ same operator workflow.                                                                    │
├────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Schema drift between           │ Package schema and plug-ins in the solution; promote through controlled environments and   │
│ environments                   │ verify versions.                                                                           │
├────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Inaccurate historical          │ Preserve source metadata, reconcile counts and keys, and retain an export/backup until     │
│ migration                      │ validation is signed off.                                                                  │
├────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Network/API throttling         │ Use bounded exponential backoff only for transient, safe-to-retry operations; do not retry │
│                                │ non-idempotent allocation blindly.                                                         │
├────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Dataverse capacity, API        │ Estimate record volume and retention with the platform owner; monitor usage before broad   │
│ limits, or retention           │ rollout.                                                                                   │
│ constraints                    │                                                                                            │
├────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Reporting exposes operational  │ Apply Dataverse/Power BI access controls and minimize collected user/device data to what   │
│ or personal data               │ operations require.                                                                        │
└────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────┘

12. Phase-by-phase implementation plan

┌──────────────────┬──────────────────────────────────────────────────────────────┬───────────────────────────────────────────┐
│ Phase            │ Scope                                                        │ Exit criteria                             │
├──────────────────┼──────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤
│ 0. Readiness and │ Confirm serial scope, statuses, retry/idempotency rules,     │ Architecture and lifecycle decisions      │
│ contract         │ outage behavior, security expectations, and production       │ approved by application, production, and  │
│                  │ acceptance criteria.                                         │ platform owners.                          │
├──────────────────┼──────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. Environment   │ Set up dev/test/prod, validate solution promotion, configure │ Test user can authenticate and access     │
│ and security     │ Entra app registration and Dataverse roles, confirm auditing │ only permitted Dataverse operations.      │
│ foundation       │ and retention.                                               │                                           │
├──────────────────┼──────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤
│ 2. Serial        │ Implement Custom API and plug-in; validate key behavior,     │ Parallel tests show no duplicate serial   │
│ allocation       │ transaction boundaries, idempotency, and concurrency.        │ allocation; retries return consistent     │
│ service          │                                                              │ results.                                  │
├──────────────────┼──────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤
│ 3. Python        │ Add authentication and Dataverse adapter; wire persistence   │ Existing workflow remains intact and      │
│ integration      │ points without changing screens, ZPL, or printer             │ backend errors are explicit and           │
│ layer            │ communication.                                               │ diagnosable.                              │
├──────────────────┼──────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤
│ 4. Print and     │ Persist production pack, label instance, and print attempt   │ Each label and attempt is traceable;      │
│ traceability     │ lifecycle; test failures and unknown outcomes.               │ statuses accurately reflect what the app  │
│ records          │                                                              │ knows.                                    │
├──────────────────┼──────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤
│ 5. Migration and │ Reconcile and migrate selected historical data; test with    │ Business owners approve data              │
│ UAT              │ operators and multiple PCs under realistic load.             │ reconciliation, performance, and          │
│                  │                                                              │ production acceptance tests.              │
├──────────────────┼──────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤
│ 6. Production    │ Promote managed solution, deploy signed app to pilot         │ Pilot meets agreed success criteria and   │
│ deployment and   │ workstations, monitor, and refine operational procedures.    │ support ownership is active.              │
│ pilot            │                                                              │                                           │
├──────────────────┼──────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤
│ 7. Scale and     │ Roll out to remaining stations; build and validate Power BI  │ Production operations are stable; report  │
│ reporting        │ reports from Dataverse.                                      │ totals reconcile to Dataverse source      │
│                  │                                                              │ records.                                  │
└──────────────────┴──────────────────────────────────────────────────────────────┴───────────────────────────────────────────┘

Recommended immediate priority: finalize the serial allocation contract and Entra/security design, then prove atomic allocation in a test environment before wiring the desktop application to production Dataverse.

# 3 

Phase 0 is complete. We’ve agreed the initial backend contract:

• Serial uniqueness: plant + line + variant + series
• Dataverse outage: block new serial allocations
• Allocation retries: reuse the same idempotency key and return the original allocation
• Print outcome: Submitted means the spooler accepted the job; it does not confirm a physical label
• Reprints: require a reason and retain every attempt
• Identity prerequisite: all intended operators have individual Entra accounts and Dataverse access

Next is Phase 1: environment and solution inventory. The available environments were not identified, and the solution’s managed/unmanaged status is unknown. Before any promotion or production changes, have a Power Platform admin confirm the environment names and types (development, test/UAT, production) and the solution status in each. Then we can validate the existing schema and permissions against the agreed contract and choose the safest next action.


environment-- Radar Calibration's Environment
env type-- developer
role-- admin
data platform -- dataverse

# 4

Developer resources
Environment unique name
unqa09d5b624fb3f1118adb000d3af24
Environment ID
c35f6172-b56a-e81b-b338-a2d054f487d3
Organization ID
a09d5b62-4fb3-f111-8adb-000d3af245da
Web API endpoint
https://org0b27d314.api.crm8.dynamics.com/api/data/v9.2
Learn more
Discovery endpoint
https://globaldisco.crm8.dynamics.com/api/discovery/v2.0/Instances

Name - Ultraviolette Automotive Private Limited

Tenant ID - 12e21b39-4efe-4165-a423-387287d871f3

Primary domain - ultraviolette.com

License - Microsoft Entra ID P2

Radar Calibration - 50498db0-2f60-4fb0-ba72-f6dac83500f4

The supplied Dataverse endpoint and tenant ID are now supported by the Python configuration. It accepts either the organization URL or the full  /api/data/v9.2  endpoint; the tenant ID can be supplied through  HV_ENTRA_TENANT_ID . I also updated the README and added a test for the endpoint format you provided. All 9 Dataverse client tests pass.

This is still a client foundation, not a live Dataverse connection. Authentication and table operations are not wired in. The next step needs the Entra public-client app ID and the exact Dataverse table/entity-set and column logical names (plus the serial-allocation Custom API name and parameters, if it exists). No client secret or access token is needed.

For the next step—sign-in setup—I need one non-secret value:

1. Microsoft Entra public-client Application (client) ID for the desktop app.

If you haven’t registered the app yet, tell me “not created” and I’ll guide you through creating it. It must be a public/native client using delegated sign-in—don’t create or send a client secret.

Later, to connect the app’s records, we’ll need the Dataverse table and column logical names, plus the serial-allocation Custom API details if one exists. We can retrieve much of that metadata after sign-in is configured. The Dataverse URL and tenant ID you already shared are enough for the environment configuration.

# 5 


I have completed Dataverse table and metadata setup.

I do not currently have Microsoft Entra App Registration access.

Generate the complete Python service layer architecture using mock repositories so development can continue until Tenant ID and Client ID are provided by IT.

Do not require authentication implementation.
Focus on interfaces, repositories, workflows, and integration points.

# 6

Added a mock-backed Python service layer so backend development can proceed without Entra registration or Dataverse access. It introduces typed models and repository interfaces for serial allocation, scan/pack/BMB-CMB traceability, label instances, production events, and print attempts, plus a thread-safe in-memory repository and service factory.

The mock enforces scoped, idempotent serial allocation; pack/label consistency; and print-attempt history with reprint reasons. The existing Tkinter screens, ZPL generation, and printer communication were not changed, and the new services are not yet wired into the current workflows. Local JSON and Excel persistence therefore remain in use. The README documents the boundary and mock’s in-memory-only behavior.

Validation: all 20 tests pass, and the new files compile. I left the existing unrelated  zpl.py  modification untouched.
