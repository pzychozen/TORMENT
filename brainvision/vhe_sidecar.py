"""Frozen Phase-9 mechanical VHE continuation sidecar boundary.

This module persists and validates recursive continuation state only. It has no
lifecycle policy, recovery actions, locks, Fabric integration, or ingress.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import os
from os import PathLike
import tempfile
from typing import ClassVar, Final

from brainvision.configuration import (
    CONFIGURATION_SCHEMA_ID,
    LIFECYCLE_DISABLED,
    MAX_LAST_ACCEPTED_SOURCE_SEQUENCE,
    BrainvisionConfigurationV1,
    BrainvisionConfigurationValidationError,
    brainvision_configuration_path,
    configuration_from_dict,
)
from brainvision.vhe import (
    FastTrace,
    PersistentContext,
    SemanticRegister,
    SemanticRegisterEntry,
    VheState,
    fresh_vhe_state,
)
from torment_service.pathing import ensure_within_base, stable_filename


VHE_SIDECAR_SCHEMA_ID: Final = "brainvision.vhe.sidecar.v1"
VHE_SIDECAR_FILENAME: Final = "vhe_state.json"

EQUAL: Final = "EQUAL"
SIDECAR_AHEAD: Final = "SIDECAR_AHEAD"
CONFIG_AHEAD: Final = "CONFIG_AHEAD"

_TOP_LEVEL_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "schema_id",
        "configuration_schema_id",
        "stream_identity",
        "adapter_contract_id",
        "accepted_source_sequence",
        "expected_operator_id",
        "expected_projection_id",
        "modulation_schema_id",
        "modulation_mapping_id",
        "modulation_profile_schema_id",
        "theta",
        "modulation_profile_id",
        "committed_active_time_ns",
        "vhe_state",
    }
)
_VHE_STATE_FIELDS: Final[frozenset[str]] = frozenset(
    {"fast_trace", "persistent_context", "semantic_register"}
)
_FAST_TRACE_FIELDS: Final[frozenset[str]] = frozenset(
    {"amplitude_1_q", "amplitude_2_q", "remaining_ns"}
)
_PERSISTENT_CONTEXT_FIELDS: Final[frozenset[str]] = frozenset(
    {"luminance_q", "contrast_q", "orientation_q"}
)
_SEMANTIC_REGISTER_FIELDS: Final[frozenset[str]] = frozenset(
    {"entries", "open_semantic_event_class"}
)
_SEMANTIC_ENTRY_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "semantic_event_class",
        "first_seen_active_time_ns",
        "last_seen_active_time_ns",
        "occurrence_count",
    }
)


class VheSidecarValidationError(ValueError):
    """A strict frozen Phase-9 sidecar validation failure."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


def _require_exact_keys(
    raw: Mapping[str, object],
    expected: frozenset[str],
    field: str,
) -> None:
    supplied = set(raw)
    missing = expected - supplied
    if missing:
        raise VheSidecarValidationError(f"{field}.{sorted(missing)[0]}", "missing_field")
    unknown = supplied - expected
    if unknown:
        raise VheSidecarValidationError(f"{field}.{sorted(unknown)[0]}", "unknown_field")


def _require_mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise VheSidecarValidationError(field, "must_be_mapping")
    return value


def _require_exact_int(value: object, field: str) -> int:
    if type(value) is not int:
        raise VheSidecarValidationError(field, "must_be_exact_int")
    return value


def _require_nonnegative_exact_int(value: object, field: str) -> int:
    value = _require_exact_int(value, field)
    if value < 0:
        raise VheSidecarValidationError(field, "must_be_nonnegative")
    return value


def _require_accepted_source_sequence(value: object) -> int:
    value = _require_exact_int(value, "accepted_source_sequence")
    if not -1 <= value <= MAX_LAST_ACCEPTED_SOURCE_SEQUENCE:
        raise VheSidecarValidationError("accepted_source_sequence", "out_of_range")
    return value


def _canonical_json_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _object_from_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for field, value in pairs:
        if field in result:
            raise VheSidecarValidationError(field, "duplicate_field")
        result[field] = value
    return result


def _fast_trace_from_dict(raw: object) -> FastTrace:
    mapping = _require_mapping(raw, "vhe_state.fast_trace")
    _require_exact_keys(mapping, _FAST_TRACE_FIELDS, "vhe_state.fast_trace")
    return FastTrace(
        amplitude_1_q=mapping["amplitude_1_q"],
        amplitude_2_q=mapping["amplitude_2_q"],
        remaining_ns=mapping["remaining_ns"],
    )


def _persistent_context_from_dict(raw: object) -> PersistentContext:
    mapping = _require_mapping(raw, "vhe_state.persistent_context")
    _require_exact_keys(
        mapping,
        _PERSISTENT_CONTEXT_FIELDS,
        "vhe_state.persistent_context",
    )
    return PersistentContext(
        luminance_q=mapping["luminance_q"],
        contrast_q=mapping["contrast_q"],
        orientation_q=mapping["orientation_q"],
    )


def _semantic_entry_from_dict(raw: object) -> SemanticRegisterEntry:
    mapping = _require_mapping(raw, "vhe_state.semantic_register.entries[]")
    _require_exact_keys(
        mapping,
        _SEMANTIC_ENTRY_FIELDS,
        "vhe_state.semantic_register.entries[]",
    )
    return SemanticRegisterEntry(
        semantic_event_class=mapping["semantic_event_class"],
        first_seen_active_time_ns=mapping["first_seen_active_time_ns"],
        last_seen_active_time_ns=mapping["last_seen_active_time_ns"],
        occurrence_count=mapping["occurrence_count"],
    )


def _semantic_register_from_dict(raw: object) -> SemanticRegister:
    mapping = _require_mapping(raw, "vhe_state.semantic_register")
    _require_exact_keys(
        mapping,
        _SEMANTIC_REGISTER_FIELDS,
        "vhe_state.semantic_register",
    )
    entries_raw = mapping["entries"]
    if type(entries_raw) is not list:
        raise VheSidecarValidationError("vhe_state.semantic_register.entries", "must_be_list")
    entries = tuple(_semantic_entry_from_dict(entry) for entry in entries_raw)
    return SemanticRegister(
        entries=entries,
        open_semantic_event_class=mapping["open_semantic_event_class"],
    )


def _vhe_state_from_dict(raw: object) -> VheState:
    mapping = _require_mapping(raw, "vhe_state")
    _require_exact_keys(mapping, _VHE_STATE_FIELDS, "vhe_state")
    return VheState(
        fast_trace=_fast_trace_from_dict(mapping["fast_trace"]),
        persistent_context=_persistent_context_from_dict(mapping["persistent_context"]),
        semantic_register=_semantic_register_from_dict(mapping["semantic_register"]),
    )


def _vhe_state_to_dict(state: VheState) -> dict[str, object]:
    if type(state) is not VheState:
        raise VheSidecarValidationError("vhe_state", "must_be_vhe_state")
    return {
        "fast_trace": {
            "amplitude_1_q": state.fast_trace.amplitude_1_q,
            "amplitude_2_q": state.fast_trace.amplitude_2_q,
            "remaining_ns": state.fast_trace.remaining_ns,
        },
        "persistent_context": {
            "luminance_q": state.persistent_context.luminance_q,
            "contrast_q": state.persistent_context.contrast_q,
            "orientation_q": state.persistent_context.orientation_q,
        },
        "semantic_register": {
            "entries": [
                {
                    "semantic_event_class": entry.semantic_event_class,
                    "first_seen_active_time_ns": entry.first_seen_active_time_ns,
                    "last_seen_active_time_ns": entry.last_seen_active_time_ns,
                    "occurrence_count": entry.occurrence_count,
                }
                for entry in state.semantic_register.entries
            ],
            "open_semantic_event_class": state.semantic_register.open_semantic_event_class,
        },
    }


def _validate_configuration_bound_fields(sidecar: "VheSidecarV1") -> None:
    """Use the frozen Phase-8 authority for shared lineage/profile validation."""
    try:
        BrainvisionConfigurationV1(
            lifecycle_status=LIFECYCLE_DISABLED,
            stream_identity=sidecar.stream_identity,
            adapter_contract_id=sidecar.adapter_contract_id,
            last_accepted_source_sequence=-1,
            expected_operator_id=sidecar.expected_operator_id,
            expected_projection_id=sidecar.expected_projection_id,
            modulation_schema_id=sidecar.modulation_schema_id,
            modulation_mapping_id=sidecar.modulation_mapping_id,
            modulation_profile_schema_id=sidecar.modulation_profile_schema_id,
            theta=sidecar.theta,
            modulation_profile_id=sidecar.modulation_profile_id,
        )
    except BrainvisionConfigurationValidationError as error:
        raise VheSidecarValidationError(error.field, error.reason) from error


@dataclass(frozen=True, kw_only=True)
class VheSidecarV1:
    """One immutable exact recursive continuation artifact."""

    configuration_schema_id: str
    stream_identity: str
    adapter_contract_id: str
    accepted_source_sequence: int
    expected_operator_id: str
    expected_projection_id: str
    modulation_schema_id: str
    modulation_mapping_id: str
    modulation_profile_schema_id: str
    theta: int
    modulation_profile_id: str
    committed_active_time_ns: int
    vhe_state: VheState

    schema_id: ClassVar[str] = VHE_SIDECAR_SCHEMA_ID

    def __post_init__(self) -> None:
        if (
            type(self.configuration_schema_id) is not str
            or self.configuration_schema_id != CONFIGURATION_SCHEMA_ID
        ):
            raise VheSidecarValidationError(
                "configuration_schema_id", "configuration_schema_mismatch"
            )
        _require_accepted_source_sequence(self.accepted_source_sequence)
        _validate_configuration_bound_fields(self)
        committed_active_time_ns = _require_nonnegative_exact_int(
            self.committed_active_time_ns,
            "committed_active_time_ns",
        )
        if type(self.vhe_state) is not VheState:
            raise VheSidecarValidationError("vhe_state", "must_be_vhe_state")
        for entry in self.vhe_state.semantic_register.entries:
            if (
                entry.first_seen_active_time_ns > committed_active_time_ns
                or entry.last_seen_active_time_ns > committed_active_time_ns
            ):
                raise VheSidecarValidationError(
                    "vhe_state.semantic_register.entries",
                    "semantic_time_after_committed_time",
                )

    def to_dict(self) -> dict[str, object]:
        """Return a fresh exact sidecar mapping."""
        return {
            "schema_id": self.schema_id,
            "configuration_schema_id": self.configuration_schema_id,
            "stream_identity": self.stream_identity,
            "adapter_contract_id": self.adapter_contract_id,
            "accepted_source_sequence": self.accepted_source_sequence,
            "expected_operator_id": self.expected_operator_id,
            "expected_projection_id": self.expected_projection_id,
            "modulation_schema_id": self.modulation_schema_id,
            "modulation_mapping_id": self.modulation_mapping_id,
            "modulation_profile_schema_id": self.modulation_profile_schema_id,
            "theta": self.theta,
            "modulation_profile_id": self.modulation_profile_id,
            "committed_active_time_ns": self.committed_active_time_ns,
            "vhe_state": _vhe_state_to_dict(self.vhe_state),
        }

    def to_canonical_json_bytes(self) -> bytes:
        """Return the exact canonical ASCII representation."""
        return _canonical_json_bytes(self.to_dict())

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> "VheSidecarV1":
        """Strictly parse one complete sidecar mapping."""
        return vhe_sidecar_from_dict(raw)


def vhe_sidecar_from_dict(raw: Mapping[str, object]) -> VheSidecarV1:
    """Strictly parse a complete sidecar mapping without coercion."""
    mapping = _require_mapping(raw, "sidecar")
    _require_exact_keys(mapping, _TOP_LEVEL_FIELDS, "sidecar")
    if mapping["schema_id"] != VHE_SIDECAR_SCHEMA_ID:
        raise VheSidecarValidationError("schema_id", "schema_mismatch")
    return VheSidecarV1(
        configuration_schema_id=mapping["configuration_schema_id"],
        stream_identity=mapping["stream_identity"],
        adapter_contract_id=mapping["adapter_contract_id"],
        accepted_source_sequence=mapping["accepted_source_sequence"],
        expected_operator_id=mapping["expected_operator_id"],
        expected_projection_id=mapping["expected_projection_id"],
        modulation_schema_id=mapping["modulation_schema_id"],
        modulation_mapping_id=mapping["modulation_mapping_id"],
        modulation_profile_schema_id=mapping["modulation_profile_schema_id"],
        theta=mapping["theta"],
        modulation_profile_id=mapping["modulation_profile_id"],
        committed_active_time_ns=mapping["committed_active_time_ns"],
        vhe_state=_vhe_state_from_dict(mapping["vhe_state"]),
    )


def vhe_sidecar_from_json_bytes(raw: bytes) -> VheSidecarV1:
    """Decode duplicate-safe strict JSON bytes into a sidecar."""
    if type(raw) is not bytes:
        raise TypeError("sidecar JSON must be bytes")
    return vhe_sidecar_from_dict(
        json.loads(raw.decode("ascii"), object_pairs_hook=_object_from_pairs)
    )


def _validated_configuration(
    configuration: BrainvisionConfigurationV1,
) -> BrainvisionConfigurationV1:
    if type(configuration) is not BrainvisionConfigurationV1:
        raise TypeError("configuration must be BrainvisionConfigurationV1")
    return configuration_from_dict(configuration.to_dict())


def _validated_sidecar(sidecar: VheSidecarV1) -> VheSidecarV1:
    if type(sidecar) is not VheSidecarV1:
        raise TypeError("sidecar must be VheSidecarV1")
    return vhe_sidecar_from_dict(sidecar.to_dict())


def fresh_vhe_sidecar(configuration: BrainvisionConfigurationV1) -> VheSidecarV1:
    """Build a fresh sidecar without authorizing a lifecycle operation or write."""
    configuration = _validated_configuration(configuration)
    return VheSidecarV1(
        configuration_schema_id=configuration.schema_id,
        stream_identity=configuration.stream_identity,
        adapter_contract_id=configuration.adapter_contract_id,
        accepted_source_sequence=configuration.last_accepted_source_sequence,
        expected_operator_id=configuration.expected_operator_id,
        expected_projection_id=configuration.expected_projection_id,
        modulation_schema_id=configuration.modulation_schema_id,
        modulation_mapping_id=configuration.modulation_mapping_id,
        modulation_profile_schema_id=configuration.modulation_profile_schema_id,
        theta=configuration.theta,
        modulation_profile_id=configuration.modulation_profile_id,
        committed_active_time_ns=0,
        vhe_state=fresh_vhe_state(),
    )


def _resolved_data_root(data_root: str | PathLike[str]) -> str:
    root = os.fspath(data_root)
    if type(root) is not str:
        raise TypeError("data_root must be a string path")
    return os.path.realpath(root)


def vhe_sidecar_path(
    data_root: str | PathLike[str],
    workspace_id: str,
    agent_id: str,
) -> str:
    """Return the contained sidecar path without creating any filesystem entry."""
    root = _resolved_data_root(data_root)
    configuration_path = brainvision_configuration_path(root, workspace_id, agent_id)
    brainvision_directory = os.path.dirname(configuration_path)
    target = stable_filename(brainvision_directory, VHE_SIDECAR_FILENAME)
    return ensure_within_base(target, root)


def load_vhe_sidecar(
    data_root: str | PathLike[str],
    workspace_id: str,
    agent_id: str,
) -> VheSidecarV1 | None:
    """Load a sidecar, returning ``None`` only when its file is absent."""
    target = vhe_sidecar_path(data_root, workspace_id, agent_id)
    try:
        with open(target, "rb") as source:
            return vhe_sidecar_from_json_bytes(source.read())
    except FileNotFoundError:
        return None


def write_vhe_sidecar(
    data_root: str | PathLike[str],
    workspace_id: str,
    agent_id: str,
    sidecar: VheSidecarV1,
) -> None:
    """Atomically persist an already-authorized sidecar without creating paths."""
    sidecar = _validated_sidecar(sidecar)
    root = _resolved_data_root(data_root)
    target = vhe_sidecar_path(root, workspace_id, agent_id)
    brainvision_directory = os.path.dirname(target)
    ensure_within_base(brainvision_directory, root)
    ensure_within_base(target, root)
    if not os.path.exists(brainvision_directory):
        raise FileNotFoundError(brainvision_directory)
    if not os.path.isdir(brainvision_directory):
        raise NotADirectoryError(brainvision_directory)

    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="xb",
            dir=brainvision_directory,
            prefix=".vhe-state-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = ensure_within_base(temporary.name, brainvision_directory)
            ensure_within_base(temporary_path, root)
            temporary.write(sidecar.to_canonical_json_bytes())
            temporary.flush()
            os.fsync(temporary.fileno())
        ensure_within_base(target, brainvision_directory)
        ensure_within_base(target, root)
        os.replace(temporary_path, target)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                ensure_within_base(temporary_path, brainvision_directory)
                ensure_within_base(temporary_path, root)
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


def validate_configuration_sidecar_compatibility(
    configuration: BrainvisionConfigurationV1,
    sidecar: VheSidecarV1,
) -> str:
    """Classify only identity-compatible configuration/sidecar sequences."""
    configuration = _validated_configuration(configuration)
    sidecar = _validated_sidecar(sidecar)
    pairs = (
        ("configuration_schema_id", configuration.schema_id, sidecar.configuration_schema_id),
        ("stream_identity", configuration.stream_identity, sidecar.stream_identity),
        ("adapter_contract_id", configuration.adapter_contract_id, sidecar.adapter_contract_id),
        ("expected_operator_id", configuration.expected_operator_id, sidecar.expected_operator_id),
        ("expected_projection_id", configuration.expected_projection_id, sidecar.expected_projection_id),
        ("modulation_schema_id", configuration.modulation_schema_id, sidecar.modulation_schema_id),
        ("modulation_mapping_id", configuration.modulation_mapping_id, sidecar.modulation_mapping_id),
        (
            "modulation_profile_schema_id",
            configuration.modulation_profile_schema_id,
            sidecar.modulation_profile_schema_id,
        ),
        ("theta", configuration.theta, sidecar.theta),
        ("modulation_profile_id", configuration.modulation_profile_id, sidecar.modulation_profile_id),
    )
    for field, configuration_value, sidecar_value in pairs:
        if configuration_value != sidecar_value:
            raise VheSidecarValidationError(
                field,
                "configuration_sidecar_identity_mismatch",
            )
    if sidecar.accepted_source_sequence == configuration.last_accepted_source_sequence:
        return EQUAL
    if sidecar.accepted_source_sequence > configuration.last_accepted_source_sequence:
        return SIDECAR_AHEAD
    return CONFIG_AHEAD


__all__ = (
    "CONFIG_AHEAD",
    "EQUAL",
    "SIDECAR_AHEAD",
    "VHE_SIDECAR_FILENAME",
    "VHE_SIDECAR_SCHEMA_ID",
    "VheSidecarV1",
    "VheSidecarValidationError",
    "fresh_vhe_sidecar",
    "load_vhe_sidecar",
    "validate_configuration_sidecar_compatibility",
    "vhe_sidecar_from_dict",
    "vhe_sidecar_from_json_bytes",
    "vhe_sidecar_path",
    "write_vhe_sidecar",
)
