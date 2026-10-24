 

import json
import sqlite3
from contextlib import closing, contextmanager
from typing import Iterator

from common.storage import DATABASE_FILE
from models.hv.nomenclature.serial_number import build_serial_number, parse_serial_number
from models.hv.session.paths import get_base_dir

PACK_SESSION_DB = get_base_dir() / "data" / "pack_session.db"
LEGACY_PACK_SESSION_FILE = get_base_dir() / "data" / "pack_session.json"
_APP_DB_MIGRATION = "app_data_pack_state_v1"
_JSON_MIGRATION = "pack_session_json_v1"


def _migration_completed(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM storage_migrations WHERE name = ?", (name,)
    ).fetchone() is not None


def _mark_migration_completed(connection: sqlite3.Connection, name: str) -> None:
    connection.execute("INSERT INTO storage_migrations(name) VALUES (?)", (name,))


def _import_shared_database_state(connection: sqlite3.Connection) -> None:
    if _migration_completed(connection, _APP_DB_MIGRATION):
        return

    if not DATABASE_FILE.exists():
        _mark_migration_completed(connection, _APP_DB_MIGRATION)
        return

    with closing(sqlite3.connect(DATABASE_FILE, timeout=10)) as legacy_connection:
        has_app_state = legacy_connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'app_state'"
        ).fetchone()
        if has_app_state:
            rows = legacy_connection.execute(
                "SELECT key, value FROM app_state "
                "WHERE key IN ('serial_number', 'serial_count')"
            ).fetchall()
            connection.executemany(
                "INSERT OR IGNORE INTO app_state(key, value) VALUES (?, ?)", rows
            )

    _mark_migration_completed(connection, _APP_DB_MIGRATION)


def _import_legacy_json(connection: sqlite3.Connection) -> None:
    if _migration_completed(connection, _JSON_MIGRATION):
        return

    if not LEGACY_PACK_SESSION_FILE.exists():
        _mark_migration_completed(connection, _JSON_MIGRATION)
        return

    try:
        with LEGACY_PACK_SESSION_FILE.open(encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return

    if isinstance(data, dict):
        for key in ("serial_number", "serial_count"):
            value = data.get(key)
            if isinstance(value, str):
                connection.execute(
                    "INSERT OR IGNORE INTO app_state(key, value) VALUES (?, ?)",
                    (key, value),
                )

    _mark_migration_completed(connection, _JSON_MIGRATION)


@contextmanager
def _connect_db() -> Iterator[sqlite3.Connection]:
    PACK_SESSION_DB.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(PACK_SESSION_DB, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS app_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS storage_migrations (name TEXT PRIMARY KEY)"
        )
        connection.execute("BEGIN IMMEDIATE")
        _import_shared_database_state(connection)
        _import_legacy_json(connection)
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def _load_value(key: str) -> str:
    with _connect_db() as connection:
        record = connection.execute(
            "SELECT value FROM app_state WHERE key = ?", (key,)
        ).fetchone()
        return record["value"] if record else ""


def _save_values(values: dict[str, str]) -> None:
    with _connect_db() as connection:
        connection.executemany(
            """
            INSERT INTO app_state(key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            values.items(),
        )


def save_pack_serial(serial_number: str) -> None:
    serial_number = serial_number.strip()
    if not serial_number:
        return

    values = {"serial_number": serial_number}
    parsed = parse_serial_number(serial_number)
    if parsed is not None:
        values["serial_count"] = parsed.serial_count
    _save_values(values)


def load_pack_serial() -> str:
    return _load_value("serial_number").strip()


def load_pack_serial_count() -> str:
    return _load_value("serial_count").strip()


def save_pack_serial_count(serial_count: str) -> None:
    serial_count = serial_count.strip()
    if serial_count:
        _save_values({"serial_count": serial_count})


def increment_pack_serial() -> str:
    current = load_pack_serial()
    if not current:
        return ""

    parsed = parse_serial_number(current)
    if parsed is None:
        return current

    next_count = int(parsed.serial_count) + 1
    if next_count > 99999:
        raise ValueError("Serial count has reached the maximum value of 99999.")
    new_count = str(next_count).zfill(5)

    new_serial = build_serial_number(
        plant=parsed.plant,
        line=parsed.line,
        when=parsed.as_date,
        serial_count=new_count,
        model=parsed.model,
        variant=parsed.variant,
        cell_mfr=parsed.cell_mfr,
        category=parsed.category,
    )
    save_pack_serial(new_serial)
    return new_serial
