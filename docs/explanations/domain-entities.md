# Domain Entities — Explanation

**File:** `src/kirokyu/domain/entities.py`
**Layer:** Domain (innermost — no external dependencies)

---

## What is an entity?

An entity is a domain object whose identity is tracked explicitly — it
has an ID, and that ID is what makes it unique. Two tasks with the same
title are still two different tasks. This is different from a value
object (like `TaskId` or `DueDate`), where identity is defined entirely
by the data.

`Task` is the only entity in Phase 1. It is the central aggregate root
of the domain.

---

## Why `@dataclass` without `frozen=True`?

Value objects use `@dataclass(frozen=True)` — immutable by design.
`Task` uses plain `@dataclass` — mutable by design. A task changes
state over its lifetime (completed, archived, title updated). Freezing
it would make every mutation require creating a new object, which adds
complexity without benefit here.

---

## The factory: `Task.create()`

Tasks are not constructed directly via `Task(...)`. They are created
through the `Task.create()` factory classmethod. Reasons:

- Enforces invariants at construction time (title validation)
- Sets `status` to `PENDING` — a new task is always pending, the
  caller cannot accidentally create a completed task
- Sets `created_at` and `updated_at` to the same `now` value
- Takes `now` as a parameter (injected from the Clock port) rather
  than calling `datetime.now()` internally — keeps it deterministic

The `*` in the signature forces all arguments to be keyword-only:
`Task.create(id=..., title=..., now=...)`. This prevents mistakes from
argument ordering.

---

## Lifecycle transitions

Four explicit state transitions, each taking `now: datetime`:

| Method | From | To | Guards |
|--------|------|----|--------|
| `complete()` | PENDING | COMPLETED | Raises if ARCHIVED; idempotent if already COMPLETED |
| `uncomplete()` | COMPLETED | PENDING | Raises if not COMPLETED |
| `archive()` | PENDING or COMPLETED | ARCHIVED | Raises if already ARCHIVED |
| `unarchive()` | ARCHIVED | PENDING | Raises if not ARCHIVED |

Each transition advances `updated_at`. `created_at` is never touched
after construction.

The guard conditions enforce domain rules — invalid transitions raise
`ValueError` with a clear message. The domain layer never silently
ignores a bad operation.

---

## Mutations

Six mutation methods, each taking `now: datetime`:

- `update_title()` — validates and strips whitespace before storing
- `update_description()` — no validation; empty string is valid
- `update_priority()` — replaces the priority enum value
- `update_due_date()` — sets or clears the due date
- `toggle_starred()` — flips the boolean flag

Every mutation advances `updated_at`. This is the pattern: any method
that changes state takes `now` and updates the timestamp.

---

## Query properties

Three `@property` methods — `is_pending`, `is_completed`, `is_archived`
— provide readable boolean checks without exposing the status enum
directly to every caller.

```python
if task.is_pending:   # clean
if task.status == TaskStatus.PENDING:  # also works but more verbose
```

---

## `_validate_title`

A `@staticmethod` — it belongs to the class conceptually (it's a domain
rule about titles) but doesn't need access to `self` or `cls`. Prefixed
with `_` to signal it's internal. Called by both `create()` and
`update_title()` to avoid duplicating the validation logic.

---

## `__repr__`

Custom string representation for debugging. Without it, Python would
print `Task(id=TaskId(value='...'), title='...', status=<TaskStatus.PENDING: 'pending'>, ...)` — verbose and hard to read. The custom version
prints `Task(id=..., title='...', status=pending, priority=medium)`.
