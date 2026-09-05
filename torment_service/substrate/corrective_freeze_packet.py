"""Read-only corrective freeze packet capture and strict offline reload.

This module is deliberately a preservation boundary, not an admission path.
It writes a versioned packet *outside* a supplied source root after a stable
read-only observation.  It never starts, stops, or inspects a host process,
never opens a network connection, and never allocates future admission IDs.

The caller supplies the source-specific typed evidence through a narrow
adapter.  That keeps the existing root description, explicit-source manifest,
and root-scope types authoritative while making the all-or-nothing capture
sequence reusable for a held frozen epoch.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Callable, Protocol

from .canonical_intent import canonical_intent_text
from .deployment_types import require_digest
from .errors import DeploymentAuthorityError
from .migration.explicit_source_evidence import (
    EvidenceAbsenceReason,
    EvidenceOwnerBoundary,
    EvidenceOwnerBoundaryKind,
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExplicitSourceEvidence,
    ExplicitSourceEvidenceError,
    RootEvidenceManifest,
    SourceOwnerClass,
    load_explicit_source_manifest,
)
from .migration.root_admission_description import (
    DeclaredUnmaterializedDomain,
    ExpectedRootCensus,
    ExternalOwnerObservation,
    ExternalOwnerObservationKind,
    GeometryDerivedExternalStateDisposition,
    IdentityOnlyAgentObservation,
    MaterializedRootScopePlan,
    MaterializedScopePosture,
    RepresentationDispositionCount,
    RootFeaturePosture,
    RootNativeProductionAdmissionDescription,
    RootRepresentationDisposition,
    WorkspaceRootAdmissionPlan,
    WorkspaceTopologyCounts,
    WriterFreezeEvidenceState,
)
from .migration.root_scope import RootScopeKey, RootScopeKind
from .root_blocker5_binding import (
    RootDiscoveredCensus,
    RootGeometryDispositionPlan,
    RootGeometryDispositionPlanEntry,
    RootWriterFreezeWitness,
    discover_canonical_root_layout,
    frozen_root_geometry_disposition_plan,
)
from .runtime_binding import NativeRepresentationLane
from .writer_freeze_evidence import (
    CapturedRootWriterFreezeEvidence,
    ListenerObservation,
    RootJobObservation,
    RootTreeStabilityObservation,
    RootWriterFreezeEvidencePayload,
    RootWriterFreezeEvidenceRefused,
    WorkspaceTreeSnapshot,
    WriterProcessObservation,
    capture_root_writer_freeze_evidence,
    root_writer_freeze_evidence_payload_from_payload,
)


CORRECTIVE_FREEZE_PACKET_CONTRACT = "TORMENT_HELD_FREEZE_CORRECTIVE_PACKET"
CORRECTIVE_FREEZE_PACKET_VERSION = 1
_MINIMUM_FREEZE_INTERVAL_SECONDS = 60


class CorrectiveFreezePacketRefused(DeploymentAuthorityError):
    """The proposed capture or persisted packet is incomplete or has drifted."""


class SourceArtifactPresence(StrEnum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"


class SourceArtifactKind(StrEnum):
    FILE = "FILE"
    DIRECTORY = "DIRECTORY"


@dataclass(frozen=True)
class FrozenWorkspaceTreeTriple:
    """The predecessor tree identity required before successor capture."""

    tree_digest: str
    file_count: int
    maximum_mtime_ns: int

    def __post_init__(self) -> None:
        require_digest(self.tree_digest, "predecessor tree digest")
        if not isinstance(self.file_count, int) or self.file_count < 0:
            raise CorrectiveFreezePacketRefused("predecessor file count must be non-negative")
        if not isinstance(self.maximum_mtime_ns, int) or self.maximum_mtime_ns < 0:
            raise CorrectiveFreezePacketRefused("predecessor maximum mtime must be non-negative")

    def payload(self) -> dict[str, object]:
        return {
            "tree_digest": self.tree_digest,
            "file_count": self.file_count,
            "maximum_mtime_ns": self.maximum_mtime_ns,
        }

    def require_matches(self, snapshot: WorkspaceTreeSnapshot) -> None:
        if not isinstance(snapshot, WorkspaceTreeSnapshot):
            raise CorrectiveFreezePacketRefused("predecessor equality requires a workspace snapshot")
        if (
            snapshot.tree_digest != self.tree_digest
            or snapshot.file_count != self.file_count
            or snapshot.maximum_mtime_ns != self.maximum_mtime_ns
        ):
            raise CorrectiveFreezePacketRefused("CONTINUOUS_FREEZE_RECERTIFICATION_PREDECESSOR_MISMATCH")


@dataclass(frozen=True)
class ExcludedSourceArtifactExpectation:
    """A top-level source artifact intentionally outside ``workspaces/**``."""

    canonical_locator: str
    source_role: str
    predecessor_sha256: str

    def __post_init__(self) -> None:
        _top_level_locator(self.canonical_locator)
        _text(self.source_role, "excluded source role")
        require_digest(self.predecessor_sha256, "excluded predecessor sha256")

    def payload(self) -> dict[str, str]:
        return {
            "canonical_locator": self.canonical_locator,
            "source_role": self.source_role,
            "predecessor_sha256": self.predecessor_sha256,
        }


@dataclass(frozen=True)
class ExcludedSourceArtifactObservation:
    canonical_locator: str
    source_role: str
    byte_length: int
    sha256: str

    def __post_init__(self) -> None:
        _top_level_locator(self.canonical_locator)
        _text(self.source_role, "excluded source role")
        if not isinstance(self.byte_length, int) or self.byte_length < 0:
            raise CorrectiveFreezePacketRefused("excluded artifact byte length must be non-negative")
        require_digest(self.sha256, "excluded artifact sha256")

    def payload(self) -> dict[str, object]:
        return {
            "canonical_locator": self.canonical_locator,
            "source_role": self.source_role,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class SourceArtifactObservation:
    """A non-manifest source fact retained for empty-scope qualification."""

    canonical_locator: str
    presence: SourceArtifactPresence
    status: str
    byte_length: int | None = None
    sha256: str | None = None
    artifact_kind: SourceArtifactKind = SourceArtifactKind.FILE

    def __post_init__(self) -> None:
        _relative_locator(self.canonical_locator)
        if not isinstance(self.presence, SourceArtifactPresence):
            raise CorrectiveFreezePacketRefused("source artifact presence must be typed")
        if not isinstance(self.artifact_kind, SourceArtifactKind):
            raise CorrectiveFreezePacketRefused("source artifact kind must be typed")
        _text(self.status, "source artifact status")
        if self.artifact_kind is SourceArtifactKind.DIRECTORY:
            if self.byte_length is not None or self.sha256 is not None:
                raise CorrectiveFreezePacketRefused("directory source artifact cannot retain file bytes or digest")
        elif self.presence is SourceArtifactPresence.PRESENT:
            if not isinstance(self.byte_length, int) or self.byte_length < 0:
                raise CorrectiveFreezePacketRefused("present source artifact requires byte length")
            require_digest(self.sha256, "present source artifact sha256")
        elif self.byte_length is not None or self.sha256 is not None:
            raise CorrectiveFreezePacketRefused("absent source artifact cannot retain bytes or digest")

    def payload(self) -> dict[str, object]:
        return {
            "canonical_locator": self.canonical_locator,
            "presence": self.presence.value,
            "status": self.status,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
            "artifact_kind": self.artifact_kind.value,
        }


@dataclass(frozen=True)
class MetadataLessPerEidEvidence:
    """Exact identity evidence for one metadata-less legacy vector."""

    scope_key: RootScopeKey
    eid: int
    vector_evidence: ExplicitSourceEvidence
    canonical_text_evidence: ExplicitSourceEvidence
    dtype: str
    shape: tuple[int, ...]
    metadata_less_source_evidence_identity: str

    def __post_init__(self) -> None:
        if not isinstance(self.scope_key, RootScopeKey):
            raise CorrectiveFreezePacketRefused("metadata-less evidence requires a root scope")
        if not isinstance(self.eid, int) or isinstance(self.eid, bool) or self.eid < 0:
            raise CorrectiveFreezePacketRefused("metadata-less EID must be non-negative")
        if not isinstance(self.vector_evidence, ExplicitSourceEvidence) or not isinstance(
            self.canonical_text_evidence, ExplicitSourceEvidence,
        ):
            raise CorrectiveFreezePacketRefused("metadata-less evidence requires explicit source evidence")
        if self.vector_evidence.scope_key != self.scope_key or self.canonical_text_evidence.scope_key != self.scope_key:
            raise CorrectiveFreezePacketRefused("metadata-less evidence crosses its scope")
        if self.vector_evidence.presence_expectation is not EvidencePresenceExpectation.EXPECTED_PRESENT:
            raise CorrectiveFreezePacketRefused("metadata-less vector evidence must be present")
        if self.canonical_text_evidence.presence_expectation is not EvidencePresenceExpectation.EXPECTED_PRESENT:
            raise CorrectiveFreezePacketRefused("metadata-less text evidence must be present")
        _text(self.dtype, "metadata-less dtype")
        if not isinstance(self.shape, tuple) or not self.shape or any(
            not isinstance(value, int) or value < 0 for value in self.shape
        ):
            raise CorrectiveFreezePacketRefused("metadata-less vector shape must be a non-empty integer tuple")
        _text(self.metadata_less_source_evidence_identity, "metadata-less source evidence identity")

    @property
    def canonical_key(self) -> tuple[object, ...]:
        return (*self.scope_key.canonical_key, self.eid)

    def payload(self) -> dict[str, object]:
        return {
            "scope_key": self.scope_key.identity_payload(),
            "eid": self.eid,
            "vector_evidence": self.vector_evidence.identity_payload(),
            "canonical_text_evidence": self.canonical_text_evidence.identity_payload(),
            "dtype": self.dtype,
            "shape": list(self.shape),
            "metadata_less_source_evidence_identity": self.metadata_less_source_evidence_identity,
        }


@dataclass(frozen=True)
class EmptyPrivateSourceEvidence:
    """The source facts proving an ``EMPTY_PRIVATE`` runtime obligation."""

    scope_key: RootScopeKey
    identity_declaration_evidence: ExplicitSourceEvidence
    private_directory_observation: SourceArtifactObservation
    nodes_absence_evidence: ExplicitSourceEvidence
    memory_events_observation: SourceArtifactObservation
    embedding_manifest_evidence: ExplicitSourceEvidence
    embedding_manifest_total_rows: int
    embedding_manifest_next_row: int
    canonical_source_evidence_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.scope_key, RootScopeKey) or self.scope_key.scope_kind is not RootScopeKind.PRIVATE:
            raise CorrectiveFreezePacketRefused("empty-private evidence requires a PRIVATE scope")
        if not isinstance(self.identity_declaration_evidence, ExplicitSourceEvidence):
            raise CorrectiveFreezePacketRefused("empty-private identity evidence must be explicit")
        if not isinstance(self.private_directory_observation, SourceArtifactObservation):
            raise CorrectiveFreezePacketRefused("empty-private directory observation must be typed")
        if self.private_directory_observation.presence is not SourceArtifactPresence.PRESENT:
            raise CorrectiveFreezePacketRefused("empty-private directory must be present")
        if not isinstance(self.nodes_absence_evidence, ExplicitSourceEvidence):
            raise CorrectiveFreezePacketRefused("empty-private nodes evidence must be explicit")
        if self.nodes_absence_evidence.scope_key != self.scope_key or (
            self.nodes_absence_evidence.presence_expectation is not EvidencePresenceExpectation.EXPECTED_ABSENT
        ):
            raise CorrectiveFreezePacketRefused("empty-private nodes absence is not bound to its scope")
        if not isinstance(self.memory_events_observation, SourceArtifactObservation):
            raise CorrectiveFreezePacketRefused("empty-private memory-events observation must be typed")
        if not isinstance(self.embedding_manifest_evidence, ExplicitSourceEvidence):
            raise CorrectiveFreezePacketRefused("empty-private embedding manifest evidence must be explicit")
        if self.embedding_manifest_evidence.scope_key != self.scope_key or (
            self.embedding_manifest_evidence.presence_expectation is not EvidencePresenceExpectation.EXPECTED_PRESENT
        ):
            raise CorrectiveFreezePacketRefused("empty-private embedding manifest is not bound to its scope")
        for value, label in (
            (self.embedding_manifest_total_rows, "embedding manifest total_rows"),
            (self.embedding_manifest_next_row, "embedding manifest next_row"),
        ):
            if not isinstance(value, int) or value < 0:
                raise CorrectiveFreezePacketRefused(f"{label} must be non-negative")
        require_digest(self.canonical_source_evidence_digest, "empty-private source evidence digest")
        if self.canonical_source_evidence_digest != _sha256(self._unsigned_payload()):
            raise CorrectiveFreezePacketRefused("empty-private source evidence digest does not recompute")

    def _unsigned_payload(self) -> dict[str, object]:
        return {
            "scope_key": self.scope_key.identity_payload(),
            "identity_declaration_evidence": self.identity_declaration_evidence.identity_payload(),
            "private_directory_observation": self.private_directory_observation.payload(),
            "nodes_absence_evidence": self.nodes_absence_evidence.identity_payload(),
            "memory_events_observation": self.memory_events_observation.payload(),
            "embedding_manifest_evidence": self.embedding_manifest_evidence.identity_payload(),
            "embedding_manifest_total_rows": self.embedding_manifest_total_rows,
            "embedding_manifest_next_row": self.embedding_manifest_next_row,
        }

    def payload(self) -> dict[str, object]:
        return {**self._unsigned_payload(), "canonical_source_evidence_digest": self.canonical_source_evidence_digest}


@dataclass(frozen=True)
class DeclaredEmptySharedSourceEvidence:
    """A derived, not assumed, unmaterialized shared-domain obligation."""

    workspace_id: str
    domain_id: str
    domains_declaration_evidence: ExplicitSourceEvidence
    shared_directory_observation: SourceArtifactObservation
    nodes_absence_evidence: ExplicitSourceEvidence
    motif_observation: SourceArtifactObservation
    observation_key: str
    observation_digest: str

    def __post_init__(self) -> None:
        _text(self.workspace_id, "declared-empty workspace_id")
        _text(self.domain_id, "declared-empty domain_id")
        if not isinstance(self.domains_declaration_evidence, ExplicitSourceEvidence):
            raise CorrectiveFreezePacketRefused("declared-empty domains evidence must be explicit")
        key = RootScopeKey(self.workspace_id, RootScopeKind.SHARED, domain_id=self.domain_id)
        if not isinstance(self.shared_directory_observation, SourceArtifactObservation) or (
            self.shared_directory_observation.presence is not SourceArtifactPresence.ABSENT
        ):
            raise CorrectiveFreezePacketRefused("declared-empty shared directory must be absent")
        if not isinstance(self.nodes_absence_evidence, ExplicitSourceEvidence) or self.nodes_absence_evidence.scope_key != key:
            raise CorrectiveFreezePacketRefused("declared-empty nodes evidence does not bind its scope")
        if self.nodes_absence_evidence.presence_expectation is not EvidencePresenceExpectation.EXPECTED_ABSENT:
            raise CorrectiveFreezePacketRefused("declared-empty nodes evidence must be absent")
        if not isinstance(self.motif_observation, SourceArtifactObservation):
            raise CorrectiveFreezePacketRefused("declared-empty motif observation must be typed")
        _text(self.observation_key, "declared-empty observation key")
        require_digest(self.observation_digest, "declared-empty observation digest")
        if self.observation_digest != _sha256(self._unsigned_payload()):
            raise CorrectiveFreezePacketRefused("declared-empty observation digest does not recompute")

    @property
    def scope_key(self) -> RootScopeKey:
        return RootScopeKey(self.workspace_id, RootScopeKind.SHARED, domain_id=self.domain_id)

    def _unsigned_payload(self) -> dict[str, object]:
        return {
            "workspace_id": self.workspace_id,
            "domain_id": self.domain_id,
            "domains_declaration_evidence": self.domains_declaration_evidence.identity_payload(),
            "shared_directory_observation": self.shared_directory_observation.payload(),
            "nodes_absence_evidence": self.nodes_absence_evidence.identity_payload(),
            "motif_observation": self.motif_observation.payload(),
            "observation_key": self.observation_key,
        }

    def payload(self) -> dict[str, object]:
        return {**self._unsigned_payload(), "observation_digest": self.observation_digest}


@dataclass(frozen=True)
class RootSourceScopePlan:
    """Source-only scope plan inputs; it intentionally excludes future UUIDs."""

    scope_key: RootScopeKey
    materialization_posture: MaterializedScopePosture
    representation_disposition: RootRepresentationDisposition
    motif_domain_id: str | None
    target_representation_lane: NativeRepresentationLane

    def __post_init__(self) -> None:
        if not isinstance(self.scope_key, RootScopeKey):
            raise CorrectiveFreezePacketRefused("source scope plan requires a root scope key")
        if not isinstance(self.materialization_posture, MaterializedScopePosture):
            raise CorrectiveFreezePacketRefused("source scope posture must be typed")
        if not isinstance(self.representation_disposition, RootRepresentationDisposition):
            raise CorrectiveFreezePacketRefused("source scope disposition must be typed")
        if self.motif_domain_id is not None:
            _text(self.motif_domain_id, "motif_domain_id")
        if not isinstance(self.target_representation_lane, NativeRepresentationLane):
            raise CorrectiveFreezePacketRefused("source scope target lane must be typed")
        if self.materialization_posture in {
            MaterializedScopePosture.EMPTY_PRIVATE,
            MaterializedScopePosture.DECLARED_EMPTY_SHARED,
        } and self.representation_disposition is not RootRepresentationDisposition.NO_VECTOR:
            raise CorrectiveFreezePacketRefused("empty source scope must retain NO_VECTOR disposition")

    @property
    def canonical_key(self) -> tuple[str, str, str]:
        return self.scope_key.canonical_key

    def payload(self) -> dict[str, object]:
        return {
            "scope_key": self.scope_key.identity_payload(),
            "materialization_posture": self.materialization_posture.value,
            "representation_disposition": self.representation_disposition.value,
            "motif_domain_id": self.motif_domain_id,
            "target_representation_lane": _lane_payload(self.target_representation_lane),
        }


@dataclass(frozen=True)
class CorrectiveFreezeTypedEvidence:
    """All source-derived facts required to reconstruct a root description offline."""

    description: RootNativeProductionAdmissionDescription
    discovered_census: RootDiscoveredCensus
    source_scope_plans: tuple[RootSourceScopePlan, ...]
    unknown_identity_evidence: tuple[MetadataLessPerEidEvidence, ...]
    empty_private_evidence: tuple[EmptyPrivateSourceEvidence, ...]
    declared_empty_shared_evidence: tuple[DeclaredEmptySharedSourceEvidence, ...]
    geometry_disposition_plan: RootGeometryDispositionPlan

    def __post_init__(self) -> None:
        if not isinstance(self.description, RootNativeProductionAdmissionDescription):
            raise CorrectiveFreezePacketRefused("corrective capture requires a root description")
        if not isinstance(self.discovered_census, RootDiscoveredCensus):
            raise CorrectiveFreezePacketRefused("corrective capture requires a discovered census")
        if not isinstance(self.geometry_disposition_plan, RootGeometryDispositionPlan):
            raise CorrectiveFreezePacketRefused("corrective capture requires a geometry disposition plan")
        for value, expected, label in (
            (self.source_scope_plans, RootSourceScopePlan, "source scope plans"),
            (self.unknown_identity_evidence, MetadataLessPerEidEvidence, "unknown identity evidence"),
            (self.empty_private_evidence, EmptyPrivateSourceEvidence, "empty-private evidence"),
            (self.declared_empty_shared_evidence, DeclaredEmptySharedSourceEvidence, "declared-empty evidence"),
        ):
            if not isinstance(value, tuple) or any(not isinstance(item, expected) for item in value):
                raise CorrectiveFreezePacketRefused(f"{label} must be a typed tuple")
        plans = tuple(sorted(self.source_scope_plans, key=lambda item: item.canonical_key))
        if len({item.canonical_key for item in plans}) != len(plans):
            raise CorrectiveFreezePacketRefused("source scope plans contain duplicate scopes")
        expected = {
            scope.scope_key: scope
            for workspace in self.description.workspace_plans
            for scope in workspace.runtime_scopes
        }
        if {item.scope_key for item in plans} != set(expected):
            raise CorrectiveFreezePacketRefused("source scope plans do not cover the declared runtime scopes")
        expected_discovered = RootDiscoveredCensus(
            tuple(workspace.workspace_id for workspace in self.description.workspace_plans),
            tuple(
                scope.scope_key
                for workspace in self.description.workspace_plans
                for scope in workspace.materialized_scopes
            ),
        )
        if self.discovered_census != expected_discovered:
            raise CorrectiveFreezePacketRefused("discovered census does not match declared materialized scopes")
        for item in plans:
            plan = expected[item.scope_key]
            if (
                item.materialization_posture != plan.materialization_posture
                or item.representation_disposition != plan.representation_disposition
                or item.target_representation_lane != self.description.target_representation_lane
            ):
                raise CorrectiveFreezePacketRefused("source scope plan disagrees with root description")
        unknown = tuple(sorted(self.unknown_identity_evidence, key=lambda item: item.canonical_key))
        if len({item.canonical_key for item in unknown}) != len(unknown):
            raise CorrectiveFreezePacketRefused("metadata-less evidence contains duplicate scope/EID facts")
        unknown_scopes = {item.scope_key for item in unknown}
        expected_unknown = {
            key for key, plan in expected.items()
            if plan.representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY
        }
        if unknown_scopes != expected_unknown:
            raise CorrectiveFreezePacketRefused("metadata-less evidence does not cover UNKNOWN_IDENTITY scopes")
        empty = tuple(sorted(self.empty_private_evidence, key=lambda item: item.scope_key.canonical_key))
        if len({item.scope_key for item in empty}) != len(empty):
            raise CorrectiveFreezePacketRefused("empty-private evidence contains duplicate scopes")
        expected_empty = {
            key for key, plan in expected.items()
            if plan.materialization_posture is MaterializedScopePosture.EMPTY_PRIVATE
        }
        if {item.scope_key for item in empty} != expected_empty:
            raise CorrectiveFreezePacketRefused("empty-private evidence does not cover EMPTY_PRIVATE scopes")
        declared = tuple(sorted(self.declared_empty_shared_evidence, key=lambda item: item.scope_key.canonical_key))
        if len({item.scope_key for item in declared}) != len(declared):
            raise CorrectiveFreezePacketRefused("declared-empty evidence contains duplicate scopes")
        expected_declared = {
            key for key, plan in expected.items()
            if plan.materialization_posture is MaterializedScopePosture.DECLARED_EMPTY_SHARED
        }
        if {item.scope_key for item in declared} != expected_declared:
            raise CorrectiveFreezePacketRefused("declared-empty evidence does not cover declared obligations")
        manifest_entries = set(self.description.explicit_source_manifest.entries)
        required_special_entries = {
            item.vector_evidence for item in unknown
        } | {
            item.canonical_text_evidence for item in unknown
        } | {
            item.identity_declaration_evidence for item in empty
        } | {
            item.nodes_absence_evidence for item in empty
        } | {
            item.embedding_manifest_evidence for item in empty
        } | {
            item.domains_declaration_evidence for item in declared
        } | {
            item.nodes_absence_evidence for item in declared
        }
        if not required_special_entries <= manifest_entries:
            raise CorrectiveFreezePacketRefused("special source evidence is not retained in the root manifest")
        expected_geometry = frozen_root_geometry_disposition_plan(
            external_owner_observation_digest=self.description.external_owner_observation_digest,
        )
        if self.geometry_disposition_plan != expected_geometry:
            raise CorrectiveFreezePacketRefused("geometry disposition plan does not bind the external owner aggregate")
        object.__setattr__(self, "source_scope_plans", plans)
        object.__setattr__(self, "unknown_identity_evidence", unknown)
        object.__setattr__(self, "empty_private_evidence", empty)
        object.__setattr__(self, "declared_empty_shared_evidence", declared)


class CorrectiveSourceEvidenceAdapter(Protocol):
    """Source-specific, read-only typed collection after the t1 stability gate."""

    def capture_typed_evidence(
        self, *, data_root: Path, discovered_census: RootDiscoveredCensus,
    ) -> CorrectiveFreezeTypedEvidence: ...


@dataclass(frozen=True)
class CorrectiveCaptureObservations:
    """Injected administrative observations; no process probing lives here."""

    covered_writer_classes: tuple[WriterProcessObservation, ...]
    listener_observation: ListenerObservation
    job_observer: Callable[..., RootJobObservation]
    clock_ns: Callable[[], int]
    snapshotter: Callable[..., WorkspaceTreeSnapshot]

    def __post_init__(self) -> None:
        if not isinstance(self.covered_writer_classes, tuple) or any(
            not isinstance(item, WriterProcessObservation) for item in self.covered_writer_classes
        ):
            raise CorrectiveFreezePacketRefused("corrective writer observations must be typed")
        if not isinstance(self.listener_observation, ListenerObservation):
            raise CorrectiveFreezePacketRefused("corrective listener observation must be typed")
        if not callable(self.job_observer) or not callable(self.clock_ns) or not callable(self.snapshotter):
            raise CorrectiveFreezePacketRefused("corrective observation adapters must be callable")


@dataclass(frozen=True)
class PredecessorFreezeLineage:
    """Historical lineage only; it does not alter a predecessor witness."""

    predecessor_operation_identity: str
    predecessor_payload_digest: str
    predecessor_witness_digest: str
    predecessor_tree: FrozenWorkspaceTreeTriple
    successor_operation_identity: str
    operator_identity: str
    capture_head: str

    def __post_init__(self) -> None:
        for field in (
            "predecessor_operation_identity", "successor_operation_identity",
            "operator_identity", "capture_head",
        ):
            _text(getattr(self, field), field)
        require_digest(self.predecessor_payload_digest, "predecessor payload digest")
        require_digest(self.predecessor_witness_digest, "predecessor witness digest")
        if not isinstance(self.predecessor_tree, FrozenWorkspaceTreeTriple):
            raise CorrectiveFreezePacketRefused("predecessor lineage requires a frozen tree triple")

    def payload(
        self, *, t0_ns: int, t2_ns: int, pre_capture_equality: bool, post_capture_equality: bool,
    ) -> dict[str, object]:
        if not isinstance(t0_ns, int) or not isinstance(t2_ns, int) or t0_ns < 0 or t2_ns < t0_ns:
            raise CorrectiveFreezePacketRefused("lineage capture window is invalid")
        if not isinstance(pre_capture_equality, bool) or not isinstance(post_capture_equality, bool):
            raise CorrectiveFreezePacketRefused("lineage equality results must be bool")
        return {
            "contract": "TORMENT_HELD_FREEZE_PREDECESSOR_LINEAGE",
            "version": 1,
            "predecessor_operation_identity": self.predecessor_operation_identity,
            "predecessor_payload_digest": self.predecessor_payload_digest,
            "predecessor_witness_digest": self.predecessor_witness_digest,
            "predecessor_tree": self.predecessor_tree.payload(),
            "successor_operation_identity": self.successor_operation_identity,
            "operator_identity": self.operator_identity,
            "capture_head": self.capture_head,
            "capture_window": {"t0_ns": t0_ns, "t2_ns": t2_ns},
            "pre_capture_predecessor_equality": pre_capture_equality,
            "pre_capture_excluded_artifact_equality": pre_capture_equality,
            "post_capture_tree_equality": post_capture_equality,
            "post_capture_excluded_artifact_equality": post_capture_equality,
            "predecessor_witness_role": "HISTORICAL_LINEAGE_ONLY",
            "successor_witness_role": "ADMISSION_CARRIER_AFTER_FUTURE_AUTHORIZATION",
        }


@dataclass(frozen=True)
class CorrectiveFreezePacket:
    """Fully reloaded packet.  Its contents are usable without the source root."""

    directory: Path
    packet_digest: str
    writer_freeze_payload: RootWriterFreezeEvidencePayload
    writer_freeze_witness: RootWriterFreezeWitness
    typed_evidence: CorrectiveFreezeTypedEvidence
    predecessor_lineage: dict[str, object]
    excluded_source_artifacts: tuple[ExcludedSourceArtifactObservation, ...]


def capture_corrective_freeze_packet(
    *,
    data_root: str | Path,
    packet_directory: str | Path,
    data_root_identity: str,
    lineage: PredecessorFreezeLineage,
    observations: CorrectiveCaptureObservations,
    source_adapter: CorrectiveSourceEvidenceAdapter,
    excluded_artifacts: tuple[ExcludedSourceArtifactExpectation, ...],
    expected_root_admission_description_contract: str,
    invalidation_rule_version: str,
    minimum_delta_seconds: int = _MINIMUM_FREEZE_INTERVAL_SECONDS,
) -> CorrectiveFreezePacket:
    """Capture one successor witness and a closed typed packet.

    No file below ``data_root`` is written.  The source adapter runs only after
    a predecessor-matching t0/t1 stability observation.  Its source facts are
    then bounded by the payload's t2 snapshot and repeated excluded-artifact
    hashes before packet serialization begins.
    """

    root = _source_root(data_root)
    destination = _new_packet_directory(packet_directory, root)
    _text(data_root_identity, "data_root_identity")
    if not isinstance(lineage, PredecessorFreezeLineage):
        raise CorrectiveFreezePacketRefused("corrective capture requires predecessor lineage")
    if not isinstance(observations, CorrectiveCaptureObservations):
        raise CorrectiveFreezePacketRefused("corrective capture requires typed observations")
    if not callable(getattr(source_adapter, "capture_typed_evidence", None)):
        raise CorrectiveFreezePacketRefused("corrective source adapter must expose typed capture")
    if not isinstance(excluded_artifacts, tuple) or any(
        not isinstance(item, ExcludedSourceArtifactExpectation) for item in excluded_artifacts
    ):
        raise CorrectiveFreezePacketRefused("excluded artifacts must be a typed tuple")
    if len({item.canonical_locator for item in excluded_artifacts}) != len(excluded_artifacts):
        raise CorrectiveFreezePacketRefused("excluded artifact locators must be unique")
    if not isinstance(minimum_delta_seconds, int) or minimum_delta_seconds < _MINIMUM_FREEZE_INTERVAL_SECONDS:
        raise CorrectiveFreezePacketRefused("corrective capture requires a minimum 60-second stability interval")

    captured_evidence: CorrectiveFreezeTypedEvidence | None = None
    before_excluded: tuple[ExcludedSourceArtifactObservation, ...] | None = None
    after_excluded: tuple[ExcludedSourceArtifactObservation, ...] | None = None

    def _pre_capture(snapshot: WorkspaceTreeSnapshot) -> None:
        lineage.predecessor_tree.require_matches(snapshot)

    def _during_capture(_stability: RootTreeStabilityObservation) -> None:
        nonlocal captured_evidence, before_excluded
        before_excluded = _observe_excluded_artifacts(root, excluded_artifacts)
        direct_census = discover_canonical_root_layout(data_root=root)
        evidence = source_adapter.capture_typed_evidence(data_root=root, discovered_census=direct_census)
        if not isinstance(evidence, CorrectiveFreezeTypedEvidence):
            raise CorrectiveFreezePacketRefused("corrective source adapter returned invalid evidence")
        if evidence.discovered_census != direct_census:
            raise CorrectiveFreezePacketRefused("typed evidence discovered census is not the direct census")
        try:
            evidence.description.explicit_source_manifest.verify(data_root=root)
        except Exception as exc:
            raise CorrectiveFreezePacketRefused("typed source manifest did not verify during capture") from exc
        captured_evidence = evidence

    def _post_capture(payload: RootWriterFreezeEvidencePayload) -> None:
        nonlocal after_excluded
        if payload.external_owner_observation_digest != _external_owner_digest(captured_evidence):
            raise CorrectiveFreezePacketRefused("writer payload external owner digest disagrees with typed evidence")
        after_excluded = _observe_excluded_artifacts(root, excluded_artifacts)
        if before_excluded != after_excluded:
            raise CorrectiveFreezePacketRefused("SUCCESSOR_FREEZE_EXCLUDED_ARTIFACT_DRIFT")

    try:
        captured = capture_root_writer_freeze_evidence(
            data_root=root,
            data_root_identity=data_root_identity,
            writer_freeze_operation_identity=lineage.successor_operation_identity,
            operator_identity=lineage.operator_identity,
            covered_writer_classes=observations.covered_writer_classes,
            listener_observation=observations.listener_observation,
            external_owner_observation_digest=None,
            expected_root_admission_description_contract=expected_root_admission_description_contract,
            invalidation_rule_version=invalidation_rule_version,
            minimum_delta_seconds=minimum_delta_seconds,
            snapshotter=observations.snapshotter,
            job_observer=observations.job_observer,
            clock_ns=observations.clock_ns,
            pre_capture_snapshot_validator=_pre_capture,
            during_capture=_during_capture,
            post_capture=_post_capture,
            external_owner_observation_digest_supplier=lambda: _external_owner_digest(captured_evidence),
        )
    except RootWriterFreezeEvidenceRefused as exc:
        raise CorrectiveFreezePacketRefused(str(exc)) from exc
    if captured_evidence is None or before_excluded is None or after_excluded is None:
        raise CorrectiveFreezePacketRefused("corrective capture did not complete its typed evidence callbacks")
    # The writer payload is constructed after the adapter.  Its owner digest
    # cannot be supplied earlier, so bind its exact typed value and then prove
    # all other successor relations before writing the packet.
    if captured.payload.external_owner_observation_digest != _external_owner_digest(captured_evidence):
        raise CorrectiveFreezePacketRefused("writer payload owner digest is not the typed aggregate")
    lineage_payload = lineage.payload(
        t0_ns=captured.payload.stability_observation.t0_ns,
        t2_ns=captured.payload.post_capture_stability.t2_ns,
        pre_capture_equality=True,
        post_capture_equality=(
            captured.payload.post_capture_stability.snapshot_t2.tree_digest
            == captured.payload.stability_observation.snapshot_t1.tree_digest
            and captured.payload.post_capture_stability.snapshot_t2.file_count
            == captured.payload.stability_observation.snapshot_t1.file_count
            and captured.payload.post_capture_stability.snapshot_t2.maximum_mtime_ns
            == captured.payload.stability_observation.snapshot_t1.maximum_mtime_ns
        ),
    )
    if not lineage_payload["post_capture_tree_equality"]:
        raise CorrectiveFreezePacketRefused("SUCCESSOR_FREEZE_EVIDENCE_INVALID")
    _write_packet(
        destination=destination,
        captured=captured,
        typed=captured_evidence,
        lineage_payload=lineage_payload,
        excluded=after_excluded,
    )
    return load_corrective_freeze_packet(destination)


def load_corrective_freeze_packet(packet_directory: str | Path) -> CorrectiveFreezePacket:
    """Strictly reload a packet without reading its original source root."""

    directory = Path(packet_directory).expanduser().resolve()
    if not directory.is_dir():
        raise CorrectiveFreezePacketRefused("corrective packet directory is unavailable")
    manifest = _read_json(directory / "packet_manifest.json")
    required = {"contract", "version", "artifacts", "packet_digest"}
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise CorrectiveFreezePacketRefused("packet manifest shape is invalid")
    if manifest.get("contract") != CORRECTIVE_FREEZE_PACKET_CONTRACT:
        raise CorrectiveFreezePacketRefused("packet manifest contract is unsupported")
    if manifest.get("version") != CORRECTIVE_FREEZE_PACKET_VERSION:
        raise CorrectiveFreezePacketRefused("packet manifest version is unsupported")
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise CorrectiveFreezePacketRefused("packet manifest artifacts are invalid")
    names: list[str] = []
    for item in artifacts:
        if not isinstance(item, dict) or set(item) != {"filename", "byte_length", "sha256"}:
            raise CorrectiveFreezePacketRefused("packet manifest artifact entry is invalid")
        filename = item["filename"]
        if not isinstance(filename, str) or filename != Path(filename).name or filename == "packet_manifest.json":
            raise CorrectiveFreezePacketRefused("packet manifest artifact filename is invalid")
        if not isinstance(item["byte_length"], int) or item["byte_length"] < 0:
            raise CorrectiveFreezePacketRefused("packet manifest artifact length is invalid")
        require_digest(item["sha256"], "packet manifest artifact sha256")
        raw = _read_bytes(directory / filename)
        if len(raw) != item["byte_length"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise CorrectiveFreezePacketRefused("PACKET_MANIFEST_ARTIFACT_HASH_MISMATCH")
        names.append(filename)
    if len(set(names)) != len(names) or set(names) != _packet_artifact_names():
        raise CorrectiveFreezePacketRefused("packet manifest artifact set is incomplete")
    unsigned = {"contract": manifest["contract"], "version": manifest["version"], "artifacts": artifacts}
    if manifest["packet_digest"] != _sha256(unsigned):
        raise CorrectiveFreezePacketRefused("packet manifest digest does not recompute")

    payload_wrapper = _read_artifact(directory, "writer_freeze_payload.json", "WRITER_FREEZE_PAYLOAD")
    payload = _decode_writer_payload(payload_wrapper)
    witness_wrapper = _read_artifact(directory, "writer_freeze_witness.json", "WRITER_FREEZE_WITNESS")
    witness = _decode_witness(witness_wrapper)
    if witness.writer_evidence_digest != payload.digest:
        raise CorrectiveFreezePacketRefused("SUCCESSOR_WITNESS_PAYLOAD_MISMATCH")
    if witness.data_root_identity != payload.data_root_identity or (
        witness.writer_freeze_operation_identity != payload.writer_freeze_operation_identity
    ):
        raise CorrectiveFreezePacketRefused("successor witness identity does not bind payload")

    manifest_path = directory / "source_manifest.json"
    source_manifest = load_explicit_source_manifest(manifest_path)
    external = _decode_external_observations(
        _read_artifact(directory, "external_owner_observations.json", "EXTERNAL_OWNER_OBSERVATIONS"),
    )
    description_wrapper = _read_artifact(directory, "root_description.json", "ROOT_DESCRIPTION")
    description = _decode_description(description_wrapper, source_manifest, external)
    discovered = _decode_discovered_census(
        _read_artifact(directory, "discovered_census.json", "DISCOVERED_CENSUS"),
    )
    _require_declared_census_matches_description(
        _read_artifact(directory, "declared_census.json", "DECLARED_CENSUS"), description,
    )
    source_scope_plans = _decode_source_scope_plans(
        _read_artifact(directory, "source_scope_plans.json", "SOURCE_SCOPE_PLANS"),
    )
    unknown = _decode_unknown_identity_evidence(
        _read_artifact(directory, "unknown_identity_evidence.json", "UNKNOWN_IDENTITY_EVIDENCE"),
    )
    empty_private = _decode_empty_private_evidence(
        _read_artifact(directory, "empty_private_evidence.json", "EMPTY_PRIVATE_EVIDENCE"),
    )
    declared_empty = _decode_declared_empty_shared_evidence(
        _read_artifact(directory, "declared_empty_shared_evidence.json", "DECLARED_EMPTY_SHARED_EVIDENCE"),
    )
    if external != description.external_owner_observations or _external_owner_digest_from_tuple(external) != description.external_owner_observation_digest:
        raise CorrectiveFreezePacketRefused("external owner observations do not reconstruct their aggregate")
    geometry = _decode_geometry_plan(
        _read_artifact(directory, "geometry_disposition_plan.json", "GEOMETRY_DISPOSITION_PLAN"),
    )
    excluded = _decode_excluded_artifacts(
        _read_artifact(directory, "excluded_source_artifacts.json", "EXCLUDED_SOURCE_ARTIFACTS"),
    )
    lineage = _decode_lineage(_read_artifact(directory, "predecessor_lineage.json", "PREDECESSOR_LINEAGE"))
    typed = CorrectiveFreezeTypedEvidence(
        description=description,
        discovered_census=discovered,
        source_scope_plans=source_scope_plans,
        unknown_identity_evidence=unknown,
        empty_private_evidence=empty_private,
        declared_empty_shared_evidence=declared_empty,
        geometry_disposition_plan=geometry,
    )
    if payload.external_owner_observation_digest != description.external_owner_observation_digest:
        raise CorrectiveFreezePacketRefused("writer payload owner digest disagrees with typed description")
    if lineage["successor_operation_identity"] != witness.writer_freeze_operation_identity:
        raise CorrectiveFreezePacketRefused("lineage successor does not match writer witness")
    if lineage["operator_identity"] != payload.operator_identity:
        raise CorrectiveFreezePacketRefused("lineage operator does not match writer payload")
    if lineage["predecessor_witness_role"] != "HISTORICAL_LINEAGE_ONLY":
        raise CorrectiveFreezePacketRefused("lineage predecessor witness role is invalid")
    return CorrectiveFreezePacket(
        directory=directory,
        packet_digest=manifest["packet_digest"],
        writer_freeze_payload=payload,
        writer_freeze_witness=witness,
        typed_evidence=typed,
        predecessor_lineage=lineage,
        excluded_source_artifacts=excluded,
    )


def _write_packet(
    *,
    destination: Path,
    captured: CapturedRootWriterFreezeEvidence,
    typed: CorrectiveFreezeTypedEvidence,
    lineage_payload: dict[str, object],
    excluded: tuple[ExcludedSourceArtifactObservation, ...],
) -> None:
    destination.mkdir(parents=False, exist_ok=False)
    artifacts: dict[str, dict[str, object]] = {
        "writer_freeze_payload.json": _artifact("WRITER_FREEZE_PAYLOAD", {
            "payload_digest": captured.payload.digest, "payload": captured.payload.payload(),
        }),
        "writer_freeze_witness.json": _artifact("WRITER_FREEZE_WITNESS", {
            "witness_digest": captured.witness.digest, "witness": captured.witness.payload(),
        }),
        "discovered_census.json": _artifact("DISCOVERED_CENSUS", {
            "census_digest": typed.discovered_census.digest, "census": typed.discovered_census.payload(),
        }),
        "declared_census.json": _artifact("DECLARED_CENSUS", {
            "expected_census": typed.description.expected_census.identity_payload(),
            "workspace_plans": [item.identity_payload() for item in typed.description.workspace_plans],
        }),
        "source_manifest.json": {
            "manifest_digest": typed.description.explicit_source_manifest.digest,
            "manifest": typed.description.explicit_source_manifest.canonical_payload,
        },
        "root_description.json": _artifact("ROOT_DESCRIPTION", {
            "description_digest": typed.description.identity_digest,
            "description": typed.description.canonical_payload,
        }),
        "source_scope_plans.json": _artifact("SOURCE_SCOPE_PLANS", {
            "plans": [item.payload() for item in typed.source_scope_plans],
            "plans_digest": _sha256([item.payload() for item in typed.source_scope_plans]),
        }),
        "unknown_identity_evidence.json": _artifact("UNKNOWN_IDENTITY_EVIDENCE", {
            "entries": [item.payload() for item in typed.unknown_identity_evidence],
        }),
        "empty_private_evidence.json": _artifact("EMPTY_PRIVATE_EVIDENCE", {
            "entries": [item.payload() for item in typed.empty_private_evidence],
        }),
        "declared_empty_shared_evidence.json": _artifact("DECLARED_EMPTY_SHARED_EVIDENCE", {
            "entries": [item.payload() for item in typed.declared_empty_shared_evidence],
        }),
        "external_owner_observations.json": _artifact("EXTERNAL_OWNER_OBSERVATIONS", {
            "entries": [item.identity_payload() for item in typed.description.external_owner_observations],
            "aggregate_digest": typed.description.external_owner_observation_digest,
        }),
        "geometry_disposition_plan.json": _artifact("GEOMETRY_DISPOSITION_PLAN", {
            "entries": [item.payload() for item in typed.geometry_disposition_plan.entries],
            "plan_digest": typed.geometry_disposition_plan.digest,
        }),
        "excluded_source_artifacts.json": _artifact("EXCLUDED_SOURCE_ARTIFACTS", {
            "entries": [item.payload() for item in excluded],
        }),
        "predecessor_lineage.json": _artifact("PREDECESSOR_LINEAGE", {"lineage": lineage_payload}),
    }
    for filename, payload in artifacts.items():
        _write_json(destination / filename, payload)
    manifest_entries = []
    for filename in sorted(artifacts):
        raw = _read_bytes(destination / filename)
        manifest_entries.append({
            "filename": filename,
            "byte_length": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    unsigned = {
        "contract": CORRECTIVE_FREEZE_PACKET_CONTRACT,
        "version": CORRECTIVE_FREEZE_PACKET_VERSION,
        "artifacts": manifest_entries,
    }
    _write_json(destination / "packet_manifest.json", {**unsigned, "packet_digest": _sha256(unsigned)})


def _artifact(kind: str, body: dict[str, object]) -> dict[str, object]:
    return {"contract": f"TORMENT_HELD_FREEZE_PACKET_{kind}", "version": 1, **body}


def _read_artifact(directory: Path, filename: str, kind: str) -> dict[str, object]:
    value = _read_json(directory / filename)
    if not isinstance(value, dict) or value.get("contract") != f"TORMENT_HELD_FREEZE_PACKET_{kind}" or value.get("version") != 1:
        raise CorrectiveFreezePacketRefused(f"{kind} artifact contract or version is unsupported")
    return value


def _decode_writer_payload(value: dict[str, object]) -> RootWriterFreezeEvidencePayload:
    if set(value) != {"contract", "version", "payload_digest", "payload"}:
        raise CorrectiveFreezePacketRefused("writer payload artifact shape is invalid")
    try:
        payload = root_writer_freeze_evidence_payload_from_payload(value["payload"])
    except RootWriterFreezeEvidenceRefused as exc:
        raise CorrectiveFreezePacketRefused("writer payload artifact cannot decode") from exc
    if value["payload_digest"] != payload.digest:
        raise CorrectiveFreezePacketRefused("writer payload digest does not recompute")
    return payload


def _decode_witness(value: dict[str, object]) -> RootWriterFreezeWitness:
    if set(value) != {"contract", "version", "witness_digest", "witness"} or not isinstance(value["witness"], dict):
        raise CorrectiveFreezePacketRefused("writer witness artifact shape is invalid")
    try:
        witness = RootWriterFreezeWitness(**value["witness"])
    except (TypeError, ValueError, DeploymentAuthorityError) as exc:
        raise CorrectiveFreezePacketRefused("writer witness artifact cannot decode") from exc
    if value["witness_digest"] != witness.digest:
        raise CorrectiveFreezePacketRefused("writer witness digest does not recompute")
    return witness


def _decode_discovered_census(value: dict[str, object]) -> RootDiscoveredCensus:
    if set(value) != {"contract", "version", "census_digest", "census"} or not isinstance(value["census"], dict):
        raise CorrectiveFreezePacketRefused("discovered census artifact shape is invalid")
    census = value["census"]
    if set(census) != {"workspace_ids", "materialized_scope_keys"}:
        raise CorrectiveFreezePacketRefused("discovered census payload shape is invalid")
    try:
        result = RootDiscoveredCensus(
            tuple(census["workspace_ids"]), tuple(_scope_key_from_payload(item) for item in census["materialized_scope_keys"]),
        )
    except (TypeError, ValueError, DeploymentAuthorityError) as exc:
        raise CorrectiveFreezePacketRefused("discovered census cannot decode") from exc
    if value["census_digest"] != result.digest:
        raise CorrectiveFreezePacketRefused("discovered census digest does not recompute")
    return result


def _decode_source_scope_plans(value: dict[str, object]) -> tuple[RootSourceScopePlan, ...]:
    if set(value) != {"contract", "version", "plans", "plans_digest"} or not isinstance(value["plans"], list):
        raise CorrectiveFreezePacketRefused("source scope plans artifact shape is invalid")
    plans = tuple(_source_scope_plan_from_payload(item) for item in value["plans"])
    if value["plans_digest"] != _sha256([item.payload() for item in plans]):
        raise CorrectiveFreezePacketRefused("source scope plans digest does not recompute")
    return plans


def _decode_unknown_identity_evidence(value: dict[str, object]) -> tuple[MetadataLessPerEidEvidence, ...]:
    return tuple(_metadata_less_from_payload(item) for item in _entries(value, "UNKNOWN_IDENTITY_EVIDENCE"))


def _decode_empty_private_evidence(value: dict[str, object]) -> tuple[EmptyPrivateSourceEvidence, ...]:
    return tuple(_empty_private_from_payload(item) for item in _entries(value, "EMPTY_PRIVATE_EVIDENCE"))


def _decode_declared_empty_shared_evidence(value: dict[str, object]) -> tuple[DeclaredEmptySharedSourceEvidence, ...]:
    return tuple(_declared_empty_from_payload(item) for item in _entries(value, "DECLARED_EMPTY_SHARED_EVIDENCE"))


def _decode_external_observations(value: dict[str, object]) -> tuple[ExternalOwnerObservation, ...]:
    if set(value) != {"contract", "version", "entries", "aggregate_digest"} or not isinstance(value["entries"], list):
        raise CorrectiveFreezePacketRefused("external observations artifact shape is invalid")
    result = tuple(_external_observation_from_payload(item) for item in value["entries"])
    if value["aggregate_digest"] != _external_owner_digest_from_tuple(result):
        raise CorrectiveFreezePacketRefused("external owner aggregate digest does not recompute")
    return result


def _decode_geometry_plan(value: dict[str, object]) -> RootGeometryDispositionPlan:
    if set(value) != {"contract", "version", "entries", "plan_digest"} or not isinstance(value["entries"], list):
        raise CorrectiveFreezePacketRefused("geometry disposition artifact shape is invalid")
    try:
        result = RootGeometryDispositionPlan(tuple(RootGeometryDispositionPlanEntry(**item) for item in value["entries"]))
    except (TypeError, ValueError, DeploymentAuthorityError) as exc:
        raise CorrectiveFreezePacketRefused("geometry disposition plan cannot decode") from exc
    if value["plan_digest"] != result.digest:
        raise CorrectiveFreezePacketRefused("geometry disposition plan digest does not recompute")
    return result


def _decode_excluded_artifacts(value: dict[str, object]) -> tuple[ExcludedSourceArtifactObservation, ...]:
    return tuple(_excluded_observation_from_payload(item) for item in _entries(value, "EXCLUDED_SOURCE_ARTIFACTS"))


def _decode_lineage(value: dict[str, object]) -> dict[str, object]:
    if set(value) != {"contract", "version", "lineage"} or not isinstance(value["lineage"], dict):
        raise CorrectiveFreezePacketRefused("predecessor lineage artifact shape is invalid")
    result = value["lineage"]
    required = {
        "contract", "version", "predecessor_operation_identity", "predecessor_payload_digest",
        "predecessor_witness_digest", "predecessor_tree", "successor_operation_identity",
        "operator_identity", "capture_head", "capture_window", "pre_capture_predecessor_equality",
        "pre_capture_excluded_artifact_equality", "post_capture_tree_equality",
        "post_capture_excluded_artifact_equality", "predecessor_witness_role", "successor_witness_role",
    }
    if set(result) != required or result.get("contract") != "TORMENT_HELD_FREEZE_PREDECESSOR_LINEAGE" or result.get("version") != 1:
        raise CorrectiveFreezePacketRefused("predecessor lineage payload is invalid")
    try:
        predecessor = FrozenWorkspaceTreeTriple(**result["predecessor_tree"])
    except (TypeError, ValueError, DeploymentAuthorityError) as exc:
        raise CorrectiveFreezePacketRefused("predecessor lineage tree is invalid") from exc
    for key in ("predecessor_payload_digest", "predecessor_witness_digest"):
        require_digest(result[key], key)
    window = result["capture_window"]
    if not isinstance(window, dict) or set(window) != {"t0_ns", "t2_ns"} or not all(
        isinstance(window[key], int) and window[key] >= 0 for key in window
    ) or window["t2_ns"] < window["t0_ns"]:
        raise CorrectiveFreezePacketRefused("predecessor lineage capture window is invalid")
    if (
        not result["pre_capture_predecessor_equality"]
        or not result["pre_capture_excluded_artifact_equality"]
        or not result["post_capture_tree_equality"]
        or not result["post_capture_excluded_artifact_equality"]
    ):
        raise CorrectiveFreezePacketRefused("predecessor lineage does not record successful equality gates")
    del predecessor
    return result


def _decode_description(
    value: dict[str, object], manifest: RootEvidenceManifest,
    external_observations: tuple[ExternalOwnerObservation, ...],
) -> RootNativeProductionAdmissionDescription:
    if set(value) != {"contract", "version", "description_digest", "description"} or not isinstance(value["description"], dict):
        raise CorrectiveFreezePacketRefused("root description artifact shape is invalid")
    raw = value["description"]
    required = {
        "data_root_identity", "operator_identity", "workspace_plans", "target_representation_lane",
        "expected_census", "explicit_source_manifest_digest", "external_owner_observation_digest",
        "feature_posture", "writer_freeze_evidence_state",
    }
    if set(raw) != required or raw["explicit_source_manifest_digest"] != manifest.digest:
        raise CorrectiveFreezePacketRefused("root description payload does not bind its source manifest")
    try:
        description = RootNativeProductionAdmissionDescription(
            data_root_identity=raw["data_root_identity"],
            operator_identity=raw["operator_identity"],
            workspace_plans=tuple(_workspace_plan_from_payload(item) for item in raw["workspace_plans"]),
            target_representation_lane=_lane_from_payload(raw["target_representation_lane"]),
            expected_census=_expected_census_from_payload(raw["expected_census"]),
            explicit_source_manifest=manifest,
            external_owner_observations=external_observations,
            feature_posture=_feature_posture_from_payload(raw["feature_posture"]),
            writer_freeze_evidence_state=WriterFreezeEvidenceState(raw["writer_freeze_evidence_state"]),
        )
    except (TypeError, ValueError, DeploymentAuthorityError, ExplicitSourceEvidenceError) as exc:
        raise CorrectiveFreezePacketRefused("root description cannot decode") from exc
    if raw["external_owner_observation_digest"] != description.external_owner_observation_digest:
        raise CorrectiveFreezePacketRefused("root description external owner digest does not recompute")
    if value["description_digest"] != description.identity_digest:
        raise CorrectiveFreezePacketRefused("root description digest does not recompute")
    if canonical_intent_text(raw) != canonical_intent_text(description.canonical_payload):
        raise CorrectiveFreezePacketRefused("root description payload is noncanonical")
    return description


def _require_declared_census_matches_description(
    value: dict[str, object], description: RootNativeProductionAdmissionDescription,
) -> None:
    if set(value) != {"contract", "version", "expected_census", "workspace_plans"}:
        raise CorrectiveFreezePacketRefused("declared census artifact shape is invalid")
    if value["expected_census"] != description.expected_census.identity_payload() or (
        value["workspace_plans"] != [item.identity_payload() for item in description.workspace_plans]
    ):
        raise CorrectiveFreezePacketRefused("declared census artifact disagrees with root description")


def _entries(value: dict[str, object], kind: str) -> list[object]:
    if set(value) != {"contract", "version", "entries"} or not isinstance(value["entries"], list):
        raise CorrectiveFreezePacketRefused(f"{kind} artifact shape is invalid")
    return value["entries"]


def _source_root(value: str | Path) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise CorrectiveFreezePacketRefused("corrective capture source root must be an existing directory")
    return root


def _new_packet_directory(value: str | Path, source_root: Path) -> Path:
    destination = Path(value).expanduser().resolve()
    if destination.exists() or source_root == destination or source_root in destination.parents:
        raise CorrectiveFreezePacketRefused("packet directory must be new and outside its source root")
    if not destination.parent.is_dir():
        raise CorrectiveFreezePacketRefused("packet directory parent must already exist")
    return destination


def _observe_excluded_artifacts(
    root: Path, expectations: tuple[ExcludedSourceArtifactExpectation, ...],
) -> tuple[ExcludedSourceArtifactObservation, ...]:
    observations: list[ExcludedSourceArtifactObservation] = []
    for expected in sorted(expectations, key=lambda item: item.canonical_locator):
        path = root / expected.canonical_locator
        if not path.is_file():
            raise CorrectiveFreezePacketRefused("excluded source artifact is missing or not a regular file")
        payload = _read_bytes(path)
        digest = hashlib.sha256(payload).hexdigest()
        if digest != expected.predecessor_sha256:
            raise CorrectiveFreezePacketRefused("PREDECESSOR_EXCLUDED_ARTIFACT_HASH_MISMATCH")
        observations.append(ExcludedSourceArtifactObservation(
            expected.canonical_locator, expected.source_role, len(payload), digest,
        ))
    return tuple(observations)


def _external_owner_digest(value: CorrectiveFreezeTypedEvidence | None) -> str:
    if value is None:
        raise CorrectiveFreezePacketRefused("typed evidence is unavailable")
    return value.description.external_owner_observation_digest


def _external_owner_digest_from_tuple(value: tuple[ExternalOwnerObservation, ...]) -> str:
    return hashlib.sha256(canonical_intent_text([item.identity_payload() for item in value]).encode("utf-8")).hexdigest()


def _sha256(value: object) -> str:
    return hashlib.sha256(canonical_intent_text(value).encode("utf-8")).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(canonical_intent_text(value) + "\n", encoding="utf-8", newline="\n")


def _read_json(path: Path) -> object:
    try:
        return json.loads(_read_bytes(path).decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CorrectiveFreezePacketRefused("packet artifact is not canonical JSON") from exc


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise CorrectiveFreezePacketRefused("packet artifact cannot be read") from exc


def _packet_artifact_names() -> set[str]:
    return {
        "writer_freeze_payload.json", "writer_freeze_witness.json", "discovered_census.json",
        "declared_census.json", "source_manifest.json", "root_description.json",
        "source_scope_plans.json", "unknown_identity_evidence.json", "empty_private_evidence.json",
        "declared_empty_shared_evidence.json", "external_owner_observations.json",
        "geometry_disposition_plan.json", "excluded_source_artifacts.json", "predecessor_lineage.json",
    }


def _scope_key_from_payload(value: object) -> RootScopeKey:
    if not isinstance(value, dict) or set(value) != {"workspace_id", "scope_kind", "agent_id", "domain_id"}:
        raise CorrectiveFreezePacketRefused("root scope payload is invalid")
    try:
        return RootScopeKey(
            workspace_id=value["workspace_id"], scope_kind=RootScopeKind(value["scope_kind"]),
            agent_id=value["agent_id"], domain_id=value["domain_id"],
        )
    except (TypeError, ValueError) as exc:
        raise CorrectiveFreezePacketRefused("root scope payload cannot decode") from exc


def _evidence_from_payload(value: object) -> ExplicitSourceEvidence:
    if not isinstance(value, dict):
        raise CorrectiveFreezePacketRefused("explicit source evidence payload is invalid")
    required = {
        "owner_class", "owner_boundary", "canonical_locator", "semantic_role", "presence_expectation",
        "scope_key", "byte_length", "sha256_hex", "absence_reason",
    }
    if set(value) != required or not isinstance(value["owner_boundary"], dict):
        raise CorrectiveFreezePacketRefused("explicit source evidence payload shape is invalid")
    owner = value["owner_boundary"]
    try:
        return ExplicitSourceEvidence(
            owner_class=SourceOwnerClass(value["owner_class"]),
            owner_boundary=EvidenceOwnerBoundary(
                workspace_id=owner["workspace_id"], boundary_kind=EvidenceOwnerBoundaryKind(owner["boundary_kind"]),
                agent_id=owner.get("agent_id"), domain_id=owner.get("domain_id"),
            ),
            canonical_locator=value["canonical_locator"], semantic_role=EvidenceSemanticRole(value["semantic_role"]),
            presence_expectation=EvidencePresenceExpectation(value["presence_expectation"]),
            scope_key=None if value["scope_key"] is None else _scope_key_from_payload(value["scope_key"]),
            byte_length=value["byte_length"], sha256_hex=value["sha256_hex"],
            absence_reason=None if value["absence_reason"] is None else EvidenceAbsenceReason(value["absence_reason"]),
        )
    except (KeyError, TypeError, ValueError, ExplicitSourceEvidenceError) as exc:
        raise CorrectiveFreezePacketRefused("explicit source evidence cannot decode") from exc


def _source_artifact_from_payload(value: object) -> SourceArtifactObservation:
    if not isinstance(value, dict) or set(value) != {
        "canonical_locator", "presence", "status", "byte_length", "sha256", "artifact_kind",
    }:
        raise CorrectiveFreezePacketRefused("source artifact observation payload is invalid")
    try:
        return SourceArtifactObservation(
            canonical_locator=value["canonical_locator"], presence=SourceArtifactPresence(value["presence"]),
            status=value["status"], byte_length=value["byte_length"], sha256=value["sha256"],
            artifact_kind=SourceArtifactKind(value["artifact_kind"]),
        )
    except (TypeError, ValueError, DeploymentAuthorityError) as exc:
        raise CorrectiveFreezePacketRefused("source artifact observation cannot decode") from exc


def _metadata_less_from_payload(value: object) -> MetadataLessPerEidEvidence:
    if not isinstance(value, dict) or set(value) != {
        "scope_key", "eid", "vector_evidence", "canonical_text_evidence", "dtype", "shape",
        "metadata_less_source_evidence_identity",
    } or not isinstance(value["shape"], list):
        raise CorrectiveFreezePacketRefused("metadata-less evidence payload is invalid")
    return MetadataLessPerEidEvidence(
        scope_key=_scope_key_from_payload(value["scope_key"]), eid=value["eid"],
        vector_evidence=_evidence_from_payload(value["vector_evidence"]),
        canonical_text_evidence=_evidence_from_payload(value["canonical_text_evidence"]),
        dtype=value["dtype"], shape=tuple(value["shape"]),
        metadata_less_source_evidence_identity=value["metadata_less_source_evidence_identity"],
    )


def _empty_private_from_payload(value: object) -> EmptyPrivateSourceEvidence:
    required = {
        "scope_key", "identity_declaration_evidence", "private_directory_observation", "nodes_absence_evidence",
        "memory_events_observation", "embedding_manifest_evidence", "embedding_manifest_total_rows",
        "embedding_manifest_next_row", "canonical_source_evidence_digest",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise CorrectiveFreezePacketRefused("empty-private evidence payload is invalid")
    return EmptyPrivateSourceEvidence(
        scope_key=_scope_key_from_payload(value["scope_key"]),
        identity_declaration_evidence=_evidence_from_payload(value["identity_declaration_evidence"]),
        private_directory_observation=_source_artifact_from_payload(value["private_directory_observation"]),
        nodes_absence_evidence=_evidence_from_payload(value["nodes_absence_evidence"]),
        memory_events_observation=_source_artifact_from_payload(value["memory_events_observation"]),
        embedding_manifest_evidence=_evidence_from_payload(value["embedding_manifest_evidence"]),
        embedding_manifest_total_rows=value["embedding_manifest_total_rows"],
        embedding_manifest_next_row=value["embedding_manifest_next_row"],
        canonical_source_evidence_digest=value["canonical_source_evidence_digest"],
    )


def _declared_empty_from_payload(value: object) -> DeclaredEmptySharedSourceEvidence:
    required = {
        "workspace_id", "domain_id", "domains_declaration_evidence", "shared_directory_observation",
        "nodes_absence_evidence", "motif_observation", "observation_key", "observation_digest",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise CorrectiveFreezePacketRefused("declared-empty evidence payload is invalid")
    return DeclaredEmptySharedSourceEvidence(
        workspace_id=value["workspace_id"], domain_id=value["domain_id"],
        domains_declaration_evidence=_evidence_from_payload(value["domains_declaration_evidence"]),
        shared_directory_observation=_source_artifact_from_payload(value["shared_directory_observation"]),
        nodes_absence_evidence=_evidence_from_payload(value["nodes_absence_evidence"]),
        motif_observation=_source_artifact_from_payload(value["motif_observation"]),
        observation_key=value["observation_key"], observation_digest=value["observation_digest"],
    )


def _source_scope_plan_from_payload(value: object) -> RootSourceScopePlan:
    required = {
        "scope_key", "materialization_posture", "representation_disposition", "motif_domain_id",
        "target_representation_lane",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise CorrectiveFreezePacketRefused("source scope plan payload is invalid")
    return RootSourceScopePlan(
        scope_key=_scope_key_from_payload(value["scope_key"]),
        materialization_posture=MaterializedScopePosture(value["materialization_posture"]),
        representation_disposition=RootRepresentationDisposition(value["representation_disposition"]),
        motif_domain_id=value["motif_domain_id"], target_representation_lane=_lane_from_payload(value["target_representation_lane"]),
    )


def _external_observation_from_payload(value: object) -> ExternalOwnerObservation:
    required = {"workspace_id", "owner_kind", "observation_key", "observation_digest", "scope_key"}
    if not isinstance(value, dict) or set(value) != required:
        raise CorrectiveFreezePacketRefused("external owner observation payload is invalid")
    return ExternalOwnerObservation(
        workspace_id=value["workspace_id"], owner_kind=ExternalOwnerObservationKind(value["owner_kind"]),
        observation_key=value["observation_key"], observation_digest=value["observation_digest"],
        scope_key=None if value["scope_key"] is None else _scope_key_from_payload(value["scope_key"]),
    )


def _excluded_observation_from_payload(value: object) -> ExcludedSourceArtifactObservation:
    if not isinstance(value, dict) or set(value) != {"canonical_locator", "source_role", "byte_length", "sha256"}:
        raise CorrectiveFreezePacketRefused("excluded source artifact payload is invalid")
    return ExcludedSourceArtifactObservation(**value)


def _workspace_plan_from_payload(value: object) -> WorkspaceRootAdmissionPlan:
    required = {
        "workspace_id", "private_materialized_scopes", "shared_materialized_scopes", "identity_only_agents",
        "declared_unmaterialized_domains", "no_memory_scope",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise CorrectiveFreezePacketRefused("workspace plan payload is invalid")
    return WorkspaceRootAdmissionPlan(
        workspace_id=value["workspace_id"],
        private_materialized_scopes=tuple(_materialized_scope_from_payload(item) for item in value["private_materialized_scopes"]),
        shared_materialized_scopes=tuple(_materialized_scope_from_payload(item) for item in value["shared_materialized_scopes"]),
        identity_only_agents=tuple(IdentityOnlyAgentObservation(**item) for item in value["identity_only_agents"]),
        declared_unmaterialized_domains=tuple(DeclaredUnmaterializedDomain(**item) for item in value["declared_unmaterialized_domains"]),
        no_memory_scope=value["no_memory_scope"],
    )


def _materialized_scope_from_payload(value: object) -> MaterializedRootScopePlan:
    if not isinstance(value, dict) or set(value) != {"scope_key", "representation_disposition", "materialization_posture"}:
        raise CorrectiveFreezePacketRefused("materialized scope payload is invalid")
    return MaterializedRootScopePlan(
        scope_key=_scope_key_from_payload(value["scope_key"]),
        representation_disposition=RootRepresentationDisposition(value["representation_disposition"]),
        materialization_posture=MaterializedScopePosture(value["materialization_posture"]),
    )


def _expected_census_from_payload(value: object) -> ExpectedRootCensus:
    required = {
        "workspace_count", "materialized_private_scope_count", "materialized_shared_scope_count",
        "total_materialized_scope_count", "declared_empty_shared_scope_count", "empty_private_identity_scope_count",
        "representation_disposition_counts", "workspace_topology_counts",
    }
    if not isinstance(value, dict) or set(value) != required or not isinstance(value["workspace_topology_counts"], dict):
        raise CorrectiveFreezePacketRefused("expected census payload is invalid")
    try:
        return ExpectedRootCensus(
            workspace_count=value["workspace_count"],
            materialized_private_scope_count=value["materialized_private_scope_count"],
            materialized_shared_scope_count=value["materialized_shared_scope_count"],
            total_materialized_scope_count=value["total_materialized_scope_count"],
            declared_empty_shared_scope_count=value["declared_empty_shared_scope_count"],
            empty_private_identity_scope_count=value["empty_private_identity_scope_count"],
            representation_disposition_counts=tuple(
                RepresentationDispositionCount(RootRepresentationDisposition(item["disposition"]), item["scope_count"])
                for item in value["representation_disposition_counts"]
            ),
            workspace_topology_counts=WorkspaceTopologyCounts(**value["workspace_topology_counts"]),
        )
    except (TypeError, ValueError, KeyError, DeploymentAuthorityError) as exc:
        raise CorrectiveFreezePacketRefused("expected census cannot decode") from exc


def _feature_posture_from_payload(value: object) -> RootFeaturePosture:
    if not isinstance(value, dict) or set(value) != {
        "profile_name", "compression_enabled", "deep_memory_enabled", "geometry_derived_external_state_disposition",
    }:
        raise CorrectiveFreezePacketRefused("feature posture payload is invalid")
    return RootFeaturePosture(
        profile_name=value["profile_name"], compression_enabled=value["compression_enabled"],
        deep_memory_enabled=value["deep_memory_enabled"],
        geometry_derived_external_state_disposition=GeometryDerivedExternalStateDisposition(
            value["geometry_derived_external_state_disposition"],
        ),
    )


def _lane_payload(value: NativeRepresentationLane) -> dict[str, object]:
    return {field: getattr(value, field) for field in value.__dataclass_fields__}


def _lane_from_payload(value: object) -> NativeRepresentationLane:
    if not isinstance(value, dict) or set(value) != {
        "provider", "model", "dimension", "representation_class", "generation",
        "derivation_contract_version", "encoding_id", "dtype",
    }:
        raise CorrectiveFreezePacketRefused("representation lane payload is invalid")
    try:
        return NativeRepresentationLane(**value)
    except TypeError as exc:
        raise CorrectiveFreezePacketRefused("representation lane cannot decode") from exc


def _relative_locator(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise CorrectiveFreezePacketRefused("source artifact locator must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CorrectiveFreezePacketRefused("source artifact locator must remain relative")
    return value


def _top_level_locator(value: object) -> str:
    locator = _relative_locator(value)
    if len(PurePosixPath(locator).parts) != 1:
        raise CorrectiveFreezePacketRefused("excluded artifact must be a top-level locator")
    return locator


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise CorrectiveFreezePacketRefused(f"{label} must be bounded non-empty text")
    return value


__all__ = [
    "CORRECTIVE_FREEZE_PACKET_CONTRACT",
    "CORRECTIVE_FREEZE_PACKET_VERSION",
    "CorrectiveCaptureObservations",
    "CorrectiveFreezePacket",
    "CorrectiveFreezePacketRefused",
    "CorrectiveFreezeTypedEvidence",
    "CorrectiveSourceEvidenceAdapter",
    "DeclaredEmptySharedSourceEvidence",
    "EmptyPrivateSourceEvidence",
    "ExcludedSourceArtifactExpectation",
    "ExcludedSourceArtifactObservation",
    "FrozenWorkspaceTreeTriple",
    "MetadataLessPerEidEvidence",
    "PredecessorFreezeLineage",
    "RootSourceScopePlan",
    "SourceArtifactObservation",
    "SourceArtifactKind",
    "SourceArtifactPresence",
    "capture_corrective_freeze_packet",
    "load_corrective_freeze_packet",
]
