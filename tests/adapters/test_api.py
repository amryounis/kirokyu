"""Integration tests for the FastAPI REST adapter."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from kirokyu.adapters.api.app import app, get_use_cases
from kirokyu.bootstrap import build_use_cases


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    uc = build_use_cases(adapter="memory")
    app.dependency_overrides[get_use_cases] = lambda: uc
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /tasks
# ---------------------------------------------------------------------------


def test_create_task_returns_201(client: TestClient):
    response = client.post("/tasks", json={"title": "Buy milk"})
    assert response.status_code == 201


def test_create_task_body_has_expected_fields(client: TestClient):
    response = client.post("/tasks", json={"title": "Buy milk"})
    body = response.json()
    assert body["title"] == "Buy milk"
    assert body["status"] == "pending"
    assert "id" in body


def test_create_task_default_priority_is_medium(client: TestClient):
    response = client.post("/tasks", json={"title": "Plain task"})
    assert response.json()["priority"] == "medium"


def test_create_task_blank_title_returns_422(client: TestClient):
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 422


def test_create_task_missing_title_returns_422(client: TestClient):
    response = client.post("/tasks", json={})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /tasks
# ---------------------------------------------------------------------------


def test_list_tasks_empty(client: TestClient):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_returns_created_tasks(client: TestClient):
    client.post("/tasks", json={"title": "Task A"})
    client.post("/tasks", json={"title": "Task B"})
    response = client.get("/tasks")
    titles = [t["title"] for t in response.json()]
    assert "Task A" in titles
    assert "Task B" in titles


# ---------------------------------------------------------------------------
# GET /tasks/{id}
# ---------------------------------------------------------------------------


def test_get_task_returns_task(client: TestClient):
    task_id = client.post("/tasks", json={"title": "Specific"}).json()["id"]
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Specific"


def test_get_task_unknown_id_returns_404(client: TestClient):
    response = client.get("/tasks/00000000-0000-0000-0000-000000000099")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /tasks/{id}
# ---------------------------------------------------------------------------


def test_update_task_title(client: TestClient):
    task_id = client.post("/tasks", json={"title": "Old title"}).json()["id"]
    response = client.patch(f"/tasks/{task_id}", json={"title": "New title"})
    assert response.status_code == 200
    assert response.json()["title"] == "New title"


def test_update_unknown_task_returns_404(client: TestClient):
    response = client.patch(
        "/tasks/00000000-0000-0000-0000-000000000099",
        json={"title": "Doesn't matter"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /tasks/{id}/complete and /uncomplete
# ---------------------------------------------------------------------------


def test_complete_task(client: TestClient):
    task_id = client.post("/tasks", json={"title": "To complete"}).json()["id"]
    response = client.post(f"/tasks/{task_id}/complete")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_uncomplete_task(client: TestClient):
    task_id = client.post("/tasks", json={"title": "Done"}).json()["id"]
    client.post(f"/tasks/{task_id}/complete")
    response = client.post(f"/tasks/{task_id}/uncomplete")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_complete_unknown_task_returns_404(client: TestClient):
    response = client.post("/tasks/00000000-0000-0000-0000-000000000099/complete")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /tasks/{id}/archive and /unarchive
# ---------------------------------------------------------------------------


def test_archive_task(client: TestClient):
    task_id = client.post("/tasks", json={"title": "Old task"}).json()["id"]
    response = client.post(f"/tasks/{task_id}/archive")
    assert response.status_code == 200
    assert response.json()["status"] == "archived"


def test_unarchive_task(client: TestClient):
    task_id = client.post("/tasks", json={"title": "Old task"}).json()["id"]
    client.post(f"/tasks/{task_id}/archive")
    response = client.post(f"/tasks/{task_id}/unarchive")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


# ---------------------------------------------------------------------------
# DELETE /tasks/{id}
# ---------------------------------------------------------------------------


def test_delete_task_returns_204(client: TestClient):
    task_id = client.post("/tasks", json={"title": "To delete"}).json()["id"]
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204


def test_deleted_task_is_gone(client: TestClient):
    task_id = client.post("/tasks", json={"title": "Temporary"}).json()["id"]
    client.delete(f"/tasks/{task_id}")
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404


def test_delete_unknown_task_returns_404(client: TestClient):
    response = client.delete("/tasks/00000000-0000-0000-0000-000000000099")
    assert response.status_code == 404
