"""B5-A4R1 public mutation identity and legacy ingest-boundary evidence."""
from __future__ import annotations

import importlib
import os
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from torment_service.fabric import TormentFabric
from torment_service.ingest_orchestration import LegacyFabricIngestStorageAdapter
from torment_service.public_mutation_identity import (
    PublicMutationKeyError,
    canonical_public_request_fingerprint,
    derive_native_operation_key,
    normalize_public_mutation_key,
)
from torment_service.request_context import RequestContext, TRUST_INGEST
from torment_service.spine import SpineRequest, submit_task


def _embedding() -> list[float]:
    values = np.zeros(384, dtype=np.float32)
    values[0] = 1.0
    return values.tolist()


def _fabric(tmp_path: Path) -> TormentFabric:
    fabric = TormentFabric(data_dir=str(tmp_path))
    fabric.get_workspace("ws")
    fabric.create_agent("ws", "aria")
    return fabric


def test_public_mutation_key_is_opaque_bounded_and_not_trace_identity():
    key = normalize_public_mutation_key("retry-key-01")
    assert key is not None and key.value == "retry-key-01"
    with pytest.raises(PublicMutationKeyError):
        normalize_public_mutation_key("bad\nkey")
    with pytest.raises(PublicMutationKeyError):
        normalize_public_mutation_key("x" * 257)

    first = derive_native_operation_key(
        operation="ingest", workspace_id="ws", agent_id="aria", key=key,
    )
    same = derive_native_operation_key(
        operation="ingest", workspace_id="ws", agent_id="aria", key=key,
    )
    other = derive_native_operation_key(
        operation="ingest", workspace_id="ws", agent_id="aria",
        key=normalize_public_mutation_key("retry-key-02"),  # type: ignore[arg-type]
    )
    assert first == same
    assert first != other
    assert first.startswith("public-mutation/v1/")
    assert "retry-key-01" not in first

    same_task = SpineRequest("ws", "aria", "ingest", task_id="trace-a", idempotency_key="one")
    other_key = SpineRequest("ws", "aria", "ingest", task_id="trace-a", idempotency_key="two")
    same_key_new_trace = SpineRequest("ws", "aria", "ingest", task_id="trace-b", idempotency_key="one")
    assert same_task.task_id == other_key.task_id
    assert same_task.idempotency_key != other_key.idempotency_key
    assert same_task.task_id != same_key_new_trace.task_id
    assert same_task.idempotency_key == same_key_new_trace.idempotency_key


def test_ingest_preparation_derives_internal_key_and_legacy_storage_remains_single_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    fabric = _fabric(tmp_path)
    observed = []
    original = LegacyFabricIngestStorageAdapter.store

    def spy(self, prepared, **kwargs):
        observed.append(prepared)
        return original(self, prepared, **kwargs)

    monkeypatch.setattr(LegacyFabricIngestStorageAdapter, "store", spy)
    try:
        result = fabric.ingest(
            "ws", "aria", "stable public ingest", step=1,
            supplied_embedding=_embedding(), public_mutation_key="rest-retry-1",
        )
        assert "stored" in result and "reinforced" in result
        assert len(observed) == 1
        prepared = observed[0]
        assert prepared.native_operation_key is not None
        assert prepared.public_request_fingerprint is not None
        assert "rest-retry-1" not in prepared.native_operation_key
        assert "rest-retry-1" not in prepared.public_request_fingerprint
        assert not prepared.embedding.flags.writeable
        # The only durable source for this legacy call is still its graph.
        assert len(fabric.private_graphs[fabric._agent_key("ws", "aria")].entities) in {0, 1}
    finally:
        fabric.close()


def test_legacy_no_write_response_is_identical_with_or_without_public_key(tmp_path: Path):
    plain = _fabric(tmp_path / "plain")
    keyed = _fabric(tmp_path / "keyed")
    try:
        # Pin the existing no-write branch, including its public result and
        # post-write completion, then show that R1's optional key is inert in
        # public LEGACY mode.
        for fabric in (plain, keyed):
            identity = fabric.ident_store.load("ws", "aria")
            identity.overlay["write_threshold"] = 2.0
            fabric.ident_store.save(identity)
        args = ("ws", "aria", "legacy parity no write")
        kwargs = {"step": 3, "supplied_embedding": _embedding()}
        assert plain.ingest(*args, **kwargs) == keyed.ingest(
            *args, **kwargs, public_mutation_key="parity-key-1",
        )
    finally:
        plain.close()
        keyed.close()


def test_spine_propagates_key_without_redefining_task_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fabric = _fabric(tmp_path)
    captured: list[str | None] = []
    original = fabric.ingest

    def ingest(*args, **kwargs):
        captured.append(kwargs.get("public_mutation_key"))
        return original(*args, **kwargs)

    monkeypatch.setattr(fabric, "ingest", ingest)
    ctx = RequestContext("test", TRUST_INGEST, "ws", "aria")
    try:
        request = SpineRequest(
            "ws", "aria", "ingest",
            payload={"text": "spine key", "step": 2, "supplied_embedding": _embedding()},
            task_id="trace-explicit", idempotency_key="spine-retry-1",
        )
        response = submit_task(request, fabric, ctx)
        assert response.ok
        assert request.task_id == "trace-explicit"
        assert captured == ["spine-retry-1"]
    finally:
        fabric.close()


def test_canonical_fingerprint_covers_semantic_request_not_trace_fields():
    first = canonical_public_request_fingerprint(
        operation="ingest", workspace_id="ws", agent_id="aria",
        semantic_payload={"text": "same", "step": 1, "scope": "private"},
    )
    same = canonical_public_request_fingerprint(
        operation="ingest", workspace_id="ws", agent_id="aria",
        semantic_payload={"scope": "private", "step": 1, "text": "same"},
    )
    changed = canonical_public_request_fingerprint(
        operation="ingest", workspace_id="ws", agent_id="aria",
        semantic_payload={"text": "changed", "step": 1, "scope": "private"},
    )
    assert first == same
    assert first != changed


def test_rest_header_is_optional_in_legacy_mode_and_invalid_key_fails_before_spine(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    previous = os.environ.get("TORMENT_DATA_DIR")
    monkeypatch.setenv("TORMENT_DATA_DIR", str(tmp_path))
    import torment_service.app as appmod
    appmod = importlib.reload(appmod)
    try:
        with TestClient(appmod.app) as client:
            assert client.post("/workspace/create", json={"workspace_id": "ws"}).status_code == 200
            assert client.post("/agent/create", json={"workspace_id": "ws", "agent_id": "aria"}).status_code == 200
            body = {
                "workspace_id": "ws", "agent_id": "aria", "text": "legacy key optional",
                "step": 1, "supplied_embedding": _embedding(),
            }
            assert client.post("/agent/ingest", json=body).status_code == 200
            assert client.post("/agent/ingest", json=body, headers={"Idempotency-Key": "rest-key-1"}).status_code == 200
            response = client.post("/agent/ingest", json=body, headers={"Idempotency-Key": "\x7f"})
            assert response.status_code == 400
            # The rejection happens before the governed ingest dispatch.
            graph = appmod.fabric.private_graphs[appmod.fabric._agent_key("ws", "aria")]
            assert len(graph.entities) == 1

            spine_response = client.post("/spine/submit_task", json={
                "workspace_id": "ws", "agent_id": "aria", "operation": "ingest",
                "payload": body, "idempotency_key": "\x7f",
            })
            assert spine_response.status_code == 400
    finally:
        appmod.fabric.close()
        if previous is None:
            os.environ.pop("TORMENT_DATA_DIR", None)
        else:
            os.environ["TORMENT_DATA_DIR"] = previous
        importlib.reload(appmod)


def test_mcp_invalid_key_is_rejected_without_reusing_task_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    import torment_service.mcp_server as mcp_mod

    fabric = _fabric(tmp_path)
    client = mcp_mod.MCPClientContext(
        client_id="r1", trust_tier=TRUST_INGEST,
        default_workspace_id="ws", default_agent_id="aria", session_id="r1-session",
    )
    previous_fabric, previous_client = mcp_mod._fabric, mcp_mod._client_ctx
    monkeypatch.setattr(mcp_mod, "_fabric", fabric)
    monkeypatch.setattr(mcp_mod, "_client_ctx", client)
    try:
        result = mcp_mod._spine_call(
            "ingest", {"text": "MCP key validation", "supplied_embedding": _embedding()},
            idempotency_key="bad\x7fkey",
        )
        assert result["ok"] is False
        assert result["decision_code"] == "blocked_mcp_invalid_idempotency_key"
        assert not fabric.private_graphs[fabric._agent_key("ws", "aria")].entities
    finally:
        mcp_mod._fabric, mcp_mod._client_ctx = previous_fabric, previous_client
        fabric.close()
