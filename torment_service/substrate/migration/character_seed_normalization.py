"""Character-only R1 -> R2 normalization from a frozen writer witness.

This does not loosen ordinary B2: ordinary rows still require exact
``ProvenanceV1`` evidence through ``runtime_normalization``.  The only
alternative is a seed_canon row whose external CharacterStore definition and
legacy writer-shaped payload pass ``CharacterSeedWitness`` exactly.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3
from typing import Any
from uuid import UUID

from torment_service.lifecycle import LifecycleStatus

from ..canonical_intent import canonical_intent_text
from ..character_seed_witness import CharacterSeedWitness
from ..errors import SubstrateIdempotencyConflict, SubstrateInvariantViolation
from ..ids import generate_native_id, native_id_to_bytes
from ..object_revision_governance import NativeMemoryGovernanceFacts, _insert_published_governance_for_qualification
from ..objects import SubstrateTx, execute_semantic
from ..provenance import NativeProvenanceRecord
from ..schema import CORE_ROLE_STAGING, require_current_schema
from .runtime_normalization import (
    MigrationRuntimeNormalizationRequest, MigrationRuntimeNormalizationResult,
    NativeMigrationRuntimeNormalizationService, _exact_scope_plan,
    _governance_from_payload, _lifecycle_from_payload, _normalised_runtime_payload,
)
from .snapshot import load_snapshot_manifest, verify_snapshot


CHARACTER_SEED_NORMALIZATION_OPERATION_KIND = "MIGRATION_CHARACTER_SEED_NORMALIZATION"
CHARACTER_SEED_NORMALIZATION_TRANSITION_KIND = "MIGRATION_CHARACTER_SEED_NORMALIZATION"
CHARACTER_SEED_NORMALIZATION_OUTPUT_ROLE = "MIGRATION_CHARACTER_SEED_NORMALIZATION"
_CONTRACT = "TMS-MIGRATION-CHARACTER-SEED-NORMALIZATION-7G5E2/1"


class MigrationCharacterSeedNormalizationRefused(SubstrateInvariantViolation):
    """Fail closed when a legacy row cannot prove Character seed authorship."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class MigrationCharacterSeedNormalizationRequest:
    """One explicit seed witness and one admitted R1 source; no inference."""

    ordinary_request: MigrationRuntimeNormalizationRequest
    witness: CharacterSeedWitness

    def __post_init__(self) -> None:
        if not isinstance(self.ordinary_request, MigrationRuntimeNormalizationRequest):
            raise ValueError("ordinary_request must be MigrationRuntimeNormalizationRequest")
        if not isinstance(self.witness, CharacterSeedWitness):
            raise ValueError("witness must be CharacterSeedWitness")
        if self.ordinary_request.eid not in self.witness.seed_eids:
            raise ValueError("normalization EID is not one of the witnessed seed EIDs")


@dataclass(frozen=True)
class PreparedCharacterSeedNormalization:
    source: dict[str, Any]
    payload: dict[str, Any]
    payload_json: str
    payload_digest: str
    governance: NativeMemoryGovernanceFacts
    lifecycle: LifecycleStatus
    provenance: NativeProvenanceRecord
    concept_index: int


class NativeMigrationCharacterSeedNormalizationService:
    """One Character-seed semantic successor, idempotent per R1 EID."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("Character seed normalization requires an open sqlite connection")
        require_current_schema(connection)
        self._connection = connection
        # Reuse B2's evidence-only R1/snapshot/scope validation, never its
        # ordinary ProvenanceV1 translation path.
        self._ordinary = NativeMigrationRuntimeNormalizationService(connection)

    def normalize_character_seed(
        self, request: MigrationCharacterSeedNormalizationRequest,
        *, _test_lose_response_after_commit: bool = False,
    ) -> MigrationRuntimeNormalizationResult:
        if not isinstance(request, MigrationCharacterSeedNormalizationRequest):
            raise ValueError("request must be MigrationCharacterSeedNormalizationRequest")
        self._reject_changed_retry_contract(request)
        prepared = self._prepare(request, require_current=False)
        base = request.ordinary_request
        result = execute_semantic(
            self._connection, base.idempotency_namespace_id, base.idempotency_key,
            CHARACTER_SEED_NORMALIZATION_OPERATION_KIND, _intent(request, prepared), self._result_for_operation,
            lambda tx: self._commit(tx, request, prepared),
        )
        if _test_lose_response_after_commit:
            raise RuntimeError("forced response loss after committed Character seed normalization")
        return result

    def _prepare(self, request: MigrationCharacterSeedNormalizationRequest, *, require_current: bool) -> PreparedCharacterSeedNormalization:
        base, witness = request.ordinary_request, request.witness
        core_id, role = self._ordinary._current_core_facts()
        if core_id != base.expected_native_core_id or role != CORE_ROLE_STAGING:
            raise MigrationCharacterSeedNormalizationRefused("CHARACTER_SEED_NATIVE_CORE_NOT_STAGING")
        deployment = self._connection.execute("SELECT deployment_state,referenced_core_id FROM deployment_metadata").fetchall()
        if deployment != [("LEGACY_ACTIVE", None)]:
            raise MigrationCharacterSeedNormalizationRefused("CHARACTER_SEED_DEPLOYMENT_NOT_LEGACY_ACTIVE")
        manifest = load_snapshot_manifest(base.manifest_path)
        if manifest.legacy_snapshot_id != base.legacy_snapshot_id or manifest.legacy_source_namespace_id != base.legacy_source_namespace_id:
            raise MigrationCharacterSeedNormalizationRefused("CHARACTER_SEED_SNAPSHOT_MISMATCH")
        verify_snapshot(snapshot_root=base.snapshot_root, manifest=manifest)
        self._ordinary._verify_persisted_snapshot(manifest)
        plan = _exact_scope_plan(base)
        self._ordinary._verify_scope_plan_references(plan)
        if plan.idempotency_namespace_id != base.idempotency_namespace_id:
            raise MigrationCharacterSeedNormalizationRefused("CHARACTER_SEED_IDEMPOTENCY_NAMESPACE_MISMATCH")
        source = self._ordinary._admitted_r1(base, manifest)
        if source["identity_namespace_id"] != plan.target_identity_namespace_id:
            raise MigrationCharacterSeedNormalizationRefused("CHARACTER_SEED_OBJECT_NAMESPACE_MISMATCH")
        if require_current and (source["current_revision_id"] != base.expected_revision_id or source["current_revision_ordinal"] != 1):
            raise MigrationCharacterSeedNormalizationRefused("CHARACTER_SEED_CURRENT_R1_REQUIRED")
        raw = self._ordinary._verified_snapshot_row(base, manifest, source)
        payload = _normalised_runtime_payload(raw)
        index = _validate_seed_payload(payload, witness, base.eid)
        lifecycle = _lifecycle_from_payload(payload)
        governance = _governance_from_payload(payload, raw)
        payload_json = canonical_intent_text(payload)
        return PreparedCharacterSeedNormalization(
            source, payload, payload_json, hashlib.sha256(payload_json.encode("utf-8")).hexdigest(),
            governance, lifecycle, witness.provenance_for_concept(index), index,
        )

    def _commit(self, tx: SubstrateTx, request: MigrationCharacterSeedNormalizationRequest,
                prepared: PreparedCharacterSeedNormalization) -> MigrationRuntimeNormalizationResult:
        fresh = self._prepare(request, require_current=True)
        if _fingerprint(fresh) != _fingerprint(prepared):
            raise MigrationCharacterSeedNormalizationRefused("CHARACTER_SEED_PREPARED_FACTS_CHANGED")
        base = request.ordinary_request
        provenance_id = native_id_to_bytes(generate_native_id())
        tx.execute(
            """INSERT INTO provenance_records(
                   provenance_id,origin_kind,source_channel,source_role,derivation_status,
                   uncertainty_state,source_time_ns,capture_time_ns,memory_role,descriptive_notes
               ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (provenance_id, *_provenance_values(prepared.provenance)),
        )
        revision_id, transition_id = native_id_to_bytes(generate_native_id()), native_id_to_bytes(generate_native_id())
        object_id = native_id_to_bytes(prepared.source["object_id"])
        lifecycle = prepared.lifecycle
        tx.execute(
            """INSERT INTO object_revisions(
                   object_revision_id,object_id,revision_ordinal,lineage_kind,
                   predecessor_revision_id,predecessor_revision_ordinal,effective_semantic_scope_id,
                   existence_state,lifecycle_state,lifecycle_authoritative,lifecycle_actor,lifecycle_via,
                   lifecycle_set_at_ns,governance_state,authority_category,provenance_id,payload_format,
                   payload_text,created_at_ns
               ) VALUES (?, ?, 2, 'NATIVE_ORDINARY', ?, 1, ?, 'EXISTS', ?, ?, ?, ?, ?,
                         'EXPLICIT', 'NOT_APPLICABLE', ?, 'JSON', ?, 0)""",
            (
                revision_id, object_id, native_id_to_bytes(_uuid(prepared.source["current_revision_id"])),
                native_id_to_bytes(_exact_scope_plan(base).target_semantic_scope_id), lifecycle.state.value.upper(),
                int(lifecycle.is_authoritative_on_row), lifecycle.set_by.actor.value,
                lifecycle.set_by.via.value, lifecycle.set_by.at * 1_000_000_000,
                provenance_id, prepared.payload_json,
            ),
        )
        tx.execute("UPDATE objects SET current_revision_id=?,current_revision_ordinal=2 WHERE object_id=?", (revision_id, object_id))
        _insert_published_governance_for_qualification(
            tx, object_id=object_id, object_revision_id=revision_id, object_revision_ordinal=2,
            facts=prepared.governance,
        )
        tx.execute("INSERT INTO semantic_transitions VALUES (?,?,?,?,0)", (
            transition_id, tx.operation_id, CHARACTER_SEED_NORMALIZATION_TRANSITION_KIND, "NATIVE"
        ))
        tx.execute("INSERT INTO object_revision_effects VALUES (?,?,?,2)", (transition_id, object_id, revision_id))
        tx.execute(
            """INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,
                   object_id,object_revision_id,object_revision_ordinal)
               VALUES (?,?,?,'OBJECT',?,?,2)""",
            (tx.operation_id, 0, CHARACTER_SEED_NORMALIZATION_OUTPUT_ROLE, object_id, revision_id),
        )
        tx.transitions.append(transition_id)
        tx.published.append((object_id, revision_id, 2))
        return MigrationRuntimeNormalizationResult(
            _uuid(prepared.source["object_id"]), base.eid, base.expected_revision_id, 1,
            UUID(bytes=revision_id), 2, prepared.source["runtime_order_ordinal"], UUID(bytes=provenance_id),
            UUID(bytes=transition_id), UUID(bytes=tx.operation_id), prepared.payload_digest,
        )

    def _reject_changed_retry_contract(self, request: MigrationCharacterSeedNormalizationRequest) -> None:
        base = request.ordinary_request
        row = self._connection.execute(
            "SELECT canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(base.idempotency_namespace_id), base.idempotency_key),
        ).fetchone()
        if row is None:
            return
        try:
            intent = json.loads(row[0])
        except (TypeError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("stored Character seed normalization intent is malformed") from exc
        if not isinstance(intent, dict) or intent.get("retry_contract") != _retry_contract(request):
            raise SubstrateIdempotencyConflict("Character seed normalization idempotency intent differs")

    def _result_for_operation(self, operation_id: bytes) -> MigrationRuntimeNormalizationResult | None:
        rows = self._connection.execute(
            """SELECT out.object_id,out.object_revision_id,out.object_revision_ordinal,t.transition_id,
                      r.predecessor_revision_id,r.predecessor_revision_ordinal,r.provenance_id,
                      a.alias_value,ordering.runtime_ordinal,op.canonical_intent_json
                 FROM operations op JOIN semantic_transitions t ON t.operation_id=op.operation_id
                 JOIN operation_outputs out ON out.operation_id=op.operation_id
                 JOIN object_revisions r ON r.object_id=out.object_id AND r.object_revision_id=out.object_revision_id
                   AND r.revision_ordinal=out.object_revision_ordinal
                 JOIN legacy_object_aliases a ON a.object_id=out.object_id AND a.alias_kind='EID'
                 JOIN memory_runtime_enumeration_orders ordering ON ordering.object_id=out.object_id
                   AND ordering.legacy_source_namespace_id=a.legacy_source_namespace_id
                WHERE op.operation_id=? AND t.transition_kind=? AND out.output_ordinal=0
                  AND out.output_role=? AND out.output_kind='OBJECT'""",
            (operation_id, CHARACTER_SEED_NORMALIZATION_TRANSITION_KIND, CHARACTER_SEED_NORMALIZATION_OUTPUT_ROLE),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise SubstrateInvariantViolation("Character seed normalization recovery result is ambiguous")
        row = rows[0]
        try:
            digest = json.loads(row[9])["normalized_payload_digest"]
            if not isinstance(digest, str) or len(digest) != 64:
                raise ValueError
            return MigrationRuntimeNormalizationResult(
                UUID(bytes=row[0]), int(row[7]), UUID(bytes=row[4]), int(row[5]), UUID(bytes=row[1]),
                int(row[2]), int(row[8]), UUID(bytes=row[6]), UUID(bytes=row[3]), UUID(bytes=operation_id), digest,
            )
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("stored Character seed normalization result is malformed") from exc


def _validate_seed_payload(payload: dict[str, Any], witness: CharacterSeedWitness, eid: int) -> int:
    try:
        index = witness.seed_eids.index(eid)
    except ValueError as exc:
        raise MigrationCharacterSeedNormalizationRefused("CHARACTER_SEED_EID_NOT_WITNESSED") from exc
    if (
        payload.get("type") != "seed_canon" or payload.get("mtype", "seed_canon") != "seed_canon"
        or payload.get("canon") is not True or payload.get("memory_class") != "core"
        or payload.get("seed_id") != witness.seed_id or payload.get("character_name") != witness.character_name
        or payload.get("seed_concept_index") != index or payload.get("summary") != witness.concept_summaries[index]
        or payload.get("tier") != "core_identity" or payload.get("user_id") != witness.agent_id
        or not _exact_float(payload.get("strength"), .95) or not _exact_float(payload.get("confidence"), .95)
        or not _exact_float(payload.get("half_life"), float(witness.seed_definition["core_half_life"]))
        or "provenance" in payload
    ):
        raise MigrationCharacterSeedNormalizationRefused("CHARACTER_SEED_WRITER_WITNESS_MISMATCH")
    return index


def _retry_contract(request: MigrationCharacterSeedNormalizationRequest) -> dict[str, Any]:
    base, witness = request.ordinary_request, request.witness
    return {
        "legacy_snapshot_id": str(base.legacy_snapshot_id),
        "legacy_source_namespace_id": str(base.legacy_source_namespace_id),
        "native_core_id": str(base.expected_native_core_id), "eid": base.eid,
        "expected_revision_id": str(base.expected_revision_id),
        "idempotency_namespace_id": str(base.idempotency_namespace_id),
        "seed_id": witness.seed_id, "seed_definition_digest": witness.seed_definition_digest,
        "seed_witness_digest": witness.witness_digest,
    }


def _intent(request: MigrationCharacterSeedNormalizationRequest, prepared: PreparedCharacterSeedNormalization) -> str:
    return canonical_intent_text({
        "kind": CHARACTER_SEED_NORMALIZATION_OPERATION_KIND, "contract": _CONTRACT, "retry_contract": _retry_contract(request),
        "normalized_payload_digest": prepared.payload_digest, "concept_index": prepared.concept_index,
        "governance": list(prepared.governance.as_storage_tuple()),
        "provenance": {"origin_kind": prepared.provenance.origin_kind, "source_channel": prepared.provenance.source_channel,
                       "source_role": prepared.provenance.source_role, "derivation_status": prepared.provenance.derivation_status,
                       "uncertainty_state": prepared.provenance.uncertainty_state,
                       "memory_role": prepared.provenance.memory_role, "descriptive_notes": prepared.provenance.descriptive_notes},
        "lifecycle": prepared.lifecycle.to_dict(),
    })


def _fingerprint(prepared: PreparedCharacterSeedNormalization) -> str:
    return canonical_intent_text({
        "source": str(prepared.source["object_id"]), "current": str(prepared.source["current_revision_id"]),
        "payload": prepared.payload_digest, "governance": list(prepared.governance.as_storage_tuple()),
        "lifecycle": prepared.lifecycle.to_dict(), "provenance": _provenance_values(prepared.provenance),
        "concept_index": prepared.concept_index,
    })


def _uuid(value: Any) -> UUID:
    if not isinstance(value, UUID):
        raise SubstrateInvariantViolation("Character seed normalization source identity is invalid")
    return value


def _provenance_values(value: NativeProvenanceRecord) -> tuple[object, ...]:
    return (
        value.origin_kind, value.source_channel, value.source_role, value.derivation_status,
        value.uncertainty_state, value.source_time_ns, value.capture_time_ns, value.memory_role,
        value.descriptive_notes,
    )


def _exact_float(value: Any, expected: float) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and float(value) == expected


__all__ = [
    "MigrationCharacterSeedNormalizationRefused", "MigrationCharacterSeedNormalizationRequest",
    "NativeMigrationCharacterSeedNormalizationService", "PreparedCharacterSeedNormalization",
]
