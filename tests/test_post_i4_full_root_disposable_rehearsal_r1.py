"""Formal R1 disposable-root lifecycle rehearsal for the generalized root path."""

from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID

import pytest

from torment_service.public_runtime import (
    NativePublicOperationRefused,
    PublicRuntimeConfiguration,
    close_public_runtime,
    create_public_runtime,
)
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.deployment_core_maintenance import inspect_contained_core_deployment
from torment_service.substrate.deployment_selector import (
    activate_selector_native,
    resolve_deployment_agreement,
)
from torment_service.substrate.deployment_types import (
    DeploymentResolutionMode,
    DeploymentState,
    QualifiedDeploymentProfile,
)
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import (
    MaterializedRootScopePlan,
    RootNormalizationRequest,
    RootNormalizationScopeInput,
    RootRepresentationDisposition,
    RootScopeKey,
    RootScopeKind,
    WorkspaceNativeEmbedderIdentity,
    WorkspaceRootAdmissionPlan,
)
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.offline_cutover_controller import (
    OfflineCutoverController,
    OfflineCutoverRefused,
    OfflineCutoverStage,
    RootAdmissionMode,
    RootOfflineCutoverRequest,
)
from torment_service.substrate.production_native_owner import (
    NativeProductionResourceOwner,
    NativeProductionResourceOwnerError,
)
from torment_service.substrate.root_blocker5_binding import (
    RootWriterFreezeWitness,
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
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope
from torment_service.substrate.schema import create_schema

from test_substrate_root_normalization import (
    _DeterministicEmbedder,
    _b3a,
    _b4a,
    _description,
    _post_write_configuration,
    _stage_scope,
    _write_root_scope_evidence,
)


_REPOSITORY = Path(__file__).resolve().parents[1]
_REAL_ROOT = (_REPOSITORY / "data").resolve()
_SERVICE_URL = "http://127.0.0.1:8787"


class _DisposableDispositionAdapter:
    """The frozen disposition seam without a real external owner mutation."""

    def execute(self, **_kwargs: object) -> str:
        return "R1_DISPOSABLE_SYNTHETIC_NO_MUTATION"


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _runtime_scope(plan) -> NativeMemoryRuntimeScope:
    return NativeMemoryRuntimeScope(
        workspace_id=plan.workspace_id,
        scope_kind=plan.scope_kind,
        legacy_source_namespace_id=plan.legacy_source_namespace_id,
        identity_namespace_id=plan.target_identity_namespace_id,
        semantic_scope_id=plan.target_semantic_scope_id,
        agent_id=plan.agent_id,
        domain_id=plan.domain_id,
    )


def _create_root_profile(connection):
    identity_id = generate_native_id()
    scope_id = generate_native_id()
    idempotency_id = generate_native_id()
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(identity_id), "r1-root-profile-identity"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(scope_id), "r1-root-profile-scope"),
    )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency_id), "r1-root-profile-operations"),
    )
    NativeObjectService(connection).create_object(
        idempotency_namespace_id=idempotency_id,
        idempotency_key="r1-root-profile-generation",
        state=ObjectState(
            identity_id,
            scope_id,
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
    return current_root_profile_generation(connection)


def _write_disposable_public_shape(root: Path, workspace_id: str, domain_id: str) -> None:
    workspace = root / "workspaces" / workspace_id
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "workspace_meta.json").write_text("{}", encoding="utf-8")
    (workspace / "domains.json").write_text(
        json.dumps({"domains": [domain_id]}, sort_keys=True), encoding="utf-8",
    )
    (workspace / "domain_policies.json").write_text(
        json.dumps({"policies": {domain_id: {"auto_merge_motifs": False}}}, sort_keys=True),
        encoding="utf-8",
    )


def _write_disposable_agent_identity(root: Path, workspace_id: str, agent_id: str) -> None:
    """Provide an existing legacy identity before the one-way root rehearsal."""

    path = root / "workspaces" / workspace_id / "agents" / agent_id / "identity.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "seed": {},
            "overlay": {},
            "created_ts": 0,
            "updated_ts": 0,
        }, sort_keys=True),
        encoding="utf-8",
    )


def _build_disposable_root(
    tmp_path: Path,
    name: str,
    *,
    extra_private_in_north: bool = False,
) -> tuple[RootOfflineCutoverRequest, QualifiedDeploymentProfile]:
    root = (tmp_path / name).resolve()
    assert root != _REAL_ROOT
    assert _REAL_ROOT not in root.parents
    core_path = root / "substrate" / "cores" / "root-r1.db"
    core_path.parent.mkdir(parents=True)
    qualified = open_temporary_test_connection(core_path)
    try:
        connection = qualified.connection
        metadata = create_schema(connection)
        core_id = UUID(bytes=metadata.core_id)
        root_profile = _create_root_profile(connection)
        membership = RootScopeMembershipService(connection)
        entries = []
        inputs = []
        runtime_scopes = []
        workspace_plans = []
        all_plans = []
        for workspace_id in ("north", "south"):
            domain_id = "common-domain"
            _write_disposable_public_shape(root, workspace_id, domain_id)
            private_ids = ["same-agent"]
            if workspace_id == "north" and extra_private_in_north:
                private_ids.append("second-agent")
            private_scopes = []
            shared_scopes = []
            for agent_id in private_ids:
                _write_disposable_agent_identity(root, workspace_id, agent_id)
                key = RootScopeKey(workspace_id, RootScopeKind.PRIVATE, agent_id=agent_id)
                facts = _stage_scope(
                    connection, root, core_id,
                    workspace_id=workspace_id,
                    scope_key=key,
                    source_label=f"r1-{workspace_id}-{agent_id}",
                    vector_provider="st",
                    vector_model="BAAI/bge-small-en-v1.5",
                )
                facts = replace(facts, plan=replace(facts.plan, motif_domain_id=domain_id))
                runtime = _runtime_scope(facts.plan)
                membership.admit(
                    profile=root_profile,
                    runtime_scope=runtime,
                    witness=RootScopeMembershipWitness(
                        witness_id=f"r1:{workspace_id}:private:{agent_id}",
                        witness_digest=_digest(f"r1:{workspace_id}:private:{agent_id}"),
                        issuer_reference="post-i4-r1-disposable",
                        provenance_kind="QUALIFICATION_TEST",
                    ),
                    membership_identity_namespace_id=facts.plan.membership_identity_namespace_id,
                    idempotency_namespace_id=facts.plan.idempotency_namespace_id,
                    idempotency_key=f"r1-membership:{workspace_id}:private:{agent_id}",
                )
                entries.extend(_write_root_scope_evidence(root, key, has_memory=True, has_motif=False))
                private_scopes.append(MaterializedRootScopePlan(
                    key, RootRepresentationDisposition.TARGET_COMPATIBLE,
                ))
                inputs.append(RootNormalizationScopeInput(
                    key, facts.plan, facts.snapshot_id,
                    b3a_requests=(_b3a(facts, core_id, f"r1-b3a:{workspace_id}:{agent_id}"),),
                ))
                runtime_scopes.append(runtime)
                all_plans.append(facts.plan)
            shared_key = RootScopeKey(workspace_id, RootScopeKind.SHARED, domain_id=domain_id)
            shared_facts = _stage_scope(
                connection, root, core_id,
                workspace_id=workspace_id,
                scope_key=shared_key,
                source_label=f"r1-{workspace_id}-{domain_id}",
                vector_provider="st",
                vector_model="BAAI/bge-small-en-v1.5",
                motif_id=f"r1-{workspace_id}-motif",
                motif_members=[7],
            )
            shared_runtime = _runtime_scope(shared_facts.plan)
            membership.admit(
                profile=root_profile,
                runtime_scope=shared_runtime,
                witness=RootScopeMembershipWitness(
                    witness_id=f"r1:{workspace_id}:shared:{domain_id}",
                    witness_digest=_digest(f"r1:{workspace_id}:shared:{domain_id}"),
                    issuer_reference="post-i4-r1-disposable",
                    provenance_kind="QUALIFICATION_TEST",
                ),
                membership_identity_namespace_id=shared_facts.plan.membership_identity_namespace_id,
                idempotency_namespace_id=shared_facts.plan.idempotency_namespace_id,
                idempotency_key=f"r1-membership:{workspace_id}:shared:{domain_id}",
            )
            entries.extend(_write_root_scope_evidence(root, shared_key, has_memory=True, has_motif=True))
            shared_scopes.append(MaterializedRootScopePlan(
                shared_key, RootRepresentationDisposition.TARGET_COMPATIBLE,
            ))
            inputs.append(RootNormalizationScopeInput(
                shared_key, shared_facts.plan, shared_facts.snapshot_id,
                b3a_requests=(_b3a(shared_facts, core_id, f"r1-b3a:{workspace_id}:shared"),),
                b4a_requests=(_b4a(shared_facts, core_id, f"r1-b4a:{workspace_id}:shared"),),
            ))
            runtime_scopes.append(shared_runtime)
            all_plans.append(shared_facts.plan)
            workspace_plans.append(WorkspaceRootAdmissionPlan(
                workspace_id,
                private_materialized_scopes=tuple(private_scopes),
                shared_materialized_scopes=tuple(shared_scopes),
            ))
        description = replace(
            _description(root, entries, tuple(workspace_plans)),
            data_root_identity=f"post-i4-r1:{name}",
            operator_identity="post-i4-r1-disposable-operator",
        )
        lane = description.target_representation_lane
        profile = QualifiedDeploymentProfile(
            compression_enabled=False,
            deep_memory_enabled=False,
            representation_provider=lane.provider,
            representation_model=lane.model,
            representation_dimension=lane.dimension,
            admitted_scope_plan_digest=root_runtime_scope_plan_digest(tuple(all_plans), lane),
            external_owner_digest=description.external_owner_observation_digest,
        )
        normalization = RootNormalizationRequest(
            description=description,
            data_root=root,
            native_core_database_path=core_path,
            expected_native_core_id=core_id,
            scope_inputs=tuple(inputs),
            qualification_embedder_identity=WorkspaceNativeEmbedderIdentity(
                lane.provider, lane.model, lane.dimension,
            ),
            b3b_embedder=_DeterministicEmbedder(),
            post_write_configurations=tuple(
                _post_write_configuration(item.scope_plan)
                for item in inputs
                if item.scope_key.scope_kind is RootScopeKind.PRIVATE
            ),
        )
        request = RootOfflineCutoverRequest(
            data_root=root,
            description=description,
            normalization_request=normalization,
            effective_profile=profile,
            root_profile=root_profile,
            runtime_scopes=tuple(runtime_scopes),
            writer_freeze=RootWriterFreezeWitness(
                data_root_identity=description.data_root_identity,
                writer_freeze_operation_identity=f"r1-freeze:{name}",
                writer_evidence_digest=_digest(f"r1-writers-drained:{name}"),
            ),
            operator_cutover_key=f"post-i4-r1:{name}",
            admission_mode=RootAdmissionMode.SYNTHETIC_V1_COMPAT,
        )
    finally:
        qualified.close()
    return request, profile


def _service_environment(root: Path, profile: QualifiedDeploymentProfile) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update({
        "TORMENT_DATA_DIR": str(root),
        "TORMENT_DEPLOYMENT_PROFILE_JSON": json.dumps(asdict(profile), sort_keys=True),
        "TORMENT_EMBED_PROVIDER": "st",
        "TORMENT_EMBED_MODEL": "BAAI/bge-small-en-v1.5",
        "TORMENT_EMBED_DEVICE": "cpu",
        "TORMENT_AUTH_ENABLE": "0",
        "TORMENT_CHARACTER_ENABLE": "0",
        "TORMENT_CHECKPOINT_ENABLE": "0",
        "TORMENT_HIVEMIND_ENABLE": "0",
        "TORMENT_THINKING_ADVISORY": "0",
        "TORMENT_SRG_COGNITION": "0",
        "TORMENT_REINFORCE_SIM_THRESHOLD": "0",
        "TORMENT_ID_ANCHOR_MIN_COUNT": "1000",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
    })
    environment.pop("TORMENT_ADMISSION_DESCRIPTOR_PATH", None)
    return environment


def _stop_service(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=15)


def _start_service(environment: dict[str, str]) -> subprocess.Popen[str]:
    process = subprocess.Popen(
        [sys.executable, "-m", "torment_service"],
        cwd=_REPOSITORY,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.monotonic() + 35
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else ""
            raise AssertionError(f"r1 service exited before health: {output[-1000:]}")
        try:
            with urlopen(f"{_SERVICE_URL}/health", timeout=1) as response:
                if response.status == 200:
                    return process
        except OSError:
            time.sleep(0.15)
    _stop_service(process)
    raise AssertionError("r1 service did not become healthy")


def _request(
    method: str,
    path: str,
    payload: dict[str, object] | None = None,
    *,
    idempotency_key: str | None = None,
) -> tuple[int, object]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    request = Request(
        f"{_SERVICE_URL}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(error_body)
        except json.JSONDecodeError:
            return exc.code, error_body


def _activate_root_to_p7(
    request: RootOfflineCutoverRequest,
) -> tuple[OfflineCutoverController, object, object]:
    controller = OfflineCutoverController()
    prepared = controller.prepare_root(request)
    assert prepared.stage is OfflineCutoverStage.PREPARED
    pending = controller.enter_compat_root_external_pending(request)
    assert pending.stage is OfflineCutoverStage.EXTERNAL_PENDING
    normalization = controller.normalize_root_under_external_fence(request)
    assert normalization.root_normalization_complete and normalization.root_normalization_ready
    verified = controller.verify_root_completion(request, normalization)
    controller.enter_root_core_pending(request, normalization)
    # R1: completion exists but P6 has not occurred.  A new controller must
    # recover the pending authority without making the core active.
    controller = OfflineCutoverController()
    assert controller.root_current_stage(request) is OfflineCutoverStage.CORE_PENDING
    before_p6 = inspect_contained_core_deployment(
        data_root=request.root, core_relative_path=request.core_relative_path,
    )
    assert before_p6.ever_active is False
    assert pending.selector_state is not None
    assert pending.selector_state.deployment_state is DeploymentState.CUTOVER_PENDING
    active = controller.activate_root_core(request, normalization)
    assert active.witness.deployment_state is DeploymentState.NATIVE_ACTIVE
    # R2: core-active/external-pending remains maintenance-only after a fresh
    # controller recovers it; it is past the reversible point.
    controller = OfflineCutoverController()
    assert controller.root_current_stage(request) is OfflineCutoverStage.CORE_ACTIVE_EXTERNAL_PENDING
    with pytest.raises(OfflineCutoverRefused):
        controller.safe_root_pending_abort(request)
    receipt = controller.execute_root_disposition_plan(
        request, normalization, adapter=_DisposableDispositionAdapter(),
    )
    # R3: the durable receipt and frozen plan are recovered by a third
    # controller before selector activation.
    controller = OfflineCutoverController()
    assert controller.root_current_stage(request) is OfflineCutoverStage.CORE_ACTIVE_EXTERNAL_PENDING
    assert controller.execute_root_disposition_plan(
        request, normalization, adapter=_DisposableDispositionAdapter(),
    ) == receipt
    with pytest.raises(Exception):
        activate_selector_native(
            data_root=request.root,
            core_relative_path=request.core_relative_path,
            core_result=active,
            expected_generation=pending.selector_state.generation,
            operation_key=f"{request.operator_cutover_key}:wrong-p7-receipt",
            disposition_execution_receipt_digest=_digest("wrong-r1-receipt"),
        )
    selector = controller.activate_root_external_selector(request, normalization)
    assert selector.deployment_state is DeploymentState.NATIVE_ACTIVE
    assert verified.completion_verification is not None
    return controller, normalization, verified


def test_r1_full_root_disposable_lifecycle_service_restart_and_legacy_source_independence(
    tmp_path: Path,
) -> None:
    request, profile = _build_disposable_root(tmp_path, "r1-primary")
    assert request.root != _REAL_ROOT and _REAL_ROOT not in request.root.parents
    controller, normalization, verified = _activate_root_to_p7(request)
    assert controller.root_current_stage(request) is OfflineCutoverStage.NATIVE_ACTIVE
    agreement = resolve_deployment_agreement(data_root=request.root, effective_profile=profile)
    assert agreement.mode is DeploymentResolutionMode.NATIVE_AGREEMENT
    assert verified.envelope.digest == verified.completion_verification.envelope.digest
    assert profile.admitted_scope_plan_digest == verified.envelope.payload()["root_runtime_scope_plan_digest"]
    owner = NativeProductionResourceOwner.from_native_agreement(
        data_root=request.root, effective_profile=profile, agreement=agreement,
    )
    try:
        north_runtime = owner._recover_active_runtime(workspace_id="north")
        north_private = next(
            lane["plan"] for lane in north_runtime.descriptor.payload["lanes"]
            if lane["plan"]["scope_kind"] == "PRIVATE_AGENT"
        )
        assert north_private["agent_id"] == "same-agent"
        assert north_private["motif_domain_id"] == "common-domain"
    finally:
        owner.close()
    direct_runtime = create_public_runtime(
        request.root, PublicRuntimeConfiguration(effective_profile=profile),
    )
    try:
        assert direct_runtime.get_workspace("north").domains == ("common-domain",)
        assert direct_runtime.create_agent("north", "same-agent", seed=None).agent_id == "same-agent"
        assert direct_runtime.create_agent("south", "same-agent", seed=None).agent_id == "same-agent"
        with pytest.raises(NativePublicOperationRefused, match="not admitted"):
            direct_runtime.create_agent("north", "unadmitted-agent", seed=None)
    finally:
        close_public_runtime(request.root)

    environment = _service_environment(request.root, profile)
    assert Path(environment["TORMENT_DATA_DIR"]).resolve() == request.root
    assert "TORMENT_ADMISSION_DESCRIPTOR_PATH" not in environment
    service = _start_service(environment)
    try:
        health_status, health = _request("GET", "/health")
        assert health_status == 200 and health["public_memory_mode"] == "NATIVE"
        for workspace_id in ("north", "south"):
            status, workspace = _request("GET", f"/workspace/{workspace_id}/domains")
            assert status == 409
            assert workspace["detail"] == "native public route is refused before legacy-memory effect"
            status, created = _request("POST", "/agent/create", {
                "workspace_id": workspace_id, "agent_id": "same-agent", "seed": None,
            })
            assert status == 409
            assert created["detail"] == "native public route is refused before legacy-memory effect"
            text = f"r1-{workspace_id}-private-isolated-memory"
            status, ingested = _request("POST", "/agent/ingest", {
                "workspace_id": workspace_id,
                "agent_id": "same-agent",
                "text": text,
                "step": 1,
                "domain_id": "common-domain",
                "scope": "private",
                "supplied_embedding": [1.0] + [0.0] * 383,
            }, idempotency_key=f"r1-{workspace_id}-ingest")
            assert status == 200 and ingested["stored"] is True, ingested
            status, queried = _request("POST", "/agent/query", {
                "workspace_id": workspace_id,
                "agent_id": "same-agent",
                "query": text,
                "domain_id": "common-domain",
            })
            assert status == 200 and queried["results"]
            assert text in json.dumps(queried["results"], sort_keys=True)
        status, south_query = _request("POST", "/agent/query", {
            "workspace_id": "south",
            "agent_id": "same-agent",
            "query": "r1-north-private-isolated-memory",
            "domain_id": "common-domain",
        })
        assert status == 200
        assert "r1-north-private-isolated-memory" not in json.dumps(south_query, sort_keys=True)
        assert _request("POST", "/agent/trace", {
            "workspace_id": "north", "agent_id": "same-agent", "query": "r1 trace",
        })[0] != 200
        status, unadmitted = _request("POST", "/agent/ingest", {
            "workspace_id": "north", "agent_id": "unadmitted-agent", "text": "refuse",
            "step": 2, "domain_id": "common-domain", "scope": "private",
            "supplied_embedding": [1.0] + [0.0] * 383,
        }, idempotency_key="r1-unadmitted-ingest")
        assert status != 200
        assert "admitted" in json.dumps(unadmitted, sort_keys=True)
        assert _request("POST", "/memory/chain", {
            "workspace_id": "north", "agent_id": "same-agent", "eid": 7,
            "scope": "private", "domain_id": "common-domain",
        })[0] != 200
    finally:
        _stop_service(service)

    service = _start_service(environment)
    try:
        assert _request("GET", "/health")[1]["public_memory_mode"] == "NATIVE"
        assert _request("POST", "/agent/query", {
            "workspace_id": "north", "agent_id": "same-agent",
            "query": "r1-north-private-isolated-memory", "domain_id": "common-domain",
        })[0] == 200
    finally:
        _stop_service(service)

    legacy_layout = request.root / "workspaces"
    hidden_layout = request.root / "r1-legacy-source-hidden"
    legacy_layout.rename(hidden_layout)
    assert not legacy_layout.exists() and hidden_layout.is_dir()
    service = _start_service(environment)
    try:
        assert _request("GET", "/health")[1]["public_memory_mode"] == "NATIVE"
    finally:
        _stop_service(service)
    assert not legacy_layout.exists()
    owner = NativeProductionResourceOwner.from_native_agreement(
        data_root=request.root,
        effective_profile=profile,
        agreement=resolve_deployment_agreement(data_root=request.root, effective_profile=profile),
    )
    owner.close()


def test_r1_preactive_abort_census_and_manifest_refusal_arms(tmp_path: Path) -> None:
    abort_request, abort_profile = _build_disposable_root(tmp_path, "r1-preactive-abort")
    abort_controller = OfflineCutoverController()
    abort_controller.prepare_root(abort_request)
    abort_controller.enter_compat_root_external_pending(abort_request)
    abort_normalization = abort_controller.normalize_root_under_external_fence(abort_request)
    abort_controller.verify_root_completion(abort_request, abort_normalization)
    abort_controller.enter_root_core_pending(abort_request, abort_normalization)
    assert abort_controller.safe_root_pending_abort(abort_request).deployment_state is DeploymentState.LEGACY_ACTIVE
    aborted = inspect_contained_core_deployment(
        data_root=abort_request.root, core_relative_path=abort_request.core_relative_path,
    )
    assert aborted.ever_active is False
    assert aborted.deployment_state is DeploymentState.LEGACY_ACTIVE
    assert resolve_deployment_agreement(
        data_root=abort_request.root, effective_profile=abort_profile,
    ).mode is DeploymentResolutionMode.LEGACY_PUBLIC

    census_request, census_profile = _build_disposable_root(tmp_path, "r1-census-mismatch")
    unrelated = census_request.root / "unrelated-co-located.txt"
    unrelated.write_text("inert", encoding="utf-8")
    OfflineCutoverController().prepare_root(census_request)
    undeclared = census_request.root / "workspaces" / "north" / "agents" / "undeclared" / "private"
    undeclared.mkdir(parents=True)
    with pytest.raises(OfflineCutoverRefused):
        OfflineCutoverController().prepare_root(census_request)
    census_core = inspect_contained_core_deployment(
        data_root=census_request.root, core_relative_path=census_request.core_relative_path,
    )
    assert census_core.ever_active is False
    assert resolve_deployment_agreement(
        data_root=census_request.root, effective_profile=census_profile,
    ).mode is DeploymentResolutionMode.LEGACY_PUBLIC

    drift_request, _drift_profile = _build_disposable_root(tmp_path, "r1-manifest-drift")
    drift_controller = OfflineCutoverController()
    drift_controller.prepare_root(drift_request)
    drift_controller.enter_compat_root_external_pending(drift_request)
    drift_normalization = drift_controller.normalize_root_under_external_fence(drift_request)
    drift_controller.verify_root_completion(drift_request, drift_normalization)
    drift_controller.enter_root_core_pending(drift_request, drift_normalization)
    source = drift_request.root / "workspaces" / "north" / "agents" / "same-agent" / "private" / "nodes.jsonl"
    source.write_text("manifest drift", encoding="utf-8")
    with pytest.raises(OfflineCutoverRefused):
        drift_controller.activate_root_core(drift_request, drift_normalization)
    drift_core = inspect_contained_core_deployment(
        data_root=drift_request.root, core_relative_path=drift_request.core_relative_path,
    )
    assert drift_core.ever_active is False


def test_r1_extra_private_lane_is_lawful_when_shared_lane_remains_admitted(tmp_path: Path) -> None:
    request, profile = _build_disposable_root(
        tmp_path, "r1-negative-public-topology", extra_private_in_north=True,
    )
    _controller, _normalization, _verified = _activate_root_to_p7(request)
    agreement = resolve_deployment_agreement(data_root=request.root, effective_profile=profile)
    owner = NativeProductionResourceOwner.from_native_agreement(
        data_root=request.root, effective_profile=profile, agreement=agreement,
    )
    try:
        assert owner.authority_facts.core_id == request.native_staging_core_id
    finally:
        owner.close()
