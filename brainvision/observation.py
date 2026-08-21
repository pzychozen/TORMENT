"""Typed Phase-2 FIRSTHAND_VISUAL observation contract.

This module defines the immutable descriptor and observation boundary only.
It deliberately contains no clock, VHE, lifecycle, persistence, ingress, or
production-runtime integration.
"""

from __future__ import annotations

import base64
from collections.abc import Mapping
from dataclasses import dataclass
import json
import re
from enum import Enum
from typing import Any, ClassVar


Q_SCALE = 1_000_000
"""Fixed-point scale for ``brainvision.low_level_descriptor.v1`` values."""

DESCRIPTOR_SCHEMA_ID = "brainvision.low_level_descriptor.v1"
DESCRIPTOR_COORDINATE_ORDER: tuple[str, str] = (
    "mean_luminance_q",
    "mean_adjacent_luminance_difference_q",
)
OBSERVATION_SCHEMA_ID = "brainvision.firsthand_visual_observation.v1"
IDENTITY_SCHEMA_ID = "brainvision.observation-id.v1"
OBSERVATION_ID_PREFIX = "bvobs1_"

MAX_SOURCE_SEQUENCE = (2**63) - 1
MIN_CAPTURE_TIME_UNIX_NS = -(2**63)
MAX_CAPTURE_TIME_UNIX_NS = (2**63) - 1

_IDENTIFIER_PATTERN = re.compile(r"[a-z][a-z0-9._-]{0,63}")
_SEMANTIC_EVENT_CLASS_PATTERN = re.compile(
    r"[a-z][a-z0-9_-]{0,31}:[a-z][a-z0-9._-]{0,63}"
)
_WORLD_EVENT_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
_BASE64URL_PATTERN = re.compile(r"[A-Za-z0-9_-]+")


class ObservationValidationError(ValueError):
    """A strict Phase-2 observation-contract validation failure."""

    def __init__(self, field: str, reason: str, detail: str | None = None) -> None:
        self.field = field
        self.reason = reason
        self.detail = detail
        message = f"{field}: {reason}"
        if detail is not None:
            message = f"{message} ({detail})"
        super().__init__(message)


class ObservationProvenanceType(str, Enum):
    """The single provenance type admitted by the Phase-2 DTO."""

    FIRSTHAND_VISUAL = "FIRSTHAND_VISUAL"


def _canonical_json_bytes(payload: Mapping[str, object]) -> bytes:
    """Encode a validated contract mapping in its frozen canonical form."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _require_exact_keys(
    raw: Mapping[str, object],
    expected_keys: frozenset[str],
    field: str,
) -> None:
    actual_keys = set(raw)
    missing = expected_keys - actual_keys
    unknown = actual_keys - expected_keys
    if missing or unknown:
        detail = f"missing={sorted(map(repr, missing))}; unknown={sorted(map(repr, unknown))}"
        raise ObservationValidationError(field, "unexpected_field_set", detail)


def _require_integer(value: object, field: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise ObservationValidationError(field, "must_be_exact_int")
    if not minimum <= value <= maximum:
        raise ObservationValidationError(
            field,
            "out_of_range",
            f"expected {minimum}..{maximum}",
        )
    return value


def _require_identifier(value: object, field: str) -> str:
    if type(value) is not str:
        raise ObservationValidationError(field, "must_be_ascii_identifier")
    if _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ObservationValidationError(field, "invalid_ascii_identifier")
    return value


def _require_semantic_event_class(value: object) -> str:
    if type(value) is not str:
        raise ObservationValidationError("semantic_event_class", "must_be_null_or_namespaced_token")
    if _SEMANTIC_EVENT_CLASS_PATTERN.fullmatch(value) is None:
        raise ObservationValidationError("semantic_event_class", "invalid_namespaced_token")
    return value


def _require_world_event_id(value: object) -> str:
    if type(value) is not str:
        raise ObservationValidationError("world_event_id", "must_be_null_or_ascii_token")
    if _WORLD_EVENT_ID_PATTERN.fullmatch(value) is None:
        raise ObservationValidationError("world_event_id", "invalid_ascii_token")
    return value


def _identity_payload(stream_identity: str, source_sequence: int) -> dict[str, object]:
    return {
        "identity_schema": IDENTITY_SCHEMA_ID,
        "source_sequence": source_sequence,
        "stream_identity": stream_identity,
    }


def derive_observation_id(stream_identity: str, source_sequence: int) -> str:
    """Return the reversible canonical ID bound exactly to stream and sequence."""
    stream_identity = _require_identifier(stream_identity, "stream_identity")
    source_sequence = _require_integer(
        source_sequence,
        "source_sequence",
        0,
        MAX_SOURCE_SEQUENCE,
    )
    encoded = base64.urlsafe_b64encode(
        _canonical_json_bytes(_identity_payload(stream_identity, source_sequence))
    ).rstrip(b"=")
    return OBSERVATION_ID_PREFIX + encoded.decode("ascii")


def decode_observation_id(observation_id: str) -> tuple[str, int]:
    """Decode and canonicality-check a Phase-2 observation identity."""
    if type(observation_id) is not str:
        raise ObservationValidationError("observation_id", "must_be_ascii_string")
    if not observation_id.startswith(OBSERVATION_ID_PREFIX):
        raise ObservationValidationError("observation_id", "invalid_prefix")

    encoded = observation_id.removeprefix(OBSERVATION_ID_PREFIX)
    if _BASE64URL_PATTERN.fullmatch(encoded) is None or len(encoded) % 4 == 1:
        raise ObservationValidationError("observation_id", "invalid_base64url")

    try:
        padding = "=" * ((4 - (len(encoded) % 4)) % 4)
        decoded = base64.urlsafe_b64decode((encoded + padding).encode("ascii"))
        payload = json.loads(decoded.decode("ascii"))
    except (UnicodeDecodeError, ValueError):
        raise ObservationValidationError("observation_id", "invalid_identity_payload") from None

    if not isinstance(payload, Mapping):
        raise ObservationValidationError("observation_id", "identity_payload_must_be_mapping")
    _require_exact_keys(
        payload,
        frozenset({"identity_schema", "stream_identity", "source_sequence"}),
        "observation_id",
    )
    if payload["identity_schema"] != IDENTITY_SCHEMA_ID:
        raise ObservationValidationError("observation_id", "incorrect_identity_schema")

    try:
        stream_identity = _require_identifier(payload["stream_identity"], "stream_identity")
        source_sequence = _require_integer(
            payload["source_sequence"],
            "source_sequence",
            0,
            MAX_SOURCE_SEQUENCE,
        )
    except ObservationValidationError:
        raise ObservationValidationError("observation_id", "invalid_identity_payload") from None

    if observation_id != derive_observation_id(stream_identity, source_sequence):
        raise ObservationValidationError("observation_id", "noncanonical_identity_encoding")
    return stream_identity, source_sequence


@dataclass(frozen=True, kw_only=True)
class LowLevelVisualDescriptorV1:
    """One-frame, non-semantic low-level descriptor encoded as exact integers.

    ``mean_luminance_q`` is the arithmetic mean of the upstream
    adapter-contract-defined normalized luminance analysis plane.  The second
    field is the arithmetic mean absolute luminance difference over that
    adapter contract's adjacency relation.  Each channel is derived from one
    visual observation only; neither is temporal or multiframe.
    """

    mean_luminance_q: int
    mean_adjacent_luminance_difference_q: int

    schema_id: ClassVar[str] = DESCRIPTOR_SCHEMA_ID

    def __post_init__(self) -> None:
        _require_integer(self.mean_luminance_q, "mean_luminance_q", 0, Q_SCALE)
        _require_integer(
            self.mean_adjacent_luminance_difference_q,
            "mean_adjacent_luminance_difference_q",
            0,
            Q_SCALE,
        )

    def to_dict(self) -> dict[str, object]:
        """Return the exact descriptor contract mapping."""
        return {
            "schema_id": self.schema_id,
            "mean_luminance_q": self.mean_luminance_q,
            "mean_adjacent_luminance_difference_q": self.mean_adjacent_luminance_difference_q,
        }

    def to_canonical_json_bytes(self) -> bytes:
        """Return canonical ASCII JSON bytes for fixture and replay evidence."""
        return _canonical_json_bytes(self.to_dict())

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> "LowLevelVisualDescriptorV1":
        """Parse a strict descriptor mapping without coercion."""
        if not isinstance(raw, Mapping):
            raise ObservationValidationError("descriptor", "must_be_mapping")
        _require_exact_keys(
            raw,
            frozenset(
                {
                    "schema_id",
                    "mean_luminance_q",
                    "mean_adjacent_luminance_difference_q",
                }
            ),
            "descriptor",
        )
        if raw["schema_id"] != cls.schema_id:
            raise ObservationValidationError("descriptor.schema_id", "incorrect_schema")
        return cls(
            mean_luminance_q=raw["mean_luminance_q"],
            mean_adjacent_luminance_difference_q=raw[
                "mean_adjacent_luminance_difference_q"
            ],
        )


@dataclass(frozen=True, kw_only=True)
class FirsthandVisualObservationV1:
    """A strict typed observation before later lifecycle and ingress phases.

    The DTO does not establish admission.  It validates only one proposed
    FIRSTHAND_VISUAL observation and its deterministic stream/sequence ID.
    """

    provenance_type: ObservationProvenanceType
    stream_identity: str
    source_sequence: int
    observation_id: str
    descriptor: LowLevelVisualDescriptorV1
    adapter_id: str
    adapter_contract_id: str
    source_capture_time_unix_ns: int | None = None
    confidence_q: int | None = None
    semantic_event_class: str | None = None
    world_event_id: str | None = None

    schema_id: ClassVar[str] = OBSERVATION_SCHEMA_ID

    def __post_init__(self) -> None:
        if self.provenance_type is not ObservationProvenanceType.FIRSTHAND_VISUAL:
            raise ObservationValidationError("provenance_type", "must_be_FIRSTHAND_VISUAL")
        _require_identifier(self.stream_identity, "stream_identity")
        _require_integer(self.source_sequence, "source_sequence", 0, MAX_SOURCE_SEQUENCE)
        if type(self.descriptor) is not LowLevelVisualDescriptorV1:
            raise ObservationValidationError("descriptor", "must_be_low_level_descriptor_v1")
        _require_identifier(self.adapter_id, "adapter_id")
        _require_identifier(self.adapter_contract_id, "adapter_contract_id")

        if self.source_capture_time_unix_ns is not None:
            _require_integer(
                self.source_capture_time_unix_ns,
                "source_capture_time_unix_ns",
                MIN_CAPTURE_TIME_UNIX_NS,
                MAX_CAPTURE_TIME_UNIX_NS,
            )
        if self.confidence_q is not None:
            _require_integer(self.confidence_q, "confidence_q", 0, Q_SCALE)
        if self.semantic_event_class is not None:
            _require_semantic_event_class(self.semantic_event_class)
        if self.world_event_id is not None:
            _require_world_event_id(self.world_event_id)

        if type(self.observation_id) is not str:
            raise ObservationValidationError("observation_id", "must_be_ascii_string")
        expected_observation_id = derive_observation_id(
            self.stream_identity,
            self.source_sequence,
        )
        if self.observation_id != expected_observation_id:
            raise ObservationValidationError("observation_id", "mismatched_stream_sequence_identity")
        decode_observation_id(self.observation_id)

    def to_dict(self) -> dict[str, object]:
        """Return the exact observation contract mapping, including null optionals."""
        return {
            "schema_id": self.schema_id,
            "provenance_type": self.provenance_type.value,
            "stream_identity": self.stream_identity,
            "source_sequence": self.source_sequence,
            "observation_id": self.observation_id,
            "descriptor": self.descriptor.to_dict(),
            "adapter_id": self.adapter_id,
            "adapter_contract_id": self.adapter_contract_id,
            "source_capture_time_unix_ns": self.source_capture_time_unix_ns,
            "confidence_q": self.confidence_q,
            "semantic_event_class": self.semantic_event_class,
            "world_event_id": self.world_event_id,
        }

    def to_canonical_json_bytes(self) -> bytes:
        """Return canonical ASCII JSON bytes for the full observation contract."""
        return _canonical_json_bytes(self.to_dict())

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> "FirsthandVisualObservationV1":
        """Parse a strict observation mapping without field or type coercion."""
        if not isinstance(raw, Mapping):
            raise ObservationValidationError("observation", "must_be_mapping")
        _require_exact_keys(
            raw,
            frozenset(
                {
                    "schema_id",
                    "provenance_type",
                    "stream_identity",
                    "source_sequence",
                    "observation_id",
                    "descriptor",
                    "adapter_id",
                    "adapter_contract_id",
                    "source_capture_time_unix_ns",
                    "confidence_q",
                    "semantic_event_class",
                    "world_event_id",
                }
            ),
            "observation",
        )
        if raw["schema_id"] != cls.schema_id:
            raise ObservationValidationError("schema_id", "incorrect_schema")
        if raw["provenance_type"] != ObservationProvenanceType.FIRSTHAND_VISUAL.value:
            raise ObservationValidationError("provenance_type", "must_be_FIRSTHAND_VISUAL")
        return cls(
            provenance_type=ObservationProvenanceType.FIRSTHAND_VISUAL,
            stream_identity=raw["stream_identity"],
            source_sequence=raw["source_sequence"],
            observation_id=raw["observation_id"],
            descriptor=LowLevelVisualDescriptorV1.from_dict(raw["descriptor"]),
            adapter_id=raw["adapter_id"],
            adapter_contract_id=raw["adapter_contract_id"],
            source_capture_time_unix_ns=raw["source_capture_time_unix_ns"],
            confidence_q=raw["confidence_q"],
            semantic_event_class=raw["semantic_event_class"],
            world_event_id=raw["world_event_id"],
        )


def validate_firsthand_visual_observation(
    raw: Mapping[str, Any],
) -> FirsthandVisualObservationV1:
    """Validate a raw contract mapping as the sole Phase-2 observation type."""
    return FirsthandVisualObservationV1.from_dict(raw)


__all__ = (
    "DESCRIPTOR_COORDINATE_ORDER",
    "DESCRIPTOR_SCHEMA_ID",
    "IDENTITY_SCHEMA_ID",
    "MAX_SOURCE_SEQUENCE",
    "OBSERVATION_ID_PREFIX",
    "OBSERVATION_SCHEMA_ID",
    "FirsthandVisualObservationV1",
    "LowLevelVisualDescriptorV1",
    "ObservationProvenanceType",
    "ObservationValidationError",
    "Q_SCALE",
    "decode_observation_id",
    "derive_observation_id",
    "validate_firsthand_visual_observation",
)
