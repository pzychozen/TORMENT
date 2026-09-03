"""Phase 7G5A1 native motif persistence primitives.

This module intentionally persists already-decided motif changes.  It neither
selects motifs nor invokes the legacy :mod:`torment_service.motifs` algorithm.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import sqlite3
from types import MappingProxyType
from typing import Any, Callable, Mapping
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
MIGRATION_ZERO_MEMBER_MOTIF_BASELINE_OPERATION_KIND = (
    "MIGRATION_RUNTIME_ZERO_MEMBER_MOTIF_PROJECTION"
)
MIGRATION_ZERO_MEMBER_MOTIF_BASELINE_TRANSITION_KIND = (
    "MIGRATION_RUNTIME_ZERO_MEMBER_MOTIF_PROJECTION"
)
MIGRATION_ZERO_MEMBER_MOTIF_BASELINE_OUTPUT_ROLE = (
    "MIGRATION_RUNTIME_ZERO_MEMBER_MOTIF_PROJECTION"
)
MIGRATION_ZERO_MEMBER_MOTIF_BASELINE_CONTRACT = (
    "TMS-MIGRATION-ZERO-MEMBER-MOTIF-BASELINE/1"
)

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


@dataclass(frozen=True)
class MigrationZeroMemberMotifBaselineEvidence:
    """Durable evidence bound to the one lawful empty-motif import path.

    This is deliberately not a generic motif-creation request.  Its complete
    source and target-lane witness is included in the idempotent operation
    intent, and :meth:`NativeMotifService.publish_migration_zero_member_baseline`
    accepts only an exactly-zero source member count.
    """

    native_core_id: UUID
    legacy_snapshot_id: UUID
    legacy_source_namespace_id: UUID
    source_motif_object_id: UUID
    source_motif_revision_id: UUID
    source_operation_id: UUID
    source_transition_id: UUID
    source_motif_artifact_id: UUID
    source_motif_artifact_digest: str
    workspace_metadata_artifact_id: UUID
    workspace_metadata_digest: str
    runtime_motif_id: str
    source_geometry_lane: tuple[str, str, int]
    target_lane_identity: tuple[str, str, int, str, int, str, str, str]
    scope_plan_digest: str
    motif_identity_namespace_id: UUID
    membership_identity_namespace_id: UUID
    motif_alias_namespace_id: UUID
    target_semantic_scope_id: UUID
    source_state_digest: str
    source_membership_digest: str
    source_member_count: int

    def intent(self) -> dict[str, Any]:
        return {
            "contract": MIGRATION_ZERO_MEMBER_MOTIF_BASELINE_CONTRACT,
            "native_core_id": str(self.native_core_id),
            "snapshot_id": str(self.legacy_snapshot_id),
            "source_namespace_id": str(self.legacy_source_namespace_id),
            "source_motif_object_id": str(self.source_motif_object_id),
            "source_motif_revision_id": str(self.source_motif_revision_id),
            "source_operation_id": str(self.source_operation_id),
            "source_transition_id": str(self.source_transition_id),
            "source_motif_artifact_id": str(self.source_motif_artifact_id),
            "source_motif_artifact_digest": self.source_motif_artifact_digest,
            "workspace_metadata_artifact_id": str(self.workspace_metadata_artifact_id),
            "workspace_metadata_digest": self.workspace_metadata_digest,
            "runtime_motif_id": self.runtime_motif_id,
            "source_geometry_lane": list(self.source_geometry_lane),
            "target_lane_identity": list(self.target_lane_identity),
            "scope_plan_digest": self.scope_plan_digest,
            "motif_identity_namespace_id": str(self.motif_identity_namespace_id),
            "membership_identity_namespace_id": str(self.membership_identity_namespace_id),
            "motif_alias_namespace_id": str(self.motif_alias_namespace_id),
            "target_semantic_scope_id": str(self.target_semantic_scope_id),
            "source_state_digest": self.source_state_digest,
            "source_membership_digest": self.source_membership_digest,
            "source_member_count": self.source_member_count,
        }


@dataclass(frozen=True)
class NativeMotifSplitPlan:
    """Storage-shaped final topology for one already-decided auto-split.

    The mathematical partition is deliberately decided by
    :mod:`torment_service.motif_split_policy`.  This plan contains only the
    durable relationship identities which must move and the final aggregate
    states to publish.
    """

    parent_motif_object_id: UUID
    expected_parent_revision_id: UUID
    parent_state: MotifState
    child_state: MotifState
    moved_member_object_ids: tuple[UUID, ...]
    candidate_member_object_id: UUID
    candidate_in_child: bool

    def __post_init__(self) -> None:
        if not self.moved_member_object_ids:
            raise ValueError("native motif split requires at least one moved member")
        if len(set(self.moved_member_object_ids)) != len(self.moved_member_object_ids):
            raise ValueError("native motif split moved members must be unique")
        if self.candidate_member_object_id in self.moved_member_object_ids:
            raise ValueError("candidate membership is not a pre-existing parent membership")
        if self.parent_state.runtime_motif_id == self.child_state.runtime_motif_id:
            raise ValueError("native motif split child must have a distinct runtime motif ID")


@dataclass(frozen=True)
class NativeMotifSplitResult:
    parent_motif_object_id: UUID
    parent_motif_revision_id: UUID
    parent_motif_revision_ordinal: int
    child_motif_object_id: UUID
    child_motif_revision_id: UUID
    child_runtime_motif_id: str
    retired_membership_relationship_ids: tuple[UUID, ...]
    child_membership_relationship_ids: tuple[UUID, ...]
    parent_candidate_membership_relationship_id: UUID | None
    transition_id: UUID
    operation_id: UUID


@dataclass(frozen=True)
class NativePrecommitSplitAttach:
    """The durable first half of I4B-2's two-stage true split.

    The incoming memory is deliberately attached to the existing parent in
    this operation.  The stored final plan, rather than a later catalog read,
    is the authority for the bounded finalization operation.
    """

    plan: NativeMotifSplitPlan
    attached_parent_state: MotifState
    mutation: NativeMotifMutationResult
    precommit_context: Mapping[str, Any]


@dataclass(frozen=True)
class NativeMotifMergeResult:
    """Durable outcome of one already-authorized native motif merge.

    The surviving motif receives an ordinary successor.  The dropped motif is
    retained as a current ``RETIRED`` successor so its alias and complete
    historical lineage remain resolvable without making it part of current
    runtime geometry.
    """

    keep_motif_object_id: UUID
    keep_motif_revision_id: UUID
    keep_motif_revision_ordinal: int
    keep_runtime_motif_id: str
    drop_motif_object_id: UUID
    drop_motif_revision_id: UUID
    drop_motif_revision_ordinal: int
    drop_runtime_motif_id: str
    retired_drop_membership_relationship_ids: tuple[UUID, ...]
    created_keep_membership_relationship_ids: tuple[UUID, ...]
    transition_id: UUID
    operation_id: UUID


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

    def publish_migration_zero_member_baseline(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        state: MotifState,
        evidence: MigrationZeroMemberMotifBaselineEvidence,
        revalidate: Callable[[], tuple[MotifState, MigrationZeroMemberMotifBaselineEvidence]],
    ) -> NativeMotifMutationResult:
        """Publish the sole migration-authorized zero-member motif baseline.

        Ordinary native creation remains :meth:`create_motif_with_member`.
        This separate primitive has no member parameter, is bound to a
        complete durable source witness, and is permitted only while the core
        remains STAGING with legacy deployment authority.  ``revalidate`` is
        invoked after ``BEGIN IMMEDIATE`` so a B4C coordinator can reread its
        source evidence while this service owns the publication transaction.
        """
        _validate_state(state)
        _validate_zero_member_baseline_evidence(evidence, state)
        if not callable(revalidate):
            raise ValueError("migration zero-member baseline requires a revalidation callback")
        self._validate_zero_member_baseline_posture(evidence)
        for table, column, value in (
            ("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id),
            ("identity_namespaces", "identity_namespace_id", evidence.motif_identity_namespace_id),
            ("identity_namespaces", "identity_namespace_id", evidence.membership_identity_namespace_id),
            ("legacy_source_namespaces", "legacy_source_namespace_id", evidence.motif_alias_namespace_id),
            ("semantic_scopes", "semantic_scope_id", evidence.target_semantic_scope_id),
        ):
            self._require_row(table, column, value)
        if state.semantic_scope_id != evidence.target_semantic_scope_id:
            raise SubstrateInvariantViolation("migration zero-member baseline scope does not match its evidence")
        intent = canonical_intent_text(
            {
                "kind": MIGRATION_ZERO_MEMBER_MOTIF_BASELINE_OPERATION_KIND,
                "state": state.intent(),
                "evidence": evidence.intent(),
            }
        )

        def mutate(tx: SubstrateTx) -> NativeMotifMutationResult:
            fresh_state, fresh_evidence = revalidate()
            _validate_state(fresh_state)
            _validate_zero_member_baseline_evidence(fresh_evidence, fresh_state)
            self._validate_zero_member_baseline_posture(fresh_evidence)
            if fresh_state.intent() != state.intent() or fresh_evidence.intent() != evidence.intent():
                raise SubstrateInvariantViolation("migration zero-member baseline evidence changed before publication")
            return self._publish_migration_zero_member_baseline(tx, fresh_state, fresh_evidence)

        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            idempotency_key,
            MIGRATION_ZERO_MEMBER_MOTIF_BASELINE_OPERATION_KIND,
            intent,
            self._zero_member_baseline_result_for_operation,
            mutate,
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

    def split_motif_with_member(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        motif_identity_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        motif_alias_namespace_id: UUID,
        plan: NativeMotifSplitPlan,
        _test_fail_after: str | None = None,
    ) -> NativeMotifSplitResult:
        """Atomically publish a final parent/child membership topology.

        The candidate has no transient parent relationship when it belongs to
        the child.  Existing parent memberships moved to the child retain
        their relationship identity and receive one ``RETIRED`` successor.
        """
        if not isinstance(plan, NativeMotifSplitPlan):
            raise ValueError("a NativeMotifSplitPlan is required")
        _validate_state(plan.parent_state)
        _validate_state(plan.child_state)
        _validate_mutation_ids(
            idempotency_namespace_id, idempotency_key, motif_identity_namespace_id,
            membership_identity_namespace_id, motif_alias_namespace_id,
            plan.parent_motif_object_id, plan.expected_parent_revision_id,
            *plan.moved_member_object_ids, plan.candidate_member_object_id,
        )
        for table, column, value in (
            ("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id),
            ("identity_namespaces", "identity_namespace_id", motif_identity_namespace_id),
            ("identity_namespaces", "identity_namespace_id", membership_identity_namespace_id),
            ("legacy_source_namespaces", "legacy_source_namespace_id", motif_alias_namespace_id),
            ("semantic_scopes", "semantic_scope_id", plan.parent_state.semantic_scope_id),
            ("semantic_scopes", "semantic_scope_id", plan.child_state.semantic_scope_id),
        ):
            self._require_row(table, column, value)
        intent = canonical_intent_text({
            "kind": "NATIVE_MOTIF_SPLIT_WITH_MEMBER",
            "motif_identity_namespace_id": str(motif_identity_namespace_id),
            "membership_identity_namespace_id": str(membership_identity_namespace_id),
            "motif_alias_namespace_id": str(motif_alias_namespace_id),
            "plan": _split_plan_intent(plan),
        })
        return execute_semantic(
            self._connection, idempotency_namespace_id, idempotency_key,
            "NATIVE_MOTIF_SPLIT_WITH_MEMBER", intent, self._split_result_for_operation,
            lambda tx: self._split_with_member(
                tx, motif_identity_namespace_id, membership_identity_namespace_id,
                motif_alias_namespace_id, plan, _test_fail_after=_test_fail_after,
            ),
        )

    def attach_member_for_precommit_split(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        motif_alias_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        plan: NativeMotifSplitPlan,
        attached_parent_state: MotifState,
        request_identity: Mapping[str, Any],
        precommit_context: Mapping[str, Any],
    ) -> NativeMotifMutationResult:
        """Durably attach the pending candidate before a bounded true split.

        This is intentionally separate from ordinary ``add_motif_member``.
        Its operation intent retains both the attach successor and the final
        split plan so a restart never recalculates the partition from a
        changed catalog.
        """
        if not isinstance(plan, NativeMotifSplitPlan):
            raise ValueError("a NativeMotifSplitPlan is required")
        _validate_state(attached_parent_state)
        _validate_mutation_ids(
            idempotency_namespace_id, idempotency_key,
            motif_alias_namespace_id, membership_identity_namespace_id,
            plan.parent_motif_object_id, plan.expected_parent_revision_id,
            plan.candidate_member_object_id,
        )
        if attached_parent_state.runtime_motif_id != plan.parent_state.runtime_motif_id:
            raise ValueError("precommit split attach changes the parent runtime motif ID")
        if not isinstance(request_identity, Mapping):
            raise ValueError("precommit split request_identity must be a mapping")
        if not isinstance(precommit_context, Mapping):
            raise ValueError("precommit split precommit_context must be a mapping")
        self._require_row("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id)
        self._require_row("identity_namespaces", "identity_namespace_id", membership_identity_namespace_id)
        self._require_row("legacy_source_namespaces", "legacy_source_namespace_id", motif_alias_namespace_id)
        self._require_row("semantic_scopes", "semantic_scope_id", attached_parent_state.semantic_scope_id)
        intent = canonical_intent_text({
            "kind": "NATIVE_I4B2_PRECOMMIT_SPLIT_ATTACH",
            "request_identity": dict(request_identity),
            "precommit_context": dict(precommit_context),
            "parent": {
                "motif_object_id": str(plan.parent_motif_object_id),
                "predecessor_revision_id": str(plan.expected_parent_revision_id),
                "attached_successor_state": attached_parent_state.intent(),
            },
            "incoming": {"memory_object_id": str(plan.candidate_member_object_id)},
            "final_split": _split_plan_intent(plan),
            "child_runtime_motif_id": plan.child_state.runtime_motif_id,
        })
        return execute_semantic(
            self._connection, idempotency_namespace_id, idempotency_key,
            "NATIVE_I4B2_PRECOMMIT_SPLIT_ATTACH", intent,
            self._result_for_operation,
            lambda tx: self._add_member(
                tx, motif_alias_namespace_id, membership_identity_namespace_id,
                plan.parent_motif_object_id, plan.expected_parent_revision_id,
                attached_parent_state, plan.candidate_member_object_id,
                transition_kind="NATIVE_I4B2_PRECOMMIT_SPLIT_ATTACH",
            ),
        )

    def recover_precommit_split_attach(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        request_identity: Mapping[str, Any],
    ) -> NativePrecommitSplitAttach | None:
        """Recover exactly one stored first-stage plan without replanning."""
        if not isinstance(request_identity, Mapping):
            raise ValueError("precommit split request_identity must be a mapping")
        row = self._connection.execute(
            "SELECT operation_id,canonical_intent_json FROM operations "
            "WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (_blob(idempotency_namespace_id), idempotency_key),
        ).fetchone()
        if row is None:
            return None
        try:
            intent = json.loads(row[1])
            if (
                not isinstance(intent, dict)
                or intent.get("kind") != "NATIVE_I4B2_PRECOMMIT_SPLIT_ATTACH"
                or intent.get("request_identity") != dict(request_identity)
            ):
                raise SubstrateRevisionConflict("precommit split attach idempotency intent differs")
            parent = intent["parent"]
            final_split = intent["final_split"]
            if not isinstance(parent, Mapping) or not isinstance(final_split, Mapping):
                raise ValueError("precommit split attach intent is incomplete")
            plan = _split_plan_from_intent(final_split)
            attached_state = _motif_state_from_intent(parent["attached_successor_state"])
            precommit_context = intent["precommit_context"]
            if not isinstance(precommit_context, Mapping):
                raise ValueError("precommit split context is incomplete")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("precommit split attach intent is malformed") from exc
        mutation = self._result_for_operation(row[0])
        if (
            mutation is None
            or mutation.motif_object_id != plan.parent_motif_object_id
            or mutation.membership_relationship_id is None
            or mutation.motif_revision_id == plan.expected_parent_revision_id
        ):
            raise SubstrateInvariantViolation("precommit split attach outputs are incomplete")
        return NativePrecommitSplitAttach(
            plan, attached_state, mutation, MappingProxyType(dict(precommit_context)),
        )

    def finalize_precommit_attached_split(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        motif_identity_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        motif_alias_namespace_id: UUID,
        plan: NativeMotifSplitPlan,
        attached_parent_revision_id: UUID,
        attached_candidate_membership_id: UUID,
        request_identity: Mapping[str, Any],
        _test_fail_after: str | None = None,
    ) -> NativeMotifSplitResult:
        """Publish the final topology after the candidate is already attached.

        The original atomic split remains untouched.  In this variant only a
        candidate sent to the child is retired/recreated; a parent candidate
        keeps its Stage-A membership identity with no duplicate membership.
        """
        if not isinstance(plan, NativeMotifSplitPlan):
            raise ValueError("a NativeMotifSplitPlan is required")
        if not isinstance(request_identity, Mapping):
            raise ValueError("precommit split request_identity must be a mapping")
        _validate_state(plan.parent_state)
        _validate_state(plan.child_state)
        _validate_mutation_ids(
            idempotency_namespace_id, idempotency_key, motif_identity_namespace_id,
            membership_identity_namespace_id, motif_alias_namespace_id,
            plan.parent_motif_object_id, attached_parent_revision_id,
            attached_candidate_membership_id, *plan.moved_member_object_ids,
            plan.candidate_member_object_id,
        )
        for table, column, value in (
            ("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id),
            ("identity_namespaces", "identity_namespace_id", motif_identity_namespace_id),
            ("identity_namespaces", "identity_namespace_id", membership_identity_namespace_id),
            ("legacy_source_namespaces", "legacy_source_namespace_id", motif_alias_namespace_id),
            ("semantic_scopes", "semantic_scope_id", plan.parent_state.semantic_scope_id),
            ("semantic_scopes", "semantic_scope_id", plan.child_state.semantic_scope_id),
        ):
            self._require_row(table, column, value)
        intent = canonical_intent_text({
            "kind": "NATIVE_I4B2_PRECOMMIT_SPLIT_FINALIZE",
            "request_identity": dict(request_identity),
            "attached_parent_revision_id": str(attached_parent_revision_id),
            "attached_candidate_membership_id": str(attached_candidate_membership_id),
            "final_split": _split_plan_intent(plan),
        })
        return execute_semantic(
            self._connection, idempotency_namespace_id, idempotency_key,
            "NATIVE_I4B2_PRECOMMIT_SPLIT_FINALIZE", intent,
            self._split_result_for_operation,
            lambda tx: self._split_with_attached_member(
                tx, motif_identity_namespace_id, membership_identity_namespace_id,
                motif_alias_namespace_id, plan, attached_parent_revision_id,
                attached_candidate_membership_id, _test_fail_after=_test_fail_after,
            ),
        )

    def recover_precommit_attached_split_finalization(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        request_identity: Mapping[str, Any],
    ) -> NativeMotifSplitResult | None:
        """Read exact stage-B outputs without reconstructing memberships."""
        if not isinstance(request_identity, Mapping):
            raise ValueError("precommit split request_identity must be a mapping")
        row = self._connection.execute(
            "SELECT operation_id,canonical_intent_json FROM operations "
            "WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (_blob(idempotency_namespace_id), idempotency_key),
        ).fetchone()
        if row is None:
            return None
        try:
            intent = json.loads(row[1])
        except (TypeError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("precommit split finalization intent is malformed") from exc
        if (
            not isinstance(intent, Mapping)
            or intent.get("kind") != "NATIVE_I4B2_PRECOMMIT_SPLIT_FINALIZE"
            or intent.get("request_identity") != dict(request_identity)
        ):
            raise SubstrateRevisionConflict("precommit split finalization idempotency intent differs")
        result = self._split_result_for_operation(row[0])
        if result is None:
            raise SubstrateInvariantViolation("precommit split finalization outputs are incomplete")
        return result

    def merge_motifs(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        legacy_source_namespace_id: UUID,
        motif_identity_namespace_id: UUID,
        motif_alias_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        semantic_scope_id: UUID,
        domain_id: str,
        a_runtime_motif_id: str,
        b_runtime_motif_id: str,
        merge_timestamp: int,
        _test_fail_after: str | None = None,
    ) -> NativeMotifMergeResult:
        """Atomically apply the frozen legacy keep/drop merge law.

        This operation owns only native motif truth.  Suggestion decision
        status and diagnostic events deliberately remain in the external M1
        workflow store and are applied by the outer maintenance adapter only
        after this transaction commits.
        """
        _validate_mutation_ids(
            idempotency_namespace_id, idempotency_key, legacy_source_namespace_id, motif_identity_namespace_id, motif_alias_namespace_id,
            membership_identity_namespace_id, semantic_scope_id,
        )
        _nonempty_text("domain_id", domain_id)
        _nonempty_text("a_runtime_motif_id", a_runtime_motif_id)
        _nonempty_text("b_runtime_motif_id", b_runtime_motif_id)
        if not isinstance(merge_timestamp, int):
            raise ValueError("merge_timestamp must be an integer")
        if a_runtime_motif_id == b_runtime_motif_id:
            raise SubstrateInvariantViolation("native motif merge requires two distinct runtime motif IDs")
        for table, column, value in (
            ("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id),
            ("legacy_source_namespaces", "legacy_source_namespace_id", legacy_source_namespace_id),
            ("identity_namespaces", "identity_namespace_id", motif_identity_namespace_id),
            ("identity_namespaces", "identity_namespace_id", membership_identity_namespace_id),
            ("legacy_source_namespaces", "legacy_source_namespace_id", motif_alias_namespace_id),
            ("semantic_scopes", "semantic_scope_id", semantic_scope_id),
        ):
            self._require_row(table, column, value)
        intent = canonical_intent_text({
            "kind": "NATIVE_MOTIF_MERGE",
            "legacy_source_namespace_id": str(legacy_source_namespace_id),
            "motif_identity_namespace_id": str(motif_identity_namespace_id),
            "motif_alias_namespace_id": str(motif_alias_namespace_id),
            "membership_identity_namespace_id": str(membership_identity_namespace_id),
            "semantic_scope_id": str(semantic_scope_id),
            "domain_id": domain_id,
            "a_runtime_motif_id": a_runtime_motif_id,
            "b_runtime_motif_id": b_runtime_motif_id,
            "merge_timestamp": merge_timestamp,
        })
        result = execute_semantic(
            self._connection, idempotency_namespace_id, idempotency_key,
            "NATIVE_MOTIF_MERGE", intent, self._merge_result_for_operation,
            lambda tx: self._merge_motifs(
                tx, legacy_source_namespace_id, motif_identity_namespace_id, motif_alias_namespace_id, membership_identity_namespace_id,
                semantic_scope_id, domain_id, a_runtime_motif_id,
                b_runtime_motif_id, merge_timestamp, _test_fail_after=_test_fail_after,
            ),
        )
        if _test_fail_after == "after_complete_before_response":
            raise RuntimeError("forced native motif merge lost response after semantic completion")
        return result

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
        states = self._connection.execute(
            """
            SELECT h.relationship_id,r.relationship_revision_id,r.revision_ordinal,r.existence_state
              FROM relationships h JOIN relationship_revisions r
                ON r.relationship_id=h.relationship_id
               AND r.relationship_revision_id=h.current_revision_id
               AND r.revision_ordinal=h.current_revision_ordinal
              JOIN relationship_revision_endpoints motif
                ON motif.relationship_revision_id=r.relationship_revision_id
               AND motif.endpoint_ordinal=0 AND motif.endpoint_role='MOTIF'
               AND motif.binding_mode='IDENTITY'
             WHERE h.relationship_kind=? AND motif.object_id=?
            """,
            (MOTIF_MEMBERSHIP_RELATIONSHIP_KIND, _blob(motif_object_id)),
        ).fetchall()
        if any(row[3] not in {"EXISTS", "RETIRED"} for row in states):
            raise SubstrateInvariantViolation("current motif membership has an unknown existence state")
        for relationship_id, revision_id, ordinal, existence_state in states:
            if existence_state == "RETIRED":
                _validate_retired_membership_successor(
                    self._connection, relationship_id, revision_id, ordinal,
                )
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
             WHERE h.relationship_kind=? AND motif.object_id=? AND r.existence_state='EXISTS'
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

    def _publish_migration_zero_member_baseline(
        self,
        tx: SubstrateTx,
        state: MotifState,
        evidence: MigrationZeroMemberMotifBaselineEvidence,
    ) -> NativeMotifMutationResult:
        if self._alias_row(tx, evidence.motif_alias_namespace_id, state.runtime_motif_id) is not None:
            raise SubstrateRevisionConflict("runtime motif ID alias already exists in this namespace")
        transition_id, motif_object_id, motif_revision_id = _new(), _new(), _new()
        self._insert_motif_creation(
            tx,
            motif_object_id,
            motif_revision_id,
            transition_id,
            _motif_object_state(evidence.motif_identity_namespace_id, state),
        )
        tx.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
            (
                _blob(evidence.motif_alias_namespace_id),
                MOTIF_ID_ALIAS_KIND,
                state.runtime_motif_id,
                motif_object_id,
            ),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (
                transition_id,
                tx.operation_id,
                MIGRATION_ZERO_MEMBER_MOTIF_BASELINE_TRANSITION_KIND,
                "NATIVE",
            ),
        )
        tx.execute(
            "INSERT INTO object_revision_effects VALUES (?,?,?,1)",
            (transition_id, motif_object_id, motif_revision_id),
        )
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,
                object_id,object_revision_id,object_revision_ordinal
            ) VALUES (?,?,?,'OBJECT',?,?,1)
            """,
            (
                tx.operation_id,
                0,
                MIGRATION_ZERO_MEMBER_MOTIF_BASELINE_OUTPUT_ROLE,
                motif_object_id,
                motif_revision_id,
            ),
        )
        tx.execute(
            "UPDATE objects SET current_revision_id=?,current_revision_ordinal=1 WHERE object_id=?",
            (motif_revision_id, motif_object_id),
        )
        tx.transitions.append(transition_id)
        tx.published.append((motif_object_id, motif_revision_id, 1))
        result = self._zero_member_baseline_result_for_operation(tx.operation_id)
        if result is None:
            raise SubstrateInvariantViolation("migration zero-member baseline was not durably published")
        return result

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
        *,
        transition_kind: str = "NATIVE_MOTIF_ADD_MEMBER",
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
            transition_kind,
            _blob(motif_object_id),
            motif_revision_id,
            ordinal,
            membership_id,
            membership_revision_id,
            1,
        )

    def _split_with_attached_member(
        self,
        tx: SubstrateTx,
        motif_identity_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        motif_alias_namespace_id: UUID,
        plan: NativeMotifSplitPlan,
        attached_parent_revision_id: UUID,
        attached_candidate_membership_id: UUID,
        *,
        _test_fail_after: str | None,
    ) -> NativeMotifSplitResult:
        """The stage-B variant of the atomic splitter for an attached EID."""
        current = self._assert_current_motif(
            tx, plan.parent_motif_object_id, attached_parent_revision_id, plan.parent_state,
        )
        self._assert_alias_target(
            tx, motif_alias_namespace_id, plan.parent_state.runtime_motif_id,
            plan.parent_motif_object_id,
        )
        if self._alias_row(tx, motif_alias_namespace_id, plan.child_state.runtime_motif_id) is not None:
            raise SubstrateRevisionConflict("split child runtime motif ID alias already exists")
        if plan.parent_state.semantic_scope_id != plan.child_state.semantic_scope_id:
            raise SubstrateInvariantViolation("split child changes the parent semantic scope")
        moved = tuple(
            self._current_active_membership(tx, plan.parent_motif_object_id, member_id)
            for member_id in plan.moved_member_object_ids
        )
        candidate = self._current_active_membership(
            tx, plan.parent_motif_object_id, plan.candidate_member_object_id,
        )
        if UUID(bytes=candidate[0]) != attached_candidate_membership_id:
            raise SubstrateRevisionConflict("precommit split candidate membership differs from stage A")

        transition_id = _new()
        parent_revision_id = _new()
        parent_ordinal = current[1] + 1
        self._insert_motif_successor(
            tx, plan.parent_motif_object_id, parent_revision_id, parent_ordinal,
            attached_parent_revision_id, current[1],
            _motif_object_state(UUID(bytes=current[2]), plan.parent_state),
        )
        if _test_fail_after == "parent_successor":
            raise RuntimeError("forced native precommit split failure after parent successor")

        child_object_id, child_revision_id = _new(), _new()
        self._insert_motif_creation(
            tx, child_object_id, child_revision_id, transition_id,
            _motif_object_state(motif_identity_namespace_id, plan.child_state),
        )
        tx.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
            (_blob(motif_alias_namespace_id), MOTIF_ID_ALIAS_KIND,
             plan.child_state.runtime_motif_id, child_object_id),
        )
        if _test_fail_after == "child_object":
            raise RuntimeError("forced native precommit split failure after child object")

        retired: list[tuple[bytes, bytes, int]] = []
        for index, membership in enumerate(moved):
            revision_id = _new()
            self._relationships._revision(
                tx, membership[0], revision_id, membership[2] + 1, "NATIVE_ORDINARY",
                membership[1], membership[2],
                self._retired_membership_state(tx, membership[0], membership[1], membership[2]),
            )
            retired.append((membership[0], revision_id, membership[2] + 1))
            if index == 0 and _test_fail_after == "first_retirement":
                raise RuntimeError("forced native precommit split failure after first retirement")

        child_members: list[tuple[bytes, bytes, int]] = []
        for _relationship, _revision, _ordinal, member_id, member_scope in moved:
            membership_id, membership_revision_id = _new(), _new()
            self._insert_membership(
                tx, membership_id, membership_revision_id, transition_id,
                _membership_state(
                    membership_identity_namespace_id, plan.child_state.semantic_scope_id,
                    UUID(bytes=child_object_id), UUID(bytes=member_scope), UUID(bytes=member_id),
                ),
            )
            child_members.append((membership_id, membership_revision_id, 1))

        parent_candidate_membership: tuple[bytes, bytes, int] | None = None
        if plan.candidate_in_child:
            candidate_revision_id = _new()
            self._relationships._revision(
                tx, candidate[0], candidate_revision_id, candidate[2] + 1, "NATIVE_ORDINARY",
                candidate[1], candidate[2],
                self._retired_membership_state(tx, candidate[0], candidate[1], candidate[2]),
            )
            retired.append((candidate[0], candidate_revision_id, candidate[2] + 1))
            membership_id, membership_revision_id = _new(), _new()
            self._insert_membership(
                tx, membership_id, membership_revision_id, transition_id,
                _membership_state(
                    membership_identity_namespace_id, plan.child_state.semantic_scope_id,
                    UUID(bytes=child_object_id), UUID(bytes=candidate[4]), plan.candidate_member_object_id,
                ),
            )
            child_members.append((membership_id, membership_revision_id, 1))
        else:
            # Stage A already created this parent membership.  Reusing that
            # relationship identity is the key distinction from atomic split.
            parent_candidate_membership = (candidate[0], candidate[1], candidate[2])
        if _test_fail_after == "child_memberships":
            raise RuntimeError("forced native precommit split failure after child memberships")
        if _test_fail_after == "before_current_pointer_publication":
            raise RuntimeError("forced native precommit split failure before current-pointer publication")

        self._publish_split(
            tx, transition_id, _blob(plan.parent_motif_object_id), parent_revision_id,
            parent_ordinal, child_object_id, child_revision_id, retired, child_members,
            None,
            transition_kind="NATIVE_I4B2_PRECOMMIT_SPLIT_FINALIZE",
        )
        self._validate_split_publication(
            tx, transition_id, _blob(plan.parent_motif_object_id), parent_revision_id,
            parent_ordinal, child_object_id, child_revision_id, retired, child_members, None,
        )
        return NativeMotifSplitResult(
            plan.parent_motif_object_id, UUID(bytes=parent_revision_id), parent_ordinal,
            UUID(bytes=child_object_id), UUID(bytes=child_revision_id),
            plan.child_state.runtime_motif_id,
            tuple(UUID(bytes=item[0]) for item in retired),
            tuple(UUID(bytes=item[0]) for item in child_members),
            UUID(bytes=candidate[0]) if not plan.candidate_in_child else None,
            UUID(bytes=transition_id), UUID(bytes=tx.operation_id),
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

    def _split_with_member(
        self,
        tx: SubstrateTx,
        motif_identity_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        motif_alias_namespace_id: UUID,
        plan: NativeMotifSplitPlan,
        *,
        _test_fail_after: str | None,
    ) -> NativeMotifSplitResult:
        current = self._assert_current_motif(
            tx, plan.parent_motif_object_id, plan.expected_parent_revision_id, plan.parent_state,
        )
        self._assert_alias_target(
            tx, motif_alias_namespace_id, plan.parent_state.runtime_motif_id,
            plan.parent_motif_object_id,
        )
        if self._alias_row(tx, motif_alias_namespace_id, plan.child_state.runtime_motif_id) is not None:
            raise SubstrateRevisionConflict("split child runtime motif ID alias already exists")
        if plan.parent_state.semantic_scope_id != plan.child_state.semantic_scope_id:
            raise SubstrateInvariantViolation("split child changes the parent semantic scope")
        moved = tuple(
            self._current_active_membership(tx, plan.parent_motif_object_id, member_id)
            for member_id in plan.moved_member_object_ids
        )
        candidate_scope = self._require_compatible_member(tx, plan.candidate_member_object_id)
        if self._has_current_membership(tx, plan.parent_motif_object_id, plan.candidate_member_object_id):
            raise SubstrateRevisionConflict("candidate is already a current parent motif member")

        transition_id = _new()
        parent_revision_id = _new()
        parent_ordinal = current[1] + 1
        self._insert_motif_successor(
            tx, plan.parent_motif_object_id, parent_revision_id, parent_ordinal,
            plan.expected_parent_revision_id, current[1],
            _motif_object_state(UUID(bytes=current[2]), plan.parent_state),
        )
        if _test_fail_after == "parent_successor":
            raise RuntimeError("forced native motif split failure after parent successor")

        child_object_id, child_revision_id = _new(), _new()
        self._insert_motif_creation(
            tx, child_object_id, child_revision_id, transition_id,
            _motif_object_state(motif_identity_namespace_id, plan.child_state),
        )
        tx.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
            (_blob(motif_alias_namespace_id), MOTIF_ID_ALIAS_KIND,
             plan.child_state.runtime_motif_id, child_object_id),
        )
        if _test_fail_after == "child_object":
            raise RuntimeError("forced native motif split failure after child object")

        retired: list[tuple[bytes, bytes, int]] = []
        for index, membership in enumerate(moved):
            revision_id = _new()
            retirement_state = self._retired_membership_state(tx, membership[0], membership[1], membership[2])
            self._relationships._revision(
                tx, membership[0], revision_id, membership[2] + 1, "NATIVE_ORDINARY",
                membership[1], membership[2], retirement_state,
            )
            retired.append((membership[0], revision_id, membership[2] + 1))
            if index == 0 and _test_fail_after == "first_retirement":
                raise RuntimeError("forced native motif split failure after first retirement")

        child_members: list[tuple[bytes, bytes, int]] = []
        for _relationship, _revision, _ordinal, member_id, member_scope in moved:
            membership_id, membership_revision_id = _new(), _new()
            state = _membership_state(
                membership_identity_namespace_id, plan.child_state.semantic_scope_id,
                UUID(bytes=child_object_id), UUID(bytes=member_scope), UUID(bytes=member_id),
            )
            self._insert_membership(tx, membership_id, membership_revision_id, transition_id, state)
            child_members.append((membership_id, membership_revision_id, 1))
        candidate_parent_membership: tuple[bytes, bytes, int] | None = None
        if plan.candidate_in_child:
            membership_id, membership_revision_id = _new(), _new()
            state = _membership_state(
                membership_identity_namespace_id, plan.child_state.semantic_scope_id,
                UUID(bytes=child_object_id), candidate_scope, plan.candidate_member_object_id,
            )
            self._insert_membership(tx, membership_id, membership_revision_id, transition_id, state)
            child_members.append((membership_id, membership_revision_id, 1))
        else:
            membership_id, membership_revision_id = _new(), _new()
            state = _membership_state(
                membership_identity_namespace_id, plan.parent_state.semantic_scope_id,
                plan.parent_motif_object_id, candidate_scope, plan.candidate_member_object_id,
            )
            self._insert_membership(tx, membership_id, membership_revision_id, transition_id, state)
            candidate_parent_membership = (membership_id, membership_revision_id, 1)
        if _test_fail_after == "child_memberships":
            raise RuntimeError("forced native motif split failure after child memberships")
        if _test_fail_after == "before_current_pointer_publication":
            raise RuntimeError("forced native motif split failure before current-pointer publication")

        self._publish_split(
            tx, transition_id, _blob(plan.parent_motif_object_id), parent_revision_id,
            parent_ordinal, child_object_id, child_revision_id, retired, child_members,
            candidate_parent_membership,
        )
        self._validate_split_publication(
            tx, transition_id, _blob(plan.parent_motif_object_id), parent_revision_id,
            parent_ordinal, child_object_id, child_revision_id, retired, child_members,
            candidate_parent_membership,
        )
        return NativeMotifSplitResult(
            plan.parent_motif_object_id, UUID(bytes=parent_revision_id), parent_ordinal,
            UUID(bytes=child_object_id), UUID(bytes=child_revision_id),
            plan.child_state.runtime_motif_id,
            tuple(UUID(bytes=item[0]) for item in retired),
            tuple(UUID(bytes=item[0]) for item in child_members),
            UUID(bytes=candidate_parent_membership[0]) if candidate_parent_membership else None,
            UUID(bytes=transition_id), UUID(bytes=tx.operation_id),
        )

    def _merge_motifs(
        self,
        tx: SubstrateTx,
        legacy_source_namespace_id: UUID,
        motif_identity_namespace_id: UUID,
        motif_alias_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        semantic_scope_id: UUID,
        domain_id: str,
        a_runtime_motif_id: str,
        b_runtime_motif_id: str,
        merge_timestamp: int,
        *,
        _test_fail_after: str | None,
    ) -> NativeMotifMergeResult:
        a_id = self._alias_row(tx, motif_alias_namespace_id, a_runtime_motif_id)
        b_id = self._alias_row(tx, motif_alias_namespace_id, b_runtime_motif_id)
        if a_id is None or b_id is None:
            raise SubstrateObjectNotFound("native motif merge alias was not found")
        if a_id == b_id:
            raise SubstrateInvariantViolation("native motif merge aliases resolve to one object")
        a = self._current_live_motif_for_merge(tx, UUID(bytes=a_id), semantic_scope_id, domain_id)
        b = self._current_live_motif_for_merge(tx, UUID(bytes=b_id), semantic_scope_id, domain_id)
        if a[3] != _blob(motif_identity_namespace_id) or b[3] != _blob(motif_identity_namespace_id):
            raise SubstrateInvariantViolation("native motif merge does not match the claimed motif identity namespace")
        keep, drop = (a, b) if a[4].strength >= b[4].strength else (b, a)
        keep_id, keep_revision, keep_ordinal, keep_identity, keep_state = keep
        drop_id, drop_revision, drop_ordinal, drop_identity, drop_state = drop
        keep_uuid = UUID(bytes=keep_id)
        drop_uuid = UUID(bytes=drop_id)

        keep_members = self._current_active_memberships(tx, keep_uuid)
        drop_members = self._current_active_memberships(tx, drop_uuid)
        keep_by_member = {item[3]: item for item in keep_members}
        drop_by_member = {item[3]: item for item in drop_members}
        if len(keep_by_member) != len(keep_members) or len(drop_by_member) != len(drop_members):
            raise SubstrateInvariantViolation("native motif merge has duplicate current member identities")
        final_member_ids = set(keep_by_member) | set(drop_by_member)
        if not final_member_ids:
            raise SubstrateInvariantViolation("native motif merge cannot produce an empty survivor")
        # The claimed source namespace is not merely an operation-key label:
        # every projected member must have its durable legacy EID there before
        # any successor revision is created.
        for member_id in final_member_ids:
            self._legacy_eid_sort_key(tx, legacy_source_namespace_id, member_id)

        keep_successor_state = _merged_keep_state(keep_state, drop_state, merge_timestamp)
        transition_id, keep_successor_id, drop_successor_id = _new(), _new(), _new()
        keep_successor_ordinal = keep_ordinal + 1
        drop_successor_ordinal = drop_ordinal + 1
        self._insert_motif_successor(
            tx, keep_uuid, keep_successor_id, keep_successor_ordinal,
            UUID(bytes=keep_revision), keep_ordinal,
            _motif_object_state(UUID(bytes=keep_identity), keep_successor_state),
        )
        if _test_fail_after == "keep_successor":
            raise RuntimeError("forced native motif merge failure after keep successor")
        self._insert_motif_successor(
            tx, drop_uuid, drop_successor_id, drop_successor_ordinal,
            UUID(bytes=drop_revision), drop_ordinal,
            _retired_motif_object_state(UUID(bytes=drop_identity), drop_state),
        )
        if _test_fail_after == "drop_successor":
            raise RuntimeError("forced native motif merge failure after drop successor")

        retired: list[tuple[bytes, bytes, int]] = []
        for membership in drop_members:
            relationship_id, revision_id, ordinal, _member_id, _member_scope = membership
            successor_id = _new()
            self._relationships._revision(
                tx, relationship_id, successor_id, ordinal + 1, "NATIVE_ORDINARY",
                revision_id, ordinal,
                self._retired_membership_state(tx, relationship_id, revision_id, ordinal),
            )
            retired.append((relationship_id, successor_id, ordinal + 1))
        if _test_fail_after == "retire_memberships":
            raise RuntimeError("forced native motif merge failure after membership retirement")

        created: list[tuple[bytes, bytes, int]] = []
        for member_id in sorted(set(drop_by_member) - set(keep_by_member), key=lambda value: self._legacy_eid_sort_key(tx, legacy_source_namespace_id, value)):
            _old_relationship, _old_revision, _old_ordinal, _old_member, member_scope = drop_by_member[member_id]
            relationship_id, revision_id = _new(), _new()
            self._insert_membership(
                tx, relationship_id, revision_id, transition_id,
                _membership_state(
                    membership_identity_namespace_id, semantic_scope_id, keep_uuid,
                    UUID(bytes=member_scope), UUID(bytes=member_id),
                ),
            )
            created.append((relationship_id, revision_id, 1))
        if _test_fail_after == "before_current_pointer_publication":
            raise RuntimeError("forced native motif merge failure before current-pointer publication")

        self._publish_merge(
            tx, transition_id,
            keep_id, keep_successor_id, keep_successor_ordinal,
            drop_id, drop_successor_id, drop_successor_ordinal,
            retired, created,
        )
        return NativeMotifMergeResult(
            keep_uuid, UUID(bytes=keep_successor_id), keep_successor_ordinal,
            keep_state.runtime_motif_id,
            drop_uuid, UUID(bytes=drop_successor_id), drop_successor_ordinal,
            drop_state.runtime_motif_id,
            tuple(UUID(bytes=item[0]) for item in retired),
            tuple(UUID(bytes=item[0]) for item in created),
            UUID(bytes=transition_id), UUID(bytes=tx.operation_id),
        )

    def _publish_merge(
        self,
        tx: SubstrateTx,
        transition_id: bytes,
        keep_id: bytes,
        keep_revision_id: bytes,
        keep_ordinal: int,
        drop_id: bytes,
        drop_revision_id: bytes,
        drop_ordinal: int,
        retired: list[tuple[bytes, bytes, int]],
        created: list[tuple[bytes, bytes, int]],
    ) -> None:
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (transition_id, tx.operation_id, "NATIVE_MOTIF_MERGE", "NATIVE"),
        )
        for object_id, revision_id, ordinal in (
            (keep_id, keep_revision_id, keep_ordinal),
            (drop_id, drop_revision_id, drop_ordinal),
        ):
            tx.execute(
                "INSERT INTO object_revision_effects VALUES (?,?,?,?)",
                (transition_id, object_id, revision_id, ordinal),
            )
            tx.execute(
                "UPDATE objects SET current_revision_id=?,current_revision_ordinal=? WHERE object_id=?",
                (revision_id, ordinal, object_id),
            )
        output_ordinal = 0
        for role, object_id, revision_id, ordinal in (
            ("MERGE_KEEP_MOTIF", keep_id, keep_revision_id, keep_ordinal),
            ("RETIRED_DROP_MOTIF", drop_id, drop_revision_id, drop_ordinal),
        ):
            tx.execute(
                "INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,object_id,object_revision_id,object_revision_ordinal) VALUES (?,?,?,?,?,?,?)",
                (tx.operation_id, output_ordinal, role, "OBJECT", object_id, revision_id, ordinal),
            )
            output_ordinal += 1
        for role, rows in (("RETIRED_DROP_MEMBERSHIP", retired), ("MERGE_KEEP_MEMBERSHIP", created)):
            for relationship_id, revision_id, ordinal in rows:
                tx.execute(
                    "INSERT INTO relationship_revision_effects VALUES (?,?,?,?)",
                    (transition_id, relationship_id, revision_id, ordinal),
                )
                tx.execute(
                    "INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,relationship_id,relationship_revision_id,relationship_revision_ordinal) VALUES (?,?,?,?,?,?,?)",
                    (tx.operation_id, output_ordinal, role, "RELATIONSHIP", relationship_id, revision_id, ordinal),
                )
                tx.execute(
                    "UPDATE relationships SET current_revision_id=?,current_revision_ordinal=? WHERE relationship_id=?",
                    (revision_id, ordinal, relationship_id),
                )
                output_ordinal += 1
        tx.transitions.append(transition_id)
        tx.published.extend(((keep_id, keep_revision_id, keep_ordinal), (drop_id, drop_revision_id, drop_ordinal)))
        tx.relationship_published.extend(retired)
        tx.relationship_published.extend(created)

    def _current_live_motif_for_merge(
        self, tx: SubstrateTx, motif_id: UUID, semantic_scope_id: UUID, domain_id: str,
    ) -> tuple[bytes, bytes, int, bytes, MotifState]:
        row = tx.execute(
            """
            SELECT o.object_id,o.current_revision_id,o.current_revision_ordinal,
                   o.identity_namespace_id,r.effective_semantic_scope_id,r.existence_state,
                   r.payload_format,r.payload_text,o.object_kind
              FROM objects o JOIN object_revisions r
                ON r.object_id=o.object_id
               AND r.object_revision_id=o.current_revision_id
               AND r.revision_ordinal=o.current_revision_ordinal
             WHERE o.object_id=?
            """,
            (_blob(motif_id),),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("native motif was not found")
        if row[8] != DERIVED_MOTIF_OBJECT_KIND or row[5] != "EXISTS":
            raise SubstrateObjectNotFound("native motif is not current live truth")
        if row[4] != _blob(semantic_scope_id):
            raise SubstrateInvariantViolation("native motif merge crosses semantic scopes")
        if row[6] != "JSON" or row[7] is None:
            raise SubstrateInvariantViolation("native motif current state is not JSON")
        state = _state_from_payload(semantic_scope_id, row[7])
        if state.semantic_scope_id != semantic_scope_id or state.domain_id != domain_id:
            raise SubstrateInvariantViolation("native motif merge crosses the claimed domain")
        return row[0], row[1], row[2], row[3], state

    def _current_active_memberships(
        self, tx: SubstrateTx, motif_id: UUID,
    ) -> tuple[tuple[bytes, bytes, int, bytes, bytes], ...]:
        rows = tx.execute(
            """
            SELECT h.relationship_id,r.relationship_revision_id,r.revision_ordinal,
                   member.object_id,member.endpoint_semantic_scope_id
              FROM relationships h JOIN relationship_revisions r
                ON r.relationship_id=h.relationship_id
               AND r.relationship_revision_id=h.current_revision_id
               AND r.revision_ordinal=h.current_revision_ordinal
              JOIN relationship_revision_endpoints motif ON motif.relationship_revision_id=r.relationship_revision_id
               AND motif.endpoint_ordinal=0 AND motif.endpoint_role='MOTIF' AND motif.binding_mode='IDENTITY'
              JOIN relationship_revision_endpoints member ON member.relationship_revision_id=r.relationship_revision_id
               AND member.endpoint_ordinal=1 AND member.endpoint_role='MEMBER' AND member.binding_mode='IDENTITY'
             WHERE h.relationship_kind=? AND r.existence_state='EXISTS' AND motif.object_id=?
            """,
            (MOTIF_MEMBERSHIP_RELATIONSHIP_KIND, _blob(motif_id)),
        ).fetchall()
        if not rows:
            raise SubstrateInvariantViolation("native motif merge requires current memberships")
        for _relationship_id, _revision_id, _ordinal, member_id, _member_scope in rows:
            self._require_compatible_member(tx, UUID(bytes=member_id))
        return tuple(rows)

    def _legacy_eid_sort_key(
        self, tx: SubstrateTx, legacy_source_namespace_id: UUID, member_id: bytes,
    ) -> tuple[int, str, bytes]:
        rows = tx.execute(
            "SELECT alias_value FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND object_id=? AND alias_kind='EID' ORDER BY alias_value",
            (_blob(legacy_source_namespace_id), member_id),
        ).fetchall()
        if not rows:
            raise SubstrateInvariantViolation("native motif member has no legacy EID alias")
        value = rows[0][0]
        try:
            return int(value), value, member_id
        except (TypeError, ValueError) as error:
            raise SubstrateInvariantViolation("native motif member EID alias is not numeric") from error

    def _publish_split(
        self, tx: SubstrateTx, transition_id: bytes, parent_id: bytes,
        parent_revision_id: bytes, parent_ordinal: int, child_id: bytes,
        child_revision_id: bytes, retired: list[tuple[bytes, bytes, int]],
        child_members: list[tuple[bytes, bytes, int]],
        candidate_parent_membership: tuple[bytes, bytes, int] | None,
        *,
        transition_kind: str = "NATIVE_MOTIF_SPLIT_WITH_MEMBER",
    ) -> None:
        tx.execute("INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
                   (transition_id, tx.operation_id, transition_kind, "NATIVE"))
        for object_id, revision_id, ordinal in ((parent_id, parent_revision_id, parent_ordinal), (child_id, child_revision_id, 1)):
            tx.execute("INSERT INTO object_revision_effects VALUES (?,?,?,?)", (transition_id, object_id, revision_id, ordinal))
        tx.execute("UPDATE objects SET current_revision_id=?,current_revision_ordinal=? WHERE object_id=?", (parent_revision_id, parent_ordinal, parent_id))
        ordinal = 0
        for role, object_id, revision_id, object_ordinal in (
            ("SPLIT_PARENT_MOTIF", parent_id, parent_revision_id, parent_ordinal),
            ("SPLIT_CHILD_MOTIF", child_id, child_revision_id, 1),
        ):
            tx.execute("INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,object_id,object_revision_id,object_revision_ordinal) VALUES (?,?,?,?,?,?,?)", (tx.operation_id, ordinal, role, "OBJECT", object_id, revision_id, object_ordinal))
            ordinal += 1
        for role, values in (("RETIRED_PARENT_MEMBERSHIP", retired), ("CHILD_MOTIF_MEMBERSHIP", child_members), ("PARENT_MOTIF_MEMBERSHIP", [] if candidate_parent_membership is None else [candidate_parent_membership])):
            for relationship_id, revision_id, relationship_ordinal in values:
                tx.execute("INSERT INTO relationship_revision_effects VALUES (?,?,?,?)", (transition_id, relationship_id, revision_id, relationship_ordinal))
                tx.execute("INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,relationship_id,relationship_revision_id,relationship_revision_ordinal) VALUES (?,?,?,?,?,?,?)", (tx.operation_id, ordinal, role, "RELATIONSHIP", relationship_id, revision_id, relationship_ordinal))
                tx.execute("UPDATE relationships SET current_revision_id=?,current_revision_ordinal=? WHERE relationship_id=?", (revision_id, relationship_ordinal, relationship_id))
                ordinal += 1
        tx.transitions.append(transition_id)
        tx.published.extend(((parent_id, parent_revision_id, parent_ordinal), (child_id, child_revision_id, 1)))
        tx.relationship_published.extend(retired)
        tx.relationship_published.extend(child_members)
        if candidate_parent_membership is not None:
            tx.relationship_published.append(candidate_parent_membership)

    def _validate_split_publication(
        self, tx: SubstrateTx, transition_id: bytes, parent_id: bytes,
        parent_revision_id: bytes, parent_ordinal: int, child_id: bytes,
        child_revision_id: bytes, retired: list[tuple[bytes, bytes, int]],
        child_members: list[tuple[bytes, bytes, int]],
        candidate_parent_membership: tuple[bytes, bytes, int] | None,
    ) -> None:
        for object_id, revision_id, ordinal in (
            (parent_id, parent_revision_id, parent_ordinal), (child_id, child_revision_id, 1),
        ):
            if tx.execute(
                "SELECT 1 FROM object_revision_effects WHERE transition_id=? AND object_id=? AND object_revision_id=? AND object_revision_ordinal=?",
                (transition_id, object_id, revision_id, ordinal),
            ).fetchone() is None:
                raise SubstrateInvariantViolation("native split omits a required object revision effect")
        for relationship_id, revision_id, ordinal in [
            *retired, *child_members,
            *(() if candidate_parent_membership is None else (candidate_parent_membership,)),
        ]:
            if tx.execute(
                "SELECT 1 FROM relationship_revision_effects WHERE transition_id=? AND relationship_id=? AND relationship_revision_id=? AND relationship_revision_ordinal=?",
                (transition_id, relationship_id, revision_id, ordinal),
            ).fetchone() is None:
                raise SubstrateInvariantViolation("native split omits a required relationship revision effect")
        outputs = tx.execute(
            "SELECT output_ordinal,output_role,output_kind FROM operation_outputs WHERE operation_id=? ORDER BY output_ordinal",
            (tx.operation_id,),
        ).fetchall()
        if outputs[:2] != [
            (0, "SPLIT_PARENT_MOTIF", "OBJECT"), (1, "SPLIT_CHILD_MOTIF", "OBJECT"),
        ]:
            raise SubstrateInvariantViolation("native split durable outputs do not match its publication")

    def _current_active_membership(
        self, tx: SubstrateTx, motif_id: UUID, member_id: UUID,
    ) -> tuple[bytes, bytes, int, bytes, bytes]:
        rows = tx.execute(
            """
            SELECT h.relationship_id,r.relationship_revision_id,r.revision_ordinal,
                   member.object_id,member.endpoint_semantic_scope_id
              FROM relationships h JOIN relationship_revisions r
                ON r.relationship_id=h.relationship_id
               AND r.relationship_revision_id=h.current_revision_id
               AND r.revision_ordinal=h.current_revision_ordinal
              JOIN relationship_revision_endpoints motif ON motif.relationship_revision_id=r.relationship_revision_id
               AND motif.endpoint_ordinal=0 AND motif.endpoint_role='MOTIF' AND motif.binding_mode='IDENTITY'
              JOIN relationship_revision_endpoints member ON member.relationship_revision_id=r.relationship_revision_id
               AND member.endpoint_ordinal=1 AND member.endpoint_role='MEMBER' AND member.binding_mode='IDENTITY'
             WHERE h.relationship_kind=? AND r.existence_state='EXISTS' AND motif.object_id=? AND member.object_id=?
            """, (MOTIF_MEMBERSHIP_RELATIONSHIP_KIND, _blob(motif_id), _blob(member_id)),
        ).fetchall()
        if len(rows) != 1:
            raise SubstrateInvariantViolation("split moved member is not exactly one current active parent membership")
        return rows[0]

    def _retired_membership_state(
        self, tx: SubstrateTx, relationship_id: bytes, revision_id: bytes, ordinal: int,
    ) -> RelationshipState:
        row = tx.execute(
            """
            SELECT h.identity_namespace_id,h.relationship_kind,r.effective_semantic_scope_id,
                   r.lifecycle_state,r.lifecycle_authoritative,r.governance_state,
                   r.authority_category,r.payload_format,r.payload_text,r.existence_state
              FROM relationships h JOIN relationship_revisions r
                ON r.relationship_id=h.relationship_id
             WHERE h.relationship_id=? AND r.relationship_revision_id=? AND r.revision_ordinal=?
            """, (relationship_id, revision_id, ordinal),
        ).fetchone()
        if row is None or row[1] != MOTIF_MEMBERSHIP_RELATIONSHIP_KIND or row[9] != "EXISTS":
            raise SubstrateInvariantViolation("split retirement requires a current active MOTIF_MEMBERSHIP")
        endpoints = tuple(
            Endpoint(index, role, UUID(bytes=scope), UUID(bytes=object_id), binding, UUID(bytes=bound) if bound else None)
            for index, role, scope, object_id, binding, bound in tx.execute(
                "SELECT endpoint_ordinal,endpoint_role,endpoint_semantic_scope_id,object_id,binding_mode,bound_object_revision_id FROM relationship_revision_endpoints WHERE relationship_revision_id=? ORDER BY endpoint_ordinal", (revision_id,)
            )
        )
        payload: str | dict[str, Any] | None
        if row[7] == "NONE":
            payload = None
        elif row[7] == "TEXT":
            payload = row[8]
        elif row[7] == "JSON":
            payload = json.loads(row[8])
        else:
            raise SubstrateInvariantViolation("split retirement has an unsupported membership payload format")
        return RelationshipState(
            UUID(bytes=row[0]), UUID(bytes=row[2]), row[1], "RETIRED", row[3], bool(row[4]),
            row[5], row[6], endpoints, payload, row[7],
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
             WHERE h.relationship_kind=? AND r.existence_state='EXISTS' AND motif.object_id=? AND member.object_id=?
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
        if len(rows) != 2 or motif[2] not in {
            "NATIVE_MOTIF_CREATE_WITH_MEMBER",
            "NATIVE_MOTIF_ADD_MEMBER",
            "NATIVE_I4B2_PRECOMMIT_SPLIT_ATTACH",
        }:
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

    def _zero_member_baseline_result_for_operation(
        self, operation_id: bytes,
    ) -> NativeMotifMutationResult | None:
        """Recover only the exact one-object B4C publication topology."""
        rows = self._connection.execute(
            """
            SELECT t.transition_id,t.transition_kind,t.origin_kind,o.output_ordinal,
                   o.output_role,o.output_kind,o.object_id,o.object_revision_id,
                   o.object_revision_ordinal,o.relationship_id,o.relationship_revision_id,
                   o.relationship_revision_ordinal
              FROM semantic_transitions t
              JOIN operation_outputs o ON o.operation_id=t.operation_id
             WHERE t.operation_id=?
             ORDER BY o.output_ordinal
            """,
            (operation_id,),
        ).fetchall()
        if len(rows) != 1:
            return None
        row = rows[0]
        if row[1:9] != (
            MIGRATION_ZERO_MEMBER_MOTIF_BASELINE_TRANSITION_KIND,
            "NATIVE",
            0,
            MIGRATION_ZERO_MEMBER_MOTIF_BASELINE_OUTPUT_ROLE,
            "OBJECT",
            row[6],
            row[7],
            1,
        ) or row[6] is None or row[7] is None or any(value is not None for value in row[9:]):
            return None
        effect = self._connection.execute(
            """
            SELECT object_revision_id,object_revision_ordinal
              FROM object_revision_effects
             WHERE transition_id=? AND object_id=?
            """,
            (row[0], row[6]),
        ).fetchall()
        if effect != [(row[7], 1)]:
            return None
        if self._connection.execute(
            "SELECT 1 FROM relationship_revision_effects WHERE transition_id=?",
            (row[0],),
        ).fetchone() is not None:
            return None
        if self._connection.execute(
            "SELECT 1 FROM relationships WHERE creating_transition_id=?",
            (row[0],),
        ).fetchone() is not None:
            return None
        return NativeMotifMutationResult(
            UUID(bytes=row[6]),
            UUID(bytes=row[7]),
            1,
            UUID(bytes=row[0]),
            UUID(bytes=operation_id),
        )

    def _split_result_for_operation(self, operation_id: bytes) -> NativeMotifSplitResult | None:
        rows = self._connection.execute(
            """
            SELECT t.transition_id,t.operation_id,o.output_ordinal,o.output_role,o.output_kind,
                   o.object_id,o.object_revision_id,o.object_revision_ordinal,
                   o.relationship_id,o.relationship_revision_id,o.relationship_revision_ordinal
              FROM semantic_transitions t JOIN operation_outputs o ON o.operation_id=t.operation_id
             WHERE t.operation_id=? AND t.transition_kind IN (
                   'NATIVE_MOTIF_SPLIT_WITH_MEMBER',
                   'NATIVE_I4B2_PRECOMMIT_SPLIT_FINALIZE'
             )
             ORDER BY o.output_ordinal
            """, (operation_id,),
        ).fetchall()
        if len(rows) < 4 or [row[3:5] for row in rows[:2]] != [
            ("SPLIT_PARENT_MOTIF", "OBJECT"), ("SPLIT_CHILD_MOTIF", "OBJECT"),
        ]:
            return None
        parent, child = rows[:2]
        retired: list[UUID] = []
        child_members: list[UUID] = []
        candidate_parent: UUID | None = None
        for row in rows[2:]:
            if row[4] != "RELATIONSHIP" or row[8] is None or row[9] is None:
                return None
            if row[3] == "RETIRED_PARENT_MEMBERSHIP":
                retired.append(UUID(bytes=row[8]))
            elif row[3] == "CHILD_MOTIF_MEMBERSHIP":
                child_members.append(UUID(bytes=row[8]))
            elif row[3] == "PARENT_MOTIF_MEMBERSHIP" and candidate_parent is None:
                candidate_parent = UUID(bytes=row[8])
            else:
                return None
        if not retired or not child_members:
            return None
        alias = self._connection.execute(
            "SELECT alias_value FROM legacy_object_aliases WHERE object_id=? AND alias_kind=?",
            (child[5], MOTIF_ID_ALIAS_KIND),
        ).fetchall()
        if len(alias) != 1:
            raise SubstrateInvariantViolation("split child motif alias is incomplete")
        return NativeMotifSplitResult(
            UUID(bytes=parent[5]), UUID(bytes=parent[6]), parent[7],
            UUID(bytes=child[5]), UUID(bytes=child[6]), alias[0][0],
            tuple(retired), tuple(child_members), candidate_parent,
            UUID(bytes=parent[0]), UUID(bytes=parent[1]),
        )

    def _merge_result_for_operation(self, operation_id: bytes) -> NativeMotifMergeResult | None:
        rows = self._connection.execute(
            """
            SELECT t.transition_id,t.operation_id,o.output_ordinal,o.output_role,o.output_kind,
                   o.object_id,o.object_revision_id,o.object_revision_ordinal,
                   o.relationship_id,o.relationship_revision_id,o.relationship_revision_ordinal
              FROM semantic_transitions t JOIN operation_outputs o ON o.operation_id=t.operation_id
             WHERE t.operation_id=? AND t.transition_kind='NATIVE_MOTIF_MERGE'
             ORDER BY o.output_ordinal
            """,
            (operation_id,),
        ).fetchall()
        if len(rows) < 3 or [row[3:5] for row in rows[:2]] != [
            ("MERGE_KEEP_MOTIF", "OBJECT"), ("RETIRED_DROP_MOTIF", "OBJECT"),
        ]:
            return None
        keep, drop = rows[:2]
        retired: list[UUID] = []
        created: list[UUID] = []
        for row in rows[2:]:
            if row[4] != "RELATIONSHIP" or row[8] is None or row[9] is None:
                return None
            if row[3] == "RETIRED_DROP_MEMBERSHIP":
                retired.append(UUID(bytes=row[8]))
            elif row[3] == "MERGE_KEEP_MEMBERSHIP":
                created.append(UUID(bytes=row[8]))
            else:
                return None
        if not retired:
            return None
        names: list[str] = []
        for object_id in (keep[5], drop[5]):
            current = self._connection.execute(
                """
                SELECT r.effective_semantic_scope_id,r.payload_format,r.payload_text
                  FROM objects o JOIN object_revisions r
                    ON r.object_id=o.object_id
                   AND r.object_revision_id=o.current_revision_id
                   AND r.revision_ordinal=o.current_revision_ordinal
                 WHERE o.object_id=?
                """,
                (object_id,),
            ).fetchone()
            if current is None or current[1] != "JSON" or current[2] is None:
                return None
            names.append(_state_from_payload(UUID(bytes=current[0]), current[2]).runtime_motif_id)
        return NativeMotifMergeResult(
            UUID(bytes=keep[5]), UUID(bytes=keep[6]), keep[7], names[0],
            UUID(bytes=drop[5]), UUID(bytes=drop[6]), drop[7], names[1],
            tuple(retired), tuple(created), UUID(bytes=keep[0]), UUID(bytes=keep[1]),
        )

    def _require_row(self, table: str, column: str, value: UUID) -> None:
        if self._connection.execute(
            f"SELECT 1 FROM {table} WHERE {column}=?", (_blob(value),)
        ).fetchone() is None:
            raise SubstrateObjectNotFound(f"required {table} identity was not found")

    def _validate_zero_member_baseline_posture(
        self, evidence: MigrationZeroMemberMotifBaselineEvidence,
    ) -> None:
        """Keep the exceptional import path unavailable to active runtime."""
        if self._connection.execute(
            "SELECT core_id,core_role FROM core_metadata"
        ).fetchall() != [(_blob(evidence.native_core_id), "STAGING")]:
            raise SubstrateInvariantViolation(
                "migration zero-member baseline requires its exact STAGING core"
            )
        if self._connection.execute(
            "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
        ).fetchall() != [("LEGACY_ACTIVE", None)]:
            raise SubstrateInvariantViolation(
                "migration zero-member baseline requires LEGACY_ACTIVE deployment"
            )


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


def _retired_motif_object_state(identity_namespace_id: UUID, state: MotifState) -> ObjectState:
    """Keep a merged-away motif historically addressable, but not live."""
    return ObjectState(
        identity_namespace_id,
        state.semantic_scope_id,
        DERIVED_MOTIF_OBJECT_KIND,
        "RETIRED",
        "DERIVED",
        False,
        "DERIVED",
        "NOT_APPLICABLE",
        state.payload(),
        "JSON",
    )


def _merged_keep_state(keep: MotifState, drop: MotifState, merge_timestamp: int) -> MotifState:
    """The frozen ``MotifRegistry.decide_merge`` aggregate law."""
    centroid = keep.centroid
    if len(keep.centroid) == len(drop.centroid) and len(keep.centroid) > 0:
        keep_weight = max(1e-6, float(keep.strength))
        drop_weight = max(1e-6, float(drop.strength))
        weighted = tuple(
            (float(a) * keep_weight + float(b) * drop_weight) / (keep_weight + drop_weight)
            for a, b in zip(keep.centroid, drop.centroid)
        )
        norm = math.sqrt(sum(value * value for value in weighted))
        centroid = weighted if norm <= 1e-12 else tuple(value / norm for value in weighted)
    return MotifState(
        keep.semantic_scope_id,
        keep.runtime_motif_id,
        keep.domain_id,
        keep.label,
        centroid,
        float(min(1.0, float(keep.strength) + 0.5 * float(drop.strength))),
        keep.stability_score,
        tuple(sorted(set(keep.contributing_agents) | set(drop.contributing_agents))),
        keep.created_ts,
        merge_timestamp,
        keep.derivation_metadata,
        keep.extra_payload,
    )


def _split_plan_intent(plan: NativeMotifSplitPlan) -> dict[str, Any]:
    return {
        "parent_motif_object_id": str(plan.parent_motif_object_id),
        "expected_parent_revision_id": str(plan.expected_parent_revision_id),
        "parent_state": plan.parent_state.intent(),
        "child_state": plan.child_state.intent(),
        "moved_member_object_ids": [str(value) for value in plan.moved_member_object_ids],
        "candidate_member_object_id": str(plan.candidate_member_object_id),
        "candidate_in_child": plan.candidate_in_child,
    }


def _motif_state_from_intent(value: Any) -> MotifState:
    if not isinstance(value, Mapping):
        raise ValueError("motif state intent must be a mapping")
    try:
        state = MotifState(
            UUID(str(value["semantic_scope_id"])),
            value["runtime_motif_id"],
            value["domain_id"],
            value["label"],
            tuple(value["centroid"]),
            value["strength"],
            value["stability_score"],
            tuple(value["contributing_agents"]),
            value["created_ts"],
            value["last_active_ts"],
            value.get("derivation_metadata"),
            value.get("extra_payload"),
        )
        _validate_state(state)
        return state
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("motif state intent is invalid") from exc


def _split_plan_from_intent(value: Any) -> NativeMotifSplitPlan:
    if not isinstance(value, Mapping):
        raise ValueError("split plan intent must be a mapping")
    try:
        return NativeMotifSplitPlan(
            UUID(str(value["parent_motif_object_id"])),
            UUID(str(value["expected_parent_revision_id"])),
            _motif_state_from_intent(value["parent_state"]),
            _motif_state_from_intent(value["child_state"]),
            tuple(UUID(str(item)) for item in value["moved_member_object_ids"]),
            UUID(str(value["candidate_member_object_id"])),
            value["candidate_in_child"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("split plan intent is invalid") from exc


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


def _validate_retired_membership_successor(
    connection: sqlite3.Connection,
    relationship_id: bytes,
    revision_id: bytes,
    revision_ordinal: int,
) -> None:
    """Validate the immutable evidence carried by a current retirement.

    ``RETIRED`` is not a free-form relationship state: it is exactly one
    ordinary successor of the active membership that it preserves.  Readers
    perform this check as well as writers so a malformed historical row never
    becomes silently invisible merely because it is not active geometry.
    """
    row = connection.execute(
        """
        SELECT h.relationship_kind,r.lineage_kind,r.predecessor_revision_id,
               r.predecessor_revision_ordinal,r.effective_semantic_scope_id,
               r.payload_format,r.payload_text,r.existence_state,
               predecessor.relationship_id,predecessor.revision_ordinal,
               predecessor.existence_state,predecessor.effective_semantic_scope_id,
               predecessor.payload_format,predecessor.payload_text
          FROM relationships h
          JOIN relationship_revisions r
            ON r.relationship_id=h.relationship_id
          LEFT JOIN relationship_revisions predecessor
            ON predecessor.relationship_revision_id=r.predecessor_revision_id
           AND predecessor.revision_ordinal=r.predecessor_revision_ordinal
         WHERE h.relationship_id=? AND r.relationship_revision_id=?
           AND r.revision_ordinal=?
        """,
        (relationship_id, revision_id, revision_ordinal),
    ).fetchone()
    if row is None or row[0] != MOTIF_MEMBERSHIP_RELATIONSHIP_KIND:
        raise SubstrateInvariantViolation("retired relationship is not a motif membership")
    if (
        row[1] != "NATIVE_ORDINARY" or row[2] is None or row[3] is None
        or revision_ordinal != row[3] + 1 or row[7] != "RETIRED"
        or row[8] != relationship_id or row[9] != row[3] or row[10] != "EXISTS"
        or row[4] != row[11] or row[5] != row[12] or row[6] != row[13]
    ):
        raise SubstrateInvariantViolation("retired motif membership has invalid predecessor lineage")
    endpoints = connection.execute(
        """
        SELECT endpoint_ordinal,endpoint_role,endpoint_semantic_scope_id,object_id,
               binding_mode,bound_object_revision_id
          FROM relationship_revision_endpoints
         WHERE relationship_revision_id=?
         ORDER BY endpoint_ordinal
        """,
        (revision_id,),
    ).fetchall()
    predecessor_endpoints = connection.execute(
        """
        SELECT endpoint_ordinal,endpoint_role,endpoint_semantic_scope_id,object_id,
               binding_mode,bound_object_revision_id
          FROM relationship_revision_endpoints
         WHERE relationship_revision_id=?
         ORDER BY endpoint_ordinal
        """,
        (row[2],),
    ).fetchall()
    if endpoints != predecessor_endpoints:
        raise SubstrateInvariantViolation("retired motif membership changes immutable endpoints")


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


def _validate_zero_member_baseline_evidence(
    evidence: MigrationZeroMemberMotifBaselineEvidence,
    state: MotifState,
) -> None:
    if not isinstance(evidence, MigrationZeroMemberMotifBaselineEvidence):
        raise ValueError("migration zero-member baseline evidence is required")
    for field in (
        "native_core_id",
        "legacy_snapshot_id",
        "legacy_source_namespace_id",
        "source_motif_object_id",
        "source_motif_revision_id",
        "source_operation_id",
        "source_transition_id",
        "source_motif_artifact_id",
        "workspace_metadata_artifact_id",
        "motif_identity_namespace_id",
        "membership_identity_namespace_id",
        "motif_alias_namespace_id",
        "target_semantic_scope_id",
    ):
        _require_uuid(field, getattr(evidence, field))
    _nonempty_text("runtime_motif_id", evidence.runtime_motif_id)
    for field in (
        "source_motif_artifact_digest",
        "workspace_metadata_digest",
        "scope_plan_digest",
        "source_state_digest",
        "source_membership_digest",
    ):
        _sha256_text(field, getattr(evidence, field))
    source_lane = evidence.source_geometry_lane
    if (
        not isinstance(source_lane, tuple)
        or len(source_lane) != 3
        or not isinstance(source_lane[0], str)
        or not source_lane[0]
        or not isinstance(source_lane[1], str)
        or not source_lane[1]
        or not isinstance(source_lane[2], int)
        or isinstance(source_lane[2], bool)
        or source_lane[2] < 1
    ):
        raise ValueError("migration zero-member baseline source lane is invalid")
    target_lane = evidence.target_lane_identity
    if (
        not isinstance(target_lane, tuple)
        or len(target_lane) != 8
        or not isinstance(target_lane[0], str)
        or not target_lane[0]
        or not isinstance(target_lane[1], str)
        or not target_lane[1]
        or not isinstance(target_lane[2], int)
        or isinstance(target_lane[2], bool)
        or target_lane[2] < 1
        or target_lane[3:] != (
            "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32",
        )
    ):
        raise ValueError("migration zero-member baseline target lane is invalid")
    if (
        evidence.source_member_count != 0
        or not isinstance(evidence.source_member_count, int)
        or isinstance(evidence.source_member_count, bool)
    ):
        raise ValueError("migration zero-member baseline requires exactly zero source members")
    if state.semantic_scope_id != evidence.target_semantic_scope_id:
        raise ValueError("migration zero-member baseline state scope differs from its evidence")
    if state.runtime_motif_id != evidence.runtime_motif_id:
        raise ValueError("migration zero-member baseline runtime motif ID differs from its evidence")
    if _motif_state_digest(state) != evidence.source_state_digest:
        raise ValueError("migration zero-member baseline state does not match the qualified source digest")


def _motif_state_digest(state: MotifState) -> str:
    return hashlib.sha256(canonical_intent_text(state.payload()).encode("utf-8")).hexdigest()


def _sha256_text(field: str, value: Any) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field} must be a lowercase SHA-256 hex digest")


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
