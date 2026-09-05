"""Read-only, typed evidence collection for the held-freeze source layout.

This module intentionally owns no admission, runtime, provider, or writer
logic.  It reads only the small, explicit source-file contract below and
turns those facts into the already-authoritative corrective packet types.
In particular, it never writes below ``data_root``, walks arbitrary trees,
opens SQLite, or loads vector values.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import struct
from typing import Final

from .canonical_intent import canonical_intent_text
from .corrective_freeze_packet import (
    CorrectiveFreezePacketRefused,
    CorrectiveFreezeTypedEvidence,
    DeclaredEmptySharedSourceEvidence,
    EmptyPrivateSourceEvidence,
    ExcludedAlternateRootExpectation,
    ExcludedAlternateRootObservation,
    ExcludedAlternateRootRole,
    ExcludedSourceArtifactExpectation,
    ExcludedSourceArtifactObservation,
    MetadataLessPerEidEvidence,
    RootSourceScopePlan,
    SourceArtifactKind,
    SourceArtifactObservation,
    SourceArtifactPresence,
)
from .migration.explicit_source_evidence import (
    EvidenceAbsenceReason,
    EvidenceOwnerBoundary,
    EvidenceOwnerBoundaryKind,
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExplicitSourceEvidence,
    RootEvidenceManifest,
    SourceOwnerClass,
)
from .migration.root_admission_description import (
    DeclaredUnmaterializedDomain,
    ExpectedRootCensus,
    ExternalOwnerObservation,
    ExternalOwnerObservationKind,
    IdentityOnlyAgentObservation,
    MaterializedRootScopePlan,
    MaterializedScopePosture,
    RepresentationDispositionCount,
    RootFeaturePosture,
    RootNativeProductionAdmissionDescription,
    RootRepresentationDisposition,
    WorkspaceRootAdmissionPlan,
    WorkspaceTopologyCounts,
)
from .migration.root_scope import RootScopeKey, RootScopeKind
from .root_blocker5_binding import (
    RootDiscoveredCensus,
    discover_canonical_root_layout,
    frozen_root_geometry_disposition_plan,
)
from .runtime_binding import NativeRepresentationLane


_TARGET_LANE: Final[NativeRepresentationLane] = NativeRepresentationLane(
    "st", "BAAI/bge-small-en-v1.5", 384,
    "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32",
)
_WORKSPACE_FILES: Final[frozenset[str]] = frozenset({
    "workspace_meta.json", "domains.json", "domain_policies.json",
})
_WORKSPACE_OWNER_FILES: Final[dict[str, ExternalOwnerObservationKind]] = {
    "bridges.json": ExternalOwnerObservationKind.BRIDGE,
}
_WORKSPACE_RETAINED_FILES: Final[frozenset[str]] = frozenset({
    "bridge_events.jsonl",
})
_WORKSPACE_RETAINED_DIRECTORIES: Final[frozenset[str]] = frozenset({
    "collective", "reference_memory", "environment_memory", "closure_memory",
    "contest_memory", "governance",
})
_AGENT_OWNER_FILES: Final[dict[str, ExternalOwnerObservationKind]] = {
    "identity.json": ExternalOwnerObservationKind.IDENTITY,
    "roles.json": ExternalOwnerObservationKind.ROLE,
    "character_state.json": ExternalOwnerObservationKind.CHARACTER,
}
_AGENT_RETAINED_FILES: Final[frozenset[str]] = frozenset({
    "affect_state.json", "anchors.json", "symbol_state.json", "feedback_events.jsonl",
})
_AGENT_RETAINED_DIRECTORIES: Final[frozenset[str]] = frozenset({
    "index", "memory_archive", "warmup",
})
_DOMAIN_OWNER_FILES: Final[dict[str, ExternalOwnerObservationKind]] = {
    "proposals.jsonl": ExternalOwnerObservationKind.PROPOSAL_WORKFLOW,
    "conflicts.jsonl": ExternalOwnerObservationKind.CONFLICT,
}
_DOMAIN_RETAINED_FILES: Final[frozenset[str]] = frozenset({
    "motif_events.jsonl", "motif_merges.json", "proposal_events.jsonl", "conflict_events.jsonl",
})
_NPY_DTYPE_NAMES: Final[dict[str, str]] = {
    "<f4": "float32", ">f4": "float32", "|f4": "float32",
    "<f8": "float64", ">f8": "float64", "|u1": "uint8",
}


@dataclass(frozen=True)
class ExcludedSourceArtifactLocator:
    """One consciously retained top-level artifact outside ``workspaces``."""

    canonical_locator: str
    source_role: str

    def __post_init__(self) -> None:
        locator = _top_level_locator(self.canonical_locator)
        if not isinstance(self.source_role, str) or not self.source_role:
            raise CorrectiveFreezePacketRefused("excluded source role must be non-empty")
        object.__setattr__(self, "canonical_locator", locator)


@dataclass(frozen=True)
class ExcludedAlternateRootLocator:
    """A selected alternate top-level root excluded without reading contents."""

    canonical_locator: str
    exclusion_role: ExcludedAlternateRootRole = ExcludedAlternateRootRole.ALTERNATE_SELECTED_ROOT

    def __post_init__(self) -> None:
        object.__setattr__(self, "canonical_locator", _top_level_locator(self.canonical_locator))
        if not isinstance(self.exclusion_role, ExcludedAlternateRootRole):
            raise CorrectiveFreezePacketRefused("alternate root exclusion role must be typed")


@dataclass(frozen=True)
class RealRootTypedEvidenceAdapter:
    """Strict read-only adapter for a source tree frozen by a future caller.

    The name identifies the production-shaped contract, not permission to
    contact a production root.  Qualification tests pass disposable roots.
    A caller must separately provide any writer-freeze evidence to the packet
    capture seam; this adapter performs no process or listener observation.
    """

    data_root_identity: str
    operator_identity: str
    profile_name: str = "held-freeze-typed-evidence"
    target_representation_lane: NativeRepresentationLane = _TARGET_LANE
    excluded_source_artifacts: tuple[ExcludedSourceArtifactLocator, ...] = ()
    excluded_alternate_roots: tuple[ExcludedAlternateRootLocator, ...] = ()

    def __post_init__(self) -> None:
        for value, label in (
            (self.data_root_identity, "data_root_identity"),
            (self.operator_identity, "operator_identity"),
            (self.profile_name, "profile_name"),
        ):
            if not isinstance(value, str) or not value:
                raise CorrectiveFreezePacketRefused(f"{label} must be non-empty text")
        if self.target_representation_lane != _TARGET_LANE:
            raise CorrectiveFreezePacketRefused("typed evidence adapter requires the frozen target lane")
        if not isinstance(self.excluded_source_artifacts, tuple) or any(
            not isinstance(item, ExcludedSourceArtifactLocator) for item in self.excluded_source_artifacts
        ):
            raise CorrectiveFreezePacketRefused("excluded source artifacts must be typed")
        if len({item.canonical_locator for item in self.excluded_source_artifacts}) != len(self.excluded_source_artifacts):
            raise CorrectiveFreezePacketRefused("excluded source artifact locators must be unique")
        if not isinstance(self.excluded_alternate_roots, tuple) or any(
            not isinstance(item, ExcludedAlternateRootLocator) for item in self.excluded_alternate_roots
        ):
            raise CorrectiveFreezePacketRefused("excluded alternate roots must be typed")
        if len({item.canonical_locator for item in self.excluded_alternate_roots}) != len(self.excluded_alternate_roots):
            raise CorrectiveFreezePacketRefused("duplicate excluded alternate root locator")
        if {item.canonical_locator for item in self.excluded_source_artifacts} & {
            item.canonical_locator for item in self.excluded_alternate_roots
        }:
            raise CorrectiveFreezePacketRefused("file artifacts and alternate roots cannot share a locator")

    def excluded_artifact_expectations(self, *, data_root: Path) -> tuple[ExcludedSourceArtifactExpectation, ...]:
        """Hash configured top-level excluded artifacts without changing them."""

        root = _source_root(data_root)
        return tuple(ExcludedSourceArtifactExpectation(
            item.canonical_locator, item.source_role, _hash_file(_regular_file(root / item.canonical_locator)),
        ) for item in self.excluded_source_artifacts)

    def capture_excluded_source_artifacts(self, *, data_root: Path) -> tuple[ExcludedSourceArtifactObservation, ...]:
        """Return typed facts corresponding exactly to configured exclusions."""

        root = _source_root(data_root)
        return tuple(ExcludedSourceArtifactObservation(
            item.canonical_locator, item.source_role, _regular_file(root / item.canonical_locator).stat().st_size,
            _hash_file(root / item.canonical_locator),
        ) for item in self.excluded_source_artifacts)

    def excluded_alternate_root_expectations(
        self, *, data_root: Path,
    ) -> tuple[ExcludedAlternateRootExpectation, ...]:
        """Declare configured alternate roots after presence-only validation."""

        root = _source_root(data_root)
        self._validate_excluded_alternate_roots(root)
        return tuple(ExcludedAlternateRootExpectation(item.canonical_locator, item.exclusion_role)
                     for item in self.excluded_alternate_roots)

    def capture_excluded_alternate_roots(
        self, *, data_root: Path,
    ) -> tuple[ExcludedAlternateRootObservation, ...]:
        """Capture directory presence only; no alternate-root child is read."""

        root = _source_root(data_root)
        self._validate_excluded_alternate_roots(root)
        return tuple(ExcludedAlternateRootObservation(item.canonical_locator, item.exclusion_role)
                     for item in self.excluded_alternate_roots)

    def capture_typed_evidence(
        self, *, data_root: Path, discovered_census: RootDiscoveredCensus,
    ) -> CorrectiveFreezeTypedEvidence:
        """Read the fixed source contract and create no source-side artifacts."""

        root = _source_root(data_root)
        if not isinstance(discovered_census, RootDiscoveredCensus):
            raise CorrectiveFreezePacketRefused("typed evidence requires a discovered root census")
        direct_census = discover_canonical_root_layout(data_root=root)
        if direct_census != discovered_census:
            raise CorrectiveFreezePacketRefused("typed evidence discovered census does not match fixed layout")
        self._validate_excluded_alternate_roots(root)
        self._validate_root_children(root)
        workspaces_root = _real_directory(root / "workspaces", "workspaces root")

        entries: list[ExplicitSourceEvidence] = []
        workspace_plans: list[WorkspaceRootAdmissionPlan] = []
        source_plans: list[RootSourceScopePlan] = []
        unknown_evidence: list[MetadataLessPerEidEvidence] = []
        empty_private_evidence: list[EmptyPrivateSourceEvidence] = []
        declared_empty_evidence: list[DeclaredEmptySharedSourceEvidence] = []
        external_observations: list[ExternalOwnerObservation] = []

        for workspace_path in _direct_directories(workspaces_root, "workspace"):
            workspace_id = workspace_path.name
            result = self._capture_workspace(root, workspace_path, workspace_id)
            entries.extend(result.entries)
            workspace_plans.append(result.workspace_plan)
            source_plans.extend(result.source_plans)
            unknown_evidence.extend(result.unknown_evidence)
            empty_private_evidence.extend(result.empty_private_evidence)
            declared_empty_evidence.extend(result.declared_empty_evidence)
            external_observations.extend(result.external_observations)

        if not workspace_plans:
            raise CorrectiveFreezePacketRefused("typed evidence requires at least one workspace")
        manifest = RootEvidenceManifest(tuple(entries))
        expected = _expected_census(tuple(workspace_plans))
        description = RootNativeProductionAdmissionDescription(
            data_root_identity=self.data_root_identity,
            operator_identity=self.operator_identity,
            workspace_plans=tuple(workspace_plans),
            target_representation_lane=self.target_representation_lane,
            expected_census=expected,
            explicit_source_manifest=manifest,
            external_owner_observations=tuple(external_observations),
            feature_posture=RootFeaturePosture(self.profile_name, False, False),
        )
        return CorrectiveFreezeTypedEvidence(
            description=description,
            discovered_census=discovered_census,
            source_scope_plans=tuple(source_plans),
            unknown_identity_evidence=tuple(unknown_evidence),
            empty_private_evidence=tuple(empty_private_evidence),
            declared_empty_shared_evidence=tuple(declared_empty_evidence),
            geometry_disposition_plan=frozen_root_geometry_disposition_plan(
                external_owner_observation_digest=description.external_owner_observation_digest,
            ),
        )

    def _validate_root_children(self, root: Path) -> None:
        allowed = {
            "workspaces", *(item.canonical_locator for item in self.excluded_source_artifacts),
            *(item.canonical_locator for item in self.excluded_alternate_roots),
        }
        observed = {item.name for item in root.iterdir()}
        if observed - allowed:
            raise CorrectiveFreezePacketRefused("unclassified durable root artifact is not allowed")
        if "workspaces" not in observed:
            raise CorrectiveFreezePacketRefused("typed evidence source requires workspaces")
        for item in root.iterdir():
            if item.is_symlink():
                raise CorrectiveFreezePacketRefused("typed evidence source paths must not be symlinks")

    def _validate_excluded_alternate_roots(self, root: Path) -> None:
        for item in self.excluded_alternate_roots:
            _alternate_root_directory(root / item.canonical_locator)

    def _capture_workspace(self, root: Path, path: Path, workspace_id: str) -> "_WorkspaceCapture":
        workspace_boundary = EvidenceOwnerBoundary(workspace_id, EvidenceOwnerBoundaryKind.WORKSPACE)
        workspace_meta = _capture_present(
            root, path / "workspace_meta.json", SourceOwnerClass.WORKSPACE_IDENTITY_METADATA,
            workspace_boundary, "workspace_meta.json", EvidenceSemanticRole.WORKSPACE_META,
        )
        domains_evidence = _capture_present(
            root, path / "domains.json", SourceOwnerClass.DOMAIN_DECLARATION,
            workspace_boundary, "domains.json", EvidenceSemanticRole.DOMAINS,
        )
        declared_domains = _declared_domains(_read_json(path / "domains.json"))
        representation_lock = _workspace_representation_lock(
            _read_json(path / "workspace_meta.json"), workspace_id,
        )
        entries = [workspace_meta, domains_evidence]
        policy_path = path / "domain_policies.json"
        if policy_path.exists():
            entries.append(_capture_present(
                root, policy_path, SourceOwnerClass.DOMAIN_POLICY, workspace_boundary,
                "domain_policies.json", EvidenceSemanticRole.DOMAIN_POLICY,
            ))

        owner_entries, owner_observations = _capture_workspace_owner_state(
            root=root, workspace_path=path, workspace_id=workspace_id, workspace_boundary=workspace_boundary,
        )
        entries.extend(owner_entries)
        owner_observations = list(owner_observations)
        self._validate_workspace_children(path)

        private_scopes: list[MaterializedRootScopePlan] = []
        shared_scopes: list[MaterializedRootScopePlan] = []
        identities: list[IdentityOnlyAgentObservation] = []
        unmaterialized: list[DeclaredUnmaterializedDomain] = []
        source_plans: list[RootSourceScopePlan] = []
        unknown_evidence: list[MetadataLessPerEidEvidence] = []
        empty_evidence: list[EmptyPrivateSourceEvidence] = []
        declared_evidence: list[DeclaredEmptySharedSourceEvidence] = []

        agents_path = path / "agents"
        if agents_path.exists():
            for agent_path in _direct_directories(_real_directory(agents_path, "agents directory"), "agent"):
                self._validate_agent_children(agent_path)
                agent_id = agent_path.name
                identity_boundary = EvidenceOwnerBoundary(
                    workspace_id, EvidenceOwnerBoundaryKind.AGENT, agent_id=agent_id,
                )
                identity = _capture_present(
                    root, agent_path / "identity.json", SourceOwnerClass.EXTERNAL_OWNER_OBSERVATION,
                    identity_boundary, "identity.json", EvidenceSemanticRole.EXTERNAL_OBSERVATION,
                )
                entries.append(identity)
                owner_observations.append(ExternalOwnerObservation(
                    workspace_id, ExternalOwnerObservationKind.IDENTITY,
                    f"agent:{agent_id}:identity", _hash_file(agent_path / "identity.json"),
                ))
                agent_entries, agent_observations = _capture_agent_owner_state(
                    root=root, agent_path=agent_path, workspace_id=workspace_id,
                    agent_id=agent_id, boundary=identity_boundary,
                )
                entries.extend(agent_entries)
                owner_observations.extend(agent_observations)
                private_path = agent_path / "private"
                if not private_path.exists():
                    continue
                scope = RootScopeKey(workspace_id, RootScopeKind.PRIVATE, agent_id=agent_id)
                capture = _capture_private_scope(
                    root, private_path, scope, identity, self.target_representation_lane,
                    representation_lock,
                )
                entries.extend(capture.entries)
                private_scopes.append(capture.scope_plan)
                source_plans.append(capture.source_plan)
                if capture.empty_evidence is not None:
                    empty_evidence.append(capture.empty_evidence)
                    identities.append(IdentityOnlyAgentObservation(agent_id, f"identity:{workspace_id}:{agent_id}"))
                unknown_evidence.extend(capture.unknown_evidence)

        domains_path = path / "domains"
        physical_domains: set[str] = set()
        if domains_path.exists():
            for domain_path in _direct_directories(_real_directory(domains_path, "domains directory"), "domain"):
                domain_id = domain_path.name
                physical_domains.add(domain_id)
                if domain_id not in declared_domains:
                    raise CorrectiveFreezePacketRefused("materialized domain lacks a direct declaration")
                self._validate_domain_children(domain_path)
                domain_entries, domain_observations = _capture_domain_owner_state(
                    root=root, domain_path=domain_path, workspace_id=workspace_id, domain_id=domain_id,
                )
                entries.extend(domain_entries)
                owner_observations.extend(domain_observations)
                shared_path = domain_path / "shared"
                if not shared_path.exists():
                    raise CorrectiveFreezePacketRefused("materialized domain must contain shared or be absent")
                scope = RootScopeKey(workspace_id, RootScopeKind.SHARED, domain_id=domain_id)
                capture = _capture_shared_scope(
                    root, shared_path, domain_path, scope, self.target_representation_lane, representation_lock,
                )
                entries.extend(capture.entries)
                shared_scopes.append(capture.scope_plan)
                source_plans.append(capture.source_plan)
                unknown_evidence.extend(capture.unknown_evidence)

        for domain_id in sorted(declared_domains - physical_domains):
            scope = RootScopeKey(workspace_id, RootScopeKind.SHARED, domain_id=domain_id)
            boundary = EvidenceOwnerBoundary(workspace_id, EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id=domain_id)
            nodes = _absent(
                SourceOwnerClass.SHARED_GRAPH_SOURCE, boundary, "nodes.jsonl", EvidenceSemanticRole.NODES,
                scope, EvidenceAbsenceReason.UNMATERIALIZED_DECLARATION,
            )
            entries.append(nodes)
            shared_scopes.append(MaterializedRootScopePlan(
                scope, RootRepresentationDisposition.NO_VECTOR, MaterializedScopePosture.DECLARED_EMPTY_SHARED,
            ))
            source_plans.append(RootSourceScopePlan(
                scope, MaterializedScopePosture.DECLARED_EMPTY_SHARED,
                RootRepresentationDisposition.NO_VECTOR, domain_id, self.target_representation_lane,
                SourceArtifactPresence.ABSENT,
            ))
            shared_directory = SourceArtifactObservation(
                "shared", SourceArtifactPresence.ABSENT, "ABSENT", artifact_kind=SourceArtifactKind.DIRECTORY,
            )
            motif = SourceArtifactObservation("motifs.json", SourceArtifactPresence.ABSENT, "ABSENT")
            key = f"declared-empty:{workspace_id}:{domain_id}"
            unsigned = {
                "workspace_id": workspace_id, "domain_id": domain_id,
                "domains_declaration_evidence": domains_evidence.identity_payload(),
                "shared_directory_observation": shared_directory.payload(),
                "nodes_absence_evidence": nodes.identity_payload(),
                "motif_observation": motif.payload(), "observation_key": key,
            }
            declared_evidence.append(DeclaredEmptySharedSourceEvidence(
                workspace_id, domain_id, domains_evidence, shared_directory, nodes, motif, key, _digest(unsigned),
            ))
            unmaterialized.append(DeclaredUnmaterializedDomain(domain_id, f"domains:{workspace_id}:{domain_id}"))

        materialized = tuple(private_scopes) + tuple(
            item for item in shared_scopes
            if item.materialization_posture is not MaterializedScopePosture.DECLARED_EMPTY_SHARED
        )
        return _WorkspaceCapture(
            entries=tuple(entries),
            workspace_plan=WorkspaceRootAdmissionPlan(
                workspace_id, tuple(private_scopes), tuple(shared_scopes), tuple(identities),
                tuple(unmaterialized), no_memory_scope=not materialized,
            ),
            source_plans=tuple(source_plans), unknown_evidence=tuple(unknown_evidence),
            empty_private_evidence=tuple(empty_evidence), declared_empty_evidence=tuple(declared_evidence),
            external_observations=tuple(owner_observations),
        )

    @staticmethod
    def _validate_workspace_children(path: Path) -> None:
        allowed = (
            set(_WORKSPACE_FILES) | set(_WORKSPACE_OWNER_FILES) | set(_WORKSPACE_RETAINED_FILES)
            | set(_WORKSPACE_RETAINED_DIRECTORIES) | {"agents", "domains", "seeds"}
        )
        observed = {item.name for item in path.iterdir()}
        if observed - allowed:
            raise CorrectiveFreezePacketRefused("unclassified durable workspace owner is not allowed")
        if {"workspace_meta.json", "domains.json"} - observed:
            raise CorrectiveFreezePacketRefused("workspace source is missing required declarations")
        for item in path.iterdir():
            if item.is_symlink():
                raise CorrectiveFreezePacketRefused("workspace source paths must not be symlinks")

    @staticmethod
    def _validate_agent_children(path: Path) -> None:
        _validate_direct_children(
            path,
            set(_AGENT_OWNER_FILES) | set(_AGENT_RETAINED_FILES) | set(_AGENT_RETAINED_DIRECTORIES) | {"private"},
            "agent",
        )
        if not (path / "identity.json").is_file():
            raise CorrectiveFreezePacketRefused("agent source lacks identity declaration")

    @staticmethod
    def _validate_domain_children(path: Path) -> None:
        _validate_direct_children(
            path, {"shared", "motifs.json"} | set(_DOMAIN_OWNER_FILES) | set(_DOMAIN_RETAINED_FILES), "domain",
        )


@dataclass(frozen=True)
class _WorkspaceCapture:
    entries: tuple[ExplicitSourceEvidence, ...]
    workspace_plan: WorkspaceRootAdmissionPlan
    source_plans: tuple[RootSourceScopePlan, ...]
    unknown_evidence: tuple[MetadataLessPerEidEvidence, ...]
    empty_private_evidence: tuple[EmptyPrivateSourceEvidence, ...]
    declared_empty_evidence: tuple[DeclaredEmptySharedSourceEvidence, ...]
    external_observations: tuple[ExternalOwnerObservation, ...]


@dataclass(frozen=True)
class _ScopeCapture:
    entries: tuple[ExplicitSourceEvidence, ...]
    scope_plan: MaterializedRootScopePlan
    source_plan: RootSourceScopePlan
    unknown_evidence: tuple[MetadataLessPerEidEvidence, ...]
    empty_evidence: EmptyPrivateSourceEvidence | None = None


def _capture_private_scope(
    root: Path, path: Path, scope: RootScopeKey, identity: ExplicitSourceEvidence,
    target_lane: NativeRepresentationLane, representation_lock: tuple[str, str, int] | None,
) -> _ScopeCapture:
    path = _real_directory(path, "private scope")
    boundary = EvidenceOwnerBoundary(
        scope.workspace_id, EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id=scope.agent_id,
    )
    nodes_path = path / "nodes.jsonl"
    embedding_path = path / "embeddings" / "manifest.json"
    memory_events = path / "memory_events.jsonl"
    if not nodes_path.exists():
        _validate_direct_children(path, {"embeddings", "memory_events.jsonl"}, "empty private scope")
        embedding = _capture_present(
            root, embedding_path, SourceOwnerClass.EMBEDDING_MANIFEST, boundary,
            "embeddings/manifest.json", EvidenceSemanticRole.EMBEDDING_MANIFEST, scope,
        )
        metadata = _read_json(embedding_path)
        _validate_storage_manifest(metadata, representation_lock)
        _validate_embedding_storage(path / "embeddings")
        total_rows, next_row = metadata["total_rows"], metadata["next_row"]
        if total_rows != 0 or next_row != 0:
            raise CorrectiveFreezePacketRefused("empty private embedding manifest must prove zero rows and next row")
        if memory_events.exists() and (_regular_file(memory_events).stat().st_size != 0):
            raise CorrectiveFreezePacketRefused("empty private memory events must be absent or empty")
        nodes = _absent(
            SourceOwnerClass.PRIVATE_GRAPH_SOURCE, boundary, "nodes.jsonl", EvidenceSemanticRole.NODES,
            scope, EvidenceAbsenceReason.EMPTY_GRAPH,
        )
        directory = SourceArtifactObservation(
            "private", SourceArtifactPresence.PRESENT, "DIRECTORY_PRESENT", artifact_kind=SourceArtifactKind.DIRECTORY,
        )
        memory = _file_observation(memory_events, "memory_events.jsonl")
        unsigned = {
            "scope_key": scope.identity_payload(), "identity_declaration_evidence": identity.identity_payload(),
            "private_directory_observation": directory.payload(), "nodes_absence_evidence": nodes.identity_payload(),
            "memory_events_observation": memory.payload(), "embedding_manifest_evidence": embedding.identity_payload(),
            "embedding_manifest_total_rows": total_rows, "embedding_manifest_next_row": next_row,
        }
        empty = EmptyPrivateSourceEvidence(
            scope, identity, directory, nodes, memory, embedding, total_rows, next_row, _digest(unsigned),
        )
        return _ScopeCapture(
            (nodes, embedding), MaterializedRootScopePlan(
                scope, RootRepresentationDisposition.NO_VECTOR, MaterializedScopePosture.EMPTY_PRIVATE,
            ), RootSourceScopePlan(
                scope, MaterializedScopePosture.EMPTY_PRIVATE, RootRepresentationDisposition.NO_VECTOR,
                None, target_lane, SourceArtifactPresence.ABSENT,
            ), (), empty,
        )

    _validate_regular_file(nodes_path, "private nodes")
    return _capture_memory_scope(root, path, scope, boundary, SourceOwnerClass.PRIVATE_GRAPH_SOURCE, target_lane, representation_lock)


def _capture_shared_scope(
    root: Path, path: Path, domain_path: Path, scope: RootScopeKey, target_lane: NativeRepresentationLane,
    representation_lock: tuple[str, str, int] | None,
) -> _ScopeCapture:
    path = _real_directory(path, "shared scope")
    boundary = EvidenceOwnerBoundary(
        scope.workspace_id, EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id=scope.domain_id,
    )
    nodes_path = path / "nodes.jsonl"
    motifs_path = domain_path / "motifs.json"
    motif_boundary = EvidenceOwnerBoundary(
        scope.workspace_id, EvidenceOwnerBoundaryKind.DOMAIN, domain_id=scope.domain_id,
    )
    if not nodes_path.exists():
        _validate_direct_children(path, set(), "empty shared scope")
        motifs = _capture_present(
            root, motifs_path, SourceOwnerClass.MOTIF_SOURCE, motif_boundary,
            "motifs.json", EvidenceSemanticRole.MOTIFS, scope,
        )
        nodes = _absent(
            SourceOwnerClass.SHARED_GRAPH_SOURCE, boundary, "nodes.jsonl", EvidenceSemanticRole.NODES,
            scope, EvidenceAbsenceReason.EMPTY_GRAPH,
        )
        return _ScopeCapture(
            (nodes, motifs), MaterializedRootScopePlan(
                scope, RootRepresentationDisposition.NO_VECTOR, MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF,
            ), RootSourceScopePlan(
                scope, MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF, RootRepresentationDisposition.NO_VECTOR,
                scope.domain_id, target_lane, SourceArtifactPresence.PRESENT,
            ), (), None,
        )
    _validate_regular_file(nodes_path, "shared nodes")
    capture = _capture_memory_scope(
        root, path, scope, boundary, SourceOwnerClass.SHARED_GRAPH_SOURCE, target_lane, representation_lock,
    )
    if not motifs_path.exists():
        return capture
    motifs = _capture_present(
        root, motifs_path, SourceOwnerClass.MOTIF_SOURCE, motif_boundary,
        "motifs.json", EvidenceSemanticRole.MOTIFS, scope,
    )
    return _ScopeCapture(
        capture.entries + (motifs,), capture.scope_plan, capture.source_plan,
        capture.unknown_evidence, capture.empty_evidence,
    )


def _capture_memory_scope(
    root: Path, path: Path, scope: RootScopeKey, boundary: EvidenceOwnerBoundary,
    graph_owner: SourceOwnerClass, target_lane: NativeRepresentationLane,
    representation_lock: tuple[str, str, int] | None,
) -> _ScopeCapture:
    embedding_path = path / "embeddings" / "manifest.json"
    _validate_memory_scope_side_stores(path, scope)
    nodes = _capture_present(root, path / "nodes.jsonl", graph_owner, boundary, "nodes.jsonl", EvidenceSemanticRole.NODES, scope)
    embedding = _capture_present(
        root, embedding_path, SourceOwnerClass.EMBEDDING_MANIFEST, boundary,
        "embeddings/manifest.json", EvidenceSemanticRole.EMBEDDING_MANIFEST, scope,
    )
    metadata = _read_json(embedding_path)
    _validate_storage_manifest(metadata, representation_lock)
    _validate_embedding_storage(path / "embeddings")
    _validate_node_embedding_stamps(path / "nodes.jsonl", representation_lock)
    disposition = _representation_disposition_from_workspace_lock(scope, representation_lock, target_lane)
    motif_domain_id = scope.domain_id
    entries = [nodes, embedding]
    unknown: tuple[MetadataLessPerEidEvidence, ...] = ()
    allowed = _memory_scope_direct_children(scope)
    if disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY:
        unknown, extra_entries, allowed_unknown = _metadata_less_evidence_from_nodes(root, path, scope, boundary)
        entries.extend(extra_entries)
        allowed |= allowed_unknown
    _validate_direct_children(path, allowed, "memory scope")
    return _ScopeCapture(
        tuple(entries), MaterializedRootScopePlan(scope, disposition),
        RootSourceScopePlan(scope, MaterializedScopePosture.MEMORY_GRAPH, disposition, motif_domain_id, target_lane),
        unknown,
    )


def _capture_workspace_owner_state(
    *, root: Path, workspace_path: Path, workspace_id: str, workspace_boundary: EvidenceOwnerBoundary,
) -> tuple[tuple[ExplicitSourceEvidence, ...], tuple[ExternalOwnerObservation, ...]]:
    """Capture only canonical owner facts; retained owner trees stay opaque."""

    entries: list[ExplicitSourceEvidence] = []
    observations: list[ExternalOwnerObservation] = []
    for filename, kind in _WORKSPACE_OWNER_FILES.items():
        path = workspace_path / filename
        if path.exists():
            entry = _capture_present(
                root, path, SourceOwnerClass.EXTERNAL_OWNER_OBSERVATION, workspace_boundary,
                filename, EvidenceSemanticRole.EXTERNAL_OBSERVATION,
            )
            entries.append(entry)
            observations.append(ExternalOwnerObservation(
                workspace_id, kind, f"workspace:{filename}", _hash_file(path),
            ))
    for filename in _WORKSPACE_RETAINED_FILES:
        path = workspace_path / filename
        if path.exists():
            _regular_file(path)
    for name in _WORKSPACE_RETAINED_DIRECTORIES:
        path = workspace_path / name
        if path.exists():
            _retained_directory(path, f"workspace retained {name}")
    seeds = workspace_path / "seeds"
    if seeds.exists():
        for seed_path in _direct_directories(_retained_directory(seeds, "seeds directory"), "seed"):
            _validate_direct_children(seed_path, {"seed.json"}, "character seed")
            source_path = seed_path / "seed.json"
            entry = _capture_present(
                root, source_path, SourceOwnerClass.EXTERNAL_OWNER_OBSERVATION, workspace_boundary,
                f"seeds/{seed_path.name}/seed.json", EvidenceSemanticRole.EXTERNAL_OBSERVATION,
            )
            entries.append(entry)
            observations.append(ExternalOwnerObservation(
                workspace_id, ExternalOwnerObservationKind.CHARACTER,
                f"seed:{seed_path.name}", _hash_file(source_path),
            ))
    return tuple(entries), tuple(observations)


def _capture_agent_owner_state(
    *, root: Path, agent_path: Path, workspace_id: str, agent_id: str, boundary: EvidenceOwnerBoundary,
) -> tuple[tuple[ExplicitSourceEvidence, ...], tuple[ExternalOwnerObservation, ...]]:
    entries: list[ExplicitSourceEvidence] = []
    observations: list[ExternalOwnerObservation] = []
    for filename in ("roles.json", "character_state.json"):
        path = agent_path / filename
        if not path.exists():
            continue
        entry = _capture_present(
            root, path, SourceOwnerClass.EXTERNAL_OWNER_OBSERVATION, boundary,
            filename, EvidenceSemanticRole.EXTERNAL_OBSERVATION,
        )
        entries.append(entry)
        observations.append(ExternalOwnerObservation(
            workspace_id, _AGENT_OWNER_FILES[filename], f"agent:{agent_id}:{filename}", _hash_file(path),
        ))
    for filename in _AGENT_RETAINED_FILES:
        path = agent_path / filename
        if path.exists():
            _regular_file(path)
    for name in _AGENT_RETAINED_DIRECTORIES:
        path = agent_path / name
        if path.exists():
            _retained_directory(path, f"agent retained {name}")
    return tuple(entries), tuple(observations)


def _capture_domain_owner_state(
    *, root: Path, domain_path: Path, workspace_id: str, domain_id: str,
) -> tuple[tuple[ExplicitSourceEvidence, ...], tuple[ExternalOwnerObservation, ...]]:
    boundary = EvidenceOwnerBoundary(workspace_id, EvidenceOwnerBoundaryKind.DOMAIN, domain_id=domain_id)
    entries: list[ExplicitSourceEvidence] = []
    observations: list[ExternalOwnerObservation] = []
    for filename, kind in _DOMAIN_OWNER_FILES.items():
        path = domain_path / filename
        if not path.exists():
            continue
        entry = _capture_present(
            root, path, SourceOwnerClass.EXTERNAL_OWNER_OBSERVATION, boundary,
            filename, EvidenceSemanticRole.EXTERNAL_OBSERVATION,
        )
        entries.append(entry)
        observations.append(ExternalOwnerObservation(
            workspace_id, kind, f"domain:{domain_id}:{filename}", _hash_file(path),
        ))
    for filename in _DOMAIN_RETAINED_FILES:
        path = domain_path / filename
        if path.exists():
            _regular_file(path)
    return tuple(entries), tuple(observations)


def _memory_scope_direct_children(scope: RootScopeKey) -> set[str]:
    common = {"nodes.jsonl", "edges.jsonl", "memory_events.jsonl", "embeddings", "logs", "trajectories"}
    if scope.scope_kind is RootScopeKind.PRIVATE:
        return common | {"checkpoints", "trajectories.jsonl"}
    return common


def _validate_memory_scope_side_stores(path: Path, scope: RootScopeKey) -> None:
    for name in ("logs", "trajectories"):
        candidate = path / name
        if candidate.exists():
            _retained_directory(candidate, f"retained {name}")
    if scope.scope_kind is RootScopeKind.PRIVATE:
        checkpoints = path / "checkpoints"
        if checkpoints.exists():
            _retained_directory(checkpoints, "retained checkpoints")
        legacy_trajectory = path / "trajectories.jsonl"
        if legacy_trajectory.exists():
            _regular_file(legacy_trajectory)


def _retained_directory(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise CorrectiveFreezePacketRefused(f"{label} must be a non-symlink directory")
    return path


def _workspace_representation_lock(value: object, workspace_id: str) -> tuple[str, str, int] | None:
    """Read the frozen representation authority directly from workspace metadata."""
    if not isinstance(value, dict):
        raise CorrectiveFreezePacketRefused("workspace metadata is invalid")
    fields = ("embed_provider", "embed_model", "embed_dim")
    present = [field in value for field in fields]
    if not any(present):
        return None
    if not all(present):
        raise CorrectiveFreezePacketRefused("workspace representation lock is partial")
    provider, model, dimension = (value[field] for field in fields)
    if not isinstance(provider, str) or not provider or not isinstance(model, str) or not model:
        raise CorrectiveFreezePacketRefused("workspace representation lock is malformed")
    if not isinstance(dimension, int) or isinstance(dimension, bool) or dimension <= 0:
        raise CorrectiveFreezePacketRefused("workspace representation lock is malformed")
    return provider, model, dimension


def _representation_disposition_from_workspace_lock(
    scope: RootScopeKey, lock: tuple[str, str, int] | None, lane: NativeRepresentationLane,
) -> RootRepresentationDisposition:
    if lock is None:
        if scope.canonical_key in {
            ("ws3", "PRIVATE", "a1"), ("ws4", "PRIVATE", "a1"), ("ws5", "PRIVATE", "a1"),
        }:
            return RootRepresentationDisposition.UNKNOWN_IDENTITY
        raise CorrectiveFreezePacketRefused("memory-bearing scope lacks the frozen workspace representation lock")
    if lock == (lane.provider, lane.model, lane.dimension):
        return RootRepresentationDisposition.TARGET_COMPATIBLE
    if lock == ("hash", "hash:384:torment", 384):
        return RootRepresentationDisposition.REEMBED_REQUIRED
    raise CorrectiveFreezePacketRefused("workspace representation lock contradicts the frozen census")


def _validate_storage_manifest(value: object, lock: tuple[str, str, int] | None) -> None:
    required = {"version", "embedding_dim", "dtype", "rows_per_shard", "active_shard", "next_row", "total_rows"}
    if not isinstance(value, dict) or set(value) != required:
        raise CorrectiveFreezePacketRefused("storage manifest must use the production seven-key form")
    dimension = value["embedding_dim"]
    if not isinstance(dimension, int) or isinstance(dimension, bool) or dimension <= 0:
        raise CorrectiveFreezePacketRefused("storage manifest embedding dimension is invalid")
    for name in ("version", "rows_per_shard", "active_shard", "next_row", "total_rows"):
        item = value[name]
        if not isinstance(item, int) or isinstance(item, bool) or item < 0:
            raise CorrectiveFreezePacketRefused(f"storage manifest {name} is invalid")
    if not isinstance(value["dtype"], str) or not value["dtype"]:
        raise CorrectiveFreezePacketRefused("storage manifest dtype is invalid")
    if lock is not None and dimension != lock[2]:
        raise CorrectiveFreezePacketRefused("storage manifest dimension contradicts workspace representation lock")


def _validate_embedding_storage(path: Path) -> None:
    """Admit only the established shard-store leaves without loading vectors."""

    path = _retained_directory(path, "embedding storage")
    for item in path.iterdir():
        if item.is_symlink() or not item.is_file():
            raise CorrectiveFreezePacketRefused("embedding storage contains an unclassified durable artifact")
        if item.name == "manifest.json":
            continue
        if not re.fullmatch(r"shard_[0-9]+\.(?:npy|map\.jsonl)", item.name):
            raise CorrectiveFreezePacketRefused("embedding storage contains an unclassified durable artifact")


def _validate_node_embedding_stamps(path: Path, lock: tuple[str, str, int] | None) -> None:
    """Use persisted node stamps only as lock-contradiction evidence."""

    if lock is None:
        return
    try:
        rows = [json.loads(line) for line in _regular_file(path).read_text(encoding="utf-8").splitlines() if line]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CorrectiveFreezePacketRefused("canonical nodes source is invalid") from exc
    fields = ("embedding_provider", "embedding_model", "embedding_dim")
    for row in rows:
        if not isinstance(row, dict):
            continue
        present = [field in row for field in fields]
        if not any(present):
            continue
        if not all(present) or tuple(row[field] for field in fields) != lock:
            raise CorrectiveFreezePacketRefused("node embedding stamp contradicts workspace representation lock")


def _metadata_less_evidence_from_nodes(
    root: Path, path: Path, scope: RootScopeKey, boundary: EvidenceOwnerBoundary,
) -> tuple[tuple[MetadataLessPerEidEvidence, ...], tuple[ExplicitSourceEvidence, ...], set[str]]:
    try:
        rows = [json.loads(line) for line in _regular_file(path / "nodes.jsonl").read_text(encoding="utf-8").splitlines() if line]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CorrectiveFreezePacketRefused("metadata-less nodes source is invalid") from exc
    raw = next((item.get("metadata_less_source_evidence") for item in rows if isinstance(item, dict) and isinstance(item.get("metadata_less_source_evidence"), list)), None)
    if raw is None:
        raise CorrectiveFreezePacketRefused("qualified metadata-less scope lacks Phase-9B per-EID evidence")
    return _metadata_less_evidence(root, path, scope, boundary, {"metadata_less_source_evidence": raw})


def _metadata_less_evidence(
    root: Path, path: Path, scope: RootScopeKey, boundary: EvidenceOwnerBoundary, representation: dict[str, object],
) -> tuple[tuple[MetadataLessPerEidEvidence, ...], tuple[ExplicitSourceEvidence, ...], set[str]]:
    raw = representation["metadata_less_source_evidence"]
    if not isinstance(raw, list) or not raw:
        raise CorrectiveFreezePacketRefused("metadata-less representation requires per-EID evidence")
    evidence: list[MetadataLessPerEidEvidence] = []
    entries: list[ExplicitSourceEvidence] = []
    allowed: set[str] = set()
    for item in raw:
        required = {"eid", "vector_locator", "canonical_text_locator", "metadata_less_source_evidence_identity"}
        if not isinstance(item, dict) or set(item) != required or not isinstance(item["eid"], int) or item["eid"] < 0:
            raise CorrectiveFreezePacketRefused("metadata-less per-EID evidence shape is invalid")
        eid = item["eid"]
        vector_locator = item["vector_locator"]
        text_locator = item["canonical_text_locator"]
        if vector_locator != f"emb_{eid}.npy" or text_locator != f"canonical_text_{eid}.json":
            raise CorrectiveFreezePacketRefused("metadata-less evidence must use exact per-EID source locators")
        identity = item["metadata_less_source_evidence_identity"]
        if not isinstance(identity, str) or not identity:
            raise CorrectiveFreezePacketRefused("metadata-less source evidence identity must be text")
        vector_path, text_path = path / vector_locator, path / text_locator
        dtype, shape = _npy_header(vector_path)
        vector = _capture_present(
            root, vector_path, SourceOwnerClass.METADATA_LESS_PER_EID_LEGACY_REPRESENTATION,
            boundary, vector_locator, EvidenceSemanticRole.LEGACY_REPRESENTATION, scope,
        )
        text = _capture_present(
            root, text_path, SourceOwnerClass.PRIVATE_GRAPH_SOURCE, boundary,
            text_locator, EvidenceSemanticRole.NODES, scope,
        )
        evidence.append(MetadataLessPerEidEvidence(scope, eid, vector, text, dtype, shape, identity))
        entries.extend((vector, text))
        allowed.update((vector_locator, text_locator))
    if len({item.eid for item in evidence}) != len(evidence):
        raise CorrectiveFreezePacketRefused("metadata-less per-EID evidence repeats an EID")
    return tuple(evidence), tuple(entries), allowed


def _expected_census(workspaces: tuple[WorkspaceRootAdmissionPlan, ...]) -> ExpectedRootCensus:
    materialized = tuple(scope for workspace in workspaces for scope in workspace.materialized_scopes)
    runtime = tuple(scope for workspace in workspaces for scope in workspace.runtime_scopes)
    counts = tuple(RepresentationDispositionCount(
        disposition, sum(scope.representation_disposition is disposition for scope in runtime),
    ) for disposition in RootRepresentationDisposition)
    return ExpectedRootCensus(
        workspace_count=len(workspaces),
        materialized_private_scope_count=sum(scope.scope_key.scope_kind is RootScopeKind.PRIVATE for scope in materialized),
        materialized_shared_scope_count=sum(scope.scope_key.scope_kind is RootScopeKind.SHARED for scope in materialized),
        total_materialized_scope_count=len(materialized),
        declared_empty_shared_scope_count=sum(
            scope.materialization_posture is MaterializedScopePosture.DECLARED_EMPTY_SHARED for scope in runtime
        ),
        empty_private_identity_scope_count=sum(
            scope.materialization_posture is MaterializedScopePosture.EMPTY_PRIVATE for scope in runtime
        ),
        representation_disposition_counts=counts,
        workspace_topology_counts=WorkspaceTopologyCounts(
            zero_private_workspaces=sum(not workspace.private_materialized_scopes for workspace in workspaces),
            one_private_workspace=sum(len(workspace.private_materialized_scopes) == 1 for workspace in workspaces),
            multiple_private_workspaces=sum(len(workspace.private_materialized_scopes) > 1 for workspace in workspaces),
            zero_shared_workspaces=sum(not workspace.shared_materialized_scopes for workspace in workspaces),
            one_shared_workspace=sum(len(workspace.shared_materialized_scopes) == 1 for workspace in workspaces),
            multiple_shared_workspaces=sum(len(workspace.shared_materialized_scopes) > 1 for workspace in workspaces),
        ),
    )


def _declared_domains(value: object) -> set[str]:
    if not isinstance(value, dict) or "domains" not in value or set(value) - {"domains", "legacy_default_domain"}:
        raise CorrectiveFreezePacketRefused("domains declaration must use the direct/default source contract")
    domains = value["domains"]
    if not isinstance(domains, list) or any(not isinstance(item, str) or not item for item in domains):
        raise CorrectiveFreezePacketRefused("domains declaration must list text domain identities")
    declared = set(domains)
    if len(declared) != len(domains):
        raise CorrectiveFreezePacketRefused("domains declaration repeats an identity")
    default = value.get("legacy_default_domain")
    if default is not None:
        if not isinstance(default, str) or not default:
            raise CorrectiveFreezePacketRefused("legacy default domain identity must be text")
        declared.add(default)
    return declared


def _capture_present(
    root: Path, path: Path, owner_class: SourceOwnerClass, boundary: EvidenceOwnerBoundary,
    locator: str, role: EvidenceSemanticRole, scope: RootScopeKey | None = None,
) -> ExplicitSourceEvidence:
    source = _regular_file(path)
    return ExplicitSourceEvidence(
        owner_class=owner_class, owner_boundary=boundary, canonical_locator=locator, semantic_role=role,
        presence_expectation=EvidencePresenceExpectation.EXPECTED_PRESENT, scope_key=scope,
        byte_length=source.stat().st_size, sha256_hex=_hash_file(source),
    )


def _absent(
    owner_class: SourceOwnerClass, boundary: EvidenceOwnerBoundary, locator: str, role: EvidenceSemanticRole,
    scope: RootScopeKey, reason: EvidenceAbsenceReason,
) -> ExplicitSourceEvidence:
    return ExplicitSourceEvidence(
        owner_class=owner_class, owner_boundary=boundary, canonical_locator=locator, semantic_role=role,
        presence_expectation=EvidencePresenceExpectation.EXPECTED_ABSENT, scope_key=scope, absence_reason=reason,
    )


def _file_observation(path: Path, locator: str) -> SourceArtifactObservation:
    if not path.exists():
        return SourceArtifactObservation(locator, SourceArtifactPresence.ABSENT, "ABSENT")
    source = _regular_file(path)
    return SourceArtifactObservation(locator, SourceArtifactPresence.PRESENT, "PRESENT", source.stat().st_size, _hash_file(source))


def _npy_header(path: Path) -> tuple[str, tuple[int, ...]]:
    """Read just an ``.npy`` header; never materialize vector values."""

    source = _regular_file(path)
    try:
        with source.open("rb") as stream:
            prefix = stream.read(8)
            if len(prefix) != 8 or prefix[:6] != b"\x93NUMPY":
                raise ValueError
            major = prefix[6]
            if major == 1:
                raw_length = stream.read(2)
                header_length = struct.unpack("<H", raw_length)[0]
            elif major in {2, 3}:
                raw_length = stream.read(4)
                header_length = struct.unpack("<I", raw_length)[0]
            else:
                raise ValueError
            header = ast.literal_eval(stream.read(header_length).decode("latin1"))
    except (OSError, ValueError, SyntaxError, UnicodeDecodeError, struct.error) as exc:
        raise CorrectiveFreezePacketRefused("metadata-less vector must have a readable NumPy header") from exc
    if not isinstance(header, dict) or set(header) != {"descr", "fortran_order", "shape"}:
        raise CorrectiveFreezePacketRefused("metadata-less NumPy header shape is unsupported")
    dtype = header["descr"]
    shape = header["shape"]
    if not isinstance(dtype, str) or dtype not in _NPY_DTYPE_NAMES or header["fortran_order"] is not False:
        raise CorrectiveFreezePacketRefused("metadata-less NumPy dtype/order is unsupported")
    if not isinstance(shape, tuple) or not shape or any(not isinstance(item, int) or item < 0 for item in shape):
        raise CorrectiveFreezePacketRefused("metadata-less NumPy shape is unsupported")
    return _NPY_DTYPE_NAMES[dtype], shape


def _source_root(value: Path) -> Path:
    root = Path(value).expanduser().resolve()
    return _real_directory(root, "typed evidence source root")


def _real_directory(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise CorrectiveFreezePacketRefused(f"{label} must be a non-symlink directory")
    return path


def _alternate_root_directory(path: Path) -> Path:
    try:
        information = path.lstat()
    except OSError as exc:
        raise CorrectiveFreezePacketRefused("excluded alternate root is missing or cannot be inspected") from exc
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if stat.S_ISLNK(information.st_mode) or getattr(information, "st_file_attributes", 0) & reparse_flag or not path.is_dir():
        raise CorrectiveFreezePacketRefused("excluded alternate root must be a real top-level directory")
    return path


def _regular_file(path: Path) -> Path:
    if path.is_symlink() or not path.is_file():
        raise CorrectiveFreezePacketRefused("typed evidence source must be a non-symlink regular file")
    return path


def _validate_regular_file(path: Path, label: str) -> None:
    try:
        _regular_file(path)
    except CorrectiveFreezePacketRefused as exc:
        raise CorrectiveFreezePacketRefused(f"{label} must be a regular file") from exc


def _direct_directories(path: Path, label: str) -> tuple[Path, ...]:
    directories: list[Path] = []
    for item in path.iterdir():
        if item.is_symlink():
            raise CorrectiveFreezePacketRefused(f"{label} path must not be a symlink")
        if item.is_dir():
            directories.append(item)
        elif item.is_file():
            raise CorrectiveFreezePacketRefused(f"{label} container contains an unclassified durable file")
    return tuple(sorted(directories, key=lambda item: item.name))


def _validate_direct_children(path: Path, allowed: set[str], label: str) -> None:
    allowed_names = set(allowed)
    observed = {item.name for item in path.iterdir()}
    if observed - allowed_names:
        raise CorrectiveFreezePacketRefused(f"{label} contains an unclassified durable artifact")
    for item in path.iterdir():
        if item.is_symlink():
            raise CorrectiveFreezePacketRefused(f"{label} paths must not be symlinks")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with _regular_file(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise CorrectiveFreezePacketRefused("typed evidence source file cannot be read") from exc
    return digest.hexdigest()


def _read_json(path: Path) -> object:
    try:
        return json.loads(_regular_file(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CorrectiveFreezePacketRefused("typed evidence JSON source is invalid") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_intent_text(value).encode("utf-8")).hexdigest()


def _top_level_locator(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise CorrectiveFreezePacketRefused("source locator must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or len(path.parts) != 1 or any(part in {"", ".", ".."} for part in path.parts):
        raise CorrectiveFreezePacketRefused("source locator must be a direct child")
    return value


__all__ = [
    "ExcludedAlternateRootLocator",
    "ExcludedSourceArtifactLocator",
    "RealRootTypedEvidenceAdapter",
]
