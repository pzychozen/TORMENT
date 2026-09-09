"""Additive P3 carrier for P2-anchored Character seed witnesses.

The ordinary P3 source carrier predates Character recovery and must remain
immutable.  This module deliberately stores a successor record beside it.  A
seed definition's raw bytes are consumed only while composing that successor:
the durable record retains the existing :class:`CharacterSeedWitness`
descriptor and the P2 observation identity, never a second Character model.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping
from uuid import UUID

from ..canonical_intent import canonical_intent_text
from ..character_seed_witness import CharacterSeedWitness, CharacterSeedWitnessRefused
from .root_admission_description import ExternalOwnerObservation, ExternalOwnerObservationKind
from .root_scope import RootScopeKey, RootScopeKind


_RECORD_NAME = "p3_character_seed_witness_domain_derivation_continuation.json"
_LEGACY_RECORD_NAME = "p3_character_seed_witness_continuation.json"
_SCHEMA = "TORMENT_ROOT_P3_CHARACTER_SEED_WITNESS_DOMAIN_DERIVATION_CONTINUATION"
_VERSION = 1
_AGGREGATE_COMMITMENT_OPENING = "AGGREGATE_COMMITMENT_OPENING"
_CHARACTER_DOMAIN_DERIVATION_LAW = "UNIQUE_BOUNDED_CHARACTER_WITNESS_DOMAIN_V1"
_CHARACTER_SEMANTIC_WITNESS_FIELDS = (
    "workspace_id",
    "agent_id",
    "domain_id",
    "seed_definition",
    "seed_definition_compatibility",
    "derived_owner_agent_id",
    "lifecycle_compatibility",
    "seed_definition_digest",
    "seed_id",
    "character_name",
    "seed_text",
    "seed_eids",
    "seed_motif_id",
    "seed_motif_member_eids",
    "seed_motif_seed_eids",
    "concept_summaries",
)


class RootP3CharacterWitnessContinuationRefused(ValueError):
    """The narrow P2-to-P3 Character witness bridge is not exact."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _character_witness_semantically_equivalent(
    historical_descriptor_witness: CharacterSeedWitness,
    freshly_rederived_witness: CharacterSeedWitness,
) -> bool:
    """Compare two already-qualified Character witnesses across digest generations.

    ``CharacterSeedWitness`` owns validation of a descriptor's historical
    checksum forms.  P3 owns only this narrow bridge from that accepted
    descriptor to a freshly derived frozen-byte witness.  Every semantic fact
    must agree; the checksum-generation ``witness_digest`` is intentionally
    the sole excluded field.
    """

    return (
        isinstance(historical_descriptor_witness, CharacterSeedWitness)
        and isinstance(freshly_rederived_witness, CharacterSeedWitness)
        and all(
            getattr(historical_descriptor_witness, field)
            == getattr(freshly_rederived_witness, field)
            for field in _CHARACTER_SEMANTIC_WITNESS_FIELDS
        )
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_intent_text(value).encode("utf-8")).hexdigest()


def _sha256_text(value: str, code: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise RootP3CharacterWitnessContinuationRefused(code)
    try:
        int(value, 16)
    except ValueError as exc:
        raise RootP3CharacterWitnessContinuationRefused(code) from exc
    return value


@dataclass(frozen=True)
class RootP3ExternalOwnerObservationAuthority:
    """The opened P2 aggregate and only the Character tuple(s) it proved."""

    envelope_c_digest: str
    external_owner_observation_aggregate: str
    opened_character_observations: tuple[ExternalOwnerObservation, ...]
    proof: str = _AGGREGATE_COMMITMENT_OPENING

    def __post_init__(self) -> None:
        _sha256_text(self.envelope_c_digest, "P3_CHARACTER_ENVELOPE_C_INVALID")
        _sha256_text(
            self.external_owner_observation_aggregate,
            "P3_CHARACTER_EXTERNAL_OWNER_AGGREGATE_INVALID",
        )
        if self.proof != _AGGREGATE_COMMITMENT_OPENING:
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_OBSERVATION_PROOF_INVALID")
        if not isinstance(self.opened_character_observations, tuple) or not self.opened_character_observations:
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_OPENED_OBSERVATIONS_REQUIRED")
        if any(
            not isinstance(item, ExternalOwnerObservation)
            or item.owner_kind is not ExternalOwnerObservationKind.CHARACTER
            for item in self.opened_character_observations
        ):
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_OPENED_OBSERVATION_INVALID")
        keys = [item.canonical_key for item in self.opened_character_observations]
        if len(set(keys)) != len(keys):
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_OPENED_OBSERVATION_DUPLICATE")

    def observation_for(self, *, workspace_id: str, seed_id: str) -> ExternalOwnerObservation:
        matches = [
            item for item in self.opened_character_observations
            if item.workspace_id == workspace_id and item.observation_key == f"seed:{seed_id}"
        ]
        if len(matches) != 1:
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_P2_OBSERVATION_MISSING")
        return matches[0]


@dataclass(frozen=True)
class RootP3CharacterWitnessInput:
    """Ephemeral P3 composition input for one private Character seed scope."""

    scope_key: RootScopeKey
    legacy_source_namespace_id: UUID
    seed_definition_bytes: bytes
    descriptor_payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.scope_key, RootScopeKey) or self.scope_key.scope_kind is not RootScopeKind.PRIVATE:
            raise ValueError("Character witness input requires a private RootScopeKey")
        if not isinstance(self.legacy_source_namespace_id, UUID):
            raise ValueError("legacy_source_namespace_id must be UUID")
        if not isinstance(self.seed_definition_bytes, bytes) or not self.seed_definition_bytes:
            raise ValueError("seed_definition_bytes must be non-empty bytes")
        if not isinstance(self.descriptor_payload, Mapping):
            raise ValueError("descriptor_payload must be a mapping")


@dataclass(frozen=True)
class RootP3CharacterDomainCandidateEvidence:
    """One P2-authorized, P3-frozen motif domain considered for Character only."""

    domain_id: str
    p2_manifest_evidence_identity_digest: str
    p3_snapshot_id: UUID
    p3_motif_artifact_id: UUID
    p3_motif_artifact_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.domain_id, str) or not self.domain_id:
            raise ValueError("Character candidate domain_id must be non-empty text")
        _sha256_text(
            self.p2_manifest_evidence_identity_digest,
            "P3_CHARACTER_DOMAIN_CANDIDATE_P2_IDENTITY_INVALID",
        )
        if not isinstance(self.p3_snapshot_id, UUID) or not isinstance(self.p3_motif_artifact_id, UUID):
            raise ValueError("Character candidate snapshot and artifact identities must be UUID")
        _sha256_text(
            self.p3_motif_artifact_digest,
            "P3_CHARACTER_DOMAIN_CANDIDATE_MOTIF_DIGEST_INVALID",
        )

    def identity_payload(self) -> dict[str, str]:
        return {
            "domain_id": self.domain_id,
            "p2_manifest_evidence_identity_digest": self.p2_manifest_evidence_identity_digest,
            "p3_snapshot_id": str(self.p3_snapshot_id),
            "p3_motif_artifact_id": str(self.p3_motif_artifact_id),
            "p3_motif_artifact_digest": self.p3_motif_artifact_digest,
        }


@dataclass(frozen=True)
class RootP3CharacterDomainDerivation:
    """The unique frozen candidate proved by the existing Character witness."""

    scope_key: RootScopeKey
    domain_id: str
    candidate_evidence: tuple[RootP3CharacterDomainCandidateEvidence, ...]
    candidate_evidence_digest: str
    witness_digest: str
    freshly_rederived_witness: CharacterSeedWitness
    law: str = _CHARACTER_DOMAIN_DERIVATION_LAW

    def __post_init__(self) -> None:
        if not isinstance(self.scope_key, RootScopeKey) or self.scope_key.scope_kind is not RootScopeKind.PRIVATE:
            raise ValueError("Character domain derivation requires a private RootScopeKey")
        if not isinstance(self.domain_id, str) or not self.domain_id:
            raise ValueError("Character domain derivation requires non-empty domain_id")
        if self.law != _CHARACTER_DOMAIN_DERIVATION_LAW:
            raise ValueError("Character domain derivation law is invalid")
        if not isinstance(self.candidate_evidence, tuple) or not self.candidate_evidence or any(
            not isinstance(item, RootP3CharacterDomainCandidateEvidence)
            for item in self.candidate_evidence
        ):
            raise ValueError("Character domain derivation requires candidate evidence")
        if tuple(sorted(item.domain_id for item in self.candidate_evidence)) != tuple(
            item.domain_id for item in self.candidate_evidence
        ) or len({item.domain_id for item in self.candidate_evidence}) != len(self.candidate_evidence):
            raise ValueError("Character domain candidate evidence must be unique and ordered")
        _sha256_text(self.candidate_evidence_digest, "P3_CHARACTER_DOMAIN_CANDIDATE_EVIDENCE_INVALID")
        _sha256_text(self.witness_digest, "P3_CHARACTER_DOMAIN_WITNESS_DIGEST_INVALID")
        if not isinstance(self.freshly_rederived_witness, CharacterSeedWitness):
            raise ValueError("Character domain derivation requires a fresh Character witness")
        if (
            self.freshly_rederived_witness.workspace_id != self.scope_key.workspace_id
            or self.freshly_rederived_witness.agent_id != (self.scope_key.agent_id or "")
            or self.freshly_rederived_witness.domain_id != self.domain_id
            or self.freshly_rederived_witness.witness_digest != self.witness_digest
        ):
            raise ValueError("Character domain derivation fresh witness disagrees with scope")
        expected = _sha256_value({
            "law": self.law,
            "scope_key": self.scope_key.identity_payload(),
            "candidate_evidence": [item.identity_payload() for item in self.candidate_evidence],
        })
        if self.candidate_evidence_digest != expected:
            raise ValueError("Character domain candidate evidence digest disagrees with candidates")
        if self.domain_id not in {item.domain_id for item in self.candidate_evidence}:
            raise ValueError("Character domain must be one of its frozen candidates")

    def carrier_payload(self) -> dict[str, Any]:
        return {
            "character_domain_id": self.domain_id,
            "character_domain_derivation_law": self.law,
            "character_domain_candidate_evidence": [
                item.identity_payload() for item in self.candidate_evidence
            ],
            "character_domain_candidate_evidence_digest": self.candidate_evidence_digest,
        }


@dataclass(frozen=True)
class RootP3CharacterWitnessBinding:
    """Validated P2 anchor plus the existing immutable Character descriptor."""

    scope_key: RootScopeKey
    legacy_source_namespace_id: UUID
    seed_observation_key: str
    seed_observation_digest: str
    witness: CharacterSeedWitness
    domain_derivation: RootP3CharacterDomainDerivation

    def carrier_payload(self) -> dict[str, Any]:
        payload = {
            "scope_key": self.scope_key.identity_payload(),
            "legacy_source_namespace_id": str(self.legacy_source_namespace_id),
            "seed_observation_key": self.seed_observation_key,
            "seed_observation_digest": self.seed_observation_digest,
            "character_witness": self.witness.descriptor_payload(),
        }
        payload.update(self.domain_derivation.carrier_payload())
        return payload


def validate_character_witness_inputs(
    *,
    authority: RootP3ExternalOwnerObservationAuthority | None,
    inputs: tuple[RootP3CharacterWitnessInput, ...],
    scope_facts: Mapping[RootScopeKey, tuple[UUID, str | None]],
    domain_derivations: Mapping[RootScopeKey, RootP3CharacterDomainDerivation],
) -> dict[RootScopeKey, RootP3CharacterWitnessBinding]:
    """Validate P2 bytes, existing descriptor, and frozen private P3 topology."""

    if not inputs:
        return {}
    if authority is None:
        raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_P2_AUTHORITY_REQUIRED")
    result: dict[RootScopeKey, RootP3CharacterWitnessBinding] = {}
    for item in inputs:
        if not isinstance(item, RootP3CharacterWitnessInput) or item.scope_key in result:
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_WITNESS_SCOPE_DUPLICATE")
        facts = scope_facts.get(item.scope_key)
        if facts is None:
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_WITNESS_SCOPE_MISSING")
        namespace_id, _generic_domain_hint = facts
        if namespace_id != item.legacy_source_namespace_id:
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_WITNESS_NAMESPACE_MISMATCH")
        derivation = domain_derivations.get(item.scope_key)
        if derivation is None:
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_WITNESS_DOMAIN_UNRESOLVED")
        domain_id = derivation.domain_id
        try:
            raw_definition = json.loads(item.seed_definition_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_SEED_BYTES_INVALID") from exc
        try:
            witness = CharacterSeedWitness.from_descriptor_payload(
                workspace_id=item.scope_key.workspace_id,
                agent_id=item.scope_key.agent_id or "",
                domain_id=domain_id,
                value=item.descriptor_payload,
            )
        except CharacterSeedWitnessRefused as exc:
            raise RootP3CharacterWitnessContinuationRefused(exc.code) from exc
        if not witness.matches_raw_seed_definition(raw_definition):
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_DESCRIPTOR_SEED_BYTES_MISMATCH")
        observation = authority.observation_for(
            workspace_id=item.scope_key.workspace_id, seed_id=witness.seed_id,
        )
        if _sha256_bytes(item.seed_definition_bytes) != observation.observation_digest:
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_P2_OBSERVATION_DIGEST_MISMATCH")
        if not _character_witness_semantically_equivalent(
            witness, derivation.freshly_rederived_witness,
        ):
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_DOMAIN_WITNESS_MISMATCH")
        result[item.scope_key] = RootP3CharacterWitnessBinding(
            item.scope_key, item.legacy_source_namespace_id, observation.observation_key,
            observation.observation_digest, witness, derivation,
        )
    return result


def select_or_recover_character_continuation(
    *,
    directory: Path | None,
    predecessor_record_path: Path,
    predecessor_identity_digest: str,
    snapshot_scope_count: int,
    snapshot_identity_digest: str,
    authority: RootP3ExternalOwnerObservationAuthority | None,
    bindings: Mapping[RootScopeKey, RootP3CharacterWitnessBinding],
    scope_facts: Mapping[RootScopeKey, tuple[UUID, str | None]],
    domain_derivations: Mapping[RootScopeKey, RootP3CharacterDomainDerivation],
) -> dict[RootScopeKey, CharacterSeedWitness]:
    """Persist or reload an additive descriptor-only continuation carrier."""

    if not bindings and directory is None:
        if authority is not None:
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_AUTHORITY_WITHOUT_WITNESS")
        return {}
    if directory is None or authority is None:
        raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_REQUIRED")
    if not directory.parent.is_dir() or directory.is_symlink():
        raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_DIRECTORY_INVALID")
    path = directory / _RECORD_NAME
    if path.exists():
        observed = _load(path)
        _validate_predecessor(
            observed, predecessor_record_path=predecessor_record_path,
            predecessor_identity_digest=predecessor_identity_digest,
            snapshot_scope_count=snapshot_scope_count,
            snapshot_identity_digest=snapshot_identity_digest,
        )
        witnesses = _validate_payload(
            observed, authority=authority, scope_facts=scope_facts,
            domain_derivations=domain_derivations,
        )
        if bindings:
            expected = _payload(
                predecessor_record_path=predecessor_record_path,
                predecessor_identity_digest=predecessor_identity_digest,
                snapshot_scope_count=snapshot_scope_count,
                snapshot_identity_digest=snapshot_identity_digest,
                authority=authority,
                bindings=bindings,
            )
            if observed != expected:
                raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_BINDING_MISMATCH")
        return witnesses
    if not bindings:
        raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_REQUIRED")
    payload = _payload(
        predecessor_record_path=predecessor_record_path,
        predecessor_identity_digest=predecessor_identity_digest,
        snapshot_scope_count=snapshot_scope_count,
        snapshot_identity_digest=snapshot_identity_digest,
        authority=authority,
        bindings=bindings,
    )
    if directory.exists():
        if not directory.is_dir() or any(
            child.name not in {_LEGACY_RECORD_NAME, _RECORD_NAME}
            for child in directory.iterdir()
        ):
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_DESTINATION_NOT_EMPTY")
    directory.mkdir(exist_ok=True)
    _write(path, payload)
    return _validate_payload(
        payload, authority=authority, scope_facts=scope_facts,
        domain_derivations=domain_derivations,
    )


def _validate_predecessor(
    payload: Mapping[str, Any], *, predecessor_record_path: Path,
    predecessor_identity_digest: str, snapshot_scope_count: int,
    snapshot_identity_digest: str,
) -> None:
    if (
        payload.get("predecessor_carrier_record_path") != str(predecessor_record_path)
        or payload.get("predecessor_carrier_identity_digest") != predecessor_identity_digest
        or payload.get("snapshot_scope_count") != snapshot_scope_count
        or payload.get("snapshot_identity_digest") != snapshot_identity_digest
    ):
        raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_BINDING_MISMATCH")


def _payload(
    *, predecessor_record_path: Path, predecessor_identity_digest: str,
    snapshot_scope_count: int, snapshot_identity_digest: str,
    authority: RootP3ExternalOwnerObservationAuthority,
    bindings: Mapping[RootScopeKey, RootP3CharacterWitnessBinding],
) -> dict[str, Any]:
    if not predecessor_record_path.is_file() or predecessor_record_path.is_symlink():
        raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_PREDECESSOR_RECORD_INVALID")
    _sha256_text(predecessor_identity_digest, "P3_CHARACTER_PREDECESSOR_DIGEST_INVALID")
    _sha256_text(snapshot_identity_digest, "P3_CHARACTER_SNAPSHOT_DIGEST_INVALID")
    if not isinstance(snapshot_scope_count, int) or isinstance(snapshot_scope_count, bool) or snapshot_scope_count < 1:
        raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_SNAPSHOT_COUNT_INVALID")
    return {
        "predecessor_carrier_record_path": str(predecessor_record_path),
        "predecessor_carrier_identity_digest": predecessor_identity_digest,
        "snapshot_scope_count": snapshot_scope_count,
        "snapshot_identity_digest": snapshot_identity_digest,
        "envelope_c_digest": authority.envelope_c_digest,
        "external_owner_observation_aggregate": authority.external_owner_observation_aggregate,
        "external_owner_observation_proof": authority.proof,
        "witnesses": [
            bindings[key].carrier_payload() for key in sorted(bindings, key=lambda value: value.canonical_key)
        ],
    }


def _validate_payload(
    payload: Mapping[str, Any], *, authority: RootP3ExternalOwnerObservationAuthority,
    scope_facts: Mapping[RootScopeKey, tuple[UUID, str | None]],
    domain_derivations: Mapping[RootScopeKey, RootP3CharacterDomainDerivation],
) -> dict[RootScopeKey, CharacterSeedWitness]:
    required = {
        "predecessor_carrier_record_path", "predecessor_carrier_identity_digest",
        "snapshot_scope_count", "snapshot_identity_digest", "envelope_c_digest",
        "external_owner_observation_aggregate", "external_owner_observation_proof", "witnesses",
    }
    if set(payload) != required:
        raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_SHAPE_INVALID")
    if (
        payload["envelope_c_digest"] != authority.envelope_c_digest
        or payload["external_owner_observation_aggregate"] != authority.external_owner_observation_aggregate
        or payload["external_owner_observation_proof"] != authority.proof
    ):
        raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_AUTHORITY_MISMATCH")
    witnesses = payload["witnesses"]
    if not isinstance(witnesses, list) or not witnesses:
        raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_WITNESSES_INVALID")
    result: dict[RootScopeKey, CharacterSeedWitness] = {}
    for entry in witnesses:
        if not isinstance(entry, dict) or set(entry) != {
            "scope_key", "legacy_source_namespace_id", "seed_observation_key",
            "seed_observation_digest", "character_witness", "character_domain_id",
            "character_domain_derivation_law", "character_domain_candidate_evidence",
            "character_domain_candidate_evidence_digest",
        }:
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_WITNESS_INVALID")
        try:
            scope = _scope_from_payload(entry["scope_key"])
            namespace = UUID(entry["legacy_source_namespace_id"])
        except (TypeError, ValueError) as exc:
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_WITNESS_INVALID") from exc
        facts = scope_facts.get(scope)
        derivation = domain_derivations.get(scope)
        if facts is None or facts[0] != namespace or derivation is None:
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_SCOPE_MISMATCH")
        expected_domain = derivation.carrier_payload()
        if any(entry.get(key) != value for key, value in expected_domain.items()):
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_DOMAIN_MISMATCH")
        try:
            witness = CharacterSeedWitness.from_descriptor_payload(
                workspace_id=scope.workspace_id, agent_id=scope.agent_id or "",
                domain_id=derivation.domain_id, value=entry["character_witness"],
            )
        except CharacterSeedWitnessRefused as exc:
            raise RootP3CharacterWitnessContinuationRefused(exc.code) from exc
        observation = authority.observation_for(workspace_id=scope.workspace_id, seed_id=witness.seed_id)
        if (
            entry["seed_observation_key"] != observation.observation_key
            or entry["seed_observation_digest"] != observation.observation_digest
            or not _character_witness_semantically_equivalent(
                witness, derivation.freshly_rederived_witness,
            )
            or scope in result
        ):
            raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_WITNESS_MISMATCH")
        result[scope] = witness
    return result


def _scope_from_payload(value: Any) -> RootScopeKey:
    if not isinstance(value, Mapping):
        raise ValueError("scope")
    if value.get("scope_kind") != RootScopeKind.PRIVATE.value:
        raise ValueError("scope")
    return RootScopeKey(value["workspace_id"], RootScopeKind.PRIVATE, agent_id=value["agent_id"])


def _load(path: Path) -> dict[str, Any]:
    try:
        outer = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_UNREADABLE") from exc
    if (
        not isinstance(outer, dict) or set(outer) != {"schema", "version", "payload", "digest"}
        or outer.get("schema") != _SCHEMA or outer.get("version") != _VERSION
        or not isinstance(outer.get("payload"), dict) or outer.get("digest") != _sha256_value(outer["payload"])
    ):
        raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_INTEGRITY_INVALID")
    return outer["payload"]


def _write(path: Path, payload: dict[str, Any]) -> None:
    outer = {"schema": _SCHEMA, "version": _VERSION, "payload": payload, "digest": _sha256_value(payload)}
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_intent_text(outer) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise RootP3CharacterWitnessContinuationRefused("P3_CHARACTER_CONTINUATION_WRITE_FAILED") from exc


__all__ = [
    "RootP3CharacterWitnessContinuationRefused", "RootP3CharacterWitnessInput",
    "RootP3CharacterWitnessBinding", "RootP3CharacterDomainCandidateEvidence",
    "RootP3CharacterDomainDerivation", "RootP3ExternalOwnerObservationAuthority",
    "select_or_recover_character_continuation", "validate_character_witness_inputs",
]
