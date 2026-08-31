"""One bounded B3A/B4A-only N0 construction from the frozen real L0 root."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.fabric_native_routing import NativeFabricRoutingScope
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import (
    MigrationRehearsalConfig,
    MigrationRuntimeScopePlan,
    WorkspaceNativeEmbedderIdentity,
    WorkspaceNativeFeaturePosture,
    WorkspaceNativeRuntimeReadinessRequest,
)
from torment_service.substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntimeConfiguration
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
)
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
from torment_service.substrate.schema import create_schema

from .manifest import fingerprint_legacy_baseline
from .n0 import N0BaselineBuilder, N0BuildPlan, materialize_l0_snapshot
from .protocol import D1ProtocolError
from .side_store_observation import observe_frozen_d1_core_retained_side_stores


class _InertSideStore:
    def load_anchor_state(self, **_kwargs):
        return {}

    def save_anchor_state(self, **_kwargs):
        raise AssertionError("B5 construction must not write retained side stores")

    def load_affect_state(self, **_kwargs):
        return {}

    def save_affect_state(self, **_kwargs):
        raise AssertionError("B5 construction must not write retained side stores")


def _configuration(plan: MigrationRuntimeScopePlan, lane: NativeRepresentationLane) -> NativePostWriteQualificationConfiguration:
    runtime = NativeMemoryRuntimeScope(
        workspace_id=plan.workspace_id, scope_kind=plan.scope_kind,
        legacy_source_namespace_id=plan.legacy_source_namespace_id,
        identity_namespace_id=plan.target_identity_namespace_id,
        semantic_scope_id=plan.target_semantic_scope_id, agent_id=plan.agent_id,
    )
    routing = NativeFabricRoutingScope(
        runtime_scope=runtime, motif_alias_namespace_id=plan.motif_alias_namespace_id,
        motif_identity_namespace_id=plan.motif_identity_namespace_id,
        membership_identity_namespace_id=plan.membership_identity_namespace_id,
        idempotency_namespace_id=plan.idempotency_namespace_id,
    )
    template = NativeDerivedMemoryRuntimeConfiguration(
        workspace_id=plan.workspace_id, agent_id=plan.agent_id or "d1-agent", domain_id=plan.motif_domain_id or "research",
        legacy_source_namespace_id=plan.legacy_source_namespace_id, motif_alias_namespace_id=plan.motif_alias_namespace_id,
        memory_identity_namespace_id=plan.target_identity_namespace_id, semantic_scope_id=plan.target_semantic_scope_id,
        idempotency_namespace_id=plan.idempotency_namespace_id, parent_native_operation_key="D1:N0:B5:INERT",
        expected_dimension=lane.dimension, embed=lambda _text: (_ for _ in ()).throw(AssertionError("B5 must not embed")),
        embedder_provider=lane.provider, embedder_model=lane.model, side_store=_InertSideStore(),
    )
    return NativePostWriteQualificationConfiguration(
        routing_scope=routing, profile=NativePostWriteQualificationProfile.core_staging(),
        external=NativePostWriteExternalDependencies(
            owner=SimpleNamespace(), workspace=SimpleNamespace(), identity=SimpleNamespace(seed={}), agent_key=plan.agent_id or "d1-agent",
            detect_canon_conflict=lambda *_args: (_ for _ in ()).throw(AssertionError("B5 must not invoke post-write")),
            proposal_allowed=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("B5 must not invoke post-write")),
            hivemind_log=logging.getLogger("d1.n0.inert"),
        ),
        derived_runtime_template=template, motif_suggestion_maintenance_required=False,
        persistent_trajectory_evidence_required=False, checkpoint_snapshots_required=False,
        bridge_suggestions_required=False, deep_memory_required=False,
    )


def build_real_n0(
    *,
    l0_root: str | Path,
    staging_root: str | Path,
    workspace_id: str,
    agent_id: str,
    character_seed_required: bool = False,
) -> dict[str, Any]:
    """Materialize L0 and run only B2/B3A/B4A/B5 on one new STAGING core."""
    root = Path(staging_root).resolve()
    if root.exists():
        raise D1ProtocolError("real N0 staging destination must be new")
    baseline = fingerprint_legacy_baseline(
        root=l0_root,
        workspace_id=workspace_id,
        agent_id=agent_id,
        character_seed_required=character_seed_required,
    )
    root.mkdir(parents=True)
    snapshot = materialize_l0_snapshot(baseline=baseline, destination=root / "l0_snapshot")
    database = root / "n0_core.db"
    manifest = root / "l0_snapshot_manifest.json"
    source_namespace = generate_native_id()
    object_namespace = generate_native_id()
    relationship_namespace = generate_native_id()
    motif_alias_namespace = generate_native_id()
    unknown_scope = generate_native_id()
    target_scope = generate_native_id()
    idempotency = generate_native_id()
    lock = baseline.workspace_embedding_lock.value
    provider, model, dimension = lock.get("embed_provider"), lock.get("embed_model"), lock.get("embed_dim")
    if (
        not isinstance(provider, str) or not provider
        or not isinstance(model, str) or not model
        or not isinstance(dimension, int) or isinstance(dimension, bool) or dimension < 1
    ):
        raise D1ProtocolError("real N0 requires the captured workspace embedding lock")
    lane = NativeRepresentationLane(
        provider=provider, model=model, dimension=dimension, representation_class="COMPAT_EMBEDDING",
        generation=1, derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR", dtype="float32",
    )
    qualified = open_temporary_test_connection(database)
    try:
        connection = qualified.connection
        metadata = create_schema(connection)
        for namespace, key in ((object_namespace, "d1-n0-objects"), (relationship_namespace, "d1-n0-relationships")):
            connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(namespace), key))
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(motif_alias_namespace), "d1-n0-runtime-motif-aliases"),
        )
        for scope, key in ((unknown_scope, "d1-n0-legacy-unknown"), (target_scope, "d1-n0-private-research")):
            connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(scope), key))
        connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "d1-n0"))
        plan = MigrationRuntimeScopePlan(
            legacy_source_namespace_id=source_namespace, workspace_id=workspace_id, scope_kind="PRIVATE_AGENT", agent_id=agent_id,
            target_identity_namespace_id=object_namespace, target_semantic_scope_id=target_scope,
            motif_alias_namespace_id=motif_alias_namespace, motif_identity_namespace_id=object_namespace,
            membership_identity_namespace_id=relationship_namespace, idempotency_namespace_id=idempotency,
            motif_domain_id="research",
        )
        side_store_observation = observe_frozen_d1_core_retained_side_stores(
            root=l0_root,
            workspace_id=workspace_id,
            agent_id=agent_id,
            domain_id=plan.motif_domain_id or "research",
            legacy_source_namespace_id=source_namespace,
        )
        core_id = UUID(bytes=metadata.core_id)
        request = WorkspaceNativeRuntimeReadinessRequest(
            legacy_snapshot_id=generate_native_id(), expected_native_core_id=core_id, native_core_database_path=database,
            scope_plans=(plan,), target_lane=lane, expected_workspace_ids=(workspace_id,),
            staging_feature_posture=WorkspaceNativeFeaturePosture.a3d10_core_staging(),
            production_feature_posture=WorkspaceNativeFeaturePosture(True, True, True, True, True, True, True, True, True),
            qualification_embedder_identity=WorkspaceNativeEmbedderIdentity(lane.provider, lane.model, lane.dimension),
            post_write_configuration=_configuration(plan, lane),
            retained_side_store_eid_references=(),
            retained_side_store_eid_observations=side_store_observation.observations,
            observed_file_roots=(Path(l0_root).resolve(), snapshot),
        )
        result = N0BaselineBuilder(connection).build(N0BuildPlan(
            baseline=baseline, snapshot_root=snapshot, manifest_path=manifest,
            legacy_source_namespace_id=source_namespace, legacy_source_namespace_key="d1-real-l0-20260831",
            migration_config=MigrationRehearsalConfig(core_id, idempotency, object_namespace, relationship_namespace, unknown_scope),
            scope_plans=(plan,), target_lane=lane, readiness_request=request,
        ))
        report = {
            "schema": "memory-substrate-d1-real-n0-v1", "l0_fingerprint_sha256": baseline.digest,
            "native_formal_event_count": 0, "b3a_eids": result.b3a_eids, "b4a_motif_ids": result.b4a_motif_ids,
            "whole_workspace_memory_closure": result.readiness.memory_closure_ready,
            "whole_workspace_motif_closure": result.readiness.motif_closure_ready,
            "whole_workspace_member_reference_closure": result.readiness.member_reference_closure_ready,
            "whole_workspace_side_store_retention": result.readiness.side_store_retention_ready,
            "core_staging_runtime_ready": result.readiness.core_staging_runtime_ready,
            "controlled_native_staging_experiment_ready": result.readiness.controlled_native_staging_experiment_ready,
            "b4a_ready_motif_count": result.readiness.b4a_ready_motif_count,
            "b4b_ready_motif_count": result.readiness.b4b_ready_motif_count,
            "readiness_report_digest": result.readiness.report_digest,
            "core_side_store_observation_digest": side_store_observation.digest,
            "core_side_store_observation_evidence": side_store_observation.intent(),
            "side_store_readiness": [
                {
                    "side_store": item.side_store,
                    "observation_status": item.observation_status.value,
                    "reference_count": item.reference_count,
                    "compatible": item.compatible,
                }
                for item in result.readiness.side_stores
            ],
        }
        output = root / "n0_build_report.json"
        descriptor = os.open(str(output), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(json.dumps(report, sort_keys=True, indent=2).encode("utf-8") + b"\n")
        return report
    finally:
        qualified.close()


__all__ = ["build_real_n0"]
