"""S-1 — the REST API key is accepted via the X-API-Key header only.

The former ``?api_key=<secret>`` query-string transport is retired on purpose: uvicorn's
default access log records the request line, so a query-form key was written to the
service log (and to browser history / proxy logs).  Everything else about the
authentication boundary is unchanged and pinned here:

  * valid X-API-Key header -> admitted;
  * query-only key -> 401, and the response never echoes the supplied secret;
  * header + query -> the valid header wins and the request is admitted;
  * explicit ``resolve_request_context(..., api_key=<key>)`` remains supported;
  * invalid header -> 401 "Invalid API key.";
  * missing key -> 401 "Missing API key. Provide X-API-Key header.";
  * auth disabled -> the established operator context, no key consulted;
  * public-safe routes stay reachable without a key; trailing-slash normalisation
    of the auth boundary unchanged.
"""
from __future__ import annotations

import importlib
import os
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from conftest import _is_repo_default, assert_legacy_mode, existing_legacy_root, safe_run_data_root

API_KEY = "sk-header-only-test"
LOW_TRUST_API_KEY = "sk-header-only-low"
SENSITIVE = "/health"                 # auth-required read, native-classified
PUBLIC_SAFE = "/retrieve/profiles"    # in PUBLIC_SAFE_REST_ROUTES
MISSING_DETAIL = "Missing API key. Provide X-API-Key header."
INVALID_DETAIL = "Invalid API key."


def _client_with_env(tmp_path, *, auth_enabled: bool) -> Iterator[tuple[TestClient, object, object]]:
    safe_run_data_root()
    data_dir = existing_legacy_root(tmp_path / "data")  # I11: empty roots are refused
    env_keys = ["TORMENT_DATA_DIR", "TORMENT_AUTH_ENABLE", "TORMENT_API_KEYS", "TORMENT_API_KEYS_FILE",
                "TORMENT_ARCHIVIST_WRITEBACK", "TORMENT_EMBED_PROVIDER"]
    original_env = {key: os.environ.get(key) for key in env_keys}
    os.environ["TORMENT_DATA_DIR"] = str(data_dir)
    os.environ["TORMENT_AUTH_ENABLE"] = "1" if auth_enabled else "0"
    os.environ["TORMENT_API_KEYS"] = f"{LOW_TRUST_API_KEY}:header-only-low:0.0,{API_KEY}:header-only-client:1.0"
    os.environ.pop("TORMENT_API_KEYS_FILE", None)
    os.environ["TORMENT_ARCHIVIST_WRITEBACK"] = "0"
    os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
    authmod = appmod = None
    try:
        import torment_service.auth as authmod
        import torment_service.app as appmod
        authmod = importlib.reload(authmod)
        appmod = importlib.reload(appmod)
        with TestClient(appmod.app) as client:
            assert_legacy_mode(appmod)
            yield client, appmod, authmod
    finally:
        try:
            from torment_service.public_runtime import reset_public_runtime_for_test
            reset_public_runtime_for_test(data_dir)
        finally:
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            if authmod is not None:
                importlib.reload(authmod)
            if appmod is not None and not _is_repo_default(os.environ.get("TORMENT_DATA_DIR")):
                importlib.reload(appmod)


@pytest.fixture()
def auth_client(tmp_path):
    yield from _client_with_env(tmp_path, auth_enabled=True)


@pytest.fixture()
def no_auth_client(tmp_path):
    yield from _client_with_env(tmp_path, auth_enabled=False)


def _bare_request(path: str = SENSITIVE, query: bytes = b"") -> Request:
    return Request({"type": "http", "method": "GET", "path": path, "headers": [], "query_string": query})


# ---------------------------------------------------------------- transport
def test_valid_header_is_accepted(auth_client):
    client, _, _ = auth_client
    response = client.get(SENSITIVE, headers={"X-API-Key": API_KEY})
    assert response.status_code == 200, response.text
    assert response.json()["ok"] is True


def test_query_only_key_is_rejected_and_not_echoed(auth_client):
    client, _, _ = auth_client
    response = client.get(SENSITIVE, params={"api_key": API_KEY})
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": MISSING_DETAIL}
    assert API_KEY not in response.text
    assert API_KEY not in str(response.headers)


def test_header_plus_query_is_admitted_by_the_header(auth_client):
    client, _, _ = auth_client
    # the query value is ignored entirely: a bogus query value cannot taint a valid header
    response = client.get(SENSITIVE, headers={"X-API-Key": API_KEY}, params={"api_key": "sk-bogus"})
    assert response.status_code == 200, response.text
    assert response.json()["ok"] is True
    # and a valid query value cannot rescue an invalid header
    response = client.get(SENSITIVE, headers={"X-API-Key": "sk-bogus"}, params={"api_key": API_KEY})
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": INVALID_DETAIL}
    assert API_KEY not in response.text


def test_explicit_api_key_argument_remains_supported(auth_client):
    _, _, authmod = auth_client
    ctx = authmod.resolve_request_context(_bare_request(), api_key=API_KEY)
    assert (ctx.client_id, ctx.trust_tier) == ("header-only-client", 1.0)
    low = authmod.resolve_request_context(_bare_request(), workspace_id="ws", agent_id="ag", api_key=LOW_TRUST_API_KEY)
    assert (low.client_id, low.trust_tier, low.workspace_id, low.agent_id) == ("header-only-low", 0.0, "ws", "ag")
    # the explicit argument outranks a conflicting header, exactly as before
    scope = {"type": "http", "method": "GET", "path": SENSITIVE,
             "headers": [(b"x-api-key", LOW_TRUST_API_KEY.encode())], "query_string": b""}
    ctx = authmod.resolve_request_context(Request(scope), api_key=API_KEY)
    assert ctx.client_id == "header-only-client"
    # a query string alone no longer resolves anything for the direct call either
    with pytest.raises(Exception) as excinfo:
        authmod.resolve_request_context(_bare_request(query=f"api_key={API_KEY}".encode()))
    assert getattr(excinfo.value, "status_code", None) == 401
    assert getattr(excinfo.value, "detail", None) == MISSING_DETAIL


def test_invalid_header_is_rejected_with_the_established_detail(auth_client):
    client, _, _ = auth_client
    response = client.get(SENSITIVE, headers={"X-API-Key": "sk-not-a-key"})
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": INVALID_DETAIL}


def test_missing_key_detail_names_the_header_only(auth_client):
    client, _, _ = auth_client
    response = client.get(SENSITIVE)
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": MISSING_DETAIL}
    assert "api_key" not in response.json()["detail"]


# ---------------------------------------------------------------- unchanged surroundings
def test_auth_disabled_keeps_the_operator_context_without_consulting_any_key(no_auth_client):
    client, _, authmod = no_auth_client
    assert authmod.AUTH_ENABLED is False
    assert client.get(SENSITIVE).status_code == 200
    assert client.get(SENSITIVE, params={"api_key": "anything"}).status_code == 200
    ctx = authmod.resolve_request_context(_bare_request(query=b"api_key=anything"))
    assert (ctx.client_id, ctx.trust_tier) == (authmod._DEFAULT_CLIENT_ID, authmod.TRUST_OPERATOR)


def test_public_safe_routes_and_trailing_slash_boundary_are_unchanged(auth_client):
    client, appmod, _ = auth_client
    assert appmod.PUBLIC_SAFE_REST_ROUTES == frozenset({("GET", "/retrieve/profiles"), ("GET", "/thinking/debug/geo_profiles")})
    assert client.get(PUBLIC_SAFE).status_code == 200
    assert client.get(PUBLIC_SAFE + "/").status_code == 200           # normalised to the public-safe route
    assert client.get(SENSITIVE + "/").status_code == 401             # normalised sensitive route still needs the key
    assert client.get(SENSITIVE + "/", headers={"X-API-Key": API_KEY}).status_code == 200
    assert appmod.is_public_safe_rest_route("GET", "/retrieve/profiles/") is True
    assert appmod.is_public_safe_rest_route("GET", "/health") is False
