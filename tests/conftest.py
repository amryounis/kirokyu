"""Shared pytest fixtures for Phase 1 tests.

All fixtures are function-scoped (default) — each test gets a fresh
in-memory repository, a predictable ID sequence, and a fixed clock.
No shared mutable state between tests.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from kirokyu.adapters.in_memory.providers import FixedClock, SequentialIdProvider
from kirokyu.adapters.in_memory.repository import InMemoryTaskRepository
from kirokyu.application.use_cases.create_task import CreateTask
from kirokyu.application.use_cases.mutate_tasks import (
    ArchiveTask,
    CompleteTask,
    UnarchiveTask,
    UncompleteTask,
    UpdateTask,
)
from kirokyu.application.use_cases.query_tasks import DeleteTask, GetTask, ListTasks

FIXED_NOW = datetime(2026, 4, 20, 9, 0, 0)


@pytest.fixture()
def repo() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


@pytest.fixture()
def id_provider() -> SequentialIdProvider:
    return SequentialIdProvider()


@pytest.fixture()
def clock() -> FixedClock:
    return FixedClock(fixed=FIXED_NOW)


@pytest.fixture()
def create_task(
    repo: InMemoryTaskRepository,
    id_provider: SequentialIdProvider,
    clock: FixedClock,
) -> CreateTask:
    return CreateTask(repository=repo, id_provider=id_provider, clock=clock)


@pytest.fixture()
def get_task(repo: InMemoryTaskRepository) -> GetTask:
    return GetTask(repository=repo)


@pytest.fixture()
def list_tasks(repo: InMemoryTaskRepository) -> ListTasks:
    return ListTasks(repository=repo)


@pytest.fixture()
def delete_task(repo: InMemoryTaskRepository) -> DeleteTask:
    return DeleteTask(repository=repo)


@pytest.fixture()
def update_task(repo: InMemoryTaskRepository, clock: FixedClock) -> UpdateTask:
    return UpdateTask(repository=repo, clock=clock)


@pytest.fixture()
def complete_task(repo: InMemoryTaskRepository, clock: FixedClock) -> CompleteTask:
    return CompleteTask(repository=repo, clock=clock)


@pytest.fixture()
def uncomplete_task(repo: InMemoryTaskRepository, clock: FixedClock) -> UncompleteTask:
    return UncompleteTask(repository=repo, clock=clock)


@pytest.fixture()
def archive_task(repo: InMemoryTaskRepository, clock: FixedClock) -> ArchiveTask:
    return ArchiveTask(repository=repo, clock=clock)


@pytest.fixture()
def unarchive_task(repo: InMemoryTaskRepository, clock: FixedClock) -> UnarchiveTask:
    return UnarchiveTask(repository=repo, clock=clock)
