import sys
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from models.hv.session.bms_scan_log import BmsScanRecord
    from models.hv.session.pack_id_scan_log import PackIdScanRecord
    from models.hv.session.scan_log import ScanRecord

API_DUMMY_URL = "http://10.0.42.86:8001/data/dummy"
API_PACK_ID_URL = "http://10.0.42.86:8001/data/packid"
API_BMB_CMB_URL = "http://10.0.42.86:8001/data/bmbcmb"


def _post(url: str, payload: dict[str, str]) -> None:
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)


def _patch(url: str, payload: dict[str, str]) -> None:
    try:
        response = requests.patch(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)


def send_dummy_scan(record: ScanRecord) -> None:
    _post(
        API_DUMMY_URL,
        {
            "date": record.date,
            "time": record.time,
            "serial_count": record.serial_count,
            "serial_number": record.serial_number,
            "ref_no": record.ref_no,
            "variant": record.variant,
            "m1": record.m1,
            "m2": record.m2,
            "m3": record.m3,
            "m4": record.m4,
            "dummy_pack_status": record.dummy_pack_status,
            "dummy_pack_qr": record.dummy_pack_qr,
            "issue_desc_1": record.issue_desc_1,
            "issue_desc_2": record.issue_desc_2,
            "action_plan": record.action_plan,
            "remark": record.remark,
            "admin_ack": record.admin_ack,
        },
    )


def send_pack_id_scan(record: PackIdScanRecord) -> None:
    _post(
        API_PACK_ID_URL,
        {
            "date": record.date,
            "time": record.time,
            "serial_number": record.serial_number,
            "variant": record.variant,
            "pack_qr_data": record.pack_qr_data,
        },
    )


def send_bms_scan(record: BmsScanRecord) -> None:
    _post(
        API_BMB_CMB_URL,
        {
            "date": record.date,
            "time": record.time,
            "pack_qr_data": record.pack_qr_data,
            "bmb_id": record.bmb_id,
            "cmb_id": record.cmb_id,
            "rework_bmb_id": record.rework_bmb_id,
            "rework_cmb_id": record.rework_cmb_id,
        },
    )


def send_bms_rework(pack_qr_data: str, kind: str, value: str) -> None:
    _patch(
        API_BMB_CMB_URL,
        {"pack_qr_data": pack_qr_data, "kind": kind, "value": value},
    )


if __name__ == "__main__":
    try:
        print("Scan log API:")
    except requests.exceptions.RequestException as e:
            print("Request failed:", e)
