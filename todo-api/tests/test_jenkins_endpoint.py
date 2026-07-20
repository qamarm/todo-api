from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app, get_jenkins_status_fetcher, get_jenkins_trigger
from app.models import JenkinsBuildStatus

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


def test_get_jenkins_build_returns_status():
    async def fake_fetch_status(number: int) -> JenkinsBuildStatus:
        assert number == 7
        return JenkinsBuildStatus(
            number=7, url="http://localhost:8080/job/my-cli/7/", building=False, result="SUCCESS"
        )

    app.dependency_overrides[get_jenkins_status_fetcher] = lambda: fake_fetch_status
    try:
        resp = client.get("/jenkins/builds/7")
    finally:
        app.dependency_overrides.pop(get_jenkins_status_fetcher, None)

    assert resp.status_code == 200
    assert resp.json() == {
        "number": 7,
        "url": "http://localhost:8080/job/my-cli/7/",
        "building": False,
        "result": "SUCCESS",
    }


def test_get_jenkins_build_not_found():
    async def fake_fetch_status(number: int) -> JenkinsBuildStatus:
        raise HTTPException(status_code=404, detail=f"Build {number} not found")

    app.dependency_overrides[get_jenkins_status_fetcher] = lambda: fake_fetch_status
    try:
        resp = client.get("/jenkins/builds/999")
    finally:
        app.dependency_overrides.pop(get_jenkins_status_fetcher, None)

    assert resp.status_code == 404
