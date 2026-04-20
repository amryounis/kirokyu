# Domain Value Objects — Explanation

**File:** `src/kirokyu/domain/value_objects.py`
**Layer:** Domain (innermost — no external dependencies)

---

## Why value objects?

A value object is an immutable object whose identity is defined entirely
by its data, not by a reference. Two `TaskId` instances with the same
UUID string are equal. Two `DueDate` instances with the same date are
equal. There is no meaningful distinction between them.

This is different from an *entity* (like `Task`), where identity is
tracked explicitly — two tasks with the same title are still two
different tasks.

Value objects are implemented as `@dataclass(frozen=True)` — Python
generates `__init__`, `__repr__`, and `__eq__` automatically, and
`frozen=True` makes them immutable after construction.

---

## `from __future__ import annotations`

Makes all type annotations lazy (evaluated as strings, not immediately).
Prevents self-reference errors inside a class definition. A one-line
habit applied to every file.

---

## Imports

```python
import uuid
from dataclasses import dataclass
from datetime import date
from enum import Enum
```

All standard library. No third-party imports anywhere in the domain
layer — this is enforced by Decision 15. If you ever see a third-party
import in `domain/`, something has gone wrong architecturally.

---

## `TaskId`

Wraps a UUID string. Validates format on construction via `__post_init__`
— the object can never exist in an invalid state.

Stores a `str`, not Python's `uuid.UUID` type — strings are easier to
serialize, compare, and print.

Two construction paths:
- `TaskId.generate()` — fresh random ID (used by `IdProvider` adapter)
- `TaskId(value="...")` — reconstruct from storage (used by repositories)

`__str__` returns the plain UUID string so f-strings and logs are clean.

---

## `Priority`

An `Enum` with three members: `LOW`, `MEDIUM`, `HIGH`.

String values (`"low"`, `"medium"`, `"high"`) are what gets stored in
the database or JSON file. Recover from string with `Priority("low")`.

Why Enum over plain strings?
- Typos are caught by the type checker, not at runtime
- Adding a new member forces you to handle it everywhere
- Reads like English: `task.priority == Priority.HIGH`

---

## `TaskStatus`

An `Enum` with three members: `PENDING`, `COMPLETED`, `ARCHIVED`.

Decision 17: no `DELETED` status. A deleted task does not exist — it is
removed from the repository entirely. Representing deletion as a status
would mean deleted tasks still occupy memory, still appear in queries
unless filtered, and still require handling in every piece of code that
touches status. Removal is cleaner.

---

## `DueDate`

Wraps `datetime.date` (calendar date only, no time component).

Why wrap `date` at all?
- Attaches domain behaviour (`is_overdue`) that a plain `date` doesn't have
- Makes the type expressive: `task.due_date: DueDate | None` signals a
  domain concept, not just any date

`is_overdue(relative_to)` takes the reference date as a parameter rather
than calling `date.today()` internally. This keeps the method
deterministic and testable — the caller controls what "now" means.
Same principle as the `Clock` port (Decision 16).

`__str__` returns ISO-8601 format (`"2026-04-20"`) for clean output.
