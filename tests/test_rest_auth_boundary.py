"""Security regression tests for the systemic REST authentication boundary."""
from __future__ import annotations

import importlib
import os
import re
from typing import Iterator

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient


API_KEY = "sk-rest-boundary-test"
WORKSPACE_ID = "ws_rest_auth"
AGENT_ID = "ag_rest_auth"
DOC_ID = "doc_rest_auth"

APP_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
EXPECTED_PUBLIC_SAFE_ROUTES = frozenset(
    {
        ("GET", "/retrieve/profiles"),
        ("GET", "/thinking/debug/geo_profiles"),
    }
)
PATH_VALUES = {
    "workspace_id": WORKSPACE_ID,
    "agent_id": AGENT_ID,
    "domain_id": "personal",
    "event_id": "event_rest_auth",
    "job_id": "job_rest_auth",
    "doc_id": DOC_ID,
    "motif_id": "motif_rest_auth",
}


def _client_with_env(tmp_path, *, auth_enabled: bool) -> Iterator[tuple[TestClient, object]]:
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
    os.environ["TORMENT_API_KEYS"] = f"{API_KEY}:rest-boundary-test-client:1.0"
    os.environ.pop("TORMENT_API_KEYS_FILE", None)
    os.environ["TORMENT_EMBED_PROVIDER"] = "hash"

    import torment_service.auth as authmod
    import torment_service.app as appmod

    authmod = importlib.reload(authmod)
    appmod = importlib.reload(appmod)
    client = TestClient(appmod.app)
    try:
        yield client, appmod
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
def auth_client(tmp_path) -> Iterator[tuple[TestClient, object]]:
    yield from _client_with_env(tmp_path, auth_enabled=True)


@pytest.fixture()
def no_auth_client(tmp_path) -> Iterator[tuple[TestClient, object]]:
    yield from _client_with_env(tmp_path, auth_enabled=False)


def _auth_headers() -> dict[str, str]:
    return {"X-API-Key": API_KEY}


def _concrete_path(path: str) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1).split(":", 1)[0]
        return PATH_VALUES.get(key, f"{key}_rest_auth")

    return re.sub(r"{([^}]+)}", repl, path)


def _app_routes(appmod) -> list[tuple[str, str, str]]:
    routes: list[tuple[str, str, str]] = []
    for route in appmod.app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in sorted(set(route.methods or ()) & APP_HTTP_METHODS):
            routes.append((method, route.path, route.name))
    return routes


def test_public_safe_allowlist_is_explicit_and_small(auth_client):
    _client, appmod = auth_client

    assert appmod.PUBLIC_SAFE_REST_ROUTES == EXPECTED_PUBLIC_SAFE_ROUTES


def test_auth_enabled_rejects_missing_key_on_every_non_public_app_route(auth_client):
    client, appmod = auth_client
    failures = []

    for method, path, handler in _app_routes(appmod):
        if (method, path) in appmod.PUBLIC_SAFE_REST_ROUTES:
            continue
        response = client.request(method, _concrete_path(path))
        if response.status_code != 401:
            failures.append(
                f"{method} {path} ({handler}) -> {response.status_code}: {response.text[:160]}"
            )

    assert not failures, "\n".join(failures)


def test_public_safe_routes_remain_available_without_key_when_auth_enabled(auth_client):
    client, _appmod = auth_client

    for method, path in EXPECTED_PUBLIC_SAFE_ROUTES:
        response = client.request(method, path)
        assert response.status_code == 200, response.text


def test_docs_and_openapi_are_not_accidentally_public_when_auth_enabled(auth_client):
    client, _appmod = auth_client

    for path in ("/docs", "/openapi.json", "/redoc"):
        response = client.get(path)
        assert response.status_code == 401, response.text


def test_invalid_key_rejected_before_sensitive_handler(auth_client):
    client, _appmod = auth_client

    response = client.get("/health", headers={"X-API-Key": "sk-invalid"})

    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "Invalid API key."


def test_valid_header_and_query_api_keys_reach_sensitive_handler(auth_client):
    client, _appmod = auth_client

    header_response = client.get("/health", headers=_auth_headers())
    query_response = client.get(f"/health?api_key={API_KEY}")

    assert header_response.status_code == 200, header_response.text
    assert query_response.status_code == 200, query_response.text
    assert header_response.json()["ok"] is True
    assert query_response.json()["ok"] is True


@pytest.mark.parametrize(
    "method,path,kwargs,expected_valid_statuses",
    [
        (
            "POST",
            "/retrieve",
            {
                "json": {
                    "workspace_id": WORKSPACE_ID,
                    "agent_id": AGENT_ID,
                    "query": "auth boundary retrieve probe",
                }
            },
            {200},
        ),
        (
            "POST",
            "/promote",
            {
                "json": {
                    "workspace_id": WORKSPACE_ID,
                    "agent_id": AGENT_ID,
                    "chunk_id": "missing_chunk",
                }
            },
            {404},
        ),
        ("GET", f"/promote/suggestions/{WORKSPACE_ID}/{AGENT_ID}", {}, {200}),
        (
            "POST",
            "/agent/query",
            {
                "json": {
                    "workspace_id": WORKSPACE_ID,
                    "agent_id": AGENT_ID,
                    "query": "auth boundary query probe",
                    "top_k": 1,
                }
            },
            {200},
        ),
        ("GET", "/debug/provenance", {}, {200}),
        (
            "POST",
            "/workspace/create",
            {"json": {"workspace_id": "ws_rest_auth_create", "domains": ["personal"]}},
            {200},
        ),
    ],
)
def test_known_sensitive_routes_require_auth_and_accept_valid_key(
    auth_client,
    method: str,
    path: str,
    kwargs: dict,
    expected_valid_statuses: set[int],
):
    client, _appmod = auth_client

    missing = client.request(method, path, **kwargs)
    invalid = client.request(method, path, headers={"X-API-Key": "sk-invalid"}, **kwargs)
    valid = client.request(method, path, headers=_auth_headers(), **kwargs)

    assert missing.status_code == 401, missing.text
    assert invalid.status_code == 401, invalid.text
    assert valid.status_code in expected_valid_statuses, valid.text


def test_auth_disabled_preserves_local_no_auth_behavior(no_auth_client):
    client, _appmod = no_auth_client

    health = client.get("/health")
    create = client.post(
        "/workspace/create",
        json={"workspace_id": "ws_no_auth_boundary", "domains": ["personal"]},
    )
    query = client.post(
        "/agent/query",
        json={
            "workspace_id": "ws_no_auth_boundary",
            "agent_id": "ag_no_auth_boundary",
            "query": "local no auth query",
            "top_k": 1,
        },
    )

    assert health.status_code == 200, health.text
    assert create.status_code == 200, create.text
    assert query.status_code == 200, query.text
