"""Focused no-network coverage for incident error-diagnostic redaction."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import torment_service.incident_log as incident_module
import torment_service.mcp_server as mcp_server
import torment_service.spine as spine_module
from torment_service.app import app, fabric
from torment_service.incident_log import get_incident_log, log_spine_decision
from torment_service.request_context import RequestContext
from torment_service.spine import SpineRequest, submit_task


FAKE_ANTHROPIC_KEY = "sk-ant-INCIDENT-REDACTION-TEST-ONLY"
FAKE_OPENAI_KEY = "sk-proj-INCIDENT-REDACTION-TEST-ONLY"
FAKE_OPENROUTER_KEY = "sk-or-v1-INCIDENT-REDACTION-TEST-ONLY"
FAKE_TORMENT_KEY = "torment-auth-INCIDENT-REDACTION-TEST-ONLY"
FAKE_SECOND_TORMENT_KEY = "torment-auth-SECOND-INCIDENT-TEST-ONLY"
NON_SECRET_DETAIL = "provider rejected the request after validation"

_SECRET_ENV_NAMES = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "TORMENT_API_KEYS",
)

_EXPECTED_INCIDENT_KEYS = {
    "timestamp",
    "operation",
    "decision_code",
    "result_code",
    "ok",
    "workspace_id",
    "agent_id",
    "trust_tier",
    "drift_status",
    "path",
    "elapsed_ms",
    "escalated",
    "escalation_reasons",
    "reason",
    "client_id",
    "session_id",
    "task_id",
    "operation_ok",
}


@pytest.fixture
def configured_incident_log(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Configure synthetic secrets and a fresh optional JSONL incident sink."""
    prior_log = incident_module._incident_log
    incident_module._incident_log = None

    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_ANTHROPIC_KEY)
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_OPENAI_KEY)
    monkeypatch.setenv("OPENROUTER_API_KEY", FAKE_OPENROUTER_KEY)
    monkeypatch.setenv(
        "TORMENT_API_KEYS",
        f"{FAKE_TORMENT_KEY}:incident-test:1.0,"
        f"{FAKE_SECOND_TORMENT_KEY}:second-client:0.6",
    )
    path = tmp_path / "incident.jsonl"
    monkeypatch.setenv("TORMENT_MCP_INCIDENT_LOG", str(path))

    try:
        yield path
    finally:
        incident_module._incident_log = prior_log


def _all_fake_secrets() -> tuple[str, ...]:
    return (
        FAKE_ANTHROPIC_KEY,
        FAKE_OPENAI_KEY,
        FAKE_OPENROUTER_KEY,
        FAKE_TORMENT_KEY,
        FAKE_SECOND_TORMENT_KEY,
    )


def _submit_dispatch_error(monkeypatch: pytest.MonkeyPatch):
    """Exercise the real Spine exception exit while avoiding Fabric mutation."""
    raw_reason = (
        f"RuntimeError: {NON_SECRET_DETAIL}: {FAKE_ANTHROPIC_KEY}; "
        f"{FAKE_OPENAI_KEY}; {FAKE_OPENROUTER_KEY}; {FAKE_TORMENT_KEY}; "
        f"{FAKE_SECOND_TORMENT_KEY}"
    )

    def raising_handler(_fabric, _ctx, _payload):
        raise RuntimeError(raw_reason.removeprefix("RuntimeError: "))

    monkeypatch.setitem(spine_module.FAST_DISPATCH, "ingest", raising_handler)
    response = submit_task(
        SpineRequest(
            workspace_id="incident_redaction_ws",
            agent_id="incident_redaction_agent",
            operation="ingest",
            payload={"text": "ordinary test input", "step": 1},
        ),
        fabric,
        RequestContext(
            client_id="incident_redaction_client",
            trust_tier=0.6,
            workspace_id="incident_redaction_ws",
            agent_id="incident_redaction_agent",
        ),
    )
    return response, raw_reason


def _call_guarded_admin_status(monkeypatch: pytest.MonkeyPatch) -> str:
    """Invoke the production guarded MCP resource body without transport I/O."""
    captured = {}
    original_resource = mcp_server.FastMCP.resource

    def capture_resource(self, *args, **kwargs):
        decorator = original_resource(self, *args, **kwargs)
        uri = kwargs.get("uri") if "uri" in kwargs else args[0]

        def capture(function):
            registered = decorator(function)
            if uri == "torment://admin/status":
                captured["admin_status"] = function
            return registered

        return capture

    monkeypatch.setenv("TORMENT_MCP_EXPOSURE_TIER", "guarded")
    monkeypatch.setattr(mcp_server.FastMCP, "resource", capture_resource)
    monkeypatch.setattr(mcp_server, "_fabric", fabric)
    mcp_server.create_mcp_server()
    return captured["admin_status"]()


def test_error_dispatch_redacts_only_incident_sinks(
    configured_incident_log, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = configured_incident_log
    response, raw_reason = _submit_dispatch_error(monkeypatch)
    log = get_incident_log()
    incident = log.query(limit=1)[0]

    # Spine response and dispatch envelope retain their established values.
    assert response.reason == raw_reason
    assert response.ok is False
    assert response.allowed is True
    assert response.decision_code == "error_dispatch"
    assert response.result_code == "none"
    assert response.http_status == 0
    assert response.escalated is False
    assert response.escalation_reasons == []

    # The in-memory incident keeps useful diagnostics, but no configured key.
    assert NON_SECRET_DETAIL in incident.reason
    for secret in _all_fake_secrets():
        assert secret not in incident.reason
    assert set(incident.to_dict()) == _EXPECTED_INCIDENT_KEYS
    assert log._total_logged == 1
    assert log._total_failures == 1
    assert incident.is_failure()

    # The persisted JSONL is the same redacted incident projection.
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    persisted = json.loads(lines[0])
    assert set(persisted) == _EXPECTED_INCIDENT_KEYS
    assert persisted["reason"] == incident.reason
    for secret in _all_fake_secrets():
        assert secret not in lines[0]

    # The REST status endpoint serializes the same redacted incident record.
    status = TestClient(app).get("/spine/status")
    assert status.status_code == 200
    status_text = status.text
    assert NON_SECRET_DETAIL in status_text
    for secret in _all_fake_secrets():
        assert secret not in status_text

    # The guarded MCP admin resource uses the production to_dict() projection.
    admin_status = _call_guarded_admin_status(monkeypatch)
    assert NON_SECRET_DETAIL in admin_status
    for secret in _all_fake_secrets():
        assert secret not in admin_status


def test_non_error_reasons_remain_exact_and_persistence_still_appends(
    configured_incident_log,
) -> None:
    original_reason = f"Unknown operation: {FAKE_ANTHROPIC_KEY}"
    response = SimpleNamespace(
        operation="unregistered_operation",
        decision_code="blocked_unknown_operation",
        result_code="none",
        ok=False,
        workspace_id="incident_redaction_ws",
        agent_id="incident_redaction_agent",
        trust_tier=0.0,
        drift_status="green",
        path="none",
        elapsed_ms=1.0,
        escalated=False,
        escalation_reasons=[],
        reason=original_reason,
        task_id="incident_redaction_task",
        result={},
    )
    context = SimpleNamespace(client_id="incident_redaction_client", session_id="")

    log_spine_decision(response, SimpleNamespace(), context)
    log_spine_decision(response, SimpleNamespace(), context)
    log = get_incident_log()

    incidents = log.query(limit=2)
    assert [incident.reason for incident in incidents] == [original_reason, original_reason]
    assert log._total_logged == 2
    assert log._total_failures == 2
    assert [incident.escalation_reasons for incident in incidents] == [[], []]

    lines = configured_incident_log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert [json.loads(line)["reason"] for line in lines] == [original_reason, original_reason]


def test_empty_or_unconfigured_values_do_not_change_error_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prior_log = incident_module._incident_log
    incident_module._incident_log = None
    for env_name in _SECRET_ENV_NAMES:
        monkeypatch.setenv(env_name, "")
    monkeypatch.delenv("TORMENT_MCP_INCIDENT_LOG", raising=False)

    original_reason = "RuntimeError: ordinary diagnostic without configured credentials"
    response = SimpleNamespace(
        operation="ingest",
        decision_code="error_dispatch",
        result_code="none",
        ok=False,
        workspace_id="incident_redaction_ws",
        agent_id="incident_redaction_agent",
        trust_tier=0.6,
        drift_status="green",
        path="fast",
        elapsed_ms=1.0,
        escalated=False,
        escalation_reasons=[],
        reason=original_reason,
        task_id="incident_redaction_task",
        result={},
    )
    try:
        log_spine_decision(response, SimpleNamespace(), SimpleNamespace(client_id="client", session_id=""))
        assert get_incident_log().query(limit=1)[0].reason == original_reason
    finally:
        incident_module._incident_log = prior_log
