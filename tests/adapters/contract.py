"""Shared repository contract test suite.

Defines RepositoryContractTests — a base class that declares one test
method per contract obligation of TaskRepository.

Concrete adapter test modules subclass it and provide a repo fixture.
pytest collects and runs all inherited test methods automatically, so
every adapter is verified against the same assertions.
"""

from __future__ import annotations

from datetime import date, datetime

from kirokyu.application.ports.task_repository import TaskRepository
from kirokyu.domain.entities import Task
from kirokyu.domain.value_objects import DueDate, Priority, TaskId, TaskStatus

_T0 = datetime(2026, 4, 20, 9, 0, 0)
_T1 = datetime(2026, 4, 20, 10, 0, 0)


def _make_task(
    *,
    title: str = "Test task",
    uid: str = "00000000-0000-0000-0000-000000000001",
    priority: Priority = Priority.MEDIUM,
    description: str = "",
    due_date: DueDate | None = None,
    starred: bool = False,
    now: datetime = _T0,
) -> Task:
    return Task.create(
        id=TaskId(value=uid),
        title=title,
        priority=priority,
        description=description,
        due_date=due_date,
        starred=starred,
        now=now,
    )


class RepositoryContractTests:
    """Abstract contract test suite for TaskRepository implementations.

    Subclasses must provide a repo fixture returning a fresh empty
    TaskRepository instance for each test.
    """

    # ------------------------------------------------------------------
    # save / get_by_id
    # ------------------------------------------------------------------

    def test_save_and_retrieve_by_id(self, repo: TaskRepository):
        task = _make_task(title="Round-trip")
        repo.save(task)
        found = repo.get_by_id(task.id)
        assert found is not None
        assert found.id == task.id
        assert found.title == "Round-trip"

    def test_get_by_id_returns_none_for_missing(self, repo: TaskRepository):
        result = repo.get_by_id(TaskId("00000000-0000-0000-0000-000000000099"))
        assert result is None

    def test_save_is_upsert(self, repo: TaskRepository):
        """Saving the same id twice updates rather than duplicates."""
        task = _make_task(title="Original")
        repo.save(task)
        task.update_title("Updated", _T1)
        repo.save(task)
        found = repo.get_by_id(task.id)
        assert found is not None
        assert found.title == "Updated"
        assert len(repo.list_all()) == 1

    # ------------------------------------------------------------------
    # list_all
    # ------------------------------------------------------------------

    def test_list_all_empty(self, repo: TaskRepository):
        assert repo.list_all() == []

    def test_list_all_returns_all_saved(self, repo: TaskRepository):
        uid_base = "00000000-0000-0000-0000-{:012d}"
        for i in range(1, 4):
            repo.save(_make_task(title=f"Task {i}", uid=uid_base.format(i)))
        assert len(repo.list_all()) == 3

    # ------------------------------------------------------------------
    # delete
    # ------------------------------------------------------------------

    def test_delete_removes_task(self, repo: TaskRepository):
        task = _make_task()
        repo.save(task)
        repo.delete(task.id)
        assert repo.get_by_id(task.id) is None

    def test_delete_is_idempotent(self, repo: TaskRepository):
        tid = TaskId("00000000-0000-0000-0000-000000000042")
        repo.delete(tid)
        repo.delete(tid)

    def test_delete_does_not_affect_other_tasks(self, repo: TaskRepository):
        a = _make_task(title="Keep", uid="00000000-0000-0000-0000-000000000001")
        b = _make_task(title="Remove", uid="00000000-0000-0000-0000-000000000002")
        repo.save(a)
        repo.save(b)
        repo.delete(b.id)
        assert repo.get_by_id(a.id) is not None
        assert repo.get_by_id(b.id) is None

    # ------------------------------------------------------------------
    # Field round-trips
    # ------------------------------------------------------------------

    def test_priority_round_trip(self, repo: TaskRepository):
        uid_base = "00000000-0000-0000-0000-{:012d}"
        for i, priority in enumerate(Priority, 1):
            task = _make_task(priority=priority, uid=uid_base.format(i))
            repo.save(task)
            found = repo.get_by_id(task.id)
            assert found is not None
            assert found.priority == priority

    def test_status_round_trip(self, repo: TaskRepository):
        task = _make_task()
        repo.save(task)
        task.complete(_T1)
        repo.save(task)
        found = repo.get_by_id(task.id)
        assert found is not None
        assert found.status == TaskStatus.COMPLETED

        task2 = _make_task(uid="00000000-0000-0000-0000-000000000002")
        repo.save(task2)
        task2.archive(_T1)
        repo.save(task2)
        found2 = repo.get_by_id(task2.id)
        assert found2 is not None
        assert found2.status == TaskStatus.ARCHIVED

    def test_due_date_round_trip(self, repo: TaskRepository):
        dd = DueDate(value=date(2026, 12, 31))
        task = _make_task(due_date=dd)
        repo.save(task)
        found = repo.get_by_id(task.id)
        assert found is not None
        assert found.due_date is not None
        assert found.due_date.value == date(2026, 12, 31)

    def test_null_due_date_round_trip(self, repo: TaskRepository):
        task = _make_task(due_date=None)
        repo.save(task)
        found = repo.get_by_id(task.id)
        assert found is not None
        assert found.due_date is None

    def test_starred_true_round_trip(self, repo: TaskRepository):
        task = _make_task(starred=True)
        repo.save(task)
        found = repo.get_by_id(task.id)
        assert found is not None
        assert found.starred is True

    def test_starred_false_round_trip(self, repo: TaskRepository):
        task = _make_task(starred=False)
        repo.save(task)
        found = repo.get_by_id(task.id)
        assert found is not None
        assert found.starred is False

    def test_timestamps_preserved(self, repo: TaskRepository):
        task = _make_task(now=_T0)
        repo.save(task)
        found = repo.get_by_id(task.id)
        assert found is not None
        assert found.created_at == _T0
        assert found.updated_at == _T0

    def test_description_round_trip(self, repo: TaskRepository):
        task = _make_task(description="Some notes here.")
        repo.save(task)
        found = repo.get_by_id(task.id)
        assert found is not None
        assert found.description == "Some notes here."

    def test_unicode_title_round_trip(self, repo: TaskRepository):
        task = _make_task(title="مهمة مهمة 🎯")
        repo.save(task)
        found = repo.get_by_id(task.id)
        assert found is not None
        assert found.title == "مهمة مهمة 🎯"
