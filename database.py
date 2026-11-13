import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data") / "privatedocs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS departments (
    id   INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY,
    username        TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('admin', 'staff')),
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until    TEXT
);

CREATE TABLE IF NOT EXISTS user_departments (
    user_id       INTEGER NOT NULL REFERENCES users(id),
    department_id INTEGER NOT NULL REFERENCES departments(id),
    PRIMARY KEY (user_id, department_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id            TEXT PRIMARY KEY,
    display_name  TEXT NOT NULL,
    file_type     TEXT NOT NULL,
    stored_name   TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(id),
    status        TEXT NOT NULL DEFAULT 'queued',
    error_message TEXT,
    chunk_count   INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL,
    effective_date TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id       INTEGER PRIMARY KEY,
    ts       TEXT NOT NULL,
    username TEXT,
    event    TEXT NOT NULL,
    detail   TEXT
);
"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row            # read columns by name: row["status"]
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite ignores links unless this is on
    return conn


def init_db():
    conn = connect()
    conn.executescript(SCHEMA)
    # Older databases were created without effective_date: add the column once.
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(documents)")]
    if "effective_date" not in columns:
        conn.execute("ALTER TABLE documents ADD COLUMN effective_date TEXT")
    # Older databases have no must_change_password: add it once. 1 = this person must choose a new password.
    user_columns = [row["name"] for row in conn.execute("PRAGMA table_info(users)")]
    if "must_change_password" not in user_columns:
        conn.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0")
    conn.commit()
    conn.close()
