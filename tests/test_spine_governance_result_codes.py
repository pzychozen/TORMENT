"""Regression invariants for handler-driven governance result codes."""
from __future__ import annotations

from torment_service import spine as spine_module
from torment_service.fabric import TormentFabric
from torment_service.request_context import RequestContext, TRUST_OPERATOR
from torment_service.spine import (
    RESULT_COGNITION,
    RESULT_GOVERNED,
    RESULT_NO_OP,
    SpineRequest,
    submit_task,
)


WORKSPACE_ID = "ws_governance_result_codes"
AGENT_ID = "agent_governance_result_codes"


def _fabric(tmp_path, monkeypatch, *, create_agent: bool) -> TormentFabric:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    fabric = TormentFabric(data_dir=str(tmp_path / "fabric"))
    fabric.get_workspace(WORKSPACE_ID)
    if create_agent:
        fabric.create_agent(WORKSPACE_ID, AGENT_ID)
    return fabric


def _context() -> RequestContext:
    return RequestContext(
        client_id="governance-result-test",
        trust_tier=TRUST_OPERATOR,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
    )


def _governance_set(fabric: TormentFabric, *, eid: int, flags: dict):
    return submit_task(
        SpineRequest(
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            operation="memory_governance_set",
            payload={"eid": eid, "flags": flags},
            mode="fast",
        ),
        fabric,
        _context(),
    )


def _memory_eid(fabric: TormentFabric) -> int:
    result = fabric.ingest(
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        text="governance result-code fixture",
        step=1,
    )
    return result["eid"]


def test_governance_missing_graph_is_no_op_and_carries_metadata(tmp_path, monkeypatch):
    response = _governance_set(
        _fabric(tmp_path, monkeypatch, create_agent=False),
        eid=999_999,
        flags={"protected": True},
    )

    assert response.ok is True
    assert response.result["ok"] is False
    assert response.result["reason"] == "Agent graph not found"
    assert response.result["_spine_result_code"] == RESULT_NO_OP
    assert response.result_code == RESULT_NO_OP


def test_governance_missing_eid_is_no_op_and_carries_metadata(tmp_path, monkeypatch):
    response = _governance_set(
        _fabric(tmp_path, monkeypatch, create_agent=True),
        eid=999_999,
        flags={"protected": True},
    )

    assert response.ok is True
    assert response.result["ok"] is False
    assert response.result["reason"] == "Memory eid=999999 not found"
    assert response.result["_spine_result_code"] == RESULT_NO_OP
    assert response.result_code == RESULT_NO_OP


def test_governance_unchanged_flags_is_no_op(tmp_path, monkeypatch):
    fabric = _fabric(tmp_path, monkeypatch, create_agent=True)
    response = _governance_set(
        fabric,
        eid=_memory_eid(fabric),
        flags={"protected": False},
    )

    assert response.result["ok"] is True
    assert response.result["audit"]["changed"] == {}
    assert response.result["_spine_result_code"] == RESULT_NO_OP
    assert response.result_code == RESULT_NO_OP


def test_governance_mutation_is_governed(tmp_path, monkeypatch):
    fabric = _fabric(tmp_path, monkeypatch, create_agent=True)
    response = _governance_set(
        fabric,
        eid=_memory_eid(fabric),
        flags={"protected": True},
    )

    assert response.result["ok"] is True
    assert response.result["audit"]["changed"]
    assert response.result["_spine_result_code"] == RESULT_GOVERNED
    assert response.result_code == RESULT_GOVERNED


def test_reinforce_private_result_code_fallback_is_unchanged(tmp_path, monkeypatch):
    fabric = _fabric(tmp_path, monkeypatch, create_agent=True)
    eid = _memory_eid(fabric)

    success = submit_task(
        SpineRequest(
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            operation="reinforce",
            payload={"retrieved_ids": [eid], "used_successfully": [eid]},
            mode="fast",
        ),
        fabric,
        _context(),
    )
    no_op = submit_task(
        SpineRequest(
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            operation="reinforce",
            payload={"retrieved_ids": [999_999], "used_successfully": [999_999]},
            mode="fast",
        ),
        fabric,
        _context(),
    )

    assert success.result_code == "reinforced"
    assert success.result["reinforced_eids"] == [eid]
    assert no_op.result_code == RESULT_NO_OP
    assert no_op.result["reinforced_eids"] == []


def test_full_cognition_result_code_remains_a_path_stamp(tmp_path, monkeypatch):
    fabric = _fabric(tmp_path, monkeypatch, create_agent=False)
    monkeypatch.setattr(
        spine_module,
        "_full_cognition",
        lambda *_args, **_kwargs: {"ok": False, "reason": "forced inner failure"},
    )

    response = submit_task(
        SpineRequest(
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            operation="cognition_run",
            payload={},
            mode="full",
        ),
        fabric,
        _context(),
    )

    assert response.ok is True
    assert response.result["ok"] is False
    assert response.result_code == RESULT_COGNITION
