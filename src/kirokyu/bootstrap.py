"""Bootstrap — the composition root for Kirokyu.

The single place where concrete adapter classes are named and wired
together. The CLI and API receive a UseCases bundle from here and
never import an adapter directly.

Configuration via environment variables:
    KIROKYU_ADAPTER   sqlite | json | memory   (default: sqlite)
    KIROKYU_DB_PATH   path to storage file
                      (default: ~/.kirokyu/tasks.db or ~/.kirokyu/tasks.json)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from kirokyu.adapters.in_memory.providers import SystemClock, UuidIdProvider
from kirokyu.adapters.in_memory.repository import InMemoryTaskRepository
from kirokyu.adapters.json_file.repository import JsonFileTaskRepository
from kirokyu.adapters.sqlite.repository import SqliteTaskRepository
from kirokyu.application.ports.task_repository import TaskRepository
from kirokyu.application.use_cases.create_task import CreateTask
from kirokyu.application.use_cases.mutate_tasks import (
    ArchiveTask,
    CompleteTask,
    UnarchiveTask,
    UncompleteTask,
    UpdateTask,
)
from kirokyu.application.use_cases.query_tasks import DeleteTask, GetTask, ListTasks
from kirokyu.workspaces.registry import WorkspaceRegistry

ADAPTER_ENV = "KIROKYU_ADAPTER"
DB_PATH_ENV = "KIROKYU_DB_PATH"

DEFAULT_SQLITE_PATH = Path.home() / ".kirokyu" / "tasks.db"
DEFAULT_JSON_PATH = Path.home() / ".kirokyu" / "tasks.json"


@dataclass
class UseCases:
    """All constructed use cases, ready to call."""

    create_task: CreateTask
    get_task: GetTask
    list_tasks: ListTasks
    update_task: UpdateTask
    complete_task: CompleteTask
    uncomplete_task: UncompleteTask
    archive_task: ArchiveTask
    unarchive_task: UnarchiveTask
    delete_task: DeleteTask


def build_use_cases(
    adapter: str | None = None,
    db_path: str | Path | None = None,
    workspace: str | None = None,
) -> UseCases:
    """Construct and return all use cases wired to the selected adapter."""
    resolved_adapter = adapter or os.environ.get(ADAPTER_ENV, "sqlite")
    resolved_db_path = _resolve_db_path(workspace, db_path)
    repository = _build_repository(resolved_adapter, resolved_db_path)
    return _wire(repository)


def _resolve_db_path(
    workspace: str | None,
    db_path: str | Path | None,
) -> str | Path | None:
    """Resolve the db path from a workspace name or a direct path."""
    if workspace is None:
        return db_path
    registry = WorkspaceRegistry()
    ws = registry.get(workspace)
    if ws is None:
        raise ValueError(f"Workspace {workspace!r} not found in registry.")
    registry.touch(workspace)
    return ws.db_path


def _build_repository(adapter: str, db_path: str | Path | None) -> TaskRepository:
    if adapter == "memory":
        return InMemoryTaskRepository()

    if adapter == "sqlite":
        path = Path(db_path or os.environ.get(DB_PATH_ENV) or DEFAULT_SQLITE_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        return SqliteTaskRepository(db_path=path)

    if adapter == "json":
        path = Path(db_path or os.environ.get(DB_PATH_ENV) or DEFAULT_JSON_PATH)
        return JsonFileTaskRepository(file_path=path)

    raise ValueError(f"Unknown adapter {adapter!r}. Valid values: 'sqlite', 'json', 'memory'.")


def _wire(repository: TaskRepository) -> UseCases:
    """Wire providers and use cases against the given repository."""
    id_provider = UuidIdProvider()
    clock = SystemClock()

    return UseCases(
        create_task=CreateTask(repository, id_provider, clock),
        get_task=GetTask(repository),
        list_tasks=ListTasks(repository),
        update_task=UpdateTask(repository, clock),
        complete_task=CompleteTask(repository, clock),
        uncomplete_task=UncompleteTask(repository, clock),
        archive_task=ArchiveTask(repository, clock),
        unarchive_task=UnarchiveTask(repository, clock),
        delete_task=DeleteTask(repository),
    )
