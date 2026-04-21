"""Task detail page — view and edit a single task."""

from __future__ import annotations

import streamlit as st

from kirokyu.application.dtos import UpdateTaskInput
from kirokyu.bootstrap import UseCases, build_use_cases
from kirokyu.domain.exceptions import TaskNotFoundError
from kirokyu.domain.value_objects import Priority


def _uc() -> UseCases:
    return build_use_cases(workspace=st.session_state.workspace)


def show() -> None:
    """Render the task detail page."""
    task_id = st.session_state.get("selected_task_id")
    if not task_id:
        st.session_state.page = "task_list"
        st.rerun()

    try:
        task = _uc().get_task.execute(task_id)
    except TaskNotFoundError:
        st.error("Task not found.")
        if st.button("Back to list"):
            st.session_state.page = "task_list"
            st.rerun()
        return

    # --- Back button ---
    if st.button("← Back to list"):
        st.session_state.page = "task_list"
        st.rerun()

    st.title(task.title)
    st.caption(f"ID: {task.id}  ·  status: {task.status.value}  ·  created: {task.created_at[:10]}")

    st.divider()

    # --- Edit form ---
    with st.form("update_task"):
        title = st.text_input("Title", value=task.title)
        description = st.text_area("Description", value=task.description, height=100)
        priority = st.selectbox(
            "Priority",
            options=[p.value for p in Priority],
            index=[p.value for p in Priority].index(task.priority.value),
        )
        starred = st.checkbox("Starred", value=task.starred)
        submitted = st.form_submit_button("Save changes")
        if submitted:
            try:
                input_ = UpdateTaskInput(
                    title=title.strip(),
                    description=description,
                    priority=Priority(priority),
                    starred=starred,
                )
                _uc().update_task.execute(task_id, input_)
                st.success("Saved.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    st.divider()

    # --- Actions ---
    st.markdown("#### Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if task.status.value == "pending" and st.button("Mark as complete"):
            try:
                _uc().complete_task.execute(task_id)
                st.rerun()
            except TaskNotFoundError as e:
                st.error(str(e))
        elif task.status.value == "completed" and st.button("Revert to pending"):
            try:
                _uc().uncomplete_task.execute(task_id)
                st.rerun()
            except TaskNotFoundError as e:
                st.error(str(e))

    with col2:
        if task.status.value == "archived":
            if st.button("Unarchive"):
                try:
                    _uc().unarchive_task.execute(task_id)
                    st.rerun()
                except TaskNotFoundError as e:
                    st.error(str(e))
        else:
            if st.button("Archive"):
                try:
                    _uc().archive_task.execute(task_id)
                    st.rerun()
                except TaskNotFoundError as e:
                    st.error(str(e))

    with col3:
        if st.button("Delete task", type="primary"):
            try:
                _uc().delete_task.execute(task_id)
                st.session_state.page = "task_list"
                st.rerun()
            except TaskNotFoundError as e:
                st.error(str(e))
