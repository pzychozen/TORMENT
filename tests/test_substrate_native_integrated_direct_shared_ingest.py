"""E1 qualification for direct shared routing and lane-local vector freshness.

This remains an explicit test seam.  It deliberately never imports or calls
``TormentFabric.ingest``: the public Fabric path stays legacy while this file
composes the already-qualified native storage and post-write capabilities.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.memory_kernel import TriOctaMemoryKernel
from torment_service.motif_geometry_port import NativeMotifGeometryAdapter
from torment_service.post_write_runtime import LegacyFabricPostWriteAdapter
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import (
    open_existing_native_core_connection,
    open_temporary_test_connection,
)
from torment_service.substrate.errors import SubstrateConfigurationError
from torment_service.substrate.fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteRequest,
    NativeFabricRoutingScope,
    prepare_native_fabric_routing_capability,
)
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntimeConfiguration
from torment_service.substrate.native_direct_shared_ingest import (
    NativeDirectSharedIngestAdapter,
    NativeDirectSharedPostWriteFacts,
)
from torment_service.substrate.native_memory_vector_runtime import (
    NativeMemoryVectorRuntime,
    NativeMemoryVectorRuntimeConfiguration,
)
from torment_service.substrate.native_post_write_runtime import (
    NativeFabricPostWriteAdapter,
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
    NativeSharedCheckpointSnapshotBinding,
    NativeSharedTrajectoryEvidenceBinding,
    NativeSharedTriggerMoodDriftBinding,
    prepare_native_fabric_post_write_adapter,
)
from torment_service.substrate.native_trajectory_evidence_runtime import resolve_trajectory_format
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


class _Embedder:
    provider = "synthetic"
    model = "synthetic-v1"
    dim = 3

    def embed(self, _text: str) -> np.ndarray:
        return np.asarray((1.0, 0.0, 0.0), dtype=np.float32)


def _scope(
    connection,
    *,
    kind: str,
    label: str,
    domain_id: str | None = None,
) -> NativeFabricRoutingScope:
    memory_identity, semantic_scope, memory_alias = _id(), _id(), _id()
    motif_identity, membership_identity, motif_alias, idempotency = (_id() for _ in range(4))
    for value, name in (
        (memory_identity, "memory"), (motif_identity, "motif"), (membership_identity, "membership"),
    ):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"e1:{label}:{name}"),
        )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(semantic_scope), f"e1:{label}:semantic"),
    )
    for value, name in ((memory_alias, "memory-alias"), (motif_alias, "motif-alias")):
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"e1:{label}:{name}"),
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency), f"e1:{label}"),
    )
    if kind == "PRIVATE_AGENT":
        runtime_scope = NativeMemoryRuntimeScope(
            workspace_id="ws", scope_kind=kind, legacy_source_namespace_id=memory_alias,
            identity_namespace_id=memory_identity, semantic_scope_id=semantic_scope, agent_id="aria",
        )
    else:
        assert domain_id is not None
        runtime_scope = NativeMemoryRuntimeScope(
            workspace_id="ws", scope_kind=kind, legacy_source_namespace_id=memory_alias,
            identity_namespace_id=memory_identity, semantic_scope_id=semantic_scope, domain_id=domain_id,
        )
    return NativeFabricRoutingScope(
        runtime_scope=runtime_scope, motif_alias_namespace_id=motif_alias,
        motif_identity_namespace_id=motif_identity,
        membership_identity_namespace_id=membership_identity,
        idempotency_namespace_id=idempotency,
    )


class _RecoveredSharedScope:
    """The existing E4C recovery reader shape, with no writer capability."""

    def __init__(self, core_path: Path, scope: NativeFabricRoutingScope) -> None:
        self.memory_runtime_scope = scope.runtime_scope
        self.fabric_routing_scope = scope
        self._core_path = core_path

    @contextmanager
    def open_readers(self):
        with open_existing_native_core_connection(self._core_path) as opened:
            yield SimpleNamespace(motifs=NativeMotifRuntimeReader(opened.connection))


class _RecoveredSharedRuntime:
    def __init__(self, core_path: Path, scopes: dict[str, NativeFabricRoutingScope]) -> None:
        self._scopes = {
            domain: _RecoveredSharedScope(core_path, scope) for domain, scope in scopes.items()
        }

    def lookup_shared(self, domain_id: str) -> _RecoveredSharedScope:
        return self._scopes[domain_id]


class _SideStore:
    """A tiny file-backed owner used to prove cold reload preserves D1 state."""

    def __init__(self, root: Path, *, affect: dict[str, object] | None = None) -> None:
        self._path = root / "side-store.json"
        self._initial = {
            "anchor": {"motifs": {}},
            "affect": affect or {
                "last_tag": None, "last_conf": 0.0, "last_step": -10**9, "drift_hist": [],
            },
        }
        self.anchor_save_calls = 0

    def _state(self) -> dict[str, object]:
        if not self._path.exists():
            return json.loads(json.dumps(self._initial))
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self, state: dict[str, object]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")

    @property
    def anchor(self) -> dict[str, object]:
        return dict(self._state()["anchor"])

    @property
    def affect(self) -> dict[str, object]:
        return dict(self._state()["affect"])

    def load_anchor_state(self, **_kwargs):
        return self.anchor

    def save_anchor_state(self, *, state, **_kwargs):
        self.anchor_save_calls += 1
        raise AssertionError("shared D0 must not mutate private anchors")

    def load_affect_state(self, **_kwargs):
        return self.affect

    def save_affect_state(self, *, state, **_kwargs):
        current = self._state()
        current["affect"] = state
        self._save(current)


class _CharacterStore:
    def __init__(self) -> None:
        self.seed_calls = 0
        self.state_calls = 0

    def load_seed(self, *_args):
        self.seed_calls += 1
        raise AssertionError("shared Character must not read a private seed")

    def load_state(self, *_args):
        self.state_calls += 1
        return None


class _Field:
    def __init__(self) -> None:
        self.fail = False
        self.packets: list[object] = []

    def append_packet(self, packet, *, embedding):
        if self.fail:
            raise OSError("injected Hivemind failure")
        self.packets.append((packet, np.asarray(embedding).copy()))
        return None


class _Bridges:
    def __init__(self) -> None:
        self.calls: list[tuple[object, float, int]] = []
        self.fail = False

    def suggest(self, geometry, *, sim_threshold: float, max_new: int) -> None:
        self.calls.append((geometry, sim_threshold, max_new))
        if self.fail:
            raise OSError("injected bridge failure")


class _Owner:
    def __init__(self, root: Path, *, field: _Field, character_store: _CharacterStore) -> None:
        self._log = logging.getLogger("e1.integrated.owner")
        self.data_dir = str(root / "workflow")
        self._compress_enable = False
        self._compress_min_step = 0
        self._srg_enable = False
        self._hivemind_enable = True
        self._hivemind_telemetry_enable = True
        self._checkpoint_enable = True
        self._checkpoint_interval = 1
        self._checkpoint_max_keep = 2
        self._character_enable = True
        self._character_drift_every = 1
        self._last_drift_was_high: dict[tuple[str, str], bool] = {}
        self.drift_reflex_callback = None
        self.character_store = character_store
        self._field = field
        self.telemetry: list[dict[str, object]] = []

    def _get_collective_field(self, _workspace_id: str):
        return self._field

    def _get_proposal_bridge(self, _workspace_id: str):
        return SimpleNamespace(maybe_draft_proposal=lambda **_kwargs: None)

    def _emit_hivemind_packet_telemetry(self, **kwargs) -> None:
        self.telemetry.append(kwargs)


def _policy() -> dict[str, object]:
    return {
        "motif_entropy_target_n": 2,
        "motif_entropy_high": 0.0,
        "motif_merge_similarity": 0.93,
        "motif_merge_max_suggestions": 20,
        "auto_merge_motifs": True,
        "auto_merge_entropy_trigger": 0.0,
    }


def _template(private: NativeFabricRoutingScope, side: _SideStore) -> NativeDerivedMemoryRuntimeConfiguration:
    return NativeDerivedMemoryRuntimeConfiguration(
        workspace_id="ws", agent_id="aria", domain_id="research",
        legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
        motif_alias_namespace_id=private.motif_alias_namespace_id,
        memory_identity_namespace_id=private.runtime_scope.identity_namespace_id,
        semantic_scope_id=private.runtime_scope.semantic_scope_id,
        idempotency_namespace_id=private.idempotency_namespace_id,
        parent_native_operation_key="e1-template-never-used", expected_dimension=3,
        embed=lambda _text: np.asarray((.8, .6, .0), dtype=np.float32),
        embedder_provider="synthetic", embedder_model="synthetic-v1", side_store=side,
        now_ts=lambda: 777,
    )


def _request(
    key: str,
    *,
    domain_id: str = "research",
    step: int = 1,
    vector=(.2, .8, .1),
) -> NativeFabricRouteRequest:
    return NativeFabricRouteRequest(
        workspace_id="ws", scope="shared", agent_id="aria", domain_id=domain_id,
        native_operation_key=key, embedder_lane=_lane(), summary=f"E1 {key}",
        memory_type="reflection", memory_class="core", strength=.8, confidence=.9,
        half_life_days=20., logical_step=step, created_ts=step, last_active_ts=step,
        last_reinforced_ts=step, incoming_embedding=vector,
        provenance=ProvenanceV1.for_user_ingest(step=step), governance=MemoryGovernanceFlags(),
        flexible_payload={"e1": key, "seed_pos0": [3., 4., 0.], "seed_v0": [1., -.5, 2.]},
    )


def _facts(*, affect_tag: str | None = None, affect_conf: float | None = None) -> NativeDirectSharedPostWriteFacts:
    return NativeDirectSharedPostWriteFacts(
        promotion_score=.4, stability_delta=.1,
        tri_mod={"bridge_p": .08, "bridge_sim": .86, "cycle_stage": "rise"},
        debug={"coherence": .8}, srg_state={"R_band": "stable"},
        phase_durations={"corridor_duration_steps": 1, "phase_duration_steps": 1},
        state_symbol="R", affect_tag=affect_tag, affect_conf=affect_conf,
        skip_packet_emission=False,
    )


def _views(connection, scope: NativeFabricRoutingScope):
    rows = connection.execute(
        """SELECT alias_value FROM legacy_object_aliases
             WHERE legacy_source_namespace_id=? AND alias_kind='EID'
             ORDER BY CAST(alias_value AS INTEGER)""",
        (native_id_to_bytes(scope.runtime_scope.legacy_source_namespace_id),),
    ).fetchall()
    facade = NativeMemoryCompatibilityFacade(connection)
    return tuple(facade.get_memory_by_eid(
        legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id, eid=int(row[0]),
    ) for row in rows)


def _counts(connection) -> tuple[int, ...]:
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
        "objects", "object_revisions", "relationships", "relationship_revisions",
        "representations", "representation_payloads", "operations", "semantic_transitions",
    ))


def _vector_runtime(capability, scope: NativeFabricRoutingScope) -> NativeMemoryVectorRuntime:
    return NativeMemoryVectorRuntime(
        NativeMemoryVectorRuntimeConfiguration(
            capability.core_database_path, capability.core_id, scope.runtime_scope, _lane(),
        ),
        embedder=_Embedder(),
    )


def _harness(tmp_path: Path, *, affect: dict[str, object] | None = None):
    qualified = open_temporary_test_connection(tmp_path / "e1-integrated.db")
    metadata = create_schema(qualified.connection)
    connection = qualified.connection
    private = _scope(connection, kind="PRIVATE_AGENT", label="aria")
    research = _scope(connection, kind="SHARED_DOMAIN", label="research", domain_id="research")
    engineering = _scope(connection, kind="SHARED_DOMAIN", label="engineering", domain_id="engineering")
    binding = prepare_native_memory_runtime_binding(
        connection=connection, core_database_path=qualified.database_path,
        expected_core_id=native_id_from_bytes(metadata.core_id),
        scope_bindings=(private.runtime_scope, research.runtime_scope, engineering.runtime_scope),
        representation_lane=_lane(),
    )
    capability = prepare_native_fabric_routing_capability(
        binding=binding, connection=connection, routing_scopes=(private, research, engineering),
        expected_core_id=native_id_from_bytes(metadata.core_id),
    )
    side = _SideStore(tmp_path, affect=affect)
    field, character_store, bridges = _Field(), _CharacterStore(), _Bridges()
    owner = _Owner(tmp_path, field=field, character_store=character_store)
    workspace = SimpleNamespace(
        data_dir=owner.data_dir, domain_policies={"research": _policy()}, proposals={"research": object()},
        bridges=bridges,
    )
    geometry = NativeMotifGeometryAdapter(
        _RecoveredSharedRuntime(capability.core_database_path, {"research": research, "engineering": engineering}),
        domain_ids=("research", "engineering"), expected_dimension=3,
    )
    kernel = TriOctaMemoryKernel()
    configuration = NativePostWriteQualificationConfiguration(
        routing_scope=research,
        profile=NativePostWriteQualificationProfile.core_staging_with_shared_integrated_default(),
        external=NativePostWriteExternalDependencies(
            owner=owner, workspace=workspace, identity=SimpleNamespace(seed={}), agent_key="ws/aria",
            detect_canon_conflict=lambda *_args: (False, 0.0, "unused"),
            proposal_allowed=lambda *_args, **_kwargs: False,
            hivemind_log=logging.getLogger("e1.integrated.hivemind"), character_store=character_store,
            shared_bridge_geometry=geometry, random_chance=lambda _p: True,
        ),
        derived_runtime_template=None, motif_suggestion_maintenance_required=False,
        persistent_trajectory_evidence_required=False, checkpoint_snapshots_required=False,
        bridge_suggestions_required=False, deep_memory_required=False,
        shared_mood_drift_binding=NativeSharedTriggerMoodDriftBinding(private, _template(private, side)),
        shared_trajectory_evidence_binding=NativeSharedTrajectoryEvidenceBinding(
            str(tmp_path / "workflow" / "workspaces" / "ws" / "domains" / "research" / "shared"),
            resolve_trajectory_format(),
        ),
        shared_checkpoint_snapshot_binding=NativeSharedCheckpointSnapshotBinding(
            kernel.init_state("ws/aria"), kernel.new_runtime_context(),
        ),
        shared_integrated_default_required=True,
    )
    post_write = prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)
    vectors = (_vector_runtime(capability, private), _vector_runtime(capability, research), _vector_runtime(capability, engineering))
    for runtime in vectors:
        assert runtime.search_by_embedding((1., 0., 0.)) == []
        assert runtime.rebuild_count == 1 and runtime.snapshot is not None
    direct = NativeDirectSharedIngestAdapter(
        capability=capability, post_write_adapter=post_write, warm_vector_runtimes=vectors,
    )
    return SimpleNamespace(
        qualified=qualified, connection=connection, metadata=metadata, capability=capability,
        private=private, research=research, engineering=engineering, side=side, field=field,
        character_store=character_store, bridges=bridges, owner=owner, workspace=workspace,
        post_write=post_write, vectors=vectors, direct=direct,
    )


def _close(harness) -> None:
    for runtime in harness.vectors:
        runtime.close()
    harness.post_write.close()
    harness.qualified.close()


def test_e1_shared_no_mood_freezes_complete_order_and_only_rebuilds_research(tmp_path: Path, monkeypatch):
    harness = _harness(tmp_path)
    try:
        import torment_service.substrate.native_derived_memory_runtime as derived_runtime
        import torment_service.substrate.native_post_write_runtime as post_runtime
        from torment_service.motif_maintenance import NativeMotifMaintenanceAdapter

        trace: list[str] = []

        def wrap_method(owner, name, marker):
            original = getattr(owner, name)

            def wrapped(*args, **kwargs):
                trace.append(marker)
                return original(*args, **kwargs)

            monkeypatch.setattr(owner, name, wrapped)

        wrap_method(LegacyFabricPostWriteAdapter, "_run_contradiction_surface", "contradiction")
        wrap_method(LegacyFabricPostWriteAdapter, "_run_srg_collision", "srg")
        wrap_method(LegacyFabricPostWriteAdapter, "_run_hivemind", "hivemind")
        wrap_method(LegacyFabricPostWriteAdapter, "_run_character_drift", "character-noop")
        wrap_method(LegacyFabricPostWriteAdapter, "_run_proposal", "proposal-noop")
        wrap_method(NativeMotifMaintenanceAdapter, "update_entropy_and_suggest", "m1-m2")
        wrap_method(derived_runtime.NativeDerivedMemoryRuntime, "maybe_emit_identity_anchor", "d0-anchor-noop")
        wrap_method(derived_runtime.NativeDerivedMemoryRuntime, "refine_identity_anchors", "d0-refine-noop")
        wrap_method(derived_runtime.NativeDerivedMemoryRuntime, "maybe_emit_mood_drift", "d1-mood")
        wrap_method(NativeFabricPostWriteAdapter, "_run_shared_trajectory_evidence", "d3-trajectory")
        wrap_method(NativeFabricPostWriteAdapter, "_run_shared_checkpoint_snapshot", "d4-checkpoint")
        wrap_method(NativeFabricPostWriteAdapter, "_run_shared_compression_disabled_noop", "d6-disabled")
        original_bridge = post_runtime.run_bridge_suggestions

        def traced_bridge(*args, **kwargs):
            trace.append("b1-bridge")
            return original_bridge(*args, **kwargs)

        monkeypatch.setattr(post_runtime, "run_bridge_suggestions", traced_bridge)
        result = harness.direct.execute(_request("E1:NO_MOOD"), _facts())
        source_eid = result.route_attempt.result.eid
        assert result.route_attempt.result.reinforced is False
        assert result.post_write.ready_memory_eids == ((harness.research, source_eid),)
        assert result.invalidated_lane_keys == (harness.vectors[1].configuration.lane_key,)
        assert trace == [
            "contradiction", "srg", "hivemind", "m1-m2", "d0-anchor-noop", "d0-refine-noop",
            "d1-mood", "d3-trajectory", "character-noop", "d4-checkpoint", "d6-disabled",
            "proposal-noop", "b1-bridge",
        ]
        assert harness.side.anchor == {"motifs": {}} and harness.side.anchor_save_calls == 0
        assert harness.character_store.seed_calls == 0
        assert len(harness.field.packets) == 1 and len(harness.bridges.calls) == 1
        assert (tmp_path / "workflow" / "workspaces" / "ws" / "domains" / "research" / "shared").exists()

        private, research, engineering = harness.vectors
        assert [row["eid"] for row in research.search_by_embedding((.2, .8, .1))] == [source_eid]
        assert research.rebuild_count == 2
        assert private.search_by_embedding((1., 0., 0.)) == [] and private.rebuild_count == 1
        assert engineering.search_by_embedding((1., 0., 0.)) == [] and engineering.rebuild_count == 1
        source = _views(harness.connection, harness.research)[0]
        assert (source.payload["summary"], source.payload["type"], source.payload["user_id"]) == (
            "E1 E1:NO_MOOD", "reflection", "aria",
        )
        assert source.representation_references[0].usable is True
    finally:
        _close(harness)


def test_e1_mood_freshens_research_and_private_once_without_engineering(tmp_path: Path):
    harness = _harness(tmp_path, affect={"last_tag": "sad", "last_conf": .7, "last_step": 0, "drift_hist": []})
    try:
        result = harness.direct.execute(_request("E1:MOOD", step=200), _facts(affect_tag="angry", affect_conf=.8))
        source_eid = result.route_attempt.result.eid
        ready = dict(result.post_write.ready_memory_eids)
        mood_eid = ready[harness.private]
        assert ready[harness.research] == source_eid
        assert result.invalidated_lane_keys == (
            harness.vectors[1].configuration.lane_key, harness.vectors[0].configuration.lane_key,
        )
        private, research, engineering = harness.vectors
        assert source_eid in [row["eid"] for row in research.search_by_embedding((.2, .8, .1))]
        assert mood_eid in [row["eid"] for row in private.search_by_embedding((.8, .6, .0))]
        assert research.rebuild_count == private.rebuild_count == 2
        assert engineering.search_by_embedding((1., 0., 0.)) == [] and engineering.rebuild_count == 1
        mood = [view for view in _views(harness.connection, harness.private) if view.eid == mood_eid][0]
        assert mood.payload["type"] == "mood_drift"
        assert {"source_eid", "source_member_eids", "parent_eid"}.isdisjoint(mood.payload)
        assert not [view for view in _views(harness.connection, harness.research) if view.payload.get("type") == "mood_drift"]
    finally:
        _close(harness)


def test_e1_shared_direct_attach_uses_route_owned_created_motif_truth(tmp_path: Path):
    harness = _harness(tmp_path)
    try:
        created = harness.direct.execute(
            _request("E1:CREATED-MOTIF", vector=(.2, .8, .1)),
            _facts(),
        ).route_attempt.result
        attached = harness.direct.execute(
            _request("E1:ATTACHED-MOTIF", vector=(.2, .8, .1)),
            _facts(),
        ).route_attempt.result
        assert created is not None and attached is not None
        assert created.created_motif == created.motifs[0]
        assert attached.reinforced is False
        assert attached.created_motif is None
        assert attached.motifs == created.motifs
    finally:
        _close(harness)


def test_e1_cold_recovery_reopens_ready_source_mood_motif_and_external_state(tmp_path: Path):
    harness = _harness(tmp_path, affect={"last_tag": "sad", "last_conf": .7, "last_step": 0, "drift_hist": []})
    core_path, core_id = harness.capability.core_database_path, harness.capability.core_id
    private, research, engineering = harness.private, harness.research, harness.engineering
    try:
        result = harness.direct.execute(
            _request("E1:COLD", step=200), _facts(affect_tag="angry", affect_conf=.8),
        )
        source_eid = result.route_attempt.result.eid
        mood_eid = dict(result.post_write.ready_memory_eids)[private]
        assert harness.side.affect["last_tag"] == "angry"
        assert (tmp_path / "workflow" / "workspaces" / "ws" / "agents" / "aria" / "private" / "checkpoints").exists()
    finally:
        _close(harness)

    # No process-local owner is reused: recovery admits the old identities
    # from SQLite, opens new vector readers, and reloads the D1 owner state.
    with open_existing_native_core_connection(core_path) as reopened:
        connection = reopened.connection
        binding = prepare_native_memory_runtime_binding(
            connection=connection, core_database_path=core_path, expected_core_id=core_id,
            scope_bindings=(private.runtime_scope, research.runtime_scope, engineering.runtime_scope),
            representation_lane=_lane(),
        )
        recovered_capability = prepare_native_fabric_routing_capability(
            binding=binding, connection=connection, routing_scopes=(private, research, engineering),
            expected_core_id=core_id,
        )
        assert [view.eid for view in _views(connection, research)] == [source_eid]
        assert [view.eid for view in _views(connection, private)] == [mood_eid]
        motifs = NativeMotifRuntimeReader(connection).list_runtime_motifs(
            motif_alias_namespace_id=research.motif_alias_namespace_id,
            domain_id="research", semantic_scope_id=research.runtime_scope.semantic_scope_id,
        )
        assert motifs and motifs[0].read_model.member_count == 1
        assert _views(connection, engineering) == ()

    reloaded_side = _SideStore(tmp_path)
    assert reloaded_side.affect["last_tag"] == "angry"
    cold_private = _vector_runtime(recovered_capability, private)
    cold_research = _vector_runtime(recovered_capability, research)
    cold_engineering = _vector_runtime(recovered_capability, engineering)
    try:
        assert mood_eid in [row["eid"] for row in cold_private.search_by_embedding((.8, .6, .0))]
        assert source_eid in [row["eid"] for row in cold_research.search_by_embedding((.2, .8, .1))]
        assert cold_engineering.search_by_embedding((1., 0., 0.)) == []
        assert tuple(runtime.rebuild_count for runtime in (cold_private, cold_research, cold_engineering)) == (1, 1, 1)
    finally:
        cold_private.close()
        cold_research.close()
        cold_engineering.close()


def test_e1_refuses_compression_and_wrong_domain_before_effects(tmp_path: Path):
    harness = _harness(tmp_path)
    try:
        before = _counts(harness.connection)
        harness.owner._compress_enable = True
        with pytest.raises(SubstrateConfigurationError, match="TORMENT_COMPRESS_ENABLE=false"):
            harness.direct.execute(_request("E1:COMPRESS"), _facts())
        assert _counts(harness.connection) == before
        assert not harness.field.packets and not harness.bridges.calls and harness.side.affect["last_tag"] is None
        harness.owner._compress_enable = False

        before = _counts(harness.connection)
        refusal = harness.direct.execute(_request("E1:UNCLAIMED", domain_id="creative"), _facts())
        assert refusal.route_attempt.qualification.reason_code == "SCOPE_NOT_CLAIMED"
        assert refusal.post_write is None and refusal.invalidated_lane_keys == ()
        assert _counts(harness.connection) == before
        assert not harness.field.packets and not harness.bridges.calls
    finally:
        _close(harness)


def test_e1_recovers_interrupted_and_lost_responses_without_stale_lane_rebuilds(tmp_path: Path):
    harness = _harness(tmp_path, affect={"last_tag": "sad", "last_conf": .7, "last_step": 0, "drift_hist": []})
    try:
        interrupted = _request("E1:INTERRUPTED", step=10)
        with pytest.raises(RuntimeError, match="committed native new-memory source"):
            harness.direct.execute(interrupted, _facts(), _test_stop_after="source")
        committed_source = _views(harness.connection, harness.research)
        assert len(committed_source) == 1 and not committed_source[0].representation_references
        recovered = harness.direct.execute(interrupted, _facts())
        assert recovered.route_attempt.result.eid == committed_source[0].eid
        assert recovered.invalidated_lane_keys == (harness.vectors[1].configuration.lane_key,)
        assert len(_views(harness.connection, harness.research)) == 1
        assert harness.vectors[1].search_by_embedding((.2, .8, .1))[0]["eid"] == committed_source[0].eid

        lost = _request("E1:LOST", step=200, vector=(.8, .2, .0))
        first = harness.direct.execute(lost, _facts(affect_tag="angry", affect_conf=.8))
        source_eid = first.route_attempt.result.eid
        mood_eid = dict(first.post_write.ready_memory_eids)[harness.private]
        for runtime, vector in zip(harness.vectors[:2], ((.8, .2, .0), (.8, .6, .0)), strict=True):
            runtime.search_by_embedding(vector)
        baseline = tuple(runtime.rebuild_count for runtime in harness.vectors)
        retry = harness.direct.execute(lost, _facts(affect_tag="angry", affect_conf=.8))
        assert retry.route_attempt.result.eid == source_eid
        # D1's established lost-response law detects the already-recorded
        # private mood side effect and does not present it as a new READY
        # representation on the retry.  The original mood EID stays current.
        assert retry.post_write.ready_memory_eids == ((harness.research, source_eid),)
        assert any(view.eid == mood_eid for view in _views(harness.connection, harness.private))
        assert retry.invalidated_lane_keys == ()
        assert tuple(runtime.rebuild_count for runtime in harness.vectors) == baseline
        assert len(_views(harness.connection, harness.research)) == 2
        assert len(_views(harness.connection, harness.private)) == 1
    finally:
        _close(harness)


def test_e1_failure_boundaries_preserve_existing_consumer_law(tmp_path: Path, monkeypatch):
    harness = _harness(tmp_path, affect={"last_tag": "sad", "last_conf": .7, "last_step": 0, "drift_hist": []})
    try:
        import torment_service.substrate.native_post_write_runtime as post_runtime
        from torment_service.motif_maintenance import NativeMotifMaintenanceAdapter
        from torment_service.substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntime
        from torment_service.substrate.native_world_runtime import NativeWorldRuntime

        trace: list[str] = []
        original_character = LegacyFabricPostWriteAdapter._run_character_drift
        original_proposal = LegacyFabricPostWriteAdapter._run_proposal
        original_d6 = NativeFabricPostWriteAdapter._run_shared_compression_disabled_noop

        def character(*args, **kwargs):
            trace.append("character")
            return original_character(*args, **kwargs)

        def proposal(*args, **kwargs):
            trace.append("proposal")
            return original_proposal(*args, **kwargs)

        def d6(*args, **kwargs):
            trace.append("compression")
            return original_d6(*args, **kwargs)

        monkeypatch.setattr(LegacyFabricPostWriteAdapter, "_run_character_drift", character)
        monkeypatch.setattr(LegacyFabricPostWriteAdapter, "_run_proposal", proposal)
        monkeypatch.setattr(NativeFabricPostWriteAdapter, "_run_shared_compression_disabled_noop", d6)
        monkeypatch.setattr(NativeMotifMaintenanceAdapter, "update_entropy_and_suggest", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("M1")))
        monkeypatch.setattr(NativeDerivedMemoryRuntime, "maybe_emit_mood_drift", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("mood")))
        monkeypatch.setattr(NativeWorldRuntime, "write_trajectory_genesis_for_post_write", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("trajectory")))
        monkeypatch.setattr(post_runtime, "save_checkpoint", lambda **_kwargs: (_ for _ in ()).throw(OSError("checkpoint")))
        harness.field.fail = True
        harness.bridges.fail = True
        with pytest.raises(OSError, match="bridge failure"):
            harness.direct.execute(_request("E1:FAIL", step=20), _facts(affect_tag="angry", affect_conf=.8))
        assert trace == ["character", "compression", "proposal"]
        assert harness.owner.telemetry[-1]["gate_outcome"] == "error"
        # The source was READY before the fail-propagating B1 slot and its one
        # affected lane was still dirtied; no failed mood source is claimed.
        assert harness.vectors[1].last_invalidation_reason == "E1 READY representation changed"
        assert len(_views(harness.connection, harness.private)) == 0
    finally:
        _close(harness)
