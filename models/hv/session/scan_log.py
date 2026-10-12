from __future__ import annotations

import os
import stat
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.protection import SheetProtection

from models.hv.session.paths import get_base_dir
from models.hv.session.mongo_store import (
    insert_scan_record,
    list_scan_records,
    update_scan_record_at_row,
)

LOG_FILE = get_base_dir() / "data" / "scan_log.xlsx"
EXPORT_FILE = get_base_dir() / "data" / "scan_log_atlas_export.xlsx"

SHEET_NAME = "HV Dummy"

PROTECT_SHEET = False #excel sheet protection is disables (False)


def _ensure_writable(path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.parent.chmod(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        if path.exists():
            path.chmod(
                stat.S_IRUSR | stat.S_IWUSR |
                stat.S_IRGRP | stat.S_IWGRP |
                stat.S_IROTH | stat.S_IWOTH
            )
    except OSError:
        pass


COLUMNS = [
    "Sl.No",
    "Date",
    "Time",
    "Serial Count",
    "Pack ID (Serial Number)",
    "Ref No",
    "Variant",
    "M1",
    "M2",
    "M3",
    "M4",
    "Dummy Pack ID Status",
    "Dummy Pack QR Data",
    "Issue Description 1",
    "Issue Description 2",
    "Action Plan",
    "Remark",
    "Admin Acknowledgement",
]

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(name="Segoe UI", bold=True, color="FFFFFF", size=10)
CELL_FONT   = Font(name="Segoe UI", size=10)
ALT_FILL    = PatternFill("solid", fgColor="EEF2F7")

COL_WIDTHS = {
    "Sl.No":                    7,
    "Date":                    13,
    "Time":                    12,
    "Serial Count":            12,
    "Ref No":                  12,
    "Variant":                 12,
    "M1":                      26,
    "M2":                      26,
    "M3":                      26,
    "M4":                      26,
    "Dummy Pack ID Status":    18,
    "Dummy Pack QR Data":      40,
    "Pack ID (Serial Number)": 22,
    "Issue Description 1":    30,
    "Issue Description 2":    30,
    "Action Plan":             30,
    "Remark":                  20,
    "Admin Acknowledgement":   30,
}

LEFT_ALIGN_COLS = {
    "M1", "M2", "M3", "M4",
    "Dummy Pack QR Data", "Pack ID (Serial Number)",
    "Issue Description 1", "Issue Description 2",
    "Action Plan", "Remark", "Admin Acknowledgement",
}

UNLOCKED_COLS = {
    "Ref No",
    "Serial Count",
    "Issue Description 1",
    "Issue Description 2",
    "Action Plan",
    "Remark",
    "Admin Acknowledgement",
}


@dataclass
class ScanRecord:
    date: str               = ""
    time: str               = ""
    serial_count: str       = ""
    ref_no: str             = ""
    variant: str            = ""
    m1: str                 = ""
    m2: str                 = ""
    m3: str                 = ""
    m4: str                 = ""
    dummy_pack_status: str  = ""
    dummy_pack_qr: str      = ""
    serial_number: str      = ""
    issue_desc_1: str       = ""
    issue_desc_2: str       = ""
    action_plan: str        = ""
    remark: str             = ""
    admin_ack: str          = ""

    @property
    def has_issue(self) -> bool:
        return bool(self.issue_desc_1.strip() or self.issue_desc_2.strip())

    @property
    def is_unacknowledged(self) -> bool:
        return self.has_issue and not self.admin_ack.strip()

    def as_row(self, sl_no: int) -> list:
        return [
            sl_no,
            self.date,
            self.time,
            self.serial_count,
            self.serial_number,
            self.ref_no,
            self.variant,
            self.m1,
            self.m2,
            self.m3,
            self.m4,
            self.dummy_pack_status,
            self.dummy_pack_qr,
            self.issue_desc_1,
            self.issue_desc_2,
            self.action_plan,
            self.remark,
            self.admin_ack,
        ]


def _protection(password: str, enabled: bool = True) -> SheetProtection:
    if not enabled:
        return SheetProtection(sheet=False)
    return SheetProtection(
        sheet=True,
        password=password,
        selectLockedCells=True,
        selectUnlockedCells=True,
        insertRows=False,
        insertColumns=False,
        deleteRows=False,
        deleteColumns=False,
        sort=False,
        autoFilter=False,
    )


def _build_header(ws: openpyxl.worksheet.worksheet.Worksheet, excel_password: str) -> None:
    for col_idx, col_name in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col_idx)].width = COL_WIDTHS.get(col_name, 18)
        if col_name in UNLOCKED_COLS:
            cell.protection = openpyxl.styles.Protection(locked=False)
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 28
    ws.protection = _protection(excel_password, enabled=PROTECT_SHEET)


def _get_scan_log_sheet(wb: openpyxl.Workbook, excel_password: str) -> openpyxl.worksheet.worksheet.Worksheet:
    
    if SHEET_NAME in wb.sheetnames:
        return wb[SHEET_NAME]
    ws = wb.create_sheet(title=SHEET_NAME, index=0)
    _build_header(ws, excel_password)
    return ws


def _ensure_workbook(
    excel_password: str, *, path: Path = LOG_FILE
) -> openpyxl.Workbook:
    if path.exists():
        try:
            wb = openpyxl.load_workbook(path)
            ws = _get_scan_log_sheet(wb, excel_password)
            existing_headers = [
                str(ws.cell(row=1, column=i + 1).value or "").strip()
                for i in range(ws.max_column)
            ]
            if existing_headers != COLUMNS:
                data_rows = []
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if any(c is not None and str(c).strip() for c in row):
                        data_rows.append(list(row))
                old_col_map = {h: i for i, h in enumerate(existing_headers)}
                ws.protection = _protection(excel_password, enabled=False)
                ws.delete_rows(1, ws.max_row + 1)
                _build_header(ws, excel_password)
                ws.protection = _protection(excel_password, enabled=False)
                for row_idx, old_row in enumerate(data_rows, start=2):
                    alt = row_idx % 2 == 0
                    for col_idx, col_name in enumerate(COLUMNS, start=1):
                        old_i = old_col_map.get(col_name)
                        if old_i is not None and old_i < len(old_row):
                            value = old_row[old_i]
                        else:
                            value = ""
                        cell = ws.cell(row=row_idx, column=col_idx, value=value)
                        cell.font = CELL_FONT
                        h_align = "left" if col_name in LEFT_ALIGN_COLS else "center"
                        cell.alignment = Alignment(horizontal=h_align, vertical="center")
                        if alt:
                            cell.fill = ALT_FILL
                        if col_name in UNLOCKED_COLS:
                            cell.protection = openpyxl.styles.Protection(locked=False)
                    ws.row_dimensions[row_idx].height = 18
                ws.protection = _protection(excel_password, enabled=PROTECT_SHEET)
                _ensure_writable(path)
                wb.save(path)
            return wb
        except Exception:
            pass

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    _build_header(ws, excel_password)
    _ensure_writable(path)
    wb.save(path)
    return wb


def append_scan_record(record: ScanRecord, *, excel_password: str = "06082003") -> None:
    insert_scan_record("dummy_scan_logs", record)
    wb = _ensure_workbook(excel_password)
    ws = _get_scan_log_sheet(wb, excel_password)
    ws.protection = _protection(excel_password, enabled=False)

    sl_no = ws.max_row
    row_idx = ws.max_row + 1
    row_data = record.as_row(sl_no)

    for col_idx, (col_name, value) in enumerate(zip(COLUMNS, row_data), start=1):
        cell = ws.cell(row=row_idx, column=col_idx, value=value)
        cell.font = CELL_FONT
        h_align = "left" if col_name in LEFT_ALIGN_COLS else "center"
        cell.alignment = Alignment(horizontal=h_align, vertical="center", wrap_text=True)
        if row_idx % 2 == 0:
            cell.fill = ALT_FILL
        if col_name in UNLOCKED_COLS:
            cell.protection = openpyxl.styles.Protection(locked=False)

    ws.row_dimensions[row_idx].height = 18
    ws.protection = _protection(excel_password, enabled=PROTECT_SHEET)
    _ensure_writable(LOG_FILE)
    wb.save(LOG_FILE)


def load_all_records_with_rows() -> list[tuple[int, ScanRecord]]:
    records = []
    for row_idx, document in enumerate(list_scan_records("dummy_scan_logs"), start=2):
        record = ScanRecord(**{
            field: str(document.get(field, "") or "")
            for field in ScanRecord.__dataclass_fields__
        })
        records.append((row_idx, record))
    return records


def load_all_records() -> list[ScanRecord]:
    return [rec for _row, rec in load_all_records_with_rows()]


def load_unacknowledged_issues() -> list[tuple[int, ScanRecord]]:
    return [(row, rec) for row, rec in load_all_records_with_rows() if rec.is_unacknowledged]


def sync_excel_from_mongodb(*, excel_password: str = "06082003") -> None:
    records = load_all_records()
    workbook = _ensure_workbook(excel_password, path=EXPORT_FILE)
    worksheet = _get_scan_log_sheet(workbook, excel_password)
    worksheet.protection = _protection(excel_password, enabled=False)
    worksheet.delete_rows(1, worksheet.max_row)
    _build_header(worksheet, excel_password)
    for sl_no, record in enumerate(records, start=1):
        row_idx = sl_no + 1
        for col_idx, (col_name, value) in enumerate(
            zip(COLUMNS, record.as_row(sl_no)), start=1
        ):
            cell = worksheet.cell(row=row_idx, column=col_idx, value=value)
            cell.font = CELL_FONT
            h_align = "left" if col_name in LEFT_ALIGN_COLS else "center"
            cell.alignment = Alignment(
                horizontal=h_align, vertical="center", wrap_text=True
            )
            if row_idx % 2 == 0:
                cell.fill = ALT_FILL
            if col_name in UNLOCKED_COLS:
                cell.protection = openpyxl.styles.Protection(locked=False)
        worksheet.row_dimensions[row_idx].height = 18
    worksheet.protection = _protection(excel_password, enabled=PROTECT_SHEET)
    _ensure_writable(EXPORT_FILE)
    workbook.save(EXPORT_FILE)
    workbook.close()


def patch_admin_ack(sheet_row: int, ack_text: str, *, excel_password: str = "06082003") -> bool:
    if not update_scan_record_at_row(
        "dummy_scan_logs", sheet_row, {"admin_ack": ack_text}
    ):
        return False

    records = list_scan_records("dummy_scan_logs")
    record_index = sheet_row - 2
    if LOG_FILE.exists() and 0 <= record_index < len(records):
        pack_qr = records[record_index].get("dummy_pack_qr", "")
        wb = _ensure_workbook(excel_password)
        ws = _get_scan_log_sheet(wb, excel_password)
        qr_col = COLUMNS.index("Dummy Pack QR Data") + 1
        ack_col = COLUMNS.index("Admin Acknowledgement") + 1
        for row in range(2, ws.max_row + 1):
            if str(ws.cell(row=row, column=qr_col).value or "").strip() == pack_qr:
                ws.protection = _protection(excel_password, enabled=False)
                cell = ws.cell(row=row, column=ack_col, value=ack_text)
                cell.font = CELL_FONT
                cell.alignment = Alignment(horizontal="left", vertical="center")
                ws.protection = _protection(excel_password, enabled=PROTECT_SHEET)
                _ensure_writable(LOG_FILE)
                wb.save(LOG_FILE)
                break
    return True


def add_sheet(sheet_name: str, *, excel_password: str = "06082003") -> tuple[bool, str]:
    if not sheet_name.strip():
        return False, "Sheet name cannot be empty."
    wb = _ensure_workbook(excel_password)
    existing = [ws.title.lower() for ws in wb.worksheets]
    if sheet_name.strip().lower() in existing:
        return False, f'Sheet "{sheet_name}" already exists.'
    new_ws = wb.create_sheet(title=sheet_name.strip())
    new_ws.sheet_properties.tabColor = "4472C4"
    _ensure_writable(LOG_FILE)
    wb.save(LOG_FILE)
    return True, f'Sheet "{sheet_name}" added.'


def open_log_file() -> None:
    sync_excel_from_mongodb()
    if EXPORT_FILE.exists():
        os.startfile(str(EXPORT_FILE))