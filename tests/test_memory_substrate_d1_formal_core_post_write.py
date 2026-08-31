"""Synthetic-only 7G5D1I coverage for the live formal post-write posture."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.memory_substrate_d1_trace_replay_v1.formal_core_post_write import (
    FormalConflictSurface,
    FormalPostWriteDependencyError,
    FormalProposalSurface,
    build_formal_native_post_write_configuration,
    validate_formal_post_write_external_dependencies,
)
from experiments.memory_substrate_d1_trace_replay_v1.formal_core_executor import CoreFrozenFixture
from experiments.memory_substrate_d1_trace_replay_v1.formal_core_ports import CoreNoWritePostWriteFacts
from experiments.memory_substrate_d1_trace_replay_v1.native_replay import NativeCoreStorageSnapshot, NativeReplayHarness
from experiments.memory_substrate_d1_trace_replay_v1.legacy_capture import InitialPostWritePlaceholderPosture
from torment_service.collective_models import MemoryGovernanceFlags
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
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteRouteWitness,
    prepare_native_fabric_post_write_adapter,
)
from torment_service.substrate.native_memory_runtime_access import NativePostWriteMemoryAccess
from torment_service.substrate.runtime_binding import (
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
    prepare_native_memory_runtime_binding,
)
from torment_service.substrate.schema import create_schema


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane(
        provider="hash", model="hash:3:torment", dimension=3,
        representation_class="COMPAT_EMBEDDING", generation=1,
        derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR", dtype="float32",
    )


def _prepared(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "formal-post-write.db")
    metadata = create_schema(qualified.connection)
    connection = qualified.connection
    memory_identity, semantic_scope, memory_alias = (generate_native_id() for _ in range(3))
    motif_identity, membership_identity, motif_alias, idempotency = (generate_native_id() for _ in range(4))
    for value, key in ((memory_identity, "memory"), (motif_identity, "motif"), (membership_identity, "membership")):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), key))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(semantic_scope), "formal-private"))
    for value, key in ((memory_alias, "memory-alias"), (motif_alias, "motif-alias")):
        connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), key))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "formal-idempotency"))
    runtime = NativeMemoryRuntimeScope(
        workspace_id="d1core20260831", scope_kind="PRIVATE_AGENT", agent_id="d1coreagent",
        legacy_source_namespace_id=memory_alias, identity_namespace_id=memory_identity,
        semantic_scope_id=semantic_scope,
    )
    scope = NativeFabricRoutingScope(
        runtime_scope=runtime, motif_alias_namespace_id=motif_alias,
        motif_identity_namespace_id=motif_identity, membership_identity_namespace_id=membership_identity,
        idempotency_namespace_id=idempotency,
    )
    lane = _lane()
    binding = prepare_native_memory_runtime_binding(
        connection=connection, core_database_path=qualified.database_path,
        expected_core_id=native_id_from_bytes(metadata.core_id), scope_bindings=(runtime,), representation_lane=lane,
    )
    capability = prepare_native_fabric_routing_capability(
        binding=binding, connection=connection, routing_scopes=(scope,), expected_core_id=native_id_from_bytes(metadata.core_id),
    )
    configuration = build_formal_native_post_write_configuration(
        routing_scope=scope, lane=lane, mutable_arm_root=tmp_path / "formal-arm",
    )
    return qualified, capability, scope, lane, configuration


def _request(key: str, step: int, *, summary: str, vector=(2.0, 0.6, 0.0)) -> NativeFabricRouteRequest:
    return NativeFabricRouteRequest(
        workspace_id="d1core20260831", scope="private", agent_id="d1coreagent", domain_id="research",
        native_operation_key=key, embedder_lane=_lane(), summary=summary,
        memory_type="episode", memory_class="core", strength=0.9, confidence=0.9,
        half_life_days=30.0, logical_step=step, created_ts=step, last_active_ts=step,
        last_reinforced_ts=step, incoming_embedding=np.asarray(vector, dtype=np.float32),
        provenance=ProvenanceV1.for_user_ingest(step=step), governance=MemoryGovernanceFlags(),
        flexible_payload={},
    )


def _context(result, request: NativeFabricRouteRequest, *, outcome: PostWriteStorageOutcome | None = None) -> FabricPostWriteContext:
    return FabricPostWriteContext.make(
        workspace_id=request.workspace_id, agent_id=request.agent_id, scope=request.scope,
        chosen_domain=request.domain_id, step=request.logical_step,
        storage_outcome=outcome or (PostWriteStorageOutcome.REINFORCED_EXISTING if result.reinforced else PostWriteStorageOutcome.CREATED_NEW),
        stored=result.stored, eid=result.eid, created_motif=None, motif_ids=result.motifs,
        half_life_days=request.half_life_days, summary=request.summary,
        embedding=np.asarray(request.incoming_embedding, dtype=np.float32), memory_class=request.memory_class,
        memory_type=request.memory_type, strength=request.strength, confidence=request.confidence,
        promotion_score=0.9, stability_delta=0.0, tri_mod={}, debug={}, srg_state=None,
        phase_durations={}, state_symbol=None, affect_tag=None, affect_conf=None,
        skip_packet_emission=False,
    )


def test_frozen_formal_posture_is_complete_and_disables_excluded_features(tmp_path: Path) -> None:
    qualified, _capability, _scope, _lane_value, configuration = _prepared(tmp_path)
    try:
        validate_formal_post_write_external_dependencies(configuration)
        owner = configuration.external.owner
        assert configuration.external.workspace.domain_policies["research"]["auto_merge_motifs"] is False
        assert configuration.external.identity.seed["coupling_mode"] == "read_only"
        assert all(getattr(owner, name) is False for name in (
            "_character_enable", "_compress_enable", "_checkpoint_enable", "_srg_enable",
            "_hivemind_enable", "_hivemind_telemetry_enable",
        ))
        assert configuration.motif_suggestion_maintenance_required is False
        assert configuration.bridge_suggestions_required is False
        assert configuration.deep_memory_required is False
    finally:
        qualified.close()


def test_synthetic_created_reinforced_and_no_write_cross_live_formal_post_write(tmp_path: Path) -> None:
    qualified, capability, _scope, _lane_value, configuration = _prepared(tmp_path)
    try:
        adapter = prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)
        router = NativeFabricMemoryRouter(capability)
        created_request = _request("D1:TEST:CREATED", 1, summary="synthetic formal claim is stable")
        created = router.route(created_request).result
        assert created is not None and created.reinforced is False
        assert adapter.run(
            _context(created, created_request),
            route_witness=NativePostWriteRouteWitness(created, created_request.native_operation_key),
        ).proposal_id is None

        reinforced_request = _request("D1:TEST:REINFORCED", 2, summary="synthetic formal claim is stable")
        reinforced = router.route(reinforced_request).result
        assert reinforced is not None and reinforced.reinforced is True
        assert adapter.run(
            _context(reinforced, reinforced_request),
            route_witness=NativePostWriteRouteWitness(reinforced, reinforced_request.native_operation_key),
        ).proposal_id is None

        no_write = FabricPostWriteContext.make(
            workspace_id="d1core20260831", agent_id="d1coreagent", scope="private", chosen_domain="research",
            step=3, storage_outcome=PostWriteStorageOutcome.NO_WRITE, stored=False, eid=None,
            created_motif=None, motif_ids=(), half_life_days=None, summary="synthetic no write",
            embedding=np.asarray((2.0, 0.6, 0.0), dtype=np.float32), memory_class="core",
            memory_type="episode", strength=0.0, confidence=0.0, promotion_score=0.0,
            stability_delta=0.0, tri_mod={}, debug={}, srg_state=None, phase_durations={}, state_symbol=None,
            affect_tag=None, affect_conf=None, skip_packet_emission=True,
        )
        assert adapter.run(no_write).proposal_id is None
        assert configuration.external.workspace.proposals["research"].records == []
    finally:
        qualified.close()


def test_exact_m5_no_write_facts_cross_live_adapter_without_a_route_or_durable_delta(tmp_path: Path) -> None:
    """Exercise the repaired input contract on synthetic native state only."""
    qualified, capability, _scope, _lane_value, configuration = _prepared(tmp_path)
    try:
        m5 = next(event for arm in CoreFrozenFixture.load().arms if arm.arm_id == "M5_NO_WRITE" for event in arm.events)
        facts = CoreNoWritePostWriteFacts.from_mapping(m5.native_request())

        class NoRouteRouter:
            calls = 0

            def route(self, _request):
                self.calls += 1
                raise AssertionError("NO_WRITE must not invoke native routing")

        router = NoRouteRouter()
        adapter = prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)
        before = NativeCoreStorageSnapshot.capture(qualified.database_path)
        outcome = NativeReplayHarness(
            router=router, post_write=adapter,
            native_storage_snapshot=lambda: NativeCoreStorageSnapshot.capture(qualified.database_path),
            placeholder_posture=InitialPostWritePlaceholderPosture(False, "read_only"),
        ).replay_no_write_context(facts.to_post_write_context())
        after = NativeCoreStorageSnapshot.capture(qualified.database_path)
        assert outcome.route_attempt is None and outcome.operation_key is None
        assert router.calls == 0 and before == after
        assert configuration.external.workspace.proposals["research"].records == []
    finally:
        qualified.close()


def test_conflict_and_derived_side_store_surfaces_are_arm_local(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "1.1")
    qualified, capability, scope, _lane_value, configuration = _prepared(tmp_path)
    try:
        adapter = prepare_native_fabric_post_write_adapter(capability=capability, configuration=configuration)
        router = NativeFabricMemoryRouter(capability)
        first_request = _request("D1:TEST:CONFLICT:ZERO", 1, summary="an unrelated synthetic baseline")
        first = router.route(first_request).result
        assert first is not None
        adapter.run(_context(first, first_request), route_witness=NativePostWriteRouteWitness(first, first_request.native_operation_key))
        second_request = _request("D1:TEST:CONFLICT:ONE", 2, summary="the synthetic claim is stable")
        second = router.route(second_request).result
        assert second is not None and second.reinforced is False
        adapter.run(_context(second, second_request), route_witness=NativePostWriteRouteWitness(second, second_request.native_operation_key))
        third_request = _request("D1:TEST:CONFLICT:TWO", 3, summary="the synthetic claim is not stable")
        third = router.route(third_request).result
        assert third is not None and third.reinforced is False
        candidates = NativePostWriteMemoryAccess(
            qualified.connection,
            legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
            expected_dimension=3,
        ).search_by_embedding(third_request.incoming_embedding, top_k=3, user_id="d1coreagent")
        assert len(candidates.hits) == 3
        assert configuration.external.detect_canon_conflict(
            third_request.summary, second_request.summary, 1.0,
        )[0] is True
        adapter.run(_context(third, third_request), route_witness=NativePostWriteRouteWitness(third, third_request.native_operation_key))
        conflicts = configuration.external.workspace.conflicts["research"]
        assert isinstance(conflicts, FormalConflictSurface) and len(conflicts.records) == 1
        assert (tmp_path / "formal-arm" / "formal_post_write" / "conflicts.jsonl").is_file()

        side_store = configuration.derived_runtime_template.side_store
        side_store.save_anchor_state(workspace_id="d1core20260831", agent_id="d1coreagent", state={"motifs": {"m": {"count": 1}}})
        assert side_store.load_anchor_state(workspace_id="d1core20260831", agent_id="d1coreagent")["motifs"]["m"]["count"] == 1
        assert (tmp_path / "formal-arm" / "formal_post_write" / "anchor_state.json").is_file()
    finally:
        qualified.close()


def test_proposal_surface_is_structurally_executable_but_frozen_posture_is_ineligible(tmp_path: Path) -> None:
    qualified, _capability, _scope, _lane_value, configuration = _prepared(tmp_path)
    try:
        proposal = configuration.external.workspace.proposals["research"]
        assert isinstance(proposal, FormalProposalSurface)
        result = proposal.submit(summary="synthetic proposal", embedding=np.asarray((1.0, 0.0, 0.0), dtype=np.float32))
        assert result.proposal_id == "formal-proposal-1"
        assert configuration.external.identity.seed["coupling_mode"] == "read_only"
    finally:
        qualified.close()


def test_exact_001_inert_workspace_is_refused_before_route_or_post_write_contact(tmp_path: Path) -> None:
    qualified, _capability, _scope, _lane_value, configuration = _prepared(tmp_path)
    try:
        inert = replace(configuration, external=replace(configuration.external, workspace=SimpleNamespace()))
        with pytest.raises(FormalPostWriteDependencyError, match="FORMAL_POST_WRITE_EXTERNAL_DEPENDENCIES_INVALID"):
            validate_formal_post_write_external_dependencies(inert)
    finally:
        qualified.close()


@pytest.mark.parametrize("attribute", (
    "_log", "_srg_enable", "_hivemind_enable", "_hivemind_telemetry_enable",
    "_character_enable", "_character_drift_every", "_compress_enable", "_compress_min_step",
    "_checkpoint_enable", "_checkpoint_interval", "character_store", "ident_store",
    "_get_collective_field", "_get_proposal_bridge", "_emit_hivemind_packet_telemetry",
))
def test_validator_refuses_each_required_live_owner_field_before_contact(tmp_path: Path, attribute: str) -> None:
    qualified, _capability, _scope, _lane_value, configuration = _prepared(tmp_path)
    try:
        setattr(configuration.external.owner, attribute, None)
        with pytest.raises(FormalPostWriteDependencyError, match="FORMAL_POST_WRITE_EXTERNAL_DEPENDENCIES_INVALID"):
            validate_formal_post_write_external_dependencies(configuration)
    finally:
        qualified.close()
