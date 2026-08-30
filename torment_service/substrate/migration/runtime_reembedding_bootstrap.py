"""Bounded B3B bootstrap of a runtime vector from qualified B2 memory text.

The service is deliberately a representation-only administrative boundary.  It
accepts a caller-owned target embedder, proves the same B2 topology used by
B3A, and uses the normal native PENDING -> expectation -> READY protocol.  It
never constructs an embedder, rewrites a memory payload, or promotes legacy
representation evidence.
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

from torment_service.embeddings import Embedder

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
from .runtime_embedding_input import (
    CanonicalEmbeddingInputUnavailable,
    select_canonical_embedding_input,
)
from .runtime_readiness import (
    LegacyVectorStrategy,
    MigrationRuntimeReadinessRequest,
    MigrationRuntimeScopePlan,
    NativeMigrationRuntimeReadinessPreflight,
    ObjectRuntimeReadiness,
)
from .runtime_representation_bootstrap import (
    MigrationRuntimeRepresentationBootstrapRefused,
    MigrationRuntimeRepresentationBootstrapRequest,
    NativeMigrationRuntimeRepresentationBootstrapService,
)
from .snapshot import LegacySnapshotManifest, load_snapshot_manifest, verify_snapshot


_BOOTSTRAP_CONTRACT = "TMS-MIGRATION-REEMBED-BOOTSTRAP-7G5B3B/1"
_PREPARED = object()
_ACCEPTED_STRATEGIES = {
    LegacyVectorStrategy.REEMBED_REQUIRED,
    LegacyVectorStrategy.NO_VECTOR_PRESENT,
    LegacyVectorStrategy.UNUSABLE_VECTOR_EVIDENCE,
}


class MigrationRuntimeReembeddingBootstrapRefused(SubstrateInvariantViolation):
    """A stable fail-closed B3B qualification refusal."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class MigrationRuntimeReembeddingBootstrapRequest:
    """References for one generated-vector bootstrap; never accepts vector bytes."""

    snapshot_root: str | Path
    manifest_path: str | Path
    legacy_snapshot_id: UUID
    legacy_source_namespace_id: UUID
    expected_native_core_id: UUID
    eid: int
    expected_r1_revision_id: UUID
    expected_r2_revision_id: UUID
    scope_plans: tuple[MigrationRuntimeScopePlan, ...]
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
        if not isinstance(self.scope_plans, tuple) or any(
            not isinstance(plan, MigrationRuntimeScopePlan) for plan in self.scope_plans
        ):
            raise ValueError("scope_plans must be a tuple of MigrationRuntimeScopePlan values")
        if not isinstance(self.target_lane, NativeRepresentationLane):
            raise ValueError("target_lane must be a NativeRepresentationLane")
        if not isinstance(self.idempotency_key, str) or not self.idempotency_key:
            raise ValueError("idempotency_key must be a non-empty string")
        for name in ("snapshot_root", "manifest_path"):
            value = getattr(self, name)
            if not isinstance(value, (str, Path)) or not str(value).strip():
                raise ValueError(f"{name} is required")


@dataclass(frozen=True, init=False)
class PreparedRuntimeReembeddingBootstrap:
    """Marker-protected durable facts and transient qualified input text."""

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
    scope_plan_digest: str
    embedding_input_field: str
    embedding_input_digest: str
    embedding_input_text: str
    target_lane: NativeRepresentationLane
    embedder_provider: str
    embedder_model: str
    embedder_dimension: int
    legacy_vector_strategy: LegacyVectorStrategy
    retained_legacy_capture_ids: tuple[UUID, ...]
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
class MigrationRuntimeReembeddingBootstrapResult:
    object_id: UUID
    eid: int
    r1_revision_id: UUID
    r2_revision_id: UUID
    retained_legacy_capture_ids: tuple[UUID, ...]
    representation_id: UUID
    expectation_id: UUID
    selected_measurement_id: UUID
    payload_sha256: str
    payload_byte_length: int


@dataclass(frozen=True)
class _ObservedVector:
    payload_bytes: bytes
    payload_sha256: str


class NativeMigrationRuntimeReembeddingBootstrapService:
    """Generate one qualified representation from B2 R2 text using an injected embedder."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("bootstrap requires an already-open sqlite connection")
        require_current_schema(connection)
        self._connection = connection

    def bootstrap_from_qualified_text(
        self,
        request: MigrationRuntimeReembeddingBootstrapRequest,
        *,
        embedder: Embedder,
        _test_stop_after: str | None = None,
        _test_lose_response_after_ready: bool = False,
    ) -> MigrationRuntimeReembeddingBootstrapResult:
        """Publish/recover one target-lane vector without provider construction or fallback."""
        if not isinstance(request, MigrationRuntimeReembeddingBootstrapRequest):
            raise ValueError("a MigrationRuntimeReembeddingBootstrapRequest is required")
        if _test_stop_after not in {None, "PENDING", "EXPECTATION"}:
            raise ValueError("_test_stop_after must be PENDING or EXPECTATION when supplied")
        _validate_target_lane(request.target_lane)
        _validate_embedder_identity(embedder, request.target_lane)
        self._reject_stale_phase_retry(request, embedder)
        plan = self._prepare(request, embedder)

        existing = self._existing_target(plan)
        if existing is not None:
            if existing.readiness == "READY" and existing.disposition == "USABLE":
                witness = self._read_current_qualified(plan)
                if witness is None:
                    raise MigrationRuntimeReembeddingBootstrapRefused("B3B_EXISTING_READY_NOT_QUALIFIED")
                return self._result_from_witness(plan, witness)
            if (existing.readiness, existing.disposition) != ("PENDING", "WITHHELD"):
                raise MigrationRuntimeReembeddingBootstrapRefused("B3B_EXISTING_TARGET_NOT_RECOVERABLE")

        # The first observation happens before the first PENDING write.  A model
        # failure therefore leaves no B3B representation residue at all.
        observed = self._observe_vector(embedder, plan)
        representations = NativeRepresentationService(self._connection)
        if existing is None:
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
                    expected_payload_byte_length=len(observed.payload_bytes),
                    administrative_derivation_intent=canonical_intent_text(
                        _administrative_intent(plan, observed.payload_sha256)
                    ),
                ),
            )
            if pending.representation_id != plan.representation_id:
                raise SubstrateInvariantViolation("B3B pending operation returned a different representation")
        if _test_stop_after == "PENDING":
            raise RuntimeError("forced interruption after committed pending representation")

        self._revalidate_prepared(request, embedder, plan)
        expectation = self._establish_or_match_expectation(
            representations, request, plan, observed.payload_sha256
        )
        if _test_stop_after == "EXPECTATION":
            raise RuntimeError("forced interruption after committed integrity expectation")

        self._revalidate_prepared(request, embedder, plan)
        ready = representations.publish_representation_ready(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=_phase_key(request, "READY"),
            request=RepresentationReadyRequest(
                representation_id=plan.representation_id,
                representation_class=plan.target_lane.representation_class,
                generation=plan.target_lane.generation,
                derivation_contract_version=plan.target_lane.derivation_contract_version,
                encoding_id=plan.target_lane.encoding_id,
                payload_bytes=observed.payload_bytes,
            ),
        )
        if ready.readiness != "READY" or ready.disposition != "USABLE":
            raise SubstrateInvariantViolation("B3B ready operation did not publish a usable representation")
        if _test_lose_response_after_ready:
            raise RuntimeError("forced response loss after committed ready representation")
        witness = self._read_current_qualified(plan)
        if witness is None:
            raise SubstrateInvariantViolation("B3B ready publication is not readable through NativeCompatEmbeddingReader")
        if witness.payload_bytes != observed.payload_bytes or witness.payload_sha256 != observed.payload_sha256:
            raise SubstrateInvariantViolation("B3B reader witness contradicts the published generated vector")
        result = self._result_from_witness(plan, witness)
        if result.expectation_id != expectation.expectation_id:
            raise SubstrateInvariantViolation("B3B expectation recovery does not match the qualified reader witness")
        return result

    def _reject_stale_phase_retry(
        self, request: MigrationRuntimeReembeddingBootstrapRequest, embedder: Embedder
    ) -> None:
        """Fail before model contact when a same-key request changed its semantic identity."""
        row = self._connection.execute(
            "SELECT canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), _phase_key(request, "PENDING")),
        ).fetchone()
        if row is None:
            return
        try:
            stored = json.loads(row[0])
            administrative = stored["administrative_derivation"]
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("stored B3B pending intent is malformed") from exc
        expected = _request_identity(request, embedder)
        if not isinstance(administrative, dict) or any(
            administrative.get(key) != value for key, value in expected.items()
        ):
            raise SubstrateIdempotencyConflict("idempotency intent differs")

    def _prepare(
        self, request: MigrationRuntimeReembeddingBootstrapRequest, embedder: Embedder
    ) -> PreparedRuntimeReembeddingBootstrap:
        _validate_target_lane(request.target_lane)
        _validate_embedder_identity(embedder, request.target_lane)
        metadata = require_current_schema(self._connection)
        core_id = native_id_from_bytes(metadata.core_id)
        if core_id != request.expected_native_core_id:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_NATIVE_CORE_ID_MISMATCH")
        if metadata.core_role != CORE_ROLE_STAGING:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_CORE_ROLE_NOT_STAGING")
        if self._connection.execute(
            "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
        ).fetchall() != [("LEGACY_ACTIVE", None)]:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_DEPLOYMENT_NOT_LEGACY_ACTIVE")

        manifest = load_snapshot_manifest(request.manifest_path)
        if manifest.legacy_snapshot_id != request.legacy_snapshot_id:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_SNAPSHOT_ID_MISMATCH")
        if manifest.legacy_source_namespace_id != request.legacy_source_namespace_id:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_SOURCE_NAMESPACE_MISMATCH")
        verify_snapshot(snapshot_root=request.snapshot_root, manifest=manifest)

        # B3A owns the frozen source/snapshot and strong B2 topology proof.  Reusing
        # it here keeps B3B subject to exactly the already-qualified evidence test.
        proof_request = MigrationRuntimeRepresentationBootstrapRequest(
            snapshot_root=request.snapshot_root, manifest_path=request.manifest_path,
            legacy_snapshot_id=request.legacy_snapshot_id,
            legacy_source_namespace_id=request.legacy_source_namespace_id,
            expected_native_core_id=request.expected_native_core_id, eid=request.eid,
            expected_r1_revision_id=request.expected_r1_revision_id,
            expected_r2_revision_id=request.expected_r2_revision_id,
            target_lane=request.target_lane,
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=request.idempotency_key,
        )
        proof = NativeMigrationRuntimeRepresentationBootstrapService(self._connection)
        try:
            proof._verify_persisted_snapshot(manifest)
            source = proof._source_facts(proof_request, manifest)
            r2 = proof._b2_r2_facts(proof_request, source)
        except MigrationRuntimeRepresentationBootstrapRefused as exc:
            raise MigrationRuntimeReembeddingBootstrapRefused(
                "B3B_B2_OR_SOURCE_PROOF_REFUSED"
            ) from exc

        readiness = NativeMigrationRuntimeReadinessPreflight(self._connection).run(
            MigrationRuntimeReadinessRequest(
                legacy_snapshot_id=request.legacy_snapshot_id,
                expected_native_core_id=request.expected_native_core_id,
                scope_plans=request.scope_plans,
                target_lane=request.target_lane,
            )
        )
        items = [item for item in readiness.object_items if item.object_id == source["object_id"]]
        if len(items) != 1:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_B1_OBJECT_NOT_UNIQUE")
        item = items[0]
        if item.current_revision_id != request.expected_r2_revision_id or item.current_revision_ordinal != 2:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_B1_CURRENT_R2_MISMATCH")
        strategy = item.legacy_vector_strategy
        if strategy is LegacyVectorStrategy.BYTE_DERIVATION_POSSIBLE:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3A_DETERMINISTIC_CAPTURE_BOOTSTRAP_AVAILABLE")
        if strategy not in _ACCEPTED_STRATEGIES:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_LEGACY_VECTOR_STRATEGY_NOT_ACCEPTED")
        if item.readiness not in {
            ObjectRuntimeReadiness.REPRESENTATION_BOOTSTRAP_REQUIRED,
            ObjectRuntimeReadiness.RUNTIME_READY_AS_IS,
        }:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_OBJECT_NOT_REEMBED_ELIGIBLE")
        try:
            input_value = select_canonical_embedding_input(r2["payload"])
        except CanonicalEmbeddingInputUnavailable as exc:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_CANONICAL_EMBEDDING_INPUT_BLOCKED") from exc
        retained_ids = tuple(sorted((capture.representation_id for capture in item.legacy_captures), key=str))
        values: dict[str, Any] = {
            "native_core_id": core_id,
            "legacy_snapshot_id": request.legacy_snapshot_id,
            "legacy_source_namespace_id": request.legacy_source_namespace_id,
            "object_id": source["object_id"], "eid": request.eid,
            "r1_revision_id": request.expected_r1_revision_id,
            "r2_revision_id": request.expected_r2_revision_id,
            "b2_operation_id": r2["operation_id"], "b2_transition_id": r2["transition_id"],
            "runtime_order_ordinal": source["runtime_order_ordinal"],
            "scope_plan_digest": readiness.scope_plan_digest,
            "embedding_input_field": input_value.field,
            "embedding_input_digest": input_value.digest,
            "embedding_input_text": input_value.text,
            "target_lane": request.target_lane,
            "embedder_provider": getattr(embedder, "provider"),
            "embedder_model": getattr(embedder, "model"),
            "embedder_dimension": getattr(embedder, "dim"),
            "legacy_vector_strategy": strategy,
            "retained_legacy_capture_ids": retained_ids,
            "idempotency_namespace_id": request.idempotency_namespace_id,
        }
        representation_id = _deterministic_native_id(_plan_identity(values))
        return PreparedRuntimeReembeddingBootstrap(
            **values, representation_id=representation_id, _marker=_PREPARED,
        )

    def _revalidate_prepared(
        self,
        request: MigrationRuntimeReembeddingBootstrapRequest,
        embedder: Embedder,
        plan: PreparedRuntimeReembeddingBootstrap,
    ) -> None:
        fresh = self._prepare(request, embedder)
        if _plan_identity(_plan_values(fresh)) != _plan_identity(_plan_values(plan)):
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_PREPARED_FACTS_CHANGED")

    def _existing_target(self, plan: PreparedRuntimeReembeddingBootstrap) -> RepresentationMetadata | None:
        rows = self._connection.execute(
            """
            SELECT representation_id FROM representations
             WHERE source_kind='OBJECT_REVISION' AND source_object_id=?
               AND source_object_revision_id=? AND source_object_revision_ordinal=2
               AND representation_class=? AND generation=?
            """,
            (
                native_id_to_bytes(plan.object_id), native_id_to_bytes(plan.r2_revision_id),
                plan.target_lane.representation_class, plan.target_lane.generation,
            ),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1 or UUID(bytes=rows[0][0]) != plan.representation_id:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_COMPETING_CURRENT_COMPAT_EMBEDDING")
        self._validate_existing_target_contract(plan)
        return NativeRepresentationService(self._connection).get_representation_metadata(plan.representation_id)

    def _validate_existing_target_contract(self, plan: PreparedRuntimeReembeddingBootstrap) -> None:
        rows = self._connection.execute(
            """
            SELECT operation.canonical_intent_json
              FROM operation_outputs output
              JOIN operations operation ON operation.operation_id=output.operation_id
             WHERE output.output_kind='REPRESENTATION' AND output.output_role='REPRESENTATION_PENDING'
               AND output.representation_id=?
            """, (native_id_to_bytes(plan.representation_id),)
        ).fetchall()
        if len(rows) != 1:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_EXISTING_TARGET_CONTRACT_INVALID")
        try:
            stored = json.loads(rows[0][0])["administrative_derivation"]
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_EXISTING_TARGET_CONTRACT_INVALID") from exc
        if not isinstance(stored, dict) or any(
            stored.get(key) != value for key, value in _administrative_contract(plan).items()
        ):
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_EXISTING_TARGET_CONTRACT_INVALID")

    def _observe_vector(self, embedder: Embedder, plan: PreparedRuntimeReembeddingBootstrap) -> _ObservedVector:
        try:
            raw = embedder.embed(plan.embedding_input_text)
        except Exception as exc:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_TARGET_EMBEDDER_FAILED") from exc
        try:
            vector = np.asarray(raw, dtype=np.float32).reshape(-1)
        except (TypeError, ValueError) as exc:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_TARGET_EMBEDDER_OUTPUT_INVALID") from exc
        if vector.size != plan.target_lane.dimension:
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_TARGET_EMBEDDER_DIMENSION_INVALID")
        if not bool(np.all(np.isfinite(vector))):
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_TARGET_EMBEDDER_NONFINITE")
        payload = vector.tobytes()
        return _ObservedVector(payload, hashlib.sha256(payload).hexdigest())

    def _establish_or_match_expectation(
        self,
        representations: NativeRepresentationService,
        request: MigrationRuntimeReembeddingBootstrapRequest,
        plan: PreparedRuntimeReembeddingBootstrap,
        payload_sha256: str,
    ):
        expected = bytes.fromhex(payload_sha256)
        try:
            expectation = representations.get_representation_integrity_expectation(plan.representation_id)
        except SubstrateObjectNotFound:
            return representations.establish_representation_integrity_expectation(
                idempotency_namespace_id=request.idempotency_namespace_id,
                idempotency_key=_phase_key(request, "EXPECTATION"),
                request=RepresentationIntegrityExpectationRequest(
                    representation_id=plan.representation_id,
                    algorithm_id=INTEGRITY_ALGORITHM_SHA256,
                    expected_value=expected,
                    value_encoding=INTEGRITY_VALUE_ENCODING_RAW,
                ),
            )
        if (
            expectation.algorithm_id != INTEGRITY_ALGORITHM_SHA256
            or expectation.value_encoding != INTEGRITY_VALUE_ENCODING_RAW
            or expectation.expected_value != expected
        ):
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_REEMBED_OUTPUT_NOT_BYTE_STABLE")
        return expectation

    def _read_current_qualified(
        self, plan: PreparedRuntimeReembeddingBootstrap
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
        ):
            raise MigrationRuntimeReembeddingBootstrapRefused("B3B_COMPETING_CURRENT_COMPAT_EMBEDDING")
        return witness

    @staticmethod
    def _result_from_witness(
        plan: PreparedRuntimeReembeddingBootstrap,
        witness: QualifiedCompatEmbedding,
    ) -> MigrationRuntimeReembeddingBootstrapResult:
        if witness.expectation_id is None or witness.selected_measurement_id is None:
            raise SubstrateInvariantViolation("qualified B3B reader witness lacks integrity identity")
        return MigrationRuntimeReembeddingBootstrapResult(
            plan.object_id, plan.eid, plan.r1_revision_id, plan.r2_revision_id,
            plan.retained_legacy_capture_ids, witness.representation_id, witness.expectation_id,
            witness.selected_measurement_id, witness.payload_sha256, witness.payload_byte_length,
        )


def _validate_target_lane(lane: NativeRepresentationLane) -> None:
    if not isinstance(lane.provider, str) or not lane.provider or not isinstance(lane.model, str) or not lane.model:
        raise MigrationRuntimeReembeddingBootstrapRefused("B3B_TARGET_LANE_INVALID")
    expected = (
        COMPAT_EMBEDDING_REPRESENTATION_CLASS, COMPAT_EMBEDDING_GENERATION,
        COMPAT_EMBEDDING_DERIVATION_CONTRACT, COMPAT_EMBEDDING_ENCODING, COMPAT_EMBEDDING_DTYPE,
    )
    actual = (
        lane.representation_class, lane.generation, lane.derivation_contract_version,
        lane.encoding_id, lane.dtype,
    )
    if actual != expected or not isinstance(lane.dimension, int) or isinstance(lane.dimension, bool) or lane.dimension < 1:
        raise MigrationRuntimeReembeddingBootstrapRefused("B3B_TARGET_LANE_INVALID")


def _validate_embedder_identity(embedder: Embedder, lane: NativeRepresentationLane) -> None:
    if getattr(embedder, "provider", None) != lane.provider:
        raise MigrationRuntimeReembeddingBootstrapRefused("B3B_TARGET_EMBEDDER_PROVIDER_UNQUALIFIED")
    if getattr(embedder, "model", None) != lane.model:
        raise MigrationRuntimeReembeddingBootstrapRefused("B3B_TARGET_EMBEDDER_MODEL_UNQUALIFIED")
    dimension = getattr(embedder, "dim", None)
    if not isinstance(dimension, int) or isinstance(dimension, bool) or dimension != lane.dimension:
        raise MigrationRuntimeReembeddingBootstrapRefused("B3B_TARGET_EMBEDDER_DIMENSION_UNQUALIFIED")
    if not callable(getattr(embedder, "embed", None)):
        raise MigrationRuntimeReembeddingBootstrapRefused("B3B_TARGET_EMBEDDER_IDENTITY_UNQUALIFIED")


def _administrative_contract(plan: PreparedRuntimeReembeddingBootstrap) -> dict[str, object]:
    return {
        "kind": "MIGRATION_REEMBED_BOOTSTRAP", "bootstrap_contract": _BOOTSTRAP_CONTRACT,
        "core_id": str(plan.native_core_id), "snapshot_id": str(plan.legacy_snapshot_id),
        "source_namespace_id": str(plan.legacy_source_namespace_id), "object_id": str(plan.object_id),
        "eid": plan.eid, "r1_revision_id": str(plan.r1_revision_id),
        "r2_revision_id": str(plan.r2_revision_id), "b2_operation_id": str(plan.b2_operation_id),
        "b2_transition_id": str(plan.b2_transition_id), "runtime_order_ordinal": plan.runtime_order_ordinal,
        "scope_plan_digest": plan.scope_plan_digest,
        "embedding_input_field": plan.embedding_input_field,
        "embedding_input_digest": plan.embedding_input_digest,
        "target_lane": _lane_intent(plan.target_lane),
        "embedder_provider": plan.embedder_provider, "embedder_model": plan.embedder_model,
        "embedder_dimension": plan.embedder_dimension,
        "legacy_vector_strategy": plan.legacy_vector_strategy.value,
        "retained_legacy_capture_ids": [str(value) for value in plan.retained_legacy_capture_ids],
        "idempotency_namespace_id": str(plan.idempotency_namespace_id),
    }


def _administrative_intent(plan: PreparedRuntimeReembeddingBootstrap, payload_sha256: str) -> dict[str, object]:
    return {
        **_administrative_contract(plan),
        "initial_observed_payload_sha256": payload_sha256,
        "initial_observed_payload_byte_length": plan.target_lane.dimension * np.dtype(np.float32).itemsize,
    }


def _request_identity(
    request: MigrationRuntimeReembeddingBootstrapRequest, embedder: Embedder
) -> dict[str, object]:
    return {
        "bootstrap_contract": _BOOTSTRAP_CONTRACT,
        "core_id": str(request.expected_native_core_id),
        "snapshot_id": str(request.legacy_snapshot_id),
        "source_namespace_id": str(request.legacy_source_namespace_id),
        "eid": request.eid, "r1_revision_id": str(request.expected_r1_revision_id),
        "r2_revision_id": str(request.expected_r2_revision_id),
        "scope_plan_digest": _scope_plan_digest(request.scope_plans),
        "target_lane": _lane_intent(request.target_lane),
        "embedder_provider": getattr(embedder, "provider"),
        "embedder_model": getattr(embedder, "model"),
        "embedder_dimension": getattr(embedder, "dim"),
        "idempotency_namespace_id": str(request.idempotency_namespace_id),
    }


def _plan_values(plan: PreparedRuntimeReembeddingBootstrap) -> dict[str, Any]:
    return {
        "native_core_id": plan.native_core_id, "legacy_snapshot_id": plan.legacy_snapshot_id,
        "legacy_source_namespace_id": plan.legacy_source_namespace_id, "object_id": plan.object_id,
        "eid": plan.eid, "r1_revision_id": plan.r1_revision_id, "r2_revision_id": plan.r2_revision_id,
        "b2_operation_id": plan.b2_operation_id, "b2_transition_id": plan.b2_transition_id,
        "runtime_order_ordinal": plan.runtime_order_ordinal, "scope_plan_digest": plan.scope_plan_digest,
        "embedding_input_field": plan.embedding_input_field,
        "embedding_input_digest": plan.embedding_input_digest,
        "embedding_input_text": plan.embedding_input_text, "target_lane": plan.target_lane,
        "embedder_provider": plan.embedder_provider, "embedder_model": plan.embedder_model,
        "embedder_dimension": plan.embedder_dimension,
        "legacy_vector_strategy": plan.legacy_vector_strategy,
        "retained_legacy_capture_ids": plan.retained_legacy_capture_ids,
        "idempotency_namespace_id": plan.idempotency_namespace_id,
    }


def _plan_identity(values: dict[str, Any]) -> dict[str, object]:
    return {
        "bootstrap_contract": _BOOTSTRAP_CONTRACT, "core_id": str(values["native_core_id"]),
        "snapshot_id": str(values["legacy_snapshot_id"]),
        "source_namespace_id": str(values["legacy_source_namespace_id"]),
        "object_id": str(values["object_id"]), "eid": values["eid"],
        "r1_revision_id": str(values["r1_revision_id"]), "r2_revision_id": str(values["r2_revision_id"]),
        "b2_operation_id": str(values["b2_operation_id"]),
        "b2_transition_id": str(values["b2_transition_id"]),
        "runtime_order_ordinal": values["runtime_order_ordinal"],
        "scope_plan_digest": values["scope_plan_digest"],
        "embedding_input_field": values["embedding_input_field"],
        "embedding_input_digest": values["embedding_input_digest"],
        "target_lane": _lane_intent(values["target_lane"]),
        "embedder_provider": values["embedder_provider"], "embedder_model": values["embedder_model"],
        "embedder_dimension": values["embedder_dimension"],
        "legacy_vector_strategy": values["legacy_vector_strategy"].value,
        "retained_legacy_capture_ids": [str(value) for value in values["retained_legacy_capture_ids"]],
        "idempotency_namespace_id": str(values["idempotency_namespace_id"]),
    }


def _lane_intent(lane: NativeRepresentationLane) -> dict[str, object]:
    return {
        "provider": lane.provider, "model": lane.model, "dimension": lane.dimension,
        "representation_class": lane.representation_class, "generation": lane.generation,
        "derivation_contract_version": lane.derivation_contract_version, "encoding_id": lane.encoding_id,
        "dtype": lane.dtype,
    }


def _scope_plan_digest(plans: tuple[MigrationRuntimeScopePlan, ...]) -> str:
    values = sorted((plan.intent() for plan in plans), key=canonical_intent_text)
    return hashlib.sha256(canonical_intent_text(values).encode("utf-8")).hexdigest()


def _phase_key(request: MigrationRuntimeReembeddingBootstrapRequest, phase: str) -> str:
    return f"B3B_REEMBED_BOOTSTRAP:{phase}:{request.idempotency_key}"


def _deterministic_native_id(intent: dict[str, object]) -> UUID:
    raw = bytearray(hashlib.sha256(canonical_intent_text(intent).encode("utf-8")).digest()[:16])
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    return UUID(bytes=bytes(raw))


__all__ = [
    "MigrationRuntimeReembeddingBootstrapRefused",
    "MigrationRuntimeReembeddingBootstrapRequest",
    "MigrationRuntimeReembeddingBootstrapResult",
    "NativeMigrationRuntimeReembeddingBootstrapService",
    "PreparedRuntimeReembeddingBootstrap",
]
