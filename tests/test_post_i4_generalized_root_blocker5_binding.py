"""Synthetic/offline qualification for the Post-I4 generalized root bridge."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.deployment_core_maintenance import (
    inspect_contained_core_deployment,
    read_root_admission_envelope_record,
    record_root_admission_envelope,
    record_root_disposition_execution,
)
from torment_service.substrate.deployment_selector import (
    activate_selector_native,
    read_selector_state,
)
from torment_service.substrate.deployment_types import (
    AdmissionCompletionWitness,
    DeploymentState,
    QualifiedDeploymentProfile,
    completion_witness_from_payload,
)
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration.explicit_source_evidence import (
    EvidenceOwnerBoundary,
    EvidenceOwnerBoundaryKind,
    EvidenceSemanticRole,
    RootEvidenceManifest,
    SourceOwnerClass,
    capture_present_source_evidence,
)
from torment_service.substrate.migration.existing_workspace_multi_scope_admission import (
    WorkspaceNativeEmbedderIdentity,
)
from torment_service.substrate.migration.runtime_readiness import MigrationRuntimeScopePlan
from torment_service.substrate.migration.root_admission_description import (
    ExpectedRootCensus,
    GeometryDerivedExternalStateDisposition,
    RepresentationDispositionCount,
    RootFeaturePosture,
    RootNativeProductionAdmissionDescription,
    RootRepresentationDisposition,
    WorkspaceRootAdmissionPlan,
    WorkspaceTopologyCounts,
)
from torment_service.substrate.migration.root_normalization import (
    NativeRootWideNormalizationService,
    RootNormalizationRecoveryWitness,
    RootNormalizationRequest,
    RootNormalizationResult,
    RootWorkspaceNormalizationResult,
)
from torment_service.substrate.migration.root_scope import RootScopeKey
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.offline_cutover_controller import (
    OfflineCutoverController,
    OfflineCutoverRefused,
    OfflineCutoverStage,
    RootAdmissionMode,
    RootOfflineCutoverRequest,
)
from torment_service.substrate.root_blocker5_binding import (
    RootBlocker5BindingRefused,
    RootWriterFreezeWitness,
    discover_canonical_root_layout,
    root_admission_envelope_record_from_payload,
    root_runtime_scope_plan_digest,
)
from torment_service.substrate.root_profile import (
    ROOT_NATIVE_PROFILE_GENERATION_KIND,
    current_root_profile_generation,
    root_profile_generation_payload,
)
from torment_service.substrate.runtime_binding import NativeRepresentationLane
from torment_service.substrate.errors import DeploymentAuthorityError, DeploymentIdempotencyConflict
from torment_service.substrate.schema import create_schema
from torment_service.substrate.writer_freeze_evidence import (
    ListenerObservation,
    ListenerObservationResult,
    RootWriterClass,
    RootWriterFreezeRecheck,
    WriterObservationResult,
    WriterProcessObservation,
    capture_root_writer_freeze_evidence,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class _DeterministicEmbedder:
    def embed(self, text: str) -> list[float]:
        del text
        return [1.0] + [0.0] * 383


class _SyntheticDispositionAdapter:
    def __init__(self, *, fail_once_for: str | None = None) -> None:
        self.calls: list[tuple[str, str]] = []
        self.mutations: set[str] = set()
        self.fail_once_for = fail_once_for
        self.failed = False

    def execute(
        self,
        *,
        entry,
        root_admission_envelope_digest: str,
        geometry_transition_identity: str,
    ) -> str:
        self.calls.append((entry.owner_identity, root_admission_envelope_digest))
        assert geometry_transition_identity.startswith("ROOT_GEOMETRY_EPOCH:")
        if entry.owner_identity == self.fail_once_for and not self.failed:
            self.failed = True
            raise RuntimeError("synthetic partial-owner interruption")
        if entry.owner_identity in self.mutations:
            return "SYNTHETIC_IDEMPOTENT_NO_MUTATION"
        self.mutations.add(entry.owner_identity)
        return "SYNTHETIC_LAWFUL_NO_MUTATION"


def _root_fixture(tmp_path: Path):
    root = tmp_path / "synthetic-root"
    workspace = root / "workspaces" / "ws-one"
    workspace.mkdir(parents=True)
    (workspace / "workspace_meta.json").write_bytes(b"{}")
    core_path = root / "substrate" / "cores" / "root.db"
    core_path.parent.mkdir(parents=True)
    qualified = open_temporary_test_connection(core_path)
    try:
        connection = qualified.connection
        create_schema(connection)
        profile_identity_namespace_id = generate_native_id()
        idempotency_namespace_id = generate_native_id()
        profile_semantic_scope_id = generate_native_id()
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(profile_identity_namespace_id), "root-profile-identity"),
        )
        connection.execute(
            "INSERT INTO semantic_scopes VALUES (?,?,0)",
            (native_id_to_bytes(profile_semantic_scope_id), "root-profile-scope"),
        )
        connection.execute(
            "INSERT INTO idempotency_namespaces VALUES (?,?)",
            (native_id_to_bytes(idempotency_namespace_id), "root-profile-ops"),
        )
        NativeObjectService(connection).create_object(
            idempotency_namespace_id=idempotency_namespace_id,
            idempotency_key="root-profile-generation",
            state=ObjectState(
                profile_identity_namespace_id,
                profile_semantic_scope_id,
                ROOT_NATIVE_PROFILE_GENERATION_KIND,
                "EXISTS",
                "ACTIVE",
                True,
                "QUALIFIED",
                authority_category="EVIDENCE",
                payload=root_profile_generation_payload(1),
                payload_format="JSON",
            ),
        )
        profile_ref = current_root_profile_generation(connection)
    finally:
        qualified.close()

    owner = EvidenceOwnerBoundary("ws-one", EvidenceOwnerBoundaryKind.WORKSPACE)
    manifest = RootEvidenceManifest((capture_present_source_evidence(
        data_root=root,
        owner_class=SourceOwnerClass.WORKSPACE_IDENTITY_METADATA,
        owner_boundary=owner,
        canonical_locator="workspace_meta.json",
        semantic_role=EvidenceSemanticRole.WORKSPACE_META,
    ),))
    lane = NativeRepresentationLane(
        provider="st",
        model="BAAI/bge-small-en-v1.5",
        dimension=384,
        representation_class="COMPAT_EMBEDDING",
        generation=1,
        derivation_contract_version="compat-embedding-v1",
        encoding_id="RAW_VECTOR",
        dtype="float32",
    )
    counts = tuple(
        RepresentationDispositionCount(disposition, 0)
        for disposition in RootRepresentationDisposition
    )
    description = RootNativeProductionAdmissionDescription(
        data_root_identity="post-i4-synthetic-root",
        operator_identity="post-i4-qualification",
        workspace_plans=(WorkspaceRootAdmissionPlan("ws-one", no_memory_scope=True),),
        target_representation_lane=lane,
        expected_census=ExpectedRootCensus(
            workspace_count=1,
            materialized_private_scope_count=0,
            materialized_shared_scope_count=0,
            total_materialized_scope_count=0,
            representation_disposition_counts=counts,
            workspace_topology_counts=WorkspaceTopologyCounts(1, 0, 0, 1, 0, 0),
        ),
        explicit_source_manifest=manifest,
        external_owner_observations=(),
        feature_posture=RootFeaturePosture("synthetic-disabled", False, False),
    )
    profile = QualifiedDeploymentProfile(
        compression_enabled=False,
        deep_memory_enabled=False,
        representation_provider=lane.provider,
        representation_model=lane.model,
        representation_dimension=lane.dimension,
        admitted_scope_plan_digest=root_runtime_scope_plan_digest((), lane),
        external_owner_digest=description.external_owner_observation_digest,
    )
    normalization_request = RootNormalizationRequest(
        description=description,
        data_root=root,
        native_core_database_path=core_path,
        expected_native_core_id=profile_ref.core_id,
        scope_inputs=(),
        qualification_embedder_identity=WorkspaceNativeEmbedderIdentity(
            lane.provider, lane.model, lane.dimension,
        ),
        b3b_embedder=_DeterministicEmbedder(),
    )
    request = RootOfflineCutoverRequest(
        data_root=root,
        description=description,
        normalization_request=normalization_request,
        effective_profile=profile,
        root_profile=profile_ref,
        runtime_scopes=(),
        writer_freeze=RootWriterFreezeWitness(
            data_root_identity=description.data_root_identity,
            writer_freeze_operation_identity="synthetic-writer-freeze-v1",
            writer_evidence_digest=_digest("writers-drained"),
        ),
        operator_cutover_key="post-i4-root-binding",
        admission_mode=RootAdmissionMode.SYNTHETIC_V1_COMPAT,
    )
    normalization = RootNormalizationResult(
        recovery_witness=RootNormalizationRecoveryWitness(
            root_description_digest=description.identity_digest,
            expected_census_digest=_digest(description.expected_census.identity_payload().__repr__()),
            source_manifest_digest=manifest.digest,
            native_staging_core_id=profile_ref.core_id,
            target_lane=lane,
        ),
        expected_workspace_count=1,
        observed_workspace_closure=1,
        expected_materialized_scope_count=0,
        observed_materialized_scope_closure=0,
        workspace_results=(RootWorkspaceNormalizationResult("ws-one", 0, 0, True),),
        scope_results=(),
        generalized_readiness_result=None,
        source_manifest_recheck_passed=True,
        unresolved_activation_gates=(
            GeometryDerivedExternalStateDisposition.UNRESOLVED_PRE_ACTIVATION_GATE,
        ),
        root_normalization_complete=True,
        root_normalization_ready=True,
        real_root_activation_ready=False,
        partial_activation=False,
        reason_codes=(),
    )
    return request, normalization


def test_v1_decoder_remains_historical_and_v2_root_has_explicit_contract(tmp_path: Path) -> None:
    request, normalization = _root_fixture(tmp_path)
    controller = OfflineCutoverController()
    controller.prepare_root(request)
    controller.enter_compat_root_external_pending(request)
    verification = controller.verify_root_completion(request, normalization)
    assert verification.completion_verification is not None
    root_witness = verification.completion_verification.completion_witness
    decoded_root = completion_witness_from_payload(root_witness.payload())
    assert decoded_root == root_witness
    assert root_witness.payload()["contract"] == "TORMENT_ROOT_ADMISSION_COMPLETION_WITNESS"
    assert root_witness.payload()["version"] == 2
    unsupported_root = dict(root_witness.payload())
    unsupported_root["version"] = 3
    with pytest.raises(DeploymentAuthorityError):
        completion_witness_from_payload(unsupported_root)

    legacy = AdmissionCompletionWitness(
        admission_identity_digest=_digest("legacy-admission"),
        completed_descriptor_digest=_digest("legacy-descriptor"),
        completed_progress_digest=_digest("legacy-progress"),
        native_core_id=generate_native_id(),
        workspace_id="historical-workspace",
        whole_workspace_closure_digest=_digest("legacy-closure"),
        profile_digest=_digest("legacy-profile"),
    )
    assert completion_witness_from_payload(legacy.payload()) == legacy


def test_synthetic_root_bridge_requires_post_p6_receipt_then_recovers_idempotently(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, normalization = _root_fixture(tmp_path)
    controller = OfflineCutoverController()

    discovered = discover_canonical_root_layout(data_root=request.root)
    assert discovered.workspace_ids == ("ws-one",)
    assert discovered.materialized_scope_keys == ()
    prepared = controller.prepare_root(request)
    pending = controller.enter_compat_root_external_pending(request)
    assert prepared.stage is OfflineCutoverStage.PREPARED
    assert pending.stage is OfflineCutoverStage.EXTERNAL_PENDING
    monkeypatch.setattr(
        NativeRootWideNormalizationService,
        "normalize",
        lambda _self, _request, **_kwargs: normalization,
    )
    assert controller.normalize_root_under_external_fence(request) == normalization
    verified = controller.verify_root_completion(request, normalization)
    assert verified.completion_verification is not None
    controller.enter_root_core_pending(request, normalization)
    manifest_path = request.root / "workspaces" / "ws-one" / "workspace_meta.json"
    manifest_path.write_bytes(b"manifest-drift")
    with pytest.raises(OfflineCutoverRefused):
        controller.activate_root_core(request, normalization)
    manifest_path.write_bytes(b"{}")
    active = controller.activate_root_core(request, normalization)
    assert active.witness.deployment_state.value == "NATIVE_ACTIVE"
    assert controller.activate_root_core(request, normalization) == active
    assert controller.root_current_stage(request) is OfflineCutoverStage.CORE_ACTIVE_EXTERNAL_PENDING

    with pytest.raises(OfflineCutoverRefused, match="P7_RECEIPT_REQUIRED"):
        controller.activate_root_external_selector(request, normalization)

    adapter = _SyntheticDispositionAdapter(fail_once_for="proposal_registry")
    with pytest.raises(RuntimeError, match="partial-owner"):
        controller.execute_root_disposition_plan(request, normalization, adapter=adapter)
    with pytest.raises(OfflineCutoverRefused, match="P7_RECEIPT_REQUIRED"):
        controller.activate_root_external_selector(request, normalization)
    receipt = controller.execute_root_disposition_plan(
        request, normalization, adapter=adapter,
    )
    assert len(adapter.mutations) == 11
    assert controller.execute_root_disposition_plan(
        request, normalization, adapter=adapter,
    ) == receipt
    assert len(adapter.mutations) == 11

    conflicting_receipt = replace(
        receipt,
        geometry_transition_identity="ROOT_GEOMETRY_EPOCH:conflicting",
        owner_results=tuple(
            replace(item, geometry_transition_identity="ROOT_GEOMETRY_EPOCH:conflicting")
            for item in receipt.owner_results
        ),
    )
    with pytest.raises(DeploymentIdempotencyConflict):
        record_root_disposition_execution(
            data_root=request.root,
            core_relative_path=request.core_relative_path,
            completion_witness=verified.completion_verification.completion_witness,
            receipt=conflicting_receipt,
            operation_key="B5-A5:post-i4-root-binding:root-disposition-execution",
        )

    assert pending.selector_state is not None
    with pytest.raises(DeploymentAuthorityError, match="missing or mismatched"):
        activate_selector_native(
            data_root=request.root,
            core_relative_path=request.core_relative_path,
            core_result=active,
            expected_generation=pending.selector_state.generation,
            operation_key="post-i4-root-binding:mismatched-receipt",
            disposition_execution_receipt_digest=_digest("mismatched-receipt"),
        )

    selector = controller.activate_root_external_selector(request, normalization)
    assert selector.deployment_state.value == "NATIVE_ACTIVE"
    assert controller.activate_root_external_selector(request, normalization) == selector
    assert controller.root_current_stage(request) is OfflineCutoverStage.NATIVE_ACTIVE


def test_root_discovery_refuses_an_undeclared_canonical_workspace(tmp_path: Path) -> None:
    request, _normalization = _root_fixture(tmp_path)
    (request.root / "workspaces" / "undeclared").mkdir()

    with pytest.raises(OfflineCutoverRefused):
        OfflineCutoverController().prepare_root(request)


def test_root_runtime_scope_plan_digest_is_sorted_and_profile_bound(tmp_path: Path) -> None:
    request, _normalization = _root_fixture(tmp_path)
    lane = request.description.target_representation_lane
    private = MigrationRuntimeScopePlan(
        legacy_source_namespace_id=generate_native_id(),
        workspace_id="ws-one",
        scope_kind="PRIVATE_AGENT",
        target_identity_namespace_id=generate_native_id(),
        target_semantic_scope_id=generate_native_id(),
        motif_alias_namespace_id=generate_native_id(),
        motif_identity_namespace_id=generate_native_id(),
        membership_identity_namespace_id=generate_native_id(),
        idempotency_namespace_id=generate_native_id(),
        agent_id="agent-one",
        motif_domain_id="agent-one",
    )
    shared = MigrationRuntimeScopePlan(
        legacy_source_namespace_id=generate_native_id(),
        workspace_id="ws-one",
        scope_kind="SHARED_DOMAIN",
        target_identity_namespace_id=generate_native_id(),
        target_semantic_scope_id=generate_native_id(),
        motif_alias_namespace_id=generate_native_id(),
        motif_identity_namespace_id=generate_native_id(),
        membership_identity_namespace_id=generate_native_id(),
        idempotency_namespace_id=generate_native_id(),
        domain_id="domain-one",
        motif_domain_id="domain-one",
    )
    assert root_runtime_scope_plan_digest((private, shared), lane) == root_runtime_scope_plan_digest(
        (shared, private), lane,
    )

    invalid_profile = replace(
        request.effective_profile,
        admitted_scope_plan_digest=_digest("not-the-frozen-root-plan"),
    )
    invalid_request = replace(request, effective_profile=invalid_profile)
    with pytest.raises(OfflineCutoverRefused, match="ENVELOPE_REFUSED"):
        OfflineCutoverController().prepare_root(invalid_request)


def test_root_envelope_record_is_immutable_readable_without_legacy_layout(tmp_path: Path) -> None:
    request, _normalization = _root_fixture(tmp_path)
    controller = OfflineCutoverController()
    envelope = controller._root_envelope(request)

    recorded = record_root_admission_envelope(
        data_root=request.root,
        core_relative_path=request.core_relative_path,
        envelope=envelope,
        operation_key="root-v2-b1:record",
    )
    assert recorded.envelope_digest == envelope.digest
    assert record_root_admission_envelope(
        data_root=request.root,
        core_relative_path=request.core_relative_path,
        envelope=envelope,
        operation_key="root-v2-b1:record",
    ) == recorded

    legacy_layout = request.root / "workspaces"
    legacy_layout.rename(request.root / "legacy-layout-unavailable")
    loaded = read_root_admission_envelope_record(
        data_root=request.root,
        core_relative_path=request.core_relative_path,
        root_admission_envelope_digest=envelope.digest,
    )
    assert loaded == recorded
    assert loaded is not None
    assert loaded.envelope_digest == envelope.digest


def test_root_envelope_record_refuses_conflict_and_unknown_version(tmp_path: Path) -> None:
    request, _normalization = _root_fixture(tmp_path)
    controller = OfflineCutoverController()
    envelope = controller._root_envelope(request)
    record_root_admission_envelope(
        data_root=request.root,
        core_relative_path=request.core_relative_path,
        envelope=envelope,
        operation_key="root-v2-b1:conflict",
    )
    changed_request = replace(
        request,
        writer_freeze=replace(
            request.writer_freeze,
            writer_evidence_digest=_digest("different-writer-evidence"),
        ),
    )
    with pytest.raises(DeploymentIdempotencyConflict):
        record_root_admission_envelope(
            data_root=changed_request.root,
            core_relative_path=changed_request.core_relative_path,
            envelope=controller._root_envelope(changed_request),
            operation_key="root-v2-b1:conflict",
        )

    recorded_payload = record_root_admission_envelope(
        data_root=request.root,
        core_relative_path=request.core_relative_path,
        envelope=envelope,
        operation_key="root-v2-b1:version",
    ).payload()
    unsupported = dict(recorded_payload)
    unsupported["version"] = 2
    with pytest.raises(RootBlocker5BindingRefused, match="version is unsupported"):
        root_admission_envelope_record_from_payload(unsupported)
    noncanonical = dict(recorded_payload)
    noncanonical_envelope = dict(recorded_payload["root_admission_envelope_payload"])
    noncanonical_envelope["unexpected"] = "not-authority"
    noncanonical["root_admission_envelope_payload"] = noncanonical_envelope
    with pytest.raises(RootBlocker5BindingRefused, match="noncanonical"):
        root_admission_envelope_record_from_payload(noncanonical)


def test_p4_and_immediately_pre_p6_refuse_missing_or_mismatched_envelope_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, normalization = _root_fixture(tmp_path)
    controller = OfflineCutoverController()
    controller.prepare_root(request)
    controller.enter_compat_root_external_pending(request)

    import torment_service.substrate.offline_cutover_controller as controller_module

    monkeypatch.setattr(controller_module, "read_root_admission_envelope_record", lambda **_kwargs: None)
    with pytest.raises(OfflineCutoverRefused, match="COMPLETION_REFUSED"):
        controller.verify_root_completion(request, normalization)

    monkeypatch.undo()
    controller.verify_root_completion(request, normalization)
    controller.enter_root_core_pending(request, normalization)
    monkeypatch.setattr(controller_module, "read_root_admission_envelope_record", lambda **_kwargs: object())
    with pytest.raises(OfflineCutoverRefused, match="COMPLETION_REFUSED"):
        controller.activate_root_core(request, normalization)


def test_root_pre_active_abort_restores_legacy_without_disposition_or_native_residue(
    tmp_path: Path,
) -> None:
    request, normalization = _root_fixture(tmp_path)
    controller = OfflineCutoverController()
    controller.prepare_root(request)
    controller.enter_compat_root_external_pending(request)
    controller.verify_root_completion(request, normalization)
    controller.enter_root_core_pending(request, normalization)

    aborted = controller.safe_root_pending_abort(request)

    assert aborted.deployment_state.value == "LEGACY_ACTIVE"
    inspection = controller._inspection(request)
    assert inspection.deployment_state.value == "LEGACY_ACTIVE"
    assert inspection.core_role == "STAGING"
    assert inspection.ever_active is False
    assert controller.root_current_stage(request) is OfflineCutoverStage.PREPARED
    assert controller.safe_root_pending_abort(request).deployment_state.value == "LEGACY_ACTIVE"


def _root_writer_freeze_evidence(request: RootOfflineCutoverRequest):
    observations = tuple(
        WriterProcessObservation(
            writer_class=item,
            observation_mechanism="SYNTHETIC_OPERATOR_CENSUS_V1",
            result=WriterObservationResult.ABSENT,
        )
        for item in RootWriterClass
    )
    listener = ListenerObservation(
        listener_identity="127.0.0.1:8787",
        observation_mechanism="SYNTHETIC_LISTENER_CENSUS_V1",
        result=ListenerObservationResult.ABSENT,
    )
    timestamps = iter((2_000_000_000_000_000_000, 2_000_000_000_000_000_100, 2_000_000_000_000_000_200))
    captured = capture_root_writer_freeze_evidence(
        data_root=request.root,
        data_root_identity=request.description.data_root_identity,
        writer_freeze_operation_identity="synthetic-root-freeze-evidence",
        operator_identity="synthetic-root-operator",
        covered_writer_classes=observations,
        listener_observation=listener,
        external_owner_observation_digest=request.description.external_owner_observation_digest,
        expected_root_admission_description_contract="ROOT_ADMISSION_DESCRIPTION_V1",
        invalidation_rule_version="ROOT_WRITER_FREEZE_INVALIDATION_V1",
        minimum_delta_seconds=0,
        clock_ns=lambda: next(timestamps),
    )
    recheck = RootWriterFreezeRecheck(
        covered_writer_classes=observations,
        listener_observation=listener,
        job_observation=captured.payload.job_observation,
        external_owner_observation_digest=request.description.external_owner_observation_digest,
    )
    return captured, recheck


def test_f15_p2_refuses_tree_drift_against_frozen_writer_evidence(tmp_path: Path) -> None:
    request, _normalization = _root_fixture(tmp_path)
    captured, recheck = _root_writer_freeze_evidence(request)
    frozen_request = replace(
        request,
        writer_freeze=captured.witness,
        writer_freeze_evidence=captured.payload,
        writer_freeze_recheck=recheck,
    )
    controller = OfflineCutoverController()
    controller.prepare_root(frozen_request)
    (frozen_request.root / "workspaces" / "ws-one" / "workspace_meta.json").write_bytes(b"tree-drift")

    with pytest.raises(OfflineCutoverRefused, match="ENVELOPE_REFUSED"):
        controller.enter_compat_root_external_pending(frozen_request)


def test_frozen_writer_evidence_is_rechecked_at_p4_and_immediately_pre_p6(tmp_path: Path) -> None:
    request, normalization = _root_fixture(tmp_path)
    captured, recheck = _root_writer_freeze_evidence(request)
    frozen_request = replace(
        request,
        writer_freeze=captured.witness,
        writer_freeze_evidence=captured.payload,
        writer_freeze_recheck=recheck,
    )
    controller = OfflineCutoverController()
    controller.prepare_root(frozen_request)
    controller.enter_compat_root_external_pending(frozen_request)
    controller.verify_root_completion(frozen_request, normalization)
    controller.enter_root_core_pending(frozen_request, normalization)
    (frozen_request.root / "workspaces" / "ws-one" / "workspace_meta.json").write_bytes(b"tree-drift")

    with pytest.raises(OfflineCutoverRefused, match="ENVELOPE_REFUSED"):
        controller.activate_root_core(frozen_request, normalization)


def _real_request(request: RootOfflineCutoverRequest) -> RootOfflineCutoverRequest:
    captured, recheck = _root_writer_freeze_evidence(request)
    return replace(
        request,
        admission_mode=RootAdmissionMode.REAL_ROOT_V2,
        writer_freeze=captured.witness,
        writer_freeze_evidence=captured.payload,
        writer_freeze_recheck=recheck,
    )


def _assert_no_real_p2_durable_effect(request: RootOfflineCutoverRequest) -> None:
    inspection = inspect_contained_core_deployment(
        data_root=request.root,
        core_relative_path=request.core_relative_path,
    )
    assert inspection.core_role == "STAGING"
    assert inspection.deployment_state is DeploymentState.LEGACY_ACTIVE
    assert inspection.witness is None
    assert inspection.latest_maintenance_id is None
    assert not inspection.ever_active
    with pytest.raises(DeploymentAuthorityError):
        read_selector_state(data_root=request.root)


def test_real_root_p2_refuses_witness_only_before_all_durable_effects(tmp_path: Path) -> None:
    compat_request, _normalization = _root_fixture(tmp_path)
    real_request = replace(compat_request, admission_mode=RootAdmissionMode.REAL_ROOT_V2)
    controller = OfflineCutoverController()

    with pytest.raises(OfflineCutoverRefused, match="ENVELOPE_REFUSED"):
        controller.enter_root_external_pending(real_request)

    _assert_no_real_p2_durable_effect(real_request)
    with pytest.raises(OfflineCutoverRefused, match="REAL_P2_MODE_REQUIRED"):
        controller.enter_root_external_pending(compat_request)


def test_real_root_p2_refuses_payload_without_recheck_before_all_durable_effects(tmp_path: Path) -> None:
    compat_request, _normalization = _root_fixture(tmp_path)
    captured, _recheck = _root_writer_freeze_evidence(compat_request)
    real_request = replace(
        compat_request,
        admission_mode=RootAdmissionMode.REAL_ROOT_V2,
        writer_freeze=captured.witness,
        writer_freeze_evidence=captured.payload,
        writer_freeze_recheck=None,
    )

    with pytest.raises(OfflineCutoverRefused, match="ENVELOPE_REFUSED"):
        OfflineCutoverController().enter_root_external_pending(real_request)

    _assert_no_real_p2_durable_effect(real_request)


def test_real_root_p2_refuses_stale_recheck_before_all_durable_effects(tmp_path: Path) -> None:
    compat_request, _normalization = _root_fixture(tmp_path)
    real_request = _real_request(compat_request)
    assert real_request.writer_freeze_recheck is not None
    stale_request = replace(
        real_request,
        writer_freeze_recheck=replace(
            real_request.writer_freeze_recheck,
            external_owner_observation_digest=_digest("stale-owner-observation"),
        ),
    )

    with pytest.raises(OfflineCutoverRefused, match="ENVELOPE_(REFUSED|UNAVAILABLE)"):
        OfflineCutoverController().enter_root_external_pending(stale_request)

    _assert_no_real_p2_durable_effect(stale_request)


def test_real_root_p2_refuses_stale_profile_prerequisite_before_all_durable_effects(
    tmp_path: Path,
) -> None:
    compat_request, _normalization = _root_fixture(tmp_path)
    real_request = _real_request(compat_request)
    stale_request = replace(
        real_request,
        root_profile=replace(real_request.root_profile, profile_generation=2),
    )

    with pytest.raises(OfflineCutoverRefused, match="ENVELOPE_(REFUSED|UNAVAILABLE)"):
        OfflineCutoverController().enter_root_external_pending(stale_request)

    _assert_no_real_p2_durable_effect(stale_request)


def test_real_root_p2_records_strong_envelope_before_pending_and_refuses_downgrade(
    tmp_path: Path,
) -> None:
    compat_request, _normalization = _root_fixture(tmp_path)
    real_request = _real_request(compat_request)
    controller = OfflineCutoverController()

    pending = controller.enter_root_external_pending(real_request)

    assert pending.selector_state is not None
    assert pending.selector_state.deployment_state is DeploymentState.CUTOVER_PENDING
    record = read_root_admission_envelope_record(
        data_root=real_request.root,
        core_relative_path=real_request.core_relative_path,
        root_admission_envelope_digest=pending.envelope.digest,
    )
    assert record is not None
    inspection = inspect_contained_core_deployment(
        data_root=real_request.root,
        core_relative_path=real_request.core_relative_path,
    )
    assert inspection.core_role == "STAGING"
    assert inspection.deployment_state is DeploymentState.LEGACY_ACTIVE
    assert inspection.witness is None
    assert not inspection.ever_active

    downgraded = replace(
        real_request,
        admission_mode=RootAdmissionMode.SYNTHETIC_V1_COMPAT,
        writer_freeze_evidence=None,
        writer_freeze_recheck=None,
    )
    with pytest.raises(OfflineCutoverRefused, match="PENDING_BINDING_MISMATCH"):
        controller.normalize_root_under_external_fence(downgraded)


def test_real_root_p2_retains_record_when_selector_transition_fails_then_retries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    compat_request, _normalization = _root_fixture(tmp_path)
    real_request = _real_request(compat_request)
    controller = OfflineCutoverController()
    expected = controller._root_envelope(real_request)

    import torment_service.substrate.offline_cutover_controller as controller_module

    def _interrupt_pending(**_kwargs):
        raise DeploymentAuthorityError("synthetic selector interruption")

    monkeypatch.setattr(controller_module, "begin_cutover_pending", _interrupt_pending)
    with pytest.raises(DeploymentAuthorityError, match="selector interruption"):
        controller.enter_root_external_pending(real_request)

    assert read_root_admission_envelope_record(
        data_root=real_request.root,
        core_relative_path=real_request.core_relative_path,
        root_admission_envelope_digest=expected.digest,
    ) is not None
    assert read_selector_state(data_root=real_request.root).deployment_state is DeploymentState.LEGACY_ACTIVE
    monkeypatch.undo()
    assert controller.enter_root_external_pending(
        real_request,
    ).selector_state.deployment_state is DeploymentState.CUTOVER_PENDING
