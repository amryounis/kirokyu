"""JsonFileTaskRepository — TaskRepository backed by a single JSON file.

Storage format:
    {
        "version": 1,
        "tasks": {
            "<uuid>": { ...task fields... },
            ...
        }
    }

Writes are atomic — data is written to a temp file first, then renamed.
Supports file_path=None for in-memory operation (useful in tests).
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

from kirokyu.application.ports.task_repository import TaskRepository
from kirokyu.domain.entities import Task
from kirokyu.domain.value_objects import DueDate, Priority, TaskId, TaskStatus

SCHEMA_VERSION = 1


class JsonFileTaskRepository(TaskRepository):
    """Persists Tasks as a JSON file on disk.

    Args:
        file_path: Path to the .json data file. Pass None for
                   in-memory operation without filesystem side-effects.
    """

    def __init__(self, file_path: str | Path | None = None) -> None:
        self._file_path = Path(file_path) if file_path else None
        self._store: dict[str, dict[str, Any]] | None = None

    # ------------------------------------------------------------------
    # TaskRepository protocol
    # ------------------------------------------------------------------

    def save(self, task: Task) -> None:
        """Insert or replace the task."""
        store = self._load()
        store[task.id.value] = _to_dict(task)
        self._persist(store)

    def get_by_id(self, task_id: TaskId) -> Task | None:
        """Return the Task with the given id, or None if not found."""
        store = self._load()
        raw = store.get(task_id.value)
        return _to_task(raw) if raw is not None else None

    def list_all(self) -> list[Task]:
        """Return all Tasks in storage."""
        return [_to_task(v) for v in self._load().values()]

    def delete(self, task_id: TaskId) -> None:
        """Permanently remove the Task with the given id."""
        store = self._load()
        store.pop(task_id.value, None)
        self._persist(store)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Return the number of stored tasks."""
        return len(self._load())

    def _load(self) -> dict[str, dict[str, Any]]:
        """Return the in-memory store, loading from disk if needed."""
        if self._store is not None:
            return self._store

        if self._file_path is None or not self._file_path.exists():
            self._store = {}
            return self._store

        with self._file_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        if data.get("version") != SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported JSON store version {data.get('version')!r}; expected {SCHEMA_VERSION}"
            )

        self._store = data.get("tasks", {})
        return self._store

    def _persist(self, store: dict[str, dict[str, Any]]) -> None:
        """Write the store to disk atomically."""
        self._store = store

        if self._file_path is None:
            return

        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {"version": SCHEMA_VERSION, "tasks": store},
            indent=2,
            ensure_ascii=False,
        )

        dir_ = self._file_path.parent
        fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
            if os.name == "nt" and self._file_path.exists():
                self._file_path.unlink()
            os.rename(tmp_path, self._file_path)
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


def _to_dict(task: Task) -> dict[str, Any]:
    return {
        "id": task.id.value,
        "title": task.title,
        "description": task.description,
        "priority": task.priority.value,
        "status": task.status.value,
        "due_date": task.due_date.value.isoformat() if task.due_date else None,
        "starred": task.starred,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


def _to_task(raw: dict[str, Any]) -> Task:
    due_date: DueDate | None = None
    if raw.get("due_date") is not None:
        due_date = DueDate(value=date.fromisoformat(raw["due_date"]))

    return Task(
        id=TaskId(value=raw["id"]),
        title=raw["title"],
        description=raw["description"],
        priority=Priority(raw["priority"]),
        status=TaskStatus(raw["status"]),
        due_date=due_date,
        starred=bool(raw["starred"]),
        created_at=datetime.fromisoformat(raw["created_at"]),
        updated_at=datetime.fromisoformat(raw["updated_at"]),
    )
