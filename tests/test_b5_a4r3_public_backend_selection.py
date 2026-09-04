"""B5-A4R3 public runtime selection and transport qualification."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from torment_service.fabric import TormentFabric
from torment_service.memory_graph import MemoryGraph
from torment_service.substrate.native_public_mutation_receipts import PublicMutationIdempotencyConflict
from torment_service.public_runtime import (
    NativePublicOperationRefused,
    PublicRuntimeConfiguration,
    PublicRuntimeMode,
    PublicRuntimeStartupRefused,
    close_public_runtime,
    configure_public_runtime,
    create_public_runtime,
    reset_public_runtime_for_test,
)
from torment_service.request_context import RequestContext, TRUST_INGEST, TRUST_READ_ONLY
from torment_service.spine import SpineRequest, submit_task
from torment_service.substrate.connection import open_existing_native_core_connection
from torment_service.substrate.deployment_selector import resolve_deployment_agreement
from torment_service.substrate.deployment_types import DeploymentResolutionMode

from test_b5_a3_production_native_resource_owner import _Embedder, _active_fixture


class _NativeLaneFabric(TormentFabric):
    """Test-only Fabric construction matching B5-A3's admitted 3D lane."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kernel.embedder = _Embedder()


def _prime_external_identity(root: Path) -> bytes:
    """Create frozen external identity/config before native service startup."""
    fabric = _NativeLaneFabric(data_dir=str(root))
    try:
        workspace = fabric.get_workspace("orchard", domains=["personal", "archive", "research"])
        # Auto-merge is a separately-qualified maintenance operation.  The
        # public NATIVE fixture retains a persisted, inactive external policy
        # before the runtime factory can consume it.
        workspace.domain_policies["personal"]["auto_merge_motifs"] = False
        Path(workspace.domain_policies_path).write_text(
            json.dumps({"policies": workspace.domain_policies}, sort_keys=True),
            encoding="utf-8",
        )
        fabric.create_agent("orchard", "aria")
        graph_path = root / "workspaces" / "orchard" / "agents" / "aria" / "private" / "nodes.jsonl"
        return graph_path.read_bytes() if graph_path.exists() else b""
    finally:
        fabric.close()


def _configuration(root: Path, descriptor: Path, profile) -> PublicRuntimeConfiguration:
    return PublicRuntimeConfiguration(
        effective_profile=profile,
        admission_descriptor_path=descriptor,
    )


def _native_counts(runtime) -> tuple[int, int, int]:
    with open_existing_native_core_connection(runtime.native_owner.authority_facts.core_database_path) as opened:
        return tuple(int(opened.connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]) for table in (
            "objects", "object_revisions", "representations",
        ))


def _forbid_legacy_core_memory(monkeypatch) -> list[str]:
    """Turn every legacy core-memory authority call into a test failure."""
    calls: list[str] = []

    def _refuse(*_args, _method: str, **_kwargs):
        calls.append(_method)
        raise AssertionError(f"native public path touched legacy MemoryGraph.{_method}")

    for method in ("__init__", "search", "search_by_embedding", "spawn_memory", "update_payload", "flush_node"):
        monkeypatch.setattr(
            MemoryGraph,
            method,
            lambda *_args, _method=method, **_kwargs: _refuse(*_args, _method=_method, **_kwargs),
        )
    return calls


def test_factory_uses_read_only_selector_dispositions(tmp_path: Path, monkeypatch):
    import torment_service.public_runtime as public_runtime

    monkeypatch.setattr(public_runtime, "TormentFabric", _NativeLaneFabric)
    legacy_root = tmp_path / "legacy"
    legacy_root.mkdir()
    legacy = create_public_runtime(legacy_root)
    try:
        assert legacy.mode is PublicRuntimeMode.LEGACY
        assert legacy.native_owner is None
        assert not (legacy_root / "substrate" / "deployment").exists()
    finally:
        close_public_runtime(legacy_root)

    pending_root, _core, descriptor, profile, pending = _active_fixture(tmp_path / "pending", activate=False)
    assert pending.mode is DeploymentResolutionMode.MAINTENANCE_ONLY
    with pytest.raises(PublicRuntimeStartupRefused):
        create_public_runtime(pending_root, _configuration(pending_root, descriptor, profile))
    # The resolver remains read-only; no startup attempt can advance pending.
    assert resolve_deployment_agreement(data_root=pending_root, effective_profile=profile).mode is DeploymentResolutionMode.MAINTENANCE_ONLY


def test_native_runtime_uses_r2_ingest_and_b5_query_without_legacy_graphs(tmp_path: Path, monkeypatch):
    import torment_service.public_runtime as public_runtime

    monkeypatch.setattr(public_runtime, "TormentFabric", _NativeLaneFabric)
    root, _core, descriptor, profile, agreement = _active_fixture(tmp_path)
    assert agreement.mode is DeploymentResolutionMode.NATIVE_AGREEMENT
    legacy_before = _prime_external_identity(root)
    legacy_calls = _forbid_legacy_core_memory(monkeypatch)
    config = _configuration(root, descriptor, profile)
    runtime = create_public_runtime(root, config)
    try:
        assert runtime.mode is PublicRuntimeMode.NATIVE
        assert runtime.cognition_fabric.private_graphs == {}
        first = runtime.ingest(
            "orchard", "aria", "native transport memory", step=7,
            supplied_embedding=[1.0, 0.0, 0.0], public_mutation_key="native-public-retry",
        )
        counts_after_first = _native_counts(runtime)
        replay = runtime.ingest(
            "orchard", "aria", "native transport memory", step=7,
            supplied_embedding=[1.0, 0.0, 0.0], public_mutation_key="native-public-retry",
        )
        assert replay == first
        assert _native_counts(runtime) == counts_after_first
        assert "object_id" not in repr(first) and "revision_id" not in repr(first)
        with pytest.raises(PublicMutationIdempotencyConflict, match="PUBLIC_IDEMPOTENCY_CONFLICT"):
            runtime.ingest(
                "orchard", "aria", "changed native meaning", step=7,
                supplied_embedding=[1.0, 0.0, 0.0], public_mutation_key="native-public-retry",
            )

        no_write = runtime.ingest(
            "orchard", "aria", "", supplied_embedding=[1.0, 0.0, 0.0],
            public_mutation_key="native-no-write-retry",
        )
        no_write_replay = runtime.ingest(
            "orchard", "aria", "", supplied_embedding=[1.0, 0.0, 0.0],
            public_mutation_key="native-no-write-retry",
        )
        assert no_write["stored"] is False and no_write_replay == no_write

        reinforced = runtime.ingest(
            "orchard", "aria", "native transport memory", step=8,
            supplied_embedding=[1.0, 0.0, 0.0], public_mutation_key="native-reinforce-retry",
        )
        reinforced_replay = runtime.ingest(
            "orchard", "aria", "native transport memory", step=8,
            supplied_embedding=[1.0, 0.0, 0.0], public_mutation_key="native-reinforce-retry",
        )
        assert reinforced["reinforced"] is True and reinforced_replay == reinforced

        shared = runtime.ingest(
            "orchard", "aria", "native shared transport memory", step=9,
            scope="shared", domain_id="research", supplied_embedding=[1.0, 0.0, 0.0],
            public_mutation_key="native-shared-retry",
        )
        shared_replay = runtime.ingest(
            "orchard", "aria", "native shared transport memory", step=9,
            scope="shared", domain_id="research", supplied_embedding=[1.0, 0.0, 0.0],
            public_mutation_key="native-shared-retry",
        )
        assert shared["stored"] is True and shared["domain_chosen"] == "research"
        assert shared_replay == shared
        result = runtime.query("orchard", "aria", "native transport memory", top_k=4)
        assert "results" in result
        with runtime.native_owner.open_query_context(embedder=runtime.kernel.embedder) as direct_query:
            direct_private = direct_query.private_lane("orchard", "aria").search(
                "native transport memory", top_k=4,
            )
        public_private_eids = {
            item["eid"] for item in result["results"]
            if item.get("scope") == "private"
        }
        assert direct_private and direct_private[0].memory_identity.eid in public_private_eids
        with pytest.raises(NativePublicOperationRefused, match="Idempotency-Key"):
            runtime.ingest("orchard", "aria", "missing key", supplied_embedding=[1.0, 0.0, 0.0])
        with pytest.raises(NativePublicOperationRefused, match="feedback"):
            runtime.preflight_spine_operation("feedback", path="fast")
        graph_path = root / "workspaces" / "orchard" / "agents" / "aria" / "private" / "nodes.jsonl"
        assert (graph_path.read_bytes() if graph_path.exists() else b"") == legacy_before
        assert legacy_calls == []
    finally:
        close_public_runtime(root)

    restarted = create_public_runtime(root, config)
    try:
        assert restarted.mode is PublicRuntimeMode.NATIVE
        recovered = restarted.query("orchard", "aria", "native transport memory", top_k=4)
        assert recovered["results"]
    finally:
        close_public_runtime(root)


def test_native_spine_requires_key_and_replays_exact_r2_result(tmp_path: Path, monkeypatch):
    import torment_service.public_runtime as public_runtime

    monkeypatch.setattr(public_runtime, "TormentFabric", _NativeLaneFabric)
    root, _core, descriptor, profile, _agreement = _active_fixture(tmp_path)
    _prime_external_identity(root)
    legacy_calls = _forbid_legacy_core_memory(monkeypatch)
    runtime = create_public_runtime(root, _configuration(root, descriptor, profile))
    ctx = RequestContext("r3-test", TRUST_INGEST, "orchard", "aria")
    try:
        missing = submit_task(
            SpineRequest("orchard", "aria", "ingest", {"text": "spine missing key", "supplied_embedding": [1.0, 0.0, 0.0]}),
            runtime, ctx,
        )
        assert missing.ok is False and missing.decision_code == "blocked_native_public_operation"
        req = SpineRequest(
            "orchard", "aria", "ingest",
            {"text": "spine native memory", "step": 3, "supplied_embedding": [1.0, 0.0, 0.0]},
            idempotency_key="spine-native-retry",
        )
        first = submit_task(req, runtime, ctx)
        replay = submit_task(
            SpineRequest(
                "orchard", "aria", "ingest",
                {"text": "spine native memory", "step": 3, "supplied_embedding": [1.0, 0.0, 0.0]},
                idempotency_key="spine-native-retry",
            ),
            runtime, ctx,
        )
        assert first.ok and replay.ok and replay.result == first.result
        query = submit_task(
            SpineRequest("orchard", "aria", "query_memory", {"query": "spine native memory"}),
            runtime,
            RequestContext("r3-read", TRUST_READ_ONLY, "orchard", "aria"),
        )
        assert query.ok and "results" in query.result
    finally:
        close_public_runtime(root)


def test_mcp_uses_the_same_native_runtime_and_refuses_legacy_resources(tmp_path: Path, monkeypatch):
    import torment_service.mcp_server as mcp_module
    import torment_service.public_runtime as public_runtime

    monkeypatch.setattr(public_runtime, "TormentFabric", _NativeLaneFabric)
    root, _core, descriptor, profile, _agreement = _active_fixture(tmp_path)
    _prime_external_identity(root)
    legacy_calls = _forbid_legacy_core_memory(monkeypatch)
    old_fabric, old_context = mcp_module._fabric, mcp_module._client_ctx
    monkeypatch.setenv("TORMENT_MCP_DATA_DIR", str(root))
    monkeypatch.setenv("TORMENT_MCP_EXPOSURE_TIER", "open")
    try:
        configure_public_runtime(root, _configuration(root, descriptor, profile))
        mcp_module._fabric = None
        mcp_module._client_ctx = mcp_module.MCPClientContext(
            client_id="r3-mcp",
            trust_tier=TRUST_INGEST,
            default_workspace_id="orchard",
            default_agent_id="aria",
            session_id="r3-mcp-session",
        )
        missing = mcp_module._spine_call(
            "ingest", {"text": "mcp missing key", "supplied_embedding": [1.0, 0.0, 0.0]},
        )
        assert missing["ok"] is False and missing["decision_code"] == "blocked_native_public_operation"
        first = mcp_module._spine_call(
            "ingest",
            {"text": "mcp native memory", "step": 5, "supplied_embedding": [1.0, 0.0, 0.0]},
            idempotency_key="mcp-native-retry",
        )
        replay = mcp_module._spine_call(
            "ingest",
            {"text": "mcp native memory", "step": 5, "supplied_embedding": [1.0, 0.0, 0.0]},
            idempotency_key="mcp-native-retry",
        )
        assert first["ok"] and replay["ok"] and replay["result"] == first["result"]
        query = mcp_module._spine_call("query_memory", {"query": "mcp native memory"})
        assert query["ok"] and query["result"]["results"]
        assert mcp_module._get_fabric().mode is PublicRuntimeMode.NATIVE

        server = mcp_module.create_mcp_server()
        summary = next(
            template for uri, template in server._resource_manager._templates.items()
            if "memory-summary" in str(uri)
        )
        refused = json.loads(summary.fn("orchard", "aria"))
        assert refused["decision_code"] == "blocked_native_public_operation"
        assert legacy_calls == []
    finally:
        mcp_module._close_runtime()
        mcp_module._fabric, mcp_module._client_ctx = old_fabric, old_context
        reset_public_runtime_for_test(root)


def test_rest_native_transport_uses_one_configured_runtime(tmp_path: Path, monkeypatch):
    import torment_service.app as app_module
    import torment_service.public_runtime as public_runtime

    monkeypatch.setattr(public_runtime, "TormentFabric", _NativeLaneFabric)
    root, _core, descriptor, profile, _agreement = _active_fixture(tmp_path)
    _prime_external_identity(root)
    legacy_calls = _forbid_legacy_core_memory(monkeypatch)
    monkeypatch.setattr(app_module, "DATA_DIR", str(root))
    app_module.configure_app_public_runtime(_configuration(root, descriptor, profile))
    try:
        with TestClient(app_module.app) as client:
            missing = client.post("/agent/ingest", json={
                "workspace_id": "orchard", "agent_id": "aria", "text": "missing", "supplied_embedding": [1.0, 0.0, 0.0],
            })
            assert missing.status_code == 409
            first = client.post("/agent/ingest", headers={"Idempotency-Key": "rest-native-retry"}, json={
                "workspace_id": "orchard", "agent_id": "aria", "text": "rest native memory", "step": 11,
                "supplied_embedding": [1.0, 0.0, 0.0],
            })
            assert first.status_code == 200
            replay = client.post("/agent/ingest", headers={"Idempotency-Key": "rest-native-retry"}, json={
                "workspace_id": "orchard", "agent_id": "aria", "text": "rest native memory", "step": 11,
                "supplied_embedding": [1.0, 0.0, 0.0],
            })
            assert replay.status_code == 200 and replay.json() == first.json()
            native_fabric = app_module.fabric.runtime().cognition_fabric
            process_calls = 0
            original_process = native_fabric.kernel.process

            def _count_process(*args, **kwargs):
                nonlocal process_calls
                process_calls += 1
                return original_process(*args, **kwargs)

            monkeypatch.setattr(native_fabric.kernel, "process", _count_process)
            changed = client.post("/agent/ingest", headers={"Idempotency-Key": "rest-native-retry"}, json={
                "workspace_id": "orchard", "agent_id": "aria", "text": "changed rest meaning", "step": 11,
                "supplied_embedding": [1.0, 0.0, 0.0],
            })
            assert changed.status_code == 409 and process_calls == 0
            query = client.post("/agent/query", json={
                "workspace_id": "orchard", "agent_id": "aria", "query": "rest native memory",
            })
            assert query.status_code == 200 and "results" in query.json()
            retrieve = client.post("/retrieve", json={
                "workspace_id": "orchard", "agent_id": "aria", "query": "rest native memory",
            })
            assert retrieve.status_code == 200
            native_runtime = app_module.fabric.runtime()
            scoped_query_calls = 0

            def _refuse_scoped_query(*_args, **_kwargs):
                nonlocal scoped_query_calls
                scoped_query_calls += 1
                raise AssertionError("scoped native retrieve reached core query")

            monkeypatch.setattr(native_runtime, "query", _refuse_scoped_query)
            scoped_retrieve = client.post("/retrieve", json={
                "workspace_id": "orchard", "agent_id": "aria", "query": "rest native memory",
                "scope_tag": "legacy-reference-scope",
            })
            assert scoped_retrieve.status_code == 409
            assert scoped_retrieve.json()["detail"] == "native reference-load composition is not yet qualified"
            assert scoped_query_calls == 0
            refused = client.post("/agent/feedback", json={
                "workspace_id": "orchard", "agent_id": "aria",
            })
            assert refused.status_code == 409
            tool_missing = client.post("/tool/ingest", json={
                "workspace_id": "orchard", "agent_id": "aria",
                "tool_name": "r3", "content": "missing key",
                "supplied_embedding": [1.0, 0.0, 0.0],
            })
            assert tool_missing.status_code == 409
            assert client.get("/health").json()["public_memory_mode"] == "NATIVE"
            assert legacy_calls == []
    finally:
        reset_public_runtime_for_test(root)
