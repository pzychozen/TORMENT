from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from torment_service.substrate.deployment_core_maintenance import (
    inspect_contained_core_deployment,
    read_root_admission_envelope_record,
)
from torment_service.substrate.deployment_selector import (
    read_selector_state,
    resolve_deployment_agreement,
)
from torment_service.substrate.deployment_types import (
    DeploymentResolutionMode,
    DeploymentState,
    QualifiedDeploymentProfile,
)
from torment_service.substrate.production_native_owner import (
    NativeProductionResourceOwner,
    NativeProductionResourceOwnerError,
)
from torment_service.substrate.real_root_staging_bootstrap import (
    P1ExistingCoreDisposition,
    P1StagingBootstrapRequest,
    P1StaleInertCore,
    RealRootStagingBootstrap,
    RootProfileBootstrap,
    RuntimeScopeBootstrap,
)
from torment_service.substrate.root_scope_membership import RootScopeMembershipWitness
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _profile() -> QualifiedDeploymentProfile:
    return QualifiedDeploymentProfile(
        compression_enabled=False,
        deep_memory_enabled=False,
        representation_provider="test-provider",
        representation_model="test-model",
        representation_dimension=3,
        admitted_scope_plan_digest=_digest("scope-plan"),
        external_owner_digest=_digest("owner-facts"),
    )


def _request(root: Path, *, filename: str, core_id: UUID, generation: int = 1) -> P1StagingBootstrapRequest:
    scope = NativeMemoryRuntimeScope(
        workspace_id="bootstrap-workspace",
        scope_kind="PRIVATE_AGENT",
        legacy_source_namespace_id=uuid4(),
        identity_namespace_id=uuid4(),
        semantic_scope_id=uuid4(),
        agent_id="bootstrap-agent",
    )
    return P1StagingBootstrapRequest(
        data_root=root,
        native_core_database_path=root / "substrate" / "cores" / filename,
        core_id=core_id,
        root_profile=RootProfileBootstrap(
            profile_object_id=uuid4(),
            profile_generation=generation,
            identity_namespace_id=uuid4(),
            identity_namespace_key=f"profile-identity-{filename}",
            semantic_scope_id=uuid4(),
            semantic_scope_key=f"profile-scope-{filename}",
            idempotency_namespace_id=uuid4(),
            idempotency_namespace_key=f"profile-idempotency-{filename}",
            idempotency_key=f"profile-create-{filename}",
        ),
        runtime_scopes=(
            RuntimeScopeBootstrap(
                runtime_scope=scope,
                identity_namespace_key=f"scope-identity-{filename}",
                semantic_scope_key=f"scope-semantic-{filename}",
                legacy_source_namespace_key=f"scope-legacy-namespace-{filename}",
                membership_identity_namespace_id=uuid4(),
                membership_identity_namespace_key=f"membership-identity-{filename}",
                idempotency_namespace_id=uuid4(),
                idempotency_namespace_key=f"membership-idempotency-{filename}",
                idempotency_key=f"membership-create-{filename}",
                membership_witness=RootScopeMembershipWitness(
                    witness_id=f"bootstrap-witness-{filename}",
                    witness_digest=_digest(f"bootstrap-witness-{filename}"),
                    issuer_reference="p1-bootstrap-disposable-test",
                    provenance_kind="QUALIFICATION_TEST",
                ),
            ),
        ),
    )


def test_p1_bootstrap_is_source_free_contained_and_non_authoritative(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "p1-source-free"
    root.mkdir()
    request = _request(root, filename="p1-a.db", core_id=uuid4())

    original_open = Path.open

    def _forbid_source_open(path: Path, *args, **kwargs):
        if "workspaces" in path.parts or path.name in {"nodes.jsonl", "embeddings"}:
            raise AssertionError("P1_BOOTSTRAP_SOURCE_CONTACT")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", _forbid_source_open)
    result = RealRootStagingBootstrap().bootstrap(request)

    assert result.disposition is P1ExistingCoreDisposition.CREATED
    assert result.core_path == root / "substrate" / "cores" / "p1-a.db"
    inspection = inspect_contained_core_deployment(
        data_root=root,
        core_relative_path="p1-a.db",
    )
    assert inspection.core_id == request.core_id
    assert inspection.core_role == "STAGING"
    assert inspection.deployment_state is DeploymentState.LEGACY_ACTIVE
    assert inspection.witness is None
    assert not inspection.ever_active
    assert read_root_admission_envelope_record(
        data_root=root,
        core_relative_path="p1-a.db",
        root_admission_envelope_digest=_digest("not-present"),
    ) is None

    agreement = resolve_deployment_agreement(data_root=root, effective_profile=_profile())
    assert agreement.mode is DeploymentResolutionMode.LEGACY_PUBLIC
    with pytest.raises(NativeProductionResourceOwnerError, match="NATIVE_AGREEMENT"):
        NativeProductionResourceOwner.from_native_agreement(
            data_root=root,
            effective_profile=_profile(),
            agreement=agreement,
        )
    with pytest.raises(Exception):
        read_selector_state(data_root=root)


def test_p1_exact_reuse_and_stale_inert_supersession_preserve_legacy_public(tmp_path: Path) -> None:
    root = tmp_path / "p1-supersession"
    root.mkdir()
    workflow = RealRootStagingBootstrap()
    core_a = uuid4()
    request_a = _request(root, filename="stale-a.db", core_id=core_a)
    created_a = workflow.bootstrap(request_a)
    reused_a = workflow.bootstrap(request_a)

    assert created_a.disposition is P1ExistingCoreDisposition.CREATED
    assert reused_a.disposition is P1ExistingCoreDisposition.EXACT_INERT_MATCH
    stale_a = replace(
        request_a,
        root_profile=replace(request_a.root_profile, profile_generation=2),
    )
    assert workflow.classify_existing(stale_a) is P1ExistingCoreDisposition.STALE_INERT
    with pytest.raises(P1StaleInertCore, match="stale inert"):
        workflow.bootstrap(stale_a)

    request_b = _request(root, filename="replacement-b.db", core_id=uuid4(), generation=2)
    created_b = workflow.bootstrap(request_b)
    assert created_b.disposition is P1ExistingCoreDisposition.CREATED
    assert created_b.core_id != created_a.core_id

    for filename, core_id in (("stale-a.db", core_a), ("replacement-b.db", request_b.core_id)):
        inspection = inspect_contained_core_deployment(data_root=root, core_relative_path=filename)
        assert inspection.core_id == core_id
        assert inspection.core_role == "STAGING"
        assert inspection.deployment_state is DeploymentState.LEGACY_ACTIVE
        assert inspection.witness is None
        assert not inspection.ever_active

    assert resolve_deployment_agreement(
        data_root=root, effective_profile=_profile()
    ).mode is DeploymentResolutionMode.LEGACY_PUBLIC
