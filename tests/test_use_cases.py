"""Use case tests — full stack through in-memory adapters, no mocking."""

from __future__ import annotations

from datetime import date

import pytest

from kirokyu.adapters.in_memory.repository import InMemoryTaskRepository
from kirokyu.application.dtos import CreateTaskInput, UpdateTaskInput
from kirokyu.application.use_cases.create_task import CreateTask
from kirokyu.application.use_cases.mutate_tasks import (
    ArchiveTask,
    CompleteTask,
    UnarchiveTask,
    UncompleteTask,
    UpdateTask,
)
from kirokyu.application.use_cases.query_tasks import DeleteTask, GetTask, ListTasks
from kirokyu.domain.exceptions import TaskNotFoundError
from kirokyu.domain.value_objects import Priority, TaskStatus


class TestCreateTask:
    def test_returns_task_output_with_correct_title(self, create_task: CreateTask):
        out = create_task.execute(CreateTaskInput(title="Buy milk"))
        assert out.title == "Buy milk"

    def test_new_task_is_pending(self, create_task: CreateTask):
        out = create_task.execute(CreateTaskInput(title="Something"))
        assert out.status == TaskStatus.PENDING

    def test_assigns_sequential_id(self, create_task: CreateTask):
        a = create_task.execute(CreateTaskInput(title="First"))
        b = create_task.execute(CreateTaskInput(title="Second"))
        assert a.id != b.id

    def test_persists_to_repo(self, create_task: CreateTask, repo: InMemoryTaskRepository):
        create_task.execute(CreateTaskInput(title="Persisted"))
        assert repo.count() == 1

    def test_default_priority_is_medium(self, create_task: CreateTask):
        out = create_task.execute(CreateTaskInput(title="Task"))
        assert out.priority == Priority.MEDIUM

    def test_accepts_high_priority(self, create_task: CreateTask):
        out = create_task.execute(CreateTaskInput(title="Urgent", priority=Priority.HIGH))
        assert out.priority == Priority.HIGH

    def test_accepts_due_date(self, create_task: CreateTask):
        out = create_task.execute(CreateTaskInput(title="Due soon", due_date=date(2026, 5, 1)))
        assert out.due_date == date(2026, 5, 1)

    def test_timestamps_are_iso_strings(self, create_task: CreateTask):
        from datetime import datetime

        out = create_task.execute(CreateTaskInput(title="Task"))
        datetime.fromisoformat(out.created_at)
        datetime.fromisoformat(out.updated_at)

    def test_created_at_equals_updated_at_initially(self, create_task: CreateTask):
        out = create_task.execute(CreateTaskInput(title="Task"))
        assert out.created_at == out.updated_at

    def test_rejects_blank_title(self, create_task: CreateTask):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            create_task.execute(CreateTaskInput(title="   "))


class TestGetTask:
    def test_retrieves_task_by_id(self, create_task: CreateTask, get_task: GetTask):
        created = create_task.execute(CreateTaskInput(title="Retrieve me"))
        found = get_task.execute(created.id)
        assert found.id == created.id
        assert found.title == "Retrieve me"

    def test_raises_for_unknown_id(self, get_task: GetTask):
        with pytest.raises(TaskNotFoundError):
            get_task.execute("00000000-0000-0000-0000-000000000099")


class TestListTasks:
    def test_empty_repo_returns_empty_list(self, list_tasks: ListTasks):
        assert list_tasks.execute() == []

    def test_returns_all_tasks(self, create_task: CreateTask, list_tasks: ListTasks):
        create_task.execute(CreateTaskInput(title="A"))
        create_task.execute(CreateTaskInput(title="B"))
        create_task.execute(CreateTaskInput(title="C"))
        assert len(list_tasks.execute()) == 3

    def test_titles_present(self, create_task: CreateTask, list_tasks: ListTasks):
        create_task.execute(CreateTaskInput(title="Alpha"))
        titles = {t.title for t in list_tasks.execute()}
        assert "Alpha" in titles


class TestDeleteTask:
    def test_deletes_existing_task(
        self,
        create_task: CreateTask,
        delete_task: DeleteTask,
        repo: InMemoryTaskRepository,
    ):
        out = create_task.execute(CreateTaskInput(title="Gone"))
        delete_task.execute(out.id)
        assert repo.count() == 0

    def test_raises_for_unknown_id(self, delete_task: DeleteTask):
        with pytest.raises(TaskNotFoundError):
            delete_task.execute("00000000-0000-0000-0000-000000000099")

    def test_deleted_task_not_retrievable(
        self, create_task: CreateTask, delete_task: DeleteTask, get_task: GetTask
    ):
        out = create_task.execute(CreateTaskInput(title="Delete me"))
        delete_task.execute(out.id)
        with pytest.raises(TaskNotFoundError):
            get_task.execute(out.id)


class TestUpdateTask:
    def test_updates_title(
        self, create_task: CreateTask, update_task: UpdateTask, get_task: GetTask
    ):
        out = create_task.execute(CreateTaskInput(title="Old title"))
        update_task.execute(out.id, UpdateTaskInput(title="New title"))
        assert get_task.execute(out.id).title == "New title"

    def test_updates_priority(
        self, create_task: CreateTask, update_task: UpdateTask, get_task: GetTask
    ):
        out = create_task.execute(CreateTaskInput(title="Task"))
        update_task.execute(out.id, UpdateTaskInput(priority=Priority.HIGH))
        assert get_task.execute(out.id).priority == Priority.HIGH

    def test_sets_due_date(
        self, create_task: CreateTask, update_task: UpdateTask, get_task: GetTask
    ):
        out = create_task.execute(CreateTaskInput(title="Task"))
        update_task.execute(out.id, UpdateTaskInput(due_date=date(2026, 6, 1)))
        assert get_task.execute(out.id).due_date == date(2026, 6, 1)

    def test_clears_due_date(
        self, create_task: CreateTask, update_task: UpdateTask, get_task: GetTask
    ):
        out = create_task.execute(CreateTaskInput(title="Task", due_date=date(2026, 6, 1)))
        update_task.execute(out.id, UpdateTaskInput(clear_due_date=True))
        assert get_task.execute(out.id).due_date is None

    def test_partial_update_leaves_other_fields_intact(
        self, create_task: CreateTask, update_task: UpdateTask, get_task: GetTask
    ):
        out = create_task.execute(CreateTaskInput(title="Original", priority=Priority.LOW))
        update_task.execute(out.id, UpdateTaskInput(title="Changed"))
        found = get_task.execute(out.id)
        assert found.title == "Changed"
        assert found.priority == Priority.LOW

    def test_raises_for_unknown_id(self, update_task: UpdateTask):
        with pytest.raises(TaskNotFoundError):
            update_task.execute("00000000-0000-0000-0000-000000000099", UpdateTaskInput(title="X"))


class TestCompleteTask:
    def test_completes_pending_task(
        self, create_task: CreateTask, complete_task: CompleteTask, get_task: GetTask
    ):
        out = create_task.execute(CreateTaskInput(title="Finish me"))
        complete_task.execute(out.id)
        assert get_task.execute(out.id).status == TaskStatus.COMPLETED

    def test_raises_for_unknown_id(self, complete_task: CompleteTask):
        with pytest.raises(TaskNotFoundError):
            complete_task.execute("00000000-0000-0000-0000-000000000099")


class TestUncompleteTask:
    def test_reverts_completed_task(
        self,
        create_task: CreateTask,
        complete_task: CompleteTask,
        uncomplete_task: UncompleteTask,
        get_task: GetTask,
    ):
        out = create_task.execute(CreateTaskInput(title="Done... or not"))
        complete_task.execute(out.id)
        uncomplete_task.execute(out.id)
        assert get_task.execute(out.id).status == TaskStatus.PENDING

    def test_raises_if_task_not_completed(
        self, create_task: CreateTask, uncomplete_task: UncompleteTask
    ):
        out = create_task.execute(CreateTaskInput(title="Pending"))
        with pytest.raises(ValueError):
            uncomplete_task.execute(out.id)


class TestArchiveTask:
    def test_archives_pending_task(
        self, create_task: CreateTask, archive_task: ArchiveTask, get_task: GetTask
    ):
        out = create_task.execute(CreateTaskInput(title="Archive me"))
        archive_task.execute(out.id)
        assert get_task.execute(out.id).status == TaskStatus.ARCHIVED

    def test_raises_for_unknown_id(self, archive_task: ArchiveTask):
        with pytest.raises(TaskNotFoundError):
            archive_task.execute("00000000-0000-0000-0000-000000000099")


class TestUnarchiveTask:
    def test_returns_archived_task_to_pending(
        self,
        create_task: CreateTask,
        archive_task: ArchiveTask,
        unarchive_task: UnarchiveTask,
        get_task: GetTask,
    ):
        out = create_task.execute(CreateTaskInput(title="Back from archive"))
        archive_task.execute(out.id)
        unarchive_task.execute(out.id)
        assert get_task.execute(out.id).status == TaskStatus.PENDING

    def test_raises_if_task_not_archived(
        self, create_task: CreateTask, unarchive_task: UnarchiveTask
    ):
        out = create_task.execute(CreateTaskInput(title="Not archived"))
        with pytest.raises(ValueError):
            unarchive_task.execute(out.id)


class TestInMemoryRepository:
    def test_save_then_get_returns_copy(self, repo: InMemoryTaskRepository):
        from kirokyu.adapters.in_memory.providers import FixedClock, SequentialIdProvider
        from kirokyu.application.use_cases.create_task import CreateTask

        uc = CreateTask(
            repository=repo,
            id_provider=SequentialIdProvider(),
            clock=FixedClock(),
        )
        out = uc.execute(CreateTaskInput(title="Isolation check"))

        from kirokyu.domain.value_objects import TaskId

        task = repo.get_by_id(TaskId(out.id))
        assert task is not None
        task.title = "MUTATED"

        stored = repo.get_by_id(TaskId(out.id))
        assert stored is not None
        assert stored.title == "Isolation check"

    def test_delete_is_idempotent(self, repo: InMemoryTaskRepository):
        from kirokyu.domain.value_objects import TaskId

        tid = TaskId.generate()
        repo.delete(tid)
        repo.delete(tid)
