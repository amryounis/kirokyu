"""TaskRepository port — the persistence contract for Task aggregates.

The application layer declares what it needs; adapters implement it.
Use cases depend on this ABC, never on a concrete class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from kirokyu.domain.entities import Task
from kirokyu.domain.value_objects import TaskId


class TaskRepository(ABC):
    """Abstract contract for storing and retrieving Task aggregates."""

    @abstractmethod
    def save(self, task: Task) -> None:
        """Persist a Task (insert if new, update if existing)."""
        ...

    @abstractmethod
    def get_by_id(self, task_id: TaskId) -> Task | None:
        """Return the Task with the given id, or None if not found."""
        ...

    @abstractmethod
    def list_all(self) -> list[Task]:
        """Return all Tasks in storage, in no guaranteed order."""
        ...

    @abstractmethod
    def delete(self, task_id: TaskId) -> None:
        """Permanently remove the Task with the given id.

        Silently succeeds if the task does not exist (idempotent).
        """
        ...
