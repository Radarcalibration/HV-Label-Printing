import csv
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Machine Data API")

LOG_DIR = Path(__file__).resolve().parent # this file's folder


DUMMY_COLUMNS = [
    "Sl.No",
    "Date",
    "Time",
    "Serial Count",
    "Pack ID",
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
PACK_ID_COLUMNS = [
    "Sl.No", "Date", "Time", "Serial Number", "Variant", "Pack QR Data"
]
BMS_COLUMNS = [
    "Sl.No", "Date", "Time", "Pack QR Data", "BMB ID", "CMB ID",
    "Rework BMB ID", "Rework CMB ID",
]

LOG_LOCK = threading.Lock() # prevents two requests writing at the same time


class DummyScan(BaseModel):
    date: str = ""
    time: str = ""
    serial_count: str = ""
    serial_number: str = ""
    ref_no: str = ""
    variant: str = ""
    m1: str = ""
    m2: str = ""
    m3: str = ""
    m4: str = ""
    dummy_pack_status: str = ""
    dummy_pack_qr: str = ""
    issue_desc_1: str = ""
    issue_desc_2: str = ""
    action_plan: str = ""
    remark: str = ""
    admin_ack: str = ""


class PackIdScan(BaseModel):
    date: str = ""
    time: str = ""
    serial_number: str = ""
    variant: str = ""
    pack_qr_data: str = ""


class BmsScan(BaseModel):
    date: str = ""
    time: str = ""
    pack_qr_data: str = ""
    bmb_id: str = ""
    cmb_id: str = ""
    rework_bmb_id: str = ""
    rework_cmb_id: str = ""


class BmsRework(BaseModel):
    pack_qr_data: str
    kind: str
    value: str


def _read_rows(file_name: str, columns: list[str]) -> list[dict[str, str]]:
    path = LOG_DIR / file_name
    with LOG_LOCK:
        if not path.exists():
            return []
        try:
            with path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != columns:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Unexpected CSV headers in {file_name}",
                    )
                return list(reader)
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Could not read {file_name}: {e}") from e


def _resequence_rows(rows: list[dict[str, str]]) -> None:
    for index, row in enumerate(rows, start=1):
        row["Sl.No"] = str(index)

def _append_row(
    file_name: str,
    columns: list[str],
    values: dict[str, str],
) -> dict[str, str]:
    path = LOG_DIR / file_name
    with LOG_LOCK:
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            existing_rows = []
            if path.exists() and path.stat().st_size > 0:
                with path.open("r", newline="", encoding="utf-8") as csv_file:
                    reader = csv.DictReader(csv_file)
                    if reader.fieldnames != columns:
                        raise HTTPException(status_code=500,detail=f"Unexpected CSV headers in {file_name}",)
                    existing_rows = list(reader)
                # Resequence existing rows
                for index, row in enumerate(existing_rows, start=1):
                    row["Sl.No"] = str(index)
                # Rewrite file with corrected serial numbers
                with path.open("w", newline="", encoding="utf-8") as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=columns)
                    writer.writeheader()
                    writer.writerows(existing_rows)
            next_serial_number = len(existing_rows) + 1
            row = {"Sl.No": str(next_serial_number),**values,}
            with path.open("a", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=columns)
                if path.stat().st_size == 0:
                    writer.writeheader()
                writer.writerow(row)
            return row
        except HTTPException:
            raise
        except OSError as e:
            raise HTTPException(status_code=500,detail=f"Could not write {file_name}: {e}",) from e



def _update_bms_rework(item: BmsRework) -> dict[str, str]:
    kind = item.kind.upper()
    if kind not in {"BMB", "CMB"}:
        raise HTTPException(status_code=422, detail="kind must be BMB or CMB")

    path = LOG_DIR / "bms_scan_log.csv"
    with LOG_LOCK:
        if not path.exists():
            raise HTTPException(status_code=404, detail="BMS scan log does not exist")
        try:
            with path.open("r", newline="", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                if reader.fieldnames != BMS_COLUMNS:
                    raise HTTPException(status_code=500, detail="Unexpected BMS CSV headers")
                rows = list(reader)
            target = item.pack_qr_data.strip()
            for row in reversed(rows):
                if row["Pack QR Data"].strip() == target:
                    column = "Rework BMB ID" if kind == "BMB" else "Rework CMB ID"
                    row[column] = item.value
                    break
            else:
                raise HTTPException(status_code=404, detail="Pack QR Data not found")

            with path.open("w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=BMS_COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            return row
        except HTTPException:
            raise
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Could not update BMS CSV: {e}") from e


@app.get("/data/dummy")
def get_dummy_scans() -> list[dict[str, str]]:
    return _read_rows("Dummy_scan_log.csv", DUMMY_COLUMNS)


@app.post("/data/dummy", status_code=201)
def receive_dummy_scan(item: DummyScan) -> dict:
    row = _append_row(
        "Dummy_scan_log.csv",
        DUMMY_COLUMNS,
        {
            "Date": item.date,
            "Time": item.time,
            "Serial Count": item.serial_count,
            "Pack ID": item.serial_number,
            "Ref No": item.ref_no,
            "Variant": item.variant,
            "M1": item.m1,
            "M2": item.m2,
            "M3": item.m3,
            "M4": item.m4,
            "Dummy Pack ID Status": item.dummy_pack_status,
            "Dummy Pack QR Data": item.dummy_pack_qr,
            "Issue Description 1": item.issue_desc_1,
            "Issue Description 2": item.issue_desc_2,
            "Action Plan": item.action_plan,
            "Remark": item.remark,
            "Admin Acknowledgement": item.admin_ack,
        },
    )
    return {"message": "Dummy scan saved", "data": row}


@app.get("/data/packid")
def get_pack_id_scans() -> list[dict[str, str]]:
    return _read_rows("pack_id_scan_log.csv", PACK_ID_COLUMNS)


@app.post("/data/packid", status_code=201)
def receive_pack_id_scan(item: PackIdScan) -> dict:
    row = _append_row(
        "pack_id_scan_log.csv",
        PACK_ID_COLUMNS,
        {
            "Date": item.date,
            "Time": item.time,
            "Serial Number": item.serial_number,
            "Variant": item.variant,
            "Pack QR Data": item.pack_qr_data,
        },
    )
    return {"message": "Pack ID scan saved", "data": row}


@app.get("/data/bmbcmb")
def get_bms_scans() -> list[dict[str, str]]:
    return _read_rows("bms_scan_log.csv", BMS_COLUMNS)


@app.post("/data/bmbcmb", status_code=201)
def receive_bms_scan(item: BmsScan) -> dict:
    row = _append_row(
        "bms_scan_log.csv",
        BMS_COLUMNS,
        {
            "Date": item.date,
            "Time": item.time,
            "Pack QR Data": item.pack_qr_data,
            "BMB ID": item.bmb_id,
            "CMB ID": item.cmb_id,
            "Rework BMB ID": item.rework_bmb_id,
            "Rework CMB ID": item.rework_cmb_id,
        },
    )
    return {"message": "BMB/CMB scan saved", "data": row}


@app.patch("/data/bmbcmb")
def update_bms_rework(item: BmsRework) -> dict:
    return {"message": "BMB/CMB rework updated", "data": _update_bms_rework(item)}


# python -m uvicorn Server:app --host 0.0.0.0 --port 8001
