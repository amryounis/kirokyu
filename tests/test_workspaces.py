"""Tests for the workspace registry and models."""

from __future__ import annotations

from pathlib import Path

import pytest

from kirokyu.workspaces.models import Workspace
from kirokyu.workspaces.registry import WorkspaceRegistry


@pytest.fixture()
def registry(tmp_path: Path) -> WorkspaceRegistry:
    """A fresh registry backed by a temp directory."""
    return WorkspaceRegistry(tmp_path / "workspaces.json")


# ---------------------------------------------------------------------------
# Workspace model
# ---------------------------------------------------------------------------


def test_workspace_rejects_empty_name():
    from datetime import datetime

    with pytest.raises(ValueError, match="empty"):
        Workspace(name="", db_path="/tmp/x.db", created_at=datetime.now())


def test_workspace_rejects_invalid_characters():
    from datetime import datetime

    with pytest.raises(ValueError, match="only contain"):
        Workspace(name="my workspace", db_path="/tmp/x.db", created_at=datetime.now())


def test_workspace_accepts_valid_name():
    from datetime import datetime

    ws = Workspace(name="my-workspace", db_path="/tmp/x.db", created_at=datetime.now())
    assert ws.name == "my-workspace"


# ---------------------------------------------------------------------------
# Registry — create
# ---------------------------------------------------------------------------


def test_create_workspace(registry: WorkspaceRegistry):
    ws = registry.create("personal")
    assert ws.name == "personal"
    assert ws.db_path.endswith("personal.db")
    assert ws.last_opened_at is None


def test_create_duplicate_raises(registry: WorkspaceRegistry):
    registry.create("personal")
    with pytest.raises(ValueError, match="already exists"):
        registry.create("personal")


def test_create_persists_to_disk(registry: WorkspaceRegistry):
    registry.create("personal")
    registry2 = WorkspaceRegistry(registry._registry_path)
    assert registry2.exists("personal")


# ---------------------------------------------------------------------------
# Registry — list
# ---------------------------------------------------------------------------


def test_list_empty(registry: WorkspaceRegistry):
    assert registry.list_all() == []


def test_list_returns_all(registry: WorkspaceRegistry):
    registry.create("personal")
    registry.create("work")
    names = [ws.name for ws in registry.list_all()]
    assert "personal" in names
    assert "work" in names


def test_list_sorted_by_name(registry: WorkspaceRegistry):
    registry.create("work")
    registry.create("personal")
    names = [ws.name for ws in registry.list_all()]
    assert names == sorted(names)


# ---------------------------------------------------------------------------
# Registry — get
# ---------------------------------------------------------------------------


def test_get_existing(registry: WorkspaceRegistry):
    registry.create("personal")
    ws = registry.get("personal")
    assert ws is not None
    assert ws.name == "personal"


def test_get_missing_returns_none(registry: WorkspaceRegistry):
    assert registry.get("nonexistent") is None


# ---------------------------------------------------------------------------
# Registry — touch
# ---------------------------------------------------------------------------


def test_touch_updates_last_opened(registry: WorkspaceRegistry):
    registry.create("personal")
    registry.touch("personal")
    ws = registry.get("personal")
    assert ws is not None
    assert ws.last_opened_at is not None


def test_touch_missing_raises(registry: WorkspaceRegistry):
    with pytest.raises(ValueError, match="not found"):
        registry.touch("nonexistent")


# ---------------------------------------------------------------------------
# Registry — delete
# ---------------------------------------------------------------------------


def test_delete_removes_from_registry(registry: WorkspaceRegistry):
    registry.create("personal")
    registry.delete("personal")
    assert not registry.exists("personal")


def test_delete_missing_raises(registry: WorkspaceRegistry):
    with pytest.raises(ValueError, match="not found"):
        registry.delete("nonexistent")


def test_delete_does_not_remove_db_file(registry: WorkspaceRegistry, tmp_path: Path):
    ws = registry.create("personal")
    db = Path(ws.db_path)
    db.touch()
    registry.delete("personal")
    assert db.exists()
