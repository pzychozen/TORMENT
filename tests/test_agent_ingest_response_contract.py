from __future__ import annotations

from types import SimpleNamespace

from torment_service.request_context import RequestContext
from torment_service.spine import SpineResponse


def _ctx(workspace_id="ws", agent_id="ag"):
    return RequestContext(
        client_id="test",
        trust_tier=1.0,
        workspace_id=workspace_id,
        agent_id=agent_id,
    )


class _Fabric:
    def __init__(self):
        self.create_agent_calls = []

    def create_agent(self, workspace_id, agent_id):
        self.create_agent_calls.append((workspace_id, agent_id))


def _ingest_req(appmod):
    return appmod.IngestReq(
        workspace_id="ws",
        agent_id="ag",
        text="memory text",
        step=7,
        supplied_summary="memory summary",
        supplied_embedding=[0.1, 0.2],
        scope="private",
    )


def _call_ingest(monkeypatch, response):
    import torment_service.app as appmod
    import torment_service.spine as spine

    fabric = _Fabric()
    captured = {}

    def fake_submit_task(req, fabric_arg, ctx):
        captured["req"] = req
        captured["fabric"] = fabric_arg
        captured["ctx"] = ctx
        return response

    monkeypatch.setattr(appmod, "fabric", fabric)
    monkeypatch.setattr(
        appmod,
        "resolve_request_context",
        lambda request, workspace_id, agent_id: _ctx(workspace_id, agent_id),
    )
    monkeypatch.setattr(spine, "submit_task", fake_submit_task)

    payload = appmod.ingest(_ingest_req(appmod), SimpleNamespace())
    return payload, captured, fabric


def _response(**overrides):
    data = {
        "ok": True,
        "path": "fast",
        "operation": "ingest",
        "allowed": True,
        "workspace_id": "ws",
        "agent_id": "ag",
        "decision_code": "fast_allowed",
        "result_code": "stored",
        "result": {"stored": True, "reinforced": False, "eid": 123},
        "escalated": False,
    }
    data.update(overrides)
    return SpineResponse(**data)


def test_agent_ingest_stored_response_exposes_storage_outcome_and_eid(monkeypatch):
    payload, captured, fabric = _call_ingest(monkeypatch, _response())

    assert payload["stored"] is True
    assert payload["reinforced"] is False
    assert payload["eid"] == 123
    assert payload["path"] == "fast"
    assert payload["escalated"] is False
    assert payload["result_code"] == "stored"
    assert payload["decision_code"] == "fast_allowed"
    assert fabric.create_agent_calls == [("ws", "ag")]
    assert captured["req"].payload == {
        "text": "memory text",
        "step": 7,
        "domain_id": None,
        "supplied_summary": "memory summary",
        "supplied_embedding": [0.1, 0.2],
        "scope": "private",
    }


def test_agent_ingest_reinforced_response_is_distinct_from_new_store(monkeypatch):
    payload, _captured, _fabric = _call_ingest(
        monkeypatch,
        _response(
            result_code="reinforced",
            result={"stored": False, "reinforced": True, "eid": 321},
        ),
    )

    assert payload["stored"] is False
    assert payload["reinforced"] is True
    assert payload["eid"] == 321
    assert payload["result_code"] == "reinforced"


def test_agent_ingest_escalated_handled_non_write_is_visible(monkeypatch):
    payload, _captured, _fabric = _call_ingest(
        monkeypatch,
        _response(
            path="full",
            escalated=True,
            decision_code="escalated_full",
            result_code="cognition",
            result={"status": "handled"},
        ),
    )

    assert payload["status"] == "handled"
    assert payload["path"] == "full"
    assert payload["escalated"] is True
    assert payload["decision_code"] == "escalated_full"
    assert payload["result_code"] == "cognition"
    assert payload["stored"] is False
    assert payload["reinforced"] is False


def test_agent_ingest_projection_does_not_serialize_spine_raw_internals(monkeypatch):
    payload, _captured, _fabric = _call_ingest(
        monkeypatch,
        _response(
            audit={"hidden_reasoning": "do not serialize"},
            task_id="spine_secret_task",
            trust_tier=0.8,
            result={"stored": True, "reinforced": False, "eid": 456},
        ),
    )

    assert "audit" not in payload
    assert "task_id" not in payload
    assert "trust_tier" not in payload
    assert "result" not in payload
