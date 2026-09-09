"""Fail-closed real-root P3 source admission and normalization.

The only mutating path is ``--apply``.  It first proves that the current
D-bound source is equivalent to the completed copied-P3 reference, then runs
the existing P3A/P3B controller against the already-selected inert staging
core.  It deliberately has no P4--P7 or activation call path.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from typing import Any
from uuid import UUID

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from torment_service.embeddings import STEmbedding
from torment_service.substrate.character_seed_witness import (
    CharacterSeedWitness,
    CharacterSeedWitnessRefused,
    read_legacy_character_seed_witness_from_frozen_bytes,
)
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
from torment_service.substrate.migration.certified_refusal_runtime_proof import (
    CertifiedRefusalRuntimeProofFailed,
    CertifiedRefusalRuntimeSource,
    prove_certified_refusal_runtime_negative,
)
from torment_service.substrate.migration.explicit_source_evidence import (
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    resolve_explicit_source_evidence_path,
)
from torment_service.substrate.migration.root_normalization import RootP2ScopePlanCarrier
from torment_service.substrate.migration.root_p3_character_witness_continuation import (
    RootP3CharacterWitnessInput,
    RootP3ExternalOwnerObservationAuthority,
    _character_witness_semantically_equivalent,
)
from torment_service.substrate.migration.root_p3_source_admission import (
    RootP3CertifiedRefusalSourceMember,
    RootP3ScopeBinding,
    RootP3SourceAdmissionRequest,
)
from torment_service.substrate.migration.root_scope import RootScopeKey, RootScopeKind
from torment_service.substrate.migration.snapshot import load_snapshot_manifest
from torment_service.substrate.migration.workspace_runtime_readiness import WorkspaceNativeEmbedderIdentity
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.offline_cutover_controller import (
    OfflineCutoverController,
    RootOfflineCutoverRequest,
)
from torment_service.substrate.real_root_typed_evidence import (
    DirectPhase9BNamespaceBinding,
    build_real_direct_admission_source_adapter,
)
from torment_service.substrate.root_blocker5_binding import (
    RootGeometryDispositionPlan,
    RootGeometryDispositionPlanEntry,
    RootWriterFreezeWitness,
)
from torment_service.substrate.root_profile import current_root_profile_generation
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
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


EXPECTED_HEAD = "c4a2f6e63e5474f3e985ec26c8f855febadf6b77"
ENVELOPE_D_DIGEST = "e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb"
ENVELOPE_C_DIGEST = "d97c0545a538efca9657119abac133efc010bc41191b35f9e74ce9885f79b34b"
CORRECTED_CORE_ID = UUID("f21c730f-5222-4aa8-9a5f-1c1188456df3")
HISTORICAL_CORE_ID = UUID("0e9cb4b7-cf57-49fa-b60a-0e5a25f9d288")
FAILED_SCHEMA_CORE_ID = UUID("61cf7c92-398f-49cc-bad3-c980fbf2aab4")
CORRECTED_CORE_NAME = f"root-native-staging-{CORRECTED_CORE_ID}.db"
HISTORICAL_CORE_NAME = f"root-native-staging-{HISTORICAL_CORE_ID}.db"
FAILED_SCHEMA_CORE_NAME = f"root-native-staging-{FAILED_SCHEMA_CORE_ID}.db"
EXPECTED_SCOPE_COUNT = 154
EXPECTED_B1M = 2076
EXPECTED_B2_ORDINARY = 1953
EXPECTED_B2_CHARACTER = 88
EXPECTED_B2_REFUSED = 35
EXPECTED_B4 = {"b4a": 183, "b4b": 233, "b4c": 0, "b4p": 11, "b4_refused_member_semantic_gap": 23}
RUN_ID = "real-root-p3-production-20260909"
MODEL = "BAAI/bge-small-en-v1.5"
MODEL_CACHE_ROOT = Path(r"C:\Users\Notandi\.cache\huggingface\hub\models--BAAI--bge-small-en-v1.5")

ADMIN_ROOT = Path(r"C:\TORMENT\TORMENT_administration") / RUN_ID
REFERENCE_ROOT = Path(
    r"C:\TORMENT\TORMENT_administration\p1-p3-corrected-disposable-20260908"
    r"\retry24_dependent_motif_terminal_disposition"
)
REFERENCE_CARRIER = REFERENCE_ROOT / "successor_carrier" / "p3_source_admission_carrier.json"
REFERENCE_CHARACTER = (
    REFERENCE_ROOT / "character_continuation"
    / "p3_character_seed_witness_domain_derivation_continuation.json"
)
REFERENCE_CHARACTER_CENSUS = Path(
    r"C:\TORMENT\TORMENT_administration\envelope-c-complete-p2-input-recovery-b31c942-20260907"
    r"\frozen-source-character-census\census_result.json"
)
REFERENCE_REFUSALS = Path(
    r"C:\TORMENT\TORMENT_administration\p1-p3-corrected-disposable-20260908"
    r"\pre_b2_disposition_census_retry17.json"
)


class RealRootP3Refused(RuntimeError):
    """The authorized P3 proposition is not exactly established."""


class _NegativeProofEmbedder:
    provider = "st"
    model = MODEL
    dim = 384

    def embed(self, _text: str) -> np.ndarray:
        return np.ones(self.dim, dtype=np.float32)


def _qualified_local_b3b_embedder() -> tuple[STEmbedding, str]:
    """Open the already-qualified immutable Hub snapshot without any network lookup."""
    revision_path = MODEL_CACHE_ROOT / "refs" / "main"
    _require(revision_path.is_file(), "P3_QUALIFIED_MODEL_REFERENCE_MISSING")
    revision = revision_path.read_text(encoding="utf-8").strip()
    _require(len(revision) == 40 and all(char in "0123456789abcdef" for char in revision), "P3_QUALIFIED_MODEL_REFERENCE_INVALID")
    snapshot = MODEL_CACHE_ROOT / "snapshots" / revision
    _require(
        all((snapshot / name).is_file() for name in ("config.json", "modules.json", "model.safetensors", "tokenizer.json")),
        "P3_QUALIFIED_MODEL_SNAPSHOT_INCOMPLETE",
    )
    # SentenceTransformers treats a named Hub model differently from an
    # explicit snapshot and may perform an adapter metadata request even with
    # the offline flags.  Passing the pinned local snapshot prevents that I/O;
    # restore the canonical model identity exposed to the P3 request.
    embedder = STEmbedding(model=str(snapshot), device="cpu")
    _require(embedder.provider == "st" and embedder.dim == 384, "P3_QUALIFIED_MODEL_IDENTITY_MISMATCH")
    embedder.model = MODEL
    return embedder, revision


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RealRootP3Refused(code)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RealRootP3Refused(code) from exc
    _require(isinstance(value, dict), code)
    return value


def _scope_from_payload(value: object) -> RootScopeKey:
    _require(isinstance(value, dict), "P3_REFERENCE_SCOPE_SHAPE_INVALID")
    try:
        return RootScopeKey(
            value["workspace_id"], RootScopeKind(value["scope_kind"]),
            agent_id=value.get("agent_id"), domain_id=value.get("domain_id"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RealRootP3Refused("P3_REFERENCE_SCOPE_SHAPE_INVALID") from exc


def _scope_from_plan(plan: object) -> RootScopeKey:
    if getattr(plan, "scope_kind") == "PRIVATE_AGENT":
        return RootScopeKey(getattr(plan, "workspace_id"), RootScopeKind.PRIVATE, agent_id=getattr(plan, "agent_id"))
    if getattr(plan, "scope_kind") == "SHARED_DOMAIN":
        return RootScopeKey(getattr(plan, "workspace_id"), RootScopeKind.SHARED, domain_id=getattr(plan, "domain_id"))
    raise RealRootP3Refused("P3_RUNTIME_SCOPE_KIND_INVALID")


def _profile(payload: dict[str, object]) -> QualifiedDeploymentProfile:
    return QualifiedDeploymentProfile(
        compression_enabled=payload["compression_enabled"],
        deep_memory_enabled=payload["deep_memory_enabled"],
        representation_provider=payload["representation_provider"],
        representation_model=payload["representation_model"],
        representation_dimension=payload["representation_dimension"],
        admitted_scope_plan_digest=payload["admitted_scope_plan_digest"],
        external_owner_digest=payload["external_owner_digest"],
    )


def _read_core_profile(core: Path):
    connection = sqlite3.connect(f"file:{core.as_posix()}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        return current_root_profile_generation(connection)
    finally:
        connection.close()


def _schema_only_inert(root: Path, core_name: str, expected_id: UUID) -> bool:
    core = root / "substrate" / "cores" / core_name
    if not core.is_file():
        return False
    inspection = inspect_contained_core_deployment(data_root=root, core_relative_path=core_name)
    if not (
        inspection.core_id == expected_id
        and inspection.core_role == "STAGING"
        and inspection.deployment_state is DeploymentState.LEGACY_ACTIVE
        and inspection.witness is None
        and not inspection.ever_active
    ):
        return False
    connection = sqlite3.connect(f"file:{core.as_posix()}?mode=ro", uri=True)
    try:
        tables = (
            "identity_namespaces", "semantic_scopes", "legacy_source_namespaces",
            "idempotency_namespaces", "objects", "object_revisions", "operations",
            "maintenance_events", "legacy_admission_records", "legacy_artifact_records",
        )
        return all(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0 for table in tables)
    finally:
        connection.close()


def _fresh_writer_recheck(root: Path, external_owner_digest: str) -> RootWriterFreezeRecheck:
    census = subprocess.run(
        [
            "powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Compress",
        ],
        check=True, capture_output=True, text=True,
    )
    rows = json.loads(census.stdout) if census.stdout.strip() else []
    if isinstance(rows, dict):
        rows = [rows]
    _require(isinstance(rows, list), "P3_WRITER_PROCESS_CENSUS_INVALID")
    root_token = str(root).casefold()
    _require(
        not any(isinstance(row, dict) and isinstance(row.get("CommandLine"), str) and root_token in row["CommandLine"].casefold() for row in rows),
        "P3_WRITER_PROCESS_PRESENT",
    )
    listeners = subprocess.run(["netstat", "-ano", "-p", "tcp"], check=True, capture_output=True, text=True)
    _require(not any("127.0.0.1:8787" in line.casefold() for line in listeners.stdout.splitlines()), "P3_WRITER_LISTENER_PRESENT")
    observations = tuple(
        WriterProcessObservation(
            writer_class=writer_class,
            observation_mechanism="WINDOWS_CIM_ROOT_TARGET_CENSUS_V1",
            result=WriterObservationResult.ABSENT,
        )
        for writer_class in RootWriterClass
    )
    return RootWriterFreezeRecheck(
        covered_writer_classes=observations,
        listener_observation=ListenerObservation(
            listener_identity="127.0.0.1:8787",
            observation_mechanism="WINDOWS_NETSTAT_ANO_127_0_0_1_8787_V1",
            result=ListenerObservationResult.ABSENT,
        ),
        job_observation=observe_root_clone_repair_jobs(data_root=root),
        external_owner_observation_digest=external_owner_digest,
    )


def _reference() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    for path in (REFERENCE_CARRIER, REFERENCE_CHARACTER, REFERENCE_CHARACTER_CENSUS, REFERENCE_REFUSALS):
        _require(path.is_file(), "P3_FROZEN_REFERENCE_MISSING")
    carrier_outer = _json(REFERENCE_CARRIER, "P3_FROZEN_REFERENCE_CARRIER_UNREADABLE")
    carrier = carrier_outer.get("payload")
    _require(isinstance(carrier, dict) and isinstance(carrier.get("scopes"), list), "P3_FROZEN_REFERENCE_CARRIER_INVALID")
    _require(len(carrier["scopes"]) == EXPECTED_SCOPE_COUNT, "P3_FROZEN_REFERENCE_SCOPE_COUNT_INVALID")
    character_outer = _json(REFERENCE_CHARACTER, "P3_FROZEN_REFERENCE_CHARACTER_UNREADABLE")
    character = character_outer.get("payload")
    _require(isinstance(character, dict) and isinstance(character.get("witnesses"), list), "P3_FROZEN_REFERENCE_CHARACTER_INVALID")
    census = _json(REFERENCE_CHARACTER_CENSUS, "P3_FROZEN_REFERENCE_CHARACTER_CENSUS_UNREADABLE")
    refusals = _json(REFERENCE_REFUSALS, "P3_FROZEN_REFERENCE_REFUSALS_UNREADABLE")
    return carrier, character, census, refusals


def _p2_bound_preflight(root: Path) -> dict[str, Any]:
    _require(root.is_dir(), "P3_REAL_DATA_ROOT_MISSING")
    _require(_git("rev-parse", "HEAD") == EXPECTED_HEAD, "P3_STARTING_HEAD_MISMATCH")
    _require(_git("rev-parse", "origin/main") == EXPECTED_HEAD, "P3_ORIGIN_MAIN_MISMATCH")
    _require(not _git("status", "--porcelain", "--untracked-files=no"), "P3_TRACKED_WORKTREE_DIRTY")

    core = root / "substrate" / "cores" / CORRECTED_CORE_NAME
    historical = root / "substrate" / "cores" / HISTORICAL_CORE_NAME
    _require(core.is_file() and historical.is_file(), "P3_REQUIRED_CORE_MISSING")
    selector = read_selector_state(data_root=root)
    _require(
        selector.generation == 7
        and selector.deployment_state is DeploymentState.CUTOVER_PENDING
        and selector.core_id == CORRECTED_CORE_ID
        and selector.core_relative_path == CORRECTED_CORE_NAME
        and selector.descriptor_digest == ENVELOPE_D_DIGEST,
        "P3_SELECTOR_D_BOUNDARY_MISMATCH",
    )
    record_d = read_root_admission_envelope_record(
        data_root=root, core_relative_path=CORRECTED_CORE_NAME,
        root_admission_envelope_digest=ENVELOPE_D_DIGEST,
    )
    freeze_d = read_root_writer_freeze_evidence_record(
        data_root=root, core_relative_path=CORRECTED_CORE_NAME,
        root_admission_envelope_digest=ENVELOPE_D_DIGEST,
    )
    _require(record_d is not None and freeze_d is not None, "P3_ENVELOPE_D_EVIDENCE_MISSING")
    profile = _profile(record_d.effective_profile_payload)
    agreement = resolve_deployment_agreement(data_root=root, effective_profile=profile)
    _require(agreement.mode is DeploymentResolutionMode.MAINTENANCE_ONLY, "P3_PUBLIC_POSTURE_MISMATCH")
    inspection = inspect_contained_core_deployment(data_root=root, core_relative_path=CORRECTED_CORE_NAME)
    _require(
        inspection.core_id == CORRECTED_CORE_ID
        and inspection.core_role == "STAGING"
        and inspection.deployment_state is DeploymentState.LEGACY_ACTIVE
        and inspection.witness is None
        and not inspection.ever_active,
        "P3_CORRECTED_CORE_NOT_INERT",
    )
    record_c = read_root_admission_envelope_record(
        data_root=root, core_relative_path=HISTORICAL_CORE_NAME,
        root_admission_envelope_digest=ENVELOPE_C_DIGEST,
    )
    _require(record_c is not None and record_c.envelope_digest == ENVELOPE_C_DIGEST, "P3_ENVELOPE_C_MISSING")
    historical_before = _sha256_file(historical)
    historical_inspection = inspect_contained_core_deployment(data_root=root, core_relative_path=HISTORICAL_CORE_NAME)
    _require(
        historical_inspection.core_id == HISTORICAL_CORE_ID
        and historical_inspection.core_role == "STAGING"
        and historical_inspection.deployment_state is DeploymentState.LEGACY_ACTIVE
        and historical_inspection.witness is None
        and not historical_inspection.ever_active,
        "P3_HISTORICAL_CORE_NOT_INERT",
    )
    _require(_schema_only_inert(root, FAILED_SCHEMA_CORE_NAME, FAILED_SCHEMA_CORE_ID), "P3_FAILED_SCHEMA_CORE_NOT_INERT")
    _require(
        selector.core_id != FAILED_SCHEMA_CORE_ID and selector.core_relative_path != FAILED_SCHEMA_CORE_NAME,
        "P3_FAILED_SCHEMA_CORE_SELECTED",
    )
    _require(
        ENVELOPE_D_DIGEST != ENVELOPE_C_DIGEST
        and record_d.envelope_payload.get("native_staging_core_id") == str(CORRECTED_CORE_ID),
        "P3_ENVELOPE_D_CORE_BINDING_MISMATCH",
    )
    _require(
        all(plan.motif_alias_namespace_id != plan.legacy_source_namespace_id for plan in record_d.runtime_scope_plans),
        "P3_MOTIF_ALIAS_SEPARATION_MISMATCH",
    )
    _require(len(record_d.runtime_scope_plans) == EXPECTED_SCOPE_COUNT, "P3_SCOPE_COUNT_MISMATCH")
    return {
        "record_d": record_d,
        "freeze_d": freeze_d,
        "profile": profile,
        "selector": selector,
        "historical_sha256": historical_before,
        "core": core,
        "root_profile": _read_core_profile(core),
    }


def _prepare_live_source(root: Path, record_d: Any) -> Any:
    plan_by_scope = {_scope_from_plan(plan): plan for plan in record_d.runtime_scope_plans}
    bindings = tuple(
        DirectPhase9BNamespaceBinding(
            scope, plan.legacy_source_namespace_id, plan.target_identity_namespace_id,
        )
        for scope, plan in plan_by_scope.items()
        if scope.canonical_key in {
            ("ws3", "PRIVATE", "a1"), ("ws4", "PRIVATE", "a1"), ("ws5", "PRIVATE", "a1"),
        }
    )
    _require(len(bindings) == 3, "P3_PHASE9B_BINDING_SET_INVALID")
    adapter = build_real_direct_admission_source_adapter(
        data_root_identity=record_d.root_description_payload["data_root_identity"],
        operator_identity=record_d.root_description_payload["operator_identity"],
        direct_phase9b_namespace_bindings=tuple(sorted(bindings, key=lambda item: item.scope_key.canonical_key)),
    )
    prepared = adapter.prepare_direct_admission_source(data_root=root)
    _require(prepared.description.canonical_payload == record_d.root_description_payload, "P3_SOURCE_DESCRIPTION_DRIFT")
    _require(prepared.description.identity_digest == record_d.envelope_payload["root_description_digest"], "P3_SOURCE_DESCRIPTION_DIGEST_DRIFT")
    _require(len(prepared.source_scope_plans) == EXPECTED_SCOPE_COUNT, "P3_SOURCE_SCOPE_TOPOLOGY_DRIFT")
    _require({item.scope_key for item in prepared.source_scope_plans} == set(plan_by_scope), "P3_SOURCE_SCOPE_SET_DRIFT")
    return prepared


def _selected_rows(root: Path, description: Any) -> dict[tuple[RootScopeKey, int], str]:
    nodes = [
        item for item in description.explicit_source_manifest.entries
        if item.semantic_role is EvidenceSemanticRole.NODES
        and item.presence_expectation is EvidencePresenceExpectation.EXPECTED_PRESENT
        and item.scope_key is not None
    ]
    result: dict[tuple[RootScopeKey, int], str] = {}
    for evidence in nodes:
        path = resolve_explicit_source_evidence_path(data_root=root, evidence=evidence)
        try:
            rows = path.read_bytes().splitlines(keepends=True)
        except OSError as exc:
            raise RealRootP3Refused("P3_SOURCE_NODES_UNREADABLE") from exc
        for row in rows:
            try:
                value = json.loads(row.decode("utf-8"))
                eid = value["eid"]
            except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
                raise RealRootP3Refused("P3_SOURCE_NODE_ROW_INVALID") from exc
            _require(isinstance(eid, int) and not isinstance(eid, bool) and eid >= 0, "P3_SOURCE_NODE_EID_INVALID")
            result[(evidence.scope_key, eid)] = _sha256_bytes(row)
    return result


def _reference_rows(carrier: dict[str, Any]) -> dict[tuple[RootScopeKey, int], str]:
    result: dict[tuple[RootScopeKey, int], str] = {}
    for entry in carrier["scopes"]:
        _require(isinstance(entry, dict) and isinstance(entry.get("b1"), dict), "P3_REFERENCE_B1_MISSING")
        scope = _scope_from_payload(entry.get("scope_key"))
        expected_memories = entry["b1"].get("memories", [])
        _require(isinstance(expected_memories, list), "P3_REFERENCE_B1_MEMORY_INVALID")
        if not expected_memories:
            continue
        snapshot = Path(str(entry.get("snapshot_root", ""))) / "nodes.jsonl"
        try:
            rows = snapshot.read_bytes().splitlines(keepends=True)
        except OSError as exc:
            raise RealRootP3Refused("P3_REFERENCE_B1_NODES_UNREADABLE") from exc
        selected: dict[int, str] = {}
        for row in rows:
            try:
                value = json.loads(row.decode("utf-8"))
                eid = value["eid"]
            except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
                raise RealRootP3Refused("P3_REFERENCE_B1_NODE_ROW_INVALID") from exc
            _require(isinstance(eid, int) and not isinstance(eid, bool) and eid >= 0, "P3_REFERENCE_B1_NODE_EID_INVALID")
            selected[eid] = _sha256_bytes(row)
        _require(set(selected) == {item.get("eid") for item in expected_memories}, "P3_REFERENCE_B1_SNAPSHOT_CENSUS_INVALID")
        for eid, digest in selected.items():
            key = (scope, eid)
            _require(key not in result, "P3_REFERENCE_B1_EID_DUPLICATE")
            result[key] = digest
    return result


def _reference_snapshot_equivalence(root: Path, prepared: Any, carrier: dict[str, Any]) -> int:
    description = prepared.description
    by_scope = {_scope_from_payload(item.get("scope_key")): item for item in carrier["scopes"]}
    _require(len(by_scope) == EXPECTED_SCOPE_COUNT, "P3_REFERENCE_SNAPSHOT_SCOPE_INVALID")
    plans_by_scope = {plan.scope_key: plan for plan in prepared.source_scope_plans}
    checked = 0
    roles = {
        EvidenceSemanticRole.NODES, EvidenceSemanticRole.EDGES, EvidenceSemanticRole.EMBEDDING_MANIFEST,
        EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP, EvidenceSemanticRole.LEGACY_REPRESENTATION,
        EvidenceSemanticRole.MOTIFS, EvidenceSemanticRole.WORKSPACE_META,
    }
    for evidence in description.explicit_source_manifest.entries:
        if evidence.presence_expectation is not EvidencePresenceExpectation.EXPECTED_PRESENT or evidence.semantic_role not in roles:
            continue
        scope = evidence.scope_key
        if scope is None:
            # P3 only snapshots workspace metadata for a scope with motifs or a
            # materialized memory graph.  P2-D binds all metadata, but metadata
            # outside that P3 input boundary was intentionally absent from the
            # copied P3 carrier and must not be mistaken for source-epoch drift.
            captured_scopes = [
                key for key, plan in plans_by_scope.items()
                if key.workspace_id == evidence.owner_boundary.workspace_id
                and (
                    plan.motif_presence.value == "PRESENT"
                    or (
                        plan.materialization_posture.value == "MEMORY_GRAPH"
                        and plan.representation_disposition.value != "UNKNOWN_IDENTITY"
                    )
                )
            ]
            if not captured_scopes:
                continue
            candidates = [by_scope.get(key) for key in captured_scopes]
        else:
            candidates = [by_scope.get(scope)]
        matched = False
        for entry in candidates:
            if not isinstance(entry, dict):
                continue
            manifest_path = Path(str(entry.get("manifest_path", "")))
            try:
                manifest = load_snapshot_manifest(manifest_path)
            except Exception as exc:
                raise RealRootP3Refused("P3_REFERENCE_SNAPSHOT_UNREADABLE") from exc
            wanted = evidence.canonical_locator
            artifact = next((item for item in manifest.artifacts if item.observed_relative_locator.endswith(wanted)), None)
            if artifact is None:
                continue
            if artifact.byte_length == evidence.byte_length and artifact.digest_hex == evidence.sha256_hex:
                matched = True
                break
        if not matched:
            scope_label = evidence.owner_boundary.workspace_id if scope is None else "|".join(scope.canonical_key)
            raise RealRootP3Refused(f"P3_SOURCE_EPOCH_ARTIFACT_DRIFT:{evidence.semantic_role.value}:{scope_label}:{evidence.canonical_locator}")
        checked += 1
    _require(checked > 0, "P3_SOURCE_EPOCH_ARTIFACT_CENSUS_EMPTY")
    return checked


def _character_inputs(root: Path, prepared: Any, plans: tuple[object, ...], character: dict[str, Any], census: dict[str, Any]):
    _require(census.get("status") == "PASS" and census.get("frozen_source_character_scope_count") == 37, "P3_REFERENCE_CHARACTER_CENSUS_INVALID")
    reference_by_scope = {
        _scope_from_payload(item.get("scope_key")): item
        for item in character.get("witnesses", []) if isinstance(item, dict)
    }
    census_by_scope = {
        _scope_from_payload(item.get("scope_key")): item
        for item in census.get("character_scopes", []) if isinstance(item, dict)
    }
    _require(len(reference_by_scope) == len(census_by_scope) == 37, "P3_REFERENCE_CHARACTER_SCOPE_COUNT_INVALID")
    plan_by_scope = {_scope_from_plan(plan): plan for plan in plans}
    observations = {
        (item.workspace_id, item.observation_key): item
        for item in prepared.description.external_owner_observations
        if item.owner_kind.value == "CHARACTER"
    }
    motifs_by_workspace: dict[str, list[Path]] = {}
    for evidence in prepared.description.explicit_source_manifest.entries:
        if evidence.semantic_role is EvidenceSemanticRole.MOTIFS and evidence.presence_expectation is EvidencePresenceExpectation.EXPECTED_PRESENT:
            motifs_by_workspace.setdefault(evidence.owner_boundary.workspace_id, []).append(
                resolve_explicit_source_evidence_path(data_root=root, evidence=evidence)
            )
    inputs: list[RootP3CharacterWitnessInput] = []
    opened = []
    exact = compatible = 0
    pairs: set[tuple[RootScopeKey, int]] = set()
    for scope in sorted(census_by_scope, key=lambda item: item.canonical_key):
        frozen = census_by_scope[scope]
        witness_record = reference_by_scope.get(scope)
        plan = plan_by_scope.get(scope)
        _require(witness_record is not None and plan is not None, "P3_CHARACTER_SCOPE_DRIFT")
        seed_id = frozen.get("seed_id")
        seed_digest = frozen.get("p2_observation_digest")
        _require(isinstance(seed_id, str) and isinstance(seed_digest, str), "P3_CHARACTER_REFERENCE_INVALID")
        seed_path = root / "workspaces" / scope.workspace_id / "seeds" / seed_id / "seed.json"
        _require(seed_path.is_file() and _sha256_file(seed_path) == seed_digest, "P3_CHARACTER_SEED_DRIFT")
        observation = observations.get((scope.workspace_id, f"seed:{seed_id}"))
        _require(observation is not None and observation.observation_digest == seed_digest, "P3_CHARACTER_P2_OBSERVATION_DRIFT")
        private_nodes = root / "workspaces" / scope.workspace_id / "agents" / (scope.agent_id or "") / "private" / "nodes.jsonl"
        _require(private_nodes.is_file(), "P3_CHARACTER_PRIVATE_NODES_MISSING")
        descriptor = witness_record.get("character_witness")
        _require(isinstance(descriptor, dict), "P3_CHARACTER_REFERENCE_DESCRIPTOR_INVALID")
        successful: list[tuple[str, CharacterSeedWitness]] = []
        seed_bytes = seed_path.read_bytes()
        nodes_bytes = private_nodes.read_bytes()
        for motif_path in motifs_by_workspace.get(scope.workspace_id, []):
            domain_id = motif_path.parent.name
            try:
                derived = read_legacy_character_seed_witness_from_frozen_bytes(
                    seed_definition_bytes=seed_bytes, private_nodes_bytes=nodes_bytes,
                    motif_bytes=motif_path.read_bytes(), workspace_id=scope.workspace_id,
                    agent_id=scope.agent_id or "", domain_id=domain_id, requested_seed_id=seed_id,
                )
            except CharacterSeedWitnessRefused:
                continue
            successful.append((domain_id, derived))
        _require(len(successful) == 1, "P3_CHARACTER_DOMAIN_DRIFT")
        frozen_eids = frozen.get("seed_canon_eids")
        _require(isinstance(frozen_eids, list) and tuple(successful[0][1].seed_eids) == tuple(sorted(frozen_eids)), "P3_CHARACTER_EID_DRIFT")
        descriptor_witness = CharacterSeedWitness.from_descriptor_payload(
            workspace_id=scope.workspace_id, agent_id=scope.agent_id or "", domain_id=successful[0][0], value=descriptor,
        )
        if descriptor_witness.witness_digest == successful[0][1].witness_digest:
            exact += 1
        else:
            _require(_character_witness_semantically_equivalent(descriptor_witness, successful[0][1]), "P3_CHARACTER_SEMANTIC_DRIFT")
            compatible += 1
        for eid in successful[0][1].seed_eids:
            _require((scope, eid) not in pairs, "P3_CHARACTER_EID_DUPLICATE")
            pairs.add((scope, eid))
        inputs.append(RootP3CharacterWitnessInput(scope, plan.legacy_source_namespace_id, seed_bytes, descriptor))
        opened.append(observation)
    _require((exact, compatible, len(pairs)) == (36, 1, 88), "P3_CHARACTER_CLOSURE_DRIFT")
    authority = RootP3ExternalOwnerObservationAuthority(
        ENVELOPE_D_DIGEST, prepared.description.external_owner_observation_digest,
        tuple(sorted(opened, key=lambda item: item.canonical_key)),
    )
    return authority, tuple(inputs), {"closure": "37 / 37", "exact_current": exact, "historical_compatible": compatible, "semantic_mismatch": 0}


def _certified_refusals(prepared: Any, plans: tuple[object, ...], selected: dict[tuple[RootScopeKey, int], str], reference: dict[str, Any]):
    _require(reference.get("pre_b2_b1m") == EXPECTED_B1M and reference.get("pre_b2_certified_refusal_candidates") == EXPECTED_B2_REFUSED, "P3_REFERENCE_REFUSAL_CENSUS_INVALID")
    plan_by_scope = {_scope_from_plan(plan): plan for plan in plans}
    nodes_by_scope = {
        item.scope_key: item.sha256_hex
        for item in prepared.description.explicit_source_manifest.entries
        if item.semantic_role is EvidenceSemanticRole.NODES and item.presence_expectation is EvidencePresenceExpectation.EXPECTED_PRESENT
    }
    result = []
    for item in reference.get("refused_members", []):
        _require(isinstance(item, dict), "P3_REFERENCE_REFUSAL_MEMBER_INVALID")
        scope = _scope_from_payload(item.get("scope_key"))
        eid, digest = item.get("eid"), item.get("selected_raw_row_sha256")
        plan = plan_by_scope.get(scope)
        _require(isinstance(eid, int) and isinstance(digest, str) and plan is not None, "P3_REFERENCE_REFUSAL_MEMBER_INVALID")
        _require(selected.get((scope, eid)) == digest, "P3_REFUSAL_SOURCE_DRIFT")
        node_digest = nodes_by_scope.get(scope)
        _require(isinstance(node_digest, str), "P3_REFUSAL_NODES_EVIDENCE_MISSING")
        result.append(RootP3CertifiedRefusalSourceMember(scope, plan.legacy_source_namespace_id, eid, digest, node_digest))
    result.sort(key=lambda item: (item.scope_key.canonical_key, item.eid))
    _require(len(result) == EXPECTED_B2_REFUSED and len({(item.scope_key, item.eid) for item in result}) == EXPECTED_B2_REFUSED, "P3_REFUSAL_CLOSURE_DRIFT")
    return tuple(result)


def _reference_motif_dependency_census(
    carrier: dict[str, Any],
    refusal_members: tuple[RootP3CertifiedRefusalSourceMember, ...],
) -> dict[str, int]:
    routes = carrier.get("b4_routes")
    _require(isinstance(routes, dict) and isinstance(routes.get("scope_routes"), list), "P3_REFERENCE_B4_ROUTES_INVALID")
    counts = {"B4A": 0, "B4B": 0, "B4C": 0, "B4P": 0, "B4_REFUSED_MEMBER_SEMANTIC_GAP": 0}
    scope_by_source_namespace = {str(item.legacy_source_namespace_id): item.scope_key for item in refusal_members}
    referenced: list[tuple[RootScopeKey, int]] = []
    for entry in routes["scope_routes"]:
        _require(isinstance(entry, dict), "P3_REFERENCE_B4_ROUTES_INVALID")
        scope = _scope_from_payload(entry.get("scope_key"))
        items = entry.get("routes")
        _require(isinstance(items, list), "P3_REFERENCE_B4_ROUTES_INVALID")
        for route in items:
            _require(isinstance(route, dict) and route.get("route") in counts, "P3_REFERENCE_B4_ROUTES_INVALID")
            counts[route["route"]] += 1
            if route["route"] == "B4_REFUSED_MEMBER_SEMANTIC_GAP":
                members = route.get("refused_members")
                _require(isinstance(members, list) and members, "P3_REFERENCE_B4_REFUSAL_INVALID")
                for member in members:
                    _require(
                        isinstance(member, dict) and isinstance(member.get("eid"), int)
                        and isinstance(member.get("legacy_source_namespace_id"), str),
                        "P3_REFERENCE_B4_REFUSAL_INVALID",
                    )
                    source_scope = scope_by_source_namespace.get(member["legacy_source_namespace_id"])
                    _require(source_scope is not None, "P3_REFERENCE_B4_REFUSAL_INVALID")
                    referenced.append((source_scope, member["eid"]))
    # The carrier records execution routes only: B4P is a terminal partial
    # disposition established in B1F, while B4C has no source instances.
    _require(
        counts == {"B4A": 183, "B4B": 233, "B4C": 0, "B4P": 0, "B4_REFUSED_MEMBER_SEMANTIC_GAP": 23},
        "P3_REFERENCE_B4_CENSUS_INVALID",
    )
    refusal_set = {(item.scope_key, item.eid) for item in refusal_members}
    referenced_set = set(referenced)
    _require(
        len(referenced) == len(referenced_set) == 30
        and referenced_set <= refusal_set
        and len(refusal_set - referenced_set) == 5,
        "P3_REFERENCE_B4_DEPENDENCY_CENSUS_INVALID",
    )
    return {
        "refusal_memory_count": len(refusal_set),
        "refused_memories_referenced_by_motifs": len(referenced_set),
        "refused_memories_not_referenced_by_motifs": len(refusal_set - referenced_set),
        "motifs_containing_refused_member": counts["B4_REFUSED_MEMBER_SEMANTIC_GAP"],
        "total_refused_member_occurrences": len(referenced),
    }


def _source_census(root: Path, prepared: Any, plans: tuple[object, ...]) -> dict[str, Any]:
    carrier, character, character_census, refusals = _reference()
    selected = _selected_rows(root, prepared.description)
    expected = _reference_rows(carrier)
    _require(selected == expected and len(selected) == EXPECTED_B1M, "P3_MEMORY_EPOCH_DRIFT")
    artifacts = _reference_snapshot_equivalence(root, prepared, carrier)
    authority, character_inputs, character_result = _character_inputs(root, prepared, plans, character, character_census)
    refusal_members = _certified_refusals(prepared, plans, selected, refusals)
    motif_dependencies = _reference_motif_dependency_census(carrier, refusal_members)
    b1f = carrier.get("b1f")
    _require(isinstance(b1f, dict), "P3_REFERENCE_MOTIF_CENSUS_INVALID")
    _require(
        (b1f.get("total_motif_count"), b1f.get("exact_motif_count"), b1f.get("partial_motif_count"), b1f.get("zero_member_motif_count"), b1f.get("blocking_motif_count")) == (450, 439, 11, 0, 0),
        "P3_REFERENCE_MOTIF_CENSUS_INVALID",
    )
    return {
        "selected": selected,
        "character_authority": authority,
        "character_inputs": character_inputs,
        "character": character_result,
        "refusal_members": refusal_members,
        "artifact_count": artifacts,
        "memory_count": len(selected),
        "motif_count": 450,
        "motif_dependencies": motif_dependencies,
    }


def _request(
    root: Path,
    state: dict[str, Any],
    prepared: Any,
    census: dict[str, Any],
    *,
    b3b_embedder: STEmbedding,
) -> tuple[RootOfflineCutoverRequest, RootP3SourceAdmissionRequest]:
    record = state["record_d"]
    plans = record.runtime_scope_plans
    carrier = RootP2ScopePlanCarrier(
        description=prepared.description, data_root=root, native_core_database_path=state["core"],
        expected_native_core_id=CORRECTED_CORE_ID, runtime_scope_plans=plans,
    )
    runtime_scopes = tuple(
        NativeMemoryRuntimeScope(
            workspace_id=plan.workspace_id, scope_kind=plan.scope_kind,
            legacy_source_namespace_id=plan.legacy_source_namespace_id,
            identity_namespace_id=plan.target_identity_namespace_id,
            semantic_scope_id=plan.target_semantic_scope_id,
            agent_id=plan.agent_id, domain_id=plan.domain_id,
        ) for plan in plans
    )
    freeze_payload = root_writer_freeze_evidence_payload_from_payload(state["freeze_d"].writer_freeze_evidence_payload)
    cutover = RootOfflineCutoverRequest(
        data_root=root, description=prepared.description, normalization_request=carrier,
        effective_profile=state["profile"], root_profile=state["root_profile"], runtime_scopes=runtime_scopes,
        writer_freeze=RootWriterFreezeWitness(**record.writer_freeze_payload),
        writer_freeze_evidence=freeze_payload,
        writer_freeze_recheck=_fresh_writer_recheck(root, prepared.description.external_owner_observation_digest),
        geometry_disposition_plan=RootGeometryDispositionPlan(tuple(
            RootGeometryDispositionPlanEntry(**item) for item in record.geometry_disposition_entries
        )),
        operator_cutover_key=f"{RUN_ID}:envelope-d-recovery",
    )
    scope_bindings = tuple(sorted((
        RootP3ScopeBinding(_scope_from_plan(plan), plan, plan.target_semantic_scope_id)
        for plan in plans
    ), key=lambda item: item.scope_key.canonical_key))
    _require({item.scope_key for item in scope_bindings} == {item.scope_key for item in prepared.source_scope_plans}, "P3_SCOPE_BINDING_DRIFT")
    p3 = RootP3SourceAdmissionRequest(
        data_root=root, native_core_database_path=state["core"], expected_native_core_id=CORRECTED_CORE_ID,
        description=prepared.description, source_scope_plans=tuple(sorted(prepared.source_scope_plans, key=lambda item: item.scope_key.canonical_key)),
        scope_bindings=scope_bindings, unknown_identity_evidence=prepared.unknown_identity_evidence,
        carrier_directory=ADMIN_ROOT / "carrier", operation_key=RUN_ID,
        qualification_embedder_identity=WorkspaceNativeEmbedderIdentity("st", MODEL, 384),
        b3b_embedder=b3b_embedder,
        character_observation_authority=census["character_authority"],
        character_witness_inputs=census["character_inputs"],
        character_continuation_carrier_directory=ADMIN_ROOT / "character_continuation",
        partial_authority_continuation_directory=ADMIN_ROOT / "partial_motif_authority_continuation",
        certified_refusal_source_members=census["refusal_members"],
    )
    return cutover, p3


def _proof_sources(carrier_path: Path) -> tuple[CertifiedRefusalRuntimeSource, ...]:
    payload = _json(carrier_path, "P3_RESULT_CARRIER_UNREADABLE").get("payload")
    _require(isinstance(payload, dict), "P3_RESULT_CARRIER_INVALID")
    sources = []
    for entry in payload.get("scopes", []):
        _require(isinstance(entry, dict), "P3_RESULT_CARRIER_INVALID")
        plan = entry.get("scope_plan")
        _require(isinstance(plan, dict), "P3_RESULT_CARRIER_INVALID")
        scope = NativeMemoryRuntimeScope(
            workspace_id=plan["workspace_id"], scope_kind=plan["scope_kind"],
            legacy_source_namespace_id=UUID(plan["legacy_source_namespace_id"]),
            identity_namespace_id=UUID(plan["target_identity_namespace_id"]),
            semantic_scope_id=UUID(plan["target_semantic_scope_id"]),
            agent_id=plan["qualifier"] if plan["scope_kind"] == "PRIVATE_AGENT" else None,
            domain_id=plan["qualifier"] if plan["scope_kind"] == "SHARED_DOMAIN" else None,
        )
        b1 = {item["eid"]: item for item in entry.get("b1", {}).get("memories", [])}
        for receipt in entry.get("b2", {}).get("memories", []):
            if receipt.get("disposition") == "B2_REFUSED_SOURCE_SEMANTIC_GAP":
                item = b1[receipt["eid"]]
                sources.append(CertifiedRefusalRuntimeSource(receipt["eid"], UUID(item["object_id"]), UUID(item["r1_revision_id"]), scope))
    _require(len(sources) == EXPECTED_B2_REFUSED, "P3_RESULT_REFUSAL_COUNT_INVALID")
    return tuple(sources)


def _result_memory_partition(carrier_path: Path) -> dict[str, int]:
    payload = _json(carrier_path, "P3_RESULT_CARRIER_UNREADABLE").get("payload")
    _require(isinstance(payload, dict) and isinstance(payload.get("scopes"), list), "P3_RESULT_CARRIER_INVALID")
    ordinary = character = admitted = refused = 0
    for entry in payload["scopes"]:
        _require(isinstance(entry, dict), "P3_RESULT_CARRIER_INVALID")
        b1 = entry.get("b1")
        b2 = entry.get("b2")
        _require(isinstance(b1, dict) and isinstance(b2, dict), "P3_RESULT_CARRIER_INVALID")
        b1_by_eid = {item.get("eid"): item for item in b1.get("memories", []) if isinstance(item, dict)}
        for receipt in b2.get("memories", []):
            _require(isinstance(receipt, dict), "P3_RESULT_CARRIER_INVALID")
            source = b1_by_eid.get(receipt.get("eid"))
            _require(isinstance(source, dict), "P3_RESULT_CARRIER_INVALID")
            disposition = receipt.get("disposition")
            if disposition == "B2_REFUSED_SOURCE_SEMANTIC_GAP":
                refused += 1
                continue
            _require(disposition == "ADMITTED", "P3_RESULT_B2_DISPOSITION_INVALID")
            admitted += 1
            if source.get("normalization_kind") == "ORDINARY":
                ordinary += 1
            elif source.get("normalization_kind") == "CHARACTER_SEED":
                character += 1
            else:
                raise RealRootP3Refused("P3_RESULT_B2_KIND_INVALID")
    _require(
        (ordinary, character, admitted, refused) == (EXPECTED_B2_ORDINARY, EXPECTED_B2_CHARACTER, 2041, EXPECTED_B2_REFUSED),
        "P3_RESULT_B2_PARTITION_MISMATCH",
    )
    return {"ordinary": ordinary, "character": character, "admitted": admitted, "refused": refused, "unaccounted": 0}


def _prove_refused_motif_runtime_negative(
    connection: sqlite3.Connection,
    *,
    carrier_path: Path,
    runtime_scope_plans: tuple[object, ...],
) -> dict[str, int]:
    """Prove every B4 refusal has no native object, membership, or reader exposure."""
    payload = _json(carrier_path, "P3_RESULT_CARRIER_UNREADABLE").get("payload")
    _require(isinstance(payload, dict), "P3_RESULT_CARRIER_INVALID")
    b4_routes = payload.get("b4_routes")
    _require(isinstance(b4_routes, dict), "P3_RESULT_B4_ROUTES_INVALID")
    scope_routes = b4_routes.get("scope_routes")
    _require(isinstance(scope_routes, list), "P3_RESULT_B4_ROUTES_INVALID")
    plans = {_scope_from_plan(plan): plan for plan in runtime_scope_plans}
    reader = NativeMotifRuntimeReader(connection)
    visible_by_scope: dict[RootScopeKey, set[str]] = {}
    refusal_count = alias_absences = reader_absences = 0
    for scope_entry in scope_routes:
        _require(isinstance(scope_entry, dict), "P3_RESULT_B4_ROUTES_INVALID")
        scope = _scope_from_payload(scope_entry.get("scope_key"))
        plan = plans.get(scope)
        routes = scope_entry.get("routes")
        _require(plan is not None and isinstance(routes, list), "P3_RESULT_B4_ROUTES_INVALID")
        rejected = [item for item in routes if isinstance(item, dict) and item.get("route") == "B4_REFUSED_MEMBER_SEMANTIC_GAP"]
        if rejected:
            _require(scope.scope_kind is RootScopeKind.SHARED and scope.domain_id is not None, "P3_RESULT_B4_SCOPE_INVALID")
            visible_by_scope[scope] = {
                item.read_model.runtime_motif_id
                for item in reader.list_runtime_motifs(
                    motif_alias_namespace_id=plan.motif_alias_namespace_id,
                    domain_id=scope.domain_id,
                    semantic_scope_id=plan.target_semantic_scope_id,
                )
            }
        for route in rejected:
            runtime_motif_id = route.get("runtime_motif_id")
            operation_id = route.get("receipt_operation_id")
            _require(isinstance(runtime_motif_id, str) and isinstance(operation_id, str), "P3_RESULT_B4_ROUTE_INVALID")
            operation = connection.execute(
                "SELECT operation_kind FROM operations WHERE operation_id=?", (native_id_to_bytes(UUID(operation_id)),)
            ).fetchone()
            rejection = connection.execute(
                "SELECT rejection_code FROM operation_rejections WHERE operation_id=?", (native_id_to_bytes(UUID(operation_id)),)
            ).fetchone()
            transitions = connection.execute(
                "SELECT count(*) FROM semantic_transitions WHERE operation_id=?", (native_id_to_bytes(UUID(operation_id)),)
            ).fetchone()[0]
            outputs = connection.execute(
                "SELECT count(*) FROM operation_outputs WHERE operation_id=?", (native_id_to_bytes(UUID(operation_id)),)
            ).fetchone()[0]
            aliases = connection.execute(
                """SELECT count(*) FROM legacy_object_aliases
                   WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value=?""",
                (native_id_to_bytes(plan.motif_alias_namespace_id), runtime_motif_id),
            ).fetchone()[0]
            _require(
                operation == ("P3_B4_REFUSED_MEMBER_SEMANTIC_GAP",)
                and rejection == ("B4_REFUSED_MEMBER_SEMANTIC_GAP",)
                and transitions == outputs == aliases == 0,
                "P3_MOTIF_REFUSAL_RUNTIME_LEAK",
            )
            _require(runtime_motif_id not in visible_by_scope[scope], "P3_MOTIF_REFUSAL_RUNTIME_READER_LEAK")
            refusal_count += 1
            alias_absences += 1
            reader_absences += 1
    _require(refusal_count == EXPECTED_B4["b4_refused_member_semantic_gap"], "P3_MOTIF_REFUSAL_ROUTE_COUNT_INVALID")
    return {
        "refusal_count": refusal_count,
        "target_alias_absences": alias_absences,
        "runtime_reader_absences": reader_absences,
    }


def _verify_post_p3(root: Path, state: dict[str, Any], evidence: Any, census: dict[str, Any]) -> dict[str, Any]:
    selector = read_selector_state(data_root=root)
    _require(
        selector.generation == 7 and selector.deployment_state is DeploymentState.CUTOVER_PENDING
        and selector.core_id == CORRECTED_CORE_ID and selector.descriptor_digest == ENVELOPE_D_DIGEST,
        "P3_SELECTOR_AUTHORITY_CHANGED",
    )
    inspection = inspect_contained_core_deployment(data_root=root, core_relative_path=CORRECTED_CORE_NAME)
    _require(inspection.core_role == "STAGING" and inspection.deployment_state is DeploymentState.LEGACY_ACTIVE and inspection.witness is None and not inspection.ever_active, "P3_CORE_AUTHORITY_CHANGED")
    historical = root / "substrate" / "cores" / HISTORICAL_CORE_NAME
    _require(_sha256_file(historical) == state["historical_sha256"], "P3_HISTORICAL_CORE_MUTATED")
    _require(_schema_only_inert(root, FAILED_SCHEMA_CORE_NAME, FAILED_SCHEMA_CORE_ID), "P3_FAILED_SCHEMA_CORE_MUTATED")
    normalization = evidence.normalization
    source = evidence.source_admission
    child = dict(source.child_request_counts)
    _require(
        source.b1_memory_count == EXPECTED_B1M and source.b2_memory_count == EXPECTED_B1M - EXPECTED_B2_REFUSED
        and source.b2_refused_memory_count == EXPECTED_B2_REFUSED
        and child.get("b3a") == 1808 and child.get("total_b3b") == 233
        and all(child.get(key) == value for key, value in EXPECTED_B4.items()),
        "P3_RESULT_ROUTE_CENSUS_MISMATCH",
    )
    _require(
        normalization.root_memory_disposition_closed and normalization.root_motif_disposition_closed
        and normalization.root_normalization_complete and not normalization.root_normalization_ready
        and normalization.p3_completion_class == "P3_DISPOSITION_CLOSED_WITH_CERTIFIED_EXCEPTIONS",
        "P3_RESULT_CLOSURE_MISMATCH",
    )
    carrier = source.carrier_record_path
    memory_partition = _result_memory_partition(carrier)
    connection = sqlite3.connect(f"file:{state['core'].as_posix()}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        proof = prove_certified_refusal_runtime_negative(
            connection, sources=_proof_sources(carrier), native_core_database_path=state["core"],
            expected_native_core_id=CORRECTED_CORE_ID, representation_lane=prepared_lane(state["record_d"]),
            vector_embedder=_NegativeProofEmbedder(),
        )
        motif_proof = _prove_refused_motif_runtime_negative(
            connection, carrier_path=carrier, runtime_scope_plans=state["record_d"].runtime_scope_plans,
        )
        _require(normalization.b4_certified_refused_motif_count == motif_proof["refusal_count"], "P3_MOTIF_REFUSAL_RUNTIME_LEAK")
    except CertifiedRefusalRuntimeProofFailed as exc:
        raise RealRootP3Refused("P3_MEMORY_REFUSAL_RUNTIME_LEAK") from exc
    finally:
        connection.close()
    return {
        "final_evidence_set_e_digest": source.final_evidence_set_e_digest,
        "b1m": source.b1_memory_count,
        "b2_ordinary": memory_partition["ordinary"],
        "b2_character": memory_partition["character"],
        "b2_admitted": memory_partition["admitted"],
        "b2_refused": memory_partition["refused"],
        "b2_unaccounted": memory_partition["unaccounted"],
        "b3a": child["b3a"], "b3b": child["total_b3b"],
        **{key: child[key] for key in EXPECTED_B4},
        "memory_refusal_runtime_proof": asdict(proof),
        "motif_refusal_runtime_proof": motif_proof,
        "motif_refusal_runtime_leak": False,
        "root_memory_disposition_closed": normalization.root_memory_disposition_closed,
        "root_motif_disposition_closed": normalization.root_motif_disposition_closed,
        "root_disposition_closure": source.root_disposition_closed,
        "root_normalization_ready": normalization.root_normalization_ready,
        "completion_class": normalization.p3_completion_class,
        "character": census["character"],
    }


def prepared_lane(record: Any) -> NativeRepresentationLane:
    return record.target_representation_lane


def _git(*arguments: str) -> str:
    result = subprocess.run(["git", *arguments], cwd=REPOSITORY_ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def run(*, apply: bool) -> dict[str, Any]:
    root = (REPOSITORY_ROOT / "data").resolve()
    state = _p2_bound_preflight(root)
    prepared = _prepare_live_source(root, state["record_d"])
    freeze = root_writer_freeze_evidence_payload_from_payload(state["freeze_d"].writer_freeze_evidence_payload)
    _require(snapshot_root_workspaces(data_root=root) == freeze.source_tree_snapshot, "P3_WORKSPACE_FREEZE_DRIFT")
    census = _source_census(root, prepared, state["record_d"].runtime_scope_plans)
    result: dict[str, Any] = {
        "mode": "APPLY" if apply else "DRY_RUN",
        "starting_head": EXPECTED_HEAD,
        "origin_main": _git("rev-parse", "origin/main"),
        "tracked_worktree": "CLEAN",
        "envelope_d_digest": ENVELOPE_D_DIGEST,
        "corrected_core_id": str(CORRECTED_CORE_ID),
        "corrected_core_path": str(state["core"]),
        "selector_generation_initial": state["selector"].generation,
        "selector_state_initial": state["selector"].deployment_state.value,
        "public_api_posture_initial": "MAINTENANCE_ONLY",
        "historical_core_sha256": state["historical_sha256"],
        "source_census_equivalent": True,
        "motif_census_equivalent": True,
        "character_census_equivalent": True,
        "source_epoch_drift": False,
        "source_artifact_count_compared": census["artifact_count"],
        "b1m": census["memory_count"],
        "source_motif_count": census["motif_count"],
        **census["motif_dependencies"],
        "p4_executed": False, "p5_executed": False, "p6_executed": False, "p7_executed": False,
    }
    if not apply:
        return result
    # Never allow a production P3 run to fetch or alter model provenance.  The
    # already-qualified model must be locally available before we create any
    # P3 administration evidence or open the staging core for mutation.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    embedder, model_snapshot_revision = _qualified_local_b3b_embedder()
    _require(not ADMIN_ROOT.exists(), "P3_ADMINISTRATION_DESTINATION_EXISTS")
    ADMIN_ROOT.mkdir(parents=True)
    cutover, source_admission = _request(root, state, prepared, census, b3b_embedder=embedder)
    evidence = OfflineCutoverController().admit_and_normalize_root_under_external_fence(cutover, source_admission)
    post = _verify_post_p3(root, state, evidence, census)
    result.update(post)
    selector = read_selector_state(data_root=root)
    result.update({
        "real_root_contact": "YES", "real_p3_executed": True,
        "carrier_record": str(evidence.source_admission.carrier_record_path),
        "qualified_model_snapshot_revision": model_snapshot_revision,
        "selector_generation_final": selector.generation,
        "selector_state_final": selector.deployment_state.value,
        "public_api_posture_final": "MAINTENANCE_ONLY",
    })
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="run the authorized P3 operation after preflight")
    arguments = parser.parse_args()
    print(json.dumps(run(apply=arguments.apply), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
