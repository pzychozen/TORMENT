"""Runtime regression coverage for Spine's canonical logical request text."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

import torment_service.spine as spine
from torment_service.fabric import TormentFabric
from torment_service.request_context import RequestContext, TRUST_READ_ONLY


WORKSPACE_ID = "spine_canonical_text_ws"
AGENT_ID = "spine_canonical_text_agent"


def _make_fabric(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TormentFabric:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
    monkeypatch.setenv("TORMENT_CHECKPOINT_ENABLE", "0")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")
    fabric = TormentFabric(data_dir=str(tmp_path / "fabric_data"))
    fabric.get_workspace(WORKSPACE_ID)
    fabric.create_agent(WORKSPACE_ID, AGENT_ID)
    return fabric


def _close_fabric(fabric: TormentFabric) -> None:
    for graph in list(getattr(fabric, "private_graphs", {}).values()):
        try:
            graph.close()
        except Exception:
            pass
    fabric.close()


def _request_context() -> RequestContext:
    return RequestContext(
        client_id="spine-canonical-text-test",
        trust_tier=TRUST_READ_ONLY,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
    )


@pytest.fixture()
def isolated_alignment_buffer() -> None:
    """Keep live advisory alignment records from leaking between tests."""
    with spine._alignment_lock:
        saved = list(spine._alignment_buffer)
        spine._alignment_buffer.clear()
    try:
        yield
    finally:
        with spine._alignment_lock:
            spine._alignment_buffer.clear()
            spine._alignment_buffer.extend(saved)


def _submit_fast_with_traces(
    fabric: TormentFabric,
    monkeypatch: pytest.MonkeyPatch,
    payload: Dict[str, Any],
) -> Tuple[Any, List[str], List[Dict[str, Any]]]:
    """Run the real fast path while recording its two advisory invocations."""
    monkeypatch.setattr(spine, "_THINKING_ADVISORY_ENABLE", True)
    thinking_texts: List[str] = []
    query_calls: List[Dict[str, Any]] = []
    original_advisory = spine._advisory_thinking
    original_query = fabric.query

    def advisory_spy(
        workspace_id: str,
        agent_id: str,
        text: str,
        geometric_context: Any = None,
    ) -> Any:
        thinking_texts.append(text)
        return original_advisory(
            workspace_id,
            agent_id,
            text,
            geometric_context=geometric_context,
        )

    def query_spy(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        query_calls.append({
            "query_text": kwargs["query_text"],
            "memory_plan": copy.deepcopy(kwargs.get("memory_plan")),
        })
        return original_query(*args, **kwargs)

    monkeypatch.setattr(spine, "_advisory_thinking", advisory_spy)
    monkeypatch.setattr(fabric, "query", query_spy)
    response = spine.submit_task(
        spine.SpineRequest(
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            operation="query_memory",
            payload=payload,
            mode=spine.MODE_FAST,
        ),
        fabric,
        _request_context(),
    )
    return response, thinking_texts, query_calls


def test_both_keys_share_audit_effective_plan_and_fabric_query_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_alignment_buffer: None,
) -> None:
    """text takes canonical precedence for both intentional Thinking calls."""
    fabric = _make_fabric(tmp_path, monkeypatch)
    try:
        response, thinking_texts, query_calls = _submit_fast_with_traces(
            fabric,
            monkeypatch,
            {"text": "who am I", "query": "cats"},
        )
        assert response.ok and response.path == spine.PATH_FAST
        assert thinking_texts == ["who am I", "who am I"]
        assert len(query_calls) == 1
        assert query_calls[0]["query_text"] == "who am I"

        audit_plan = response.audit["advisory_thinking"]["memory_plan"]
        assert query_calls[0]["memory_plan"] == {
            "top_k_by_lane": audit_plan["top_k_by_lane"],
            "weight_by_lane": audit_plan["weight_by_lane"],
        }
    finally:
        _close_fabric(fabric)


def test_empty_text_falls_through_to_query_for_auto_full_cognition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_alignment_buffer: None,
) -> None:
    """A query-only identity turn escalates and reaches full cognition intact."""
    import cognition.pipeline as pipeline

    fabric = _make_fabric(tmp_path, monkeypatch)
    try:
        task_inputs: List[str] = []
        original_pipeline = pipeline.run_cognition_pipeline

        def pipeline_spy(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            task_inputs.append(kwargs["task"].user_input)
            return original_pipeline(*args, **kwargs)

        monkeypatch.setattr(pipeline, "run_cognition_pipeline", pipeline_spy)
        response = spine.submit_task(
            spine.SpineRequest(
                workspace_id=WORKSPACE_ID,
                agent_id=AGENT_ID,
                operation="query_memory",
                payload={"text": "", "query": "who am I"},
            ),
            fabric,
            _request_context(),
        )

        assert spine._canonical_spine_text({"text": "", "query": "who am I"}) == "who am I"
        assert response.ok
        assert response.path == spine.PATH_FULL
        assert response.decision_code != spine.DECISION_ERROR_DISPATCH
        assert task_inputs == ["who am I"]
        assert response.audit["advisory_thinking"]["task_frame"]["normalized_input"] == "who am I"
    finally:
        _close_fabric(fabric)


@pytest.mark.parametrize(
    "payload",
    [
        {"query": "cats"},
        {"text": "cats"},
        {"user_input": "cats"},
    ],
)
def test_single_key_callers_share_canonical_text_on_fast_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: Dict[str, Any],
    isolated_alignment_buffer: None,
) -> None:
    """Legacy single-key forms agree across audit, effective Think, and Fabric."""
    fabric = _make_fabric(tmp_path, monkeypatch)
    try:
        response, thinking_texts, query_calls = _submit_fast_with_traces(
            fabric, monkeypatch, payload,
        )
        assert spine._canonical_spine_text(payload) == "cats"
        assert response.ok and response.path == spine.PATH_FAST
        assert thinking_texts == ["cats", "cats"]
        assert len(query_calls) == 1
        assert query_calls[0]["query_text"] == "cats"
    finally:
        _close_fabric(fabric)
