"""CLI driving adapter — Typer-based command-line interface for Kirokyu."""

from __future__ import annotations

import typer

from kirokyu.application.dtos import CreateTaskInput, UpdateTaskInput
from kirokyu.bootstrap import UseCases, build_use_cases
from kirokyu.domain.exceptions import TaskNotFoundError
from kirokyu.domain.value_objects import Priority

app = typer.Typer(
    name="kirokyu",
    help="Kirokyu — personal task manager.",
    no_args_is_help=True,
)
task_app = typer.Typer(help="Manage tasks.", no_args_is_help=True)
app.add_typer(task_app, name="task")

_use_cases: UseCases | None = None


def _uc() -> UseCases:
    global _use_cases
    if _use_cases is None:
        _use_cases = build_use_cases()
    return _use_cases


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


if __name__ == "__main__":
    app()
