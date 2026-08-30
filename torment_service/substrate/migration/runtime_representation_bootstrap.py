"""Bounded B3A bootstrap of a qualified runtime vector from frozen evidence.

This boundary deliberately republishes one already-admitted vector as a new
``COMPAT_EMBEDDING`` for a current B2 R2.  It never changes the legacy capture,
constructs an embedder, or writes semantic object state.
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

from ..canonical_intent import canonical_intent_text
from ..compat_embedding_reader import (
    COMPAT_EMBEDDING_DERIVATION_CONTRACT,
    COMPAT_EMBEDDING_DTYPE,
    COMPAT_EMBEDDING_ENCODING,
    COMPAT_EMBEDDING_GENERATION,
    COMPAT_EMBEDDING_REPRESENTATION_CLASS,
    NativeCompatEmbeddingReader,
    QualifiedCompatEmbedding,
)
from ..errors import (
    SubstrateIdempotencyConflict,
    SubstrateInvariantViolation,
    SubstrateObjectNotFound,
)
from ..ids import native_id_from_bytes, native_id_to_bytes
from ..representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationMetadata,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from ..runtime_binding import NativeRepresentationLane
from ..schema import CORE_ROLE_STAGING, require_current_schema
from .representation_admission import (
    LEGACY_EMBEDDING_REPRESENTATION_CLASS,
    NativeLegacyRepresentationAdmissionService,
)
from .runtime_normalization import _OPERATION_KIND as _B2_OPERATION_KIND
from .runtime_normalization import _OUTPUT_ROLE as _B2_OUTPUT_ROLE
from .runtime_normalization import _TRANSITION_KIND as _B2_TRANSITION_KIND
from .runtime_embedding_input import (
    CanonicalEmbeddingInputUnavailable,
    require_embedding_input_continuity,
)
from .snapshot import LegacySnapshotManifest, load_snapshot_manifest, verify_snapshot


_BOOTSTRAP_CONTRACT = "TMS-MIGRATION-CAPTURE-BOOTSTRAP-7G5B3A/1"
_PREPARED = object()


class MigrationRuntimeRepresentationBootstrapRefused(SubstrateInvariantViolation):
    """A stable fail-closed B3A qualification refusal."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class MigrationRuntimeRepresentationBootstrapRequest:
    """References only; this API never accepts embedding bytes from its caller."""

    snapshot_root: str | Path
    manifest_path: str | Path
    legacy_snapshot_id: UUID
    legacy_source_namespace_id: UUID
    expected_native_core_id: UUID
    eid: int
    expected_r1_revision_id: UUID
    expected_r2_revision_id: UUID
    target_lane: NativeRepresentationLane
    idempotency_namespace_id: UUID
    idempotency_key: str

    def __post_init__(self) -> None:
        for name in (
            "legacy_snapshot_id", "legacy_source_namespace_id", "expected_native_core_id",
            "expected_r1_revision_id", "expected_r2_revision_id", "idempotency_namespace_id",
        ):
            if not isinstance(getattr(self, name), UUID):
                raise ValueError(f"{name} must be a UUID")
        if not isinstance(self.eid, int) or isinstance(self.eid, bool) or self.eid < 0:
            raise ValueError("eid must be a non-negative integer")
        if not isinstance(self.target_lane, NativeRepresentationLane):
            raise ValueError("target_lane must be a NativeRepresentationLane")
        if not isinstance(self.idempotency_key, str) or not self.idempotency_key:
            raise ValueError("idempotency_key must be a non-empty string")
        for name in ("snapshot_root", "manifest_path"):
            value = getattr(self, name)
            if not isinstance(value, (str, Path)) or not str(value).strip():
                raise ValueError(f"{name} is required")


@dataclass(frozen=True, init=False)
class PreparedLegacyCaptureRepresentationBootstrap:
    """Marker-protected evidence and target facts used for all three phases."""

    native_core_id: UUID
    legacy_snapshot_id: UUID
    legacy_source_namespace_id: UUID
    object_id: UUID
    eid: int
    r1_revision_id: UUID
    r2_revision_id: UUID
    b2_operation_id: UUID
    b2_transition_id: UUID
    runtime_order_ordinal: int
    capture_representation_id: UUID
    capture_sha256: str
    capture_byte_length: int
    capture_provider: str
    capture_model: str
    capture_dtype: str
    capture_dimension: int
    capture_encoding_id: str
    capture_derivation_contract_version: str
    target_lane: NativeRepresentationLane
    embedding_input_field: str
    embedding_input_digest: str
    idempotency_namespace_id: UUID
    representation_id: UUID
    _marker: object = field(repr=False, compare=False)

    def __init__(self, *, _marker: object, **values: Any) -> None:
        if _marker is not _PREPARED:
            raise ValueError("bootstrap plans must be prepared from verified durable evidence")
        for name, value in values.items():
            object.__setattr__(self, name, value)
        object.__setattr__(self, "_marker", _marker)


@dataclass(frozen=True)
class MigrationRuntimeRepresentationBootstrapResult:
    object_id: UUID
    eid: int
    r1_revision_id: UUID
    r2_revision_id: UUID
    capture_representation_id: UUID
    representation_id: UUID
    expectation_id: UUID
    selected_measurement_id: UUID
    payload_sha256: str
    payload_byte_length: int


class NativeMigrationRuntimeRepresentationBootstrapService:
    """Republish one exact B1-byte-derivable legacy vector through normal READY flow."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("bootstrap requires an already-open sqlite connection")
        require_current_schema(connection)
        self._connection = connection

    def bootstrap_from_legacy_capture(
        self,
        request: MigrationRuntimeRepresentationBootstrapRequest,
        *,
        _test_stop_after: str | None = None,
        _test_lose_response_after_ready: bool = False,
    ) -> MigrationRuntimeRepresentationBootstrapResult:
        """Create/recover one B3A representation using no bytes except captured evidence.

        The underscored switches are focused interruption seams.  They are not
        semantic inputs and cannot select a different payload or target lane.
        """
        if not isinstance(request, MigrationRuntimeRepresentationBootstrapRequest):
            raise ValueError("a MigrationRuntimeRepresentationBootstrapRequest is required")
        if _test_stop_after not in {None, "PENDING", "EXPECTATION"}:
            raise ValueError("_test_stop_after must be PENDING or EXPECTATION when supplied")
        self._reject_stale_phase_retry(request)
        plan = self._prepare(request)
        existing = self._read_current_qualified(plan)
        if existing is not None:
            return self._result_from_witness(plan, existing)

        representations = NativeRepresentationService(self._connection)
        pending = representations.create_representation_pending(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=_phase_key(request, "PENDING"),
            request=RepresentationRequest(
                source_kind="OBJECT_REVISION", object_id=plan.object_id,
                object_revision_id=plan.r2_revision_id, relationship_id=None,
                relationship_revision_id=None,
                representation_class=plan.target_lane.representation_class,
                generation=plan.target_lane.generation,
                derivation_contract_version=plan.target_lane.derivation_contract_version,
                encoding_id=plan.target_lane.encoding_id, dtype=plan.target_lane.dtype,
                dimension=plan.target_lane.dimension, dependencies=(),
                representation_id=plan.representation_id,
                expected_payload_byte_length=plan.capture_byte_length,
                administrative_derivation_intent=canonical_intent_text(_administrative_intent(plan)),
            ),
        )
        if pending.representation_id != plan.representation_id:
            raise SubstrateInvariantViolation("B3A pending operation returned a different representation")
        if _test_stop_after == "PENDING":
            raise RuntimeError("forced interruption after committed pending representation")

        self._revalidate_prepared(request, plan)
        expectation = representations.establish_representation_integrity_expectation(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=_phase_key(request, "EXPECTATION"),
            request=RepresentationIntegrityExpectationRequest(
                representation_id=plan.representation_id,
                algorithm_id=INTEGRITY_ALGORITHM_SHA256,
                expected_value=bytes.fromhex(plan.capture_sha256),
                value_encoding=INTEGRITY_VALUE_ENCODING_RAW,
            ),
        )
        if _test_stop_after == "EXPECTATION":
            raise RuntimeError("forced interruption after committed integrity expectation")

        self._revalidate_prepared(request, plan)
        capture_bytes = self._read_capture_bytes(plan.capture_representation_id)
        if _sha256(capture_bytes) != plan.capture_sha256 or len(capture_bytes) != plan.capture_byte_length:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_CAPTURE_BYTES_CHANGED")
        ready = representations.publish_representation_ready(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=_phase_key(request, "READY"),
            request=RepresentationReadyRequest(
                representation_id=plan.representation_id,
                representation_class=plan.target_lane.representation_class,
                generation=plan.target_lane.generation,
                derivation_contract_version=plan.target_lane.derivation_contract_version,
                encoding_id=plan.target_lane.encoding_id,
                payload_bytes=capture_bytes,
            ),
        )
        if ready.readiness != "READY" or ready.disposition != "USABLE":
            raise SubstrateInvariantViolation("B3A ready operation did not publish a usable representation")
        if _test_lose_response_after_ready:
            raise RuntimeError("forced response loss after committed ready representation")
        witness = self._read_current_qualified(plan)
        if witness is None:
            raise SubstrateInvariantViolation("B3A ready publication is not readable through NativeCompatEmbeddingReader")
        result = self._result_from_witness(plan, witness)
        if result.expectation_id != expectation.expectation_id:
            raise SubstrateInvariantViolation("B3A expectation recovery does not match qualified reader witness")
        return result

    def _reject_stale_phase_retry(self, request: MigrationRuntimeRepresentationBootstrapRequest) -> None:
        """Make a changed current R2 fail as an idempotency conflict before preparation."""
        row = self._connection.execute(
            "SELECT canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), _phase_key(request, "PENDING")),
        ).fetchone()
        if row is None:
            return
        try:
            stored = json.loads(row[0])
            source_r2 = stored["object_revision_id"]
            source_object = stored["object_id"]
            administrative = stored["administrative_derivation"]
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("stored B3A pending intent is malformed") from exc
        if source_r2 != str(request.expected_r2_revision_id):
            raise SubstrateIdempotencyConflict("idempotency intent differs")
        expected = {
            "bootstrap_contract": _BOOTSTRAP_CONTRACT,
            "core_id": str(request.expected_native_core_id),
            "snapshot_id": str(request.legacy_snapshot_id),
            "source_namespace_id": str(request.legacy_source_namespace_id),
            "eid": request.eid,
            "r1_revision_id": str(request.expected_r1_revision_id),
            "r2_revision_id": str(request.expected_r2_revision_id),
            "target_lane": _lane_intent(request.target_lane),
            "idempotency_namespace_id": str(request.idempotency_namespace_id),
        }
        if not isinstance(source_object, str) or not isinstance(administrative, dict):
            raise SubstrateInvariantViolation("stored B3A pending intent is malformed")
        if any(administrative.get(key) != value for key, value in expected.items()):
            raise SubstrateIdempotencyConflict("idempotency intent differs")

    def _prepare(
        self, request: MigrationRuntimeRepresentationBootstrapRequest
    ) -> PreparedLegacyCaptureRepresentationBootstrap:
        _validate_target_lane(request.target_lane)
        metadata = require_current_schema(self._connection)
        core_id = native_id_from_bytes(metadata.core_id)
        if core_id != request.expected_native_core_id:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_NATIVE_CORE_ID_MISMATCH")
        if metadata.core_role != CORE_ROLE_STAGING:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_CORE_ROLE_NOT_STAGING")
        if self._connection.execute(
            "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
        ).fetchall() != [("LEGACY_ACTIVE", None)]:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_DEPLOYMENT_NOT_LEGACY_ACTIVE")

        manifest = load_snapshot_manifest(request.manifest_path)
        if manifest.legacy_snapshot_id != request.legacy_snapshot_id:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_SNAPSHOT_ID_MISMATCH")
        if manifest.legacy_source_namespace_id != request.legacy_source_namespace_id:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_SOURCE_NAMESPACE_MISMATCH")
        verify_snapshot(snapshot_root=request.snapshot_root, manifest=manifest)
        self._verify_persisted_snapshot(manifest)

        source = self._source_facts(request, manifest)
        r2 = self._b2_r2_facts(request, source)
        capture = self._capture_facts(request, manifest, source)
        try:
            embedding_input = require_embedding_input_continuity(source["r1_payload"], r2["payload"])
        except CanonicalEmbeddingInputUnavailable as exc:
            raise MigrationRuntimeRepresentationBootstrapRefused(
                "B3A_EMBEDDING_INPUT_CONTINUITY_BLOCKED"
            ) from exc
        plan_values: dict[str, Any] = {
            "native_core_id": core_id,
            "legacy_snapshot_id": request.legacy_snapshot_id,
            "legacy_source_namespace_id": request.legacy_source_namespace_id,
            "object_id": source["object_id"], "eid": request.eid,
            "r1_revision_id": request.expected_r1_revision_id,
            "r2_revision_id": request.expected_r2_revision_id,
            "b2_operation_id": r2["operation_id"], "b2_transition_id": r2["transition_id"],
            "runtime_order_ordinal": source["runtime_order_ordinal"],
            "capture_representation_id": capture["representation_id"],
            "capture_sha256": capture["sha256"], "capture_byte_length": capture["byte_length"],
            "capture_provider": capture["provider"], "capture_model": capture["model"],
            "capture_dtype": capture["dtype"], "capture_dimension": capture["dimension"],
            "capture_encoding_id": capture["encoding_id"],
            "capture_derivation_contract_version": capture["derivation_contract_version"],
            "target_lane": request.target_lane, "embedding_input_field": embedding_input.field,
            "embedding_input_digest": embedding_input.digest,
            "idempotency_namespace_id": request.idempotency_namespace_id,
        }
        representation_id = _deterministic_native_id(_plan_identity(plan_values))
        return PreparedLegacyCaptureRepresentationBootstrap(
            **plan_values, representation_id=representation_id, _marker=_PREPARED,
        )

    def _revalidate_prepared(
        self,
        request: MigrationRuntimeRepresentationBootstrapRequest,
        plan: PreparedLegacyCaptureRepresentationBootstrap,
    ) -> None:
        fresh = self._prepare(request)
        if _plan_identity(_plan_values(fresh)) != _plan_identity(_plan_values(plan)):
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_PREPARED_FACTS_CHANGED")

    def _verify_persisted_snapshot(self, manifest: LegacySnapshotManifest) -> None:
        snapshots = self._connection.execute(
            "SELECT legacy_source_namespace_id FROM legacy_snapshots WHERE legacy_snapshot_id=?",
            (native_id_to_bytes(manifest.legacy_snapshot_id),),
        ).fetchall()
        if snapshots != [(native_id_to_bytes(manifest.legacy_source_namespace_id),)]:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_PERSISTED_SNAPSHOT_MISMATCH")
        nodes = [artifact for artifact in manifest.artifacts if artifact.artifact_class == "LEGACY_CORE_NODE_EVIDENCE"]
        if len(nodes) != 1:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_NODES_ARTIFACT_NOT_UNIQUE")
        artifact = nodes[0]
        persisted = self._connection.execute(
            """SELECT legacy_snapshot_id,artifact_kind,observed_locator,digest_algorithm,digest_value
                 FROM legacy_artifacts WHERE legacy_artifact_id=?""",
            (native_id_to_bytes(artifact.artifact_id),),
        ).fetchall()
        expected = (native_id_to_bytes(manifest.legacy_snapshot_id), artifact.artifact_class,
                    artifact.observed_relative_locator, artifact.digest_algorithm, bytes.fromhex(artifact.digest_hex))
        if persisted != [expected]:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_PERSISTED_ARTIFACT_MISMATCH")

    def _source_facts(
        self,
        request: MigrationRuntimeRepresentationBootstrapRequest,
        manifest: LegacySnapshotManifest,
    ) -> dict[str, Any]:
        namespace = native_id_to_bytes(request.legacy_source_namespace_id)
        rows = self._connection.execute(
            """
            SELECT o.object_id,o.identity_namespace_id,o.object_kind,r.payload_text,
                   ordering.runtime_ordinal,artifact.legacy_artifact_id,record.record_identity
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
              JOIN memory_runtime_enumeration_orders ordering
                ON ordering.legacy_source_namespace_id=alias.legacy_source_namespace_id AND ordering.object_id=o.object_id
             WHERE alias.legacy_source_namespace_id=? AND alias.alias_kind='EID' AND alias.alias_value=?
               AND batch.legacy_snapshot_id=? AND admission.admission_status='ADMITTED'
               AND transition.transition_kind='LEGACY_OBJECT_ADMISSION'
               AND r.lineage_kind='LEGACY_PREDECESSOR_UNKNOWN' AND r.existence_state='EXISTS'
               AND r.lifecycle_state='UNKNOWN' AND r.lifecycle_authoritative=0
               AND r.governance_state='UNKNOWN' AND r.authority_category='NOT_APPLICABLE'
               AND r.provenance_id IS NULL AND r.payload_format='TEXT'
            """,
            (native_id_to_bytes(request.expected_r1_revision_id), namespace, str(request.eid),
             native_id_to_bytes(manifest.legacy_snapshot_id)),
        ).fetchall()
        if len(rows) != 1 or rows[0][2] != "LEGACY_CORE_NODE" or not isinstance(rows[0][3], str):
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_ADMITTED_R1_NOT_UNIQUE")
        aliases = self._connection.execute(
            "SELECT legacy_source_namespace_id,alias_value FROM legacy_object_aliases WHERE object_id=? AND alias_kind='EID'",
            (rows[0][0],),
        ).fetchall()
        if aliases != [(namespace, str(request.eid))] or not isinstance(rows[0][4], int):
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_EID_ALIAS_OR_RUNTIME_ORDER_INVALID")
        try:
            raw = json.loads(rows[0][3])
            payload = raw["payload"]
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_R1_PAYLOAD_INVALID") from exc
        if not isinstance(raw, dict) or raw.get("eid") != request.eid or not isinstance(payload, dict):
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_R1_PAYLOAD_INVALID")
        return {
            "object_id": UUID(bytes=rows[0][0]), "identity_namespace_id": UUID(bytes=rows[0][1]),
            "r1_payload": payload, "runtime_order_ordinal": rows[0][4],
            "artifact_id": UUID(bytes=rows[0][5]), "record_identity": rows[0][6],
        }

    def _b2_r2_facts(
        self, request: MigrationRuntimeRepresentationBootstrapRequest, source: dict[str, Any]
    ) -> dict[str, Any]:
        object_blob = native_id_to_bytes(source["object_id"])
        r2_blob = native_id_to_bytes(request.expected_r2_revision_id)
        rows = self._connection.execute(
            """
            SELECT o.current_revision_id,o.current_revision_ordinal,r.lineage_kind,
                   r.predecessor_revision_id,r.predecessor_revision_ordinal,r.existence_state,
                   r.lifecycle_state,r.lifecycle_authoritative,r.lifecycle_actor,r.lifecycle_via,
                   r.lifecycle_set_at_ns,r.governance_state,r.authority_category,r.provenance_id,
                   r.payload_format,r.payload_text,t.transition_id,t.operation_id,t.transition_kind,
                   t.origin_kind,operation.operation_kind,e.object_revision_id,e.object_revision_ordinal,
                   output.output_role,output.output_kind,output.object_id,output.object_revision_id,
                   output.object_revision_ordinal
              FROM objects o
              JOIN object_revisions r ON r.object_id=o.object_id AND r.object_revision_id=?
              JOIN object_revision_effects e ON e.object_id=r.object_id
               AND e.object_revision_id=r.object_revision_id AND e.object_revision_ordinal=r.revision_ordinal
              JOIN semantic_transitions t ON t.transition_id=e.transition_id
              JOIN operations operation ON operation.operation_id=t.operation_id
              JOIN operation_outputs output ON output.operation_id=operation.operation_id
             WHERE o.object_id=?
            """, (r2_blob, object_blob),
        ).fetchall()
        if len(rows) != 1:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_B2_TOPOLOGY_NOT_UNIQUE")
        row = rows[0]
        expected = (
            r2_blob, 2, "NATIVE_ORDINARY", native_id_to_bytes(request.expected_r1_revision_id), 1,
            "EXISTS", "EXPLICIT", "NOT_APPLICABLE", "JSON", _B2_TRANSITION_KIND, "NATIVE",
            _B2_OPERATION_KIND, r2_blob, 2, _B2_OUTPUT_ROLE, "OBJECT", object_blob, r2_blob, 2,
        )
        actual = (
            row[0], row[1], row[2], row[3], row[4], row[5], row[11], row[12], row[14],
            row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27],
        )
        if actual != expected or row[6] is None or row[7] != 1 or not _nonempty(row[8], row[9]) or not isinstance(row[10], int):
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_B2_R2_WITNESS_INVALID")
        governance = self._connection.execute(
            """SELECT protected,non_shareable,collective_export_blocked,collective_reingest_blocked,decay_accelerated
                 FROM object_revision_governance WHERE object_id=? AND object_revision_id=? AND object_revision_ordinal=2""",
            (object_blob, r2_blob),
        ).fetchall()
        if len(governance) != 1 or any(value not in (0, 1) for value in governance[0]):
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_B2_GOVERNANCE_INVALID")
        provenance = self._connection.execute(
            """SELECT origin_kind,source_channel,source_role,derivation_status,uncertainty_state
                 FROM provenance_records WHERE provenance_id=?""", (row[13],)
        ).fetchall()
        if len(provenance) != 1 or not _nonempty(provenance[0][0], provenance[0][1], provenance[0][3], provenance[0][4]) or (
            provenance[0][2] is not None and not _nonempty(provenance[0][2])
        ):
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_B2_PROVENANCE_INVALID")
        try:
            payload = json.loads(row[15])
        except (TypeError, json.JSONDecodeError) as exc:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_B2_PAYLOAD_INVALID") from exc
        if not isinstance(payload, dict):
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_B2_PAYLOAD_INVALID")
        return {"payload": payload, "transition_id": UUID(bytes=row[16]), "operation_id": UUID(bytes=row[17])}

    def _capture_facts(
        self,
        request: MigrationRuntimeRepresentationBootstrapRequest,
        manifest: LegacySnapshotManifest,
        source: dict[str, Any],
    ) -> dict[str, Any]:
        rows = self._connection.execute(
            """
            SELECT r.representation_id,r.dtype,r.dimension,r.encoding_id,r.derivation_contract_version,
                   r.expected_payload_byte_length,p.payload_bytes,admission.unknown_fields_json,
                   batch.legacy_snapshot_id
              FROM representations r
              JOIN representation_current_state state USING(representation_id)
              JOIN representation_state_effects state_effect ON state_effect.representation_id=r.representation_id
              JOIN semantic_transitions transition ON transition.transition_id=state_effect.transition_id
              JOIN legacy_admission_effects effect ON effect.transition_id=transition.transition_id
              JOIN legacy_admission_records admission ON admission.admission_record_id=effect.admission_record_id
              JOIN legacy_admission_batches batch ON batch.admission_batch_id=admission.admission_batch_id
              JOIN representation_payloads p USING(representation_id)
             WHERE r.source_kind='OBJECT_REVISION' AND r.source_object_id=?
               AND r.source_object_revision_id=? AND r.source_object_revision_ordinal=1
               AND r.representation_class=? AND state.readiness='UNKNOWN'
               AND state.operational_disposition='RECONCILIATION_REQUIRED'
               AND transition.transition_kind='LEGACY_REPRESENTATION_ADMISSION'
               AND transition.origin_kind='LEGACY_ADMISSION' AND admission.admission_status='ADMITTED'
            """,
            (native_id_to_bytes(source["object_id"]), native_id_to_bytes(request.expected_r1_revision_id),
             LEGACY_EMBEDDING_REPRESENTATION_CLASS),
        ).fetchall()
        if len(rows) != 1 or rows[0][8] != native_id_to_bytes(manifest.legacy_snapshot_id):
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_CAPTURE_SELECTION_AMBIGUOUS_OR_MISSING")
        row = rows[0]
        try:
            metadata = json.loads(row[7])
            identity = metadata["legacy_derivation_metadata"]
            provider, model = identity["provider"], identity["model"]
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_CAPTURE_IDENTITY_INSUFFICIENT") from exc
        if not _nonempty(provider, model) or row[3] != "NUMPY_NPY":
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_CAPTURE_IDENTITY_INSUFFICIENT")
        lane = request.target_lane
        if (row[1], row[2], provider, model) != (lane.dtype, lane.dimension, lane.provider, lane.model):
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_REEMBED_REQUIRED")
        payload = self._read_capture_bytes(UUID(bytes=row[0]))
        if payload != row[6] or row[5] != len(payload) or len(payload) != lane.dimension * np.dtype(np.float32).itemsize:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_CAPTURE_BYTE_DERIVATION_CONTRACT_BLOCKED")
        vector = np.frombuffer(payload, dtype=np.float32)
        if vector.size != lane.dimension or not bool(np.all(np.isfinite(vector))):
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_UNUSABLE_VECTOR_EVIDENCE")
        return {
            "representation_id": UUID(bytes=row[0]), "dtype": row[1], "dimension": row[2],
            "encoding_id": row[3], "derivation_contract_version": row[4],
            "byte_length": len(payload), "sha256": _sha256(payload), "provider": provider, "model": model,
        }

    def _read_capture_bytes(self, representation_id: UUID) -> bytes:
        try:
            return NativeLegacyRepresentationAdmissionService(self._connection).read_admitted_representation_payload(representation_id)
        except SubstrateObjectNotFound as exc:
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_CAPTURE_EVIDENCE_UNAVAILABLE") from exc

    def _read_current_qualified(
        self, plan: PreparedLegacyCaptureRepresentationBootstrap
    ) -> QualifiedCompatEmbedding | None:
        witness = NativeCompatEmbeddingReader(self._connection).read_current(
            plan.object_id, expected_dimension=plan.target_lane.dimension,
        )
        if witness is None:
            return None
        if (
            witness.representation_id != plan.representation_id
            or witness.source_revision_id != plan.r2_revision_id
            or witness.source_revision_ordinal != 2
            or witness.payload_sha256 != plan.capture_sha256
            or witness.payload_bytes != self._read_capture_bytes(plan.capture_representation_id)
        ):
            raise MigrationRuntimeRepresentationBootstrapRefused("B3A_COMPETING_CURRENT_COMPAT_EMBEDDING")
        return witness

    @staticmethod
    def _result_from_witness(
        plan: PreparedLegacyCaptureRepresentationBootstrap,
        witness: QualifiedCompatEmbedding,
    ) -> MigrationRuntimeRepresentationBootstrapResult:
        if witness.expectation_id is None or witness.selected_measurement_id is None:
            raise SubstrateInvariantViolation("qualified B3A reader witness lacks integrity identity")
        return MigrationRuntimeRepresentationBootstrapResult(
            plan.object_id, plan.eid, plan.r1_revision_id, plan.r2_revision_id,
            plan.capture_representation_id, witness.representation_id, witness.expectation_id,
            witness.selected_measurement_id, witness.payload_sha256, witness.payload_byte_length,
        )


def _validate_target_lane(lane: NativeRepresentationLane) -> None:
    if not _nonempty(lane.provider, lane.model) or not isinstance(lane.dimension, int) or isinstance(lane.dimension, bool):
        raise MigrationRuntimeRepresentationBootstrapRefused("B3A_TARGET_LANE_INVALID")
    actual = (lane.representation_class, lane.generation, lane.derivation_contract_version, lane.encoding_id, lane.dtype)
    expected = (COMPAT_EMBEDDING_REPRESENTATION_CLASS, COMPAT_EMBEDDING_GENERATION,
                COMPAT_EMBEDDING_DERIVATION_CONTRACT, COMPAT_EMBEDDING_ENCODING, COMPAT_EMBEDDING_DTYPE)
    if actual != expected or lane.dimension < 1:
        raise MigrationRuntimeRepresentationBootstrapRefused("B3A_TARGET_LANE_INVALID")


def _administrative_intent(plan: PreparedLegacyCaptureRepresentationBootstrap) -> dict[str, object]:
    return {
        "kind": "MIGRATION_CAPTURE_BOOTSTRAP", "bootstrap_contract": _BOOTSTRAP_CONTRACT,
        "core_id": str(plan.native_core_id), "snapshot_id": str(plan.legacy_snapshot_id),
        "source_namespace_id": str(plan.legacy_source_namespace_id), "object_id": str(plan.object_id),
        "eid": plan.eid, "r1_revision_id": str(plan.r1_revision_id),
        "r2_revision_id": str(plan.r2_revision_id), "b2_operation_id": str(plan.b2_operation_id),
        "b2_transition_id": str(plan.b2_transition_id), "runtime_order_ordinal": plan.runtime_order_ordinal,
        "legacy_capture_representation_id": str(plan.capture_representation_id),
        "capture_sha256": plan.capture_sha256, "capture_byte_length": plan.capture_byte_length,
        "capture_provider": plan.capture_provider, "capture_model": plan.capture_model,
        "capture_dtype": plan.capture_dtype, "capture_dimension": plan.capture_dimension,
        "capture_encoding_id": plan.capture_encoding_id,
        "capture_derivation_contract_version": plan.capture_derivation_contract_version,
        "target_lane": _lane_intent(plan.target_lane), "embedding_input_field": plan.embedding_input_field,
        "embedding_input_digest": plan.embedding_input_digest,
        "idempotency_namespace_id": str(plan.idempotency_namespace_id),
    }


def _plan_values(plan: PreparedLegacyCaptureRepresentationBootstrap) -> dict[str, Any]:
    return {
        "native_core_id": plan.native_core_id, "legacy_snapshot_id": plan.legacy_snapshot_id,
        "legacy_source_namespace_id": plan.legacy_source_namespace_id, "object_id": plan.object_id,
        "eid": plan.eid, "r1_revision_id": plan.r1_revision_id, "r2_revision_id": plan.r2_revision_id,
        "b2_operation_id": plan.b2_operation_id, "b2_transition_id": plan.b2_transition_id,
        "runtime_order_ordinal": plan.runtime_order_ordinal,
        "capture_representation_id": plan.capture_representation_id, "capture_sha256": plan.capture_sha256,
        "capture_byte_length": plan.capture_byte_length, "capture_provider": plan.capture_provider,
        "capture_model": plan.capture_model, "capture_dtype": plan.capture_dtype,
        "capture_dimension": plan.capture_dimension, "capture_encoding_id": plan.capture_encoding_id,
        "capture_derivation_contract_version": plan.capture_derivation_contract_version,
        "target_lane": plan.target_lane, "embedding_input_field": plan.embedding_input_field,
        "embedding_input_digest": plan.embedding_input_digest,
        "idempotency_namespace_id": plan.idempotency_namespace_id,
    }


def _plan_identity(values: dict[str, Any]) -> dict[str, object]:
    return {
        "bootstrap_contract": _BOOTSTRAP_CONTRACT, "core_id": str(values["native_core_id"]),
        "snapshot_id": str(values["legacy_snapshot_id"]), "source_namespace_id": str(values["legacy_source_namespace_id"]),
        "object_id": str(values["object_id"]), "eid": values["eid"],
        "r1_revision_id": str(values["r1_revision_id"]), "r2_revision_id": str(values["r2_revision_id"]),
        "b2_operation_id": str(values["b2_operation_id"]), "b2_transition_id": str(values["b2_transition_id"]),
        "runtime_order_ordinal": values["runtime_order_ordinal"],
        "legacy_capture_representation_id": str(values["capture_representation_id"]),
        "capture_sha256": values["capture_sha256"], "capture_byte_length": values["capture_byte_length"],
        "capture_provider": values["capture_provider"], "capture_model": values["capture_model"],
        "capture_dtype": values["capture_dtype"], "capture_dimension": values["capture_dimension"],
        "capture_encoding_id": values["capture_encoding_id"],
        "capture_derivation_contract_version": values["capture_derivation_contract_version"],
        "target_lane": _lane_intent(values["target_lane"]),
        "embedding_input_field": values["embedding_input_field"],
        "embedding_input_digest": values["embedding_input_digest"],
        "idempotency_namespace_id": str(values["idempotency_namespace_id"]),
    }


def _lane_intent(lane: NativeRepresentationLane) -> dict[str, object]:
    return {
        "provider": lane.provider, "model": lane.model, "dimension": lane.dimension,
        "representation_class": lane.representation_class, "generation": lane.generation,
        "derivation_contract_version": lane.derivation_contract_version, "encoding_id": lane.encoding_id,
        "dtype": lane.dtype,
    }


def _phase_key(request: MigrationRuntimeRepresentationBootstrapRequest, phase: str) -> str:
    return f"B3A_CAPTURE_BOOTSTRAP:{phase}:{request.idempotency_key}"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _deterministic_native_id(intent: dict[str, object]) -> UUID:
    """Derive a stable UUIDv4-shaped native ID from the frozen bootstrap contract."""
    raw = bytearray(hashlib.sha256(canonical_intent_text(intent).encode("utf-8")).digest()[:16])
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    return UUID(bytes=bytes(raw))


def _nonempty(*values: object) -> bool:
    return all(isinstance(value, str) and value for value in values)


__all__ = [
    "MigrationRuntimeRepresentationBootstrapRefused",
    "MigrationRuntimeRepresentationBootstrapRequest",
    "MigrationRuntimeRepresentationBootstrapResult",
    "NativeMigrationRuntimeRepresentationBootstrapService",
    "PreparedLegacyCaptureRepresentationBootstrap",
]
