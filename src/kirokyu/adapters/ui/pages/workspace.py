"""Workspace selection page."""

from __future__ import annotations

import streamlit as st

from kirokyu.workspaces.registry import WorkspaceRegistry


def show() -> None:
    """Render the workspace selection page."""
    st.title("Kirokyu")
    st.subheader("Select or create a workspace to get started")

    registry = WorkspaceRegistry()
    workspaces = registry.list_all()

    # --- Open existing workspace ---
    if workspaces:
        st.markdown("#### Open workspace")
        for ws in workspaces:
            last = ws.last_opened_at.strftime("%Y-%m-%d %H:%M") if ws.last_opened_at else "never"
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{ws.name}** — last opened: {last}")
            with col2:
                if st.button("Open", key=f"open_{ws.name}"):
                    registry.touch(ws.name)
                    st.session_state.workspace = ws.name
                    st.session_state.page = "task_list"
                    st.rerun()

        st.divider()

    # --- Create new workspace ---
    st.markdown("#### Create workspace")
    with st.form("create_workspace"):
        name = st.text_input(
            "Workspace name",
            placeholder="e.g. personal, work, side-project",
        )
        submitted = st.form_submit_button("Create")
        if submitted:
            if not name:
                st.error("Workspace name cannot be empty.")
            else:
                try:
                    registry.create(name.strip())
                    registry.touch(name.strip())
                    st.session_state.workspace = name.strip()
                    st.session_state.page = "task_list"
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
