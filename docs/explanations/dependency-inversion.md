# Dependency Inversion in Kirokyu

## The principle

Dependency Inversion is one of the SOLID principles. It states:

- High-level modules should not depend on low-level modules
- Both should depend on abstractions
- Abstractions should not depend on details

In plain language: the parts of your system that contain business logic
should not be coupled to the parts that deal with infrastructure
(databases, files, HTTP, clocks, random number generators).

## The problem it solves

Imagine `CreateTask` called `sqlite3.connect()` directly. You could not
test it without a real database file. You could not swap SQLite for
a JSON file without modifying the use case. The business logic would be
entangled with an infrastructure detail.

## How it is implemented in Kirokyu

### The repository port

`src/kirokyu/application/ports/task_repository.py` defines an abstract
class `TaskRepository` with four methods: `save`, `get_by_id`,
`list_all`, `delete`.

This is the abstraction. The use cases depend on it:

```python
class CreateTask:
    def __init__(self, repository: TaskRepository, ...):
        self._repository = repository
```

`CreateTask` does not know whether the repository is SQLite, JSON, or
in-memory. It knows only that whatever it receives satisfies the
`TaskRepository` contract.

### The concrete adapters

Three classes implement `TaskRepository`:

- `InMemoryTaskRepository` — lives in `adapters/in_memory/`
- `SqliteTaskRepository` — lives in `adapters/sqlite/`
- `JsonFileTaskRepository` — lives in `adapters/json_file/`

Each one satisfies the contract. None of them is known to the use cases.

### The providers ports

The same pattern applies to infrastructure concerns smaller than
persistence. `IdProvider` and `Clock` in
`src/kirokyu/application/ports/providers.py` are abstract ports.

`CreateTask` does not call `uuid.uuid4()` directly. It calls
`self._id_provider.next_id()`. In production that produces a random
UUID. In tests a `SequentialIdProvider` produces deterministic IDs
like `00000000-0000-0000-0000-000000000001`.

### The visible consequence

Run this from the project root:

```bash
grep -r "^from\|^import" src/kirokyu/domain/
grep -r "^from\|^import" src/kirokyu/application/
```

The domain imports nothing outside the standard library. The application
imports nothing outside the standard library and the domain. Neither
knows SQLite, JSON, uuid, or datetime infrastructure exists.

The dependency arrows all point inward — toward the domain. Never
outward toward infrastructure. That is dependency inversion made visible
in the import graph.

### The composition root

The one place where concrete classes are named and wired together is
`src/kirokyu/bootstrap.py`. It selects the adapter, constructs it, and
injects it into the use cases. Everything above bootstrap (CLI, API)
receives abstractions. Everything below bootstrap (adapters) implements
them.
