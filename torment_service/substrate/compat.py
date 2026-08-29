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
import time
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID
import sqlite3

import numpy as np

from torment_service.candidate_types import CandidateShapedValue
from torment_service.lifecycle import LifecycleActor, derive_protected_lifecycle_from_legacy_markers, validate_lifecycle_envelope

from .canonical_intent import canonical_intent_text
from .errors import SubstrateInvariantViolation, SubstrateObjectNotFound, SubstrateRevisionConflict
from .ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from .objects import NativeObjectService, ObjectResult, ObjectState, SubstrateTx, execute_semantic
from .relationships import Endpoint, NativeRelationshipService, RelationshipResult, RelationshipState
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
_COMPAT_EMBEDDING_REPRESENTATION_CLASS = "COMPAT_EMBEDDING"
_COMPAT_EMBEDDING_GENERATION = 1
_COMPAT_EMBEDDING_DERIVATION_CONTRACT = "compat-embedding-v1"
_COMPAT_EMBEDDING_ENCODING = "RAW_VECTOR"
_COMPAT_EMBEDDING_DTYPE = "float32"
_DECAY_RANKING_FLOOR = 0.03


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
class CompatibilityMemoryRelationshipResult:
    """A native LINK publication addressed by the caller's scoped endpoint EIDs."""
    source_eid: int; target_eid: int; relationship_id: UUID; revision_id: UUID
    transition_id: UUID; operation_id: UUID


@dataclass(frozen=True)
class CompatibilityMemoryRelationshipView:
    """Scoped compatibility projection of a native identity-bound LINK relationship."""
    source_eid: int; target_eid: int; relationship_id: UUID; revision_id: UUID
    revision_ordinal: int; semantic_scope_id: UUID; relationship_kind: str
    weight: float; legacy_timestamp: str | int | float | None; payload: Mapping[str, Any]


@dataclass(frozen=True)
class CompatibilityEmbeddingSearchResult:
    """An immutable current-memory compatibility result from one native vector lane."""
    eid: int; object_id: UUID; revision_id: UUID; representation_id: UUID
    score: float; raw_score: float; decay_factor: float
    summary: str; memory_type: str; strength: float; confidence: float; step: int; ts: int
    semantic_scope_id: UUID; lifecycle_state: str; lifecycle_authoritative: bool
    governance_state: str; authority_category: str; payload: Mapping[str, Any]

    def to_legacy_dict(self) -> dict[str, Any]:
        """Return a fresh legacy-shaped projection with structural truth last."""
        result = dict(self.payload)
        result.update({
            "eid": self.eid, "score": self.score, "raw_score": self.raw_score,
            "decay_factor": self.decay_factor, "summary": self.summary,
            "type": self.memory_type, "strength": self.strength,
            "confidence": self.confidence, "step": self.step, "ts": self.ts,
            "semantic_scope_id": str(self.semantic_scope_id),
            "lifecycle_state": self.lifecycle_state,
            "lifecycle_authoritative": self.lifecycle_authoritative,
            "governance_state": self.governance_state,
            "authority_category": self.authority_category,
        })
        return result


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

    def create_memory_relationship(
        self,
        *,
        source_legacy_source_namespace_id: UUID,
        source_eid: int,
        target_legacy_source_namespace_id: UUID,
        target_eid: int,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        identity_namespace_id: UUID,
        semantic_scope_id: UUID,
        relationship_kind: str = "LINK",
        weight: float = 1.0,
        legacy_timestamp: str | int | float | None = None,
        extra_payload: Mapping[str, Any] | None = None,
        governance_state: str = "UNKNOWN",
    ) -> CompatibilityMemoryRelationshipResult:
        """Publish one native, identity-bound LINK between two committed memories.

        Endpoint EIDs are intentionally scoped aliases rather than global native
        identifiers. This primitive does not consume drafts, edge dictionaries,
        or MemoryGraph state, and it has no endpoint-based de-duplication rule.
        """
        _validate_relationship_inputs(
            source_legacy_source_namespace_id, source_eid,
            target_legacy_source_namespace_id, target_eid,
            idempotency_namespace_id, idempotency_key,
            identity_namespace_id, semantic_scope_id, relationship_kind,
            weight, legacy_timestamp, governance_state,
        )
        flexible = _relationship_flexible_mapping(extra_payload, field="extra_payload")

        # Resolve and carrier-check both aliases before a semantic operation is
        # opened. A failed draft token, unknown EID, or incompatible carrier
        # therefore cannot publish even a partial relationship.
        source = self._current_row(source_legacy_source_namespace_id, source_eid)
        target = self._current_row(target_legacy_source_namespace_id, target_eid)
        payload: dict[str, Any] = {"weight": float(weight)}
        if legacy_timestamp is not None:
            payload["legacy_timestamp"] = legacy_timestamp
        payload.update(flexible)
        state = RelationshipState(
            identity_namespace_id, semantic_scope_id, "LINK", "EXISTS", "UNSET", True,
            governance_state, "NOT_APPLICABLE",
            (
                Endpoint(0, "SOURCE", native_id_from_bytes(source[3]), native_id_from_bytes(source[0]), "IDENTITY"),
                Endpoint(1, "TARGET", native_id_from_bytes(target[3]), native_id_from_bytes(target[0]), "IDENTITY"),
            ),
            payload, "JSON",
        )
        intent = canonical_intent_text({
            "kind": "CREATE_COMPAT_MEMORY_RELATIONSHIP",
            "source": {"legacy_source_namespace_id": str(source_legacy_source_namespace_id), "eid": source_eid},
            "target": {"legacy_source_namespace_id": str(target_legacy_source_namespace_id), "eid": target_eid},
            "state": _relationship_state_intent(state),
        })
        native = NativeRelationshipService(self._connection)

        def mutate(tx: SubstrateTx) -> CompatibilityMemoryRelationshipResult:
            result = native._create(tx, state, None)
            return _relationship_result(source_eid, target_eid, result)

        return execute_semantic(
            self._connection, idempotency_namespace_id, idempotency_key,
            "CREATE_COMPAT_MEMORY_RELATIONSHIP", intent,
            lambda operation_id: self._relationship_result_for_operation(operation_id, source_eid, target_eid),
            mutate,
        )

    def get_memory_relationship(
        self,
        *,
        relationship_id: UUID,
        source_legacy_source_namespace_id: UUID,
        target_legacy_source_namespace_id: UUID,
    ) -> CompatibilityMemoryRelationshipView:
        """Project a compatibility-created LINK through caller-supplied namespaces.

        Reverse alias lookup is deliberately scoped. The projection fails rather
        than fabricating an EID when either endpoint has no unique alias in the
        requested namespace.
        """
        if not isinstance(relationship_id, UUID):
            raise ValueError("relationship_id must be a UUID")
        for field, value in (
            ("source_legacy_source_namespace_id", source_legacy_source_namespace_id),
            ("target_legacy_source_namespace_id", target_legacy_source_namespace_id),
        ):
            if not isinstance(value, UUID):
                raise ValueError(f"{field} must be a UUID")
        row = self._connection.execute(
            """SELECT h.relationship_kind,r.relationship_revision_id,r.revision_ordinal,
                      r.effective_semantic_scope_id,r.payload_format,r.payload_text
                 FROM relationships h JOIN relationship_revisions r
                   ON r.relationship_revision_id=h.current_revision_id
                WHERE h.relationship_id=?""",
            (native_id_to_bytes(relationship_id),),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("native relationship was not found")
        if row[0] != "LINK":
            raise SubstrateInvariantViolation("native relationship is not an admissible compatibility LINK")
        endpoints = NativeRelationshipService(self._connection).get_current_relationship(relationship_id).endpoints
        if len(endpoints) != 2 or tuple((item.ordinal, item.role) for item in endpoints) != ((0, "SOURCE"), (1, "TARGET")):
            raise SubstrateInvariantViolation("compatibility LINK endpoint aggregate is incomplete")
        source, target = endpoints
        if any(item.binding_mode != "IDENTITY" or item.object_revision_id is not None for item in endpoints):
            raise SubstrateInvariantViolation("compatibility LINK endpoints must use identity binding")
        source_eid = self.resolve_native_memory_legacy_eid(
            legacy_source_namespace_id=source_legacy_source_namespace_id, native_object_id=source.object_id,
        )
        target_eid = self.resolve_native_memory_legacy_eid(
            legacy_source_namespace_id=target_legacy_source_namespace_id, native_object_id=target.object_id,
        )
        payload = _payload_mapping(row[4], row[5])
        value = payload.get("legacy_timestamp")
        timestamp = value if isinstance(value, (str, int, float)) and not isinstance(value, bool) else None
        weight = payload.get("weight")
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or not math.isfinite(float(weight)):
            raise SubstrateInvariantViolation("compatibility LINK has no finite weight payload")
        return CompatibilityMemoryRelationshipView(
            source_eid, target_eid, relationship_id, native_id_from_bytes(row[1]), row[2],
            native_id_from_bytes(row[3]), row[0], float(weight), timestamp, MappingProxyType(payload),
        )

    def search_by_embedding(
        self,
        *,
        legacy_source_namespace_id: UUID,
        embedding: Any,
        dimension: int,
        representation_class: str = _COMPAT_EMBEDDING_REPRESENTATION_CLASS,
        generation: int = _COMPAT_EMBEDDING_GENERATION,
        derivation_contract_version: str = _COMPAT_EMBEDDING_DERIVATION_CONTRACT,
        encoding_id: str = _COMPAT_EMBEDDING_ENCODING,
        dtype: str = _COMPAT_EMBEDDING_DTYPE,
        top_k: int = 8,
        user_id: str | None = None,
        min_score: float | None = None,
        type_filter: tuple[str, ...] | list[str] | None = None,
        canon_only: bool = False,
        now_ts: float | int | None = None,
    ) -> tuple[CompatibilityEmbeddingSearchResult, ...]:
        """Read-only exact cosine search over one explicit native embedding lane.

        The method never imports ``MemoryGraph`` or examines legacy files. Only
        representations with durable READY/USABLE/MATCH state and a source equal
        to the current native core-memory revision are considered.
        """
        query, limit, score_floor, type_set, effective_now = _validate_search_inputs(
            legacy_source_namespace_id, embedding, dimension, representation_class,
            generation, derivation_contract_version, encoding_id, dtype, top_k,
            user_id, min_score, type_filter, canon_only, now_ts,
        )
        candidates = self._eligible_embedding_candidates(
            legacy_source_namespace_id=legacy_source_namespace_id,
            representation_class=representation_class,
            generation=generation,
            derivation_contract_version=derivation_contract_version,
            encoding_id=encoding_id,
            dtype=dtype,
            dimension=dimension,
        )
        representations = NativeRepresentationService(self._connection)
        scored: list[tuple[float, int, bytes, bytes, bytes]] = []
        seen_objects: set[bytes] = set()
        for representation_id, object_id, source_revision_id, expected_length, alias_value in candidates:
            if object_id in seen_objects:
                raise SubstrateInvariantViolation("compatibility search lane has contradictory eligible representations")
            seen_objects.add(object_id)
            eid = _canonical_eid(alias_value)
            metadata = representations.get_representation_metadata(UUID(bytes=representation_id))
            if not _metadata_is_search_eligible(metadata):
                continue
            payload = representations.read_representation_payload(UUID(bytes=representation_id))
            vector = _decode_compat_embedding_payload(payload, expected_length, dtype, dimension)
            if vector is None:
                continue
            raw_score = float(np.dot(vector, query))
            scored.append((raw_score, eid, representation_id, object_id, source_revision_id))

        # This intentionally takes the raw-score top-k before all legacy-facing
        # filters. A filter may therefore leave fewer than ``top_k`` results.
        scored.sort(key=lambda item: (-item[0], item[1], item[2]))
        results: list[CompatibilityEmbeddingSearchResult] = []
        for raw_score, eid, representation_id, object_id, source_revision_id in scored[:limit]:
            if score_floor is not None and raw_score < score_floor:
                continue
            current = self._current_row(legacy_source_namespace_id, eid)
            if current[0] != object_id or current[1] != source_revision_id:
                # The source advanced after candidate selection. Never return a
                # historical vector as though it described the new current state.
                continue
            payload = _payload_mapping(current[10], current[11])
            if canon_only and not payload.get("canon", False):
                continue
            if user_id is not None and str(payload.get("user_id", "")) != user_id:
                continue
            memory_type = str(payload.get("type") or payload.get("mtype") or "")
            if type_set and memory_type and memory_type not in type_set:
                continue
            decay = _compat_half_life_decay_factor(payload, effective_now)
            results.append(CompatibilityEmbeddingSearchResult(
                eid, native_id_from_bytes(current[0]), native_id_from_bytes(current[1]),
                UUID(bytes=representation_id), raw_score * decay, raw_score, decay,
                _compat_summary(payload), memory_type or "memory",
                _compat_number(payload.get("strength")), _compat_number(payload.get("confidence")),
                _compat_int(payload.get("step") or payload.get("born_step") or payload.get("created_at")),
                _compat_int(payload.get("ts") or payload.get("created_ts")),
                native_id_from_bytes(current[3]), current[5], bool(current[6]), current[7], current[8],
                MappingProxyType(payload),
            ))
        results.sort(key=lambda item: (-item.score, item.eid, item.representation_id.bytes))
        return tuple(results)

    def _eligible_embedding_candidates(
        self,
        *,
        legacy_source_namespace_id: UUID,
        representation_class: str,
        generation: int,
        derivation_contract_version: str,
        encoding_id: str,
        dtype: str,
        dimension: int,
    ) -> tuple[tuple[bytes, bytes, bytes, int | None, str], ...]:
        """Return metadata only; usable bytes are later loaded via the native service."""
        rows = self._connection.execute(
            """
            SELECT r.representation_id,r.source_object_id,r.source_object_revision_id,
                   r.expected_payload_byte_length,a.alias_value
            FROM representations r
            JOIN representation_current_state s USING(representation_id)
            JOIN integrity_measurements m ON m.measurement_id=s.selected_integrity_measurement_id
            JOIN objects o ON o.object_id=r.source_object_id
            JOIN legacy_object_aliases a ON a.object_id=o.object_id
            WHERE r.source_kind='OBJECT_REVISION'
              AND o.object_kind=?
              AND r.source_object_revision_id=o.current_revision_id
              AND r.source_object_revision_ordinal=o.current_revision_ordinal
              AND a.legacy_source_namespace_id=? AND a.alias_kind='EID'
              AND r.representation_class=? AND r.generation=?
              AND r.derivation_contract_version=? AND r.encoding_id=?
              AND r.dtype=? AND r.dimension=?
              AND s.readiness='READY' AND s.operational_disposition='USABLE'
              AND m.result='MATCH'
              AND EXISTS (
                  SELECT 1 FROM integrity_expectations e
                  WHERE e.subject_kind='REPRESENTATION' AND e.representation_id=r.representation_id
              )
              AND NOT EXISTS (
                  SELECT 1
                  FROM reconciliation_cases c
                  JOIN reconciliation_case_states cs
                    ON cs.reconciliation_case_id=c.reconciliation_case_id
                   AND cs.reconciliation_state_id=c.current_state_id
                   AND cs.state_ordinal=c.current_state_ordinal
                  WHERE c.subject_kind='REPRESENTATION' AND c.representation_id=r.representation_id
                    AND cs.operational_disposition<>'USABLE'
              )
            ORDER BY a.alias_value,r.representation_id
            """,
            (
                _MEMORY_OBJECT_KIND, native_id_to_bytes(legacy_source_namespace_id),
                representation_class, generation, derivation_contract_version, encoding_id, dtype, dimension,
            ),
        ).fetchall()
        return tuple((row[0], row[1], row[2], row[3], row[4]) for row in rows)

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

    def _relationship_result_for_operation(
        self, operation_id: bytes, source_eid: int, target_eid: int,
    ) -> CompatibilityMemoryRelationshipResult | None:
        row = self._connection.execute(
            """SELECT o.relationship_id,o.relationship_revision_id,t.transition_id,t.operation_id
                 FROM operation_outputs o JOIN semantic_transitions t ON t.operation_id=o.operation_id
                WHERE o.operation_id=? AND o.output_kind='RELATIONSHIP'
                ORDER BY o.output_ordinal LIMIT 1""",
            (operation_id,),
        ).fetchone()
        if row is None:
            return None
        return _relationship_result(source_eid, target_eid, RelationshipResult(
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

_RELATIONSHIP_STRUCTURAL_PAYLOAD_KEYS = _STRUCTURAL_PAYLOAD_KEYS | frozenset({
    "relationship_id", "relationship_kind", "relationship_revision_id",
    "relationship_revision_ordinal", "endpoint", "endpoints", "endpoint_ordinal",
    "endpoint_role", "endpoint_semantic_scope_id", "source", "source_eid",
    "target", "target_eid", "binding", "binding_mode", "bound_object_revision_id",
    "bound_object_revision_ordinal", "weight", "legacy_timestamp", "authority",
    "active_authorization", "authorization_state",
})


def _relationship_result(
    source_eid: int, target_eid: int, result: RelationshipResult,
) -> CompatibilityMemoryRelationshipResult:
    return CompatibilityMemoryRelationshipResult(
        source_eid, target_eid, result.relationship_id, result.revision_id,
        result.transition_id, result.operation_id,
    )


def _relationship_state_intent(state: RelationshipState) -> dict[str, Any]:
    return {
        "identity_namespace_id": str(state.identity_namespace_id),
        "semantic_scope_id": str(state.semantic_scope_id),
        "relationship_kind": state.relationship_kind,
        "existence_state": state.existence_state,
        "lifecycle_state": state.lifecycle_state,
        "lifecycle_authoritative": state.lifecycle_authoritative,
        "governance_state": state.governance_state,
        "authority_category": state.authority_category,
        "payload": state.payload,
        "payload_format": state.payload_format,
        "endpoints": [
            {
                "ordinal": endpoint.ordinal, "role": endpoint.role,
                "semantic_scope_id": str(endpoint.semantic_scope_id),
                "object_id": str(endpoint.object_id), "binding_mode": endpoint.binding_mode,
                "object_revision_id": str(endpoint.object_revision_id) if endpoint.object_revision_id else None,
            }
            for endpoint in state.endpoints
        ],
    }


def _validate_relationship_inputs(
    source_namespace: Any, source_eid: Any, target_namespace: Any, target_eid: Any,
    idempotency_namespace: Any, idempotency_key: Any, identity_namespace: Any,
    semantic_scope: Any, relationship_kind: Any, weight: Any, legacy_timestamp: Any,
    governance_state: Any,
) -> None:
    for field, value in (
        ("source_legacy_source_namespace_id", source_namespace),
        ("target_legacy_source_namespace_id", target_namespace),
        ("idempotency_namespace_id", idempotency_namespace),
        ("identity_namespace_id", identity_namespace),
        ("semantic_scope_id", semantic_scope),
    ):
        if not isinstance(value, UUID):
            raise ValueError(f"{field} must be a UUID")
    _validate_eid(source_eid)
    _validate_eid(target_eid)
    if not isinstance(idempotency_key, str) or not idempotency_key:
        raise ValueError("idempotency_key must be a non-empty string")
    if relationship_kind != "LINK":
        raise ValueError("only the LINK compatibility relationship kind is supported")
    if isinstance(weight, bool):
        raise ValueError("weight must be a finite number")
    try:
        numeric_weight = float(weight)
    except (TypeError, ValueError) as exc:
        raise ValueError("weight must be a finite number") from exc
    if not math.isfinite(numeric_weight):
        raise ValueError("weight must be a finite number")
    if legacy_timestamp is not None:
        if isinstance(legacy_timestamp, bool) or not isinstance(legacy_timestamp, (str, int, float)):
            raise ValueError("legacy_timestamp must be a string or finite number when supplied")
        if isinstance(legacy_timestamp, float) and not math.isfinite(legacy_timestamp):
            raise ValueError("legacy_timestamp must be a string or finite number when supplied")
    if not isinstance(governance_state, str) or not governance_state:
        raise ValueError("governance_state must be a non-empty string")


def _relationship_flexible_mapping(value: Mapping[str, Any] | None, *, field: str) -> dict[str, Any]:
    if isinstance(value, CandidateShapedValue):
        raise TypeError(f"candidate-shaped value cannot be written as relationship {field}")
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an ordinary mapping")
    copied = dict(value)
    for key, item in copied.items():
        if not isinstance(key, str):
            raise ValueError(f"{field} keys must be strings")
        if isinstance(item, CandidateShapedValue):
            raise TypeError("candidate-shaped value cannot be written into relationship payload")
        if key.casefold() in _RELATIONSHIP_STRUCTURAL_PAYLOAD_KEYS:
            raise ValueError(f"{field} cannot overwrite structural relationship semantics")
    return copied


def _validate_search_inputs(
    legacy_source_namespace_id: Any, embedding: Any, dimension: Any,
    representation_class: Any, generation: Any, derivation_contract_version: Any,
    encoding_id: Any, dtype: Any, top_k: Any, user_id: Any, min_score: Any,
    type_filter: Any, canon_only: Any, now_ts: Any,
) -> tuple[np.ndarray, int, float | None, frozenset[str], float]:
    if not isinstance(legacy_source_namespace_id, UUID):
        raise ValueError("legacy_source_namespace_id must be a UUID")
    if not isinstance(dimension, int) or isinstance(dimension, bool) or dimension < 1:
        raise ValueError("dimension must be a positive integer")
    if (
        representation_class,
        generation,
        derivation_contract_version,
        encoding_id,
        dtype,
    ) != (
        _COMPAT_EMBEDDING_REPRESENTATION_CLASS,
        _COMPAT_EMBEDDING_GENERATION,
        _COMPAT_EMBEDDING_DERIVATION_CONTRACT,
        _COMPAT_EMBEDDING_ENCODING,
        _COMPAT_EMBEDDING_DTYPE,
    ):
        raise ValueError("only the qualified COMPAT_EMBEDDING/1 RAW_VECTOR float32 lane is supported")
    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise ValueError("top_k must be an integer")
    limit = max(1, top_k)
    if user_id is not None and not isinstance(user_id, str):
        raise ValueError("user_id must be a string when supplied")
    if min_score is None:
        score_floor = None
    else:
        if isinstance(min_score, bool):
            raise ValueError("min_score must be a finite number")
        try:
            score_floor = float(min_score)
        except (TypeError, ValueError) as exc:
            raise ValueError("min_score must be a finite number") from exc
        if not math.isfinite(score_floor):
            raise ValueError("min_score must be a finite number")
    if type_filter is None:
        type_set = frozenset()
    else:
        if not isinstance(type_filter, (list, tuple)) or any(not isinstance(value, str) for value in type_filter):
            raise ValueError("type_filter must be a list or tuple of strings when supplied")
        type_set = frozenset(type_filter)
    if not isinstance(canon_only, bool):
        raise ValueError("canon_only must be a boolean")
    try:
        raw = np.asarray(embedding)
    except (TypeError, ValueError) as exc:
        raise ValueError("embedding must be a numeric vector") from exc
    if not np.issubdtype(raw.dtype, np.number) or np.issubdtype(raw.dtype, np.bool_):
        raise ValueError("embedding must be a numeric vector")
    try:
        query = np.asarray(raw, dtype=np.float64).reshape(-1)
    except (TypeError, ValueError) as exc:
        raise ValueError("embedding must be a numeric vector") from exc
    if query.size == 0:
        raise ValueError("embedding must be non-empty")
    if query.size != dimension:
        raise ValueError("query dimension does not match the explicit representation lane")
    if not np.all(np.isfinite(query)):
        raise ValueError("embedding must contain only finite values")
    norm = float(np.linalg.norm(query))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError("embedding must have a positive finite norm")
    if now_ts is None:
        effective_now = float(time.time())
    else:
        if isinstance(now_ts, bool):
            raise ValueError("now_ts must be a finite number when supplied")
        try:
            effective_now = float(now_ts)
        except (TypeError, ValueError) as exc:
            raise ValueError("now_ts must be a finite number when supplied") from exc
        if not math.isfinite(effective_now):
            raise ValueError("now_ts must be a finite number when supplied")
    return query / norm, limit, score_floor, type_set, effective_now


def _metadata_is_search_eligible(metadata: RepresentationMetadata) -> bool:
    return (
        metadata.source_kind == "OBJECT_REVISION"
        and metadata.readiness == "READY"
        and metadata.disposition == "USABLE"
        and metadata.integrity_expectation_id is not None
        and metadata.selected_measurement_id is not None
    )


def _decode_compat_embedding_payload(
    payload: bytes, expected_payload_byte_length: int | None, dtype: str, dimension: int,
) -> np.ndarray | None:
    if dtype != _COMPAT_EMBEDDING_DTYPE:
        raise SubstrateInvariantViolation("compatibility search does not support this representation dtype")
    expected_length = np.dtype(dtype).itemsize * dimension
    if (
        not isinstance(expected_payload_byte_length, int)
        or isinstance(expected_payload_byte_length, bool)
        or expected_payload_byte_length != expected_length
        or len(payload) != expected_length
    ):
        raise SubstrateInvariantViolation("compatibility embedding payload length does not match frozen metadata")
    vector = np.frombuffer(payload, dtype=np.dtype(dtype))
    if vector.size != dimension:
        raise SubstrateInvariantViolation("compatibility embedding payload dimension is inconsistent")
    vector64 = vector.astype(np.float64, copy=False)
    if not np.all(np.isfinite(vector64)):
        return None
    norm = float(np.linalg.norm(vector64))
    if not math.isfinite(norm) or norm <= 0.0:
        return None
    return vector64 / norm


def _compat_half_life_decay_factor(payload: Mapping[str, Any], now_ts: float) -> float:
    try:
        half_life = float(payload.get("half_life", 0) or 0)
    except (TypeError, ValueError):
        return 1.0
    if not math.isfinite(half_life) or half_life <= 0.0:
        return 1.0
    anchor = _compat_number(payload.get("last_reinforced_ts"), default=0.0)
    if anchor <= 0.0:
        anchor = _compat_number(payload.get("created_ts"), default=0.0)
    if anchor <= 0.0:
        return 1.0
    age_days = max(0.0, (now_ts - anchor) / 86400.0)
    if age_days <= 0.0:
        return 1.0
    return max(_DECAY_RANKING_FLOOR, float(2.0 ** (-age_days / half_life)))


def _compat_summary(payload: Mapping[str, Any]) -> str:
    value = payload.get("summary") or payload.get("text") or ""
    return str(value)


def _compat_number(value: Any, *, default: float = 0.0) -> float:
    try:
        result = float(value or 0.0)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _compat_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError, OverflowError):
        return 0


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
