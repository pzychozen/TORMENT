"""Bounded B4A legacy-motif to native-runtime projection.

The legacy motif and its memberships remain immutable 7F evidence.  This
module is intentionally the only migration writer which may create the
separate native ``DERIVED_MOTIF`` baseline used by the A3B reader.
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
from ..compat_embedding_reader import NativeCompatEmbeddingReader
from ..errors import SubstrateIdempotencyConflict, SubstrateInvariantViolation
from ..ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from ..motifs import (
    MOTIF_ID_ALIAS_KIND, MotifState, NativeMotifService, _membership_state,
    _motif_object_state, _validate_state,
)
from ..objects import SubstrateTx, execute_semantic
from ..runtime_binding import NativeRepresentationLane
from ..schema import CORE_ROLE_STAGING, require_current_schema
from .motif_admission import LEGACY_DERIVED_MOTIF_OBJECT_KIND
from .character_seed_normalization import (
    CHARACTER_SEED_NORMALIZATION_OPERATION_KIND as _CHARACTER_B2_OPERATION_KIND,
    CHARACTER_SEED_NORMALIZATION_OUTPUT_ROLE as _CHARACTER_B2_OUTPUT_ROLE,
    CHARACTER_SEED_NORMALIZATION_TRANSITION_KIND as _CHARACTER_B2_TRANSITION_KIND,
)
from .runtime_readiness import MigrationRuntimeScopePlan, _scope_plan_digest, _validate_target_lane
from .snapshot import LegacyArtifact, LegacySnapshotManifest, load_snapshot_manifest, verify_snapshot


_CONTRACT = "TMS-MIGRATION-RUNTIME-MOTIF-PROJECTION-7G5B4A/1"
_OPERATION_KIND = "MIGRATION_RUNTIME_MOTIF_PROJECTION"
_TRANSITION_KIND = "MIGRATION_RUNTIME_MOTIF_PROJECTION"
_OUTPUT_MOTIF = "MIGRATION_RUNTIME_MOTIF_PROJECTION"
_OUTPUT_MEMBERSHIP = "MIGRATION_RUNTIME_MOTIF_PROJECTION_MEMBERSHIP"
_PREPARED = object()


class MigrationRuntimeMotifProjectionRefused(SubstrateInvariantViolation):
    """A stable, fail-closed B4A precondition refusal."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class MigrationRuntimeMotifProjectionRequest:
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
        if any(not isinstance(getattr(self, name), (str, Path)) or not str(getattr(self, name)).strip()
               for name in ("snapshot_root", "manifest_path")):
            raise ValueError("snapshot_root and manifest_path are required")


@dataclass(frozen=True, init=False)
class PreparedLegacyMotifRuntimeProjection:
    native_core_id: UUID
    legacy_snapshot_id: UUID
    legacy_source_namespace_id: UUID
    source_motif_object_id: UUID
    source_motif_revision_id: UUID
    source_operation_id: UUID
    source_transition_id: UUID
    runtime_motif_id: str
    workspace_id: str
    domain_id: str
    workspace_metadata_artifact_id: UUID
    workspace_metadata_digest: str
    workspace_provider: str
    workspace_model: str
    workspace_dimension: int
    target_lane: NativeRepresentationLane
    scope_plan_digest: str
    motif_identity_namespace_id: UUID
    membership_identity_namespace_id: UUID
    motif_alias_namespace_id: UUID
    target_semantic_scope_id: UUID
    state: MotifState
    state_digest: str
    member_eids: tuple[int, ...]
    member_object_ids: tuple[UUID, ...]
    member_revision_ids: tuple[UUID, ...]
    member_representation_ids: tuple[UUID, ...]
    member_scope_ids: tuple[UUID, ...]
    idempotency_namespace_id: UUID
    _marker: object = field(repr=False, compare=False)

    def __init__(self, *, _marker: object, **values: Any) -> None:
        if _marker is not _PREPARED:
            raise ValueError("projection plans must be prepared from verified durable evidence")
        for name, value in values.items():
            object.__setattr__(self, name, value)
        object.__setattr__(self, "_marker", _marker)


@dataclass(frozen=True)
class MigrationRuntimeMotifProjectionResult:
    source_motif_object_id: UUID
    source_motif_revision_id: UUID
    motif_object_id: UUID
    motif_revision_id: UUID
    transition_id: UUID
    operation_id: UUID
    membership_ids: tuple[UUID, ...]
    membership_revision_ids: tuple[UUID, ...]


class NativeMigrationRuntimeMotifProjectionService:
    """Publish one all-or-nothing, lane-preserving native motif baseline."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("projection requires an open sqlite connection")
        self._metadata = require_current_schema(connection)
        self._connection = connection
        self._motifs = NativeMotifService(connection)
        self._compat_reader = NativeCompatEmbeddingReader(connection)

    def project_lane_preserving_legacy_motif(
        self, request: MigrationRuntimeMotifProjectionRequest, *,
        _test_lose_response_after_commit: bool = False,
    ) -> MigrationRuntimeMotifProjectionResult:
        if not isinstance(request, MigrationRuntimeMotifProjectionRequest):
            raise ValueError("a MigrationRuntimeMotifProjectionRequest is required")
        self._reject_stale_retry(request)
        plan = self._prepare(request)
        intent = canonical_intent_text(_intent(plan))

        def resolver(operation_id: bytes) -> MigrationRuntimeMotifProjectionResult | None:
            return self._recorded_result(operation_id, plan)

        def mutate(tx: SubstrateTx) -> MigrationRuntimeMotifProjectionResult:
            # All externally supplied facts are reread while the writer owns
            # BEGIN IMMEDIATE; a prior B1 report is never write authority.
            fresh = self._prepare(request)
            if _intent(fresh) != _intent(plan):
                raise MigrationRuntimeMotifProjectionRefused("B4A_PREPARED_FACTS_CHANGED")
            return self._publish(tx, fresh)

        result = execute_semantic(
            self._connection, request.idempotency_namespace_id, request.idempotency_key,
            _OPERATION_KIND, intent, resolver, mutate,
        )
        if _test_lose_response_after_commit:
            raise RuntimeError("forced response loss after committed motif projection")
        return result

    def _reject_stale_retry(self, request: MigrationRuntimeMotifProjectionRequest) -> None:
        """Reject an obviously changed same-key request before source loading.

        A source artifact might itself no longer be admissible after the first
        commit.  Idempotency is still a stronger boundary than that later
        refusal: a changed operator request may not reuse the old key.
        """
        row = self._connection.execute(
            "SELECT canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), request.idempotency_key),
        ).fetchone()
        if row is None:
            return
        try:
            stored = json.loads(row[0])
        except (TypeError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("stored B4A projection intent is malformed") from exc
        expected_lane = [request.target_lane.provider, request.target_lane.model, request.target_lane.dimension,
                         request.target_lane.representation_class, request.target_lane.generation,
                         request.target_lane.derivation_contract_version, request.target_lane.encoding_id,
                         request.target_lane.dtype]
        expected = {
            "source_motif_object_id": str(request.expected_source_motif_object_id),
            "source_motif_revision_id": str(request.expected_source_motif_revision_id),
            "snapshot_id": str(request.legacy_snapshot_id),
            "source_namespace_id": str(request.legacy_source_namespace_id),
            "runtime_motif_id": request.runtime_motif_id,
            "target_lane": expected_lane,
            "scope_plan_digest": _scope_plan_digest(request.scope_plans),
        }
        if not isinstance(stored, dict) or any(stored.get(key) != value for key, value in expected.items()):
            raise SubstrateIdempotencyConflict("idempotency intent differs")

    def _prepare(self, request: MigrationRuntimeMotifProjectionRequest) -> PreparedLegacyMotifRuntimeProjection:
        _validate_target_lane(request.target_lane)
        # ``execute_semantic`` owns the revalidation transaction.  The schema
        # gate itself rightly refuses to run inside it, so use the already
        # qualified immutable metadata witness during that second read.
        metadata = self._metadata if self._connection.in_transaction else require_current_schema(self._connection)
        if native_id_from_bytes(metadata.core_id) != request.expected_native_core_id:
            raise MigrationRuntimeMotifProjectionRefused("B4A_NATIVE_CORE_ID_MISMATCH")
        if metadata.core_role != CORE_ROLE_STAGING:
            raise MigrationRuntimeMotifProjectionRefused("B4A_CORE_ROLE_NOT_STAGING")
        if self._connection.execute("SELECT deployment_state,referenced_core_id FROM deployment_metadata").fetchall() != [("LEGACY_ACTIVE", None)]:
            raise MigrationRuntimeMotifProjectionRefused("B4A_DEPLOYMENT_NOT_LEGACY_ACTIVE")
        manifest = load_snapshot_manifest(request.manifest_path)
        if manifest.legacy_snapshot_id != request.legacy_snapshot_id:
            raise MigrationRuntimeMotifProjectionRefused("B4A_SNAPSHOT_ID_MISMATCH")
        if manifest.legacy_source_namespace_id != request.legacy_source_namespace_id:
            raise MigrationRuntimeMotifProjectionRefused("B4A_SOURCE_NAMESPACE_MISMATCH")
        verify_snapshot(snapshot_root=request.snapshot_root, manifest=manifest)
        plan = _unique_plan(request.scope_plans, request.legacy_source_namespace_id)
        if plan.motif_domain_id is None:
            raise MigrationRuntimeMotifProjectionRefused("B4A_MOTIF_DOMAIN_PLAN_MISSING")
        if plan.motif_alias_namespace_id == request.legacy_source_namespace_id:
            raise MigrationRuntimeMotifProjectionRefused("B4A_ALIAS_SEPARATION_BLOCKED")
        _require_plan_references(self._connection, plan, request.idempotency_namespace_id)
        motif_locator = f"workspaces/{plan.workspace_id}/domains/{plan.motif_domain_id}/motifs.json"
        meta_locator = f"workspaces/{plan.workspace_id}/workspace_meta.json"
        motif_artifact = _unique_artifact(manifest, motif_locator, "B4A_SOURCE_MOTIF_ARTIFACT_UNQUALIFIED")
        meta_artifact = _unique_artifact(manifest, meta_locator, "B4A_MOTIF_GEOMETRY_LANE_UNQUALIFIED")
        _persisted_artifact(self._connection, manifest, motif_artifact, "B4A_SOURCE_MOTIF_ARTIFACT_UNQUALIFIED")
        _persisted_artifact(self._connection, manifest, meta_artifact, "B4A_MOTIF_GEOMETRY_LANE_UNQUALIFIED")
        raw_motif = _raw_motif(request.snapshot_root, motif_locator, request.runtime_motif_id)
        workspace = _workspace_lane(request.snapshot_root, meta_locator)
        if workspace != (request.target_lane.provider, request.target_lane.model, request.target_lane.dimension):
            raise MigrationRuntimeMotifProjectionRefused("B4A_MOTIF_GEOMETRY_LANE_UNQUALIFIED")
        source = self._source_facts(request, manifest, motif_artifact, raw_motif)
        if source["domain_id"] != plan.motif_domain_id:
            raise MigrationRuntimeMotifProjectionRefused("B4A_MOTIF_DOMAIN_WORKSPACE_MISMATCH")
        state = _state_from_raw(plan.target_semantic_scope_id, raw_motif)
        if state.domain_id != plan.motif_domain_id:
            raise MigrationRuntimeMotifProjectionRefused("B4A_MOTIF_DOMAIN_WORKSPACE_MISMATCH")
        if len(state.centroid) != request.target_lane.dimension:
            raise MigrationRuntimeMotifProjectionRefused("B4A_MOTIF_GEOMETRY_LANE_UNQUALIFIED")
        if source["stored_payload"] != {key: value for key, value in raw_motif.items() if key != "members"}:
            raise MigrationRuntimeMotifProjectionRefused("B4A_SOURCE_MOTIF_STATE_CONTRADICTORY")
        members = self._members(request, source, raw_motif)
        alias = self._connection.execute(
            "SELECT object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind=? AND alias_value=?",
            (native_id_to_bytes(plan.motif_alias_namespace_id), MOTIF_ID_ALIAS_KIND, request.runtime_motif_id),
        ).fetchall()
        existing_key = self._connection.execute(
            "SELECT 1 FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(request.idempotency_namespace_id), request.idempotency_key),
        ).fetchone()
        if alias and existing_key is None:
            raise MigrationRuntimeMotifProjectionRefused("B4A_TARGET_MOTIF_ALIAS_COLLISION")
        values: dict[str, Any] = {
            "native_core_id": request.expected_native_core_id,
            "legacy_snapshot_id": request.legacy_snapshot_id,
            "legacy_source_namespace_id": request.legacy_source_namespace_id,
            "source_motif_object_id": request.expected_source_motif_object_id,
            "source_motif_revision_id": request.expected_source_motif_revision_id,
            "source_operation_id": source["operation_id"], "source_transition_id": source["transition_id"],
            "runtime_motif_id": request.runtime_motif_id, "workspace_id": plan.workspace_id,
            "domain_id": plan.motif_domain_id, "workspace_metadata_artifact_id": meta_artifact.artifact_id,
            "workspace_metadata_digest": meta_artifact.digest_hex,
            "workspace_provider": workspace[0], "workspace_model": workspace[1], "workspace_dimension": workspace[2],
            "target_lane": request.target_lane, "scope_plan_digest": _scope_plan_digest(request.scope_plans),
            "motif_identity_namespace_id": plan.motif_identity_namespace_id,
            "membership_identity_namespace_id": plan.membership_identity_namespace_id,
            "motif_alias_namespace_id": plan.motif_alias_namespace_id,
            "target_semantic_scope_id": plan.target_semantic_scope_id, "state": state,
            "state_digest": hashlib.sha256(canonical_intent_text(state.payload()).encode()).hexdigest(),
            "member_eids": members["eids"], "member_object_ids": members["object_ids"],
            "member_revision_ids": members["revision_ids"], "member_representation_ids": members["representation_ids"],
            "member_scope_ids": members["scope_ids"], "idempotency_namespace_id": request.idempotency_namespace_id,
        }
        return PreparedLegacyMotifRuntimeProjection(**values, _marker=_PREPARED)

    def _source_facts(self, request: MigrationRuntimeMotifProjectionRequest, manifest: LegacySnapshotManifest,
                      artifact: LegacyArtifact, raw: dict[str, Any]) -> dict[str, Any]:
        rows = self._connection.execute(
            """
            SELECT o.object_id,o.current_revision_id,o.current_revision_ordinal,o.object_kind,
                   r.lineage_kind,r.payload_format,r.payload_text,t.transition_id,t.operation_id,
                   a.alias_value,b.legacy_snapshot_id,ar.legacy_artifact_id,ad.admission_status
              FROM legacy_object_aliases a JOIN objects o ON o.object_id=a.object_id
              JOIN object_revisions r ON r.object_id=o.object_id AND r.object_revision_id=o.current_revision_id
              JOIN semantic_transitions t ON t.transition_id=o.creating_transition_id
              JOIN legacy_admission_effects e ON e.transition_id=t.transition_id
              JOIN legacy_admission_records ad ON ad.admission_record_id=e.admission_record_id
              JOIN legacy_admission_batches b ON b.admission_batch_id=ad.admission_batch_id
              JOIN legacy_artifact_records ar ON ar.legacy_artifact_record_id=ad.legacy_artifact_record_id
             WHERE a.legacy_source_namespace_id=? AND a.alias_kind='MOTIF_ID' AND a.alias_value=?
            """, (native_id_to_bytes(request.legacy_source_namespace_id), request.runtime_motif_id),
        ).fetchall()
        if len(rows) != 1:
            raise MigrationRuntimeMotifProjectionRefused("B4A_SOURCE_MOTIF_ALIAS_NOT_UNIQUE")
        row = rows[0]
        expected = (native_id_to_bytes(request.expected_source_motif_object_id), native_id_to_bytes(request.expected_source_motif_revision_id), 1,
                    LEGACY_DERIVED_MOTIF_OBJECT_KIND, "LEGACY_PREDECESSOR_UNKNOWN", "JSON", "LEGACY_MOTIF_ADMISSION",
                    "LEGACY_ADMISSION", native_id_to_bytes(manifest.legacy_snapshot_id), native_id_to_bytes(artifact.artifact_id), "ADMITTED")
        actual = (row[0], row[1], row[2], row[3], row[4], row[5], self._transition_kind(row[7]), self._transition_origin(row[7]), row[10], row[11], row[12])
        if actual != expected:
            raise MigrationRuntimeMotifProjectionRefused("B4A_SOURCE_MOTIF_TOPOLOGY_UNQUALIFIED")
        output = self._connection.execute(
            """SELECT o.output_role,o.output_kind,o.object_id,o.object_revision_id,o.object_revision_ordinal,
                      e.object_revision_id,e.object_revision_ordinal
                 FROM operation_outputs o JOIN object_revision_effects e ON e.transition_id=?
                  AND e.object_id=o.object_id AND e.object_revision_id=o.object_revision_id
                  AND e.object_revision_ordinal=o.object_revision_ordinal
                WHERE o.operation_id=? AND o.output_ordinal=0""",
            (row[7], row[8]),
        ).fetchall()
        if output != [("LEGACY_MOTIF_ADMISSION", "OBJECT", row[0], row[1], 1, row[1], 1)]:
            raise MigrationRuntimeMotifProjectionRefused("B4A_SOURCE_MOTIF_TOPOLOGY_UNQUALIFIED")
        try:
            stored = json.loads(row[6])
        except (TypeError, json.JSONDecodeError) as exc:
            raise MigrationRuntimeMotifProjectionRefused("B4A_SOURCE_MOTIF_STATE_CONTRADICTORY") from exc
        if not isinstance(stored, dict) or stored.get("motif_id") != request.runtime_motif_id or raw.get("domain_id") != stored.get("domain_id"):
            raise MigrationRuntimeMotifProjectionRefused("B4A_SOURCE_MOTIF_STATE_CONTRADICTORY")
        return {"operation_id": UUID(bytes=row[8]), "transition_id": UUID(bytes=row[7]),
                "stored_payload": stored, "domain_id": stored["domain_id"]}

    def _transition_kind(self, transition_id: bytes) -> str:
        row = self._connection.execute("SELECT transition_kind FROM semantic_transitions WHERE transition_id=?", (transition_id,)).fetchone()
        return row[0] if row else ""

    def _transition_origin(self, transition_id: bytes) -> str:
        row = self._connection.execute("SELECT origin_kind FROM semantic_transitions WHERE transition_id=?", (transition_id,)).fetchone()
        return row[0] if row else ""

    def _members(self, request: MigrationRuntimeMotifProjectionRequest, source: dict[str, Any], raw: dict[str, Any]) -> dict[str, tuple[Any, ...]]:
        raw_eids = raw.get("members")
        if not isinstance(raw_eids, list) or not raw_eids or any(not isinstance(eid, int) or isinstance(eid, bool) or eid < 0 for eid in raw_eids):
            raise MigrationRuntimeMotifProjectionRefused("B4A_LEGACY_MEMBER_ORDER_UNRESOLVED")
        if len(set(raw_eids)) != len(raw_eids):
            raise MigrationRuntimeMotifProjectionRefused("B4A_LEGACY_MEMBER_ORDER_CONTRADICTORY")
        rows = self._connection.execute(
            """
            SELECT out.output_ordinal,out.relationship_id,out.relationship_revision_id,
                   h.current_revision_id,h.current_revision_ordinal,rr.lineage_kind,h.creating_transition_id,
                   h.relationship_kind,member.object_id,member.endpoint_semantic_scope_id
              FROM operation_outputs out JOIN relationship_revision_effects effect
                ON effect.transition_id=? AND effect.relationship_id=out.relationship_id
               AND effect.relationship_revision_id=out.relationship_revision_id AND effect.relationship_revision_ordinal=out.relationship_revision_ordinal
              JOIN relationships h ON h.relationship_id=out.relationship_id
              JOIN relationship_revisions rr ON rr.relationship_id=h.relationship_id AND rr.relationship_revision_id=h.current_revision_id
              JOIN relationship_revision_endpoints motif ON motif.relationship_revision_id=rr.relationship_revision_id AND motif.endpoint_ordinal=0 AND motif.endpoint_role='MOTIF' AND motif.binding_mode='IDENTITY'
              JOIN relationship_revision_endpoints member ON member.relationship_revision_id=rr.relationship_revision_id AND member.endpoint_ordinal=1 AND member.endpoint_role='MEMBER' AND member.binding_mode='IDENTITY'
             WHERE out.operation_id=? AND out.output_role=? AND out.output_kind='RELATIONSHIP'
               AND motif.object_id=? ORDER BY out.output_ordinal
            """, (native_id_to_bytes(source["transition_id"]), native_id_to_bytes(source["operation_id"]), _OUTPUT_LEGACY_MEMBERSHIP(), native_id_to_bytes(request.expected_source_motif_object_id)),
        ).fetchall()
        if len(rows) != len(raw_eids) or [row[0] for row in rows] != list(range(1, len(raw_eids) + 1)):
            raise MigrationRuntimeMotifProjectionRefused("B4A_LEGACY_MEMBER_ORDER_CONTRADICTORY")
        objects: list[UUID] = []; revisions: list[UUID] = []; representations: list[UUID] = []; scopes: list[UUID] = []
        for eid, row in zip(raw_eids, rows, strict=True):
            if row[2] != row[3] or row[4] != 1 or row[5] != "LEGACY_PREDECESSOR_UNKNOWN" or row[6] != native_id_to_bytes(source["transition_id"]) or row[7] != "MOTIF_MEMBERSHIP":
                raise MigrationRuntimeMotifProjectionRefused("B4A_SOURCE_MEMBERSHIP_EVIDENCE_CHANGED")
            aliases = self._connection.execute(
                "SELECT a.object_id,o.object_kind FROM legacy_object_aliases a JOIN objects o ON o.object_id=a.object_id WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID' AND a.alias_value=?",
                (native_id_to_bytes(request.legacy_source_namespace_id), str(eid)),
            ).fetchall()
            if len(aliases) != 1 or aliases[0][0] != row[8] or aliases[0][1] != "LEGACY_CORE_NODE":
                raise MigrationRuntimeMotifProjectionRefused("B4A_MEMBER_EID_UNRESOLVED")
            current = self._connection.execute(
                """SELECT o.current_revision_id,o.current_revision_ordinal,r.effective_semantic_scope_id,
                          r.lineage_kind,r.predecessor_revision_id,r.predecessor_revision_ordinal,
                          predecessor.lineage_kind,t.transition_kind,t.origin_kind,operation.operation_kind,
                          output.output_role,output.output_kind,output.object_id,output.object_revision_id,
                          output.object_revision_ordinal
                     FROM objects o JOIN object_revisions r ON r.object_id=o.object_id
                      AND r.object_revision_id=o.current_revision_id AND r.revision_ordinal=o.current_revision_ordinal
                     JOIN object_revisions predecessor ON predecessor.object_id=o.object_id AND predecessor.object_revision_id=r.predecessor_revision_id
                     JOIN object_revision_effects effect ON effect.object_id=o.object_id AND effect.object_revision_id=r.object_revision_id AND effect.object_revision_ordinal=r.revision_ordinal
                     JOIN semantic_transitions t ON t.transition_id=effect.transition_id
                     JOIN operations operation ON operation.operation_id=t.operation_id
                     JOIN operation_outputs output ON output.operation_id=operation.operation_id
                    WHERE o.object_id=?""", (row[8],)
            ).fetchone()
            ordinary_topology = (
                2, "NATIVE_ORDINARY", 1, "LEGACY_PREDECESSOR_UNKNOWN",
                "MIGRATION_RUNTIME_NORMALIZATION", "NATIVE", "MIGRATION_RUNTIME_NORMALIZATION",
                "MIGRATION_RUNTIME_NORMALIZATION", "OBJECT", row[8], 2,
            )
            character_topology = (
                2, "NATIVE_ORDINARY", 1, "LEGACY_PREDECESSOR_UNKNOWN",
                _CHARACTER_B2_TRANSITION_KIND, "NATIVE", _CHARACTER_B2_OPERATION_KIND,
                _CHARACTER_B2_OUTPUT_ROLE, "OBJECT", row[8], 2,
            )
            if current is None or (
                current[1], current[3], current[5], current[6], current[7], current[8], current[9],
                current[10], current[11], current[12], current[14]
            ) not in {ordinary_topology, character_topology} or current[0] != current[13]:
                raise MigrationRuntimeMotifProjectionRefused("B4A_MEMBER_NOT_RUNTIME_SEMANTIC")
            object_id = UUID(bytes=row[8])
            try:
                qualified = self._compat_reader.read_current(object_id, expected_dimension=request.target_lane.dimension)
            except SubstrateInvariantViolation as exc:
                raise MigrationRuntimeMotifProjectionRefused("B4A_MEMBER_COMPAT_REPRESENTATION_UNQUALIFIED") from exc
            if qualified is None:
                raise MigrationRuntimeMotifProjectionRefused("B4A_MEMBER_COMPAT_REPRESENTATION_UNQUALIFIED")
            # This is precisely NativeMotifService._require_compatible_member's
            # rule: member endpoints retain the *current* member scope, not
            # the historical 7F membership evidence scope.
            objects.append(object_id); revisions.append(UUID(bytes=current[0])); representations.append(qualified.representation_id); scopes.append(UUID(bytes=current[2]))
        return {"eids": tuple(raw_eids), "object_ids": tuple(objects), "revision_ids": tuple(revisions),
                "representation_ids": tuple(representations), "scope_ids": tuple(scopes)}

    def _publish(self, tx: SubstrateTx, plan: PreparedLegacyMotifRuntimeProjection) -> MigrationRuntimeMotifProjectionResult:
        service = self._motifs
        transition_id = _new()
        motif_id, motif_revision_id = _new(), _new()
        service._insert_motif_creation(tx, motif_id, motif_revision_id, transition_id, _motif_object_state(plan.motif_identity_namespace_id, plan.state))
        memberships: list[tuple[bytes, bytes]] = []
        for member_id, expected_scope in zip(plan.member_object_ids, plan.member_scope_ids, strict=True):
            actual_scope = service._require_compatible_member(tx, member_id)
            if actual_scope != expected_scope:
                raise MigrationRuntimeMotifProjectionRefused("B4A_MEMBER_SCOPE_CHANGED")
            relationship_id, revision_id = _new(), _new()
            service._insert_membership(tx, relationship_id, revision_id, transition_id, _membership_state(
                plan.membership_identity_namespace_id, plan.target_semantic_scope_id, motif_id, actual_scope, member_id
            ))
            memberships.append((relationship_id, revision_id))
        tx.execute("INSERT INTO legacy_object_aliases VALUES (?,?,?,?)", (
            native_id_to_bytes(plan.motif_alias_namespace_id), MOTIF_ID_ALIAS_KIND, plan.runtime_motif_id, motif_id,
        ))
        tx.execute("INSERT INTO semantic_transitions VALUES (?,?,?,?,0)", (transition_id, tx.operation_id, _TRANSITION_KIND, "NATIVE"))
        tx.execute("INSERT INTO object_revision_effects VALUES (?,?,?,1)", (transition_id, motif_id, motif_revision_id))
        tx.execute("""INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,object_id,object_revision_id,object_revision_ordinal)
                      VALUES (?,?,?,'OBJECT',?,?,1)""", (tx.operation_id, 0, _OUTPUT_MOTIF, motif_id, motif_revision_id))
        tx.execute("UPDATE objects SET current_revision_id=?,current_revision_ordinal=1 WHERE object_id=?", (motif_revision_id, motif_id))
        for ordinal, (relationship_id, revision_id) in enumerate(memberships, start=1):
            tx.execute("INSERT INTO relationship_revision_effects VALUES (?,?,?,1)", (transition_id, relationship_id, revision_id))
            tx.execute("""INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,relationship_id,relationship_revision_id,relationship_revision_ordinal)
                          VALUES (?,?,?,'RELATIONSHIP',?,?,1)""", (tx.operation_id, ordinal, _OUTPUT_MEMBERSHIP, relationship_id, revision_id))
            tx.execute("UPDATE relationships SET current_revision_id=?,current_revision_ordinal=1 WHERE relationship_id=?", (revision_id, relationship_id))
        tx.transitions.append(transition_id); tx.published.append((motif_id, motif_revision_id, 1)); tx.relationship_published.extend((relationship_id, revision_id, 1) for relationship_id, revision_id in memberships)
        result = self._recorded_result(tx.operation_id, plan)
        if result is None:
            raise SubstrateInvariantViolation("B4A projection result was not durably published")
        return result

    def _recorded_result(self, operation_id: bytes, plan: PreparedLegacyMotifRuntimeProjection) -> MigrationRuntimeMotifProjectionResult | None:
        rows = self._connection.execute(
            """SELECT t.transition_id,t.transition_kind,t.origin_kind,o.output_ordinal,o.output_role,o.output_kind,
                      o.object_id,o.object_revision_id,o.object_revision_ordinal,o.relationship_id,o.relationship_revision_id,o.relationship_revision_ordinal
                 FROM semantic_transitions t JOIN operation_outputs o ON o.operation_id=t.operation_id
                WHERE t.operation_id=? ORDER BY o.output_ordinal""", (operation_id,)
        ).fetchall()
        if len(rows) != len(plan.member_object_ids) + 1 or not rows:
            return None
        first = rows[0]
        if first[1:9] != (_TRANSITION_KIND, "NATIVE", 0, _OUTPUT_MOTIF, "OBJECT", first[6], first[7], 1):
            return None
        if first[6] is None or first[7] is None:
            return None
        memberships: list[UUID] = []; revisions: list[UUID] = []
        for ordinal, row in enumerate(rows[1:], start=1):
            if row[0] != first[0] or row[3:6] != (ordinal, _OUTPUT_MEMBERSHIP, "RELATIONSHIP") or row[9] is None or row[10] is None or row[11] != 1:
                return None
            memberships.append(UUID(bytes=row[9])); revisions.append(UUID(bytes=row[10]))
        return MigrationRuntimeMotifProjectionResult(plan.source_motif_object_id, plan.source_motif_revision_id,
            UUID(bytes=first[6]), UUID(bytes=first[7]), UUID(bytes=first[0]), UUID(bytes=operation_id), tuple(memberships), tuple(revisions))


def _unique_plan(plans: tuple[MigrationRuntimeScopePlan, ...], source: UUID) -> MigrationRuntimeScopePlan:
    selected = [plan for plan in plans if plan.legacy_source_namespace_id == source]
    if len(selected) != 1:
        raise MigrationRuntimeMotifProjectionRefused("B4A_RUNTIME_SCOPE_PLAN_AMBIGUOUS" if selected else "B4A_RUNTIME_SCOPE_PLAN_MISSING")
    return selected[0]


def _require_plan_references(connection: sqlite3.Connection, plan: MigrationRuntimeScopePlan, idempotency_namespace_id: UUID) -> None:
    values = (("identity_namespaces", "identity_namespace_id", plan.target_identity_namespace_id),
              ("identity_namespaces", "identity_namespace_id", plan.motif_identity_namespace_id),
              ("identity_namespaces", "identity_namespace_id", plan.membership_identity_namespace_id),
              ("semantic_scopes", "semantic_scope_id", plan.target_semantic_scope_id),
              ("legacy_source_namespaces", "legacy_source_namespace_id", plan.motif_alias_namespace_id),
              ("idempotency_namespaces", "idempotency_namespace_id", idempotency_namespace_id))
    if any(connection.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)).fetchone() is None for table, column, value in values):
        raise MigrationRuntimeMotifProjectionRefused("B4A_TARGET_NAMESPACE_OR_SCOPE_MISSING")


def _unique_artifact(manifest: LegacySnapshotManifest, locator: str, code: str) -> LegacyArtifact:
    rows = [artifact for artifact in manifest.artifacts if artifact.observed_relative_locator == locator]
    if len(rows) != 1:
        raise MigrationRuntimeMotifProjectionRefused(code)
    return rows[0]


def _persisted_artifact(connection: sqlite3.Connection, manifest: LegacySnapshotManifest, artifact: LegacyArtifact, code: str) -> None:
    rows = connection.execute("SELECT legacy_snapshot_id,observed_locator,digest_algorithm,digest_value FROM legacy_artifacts WHERE legacy_artifact_id=?", (native_id_to_bytes(artifact.artifact_id),)).fetchall()
    expected = (native_id_to_bytes(manifest.legacy_snapshot_id), artifact.observed_relative_locator, artifact.digest_algorithm, bytes.fromhex(artifact.digest_hex))
    if rows != [expected]:
        raise MigrationRuntimeMotifProjectionRefused(code)


def _snapshot_file(root: str | Path, locator: str) -> Path:
    base = Path(root).resolve(); result = (base / locator).resolve()
    try:
        result.relative_to(base)
    except ValueError as exc:
        raise MigrationRuntimeMotifProjectionRefused("B4A_SNAPSHOT_LOCATOR_INVALID") from exc
    return result


def _raw_motif(root: str | Path, locator: str, motif_id: str) -> dict[str, Any]:
    try:
        document = json.loads(_snapshot_file(root, locator).read_text(encoding="utf-8"))
        raw = document["motifs"][motif_id]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise MigrationRuntimeMotifProjectionRefused("B4A_SOURCE_MOTIF_ARTIFACT_UNQUALIFIED") from exc
    if not isinstance(document, dict) or not isinstance(document.get("motifs"), dict) or not isinstance(raw, dict):
        raise MigrationRuntimeMotifProjectionRefused("B4A_SOURCE_MOTIF_ARTIFACT_UNQUALIFIED")
    return raw


def _workspace_lane(root: str | Path, locator: str) -> tuple[str, str, int]:
    try:
        value = json.loads(_snapshot_file(root, locator).read_text(encoding="utf-8"))
        provider, model, dimension = value["embed_provider"], value["embed_model"], value["embed_dim"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise MigrationRuntimeMotifProjectionRefused("B4A_MOTIF_GEOMETRY_LANE_UNQUALIFIED") from exc
    if not isinstance(value, dict) or not isinstance(provider, str) or not provider or not isinstance(model, str) or not model or not isinstance(dimension, int) or isinstance(dimension, bool) or dimension < 1:
        raise MigrationRuntimeMotifProjectionRefused("B4A_MOTIF_GEOMETRY_LANE_UNQUALIFIED")
    return provider, model, dimension


def _state_from_raw(scope: UUID, raw: dict[str, Any]) -> MotifState:
    try:
        state = MotifState(scope, raw["motif_id"], raw["domain_id"], raw["label"], tuple(raw["centroid"]), raw["strength"], raw["stability_score"], tuple(raw["contributing_agents"]), raw["created_ts"], raw["last_active_ts"])
        _validate_state(state)
    except (KeyError, TypeError, ValueError) as exc:
        raise MigrationRuntimeMotifProjectionRefused("B4A_LEGACY_MOTIF_STATE_INVALID") from exc
    return state


def _intent(plan: PreparedLegacyMotifRuntimeProjection) -> dict[str, Any]:
    return {"contract": _CONTRACT, "source_motif_object_id": str(plan.source_motif_object_id), "source_motif_revision_id": str(plan.source_motif_revision_id), "source_operation_id": str(plan.source_operation_id), "source_transition_id": str(plan.source_transition_id), "snapshot_id": str(plan.legacy_snapshot_id), "source_namespace_id": str(plan.legacy_source_namespace_id), "workspace_metadata_artifact_id": str(plan.workspace_metadata_artifact_id), "workspace_metadata_digest": plan.workspace_metadata_digest, "workspace_lane": [plan.workspace_provider, plan.workspace_model, plan.workspace_dimension], "target_lane": [plan.target_lane.provider, plan.target_lane.model, plan.target_lane.dimension, plan.target_lane.representation_class, plan.target_lane.generation, plan.target_lane.derivation_contract_version, plan.target_lane.encoding_id, plan.target_lane.dtype], "scope_plan_digest": plan.scope_plan_digest, "motif_identity_namespace_id": str(plan.motif_identity_namespace_id), "membership_identity_namespace_id": str(plan.membership_identity_namespace_id), "motif_alias_namespace_id": str(plan.motif_alias_namespace_id), "target_semantic_scope_id": str(plan.target_semantic_scope_id), "runtime_motif_id": plan.runtime_motif_id, "state": plan.state.payload(), "state_digest": plan.state_digest, "member_eids": list(plan.member_eids), "member_object_ids": [str(item) for item in plan.member_object_ids], "member_revision_ids": [str(item) for item in plan.member_revision_ids], "member_representation_ids": [str(item) for item in plan.member_representation_ids]}


def _new() -> bytes:
    return native_id_to_bytes(generate_native_id())


def _OUTPUT_LEGACY_MEMBERSHIP() -> str:
    return "LEGACY_MOTIF_MEMBERSHIP_ADMISSION"


__all__ = ["MigrationRuntimeMotifProjectionRefused", "MigrationRuntimeMotifProjectionRequest", "MigrationRuntimeMotifProjectionResult", "NativeMigrationRuntimeMotifProjectionService", "PreparedLegacyMotifRuntimeProjection"]
