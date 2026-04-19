# To-Do App — Learning & Showcase Project Plan

## Purpose

This project is deliberately a **training vehicle**, not a product. The to-do domain is chosen because it is small enough to keep out of the way while the real subjects — architecture, Python craftsmanship, layered design, UI and persistence options — are practiced properly.

The plan serves three overlapping purposes, in no fixed order of priority:

- **Learning** — deliberate practice of Hexagonal Architecture, clean Python, testing discipline, and the broader toolset.
- **Interviews / portfolio** — a codebase whose *quality* and *clarity of decisions* evidence seniority.
- **Business (optional, later)** — once the toolset and mindset are mastered, pivot to a domain with commercial weight. The architecture chosen here is deliberately pivot-friendly: swap the domain, keep the skeleton.

The family-venture direction (with Kareem and Nour) is parked for now and will be revisited separately when it matures.

---

## Guiding principles

- **Every phase ends at a showable state.** No phase depends on a later phase being finished. Stopping after Phase 2 still leaves a complete, demo-able artifact.
- **Session-sized units of work.** Availability is lumpy — scope within a sitting matters more than scope within a phase.
- **Add layers, not features.** A to-do app is a small domain by design. Depth comes from architecture and craft, not feature count.
- **Document as you go.** README is alive from Phase 0. Decision records (`DECISIONS.md` or lightweight ADRs) capture *why*, not just *what*.
- **Local-first git from day one.** Full history migrates cleanly to GitHub when the time comes.
- **Resist interruption panic.** If priorities shift, pause cleanly. The project tolerates gaps.

---

## Environment & tooling decisions

| Area | Decision | Reasoning |
|------|----------|-----------|
| OS | Windows 10 + WSL2 (Ubuntu) | Real Linux without VM overhead; deployment target parity. Note: Windows 10 ESU runs through Oct 13, 2026 — enroll if staying on it. |
| Editor | VS Code + Remote-WSL | Edit from Windows, execute on Linux. |
| Python | 3.12, pinned in `pyproject.toml` | Stable; well supported by FastAPI, Pydantic v2, SQLAlchemy 2.x, Streamlit, Flet. |
| Packaging | `src/` layout + `pyproject.toml` | Modern Python standard; avoids import surprises. |
| Lint / format | `ruff` | One tool replaces several. |
| Types | `mypy` (strict where feasible) | Catches mistakes the architecture is meant to surface. |
| Tests | `pytest` | De facto standard. |
| Hooks | `pre-commit` | Enforces standards without thinking. |
| VCS | `git` from day one, local only initially | Clean history, painless GitHub migration later. |
| Persistence (primary) | SQLite via SQLAlchemy 2.x | Lightweight, embeddable, exportable. |
| Persistence (secondary, for demonstration) | JSON file adapter | Showcases Ports & Adapters — same port, two adapters. |
| UI (primary) | Streamlit | Fastest path to demo; fits data-direction career track. |
| UI (optional, later) | Flet | Desktop/web/mobile from one codebase — added only if a concrete need appears. |
| API | FastAPI | Pairs naturally with Pydantic; industry-standard. |
| CLI | Typer | Shares the same use cases as the API. |

---

## Phased roadmap

### Phase 0 — Foundation (~1 week)

Set up the project the way a professional would before writing domain code.

- WSL2 + Ubuntu installed, VS Code Remote-WSL connected.
- `src/` layout project with `pyproject.toml`.
- `ruff`, `mypy`, `pytest`, `pre-commit` configured.
- `git init`, comprehensive `.gitignore` (Python, venv, SQLite files, `.env`, IDE clutter).
- Initial README with project purpose and status.
- `DECISIONS.md` started with the decisions captured in this plan.

**Showable state:** a repo that already signals care. Most portfolio projects skip this step and it shows.

---

### Phase 1 — The hexagonal core (~2 weeks)

Domain-only. No infrastructure.

- `Task` entity, value objects (`TaskId`, `Priority`, `DueDate`).
- `TaskRepository` port (interface, no implementation).
- Use cases: `CreateTask`, `CompleteTask`, `ListTasks`.
- Pydantic DTOs at the boundary of the use cases.
- In-memory repository as the only adapter.
- Test suite exercising real business logic without any infrastructure.

**Showable state:** a passing test suite and a clean dependency graph where the core depends on nothing. This is the phase that proves Hexagonal understanding — rare among candidates.

---

### Phase 2 — Persistence adapters (~1 week)

Two adapters for the same port. Configuration-selected.

- SQLite adapter (SQLAlchemy 2.x).
- JSON file adapter.
- Configuration mechanism to swap between them.
- Tests for each adapter against the same port contract.

**Showable state:** the core did not change by a single line to gain persistence. Ports & Adapters made visible.

---

### Phase 3 — Driving adapters: CLI + API (~2 weeks)

Two delivery mechanisms. Shared use cases. Zero duplication.

- CLI with Typer.
- REST API with FastAPI.
- Both call the exact same use case layer.
- Integration tests for each.

**Showable state:** same business logic reachable through two completely different interfaces. Interface independence demonstrated.

---

### Phase 4 — UI layer (~1–2 weeks)

Web UI first. Desktop/mobile deferred.

- Streamlit app that talks to the FastAPI layer (not directly to the core).
- Clean separation — the UI is another adapter, not a new codebase.
- Optional later: Flet for desktop/mobile from the same Python codebase.

**Showable state:** a working UI that a non-technical viewer can use, built on exactly the same core as the CLI and API.

---

### Phase 5 — Analytics / BI layer (~2 weeks)

Separate read side. Introduces CQRS lightly.

- Read model for completion trends, productivity metrics, overdue analysis.
- Distinct bounded context — not bolted onto the transactional core.
- Streamlit + Plotly dashboard consuming the read side.

**Showable state:** fluency in separating transactional from analytical concerns — directly aligned with the data-analysis career track.

---

### Phase 6 — Production polish (~1 week)

The framing and final surface.

- Dockerfile(s) and `docker-compose`.
- GitHub Actions CI (lint, type check, tests).
- README rewrite with architecture diagrams and design rationale.
- Optional: short walkthrough video or blog post.
- GitHub migration if not already done.

**Showable state:** something a stranger could land on, understand, and respect.

---

## Minimum viable showcase

Phases **1 through 3** (plus Phase 0) are the minimum viable portfolio artifact. Roughly 5–6 weeks of focused evening work. If the job search intensifies or priorities shift, pausing at that checkpoint is legitimate — what's built is complete on its own terms.

Phases 4–6 are what turn it from solid to distinctive.

---

## Working rhythm

- **Per session:** finish one atomic unit (a use case, one adapter, one endpoint). Commit cleanly. Never leave a half-state.
- **Per phase:** end at a state that would pass a review today.
- **Per interruption:** `DECISIONS.md` and README capture enough context that a two-week gap doesn't require re-reading the codebase.

---

## What this plan is not

- Not a product roadmap. There is no marketing, no user research, no pricing.
- Not a rigid schedule. Timelines are estimates under ideal focus; real life applies.
- Not permanent. If a real business domain emerges, the to-do domain gets retired and the skeleton carries forward.

---

*Last updated: April 18, 2026.*
