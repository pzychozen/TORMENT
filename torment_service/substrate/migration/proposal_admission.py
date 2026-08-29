"""Conservative admission of frozen legacy share-proposal effective state.

Only ``workspaces/<workspace>/domains/<domain>/proposals.jsonl`` and its
paired ``proposal_events.jsonl`` are recognized.  Proposal events are read
solely to reproduce the legacy registry's *captured effective status*; they
are never promoted into native semantic history or authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
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


LEGACY_SHARE_PROPOSAL_OBJECT_KIND: Final[str] = "LEGACY_SHARE_PROPOSAL"
LEGACY_PROPOSAL_ALIAS_KIND: Final[str] = "SHARE_PROPOSAL_ID"
LEGACY_PROPOSAL_ADMISSION_BATCH: Final[str] = "TMS-LEGACY-PROPOSAL-ADMISSION-7F3F"
_SUPPORTED_STATUSES: Final[frozenset[str]] = frozenset({"pending", "approved", "rejected"})


@dataclass(frozen=True)
class LegacyProposalEventEvidence:
    artifact_id: UUID
    observed_relative_locator: str
    line_ordinal: int
    proposal_id: str
    status: str
    note: str | None
    note_present: bool
    processed_ts: int | None
    raw_sha256: str


@dataclass(frozen=True)
class LegacyProposalCandidate:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    observed_relative_locator: str
    proposal_id: str
    workspace_id: str
    domain_id: str
    proposal: dict[str, Any]
    proposal_line_ordinals: tuple[int, ...]
    proposal_raw_sha256: tuple[str, ...]
    event_evidence: tuple[LegacyProposalEventEvidence, ...]

    @property
    def record_identity(self) -> str:
        return _proposal_record_identity(self.observed_relative_locator, self.proposal_id)

    @property
    def record_locator(self) -> str:
        return f"{self.observed_relative_locator}#proposal:{self.proposal_id}"

    @property
    def alias_value(self) -> str:
        return _proposal_alias_value(self.workspace_id, self.domain_id, self.proposal_id)


@dataclass(frozen=True)
class LegacyProposalAdmissionRecord:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    observed_relative_locator: str
    record_identity: str
    record_locator: str
    proposal_id: str | None
    admission_status: str
    reason: str


@dataclass(frozen=True)
class LegacyProposalAdmissionResult:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    observed_relative_locator: str
    proposal_id: str | None
    admission_status: str
    admission_record_id: UUID
    operation_id: UUID
    object_id: UUID | None = None
    revision_id: UUID | None = None
    transition_id: UUID | None = None


@dataclass(frozen=True)
class LegacyProposalAdmissionRun:
    legacy_snapshot_id: UUID
    results: tuple[LegacyProposalAdmissionResult, ...]


class NativeLegacyProposalAdmissionService:
    """Admit only unambiguous frozen proposal current state as intent."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection)
        self._connection = connection

    def admit_proposals_effective_state(
        self,
        *,
        snapshot_root: str | Path,
        manifest_path: str | Path,
        idempotency_namespace_id: UUID,
        object_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyProposalAdmissionRun:
        self._require_admission_namespaces(
            idempotency_namespace_id, object_identity_namespace_id, unknown_semantic_scope_id
        )
        manifest = load_snapshot_manifest(manifest_path)
        inventory_snapshot(self._connection, snapshot_root=snapshot_root, manifest_path=manifest_path)
        candidates, records = _extract_proposal_evidence(snapshot_root, manifest)
        results: list[LegacyProposalAdmissionResult] = []
        for item in sorted((*candidates, *records), key=_item_sort_key):
            if isinstance(item, LegacyProposalCandidate):
                results.append(
                    self._admit_candidate(
                        manifest,
                        item,
                        idempotency_namespace_id,
                        object_identity_namespace_id,
                        unknown_semantic_scope_id,
                    )
                )
            else:
                results.append(self._record_nonadmitted(manifest, item, idempotency_namespace_id))
        return LegacyProposalAdmissionRun(manifest.legacy_snapshot_id, tuple(results))

    def resolve_legacy_proposal_alias(
        self,
        *,
        legacy_source_namespace_id: UUID,
        workspace_id: str,
        domain_id: str,
        proposal_id: str,
    ) -> UUID:
        alias_value = _proposal_alias_value(workspace_id, domain_id, proposal_id)
        row = self._connection.execute(
            """
            SELECT object_id FROM legacy_object_aliases
            WHERE legacy_source_namespace_id=? AND alias_kind=? AND alias_value=?
            """,
            (native_id_to_bytes(legacy_source_namespace_id), LEGACY_PROPOSAL_ALIAS_KIND, alias_value),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("namespaced legacy proposal alias was not found")
        return native_id_from_bytes(row[0])

    def _admit_candidate(
        self,
        manifest: LegacySnapshotManifest,
        candidate: LegacyProposalCandidate,
        idempotency_namespace_id: UUID,
        object_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyProposalAdmissionResult:
        intent = _candidate_intent(candidate)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "ADMIT_LEGACY_PROPOSAL_EFFECTIVE_STATE",
            intent,
            lambda operation_id: self._recorded_result(operation_id, manifest, candidate),
            lambda tx: self._publish_candidate(
                tx, manifest, candidate, object_identity_namespace_id, unknown_semantic_scope_id
            ),
        )

    def _record_nonadmitted(
        self,
        manifest: LegacySnapshotManifest,
        record: LegacyProposalAdmissionRecord,
        idempotency_namespace_id: UUID,
    ) -> LegacyProposalAdmissionResult:
        intent = _record_intent(record)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "RECORD_LEGACY_PROPOSAL_ADMISSION_" + record.admission_status,
            intent,
            lambda operation_id: self._recorded_result(operation_id, manifest, record),
            lambda tx: self._publish_nonadmitted(tx, manifest, record),
        )

    def _publish_candidate(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        candidate: LegacyProposalCandidate,
        object_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyProposalAdmissionResult:
        snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
        source_namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
        artifact_id = native_id_to_bytes(candidate.legacy_artifact_id)
        batch_id = _ensure_admission_batch(tx, snapshot_id, LEGACY_PROPOSAL_ADMISSION_BATCH)
        artifact_record_id = _ensure_artifact_record(
            tx, artifact_id, candidate.record_identity, candidate.record_locator
        )
        if _admission_record_for_artifact_record(tx, batch_id, artifact_record_id) is not None:
            raise SubstrateRevisionConflict("legacy proposal evidence already has an admission result")
        if tx.execute(
            """
            SELECT object_id FROM legacy_object_aliases
            WHERE legacy_source_namespace_id=? AND alias_kind=? AND alias_value=?
            """,
            (source_namespace_id, LEGACY_PROPOSAL_ALIAS_KIND, candidate.alias_value),
        ).fetchone() is not None:
            raise SubstrateRevisionConflict("legacy proposal alias is already admitted for this source namespace")

        object_id, revision_id, transition_id, admission_record_id = _new(), _new(), _new(), _new()
        now_ns = time.time_ns()
        payload = _candidate_payload(candidate)
        tx.execute(
            """
            INSERT INTO objects(
                object_id,identity_namespace_id,object_kind,creating_transition_id,
                current_revision_id,current_revision_ordinal,created_at_ns
            ) VALUES (?,?,?,?,?,?,?)
            """,
            (
                object_id,
                native_id_to_bytes(object_identity_namespace_id),
                LEGACY_SHARE_PROPOSAL_OBJECT_KIND,
                transition_id,
                revision_id,
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
                      'UNKNOWN','INTENT_PROPOSAL',NULL,'JSON',?,?)
            """,
            (
                revision_id,
                object_id,
                native_id_to_bytes(unknown_semantic_scope_id),
                canonical_intent_text(payload),
                now_ns,
            ),
        )
        tx.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
            (source_namespace_id, LEGACY_PROPOSAL_ALIAS_KIND, candidate.alias_value, object_id),
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
                        "admitted_effective_status": payload["effective_status"],
                        "authority_category": "INTENT_PROPOSAL",
                        "event_evidence": payload["legacy_event_evidence"],
                        "event_semantic_history": "NOT_IMPORTED",
                        "embedding_disposition": "CAPTURED_CONTENT_ONLY",
                        "original_provenance": "UNKNOWN",
                    }
                ),
            ),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,?)",
            (transition_id, tx.operation_id, "LEGACY_PROPOSAL_ADMISSION", "LEGACY_ADMISSION", now_ns),
        )
        tx.execute("INSERT INTO object_revision_effects VALUES (?,?,?,1)", (transition_id, object_id, revision_id))
        tx.execute("INSERT INTO legacy_admission_effects VALUES (?,?)", (transition_id, admission_record_id))
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,object_id,
                object_revision_id,object_revision_ordinal
            ) VALUES (?,?,?,'OBJECT',?,?,1)
            """,
            (tx.operation_id, 0, "LEGACY_PROPOSAL_ADMISSION", object_id, revision_id),
        )
        tx.transitions.append(transition_id)
        tx.published.append((object_id, revision_id, 1))
        tx.legacy_proposal_admitted.append(
            (
                object_id,
                revision_id,
                1,
                admission_record_id,
                transition_id,
                snapshot_id,
                artifact_id,
                artifact_record_id,
                candidate.alias_value,
                payload["effective_status"],
            )
        )
        result = self._recorded_result(tx.operation_id, manifest, candidate)
        if result is None:
            raise SubstrateInvariantViolation("legacy proposal admission result was not durably published")
        return result

    def _publish_nonadmitted(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        record: LegacyProposalAdmissionRecord,
    ) -> LegacyProposalAdmissionResult:
        batch_id = _ensure_admission_batch(
            tx, native_id_to_bytes(manifest.legacy_snapshot_id), LEGACY_PROPOSAL_ADMISSION_BATCH
        )
        artifact_record_id = _ensure_artifact_record(
            tx,
            native_id_to_bytes(record.legacy_artifact_id),
            record.record_identity,
            record.record_locator,
        )
        existing = _admission_record_for_artifact_record(tx, batch_id, artifact_record_id)
        if existing is None:
            tx.execute(
                """
                INSERT INTO legacy_admission_records(
                    admission_record_id,admission_batch_id,legacy_artifact_record_id,
                    admission_status,unknown_fields_json
                ) VALUES (?,?,?,?,?)
                """,
                (
                    _new(),
                    batch_id,
                    artifact_record_id,
                    record.admission_status,
                    canonical_intent_text(
                        {
                            "proposal_id": record.proposal_id,
                            "reason": record.reason,
                            "original_provenance": "UNKNOWN",
                        }
                    ),
                ),
            )
        elif existing[1] != record.admission_status:
            raise SubstrateRevisionConflict("legacy proposal evidence has a different admission result")
        result = self._recorded_result(tx.operation_id, manifest, record)
        if result is None:
            raise SubstrateInvariantViolation("legacy proposal non-admission result was not durable")
        return result

    def _recorded_result(
        self,
        operation_id: bytes,
        manifest: LegacySnapshotManifest,
        item: LegacyProposalCandidate | LegacyProposalAdmissionRecord,
    ) -> LegacyProposalAdmissionResult | None:
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
                LEGACY_PROPOSAL_ADMISSION_BATCH,
                native_id_to_bytes(item.legacy_artifact_id),
                record_identity,
            ),
        ).fetchone()
        if record is None:
            return None
        proposal_id = item.proposal_id
        if record[1] != "ADMITTED":
            return LegacyProposalAdmissionResult(
                item.legacy_snapshot_id,
                item.legacy_artifact_id,
                item.observed_relative_locator,
                proposal_id,
                record[1],
                native_id_from_bytes(record[0]),
                native_id_from_bytes(operation_id),
            )
        row = self._connection.execute(
            """
            SELECT o.object_id,o.object_revision_id,t.transition_id,t.operation_id,a.admission_record_id
            FROM operation_outputs o
            JOIN semantic_transitions t ON t.operation_id=o.operation_id
            JOIN object_revision_effects e ON e.transition_id=t.transition_id
            JOIN legacy_admission_effects le ON le.transition_id=t.transition_id
            JOIN legacy_admission_records a ON a.admission_record_id=le.admission_record_id
            WHERE o.operation_id=? AND o.output_kind='OBJECT'
              AND o.output_role='LEGACY_PROPOSAL_ADMISSION'
              AND e.object_id=o.object_id AND e.object_revision_id=o.object_revision_id
              AND e.object_revision_ordinal=o.object_revision_ordinal
              AND a.admission_record_id=? AND a.admission_status='ADMITTED'
            """,
            (operation_id, record[0]),
        ).fetchone()
        if row is None:
            return None
        return LegacyProposalAdmissionResult(
            item.legacy_snapshot_id,
            item.legacy_artifact_id,
            item.observed_relative_locator,
            proposal_id,
            "ADMITTED",
            native_id_from_bytes(row[4]),
            native_id_from_bytes(row[3]),
            native_id_from_bytes(row[0]),
            native_id_from_bytes(row[1]),
            native_id_from_bytes(row[2]),
        )

    def _require_admission_namespaces(
        self,
        idempotency_namespace_id: UUID,
        object_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> None:
        for table, column, value in (
            ("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id),
            ("identity_namespaces", "identity_namespace_id", object_identity_namespace_id),
            ("semantic_scopes", "semantic_scope_id", unknown_semantic_scope_id),
        ):
            if self._connection.execute(
                f"SELECT 1 FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)
            ).fetchone() is None:
                raise SubstrateObjectNotFound(f"required {table} identity was not found")


def _extract_proposal_evidence(
    snapshot_root: str | Path, manifest: LegacySnapshotManifest
) -> tuple[tuple[LegacyProposalCandidate, ...], tuple[LegacyProposalAdmissionRecord, ...]]:
    root = Path(snapshot_root).expanduser().resolve()
    proposal_artifacts = {
        _proposal_group(artifact.observed_relative_locator): artifact
        for artifact in manifest.artifacts
        if _proposal_group(artifact.observed_relative_locator) is not None
    }
    event_artifacts = {
        _event_group(artifact.observed_relative_locator): artifact
        for artifact in manifest.artifacts
        if _event_group(artifact.observed_relative_locator) is not None
    }
    candidates: list[LegacyProposalCandidate] = []
    records: list[LegacyProposalAdmissionRecord] = []
    for group, proposals_artifact in sorted(proposal_artifacts.items()):
        assert group is not None
        event_artifact = event_artifacts.pop(group, None)
        group_candidates, group_records = _extract_group(
            root, manifest, group, proposals_artifact, event_artifact
        )
        candidates.extend(group_candidates)
        records.extend(group_records)
    for group, event_artifact in sorted(event_artifacts.items()):
        assert group is not None
        records.extend(_records_for_events_without_proposals(root, manifest, event_artifact))
    return tuple(candidates), tuple(records)


def _extract_group(
    root: Path,
    manifest: LegacySnapshotManifest,
    group: tuple[str, str],
    proposals_artifact: LegacyArtifact,
    event_artifact: LegacyArtifact | None,
) -> tuple[list[LegacyProposalCandidate], list[LegacyProposalAdmissionRecord]]:
    workspace_id, domain_id = group
    records: list[LegacyProposalAdmissionRecord] = []
    valid: dict[str, list[tuple[int, bytes, dict[str, Any]]]] = {}
    invalid_pids: set[str] = set()
    for ordinal, raw in _artifact_lines(root, proposals_artifact):
        parsed, reason = _json_object(raw)
        if parsed is None:
            records.append(_line_record(manifest, proposals_artifact, ordinal, None, "UNKNOWN", reason))
            continue
        proposal_id = parsed.get("proposal_id") if isinstance(parsed.get("proposal_id"), str) and parsed.get("proposal_id") else None
        try:
            _validate_proposal(parsed, workspace_id, domain_id)
        except ValueError as exc:
            if proposal_id is not None:
                invalid_pids.add(proposal_id)
            records.append(_line_record(manifest, proposals_artifact, ordinal, proposal_id, "UNKNOWN", str(exc)))
            continue
        valid.setdefault(parsed["proposal_id"], []).append((ordinal, raw, parsed))

    events_by_pid: dict[str, list[LegacyProposalEventEvidence]] = {}
    invalid_event_pids: set[str] = set()
    if event_artifact is not None:
        for ordinal, raw in _artifact_lines(root, event_artifact):
            parsed, reason = _json_object(raw)
            if parsed is None:
                records.append(_line_record(manifest, event_artifact, ordinal, None, "UNKNOWN", reason))
                continue
            pid = parsed.get("proposal_id") if isinstance(parsed.get("proposal_id"), str) and parsed.get("proposal_id") else None
            try:
                event = _validate_event(parsed, workspace_id, domain_id, event_artifact, ordinal, raw)
            except ValueError as exc:
                records.append(_line_record(manifest, event_artifact, ordinal, pid, "QUARANTINED", str(exc)))
                if pid is not None and pid in valid:
                    invalid_event_pids.add(pid)
                continue
            if event.proposal_id not in valid:
                records.append(_line_record(manifest, event_artifact, ordinal, event.proposal_id, "UNKNOWN", "proposal event references no submitted proposal"))
            else:
                events_by_pid.setdefault(event.proposal_id, []).append(event)

    candidates: list[LegacyProposalCandidate] = []
    for proposal_id, rows in sorted(valid.items()):
        record_identity = _proposal_record_identity(proposals_artifact.observed_relative_locator, proposal_id)
        record_locator = f"{proposals_artifact.observed_relative_locator}#proposal:{proposal_id}"
        unique_payloads = {canonical_intent_text(row[2]) for row in rows}
        if proposal_id in invalid_pids:
            records.append(_aggregate_record(manifest, proposals_artifact, record_identity, record_locator, proposal_id, "QUARANTINED", "proposal ID also occurs in a malformed submission row"))
            continue
        if len(unique_payloads) != 1:
            records.append(_aggregate_record(manifest, proposals_artifact, record_identity, record_locator, proposal_id, "QUARANTINED", "conflicting duplicate proposal submissions have no frozen current-record rule"))
            continue
        if proposal_id in invalid_event_pids:
            records.append(_aggregate_record(manifest, proposals_artifact, record_identity, record_locator, proposal_id, "QUARANTINED", "a captured proposal event for this proposal is malformed or unsupported"))
            continue
        first = rows[0][2]
        effective = dict(first)
        evidence = tuple(events_by_pid.get(proposal_id, ()))
        for event in evidence:
            effective["status"] = event.status
            if event.note_present:
                effective["note"] = event.note
            if event.processed_ts is not None:
                effective["processed_ts"] = event.processed_ts
        candidates.append(
            LegacyProposalCandidate(
                manifest.legacy_snapshot_id,
                proposals_artifact.artifact_id,
                proposals_artifact.observed_relative_locator,
                proposal_id,
                workspace_id,
                domain_id,
                effective,
                tuple(row[0] for row in rows),
                tuple(_sha256(row[1]) for row in rows),
                evidence,
            )
        )
    return candidates, records


def _records_for_events_without_proposals(
    root: Path, manifest: LegacySnapshotManifest, event_artifact: LegacyArtifact
) -> list[LegacyProposalAdmissionRecord]:
    records: list[LegacyProposalAdmissionRecord] = []
    for ordinal, raw in _artifact_lines(root, event_artifact):
        parsed, reason = _json_object(raw)
        pid = parsed.get("proposal_id") if parsed and isinstance(parsed.get("proposal_id"), str) and parsed.get("proposal_id") else None
        reason = reason if parsed is None else "proposal event has no paired proposals.jsonl source"
        records.append(_line_record(manifest, event_artifact, ordinal, pid, "UNKNOWN", reason))
    return records


def _validate_proposal(value: dict[str, Any], workspace_id: str, domain_id: str) -> None:
    required_text = ("proposal_id", "workspace_id", "domain_id", "agent_id", "summary", "mtype")
    if any(not _nonempty_text(value.get(key)) for key in required_text):
        raise ValueError("proposal lacks required non-empty text fields")
    if value["workspace_id"] != workspace_id or value["domain_id"] != domain_id:
        raise ValueError("proposal declaration disagrees with its durable workspace/domain locator")
    if not isinstance(value.get("embedding"), list) or not all(_finite_number(item) for item in value["embedding"]):
        raise ValueError("proposal embedding is not a finite numeric list")
    if not _finite_number(value.get("confidence")) or not _finite_number(value.get("strength")):
        raise ValueError("proposal confidence or strength is not finite")
    if not _nonnegative_int(value.get("created_ts")):
        raise ValueError("proposal created_ts is not a non-negative integer")
    if value.get("status") not in _SUPPORTED_STATUSES:
        raise ValueError("proposal initial status is missing or unsupported")
    if value.get("half_life_days") is not None and not _finite_number(value.get("half_life_days")):
        raise ValueError("proposal half_life_days is not finite or null")
    if value.get("processed_ts") is not None and not _nonnegative_int(value.get("processed_ts")):
        raise ValueError("proposal processed_ts is not a non-negative integer or null")
    if value.get("note") is not None and not isinstance(value.get("note"), str):
        raise ValueError("proposal note is not text or null")
    try:
        canonical_intent_text(value)
    except Exception as exc:
        raise ValueError("proposal contains non-canonicalizable captured content") from exc


def _validate_event(
    value: dict[str, Any],
    workspace_id: str,
    domain_id: str,
    artifact: LegacyArtifact,
    line_ordinal: int,
    raw: bytes,
) -> LegacyProposalEventEvidence:
    proposal_id, status = value.get("proposal_id"), value.get("status")
    if not _nonempty_text(proposal_id):
        raise ValueError("proposal event lacks a non-empty proposal_id")
    if status not in _SUPPORTED_STATUSES:
        raise ValueError("proposal event status is missing or unsupported")
    if value.get("workspace_id") != workspace_id or value.get("domain_id") != domain_id:
        raise ValueError("proposal event declaration disagrees with its durable workspace/domain locator")
    note = value.get("note")
    if note is not None and not isinstance(note, str):
        raise ValueError("proposal event note is not text or null")
    processed_ts = value.get("ts")
    if not _nonnegative_int(processed_ts):
        raise ValueError("proposal event ts is not a non-negative integer")
    return LegacyProposalEventEvidence(
        artifact.artifact_id, artifact.observed_relative_locator, line_ordinal, proposal_id, status, note, "note" in value, processed_ts, _sha256(raw)
    )


def _candidate_payload(candidate: LegacyProposalCandidate) -> dict[str, Any]:
    return {
        "effective_status": candidate.proposal["status"],
        "legacy_event_evidence": [
            {
                "artifact_id": str(event.artifact_id),
                "line_ordinal": event.line_ordinal,
                "observed_relative_locator": event.observed_relative_locator,
                "raw_sha256": event.raw_sha256,
                "status": event.status,
            }
            for event in candidate.event_evidence
        ],
        "legacy_proposal": candidate.proposal,
        "source": {
            "domain_id": candidate.domain_id,
            "proposal_id": candidate.proposal_id,
            "workspace_id": candidate.workspace_id,
        },
    }


def _artifact_lines(root: Path, artifact: LegacyArtifact) -> list[tuple[int, bytes]]:
    path = (root / artifact.observed_relative_locator).resolve()
    if root not in path.parents:
        raise SubstrateInvariantViolation("proposal evidence locator escapes snapshot root")
    try:
        return [(ordinal, raw) for ordinal, raw in enumerate(path.read_bytes().splitlines(keepends=True), start=1) if raw.strip()]
    except OSError as exc:
        raise SubstrateInvariantViolation("proposal evidence cannot be read after snapshot verification") from exc


def _json_object(raw: bytes) -> tuple[dict[str, Any] | None, str]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "proposal evidence row is not valid UTF-8 JSON"
    if not isinstance(value, dict):
        return None, "proposal evidence row is not a JSON object"
    return value, ""


def _proposal_group(locator: str) -> tuple[str, str] | None:
    path = PurePosixPath(locator)
    parts = path.parts
    if len(parts) == 5 and parts[0] == "workspaces" and parts[2] == "domains" and path.name == "proposals.jsonl" and parts[1] and parts[3]:
        return parts[1], parts[3]
    return None


def _event_group(locator: str) -> tuple[str, str] | None:
    path = PurePosixPath(locator)
    parts = path.parts
    if len(parts) == 5 and parts[0] == "workspaces" and parts[2] == "domains" and path.name == "proposal_events.jsonl" and parts[1] and parts[3]:
        return parts[1], parts[3]
    return None


def _line_record(
    manifest: LegacySnapshotManifest,
    artifact: LegacyArtifact,
    line_ordinal: int,
    proposal_id: str | None,
    admission_status: str,
    reason: str,
) -> LegacyProposalAdmissionRecord:
    return _aggregate_record(
        manifest,
        artifact,
        f"TMS-LEGACY-PROPOSAL-LINE-1:{artifact.observed_relative_locator}:{line_ordinal}",
        f"{artifact.observed_relative_locator}#line:{line_ordinal}",
        proposal_id,
        admission_status,
        reason,
    )


def _aggregate_record(
    manifest: LegacySnapshotManifest,
    artifact: LegacyArtifact,
    record_identity: str,
    record_locator: str,
    proposal_id: str | None,
    admission_status: str,
    reason: str,
) -> LegacyProposalAdmissionRecord:
    return LegacyProposalAdmissionRecord(
        manifest.legacy_snapshot_id,
        artifact.artifact_id,
        artifact.observed_relative_locator,
        record_identity,
        record_locator,
        proposal_id,
        admission_status,
        reason,
    )


def _proposal_record_identity(locator: str, proposal_id: str) -> str:
    return f"TMS-LEGACY-PROPOSAL-STATE-1:{locator}:proposal:{proposal_id}"


def _proposal_alias_value(workspace_id: str, domain_id: str, proposal_id: str) -> str:
    if not all(_nonempty_text(value) for value in (workspace_id, domain_id, proposal_id)):
        raise ValueError("legacy proposal alias requires non-empty workspace, domain, and proposal IDs")
    return canonical_intent_text(
        {"domain_id": domain_id, "proposal_id": proposal_id, "workspace_id": workspace_id}
    )


def _candidate_intent(candidate: LegacyProposalCandidate) -> str:
    return canonical_intent_text(
        {
            "kind": "ADMIT_LEGACY_PROPOSAL_EFFECTIVE_STATE",
            "legacy_snapshot_id": str(candidate.legacy_snapshot_id),
            "legacy_artifact_id": str(candidate.legacy_artifact_id),
            "record_identity": candidate.record_identity,
            "proposal_raw_sha256": list(candidate.proposal_raw_sha256),
            "event_evidence": [
                {
                    "artifact_id": str(event.artifact_id),
                    "line_ordinal": event.line_ordinal,
                    "raw_sha256": event.raw_sha256,
                }
                for event in candidate.event_evidence
            ],
        }
    )


def _record_intent(record: LegacyProposalAdmissionRecord) -> str:
    return canonical_intent_text(
        {
            "kind": "RECORD_LEGACY_PROPOSAL_ADMISSION_" + record.admission_status,
            "legacy_snapshot_id": str(record.legacy_snapshot_id),
            "legacy_artifact_id": str(record.legacy_artifact_id),
            "record_identity": record.record_identity,
            "reason": record.reason,
        }
    )


def _item_sort_key(item: LegacyProposalCandidate | LegacyProposalAdmissionRecord) -> tuple[str, str, int]:
    if isinstance(item, LegacyProposalCandidate):
        return item.observed_relative_locator, item.record_locator, 0
    return item.observed_relative_locator, item.record_locator, 1


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
