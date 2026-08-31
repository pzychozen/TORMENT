"""Bounded native Character seed planting without MemoryGraph or CharacterStore writes."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import sqlite3
import time
from typing import Any, Callable
from uuid import UUID

import numpy as np

from torment_service.character import CharacterSeed, _split_seed_text
from torment_service.memory_graph import _ensure_lifecycle_envelope
from torment_service.motif_decision import (
    CURRENT_MOTIF_DECISION_POLICY, decide_attach_or_create,
    realize_attach_next_state, realize_create_next_state,
)
from torment_service.world_runtime import legacy_world_genesis_payload

from .canonical_intent import canonical_intent_text
from .character_seed_witness import character_seed_definition_digest
from .errors import SubstrateConfigurationError, SubstrateIdempotencyConflict, SubstrateInvariantViolation
from .fabric_native_routing import NativeFabricRoutingScope
from .ids import generate_native_id, native_id_to_bytes
from .memory_runtime_order import allocate_next_runtime_ordinal, publish_runtime_order
from .motif_runtime_reader import NativeMotifRuntimeReader, NativeRuntimeMotif
from .motifs import MotifState, NativeMotifService
from .object_revision_governance import NativeMemoryGovernanceFacts, _insert_published_governance_for_qualification
from .objects import ObjectState, SubstrateTx, execute_semantic
from .provenance import NativeProvenanceRecord
from .representations import (
    INTEGRITY_ALGORITHM_SHA256, INTEGRITY_VALUE_ENCODING_RAW, NativeRepresentationService,
    RepresentationIntegrityExpectationRequest, RepresentationReadyRequest, RepresentationRequest,
)
from .runtime_binding import NativeRepresentationLane
from .schema import require_current_schema


_SOURCE_KIND = "NATIVE_CHARACTER_SEED_PLANT"
_SOURCE_OUTPUT = "CHARACTER_SEED_CANON"


class CharacterSeedPlantRefused(SubstrateInvariantViolation):
    """A fresh seed cannot enter the bounded Character seed profile."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class NativeCharacterSeedPlantRuntimeConfiguration:
    workspace_id: str
    agent_id: str
    domain_id: str
    parent_native_operation_key: str
    routing_scope: NativeFabricRoutingScope
    representation_lane: NativeRepresentationLane
    embedder: Any = field(repr=False, compare=False)
    now_ts: Callable[[], int] = field(default=lambda: int(time.time()), repr=False, compare=False)

    def __post_init__(self) -> None:
        for name in ("workspace_id", "agent_id", "domain_id", "parent_native_operation_key"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.routing_scope, NativeFabricRoutingScope):
            raise ValueError("routing_scope must be NativeFabricRoutingScope")
        if not isinstance(self.representation_lane, NativeRepresentationLane):
            raise ValueError("representation_lane must be NativeRepresentationLane")
        if not callable(self.now_ts):
            raise ValueError("now_ts must be callable")
        if (
            self.routing_scope.runtime_scope.workspace_id != self.workspace_id
            or self.routing_scope.runtime_scope.agent_id != self.agent_id
        ):
            raise ValueError("seed planter configuration does not match routing scope")
        lane = self.representation_lane
        if (
            getattr(self.embedder, "provider", None) != lane.provider
            or getattr(self.embedder, "model", None) != lane.model
            or getattr(self.embedder, "dim", None) != lane.dimension
        ):
            raise SubstrateConfigurationError("Character seed embedder does not match qualified representation lane")


@dataclass(frozen=True)
class NativeCharacterSeedPlantRequest:
    seed: CharacterSeed
    step: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.seed, CharacterSeed):
            raise ValueError("seed must be CharacterSeed")
        if not isinstance(self.step, int) or isinstance(self.step, bool) or self.step < 0:
            raise ValueError("step must be a non-negative integer")


@dataclass(frozen=True)
class NativeCharacterSeedSourceResult:
    object_id: UUID
    revision_id: UUID
    eid: int
    provenance_id: UUID
    representation_id: UUID
    concept_index: int
    concept: str
    payload_sha256: str
    created_ts: int


@dataclass(frozen=True)
class NativeCharacterSeedPlantResult:
    seed_definition_digest: str
    seed_eids: tuple[int, ...]
    seed_motif_id: str
    seed_motif_object_id: UUID
    sources: tuple[NativeCharacterSeedSourceResult, ...]
    state: str = "COMPLETE"


class NativeCharacterSeedPlantRuntime:
    """Explicit multi-concept Character seed writer; no selector or store mutation."""

    def __init__(self, connection: sqlite3.Connection, *, configuration: NativeCharacterSeedPlantRuntimeConfiguration) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("seed planter requires an already-open qualified sqlite connection")
        require_current_schema(connection)
        if not isinstance(configuration, NativeCharacterSeedPlantRuntimeConfiguration):
            raise ValueError("configuration must be NativeCharacterSeedPlantRuntimeConfiguration")
        self._connection = connection
        self._config = configuration
        self._representations = NativeRepresentationService(connection)
        self._motifs = NativeMotifService(connection)
        self._motif_reader = NativeMotifRuntimeReader(connection)

    def plant_seed(
        self, request: NativeCharacterSeedPlantRequest,
        *, _test_interrupt_after_concept: int | None = None,
    ) -> NativeCharacterSeedPlantResult:
        if not isinstance(request, NativeCharacterSeedPlantRequest):
            raise ValueError("request must be NativeCharacterSeedPlantRequest")
        if _test_interrupt_after_concept is not None and (
            not isinstance(_test_interrupt_after_concept, int) or _test_interrupt_after_concept < 0
        ):
            raise ValueError("_test_interrupt_after_concept must be a non-negative integer")
        seed = request.seed
        if seed.owner_agent_id != self._config.agent_id:
            raise CharacterSeedPlantRefused("CHARACTER_SEED_OWNER_AGENT_MISMATCH")
        concepts = tuple(_split_seed_text(seed.seed_text))
        if not concepts:
            raise CharacterSeedPlantRefused("CHARACTER_SEED_CONCEPTS_REQUIRED")
        if len(concepts) >= 96:
            raise CharacterSeedPlantRefused("CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED")
        definition_digest = character_seed_definition_digest(seed)
        sources: list[NativeCharacterSeedSourceResult] = []
        vectors: list[np.ndarray] = []
        for index, concept in enumerate(concepts):
            vector = self._embed(concept)
            source = self._source(request, definition_digest, index, concept, vector)
            ready = self._publish_representation(source, vector)
            sources.append(NativeCharacterSeedSourceResult(
                source.object_id, source.revision_id, source.eid, source.provenance_id,
                ready.representation_id, index, concept, source.payload_sha256, source.created_ts,
            ))
            vectors.append(vector)
            if _test_interrupt_after_concept == index:
                raise RuntimeError("forced interruption after committed Character seed concept")
        motif_id, motif_object_id = self._ensure_seed_motif(request, sources, vectors)
        return NativeCharacterSeedPlantResult(
            definition_digest, tuple(source.eid for source in sources), motif_id,
            motif_object_id, tuple(sources),
        )

    @dataclass(frozen=True)
    class _Source:
        object_id: UUID
        revision_id: UUID
        eid: int
        provenance_id: UUID
        operation_id: UUID
        concept_index: int
        concept: str
        payload_sha256: str
        created_ts: int

    def _source(self, request: NativeCharacterSeedPlantRequest, definition_digest: str,
                index: int, concept: str, vector: np.ndarray) -> "NativeCharacterSeedPlantRuntime._Source":
        key = self._source_key(request.seed.seed_id, index)
        prior = self._connection.execute(
            "SELECT operation_id,canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(self._config.routing_scope.idempotency_namespace_id), key),
        ).fetchone()
        if prior is not None:
            try:
                stored = json.loads(prior[1])
            except (TypeError, json.JSONDecodeError) as exc:
                raise SubstrateInvariantViolation("stored Character seed source intent is malformed") from exc
            if _source_retry_contract(stored) != _source_retry_contract(json.loads(
                self._source_intent(request, definition_digest, index, concept, vector, created_ts=0)
            )):
                raise SubstrateIdempotencyConflict("Character seed source idempotency intent differs")
            recovered = self._source_result(prior[0])
            if recovered is None:
                raise SubstrateInvariantViolation("stored Character seed source is incomplete")
            return recovered
        # The timestamp is part of the durable semantic intent and payload.  Generate it
        # once so a successful source transition cannot record two different values.
        created_ts = self._now()
        intent = self._source_intent(request, definition_digest, index, concept, vector, created_ts)
        return execute_semantic(
            self._connection, self._config.routing_scope.idempotency_namespace_id, key,
            _SOURCE_KIND, intent, self._source_result,
            lambda tx: self._commit_source(
                tx, request, definition_digest, index, concept, vector, created_ts
            ),
        )

    def _commit_source(self, tx: SubstrateTx, request: NativeCharacterSeedPlantRequest,
                       definition_digest: str, index: int, concept: str, vector: np.ndarray,
                       created_ts: int) -> "NativeCharacterSeedPlantRuntime._Source":
        self._assert_identities(tx)
        provenance = _seed_provenance(request.seed, definition_digest, index)
        provenance_id, object_id, revision_id, transition_id = (
            native_id_to_bytes(generate_native_id()), native_id_to_bytes(generate_native_id()),
            native_id_to_bytes(generate_native_id()), native_id_to_bytes(generate_native_id()),
        )
        tx.execute(
            """INSERT INTO provenance_records(provenance_id,origin_kind,source_channel,source_role,
                   derivation_status,uncertainty_state,source_time_ns,capture_time_ns,memory_role,descriptive_notes)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (provenance_id, *_provenance_values(provenance)),
        )
        state = _seed_state(
            self._config.routing_scope, self._config.agent_id, request, index, concept,
            created_ts, UUID(bytes=provenance_id)
        )
        eid = _allocate_eid(tx, self._config.routing_scope.runtime_scope.legacy_source_namespace_id)
        tx.execute(
            """INSERT INTO objects(object_id,identity_namespace_id,object_kind,creating_transition_id,
                   current_revision_id,current_revision_ordinal,created_at_ns) VALUES (?,?,?,?,?,?,0)""",
            (object_id, native_id_to_bytes(state.identity_namespace_id), "LEGACY_CORE_NODE", transition_id, revision_id, 1),
        )
        lifecycle = state.payload["lifecycle_status"]
        tx.execute(
            """INSERT INTO object_revisions(object_revision_id,object_id,revision_ordinal,lineage_kind,
                   predecessor_revision_id,predecessor_revision_ordinal,effective_semantic_scope_id,existence_state,
                   lifecycle_state,lifecycle_authoritative,lifecycle_actor,lifecycle_via,lifecycle_set_at_ns,
                   governance_state,authority_category,provenance_id,payload_format,payload_text,created_at_ns)
               VALUES (?, ?, 1, 'NATIVE_CREATION', NULL, NULL, ?, 'EXISTS', 'PROTECTED', 1,
                       'system', 'canon_set', ?, 'EXPLICIT', 'NOT_APPLICABLE', ?, 'JSON', ?, 0)""",
            (revision_id, object_id, native_id_to_bytes(state.semantic_scope_id),
             int(lifecycle["set_by"]["at"]) * 1_000_000_000, provenance_id,
             canonical_intent_text(state.payload)),
        )
        tx.execute("INSERT INTO legacy_object_aliases VALUES (?,'EID',?,?)", (
            native_id_to_bytes(self._config.routing_scope.runtime_scope.legacy_source_namespace_id), str(eid), object_id,
        ))
        publish_runtime_order(
            tx, legacy_source_namespace_id=self._config.routing_scope.runtime_scope.legacy_source_namespace_id,
            object_id=UUID(bytes=object_id), runtime_ordinal=allocate_next_runtime_ordinal(
                tx, self._config.routing_scope.runtime_scope.legacy_source_namespace_id,
            ),
        )
        _insert_published_governance_for_qualification(
            tx, object_id=object_id, object_revision_id=revision_id, object_revision_ordinal=1,
            facts=NativeMemoryGovernanceFacts(),
        )
        tx.execute("INSERT INTO semantic_transitions VALUES (?,?,?,?,0)", (transition_id, tx.operation_id, _SOURCE_KIND, "NATIVE"))
        tx.execute("INSERT INTO object_revision_effects VALUES (?,?,?,1)", (transition_id, object_id, revision_id))
        tx.execute(
            """INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,
                   object_id,object_revision_id,object_revision_ordinal) VALUES (?,?,?,'OBJECT',?,?,1)""",
            (tx.operation_id, 0, _SOURCE_OUTPUT, object_id, revision_id),
        )
        tx.transitions.append(transition_id)
        tx.published.append((object_id, revision_id, 1))
        return self._Source(
            UUID(bytes=object_id), UUID(bytes=revision_id), eid, UUID(bytes=provenance_id),
            UUID(bytes=tx.operation_id), index, concept, _sha(vector), created_ts,
        )

    def _source_result(self, operation_id: bytes) -> "NativeCharacterSeedPlantRuntime._Source | None":
        row = self._connection.execute(
            """SELECT out.object_id,out.object_revision_id,out.object_revision_ordinal,r.provenance_id,
                      a.alias_value,op.canonical_intent_json
                 FROM operation_outputs out JOIN object_revisions r ON r.object_id=out.object_id
                   AND r.object_revision_id=out.object_revision_id AND r.revision_ordinal=out.object_revision_ordinal
                 JOIN legacy_object_aliases a ON a.object_id=out.object_id AND a.alias_kind='EID'
                 JOIN operations op ON op.operation_id=out.operation_id
                WHERE out.operation_id=? AND out.output_ordinal=0 AND out.output_role=? AND out.output_kind='OBJECT'""",
            (operation_id, _SOURCE_OUTPUT),
        ).fetchall()
        if not row:
            return None
        if len(row) != 1:
            raise SubstrateInvariantViolation("Character seed source recovery is ambiguous")
        value = row[0]
        try:
            intent = json.loads(value[5])
            return self._Source(
                UUID(bytes=value[0]), UUID(bytes=value[1]), int(value[4]), UUID(bytes=value[3]),
                UUID(bytes=operation_id), int(intent["concept_index"]), str(intent["concept"]),
                str(intent["embedding_sha256"]), int(intent["created_ts"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("stored Character seed source is malformed") from exc

    def _publish_representation(self, source: "NativeCharacterSeedPlantRuntime._Source", vector: np.ndarray):
        payload = vector.tobytes(order="C")
        lane = self._config.representation_lane
        pending = self._representations.create_representation_pending(
            idempotency_namespace_id=self._config.routing_scope.idempotency_namespace_id,
            idempotency_key=self._representation_key(source, "PENDING"),
            request=RepresentationRequest(
                "OBJECT_REVISION", source.object_id, source.revision_id, None, None,
                lane.representation_class, lane.generation, lane.derivation_contract_version,
                lane.encoding_id, lane.dtype, lane.dimension, (), None, len(payload),
            ),
        )
        expectation = self._representations.establish_representation_integrity_expectation(
            idempotency_namespace_id=self._config.routing_scope.idempotency_namespace_id,
            idempotency_key=self._representation_key(source, "EXPECTATION"),
            request=RepresentationIntegrityExpectationRequest(
                pending.representation_id, INTEGRITY_ALGORITHM_SHA256, hashlib.sha256(payload).digest(),
                INTEGRITY_VALUE_ENCODING_RAW,
            ),
        )
        ready = self._representations.publish_representation_ready(
            idempotency_namespace_id=self._config.routing_scope.idempotency_namespace_id,
            idempotency_key=self._representation_key(source, "READY"),
            request=RepresentationReadyRequest(
                pending.representation_id, lane.representation_class, lane.generation,
                lane.derivation_contract_version, lane.encoding_id, payload,
            ),
        )
        if ready.integrity_expectation_id != expectation.expectation_id:
            raise SubstrateInvariantViolation("Character seed READY does not select its expectation")
        return ready

    def _ensure_seed_motif(
        self, request: NativeCharacterSeedPlantRequest,
        sources: list[NativeCharacterSeedSourceResult], vectors: list[np.ndarray],
    ) -> tuple[str, UUID]:
        """Apply the same 0.50 attach/create decision as ``plant_seed``.

        Retrieval of a qualified raw vector remains separate from this
        geometry transformation.  Each source has its own durable child
        operation, so a process may resume a partial multi-concept plant
        without inventing a replacement motif topology.
        """
        scope = self._config.routing_scope
        affected: list[UUID] = []
        for source, vector in zip(sources, vectors, strict=True):
            key = self._motif_key(request.seed.seed_id, f"DECISION:{source.concept_index}")
            prior = self._operation_result(key)
            if prior is not None:
                affected.append(prior.motif_object_id)
                continue
            catalog = self._motif_reader.list_runtime_motifs(
                motif_alias_namespace_id=scope.motif_alias_namespace_id,
                domain_id=self._config.domain_id,
                semantic_scope_id=scope.runtime_scope.semantic_scope_id,
            )
            decision = decide_attach_or_create(
                tuple(item.read_model for item in catalog), vector, .50,
                CURRENT_MOTIF_DECISION_POLICY,
            )
            selected = _selected_motif(decision.selected, catalog)
            if decision.kind == "ATTACH_EXISTING":
                if selected is None:
                    raise SubstrateInvariantViolation("Character seed motif decision selected no current motif")
                if selected.read_model.member_count + 1 >= 96:
                    raise CharacterSeedPlantRefused("CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED")
                current = self._motifs.get_current_motif(selected.motif_object_id)
                aggregate = realize_attach_next_state(
                    decision, agent_id=self._config.agent_id, last_active_ts=source.created_ts,
                )
                result = self._motifs.add_motif_member(
                    idempotency_namespace_id=scope.idempotency_namespace_id, idempotency_key=key,
                    motif_alias_namespace_id=scope.motif_alias_namespace_id,
                    membership_identity_namespace_id=scope.membership_identity_namespace_id,
                    motif_object_id=selected.motif_object_id,
                    expected_motif_revision_id=current.motif_revision_id,
                    state=_motif_state_from_aggregate(aggregate, scope.runtime_scope.semantic_scope_id, current.state),
                    member_object_id=source.object_id,
                )
            else:
                runtime_id = _next_runtime_motif_id(
                    self._config.domain_id, tuple(item.read_model.runtime_motif_id for item in catalog),
                )
                aggregate = realize_create_next_state(
                    decision, runtime_motif_id=runtime_id, domain_id=self._config.domain_id,
                    summary=source.concept, agent_id=self._config.agent_id,
                    created_ts=source.created_ts, last_active_ts=source.created_ts,
                )
                result = self._motifs.create_motif_with_member(
                    idempotency_namespace_id=scope.idempotency_namespace_id, idempotency_key=key,
                    motif_identity_namespace_id=scope.motif_identity_namespace_id,
                    membership_identity_namespace_id=scope.membership_identity_namespace_id,
                    motif_alias_namespace_id=scope.motif_alias_namespace_id,
                    state=_motif_state_from_aggregate(aggregate, scope.runtime_scope.semantic_scope_id, None),
                    member_object_id=source.object_id,
                )
            affected.append(result.motif_object_id)

        seed_object_ids = {source.object_id for source in sources}
        # Legacy records the set of motifs affected by the seed loop and uses
        # the greatest seed-member count.  This loop preserves that semantic,
        # with stable source-order tie handling rather than UUID/row order.
        best: tuple[int, UUID, MotifState] | None = None
        for motif_object_id in dict.fromkeys(affected):
            current = self._motifs.get_current_motif(motif_object_id)
            count = sum(
                member.member_object_id in seed_object_ids
                for member in self._motifs.list_current_motif_members(motif_object_id)
            )
            if count and (best is None or count > best[0]):
                best = (count, motif_object_id, current.state)
        if best is None:
            raise SubstrateInvariantViolation("Character seed planting produced no seed motif")
        _count, motif_object_id, state = best
        boost_key = self._motif_key(request.seed.seed_id, "SEED_BASIN_BOOST")
        boosted = self._operation_result(boost_key)
        if boosted is None:
            current = self._motifs.get_current_motif(motif_object_id)
            boosted_state = MotifState(
                current.state.semantic_scope_id, current.state.runtime_motif_id, current.state.domain_id,
                current.state.label, current.state.centroid, min(1.0, max(current.state.strength, .85)),
                min(1.0, max(current.state.stability_score, .90)), current.state.contributing_agents,
                current.state.created_ts, current.state.last_active_ts, current.state.derivation_metadata,
                current.state.extra_payload,
            )
            boosted = self._motifs.advance_motif_state(
                idempotency_namespace_id=scope.idempotency_namespace_id, idempotency_key=boost_key,
                motif_alias_namespace_id=scope.motif_alias_namespace_id, motif_object_id=motif_object_id,
                expected_motif_revision_id=current.motif_revision_id, state=boosted_state,
            )
        final = self._motifs.get_current_motif(boosted.motif_object_id)
        return final.state.runtime_motif_id, boosted.motif_object_id

    def _operation_result(self, idempotency_key: str):
        row = self._connection.execute(
            "SELECT operation_id FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(self._config.routing_scope.idempotency_namespace_id), idempotency_key),
        ).fetchone()
        if row is None:
            return None
        result = self._motifs._result_for_operation(row[0])
        if result is None:
            raise SubstrateInvariantViolation("stored Character seed motif operation is incomplete")
        return result

    def _embed(self, concept: str) -> np.ndarray:
        value = np.asarray(self._config.embedder.embed(concept), dtype=np.float32).reshape(-1)
        if value.size != self._config.representation_lane.dimension or not np.all(np.isfinite(value)):
            raise SubstrateConfigurationError("Character seed embedder returned an unqualified vector")
        return np.ascontiguousarray(value, dtype=np.float32)

    def _now(self) -> int:
        value = self._config.now_ts()
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError("now_ts must return a non-negative integer")
        return value

    def _assert_identities(self, tx: SubstrateTx) -> None:
        scope = self._config.routing_scope
        checks = (
            ("legacy_source_namespaces", "legacy_source_namespace_id", scope.runtime_scope.legacy_source_namespace_id),
            ("identity_namespaces", "identity_namespace_id", scope.runtime_scope.identity_namespace_id),
            ("semantic_scopes", "semantic_scope_id", scope.runtime_scope.semantic_scope_id),
            ("idempotency_namespaces", "idempotency_namespace_id", scope.idempotency_namespace_id),
        )
        for table, column, value in checks:
            if tx.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)).fetchone() is None:
                raise SubstrateInvariantViolation("Character seed routing identity is missing")

    def _source_key(self, seed_id: str, index: int) -> str:
        return f"NATIVE_CHARACTER_SEED:SOURCE:{self._child_key(seed_id)}:{index}"

    def _representation_key(self, source: "NativeCharacterSeedPlantRuntime._Source", stage: str) -> str:
        return (
            f"NATIVE_CHARACTER_SEED:REPRESENTATION_{stage}:"
            f"{self._child_key_for_source(source)}:{source.concept_index}"
        )

    def _motif_key(self, seed_id: str, stage: str) -> str:
        return f"NATIVE_CHARACTER_SEED:MOTIF:{self._child_key(seed_id)}:{stage}"

    def _child_key(self, seed_id: str) -> str:
        return hashlib.sha256(canonical_intent_text({
            "parent_native_operation_key": self._config.parent_native_operation_key,
            "workspace_id": self._config.workspace_id, "agent_id": self._config.agent_id,
            "domain_id": self._config.domain_id, "seed_id": seed_id,
        }).encode("utf-8")).hexdigest()

    def _child_key_for_source(self, source: "NativeCharacterSeedPlantRuntime._Source") -> str:
        row = self._connection.execute("SELECT canonical_intent_json FROM operations WHERE operation_id=?", (native_id_to_bytes(source.operation_id),)).fetchone()
        if row is None:
            raise SubstrateInvariantViolation("Character seed source operation disappeared")
        try:
            return str(json.loads(row[0])["child_key"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("Character seed source child key is malformed") from exc

    def _source_intent(self, request: NativeCharacterSeedPlantRequest, definition_digest: str,
                       index: int, concept: str, vector: np.ndarray, created_ts: int) -> str:
        return canonical_intent_text({
            "kind": _SOURCE_KIND, "child_key": self._child_key(request.seed.seed_id),
            "workspace_id": self._config.workspace_id, "agent_id": self._config.agent_id,
            "domain_id": self._config.domain_id, "step": request.step,
            "seed_id": request.seed.seed_id, "character_name": request.seed.character_name,
            "seed_definition_digest": definition_digest, "concept_index": index, "concept": concept,
            "embedding_sha256": _sha(vector), "created_ts": created_ts,
        })


def _seed_provenance(seed: CharacterSeed, definition_digest: str, index: int) -> NativeProvenanceRecord:
    return NativeProvenanceRecord(
        "CHARACTER_SEED_PLANT", "character_runtime", "seed_canon", "seed_plant", "KNOWN",
        None, None, "seed_canon", canonical_intent_text({
            "character_name": seed.character_name, "seed_concept_index": index,
            "seed_definition_digest": definition_digest, "seed_id": seed.seed_id,
        }),
    )


def _seed_state(scope: NativeFabricRoutingScope, agent_id: str, request: NativeCharacterSeedPlantRequest,
                index: int, concept: str, created_ts: int, provenance_id: UUID) -> ObjectState:
    payload: dict[str, Any] = {
        "summary": concept, "type": "seed_canon", "memory_class": "core", "strength": .95,
        "confidence": .95, "canon": True, "created_at": request.step, "created_ts": created_ts,
        "last_reinforced": request.step, "half_life": float(request.seed.core_half_life),
        "user_id": agent_id, "seed_id": request.seed.seed_id,
        "character_name": request.seed.character_name, "tier": "core_identity", "seed_concept_index": index,
    }
    _ensure_lifecycle_envelope(payload)
    payload.update(legacy_world_genesis_payload(payload))
    return ObjectState(
        scope.runtime_scope.identity_namespace_id, scope.runtime_scope.semantic_scope_id,
        "LEGACY_CORE_NODE", "EXISTS", "PROTECTED", True, "EXPLICIT", "NOT_APPLICABLE",
        payload, "JSON", provenance_id,
    )


def _motif_state_from_aggregate(aggregate: Any, scope_id: UUID, prior: MotifState | None) -> MotifState:
    return MotifState(
        scope_id, aggregate.runtime_motif_id, aggregate.domain_id, aggregate.label,
        aggregate.centroid, aggregate.strength, aggregate.stability_score,
        aggregate.contributing_agents, aggregate.created_ts, aggregate.last_active_ts,
        prior.derivation_metadata if prior is not None else None,
        prior.extra_payload if prior is not None else None,
    )


def _selected_motif(selected: Any, catalog: tuple[NativeRuntimeMotif, ...]) -> NativeRuntimeMotif | None:
    if selected is None:
        return None
    matches = [item for item in catalog if item.read_model is selected]
    if len(matches) != 1:
        raise SubstrateInvariantViolation("Character seed motif decision selected no unique native motif")
    return matches[0]


def _next_runtime_motif_id(domain_id: str, runtime_ids: tuple[str, ...]) -> str:
    numbers: list[int] = []
    for value in runtime_ids:
        for item in value.split("_"):
            if item.isdigit():
                numbers.append(int(item))
    return f"motif_{domain_id}_{max(numbers, default=0) + 1:04d}"


def _allocate_eid(tx: SubstrateTx, namespace: UUID) -> int:
    rows = tx.execute(
        "SELECT alias_value FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID'",
        (native_id_to_bytes(namespace),),
    ).fetchall()
    values: list[int] = []
    for (value,) in rows:
        if not isinstance(value, str) or not value.isdigit() or str(int(value)) != value:
            raise SubstrateInvariantViolation("Character seed EID namespace has a non-canonical alias")
        values.append(int(value))
    return max(values, default=-1) + 1


def _sha(vector: np.ndarray) -> str:
    return hashlib.sha256(vector.tobytes(order="C")).hexdigest()


def _source_retry_contract(value: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "kind", "child_key", "workspace_id", "agent_id", "domain_id", "step", "seed_id",
        "character_name", "seed_definition_digest", "concept_index", "concept", "embedding_sha256",
    )
    try:
        return {key: value[key] for key in keys}
    except (KeyError, TypeError) as exc:
        raise SubstrateInvariantViolation("Character seed source retry contract is malformed") from exc


def _provenance_values(value: NativeProvenanceRecord) -> tuple[object, ...]:
    return (
        value.origin_kind, value.source_channel, value.source_role, value.derivation_status,
        value.uncertainty_state, value.source_time_ns, value.capture_time_ns, value.memory_role,
        value.descriptive_notes,
    )


__all__ = [
    "CharacterSeedPlantRefused", "NativeCharacterSeedPlantRequest", "NativeCharacterSeedPlantResult",
    "NativeCharacterSeedPlantRuntime", "NativeCharacterSeedPlantRuntimeConfiguration",
    "NativeCharacterSeedSourceResult",
]
