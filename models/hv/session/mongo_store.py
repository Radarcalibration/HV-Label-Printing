from __future__ import annotations

import os
import socket
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

_client: MongoClient | None = None
_client_uri: str | None = None
_indexed_scan_collections: set[tuple[str, str]] = set()
_indexed_session_collections: set[tuple[str, str]] = set()
_DATABASE_NAME = "hv_label_printing"


def _get_collection(name: str) -> Collection:
    global _client, _client_uri

    uri = os.environ.get("MONGODB_URI", "").strip()
    if not uri:
        raise RuntimeError(
            "MongoDB is not configured. Set the MONGODB_URI environment variable "
            "to the Atlas connection string."
        )

    if _client is None or _client_uri != uri:
        if _client is not None:
            _client.close()
        _client = MongoClient(
            uri,
            appname="HVLabelPrinter",
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
        )
        _client_uri = uri
        _indexed_scan_collections.clear()
        _indexed_session_collections.clear()
        try:
            _client.admin.command("ping")
        except PyMongoError:
            _client.close()
            _client = None
            _client_uri = None
            raise

    database_name = os.environ.get("MONGODB_DATABASE", _DATABASE_NAME).strip()
    if not database_name:
        raise RuntimeError("MONGODB_DATABASE cannot be empty.")
    return _client[database_name][name]


def _ensure_scan_indexes(collection_name: str) -> Collection:
    collection = _get_collection(collection_name)
    key = (os.environ.get("MONGODB_DATABASE", _DATABASE_NAME), collection_name)
    if key not in _indexed_scan_collections:
        collection.create_index("created_at")
        collection.create_index([("updated_at", -1), ("_id", -1)])
        if collection_name == "bms_scan_logs":
            collection.create_index("pack_qr_data")
        _indexed_scan_collections.add(key)
    return collection


def _record_document(record: Any) -> dict[str, Any]:
    if not is_dataclass(record):
        raise TypeError("MongoDB scan records must be dataclass instances.")
    document = asdict(record)
    now = datetime.now(timezone.utc)
    document.update(schema_version=1, created_at=now, updated_at=now)
    return document


def insert_scan_record(collection_name: str, record: Any) -> None:
    _ensure_scan_indexes(collection_name).insert_one(_record_document(record))


def list_scan_records(collection_name: str) -> list[dict[str, Any]]:
    return list(_ensure_scan_indexes(collection_name).find().sort("_id", 1))


def update_scan_record_at_row(
    collection_name: str, row_number: int, updates: dict[str, Any]
) -> bool:
    if row_number < 2:
        return False
    collection = _ensure_scan_indexes(collection_name)
    document = collection.find().sort("_id", 1).skip(row_number - 2).limit(1)
    record = next(document, None)
    if record is None:
        return False
    return collection.update_one(
        {"_id": record["_id"]},
        {"$set": {**updates, "updated_at": datetime.now(timezone.utc)}},
    ).matched_count == 1


def find_latest_scan_record(
    collection_name: str, field: str, value: str
) -> dict[str, Any] | None:
    return _ensure_scan_indexes(collection_name).find_one(
        {field: value}, sort=[("_id", -1)]
    )


def update_latest_scan_record(
    collection_name: str, field: str, value: str, updates: dict[str, Any]
) -> bool:
    collection = _ensure_scan_indexes(collection_name)
    record = collection.find_one({field: value}, sort=[("_id", -1)])
    if record is None:
        return False
    return collection.update_one(
        {"_id": record["_id"]},
        {"$set": {**updates, "updated_at": datetime.now(timezone.utc)}},
    ).matched_count == 1


def get_scan_collection_watermark(
    collection_name: str,
) -> tuple[datetime | None, str] | None:
    record = _ensure_scan_indexes(collection_name).find_one(
        {},
        projection={"updated_at": 1, "created_at": 1},
        sort=[("updated_at", -1), ("_id", -1)],
    )
    if record is None:
        return None
    return record.get("updated_at") or record.get("created_at"), str(record["_id"])


def start_login_session(username: str, role: str) -> str:
    sessions = _get_collection("login_sessions")
    key = (os.environ.get("MONGODB_DATABASE", _DATABASE_NAME), "login_sessions")
    if key not in _indexed_session_collections:
        sessions.create_index("login_at")
        _indexed_session_collections.add(key)
    result = sessions.insert_one(
        {
            "username": username,
            "role": role,
            "machine_name": socket.gethostname(),
            "login_at": datetime.now(timezone.utc),
            "logout_at": None,
            "schema_version": 1,
        }
    )
    return str(result.inserted_id)


def end_login_session(session_id: str) -> None:
    try:
        object_id = ObjectId(session_id)
    except (InvalidId, TypeError) as exc:
        raise ValueError("The login session identifier is invalid.") from exc

    result = _get_collection("login_sessions").update_one(
        {"_id": object_id, "logout_at": None},
        {"$set": {"logout_at": datetime.now(timezone.utc)}},
    )
    if result.matched_count != 1:
        raise RuntimeError("The login session was not found or was already closed.")


def load_pack_state() -> dict[str, str] | None:
    state = _get_collection("application_state").find_one({"_id": "pack_serial"})
    if state is None:
        return None
    return {
        key: str(state[key])
        for key in ("serial_number", "serial_count")
        if state.get(key) is not None
    }


def save_pack_state(updates: dict[str, str]) -> None:
    _get_collection("application_state").update_one(
        {"_id": "pack_serial"},
        {
            "$set": {**updates, "updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"schema_version": 1},
        },
        upsert=True,
    )


def advance_pack_serial(
    expected_serial: str, next_serial: str, next_count: str
) -> bool:
    result = _get_collection("application_state").update_one(
        {"_id": "pack_serial", "serial_number": expected_serial},
        {
            "$set": {
                "serial_number": next_serial,
                "serial_count": next_count,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return result.modified_count == 1


def insert_legacy_record(
    collection_name: str, record: dict[str, Any], *, source_file: str, row_number: int
) -> bool:
    collection = _ensure_scan_indexes(collection_name)
    collection.create_index(
        "legacy_key",
        unique=True,
        partialFilterExpression={"legacy_key": {"$exists": True}},
    )
    legacy_key = f"{socket.gethostname()}:{source_file}:{row_number}"
    now = datetime.now(timezone.utc)
    document = {
        **record,
        "schema_version": 1,
        "created_at": now,
        "updated_at": now,
        "legacy_key": legacy_key,
    }
    result = collection.update_one(
        {"legacy_key": legacy_key}, {"$setOnInsert": document}, upsert=True
    )
    return result.upserted_id is not None


def ping() -> None:
    _get_collection("application_state")
