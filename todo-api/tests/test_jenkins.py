import asyncio

import httpx
import pytest
import respx

from app import jenkins


@pytest.fixture(autouse=True)
def jenkins_credentials(monkeypatch):
    monkeypatch.setattr(jenkins, "JENKINS_USER", "alice")
    monkeypatch.setattr(jenkins, "JENKINS_API_TOKEN", "token123")


QUEUE_URL = f"{jenkins.JENKINS_URL}/queue/item/42/"
BUILD_URL = f"{jenkins.JENKINS_URL}/job/my-cli/7/"


def test_trigger_build_and_wait_returns_build_url():
    with respx.mock:
        respx.get(f"{jenkins.JENKINS_URL}/crumbIssuer/api/json").mock(
            return_value=httpx.Response(200, json={"crumbRequestField": "Jenkins-Crumb", "crumb": "abc123"})
        )
        build_route = respx.post(f"{jenkins.JENKINS_URL}/{jenkins.JENKINS_JOB_PATH}/build").mock(
            return_value=httpx.Response(201, headers={"Location": QUEUE_URL})
        )
        respx.get(f"{QUEUE_URL}api/json").mock(
            return_value=httpx.Response(200, json={"executable": {"number": 7, "url": BUILD_URL}})
        )

        build_url = asyncio.run(jenkins.trigger_build_and_wait())

    assert build_url == BUILD_URL
    assert build_route.calls[0].request.headers["Jenkins-Crumb"] == "abc123"


def test_trigger_build_skips_crumb_when_disabled():
    with respx.mock:
        respx.get(f"{jenkins.JENKINS_URL}/crumbIssuer/api/json").mock(return_value=httpx.Response(404))
        build_route = respx.post(f"{jenkins.JENKINS_URL}/{jenkins.JENKINS_JOB_PATH}/build").mock(
            return_value=httpx.Response(201, headers={"Location": QUEUE_URL})
        )
        respx.get(f"{QUEUE_URL}api/json").mock(
            return_value=httpx.Response(200, json={"executable": {"number": 7, "url": BUILD_URL}})
        )

        build_url = asyncio.run(jenkins.trigger_build_and_wait())

    assert build_url == BUILD_URL
    assert "Jenkins-Crumb" not in build_route.calls[0].request.headers


def test_poll_queue_item_waits_until_executable():
    with respx.mock:
        respx.get(f"{QUEUE_URL}api/json").mock(
            side_effect=[
                httpx.Response(200, json={"why": "waiting for executor"}),
                httpx.Response(200, json={"executable": {"number": 7, "url": BUILD_URL}}),
            ]
        )

        async def run():
            async with httpx.AsyncClient() as client:
                return await jenkins._poll_queue_item(client, QUEUE_URL)

        original_interval = jenkins.POLL_INTERVAL_SECONDS
        jenkins.POLL_INTERVAL_SECONDS = 0.01
        try:
            build_url = asyncio.run(run())
        finally:
            jenkins.POLL_INTERVAL_SECONDS = original_interval

    assert build_url == BUILD_URL


def test_poll_queue_item_raises_on_cancelled():
    with respx.mock:
        respx.get(f"{QUEUE_URL}api/json").mock(return_value=httpx.Response(200, json={"cancelled": True}))

        async def run():
            async with httpx.AsyncClient() as client:
                return await jenkins._poll_queue_item(client, QUEUE_URL)

        with pytest.raises(Exception) as exc_info:
            asyncio.run(run())

    assert exc_info.value.status_code == 502


def test_poll_queue_item_times_out():
    with respx.mock:
        respx.get(f"{QUEUE_URL}api/json").mock(return_value=httpx.Response(200, json={"why": "still waiting"}))

        async def run():
            async with httpx.AsyncClient() as client:
                return await jenkins._poll_queue_item(client, QUEUE_URL)

        original_timeout = jenkins.POLL_TIMEOUT_SECONDS
        original_interval = jenkins.POLL_INTERVAL_SECONDS
        jenkins.POLL_TIMEOUT_SECONDS = 0.02
        jenkins.POLL_INTERVAL_SECONDS = 0.01
        try:
            with pytest.raises(Exception) as exc_info:
                asyncio.run(run())
        finally:
            jenkins.POLL_TIMEOUT_SECONDS = original_timeout
            jenkins.POLL_INTERVAL_SECONDS = original_interval

    assert exc_info.value.status_code == 504


def test_missing_credentials_raises(monkeypatch):
    monkeypatch.setattr(jenkins, "JENKINS_USER", None)

    with pytest.raises(Exception) as exc_info:
        asyncio.run(jenkins.trigger_build_and_wait())

    assert exc_info.value.status_code == 500
