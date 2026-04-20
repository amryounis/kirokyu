"""GetTask, ListTasks, and DeleteTask use cases."""

from __future__ import annotations

from kirokyu.application.dtos import TaskOutput
from kirokyu.application.ports.task_repository import TaskRepository
from kirokyu.domain.entities import Task
from kirokyu.domain.exceptions import TaskNotFoundError
from kirokyu.domain.value_objects import TaskId


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


class GetTask:
    """Retrieve a single Task by id."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def execute(self, task_id: str) -> TaskOutput:
        task = self._repository.get_by_id(TaskId(task_id))
        if task is None:
            raise TaskNotFoundError(task_id)
        return _to_output(task)


class ListTasks:
    """Return all tasks."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def execute(self) -> list[TaskOutput]:
        return [_to_output(t) for t in self._repository.list_all()]


class DeleteTask:
    """Permanently remove a Task (Decision 17: deletion = removal, not a flag)."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def execute(self, task_id: str) -> None:
        tid = TaskId(task_id)
        if self._repository.get_by_id(tid) is None:
            raise TaskNotFoundError(task_id)
        self._repository.delete(tid)
