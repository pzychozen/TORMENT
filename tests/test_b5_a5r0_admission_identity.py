"""B5-A5R0 immutable admission identity and pending compatibility tests."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from torment_service.fabric import TormentFabric
from torment_service.public_runtime import (
    PublicRuntimeConfiguration,
    PublicRuntimeStartupRefused,
    create_public_runtime,
)
from torment_service.substrate.deployment_core_maintenance import (
    activate_core,
    enter_cutover_pending,
    inspect_contained_core_deployment,
    staging_legacy_witness,
)
from torment_service.substrate.deployment_selector import (
    activate_selector_native,
    begin_cutover_pending,
    establish_selector_era,
    initialize_selector,
    resolve_deployment_agreement,
)
from torment_service.substrate.deployment_types import (
    DeploymentAuthorityError,
    DeploymentResolutionMode,
    DeploymentState,
    QualifiedDeploymentProfile,
)
from torment_service.substrate.ids import generate_native_id
from torment_service.substrate.migration import (
    ExistingWorkspaceMultiScopeAdmissionRefused,
    ExistingWorkspaceNativeMultiScopeAdmissionRequest,
    ExistingWorkspaceNativeMultiScopeAdmissionService,
    WorkspaceNativeEmbedderIdentity,
    WorkspaceNativeFeaturePosture,
    load_existing_workspace_multi_scope_admission_descriptor,
)
from torment_service.substrate.production_native_owner import NativeProductionResourceOwner

from test_substrate_existing_workspace_multi_scope_admission import (
    _lane,
    _observations,
    _plans,
    _post_write_private,
)


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _workspace(data_root: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build real legacy files through Fabric, without a public service process."""

    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_HASH_DIM", "3")
    monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
    monkeypatch.setenv("TORMENT_CHECKPOINT_ENABLE", "0")
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "0")
    monkeypatch.setenv("TORMENT_THINKING_ADVISORY", "0")
    monkeypatch.setenv("TORMENT_SRG_COGNITION", "0")
    monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "0")
    monkeypatch.setenv("TORMENT_ID_ANCHOR_MIN_COUNT", "1000")
    fabric = TormentFabric(data_dir=str(data_root))
    try:
        fabric.get_workspace("orchard", domains=["personal", "research", "engineering", "creative"])
        fabric.create_agent("orchard", "aria")
        vectors = {
            "personal": ((0.9, 0.3, 0.1), (0.85, 0.35, 0.1), (0.8, 0.4, 0.1)),
            "research": ((0.7, 0.6, 0.1), (0.68, 0.62, 0.1), (0.66, 0.64, 0.1)),
            "engineering": ((0.1, 0.8, 0.5), (0.1, 0.78, 0.52), (0.1, 0.76, 0.54)),
            "creative": ((0.3, 0.1, 0.9), (0.32, 0.1, 0.88), (0.34, 0.1, 0.86)),
        }
        step = 0
        for domain, rows in vectors.items():
            for ordinal, vector in enumerate(rows):
                step += 1
                fabric.ingest(
                    "orchard", "aria", f"{domain} frozen memory {ordinal}",
                    step=step,
                    scope="private" if domain == "personal" else "shared",
                    domain_id=domain,
                    supplied_summary=f"{domain} frozen memory {ordinal}",
                    supplied_embedding=list(vector),
                )
    finally:
        fabric.close()
    return data_root / "workspaces" / "orchard"


def _request(data_root: Path, root: Path):
    lane = _lane()
    plans = _plans(root)
    profile = QualifiedDeploymentProfile(
        compression_enabled=False,
        deep_memory_enabled=False,
        representation_provider=lane.provider,
        representation_model=lane.model,
        representation_dimension=lane.dimension,
        admitted_scope_plan_digest=_digest([plan.payload() for plan in plans]),
        external_owner_digest=hashlib.sha256(b"a5r0-external-owner-witness").hexdigest(),
    )
    (data_root / "substrate" / "cores").mkdir(parents=True)
    (data_root / "admission").mkdir()
    (data_root / "snapshots").mkdir()
    request = ExistingWorkspaceNativeMultiScopeAdmissionRequest(
        legacy_workspace_root=root,
        workspace_id="orchard",
        native_core_database_path=data_root / "substrate" / "cores" / "a5r0-rehearsal.db",
        admission_descriptor_path=data_root / "admission" / "a5r0-admission.json",
        snapshot_root=data_root / "snapshots" / "a5r0-evidence",
        admission_key="a5r0-rehearsal-001",
        lane_plans=plans,
        unknown_semantic_scope_id=generate_native_id(),
        qualified_representation_lane=lane,
        staging_feature_posture=WorkspaceNativeFeaturePosture.a3d10_core_staging(),
        production_feature_posture=WorkspaceNativeFeaturePosture.a3d10_core_staging(),
        qualification_embedder_identity=WorkspaceNativeEmbedderIdentity(lane.provider, lane.model, lane.dimension),
        private_post_write_configuration=_post_write_private(plans[0], lane),
        effective_deployment_profile=profile,
        retained_side_store_eid_observations=_observations(),
    )
    return request, profile


def test_prepare_is_inert_idempotent_and_refuses_changed_source_or_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_root = tmp_path / "rehearsal"
    root = _workspace(data_root, monkeypatch)
    request, _profile = _request(data_root, root)
    service = ExistingWorkspaceNativeMultiScopeAdmissionService()

    first = service.prepare(request)
    core = inspect_contained_core_deployment(
        data_root=data_root,
        core_relative_path="a5r0-rehearsal.db",
    )
    assert first.state.value == "ADMISSION_INCOMPLETE_RESUMABLE"
    assert core.core_role == "STAGING"
    assert core.deployment_state is DeploymentState.LEGACY_ACTIVE
    assert core.witness is None
    assert first.snapshot_witnesses

    recovered = service.prepare(request)
    assert recovered.resumed is True
    assert recovered.native_core_id == first.native_core_id
    assert recovered.snapshot_witnesses == first.snapshot_witnesses
    assert recovered.admission_identity_digest == first.admission_identity_digest
    assert recovered.descriptor_digest == first.descriptor_digest

    with pytest.raises(ExistingWorkspaceMultiScopeAdmissionRefused, match="REQUEST_MISMATCH"):
        service.prepare(replace(request, admission_key="a5r0-changed-key"))

    source = root / "domains" / "research" / "shared" / "nodes.jsonl"
    original = source.read_bytes()
    source.write_bytes(original + b"\n")
    with pytest.raises(ExistingWorkspaceMultiScopeAdmissionRefused, match="SOURCE_EVIDENCE_MISMATCH"):
        service.prepare(request)
    source.write_bytes(original)


def test_pending_admission_completion_activation_and_owner_require_both_witnesses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_root = tmp_path / "rehearsal"
    root = _workspace(data_root, monkeypatch)
    request, profile = _request(data_root, root)
    service = ExistingWorkspaceNativeMultiScopeAdmissionService()
    prepared = service.prepare(request)

    establish_selector_era(data_root=data_root)
    legacy = initialize_selector(data_root=data_root, operation_key="a5r0-selector-init")
    pending = begin_cutover_pending(
        data_root=data_root,
        core_relative_path="a5r0-rehearsal.db",
        descriptor_digest=prepared.admission_identity_digest,
        profile=profile,
        expected_generation=legacy.generation,
        operation_key="a5r0-selector-pending",
    )
    assert resolve_deployment_agreement(data_root=data_root, effective_profile=profile).mode is DeploymentResolutionMode.MAINTENANCE_ONLY
    with pytest.raises(PublicRuntimeStartupRefused):
        create_public_runtime(
            data_root,
            PublicRuntimeConfiguration(profile, request.admission_descriptor_path),
        )

    with pytest.raises(RuntimeError, match="private B2"):
        service.admit(request, _test_interrupt_after="PRIVATE_B2")
    interrupted = load_existing_workspace_multi_scope_admission_descriptor(request.admission_descriptor_path)
    assert interrupted.digest != prepared.descriptor_digest
    assert interrupted.admission_identity_digest == prepared.admission_identity_digest
    assert inspect_contained_core_deployment(
        data_root=data_root,
        core_relative_path="a5r0-rehearsal.db",
    ).deployment_state is DeploymentState.LEGACY_ACTIVE

    admitted = service.admit(request)
    completion = admitted.descriptor.completed_admission_witness()
    assert admitted.descriptor.admission_identity_digest == prepared.admission_identity_digest
    assert completion.completed_descriptor_digest == admitted.descriptor.digest
    assert completion.admission_identity_digest == pending.descriptor_digest

    inspection = inspect_contained_core_deployment(
        data_root=data_root,
        core_relative_path="a5r0-rehearsal.db",
    )
    core_pending = enter_cutover_pending(
        data_root=data_root,
        core_relative_path="a5r0-rehearsal.db",
        expected_witness=staging_legacy_witness(
            inspection,
            descriptor_digest=prepared.admission_identity_digest,
            profile_digest=profile.digest,
        ),
        selector_generation=pending.generation,
        selector_witness_digest=pending.core_witness_digest or "",
        operation_key="a5r0-core-pending",
    )
    with pytest.raises(Exception, match="completed admission witness"):
        activate_core(
            data_root=data_root,
            core_relative_path="a5r0-rehearsal.db",
            expected_witness=core_pending.witness,
            selector_generation=pending.generation,
            selector_witness_digest=pending.core_witness_digest or "",
            operation_key="a5r0-core-active-without-completion",
        )
    with pytest.raises(DeploymentAuthorityError, match="deployment profile"):
        activate_core(
            data_root=data_root,
            core_relative_path="a5r0-rehearsal.db",
            expected_witness=core_pending.witness,
            selector_generation=pending.generation,
            selector_witness_digest=pending.core_witness_digest or "",
            operation_key="a5r0-core-active-wrong-profile",
            completion_witness=replace(
                completion,
                profile_digest=hashlib.sha256(b"a5r0-wrong-profile").hexdigest(),
            ),
        )
    active = activate_core(
        data_root=data_root,
        core_relative_path="a5r0-rehearsal.db",
        expected_witness=core_pending.witness,
        selector_generation=pending.generation,
        selector_witness_digest=pending.core_witness_digest or "",
        operation_key="a5r0-core-active",
        completion_witness=completion,
    )
    active_selector = activate_selector_native(
        data_root=data_root,
        core_relative_path="a5r0-rehearsal.db",
        core_result=active,
        expected_generation=pending.generation,
        operation_key="a5r0-selector-active",
    )
    agreement = resolve_deployment_agreement(data_root=data_root, effective_profile=profile)
    assert active_selector.descriptor_digest == prepared.admission_identity_digest
    assert agreement.mode is DeploymentResolutionMode.NATIVE_AGREEMENT
    owner = NativeProductionResourceOwner.from_native_agreement(
        data_root=data_root,
        effective_profile=profile,
        agreement=agreement,
        admission_descriptor_path=request.admission_descriptor_path,
    )
    owner.close()

    original = Path(request.admission_descriptor_path).read_text(encoding="utf-8")
    wrapped = json.loads(original)
    wrapped["payload"]["multi_scope_b5"]["joint_binding_constructible"] = False
    wrapped["descriptor_digest"] = _digest(wrapped["payload"])
    Path(request.admission_descriptor_path).write_text(
        json.dumps(wrapped, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="descriptor"):
        NativeProductionResourceOwner.from_native_agreement(
            data_root=data_root,
            effective_profile=profile,
            agreement=agreement,
            admission_descriptor_path=request.admission_descriptor_path,
        )
    Path(request.admission_descriptor_path).write_text(original, encoding="utf-8")
