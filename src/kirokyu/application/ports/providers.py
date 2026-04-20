"""Infrastructure ports for identity and time (Decision 16).

Separating these into ports makes use cases pure functions of their
inputs — deterministic ID generation and fixed timestamps can be
injected in tests without any mocking framework.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from kirokyu.domain.value_objects import TaskId


class IdProvider(ABC):
    """Port that generates a fresh, unique TaskId."""

    @abstractmethod
    def next_id(self) -> TaskId:
        """Return a new, unique TaskId."""
        ...


class Clock(ABC):
    """Port that returns the current datetime."""

    @abstractmethod
    def now(self) -> datetime:
        """Return the current datetime (timezone-naive UTC assumed)."""
        ...
