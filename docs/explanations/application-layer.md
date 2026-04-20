# Application Layer — Explanation

**Files:** `src/kirokyu/application/`
**Layer:** Application (middle — depends on domain, not on adapters)

---

## What is the application layer?

The application layer contains the use cases — the actual things the
system can do. It sits between the domain (what the rules are) and the
adapters (how data is stored and delivered).

It has three responsibilities:
1. Declare what it needs from the outside world (ports)
2. Accept and validate incoming data (DTOs)
3. Orchestrate the domain to fulfil a request (use cases)

---

## Ports

A port is an abstract interface — a contract declared by the application
layer that says "I need something that can do X" without specifying how.

Two kinds of ports in Phase 1:

**`TaskRepository`** (`ports/task_repository.py`)
Declares four operations: `save`, `get_by_id`, `list_all`, `delete`.
The application layer calls these; adapters implement them. The
in-memory, SQLite, and JSON adapters are all implementations of this
one interface. Swapping storage means swapping the adapter — no use
case changes.

**`IdProvider` and `Clock`** (`ports/providers.py`)
Two small ports from Decision 16. Rather than calling `uuid.uuid4()`
and `datetime.now()` directly inside use cases (which would make them
non-deterministic), these are declared as ports. Tests inject
predictable implementations (`SequentialIdProvider`, `FixedClock`)
without any mocking framework.

Ports are defined as ABCs (`Abstract Base Classes`). A class that
inherits from an ABC and does not implement all `@abstractmethod`
methods cannot be instantiated — Python enforces the contract.

---

## DTOs — Data Transfer Objects

DTOs are Pydantic models that carry data across the use-case boundary.

**Why a boundary at all?**
The domain works with rich types: `TaskId`, `Priority`, `DueDate`.
The outside world (CLI, API, tests) works with flat data: strings,
plain dates, plain enums. DTOs are the translation layer between the
two. They live in the application layer because that boundary is where
translation belongs.

**Why Pydantic?**
Pydantic validates data at construction time and raises a clear
`ValidationError` if something is wrong. This is exactly what a
boundary validator should do — catch bad input before it reaches the
domain. Decision 15 restricts Pydantic to this layer only; the domain
layer uses stdlib frozen dataclasses.

**Three DTOs in Phase 1:**

`CreateTaskInput` — carries data *into* the CreateTask use case.
Fields: `title` (required, non-blank), `description`, `priority`,
`due_date`, `starred`. Pydantic validates types and the blank-title
rule before the use case sees the data.

`UpdateTaskInput` — carries partial updates into UpdateTask. All fields
are optional — only fields that are provided get applied. The
`clear_due_date` boolean flag handles the case where you want to
explicitly remove a due date (setting `due_date=None` is ambiguous —
it could mean "not provided" or "clear it").

`TaskOutput` — carries data *out of* every use case back to the caller.
A flat, safe projection of a Task: all IDs as strings, dates as ISO
strings, no domain objects exposed. Any caller — CLI, API, test — can
consume this without knowing anything about the domain layer.

---

## Use cases

Each use case is a class with:
- Dependencies injected via `__init__` (repository, clock, id provider)
- A single `execute()` method that does the work

This structure makes dependencies explicit and testable. You can
construct a use case with any combination of adapters:

```python
# In production
CreateTask(
    repository=SqliteTaskRepository("kirokyu.db"),
    id_provider=UuidIdProvider(),
    clock=SystemClock(),
)

# In tests
CreateTask(
    repository=InMemoryTaskRepository(),
    id_provider=SequentialIdProvider(),
    clock=FixedClock(),
)
```

Same use case, different adapters, no code change.

**Use cases in Phase 1:**

| File | Use cases |
|------|-----------|
| `create_task.py` | `CreateTask` |
| `query_tasks.py` | `GetTask`, `ListTasks`, `DeleteTask` |
| `mutate_tasks.py` | `UpdateTask`, `CompleteTask`, `UncompleteTask`, `ArchiveTask`, `UnarchiveTask` |

**The `_to_output()` helper**
Each file has a private `_to_output(task: Task) -> TaskOutput` function
that converts a domain `Task` into a `TaskOutput` DTO. It is repeated
in each file deliberately — shared helpers create coupling between files
that should be independent. The duplication is small and the isolation
is worth it.

**The `_get_or_raise()` helper** (in `mutate_tasks.py`)
Fetches a task by id and raises `TaskNotFoundError` if not found.
Extracted because every mutation use case needs the same pattern:
fetch, check, operate, save.

---

## Dependency direction

The application layer imports from the domain layer.
The application layer never imports from the adapters layer.
The adapters layer imports from both.

This is the dependency rule of hexagonal architecture made concrete.
If you ever see `from kirokyu.adapters` inside `kirokyu.application`,
something has gone wrong.
