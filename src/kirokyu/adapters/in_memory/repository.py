"""InMemoryTaskRepository — in-process dict-backed TaskRepository.

Used in all unit tests and as the default during development before
a persistence adapter is wired in Phase 2.
"""

from __future__ import annotations

import copy

from kirokyu.application.ports.task_repository import TaskRepository
from kirokyu.domain.entities import Task
from kirokyu.domain.value_objects import TaskId


class InMemoryTaskRepository(TaskRepository):
    """Stores Tasks in a plain dict keyed by TaskId.value.

    Stores copies of tasks on save so that callers mutating a Task
    object after saving do not silently corrupt stored state.
    """

    def __init__(self) -> None:
        self._store: dict[str, Task] = {}

    def save(self, task: Task) -> None:
        """Insert or replace the task (keyed by id)."""
        self._store[task.id.value] = copy.deepcopy(task)

    def get_by_id(self, task_id: TaskId) -> Task | None:
        """Return a copy of the stored task, or None."""
        stored = self._store.get(task_id.value)
        return copy.deepcopy(stored) if stored is not None else None

    def list_all(self) -> list[Task]:
        """Return copies of all stored tasks."""
        return [copy.deepcopy(t) for t in self._store.values()]

    def delete(self, task_id: TaskId) -> None:
        """Remove the task; silently succeeds if absent (idempotent)."""
        self._store.pop(task_id.value, None)

    def count(self) -> int:
        """Return the number of stored tasks."""
        return len(self._store)

    def clear(self) -> None:
        """Wipe all tasks — useful for fixture teardown."""
        self._store.clear()
