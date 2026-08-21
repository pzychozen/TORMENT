"""Frozen Phase-8 Brainvision configuration representation and storage.

This module owns only the configuration artifact boundary: strict validation,
canonical serialization, contained paths, and mechanical atomic persistence.
It deliberately does not allocate recursive VHE state, authorize lifecycle
operations, create agents, or integrate with Fabric.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import os
from os import PathLike
import re
import tempfile
from typing import ClassVar, Final

from brainvision.character_modulation import (
    MODULATION_MAPPING_ID,
    MODULATION_PROFILE_SCHEMA_ID,
    MODULATION_SCHEMA_ID,
    modulation_profile_id,
    validate_theta,
)
from brainvision.observation import MAX_SOURCE_SEQUENCE
from brainvision.projection import PROJECTION_ID
from brainvision.vhe import OPERATOR_ID
from torment_service.pathing import ensure_within_base, safe_join, safe_slug, stable_filename


CONFIGURATION_SCHEMA_ID: Final = "brainvision.configuration.v1"
CONFIGURATION_FILENAME: Final = "configuration.json"

LIFECYCLE_DISABLED: Final = "disabled"
LIFECYCLE_ACTIVE: Final = "active"
LIFECYCLE_SUSPENDED: Final = "suspended"
LIFECYCLE_STATUSES: Final[frozenset[str]] = frozenset(
    {LIFECYCLE_DISABLED, LIFECYCLE_ACTIVE, LIFECYCLE_SUSPENDED}
)

FRESH_LAST_ACCEPTED_SOURCE_SEQUENCE: Final = -1
MAX_LAST_ACCEPTED_SOURCE_SEQUENCE: Final = MAX_SOURCE_SEQUENCE

_BRAINVISION_DIRECTORY_NAME: Final = "brainvision"
_IDENTIFIER_PATTERN: Final = re.compile(r"[a-z][a-z0-9._-]{0,63}")
_CONFIGURATION_FIELDS: Final[tuple[str, ...]] = (
    "schema_id",
    "lifecycle_status",
    "stream_identity",
    "adapter_contract_id",
    "last_accepted_source_sequence",
    "expected_operator_id",
    "expected_projection_id",
    "modulation_schema_id",
    "modulation_mapping_id",
    "modulation_profile_schema_id",
    "theta",
    "modulation_profile_id",
)
_CONFIGURATION_FIELD_SET: Final[frozenset[str]] = frozenset(_CONFIGURATION_FIELDS)


class BrainvisionConfigurationValidationError(ValueError):
    """A strict Phase-8 configuration validation failure."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


def _require_identifier(value: object, field: str) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise BrainvisionConfigurationValidationError(field, "invalid_identifier")
    return value


def _require_watermark(value: object) -> int:
    if type(value) is not int:
        raise BrainvisionConfigurationValidationError(
            "last_accepted_source_sequence", "must_be_exact_int"
        )
    if not FRESH_LAST_ACCEPTED_SOURCE_SEQUENCE <= value <= MAX_LAST_ACCEPTED_SOURCE_SEQUENCE:
        raise BrainvisionConfigurationValidationError(
            "last_accepted_source_sequence", "out_of_range"
        )
    return value


def _require_theta(value: object) -> int:
    if type(value) is not int:
        raise BrainvisionConfigurationValidationError("theta", "must_be_exact_int")
    try:
        return validate_theta(value)
    except ValueError as error:
        raise BrainvisionConfigurationValidationError("theta", "out_of_range") from error


def _require_frozen_identity(
    value: object,
    *,
    field: str,
    expected: str,
    reason: str,
) -> str:
    if type(value) is not str or value != expected:
        raise BrainvisionConfigurationValidationError(field, reason)
    return value


def _require_exact_field_set(raw: Mapping[str, object]) -> None:
    raw_fields = set(raw)
    missing = _CONFIGURATION_FIELD_SET - raw_fields
    if missing:
        raise BrainvisionConfigurationValidationError(
            sorted(missing)[0], "missing_field"
        )
    unknown = raw_fields - _CONFIGURATION_FIELD_SET
    if unknown:
        raise BrainvisionConfigurationValidationError(
            sorted(unknown)[0], "unknown_field"
        )


def _canonical_json_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


@dataclass(frozen=True, kw_only=True)
class BrainvisionConfigurationV1:
    """One fully populated immutable Phase-8 Brainvision configuration."""

    lifecycle_status: str
    stream_identity: str
    adapter_contract_id: str
    last_accepted_source_sequence: int
    expected_operator_id: str
    expected_projection_id: str
    modulation_schema_id: str
    modulation_mapping_id: str
    modulation_profile_schema_id: str
    theta: int
    modulation_profile_id: str

    schema_id: ClassVar[str] = CONFIGURATION_SCHEMA_ID

    def __post_init__(self) -> None:
        if type(self.lifecycle_status) is not str or self.lifecycle_status not in LIFECYCLE_STATUSES:
            raise BrainvisionConfigurationValidationError(
                "lifecycle_status", "invalid_lifecycle_status"
            )
        _require_identifier(self.stream_identity, "stream_identity")
        _require_identifier(self.adapter_contract_id, "adapter_contract_id")
        _require_watermark(self.last_accepted_source_sequence)
        _require_frozen_identity(
            self.expected_operator_id,
            field="expected_operator_id",
            expected=OPERATOR_ID,
            reason="operator_identity_mismatch",
        )
        _require_frozen_identity(
            self.expected_projection_id,
            field="expected_projection_id",
            expected=PROJECTION_ID,
            reason="projection_identity_mismatch",
        )
        _require_frozen_identity(
            self.modulation_schema_id,
            field="modulation_schema_id",
            expected=MODULATION_SCHEMA_ID,
            reason="modulation_schema_mismatch",
        )
        _require_frozen_identity(
            self.modulation_mapping_id,
            field="modulation_mapping_id",
            expected=MODULATION_MAPPING_ID,
            reason="modulation_mapping_mismatch",
        )
        _require_frozen_identity(
            self.modulation_profile_schema_id,
            field="modulation_profile_schema_id",
            expected=MODULATION_PROFILE_SCHEMA_ID,
            reason="modulation_profile_schema_mismatch",
        )
        theta = _require_theta(self.theta)
        if (
            type(self.modulation_profile_id) is not str
            or self.modulation_profile_id != modulation_profile_id(theta)
        ):
            raise BrainvisionConfigurationValidationError(
                "modulation_profile_id", "modulation_profile_mismatch"
            )

    def to_dict(self) -> dict[str, object]:
        """Return the exact complete Phase-8 configuration mapping."""
        return {
            "schema_id": self.schema_id,
            "lifecycle_status": self.lifecycle_status,
            "stream_identity": self.stream_identity,
            "adapter_contract_id": self.adapter_contract_id,
            "last_accepted_source_sequence": self.last_accepted_source_sequence,
            "expected_operator_id": self.expected_operator_id,
            "expected_projection_id": self.expected_projection_id,
            "modulation_schema_id": self.modulation_schema_id,
            "modulation_mapping_id": self.modulation_mapping_id,
            "modulation_profile_schema_id": self.modulation_profile_schema_id,
            "theta": self.theta,
            "modulation_profile_id": self.modulation_profile_id,
        }

    def to_canonical_json_bytes(self) -> bytes:
        """Return the frozen canonical ASCII configuration bytes."""
        return _canonical_json_bytes(self.to_dict())

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> "BrainvisionConfigurationV1":
        """Strictly parse one complete configuration mapping without coercion."""
        return configuration_from_dict(raw)


def configuration_from_dict(raw: Mapping[str, object]) -> BrainvisionConfigurationV1:
    """Strictly validate a complete Phase-8 configuration mapping."""
    if not isinstance(raw, Mapping):
        raise BrainvisionConfigurationValidationError("configuration", "must_be_mapping")
    _require_exact_field_set(raw)
    if raw["schema_id"] != CONFIGURATION_SCHEMA_ID:
        raise BrainvisionConfigurationValidationError("schema_id", "schema_mismatch")
    return BrainvisionConfigurationV1(
        lifecycle_status=raw["lifecycle_status"],
        stream_identity=raw["stream_identity"],
        adapter_contract_id=raw["adapter_contract_id"],
        last_accepted_source_sequence=raw["last_accepted_source_sequence"],
        expected_operator_id=raw["expected_operator_id"],
        expected_projection_id=raw["expected_projection_id"],
        modulation_schema_id=raw["modulation_schema_id"],
        modulation_mapping_id=raw["modulation_mapping_id"],
        modulation_profile_schema_id=raw["modulation_profile_schema_id"],
        theta=raw["theta"],
        modulation_profile_id=raw["modulation_profile_id"],
    )


def configuration_from_json_bytes(raw: bytes) -> BrainvisionConfigurationV1:
    """Decode strict ASCII JSON bytes into a validated configuration."""
    if type(raw) is not bytes:
        raise TypeError("configuration JSON must be bytes")
    return configuration_from_dict(json.loads(raw.decode("ascii")))


def fresh_disabled_brainvision_configuration(
    *,
    stream_identity: str,
    adapter_contract_id: str,
    theta: int,
) -> BrainvisionConfigurationV1:
    """Build, but do not authorize persistence of, a fresh disabled lineage."""
    theta = _require_theta(theta)
    return BrainvisionConfigurationV1(
        lifecycle_status=LIFECYCLE_DISABLED,
        stream_identity=stream_identity,
        adapter_contract_id=adapter_contract_id,
        last_accepted_source_sequence=FRESH_LAST_ACCEPTED_SOURCE_SEQUENCE,
        expected_operator_id=OPERATOR_ID,
        expected_projection_id=PROJECTION_ID,
        modulation_schema_id=MODULATION_SCHEMA_ID,
        modulation_mapping_id=MODULATION_MAPPING_ID,
        modulation_profile_schema_id=MODULATION_PROFILE_SCHEMA_ID,
        theta=theta,
        modulation_profile_id=modulation_profile_id(theta),
    )


def _resolved_data_root(data_root: str | PathLike[str]) -> str:
    root = os.fspath(data_root)
    if type(root) is not str:
        raise TypeError("data_root must be a string path")
    return os.path.realpath(root)


def brainvision_configuration_path(
    data_root: str | PathLike[str],
    workspace_id: str,
    agent_id: str,
) -> str:
    """Return the contained configuration path without creating any path entry."""
    root = _resolved_data_root(data_root)
    workspace_component = safe_slug(workspace_id, "workspace_id")
    agent_component = safe_slug(agent_id, "agent_id")
    agent_root = safe_join(
        root,
        "workspaces",
        workspace_component,
        "agents",
        agent_component,
    )
    brainvision_root = safe_join(agent_root, _BRAINVISION_DIRECTORY_NAME)
    target = stable_filename(brainvision_root, CONFIGURATION_FILENAME)
    return ensure_within_base(target, root)


def load_brainvision_configuration(
    data_root: str | PathLike[str],
    workspace_id: str,
    agent_id: str,
) -> BrainvisionConfigurationV1 | None:
    """Load a strict configuration, returning ``None`` only for an absent file."""
    target = brainvision_configuration_path(data_root, workspace_id, agent_id)
    try:
        with open(target, "rb") as source:
            return configuration_from_json_bytes(source.read())
    except FileNotFoundError:
        return None


def _validated_configuration(
    configuration: BrainvisionConfigurationV1,
) -> BrainvisionConfigurationV1:
    if type(configuration) is not BrainvisionConfigurationV1:
        raise TypeError("configuration must be BrainvisionConfigurationV1")
    return configuration_from_dict(configuration.to_dict())


def write_brainvision_configuration(
    data_root: str | PathLike[str],
    workspace_id: str,
    agent_id: str,
    configuration: BrainvisionConfigurationV1,
) -> None:
    """Atomically persist exactly one caller-supplied validated configuration."""
    validated_configuration = _validated_configuration(configuration)
    root = _resolved_data_root(data_root)
    target = brainvision_configuration_path(root, workspace_id, agent_id)
    target_directory = os.path.dirname(target)

    ensure_within_base(target_directory, root)
    ensure_within_base(target, root)
    os.makedirs(target_directory, exist_ok=True)

    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="xb",
            dir=target_directory,
            prefix=".configuration-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = ensure_within_base(temporary.name, target_directory)
            ensure_within_base(temporary_path, root)
            temporary.write(validated_configuration.to_canonical_json_bytes())
            temporary.flush()
            os.fsync(temporary.fileno())
        ensure_within_base(target, target_directory)
        ensure_within_base(target, root)
        os.replace(temporary_path, target)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                ensure_within_base(temporary_path, target_directory)
                ensure_within_base(temporary_path, root)
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


def validate_configuration_replacement(
    prior: BrainvisionConfigurationV1,
    candidate: BrainvisionConfigurationV1,
) -> None:
    """Validate frozen lineage invariants without authorizing a transition."""
    prior = _validated_configuration(prior)
    candidate = _validated_configuration(candidate)

    immutable_fields = (
        "schema_id",
        "stream_identity",
        "adapter_contract_id",
        "expected_operator_id",
        "expected_projection_id",
        "modulation_schema_id",
        "modulation_mapping_id",
        "modulation_profile_schema_id",
    )
    for field in immutable_fields:
        if getattr(prior, field) != getattr(candidate, field):
            raise BrainvisionConfigurationValidationError(
                field, "immutable_lineage_field_changed"
            )

    if candidate.last_accepted_source_sequence < prior.last_accepted_source_sequence:
        raise BrainvisionConfigurationValidationError(
            "last_accepted_source_sequence", "watermark_decrease"
        )

    if prior.lifecycle_status in {LIFECYCLE_ACTIVE, LIFECYCLE_SUSPENDED} and (
        candidate.theta != prior.theta
        or candidate.modulation_profile_id != prior.modulation_profile_id
    ):
        raise BrainvisionConfigurationValidationError(
            "theta", "profile_change_requires_disabled"
        )


__all__ = (
    "BrainvisionConfigurationV1",
    "BrainvisionConfigurationValidationError",
    "CONFIGURATION_FILENAME",
    "CONFIGURATION_SCHEMA_ID",
    "FRESH_LAST_ACCEPTED_SOURCE_SEQUENCE",
    "LIFECYCLE_ACTIVE",
    "LIFECYCLE_DISABLED",
    "LIFECYCLE_STATUSES",
    "LIFECYCLE_SUSPENDED",
    "MAX_LAST_ACCEPTED_SOURCE_SEQUENCE",
    "brainvision_configuration_path",
    "configuration_from_dict",
    "configuration_from_json_bytes",
    "fresh_disabled_brainvision_configuration",
    "load_brainvision_configuration",
    "validate_configuration_replacement",
    "write_brainvision_configuration",
)
