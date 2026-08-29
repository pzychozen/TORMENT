"""Conservative admission of frozen legacy identity and character definitions.

Only the two current durable definition files are in scope: workspace-agent
``identity.json`` and workspace seed ``seed.json``.  They are admitted as
generic native objects without any memory, motif, retrieval, or Character
runtime dependency.  ``character_state.json`` remains captured evidence: it
is a materialized drift snapshot, not a primary identity definition.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
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


LEGACY_AGENT_IDENTITY_OBJECT_KIND: Final[str] = "LEGACY_AGENT_IDENTITY"
LEGACY_CHARACTER_DEFINITION_OBJECT_KIND: Final[str] = "LEGACY_CHARACTER_DEFINITION"
LEGACY_IDENTITY_ALIAS_KIND: Final[str] = "AGENT_IDENTITY"
LEGACY_CHARACTER_SEED_ALIAS_KIND: Final[str] = "CHARACTER_SEED_ID"
_ADMISSION_BATCH_IDENTITY: Final[str] = "TMS-LEGACY-IDENTITY-ADMISSION-7F3C"


@dataclass(frozen=True)
class LegacyIdentityDefinitionCandidate:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    observed_relative_locator: str
    object_kind: str
    alias_kind: str
    alias_value: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class LegacyIdentityDefinitionRecord:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    observed_relative_locator: str
    definition_kind: str
    admission_status: str
    reason: str


@dataclass(frozen=True)
class LegacyIdentityAdmissionResult:
    legacy_snapshot_id: UUID
    legacy_artifact_id: UUID
    observed_relative_locator: str
    definition_kind: str
    admission_status: str
    admission_record_id: UUID
    operation_id: UUID
    object_id: UUID | None = None
    revision_id: UUID | None = None
    transition_id: UUID | None = None


@dataclass(frozen=True)
class LegacyIdentityAdmissionRun:
    legacy_snapshot_id: UUID
    results: tuple[LegacyIdentityAdmissionResult, ...]


class NativeLegacyIdentityAdmissionService:
    """Admit only verified primary identity/character-definition evidence."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection)
        self._connection = connection

    def admit_identity_definitions(
        self,
        *,
        snapshot_root: str | Path,
        manifest_path: str | Path,
        idempotency_namespace_id: UUID,
        object_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyIdentityAdmissionRun:
        """Admit ``identity.json`` and ``seed.json`` without memory dependencies."""
        self._require_admission_namespaces(
            idempotency_namespace_id, object_identity_namespace_id, unknown_semantic_scope_id
        )
        manifest = load_snapshot_manifest(manifest_path)
        inventory_snapshot(
            self._connection, snapshot_root=snapshot_root, manifest_path=manifest_path
        )
        candidates, records = _extract_identity_definition_evidence(snapshot_root, manifest)
        results: list[LegacyIdentityAdmissionResult] = []
        for item in sorted((*candidates, *records), key=lambda value: value.observed_relative_locator):
            if isinstance(item, LegacyIdentityDefinitionCandidate):
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
                results.append(self._record_unknown(manifest, item, idempotency_namespace_id))
        return LegacyIdentityAdmissionRun(manifest.legacy_snapshot_id, tuple(results))

    def resolve_legacy_identity_alias(
        self,
        *,
        legacy_source_namespace_id: UUID,
        alias_kind: str,
        alias_value: str,
    ) -> UUID:
        """Resolve only a declared, source-namespaced identity alias."""
        if alias_kind not in {LEGACY_IDENTITY_ALIAS_KIND, LEGACY_CHARACTER_SEED_ALIAS_KIND}:
            raise ValueError("legacy identity alias kind is not supported")
        if not isinstance(alias_value, str) or not alias_value:
            raise ValueError("legacy identity alias value must be non-empty text")
        row = self._connection.execute(
            """
            SELECT object_id FROM legacy_object_aliases
            WHERE legacy_source_namespace_id=? AND alias_kind=? AND alias_value=?
            """,
            (native_id_to_bytes(legacy_source_namespace_id), alias_kind, alias_value),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("namespaced legacy identity alias was not found")
        return native_id_from_bytes(row[0])

    def _admit_candidate(
        self,
        manifest: LegacySnapshotManifest,
        candidate: LegacyIdentityDefinitionCandidate,
        idempotency_namespace_id: UUID,
        object_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyIdentityAdmissionResult:
        intent = _candidate_intent(candidate)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "ADMIT_LEGACY_IDENTITY_DEFINITION",
            intent,
            lambda operation_id: self._recorded_result(operation_id, manifest, candidate),
            lambda tx: self._publish_candidate(
                tx, manifest, candidate, object_identity_namespace_id, unknown_semantic_scope_id
            ),
        )

    def _record_unknown(
        self,
        manifest: LegacySnapshotManifest,
        record: LegacyIdentityDefinitionRecord,
        idempotency_namespace_id: UUID,
    ) -> LegacyIdentityAdmissionResult:
        intent = _record_intent(record)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            _evidence_idempotency_key(intent),
            "RECORD_LEGACY_IDENTITY_ADMISSION_UNKNOWN",
            intent,
            lambda operation_id: self._recorded_result(operation_id, manifest, record),
            lambda tx: self._publish_unknown(tx, manifest, record),
        )

    def _publish_candidate(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        candidate: LegacyIdentityDefinitionCandidate,
        object_identity_namespace_id: UUID,
        unknown_semantic_scope_id: UUID,
    ) -> LegacyIdentityAdmissionResult:
        snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
        source_namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
        artifact_id = native_id_to_bytes(candidate.legacy_artifact_id)
        batch_id = _ensure_admission_batch(tx, snapshot_id, _ADMISSION_BATCH_IDENTITY)
        artifact_record_id = _ensure_artifact_record(
            tx,
            artifact_id,
            _record_identity(candidate.observed_relative_locator),
            candidate.observed_relative_locator,
        )
        if _admission_record_for_artifact_record(tx, batch_id, artifact_record_id) is not None:
            raise SubstrateRevisionConflict("legacy identity definition evidence already has an admission result")
        if tx.execute(
            """
            SELECT object_id FROM legacy_object_aliases
            WHERE legacy_source_namespace_id=? AND alias_kind=? AND alias_value=?
            """,
            (source_namespace_id, candidate.alias_kind, candidate.alias_value),
        ).fetchone() is not None:
            raise SubstrateRevisionConflict("declared legacy identity alias is already admitted for this source namespace")

        object_id, revision_id, transition_id, admission_record_id = _new(), _new(), _new(), _new()
        now_ns = time.time_ns()
        payload = canonical_intent_text(candidate.payload)
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
                candidate.object_kind,
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
                      'UNKNOWN','NOT_APPLICABLE',NULL,'JSON',?,?)
            """,
            (
                revision_id,
                object_id,
                native_id_to_bytes(unknown_semantic_scope_id),
                payload,
                now_ns,
            ),
        )
        tx.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
            (source_namespace_id, candidate.alias_kind, candidate.alias_value, object_id),
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
                        "definition_kind": _definition_kind(candidate.object_kind),
                        "original_provenance": "UNKNOWN",
                        "authority_category": "NOT_APPLICABLE",
                        "payload_role": "FLEXIBLE_CHARACTER_DEFINITION_CONTENT",
                        "memory_dependency": "NONE",
                    }
                ),
            ),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,?)",
            (transition_id, tx.operation_id, "LEGACY_IDENTITY_ADMISSION", "LEGACY_ADMISSION", now_ns),
        )
        tx.execute(
            "INSERT INTO object_revision_effects VALUES (?,?,?,1)",
            (transition_id, object_id, revision_id),
        )
        tx.execute("INSERT INTO legacy_admission_effects VALUES (?,?)", (transition_id, admission_record_id))
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,object_id,
                object_revision_id,object_revision_ordinal
            ) VALUES (?,?,?,'OBJECT',?,?,1)
            """,
            (tx.operation_id, 0, "LEGACY_IDENTITY_ADMISSION", object_id, revision_id),
        )
        tx.transitions.append(transition_id)
        tx.published.append((object_id, revision_id, 1))
        tx.legacy_identity_admitted.append(
            (
                object_id,
                revision_id,
                1,
                admission_record_id,
                transition_id,
                snapshot_id,
                artifact_id,
                artifact_record_id,
                candidate.object_kind,
                candidate.alias_kind,
                candidate.alias_value,
            )
        )
        result = self._recorded_result(tx.operation_id, manifest, candidate)
        if result is None:
            raise SubstrateInvariantViolation("legacy identity admission result was not durably published")
        return result

    def _publish_unknown(
        self,
        tx: SubstrateTx,
        manifest: LegacySnapshotManifest,
        record: LegacyIdentityDefinitionRecord,
    ) -> LegacyIdentityAdmissionResult:
        batch_id = _ensure_admission_batch(
            tx, native_id_to_bytes(manifest.legacy_snapshot_id), _ADMISSION_BATCH_IDENTITY
        )
        artifact_record_id = _ensure_artifact_record(
            tx,
            native_id_to_bytes(record.legacy_artifact_id),
            _record_identity(record.observed_relative_locator),
            record.observed_relative_locator,
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
                            "definition_kind": record.definition_kind,
                            "reason": record.reason,
                            "original_provenance": "UNKNOWN",
                        }
                    ),
                ),
            )
        elif existing[1] != "UNKNOWN":
            raise SubstrateRevisionConflict("legacy identity definition evidence has a different admission result")
        result = self._recorded_result(tx.operation_id, manifest, record)
        if result is None:
            raise SubstrateInvariantViolation("legacy identity admission uncertainty result was not durable")
        return result

    def _recorded_result(
        self,
        operation_id: bytes,
        manifest: LegacySnapshotManifest,
        item: LegacyIdentityDefinitionCandidate | LegacyIdentityDefinitionRecord,
    ) -> LegacyIdentityAdmissionResult | None:
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
                _record_identity(item.observed_relative_locator),
            ),
        ).fetchone()
        if record is None:
            return None
        definition_kind = (
            _definition_kind(item.object_kind)
            if isinstance(item, LegacyIdentityDefinitionCandidate)
            else item.definition_kind
        )
        if record[1] != "ADMITTED":
            return LegacyIdentityAdmissionResult(
                item.legacy_snapshot_id,
                item.legacy_artifact_id,
                item.observed_relative_locator,
                definition_kind,
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
              AND o.output_role='LEGACY_IDENTITY_ADMISSION'
              AND e.object_id=o.object_id AND e.object_revision_id=o.object_revision_id
              AND e.object_revision_ordinal=o.object_revision_ordinal
              AND a.admission_record_id=? AND a.admission_status='ADMITTED'
            """,
            (operation_id, record[0]),
        ).fetchone()
        if row is None:
            return None
        return LegacyIdentityAdmissionResult(
            item.legacy_snapshot_id,
            item.legacy_artifact_id,
            item.observed_relative_locator,
            definition_kind,
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


def _extract_identity_definition_evidence(
    snapshot_root: str | Path, manifest: LegacySnapshotManifest
) -> tuple[tuple[LegacyIdentityDefinitionCandidate, ...], tuple[LegacyIdentityDefinitionRecord, ...]]:
    candidates: list[LegacyIdentityDefinitionCandidate] = []
    records: list[LegacyIdentityDefinitionRecord] = []
    root = Path(snapshot_root).expanduser().resolve()
    for artifact in manifest.artifacts:
        kind = _artifact_definition_kind(artifact.observed_relative_locator)
        if kind is None:
            continue
        try:
            payload = _load_json_object(root, artifact)
            candidate = _candidate_from_payload(manifest, artifact, kind, payload)
        except ValueError as exc:
            records.append(
                LegacyIdentityDefinitionRecord(
                    manifest.legacy_snapshot_id,
                    artifact.artifact_id,
                    artifact.observed_relative_locator,
                    kind,
                    "UNKNOWN",
                    str(exc),
                )
            )
        else:
            candidates.append(candidate)
    return tuple(candidates), tuple(records)


def _artifact_definition_kind(locator: str) -> str | None:
    path = PurePosixPath(locator)
    parts = path.parts
    if (
        len(parts) == 5
        and parts[0] == "workspaces"
        and parts[2] == "agents"
        and path.name == "identity.json"
        and all(parts[index] for index in (1, 3))
    ):
        return "IDENTITY"
    if (
        len(parts) == 5
        and parts[0] == "workspaces"
        and parts[2] == "seeds"
        and path.name == "seed.json"
        and all(parts[index] for index in (1, 3))
    ):
        return "CHARACTER_DEFINITION"
    return None


def _load_json_object(root: Path, artifact: LegacyArtifact) -> dict[str, Any]:
    path = (root / artifact.observed_relative_locator).resolve()
    if root not in path.parents:
        raise ValueError("identity definition locator escapes snapshot root")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("definition is not valid UTF-8 JSON evidence") from exc
    if not isinstance(value, dict):
        raise ValueError("definition is not a JSON object")
    return value


def _candidate_from_payload(
    manifest: LegacySnapshotManifest,
    artifact: LegacyArtifact,
    definition_kind: str,
    payload: dict[str, Any],
) -> LegacyIdentityDefinitionCandidate:
    parts = PurePosixPath(artifact.observed_relative_locator).parts
    if definition_kind == "IDENTITY":
        workspace_id, agent_id = payload.get("workspace_id"), payload.get("agent_id")
        if not _nonempty_text(workspace_id) or not _nonempty_text(agent_id):
            raise ValueError("identity definition lacks declared workspace_id or agent_id")
        if workspace_id != parts[1] or agent_id != parts[3]:
            raise ValueError("identity definition declaration disagrees with its durable locator")
        if not isinstance(payload.get("seed"), dict) or not isinstance(payload.get("overlay"), dict):
            raise ValueError("identity definition lacks object-valued seed or overlay content")
        if not _nonnegative_int(payload.get("created_ts")) or not _nonnegative_int(payload.get("updated_ts")):
            raise ValueError("identity definition lacks non-negative durable timestamps")
        return LegacyIdentityDefinitionCandidate(
            manifest.legacy_snapshot_id,
            artifact.artifact_id,
            artifact.observed_relative_locator,
            LEGACY_AGENT_IDENTITY_OBJECT_KIND,
            LEGACY_IDENTITY_ALIAS_KIND,
            canonical_intent_text({"workspace_id": workspace_id, "agent_id": agent_id}),
            payload,
        )
    seed_id, character_name, seed_text = payload.get("seed_id"), payload.get("character_name"), payload.get("seed_text")
    if not _nonempty_text(seed_id) or not isinstance(character_name, str) or not isinstance(seed_text, str):
        raise ValueError("character definition lacks durable seed_id, character_name, or seed_text")
    if seed_id != parts[3]:
        raise ValueError("character definition seed_id disagrees with its durable locator")
    return LegacyIdentityDefinitionCandidate(
        manifest.legacy_snapshot_id,
        artifact.artifact_id,
        artifact.observed_relative_locator,
        LEGACY_CHARACTER_DEFINITION_OBJECT_KIND,
        LEGACY_CHARACTER_SEED_ALIAS_KIND,
        seed_id,
        payload,
    )


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _record_identity(locator: str) -> str:
    return "TMS-LEGACY-IDENTITY-DEFINITION-1:" + locator


def _candidate_intent(candidate: LegacyIdentityDefinitionCandidate) -> str:
    return canonical_intent_text(
        {
            "kind": "ADMIT_LEGACY_IDENTITY_DEFINITION",
            "legacy_snapshot_id": str(candidate.legacy_snapshot_id),
            "legacy_artifact_id": str(candidate.legacy_artifact_id),
            "record_identity": _record_identity(candidate.observed_relative_locator),
            "object_kind": candidate.object_kind,
            "alias_kind": candidate.alias_kind,
            "alias_value": candidate.alias_value,
        }
    )


def _record_intent(record: LegacyIdentityDefinitionRecord) -> str:
    return canonical_intent_text(
        {
            "kind": "RECORD_LEGACY_IDENTITY_ADMISSION_UNKNOWN",
            "legacy_snapshot_id": str(record.legacy_snapshot_id),
            "legacy_artifact_id": str(record.legacy_artifact_id),
            "record_identity": _record_identity(record.observed_relative_locator),
            "reason": record.reason,
        }
    )


def _definition_kind(object_kind: str) -> str:
    if object_kind == LEGACY_AGENT_IDENTITY_OBJECT_KIND:
        return "IDENTITY"
    if object_kind == LEGACY_CHARACTER_DEFINITION_OBJECT_KIND:
        return "CHARACTER_DEFINITION"
    raise SubstrateInvariantViolation("identity admission object kind is not recognized")
