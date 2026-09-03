"""Read-only authority for the durable root-native profile generation.

The root/deployment profile is represented by one existing immutable native
object.  This module owns its contract and discovery; it creates neither a
profile nor any root-scope membership.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
from typing import Final
from uuid import UUID

from .errors import SubstrateConfigurationError
from .ids import native_id_from_bytes, native_id_to_bytes
from .schema import SchemaMetadata, open_schema


ROOT_NATIVE_PROFILE_GENERATION_KIND: Final[str] = "ROOT_NATIVE_PROFILE_GENERATION"
ROOT_NATIVE_PROFILE_GENERATION_CONTRACT: Final[str] = "TMS-ROOT-NATIVE-PROFILE-GENERATION-1"
ROOT_PROFILE_ADMISSIBLE_EXISTENCE_STATE: Final[str] = "EXISTS"
ROOT_PROFILE_ADMISSIBLE_LIFECYCLE_STATE: Final[str] = "ACTIVE"
ROOT_PROFILE_ADMISSIBLE_GOVERNANCE_STATE: Final[str] = "QUALIFIED"


class RootProfileGenerationError(SubstrateConfigurationError):
    """Raised when durable root-profile authority is absent or contradictory."""


@dataclass(frozen=True)
class RootProfileGenerationRef:
    """A verified claim about one exact current root-profile revision."""

    core_id: UUID
    profile_generation: int
    profile_object_id: UUID
    profile_revision_id: UUID
    profile_revision_ordinal: int
    profile_semantic_scope_id: UUID

    def __post_init__(self) -> None:
        for value, label in (
            (self.core_id, "core_id"),
            (self.profile_object_id, "profile_object_id"),
            (self.profile_revision_id, "profile_revision_id"),
            (self.profile_semantic_scope_id, "profile_semantic_scope_id"),
        ):
            _native_uuid(value, label)
        _positive_int(self.profile_generation, "profile_generation")
        _positive_int(self.profile_revision_ordinal, "profile_revision_ordinal")

    def payload(self) -> dict[str, object]:
        """Membership evidence repeats only its root/profile identity facts."""

        return {
            "core_id": str(self.core_id),
            "profile_generation": self.profile_generation,
        }


def root_profile_generation_payload(profile_generation: int) -> dict[str, object]:
    """Return the canonical durable payload for a root-profile object revision.

    This is a non-mutating contract helper.  The deployment/root owner remains
    responsible for admitting an object revision through the native substrate.
    """

    _positive_int(profile_generation, "profile_generation")
    return {
        "contract": ROOT_NATIVE_PROFILE_GENERATION_CONTRACT,
        "profile_generation": profile_generation,
    }


def current_root_profile_generation(connection: sqlite3.Connection) -> RootProfileGenerationRef:
    """Discover exactly one current admissible durable root-profile generation."""

    metadata = open_schema(connection)
    rows = connection.execute(
        "SELECT o.object_id,o.object_kind,r.object_revision_id,r.revision_ordinal,"
        "r.effective_semantic_scope_id,r.existence_state,r.lifecycle_state,"
        "r.governance_state,r.payload_format,r.payload_text "
        "FROM objects o JOIN object_revisions r ON r.object_revision_id=o.current_revision_id "
        "WHERE o.object_kind=?",
        (ROOT_NATIVE_PROFILE_GENERATION_KIND,),
    ).fetchall()
    if not rows:
        raise RootProfileGenerationError("current root profile generation is absent")

    admissible: list[RootProfileGenerationRef] = []
    for row in rows:
        reference = _reference_from_row(metadata, row)
        if _admissible(row):
            admissible.append(reference)
    if len(admissible) != 1:
        if len(admissible) > 1:
            raise RootProfileGenerationError("multiple current admissible root profile generations exist")
        raise RootProfileGenerationError("root profile generation is not admissible")
    return admissible[0]


def verify_root_profile_generation(
    connection: sqlite3.Connection,
    claimed: RootProfileGenerationRef,
) -> RootProfileGenerationRef:
    """Verify a caller claim solely against durable root/deployment facts."""

    if not isinstance(claimed, RootProfileGenerationRef):
        raise RootProfileGenerationError("root profile claim must be typed")
    metadata = open_schema(connection)
    kind_row = connection.execute(
        "SELECT object_kind FROM objects WHERE object_id=?",
        (native_id_to_bytes(claimed.profile_object_id),),
    ).fetchone()
    if kind_row is None:
        raise RootProfileGenerationError("claimed root profile object is absent")
    if kind_row[0] != ROOT_NATIVE_PROFILE_GENERATION_KIND:
        raise RootProfileGenerationError("claimed object is not a root profile generation")
    actual = current_root_profile_generation(connection)
    if actual.core_id != native_id_from_bytes(metadata.core_id) or actual != claimed:
        raise RootProfileGenerationError("root profile claim conflicts with current durable authority")
    return actual


def _reference_from_row(metadata: SchemaMetadata, row: tuple[object, ...]) -> RootProfileGenerationRef:
    (
        object_id,
        object_kind,
        revision_id,
        ordinal,
        semantic_scope_id,
        _existence_state,
        _lifecycle_state,
        _governance_state,
        payload_format,
        payload_text,
    ) = row
    if object_kind != ROOT_NATIVE_PROFILE_GENERATION_KIND:
        raise RootProfileGenerationError("root profile discovery received a wrong object kind")
    if payload_format != "JSON" or not isinstance(payload_text, str):
        raise RootProfileGenerationError("root profile generation payload is not authoritative JSON")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise RootProfileGenerationError("root profile generation payload is malformed") from exc
    if not isinstance(payload, dict) or payload.get("contract") != ROOT_NATIVE_PROFILE_GENERATION_CONTRACT:
        raise RootProfileGenerationError("root profile generation contract is invalid")
    generation = payload.get("profile_generation")
    _positive_int(generation, "durable profile_generation")
    return RootProfileGenerationRef(
        core_id=native_id_from_bytes(metadata.core_id),
        profile_generation=generation,
        profile_object_id=_uuid_from_blob(object_id, "profile_object_id"),
        profile_revision_id=_uuid_from_blob(revision_id, "profile_revision_id"),
        profile_revision_ordinal=_positive_int(ordinal, "profile_revision_ordinal"),
        profile_semantic_scope_id=_uuid_from_blob(semantic_scope_id, "profile_semantic_scope_id"),
    )


def _admissible(row: tuple[object, ...]) -> bool:
    return (
        row[5] == ROOT_PROFILE_ADMISSIBLE_EXISTENCE_STATE
        and row[6] == ROOT_PROFILE_ADMISSIBLE_LIFECYCLE_STATE
        and row[7] == ROOT_PROFILE_ADMISSIBLE_GOVERNANCE_STATE
    )


def _native_uuid(value: object, label: str) -> UUID:
    try:
        native_id_to_bytes(value)  # type: ignore[arg-type]
    except Exception as exc:
        raise RootProfileGenerationError(f"{label} must be a native UUID") from exc
    return value  # type: ignore[return-value]


def _uuid_from_blob(value: object, label: str) -> UUID:
    if not isinstance(value, bytes):
        raise RootProfileGenerationError(f"{label} must be a native UUID blob")
    try:
        return native_id_from_bytes(value)
    except Exception as exc:
        raise RootProfileGenerationError(f"{label} is malformed") from exc


def _positive_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise RootProfileGenerationError(f"{label} must be a positive integer")
    return value


__all__ = [
    "ROOT_NATIVE_PROFILE_GENERATION_CONTRACT",
    "ROOT_NATIVE_PROFILE_GENERATION_KIND",
    "ROOT_PROFILE_ADMISSIBLE_EXISTENCE_STATE",
    "ROOT_PROFILE_ADMISSIBLE_GOVERNANCE_STATE",
    "ROOT_PROFILE_ADMISSIBLE_LIFECYCLE_STATE",
    "RootProfileGenerationError",
    "RootProfileGenerationRef",
    "current_root_profile_generation",
    "root_profile_generation_payload",
    "verify_root_profile_generation",
]
