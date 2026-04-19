# Kirokyu

A task management system with a clean, pluggable architecture.

**Status:** Early development — Phase 0 (project scaffolding). Not yet functional.

---

## What this is

Kirokyu is a task and work management system built in Python. It is being developed incrementally, with emphasis on architectural clarity and engineering discipline rather than feature count. The domain is deliberately small so that the design of each layer can receive careful attention.

The project is intended to grow. What starts as a personal task tracker is structured so that it can extend toward project management, team workflows, or other directions without reworking its foundations.

## Architecture

Kirokyu follows the Hexagonal Architecture pattern (also known as Ports and Adapters). The domain core is independent of infrastructure concerns; persistence, delivery mechanisms, and user interfaces are swappable adapters plugged into well-defined ports.

For the full architectural rationale and design notes, see [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Project structure
kirokyu/
├── src/
│   └── kirokyu/                # Application package (domain + application layers)
├── tests/                      # Test suite
├── docs/                       # Project documents (plan, phase notes)
├── pyproject.toml              # Project metadata and tool configuration
├── .pre-commit-config.yaml     # Automated checks run on every commit
├── ARCHITECTURE.md             # Hexagonal Architecture notes
├── DECISIONS.md                # Decision log — the why behind choices
└── README.md                   # This file

## Getting started

Requires Python 3.12 or newer.

```bash
# Clone the repository
git clone <repository-url> kirokyu
cd kirokyu

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install the project with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Development workflow

```bash
# Run the full test suite
pytest

# Run linter and formatter (auto-fixes where possible)
ruff check --fix
ruff format

# Run type checker
mypy

# Run all pre-commit hooks against all files
pre-commit run --all-files
```

All checks are run automatically by pre-commit on every `git commit`.

## Roadmap

Development is organized into six phases, each ending at a showable state:

1. **Foundation** — project scaffolding and tooling *(in progress)*
2. **Hexagonal core** — domain entities, value objects, use cases, in-memory repository
3. **Persistence adapters** — SQLite and JSON adapters behind the same port
4. **Driving adapters** — CLI (Typer) and REST API (FastAPI)
5. **UI layer** — web interface via Streamlit
6. **Analytics layer** — read-side projections, productivity dashboards
7. **Production polish** — containerization, CI, documentation

See [`docs/project-plan.md`](docs/project-plan.md) for the full plan with reasoning.

## License

MIT. See `pyproject.toml` for the license declaration. A `LICENSE` file will be added when this project is published to GitHub.
