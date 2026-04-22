# Decision Log

This document records the substantive decisions that shaped Kirokyu. Each entry follows a Context / Decision / Consequences structure, loosely based on Michael Nygard's ADR format but consolidated into a single file for this project's scale.

Decisions are numbered sequentially in roughly the order they were made. Earlier numbers represent foundational choices; later numbers build on them.

When a decision is revisited or reversed, the original entry is preserved and the new decision added with a reference back.

---

## 1. Development environment: Windows + WSL2 + Ubuntu 24.04

**Context.** The development host is a Windows 10 laptop. Python development on pure Windows is workable but poorly matched to the Linux-centric tooling, deployment targets, and library ecosystems most Python work assumes. Dual-booting introduces friction; a full VM has overhead; native Windows Python has enough small differences from Linux Python to cause occasional confusion.

**Decision.** Use WSL2 (Windows Subsystem for Linux) with Ubuntu 24.04 LTS pinned explicitly (not the unversioned `Ubuntu` alias). Ubuntu 24.04 ships Python 3.12.3 as the system Python, matching the project's target Python version without needing deadsnakes PPA or pyenv. VS Code runs on Windows and connects to WSL via the Remote-WSL extension, providing a Linux execution environment with Windows desktop integration.

**Consequences.** Gets real Linux filesystem, tooling, and behavior without VM overhead. Project files must live under `/home/<user>/` rather than `/mnt/c/...` — cross-filesystem access is ~10-20x slower and causes git weirdness. Pinning to `Ubuntu-24.04` keeps the setup reproducible; the unversioned `Ubuntu` alias will roll forward to 26.04 LTS when it releases, which could introduce unexpected Python version changes. Windows 10 mainstream support ended October 2025; ESU runs through October 2026, so a Windows 11 migration plan will be needed before then.

---

## 2. Python version: 3.12, pinned via `requires-python`

**Context.** Python has multiple actively-supported versions. 3.11 is mature but aging; 3.13 is recent but less widely supported by dependencies. 3.12 is the current sweet spot — stable, well-supported by FastAPI, Pydantic v2, SQLAlchemy 2.x, and every library this project is likely to use.

**Decision.** Target Python 3.12. Declare via `requires-python = ">=3.12"` in `pyproject.toml`. Reinforce via `target-version = "py312"` in ruff and `python_version = "3.12"` in mypy. Ubuntu 24.04's system Python satisfies this without additional installation.

**Consequences.** Users (and future deployments) need Python 3.12 or newer. Pip refuses to install on older versions with a clear error. Code can use 3.12-specific syntax (generic types with `[T]` syntax, PEP 695 type parameters if desired later). When Python 3.13 or 3.14 matures, we can bump the floor; for now, no reason to exclude 3.12 users.

---

## 3. Project name: Kirokyu

**Context.** The project needed a name that (a) is short and easy to type, (b) doesn't lock the project into "to-do app" identity, (c) doesn't lock the project into a specific architecture, and (d) is globally readable without carrying regional market associations. Generic names like `todo` compete with hundreds of similar GitHub repos and signal "first project." Architecture-stamped names like `todo-hex` front-load implementation detail over product identity. Arabic-rooted names carry regional-market-operator associations unhelpful for international positioning.

**Decision.** Kirokyu — a coined name inspired by the Japanese word *kiroku* (記録), meaning "record." Not a Japanese word itself; the final syllable is modified to produce a distinctive handle. Six letters, pronounceable as "kee-roh-KYOO," no existing product collisions in the task management space.

**Consequences.** The name doesn't semantically commit to any domain or architecture — the project can grow from personal task tracker to team collaboration platform to project management tool without the name becoming awkward. Japanese-origin naming carries neutral-to-positive associations internationally (precision, craft), unlike Arabic-origin naming which in practice signals regional SME operators. The project narrative can honestly describe the name as "coined, inspired by the Japanese word for 'record,'" which is a respectable origin story without overclaiming dictionary meaning.

---

## 4. Python packaging structure: `src/` layout with hatchling backend

**Context.** Python projects can be laid out in two conventions: *flat layout* (package directory directly under project root) or *src layout* (package directory under a `src/` wrapper). They look nearly identical, but the src layout forces packages to be installed before they're importable — which forces `pyproject.toml` to be correct. Additionally, multiple build backends exist: setuptools (historical default), hatchling (modern PyPA recommendation), poetry-core (coupled to Poetry), flit-core (lightweight), pdm-backend (coupled to PDM).

**Decision.** Use the `src/` layout with the importable package at `src/kirokyu/`. Use `hatchling` as the build backend via `[build-system] requires = ["hatchling"]`. Declare the package location explicitly in `pyproject.toml` via `[tool.hatch.build.targets.wheel] packages = ["src/kirokyu"]`.

**Consequences.** Running Python from the project root won't find the package unless it's installed (even in editable mode via `pip install -e .`). This catches missing dependency declarations immediately — tests can't pass by coincidentally finding packages on the filesystem. Hatchling requires the explicit package location because it can't auto-discover under `src/`. This one-line configuration is a common first-time-installing-a-src-layout gotcha; documenting it here prevents re-encountering the confusion.

---

## 5. Dependency management: venv + pip (not uv, Poetry, or conda)

**Context.** Python has several competing dependency management tools. `venv + pip` is the stdlib baseline — universal, familiar, slow. `uv` (Astral, 2024) is a Rust-based modern replacement that's 10-100x faster and offers lockfiles by default. `Poetry` is an established alternative with opinionated workflow. `conda` targets data science with binary package support. Each has real merits.

**Decision.** Use venv + pip for this project. Install the project in editable mode with dev dependencies via `pip install -e ".[dev]"`.

**Consequences.** This is a learning project with emphasis on understanding fundamentals. Adding uv or Poetry as a tool-to-learn alongside Python, pyproject.toml, hexagonal architecture, git discipline, and CI tooling would exceed reasonable simultaneous-novelty limits. venv + pip is what every Python tutorial assumes, what every CI system supports natively, and what a new developer encountering this project will already understand. The project's `pyproject.toml` is tool-agnostic — migrating to uv later is `rm -rf .venv && uv sync`, effectively costless. The main thing given up is install speed and built-in lockfiles; both are tolerable for a solo learning project.

---

## 6. Linter and formatter: Ruff (Flake8 and Black extensions disabled)

**Context.** Python's linting and formatting ecosystem historically required multiple tools: Flake8 (linter), Black (formatter), isort (import sorter), plus plugins. Each tool has its own configuration, its own invocation, and occasional conflicts with others. Ruff (Astral) consolidates all of them into one fast Rust-based tool. The VS Code environment had the Microsoft Flake8 and Black Formatter extensions installed, which would fight with Ruff if both ran.

**Decision.** Use Ruff exclusively for linting and formatting. Configure via `[tool.ruff]`, `[tool.ruff.lint]`, and `[tool.ruff.format]` in `pyproject.toml`. Enable rule families E, W, F, I, B, UP, N, SIM, RUF. Line length: 100. Quote style: double. Disable Flake8 and Black Formatter VS Code extensions (not uninstall — disable, recoverable).

**Consequences.** Single tool replaces three-plus. Much faster than the tools it replaces. The rule selection excludes overly-noisy families (pydocstyle, pylint, security) that would dominate a learning project. Line length 100 is a modern-default choice, comfortable on wide screens without sprawling. Disabled extensions are recorded here so that if a future machine setup forgets to disable them, the conflict source is traceable.

---

## 7. Type checker: mypy (not Astral ty), strict for source / relaxed for tests

**Context.** Python has two type checkers in active use for this project's choice: mypy (established, 2012, industry standard) and ty (Astral, pre-1.0 as of early 2026). Additionally, strictness levels vary from "barely checks" to "every function must be annotated." Tests often use patterns (dummy objects, mocks) that make strict typing verbose.

**Decision.** Use mypy. Enable `strict = true` globally, which turns on roughly a dozen sub-flags enforcing full annotations and no implicit `Any`. Override for the `tests.*` module namespace: `disallow_untyped_defs = false`, `disallow_incomplete_defs = false`, but keep `check_untyped_defs = true` (so test code with type errors is still caught, even if annotations aren't required).

**Consequences.** Strict mypy on source forces architectural discipline — ports and adapters must satisfy each other's type contracts, or mypy refuses. Test code stays readable; writing `def test_create_task_returns_task(task_repo: InMemoryTaskRepository) -> None:` for every test would add clutter without catching bugs. The `check_untyped_defs = true` override preserves safety in tests: unannotated functions still have their bodies analyzed. Mypy over ty is an interview-relevant choice — mypy is what 90%+ of Python shops use, and for a portfolio project, "I used the industry standard" is a stronger signal than "I experimented with pre-1.0 tooling."

---

## 8. Test runner: pytest, with strict markers and strict config

**Context.** Python has several test runners: `unittest` (stdlib, awkward), `nose2` (legacy), `pytest` (de facto standard). For configuration, pytest accepts silent typos in config and markers by default, which hides bugs (e.g., a typo'd marker decorator silently does nothing).

**Decision.** Use pytest. Pin `minversion = "8.0"`. Require `--strict-markers` and `--strict-config`. Show locals on test failure via `--showlocals`. Show summary of non-passing tests via `-ra`.

**Consequences.** Pytest is universal Python testing practice. Strict markers mean typo'd decorator names fail loudly instead of silently ignoring. `--showlocals` is enormously useful in debugging failed tests — you see exactly what state the test was in when the assertion failed, without adding print statements. The `minversion` guard prevents confusing errors if an old pytest is accidentally installed.

---

## 9. Pre-commit hooks: comprehensive scope (ruff + mypy + pytest + hygiene)

**Context.** Quality checks like linting and type-checking are only useful if they run. Running them manually is voluntary — in practice, people forget. Pre-commit (the framework) can run checks automatically before each git commit, rejecting commits that fail. Scope choices range from "lightweight" (hygiene checks only) to "comprehensive" (full test suite on every commit). Lightweight is fast; comprehensive catches everything but can slow commits.

**Decision.** Comprehensive pre-commit scope. Configure `.pre-commit-config.yaml` to run: generic file hygiene hooks (trailing whitespace, end-of-file newlines, yaml/toml validity, large-file check, merge conflict markers, line endings), ruff linter with `--fix`, ruff formatter, mypy on `src/` only, and pytest via a `local` hook. Install via `pre-commit install` so hooks run on every `git commit`.

**Consequences.** Commits take a few seconds longer (ruff is fast, mypy is moderate, pytest on a small domain is quick). In exchange, broken code cannot enter history — no "fix typo" or "lint errors" cleanup commits cluttering git log. The `files: ^src/` scoping for mypy ensures it analyzes the whole source tree coherently rather than file-by-file (which breaks mypy's cross-file analysis). Pytest as a `local` hook uses the venv's pytest rather than a pre-commit-managed one, which simplifies configuration and matches how it runs manually.

---

## 10. Version control: git from day 1, local-only until GitHub migration

**Context.** Starting git at the beginning of a project produces cleaner history than retrofitting it later. However, pushing to GitHub introduces public visibility, contributor friction, and URL commitments that are premature for a project still defining its identity. Phase 0 and early Phase 1 can proceed entirely locally.

**Decision.** Run `git init` immediately as the first repo action. Use the empty-first-commit pattern (a commit with no files, labeled "Initial commit"). Use `main` as the default branch name (configured globally via `init.defaultBranch main`). Do not publish to GitHub until Phase 6 (production polish), or until there's a concrete reason to.

**Consequences.** Full git history is captured from day 1. Migration to GitHub is a single `git remote add origin` and `git push`; no history loss or reconstruction. The empty first commit gives a clean root to rebase from without needing `git rebase --root`. Using `main` matches GitHub's default and industry convention since ~2020. Local-only means no risk of accidentally exposing incomplete work, wrong credentials, or personal details during exploration phases.

---

## 11. License: MIT (file deferred until GitHub migration)

**Context.** Open-source licensing determines what others can legally do with the code. Common choices: MIT (permissive, short), Apache 2.0 (permissive, includes explicit patent grant, longer), GPL (copyleft, forces derivatives open), proprietary/unlicensed (no permissions granted). For a portfolio project intended to be visible on GitHub, an open license is essential — otherwise visitors can read but not legally fork, study, or learn from the code. A possible future business pivot is a consideration, but past commits under MIT stay MIT forever; future commits can be relicensed.

**Decision.** MIT license. Declare in `pyproject.toml` via `license = { text = "MIT" }`. Include `"License :: OSI Approved :: MIT License"` in classifiers. Defer creating an actual `LICENSE` file until GitHub migration — GitHub's repo landing page specifically shows the LICENSE file, making its presence more visible there.

**Consequences.** MIT is the dominant choice for new Python projects (~70% of greenfield repos). Visitors registered it as "normal, permissive, portfolio-standard" with no friction. Anyone can fork, study, modify, or reuse the code with only the requirement to preserve the copyright notice. If this project later becomes commercial, historical MIT commits don't obligate anything — the commercial product can be proprietary. The deferred LICENSE file is a minor debt: `pyproject.toml` is technically sufficient for packaging tools, but a stand-alone LICENSE file is the community convention. Will be created during GitHub migration (Phase 6).

---

## 12. Project goals and priority order

**Context.** Kirokyu started as a pure learning vehicle. Over time, with a change in work situation (career transition, freelancing pursuit, family-venture thinking), the goal mix shifted. Clarifying the actual priority order prevents the project from optimizing for the wrong thing.

**Decision.** Four goals, in priority order: (1) commercial pivot-readiness — the architecture must support swapping the domain for something with business weight; (2) training and skill acquisition — deliberate practice of hexagonal architecture, Python craft, and the broader toolset; (3) personal daily use — Kirokyu should be genuinely usable as a task tracker by the author; (4) interview and portfolio evidence — a positive but minor goal, not a driver of decisions.

**Consequences.** Architectural discipline takes precedence over speed. Domain portability matters more than domain richness — the task domain is a placeholder that teaches the pattern; the skeleton is what survives a pivot. Features are evaluated against "would I actually use this" rather than "would this impress a reviewer." Timeline is loose — quality over calendar. The project will not be rushed to produce a portfolio artifact on a hiring timeline.

---

## 13. Working style: collaborative and adaptive, not directive

**Context.** Early sessions revealed a mismatch between working styles. Claude defaulted to over-specifying requirements upfront — exhaustive pre-flight questions, ranked priorities, calibration matrices — before allowing work to begin. This drained energy and created friction inconsistent with the author's twenty-plus years of delivery experience, where requirements evolve, ambiguity is the norm, and over-specifying upfront actively harms the work.

**Decision.** Work collaboratively and adaptively. Start with working assumptions rather than locked decisions. Write code first, reflect after. Raise questions one at a time when something is genuinely load-bearing. Write DECISIONS.md entries when decisions are actually made, not before. Accept that some things will be revisited as reality pushes back — that is not failure, it is how real projects work.

**Consequences.** The project moves faster and feels less like a requirements workshop. Some decisions will be made implicitly and recorded later. DECISIONS.md stays honest — it captures what was actually decided, not what was speculatively pre-decided. If something feels wrong when it's built, it gets changed without ceremony.

---

## 14. Internal package layout: layered (domain / application / adapters)

**Context.** Python hexagonal projects can be structured in two common ways: layered (top-level subpackages by architectural concern: `domain/`, `application/`, `adapters/`) or feature-sliced (top-level subpackages by domain concept: `tasks/`, each containing its own layers). Layered is more textbook and makes the hexagon boundaries loud; feature-sliced scales better for large, multi-domain systems.

**Decision.** Use the layered layout inside `src/kirokyu/`: `domain/` for entities and value objects, `application/` for use cases, ports, and DTOs, `adapters/` for concrete implementations. Ports (interface definitions) live inside `application/` because the application layer is what declares what it needs — adapters plug in from the outside.

**Consequences.** The architectural boundaries are immediately visible from the directory structure. A reviewer scanning the repo sees "domain depends on nothing, application depends on domain, adapters depend on both" without reading a line of code. Feature-sliced would scale better if the domain grew to dozens of concepts, but Kirokyu's domain is deliberately small — the layered layout is appropriate and more pedagogically clear for this project's purpose.

---

## 15. Value object implementation: frozen dataclasses for domain, Pydantic for DTOs

**Context.** Domain value objects (TaskId, Priority, DueDate) could be implemented as either frozen dataclasses (stdlib) or Pydantic models (third-party). Pydantic-everywhere is common in real-world Python codebases for consistency; frozen dataclasses are more architecturally pure but require manual validation.

**Decision.** Use `@dataclass(frozen=True)` for domain value objects. Use Pydantic `BaseModel` exclusively for DTOs at the use-case boundary (input/output models). The domain layer imports nothing from Pydantic — it depends only on the Python standard library.

**Consequences.** `grep -r "^import\|^from" src/kirokyu/domain/` shows only stdlib imports — a visible signal of architectural discipline. Domain value objects carry identity semantics and immutability without the runtime validation overhead of Pydantic. DTOs do validation at the boundary, which is their job. The distinction between "inert domain value" and "boundary validator" is made concrete in the code. Migrating domain objects to Pydantic later, if needed, is mechanical.

---

## 16. Domain identity and time: IdProvider and Clock ports

**Context.** Use cases that create entities need to generate IDs and timestamps. The naive approach is to call `uuid.uuid4()` and `datetime.now()` directly inside use cases. This couples the use cases to real-world time and random ID generation, making them non-deterministic and harder to test (tests can't control what IDs or timestamps get produced).

**Decision.** Introduce two small ports: `IdProvider` (returns a new `TaskId`) and `Clock` (returns the current datetime). Both are defined as abstract interfaces in `application/ports/`. The in-memory adapter provides simple implementations (uuid4, datetime.now). Tests inject predictable implementations (sequential IDs, fixed timestamps) without mocking.

**Consequences.** Use cases remain pure functions of their inputs — same inputs always produce same outputs when the same providers are injected. Tests are deterministic and readable. The ports are small (one method each) — the ceremony cost is low. This is exactly the kind of detail that distinguishes a candidate who understands the pattern from one who has read about it.

---

## 17. Task status model: TaskStatus enum with three states

**Context.** Tasks need a status. The simplest approach is a boolean `is_completed`. A richer approach uses an enum, which is extensible without a breaking change if new states are needed later.

**Decision.** Use a `TaskStatus` enum with three members: `PENDING`, `COMPLETED`, `ARCHIVED`. Deleted tasks are handled by permanent removal from the repository rather than a `DELETED` status — a deleted task does not exist, so it should not be represented. Un-completion (toggling a task back to `PENDING`) is supported. Archiving is reversible (archived → pending). Deletion is permanent.

**Consequences.** The three-state model covers the full lifecycle established in the product definition without over-engineering. Using an enum (rather than a boolean) means adding `IN_PROGRESS` or `CANCELLED` later is additive — no existing code breaks, no database migration for the boolean column. The decision to handle deletion as removal (not a status) keeps the repository contract clean: a repository query never returns deleted tasks because deleted tasks are not in the repository.

---

---

## 18. CLI framework: Typer

**Context.** The CLI driving adapter needs a framework for argument parsing, help generation, and command grouping.

**Decision.** Use Typer. Commands are defined as plain Python functions with type-annotated parameters; Typer derives argument names, types, and help text from those annotations automatically.

**Consequences.** CLI commands read like normal Python functions. Type annotations do double duty: mypy checks them, Typer reads them. `CliRunner` from Typer's test utilities allows testing CLI commands without spawning subprocesses. The entry point is declared in `pyproject.toml` under `[project.scripts]`, so `pip install -e .` makes the `kirokyu` command available in the venv.

---

## 19. REST API framework: FastAPI

**Context.** The REST API driving adapter needs an HTTP framework.

**Decision.** Use FastAPI. The deciding factors: (1) we already use Pydantic v2 for DTOs — FastAPI reads those same models for request validation and response serialization at no extra cost; (2) FastAPI generates interactive OpenAPI documentation at `/docs` automatically from type annotations; (3) FastAPI is the current industry standard for new Python APIs.

**Consequences.** The `CreateTaskInput` and `TaskOutput` DTOs from Phase 1 plug directly into FastAPI route signatures. Validation failures return 422 automatically. `TestClient` from `httpx` allows testing routes without a running server. The hexagonal core is unaware of FastAPI — nothing in the domain or application layer imports it.

---

## 20. Composition root: bootstrap module with UseCases dataclass

**Context.** Both the CLI and the REST API need to construct the same set of use cases wired to a repository adapter and infrastructure providers. Without a central wiring point, that construction logic would be duplicated.

**Decision.** Introduce `src/kirokyu/bootstrap.py` as the composition root. It exports a `UseCases` dataclass and a `build_use_cases()` factory that reads configuration from environment variables, instantiates the selected adapter, and returns a fully wired bundle. The CLI and API call `build_use_cases()` once at startup and never import adapter classes themselves.

**Consequences.** The bootstrap is the only file that imports both application-layer and adapter-layer types simultaneously — intentional and contained. Adapter selection lives in exactly one place. Tests override the bundle directly without touching environment variables or the filesystem.

*Last updated: April 21, 2026 (Phase 3 — CLI and REST API driving adapters).*

---

## 21. GitHub migration and CI: Phase 6

**Context.** The project plan deferred GitHub migration to Phase 6. Local git history was maintained from day one (Decision 10), making migration a single push operation.

**Decision.** Migrate to GitHub at `https://github.com/amryounis/kirokyu`. Add GitHub Actions CI workflow running ruff lint, ruff format check, mypy, and pytest on every push to main. Defer Dockerfile — not justified for a local-first personal app at this stage.

**Consequences.** The full git history from Phase 0 is preserved on GitHub. CI enforces the same quality gates as local pre-commit on every push, catching issues that pre-commit auto-fixes locally but would otherwise be invisible in CI. Dockerfile deferred to a future phase when deployment or distribution needs arise.

*Last updated: April 22, 2026 (Phase 6 — Production polish).*
