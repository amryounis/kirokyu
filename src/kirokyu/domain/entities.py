"""Task entity — the central domain object.

Domain rules enforced here:
- Title cannot be empty or whitespace-only.
- Completion toggles between COMPLETED and PENDING only.
- Archiving and un-archiving are explicit transitions.
- updated_at advances on every mutation; created_at is immutable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from kirokyu.domain.value_objects import DueDate, Priority, TaskId, TaskStatus


@dataclass
class Task:
    """A single unit of work tracked by Kirokyu."""

    id: TaskId
    title: str
    status: TaskStatus
    priority: Priority
    created_at: datetime
    updated_at: datetime
    description: str = ""
    due_date: DueDate | None = None
    starred: bool = False

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        id: TaskId,
        title: str,
        priority: Priority = Priority.MEDIUM,
        description: str = "",
        due_date: DueDate | None = None,
        starred: bool = False,
        now: datetime,
    ) -> Task:
        """Create a new Task, validating invariants at construction time.

        Args:
            id: Pre-generated identity (injected from IdProvider port).
            title: Human-readable title; must be non-empty after stripping.
            priority: Task urgency level; defaults to MEDIUM.
            description: Optional free-form notes.
            due_date: Optional DueDate value object.
            starred: Whether the task is user-favourited.
            now: Creation timestamp (injected from Clock port).

        Returns:
            A new Task in PENDING status.

        Raises:
            ValueError: If title is empty or whitespace-only.
        """
        cls._validate_title(title)
        return cls(
            id=id,
            title=title.strip(),
            status=TaskStatus.PENDING,
            priority=priority,
            description=description,
            due_date=due_date,
            starred=starred,
            created_at=now,
            updated_at=now,
        )

    # ------------------------------------------------------------------
    # Lifecycle transitions
    # ------------------------------------------------------------------

    def complete(self, now: datetime) -> None:
        """Mark the task as COMPLETED.

        Idempotent: completing an already-completed task is a no-op.

        Raises:
            ValueError: If the task is ARCHIVED.
        """
        if self.status == TaskStatus.ARCHIVED:
            raise ValueError("Cannot complete an archived task; un-archive it first.")
        if self.status == TaskStatus.COMPLETED:
            return
        self.status = TaskStatus.COMPLETED
        self.updated_at = now

    def uncomplete(self, now: datetime) -> None:
        """Revert a COMPLETED task to PENDING.

        Raises:
            ValueError: If the task is not COMPLETED.
        """
        if self.status != TaskStatus.COMPLETED:
            raise ValueError(f"Cannot un-complete a task with status {self.status.value!r}.")
        self.status = TaskStatus.PENDING
        self.updated_at = now

    def archive(self, now: datetime) -> None:
        """Move the task to ARCHIVED, hiding it from default views.

        Raises:
            ValueError: If the task is already ARCHIVED.
        """
        if self.status == TaskStatus.ARCHIVED:
            raise ValueError("Task is already archived.")
        self.status = TaskStatus.ARCHIVED
        self.updated_at = now

    def unarchive(self, now: datetime) -> None:
        """Return an ARCHIVED task to PENDING.

        Raises:
            ValueError: If the task is not ARCHIVED.
        """
        if self.status != TaskStatus.ARCHIVED:
            raise ValueError(f"Cannot un-archive a task with status {self.status.value!r}.")
        self.status = TaskStatus.PENDING
        self.updated_at = now

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def update_title(self, title: str, now: datetime) -> None:
        """Replace the title, advancing updated_at.

        Raises:
            ValueError: If title is empty or whitespace-only.
        """
        self._validate_title(title)
        self.title = title.strip()
        self.updated_at = now

    def update_description(self, description: str, now: datetime) -> None:
        """Replace the description."""
        self.description = description
        self.updated_at = now

    def update_priority(self, priority: Priority, now: datetime) -> None:
        """Change the task priority."""
        self.priority = priority
        self.updated_at = now

    def update_due_date(self, due_date: DueDate | None, now: datetime) -> None:
        """Set or clear the due date."""
        self.due_date = due_date
        self.updated_at = now

    def toggle_starred(self, now: datetime) -> None:
        """Flip the starred flag."""
        self.starred = not self.starred
        self.updated_at = now

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def is_pending(self) -> bool:
        """Return True if the task is in PENDING status."""
        return self.status == TaskStatus.PENDING

    @property
    def is_completed(self) -> bool:
        """Return True if the task is in COMPLETED status."""
        return self.status == TaskStatus.COMPLETED

    @property
    def is_archived(self) -> bool:
        """Return True if the task is in ARCHIVED status."""
        return self.status == TaskStatus.ARCHIVED

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty or whitespace-only.")

    def __repr__(self) -> str:
        return (
            f"Task(id={self.id}, title={self.title!r}, "
            f"status={self.status.value}, priority={self.priority.value})"
        )
