"""D4 parity for the external shared-trigger checkpoint snapshot."""
from __future__ import annotations

from dataclasses import asdict, replace
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from torment_service.character import CharacterState
from torment_service.checkpoint import (
    CheckpointContainmentError,
    _build_checkpoint_dir,
    build_motif_summary,
    load_latest_checkpoint,
    save_checkpoint,
    serialize_corridor_monitor,
    serialize_kernel_runtime_context,
    serialize_model_state,
)
from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.cognitive_core import CognitiveCoreState
from torment_service.memory_kernel import TriOctaMemoryKernel
from torment_service.post_write_runtime import FabricPostWriteContext, PostWriteStorageOutcome
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteRequest,
    NativeFabricRoutingScope,
    prepare_native_fabric_routing_capability,
)
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
    NativePostWriteRouteWitness,
    NativeSharedCheckpointSnapshotBinding,
    prepare_native_fabric_post_write_adapter,
)
from torment_service.substrate.runtime_binding import (
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
    prepare_native_memory_runtime_binding,
)
from torment_service.substrate.schema import create_schema


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
            (native_id_to_bytes(value), f"d4:{label}"),
        )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(semantic_scope), "d4:semantic"),
    )
    for value, label in ((memory_alias, "memory-alias"), (motif_alias, "motif-alias")):
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"d4:{label}"),
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "d4"))
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
    qualified = open_temporary_test_connection(tmp_path / "d4.db")
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


class _CharacterStore:
    def __init__(self, state: CharacterState | None) -> None:
        self.state = state
        self.calls: list[tuple[str, str]] = []

    def load_state(self, workspace_id: str, agent_id: str) -> CharacterState | None:
        self.calls.append((workspace_id, agent_id))
        return self.state


class _Owner:
    def __init__(self, data_dir: Path, *, interval: int = 10, keep: int = 2) -> None:
        self._log = logging.getLogger("d4.shared.owner")
        self.data_dir = str(data_dir)
        self._checkpoint_enable = True
        self._checkpoint_interval = interval
        self._checkpoint_max_keep = keep


def _live_kernel():
    kernel = TriOctaMemoryKernel()
    state = kernel.init_state("ws/aria")
    context = kernel.new_runtime_context()
    context.mon.coh_ema = .81
    context.mon.surv_ema = .72
    context.disp_buffer[:] = [.1, .2, .3]
    context.last_effective_scale = 1.5
    context.cognitive_state = CognitiveCoreState(z_mem=.031, z_identity=.42, identity_state=5)
    return state, context


def _configuration(
    data_root: Path,
    scope: NativeFabricRoutingScope,
    *,
    model_state=None,
    kernel_runtime_context=None,
    character_store: _CharacterStore | None = None,
    interval: int = 10,
    keep: int = 2,
):
    state, runtime_context = _live_kernel()
    owner = _Owner(data_root, interval=interval, keep=keep)
    character_store = character_store or _CharacterStore(
        CharacterState("ws", "aria", "seed-1", drift_score=.25, drift_history=[(3, .25)]),
    )
    return (
        NativePostWriteQualificationConfiguration(
            routing_scope=scope,
            profile=NativePostWriteQualificationProfile.core_staging_with_shared_checkpoint_snapshot(),
            external=NativePostWriteExternalDependencies(
                owner=owner, workspace=SimpleNamespace(domain_policies={"research": {}}),
                identity=SimpleNamespace(seed={}), agent_key="ws/aria",
                detect_canon_conflict=lambda *_args: (False, 0.0, "unused"),
                proposal_allowed=lambda *_args, **_kwargs: False,
                hivemind_log=logging.getLogger("d4.shared.hivemind"),
                character_store=character_store,
            ),
            derived_runtime_template=None, motif_suggestion_maintenance_required=False,
            persistent_trajectory_evidence_required=False, checkpoint_snapshots_required=False,
            bridge_suggestions_required=False, deep_memory_required=False,
            shared_checkpoint_snapshot_required=True,
            shared_checkpoint_snapshot_binding=NativeSharedCheckpointSnapshotBinding(
                state if model_state is None else model_state,
                runtime_context if kernel_runtime_context is None else kernel_runtime_context,
            ),
        ),
        owner,
        character_store,
    )


def _request(key: str = "D4:SOURCE") -> NativeFabricRouteRequest:
    return NativeFabricRouteRequest(
        workspace_id="ws", scope="shared", agent_id="aria", domain_id="research",
        native_operation_key=key, embedder_lane=_lane(), summary="checkpoint source",
        memory_type="reflection", memory_class="core", strength=.8, confidence=.9,
        half_life_days=20., logical_step=1, created_ts=1, last_active_ts=1, last_reinforced_ts=1,
        incoming_embedding=(.2, .8, .1), provenance=ProvenanceV1.for_user_ingest(step=1),
        governance=MemoryGovernanceFlags(), flexible_payload={},
    )


def _context(result, request: NativeFabricRouteRequest, *, step: int) -> FabricPostWriteContext:
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


def _no_write_context(*, step: int) -> FabricPostWriteContext:
    return FabricPostWriteContext.make(
        workspace_id="ws", agent_id="aria", scope="shared", chosen_domain="research", step=step,
        storage_outcome=PostWriteStorageOutcome.NO_WRITE, stored=False, eid=None, created_motif=None,
        motif_ids=(), half_life_days=None, summary="no write", embedding=np.zeros(3, dtype=np.float32),
        memory_class="core", memory_type="reflection", strength=0., confidence=0.,
        promotion_score=0., stability_delta=0., tri_mod={}, debug={}, srg_state=None,
        phase_durations={}, state_symbol=None, affect_tag=None, affect_conf=None, skip_packet_emission=True,
    )


def _counts(connection) -> tuple[int, ...]:
    tables = (
        "objects", "object_revisions", "relationships", "relationship_revisions", "representations",
        "operations", "semantic_transitions", "provenance_records", "object_revision_governance",
    )
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables)


def _native_motif_summary(connection, scope: NativeFabricRoutingScope):
    reader = NativeMotifRuntimeReader(connection)
    motifs = reader.list_runtime_motifs(
        motif_alias_namespace_id=scope.motif_alias_namespace_id,
        domain_id="research", semantic_scope_id=scope.runtime_scope.semantic_scope_id,
    )
    # This fixture is a reference shape only.  D4 itself must read the same
    # current native motifs, not this projection or a legacy registry.
    projection = SimpleNamespace(motifs={
        item.read_model.runtime_motif_id: SimpleNamespace(
            motif_id=item.read_model.runtime_motif_id,
            label=item.read_model.label,
            strength=item.read_model.strength,
            members=range(item.read_model.member_count),
        )
        for item in motifs
    })
    return build_motif_summary(projection)


def _run(adapter, result, request, *, step: int) -> None:
    adapter.run(
        _context(result, request, step=step),
        route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
    )


def test_d4_shared_checkpoint_uses_native_motifs_and_existing_snapshot_schema(tmp_path: Path):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        request = _request()
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None
        configuration, owner, character_store = _configuration(tmp_path / "native", scope)
        adapter = prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)
        expected_motifs = _native_motif_summary(connection, scope)
        before = _counts(connection)
        binding = configuration.shared_checkpoint_snapshot_binding
        assert binding is not None
        model_before = serialize_model_state(binding.model_state)
        monitor_before = serialize_corridor_monitor(binding.kernel_runtime_context.mon)
        context_before = serialize_kernel_runtime_context(binding.kernel_runtime_context)

        _run(adapter, result, request, step=9)
        assert load_latest_checkpoint(owner.data_dir, "ws", "aria") is None
        _run(adapter, result, request, step=10)
        payload = load_latest_checkpoint(owner.data_dir, "ws", "aria")
        assert payload is not None
        assert payload["version"] == 3 and payload["step"] == 10
        assert payload["model_state"] == {
            **serialize_model_state(binding.model_state),
            "z_mem": .031,
        }
        assert payload["corridor_monitor"] == serialize_corridor_monitor(binding.kernel_runtime_context.mon)
        assert payload["kernel_runtime_context"] == serialize_kernel_runtime_context(binding.kernel_runtime_context)
        serialized_character = json.loads(json.dumps(asdict(character_store.state)))
        assert payload["character_state"] == serialized_character
        assert payload["motif_summary"] == expected_motifs
        assert payload["shard_snapshot"] is None
        assert character_store.calls == [("ws", "aria")]
        assert serialize_model_state(binding.model_state) == model_before
        assert serialize_corridor_monitor(binding.kernel_runtime_context.mon) == monitor_before
        assert serialize_kernel_runtime_context(binding.kernel_runtime_context) == context_before
        assert _counts(connection) == before
        assert _build_checkpoint_dir(owner.data_dir, "ws", "aria").endswith(
            "workspaces\\ws\\agents\\aria\\private\\checkpoints"
        )

        # The same legacy writer schema is retained.  A legacy shard manifest
        # may be supplied there; native deliberately preserves its absence.
        legacy_root = tmp_path / "legacy"
        legacy_path = save_checkpoint(
            data_dir=str(legacy_root), workspace_id="ws", agent_id="aria", step=10,
            model_state=binding.model_state, corridor_monitor=binding.kernel_runtime_context.mon,
            kernel_runtime_context=binding.kernel_runtime_context,
            character_state_dict=asdict(character_store.state), motif_summary=expected_motifs,
            shard_snapshot={"active_shard": 2, "next_row": 9, "total_rows": 11, "embedding_dim": 3},
        )
        assert legacy_path is not None
        legacy = load_latest_checkpoint(str(legacy_root), "ws", "aria")
        assert legacy is not None
        for key in ("version", "step", "model_state", "corridor_monitor", "kernel_runtime_context", "character_state", "motif_summary"):
            assert payload[key] == legacy[key]
        assert legacy["shard_snapshot"] is not None and payload["shard_snapshot"] is None
    finally:
        qualified.close()


def test_d4_character_snapshot_preserves_existing_absent_none_behavior(tmp_path: Path):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        request = _request("D4:CHARACTER-ABSENT")
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None
        character_store = _CharacterStore(None)
        configuration, owner, _ = _configuration(
            tmp_path / "native", scope, character_store=character_store,
        )
        adapter = prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)
        before = _counts(connection)
        _run(adapter, result, request, step=10)
        payload = load_latest_checkpoint(owner.data_dir, "ws", "aria")
        assert payload is not None and payload["character_state"] is None
        assert character_store.calls == [("ws", "aria")]
        assert _counts(connection) == before
    finally:
        qualified.close()


def test_d4_checkpoint_reaches_no_write_gate_retains_latest_and_load_stays_non_authoritative(tmp_path: Path):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        request = _request("D4:RETENTION")
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None
        configuration, owner, _character_store = _configuration(tmp_path / "native", scope, interval=5, keep=2)
        adapter = prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)
        before = _counts(connection)
        for step in (5, 10, 15):
            _run(adapter, result, request, step=step)
        # Legacy reaches checkpoint for all outcomes; D4 retains that gate.
        adapter.run(_no_write_context(step=20))
        checkpoint_dir = Path(_build_checkpoint_dir(owner.data_dir, "ws", "aria"))
        names = sorted(path.name for path in checkpoint_dir.glob("checkpoint_*.json"))
        assert names == ["checkpoint_000015.json", "checkpoint_000020.json"]
        assert _counts(connection) == before

        # Current loader returns None rather than falling back when the newest
        # candidate is corrupt; neither missing nor corrupt load changes SQLite.
        (checkpoint_dir / names[-1]).write_text("{", encoding="utf-8")
        assert load_latest_checkpoint(owner.data_dir, "ws", "aria") is None
        assert load_latest_checkpoint(owner.data_dir, "ws", "missing") is None
        assert _counts(connection) == before
    finally:
        qualified.close()


def test_d4_checkpoint_component_and_writer_failures_remain_fail_soft(tmp_path: Path, monkeypatch):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        request = _request("D4:FAILURES")
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None
        configuration, owner, _character_store = _configuration(tmp_path / "native", scope)
        adapter = prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)
        before = _counts(connection)

        with monkeypatch.context() as faults:
            faults.setattr(adapter, "_build_native_checkpoint_motif_summary", lambda *_args: (_ for _ in ()).throw(OSError("motif")))
            _run(adapter, result, request, step=10)
        motif_failed = load_latest_checkpoint(owner.data_dir, "ws", "aria")
        assert motif_failed is not None and motif_failed["motif_summary"] is None
        assert _counts(connection) == before

        # Serialization and ordinary filesystem errors are returned/absorbed by
        # the existing external writer and never roll back native source state.
        broken_configuration, broken_owner, _ = _configuration(
            tmp_path / "serialization", scope, model_state=object(),
        )
        broken = prepare_native_fabric_post_write_adapter(capability=capability, configuration=broken_configuration)
        _run(broken, result, request, step=10)
        assert load_latest_checkpoint(broken_owner.data_dir, "ws", "aria") is None
        with monkeypatch.context() as faults:
            import torment_service.substrate.native_post_write_runtime as post_runtime

            faults.setattr(post_runtime, "save_checkpoint", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("filesystem")))
            _run(adapter, result, request, step=20)
        assert _counts(connection) == before

        # The checkpoint writer preserves its special containment error, while
        # the legacy-shaped post-write outer boundary logs it and continues.
        with monkeypatch.context() as faults:
            import torment_service.substrate.native_post_write_runtime as post_runtime

            faults.setattr(post_runtime, "save_checkpoint", lambda *_args, **_kwargs: (_ for _ in ()).throw(CheckpointContainmentError("containment")))
            _run(adapter, result, request, step=30)
        assert _counts(connection) == before
    finally:
        qualified.close()


def test_d4_refuses_profile_composition_and_requires_the_existing_character_store_interface(tmp_path: Path):
    qualified, _connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, _owner, _character_store = _configuration(tmp_path / "native", scope)
        with pytest.raises(Exception, match="prepared separately"):
            prepare_native_fabric_post_write_adapter(
                capability=capability,
                configuration=replace(configuration, shared_trajectory_evidence_required=True),
            )
        with pytest.raises(Exception, match="CharacterStore"):
            prepare_native_fabric_post_write_adapter(
                capability=capability,
                configuration=replace(
                    configuration,
                    external=replace(configuration.external, character_store=None),
                ),
            )
    finally:
        qualified.close()
