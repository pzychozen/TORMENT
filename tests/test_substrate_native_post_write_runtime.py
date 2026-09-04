"""A3D10 qualification for the explicit native Fabric post-write adapter."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.motif_maintenance import NativeMotifMaintenanceAdapter
from torment_service.post_write_runtime import (
    FabricPostWriteContext,
    LegacyFabricPostWriteAdapter,
    PostWriteStorageOutcome,
)
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.connection import open_existing_native_core_connection, open_temporary_test_connection
from torment_service.substrate.errors import SubstrateConfigurationError, SubstrateInvariantViolation
from torment_service.substrate.fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteRequest,
    NativeFabricRoutingScope,
    prepare_native_fabric_routing_capability,
)
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntimeConfiguration
from torment_service.substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntime
from torment_service.substrate.native_post_write_runtime import (
    NativeFabricPostWriteAdapter,
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
    NativePostWriteRouteWitness,
    prepare_native_fabric_post_write_adapter,
)
from torment_service.substrate.native_memory_runtime_access import NativePostWriteMemoryAccess
from torment_service.substrate.native_srg_runtime import NativeSRGTransientRuntime
from torment_service.substrate.native_world_runtime import NativeWorldRuntime
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
        provider="synthetic", model="synthetic-v1", dimension=3,
        representation_class="COMPAT_EMBEDDING", generation=1,
        derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR", dtype="float32",
    )


def _prepared(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "a3d10-staging.db")
    metadata = create_schema(qualified.connection)
    connection = qualified.connection
    memory_identity, semantic_scope, memory_alias = _id(), _id(), _id()
    motif_identity, membership_identity, motif_alias, idempotency = (_id() for _ in range(4))
    for value, label in (
        (memory_identity, "memory"), (motif_identity, "motif"), (membership_identity, "membership"),
    ):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), label))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(semantic_scope), "private"))
    for value, label in ((memory_alias, "memory-alias"), (motif_alias, "motif-alias")):
        connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), label))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "idempotency"))
    runtime_scope = NativeMemoryRuntimeScope(
        workspace_id="ws", scope_kind="PRIVATE_AGENT", legacy_source_namespace_id=memory_alias,
        identity_namespace_id=memory_identity, semantic_scope_id=semantic_scope, agent_id="aria",
    )
    routing_scope = NativeFabricRoutingScope(
        runtime_scope=runtime_scope, motif_alias_namespace_id=motif_alias,
        motif_identity_namespace_id=motif_identity, membership_identity_namespace_id=membership_identity,
        idempotency_namespace_id=idempotency,
    )
    binding = prepare_native_memory_runtime_binding(
        connection=connection, core_database_path=qualified.database_path,
        expected_core_id=native_id_from_bytes(metadata.core_id),
        scope_bindings=(runtime_scope,), representation_lane=_lane(),
    )
    capability = prepare_native_fabric_routing_capability(
        binding=binding, connection=connection, routing_scopes=(routing_scope,),
        expected_core_id=native_id_from_bytes(metadata.core_id),
    )
    return qualified, connection, capability, routing_scope


class _SideStore:
    def __init__(self) -> None:
        self.anchor = {"motifs": {}}
        self.affect = {"last_tag": None, "last_conf": 0.0, "last_step": -10**9, "drift_hist": []}
        self.events: list[str] = []

    def load_anchor_state(self, **_kwargs):
        return json.loads(json.dumps(self.anchor))

    def save_anchor_state(self, *, state, **_kwargs):
        self.anchor = json.loads(json.dumps(state))
        self.events.append("anchor")

    def load_affect_state(self, **_kwargs):
        return json.loads(json.dumps(self.affect))

    def save_affect_state(self, *, state, **_kwargs):
        self.affect = json.loads(json.dumps(state))
        self.events.append("affect")


class _ConflictRegistry:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def add(self, **kwargs) -> None:
        self.calls.append(kwargs)


class _CollectiveField:
    def __init__(self) -> None:
        self.packets = []

    def append_packet(self, packet, *, embedding):
        self.packets.append((packet, np.asarray(embedding).copy()))
        return None


class _ProposalRegistry:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def submit(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(proposal_id=f"proposal-{len(self.calls)}")


class _IdentityStore:
    def __init__(self) -> None:
        self.saved = 0

    def save(self, _identity) -> None:
        self.saved += 1


class _ProposalBridge:
    def __init__(self) -> None:
        self.calls = 0

    def maybe_draft_proposal(self, **_kwargs) -> None:
        self.calls += 1


class _Owner:
    def __init__(self) -> None:
        self._log = logging.getLogger("a3d10.owner")
        self._srg_enable = True
        self._hivemind_enable = True
        self._hivemind_telemetry_enable = True
        self._character_enable = False
        self._character_drift_every = 1
        self._last_drift_was_high = {}
        self.drift_reflex_callback = None
        self._compress_enable = False
        self._compress_min_step = 0
        self._checkpoint_enable = False
        self._checkpoint_interval = 1
        self.character_store = SimpleNamespace(load_state=lambda *_args: None)
        self.ident_store = _IdentityStore()
        self.field = _CollectiveField()
        self.bridge = _ProposalBridge()
        self.telemetry: list[dict[str, object]] = []

    def _get_collective_field(self, _workspace_id):
        return self.field

    def _get_proposal_bridge(self, _workspace_id):
        return self.bridge

    def _emit_hivemind_packet_telemetry(self, **kwargs) -> None:
        self.telemetry.append(kwargs)


class _CharacterEmbedder:
    provider = "synthetic"
    model = "synthetic-v1"
    dim = 3

    def embed(self, _text: str):
        return np.asarray((2.0, 0.6, 0.0), dtype=np.float32)


def _environment(scope):
    side = _SideStore()
    owner = _Owner()
    conflicts = _ConflictRegistry()
    proposals = _ProposalRegistry()
    workspace = SimpleNamespace(
        domain_policies={"personal": {"auto_merge_motifs": False}},
        conflicts={"personal": conflicts}, proposals={"personal": proposals},
    )
    identity = SimpleNamespace(seed={"coupling_mode": "propose"})
    template = NativeDerivedMemoryRuntimeConfiguration(
        workspace_id="ws", agent_id="aria", domain_id="personal",
        legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
        motif_alias_namespace_id=scope.motif_alias_namespace_id,
        memory_identity_namespace_id=scope.runtime_scope.identity_namespace_id,
        semantic_scope_id=scope.runtime_scope.semantic_scope_id,
        idempotency_namespace_id=scope.idempotency_namespace_id,
        parent_native_operation_key="template-never-used", expected_dimension=3,
        embed=lambda _text: np.asarray((2.0, 0.6, 0.0), dtype=np.float32),
        embedder_provider="synthetic", embedder_model="synthetic-v1", side_store=side,
        seed_eids=(0, 1), now_ts=lambda: 500,
    )
    configuration = NativePostWriteQualificationConfiguration(
        routing_scope=scope, profile=NativePostWriteQualificationProfile.core_staging(),
        external=NativePostWriteExternalDependencies(
            owner=owner, workspace=workspace, identity=identity, agent_key="aria",
            detect_canon_conflict=lambda *_args: (True, 0.97, "qualified-fixture"),
            proposal_allowed=lambda *_args, **_kwargs: True,
            hivemind_log=logging.getLogger("a3d10.hivemind"),
        ),
        derived_runtime_template=template, motif_suggestion_maintenance_required=False,
        persistent_trajectory_evidence_required=False, checkpoint_snapshots_required=False,
        bridge_suggestions_required=False, deep_memory_required=False,
    )
    return configuration, owner, workspace, identity, side, conflicts, proposals


def _request(key: str, step: int, *, vector=(2.0, 0.6, 0.0)) -> NativeFabricRouteRequest:
    return NativeFabricRouteRequest(
        workspace_id="ws", scope="private", agent_id="aria", domain_id="personal",
        native_operation_key=key, embedder_lane=_lane(), summary=f"qualified {key}",
        memory_type="reflection", memory_class="core", strength=0.8, confidence=0.9,
        half_life_days=20.0, logical_step=step, created_ts=step, last_active_ts=step,
        last_reinforced_ts=step, incoming_embedding=vector,
        provenance=ProvenanceV1.for_user_ingest(step=step), governance=MemoryGovernanceFlags(),
        flexible_payload={
            "qualification": "a3d10",
            "srg": {"R": 0.10, "R_band": 0, "heartbeat_class": "A", "last_collision_step": -1},
        },
    )


def _context(result, request: NativeFabricRouteRequest, *, outcome=None, **changes) -> FabricPostWriteContext:
    values = {
        "workspace_id": "ws", "agent_id": "aria", "scope": "private", "chosen_domain": "personal",
        "step": request.logical_step,
        "storage_outcome": outcome or (
            PostWriteStorageOutcome.REINFORCED_EXISTING if result.reinforced else PostWriteStorageOutcome.CREATED_NEW
        ),
        "stored": result.stored, "eid": result.eid,
        "created_motif": result.motifs[0] if not result.reinforced else None,
        "motif_ids": result.motifs, "half_life_days": request.half_life_days,
        "summary": request.summary, "embedding": np.asarray(request.incoming_embedding, dtype=np.float32),
        "memory_class": request.memory_class, "memory_type": request.memory_type,
        "strength": request.strength, "confidence": request.confidence,
        "promotion_score": 0.9, "stability_delta": 0.1,
        "tri_mod": {"cycle_stage": "stable", "identity_state": "coherent"},
        "debug": {"coherence": 0.8},
        "srg_state": request.flexible_payload["srg"], "phase_durations": {},
        "state_symbol": "s", "affect_tag": None, "affect_conf": None,
        "skip_packet_emission": False,
    }
    values.update(changes)
    return FabricPostWriteContext.make(**values)


def _no_write_context(step: int) -> FabricPostWriteContext:
    return FabricPostWriteContext.make(
        workspace_id="ws", agent_id="aria", scope="private", chosen_domain="personal", step=step,
        storage_outcome=PostWriteStorageOutcome.NO_WRITE, stored=False, eid=None, created_motif=None,
        motif_ids=(), half_life_days=None, summary="no write", embedding=np.asarray((2.0, 0.6, 0.0), dtype=np.float32),
        memory_class="core", memory_type="reflection", strength=0.0, confidence=0.0,
        promotion_score=0.0, stability_delta=0.0, tri_mod={}, debug={}, srg_state=None,
        phase_durations={}, state_symbol=None, affect_tag=None, affect_conf=None, skip_packet_emission=True,
    )


def _counts(connection):
    tables = (
        "objects", "object_revisions", "legacy_object_aliases", "memory_runtime_enumeration_orders",
        "provenance_records", "object_revision_governance", "relationships", "relationship_revisions",
        "representations", "representation_payloads", "operations", "semantic_transitions",
        "object_revision_effects", "relationship_revision_effects",
    )
    return {table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables}


def _world(connection, capability, scope):
    return NativeWorldRuntime(
        connection, legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
        expected_dimension=3, process_state=capability.world_process_state,
    ).snapshot_for_testing()


def _adapter(capability, configuration):
    return prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)


def test_adapter_requires_explicit_preparation_and_does_not_grant_activation(tmp_path: Path):
    _qualified, _connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, *_rest = _environment(scope)
        with pytest.raises(SubstrateConfigurationError, match="explicitly prepared"):
            NativeFabricPostWriteAdapter(capability, configuration)
        adapter = _adapter(capability, configuration)
        assert not hasattr(adapter, "_connection")
        assert capability.production_activation_allowed is False
        assert capability.qualification_only is True
    finally:
        _qualified.close()


def test_explicit_character_profile_admits_only_the_native_character_slot(tmp_path: Path):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, owner, _workspace, identity, _side, _conflicts, _proposals = _environment(scope)
        owner._character_enable = True
        identity.seed["seed_id"] = "unavailable"
        character_store = SimpleNamespace(
            load_seed=lambda *_args: None,
            load_state=lambda *_args: None,
            save_state=lambda *_args, **_kwargs: None,
        )
        configuration = replace(
            configuration,
            profile=NativePostWriteQualificationProfile.core_staging_with_character(),
            external=replace(
                configuration.external,
                character_store=character_store,
                character_embedder=_CharacterEmbedder(),
            ),
        )
        request = _request("character-profile", 1)
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None
        before = _counts(connection)
        _adapter(capability, configuration).run(
            _context(result, request),
            route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
        )
        assert _counts(connection) == before
        assert configuration.profile.character.name == "QUALIFIED"
        assert NativePostWriteQualificationProfile.core_staging().character.name == "UNSUPPORTED"
    finally:
        qualified.close()


def test_created_new_runs_the_qualified_native_core_in_frozen_order(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "1.1")
    monkeypatch.setenv("TORMENT_ID_ANCHOR_MIN_COUNT", "3")
    monkeypatch.setenv("TORMENT_ID_ANCHOR_MIN_GAP_STEPS", "0")
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, owner, _workspace, _identity, side, conflicts, proposals = _environment(scope)
        router = NativeFabricMemoryRouter(capability)
        routed = []
        for step in range(1, 4):
            request = _request(f"created-{step}", step)
            result = router.route(request).result
            assert result is not None and result.reinforced is False
            routed.append((result, request))
        result, request = routed[-1]
        before = _counts(connection)
        before_world = _world(connection, capability, scope)
        outcome = _adapter(capability, configuration).run(
            _context(result, request),
            route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
        )
        after = _counts(connection)
        after_world = _world(connection, capability, scope)
        assert outcome.proposal_id == "proposal-1"
        assert len(conflicts.calls) == 1
        assert len(owner.field.packets) == 1 and owner.telemetry[-1]["gate_outcome"] == "emitted"
        assert side.events == ["anchor"]
        assert len(proposals.calls) == 1 and owner.ident_store.saved == 1
        # The only native durable delta is the explicitly qualified derived
        # anchor: one row family plus its documented membership effects.
        assert after["objects"] == before["objects"] + 1
        assert after["object_revisions"] == before["object_revisions"] + 1
        assert after["representations"] == before["representations"] + 1
        assert after["representation_payloads"] == before["representation_payloads"] + 1
        assert after["memory_runtime_enumeration_orders"] == before["memory_runtime_enumeration_orders"] + 1
        assert after["operations"] == before["operations"] + 4
        assert after["semantic_transitions"] == before["semantic_transitions"] + 3
        assert after["object_revision_effects"] == before["object_revision_effects"] + 1
        assert after["relationships"] == before["relationships"]
        assert after["relationship_revisions"] == before["relationship_revisions"]
        assert after["relationship_revision_effects"] == before["relationship_revision_effects"]
        assert after_world.eids == (*before_world.eids, 3)
        assert all(after_length == before_length + 1 for after_length, before_length in zip(
            after_world.trail_lengths[:3], before_world.trail_lengths,
        ))
        reads = NativePostWriteMemoryAccess(
            connection, legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id, expected_dimension=3,
        )
        srg = NativeSRGTransientRuntime(
            connection, legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
            process_state=capability.srg_process_state,
        )
        assert srg.effective_collision_report(reads.get_current(result.eid))["collision"] is True
    finally:
        qualified.close()


def test_reinforcement_runs_only_all_outcome_native_consumers(tmp_path: Path):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, owner, _workspace, identity, side, conflicts, proposals = _environment(scope)
        identity.seed["coupling_mode"] = "read_only"
        router = NativeFabricMemoryRouter(capability)
        seed_request = _request("reinforce-seed", 1)
        seed = router.route(seed_request).result
        request = _request("reinforce-r2", 2)
        result = router.route(request).result
        assert seed is not None and result is not None and result.reinforced is True
        before = _counts(connection)
        before_world = _world(connection, capability, scope)
        outcome = _adapter(capability, configuration).run(
            _context(result, request), route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
        )
        assert outcome.proposal_id is None
        assert _counts(connection) == before
        assert _world(connection, capability, scope).trail_lengths == tuple(value + 1 for value in before_world.trail_lengths)
        assert not conflicts.calls and not owner.field.packets and not side.events and not proposals.calls
    finally:
        qualified.close()


def test_no_write_has_no_native_route_or_durable_mutation_and_steps_world_once(tmp_path: Path):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, owner, _workspace, _identity, side, conflicts, proposals = _environment(scope)
        seed = NativeFabricMemoryRouter(capability).route(_request("no-write-seed", 1)).result
        assert seed is not None
        before = _counts(connection)
        before_world = _world(connection, capability, scope)
        outcome = _adapter(capability, configuration).run(_no_write_context(2))
        assert outcome.proposal_id is None
        assert _counts(connection) == before
        assert _world(connection, capability, scope).trail_lengths == tuple(value + 1 for value in before_world.trail_lengths)
        assert not owner.field.packets and not side.events and not conflicts.calls and not proposals.calls
    finally:
        qualified.close()


def test_route_witness_mismatch_refuses_before_any_post_write_effect(tmp_path: Path):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, owner, _workspace, _identity, side, conflicts, proposals = _environment(scope)
        request = _request("mismatch", 1)
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None
        before = _counts(connection)
        context = replace(_context(result, request), eid=result.eid + 1)
        with pytest.raises(SubstrateInvariantViolation, match="disagrees"):
            _adapter(capability, configuration).run(
                context, route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
            )
        with pytest.raises(SubstrateInvariantViolation, match="operation key"):
            _adapter(capability, configuration).run(
                _context(result, request), route_witness=NativePostWriteRouteWitness(result, "wrong-native-key"),
            )
        assert _counts(connection) == before
        assert not owner.field.packets and not side.events and not conflicts.calls and not proposals.calls
    finally:
        qualified.close()


@pytest.mark.parametrize(
    "posture",
    ("motif-maintenance", "auto-merge", "character", "compression", "checkpoint", "trajectory", "bridges", "deep"),
)
def test_enabled_or_required_unqualified_feature_postures_refuse_before_effects(tmp_path: Path, posture: str):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, owner, workspace, _identity, side, conflicts, proposals = _environment(scope)
        request = _request(f"posture-{posture}", 1)
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None
        if posture == "motif-maintenance":
            configuration = replace(configuration, motif_suggestion_maintenance_required=True)
        elif posture == "auto-merge":
            workspace.domain_policies["personal"]["auto_merge_motifs"] = True
        elif posture == "character":
            owner._character_enable = True
        elif posture == "compression":
            owner._compress_enable = True
        elif posture == "checkpoint":
            owner._checkpoint_enable = True
        elif posture == "trajectory":
            configuration = replace(configuration, persistent_trajectory_evidence_required=True)
        elif posture == "bridges":
            configuration = replace(configuration, bridge_suggestions_required=True)
        else:
            configuration = replace(configuration, deep_memory_required=True)
        before = _counts(connection)
        with pytest.raises(SubstrateConfigurationError, match="refuses"):
            _adapter(capability, configuration).run(
                _context(result, request),
                route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
            )
        assert _counts(connection) == before
        assert not owner.field.packets and not side.events and not conflicts.calls and not proposals.calls
    finally:
        qualified.close()


def test_adapter_opens_a_new_operation_connection_and_keeps_process_owners(tmp_path: Path, monkeypatch):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, _owner, _workspace, identity, _side, _conflicts, _proposals = _environment(scope)
        identity.seed["coupling_mode"] = "read_only"
        request = _request("connection-boundary", 1)
        result = NativeFabricMemoryRouter(capability).route(request).result
        assert result is not None
        import torment_service.substrate.native_post_write_runtime as native_post_write_runtime

        original = native_post_write_runtime.open_existing_native_core_connection
        opened_ids: list[int] = []

        @contextmanager
        def observed(path):
            with original(path) as opened:
                opened_ids.append(id(opened.connection))
                yield opened

        monkeypatch.setattr(native_post_write_runtime, "open_existing_native_core_connection", observed)
        adapter = _adapter(capability, configuration)
        adapter.run(
            _context(result, request), route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
        )
        assert opened_ids and opened_ids[0] != id(connection)
        assert not hasattr(adapter, "_connection")
        assert _world(connection, capability, scope).eids == (0,)
    finally:
        qualified.close()


def test_new_source_response_loss_recovers_before_one_native_post_write(tmp_path: Path):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, _owner, _workspace, identity, _side, _conflicts, _proposals = _environment(scope)
        identity.seed["coupling_mode"] = "read_only"
        router = NativeFabricMemoryRouter(capability)
        request = _request("new-source-recovery", 1)
        with pytest.raises(RuntimeError, match="forced interruption|committed native"):
            router.route(request, _test_stop_after="source")
        recovered = router.route(request).result
        assert recovered is not None and recovered.reinforced is False
        before = _counts(connection)
        _adapter(capability, configuration).run(
            _context(recovered, request), route_witness=NativePostWriteRouteWitness(recovered, request.native_operation_key),
        )
        assert _counts(connection) == before
        assert _world(connection, capability, scope).eids == (0,)
    finally:
        qualified.close()


def test_new_representation_response_loss_recovers_before_one_native_post_write(tmp_path: Path, monkeypatch):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, _owner, _workspace, identity, _side, _conflicts, _proposals = _environment(scope)
        identity.seed["coupling_mode"] = "read_only"
        import torment_service.substrate.fabric_native_routing as fabric_native_routing

        original = fabric_native_routing.NativeRepresentationService.publish_representation_ready
        called = False

        def interrupt_ready(service, *args, **kwargs):
            nonlocal called
            if not called:
                called = True
                raise RuntimeError("forced native E1 response loss")
            return original(service, *args, **kwargs)

        monkeypatch.setattr(
            fabric_native_routing.NativeRepresentationService, "publish_representation_ready", interrupt_ready,
        )
        request = _request("new-representation-recovery", 1)
        with pytest.raises(RuntimeError, match="forced native E1 response loss"):
            NativeFabricMemoryRouter(capability).route(request)
        recovered = NativeFabricMemoryRouter(capability).route(request).result
        assert recovered is not None and recovered.reinforced is False
        before = _counts(connection)
        _adapter(capability, configuration).run(
            _context(recovered, request), route_witness=NativePostWriteRouteWitness(recovered, request.native_operation_key),
        )
        assert _counts(connection) == before
    finally:
        qualified.close()


@pytest.mark.parametrize("stop", ("source", "pending", "expectation"))
def test_reinforcement_response_loss_recovers_before_one_native_post_write(tmp_path: Path, stop: str):
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, _owner, _workspace, identity, _side, _conflicts, _proposals = _environment(scope)
        identity.seed["coupling_mode"] = "read_only"
        router = NativeFabricMemoryRouter(capability)
        assert router.route(_request(f"reinforce-recovery-{stop}-seed", 1)).result is not None
        request = _request(f"reinforce-recovery-{stop}", 2)
        with pytest.raises(RuntimeError, match="forced interruption|committed native"):
            router.route(request, _test_stop_after=stop)
        recovered = router.route(request).result
        assert recovered is not None and recovered.reinforced is True
        before = _counts(connection)
        _adapter(capability, configuration).run(
            _context(recovered, request), route_witness=NativePostWriteRouteWitness(recovered, request.native_operation_key),
        )
        assert _counts(connection) == before
        assert _world(connection, capability, scope).eids == (0,)
    finally:
        qualified.close()


def test_derived_representation_recovery_inside_post_write_creates_no_duplicate_row(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "1.1")
    monkeypatch.setenv("TORMENT_ID_ANCHOR_MIN_COUNT", "3")
    monkeypatch.setenv("TORMENT_ID_ANCHOR_MIN_GAP_STEPS", "0")
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, owner, _workspace, identity, side, _conflicts, _proposals = _environment(scope)
        owner._hivemind_enable = False
        identity.seed["coupling_mode"] = "read_only"
        router = NativeFabricMemoryRouter(capability)
        routed = []
        for step in range(1, 4):
            request = _request(f"derived-recovery-{step}", step)
            result = router.route(request).result
            assert result is not None
            routed.append((result, request))
        result, request = routed[-1]
        import torment_service.substrate.native_derived_memory_runtime as native_derived_memory_runtime

        original = native_derived_memory_runtime.NativeDerivedMemoryCreationService.create
        first = True

        def interrupt_once(service, creation_request, **kwargs):
            nonlocal first
            if first:
                first = False
                return original(service, creation_request, _test_stop_after="pending", **kwargs)
            return original(service, creation_request, **kwargs)

        monkeypatch.setattr(native_derived_memory_runtime.NativeDerivedMemoryCreationService, "create", interrupt_once)
        adapter = _adapter(capability, configuration)
        adapter.run(
            _context(result, request), route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
        )
        after_interruption = _counts(connection)
        assert _world(connection, capability, scope).eids == (0, 1, 2, 3)
        adapter.run(
            _context(result, request), route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
        )
        after_recovery = _counts(connection)
        assert after_recovery["objects"] == after_interruption["objects"]
        assert after_recovery["object_revisions"] == after_interruption["object_revisions"]
        assert after_recovery["representations"] == after_interruption["representations"]
        assert side.events == ["anchor"]
        assert _world(connection, capability, scope).eids == (0, 1, 2, 3)
    finally:
        qualified.close()


def test_explicit_m1_profile_runs_native_suggestion_maintenance_without_legacy_motif_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "1.1")
    qualified, connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, owner, workspace, identity, _side, _conflicts, _proposals = _environment(scope)
        owner._hivemind_enable = False
        identity.seed["coupling_mode"] = "read_only"
        workflow_root = tmp_path / "external-workflow"
        workspace = SimpleNamespace(
            data_dir=str(workflow_root),
            domain_policies={"personal": {
                "auto_merge_motifs": False,
                "motif_entropy_target_n": 2,
                "motif_entropy_high": 0.0,
                "motif_merge_similarity": .9,
                "motif_merge_max_suggestions": 20,
                "auto_merge_entropy_trigger": .8,
            }},
            conflicts=workspace.conflicts,
            proposals=workspace.proposals,
        )
        configuration = replace(
            configuration,
            profile=NativePostWriteQualificationProfile.core_staging_with_motif_suggestion_maintenance(),
            external=replace(configuration.external, workspace=workspace),
            motif_suggestion_maintenance_required=True,
        )
        router = NativeFabricMemoryRouter(capability)
        assert router.route(_request("m1-first", 1, vector=(1.0, 0.0, 0.0))).result is not None
        request = _request("m1-second", 2, vector=(0.0, 1.0, 0.0))
        result = router.route(request).result
        assert result is not None and result.reinforced is False

        _adapter(capability, configuration).run(
            _context(result, request),
            route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
        )
        motif_base = workflow_root / "workspaces" / "ws" / "domains" / "personal"
        assert not (motif_base / "motifs.json").exists()
        events = [json.loads(line) for line in (motif_base / "motif_events.jsonl").read_text(encoding="utf-8").splitlines()]
        assert [event["type"] for event in events] == ["MOTIF_ENTROPY"]
        assert NativePostWriteQualificationProfile.core_staging().motif_suggestion_maintenance.name == "REQUIRED_NOOP"
        assert configuration.profile.motif_suggestion_maintenance.name == "QUALIFIED"
        assert configuration.profile.motif_auto_merge.name == "UNSUPPORTED"
        # The workflow event is external; it did not create or mutate native
        # objects beyond the already-routed source/motif composition.
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 4
    finally:
        qualified.close()


def test_i4c_true_split_runs_conflict_then_i4b2_motif_and_anchor_tail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "1.1")
    qualified, _connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, owner, workspace, identity, side, conflicts, proposals = _environment(scope)
        owner._hivemind_enable = False
        identity.seed["coupling_mode"] = "read_only"
        workflow_root = tmp_path / "i4b2-external-workflow"
        workspace = SimpleNamespace(
            data_dir=str(workflow_root),
            domain_policies={"personal": {"auto_merge_motifs": False}},
            conflicts=workspace.conflicts,
            proposals=workspace.proposals,
        )
        configuration = replace(
            configuration,
            profile=NativePostWriteQualificationProfile.core_staging_with_motif_merge_maintenance(),
            external=replace(configuration.external, workspace=workspace),
            motif_suggestion_maintenance_required=True,
        )
        router = NativeFabricMemoryRouter(capability)
        assert router.route(_request("i4c-conflict-zero-eid", 1)).result is not None
        seed_request = _request("i4c-conflict-seed", 2)
        seed = router.route(seed_request).result
        assert seed is not None
        request = _request("i4c-conflict-true-split", 3)
        routed = router.route(request).result
        assert routed is not None
        result = replace(routed, created_motif=None, precommit_true_split=True)

        events: list[str] = []
        original_add = conflicts.add
        original_maintenance = NativeMotifMaintenanceAdapter.update_entropy_and_suggest

        def record_conflict(**kwargs):
            events.append("conflict")
            return original_add(**kwargs)

        def record_maintenance(adapter, *args, **kwargs):
            events.append("motif_maintenance")
            return original_maintenance(adapter, *args, **kwargs)

        def forbidden(*_args, **_kwargs):
            raise AssertionError("I4C reached an unqualified post-write consumer")

        monkeypatch.setattr(conflicts, "add", record_conflict)
        monkeypatch.setattr(NativeMotifMaintenanceAdapter, "update_entropy_and_suggest", record_maintenance)
        monkeypatch.setattr(LegacyFabricPostWriteAdapter, "_run_srg_collision", forbidden)
        monkeypatch.setattr(LegacyFabricPostWriteAdapter, "_run_hivemind", forbidden)
        monkeypatch.setattr(LegacyFabricPostWriteAdapter, "_run_world_step", forbidden)
        monkeypatch.setattr(LegacyFabricPostWriteAdapter, "_run_character_drift", forbidden)
        monkeypatch.setattr(LegacyFabricPostWriteAdapter, "_run_proposal", forbidden)
        monkeypatch.setattr(LegacyFabricPostWriteAdapter, "_run_derived_memory", forbidden)

        outcome = _adapter(capability, configuration).run(
            _context(result, request, created_motif=None),
            route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
        )
        assert outcome.proposal_id is None
        assert events[:2] == ["conflict", "motif_maintenance"]
        assert len(conflicts.calls) == 1
        conflict = conflicts.calls[0]
        assert conflict["eid_a"] == seed.eid
        assert conflict["eid_b"] == routed.eid
        assert conflict["origin_scope"] == "private"
        assert conflict["origin_agent_id"] == "aria"
        assert conflict["origin_domain_id"] is None
        assert not owner.field.packets
        assert not proposals.calls
        assert (workflow_root / "workspaces" / "ws" / "domains" / "personal" / "motif_events.jsonl").exists()
        # Anchor failure/success is intentionally fail-soft, but mood drift is
        # excluded: this run may write only the M1 workflow and N02 anchor state.
        assert "affect" not in side.events
    finally:
        qualified.close()


def test_i4c_true_split_conflict_failure_is_soft_and_does_not_skip_motif_tail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "1.1")
    qualified, _connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, _owner, workspace, identity, _side, conflicts, _proposals = _environment(scope)
        identity.seed["coupling_mode"] = "read_only"
        workflow_root = tmp_path / "i4c-conflict-failure-workflow"
        workspace = SimpleNamespace(
            data_dir=str(workflow_root),
            domain_policies={"personal": {"auto_merge_motifs": False}},
            conflicts=workspace.conflicts,
            proposals=workspace.proposals,
        )
        configuration = replace(
            configuration,
            profile=NativePostWriteQualificationProfile.core_staging_with_motif_merge_maintenance(),
            external=replace(configuration.external, workspace=workspace),
            motif_suggestion_maintenance_required=True,
        )
        router = NativeFabricMemoryRouter(capability)
        assert router.route(_request("i4c-conflict-failure-zero-eid", 1)).result is not None
        assert router.route(_request("i4c-conflict-failure-seed", 2)).result is not None
        request = _request("i4c-conflict-failure", 3)
        routed = router.route(request).result
        assert routed is not None
        split_result = replace(routed, created_motif=None, precommit_true_split=True)
        monkeypatch.setattr(
            conflicts,
            "add",
            lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("forced conflict owner failure")),
        )

        assert _adapter(capability, configuration).run(
            _context(split_result, request, created_motif=None),
            route_witness=NativePostWriteRouteWitness(split_result, request.native_operation_key),
        ).proposal_id is None
        assert (workflow_root / "workspaces" / "ws" / "domains" / "personal" / "motif_events.jsonl").exists()
    finally:
        qualified.close()


def test_i4c_true_split_conflict_reentry_has_no_invented_exactly_once_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "1.1")
    qualified, _connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, _owner, workspace, identity, _side, conflicts, _proposals = _environment(scope)
        identity.seed["coupling_mode"] = "read_only"
        workspace = SimpleNamespace(
            data_dir=str(tmp_path / "i4c-conflict-reentry-workflow"),
            domain_policies={"personal": {"auto_merge_motifs": False}},
            conflicts=workspace.conflicts,
            proposals=workspace.proposals,
        )
        configuration = replace(
            configuration,
            profile=NativePostWriteQualificationProfile.core_staging_with_motif_merge_maintenance(),
            external=replace(configuration.external, workspace=workspace),
            motif_suggestion_maintenance_required=True,
        )
        router = NativeFabricMemoryRouter(capability)
        assert router.route(_request("i4c-conflict-reentry-zero-eid", 1)).result is not None
        assert router.route(_request("i4c-conflict-reentry-seed", 2)).result is not None
        request = _request("i4c-conflict-reentry", 3)
        routed = router.route(request).result
        assert routed is not None
        split_result = replace(routed, created_motif=None, precommit_true_split=True)
        context = _context(split_result, request, created_motif=None)
        adapter = _adapter(capability, configuration)
        witness = NativePostWriteRouteWitness(split_result, request.native_operation_key)

        adapter.run(context, route_witness=witness)
        adapter.run(context, route_witness=witness)

        assert len(conflicts.calls) == 2
        assert all(call["eid_b"] == routed.eid for call in conflicts.calls)
        assert all(call["origin_scope"] == "private" for call in conflicts.calls)
    finally:
        qualified.close()


def test_i4b2_tail_keeps_maintenance_and_anchor_failures_independent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """The qualified prefix preserves the legacy independent fail-soft slots."""
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "1.1")
    qualified, _connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, _owner, workspace, identity, _side, _conflicts, _proposals = _environment(scope)
        identity.seed["coupling_mode"] = "read_only"
        workflow_root = tmp_path / "i4b2-failure-workflow"
        workspace = SimpleNamespace(
            data_dir=str(workflow_root),
            domain_policies={"personal": {"auto_merge_motifs": False}},
            conflicts=workspace.conflicts,
            proposals=workspace.proposals,
        )
        configuration = replace(
            configuration,
            profile=NativePostWriteQualificationProfile.core_staging_with_motif_merge_maintenance(),
            external=replace(configuration.external, workspace=workspace),
            motif_suggestion_maintenance_required=True,
        )
        request = _request("i4b2-independent-failures", 1)
        routed = NativeFabricMemoryRouter(capability).route(request).result
        assert routed is not None
        split_result = replace(routed, created_motif=None, precommit_true_split=True)
        context = _context(split_result, request, created_motif=None)
        adapter = _adapter(capability, configuration)

        calls: list[str] = []
        monkeypatch.setattr(
            NativeMotifMaintenanceAdapter,
            "update_entropy_and_suggest",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("forced M1 failure")),
        )
        monkeypatch.setattr(
            NativeDerivedMemoryRuntime,
            "maybe_emit_identity_anchor",
            lambda *_args, **_kwargs: calls.append("emit"),
        )
        monkeypatch.setattr(
            NativeDerivedMemoryRuntime,
            "refine_identity_anchors",
            lambda *_args, **_kwargs: calls.append("refine"),
        )
        adapter.run(
            context,
            route_witness=NativePostWriteRouteWitness(split_result, request.native_operation_key),
        )
        assert calls == ["emit", "refine"]

        calls.clear()
        monkeypatch.setattr(
            NativeDerivedMemoryRuntime,
            "maybe_emit_identity_anchor",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("forced anchor emission failure")),
        )
        adapter.run(
            context,
            route_witness=NativePostWriteRouteWitness(split_result, request.native_operation_key),
        )
        assert calls == ["refine"]
    finally:
        qualified.close()


def test_i4b2_tail_with_no_motif_runtime_is_a_complete_no_op(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "1.1")
    qualified, _connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, _owner, workspace, identity, side, _conflicts, _proposals = _environment(scope)
        identity.seed["coupling_mode"] = "read_only"
        workspace = SimpleNamespace(
            data_dir=str(tmp_path / "i4b2-null-motif-runtime"),
            domain_policies={"personal": {"auto_merge_motifs": False}},
            conflicts=workspace.conflicts,
            proposals=workspace.proposals,
        )
        configuration = replace(
            configuration,
            profile=NativePostWriteQualificationProfile.core_staging_with_motif_merge_maintenance(),
            external=replace(configuration.external, workspace=workspace),
            motif_suggestion_maintenance_required=True,
        )
        request = _request("i4b2-null-motif-runtime", 1)
        routed = NativeFabricMemoryRouter(capability).route(request).result
        assert routed is not None
        split_result = replace(routed, created_motif=None, precommit_true_split=True)
        adapter = _adapter(capability, configuration)
        original_bind = NativeFabricPostWriteAdapter._bind_dependencies

        def bind_without_motif_runtime(self, connection, context, witness):
            return replace(
                original_bind(self, connection, context, witness),
                motif_runtime=None,
            )

        calls: list[str] = []
        monkeypatch.setattr(
            NativeFabricPostWriteAdapter,
            "_bind_dependencies",
            bind_without_motif_runtime,
        )
        monkeypatch.setattr(
            NativeDerivedMemoryRuntime,
            "maybe_emit_identity_anchor",
            lambda *_args, **_kwargs: calls.append("emit"),
        )
        monkeypatch.setattr(
            NativeDerivedMemoryRuntime,
            "refine_identity_anchors",
            lambda *_args, **_kwargs: calls.append("refine"),
        )

        assert adapter.run(
            _context(split_result, request, created_motif=None),
            route_witness=NativePostWriteRouteWitness(split_result, request.native_operation_key),
        ).proposal_id is None
        assert calls == []
        assert side.events == []
    finally:
        qualified.close()


def test_i4b2_tail_skips_reinforcement_and_no_write_before_any_motif_consumer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "1.1")
    qualified, _connection, capability, scope = _prepared(tmp_path)
    try:
        configuration, _owner, workspace, identity, _side, _conflicts, _proposals = _environment(scope)
        identity.seed["coupling_mode"] = "read_only"
        workspace = SimpleNamespace(
            data_dir=str(tmp_path / "i4b2-gate-workflow"),
            domain_policies={"personal": {"auto_merge_motifs": False}},
            conflicts=workspace.conflicts,
            proposals=workspace.proposals,
        )
        configuration = replace(
            configuration,
            profile=NativePostWriteQualificationProfile.core_staging_with_motif_merge_maintenance(),
            external=replace(configuration.external, workspace=workspace),
            motif_suggestion_maintenance_required=True,
        )
        request = _request("i4b2-tail-gates", 1)
        routed = NativeFabricMemoryRouter(capability).route(request).result
        assert routed is not None
        split_result = replace(routed, created_motif=None, precommit_true_split=True)
        adapter = _adapter(capability, configuration)
        monkeypatch.setattr(
            NativeMotifMaintenanceAdapter,
            "update_entropy_and_suggest",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("I4B-2 tail ran")),
        )
        monkeypatch.setattr(
            LegacyFabricPostWriteAdapter,
            "_run_contradiction_surface",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("I4C conflict ran")),
        )
        witness = NativePostWriteRouteWitness(split_result, request.native_operation_key)

        adapter.run(
            _context(
                split_result,
                request,
                outcome=PostWriteStorageOutcome.REINFORCED_EXISTING,
                created_motif=None,
            ),
            route_witness=witness,
        )
        adapter.run(_no_write_context(2), route_witness=witness)
    finally:
        qualified.close()


def test_explicit_m2_profile_is_the_only_profile_that_qualifies_native_auto_merge():
    baseline = NativePostWriteQualificationProfile.core_staging()
    m1 = NativePostWriteQualificationProfile.core_staging_with_motif_suggestion_maintenance()
    m2 = NativePostWriteQualificationProfile.core_staging_with_motif_merge_maintenance()
    assert baseline.motif_suggestion_maintenance.name == "REQUIRED_NOOP"
    assert baseline.motif_auto_merge.name == "UNSUPPORTED"
    assert m1.motif_suggestion_maintenance.name == "QUALIFIED"
    assert m1.motif_auto_merge.name == "UNSUPPORTED"
    assert m2.motif_suggestion_maintenance.name == "QUALIFIED"
    assert m2.motif_auto_merge.name == "QUALIFIED"
