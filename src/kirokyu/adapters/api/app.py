"""REST API driving adapter — FastAPI application for Kirokyu.

Run with:
    uvicorn kirokyu.adapters.api.app:app --reload

Endpoints:
    POST   /tasks
    GET    /tasks
    GET    /tasks/{id}
    PATCH  /tasks/{id}
    POST   /tasks/{id}/complete
    POST   /tasks/{id}/uncomplete
    POST   /tasks/{id}/archive
    POST   /tasks/{id}/unarchive
    DELETE /tasks/{id}
"""

from __future__ import annotations

from typing import Never

from fastapi import Depends, FastAPI, HTTPException, status

from kirokyu.application.dtos import CreateTaskInput, TaskOutput, UpdateTaskInput
from kirokyu.bootstrap import UseCases, build_use_cases
from kirokyu.domain.exceptions import TaskNotFoundError

app = FastAPI(
    title="Kirokyu",
    description="Personal task manager — REST API.",
    version="0.1.0",
)

_use_cases: UseCases | None = None


def get_use_cases() -> UseCases:
    global _use_cases
    if _use_cases is None:
        _use_cases = build_use_cases()
    return _use_cases


def _raise_404(task_id: str) -> Never:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task not found: {task_id!r}",
    )


@app.post("/tasks", response_model=TaskOutput, status_code=status.HTTP_201_CREATED)
def create_task(
    input_: CreateTaskInput,
    uc: UseCases = Depends(get_use_cases),
) -> TaskOutput:
    """Create a new task."""
    return uc.create_task.execute(input_)


@app.get("/tasks", response_model=list[TaskOutput])
def list_tasks(
    uc: UseCases = Depends(get_use_cases),
) -> list[TaskOutput]:
    """Return all tasks."""
    return uc.list_tasks.execute()


@app.get("/tasks/{task_id}", response_model=TaskOutput)
def get_task(
    task_id: str,
    uc: UseCases = Depends(get_use_cases),
) -> TaskOutput:
    """Return a single task by ID."""
    try:
        return uc.get_task.execute(task_id)
    except TaskNotFoundError:
        _raise_404(task_id)


@app.patch("/tasks/{task_id}", response_model=TaskOutput)
def update_task(
    task_id: str,
    input_: UpdateTaskInput,
    uc: UseCases = Depends(get_use_cases),
) -> TaskOutput:
    """Update one or more fields on an existing task."""
    try:
        return uc.update_task.execute(task_id, input_)
    except TaskNotFoundError:
        _raise_404(task_id)


@app.post("/tasks/{task_id}/complete", response_model=TaskOutput)
def complete_task(
    task_id: str,
    uc: UseCases = Depends(get_use_cases),
) -> TaskOutput:
    """Mark a task as completed."""
    try:
        return uc.complete_task.execute(task_id)
    except TaskNotFoundError:
        _raise_404(task_id)


@app.post("/tasks/{task_id}/uncomplete", response_model=TaskOutput)
def uncomplete_task(
    task_id: str,
    uc: UseCases = Depends(get_use_cases),
) -> TaskOutput:
    """Revert a completed task to pending."""
    try:
        return uc.uncomplete_task.execute(task_id)
    except TaskNotFoundError:
        _raise_404(task_id)


@app.post("/tasks/{task_id}/archive", response_model=TaskOutput)
def archive_task(
    task_id: str,
    uc: UseCases = Depends(get_use_cases),
) -> TaskOutput:
    """Archive a task."""
    try:
        return uc.archive_task.execute(task_id)
    except TaskNotFoundError:
        _raise_404(task_id)


@app.post("/tasks/{task_id}/unarchive", response_model=TaskOutput)
def unarchive_task(
    task_id: str,
    uc: UseCases = Depends(get_use_cases),
) -> TaskOutput:
    """Return an archived task to pending."""
    try:
        return uc.unarchive_task.execute(task_id)
    except TaskNotFoundError:
        _raise_404(task_id)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    uc: UseCases = Depends(get_use_cases),
) -> None:
    """Permanently delete a task."""
    try:
        uc.delete_task.execute(task_id)
    except TaskNotFoundError:
        _raise_404(task_id)
