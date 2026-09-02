"""B5-A5 offline controller qualification over isolated rehearsal roots."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Callable

import pytest
from fastapi.testclient import TestClient

from torment_service.fabric import TormentFabric
from torment_service.memory_graph import MemoryGraph
from torment_service.public_runtime import (
    PublicRuntimeConfiguration,
    PublicRuntimeMode,
    PublicRuntimeStartupRefused,
    close_public_runtime,
    configure_public_runtime,
    create_public_runtime,
    reset_public_runtime_for_test,
)
from torment_service.request_context import RequestContext, TRUST_READ_ONLY
from torment_service.spine import SpineRequest, submit_task
from torment_service.substrate.deployment_selector import resolve_deployment_agreement
from torment_service.substrate.deployment_types import (
    DeploymentResolutionMode,
    DeploymentState,
    QualifiedDeploymentProfile,
)
from torment_service.substrate.ids import generate_native_id
from torment_service.substrate.offline_cutover_controller import (
    OfflineCutoverController,
    OfflineCutoverRefused,
    OfflineCutoverRequest,
    OfflineCutoverStage,
    OfflineWriterDrainWitness,
)

from test_b5_a5r0_admission_identity import _digest, _request, _workspace
from test_substrate_existing_workspace_multi_scope_admission import (
    _Embedder,
    _create_real_workspace,
    _freeze_zero_eid_overlap,
    _lane,
    _observations,
    _plans,
    _post_write_private,
)
from torment_service.substrate.migration import (
    ExistingWorkspaceNativeMultiScopeAdmissionRequest,
    WorkspaceNativeEmbedderIdentity,
    WorkspaceNativeFeaturePosture,
)


class _NativeLaneFabric(TormentFabric):
    """Keep public reconstruction on the frozen 3D qualified hash lane."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kernel.embedder = _Embedder()


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _set_hash_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in {
        "TORMENT_EMBED_PROVIDER": "hash",
        "TORMENT_HASH_DIM": "3",
        "TORMENT_CHARACTER_ENABLE": "0",
        "TORMENT_CHECKPOINT_ENABLE": "0",
        "TORMENT_HIVEMIND_ENABLE": "0",
        "TORMENT_THINKING_ADVISORY": "0",
        "TORMENT_SRG_COGNITION": "0",
        "TORMENT_REINFORCE_SIM_THRESHOLD": "0",
        "TORMENT_ID_ANCHOR_MIN_COUNT": "1000",
    }.items():
        monkeypatch.setenv(name, value)


def _controller_request(
    data_root: Path,
    workspace_root: Path,
    *,
    admission_key: str,
    operator_key: str,
) -> tuple[OfflineCutoverRequest, QualifiedDeploymentProfile]:
    lane = _lane()
    plans = _plans(workspace_root)
    profile = QualifiedDeploymentProfile(
        compression_enabled=False,
        deep_memory_enabled=False,
        representation_provider=lane.provider,
        representation_model=lane.model,
        representation_dimension=lane.dimension,
        admitted_scope_plan_digest=_digest([plan.payload() for plan in plans]),
        external_owner_digest=hashlib.sha256(b"b5-a5-rehearsal-external-owner").hexdigest(),
    )
    (data_root / "substrate" / "cores").mkdir(parents=True, exist_ok=True)
    (data_root / "admission").mkdir(exist_ok=True)
    (data_root / "snapshots").mkdir(exist_ok=True)
    admission = ExistingWorkspaceNativeMultiScopeAdmissionRequest(
        legacy_workspace_root=workspace_root,
        workspace_id="orchard",
        native_core_database_path=data_root / "substrate" / "cores" / "b5-a5-rehearsal.db",
        admission_descriptor_path=data_root / "admission" / "b5-a5-admission.json",
        snapshot_root=data_root / "snapshots" / "b5-a5-evidence",
        admission_key=admission_key,
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
    return OfflineCutoverRequest(
        data_root=data_root,
        admission_request=admission,
        effective_profile=profile,
        operator_cutover_key=operator_key,
        writer_drain=OfflineWriterDrainWitness("orchard", f"{operator_key}:legacy-writers-drained"),
    ), profile


def _direct_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, key: str) -> tuple[OfflineCutoverRequest, QualifiedDeploymentProfile]:
    data_root = tmp_path / key
    workspace_root = _workspace(data_root, monkeypatch)
    admission, profile = _request(data_root, workspace_root)
    return OfflineCutoverRequest(
        data_root=data_root,
        admission_request=replace(admission, admission_key=key),
        effective_profile=profile,
        operator_cutover_key=key,
        writer_drain=OfflineWriterDrainWitness("orchard", f"{key}:drained"),
    ), profile


def _forbid_legacy_memory_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[list[str], Callable[[], None]]:
    calls: list[str] = []
    originals: dict[str, object] = {}

    def _refuse(*_args, _method: str, **_kwargs):
        calls.append(_method)
        raise AssertionError(f"native public path touched legacy MemoryGraph.{_method}")

    for method in ("__init__", "search", "search_by_embedding", "spawn_memory", "update_payload", "flush_node"):
        originals[method] = getattr(MemoryGraph, method)
        monkeypatch.setattr(
            MemoryGraph,
            method,
            lambda *_args, _method=method, **_kwargs: _refuse(*_args, _method=_method, **_kwargs),
        )

    def restore() -> None:
        for method, original in originals.items():
            setattr(MemoryGraph, method, original)

    return calls, restore


def _freeze_native_compatible_external_policy(workspace_root: Path) -> None:
    """Freeze the already-qualified inactive motif policy before P0 drain."""

    path = workspace_root / "domain_policies.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["policies"]["personal"]["auto_merge_motifs"] = False
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_controller_resumes_every_admission_interruption_under_external_pending(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _set_hash_environment(monkeypatch)
    cases = (
        ("private-b2", {"_test_interrupt_after": "PRIVATE_B2"}),
        ("between-lanes", {"_test_interrupt_after": "BETWEEN_PRIVATE_AND_SHARED"}),
        ("shared-b3a", {"_test_interrupt_after": "SHARED_B3A"}),
        ("shared-b4a", {"_test_interrupt_after": "SHARED_B4A"}),
        ("before-b5", {"_test_interrupt_after": "BEFORE_B5"}),
        ("after-b5", {"_test_lose_response_after": "B5"}),
    )
    for key, interruption in cases:
        request, profile = _direct_request(tmp_path, monkeypatch, key)
        controller = OfflineCutoverController()
        prepared = controller.prepare(request)
        pending = controller.enter_external_pending(request)
        with pytest.raises(RuntimeError):
            controller.admit_under_external_fence(request, **interruption)
        assert resolve_deployment_agreement(
            data_root=request.root, effective_profile=profile,
        ).mode is DeploymentResolutionMode.MAINTENANCE_ONLY
        resumed = controller.admit_under_external_fence(request)
        assert resumed.descriptor.admission_identity_digest == prepared.admission_identity_digest
        assert resumed.descriptor.native_core_id == prepared.core.core_id
        assert resumed.descriptor.payload["admission_identity"]["snapshots"] == prepared.descriptor.payload["admission_identity"]["snapshots"]
        assert controller.current_stage(request) is OfflineCutoverStage.ADMISSION_COMPLETE
        assert pending.selector_state is not None

        changed_profile = replace(
            profile,
            external_owner_digest=hashlib.sha256(f"{key}:changed-owner".encode("utf-8")).hexdigest(),
        )
        changed_request = replace(
            request,
            admission_request=replace(
                request.admission_request,
                effective_deployment_profile=changed_profile,
            ),
            effective_profile=changed_profile,
        )
        with pytest.raises(OfflineCutoverRefused):
            controller.prepare(changed_request)


def test_offline_cutover_full_rehearsal_abort_and_post_active_refusal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Exercise P0--P8, C0.5/C5/C7/C8, and a separate never-active abort root."""

    _set_hash_environment(monkeypatch)
    import torment_service.app as app_module
    import torment_service.mcp_server as mcp_module
    import torment_service.public_runtime as public_runtime

    monkeypatch.setattr(public_runtime, "TormentFabric", _NativeLaneFabric)
    data_root = tmp_path / "full-rehearsal"
    workspace_root = _create_real_workspace(data_root)
    _freeze_native_compatible_external_policy(workspace_root)
    _freeze_zero_eid_overlap(workspace_root, _plans(workspace_root))
    legacy_before = _tree_digest(workspace_root)
    request, profile = _controller_request(
        data_root, workspace_root, admission_key="b5-a5-full-admission", operator_key="b5-a5-full",
    )
    controller = OfflineCutoverController()

    # P0 and C0/P1/C0.5: the real legacy service has stopped; its root is
    # frozen, and an inert prepared core cannot seize public authority.
    assert resolve_deployment_agreement(data_root=data_root, effective_profile=profile).mode is DeploymentResolutionMode.LEGACY_PUBLIC
    prepared = controller.prepare(request)
    retried = controller.prepare(request)
    assert retried.admission_identity_digest == prepared.admission_identity_digest
    assert retried.core.core_id == prepared.core.core_id
    config = PublicRuntimeConfiguration(profile, request.admission_request.admission_descriptor_path)
    monkeypatch.setattr(app_module, "DATA_DIR", str(data_root))
    app_module.configure_app_public_runtime(config)
    try:
        with TestClient(app_module.app) as client:
            assert client.get("/health").json()["public_memory_mode"] == "LEGACY"
    finally:
        reset_public_runtime_for_test(data_root)
    assert _tree_digest(workspace_root) == legacy_before

    # P2/C1: both public transports refuse while the controller alone holds
    # maintenance authority.
    pending = controller.enter_external_pending(request)
    with pytest.raises(PublicRuntimeStartupRefused):
        create_public_runtime(data_root)
    with pytest.raises(PublicRuntimeStartupRefused):
        create_public_runtime(data_root, config)
    old_mcp_fabric, old_mcp_context = mcp_module._fabric, mcp_module._client_ctx
    monkeypatch.setenv("TORMENT_MCP_DATA_DIR", str(data_root))
    mcp_module._fabric = None
    try:
        with pytest.raises(PublicRuntimeStartupRefused):
            mcp_module._get_fabric()
    finally:
        mcp_module._fabric, mcp_module._client_ctx = old_mcp_fabric, old_mcp_context
        reset_public_runtime_for_test(data_root)
    monkeypatch.setattr(app_module, "DATA_DIR", str(data_root))
    app_module.configure_app_public_runtime(config)
    with pytest.raises(PublicRuntimeStartupRefused):
        with TestClient(app_module.app):
            pass
    reset_public_runtime_for_test(data_root)
    assert pending.stage is OfflineCutoverStage.EXTERNAL_PENDING

    # P3/P4 plus pre-activation cold recovery.  Every reader opens only the
    # admitted STAGING core; public authority remains maintenance-only.
    completed = controller.admit_under_external_fence(request)
    verified = controller.verify_completion(request)
    assert completed.descriptor.digest == verified.descriptor.digest
    staging = controller.staging_read_model(request)
    assert [scope.memory_runtime_scope.qualifier for scope in staging.scopes] == ["aria", "creative", "engineering", "research"]
    for scope in staging.scopes:
        with scope.open_readers():
            pass

    # P5/C4 then P6/C5: core transitions are recoverable while external
    # authority remains pending and both public starts still refuse.
    core_pending = controller.enter_core_pending(request)
    assert core_pending.witness.deployment_state is DeploymentState.CUTOVER_PENDING
    assert controller.current_stage(request) is OfflineCutoverStage.CORE_PENDING
    core_active = controller.activate_core(request)
    assert core_active.witness.deployment_state is DeploymentState.NATIVE_ACTIVE
    assert controller.current_stage(request) is OfflineCutoverStage.CORE_ACTIVE_EXTERNAL_PENDING
    with pytest.raises(PublicRuntimeStartupRefused):
        create_public_runtime(data_root, config)
    assert resolve_deployment_agreement(data_root=data_root, effective_profile=profile).mode is DeploymentResolutionMode.MAINTENANCE_ONLY

    # P7/P8: the selector is activated last.  REST, Spine, and MCP use the
    # one selector-owned native runtime and never touch a legacy MemoryGraph.
    active_selector = controller.activate_external_selector(request)
    assert active_selector.deployment_state is DeploymentState.NATIVE_ACTIVE
    assert controller.current_stage(request) is OfflineCutoverStage.NATIVE_ACTIVE
    legacy_calls, restore_legacy_memory_graph = _forbid_legacy_memory_graph(monkeypatch)
    app_module.configure_app_public_runtime(config)
    with TestClient(app_module.app) as client:
        assert client.get("/health").json()["public_memory_mode"] == "NATIVE"
        migrated = client.post("/agent/query", json={
            "workspace_id": "orchard", "agent_id": "aria", "query": "personal normal-service memory",
        })
        assert migrated.status_code == 200 and migrated.json()["results"]
        retrieved = client.post("/retrieve", json={
            "workspace_id": "orchard", "agent_id": "aria", "query": "research normal-service memory",
        })
        assert retrieved.status_code == 200
        first = client.post("/agent/ingest", headers={"Idempotency-Key": "b5-a5-native-loss"}, json={
            "workspace_id": "orchard", "agent_id": "aria", "text": "b5 a5 native public memory",
            "step": 91, "supplied_embedding": [1.0, 0.0, 0.0],
        })
        assert first.status_code == 200 and first.json()["stored"] is True
        runtime = app_module.fabric.runtime()
        spine = submit_task(
            SpineRequest("orchard", "aria", "query_memory", {"query": "b5 a5 native public memory"}),
            runtime,
            RequestContext("b5-a5-spine", TRUST_READ_ONLY, "orchard", "aria"),
        )
        assert spine.ok and spine.result["results"]
    first_payload = first.json()  # Simulated lost response: restart before retrying its key.
    reset_public_runtime_for_test(data_root)

    old_mcp_fabric, old_mcp_context = mcp_module._fabric, mcp_module._client_ctx
    mcp_module._fabric = None
    mcp_module._client_ctx = mcp_module.MCPClientContext(
        client_id="b5-a5-mcp", trust_tier=TRUST_READ_ONLY,
        default_workspace_id="orchard", default_agent_id="aria", session_id="b5-a5-mcp",
    )
    try:
        configure_public_runtime(data_root, config)
        mcp_query = mcp_module._spine_call("query_memory", {"query": "b5 a5 native public memory"})
        assert mcp_query["ok"] and mcp_query["result"]["results"]
    finally:
        mcp_module._close_runtime()
        mcp_module._fabric, mcp_module._client_ctx = old_mcp_fabric, old_mcp_context
        reset_public_runtime_for_test(data_root)

    # C7/P8 restart recovery is exact and cannot allocate a second cognition,
    # source object, reinforcement, or post-write side effect.
    app_module.configure_app_public_runtime(config)
    with TestClient(app_module.app) as client:
        native_fabric = app_module.fabric.runtime().cognition_fabric
        replay_process_calls = 0
        original_process = native_fabric.kernel.process

        def _count_replay_process(*args, **kwargs):
            nonlocal replay_process_calls
            replay_process_calls += 1
            return original_process(*args, **kwargs)

        monkeypatch.setattr(native_fabric.kernel, "process", _count_replay_process)
        replay = client.post("/agent/ingest", headers={"Idempotency-Key": "b5-a5-native-loss"}, json={
            "workspace_id": "orchard", "agent_id": "aria", "text": "b5 a5 native public memory",
            "step": 91, "supplied_embedding": [1.0, 0.0, 0.0],
        })
        assert replay.status_code == 200 and replay.json() == first_payload
        assert replay_process_calls == 0
    reset_public_runtime_for_test(data_root)
    restarted = create_public_runtime(data_root, config)
    try:
        assert restarted.mode is PublicRuntimeMode.NATIVE
        assert restarted.query("orchard", "aria", "b5 a5 native public memory", top_k=4)["results"]
    finally:
        close_public_runtime(data_root)
    second_lifecycle = create_public_runtime(data_root, config)
    try:
        assert second_lifecycle.mode is PublicRuntimeMode.NATIVE
        assert second_lifecycle.query("orchard", "aria", "b5 a5 native public memory", top_k=4)["results"]
    finally:
        close_public_runtime(data_root)
    assert legacy_calls == []
    assert _tree_digest(workspace_root) == legacy_before
    restore_legacy_memory_graph()

    # Post-active rollback is a hard refusal.  C8 then deliberately corrupts
    # the isolated selected core and the resolver refuses rather than guessing.
    with pytest.raises(OfflineCutoverRefused):
        controller.safe_pending_abort(request)
    core_path = Path(request.admission_request.native_core_database_path)
    core_path.rename(core_path.with_name("b5-a5-corrupt-selected-core.db"))
    assert resolve_deployment_agreement(data_root=data_root, effective_profile=profile).mode is DeploymentResolutionMode.REFUSED

    # A distinct never-active root proves the only allowed pending abort path.
    abort_request, abort_profile = _direct_request(tmp_path, monkeypatch, "pending-abort")
    abort_controller = OfflineCutoverController()
    abort_legacy = _tree_digest(abort_request.admission_request.legacy_workspace_root)
    abort_controller.prepare(abort_request)
    abort_controller.enter_external_pending(abort_request)
    abort_controller.admit_under_external_fence(abort_request)
    abort_controller.verify_completion(abort_request)
    abort_controller.enter_core_pending(abort_request)
    aborted = abort_controller.safe_pending_abort(abort_request)
    assert aborted.deployment_state is DeploymentState.LEGACY_ACTIVE
    assert resolve_deployment_agreement(
        data_root=abort_request.root, effective_profile=abort_profile,
    ).mode is DeploymentResolutionMode.LEGACY_PUBLIC
    assert _tree_digest(abort_request.admission_request.legacy_workspace_root) == abort_legacy
