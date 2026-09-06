"""Recoverable P3 source admission before the existing root B3/B4 normalizer.

The root normalizer intentionally starts after B1/B2.  This module supplies
the missing, narrowly bounded source-admission carrier for P3: it captures
only declared source evidence into external snapshots, records the selected
snapshot identities atomically, runs the established B1 and B2 services, and
then constructs an ordinary :class:`RootNormalizationRequest` for the
existing B3/B4 coordinator.

The carrier is evidence, not deployment authority.  Its one record is
deliberately external to ``data_root`` and contains no selector, cutover, or
progress-ledger state.  It retains only the snapshot selection and the B1/B2
identities needed to recover an interrupted P3 without minting new snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
from typing import TYPE_CHECKING, Any
from uuid import UUID

from ..canonical_intent import canonical_intent_text
from ..errors import SubstrateConfigurationError
from ..runtime_binding import NativeRepresentationLane
if TYPE_CHECKING:
    from ..corrective_freeze_packet import (
        MetadataLessPerEidEvidence,
        RootSourceScopePlan,
        SourceArtifactPresence,
    )
from .explicit_source_evidence import (
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExplicitSourceEvidence,
    ExplicitSourceEvidenceDrift,
    resolve_explicit_source_evidence_path,
)
from .metadata_less_per_eid_legacy_source import qualify_metadata_less_per_eid_legacy_source
from .rehearsal import MigrationRehearsalConfig, NativeLegacyMigrationRehearsal
from .root_admission_description import (
    MaterializedScopePosture,
    RootNativeProductionAdmissionDescription,
    RootRepresentationDisposition,
)
from .root_normalization import (
    MetadataLessB3BDispatch,
    RootNormalizationRequest,
    RootNormalizationScopeInput,
)
from .root_scope import RootScopeKey, RootScopeKind
from .runtime_motif_projection import MigrationRuntimeMotifProjectionRequest
from .runtime_motif_regeometry_projection import MigrationRuntimeMotifRegeometryProjectionRequest
from .runtime_normalization import (
    MigrationRuntimeNormalizationRequest,
    NativeMigrationRuntimeNormalizationService,
)
from .runtime_readiness import (
    MigrationRuntimeReadinessRequest,
    MigrationRuntimeScopePlan,
    LegacyVectorStrategy,
    NativeMigrationRuntimeReadinessPreflight,
    ObjectRuntimeReadiness,
)
from .runtime_reembedding_bootstrap import MigrationRuntimeReembeddingBootstrapRequest
from .runtime_representation_bootstrap import MigrationRuntimeRepresentationBootstrapRequest
from .runtime_zero_member_motif_projection import MigrationRuntimeZeroMemberMotifProjectionRequest
from .snapshot import (
    complete_snapshot_manifest,
    create_snapshot_manifest,
    load_snapshot_manifest,
    verify_snapshot,
)
from .workspace_runtime_readiness import (
    NativePostWriteQualificationConfiguration,
    WorkspaceNativeEmbedderIdentity,
)


_RECORD_NAME = "p3_source_admission_carrier.json"
_RECORD_SCHEMA = "TORMENT_ROOT_P3_SOURCE_ADMISSION_CARRIER"
_RECORD_VERSION = 1
_COMPLETION_ALLOWED_ROLES = frozenset({
    EvidenceSemanticRole.WORKSPACE_META,
    EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP,
    EvidenceSemanticRole.LEGACY_REPRESENTATION,
})


def _corrective_freeze_types():
    """Load the corrective-freeze-owned runtime classes only after import init."""

    from ..corrective_freeze_packet import (
        MetadataLessPerEidEvidence,
        RootSourceScopePlan,
        SourceArtifactPresence,
    )
    return MetadataLessPerEidEvidence, RootSourceScopePlan, SourceArtifactPresence


class RootP3SourceAdmissionRefused(SubstrateConfigurationError):
    """The P3 source-admission carrier cannot prove an exact input."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class RootP3SourceAdmissionInterruptionPoint(StrEnum):
    """Focused qualification seams; never production semantic inputs."""

    AFTER_SNAPSHOT_SELECTION = "AFTER_SNAPSHOT_SELECTION"
    AFTER_B1 = "AFTER_B1"


class RootP3SourceAdmissionInterrupted(RuntimeError):
    """Test-only interruption after durable carrier evidence."""

    def __init__(self, point: RootP3SourceAdmissionInterruptionPoint) -> None:
        self.point = point
        super().__init__(f"forced root P3 source-admission interruption at {point.value}")


@dataclass(frozen=True)
class RootP3ScopeBinding:
    """One P1-established namespace binding consumed by P3 B1/B2 only."""

    scope_key: RootScopeKey
    scope_plan: MigrationRuntimeScopePlan
    unknown_semantic_scope_id: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.scope_key, RootScopeKey):
            raise ValueError("scope_key must be RootScopeKey")
        if not isinstance(self.scope_plan, MigrationRuntimeScopePlan):
            raise ValueError("scope_plan must be MigrationRuntimeScopePlan")
        if not isinstance(self.unknown_semantic_scope_id, UUID):
            raise ValueError("unknown_semantic_scope_id must be UUID")
        if _scope_key_from_plan(self.scope_plan) != self.scope_key:
            raise ValueError("scope_plan must match scope_key")


@dataclass(frozen=True)
class RootP3SourceAdmissionRequest:
    """One external P3A carrier request, bounded to recovered P1/P2 facts."""

    data_root: str | Path
    native_core_database_path: str | Path
    expected_native_core_id: UUID
    description: RootNativeProductionAdmissionDescription
    source_scope_plans: tuple[RootSourceScopePlan, ...]
    scope_bindings: tuple[RootP3ScopeBinding, ...]
    unknown_identity_evidence: tuple[MetadataLessPerEidEvidence, ...]
    carrier_directory: str | Path
    operation_key: str
    qualification_embedder_identity: WorkspaceNativeEmbedderIdentity
    b3b_embedder: object
    post_write_configurations: tuple[NativePostWriteQualificationConfiguration, ...] = ()
    predecessor_carrier_record_path: str | Path | None = None

    def __post_init__(self) -> None:
        MetadataLessPerEidEvidence, RootSourceScopePlan, _SourceArtifactPresence = _corrective_freeze_types()
        root = _directory(self.data_root, "data_root")
        core = Path(self.native_core_database_path).expanduser().resolve()
        if not core.is_file():
            raise ValueError("native_core_database_path must name an existing database")
        if not isinstance(self.expected_native_core_id, UUID):
            raise ValueError("expected_native_core_id must be UUID")
        if not isinstance(self.description, RootNativeProductionAdmissionDescription):
            raise ValueError("description must be RootNativeProductionAdmissionDescription")
        if self.description.target_representation_lane != self.qualification_embedder_identity_to_lane:
            raise ValueError("qualification embedder identity must match the root target lane")
        if not callable(getattr(self.b3b_embedder, "embed", None)):
            raise ValueError("b3b_embedder must provide embed")
        if not isinstance(self.operation_key, str) or not self.operation_key or len(self.operation_key) > 160:
            raise ValueError("operation_key must be bounded non-empty text")
        if not isinstance(self.source_scope_plans, tuple) or any(
            not isinstance(item, RootSourceScopePlan) for item in self.source_scope_plans
        ):
            raise ValueError("source_scope_plans must be typed")
        if not isinstance(self.scope_bindings, tuple) or any(
            not isinstance(item, RootP3ScopeBinding) for item in self.scope_bindings
        ):
            raise ValueError("scope_bindings must be typed")
        if not isinstance(self.unknown_identity_evidence, tuple) or any(
            not isinstance(item, MetadataLessPerEidEvidence) for item in self.unknown_identity_evidence
        ):
            raise ValueError("unknown_identity_evidence must be typed")
        if not isinstance(self.post_write_configurations, tuple) or any(
            not isinstance(item, NativePostWriteQualificationConfiguration)
            for item in self.post_write_configurations
        ):
            raise ValueError("post_write_configurations must be typed")
        carrier = Path(self.carrier_directory).expanduser().resolve()
        if carrier == root or root in carrier.parents:
            raise ValueError("carrier_directory must resolve outside data_root")
        if not carrier.parent.is_dir():
            raise ValueError("carrier_directory parent must already exist")
        predecessor = self.predecessor_carrier_record_path
        if predecessor is not None:
            if not isinstance(predecessor, (str, Path)) or not str(predecessor).strip():
                raise ValueError("predecessor_carrier_record_path must be an explicit path when supplied")
            predecessor_path = Path(predecessor).expanduser().resolve()
            if not predecessor_path.is_file() or predecessor_path.is_symlink():
                raise ValueError("predecessor_carrier_record_path must name an existing regular record")
            if carrier in predecessor_path.parents:
                raise ValueError("completion carrier must be separate from its predecessor carrier")
        source_by_key = {item.scope_key: item for item in self.source_scope_plans}
        bindings_by_key = {item.scope_key: item for item in self.scope_bindings}
        declared = {
            item.scope_key: item
            for workspace in self.description.workspace_plans
            for item in workspace.runtime_scopes
        }
        if (
            len(source_by_key) != len(self.source_scope_plans)
            or len(bindings_by_key) != len(self.scope_bindings)
            or set(source_by_key) != set(declared)
            or set(bindings_by_key) != set(declared)
        ):
            raise ValueError("P3 source plans and bindings must exactly cover declared runtime scopes")
        for key, declared_plan in declared.items():
            source = source_by_key[key]
            binding = bindings_by_key[key]
            if (
                source.materialization_posture != declared_plan.materialization_posture
                or source.representation_disposition != declared_plan.representation_disposition
                or source.target_representation_lane != self.description.target_representation_lane
                or binding.scope_plan.motif_domain_id != source.motif_domain_id
            ):
                raise ValueError("P3 source plan or namespace binding disagrees with root description")
        unknown = {item.scope_key for item in self.unknown_identity_evidence}
        expected_unknown = {
            key for key, item in source_by_key.items()
            if item.representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY
        }
        if unknown != expected_unknown:
            raise ValueError("metadata-less evidence must exactly cover UNKNOWN_IDENTITY scopes")
        if len({(item.scope_key, item.eid) for item in self.unknown_identity_evidence}) != len(
            self.unknown_identity_evidence
        ):
            raise ValueError("metadata-less evidence must have unique scope/EID pairs")

    @property
    def root(self) -> Path:
        return Path(self.data_root).expanduser().resolve()

    @property
    def carrier_root(self) -> Path:
        return Path(self.carrier_directory).expanduser().resolve()

    @property
    def record_path(self) -> Path:
        return self.carrier_root / _RECORD_NAME

    @property
    def predecessor_record_path(self) -> Path | None:
        if self.predecessor_carrier_record_path is None:
            return None
        return Path(self.predecessor_carrier_record_path).expanduser().resolve()

    @property
    def qualification_embedder_identity_to_lane(self) -> NativeRepresentationLane:
        identity = self.qualification_embedder_identity
        lane = self.description.target_representation_lane
        if (identity.provider, identity.model, identity.dim) != (
            lane.provider, lane.model, lane.dimension,
        ):
            raise ValueError("qualification embedder identity must match the root target lane")
        return lane


@dataclass(frozen=True)
class RootP3SourceAdmissionResult:
    """Exact B1/B2 carrier facts and the newly bound existing B3/B4 request."""

    carrier_record_path: Path
    normalization_request: RootNormalizationRequest
    snapshot_scope_count: int
    b1_memory_count: int
    b2_memory_count: int
    child_request_counts: tuple[tuple[str, int], ...]


class NativeRootP3SourceAdmissionService:
    """Compose existing capture/B1/B2 owners; it grants no P2/P4 authority."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("root P3 source admission requires an open SQLite connection")
        self._connection = connection

    def admit(
        self,
        request: RootP3SourceAdmissionRequest,
        *,
        _test_interrupt_after: RootP3SourceAdmissionInterruptionPoint | None = None,
        _test_lose_response_after_b2: bool = False,
    ) -> RootP3SourceAdmissionResult:
        if not isinstance(request, RootP3SourceAdmissionRequest):
            raise ValueError("request must be RootP3SourceAdmissionRequest")
        if _test_interrupt_after is not None and not isinstance(
            _test_interrupt_after, RootP3SourceAdmissionInterruptionPoint,
        ):
            raise ValueError("_test_interrupt_after must be RootP3SourceAdmissionInterruptionPoint")

        # This recheck is deliberately immediately before any carrier selection
        # or B1 write.  It reads only the P2-bound explicit source proposition.
        _verify_p2_bound_source(request)
        record = _select_or_recover_record(self._connection, request)
        if _test_interrupt_after is RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION:
            raise RootP3SourceAdmissionInterrupted(_test_interrupt_after)

        ordered = _ordered_scope_entries(record)
        b1_interrupted = False
        for entry in ordered:
            if entry.get("b1") is None:
                _run_b1(self._connection, request, entry)
                entry["b1"] = _read_b1_evidence(self._connection, request, entry)
                _write_record(request.record_path, record)
                if (
                    _test_interrupt_after is RootP3SourceAdmissionInterruptionPoint.AFTER_B1
                    and not b1_interrupted
                ):
                    raise RootP3SourceAdmissionInterrupted(_test_interrupt_after)
                b1_interrupted = True

        lose_response = _test_lose_response_after_b2
        for entry in ordered:
            source = _source_plan_for_key(request, _scope_key_from_payload(entry.get("scope_key")))
            memories, _motifs = _carrier_b1_evidence(entry, source)
            b2 = _require_mapping(entry.get("b2"), "P3_CARRIER_B2_EVIDENCE_REQUIRED")
            b2_by_eid = _carrier_b2_memory_evidence(b2)
            memory_eids = {item["eid"] for item in memories}
            if not set(b2_by_eid).issubset(memory_eids):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_B2_EID_SET_MISMATCH")
            for memory in memories:
                eid = memory["eid"]
                if eid in b2_by_eid:
                    continue
                result = NativeMigrationRuntimeNormalizationService(
                    self._connection
                ).normalize_legacy_core_memory(
                    MigrationRuntimeNormalizationRequest(
                        snapshot_root=Path(entry["snapshot_root"]),
                        manifest_path=Path(entry["manifest_path"]),
                        legacy_snapshot_id=UUID(entry["legacy_snapshot_id"]),
                        legacy_source_namespace_id=UUID(entry["legacy_source_namespace_id"]),
                        expected_native_core_id=request.expected_native_core_id,
                        eid=eid,
                        expected_revision_id=UUID(memory["r1_revision_id"]),
                        scope_plans=(request_binding(request, entry).scope_plan,),
                        idempotency_namespace_id=request_binding(request, entry).scope_plan.idempotency_namespace_id,
                        idempotency_key=_stage_key(request, entry, "B2", str(eid)),
                    ),
                    _test_lose_response_after_commit=lose_response,
                )
                lose_response = False
                b2.setdefault("memories", []).append({
                    "eid": eid,
                    "r2_revision_id": str(result.revision_id),
                })
                b2["memories"] = sorted(b2["memories"], key=lambda item: item["eid"])
                b2_by_eid = _carrier_b2_memory_evidence(b2)
                _write_record(request.record_path, record)
            _require_b2_closure(memories, b2_by_eid)

        normalization_request = _build_normalization_request(request, record)
        actual = p3_child_request_counts(normalization_request.scope_inputs)
        expected = _carrier_evidence_child_request_counts(request, record)
        if actual != expected:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_CHILD_COUNT_DRIFT")
        memory_count = sum(
            len(_require_list(_require_mapping(item.get("b1"), "P3_CARRIER_B1_EVIDENCE_REQUIRED").get("memories"), "P3_CARRIER_B1_MEMORY_EVIDENCE_REQUIRED"))
            for item in ordered
        )
        return RootP3SourceAdmissionResult(
            carrier_record_path=request.record_path,
            normalization_request=normalization_request,
            snapshot_scope_count=len(ordered),
            b1_memory_count=memory_count,
            b2_memory_count=sum(
                len(_require_list(_require_mapping(item.get("b2"), "P3_CARRIER_B2_EVIDENCE_REQUIRED").get("memories"), "P3_CARRIER_B2_EVIDENCE_REQUIRED"))
                for item in ordered
            ),
            child_request_counts=tuple(sorted(actual.items())),
        )


def pre_b1_p3_scope_shape_counts(
    source_scope_plans: tuple[RootSourceScopePlan, ...],
    unknown_identity_evidence: tuple[MetadataLessPerEidEvidence, ...],
) -> dict[str, int]:
    """Return pre-B1 structural facts, never executable child-operation counts."""

    MetadataLessPerEidEvidence, RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    if not isinstance(source_scope_plans, tuple) or any(
        not isinstance(item, RootSourceScopePlan) for item in source_scope_plans
    ):
        raise ValueError("source_scope_plans must be typed")
    if not isinstance(unknown_identity_evidence, tuple) or any(
        not isinstance(item, MetadataLessPerEidEvidence) for item in unknown_identity_evidence
    ):
        raise ValueError("unknown_identity_evidence must be typed")
    result = {
        "target_compatible_memory_scope_count": 0,
        "ordinary_reembed_memory_scope_count": 0,
        "unknown_identity_evidence_count": len(unknown_identity_evidence),
        "motif_present_scope_count": 0,
    }
    for plan in source_scope_plans:
        if plan.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH:
            if plan.representation_disposition is RootRepresentationDisposition.TARGET_COMPATIBLE:
                result["target_compatible_memory_scope_count"] += 1
            elif plan.representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY:
                continue
            else:
                result["ordinary_reembed_memory_scope_count"] += 1
        if plan.motif_presence is SourceArtifactPresence.PRESENT:
            result["motif_present_scope_count"] += 1
    return result


def p3_child_request_counts(
    scope_inputs: tuple[RootNormalizationScopeInput, ...],
) -> dict[str, int]:
    """Count the exact B3/B4 inputs produced by this carrier."""

    if not isinstance(scope_inputs, tuple) or any(
        not isinstance(item, RootNormalizationScopeInput) for item in scope_inputs
    ):
        raise ValueError("scope_inputs must be typed")
    result = {
        "b3a": 0, "ordinary_b3b": 0, "metadata_less_b3b": 0,
        "total_b3b": 0, "b4a": 0, "b4b": 0, "b4c": 0,
    }
    for item in scope_inputs:
        result["b3a"] += len(item.b3a_requests)
        result["ordinary_b3b"] += len(item.b3b_requests)
        result["metadata_less_b3b"] += len(item.metadata_less_b3b_dispatches)
        result["b4a"] += len(item.b4a_requests)
        result["b4b"] += len(item.b4b_requests)
        result["b4c"] += len(item.b4c_requests)
    result["total_b3b"] = result["ordinary_b3b"] + result["metadata_less_b3b"]
    return result


def request_binding(request: RootP3SourceAdmissionRequest, entry: dict[str, Any]) -> RootP3ScopeBinding:
    key = _scope_key_from_payload(entry.get("scope_key"))
    matches = [item for item in request.scope_bindings if item.scope_key == key]
    if len(matches) != 1:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SCOPE_BINDING_MISSING")
    return matches[0]


def _verify_p2_bound_source(request: RootP3SourceAdmissionRequest) -> None:
    try:
        request.description.explicit_source_manifest.verify(data_root=request.root)
    except (ExplicitSourceEvidenceDrift, OSError, ValueError) as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_MANIFEST_DRIFT") from exc


def _select_or_recover_record(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
) -> dict[str, Any]:
    path = request.record_path
    if path.exists():
        record = _load_record(path, request)
        _verify_record_snapshots(connection, record, request)
        return record
    if request.predecessor_record_path is not None:
        return _complete_predecessor_record(connection, request)
    p1_namespace_keys = {
        binding.scope_key: _p1_legacy_source_namespace_key(
            connection, binding.scope_plan.legacy_source_namespace_id,
        )
        for binding in request.scope_bindings
    }
    carrier = request.carrier_root
    if carrier.exists():
        if not carrier.is_dir() or carrier.is_symlink() or any(carrier.iterdir()):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_DESTINATION_NOT_EMPTY")
    else:
        carrier.mkdir()
    (carrier / "snapshots").mkdir()
    (carrier / "manifests").mkdir()
    scopes: list[dict[str, Any]] = []
    source_by_key = {item.scope_key: item for item in request.source_scope_plans}
    for index, binding in enumerate(sorted(request.scope_bindings, key=lambda item: item.scope_key.canonical_key)):
        token = f"{index:03d}-{_scope_token(binding.scope_key)}"
        snapshot_root = carrier / "snapshots" / token
        manifest_path = carrier / "manifests" / f"{token}.json"
        _create_scope_snapshot(
            request,
            source_by_key[binding.scope_key],
            binding,
            p1_namespace_keys[binding.scope_key],
            snapshot_root,
            manifest_path,
        )
        manifest = load_snapshot_manifest(manifest_path)
        scopes.append({
            "scope_key": binding.scope_key.identity_payload(),
            "scope_plan": binding.scope_plan.intent(),
            "unknown_semantic_scope_id": str(binding.unknown_semantic_scope_id),
            "legacy_source_namespace_id": str(binding.scope_plan.legacy_source_namespace_id),
            "legacy_source_namespace_key": manifest.legacy_source_namespace_key,
            "snapshot_root": str(snapshot_root),
            "manifest_path": str(manifest_path),
            "legacy_snapshot_id": str(manifest.legacy_snapshot_id),
            "manifest_digest": _file_digest(manifest_path),
            "b1": None,
            "b2": {"memories": []},
        })
    record: dict[str, Any] = {
        "root_description_digest": request.description.identity_digest,
        "explicit_source_manifest_digest": request.description.explicit_source_manifest.digest,
        "expected_native_core_id": str(request.expected_native_core_id),
        "operation_key": request.operation_key,
        "scopes": scopes,
    }
    _write_record(path, record)
    return record


def _complete_predecessor_record(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
) -> dict[str, Any]:
    """Create a separate carrier that only completes omitted source evidence.

    The first carrier, its snapshots, manifests, and B1 facts stay immutable.
    A successor carrier can share a snapshot identity only through the strict
    snapshot completion law, which retains every predecessor artifact exactly.
    Scopes without an omission continue to reference their predecessor
    snapshots rather than manufacturing a non-strict "completion" manifest.
    """

    predecessor_path = request.predecessor_record_path
    assert predecessor_path is not None
    predecessor, predecessor_digest = _load_predecessor_record(predecessor_path)
    _verify_predecessor_record(connection, predecessor, request)
    carrier = request.carrier_root
    if carrier.exists():
        if not carrier.is_dir() or carrier.is_symlink() or any(carrier.iterdir()):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_DESTINATION_NOT_EMPTY")
    else:
        carrier.mkdir()
    (carrier / "completed_snapshots").mkdir()
    (carrier / "completed_manifests").mkdir()
    predecessor_by_key = {
        _scope_key_from_payload(item.get("scope_key")): item
        for item in _require_list(predecessor.get("scopes"), "P3_CARRIER_PREDECESSOR_SCOPE_SET_INVALID")
    }
    p1_namespace_keys = {
        binding.scope_key: _p1_legacy_source_namespace_key(
            connection, binding.scope_plan.legacy_source_namespace_id,
        )
        for binding in request.scope_bindings
    }
    source_by_key = {item.scope_key: item for item in request.source_scope_plans}
    scopes: list[dict[str, Any]] = []
    completed: list[dict[str, Any]] = []
    inherited: list[dict[str, Any]] = []
    for index, binding in enumerate(sorted(request.scope_bindings, key=lambda item: item.scope_key.canonical_key)):
        predecessor_entry = predecessor_by_key.get(binding.scope_key)
        if predecessor_entry is None:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_SCOPE_SET_INVALID")
        token = f"{index:03d}-{_scope_token(binding.scope_key)}"
        snapshot_root, manifest_path, completion = _complete_scope_snapshot(
            request=request,
            source_plan=source_by_key[binding.scope_key],
            predecessor_entry=predecessor_entry,
            destination=carrier / "completed_snapshots" / token,
            manifest_destination=carrier / "completed_manifests" / f"{token}.json",
        )
        manifest = load_snapshot_manifest(manifest_path)
        scope = {
            "scope_key": binding.scope_key.identity_payload(),
            "scope_plan": binding.scope_plan.intent(),
            "unknown_semantic_scope_id": str(binding.unknown_semantic_scope_id),
            "legacy_source_namespace_id": str(binding.scope_plan.legacy_source_namespace_id),
            "legacy_source_namespace_key": p1_namespace_keys[binding.scope_key],
            "snapshot_root": str(snapshot_root),
            "manifest_path": str(manifest_path),
            "legacy_snapshot_id": str(manifest.legacy_snapshot_id),
            "manifest_digest": _file_digest(manifest_path),
            # Re-read B1 under the completed evidence.  Native admission is
            # idempotent on the preserved snapshot/EID identity, so this
            # recovers rather than duplicates R1 objects.
            "b1": None,
            "b2": {"memories": []},
        }
        scopes.append(scope)
        (completed if completion else inherited).append({
            "scope_key": binding.scope_key.identity_payload(),
            "snapshot_root": str(snapshot_root),
            "manifest_path": str(manifest_path),
            "legacy_snapshot_id": str(manifest.legacy_snapshot_id),
        })
    record: dict[str, Any] = {
        "root_description_digest": request.description.identity_digest,
        "explicit_source_manifest_digest": request.description.explicit_source_manifest.digest,
        "expected_native_core_id": str(request.expected_native_core_id),
        "operation_key": request.operation_key,
        "scopes": scopes,
        "carrier_completion": {
            "predecessor_record_path": str(predecessor_path),
            "predecessor_record_digest": predecessor_digest,
            "completed_snapshots": completed,
            "completed_manifests": [item["manifest_path"] for item in completed],
            "inherited_snapshots": inherited,
        },
    }
    _write_record(request.record_path, record)
    return record


def _load_predecessor_record(path: Path) -> tuple[dict[str, Any], str]:
    try:
        outer = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_RECORD_UNREADABLE") from exc
    if not isinstance(outer, dict) or set(outer) != {"schema", "version", "payload", "digest"}:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_RECORD_SHAPE_INVALID")
    payload = outer.get("payload")
    if (
        outer.get("schema") != _RECORD_SCHEMA
        or outer.get("version") != _RECORD_VERSION
        or not isinstance(payload, dict)
        or outer.get("digest") != _digest(payload)
    ):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_RECORD_INTEGRITY_INVALID")
    return payload, str(outer["digest"])


def _verify_predecessor_record(
    connection: sqlite3.Connection,
    predecessor: dict[str, Any],
    request: RootP3SourceAdmissionRequest,
) -> None:
    if predecessor.get("expected_native_core_id") != str(request.expected_native_core_id):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_CORE_MISMATCH")
    scopes = _require_list(predecessor.get("scopes"), "P3_CARRIER_PREDECESSOR_SCOPE_SET_INVALID")
    keys = {
        _scope_key_from_payload(item.get("scope_key"))
        for item in scopes
        if isinstance(item, dict)
    }
    if len(keys) != len(scopes) or keys != {item.scope_key for item in request.scope_bindings}:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_SCOPE_SET_INVALID")
    for entry in scopes:
        if not isinstance(entry, dict):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_SCOPE_SET_INVALID")
        binding = request_binding(request, entry)
        expected_key = _p1_legacy_source_namespace_key(
            connection, binding.scope_plan.legacy_source_namespace_id,
        )
        root = Path(entry.get("snapshot_root", "")).expanduser().resolve()
        manifest_path = Path(entry.get("manifest_path", "")).expanduser().resolve()
        try:
            manifest = load_snapshot_manifest(manifest_path)
            verify_snapshot(snapshot_root=root, manifest=manifest)
        except (SubstrateConfigurationError, OSError, ValueError) as exc:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_SNAPSHOT_INVALID") from exc
        if (
            manifest.legacy_source_namespace_id != binding.scope_plan.legacy_source_namespace_id
            or manifest.legacy_source_namespace_key != expected_key
            or entry.get("legacy_snapshot_id") != str(manifest.legacy_snapshot_id)
            or entry.get("manifest_digest") != _file_digest(manifest_path)
        ):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_SNAPSHOT_BINDING_MISMATCH")


def _complete_scope_snapshot(
    *,
    request: RootP3SourceAdmissionRequest,
    source_plan: RootSourceScopePlan,
    predecessor_entry: dict[str, Any],
    destination: Path,
    manifest_destination: Path,
) -> tuple[Path, Path, bool]:
    predecessor_root = Path(predecessor_entry.get("snapshot_root", "")).expanduser().resolve()
    predecessor_manifest_path = Path(predecessor_entry.get("manifest_path", "")).expanduser().resolve()
    predecessor_manifest = load_snapshot_manifest(predecessor_manifest_path)
    selected = _snapshot_sources_for_scope(request, source_plan)
    predecessor_locators = {item.observed_relative_locator for item in predecessor_manifest.artifacts}
    additions: list[tuple[ExplicitSourceEvidence, Path]] = []
    for evidence, relative in selected:
        if relative.as_posix() in predecessor_locators:
            continue
        if evidence.semantic_role not in _COMPLETION_ALLOWED_ROLES:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_UNAPPROVED_ADDITION")
        additions.append((evidence, relative))
    if not additions:
        return predecessor_root, predecessor_manifest_path, False
    if destination.exists() or manifest_destination.exists():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_DESTINATION_EXISTS")
    temporary = destination.parent / f".{destination.name}.pending"
    if temporary.exists():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_INCOMPLETE_CAPTURE")
    temporary.mkdir()
    try:
        for artifact in predecessor_manifest.artifacts:
            source = predecessor_root / artifact.observed_relative_locator
            _require_regular_source_inside_root(predecessor_root, source)
            target = temporary / artifact.observed_relative_locator
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        for evidence, relative in selected:
            source = resolve_explicit_source_evidence_path(data_root=request.root, evidence=evidence)
            _require_regular_source_inside_root(request.root, source)
            payload = source.read_bytes()
            if len(payload) != evidence.byte_length or hashlib.sha256(payload).hexdigest() != evidence.sha256_hex:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SOURCE_EVIDENCE_DRIFT")
            target = temporary / relative
            if target.exists():
                if target.read_bytes() != payload:
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_PREDECESSOR_DRIFT")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        completed = complete_snapshot_manifest(
            predecessor=predecessor_manifest,
            snapshot_root=temporary,
            manifest_path=manifest_destination,
            allowed_additional_locators=tuple(relative.as_posix() for _, relative in additions),
        )
        verify_snapshot(snapshot_root=temporary, manifest=completed)
        os.replace(temporary, destination)
    except Exception:
        raise
    return destination, manifest_destination, True


def _create_scope_snapshot(
    request: RootP3SourceAdmissionRequest,
    source_plan: RootSourceScopePlan,
    binding: RootP3ScopeBinding,
    legacy_source_namespace_key: str,
    destination: Path,
    manifest_path: Path,
) -> None:
    if destination.exists() or manifest_path.exists():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SNAPSHOT_DESTINATION_EXISTS")
    temporary = destination.parent / f".{destination.name}.pending"
    temporary_manifest = manifest_path.parent / f".{manifest_path.stem}.pending.json"
    if temporary.exists() or temporary_manifest.exists():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_INCOMPLETE_SNAPSHOT_CAPTURE")
    temporary.mkdir()
    try:
        for evidence, relative in _snapshot_sources_for_scope(request, source_plan):
            source = resolve_explicit_source_evidence_path(data_root=request.root, evidence=evidence)
            _require_regular_source_inside_root(request.root, source)
            payload = source.read_bytes()
            if len(payload) != evidence.byte_length or hashlib.sha256(payload).hexdigest() != evidence.sha256_hex:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_EVIDENCE_DRIFT")
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        manifest = create_snapshot_manifest(
            snapshot_root=temporary,
            manifest_path=temporary_manifest,
            legacy_source_namespace_id=binding.scope_plan.legacy_source_namespace_id,
            legacy_source_namespace_key=legacy_source_namespace_key,
            capture_label=f"root P3 source admission {binding.scope_key.canonical_key}",
        )
        verify_snapshot(snapshot_root=temporary, manifest=manifest)
        os.replace(temporary, destination)
        os.replace(temporary_manifest, manifest_path)
    except Exception:
        # Do not remove incomplete captures: absence of an authoritative record
        # plus residue must fail closed rather than silently choose new IDs.
        raise


def _snapshot_sources_for_scope(
    request: RootP3SourceAdmissionRequest,
    source_plan: RootSourceScopePlan,
) -> tuple[tuple[ExplicitSourceEvidence, Path], ...]:
    _MetadataLessPerEidEvidence, _RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    scope = source_plan.scope_key
    manifest = request.description.explicit_source_manifest
    selected: list[tuple[ExplicitSourceEvidence, Path]] = []
    roles = {
        EvidenceSemanticRole.NODES,
        EvidenceSemanticRole.EDGES,
        EvidenceSemanticRole.EMBEDDING_MANIFEST,
        EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP,
        EvidenceSemanticRole.LEGACY_REPRESENTATION,
        EvidenceSemanticRole.MOTIFS,
        EvidenceSemanticRole.WORKSPACE_META,
    }
    for item in manifest.entries:
        if item.presence_expectation is not EvidencePresenceExpectation.EXPECTED_PRESENT:
            continue
        include = item.scope_key == scope
        if (
            item.scope_key is None
            and item.owner_boundary.workspace_id == scope.workspace_id
            and item.semantic_role is EvidenceSemanticRole.WORKSPACE_META
            and (
                source_plan.motif_presence is SourceArtifactPresence.PRESENT
                or (
                    source_plan.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH
                    and source_plan.representation_disposition
                    is not RootRepresentationDisposition.UNKNOWN_IDENTITY
                )
            )
        ):
            include = True
        if not include:
            continue
        if item.semantic_role not in roles:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_UNSUPPORTED_DECLARED_SOURCE_ROLE")
        relative = _snapshot_relative_path(item, scope)
        selected.append((item, relative))
    destinations = [relative.as_posix() for _, relative in selected]
    if len(set(destinations)) != len(destinations):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SNAPSHOT_DESTINATION_AMBIGUOUS")
    if source_plan.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH and not any(
        item.semantic_role is EvidenceSemanticRole.NODES for item, _ in selected
    ):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_SOURCE_MISSING")
    if source_plan.motif_presence is SourceArtifactPresence.PRESENT and not any(
        item.semantic_role is EvidenceSemanticRole.MOTIFS for item, _ in selected
    ):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_SOURCE_MISSING")
    return tuple(sorted(selected, key=lambda item: item[1].as_posix()))


def _snapshot_relative_path(evidence: ExplicitSourceEvidence, scope: RootScopeKey) -> Path:
    if evidence.semantic_role in {
        EvidenceSemanticRole.NODES,
        EvidenceSemanticRole.EDGES,
        EvidenceSemanticRole.EMBEDDING_MANIFEST,
        EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP,
        EvidenceSemanticRole.LEGACY_REPRESENTATION,
    }:
        if evidence.owner_boundary.scope_key != scope:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_SCOPE_SOURCE_BOUNDARY_MISMATCH")
        return Path(*evidence.canonical_locator.split("/"))
    if evidence.semantic_role is EvidenceSemanticRole.MOTIFS:
        domain = evidence.owner_boundary.domain_id
        if domain is None or domain != scope.domain_id:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_SOURCE_BOUNDARY_MISMATCH")
        return Path("workspaces", scope.workspace_id, "domains", domain, *evidence.canonical_locator.split("/"))
    if evidence.semantic_role is EvidenceSemanticRole.WORKSPACE_META:
        if evidence.owner_boundary.workspace_id != scope.workspace_id:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_WORKSPACE_SOURCE_BOUNDARY_MISMATCH")
        return Path("workspaces", scope.workspace_id, *evidence.canonical_locator.split("/"))
    raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_ROLE_UNSUPPORTED")


def _run_b1(connection: sqlite3.Connection, request: RootP3SourceAdmissionRequest, entry: dict[str, Any]) -> None:
    binding = request_binding(request, entry)
    NativeLegacyMigrationRehearsal(connection).run(
        snapshot_root=Path(entry["snapshot_root"]),
        manifest_path=Path(entry["manifest_path"]),
        config=MigrationRehearsalConfig(
            native_core_id=request.expected_native_core_id,
            idempotency_namespace_id=binding.scope_plan.idempotency_namespace_id,
            object_identity_namespace_id=binding.scope_plan.target_identity_namespace_id,
            relationship_identity_namespace_id=binding.scope_plan.membership_identity_namespace_id,
            unknown_semantic_scope_id=binding.unknown_semantic_scope_id,
        ),
    )


def _read_b1_evidence(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
    entry: dict[str, Any],
) -> dict[str, Any]:
    _MetadataLessPerEidEvidence, _RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    binding = request_binding(request, entry)
    source_plan = _source_plan_for_key(request, binding.scope_key)
    report = NativeMigrationRuntimeReadinessPreflight(connection).run(
        MigrationRuntimeReadinessRequest(
            legacy_snapshot_id=UUID(entry["legacy_snapshot_id"]),
            expected_native_core_id=request.expected_native_core_id,
            scope_plans=(binding.scope_plan,),
            target_lane=request.description.target_representation_lane,
        )
    )
    memories: list[dict[str, Any]] = []
    if source_plan.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH:
        allowed = {
            ObjectRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED,
            ObjectRuntimeReadiness.REPRESENTATION_BOOTSTRAP_REQUIRED,
        }
        seen_eids: set[int] = set()
        for item in report.object_items:
            if item.eid is None:
                # Motifs are independently represented in the same frozen
                # snapshot but are not logical memories.  They are explicitly
                # marked evidence-only by the existing readiness owner and
                # are closed below through ``report.motif_items``.
                if (
                    item.readiness is ObjectRuntimeReadiness.EVIDENCE_ONLY_NOT_RUNTIME_OBJECT
                    and "OBJECT_KIND_NOT_CORE_RUNTIME_PROFILE" in item.reason_codes
                ):
                    continue
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_EID_INVALID")
            eid = _require_nonnegative_int(item.eid, "P3_CARRIER_MEMORY_B1_EID_INVALID")
            if eid in seen_eids:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_EID_DUPLICATE")
            if not isinstance(item.current_revision_id, UUID):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_REVISION_INVALID")
            if item.readiness not in allowed:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_NOT_NORMALIZABLE")
            seen_eids.add(eid)
            if not isinstance(item.legacy_vector_strategy, LegacyVectorStrategy):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_STRATEGY_INVALID")
            memories.append({
                "eid": eid,
                "r1_revision_id": str(item.current_revision_id),
                "legacy_vector_strategy": item.legacy_vector_strategy.value,
            })
        memories.sort(key=lambda item: item["eid"])
        if not memories:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_CLOSURE_MISMATCH")
    elif any(item.eid is not None for item in report.object_items):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_EMPTY_SCOPE_CREATED_MEMORY")
    motifs: list[dict[str, Any]] = []
    if source_plan.motif_presence is SourceArtifactPresence.PRESENT:
        if not report.motif_items:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_CLOSURE_MISMATCH")
        seen_runtime_motif_ids: set[str] = set()
        for item in report.motif_items:
            runtime_motif_id = item.runtime_motif_id
            if not isinstance(runtime_motif_id, str) or not runtime_motif_id:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_RUNTIME_ID_INVALID")
            if runtime_motif_id in seen_runtime_motif_ids:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_RUNTIME_ID_DUPLICATE")
            if not isinstance(item.motif_object_id, UUID):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_SOURCE_OBJECT_INVALID")
            if not isinstance(item.current_revision_id, UUID):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_REVISION_INVALID")
            seen_runtime_motif_ids.add(runtime_motif_id)
            motifs.append({
                "runtime_motif_id": runtime_motif_id,
                "source_object_id": str(item.motif_object_id),
                "r1_revision_id": str(item.current_revision_id),
            })
        motifs.sort(key=lambda item: item["runtime_motif_id"])
        if len(motifs) != len(report.motif_items):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_CLOSURE_MISMATCH")
    elif report.motif_items:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_UNDECLARED_MOTIF_ADMITTED")
    return {"memories": memories, "motifs": motifs}


def _carrier_b1_evidence(
    entry: dict[str, Any], source_plan: RootSourceScopePlan,
) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    """Validate recovered B1 evidence before it can drive B2/B3/B4 work."""

    _MetadataLessPerEidEvidence, _RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    b1 = _require_mapping(entry.get("b1"), "P3_CARRIER_B1_EVIDENCE_REQUIRED")
    memories = _carrier_b1_memory_evidence(b1)
    motifs = _carrier_b1_motif_evidence(b1)
    if source_plan.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH:
        if not memories:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_CLOSURE_MISMATCH")
    elif memories:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_EMPTY_SCOPE_CREATED_MEMORY")
    if source_plan.motif_presence is SourceArtifactPresence.PRESENT:
        if not motifs:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_CLOSURE_MISMATCH")
    elif motifs:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_UNDECLARED_MOTIF_ADMITTED")
    return memories, motifs


def _carrier_b1_memory_evidence(b1: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    memories = _require_list(b1.get("memories"), "P3_CARRIER_B1_MEMORY_EVIDENCE_REQUIRED")
    result: list[dict[str, Any]] = []
    seen_eids: set[int] = set()
    for memory in memories:
        eid = _require_nonnegative_int(memory.get("eid"), "P3_CARRIER_B1_MEMORY_EID_INVALID")
        if eid in seen_eids:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_MEMORY_EID_DUPLICATE")
        revision = _require_uuid(memory.get("r1_revision_id"), "P3_CARRIER_B1_MEMORY_REVISION_INVALID")
        try:
            strategy = LegacyVectorStrategy(memory.get("legacy_vector_strategy"))
        except (TypeError, ValueError) as exc:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_MEMORY_STRATEGY_INVALID") from exc
        seen_eids.add(eid)
        result.append({
            "eid": eid,
            "r1_revision_id": str(revision),
            "legacy_vector_strategy": strategy.value,
        })
    return tuple(sorted(result, key=lambda item: item["eid"]))


def _carrier_b1_motif_evidence(b1: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    motifs = _require_list(b1.get("motifs"), "P3_CARRIER_B1_MOTIF_EVIDENCE_REQUIRED")
    result: list[dict[str, Any]] = []
    seen_runtime_motif_ids: set[str] = set()
    for motif in motifs:
        runtime_motif_id = motif.get("runtime_motif_id")
        if not isinstance(runtime_motif_id, str) or not runtime_motif_id:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_MOTIF_RUNTIME_ID_INVALID")
        if runtime_motif_id in seen_runtime_motif_ids:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_MOTIF_RUNTIME_ID_DUPLICATE")
        source_object_id = _require_uuid(
            motif.get("source_object_id"), "P3_CARRIER_B1_MOTIF_SOURCE_OBJECT_INVALID",
        )
        revision = _require_uuid(
            motif.get("r1_revision_id"), "P3_CARRIER_B1_MOTIF_REVISION_INVALID",
        )
        seen_runtime_motif_ids.add(runtime_motif_id)
        result.append({
            "runtime_motif_id": runtime_motif_id,
            "source_object_id": str(source_object_id),
            "r1_revision_id": str(revision),
        })
    return tuple(sorted(result, key=lambda item: item["runtime_motif_id"]))


def _carrier_b2_memory_evidence(b2: dict[str, Any]) -> dict[int, dict[str, Any]]:
    memories = _require_list(b2.get("memories"), "P3_CARRIER_B2_MEMORY_EVIDENCE_REQUIRED")
    result: dict[int, dict[str, Any]] = {}
    for memory in memories:
        eid = _require_nonnegative_int(memory.get("eid"), "P3_CARRIER_B2_MEMORY_EID_INVALID")
        if eid in result:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B2_MEMORY_EID_DUPLICATE")
        revision = _require_uuid(memory.get("r2_revision_id"), "P3_CARRIER_B2_MEMORY_REVISION_INVALID")
        result[eid] = {"eid": eid, "r2_revision_id": str(revision)}
    return result


def _require_b2_closure(
    memories: tuple[dict[str, Any], ...], b2_by_eid: dict[int, dict[str, Any]],
) -> None:
    if {item["eid"] for item in memories} != set(b2_by_eid):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_B2_EID_SET_MISMATCH")


def _build_normalization_request(
    request: RootP3SourceAdmissionRequest, record: dict[str, Any],
) -> RootNormalizationRequest:
    _MetadataLessPerEidEvidence, _RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    inputs: list[RootNormalizationScopeInput] = []
    unknown_by_scope_eid = _unknown_evidence_by_scope_eid(request)
    for entry in _ordered_scope_entries(record):
        binding = request_binding(request, entry)
        source = _source_plan_for_key(request, binding.scope_key)
        memories, motifs = _carrier_b1_evidence(entry, source)
        b2 = _require_mapping(entry.get("b2"), "P3_CARRIER_B2_EVIDENCE_REQUIRED")
        b2_by_eid = _carrier_b2_memory_evidence(b2)
        _require_b2_closure(memories, b2_by_eid)
        b3a: list[MigrationRuntimeRepresentationBootstrapRequest] = []
        b3b: list[MigrationRuntimeReembeddingBootstrapRequest] = []
        metadata_dispatches: list[MetadataLessB3BDispatch] = []
        if source.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH:
            if source.representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY:
                _require_unknown_eid_closure(binding.scope_key, memories, unknown_by_scope_eid)
            for memory in memories:
                eid = memory["eid"]
                b2_memory = b2_by_eid.get(eid)
                if b2_memory is None:
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_B3_REQUIRES_B2_FACT")
                common = dict(
                    snapshot_root=Path(entry["snapshot_root"]),
                    manifest_path=Path(entry["manifest_path"]),
                    legacy_snapshot_id=UUID(entry["legacy_snapshot_id"]),
                    legacy_source_namespace_id=binding.scope_plan.legacy_source_namespace_id,
                    expected_native_core_id=request.expected_native_core_id,
                    eid=eid,
                    expected_r1_revision_id=UUID(memory["r1_revision_id"]),
                    expected_r2_revision_id=UUID(b2_memory["r2_revision_id"]),
                    target_lane=request.description.target_representation_lane,
                    idempotency_namespace_id=binding.scope_plan.idempotency_namespace_id,
                )
                strategy = LegacyVectorStrategy(memory["legacy_vector_strategy"])
                if strategy is LegacyVectorStrategy.BYTE_DERIVATION_POSSIBLE:
                    b3a.append(MigrationRuntimeRepresentationBootstrapRequest(
                        **common,
                        idempotency_key=_stage_key(request, entry, "B3A", str(eid)),
                    ))
                elif source.representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY:
                    evidence = unknown_by_scope_eid[(binding.scope_key, eid)]
                    try:
                        qualified = qualify_metadata_less_per_eid_legacy_source(
                            data_root=request.root,
                            scope_key=binding.scope_key,
                            legacy_eid=eid,
                            legacy_source_namespace_id=binding.scope_plan.legacy_source_namespace_id,
                            target_identity_namespace_id=binding.scope_plan.target_identity_namespace_id,
                            nodes_source=evidence.canonical_text_evidence,
                            optional_edges_source=_optional_edges_source(request, binding.scope_key),
                            legacy_representation_source=evidence.vector_evidence,
                        )
                    except (SubstrateConfigurationError, OSError, ValueError) as exc:
                        raise RootP3SourceAdmissionRefused("P3_CARRIER_METADATA_LESS_SOURCE_REFUSED") from exc
                    b3b_request = MigrationRuntimeReembeddingBootstrapRequest(
                        **common,
                        scope_plans=(binding.scope_plan,),
                        idempotency_key=_stage_key(request, entry, "B3B_METADATA_LESS", str(eid)),
                    )
                    metadata_dispatches.append(MetadataLessB3BDispatch(qualified, b3b_request))
                else:
                    b3b.append(MigrationRuntimeReembeddingBootstrapRequest(
                        **common,
                        scope_plans=(binding.scope_plan,),
                        idempotency_key=_stage_key(request, entry, "B3B", str(eid)),
                    ))

        b4a: list[MigrationRuntimeMotifProjectionRequest] = []
        b4b: list[MigrationRuntimeMotifRegeometryProjectionRequest] = []
        b4c: list[MigrationRuntimeZeroMemberMotifProjectionRequest] = []
        if source.motif_presence is SourceArtifactPresence.PRESENT:
            for motif in motifs:
                common_motif = dict(
                    snapshot_root=Path(entry["snapshot_root"]),
                    manifest_path=Path(entry["manifest_path"]),
                    legacy_snapshot_id=UUID(entry["legacy_snapshot_id"]),
                    legacy_source_namespace_id=binding.scope_plan.legacy_source_namespace_id,
                    expected_native_core_id=request.expected_native_core_id,
                    runtime_motif_id=motif["runtime_motif_id"],
                    expected_source_motif_object_id=UUID(motif["source_object_id"]),
                    expected_source_motif_revision_id=UUID(motif["r1_revision_id"]),
                    scope_plans=(binding.scope_plan,),
                    target_lane=request.description.target_representation_lane,
                    idempotency_namespace_id=binding.scope_plan.idempotency_namespace_id,
                )
                if source.materialization_posture in {
                    MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF,
                    MaterializedScopePosture.DECLARED_EMPTY_SHARED,
                }:
                    b4c.append(MigrationRuntimeZeroMemberMotifProjectionRequest(
                        **common_motif,
                        idempotency_key=_stage_key(request, entry, "B4C", str(motif["runtime_motif_id"])),
                    ))
                elif source.representation_disposition is RootRepresentationDisposition.TARGET_COMPATIBLE:
                    b4a.append(MigrationRuntimeMotifProjectionRequest(
                        **common_motif,
                        idempotency_key=_stage_key(request, entry, "B4A", str(motif["runtime_motif_id"])),
                    ))
                else:
                    b4b.append(MigrationRuntimeMotifRegeometryProjectionRequest(
                        **common_motif,
                        idempotency_key=_stage_key(request, entry, "B4B", str(motif["runtime_motif_id"])),
                    ))
        inputs.append(RootNormalizationScopeInput(
            scope_key=binding.scope_key,
            scope_plan=binding.scope_plan,
            legacy_snapshot_id=UUID(entry["legacy_snapshot_id"]),
            b3a_requests=tuple(b3a),
            b3b_requests=tuple(b3b),
            metadata_less_b3b_dispatches=tuple(metadata_dispatches),
            b4a_requests=tuple(b4a),
            b4b_requests=tuple(b4b),
            b4c_requests=tuple(b4c),
        ))
    return RootNormalizationRequest(
        description=request.description,
        data_root=request.root,
        native_core_database_path=request.native_core_database_path,
        expected_native_core_id=request.expected_native_core_id,
        scope_inputs=tuple(sorted(inputs, key=lambda item: item.scope_key.canonical_key)),
        qualification_embedder_identity=request.qualification_embedder_identity,
        b3b_embedder=request.b3b_embedder,
        post_write_configurations=request.post_write_configurations,
    )


def _unknown_evidence_by_scope_eid(
    request: RootP3SourceAdmissionRequest,
) -> dict[tuple[RootScopeKey, int], MetadataLessPerEidEvidence]:
    result: dict[tuple[RootScopeKey, int], MetadataLessPerEidEvidence] = {}
    for evidence in request.unknown_identity_evidence:
        key = (evidence.scope_key, evidence.eid)
        if key in result:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_UNKNOWN_IDENTITY_EID_DUPLICATE")
        result[key] = evidence
    return result


def _require_unknown_eid_closure(
    scope_key: RootScopeKey,
    memories: tuple[dict[str, Any], ...],
    unknown_by_scope_eid: dict[tuple[RootScopeKey, int], MetadataLessPerEidEvidence],
) -> None:
    memory_eids = {item["eid"] for item in memories}
    evidence_eids = {
        eid for candidate_scope, eid in unknown_by_scope_eid
        if candidate_scope == scope_key
    }
    if memory_eids != evidence_eids:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_UNKNOWN_IDENTITY_EID_SET_MISMATCH")


def _carrier_evidence_child_request_counts(
    request: RootP3SourceAdmissionRequest, record: dict[str, Any],
) -> dict[str, int]:
    """Derive executable B3/B4 counts only from completed carrier evidence."""

    _MetadataLessPerEidEvidence, _RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    unknown_by_scope_eid = _unknown_evidence_by_scope_eid(request)
    result = {
        "b3a": 0, "ordinary_b3b": 0, "metadata_less_b3b": 0,
        "total_b3b": 0, "b4a": 0, "b4b": 0, "b4c": 0,
    }
    for entry in _ordered_scope_entries(record):
        scope_key = _scope_key_from_payload(entry.get("scope_key"))
        source = _source_plan_for_key(request, scope_key)
        memories, motifs = _carrier_b1_evidence(entry, source)
        b2 = _require_mapping(entry.get("b2"), "P3_CARRIER_B2_EVIDENCE_REQUIRED")
        _require_b2_closure(memories, _carrier_b2_memory_evidence(b2))
        if source.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH:
            if source.representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY:
                _require_unknown_eid_closure(scope_key, memories, unknown_by_scope_eid)
                result["metadata_less_b3b"] += len(memories)
            else:
                for memory in memories:
                    strategy = LegacyVectorStrategy(memory["legacy_vector_strategy"])
                    if strategy is LegacyVectorStrategy.BYTE_DERIVATION_POSSIBLE:
                        result["b3a"] += 1
                    else:
                        result["ordinary_b3b"] += 1
        if source.motif_presence is SourceArtifactPresence.PRESENT:
            if source.materialization_posture in {
                MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF,
                MaterializedScopePosture.DECLARED_EMPTY_SHARED,
            }:
                result["b4c"] += len(motifs)
            elif source.representation_disposition is RootRepresentationDisposition.TARGET_COMPATIBLE:
                result["b4a"] += len(motifs)
            else:
                result["b4b"] += len(motifs)
    result["total_b3b"] = result["ordinary_b3b"] + result["metadata_less_b3b"]
    return result


def _optional_edges_source(
    request: RootP3SourceAdmissionRequest, scope: RootScopeKey,
) -> ExplicitSourceEvidence:
    matches = [
        item for item in request.description.explicit_source_manifest.entries
        if item.scope_key == scope and item.semantic_role is EvidenceSemanticRole.EDGES
    ]
    if len(matches) != 1:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_OPTIONAL_EDGE_EVIDENCE_MISSING")
    return matches[0]


def _load_record(path: Path, request: RootP3SourceAdmissionRequest) -> dict[str, Any]:
    try:
        outer = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_UNREADABLE") from exc
    if not isinstance(outer, dict) or set(outer) != {"schema", "version", "payload", "digest"}:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_SHAPE_INVALID")
    payload = outer.get("payload")
    if (
        outer.get("schema") != _RECORD_SCHEMA
        or outer.get("version") != _RECORD_VERSION
        or not isinstance(payload, dict)
        or outer.get("digest") != _digest(payload)
    ):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_INTEGRITY_INVALID")
    expected = {
        "root_description_digest": request.description.identity_digest,
        "explicit_source_manifest_digest": request.description.explicit_source_manifest.digest,
        "expected_native_core_id": str(request.expected_native_core_id),
        "operation_key": request.operation_key,
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_BINDING_MISMATCH")
    scopes = payload.get("scopes")
    if not isinstance(scopes, list) or len(scopes) != len(request.scope_bindings):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_SCOPE_SET_INVALID")
    keys = {_scope_key_from_payload(item.get("scope_key")) for item in scopes if isinstance(item, dict)}
    if keys != {item.scope_key for item in request.scope_bindings}:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_SCOPE_SET_INVALID")
    completion = payload.get("carrier_completion")
    if completion is not None:
        _completion_snapshot_pairs(completion, request)
    return payload


def _verify_record_snapshots(
    connection: sqlite3.Connection,
    record: dict[str, Any],
    request: RootP3SourceAdmissionRequest,
) -> None:
    carrier = request.carrier_root
    completion = record.get("carrier_completion")
    inherited_pairs = (
        _completion_snapshot_pairs(completion, request)
        if completion is not None else set()
    )
    for entry in _ordered_scope_entries(record):
        binding = request_binding(request, entry)
        expected_namespace_id = binding.scope_plan.legacy_source_namespace_id
        expected_namespace_key = _p1_legacy_source_namespace_key(connection, expected_namespace_id)
        if (
            entry.get("legacy_source_namespace_id") != str(expected_namespace_id)
            or entry.get("legacy_source_namespace_key") != expected_namespace_key
        ):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_P1_SOURCE_NAMESPACE_BINDING_MISMATCH")
        root = Path(entry.get("snapshot_root", "")).expanduser().resolve()
        manifest_path = Path(entry.get("manifest_path", "")).expanduser().resolve()
        pair = (str(root), str(manifest_path))
        if (
            (carrier not in root.parents or carrier not in manifest_path.parents)
            and pair not in inherited_pairs
        ):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_SNAPSHOT_PATH_ESCAPES_RECORD")
        try:
            manifest = load_snapshot_manifest(manifest_path)
            verify_snapshot(snapshot_root=root, manifest=manifest)
        except (SubstrateConfigurationError, OSError, ValueError) as exc:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_SNAPSHOT_RECOVERY_REFUSED") from exc
        if (
            manifest.legacy_source_namespace_id != expected_namespace_id
            or manifest.legacy_source_namespace_key != expected_namespace_key
        ):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_P1_SOURCE_NAMESPACE_BINDING_MISMATCH")
        if (
            str(manifest.legacy_snapshot_id) != entry.get("legacy_snapshot_id")
            or _file_digest(manifest_path) != entry.get("manifest_digest")
        ):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_SNAPSHOT_IDENTITY_MISMATCH")


def _completion_snapshot_pairs(
    completion: object,
    request: RootP3SourceAdmissionRequest,
) -> set[tuple[str, str]]:
    """Validate the immutable predecessor cross-binding for a completion carrier."""

    data = _require_mapping(completion, "P3_CARRIER_COMPLETION_SHAPE_INVALID")
    expected = {
        "predecessor_record_path",
        "predecessor_record_digest",
        "completed_snapshots",
        "completed_manifests",
        "inherited_snapshots",
    }
    if set(data) != expected:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
    predecessor_path_raw = data.get("predecessor_record_path")
    predecessor_digest = data.get("predecessor_record_digest")
    if not isinstance(predecessor_path_raw, str) or not isinstance(predecessor_digest, str):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
    predecessor_path = Path(predecessor_path_raw).expanduser().resolve()
    requested_predecessor = request.predecessor_record_path
    if requested_predecessor is not None and predecessor_path != requested_predecessor:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_PREDECESSOR_MISMATCH")
    predecessor, observed_digest = _load_predecessor_record(predecessor_path)
    if observed_digest != predecessor_digest:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_PREDECESSOR_DRIFT")
    predecessor_pairs = {
        (
            str(Path(item.get("snapshot_root", "")).expanduser().resolve()),
            str(Path(item.get("manifest_path", "")).expanduser().resolve()),
        )
        for item in _require_list(
            predecessor.get("scopes"),
            "P3_CARRIER_COMPLETION_PREDECESSOR_SCOPE_SET_INVALID",
        )
        if isinstance(item, dict)
    }
    completed = _require_list(data.get("completed_snapshots"), "P3_CARRIER_COMPLETION_SHAPE_INVALID")
    if any(not isinstance(item, dict) for item in completed):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
    manifests = data.get("completed_manifests")
    if not isinstance(manifests, list) or any(not isinstance(item, str) for item in manifests):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
    if sorted(manifests) != sorted(
        item.get("manifest_path") for item in completed
    ):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
    inherited = _require_list(data.get("inherited_snapshots"), "P3_CARRIER_COMPLETION_SHAPE_INVALID")
    pairs: set[tuple[str, str]] = set()
    for item in inherited:
        if not isinstance(item, dict):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
        root = item.get("snapshot_root")
        manifest = item.get("manifest_path")
        if not isinstance(root, str) or not isinstance(manifest, str):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
        pair = (str(Path(root).expanduser().resolve()), str(Path(manifest).expanduser().resolve()))
        if pair in pairs or pair not in predecessor_pairs:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
        pairs.add(pair)
    return pairs


def _write_record(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    outer = {
        "schema": _RECORD_SCHEMA,
        "version": _RECORD_VERSION,
        "payload": payload,
        "digest": _digest(payload),
    }
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_TEMPORARY_EXISTS")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_intent_text(outer) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_WRITE_FAILED") from exc


def _ordered_scope_entries(record: dict[str, Any]) -> list[dict[str, Any]]:
    scopes = record.get("scopes")
    if not isinstance(scopes, list) or any(not isinstance(item, dict) for item in scopes):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_SCOPE_SET_INVALID")
    return sorted(scopes, key=lambda item: _scope_key_from_payload(item.get("scope_key")).canonical_key)


def _source_plan_for_key(request: RootP3SourceAdmissionRequest, key: RootScopeKey) -> RootSourceScopePlan:
    matches = [item for item in request.source_scope_plans if item.scope_key == key]
    if len(matches) != 1:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_PLAN_MISSING")
    return matches[0]


def _scope_key_from_plan(plan: MigrationRuntimeScopePlan) -> RootScopeKey:
    if plan.scope_kind == "PRIVATE_AGENT":
        return RootScopeKey(plan.workspace_id, RootScopeKind.PRIVATE, agent_id=plan.agent_id)
    if plan.scope_kind == "SHARED_DOMAIN":
        return RootScopeKey(plan.workspace_id, RootScopeKind.SHARED, domain_id=plan.domain_id)
    raise ValueError("scope plan kind is unsupported")


def _scope_key_from_payload(value: object) -> RootScopeKey:
    if not isinstance(value, dict):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SCOPE_KEY_INVALID")
    try:
        return RootScopeKey(
            value["workspace_id"], RootScopeKind(value["scope_kind"]),
            agent_id=value.get("agent_id"), domain_id=value.get("domain_id"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SCOPE_KEY_INVALID") from exc


def _scope_token(scope: RootScopeKey) -> str:
    value = "-".join(scope.canonical_key)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _p1_legacy_source_namespace_key(
    connection: sqlite3.Connection,
    namespace_id: UUID,
) -> str:
    """Recover the exact P1 namespace pair without creating or repairing it."""

    rows = connection.execute(
        "SELECT source_key FROM legacy_source_namespaces WHERE legacy_source_namespace_id=?",
        (namespace_id.bytes,),
    ).fetchall()
    if len(rows) != 1:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_P1_SOURCE_NAMESPACE_MISSING")
    source_key = rows[0][0]
    if not isinstance(source_key, str) or not source_key.strip():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_P1_SOURCE_NAMESPACE_KEY_INVALID")
    reverse_rows = connection.execute(
        "SELECT legacy_source_namespace_id FROM legacy_source_namespaces WHERE source_key=?",
        (source_key,),
    ).fetchall()
    if len(reverse_rows) != 1 or reverse_rows[0][0] != namespace_id.bytes:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_P1_SOURCE_NAMESPACE_BINDING_MISMATCH")
    return source_key


def _stage_key(request: RootP3SourceAdmissionRequest, entry: dict[str, Any], stage: str, suffix: str) -> str:
    scope = _scope_key_from_payload(entry.get("scope_key"))
    return f"{request.operation_key}:{stage}:{'|'.join(scope.canonical_key)}:{suffix}"


def _directory(value: str | Path, label: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir() or path.is_symlink():
        raise ValueError(f"{label} must be an existing non-symlink directory")
    return path


def _require_regular_source_inside_root(root: Path, source: Path) -> None:
    """Reject link/reparse traversal before copying declared source evidence."""

    try:
        relative = source.relative_to(root)
    except ValueError as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_PATH_ESCAPES_ROOT") from exc
    candidate = root
    for part in relative.parts:
        candidate /= part
        try:
            information = candidate.lstat()
        except OSError as exc:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_EVIDENCE_NOT_REGULAR") from exc
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        attributes = getattr(information, "st_file_attributes", 0)
        if stat.S_ISLNK(information.st_mode) or attributes & reparse_flag:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_LINK_OR_REPARSE_REFUSED")
    if not source.is_file():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_EVIDENCE_NOT_REGULAR")


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_intent_text(value).encode("utf-8")).hexdigest()


def _require_mapping(value: object, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RootP3SourceAdmissionRefused(code)
    return value


def _require_list(value: object, code: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise RootP3SourceAdmissionRefused(code)
    return value


def _require_nonnegative_int(value: object, code: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RootP3SourceAdmissionRefused(code)
    return value


def _require_uuid(value: object, code: str) -> UUID:
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str) or not value:
        raise RootP3SourceAdmissionRefused(code)
    try:
        return UUID(value)
    except (TypeError, ValueError) as exc:
        raise RootP3SourceAdmissionRefused(code) from exc


__all__ = [
    "NativeRootP3SourceAdmissionService",
    "RootP3ScopeBinding",
    "RootP3SourceAdmissionInterrupted",
    "RootP3SourceAdmissionInterruptionPoint",
    "RootP3SourceAdmissionRefused",
    "RootP3SourceAdmissionRequest",
    "RootP3SourceAdmissionResult",
    "p3_child_request_counts",
    "pre_b1_p3_scope_shape_counts",
]
