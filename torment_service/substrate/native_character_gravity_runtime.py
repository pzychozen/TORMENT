"""C1B's bounded native Character gravity-correction writer.

This is deliberately a Character-specific writer, not a generic native memory
or motif API.  It creates only the legacy ``drift_correction`` R1 shape, may
apply the ordinary motif decision to that already-created memory, and then
publishes its ordinary compatibility representation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math
import random
import sqlite3
import time
from typing import Any, Callable, Mapping
from uuid import UUID

import numpy as np

from torment_service.character import CharacterSeed, _split_seed_text
from torment_service.character_gravity_runtime import (
    CharacterGravityCorrectionRequest,
    CharacterGravityCorrectionResult,
    CharacterGravityCorrectionStatus,
)
from torment_service.memory_graph import _ensure_lifecycle_envelope
from torment_service.motif_decision import (
    CURRENT_MOTIF_DECISION_POLICY,
    decide_attach_or_create,
    realize_attach_next_state,
    realize_create_next_state,
)
from torment_service.world_runtime import legacy_world_genesis_payload

from .canonical_intent import canonical_intent_text
from .derived_memory import (
    _allocate_eid,
    _embedding_bytes,
    _intent_mapping,
    _new,
    _provenance_values,
)
from .errors import (
    SubstrateConfigurationError,
    SubstrateIdempotencyConflict,
    SubstrateInvariantViolation,
)
from .fabric_native_routing import NativeFabricRoutingScope, NativeMotifProcessOrder
from .ids import native_id_to_bytes
from .memory_runtime_order import allocate_next_runtime_ordinal, publish_runtime_order
from .motif_runtime_reader import NativeMotifRuntimeReader, NativeRuntimeMotif
from .motifs import MotifState, NativeMotifMutationResult, NativeMotifService
from .native_world_runtime import NativeWorldProcessState, NativeWorldRuntime
from .object_revision_governance import (
    NativeMemoryGovernanceFacts,
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
from .runtime_binding import NativeRepresentationLane
from .schema import require_current_schema


_MEMORY_OBJECT_KIND = "LEGACY_CORE_NODE"
_SOURCE_OPERATION_KIND = "NATIVE_CHARACTER_DRIFT_CORRECTION"
_SOURCE_OUTPUT_ROLE = "CHARACTER_DRIFT_CORRECTION"
_MOTIF_OUTCOME_OPERATION_KIND = "NATIVE_CHARACTER_MOTIF_OUTCOME"
_PROVENANCE = NativeProvenanceRecord(
    "CHARACTER_DRIFT_CORRECTION",
    "character_runtime",
    "gravity_correction",
    "runtime_derived",
    "KNOWN",
    None,
    None,
    "drift_correction",
    "Native Character runtime-derived gravity correction",
)


class CharacterCorrectionEmbeddingNotByteStable(SubstrateInvariantViolation):
    """A recovered correction cannot honestly reuse its source intent."""


@dataclass(frozen=True)
class NativeCharacterGravityCorrectionRuntimeConfiguration:
    """Prepared scope and caller-owned lane for one C1B correction path."""

    workspace_id: str
    agent_id: str
    domain_id: str
    parent_native_operation_key: str
    routing_scope: NativeFabricRoutingScope
    representation_lane: NativeRepresentationLane
    embedder: Any = field(repr=False, compare=False)
    now_ts: Callable[[], int] = field(default=lambda: int(time.time()), repr=False, compare=False)
    choose_concept: Callable[[list[str]], str] = field(default=random.choice, repr=False, compare=False)

    def __post_init__(self) -> None:
        for name in ("workspace_id", "agent_id", "domain_id", "parent_native_operation_key"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.routing_scope, NativeFabricRoutingScope):
            raise ValueError("routing_scope must be NativeFabricRoutingScope")
        if not isinstance(self.representation_lane, NativeRepresentationLane):
            raise ValueError("representation_lane must be NativeRepresentationLane")
        if not callable(self.now_ts) or not callable(self.choose_concept):
            raise ValueError("now_ts and choose_concept must be callable")
        if (
            self.routing_scope.runtime_scope.workspace_id != self.workspace_id
            or self.routing_scope.runtime_scope.agent_id != self.agent_id
        ):
            raise ValueError("Character correction configuration does not match its routing scope")
        lane = self.representation_lane
        if getattr(self.embedder, "provider", None) != lane.provider:
            raise SubstrateConfigurationError("Character embedder provider does not match the native runtime lane")
        if getattr(self.embedder, "model", None) != lane.model:
            raise SubstrateConfigurationError("Character embedder model does not match the native runtime lane")
        if getattr(self.embedder, "dim", None) != lane.dimension:
            raise SubstrateConfigurationError("Character embedder dimension does not match the native runtime lane")


@dataclass(frozen=True)
class NativeCharacterCorrectionSourceResult:
    memory_object_id: UUID
    memory_revision_id: UUID
    memory_revision_ordinal: int
    eid: int
    provenance_id: UUID
    transition_id: UUID
    operation_id: UUID
    selected_concept: str
    correction_text: str
    embedding_sha256: str
    created_ts: int


@dataclass(frozen=True)
class NativeCharacterCorrectionResult:
    """Durable identifiers for recovery; this grants no new mutation API."""

    source: NativeCharacterCorrectionSourceResult
    representation_id: UUID
    expectation_id: UUID
    motif_status: str
    motif_result: NativeMotifMutationResult | None = None


class NativeCharacterGravityCorrectionRuntime:
    """The C1B correction sequence, explicitly unwired from production routing."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        configuration: NativeCharacterGravityCorrectionRuntimeConfiguration,
        world_process_state: NativeWorldProcessState,
        motif_process_order: NativeMotifProcessOrder,
    ) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("connection must be an already-open qualified sqlite connection")
        require_current_schema(connection)
        if not isinstance(configuration, NativeCharacterGravityCorrectionRuntimeConfiguration):
            raise ValueError("configuration must be NativeCharacterGravityCorrectionRuntimeConfiguration")
        if not isinstance(world_process_state, NativeWorldProcessState):
            raise ValueError("world_process_state must be NativeWorldProcessState")
        if not isinstance(motif_process_order, NativeMotifProcessOrder):
            raise ValueError("motif_process_order must be NativeMotifProcessOrder")
        self._connection = connection
        self._config = configuration
        self._objects = NativeObjectService(connection)
        self._representations = NativeRepresentationService(connection)
        self._motif_reader = NativeMotifRuntimeReader(connection)
        self._motifs = NativeMotifService(connection)
        self._world = NativeWorldRuntime(
            connection,
            legacy_source_namespace_id=configuration.routing_scope.runtime_scope.legacy_source_namespace_id,
            expected_dimension=configuration.representation_lane.dimension,
            process_state=world_process_state,
        )
        self._motif_process_order = motif_process_order

    def correct_for_post_write(
        self, request: CharacterGravityCorrectionRequest,
    ) -> CharacterGravityCorrectionResult:
        self._assert_request(request)
        drift_score = _drift_score(request.drift)
        if drift_score > -float(request.seed.drift_correction_threshold):
            return CharacterGravityCorrectionResult(CharacterGravityCorrectionStatus.NOT_REQUIRED, False)
        if str(request.drift.get("drift_direction", "stable")) != "away_seed":
            return CharacterGravityCorrectionResult(CharacterGravityCorrectionStatus.NOT_REQUIRED, False)

        # Initialize the process-local world *before* the R1 append so the
        # subsequent registration is the A3D8 fresh-topology append, never a
        # reload-style observation of the correction.
        self._world.ensure_initialized()
        source, fresh_vector = self._source(request, drift_score)
        self._world.register_fresh_created(
            eid=source.eid,
            memory_object_id=source.memory_object_id,
            memory_revision_id=source.memory_revision_id,
            memory_revision_ordinal=source.memory_revision_ordinal,
            born_step=request.step,
        )

        ready = self._ready_metadata(source)
        if ready is not None:
            recovered_status = (
                self._recover_motif_status(source)
                if request.seed.seed_motif_id
                else "MOTIF_SKIPPED"
            )
            return self._native_result(source, ready, recovered_status)

        vector = fresh_vector
        motif_status, motif_result = "MOTIF_SKIPPED", None
        if request.seed.seed_motif_id:
            existing_motif = self._recover_motif_result(source)
            if existing_motif is not None:
                motif_status, motif_result = self._recovered_motif_status(existing_motif), existing_motif
            else:
                if vector is None:
                    vector = self._reembed_stored_source(source)
                motif_status, motif_result = self._best_effort_motif(
                    source=source, request=request, vector=vector,
                )

        if vector is None:
            vector = self._reembed_stored_source(source)
        ready = self._publish_representation(source, vector)
        return self._native_result(source, ready, motif_status, motif_result)

    def _assert_request(self, request: CharacterGravityCorrectionRequest) -> None:
        if not isinstance(request, CharacterGravityCorrectionRequest):
            raise ValueError("request must be CharacterGravityCorrectionRequest")
        if request.workspace_id != self._config.workspace_id or request.agent_id != self._config.agent_id:
            raise SubstrateConfigurationError("Character correction request does not match the qualified native scope")
        if not isinstance(request.seed.seed_id, str) or not request.seed.seed_id:
            raise ValueError("Character correction seed_id must be non-empty")

    def _source(
        self, request: CharacterGravityCorrectionRequest, drift_score: float,
    ) -> tuple[NativeCharacterCorrectionSourceResult, np.ndarray | None]:
        key = self._source_key(request)
        prior = self._connection.execute(
            "SELECT operation_id,canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(self._config.routing_scope.idempotency_namespace_id), key),
        ).fetchone()
        request_contract = self._request_contract(request, drift_score)
        if prior is not None:
            intent = _intent_mapping(prior[1])
            if intent.get("request_contract") != request_contract:
                raise SubstrateIdempotencyConflict("Character correction idempotency intent differs")
            result = self._source_result_for_operation(prior[0])
            if result is None:
                raise SubstrateInvariantViolation("existing Character correction source is incomplete")
            return result, None

        concepts = _split_seed_text(request.seed.seed_text)
        concept = self._config.choose_concept(concepts) if concepts else request.seed.seed_text
        if not isinstance(concept, str) or (concepts and concept not in concepts):
            raise ValueError("Character concept selector must return one existing seed concept")
        correction_text = f"[identity reinforcement] {concept}"
        vector = self._embed(correction_text)
        created_ts = _nonnegative_int(self._config.now_ts(), "now_ts")
        source_intent = self._source_intent(
            request, drift_score, concept, correction_text, vector, created_ts,
        )
        result = execute_semantic(
            self._connection,
            self._config.routing_scope.idempotency_namespace_id,
            key,
            _SOURCE_OPERATION_KIND,
            source_intent,
            self._source_result_for_operation,
            lambda tx: self._commit_source(
                tx, request, drift_score, concept, correction_text, vector, created_ts,
            ),
        )
        return result, vector

    def _commit_source(
        self,
        tx: SubstrateTx,
        request: CharacterGravityCorrectionRequest,
        drift_score: float,
        concept: str,
        correction_text: str,
        vector: np.ndarray,
        created_ts: int,
    ) -> NativeCharacterCorrectionSourceResult:
        scope = self._config.routing_scope
        _assert_source_identities(tx, scope)
        transition_id, provenance_id = _new(), _new()
        tx.execute(
            """INSERT INTO provenance_records(
                   provenance_id,origin_kind,source_channel,source_role,derivation_status,
                   uncertainty_state,source_time_ns,capture_time_ns,memory_role,descriptive_notes
               ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (provenance_id, *_provenance_values(_PROVENANCE)),
        )
        object_id, revision_id = _new(), _new()
        eid = _allocate_eid(tx, scope.runtime_scope.legacy_source_namespace_id)
        state = _source_state(
            scope=scope,
            request=request,
            drift_score=drift_score,
            correction_text=correction_text,
            created_ts=created_ts,
            provenance_id=UUID(bytes=provenance_id),
        )
        self._objects._state(state)
        tx.execute(
            """INSERT INTO objects(
                   object_id,identity_namespace_id,object_kind,creating_transition_id,
                   current_revision_id,current_revision_ordinal,created_at_ns
               ) VALUES (?,?,?,?,?,?,0)""",
            (object_id, native_id_to_bytes(state.identity_namespace_id), state.object_kind,
             transition_id, revision_id, 1),
        )
        self._objects._revision(tx, revision_id, object_id, 1, "NATIVE_CREATION", None, None, state)
        tx.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,'EID',?,?)",
            (native_id_to_bytes(scope.runtime_scope.legacy_source_namespace_id), str(eid), object_id),
        )
        publish_runtime_order(
            tx,
            legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
            object_id=UUID(bytes=object_id),
            runtime_ordinal=allocate_next_runtime_ordinal(tx, scope.runtime_scope.legacy_source_namespace_id),
        )
        _insert_published_governance_for_qualification(
            tx,
            object_id=object_id,
            object_revision_id=revision_id,
            object_revision_ordinal=1,
            facts=NativeMemoryGovernanceFacts(),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (transition_id, tx.operation_id, _SOURCE_OPERATION_KIND, "NATIVE"),
        )
        tx.execute(
            "INSERT INTO object_revision_effects VALUES (?,?,?,?)",
            (transition_id, object_id, revision_id, 1),
        )
        tx.execute(
            """INSERT INTO operation_outputs(
                   operation_id,output_ordinal,output_role,output_kind,
                   object_id,object_revision_id,object_revision_ordinal
               ) VALUES (?,?,?,?,?,?,?)""",
            (tx.operation_id, 0, _SOURCE_OUTPUT_ROLE, "OBJECT", object_id, revision_id, 1),
        )
        _validate_source_publication(tx, transition_id, object_id, revision_id)
        tx.transitions.append(transition_id)
        tx.published.append((object_id, revision_id, 1))
        return NativeCharacterCorrectionSourceResult(
            UUID(bytes=object_id), UUID(bytes=revision_id), 1, eid,
            UUID(bytes=provenance_id), UUID(bytes=transition_id), UUID(bytes=tx.operation_id),
            concept, correction_text, hashlib.sha256(_embedding_bytes(tuple(vector))).hexdigest(), created_ts,
        )

    def _source_result_for_operation(self, operation_id: bytes) -> NativeCharacterCorrectionSourceResult | None:
        row = self._connection.execute(
            """SELECT t.transition_id,o.object_id,o.object_revision_id,o.object_revision_ordinal,
                      r.provenance_id,a.alias_value,op.canonical_intent_json
                 FROM semantic_transitions t
                 JOIN operation_outputs o ON o.operation_id=t.operation_id
                 JOIN object_revisions r ON r.object_id=o.object_id
                   AND r.object_revision_id=o.object_revision_id
                   AND r.revision_ordinal=o.object_revision_ordinal
                 JOIN legacy_object_aliases a ON a.object_id=o.object_id AND a.alias_kind='EID'
                 JOIN operations op ON op.operation_id=t.operation_id
                WHERE t.operation_id=? AND t.transition_kind=? AND o.output_ordinal=0
                  AND o.output_role=? AND o.output_kind='OBJECT'""",
            (operation_id, _SOURCE_OPERATION_KIND, _SOURCE_OUTPUT_ROLE),
        ).fetchone()
        if row is None:
            return None
        try:
            intent = _intent_mapping(row[6])
            selection = intent["selection"]
            embedding = intent["embedding"]
            return NativeCharacterCorrectionSourceResult(
                UUID(bytes=row[1]), UUID(bytes=row[2]), int(row[3]), int(row[5]),
                UUID(bytes=row[4]), UUID(bytes=row[0]), UUID(bytes=operation_id),
                str(selection["concept"]), str(selection["correction_text"]),
                str(embedding["sha256"]), int(intent["created_ts"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SubstrateInvariantViolation("stored Character correction source is malformed") from exc

    def _best_effort_motif(
        self,
        *,
        source: NativeCharacterCorrectionSourceResult,
        request: CharacterGravityCorrectionRequest,
        vector: np.ndarray,
    ) -> tuple[str, NativeMotifMutationResult | None]:
        try:
            scope = self._config.routing_scope
            with self._motif_process_order.locked_catalog(
                reader=self._motif_reader,
                routing_scope=scope,
                domain_id=self._config.domain_id,
            ) as catalog:
                decision = decide_attach_or_create(
                    tuple(item.read_model for item in catalog), vector, 0.50,
                    CURRENT_MOTIF_DECISION_POLICY,
                )
                selected = _selected_motif(decision.selected, catalog)
                key = self._motif_key(request)
                if decision.kind == "ATTACH_EXISTING":
                    if selected is None:
                        raise SubstrateInvariantViolation("Character motif decision selected no current motif")
                    if selected.read_model.member_count + 1 >= 96:
                        return self._record_motif_outcome(
                            source, request, "CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED",
                        ), None
                    aggregate = realize_attach_next_state(
                        decision, agent_id=request.agent_id, last_active_ts=source.created_ts,
                    )
                    prior = self._motifs.get_current_motif(selected.motif_object_id)
                    state = _motif_state(aggregate, scope.runtime_scope.semantic_scope_id, prior.state)
                    result = self._motifs.add_motif_member(
                        idempotency_namespace_id=scope.idempotency_namespace_id,
                        idempotency_key=key,
                        motif_alias_namespace_id=scope.motif_alias_namespace_id,
                        membership_identity_namespace_id=scope.membership_identity_namespace_id,
                        motif_object_id=selected.motif_object_id,
                        expected_motif_revision_id=selected.motif_revision_id,
                        state=state,
                        member_object_id=source.memory_object_id,
                    )
                    return "MOTIF_ATTACHED", result
                runtime_motif_id = _next_runtime_motif_id(
                    self._config.domain_id,
                    tuple(item.read_model.runtime_motif_id for item in catalog),
                )
                aggregate = realize_create_next_state(
                    decision,
                    runtime_motif_id=runtime_motif_id,
                    domain_id=self._config.domain_id,
                    summary=source.correction_text,
                    agent_id=request.agent_id,
                    created_ts=source.created_ts,
                    last_active_ts=source.created_ts,
                )
                state = _motif_state(aggregate, scope.runtime_scope.semantic_scope_id, None)
                result = self._motifs.create_motif_with_member(
                    idempotency_namespace_id=scope.idempotency_namespace_id,
                    idempotency_key=key,
                    motif_identity_namespace_id=scope.motif_identity_namespace_id,
                    membership_identity_namespace_id=scope.membership_identity_namespace_id,
                    motif_alias_namespace_id=scope.motif_alias_namespace_id,
                    state=state,
                    member_object_id=source.memory_object_id,
                )
                self._motif_process_order.append_created(
                    routing_scope=scope,
                    domain_id=self._config.domain_id,
                    runtime_motif_id=runtime_motif_id,
                )
                return "MOTIF_CREATED", result
        except Exception:
            # This mirrors legacy ``gravity_correction`` exactly: motif work is
            # inner best effort and cannot erase or withhold the correction.
            # A lost caller response is different from a failed motif write,
            # though: recover an existing primitive result so the returned
            # status never disagrees with the durable transition.
            try:
                recovered = self._recover_motif_result(source)
            except Exception:
                recovered = None
            if recovered is not None:
                return self._recovered_motif_status(recovered), recovered
            return "MOTIF_FAILED_BEST_EFFORT", None

    def _publish_representation(
        self, source: NativeCharacterCorrectionSourceResult, vector: np.ndarray,
    ):
        payload = _embedding_bytes(tuple(vector))
        scope, lane = self._config.routing_scope, self._config.representation_lane
        pending = self._representations.create_representation_pending(
            idempotency_namespace_id=scope.idempotency_namespace_id,
            idempotency_key=self._representation_key(source, "PENDING"),
            request=RepresentationRequest(
                "OBJECT_REVISION", source.memory_object_id, source.memory_revision_id,
                None, None, lane.representation_class, lane.generation,
                lane.derivation_contract_version, lane.encoding_id, lane.dtype,
                lane.dimension, (), None, len(payload),
            ),
        )
        expectation = self._representations.establish_representation_integrity_expectation(
            idempotency_namespace_id=scope.idempotency_namespace_id,
            idempotency_key=self._representation_key(source, "EXPECTATION"),
            request=RepresentationIntegrityExpectationRequest(
                pending.representation_id, INTEGRITY_ALGORITHM_SHA256,
                hashlib.sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW,
            ),
        )
        ready = self._representations.publish_representation_ready(
            idempotency_namespace_id=scope.idempotency_namespace_id,
            idempotency_key=self._representation_key(source, "READY"),
            request=RepresentationReadyRequest(
                pending.representation_id, lane.representation_class, lane.generation,
                lane.derivation_contract_version, lane.encoding_id, payload,
            ),
        )
        if ready.integrity_expectation_id != expectation.expectation_id:
            raise SubstrateInvariantViolation("Character correction READY does not select its expectation")
        return ready

    def _ready_metadata(self, source: NativeCharacterCorrectionSourceResult):
        lane = self._config.representation_lane
        rows = self._connection.execute(
            """SELECT r.representation_id
                 FROM representations r
                 JOIN representation_current_state state USING(representation_id)
                WHERE r.source_kind='OBJECT_REVISION' AND r.source_object_id=? AND r.source_object_revision_id=?
                  AND r.representation_class=? AND r.generation=?
                  AND r.derivation_contract_version=? AND r.encoding_id=?
                  AND state.readiness='READY' AND state.operational_disposition='USABLE'""",
            (
                native_id_to_bytes(source.memory_object_id), native_id_to_bytes(source.memory_revision_id),
                lane.representation_class, lane.generation, lane.derivation_contract_version, lane.encoding_id,
            ),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise SubstrateInvariantViolation("Character correction source has ambiguous qualified READY representations")
        return self._representations.get_representation_metadata(UUID(bytes=rows[0][0]))

    def _reembed_stored_source(self, source: NativeCharacterCorrectionSourceResult) -> np.ndarray:
        vector = self._embed(source.correction_text)
        observed = hashlib.sha256(_embedding_bytes(tuple(vector))).hexdigest()
        if observed != source.embedding_sha256:
            raise CharacterCorrectionEmbeddingNotByteStable(
                "CHARACTER_CORRECTION_EMBEDDING_NOT_BYTE_STABLE"
            )
        return vector

    def _embed(self, correction_text: str) -> np.ndarray:
        vector = np.asarray(self._config.embedder.embed(correction_text), dtype=np.float32).reshape(-1)
        if vector.size != self._config.representation_lane.dimension or not np.all(np.isfinite(vector)):
            raise SubstrateConfigurationError("Character embedder returned an unqualified vector")
        return np.ascontiguousarray(vector, dtype=np.float32)

    def _recover_motif_result(self, source: NativeCharacterCorrectionSourceResult) -> NativeMotifMutationResult | None:
        row = self._connection.execute(
            "SELECT operation_id FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(self._config.routing_scope.idempotency_namespace_id), self._motif_key_from_source(source)),
        ).fetchone()
        if row is None:
            return None
        if self._operation_kind(row[0]) == _MOTIF_OUTCOME_OPERATION_KIND:
            return None
        result = self._motifs._result_for_operation(row[0])
        if result is None:
            raise SubstrateInvariantViolation("stored Character motif operation is incomplete")
        if self._operation_kind(row[0]) == "NATIVE_MOTIF_CREATE_WITH_MEMBER":
            runtime_id = self._motifs.get_current_motif(result.motif_object_id).state.runtime_motif_id
            # A process restarted after the durable create has no local order
            # yet.  Seed it from the live catalog first; a process that saw
            # the create response instead needs the explicit append below.
            if self._motif_process_order.runtime_ids_for_testing(
                routing_scope=self._config.routing_scope, domain_id=self._config.domain_id,
            ) is None:
                with self._motif_process_order.locked_catalog(
                    reader=self._motif_reader,
                    routing_scope=self._config.routing_scope,
                    domain_id=self._config.domain_id,
                ):
                    pass
            self._motif_process_order.append_created(
                routing_scope=self._config.routing_scope,
                domain_id=self._config.domain_id,
                runtime_motif_id=runtime_id,
            )
        return result

    def _recover_motif_status(self, source: NativeCharacterCorrectionSourceResult) -> str:
        row = self._connection.execute(
            "SELECT operation_id FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(self._config.routing_scope.idempotency_namespace_id), self._motif_key_from_source(source)),
        ).fetchone()
        if row is not None and self._operation_kind(row[0]) == _MOTIF_OUTCOME_OPERATION_KIND:
            return self._motif_outcome_for_operation(row[0])
        result = self._recover_motif_result(source)
        return self._recovered_motif_status(result) if result is not None else "MOTIF_SKIPPED_OR_BEST_EFFORT"

    def _record_motif_outcome(
        self,
        source: NativeCharacterCorrectionSourceResult,
        request: CharacterGravityCorrectionRequest,
        status: str,
    ) -> str:
        if status != "CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED":
            raise ValueError("Character motif outcome is not a permitted bounded result")
        return execute_semantic(
            self._connection,
            self._config.routing_scope.idempotency_namespace_id,
            self._motif_key(request),
            _MOTIF_OUTCOME_OPERATION_KIND,
            canonical_intent_text({
                "kind": _MOTIF_OUTCOME_OPERATION_KIND,
                "source": {
                    "memory_object_id": str(source.memory_object_id),
                    "memory_revision_id": str(source.memory_revision_id),
                    "eid": source.eid,
                },
                "status": status,
            }),
            self._motif_outcome_for_operation,
            lambda _tx: status,
        )

    def _motif_outcome_for_operation(self, operation_id: bytes) -> str:
        row = self._connection.execute(
            "SELECT operation_kind,canonical_intent_json FROM operations WHERE operation_id=?", (operation_id,),
        ).fetchone()
        if row is None or row[0] != _MOTIF_OUTCOME_OPERATION_KIND:
            raise SubstrateInvariantViolation("Character motif outcome is malformed")
        status = _intent_mapping(row[1]).get("status")
        if status != "CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED":
            raise SubstrateInvariantViolation("Character motif outcome is unsupported")
        return status

    def _recovered_motif_status(self, result: NativeMotifMutationResult) -> str:
        return "MOTIF_CREATED" if result.motif_revision_ordinal == 1 else "MOTIF_ATTACHED"

    def _operation_kind(self, operation_id: bytes) -> str:
        row = self._connection.execute("SELECT operation_kind FROM operations WHERE operation_id=?", (operation_id,)).fetchone()
        if row is None or not isinstance(row[0], str):
            raise SubstrateInvariantViolation("Character operation is missing its kind")
        return row[0]

    def _native_result(
        self,
        source: NativeCharacterCorrectionSourceResult,
        ready: Any,
        motif_status: str,
        motif_result: NativeMotifMutationResult | None = None,
    ) -> CharacterGravityCorrectionResult:
        status = (
            CharacterGravityCorrectionStatus.CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED
            if motif_status == "CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED"
            else CharacterGravityCorrectionStatus.APPLIED
        )
        return CharacterGravityCorrectionResult(
            status,
            True,
            correction_identity=NativeCharacterCorrectionResult(
                source, ready.representation_id, ready.integrity_expectation_id, motif_status, motif_result,
            ),
            selected_concept=source.selected_concept,
            correction_text=source.correction_text,
            motif_status=motif_status,
        )

    def _source_key(self, request: CharacterGravityCorrectionRequest) -> str:
        return f"NATIVE_CHARACTER_CORRECTION:SOURCE:{self._child_key(request)}"

    def _motif_key(self, request: CharacterGravityCorrectionRequest) -> str:
        return f"NATIVE_CHARACTER_CORRECTION:MOTIF:{self._child_key(request)}"

    def _motif_key_from_source(self, source: NativeCharacterCorrectionSourceResult) -> str:
        contract = self._source_contract_for(source.operation_id)
        return f"NATIVE_CHARACTER_CORRECTION:MOTIF:{contract['child_key']}"

    def _representation_key(self, source: NativeCharacterCorrectionSourceResult, stage: str) -> str:
        contract = self._source_contract_for(source.operation_id)
        return f"NATIVE_CHARACTER_CORRECTION:REPRESENTATION_{stage}:{contract['child_key']}"

    def _source_contract_for(self, operation_id: UUID) -> Mapping[str, Any]:
        row = self._connection.execute(
            "SELECT canonical_intent_json FROM operations WHERE operation_id=?", (native_id_to_bytes(operation_id),)
        ).fetchone()
        if row is None:
            raise SubstrateInvariantViolation("Character source operation disappeared")
        value = _intent_mapping(row[0]).get("request_contract")
        if not isinstance(value, Mapping) or not isinstance(value.get("child_key"), str):
            raise SubstrateInvariantViolation("Character source request contract is malformed")
        return value

    def _child_key(self, request: CharacterGravityCorrectionRequest) -> str:
        return _child_key(
            self._config.parent_native_operation_key, request.agent_id, request.step, request.seed.seed_id,
        )

    def _request_contract(
        self, request: CharacterGravityCorrectionRequest, drift_score: float,
    ) -> dict[str, Any]:
        lane = self._config.representation_lane
        return {
            "child_key": self._child_key(request),
            "workspace_id": request.workspace_id,
            "agent_id": request.agent_id,
            "domain_id": self._config.domain_id,
            "step": request.step,
            "seed_id": request.seed.seed_id,
            "drift_score": drift_score,
            "drift_direction": str(request.drift.get("drift_direction", "stable")),
            "lane": {
                "provider": lane.provider, "model": lane.model, "dimension": lane.dimension,
                "representation_class": lane.representation_class, "generation": lane.generation,
                "derivation_contract_version": lane.derivation_contract_version,
                "encoding_id": lane.encoding_id, "dtype": lane.dtype,
            },
            "provenance": {
                "origin_kind": _PROVENANCE.origin_kind, "source_channel": _PROVENANCE.source_channel,
                "source_role": _PROVENANCE.source_role, "derivation_status": _PROVENANCE.derivation_status,
            },
            "governance": list(NativeMemoryGovernanceFacts().as_storage_tuple()),
        }

    def _source_intent(
        self,
        request: CharacterGravityCorrectionRequest,
        drift_score: float,
        concept: str,
        correction_text: str,
        vector: np.ndarray,
        created_ts: int,
    ) -> str:
        return canonical_intent_text({
            "kind": _SOURCE_OPERATION_KIND,
            "request_contract": self._request_contract(request, drift_score),
            "selection": {"concept": concept, "correction_text": correction_text},
            "embedding": {
                "provider": self._config.representation_lane.provider,
                "model": self._config.representation_lane.model,
                "dimension": self._config.representation_lane.dimension,
                "sha256": hashlib.sha256(_embedding_bytes(tuple(vector))).hexdigest(),
            },
            "created_ts": created_ts,
        })


def _source_state(
    *,
    scope: NativeFabricRoutingScope,
    request: CharacterGravityCorrectionRequest,
    drift_score: float,
    correction_text: str,
    created_ts: int,
    provenance_id: UUID,
) -> ObjectState:
    payload: dict[str, Any] = {
        "summary": correction_text,
        "type": "drift_correction",
        "memory_class": "core",
        "strength": float(request.seed.drift_gravity_strength),
        "confidence": 0.85,
        "canon": True,
        "created_at": request.step,
        "created_ts": created_ts,
        "last_reinforced": request.step,
        "half_life": float(request.seed.core_half_life),
        "user_id": request.agent_id,
        "seed_id": request.seed.seed_id,
        "tier": "core_identity",
        "corrects_drift_score": drift_score,
        "corrects_at_step": request.step,
    }
    _ensure_lifecycle_envelope(payload)
    payload.update(legacy_world_genesis_payload(payload))
    return ObjectState(
        scope.runtime_scope.identity_namespace_id,
        scope.runtime_scope.semantic_scope_id,
        _MEMORY_OBJECT_KIND,
        "EXISTS",
        "ORDINARY",
        False,
        "DERIVED",
        "NOT_APPLICABLE",
        payload,
        "JSON",
        provenance_id,
    )


def _assert_source_identities(tx: SubstrateTx, scope: NativeFabricRoutingScope) -> None:
    checks = (
        ("legacy source namespace", "legacy_source_namespaces", "legacy_source_namespace_id", scope.runtime_scope.legacy_source_namespace_id),
        ("memory identity namespace", "identity_namespaces", "identity_namespace_id", scope.runtime_scope.identity_namespace_id),
        ("semantic scope", "semantic_scopes", "semantic_scope_id", scope.runtime_scope.semantic_scope_id),
        ("idempotency namespace", "idempotency_namespaces", "idempotency_namespace_id", scope.idempotency_namespace_id),
    )
    for label, table, column, value in checks:
        if tx.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)).fetchone() is None:
            raise SubstrateInvariantViolation(f"Character correction {label} is missing")


def _validate_source_publication(tx: SubstrateTx, transition_id: bytes, object_id: bytes, revision_id: bytes) -> None:
    if tx.execute(
        "SELECT 1 FROM object_revision_effects WHERE transition_id=? AND object_id=? AND object_revision_id=? AND object_revision_ordinal=1",
        (transition_id, object_id, revision_id),
    ).fetchone() is None:
        raise SubstrateInvariantViolation("Character correction transition omits R1 effect")
    if tx.execute(
        "SELECT output_role,output_kind,object_id,object_revision_id,object_revision_ordinal FROM operation_outputs WHERE operation_id=?",
        (tx.operation_id,),
    ).fetchall() != [(_SOURCE_OUTPUT_ROLE, "OBJECT", object_id, revision_id, 1)]:
        raise SubstrateInvariantViolation("Character correction outputs do not match R1")
    if tx.execute(
        """SELECT protected,non_shareable,collective_export_blocked,
                  collective_reingest_blocked,decay_accelerated
             FROM object_revision_governance
            WHERE object_id=? AND object_revision_id=? AND object_revision_ordinal=1""",
        (object_id, revision_id),
    ).fetchone() != NativeMemoryGovernanceFacts().as_storage_tuple():
        raise SubstrateInvariantViolation("Character correction R1 has no exact ordinary governance")


def _drift_score(drift: Mapping[str, Any]) -> float:
    try:
        score = float(drift.get("drift_score", 0.0))
    except (TypeError, ValueError) as exc:
        raise ValueError("drift_score must be finite") from exc
    if not math.isfinite(score):
        raise ValueError("drift_score must be finite")
    return score


def _nonnegative_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field_name} must return a non-negative integer")
    return int(value)


def _child_key(parent: str, agent_id: str, step: int, seed_id: str) -> str:
    digest = hashlib.sha256(canonical_intent_text({
        "parent_native_operation_key": parent,
        "operation_kind": "CHARACTER_DRIFT_CORRECTION",
        "agent_id": agent_id,
        "step": step,
        "seed_id": seed_id,
    }).encode("utf-8")).hexdigest()
    return f"CHARACTER_DRIFT_CORRECTION:{digest}"


def _selected_motif(selected: Any, catalog: tuple[NativeRuntimeMotif, ...]) -> NativeRuntimeMotif | None:
    if selected is None:
        return None
    matches = [item for item in catalog if item.read_model is selected]
    if len(matches) != 1:
        raise SubstrateInvariantViolation("Character motif decision selected no unique native motif")
    return matches[0]


def _motif_state(aggregate: Any, scope_id: UUID, prior: MotifState | None) -> MotifState:
    return MotifState(
        scope_id,
        aggregate.runtime_motif_id,
        aggregate.domain_id,
        aggregate.label,
        aggregate.centroid,
        aggregate.strength,
        aggregate.stability_score,
        aggregate.contributing_agents,
        aggregate.created_ts,
        aggregate.last_active_ts,
        prior.derivation_metadata if prior is not None else None,
        prior.extra_payload if prior is not None else None,
    )


def _next_runtime_motif_id(domain_id: str, runtime_ids: tuple[str, ...]) -> str:
    numbers: list[int] = []
    for value in runtime_ids:
        for item in value.split("_"):
            if item.isdigit():
                numbers.append(int(item))
    return f"motif_{domain_id}_{max(numbers, default=0) + 1:04d}"


__all__ = [
    "CharacterCorrectionEmbeddingNotByteStable",
    "NativeCharacterCorrectionResult",
    "NativeCharacterCorrectionSourceResult",
    "NativeCharacterGravityCorrectionRuntime",
    "NativeCharacterGravityCorrectionRuntimeConfiguration",
]
