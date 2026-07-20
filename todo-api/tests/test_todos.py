import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import store

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_store():
    store._todos.clear()
    store._next_id = 1


def test_create_todo():
    resp = client.post("/todos", json={"title": "Buy milk"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Buy milk"
    assert data["completed"] is False
    assert data["id"] == 1


def test_list_todos_empty():
    resp = client.get("/todos")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_todos_returns_created():
    client.post("/todos", json={"title": "A"})
    client.post("/todos", json={"title": "B"})
    resp = client.get("/todos")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_todo():
    created = client.post("/todos", json={"title": "Walk dog"}).json()
    resp = client.get(f"/todos/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Walk dog"


def test_get_todo_not_found():
    resp = client.get("/todos/999")
    assert resp.status_code == 404


def test_update_todo():
    created = client.post("/todos", json={"title": "Read book"}).json()
    resp = client.patch(f"/todos/{created['id']}", json={"completed": True})
    assert resp.status_code == 200
    assert resp.json()["completed"] is True
    assert resp.json()["title"] == "Read book"


def test_update_todo_not_found():
    resp = client.patch("/todos/999", json={"completed": True})
    assert resp.status_code == 404


def test_delete_todo():
    created = client.post("/todos", json={"title": "Temp"}).json()
    resp = client.delete(f"/todos/{created['id']}")
    assert resp.status_code == 204
    resp = client.get(f"/todos/{created['id']}")
    assert resp.status_code == 404


def test_delete_todo_not_found():
    resp = client.delete("/todos/999")
    assert resp.status_code == 404
