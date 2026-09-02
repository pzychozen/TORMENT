"""Bounded B4C import of a target-compatible legacy zero-member motif.

This coordinator validates frozen 7F current-state evidence and delegates the
single native object publication to :class:`NativeMotifService`.  It neither
creates a generic empty motif nor derives, embeds, or re-geometrizes a
centroid.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import UUID

from ..canonical_intent import canonical_intent_text
from ..errors import SubstrateIdempotencyConflict, SubstrateInvariantViolation
from ..ids import native_id_from_bytes, native_id_to_bytes
from ..motifs import (
    MIGRATION_ZERO_MEMBER_MOTIF_BASELINE_OPERATION_KIND,
    MigrationZeroMemberMotifBaselineEvidence,
    MotifState,
    NativeMotifMutationResult,
    NativeMotifService,
    _validate_state,
)
from ..runtime_binding import NativeRepresentationLane
from ..schema import CORE_ROLE_STAGING, require_current_schema
from . import runtime_motif_projection as _b4a
from .runtime_readiness import MigrationRuntimeScopePlan, _scope_plan_digest, _validate_target_lane
from .snapshot import LegacyArtifact, LegacySnapshotManifest, load_snapshot_manifest, verify_snapshot


_CONTRACT = "TMS-MIGRATION-ZERO-MEMBER-MOTIF-PROJECTION-B4C/1"
_PREPARED = object()


class MigrationRuntimeZeroMemberMotifProjectionRefused(SubstrateInvariantViolation):
    """Stable B4C refusal; no source gap is repaired or inferred."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class MigrationRuntimeZeroMemberMotifProjectionRequest:
    snapshot_root: str | Path
    manifest_path: str | Path
    legacy_snapshot_id: UUID
    legacy_source_namespace_id: UUID
    expected_native_core_id: UUID
    runtime_motif_id: str
    expected_source_motif_object_id: UUID
    expected_source_motif_revision_id: UUID
    scope_plans: tuple[MigrationRuntimeScopePlan, ...]
    target_lane: NativeRepresentationLane
    idempotency_namespace_id: UUID
    idempotency_key: str

    def __post_init__(self) -> None:
        for name in (
            "legacy_snapshot_id", "legacy_source_namespace_id", "expected_native_core_id",
            "expected_source_motif_object_id", "expected_source_motif_revision_id",
            "idempotency_namespace_id",
        ):
            if not isinstance(getattr(self, name), UUID):
                raise ValueError(f"{name} must be a UUID")
        if not isinstance(self.runtime_motif_id, str) or not self.runtime_motif_id:
            raise ValueError("runtime_motif_id must be non-empty text")
        if not isinstance(self.scope_plans, tuple) or any(
            not isinstance(item, MigrationRuntimeScopePlan) for item in self.scope_plans
        ):
            raise ValueError("scope_plans must be a tuple of MigrationRuntimeScopePlan values")
        if not isinstance(self.target_lane, NativeRepresentationLane):
            raise ValueError("target_lane must be a NativeRepresentationLane")
        if not isinstance(self.idempotency_key, str) or not self.idempotency_key:
            raise ValueError("idempotency_key must be non-empty text")
        if any(
            not isinstance(getattr(self, name), (str, Path))
            or not str(getattr(self, name)).strip()
            for name in ("snapshot_root", "manifest_path")
        ):
            raise ValueError("snapshot_root and manifest_path are required")


@dataclass(frozen=True, init=False)
class PreparedLegacyZeroMemberMotifProjection:
    source_motif_object_id: UUID
    source_motif_revision_id: UUID
    state: MotifState
    state_digest: str
    evidence: MigrationZeroMemberMotifBaselineEvidence
    _marker: object = field(repr=False, compare=False)

    def __init__(self, *, _marker: object, **values: Any) -> None:
        if _marker is not _PREPARED:
            raise ValueError("B4C plans must be prepared from verified durable evidence")
        for name, value in values.items():
            object.__setattr__(self, name, value)
        object.__setattr__(self, "_marker", _marker)


@dataclass(frozen=True)
class MigrationRuntimeZeroMemberMotifProjectionResult:
    source_motif_object_id: UUID
    source_motif_revision_id: UUID
    motif_object_id: UUID
    motif_revision_id: UUID
    transition_id: UUID
    operation_id: UUID


class NativeMigrationRuntimeZeroMemberMotifProjectionService:
    """Qualify and import exactly one active B4C zero-member baseline."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("B4C projection requires an open sqlite connection")
        self._metadata = require_current_schema(connection)
        self._connection = connection
        # B4A remains the sole parser/identity authority for the admitted
        # source motif topology.  B4C supplies only its distinct zero-member
        # proof and target-compatible aggregate-state qualification.
        self._source_evidence = _b4a.NativeMigrationRuntimeMotifProjectionService(connection)
        self._motifs = NativeMotifService(connection)

    def project_target_compatible_zero_member_motif(
        self,
        request: MigrationRuntimeZeroMemberMotifProjectionRequest,
        *,
        _test_lose_response_after_commit: bool = False,
    ) -> MigrationRuntimeZeroMemberMotifProjectionResult:
        if not isinstance(request, MigrationRuntimeZeroMemberMotifProjectionRequest):
            raise ValueError("a MigrationRuntimeZeroMemberMotifProjectionRequest is required")
        self._reject_stale_retry(request)
        plan = self._prepare(request)

        def revalidate() -> tuple[MotifState, MigrationZeroMemberMotifBaselineEvidence]:
            fresh = self._prepare(request)
            if _intent(fresh) != _intent(plan):
                raise MigrationRuntimeZeroMemberMotifProjectionRefused(
                    "B4C_PREPARED_FACTS_CHANGED"
                )
            return fresh.state, fresh.evidence

        native = self._motifs.publish_migration_zero_member_baseline(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=request.idempotency_key,
            state=plan.state,
            evidence=plan.evidence,
            revalidate=revalidate,
        )
        if _test_lose_response_after_commit:
            raise RuntimeError("forced response loss after committed B4C projection")
        return _result(plan, native)

    def _reject_stale_retry(
        self, request: MigrationRuntimeZeroMemberMotifProjectionRequest,
    ) -> None:
        row = self._connection.execute(
            "SELECT canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), request.idempotency_key),
        ).fetchone()
        if row is None:
            return
        try:
            stored = json.loads(row[0])
        except (TypeError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("stored B4C projection intent is malformed") from exc
        evidence = stored.get("evidence") if isinstance(stored, dict) else None
        if (
            not isinstance(stored, dict)
            or stored.get("kind") != MIGRATION_ZERO_MEMBER_MOTIF_BASELINE_OPERATION_KIND
            or not isinstance(evidence, dict)
            or any(evidence.get(key) != value for key, value in _request_identity(request).items())
        ):
            raise SubstrateIdempotencyConflict("idempotency intent differs")

    def _prepare(
        self,
        request: MigrationRuntimeZeroMemberMotifProjectionRequest,
    ) -> PreparedLegacyZeroMemberMotifProjection:
        _validate_target_lane(request.target_lane)
        metadata = self._metadata if self._connection.in_transaction else require_current_schema(self._connection)
        if native_id_from_bytes(metadata.core_id) != request.expected_native_core_id:
            raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_NATIVE_CORE_ID_MISMATCH")
        if metadata.core_role != CORE_ROLE_STAGING:
            raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_CORE_ROLE_NOT_STAGING")
        if self._connection.execute(
            "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
        ).fetchall() != [("LEGACY_ACTIVE", None)]:
            raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_DEPLOYMENT_NOT_LEGACY_ACTIVE")
        manifest = load_snapshot_manifest(request.manifest_path)
        if manifest.legacy_snapshot_id != request.legacy_snapshot_id:
            raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_SNAPSHOT_ID_MISMATCH")
        if manifest.legacy_source_namespace_id != request.legacy_source_namespace_id:
            raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_SOURCE_NAMESPACE_MISMATCH")
        verify_snapshot(snapshot_root=request.snapshot_root, manifest=manifest)
        scope = _unique_plan(request.scope_plans, request.legacy_source_namespace_id)
        if scope.motif_domain_id is None:
            raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_MOTIF_DOMAIN_PLAN_MISSING")
        if scope.motif_alias_namespace_id == request.legacy_source_namespace_id:
            raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_ALIAS_SEPARATION_BLOCKED")
        _require_plan_references(self._connection, scope, request.idempotency_namespace_id)
        motif_locator = f"workspaces/{scope.workspace_id}/domains/{scope.motif_domain_id}/motifs.json"
        metadata_locator = f"workspaces/{scope.workspace_id}/workspace_meta.json"
        motif_artifact = _unique_artifact(
            manifest, motif_locator, "B4C_SOURCE_MOTIF_ARTIFACT_UNQUALIFIED",
        )
        metadata_artifact = _unique_artifact(
            manifest, metadata_locator, "B4C_TARGET_IDENTITY_UNQUALIFIED",
        )
        _persisted_artifact(
            self._connection, manifest, motif_artifact, "B4C_SOURCE_MOTIF_ARTIFACT_UNQUALIFIED",
        )
        _persisted_artifact(
            self._connection, manifest, metadata_artifact, "B4C_TARGET_IDENTITY_UNQUALIFIED",
        )
        raw = _raw_motif(request.snapshot_root, motif_locator, request.runtime_motif_id)
        source_lane = _workspace_lane(request.snapshot_root, metadata_locator)
        target_lane = _lane_value(request.target_lane)
        if tuple(source_lane) != target_lane[:3]:
            raise MigrationRuntimeZeroMemberMotifProjectionRefused(
                "B4C_TARGET_GEOMETRY_LANE_UNQUALIFIED"
            )
        try:
            source = self._source_evidence._source_facts(
                request, manifest, motif_artifact, raw,
            )
        except _b4a.MigrationRuntimeMotifProjectionRefused as exc:
            raise MigrationRuntimeZeroMemberMotifProjectionRefused(
                "B4C_SOURCE_MOTIF_TOPOLOGY_UNQUALIFIED"
            ) from exc
        if source["domain_id"] != scope.motif_domain_id:
            raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_MOTIF_DOMAIN_WORKSPACE_MISMATCH")
        state = _state_from_qualified_raw(scope.target_semantic_scope_id, raw)
        if state.domain_id != scope.motif_domain_id or len(state.centroid) != target_lane[2]:
            raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_TARGET_GEOMETRY_LANE_UNQUALIFIED")
        if source["stored_payload"] != state.payload() or source["stored_payload"] != {
            key: value for key, value in raw.items() if key != "members"
        }:
            raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_SOURCE_MOTIF_STATE_CONTRADICTORY")
        zero_membership_digest = _zero_source_membership_digest(
            self._connection, request, source, raw,
        )
        alias = self._connection.execute(
            "SELECT object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value=?",
            (native_id_to_bytes(scope.motif_alias_namespace_id), request.runtime_motif_id),
        ).fetchall()
        existing = self._connection.execute(
            "SELECT 1 FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), request.idempotency_key),
        ).fetchone()
        if alias and existing is None:
            raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_TARGET_MOTIF_ALIAS_COLLISION")
        state_digest = _digest(state.payload())
        evidence = MigrationZeroMemberMotifBaselineEvidence(
            native_core_id=request.expected_native_core_id,
            legacy_snapshot_id=request.legacy_snapshot_id,
            legacy_source_namespace_id=request.legacy_source_namespace_id,
            source_motif_object_id=request.expected_source_motif_object_id,
            source_motif_revision_id=request.expected_source_motif_revision_id,
            source_operation_id=source["operation_id"],
            source_transition_id=source["transition_id"],
            source_motif_artifact_id=motif_artifact.artifact_id,
            source_motif_artifact_digest=motif_artifact.digest_hex,
            workspace_metadata_artifact_id=metadata_artifact.artifact_id,
            workspace_metadata_digest=metadata_artifact.digest_hex,
            runtime_motif_id=request.runtime_motif_id,
            source_geometry_lane=tuple(source_lane),
            target_lane_identity=target_lane,
            scope_plan_digest=_scope_plan_digest(request.scope_plans),
            motif_identity_namespace_id=scope.motif_identity_namespace_id,
            membership_identity_namespace_id=scope.membership_identity_namespace_id,
            motif_alias_namespace_id=scope.motif_alias_namespace_id,
            target_semantic_scope_id=scope.target_semantic_scope_id,
            source_state_digest=state_digest,
            source_membership_digest=zero_membership_digest,
            source_member_count=0,
        )
        return PreparedLegacyZeroMemberMotifProjection(
            _marker=_PREPARED,
            source_motif_object_id=request.expected_source_motif_object_id,
            source_motif_revision_id=request.expected_source_motif_revision_id,
            state=state,
            state_digest=state_digest,
            evidence=evidence,
        )


def _unique_plan(
    plans: tuple[MigrationRuntimeScopePlan, ...], source_namespace_id: UUID,
) -> MigrationRuntimeScopePlan:
    selected = [item for item in plans if item.legacy_source_namespace_id == source_namespace_id]
    if len(selected) != 1:
        raise MigrationRuntimeZeroMemberMotifProjectionRefused(
            "B4C_RUNTIME_SCOPE_PLAN_AMBIGUOUS" if selected else "B4C_RUNTIME_SCOPE_PLAN_MISSING"
        )
    return selected[0]


def _require_plan_references(
    connection: sqlite3.Connection,
    plan: MigrationRuntimeScopePlan,
    idempotency_namespace_id: UUID,
) -> None:
    values = (
        ("identity_namespaces", "identity_namespace_id", plan.target_identity_namespace_id),
        ("identity_namespaces", "identity_namespace_id", plan.motif_identity_namespace_id),
        ("identity_namespaces", "identity_namespace_id", plan.membership_identity_namespace_id),
        ("semantic_scopes", "semantic_scope_id", plan.target_semantic_scope_id),
        ("legacy_source_namespaces", "legacy_source_namespace_id", plan.motif_alias_namespace_id),
        ("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id),
    )
    if any(
        connection.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)).fetchone() is None
        for table, column, value in values
    ):
        raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_TARGET_NAMESPACE_OR_SCOPE_MISSING")


def _unique_artifact(
    manifest: LegacySnapshotManifest, locator: str, code: str,
) -> LegacyArtifact:
    rows = [item for item in manifest.artifacts if item.observed_relative_locator == locator]
    if len(rows) != 1:
        raise MigrationRuntimeZeroMemberMotifProjectionRefused(code)
    return rows[0]


def _persisted_artifact(
    connection: sqlite3.Connection,
    manifest: LegacySnapshotManifest,
    artifact: LegacyArtifact,
    code: str,
) -> None:
    rows = connection.execute(
        "SELECT legacy_snapshot_id,observed_locator,digest_algorithm,digest_value FROM legacy_artifacts WHERE legacy_artifact_id=?",
        (native_id_to_bytes(artifact.artifact_id),),
    ).fetchall()
    expected = (
        native_id_to_bytes(manifest.legacy_snapshot_id),
        artifact.observed_relative_locator,
        artifact.digest_algorithm,
        bytes.fromhex(artifact.digest_hex),
    )
    if rows != [expected]:
        raise MigrationRuntimeZeroMemberMotifProjectionRefused(code)


def _raw_motif(root: str | Path, locator: str, motif_id: str) -> dict[str, Any]:
    try:
        return _b4a._raw_motif(root, locator, motif_id)
    except _b4a.MigrationRuntimeMotifProjectionRefused as exc:
        raise MigrationRuntimeZeroMemberMotifProjectionRefused(
            "B4C_SOURCE_MOTIF_ARTIFACT_UNQUALIFIED"
        ) from exc


def _workspace_lane(root: str | Path, locator: str) -> tuple[str, str, int]:
    try:
        return _b4a._workspace_lane(root, locator)
    except _b4a.MigrationRuntimeMotifProjectionRefused as exc:
        raise MigrationRuntimeZeroMemberMotifProjectionRefused(
            "B4C_TARGET_IDENTITY_UNQUALIFIED"
        ) from exc


def _state_from_qualified_raw(scope_id: UUID, raw: dict[str, Any]) -> MotifState:
    fields = {
        "motif_id", "domain_id", "label", "centroid", "strength", "stability_score",
        "contributing_agents", "created_ts", "last_active_ts", "derivation_metadata", "members",
    }
    try:
        state = MotifState(
            scope_id,
            raw["motif_id"],
            raw["domain_id"],
            raw["label"],
            tuple(raw["centroid"]),
            raw["strength"],
            raw["stability_score"],
            tuple(raw["contributing_agents"]),
            raw["created_ts"],
            raw["last_active_ts"],
            raw.get("derivation_metadata"),
            {key: value for key, value in raw.items() if key not in fields},
        )
        _validate_state(state)
    except (KeyError, TypeError, ValueError) as exc:
        raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_LEGACY_MOTIF_STATE_INVALID") from exc
    return state


def _zero_source_membership_digest(
    connection: sqlite3.Connection,
    request: MigrationRuntimeZeroMemberMotifProjectionRequest,
    source: dict[str, Any],
    raw: dict[str, Any],
) -> str:
    if raw.get("members") != []:
        raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_SOURCE_MEMBERS_NOT_EXACTLY_ZERO")
    output_rows = connection.execute(
        """
        SELECT output_ordinal,output_role,output_kind,object_id,object_revision_id,
               object_revision_ordinal,relationship_id,relationship_revision_id,
               relationship_revision_ordinal
          FROM operation_outputs
         WHERE operation_id=?
         ORDER BY output_ordinal
        """,
        (native_id_to_bytes(source["operation_id"]),),
    ).fetchall()
    expected = [
        (
            0,
            "LEGACY_MOTIF_ADMISSION",
            "OBJECT",
            native_id_to_bytes(request.expected_source_motif_object_id),
            native_id_to_bytes(request.expected_source_motif_revision_id),
            1,
            None,
            None,
            None,
        )
    ]
    if output_rows != expected:
        raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_SOURCE_ZERO_MEMBER_EVIDENCE_CHANGED")
    if connection.execute(
        "SELECT 1 FROM relationship_revision_effects WHERE transition_id=?",
        (native_id_to_bytes(source["transition_id"]),),
    ).fetchone() is not None or connection.execute(
        "SELECT 1 FROM relationships WHERE creating_transition_id=?",
        (native_id_to_bytes(source["transition_id"]),),
    ).fetchone() is not None:
        raise MigrationRuntimeZeroMemberMotifProjectionRefused("B4C_SOURCE_ZERO_MEMBER_EVIDENCE_CHANGED")
    return _digest(
        {
            "raw_member_eids": [],
            "source_operation_id": str(source["operation_id"]),
            "source_transition_id": str(source["transition_id"]),
            "source_membership_output_count": 0,
            "source_membership_effect_count": 0,
            "source_created_membership_count": 0,
        }
    )


def _lane_value(lane: NativeRepresentationLane) -> tuple[str, str, int, str, int, str, str, str]:
    return (
        lane.provider, lane.model, lane.dimension, lane.representation_class,
        lane.generation, lane.derivation_contract_version, lane.encoding_id, lane.dtype,
    )


def _request_identity(
    request: MigrationRuntimeZeroMemberMotifProjectionRequest,
) -> dict[str, Any]:
    return {
        "source_motif_object_id": str(request.expected_source_motif_object_id),
        "source_motif_revision_id": str(request.expected_source_motif_revision_id),
        "snapshot_id": str(request.legacy_snapshot_id),
        "source_namespace_id": str(request.legacy_source_namespace_id),
        "runtime_motif_id": request.runtime_motif_id,
        "target_lane_identity": list(_lane_value(request.target_lane)),
        "scope_plan_digest": _scope_plan_digest(request.scope_plans),
    }


def _intent(plan: PreparedLegacyZeroMemberMotifProjection) -> dict[str, Any]:
    return {"state": plan.state.intent(), "evidence": plan.evidence.intent()}


def _result(
    plan: PreparedLegacyZeroMemberMotifProjection,
    native: NativeMotifMutationResult,
) -> MigrationRuntimeZeroMemberMotifProjectionResult:
    return MigrationRuntimeZeroMemberMotifProjectionResult(
        plan.source_motif_object_id,
        plan.source_motif_revision_id,
        native.motif_object_id,
        native.motif_revision_id,
        native.transition_id,
        native.operation_id,
    )


def _digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_intent_text(value).encode("utf-8")).hexdigest()


__all__ = [
    "MigrationRuntimeZeroMemberMotifProjectionRefused",
    "MigrationRuntimeZeroMemberMotifProjectionRequest",
    "MigrationRuntimeZeroMemberMotifProjectionResult",
    "NativeMigrationRuntimeZeroMemberMotifProjectionService",
    "PreparedLegacyZeroMemberMotifProjection",
]
