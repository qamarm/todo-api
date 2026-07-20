import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_todo(client: TestClient):
    resp = client.post("/todos", json={"title": "Buy milk"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Buy milk"
    assert data["completed"] is False
    assert data["id"] == 1


def test_list_todos_empty(client: TestClient):
    resp = client.get("/todos")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_todos_returns_created(client: TestClient):
    client.post("/todos", json={"title": "A"})
    client.post("/todos", json={"title": "B"})
    resp = client.get("/todos")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_todo(client: TestClient):
    created = client.post("/todos", json={"title": "Walk dog"}).json()
    resp = client.get(f"/todos/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Walk dog"


def test_get_todo_not_found(client: TestClient):
    resp = client.get("/todos/999")
    assert resp.status_code == 404


def test_update_todo(client: TestClient):
    created = client.post("/todos", json={"title": "Read book"}).json()
    resp = client.patch(f"/todos/{created['id']}", json={"completed": True})
    assert resp.status_code == 200
    assert resp.json()["completed"] is True
    assert resp.json()["title"] == "Read book"


def test_update_todo_not_found(client: TestClient):
    resp = client.patch("/todos/999", json={"completed": True})
    assert resp.status_code == 404


def test_delete_todo(client: TestClient):
    created = client.post("/todos", json={"title": "Temp"}).json()
    resp = client.delete(f"/todos/{created['id']}")
    assert resp.status_code == 204
    resp = client.get(f"/todos/{created['id']}")
    assert resp.status_code == 404


def test_delete_todo_not_found(client: TestClient):
    resp = client.delete("/todos/999")
    assert resp.status_code == 404
