import asyncio
import os
import time

import httpx
from fastapi import HTTPException, status

from app.models import JenkinsBuildStatus

JENKINS_URL = os.environ.get("JENKINS_URL", "http://localhost:8080").rstrip("/")
JENKINS_USER = os.environ.get("JENKINS_USER")
JENKINS_API_TOKEN = os.environ.get("JENKINS_API_TOKEN")

JENKINS_JOB_PATH = "job/my-cli"

POLL_INTERVAL_SECONDS = 1.5
POLL_TIMEOUT_SECONDS = 30.0


def _auth() -> tuple[str, str]:
    if not JENKINS_USER or not JENKINS_API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JENKINS_USER and JENKINS_API_TOKEN must be set",
        )
    return JENKINS_USER, JENKINS_API_TOKEN


async def _get_crumb_headers(client: httpx.AsyncClient) -> dict[str, str]:
    try:
        resp = await client.get(f"{JENKINS_URL}/crumbIssuer/api/json", auth=_auth())
    except httpx.RequestError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Could not reach Jenkins: {exc}") from exc

    if resp.status_code == 404:
        return {}  # crumb protection disabled on this Jenkins instance

    resp.raise_for_status()
    data = resp.json()
    return {data["crumbRequestField"]: data["crumb"]}


async def _trigger_build(client: httpx.AsyncClient, headers: dict[str, str]) -> str:
    try:
        resp = await client.post(
            f"{JENKINS_URL}/{JENKINS_JOB_PATH}/build",
            auth=_auth(),
            headers=headers,
        )
    except httpx.RequestError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Could not reach Jenkins: {exc}") from exc

    if resp.status_code != 201:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"Jenkins returned {resp.status_code} triggering the build",
        )

    location = resp.headers.get("Location")
    if not location:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Jenkins did not return a queue item URL")
    return location.rstrip("/") + "/"


async def _poll_queue_item(client: httpx.AsyncClient, queue_url: str) -> str:
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    while True:
        try:
            resp = await client.get(f"{queue_url}api/json", auth=_auth())
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Error polling Jenkins queue: {exc}") from exc

        data = resp.json()
        if data.get("cancelled"):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Jenkins build was cancelled while queued")

        executable = data.get("executable")
        if executable and executable.get("url"):
            return executable["url"]

        if time.monotonic() >= deadline:
            raise HTTPException(
                status.HTTP_504_GATEWAY_TIMEOUT,
                f"Timed out waiting for Jenkins to start the build; check {queue_url}",
            )

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def trigger_build_and_wait() -> str:
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = await _get_crumb_headers(client)
        queue_url = await _trigger_build(client, headers)
        return await _poll_queue_item(client, queue_url)


async def get_build_status(number: int) -> JenkinsBuildStatus:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{JENKINS_URL}/{JENKINS_JOB_PATH}/{number}/api/json", auth=_auth())
        except httpx.RequestError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Could not reach Jenkins: {exc}") from exc

        if resp.status_code == 404:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Build {number} not found")

        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY, f"Jenkins returned {resp.status_code} fetching build {number}"
            ) from exc

        data = resp.json()
        return JenkinsBuildStatus(
            number=data["number"],
            url=data["url"],
            building=data["building"],
            result=data.get("result"),
        )
