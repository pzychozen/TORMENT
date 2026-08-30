"""Evidence-linked admission of legacy node and relationship candidates.

This boundary admits only a selected observed current node state.  It never
replays legacy history: append rows are evidence, and an admission transition
records TORMENT's present admission decision rather than historical creation.

Phase 7F3A adds an intentionally conservative ``edges.jsonl`` boundary.  It
admits only a single, successfully parsed row for a stable source edge ID and
the explicitly recognized ``LEGACY_EDGE`` kind.  It never interprets append
order as relationship revision history.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time
from typing import Any
from uuid import UUID

from ..canonical_intent import canonical_intent_text
from ..errors import (
    SubstrateInvariantViolation,
    SubstrateObjectNotFound,
    SubstrateRevisionConflict,
)
from ..ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from ..memory_runtime_order import publish_runtime_order
from ..objects import SubstrateTx, execute_semantic
from ..schema import open_schema
from .inventory import inventory_snapshot
from .snapshot import LegacyArtifact, LegacySnapshotManifest, load_snapshot_manifest


NODES_CURRENT_SELECTION_RULE = "LAST_SUCCESSFULLY_PARSED_RECORD_PER_EID_UNLESS_LATER_MALFORMED_EID"
_ADMISSION_BATCH_IDENTITY = "TMS-LEGACY-OBJECT-ADMISSION-7F2"
_MALFORMED_EID_PREFIX = re.compile(r'^\s*\{\s*"eid"\s*:\s*([0-9]+)(?:\s*[,}]|$)')
EDGES_CANDIDATE_SELECTION_RULE = "SINGLE_SUCCESSFULLY_PARSED_RECORD_PER_STABLE_EDGE_ID"
_RELATIONSHIP_ADMISSION_BATCH_IDENTITY = "TMS-LEGACY-RELATIONSHIP-ADMISSION-7F3A"
_MALFORMED_EDGE_ID_PREFIX = re.compile(r'^\s*\{\s*"edge_id"\s*:\s*("(?:[^"\\\\]|\\\\.)*"|[0-9]+)(?:\s*[,}]|$)')
_ADMISSIBLE_LEGACY_RELATIONSHIP_KIND = "LEGACY_EDGE"


@dataclass(frozen=True)
class LegacyNodeCandidate:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    line_ordinal: int
    raw_eid: int
    raw_row_bytes: bytes
    runtime_order_ordinal: int = 0


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
        publish_runtime_order(
            tx,
            legacy_source_namespace_id=manifest.legacy_source_namespace_id,
            object_id=native_id_from_bytes(object_id),
            runtime_ordinal=candidate.runtime_order_ordinal,
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
    # Python dict assignment retains an existing key's original position while
    # a removed-and-later-reintroduced EID receives a new first-surviving
    # position.  That matches MemoryGraph's observed current enumeration.
    candidates = tuple(
        LegacyNodeCandidate(
            item.legacy_snapshot_id,
            item.legacy_artifact_id,
            item.line_ordinal,
            item.raw_eid,
            item.raw_row_bytes,
            runtime_order_ordinal,
        )
        for runtime_order_ordinal, item in enumerate(current.values())
    )
    return candidates, tuple(malformed)


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


def _ensure_admission_batch(
    tx: SubstrateTx, snapshot_id: bytes, batch_identity: str = _ADMISSION_BATCH_IDENTITY
) -> bytes:
    row = tx.execute(
        """
        SELECT admission_batch_id FROM legacy_admission_batches
        WHERE legacy_snapshot_id=? AND batch_identity=?
        """,
        (snapshot_id, batch_identity),
    ).fetchone()
    if row is not None:
        return row[0]
    batch_id = _new()
    tx.execute(
        "INSERT INTO legacy_admission_batches VALUES (?,?,?, ?,NULL)",
        (batch_id, snapshot_id, batch_identity, time.time_ns()),
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
            "runtime_order_ordinal": candidate.runtime_order_ordinal,
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


@dataclass(frozen=True)
class LegacyRelationshipEndpointCandidate:
    ordinal: int
    role: str
    raw_eid: int


@dataclass(frozen=True)
class LegacyEdgeCandidate:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    line_ordinal: int
    raw_edge_id: str
    endpoints: tuple[LegacyRelationshipEndpointCandidate, ...]
    legacy_attributes: dict[str, Any]


@dataclass(frozen=True)
class LegacyEdgeAdmissionRecord:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    line_ordinal: int
    raw_edge_id: str | None
    admission_status: str
    reason: str


@dataclass(frozen=True)
class LegacyRelationshipAdmissionResult:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    line_ordinal: int
    raw_edge_id: str | None
    admission_status: str
    admission_record_id: UUID
    operation_id: UUID
    relationship_id: UUID | None = None
    revision_id: UUID | None = None
    transition_id: UUID | None = None


@dataclass(frozen=True)
class LegacyEdgeAdmissionRun:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    candidate_selection_rule: str
    results: tuple[LegacyRelationshipAdmissionResult, ...]


class NativeLegacyRelationshipAdmissionService:
    """Conservative ``edges.jsonl`` admission; ``SubstrateTx`` owns every operation."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection)
        self._connection = connection

    def admit_edges_current_state(
        self,
        *,
        snapshot_root: str | Path,
        manifest_path: str | Path,
        idempotency_namespace_id: UUID,
        relationship_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyEdgeAdmissionRun:
        """Admit only unambiguous, explicitly classed current edge evidence.

        A source edge ID must occur in exactly one successfully parsed record.
        This rule deliberately declines append-order selection, so a legacy edge
        ledger can never be mistaken for native relationship revision history.
        """
        self._require_admission_namespaces(
            idempotency_namespace_id,
            relationship_identity_namespace_id,
            unknown_semantic_scope_id,
        )
        manifest = load_snapshot_manifest(manifest_path)
        inventory_snapshot(
            self._connection, snapshot_root=snapshot_root, manifest_path=manifest_path
        )
        edges_artifact = _edges_artifact(manifest)
        candidates, records = _extract_edges(
            snapshot_root, manifest.legacy_snapshot_id, edges_artifact
        )
        results: list[LegacyRelationshipAdmissionResult] = []
        for item in sorted((*candidates, *records), key=lambda value: value.line_ordinal):
            if isinstance(item, LegacyEdgeCandidate):
                results.append(
                    self._admit_candidate(
                        manifest,
                        item,
                        idempotency_namespace_id,
                        relationship_identity_namespace_id,
                        unknown_semantic_scope_id,
                    )
                )
            else:
                results.append(
                    self._record_nonadmitted_edge(manifest, item, idempotency_namespace_id)
                )
        return LegacyEdgeAdmissionRun(
            legacy_snapshot_id=manifest.legacy_snapshot_id,
            legacy_artifact_id=edges_artifact.artifact_id,
            candidate_selection_rule=EDGES_CANDIDATE_SELECTION_RULE,
            results=tuple(results),
        )

    def resolve_legacy_relationship_alias(
        self,
        *,
        legacy_source_namespace_id: UUID,
        alias_kind: str,
        alias_value: str,
    ) -> UUID:
        """Resolve only one explicitly namespaced, stable source edge alias."""
        if alias_kind != "EDGE_ID" or not isinstance(alias_value, str) or not alias_value:
            raise ValueError("legacy relationship alias lookup requires EDGE_ID and non-empty value")
        row = self._connection.execute(
            """
            SELECT relationship_id FROM legacy_relationship_aliases
            WHERE legacy_source_namespace_id=? AND alias_kind=? AND alias_value=?
            """,
            (native_id_to_bytes(legacy_source_namespace_id), alias_kind, alias_value),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("namespaced legacy relationship alias was not found")
        return native_id_from_bytes(row[0])

    def _admit_candidate(
        self,
        manifest: LegacySnapshotManifest,
        candidate: LegacyEdgeCandidate,
        idempotency_namespace_id: UUID,
        relationship_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyRelationshipAdmissionResult:
        intent = _relationship_admission_intent("ADMIT_LEGACY_RELATIONSHIP_CURRENT", candidate)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "ADMIT_LEGACY_RELATIONSHIP_CURRENT",
            intent,
            lambda operation_id: self._recorded_result(operation_id, manifest, candidate),
            lambda tx: self._publish_candidate(
                tx,
                manifest,
                candidate,
                relationship_identity_namespace_id,
                unknown_semantic_scope_id,
            ),
        )

    def _record_nonadmitted_edge(
        self,
        manifest: LegacySnapshotManifest,
        record: LegacyEdgeAdmissionRecord,
        idempotency_namespace_id: UUID,
    ) -> LegacyRelationshipAdmissionResult:
        intent = _relationship_record_intent(record)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "RECORD_LEGACY_RELATIONSHIP_ADMISSION_" + record.admission_status,
            intent,
            lambda operation_id: self._recorded_result(operation_id, manifest, record),
            lambda tx: self._publish_nonadmitted_record(tx, manifest, record),
        )

    def _publish_candidate(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        candidate: LegacyEdgeCandidate,
        relationship_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyRelationshipAdmissionResult:
        snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
        source_namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
        artifact_id = native_id_to_bytes(candidate.legacy_artifact_id)
        batch_id = _ensure_admission_batch(
            tx, snapshot_id, _RELATIONSHIP_ADMISSION_BATCH_IDENTITY
        )
        artifact_record_id = _ensure_artifact_record(
            tx,
            artifact_id,
            _edge_record_identity(candidate.line_ordinal),
            _edge_record_locator(candidate.line_ordinal),
        )
        if _admission_record_for_artifact_record(tx, batch_id, artifact_record_id) is not None:
            raise SubstrateRevisionConflict("legacy edge evidence record already has an admission result")
        resolved, unresolved_reason = self._resolve_endpoints(
            tx, source_namespace_id, candidate
        )
        if unresolved_reason is not None:
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
                            "reason": unresolved_reason,
                            "candidate_selection_rule": EDGES_CANDIDATE_SELECTION_RULE,
                            "raw_edge_id": candidate.raw_edge_id,
                        }
                    ),
                ),
            )
            tx.execute(
                """
                INSERT INTO legacy_quarantine_records(
                    quarantine_record_id,admission_record_id,condition_code,reason_text,
                    retained_legacy_artifact_id,reconciliation_case_id
                ) VALUES (?,?,?, ?,?,NULL)
                """,
                (
                    _new(),
                    admission_record_id,
                    "UNRESOLVED_LEGACY_ENDPOINT_ALIAS",
                    unresolved_reason,
                    artifact_id,
                ),
            )
            result = self._recorded_result(tx.operation_id, manifest, candidate)
            if result is None:
                raise SubstrateInvariantViolation("quarantined relationship admission result was not durable")
            return result

        existing_alias = tx.execute(
            """
            SELECT relationship_id FROM legacy_relationship_aliases
            WHERE legacy_source_namespace_id=? AND alias_kind='EDGE_ID' AND alias_value=?
            """,
            (source_namespace_id, candidate.raw_edge_id),
        ).fetchone()
        if existing_alias is not None:
            raise SubstrateRevisionConflict("legacy edge alias is already admitted for this source namespace")

        relationship_id, revision_id, transition_id, admission_record_id = (
            _new(),
            _new(),
            _new(),
            _new(),
        )
        now_ns = time.time_ns()
        payload = (
            canonical_intent_text({"legacy_attributes": candidate.legacy_attributes})
            if candidate.legacy_attributes
            else None
        )
        payload_format = "JSON" if payload is not None else "NONE"
        tx.execute(
            """
            INSERT INTO relationships(
                relationship_id,identity_namespace_id,relationship_kind,creating_transition_id,
                current_revision_id,current_revision_ordinal,created_at_ns
            ) VALUES (?,?,?,?,?,?,?)
            """,
            (
                relationship_id,
                native_id_to_bytes(relationship_identity_namespace_id),
                _ADMISSIBLE_LEGACY_RELATIONSHIP_KIND,
                transition_id,
                revision_id,
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
                      'UNKNOWN','NOT_APPLICABLE',NULL,?,?,?)
            """,
            (
                revision_id,
                relationship_id,
                native_id_to_bytes(unknown_semantic_scope_id),
                payload_format,
                payload,
                now_ns,
            ),
        )
        for endpoint_ordinal, endpoint_role, _alias_value, object_id, scope_id in resolved:
            tx.execute(
                """
                INSERT INTO relationship_revision_endpoints(
                    relationship_revision_id,endpoint_ordinal,endpoint_role,
                    endpoint_semantic_scope_id,object_id,binding_mode,
                    bound_object_revision_id,bound_object_revision_ordinal
                ) VALUES (?,?,?,?,?,'IDENTITY',NULL,NULL)
                """,
                (revision_id, endpoint_ordinal, endpoint_role, scope_id, object_id),
            )
        tx.execute(
            "INSERT INTO legacy_relationship_aliases VALUES (?,'EDGE_ID',?,?)",
            (source_namespace_id, candidate.raw_edge_id, relationship_id),
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
                        "candidate_selection_rule": EDGES_CANDIDATE_SELECTION_RULE,
                        "relationship_kind_interpretation": _ADMISSIBLE_LEGACY_RELATIONSHIP_KIND,
                        "lifecycle_semantics": "UNKNOWN_NON_AUTHORITATIVE",
                        "governance_semantics": "UNKNOWN",
                        "authority_category": "NOT_APPLICABLE",
                    }
                ),
            ),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,?)",
            (transition_id, tx.operation_id, "LEGACY_RELATIONSHIP_ADMISSION", "LEGACY_ADMISSION", now_ns),
        )
        tx.execute(
            "INSERT INTO relationship_revision_effects VALUES (?,?,?,1)",
            (transition_id, relationship_id, revision_id),
        )
        tx.execute(
            "INSERT INTO legacy_admission_effects VALUES (?,?)",
            (transition_id, admission_record_id),
        )
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,relationship_id,
                relationship_revision_id,relationship_revision_ordinal
            ) VALUES (?,?,?,'RELATIONSHIP',?,?,1)
            """,
            (
                tx.operation_id,
                0,
                "LEGACY_RELATIONSHIP_ADMISSION",
                relationship_id,
                revision_id,
            ),
        )
        tx.transitions.append(transition_id)
        tx.relationship_published.append((relationship_id, revision_id, 1))
        tx.legacy_relationship_admitted.append(
            (
                relationship_id,
                revision_id,
                1,
                admission_record_id,
                transition_id,
                snapshot_id,
                artifact_id,
                artifact_record_id,
                "EDGE_ID",
                candidate.raw_edge_id,
                tuple(resolved),
            )
        )
        result = self._recorded_result(tx.operation_id, manifest, candidate)
        if result is None:
            raise SubstrateInvariantViolation("legacy relationship admission result was not durably published")
        return result

    def _publish_nonadmitted_record(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        record: LegacyEdgeAdmissionRecord,
    ) -> LegacyRelationshipAdmissionResult:
        batch_id = _ensure_admission_batch(
            tx,
            native_id_to_bytes(manifest.legacy_snapshot_id),
            _RELATIONSHIP_ADMISSION_BATCH_IDENTITY,
        )
        artifact_record_id = _ensure_artifact_record(
            tx,
            native_id_to_bytes(record.legacy_artifact_id),
            _edge_record_identity(record.line_ordinal),
            _edge_record_locator(record.line_ordinal),
        )
        existing = _admission_record_for_artifact_record(tx, batch_id, artifact_record_id)
        if existing is None:
            tx.execute(
                """
                INSERT INTO legacy_admission_records(
                    admission_record_id,admission_batch_id,legacy_artifact_record_id,
                    admission_status,unknown_fields_json
                ) VALUES (?,?,?, ?,?)
                """,
                (
                    _new(),
                    batch_id,
                    artifact_record_id,
                    record.admission_status,
                    canonical_intent_text(
                        {
                            "reason": record.reason,
                            "raw_edge_id": record.raw_edge_id,
                            "candidate_selection_rule": EDGES_CANDIDATE_SELECTION_RULE,
                        }
                    ),
                ),
            )
        elif existing[1] != record.admission_status:
            raise SubstrateRevisionConflict("legacy edge evidence record has a different admission result")
        result = self._recorded_result(tx.operation_id, manifest, record)
        if result is None:
            raise SubstrateInvariantViolation("legacy relationship uncertainty result was not durable")
        return result

    def _resolve_endpoints(
        self,
        tx: SubstrateTx,
        source_namespace_id: bytes,
        candidate: LegacyEdgeCandidate,
    ) -> tuple[tuple[tuple[int, str, str, bytes, bytes], ...], str | None]:
        resolved: list[tuple[int, str, str, bytes, bytes]] = []
        for endpoint in candidate.endpoints:
            alias_value = str(endpoint.raw_eid)
            rows = tx.execute(
                """
                SELECT a.object_id,r.effective_semantic_scope_id
                FROM legacy_object_aliases a
                JOIN objects o ON o.object_id=a.object_id
                JOIN object_revisions r ON r.object_id=o.object_id
                    AND r.object_revision_id=o.current_revision_id
                    AND r.revision_ordinal=o.current_revision_ordinal
                WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID'
                    AND a.alias_value=?
                """,
                (source_namespace_id, alias_value),
            ).fetchall()
            if len(rows) != 1:
                return (), (
                    f"endpoint ordinal {endpoint.ordinal} EID {alias_value} does not resolve "
                    "unambiguously inside the declared legacy source namespace"
                )
            resolved.append((endpoint.ordinal, endpoint.role, alias_value, rows[0][0], rows[0][1]))
        return tuple(resolved), None

    def _recorded_result(
        self,
        operation_id: bytes,
        manifest: LegacySnapshotManifest,
        item: LegacyEdgeCandidate | LegacyEdgeAdmissionRecord,
    ) -> LegacyRelationshipAdmissionResult | None:
        record = self._connection.execute(
            """
            SELECT a.admission_record_id,a.admission_status
            FROM legacy_admission_records a
            JOIN legacy_admission_batches b USING(admission_batch_id)
            JOIN legacy_artifact_records ar USING(legacy_artifact_record_id)
            WHERE b.legacy_snapshot_id=? AND ar.legacy_artifact_id=? AND ar.record_identity=?
            """,
            (
                native_id_to_bytes(manifest.legacy_snapshot_id),
                native_id_to_bytes(item.legacy_artifact_id),
                _edge_record_identity(item.line_ordinal),
            ),
        ).fetchone()
        if record is None:
            return None
        if record[1] != "ADMITTED":
            return LegacyRelationshipAdmissionResult(
                legacy_snapshot_id=item.legacy_snapshot_id,
                legacy_artifact_id=item.legacy_artifact_id,
                line_ordinal=item.line_ordinal,
                raw_edge_id=item.raw_edge_id,
                admission_status=record[1],
                admission_record_id=native_id_from_bytes(record[0]),
                operation_id=native_id_from_bytes(operation_id),
            )
        row = self._connection.execute(
            """
            SELECT o.relationship_id,o.relationship_revision_id,t.transition_id,t.operation_id,
                   a.admission_record_id
            FROM operation_outputs o
            JOIN semantic_transitions t ON t.operation_id=o.operation_id
            JOIN relationship_revision_effects e ON e.transition_id=t.transition_id
            JOIN legacy_admission_effects le ON le.transition_id=t.transition_id
            JOIN legacy_admission_records a ON a.admission_record_id=le.admission_record_id
            WHERE o.operation_id=? AND o.output_kind='RELATIONSHIP'
              AND o.output_role='LEGACY_RELATIONSHIP_ADMISSION'
              AND e.relationship_id=o.relationship_id
              AND e.relationship_revision_id=o.relationship_revision_id
              AND e.relationship_revision_ordinal=o.relationship_revision_ordinal
              AND a.admission_record_id=? AND a.admission_status='ADMITTED'
            """,
            (operation_id, record[0]),
        ).fetchone()
        if row is None:
            return None
        return LegacyRelationshipAdmissionResult(
            legacy_snapshot_id=item.legacy_snapshot_id,
            legacy_artifact_id=item.legacy_artifact_id,
            line_ordinal=item.line_ordinal,
            raw_edge_id=item.raw_edge_id,
            admission_status="ADMITTED",
            admission_record_id=native_id_from_bytes(row[4]),
            operation_id=native_id_from_bytes(row[3]),
            relationship_id=native_id_from_bytes(row[0]),
            revision_id=native_id_from_bytes(row[1]),
            transition_id=native_id_from_bytes(row[2]),
        )

    def _require_admission_namespaces(
        self,
        idempotency_namespace_id: UUID,
        relationship_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> None:
        checks = (
            ("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id),
            ("identity_namespaces", "identity_namespace_id", relationship_identity_namespace_id),
            ("semantic_scopes", "semantic_scope_id", unknown_semantic_scope_id),
        )
        for table, column, value in checks:
            if self._connection.execute(
                f"SELECT 1 FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)
            ).fetchone() is None:
                raise SubstrateObjectNotFound(f"required {table} identity was not found")


def _edges_artifact(manifest: LegacySnapshotManifest) -> LegacyArtifact:
    candidates = [
        artifact
        for artifact in manifest.artifacts
        if artifact.artifact_class == "LEGACY_RELATIONSHIP_CANDIDATE_EVIDENCE"
        and artifact.observed_relative_locator == "edges.jsonl"
    ]
    if len(candidates) != 1:
        raise SubstrateRevisionConflict("snapshot must contain exactly one edges.jsonl evidence artifact")
    return candidates[0]


def _extract_edges(
    snapshot_root: str | Path, snapshot_id: UUID, artifact: LegacyArtifact
) -> tuple[tuple[LegacyEdgeCandidate, ...], tuple[LegacyEdgeAdmissionRecord, ...]]:
    root = Path(snapshot_root).expanduser().resolve()
    path = (root / artifact.observed_relative_locator).resolve()
    if root not in path.parents:
        raise SubstrateInvariantViolation("edge evidence locator escapes snapshot root")
    parsed_by_id: dict[str, list[LegacyEdgeCandidate]] = {}
    blocked_ids: set[str] = set()
    records: list[LegacyEdgeAdmissionRecord] = []
    with path.open("rb") as stream:
        for line_ordinal, raw_row_bytes in enumerate(stream, start=1):
            candidate, record = _parse_edge_record(
                snapshot_id, artifact.artifact_id, line_ordinal, raw_row_bytes
            )
            if candidate is not None:
                parsed_by_id.setdefault(candidate.raw_edge_id, []).append(candidate)
            else:
                assert record is not None
                records.append(record)
                if record.raw_edge_id is not None:
                    blocked_ids.add(record.raw_edge_id)
    candidates: list[LegacyEdgeCandidate] = []
    for edge_id, same_id in parsed_by_id.items():
        if len(same_id) != 1:
            records.extend(
                LegacyEdgeAdmissionRecord(
                    item.legacy_snapshot_id,
                    item.legacy_artifact_id,
                    item.line_ordinal,
                    item.raw_edge_id,
                    "NOT_ADMITTED",
                    "stable source edge identifier occurs in multiple edge evidence records",
                )
                for item in same_id
            )
        elif edge_id in blocked_ids:
            item = same_id[0]
            records.append(
                LegacyEdgeAdmissionRecord(
                    item.legacy_snapshot_id,
                    item.legacy_artifact_id,
                    item.line_ordinal,
                    item.raw_edge_id,
                    "NOT_ADMITTED",
                    "a malformed or semantically inadmissible record shares the stable source edge identifier",
                )
            )
        else:
            candidates.append(same_id[0])
    return tuple(candidates), tuple(records)


def _parse_edge_record(
    snapshot_id: UUID,
    artifact_id: UUID,
    line_ordinal: int,
    raw_row_bytes: bytes,
) -> tuple[LegacyEdgeCandidate | None, LegacyEdgeAdmissionRecord | None]:
    try:
        decoded = raw_row_bytes.decode("utf-8")
        value = json.loads(decoded)
    except UnicodeDecodeError:
        return None, _edge_record(snapshot_id, artifact_id, line_ordinal, raw_row_bytes, "UNKNOWN", "row is not valid UTF-8")
    except json.JSONDecodeError:
        return None, _edge_record(snapshot_id, artifact_id, line_ordinal, raw_row_bytes, "UNKNOWN", "row is not valid JSON")
    if not isinstance(value, dict):
        return None, _edge_record(snapshot_id, artifact_id, line_ordinal, raw_row_bytes, "NOT_ADMITTED", "row is not a JSON object")
    edge_id = _stable_edge_id(value.get("edge_id"))
    if edge_id is None:
        return None, _edge_record(snapshot_id, artifact_id, line_ordinal, raw_row_bytes, "NOT_ADMITTED", "row lacks a stable source edge identifier")
    if value.get("relationship_kind") != _ADMISSIBLE_LEGACY_RELATIONSHIP_KIND:
        return None, LegacyEdgeAdmissionRecord(
            snapshot_id,
            artifact_id,
            line_ordinal,
            edge_id,
            "NOT_ADMITTED",
            "legacy relationship kind lacks the frozen LEGACY_EDGE interpretation",
        )
    endpoints, reason = _edge_endpoints(value)
    if reason is not None:
        return None, LegacyEdgeAdmissionRecord(
            snapshot_id, artifact_id, line_ordinal, edge_id, "NOT_ADMITTED", reason
        )
    attributes = {
        key: item
        for key, item in value.items()
        if key not in {"edge_id", "relationship_kind", "endpoints", "source", "target"}
    }
    return LegacyEdgeCandidate(
        snapshot_id, artifact_id, line_ordinal, edge_id, endpoints, attributes
    ), None


def _edge_endpoints(
    value: dict[str, Any],
) -> tuple[tuple[LegacyRelationshipEndpointCandidate, ...], str | None]:
    raw_endpoints = value.get("endpoints")
    if raw_endpoints is None and "source" in value and "target" in value:
        raw_endpoints = [
            {"role": "SOURCE", "eid": value["source"]},
            {"role": "TARGET", "eid": value["target"]},
        ]
    if not isinstance(raw_endpoints, list) or len(raw_endpoints) < 2:
        return (), "relationship candidate requires at least two explicit endpoints"
    endpoints: list[LegacyRelationshipEndpointCandidate] = []
    for ordinal, endpoint in enumerate(raw_endpoints):
        if not isinstance(endpoint, dict):
            return (), f"endpoint ordinal {ordinal} is not an object"
        role, raw_eid = endpoint.get("role"), endpoint.get("eid")
        if not isinstance(role, str) or not role:
            return (), f"endpoint ordinal {ordinal} lacks a non-empty role"
        if not isinstance(raw_eid, int) or isinstance(raw_eid, bool) or raw_eid < 0:
            return (), f"endpoint ordinal {ordinal} lacks a non-negative integer EID"
        endpoints.append(LegacyRelationshipEndpointCandidate(ordinal, role, raw_eid))
    return tuple(endpoints), None


def _edge_record(
    snapshot_id: UUID,
    artifact_id: UUID,
    line_ordinal: int,
    raw_row_bytes: bytes,
    status: str,
    reason: str,
) -> LegacyEdgeAdmissionRecord:
    return LegacyEdgeAdmissionRecord(
        snapshot_id,
        artifact_id,
        line_ordinal,
        _conservative_malformed_edge_id(raw_row_bytes),
        status,
        reason,
    )


def _stable_edge_id(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return str(value)
    return None


def _conservative_malformed_edge_id(raw_row_bytes: bytes) -> str | None:
    try:
        decoded = raw_row_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None
    match = _MALFORMED_EDGE_ID_PREFIX.match(decoded)
    if match is None:
        return None
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return _stable_edge_id(value)


def _edge_record_identity(line_ordinal: int) -> str:
    return f"TMS-LEGACY-EDGES-LINE-1:{line_ordinal}"


def _edge_record_locator(line_ordinal: int) -> str:
    return f"edges.jsonl#line:{line_ordinal}"


def _relationship_admission_intent(kind: str, candidate: LegacyEdgeCandidate) -> str:
    return canonical_intent_text(
        {
            "kind": kind,
            "legacy_snapshot_id": str(candidate.legacy_snapshot_id),
            "legacy_artifact_id": str(candidate.legacy_artifact_id),
            "record_identity": _edge_record_identity(candidate.line_ordinal),
            "raw_edge_id": candidate.raw_edge_id,
        }
    )


def _relationship_record_intent(record: LegacyEdgeAdmissionRecord) -> str:
    return canonical_intent_text(
        {
            "kind": "RECORD_LEGACY_RELATIONSHIP_ADMISSION_" + record.admission_status,
            "legacy_snapshot_id": str(record.legacy_snapshot_id),
            "legacy_artifact_id": str(record.legacy_artifact_id),
            "record_identity": _edge_record_identity(record.line_ordinal),
            "reason": record.reason,
        }
    )
