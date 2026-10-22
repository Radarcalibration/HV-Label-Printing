from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import requests

if TYPE_CHECKING:
    from models.hv.session.bms_scan_log import BmsScanRecord
    from models.hv.session.pack_id_scan_log import PackIdScanRecord
    from models.hv.session.scan_log import ScanRecord

_API_URLS = {
    "dummy_api_url": "",
    "pack_id_api_url": "",
    "bms_api_url": "",
}


def get_api_urls() -> dict[str, str]:
    return _API_URLS.copy()


def save_api_urls(dummy_url: str, pack_id_url: str, bms_url: str) -> None:
    _API_URLS.update(
        dummy_api_url=dummy_url.strip(),
        pack_id_api_url=pack_id_url.strip(),
        bms_api_url=bms_url.strip(),
    )


def is_valid_api_url(value: str) -> bool:
    try:
        parsed = urlsplit(value.strip())
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
            and not any(character.isspace() for character in value)
            # and (parsed.port is None or 1 <= parsed.port <= 65535)
        )
    except ValueError:
        return False


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
        get_api_urls()["dummy_api_url"],
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
        get_api_urls()["pack_id_api_url"],
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
        get_api_urls()["bms_api_url"],
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
        get_api_urls()["bms_api_url"],
        {"pack_qr_data": pack_qr_data, "kind": kind, "value": value},
    )


if __name__ == "__main__":
    try:
        print("Succeed")
    except requests.exceptions.RequestException as e:
            print("Request failed:", e)
