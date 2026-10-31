from typing import TYPE_CHECKING
from urllib.parse import urlsplit
from tkinter import messagebox

import requests

from common.storage import connect_db

if TYPE_CHECKING:
    from models.hv.session.bms_scan_log import BmsScanRecord
    from models.hv.session.pack_id_scan_log import PackIdScanRecord
    from models.hv.session.scan_log import ScanRecord

_SETTING_KEYS = {
    "dummy_api_url": "api.dummy.url",
    "pack_id_api_url": "api.pack_id.url",
    "bms_api_url": "api.bms.url",
    "dummy_api_key": "api.dummy.key",
    "pack_id_api_key": "api.pack_id.key",
    "bms_api_key": "api.bms.key",
    "dummy_enabled": "api.dummy.enabled",
    "pack_id_enabled": "api.pack_id.enabled",
    "bms_enabled": "api.bms.enabled",
    "machine_name": "api.machine.name",
    "machine_id": "api.machine.id",
}

_API_URLS = {
    "dummy_api_url": "",
    "pack_id_api_url": "",
    "bms_api_url": "",
}

_API_KEYS = {
    "dummy_api_key": "",
    "pack_id_api_key": "",
    "bms_api_key": "",
}

_API_CALL_ENABLED = {
    "dummy": True,
    "pack_id": True,
    "bms": True,
}

_machine_details = {
    "machine_name": "",
    "machine_id": "",
}


def _persist_settings(values: dict[str, str]) -> None:
    with connect_db() as connection:
        connection.executemany(
            """
            INSERT INTO app_state(key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            ((_SETTING_KEYS[name], value) for name, value in values.items()),
        )


def _load_settings() -> None:
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT key, value FROM app_state WHERE key IN ({})".format(
                ", ".join("?" for _ in _SETTING_KEYS.values())
            ),
            tuple(_SETTING_KEYS.values()),
        ).fetchall()
    values = {row["key"]: row["value"] for row in rows}

    for name in _API_URLS:
        _API_URLS[name] = values.get(_SETTING_KEYS[name], "")
    for name in _API_KEYS:
        _API_KEYS[name] = values.get(_SETTING_KEYS[name], "")
    for endpoint in _API_CALL_ENABLED:
        setting_name = f"{endpoint}_enabled"
        _API_CALL_ENABLED[endpoint] = values.get(
            _SETTING_KEYS[setting_name], "true"
        ).lower() == "true"
    for name in _machine_details:
        _machine_details[name] = values.get(_SETTING_KEYS[name], "")


_load_settings()


def get_api_urls() -> dict[str, str]:
    return _API_URLS.copy()


def get_api_keys() -> dict[str, str]:
    return _API_KEYS.copy()


def get_api_call_settings() -> dict[str, bool]:
    return _API_CALL_ENABLED.copy()


def set_api_call_enabled(endpoint: str, enabled: bool) -> None:
    if endpoint not in _API_CALL_ENABLED:
        raise ValueError(f"Unknown API endpoint: {endpoint}")
    _persist_settings({f"{endpoint}_enabled": str(enabled).lower()})
    _API_CALL_ENABLED[endpoint] = enabled


def get_machine_details() -> dict[str, str]:
    return _machine_details.copy()


def save_machine_details(machine_name: str, machine_id: str) -> None:
    values = {
        "machine_name": machine_name.strip(),
        "machine_id": machine_id.strip(),
    }
    _persist_settings(values)
    _machine_details.update(values)


def save_api_urls(dummy_url: str, pack_id_url: str, bms_url: str) -> None:
    values = {
        "dummy_api_url": dummy_url.strip(),
        "pack_id_api_url": pack_id_url.strip(),
        "bms_api_url": bms_url.strip(),
    }
    _persist_settings(values)
    _API_URLS.update(values)


def save_api_keys(dummy_key: str, pack_id_key: str, bms_key: str) -> None:
    values = {
        "dummy_api_key": dummy_key.strip(),
        "pack_id_api_key": pack_id_key.strip(),
        "bms_api_key": bms_key.strip(),
    }
    _persist_settings(values)
    _API_KEYS.update(values)


def is_valid_api_url(value: str) -> bool:
    try:
        parsed = urlsplit(value.strip())
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
            and not any(character.isspace() for character in value)
            and (parsed.port is None or 1 <= parsed.port <= 65535)
        )
    except ValueError:
        return False


def is_valid_api_key(value: str) -> bool:
    return bool(value.strip())


def validate_api_key(url: str, api_key: str) -> bool:
    response = requests.get(
        url,
        headers={"X-API-Key": api_key},
        timeout=10,
        allow_redirects=False,
    )
    if response.status_code in {401, 403}:
        return False
    if response.is_redirect:
        raise requests.exceptions.RequestException(
            "The API endpoint redirected instead of validating the key."
        )
    response.raise_for_status()
    return True


def _post(url: str, api_key: str, payload: dict[str, str]) -> None:
    try:
        response = requests.post(
            url,
            headers={"X-API-Key": api_key},
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        try:
            result = response.json()
        except ValueError:
            result = {}
        acknowledgement = result.get("message") if isinstance(result, dict) else None
        print(
            f"API POST succeeded ({response.status_code}): "
            f"{acknowledgement or 'Server accepted the scan.'}"
        )
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        messagebox.showerror(
            "API Request Failed",
            f"The server did not save the scan:\n{e}",
        )


def send_dummy_scan(record: ScanRecord) -> None:
    if not _API_CALL_ENABLED["dummy"]:
        messagebox.showwarning("api warning", "this data is not appended in server side")
        return 
    _post(
        get_api_urls()["dummy_api_url"],
        get_api_keys()["dummy_api_key"],
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
            "machine_name": record.machine_name,
            "machine_id": record.machine_id,
        },
    )


def send_pack_id_scan(record: PackIdScanRecord) -> None:
    if not _API_CALL_ENABLED["pack_id"]:
        messagebox.showwarning("api warning", "this data is not appended in server side")
        return
    _post(
        get_api_urls()["pack_id_api_url"],
        get_api_keys()["pack_id_api_key"],
        {
            "date": record.date,
            "time": record.time,
            "serial_number": record.serial_number,
            "variant": record.variant,
            "pack_qr_data": record.pack_qr_data,
            "machine_name": record.machine_name,
            "machine_id": record.machine_id,
        },
    )


def send_bms_scan(record: BmsScanRecord) -> None:
    if not _API_CALL_ENABLED["bms"]:
        messagebox.showwarning("api warning", "this data is not appended in server side")
        return
    _post(
        get_api_urls()["bms_api_url"],
        get_api_keys()["bms_api_key"],
        {
            "date": record.date,
            "time": record.time,
            "pack_qr_data": record.pack_qr_data,
            "bmb_id": record.bmb_id,
            "cmb_id": record.cmb_id,
            "status": record.status,
            "machine_name": record.machine_name,
            "machine_id": record.machine_id,
        },
    )


if __name__ == "__main__":
    try:
        print("Succeed")
    except requests.exceptions.RequestException as e:
            print("Request failed:", e)
