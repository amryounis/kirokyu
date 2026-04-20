Adapters import from both the application layer (to implement ports)
and the domain layer (to work with domain objects like Task and TaskId).
Nothing in the domain or application layers imports from adapters.

This is what makes adapters swappable — the rest of the system has no
knowledge of which adapter is in use.

---

## Why the in-memory adapter exists permanently

The in-memory adapter (`adapters/in_memory/`) was built in Phase 1,
before any real persistence existed. Its purpose was to:

1. **Enable testing immediately** — use cases needed a TaskRepository
   to run against. Without the in-memory adapter, no tests could run
   until a database was built.

2. **Prove the architecture** — if the ports and use cases are correctly
   designed, the in-memory adapter and the SQLite adapter should be
   completely interchangeable. Phase 2 proved this claim — 149 tests
   pass with all three adapters without changing a single line of
   domain or application code.

The in-memory adapter is not a temporary scaffold that gets removed
when real persistence arrives. It stays permanently as the preferred
adapter for all unit and use-case tests, because:

- Tests should never depend on the filesystem if they don't have to
- In-memory is faster (no I/O)
- In-memory is simpler (no cleanup, no temp files)
- In-memory is isolated (each test gets a fresh empty instance)

The SQLite and JSON adapters are tested separately with their own
adapter-specific tests and the shared contract suite.

---

## Three adapters, one port

All three adapters implement the same four methods declared by
`TaskRepository`:

| Method | Behaviour |
|--------|-----------|
| `save(task)` | Insert if new, update if existing (upsert) |
| `get_by_id(task_id)` | Return Task or None |
| `list_all()` | Return all tasks |
| `delete(task_id)` | Remove permanently, silently if absent |

Swapping adapters is a one-line change at the composition root —
the place where the application is wired together.

---

## InMemoryTaskRepository

Stores tasks in a plain Python dict keyed by `TaskId.value`.

Stores and returns **deep copies** of tasks. This is important —
without deep copies, a caller that mutates a task object after saving
it would silently corrupt the stored state. The test
`test_save_then_get_returns_copy` in `test_use_cases.py` verifies this.

Has two extra helper methods not part of the port contract:
- `count()` — useful in tests to assert how many tasks are stored
- `clear()` — wipes all tasks for teardown scenarios

---

## SqliteTaskRepository

Backed by a SQLite database file. SQLite is part of Python's standard
library — no extra dependency needed.

Key design decisions:

**Lazy connection** — the connection is opened on first use, not at
construction time. This avoids opening a file until actually needed.

**`:memory:` support** — passing `":memory:"` as the path creates an
in-process SQLite database with no file on disk. Used in adapter tests
for speed and isolation.

**Context manager** — supports `with SqliteTaskRepository(...) as repo:`
for clean connection lifecycle management.

**Upsert** — `save()` uses `INSERT ... ON CONFLICT DO UPDATE` rather
than a separate SELECT then INSERT or UPDATE. One SQL statement handles
both cases.

**WAL mode** — `PRAGMA journal_mode=WAL` improves read performance.
Appropriate for a single-user local application.

**Schema versioning** — `schema.py` tracks the schema version via
`PRAGMA user_version`. Migrations are numbered functions applied
additively. Adding a column in a future phase means writing one new
`_migrate_to_v2()` function — nothing else changes.

**Type mapping:**
- Enums → their string values (`"pending"`, `"medium"`)
- Booleans → integers (0/1, SQLite has no boolean type)
- Dates/datetimes → ISO-8601 strings
- None → NULL

---

## JsonFileTaskRepository

Backed by a single JSON file on disk.

Wire format:
```json
{
  "version": 1,
  "tasks": {
    "<uuid>": { ...task fields... }
  }
}
```

Key design decisions:

**Atomic writes** — data is written to a temporary file in the same
directory, then renamed to the target path. On POSIX systems (Linux,
macOS) `os.rename` is atomic — a crash mid-write leaves either the
old file or the new file intact, never a corrupt partial write.

**Schema version guard** — on load, the version field is checked. A
mismatch raises immediately with a clear error rather than silently
loading corrupt data.

**`file_path=None` mode** — operates entirely in memory without
touching the filesystem. Used in contract tests to exercise the
serialisation logic without filesystem side-effects.

**In-memory cache** — once loaded, the store is kept in memory.
Reads after the first load are fast dict lookups with no I/O.

---

## Contract tests

`tests/adapters/contract.py` defines `RepositoryContractTests` — a
base class with 18 test methods, one per contract obligation.

Each adapter test class subclasses it and provides only a `repo`
fixture:

```python
class TestSqliteContract(RepositoryContractTests):
    @pytest.fixture()
    def repo(self):
        with SqliteTaskRepository(":memory:") as r:
            yield r
```

pytest discovers and runs all 18 inherited tests automatically. Adding
a fourth adapter in the future means writing one subclass with one
fixture — 18 contract tests come for free.

The contract tests cover: save/retrieve, upsert, list_all, delete
idempotency, and field-level round-trips for all non-trivial types
(enums, booleans, dates, Unicode, timestamps).
