"""Mutation use cases for existing Tasks."""

from __future__ import annotations

from kirokyu.application.dtos import TaskOutput, UpdateTaskInput
from kirokyu.application.ports.providers import Clock
from kirokyu.application.ports.task_repository import TaskRepository
from kirokyu.domain.entities import Task
from kirokyu.domain.exceptions import TaskNotFoundError
from kirokyu.domain.value_objects import DueDate, TaskId


def _to_output(task: Task) -> TaskOutput:
    return TaskOutput(
        id=str(task.id),
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=task.status,
        due_date=task.due_date.value if task.due_date else None,
        starred=task.starred,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


def _get_or_raise(repository: TaskRepository, task_id: str) -> Task:
    task = repository.get_by_id(TaskId(task_id))
    if task is None:
        raise TaskNotFoundError(task_id)
    return task


class UpdateTask:
    """Apply partial updates to an existing Task."""

    def __init__(self, repository: TaskRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self, task_id: str, input: UpdateTaskInput) -> TaskOutput:
        task = _get_or_raise(self._repository, task_id)
        now = self._clock.now()

        if input.title is not None:
            task.update_title(input.title, now)
        if input.description is not None:
            task.update_description(input.description, now)
        if input.priority is not None:
            task.update_priority(input.priority, now)
        if input.clear_due_date:
            task.update_due_date(None, now)
        elif input.due_date is not None:
            task.update_due_date(DueDate(value=input.due_date), now)
        if input.starred is not None and input.starred != task.starred:
            task.toggle_starred(now)

        self._repository.save(task)
        return _to_output(task)


class CompleteTask:
    """Transition a Task to COMPLETED."""

    def __init__(self, repository: TaskRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self, task_id: str) -> TaskOutput:
        task = _get_or_raise(self._repository, task_id)
        task.complete(self._clock.now())
        self._repository.save(task)
        return _to_output(task)


class UncompleteTask:
    """Revert a COMPLETED Task to PENDING."""

    def __init__(self, repository: TaskRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self, task_id: str) -> TaskOutput:
        task = _get_or_raise(self._repository, task_id)
        task.uncomplete(self._clock.now())
        self._repository.save(task)
        return _to_output(task)


class ArchiveTask:
    """Move a Task to ARCHIVED."""

    def __init__(self, repository: TaskRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self, task_id: str) -> TaskOutput:
        task = _get_or_raise(self._repository, task_id)
        task.archive(self._clock.now())
        self._repository.save(task)
        return _to_output(task)


class UnarchiveTask:
    """Return an ARCHIVED Task to PENDING."""

    def __init__(self, repository: TaskRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self, task_id: str) -> TaskOutput:
        task = _get_or_raise(self._repository, task_id)
        task.unarchive(self._clock.now())
        self._repository.save(task)
        return _to_output(task)
