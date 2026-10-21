 

import hashlib
import json
import secrets
import sqlite3

from common.paths import get_common_base_dir
from common.storage import connect_db

USERS_FILE = get_common_base_dir() / "common" / "data" / "users.json"

ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLES = (ROLE_ADMIN, ROLE_OPERATOR)

MIN_PASSWORD_LENGTH = 6
_USERS_MIGRATION = "users_json_v1"


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def _import_legacy_users(connection: sqlite3.Connection) -> None:
    if connection.execute(
        "SELECT 1 FROM storage_migrations WHERE name = ?", (_USERS_MIGRATION,)
    ).fetchone():
        return

    if not USERS_FILE.exists():
        connection.execute(
            "INSERT INTO storage_migrations(name) VALUES (?)", (_USERS_MIGRATION,)
        )
        return

    try:
        with USERS_FILE.open(encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return

    if isinstance(data, dict):
        for username, record in data.items():
            if not isinstance(username, str) or not isinstance(record, dict):
                continue
            salt = record.get("salt")
            password_hash = record.get("password_hash")
            role = record.get("role", ROLE_OPERATOR)
            if not all(isinstance(value, str) for value in (salt, password_hash, role)):
                continue
            connection.execute(
                """
                INSERT OR IGNORE INTO users(username, salt, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (username, salt, password_hash, role),
            )

    connection.execute(
        "INSERT INTO storage_migrations(name) VALUES (?)", (_USERS_MIGRATION,)
    )


def _seed_default_admin_if_empty(connection: sqlite3.Connection) -> None:
    connection.execute("BEGIN IMMEDIATE")
    _import_legacy_users(connection)
    if not connection.execute("SELECT 1 FROM users LIMIT 1").fetchone():
        salt = secrets.token_hex(16)
        connection.execute(
            """
            INSERT INTO users(username, salt, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            ("Anil", salt, _hash_password("06082003", salt), ROLE_ADMIN),
        )


def authenticate_user(username: str, password: str) -> tuple[bool, str, str]:
    username = username.strip()
    password = password.strip()

    with connect_db() as connection:
        _seed_default_admin_if_empty(connection)
        if not username or not password:
            return False, "Username and password are required.", ""

        record = connection.execute(
            "SELECT salt, password_hash, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if record is None:
            return False, "Invalid username or password.", ""

        actual = _hash_password(password, record["salt"])
        if actual != record["password_hash"]:
            return False, "Invalid username or password.", ""

        return True, username, record["role"]


def list_users() -> list[tuple[str, str]]:
    with connect_db() as connection:
        _seed_default_admin_if_empty(connection)
        records = connection.execute(
            "SELECT username, role FROM users ORDER BY username"
        ).fetchall()
        return [
            (record["username"], record["role"]) for record in records
        ]


def get_user_role(username: str) -> str | None:
    with connect_db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _import_legacy_users(connection)
        record = connection.execute(
            "SELECT role FROM users WHERE username = ?", (username,)
        ).fetchone()
        return record["role"] if record else None


def add_user(username: str, password: str, role: str = ROLE_OPERATOR) -> tuple[bool, str]:
    username = username.strip()
    password = password.strip()

    if not username or not password:
        return False, "Username and password are required."
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if role not in ROLES:
        return False, "Invalid role."

    salt = secrets.token_hex(16)
    with connect_db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _import_legacy_users(connection)
        if username.lower() in {
            row["username"].lower()
            for row in connection.execute("SELECT username FROM users")
        }:
            return False, "Username already exists."
        try:
            connection.execute(
                """
                INSERT INTO users(username, salt, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (username, salt, _hash_password(password, salt), role),
            )
        except sqlite3.IntegrityError:
            return False, "Username already exists."

    role_label = "Admin" if role == ROLE_ADMIN else "Operator"
    return True, f'{role_label} "{username}" added.'


def delete_user(username: str, *, current_user: str) -> tuple[bool, str]:
    username = username.strip()
    with connect_db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _import_legacy_users(connection)
        record = connection.execute(
            "SELECT role FROM users WHERE username = ?", (username,)
        ).fetchone()
        if record is None:
            return False, "User not found."
        if username == current_user:
            return False, "You cannot delete the account you're currently logged in as."

        admin_count = connection.execute(
            "SELECT COUNT(*) FROM users WHERE role = ?", (ROLE_ADMIN,)
        ).fetchone()[0]
        user_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if record["role"] == ROLE_ADMIN and admin_count <= 1:
            return False, "At least one Admin account must remain."
        if user_count <= 1:
            return False, "At least one account must remain."

        connection.execute("DELETE FROM users WHERE username = ?", (username,))

    role_label = "Admin" if record["role"] == ROLE_ADMIN else "Operator"
    return True, f'{role_label} "{username}" removed.'