"""Synthetic-only integrated verification for already-supported legacy migration.

This module is deliberately a coordinator, not another admission boundary.  It
performs whole-snapshot verification before persisting any evidence, invokes
the existing bounded admission services in dependency order, and returns a
deterministically ordered verification report.  It has no runtime-storage or
cutover integration.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import sqlite3
from typing import Final
from uuid import UUID

from ..errors import SubstrateInvariantViolation
from ..ids import native_id_to_bytes
from ..schema import open_schema
from .admission import NativeLegacyObjectAdmissionService, NativeLegacyRelationshipAdmissionService
from .deep_memory_admission import NativeLegacyDeepMemoryAdmissionService
from .identity_admission import NativeLegacyIdentityAdmissionService
from .inventory import InventorySnapshot, inventory_snapshot
from .motif_admission import NativeLegacyMotifAdmissionService
from .proposal_admission import NativeLegacyProposalAdmissionService
from .representation_admission import NativeLegacyRepresentationAdmissionService
from .snapshot import LegacySnapshotManifest, load_snapshot_manifest, verify_snapshot


_ORDER: Final[tuple[str, ...]] = (
    "IDENTITY_CHARACTER",
    "CORE_OBJECT",
    "CORE_RELATIONSHIP",
    "CORE_EMBEDDING_REPRESENTATION",
    "MOTIF_DERIVATION",
    "DEEP_MEMORY_DERIVATION",
    "PROPOSAL_EFFECTIVE_STATE",
)


@dataclass(frozen=True)
class MigrationRehearsalConfig:
    """Existing native identities needed by the already-implemented services."""

    native_core_id: UUID
    idempotency_namespace_id: UUID
    object_identity_namespace_id: UUID
    relationship_identity_namespace_id: UUID
    unknown_semantic_scope_id: UUID


@dataclass(frozen=True)
class ArtifactCoverage:
    observed_relative_locator: str
    evidence_class: str
    coverage: str


@dataclass(frozen=True)
class FamilyAdmissionCount:
    family: str
    admitted: int
    quarantined: int
    unknown: int
    not_admitted: int

    @property
    def total(self) -> int:
        return self.admitted + self.quarantined + self.unknown + self.not_admitted


@dataclass(frozen=True)
class MigrationRehearsalReport:
    legacy_snapshot_id: UUID
    native_core_id: UUID
    execution_order: tuple[str, ...]
    artifact_counts_by_evidence_class: tuple[tuple[str, int], ...]
    coverage: tuple[ArtifactCoverage, ...]
    admission_counts: tuple[FamilyAdmissionCount, ...]
    native_object_count: int
    native_relationship_count: int
    native_representation_count: int
    object_alias_count: int
    relationship_alias_count: int
    legacy_admission_count: int
    semantic_transition_count: int
    unknown_or_evidence_only_artifact_count: int
    active_authorization_count: int
    invariant_verification_result: bool

    @property
    def quarantined_or_not_admitted_count(self) -> int:
        return sum(item.quarantined + item.not_admitted for item in self.admission_counts)


class NativeLegacyMigrationRehearsal:
    """Run selected frozen migration families in explicit dependency order."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection)
        self._connection = connection

    def run(
        self,
        *,
        snapshot_root: str | Path,
        manifest_path: str | Path,
        config: MigrationRehearsalConfig,
    ) -> MigrationRehearsalReport:
        """Verify all bytes before any inventory or semantic admission occurs."""
        manifest = load_snapshot_manifest(manifest_path)
        # This preflight is intentionally before ``inventory_snapshot`` and every
        # service call.  It prevents a changed later artifact from permitting an
        # earlier family to publish semantics.
        verify_snapshot(snapshot_root=snapshot_root, manifest=manifest)
        inventory = inventory_snapshot(
            self._connection, snapshot_root=snapshot_root, manifest_path=manifest_path
        )
        locators = {artifact.observed_relative_locator for artifact in manifest.artifacts}
        family_counts: list[FamilyAdmissionCount] = []

        if _has_identity_definitions(locators):
            identity = NativeLegacyIdentityAdmissionService(self._connection).admit_identity_definitions(
                snapshot_root=snapshot_root,
                manifest_path=manifest_path,
                idempotency_namespace_id=config.idempotency_namespace_id,
                object_identity_namespace_id=config.object_identity_namespace_id,
                unknown_semantic_scope_id=config.unknown_semantic_scope_id,
            )
            family_counts.append(_count_results("IDENTITY_CHARACTER", identity.results))

        if "nodes.jsonl" in locators:
            objects = NativeLegacyObjectAdmissionService(self._connection).admit_nodes_current_state(
                snapshot_root=snapshot_root,
                manifest_path=manifest_path,
                idempotency_namespace_id=config.idempotency_namespace_id,
                object_identity_namespace_id=config.object_identity_namespace_id,
                unknown_semantic_scope_id=config.unknown_semantic_scope_id,
            )
            family_counts.append(_count_results("CORE_OBJECT", objects.results))

        if "edges.jsonl" in locators:
            relationships = NativeLegacyRelationshipAdmissionService(self._connection).admit_edges_current_state(
                snapshot_root=snapshot_root,
                manifest_path=manifest_path,
                idempotency_namespace_id=config.idempotency_namespace_id,
                relationship_identity_namespace_id=config.relationship_identity_namespace_id,
                unknown_semantic_scope_id=config.unknown_semantic_scope_id,
            )
            family_counts.append(_count_results("CORE_RELATIONSHIP", relationships.results))

        if "nodes.jsonl" in locators and "embeddings/manifest.json" in locators:
            embeddings = NativeLegacyRepresentationAdmissionService(self._connection).admit_embedding_evidence(
                snapshot_root=snapshot_root,
                manifest_path=manifest_path,
                idempotency_namespace_id=config.idempotency_namespace_id,
            )
            family_counts.append(_count_results("CORE_EMBEDDING_REPRESENTATION", embeddings.results))

        if any(PurePosixPath(locator).name == "motifs.json" for locator in locators):
            motifs = NativeLegacyMotifAdmissionService(self._connection).admit_motifs_current_state(
                snapshot_root=snapshot_root,
                manifest_path=manifest_path,
                idempotency_namespace_id=config.idempotency_namespace_id,
                motif_identity_namespace_id=config.object_identity_namespace_id,
                membership_identity_namespace_id=config.relationship_identity_namespace_id,
                unknown_semantic_scope_id=config.unknown_semantic_scope_id,
            )
            family_counts.append(_count_results("MOTIF_DERIVATION", motifs.results))

        if any(_is_deep_memory_locator(locator) for locator in locators):
            deep = NativeLegacyDeepMemoryAdmissionService(self._connection).admit_deep_memory_current_state(
                snapshot_root=snapshot_root,
                manifest_path=manifest_path,
                idempotency_namespace_id=config.idempotency_namespace_id,
            )
            family_counts.append(_count_results("DEEP_MEMORY_DERIVATION", deep.results))

        if any(PurePosixPath(locator).name == "proposals.jsonl" for locator in locators):
            proposals = NativeLegacyProposalAdmissionService(self._connection).admit_proposals_effective_state(
                snapshot_root=snapshot_root,
                manifest_path=manifest_path,
                idempotency_namespace_id=config.idempotency_namespace_id,
                object_identity_namespace_id=config.object_identity_namespace_id,
                unknown_semantic_scope_id=config.unknown_semantic_scope_id,
            )
            family_counts.append(_count_results("PROPOSAL_EFFECTIVE_STATE", proposals.results))

        _verify_whole_core(self._connection)
        coverage = tuple(
            ArtifactCoverage(
                artifact.observed_relative_locator,
                artifact.artifact_class,
                _coverage_for_artifact(artifact.observed_relative_locator, artifact.artifact_class),
            )
            for artifact in sorted(inventory.artifacts, key=lambda item: item.observed_relative_locator)
        )
        counts = Counter(artifact.artifact_class for artifact in inventory.artifacts)
        return MigrationRehearsalReport(
            legacy_snapshot_id=manifest.legacy_snapshot_id,
            native_core_id=config.native_core_id,
            execution_order=tuple(item.family for item in family_counts),
            artifact_counts_by_evidence_class=tuple(sorted(counts.items())),
            coverage=coverage,
            admission_counts=tuple(family_counts),
            native_object_count=_scalar(self._connection, "SELECT count(*) FROM objects"),
            native_relationship_count=_scalar(self._connection, "SELECT count(*) FROM relationships"),
            native_representation_count=_scalar(self._connection, "SELECT count(*) FROM representations"),
            object_alias_count=_scalar(self._connection, "SELECT count(*) FROM legacy_object_aliases"),
            relationship_alias_count=_scalar(self._connection, "SELECT count(*) FROM legacy_relationship_aliases"),
            legacy_admission_count=_scalar(self._connection, "SELECT count(*) FROM legacy_admission_records"),
            semantic_transition_count=_scalar(self._connection, "SELECT count(*) FROM semantic_transitions"),
            unknown_or_evidence_only_artifact_count=sum(
                item.coverage in {"EVIDENCE_ONLY", "ACCELERATION_ONLY", "UNKNOWN"}
                for item in coverage
            ),
            active_authorization_count=_scalar(
                self._connection,
                "SELECT count(*) FROM object_revisions WHERE authority_category='ACTIVE_AUTHORIZATION'",
            ),
            invariant_verification_result=True,
        )


def _count_results(family: str, results: object) -> FamilyAdmissionCount:
    statuses = Counter(getattr(item, "admission_status") for item in results)
    return FamilyAdmissionCount(
        family,
        statuses["ADMITTED"],
        statuses["QUARANTINED"],
        statuses["UNKNOWN"],
        statuses["NOT_ADMITTED"],
    )


def _has_identity_definitions(locators: set[str]) -> bool:
    return any(PurePosixPath(locator).name in {"identity.json", "seed.json"} for locator in locators)


def _is_deep_memory_locator(locator: str) -> bool:
    path = PurePosixPath(locator)
    return path.name == "memories.jsonl" and "deep_memory" in path.parts


def _coverage_for_artifact(locator: str, evidence_class: str) -> str:
    name = PurePosixPath(locator).name
    if name in {"nodes.jsonl", "identity.json", "seed.json", "proposals.jsonl"}:
        return "ADMITTED_PRIMARY_STATE"
    if name == "edges.jsonl":
        return "ADMITTED_RELATIONSHIP"
    if name in {"motifs.json", "memories.jsonl", "manifest.json"} or locator.endswith(".map.jsonl") or locator.endswith(".npy"):
        return "ADMITTED_DERIVATION"
    if evidence_class == "LEGACY_ACCELERATION_EVIDENCE":
        return "ACCELERATION_ONLY"
    if evidence_class == "UNKNOWN":
        return "UNKNOWN"
    return "EVIDENCE_ONLY"


def _scalar(connection: sqlite3.Connection, sql: str) -> int:
    return int(connection.execute(sql).fetchone()[0])


def _verify_whole_core(connection: sqlite3.Connection) -> None:
    """Bounded whole-core H1–H8 checks for the staged rehearsal database."""
    checks: tuple[tuple[str, str], ...] = (
        # H1 current pointers resolve to their exact owner and ordinal.
        ("H1 object current pointer is incomplete", """
            SELECT 1 FROM objects o LEFT JOIN object_revisions r
              ON r.object_id=o.object_id AND r.object_revision_id=o.current_revision_id
             AND r.revision_ordinal=o.current_revision_ordinal
            WHERE r.object_revision_id IS NULL LIMIT 1
        """),
        ("H1 relationship current pointer is incomplete", """
            SELECT 1 FROM relationships r LEFT JOIN relationship_revisions v
              ON v.relationship_id=r.relationship_id AND v.relationship_revision_id=r.current_revision_id
             AND v.revision_ordinal=r.current_revision_ordinal
            WHERE v.relationship_revision_id IS NULL LIMIT 1
        """),
        # H2 every transition has a typed publication effect.
        ("H2 transition lacks a typed effect", """
            SELECT 1 FROM semantic_transitions t WHERE NOT EXISTS (
              SELECT 1 FROM object_revision_effects e WHERE e.transition_id=t.transition_id
              UNION SELECT 1 FROM relationship_revision_effects e WHERE e.transition_id=t.transition_id
              UNION SELECT 1 FROM representation_state_effects e WHERE e.transition_id=t.transition_id
              UNION SELECT 1 FROM reconciliation_state_effects e WHERE e.transition_id=t.transition_id
              UNION SELECT 1 FROM legacy_admission_effects e WHERE e.transition_id=t.transition_id
            ) LIMIT 1
        """),
        # H3 an operation cannot both publish and durably reject.
        ("H3 operation has both rejection and transition", """
            SELECT 1 FROM operations o JOIN semantic_transitions t ON t.operation_id=o.operation_id
            JOIN operation_rejections r ON r.operation_id=o.operation_id LIMIT 1
        """),
        # H4 applies only to any state that claims READY.
        ("H4 ready representation has incomplete integrity", """
            SELECT 1 FROM representation_current_state s
            LEFT JOIN representation_payloads p ON p.representation_id=s.representation_id
            LEFT JOIN integrity_measurements m ON m.measurement_id=s.selected_integrity_measurement_id
            LEFT JOIN integrity_expectations x ON x.expectation_id=m.expectation_id
            WHERE s.readiness='READY' AND (p.representation_id IS NULL OR m.result!='MATCH'
                OR x.subject_kind!='REPRESENTATION' OR m.observed_value!=x.expected_value)
            LIMIT 1
        """),
        ("H4 ready representation has non-ready dependency", """
            SELECT 1 FROM representation_dependencies d
            JOIN representation_current_state s ON s.representation_id=d.representation_id
            JOIN representation_current_state dependency ON dependency.representation_id=d.dependency_representation_id
            WHERE s.readiness='READY' AND (dependency.readiness!='READY' OR dependency.operational_disposition!='USABLE')
            LIMIT 1
        """),
        # H5 static guard: immutable aggregates retain their installed protection.
        ("H5 object revision immutability trigger is absent", """
            SELECT 1 WHERE NOT EXISTS (
              SELECT 1 FROM sqlite_master WHERE type='trigger' AND name='immutable_object_revision_update'
            )
        """),
        # H6 no reconciliation current pointer can be dangling.
        ("H6 reconciliation current pointer is incomplete", """
            SELECT 1 FROM reconciliation_cases c LEFT JOIN reconciliation_case_states s
              ON s.reconciliation_case_id=c.reconciliation_case_id AND s.reconciliation_state_id=c.current_state_id
             AND s.state_ordinal=c.current_state_ordinal
            WHERE c.current_state_id IS NOT NULL AND s.reconciliation_state_id IS NULL LIMIT 1
        """),
        # H7 every ADMITTED evidence record has a typed legacy-admission effect.
        ("H7 admitted evidence lacks typed legacy publication", """
            SELECT 1 FROM legacy_admission_records a WHERE a.admission_status='ADMITTED' AND NOT EXISTS (
              SELECT 1 FROM legacy_admission_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id
              WHERE e.admission_record_id=a.admission_record_id AND t.origin_kind='LEGACY_ADMISSION'
            ) LIMIT 1
        """),
        # H8 outputs must point to an effect emitted by the same operation.
        ("H8 object output does not match publication", """
            SELECT 1 FROM operation_outputs o WHERE o.output_kind='OBJECT' AND NOT EXISTS (
              SELECT 1 FROM semantic_transitions t JOIN object_revision_effects e ON e.transition_id=t.transition_id
              WHERE t.operation_id=o.operation_id AND e.object_id=o.object_id
                AND e.object_revision_id=o.object_revision_id AND e.object_revision_ordinal=o.object_revision_ordinal
            ) LIMIT 1
        """),
        ("H8 relationship output does not match publication", """
            SELECT 1 FROM operation_outputs o WHERE o.output_kind='RELATIONSHIP' AND NOT EXISTS (
              SELECT 1 FROM semantic_transitions t JOIN relationship_revision_effects e ON e.transition_id=t.transition_id
              WHERE t.operation_id=o.operation_id AND e.relationship_id=o.relationship_id
                AND e.relationship_revision_id=o.relationship_revision_id AND e.relationship_revision_ordinal=o.relationship_revision_ordinal
            ) LIMIT 1
        """),
        ("H8 representation output does not match publication", """
            SELECT 1 FROM operation_outputs o WHERE o.output_kind='REPRESENTATION' AND NOT EXISTS (
              SELECT 1 FROM semantic_transitions t JOIN representation_state_effects e ON e.transition_id=t.transition_id
              WHERE t.operation_id=o.operation_id AND e.representation_id=o.representation_id
            ) LIMIT 1
        """),
    )
    foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_keys:
        raise SubstrateInvariantViolation("whole-core foreign key closure failed")
    for message, query in checks:
        if connection.execute(query).fetchone() is not None:
            raise SubstrateInvariantViolation(message)
