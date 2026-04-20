"""Tests for the Task entity — lifecycle transitions and invariant enforcement."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from kirokyu.domain.entities import Task
from kirokyu.domain.value_objects import DueDate, Priority, TaskId, TaskStatus

T0 = datetime(2026, 4, 20, 9, 0, 0)
T1 = datetime(2026, 4, 20, 10, 0, 0)
SAMPLE_ID = TaskId(value="00000000-0000-0000-0000-000000000001")


def make_task(**kwargs) -> Task:
    defaults = dict(id=SAMPLE_ID, title="Buy milk", now=T0)
    return Task.create(**{**defaults, **kwargs})


class TestTaskCreate:
    def test_creates_pending_task(self):
        task = make_task()
        assert task.status == TaskStatus.PENDING

    def test_strips_title_whitespace(self):
        task = make_task(title="  Buy milk  ")
        assert task.title == "Buy milk"

    def test_rejects_empty_title(self):
        with pytest.raises(ValueError, match="empty"):
            make_task(title="")

    def test_rejects_whitespace_only_title(self):
        with pytest.raises(ValueError, match="empty"):
            make_task(title="   ")

    def test_default_priority_is_medium(self):
        task = make_task()
        assert task.priority == Priority.MEDIUM

    def test_created_at_and_updated_at_equal_on_creation(self):
        task = make_task(now=T0)
        assert task.created_at == T0
        assert task.updated_at == T0

    def test_description_defaults_to_empty(self):
        task = make_task()
        assert task.description == ""

    def test_starred_defaults_to_false(self):
        task = make_task()
        assert task.starred is False

    def test_due_date_stored(self):
        dd = DueDate(value=date(2026, 5, 1))
        task = make_task(due_date=dd)
        assert task.due_date == dd


class TestTaskComplete:
    def test_pending_task_can_be_completed(self):
        task = make_task()
        task.complete(T1)
        assert task.status == TaskStatus.COMPLETED
        assert task.updated_at == T1

    def test_completing_is_idempotent(self):
        task = make_task()
        task.complete(T1)
        task.complete(T1)
        assert task.status == TaskStatus.COMPLETED

    def test_archived_task_cannot_be_completed(self):
        task = make_task()
        task.archive(T1)
        with pytest.raises(ValueError, match="archived"):
            task.complete(T1)


class TestTaskUncomplete:
    def test_completed_task_reverts_to_pending(self):
        task = make_task()
        task.complete(T0)
        task.uncomplete(T1)
        assert task.status == TaskStatus.PENDING
        assert task.updated_at == T1

    def test_cannot_uncomplete_pending_task(self):
        task = make_task()
        with pytest.raises(ValueError):
            task.uncomplete(T1)

    def test_cannot_uncomplete_archived_task(self):
        task = make_task()
        task.archive(T0)
        with pytest.raises(ValueError):
            task.uncomplete(T1)


class TestTaskArchive:
    def test_pending_task_can_be_archived(self):
        task = make_task()
        task.archive(T1)
        assert task.status == TaskStatus.ARCHIVED
        assert task.updated_at == T1

    def test_completed_task_can_be_archived(self):
        task = make_task()
        task.complete(T0)
        task.archive(T1)
        assert task.status == TaskStatus.ARCHIVED

    def test_already_archived_raises(self):
        task = make_task()
        task.archive(T0)
        with pytest.raises(ValueError, match="already archived"):
            task.archive(T1)


class TestTaskUnarchive:
    def test_archived_task_returns_to_pending(self):
        task = make_task()
        task.archive(T0)
        task.unarchive(T1)
        assert task.status == TaskStatus.PENDING
        assert task.updated_at == T1

    def test_cannot_unarchive_pending_task(self):
        task = make_task()
        with pytest.raises(ValueError):
            task.unarchive(T1)


class TestTaskMutations:
    def test_update_title(self):
        task = make_task()
        task.update_title("New title", T1)
        assert task.title == "New title"
        assert task.updated_at == T1

    def test_update_title_strips_whitespace(self):
        task = make_task()
        task.update_title("  padded  ", T1)
        assert task.title == "padded"

    def test_update_title_rejects_blank(self):
        task = make_task()
        with pytest.raises(ValueError):
            task.update_title("   ", T1)

    def test_update_description(self):
        task = make_task()
        task.update_description("some notes", T1)
        assert task.description == "some notes"

    def test_update_priority(self):
        task = make_task()
        task.update_priority(Priority.HIGH, T1)
        assert task.priority == Priority.HIGH

    def test_update_due_date(self):
        task = make_task()
        dd = DueDate(value=date(2026, 6, 1))
        task.update_due_date(dd, T1)
        assert task.due_date == dd

    def test_clear_due_date(self):
        task = make_task(due_date=DueDate(value=date(2026, 6, 1)))
        task.update_due_date(None, T1)
        assert task.due_date is None

    def test_toggle_starred_on(self):
        task = make_task()
        task.toggle_starred(T1)
        assert task.starred is True

    def test_toggle_starred_off(self):
        task = make_task(starred=True)
        task.toggle_starred(T1)
        assert task.starred is False


class TestTaskProperties:
    def test_is_pending(self):
        task = make_task()
        assert task.is_pending
        assert not task.is_completed
        assert not task.is_archived

    def test_is_completed(self):
        task = make_task()
        task.complete(T0)
        assert task.is_completed
        assert not task.is_pending

    def test_is_archived(self):
        task = make_task()
        task.archive(T0)
        assert task.is_archived
        assert not task.is_pending
