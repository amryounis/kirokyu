"""Task list page — main view."""

from __future__ import annotations

import streamlit as st

from kirokyu.application.dtos import CreateTaskInput
from kirokyu.bootstrap import UseCases, build_use_cases
from kirokyu.domain.exceptions import TaskNotFoundError
from kirokyu.domain.value_objects import Priority


def _uc() -> UseCases:
    """Return use cases for the active workspace."""
    return build_use_cases(workspace=st.session_state.workspace)


def show() -> None:
    """Render the task list page."""
    workspace = st.session_state.workspace
    st.title(f"Kirokyu — {workspace}")

    _, col2 = st.columns([6, 1])
    with col2:
        if st.button("Switch workspace"):
            st.session_state.workspace = None
            st.session_state.page = "workspace"
            st.rerun()

    st.divider()

    # --- Create task form ---
    with st.expander("New task", expanded=False), st.form("create_task"):
        title = st.text_input("Title")
        description = st.text_area("Description", height=80)
        priority = st.selectbox(
            "Priority",
            options=[p.value for p in Priority],
            index=1,
        )
        starred = st.checkbox("Starred")
        submitted = st.form_submit_button("Create")
        if submitted:
            if not title.strip():
                st.error("Title cannot be empty.")
            else:
                try:
                    input_ = CreateTaskInput(
                        title=title.strip(),
                        description=description,
                        priority=Priority(priority),
                        starred=starred,
                    )
                    _uc().create_task.execute(input_)
                    st.success(f"Created: {title.strip()}")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    st.divider()

    # --- Task list ---
    tasks = _uc().list_tasks.execute()
    pending = [t for t in tasks if t.status.value == "pending"]
    completed = [t for t in tasks if t.status.value == "completed"]
    archived = [t for t in tasks if t.status.value == "archived"]

    st.markdown(f"#### Pending ({len(pending)})")
    if not pending:
        st.caption("No pending tasks.")
    for task in pending:
        _render_task_row(task)

    if completed:
        with st.expander(f"Completed ({len(completed)})"):
            for task in completed:
                _render_task_row(task, show_uncomplete=True)

    if archived:
        with st.expander(f"Archived ({len(archived)})"):
            for task in archived:
                _render_task_row(task, show_unarchive=True)


def _render_task_row(
    task: object,
    show_uncomplete: bool = False,
    show_unarchive: bool = False,
) -> None:
    from kirokyu.application.dtos import TaskOutput

    t = task
    assert isinstance(t, TaskOutput)

    star = "★" if t.starred else ""
    due = f" · due {t.due_date.isoformat()}" if t.due_date else ""
    label = f"{star} **{t.title}** `{t.priority.value}`{due}"

    col1, col2, col3, col4, col5 = st.columns([5, 1, 1, 1, 1])
    with col1:
        st.markdown(label)
    with col2:
        if st.button("View", key=f"view_{t.id}"):
            st.session_state.page = "task_detail"
            st.session_state.selected_task_id = t.id
            st.rerun()
    with col3:
        if show_uncomplete:
            if st.button("Undo", key=f"uncomplete_{t.id}"):
                try:
                    _uc().uncomplete_task.execute(t.id)
                    st.rerun()
                except TaskNotFoundError as e:
                    st.error(str(e))
        elif show_unarchive:
            if st.button("Restore", key=f"unarchive_{t.id}"):
                try:
                    _uc().unarchive_task.execute(t.id)
                    st.rerun()
                except TaskNotFoundError as e:
                    st.error(str(e))
        else:
            if st.button("Done", key=f"complete_{t.id}"):
                try:
                    _uc().complete_task.execute(t.id)
                    st.rerun()
                except TaskNotFoundError as e:
                    st.error(str(e))
    with col4:
        if not show_unarchive and st.button("Archive", key=f"archive_{t.id}"):
            try:
                _uc().archive_task.execute(t.id)
                st.rerun()
            except TaskNotFoundError as e:
                st.error(str(e))
    with col5:
        if st.button("Delete", key=f"delete_{t.id}"):
            try:
                _uc().delete_task.execute(t.id)
                st.rerun()
            except TaskNotFoundError as e:
                st.error(str(e))
