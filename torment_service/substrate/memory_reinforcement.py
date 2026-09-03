"""Unwired A3C3 native reinforcement and representation continuity.

Selection belongs to existing Fabric logic.  This module accepts an already
selected current memory revision and its exact current qualified embedding,
publishes one source successor, then continues the separate representation
workflow with byte-for-byte historical embedding carry-forward.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import sqlite3
from typing import Any, Callable, Literal, Mapping
from uuid import UUID

from .canonical_intent import canonical_intent_text
from .compat_embedding_reader import (
    NativeCompatEmbeddingReader,
    QualifiedCompatEmbedding,
)
from .errors import (
    SubstrateIdempotencyConflict,
    SubstrateInvariantViolation,
    SubstrateObjectNotFound,
    SubstrateRevisionConflict,
)
from .ids import generate_native_id, native_id_to_bytes
from .native_srg_runtime import SRGSuccessorMaterialization
from .native_world_runtime import WorldDiagnosticSuccessorMaterialization
from .object_revision_governance import (
    NativeMemoryGovernanceFacts,
    NativeObjectRevisionGovernanceService,
    _insert_published_governance_for_qualification,
)
from .objects import NativeObjectService, ObjectState, SubstrateTx, execute_semantic
from .provenance import NativeProvenanceRecord
from .representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from .schema import require_current_schema


_MEMORY_OBJECT_KIND = "LEGACY_CORE_NODE"
_SOURCE_OPERATION_KIND = "NATIVE_MEMORY_REINFORCEMENT_SOURCE"
_SOURCE_TRANSITION_KIND = "NATIVE_MEMORY_REINFORCEMENT"


class StaleReinforcementPlanError(SubstrateRevisionConflict):
    """The selected R1/E1 pair no longer matches qualified current state."""


@dataclass(frozen=True)
class NativeMemoryReinforcementRequest:
    """Caller-stable facts for a memory selected outside A3C3."""

    legacy_source_namespace_id: UUID
    eid: int
    expected_revision_id: UUID
    expected_representation_id: UUID
    idempotency_namespace_id: UUID
    idempotency_key: str
    reinforcement_step: int
    last_reinforced_ts: int
    expected_dimension: int
    last_tool_refresh_ts: int | None = None
    direct_ingest_provenance_backfill: NativeProvenanceRecord | None = None
    routing_input_digest: str | None = None
    srg_materialization: SRGSuccessorMaterialization | None = None
    world_diagnostic_materialization: WorldDiagnosticSuccessorMaterialization | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "legacy_source_namespace_id", "expected_revision_id",
            "expected_representation_id", "idempotency_namespace_id",
        ):
            if not isinstance(getattr(self, field_name), UUID):
                raise ValueError(f"{field_name} must be a UUID")
        if not isinstance(self.idempotency_key, str) or not self.idempotency_key:
            raise ValueError("idempotency_key must be non-empty text")
        for field_name in (
            "eid", "reinforcement_step", "last_reinforced_ts", "expected_dimension",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if self.expected_dimension < 1:
            raise ValueError("expected_dimension must be a positive integer")
        if self.last_tool_refresh_ts is not None and (
            not isinstance(self.last_tool_refresh_ts, int)
            or isinstance(self.last_tool_refresh_ts, bool)
            or self.last_tool_refresh_ts < 0
        ):
            raise ValueError("last_tool_refresh_ts must be a non-negative integer when supplied")
        if self.direct_ingest_provenance_backfill is not None and not isinstance(
            self.direct_ingest_provenance_backfill, NativeProvenanceRecord
        ):
            raise ValueError("direct_ingest_provenance_backfill must be NativeProvenanceRecord when supplied")
        if self.routing_input_digest is not None and (
            not isinstance(self.routing_input_digest, str)
            or len(self.routing_input_digest) != 64
            or any(character not in "0123456789abcdef" for character in self.routing_input_digest)
        ):
            raise ValueError("routing_input_digest must be a lowercase SHA-256 hex digest when supplied")
        if self.srg_materialization is not None and not isinstance(
            self.srg_materialization, SRGSuccessorMaterialization
        ):
            raise ValueError("srg_materialization must be SRGSuccessorMaterialization when supplied")
        if self.world_diagnostic_materialization is not None and not isinstance(
            self.world_diagnostic_materialization, WorldDiagnosticSuccessorMaterialization
        ):
            raise ValueError(
                "world_diagnostic_materialization must be WorldDiagnosticSuccessorMaterialization when supplied"
            )


@dataclass(frozen=True)
class ReinforcementPatch:
    """Exact legacy-equivalent fields applied to one immutable successor."""

    values: Mapping[str, Any]
    is_tool_result: bool


@dataclass(frozen=True)
class NativeMemoryReinforcementSourceResult:
    memory_object_id: UUID
    predecessor_revision_id: UUID
    predecessor_revision_ordinal: int
    revision_id: UUID
    revision_ordinal: int
    eid: int
    transition_id: UUID
    operation_id: UUID
    e1_witness: QualifiedCompatEmbedding


@dataclass(frozen=True)
class NativeMemoryReinforcementResult:
    """Complete A3C3 source and representation operation identities."""

    source: NativeMemoryReinforcementSourceResult
    e1_representation_id: UUID
    e2_representation_id: UUID
    e2_expectation_id: UUID
    pending_operation_id: UUID
    expectation_operation_id: UUID
    ready_operation_id: UUID


@dataclass(frozen=True)
class _SourcePlan:
    request: NativeMemoryReinforcementRequest
    object_id: UUID
    revision_ordinal: int
    state: ObjectState
    governance: NativeMemoryGovernanceFacts
    provenance_source_channel: str | None
    provenance_backfill: NativeProvenanceRecord | None
    patch: ReinforcementPatch
    e1_witness: QualifiedCompatEmbedding
    srg_materialization: SRGSuccessorMaterialization | None
    world_diagnostic_materialization: WorldDiagnosticSuccessorMaterialization | None


class NativeMemoryReinforcementService:
    """v1.1 native-only reinforcement; deliberately not wired into Fabric."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        require_current_schema(connection)
        self._connection = connection
        self._objects = NativeObjectService(connection)
        self._governance = NativeObjectRevisionGovernanceService(connection)
        self._embeddings = NativeCompatEmbeddingReader(connection)
        self._representations = NativeRepresentationService(connection)

    def reinforce(
        self,
        request: NativeMemoryReinforcementRequest,
        *,
        _test_stop_after: Literal["source", "pending", "expectation"] | None = None,
        _test_source_fail_after: Literal["revision", "governance"] | None = None,
        _test_omit_source_effect: bool = False,
        _test_omit_source_output: bool = False,
        _test_omit_governance: bool = False,
        on_source_committed: Callable[[NativeMemoryReinforcementSourceResult], None] | None = None,
    ) -> NativeMemoryReinforcementResult:
        """Publish/recover R2, then independently carry E1 bytes to E2."""
        if not isinstance(request, NativeMemoryReinforcementRequest):
            raise ValueError("a NativeMemoryReinforcementRequest is required")
        source = self._source(
            request,
            _test_fail_after=_test_source_fail_after,
            _test_omit_effect=_test_omit_source_effect,
            _test_omit_output=_test_omit_source_output,
            _test_omit_governance=_test_omit_governance,
        )
        if on_source_committed is not None:
            on_source_committed(source)
        if _test_stop_after == "source":
            raise RuntimeError("forced interruption after committed reinforcement source")

        # R2 is now current.  E1 must be read by its known immutable identity,
        # never selected as current geometry for the memory.
        e1 = self._embeddings.read_historical(source.e1_witness)
        pending = self._representations.create_representation_pending(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=_subkey(request.idempotency_key, "REP_PENDING"),
            request=RepresentationRequest(
                "OBJECT_REVISION", source.memory_object_id, source.revision_id,
                None, None, e1.representation_class, e1.generation,
                e1.derivation_contract_version, e1.encoding_id, e1.dtype,
                e1.dimension, e1.dependencies, None, e1.expected_payload_byte_length,
            ),
        )
        if _test_stop_after == "pending":
            raise RuntimeError("forced interruption after E2 pending publication")
        expectation = self._representations.establish_representation_integrity_expectation(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=_subkey(request.idempotency_key, "REP_EXPECTATION"),
            request=RepresentationIntegrityExpectationRequest(
                pending.representation_id, INTEGRITY_ALGORITHM_SHA256,
                bytes.fromhex(e1.payload_sha256), INTEGRITY_VALUE_ENCODING_RAW,
            ),
        )
        if _test_stop_after == "expectation":
            raise RuntimeError("forced interruption after E2 integrity expectation")
        ready = self._representations.publish_representation_ready(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=_subkey(request.idempotency_key, "REP_READY"),
            request=RepresentationReadyRequest(
                pending.representation_id, e1.representation_class, e1.generation,
                e1.derivation_contract_version, e1.encoding_id, e1.payload_bytes,
            ),
        )
        return NativeMemoryReinforcementResult(
            source=source,
            e1_representation_id=e1.representation_id,
            e2_representation_id=ready.representation_id,
            e2_expectation_id=expectation.expectation_id,
            pending_operation_id=self._operation_id(request, "REP_PENDING"),
            expectation_operation_id=self._operation_id(request, "REP_EXPECTATION"),
            ready_operation_id=self._operation_id(request, "REP_READY"),
        )

    def _source(
        self,
        request: NativeMemoryReinforcementRequest,
        *,
        _test_fail_after: str | None,
        _test_omit_effect: bool,
        _test_omit_output: bool,
        _test_omit_governance: bool,
    ) -> NativeMemoryReinforcementSourceResult:
        source_key = _subkey(request.idempotency_key, "SOURCE")
        prior = self._connection.execute(
            "SELECT operation_id,canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), source_key),
        ).fetchone()
        if prior is not None:
            stored = _intent_mapping(prior[1])
            if stored.get("retry_contract") != _retry_contract(request):
                raise SubstrateIdempotencyConflict("idempotency intent differs")
            recovered = self._source_result_for_operation(prior[0])
            if recovered is None:
                raise SubstrateInvariantViolation("existing reinforcement source operation is incomplete")
            return recovered
        plan = self._prepare_source(request)
        return execute_semantic(
            self._connection,
            request.idempotency_namespace_id,
            source_key,
            _SOURCE_OPERATION_KIND,
            _source_intent(plan),
            self._source_result_for_operation,
            lambda tx: self._commit_source(
                tx, plan, _test_fail_after=_test_fail_after,
                _test_omit_effect=_test_omit_effect,
                _test_omit_output=_test_omit_output,
                _test_omit_governance=_test_omit_governance,
            ),
        )

    def _prepare_source(self, request: NativeMemoryReinforcementRequest) -> _SourcePlan:
        current = self._current_memory(request.legacy_source_namespace_id, request.eid)
        if current["revision_id"] != request.expected_revision_id:
            raise StaleReinforcementPlanError("expected reinforcement predecessor is not current")
        if current["authority_category"] != "NOT_APPLICABLE":
            raise SubstrateInvariantViolation("qualified reinforcement source has authorizing authority")
        governance = self._governance.get_object_revision_governance(
            object_id=current["object_id"], object_revision_id=current["revision_id"],
            object_revision_ordinal=current["revision_ordinal"],
        )
        if governance is None:
            raise SubstrateInvariantViolation("qualified reinforcement requires explicit current governance")
        provenance_id = current["provenance_id"]
        provenance_backfill: NativeProvenanceRecord | None = None
        if provenance_id is None:
            candidate = request.direct_ingest_provenance_backfill
            if candidate is None or candidate.source_channel != "direct_ingest":
                raise SubstrateInvariantViolation(
                    "qualified reinforcement requires structural provenance or direct-ingest backfill"
                )
            provenance_id = generate_native_id()
            provenance_source_channel = candidate.source_channel
            provenance_backfill = candidate
        else:
            provenance = self._connection.execute(
                "SELECT source_channel FROM provenance_records WHERE provenance_id=?",
                (native_id_to_bytes(provenance_id),),
            ).fetchone()
            if provenance is None:
                raise SubstrateInvariantViolation("current reinforcement provenance is missing")
            provenance_source_channel = provenance[0]
        embedding = self._embeddings.read_current(
            current["object_id"], expected_dimension=request.expected_dimension
        )
        if embedding is None or embedding.representation_id != request.expected_representation_id:
            raise StaleReinforcementPlanError("expected qualified current E1 representation is stale")
        patch = realize_reinforcement_patch(
            current["payload"], source_channel=provenance_source_channel,
            reinforcement_step=request.reinforcement_step,
            last_reinforced_ts=request.last_reinforced_ts,
            last_tool_refresh_ts=request.last_tool_refresh_ts,
        )
        materialization = request.srg_materialization
        if materialization is not None and not materialization.validates_predecessor(
            revision_id=current["revision_id"], revision_ordinal=current["revision_ordinal"],
        ):
            raise StaleReinforcementPlanError(
                "SRG materialization predecessor is not the current reinforcement source"
            )
        world_materialization = request.world_diagnostic_materialization
        if world_materialization is not None and not world_materialization.validates_predecessor(
            revision_id=current["revision_id"], revision_ordinal=current["revision_ordinal"],
        ):
            raise StaleReinforcementPlanError(
                "world diagnostic materialization predecessor is not the current reinforcement source"
            )
        state = ObjectState(
            current["identity_namespace_id"], current["semantic_scope_id"], current["object_kind"],
            current["existence_state"], current["lifecycle_state"], current["lifecycle_authoritative"],
            current["governance_state"], current["authority_category"],
            {
                **current["payload"],
                **({} if materialization is None else materialization.payload_contribution()),
                **({} if world_materialization is None else world_materialization.payload_contribution()),
                **dict(patch.values),
            }, "JSON", provenance_id,
        )
        return _SourcePlan(
            request, current["object_id"], current["revision_ordinal"], state,
            governance.facts, provenance_source_channel, provenance_backfill,
            patch, embedding, materialization, world_materialization,
        )

    def _commit_source(
        self,
        tx: SubstrateTx,
        plan: _SourcePlan,
        *,
        _test_fail_after: str | None,
        _test_omit_effect: bool,
        _test_omit_output: bool,
        _test_omit_governance: bool,
    ) -> NativeMemoryReinforcementSourceResult:
        request = plan.request
        current = self._current_memory(request.legacy_source_namespace_id, request.eid)
        if current["object_id"] != plan.object_id or current["revision_id"] != request.expected_revision_id:
            raise StaleReinforcementPlanError("reinforcement predecessor changed before source commit")
        if current["revision_ordinal"] != plan.revision_ordinal:
            raise StaleReinforcementPlanError("reinforcement predecessor ordinal changed before source commit")
        if plan.srg_materialization is not None and not plan.srg_materialization.validates_predecessor(
            revision_id=current["revision_id"], revision_ordinal=current["revision_ordinal"],
        ):
            raise StaleReinforcementPlanError(
                "SRG materialization predecessor changed before source commit"
            )
        if plan.world_diagnostic_materialization is not None and not plan.world_diagnostic_materialization.validates_predecessor(
            revision_id=current["revision_id"], revision_ordinal=current["revision_ordinal"],
        ):
            raise StaleReinforcementPlanError(
                "world diagnostic materialization predecessor changed before source commit"
            )
        current_embedding = self._embeddings.read_current(
            plan.object_id, expected_dimension=request.expected_dimension
        )
        if current_embedding is None or current_embedding.intent() != plan.e1_witness.intent():
            raise StaleReinforcementPlanError("qualified E1 witness changed before source commit")
        governance = self._governance.get_object_revision_governance(
            object_id=plan.object_id, object_revision_id=request.expected_revision_id,
            object_revision_ordinal=plan.revision_ordinal,
        )
        if governance is None or governance.facts != plan.governance:
            raise StaleReinforcementPlanError("current governance changed before source commit")
        expected_predecessor_provenance = (
            None if plan.provenance_backfill is not None else plan.state.provenance_id
        )
        if current["provenance_id"] != expected_predecessor_provenance:
            raise StaleReinforcementPlanError("current provenance changed before source commit")

        if plan.provenance_backfill is not None:
            tx.execute(
                """
                INSERT INTO provenance_records(
                    provenance_id,origin_kind,source_channel,source_role,
                    derivation_status,uncertainty_state,source_time_ns,
                    capture_time_ns,memory_role,descriptive_notes
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (native_id_to_bytes(plan.state.provenance_id), *_provenance_values(plan.provenance_backfill)),
            )

        revision_id, transition_id = _new(), _new()
        revision_ordinal = plan.revision_ordinal + 1
        self._objects._state(plan.state)
        self._objects._revision(
            tx, revision_id, native_id_to_bytes(plan.object_id), revision_ordinal,
            "NATIVE_ORDINARY", native_id_to_bytes(request.expected_revision_id),
            plan.revision_ordinal, plan.state,
        )
        tx.execute(
            "UPDATE objects SET current_revision_id=?,current_revision_ordinal=? WHERE object_id=?",
            (revision_id, revision_ordinal, native_id_to_bytes(plan.object_id)),
        )
        if _test_fail_after == "revision":
            raise RuntimeError("forced reinforcement failure after R2 insertion")
        if not _test_omit_governance:
            _insert_published_governance_for_qualification(
                tx, object_id=native_id_to_bytes(plan.object_id), object_revision_id=revision_id,
                object_revision_ordinal=revision_ordinal, facts=plan.governance,
            )
        if _test_fail_after == "governance":
            raise RuntimeError("forced reinforcement failure after R2 governance")
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (transition_id, tx.operation_id, _SOURCE_TRANSITION_KIND, "NATIVE"),
        )
        if not _test_omit_effect:
            tx.execute(
                "INSERT INTO object_revision_effects VALUES (?,?,?,?)",
                (transition_id, native_id_to_bytes(plan.object_id), revision_id, revision_ordinal),
            )
        if not _test_omit_output:
            tx.execute(
                "INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,object_id,object_revision_id,object_revision_ordinal) VALUES (?,?,?,?,?,?,?)",
                (tx.operation_id, 0, "MEMORY_REINFORCEMENT", "OBJECT", native_id_to_bytes(plan.object_id), revision_id, revision_ordinal),
            )
        tx.transitions.append(transition_id)
        tx.published.append((native_id_to_bytes(plan.object_id), revision_id, revision_ordinal))
        self._validate_source_publication(
            tx, transition_id, plan.object_id, revision_id, revision_ordinal, plan.governance,
        )
        return NativeMemoryReinforcementSourceResult(
            plan.object_id, request.expected_revision_id, plan.revision_ordinal,
            UUID(bytes=revision_id), revision_ordinal, request.eid, UUID(bytes=transition_id),
            UUID(bytes=tx.operation_id), plan.e1_witness,
        )

    def _validate_source_publication(
        self,
        tx: SubstrateTx,
        transition_id: bytes,
        object_id: UUID,
        revision_id: bytes,
        revision_ordinal: int,
        governance: NativeMemoryGovernanceFacts,
    ) -> None:
        object_bytes = native_id_to_bytes(object_id)
        if tx.execute(
            "SELECT 1 FROM object_revision_effects WHERE transition_id=? AND object_id=? AND object_revision_id=? AND object_revision_ordinal=?",
            (transition_id, object_bytes, revision_id, revision_ordinal),
        ).fetchone() is None:
            raise SubstrateInvariantViolation("A3C3 source transition omits its R2 object effect")
        if tx.execute(
            "SELECT output_role,output_kind,object_id,object_revision_id,object_revision_ordinal FROM operation_outputs WHERE operation_id=?",
            (tx.operation_id,),
        ).fetchall() != [("MEMORY_REINFORCEMENT", "OBJECT", object_bytes, revision_id, revision_ordinal)]:
            raise SubstrateInvariantViolation("A3C3 source output does not match R2 publication")
        if tx.execute(
            "SELECT protected,non_shareable,collective_export_blocked,collective_reingest_blocked,decay_accelerated FROM object_revision_governance WHERE object_id=? AND object_revision_id=? AND object_revision_ordinal=?",
            (object_bytes, revision_id, revision_ordinal),
        ).fetchone() != governance.as_storage_tuple():
            raise SubstrateInvariantViolation("A3C3 R2 has no exact governance child")

    def _source_result_for_operation(self, operation_id: bytes) -> NativeMemoryReinforcementSourceResult | None:
        row = self._connection.execute(
            """
            SELECT t.transition_id,o.object_id,o.object_revision_id,o.object_revision_ordinal
            FROM semantic_transitions t
            JOIN operation_outputs o ON o.operation_id=t.operation_id
            WHERE t.operation_id=? AND t.transition_kind=?
              AND o.output_ordinal=0 AND o.output_role='MEMORY_REINFORCEMENT'
              AND o.output_kind='OBJECT'
            """,
            (operation_id, _SOURCE_TRANSITION_KIND),
        ).fetchone()
        intent_row = self._connection.execute(
            "SELECT canonical_intent_json FROM operations WHERE operation_id=?", (operation_id,)
        ).fetchone()
        if row is None or intent_row is None:
            return None
        intent = _intent_mapping(intent_row[0])
        try:
            predecessor = intent["predecessor"]
            request_contract = intent["retry_contract"]
            witness = QualifiedCompatEmbedding.from_intent(intent["e1_witness"], b"")
            return NativeMemoryReinforcementSourceResult(
                UUID(bytes=row[1]), UUID(str(predecessor["revision_id"])),
                int(predecessor["revision_ordinal"]), UUID(bytes=row[2]), row[3],
                int(request_contract["eid"]), UUID(bytes=row[0]), UUID(bytes=operation_id), witness,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SubstrateInvariantViolation("stored reinforcement source result is malformed") from exc

    def _operation_id(self, request: NativeMemoryReinforcementRequest, suffix: str) -> UUID:
        row = self._connection.execute(
            "SELECT operation_id FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), _subkey(request.idempotency_key, suffix)),
        ).fetchone()
        if row is None:
            raise SubstrateInvariantViolation("A3C3 representation operation was not durably created")
        return UUID(bytes=row[0])

    def _current_memory(self, namespace: UUID, eid: int) -> dict[str, Any]:
        rows = self._connection.execute(
            """
            SELECT o.object_id,o.identity_namespace_id,o.object_kind,
                   r.object_revision_id,r.revision_ordinal,r.effective_semantic_scope_id,
                   r.existence_state,r.lifecycle_state,r.lifecycle_authoritative,
                   r.governance_state,r.authority_category,r.provenance_id,
                   r.payload_format,r.payload_text
            FROM legacy_object_aliases a
            JOIN objects o ON o.object_id=a.object_id
            JOIN object_revisions r ON r.object_id=o.object_id
              AND r.object_revision_id=o.current_revision_id
              AND r.revision_ordinal=o.current_revision_ordinal
            WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID' AND a.alias_value=?
            """,
            (native_id_to_bytes(namespace), str(eid)),
        ).fetchall()
        if not rows:
            raise SubstrateObjectNotFound("reinforcement EID alias was not found")
        if len(rows) != 1:
            raise SubstrateInvariantViolation("reinforcement EID alias is ambiguous")
        row = rows[0]
        if row[2] != _MEMORY_OBJECT_KIND:
            raise SubstrateInvariantViolation("reinforcement EID does not target a LEGACY_CORE_NODE")
        if row[12] != "JSON" or row[13] is None:
            raise SubstrateInvariantViolation("reinforcement source payload is not JSON")
        try:
            payload = json.loads(row[13])
        except (TypeError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("reinforcement source payload is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise SubstrateInvariantViolation("reinforcement source payload is not an object")
        return {
            "object_id": UUID(bytes=row[0]), "identity_namespace_id": UUID(bytes=row[1]),
            "object_kind": row[2], "revision_id": UUID(bytes=row[3]),
            "revision_ordinal": row[4], "semantic_scope_id": UUID(bytes=row[5]),
            "existence_state": row[6], "lifecycle_state": row[7],
            "lifecycle_authoritative": bool(row[8]), "governance_state": row[9],
            "authority_category": row[10], "provenance_id": UUID(bytes=row[11]) if row[11] else None,
            "payload": payload,
        }


def realize_reinforcement_patch(
    payload: Mapping[str, Any],
    *,
    source_channel: str | None,
    reinforcement_step: int,
    last_reinforced_ts: int,
    last_tool_refresh_ts: int | None,
) -> ReinforcementPatch:
    """Produce the frozen legacy reinforcement patch without mutation or I/O."""
    if not isinstance(payload, Mapping):
        raise ValueError("current reinforcement payload must be a mapping")
    try:
        old_strength = float(payload.get("strength", 0.5))
        old_count = int(payload.get("reinforcement_count", 0))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("current reinforcement payload is malformed") from exc
    if not math.isfinite(old_strength) or old_count < 0:
        raise ValueError("current reinforcement payload is malformed")
    is_tool_result = source_channel == "tool_result"
    if is_tool_result:
        if last_tool_refresh_ts is None:
            raise ValueError("tool-result reinforcement requires last_tool_refresh_ts")
        strength = round(old_strength, 4)
    else:
        if last_tool_refresh_ts is not None:
            raise ValueError("non-tool reinforcement must not provide last_tool_refresh_ts")
        strength = round(min(0.98, old_strength + (1.0 - old_strength) * 0.3), 4)
    patch: dict[str, Any] = {
        "strength": strength,
        "last_reinforced": reinforcement_step,
        "last_reinforced_ts": last_reinforced_ts,
        "reinforcement_count": old_count + 1,
    }
    if is_tool_result:
        patch["last_tool_refresh_ts"] = last_tool_refresh_ts
    return ReinforcementPatch(patch, is_tool_result)


def _retry_contract(request: NativeMemoryReinforcementRequest) -> dict[str, Any]:
    contract = {
        "legacy_source_namespace_id": str(request.legacy_source_namespace_id),
        "eid": request.eid,
        "expected_revision_id": str(request.expected_revision_id),
        "expected_representation_id": str(request.expected_representation_id),
        "reinforcement_step": request.reinforcement_step,
        "last_reinforced_ts": request.last_reinforced_ts,
        "last_tool_refresh_ts": request.last_tool_refresh_ts,
        "direct_ingest_provenance_backfill": _provenance_intent(
            request.direct_ingest_provenance_backfill
        ),
        "expected_dimension": request.expected_dimension,
        "routing_input_digest": request.routing_input_digest,
    }
    if request.srg_materialization is not None:
        contract["srg_materialization"] = request.srg_materialization.intent()
    if request.world_diagnostic_materialization is not None:
        contract["world_diagnostic_materialization"] = request.world_diagnostic_materialization.intent()
    return contract


def _source_intent(plan: _SourcePlan) -> str:
    return canonical_intent_text({
        "kind": _SOURCE_OPERATION_KIND,
        "retry_contract": _retry_contract(plan.request),
        "predecessor": {
            "object_id": str(plan.object_id),
            "revision_id": str(plan.request.expected_revision_id),
            "revision_ordinal": plan.revision_ordinal,
            "provenance_id": str(plan.state.provenance_id),
            "governance": list(plan.governance.as_storage_tuple()),
        },
        "patch": dict(plan.patch.values),
        "is_tool_result": plan.patch.is_tool_result,
        "provenance_backfill": _provenance_intent(plan.provenance_backfill),
        "e1_witness": plan.e1_witness.intent(),
        "source_state": {
            "identity_namespace_id": str(plan.state.identity_namespace_id),
            "semantic_scope_id": str(plan.state.semantic_scope_id),
            "object_kind": plan.state.object_kind,
            "existence_state": plan.state.existence_state,
            "lifecycle_state": plan.state.lifecycle_state,
            "lifecycle_authoritative": plan.state.lifecycle_authoritative,
            "governance_state": plan.state.governance_state,
            "authority_category": plan.state.authority_category,
            "payload": plan.state.payload,
        },
    })


def _subkey(base: str, suffix: str) -> str:
    return f"NATIVE_REINFORCEMENT:{suffix}:{base}"


def _provenance_values(record: NativeProvenanceRecord) -> tuple[Any, ...]:
    return (
        record.origin_kind, record.source_channel, record.source_role,
        record.derivation_status, record.uncertainty_state, record.source_time_ns,
        record.capture_time_ns, record.memory_role, record.descriptive_notes,
    )


def _provenance_intent(record: NativeProvenanceRecord | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return {
        "origin_kind": record.origin_kind,
        "source_channel": record.source_channel,
        "source_role": record.source_role,
        "derivation_status": record.derivation_status,
        "uncertainty_state": record.uncertainty_state,
        "source_time_ns": record.source_time_ns,
        "capture_time_ns": record.capture_time_ns,
        "memory_role": record.memory_role,
        "descriptive_notes": record.descriptive_notes,
    }


def _intent_mapping(value: str) -> dict[str, Any]:
    try:
        decoded = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise SubstrateInvariantViolation("stored operation intent is malformed") from exc
    if not isinstance(decoded, dict):
        raise SubstrateInvariantViolation("stored operation intent is not an object")
    return decoded


def _new() -> bytes:
    return native_id_to_bytes(generate_native_id())


__all__ = [
    "NativeMemoryReinforcementRequest",
    "NativeMemoryReinforcementResult",
    "NativeMemoryReinforcementService",
    "NativeMemoryReinforcementSourceResult",
    "ReinforcementPatch",
    "SRGSuccessorMaterialization",
    "StaleReinforcementPlanError",
    "realize_reinforcement_patch",
]
