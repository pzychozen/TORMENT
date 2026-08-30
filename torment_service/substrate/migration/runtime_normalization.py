"""Evidence-bounded Phase 7G5B2 legacy-memory runtime normalization.

This is deliberately a one-object, one-successor service.  It converts a
verified 7F ``LEGACY_PREDECESSOR_UNKNOWN`` core-node admission into one normal
native R2 only when the snapshot, source namespace, R1 evidence, runtime
order, scope plan, governance, provenance, and lifecycle facts all agree.
It is not a generic object transition API and it does not create a vector.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import UUID

import numpy as np

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.kernel.seed_entities import _as3
from torment_service.lifecycle import (
    LifecycleStatus,
    detect_lifecycle_legacy_marker_disagreement,
    validate_lifecycle_envelope,
)
from torment_service.provenance_v1 import ProvenanceV1

from ..canonical_intent import canonical_intent_text
from ..errors import SubstrateIdempotencyConflict, SubstrateInvariantViolation
from ..fabric_translation import translate_governance_flags, translate_provenance_v1
from ..ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from ..object_revision_governance import (
    NativeMemoryGovernanceFacts,
    _insert_published_governance_for_qualification,
)
from ..objects import SubstrateTx, execute_semantic
from ..provenance import NativeProvenanceRecord
from ..schema import CORE_ROLE_STAGING, SCHEMA_MAJOR, SCHEMA_MINOR, require_current_schema
from .admission import _extract_nodes, _nodes_artifact
from .runtime_readiness import MigrationRuntimeScopePlan
from .snapshot import LegacySnapshotManifest, load_snapshot_manifest, verify_snapshot


_OPERATION_KIND = "MIGRATION_RUNTIME_NORMALIZATION"
_TRANSITION_KIND = "MIGRATION_RUNTIME_NORMALIZATION"
_OUTPUT_ROLE = "MIGRATION_RUNTIME_NORMALIZATION"
_NORMALIZATION_CONTRACT = "TMS-MIGRATION-RUNTIME-NORMALIZATION-7G5B2/1"
_MEMORY_OBJECT_KIND = "LEGACY_CORE_NODE"
_PREPARED = object()


class MigrationRuntimeNormalizationRefused(SubstrateInvariantViolation):
    """A fail-closed B2 eligibility refusal with a stable reason code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class MigrationRuntimeNormalizationRequest:
    """Caller-controlled identity/evidence references, never normalized facts."""

    snapshot_root: str | Path
    manifest_path: str | Path
    legacy_snapshot_id: UUID
    legacy_source_namespace_id: UUID
    expected_native_core_id: UUID
    eid: int
    expected_revision_id: UUID
    scope_plans: tuple[MigrationRuntimeScopePlan, ...]
    idempotency_namespace_id: UUID
    idempotency_key: str

    def __post_init__(self) -> None:
        for name in (
            "legacy_snapshot_id", "legacy_source_namespace_id",
            "expected_native_core_id", "expected_revision_id",
            "idempotency_namespace_id",
        ):
            if not isinstance(getattr(self, name), UUID):
                raise ValueError(f"{name} must be a UUID")
        if not isinstance(self.eid, int) or isinstance(self.eid, bool) or self.eid < 0:
            raise ValueError("eid must be a non-negative integer")
        if not isinstance(self.scope_plans, tuple) or any(
            not isinstance(plan, MigrationRuntimeScopePlan) for plan in self.scope_plans
        ):
            raise ValueError("scope_plans must be a tuple of MigrationRuntimeScopePlan values")
        if not isinstance(self.idempotency_key, str) or not self.idempotency_key:
            raise ValueError("idempotency_key must be a non-empty string")
        if not isinstance(self.snapshot_root, (str, Path)) or not str(self.snapshot_root).strip():
            raise ValueError("snapshot_root is required")
        if not isinstance(self.manifest_path, (str, Path)) or not str(self.manifest_path).strip():
            raise ValueError("manifest_path is required")


@dataclass(frozen=True, init=False)
class PreparedLegacyMemoryNormalization:
    """Internally prepared, immutable facts for exactly one R1 -> R2 operation."""

    legacy_snapshot_id: UUID
    legacy_source_namespace_id: UUID
    native_core_id: UUID
    object_id: UUID
    eid: int
    expected_revision_id: UUID
    expected_revision_ordinal: int
    runtime_order_ordinal: int
    scope_plan_digest: str
    target_semantic_scope_id: UUID
    identity_namespace_id: UUID
    payload: dict[str, Any]
    payload_json: str
    payload_digest: str
    governance: NativeMemoryGovernanceFacts
    provenance: NativeProvenanceRecord
    lifecycle: LifecycleStatus
    authority_category: str
    _marker: object = field(repr=False, compare=False)

    def __init__(
        self,
        *,
        legacy_snapshot_id: UUID,
        legacy_source_namespace_id: UUID,
        native_core_id: UUID,
        object_id: UUID,
        eid: int,
        expected_revision_id: UUID,
        expected_revision_ordinal: int,
        runtime_order_ordinal: int,
        scope_plan_digest: str,
        target_semantic_scope_id: UUID,
        identity_namespace_id: UUID,
        payload: dict[str, Any],
        payload_json: str,
        payload_digest: str,
        governance: NativeMemoryGovernanceFacts,
        provenance: NativeProvenanceRecord,
        lifecycle: LifecycleStatus,
        authority_category: str,
        _marker: object,
    ) -> None:
        if _marker is not _PREPARED:
            raise ValueError("normalization plans must be prepared from verified legacy evidence")
        for name, value in locals().items():
            if name != "self":
                object.__setattr__(self, name, value)


@dataclass(frozen=True)
class MigrationRuntimeNormalizationResult:
    """The one actual R2 publication and its immutable provenance child."""

    object_id: UUID
    eid: int
    predecessor_revision_id: UUID
    predecessor_revision_ordinal: int
    revision_id: UUID
    revision_ordinal: int
    runtime_order_ordinal: int
    provenance_id: UUID
    transition_id: UUID
    operation_id: UUID
    payload_digest: str


class NativeMigrationRuntimeNormalizationService:
    """Narrow B2 writer; it never accepts caller-composed object semantics."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("normalization requires an already-open sqlite connection")
        require_current_schema(connection)
        self._connection = connection

    def normalize_legacy_core_memory(
        self,
        request: MigrationRuntimeNormalizationRequest,
        *,
        _test_fail_after_provenance: bool = False,
        _test_lose_response_after_commit: bool = False,
    ) -> MigrationRuntimeNormalizationResult:
        """Publish/recover exactly one evidence-derived R2.

        The two underscored switches are rollback/response-loss qualification
        seams.  They are intentionally not semantic inputs and have no normal
        caller use.
        """
        if not isinstance(request, MigrationRuntimeNormalizationRequest):
            raise ValueError("a MigrationRuntimeNormalizationRequest is required")
        self._reject_changed_retry_contract(request)
        plan = self._prepare(request, require_current=False)
        result = execute_semantic(
            self._connection,
            request.idempotency_namespace_id,
            request.idempotency_key,
            _OPERATION_KIND,
            _intent(request, plan),
            self._result_for_operation,
            lambda tx: self._commit(
                tx, request, plan, _test_fail_after_provenance=_test_fail_after_provenance,
            ),
        )
        if _test_lose_response_after_commit:
            raise RuntimeError("forced response loss after committed normalization")
        return result

    def _reject_changed_retry_contract(self, request: MigrationRuntimeNormalizationRequest) -> None:
        row = self._connection.execute(
            "SELECT canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), request.idempotency_key),
        ).fetchone()
        if row is None:
            return
        try:
            stored = json.loads(row[0])
        except (TypeError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("stored B2 normalization intent is malformed") from exc
        if not isinstance(stored, dict) or stored.get("retry_contract") != _retry_contract(request):
            raise SubstrateIdempotencyConflict("idempotency intent differs")

    def _prepare(
        self,
        request: MigrationRuntimeNormalizationRequest,
        *,
        require_current: bool,
    ) -> PreparedLegacyMemoryNormalization:
        native_core_id, core_role = self._current_core_facts()
        if native_core_id != request.expected_native_core_id:
            raise MigrationRuntimeNormalizationRefused("B2_NATIVE_CORE_ID_MISMATCH")
        if core_role != CORE_ROLE_STAGING:
            raise MigrationRuntimeNormalizationRefused("B2_CORE_ROLE_NOT_STAGING")
        deployment = self._connection.execute(
            "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
        ).fetchall()
        if deployment != [("LEGACY_ACTIVE", None)]:
            raise MigrationRuntimeNormalizationRefused("B2_DEPLOYMENT_NOT_LEGACY_ACTIVE")

        manifest = load_snapshot_manifest(request.manifest_path)
        if manifest.legacy_snapshot_id != request.legacy_snapshot_id:
            raise MigrationRuntimeNormalizationRefused("B2_SNAPSHOT_ID_MISMATCH")
        if manifest.legacy_source_namespace_id != request.legacy_source_namespace_id:
            raise MigrationRuntimeNormalizationRefused("B2_SOURCE_NAMESPACE_MISMATCH")
        verify_snapshot(snapshot_root=request.snapshot_root, manifest=manifest)
        self._verify_persisted_snapshot(manifest)

        plan = _exact_scope_plan(request)
        self._verify_scope_plan_references(plan)
        if plan.idempotency_namespace_id != request.idempotency_namespace_id:
            raise MigrationRuntimeNormalizationRefused("B2_IDEMPOTENCY_NAMESPACE_MISMATCH")

        source = self._admitted_r1(request, manifest)
        if source["identity_namespace_id"] != plan.target_identity_namespace_id:
            raise MigrationRuntimeNormalizationRefused("B2_OBJECT_IDENTITY_NAMESPACE_MISMATCH")
        if require_current and (
            source["current_revision_id"] != request.expected_revision_id
            or source["current_revision_ordinal"] != 1
        ):
            raise MigrationRuntimeNormalizationRefused("B2_CURRENT_R1_REQUIRED")

        raw_row = self._verified_snapshot_row(request, manifest, source)
        payload = _normalised_runtime_payload(raw_row)
        _reject_conflicting_outer_evidence(raw_row, payload)
        governance = _governance_from_payload(payload)
        provenance = _provenance_from_payload(payload)
        lifecycle = _lifecycle_from_payload(payload)
        payload_json = canonical_intent_text(payload)
        return PreparedLegacyMemoryNormalization(
            legacy_snapshot_id=request.legacy_snapshot_id,
            legacy_source_namespace_id=request.legacy_source_namespace_id,
            native_core_id=native_core_id,
            object_id=source["object_id"],
            eid=request.eid,
            expected_revision_id=request.expected_revision_id,
            expected_revision_ordinal=1,
            runtime_order_ordinal=source["runtime_order_ordinal"],
            scope_plan_digest=_scope_plan_digest(request.scope_plans),
            target_semantic_scope_id=plan.target_semantic_scope_id,
            identity_namespace_id=source["identity_namespace_id"],
            payload=payload,
            payload_json=payload_json,
            payload_digest=hashlib.sha256(payload_json.encode("utf-8")).hexdigest(),
            governance=governance,
            provenance=provenance,
            lifecycle=lifecycle,
            authority_category="NOT_APPLICABLE",
            _marker=_PREPARED,
        )

    def _current_core_facts(self) -> tuple[UUID, str]:
        """Re-read core/deployment facts without invoking the schema gate in a tx."""
        if not self._connection.in_transaction:
            metadata = require_current_schema(self._connection)
            return native_id_from_bytes(metadata.core_id), metadata.core_role
        rows = self._connection.execute(
            "SELECT schema_major,schema_minor,core_id,core_role FROM core_metadata"
        ).fetchall()
        if len(rows) != 1 or rows[0][0:2] != (SCHEMA_MAJOR, SCHEMA_MINOR):
            raise MigrationRuntimeNormalizationRefused("B2_SCHEMA_NOT_CURRENT")
        return native_id_from_bytes(rows[0][2]), rows[0][3]

    def _verify_persisted_snapshot(self, manifest: LegacySnapshotManifest) -> None:
        row = self._connection.execute(
            "SELECT legacy_source_namespace_id FROM legacy_snapshots WHERE legacy_snapshot_id=?",
            (native_id_to_bytes(manifest.legacy_snapshot_id),),
        ).fetchall()
        if row != [(native_id_to_bytes(manifest.legacy_source_namespace_id),)]:
            raise MigrationRuntimeNormalizationRefused("B2_PERSISTED_SNAPSHOT_MISMATCH")
        artifact = _nodes_artifact(manifest)
        evidence = self._connection.execute(
            """SELECT legacy_snapshot_id,artifact_kind,observed_locator,digest_algorithm,digest_value
                 FROM legacy_artifacts WHERE legacy_artifact_id=?""",
            (native_id_to_bytes(artifact.artifact_id),),
        ).fetchall()
        expected = (
            native_id_to_bytes(manifest.legacy_snapshot_id), artifact.artifact_class,
            artifact.observed_relative_locator, artifact.digest_algorithm, bytes.fromhex(artifact.digest_hex),
        )
        if evidence != [expected]:
            raise MigrationRuntimeNormalizationRefused("B2_PERSISTED_ARTIFACT_MISMATCH")

    def _verify_scope_plan_references(self, plan: MigrationRuntimeScopePlan) -> None:
        checks = (
            ("identity_namespaces", "identity_namespace_id", plan.target_identity_namespace_id),
            ("identity_namespaces", "identity_namespace_id", plan.motif_identity_namespace_id),
            ("identity_namespaces", "identity_namespace_id", plan.membership_identity_namespace_id),
            ("semantic_scopes", "semantic_scope_id", plan.target_semantic_scope_id),
            ("idempotency_namespaces", "idempotency_namespace_id", plan.idempotency_namespace_id),
            ("legacy_source_namespaces", "legacy_source_namespace_id", plan.motif_alias_namespace_id),
        )
        for table, column, value in checks:
            if self._connection.execute(
                f"SELECT 1 FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)
            ).fetchone() is None:
                raise MigrationRuntimeNormalizationRefused("B2_SCOPE_PLAN_REFERENCE_MISSING")

    def _admitted_r1(
        self,
        request: MigrationRuntimeNormalizationRequest,
        manifest: LegacySnapshotManifest,
    ) -> dict[str, Any]:
        namespace = native_id_to_bytes(request.legacy_source_namespace_id)
        rows = self._connection.execute(
            """
            SELECT o.object_id,o.identity_namespace_id,o.object_kind,o.current_revision_id,
                   o.current_revision_ordinal,r.object_revision_id,r.revision_ordinal,
                   r.lineage_kind,r.effective_semantic_scope_id,r.existence_state,
                   r.lifecycle_state,r.lifecycle_authoritative,r.governance_state,
                   r.authority_category,r.provenance_id,r.payload_format,r.payload_text,
                   artifact.legacy_artifact_id,record.record_identity,ordering.runtime_ordinal
              FROM legacy_object_aliases alias
              JOIN objects o ON o.object_id=alias.object_id
              JOIN object_revisions r ON r.object_id=o.object_id
               AND r.object_revision_id=? AND r.revision_ordinal=1
              JOIN semantic_transitions transition ON transition.transition_id=o.creating_transition_id
              JOIN legacy_admission_effects effect ON effect.transition_id=transition.transition_id
              JOIN legacy_admission_records admission ON admission.admission_record_id=effect.admission_record_id
              JOIN legacy_admission_batches batch ON batch.admission_batch_id=admission.admission_batch_id
              JOIN legacy_artifact_records record ON record.legacy_artifact_record_id=admission.legacy_artifact_record_id
              JOIN legacy_artifacts artifact ON artifact.legacy_artifact_id=record.legacy_artifact_id
              LEFT JOIN memory_runtime_enumeration_orders ordering
                ON ordering.legacy_source_namespace_id=alias.legacy_source_namespace_id
               AND ordering.object_id=o.object_id
             WHERE alias.legacy_source_namespace_id=? AND alias.alias_kind='EID' AND alias.alias_value=?
               AND batch.legacy_snapshot_id=? AND admission.admission_status='ADMITTED'
               AND transition.transition_kind='LEGACY_OBJECT_ADMISSION'
            """,
            (native_id_to_bytes(request.expected_revision_id), namespace, str(request.eid),
             native_id_to_bytes(manifest.legacy_snapshot_id)),
        ).fetchall()
        if len(rows) != 1:
            raise MigrationRuntimeNormalizationRefused("B2_ADMITTED_R1_NOT_UNIQUE")
        row = rows[0]
        expected = (
            _MEMORY_OBJECT_KIND, native_id_to_bytes(request.expected_revision_id), 1,
            "LEGACY_PREDECESSOR_UNKNOWN", "EXISTS", "UNKNOWN", 0, "UNKNOWN",
            "NOT_APPLICABLE", None, "TEXT",
        )
        # Deliberately inspect R1 independently of currentness here.  A
        # response-loss retry may legitimately observe R2 as current; the
        # mutating path below is where a new operation requires current R1.
        actual = (row[2], row[5], row[6], row[7], row[9], row[10], row[11], row[12], row[13], row[14], row[15])
        if actual != expected or not isinstance(row[16], str):
            raise MigrationRuntimeNormalizationRefused("B2_R1_LEGACY_EVIDENCE_SHAPE_REQUIRED")
        if row[19] is None or not isinstance(row[19], int):
            raise MigrationRuntimeNormalizationRefused("B2_RUNTIME_ORDER_REQUIRED")
        aliases = self._connection.execute(
            "SELECT legacy_source_namespace_id,alias_value FROM legacy_object_aliases WHERE object_id=? AND alias_kind='EID'",
            (row[0],),
        ).fetchall()
        if aliases != [(namespace, str(request.eid))]:
            raise MigrationRuntimeNormalizationRefused("B2_EID_ALIAS_AMBIGUOUS_OR_FOREIGN")
        if self._connection.execute(
            "SELECT 1 FROM object_revision_governance WHERE object_id=? AND object_revision_id=? AND object_revision_ordinal=1",
            (row[0], native_id_to_bytes(request.expected_revision_id)),
        ).fetchone() is not None:
            raise MigrationRuntimeNormalizationRefused("B2_R1_GOVERNANCE_EVIDENCE_CONFLICT")
        return {
            "object_id": UUID(bytes=row[0]), "identity_namespace_id": UUID(bytes=row[1]),
            "current_revision_id": UUID(bytes=row[3]) if row[3] is not None else None,
            "current_revision_ordinal": row[4], "artifact_id": UUID(bytes=row[17]),
            "record_identity": row[18], "runtime_order_ordinal": row[19],
            "raw_text": row[16],
        }

    def _verified_snapshot_row(
        self,
        request: MigrationRuntimeNormalizationRequest,
        manifest: LegacySnapshotManifest,
        source: dict[str, Any],
    ) -> dict[str, Any]:
        artifact = _nodes_artifact(manifest)
        if source["artifact_id"] != artifact.artifact_id:
            raise MigrationRuntimeNormalizationRefused("B2_ADMITTED_ARTIFACT_MISMATCH")
        candidates, _malformed = _extract_nodes(request.snapshot_root, manifest.legacy_snapshot_id, artifact)
        matching = [item for item in candidates if item.raw_eid == request.eid]
        if len(matching) != 1:
            raise MigrationRuntimeNormalizationRefused("B2_SNAPSHOT_EID_NOT_UNIQUE")
        candidate = matching[0]
        expected_record = f"TMS-LEGACY-NODES-LINE-1:{candidate.line_ordinal}"
        if (
            source["record_identity"] != expected_record
            or source["runtime_order_ordinal"] != candidate.runtime_order_ordinal
        ):
            raise MigrationRuntimeNormalizationRefused("B2_RUNTIME_ORDER_OR_RECORD_MISMATCH")
        try:
            raw_text = candidate.raw_row_bytes.decode("utf-8")
            row = json.loads(raw_text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MigrationRuntimeNormalizationRefused("B2_LEGACY_NODE_JSON_INVALID") from exc
        if raw_text != source["raw_text"] or not isinstance(row, dict) or row.get("eid") != request.eid:
            raise MigrationRuntimeNormalizationRefused("B2_ADMITTED_R1_BYTES_MISMATCH")
        return row

    def _commit(
        self,
        tx: SubstrateTx,
        request: MigrationRuntimeNormalizationRequest,
        plan: PreparedLegacyMemoryNormalization,
        *,
        _test_fail_after_provenance: bool,
    ) -> MigrationRuntimeNormalizationResult:
        fresh = self._prepare(request, require_current=True)
        if _plan_fingerprint(fresh) != _plan_fingerprint(plan):
            raise MigrationRuntimeNormalizationRefused("B2_PREPARED_FACTS_CHANGED")
        provenance_id = native_id_to_bytes(generate_native_id())
        tx.execute(
            """INSERT INTO provenance_records(
                   provenance_id,origin_kind,source_channel,source_role,derivation_status,
                   uncertainty_state,source_time_ns,capture_time_ns,memory_role,descriptive_notes
               ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (provenance_id, *_provenance_values(plan.provenance)),
        )
        if _test_fail_after_provenance:
            raise RuntimeError("forced B2 rollback after provenance publication")
        revision_id = native_id_to_bytes(generate_native_id())
        transition_id = native_id_to_bytes(generate_native_id())
        object_id = native_id_to_bytes(plan.object_id)
        lifecycle = plan.lifecycle
        tx.execute(
            """INSERT INTO object_revisions(
                   object_revision_id,object_id,revision_ordinal,lineage_kind,
                   predecessor_revision_id,predecessor_revision_ordinal,effective_semantic_scope_id,
                   existence_state,lifecycle_state,lifecycle_authoritative,lifecycle_actor,lifecycle_via,
                   lifecycle_set_at_ns,governance_state,authority_category,provenance_id,payload_format,
                   payload_text,created_at_ns
               ) VALUES (?, ?, 2, 'NATIVE_ORDINARY', ?, 1, ?, 'EXISTS', ?, ?, ?, ?, ?,
                         'EXPLICIT', 'NOT_APPLICABLE', ?, 'JSON', ?, 0)""",
            (
                revision_id, object_id, native_id_to_bytes(plan.expected_revision_id),
                native_id_to_bytes(plan.target_semantic_scope_id), lifecycle.state.value.upper(),
                int(lifecycle.is_authoritative_on_row), lifecycle.set_by.actor.value,
                lifecycle.set_by.via.value, lifecycle.set_by.at * 1_000_000_000,
                provenance_id, plan.payload_json,
            ),
        )
        tx.execute(
            "UPDATE objects SET current_revision_id=?,current_revision_ordinal=2 WHERE object_id=?",
            (revision_id, object_id),
        )
        _insert_published_governance_for_qualification(
            tx, object_id=object_id, object_revision_id=revision_id,
            object_revision_ordinal=2, facts=plan.governance,
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (transition_id, tx.operation_id, _TRANSITION_KIND, "NATIVE"),
        )
        tx.execute(
            "INSERT INTO object_revision_effects VALUES (?,?,?,2)",
            (transition_id, object_id, revision_id),
        )
        tx.execute(
            """INSERT INTO operation_outputs(
                   operation_id,output_ordinal,output_role,output_kind,object_id,
                   object_revision_id,object_revision_ordinal
               ) VALUES (?,?,?,'OBJECT',?,?,2)""",
            (tx.operation_id, 0, _OUTPUT_ROLE, object_id, revision_id),
        )
        tx.transitions.append(transition_id)
        tx.published.append((object_id, revision_id, 2))
        self._validate_publication(tx, plan, provenance_id, revision_id, transition_id)
        return MigrationRuntimeNormalizationResult(
            plan.object_id, plan.eid, plan.expected_revision_id, 1, UUID(bytes=revision_id), 2,
            plan.runtime_order_ordinal, UUID(bytes=provenance_id), UUID(bytes=transition_id),
            UUID(bytes=tx.operation_id), plan.payload_digest,
        )

    def _validate_publication(
        self,
        tx: SubstrateTx,
        plan: PreparedLegacyMemoryNormalization,
        provenance_id: bytes,
        revision_id: bytes,
        transition_id: bytes,
    ) -> None:
        object_id = native_id_to_bytes(plan.object_id)
        if tx.execute(
            """SELECT lineage_kind,predecessor_revision_id,predecessor_revision_ordinal,
                      effective_semantic_scope_id,lifecycle_state,lifecycle_authoritative,
                      lifecycle_actor,lifecycle_via,lifecycle_set_at_ns,governance_state,
                      authority_category,provenance_id,payload_format,payload_text
                 FROM object_revisions WHERE object_id=? AND object_revision_id=? AND revision_ordinal=2""",
            (object_id, revision_id),
        ).fetchone() != (
            "NATIVE_ORDINARY", native_id_to_bytes(plan.expected_revision_id), 1,
            native_id_to_bytes(plan.target_semantic_scope_id), plan.lifecycle.state.value.upper(),
            1, plan.lifecycle.set_by.actor.value, plan.lifecycle.set_by.via.value,
            plan.lifecycle.set_by.at * 1_000_000_000, "EXPLICIT", "NOT_APPLICABLE",
            provenance_id, "JSON", plan.payload_json,
        ):
            raise SubstrateInvariantViolation("B2 R2 publication does not match prepared facts")
        if tx.execute(
            "SELECT transition_kind,origin_kind FROM semantic_transitions WHERE transition_id=?",
            (transition_id,),
        ).fetchone() != (_TRANSITION_KIND, "NATIVE"):
            raise SubstrateInvariantViolation("B2 semantic transition is incomplete")
        if tx.execute(
            """SELECT output_role,output_kind,object_id,object_revision_id,object_revision_ordinal
                 FROM operation_outputs WHERE operation_id=?""",
            (tx.operation_id,),
        ).fetchall() != [(_OUTPUT_ROLE, "OBJECT", object_id, revision_id, 2)]:
            raise SubstrateInvariantViolation("B2 operation output does not match R2 publication")
        if tx.execute(
            """SELECT origin_kind,source_channel,source_role,derivation_status,uncertainty_state,
                      source_time_ns,capture_time_ns,memory_role,descriptive_notes
                 FROM provenance_records WHERE provenance_id=?""",
            (provenance_id,),
        ).fetchone() != _provenance_values(plan.provenance):
            raise SubstrateInvariantViolation("B2 provenance child does not match qualified legacy provenance")

    def _result_for_operation(self, operation_id: bytes) -> MigrationRuntimeNormalizationResult | None:
        rows = self._connection.execute(
            """
            SELECT output.object_id,output.object_revision_id,output.object_revision_ordinal,
                   transition.transition_id,revision.predecessor_revision_id,
                   revision.predecessor_revision_ordinal,revision.provenance_id,
                   alias.alias_value,ordering.runtime_ordinal,operation.canonical_intent_json
              FROM operations operation
              JOIN semantic_transitions transition ON transition.operation_id=operation.operation_id
              JOIN operation_outputs output ON output.operation_id=operation.operation_id
              JOIN object_revisions revision ON revision.object_id=output.object_id
               AND revision.object_revision_id=output.object_revision_id
               AND revision.revision_ordinal=output.object_revision_ordinal
              JOIN legacy_object_aliases alias ON alias.object_id=output.object_id AND alias.alias_kind='EID'
              JOIN memory_runtime_enumeration_orders ordering ON ordering.object_id=output.object_id
               AND ordering.legacy_source_namespace_id=alias.legacy_source_namespace_id
             WHERE operation.operation_id=? AND transition.transition_kind=?
               AND output.output_ordinal=0 AND output.output_role=? AND output.output_kind='OBJECT'
            """,
            (operation_id, _TRANSITION_KIND, _OUTPUT_ROLE),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise SubstrateInvariantViolation("B2 normalization recovery result is ambiguous")
        row = rows[0]
        try:
            intent = json.loads(row[9])
            digest = intent["normalized_payload_digest"]
            if not isinstance(digest, str) or len(digest) != 64:
                raise ValueError
            return MigrationRuntimeNormalizationResult(
                UUID(bytes=row[0]), int(row[7]), UUID(bytes=row[4]), row[5], UUID(bytes=row[1]), row[2],
                row[8], UUID(bytes=row[6]), UUID(bytes=row[3]), UUID(bytes=operation_id), digest,
            )
        except (TypeError, ValueError, KeyError) as exc:
            raise SubstrateInvariantViolation("stored B2 normalization result is malformed") from exc


def _exact_scope_plan(request: MigrationRuntimeNormalizationRequest) -> MigrationRuntimeScopePlan:
    plans = tuple(
        plan for plan in request.scope_plans
        if plan.legacy_source_namespace_id == request.legacy_source_namespace_id
    )
    if not plans:
        raise MigrationRuntimeNormalizationRefused("B2_SCOPE_PLAN_MISSING")
    if len(plans) != 1:
        raise MigrationRuntimeNormalizationRefused("B2_SCOPE_PLAN_AMBIGUOUS")
    return plans[0]


def _normalised_runtime_payload(raw_row: dict[str, Any]) -> dict[str, Any]:
    """Apply exactly the existing ``MemoryGraph._load`` payload fallback law."""
    if not isinstance(raw_row.get("payload"), dict):
        raise MigrationRuntimeNormalizationRefused("B2_LEGACY_PAYLOAD_REQUIRED")
    payload = raw_row["payload"]
    try:
        pos = _as3(payload.get("pos", payload.get("seed_pos0", np.zeros(3))))
        vel = _as3(payload.get("vel", payload.get("seed_v0", np.zeros(3))))
        vel0 = _as3(payload.get("vel0", vel))
    except (TypeError, ValueError) as exc:
        raise MigrationRuntimeNormalizationRefused("B2_KINEMATIC_PAYLOAD_INVALID") from exc
    if not all(bool(np.all(np.isfinite(vector))) for vector in (pos, vel, vel0)):
        raise MigrationRuntimeNormalizationRefused("B2_KINEMATIC_PAYLOAD_INVALID")
    try:
        # Canonical JSON is also the exact durable payload domain.  This is a
        # copy, never an in-place rewrite of the admitted evidence mapping.
        result = json.loads(canonical_intent_text(payload))
    except Exception as exc:
        raise MigrationRuntimeNormalizationRefused("B2_RUNTIME_PAYLOAD_NOT_CANONICAL_JSON") from exc
    result["pos"] = [float(value) for value in pos.tolist()]
    result["vel"] = [float(value) for value in vel.tolist()]
    result["vel0"] = [float(value) for value in vel0.tolist()]
    result["alive"] = bool(payload.get("alive", True))
    # born_step/channel are deliberately not copied: the actual legacy loader
    # treats them as node fields, not as SeedEntity.payload facts.
    return result


def _governance_from_payload(payload: dict[str, Any]) -> NativeMemoryGovernanceFacts:
    fields = (
        "protected", "non_shareable", "collective_export_blocked",
        "collective_reingest_blocked", "decay_accelerated",
    )
    raw = payload.get("governance")
    if not isinstance(raw, dict) or set(raw) != set(fields) or any(type(raw[name]) is not bool for name in fields):
        raise MigrationRuntimeNormalizationRefused("B2_EXPLICIT_GOVERNANCE_REQUIRED")
    try:
        return translate_governance_flags(MemoryGovernanceFlags(**raw))
    except (TypeError, ValueError) as exc:
        raise MigrationRuntimeNormalizationRefused("B2_EXPLICIT_GOVERNANCE_REQUIRED") from exc


def _provenance_from_payload(payload: dict[str, Any]) -> NativeProvenanceRecord:
    raw = payload.get("provenance")
    if not isinstance(raw, dict):
        raise MigrationRuntimeNormalizationRefused("B2_EXACT_PROVENANCE_V1_REQUIRED")
    try:
        provenance = ProvenanceV1.from_dict(raw)
        if provenance.to_dict() != raw:
            raise ValueError("non-canonical ProvenanceV1 evidence")
        return translate_provenance_v1(provenance)
    except (TypeError, ValueError) as exc:
        raise MigrationRuntimeNormalizationRefused("B2_EXACT_PROVENANCE_V1_REQUIRED") from exc


def _lifecycle_from_payload(payload: dict[str, Any]) -> LifecycleStatus:
    raw = payload.get("lifecycle_status")
    if not isinstance(raw, dict):
        raise MigrationRuntimeNormalizationRefused("B2_EXPLICIT_LIFECYCLE_REQUIRED")
    try:
        lifecycle = validate_lifecycle_envelope(raw)
        if lifecycle.to_dict() != raw or not lifecycle.is_authoritative_on_row:
            raise ValueError("non-canonical or non-authoritative lifecycle evidence")
        if detect_lifecycle_legacy_marker_disagreement(payload) is not None:
            raise ValueError("explicit lifecycle conflicts with protected-marker evidence")
        return lifecycle
    except (TypeError, ValueError) as exc:
        raise MigrationRuntimeNormalizationRefused("B2_EXPLICIT_LIFECYCLE_REQUIRED") from exc


def _reject_conflicting_outer_evidence(raw_row: dict[str, Any], payload: dict[str, Any]) -> None:
    """Reject a second, disagreeing legacy carrier instead of picking a side."""
    for field, code in (
        ("governance", "B2_GOVERNANCE_EVIDENCE_CONFLICT"),
        ("provenance", "B2_PROVENANCE_EVIDENCE_CONFLICT"),
        ("lifecycle_status", "B2_LIFECYCLE_EVIDENCE_CONFLICT"),
    ):
        if field in raw_row and raw_row[field] != payload.get(field):
            raise MigrationRuntimeNormalizationRefused(code)


def _scope_plan_digest(plans: tuple[MigrationRuntimeScopePlan, ...]) -> str:
    values = sorted((plan.intent() for plan in plans), key=canonical_intent_text)
    return hashlib.sha256(canonical_intent_text(values).encode("utf-8")).hexdigest()


def _retry_contract(request: MigrationRuntimeNormalizationRequest) -> dict[str, object]:
    return {
        "legacy_snapshot_id": str(request.legacy_snapshot_id),
        "legacy_source_namespace_id": str(request.legacy_source_namespace_id),
        "expected_native_core_id": str(request.expected_native_core_id),
        "eid": request.eid,
        "expected_revision_id": str(request.expected_revision_id),
        "scope_plan_digest": _scope_plan_digest(request.scope_plans),
        "idempotency_namespace_id": str(request.idempotency_namespace_id),
    }


def _intent(request: MigrationRuntimeNormalizationRequest, plan: PreparedLegacyMemoryNormalization) -> str:
    return canonical_intent_text({
        "kind": _OPERATION_KIND,
        "normalization_contract": _NORMALIZATION_CONTRACT,
        "retry_contract": _retry_contract(request),
        "legacy_snapshot_id": str(plan.legacy_snapshot_id),
        "legacy_source_namespace_id": str(plan.legacy_source_namespace_id),
        "native_core_id": str(plan.native_core_id),
        "object_id": str(plan.object_id),
        "eid": plan.eid,
        "expected_r1": {"revision_id": str(plan.expected_revision_id), "revision_ordinal": 1},
        "runtime_order_ordinal": plan.runtime_order_ordinal,
        "scope_plan_digest": plan.scope_plan_digest,
        "target_semantic_scope_id": str(plan.target_semantic_scope_id),
        "normalized_payload_digest": plan.payload_digest,
        "governance": list(plan.governance.as_storage_tuple()),
        "provenance": _provenance_intent(plan.provenance),
        "lifecycle": plan.lifecycle.to_dict(),
        "authority_category": plan.authority_category,
    })


def _plan_fingerprint(plan: PreparedLegacyMemoryNormalization) -> str:
    return canonical_intent_text({
        "snapshot": str(plan.legacy_snapshot_id), "source": str(plan.legacy_source_namespace_id),
        "core": str(plan.native_core_id), "object": str(plan.object_id), "eid": plan.eid,
        "r1": str(plan.expected_revision_id), "order": plan.runtime_order_ordinal,
        "scope": plan.scope_plan_digest, "target_scope": str(plan.target_semantic_scope_id),
        "identity": str(plan.identity_namespace_id), "payload_digest": plan.payload_digest,
        "governance": list(plan.governance.as_storage_tuple()),
        "provenance": _provenance_intent(plan.provenance), "lifecycle": plan.lifecycle.to_dict(),
        "authority": plan.authority_category,
    })


def _provenance_intent(provenance: NativeProvenanceRecord) -> dict[str, object | None]:
    return {
        "origin_kind": provenance.origin_kind, "source_channel": provenance.source_channel,
        "source_role": provenance.source_role, "derivation_status": provenance.derivation_status,
        "uncertainty_state": provenance.uncertainty_state, "source_time_ns": provenance.source_time_ns,
        "capture_time_ns": provenance.capture_time_ns, "memory_role": provenance.memory_role,
        "descriptive_notes": provenance.descriptive_notes,
    }


def _provenance_values(provenance: NativeProvenanceRecord) -> tuple[object, ...]:
    return (
        provenance.origin_kind, provenance.source_channel, provenance.source_role,
        provenance.derivation_status, provenance.uncertainty_state, provenance.source_time_ns,
        provenance.capture_time_ns, provenance.memory_role, provenance.descriptive_notes,
    )


__all__ = [
    "MigrationRuntimeNormalizationRefused",
    "MigrationRuntimeNormalizationRequest",
    "MigrationRuntimeNormalizationResult",
    "NativeMigrationRuntimeNormalizationService",
    "PreparedLegacyMemoryNormalization",
]
