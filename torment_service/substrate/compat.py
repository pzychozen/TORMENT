"""Namespaced core-memory compatibility views and native write primitives.

The facade is deliberately independent of ``MemoryGraph`` and legacy files.
Its EID is only a scoped compatibility alias; native object and revision UUIDs
remain the durable semantic identities.  Create and patch operations use the
ordinary native object semantic transaction path, never a JSONL shadow write.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID
import sqlite3

from torment_service.candidate_types import CandidateShapedValue
from torment_service.lifecycle import LifecycleActor, derive_protected_lifecycle_from_legacy_markers, validate_lifecycle_envelope

from .canonical_intent import canonical_intent_text
from .errors import SubstrateInvariantViolation, SubstrateObjectNotFound, SubstrateRevisionConflict
from .ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from .objects import NativeObjectService, ObjectResult, ObjectState, SubstrateTx, execute_semantic
from .representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectation,
    RepresentationIntegrityExpectationRequest,
    RepresentationMetadata,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from .schema import open_schema

_MEMORY_OBJECT_KIND = "LEGACY_CORE_NODE"


@dataclass(frozen=True)
class LegacyRepresentationReference:
    representation_id: UUID; representation_class: str; generation: int; readiness: str; operational_disposition: str; usable: bool


@dataclass(frozen=True)
class LegacyMemoryView:
    """An immutable compatibility projection, never a persisted shadow record."""
    eid: int; object_id: UUID; revision_id: UUID; revision_ordinal: int; semantic_scope_id: UUID
    existence_state: str; lifecycle_state: str; lifecycle_authoritative: bool; governance_state: str
    authority_category: str; provenance_id: UUID | None; payload: Mapping[str, Any]
    representation_references: tuple[LegacyRepresentationReference, ...]

    @property
    def summary(self) -> str | None:
        value = self.payload.get("summary", self.payload.get("text"))
        return value if isinstance(value, str) else None

    def to_legacy_dict(self) -> dict[str, Any]:
        """Return a fresh legacy-shaped read view without leaking SQLite rows."""
        value = dict(self.payload)
        value.update({"eid": self.eid, "summary": self.summary, "lifecycle_state": self.lifecycle_state,
                      "lifecycle_authoritative": self.lifecycle_authoritative, "governance_state": self.governance_state,
                      "authority_category": self.authority_category, "exists": self.existence_state == "EXISTS",
                      "representation_refs": [{"representation_class": item.representation_class, "generation": item.generation,
                          "readiness": item.readiness, "operational_disposition": item.operational_disposition, "usable": item.usable}
                          for item in self.representation_references]})
        return value


@dataclass(frozen=True)
class CompatibilityMemoryWriteResult:
    """The native publication result plus its stable scoped EID alias."""
    eid: int; object_id: UUID; revision_id: UUID; transition_id: UUID; operation_id: UUID


@dataclass(frozen=True)
class CompatibilityEmbeddingPublicationRequest:
    """Explicit already-derived embedding facts; this boundary never calls an embedder."""
    payload_bytes: bytes; representation_class: str; generation: int; derivation_contract_version: str; encoding_id: str
    dtype: str | None = None; dimension: int | None = None; dependencies: tuple[UUID, ...] = (); representation_id: UUID | None = None


@dataclass(frozen=True)
class MemoryDraft:
    """Immutable, process-local preparation state with no native semantic identity."""
    draft_token: UUID; legacy_source_namespace_id: UUID; idempotency_namespace_id: UUID; idempotency_key: str
    identity_namespace_id: UUID; semantic_scope_id: UUID; summary: str; memory_type: str; memory_class: str
    strength: float; confidence: float; half_life_days: float; user_id: str; logical_step: int
    extra_payload: Mapping[str, Any]; lifecycle_status: Mapping[str, Any] | None; governance_state: str
    provenance_id: UUID | None; embedding_request: CompatibilityEmbeddingPublicationRequest | None = None


@dataclass(frozen=True)
class MemoryDraftEmbeddingPreparation:
    """A finalized source plus PENDING representation and pre-payload expectation."""
    source: CompatibilityMemoryWriteResult; representation: RepresentationMetadata; expectation: RepresentationIntegrityExpectation


@dataclass(frozen=True)
class MemoryDraftFinalizeResult:
    """A source finalization and, when requested, its explicit READY publication."""
    source: CompatibilityMemoryWriteResult; representation: RepresentationMetadata | None = None
    expectation: RepresentationIntegrityExpectation | None = None

    @property
    def eid(self) -> int:
        return self.source.eid

    @property
    def object_id(self) -> UUID:
        return self.source.object_id

    @property
    def revision_id(self) -> UUID:
        return self.source.revision_id

    @property
    def transition_id(self) -> UUID:
        return self.source.transition_id

    @property
    def operation_id(self) -> UUID:
        return self.source.operation_id


class NativeMemoryCompatibilityFacade:
    """Substrate-owned namespaced EID facade; a namespace is always required."""
    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection); self._connection = connection

    def resolve_memory_eid(self, *, legacy_source_namespace_id: UUID, eid: int) -> UUID:
        return native_id_from_bytes(self._current_row(legacy_source_namespace_id, eid)[0])

    def resolve_native_memory_legacy_eid(self, *, legacy_source_namespace_id: UUID, native_object_id: UUID) -> int:
        object_id = native_id_to_bytes(native_object_id)
        kind = self._connection.execute("SELECT object_kind FROM objects WHERE object_id=?", (object_id,)).fetchone()
        if kind is None: raise SubstrateObjectNotFound("native object was not found")
        if kind[0] != _MEMORY_OBJECT_KIND: raise SubstrateInvariantViolation("native object is not an admissible core memory")
        aliases = self._connection.execute("SELECT alias_value FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND object_id=? ORDER BY alias_value", (native_id_to_bytes(legacy_source_namespace_id), object_id)).fetchall()
        if not aliases: raise SubstrateObjectNotFound("native core memory has no EID compatibility alias in this namespace")
        if len(aliases) != 1: raise SubstrateInvariantViolation("native core memory has ambiguous EID aliases in this namespace")
        try: eid = int(aliases[0][0])
        except (TypeError, ValueError) as exc: raise SubstrateInvariantViolation("EID alias is not an integer") from exc
        if str(eid) != aliases[0][0] or eid < 0: raise SubstrateInvariantViolation("EID alias is not canonical non-negative integer text")
        self._current_row(legacy_source_namespace_id, eid)
        return eid

    def get_memory_by_eid(self, *, legacy_source_namespace_id: UUID, eid: int) -> LegacyMemoryView:
        return self._view(eid, self._current_row(legacy_source_namespace_id, eid))

    def get_memory_revision(self, *, legacy_source_namespace_id: UUID, eid: int, revision_id: UUID) -> LegacyMemoryView:
        object_id = self.resolve_memory_eid(legacy_source_namespace_id=legacy_source_namespace_id, eid=eid)
        row = self._connection.execute("""SELECT o.object_id,r.object_revision_id,r.revision_ordinal,r.effective_semantic_scope_id,r.existence_state,r.lifecycle_state,r.lifecycle_authoritative,r.governance_state,r.authority_category,r.provenance_id,r.payload_format,r.payload_text FROM objects o JOIN object_revisions r ON r.object_id=o.object_id WHERE o.object_id=? AND r.object_revision_id=? AND o.object_kind=?""", (native_id_to_bytes(object_id), native_id_to_bytes(revision_id), _MEMORY_OBJECT_KIND)).fetchone()
        if row is None: raise SubstrateObjectNotFound("native core-memory revision was not found")
        return self._view(eid, row)

    def create_memory_state(
        self,
        *,
        legacy_source_namespace_id: UUID,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        identity_namespace_id: UUID,
        semantic_scope_id: UUID,
        summary: str,
        memory_type: str,
        memory_class: str = "core",
        strength: float = 1.0,
        confidence: float = 1.0,
        half_life_days: float = 0.0,
        user_id: str = "default",
        logical_step: int = 0,
        extra_payload: Mapping[str, Any] | None = None,
        lifecycle_status: Mapping[str, Any] | None = None,
        governance_state: str = "UNKNOWN",
        provenance_id: UUID | None = None,
    ) -> CompatibilityMemoryWriteResult:
        """Atomically publish native R1 and its newly allocated scoped EID alias.

        The caller must retain ``idempotency_namespace_id`` and
        ``idempotency_key`` to safely retry this operation.
        """
        _validate_create_inputs(summary, memory_type, memory_class, user_id, logical_step)
        flexible = _flexible_mapping(extra_payload, field="extra_payload")
        lifecycle_state, lifecycle_authoritative = _creation_lifecycle(flexible, lifecycle_status)
        payload = {
            "summary": summary,
            "type": memory_type,
            "memory_class": memory_class,
            "strength": float(strength),
            "confidence": float(confidence),
            "half_life": float(half_life_days),
            "user_id": user_id,
            "created_at": logical_step,
            "last_reinforced": logical_step,
        }
        payload.update(flexible)
        state = ObjectState(
            identity_namespace_id, semantic_scope_id, _MEMORY_OBJECT_KIND, "EXISTS",
            lifecycle_state, lifecycle_authoritative, governance_state, "NOT_APPLICABLE",
            payload, "JSON", provenance_id,
        )
        intent = canonical_intent_text({
            "kind": "CREATE_COMPAT_MEMORY_STATE",
            "legacy_source_namespace_id": str(legacy_source_namespace_id),
            "identity_namespace_id": str(identity_namespace_id),
            "semantic_scope_id": str(semantic_scope_id),
            "state": _state_intent(state),
        })
        native = NativeObjectService(self._connection)

        def mutate(tx: SubstrateTx) -> CompatibilityMemoryWriteResult:
            eid = _allocate_eid(tx, legacy_source_namespace_id)
            result = native._create(tx, state, None)
            tx.execute(
                "INSERT INTO legacy_object_aliases VALUES (?,'EID',?,?)",
                (native_id_to_bytes(legacy_source_namespace_id), str(eid), native_id_to_bytes(result.object_id)),
            )
            _assert_exact_alias(tx, legacy_source_namespace_id, eid, result.object_id)
            return _write_result(eid, result)

        return execute_semantic(
            self._connection, idempotency_namespace_id, idempotency_key,
            "CREATE_COMPAT_MEMORY_STATE", intent,
            lambda operation_id: self._write_result_for_operation(operation_id, legacy_source_namespace_id),
            mutate,
        )

    def begin_memory_draft(
        self,
        *,
        legacy_source_namespace_id: UUID,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        identity_namespace_id: UUID,
        semantic_scope_id: UUID,
        summary: str,
        memory_type: str,
        memory_class: str = "core",
        strength: float = 1.0,
        confidence: float = 1.0,
        half_life_days: float = 0.0,
        user_id: str = "default",
        logical_step: int = 0,
        extra_payload: Mapping[str, Any] | None = None,
        lifecycle_status: Mapping[str, Any] | None = None,
        governance_state: str = "UNKNOWN",
        provenance_id: UUID | None = None,
        embedding_request: CompatibilityEmbeddingPublicationRequest | None = None,
    ) -> MemoryDraft:
        """Validate and return an in-process draft without opening a semantic transaction."""
        _validate_draft_identity_inputs(
            legacy_source_namespace_id, idempotency_namespace_id, idempotency_key,
            identity_namespace_id, semantic_scope_id, governance_state, provenance_id,
        )
        _validate_create_inputs(summary, memory_type, memory_class, user_id, logical_step)
        flexible = _flexible_mapping(extra_payload, field="extra_payload")
        _creation_lifecycle(flexible, lifecycle_status)
        _validate_memory_numbers(strength, confidence, half_life_days)
        _validate_embedding_request(embedding_request)
        return MemoryDraft(
            generate_native_id(), legacy_source_namespace_id, idempotency_namespace_id, idempotency_key,
            identity_namespace_id, semantic_scope_id, summary, memory_type, memory_class,
            float(strength), float(confidence), float(half_life_days), user_id, logical_step,
            _freeze_draft_mapping(flexible), _freeze_draft_mapping(lifecycle_status) if lifecycle_status is not None else None,
            governance_state, provenance_id, embedding_request,
        )

    def enrich_memory_draft(self, draft: MemoryDraft, patch: Mapping[str, Any]) -> MemoryDraft:
        """Return a replacement draft with a deterministic flexible-payload merge."""
        _validate_memory_draft(draft)
        merged = _thaw_draft_mapping(draft.extra_payload)
        merged.update(_flexible_mapping(patch, field="draft enrichment"))
        return replace(draft, extra_payload=_freeze_draft_mapping(merged))

    def abandon_memory_draft(self, draft: MemoryDraft) -> None:
        """Explicit process-local discard; no semantic core cleanup is required."""
        _validate_memory_draft(draft)

    def finalize_memory_draft(
        self, draft: MemoryDraft, *, publish_embedding: bool = True
    ) -> MemoryDraftFinalizeResult:
        """Finalize source, then optionally run the separate representation READY workflow."""
        source = self._finalize_draft_source(draft)
        if draft.embedding_request is None or not publish_embedding:
            return MemoryDraftFinalizeResult(source)
        prepared = self._prepare_draft_embedding(draft, source)
        ready = NativeRepresentationService(self._connection).publish_representation_ready(
            idempotency_namespace_id=draft.idempotency_namespace_id,
            idempotency_key=_draft_operation_key(draft, "REPRESENTATION_READY"),
            request=RepresentationReadyRequest(
                prepared.representation.representation_id,
                draft.embedding_request.representation_class,
                draft.embedding_request.generation,
                draft.embedding_request.derivation_contract_version,
                draft.embedding_request.encoding_id,
                draft.embedding_request.payload_bytes,
            ),
        )
        return MemoryDraftFinalizeResult(source, ready, prepared.expectation)

    def prepare_memory_draft_embedding(self, draft: MemoryDraft) -> MemoryDraftEmbeddingPreparation:
        """Finalize/recover source, then create PENDING representation and expectation only."""
        return self._prepare_draft_embedding(draft, self._finalize_draft_source(draft))

    def _finalize_draft_source(self, draft: MemoryDraft) -> CompatibilityMemoryWriteResult:
        _validate_memory_draft(draft)
        return self.create_memory_state(
            legacy_source_namespace_id=draft.legacy_source_namespace_id,
            idempotency_namespace_id=draft.idempotency_namespace_id,
            idempotency_key=_draft_operation_key(draft, "SOURCE_FINALIZE"),
            identity_namespace_id=draft.identity_namespace_id,
            semantic_scope_id=draft.semantic_scope_id,
            summary=draft.summary,
            memory_type=draft.memory_type,
            memory_class=draft.memory_class,
            strength=draft.strength,
            confidence=draft.confidence,
            half_life_days=draft.half_life_days,
            user_id=draft.user_id,
            logical_step=draft.logical_step,
            extra_payload=_thaw_draft_mapping(draft.extra_payload),
            lifecycle_status=_thaw_draft_mapping(draft.lifecycle_status) if draft.lifecycle_status is not None else None,
            governance_state=draft.governance_state,
            provenance_id=draft.provenance_id,
        )

    def _prepare_draft_embedding(
        self, draft: MemoryDraft, source: CompatibilityMemoryWriteResult
    ) -> MemoryDraftEmbeddingPreparation:
        _validate_memory_draft(draft)
        request = draft.embedding_request
        if request is None:
            raise ValueError("draft has no embedding publication request")
        service = NativeRepresentationService(self._connection)
        pending = service.create_representation_pending(
            idempotency_namespace_id=draft.idempotency_namespace_id,
            idempotency_key=_draft_operation_key(draft, "REPRESENTATION_PENDING"),
            request=RepresentationRequest(
                "OBJECT_REVISION", source.object_id, source.revision_id, None, None,
                request.representation_class, request.generation, request.derivation_contract_version,
                request.encoding_id, request.dtype, request.dimension, request.dependencies,
                request.representation_id, len(request.payload_bytes),
            ),
        )
        expectation = service.establish_representation_integrity_expectation(
            idempotency_namespace_id=draft.idempotency_namespace_id,
            idempotency_key=_draft_operation_key(draft, "REPRESENTATION_EXPECTATION"),
            request=RepresentationIntegrityExpectationRequest(
                pending.representation_id, INTEGRITY_ALGORITHM_SHA256,
                hashlib.sha256(request.payload_bytes).digest(), INTEGRITY_VALUE_ENCODING_RAW,
            ),
        )
        return MemoryDraftEmbeddingPreparation(source, pending, expectation)

    def patch_memory_state(
        self,
        *,
        legacy_source_namespace_id: UUID,
        eid: int,
        patch: Mapping[str, Any],
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        expected_revision_id: UUID | None = None,
    ) -> CompatibilityMemoryWriteResult:
        """Merge permitted flexible fields into one native ordinary successor."""
        _validate_eid(eid)
        flexible = _flexible_mapping(patch, field="patch")
        if expected_revision_id is not None and not isinstance(expected_revision_id, UUID):
            raise ValueError("expected_revision_id must be a UUID when supplied")
        intent = canonical_intent_text({
            "kind": "PATCH_COMPAT_MEMORY_STATE",
            "legacy_source_namespace_id": str(legacy_source_namespace_id),
            "eid": eid,
            "expected_revision_id": str(expected_revision_id) if expected_revision_id else None,
            "patch": flexible,
        })
        native = NativeObjectService(self._connection)

        def mutate(tx: SubstrateTx) -> CompatibilityMemoryWriteResult:
            row = _current_memory_row(tx, legacy_source_namespace_id, eid)
            current_revision_id = native_id_from_bytes(row[1])
            if expected_revision_id is not None and expected_revision_id != current_revision_id:
                raise SubstrateRevisionConflict("expected predecessor is not current")
            payload = _payload_mapping(row[12], row[13])
            payload.update(flexible)
            state = ObjectState(
                native_id_from_bytes(row[3]), native_id_from_bytes(row[4]), row[5], row[6],
                row[7], bool(row[8]), row[9], row[10], payload, "JSON",
                native_id_from_bytes(row[11]) if row[11] is not None else None,
            )
            result = native._successor(tx, native_id_from_bytes(row[0]), current_revision_id, state)
            _assert_exact_alias(tx, legacy_source_namespace_id, eid, result.object_id)
            return _write_result(eid, result)

        return execute_semantic(
            self._connection, idempotency_namespace_id, idempotency_key,
            "PATCH_COMPAT_MEMORY_STATE", intent,
            lambda operation_id: self._write_result_for_operation(operation_id, legacy_source_namespace_id),
            mutate,
        )

    def _current_row(self, namespace: UUID, eid: int) -> tuple[Any, ...]:
        _validate_eid(eid)
        row = self._connection.execute("""SELECT o.object_id,r.object_revision_id,r.revision_ordinal,r.effective_semantic_scope_id,r.existence_state,r.lifecycle_state,r.lifecycle_authoritative,r.governance_state,r.authority_category,r.provenance_id,r.payload_format,r.payload_text FROM legacy_object_aliases a JOIN objects o ON o.object_id=a.object_id JOIN object_revisions r ON r.object_id=o.object_id AND r.object_revision_id=o.current_revision_id AND r.revision_ordinal=o.current_revision_ordinal WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID' AND a.alias_value=?""", (native_id_to_bytes(namespace), str(eid))).fetchone()
        if row is None: raise SubstrateObjectNotFound("namespaced EID compatibility alias was not found")
        if self._connection.execute("SELECT object_kind FROM objects WHERE object_id=?", (row[0],)).fetchone()[0] != _MEMORY_OBJECT_KIND: raise SubstrateInvariantViolation("EID alias does not target an admissible core memory")
        return row

    def _write_result_for_operation(self, operation_id: bytes, namespace: UUID) -> CompatibilityMemoryWriteResult | None:
        row = self._connection.execute(
            """SELECT o.object_id,o.object_revision_id,t.transition_id,t.operation_id
               FROM operation_outputs o JOIN semantic_transitions t ON t.operation_id=o.operation_id
               WHERE o.operation_id=? AND o.output_kind='OBJECT'
               ORDER BY o.output_ordinal LIMIT 1""",
            (operation_id,),
        ).fetchone()
        if row is None:
            return None
        aliases = self._connection.execute(
            "SELECT alias_value FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND object_id=? ORDER BY alias_value",
            (native_id_to_bytes(namespace), row[0]),
        ).fetchall()
        if len(aliases) != 1:
            raise SubstrateInvariantViolation("compatibility write operation has no unambiguous EID alias")
        return _write_result(_canonical_eid(aliases[0][0]), ObjectResult(
            native_id_from_bytes(row[0]), native_id_from_bytes(row[1]),
            native_id_from_bytes(row[2]), native_id_from_bytes(row[3]),
        ))

    def _view(self, eid: int, row: tuple[Any, ...]) -> LegacyMemoryView:
        refs = tuple(LegacyRepresentationReference(native_id_from_bytes(item[0]), item[1], item[2], item[3], item[4], item[3] == "READY" and item[4] == "USABLE") for item in self._connection.execute("""SELECT r.representation_id,r.representation_class,r.generation,s.readiness,s.operational_disposition FROM representations r JOIN representation_current_state s USING(representation_id) WHERE r.source_kind='OBJECT_REVISION' AND r.source_object_id=? AND r.source_object_revision_id=? AND r.source_object_revision_ordinal=? ORDER BY r.representation_class,r.generation,r.representation_id""", (row[0], row[1], row[2])))
        return LegacyMemoryView(eid, native_id_from_bytes(row[0]), native_id_from_bytes(row[1]), row[2], native_id_from_bytes(row[3]), row[4], row[5], bool(row[6]), row[7], row[8], native_id_from_bytes(row[9]) if row[9] is not None else None, MappingProxyType(_payload_mapping(row[10], row[11])), refs)


def _payload_mapping(payload_format: str, payload_text: str | None) -> dict[str, Any]:
    if payload_text is None: return {}
    if payload_format in {"JSON", "TEXT"}:
        try: value = json.loads(payload_text)
        except json.JSONDecodeError: return {"content": payload_text}
        return value if isinstance(value, dict) else {"content": payload_text}
    return {}


_STRUCTURAL_PAYLOAD_KEYS = frozenset({
    "semantic_scope_id", "scope", "lifecycle", "lifecycle_state", "lifecycle_status",
    "lifecycle_authoritative", "governance", "governance_state", "authority_category",
    "authorization", "provenance", "provenance_id", "identity_namespace_id", "object_id",
    "object_kind", "eid", "revision", "revision_id", "object_revision_id",
    "object_revision_ordinal", "predecessor", "predecessor_revision_id",
    "predecessor_revision_ordinal", "representation", "representation_id", "readiness",
    "representation_readiness", "integrity", "integrity_expectation", "integrity_measurement",
    "reconciliation", "operation_id", "transition_id",
})


def _validate_eid(eid: int) -> None:
    if not isinstance(eid, int) or isinstance(eid, bool) or eid < 0:
        raise ValueError("compatibility EID must be a non-negative integer")


def _canonical_eid(value: Any) -> int:
    try:
        eid = int(value)
    except (TypeError, ValueError) as exc:
        raise SubstrateInvariantViolation("EID alias is not an integer") from exc
    if str(eid) != value or eid < 0:
        raise SubstrateInvariantViolation("EID alias is not canonical non-negative integer text")
    return eid


def _flexible_mapping(value: Mapping[str, Any] | None, *, field: str) -> dict[str, Any]:
    if isinstance(value, CandidateShapedValue):
        raise TypeError(f"candidate-shaped value cannot be written as ordinary memory {field}")
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an ordinary mapping")
    copied = dict(value)
    for key, item in copied.items():
        if not isinstance(key, str):
            raise ValueError(f"{field} keys must be strings")
        if isinstance(item, CandidateShapedValue):
            raise TypeError("candidate-shaped value cannot be written into ordinary memory payload")
        if key.casefold() in _STRUCTURAL_PAYLOAD_KEYS:
            raise ValueError(f"{field} cannot overwrite structural substrate semantics")
    return copied


def _validate_create_inputs(summary: Any, memory_type: Any, memory_class: Any, user_id: Any, logical_step: Any) -> None:
    if isinstance(summary, CandidateShapedValue):
        raise TypeError("candidate-shaped value cannot be written as ordinary memory summary")
    if not isinstance(summary, str):
        raise ValueError("summary must be a string")
    for field, value in (("memory_type", memory_type), ("memory_class", memory_class), ("user_id", user_id)):
        if not isinstance(value, str):
            raise ValueError(f"{field} must be a string")
    if not isinstance(logical_step, int) or isinstance(logical_step, bool):
        raise ValueError("logical_step must be an integer")


def _creation_lifecycle(payload: Mapping[str, Any], supplied: Mapping[str, Any] | None) -> tuple[str, bool]:
    if supplied is not None:
        status = validate_lifecycle_envelope(supplied)
    else:
        status = derive_protected_lifecycle_from_legacy_markers(dict(payload), actor=LifecycleActor.SYSTEM)
        if status is None:
            return "UNSET", True
    return status.state.value.upper(), status.is_authoritative_on_row


def _state_intent(state: ObjectState) -> dict[str, Any]:
    return {
        "identity_namespace_id": str(state.identity_namespace_id), "semantic_scope_id": str(state.semantic_scope_id),
        "object_kind": state.object_kind, "existence_state": state.existence_state,
        "lifecycle_state": state.lifecycle_state, "lifecycle_authoritative": state.lifecycle_authoritative,
        "governance_state": state.governance_state, "authority_category": state.authority_category,
        "payload": state.payload, "payload_format": state.payload_format,
        "provenance_id": str(state.provenance_id) if state.provenance_id else None,
    }


def _allocate_eid(tx: SubstrateTx, namespace: UUID) -> int:
    values = tx.execute(
        "SELECT alias_value FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID'",
        (native_id_to_bytes(namespace),),
    ).fetchall()
    return max((_canonical_eid(row[0]) for row in values), default=-1) + 1


def _assert_exact_alias(tx: SubstrateTx, namespace: UUID, eid: int, object_id: UUID) -> None:
    row = tx.execute(
        "SELECT object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND alias_value=?",
        (native_id_to_bytes(namespace), str(eid)),
    ).fetchone()
    if row is None or row[0] != native_id_to_bytes(object_id):
        raise SubstrateInvariantViolation("compatibility EID alias does not match native publication")


def _current_memory_row(tx: SubstrateTx, namespace: UUID, eid: int) -> tuple[Any, ...]:
    row = tx.execute(
        """SELECT o.object_id,r.object_revision_id,r.revision_ordinal,o.identity_namespace_id,
                  r.effective_semantic_scope_id,o.object_kind,r.existence_state,r.lifecycle_state,
                  r.lifecycle_authoritative,r.governance_state,r.authority_category,r.provenance_id,
                  r.payload_format,r.payload_text
           FROM legacy_object_aliases a JOIN objects o ON o.object_id=a.object_id
           JOIN object_revisions r ON r.object_id=o.object_id AND r.object_revision_id=o.current_revision_id
              AND r.revision_ordinal=o.current_revision_ordinal
           WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID' AND a.alias_value=?""",
        (native_id_to_bytes(namespace), str(eid)),
    ).fetchone()
    if row is None:
        raise SubstrateObjectNotFound("namespaced EID compatibility alias was not found")
    if row[5] != _MEMORY_OBJECT_KIND:
        raise SubstrateInvariantViolation("EID alias does not target an admissible core memory")
    return row


def _write_result(eid: int, result: ObjectResult) -> CompatibilityMemoryWriteResult:
    return CompatibilityMemoryWriteResult(eid, result.object_id, result.revision_id, result.transition_id, result.operation_id)


def _validate_draft_identity_inputs(
    source_namespace: Any, idempotency_namespace: Any, idempotency_key: Any,
    identity_namespace: Any, semantic_scope: Any, governance_state: Any, provenance_id: Any,
) -> None:
    for field, value in (
        ("legacy_source_namespace_id", source_namespace),
        ("idempotency_namespace_id", idempotency_namespace),
        ("identity_namespace_id", identity_namespace),
        ("semantic_scope_id", semantic_scope),
    ):
        if not isinstance(value, UUID):
            raise ValueError(f"{field} must be a UUID")
    if not isinstance(idempotency_key, str) or not idempotency_key:
        raise ValueError("idempotency_key must be a non-empty string")
    if not isinstance(governance_state, str) or not governance_state:
        raise ValueError("governance_state must be a non-empty string")
    if provenance_id is not None and not isinstance(provenance_id, UUID):
        raise ValueError("provenance_id must be a UUID when supplied")


def _validate_memory_numbers(strength: Any, confidence: Any, half_life_days: Any) -> None:
    for field, value in (("strength", strength), ("confidence", confidence), ("half_life_days", half_life_days)):
        try:
            converted = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field} must be a finite number") from exc
        if not math.isfinite(converted):
            raise ValueError(f"{field} must be a finite number")


def _validate_embedding_request(request: CompatibilityEmbeddingPublicationRequest | None) -> None:
    if request is None:
        return
    if not isinstance(request, CompatibilityEmbeddingPublicationRequest):
        raise ValueError("embedding_request must be a CompatibilityEmbeddingPublicationRequest")
    if type(request.payload_bytes) is not bytes:
        raise ValueError("embedding payload must be immutable bytes")
    if not isinstance(request.generation, int) or isinstance(request.generation, bool) or request.generation < 1:
        raise ValueError("embedding representation generation must be a positive integer")
    if not all(isinstance(value, str) and value for value in (request.representation_class, request.derivation_contract_version, request.encoding_id)):
        raise ValueError("embedding representation contract fields must be non-empty strings")
    if request.dtype is not None and not isinstance(request.dtype, str):
        raise ValueError("embedding dtype must be a string when supplied")
    if request.dimension is not None and (not isinstance(request.dimension, int) or isinstance(request.dimension, bool) or request.dimension < 1):
        raise ValueError("embedding dimension must be a positive integer when supplied")
    if not isinstance(request.dependencies, tuple) or any(not isinstance(item, UUID) for item in request.dependencies):
        raise ValueError("embedding dependencies must be a tuple of UUIDs")
    if len(set(request.dependencies)) != len(request.dependencies):
        raise ValueError("embedding dependencies must not repeat")
    if request.representation_id is not None and not isinstance(request.representation_id, UUID):
        raise ValueError("representation_id must be a UUID when supplied")


def _validate_memory_draft(draft: Any) -> None:
    if not isinstance(draft, MemoryDraft):
        raise ValueError("a MemoryDraft is required")
    _validate_draft_identity_inputs(
        draft.legacy_source_namespace_id, draft.idempotency_namespace_id, draft.idempotency_key,
        draft.identity_namespace_id, draft.semantic_scope_id, draft.governance_state, draft.provenance_id,
    )
    _validate_create_inputs(draft.summary, draft.memory_type, draft.memory_class, draft.user_id, draft.logical_step)
    _flexible_mapping(draft.extra_payload, field="draft payload")
    _creation_lifecycle(_thaw_draft_mapping(draft.extra_payload), _thaw_draft_mapping(draft.lifecycle_status) if draft.lifecycle_status is not None else None)
    _validate_memory_numbers(draft.strength, draft.confidence, draft.half_life_days)
    _validate_embedding_request(draft.embedding_request)


def _draft_operation_key(draft: MemoryDraft, phase: str) -> str:
    return f"COMPAT_MEMORY_DRAFT:{phase}:{draft.idempotency_key}"


def _freeze_draft_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("draft mapping must be a mapping")
    return MappingProxyType({key: _freeze_draft_value(item) for key, item in value.items()})


def _freeze_draft_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_draft_mapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_draft_value(item) for item in value)
    return value


def _thaw_draft_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: _thaw_draft_value(item) for key, item in value.items()}


def _thaw_draft_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _thaw_draft_mapping(value)
    if isinstance(value, tuple):
        return [_thaw_draft_value(item) for item in value]
    return value
