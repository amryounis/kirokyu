"""Domain value objects.

All implemented as frozen dataclasses — immutable, equality by value.
No third-party dependencies; standard library only (Decision 15).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from enum import Enum


@dataclass(frozen=True)
class TaskId:
    """Opaque identifier for a Task, wrapping a UUID string."""

    value: str

    def __post_init__(self) -> None:
        try:
            uuid.UUID(self.value)
        except ValueError as exc:
            raise ValueError(f"TaskId must be a valid UUID string, got: {self.value!r}") from exc

    @classmethod
    def generate(cls) -> TaskId:
        """Create a random v4 UUID-based TaskId."""
        return cls(value=str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(Enum):
    """Decision 17: three states only. Deleted tasks are removed, not flagged."""

    PENDING = "pending"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class DueDate:
    """A validated due date with domain semantics."""

    value: date

    def is_overdue(self, relative_to: date) -> bool:
        return self.value < relative_to

    def __str__(self) -> str:
        return self.value.isoformat()
