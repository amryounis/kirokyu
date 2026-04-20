"""Concrete IdProvider and Clock adapters (Decision 16).

Production adapters:
    UuidIdProvider  — generates random UUID v4 TaskIds
    SystemClock     — returns datetime.utcnow()

Test adapters:
    SequentialIdProvider  — deterministic ids for tests
    FixedClock            — always returns a single fixed datetime
"""

from __future__ import annotations

import uuid
from datetime import datetime

from kirokyu.application.ports.providers import Clock, IdProvider
from kirokyu.domain.value_objects import TaskId


class UuidIdProvider(IdProvider):
    """Generates random UUID v4 TaskIds."""

    def next_id(self) -> TaskId:
        return TaskId(value=str(uuid.uuid4()))


class SystemClock(Clock):
    """Returns the current UTC datetime (timezone-naive)."""

    def now(self) -> datetime:
        return datetime.utcnow()


class SequentialIdProvider(IdProvider):
    """Generates deterministic TaskIds for use in tests.

    Example IDs produced:
        00000000-0000-0000-0000-000000000001
        00000000-0000-0000-0000-000000000002
        ...
    """

    def __init__(self, start: int = 1) -> None:
        self._counter = start

    def next_id(self) -> TaskId:
        hex_suffix = f"{self._counter:012x}"
        uid = f"00000000-0000-0000-0000-{hex_suffix}"
        self._counter += 1
        return TaskId(value=uid)

    def reset(self, start: int = 1) -> None:
        """Reset the counter between tests."""
        self._counter = start


class FixedClock(Clock):
    """Always returns the same datetime — makes time deterministic in tests."""

    def __init__(self, fixed: datetime | None = None) -> None:
        self._fixed = fixed or datetime(2026, 1, 1, 12, 0, 0)

    def now(self) -> datetime:
        return self._fixed
