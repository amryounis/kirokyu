"""Tests for domain value objects."""

from __future__ import annotations

from datetime import date

import pytest

from kirokyu.domain.value_objects import DueDate, Priority, TaskId, TaskStatus


class TestTaskId:
    def test_accepts_valid_uuid(self):
        tid = TaskId(value="12345678-1234-5678-1234-567812345678")
        assert str(tid) == "12345678-1234-5678-1234-567812345678"

    def test_rejects_non_uuid(self):
        with pytest.raises(ValueError, match="valid UUID"):
            TaskId(value="not-a-uuid")

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError):
            TaskId(value="")

    def test_generate_returns_valid_task_id(self):
        tid = TaskId.generate()
        assert TaskId(value=tid.value) == tid

    def test_equality_by_value(self):
        v = "12345678-1234-5678-1234-567812345678"
        assert TaskId(value=v) == TaskId(value=v)

    def test_inequality(self):
        a = TaskId.generate()
        b = TaskId.generate()
        assert a != b

    def test_frozen(self):
        tid = TaskId.generate()
        with pytest.raises((AttributeError, TypeError)):
            tid.value = "something-else"  # type: ignore[misc]


class TestPriority:
    def test_members_exist(self):
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"

    def test_enum_by_value(self):
        assert Priority("medium") is Priority.MEDIUM


class TestTaskStatus:
    def test_members_exist(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.ARCHIVED.value == "archived"

    def test_no_deleted_status(self):
        values = {s.value for s in TaskStatus}
        assert "deleted" not in values


class TestDueDate:
    def test_is_overdue_when_before_reference(self):
        dd = DueDate(value=date(2026, 1, 1))
        assert dd.is_overdue(relative_to=date(2026, 1, 2))

    def test_not_overdue_when_equal_to_reference(self):
        dd = DueDate(value=date(2026, 4, 20))
        assert not dd.is_overdue(relative_to=date(2026, 4, 20))

    def test_not_overdue_when_after_reference(self):
        dd = DueDate(value=date(2026, 12, 31))
        assert not dd.is_overdue(relative_to=date(2026, 4, 20))

    def test_str_returns_iso_format(self):
        dd = DueDate(value=date(2026, 4, 20))
        assert str(dd) == "2026-04-20"

    def test_frozen(self):
        dd = DueDate(value=date(2026, 4, 20))
        with pytest.raises((AttributeError, TypeError)):
            dd.value = date(2026, 1, 1)  # type: ignore[misc]
