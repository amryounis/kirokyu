"""CreateTask use case."""

from __future__ import annotations

from kirokyu.application.dtos import CreateTaskInput, TaskOutput
from kirokyu.application.ports.providers import Clock, IdProvider
from kirokyu.application.ports.task_repository import TaskRepository
from kirokyu.domain.entities import Task
from kirokyu.domain.value_objects import DueDate


class CreateTask:
    """Create a new Task and persist it."""

    def __init__(
        self,
        repository: TaskRepository,
        id_provider: IdProvider,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._id_provider = id_provider
        self._clock = clock

    def execute(self, input: CreateTaskInput) -> TaskOutput:
        now = self._clock.now()
        task = Task.create(
            id=self._id_provider.next_id(),
            title=input.title,
            priority=input.priority,
            description=input.description,
            due_date=DueDate(value=input.due_date) if input.due_date else None,
            starred=input.starred,
            now=now,
        )
        self._repository.save(task)
        return _to_output(task)


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
