"""Bounded real-root administration for the corrective P1/P2 successor.

This runner is deliberately fail-closed.  Its default mode is read-only; the
only mutating path requires ``--apply`` and invokes the qualified selector
supersession, P1 bootstrap, and real-root-v2 P2 controller seams.  It never
calls a P3/P4/P5/P6/P7 API.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from uuid import UUID, uuid4

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from torment_service.substrate.deployment_core_maintenance import (
    inspect_contained_core_deployment,
    read_root_admission_envelope_record,
    read_root_writer_freeze_evidence_record,
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
from torment_service.substrate.ids import native_id_to_bytes
from torment_service.substrate.migration import RootScopeKey, RootScopeKind
from torment_service.substrate.migration.root_normalization import RootP2ScopePlanCarrier
from torment_service.substrate.offline_cutover_controller import (
    OfflineCutoverController,
    RootExternalPendingInertAbortRequest,
    RootOfflineCutoverRequest,
)
from torment_service.substrate.real_root_staging_bootstrap import (
    P1StagingBootstrapRequest,
    RootProfileBootstrap,
    RuntimeScopeBootstrap,
    bootstrap_real_root_staging,
)
from torment_service.substrate.real_root_typed_evidence import (
    DirectPhase9BNamespaceBinding,
    build_real_direct_admission_source_adapter,
)
from torment_service.substrate.root_blocker5_binding import RootWriterFreezeWitness, root_runtime_scope_plan_digest
from torment_service.substrate.root_profile import current_root_profile_generation
from torment_service.substrate.root_scope_membership import RootScopeMembershipReader
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope
from torment_service.substrate.writer_freeze_evidence import (
    ListenerObservation,
    ListenerObservationResult,
    RootWriterClass,
    RootWriterFreezeRecheck,
    WriterObservationResult,
    WriterProcessObservation,
    observe_root_clone_repair_jobs,
    root_writer_freeze_evidence_payload_from_payload,
    snapshot_root_workspaces,
)


EXPECTED_HEAD = "7bc367c936ab892e6f4633d957382b98cc83d1a1"
HISTORICAL_CORE_ID = UUID("0e9cb4b7-cf57-49fa-b60a-0e5a25f9d288")
HISTORICAL_CORE_NAME = f"root-native-staging-{HISTORICAL_CORE_ID}.db"
ENVELOPE_C_DIGEST = "d97c0545a538efca9657119abac133efc010bc41191b35f9e74ce9885f79b34b"
EXPECTED_SCOPE_COUNT = 154
RUN_ID = "real-root-corrective-p1-p2-20260909"


class CorrectiveAdministrationRefused(RuntimeError):
    """The real root no longer matches the exact, authorized predecessor."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CorrectiveAdministrationRefused(message)


def _scope_key(plan: object) -> RootScopeKey:
    if getattr(plan, "scope_kind") == "PRIVATE_AGENT":
        return RootScopeKey(
            getattr(plan, "workspace_id"), RootScopeKind.PRIVATE, agent_id=getattr(plan, "agent_id"),
        )
    if getattr(plan, "scope_kind") == "SHARED_DOMAIN":
        return RootScopeKey(
            getattr(plan, "workspace_id"), RootScopeKind.SHARED, domain_id=getattr(plan, "domain_id"),
        )
    raise CorrectiveAdministrationRefused("historical P2 scope kind is unsupported")


def _namespace_key(
    connection: sqlite3.Connection,
    table: str,
    id_column: str,
    key_column: str,
    value: UUID,
) -> str:
    row = connection.execute(
        f"SELECT {key_column} FROM {table} WHERE {id_column}=?",
        (native_id_to_bytes(value),),
    ).fetchone()
    if row is None or not isinstance(row[0], str) or not row[0]:
        raise CorrectiveAdministrationRefused(f"historical namespace key missing from {table}")
    return row[0]


def _read_historical_memberships(core_path: Path) -> dict[RootScopeKey, object]:
    connection = sqlite3.connect(f"file:{core_path.as_posix()}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        profile = current_root_profile_generation(connection)
        _require(profile.core_id == HISTORICAL_CORE_ID, "historical profile names another core")
        memberships = {
            record.runtime_key.scope_key: record
            for record in RootScopeMembershipReader(connection).recover(profile)
        }
        return memberships
    finally:
        connection.close()


def _historical_namespace_keys(core_path: Path, plans: tuple[object, ...]) -> dict[tuple[str, UUID], str]:
    connection = sqlite3.connect(f"file:{core_path.as_posix()}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        keys: dict[tuple[str, UUID], str] = {}
        for plan in plans:
            values = (
                ("identity", "identity_namespaces", "identity_namespace_id", "namespace_key", plan.target_identity_namespace_id),
                ("semantic", "semantic_scopes", "semantic_scope_id", "scope_key", plan.target_semantic_scope_id),
                ("legacy", "legacy_source_namespaces", "legacy_source_namespace_id", "source_key", plan.legacy_source_namespace_id),
                ("membership", "identity_namespaces", "identity_namespace_id", "namespace_key", plan.membership_identity_namespace_id),
                ("idempotency", "idempotency_namespaces", "idempotency_namespace_id", "namespace_key", plan.idempotency_namespace_id),
            )
            for family, table, id_column, key_column, value in values:
                key = (family, value)
                observed = _namespace_key(connection, table, id_column, key_column, value)
                previous = keys.setdefault(key, observed)
                _require(previous == observed, "historical namespace id maps to conflicting keys")
        return keys
    finally:
        connection.close()


def _alias_identity(scope: RootScopeKey) -> tuple[UUID, str]:
    value = uuid4()
    key = _alias_key(scope)
    _require(len(key) <= 240, "corrected motif alias namespace key is too long")
    return value, key


def _alias_key(scope: RootScopeKey) -> str:
    return f"{RUN_ID}:motif-alias:{scope.canonical_key}"


def _profile_from_payload(payload: dict[str, object]) -> QualifiedDeploymentProfile:
    return QualifiedDeploymentProfile(
        compression_enabled=payload["compression_enabled"],
        deep_memory_enabled=payload["deep_memory_enabled"],
        representation_provider=payload["representation_provider"],
        representation_model=payload["representation_model"],
        representation_dimension=payload["representation_dimension"],
        admitted_scope_plan_digest=payload["admitted_scope_plan_digest"],
        external_owner_digest=payload["external_owner_digest"],
    )


def _fresh_writer_recheck(root: Path, external_owner_digest: str) -> tuple[RootWriterFreezeRecheck, int, int]:
    census = subprocess.run(
        [
            "powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Compress",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    rows = json.loads(census.stdout) if census.stdout.strip() else []
    if isinstance(rows, dict):
        rows = [rows]
    _require(isinstance(rows, list), "Windows process census did not return a list")
    root_token = str(root).casefold()
    root_target_processes = [
        item for item in rows
        if isinstance(item, dict)
        and isinstance(item.get("CommandLine"), str)
        and root_token in item["CommandLine"].casefold()
    ]
    _require(not root_target_processes, "root-target process census is not empty")

    listeners = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"], check=True, capture_output=True, text=True,
    )
    listener_count = sum(
        "127.0.0.1:8787" in line.casefold() for line in listeners.stdout.splitlines()
    )
    _require(listener_count == 0, "127.0.0.1:8787 listener is present")

    mechanism = "WINDOWS_CIM_ROOT_TARGET_CENSUS_V1"
    observations = tuple(
        WriterProcessObservation(
            writer_class=writer_class,
            observation_mechanism=mechanism,
            result=WriterObservationResult.ABSENT,
        )
        for writer_class in RootWriterClass
    )
    return (
        RootWriterFreezeRecheck(
            covered_writer_classes=observations,
            listener_observation=ListenerObservation(
                listener_identity="127.0.0.1:8787",
                observation_mechanism="WINDOWS_NETSTAT_ANO_127_0_0_1_8787_V1",
                result=ListenerObservationResult.ABSENT,
            ),
            job_observation=observe_root_clone_repair_jobs(data_root=root),
            external_owner_observation_digest=external_owner_digest,
        ),
        len(root_target_processes),
        listener_count,
    )


def _is_schema_only_failed_p1_core(root: Path, core_path: Path) -> bool:
    inspection = inspect_contained_core_deployment(data_root=root, core_relative_path=core_path.name)
    if not (
        inspection.core_id is not None
        and inspection.core_role == "STAGING"
        and inspection.deployment_state is DeploymentState.LEGACY_ACTIVE
        and inspection.witness is None
        and not inspection.ever_active
    ):
        return False
    connection = sqlite3.connect(f"file:{core_path.as_posix()}?mode=ro", uri=True)
    try:
        tables = (
            "identity_namespaces", "semantic_scopes", "legacy_source_namespaces",
            "idempotency_namespaces", "objects", "object_revisions", "operations",
            "maintenance_events", "legacy_admission_records", "legacy_artifact_records",
        )
        return all(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0 for table in tables)
    finally:
        connection.close()


def _preflight(root: Path, *, resume_after_retained_p1_refusal: bool) -> dict[str, object]:
    historical_core = root / "substrate" / "cores" / HISTORICAL_CORE_NAME
    _require(historical_core.is_file(), "historical core is missing")
    core_files = tuple(sorted((root / "substrate" / "cores").glob("*.db")))
    retained_failed_p1_core: Path | None = None
    if resume_after_retained_p1_refusal:
        retained = tuple(item for item in core_files if item != historical_core)
        _require(len(retained) == 1, "resume requires exactly one retained failed P1 core")
        _require(_is_schema_only_failed_p1_core(root, retained[0]), "retained P1 core is not schema-only inert residue")
        retained_failed_p1_core = retained[0]
    else:
        _require(core_files == (historical_core,), "unexpected second native core is present")
    selector = read_selector_state(data_root=root)
    if resume_after_retained_p1_refusal:
        _require(
            selector.generation == 6
            and selector.deployment_state is DeploymentState.LEGACY_ACTIVE
            and selector.core_id is None
            and selector.core_relative_path is None
            and selector.descriptor_digest is None,
            "resume selector is not the exact post-abort legacy state",
        )
    else:
        _require(selector.deployment_state is DeploymentState.CUTOVER_PENDING, "selector is not stale CUTOVER_PENDING")
        _require(selector.generation == 5, "selector generation is not the expected predecessor generation")
        _require(selector.core_id == HISTORICAL_CORE_ID, "selector names another staging core")
        _require(selector.core_relative_path == HISTORICAL_CORE_NAME, "selector names another core path")
        _require(selector.descriptor_digest == ENVELOPE_C_DIGEST, "selector does not name Envelope C")
    inspection = inspect_contained_core_deployment(data_root=root, core_relative_path=HISTORICAL_CORE_NAME)
    _require(
        inspection.core_id == HISTORICAL_CORE_ID
        and inspection.core_role == "STAGING"
        and inspection.deployment_state is DeploymentState.LEGACY_ACTIVE
        and inspection.witness is None
        and not inspection.ever_active,
        "historical core is not the expected inert predecessor",
    )
    record_c = read_root_admission_envelope_record(
        data_root=root,
        core_relative_path=HISTORICAL_CORE_NAME,
        root_admission_envelope_digest=ENVELOPE_C_DIGEST,
    )
    _require(record_c is not None and record_c.envelope_digest == ENVELOPE_C_DIGEST, "Envelope C is missing")
    writer_record_c = read_root_writer_freeze_evidence_record(
        data_root=root,
        core_relative_path=HISTORICAL_CORE_NAME,
        root_admission_envelope_digest=ENVELOPE_C_DIGEST,
    )
    _require(writer_record_c is not None, "Envelope C writer-freeze evidence is missing")
    profile_c = _profile_from_payload(record_c.effective_profile_payload)
    if resume_after_retained_p1_refusal:
        _require(selector.profile_digest is None, "resume selector unexpectedly retains a profile")
    else:
        _require(selector.profile_digest == profile_c.digest, "selector profile does not bind Envelope C")
    agreement = resolve_deployment_agreement(data_root=root, effective_profile=profile_c)
    expected_mode = (
        DeploymentResolutionMode.LEGACY_PUBLIC
        if resume_after_retained_p1_refusal
        else DeploymentResolutionMode.MAINTENANCE_ONLY
    )
    _require(agreement.mode is expected_mode, "public API posture is unexpected")
    plans = record_c.runtime_scope_plans
    _require(len(plans) == EXPECTED_SCOPE_COUNT, "Envelope C does not carry 154 scope plans")
    _require(all(plan.motif_alias_namespace_id == plan.legacy_source_namespace_id for plan in plans), "Envelope C is not the expected collapsed-alias predecessor")
    snapshot = snapshot_root_workspaces(data_root=root)
    payload_c = root_writer_freeze_evidence_payload_from_payload(writer_record_c.writer_freeze_evidence_payload)
    _require(snapshot == payload_c.source_tree_snapshot, "current workspace snapshot differs from Envelope C freeze")
    memberships = _read_historical_memberships(historical_core)
    _require(len(memberships) == EXPECTED_SCOPE_COUNT, "historical P1 membership topology is not 154 scopes")
    _require(
        set(memberships) == {_scope_key(plan) for plan in plans},
        "historical P1 membership keys disagree with Envelope C",
    )
    namespace_keys = _historical_namespace_keys(historical_core, plans)
    return {
        "historical_core": historical_core,
        "historical_core_sha256": _sha256(historical_core),
        "record_c": record_c,
        "writer_record_c": writer_record_c,
        "profile_c": profile_c,
        "plans": plans,
        "memberships": memberships,
        "namespace_keys": namespace_keys,
        "workspace_snapshot": snapshot,
        "nodes_sha256": _sha256(root / "nodes.jsonl"),
        "embeddings_sha256": _sha256(root / "emb_1.npy"),
        "retained_failed_p1_core": retained_failed_p1_core,
    }


def _prepare_successor(root: Path, preflight: dict[str, object], core_id: UUID):
    plans = preflight["plans"]
    bindings = tuple(
        DirectPhase9BNamespaceBinding(
            _scope_key(plan), plan.legacy_source_namespace_id, plan.target_identity_namespace_id,
        )
        for plan in plans
        if plan.scope_kind == "PRIVATE_AGENT"
        and plan.workspace_id in {"ws3", "ws4", "ws5"}
        and plan.agent_id == "a1"
    )
    _require(len(bindings) == 3, "qualified Phase-9B binding set is incomplete")
    writer_payload = root_writer_freeze_evidence_payload_from_payload(
        preflight["writer_record_c"].writer_freeze_evidence_payload,
    )
    adapter = build_real_direct_admission_source_adapter(
        data_root_identity=writer_payload.data_root_identity,
        operator_identity=writer_payload.operator_identity,
        direct_phase9b_namespace_bindings=bindings,
    )
    prepared = adapter.prepare_direct_admission_source(data_root=root)
    _require(
        sum(len(workspace.runtime_scopes) for workspace in prepared.description.workspace_plans)
        == EXPECTED_SCOPE_COUNT,
        "current direct root topology is not 154 scopes",
    )
    corrected: list[object] = []
    runtime_bootstraps: list[RuntimeScopeBootstrap] = []
    runtime_scopes: list[NativeMemoryRuntimeScope] = []
    memberships = preflight["memberships"]
    namespace_keys = preflight["namespace_keys"]
    for plan in plans:
        scope = _scope_key(plan)
        alias_id, alias_key = _alias_identity(scope)
        _require(alias_id != plan.legacy_source_namespace_id, "corrected motif alias id collides with legacy source")
        corrected_plan = replace(plan, motif_alias_namespace_id=alias_id)
        corrected.append(corrected_plan)
        runtime_scope = NativeMemoryRuntimeScope(
            workspace_id=plan.workspace_id,
            scope_kind=plan.scope_kind,
            legacy_source_namespace_id=plan.legacy_source_namespace_id,
            identity_namespace_id=plan.target_identity_namespace_id,
            semantic_scope_id=plan.target_semantic_scope_id,
            agent_id=plan.agent_id,
            domain_id=plan.domain_id,
        )
        membership = memberships[scope]
        runtime_scopes.append(runtime_scope)
        runtime_bootstraps.append(RuntimeScopeBootstrap(
            runtime_scope=runtime_scope,
            identity_namespace_key=namespace_keys[("identity", plan.target_identity_namespace_id)],
            semantic_scope_key=namespace_keys[("semantic", plan.target_semantic_scope_id)],
            legacy_source_namespace_key=namespace_keys[("legacy", plan.legacy_source_namespace_id)],
            motif_alias_namespace_id=alias_id,
            motif_alias_namespace_key=alias_key,
            membership_identity_namespace_id=plan.membership_identity_namespace_id,
            membership_identity_namespace_key=namespace_keys[("membership", plan.membership_identity_namespace_id)],
            idempotency_namespace_id=plan.idempotency_namespace_id,
            idempotency_namespace_key=namespace_keys[("idempotency", plan.idempotency_namespace_id)],
            idempotency_key=f"{RUN_ID}:membership:{scope.canonical_key}",
            membership_witness=membership.witness,
        ))
    corrected_plans = tuple(corrected)
    _require(len({plan.motif_alias_namespace_id for plan in corrected_plans}) == EXPECTED_SCOPE_COUNT, "corrected motif alias ids collide")
    carrier = RootP2ScopePlanCarrier(
        description=prepared.description,
        data_root=root,
        native_core_database_path=root / "substrate" / "cores" / f"root-native-staging-{core_id}.db",
        expected_native_core_id=core_id,
        runtime_scope_plans=corrected_plans,
    )
    profile = QualifiedDeploymentProfile(
        compression_enabled=False,
        deep_memory_enabled=False,
        representation_provider=prepared.description.target_representation_lane.provider,
        representation_model=prepared.description.target_representation_lane.model,
        representation_dimension=prepared.description.target_representation_lane.dimension,
        admitted_scope_plan_digest=root_runtime_scope_plan_digest(
            corrected_plans, prepared.description.target_representation_lane,
        ),
        external_owner_digest=prepared.description.external_owner_observation_digest,
    )
    root_profile = RootProfileBootstrap(
        profile_object_id=uuid4(),
        profile_generation=1,
        identity_namespace_id=uuid4(),
        identity_namespace_key=f"{RUN_ID}:root-profile-identity:{core_id}",
        semantic_scope_id=uuid4(),
        semantic_scope_key=f"{RUN_ID}:root-profile-semantic:{core_id}",
        idempotency_namespace_id=uuid4(),
        idempotency_namespace_key=f"{RUN_ID}:root-profile-idempotency:{core_id}",
        idempotency_key=f"{RUN_ID}:root-profile-generation",
    )
    p1_request = P1StagingBootstrapRequest(
        data_root=root,
        native_core_database_path=carrier.native_core_database_path,
        core_id=core_id,
        root_profile=root_profile,
        runtime_scopes=tuple(runtime_bootstraps),
    )
    return prepared, corrected_plans, tuple(runtime_scopes), profile, carrier, p1_request


def _verify_unchanged_predecessor(root: Path, preflight: dict[str, object]) -> None:
    historical_core = preflight["historical_core"]
    _require(_sha256(historical_core) == preflight["historical_core_sha256"], "historical core bytes changed")
    record_c = read_root_admission_envelope_record(
        data_root=root,
        core_relative_path=HISTORICAL_CORE_NAME,
        root_admission_envelope_digest=ENVELOPE_C_DIGEST,
    )
    _require(record_c is not None and record_c.envelope_digest == ENVELOPE_C_DIGEST, "Envelope C changed")
    _require(snapshot_root_workspaces(data_root=root) == preflight["workspace_snapshot"], "workspace source changed")
    _require(_sha256(root / "nodes.jsonl") == preflight["nodes_sha256"], "top-level nodes source changed")
    _require(_sha256(root / "emb_1.npy") == preflight["embeddings_sha256"], "top-level embeddings source changed")


def run(*, apply: bool, resume_after_retained_p1_refusal: bool = False) -> dict[str, object]:
    root = Path("data").resolve()
    _require(root.is_dir(), "real data root is missing")
    preflight = _preflight(root, resume_after_retained_p1_refusal=resume_after_retained_p1_refusal)
    corrected_core_id = uuid4()
    prepared, corrected_plans, runtime_scopes, profile_d, carrier, p1_request = _prepare_successor(
        root, preflight, corrected_core_id,
    )
    result: dict[str, object] = {
        "mode": "APPLY" if apply else "DRY_RUN",
        "historical_core_id": str(HISTORICAL_CORE_ID),
        "historical_core_sha256": preflight["historical_core_sha256"],
        "envelope_c_digest": ENVELOPE_C_DIGEST,
        "initial_selector_state": "LEGACY_ACTIVE" if resume_after_retained_p1_refusal else "CUTOVER_PENDING",
        "initial_public_api_posture": "LEGACY_PUBLIC" if resume_after_retained_p1_refusal else "MAINTENANCE_ONLY",
        "current_scope_count": len(corrected_plans),
        "corrected_core_id": str(corrected_core_id),
        "corrected_core_path": str(carrier.native_core_database_path),
        "corrected_scope_plan_digest": profile_d.admitted_scope_plan_digest,
        "corrected_description_digest": prepared.description.identity_digest,
        "retained_failed_p1_core": (
            str(preflight["retained_failed_p1_core"])
            if preflight["retained_failed_p1_core"] is not None else None
        ),
    }
    if not apply:
        return result

    controller = OfflineCutoverController()
    if not resume_after_retained_p1_refusal:
        controller.supersede_root_external_pending_pre_p5(RootExternalPendingInertAbortRequest(
            data_root=root,
            core_relative_path=HISTORICAL_CORE_NAME,
            expected_selector_generation=5,
            expected_root_admission_envelope_digest=ENVELOPE_C_DIGEST,
            effective_profile=preflight["profile_c"],
            operation_key=f"{RUN_ID}:pre-p5-supersede",
        ))
    post_abort = resolve_deployment_agreement(data_root=root, effective_profile=preflight["profile_c"])
    _require(post_abort.mode is DeploymentResolutionMode.LEGACY_PUBLIC, "safe pre-P5 abort did not restore legacy authority")
    _verify_unchanged_predecessor(root, preflight)

    p1_result = bootstrap_real_root_staging(p1_request)
    _require(p1_result.core_id == corrected_core_id and len(p1_result.memberships) == EXPECTED_SCOPE_COUNT, "P1 result disagrees")
    corrected_inspection = inspect_contained_core_deployment(
        data_root=root, core_relative_path=carrier.native_core_database_path.name,
    )
    _require(
        corrected_inspection.core_role == "STAGING"
        and corrected_inspection.deployment_state is DeploymentState.LEGACY_ACTIVE
        and corrected_inspection.witness is None
        and not corrected_inspection.ever_active,
        "corrected P1 core is not inert",
    )
    _verify_unchanged_predecessor(root, preflight)

    recheck, process_count, listener_count = _fresh_writer_recheck(
        root, prepared.description.external_owner_observation_digest,
    )
    writer_record_c = preflight["writer_record_c"]
    writer_evidence = root_writer_freeze_evidence_payload_from_payload(
        writer_record_c.writer_freeze_evidence_payload,
    )
    writer_witness = RootWriterFreezeWitness(**writer_record_c.writer_freeze_witness_payload)
    request_d = RootOfflineCutoverRequest(
        data_root=root,
        description=prepared.description,
        normalization_request=carrier,
        effective_profile=profile_d,
        root_profile=p1_result.root_profile,
        runtime_scopes=runtime_scopes,
        writer_freeze=writer_witness,
        writer_freeze_evidence=writer_evidence,
        writer_freeze_recheck=recheck,
        geometry_disposition_plan=prepared.geometry_disposition_plan,
        operator_cutover_key=f"{RUN_ID}:envelope-d",
    )
    controller.prepare_root(request_d)
    pending = controller.enter_root_external_pending(request_d)
    _require(pending.selector_state is not None, "P2 did not return selector evidence")
    state = read_selector_state(data_root=root)
    _require(
        state.deployment_state is DeploymentState.CUTOVER_PENDING
        and state.core_id == corrected_core_id
        and state.core_relative_path == carrier.native_core_database_path.name
        and state.descriptor_digest == pending.envelope.digest,
        "selector does not bind corrected Envelope D",
    )
    agreement = resolve_deployment_agreement(data_root=root, effective_profile=profile_d)
    _require(agreement.mode is DeploymentResolutionMode.MAINTENANCE_ONLY, "corrected P2 did not retain maintenance-only authority")
    corrected_inspection = inspect_contained_core_deployment(
        data_root=root, core_relative_path=carrier.native_core_database_path.name,
    )
    _require(
        corrected_inspection.core_role == "STAGING"
        and corrected_inspection.deployment_state is DeploymentState.LEGACY_ACTIVE
        and corrected_inspection.witness is None
        and not corrected_inspection.ever_active,
        "corrected core changed authority during P2",
    )
    record_d = read_root_admission_envelope_record(
        data_root=root,
        core_relative_path=carrier.native_core_database_path.name,
        root_admission_envelope_digest=pending.envelope.digest,
    )
    _require(record_d is not None and record_d.envelope_digest != ENVELOPE_C_DIGEST, "Envelope D is not a distinct durable record")
    _require(
        read_root_writer_freeze_evidence_record(
            data_root=root,
            core_relative_path=carrier.native_core_database_path.name,
            root_admission_envelope_digest=pending.envelope.digest,
        ) is not None,
        "Envelope D writer-freeze evidence is missing",
    )
    _verify_unchanged_predecessor(root, preflight)

    connection = sqlite3.connect(f"file:{carrier.native_core_database_path.as_posix()}?mode=ro", uri=True)
    try:
        aliases = {
            UUID(bytes=row[0]): row[1]
            for row in connection.execute(
                "SELECT legacy_source_namespace_id,source_key FROM legacy_source_namespaces"
            )
        }
    finally:
        connection.close()
    _require(
        all(
            plan.motif_alias_namespace_id in aliases
            and aliases[plan.motif_alias_namespace_id] == _alias_key(_scope_key(plan))
            and plan.motif_alias_namespace_id != plan.legacy_source_namespace_id
            for plan in corrected_plans
        ),
        "durable corrected motif alias namespace evidence is incomplete",
    )
    result.update({
        "safe_root_pending_abort": "PRE_P5_CANONICAL_SPECIALIZATION",
        "post_abort_legacy_authority": "LEGACY_PUBLIC",
        "corrected_p1_disposition": p1_result.disposition.value,
        "envelope_d_digest": pending.envelope.digest,
        "final_selector_generation": state.generation,
        "final_selector_state": state.deployment_state.value,
        "final_public_api_posture": agreement.mode.value,
        "corrected_core_role": corrected_inspection.core_role,
        "corrected_core_deployment_state": corrected_inspection.deployment_state.value,
        "corrected_core_ever_active": corrected_inspection.ever_active,
        "corrected_core_witness": None,
        "corrected_motif_alias_separation": True,
        "fresh_root_target_process_count": process_count,
        "fresh_listener_count": listener_count,
        "real_p3_executed": False,
        "p4_executed": False,
        "p5_executed": False,
        "p6_executed": False,
        "p7_executed": False,
    })
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="perform the authorized P1/P2 administration")
    parser.add_argument(
        "--resume-after-retained-p1-refusal",
        action="store_true",
        help="require the exact retained schema-only P1 refusal state before continuing",
    )
    arguments = parser.parse_args()
    print(json.dumps(
        run(
            apply=arguments.apply,
            resume_after_retained_p1_refusal=arguments.resume_after_retained_p1_refusal,
        ),
        indent=2,
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
