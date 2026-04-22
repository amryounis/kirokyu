"""Workspace registry — reads and writes ~/.kirokyu/workspaces.json.

The registry is the single source of truth for all known workspaces.
It tracks workspace names, their db paths, and metadata (created_at,
last_opened_at). The actual task data lives in the individual SQLite
files — the registry only holds the index.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from kirokyu.workspaces.models import Workspace

DEFAULT_KIROKYU_DIR = Path.home() / ".kirokyu"
REGISTRY_FILE = DEFAULT_KIROKYU_DIR / "workspaces.json"
WORKSPACES_DIR = DEFAULT_KIROKYU_DIR / "workspaces"


class WorkspaceRegistry:
    """Manages the workspace registry file."""

    def __init__(self, registry_path: Path = REGISTRY_FILE) -> None:
        self._registry_path = registry_path
        self._workspaces_dir = registry_path.parent / "workspaces"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self, name: str) -> Workspace:
        """Create a new workspace and add it to the registry.

        Raises:
            ValueError: If a workspace with this name already exists.
        """
        workspaces = self._load()
        if name in workspaces:
            raise ValueError(f"Workspace {name!r} already exists.")

        self._workspaces_dir.mkdir(parents=True, exist_ok=True)
        db_path = str(self._workspaces_dir / f"{name}.db")
        now = datetime.now()

        workspace = Workspace(
            name=name,
            db_path=db_path,
            created_at=now,
            last_opened_at=None,
        )
        workspaces[name] = _to_dict(workspace)
        self._save(workspaces)
        return workspace

    def list_all(self) -> list[Workspace]:
        """Return all registered workspaces, most recently used first."""
        workspaces = self._load()
        return sorted(
            [_to_workspace(w) for w in workspaces.values()],
            key=lambda w: w.last_opened_at or w.created_at,
            reverse=True,
        )

    def get(self, name: str) -> Workspace | None:
        """Return the workspace with the given name, or None."""
        workspaces = self._load()
        raw = workspaces.get(name)
        return _to_workspace(raw) if raw else None

    def touch(self, name: str) -> None:
        """Update last_opened_at for the given workspace."""
        workspaces = self._load()
        if name not in workspaces:
            raise ValueError(f"Workspace {name!r} not found.")
        workspaces[name]["last_opened_at"] = datetime.now().isoformat()
        self._save(workspaces)

    def delete(self, name: str) -> None:
        """Remove a workspace from the registry.

        Does not delete the SQLite file — that is the caller's
        responsibility to avoid accidental data loss.
        """
        workspaces = self._load()
        if name not in workspaces:
            raise ValueError(f"Workspace {name!r} not found.")
        del workspaces[name]
        self._save(workspaces)

    def exists(self, name: str) -> bool:
        """Return True if a workspace with this name is registered."""
        return name in self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> dict[str, dict]:  # type: ignore[type-arg]
        if not self._registry_path.exists():
            return {}
        with self._registry_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)  # type: ignore[no-any-return]

    def _save(self, workspaces: dict[str, dict]) -> None:  # type: ignore[type-arg]
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        with self._registry_path.open("w", encoding="utf-8") as fh:
            json.dump(workspaces, fh, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


def _to_dict(workspace: Workspace) -> dict:  # type: ignore[type-arg]
    return {
        "name": workspace.name,
        "db_path": workspace.db_path,
        "created_at": workspace.created_at.isoformat(),
        "last_opened_at": (
            workspace.last_opened_at.isoformat() if workspace.last_opened_at else None
        ),
    }


def _to_workspace(raw: dict) -> Workspace:  # type: ignore[type-arg]
    return Workspace(
        name=raw["name"],
        db_path=raw["db_path"],
        created_at=datetime.fromisoformat(raw["created_at"]),
        last_opened_at=(
            datetime.fromisoformat(raw["last_opened_at"]) if raw.get("last_opened_at") else None
        ),
    )
