"""Adapter parity and adapter-specific tests for Phase 2.

Each adapter class subclasses RepositoryContractTests — pytest runs
the full shared contract suite against it automatically.

Adapter-specific tests live in their own classes below.
"""

from __future__ import annotations

import json
from collections.abc import Generator
from datetime import datetime
from pathlib import Path

import pytest

from kirokyu.adapters.in_memory.repository import InMemoryTaskRepository
from kirokyu.adapters.json_file.repository import JsonFileTaskRepository
from kirokyu.adapters.sqlite.repository import SqliteTaskRepository
from kirokyu.adapters.sqlite.schema import CURRENT_VERSION
from kirokyu.domain.entities import Task
from kirokyu.domain.value_objects import TaskId
from tests.adapters.contract import RepositoryContractTests

_T0 = datetime(2026, 4, 20, 9, 0, 0)
_T1 = datetime(2026, 4, 20, 10, 0, 0)


def _make_task(
    title: str = "Test",
    uid: str = "00000000-0000-0000-0000-000000000001",
    now: datetime = _T0,
) -> Task:
    return Task.create(id=TaskId(value=uid), title=title, now=now)


# ===========================================================================
# In-memory adapter — contract
# ===========================================================================


class TestInMemoryContract(RepositoryContractTests):
    @pytest.fixture()
    def repo(self) -> InMemoryTaskRepository:
        return InMemoryTaskRepository()


# ===========================================================================
# SQLite adapter — contract + specific tests
# ===========================================================================


class TestSqliteContract(RepositoryContractTests):
    @pytest.fixture()
    def repo(self) -> Generator[SqliteTaskRepository, None, None]:
        with SqliteTaskRepository(":memory:") as r:
            yield r


class TestSqliteSpecific:
    def test_schema_version_is_set(self):
        with SqliteTaskRepository(":memory:") as repo:
            version = repo._connection.execute("PRAGMA user_version").fetchone()[0]
            assert version == CURRENT_VERSION

    def test_tasks_table_exists(self):
        with SqliteTaskRepository(":memory:") as repo:
            tables = {
                row[0]
                for row in repo._connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            assert "tasks" in tables

    def test_file_persistence(self, tmp_path: Path):
        """Data written in one connection is readable in a fresh one."""
        db_file = tmp_path / "kirokyu.db"
        task = _make_task(title="Persisted across connections")

        with SqliteTaskRepository(db_file) as repo:
            repo.save(task)

        with SqliteTaskRepository(db_file) as repo2:
            found = repo2.get_by_id(task.id)
            assert found is not None
            assert found.title == "Persisted across connections"

    def test_upsert_does_not_change_created_at(self, tmp_path: Path):
        db_file = tmp_path / "kirokyu.db"
        task = _make_task()

        with SqliteTaskRepository(db_file) as repo:
            repo.save(task)
            task.update_title("Modified", _T1)
            repo.save(task)
            found = repo.get_by_id(task.id)
            assert found is not None
            assert found.created_at == _T0
            assert found.updated_at == _T1

    def test_count_helper(self):
        with SqliteTaskRepository(":memory:") as repo:
            assert repo.count() == 0
            repo.save(_make_task())
            assert repo.count() == 1

    def test_starred_stored_as_integer(self):
        with SqliteTaskRepository(":memory:") as repo:
            task = Task.create(
                id=TaskId("00000000-0000-0000-0000-000000000001"),
                title="Starred",
                starred=True,
                now=_T0,
            )
            repo.save(task)
            raw = repo._connection.execute(
                "SELECT starred FROM tasks WHERE id = ?",
                (task.id.value,),
            ).fetchone()
            assert raw[0] in (0, 1)
            assert raw[0] == 1

    def test_migrate_is_idempotent(self):
        import sqlite3

        from kirokyu.adapters.sqlite.schema import migrate

        conn = sqlite3.connect(":memory:")
        migrate(conn)
        migrate(conn)
        conn.close()


# ===========================================================================
# JSON file adapter — contract + specific tests
# ===========================================================================


class TestJsonFileContract(RepositoryContractTests):
    @pytest.fixture()
    def repo(self) -> JsonFileTaskRepository:
        return JsonFileTaskRepository(file_path=None)


class TestJsonFileSpecific:
    def test_file_is_created_on_first_write(self, tmp_path: Path):
        db_file = tmp_path / "data" / "tasks.json"
        assert not db_file.exists()
        repo = JsonFileTaskRepository(file_path=db_file)
        repo.save(_make_task())
        assert db_file.exists()

    def test_file_format_is_valid_json(self, tmp_path: Path):
        db_file = tmp_path / "tasks.json"
        repo = JsonFileTaskRepository(file_path=db_file)
        repo.save(_make_task(title="JSON round-trip"))

        with db_file.open() as fh:
            data = json.load(fh)

        assert data["version"] == 1
        assert isinstance(data["tasks"], dict)
        assert len(data["tasks"]) == 1

    def test_file_persistence_across_instances(self, tmp_path: Path):
        db_file = tmp_path / "tasks.json"
        task = _make_task(title="Cross-instance")
        JsonFileTaskRepository(file_path=db_file).save(task)

        repo2 = JsonFileTaskRepository(file_path=db_file)
        found = repo2.get_by_id(task.id)
        assert found is not None
        assert found.title == "Cross-instance"

    def test_delete_updates_file(self, tmp_path: Path):
        db_file = tmp_path / "tasks.json"
        task = _make_task()
        repo = JsonFileTaskRepository(file_path=db_file)
        repo.save(task)
        repo.delete(task.id)

        repo2 = JsonFileTaskRepository(file_path=db_file)
        assert repo2.get_by_id(task.id) is None
        assert repo2.count() == 0

    def test_unicode_survives_file_round_trip(self, tmp_path: Path):
        db_file = tmp_path / "tasks.json"
        task = _make_task(title="مهمة 🎯")
        repo = JsonFileTaskRepository(file_path=db_file)
        repo.save(task)

        repo2 = JsonFileTaskRepository(file_path=db_file)
        found = repo2.get_by_id(task.id)
        assert found is not None
        assert found.title == "مهمة 🎯"

    def test_version_mismatch_raises(self, tmp_path: Path):
        db_file = tmp_path / "tasks.json"
        db_file.write_text(json.dumps({"version": 99, "tasks": {}}), encoding="utf-8")
        repo = JsonFileTaskRepository(file_path=db_file)
        with pytest.raises(ValueError, match="Unsupported"):
            repo.list_all()

    def test_memory_mode_does_not_touch_filesystem(self, tmp_path: Path):
        repo = JsonFileTaskRepository(file_path=None)
        repo.save(_make_task())
        repo.save(_make_task(uid="00000000-0000-0000-0000-000000000002", title="B"))
        repo.delete(TaskId("00000000-0000-0000-0000-000000000002"))
        assert list(tmp_path.iterdir()) == []
        assert repo.count() == 1

    def test_due_date_null_in_json(self, tmp_path: Path):
        db_file = tmp_path / "tasks.json"
        repo = JsonFileTaskRepository(file_path=db_file)
        repo.save(_make_task())

        with db_file.open() as fh:
            data = json.load(fh)

        tasks = list(data["tasks"].values())
        assert tasks[0]["due_date"] is None
