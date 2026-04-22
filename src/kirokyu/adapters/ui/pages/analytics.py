"""Analytics dashboard page."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from kirokyu.analytics.queries import AnalyticsQueries
from kirokyu.workspaces.registry import WorkspaceRegistry


def _get_db_path() -> str | None:
    workspace_name = st.session_state.get("workspace")
    if not workspace_name:
        return None
    registry = WorkspaceRegistry()
    ws = registry.get(workspace_name)
    return ws.db_path if ws else None


def show() -> None:
    """Render the analytics dashboard page."""
    st.title("Analytics")

    db_path = _get_db_path()
    if not db_path:
        st.error("No workspace selected.")
        return

    queries = AnalyticsQueries(db_path)

    st.divider()

    # ------------------------------------------------------------------
    # Completion rate
    # ------------------------------------------------------------------
    st.subheader("Completion rate")

    period = st.radio(
        "Period",
        ["All time", "This month", "This week"],
        horizontal=True,
        label_visibility="collapsed",
    )

    since: date | None = None
    today = date.today()
    if period == "This month":
        since = today.replace(day=1)
    elif period == "This week":
        since = today - timedelta(days=today.weekday())

    summary = queries.completion_rate(since=since)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total tasks", summary.total)
    col2.metric("Completed", summary.completed)
    col3.metric("Completion rate", f"{summary.rate}%")

    st.divider()

    # ------------------------------------------------------------------
    # Tasks by priority
    # ------------------------------------------------------------------
    st.subheader("Tasks by priority")

    priority_data = queries.tasks_by_priority()
    if priority_data:
        try:
            import plotly.graph_objects as go

            priority_colors = {
                "high": "#F44336",
                "medium": "#FF9800",
                "low": "#4CAF50",
            }
            fig = go.Figure(
                go.Bar(
                    x=[p.priority for p in priority_data],
                    y=[p.count for p in priority_data],
                    marker_color=[
                        priority_colors.get(p.priority, "#888888") for p in priority_data
                    ],
                )
            )
            fig.update_layout(
                xaxis_title="Priority",
                yaxis_title="Tasks",
                height=300,
                margin={"t": 20},
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            for p in priority_data:
                st.write(f"**{p.priority}**: {p.count}")
    else:
        st.caption("No task data yet.")

    st.divider()

    # ------------------------------------------------------------------
    # Completion trend
    # ------------------------------------------------------------------
    st.subheader("Completion trend (last 30 days)")

    trend_data = queries.completion_trend(days=30)
    if trend_data:
        try:
            import plotly.graph_objects as go

            fig = go.Figure(
                go.Scatter(
                    x=[d.day for d in trend_data],
                    y=[d.count for d in trend_data],
                    mode="lines+markers",
                    line={"color": "#2196F3"},
                )
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Tasks completed",
                height=300,
                margin={"t": 20},
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            for d in trend_data:
                st.write(f"{d.day}: {d.count}")
    else:
        st.caption("No completed tasks in the last 30 days.")

    st.divider()

    # ------------------------------------------------------------------
    # Overdue summary
    # ------------------------------------------------------------------
    st.subheader("Overdue tasks")

    overdue = queries.overdue_summary()
    if overdue:
        for bucket in overdue:
            st.warning(f"**{bucket.label}**: {bucket.count} task(s)")
    else:
        st.success("No overdue tasks.")
