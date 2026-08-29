"""Phase 7F2 evidence-linked admission of legacy ``nodes.jsonl`` current state.

This boundary admits only a selected observed current node state.  It never
replays legacy history: append rows are evidence, and an admission transition
records TORMENT's present admission decision rather than historical creation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time
from uuid import UUID

from ..canonical_intent import canonical_intent_text
from ..errors import (
    SubstrateInvariantViolation,
    SubstrateObjectNotFound,
    SubstrateRevisionConflict,
)
from ..ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from ..objects import SubstrateTx, execute_semantic
from ..schema import open_schema
from .inventory import inventory_snapshot
from .snapshot import LegacyArtifact, LegacySnapshotManifest, load_snapshot_manifest


NODES_CURRENT_SELECTION_RULE = "LAST_SUCCESSFULLY_PARSED_RECORD_PER_EID_UNLESS_LATER_MALFORMED_EID"
_ADMISSION_BATCH_IDENTITY = "TMS-LEGACY-OBJECT-ADMISSION-7F2"
_MALFORMED_EID_PREFIX = re.compile(r'^\s*\{\s*"eid"\s*:\s*([0-9]+)(?:\s*[,}]|$)')


@dataclass(frozen=True)
class LegacyNodeCandidate:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    line_ordinal: int
    raw_eid: int
    raw_row_bytes: bytes


@dataclass(frozen=True)
class MalformedLegacyNodeRecord:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    line_ordinal: int
    raw_eid: int | None
    raw_row_bytes: bytes
    reason: str


@dataclass(frozen=True)
class LegacyObjectAdmissionResult:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    line_ordinal: int
    raw_eid: int | None
    admission_status: str
    admission_record_id: UUID
    operation_id: UUID
    object_id: UUID | None = None
    revision_id: UUID | None = None
    transition_id: UUID | None = None


@dataclass(frozen=True)
class LegacyNodeAdmissionRun:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    candidate_selection_rule: str
    results: tuple[LegacyObjectAdmissionResult, ...]


class NativeLegacyObjectAdmissionService:
    """Small typed admission boundary; ``SubstrateTx`` remains the only owner."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection)
        self._connection = connection

    def admit_nodes_current_state(
        self,
        *,
        snapshot_root: str | Path,
        manifest_path: str | Path,
        idempotency_namespace_id: UUID,
        object_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyNodeAdmissionRun:
        """Verify/inventory an explicit snapshot and admit its selected node candidates."""
        self._require_admission_namespaces(
            idempotency_namespace_id, object_identity_namespace_id, unknown_semantic_scope_id
        )
        manifest = load_snapshot_manifest(manifest_path)
        inventory_snapshot(
            self._connection, snapshot_root=snapshot_root, manifest_path=manifest_path
        )
        nodes_artifact = _nodes_artifact(manifest)
        candidates, malformed = _extract_nodes(
            snapshot_root, manifest.legacy_snapshot_id, nodes_artifact
        )
        results = [
            self._admit_candidate(
                manifest,
                candidate,
                idempotency_namespace_id,
                object_identity_namespace_id,
                unknown_semantic_scope_id,
            )
            for candidate in sorted(candidates, key=lambda item: (item.raw_eid, item.line_ordinal))
        ]
        results.extend(
            self._record_malformed_candidate(
                manifest, record, idempotency_namespace_id
            )
            for record in sorted(malformed, key=lambda item: item.line_ordinal)
        )
        return LegacyNodeAdmissionRun(
            legacy_snapshot_id=manifest.legacy_snapshot_id,
            legacy_artifact_id=nodes_artifact.artifact_id,
            candidate_selection_rule=NODES_CURRENT_SELECTION_RULE,
            results=tuple(results),
        )

    def resolve_legacy_object_alias(
        self,
        *,
        legacy_source_namespace_id: UUID,
        alias_kind: str,
        alias_value: str,
    ) -> UUID:
        """Resolve only an explicitly namespaced legacy alias; there is no bare EID lookup."""
        if alias_kind != "EID" or not isinstance(alias_value, str) or not alias_value:
            raise ValueError("legacy object alias lookup requires EID and non-empty alias value")
        row = self._connection.execute(
            """
            SELECT object_id FROM legacy_object_aliases
            WHERE legacy_source_namespace_id=? AND alias_kind=? AND alias_value=?
            """,
            (native_id_to_bytes(legacy_source_namespace_id), alias_kind, alias_value),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("namespaced legacy object alias was not found")
        return native_id_from_bytes(row[0])

    def _admit_candidate(
        self,
        manifest: LegacySnapshotManifest,
        candidate: LegacyNodeCandidate,
        idempotency_namespace_id: UUID,
        object_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyObjectAdmissionResult:
        intent = _admission_intent("ADMIT_LEGACY_NODE_CURRENT", candidate)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "ADMIT_LEGACY_NODE_CURRENT",
            intent,
            lambda operation_id: self._admitted_result(operation_id, candidate),
            lambda tx: self._publish_admitted_candidate(
                tx,
                manifest,
                candidate,
                object_identity_namespace_id,
                unknown_semantic_scope_id,
            ),
        )

    def _record_malformed_candidate(
        self,
        manifest: LegacySnapshotManifest,
        record: MalformedLegacyNodeRecord,
        idempotency_namespace_id: UUID,
    ) -> LegacyObjectAdmissionResult:
        intent = _malformed_intent(record)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "RECORD_LEGACY_NODE_ADMISSION_UNKNOWN",
            intent,
            lambda operation_id: self._unknown_result(operation_id, manifest, record),
            lambda tx: self._publish_unknown_record(tx, manifest, record),
        )

    def _publish_admitted_candidate(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        candidate: LegacyNodeCandidate,
        object_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyObjectAdmissionResult:
        snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
        source_namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
        artifact_id = native_id_to_bytes(candidate.legacy_artifact_id)
        alias_value = str(candidate.raw_eid)
        existing_alias = tx.execute(
            """
            SELECT object_id FROM legacy_object_aliases
            WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND alias_value=?
            """,
            (source_namespace_id, alias_value),
        ).fetchone()
        if existing_alias is not None:
            raise SubstrateRevisionConflict("legacy EID alias is already admitted for this source namespace")
        batch_id = _ensure_admission_batch(tx, snapshot_id)
        artifact_record_id = _ensure_artifact_record(
            tx, artifact_id, _record_identity(candidate.line_ordinal), _record_locator(candidate.line_ordinal)
        )
        existing_record = _admission_record_for_artifact_record(tx, batch_id, artifact_record_id)
        if existing_record is not None:
            raise SubstrateRevisionConflict("legacy node evidence record already has an admission result")

        object_id, revision_id, transition_id, admission_record_id = (
            _new(),
            _new(),
            _new(),
            _new(),
        )
        now_ns = time.time_ns()
        raw_text = candidate.raw_row_bytes.decode("utf-8")
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
                "LEGACY_CORE_NODE",
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
                      'UNKNOWN','NOT_APPLICABLE',NULL,'TEXT',?,?)
            """,
            (revision_id, object_id, native_id_to_bytes(unknown_semantic_scope_id), raw_text, now_ns),
        )
        tx.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,'EID',?,?)",
            (source_namespace_id, alias_value, object_id),
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
                        "candidate_selection_rule": NODES_CURRENT_SELECTION_RULE,
                        "lifecycle_semantics": "UNKNOWN_NON_AUTHORITATIVE",
                        "governance_semantics": "UNKNOWN",
                        "authority_category": "NOT_APPLICABLE",
                        "original_provenance": "UNKNOWN",
                    }
                ),
            ),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,?)",
            (transition_id, tx.operation_id, "LEGACY_OBJECT_ADMISSION", "LEGACY_ADMISSION", now_ns),
        )
        tx.execute(
            "INSERT INTO object_revision_effects VALUES (?,?,?,1)",
            (transition_id, object_id, revision_id),
        )
        tx.execute(
            "INSERT INTO legacy_admission_effects VALUES (?,?)",
            (transition_id, admission_record_id),
        )
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,object_id,
                object_revision_id,object_revision_ordinal
            ) VALUES (?,?,?,'OBJECT',?,?,1)
            """,
            (
                tx.operation_id,
                0,
                "LEGACY_OBJECT_ADMISSION",
                object_id,
                revision_id,
            ),
        )
        tx.transitions.append(transition_id)
        tx.published.append((object_id, revision_id, 1))
        tx.legacy_admitted.append(
            (
                object_id,
                revision_id,
                1,
                admission_record_id,
                transition_id,
                snapshot_id,
                artifact_id,
                artifact_record_id,
                alias_value,
            )
        )
        result = self._admitted_result(tx.operation_id, candidate)
        if result is None:
            raise SubstrateInvariantViolation("legacy object admission result was not durably published")
        return result

    def _publish_unknown_record(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        record: MalformedLegacyNodeRecord,
    ) -> LegacyObjectAdmissionResult:
        batch_id = _ensure_admission_batch(tx, native_id_to_bytes(manifest.legacy_snapshot_id))
        artifact_record_id = _ensure_artifact_record(
            tx,
            native_id_to_bytes(record.legacy_artifact_id),
            _record_identity(record.line_ordinal),
            _record_locator(record.line_ordinal),
        )
        existing = _admission_record_for_artifact_record(tx, batch_id, artifact_record_id)
        if existing is None:
            admission_record_id = _new()
            tx.execute(
                """
                INSERT INTO legacy_admission_records(
                    admission_record_id,admission_batch_id,legacy_artifact_record_id,
                    admission_status,unknown_fields_json
                ) VALUES (?,?,?,'UNKNOWN',?)
                """,
                (
                    admission_record_id,
                    batch_id,
                    artifact_record_id,
                    canonical_intent_text(
                        {
                            "reason": record.reason,
                            "raw_eid": record.raw_eid,
                            "candidate_selection_rule": NODES_CURRENT_SELECTION_RULE,
                        }
                    ),
                ),
            )
        elif existing[1] != "UNKNOWN":
            raise SubstrateRevisionConflict("legacy evidence record has a different admission result")
        result = self._unknown_result(tx.operation_id, manifest, record)
        if result is None:
            raise SubstrateInvariantViolation("legacy unknown admission result was not durably recorded")
        return result

    def _admitted_result(
        self, operation_id: bytes, candidate: LegacyNodeCandidate
    ) -> LegacyObjectAdmissionResult | None:
        row = self._connection.execute(
            """
            SELECT o.object_id,o.object_revision_id,t.transition_id,t.operation_id,
                   a.admission_record_id
            FROM operation_outputs o
            JOIN semantic_transitions t ON t.operation_id=o.operation_id
            JOIN object_revision_effects e ON e.transition_id=t.transition_id
            JOIN legacy_admission_effects le ON le.transition_id=t.transition_id
            JOIN legacy_admission_records a ON a.admission_record_id=le.admission_record_id
            WHERE o.operation_id=? AND o.output_kind='OBJECT'
              AND o.output_role='LEGACY_OBJECT_ADMISSION'
              AND e.object_id=o.object_id AND e.object_revision_id=o.object_revision_id
              AND e.object_revision_ordinal=o.object_revision_ordinal
              AND a.admission_status='ADMITTED'
            """,
            (operation_id,),
        ).fetchone()
        if row is None:
            return None
        return LegacyObjectAdmissionResult(
            legacy_snapshot_id=candidate.legacy_snapshot_id,
            legacy_artifact_id=candidate.legacy_artifact_id,
            line_ordinal=candidate.line_ordinal,
            raw_eid=candidate.raw_eid,
            admission_status="ADMITTED",
            admission_record_id=native_id_from_bytes(row[4]),
            operation_id=native_id_from_bytes(row[3]),
            object_id=native_id_from_bytes(row[0]),
            revision_id=native_id_from_bytes(row[1]),
            transition_id=native_id_from_bytes(row[2]),
        )

    def _unknown_result(
        self,
        operation_id: bytes,
        manifest: LegacySnapshotManifest,
        record: MalformedLegacyNodeRecord,
    ) -> LegacyObjectAdmissionResult | None:
        row = self._connection.execute(
            """
            SELECT a.admission_record_id,a.admission_status
            FROM legacy_admission_records a
            JOIN legacy_admission_batches b USING(admission_batch_id)
            JOIN legacy_artifact_records ar USING(legacy_artifact_record_id)
            WHERE b.legacy_snapshot_id=? AND ar.legacy_artifact_id=?
              AND ar.record_identity=? AND a.admission_status='UNKNOWN'
            """,
            (
                native_id_to_bytes(manifest.legacy_snapshot_id),
                native_id_to_bytes(record.legacy_artifact_id),
                _record_identity(record.line_ordinal),
            ),
        ).fetchone()
        if row is None:
            return None
        return LegacyObjectAdmissionResult(
            legacy_snapshot_id=record.legacy_snapshot_id,
            legacy_artifact_id=record.legacy_artifact_id,
            line_ordinal=record.line_ordinal,
            raw_eid=record.raw_eid,
            admission_status=row[1],
            admission_record_id=native_id_from_bytes(row[0]),
            operation_id=native_id_from_bytes(operation_id),
        )

    def _require_admission_namespaces(
        self,
        idempotency_namespace_id: UUID,
        object_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> None:
        checks = (
            ("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id),
            ("identity_namespaces", "identity_namespace_id", object_identity_namespace_id),
            ("semantic_scopes", "semantic_scope_id", unknown_semantic_scope_id),
        )
        for table, column, value in checks:
            if self._connection.execute(
                f"SELECT 1 FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)
            ).fetchone() is None:
                raise SubstrateObjectNotFound(f"required {table} identity was not found")


def _nodes_artifact(manifest: LegacySnapshotManifest) -> LegacyArtifact:
    candidates = [
        artifact
        for artifact in manifest.artifacts
        if artifact.artifact_class == "LEGACY_CORE_NODE_EVIDENCE"
        and artifact.observed_relative_locator == "nodes.jsonl"
    ]
    if len(candidates) != 1:
        raise SubstrateRevisionConflict("snapshot must contain exactly one nodes.jsonl evidence artifact")
    return candidates[0]


def _extract_nodes(
    snapshot_root: str | Path, snapshot_id: UUID, artifact: LegacyArtifact
) -> tuple[tuple[LegacyNodeCandidate, ...], tuple[MalformedLegacyNodeRecord, ...]]:
    root = Path(snapshot_root).expanduser().resolve()
    path = (root / artifact.observed_relative_locator).resolve()
    if root not in path.parents:
        raise SubstrateInvariantViolation("nodes evidence locator escapes snapshot root")
    current: dict[int, LegacyNodeCandidate] = {}
    malformed: list[MalformedLegacyNodeRecord] = []
    blocked_eids: set[int] = set()
    with path.open("rb") as stream:
        for line_ordinal, raw_row_bytes in enumerate(stream, start=1):
            parsed, malformed_reason = _parse_node_record(raw_row_bytes)
            if parsed is None:
                raw_eid = _conservative_malformed_eid(raw_row_bytes)
                if raw_eid is not None:
                    current.pop(raw_eid, None)
                    blocked_eids.add(raw_eid)
                malformed.append(
                    MalformedLegacyNodeRecord(
                        snapshot_id,
                        artifact.artifact_id,
                        line_ordinal,
                        raw_eid,
                        raw_row_bytes,
                        malformed_reason,
                    )
                )
                continue
            raw_eid = parsed
            blocked_eids.discard(raw_eid)
            current[raw_eid] = LegacyNodeCandidate(
                snapshot_id, artifact.artifact_id, line_ordinal, raw_eid, raw_row_bytes
            )
    for raw_eid in blocked_eids:
        current.pop(raw_eid, None)
    return tuple(current.values()), tuple(malformed)


def _parse_node_record(raw_row_bytes: bytes) -> tuple[int | None, str]:
    try:
        decoded = raw_row_bytes.decode("utf-8")
        value = json.loads(decoded)
    except UnicodeDecodeError:
        return None, "row is not valid UTF-8"
    except json.JSONDecodeError:
        return None, "row is not valid JSON"
    if not isinstance(value, dict):
        return None, "row is not a JSON object"
    raw_eid = value.get("eid")
    if not isinstance(raw_eid, int) or isinstance(raw_eid, bool) or raw_eid < 0:
        return None, "row lacks a non-negative integer EID"
    return raw_eid, ""


def _conservative_malformed_eid(raw_row_bytes: bytes) -> int | None:
    try:
        decoded = raw_row_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None
    match = _MALFORMED_EID_PREFIX.match(decoded)
    return int(match.group(1)) if match else None


def _ensure_admission_batch(tx: SubstrateTx, snapshot_id: bytes) -> bytes:
    row = tx.execute(
        """
        SELECT admission_batch_id FROM legacy_admission_batches
        WHERE legacy_snapshot_id=? AND batch_identity=?
        """,
        (snapshot_id, _ADMISSION_BATCH_IDENTITY),
    ).fetchone()
    if row is not None:
        return row[0]
    batch_id = _new()
    tx.execute(
        "INSERT INTO legacy_admission_batches VALUES (?,?,?, ?,NULL)",
        (batch_id, snapshot_id, _ADMISSION_BATCH_IDENTITY, time.time_ns()),
    )
    return batch_id


def _ensure_artifact_record(
    tx: SubstrateTx, artifact_id: bytes, record_identity: str, observed_locator: str
) -> bytes:
    row = tx.execute(
        """
        SELECT legacy_artifact_record_id FROM legacy_artifact_records
        WHERE legacy_artifact_id=? AND record_identity=?
        """,
        (artifact_id, record_identity),
    ).fetchone()
    if row is not None:
        return row[0]
    record_id = _new()
    tx.execute(
        "INSERT INTO legacy_artifact_records VALUES (?,?,?,?)",
        (record_id, artifact_id, record_identity, observed_locator),
    )
    return record_id


def _admission_record_for_artifact_record(
    tx: SubstrateTx, batch_id: bytes, artifact_record_id: bytes
) -> tuple[bytes, str] | None:
    return tx.execute(
        """
        SELECT admission_record_id,admission_status FROM legacy_admission_records
        WHERE admission_batch_id=? AND legacy_artifact_record_id=?
        """,
        (batch_id, artifact_record_id),
    ).fetchone()


def _record_identity(line_ordinal: int) -> str:
    return f"TMS-LEGACY-NODES-LINE-1:{line_ordinal}"


def _record_locator(line_ordinal: int) -> str:
    return f"nodes.jsonl#line:{line_ordinal}"


def _admission_intent(kind: str, candidate: LegacyNodeCandidate) -> str:
    return canonical_intent_text(
        {
            "kind": kind,
            "legacy_snapshot_id": str(candidate.legacy_snapshot_id),
            "legacy_artifact_id": str(candidate.legacy_artifact_id),
            "record_identity": _record_identity(candidate.line_ordinal),
            "raw_eid": candidate.raw_eid,
        }
    )


def _malformed_intent(record: MalformedLegacyNodeRecord) -> str:
    return canonical_intent_text(
        {
            "kind": "RECORD_LEGACY_NODE_ADMISSION_UNKNOWN",
            "legacy_snapshot_id": str(record.legacy_snapshot_id),
            "legacy_artifact_id": str(record.legacy_artifact_id),
            "record_identity": _record_identity(record.line_ordinal),
            "reason": record.reason,
        }
    )


def _evidence_idempotency_key(intent: str) -> str:
    return "legacy-evidence:" + hashlib.sha256(intent.encode("utf-8")).hexdigest()


def _new() -> bytes:
    return native_id_to_bytes(generate_native_id())
