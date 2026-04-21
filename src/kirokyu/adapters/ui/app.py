"""Streamlit UI — driving adapter for Kirokyu.

Run with:
    streamlit run src/kirokyu/adapters/ui/app.py

Environment variables:
    KIROKYU_WORKSPACE   workspace name to open directly (skips selection page)
"""

from __future__ import annotations

import os

import streamlit as st

from kirokyu.adapters.ui.pages import analytics, task_detail, task_list, workspace

st.set_page_config(
    page_title="Kirokyu",
    page_icon="✓",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "page" not in st.session_state:
    st.session_state.page = "workspace"

if "workspace" not in st.session_state:
    st.session_state.workspace = None

if "selected_task_id" not in st.session_state:
    st.session_state.selected_task_id = None

# ---------------------------------------------------------------------------
# Environment variable override
# ---------------------------------------------------------------------------

if "env_loaded" not in st.session_state:
    st.session_state.env_loaded = False

if not st.session_state.env_loaded:
    env_workspace = os.environ.get("KIROKYU_WORKSPACE")
    if env_workspace:
        st.session_state.workspace = env_workspace
        st.session_state.page = "task_list"
    st.session_state.env_loaded = True

# ---------------------------------------------------------------------------
# Sidebar navigation (only when workspace is active)
# ---------------------------------------------------------------------------

if st.session_state.workspace:
    with st.sidebar:
        st.markdown(f"**Workspace:** {st.session_state.workspace}")
        st.divider()
        if st.button("📋 Tasks", use_container_width=True):
            st.session_state.page = "task_list"
            st.rerun()
        if st.button("📊 Analytics", use_container_width=True):
            st.session_state.page = "analytics"
            st.rerun()
        st.divider()
        if st.button("⇄ Switch workspace", use_container_width=True):
            st.session_state.workspace = None
            st.session_state.page = "workspace"
            st.rerun()

# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------

if st.session_state.workspace is None:
    st.session_state.page = "workspace"

match st.session_state.page:
    case "workspace":
        workspace.show()
    case "task_list":
        task_list.show()
    case "task_detail":
        task_detail.show()
    case "analytics":
        analytics.show()
    case _:
        st.session_state.page = "workspace"
        st.rerun()
