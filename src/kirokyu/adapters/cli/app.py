"""CLI driving adapter — Typer-based command-line interface for Kirokyu."""

from __future__ import annotations

import typer

from kirokyu.application.dtos import CreateTaskInput, UpdateTaskInput
from kirokyu.bootstrap import UseCases, build_use_cases
from kirokyu.domain.exceptions import TaskNotFoundError
from kirokyu.domain.value_objects import Priority
from kirokyu.workspaces.registry import WorkspaceRegistry

app = typer.Typer(
    name="kirokyu",
    help="Kirokyu — personal task manager.",
    no_args_is_help=True,
)
task_app = typer.Typer(help="Manage tasks.", no_args_is_help=True)
app.add_typer(task_app, name="task")

_use_cases: UseCases | None = None
_workspace_name: str | None = None


def _uc() -> UseCases:
    global _use_cases
    if _use_cases is None:
        _use_cases = build_use_cases(workspace=_workspace_name)
    return _use_cases


@app.callback()
def main(
    workspace: str | None = typer.Option(
        None,
        "--workspace",
        "-w",
        envvar="KIROKYU_WORKSPACE",
        help="Workspace name. Falls back to KIROKYU_WORKSPACE env var.",
    ),
) -> None:
    """Kirokyu — personal task manager."""
    global _workspace_name
    _workspace_name = workspace


@task_app.command("create")
def create_task(
    title: str = typer.Argument(..., help="Task title."),
    description: str = typer.Option("", "--desc", "-d", help="Optional description."),
    priority: Priority = typer.Option(
        Priority.MEDIUM, "--priority", "-p", help="low | medium | high"
    ),
    starred: bool = typer.Option(False, "--starred", "-s", help="Mark as starred."),
) -> None:
    """Create a new task."""
    input_ = CreateTaskInput(
        title=title,
        description=description,
        priority=priority,
        starred=starred,
    )
    output = _uc().create_task.execute(input_)
    typer.echo(f"Created  {output.id}")
    typer.echo(f"  title:    {output.title}")
    typer.echo(f"  priority: {output.priority.value}")


@task_app.command("list")
def list_tasks(
    all_statuses: bool = typer.Option(
        False, "--all", "-a", help="Include completed and archived tasks."
    ),
) -> None:
    """List tasks."""
    tasks = _uc().list_tasks.execute()
    if not all_statuses:
        tasks = [t for t in tasks if t.status.value == "pending"]
    if not tasks:
        typer.echo("No tasks found.")
        return
    for task in tasks:
        star = "★" if task.starred else " "
        due = f"  due {task.due_date.isoformat()}" if task.due_date else ""
        typer.echo(f"{star} {task.id[:8]}…  [{task.priority.value:6}]  {task.title}{due}")


@task_app.command("complete")
def complete_task(
    task_id: str = typer.Argument(..., help="Task ID."),
) -> None:
    """Mark a task as completed."""
    try:
        output = _uc().complete_task.execute(task_id)
        typer.echo(f"Completed: {output.title}")
    except TaskNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e


@task_app.command("get")
def get_task(
    task_id: str = typer.Argument(..., help="Task ID."),
) -> None:
    """Show full details of a single task."""
    try:
        output = _uc().get_task.execute(task_id)
        star = "★" if output.starred else "☆"
        due = output.due_date.isoformat() if output.due_date else "—"
        typer.echo(f"  {star} [{output.status.value}] {output.title}")
        typer.echo(f"     id:       {output.id}")
        typer.echo(f"     priority: {output.priority.value}")
        typer.echo(f"     due:      {due}")
        if output.description:
            typer.echo(f"     desc:     {output.description}")
    except TaskNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e


@task_app.command("update")
def update_task(
    task_id: str = typer.Argument(..., help="Task ID."),
    title: str | None = typer.Option(None, "--title", "-t"),
    description: str | None = typer.Option(None, "--desc", "-d"),
    priority: Priority | None = typer.Option(None, "--priority", "-p"),
    starred: bool | None = typer.Option(None, "--starred/--no-starred"),
) -> None:
    """Update one or more fields on a task."""
    try:
        input_ = UpdateTaskInput(
            title=title,
            description=description,
            priority=priority,
            starred=starred,
        )
        output = _uc().update_task.execute(task_id, input_)
        typer.echo(f"Updated: {output.title}")
    except TaskNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e


@task_app.command("archive")
def archive_task(
    task_id: str = typer.Argument(..., help="Task ID."),
) -> None:
    """Archive a task."""
    try:
        output = _uc().archive_task.execute(task_id)
        typer.echo(f"Archived: {output.title}")
    except TaskNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e


@task_app.command("unarchive")
def unarchive_task(
    task_id: str = typer.Argument(..., help="Task ID."),
) -> None:
    """Return an archived task to pending."""
    try:
        output = _uc().unarchive_task.execute(task_id)
        typer.echo(f"Unarchived: {output.title}")
    except TaskNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e


@task_app.command("uncomplete")
def uncomplete_task(
    task_id: str = typer.Argument(..., help="Task ID."),
) -> None:
    """Revert a completed task back to pending."""
    try:
        output = _uc().uncomplete_task.execute(task_id)
        typer.echo(f"Reverted to pending: {output.title}")
    except TaskNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e


@task_app.command("delete")
def delete_task(
    task_id: str = typer.Argument(..., help="Task ID."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
) -> None:
    """Permanently delete a task."""
    if not yes:
        typer.confirm("This cannot be undone. Continue?", abort=True)
    try:
        _uc().delete_task.execute(task_id)
        typer.echo("Deleted.")
    except TaskNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e


# ---------------------------------------------------------------------------
# Workspace commands
# ---------------------------------------------------------------------------

workspace_app = typer.Typer(help="Manage workspaces.", no_args_is_help=True)
app.add_typer(workspace_app, name="workspace")


@workspace_app.command("create")
def workspace_create(
    name: str = typer.Argument(..., help="Workspace name (letters, digits, hyphens, underscores)."),
) -> None:
    """Create a new workspace."""
    try:
        registry = WorkspaceRegistry()
        ws = registry.create(name)
        typer.echo(f"Created workspace '{ws.name}'")
        typer.echo(f"  db: {ws.db_path}")
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e


@workspace_app.command("list")
def workspace_list() -> None:
    """List all workspaces."""
    registry = WorkspaceRegistry()
    workspaces = registry.list_all()
    if not workspaces:
        typer.echo("No workspaces found. Create one with: kirokyu workspace create <name>")
        return
    for ws in workspaces:
        last = ws.last_opened_at.strftime("%Y-%m-%d %H:%M") if ws.last_opened_at else "never"
        typer.echo(f"  {ws.name:20}  last opened: {last}")


@workspace_app.command("delete")
def workspace_delete(
    name: str = typer.Argument(..., help="Workspace name to delete."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
    remove_db: bool = typer.Option(False, "--remove-db", help="Also delete the SQLite file."),
) -> None:
    """Remove a workspace from the registry."""
    try:
        registry = WorkspaceRegistry()
        ws = registry.get(name)
        if ws is None:
            typer.echo(f"Workspace {name!r} not found.", err=True)
            raise typer.Exit(1)
        if not yes:
            typer.confirm(
                f"Remove workspace '{name}' from registry?",
                abort=True,
            )
        registry.delete(name)
        typer.echo(f"Removed workspace '{name}' from registry.")
        if remove_db:
            from pathlib import Path

            db = Path(ws.db_path)
            if db.exists():
                db.unlink()
                typer.echo(f"Deleted database file: {ws.db_path}")
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
