"""Disposable production-shaped owner routing without a selector mutation."""
from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
from uuid import uuid4

import pytest
from torment_service.character import CharacterSeed, CharacterState, CharacterStore
from torment_service.substrate.character_baseline_disposition import (
    CharacterBaselineBinding, CharacterBaselineRequest, QualifiedTargetGeometry,
)
from torment_service.substrate.deployment_types import (
    FROZEN_ROOT_GEOMETRY_DISPOSITIONS, RootDispositionExecutionReceipt, RootDispositionOwnerResult,
)
from torment_service.substrate.migration.root_scope import RootScopeKey, RootScopeKind
from torment_service.substrate.production_root_disposition import (
    ProductionRootDispositionAdapter, ReceiptOnlyDispositionEvidence,
    SyntheticOnlyDispositionEvidence, TrajectoryScopeHandoffInstruction,
    ProductionRootDispositionRefused, verify_production_root_disposition_receipt,
)
from torment_service.substrate.root_blocker5_binding import RootGeometryDispositionPlan, RootGeometryDispositionPlanEntry
from torment_service.substrate.trajectory_writer_handoff import TrajectoryHandoffBinding, TrajectoryScopeIdentity


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_production_adapter_routes_real_owners_and_only_classifies_synthetic_records(tmp_path: Path):
    core = uuid4()
    envelope = _digest("envelope")
    p6_receipt = str(uuid4())
    entries = tuple(
        RootGeometryDispositionPlanEntry(owner, disposition, _digest(owner))
        for owner, disposition in FROZEN_ROOT_GEOMETRY_DISPOSITIONS
    )
    plan = RootGeometryDispositionPlan(entries)
    store = CharacterStore(str(tmp_path))
    store.save_seed("ws", CharacterSeed(
        seed_id="seed", character_name="A", seed_text="a sufficient seed text", seed_motif_id="motif", seed_eids=[1],
    ))
    store.save_state("ws", CharacterState(
        workspace_id="ws", agent_id="agent", seed_id="seed", distance_to_seed=0.1,
        drift_direction="away_seed", drift_history=[(1, 0.1)], core_count=2,
    ))
    character_request = CharacterBaselineRequest(
        workspace_id="ws", agent_id="agent", seed_id="seed", operation_key="char:one",
        binding=CharacterBaselineBinding(
            corrected_core_id=core, p6_receipt_id=p6_receipt,
            root_admission_envelope_digest=envelope, plan_digest=plan.digest,
        ),
        target_geometry=QualifiedTargetGeometry(
            target_representation_identity="native:lane:384",
            ordered_native_memory_digest=_digest("memory"), native_seed_geometry_digest=_digest("geometry"),
            expected_dimension=384, distance_to_seed=0.75,
        ),
    )
    artifact = tmp_path / "workspaces" / "ws" / "agents" / "agent" / "private"
    artifact.mkdir(parents=True)
    scope = TrajectoryScopeIdentity(
        data_root_identity="disposable:root",
        scope_key=RootScopeKey("ws", RootScopeKind.PRIVATE, agent_id="agent"),
        legacy_source_namespace_id=uuid4(), artifact_root=str(artifact),
    )
    trajectory_binding = TrajectoryHandoffBinding(
        corrected_core_id=core, p6_receipt_id=p6_receipt,
        root_admission_envelope_digest=envelope, plan_digest=plan.digest,
    )
    receipt_only = [
        ReceiptOnlyDispositionEvidence(owner, envelope, plan.digest, _digest(owner), _digest("receipt:" + owner))
        for owner, _ in FROZEN_ROOT_GEOMETRY_DISPOSITIONS
        if owner in {
            "bridge_registry", "character_drift_history", "character_seed", "conflict_role_affect_identity",
            "deep_archive_vector_state", "hivemind_historical_geometry_scores", "proposal_registry",
        }
    ]
    synthetic_only = [
        SyntheticOnlyDispositionEvidence(owner, envelope, plan.digest, _digest(owner), _digest("classification:" + owner))
        for owner, _ in FROZEN_ROOT_GEOMETRY_DISPOSITIONS
        if owner in {"checkpoint_kernel_calibration", "srg_payload_markers"}
    ]
    adapter = ProductionRootDispositionAdapter(
        data_root=tmp_path, p6_receipt_id=p6_receipt, plan_digest=plan.digest,
        character_requests=(character_request,), trajectory_binding=trajectory_binding,
        trajectory_instructions=(TrajectoryScopeHandoffInstruction(
            scope=scope, legacy_writer_identity="LEGACY_MEMORY_GRAPH", operation_key="trajectory:one",
            quiescing_evidence_digest=_digest("quiescing"), quiescence_evidence_digest=_digest("quiesced"),
            native_admission_evidence_digest=_digest("native-admitted"),
        ),),
        receipt_only_evidence=receipt_only, synthetic_only_evidence=synthetic_only,
    )
    transition = "ROOT_GEOMETRY_EPOCH:" + envelope
    results = tuple(
        RootDispositionOwnerResult(
            owner_identity=entry.owner_identity, source_observation_digest=entry.source_observation_digest,
            disposition=entry.disposition,
            outcome=adapter.execute(
                entry=entry, root_admission_envelope_digest=envelope,
                geometry_transition_identity=transition,
            ),
            geometry_transition_identity=transition,
        )
        for entry in plan.entries
    )
    receipt = RootDispositionExecutionReceipt(
        root_admission_envelope_digest=envelope, native_staging_core_id=core,
        geometry_disposition_table_digest=plan.digest, geometry_transition_identity=transition,
        owner_results=results,
    )
    verify_production_root_disposition_receipt(data_root=tmp_path, receipt=receipt)
    state = store.load_state("ws", "agent")
    assert state is not None and state.distance_to_seed == 0.75 and state.drift_direction == "stable"
    assert next(item for item in results if item.owner_identity == "checkpoint_kernel_calibration").outcome.startswith(
        "PRODUCTION_SYNTHETIC_ONLY:"
    )
    assert next(item for item in results if item.owner_identity == "world_trajectory").outcome.startswith(
        "PRODUCTION_TRAJECTORY_HANDOFF:"
    )

    def altered(owner: str, outcome: str) -> RootDispositionExecutionReceipt:
        return replace(receipt, owner_results=tuple(
            replace(item, outcome=outcome) if item.owner_identity == owner else item
            for item in receipt.owner_results
        ))

    with pytest.raises(ProductionRootDispositionRefused):
        verify_production_root_disposition_receipt(
            data_root=tmp_path, receipt=altered("character_active_baseline", "PRODUCTION_CHARACTER_BASELINE:" + _digest("missing")),
        )
    with pytest.raises(ProductionRootDispositionRefused):
        verify_production_root_disposition_receipt(
            data_root=tmp_path, receipt=altered("bridge_registry", "PRODUCTION_RECEIPT_ONLY:not-a-digest"),
        )
    with pytest.raises(ProductionRootDispositionRefused):
        verify_production_root_disposition_receipt(
            data_root=tmp_path, receipt=replace(receipt, native_staging_core_id=uuid4()),
        )

    # An extra nonterminal scope for the exact P6 binding makes the prior
    # aggregate incomplete, so P7 cannot rely on a stale aggregate digest.
    extra_artifact = tmp_path / "workspaces" / "ws" / "agents" / "other" / "private"
    extra_artifact.mkdir(parents=True)
    extra_scope = TrajectoryScopeIdentity(
        data_root_identity="disposable:root",
        scope_key=RootScopeKey("ws", RootScopeKind.PRIVATE, agent_id="other"),
        legacy_source_namespace_id=uuid4(), artifact_root=str(extra_artifact),
    )
    from torment_service.substrate.trajectory_writer_handoff import TrajectoryWriterHandoffCoordinator

    TrajectoryWriterHandoffCoordinator.open_existing(data_root=tmp_path).initialize_legacy_scope(
        scope=extra_scope, binding=trajectory_binding, legacy_writer_identity="LEGACY_MEMORY_GRAPH",
        operation_key="partial:extra",
    )
    with pytest.raises(ProductionRootDispositionRefused):
        verify_production_root_disposition_receipt(data_root=tmp_path, receipt=receipt)
