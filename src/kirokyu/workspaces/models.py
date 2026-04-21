"""Workspace domain model.

A workspace is an isolated data silo — its own SQLite file, its own tasks.
It is an infrastructure concept, not a task-domain concept. The task domain
is unaware of workspaces; the bootstrap uses the workspace to resolve the
correct database path before constructing use cases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Workspace:
    """A named, isolated task database."""

    name: str
    db_path: str
    created_at: datetime
    last_opened_at: datetime | None = field(default=None)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Workspace name cannot be empty.")
        if not self.name.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Workspace name may only contain letters, digits, hyphens, and underscores."
            )
