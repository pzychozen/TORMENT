"""Disposable P6 -> production disposition -> canonical P7 continuation."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from torment_service.character import CharacterSeed, CharacterState, CharacterStore
from torment_service.kernel.seed_entities import SeedWorld
from torment_service.memory_graph import MemoryGraph
from torment_service.substrate.character_baseline_disposition import (
    CharacterBaselineBinding, CharacterBaselineRequest, QualifiedTargetGeometry,
)
from torment_service.substrate.deployment_types import DeploymentState
from torment_service.substrate.migration.root_scope import RootScopeKey, RootScopeKind
from torment_service.substrate.offline_cutover_controller import (
    OfflineCutoverController, OfflineCutoverStage,
)
from torment_service.substrate.production_root_disposition import (
    ProductionRootDispositionAdapter, ReceiptOnlyDispositionEvidence,
    SyntheticOnlyDispositionEvidence, TrajectoryScopeHandoffInstruction,
)
from torment_service.substrate.native_trajectory_evidence_runtime import NativeTrajectoryEvidenceRuntime
from torment_service.substrate.trajectory_writer_handoff import (
    TrajectoryHandoffBinding, TrajectoryHandoffRefused, TrajectoryScopeIdentity,
    TrajectoryWriterHandoffCoordinator,
)

from test_post_i4_full_root_disposable_rehearsal_r1 import _build_disposable_root


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _artifact_root(root: Path, scope: RootScopeKey) -> Path:
    if scope.scope_kind is RootScopeKind.PRIVATE:
        return root / "workspaces" / scope.workspace_id / "agents" / str(scope.agent_id) / "private"
    return root / "workspaces" / scope.workspace_id / "domains" / str(scope.domain_id) / "shared"


def test_disposable_real_owner_continuation_reaches_p7_without_real_root_contact(tmp_path: Path):
    request, _profile = _build_disposable_root(tmp_path, "production-disposition")
    controller = OfflineCutoverController()
    controller.prepare_root(request)
    pending = controller.enter_compat_root_external_pending(request)
    normalization = controller.normalize_root_under_external_fence(request)
    verified = controller.verify_root_completion(request, normalization)
    controller.enter_root_core_pending(request, normalization)
    active = controller.activate_root_core(request, normalization)
    assert controller.root_current_stage(request) is OfflineCutoverStage.CORE_ACTIVE_EXTERNAL_PENDING

    envelope = verified.envelope
    plan = envelope.geometry_disposition_plan
    p6_receipt_id = str(active.maintenance_id)
    core_id = envelope.native_staging_core_id
    store = CharacterStore(str(request.root))
    runtime_by_key = {
        (item.workspace_id, item.scope_kind, item.qualifier): item
        for item in request.runtime_scopes
    }
    character_requests = []
    instructions = []
    for workspace in request.description.workspace_plans:
        for materialized in workspace.materialized_scopes:
            scope = materialized.scope_key
            runtime = runtime_by_key[(
                scope.workspace_id,
                "PRIVATE_AGENT" if scope.scope_kind is RootScopeKind.PRIVATE else "SHARED_DOMAIN",
                scope.qualifier,
            )]
            artifact = _artifact_root(request.root, scope)
            assert artifact.is_dir()
            identity = TrajectoryScopeIdentity(
                data_root_identity=request.description.data_root_identity,
                scope_key=scope, legacy_source_namespace_id=runtime.legacy_source_namespace_id,
                artifact_root=str(artifact),
            )
            instructions.append(TrajectoryScopeHandoffInstruction(
                scope=identity, legacy_writer_identity="LEGACY_MEMORY_GRAPH",
                operation_key=f"production-handoff:{scope.workspace_id}:{scope.scope_kind.value}:{scope.qualifier}",
                quiescing_evidence_digest=_digest("quiescing:" + repr(scope.canonical_key)),
                quiescence_evidence_digest=_digest("quiesced:" + repr(scope.canonical_key)),
                native_admission_evidence_digest=_digest("native:" + repr(scope.canonical_key)),
            ))
            if scope.scope_kind is RootScopeKind.PRIVATE:
                seed_id = f"cutover-{scope.workspace_id}-{scope.agent_id}"
                store.save_seed(scope.workspace_id, CharacterSeed(
                    seed_id=seed_id, character_name="Disposable", seed_text="A disposable qualified character seed.",
                    seed_motif_id="native-seed", seed_eids=[7],
                ))
                store.save_state(scope.workspace_id, CharacterState(
                    workspace_id=scope.workspace_id, agent_id=str(scope.agent_id), seed_id=seed_id,
                    distance_to_seed=0.1, drift_direction="away_seed", drift_history=[(1, 0.1)],
                ))
                character_requests.append(CharacterBaselineRequest(
                    workspace_id=scope.workspace_id, agent_id=str(scope.agent_id), seed_id=seed_id,
                    operation_key=f"production-character:{scope.workspace_id}:{scope.agent_id}",
                    binding=CharacterBaselineBinding(
                        corrected_core_id=core_id, p6_receipt_id=p6_receipt_id,
                        root_admission_envelope_digest=envelope.digest, plan_digest=plan.digest,
                    ),
                    target_geometry=QualifiedTargetGeometry(
                        target_representation_identity="disposable-native-lane:384",
                        ordered_native_memory_digest=_digest("memory:" + repr(scope.canonical_key)),
                        native_seed_geometry_digest=_digest("seed:" + repr(scope.canonical_key)),
                        expected_dimension=384, distance_to_seed=0.8,
                    ),
                ))
    trajectory_binding = TrajectoryHandoffBinding(
        corrected_core_id=core_id, p6_receipt_id=p6_receipt_id,
        root_admission_envelope_digest=envelope.digest, plan_digest=plan.digest,
    )
    receipt_only = [
        ReceiptOnlyDispositionEvidence(entry.owner_identity, envelope.digest, plan.digest,
                                       entry.source_observation_digest, _digest("receipt:" + entry.owner_identity))
        for entry in plan.entries
        if entry.owner_identity in {
            "bridge_registry", "character_drift_history", "character_seed", "conflict_role_affect_identity",
            "deep_archive_vector_state", "hivemind_historical_geometry_scores", "proposal_registry",
        }
    ]
    synthetic_only = [
        SyntheticOnlyDispositionEvidence(entry.owner_identity, envelope.digest, plan.digest,
                                         entry.source_observation_digest, _digest("synthetic:" + entry.owner_identity))
        for entry in plan.entries
        if entry.owner_identity in {"checkpoint_kernel_calibration", "srg_payload_markers"}
    ]
    adapter = ProductionRootDispositionAdapter(
        data_root=request.root, p6_receipt_id=p6_receipt_id, plan_digest=plan.digest,
        character_requests=tuple(character_requests), trajectory_binding=trajectory_binding,
        trajectory_instructions=tuple(instructions), receipt_only_evidence=receipt_only,
        synthetic_only_evidence=synthetic_only,
    )
    receipt = controller.execute_root_disposition_plan(request, normalization, adapter=adapter)
    assert controller.execute_root_disposition_plan(request, normalization, adapter=adapter) == receipt
    # No adapter API activates a selector. It remains pending until this one
    # explicit P7 controller action rechecks production evidence.
    assert pending.selector_state is not None
    selector = controller.activate_root_external_selector(request, normalization)
    assert selector.deployment_state is DeploymentState.NATIVE_ACTIVE

    # A newly constructed native writer uses the admitted durable session;
    # this is a bounded post-P7 trajectory check, still entirely disposable.
    first = instructions[0]
    native = NativeTrajectoryEvidenceRuntime(root_dir=first.scope.artifact_root)
    entity = SeedWorld().spawn(born_step=0, channel=0, pos=[0.0, 0.0, 0.0], vel=[0.0, 0.0, 0.0])
    native.write_genesis(entity)
    native.write_step((entity,), step=1)
    coordinator = TrajectoryWriterHandoffCoordinator.open_existing(data_root=request.root)
    assert coordinator.record_for_scope(scope=first.scope)["native_session_identity"] is not None
    assert (Path(first.scope.artifact_root) / "trajectories" / "v2").is_dir()
    with pytest.raises(TrajectoryHandoffRefused):
        MemoryGraph(first.scope.artifact_root)
