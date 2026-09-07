"""Frozen evidence contract for legacy Character seed planting.

CharacterStore remains the owner of ``seed.json`` and ``character_state.json``.
This module only validates the stable, already-written relationship between an
external seed definition, current private core rows, and the selected legacy
motif.  It has no SQLite connection and cannot activate native routing.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from torment_service.character import CharacterSeed, _split_seed_text
from torment_service.lifecycle import validate_lifecycle_envelope

from .canonical_intent import canonical_intent_text
from .errors import SubstrateInvariantViolation
from .provenance import NativeProvenanceRecord


_ORIGIN_KIND = "CHARACTER_SEED_PLANT"
_CURRENT_CANONICAL = "CURRENT_CANONICAL"
_LEGACY_MISSING_OWNER_AGENT_ID_V1 = "LEGACY_MISSING_OWNER_AGENT_ID_V1"


class CharacterSeedWitnessRefused(SubstrateInvariantViolation):
    """The source does not prove the exact legacy seed writer witness."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class CharacterSeedWitness:
    """Immutable, source-derived Character seed facts for one private agent."""

    workspace_id: str
    agent_id: str
    domain_id: str
    seed_definition: Mapping[str, Any]
    seed_definition_compatibility: str
    derived_owner_agent_id: str | None
    seed_definition_digest: str
    seed_id: str
    character_name: str
    seed_text: str
    seed_eids: tuple[int, ...]
    seed_motif_id: str
    seed_motif_member_eids: tuple[int, ...]
    seed_motif_seed_eids: tuple[int, ...]
    concept_summaries: tuple[str, ...]
    witness_digest: str

    def descriptor_payload(self) -> dict[str, Any]:
        return {
            "compatibility_status": "CHARACTER_SEED_WITNESS_QUALIFIED",
            "seed_definition": dict(self.seed_definition),
            "seed_definition_compatibility": self.seed_definition_compatibility,
            "derived_owner_agent_id": self.derived_owner_agent_id,
            "seed_definition_digest": self.seed_definition_digest,
            "seed_id": self.seed_id,
            "character_name": self.character_name,
            "seed_text": self.seed_text,
            "seed_eids": list(self.seed_eids),
            "seed_motif_id": self.seed_motif_id,
            "seed_motif_member_eids": list(self.seed_motif_member_eids),
            "seed_motif_seed_eids": list(self.seed_motif_seed_eids),
            "concept_summaries": list(self.concept_summaries),
            "witness_digest": self.witness_digest,
        }

    def provenance_for_concept(self, concept_index: int) -> NativeProvenanceRecord:
        if not isinstance(concept_index, int) or isinstance(concept_index, bool):
            raise ValueError("concept_index must be an integer")
        if concept_index < 0 or concept_index >= len(self.concept_summaries):
            raise ValueError("concept_index is outside the witnessed seed concepts")
        notes = canonical_intent_text({
            "character_name": self.character_name,
            "seed_concept_index": concept_index,
            "seed_definition_digest": self.seed_definition_digest,
            "seed_id": self.seed_id,
            "seed_witness_digest": self.witness_digest,
        })
        return NativeProvenanceRecord(
            _ORIGIN_KIND, "character_runtime", "seed_canon", "seed_plant", "KNOWN",
            None, None, "seed_canon", notes,
        )

    def matches_raw_seed_definition(self, raw_definition: Any) -> bool:
        """Return whether P2's untouched object has this witness's exact shape."""
        if not isinstance(raw_definition, dict):
            return False
        definition = dict(self.seed_definition)
        if self.seed_definition_compatibility == _CURRENT_CANONICAL:
            return raw_definition == definition
        if self.seed_definition_compatibility == _LEGACY_MISSING_OWNER_AGENT_ID_V1:
            if (
                self.derived_owner_agent_id != self.agent_id
                or definition.get("owner_agent_id") != self.derived_owner_agent_id
            ):
                return False
            expected = dict(definition)
            expected.pop("owner_agent_id", None)
            return raw_definition == expected
        return False

    @classmethod
    def from_descriptor_payload(
        cls, *, workspace_id: str, agent_id: str, domain_id: str, value: Mapping[str, Any],
    ) -> "CharacterSeedWitness":
        if not isinstance(value, Mapping) or value.get("compatibility_status") != "CHARACTER_SEED_WITNESS_QUALIFIED":
            raise CharacterSeedWitnessRefused("CHARACTER_DESCRIPTOR_WITNESS_INVALID")
        try:
            seed_definition = value["seed_definition"]
            witness = cls(
                workspace_id, agent_id, domain_id, seed_definition,
                value.get("seed_definition_compatibility", _CURRENT_CANONICAL),
                value.get("derived_owner_agent_id"),
                _text(value, "seed_definition_digest"), _text(value, "seed_id"),
                _text(value, "character_name"), _text(value, "seed_text"),
                _integer_tuple(value, "seed_eids", unique=True), _text(value, "seed_motif_id"),
                _integer_tuple(value, "seed_motif_member_eids", unique=False, nonempty=True),
                _integer_tuple(value, "seed_motif_seed_eids", unique=False, nonempty=True),
                _text_tuple(value, "concept_summaries"), _text(value, "witness_digest"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CharacterSeedWitnessRefused("CHARACTER_DESCRIPTOR_WITNESS_INVALID") from exc
        _validate_descriptor_witness(witness)
        return witness


def read_legacy_character_seed_witness(
    *, workspace_root: str | Path, workspace_id: str, agent_id: str,
    domain_id: str, requested_seed_id: str,
) -> CharacterSeedWitness:
    """Read and validate one real writer witness without loading MemoryGraph."""
    root = Path(workspace_root).expanduser().resolve()
    try:
        seed_definition_bytes = (root / "seeds" / requested_seed_id / "seed.json").read_bytes()
    except OSError as exc:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_DEFINITION_REQUIRED") from exc
    try:
        private_nodes_bytes = (root / "agents" / agent_id / "private" / "nodes.jsonl").read_bytes()
    except OSError as exc:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_PRIVATE_NODES_REQUIRED") from exc
    try:
        motif_bytes = (root / "domains" / domain_id / "motifs.json").read_bytes()
    except OSError as exc:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_MOTIF_REQUIRED") from exc
    return read_legacy_character_seed_witness_from_frozen_bytes(
        seed_definition_bytes=seed_definition_bytes,
        private_nodes_bytes=private_nodes_bytes,
        motif_bytes=motif_bytes,
        workspace_id=workspace_id,
        agent_id=agent_id,
        domain_id=domain_id,
        requested_seed_id=requested_seed_id,
    )


def read_legacy_character_seed_witness_from_frozen_bytes(
    *, seed_definition_bytes: bytes, private_nodes_bytes: bytes, motif_bytes: bytes,
    workspace_id: str, agent_id: str, domain_id: str, requested_seed_id: str,
) -> CharacterSeedWitness:
    """Apply the established Character witness law to already-frozen bytes.

    P3's source carrier owns immutable snapshots, not a live workspace root.
    This byte-oriented entry point deliberately shares every semantic rule with
    :func:`read_legacy_character_seed_witness`; it changes only where the three
    already-authorized source artifacts are obtained.
    """
    if not isinstance(requested_seed_id, str) or not requested_seed_id:
        raise ValueError("requested_seed_id must be non-empty")
    try:
        raw_seed = json.loads(seed_definition_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_DEFINITION_REQUIRED") from exc
    seed, definition_compatibility, derived_owner_agent_id = _qualified_seed_from_raw_definition(
        raw_seed, agent_id,
    )
    if seed.seed_id != requested_seed_id or not seed.character_name or not seed.seed_text:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_IDENTITY_MISMATCH")
    if seed.owner_agent_id != agent_id:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_OWNER_AGENT_MISMATCH")
    concepts = tuple(_split_seed_text(seed.seed_text))
    if not concepts or len(seed.seed_eids) != len(concepts):
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_CONCEPT_CARDINALITY_MISMATCH")
    seed_eids = _validate_eids(seed.seed_eids, "CHARACTER_SEED_EIDS_INVALID", unique=True)
    rows = _current_node_payloads_from_bytes(private_nodes_bytes)
    _validate_seed_rows(rows, seed, concepts, seed_eids)
    member_eids = _read_selected_motif_members_from_bytes(motif_bytes, seed.seed_motif_id)
    seed_eid_membership = set(seed_eids)
    seed_members = tuple(eid for eid in member_eids if eid in seed_eid_membership)
    if not seed_members:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_MOTIF_HAS_NO_SEED_MEMBER")
    definition = seed.to_dict()
    definition_digest = _digest(definition)
    witness_payload = {
        "workspace_id": workspace_id, "agent_id": agent_id, "domain_id": domain_id,
        "seed_definition_compatibility": definition_compatibility,
        "derived_owner_agent_id": derived_owner_agent_id,
        "seed_definition_digest": definition_digest, "seed_id": seed.seed_id,
        "character_name": seed.character_name, "seed_eids": list(seed_eids),
        "seed_motif_id": seed.seed_motif_id, "seed_motif_member_eids": list(member_eids),
        "seed_motif_seed_eids": list(seed_members), "concept_summaries": list(concepts),
    }
    return CharacterSeedWitness(
        workspace_id, agent_id, domain_id, definition, definition_compatibility,
        derived_owner_agent_id, definition_digest, seed.seed_id,
        seed.character_name, seed.seed_text, seed_eids, seed.seed_motif_id, member_eids,
        seed_members, concepts, _digest(witness_payload),
    )


def _qualified_seed_from_raw_definition(
    raw_definition: Any, agent_id: str,
) -> tuple[CharacterSeed, str, str | None]:
    """Recognize current seed JSON or one exact migration-only historic class."""
    if not isinstance(raw_definition, dict):
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_DEFINITION_NONCANONICAL")
    try:
        seed = CharacterSeed.from_dict(raw_definition)
    except (TypeError, ValueError) as exc:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_DEFINITION_REQUIRED") from exc
    current_definition = seed.to_dict()
    if raw_definition == current_definition:
        return seed, _CURRENT_CANONICAL, None

    # This historic file omitted precisely the field added later.  Projecting
    # that owner enables the existing writer-row witness; P2 still owns and
    # later rechecks the untouched raw object and its bytes.
    legacy_definition = dict(current_definition)
    legacy_definition.pop("owner_agent_id")
    if raw_definition != legacy_definition:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_DEFINITION_NONCANONICAL")
    projected_definition = dict(raw_definition)
    projected_definition["owner_agent_id"] = agent_id
    try:
        projected_seed = CharacterSeed.from_dict(projected_definition)
    except (TypeError, ValueError) as exc:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_DEFINITION_REQUIRED") from exc
    if projected_seed.to_dict() != projected_definition:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_DEFINITION_NONCANONICAL")
    return projected_seed, _LEGACY_MISSING_OWNER_AGENT_ID_V1, agent_id


def character_seed_definition_digest(seed: CharacterSeed) -> str:
    """Canonical digest for a fresh caller-owned seed definition."""
    if not isinstance(seed, CharacterSeed):
        raise ValueError("seed must be CharacterSeed")
    if not seed.seed_id or not seed.character_name or not seed.seed_text:
        raise ValueError("seed definition requires seed_id, character_name, and seed_text")
    # Planting references are generated outputs, not inputs to fresh identity.
    value = seed.to_dict()
    value["seed_eids"] = []
    value["seed_motif_id"] = ""
    value["created_ts"] = 0
    return _digest(value)


def _validate_seed_rows(
    rows: Mapping[int, Mapping[str, Any]], seed: CharacterSeed,
    concepts: tuple[str, ...], seed_eids: tuple[int, ...],
) -> None:
    for index, eid in enumerate(seed_eids):
        payload = rows.get(eid)
        if payload is None:
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_EID_NOT_IN_CURRENT_PRIVATE_CORE")
        if payload.get("type") != "seed_canon" or payload.get("mtype", "seed_canon") != "seed_canon":
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_MEMORY_TYPE_MISMATCH")
        if payload.get("canon") is not True or payload.get("memory_class") != "core":
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_CANON_CORE_MISMATCH")
        if payload.get("seed_id") != seed.seed_id or payload.get("character_name") != seed.character_name:
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_MEMORY_IDENTITY_MISMATCH")
        if payload.get("seed_concept_index") != index or payload.get("summary") != concepts[index]:
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_CONCEPT_WITNESS_MISMATCH")
        if payload.get("tier") != "core_identity" or payload.get("user_id") != seed.owner_agent_id:
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_TIER_OR_OWNER_MISMATCH")
        if not _exact_float(payload.get("strength"), .95) or not _exact_float(payload.get("confidence"), .95):
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_STRENGTH_CONFIDENCE_MISMATCH")
        if not _exact_float(payload.get("half_life"), seed.core_half_life):
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_HALF_LIFE_MISMATCH")
        if not isinstance(payload.get("created_at"), int) or isinstance(payload.get("created_at"), bool) or payload.get("last_reinforced") != payload.get("created_at"):
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_WRITER_STEP_MISMATCH")
        if "provenance" in payload:
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_UNEXPECTED_PROVENANCE")
        try:
            lifecycle = validate_lifecycle_envelope(payload["lifecycle_status"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_LIFECYCLE_INVALID") from exc
        if (
            lifecycle.to_dict() != payload["lifecycle_status"]
            or not lifecycle.is_authoritative_on_row
            or lifecycle.state.value != "protected"
            or lifecycle.set_by.actor.value != "system"
            or lifecycle.set_by.via.value != "canon_set"
        ):
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_LIFECYCLE_INVALID")

    for eid, payload in rows.items():
        if payload.get("type") == "seed_canon" and eid not in seed_eids:
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_FOREIGN_SEED_CANON_EID")


def _current_node_payloads_from_bytes(value: bytes) -> dict[int, Mapping[str, Any]]:
    try:
        raw_lines = value.splitlines()
    except AttributeError as exc:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_PRIVATE_NODES_MALFORMED") from exc
    rows: dict[int, Mapping[str, Any]] = {}
    for raw in raw_lines:
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
            eid = value["eid"]
            payload = value["payload"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_PRIVATE_NODES_MALFORMED") from exc
        if not isinstance(eid, int) or isinstance(eid, bool) or eid < 0 or not isinstance(payload, dict):
            raise CharacterSeedWitnessRefused("CHARACTER_SEED_PRIVATE_NODES_MALFORMED")
        rows[eid] = payload
    return rows


def _read_selected_motif_members_from_bytes(motif_bytes: bytes, seed_motif_id: str) -> tuple[int, ...]:
    if not isinstance(seed_motif_id, str) or not seed_motif_id:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_MOTIF_ID_REQUIRED")
    try:
        raw = json.loads(motif_bytes.decode("utf-8"))
        motif = raw["motifs"][seed_motif_id]
        members = motif["members"]
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise CharacterSeedWitnessRefused("CHARACTER_SEED_MOTIF_REQUIRED") from exc
    # MotifRegistry preserves the source's append sequence.  Unlike logical
    # Character seed EIDs, this is occurrence evidence: duplicates and order
    # are therefore both part of the witness and its digest.
    return _validate_eids(members, "CHARACTER_SEED_MOTIF_MEMBERS_INVALID", unique=False)


def _validate_eids(value: Any, code: str, *, unique: bool) -> tuple[int, ...]:
    if not isinstance(value, list) or not value:
        raise CharacterSeedWitnessRefused(code)
    result = tuple(value)
    if any(not isinstance(item, int) or isinstance(item, bool) or item < 0 for item in result):
        raise CharacterSeedWitnessRefused(code)
    if unique and len(set(result)) != len(result):
        raise CharacterSeedWitnessRefused(code)
    return result


def _exact_float(value: Any, expected: float) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and float(value) == expected


def _text(value: Mapping[str, Any], key: str) -> str:
    item = value[key]
    if not isinstance(item, str) or not item:
        raise ValueError(key)
    return item


def _text_tuple(value: Mapping[str, Any], key: str) -> tuple[str, ...]:
    items = value[key]
    if not isinstance(items, list) or not items or any(not isinstance(item, str) or not item for item in items):
        raise ValueError(key)
    return tuple(items)


def _integer_tuple(
    value: Mapping[str, Any], key: str, *, unique: bool, nonempty: bool = False,
) -> tuple[int, ...]:
    items = value[key]
    if not isinstance(items, list) or any(not isinstance(item, int) or isinstance(item, bool) or item < 0 for item in items):
        raise ValueError(key)
    result = tuple(items)
    if nonempty and not result:
        raise ValueError(key)
    if unique and len(set(result)) != len(result):
        raise ValueError(key)
    return result


def _validate_descriptor_witness(witness: CharacterSeedWitness) -> None:
    definition = dict(witness.seed_definition)
    if _digest(definition) != witness.seed_definition_digest:
        raise CharacterSeedWitnessRefused("CHARACTER_DESCRIPTOR_SEED_DIGEST_MISMATCH")
    try:
        seed = CharacterSeed.from_dict(definition)
    except (TypeError, ValueError) as exc:
        raise CharacterSeedWitnessRefused("CHARACTER_DESCRIPTOR_SEED_DEFINITION_INVALID") from exc
    if (
        seed.to_dict() != definition
        or seed.seed_id != witness.seed_id
        or seed.character_name != witness.character_name
        or seed.seed_text != witness.seed_text
        or seed.owner_agent_id != witness.agent_id
        or tuple(seed.seed_eids) != witness.seed_eids
        or seed.seed_motif_id != witness.seed_motif_id
    ):
        raise CharacterSeedWitnessRefused("CHARACTER_DESCRIPTOR_SEED_DEFINITION_INVALID")
    if witness.seed_definition_compatibility == _CURRENT_CANONICAL:
        if witness.derived_owner_agent_id is not None:
            raise CharacterSeedWitnessRefused("CHARACTER_DESCRIPTOR_SEED_DEFINITION_INVALID")
    elif witness.seed_definition_compatibility == _LEGACY_MISSING_OWNER_AGENT_ID_V1:
        if witness.derived_owner_agent_id != witness.agent_id:
            raise CharacterSeedWitnessRefused("CHARACTER_DESCRIPTOR_SEED_DEFINITION_INVALID")
    else:
        raise CharacterSeedWitnessRefused("CHARACTER_DESCRIPTOR_SEED_DEFINITION_INVALID")
    if tuple(_split_seed_text(witness.seed_text)) != witness.concept_summaries:
        raise CharacterSeedWitnessRefused("CHARACTER_DESCRIPTOR_CONCEPTS_MISMATCH")
    if len(witness.seed_eids) != len(witness.concept_summaries):
        raise CharacterSeedWitnessRefused("CHARACTER_DESCRIPTOR_SEED_EIDS_MISMATCH")
    expected_seed_occurrences = tuple(
        eid for eid in witness.seed_motif_member_eids if eid in set(witness.seed_eids)
    )
    if witness.seed_motif_seed_eids != expected_seed_occurrences:
        raise CharacterSeedWitnessRefused("CHARACTER_DESCRIPTOR_MOTIF_MEMBERS_MISMATCH")
    expected_payload = {
        "workspace_id": witness.workspace_id, "agent_id": witness.agent_id, "domain_id": witness.domain_id,
        "seed_definition_compatibility": witness.seed_definition_compatibility,
        "derived_owner_agent_id": witness.derived_owner_agent_id,
        "seed_definition_digest": witness.seed_definition_digest, "seed_id": witness.seed_id,
        "character_name": witness.character_name, "seed_eids": list(witness.seed_eids),
        "seed_motif_id": witness.seed_motif_id, "seed_motif_member_eids": list(witness.seed_motif_member_eids),
        "seed_motif_seed_eids": list(witness.seed_motif_seed_eids),
        "concept_summaries": list(witness.concept_summaries),
    }
    if _digest(expected_payload) == witness.witness_digest:
        return
    # Historical current-canonical descriptors predate these two fields.  They
    # cannot describe the new raw compatibility class, so retain only this
    # narrow old form for recovery of existing current-canonical carriers.
    legacy_descriptor_payload = dict(expected_payload)
    legacy_descriptor_payload.pop("seed_definition_compatibility")
    legacy_descriptor_payload.pop("derived_owner_agent_id")
    if not (
        witness.seed_definition_compatibility == _CURRENT_CANONICAL
        and witness.derived_owner_agent_id is None
        and _digest(legacy_descriptor_payload) == witness.witness_digest
    ):
        raise CharacterSeedWitnessRefused("CHARACTER_DESCRIPTOR_WITNESS_DIGEST_MISMATCH")


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_intent_text(value).encode("utf-8")).hexdigest()


__all__ = [
    "CharacterSeedWitness", "CharacterSeedWitnessRefused", "character_seed_definition_digest",
    "read_legacy_character_seed_witness", "read_legacy_character_seed_witness_from_frozen_bytes",
]
