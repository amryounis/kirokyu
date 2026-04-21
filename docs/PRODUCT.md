# Kirokyu — Product Definition

**Status:** Living document — updated as decisions are made.

**Last updated:** April 21, 2026

---

## What is Kirokyu?

Kirokyu is a personal task management application. It is intentionally small and honest about its purpose: help one person organize, track, and complete their work.

It is **not** a project management tool, not a team collaboration platform, not an enterprise solution. Those are different products, built later if needed, not features bolted onto this one.

The north star is **Microsoft To Do** — a clean, focused application that does one thing well and resists feature bloat.

---

## Core Domain

### Tasks

The central entity. Each task has:

| Field | Type | Notes |
|-------|------|-------|
| Title | Text | Required |
| Description | Text | Optional; can be empty |
| Due date | Date | Optional |
| Start date | Date | Optional; "when I plan to begin work" |
| Priority | Enum | LOW, MEDIUM, HIGH |
| Status | Enum | PENDING, ARCHIVED, DELETED |
| Time estimate | Number | Hours or minutes; informational only |
| Starred | Boolean | User-favorite flag for quick access |
| Color | Color | User-assigned visual grouping |
| Manual order | Number | Position within its list/view; used for drag-and-drop |
| Created at | Timestamp | Immutable |
| Updated at | Timestamp | Last modification time |

**Important constraints:**
- A task can only be completed if all its dependencies are completed (enforced).
- Archived tasks are hidden by default; deleted tasks are permanently removed.
- Un-completion is allowed — a task can toggle back from completed to pending.

### Subtasks

Nested under a parent task. Each subtask has:
- Title
- Status (pending / completed)
- Created at, updated at

Subtasks inherit metadata (tags, color, attachments) from the parent unless explicitly overridden. When a parent task is completed, all subtasks auto-complete.

### Lists

User-created collections. Each list has:
- Name (required)
- Color (required)
- Emoji (optional icon for visual identification)
- Created at, updated at

A task belongs to exactly one list. Lists can be manually reordered in the sidebar.

### Tags

User-created labels (e.g., `#work`, `#home`, `#urgent`). A task can have zero or more tags. Tags are searchable.

### Contacts

A user-maintained reference list of people and entities relevant to tasks. Each contact has:
- Name (required)
- Created at, updated at

A task can reference a contact via one of four relationship types:
- **Depends on** — "I can't start until X happens"
- **Delegated to** — "I asked X to handle this"
- **Waiting on** — "I'm blocked waiting for X"
- **For** — "This task is for X" (informational)

**Important:** Contacts are *not* users. Kirokyu is single-user. Contacts are names the user maintains for reference and task relationships. A contact has no login, no account, no ability to see or modify tasks.

### Attachments

A task can have zero or more attachments: files, images, or links. Attachments are stored alongside the task data (locally, in the database or file system).

### Reminders

A task can have a reminder time (distinct from the due date). Reminders fire *only while Kirokyu is running*. When the user closes the app, it warns them about pending reminders they will miss. No background processes, no OS integration, no notifications after shutdown.

### Recurring Patterns

A task can be marked as recurring with a simple pattern:
- Daily
- Weekly (on selected days)
- Monthly (on a selected date)

When a recurring task completes, a new instance is created with:
- Same title, description, priority, time estimate, tags, subtasks, attachments, and contact relationships
- Fresh due date based on the recurrence pattern
- New "created at" timestamp
- Status reset to PENDING

---

## Views & Navigation

### Smart Views (built-in, automatic)

- **My Day** — manually curated focus list, resets daily. User picks which tasks to work on today, separate from calendar.
- **Due Today** — automatic, shows all tasks due today (by due date)
- **Overdue** — automatic, shows all tasks whose due date has passed and aren't complete
- **Important** — all starred tasks
- **Planned** — all tasks with a due date
- **All Tasks** — catch-all, everything

### User Lists

User-created lists, shown in sidebar. Tasks belong to exactly one list.

### Sorting & Filtering

Within any view, the user can:
- **Sort by:** priority, due date, creation date, alphabetical, manual order
- **Filter by:** tags, contacts, list, date range, completion status
- **Search:** text search across title, description, tags
- **Filter presets:** common combinations saved for quick access (e.g., "due this week," "tagged #client-x")

**Important:** When sorting by manual order, drag-and-drop reordering is enabled. When sorting by other criteria, drag handles are disabled.

---

## Undo & Redo

Most actions are undoable:
- Create, edit, delete, complete, un-complete tasks
- Reorder tasks
- Modify tags, contacts, attachments

A simple linear undo/redo stack (undo, then redo, no branching).

---

## Reporting & Analytics

A dedicated **Reports** view within the app providing insight into task data. No heavy analysis, no machine learning — just clear, useful charts built from straightforward aggregations.

### Core Reports

1. **Completion Rate** — percentage of all tasks completed (all-time, this month, this week selectable)
2. **Tasks by Priority** — distribution pie/bar chart (LOW, MEDIUM, HIGH count)
3. **Tasks by List** — bar chart showing task count per user-created list
4. **Completion Trend** — line chart tracking tasks completed over time (daily, weekly, monthly granularity selectable)
5. **Overdue Summary** — count of overdue tasks, grouped by how long overdue (1-3 days, 4-7 days, 1+ weeks)

All charts are read-only views of task data. No drill-down into tasks from charts (yet). Charts update in real-time as tasks are created, completed, archived.

---

---

## Import & Export

### Export

User can export tasks in:
- **CSV** — flat table format, one row per task with columns for each field
- **JSON** — structured format preserving all relationships (subtasks, attachments, etc.)

Export includes all tasks (completed, pending, archived) unless filtered before export.

### Import

User can import tasks from:
- **CSV files** — parsed and merged into existing data
- **JSON files** — must match the export format

Import merges with existing data; it does not replace. Duplicates are user's responsibility to manage.

---

## Settings & Preferences

User-configurable options:
- **Theme** — light / dark mode
- **Default list** — which list to show on startup
- **Startup behavior** — show My Day, show All Tasks, or remember last view
- **Date format** — MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, etc.
- **Reminder sound** — on / off, sound selection
- **Recurring task default** — when a new recurring task is created, default pattern (none, daily, weekly, monthly)
- **Language / locale** — English is the default UI language. Arabic is the first additional language, with full RTL layout support tied to language selection. RTL layout without a translated UI is meaningless — the two are implemented together. Additional languages (e.g. French, German, Hebrew) can be contributed by the community by dropping in a new language file; no code changes are required. Data storage is Unicode (UTF-8) throughout and supports any language for content entry today. i18n architecture is built in from Phase 4 onwards.

---

## Workspaces

A workspace is an isolated data silo — its own SQLite database file, its own tasks, completely separate from other workspaces. The user switches between workspaces explicitly.

Each workspace has:
- Name (required, used as the SQLite filename)
- Created at
- Last opened at

Workspace metadata is stored in a registry file at `~/.kirokyu/workspaces.json`. Each workspace's tasks live in a corresponding SQLite file at `~/.kirokyu/workspaces/<name>.db`.

**Workspace lifecycle:**
- On first launch, the app has no active workspace — the user must create or open one before any task actions are available
- The user can create a new workspace, open an existing one from the registry, or delete a workspace (with confirmation)
- Closing a workspace returns the user to the workspace selection screen

**Design rationale:** workspaces allow a single Kirokyu installation to serve multiple independent contexts (personal, work, side project) without data mixing. The hexagonal core is unaware of workspaces — the bootstrap selects the correct SQLite file before constructing use cases.

---

## Data Storage & Sync

### Storage

Tasks are stored **locally** on the user's machine in one of two formats (Phase 2 decision):
- SQLite database file
- JSON file

The user never manually manages these files; Kirokyu handles persistence transparently.

### No Cloud Sync

Kirokyu **does not sync across devices**. One machine, one data store. If the user wants to work on multiple machines, they export from one and import to another (manual process).

This simplifies the architecture, avoids server infrastructure, and keeps the user's data fully under their control.

---

## What Kirokyu Is NOT

- **Not a project management tool.** No Gantt charts, no critical paths, no resource allocation. If that becomes necessary, it's a different app.
- **Not a team collaboration platform.** No real-time sharing, no @mentions, no activity feeds. Single user, period.
- **Not a time-tracking app.** No timers, no time logging, no billable hours. Time estimate is informational only.
- **Not a calendar.** Kirokyu shows due dates; it doesn't replace a calendar. No agenda view, no time-blocking.
- **Not backed by a server.** Local data store only. No accounts, no logins, no cloud. Export/import for moving data.
- **Not a note-taking app.** Descriptions are task-specific; there's no free-form note library or knowledge base.

---

## Growth & Future

This is intentional: **Kirokyu is not a roadmap. It's a product.**

If the user's needs grow beyond what Kirokyu offers (e.g., team collaboration, project management, analytics), the answer is not to bloat Kirokyu. The answer is to build a *different* application, potentially on the same architectural skeleton but with a different domain and different purpose.

The architecture is designed to be portable — if Kirokyu's structure proves sound, the next product can reuse the patterns without reusing the code. That's the meaning of "pivot-ready."

For now: Kirokyu is a to-do app. It stays that way until it doesn't, and if it stops being that, we build something new.

---

## Design Principles

1. **Honest about scope.** Kirokyu does what it says, nothing more.
2. **Simple by default.** When two designs are equally valid, pick the simpler one.
3. **Local-first.** User data stays on their machine. No cloud, no tracking, no vendor lock-in.
4. **Portable.** The architecture supports domain swaps; the code supports multiple UI layers.
5. **Usable.** It's not just a learning project; you'll actually use it daily.

---

## Next Steps

This definition feeds directly into Phase 1 (Hexagonal Core). The domain entities, value objects, ports, and use cases all derive from this spec. If something in this doc changes, Phase 1 pivots; if Phase 1 reveals something this doc missed, the doc updates.

The product is defined. The architecture work begins.
