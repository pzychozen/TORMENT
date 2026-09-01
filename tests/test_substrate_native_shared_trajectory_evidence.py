"""D3 parity for external shared trajectory evidence."""
from __future__ import annotations

from dataclasses import replace
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.embeddings import HashEmbedding
from torment_service.memory_graph import MemoryGraph
from torment_service.post_write_runtime import FabricPostWriteContext, PostWriteStorageOutcome
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteRequest,
    NativeFabricRoutingScope,
    prepare_native_fabric_routing_capability,
)
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
    NativePostWriteRouteWitness,
    NativeSharedTrajectoryEvidenceBinding,
    prepare_native_fabric_post_write_adapter,
)
from torment_service.substrate.native_trajectory_evidence_runtime import (
    NativeTrajectoryEvidenceRuntime,
    resolve_trajectory_format,
)
from torment_service.substrate.native_world_runtime import NativeWorldProcessState, NativeWorldRuntime
from torment_service.substrate.runtime_binding import (
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
    prepare_native_memory_runtime_binding,
)
from torment_service.substrate.schema import create_schema
from torment_service.kernel.trajectory_v2 import (
    TrajectoryPathsV2,
    TrajectoryV2Verifier,
    iter_v2_dynamic_records,
)


def _id():
    return generate_native_id()


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane(
        "synthetic", "synthetic-v1", 3, "COMPAT_EMBEDDING", 1,
        "compat-embedding-v1", "RAW_VECTOR", "float32",
    )


def _shared_scope(connection) -> NativeFabricRoutingScope:
    memory_identity, semantic_scope, memory_alias = _id(), _id(), _id()
    motif_identity, membership_identity, motif_alias, idempotency = (_id() for _ in range(4))
    for value, label in (
        (memory_identity, "memory"), (motif_identity, "motif"), (membership_identity, "membership"),
    ):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"d3:{label}"),
        )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(semantic_scope), "d3:semantic"),
    )
    for value, label in ((memory_alias, "memory-alias"), (motif_alias, "motif-alias")):
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"d3:{label}"),
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "d3"))
    runtime_scope = NativeMemoryRuntimeScope(
        workspace_id="ws", scope_kind="SHARED_DOMAIN", legacy_source_namespace_id=memory_alias,
        identity_namespace_id=memory_identity, semantic_scope_id=semantic_scope, domain_id="research",
    )
    return NativeFabricRoutingScope(
        runtime_scope=runtime_scope, motif_alias_namespace_id=motif_alias,
        motif_identity_namespace_id=motif_identity, membership_identity_namespace_id=membership_identity,
        idempotency_namespace_id=idempotency,
    )


def _prepared(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "d3.db")
    metadata = create_schema(qualified.connection)
    scope = _shared_scope(qualified.connection)
    binding = prepare_native_memory_runtime_binding(
        connection=qualified.connection, core_database_path=qualified.database_path,
        expected_core_id=native_id_from_bytes(metadata.core_id), scope_bindings=(scope.runtime_scope,),
        representation_lane=_lane(),
    )
    capability = prepare_native_fabric_routing_capability(
        binding=binding, connection=qualified.connection, routing_scopes=(scope,),
        expected_core_id=native_id_from_bytes(metadata.core_id),
    )
    return qualified, qualified.connection, capability, scope


def _artifact_root(data_root: Path) -> Path:
    return data_root / "workspaces" / "ws" / "domains" / "research" / "shared"


def _configuration(data_root: Path, scope: NativeFabricRoutingScope):
    owner = SimpleNamespace(_log=logging.getLogger("d3.shared.owner"))
    workspace = SimpleNamespace(data_dir=str(data_root), domain_policies={"research": {}})
    return NativePostWriteQualificationConfiguration(
        routing_scope=scope,
        profile=NativePostWriteQualificationProfile.core_staging_with_shared_trajectory_evidence(),
        external=NativePostWriteExternalDependencies(
            owner=owner, workspace=workspace, identity=SimpleNamespace(seed={}), agent_key="aria",
            detect_canon_conflict=lambda *_args: (False, 0.0, "unused"),
            proposal_allowed=lambda *_args, **_kwargs: False,
            hivemind_log=logging.getLogger("d3.shared.hivemind"),
        ),
        derived_runtime_template=None, motif_suggestion_maintenance_required=False,
        persistent_trajectory_evidence_required=False, checkpoint_snapshots_required=False,
        bridge_suggestions_required=False, deep_memory_required=False,
        shared_trajectory_evidence_required=True,
        shared_trajectory_evidence_binding=NativeSharedTrajectoryEvidenceBinding(
            str(_artifact_root(data_root)), resolve_trajectory_format(),
        ),
    )


def _request(key: str = "D3:SOURCE") -> NativeFabricRouteRequest:
    return NativeFabricRouteRequest(
        workspace_id="ws", scope="shared", agent_id="aria", domain_id="research",
        native_operation_key=key, embedder_lane=_lane(), summary="trajectory parity source",
        memory_type="reflection", memory_class="core", strength=.8, confidence=.9,
        half_life_days=20., logical_step=1, created_ts=1, last_active_ts=1, last_reinforced_ts=1,
        incoming_embedding=(.2, .8, .1), provenance=ProvenanceV1.for_user_ingest(step=1),
        governance=MemoryGovernanceFlags(),
        flexible_payload={"seed_pos0": [3., 4., 0.], "seed_v0": [1., -.5, 2.]},
    )


def _context(result, request: NativeFabricRouteRequest, *, step: int = 1) -> FabricPostWriteContext:
    return FabricPostWriteContext.make(
        workspace_id="ws", agent_id="aria", scope="shared", chosen_domain="research", step=step,
        storage_outcome=PostWriteStorageOutcome.CREATED_NEW, stored=result.stored, eid=result.eid,
        created_motif=result.motifs[0], motif_ids=result.motifs, half_life_days=request.half_life_days,
        summary=request.summary, embedding=np.asarray(request.incoming_embedding, dtype=np.float32),
        memory_class=request.memory_class, memory_type=request.memory_type, strength=request.strength,
        confidence=request.confidence, promotion_score=0., stability_delta=0., tri_mod={}, debug={},
        srg_state=None, phase_durations={}, state_symbol=None, affect_tag=None, affect_conf=None,
        skip_packet_emission=True,
    )


def _counts(connection) -> tuple[int, ...]:
    tables = (
        "objects", "object_revisions", "relationships", "relationship_revisions", "representations",
        "operations", "semantic_transitions", "provenance_records", "object_revision_governance",
    )
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables)


def _trajectory_events(root: Path) -> list[dict[str, object]]:
    path = root / "memory_events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
            and json.loads(line).get("type") == "TRAJ_CLASSIFY"]


def _run_steps(adapter, result, request, *, first: int = 1, last: int = 50) -> None:
    for step in range(first, last + 1):
        adapter.run(
            _context(result, request, step=step),
            route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
        )


def _legacy_v2_trace(root: Path):
    with MemoryGraph(str(root), embedder=HashEmbedding()) as graph:
        eid = graph.add_memory(
            "trajectory parity source", np.asarray((.2, .8, .1), dtype=np.float32), "reflection", .8, .9, 20.,
            step=1, memory_class="core",
            extra_payload={"seed_pos0": [3., 4., 0.], "seed_v0": [1., -.5, 2.]},
        )
        for step in range(1, 51):
            graph.step_world(step, classify_every=50, log_every=1)
        entity = graph.entities[eid]
        label = entity.payload.get("traj_label")
    paths = TrajectoryPathsV2(root)
    genesis = [json.loads(line) for line in paths.genesis.read_text(encoding="utf-8").splitlines()]
    manifest = [json.loads(line) for line in paths.manifest.read_text(encoding="utf-8").splitlines()]
    return eid, label, genesis, manifest, list(iter_v2_dynamic_records(str(root))), _trajectory_events(root)


def _v2_semantics(root: Path):
    paths = TrajectoryPathsV2(root)
    genesis = [json.loads(line) for line in paths.genesis.read_text(encoding="utf-8").splitlines()]
    manifest = [json.loads(line) for line in paths.manifest.read_text(encoding="utf-8").splitlines()]
    rows = [
        (row["step"], row["frame_seq"], row["eid"], row["pos"], row["vel"])
        for row in iter_v2_dynamic_records(str(root))
    ]
    manifests = [
        (row["seq"], row["epoch"], row["frame_seq_from"], row["frame_seq_to"], row["frame_count"],
         row["step_from"], row["step_to"], row["record_count"], row["expected_record_count"],
         row["expected_population_min"], row["expected_population_max"])
        for row in manifest
    ]
    return genesis, manifests, rows, _trajectory_events(root)


def test_d3_shared_v2_trace_matches_legacy_and_never_mutates_native_memory(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TORMENT_TRAJECTORY_FORMAT", "v2")
    legacy_root = _artifact_root(tmp_path / "legacy")
    legacy_eid, legacy_label, legacy_genesis, legacy_manifest, legacy_rows, legacy_events = _legacy_v2_trace(legacy_root)

    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        request = _request()
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None and not result.reinforced
        adapter = prepare_native_fabric_post_write_adapter(
            capability=capability, configuration=_configuration(tmp_path / "native", scope),
        )
        before = _counts(connection)
        _run_steps(adapter, result, request)
        assert _counts(connection) == before
        native_root = _artifact_root(tmp_path / "native")
        # A live V2 tail is valid before close, and close seals that exact tail.
        assert TrajectoryV2Verifier(str(native_root)).verify(mode="live").valid
        adapter.close()
        report = TrajectoryV2Verifier(str(native_root)).verify(mode="sealed")
        assert report.valid, report.to_dict()

        native_genesis, native_manifest, native_rows, native_events = _v2_semantics(native_root)
        legacy_compact_rows = [
            (row["step"], row["frame_seq"], row["pos"], row["vel"])
            for row in legacy_rows
        ]
        legacy_compact_manifest = [
            (row["seq"], row["epoch"], row["frame_seq_from"], row["frame_seq_to"], row["frame_count"],
             row["step_from"], row["step_to"], row["record_count"], row["expected_record_count"],
             row["expected_population_min"], row["expected_population_max"])
            for row in legacy_manifest
        ]
        # Compatibility EIDs are serialized bare but scoped by each artifact
        # root.  Independent fixture allocators are intentionally not mapped.
        assert (legacy_eid, result.eid) == (1, 0)
        assert {row["eid"] for row in legacy_genesis} == {legacy_eid}
        assert {row["eid"] for row in native_genesis} == {result.eid}
        assert [{key: value for key, value in row.items() if key != "eid"} for row in native_genesis] == [
            {key: value for key, value in row.items() if key != "eid"} for row in legacy_genesis
        ]
        assert [(step, sequence, pos, vel) for step, sequence, _eid, pos, vel in native_rows] == legacy_compact_rows
        assert {row[2] for row in native_rows} == {result.eid}
        assert native_manifest == legacy_compact_manifest
        assert [(row["step"], row["traj_label"]) for row in native_events] == [
            (row["step"], row["traj_label"]) for row in legacy_events
        ]
        assert {row["eid"] for row in native_events} == {result.eid}
        assert {row["eid"] for row in legacy_events} == {legacy_eid}
        assert native_events and native_events[0]["step"] == 50

        snapshot = NativeWorldRuntime(
            connection, legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
            expected_dimension=3, process_state=capability.world_process_state,
        ).snapshot_for_testing()
        assert snapshot.classifications == ((legacy_label, 50),)
        durable = NativeMemoryCompatibilityFacade(connection).get_memory_by_eid(
            legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id, eid=result.eid,
        )
        assert "traj_label" not in durable.payload and "traj_last_classify_step" not in durable.payload
        assert not list(TrajectoryPathsV2(native_root).chunks.rglob("*.partial"))
    finally:
        qualified.close()


def test_d3_shared_legacy_jsonl_fallback_has_the_same_pre_classification_snapshot_order(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TORMENT_TRAJECTORY_FORMAT", "legacy")
    legacy_root = _artifact_root(tmp_path / "legacy")
    with MemoryGraph(str(legacy_root), embedder=HashEmbedding()) as graph:
        graph.add_memory(
            "trajectory parity source", np.asarray((.2, .8, .1), dtype=np.float32), "reflection", .8, .9, 20.,
            step=1, memory_class="core",
            extra_payload={"seed_pos0": [3., 4., 0.], "seed_v0": [1., -.5, 2.]},
        )
        for step in range(1, 51):
            graph.step_world(step, classify_every=50, log_every=1)
    legacy_log = next((legacy_root / "logs" / "trajectories" / "daily").glob("*.jsonl"))
    legacy_rows = [json.loads(line) for line in legacy_log.read_text(encoding="utf-8").splitlines()]

    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        request = _request("D3:LEGACY")
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None
        adapter = prepare_native_fabric_post_write_adapter(
            capability=capability, configuration=_configuration(tmp_path / "native", scope),
        )
        _run_steps(adapter, result, request)
        adapter.close()
        native_root = _artifact_root(tmp_path / "native")
        native_log = next((native_root / "logs" / "trajectories" / "daily").glob("*.jsonl"))
        native_rows = [json.loads(line) for line in native_log.read_text(encoding="utf-8").splitlines()]
        for row in (*legacy_rows, *native_rows):
            row.pop("ts")
        assert [(row["step"], row["born_step"], row["channel"], row["alive"], row["pos"], row["vel"],
                row["vel0"], row["traj_label"], row["traj_last_classify_step"]) for row in native_rows] == [
            (row["step"], row["born_step"], row["channel"], row["alive"], row["pos"], row["vel"],
             row["vel0"], row["traj_label"], row["traj_last_classify_step"]) for row in legacy_rows
        ]
        assert {row["eid"] for row in native_rows} == {result.eid}
        assert {row["eid"] for row in legacy_rows} == {1}
        # Snapshot serialization happens before the step-50 classification update.
        assert native_rows[-1]["step"] == 50 and native_rows[-1]["traj_label"] is None
        events = _trajectory_events(native_root)
        assert [(event["step"], event["eid"]) for event in events] == [(50, result.eid)]
        assert not TrajectoryPathsV2(native_root).base.exists()
    finally:
        qualified.close()


def test_d3_close_restart_and_external_failures_are_fail_soft(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TORMENT_TRAJECTORY_FORMAT", "v2")
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        request = _request("D3:FAILURES")
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None
        adapter = prepare_native_fabric_post_write_adapter(
            capability=capability, configuration=_configuration(tmp_path / "native", scope),
        )
        before = _counts(connection)

        # Each legacy writer boundary is independently fail-soft: physics and
        # the in-process classification still continue, while SQLite is fixed.
        with monkeypatch.context() as faults:
            faults.setattr(NativeTrajectoryEvidenceRuntime, "write_genesis", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("genesis")))
            faults.setattr(NativeTrajectoryEvidenceRuntime, "write_step", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("frame")))
            faults.setattr(NativeTrajectoryEvidenceRuntime, "write_classification_event", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("event")))
            _run_steps(adapter, result, request, first=50, last=50)
        assert _counts(connection) == before
        live = NativeWorldRuntime(
            connection, legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
            expected_dimension=3, process_state=capability.world_process_state,
        ).snapshot_for_testing()
        assert live.trail_lengths == (2,) and live.history_lengths == (2,)
        assert live.classifications[0] is not None and live.classifications[0][1] == 50

        # A V2 close/seal failure is also diagnostic-only.  Restore it before
        # teardown so the open tail can be sealed for Windows cleanup.
        evidence = adapter._shared_trajectory_evidence
        assert evidence is not None
        original_close = evidence._writer.close
        monkeypatch.setattr(evidence._writer, "close", lambda: (_ for _ in ()).throw(OSError("close")))
        adapter.close()
        assert _counts(connection) == before
        monkeypatch.setattr(evidence._writer, "close", original_close)
        adapter.close()

        # Restart reads current native source payload, never the previous live
        # world coordinates or its classification overlay.  Evidence remains
        # independently readable and has no restorative authority.
        restarted = NativeWorldRuntime(
            connection, legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
            expected_dimension=3, process_state=NativeWorldProcessState(),
        )
        restarted.ensure_initialized()
        restart_snapshot = restarted.snapshot_for_testing()
        assert restart_snapshot.positions == ((3.0, 4.0, 0.0),)
        assert restart_snapshot.history_lengths == (0,) and restart_snapshot.classifications == (None,)
        assert _counts(connection) == before

        # An empty V2 lifecycle writes no semantic frame and has no tail to
        # seal; this is the same no-op close result as the legacy writer.
        empty_root = _artifact_root(tmp_path / "empty")
        empty = NativeTrajectoryEvidenceRuntime(root_dir=str(empty_root), trajectory_format="v2")
        empty.close()
        assert TrajectoryV2Verifier(str(empty_root)).verify(mode="sealed").valid
    finally:
        qualified.close()


def test_d3_chunk_manifest_close_failure_does_not_rollback_world_or_native_memory(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TORMENT_TRAJECTORY_FORMAT", "v2")
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        request = _request("D3:MANIFEST")
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None
        adapter = prepare_native_fabric_post_write_adapter(
            capability=capability, configuration=_configuration(tmp_path / "native", scope),
        )
        before = _counts(connection)
        _run_steps(adapter, result, request, first=1, last=1)
        evidence = adapter._shared_trajectory_evidence
        assert evidence is not None
        import torment_service.kernel.trajectory_v2 as trajectory_v2

        with monkeypatch.context() as faults:
            faults.setattr(trajectory_v2, "_append_jsonl", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("manifest")))
            adapter.close()
        assert _counts(connection) == before
        snapshot = NativeWorldRuntime(
            connection, legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
            expected_dimension=3, process_state=capability.world_process_state,
        ).snapshot_for_testing()
        assert snapshot.positions != ((3.0, 4.0, 0.0),) and snapshot.history_lengths == (2,)
        # The chunk may be physically closed before manifest append fails, but
        # it never gains native authority or causes a compensating mutation.
        assert (TrajectoryPathsV2(_artifact_root(tmp_path / "native")).manifest).exists() is False
    finally:
        qualified.close()


def test_d3_configuration_refuses_profile_composition_and_wrong_artifact_owner(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TORMENT_TRAJECTORY_FORMAT", "v2")
    qualified, _connection, capability, scope = _prepared(tmp_path)
    try:
        configuration = _configuration(tmp_path / "native", scope)
        with pytest.raises(Exception, match="prepared separately"):
            prepare_native_fabric_post_write_adapter(
                capability=capability,
                configuration=replace(configuration, shared_hivemind_packet_emission_required=True),
            )
        with pytest.raises(Exception, match="does not match the claimed shared domain"):
            prepare_native_fabric_post_write_adapter(
                capability=capability,
                configuration=replace(
                    configuration,
                    shared_trajectory_evidence_binding=NativeSharedTrajectoryEvidenceBinding(
                        str(tmp_path / "wrong"), "v2",
                    ),
                ),
            )
    finally:
        qualified.close()
