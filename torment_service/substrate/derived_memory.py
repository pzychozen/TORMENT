"""Closed native mutation services for default derived memories.

This module deliberately has no generic payload writer.  It owns exactly two
ordinary-memory publications used by the A3D9 qualification boundary:

* a no-motif R1 creation for ``identity_anchor`` and ``mood_drift``; and
* an immutable successor for the closed identity-anchor lifecycle patch.

Both paths use the existing v1.2 object/revision, provenance, governance,
runtime-order, and representation primitives.  Neither path owns a graph,
motif registry, selector, or long-lived connection.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
import sqlite3
from types import MappingProxyType
from typing import Any, Callable, Literal, Mapping
from uuid import UUID

import numpy as np

from torment_service.memory_graph import _ensure_lifecycle_envelope
from torment_service.world_runtime import legacy_world_genesis_payload

from .canonical_intent import canonical_intent_text
from .compat_embedding_reader import NativeCompatEmbeddingReader, QualifiedCompatEmbedding
from .errors import (
    SubstrateIdempotencyConflict,
    SubstrateInvariantViolation,
    SubstrateObjectNotFound,
    SubstrateRevisionConflict,
)
from .ids import generate_native_id, native_id_to_bytes
from .memory_runtime_order import allocate_next_runtime_ordinal, publish_runtime_order
from .native_srg_runtime import SRGSuccessorMaterialization
from .native_world_runtime import WorldDiagnosticSuccessorMaterialization
from .object_revision_governance import (
    NativeMemoryGovernanceFacts,
    NativeObjectRevisionGovernanceService,
    _insert_published_governance_for_qualification,
)
from .objects import NativeObjectService, ObjectState, SubstrateTx, execute_semantic
from .payload_policy import copy_memory_flexible_payload
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
_CREATION_OPERATION_PREFIX = "NATIVE_DERIVED_MEMORY_CREATE"
_SUCCESSOR_OPERATION_KIND = "NATIVE_IDENTITY_ANCHOR_LIFECYCLE"
_SOURCE_ROLE = "DERIVED_MEMORY"


class DerivedMemoryCreateKind(str, Enum):
    """The complete closed set of A3D9 no-motif creation kinds."""

    IDENTITY_ANCHOR_CREATE = "IDENTITY_ANCHOR_CREATE"
    MOOD_DRIFT_CREATE = "MOOD_DRIFT_CREATE"


_CREATE_MEMORY_TYPE = {
    DerivedMemoryCreateKind.IDENTITY_ANCHOR_CREATE: "identity_anchor",
    DerivedMemoryCreateKind.MOOD_DRIFT_CREATE: "mood_drift",
}


class StaleDerivedMemoryPlanError(SubstrateRevisionConflict):
    """A typed derived successor no longer has its qualified predecessor."""


@dataclass(frozen=True)
class NativeDerivedMemoryCreationRequest:
    """Already-decided inputs for one typed, no-motif derived R1.

    ``operation_kind`` is an enum rather than an arbitrary text field.  The
    public request deliberately has no links, motif fields, lifecycle fields,
    governance-state field, or authority field: those are fixed by the
    legacy-derived contract.
    """

    operation_kind: DerivedMemoryCreateKind
    legacy_source_namespace_id: UUID
    memory_identity_namespace_id: UUID
    semantic_scope_id: UUID
    idempotency_namespace_id: UUID
    idempotency_key: str
    summary: str
    strength: float
    confidence: float
    half_life_days: float
    user_id: str
    logical_step: int
    created_ts: int
    payload_fields: Mapping[str, Any]
    provenance: NativeProvenanceRecord
    governance: NativeMemoryGovernanceFacts
    embedding: Any
    expected_dimension: int
    representation_class: str = "COMPAT_EMBEDDING"
    generation: int = 1
    derivation_contract_version: str = "compat-embedding-v1"
    encoding_id: str = "RAW_VECTOR"
    dtype: str = "float32"

    def __post_init__(self) -> None:
        if not isinstance(self.operation_kind, DerivedMemoryCreateKind):
            raise ValueError("operation_kind must be a DerivedMemoryCreateKind")
        for field_name in (
            "legacy_source_namespace_id", "memory_identity_namespace_id",
            "semantic_scope_id", "idempotency_namespace_id",
        ):
            if not isinstance(getattr(self, field_name), UUID):
                raise ValueError(f"{field_name} must be a UUID")
        for field_name in ("idempotency_key", "summary", "user_id"):
            if not isinstance(getattr(self, field_name), str) or not getattr(self, field_name):
                raise ValueError(f"{field_name} must be non-empty text")
        for field_name in ("logical_step", "created_ts", "expected_dimension"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if self.expected_dimension < 1:
            raise ValueError("expected_dimension must be positive")
        for field_name in ("strength", "confidence", "half_life_days"):
            value = _finite_number(field_name, getattr(self, field_name))
            object.__setattr__(self, field_name, value)
        if not isinstance(self.provenance, NativeProvenanceRecord):
            raise ValueError("provenance must be NativeProvenanceRecord")
        _validate_provenance(self.provenance)
        if not isinstance(self.governance, NativeMemoryGovernanceFacts):
            raise ValueError("governance must be NativeMemoryGovernanceFacts")
        self.governance.as_storage_tuple()
        fields = _copy_closed_creation_payload(self.operation_kind, self.payload_fields)
        _reject_creation_payload_shadow(fields)
        object.__setattr__(self, "payload_fields", MappingProxyType(fields))
        object.__setattr__(self, "embedding", _canonical_embedding(self.embedding, self.expected_dimension))
        _validate_lane(self)

    @property
    def memory_type(self) -> str:
        return _CREATE_MEMORY_TYPE[self.operation_kind]


@dataclass(frozen=True)
class NativeDerivedMemorySourceResult:
    """Durable R1 result used for recovery and immediate world registration."""

    operation_kind: DerivedMemoryCreateKind
    memory_object_id: UUID
    memory_revision_id: UUID
    memory_revision_ordinal: int
    eid: int
    provenance_id: UUID
    transition_id: UUID
    operation_id: UUID


@dataclass(frozen=True)
class NativeDerivedMemoryCreationResult:
    """Complete source and representation identities for one derived R1."""

    source: NativeDerivedMemorySourceResult
    representation_id: UUID
    expectation_id: UUID
    pending_operation_id: UUID
    expectation_operation_id: UUID
    ready_operation_id: UUID


class NativeDerivedMemoryCreationService:
    """Closed typed no-motif R1 publisher; intentionally not Fabric-wired."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        require_current_schema(connection)
        self._connection = connection
        self._objects = NativeObjectService(connection)
        self._representations = NativeRepresentationService(connection)

    def create(
        self,
        request: NativeDerivedMemoryCreationRequest,
        *,
        _test_stop_after: Literal["source", "pending", "expectation", "ready"] | None = None,
        on_source_committed: Callable[[NativeDerivedMemorySourceResult], None] | None = None,
    ) -> NativeDerivedMemoryCreationResult:
        if not isinstance(request, NativeDerivedMemoryCreationRequest):
            raise ValueError("a NativeDerivedMemoryCreationRequest is required")
        source = self._source(request)
        if on_source_committed is not None:
            on_source_committed(source)
        if _test_stop_after == "source":
            raise RuntimeError("forced interruption after committed derived source")
        payload = _embedding_bytes(request.embedding)
        pending = self._representations.create_representation_pending(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=_creation_subkey(request.idempotency_key, "PENDING"),
            request=RepresentationRequest(
                "OBJECT_REVISION", source.memory_object_id, source.memory_revision_id,
                None, None, request.representation_class, request.generation,
                request.derivation_contract_version, request.encoding_id, request.dtype,
                request.expected_dimension, (), None, len(payload),
            ),
        )
        if _test_stop_after == "pending":
            raise RuntimeError("forced interruption after derived representation pending")
        expectation = self._representations.establish_representation_integrity_expectation(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=_creation_subkey(request.idempotency_key, "EXPECTATION"),
            request=RepresentationIntegrityExpectationRequest(
                pending.representation_id, INTEGRITY_ALGORITHM_SHA256,
                hashlib.sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW,
            ),
        )
        if _test_stop_after == "expectation":
            raise RuntimeError("forced interruption after derived representation expectation")
        ready = self._representations.publish_representation_ready(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=_creation_subkey(request.idempotency_key, "READY"),
            request=RepresentationReadyRequest(
                pending.representation_id, request.representation_class, request.generation,
                request.derivation_contract_version, request.encoding_id, payload,
            ),
        )
        result = NativeDerivedMemoryCreationResult(
            source, ready.representation_id, expectation.expectation_id,
            self._operation_id(request, "PENDING"), self._operation_id(request, "EXPECTATION"),
            self._operation_id(request, "READY"),
        )
        if _test_stop_after == "ready":
            raise RuntimeError("forced interruption after derived representation ready")
        return result

    def _source(self, request: NativeDerivedMemoryCreationRequest) -> NativeDerivedMemorySourceResult:
        source_key = _creation_subkey(request.idempotency_key, "SOURCE")
        prior = self._connection.execute(
            "SELECT operation_id,canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), source_key),
        ).fetchone()
        if prior is not None:
            if _intent_mapping(prior[1]).get("retry_contract") != _creation_retry_contract(request):
                raise SubstrateIdempotencyConflict("derived creation idempotency intent differs")
            result = self._source_result_for_operation(prior[0])
            if result is None:
                raise SubstrateInvariantViolation("existing derived creation source is incomplete")
            return result
        return execute_semantic(
            self._connection,
            request.idempotency_namespace_id,
            source_key,
            f"{_CREATION_OPERATION_PREFIX}:{request.operation_kind.value}",
            _creation_source_intent(request),
            self._source_result_for_operation,
            lambda tx: self._commit_source(tx, request),
        )

    def _commit_source(self, tx: SubstrateTx, request: NativeDerivedMemoryCreationRequest) -> NativeDerivedMemorySourceResult:
        _assert_creation_identities(tx, request)
        transition_id, provenance_id = _new(), _new()
        tx.execute(
            """INSERT INTO provenance_records(
                   provenance_id,origin_kind,source_channel,source_role,derivation_status,
                   uncertainty_state,source_time_ns,capture_time_ns,memory_role,descriptive_notes
               ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (provenance_id, *_provenance_values(request.provenance)),
        )
        object_id, revision_id = _new(), _new()
        eid = _allocate_eid(tx, request.legacy_source_namespace_id)
        state = _creation_state(request, UUID(bytes=provenance_id))
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
            (native_id_to_bytes(request.legacy_source_namespace_id), str(eid), object_id),
        )
        publish_runtime_order(
            tx,
            legacy_source_namespace_id=request.legacy_source_namespace_id,
            object_id=UUID(bytes=object_id),
            runtime_ordinal=allocate_next_runtime_ordinal(tx, request.legacy_source_namespace_id),
        )
        _insert_published_governance_for_qualification(
            tx, object_id=object_id, object_revision_id=revision_id,
            object_revision_ordinal=1, facts=request.governance,
        )
        transition_kind = f"NATIVE_{request.operation_kind.value}"
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (transition_id, tx.operation_id, transition_kind, "NATIVE"),
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
            (tx.operation_id, 0, _SOURCE_ROLE, "OBJECT", object_id, revision_id, 1),
        )
        _validate_creation_publication(
            tx, transition_id, object_id, revision_id, request.governance,
        )
        tx.transitions.append(transition_id)
        tx.published.append((object_id, revision_id, 1))
        return NativeDerivedMemorySourceResult(
            request.operation_kind, UUID(bytes=object_id), UUID(bytes=revision_id), 1,
            eid, UUID(bytes=provenance_id), UUID(bytes=transition_id), UUID(bytes=tx.operation_id),
        )

    def _source_result_for_operation(self, operation_id: bytes) -> NativeDerivedMemorySourceResult | None:
        row = self._connection.execute(
            """SELECT t.transition_id,o.object_id,o.object_revision_id,o.object_revision_ordinal,
                      r.provenance_id,a.alias_value
                 FROM semantic_transitions t
                 JOIN operation_outputs o ON o.operation_id=t.operation_id
                 JOIN object_revisions r ON r.object_id=o.object_id
                   AND r.object_revision_id=o.object_revision_id
                   AND r.revision_ordinal=o.object_revision_ordinal
                 JOIN legacy_object_aliases a ON a.object_id=o.object_id AND a.alias_kind='EID'
                WHERE t.operation_id=? AND o.output_ordinal=0 AND o.output_role=?
                  AND o.output_kind='OBJECT'""",
            (operation_id, _SOURCE_ROLE),
        ).fetchone()
        intent_row = self._connection.execute(
            "SELECT canonical_intent_json FROM operations WHERE operation_id=?", (operation_id,),
        ).fetchone()
        if row is None or intent_row is None:
            return None
        try:
            intent = _intent_mapping(intent_row[0])
            contract = intent["retry_contract"]
            return NativeDerivedMemorySourceResult(
                DerivedMemoryCreateKind(contract["operation_kind"]), UUID(bytes=row[1]), UUID(bytes=row[2]),
                int(row[3]), int(row[5]), UUID(bytes=row[4]),
                UUID(bytes=row[0]), UUID(bytes=operation_id),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SubstrateInvariantViolation("stored derived creation result is malformed") from exc

    def _operation_id(self, request: NativeDerivedMemoryCreationRequest, suffix: str) -> UUID:
        row = self._connection.execute(
            "SELECT operation_id FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), _creation_subkey(request.idempotency_key, suffix)),
        ).fetchone()
        if row is None:
            raise SubstrateInvariantViolation("derived representation operation is missing")
        return UUID(bytes=row[0])


@dataclass(frozen=True)
class IdentityAnchorLifecyclePatch:
    """Closed exact patch owned by identity-anchor refinement only."""

    anchor_retired_reason: Literal["superseded", "weak_old"]
    anchor_superseded_by: int
    last_reinforced: int
    anchor_merged_into: int | None = None

    def __post_init__(self) -> None:
        if self.anchor_retired_reason not in ("superseded", "weak_old"):
            raise ValueError("anchor_retired_reason must be superseded or weak_old")
        for field_name in ("anchor_superseded_by", "last_reinforced"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if self.anchor_merged_into is not None and (
            not isinstance(self.anchor_merged_into, int)
            or isinstance(self.anchor_merged_into, bool)
            or self.anchor_merged_into < 0
        ):
            raise ValueError("anchor_merged_into must be a non-negative integer when supplied")
        if self.anchor_retired_reason == "superseded" and self.anchor_merged_into is None:
            raise ValueError("superseded anchor lifecycle requires anchor_merged_into")
        if self.anchor_retired_reason == "weak_old" and self.anchor_merged_into is not None:
            raise ValueError("weak_old anchor lifecycle must not set anchor_merged_into")

    @classmethod
    def superseded(
        cls, *, anchor_superseded_by: int, anchor_merged_into: int, last_reinforced: int,
    ) -> "IdentityAnchorLifecyclePatch":
        return cls("superseded", anchor_superseded_by, last_reinforced, anchor_merged_into)

    @classmethod
    def weak_old(
        cls, *, anchor_superseded_by: int, last_reinforced: int,
    ) -> "IdentityAnchorLifecyclePatch":
        return cls("weak_old", anchor_superseded_by, last_reinforced)

    def payload_contribution(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "anchor_retired": True,
            "anchor_retired_reason": self.anchor_retired_reason,
            "anchor_superseded_by": self.anchor_superseded_by,
            "last_reinforced": self.last_reinforced,
        }
        if self.anchor_merged_into is not None:
            payload["anchor_merged_into"] = self.anchor_merged_into
        return payload

    def intent(self) -> dict[str, Any]:
        return self.payload_contribution()


@dataclass(frozen=True)
class NativeTypedMemorySuccessorRequest:
    """Closed identity-anchor lifecycle successor request, never a payload map."""

    legacy_source_namespace_id: UUID
    eid: int
    expected_revision_id: UUID
    expected_representation_id: UUID
    idempotency_namespace_id: UUID
    idempotency_key: str
    expected_dimension: int
    patch: IdentityAnchorLifecyclePatch
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
        for field_name in ("eid", "expected_dimension"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if self.expected_dimension < 1:
            raise ValueError("expected_dimension must be positive")
        if not isinstance(self.patch, IdentityAnchorLifecyclePatch):
            raise ValueError("patch must be IdentityAnchorLifecyclePatch")
        if self.srg_materialization is not None and not isinstance(
            self.srg_materialization, SRGSuccessorMaterialization
        ):
            raise ValueError("srg_materialization must be SRGSuccessorMaterialization")
        if self.world_diagnostic_materialization is not None and not isinstance(
            self.world_diagnostic_materialization, WorldDiagnosticSuccessorMaterialization
        ):
            raise ValueError("world_diagnostic_materialization must be WorldDiagnosticSuccessorMaterialization")


@dataclass(frozen=True)
class NativeTypedMemorySuccessorSourceResult:
    """Committed typed anchor successor before representation continuity."""

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
class NativeTypedMemorySuccessorResult:
    source: NativeTypedMemorySuccessorSourceResult
    e1_representation_id: UUID
    e2_representation_id: UUID
    e2_expectation_id: UUID
    pending_operation_id: UUID
    expectation_operation_id: UUID
    ready_operation_id: UUID


@dataclass(frozen=True)
class _SuccessorPlan:
    request: NativeTypedMemorySuccessorRequest
    current: Mapping[str, Any]
    state: ObjectState
    governance: NativeMemoryGovernanceFacts
    e1_witness: QualifiedCompatEmbedding


class NativeTypedMemorySuccessorService:
    """Closed R(n+1) publisher for identity-anchor lifecycle only."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        require_current_schema(connection)
        self._connection = connection
        self._objects = NativeObjectService(connection)
        self._governance = NativeObjectRevisionGovernanceService(connection)
        self._embeddings = NativeCompatEmbeddingReader(connection)
        self._representations = NativeRepresentationService(connection)

    def publish_identity_anchor_lifecycle(
        self,
        request: NativeTypedMemorySuccessorRequest,
        *,
        _test_stop_after: Literal["source", "pending", "expectation", "ready"] | None = None,
        on_source_committed: Callable[[NativeTypedMemorySuccessorSourceResult], None] | None = None,
    ) -> NativeTypedMemorySuccessorResult:
        if not isinstance(request, NativeTypedMemorySuccessorRequest):
            raise ValueError("a NativeTypedMemorySuccessorRequest is required")
        source = self._source(request)
        if on_source_committed is not None:
            on_source_committed(source)
        if _test_stop_after == "source":
            raise RuntimeError("forced interruption after committed typed successor")
        e1 = self._embeddings.read_historical(source.e1_witness)
        pending = self._representations.create_representation_pending(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=_successor_subkey(request.idempotency_key, "PENDING"),
            request=RepresentationRequest(
                "OBJECT_REVISION", source.memory_object_id, source.revision_id,
                None, None, e1.representation_class, e1.generation,
                e1.derivation_contract_version, e1.encoding_id, e1.dtype,
                e1.dimension, e1.dependencies, None, e1.expected_payload_byte_length,
            ),
        )
        if _test_stop_after == "pending":
            raise RuntimeError("forced interruption after typed successor pending")
        expectation = self._representations.establish_representation_integrity_expectation(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=_successor_subkey(request.idempotency_key, "EXPECTATION"),
            request=RepresentationIntegrityExpectationRequest(
                pending.representation_id, INTEGRITY_ALGORITHM_SHA256,
                bytes.fromhex(e1.payload_sha256), INTEGRITY_VALUE_ENCODING_RAW,
            ),
        )
        if _test_stop_after == "expectation":
            raise RuntimeError("forced interruption after typed successor expectation")
        ready = self._representations.publish_representation_ready(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=_successor_subkey(request.idempotency_key, "READY"),
            request=RepresentationReadyRequest(
                pending.representation_id, e1.representation_class, e1.generation,
                e1.derivation_contract_version, e1.encoding_id, e1.payload_bytes,
            ),
        )
        result = NativeTypedMemorySuccessorResult(
            source, e1.representation_id, ready.representation_id, expectation.expectation_id,
            self._operation_id(request, "PENDING"), self._operation_id(request, "EXPECTATION"),
            self._operation_id(request, "READY"),
        )
        if _test_stop_after == "ready":
            raise RuntimeError("forced interruption after typed successor ready")
        return result

    def _source(self, request: NativeTypedMemorySuccessorRequest) -> NativeTypedMemorySuccessorSourceResult:
        source_key = _successor_subkey(request.idempotency_key, "SOURCE")
        prior = self._connection.execute(
            "SELECT operation_id,canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), source_key),
        ).fetchone()
        if prior is not None:
            if _intent_mapping(prior[1]).get("retry_contract") != _successor_retry_contract(request):
                raise SubstrateIdempotencyConflict("anchor lifecycle idempotency intent differs")
            result = self._source_result_for_operation(prior[0])
            if result is None:
                raise SubstrateInvariantViolation("existing typed successor source is incomplete")
            return result
        plan = self._prepare_source(request)
        return execute_semantic(
            self._connection, request.idempotency_namespace_id, source_key,
            _SUCCESSOR_OPERATION_KIND, _successor_source_intent(plan), self._source_result_for_operation,
            lambda tx: self._commit_source(tx, plan),
        )

    def _prepare_source(self, request: NativeTypedMemorySuccessorRequest) -> _SuccessorPlan:
        current = _current_memory(self._connection, request.legacy_source_namespace_id, request.eid)
        if current["revision_id"] != request.expected_revision_id:
            raise StaleDerivedMemoryPlanError("expected anchor predecessor is not current")
        if current["authority_category"] != "NOT_APPLICABLE":
            raise SubstrateInvariantViolation("identity anchor has authorizing authority")
        if current["payload"].get("type") != "identity_anchor":
            raise SubstrateInvariantViolation("typed anchor lifecycle target is not an identity anchor")
        governance = self._governance.get_object_revision_governance(
            object_id=current["object_id"], object_revision_id=current["revision_id"],
            object_revision_ordinal=current["revision_ordinal"],
        )
        if governance is None:
            raise SubstrateInvariantViolation("identity anchor requires explicit current governance")
        if current["provenance_id"] is None:
            raise SubstrateInvariantViolation("identity anchor requires structural provenance")
        e1 = self._embeddings.read_current(current["object_id"], expected_dimension=request.expected_dimension)
        if e1 is None or e1.representation_id != request.expected_representation_id:
            raise StaleDerivedMemoryPlanError("expected qualified anchor embedding is stale")
        _validate_materializations(request, current)
        payload = dict(current["payload"])
        if request.srg_materialization is not None:
            payload.update(request.srg_materialization.payload_contribution())
        if request.world_diagnostic_materialization is not None:
            payload.update(request.world_diagnostic_materialization.payload_contribution())
        payload.update(request.patch.payload_contribution())
        state = ObjectState(
            current["identity_namespace_id"], current["semantic_scope_id"], current["object_kind"],
            current["existence_state"], current["lifecycle_state"], current["lifecycle_authoritative"],
            current["governance_state"], current["authority_category"], payload, "JSON", current["provenance_id"],
        )
        return _SuccessorPlan(request, current, state, governance.facts, e1)

    def _commit_source(self, tx: SubstrateTx, plan: _SuccessorPlan) -> NativeTypedMemorySuccessorSourceResult:
        request, expected = plan.request, plan.current
        current = _current_memory(self._connection, request.legacy_source_namespace_id, request.eid)
        if (
            current["object_id"] != expected["object_id"]
            or current["revision_id"] != request.expected_revision_id
            or current["revision_ordinal"] != expected["revision_ordinal"]
        ):
            raise StaleDerivedMemoryPlanError("anchor predecessor changed before successor commit")
        _validate_materializations(request, current)
        e1 = self._embeddings.read_current(current["object_id"], expected_dimension=request.expected_dimension)
        if e1 is None or e1.intent() != plan.e1_witness.intent():
            raise StaleDerivedMemoryPlanError("qualified anchor E1 witness changed before successor commit")
        governance = self._governance.get_object_revision_governance(
            object_id=current["object_id"], object_revision_id=current["revision_id"],
            object_revision_ordinal=current["revision_ordinal"],
        )
        if governance is None or governance.facts != plan.governance:
            raise StaleDerivedMemoryPlanError("anchor governance changed before successor commit")
        if current["provenance_id"] != plan.state.provenance_id:
            raise StaleDerivedMemoryPlanError("anchor provenance changed before successor commit")
        revision_id, transition_id = _new(), _new()
        revision_ordinal = current["revision_ordinal"] + 1
        object_id = native_id_to_bytes(current["object_id"])
        self._objects._state(plan.state)
        self._objects._revision(
            tx, revision_id, object_id, revision_ordinal, "NATIVE_ORDINARY",
            native_id_to_bytes(request.expected_revision_id), current["revision_ordinal"], plan.state,
        )
        tx.execute(
            "UPDATE objects SET current_revision_id=?,current_revision_ordinal=? WHERE object_id=?",
            (revision_id, revision_ordinal, object_id),
        )
        _insert_published_governance_for_qualification(
            tx, object_id=object_id, object_revision_id=revision_id,
            object_revision_ordinal=revision_ordinal, facts=plan.governance,
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (transition_id, tx.operation_id, _SUCCESSOR_OPERATION_KIND, "NATIVE"),
        )
        tx.execute(
            "INSERT INTO object_revision_effects VALUES (?,?,?,?)",
            (transition_id, object_id, revision_id, revision_ordinal),
        )
        tx.execute(
            """INSERT INTO operation_outputs(
                   operation_id,output_ordinal,output_role,output_kind,
                   object_id,object_revision_id,object_revision_ordinal
               ) VALUES (?,?,?,?,?,?,?)""",
            (tx.operation_id, 0, "IDENTITY_ANCHOR_LIFECYCLE", "OBJECT", object_id, revision_id, revision_ordinal),
        )
        _validate_successor_publication(
            tx, transition_id, object_id, revision_id, revision_ordinal, plan.governance,
        )
        tx.transitions.append(transition_id)
        tx.published.append((object_id, revision_id, revision_ordinal))
        return NativeTypedMemorySuccessorSourceResult(
            current["object_id"], request.expected_revision_id, current["revision_ordinal"],
            UUID(bytes=revision_id), revision_ordinal, request.eid, UUID(bytes=transition_id),
            UUID(bytes=tx.operation_id), plan.e1_witness,
        )

    def _source_result_for_operation(self, operation_id: bytes) -> NativeTypedMemorySuccessorSourceResult | None:
        row = self._connection.execute(
            """SELECT t.transition_id,o.object_id,o.object_revision_id,o.object_revision_ordinal
                 FROM semantic_transitions t JOIN operation_outputs o ON o.operation_id=t.operation_id
                WHERE t.operation_id=? AND t.transition_kind=? AND o.output_ordinal=0
                  AND o.output_role='IDENTITY_ANCHOR_LIFECYCLE' AND o.output_kind='OBJECT'""",
            (operation_id, _SUCCESSOR_OPERATION_KIND),
        ).fetchone()
        intent_row = self._connection.execute(
            "SELECT canonical_intent_json FROM operations WHERE operation_id=?", (operation_id,),
        ).fetchone()
        if row is None or intent_row is None:
            return None
        try:
            intent = _intent_mapping(intent_row[0])
            predecessor = intent["predecessor"]
            contract = intent["retry_contract"]
            witness = QualifiedCompatEmbedding.from_intent(intent["e1_witness"], b"")
            return NativeTypedMemorySuccessorSourceResult(
                UUID(bytes=row[1]), UUID(str(predecessor["revision_id"])),
                int(predecessor["revision_ordinal"]), UUID(bytes=row[2]), int(row[3]),
                int(contract["eid"]), UUID(bytes=row[0]), UUID(bytes=operation_id), witness,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SubstrateInvariantViolation("stored typed successor result is malformed") from exc

    def _operation_id(self, request: NativeTypedMemorySuccessorRequest, suffix: str) -> UUID:
        row = self._connection.execute(
            "SELECT operation_id FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), _successor_subkey(request.idempotency_key, suffix)),
        ).fetchone()
        if row is None:
            raise SubstrateInvariantViolation("typed successor representation operation is missing")
        return UUID(bytes=row[0])


def derived_child_operation_key(
    *, parent_native_operation_key: str, operation_kind: str, semantic_discriminator: str,
) -> str:
    """Deterministically derive one D9 child key from frozen parent facts."""
    for name, value in (
        ("parent_native_operation_key", parent_native_operation_key),
        ("operation_kind", operation_kind),
        ("semantic_discriminator", semantic_discriminator),
    ):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} must be non-empty text")
    digest = hashlib.sha256(canonical_intent_text({
        "parent_native_operation_key": parent_native_operation_key,
        "operation_kind": operation_kind,
        "semantic_discriminator": semantic_discriminator,
    }).encode("utf-8")).hexdigest()
    return f"NATIVE_DERIVED_CHILD:{operation_kind}:{digest}"


def _creation_state(request: NativeDerivedMemoryCreationRequest, provenance_id: UUID) -> ObjectState:
    payload: dict[str, Any] = {
        "summary": request.summary,
        "type": request.memory_type,
        "memory_class": "core",
        "strength": request.strength,
        "confidence": request.confidence,
        "canon": False,
        "created_at": request.logical_step,
        "created_ts": request.created_ts,
        "last_reinforced": request.logical_step,
        "half_life": request.half_life_days,
        "user_id": request.user_id,
    }
    payload.update(dict(request.payload_fields))
    _ensure_lifecycle_envelope(payload)
    payload.update(legacy_world_genesis_payload(payload))
    return ObjectState(
        request.memory_identity_namespace_id, request.semantic_scope_id, _MEMORY_OBJECT_KIND,
        "EXISTS", "ORDINARY", False, "DERIVED", "NOT_APPLICABLE", payload, "JSON", provenance_id,
    )


def _creation_retry_contract(request: NativeDerivedMemoryCreationRequest) -> dict[str, Any]:
    return {
        "operation_kind": request.operation_kind.value,
        "legacy_source_namespace_id": str(request.legacy_source_namespace_id),
        "memory_identity_namespace_id": str(request.memory_identity_namespace_id),
        "semantic_scope_id": str(request.semantic_scope_id),
        "summary": request.summary,
        "strength": request.strength,
        "confidence": request.confidence,
        "half_life_days": request.half_life_days,
        "user_id": request.user_id,
        "logical_step": request.logical_step,
        "created_ts": request.created_ts,
        "payload_fields": dict(request.payload_fields),
        "provenance": _provenance_intent(request.provenance),
        "governance": list(request.governance.as_storage_tuple()),
        "embedding": {
            "dtype": request.dtype, "dimension": request.expected_dimension,
            "byte_length": len(_embedding_bytes(request.embedding)),
            "sha256": hashlib.sha256(_embedding_bytes(request.embedding)).hexdigest(),
        },
        "lane": {
            "representation_class": request.representation_class,
            "generation": request.generation,
            "derivation_contract_version": request.derivation_contract_version,
            "encoding_id": request.encoding_id,
        },
    }


def _creation_source_intent(request: NativeDerivedMemoryCreationRequest) -> str:
    # The allocated EID and provenance identity are recovered from the durable
    # R1 output and its current revision; neither is caller input.
    return canonical_intent_text({
        "kind": f"{_CREATION_OPERATION_PREFIX}:{request.operation_kind.value}",
        "retry_contract": _creation_retry_contract(request),
    })


def _successor_retry_contract(request: NativeTypedMemorySuccessorRequest) -> dict[str, Any]:
    result: dict[str, Any] = {
        "legacy_source_namespace_id": str(request.legacy_source_namespace_id),
        "eid": request.eid,
        "expected_revision_id": str(request.expected_revision_id),
        "expected_representation_id": str(request.expected_representation_id),
        "expected_dimension": request.expected_dimension,
        "patch": request.patch.intent(),
    }
    if request.srg_materialization is not None:
        result["srg_materialization"] = request.srg_materialization.intent()
    if request.world_diagnostic_materialization is not None:
        result["world_diagnostic_materialization"] = request.world_diagnostic_materialization.intent()
    return result


def _successor_source_intent(plan: _SuccessorPlan) -> str:
    current = plan.current
    return canonical_intent_text({
        "kind": _SUCCESSOR_OPERATION_KIND,
        "retry_contract": _successor_retry_contract(plan.request),
        "predecessor": {
            "object_id": str(current["object_id"]),
            "revision_id": str(current["revision_id"]),
            "revision_ordinal": current["revision_ordinal"],
            "provenance_id": str(current["provenance_id"]),
            "governance": list(plan.governance.as_storage_tuple()),
        },
        "patch": plan.request.patch.intent(),
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


def _creation_subkey(base: str, suffix: str) -> str:
    return f"NATIVE_DERIVED_CREATION:{suffix}:{base}"


def _successor_subkey(base: str, suffix: str) -> str:
    return f"NATIVE_DERIVED_SUCCESSOR:{suffix}:{base}"


def _current_memory(connection: sqlite3.Connection, namespace: UUID, eid: int) -> dict[str, Any]:
    rows = connection.execute(
        """SELECT o.object_id,o.identity_namespace_id,o.object_kind,
                  r.object_revision_id,r.revision_ordinal,r.effective_semantic_scope_id,
                  r.existence_state,r.lifecycle_state,r.lifecycle_authoritative,
                  r.governance_state,r.authority_category,r.provenance_id,
                  r.payload_format,r.payload_text
             FROM legacy_object_aliases a
             JOIN objects o ON o.object_id=a.object_id
             JOIN object_revisions r ON r.object_id=o.object_id
               AND r.object_revision_id=o.current_revision_id
               AND r.revision_ordinal=o.current_revision_ordinal
            WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID' AND a.alias_value=?""",
        (native_id_to_bytes(namespace), str(eid)),
    ).fetchall()
    if not rows:
        raise SubstrateObjectNotFound("derived memory EID alias was not found")
    if len(rows) != 1:
        raise SubstrateInvariantViolation("derived memory EID alias is ambiguous")
    row = rows[0]
    if row[2] != _MEMORY_OBJECT_KIND:
        raise SubstrateInvariantViolation("derived memory EID is not a LEGACY_CORE_NODE")
    if row[12] != "JSON" or row[13] is None:
        raise SubstrateInvariantViolation("derived memory current payload is not JSON")
    try:
        payload = json.loads(row[13])
    except (TypeError, json.JSONDecodeError) as exc:
        raise SubstrateInvariantViolation("derived memory current payload is invalid JSON") from exc
    if not isinstance(payload, dict):
        raise SubstrateInvariantViolation("derived memory current payload is not an object")
    return {
        "object_id": UUID(bytes=row[0]), "identity_namespace_id": UUID(bytes=row[1]),
        "object_kind": row[2], "revision_id": UUID(bytes=row[3]),
        "revision_ordinal": row[4], "semantic_scope_id": UUID(bytes=row[5]),
        "existence_state": row[6], "lifecycle_state": row[7],
        "lifecycle_authoritative": bool(row[8]), "governance_state": row[9],
        "authority_category": row[10], "provenance_id": UUID(bytes=row[11]) if row[11] else None,
        "payload": payload,
    }


def _validate_materializations(request: NativeTypedMemorySuccessorRequest, current: Mapping[str, Any]) -> None:
    for materialization, label in (
        (request.srg_materialization, "SRG"),
        (request.world_diagnostic_materialization, "world diagnostic"),
    ):
        if materialization is not None and not materialization.validates_predecessor(
            revision_id=current["revision_id"], revision_ordinal=current["revision_ordinal"],
        ):
            raise StaleDerivedMemoryPlanError(f"{label} materialization predecessor is stale")


def _assert_creation_identities(tx: SubstrateTx, request: NativeDerivedMemoryCreationRequest) -> None:
    checks = (
        ("legacy source namespace", "legacy_source_namespaces", "legacy_source_namespace_id", request.legacy_source_namespace_id),
        ("memory identity namespace", "identity_namespaces", "identity_namespace_id", request.memory_identity_namespace_id),
        ("semantic scope", "semantic_scopes", "semantic_scope_id", request.semantic_scope_id),
        ("idempotency namespace", "idempotency_namespaces", "idempotency_namespace_id", request.idempotency_namespace_id),
    )
    for label, table, column, value in checks:
        if tx.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)).fetchone() is None:
            raise SubstrateInvariantViolation(f"derived creation {label} is missing")


def _validate_creation_publication(
    tx: SubstrateTx, transition_id: bytes, object_id: bytes, revision_id: bytes,
    governance: NativeMemoryGovernanceFacts,
) -> None:
    if tx.execute(
        "SELECT 1 FROM object_revision_effects WHERE transition_id=? AND object_id=? AND object_revision_id=? AND object_revision_ordinal=1",
        (transition_id, object_id, revision_id),
    ).fetchone() is None:
        raise SubstrateInvariantViolation("derived creation transition omits R1 effect")
    if tx.execute(
        "SELECT output_role,output_kind,object_id,object_revision_id,object_revision_ordinal FROM operation_outputs WHERE operation_id=?",
        (tx.operation_id,),
    ).fetchall() != [(_SOURCE_ROLE, "OBJECT", object_id, revision_id, 1)]:
        raise SubstrateInvariantViolation("derived creation outputs do not match R1")
    if tx.execute(
        """SELECT protected,non_shareable,collective_export_blocked,
                  collective_reingest_blocked,decay_accelerated
             FROM object_revision_governance
            WHERE object_id=? AND object_revision_id=? AND object_revision_ordinal=1""",
        (object_id, revision_id),
    ).fetchone() != governance.as_storage_tuple():
        raise SubstrateInvariantViolation("derived creation R1 has no exact governance")


def _validate_successor_publication(
    tx: SubstrateTx, transition_id: bytes, object_id: bytes, revision_id: bytes,
    revision_ordinal: int, governance: NativeMemoryGovernanceFacts,
) -> None:
    if tx.execute(
        "SELECT 1 FROM object_revision_effects WHERE transition_id=? AND object_id=? AND object_revision_id=? AND object_revision_ordinal=?",
        (transition_id, object_id, revision_id, revision_ordinal),
    ).fetchone() is None:
        raise SubstrateInvariantViolation("typed successor transition omits its R(n+1) effect")
    if tx.execute(
        "SELECT output_role,output_kind,object_id,object_revision_id,object_revision_ordinal FROM operation_outputs WHERE operation_id=?",
        (tx.operation_id,),
    ).fetchall() != [("IDENTITY_ANCHOR_LIFECYCLE", "OBJECT", object_id, revision_id, revision_ordinal)]:
        raise SubstrateInvariantViolation("typed successor outputs do not match R(n+1)")
    if tx.execute(
        """SELECT protected,non_shareable,collective_export_blocked,
                  collective_reingest_blocked,decay_accelerated
             FROM object_revision_governance
            WHERE object_id=? AND object_revision_id=? AND object_revision_ordinal=?""",
        (object_id, revision_id, revision_ordinal),
    ).fetchone() != governance.as_storage_tuple():
        raise SubstrateInvariantViolation("typed successor has no exact governance")


def _allocate_eid(tx: SubstrateTx, namespace: UUID) -> int:
    values = tx.execute(
        "SELECT alias_value FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID'",
        (native_id_to_bytes(namespace),),
    ).fetchall()
    eids: list[int] = []
    for (value,) in values:
        if not isinstance(value, str):
            raise SubstrateInvariantViolation("stored EID alias is not text")
        try:
            eid = int(value)
        except ValueError as exc:
            raise SubstrateInvariantViolation("stored EID alias is not an integer") from exc
        if eid < 0 or str(eid) != value:
            raise SubstrateInvariantViolation("stored EID alias is not canonical")
        eids.append(eid)
    return max(eids, default=-1) + 1


def _reject_creation_payload_shadow(payload: Mapping[str, Any]) -> None:
    # Creation owns all fields that ``MemoryGraph.spawn_memory`` establishes
    # before merging extra payload.  A caller cannot silently replace them.
    reserved = {
        "summary", "type", "memory_class", "strength", "confidence", "canon",
        "created_at", "created_ts", "last_reinforced", "half_life", "user_id",
        "pos", "vel", "vel0",
    }
    overlap = reserved.intersection(payload)
    if overlap:
        raise ValueError(f"derived payload_fields cannot replace creation fields: {sorted(overlap)!r}")


def _copy_closed_creation_payload(
    operation_kind: DerivedMemoryCreateKind, value: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate only the known legacy fields for each derived creation kind.

    ``scope`` is a legacy descriptive payload field even though generic
    compatibility writers correctly reserve it as a substrate shadow.  The
    derived service has no generic payload mode, so it may carry that one
    fixed legacy field after the ordinary shared shadow policy has checked all
    remaining values.
    """
    if not isinstance(value, Mapping):
        raise ValueError("derived payload_fields must be a mapping")
    common = {
        "workspace_id", "domain_id", "scope", "agent_id", "embedding_provider",
        "embedding_model", "embedding_dim", "embedding_checksum", "seed_pos0", "seed_v0",
    }
    by_kind = {
        DerivedMemoryCreateKind.IDENTITY_ANCHOR_CREATE: {
            "anchor_for_motif", "anchor_member_count", "anchor_label",
            "anchor_affect_sensitive", "anchor_origin", "anchor_source",
            "seed_overlap_count", "seed_aligned", "source_member_eids",
        },
        DerivedMemoryCreateKind.MOOD_DRIFT_CREATE: {
            "affect_tag", "affect_conf", "affect_attribution", "mood_from", "mood_to",
        },
    }
    copied = dict(value)
    unknown = set(copied).difference(common | by_kind[operation_kind])
    if unknown:
        raise ValueError(f"derived payload_fields contain unknown fields: {sorted(unknown)!r}")
    scope = copied.pop("scope", None)
    if scope is not None and scope not in ("private", "shared"):
        raise ValueError("derived payload scope must be private or shared")
    checked = copy_memory_flexible_payload(copied, field="derived payload_fields")
    if scope is not None:
        checked["scope"] = scope
    return checked


def _canonical_embedding(value: Any, dimension: int) -> tuple[float, ...]:
    try:
        vector = np.asarray(value, dtype=np.float32).reshape(-1)
    except (TypeError, ValueError) as exc:
        raise ValueError("embedding must be numeric float32 data") from exc
    if vector.size != dimension or not np.all(np.isfinite(vector)):
        raise ValueError("embedding must be finite and match expected_dimension")
    return tuple(float(item) for item in vector)


def _embedding_bytes(value: tuple[float, ...]) -> bytes:
    return np.ascontiguousarray(np.asarray(value, dtype=np.float32)).tobytes(order="C")


def _validate_lane(request: NativeDerivedMemoryCreationRequest) -> None:
    if (
        request.representation_class, request.generation,
        request.derivation_contract_version, request.encoding_id, request.dtype,
    ) != ("COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32"):
        raise ValueError("derived creation requires the qualified compatibility embedding lane")


def _finite_number(name: str, value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be finite")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{name} must be finite")
    return numeric


def _validate_provenance(value: NativeProvenanceRecord) -> None:
    for field_name in ("origin_kind", "derivation_status", "uncertainty_state"):
        if not isinstance(getattr(value, field_name), str) or not getattr(value, field_name):
            raise ValueError(f"provenance {field_name} must be non-empty text")
    for item in (value.source_channel, value.source_role, value.memory_role, value.descriptive_notes):
        if item is not None and not isinstance(item, str):
            raise ValueError("optional provenance text must be text")
    for item in (value.source_time_ns, value.capture_time_ns):
        if item is not None and (not isinstance(item, int) or isinstance(item, bool)):
            raise ValueError("optional provenance time must be an integer")


def _provenance_values(value: NativeProvenanceRecord) -> tuple[object, ...]:
    return (
        value.origin_kind, value.source_channel, value.source_role, value.derivation_status,
        value.uncertainty_state, value.source_time_ns, value.capture_time_ns,
        value.memory_role, value.descriptive_notes,
    )


def _provenance_intent(value: NativeProvenanceRecord) -> dict[str, Any]:
    return {
        "origin_kind": value.origin_kind, "source_channel": value.source_channel,
        "source_role": value.source_role, "derivation_status": value.derivation_status,
        "uncertainty_state": value.uncertainty_state, "source_time_ns": value.source_time_ns,
        "capture_time_ns": value.capture_time_ns, "memory_role": value.memory_role,
        "descriptive_notes": value.descriptive_notes,
    }


def _intent_mapping(value: str) -> dict[str, Any]:
    try:
        decoded = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise SubstrateInvariantViolation("stored derived operation intent is malformed") from exc
    if not isinstance(decoded, dict):
        raise SubstrateInvariantViolation("stored derived operation intent is not an object")
    return decoded


def _new() -> bytes:
    return native_id_to_bytes(generate_native_id())


__all__ = [
    "DerivedMemoryCreateKind",
    "IdentityAnchorLifecyclePatch",
    "NativeDerivedMemoryCreationRequest",
    "NativeDerivedMemoryCreationResult",
    "NativeDerivedMemoryCreationService",
    "NativeDerivedMemorySourceResult",
    "NativeTypedMemorySuccessorRequest",
    "NativeTypedMemorySuccessorResult",
    "NativeTypedMemorySuccessorService",
    "NativeTypedMemorySuccessorSourceResult",
    "StaleDerivedMemoryPlanError",
    "derived_child_operation_key",
]
