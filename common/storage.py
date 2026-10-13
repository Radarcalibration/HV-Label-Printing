from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from common.paths import get_common_base_dir

DATABASE_FILE = get_common_base_dir() / "common" / "data" / "app_data.db"


@contextmanager
def connect_db() -> Iterator[sqlite3.Connection]:
    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS users_username_casefold "
            "ON users(username COLLATE NOCASE)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS storage_migrations (
                name TEXT PRIMARY KEY
            )
            """
        )
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()
