"""Regression coverage for REST authorization repair batch A1."""
from __future__ import annotations

import ast
import importlib
import inspect
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request


KEYS_BY_TIER = {
    0.0: "sk-a1-tier-0",
    0.3: "sk-a1-tier-03",
    0.6: "sk-a1-tier-06",
    0.9: "sk-a1-tier-09",
    1.0: "sk-a1-tier-10",
}
ALL_TIERS = tuple(KEYS_BY_TIER)


def _client_with_env(tmp_path, *, auth_enabled: bool) -> Iterator[tuple[TestClient, object, object]]:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    env_keys = (
        "TORMENT_DATA_DIR",
        "TORMENT_AUTH_ENABLE",
        "TORMENT_API_KEYS",
        "TORMENT_API_KEYS_FILE",
        "TORMENT_ARCHIVIST_WRITEBACK",
        "TORMENT_EMBED_PROVIDER",
        "TORMENT_HIVEMIND_ENABLE",
    )
    original_env = {key: os.environ.get(key) for key in env_keys}

    os.environ["TORMENT_DATA_DIR"] = str(data_dir)
    os.environ["TORMENT_AUTH_ENABLE"] = "1" if auth_enabled else "0"
    os.environ["TORMENT_API_KEYS"] = ",".join(
        f"{key}:a1-tier-{tier:.1f}:{tier:.1f}"
        for tier, key in KEYS_BY_TIER.items()
    )
    os.environ.pop("TORMENT_API_KEYS_FILE", None)
    os.environ["TORMENT_ARCHIVIST_WRITEBACK"] = "0"
    os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
    os.environ["TORMENT_HIVEMIND_ENABLE"] = "1"

    import torment_service.auth as authmod
    import torment_service.app as appmod

    authmod = importlib.reload(authmod)
    appmod = importlib.reload(appmod)
    client = TestClient(appmod.app)
    try:
        yield client, appmod, authmod
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
def auth_client(tmp_path) -> Iterator[tuple[TestClient, object, object]]:
    yield from _client_with_env(tmp_path, auth_enabled=True)


@pytest.fixture()
def no_auth_client(tmp_path) -> Iterator[tuple[TestClient, object, object]]:
    yield from _client_with_env(tmp_path, auth_enabled=False)


def _headers(tier: float) -> dict[str, str]:
    return {"X-API-Key": KEYS_BY_TIER[tier]}


def _request_without_state() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [],
        }
    )


def _assert_agent_absent(appmod, workspace_id: str, agent_id: str) -> None:
    agent_key = appmod.fabric._agent_key(workspace_id, agent_id)
    assert workspace_id not in appmod.fabric.workspaces
    assert agent_key not in appmod.fabric.agent_states
    assert agent_key not in appmod.fabric.private_graphs
    agent_dir = Path(appmod.DATA_DIR) / "workspaces" / workspace_id / "agents" / agent_id
    assert not agent_dir.exists()


def test_authenticated_request_context_is_reused_and_rebound(auth_client, monkeypatch):
    _client, _appmod, authmod = auth_client
    request = _request_without_state()
    original = authmod.RequestContext(
        client_id="authenticated-client",
        trust_tier=0.6,
        workspace_id="middleware-workspace",
        agent_id="middleware-agent",
        session_id="session-a1",
        timestamp=123.0,
        metadata={"request_id": "audit-a1"},
    )
    request.state.torment_auth_context = original

    def unexpected_lookup(*_args, **_kwargs):
        raise AssertionError("handler attempted a second API-key lookup")

    monkeypatch.setattr(authmod, "resolve_request_context", unexpected_lookup)
    context = authmod.get_request_context(
        request,
        workspace_id="route-workspace",
        agent_id="route-agent",
    )

    assert context is not original
    assert context.client_id == "authenticated-client"
    assert context.trust_tier == 0.6
    assert context.workspace_id == "route-workspace"
    assert context.agent_id == "route-agent"
    assert context.session_id == "session-a1"
    assert context.timestamp == 123.0
    assert context.metadata == {"request_id": "audit-a1"}


def test_auth_disabled_context_does_not_require_middleware_state(no_auth_client):
    _client, _appmod, authmod = no_auth_client

    context = authmod.get_request_context(
        _request_without_state(),
        workspace_id="local-workspace",
        agent_id="local-agent",
    )

    assert context.client_id == authmod._DEFAULT_CLIENT_ID
    assert context.trust_tier == 1.0
    assert context.workspace_id == "local-workspace"
    assert context.agent_id == "local-agent"


def _patch_authorized_operation(monkeypatch, appmod, operation: str) -> None:
    if operation == "archive_ingest":
        class ArchiveStoreStub:
            def ingest_document(self, **_kwargs):
                return {"ok": True}

        monkeypatch.setattr(appmod, "_get_archive_store", lambda *_args: ArchiveStoreStub())
        return
    if operation == "promote":
        class ArchiveStoreStub:
            _chunks = {"chunk-a1": SimpleNamespace(text="ordinary promotion", doc_id="doc-a1")}
            _chunk_embeddings = {"chunk-a1": None}

        monkeypatch.setattr(appmod, "_get_archive_store", lambda *_args: ArchiveStoreStub())
        return

    fabric_method = {
        "propose_share": "propose_share",
        "process_proposals": "process_proposals",
        "bridges_decide": "decide_bridge",
        "proposals_decide": "decide_proposal",
        "motif_merges_decide": "decide_motif_merge",
        "conflicts_decide": "decide_conflict",
    }.get(operation)
    if fabric_method:
        monkeypatch.setattr(appmod.fabric, fabric_method, lambda *_args, **_kwargs: {"ok": True})


DIRECT_ROUTE_CASES = (
    (
        "workspace_create",
        "/workspace/create",
        {"workspace_id": "ws_a1_create", "domains": ["personal"]},
        1.0,
    ),
    (
        "agent_create",
        "/agent/create",
        {"workspace_id": "ws_a1_agent", "agent_id": "ag_a1_agent"},
        1.0,
    ),
    (
        "propose_share",
        "/agent/propose_share",
        {"workspace_id": "ws_a1", "agent_id": "ag_a1", "summary": "proposal"},
        0.6,
    ),
    (
        "process_proposals",
        "/workspace/process_proposals",
        {"workspace_id": "ws_a1", "domain_id": "personal"},
        0.9,
    ),
    (
        "bridges_decide",
        "/workspace/bridges/decide",
        {
            "workspace_id": "ws_a1",
            "from_domain": "personal",
            "from_motif": "left",
            "to_domain": "personal",
            "to_motif": "right",
            "decision": "approve",
        },
        1.0,
    ),
    (
        "proposals_decide",
        "/workspace/domain/proposals/decide",
        {"workspace_id": "ws_a1", "domain_id": "personal", "proposal_id": "proposal-a1", "decision": "approve"},
        1.0,
    ),
    (
        "motif_merges_decide",
        "/workspace/motif_merges/decide",
        {"workspace_id": "ws_a1", "domain_id": "personal", "suggestion_id": "merge-a1", "decision": "approve"},
        1.0,
    ),
    (
        "conflicts_decide",
        "/workspace/conflicts/decide",
        {"workspace_id": "ws_a1", "domain_id": "personal", "conflict_id": "conflict-a1", "decision": "reject"},
        1.0,
    ),
    (
        "archive_ingest",
        "/archive/ingest_document",
        {"workspace_id": "ws_a1", "agent_id": "ag_a1", "text": "archive document"},
        0.6,
    ),
    (
        "compress_trigger",
        "/workspace/ws_a1/compress/trigger",
        {"workspace_id": "ws_a1", "agent_id": "ag_a1", "step": 1},
        1.0,
    ),
    (
        "promote",
        "/promote",
        {"workspace_id": "ws_a1", "agent_id": "ag_a1", "chunk_id": "chunk-a1", "force": False},
        0.6,
    ),
)


@pytest.mark.parametrize("operation,path,payload,minimum_tier", DIRECT_ROUTE_CASES)
def test_direct_routes_enforce_existing_policy(
    auth_client,
    monkeypatch,
    operation: str,
    path: str,
    payload: dict,
    minimum_tier: float,
):
    client, appmod, _authmod = auth_client
    _patch_authorized_operation(monkeypatch, appmod, operation)

    for tier in ALL_TIERS:
        response = client.post(path, headers=_headers(tier), json=payload)
        if tier < minimum_tier:
            assert response.status_code == 403, (operation, tier, response.text)
        else:
            assert response.status_code == 200, (operation, tier, response.text)


def test_compress_denial_precedes_feature_state(auth_client):
    client, _appmod, _authmod = auth_client
    payload = {"workspace_id": "ws_a1_compress", "agent_id": "ag_a1_compress", "step": 1}

    denied = client.post(
        "/workspace/ws_a1_compress/compress/trigger",
        headers=_headers(0.9),
        json=payload,
    )
    operator = client.post(
        "/workspace/ws_a1_compress/compress/trigger",
        headers=_headers(1.0),
        json=payload,
    )

    assert denied.status_code == 403, denied.text
    assert operator.status_code == 200, operator.text
    assert operator.json()["ok"] is False


def test_direct_trust_literals_are_defined_policy_operations(auth_client):
    _client, appmod, _authmod = auth_client
    from torment_service.request_context import OPERATION_TRUST_REQUIREMENTS

    source = inspect.getsource(appmod)
    tree = ast.parse(source)
    direct_operations = {
        call.args[1].value
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "require_request_trust"
        and len(call.args) >= 2
        and isinstance(call.args[1], ast.Constant)
        and isinstance(call.args[1].value, str)
    }

    assert direct_operations == {case[0] for case in DIRECT_ROUTE_CASES}
    assert direct_operations <= set(OPERATION_TRUST_REQUIREMENTS)


def test_insufficient_trust_spine_routes_do_not_create_agent_state(auth_client):
    client, appmod, _authmod = auth_client
    cases = (
        (
            "/agent/ingest",
            0.0,
            {"workspace_id": "ws_a1_ingest", "agent_id": "ag_a1_ingest", "text": "denied"},
            403,
        ),
        (
            "/tool/ingest",
            0.0,
            {
                "workspace_id": "ws_a1_tool",
                "agent_id": "ag_a1_tool",
                "tool_name": "probe",
                "content": "denied",
            },
            403,
        ),
        (
            "/workspace/ws_a1_collective/collective/reingest",
            0.6,
            {"agent_id": "ag_a1_collective", "event_id": "missing-event"},
            403,
        ),
    )

    for path, tier, payload, expected_status in cases:
        workspace_id = payload.get("workspace_id") or "ws_a1_collective"
        agent_id = payload["agent_id"]
        _assert_agent_absent(appmod, workspace_id, agent_id)
        response = client.post(path, headers=_headers(tier), json=payload)
        assert response.status_code == expected_status, response.text
        _assert_agent_absent(appmod, workspace_id, agent_id)

    workspace_id = "ws_a1_generic"
    agent_id = "ag_a1_generic"
    _assert_agent_absent(appmod, workspace_id, agent_id)
    response = client.post(
        "/spine/submit_task",
        headers=_headers(0.0),
        json={
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "operation": "ingest",
            "payload": {"text": "denied"},
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["allowed"] is False
    assert response.json()["decision_code"] == "blocked_insufficient_trust"
    _assert_agent_absent(appmod, workspace_id, agent_id)


def test_authorized_generic_spine_and_direct_submit_task_preserve_provisioning(auth_client):
    client, appmod, _authmod = auth_client
    workspace_id = "ws_a1_generic_authorized"
    agent_id = "ag_a1_generic_authorized"
    response = client.post(
        "/spine/submit_task",
        headers=_headers(0.6),
        json={
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "operation": "ingest",
            "payload": {"text": "authorized"},
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["allowed"] is True
    assert appmod.fabric._agent_key(workspace_id, agent_id) in appmod.fabric.agent_states

    from torment_service.request_context import RequestContext
    from torment_service.spine import SpineRequest, submit_task

    mcp_workspace_id = "ws_a1_mcp"
    mcp_agent_id = "ag_a1_mcp"
    direct_response = submit_task(
        SpineRequest(
            workspace_id=mcp_workspace_id,
            agent_id=mcp_agent_id,
            operation="ingest",
            payload={"text": "direct submit"},
        ),
        appmod.fabric,
        RequestContext(
            client_id="mcp-client",
            trust_tier=0.6,
            workspace_id=mcp_workspace_id,
            agent_id=mcp_agent_id,
        ),
    )
    assert direct_response.ok is True
    assert appmod.fabric._agent_key(mcp_workspace_id, mcp_agent_id) in appmod.fabric.agent_states


def test_auth_disabled_direct_routes_remain_operator_equivalent(no_auth_client, monkeypatch):
    client, appmod, _authmod = no_auth_client
    monkeypatch.setattr(appmod.fabric, "propose_share", lambda *_args, **_kwargs: {"ok": True})

    workspace = client.post(
        "/workspace/create",
        json={"workspace_id": "ws_a1_local", "domains": ["personal"]},
    )
    proposal = client.post(
        "/agent/propose_share",
        json={"workspace_id": "ws_a1_local", "agent_id": "ag_a1_local", "summary": "local"},
    )

    assert workspace.status_code == 200, workspace.text
    assert proposal.status_code == 200, proposal.text
