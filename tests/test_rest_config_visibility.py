"""D1: named HTTP configuration values follow the resolved operator context."""
from contextlib import contextmanager
import copy
import importlib
import json
import math
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from conftest import existing_legacy_root, safe_run_data_root
from torment_service.request_context import TRUST_OPERATOR


REDACTED = "<redacted>"
SENSITIVE_FLAGS = ("TORMENT_DATA_DIR", "TORMENT_SERVER_LAUNCHER_PATH", "TORMENT_TEST_CONDITION")
TIERS = {"reader": 0.0, "reinforce": 0.3, "ingest": 0.6, "collective": 0.9,
         "almost_operator": math.nextafter(TRUST_OPERATOR, 0.0), "operator": TRUST_OPERATOR}
KEYS = {name: "synthetic-d1-key-" + name for name in TIERS}
LEGACY_TARGETS = [("/config", None), ("/debug/metrics", "present"), ("/debug/metrics", "missing")]


@pytest.fixture
def service(tmp_path, monkeypatch):
    @contextmanager
    def start(*, native=False, auth=True, empty=False):
        safe_run_data_root()
        authmod = appmod = None
        root = None
        with monkeypatch.context() as scoped:
            # Bind import-time configuration before reloading auth/app. All data,
            # keys and configuration strings belong to this disposable fixture.
            scoped.setenv("TORMENT_AUTH_ENABLE", "1" if auth else "0")
            scoped.setenv("TORMENT_API_KEYS", ",".join(
                f"{KEYS[name]}:{'operator-named-reader' if name == 'reader' else name}:{tier!r}"
                for name, tier in TIERS.items()))
            scoped.delenv("TORMENT_API_KEYS_FILE", raising=False)
            scoped.delenv("TORMENT_PROFILE", raising=False)
            scoped.setenv("TORMENT_EMBED_PROVIDER", "hash")
            scoped.setenv("TORMENT_ARCHIVIST_WRITEBACK", "0")
            scoped.setenv("TORMENT_MCP_DATA_DIR", str(tmp_path / "isolated-mcp"))
            scoped.setenv("TORMENT_TEST_CONDITION", "" if empty else "D1_PRIVATE_CONDITION_73A9")
            scoped.setenv("TORMENT_SERVER_LAUNCHER_PATH", "" if empty else "C:/D1_PRIVATE_LAUNCHER_73A9/server.cmd")
            try:
                from torment_service import public_runtime
                if native:
                    # Reuse the admitted native SQLite fixture and its deterministic
                    # embedder; no runtime/selector/HTTP-response double is used.
                    from test_b5_a3_production_native_resource_owner import _active_fixture
                    from test_b5_a4r3_public_backend_selection import (
                        _NativeLaneFabric, _configuration, _forbid_legacy_core_memory,
                        _native_counts, _prime_external_identity,
                    )
                    scoped.setattr(public_runtime, "TormentFabric", _NativeLaneFabric)
                    root, core, descriptor, profile, agreement = _active_fixture(tmp_path / "D1_PRIVATE_NATIVE_ROOT_73A9")
                    assert agreement.mode.value == "NATIVE_AGREEMENT"
                    _prime_external_identity(root)
                    legacy_calls = _forbid_legacy_core_memory(scoped)
                else:
                    root = existing_legacy_root(tmp_path / "D1_PRIVATE_LEGACY_ROOT_73A9")
                scoped.setenv("TORMENT_DATA_DIR", str(root))
                import torment_service.auth as authmod
                import torment_service.app as appmod
                importlib.reload(authmod)
                importlib.reload(appmod)
                if native:
                    appmod.configure_app_public_runtime(_configuration(root, descriptor, profile))
                # Explicit loopback peer: it must never promote lower-trust keys.
                with TestClient(appmod.app, client=("127.0.0.1", 54321)) as client:
                    runtime = appmod.fabric.runtime()
                    assert runtime.mode.value == ("NATIVE" if native else "LEGACY")
                    if native:
                        assert runtime.native_owner is not None and core.is_file()
                        before_counts = _native_counts(runtime)
                    else:
                        appmod.fabric.get_workspace("present", domains=["personal"])
                    yield SimpleNamespace(client=client, app=appmod, auth=authmod, runtime=runtime,
                                          root=root, native=native, empty=empty)
                    if native:
                        assert _native_counts(runtime) == before_counts
                        assert legacy_calls == []
            finally:
                try:
                    if root is not None:
                        public_runtime.reset_public_runtime_for_test(root)
                finally:
                    # Restore even when a deliberately failing predecessor
                    # assertion exits the context at yield.
                    scoped.undo()
                    if authmod is not None:
                        importlib.reload(authmod)
                    if appmod is not None:
                        importlib.reload(appmod)
    return start


def _request(svc, route, workspace=None, role="operator", **kwargs):
    headers = kwargs.pop("headers", {})
    if role is not None:
        headers = {"X-API-Key": KEYS[role], **headers}
    params = kwargs.pop("params", {})
    if workspace is not None:
        params = {"workspace_id": workspace, "agent_id": "synthetic-agent", **params}
    return svc.client.get(route, params=params, headers=headers, **kwargs)


def _raw_config(svc):
    return svc.app.build_config_view(active_profile=svc.app.ACTIVE_PROFILE,
        profile_applied=svc.app.PROFILE_APPLIED, profile_known=svc.app.PROFILE_KNOWN,
        data_dir=svc.app.DATA_DIR)


def _redacted(payload, route):
    expected = copy.deepcopy(payload)
    if route == "/config":
        expected["effective"]["TORMENT_DATA_DIR"]["value"] = REDACTED
    else:
        for name in SENSITIVE_FLAGS:
            expected["companion_runtime_flags"][name]["effective_value"] = REDACTED
    return expected


def _assert_no_sensitive_response(svc, response):
    # Check the entire serialized JSON, including any unrelated/error fields.
    for value in (svc.app.DATA_DIR, svc.app.SERVER_LAUNCHER_PATH, svc.app.TEST_CONDITION):
        if value:
            assert json.dumps(value)[1:-1] not in response.text
    for marker in ("D1_PRIVATE_LEGACY_ROOT_73A9", "D1_PRIVATE_NATIVE_ROOT_73A9",
                   "D1_PRIVATE_LAUNCHER_73A9", "D1_PRIVATE_CONDITION_73A9"):
        assert marker not in response.text


@pytest.mark.parametrize("role", ["local", *TIERS])
@pytest.mark.parametrize("route,workspace", LEGACY_TARGETS)
@pytest.mark.parametrize("empty", [False, True])
def test_legacy_http_visibility(service, role, route, workspace, empty):
    with service(auth=role != "local", empty=empty) as svc:
        operator = _request(svc, route, workspace)
        assert operator.status_code == 200
        original = operator.json()
        actual = _request(svc, route, workspace, None if role == "local" else role)
        assert actual.status_code == 200
        if role in ("operator", "local"):
            assert actual.json() == original
        else:
            assert actual.json() == _redacted(original, route)
            _assert_no_sensitive_response(svc, actual)
        if route == "/config":
            assert original == _raw_config(svc)
            assert original["effective"]["TORMENT_DATA_DIR"]["value"] == str(svc.root)
            assert original["effective"]["TORMENT_DATA_DIR"]["default"] == "<auto>"
            assert "TORMENT_SERVER_LAUNCHER_PATH" not in original["effective"]
            assert "TORMENT_TEST_CONDITION" not in original["effective"]
        else:
            assert original["companion_runtime_flags"] == svc.app.build_companion_runtime_flags()
            assert original["companion_runtime_flags"]["TORMENT_DATA_DIR"]["effective_value"] == str(svc.root)
            assert original["companion_runtime_flags"]["TORMENT_SERVER_LAUNCHER_PATH"]["effective_value"] == ("" if empty else "C:/D1_PRIVATE_LAUNCHER_73A9/server.cmd")
            assert original["companion_runtime_flags"]["TORMENT_TEST_CONDITION"]["effective_value"] == ("" if empty else "D1_PRIVATE_CONDITION_73A9")
            assert isinstance(original["features"]["compress_enable"], bool)
            if workspace == "present":
                assert original["agents"]["synthetic-agent"]["memory_count"] == 0
                assert original["domains"]["personal"]["shared_memory_count"] == 0
            else:
                assert original["error"] == "workspace 'missing' not found"


@pytest.mark.parametrize("role", ["local", *TIERS])
def test_native_config_visibility(service, role):
    with service(native=True, auth=role != "local") as svc:
        response = _request(svc, "/config", role=None if role == "local" else role)
        assert response.status_code == 200
        raw = _raw_config(svc)
        assert raw["effective"]["TORMENT_DATA_DIR"]["value"] == str(svc.root)
        expected = raw if role in ("local", "operator") else _redacted(raw, "/config")
        assert response.json() == expected
        if role not in ("local", "operator"):
            _assert_no_sensitive_response(svc, response)
        assert _raw_config(svc) == raw


@pytest.mark.parametrize("native", [False, True])
@pytest.mark.parametrize("route", ["/config", "/debug/metrics"])
@pytest.mark.parametrize("credential", ["missing", "invalid", "query-only"])
def test_credentials_refused_before_visibility_or_native_fence(service, native, route, credential):
    with service(native=native) as svc:
        headers = {"X-Role": "operator", "X-Trust-Tier": "1.0", "X-Forwarded-For": "127.0.0.1"}
        params = {"client_id": "operator", "trust_tier": "1.0", "role": "operator"}
        if credential == "invalid":
            headers["X-API-Key"] = "synthetic-invalid-key"
        elif credential == "query-only":
            params["api_key"] = KEYS["operator"]
        response = _request(svc, route, role=None, headers=headers, params=params)
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid API key." if credential == "invalid"
                                   else "Missing API key. Provide X-API-Key header."}
        _assert_no_sensitive_response(svc, response)
        for key in KEYS.values():
            assert key not in response.text


@pytest.mark.parametrize("native,route", [(False, "/config"), (False, "/debug/metrics"), (True, "/config")])
def test_untrusted_privilege_claims_and_loopback_do_not_elevate(service, native, route):
    with service(native=native) as svc:
        response = _request(svc, route, "operator", "reader",
            headers={"X-Role": "operator", "X-Trust-Tier": "1.0", "X-Client-Id": "operator",
                     "X-Forwarded-For": "127.0.0.1", "Forwarded": "for=127.0.0.1;host=localhost"},
            params={"role": "operator", "trust_tier": "1.0", "agent_id": "operator",
                    "client_id": "operator", "api_key": KEYS["operator"]})
        assert response.status_code == 200
        _assert_no_sensitive_response(svc, response)
        if route == "/config":
            assert response.json() == _redacted(_raw_config(svc), route)
        else:
            for name in SENSITIVE_FLAGS:
                assert response.json()["companion_runtime_flags"][name]["effective_value"] == REDACTED


@pytest.mark.parametrize("native,route", [(False, "/config"), (False, "/debug/metrics"), (True, "/config")])
@pytest.mark.parametrize("order", [("operator", "reader", "operator"), ("reader", "operator", "reader")])
def test_request_order_and_raw_builders_are_unchanged(service, native, route, order):
    with service(native=native) as svc:
        raw_config = _raw_config(svc)
        raw_flags = None if native else svc.app.build_companion_runtime_flags()
        operator = _request(svc, route, "present").json()
        for role in order:
            response = _request(svc, route, "present", role)
            assert response.status_code == 200
            assert response.json() == (operator if role == "operator" else _redacted(operator, route))
            assert _raw_config(svc) == raw_config
            if not native:
                assert svc.app.build_companion_runtime_flags() == raw_flags
        assert svc.app.DATA_DIR == str(svc.root)


@pytest.mark.parametrize("route", ["/config", "/debug/metrics"])
def test_cached_builder_dicts_are_not_mutated(service, monkeypatch, route):
    # Supplement real-builder HTTP tests by checking an internal consumer that
    # retains the same dict; the route and authentication still execute normally.
    with service() as svc:
        if route == "/config":
            raw = _raw_config(svc)
            monkeypatch.setattr(svc.app, "build_config_view", lambda **kwargs: raw)
        else:
            raw = svc.app.build_companion_runtime_flags()
            monkeypatch.setattr(svc.app, "build_companion_runtime_flags", lambda: raw)
        before = copy.deepcopy(raw)
        low = _request(svc, route, "missing", "reader")
        assert low.status_code == 200
        _assert_no_sensitive_response(svc, low)
        assert raw == before
        high = _request(svc, route, "missing", "operator")
        assert high.status_code == 200
        assert raw == before
        assert (high.json() if route == "/config" else high.json()["companion_runtime_flags"]) == before


@pytest.mark.parametrize("native,route", [(False, "/config"), (False, "/debug/metrics"), (True, "/config")])
def test_middleware_key_lookup_is_not_repeated(service, monkeypatch, native, route):
    with service(native=native) as svc:
        store = svc.auth.get_key_store()
        real_lookup = store.lookup
        calls = []
        def lookup(key):
            calls.append(key)
            return real_lookup(key)
        monkeypatch.setattr(store, "lookup", lookup)
        response = _request(svc, route, "missing", "reader")
        assert response.status_code == 200
        assert calls == [KEYS["reader"]]


@pytest.mark.parametrize("role", ["local", "operator", "reader"])
def test_native_metrics_refused_before_handler(service, monkeypatch, role):
    with service(native=True, auth=role != "local") as svc:
        entered = []
        # A delegating endpoint spy observes entry; the real native middleware
        # must refuse before either the spy or original handler is invoked.
        route = next(route for route in svc.app.app.routes if route.path == "/debug/metrics")
        original = route.dependant.call
        async def record(*args, **kwargs):
            entered.append(True)
            return await original(*args, **kwargs)
        monkeypatch.setattr(route.dependant, "call", record)
        response = _request(svc, "/debug/metrics", "orchard", None if role == "local" else role)
        assert response.status_code == 409
        assert response.json() == {"detail": "native public route is refused before legacy-memory effect"}
        assert entered == []
        _assert_no_sensitive_response(svc, response)
