"""B5 whole-workspace readiness is observational over prepared B2--B4 state."""
from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from torment_service.substrate.fabric_native_routing import NativeFabricRoutingScope
from torment_service.substrate.migration import (
    NativeMigrationRuntimeMotifProjectionService,
    NativeMigrationRuntimeMotifRegeometryProjectionService,
    NativeWorkspaceRuntimeReadiness,
    RetainedSideStoreEIDReference,
    WorkspaceNativeEmbedderIdentity,
    WorkspaceNativeFeaturePosture,
    WorkspaceNativeReadinessVerdict,
    WorkspaceNativeRuntimeReadinessRequest,
)
from torment_service.substrate.migration.workspace_runtime_readiness import _whole_core_fingerprint
from torment_service.substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntimeConfiguration
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
)
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope
from torment_service.substrate.ids import generate_native_id

from test_substrate_migration_runtime_motif_projection import _context as _b4a_context
from test_substrate_migration_runtime_motif_regeometry_projection import _context as _b4b_context


class _InertSideStore:
    def load_anchor_state(self, **_kwargs):
        return {}

    def save_anchor_state(self, **_kwargs):
        raise AssertionError("B5 must not invoke the retained side store")

    def load_affect_state(self, **_kwargs):
        return {}

    def save_affect_state(self, **_kwargs):
        raise AssertionError("B5 must not invoke the retained side store")


def _configuration(plan, lane):
    runtime = NativeMemoryRuntimeScope(
        workspace_id=plan.workspace_id,
        scope_kind=plan.scope_kind,
        legacy_source_namespace_id=plan.legacy_source_namespace_id,
        identity_namespace_id=plan.target_identity_namespace_id,
        semantic_scope_id=plan.target_semantic_scope_id,
        agent_id=plan.agent_id,
        domain_id=plan.domain_id,
    )
    routing = NativeFabricRoutingScope(
        runtime_scope=runtime,
        motif_alias_namespace_id=plan.motif_alias_namespace_id,
        motif_identity_namespace_id=plan.motif_identity_namespace_id,
        membership_identity_namespace_id=plan.membership_identity_namespace_id,
        idempotency_namespace_id=plan.idempotency_namespace_id,
    )
    template = NativeDerivedMemoryRuntimeConfiguration(
        workspace_id=plan.workspace_id,
        agent_id=plan.agent_id or "agent",
        domain_id=plan.motif_domain_id or plan.domain_id or "domain",
        legacy_source_namespace_id=plan.legacy_source_namespace_id,
        motif_alias_namespace_id=plan.motif_alias_namespace_id,
        memory_identity_namespace_id=plan.target_identity_namespace_id,
        semantic_scope_id=plan.target_semantic_scope_id,
        idempotency_namespace_id=plan.idempotency_namespace_id,
        parent_native_operation_key="B5-INERT-NEVER-EXECUTED",
        expected_dimension=lane.dimension,
        embed=lambda _text: (_ for _ in ()).throw(AssertionError("B5 must not call an embedder")),
        embedder_provider=lane.provider,
        embedder_model=lane.model,
        side_store=_InertSideStore(),
    )
    return NativePostWriteQualificationConfiguration(
        routing_scope=routing,
        profile=NativePostWriteQualificationProfile.core_staging(),
        external=NativePostWriteExternalDependencies(
            owner=SimpleNamespace(), workspace=SimpleNamespace(), identity=SimpleNamespace(), agent_key=plan.agent_id or "agent",
            detect_canon_conflict=lambda *_args: (_ for _ in ()).throw(AssertionError("B5 must not call post-write")),
            proposal_allowed=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("B5 must not call post-write")),
            hivemind_log=logging.getLogger("b5.inert"),
        ),
        derived_runtime_template=template,
        motif_suggestion_maintenance_required=False,
        persistent_trajectory_evidence_required=False,
        checkpoint_snapshots_required=False,
        bridge_suggestions_required=False,
        deep_memory_required=False,
    )


def _production_posture():
    return WorkspaceNativeFeaturePosture(
        character_enabled=True,
        character_gravity_effective=True,
        compression_enabled=True,
        deep_memory_required=True,
        motif_auto_merge_enabled=True,
        motif_suggestions_required=True,
        checkpoint_required=True,
        trajectory_persistence_required=True,
        bridge_suggestions_required=True,
    )


def _references(facts):
    source = facts["plan"].legacy_source_namespace_id
    return tuple(
        RetainedSideStoreEIDReference(name, source, 7)
        for name in (
            "conflicts", "anchors", "affect_history", "character_store",
            "hivemind_collective", "bridges", "trajectory_evidence", "deep_memory",
        )
    )


def _request(qualified, facts, *, lane=None, plans=None, references=None):
    lane = lane or facts["lane"]
    plans = plans or (facts["plan"],)
    references = _references(facts) if references is None else references
    return WorkspaceNativeRuntimeReadinessRequest(
        legacy_snapshot_id=facts["manifest"].legacy_snapshot_id,
        expected_native_core_id=facts["request"].expected_native_core_id,
        native_core_database_path=qualified.database_path,
        scope_plans=plans,
        target_lane=lane,
        expected_workspace_ids=tuple(sorted({plan.workspace_id for plan in plans})),
        staging_feature_posture=WorkspaceNativeFeaturePosture.a3d10_core_staging(),
        production_feature_posture=_production_posture(),
        qualification_embedder_identity=WorkspaceNativeEmbedderIdentity(lane.provider, lane.model, lane.dimension),
        post_write_configuration=_configuration(plans[0], lane),
        retained_side_store_eid_references=references,
        observed_file_roots=(facts.get("root") or facts["request"].snapshot_root,),
    )


def test_b5_reports_prepared_b3a_b3b_b4b_workspace_without_mutating_it(tmp_path: Path):
    qualified, facts = _b4b_context(tmp_path)
    try:
        NativeMigrationRuntimeMotifRegeometryProjectionService(facts["connection"]).project_target_lane_regeometry(facts["request"])
        calls_before = {eid: len(embedder.calls) for eid, embedder in facts["embedders"].items()}
        before = _whole_core_fingerprint(facts["connection"])
        report = NativeWorkspaceRuntimeReadiness(facts["connection"]).run(
            _request(
                qualified, facts,
                references=_references(facts),
            )
        )
        assert report.core_staging_runtime_ready is True
        assert report.controlled_native_staging_experiment_ready is True
        assert report.full_production_behavior_parity_ready is False
        assert report.production_cutover_ready is False
        assert report.verdict is WorkspaceNativeReadinessVerdict.CORE_READY_PRODUCTION_PARITY_INCOMPLETE
        assert report.b3a_ready_memory_count == 1
        assert report.b3b_ready_memory_count == 2
        assert report.b4a_ready_motif_count == 0
        assert report.b4b_ready_motif_count == 1
        assert report.memory_closure_ready and report.motif_closure_ready and report.member_reference_closure_ready
        assert report.runtime_binding_constructible
        assert report.routing_capability_constructible
        assert report.post_write_adapter_constructible
        assert report.migration_active_authorization_count == 0
        assert report.legacy_evidence_retained
        assert report.durable_effect_count == report.file_mutation_count == report.embedder_call_count == 0
        assert _whole_core_fingerprint(facts["connection"]) == before
        assert {eid: len(embedder.calls) for eid, embedder in facts["embedders"].items()} == calls_before
        assert set(report.conditional_feature_blockers) == {
            "CHARACTER_PARITY", "CHARACTER_GRAVITY_PARITY", "COMPRESSION_PARITY",
            "DEEP_MEMORY_RUNTIME_PARITY", "MOTIF_AUTO_MERGE_PARITY",
        }
        assert set(report.operational_parity_blockers) == {
            "MOTIF_SUGGESTION_MAINTENANCE_PARITY", "CHECKPOINT_PARITY",
            "PERSISTENT_TRAJECTORY_EVIDENCE_PARITY", "BRIDGE_SUGGESTION_PARITY",
        }
    finally:
        qualified.close()


def test_b5_reports_b4a_lineage_through_the_same_read_only_contract(tmp_path: Path):
    qualified, facts = _b4a_context(tmp_path)
    try:
        NativeMigrationRuntimeMotifProjectionService(facts["connection"]).project_lane_preserving_legacy_motif(facts["request"])
        report = NativeWorkspaceRuntimeReadiness(facts["connection"]).run(_request(qualified, facts))
        assert report.core_staging_runtime_ready
        assert report.b3a_ready_memory_count == 1
        assert report.b4a_ready_motif_count == 1
        assert report.b4b_ready_motif_count == 0
        assert report.motif_items[0].target_motif_object_id is not None
    finally:
        qualified.close()


def test_b5_preparation_gap_and_side_store_ambiguity_are_exact_blockers(tmp_path: Path):
    qualified, facts = _b4b_context(tmp_path, bootstrap_all=False)
    try:
        report = NativeWorkspaceRuntimeReadiness(facts["connection"]).run(
            _request(qualified, facts, references=(RetainedSideStoreEIDReference("conflicts", None, 7),))
        )
        assert report.core_staging_runtime_ready is False
        assert report.memory_closure_ready is False
        assert report.motif_closure_ready is False
        assert report.migration_active_authorization_count == 0
        reasons = {reason for _kind, reason in report.blockers}
        assert "WHOLE_WORKSPACE_MEMORY_CLOSURE_INCOMPLETE" in reasons
        assert "WHOLE_WORKSPACE_MOTIF_CLOSURE_INCOMPLETE" in reasons
        assert "SIDE_STORE_EID_UNRESOLVED:conflicts" in reasons
        assert "SIDE_STORE_EID_OBSERVATION_REQUIRED:anchors" in reasons
        assert report.durable_effect_count == report.file_mutation_count == report.embedder_call_count == 0
    finally:
        qualified.close()


def test_b5_reports_are_observational_and_stale_after_a_legitimate_migration_change(tmp_path: Path):
    qualified, facts = _b4b_context(tmp_path)
    try:
        request = _request(qualified, facts)
        before_projection = NativeWorkspaceRuntimeReadiness(facts["connection"]).run(request)
        assert before_projection.core_staging_runtime_ready is False
        NativeMigrationRuntimeMotifRegeometryProjectionService(facts["connection"]).project_target_lane_regeometry(facts["request"])
        after_projection = NativeWorkspaceRuntimeReadiness(facts["connection"]).run(request)
        assert before_projection.observed_core_fingerprint != after_projection.observed_core_fingerprint
        assert before_projection.core_staging_runtime_ready is False
        assert after_projection.core_staging_runtime_ready is True
        assert not hasattr(before_projection, "approval")
    finally:
        qualified.close()


def test_b5_fails_closed_for_wrong_lane_scope_and_staging_deployment_gates(tmp_path: Path):
    qualified, facts = _b4b_context(tmp_path)
    try:
        NativeMigrationRuntimeMotifRegeometryProjectionService(facts["connection"]).project_target_lane_regeometry(facts["request"])
        wrong_lane = replace(facts["lane"], model="wrong-model")
        lane_report = NativeWorkspaceRuntimeReadiness(facts["connection"]).run(
            _request(qualified, facts, lane=wrong_lane)
        )
        assert not lane_report.core_staging_runtime_ready
        assert not lane_report.memory_closure_ready

        missing_scope = replace(facts["plan"], target_semantic_scope_id=generate_native_id())
        scope_report = NativeWorkspaceRuntimeReadiness(facts["connection"]).run(
            _request(qualified, facts, plans=(missing_scope,))
        )
        assert not scope_report.workspace_scope_ready or not scope_report.runtime_binding_constructible

        facts["connection"].execute("UPDATE core_metadata SET core_role='EVIDENCE_ONLY'")
        role_report = NativeWorkspaceRuntimeReadiness(facts["connection"]).run(_request(qualified, facts))
        assert not role_report.core_deployment_ready
        assert not role_report.runtime_binding_constructible
    finally:
        qualified.close()


@pytest.mark.parametrize(
    ("posture", "expected"),
    (
        (WorkspaceNativeFeaturePosture(True, False, False, False, False, False, False, False, False), "CHARACTER_PARITY"),
        (WorkspaceNativeFeaturePosture(False, False, True, False, False, False, False, False, False), "COMPRESSION_PARITY"),
        (WorkspaceNativeFeaturePosture(False, False, False, False, True, False, False, False, False), "MOTIF_AUTO_MERGE_PARITY"),
        (WorkspaceNativeFeaturePosture(False, False, False, False, False, True, False, False, False), "MOTIF_SUGGESTION_MAINTENANCE_PARITY"),
    ),
)
def test_b5_feature_posture_is_explicit_and_blocks_only_requested_parity(tmp_path: Path, posture, expected):
    qualified, facts = _b4b_context(tmp_path)
    try:
        NativeMigrationRuntimeMotifRegeometryProjectionService(facts["connection"]).project_target_lane_regeometry(facts["request"])
        request = replace(_request(qualified, facts), production_feature_posture=posture)
        report = NativeWorkspaceRuntimeReadiness(facts["connection"]).run(request)
        assert report.core_staging_runtime_ready
        assert report.full_production_behavior_parity_ready is False
        assert expected in set(report.conditional_feature_blockers) | set(report.operational_parity_blockers)
        assert report.production_cutover_ready is False
    finally:
        qualified.close()
