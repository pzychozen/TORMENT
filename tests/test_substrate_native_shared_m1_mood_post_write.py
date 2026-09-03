"""D1 qualification: shared M1, D0 anchors, and private-target mood drift."""
from __future__ import annotations

from dataclasses import replace
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from torment_service.collective_models import ConvergenceEvent, MemoryGovernanceFlags
from torment_service.post_write_runtime import (
    FabricPostWriteContext,
    LegacyFabricPostWriteAdapter,
    PostWriteStorageOutcome,
)
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_existing_native_core_connection, open_temporary_test_connection
from torment_service.substrate.errors import SubstrateConfigurationError, SubstrateIdempotencyConflict
from torment_service.substrate.fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteRequest,
    NativeFabricRoutingScope,
    prepare_native_fabric_routing_capability,
)
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.native_derived_memory_runtime import (
    NativeDerivedMemoryRuntimeConfiguration,
)
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
    NativePostWriteRouteWitness,
    NativeSharedTriggerMoodDriftBinding,
    prepare_native_fabric_post_write_adapter,
)
from torment_service.substrate.runtime_binding import (
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
    prepare_native_memory_runtime_binding,
)
from torment_service.substrate.schema import create_schema
from torment_service.derived_memory_runtime import DerivedMemoryRuntimeContext


def _id():
    return generate_native_id()


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane(
        "synthetic", "synthetic-v1", 3, "COMPAT_EMBEDDING", 1,
        "compat-embedding-v1", "RAW_VECTOR", "float32",
    )


def _scope(connection, *, kind: str, label: str) -> NativeFabricRoutingScope:
    memory_identity, semantic_scope, memory_alias = _id(), _id(), _id()
    motif_identity, membership_identity, motif_alias, idempotency = (_id() for _ in range(4))
    for value, name in (
        (memory_identity, "memory"), (motif_identity, "motif"), (membership_identity, "membership"),
    ):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"d1:{label}:{name}"),
        )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(semantic_scope), f"d1:{label}:semantic"),
    )
    for value, name in ((memory_alias, "memory-alias"), (motif_alias, "motif-alias")):
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"d1:{label}:{name}"),
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), f"d1:{label}"))
    if kind == "PRIVATE_AGENT":
        runtime_scope = NativeMemoryRuntimeScope(
            workspace_id="ws", scope_kind=kind, legacy_source_namespace_id=memory_alias,
            identity_namespace_id=memory_identity, semantic_scope_id=semantic_scope, agent_id="aria",
        )
    else:
        runtime_scope = NativeMemoryRuntimeScope(
            workspace_id="ws", scope_kind=kind, legacy_source_namespace_id=memory_alias,
            identity_namespace_id=memory_identity, semantic_scope_id=semantic_scope, domain_id="research",
        )
    return NativeFabricRoutingScope(
        runtime_scope=runtime_scope, motif_alias_namespace_id=motif_alias,
        motif_identity_namespace_id=motif_identity, membership_identity_namespace_id=membership_identity,
        idempotency_namespace_id=idempotency,
    )


def _prepared(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "d1-shared-m1-mood.db")
    metadata = create_schema(qualified.connection)
    connection = qualified.connection
    private = _scope(connection, kind="PRIVATE_AGENT", label="aria")
    shared = _scope(connection, kind="SHARED_DOMAIN", label="research")
    binding = prepare_native_memory_runtime_binding(
        connection=connection, core_database_path=qualified.database_path,
        expected_core_id=native_id_from_bytes(metadata.core_id),
        scope_bindings=(private.runtime_scope, shared.runtime_scope), representation_lane=_lane(),
    )
    capability = prepare_native_fabric_routing_capability(
        binding=binding, connection=connection, routing_scopes=(private, shared),
        expected_core_id=native_id_from_bytes(metadata.core_id),
    )
    return qualified, connection, capability, private, shared


class _SideStore:
    def __init__(self, *, affect=None, fail_affect_saves: set[int] | None = None) -> None:
        self.anchor = {"motifs": {}}
        self.affect = affect or {"last_tag": None, "last_conf": 0.0, "last_step": -10**9, "drift_hist": []}
        self.events: list[dict[str, object]] = []
        self._fail_affect_saves = fail_affect_saves or set()

    def load_anchor_state(self, **_kwargs):
        return json.loads(json.dumps(self.anchor))

    def save_anchor_state(self, *, state, **_kwargs):
        self.anchor = json.loads(json.dumps(state))
        raise AssertionError("D1 shared-trigger anchors must not mutate anchors.json")

    def load_affect_state(self, **_kwargs):
        return json.loads(json.dumps(self.affect))

    def save_affect_state(self, *, state, **_kwargs):
        event = json.loads(json.dumps(state))
        self.events.append(event)
        if len(self.events) in self._fail_affect_saves:
            raise OSError("injected affect side-store failure")
        self.affect = event


class _HivemindField:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.packets: list[tuple[object, np.ndarray]] = []

    def append_packet(self, packet, *, embedding):
        if self.fail:
            raise OSError("injected collective-field failure")
        self.packets.append((packet, np.asarray(embedding).copy()))
        return ConvergenceEvent(
            event_id="d2-convergence", workspace_id="ws", domain_id="research",
            participating_agents=["aria", "bryn"], source_packets=["other", packet.packet_id],
            source_eids=[17, packet.source_eid], confidence=.95,
        )


class _HivemindProposalBridge:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def maybe_draft_proposal(self, **kwargs) -> None:
        self.calls.append(kwargs)


class _HivemindOwner:
    def __init__(self, field: _HivemindField, bridge: _HivemindProposalBridge) -> None:
        self._log = logging.getLogger("d2.shared.hivemind.owner")
        self._hivemind_enable = True
        self._hivemind_telemetry_enable = True
        self.character_store = SimpleNamespace(load_state=lambda *_args: None)
        self._field = field
        self._bridge = bridge
        self.telemetry: list[dict[str, object]] = []

    def _get_collective_field(self, _workspace_id: str) -> _HivemindField:
        return self._field

    def _get_proposal_bridge(self, _workspace_id: str) -> _HivemindProposalBridge:
        return self._bridge

    def _emit_hivemind_packet_telemetry(self, **kwargs) -> None:
        self.telemetry.append(kwargs)


def _policy(*, auto_merge: bool = False) -> dict[str, object]:
    return {
        "motif_entropy_target_n": 2,
        "motif_entropy_high": 0.0,
        "motif_merge_similarity": 0.93,
        "motif_merge_max_suggestions": 20,
        "auto_merge_motifs": auto_merge,
        "auto_merge_entropy_trigger": 0.0 if auto_merge else 0.80,
    }


def _external(tmp_path: Path, *, auto_merge: bool = False):
    workspace = SimpleNamespace(
        data_dir=str(tmp_path / "workflow"), domain_policies={"research": _policy(auto_merge=auto_merge)},
    )
    owner = SimpleNamespace(_log=logging.getLogger("d1.shared.post-write"))
    return NativePostWriteExternalDependencies(
        owner=owner, workspace=workspace, identity=SimpleNamespace(seed={}), agent_key="aria",
        detect_canon_conflict=lambda *_args: (False, 0.0, "unused"),
        proposal_allowed=lambda *_args, **_kwargs: False,
        hivemind_log=logging.getLogger("d1.shared.hivemind"),
    )


def _template(private: NativeFabricRoutingScope, side: _SideStore) -> NativeDerivedMemoryRuntimeConfiguration:
    return NativeDerivedMemoryRuntimeConfiguration(
        workspace_id="ws", agent_id="aria", domain_id="research",
        legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
        motif_alias_namespace_id=private.motif_alias_namespace_id,
        memory_identity_namespace_id=private.runtime_scope.identity_namespace_id,
        semantic_scope_id=private.runtime_scope.semantic_scope_id,
        idempotency_namespace_id=private.idempotency_namespace_id,
        parent_native_operation_key="template-never-used", expected_dimension=3,
        embed=lambda _text: np.asarray((2.0, 0.6, 0.0), dtype=np.float32),
        embedder_provider="synthetic", embedder_model="synthetic-v1", side_store=side,
        now_ts=lambda: 777,
    )


def _configuration(
    tmp_path: Path,
    *,
    private: NativeFabricRoutingScope,
    shared: NativeFabricRoutingScope,
    side: _SideStore,
    auto_merge: bool = False,
) -> NativePostWriteQualificationConfiguration:
    template = _template(private, side)
    return NativePostWriteQualificationConfiguration(
        routing_scope=shared,
        profile=NativePostWriteQualificationProfile.core_staging_with_shared_m1_mood_drift(),
        external=_external(tmp_path, auto_merge=auto_merge), derived_runtime_template=None,
        motif_suggestion_maintenance_required=False, persistent_trajectory_evidence_required=False,
        checkpoint_snapshots_required=False, bridge_suggestions_required=False, deep_memory_required=False,
        shared_motif_suggestion_maintenance_required=True,
        shared_mood_drift_binding=NativeSharedTriggerMoodDriftBinding(private, template),
    )


def _hivemind_configuration(
    *,
    shared: NativeFabricRoutingScope,
    field: _HivemindField,
    bridge: _HivemindProposalBridge,
) -> tuple[NativePostWriteQualificationConfiguration, _HivemindOwner, object]:
    owner = _HivemindOwner(field, bridge)
    proposal_registry = object()
    workspace = SimpleNamespace(
        domain_policies={"research": _policy()},
        proposals={"research": proposal_registry},
    )
    return (
        NativePostWriteQualificationConfiguration(
            routing_scope=shared,
            profile=NativePostWriteQualificationProfile.core_staging_with_shared_hivemind_packet_emission(),
            external=NativePostWriteExternalDependencies(
                owner=owner, workspace=workspace, identity=SimpleNamespace(seed={}), agent_key="aria",
                detect_canon_conflict=lambda *_args: (False, 0.0, "unused"),
                proposal_allowed=lambda *_args, **_kwargs: False,
                hivemind_log=logging.getLogger("d2.shared.hivemind"),
            ),
            derived_runtime_template=None, motif_suggestion_maintenance_required=False,
            persistent_trajectory_evidence_required=False, checkpoint_snapshots_required=False,
            bridge_suggestions_required=False, deep_memory_required=False,
            shared_hivemind_packet_emission_required=True,
        ),
        owner,
        proposal_registry,
    )


def _request(key: str, step: int, vector) -> NativeFabricRouteRequest:
    return NativeFabricRouteRequest(
        workspace_id="ws", scope="shared", agent_id="aria", domain_id="research",
        native_operation_key=key, embedder_lane=_lane(), summary=f"shared {key}",
        memory_type="reflection", memory_class="core", strength=.8, confidence=.9,
        half_life_days=20., logical_step=step, created_ts=step, last_active_ts=step,
        last_reinforced_ts=step, incoming_embedding=vector,
        provenance=ProvenanceV1.for_user_ingest(step=step), governance=MemoryGovernanceFlags(),
        flexible_payload={"d1": True},
    )


def _shared_created(capability, *, key="D1:CURRENT", step=200, vector=(0., 1., 0.)):
    router = NativeFabricMemoryRouter(capability)
    seed = router.route(_request("D1:SEED", 1, (1., 0., 0.))).result
    result = router.route(_request(key, step, vector)).result
    assert seed is not None and result is not None and result.reinforced is False
    return result, _request(key, step, vector)


def _context(result, request, *, affect_tag=None, affect_conf=None) -> FabricPostWriteContext:
    return FabricPostWriteContext.make(
        workspace_id="ws", agent_id="aria", scope="shared", chosen_domain="research", step=request.logical_step,
        storage_outcome=PostWriteStorageOutcome.CREATED_NEW, stored=result.stored, eid=result.eid,
        created_motif=result.motifs[0], motif_ids=result.motifs, half_life_days=request.half_life_days,
        summary=request.summary, embedding=np.asarray(request.incoming_embedding, dtype=np.float32),
        memory_class=request.memory_class, memory_type=request.memory_type, strength=request.strength,
        confidence=request.confidence, promotion_score=.0, stability_delta=.0, tri_mod={}, debug={},
        srg_state=None, phase_durations={}, state_symbol=None, affect_tag=affect_tag,
        affect_conf=affect_conf, skip_packet_emission=True,
    )


def _views(connection, scope: NativeFabricRoutingScope):
    rows = connection.execute(
        "SELECT alias_value FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID' ORDER BY CAST(alias_value AS INTEGER)",
        (native_id_to_bytes(scope.runtime_scope.legacy_source_namespace_id),),
    ).fetchall()
    facade = NativeMemoryCompatibilityFacade(connection)
    return tuple(facade.get_memory_by_eid(
        legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id, eid=int(row[0]),
    ) for row in rows)


def _moods(connection, scope: NativeFabricRoutingScope):
    return tuple(view for view in _views(connection, scope) if view.payload.get("type") == "mood_drift")


def _run(capability, configuration, result, request, context):
    return prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration).run(
        context, route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
    )


def test_d1_shared_m1_retains_anchor_noops_and_creates_only_private_mood(tmp_path: Path, monkeypatch):
    qualified, connection, capability, private, shared = _prepared(tmp_path)
    try:
        side = _SideStore(affect={"last_tag": "sad", "last_conf": .7, "last_step": 1, "drift_hist": []})
        configuration = _configuration(tmp_path, private=private, shared=shared, side=side)
        result, request = _shared_created(capability)
        import torment_service.substrate.native_derived_memory_runtime as native_runtime

        trace: list[tuple[str, object]] = []
        anchor = native_runtime.NativeDerivedMemoryRuntime.maybe_emit_identity_anchor
        refine = native_runtime.NativeDerivedMemoryRuntime.refine_identity_anchors
        mood = native_runtime.NativeDerivedMemoryRuntime.maybe_emit_mood_drift

        def record_anchor(runtime, context):
            outcome = anchor(runtime, context)
            trace.append(("anchor", outcome))
            return outcome

        def record_refine(runtime, context):
            outcome = refine(runtime, context)
            trace.append(("refine", outcome))
            return outcome

        def record_mood(runtime, context):
            outcome = mood(runtime, context)
            trace.append(("mood", outcome))
            return outcome

        # The normal mood path has a distinct prior tag and therefore never
        # needs the private retry enumeration.  Any anchor read would fail.
        monkeypatch.setattr(native_runtime.NativeDerivedMemoryRuntime, "_list_current_views", lambda _self: (_ for _ in ()).throw(AssertionError("anchor read private state")))
        monkeypatch.setattr(native_runtime.NativeDerivedMemoryRuntime, "maybe_emit_identity_anchor", record_anchor)
        monkeypatch.setattr(native_runtime.NativeDerivedMemoryRuntime, "refine_identity_anchors", record_refine)
        monkeypatch.setattr(native_runtime.NativeDerivedMemoryRuntime, "maybe_emit_mood_drift", record_mood)
        assert _run(capability, configuration, result, request, _context(result, request, affect_tag="angry", affect_conf=.8)).proposal_id is None
        assert trace[0:2] == [("anchor", None), ("refine", None)]
        assert trace[2][0] == "mood" and isinstance(trace[2][1], int)
        assert side.anchor == {"motifs": {}}
        assert len(_moods(connection, shared)) == 0
        moods = _moods(connection, private)
        assert len(moods) == 1
        mood_row = moods[0]
        assert (mood_row.payload["workspace_id"], mood_row.payload["domain_id"], mood_row.payload["scope"], mood_row.payload["agent_id"]) == ("ws", "research", "private", "aria")
        assert (mood_row.payload["mood_from"], mood_row.payload["mood_to"], mood_row.payload["affect_conf"]) == ("sad", "angry", .8)
        assert {"source_eid", "source_member_eids", "parent_eid"}.isdisjoint(mood_row.payload)
        assert len(mood_row.representation_references) == 1 and mood_row.representation_references[0].usable is True
        assert side.affect["drift_hist"] == [{"from": "sad", "to": "angry", "step": 200, "conf": .8}]
        workflow = tmp_path / "workflow" / "workspaces" / "ws" / "domains" / "research"
        events = [json.loads(line) for line in (workflow / "motif_events.jsonl").read_text(encoding="utf-8").splitlines()]
        assert events[0]["type"] == "MOTIF_ENTROPY" and not (workflow / "motifs.json").exists()
    finally:
        qualified.close()


def test_i4b2_shared_witness_preserves_existing_shared_m1_dispatch(tmp_path: Path, monkeypatch):
    qualified, _connection, capability, private, shared = _prepared(tmp_path)
    try:
        side = _SideStore()
        configuration = _configuration(tmp_path, private=private, shared=shared, side=side)
        result, request = _shared_created(capability, key="D1:I4B2-SHARED-WITNESS")
        split_witness = replace(result, created_motif=None, precommit_true_split=True)
        adapter = prepare_native_fabric_post_write_adapter(
            capability=capability,
            configuration=configuration,
        )
        dispatches: list[str] = []
        original_dispatch = LegacyFabricPostWriteAdapter._run_motif_maintenance_and_anchors

        def observe_shared_dispatch(consumers, context):
            dispatches.append(context.scope)
            return original_dispatch(consumers, context)

        monkeypatch.setattr(
            LegacyFabricPostWriteAdapter,
            "_run_motif_maintenance_and_anchors",
            observe_shared_dispatch,
        )
        monkeypatch.setattr(
            adapter,
            "_run_i4b2_true_split_tail",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("shared post-write entered the private I4B-2 tail")
            ),
        )

        assert adapter.run(
            replace(_context(result, request), created_motif=None),
            route_witness=NativePostWriteRouteWitness(split_witness, request.native_operation_key),
        ).proposal_id is None
        assert dispatches == ["shared"]
    finally:
        qualified.close()


def test_d1_shared_m1_no_mood_and_m2_auto_merge_reuse(tmp_path: Path):
    qualified, connection, capability, private, shared = _prepared(tmp_path)
    try:
        side = _SideStore()
        configuration = _configuration(tmp_path, private=private, shared=shared, side=side, auto_merge=True)
        # Route composition creates the second motif below its normal join
        # threshold; D1 passes the frozen policy threshold to M2, which then
        # sees the same pair as a merge candidate.
        configuration.external.workspace.domain_policies["research"]["motif_merge_similarity"] = .5
        result, request = _shared_created(capability, vector=(.6, .8, 0.))
        _run(capability, configuration, result, request, _context(result, request))
        assert len(_moods(connection, private)) == 0 and not side.events
        # The D1 profile inherits only M2's already-qualified native merger;
        # no legacy registry is introduced by the shared M1 binding.
        assert NativePostWriteQualificationProfile.core_staging_with_shared_m1_mood_drift().motif_auto_merge.name == "QUALIFIED"
        workflow = tmp_path / "workflow" / "workspaces" / "ws" / "domains" / "research"
        events = [json.loads(line) for line in (workflow / "motif_events.jsonl").read_text(encoding="utf-8").splitlines()]
        assert any(event["type"] == "MOTIF_MERGED" for event in events)
        assert not (workflow / "motifs.json").exists()
    finally:
        qualified.close()


def test_d1_m1_and_mood_failures_keep_independent_order_boundaries(tmp_path: Path, monkeypatch):
    qualified, connection, capability, private, shared = _prepared(tmp_path)
    try:
        import torment_service.substrate.native_derived_memory_runtime as native_runtime
        import torment_service.substrate.native_post_write_runtime as post_runtime

        side = _SideStore(affect={"last_tag": "sad", "last_conf": .7, "last_step": 1, "drift_hist": []})
        configuration = _configuration(tmp_path, private=private, shared=shared, side=side)
        result, request = _shared_created(capability, key="D1:M1-FAIL")
        trace: list[str] = []
        original_anchor = native_runtime.NativeDerivedMemoryRuntime.maybe_emit_identity_anchor
        original_refine = native_runtime.NativeDerivedMemoryRuntime.refine_identity_anchors
        original_mood = native_runtime.NativeDerivedMemoryRuntime.maybe_emit_mood_drift
        original_m1 = post_runtime.NativeMotifMaintenanceAdapter.update_entropy_and_suggest

        def fail_m1(*_args, **_kwargs):
            trace.append("m1")
            raise RuntimeError("injected M1 failure")

        def anchor(runtime, context):
            trace.append("anchor")
            return original_anchor(runtime, context)

        def refine(runtime, context):
            trace.append("refine")
            return original_refine(runtime, context)

        def mood(runtime, context):
            trace.append("mood")
            return original_mood(runtime, context)

        monkeypatch.setattr(post_runtime.NativeMotifMaintenanceAdapter, "update_entropy_and_suggest", fail_m1)
        monkeypatch.setattr(native_runtime.NativeDerivedMemoryRuntime, "maybe_emit_identity_anchor", anchor)
        monkeypatch.setattr(native_runtime.NativeDerivedMemoryRuntime, "refine_identity_anchors", refine)
        monkeypatch.setattr(native_runtime.NativeDerivedMemoryRuntime, "maybe_emit_mood_drift", mood)
        _run(capability, configuration, result, request, _context(result, request, affect_tag="angry", affect_conf=.8))
        assert trace == ["m1", "anchor", "refine", "mood"] and len(_moods(connection, private)) == 1

        # A fresh shared CREATED_NEW call reaches the D1 return boundary after
        # an independently fail-soft mood exception; world and later slots are
        # not invoked by this adapter branch.
        side2 = _SideStore(affect={"last_tag": "sad", "last_conf": .7, "last_step": 1, "drift_hist": []})
        configuration2 = _configuration(tmp_path / "mood-failure", private=private, shared=shared, side=side2)
        request2 = _request("D1:MOOD-FAIL", 300, (0., 0., 1.))
        result2 = NativeFabricMemoryRouter(capability).route(request2).result
        assert result2 is not None and result2.reinforced is False
        monkeypatch.setattr(post_runtime.NativeMotifMaintenanceAdapter, "update_entropy_and_suggest", original_m1)

        def fail_mood(_runtime, _context):
            raise RuntimeError("injected mood failure")

        monkeypatch.setattr(native_runtime.NativeDerivedMemoryRuntime, "maybe_emit_mood_drift", fail_mood)
        assert _run(capability, configuration2, result2, request2, _context(result2, request2, affect_tag="angry", affect_conf=.8)).proposal_id is None
        assert len(_moods(connection, private)) == 1
    finally:
        qualified.close()


@pytest.mark.parametrize("failure", ("initial-save", "creation", "history-save"))
def test_d1_affect_side_store_failure_topology(tmp_path: Path, monkeypatch, failure: str):
    qualified, connection, capability, private, shared = _prepared(tmp_path)
    try:
        fail_saves = {1} if failure == "initial-save" else ({2} if failure == "history-save" else set())
        side = _SideStore(
            affect={"last_tag": "sad", "last_conf": .7, "last_step": 1, "drift_hist": []},
            fail_affect_saves=fail_saves,
        )
        configuration = _configuration(tmp_path, private=private, shared=shared, side=side)
        result, request = _shared_created(capability, key=f"D1:SIDE:{failure}")
        if failure == "creation":
            import torment_service.substrate.native_derived_memory_runtime as native_runtime
            monkeypatch.setattr(
                native_runtime.NativeDerivedMemoryCreationService, "create",
                lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("injected creation failure")),
            )
        _run(capability, configuration, result, request, _context(result, request, affect_tag="angry", affect_conf=.8))
        if failure == "creation":
            assert not _moods(connection, private)
            assert side.affect["last_tag"] == "angry" and side.affect["drift_hist"] == []
        elif failure == "initial-save":
            assert len(_moods(connection, private)) == 1
            assert side.affect["last_tag"] == "sad"
            assert side.affect["drift_hist"] == [{"from": "sad", "to": "angry", "step": 200, "conf": .8}]
        else:
            assert len(_moods(connection, private)) == 1
            assert side.affect["last_tag"] == "angry" and side.affect["drift_hist"] == []
    finally:
        qualified.close()


@pytest.mark.parametrize("stop", ("source", "pending", "ready"))
def test_d1_shared_mood_response_loss_recovers_one_private_ready_row(tmp_path: Path, monkeypatch, stop: str):
    qualified, connection, capability, private, shared = _prepared(tmp_path)
    try:
        import torment_service.substrate.native_derived_memory_runtime as native_runtime

        side = _SideStore(affect={"last_tag": "sad", "last_conf": .7, "last_step": 1, "drift_hist": []})
        configuration = _configuration(tmp_path, private=private, shared=shared, side=side)
        result, request = _shared_created(capability, key=f"D1:LOSS:{stop}")
        context = _context(result, request, affect_tag="angry", affect_conf=.8)
        original = native_runtime.NativeDerivedMemoryCreationService.create
        first = True

        def interrupt_once(service, creation_request, **kwargs):
            nonlocal first
            if first:
                first = False
                return original(service, creation_request, _test_stop_after=stop, **kwargs)
            return original(service, creation_request, **kwargs)

        monkeypatch.setattr(native_runtime.NativeDerivedMemoryCreationService, "create", interrupt_once)
        _run(capability, configuration, result, request, context)
        interrupted = _moods(connection, private)
        assert len(interrupted) == 1 and side.affect["last_tag"] == "angry" and side.affect["drift_hist"] == []

        # A changed retry reaches the same existing child source and fails
        # closed rather than publishing a second private mood row.
        with open_existing_native_core_connection(capability.core_database_path) as opened:
            changed = NativeFabricMemoryRouter(capability).bind_derived_memory_runtime(
                opened.connection,
                configuration=replace(_template(private, side), parent_native_operation_key=request.native_operation_key),
            )
            with pytest.raises(SubstrateIdempotencyConflict):
                changed.maybe_emit_mood_drift(DerivedMemoryRuntimeContext(
                    "ws", "aria", "research", "shared", request.logical_step, result.motifs, "angry", .9,
                ))
        _run(capability, configuration, result, request, context)
        recovered = _moods(connection, private)
        assert len(recovered) == 1 and recovered[0].eid == interrupted[0].eid
        assert len(recovered[0].representation_references) == 1
        assert recovered[0].representation_references[0].usable is True
        assert side.affect["drift_hist"] == [{"from": "sad", "to": "angry", "step": 200, "conf": .8}]
        assert not _moods(connection, shared)
    finally:
        qualified.close()


def test_d1_profile_requires_a_separate_admitted_private_mood_target(tmp_path: Path):
    qualified, _connection, capability, private, shared = _prepared(tmp_path)
    try:
        side = _SideStore()
        configuration = _configuration(tmp_path, private=private, shared=shared, side=side)
        with pytest.raises(SubstrateConfigurationError, match="requires a private mood-drift binding"):
            prepare_native_fabric_post_write_adapter(
                capability=capability, configuration=replace(configuration, shared_mood_drift_binding=None),
            )
        with pytest.raises(SubstrateConfigurationError, match="must not bind a source-scope"):
            prepare_native_fabric_post_write_adapter(
                capability=capability, configuration=replace(configuration, derived_runtime_template=_template(private, side)),
            )
        with pytest.raises(SubstrateConfigurationError, match="must be prepared separately"):
            prepare_native_fabric_post_write_adapter(
                capability=capability, configuration=replace(configuration, shared_bridge_suggestions_required=True),
            )
    finally:
        qualified.close()


def test_d2_shared_hivemind_uses_current_shared_native_source_and_external_owners(tmp_path: Path):
    qualified, connection, capability, _private, shared = _prepared(tmp_path)
    try:
        field = _HivemindField()
        bridge = _HivemindProposalBridge()
        configuration, owner, proposal_registry = _hivemind_configuration(
            shared=shared, field=field, bridge=bridge,
        )
        result, request = _shared_created(capability, key="D2:HIVEMIND", step=250, vector=(.2, .8, .1))
        context = replace(
            _context(result, request), skip_packet_emission=False,
            debug={"coherence": .6}, tri_mod={"cycle_stage": "S2", "identity_state": "s4"},
            srg_state={"R_band": 3, "heartbeat_class": "warm", "is_crystal": True},
        )
        adapter = prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)
        tables = ("objects", "object_revisions", "operations", "semantic_transitions", "representations")
        before = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables)

        adapter.run(context, route_witness=NativePostWriteRouteWitness(result, request.native_operation_key))
        adapter.run(context, route_witness=NativePostWriteRouteWitness(result, request.native_operation_key))

        after = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables)
        assert after == before
        assert len(field.packets) == 2  # Existing CollectiveField remains the external retry/dedup owner.
        packet, embedding = field.packets[0]
        assert (packet.workspace_id, packet.agent_id, packet.domain_id, packet.source_eid) == (
            "ws", "aria", "research", result.eid,
        )
        assert packet.srg_band == 3 and packet.srg_heartbeat_class == "warm" and packet.srg_is_crystal is True
        assert embedding.tolist() == pytest.approx([.2, .8, .1])
        assert len(bridge.calls) == 2
        assert bridge.calls[0]["proposal_registry"] is proposal_registry
        assert bridge.calls[0]["event"]["source_eids"] == [17, result.eid]
        assert [row["gate_outcome"] for row in owner.telemetry] == ["emitted", "emitted"]
    finally:
        qualified.close()


def test_d2_shared_hivemind_failure_is_fail_soft_and_profiles_do_not_compose(tmp_path: Path):
    qualified, connection, capability, private, shared = _prepared(tmp_path)
    try:
        field = _HivemindField(fail=True)
        bridge = _HivemindProposalBridge()
        configuration, owner, _proposal_registry = _hivemind_configuration(
            shared=shared, field=field, bridge=bridge,
        )
        result, request = _shared_created(capability, key="D2:HIVEMIND-FAIL", step=251, vector=(.2, .8, .1))
        context = replace(_context(result, request), skip_packet_emission=False, debug={"coherence": .6})
        tables = ("objects", "object_revisions", "operations", "semantic_transitions", "representations")
        before = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables)
        adapter = prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)

        assert adapter.run(context, route_witness=NativePostWriteRouteWitness(result, request.native_operation_key)).proposal_id is None
        assert tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables) == before
        assert not bridge.calls and owner.telemetry[-1]["gate_outcome"] == "error"
        with pytest.raises(SubstrateConfigurationError, match="does not qualify"):
            prepare_native_fabric_post_write_adapter(
                capability=capability,
                configuration=replace(configuration, profile=NativePostWriteQualificationProfile.core_staging()),
            )
        side = _SideStore()
        d1 = _configuration(tmp_path, private=private, shared=shared, side=side)
        with pytest.raises(SubstrateConfigurationError, match="prepared separately"):
            prepare_native_fabric_post_write_adapter(
                capability=capability,
                configuration=replace(d1, shared_hivemind_packet_emission_required=True),
            )
    finally:
        qualified.close()
