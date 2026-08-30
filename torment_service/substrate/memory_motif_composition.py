"""Unwired A3C2 atomic native new-memory and motif composition.

Planning reads and previews the native catalog before mutation.  Commit accepts
only that immutable plan, verifies its exact catalog witness under the sole
semantic transaction, and publishes the memory, closed children, motif state,
and membership as one transition.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
import re
import sqlite3
from types import MappingProxyType
from typing import Any, Literal, Mapping
from uuid import UUID

import numpy as np

from torment_service.coherence_field import compute_coherence_field
from torment_service.motif_decision import (
    CURRENT_MOTIF_DECISION_POLICY,
    MotifDecision,
    MotifReadModel,
    _unit,
    decide_attach_or_create,
    realize_attach_next_state,
    realize_create_next_state,
)
from torment_service.motif_geometry import motif_radius_from_member_vectors
from torment_service.resonance import append_symbol, summarize_resonance
from torment_service.symbols import assign_symbol_state

from .canonical_intent import canonical_intent_text
from .errors import (
    SubstrateIdempotencyConflict,
    SubstrateInvariantViolation,
    SubstrateObjectNotFound,
    SubstrateRevisionConflict,
)
from .fabric_translation import (
    QualifiedCompatibilityLinkIntent,
    UnresolvedLegacyLinkReference,
    prepare_flexible_payload,
)
from .ids import generate_native_id, native_id_to_bytes
from .motif_runtime_reader import NativeMotifRuntimeReader, NativeRuntimeMotif
from .motifs import (
    DERIVED_MOTIF_OBJECT_KIND,
    MOTIF_ID_ALIAS_KIND,
    MOTIF_MEMBERSHIP_RELATIONSHIP_KIND,
    MotifState,
)
from .object_revision_governance import (
    NativeMemoryGovernanceFacts,
    _insert_published_governance_for_qualification,
)
from .objects import NativeObjectService, ObjectState, SubstrateTx, execute_semantic
from .provenance import NativeProvenanceRecord
from .relationships import Endpoint, NativeRelationshipService, RelationshipState
from .schema import require_current_schema


_MEMORY_OBJECT_KIND = "LEGACY_CORE_NODE"
_COMPOSITION_KIND = "NATIVE_MEMORY_MOTIF_COMPOSITION"
_MOTIF_ID_NUMBER = re.compile(r"(\d+)")
_AUTO_SPLIT_ENABLED = True
_AUTO_SPLIT_MIN_MEMBERS = 96


class StaleMotifCatalogError(SubstrateRevisionConflict):
    """A prepared decision no longer describes the current native catalog."""


class UnsupportedNativeSplitError(SubstrateInvariantViolation):
    """A conservative gate prevents an attach that may need native split."""


@dataclass(frozen=True)
class NativeMotifCatalogWitnessEntry:
    """One ordered current motif identity/revision observed by the plan."""

    runtime_motif_id: str
    motif_object_id: UUID
    motif_revision_id: UUID
    motif_revision_ordinal: int


@dataclass(frozen=True)
class NativeMemoryMotifCompositionRequest:
    """Already-prepared structural facts for one prospective ordinary memory."""

    legacy_source_namespace_id: UUID
    memory_identity_namespace_id: UUID
    semantic_scope_id: UUID
    summary: str
    memory_type: str
    memory_class: str
    strength: float
    confidence: float
    half_life_days: float
    user_id: str
    logical_step: int
    flexible_payload: Mapping[str, Any]
    lifecycle_state: str
    lifecycle_authoritative: bool
    governance_state: str
    provenance: NativeProvenanceRecord
    governance: NativeMemoryGovernanceFacts
    motif_alias_namespace_id: UUID
    motif_identity_namespace_id: UUID
    membership_identity_namespace_id: UUID
    domain_id: str
    agent_id: str
    idempotency_namespace_id: UUID
    idempotency_key: str
    incoming_embedding: tuple[float, ...] | list[float] | np.ndarray
    attach_threshold: float
    created_ts: int
    last_active_ts: int
    expected_dimension: int
    stability_delta: float = 0.0
    prior_symbol: str = ""
    prior_symbol_trace: tuple[str, ...] | list[str] = ()
    prior_motif_id: str = ""
    prior_tension: float = 0.0
    qualified_link_intents: tuple[QualifiedCompatibilityLinkIntent, ...] | list[QualifiedCompatibilityLinkIntent] = ()
    unresolved_link_references: tuple[UnresolvedLegacyLinkReference, ...] | list[UnresolvedLegacyLinkReference] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "legacy_source_namespace_id", "memory_identity_namespace_id",
            "semantic_scope_id", "motif_alias_namespace_id",
            "motif_identity_namespace_id", "membership_identity_namespace_id",
            "idempotency_namespace_id",
        ):
            if not isinstance(getattr(self, field_name), UUID):
                raise ValueError(f"{field_name} must be a UUID")
        for field_name in (
            "summary", "memory_type", "memory_class", "user_id", "lifecycle_state",
            "governance_state", "domain_id", "agent_id", "idempotency_key",
        ):
            if not isinstance(getattr(self, field_name), str) or not getattr(self, field_name):
                raise ValueError(f"{field_name} must be non-empty text")
        if type(self.lifecycle_authoritative) is not bool:
            raise ValueError("lifecycle_authoritative must be a boolean")
        if not isinstance(self.logical_step, int) or isinstance(self.logical_step, bool):
            raise ValueError("logical_step must be an integer")
        for field_name in ("created_ts", "last_active_ts"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if not isinstance(self.expected_dimension, int) or isinstance(self.expected_dimension, bool) or self.expected_dimension < 1:
            raise ValueError("expected_dimension must be a positive integer")
        _finite_number("strength", self.strength)
        _finite_number("confidence", self.confidence)
        _finite_number("half_life_days", self.half_life_days)
        _finite_number("attach_threshold", self.attach_threshold)
        _finite_number("stability_delta", self.stability_delta)
        _finite_number("prior_tension", self.prior_tension)
        for field_name in (
            "strength", "confidence", "half_life_days", "attach_threshold",
            "stability_delta", "prior_tension",
        ):
            object.__setattr__(self, field_name, float(getattr(self, field_name)))
        if not isinstance(self.provenance, NativeProvenanceRecord):
            raise ValueError("provenance must be NativeProvenanceRecord")
        _validate_provenance(self.provenance)
        if not isinstance(self.governance, NativeMemoryGovernanceFacts):
            raise ValueError("governance must be NativeMemoryGovernanceFacts")
        self.governance.as_storage_tuple()
        object.__setattr__(self, "flexible_payload", MappingProxyType(prepare_flexible_payload(self.flexible_payload)))
        object.__setattr__(self, "incoming_embedding", _canonical_embedding(self.incoming_embedding, self.expected_dimension))
        object.__setattr__(self, "prior_symbol_trace", tuple(str(value) for value in self.prior_symbol_trace))
        object.__setattr__(self, "qualified_link_intents", tuple(self.qualified_link_intents))
        object.__setattr__(self, "unresolved_link_references", tuple(self.unresolved_link_references))
        if any(not isinstance(value, QualifiedCompatibilityLinkIntent) for value in self.qualified_link_intents):
            raise ValueError("qualified_link_intents must contain typed A3C1 intents")
        if any(not isinstance(value, UnresolvedLegacyLinkReference) for value in self.unresolved_link_references):
            raise ValueError("unresolved_link_references must contain typed A3C1 evidence")


@dataclass(frozen=True)
class NativeMemoryMotifCompositionPreview:
    """Pure plan derived from one catalog read; it grants no write authority."""

    request: NativeMemoryMotifCompositionRequest
    catalog_witness: tuple[NativeMotifCatalogWitnessEntry, ...]
    catalog_order_kind: Literal["RESTART_LEXICOGRAPHIC", "PROCESS_ORDER"]
    decision: MotifDecision
    selected_motif_object_id: UUID | None
    selected_motif_identity_namespace_id: UUID | None
    prospective_motif_state: MotifState
    prospective_radius: float
    prospective_field_rows: tuple[Mapping[str, Any], ...]
    primary_field_row: Mapping[str, Any]
    enrichment_patch: Mapping[str, Any]
    predicted_runtime_motif_id: str | None
    incoming_embedding_sha256: str
    incoming_embedding_byte_length: int


@dataclass(frozen=True)
class NativeMemoryMotifCompositionResult:
    """Durable outputs for lost-response retry recovery."""

    memory_object_id: UUID
    memory_revision_id: UUID
    memory_revision_ordinal: int
    memory_eid: int
    provenance_id: UUID
    motif_object_id: UUID
    motif_revision_id: UUID
    motif_revision_ordinal: int
    runtime_motif_id: str
    membership_relationship_id: UUID
    membership_revision_id: UUID
    membership_revision_ordinal: int
    transition_id: UUID
    operation_id: UUID


class NativeMemoryMotifCompositionService:
    """v1.1-only native composition service; deliberately unwired."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        require_current_schema(connection)
        self._connection = connection
        self._objects = NativeObjectService(connection)
        self._relationships = NativeRelationshipService(connection)
        self._reader = NativeMotifRuntimeReader(connection)

    def prepare_plan(
        self, request: NativeMemoryMotifCompositionRequest,
    ) -> NativeMemoryMotifCompositionPreview:
        """Read, decide, and preview without creating any semantic state."""
        if not isinstance(request, NativeMemoryMotifCompositionRequest):
            raise ValueError("a NativeMemoryMotifCompositionRequest is required")
        _reject_deferred_links(request)
        catalog = self._reader.list_runtime_motifs(
            motif_alias_namespace_id=request.motif_alias_namespace_id,
            domain_id=request.domain_id,
            semantic_scope_id=request.semantic_scope_id,
        )
        return _prepare_preview(
            request, catalog, self._reader, catalog_order_kind="RESTART_LEXICOGRAPHIC"
        )

    def prepare_plan_from_ordered_catalog(
        self,
        request: NativeMemoryMotifCompositionRequest,
        ordered_catalog: tuple[NativeRuntimeMotif, ...],
    ) -> NativeMemoryMotifCompositionPreview:
        """Prepare against one caller-owned, freshly verified motif order.

        Standalone A3C2 retains :meth:`prepare_plan`'s restart-style sorted
        reader order.  A3D alone supplies a process-owned ordering snapshot;
        this method verifies that it is an exact permutation of the current
        catalog before preserving that order for the frozen decision layer.
        """
        if not isinstance(request, NativeMemoryMotifCompositionRequest):
            raise ValueError("a NativeMemoryMotifCompositionRequest is required")
        if not isinstance(ordered_catalog, tuple) or any(
            not isinstance(item, NativeRuntimeMotif) for item in ordered_catalog
        ):
            raise ValueError("ordered_catalog must be a tuple of NativeRuntimeMotif values")
        _reject_deferred_links(request)
        current = self._reader.list_runtime_motifs(
            motif_alias_namespace_id=request.motif_alias_namespace_id,
            domain_id=request.domain_id,
            semantic_scope_id=request.semantic_scope_id,
        )
        current_by_id = {item.motif_object_id: item for item in current}
        supplied_ids = tuple(item.motif_object_id for item in ordered_catalog)
        if len(set(supplied_ids)) != len(supplied_ids) or set(supplied_ids) != set(current_by_id):
            raise StaleMotifCatalogError("ordered motif catalog does not match current native motifs")
        if any(current_by_id[item.motif_object_id] != item for item in ordered_catalog):
            raise StaleMotifCatalogError("ordered motif catalog revision differs from current native motifs")
        return _prepare_preview(
            request, ordered_catalog, self._reader, catalog_order_kind="PROCESS_ORDER"
        )

    def commit(
        self,
        preview: NativeMemoryMotifCompositionPreview,
        *,
        _test_fail_after: str | None = None,
        _test_omit_effect: Literal["memory", "motif", "membership"] | None = None,
        _test_omit_output: Literal["memory", "motif", "membership"] | None = None,
    ) -> NativeMemoryMotifCompositionResult:
        """Verify a plan under one transaction and publish exactly its state."""
        if not isinstance(preview, NativeMemoryMotifCompositionPreview):
            raise ValueError("a NativeMemoryMotifCompositionPreview is required")
        request = preview.request
        _reject_deferred_links(request)
        # A lost response is allowed to prepare again against a newer catalog:
        # the existing operation is the durable decision.  Compare the caller
        # supplied semantic inputs, not the subsequently observed witness,
        # before returning that existing result.  Any actual input change still
        # follows the ordinary idempotency-conflict path.
        existing = self._connection.execute(
            "SELECT operation_id,canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), request.idempotency_key),
        ).fetchone()
        if existing is not None:
            stored = json.loads(existing[1])
            if stored.get("request_retry_contract") != _request_retry_contract(request):
                raise SubstrateIdempotencyConflict("idempotency intent differs")
            recovered = self._result_for_operation(existing[0])
            if recovered is None:
                raise SubstrateInvariantViolation("existing A3C2 operation has no complete durable result")
            return recovered
        intent = _composition_intent(preview)
        return execute_semantic(
            self._connection,
            request.idempotency_namespace_id,
            request.idempotency_key,
            _COMPOSITION_KIND,
            intent,
            self._result_for_operation,
            lambda tx: self._commit_preview(
                tx,
                preview,
                _test_fail_after=_test_fail_after,
                _test_omit_effect=_test_omit_effect,
                _test_omit_output=_test_omit_output,
            ),
        )

    def _commit_preview(
        self,
        tx: SubstrateTx,
        preview: NativeMemoryMotifCompositionPreview,
        *,
        _test_fail_after: str | None,
        _test_omit_effect: str | None,
        _test_omit_output: str | None,
    ) -> NativeMemoryMotifCompositionResult:
        request = preview.request
        self._assert_required_identities(request)
        self._verify_catalog_witness(preview)
        transition_id = _new()
        provenance_id = _new()
        tx.execute(
            """
            INSERT INTO provenance_records(
                provenance_id,origin_kind,source_channel,source_role,
                derivation_status,uncertainty_state,source_time_ns,
                capture_time_ns,memory_role,descriptive_notes
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (provenance_id, *_provenance_values(request.provenance)),
        )
        if _test_fail_after == "provenance":
            raise RuntimeError("forced composition failure after provenance")

        memory_object_id, memory_revision_id = _new(), _new()
        memory_eid = _allocate_eid(tx, request.legacy_source_namespace_id)
        memory_state = _memory_state(request, UUID(bytes=provenance_id), preview.enrichment_patch)
        self._insert_object_creation(
            tx, memory_object_id, memory_revision_id, transition_id, memory_state
        )
        tx.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,'EID',?,?)",
            (native_id_to_bytes(request.legacy_source_namespace_id), str(memory_eid), memory_object_id),
        )
        _insert_published_governance_for_qualification(
            tx,
            object_id=memory_object_id,
            object_revision_id=memory_revision_id,
            object_revision_ordinal=1,
            facts=request.governance,
        )
        if _test_fail_after == "governance":
            raise RuntimeError("forced composition failure after governance")
        if _test_fail_after == "memory":
            raise RuntimeError("forced composition failure after memory")

        motif_state = preview.prospective_motif_state
        if preview.decision.kind == "CREATE_NEW":
            runtime_motif_id = _next_runtime_motif_id(
                request.domain_id,
                tuple(item.runtime_motif_id for item in preview.catalog_witness),
            )
            if runtime_motif_id != preview.predicted_runtime_motif_id:
                raise StaleMotifCatalogError("runtime motif ID allocation no longer matches prepared plan")
            if motif_state.runtime_motif_id != runtime_motif_id:
                raise StaleMotifCatalogError("prepared motif state no longer matches allocated runtime motif ID")
            motif_object_id, motif_revision_id, motif_ordinal = _new(), _new(), 1
            self._insert_object_creation(
                tx,
                motif_object_id,
                motif_revision_id,
                transition_id,
                _motif_object_state(request.motif_identity_namespace_id, motif_state),
            )
            tx.execute(
                "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
                (
                    native_id_to_bytes(request.motif_alias_namespace_id),
                    MOTIF_ID_ALIAS_KIND,
                    runtime_motif_id,
                    motif_object_id,
                ),
            )
        else:
            if preview.selected_motif_object_id is None:
                raise SubstrateInvariantViolation("attach preview has no selected motif identity")
            if preview.selected_motif_identity_namespace_id is None:
                raise SubstrateInvariantViolation("attach preview has no motif identity namespace")
            selected = next(
                item for item in preview.catalog_witness
                if item.motif_object_id == preview.selected_motif_object_id
            )
            runtime_motif_id = selected.runtime_motif_id
            current = tx.execute(
                "SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",
                (native_id_to_bytes(selected.motif_object_id),),
            ).fetchone()
            if current != (native_id_to_bytes(selected.motif_revision_id), selected.motif_revision_ordinal):
                raise StaleMotifCatalogError("selected motif revision became stale")
            motif_object_id = native_id_to_bytes(selected.motif_object_id)
            motif_revision_id, motif_ordinal = _new(), selected.motif_revision_ordinal + 1
            self._objects._state(_motif_object_state(preview.selected_motif_identity_namespace_id, motif_state))
            self._objects._revision(
                tx,
                motif_revision_id,
                motif_object_id,
                motif_ordinal,
                "NATIVE_ORDINARY",
                native_id_to_bytes(selected.motif_revision_id),
                selected.motif_revision_ordinal,
                _motif_object_state(preview.selected_motif_identity_namespace_id, motif_state),
            )
            tx.execute(
                "UPDATE objects SET current_revision_id=?,current_revision_ordinal=? WHERE object_id=?",
                (motif_revision_id, motif_ordinal, motif_object_id),
            )
        if _test_fail_after == "motif":
            raise RuntimeError("forced composition failure after motif")

        membership_id, membership_revision_id = _new(), _new()
        membership_state = RelationshipState(
            request.membership_identity_namespace_id,
            request.semantic_scope_id,
            MOTIF_MEMBERSHIP_RELATIONSHIP_KIND,
            "EXISTS",
            "DERIVED",
            False,
            "DERIVED",
            "NOT_APPLICABLE",
            (
                Endpoint(0, "MOTIF", request.semantic_scope_id, UUID(bytes=motif_object_id), "IDENTITY"),
                Endpoint(1, "MEMBER", request.semantic_scope_id, UUID(bytes=memory_object_id), "IDENTITY"),
            ),
        )
        self._relationships._check(membership_state, tx)
        tx.execute(
            """
            INSERT INTO relationships(
                relationship_id,identity_namespace_id,relationship_kind,creating_transition_id,
                current_revision_id,current_revision_ordinal,created_at_ns
            ) VALUES (?,?,?,?,?,?,0)
            """,
            (
                membership_id,
                native_id_to_bytes(request.membership_identity_namespace_id),
                MOTIF_MEMBERSHIP_RELATIONSHIP_KIND,
                transition_id,
                membership_revision_id,
                1,
            ),
        )
        self._relationships._revision(
            tx, membership_id, membership_revision_id, 1, "NATIVE_CREATION", None, None, membership_state
        )
        if _test_fail_after == "membership":
            raise RuntimeError("forced composition failure after membership")

        self._publish_compound(
            tx,
            transition_id,
            memory_object_id,
            memory_revision_id,
            motif_object_id,
            motif_revision_id,
            motif_ordinal,
            membership_id,
            membership_revision_id,
            omit_effect=_test_omit_effect,
            omit_output=_test_omit_output,
        )
        self._validate_compound_publication(
            tx,
            transition_id,
            memory_object_id,
            memory_revision_id,
            motif_object_id,
            motif_revision_id,
            motif_ordinal,
            membership_id,
            membership_revision_id,
        )
        return NativeMemoryMotifCompositionResult(
            UUID(bytes=memory_object_id), UUID(bytes=memory_revision_id), 1, memory_eid,
            UUID(bytes=provenance_id), UUID(bytes=motif_object_id), UUID(bytes=motif_revision_id),
            motif_ordinal, runtime_motif_id, UUID(bytes=membership_id), UUID(bytes=membership_revision_id),
            1, UUID(bytes=transition_id), UUID(bytes=tx.operation_id),
        )

    def _insert_object_creation(
        self, tx: SubstrateTx, object_id: bytes, revision_id: bytes, transition_id: bytes, state: ObjectState,
    ) -> None:
        self._objects._state(state)
        tx.execute(
            """
            INSERT INTO objects(
                object_id,identity_namespace_id,object_kind,creating_transition_id,
                current_revision_id,current_revision_ordinal,created_at_ns
            ) VALUES (?,?,?,?,?,?,0)
            """,
            (object_id, native_id_to_bytes(state.identity_namespace_id), state.object_kind, transition_id, revision_id, 1),
        )
        self._objects._revision(tx, revision_id, object_id, 1, "NATIVE_CREATION", None, None, state)

    def _publish_compound(
        self, tx: SubstrateTx, transition_id: bytes, memory_object_id: bytes, memory_revision_id: bytes,
        motif_object_id: bytes, motif_revision_id: bytes, motif_ordinal: int, membership_id: bytes,
        membership_revision_id: bytes, *, omit_effect: str | None, omit_output: str | None,
    ) -> None:
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (transition_id, tx.operation_id, _COMPOSITION_KIND, "NATIVE"),
        )
        if omit_effect != "memory":
            tx.execute("INSERT INTO object_revision_effects VALUES (?,?,?,?)", (transition_id, memory_object_id, memory_revision_id, 1))
        if omit_effect != "motif":
            tx.execute("INSERT INTO object_revision_effects VALUES (?,?,?,?)", (transition_id, motif_object_id, motif_revision_id, motif_ordinal))
        if omit_effect != "membership":
            tx.execute("INSERT INTO relationship_revision_effects VALUES (?,?,?,?)", (transition_id, membership_id, membership_revision_id, 1))
        if omit_output != "memory":
            tx.execute(
                "INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,object_id,object_revision_id,object_revision_ordinal) VALUES (?,?,?,?,?,?,?)",
                (tx.operation_id, 0, "MEMORY", "OBJECT", memory_object_id, memory_revision_id, 1),
            )
        if omit_output != "motif":
            tx.execute(
                "INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,object_id,object_revision_id,object_revision_ordinal) VALUES (?,?,?,?,?,?,?)",
                (tx.operation_id, 1, "MOTIF", "OBJECT", motif_object_id, motif_revision_id, motif_ordinal),
            )
        if omit_output != "membership":
            tx.execute(
                "INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,relationship_id,relationship_revision_id,relationship_revision_ordinal) VALUES (?,?,?,?,?,?,?)",
                (tx.operation_id, 2, "MOTIF_MEMBERSHIP", "RELATIONSHIP", membership_id, membership_revision_id, 1),
            )
        tx.transitions.append(transition_id)
        tx.published.extend(((memory_object_id, memory_revision_id, 1), (motif_object_id, motif_revision_id, motif_ordinal)))
        tx.relationship_published.append((membership_id, membership_revision_id, 1))

    def _validate_compound_publication(
        self, tx: SubstrateTx, transition_id: bytes, memory_object_id: bytes, memory_revision_id: bytes,
        motif_object_id: bytes, motif_revision_id: bytes, motif_ordinal: int, membership_id: bytes,
        membership_revision_id: bytes,
    ) -> None:
        required_effects = (
            ("OBJECT", memory_object_id, memory_revision_id, 1),
            ("OBJECT", motif_object_id, motif_revision_id, motif_ordinal),
            ("RELATIONSHIP", membership_id, membership_revision_id, 1),
        )
        for kind, object_id, revision_id, ordinal in required_effects:
            if kind == "OBJECT":
                found = tx.execute("SELECT 1 FROM object_revision_effects WHERE transition_id=? AND object_id=? AND object_revision_id=? AND object_revision_ordinal=?", (transition_id, object_id, revision_id, ordinal)).fetchone()
            else:
                found = tx.execute("SELECT 1 FROM relationship_revision_effects WHERE transition_id=? AND relationship_id=? AND relationship_revision_id=? AND relationship_revision_ordinal=?", (transition_id, object_id, revision_id, ordinal)).fetchone()
            if found is None:
                raise SubstrateInvariantViolation("A3C2 compound transition omits a required typed effect")
        outputs = tx.execute("SELECT output_ordinal,output_role,output_kind FROM operation_outputs WHERE operation_id=? ORDER BY output_ordinal", (tx.operation_id,)).fetchall()
        if outputs != [(0, "MEMORY", "OBJECT"), (1, "MOTIF", "OBJECT"), (2, "MOTIF_MEMBERSHIP", "RELATIONSHIP")]:
            raise SubstrateInvariantViolation("A3C2 durable outputs do not match the compound publication")

    def _verify_catalog_witness(self, preview: NativeMemoryMotifCompositionPreview) -> None:
        request = preview.request
        current = self._reader.list_runtime_motifs(
            motif_alias_namespace_id=request.motif_alias_namespace_id,
            domain_id=request.domain_id,
            semantic_scope_id=request.semantic_scope_id,
        )
        actual = tuple(_witness_entry(item) for item in current)
        if preview.catalog_order_kind == "RESTART_LEXICOGRAPHIC":
            if actual != preview.catalog_witness:
                raise StaleMotifCatalogError("native motif catalog differs from the prepared witness")
            return
        if preview.catalog_order_kind != "PROCESS_ORDER":
            raise SubstrateInvariantViolation("A3C2 preview has an unknown catalog ordering kind")
        # The standalone reader remains lexicographic.  A3D may instead carry
        # its own frozen process order (restart baseline plus local creates
        # appended).  Durable freshness is the exact set of motif identities
        # and revisions, not the read-order used for tie breaking.
        actual_by_object = {item.motif_object_id: item for item in actual}
        prepared_by_object = {item.motif_object_id: item for item in preview.catalog_witness}
        if (
            len(actual_by_object) != len(actual)
            or len(prepared_by_object) != len(preview.catalog_witness)
            or actual_by_object != prepared_by_object
        ):
            raise StaleMotifCatalogError("native motif catalog differs from the prepared witness")

    def _assert_required_identities(self, request: NativeMemoryMotifCompositionRequest) -> None:
        checks = (
            ("legacy source namespace", "SELECT 1 FROM legacy_source_namespaces WHERE legacy_source_namespace_id=?", request.legacy_source_namespace_id),
            ("memory identity namespace", "SELECT 1 FROM identity_namespaces WHERE identity_namespace_id=?", request.memory_identity_namespace_id),
            ("semantic scope", "SELECT 1 FROM semantic_scopes WHERE semantic_scope_id=?", request.semantic_scope_id),
            ("motif alias namespace", "SELECT 1 FROM legacy_source_namespaces WHERE legacy_source_namespace_id=?", request.motif_alias_namespace_id),
            ("motif identity namespace", "SELECT 1 FROM identity_namespaces WHERE identity_namespace_id=?", request.motif_identity_namespace_id),
            ("membership identity namespace", "SELECT 1 FROM identity_namespaces WHERE identity_namespace_id=?", request.membership_identity_namespace_id),
            ("idempotency namespace", "SELECT 1 FROM idempotency_namespaces WHERE idempotency_namespace_id=?", request.idempotency_namespace_id),
        )
        for name, statement, value in checks:
            if self._connection.execute(statement, (native_id_to_bytes(value),)).fetchone() is None:
                raise SubstrateObjectNotFound(f"required {name} was not found")

    def _result_for_operation(self, operation_id: bytes) -> NativeMemoryMotifCompositionResult | None:
        intent_row = self._connection.execute(
            "SELECT canonical_intent_json FROM operations WHERE operation_id=?",
            (operation_id,),
        ).fetchone()
        if intent_row is None:
            return None
        try:
            intent = json.loads(intent_row[0])
            memory_namespace = UUID(intent["memory"]["legacy_source_namespace_id"])
            motif_namespace = UUID(intent["motif_configuration"]["alias_namespace_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SubstrateInvariantViolation("A3C2 operation intent has no reconstructable alias scope") from exc
        rows = self._connection.execute(
            """
            SELECT t.transition_id,t.operation_id,o.output_ordinal,o.output_role,o.output_kind,
                   o.object_id,o.object_revision_id,o.object_revision_ordinal,
                   o.relationship_id,o.relationship_revision_id,o.relationship_revision_ordinal
              FROM semantic_transitions t JOIN operation_outputs o ON o.operation_id=t.operation_id
             WHERE t.operation_id=? AND t.transition_kind=?
             ORDER BY o.output_ordinal
            """,
            (operation_id, _COMPOSITION_KIND),
        ).fetchall()
        if len(rows) != 3 or [(row[2], row[3], row[4]) for row in rows] != [
            (0, "MEMORY", "OBJECT"), (1, "MOTIF", "OBJECT"), (2, "MOTIF_MEMBERSHIP", "RELATIONSHIP"),
        ]:
            return None
        memory, motif, membership = rows
        provenance = self._connection.execute(
            "SELECT provenance_id FROM object_revisions WHERE object_id=? AND object_revision_id=? AND revision_ordinal=?",
            (memory[5], memory[6], memory[7]),
        ).fetchone()
        alias = self._connection.execute(
            "SELECT alias_value FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND object_id=? AND alias_kind='EID'",
            (native_id_to_bytes(memory_namespace), memory[5]),
        ).fetchall()
        motif_alias = self._connection.execute(
            "SELECT alias_value FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND object_id=? AND alias_kind=?",
            (native_id_to_bytes(motif_namespace), motif[5], MOTIF_ID_ALIAS_KIND),
        ).fetchall()
        if provenance is None or provenance[0] is None or len(alias) != 1 or len(motif_alias) != 1:
            raise SubstrateInvariantViolation("A3C2 result reconstruction is incomplete")
        memory_eid = _canonical_eid(alias[0][0])
        return NativeMemoryMotifCompositionResult(
            UUID(bytes=memory[5]), UUID(bytes=memory[6]), memory[7], memory_eid,
            UUID(bytes=provenance[0]), UUID(bytes=motif[5]), UUID(bytes=motif[6]), motif[7],
            motif_alias[0][0], UUID(bytes=membership[8]), UUID(bytes=membership[9]), membership[10],
            UUID(bytes=memory[0]), UUID(bytes=memory[1]),
        )


def _prepare_preview(
    request: NativeMemoryMotifCompositionRequest,
    catalog: tuple[NativeRuntimeMotif, ...],
    reader: NativeMotifRuntimeReader,
    *,
    catalog_order_kind: Literal["RESTART_LEXICOGRAPHIC", "PROCESS_ORDER"],
) -> NativeMemoryMotifCompositionPreview:
    witness = tuple(_witness_entry(item) for item in catalog)
    decision = decide_attach_or_create(
        tuple(item.read_model for item in catalog),
        np.asarray(request.incoming_embedding, dtype=np.float32),
        float(request.attach_threshold),
        CURRENT_MOTIF_DECISION_POLICY,
    )
    selected = _selected_native_motif(decision, catalog)
    if decision.kind == "ATTACH_EXISTING":
        if selected is None:
            raise SubstrateInvariantViolation("native decision selected no current motif")
        prospective_count = selected.read_model.member_count + 1
        if _AUTO_SPLIT_ENABLED and prospective_count >= _AUTO_SPLIT_MIN_MEMBERS:
            raise UnsupportedNativeSplitError("UNSUPPORTED_NATIVE_SPLIT: attach reaches the legacy split eligibility gate")
        aggregate = realize_attach_next_state(
            decision, agent_id=request.agent_id, last_active_ts=request.last_active_ts
        )
        source = reader._get_current_motif(selected.motif_object_id)
        if source.identity_namespace_id != request.motif_identity_namespace_id:
            raise SubstrateInvariantViolation("selected motif identity namespace differs from the prepared configuration")
        motif_state = _motif_state_from_aggregate(
            aggregate,
            request.semantic_scope_id,
            derivation_metadata=source.state.derivation_metadata,
            extra_payload=source.state.extra_payload,
        )
        prospective_id = motif_state.runtime_motif_id
        selected_id = selected.motif_object_id
        selected_identity_namespace_id = source.identity_namespace_id
    else:
        prospective_id = _next_runtime_motif_id(request.domain_id, tuple(item.runtime_motif_id for item in witness))
        aggregate = realize_create_next_state(
            decision,
            runtime_motif_id=prospective_id,
            domain_id=request.domain_id,
            summary=request.summary,
            agent_id=request.agent_id,
            created_ts=request.created_ts,
            last_active_ts=request.last_active_ts,
        )
        motif_state = _motif_state_from_aggregate(aggregate, request.semantic_scope_id)
        selected_id = None
        selected_identity_namespace_id = None
    prospective_radius = _prospective_radius(reader, selected, motif_state, decision, request.expected_dimension)
    prospective_rows = _prospective_rows(reader, request, catalog, selected, motif_state, prospective_radius)
    field_rows = compute_coherence_field(prospective_rows)
    primary = next((row for row in field_rows if row["motif_id"] == motif_state.runtime_motif_id), {})
    enrichment = _symbol_resonance_enrichment(request, primary, is_new=decision.kind == "CREATE_NEW")
    raw = np.asarray(request.incoming_embedding, dtype=np.float32)
    return NativeMemoryMotifCompositionPreview(
        request=request,
        catalog_witness=witness,
        catalog_order_kind=catalog_order_kind,
        decision=decision,
        selected_motif_object_id=selected_id,
        selected_motif_identity_namespace_id=selected_identity_namespace_id,
        prospective_motif_state=motif_state,
        prospective_radius=prospective_radius,
        prospective_field_rows=tuple(MappingProxyType(dict(row)) for row in field_rows),
        primary_field_row=MappingProxyType(dict(primary)),
        enrichment_patch=MappingProxyType(enrichment),
        predicted_runtime_motif_id=prospective_id if decision.kind == "CREATE_NEW" else None,
        incoming_embedding_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),
        incoming_embedding_byte_length=len(raw.tobytes()),
    )


def _prospective_radius(
    reader: NativeMotifRuntimeReader,
    selected: NativeRuntimeMotif | None,
    state: MotifState,
    decision: MotifDecision,
    expected_dimension: int,
) -> float:
    # ``decide_attach_or_create()`` supplies its candidate through the frozen
    # legacy-compatible ``_unit(raw)`` path.  Existing native vectors need the
    # same transformation, but applying it a second time here would drift for
    # very small nonzero candidates.
    candidate = np.asarray(decision.candidate_embedding, dtype=np.float32)
    if selected is None:
        return motif_radius_from_member_vectors(state.centroid, (candidate,))
    member_vectors: list[np.ndarray] = []
    for member in reader.list_ordered_current_motif_members(selected.motif_object_id):
        raw = reader.read_current_compat_embedding(member.member_object_id, expected_dimension=expected_dimension)
        if raw is not None:
            member_vectors.append(_unit(raw))
    member_vectors.append(candidate)
    return motif_radius_from_member_vectors(state.centroid, member_vectors)


def _prospective_rows(
    reader: NativeMotifRuntimeReader,
    request: NativeMemoryMotifCompositionRequest,
    catalog: tuple[NativeRuntimeMotif, ...],
    selected: NativeRuntimeMotif | None,
    state: MotifState,
    radius: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for motif in catalog:
        if selected is not None and motif.motif_object_id == selected.motif_object_id:
            rows.append(_field_row(state, motif.read_model.member_count + 1, radius))
        else:
            rows.append(_field_row(motif.read_model, motif.read_model.member_count, reader.motif_radius(motif.motif_object_id, expected_dimension=request.expected_dimension)))
    if selected is None:
        rows.append(_field_row(state, 1, radius))
    return rows


def _field_row(state: MotifState | MotifReadModel, member_count: int, radius: float) -> dict[str, Any]:
    return {
        "motif_id": state.runtime_motif_id,
        "label": state.label,
        "centroid": list(state.centroid),
        "strength": state.strength,
        "stability_score": state.stability_score,
        "members": member_count,
        "radius": radius,
    }


def _symbol_resonance_enrichment(
    request: NativeMemoryMotifCompositionRequest, field: Mapping[str, Any], *, is_new: bool,
) -> dict[str, Any]:
    tension = float(field.get("tension", 0.0) or 0.0)
    symbol = assign_symbol_state(
        motif_role=str(field.get("role", "") or ""),
        phi=float(field.get("phi", 0.0) or 0.0),
        tension=tension,
        kappa=float(field.get("kappa", 0.0) or 0.0),
        coherence_delta=float(request.stability_delta),
        tension_delta=tension - float(request.prior_tension),
        previous_symbol=request.prior_symbol,
        repeated_same_motif=bool(request.prior_motif_id and request.prior_motif_id == str(field.get("motif_id", ""))),
        is_new_motif=is_new,
        symbol_trace=request.prior_symbol_trace,
    )
    trace = append_symbol(request.prior_symbol_trace, str(symbol.get("state_symbol", "")))
    resonance = summarize_resonance(trace, prev_trace=request.prior_symbol_trace)
    return {
        "state_symbol": symbol.get("state_symbol"),
        "symbol_confidence": symbol.get("symbol_confidence"),
        "symbol_reason": symbol.get("symbol_reason"),
        "symbol_trace": list(resonance.get("symbol_trace", [])),
        "resonance_score": float(resonance.get("resonance_score", 0.0)),
        "transition_entropy": float(resonance.get("transition_entropy", 0.0)),
        "loop_type": str(resonance.get("loop_type", "mixed")),
        "phase_shift": bool(resonance.get("phase_shift", False)),
        "dominant_transition": resonance.get("dominant_transition"),
        "cycles": resonance.get("cycles", []),
    }


def _memory_state(
    request: NativeMemoryMotifCompositionRequest, provenance_id: UUID, enrichment: Mapping[str, Any],
) -> ObjectState:
    payload = {
        "summary": request.summary,
        "type": request.memory_type,
        "memory_class": request.memory_class,
        "strength": float(request.strength),
        "confidence": float(request.confidence),
        "half_life": float(request.half_life_days),
        "user_id": request.user_id,
        "created_at": request.logical_step,
        "last_reinforced": request.logical_step,
    }
    payload.update(dict(request.flexible_payload))
    payload.update(dict(enrichment))
    return ObjectState(
        request.memory_identity_namespace_id, request.semantic_scope_id, _MEMORY_OBJECT_KIND,
        "EXISTS", request.lifecycle_state, request.lifecycle_authoritative,
        request.governance_state, "NOT_APPLICABLE", payload, "JSON", provenance_id,
    )


def _motif_object_state(identity_namespace_id: UUID, state: MotifState) -> ObjectState:
    return ObjectState(
        identity_namespace_id, state.semantic_scope_id, DERIVED_MOTIF_OBJECT_KIND,
        "EXISTS", "DERIVED", False, "DERIVED", "NOT_APPLICABLE", state.payload(), "JSON",
    )


def _motif_state_from_aggregate(
    aggregate: Any,
    scope_id: UUID,
    *,
    derivation_metadata: Mapping[str, Any] | None = None,
    extra_payload: Mapping[str, Any] | None = None,
) -> MotifState:
    return MotifState(
        scope_id, aggregate.runtime_motif_id, aggregate.domain_id, aggregate.label,
        aggregate.centroid, aggregate.strength, aggregate.stability_score,
        aggregate.contributing_agents, aggregate.created_ts, aggregate.last_active_ts,
        derivation_metadata, extra_payload,
    )


def _selected_native_motif(decision: MotifDecision, catalog: tuple[NativeRuntimeMotif, ...]) -> NativeRuntimeMotif | None:
    if decision.selected is None:
        return None
    selected = [item for item in catalog if item.read_model is decision.selected]
    if len(selected) != 1:
        raise SubstrateInvariantViolation("decision-selected motif is not uniquely represented by the native catalog")
    return selected[0]


def _witness_entry(motif: NativeRuntimeMotif) -> NativeMotifCatalogWitnessEntry:
    return NativeMotifCatalogWitnessEntry(
        motif.read_model.runtime_motif_id, motif.motif_object_id, motif.motif_revision_id, motif.motif_revision_ordinal,
    )


def _next_runtime_motif_id(domain_id: str, runtime_ids: tuple[str, ...]) -> str:
    max_seen = max((_extract_runtime_motif_id_number(value) for value in runtime_ids), default=0)
    return f"motif_{domain_id}_{max_seen + 1:04d}"


def _extract_runtime_motif_id_number(motif_id: str) -> int:
    numbers = _MOTIF_ID_NUMBER.findall(motif_id)
    return max((int(value) for value in numbers), default=0)


def _canonical_embedding(value: Any, dimension: int) -> tuple[float, ...]:
    try:
        vector = np.asarray(value, dtype=np.float32).reshape(-1)
    except (TypeError, ValueError) as exc:
        raise ValueError("incoming_embedding must be a numeric vector") from exc
    if vector.size != dimension or not np.all(np.isfinite(vector)):
        raise ValueError("incoming_embedding must be finite float32 data with expected_dimension entries")
    return tuple(float(item) for item in vector)


def _composition_intent(preview: NativeMemoryMotifCompositionPreview) -> str:
    request = preview.request
    return canonical_intent_text(
        {
            "kind": _COMPOSITION_KIND,
            "request_retry_contract": _request_retry_contract(request),
            "memory": {
                "legacy_source_namespace_id": str(request.legacy_source_namespace_id),
                "identity_namespace_id": str(request.memory_identity_namespace_id),
                "semantic_scope_id": str(request.semantic_scope_id),
                "summary": request.summary, "memory_type": request.memory_type,
                "memory_class": request.memory_class, "strength": request.strength,
                "confidence": request.confidence, "half_life_days": request.half_life_days,
                "user_id": request.user_id, "logical_step": request.logical_step,
                "flexible_payload": dict(request.flexible_payload), "lifecycle_state": request.lifecycle_state,
                "lifecycle_authoritative": request.lifecycle_authoritative, "governance_state": request.governance_state,
            },
            "provenance": _provenance_intent(request.provenance),
            "governance": request.governance.as_storage_tuple(),
            "motif_configuration": {
                "alias_namespace_id": str(request.motif_alias_namespace_id),
                "identity_namespace_id": str(request.motif_identity_namespace_id),
                "membership_identity_namespace_id": str(request.membership_identity_namespace_id),
                "domain_id": request.domain_id, "agent_id": request.agent_id,
                "attach_threshold": request.attach_threshold, "created_ts": request.created_ts,
                "last_active_ts": request.last_active_ts,
            },
            "incoming_embedding": {
                "dtype": "float32", "dimension": request.expected_dimension,
                "byte_length": preview.incoming_embedding_byte_length,
                "sha256": preview.incoming_embedding_sha256,
            },
            "catalog_witness": [_witness_intent(item) for item in preview.catalog_witness],
            "catalog_order_kind": preview.catalog_order_kind,
            "decision": _decision_intent(preview.decision),
            "selected_motif_object_id": str(preview.selected_motif_object_id) if preview.selected_motif_object_id else None,
            "selected_motif_identity_namespace_id": str(preview.selected_motif_identity_namespace_id) if preview.selected_motif_identity_namespace_id else None,
            "prospective_motif_state": preview.prospective_motif_state.intent(),
            "prospective_radius": preview.prospective_radius,
            "primary_field_row": dict(preview.primary_field_row),
            "enrichment_patch": dict(preview.enrichment_patch),
            "predicted_runtime_motif_id": preview.predicted_runtime_motif_id,
        }
    )


def _request_retry_contract(request: NativeMemoryMotifCompositionRequest) -> dict[str, Any]:
    """All caller-provided semantic inputs, excluding read-time catalog state."""
    raw = np.asarray(request.incoming_embedding, dtype=np.float32)
    return {
        "memory": {
            "legacy_source_namespace_id": str(request.legacy_source_namespace_id),
            "identity_namespace_id": str(request.memory_identity_namespace_id),
            "semantic_scope_id": str(request.semantic_scope_id),
            "summary": request.summary, "memory_type": request.memory_type,
            "memory_class": request.memory_class, "strength": request.strength,
            "confidence": request.confidence, "half_life_days": request.half_life_days,
            "user_id": request.user_id, "logical_step": request.logical_step,
            "flexible_payload": dict(request.flexible_payload),
            "lifecycle_state": request.lifecycle_state,
            "lifecycle_authoritative": request.lifecycle_authoritative,
            "governance_state": request.governance_state,
        },
        "provenance": _provenance_intent(request.provenance),
        "governance": list(request.governance.as_storage_tuple()),
        "motif_configuration": {
            "alias_namespace_id": str(request.motif_alias_namespace_id),
            "identity_namespace_id": str(request.motif_identity_namespace_id),
            "membership_identity_namespace_id": str(request.membership_identity_namespace_id),
            "domain_id": request.domain_id, "agent_id": request.agent_id,
            "attach_threshold": request.attach_threshold,
            "created_ts": request.created_ts, "last_active_ts": request.last_active_ts,
        },
        "incoming_embedding": {
            "dtype": "float32", "dimension": request.expected_dimension,
            "byte_length": len(raw.tobytes()), "sha256": hashlib.sha256(raw.tobytes()).hexdigest(),
        },
        "symbol_context": {
            "stability_delta": request.stability_delta, "prior_symbol": request.prior_symbol,
            "prior_symbol_trace": list(request.prior_symbol_trace),
            "prior_motif_id": request.prior_motif_id, "prior_tension": request.prior_tension,
        },
        # A3C2 rejects both link collections, but including their cardinality
        # makes that fixed boundary explicit in the recovery comparison.
        "deferred_link_counts": {
            "qualified": len(request.qualified_link_intents),
            "unresolved": len(request.unresolved_link_references),
        },
    }


def _provenance_intent(value: NativeProvenanceRecord) -> dict[str, Any]:
    return {
        "origin_kind": value.origin_kind, "source_channel": value.source_channel,
        "source_role": value.source_role, "derivation_status": value.derivation_status,
        "uncertainty_state": value.uncertainty_state, "source_time_ns": value.source_time_ns,
        "capture_time_ns": value.capture_time_ns, "memory_role": value.memory_role,
        "descriptive_notes": value.descriptive_notes,
    }


def _decision_intent(value: MotifDecision) -> dict[str, Any]:
    return {
        "kind": value.kind, "candidate_embedding": list(value.candidate_embedding),
        "selected_runtime_motif_id": value.selected.runtime_motif_id if value.selected else None,
        "raw_similarity": value.raw_similarity, "attach_score": value.attach_score,
        "effective_threshold": value.effective_threshold, "pre_mutation_density": value.pre_mutation_density,
    }


def _witness_intent(value: NativeMotifCatalogWitnessEntry) -> dict[str, Any]:
    return {
        "runtime_motif_id": value.runtime_motif_id, "motif_object_id": str(value.motif_object_id),
        "motif_revision_id": str(value.motif_revision_id), "motif_revision_ordinal": value.motif_revision_ordinal,
    }


def _reject_deferred_links(request: NativeMemoryMotifCompositionRequest) -> None:
    # Both collections are independently inspected: unresolved evidence has no
    # summary-based shortcut that could hide simultaneously qualified intents.
    if request.qualified_link_intents or request.unresolved_link_references:
        raise ValueError("A3C2 defers qualified and unresolved link publication; no safe carrier is frozen")


def _validate_provenance(value: NativeProvenanceRecord) -> None:
    for field_name in ("origin_kind", "derivation_status", "uncertainty_state"):
        if not isinstance(getattr(value, field_name), str) or not getattr(value, field_name):
            raise ValueError(f"provenance {field_name} must be non-empty text")
    for item in (value.source_channel, value.source_role, value.memory_role, value.descriptive_notes):
        if item is not None and not isinstance(item, str):
            raise ValueError("optional provenance text must be text")
    for item in (value.source_time_ns, value.capture_time_ns):
        if item is not None and (not isinstance(item, int) or isinstance(item, bool)):
            raise ValueError("optional provenance timestamps must be integers")


def _provenance_values(value: NativeProvenanceRecord) -> tuple[object, ...]:
    return (
        value.origin_kind, value.source_channel, value.source_role, value.derivation_status,
        value.uncertainty_state, value.source_time_ns, value.capture_time_ns,
        value.memory_role, value.descriptive_notes,
    )


def _allocate_eid(tx: SubstrateTx, namespace: UUID) -> int:
    values = tx.execute(
        "SELECT alias_value FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID'",
        (native_id_to_bytes(namespace),),
    ).fetchall()
    return max((_canonical_eid(row[0]) for row in values), default=-1) + 1


def _canonical_eid(value: Any) -> int:
    if not isinstance(value, str):
        raise SubstrateInvariantViolation("stored EID alias is not text")
    try:
        eid = int(value)
    except ValueError as exc:
        raise SubstrateInvariantViolation("stored EID alias is not an integer") from exc
    if eid < 0 or str(eid) != value:
        raise SubstrateInvariantViolation("stored EID alias is not canonical")
    return eid


def _finite_number(field_name: str, value: Any) -> None:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a finite number")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a finite number") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{field_name} must be a finite number")


def _new() -> bytes:
    return native_id_to_bytes(generate_native_id())


__all__ = [
    "NativeMemoryMotifCompositionPreview",
    "NativeMemoryMotifCompositionRequest",
    "NativeMemoryMotifCompositionResult",
    "NativeMemoryMotifCompositionService",
    "NativeMotifCatalogWitnessEntry",
    "StaleMotifCatalogError",
    "UnsupportedNativeSplitError",
]
