"""Read-only Phase 7G5B1 admission-to-runtime readiness classification.

The 7F admission boundary deliberately stores captured legacy facts as
evidence.  This module is the separate administrative observation boundary:
it explains which of those facts could participate in the already-qualified
A3D runtime *after* a future, separately-authorized B2 operation.  It does
not create a revision, representation, expectation, measurement,
reconciliation case, migration marker, or side-store record.

In particular, a ``LEGACY_EMBEDDING_CAPTURE`` remains UNKNOWN evidence here.
The report can say that deterministic byte derivation is conceivable, but it
never changes the capture's class, source revision, readiness, or authority.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import math
import sqlite3
from typing import Any
from uuid import UUID

import numpy as np

from torment_service.lifecycle import validate_lifecycle_envelope
from torment_service.provenance_v1 import ProvenanceV1

from ..canonical_intent import canonical_intent_text
from ..compat_embedding_reader import NativeCompatEmbeddingReader
from ..errors import SubstrateInvariantViolation
from ..ids import native_id_to_bytes
from ..motif_runtime_reader import NativeMotifRuntimeReader
from ..motifs import DERIVED_MOTIF_OBJECT_KIND
from ..runtime_binding import NativeRepresentationLane
from ..schema import SCHEMA_MAJOR, SCHEMA_MINOR, open_schema
from .motif_admission import LEGACY_DERIVED_MOTIF_OBJECT_KIND


_MEMORY_OBJECT_KIND = "LEGACY_CORE_NODE"
_LEGACY_CAPTURE_CLASS = "LEGACY_EMBEDDING_CAPTURE"
_PRIVATE_AGENT_SCOPE = "PRIVATE_AGENT"
_SHARED_DOMAIN_SCOPE = "SHARED_DOMAIN"
_RUNTIME_LANE = ("COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32")


class ObjectRuntimeReadiness(StrEnum):
    RUNTIME_READY_AS_IS = "RUNTIME_READY_AS_IS"
    DETERMINISTIC_NORMALIZATION_REQUIRED = "DETERMINISTIC_NORMALIZATION_REQUIRED"
    REPRESENTATION_BOOTSTRAP_REQUIRED = "REPRESENTATION_BOOTSTRAP_REQUIRED"
    SEMANTIC_FACTS_UNRESOLVED = "SEMANTIC_FACTS_UNRESOLVED"
    QUARANTINED_OR_UNSUPPORTED = "QUARANTINED_OR_UNSUPPORTED"
    EVIDENCE_ONLY_NOT_RUNTIME_OBJECT = "EVIDENCE_ONLY_NOT_RUNTIME_OBJECT"


class GovernanceEvidenceReadiness(StrEnum):
    EXPLICIT_LEGACY_GOVERNANCE = "EXPLICIT_LEGACY_GOVERNANCE"
    DERIVABLE_BY_FROZEN_LEGACY_RULE = "DERIVABLE_BY_FROZEN_LEGACY_RULE"
    MISSING_GOVERNANCE = "MISSING_GOVERNANCE"
    CONFLICTING_GOVERNANCE_EVIDENCE = "CONFLICTING_GOVERNANCE_EVIDENCE"


class ProvenanceEvidenceReadiness(StrEnum):
    EXPLICIT_PROVENANCE_V1 = "EXPLICIT_PROVENANCE_V1"
    DETERMINISTIC_LEGACY_PROVENANCE_TRANSLATION = "DETERMINISTIC_LEGACY_PROVENANCE_TRANSLATION"
    DESCRIPTIVE_EVIDENCE_ONLY = "DESCRIPTIVE_EVIDENCE_ONLY"
    UNKNOWN_PROVENANCE = "UNKNOWN_PROVENANCE"
    CONFLICTING_PROVENANCE = "CONFLICTING_PROVENANCE"


class LifecycleEvidenceReadiness(StrEnum):
    EXPLICIT_LIFECYCLE_ENVELOPE = "EXPLICIT_LIFECYCLE_ENVELOPE"
    FROZEN_PROTECTED_MARKER_DERIVATION = "FROZEN_PROTECTED_MARKER_DERIVATION"
    ORDINARY_OR_UNSET_DERIVATION = "ORDINARY_OR_UNSET_DERIVATION"
    UNKNOWN_LIFECYCLE = "UNKNOWN_LIFECYCLE"
    CONFLICTING_LIFECYCLE_EVIDENCE = "CONFLICTING_LIFECYCLE_EVIDENCE"


class LegacyVectorStrategy(StrEnum):
    BYTE_DERIVATION_POSSIBLE = "BYTE_DERIVATION_POSSIBLE"
    REEMBED_REQUIRED = "REEMBED_REQUIRED"
    UNUSABLE_VECTOR_EVIDENCE = "UNUSABLE_VECTOR_EVIDENCE"
    NO_VECTOR_PRESENT = "NO_VECTOR_PRESENT"


class MotifRuntimeReadiness(StrEnum):
    RUNTIME_READY_AS_IS = "RUNTIME_READY_AS_IS"
    DETERMINISTIC_NORMALIZATION_REQUIRED = "DETERMINISTIC_NORMALIZATION_REQUIRED"
    MEMBERSHIP_INCOMPLETE = "MEMBERSHIP_INCOMPLETE"
    GEOMETRY_INCOMPLETE = "GEOMETRY_INCOMPLETE"
    SCOPE_UNRESOLVED = "SCOPE_UNRESOLVED"
    QUARANTINED = "QUARANTINED"


class SideStoreDisposition(StrEnum):
    RETAIN_EXTERNAL_UNCHANGED = "RETAIN_EXTERNAL_UNCHANGED"
    MIGRATED_PRIMARY_STATE = "MIGRATED_PRIMARY_STATE"
    MIGRATED_EVIDENCE_ONLY = "MIGRATED_EVIDENCE_ONLY"
    FUTURE_PARITY_REQUIRED = "FUTURE_PARITY_REQUIRED"
    NOT_REQUIRED_FOR_CORE_RUNTIME_PROFILE = "NOT_REQUIRED_FOR_CORE_RUNTIME_PROFILE"


class EIDSideStoreReadiness(StrEnum):
    COMPATIBLE_WITH_NAMESPACED_EID = "COMPATIBLE_WITH_NAMESPACED_EID"
    REQUIRES_SCOPE_CONTEXT = "REQUIRES_SCOPE_CONTEXT"
    AMBIGUOUS = "AMBIGUOUS"
    NO_EID_REFERENCE = "NO_EID_REFERENCE"


class ScopePlanReadiness(StrEnum):
    CURRENT_SCOPE_MATCHES_PLAN = "CURRENT_SCOPE_MATCHES_PLAN"
    DETERMINISTIC_NORMALIZATION_REQUIRED = "DETERMINISTIC_NORMALIZATION_REQUIRED"
    NO_MATCHING_SCOPE_PLAN = "NO_MATCHING_SCOPE_PLAN"
    AMBIGUOUS_SCOPE_PLAN = "AMBIGUOUS_SCOPE_PLAN"


class CoreRuntimeReadiness(StrEnum):
    QUALIFIED_STAGING_LEGACY_ACTIVE = "QUALIFIED_STAGING_LEGACY_ACTIVE"
    CORE_ID_MISMATCH = "CORE_ID_MISMATCH"
    SCHEMA_VERSION_NOT_CURRENT = "SCHEMA_VERSION_NOT_CURRENT"
    CORE_ROLE_NOT_STAGING = "CORE_ROLE_NOT_STAGING"
    DEPLOYMENT_NOT_LEGACY_ACTIVE = "DEPLOYMENT_NOT_LEGACY_ACTIVE"
    DEPLOYMENT_REFERENCES_CORE = "DEPLOYMENT_REFERENCES_CORE"


@dataclass(frozen=True)
class MigrationRuntimeScopePlan:
    """An immutable operator-owned target scope for one source namespace.

    This is an administrative input, not an admitted semantic fact.  A B2
    implementation must revalidate it and create new normal/current facts; a
    B1 report never makes the supplied plan authoritative by itself.
    """

    legacy_source_namespace_id: UUID
    workspace_id: str
    scope_kind: str
    target_identity_namespace_id: UUID
    target_semantic_scope_id: UUID
    motif_alias_namespace_id: UUID
    motif_identity_namespace_id: UUID
    membership_identity_namespace_id: UUID
    idempotency_namespace_id: UUID
    agent_id: str | None = None
    domain_id: str | None = None
    motif_domain_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "legacy_source_namespace_id", "target_identity_namespace_id",
            "target_semantic_scope_id", "motif_alias_namespace_id",
            "motif_identity_namespace_id", "membership_identity_namespace_id",
            "idempotency_namespace_id",
        ):
            if not isinstance(getattr(self, name), UUID):
                raise ValueError(f"{name} must be a UUID")
        if not isinstance(self.workspace_id, str) or not self.workspace_id:
            raise ValueError("workspace_id must be a non-empty string")
        if self.scope_kind == _PRIVATE_AGENT_SCOPE:
            if not isinstance(self.agent_id, str) or not self.agent_id or self.domain_id is not None:
                raise ValueError("PRIVATE_AGENT scope requires agent_id and forbids domain_id")
        elif self.scope_kind == _SHARED_DOMAIN_SCOPE:
            if not isinstance(self.domain_id, str) or not self.domain_id or self.agent_id is not None:
                raise ValueError("SHARED_DOMAIN scope requires domain_id and forbids agent_id")
        else:
            raise ValueError("scope_kind must be PRIVATE_AGENT or SHARED_DOMAIN")
        if self.motif_domain_id is not None and (
            not isinstance(self.motif_domain_id, str) or not self.motif_domain_id
        ):
            raise ValueError("motif_domain_id must be a non-empty string when supplied")

    @property
    def qualifier(self) -> str:
        return self.agent_id if self.scope_kind == _PRIVATE_AGENT_SCOPE else self.domain_id or ""

    def intent(self) -> dict[str, object]:
        return {
            "legacy_source_namespace_id": str(self.legacy_source_namespace_id),
            "workspace_id": self.workspace_id,
            "scope_kind": self.scope_kind,
            "qualifier": self.qualifier,
            "target_identity_namespace_id": str(self.target_identity_namespace_id),
            "target_semantic_scope_id": str(self.target_semantic_scope_id),
            "motif_alias_namespace_id": str(self.motif_alias_namespace_id),
            "motif_identity_namespace_id": str(self.motif_identity_namespace_id),
            "membership_identity_namespace_id": str(self.membership_identity_namespace_id),
            "idempotency_namespace_id": str(self.idempotency_namespace_id),
            "motif_domain_id": self.motif_domain_id,
        }


@dataclass(frozen=True)
class MigrationRuntimeReadinessRequest:
    legacy_snapshot_id: UUID
    expected_native_core_id: UUID
    scope_plans: tuple[MigrationRuntimeScopePlan, ...]
    target_lane: NativeRepresentationLane

    def __post_init__(self) -> None:
        if not isinstance(self.legacy_snapshot_id, UUID):
            raise ValueError("legacy_snapshot_id must be a UUID")
        if not isinstance(self.expected_native_core_id, UUID):
            raise ValueError("expected_native_core_id must be a UUID")
        if not isinstance(self.scope_plans, tuple):
            raise ValueError("scope_plans must be a tuple")
        if any(not isinstance(plan, MigrationRuntimeScopePlan) for plan in self.scope_plans):
            raise ValueError("scope_plans must contain MigrationRuntimeScopePlan values")
        if not isinstance(self.target_lane, NativeRepresentationLane):
            raise ValueError("target_lane must be a NativeRepresentationLane")


@dataclass(frozen=True)
class LegacyCaptureReadiness:
    representation_id: UUID
    source_object_id: UUID
    source_revision_id: UUID
    source_revision_ordinal: int
    dtype: str | None
    dimension: int | None
    encoding_id: str
    derivation_contract_version: str
    provider: str | None
    model: str | None
    strategy: LegacyVectorStrategy
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ObjectRuntimeReadinessItem:
    object_id: UUID
    current_revision_id: UUID
    current_revision_ordinal: int
    eid: int | None
    runtime_ordinal: int | None
    readiness: ObjectRuntimeReadiness
    scope_readiness: ScopePlanReadiness
    governance: GovernanceEvidenceReadiness
    provenance: ProvenanceEvidenceReadiness
    lifecycle: LifecycleEvidenceReadiness
    legacy_captures: tuple[LegacyCaptureReadiness, ...]
    qualified_representation_id: UUID | None
    reason_codes: tuple[str, ...]

    @property
    def legacy_vector_strategy(self) -> LegacyVectorStrategy:
        """Summarize captured vector evidence without inventing a capture row."""
        if not self.legacy_captures:
            return LegacyVectorStrategy.NO_VECTOR_PRESENT
        ranking = {
            LegacyVectorStrategy.UNUSABLE_VECTOR_EVIDENCE: 0,
            LegacyVectorStrategy.REEMBED_REQUIRED: 1,
            LegacyVectorStrategy.BYTE_DERIVATION_POSSIBLE: 2,
        }
        return min(self.legacy_captures, key=lambda item: ranking[item.strategy]).strategy


@dataclass(frozen=True)
class MotifRuntimeReadinessItem:
    motif_object_id: UUID
    current_revision_id: UUID
    current_revision_ordinal: int
    readiness: MotifRuntimeReadiness
    runtime_motif_id: str | None
    membership_count: int
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class SideStoreReadinessItem:
    side_store: str
    disposition: SideStoreDisposition
    eid_readiness: EIDSideStoreReadiness
    reason: str


@dataclass(frozen=True)
class MigrationRuntimeReadinessReport:
    legacy_snapshot_id: UUID
    legacy_source_namespace_id: UUID | None
    native_core_id: UUID
    schema_version: tuple[int, int]
    target_lane: NativeRepresentationLane
    scope_plan_digest: str
    core_readiness: tuple[CoreRuntimeReadiness, ...]
    deploy_gate_ready: bool
    object_items: tuple[ObjectRuntimeReadinessItem, ...]
    motif_items: tuple[MotifRuntimeReadinessItem, ...]
    side_stores: tuple[SideStoreReadinessItem, ...]
    object_readiness_counts: tuple[tuple[str, int], ...]
    motif_readiness_counts: tuple[tuple[str, int], ...]
    runtime_bindable_now_count: int
    normalization_required_count: int
    representation_bootstrap_required_count: int
    reembed_required_count: int
    quarantine_or_unsupported_count: int
    unresolved_semantic_facts_count: int
    authority_expansion_count: int
    blocking_reasons: tuple[str, ...]
    durable_effect_count: int
    b2_recommendation: str

    @property
    def representation_items(self) -> tuple[LegacyCaptureReadiness, ...]:
        """One deterministic row per captured representation, without promotion."""
        return tuple(
            capture for item in self.object_items for capture in item.legacy_captures
        )


class NativeMigrationRuntimeReadinessPreflight:
    """Classify a frozen admission snapshot without changing its native core."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("preflight requires an already-open sqlite connection")
        self._connection = connection
        self._metadata = open_schema(connection, writable=False)

    def run(self, request: MigrationRuntimeReadinessRequest) -> MigrationRuntimeReadinessReport:
        """Return a deterministic, observational readiness report.

        The only database operations in this method are ``SELECT``/``PRAGMA``
        reads performed by schema validation and the qualified A3D readers.
        ``durable_effect_count`` therefore remains zero and is witnessed by a
        before/after semantic-table fingerprint.
        """
        if not isinstance(request, MigrationRuntimeReadinessRequest):
            raise ValueError("request must be a MigrationRuntimeReadinessRequest")
        _validate_target_lane(request.target_lane)
        before = _durable_fingerprint(self._connection)
        core_items = self._core_readiness(request.expected_native_core_id)
        source_row = self._connection.execute(
            "SELECT legacy_source_namespace_id FROM legacy_snapshots WHERE legacy_snapshot_id=?",
            (native_id_to_bytes(request.legacy_snapshot_id),),
        ).fetchone()
        source_namespace_id = None if source_row is None else UUID(bytes=source_row[0])
        if source_namespace_id is None:
            blocking = tuple(sorted({item.value for item in core_items} | {"LEGACY_SNAPSHOT_NOT_FOUND"}))
            return self._report(
                request, None, core_items, (), (), blocking, before, "NO_B2_ACTION_UNTIL_SNAPSHOT_IS_AVAILABLE"
            )
        if (self._metadata.schema_major, self._metadata.schema_minor) != (SCHEMA_MAJOR, SCHEMA_MINOR):
            blocking = tuple(sorted({item.value for item in core_items} | {"SCHEMA_VERSION_NOT_1_2"}))
            return self._report(
                request, source_namespace_id, core_items, (), (), blocking, before, "NO_B2_ACTION_UNTIL_SCHEMA_IS_1_2"
            )

        plans = tuple(
            item for item in request.scope_plans
            if item.legacy_source_namespace_id == source_namespace_id
        )
        plan_reasons = _scope_plan_reference_reasons(self._connection, plans)
        objects = self._admitted_objects(request.legacy_snapshot_id)
        order = self._runtime_order_observation(request.legacy_snapshot_id, source_namespace_id, objects)
        embedding_reader = NativeCompatEmbeddingReader(self._connection)
        object_items = tuple(
            self._classify_object(
                row, source_namespace_id, plans, request.target_lane, order, embedding_reader,
                plan_references_valid=not plan_reasons,
            )
            for row in objects
        )
        motif_items = tuple(
            self._classify_motif(
                row, source_namespace_id, plans, request.target_lane,
                plan_references_valid=not plan_reasons,
            )
            for row in self._motifs(request.legacy_snapshot_id)
        )
        blocking = set(item.value for item in core_items if item is not CoreRuntimeReadiness.QUALIFIED_STAGING_LEGACY_ACTIVE)
        blocking.update(plan_reasons)
        for item in object_items:
            blocking.update(item.reason_codes)
            for capture in item.legacy_captures:
                blocking.update(capture.reason_codes)
        for item in motif_items:
            blocking.update(item.reason_codes)
        recommendation = _b2_recommendation(object_items)
        return self._report(
            request, source_namespace_id, core_items, object_items, motif_items,
            tuple(sorted(blocking)), before, recommendation,
        )

    def _report(
        self,
        request: MigrationRuntimeReadinessRequest,
        source_namespace_id: UUID | None,
        core_items: tuple[CoreRuntimeReadiness, ...],
        object_items: tuple[ObjectRuntimeReadinessItem, ...],
        motif_items: tuple[MotifRuntimeReadinessItem, ...],
        blocking: tuple[str, ...],
        before: tuple[tuple[str, int], ...],
        recommendation: str,
    ) -> MigrationRuntimeReadinessReport:
        after = _durable_fingerprint(self._connection)
        if before != after:
            raise SubstrateInvariantViolation("read-only migration readiness preflight changed durable state")
        object_counts = Counter(item.readiness.value for item in object_items)
        motif_counts = Counter(item.readiness.value for item in motif_items)
        scope_digest = _scope_plan_digest(request.scope_plans)
        return MigrationRuntimeReadinessReport(
            legacy_snapshot_id=request.legacy_snapshot_id,
            legacy_source_namespace_id=source_namespace_id,
            native_core_id=UUID(bytes=self._metadata.core_id),
            schema_version=(self._metadata.schema_major, self._metadata.schema_minor),
            target_lane=request.target_lane,
            scope_plan_digest=scope_digest,
            core_readiness=core_items,
            deploy_gate_ready=core_items == (CoreRuntimeReadiness.QUALIFIED_STAGING_LEGACY_ACTIVE,),
            object_items=object_items,
            motif_items=motif_items,
            side_stores=_side_store_inventory(),
            object_readiness_counts=tuple(sorted(object_counts.items())),
            motif_readiness_counts=tuple(sorted(motif_counts.items())),
            runtime_bindable_now_count=sum(
                item.readiness is ObjectRuntimeReadiness.RUNTIME_READY_AS_IS for item in object_items
            ),
            normalization_required_count=sum(
                item.readiness is ObjectRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED
                for item in object_items
            ),
            representation_bootstrap_required_count=sum(
                item.readiness is ObjectRuntimeReadiness.REPRESENTATION_BOOTSTRAP_REQUIRED
                for item in object_items
            ),
            reembed_required_count=sum(
                capture.strategy is LegacyVectorStrategy.REEMBED_REQUIRED
                for item in object_items for capture in item.legacy_captures
            ),
            quarantine_or_unsupported_count=sum(
                item.readiness is ObjectRuntimeReadiness.QUARANTINED_OR_UNSUPPORTED
                for item in object_items
            ),
            unresolved_semantic_facts_count=sum(
                item.readiness is ObjectRuntimeReadiness.SEMANTIC_FACTS_UNRESOLVED
                for item in object_items
            ),
            authority_expansion_count=0,
            blocking_reasons=blocking,
            durable_effect_count=0,
            b2_recommendation=recommendation,
        )

    def _core_readiness(self, expected_core_id: UUID) -> tuple[CoreRuntimeReadiness, ...]:
        result: list[CoreRuntimeReadiness] = []
        actual = UUID(bytes=self._metadata.core_id)
        if actual != expected_core_id:
            result.append(CoreRuntimeReadiness.CORE_ID_MISMATCH)
        if (self._metadata.schema_major, self._metadata.schema_minor) != (SCHEMA_MAJOR, SCHEMA_MINOR):
            result.append(CoreRuntimeReadiness.SCHEMA_VERSION_NOT_CURRENT)
        if self._metadata.core_role != "STAGING":
            result.append(CoreRuntimeReadiness.CORE_ROLE_NOT_STAGING)
        deployment = self._connection.execute(
            "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
        ).fetchall()
        if len(deployment) != 1:
            result.append(CoreRuntimeReadiness.DEPLOYMENT_NOT_LEGACY_ACTIVE)
        else:
            state, reference = deployment[0]
            if state != "LEGACY_ACTIVE":
                result.append(CoreRuntimeReadiness.DEPLOYMENT_NOT_LEGACY_ACTIVE)
            if reference is not None:
                result.append(CoreRuntimeReadiness.DEPLOYMENT_REFERENCES_CORE)
        return (CoreRuntimeReadiness.QUALIFIED_STAGING_LEGACY_ACTIVE,) if not result else tuple(result)

    def _admitted_objects(self, snapshot_id: UUID) -> tuple[sqlite3.Row | tuple[Any, ...], ...]:
        return tuple(self._connection.execute(
            """
            SELECT o.object_id,o.identity_namespace_id,o.object_kind,o.current_revision_id,o.current_revision_ordinal,
                   r.effective_semantic_scope_id,r.lifecycle_state,r.lifecycle_authoritative,
                   r.governance_state,r.authority_category,r.provenance_id,r.payload_format,r.payload_text
              FROM objects o
              JOIN object_revisions r
                ON r.object_id=o.object_id
               AND r.object_revision_id=o.current_revision_id
               AND r.revision_ordinal=o.current_revision_ordinal
              JOIN semantic_transitions t ON t.transition_id=o.creating_transition_id
              JOIN legacy_admission_effects effect ON effect.transition_id=t.transition_id
              JOIN legacy_admission_records admission ON admission.admission_record_id=effect.admission_record_id
              JOIN legacy_admission_batches batch ON batch.admission_batch_id=admission.admission_batch_id
             WHERE batch.legacy_snapshot_id=?
               AND admission.admission_status='ADMITTED'
             ORDER BY o.object_id
            """,
            (native_id_to_bytes(snapshot_id),),
        ))

    def _motifs(self, snapshot_id: UUID) -> tuple[sqlite3.Row | tuple[Any, ...], ...]:
        return tuple(self._connection.execute(
            """
            SELECT o.object_id,o.identity_namespace_id,o.object_kind,o.current_revision_id,o.current_revision_ordinal,
                   r.effective_semantic_scope_id,r.payload_text
              FROM objects o
              JOIN object_revisions r
                ON r.object_id=o.object_id
               AND r.object_revision_id=o.current_revision_id
               AND r.revision_ordinal=o.current_revision_ordinal
              JOIN semantic_transitions t ON t.transition_id=o.creating_transition_id
              JOIN legacy_admission_effects effect ON effect.transition_id=t.transition_id
              JOIN legacy_admission_records admission ON admission.admission_record_id=effect.admission_record_id
              JOIN legacy_admission_batches batch ON batch.admission_batch_id=admission.admission_batch_id
             WHERE batch.legacy_snapshot_id=?
               AND admission.admission_status='ADMITTED'
               AND o.object_kind=?
             ORDER BY o.object_id
            """,
            (native_id_to_bytes(snapshot_id), LEGACY_DERIVED_MOTIF_OBJECT_KIND),
        ))

    def _runtime_order_observation(
        self,
        snapshot_id: UUID,
        source_namespace_id: UUID,
        objects: tuple[sqlite3.Row | tuple[Any, ...], ...],
    ) -> dict[bytes, tuple[int | None, tuple[str, ...]]]:
        namespace = native_id_to_bytes(source_namespace_id)
        expected: dict[bytes, int] = {}
        for object_id, _identity, object_kind, *_ in objects:
            if object_kind != _MEMORY_OBJECT_KIND:
                continue
            row = self._connection.execute(
                """
                SELECT artifact_record.record_identity
                  FROM objects object_row
                  JOIN semantic_transitions transition ON transition.transition_id=object_row.creating_transition_id
                  JOIN legacy_admission_effects effect ON effect.transition_id=transition.transition_id
                  JOIN legacy_admission_records admission ON admission.admission_record_id=effect.admission_record_id
                  JOIN legacy_admission_batches batch ON batch.admission_batch_id=admission.admission_batch_id
                  JOIN legacy_artifact_records artifact_record
                    ON artifact_record.legacy_artifact_record_id=admission.legacy_artifact_record_id
                 WHERE object_row.object_id=? AND batch.legacy_snapshot_id=?
                """,
                (object_id, native_id_to_bytes(snapshot_id)),
            ).fetchone()
            expected[object_id] = _node_line_ordinal(None if row is None else row[0])
        order_rows = self._connection.execute(
            """
            SELECT object_id,runtime_ordinal FROM memory_runtime_enumeration_orders
             WHERE legacy_source_namespace_id=? ORDER BY runtime_ordinal
            """, (namespace,)
        ).fetchall()
        observed = {row[0]: row[1] for row in order_rows}
        expected_order = tuple(key for key, _ in sorted(expected.items(), key=lambda item: item[1]))
        observed_order = tuple(row[0] for row in order_rows if row[0] in expected)
        whole_order_matches = set(observed) == set(expected) and observed_order == expected_order
        result: dict[bytes, tuple[int | None, tuple[str, ...]]] = {}
        for object_id in expected:
            reasons: list[str] = []
            ordinal = observed.get(object_id)
            if ordinal is None:
                reasons.append("RUNTIME_ORDER_MISSING")
            if not whole_order_matches:
                reasons.append("RUNTIME_ORDER_NOT_FIRST_SURVIVING_JSONL_APPEARANCE")
            result[object_id] = (ordinal, tuple(reasons))
        return result

    def _classify_object(
        self,
        row: sqlite3.Row | tuple[Any, ...],
        source_namespace_id: UUID,
        plans: tuple[MigrationRuntimeScopePlan, ...],
        lane: NativeRepresentationLane,
        order: dict[bytes, tuple[int | None, tuple[str, ...]]],
        embedding_reader: NativeCompatEmbeddingReader,
        plan_references_valid: bool,
    ) -> ObjectRuntimeReadinessItem:
        (
            object_blob, identity_blob, object_kind, revision_blob, revision_ordinal, scope_blob,
            lifecycle_state, lifecycle_authoritative, governance_state, authority_category,
            provenance_blob, payload_format, payload_text,
        ) = row
        object_id = UUID(bytes=object_blob)
        revision_id = UUID(bytes=revision_blob)
        plan_state, plan = _plan_for_current_scope(plans, UUID(bytes=scope_blob))
        payload = _json_mapping(payload_text) if payload_format in {"TEXT", "JSON"} else None
        # A 7F core-node R1 stores the whole selected JSONL row as TEXT.  Its
        # actual runtime payload is the nested ``row[\"payload\"]`` mapping,
        # exactly as MemoryGraph._load() observes it; an arbitrary top-level
        # ``text`` field remains evidence, not a runtime-payload shortcut.
        if object_kind == _MEMORY_OBJECT_KIND and payload_format == "TEXT":
            payload = _legacy_node_runtime_payload(payload)
        if object_kind != _MEMORY_OBJECT_KIND:
            return ObjectRuntimeReadinessItem(
                object_id=object_id,
                current_revision_id=revision_id,
                current_revision_ordinal=revision_ordinal,
                eid=None,
                runtime_ordinal=None,
                readiness=ObjectRuntimeReadiness.EVIDENCE_ONLY_NOT_RUNTIME_OBJECT,
                scope_readiness=plan_state,
                governance=self._governance(object_blob, revision_blob, revision_ordinal, payload),
                provenance=self._provenance(provenance_blob, payload),
                lifecycle=_lifecycle_readiness(lifecycle_state, lifecycle_authoritative, payload),
                legacy_captures=(),
                qualified_representation_id=None,
                reason_codes=("OBJECT_KIND_NOT_CORE_RUNTIME_PROFILE",),
            )
        eid, alias_reasons = _unique_eid(self._connection, source_namespace_id, object_blob)
        runtime_ordinal, order_reasons = order.get(object_blob, (None, ("RUNTIME_ORDER_MISSING",)))
        governance = self._governance(object_blob, revision_blob, revision_ordinal, payload)
        provenance = self._provenance(provenance_blob, payload)
        lifecycle = _lifecycle_readiness(lifecycle_state, lifecycle_authoritative, payload)
        captures = self._legacy_captures(object_blob, lane)
        reasons = list(alias_reasons) + list(order_reasons)
        if authority_category == "ACTIVE_AUTHORIZATION":
            reasons.append("ACTIVE_AUTHORIZATION_OUT_OF_B1_SCOPE")
        if governance is GovernanceEvidenceReadiness.MISSING_GOVERNANCE:
            reasons.append("MISSING_GOVERNANCE")
        elif governance is GovernanceEvidenceReadiness.CONFLICTING_GOVERNANCE_EVIDENCE:
            reasons.append("CONFLICTING_GOVERNANCE_EVIDENCE")
        if provenance in {
            ProvenanceEvidenceReadiness.UNKNOWN_PROVENANCE,
            ProvenanceEvidenceReadiness.DESCRIPTIVE_EVIDENCE_ONLY,
            ProvenanceEvidenceReadiness.CONFLICTING_PROVENANCE,
        }:
            reasons.append(provenance.value)
        if lifecycle in {
            LifecycleEvidenceReadiness.UNKNOWN_LIFECYCLE,
            LifecycleEvidenceReadiness.CONFLICTING_LIFECYCLE_EVIDENCE,
        }:
            reasons.append(lifecycle.value)
        if plan_state is ScopePlanReadiness.NO_MATCHING_SCOPE_PLAN:
            reasons.append("RUNTIME_SCOPE_PLAN_MISSING")
        elif plan_state is ScopePlanReadiness.AMBIGUOUS_SCOPE_PLAN:
            reasons.append("RUNTIME_SCOPE_PLAN_AMBIGUOUS")
        elif plan is not None and identity_blob != native_id_to_bytes(plan.target_identity_namespace_id):
            reasons.append("IDENTITY_NAMESPACE_NORMALIZATION_REQUIRED")
        if not plan_references_valid:
            reasons.append("RUNTIME_SCOPE_PLAN_REFERENCES_UNAVAILABLE_FACTS")
        qualified_representation_id: UUID | None = None
        try:
            qualified = embedding_reader.read_current(object_id, expected_dimension=lane.dimension)
        except (SubstrateInvariantViolation, ValueError):
            qualified = None
            reasons.append("QUALIFIED_REPRESENTATION_CONTRADICTORY")
        if qualified is not None:
            qualified_representation_id = qualified.representation_id
        if not captures and qualified_representation_id is None:
            reasons.append("NO_LEGACY_VECTOR_EVIDENCE")
        elif captures and not qualified_representation_id:
            reasons.append("NO_CURRENT_QUALIFIED_COMPAT_EMBEDDING")
        readiness = _object_readiness(
            reasons, plan_state, qualified_representation_id is not None,
        )
        return ObjectRuntimeReadinessItem(
            object_id=object_id,
            current_revision_id=revision_id,
            current_revision_ordinal=revision_ordinal,
            eid=eid,
            runtime_ordinal=runtime_ordinal,
            readiness=readiness,
            scope_readiness=plan_state,
            governance=governance,
            provenance=provenance,
            lifecycle=lifecycle,
            legacy_captures=captures,
            qualified_representation_id=qualified_representation_id,
            reason_codes=tuple(sorted(set(reasons))),
        )

    def _governance(
        self, object_blob: bytes, revision_blob: bytes, ordinal: int, payload: dict[str, Any] | None,
    ) -> GovernanceEvidenceReadiness:
        row = self._connection.execute(
            """SELECT protected,non_shareable,collective_export_blocked,
                      collective_reingest_blocked,decay_accelerated
                 FROM object_revision_governance
                WHERE object_id=? AND object_revision_id=? AND object_revision_ordinal=?""",
            (object_blob, revision_blob, ordinal),
        ).fetchall()
        stored = None if not row else tuple(bool(item) for item in row[0])
        payload_facts = _payload_governance(payload)
        if len(row) > 1 or payload_facts == "INVALID":
            return GovernanceEvidenceReadiness.CONFLICTING_GOVERNANCE_EVIDENCE
        if stored is not None and isinstance(payload_facts, tuple) and stored != payload_facts:
            return GovernanceEvidenceReadiness.CONFLICTING_GOVERNANCE_EVIDENCE
        # There is intentionally no default-all-false conversion and no frozen
        # protected-marker rule in the 7F contract.  The derivable enum is part
        # of the report vocabulary for a future frozen rule, not an inference.
        if stored is not None or isinstance(payload_facts, tuple):
            return GovernanceEvidenceReadiness.EXPLICIT_LEGACY_GOVERNANCE
        return GovernanceEvidenceReadiness.MISSING_GOVERNANCE

    def _provenance(
        self, provenance_blob: bytes | None, payload: dict[str, Any] | None,
    ) -> ProvenanceEvidenceReadiness:
        descriptive = payload is not None and "provenance" in payload
        if provenance_blob is None:
            if descriptive and _is_exact_provenance_v1(payload["provenance"]):
                return ProvenanceEvidenceReadiness.DETERMINISTIC_LEGACY_PROVENANCE_TRANSLATION
            return (
                ProvenanceEvidenceReadiness.DESCRIPTIVE_EVIDENCE_ONLY
                if descriptive else ProvenanceEvidenceReadiness.UNKNOWN_PROVENANCE
            )
        rows = self._connection.execute(
            """SELECT origin_kind,source_channel,source_role,derivation_status,
                      uncertainty_state FROM provenance_records WHERE provenance_id=?""",
            (provenance_blob,),
        ).fetchall()
        if len(rows) != 1:
            return ProvenanceEvidenceReadiness.CONFLICTING_PROVENANCE
        origin, channel, role, derivation, uncertainty = rows[0]
        # ProvenanceV1 legitimately permits source_role to be absent for
        # direct user/tool/memory sources.  Requiring a role here would make
        # a correctly translated native provenance child look contradictory.
        if not all(isinstance(value, str) and value for value in (origin, channel, derivation, uncertainty)) or (
            role is not None and (not isinstance(role, str) or not role)
        ):
            return ProvenanceEvidenceReadiness.CONFLICTING_PROVENANCE
        return ProvenanceEvidenceReadiness.EXPLICIT_PROVENANCE_V1

    def _legacy_captures(
        self, object_blob: bytes, lane: NativeRepresentationLane,
    ) -> tuple[LegacyCaptureReadiness, ...]:
        rows = self._connection.execute(
            """
            SELECT r.representation_id,r.source_object_revision_id,r.source_object_revision_ordinal,
                   r.dtype,r.dimension,r.encoding_id,r.derivation_contract_version,
                   r.expected_payload_byte_length,p.payload_bytes,admission.unknown_fields_json
              FROM representations r
              JOIN representation_current_state state USING(representation_id)
              JOIN representation_state_effects state_effect ON state_effect.representation_id=r.representation_id
              JOIN semantic_transitions transition ON transition.transition_id=state_effect.transition_id
              JOIN legacy_admission_effects effect ON effect.transition_id=transition.transition_id
              JOIN legacy_admission_records admission ON admission.admission_record_id=effect.admission_record_id
              LEFT JOIN representation_payloads p USING(representation_id)
             WHERE r.source_kind='OBJECT_REVISION' AND r.source_object_id=?
               AND r.representation_class=?
               AND transition.transition_kind='LEGACY_REPRESENTATION_ADMISSION'
               AND state.readiness='UNKNOWN' AND state.operational_disposition='RECONCILIATION_REQUIRED'
             ORDER BY r.representation_id
            """, (object_blob, _LEGACY_CAPTURE_CLASS),
        ).fetchall()
        captures: list[LegacyCaptureReadiness] = []
        for rep_id, revision_id, ordinal, dtype, dimension, encoding, contract, expected_len, payload, unknown_json in rows:
            metadata = _json_mapping(unknown_json)
            legacy_metadata = metadata.get("legacy_derivation_metadata", {}) if metadata else {}
            provider = legacy_metadata.get("provider") if isinstance(legacy_metadata, dict) else None
            model = legacy_metadata.get("model") if isinstance(legacy_metadata, dict) else None
            reasons: list[str] = []
            valid = _valid_capture_payload(dtype, dimension, expected_len, payload)
            if not valid:
                strategy = LegacyVectorStrategy.UNUSABLE_VECTOR_EVIDENCE
                reasons.append("LEGACY_VECTOR_BYTES_OR_METADATA_INVALID")
            elif (
                encoding != "NUMPY_NPY" or dtype != lane.dtype or dimension != lane.dimension
                or provider != lane.provider or model != lane.model
            ):
                strategy = LegacyVectorStrategy.REEMBED_REQUIRED
                if dtype != lane.dtype:
                    reasons.append("LEGACY_VECTOR_DTYPE_DOES_NOT_MATCH_TARGET_LANE")
                if dimension != lane.dimension:
                    reasons.append("LEGACY_VECTOR_DIMENSION_DOES_NOT_MATCH_TARGET_LANE")
                if encoding != "NUMPY_NPY":
                    reasons.append("LEGACY_VECTOR_NPY_EVIDENCE_MISSING")
                if provider != lane.provider or model != lane.model:
                    reasons.append("LEGACY_VECTOR_PROVIDER_MODEL_NOT_PROVEN_FOR_TARGET_LANE")
            else:
                strategy = LegacyVectorStrategy.BYTE_DERIVATION_POSSIBLE
                reasons.append("FUTURE_BYTE_DERIVATION_REQUIRES_FROZEN_B2_RULE")
                if contract != lane.derivation_contract_version:
                    reasons.append("LEGACY_CONTRACT_REQUIRES_EXPLICIT_NORMALIZATION")
            captures.append(LegacyCaptureReadiness(
                representation_id=UUID(bytes=rep_id),
                source_object_id=UUID(bytes=object_blob),
                source_revision_id=UUID(bytes=revision_id),
                source_revision_ordinal=ordinal,
                dtype=dtype,
                dimension=dimension,
                encoding_id=encoding,
                derivation_contract_version=contract,
                provider=provider if isinstance(provider, str) else None,
                model=model if isinstance(model, str) else None,
                strategy=strategy,
                reason_codes=tuple(sorted(set(reasons))),
            ))
        return tuple(captures)

    def _classify_motif(
        self,
        row: sqlite3.Row | tuple[Any, ...],
        source_namespace_id: UUID,
        plans: tuple[MigrationRuntimeScopePlan, ...],
        lane: NativeRepresentationLane,
        plan_references_valid: bool,
    ) -> MotifRuntimeReadinessItem:
        object_blob, identity_blob, object_kind, revision_blob, ordinal, scope_blob, payload_text = row
        object_id = UUID(bytes=object_blob)
        revision_id = UUID(bytes=revision_blob)
        plan_state, plan = _plan_for_current_scope(plans, UUID(bytes=scope_blob))
        reasons: list[str] = []
        runtime_id: str | None = None
        member_count = 0
        projected_legacy_motif = False
        payload = _json_mapping(payload_text)
        if payload is None:
            reasons.append("MOTIF_PAYLOAD_INVALID")
        else:
            motif_id = payload.get("motif_id")
            runtime_id = motif_id if isinstance(motif_id, str) and motif_id else None
            centroid = payload.get("centroid")
            if not isinstance(centroid, list) or len(centroid) != lane.dimension or not all(
                isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
                for value in centroid
            ):
                reasons.append("MOTIF_CENTROID_NOT_TARGET_LANE_DIMENSION")
        if plan_state is ScopePlanReadiness.NO_MATCHING_SCOPE_PLAN:
            reasons.append("RUNTIME_SCOPE_PLAN_MISSING")
        elif plan_state is ScopePlanReadiness.AMBIGUOUS_SCOPE_PLAN:
            reasons.append("RUNTIME_SCOPE_PLAN_AMBIGUOUS")
        elif plan is not None:
            if object_kind == LEGACY_DERIVED_MOTIF_OBJECT_KIND:
                projected = self._qualified_runtime_projection(
                    object_id, revision_id, runtime_id, payload, plan, lane
                )
                if projected is None:
                    reasons.append("MOTIF_OBJECT_KIND_NORMALIZATION_REQUIRED")
                else:
                    projected_legacy_motif = True
                    member_count = projected
            elif object_kind != DERIVED_MOTIF_OBJECT_KIND:
                reasons.append("MOTIF_OBJECT_KIND_NORMALIZATION_REQUIRED")
            if not projected_legacy_motif and identity_blob != native_id_to_bytes(plan.motif_identity_namespace_id):
                reasons.append("MOTIF_IDENTITY_NAMESPACE_NORMALIZATION_REQUIRED")
            if plan.motif_domain_id is None:
                reasons.append("MOTIF_DOMAIN_PLAN_MISSING")
            if not projected_legacy_motif:
                aliases = self._connection.execute(
                    """SELECT alias_value FROM legacy_object_aliases
                         WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND object_id=?""",
                    (native_id_to_bytes(plan.motif_alias_namespace_id), object_blob),
                ).fetchall()
                if len(aliases) != 1:
                    reasons.append("MOTIF_ID_ALIAS_NOT_UNIQUE_IN_TARGET_NAMESPACE")
                elif runtime_id is not None and aliases[0][0] != runtime_id:
                    reasons.append("MOTIF_ID_ALIAS_PAYLOAD_MISMATCH")
        if not plan_references_valid:
            reasons.append("RUNTIME_SCOPE_PLAN_REFERENCES_UNAVAILABLE_FACTS")
        reader = NativeMotifRuntimeReader(self._connection)
        if object_kind == DERIVED_MOTIF_OBJECT_KIND:
            try:
                members = reader.list_ordered_current_motif_members(object_id)
                member_count = len(members)
                if not members:
                    reasons.append("MOTIF_HAS_NO_CURRENT_MEMBERS")
                for member in members:
                    try:
                        vector = reader.read_current_compat_embedding(
                            member.member_object_id, expected_dimension=lane.dimension
                        )
                    except SubstrateInvariantViolation:
                        vector = None
                    if vector is None:
                        reasons.append("MOTIF_MEMBER_GEOMETRY_NOT_QUALIFIED")
                        break
            except (SubstrateInvariantViolation, ValueError):
                reasons.append("MOTIF_MEMBERSHIP_PUBLICATION_INCOMPLETE")
        elif not projected_legacy_motif:
            member_count = self._legacy_motif_membership_count(object_blob)
            if member_count == 0:
                reasons.append("MOTIF_HAS_NO_CURRENT_MEMBERS")
        readiness = (
            MotifRuntimeReadiness.RUNTIME_READY_AS_IS
            if projected_legacy_motif and not reasons
            else _motif_readiness(reasons, plan_state)
        )
        if readiness is MotifRuntimeReadiness.RUNTIME_READY_AS_IS and plan is not None:
            # The final ready claim uses the actual A3B reader, rather than a
            # lookalike query, so the report cannot overstate its eligibility.
            try:
                reader.list_runtime_motifs(
                    motif_alias_namespace_id=plan.motif_alias_namespace_id,
                    domain_id=plan.motif_domain_id or "",
                    semantic_scope_id=plan.target_semantic_scope_id,
                )
            except (SubstrateInvariantViolation, ValueError):
                readiness = MotifRuntimeReadiness.QUARANTINED
                reasons.append("A3B_RUNTIME_MOTIF_READER_REFUSED")
        return MotifRuntimeReadinessItem(
            motif_object_id=object_id,
            current_revision_id=revision_id,
            current_revision_ordinal=ordinal,
            readiness=readiness,
            runtime_motif_id=runtime_id,
            membership_count=member_count,
            reason_codes=tuple(sorted(set(reasons))),
        )

    def _qualified_runtime_projection(
        self,
        source_object_id: UUID,
        source_revision_id: UUID,
        runtime_id: str | None,
        source_payload: dict[str, Any] | None,
        plan: MigrationRuntimeScopePlan,
        lane: NativeRepresentationLane,
    ) -> int | None:
        """Validate a B4A projection through the actual A3B reader.

        The legacy source remains a ``LEGACY_DERIVED_MOTIF``.  This check
        therefore never retypes it; it establishes only that one exact source
        evidence object has a qualified, separately-addressed runtime peer.
        """
        if runtime_id is None or source_payload is None or plan.motif_domain_id is None:
            return None
        rows = self._connection.execute(
            """
            SELECT o.object_id,operation.canonical_intent_json
              FROM semantic_transitions t
              JOIN operations operation ON operation.operation_id=t.operation_id
              JOIN operation_outputs o ON o.operation_id=operation.operation_id
             WHERE t.transition_kind='MIGRATION_RUNTIME_MOTIF_PROJECTION' AND t.origin_kind='NATIVE'
               AND operation.operation_kind='MIGRATION_RUNTIME_MOTIF_PROJECTION'
               AND o.output_ordinal=0 AND o.output_role='MIGRATION_RUNTIME_MOTIF_PROJECTION'
               AND o.output_kind='OBJECT'
            """
        ).fetchall()
        candidates: list[tuple[bytes, dict[str, Any]]] = []
        for target_id, intent_text in rows:
            try:
                intent = json.loads(intent_text)
            except (TypeError, json.JSONDecodeError):
                return None
            if not isinstance(intent, dict):
                return None
            expected_lane = [lane.provider, lane.model, lane.dimension, lane.representation_class,
                             lane.generation, lane.derivation_contract_version, lane.encoding_id, lane.dtype]
            if (
                intent.get("source_motif_object_id") == str(source_object_id)
                and intent.get("source_motif_revision_id") == str(source_revision_id)
                and intent.get("runtime_motif_id") == runtime_id
                and intent.get("target_lane") == expected_lane
                and intent.get("motif_alias_namespace_id") == str(plan.motif_alias_namespace_id)
                and intent.get("target_semantic_scope_id") == str(plan.target_semantic_scope_id)
                and intent.get("motif_identity_namespace_id") == str(plan.motif_identity_namespace_id)
                and intent.get("membership_identity_namespace_id") == str(plan.membership_identity_namespace_id)
                and intent.get("state") == _runtime_motif_state_payload(source_payload)
            ):
                candidates.append((target_id, intent))
        if len(candidates) != 1:
            return None
        target_id, intent = candidates[0]
        try:
            reader = NativeMotifRuntimeReader(self._connection)
            motifs = reader.list_runtime_motifs(
                motif_alias_namespace_id=plan.motif_alias_namespace_id,
                domain_id=plan.motif_domain_id,
                semantic_scope_id=plan.target_semantic_scope_id,
            )
            runtime = [item for item in motifs if item.motif_object_id == UUID(bytes=target_id)]
            if len(runtime) != 1:
                return None
            members = reader.list_ordered_current_motif_members(runtime[0].motif_object_id)
            expected_members = intent.get("member_object_ids")
            if not isinstance(expected_members, list) or [str(item.member_object_id) for item in members] != expected_members:
                return None
            if not members or runtime[0].read_model.member_count != len(members):
                return None
            for member in members:
                if reader.read_current_compat_embedding(member.member_object_id, expected_dimension=lane.dimension) is None:
                    return None
        except (SubstrateInvariantViolation, ValueError):
            return None
        return len(members)

    def _legacy_motif_membership_count(self, motif_object_id: bytes) -> int:
        """Count current admitted membership identities without treating them as runtime motifs."""
        row = self._connection.execute(
            """
            SELECT count(*)
              FROM relationships relationship_row
              JOIN relationship_revisions revision
                ON revision.relationship_id=relationship_row.relationship_id
               AND revision.relationship_revision_id=relationship_row.current_revision_id
               AND revision.revision_ordinal=relationship_row.current_revision_ordinal
              JOIN relationship_revision_endpoints endpoint
                ON endpoint.relationship_revision_id=revision.relationship_revision_id
               AND endpoint.endpoint_ordinal=0 AND endpoint.endpoint_role='MOTIF'
             WHERE relationship_row.relationship_kind='MOTIF_MEMBERSHIP'
               AND endpoint.object_id=?
            """, (motif_object_id,),
        ).fetchone()
        return 0 if row is None else row[0]


def _validate_target_lane(lane: NativeRepresentationLane) -> None:
    if lane.dimension < 1 or not lane.provider or not lane.model:
        raise ValueError("target lane provider, model, and positive dimension are required")
    if (
        lane.representation_class, lane.generation, lane.derivation_contract_version,
        lane.encoding_id, lane.dtype,
    ) != _RUNTIME_LANE:
        raise ValueError("B1 assesses only the qualified COMPAT_EMBEDDING/1 RAW_VECTOR float32 lane")


def _scope_plan_digest(plans: tuple[MigrationRuntimeScopePlan, ...]) -> str:
    values = sorted((plan.intent() for plan in plans), key=canonical_intent_text)
    return hashlib.sha256(canonical_intent_text(values).encode("utf-8")).hexdigest()


def _scope_plan_reference_reasons(
    connection: sqlite3.Connection, plans: tuple[MigrationRuntimeScopePlan, ...],
) -> set[str]:
    reasons: set[str] = set()
    if len(plans) != 1:
        reasons.add("RUNTIME_SCOPE_PLAN_MISSING" if not plans else "RUNTIME_SCOPE_PLAN_AMBIGUOUS")
        return reasons
    plan = plans[0]
    checks = (
        ("identity_namespaces", "identity_namespace_id", plan.target_identity_namespace_id, "TARGET_IDENTITY_NAMESPACE_MISSING"),
        ("identity_namespaces", "identity_namespace_id", plan.motif_identity_namespace_id, "MOTIF_IDENTITY_NAMESPACE_MISSING"),
        ("identity_namespaces", "identity_namespace_id", plan.membership_identity_namespace_id, "MEMBERSHIP_IDENTITY_NAMESPACE_MISSING"),
        ("semantic_scopes", "semantic_scope_id", plan.target_semantic_scope_id, "TARGET_SEMANTIC_SCOPE_MISSING"),
        ("idempotency_namespaces", "idempotency_namespace_id", plan.idempotency_namespace_id, "IDEMPOTENCY_NAMESPACE_MISSING"),
        ("legacy_source_namespaces", "legacy_source_namespace_id", plan.motif_alias_namespace_id, "MOTIF_ALIAS_NAMESPACE_MISSING"),
    )
    for table, column, value, reason in checks:
        if connection.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)).fetchone() is None:
            reasons.add(reason)
    return reasons


def _plan_for_current_scope(
    plans: tuple[MigrationRuntimeScopePlan, ...], current_scope_id: UUID,
) -> tuple[ScopePlanReadiness, MigrationRuntimeScopePlan | None]:
    if not plans:
        return ScopePlanReadiness.NO_MATCHING_SCOPE_PLAN, None
    if len(plans) != 1:
        return ScopePlanReadiness.AMBIGUOUS_SCOPE_PLAN, None
    plan = plans[0]
    return (
        (ScopePlanReadiness.CURRENT_SCOPE_MATCHES_PLAN, plan)
        if current_scope_id == plan.target_semantic_scope_id
        else (ScopePlanReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED, plan)
    )


def _node_line_ordinal(value: str | None) -> int:
    prefix = "TMS-LEGACY-NODES-LINE-1:"
    if not isinstance(value, str) or not value.startswith(prefix):
        return 2**63 - 1
    try:
        ordinal = int(value[len(prefix):])
    except ValueError:
        return 2**63 - 1
    return ordinal if ordinal >= 1 else 2**63 - 1


def _unique_eid(connection: sqlite3.Connection, source_namespace_id: UUID, object_blob: bytes) -> tuple[int | None, tuple[str, ...]]:
    rows = connection.execute(
        """SELECT alias_value FROM legacy_object_aliases
             WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND object_id=?""",
        (native_id_to_bytes(source_namespace_id), object_blob),
    ).fetchall()
    if len(rows) != 1:
        return None, ("EID_ALIAS_NOT_UNIQUE",)
    value = rows[0][0]
    if not isinstance(value, str) or not value.isdigit() or str(int(value)) != value:
        return None, ("EID_ALIAS_NOT_CANONICAL",)
    return int(value), ()


def _json_mapping(value: object) -> dict[str, Any] | None:
    if not isinstance(value, str):
        return None
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return None
    return decoded if isinstance(decoded, dict) else None


def _legacy_node_runtime_payload(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    payload = value.get("payload")
    return payload if isinstance(payload, dict) else None


def _payload_governance(payload: dict[str, Any] | None) -> tuple[bool, ...] | str | None:
    if payload is None or "governance" not in payload:
        return None
    value = payload["governance"]
    fields = (
        "protected", "non_shareable", "collective_export_blocked",
        "collective_reingest_blocked", "decay_accelerated",
    )
    if not isinstance(value, dict) or set(value) != set(fields):
        return "INVALID"
    values = tuple(value[name] for name in fields)
    return tuple(values) if all(isinstance(item, bool) for item in values) else "INVALID"


def _lifecycle_readiness(
    state: object, authoritative: object, payload: dict[str, Any] | None,
) -> LifecycleEvidenceReadiness:
    explicit = authoritative == 1 and isinstance(state, str) and state not in {"", "UNKNOWN"}
    payload_lifecycle = payload.get("lifecycle") if payload else None
    payload_status = payload.get("lifecycle_status") if payload else None
    if payload_status is not None:
        try:
            status = validate_lifecycle_envelope(payload_status)
        except (TypeError, ValueError):
            return LifecycleEvidenceReadiness.CONFLICTING_LIFECYCLE_EVIDENCE
        if status.to_dict() != payload_status or not status.is_authoritative_on_row:
            return LifecycleEvidenceReadiness.CONFLICTING_LIFECYCLE_EVIDENCE
        if explicit and state != status.state.value.upper():
            return LifecycleEvidenceReadiness.CONFLICTING_LIFECYCLE_EVIDENCE
        return LifecycleEvidenceReadiness.EXPLICIT_LIFECYCLE_ENVELOPE
    if payload_lifecycle is not None and not isinstance(payload_lifecycle, dict):
        return LifecycleEvidenceReadiness.CONFLICTING_LIFECYCLE_EVIDENCE
    if explicit:
        if isinstance(payload_lifecycle, dict) and payload_lifecycle.get("state") not in {None, state}:
            return LifecycleEvidenceReadiness.CONFLICTING_LIFECYCLE_EVIDENCE
        return LifecycleEvidenceReadiness.EXPLICIT_LIFECYCLE_ENVELOPE
    if authoritative == 0 and state == "UNKNOWN":
        return LifecycleEvidenceReadiness.UNKNOWN_LIFECYCLE
    return LifecycleEvidenceReadiness.ORDINARY_OR_UNSET_DERIVATION


def _is_exact_provenance_v1(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    try:
        return ProvenanceV1.from_dict(value).to_dict() == value
    except (TypeError, ValueError):
        return False


def _valid_capture_payload(dtype: object, dimension: object, expected_length: object, payload: object) -> bool:
    if not isinstance(dtype, str) or not isinstance(dimension, int) or isinstance(dimension, bool) or dimension < 1:
        return False
    try:
        numeric_dtype = np.dtype(dtype)
    except TypeError:
        return False
    if numeric_dtype.kind != "f":
        return False
    if not isinstance(payload, bytes) or expected_length != len(payload) or len(payload) != dimension * numeric_dtype.itemsize:
        return False
    vector = np.frombuffer(payload, dtype=numeric_dtype)
    return vector.size == dimension and bool(np.all(np.isfinite(vector)))


def _object_readiness(
    reasons: list[str], scope: ScopePlanReadiness, qualified: bool,
) -> ObjectRuntimeReadiness:
    critical = set(reasons)
    if any(item in critical for item in (
        "EID_ALIAS_NOT_UNIQUE", "EID_ALIAS_NOT_CANONICAL", "RUNTIME_ORDER_MISSING",
        "RUNTIME_ORDER_NOT_FIRST_SURVIVING_JSONL_APPEARANCE", "ACTIVE_AUTHORIZATION_OUT_OF_B1_SCOPE",
        "QUALIFIED_REPRESENTATION_CONTRADICTORY",
    )):
        return ObjectRuntimeReadiness.QUARANTINED_OR_UNSUPPORTED
    if scope in {ScopePlanReadiness.NO_MATCHING_SCOPE_PLAN, ScopePlanReadiness.AMBIGUOUS_SCOPE_PLAN}:
        return ObjectRuntimeReadiness.SEMANTIC_FACTS_UNRESOLVED
    if any(item in critical for item in (
        "MISSING_GOVERNANCE", "CONFLICTING_GOVERNANCE_EVIDENCE",
        "RUNTIME_SCOPE_PLAN_REFERENCES_UNAVAILABLE_FACTS",
        ProvenanceEvidenceReadiness.UNKNOWN_PROVENANCE.value,
        ProvenanceEvidenceReadiness.DESCRIPTIVE_EVIDENCE_ONLY.value,
        ProvenanceEvidenceReadiness.CONFLICTING_PROVENANCE.value,
        LifecycleEvidenceReadiness.UNKNOWN_LIFECYCLE.value,
        LifecycleEvidenceReadiness.CONFLICTING_LIFECYCLE_EVIDENCE.value,
    )):
        return ObjectRuntimeReadiness.SEMANTIC_FACTS_UNRESOLVED
    if scope is ScopePlanReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED or "IDENTITY_NAMESPACE_NORMALIZATION_REQUIRED" in critical:
        return ObjectRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED
    return ObjectRuntimeReadiness.RUNTIME_READY_AS_IS if qualified else ObjectRuntimeReadiness.REPRESENTATION_BOOTSTRAP_REQUIRED


def _motif_readiness(reasons: list[str], scope: ScopePlanReadiness) -> MotifRuntimeReadiness:
    values = set(reasons)
    if "MOTIF_PAYLOAD_INVALID" in values or "A3B_RUNTIME_MOTIF_READER_REFUSED" in values:
        return MotifRuntimeReadiness.QUARANTINED
    if scope in {ScopePlanReadiness.NO_MATCHING_SCOPE_PLAN, ScopePlanReadiness.AMBIGUOUS_SCOPE_PLAN}:
        return MotifRuntimeReadiness.SCOPE_UNRESOLVED
    if "MOTIF_MEMBERSHIP_PUBLICATION_INCOMPLETE" in values or "MOTIF_HAS_NO_CURRENT_MEMBERS" in values:
        return MotifRuntimeReadiness.MEMBERSHIP_INCOMPLETE
    if "MOTIF_MEMBER_GEOMETRY_NOT_QUALIFIED" in values or "MOTIF_CENTROID_NOT_TARGET_LANE_DIMENSION" in values:
        return MotifRuntimeReadiness.GEOMETRY_INCOMPLETE
    if scope is ScopePlanReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED or any(
        item in values for item in (
            "MOTIF_IDENTITY_NAMESPACE_NORMALIZATION_REQUIRED", "MOTIF_DOMAIN_PLAN_MISSING",
            "MOTIF_ID_ALIAS_NOT_UNIQUE_IN_TARGET_NAMESPACE", "MOTIF_ID_ALIAS_PAYLOAD_MISMATCH",
            "MOTIF_OBJECT_KIND_NORMALIZATION_REQUIRED",
        )
    ):
        return MotifRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED
    return MotifRuntimeReadiness.RUNTIME_READY_AS_IS


def _runtime_motif_state_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Select only the B4A-owned state fields from immutable 7F evidence."""
    keys = (
        "motif_id", "domain_id", "label", "centroid", "strength",
        "stability_score", "contributing_agents", "created_ts", "last_active_ts",
    )
    if any(key not in payload for key in keys):
        return None
    return {key: payload[key] for key in keys}


def _durable_fingerprint(connection: sqlite3.Connection) -> tuple[tuple[str, int], ...]:
    tables = (
        "objects", "object_revisions", "relationships", "relationship_revisions", "representations",
        "representation_current_state", "representation_payloads", "integrity_expectations",
        "integrity_measurements", "reconciliation_cases", "semantic_transitions", "operations",
        "legacy_admission_records", "memory_runtime_enumeration_orders", "maintenance_events",
    )
    available = {
        row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    return tuple(
        (table, connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
        for table in tables if table in available
    )


def _side_store_inventory() -> tuple[SideStoreReadinessItem, ...]:
    return (
        SideStoreReadinessItem("conflicts", SideStoreDisposition.RETAIN_EXTERNAL_UNCHANGED, EIDSideStoreReadiness.REQUIRES_SCOPE_CONTEXT, "external conflict registry remains owner"),
        SideStoreReadinessItem("anchors", SideStoreDisposition.RETAIN_EXTERNAL_UNCHANGED, EIDSideStoreReadiness.REQUIRES_SCOPE_CONTEXT, "identity-anchor history remains external"),
        SideStoreReadinessItem("affect_history", SideStoreDisposition.RETAIN_EXTERNAL_UNCHANGED, EIDSideStoreReadiness.REQUIRES_SCOPE_CONTEXT, "affect history remains external"),
        SideStoreReadinessItem("character_store", SideStoreDisposition.FUTURE_PARITY_REQUIRED, EIDSideStoreReadiness.REQUIRES_SCOPE_CONTEXT, "Character parity is excluded from B1"),
        SideStoreReadinessItem("proposals", SideStoreDisposition.MIGRATED_PRIMARY_STATE, EIDSideStoreReadiness.NO_EID_REFERENCE, "7F proposal effective-state admission is retained as primary state"),
        SideStoreReadinessItem("hivemind_collective", SideStoreDisposition.RETAIN_EXTERNAL_UNCHANGED, EIDSideStoreReadiness.REQUIRES_SCOPE_CONTEXT, "collective field and Hivemind remain external owners"),
        SideStoreReadinessItem("bridges", SideStoreDisposition.FUTURE_PARITY_REQUIRED, EIDSideStoreReadiness.REQUIRES_SCOPE_CONTEXT, "bridge parity is excluded from B1"),
        SideStoreReadinessItem("checkpoints", SideStoreDisposition.FUTURE_PARITY_REQUIRED, EIDSideStoreReadiness.NO_EID_REFERENCE, "checkpoint persistence is excluded from B1"),
        SideStoreReadinessItem("trajectory_evidence", SideStoreDisposition.FUTURE_PARITY_REQUIRED, EIDSideStoreReadiness.REQUIRES_SCOPE_CONTEXT, "trajectory evidence remains external"),
        SideStoreReadinessItem("deep_memory", SideStoreDisposition.MIGRATED_EVIDENCE_ONLY, EIDSideStoreReadiness.COMPATIBLE_WITH_NAMESPACED_EID, "7F deep captures remain non-READY evidence"),
        SideStoreReadinessItem("identity_overlays", SideStoreDisposition.MIGRATED_PRIMARY_STATE, EIDSideStoreReadiness.NO_EID_REFERENCE, "admitted identity definitions remain primary facts"),
        SideStoreReadinessItem("role_state", SideStoreDisposition.NOT_REQUIRED_FOR_CORE_RUNTIME_PROFILE, EIDSideStoreReadiness.NO_EID_REFERENCE, "role state is not required for the core profile"),
    )


def _b2_recommendation(items: tuple[ObjectRuntimeReadinessItem, ...]) -> str:
    if not items:
        return "NO_B2_ACTION_UNTIL_ADMITTED_CORE_OBJECTS_ARE_AVAILABLE"
    categories = {item.readiness for item in items}
    if ObjectRuntimeReadiness.SEMANTIC_FACTS_UNRESOLVED in categories:
        return "B2_SCOPE_GOVERNANCE_PROVENANCE_LIFECYCLE_NORMALIZATION_FIRST"
    if ObjectRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED in categories:
        return "B2_NORMALIZE_CURRENT_RUNTIME_FACTS_BEFORE_REPRESENTATIONS"
    if ObjectRuntimeReadiness.REPRESENTATION_BOOTSTRAP_REQUIRED in categories:
        return "B2_REPRESENTATION_BOOTSTRAP_AFTER_SEMANTIC_NORMALIZATION"
    return "NO_B2_ACTION_REQUIRED_FOR_CORE_OBJECTS"


__all__ = [
    "CoreRuntimeReadiness", "EIDSideStoreReadiness", "GovernanceEvidenceReadiness",
    "LegacyCaptureReadiness", "LegacyVectorStrategy", "LifecycleEvidenceReadiness",
    "MigrationRuntimeReadinessRequest", "MigrationRuntimeReadinessReport", "MigrationRuntimeScopePlan",
    "MotifRuntimeReadiness", "MotifRuntimeReadinessItem", "NativeMigrationRuntimeReadinessPreflight",
    "ObjectRuntimeReadiness", "ObjectRuntimeReadinessItem", "ProvenanceEvidenceReadiness",
    "ScopePlanReadiness", "SideStoreDisposition", "SideStoreReadinessItem",
]
