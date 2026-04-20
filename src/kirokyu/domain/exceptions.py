"""Domain-level exceptions.

Raised by the domain layer, caught and translated at the use-case or
adapter boundary — never leaked raw to the outside world.
"""


class TaskNotFoundError(Exception):
    """Raised when a requested Task does not exist in the repository."""

    def __init__(self, task_id: str) -> None:
        super().__init__(f"Task not found: {task_id!r}")
        self.task_id = task_id
