from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app, get_jenkins_trigger

client = TestClient(app)


def test_trigger_jenkins_build_returns_build_url():
    async def fake_trigger() -> str:
        return "http://localhost:8080/job/my-cli/7/"

    app.dependency_overrides[get_jenkins_trigger] = lambda: fake_trigger
    try:
        resp = client.post("/jenkins/builds")
    finally:
        app.dependency_overrides.pop(get_jenkins_trigger, None)

    assert resp.status_code == 201
    assert resp.json() == {"build_url": "http://localhost:8080/job/my-cli/7/"}


def test_trigger_jenkins_build_propagates_errors():
    async def fake_trigger() -> str:
        raise HTTPException(status_code=504, detail="timed out")

    app.dependency_overrides[get_jenkins_trigger] = lambda: fake_trigger
    try:
        resp = client.post("/jenkins/builds")
    finally:
        app.dependency_overrides.pop(get_jenkins_trigger, None)

    assert resp.status_code == 504
    assert resp.json() == {"detail": "timed out"}
