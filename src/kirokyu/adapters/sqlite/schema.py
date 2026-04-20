"""SQLite schema definition and migration for Kirokyu.

Schema version is stored in SQLite's built-in user_version pragma.
Migrations are additive: each step takes the DB from version N to N+1.

Currently at schema version 1 (Phase 2 baseline).
"""

from __future__ import annotations

import sqlite3

CURRENT_VERSION = 1

CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    priority    TEXT NOT NULL DEFAULT 'medium',
    status      TEXT NOT NULL DEFAULT 'pending',
    due_date    TEXT,
    starred     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""


def _get_version(conn: sqlite3.Connection) -> int:
    row = conn.execute("PRAGMA user_version").fetchone()
    return int(row[0])


def _set_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(f"PRAGMA user_version = {version}")


def migrate(conn: sqlite3.Connection) -> None:
    """Apply all pending migrations to bring the schema up to CURRENT_VERSION.

    Safe to call on every connection open — idempotent when already current.
    """
    version = _get_version(conn)

    if version < 1:
        _migrate_to_v1(conn)


def _migrate_to_v1(conn: sqlite3.Connection) -> None:
    """Create the initial schema."""
    conn.execute(CREATE_TASKS_TABLE)
    _set_version(conn, 1)
    conn.commit()
