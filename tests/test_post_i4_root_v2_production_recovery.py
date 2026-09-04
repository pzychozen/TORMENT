from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.public_runtime import PublicRuntimeConfiguration
from torment_service.substrate.deployment_core_maintenance import (
    activate_core,
    enter_cutover_pending,
    inspect_contained_core_deployment,
    record_root_admission_envelope,
    record_root_disposition_execution,
    staging_legacy_witness,
)
from torment_service.substrate.deployment_selector import (
    activate_selector_native,
    begin_cutover_pending,
    establish_selector_era,
    initialize_selector,
    resolve_deployment_agreement,
)
from torment_service.substrate.deployment_diagnostic import (
    DeploymentDiagnosticRequest,
    inspect_deployment_diagnostic,
)
from torment_service.substrate.deployment_types import (
    QualifiedDeploymentProfile,
    RootAdmissionCompletionWitness,
)
from torment_service.substrate.errors import DeploymentAuthorityError
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration.explicit_source_evidence import (
    EvidenceOwnerBoundary,
    EvidenceOwnerBoundaryKind,
    EvidenceSemanticRole,
    RootEvidenceManifest,
    SourceOwnerClass,
    capture_present_source_evidence,
)
from torment_service.substrate.migration.root_admission_description import (
    ExpectedRootCensus,
    MaterializedRootScopePlan,
    RepresentationDispositionCount,
    RootFeaturePosture,
    RootNativeProductionAdmissionDescription,
    RootRepresentationDisposition,
    WorkspaceRootAdmissionPlan,
    WorkspaceTopologyCounts,
)
from torment_service.substrate.migration.root_scope import RootScopeKey, RootScopeKind
from torment_service.substrate.migration.runtime_readiness import MigrationRuntimeScopePlan
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.production_native_owner import (
    NativeProductionResourceOwner,
    NativeProductionResourceOwnerError,
)
from torment_service.substrate.root_blocker5_binding import (
    RootWriterFreezeWitness,
    build_root_admission_envelope,
    declared_census_digest,
    execute_synthetic_root_disposition_plan,
    frozen_root_geometry_disposition_plan,
    root_runtime_scope_plan_digest,
)
from torment_service.substrate.root_profile import (
    ROOT_NATIVE_PROFILE_GENERATION_KIND,
    current_root_profile_generation,
    root_profile_generation_payload,
)
from torment_service.substrate.root_scope_membership import (
    RootScopeMembershipService,
    RootScopeMembershipWitness,
)
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
from torment_service.substrate.schema import create_schema


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane(
        "st", "BAAI/bge-small-en-v1.5", 384,
        "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32",
    )


class _NoopSyntheticDisposition:
    def execute(self, **_kwargs: object) -> str:
        return "SYNTHETIC_QUALIFICATION_NO_MUTATION"


def _insert_identity(connection, identity_id: UUID, label: str) -> None:
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(identity_id), label),
    )


def _insert_scope(connection, scope_id: UUID, label: str) -> None:
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(scope_id), label),
    )


def _insert_source(connection, source_id: UUID, label: str) -> None:
    connection.execute(
        "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(source_id), label),
    )


def _insert_idempotency(connection, namespace_id: UUID, label: str) -> None:
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(namespace_id), label),
    )


def _plan(connection, *, workspace_id: str, scope_key: RootScopeKey, motif_domain_id: str) -> MigrationRuntimeScopePlan:
    target_identity = generate_native_id()
    target_scope = generate_native_id()
    legacy_source = generate_native_id()
    motif_alias = generate_native_id()
    motif_identity = generate_native_id()
    membership_identity = generate_native_id()
    idempotency = generate_native_id()
    _insert_identity(connection, target_identity, f"{scope_key.qualifier}-target")
    _insert_scope(connection, target_scope, f"{scope_key.qualifier}-scope")
    _insert_source(connection, legacy_source, f"{scope_key.qualifier}-source")
    _insert_source(connection, motif_alias, f"{scope_key.qualifier}-motif-alias")
    _insert_identity(connection, motif_identity, f"{scope_key.qualifier}-motif")
    _insert_identity(connection, membership_identity, f"{scope_key.qualifier}-membership")
    _insert_idempotency(connection, idempotency, f"{scope_key.qualifier}-operations")
    return MigrationRuntimeScopePlan(
        legacy_source_namespace_id=legacy_source,
        workspace_id=workspace_id,
        scope_kind="PRIVATE_AGENT" if scope_key.scope_kind is RootScopeKind.PRIVATE else "SHARED_DOMAIN",
        target_identity_namespace_id=target_identity,
        target_semantic_scope_id=target_scope,
        motif_alias_namespace_id=motif_alias,
        motif_identity_namespace_id=motif_identity,
        membership_identity_namespace_id=membership_identity,
        idempotency_namespace_id=idempotency,
        agent_id=scope_key.agent_id,
        domain_id=scope_key.domain_id,
        motif_domain_id=motif_domain_id,
    )


def _runtime_scope(plan: MigrationRuntimeScopePlan) -> NativeMemoryRuntimeScope:
    return NativeMemoryRuntimeScope(
        workspace_id=plan.workspace_id,
        scope_kind=plan.scope_kind,
        legacy_source_namespace_id=plan.legacy_source_namespace_id,
        identity_namespace_id=plan.target_identity_namespace_id,
        semantic_scope_id=plan.target_semantic_scope_id,
        agent_id=plan.agent_id,
        domain_id=plan.domain_id,
    )


def _completion(envelope, profile, root_profile) -> RootAdmissionCompletionWitness:
    lane = envelope.description.target_representation_lane
    return RootAdmissionCompletionWitness(
        data_root_identity=envelope.description.data_root_identity,
        root_admission_envelope_digest=envelope.digest,
        declared_census_digest=declared_census_digest(envelope.description),
        discovered_census_digest=envelope.discovered_census.digest,
        manifest_digest=envelope.description.explicit_source_manifest.digest,
        external_owner_observation_digest=envelope.description.external_owner_observation_digest,
        geometry_disposition_table_digest=envelope.geometry_disposition_plan.digest,
        target_representation_identity=(
            f"{lane.provider}:{lane.model}:{lane.dimension}:{lane.representation_class}"
        ),
        root_writer_freeze_witness_digest=envelope.writer_freeze.digest,
        native_staging_core_id=envelope.native_staging_core_id,
        qualified_deployment_profile_digest=profile.digest,
        root_profile_object_id=root_profile.profile_object_id,
        root_profile_revision_id=root_profile.profile_revision_id,
        root_profile_ordinal=root_profile.profile_revision_ordinal,
        root_membership_closure_digest=envelope.root_membership_closure_digest,
        normalization_closure_digest=_digest("root-v2-synthetic-normalization-complete"),
    )


def _active_root_fixture(tmp_path: Path, *, shared: bool = True):
    root = tmp_path / "root-v2"
    workspace = root / "workspaces" / "ws-one"
    private = workspace / "agents" / "agent-one" / "private"
    private.mkdir(parents=True)
    (workspace / "workspace_meta.json").write_text("{}", encoding="utf-8")
    (private / "nodes.jsonl").write_text("{}\n", encoding="utf-8")
    shared_path = workspace / "domains" / "domain-one" / "shared"
    if shared:
        shared_path.mkdir(parents=True)
        (shared_path / "nodes.jsonl").write_text("{}\n", encoding="utf-8")
    core_path = root / "substrate" / "cores" / "root.db"
    core_path.parent.mkdir(parents=True)
    qualified = open_temporary_test_connection(core_path)
    try:
        connection = qualified.connection
        metadata = create_schema(connection)
        core_id = UUID(bytes=metadata.core_id)
        profile_identity = generate_native_id()
        profile_scope = generate_native_id()
        profile_idempotency = generate_native_id()
        _insert_identity(connection, profile_identity, "root-profile")
        _insert_scope(connection, profile_scope, "root-profile-scope")
        _insert_idempotency(connection, profile_idempotency, "root-profile-operations")
        NativeObjectService(connection).create_object(
            idempotency_namespace_id=profile_idempotency,
            idempotency_key="root-v2-profile",
            state=ObjectState(
                profile_identity,
                profile_scope,
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
        root_profile = current_root_profile_generation(connection)
        private_key = RootScopeKey("ws-one", RootScopeKind.PRIVATE, agent_id="agent-one")
        plans = [_plan(connection, workspace_id="ws-one", scope_key=private_key, motif_domain_id="domain-one")]
        if shared:
            shared_key = RootScopeKey("ws-one", RootScopeKind.SHARED, domain_id="domain-one")
            plans.append(_plan(connection, workspace_id="ws-one", scope_key=shared_key, motif_domain_id="domain-one"))
        runtime_scopes = tuple(_runtime_scope(plan) for plan in plans)
        membership = RootScopeMembershipService(connection)
        for plan, runtime in zip(plans, runtime_scopes, strict=True):
            membership.admit(
                profile=root_profile,
                runtime_scope=runtime,
                witness=RootScopeMembershipWitness(
                    witness_id=f"synthetic:{plan.workspace_id}:{plan.qualifier}",
                    witness_digest=_digest(plan.qualifier),
                    issuer_reference="root-v2-production-recovery-test",
                    provenance_kind="QUALIFICATION_TEST",
                ),
                membership_identity_namespace_id=plan.membership_identity_namespace_id,
                idempotency_namespace_id=plan.idempotency_namespace_id,
                idempotency_key=f"root-v2-membership:{plan.scope_kind}:{plan.qualifier}",
            )
        evidence = [
            capture_present_source_evidence(
                data_root=root,
                owner_class=SourceOwnerClass.PRIVATE_GRAPH_SOURCE,
                owner_boundary=EvidenceOwnerBoundary(
                    "ws-one", EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id="agent-one",
                ),
                canonical_locator="nodes.jsonl",
                semantic_role=EvidenceSemanticRole.NODES,
                scope_key=private_key,
            ),
        ]
        private_scopes = (MaterializedRootScopePlan(
            private_key, RootRepresentationDisposition.TARGET_COMPATIBLE,
        ),)
        shared_scopes = ()
        if shared:
            shared_key = RootScopeKey("ws-one", RootScopeKind.SHARED, domain_id="domain-one")
            evidence.append(capture_present_source_evidence(
                data_root=root,
                owner_class=SourceOwnerClass.SHARED_GRAPH_SOURCE,
                owner_boundary=EvidenceOwnerBoundary(
                    "ws-one", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="domain-one",
                ),
                canonical_locator="nodes.jsonl",
                semantic_role=EvidenceSemanticRole.NODES,
                scope_key=shared_key,
            ))
            shared_scopes = (MaterializedRootScopePlan(
                shared_key, RootRepresentationDisposition.TARGET_COMPATIBLE,
            ),)
        description = RootNativeProductionAdmissionDescription(
            data_root_identity="root-v2-synthetic",
            operator_identity="root-v2-test",
            workspace_plans=(WorkspaceRootAdmissionPlan(
                "ws-one", private_scopes, shared_scopes,
            ),),
            target_representation_lane=_lane(),
            expected_census=ExpectedRootCensus(
                workspace_count=1,
                materialized_private_scope_count=1,
                materialized_shared_scope_count=1 if shared else 0,
                total_materialized_scope_count=2 if shared else 1,
                representation_disposition_counts=tuple(
                    RepresentationDispositionCount(
                        disposition,
                        (2 if shared else 1) if disposition is RootRepresentationDisposition.TARGET_COMPATIBLE else 0,
                    )
                    for disposition in RootRepresentationDisposition
                ),
                workspace_topology_counts=WorkspaceTopologyCounts(
                    0, 1, 0, 0 if shared else 1, 1 if shared else 0, 0,
                ),
            ),
            explicit_source_manifest=RootEvidenceManifest(tuple(evidence)),
            external_owner_observations=(),
            feature_posture=RootFeaturePosture("root-v2-synthetic", False, False),
        )
        profile = QualifiedDeploymentProfile(
            compression_enabled=False,
            deep_memory_enabled=False,
            representation_provider="st",
            representation_model="BAAI/bge-small-en-v1.5",
            representation_dimension=384,
            admitted_scope_plan_digest=root_runtime_scope_plan_digest(tuple(plans), _lane()),
            external_owner_digest=description.external_owner_observation_digest,
        )
        envelope = build_root_admission_envelope(
            data_root=root,
            description=description,
            writer_freeze=RootWriterFreezeWitness(
                data_root_identity=description.data_root_identity,
                writer_freeze_operation_identity="root-v2-synthetic-freeze",
                writer_evidence_digest=_digest("root-v2-synthetic-writers-drained"),
            ),
            geometry_disposition_plan=frozen_root_geometry_disposition_plan(
                external_owner_observation_digest=description.external_owner_observation_digest,
            ),
            effective_profile=profile,
            native_staging_core_id=core_id,
            root_profile=root_profile,
            runtime_scopes=runtime_scopes,
            runtime_scope_plans=tuple(plans),
            connection=connection,
        )
    finally:
        qualified.close()

    record_root_admission_envelope(
        data_root=root,
        core_relative_path="root.db",
        envelope=envelope,
        operation_key="root-v2-test:envelope",
    )
    establish_selector_era(data_root=root)
    initial = initialize_selector(data_root=root, operation_key="root-v2-test:selector-init")
    pending = begin_cutover_pending(
        data_root=root,
        core_relative_path="root.db",
        descriptor_digest=envelope.digest,
        profile=profile,
        expected_generation=initial.generation,
        operation_key="root-v2-test:selector-pending",
    )
    inspection = inspect_contained_core_deployment(data_root=root, core_relative_path="root.db")
    core_pending = enter_cutover_pending(
        data_root=root,
        core_relative_path="root.db",
        expected_witness=staging_legacy_witness(
            inspection,
            descriptor_digest=envelope.digest,
            profile_digest=profile.digest,
        ),
        selector_generation=pending.generation,
        selector_witness_digest=pending.core_witness_digest or "",
        operation_key="root-v2-test:core-pending",
    )
    completion = _completion(envelope, profile, root_profile)
    core_active = activate_core(
        data_root=root,
        core_relative_path="root.db",
        expected_witness=core_pending.witness,
        selector_generation=pending.generation,
        selector_witness_digest=pending.core_witness_digest or "",
        operation_key="root-v2-test:core-active",
        completion_witness=completion,
    )
    receipt = execute_synthetic_root_disposition_plan(
        envelope=envelope,
        adapter=_NoopSyntheticDisposition(),
    )
    receipt = record_root_disposition_execution(
        data_root=root,
        core_relative_path="root.db",
        completion_witness=completion,
        receipt=receipt,
        operation_key="root-v2-test:disposition",
    )
    activate_selector_native(
        data_root=root,
        core_relative_path="root.db",
        core_result=core_active,
        expected_generation=pending.generation,
        operation_key="root-v2-test:selector-active",
        disposition_execution_receipt_digest=receipt.digest,
    )
    agreement = resolve_deployment_agreement(data_root=root, effective_profile=profile)
    return root, profile, agreement


def test_root_v2_owner_recovers_from_native_evidence_after_legacy_layout_is_unavailable(
    tmp_path: Path,
) -> None:
    root, profile, agreement = _active_root_fixture(tmp_path)
    (root / "workspaces").rename(root / "legacy-layout-unavailable")
    assert PublicRuntimeConfiguration(effective_profile=profile).admission_descriptor_path is None

    owner = NativeProductionResourceOwner.from_native_agreement(
        data_root=root,
        effective_profile=profile,
        agreement=agreement,
    )
    try:
        first = owner._recover_active_runtime(workspace_id="ws-one")
        second = owner._recover_active_runtime(workspace_id="ws-one")
        assert first is second
        assert first.lookup_private("agent-one").memory_runtime_scope.workspace_id == "ws-one"
        assert first.lookup_shared("domain-one").memory_runtime_scope.workspace_id == "ws-one"
        diagnostic = inspect_deployment_diagnostic(
            DeploymentDiagnosticRequest(root, effective_profile=profile),
        )
        assert diagnostic.deployment_mode == "NATIVE_AGREEMENT"
        assert diagnostic.admission_state == "ROOT_V2_EVIDENCE"
        assert diagnostic.completion_witness_valid is True
    finally:
        owner.close()


def test_root_v2_owner_refuses_missing_record_receipt_intent_and_unsupported_topology(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import torment_service.substrate.production_native_owner as owner_module

    root, profile, agreement = _active_root_fixture(tmp_path / "missing-record")
    monkeypatch.setattr(owner_module, "read_root_admission_envelope_record", lambda **_kwargs: None)
    with pytest.raises(NativeProductionResourceOwnerError, match="envelope evidence is missing"):
        NativeProductionResourceOwner.from_native_agreement(
            data_root=root, effective_profile=profile, agreement=agreement,
        )
    monkeypatch.undo()

    root, profile, agreement = _active_root_fixture(tmp_path / "receipt-intent")
    monkeypatch.setattr(
        owner_module,
        "read_selector_native_activation_intent",
        lambda **_kwargs: {"disposition_execution_receipt_digest": _digest("wrong-receipt")},
    )
    with pytest.raises(NativeProductionResourceOwnerError, match="disposition receipt"):
        NativeProductionResourceOwner.from_native_agreement(
            data_root=root, effective_profile=profile, agreement=agreement,
        )
    monkeypatch.undo()

    root, profile, agreement = _active_root_fixture(tmp_path / "bad-topology", shared=False)
    with pytest.raises(NativeProductionResourceOwnerError, match="topology"):
        NativeProductionResourceOwner.from_native_agreement(
            data_root=root, effective_profile=profile, agreement=agreement,
        )


def test_root_v2_owner_failure_matrix_has_no_legacy_fallback_or_repair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import torment_service.substrate.production_native_owner as owner_module

    root, profile, agreement = _active_root_fixture(tmp_path)
    with pytest.raises(NativeProductionResourceOwnerError, match="NATIVE_AGREEMENT"):
        NativeProductionResourceOwner.from_native_agreement(
            data_root=root,
            effective_profile=replace(profile, external_owner_digest=_digest("profile-mismatch")),
            agreement=agreement,
        )

    with monkeypatch.context() as scoped:
        scoped.setattr(
            owner_module,
            "_validate_production_routing_scopes",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("missing namespace")),
        )
        with pytest.raises(NativeProductionResourceOwnerError, match="namespace or membership"):
            NativeProductionResourceOwner.from_native_agreement(
                data_root=root, effective_profile=profile, agreement=agreement,
            )

    with monkeypatch.context() as scoped:
        scoped.setattr(
            owner_module,
            "root_membership_closure_digest",
            lambda **_kwargs: _digest("membership-closure-mismatch"),
        )
        with pytest.raises(NativeProductionResourceOwnerError, match="membership closure"):
            NativeProductionResourceOwner.from_native_agreement(
                data_root=root, effective_profile=profile, agreement=agreement,
            )

    with monkeypatch.context() as scoped:
        scoped.setattr(owner_module, "read_root_disposition_execution_receipt", lambda **_kwargs: None)
        with pytest.raises(NativeProductionResourceOwnerError, match="disposition receipt"):
            NativeProductionResourceOwner.from_native_agreement(
                data_root=root, effective_profile=profile, agreement=agreement,
            )

    with monkeypatch.context() as scoped:
        original = owner_module.inspect_contained_core_deployment
        scoped.setattr(
            owner_module,
            "inspect_contained_core_deployment",
            lambda **kwargs: replace(
                original(**kwargs),
                activation_completion_witness=replace(
                    original(**kwargs).activation_completion_witness,
                    native_staging_core_id=generate_native_id(),
                ),
            ),
        )
        with pytest.raises(NativeProductionResourceOwnerError, match="completion disagrees"):
            NativeProductionResourceOwner.from_native_agreement(
                data_root=root, effective_profile=profile, agreement=agreement,
            )

    (root / "workspaces").rename(root / "legacy-layout-unavailable")
    first = NativeProductionResourceOwner.from_native_agreement(
        data_root=root, effective_profile=profile, agreement=agreement,
    )
    first.close()
    second = NativeProductionResourceOwner.from_native_agreement(
        data_root=root,
        effective_profile=profile,
        agreement=resolve_deployment_agreement(data_root=root, effective_profile=profile),
    )
    second.close()


def test_root_v2_owner_refuses_completion_and_recovery_evidence_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every simulated evidence defect refuses before any workspace view exists."""

    import torment_service.substrate.production_native_owner as owner_module

    root, profile, agreement = _active_root_fixture(tmp_path)
    original_inspection = owner_module.inspect_contained_core_deployment

    def completion_with(**changes: object):
        def altered_inspection(**kwargs: object):
            inspection = original_inspection(**kwargs)
            completion = inspection.activation_completion_witness
            assert isinstance(completion, RootAdmissionCompletionWitness)
            return replace(inspection, activation_completion_witness=replace(completion, **changes))
        return altered_inspection

    with monkeypatch.context() as scoped:
        scoped.setattr(
            owner_module,
            "inspect_contained_core_deployment",
            completion_with(root_admission_envelope_digest=_digest("wrong-envelope")),
        )
        with pytest.raises(NativeProductionResourceOwnerError, match="completion disagrees"):
            NativeProductionResourceOwner.from_native_agreement(
                data_root=root, effective_profile=profile, agreement=agreement,
            )

    with monkeypatch.context() as scoped:
        scoped.setattr(
            owner_module,
            "inspect_contained_core_deployment",
            completion_with(root_profile_revision_id=generate_native_id()),
        )
        with pytest.raises(NativeProductionResourceOwnerError, match="root profile"):
            NativeProductionResourceOwner.from_native_agreement(
                data_root=root, effective_profile=profile, agreement=agreement,
            )

    with monkeypatch.context() as scoped:
        scoped.setattr(owner_module, "root_runtime_scope_plan_digest", lambda *_args: _digest("wrong-plan"))
        with pytest.raises(NativeProductionResourceOwnerError, match="envelope record"):
            NativeProductionResourceOwner.from_native_agreement(
                data_root=root, effective_profile=profile, agreement=agreement,
            )

    original_receipt = owner_module.read_root_disposition_execution_receipt
    with monkeypatch.context() as scoped:
        scoped.setattr(
            owner_module,
            "read_root_disposition_execution_receipt",
            lambda **kwargs: replace(
                original_receipt(**kwargs), native_staging_core_id=generate_native_id(),
            ),
        )
        with pytest.raises(NativeProductionResourceOwnerError, match="disposition receipt"):
            NativeProductionResourceOwner.from_native_agreement(
                data_root=root, effective_profile=profile, agreement=agreement,
            )

    for membership_defect in ("missing", "retired", "duplicate RootScopeKey"):
        with monkeypatch.context() as scoped:
            scoped.setattr(
                owner_module,
                "root_membership_closure_digest",
                lambda **_kwargs: (_ for _ in ()).throw(RuntimeError(membership_defect)),
            )
            with pytest.raises(NativeProductionResourceOwnerError, match="namespace or membership"):
                NativeProductionResourceOwner.from_native_agreement(
                    data_root=root, effective_profile=profile, agreement=agreement,
                )

    with monkeypatch.context() as scoped:
        scoped.setattr(
            owner_module,
            "_require_root_v2_topology",
            lambda *_args: (_ for _ in ()).throw(
                NativeProductionResourceOwnerError("partial root topology")
            ),
        )
        with pytest.raises(NativeProductionResourceOwnerError, match="partial root topology"):
            NativeProductionResourceOwner.from_native_agreement(
                data_root=root, effective_profile=profile, agreement=agreement,
            )

    owner = NativeProductionResourceOwner.from_native_agreement(
        data_root=root, effective_profile=profile, agreement=agreement,
    )
    owner.close()
