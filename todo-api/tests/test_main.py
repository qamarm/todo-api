from fastapi.testclient import TestClient

from app.jenkins import get_build_status, trigger_build_and_wait
from app.main import app, get_jenkins_status_fetcher, get_jenkins_trigger

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_get_jenkins_trigger_returns_default_implementation():
    assert get_jenkins_trigger() is trigger_build_and_wait


def test_get_jenkins_status_fetcher_returns_default_implementation():
    assert get_jenkins_status_fetcher() is get_build_status
