"""Phase 7F3B conservative admission of frozen legacy embedding evidence.

Captured vector bytes are retained only when the node reference, namespaced
object alias, exact imported source revision, embedding manifest, map row, and
NPY shard agree.  This module intentionally does not reconstruct derivation
history or publish legacy bytes as native READY representations.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
import time
from typing import Any
from uuid import UUID

from ..canonical_intent import canonical_intent_text
from ..errors import SubstrateInvariantViolation, SubstrateObjectNotFound, SubstrateRevisionConflict
from ..ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from ..objects import SubstrateTx, execute_semantic
from ..representations import NativeRepresentationService, RepresentationMetadata
from ..schema import open_schema
from .admission import (
    _admission_record_for_artifact_record,
    _ensure_admission_batch,
    _ensure_artifact_record,
    _evidence_idempotency_key,
)
from .inventory import inventory_snapshot
from .snapshot import LegacyArtifact, LegacySnapshotManifest, load_snapshot_manifest


LEGACY_EMBEDDING_REPRESENTATION_CLASS = "LEGACY_EMBEDDING_CAPTURE"
LEGACY_EMBEDDING_LOCAL_GENERATION = 1
LEGACY_UNSPECIFIED_DERIVATION_CONTRACT = "LEGACY_UNSPECIFIED"
_ADMISSION_BATCH_IDENTITY = "TMS-LEGACY-REPRESENTATION-ADMISSION-7F3B"
_SUPPORTED_ENCODING = "NUMPY_NPY"


@dataclass(frozen=True)
class LegacyEmbeddingReference:
    legacy_snapshot_id: UUID
    node_artifact_id: UUID
    line_ordinal: int
    raw_eid: int
    raw_node_text: str
    map_locator: str
    shard_locator: str
    row_ordinal: int
    dimension: int
    dtype: str | None


@dataclass(frozen=True)
class _MapEntry:
    artifact_id: UUID
    line_ordinal: int
    raw_eid: int
    shard_locator: str
    row_ordinal: int
    dimension: int | None


@dataclass(frozen=True)
class LegacyEmbeddingCandidate:
    reference: LegacyEmbeddingReference
    map_entry: _MapEntry
    map_artifact_id: UUID
    shard_artifact_id: UUID
    encoding_id: str
    dtype: str
    derivation_contract_version: str
    known_derivation_metadata: dict[str, str]
    payload_bytes: bytes


@dataclass(frozen=True)
class LegacyEmbeddingAdmissionRecord:
    reference: LegacyEmbeddingReference
    admission_status: str
    reason: str
    artifact_id: UUID
    record_identity: str
    observed_locator: str


@dataclass(frozen=True)
class LegacyRepresentationAdmissionResult:
    legacy_snapshot_id: UUID
    node_artifact_id: UUID
    line_ordinal: int
    raw_eid: int
    admission_status: str
    admission_record_id: UUID
    operation_id: UUID
    representation_id: UUID | None = None
    transition_id: UUID | None = None
    source_object_id: UUID | None = None
    source_revision_id: UUID | None = None


@dataclass(frozen=True)
class LegacyEmbeddingAdmissionRun:
    legacy_snapshot_id: UUID
    results: tuple[LegacyRepresentationAdmissionResult, ...]


class NativeLegacyRepresentationAdmissionService:
    """Typed legacy vector evidence boundary; ``SubstrateTx`` is its only owner."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection)
        self._connection = connection

    def admit_embedding_evidence(
        self,
        *,
        snapshot_root: str | Path,
        manifest_path: str | Path,
        idempotency_namespace_id: UUID,
    ) -> LegacyEmbeddingAdmissionRun:
        """Admit only complete, exact object-revision embedding evidence chains."""
        self._require_idempotency_namespace(idempotency_namespace_id)
        manifest = load_snapshot_manifest(manifest_path)
        inventory_snapshot(
            self._connection, snapshot_root=snapshot_root, manifest_path=manifest_path
        )
        candidates, records = _extract_embedding_evidence(
            snapshot_root, manifest, _artifacts_by_locator(manifest)
        )
        results: list[LegacyRepresentationAdmissionResult] = []
        for item in sorted((*candidates, *records), key=lambda value: value.reference.line_ordinal):
            if isinstance(item, LegacyEmbeddingCandidate):
                results.append(self._admit_candidate(manifest, item, idempotency_namespace_id))
            else:
                results.append(self._record_uncertainty(manifest, item, idempotency_namespace_id))
        return LegacyEmbeddingAdmissionRun(manifest.legacy_snapshot_id, tuple(results))

    def get_admitted_representation_metadata(
        self, representation_id: UUID
    ) -> RepresentationMetadata:
        """Metadata-only read for an admitted, intentionally non-READY representation."""
        return NativeRepresentationService(self._connection).get_representation_metadata(representation_id)

    def read_admitted_representation_payload(self, representation_id: UUID) -> bytes:
        """Explicit evidence read; this does not make the representation usable for search."""
        row = self._connection.execute(
            """
            SELECT p.payload_bytes
            FROM representations r
            JOIN representation_current_state s USING(representation_id)
            JOIN representation_payloads p USING(representation_id)
            WHERE r.representation_id=?
              AND r.representation_class=?
              AND s.readiness='UNKNOWN'
              AND s.operational_disposition='RECONCILIATION_REQUIRED'
            """,
            (native_id_to_bytes(representation_id), LEGACY_EMBEDDING_REPRESENTATION_CLASS),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("admitted legacy representation payload was not found")
        return row[0]

    def _admit_candidate(
        self,
        manifest: LegacySnapshotManifest,
        candidate: LegacyEmbeddingCandidate,
        idempotency_namespace_id: UUID,
    ) -> LegacyRepresentationAdmissionResult:
        intent = _candidate_intent(candidate)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "ADMIT_LEGACY_EMBEDDING_EVIDENCE",
            intent,
            lambda operation_id: self._recorded_result(operation_id, manifest, candidate),
            lambda tx: self._publish_candidate(tx, manifest, candidate),
        )

    def _record_uncertainty(
        self,
        manifest: LegacySnapshotManifest,
        record: LegacyEmbeddingAdmissionRecord,
        idempotency_namespace_id: UUID,
    ) -> LegacyRepresentationAdmissionResult:
        intent = _record_intent(record)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "RECORD_LEGACY_EMBEDDING_ADMISSION_" + record.admission_status,
            intent,
            lambda operation_id: self._recorded_result(operation_id, manifest, record),
            lambda tx: self._publish_uncertainty(tx, manifest, record),
        )

    def _publish_candidate(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        candidate: LegacyEmbeddingCandidate,
    ) -> LegacyRepresentationAdmissionResult:
        reference = candidate.reference
        snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
        source_namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
        map_artifact_id = native_id_to_bytes(candidate.map_artifact_id)
        batch_id = _ensure_admission_batch(tx, snapshot_id, _ADMISSION_BATCH_IDENTITY)
        map_record_id = _ensure_artifact_record(
            tx,
            map_artifact_id,
            _map_record_identity(candidate.map_entry.line_ordinal),
            _map_record_locator(candidate.map_entry.line_ordinal),
        )
        if _admission_record_for_artifact_record(tx, batch_id, map_record_id) is not None:
            raise SubstrateRevisionConflict("legacy embedding map evidence already has an admission result")
        source, source_reason = self._resolve_imported_source(
            tx, source_namespace_id, reference
        )
        if source_reason is not None:
            record = LegacyEmbeddingAdmissionRecord(
                reference,
                "QUARANTINED",
                source_reason,
                candidate.map_artifact_id,
                _map_record_identity(candidate.map_entry.line_ordinal),
                _map_record_locator(candidate.map_entry.line_ordinal),
            )
            return self._publish_uncertainty(tx, manifest, record)
        object_id, revision_id, revision_ordinal = source
        representation_id, transition_id, admission_record_id = _new(), _new(), _new()
        now_ns = time.time_ns()
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
                object_id,
                revision_id,
                revision_ordinal,
                LEGACY_EMBEDDING_REPRESENTATION_CLASS,
                LEGACY_EMBEDDING_LOCAL_GENERATION,
                candidate.derivation_contract_version,
                candidate.encoding_id,
                candidate.dtype,
                reference.dimension,
                len(candidate.payload_bytes),
                now_ns,
            ),
        )
        tx.execute(
            "INSERT INTO representation_current_state VALUES (?,'UNKNOWN','RECONCILIATION_REQUIRED',NULL)",
            (representation_id,),
        )
        tx.execute(
            "INSERT INTO representation_payloads VALUES (?,?,?,?)",
            (representation_id, candidate.payload_bytes, len(candidate.payload_bytes), now_ns),
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
                map_record_id,
                canonical_intent_text(
                    {
                        "admission_local_generation": LEGACY_EMBEDDING_LOCAL_GENERATION,
                        "derivation_contract_version": candidate.derivation_contract_version,
                        "legacy_derivation_metadata": candidate.known_derivation_metadata,
                        "native_readiness": "UNKNOWN",
                        "operational_disposition": "RECONCILIATION_REQUIRED",
                        "semantic_integrity_expectation": "NOT_ESTABLISHED_FROM_CAPTURED_BYTES",
                    }
                ),
            ),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,?)",
            (transition_id, tx.operation_id, "LEGACY_REPRESENTATION_ADMISSION", "LEGACY_ADMISSION", now_ns),
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
            (tx.operation_id, 0, "LEGACY_REPRESENTATION_ADMISSION", "REPRESENTATION", representation_id),
        )
        tx.transitions.append(transition_id)
        tx.representation_published.append(representation_id)
        tx.legacy_representation_admitted.append(
            (
                representation_id,
                admission_record_id,
                transition_id,
                snapshot_id,
                native_id_to_bytes(reference.node_artifact_id),
                native_id_to_bytes(candidate.map_artifact_id),
                native_id_to_bytes(candidate.shard_artifact_id),
                map_record_id,
                object_id,
                revision_id,
                revision_ordinal,
                str(reference.raw_eid),
                len(candidate.payload_bytes),
            )
        )
        result = self._recorded_result(tx.operation_id, manifest, candidate)
        if result is None:
            raise SubstrateInvariantViolation("legacy representation admission result was not durable")
        return result

    def _publish_uncertainty(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        record: LegacyEmbeddingAdmissionRecord,
    ) -> LegacyRepresentationAdmissionResult:
        batch_id = _ensure_admission_batch(
            tx, native_id_to_bytes(manifest.legacy_snapshot_id), _ADMISSION_BATCH_IDENTITY
        )
        artifact_record_id = _ensure_artifact_record(
            tx,
            native_id_to_bytes(record.artifact_id),
            record.record_identity,
            record.observed_locator,
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
                            "raw_eid": record.reference.raw_eid,
                            "semantic_integrity_expectation": "NOT_ESTABLISHED_FROM_CAPTURED_BYTES",
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
                        "LEGACY_EMBEDDING_EVIDENCE_AMBIGUOUS",
                        record.reason,
                        native_id_to_bytes(record.artifact_id),
                    ),
                )
        elif existing[1] != record.admission_status:
            raise SubstrateRevisionConflict("legacy embedding evidence has a different admission result")
        result = self._recorded_result(tx.operation_id, manifest, record)
        if result is None:
            raise SubstrateInvariantViolation("legacy representation uncertainty result was not durable")
        return result

    def _resolve_imported_source(
        self,
        tx: SubstrateTx,
        source_namespace_id: bytes,
        reference: LegacyEmbeddingReference,
    ) -> tuple[tuple[bytes, bytes, int] | None, str | None]:
        rows = tx.execute(
            """
            SELECT a.object_id,r.object_revision_id,r.revision_ordinal
            FROM legacy_object_aliases a
            JOIN objects o ON o.object_id=a.object_id
            JOIN object_revisions r ON r.object_id=o.object_id
            JOIN semantic_transitions t ON t.transition_id=o.creating_transition_id
            WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID' AND a.alias_value=?
              AND r.lineage_kind='LEGACY_PREDECESSOR_UNKNOWN' AND r.revision_ordinal=1
              AND r.payload_format='TEXT' AND r.payload_text=?
              AND t.transition_kind='LEGACY_OBJECT_ADMISSION' AND t.origin_kind='LEGACY_ADMISSION'
            """,
            (source_namespace_id, str(reference.raw_eid), reference.raw_node_text),
        ).fetchall()
        if len(rows) != 1:
            return None, (
                "node EID does not resolve to exactly one imported object revision with the same "
                "captured node evidence"
            )
        return (rows[0][0], rows[0][1], rows[0][2]), None

    def _recorded_result(
        self,
        operation_id: bytes,
        manifest: LegacySnapshotManifest,
        item: LegacyEmbeddingCandidate | LegacyEmbeddingAdmissionRecord,
    ) -> LegacyRepresentationAdmissionResult | None:
        if isinstance(item, LegacyEmbeddingCandidate):
            artifact_id = item.map_artifact_id
            record_identity = _map_record_identity(item.map_entry.line_ordinal)
        else:
            artifact_id = item.artifact_id
            record_identity = item.record_identity
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
                native_id_to_bytes(artifact_id),
                record_identity,
            ),
        ).fetchone()
        reference = item.reference
        if record is None:
            return None
        if record[1] != "ADMITTED":
            return LegacyRepresentationAdmissionResult(
                reference.legacy_snapshot_id,
                reference.node_artifact_id,
                reference.line_ordinal,
                reference.raw_eid,
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
              AND o.output_role='LEGACY_REPRESENTATION_ADMISSION'
              AND e.representation_id=o.representation_id
              AND e.readiness='UNKNOWN' AND e.operational_disposition='RECONCILIATION_REQUIRED'
              AND a.admission_record_id=? AND a.admission_status='ADMITTED'
            """,
            (operation_id, record[0]),
        ).fetchone()
        if row is None:
            return None
        return LegacyRepresentationAdmissionResult(
            reference.legacy_snapshot_id,
            reference.node_artifact_id,
            reference.line_ordinal,
            reference.raw_eid,
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


def _extract_embedding_evidence(
    snapshot_root: str | Path,
    manifest: LegacySnapshotManifest,
    artifacts: dict[str, LegacyArtifact],
) -> tuple[tuple[LegacyEmbeddingCandidate, ...], tuple[LegacyEmbeddingAdmissionRecord, ...]]:
    nodes_artifact = _exact_artifact(artifacts, "nodes.jsonl", "LEGACY_CORE_NODE_EVIDENCE")
    references = _node_embedding_references(snapshot_root, manifest.legacy_snapshot_id, nodes_artifact)
    if not references:
        return (), ()
    manifest_artifact = artifacts.get("embeddings/manifest.json")
    if manifest_artifact is None or manifest_artifact.artifact_class != "LEGACY_EMBEDDING_MANIFEST_EVIDENCE":
        return (), tuple(_uncertain_from_reference(reference, "embedding manifest evidence is absent", nodes_artifact.artifact_id) for reference in references)
    metadata, manifest_reason = _embedding_manifest_metadata(snapshot_root, manifest_artifact)
    if metadata is None:
        return (), tuple(_uncertain_from_reference(reference, manifest_reason, nodes_artifact.artifact_id) for reference in references)
    candidates: list[LegacyEmbeddingCandidate] = []
    records: list[LegacyEmbeddingAdmissionRecord] = []
    map_cache: dict[str, tuple[_MapEntry, ...] | str] = {}
    for reference in references:
        result = _candidate_from_reference(
            snapshot_root, reference, artifacts, metadata, map_cache
        )
        if isinstance(result, LegacyEmbeddingCandidate):
            candidates.append(result)
        else:
            records.append(result)
    return tuple(candidates), tuple(records)


def _candidate_from_reference(
    snapshot_root: str | Path,
    reference: LegacyEmbeddingReference,
    artifacts: dict[str, LegacyArtifact],
    metadata: dict[str, Any],
    map_cache: dict[str, tuple[_MapEntry, ...] | str],
) -> LegacyEmbeddingCandidate | LegacyEmbeddingAdmissionRecord:
    if metadata["encoding_id"] != _SUPPORTED_ENCODING:
        return _uncertain_from_reference(reference, "embedding manifest encoding is unsupported", reference.node_artifact_id)
    if (reference.shard_locator, reference.map_locator) not in metadata["shards"]:
        return _uncertain_from_reference(reference, "node embedding reference is absent from the embedding manifest", reference.node_artifact_id)
    map_artifact = artifacts.get(reference.map_locator)
    shard_artifact = artifacts.get(reference.shard_locator)
    if map_artifact is None or map_artifact.artifact_class != "LEGACY_EMBEDDING_MAP_EVIDENCE":
        return _uncertain_from_reference(reference, "referenced embedding map evidence is absent", reference.node_artifact_id)
    if shard_artifact is None or shard_artifact.artifact_class != "LEGACY_EMBEDDING_NUMERIC_SHARD_EVIDENCE":
        return _uncertain_from_reference(reference, "referenced embedding shard evidence is absent", reference.node_artifact_id)
    cached = map_cache.get(reference.map_locator)
    if cached is None:
        cached = _map_entries(snapshot_root, map_artifact)
        map_cache[reference.map_locator] = cached
    if isinstance(cached, str):
        return _uncertain_from_reference(reference, cached, map_artifact.artifact_id)
    same_eid = [entry for entry in cached if entry.raw_eid == reference.raw_eid]
    same_row = [entry for entry in cached if entry.shard_locator == reference.shard_locator and entry.row_ordinal == reference.row_ordinal]
    exact = [entry for entry in same_eid if entry in same_row]
    if len(same_eid) != 1 or len(same_row) != 1 or len(exact) != 1:
        return _uncertain_from_reference(reference, "embedding map is duplicate, conflicting, or does not agree with the node reference", map_artifact.artifact_id)
    entry = exact[0]
    if entry.dimension is not None and entry.dimension != reference.dimension:
        return _uncertain_from_reference(reference, "embedding map dimension disagrees with the node reference", map_artifact.artifact_id)
    if metadata["dimension"] != reference.dimension:
        return _uncertain_from_reference(reference, "embedding manifest dimension disagrees with the node reference", map_artifact.artifact_id)
    if reference.dtype is not None and reference.dtype != metadata["dtype"]:
        return _uncertain_from_reference(reference, "node embedding dtype disagrees with the embedding manifest", map_artifact.artifact_id)
    payload, reason = _npy_row_bytes(
        snapshot_root,
        shard_artifact,
        entry.row_ordinal,
        metadata["dtype"],
        reference.dimension,
    )
    if payload is None:
        return _uncertain_from_reference(reference, reason, shard_artifact.artifact_id)
    return LegacyEmbeddingCandidate(
        reference,
        entry,
        map_artifact.artifact_id,
        shard_artifact.artifact_id,
        metadata["encoding_id"],
        metadata["dtype"],
        metadata["derivation_contract_version"],
        metadata["known_derivation_metadata"],
        payload,
    )


def _node_embedding_references(
    snapshot_root: str | Path, snapshot_id: UUID, artifact: LegacyArtifact
) -> tuple[LegacyEmbeddingReference, ...]:
    root = Path(snapshot_root).expanduser().resolve()
    path = (root / artifact.observed_relative_locator).resolve()
    if root not in path.parents:
        raise SubstrateInvariantViolation("node evidence locator escapes snapshot root")
    references: list[LegacyEmbeddingReference] = []
    with path.open("rb") as stream:
        for line_ordinal, raw_row in enumerate(stream, start=1):
            try:
                text = raw_row.decode("utf-8")
                value = json.loads(text)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not isinstance(value, dict) or "embedding_ref" not in value:
                continue
            raw_eid = value.get("eid")
            reference = value.get("embedding_ref")
            if not isinstance(raw_eid, int) or isinstance(raw_eid, bool) or raw_eid < 0 or not isinstance(reference, dict):
                continue
            parsed = _parse_node_reference(snapshot_id, artifact.artifact_id, line_ordinal, raw_eid, text, reference)
            if parsed is not None:
                references.append(parsed)
    return tuple(references)


def _parse_node_reference(
    snapshot_id: UUID,
    artifact_id: UUID,
    line_ordinal: int,
    raw_eid: int,
    raw_node_text: str,
    value: dict[str, Any],
) -> LegacyEmbeddingReference | None:
    map_locator, shard_locator = value.get("map"), value.get("shard")
    row_ordinal, dimension = value.get("row"), value.get("dimension")
    dtype = value.get("dtype")
    if (
        not isinstance(map_locator, str)
        or not map_locator
        or not isinstance(shard_locator, str)
        or not shard_locator
        or not isinstance(row_ordinal, int)
        or isinstance(row_ordinal, bool)
        or row_ordinal < 0
        or not isinstance(dimension, int)
        or isinstance(dimension, bool)
        or dimension <= 0
        or (dtype is not None and (not isinstance(dtype, str) or not dtype))
    ):
        return None
    return LegacyEmbeddingReference(
        snapshot_id,
        artifact_id,
        line_ordinal,
        raw_eid,
        raw_node_text,
        map_locator,
        shard_locator,
        row_ordinal,
        dimension,
        dtype,
    )


def _embedding_manifest_metadata(
    snapshot_root: str | Path, artifact: LegacyArtifact
) -> tuple[dict[str, Any] | None, str]:
    try:
        raw = _load_json(snapshot_root, artifact)
    except ValueError as exc:
        return None, str(exc)
    if not isinstance(raw, dict):
        return None, "embedding manifest is not an object"
    encoding_id, dtype, dimension = raw.get("encoding_id"), raw.get("dtype"), raw.get("dimension")
    if (
        not isinstance(encoding_id, str)
        or not encoding_id
        or not isinstance(dtype, str)
        or not dtype
        or not isinstance(dimension, int)
        or isinstance(dimension, bool)
        or dimension <= 0
    ):
        return None, "embedding manifest lacks supported encoding, dtype, or dimension evidence"
    shards = raw.get("shards")
    if not isinstance(shards, list):
        return None, "embedding manifest lacks explicit shard/map entries"
    pairs: set[tuple[str, str]] = set()
    for entry in shards:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not entry["path"] or not isinstance(entry.get("map"), str) or not entry["map"]:
            return None, "embedding manifest shard/map entry is malformed"
        pairs.add((entry["path"], entry["map"]))
    if len(pairs) != len(shards):
        return None, "embedding manifest repeats a shard/map entry"
    contract = raw.get("derivation_contract_version", LEGACY_UNSPECIFIED_DERIVATION_CONTRACT)
    if not isinstance(contract, str) or not contract:
        return None, "embedding manifest derivation contract value is malformed"
    known = {
        key: value
        for key, value in (("provider", raw.get("provider")), ("model", raw.get("model")))
        if isinstance(value, str) and value
    }
    return {
        "encoding_id": encoding_id,
        "dtype": dtype,
        "dimension": dimension,
        "shards": pairs,
        "derivation_contract_version": contract,
        "known_derivation_metadata": known,
    }, ""


def _map_entries(snapshot_root: str | Path, artifact: LegacyArtifact) -> tuple[_MapEntry, ...] | str:
    root = Path(snapshot_root).expanduser().resolve()
    path = (root / artifact.observed_relative_locator).resolve()
    if root not in path.parents:
        return "embedding map locator escapes snapshot root"
    entries: list[_MapEntry] = []
    try:
        with path.open("rb") as stream:
            for line_ordinal, raw_row in enumerate(stream, start=1):
                value = json.loads(raw_row.decode("utf-8"))
                if not isinstance(value, dict):
                    return "embedding map row is not an object"
                raw_eid, shard_locator, row_ordinal = value.get("eid"), value.get("shard"), value.get("row")
                dimension = value.get("dimension")
                if (
                    not isinstance(raw_eid, int)
                    or isinstance(raw_eid, bool)
                    or raw_eid < 0
                    or not isinstance(shard_locator, str)
                    or not shard_locator
                    or not isinstance(row_ordinal, int)
                    or isinstance(row_ordinal, bool)
                    or row_ordinal < 0
                    or (dimension is not None and (not isinstance(dimension, int) or isinstance(dimension, bool) or dimension <= 0))
                ):
                    return "embedding map row lacks valid EID, shard, row, or dimension evidence"
                entries.append(_MapEntry(artifact.artifact_id, line_ordinal, raw_eid, shard_locator, row_ordinal, dimension))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "embedding map is not valid UTF-8 JSONL evidence"
    return tuple(entries)


def _npy_row_bytes(
    snapshot_root: str | Path,
    artifact: LegacyArtifact,
    row_ordinal: int,
    dtype: str,
    dimension: int,
) -> tuple[bytes | None, str]:
    try:
        import numpy as np
    except ImportError:
        return None, "NumPy is required to read captured NPY evidence"
    root = Path(snapshot_root).expanduser().resolve()
    path = (root / artifact.observed_relative_locator).resolve()
    if root not in path.parents:
        return None, "embedding shard locator escapes snapshot root"
    try:
        values = np.load(path, allow_pickle=False)
    except (OSError, ValueError):
        return None, "embedding shard is not a readable non-object NPY array"
    if values.ndim != 2:
        return None, "embedding shard is not a two-dimensional row matrix"
    if str(values.dtype) != dtype:
        return None, "embedding shard dtype disagrees with the embedding manifest"
    if values.shape[1] != dimension:
        return None, "embedding shard dimension disagrees with the embedding evidence"
    if row_ordinal >= values.shape[0]:
        return None, "embedding map row is outside the captured shard bounds"
    return bytes(values[row_ordinal].tobytes(order="C")), ""


def _uncertain_from_reference(
    reference: LegacyEmbeddingReference,
    reason: str,
    artifact_id: UUID,
) -> LegacyEmbeddingAdmissionRecord:
    return LegacyEmbeddingAdmissionRecord(
        reference,
        "QUARANTINED",
        reason,
        artifact_id,
        _node_record_identity(reference.line_ordinal),
        _node_record_locator(reference.line_ordinal),
    )


def _load_json(snapshot_root: str | Path, artifact: LegacyArtifact) -> Any:
    root = Path(snapshot_root).expanduser().resolve()
    path = (root / artifact.observed_relative_locator).resolve()
    if root not in path.parents:
        raise ValueError("embedding manifest locator escapes snapshot root")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("embedding manifest is not valid UTF-8 JSON evidence") from exc


def _artifacts_by_locator(manifest: LegacySnapshotManifest) -> dict[str, LegacyArtifact]:
    return {artifact.observed_relative_locator: artifact for artifact in manifest.artifacts}


def _exact_artifact(
    artifacts: dict[str, LegacyArtifact], locator: str, expected_class: str
) -> LegacyArtifact:
    artifact = artifacts.get(locator)
    if artifact is None or artifact.artifact_class != expected_class:
        raise SubstrateRevisionConflict(f"snapshot lacks required {locator} evidence artifact")
    return artifact


def _node_record_identity(line_ordinal: int) -> str:
    return f"TMS-LEGACY-EMBEDDING-NODE-LINE-1:{line_ordinal}"


def _node_record_locator(line_ordinal: int) -> str:
    return f"nodes.jsonl#line:{line_ordinal}"


def _map_record_identity(line_ordinal: int) -> str:
    return f"TMS-LEGACY-EMBEDDING-MAP-LINE-1:{line_ordinal}"


def _map_record_locator(line_ordinal: int) -> str:
    return f"embedding.map.jsonl#line:{line_ordinal}"


def _candidate_intent(candidate: LegacyEmbeddingCandidate) -> str:
    reference = candidate.reference
    return canonical_intent_text(
        {
            "kind": "ADMIT_LEGACY_EMBEDDING_EVIDENCE",
            "legacy_snapshot_id": str(reference.legacy_snapshot_id),
            "node_artifact_id": str(reference.node_artifact_id),
            "node_record_identity": _node_record_identity(reference.line_ordinal),
            "map_artifact_id": str(candidate.map_artifact_id),
            "map_record_identity": _map_record_identity(candidate.map_entry.line_ordinal),
            "shard_artifact_id": str(candidate.shard_artifact_id),
            "shard_row": reference.row_ordinal,
        }
    )


def _record_intent(record: LegacyEmbeddingAdmissionRecord) -> str:
    return canonical_intent_text(
        {
            "kind": "RECORD_LEGACY_EMBEDDING_ADMISSION_" + record.admission_status,
            "legacy_snapshot_id": str(record.reference.legacy_snapshot_id),
            "artifact_id": str(record.artifact_id),
            "record_identity": record.record_identity,
            "reason": record.reason,
        }
    )


def _new() -> bytes:
    return native_id_to_bytes(generate_native_id())
