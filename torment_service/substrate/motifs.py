"""Phase 7G5A1 native motif persistence primitives.

This module intentionally persists already-decided motif changes.  It neither
selects motifs nor invokes the legacy :mod:`torment_service.motifs` algorithm.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import sqlite3
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from .canonical_intent import canonical_intent_text
from .errors import SubstrateInvariantViolation, SubstrateObjectNotFound, SubstrateRevisionConflict
from .ids import generate_native_id, native_id_to_bytes
from .objects import NativeObjectService, ObjectState, SubstrateTx, execute_semantic
from .relationships import Endpoint, NativeRelationshipService, RelationshipState
from .schema import open_schema


DERIVED_MOTIF_OBJECT_KIND = "DERIVED_MOTIF"
MOTIF_MEMBERSHIP_RELATIONSHIP_KIND = "MOTIF_MEMBERSHIP"
MOTIF_ID_ALIAS_KIND = "MOTIF_ID"
_MEMORY_OBJECT_KIND = "LEGACY_CORE_NODE"

_STATE_PAYLOAD_KEYS = frozenset(
    {
        "motif_id",
        "domain_id",
        "label",
        "centroid",
        "strength",
        "stability_score",
        "contributing_agents",
        "created_ts",
        "last_active_ts",
        "derivation_metadata",
        "members",
        "member_count",
    }
)
_EXTRA_FORBIDDEN_KEYS = frozenset(
    {
        "semantic_scope_id",
        "identity_namespace_id",
        "object_id",
        "object_kind",
        "revision_id",
        "object_revision_id",
        "predecessor_revision_id",
        "authority_category",
        "active_authorization",
        "operation_id",
        "transition_id",
        "representation_id",
        "readiness",
        "integrity_expectation",
        "integrity_measurement",
        "reconciliation",
    }
)


@dataclass(frozen=True)
class MotifState:
    """The bounded, durable state of one already-selected runtime motif.

    ``members`` is deliberately absent: first-class membership relationships
    are the current member-set truth.  ``centroid`` is ordinary JSON state and
    never a representation publication request.
    """

    semantic_scope_id: UUID
    runtime_motif_id: str
    domain_id: str
    label: str
    centroid: tuple[float, ...]
    strength: float
    stability_score: float
    contributing_agents: tuple[str, ...]
    created_ts: int
    last_active_ts: int
    derivation_metadata: Mapping[str, Any] | None = None
    extra_payload: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.centroid, (tuple, list)):
            raise ValueError("centroid must be a tuple or list")
        if not isinstance(self.contributing_agents, (tuple, list)):
            raise ValueError("contributing_agents must be a tuple or list")
        object.__setattr__(self, "centroid", tuple(self.centroid))
        object.__setattr__(self, "contributing_agents", tuple(self.contributing_agents))
        object.__setattr__(self, "derivation_metadata", _freeze_mapping(self.derivation_metadata))
        object.__setattr__(self, "extra_payload", _freeze_mapping(self.extra_payload))

    def payload(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "motif_id": self.runtime_motif_id,
            "domain_id": self.domain_id,
            "label": self.label,
            "centroid": list(self.centroid),
            "strength": self.strength,
            "stability_score": self.stability_score,
            "contributing_agents": list(self.contributing_agents),
            "created_ts": self.created_ts,
            "last_active_ts": self.last_active_ts,
        }
        if self.derivation_metadata is not None:
            value["derivation_metadata"] = _thaw(self.derivation_metadata)
        value.update(_thaw(self.extra_payload or {}))
        return value

    def intent(self) -> dict[str, Any]:
        return {
            "semantic_scope_id": str(self.semantic_scope_id),
            "runtime_motif_id": self.runtime_motif_id,
            "domain_id": self.domain_id,
            "label": self.label,
            "centroid": list(self.centroid),
            "strength": self.strength,
            "stability_score": self.stability_score,
            "contributing_agents": list(self.contributing_agents),
            "created_ts": self.created_ts,
            "last_active_ts": self.last_active_ts,
            "derivation_metadata": _thaw(self.derivation_metadata) if self.derivation_metadata is not None else None,
            "extra_payload": _thaw(self.extra_payload or {}),
        }


@dataclass(frozen=True)
class NativeMotifView:
    motif_object_id: UUID
    motif_revision_id: UUID
    revision_ordinal: int
    identity_namespace_id: UUID
    state: MotifState


@dataclass(frozen=True)
class MotifMembershipView:
    relationship_id: UUID
    relationship_revision_id: UUID
    revision_ordinal: int
    member_object_id: UUID
    member_semantic_scope_id: UUID


@dataclass(frozen=True)
class NativeMotifMutationResult:
    motif_object_id: UUID
    motif_revision_id: UUID
    motif_revision_ordinal: int
    transition_id: UUID
    operation_id: UUID
    membership_relationship_id: UUID | None = None
    membership_relationship_revision_id: UUID | None = None
    membership_revision_ordinal: int | None = None


class NativeMotifService:
    """Native, persistence-only motif and membership operations.

    A motif is born together with its first member because the current
    ``MotifRegistry`` never publishes a newly-created empty motif.  Adding a
    member requires its supplied aggregate successor state, matching the
    current attach path which changes the centroid and other aggregates.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection)
        self._connection = connection
        # These services own the frozen object/relationship shapes used below.
        self._objects = NativeObjectService(connection)
        self._relationships = NativeRelationshipService(connection)

    def create_motif_with_member(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        motif_identity_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        motif_alias_namespace_id: UUID,
        state: MotifState,
        member_object_id: UUID,
    ) -> NativeMotifMutationResult:
        _validate_state(state)
        _validate_mutation_ids(
            idempotency_namespace_id,
            idempotency_key,
            motif_identity_namespace_id,
            membership_identity_namespace_id,
            motif_alias_namespace_id,
            member_object_id,
        )
        self._require_row("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id)
        self._require_row("identity_namespaces", "identity_namespace_id", motif_identity_namespace_id)
        self._require_row("identity_namespaces", "identity_namespace_id", membership_identity_namespace_id)
        self._require_row("legacy_source_namespaces", "legacy_source_namespace_id", motif_alias_namespace_id)
        self._require_row("semantic_scopes", "semantic_scope_id", state.semantic_scope_id)
        intent = canonical_intent_text(
            {
                "kind": "NATIVE_MOTIF_CREATE_WITH_MEMBER",
                "motif_identity_namespace_id": str(motif_identity_namespace_id),
                "membership_identity_namespace_id": str(membership_identity_namespace_id),
                "motif_alias_namespace_id": str(motif_alias_namespace_id),
                "state": state.intent(),
                "member_object_id": str(member_object_id),
            }
        )
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            idempotency_key,
            "NATIVE_MOTIF_CREATE_WITH_MEMBER",
            intent,
            self._result_for_operation,
            lambda tx: self._create_with_member(
                tx,
                motif_identity_namespace_id,
                membership_identity_namespace_id,
                motif_alias_namespace_id,
                state,
                member_object_id,
            ),
        )

    def add_motif_member(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        motif_alias_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        motif_object_id: UUID,
        expected_motif_revision_id: UUID,
        state: MotifState,
        member_object_id: UUID,
    ) -> NativeMotifMutationResult:
        _validate_state(state)
        _validate_mutation_ids(
            idempotency_namespace_id,
            idempotency_key,
            membership_identity_namespace_id,
            motif_alias_namespace_id,
            motif_object_id,
            expected_motif_revision_id,
            member_object_id,
        )
        self._require_row("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id)
        self._require_row("identity_namespaces", "identity_namespace_id", membership_identity_namespace_id)
        self._require_row("legacy_source_namespaces", "legacy_source_namespace_id", motif_alias_namespace_id)
        self._require_row("semantic_scopes", "semantic_scope_id", state.semantic_scope_id)
        intent = canonical_intent_text(
            {
                "kind": "NATIVE_MOTIF_ADD_MEMBER",
                "motif_alias_namespace_id": str(motif_alias_namespace_id),
                "membership_identity_namespace_id": str(membership_identity_namespace_id),
                "motif_object_id": str(motif_object_id),
                "expected_motif_revision_id": str(expected_motif_revision_id),
                "state": state.intent(),
                "member_object_id": str(member_object_id),
            }
        )
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            idempotency_key,
            "NATIVE_MOTIF_ADD_MEMBER",
            intent,
            self._result_for_operation,
            lambda tx: self._add_member(
                tx,
                motif_alias_namespace_id,
                membership_identity_namespace_id,
                motif_object_id,
                expected_motif_revision_id,
                state,
                member_object_id,
            ),
        )

    def advance_motif_state(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        motif_alias_namespace_id: UUID,
        motif_object_id: UUID,
        expected_motif_revision_id: UUID,
        state: MotifState,
    ) -> NativeMotifMutationResult:
        _validate_state(state)
        _validate_mutation_ids(
            idempotency_namespace_id,
            idempotency_key,
            motif_alias_namespace_id,
            motif_object_id,
            expected_motif_revision_id,
        )
        self._require_row("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id)
        self._require_row("legacy_source_namespaces", "legacy_source_namespace_id", motif_alias_namespace_id)
        self._require_row("semantic_scopes", "semantic_scope_id", state.semantic_scope_id)
        intent = canonical_intent_text(
            {
                "kind": "NATIVE_MOTIF_STATE_ADVANCE",
                "motif_alias_namespace_id": str(motif_alias_namespace_id),
                "motif_object_id": str(motif_object_id),
                "expected_motif_revision_id": str(expected_motif_revision_id),
                "state": state.intent(),
            }
        )
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            idempotency_key,
            "NATIVE_MOTIF_STATE_ADVANCE",
            intent,
            self._result_for_operation,
            lambda tx: self._advance_state(
                tx,
                motif_alias_namespace_id,
                motif_object_id,
                expected_motif_revision_id,
                state,
            ),
        )

    def get_current_motif(self, motif_object_id: UUID) -> NativeMotifView:
        _require_uuid("motif_object_id", motif_object_id)
        row = self._connection.execute(
            """
            SELECT o.object_id,o.identity_namespace_id,o.object_kind,
                   r.object_revision_id,r.revision_ordinal,r.effective_semantic_scope_id,
                   r.payload_format,r.payload_text
              FROM objects o
              JOIN object_revisions r
                ON r.object_id=o.object_id
               AND r.object_revision_id=o.current_revision_id
               AND r.revision_ordinal=o.current_revision_ordinal
             WHERE o.object_id=?
            """,
            (_blob(motif_object_id),),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("native motif was not found")
        if row[2] != DERIVED_MOTIF_OBJECT_KIND:
            raise SubstrateInvariantViolation("object is not a native derived motif")
        if row[6] != "JSON" or row[7] is None:
            raise SubstrateInvariantViolation("native motif current state is not JSON")
        state = _state_from_payload(UUID(bytes=row[5]), row[7])
        return NativeMotifView(
            UUID(bytes=row[0]), UUID(bytes=row[3]), row[4], UUID(bytes=row[1]), state
        )

    def resolve_motif_alias(
        self, *, motif_alias_namespace_id: UUID, runtime_motif_id: str
    ) -> UUID:
        _require_uuid("motif_alias_namespace_id", motif_alias_namespace_id)
        _nonempty_text("runtime_motif_id", runtime_motif_id)
        row = self._connection.execute(
            """
            SELECT a.object_id,o.object_kind
              FROM legacy_object_aliases a
              JOIN objects o ON o.object_id=a.object_id
             WHERE a.legacy_source_namespace_id=? AND a.alias_kind=? AND a.alias_value=?
            """,
            (_blob(motif_alias_namespace_id), MOTIF_ID_ALIAS_KIND, runtime_motif_id),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("scoped runtime motif ID alias was not found")
        if row[1] != DERIVED_MOTIF_OBJECT_KIND:
            raise SubstrateInvariantViolation("runtime motif ID alias does not target a native motif")
        return UUID(bytes=row[0])

    def list_current_motif_members(self, motif_object_id: UUID) -> tuple[MotifMembershipView, ...]:
        _require_uuid("motif_object_id", motif_object_id)
        self.get_current_motif(motif_object_id)
        rows = self._connection.execute(
            """
            SELECT h.relationship_id,r.relationship_revision_id,r.revision_ordinal,
                   member.object_id,member.endpoint_semantic_scope_id
              FROM relationships h
              JOIN relationship_revisions r
                ON r.relationship_id=h.relationship_id
               AND r.relationship_revision_id=h.current_revision_id
               AND r.revision_ordinal=h.current_revision_ordinal
              JOIN relationship_revision_endpoints motif
                ON motif.relationship_revision_id=r.relationship_revision_id
               AND motif.endpoint_ordinal=0
               AND motif.endpoint_role='MOTIF'
               AND motif.binding_mode='IDENTITY'
              JOIN relationship_revision_endpoints member
                ON member.relationship_revision_id=r.relationship_revision_id
               AND member.endpoint_ordinal=1
               AND member.endpoint_role='MEMBER'
               AND member.binding_mode='IDENTITY'
             WHERE h.relationship_kind=? AND motif.object_id=?
             ORDER BY h.relationship_id
            """,
            (MOTIF_MEMBERSHIP_RELATIONSHIP_KIND, _blob(motif_object_id)),
        ).fetchall()
        return tuple(
            MotifMembershipView(
                UUID(bytes=row[0]), UUID(bytes=row[1]), row[2], UUID(bytes=row[3]), UUID(bytes=row[4])
            )
            for row in rows
        )

    def _create_with_member(
        self,
        tx: SubstrateTx,
        motif_identity_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        motif_alias_namespace_id: UUID,
        state: MotifState,
        member_object_id: UUID,
    ) -> NativeMotifMutationResult:
        if self._alias_row(tx, motif_alias_namespace_id, state.runtime_motif_id) is not None:
            raise SubstrateRevisionConflict("runtime motif ID alias already exists in this namespace")
        member_scope_id = self._require_compatible_member(tx, member_object_id)
        transition_id = _new()
        motif_object_id, motif_revision_id = _new(), _new()
        membership_id, membership_revision_id = _new(), _new()
        motif_object_state = _motif_object_state(motif_identity_namespace_id, state)
        self._insert_motif_creation(
            tx, motif_object_id, motif_revision_id, transition_id, motif_object_state
        )
        membership_state = _membership_state(
            membership_identity_namespace_id, state.semantic_scope_id, motif_object_id, member_scope_id, member_object_id
        )
        self._insert_membership(
            tx, membership_id, membership_revision_id, transition_id, membership_state
        )
        tx.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
            (_blob(motif_alias_namespace_id), MOTIF_ID_ALIAS_KIND, state.runtime_motif_id, motif_object_id),
        )
        return self._publish(
            tx,
            transition_id,
            "NATIVE_MOTIF_CREATE_WITH_MEMBER",
            motif_object_id,
            motif_revision_id,
            1,
            membership_id,
            membership_revision_id,
            1,
        )

    def _add_member(
        self,
        tx: SubstrateTx,
        motif_alias_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        motif_object_id: UUID,
        expected_motif_revision_id: UUID,
        state: MotifState,
        member_object_id: UUID,
    ) -> NativeMotifMutationResult:
        current = self._assert_current_motif(tx, motif_object_id, expected_motif_revision_id, state)
        self._assert_alias_target(tx, motif_alias_namespace_id, state.runtime_motif_id, motif_object_id)
        member_scope_id = self._require_compatible_member(tx, member_object_id)
        if self._has_current_membership(tx, motif_object_id, member_object_id):
            raise SubstrateRevisionConflict("motif already has this logical member")
        transition_id, motif_revision_id = _new(), _new()
        ordinal = current[1] + 1
        self._insert_motif_successor(
            tx, motif_object_id, motif_revision_id, ordinal, expected_motif_revision_id, current[1],
            _motif_object_state(UUID(bytes=current[2]), state),
        )
        membership_id, membership_revision_id = _new(), _new()
        membership_state = _membership_state(
            membership_identity_namespace_id, state.semantic_scope_id, motif_object_id, member_scope_id, member_object_id
        )
        self._insert_membership(
            tx, membership_id, membership_revision_id, transition_id, membership_state
        )
        return self._publish(
            tx,
            transition_id,
            "NATIVE_MOTIF_ADD_MEMBER",
            _blob(motif_object_id),
            motif_revision_id,
            ordinal,
            membership_id,
            membership_revision_id,
            1,
        )

    def _advance_state(
        self,
        tx: SubstrateTx,
        motif_alias_namespace_id: UUID,
        motif_object_id: UUID,
        expected_motif_revision_id: UUID,
        state: MotifState,
    ) -> NativeMotifMutationResult:
        current = self._assert_current_motif(tx, motif_object_id, expected_motif_revision_id, state)
        self._assert_alias_target(tx, motif_alias_namespace_id, state.runtime_motif_id, motif_object_id)
        transition_id, motif_revision_id = _new(), _new()
        ordinal = current[1] + 1
        self._insert_motif_successor(
            tx, motif_object_id, motif_revision_id, ordinal, expected_motif_revision_id, current[1],
            _motif_object_state(UUID(bytes=current[2]), state),
        )
        return self._publish(
            tx,
            transition_id,
            "NATIVE_MOTIF_STATE_ADVANCE",
            _blob(motif_object_id),
            motif_revision_id,
            ordinal,
        )

    def _insert_motif_creation(
        self, tx: SubstrateTx, motif_id: bytes, revision_id: bytes, transition_id: bytes, state: ObjectState
    ) -> None:
        self._objects._state(state)
        tx.execute(
            """
            INSERT INTO objects(
                object_id,identity_namespace_id,object_kind,creating_transition_id,
                current_revision_id,current_revision_ordinal,created_at_ns
            ) VALUES (?,?,?,?,?,?,0)
            """,
            (motif_id, _blob(state.identity_namespace_id), DERIVED_MOTIF_OBJECT_KIND, transition_id, revision_id, 1),
        )
        self._objects._revision(tx, revision_id, motif_id, 1, "NATIVE_CREATION", None, None, state)

    def _insert_motif_successor(
        self,
        tx: SubstrateTx,
        motif_id: UUID,
        revision_id: bytes,
        ordinal: int,
        predecessor_id: UUID,
        predecessor_ordinal: int,
        state: ObjectState,
    ) -> None:
        self._objects._state(state)
        self._objects._revision(
            tx, revision_id, _blob(motif_id), ordinal, "NATIVE_ORDINARY", _blob(predecessor_id), predecessor_ordinal, state
        )

    def _insert_membership(
        self,
        tx: SubstrateTx,
        membership_id: bytes,
        revision_id: bytes,
        transition_id: bytes,
        state: RelationshipState,
    ) -> None:
        self._relationships._check(state, tx)
        tx.execute(
            """
            INSERT INTO relationships(
                relationship_id,identity_namespace_id,relationship_kind,creating_transition_id,
                current_revision_id,current_revision_ordinal,created_at_ns
            ) VALUES (?,?,?,?,?,?,0)
            """,
            (membership_id, _blob(state.identity_namespace_id), MOTIF_MEMBERSHIP_RELATIONSHIP_KIND, transition_id, revision_id, 1),
        )
        self._relationships._revision(tx, membership_id, revision_id, 1, "NATIVE_CREATION", None, None, state)

    def _publish(
        self,
        tx: SubstrateTx,
        transition_id: bytes,
        transition_kind: str,
        motif_id: bytes,
        motif_revision_id: bytes,
        motif_ordinal: int,
        membership_id: bytes | None = None,
        membership_revision_id: bytes | None = None,
        membership_ordinal: int | None = None,
        *,
        omit_membership_effect: bool = False,
    ) -> NativeMotifMutationResult:
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (transition_id, tx.operation_id, transition_kind, "NATIVE"),
        )
        tx.execute(
            "INSERT INTO object_revision_effects VALUES (?,?,?,?)",
            (transition_id, motif_id, motif_revision_id, motif_ordinal),
        )
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,
                object_id,object_revision_id,object_revision_ordinal
            ) VALUES (?,?,?,?,?,?,?)
            """,
            (tx.operation_id, 0, "MOTIF", "OBJECT", motif_id, motif_revision_id, motif_ordinal),
        )
        tx.execute(
            "UPDATE objects SET current_revision_id=?,current_revision_ordinal=? WHERE object_id=?",
            (motif_revision_id, motif_ordinal, motif_id),
        )
        tx.transitions.append(transition_id)
        tx.published.append((motif_id, motif_revision_id, motif_ordinal))
        if membership_id is not None and membership_revision_id is not None and membership_ordinal is not None:
            if not omit_membership_effect:
                tx.execute(
                    "INSERT INTO relationship_revision_effects VALUES (?,?,?,?)",
                    (transition_id, membership_id, membership_revision_id, membership_ordinal),
                )
            tx.execute(
                """
                INSERT INTO operation_outputs(
                    operation_id,output_ordinal,output_role,output_kind,
                    relationship_id,relationship_revision_id,relationship_revision_ordinal
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    tx.operation_id,
                    1,
                    "MOTIF_MEMBERSHIP",
                    "RELATIONSHIP",
                    membership_id,
                    membership_revision_id,
                    membership_ordinal,
                ),
            )
            tx.execute(
                "UPDATE relationships SET current_revision_id=?,current_revision_ordinal=? WHERE relationship_id=?",
                (membership_revision_id, membership_ordinal, membership_id),
            )
            tx.relationship_published.append((membership_id, membership_revision_id, membership_ordinal))
        return NativeMotifMutationResult(
            UUID(bytes=motif_id),
            UUID(bytes=motif_revision_id),
            motif_ordinal,
            UUID(bytes=transition_id),
            UUID(bytes=tx.operation_id),
            UUID(bytes=membership_id) if membership_id is not None else None,
            UUID(bytes=membership_revision_id) if membership_revision_id is not None else None,
            membership_ordinal,
        )

    def _assert_current_motif(
        self, tx: SubstrateTx, motif_id: UUID, expected_revision_id: UUID, state: MotifState
    ) -> tuple[bytes, int, bytes, MotifState]:
        row = tx.execute(
            """
            SELECT o.current_revision_id,o.current_revision_ordinal,o.identity_namespace_id,
                   r.effective_semantic_scope_id,r.payload_format,r.payload_text,o.object_kind
              FROM objects o
              JOIN object_revisions r
                ON r.object_id=o.object_id
               AND r.object_revision_id=o.current_revision_id
               AND r.revision_ordinal=o.current_revision_ordinal
             WHERE o.object_id=?
            """,
            (_blob(motif_id),),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("native motif was not found")
        if row[6] != DERIVED_MOTIF_OBJECT_KIND:
            raise SubstrateInvariantViolation("object is not a native derived motif")
        if row[0] != _blob(expected_revision_id):
            raise SubstrateRevisionConflict("expected motif predecessor is not current")
        if row[4] != "JSON" or row[5] is None:
            raise SubstrateInvariantViolation("native motif current state is not JSON")
        current_state = _state_from_payload(UUID(bytes=row[3]), row[5])
        if (
            state.semantic_scope_id != current_state.semantic_scope_id
            or state.runtime_motif_id != current_state.runtime_motif_id
            or state.domain_id != current_state.domain_id
            or state.label != current_state.label
            or state.created_ts != current_state.created_ts
        ):
            raise SubstrateInvariantViolation("motif successor changes immutable runtime identity state")
        return row[0], row[1], row[2], current_state

    def _require_compatible_member(self, tx: SubstrateTx, member_object_id: UUID) -> UUID:
        row = tx.execute(
            """
            SELECT o.object_kind,r.effective_semantic_scope_id
              FROM objects o
              JOIN object_revisions r
                ON r.object_id=o.object_id
               AND r.object_revision_id=o.current_revision_id
               AND r.revision_ordinal=o.current_revision_ordinal
             WHERE o.object_id=?
            """,
            (_blob(member_object_id),),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("motif member object was not found or is not committed")
        if row[0] != _MEMORY_OBJECT_KIND:
            raise SubstrateInvariantViolation("motif membership requires a compatible committed native memory")
        return UUID(bytes=row[1])

    def _has_current_membership(self, tx: SubstrateTx, motif_id: UUID, member_id: UUID) -> bool:
        return tx.execute(
            """
            SELECT 1
              FROM relationships h
              JOIN relationship_revisions r
                ON r.relationship_id=h.relationship_id
               AND r.relationship_revision_id=h.current_revision_id
               AND r.revision_ordinal=h.current_revision_ordinal
              JOIN relationship_revision_endpoints motif
                ON motif.relationship_revision_id=r.relationship_revision_id
               AND motif.endpoint_ordinal=0 AND motif.endpoint_role='MOTIF'
               AND motif.binding_mode='IDENTITY'
              JOIN relationship_revision_endpoints member
                ON member.relationship_revision_id=r.relationship_revision_id
               AND member.endpoint_ordinal=1 AND member.endpoint_role='MEMBER'
               AND member.binding_mode='IDENTITY'
             WHERE h.relationship_kind=? AND motif.object_id=? AND member.object_id=?
            """,
            (MOTIF_MEMBERSHIP_RELATIONSHIP_KIND, _blob(motif_id), _blob(member_id)),
        ).fetchone() is not None

    def _alias_row(self, tx: SubstrateTx, namespace_id: UUID, runtime_motif_id: str) -> bytes | None:
        row = tx.execute(
            "SELECT object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind=? AND alias_value=?",
            (_blob(namespace_id), MOTIF_ID_ALIAS_KIND, runtime_motif_id),
        ).fetchone()
        return row[0] if row else None

    def _assert_alias_target(
        self, tx: SubstrateTx, namespace_id: UUID, runtime_motif_id: str, motif_id: UUID
    ) -> None:
        if self._alias_row(tx, namespace_id, runtime_motif_id) != _blob(motif_id):
            raise SubstrateInvariantViolation("scoped runtime motif ID alias does not match motif identity")

    def _result_for_operation(self, operation_id: bytes) -> NativeMotifMutationResult | None:
        rows = self._connection.execute(
            """
            SELECT t.transition_id,t.operation_id,t.transition_kind,o.output_ordinal,o.output_role,o.output_kind,
                   o.object_id,o.object_revision_id,o.object_revision_ordinal,
                   o.relationship_id,o.relationship_revision_id,o.relationship_revision_ordinal
              FROM semantic_transitions t
              JOIN operation_outputs o ON o.operation_id=t.operation_id
             WHERE t.operation_id=?
             ORDER BY o.output_ordinal
            """,
            (operation_id,),
        ).fetchall()
        if not rows or rows[0][5] != "OBJECT" or rows[0][4] != "MOTIF":
            return None
        motif = rows[0]
        if len(rows) == 1:
            if motif[2] != "NATIVE_MOTIF_STATE_ADVANCE":
                return None
            return NativeMotifMutationResult(
                UUID(bytes=motif[6]), UUID(bytes=motif[7]), motif[8], UUID(bytes=motif[0]), UUID(bytes=motif[1])
            )
        if len(rows) != 2 or motif[2] not in {"NATIVE_MOTIF_CREATE_WITH_MEMBER", "NATIVE_MOTIF_ADD_MEMBER"}:
            return None
        membership = rows[1]
        if membership[4:6] != ("MOTIF_MEMBERSHIP", "RELATIONSHIP"):
            return None
        return NativeMotifMutationResult(
            UUID(bytes=motif[6]),
            UUID(bytes=motif[7]),
            motif[8],
            UUID(bytes=motif[0]),
            UUID(bytes=motif[1]),
            UUID(bytes=membership[9]),
            UUID(bytes=membership[10]),
            membership[11],
        )

    def _require_row(self, table: str, column: str, value: UUID) -> None:
        if self._connection.execute(
            f"SELECT 1 FROM {table} WHERE {column}=?", (_blob(value),)
        ).fetchone() is None:
            raise SubstrateObjectNotFound(f"required {table} identity was not found")


def _motif_object_state(identity_namespace_id: UUID, state: MotifState) -> ObjectState:
    return ObjectState(
        identity_namespace_id,
        state.semantic_scope_id,
        DERIVED_MOTIF_OBJECT_KIND,
        "EXISTS",
        "DERIVED",
        False,
        "DERIVED",
        "NOT_APPLICABLE",
        state.payload(),
        "JSON",
    )


def _membership_state(
    identity_namespace_id: UUID,
    motif_scope_id: UUID,
    motif_object_id: bytes | UUID,
    member_scope_id: UUID,
    member_object_id: UUID,
) -> RelationshipState:
    motif_uuid = UUID(bytes=motif_object_id) if isinstance(motif_object_id, bytes) else motif_object_id
    return RelationshipState(
        identity_namespace_id,
        motif_scope_id,
        MOTIF_MEMBERSHIP_RELATIONSHIP_KIND,
        "EXISTS",
        "DERIVED",
        False,
        "DERIVED",
        "NOT_APPLICABLE",
        (
            Endpoint(0, "MOTIF", motif_scope_id, motif_uuid, "IDENTITY"),
            Endpoint(1, "MEMBER", member_scope_id, member_object_id, "IDENTITY"),
        ),
    )


def _state_from_payload(scope_id: UUID, payload_text: str) -> MotifState:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise SubstrateInvariantViolation("native motif payload is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise SubstrateInvariantViolation("native motif payload is not an object")
    required = {
        "motif_id", "domain_id", "label", "centroid", "strength", "stability_score",
        "contributing_agents", "created_ts", "last_active_ts",
    }
    if not required.issubset(payload):
        raise SubstrateInvariantViolation("native motif payload is missing durable state")
    extra = {key: value for key, value in payload.items() if key not in _STATE_PAYLOAD_KEYS}
    try:
        state = MotifState(
            scope_id,
            payload["motif_id"],
            payload["domain_id"],
            payload["label"],
            tuple(payload["centroid"]),
            payload["strength"],
            payload["stability_score"],
            tuple(payload["contributing_agents"]),
            payload["created_ts"],
            payload["last_active_ts"],
            payload.get("derivation_metadata"),
            extra,
        )
        _validate_state(state)
    except (TypeError, ValueError) as exc:
        raise SubstrateInvariantViolation("native motif payload is not a valid motif state") from exc
    if "members" in payload or "member_count" in payload:
        raise SubstrateInvariantViolation("motif membership truth must not be duplicated in payload")
    return state


def _validate_state(state: MotifState) -> None:
    if not isinstance(state, MotifState):
        raise ValueError("state must be a MotifState")
    _require_uuid("semantic_scope_id", state.semantic_scope_id)
    for field, value in (
        ("runtime_motif_id", state.runtime_motif_id),
        ("domain_id", state.domain_id),
        ("label", state.label),
    ):
        _nonempty_text(field, value)
    if not state.centroid:
        raise ValueError("centroid must be a non-empty finite numeric vector")
    if any(not _finite_number(value) for value in state.centroid):
        raise ValueError("centroid must be a non-empty finite numeric vector")
    for field, value in (("strength", state.strength), ("stability_score", state.stability_score)):
        if not _finite_number(value) or not 0.0 <= float(value) <= 1.0:
            raise ValueError(f"{field} must be a finite value in [0, 1]")
    if any(not isinstance(value, str) or not value for value in state.contributing_agents):
        raise ValueError("contributing_agents must contain only non-empty strings")
    if len(set(state.contributing_agents)) != len(state.contributing_agents):
        raise ValueError("contributing_agents must not repeat")
    for field, value in (("created_ts", state.created_ts), ("last_active_ts", state.last_active_ts)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{field} must be a non-negative integer")
    if state.last_active_ts < state.created_ts:
        raise ValueError("last_active_ts must not precede created_ts")
    _validate_flexible_mapping(state.derivation_metadata, "derivation_metadata", forbid_structural=False)
    _validate_flexible_mapping(state.extra_payload, "extra_payload", forbid_structural=True)
    try:
        canonical_intent_text(state.payload())
    except (TypeError, ValueError) as exc:
        raise ValueError("motif state must be JSON serializable") from exc


def _validate_mutation_ids(*values: Any) -> None:
    for value in values:
        if isinstance(value, str):
            if not value:
                raise ValueError("idempotency_key must be a non-empty string")
        else:
            _require_uuid("mutation identifier", value)


def _validate_flexible_mapping(value: Mapping[str, Any] | None, field: str, *, forbid_structural: bool) -> None:
    if value is None:
        return
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    for key in value:
        if not isinstance(key, str):
            raise ValueError(f"{field} keys must be strings")
        if forbid_structural and key in _STATE_PAYLOAD_KEYS | _EXTRA_FORBIDDEN_KEYS:
            raise ValueError(f"{field} cannot overwrite motif state semantics")


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        return value
    return MappingProxyType({key: _freeze_value(item) for key, item in value.items()})


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _nonempty_text(field: str, value: Any) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be non-empty text")


def _require_uuid(field: str, value: Any) -> None:
    if not isinstance(value, UUID):
        raise ValueError(f"{field} must be a UUID")


def _blob(value: UUID) -> bytes:
    return native_id_to_bytes(value)


def _new() -> bytes:
    return native_id_to_bytes(generate_native_id())
