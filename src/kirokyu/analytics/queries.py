"""Analytics read-side queries for Kirokyu.

These queries run directly against the SQLite database using raw SQL
aggregations. They are intentionally separate from the transactional
use cases — this is the read side of a light CQRS split.

The domain layer and use cases are unaware of this module.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class CompletionRateSummary:
    total: int
    completed: int
    rate: float


@dataclass
class PriorityCount:
    priority: str
    count: int


@dataclass
class DailyCount:
    day: str
    count: int


@dataclass
class OverdueBucket:
    label: str
    count: int


class AnalyticsQueries:
    """Read-side queries against a Kirokyu SQLite workspace database."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Completion rate
    # ------------------------------------------------------------------

    def completion_rate(self, since: date | None = None) -> CompletionRateSummary:
        """Return total tasks and completion rate, optionally filtered by date."""
        with self._conn() as conn:
            if since:
                rows = conn.execute(
                    "SELECT status, COUNT(*) as n FROM tasks WHERE created_at >= ? GROUP BY status",
                    (since.isoformat(),),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT status, COUNT(*) as n FROM tasks GROUP BY status"
                ).fetchall()

        counts = {r["status"]: r["n"] for r in rows}
        total = sum(counts.values())
        completed = counts.get("completed", 0)
        rate = round(completed / total * 100, 1) if total > 0 else 0.0
        return CompletionRateSummary(total=total, completed=completed, rate=rate)

    # ------------------------------------------------------------------
    # Tasks by priority
    # ------------------------------------------------------------------

    def tasks_by_priority(self) -> list[PriorityCount]:
        """Return task counts grouped by priority."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT priority, COUNT(*) as n FROM tasks GROUP BY priority ORDER BY priority"
            ).fetchall()
        return [PriorityCount(priority=r["priority"], count=r["n"]) for r in rows]

    # ------------------------------------------------------------------
    # Completion trend
    # ------------------------------------------------------------------

    def completion_trend(self, days: int = 30) -> list[DailyCount]:
        """Return daily completed task counts for the last N days."""
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT DATE(updated_at) as day, COUNT(*) as n
                FROM tasks
                WHERE status = 'completed'
                  AND updated_at >= DATE('now', ?)
                GROUP BY day
                ORDER BY day ASC
                """,
                (f"-{days} days",),
            ).fetchall()
        return [DailyCount(day=r["day"], count=r["n"]) for r in rows]

    # ------------------------------------------------------------------
    # Overdue summary
    # ------------------------------------------------------------------

    def overdue_summary(self) -> list[OverdueBucket]:
        """Return overdue pending tasks grouped into age buckets."""
        today = date.today().isoformat()
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT
                    CASE
                        WHEN julianday(?) - julianday(due_date) BETWEEN 1 AND 3
                            THEN '1-3 days'
                        WHEN julianday(?) - julianday(due_date) BETWEEN 4 AND 7
                            THEN '4-7 days'
                        ELSE '1+ weeks'
                    END as bucket,
                    COUNT(*) as n
                FROM tasks
                WHERE status = 'pending'
                  AND due_date IS NOT NULL
                  AND due_date < ?
                GROUP BY bucket
                ORDER BY MIN(julianday(?) - julianday(due_date))
                """,
                (today, today, today, today),
            ).fetchall()
        return [OverdueBucket(label=r["bucket"], count=r["n"]) for r in rows]

    # ------------------------------------------------------------------
    # Status summary
    # ------------------------------------------------------------------

    def status_summary(self) -> dict[str, int]:
        """Return task counts by status."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) as n FROM tasks GROUP BY status"
            ).fetchall()
        return {r["status"]: r["n"] for r in rows}
