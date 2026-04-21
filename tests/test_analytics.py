"""Tests for the analytics read-side queries."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from kirokyu.analytics.queries import AnalyticsQueries


def _make_db(tmp_path: Path) -> Path:
    """Create a minimal tasks database for testing."""
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.execute("""
        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            priority TEXT NOT NULL DEFAULT 'medium',
            status TEXT NOT NULL DEFAULT 'pending',
            due_date TEXT,
            starred INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    return db


def _insert(conn: sqlite3.Connection, **kwargs: object) -> None:
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
        (
            kwargs.get("id", "test-id"),
            kwargs.get("title", "Test"),
            kwargs.get("description", ""),
            kwargs.get("priority", "medium"),
            kwargs.get("status", "pending"),
            kwargs.get("due_date"),
            kwargs.get("starred", 0),
            kwargs.get("created_at", now),
            kwargs.get("updated_at", now),
        ),
    )
    conn.commit()


@pytest.fixture()
def db(tmp_path: Path) -> Path:
    return _make_db(tmp_path)


@pytest.fixture()
def queries(db: Path) -> AnalyticsQueries:
    return AnalyticsQueries(db)


# ---------------------------------------------------------------------------
# Completion rate
# ---------------------------------------------------------------------------


def test_completion_rate_empty(queries: AnalyticsQueries):
    result = queries.completion_rate()
    assert result.total == 0
    assert result.completed == 0
    assert result.rate == 0.0


def test_completion_rate_all_pending(queries: AnalyticsQueries, db: Path):
    with sqlite3.connect(str(db)) as conn:
        _insert(conn, id="1", status="pending")
        _insert(conn, id="2", status="pending")
    result = queries.completion_rate()
    assert result.total == 2
    assert result.completed == 0
    assert result.rate == 0.0


def test_completion_rate_mixed(queries: AnalyticsQueries, db: Path):
    with sqlite3.connect(str(db)) as conn:
        _insert(conn, id="1", status="completed")
        _insert(conn, id="2", status="completed")
        _insert(conn, id="3", status="pending")
        _insert(conn, id="4", status="pending")
    result = queries.completion_rate()
    assert result.total == 4
    assert result.completed == 2
    assert result.rate == 50.0


def test_completion_rate_with_since_filter(queries: AnalyticsQueries, db: Path):
    old_date = (datetime.now() - timedelta(days=60)).isoformat()
    recent_date = datetime.now().isoformat()
    with sqlite3.connect(str(db)) as conn:
        _insert(conn, id="1", status="completed", created_at=old_date, updated_at=old_date)
        _insert(conn, id="2", status="completed", created_at=recent_date, updated_at=recent_date)
    since = date.today() - timedelta(days=30)
    result = queries.completion_rate(since=since)
    assert result.total == 1
    assert result.completed == 1


# ---------------------------------------------------------------------------
# Tasks by priority
# ---------------------------------------------------------------------------


def test_tasks_by_priority_empty(queries: AnalyticsQueries):
    assert queries.tasks_by_priority() == []


def test_tasks_by_priority_counts(queries: AnalyticsQueries, db: Path):
    with sqlite3.connect(str(db)) as conn:
        _insert(conn, id="1", priority="high")
        _insert(conn, id="2", priority="high")
        _insert(conn, id="3", priority="medium")
    result = {p.priority: p.count for p in queries.tasks_by_priority()}
    assert result["high"] == 2
    assert result["medium"] == 1


# ---------------------------------------------------------------------------
# Completion trend
# ---------------------------------------------------------------------------


def test_completion_trend_empty(queries: AnalyticsQueries):
    assert queries.completion_trend() == []


def test_completion_trend_counts(queries: AnalyticsQueries, db: Path):
    today = datetime.now().isoformat()
    with sqlite3.connect(str(db)) as conn:
        _insert(conn, id="1", status="completed", updated_at=today)
        _insert(conn, id="2", status="completed", updated_at=today)
        _insert(conn, id="3", status="pending", updated_at=today)
    result = queries.completion_trend(days=30)
    assert len(result) == 1
    assert result[0].count == 2


# ---------------------------------------------------------------------------
# Overdue summary
# ---------------------------------------------------------------------------


def test_overdue_summary_empty(queries: AnalyticsQueries):
    assert queries.overdue_summary() == []


def test_overdue_summary_no_overdue(queries: AnalyticsQueries, db: Path):
    future = (date.today() + timedelta(days=5)).isoformat()
    with sqlite3.connect(str(db)) as conn:
        _insert(conn, id="1", status="pending", due_date=future)
    assert queries.overdue_summary() == []


def test_overdue_summary_buckets(queries: AnalyticsQueries, db: Path):
    two_days_ago = (date.today() - timedelta(days=2)).isoformat()
    five_days_ago = (date.today() - timedelta(days=5)).isoformat()
    ten_days_ago = (date.today() - timedelta(days=10)).isoformat()
    with sqlite3.connect(str(db)) as conn:
        _insert(conn, id="1", status="pending", due_date=two_days_ago)
        _insert(conn, id="2", status="pending", due_date=five_days_ago)
        _insert(conn, id="3", status="pending", due_date=ten_days_ago)
    result = {b.label: b.count for b in queries.overdue_summary()}
    assert result.get("1-3 days", 0) == 1
    assert result.get("4-7 days", 0) == 1
    assert result.get("1+ weeks", 0) == 1


# ---------------------------------------------------------------------------
# Status summary
# ---------------------------------------------------------------------------


def test_status_summary_empty(queries: AnalyticsQueries):
    assert queries.status_summary() == {}


def test_status_summary_counts(queries: AnalyticsQueries, db: Path):
    with sqlite3.connect(str(db)) as conn:
        _insert(conn, id="1", status="pending")
        _insert(conn, id="2", status="completed")
        _insert(conn, id="3", status="archived")
    result = queries.status_summary()
    assert result["pending"] == 1
    assert result["completed"] == 1
    assert result["archived"] == 1
