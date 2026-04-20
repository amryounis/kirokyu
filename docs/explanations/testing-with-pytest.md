# Testing with pytest — Explanation

**Files:** `tests/`
**Tool:** pytest 8.x

---

## What is pytest?

pytest is the standard Python test runner. It finds test files and
functions automatically, runs them, and reports results. It requires
no boilerplate — a test is just a function that starts with `test_`.

---

## How pytest finds tests

pytest looks in the `tests/` directory (configured in `pyproject.toml`
via `testpaths = ["tests"]`). It collects:

- Files matching `test_*.py`
- Classes matching `Test*`
- Functions matching `test_*`

These patterns are also configured in `pyproject.toml`:

```toml
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

---

## Test classes

Tests are grouped into classes for organisation. A test class in pytest
is a plain Python class — no inheritance required, no special setup.

```python
class TestTaskCreate:
    def test_creates_pending_task(self):
        task = make_task()
        assert task.status == TaskStatus.PENDING
```

The class is just a namespace. It groups related tests so the output
is easier to read and the file is easier to navigate.

---

## Assertions

pytest uses plain Python `assert` statements. No special assertion
methods needed:

```python
assert task.status == TaskStatus.PENDING   # equality
assert task.is_pending                     # truthiness
assert not task.is_completed               # falsy
assert len(results) == 3                   # length
assert "Alpha" in titles                   # membership
```

When an assertion fails, pytest shows the values of both sides — this
is why `--showlocals` is configured, to see all local variables at the
point of failure.

---

## `pytest.raises`

Used to assert that a piece of code raises a specific exception:

```python
with pytest.raises(ValueError):
    make_task(title="")
```

The `match` argument checks the exception message:

```python
with pytest.raises(ValueError, match="empty"):
    make_task(title="")
```

If the exception is not raised, the test fails. If a different
exception is raised, it propagates and the test errors.

---

## Fixtures

Fixtures are reusable pieces of setup, defined in `conftest.py` and
injected into tests by name.

```python
# conftest.py
@pytest.fixture()
def repo() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()

# test file
def test_something(self, repo: InMemoryTaskRepository):
    # repo is a fresh InMemoryTaskRepository, ready to use
    ...
```

pytest sees that the test function has a parameter called `repo`, looks
for a fixture with that name, calls it, and passes the result in. The
test never constructs the object itself.

**Why fixtures?**
- Each test gets a fresh instance — no shared state between tests
- Complex wiring (use case + repository + clock) is done once in
  `conftest.py`, not repeated in every test
- Changing an adapter (e.g. swapping InMemoryTaskRepository for
  SqliteTaskRepository) means changing one fixture, not every test

**Fixture scope**
All fixtures in this project are function-scoped (the default) — a new
instance is created for each test function. This guarantees isolation:
what one test does cannot affect another.

**Fixture composition**
Fixtures can depend on other fixtures:

```python
@pytest.fixture()
def create_task(
    repo: InMemoryTaskRepository,
    id_provider: SequentialIdProvider,
    clock: FixedClock,
) -> CreateTask:
    return CreateTask(repository=repo, id_provider=id_provider, clock=clock)
```

pytest resolves the dependency graph automatically. When a test requests
`create_task`, pytest first creates `repo`, `id_provider`, and `clock`,
then passes them into the `create_task` fixture.

---

## `conftest.py`

A special pytest file. Fixtures defined here are automatically available
to all test files in the same directory and below — no import needed.

---

## No mocking

This test suite uses no mocking framework. Instead of replacing real
objects with fake ones at runtime, we inject test-friendly
implementations directly:

- `SequentialIdProvider` instead of `UuidIdProvider` — predictable IDs
- `FixedClock` instead of `SystemClock` — predictable timestamps
- `InMemoryTaskRepository` instead of a database — fast, no side-effects

This is possible because of the ports — every external dependency is
behind an interface, so swapping implementations is natural, not a hack.

---

## pytest configuration in `pyproject.toml`

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--showlocals",
]
```

- `minversion` — fails loudly if an older pytest is installed
- `-ra` — shows a summary of all non-passing tests at the end
- `--strict-markers` — typos in marker names fail loudly
- `--strict-config` — typos in config fail loudly
- `--showlocals` — shows local variable values on test failure

---

## Running tests

```bash
# Run everything
pytest

# Run one file
pytest tests/test_value_objects.py

# Run one class
pytest tests/test_task_entity.py::TestTaskComplete

# Run one test
pytest tests/test_task_entity.py::TestTaskComplete::test_pending_task_can_be_completed

# Verbose output (show each test name)
pytest -v
```
