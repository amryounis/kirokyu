# Architecture

*Status: stub. Substantive content will be added as Phase 1 (Hexagonal core) materializes.*

## Intended approach

Kirokyu is built using Hexagonal Architecture (also known as Ports and Adapters), introduced by Alistair Cockburn. The pattern's central idea is that the core application logic should be isolated from infrastructure concerns.

The organizing principles will be:

- **Domain core depends on nothing external.** No database, no framework, no web library. The domain layer expresses the business rules of task management using only Python's standard library.

- **Ports are interfaces defined by the domain.** The domain declares what it needs (e.g., a way to persist a task) as an abstract interface — but does not care *how* that interface is implemented.

- **Adapters are infrastructure implementations of those interfaces.** The SQLite storage layer is an adapter. The JSON file storage layer is another adapter. The CLI is a "driving" adapter that calls into the domain. The REST API is another driving adapter. Each adapter is a peripheral concern, not a central one.

- **Dependencies always point inward.** Infrastructure depends on the domain. The domain never depends on infrastructure. This dependency rule is what makes the architecture swappable.

## Why this approach

For a project whose purpose is to demonstrate engineering discipline, Hexagonal Architecture provides several affordances:

- Tests can exercise the domain without any infrastructure.
- The same domain can be reached through multiple delivery mechanisms (CLI, API, UI) without duplication.
- Swapping persistence from SQLite to Postgres or from JSON to a remote API changes one adapter without touching the domain.
- The architecture makes architectural drift visible — attempts to couple the domain to infrastructure fail type checks before they cause runtime problems.

## Further detail

This document will be extended phase by phase:

- **Phase 1** will describe the domain entities, value objects, use cases, and ports.
- **Phase 2** will document the persistence adapters in detail.
- **Phase 3** will document the CLI and API driving adapters.
- **Phase 4 and beyond** will capture higher-level decisions as they emerge.

## References

- Alistair Cockburn, "Hexagonal Architecture" (2005): the original paper introducing the pattern.
- Vaughn Vernon, *Implementing Domain-Driven Design* (2013): treats Hexagonal as a structural foundation for DDD.
