"""Conservative admission of frozen legacy motif current-state evidence.

The supported source is the current workspace/domain ``motifs.json`` registry.
Each selected registry entry becomes a derived logical object; its EID members
become identity-bound ``MOTIF_MEMBERSHIP`` relationships in the same semantic
commit.  ``motif_events.jsonl`` is intentionally never read for semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path, PurePosixPath
import sqlite3
import time
from typing import Any, Final
from uuid import UUID

from ..canonical_intent import canonical_intent_text
from ..errors import SubstrateInvariantViolation, SubstrateObjectNotFound, SubstrateRevisionConflict
from ..ids import native_id_from_bytes, native_id_to_bytes
from ..objects import SubstrateTx, execute_semantic
from ..schema import open_schema
from .admission import (
    _admission_record_for_artifact_record,
    _ensure_admission_batch,
    _ensure_artifact_record,
    _evidence_idempotency_key,
    _new,
)
from .inventory import inventory_snapshot
from .snapshot import LegacyArtifact, LegacySnapshotManifest, load_snapshot_manifest


LEGACY_DERIVED_MOTIF_OBJECT_KIND: Final[str] = "LEGACY_DERIVED_MOTIF"
MOTIF_MEMBERSHIP_RELATIONSHIP_KIND: Final[str] = "MOTIF_MEMBERSHIP"
LEGACY_MOTIF_ALIAS_KIND: Final[str] = "MOTIF_ID"
_ADMISSION_BATCH_IDENTITY: Final[str] = "TMS-LEGACY-MOTIF-ADMISSION-7F3D"


@dataclass(frozen=True)
class LegacyMotifCandidate:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    observed_relative_locator: str
    motif_id: str
    domain_id: str
    member_eids: tuple[int, ...]
    motif_payload: dict[str, Any]

    @property
    def record_identity(self) -> str:
        return _record_identity(self.observed_relative_locator, self.motif_id)

    @property
    def record_locator(self) -> str:
        return f"{self.observed_relative_locator}#motif:{self.motif_id}"


@dataclass(frozen=True)
class LegacyMotifAdmissionRecord:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    observed_relative_locator: str
    record_identity: str
    record_locator: str
    admission_status: str
    reason: str
    motif_id: str | None = None


@dataclass(frozen=True)
class LegacyMotifMembershipResult:
    member_eid: int
    relationship_id: UUID
    revision_id: UUID


@dataclass(frozen=True)
class LegacyMotifAdmissionResult:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    observed_relative_locator: str
    motif_id: str | None
    admission_status: str
    admission_record_id: UUID
    operation_id: UUID
    motif_object_id: UUID | None = None
    motif_revision_id: UUID | None = None
    transition_id: UUID | None = None
    memberships: tuple[LegacyMotifMembershipResult, ...] = ()


@dataclass(frozen=True)
class LegacyMotifAdmissionRun:
    legacy_snapshot_id: UUID
    results: tuple[LegacyMotifAdmissionResult, ...]


class NativeLegacyMotifAdmissionService:
    """Admit verified motif registry entries, never motif history or replay."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection)
        self._connection = connection

    def admit_motifs_current_state(
        self,
        *,
        snapshot_root: str | Path,
        manifest_path: str | Path,
        idempotency_namespace_id: UUID,
        motif_identity_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyMotifAdmissionRun:
        """Admit only complete current-state motifs with every member resolved."""
        self._require_admission_namespaces(
            idempotency_namespace_id,
            motif_identity_namespace_id,
            membership_identity_namespace_id,
            unknown_semantic_scope_id,
        )
        manifest = load_snapshot_manifest(manifest_path)
        inventory_snapshot(
            self._connection, snapshot_root=snapshot_root, manifest_path=manifest_path
        )
        candidates, records = _extract_motif_evidence(snapshot_root, manifest)
        results: list[LegacyMotifAdmissionResult] = []
        for item in sorted((*candidates, *records), key=_item_sort_key):
            if isinstance(item, LegacyMotifCandidate):
                results.append(
                    self._admit_candidate(
                        manifest,
                        item,
                        idempotency_namespace_id,
                        motif_identity_namespace_id,
                        membership_identity_namespace_id,
                        unknown_semantic_scope_id,
                    )
                )
            else:
                results.append(self._record_uncertainty(manifest, item, idempotency_namespace_id))
        return LegacyMotifAdmissionRun(manifest.legacy_snapshot_id, tuple(results))

    def resolve_legacy_motif_alias(
        self,
        *,
        legacy_source_namespace_id: UUID,
        motif_id: str,
    ) -> UUID:
        """Resolve only a stable motif ID within its recorded source namespace."""
        if not isinstance(motif_id, str) or not motif_id:
            raise ValueError("legacy motif ID must be non-empty text")
        row = self._connection.execute(
            """
            SELECT object_id FROM legacy_object_aliases
            WHERE legacy_source_namespace_id=? AND alias_kind=? AND alias_value=?
            """,
            (native_id_to_bytes(legacy_source_namespace_id), LEGACY_MOTIF_ALIAS_KIND, motif_id),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("namespaced legacy motif alias was not found")
        return native_id_from_bytes(row[0])

    def _admit_candidate(
        self,
        manifest: LegacySnapshotManifest,
        candidate: LegacyMotifCandidate,
        idempotency_namespace_id: UUID,
        motif_identity_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyMotifAdmissionResult:
        intent = _candidate_intent(candidate)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "ADMIT_LEGACY_MOTIF_CURRENT",
            intent,
            lambda operation_id: self._recorded_result(operation_id, manifest, candidate),
            lambda tx: self._publish_candidate(
                tx,
                manifest,
                candidate,
                motif_identity_namespace_id,
                membership_identity_namespace_id,
                unknown_semantic_scope_id,
            ),
        )

    def _record_uncertainty(
        self,
        manifest: LegacySnapshotManifest,
        record: LegacyMotifAdmissionRecord,
        idempotency_namespace_id: UUID,
    ) -> LegacyMotifAdmissionResult:
        intent = _record_intent(record)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "RECORD_LEGACY_MOTIF_ADMISSION_" + record.admission_status,
            intent,
            lambda operation_id: self._recorded_result(operation_id, manifest, record),
            lambda tx: self._publish_uncertainty(tx, manifest, record),
        )

    def _publish_candidate(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        candidate: LegacyMotifCandidate,
        motif_identity_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyMotifAdmissionResult:
        snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
        source_namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
        artifact_id = native_id_to_bytes(candidate.legacy_artifact_id)
        batch_id = _ensure_admission_batch(tx, snapshot_id, _ADMISSION_BATCH_IDENTITY)
        artifact_record_id = _ensure_artifact_record(
            tx, artifact_id, candidate.record_identity, candidate.record_locator
        )
        if _admission_record_for_artifact_record(tx, batch_id, artifact_record_id) is not None:
            raise SubstrateRevisionConflict("legacy motif evidence record already has an admission result")
        members, unresolved_reason = self._resolve_members(
            tx, source_namespace_id, candidate.member_eids
        )
        if unresolved_reason is not None:
            return self._publish_candidate_quarantine(
                tx,
                manifest,
                candidate,
                batch_id,
                artifact_record_id,
                unresolved_reason,
            )
        if tx.execute(
            """
            SELECT object_id FROM legacy_object_aliases
            WHERE legacy_source_namespace_id=? AND alias_kind=? AND alias_value=?
            """,
            (source_namespace_id, LEGACY_MOTIF_ALIAS_KIND, candidate.motif_id),
        ).fetchone() is not None:
            raise SubstrateRevisionConflict("legacy motif alias is already admitted for this source namespace")

        motif_object_id, motif_revision_id, transition_id, admission_record_id = (
            _new(),
            _new(),
            _new(),
            _new(),
        )
        membership_rows = [(_new(), _new(), member) for member in members]
        motif_scope_id = native_id_to_bytes(unknown_semantic_scope_id)
        now_ns = time.time_ns()
        tx.execute(
            """
            INSERT INTO objects(
                object_id,identity_namespace_id,object_kind,creating_transition_id,
                current_revision_id,current_revision_ordinal,created_at_ns
            ) VALUES (?,?,?,?,?,?,?)
            """,
            (
                motif_object_id,
                native_id_to_bytes(motif_identity_namespace_id),
                LEGACY_DERIVED_MOTIF_OBJECT_KIND,
                transition_id,
                motif_revision_id,
                1,
                now_ns,
            ),
        )
        tx.execute(
            """
            INSERT INTO object_revisions(
                object_revision_id,object_id,revision_ordinal,lineage_kind,
                predecessor_revision_id,predecessor_revision_ordinal,effective_semantic_scope_id,
                existence_state,lifecycle_state,lifecycle_authoritative,governance_state,
                authority_category,provenance_id,payload_format,payload_text,created_at_ns
            ) VALUES (?,?,1,'LEGACY_PREDECESSOR_UNKNOWN',NULL,NULL,?,'EXISTS','UNKNOWN',0,
                      'UNKNOWN','NOT_APPLICABLE',NULL,'JSON',?,?)
            """,
            (motif_revision_id, motif_object_id, motif_scope_id, canonical_intent_text(candidate.motif_payload), now_ns),
        )
        for relationship_id, relationship_revision_id, member in membership_rows:
            tx.execute(
                """
                INSERT INTO relationships(
                    relationship_id,identity_namespace_id,relationship_kind,creating_transition_id,
                    current_revision_id,current_revision_ordinal,created_at_ns
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    relationship_id,
                    native_id_to_bytes(membership_identity_namespace_id),
                    MOTIF_MEMBERSHIP_RELATIONSHIP_KIND,
                    transition_id,
                    relationship_revision_id,
                    1,
                    now_ns,
                ),
            )
            tx.execute(
                """
                INSERT INTO relationship_revisions(
                    relationship_revision_id,relationship_id,revision_ordinal,lineage_kind,
                    predecessor_revision_id,predecessor_revision_ordinal,effective_semantic_scope_id,
                    existence_state,lifecycle_state,lifecycle_authoritative,governance_state,
                    authority_category,provenance_id,payload_format,payload_text,created_at_ns
                ) VALUES (?,?,1,'LEGACY_PREDECESSOR_UNKNOWN',NULL,NULL,?,'EXISTS','UNKNOWN',0,
                          'UNKNOWN','NOT_APPLICABLE',NULL,'NONE',NULL,?)
                """,
                (relationship_revision_id, relationship_id, motif_scope_id, now_ns),
            )
            tx.execute(
                """
                INSERT INTO relationship_revision_endpoints(
                    relationship_revision_id,endpoint_ordinal,endpoint_role,
                    endpoint_semantic_scope_id,object_id,binding_mode,
                    bound_object_revision_id,bound_object_revision_ordinal
                ) VALUES (?,0,'MOTIF',?,?,'IDENTITY',NULL,NULL)
                """,
                (relationship_revision_id, motif_scope_id, motif_object_id),
            )
            tx.execute(
                """
                INSERT INTO relationship_revision_endpoints(
                    relationship_revision_id,endpoint_ordinal,endpoint_role,
                    endpoint_semantic_scope_id,object_id,binding_mode,
                    bound_object_revision_id,bound_object_revision_ordinal
                ) VALUES (?,1,'MEMBER',?,?,'IDENTITY',NULL,NULL)
                """,
                (relationship_revision_id, member[1], member[0]),
            )
        tx.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
            (source_namespace_id, LEGACY_MOTIF_ALIAS_KIND, candidate.motif_id, motif_object_id),
        )
        tx.execute(
            """
            INSERT INTO legacy_admission_records(
                admission_record_id,admission_batch_id,legacy_artifact_record_id,
                admission_status,unknown_fields_json
            ) VALUES (?,?,?,'ADMITTED',?)
            """,
            (
                admission_record_id,
                batch_id,
                artifact_record_id,
                canonical_intent_text(
                    {
                        "motif_state_source": "OBSERVED_CURRENT_REGISTRY_ENTRY",
                        "membership_source": "OBSERVED_MEMBERS_EID_LIST",
                        "motif_reconstructability": "NOT_PROVEN",
                        "motif_event_completeness_for_replay": "NOT_PROVEN",
                        "native_representation_created": False,
                        "original_provenance": "UNKNOWN",
                        "authority_category": "NOT_APPLICABLE",
                    }
                ),
            ),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,?)",
            (transition_id, tx.operation_id, "LEGACY_MOTIF_ADMISSION", "LEGACY_ADMISSION", now_ns),
        )
        tx.execute(
            "INSERT INTO object_revision_effects VALUES (?,?,?,1)",
            (transition_id, motif_object_id, motif_revision_id),
        )
        for relationship_id, relationship_revision_id, _member in membership_rows:
            tx.execute(
                "INSERT INTO relationship_revision_effects VALUES (?,?,?,1)",
                (transition_id, relationship_id, relationship_revision_id),
            )
        tx.execute("INSERT INTO legacy_admission_effects VALUES (?,?)", (transition_id, admission_record_id))
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,object_id,
                object_revision_id,object_revision_ordinal
            ) VALUES (?,?,?,'OBJECT',?,?,1)
            """,
            (tx.operation_id, 0, "LEGACY_MOTIF_ADMISSION", motif_object_id, motif_revision_id),
        )
        for output_ordinal, (relationship_id, relationship_revision_id, _member) in enumerate(
            membership_rows, start=1
        ):
            tx.execute(
                """
                INSERT INTO operation_outputs(
                    operation_id,output_ordinal,output_role,output_kind,relationship_id,
                    relationship_revision_id,relationship_revision_ordinal
                ) VALUES (?,?,?,'RELATIONSHIP',?,?,1)
                """,
                (
                    tx.operation_id,
                    output_ordinal,
                    "LEGACY_MOTIF_MEMBERSHIP_ADMISSION",
                    relationship_id,
                    relationship_revision_id,
                ),
            )
        tx.transitions.append(transition_id)
        tx.published.append((motif_object_id, motif_revision_id, 1))
        tx.relationship_published.extend(
            (relationship_id, relationship_revision_id, 1)
            for relationship_id, relationship_revision_id, _member in membership_rows
        )
        tx.legacy_motif_admitted.append(
            (
                motif_object_id,
                motif_revision_id,
                1,
                admission_record_id,
                transition_id,
                snapshot_id,
                artifact_id,
                artifact_record_id,
                candidate.motif_id,
                motif_scope_id,
                tuple(
                    (
                        relationship_id,
                        relationship_revision_id,
                        1,
                        member[0],
                        member[1],
                        str(member[2]),
                    )
                    for relationship_id, relationship_revision_id, member in membership_rows
                ),
            )
        )
        result = self._recorded_result(tx.operation_id, manifest, candidate)
        if result is None:
            raise SubstrateInvariantViolation("legacy motif admission result was not durably published")
        return result

    def _publish_candidate_quarantine(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        candidate: LegacyMotifCandidate,
        batch_id: bytes,
        artifact_record_id: bytes,
        reason: str,
    ) -> LegacyMotifAdmissionResult:
        admission_record_id = _new()
        tx.execute(
            """
            INSERT INTO legacy_admission_records(
                admission_record_id,admission_batch_id,legacy_artifact_record_id,
                admission_status,unknown_fields_json
            ) VALUES (?,?,?,'QUARANTINED',?)
            """,
            (
                admission_record_id,
                batch_id,
                artifact_record_id,
                canonical_intent_text(
                    {
                        "reason": reason,
                        "motif_id": candidate.motif_id,
                        "motif_reconstructability": "NOT_PROVEN",
                    }
                ),
            ),
        )
        tx.execute(
            """
            INSERT INTO legacy_quarantine_records(
                quarantine_record_id,admission_record_id,condition_code,reason_text,
                retained_legacy_artifact_id,reconciliation_case_id
            ) VALUES (?,?,?,?,?,NULL)
            """,
            (
                _new(),
                admission_record_id,
                "UNRESOLVED_LEGACY_MOTIF_MEMBER_ALIAS",
                reason,
                native_id_to_bytes(candidate.legacy_artifact_id),
            ),
        )
        result = self._recorded_result(tx.operation_id, manifest, candidate)
        if result is None:
            raise SubstrateInvariantViolation("quarantined motif admission result was not durable")
        return result

    def _publish_uncertainty(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        record: LegacyMotifAdmissionRecord,
    ) -> LegacyMotifAdmissionResult:
        batch_id = _ensure_admission_batch(
            tx, native_id_to_bytes(manifest.legacy_snapshot_id), _ADMISSION_BATCH_IDENTITY
        )
        artifact_record_id = _ensure_artifact_record(
            tx,
            native_id_to_bytes(record.legacy_artifact_id),
            record.record_identity,
            record.record_locator,
        )
        existing = _admission_record_for_artifact_record(tx, batch_id, artifact_record_id)
        if existing is None:
            admission_record_id = _new()
            tx.execute(
                """
                INSERT INTO legacy_admission_records(
                    admission_record_id,admission_batch_id,legacy_artifact_record_id,
                    admission_status,unknown_fields_json
                ) VALUES (?,?,?,?,?)
                """,
                (
                    admission_record_id,
                    batch_id,
                    artifact_record_id,
                    record.admission_status,
                    canonical_intent_text(
                        {
                            "reason": record.reason,
                            "motif_id": record.motif_id,
                            "motif_reconstructability": "NOT_PROVEN",
                        }
                    ),
                ),
            )
            if record.admission_status == "QUARANTINED":
                tx.execute(
                    """
                    INSERT INTO legacy_quarantine_records(
                        quarantine_record_id,admission_record_id,condition_code,reason_text,
                        retained_legacy_artifact_id,reconciliation_case_id
                    ) VALUES (?,?,?,?,?,NULL)
                    """,
                    (
                        _new(),
                        admission_record_id,
                        "AMBIGUOUS_LEGACY_MOTIF_CURRENT_STATE",
                        record.reason,
                        native_id_to_bytes(record.legacy_artifact_id),
                    ),
                )
        elif existing[1] != record.admission_status:
            raise SubstrateRevisionConflict("legacy motif evidence has a different admission result")
        result = self._recorded_result(tx.operation_id, manifest, record)
        if result is None:
            raise SubstrateInvariantViolation("legacy motif uncertainty result was not durable")
        return result

    def _resolve_members(
        self, tx: SubstrateTx, source_namespace_id: bytes, member_eids: tuple[int, ...]
    ) -> tuple[tuple[tuple[bytes, bytes, int], ...], str | None]:
        resolved: list[tuple[bytes, bytes, int]] = []
        for eid in member_eids:
            rows = tx.execute(
                """
                SELECT a.object_id,r.effective_semantic_scope_id
                FROM legacy_object_aliases a
                JOIN objects o ON o.object_id=a.object_id
                JOIN object_revisions r ON r.object_revision_id=o.current_revision_id
                JOIN semantic_transitions t ON t.transition_id=o.creating_transition_id
                WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID' AND a.alias_value=?
                  AND o.object_kind='LEGACY_CORE_NODE'
                  AND t.transition_kind='LEGACY_OBJECT_ADMISSION' AND t.origin_kind='LEGACY_ADMISSION'
                """,
                (source_namespace_id, str(eid)),
            ).fetchall()
            if len(rows) != 1:
                return (), f"member EID {eid} does not resolve to exactly one imported source object"
            resolved.append((rows[0][0], rows[0][1], eid))
        return tuple(resolved), None

    def _recorded_result(
        self,
        operation_id: bytes,
        manifest: LegacySnapshotManifest,
        item: LegacyMotifCandidate | LegacyMotifAdmissionRecord,
    ) -> LegacyMotifAdmissionResult | None:
        record_identity = item.record_identity
        record = self._connection.execute(
            """
            SELECT a.admission_record_id,a.admission_status
            FROM legacy_admission_records a
            JOIN legacy_admission_batches b USING(admission_batch_id)
            JOIN legacy_artifact_records ar USING(legacy_artifact_record_id)
            WHERE b.legacy_snapshot_id=? AND b.batch_identity=?
              AND ar.legacy_artifact_id=? AND ar.record_identity=?
            """,
            (
                native_id_to_bytes(manifest.legacy_snapshot_id),
                _ADMISSION_BATCH_IDENTITY,
                native_id_to_bytes(item.legacy_artifact_id),
                record_identity,
            ),
        ).fetchone()
        motif_id = item.motif_id
        if record is None:
            return None
        if record[1] != "ADMITTED":
            return LegacyMotifAdmissionResult(
                item.legacy_snapshot_id,
                item.legacy_artifact_id,
                item.observed_relative_locator,
                motif_id,
                record[1],
                native_id_from_bytes(record[0]),
                native_id_from_bytes(operation_id),
            )
        object_row = self._connection.execute(
            """
            SELECT o.object_id,o.object_revision_id,t.transition_id,t.operation_id,a.admission_record_id
            FROM operation_outputs o
            JOIN semantic_transitions t ON t.operation_id=o.operation_id
            JOIN object_revision_effects e ON e.transition_id=t.transition_id
            JOIN legacy_admission_effects le ON le.transition_id=t.transition_id
            JOIN legacy_admission_records a ON a.admission_record_id=le.admission_record_id
            WHERE o.operation_id=? AND o.output_ordinal=0 AND o.output_kind='OBJECT'
              AND o.output_role='LEGACY_MOTIF_ADMISSION'
              AND e.object_id=o.object_id AND e.object_revision_id=o.object_revision_id
              AND e.object_revision_ordinal=o.object_revision_ordinal
              AND a.admission_record_id=? AND a.admission_status='ADMITTED'
            """,
            (operation_id, record[0]),
        ).fetchone()
        if object_row is None:
            return None
        relationship_rows = self._connection.execute(
            """
            SELECT o.relationship_id,o.relationship_revision_id
            FROM operation_outputs o
            JOIN relationship_revision_effects re
              ON re.transition_id=(SELECT transition_id FROM semantic_transitions WHERE operation_id=o.operation_id)
             AND re.relationship_id=o.relationship_id
             AND re.relationship_revision_id=o.relationship_revision_id
             AND re.relationship_revision_ordinal=o.relationship_revision_ordinal
            JOIN relationship_revision_endpoints e
              ON e.relationship_revision_id=o.relationship_revision_id
             AND e.endpoint_ordinal=1 AND e.endpoint_role='MEMBER'
            WHERE o.operation_id=? AND o.output_kind='RELATIONSHIP'
              AND o.output_role='LEGACY_MOTIF_MEMBERSHIP_ADMISSION'
            ORDER BY o.output_ordinal
            """,
            (operation_id,),
        ).fetchall()
        # EIDs are source aliases rather than endpoint columns; retain output order and map
        # it to the candidate's immutable member list.
        if not isinstance(item, LegacyMotifCandidate) or len(relationship_rows) != len(item.member_eids):
            return None
        memberships = tuple(
            LegacyMotifMembershipResult(
                item.member_eids[index], native_id_from_bytes(row[0]), native_id_from_bytes(row[1])
            )
            for index, row in enumerate(relationship_rows)
        )
        return LegacyMotifAdmissionResult(
            item.legacy_snapshot_id,
            item.legacy_artifact_id,
            item.observed_relative_locator,
            motif_id,
            "ADMITTED",
            native_id_from_bytes(object_row[4]),
            native_id_from_bytes(object_row[3]),
            native_id_from_bytes(object_row[0]),
            native_id_from_bytes(object_row[1]),
            native_id_from_bytes(object_row[2]),
            memberships,
        )

    def _require_admission_namespaces(
        self,
        idempotency_namespace_id: UUID,
        motif_identity_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> None:
        checks = (
            ("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id),
            ("identity_namespaces", "identity_namespace_id", motif_identity_namespace_id),
            ("identity_namespaces", "identity_namespace_id", membership_identity_namespace_id),
            ("semantic_scopes", "semantic_scope_id", unknown_semantic_scope_id),
        )
        for table, column, value in checks:
            if self._connection.execute(
                f"SELECT 1 FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)
            ).fetchone() is None:
                raise SubstrateObjectNotFound(f"required {table} identity was not found")


def _extract_motif_evidence(
    snapshot_root: str | Path, manifest: LegacySnapshotManifest
) -> tuple[tuple[LegacyMotifCandidate, ...], tuple[LegacyMotifAdmissionRecord, ...]]:
    root = Path(snapshot_root).expanduser().resolve()
    candidates: list[LegacyMotifCandidate] = []
    records: list[LegacyMotifAdmissionRecord] = []
    for artifact in manifest.artifacts:
        domain_id = _motif_registry_domain(artifact.observed_relative_locator)
        if domain_id is None:
            continue
        if artifact.artifact_class != "LEGACY_MOTIF_STATE_EVIDENCE":
            records.append(
                _registry_record(manifest, artifact, "UNKNOWN", "motif registry artifact class is not current-state evidence")
            )
            continue
        try:
            registry = _load_json_object(root, artifact)
            raw_motifs = registry.get("motifs")
            if not isinstance(raw_motifs, dict):
                raise ValueError("motif registry lacks an object-valued motifs mapping")
        except ValueError as exc:
            records.append(_registry_record(manifest, artifact, "UNKNOWN", str(exc)))
            continue
        for motif_id, raw_motif in raw_motifs.items():
            try:
                candidates.append(_candidate_from_record(manifest, artifact, domain_id, motif_id, raw_motif))
            except ValueError as exc:
                status = "QUARANTINED" if "duplicate member" in str(exc) else "UNKNOWN"
                records.append(
                    LegacyMotifAdmissionRecord(
                        manifest.legacy_snapshot_id,
                        artifact.artifact_id,
                        artifact.observed_relative_locator,
                        _record_identity(artifact.observed_relative_locator, motif_id if isinstance(motif_id, str) else "INVALID"),
                        f"{artifact.observed_relative_locator}#motif:{motif_id!r}",
                        status,
                        str(exc),
                        motif_id if isinstance(motif_id, str) else None,
                    )
                )
    return tuple(candidates), tuple(records)


def _motif_registry_domain(locator: str) -> str | None:
    path = PurePosixPath(locator)
    parts = path.parts
    if (
        len(parts) == 5
        and parts[0] == "workspaces"
        and parts[2] == "domains"
        and path.name == "motifs.json"
        and parts[1]
        and parts[3]
    ):
        return parts[3]
    return None


def _load_json_object(root: Path, artifact: LegacyArtifact) -> dict[str, Any]:
    path = (root / artifact.observed_relative_locator).resolve()
    if root not in path.parents:
        raise ValueError("motif registry locator escapes snapshot root")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("motif registry is not valid UTF-8 JSON evidence") from exc
    if not isinstance(value, dict):
        raise ValueError("motif registry is not a JSON object")
    return value


def _candidate_from_record(
    manifest: LegacySnapshotManifest,
    artifact: LegacyArtifact,
    domain_id: str,
    motif_id: object,
    raw_motif: object,
) -> LegacyMotifCandidate:
    if not _nonempty_text(motif_id) or not isinstance(raw_motif, dict):
        raise ValueError("motif registry entry lacks a stable motif ID or object record")
    if raw_motif.get("motif_id") != motif_id:
        raise ValueError("motif record does not repeat its stable registry motif_id")
    if raw_motif.get("domain_id") != domain_id:
        raise ValueError("motif record domain_id disagrees with its durable registry locator")
    if not isinstance(raw_motif.get("label"), str):
        raise ValueError("motif record lacks text label")
    if not _finite_number(raw_motif.get("strength")) or not _finite_number(raw_motif.get("stability_score")):
        raise ValueError("motif record lacks finite strength or stability_score")
    centroid = raw_motif.get("centroid")
    if not isinstance(centroid, list) or not all(_finite_number(value) for value in centroid):
        raise ValueError("motif centroid is not an exact numeric JSON list")
    if not _text_list(raw_motif.get("contributing_agents")):
        raise ValueError("motif record lacks text contributing_agents list")
    if not _nonnegative_int(raw_motif.get("created_ts")) or not _nonnegative_int(raw_motif.get("last_active_ts")):
        raise ValueError("motif record lacks non-negative durable timestamps")
    members = raw_motif.get("members")
    if not isinstance(members, list) or not all(_nonnegative_int(value) for value in members):
        raise ValueError("motif record lacks a non-negative integer members list")
    if len(set(members)) != len(members):
        raise ValueError("motif record has ambiguous duplicate member references")
    payload = {key: value for key, value in raw_motif.items() if key != "members"}
    return LegacyMotifCandidate(
        manifest.legacy_snapshot_id,
        artifact.artifact_id,
        artifact.observed_relative_locator,
        motif_id,
        domain_id,
        tuple(members),
        payload,
    )


def _registry_record(
    manifest: LegacySnapshotManifest,
    artifact: LegacyArtifact,
    status: str,
    reason: str,
) -> LegacyMotifAdmissionRecord:
    return LegacyMotifAdmissionRecord(
        manifest.legacy_snapshot_id,
        artifact.artifact_id,
        artifact.observed_relative_locator,
        _record_identity(artifact.observed_relative_locator, "REGISTRY"),
        artifact.observed_relative_locator,
        status,
        reason,
    )


def _record_identity(locator: str, motif_id: str) -> str:
    return f"TMS-LEGACY-MOTIF-REGISTRY-1:{locator}:{motif_id}"


def _item_sort_key(item: LegacyMotifCandidate | LegacyMotifAdmissionRecord) -> tuple[str, str]:
    return (item.observed_relative_locator, item.motif_id or "")


def _candidate_intent(candidate: LegacyMotifCandidate) -> str:
    return canonical_intent_text(
        {
            "kind": "ADMIT_LEGACY_MOTIF_CURRENT",
            "legacy_snapshot_id": str(candidate.legacy_snapshot_id),
            "legacy_artifact_id": str(candidate.legacy_artifact_id),
            "record_identity": candidate.record_identity,
            "motif_id": candidate.motif_id,
        }
    )


def _record_intent(record: LegacyMotifAdmissionRecord) -> str:
    return canonical_intent_text(
        {
            "kind": "RECORD_LEGACY_MOTIF_ADMISSION_" + record.admission_status,
            "legacy_snapshot_id": str(record.legacy_snapshot_id),
            "legacy_artifact_id": str(record.legacy_artifact_id),
            "record_identity": record.record_identity,
            "reason": record.reason,
        }
    )


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _text_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)
