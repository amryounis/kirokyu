# Kirokyu

A personal task management system built in Python with a clean, pluggable architecture.

**Status:** Phases 0–5 complete. Fully functional.

---

## What this is

Kirokyu is a local-first task manager. It helps one person organize, track, and complete their work across isolated workspaces. Each workspace is an independent data silo with its own SQLite database.

The project is deliberately built around **Hexagonal Architecture** (Ports and Adapters). The domain core is independent of all infrastructure — persistence, delivery mechanisms, and interfaces are swappable adapters. This means the same business logic is reachable through three completely different interfaces today, with more planned.

---

## Interfaces

### Web UI
```bash
streamlit run src/kirokyu/adapters/ui/app.py
```
Browser-based interface at `http://localhost:8501`. Includes task management and an analytics dashboard.

### CLI
```bash
kirokyu --help
kirokyu --workspace personal task create "Buy groceries"
kirokyu --workspace personal task list
```
Environment variable shortcut:
```bash
export KIROKYU_WORKSPACE=personal
kirokyu task list
kirokyu task create "Call the bank" --priority high
```

### REST API
```bash
uvicorn kirokyu.adapters.api.app:app --reload
```
Interactive documentation at `http://localhost:8000/docs`.

---

## Workspaces

Kirokyu organizes tasks into isolated workspaces. Each workspace has its own SQLite database file under `~/.kirokyu/workspaces/`.

```bash
kirokyu workspace create personal
kirokyu workspace create work
kirokyu workspace list
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Driving Adapters               │
│   Streamlit UI │ Typer CLI │ FastAPI REST   │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│            Application Layer               │
│   Use Cases │ DTOs │ Ports (interfaces)    │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│              Domain Layer                  │
│   Task entity │ Value objects │ Exceptions │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│            Driven Adapters                 │
│   SQLite │ JSON file │ In-memory           │
└─────────────────────────────────────────────┘
```

The domain and application layers have zero infrastructure imports. The adapter selection is made once, at the bootstrap layer, and injected into the use cases.

For the full architectural rationale see [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`DECISIONS.md`](DECISIONS.md).

---

## Getting started

Requires Python 3.12 or newer.

```bash
git clone <repository-url> kirokyu
cd kirokyu

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
pre-commit install
```

---

## Development

```bash
# Run the full test suite (197 tests)
pytest

# Linter and formatter
ruff check --fix
ruff format

# Type checker
mypy

# All pre-commit hooks
pre-commit run --all-files
```

All checks run automatically on every `git commit`.

---

## Project structure

```
kirokyu/
├── src/kirokyu/
│   ├── domain/          # Entities, value objects, exceptions
│   ├── application/     # Use cases, DTOs, ports
│   ├── adapters/
│   │   ├── cli/         # Typer CLI
│   │   ├── api/         # FastAPI REST API
│   │   ├── ui/          # Streamlit web UI
│   │   ├── sqlite/      # SQLite repository adapter
│   │   ├── json_file/   # JSON file repository adapter
│   │   └── in_memory/   # In-memory adapter (tests)
│   ├── analytics/       # Read-side query layer
│   ├── workspaces/      # Workspace registry
│   └── bootstrap.py     # Composition root
├── tests/               # 197 tests
├── docs/                # Product definition, architecture, decisions
├── DECISIONS.md         # Decision log — the why behind every choice
└── ARCHITECTURE.md      # Architecture overview
```

---

## Adapter selection

The storage adapter is selected via environment variable:

```bash
KIROKYU_ADAPTER=sqlite   # default — SQLite database file
KIROKYU_ADAPTER=json     # JSON file
KIROKYU_ADAPTER=memory   # in-memory (no persistence)
```

---

## License

MIT. See `pyproject.toml`.
