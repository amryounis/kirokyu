"""SqliteTaskRepository — TaskRepository backed by a SQLite database file."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

from kirokyu.adapters.sqlite.schema import migrate
from kirokyu.application.ports.task_repository import TaskRepository
from kirokyu.domain.entities import Task
from kirokyu.domain.value_objects import DueDate, Priority, TaskId, TaskStatus


class SqliteTaskRepository(TaskRepository):
    """Persists Tasks in a single SQLite database file.

    Args:
        db_path: Path to the .db file. Pass \":memory:\" for an
                 in-process database useful in tests.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    @property
    def _connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            migrate(self._conn)
        return self._conn

    def close(self) -> None:
        """Close the database connection explicitly."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> SqliteTaskRepository:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # TaskRepository protocol
    # ------------------------------------------------------------------

    def save(self, task: Task) -> None:
        """Upsert a Task row (insert or replace on id conflict)."""
        self._connection.execute(
            """
            INSERT INTO tasks
                (id, title, description, priority, status, due_date,
                 starred, created_at, updated_at)
            VALUES
                (:id, :title, :description, :priority, :status, :due_date,
                 :starred, :created_at, :updated_at)
            ON CONFLICT(id) DO UPDATE SET
                title       = excluded.title,
                description = excluded.description,
                priority    = excluded.priority,
                status      = excluded.status,
                due_date    = excluded.due_date,
                starred     = excluded.starred,
                updated_at  = excluded.updated_at
            """,
            _to_row(task),
        )
        self._connection.commit()

    def get_by_id(self, task_id: TaskId) -> Task | None:
        """Return the Task with the given id, or None if not found."""
        row = self._connection.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id.value,)
        ).fetchone()
        return _to_task(row) if row else None

    def list_all(self) -> list[Task]:
        """Return all Tasks in storage."""
        rows = self._connection.execute("SELECT * FROM tasks").fetchall()
        return [_to_task(r) for r in rows]

    def delete(self, task_id: TaskId) -> None:
        """Permanently remove the Task with the given id."""
        self._connection.execute("DELETE FROM tasks WHERE id = ?", (task_id.value,))
        self._connection.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Return the number of rows in the tasks table."""
        row = self._connection.execute("SELECT COUNT(*) FROM tasks").fetchone()
        return int(row[0])


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


def _to_row(task: Task) -> dict[str, str | int | None]:
    return {
        "id": task.id.value,
        "title": task.title,
        "description": task.description,
        "priority": task.priority.value,
        "status": task.status.value,
        "due_date": task.due_date.value.isoformat() if task.due_date else None,
        "starred": 1 if task.starred else 0,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


def _to_task(row: sqlite3.Row) -> Task:
    due_date: DueDate | None = None
    if row["due_date"] is not None:
        due_date = DueDate(value=date.fromisoformat(row["due_date"]))

    return Task(
        id=TaskId(value=row["id"]),
        title=row["title"],
        description=row["description"],
        priority=Priority(row["priority"]),
        status=TaskStatus(row["status"]),
        due_date=due_date,
        starred=bool(row["starred"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )
