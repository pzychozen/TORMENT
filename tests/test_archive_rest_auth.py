"""Security regression tests for archive REST endpoint authentication."""
from __future__ import annotations

import importlib
import os
from typing import Iterator

import pytest
from fastapi.testclient import TestClient


API_KEY = "sk-archive-rest-test"
WORKSPACE_ID = "ws_archive_auth"
AGENT_ID = "ag_archive_auth"
DOC_ID = "doc_archive_auth"
DOC_TEXT = "Archive auth regression document with searchable storage notes."


def _client_with_env(tmp_path, *, auth_enabled: bool) -> Iterator[TestClient]:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    env_keys = [
        "TORMENT_DATA_DIR",
        "TORMENT_AUTH_ENABLE",
        "TORMENT_API_KEYS",
        "TORMENT_API_KEYS_FILE",
        "TORMENT_EMBED_PROVIDER",
    ]
    original_env = {key: os.environ.get(key) for key in env_keys}

    os.environ["TORMENT_DATA_DIR"] = str(data_dir)
    os.environ["TORMENT_AUTH_ENABLE"] = "1" if auth_enabled else "0"
    os.environ["TORMENT_API_KEYS"] = f"{API_KEY}:archive-test-client:1.0"
    os.environ.pop("TORMENT_API_KEYS_FILE", None)
    os.environ["TORMENT_EMBED_PROVIDER"] = "hash"

    import torment_service.auth as authmod
    import torment_service.app as appmod

    authmod = importlib.reload(authmod)
    appmod = importlib.reload(appmod)
    client = TestClient(appmod.app)
    try:
        yield client
    finally:
        client.close()
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        importlib.reload(authmod)
        importlib.reload(appmod)


@pytest.fixture()
def auth_client(tmp_path) -> Iterator[TestClient]:
    yield from _client_with_env(tmp_path, auth_enabled=True)


@pytest.fixture()
def no_auth_client(tmp_path) -> Iterator[TestClient]:
    yield from _client_with_env(tmp_path, auth_enabled=False)


def _auth_headers() -> dict[str, str]:
    return {"X-API-Key": API_KEY}


def _ingest(client: TestClient, *, headers: dict[str, str] | None = None):
    return client.post(
        "/archive/ingest_document",
        json={
            "workspace_id": WORKSPACE_ID,
            "agent_id": AGENT_ID,
            "text": DOC_TEXT,
            "title": "Archive Auth",
            "doc_id": DOC_ID,
        },
        headers=headers,
    )


def _query(client: TestClient, *, headers: dict[str, str] | None = None):
    return client.post(
        "/archive/query",
        json={
            "workspace_id": WORKSPACE_ID,
            "agent_id": AGENT_ID,
            "query": "searchable storage notes",
            "top_k": 3,
            "min_score": -1.0,
        },
        headers=headers,
    )


def _list(client: TestClient, *, headers: dict[str, str] | None = None):
    return client.get(
        f"/archive/{WORKSPACE_ID}/{AGENT_ID}/documents",
        headers=headers,
    )


def _read(client: TestClient, *, headers: dict[str, str] | None = None):
    return client.get(
        f"/archive/{WORKSPACE_ID}/{AGENT_ID}/document/{DOC_ID}",
        headers=headers,
    )


def _delete(client: TestClient, *, headers: dict[str, str] | None = None):
    return client.delete(
        f"/archive/{WORKSPACE_ID}/{AGENT_ID}/document/{DOC_ID}",
        headers=headers,
    )


def test_archive_endpoints_reject_missing_auth_when_auth_enabled(auth_client: TestClient):
    for response in (
        _ingest(auth_client),
        _query(auth_client),
        _list(auth_client),
        _read(auth_client),
        _delete(auth_client),
    ):
        assert response.status_code == 401, response.text


def test_spine_submit_task_still_rejects_missing_auth_when_auth_enabled(
    auth_client: TestClient,
):
    response = auth_client.post(
        "/spine/submit_task",
        json={
            "workspace_id": WORKSPACE_ID,
            "agent_id": AGENT_ID,
            "operation": "query",
            "payload": {},
            "mode": "auto",
        },
    )

    assert response.status_code == 401, response.text


def test_archive_endpoints_accept_configured_api_key(auth_client: TestClient):
    headers = _auth_headers()

    response = _ingest(auth_client, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["doc_id"] == DOC_ID
    assert response.json()["chunk_count"] >= 1

    response = _list(auth_client, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["count"] == 1
    assert response.json()["documents"][0]["doc_id"] == DOC_ID

    response = _read(auth_client, headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["document"]["doc_id"] == DOC_ID
    assert len(body["chunks"]) >= 1

    response = _query(auth_client, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["count"] >= 1
    assert response.json()["results"][0]["doc_id"] == DOC_ID

    response = _delete(auth_client, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == {"deleted": True, "doc_id": DOC_ID}


def test_archive_endpoints_allow_local_no_auth_mode(no_auth_client: TestClient):
    response = _ingest(no_auth_client)
    assert response.status_code == 200, response.text

    response = _list(no_auth_client)
    assert response.status_code == 200, response.text
    assert response.json()["count"] == 1

    response = _read(no_auth_client)
    assert response.status_code == 200, response.text
    assert response.json()["document"]["doc_id"] == DOC_ID

    response = _query(no_auth_client)
    assert response.status_code == 200, response.text
    assert response.json()["count"] >= 1

    response = _delete(no_auth_client)
    assert response.status_code == 200, response.text
