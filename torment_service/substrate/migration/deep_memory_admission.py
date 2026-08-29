"""Conservative admission of captured deep-memory derivation content.

The supported source is the current workspace-agent
``deep_memory/memories.jsonl`` store.  Its loader selects the latest
successfully parsed row per EID; this migration preserves only that observed
current candidate, never append history.  A row becomes a non-READY
representation only after the exact imported source revision proves the
completed long-path export marker.
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
from ..representations import NativeRepresentationService, RepresentationMetadata
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


LEGACY_DEEP_MEMORY_REPRESENTATION_CLASS: Final[str] = "LEGACY_DEEP_MEMORY_CAPTURE"
LEGACY_DEEP_MEMORY_LOCAL_GENERATION: Final[int] = 1
LEGACY_DEEP_MEMORY_ENCODING: Final[str] = "LEGACY_DEEP_MEMORY_JSONL_UTF8"
LEGACY_UNSPECIFIED_DERIVATION_CONTRACT: Final[str] = "LEGACY_UNSPECIFIED"
_ADMISSION_BATCH_IDENTITY: Final[str] = "TMS-LEGACY-DEEP-MEMORY-ADMISSION-7F3E"


@dataclass(frozen=True)
class LegacyDeepMemoryCandidate:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    line_ordinal: int
    raw_row_bytes: bytes
    record: dict[str, Any]

    @property
    def raw_eid(self) -> int:
        return self.record["eid"]

    @property
    def compressed_step(self) -> int:
        return self.record["compressed_step"]

    @property
    def record_identity(self) -> str:
        return _record_identity(self.line_ordinal)

    @property
    def record_locator(self) -> str:
        return _record_locator(self.line_ordinal)


@dataclass(frozen=True)
class LegacyDeepMemoryAdmissionRecord:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    line_ordinal: int
    admission_status: str
    reason: str
    raw_eid: int | None = None

    @property
    def record_identity(self) -> str:
        return _record_identity(self.line_ordinal)

    @property
    def record_locator(self) -> str:
        return _record_locator(self.line_ordinal)


@dataclass(frozen=True)
class LegacyDeepMemoryAdmissionResult:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    line_ordinal: int
    raw_eid: int | None
    admission_status: str
    admission_record_id: UUID
    operation_id: UUID
    representation_id: UUID | None = None
    transition_id: UUID | None = None
    source_object_id: UUID | None = None
    source_revision_id: UUID | None = None


@dataclass(frozen=True)
class LegacyDeepMemoryAdmissionRun:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    results: tuple[LegacyDeepMemoryAdmissionResult, ...]


class NativeLegacyDeepMemoryAdmissionService:
    """Typed deep-memory capture boundary; no compression replay or live wiring."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection)
        self._connection = connection

    def admit_deep_memory_current_state(
        self,
        *,
        snapshot_root: str | Path,
        manifest_path: str | Path,
        idempotency_namespace_id: UUID,
    ) -> LegacyDeepMemoryAdmissionRun:
        """Admit selected corroborated deep content, keeping optional vectors separate."""
        self._require_idempotency_namespace(idempotency_namespace_id)
        manifest = load_snapshot_manifest(manifest_path)
        inventory_snapshot(
            self._connection, snapshot_root=snapshot_root, manifest_path=manifest_path
        )
        artifact = _deep_memory_artifact(manifest)
        candidates, records = _extract_deep_memory_evidence(
            snapshot_root, manifest.legacy_snapshot_id, artifact
        )
        results: list[LegacyDeepMemoryAdmissionResult] = []
        for item in sorted((*candidates, *records), key=lambda value: value.line_ordinal):
            if isinstance(item, LegacyDeepMemoryCandidate):
                results.append(self._admit_candidate(manifest, item, idempotency_namespace_id))
            else:
                results.append(self._record_uncertainty(manifest, item, idempotency_namespace_id))
        return LegacyDeepMemoryAdmissionRun(manifest.legacy_snapshot_id, artifact.artifact_id, tuple(results))

    def get_admitted_deep_memory_metadata(self, representation_id: UUID) -> RepresentationMetadata:
        """Metadata-only read for an admitted non-READY deep capture."""
        return NativeRepresentationService(self._connection).get_representation_metadata(representation_id)

    def read_admitted_deep_memory_payload(self, representation_id: UUID) -> bytes:
        """Explicit evidence read; it does not make captured deep content usable live."""
        row = self._connection.execute(
            """
            SELECT p.payload_bytes
            FROM representations r
            JOIN representation_current_state s USING(representation_id)
            JOIN representation_payloads p USING(representation_id)
            WHERE r.representation_id=? AND r.representation_class=?
              AND s.readiness='UNKNOWN' AND s.operational_disposition='RECONCILIATION_REQUIRED'
            """,
            (native_id_to_bytes(representation_id), LEGACY_DEEP_MEMORY_REPRESENTATION_CLASS),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("admitted legacy deep-memory payload was not found")
        return row[0]

    def _admit_candidate(
        self,
        manifest: LegacySnapshotManifest,
        candidate: LegacyDeepMemoryCandidate,
        idempotency_namespace_id: UUID,
    ) -> LegacyDeepMemoryAdmissionResult:
        intent = _candidate_intent(candidate)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "ADMIT_LEGACY_DEEP_MEMORY_CURRENT",
            intent,
            lambda operation_id: self._recorded_result(operation_id, manifest, candidate),
            lambda tx: self._publish_candidate(tx, manifest, candidate),
        )

    def _record_uncertainty(
        self,
        manifest: LegacySnapshotManifest,
        record: LegacyDeepMemoryAdmissionRecord,
        idempotency_namespace_id: UUID,
    ) -> LegacyDeepMemoryAdmissionResult:
        intent = _record_intent(record)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "RECORD_LEGACY_DEEP_MEMORY_ADMISSION_" + record.admission_status,
            intent,
            lambda operation_id: self._recorded_result(operation_id, manifest, record),
            lambda tx: self._publish_uncertainty(tx, manifest, record),
        )

    def _publish_candidate(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        candidate: LegacyDeepMemoryCandidate,
    ) -> LegacyDeepMemoryAdmissionResult:
        snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
        source_namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
        artifact_id = native_id_to_bytes(candidate.legacy_artifact_id)
        batch_id = _ensure_admission_batch(tx, snapshot_id, _ADMISSION_BATCH_IDENTITY)
        artifact_record_id = _ensure_artifact_record(
            tx, artifact_id, candidate.record_identity, candidate.record_locator
        )
        if _admission_record_for_artifact_record(tx, batch_id, artifact_record_id) is not None:
            raise SubstrateRevisionConflict("legacy deep-memory evidence already has an admission result")
        source, reason = self._resolve_corroborated_source(
            tx, source_namespace_id, candidate
        )
        if reason is not None:
            return self._publish_candidate_quarantine(
                tx, manifest, candidate, batch_id, artifact_record_id, reason
            )
        source_object_id, source_revision_id, source_revision_ordinal, source_payload = source
        representation_id, transition_id, admission_record_id = _new(), _new(), _new()
        now_ns = time.time_ns()
        motif_linkage = self._motif_linkage(tx, source_namespace_id, candidate.record.get("original_motif_id"))
        tx.execute(
            """
            INSERT INTO representations(
                representation_id,source_kind,source_object_id,source_object_revision_id,
                source_object_revision_ordinal,representation_class,generation,
                derivation_contract_version,encoding_id,dtype,dimension,
                expected_payload_byte_length,created_at_ns
            ) VALUES (?,'OBJECT_REVISION',?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                representation_id,
                source_object_id,
                source_revision_id,
                source_revision_ordinal,
                LEGACY_DEEP_MEMORY_REPRESENTATION_CLASS,
                LEGACY_DEEP_MEMORY_LOCAL_GENERATION,
                LEGACY_UNSPECIFIED_DERIVATION_CONTRACT,
                LEGACY_DEEP_MEMORY_ENCODING,
                None,
                None,
                len(candidate.raw_row_bytes),
                now_ns,
            ),
        )
        tx.execute(
            "INSERT INTO representation_current_state VALUES (?,'UNKNOWN','RECONCILIATION_REQUIRED',NULL)",
            (representation_id,),
        )
        tx.execute(
            "INSERT INTO representation_payloads VALUES (?,?,?,?)",
            (representation_id, candidate.raw_row_bytes, len(candidate.raw_row_bytes), now_ns),
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
                        "deep_record": {
                            "eid": candidate.raw_eid,
                            "born_step": candidate.record["born_step"],
                            "compressed_step": candidate.compressed_step,
                            "summary": candidate.record["summary"],
                            "summary_encoding": "UTF8_JSONL_RECORD",
                            "compression_score": candidate.record["compression_score"],
                            "original_motif_id": candidate.record["original_motif_id"],
                            "memory_class": candidate.record["memory_class"],
                            "embedding_ref": candidate.record["embedding_ref"],
                            "metadata": candidate.record["metadata"],
                        },
                        "completed_export_corroboration": {
                            "exported_deep": True,
                            "compression_route": "long_path",
                            "exported_step": source_payload["exported_step"],
                            "source_compression_score": source_payload.get("compression_score"),
                            "deep_compression_score": candidate.record["compression_score"],
                            "score_comparison": "OBSERVED_NOT_USED_AS_BRITTLE_IDENTITY_GATE",
                        },
                        "original_motif_linkage": motif_linkage,
                        "optional_deep_embedding": "REFERENCE_PRESERVED_ADMISSION_DEFERRED"
                        if candidate.record["embedding_ref"] is not None
                        else "NOT_PRESENT",
                        "native_readiness": "UNKNOWN",
                        "operational_disposition": "RECONCILIATION_REQUIRED",
                        "semantic_integrity_expectation": "NOT_ESTABLISHED_FROM_CAPTURED_BYTES",
                        "original_provenance": "UNKNOWN",
                    }
                ),
            ),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,?)",
            (transition_id, tx.operation_id, "LEGACY_DEEP_MEMORY_ADMISSION", "LEGACY_ADMISSION", now_ns),
        )
        tx.execute(
            "INSERT INTO representation_state_effects VALUES (?,?,?, ?,NULL)",
            (transition_id, representation_id, "UNKNOWN", "RECONCILIATION_REQUIRED"),
        )
        tx.execute("INSERT INTO legacy_admission_effects VALUES (?,?)", (transition_id, admission_record_id))
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,representation_id
            ) VALUES (?,?,?,?,?)
            """,
            (tx.operation_id, 0, "LEGACY_DEEP_MEMORY_ADMISSION", "REPRESENTATION", representation_id),
        )
        tx.transitions.append(transition_id)
        tx.representation_published.append(representation_id)
        tx.legacy_deep_memory_admitted.append(
            (
                representation_id,
                admission_record_id,
                transition_id,
                snapshot_id,
                artifact_id,
                artifact_record_id,
                source_object_id,
                source_revision_id,
                source_revision_ordinal,
                str(candidate.raw_eid),
                candidate.compressed_step,
                len(candidate.raw_row_bytes),
            )
        )
        result = self._recorded_result(tx.operation_id, manifest, candidate)
        if result is None:
            raise SubstrateInvariantViolation("legacy deep-memory admission result was not durable")
        return result

    def _publish_candidate_quarantine(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        candidate: LegacyDeepMemoryCandidate,
        batch_id: bytes,
        artifact_record_id: bytes,
        reason: str,
    ) -> LegacyDeepMemoryAdmissionResult:
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
                canonical_intent_text({"reason": reason, "raw_eid": candidate.raw_eid}),
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
                "UNCONFIRMED_LEGACY_DEEP_MEMORY_EXPORT",
                reason,
                native_id_to_bytes(candidate.legacy_artifact_id),
            ),
        )
        result = self._recorded_result(tx.operation_id, manifest, candidate)
        if result is None:
            raise SubstrateInvariantViolation("quarantined deep-memory admission result was not durable")
        return result

    def _publish_uncertainty(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        record: LegacyDeepMemoryAdmissionRecord,
    ) -> LegacyDeepMemoryAdmissionResult:
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
                    canonical_intent_text({"reason": record.reason, "raw_eid": record.raw_eid}),
                ),
            )
        elif existing[1] != record.admission_status:
            raise SubstrateRevisionConflict("legacy deep-memory evidence has a different admission result")
        result = self._recorded_result(tx.operation_id, manifest, record)
        if result is None:
            raise SubstrateInvariantViolation("legacy deep-memory uncertainty result was not durable")
        return result

    def _resolve_corroborated_source(
        self,
        tx: SubstrateTx,
        source_namespace_id: bytes,
        candidate: LegacyDeepMemoryCandidate,
    ) -> tuple[tuple[bytes, bytes, int, dict[str, Any]] | None, str | None]:
        rows = tx.execute(
            """
            SELECT a.object_id,r.object_revision_id,r.revision_ordinal,r.payload_text
            FROM legacy_object_aliases a
            JOIN objects o ON o.object_id=a.object_id
            JOIN object_revisions r ON r.object_id=o.object_id
            JOIN semantic_transitions t ON t.transition_id=o.creating_transition_id
            WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID' AND a.alias_value=?
              AND o.object_kind='LEGACY_CORE_NODE'
              AND r.lineage_kind='LEGACY_PREDECESSOR_UNKNOWN' AND r.revision_ordinal=1
              AND r.payload_format='TEXT'
              AND t.transition_kind='LEGACY_OBJECT_ADMISSION' AND t.origin_kind='LEGACY_ADMISSION'
            """,
            (source_namespace_id, str(candidate.raw_eid)),
        ).fetchall()
        if len(rows) != 1:
            return None, "deep record EID does not resolve to exactly one imported source object revision"
        try:
            source_payload = json.loads(rows[0][3])
        except (TypeError, json.JSONDecodeError):
            return None, "imported source object payload is not trustworthy JSON export evidence"
        if not isinstance(source_payload, dict):
            return None, "imported source object payload is not a JSON object"
        if (
            source_payload.get("eid") != candidate.raw_eid
            or source_payload.get("exported_deep") is not True
            or source_payload.get("compression_route") != "long_path"
            or not _nonnegative_int(source_payload.get("exported_step"))
            or source_payload["exported_step"] != candidate.compressed_step
        ):
            return None, "source core evidence does not corroborate a completed long-path deep export"
        return (rows[0][0], rows[0][1], rows[0][2], source_payload), None

    def _motif_linkage(
        self, tx: SubstrateTx, source_namespace_id: bytes, original_motif_id: object
    ) -> dict[str, Any]:
        if not isinstance(original_motif_id, str) or not original_motif_id:
            return {"status": "NOT_PRESENT"}
        rows = tx.execute(
            """
            SELECT a.object_id FROM legacy_object_aliases a
            JOIN objects o ON o.object_id=a.object_id
            JOIN semantic_transitions t ON t.transition_id=o.creating_transition_id
            WHERE a.legacy_source_namespace_id=? AND a.alias_kind='MOTIF_ID' AND a.alias_value=?
              AND o.object_kind='LEGACY_DERIVED_MOTIF'
              AND t.transition_kind='LEGACY_MOTIF_ADMISSION' AND t.origin_kind='LEGACY_ADMISSION'
            """,
            (source_namespace_id, original_motif_id),
        ).fetchall()
        if len(rows) == 1:
            return {"status": "RESOLVED_SOURCE_ALIAS", "motif_object_id": str(native_id_from_bytes(rows[0][0]))}
        return {"status": "UNRESOLVED_PRESERVED", "original_motif_id": original_motif_id}

    def _recorded_result(
        self,
        operation_id: bytes,
        manifest: LegacySnapshotManifest,
        item: LegacyDeepMemoryCandidate | LegacyDeepMemoryAdmissionRecord,
    ) -> LegacyDeepMemoryAdmissionResult | None:
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
                item.record_identity,
            ),
        ).fetchone()
        raw_eid = item.raw_eid
        if record is None:
            return None
        if record[1] != "ADMITTED":
            return LegacyDeepMemoryAdmissionResult(
                item.legacy_snapshot_id,
                item.legacy_artifact_id,
                item.line_ordinal,
                raw_eid,
                record[1],
                native_id_from_bytes(record[0]),
                native_id_from_bytes(operation_id),
            )
        row = self._connection.execute(
            """
            SELECT o.representation_id,t.transition_id,t.operation_id,
                   r.source_object_id,r.source_object_revision_id,a.admission_record_id
            FROM operation_outputs o
            JOIN semantic_transitions t ON t.operation_id=o.operation_id
            JOIN representation_state_effects e ON e.transition_id=t.transition_id
            JOIN legacy_admission_effects le ON le.transition_id=t.transition_id
            JOIN legacy_admission_records a ON a.admission_record_id=le.admission_record_id
            JOIN representations r ON r.representation_id=o.representation_id
            WHERE o.operation_id=? AND o.output_kind='REPRESENTATION'
              AND o.output_role='LEGACY_DEEP_MEMORY_ADMISSION'
              AND e.representation_id=o.representation_id
              AND e.readiness='UNKNOWN' AND e.operational_disposition='RECONCILIATION_REQUIRED'
              AND a.admission_record_id=? AND a.admission_status='ADMITTED'
            """,
            (operation_id, record[0]),
        ).fetchone()
        if row is None:
            return None
        return LegacyDeepMemoryAdmissionResult(
            item.legacy_snapshot_id,
            item.legacy_artifact_id,
            item.line_ordinal,
            raw_eid,
            "ADMITTED",
            native_id_from_bytes(row[5]),
            native_id_from_bytes(row[2]),
            native_id_from_bytes(row[0]),
            native_id_from_bytes(row[1]),
            native_id_from_bytes(row[3]),
            native_id_from_bytes(row[4]),
        )

    def _require_idempotency_namespace(self, namespace_id: UUID) -> None:
        if self._connection.execute(
            "SELECT 1 FROM idempotency_namespaces WHERE idempotency_namespace_id=?",
            (native_id_to_bytes(namespace_id),),
        ).fetchone() is None:
            raise SubstrateObjectNotFound("required idempotency namespace was not found")


def _deep_memory_artifact(manifest: LegacySnapshotManifest) -> LegacyArtifact:
    candidates = [
        artifact
        for artifact in manifest.artifacts
        if _is_deep_memory_locator(artifact.observed_relative_locator)
        and artifact.artifact_class == "LEGACY_DEEP_MEMORY_EVIDENCE"
    ]
    if len(candidates) != 1:
        raise SubstrateRevisionConflict("snapshot must contain exactly one current deep_memory/memories.jsonl evidence artifact")
    return candidates[0]


def _extract_deep_memory_evidence(
    snapshot_root: str | Path, snapshot_id: UUID, artifact: LegacyArtifact
) -> tuple[tuple[LegacyDeepMemoryCandidate, ...], tuple[LegacyDeepMemoryAdmissionRecord, ...]]:
    root = Path(snapshot_root).expanduser().resolve()
    path = (root / artifact.observed_relative_locator).resolve()
    if root not in path.parents:
        raise SubstrateInvariantViolation("deep-memory evidence locator escapes snapshot root")
    latest: dict[int, tuple[int, bytes, dict[str, Any]]] = {}
    records: list[LegacyDeepMemoryAdmissionRecord] = []
    try:
        lines = path.read_bytes().splitlines(keepends=True)
    except OSError as exc:
        raise SubstrateInvariantViolation("deep-memory evidence cannot be read after snapshot verification") from exc
    for line_ordinal, raw_row_bytes in enumerate(lines, start=1):
        if not raw_row_bytes.strip():
            continue
        loaded, reason = _loader_parse_row(raw_row_bytes)
        if loaded is None:
            records.append(
                LegacyDeepMemoryAdmissionRecord(
                    snapshot_id, artifact.artifact_id, line_ordinal, "UNKNOWN", reason
                )
            )
            continue
        raw_eid, raw_record = loaded
        latest[raw_eid] = (line_ordinal, raw_row_bytes, raw_record)
    candidates: list[LegacyDeepMemoryCandidate] = []
    for raw_eid, (line_ordinal, raw_row_bytes, raw_record) in latest.items():
        try:
            record = _trusted_deep_record(raw_record)
        except ValueError as exc:
            records.append(
                LegacyDeepMemoryAdmissionRecord(
                    snapshot_id,
                    artifact.artifact_id,
                    line_ordinal,
                    "UNKNOWN",
                    str(exc),
                    raw_eid,
                )
            )
        else:
            candidates.append(
                LegacyDeepMemoryCandidate(snapshot_id, artifact.artifact_id, line_ordinal, raw_row_bytes, record)
            )
    return tuple(candidates), tuple(records)


def _loader_parse_row(raw_row_bytes: bytes) -> tuple[tuple[int, dict[str, Any]] | None, str]:
    """Match ``DeepMemory.from_dict`` selection behavior without using its runtime store."""
    try:
        decoded = raw_row_bytes.strip().decode("utf-8")
        value = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "deep-memory row is not valid UTF-8 JSON"
    if not isinstance(value, dict):
        return None, "deep-memory row is not a JSON object"
    try:
        raw_eid = int(value.get("eid", 0))
        int(value.get("born_step", 0) or 0)
        int(value.get("compressed_step", 0) or 0)
        str(value.get("summary", "") or "")
        float(value.get("compression_score", 0.0) or 0.0)
        str(value.get("memory_class", "core") or "core")
        dict(value.get("metadata", {}) or {})
    except (TypeError, ValueError, OverflowError):
        return None, "deep-memory row does not satisfy legacy loader coercions"
    return (raw_eid, value), ""


def _trusted_deep_record(raw: dict[str, Any]) -> dict[str, Any]:
    eid = raw.get("eid")
    born_step = raw.get("born_step")
    compressed_step = raw.get("compressed_step")
    summary = raw.get("summary")
    compression_score = raw.get("compression_score", 0.0)
    original_motif_id = raw.get("original_motif_id")
    memory_class = raw.get("memory_class", "core")
    embedding_ref = raw.get("embedding_ref")
    metadata = raw.get("metadata", {})
    if not _nonnegative_int(eid) or not _nonnegative_int(born_step) or not _nonnegative_int(compressed_step):
        raise ValueError("selected deep-memory row lacks non-negative integer EID or steps")
    if not isinstance(summary, str) or not _finite_number(compression_score):
        raise ValueError("selected deep-memory row lacks text summary or finite compression score")
    if original_motif_id is not None and not isinstance(original_motif_id, str):
        raise ValueError("selected deep-memory original_motif_id is not text or null")
    if not isinstance(memory_class, str) or not memory_class:
        raise ValueError("selected deep-memory memory_class is not non-empty text")
    if embedding_ref is not None and not isinstance(embedding_ref, dict):
        raise ValueError("selected deep-memory embedding_ref is not an object or null")
    if not isinstance(metadata, dict):
        raise ValueError("selected deep-memory metadata is not an object")
    return {
        "eid": eid,
        "born_step": born_step,
        "compressed_step": compressed_step,
        "summary": summary,
        "compression_score": compression_score,
        "original_motif_id": original_motif_id,
        "memory_class": memory_class,
        "embedding_ref": embedding_ref,
        "metadata": metadata,
    }


def _is_deep_memory_locator(locator: str) -> bool:
    path = PurePosixPath(locator)
    parts = path.parts
    return (
        len(parts) == 6
        and parts[0] == "workspaces"
        and parts[2] == "agents"
        and parts[4] == "deep_memory"
        and path.name == "memories.jsonl"
        and all(parts[index] for index in (1, 3))
    )


def _record_identity(line_ordinal: int) -> str:
    return f"TMS-LEGACY-DEEP-MEMORY-LINE-1:{line_ordinal}"


def _record_locator(line_ordinal: int) -> str:
    return f"deep_memory/memories.jsonl#line:{line_ordinal}"


def _candidate_intent(candidate: LegacyDeepMemoryCandidate) -> str:
    return canonical_intent_text(
        {
            "kind": "ADMIT_LEGACY_DEEP_MEMORY_CURRENT",
            "legacy_snapshot_id": str(candidate.legacy_snapshot_id),
            "legacy_artifact_id": str(candidate.legacy_artifact_id),
            "record_identity": candidate.record_identity,
            "raw_eid": candidate.raw_eid,
        }
    )


def _record_intent(record: LegacyDeepMemoryAdmissionRecord) -> str:
    return canonical_intent_text(
        {
            "kind": "RECORD_LEGACY_DEEP_MEMORY_ADMISSION_" + record.admission_status,
            "legacy_snapshot_id": str(record.legacy_snapshot_id),
            "legacy_artifact_id": str(record.legacy_artifact_id),
            "record_identity": record.record_identity,
            "reason": record.reason,
        }
    )


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
