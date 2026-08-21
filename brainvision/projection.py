"""Frozen Phase-5 bounded relational projection of Phase-4 VHE state.

This module is a pure read over immutable VHE state.  It owns no recursive
state, clock, persistence, lifecycle, ingress, or runtime integration.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
import re
from types import MappingProxyType
from typing import Final

from brainvision.vhe import (
    OPERATOR_ID,
    Q,
    RNE_ALGORITHM_ID,
    SemanticRegisterEntry,
    VheState,
    effective_fast_trace,
    evolve_vhe_state_as_of,
    mul_q,
    round_half_even_division,
)


PROJECTION_SCHEMA_ID: Final = "brainvision.projection.v1"
PROJECTION_ALGORITHM_ID: Final = "brainvision.projection.fixed16-relational.v1"
PROJECTION_ID_PREFIX: Final = "bvproj1_"
PROJECTION_STEPS: Final = 16
PROJECTION_QUANTUM_Q: Final = Q // PROJECTION_STEPS
PROJECTION_HALF_QUANTUM_Q: Final = PROJECTION_QUANTUM_Q // 2

CURRENT_ACTIVITY_ROLE: Final = "CURRENT_ACTIVITY_ROLE"
RETAINED_HISTORY_ROLE: Final = "RETAINED_HISTORY_ROLE"
PRESENT_HISTORY_RELATION_ROLE: Final = "PRESENT_HISTORY_RELATION_ROLE"
TRAJECTORY_ROLE: Final = "TRAJECTORY_ROLE"
OPEN_EVENT_ROLE: Final = "OPEN_EVENT_ROLE"
RECURRENCE_ROLE: Final = "RECURRENCE_ROLE"

ROLE_BINDINGS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    CURRENT_ACTIVITY_ROLE: ("current_activity_code",),
    RETAINED_HISTORY_ROLE: ("retained_history_code",),
    PRESENT_HISTORY_RELATION_ROLE: ("present_history_relation_code",),
    TRAJECTORY_ROLE: ("trajectory_code",),
    OPEN_EVENT_ROLE: ("open_event_class",),
    RECURRENCE_ROLE: ("recurrence_code",),
})

ACCEPTANCE_RELEVANT_FIELD_SETS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "retained_current_equality": ("current_activity_code",),
    "retained_history_difference": ("retained_history_code",),
    "order_current_equality": ("current_activity_code",),
    "order_history_difference": ("trajectory_code",),
    "present_history_relation": ("present_history_relation_code",),
    "open_event": ("open_event_class",),
    "recurrence": ("recurrence_code",),
})

_PROJECTION_VALUE_FIELDS: Final = frozenset(
    {
        "current_activity_code",
        "retained_history_code",
        "present_history_relation_code",
        "trajectory_code",
        "open_event_class",
        "recurrence_code",
    }
)
_SEMANTIC_EVENT_CLASS_PATTERN = re.compile(
    r"[a-z][a-z0-9_-]{0,31}:[a-z][a-z0-9._-]{0,63}"
)


class ProjectionValidationError(ValueError):
    """A frozen Phase-5 projection value or comparison was invalid."""

    def __init__(self, field: str, reason: str, detail: str | None = None) -> None:
        self.field = field
        self.reason = reason
        self.detail = detail
        message = f"{field}: {reason}"
        if detail is not None:
            message = f"{message} ({detail})"
        super().__init__(message)


def _require_exact_int(value: object, field: str) -> int:
    if type(value) is not int:
        raise ProjectionValidationError(field, "must_be_exact_int")
    return value


def _require_range(value: object, field: str, minimum: int, maximum: int) -> int:
    value = _require_exact_int(value, field)
    if not minimum <= value <= maximum:
        raise ProjectionValidationError(field, "out_of_range", f"expected {minimum}..{maximum}")
    return value


def _require_open_event_class(value: object) -> str:
    if type(value) is not str:
        raise ProjectionValidationError("open_event_class", "must_be_null_or_phase_2_token")
    if _SEMANTIC_EVENT_CLASS_PATTERN.fullmatch(value) is None:
        raise ProjectionValidationError("open_event_class", "invalid_phase_2_token")
    return value


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return min(max(value, minimum), maximum)


def unsigned_code(value_q: int) -> int:
    """Quantize a frozen unsigned normalized q value with Phase-4 RNE."""
    value_q = _require_range(value_q, "unsigned_value_q", 0, Q)
    code = round_half_even_division(PROJECTION_STEPS * value_q, Q)
    return _require_range(code, "unsigned_code", 0, PROJECTION_STEPS)


def signed_code(value_q: int) -> int:
    """Quantize a frozen signed normalized q value with Phase-4 RNE."""
    value_q = _require_range(value_q, "signed_value_q", -Q, Q)
    code = round_half_even_division(PROJECTION_STEPS * value_q, Q)
    return _require_range(code, "signed_code", -PROJECTION_STEPS, PROJECTION_STEPS)


@dataclass(frozen=True, kw_only=True)
class BrainvisionProjectionV1:
    """One canonical bounded summary; it intentionally contains no raw VHE state."""

    current_activity_code: int
    retained_history_code: int
    present_history_relation_code: int
    trajectory_code: int
    open_event_class: str | None
    recurrence_code: int

    def __post_init__(self) -> None:
        _require_range(
            self.current_activity_code,
            "current_activity_code",
            0,
            PROJECTION_STEPS,
        )
        _require_range(
            self.retained_history_code,
            "retained_history_code",
            0,
            PROJECTION_STEPS,
        )
        _require_range(
            self.present_history_relation_code,
            "present_history_relation_code",
            -PROJECTION_STEPS,
            PROJECTION_STEPS,
        )
        _require_range(
            self.trajectory_code,
            "trajectory_code",
            -PROJECTION_STEPS,
            PROJECTION_STEPS,
        )
        _require_range(self.recurrence_code, "recurrence_code", 0, 2)
        if self.open_event_class is None:
            if self.recurrence_code != 0:
                raise ProjectionValidationError(
                    "recurrence_code",
                    "must_be_zero_without_open_event",
                )
            return
        _require_open_event_class(self.open_event_class)
        if self.recurrence_code == 0:
            raise ProjectionValidationError(
                "recurrence_code",
                "must_be_nonzero_with_open_event",
            )

    @property
    def schema_id(self) -> str:
        """Return the frozen serialized projection schema identifier."""
        return PROJECTION_SCHEMA_ID

    @property
    def projection_id(self) -> str:
        """Return the frozen identity of the authoritative manifest core bytes."""
        return PROJECTION_ID

    @property
    def operator_id(self) -> str:
        """Return the exact frozen Phase-4 operator identity this projects."""
        return OPERATOR_ID

    def to_dict(self) -> dict[str, object]:
        """Return the exact canonical projection mapping, including null optionals."""
        return {
            "schema_id": self.schema_id,
            "projection_id": self.projection_id,
            "operator_id": self.operator_id,
            "current_activity_code": self.current_activity_code,
            "retained_history_code": self.retained_history_code,
            "present_history_relation_code": self.present_history_relation_code,
            "trajectory_code": self.trajectory_code,
            "open_event_class": self.open_event_class,
            "recurrence_code": self.recurrence_code,
        }

    def to_canonical_json_bytes(self) -> bytes:
        """Return canonical ASCII JSON bytes for exact projection comparisons."""
        return _canonical_json_bytes(self.to_dict())


def _recurrence_code_for_open_entry(
    state: VheState,
) -> tuple[str | None, int]:
    open_event_class = state.semantic_register.open_semantic_event_class
    if open_event_class is None:
        return None, 0
    entry = next(
        entry
        for entry in state.semantic_register.entries
        if entry.semantic_event_class == open_event_class
    )
    if type(entry) is not SemanticRegisterEntry:
        raise ProjectionValidationError("semantic_register", "invalid_open_entry")
    return open_event_class, 1 if entry.occurrence_count == 1 else 2


def project_vhe_state(
    state: VheState,
    elapsed_active_time_ns: int,
) -> BrainvisionProjectionV1:
    """Purely project committed VHE state at an exact elapsed active-time read."""
    if type(state) is not VheState:
        raise ProjectionValidationError("state", "must_be_vhe_state")
    elapsed_active_time_ns = _require_exact_int(
        elapsed_active_time_ns,
        "elapsed_active_time_ns",
    )
    if elapsed_active_time_ns < 0:
        raise ProjectionValidationError("elapsed_active_time_ns", "must_be_nonnegative")

    as_of_state = evolve_vhe_state_as_of(state, elapsed_active_time_ns)
    f_eff_1_q, f_eff_2_q = effective_fast_trace(as_of_state.fast_trace)
    context = as_of_state.persistent_context
    relation_raw_q = _clamp(
        mul_q(f_eff_1_q, context.luminance_q)
        + mul_q(f_eff_2_q, context.contrast_q),
        -Q,
        Q,
    )
    open_event_class, recurrence_code = _recurrence_code_for_open_entry(as_of_state)
    return BrainvisionProjectionV1(
        current_activity_code=unsigned_code(max(abs(f_eff_1_q), abs(f_eff_2_q))),
        retained_history_code=unsigned_code(
            max(
                abs(context.luminance_q),
                abs(context.contrast_q),
                abs(context.orientation_q),
            )
        ),
        present_history_relation_code=signed_code(relation_raw_q),
        trajectory_code=signed_code(context.orientation_q),
        open_event_class=open_event_class,
        recurrence_code=recurrence_code,
    )


def within_projection_quantum(
    left: BrainvisionProjectionV1,
    right: BrainvisionProjectionV1,
    relevant_fields: tuple[str, ...],
) -> bool:
    """Compare named encoded fields by exact equality, never by tolerance."""
    if type(left) is not BrainvisionProjectionV1 or type(right) is not BrainvisionProjectionV1:
        raise ProjectionValidationError("projection", "must_be_brainvision_projection_v1")
    if type(relevant_fields) is not tuple or not relevant_fields:
        raise ProjectionValidationError("relevant_fields", "must_be_nonempty_tuple")
    if any(type(field) is not str or field not in _PROJECTION_VALUE_FIELDS for field in relevant_fields):
        raise ProjectionValidationError("relevant_fields", "contains_unknown_projection_field")
    return all(getattr(left, field) == getattr(right, field) for field in relevant_fields)


_PROJECTION_MANIFEST_CORE_DATA: Final[dict[str, object]] = {
    "acceptance_relevant_field_sets": {
        name: list(fields) for name, fields in ACCEPTANCE_RELEVANT_FIELD_SETS.items()
    },
    "algorithm_id": PROJECTION_ALGORITHM_ID,
    "canonical_serialization": {
        "allow_nan": False,
        "ensure_ascii": True,
        "separators": [",", ":"],
        "sort_keys": True,
    },
    "clipping_rules": {
        "current_activity_q": "none;max_abs_f_eff_is_in[0,Q]",
        "present_history_relation_raw_q": "clamp(sum_of_two_mul_q_terms,-Q,Q)",
        "retained_history_q": "none;max_abs_S_is_in[0,Q]",
        "trajectory_q": "none;S.orientation_q_is_in[-Q,Q]",
    },
    "claim_ceiling": [
        "projection_is_bounded_summary_not_raw_vhe_state",
        "current_activity_code_is_quantized_fast_trace_not_exact_current_image",
        "retained_history_code_is_magnitude_only_and_loses_coordinate_sign",
        "present_history_relation_code_is_coarse_coordinate_alignment_not_semantic_interpretation",
        "trajectory_code_is_coarse_signed_a_double_star_orientation_order_context",
        "open_event_class_is_structural_bookkeeping_not_objective_event_truth",
        "recurrence_is_register_window_relative",
        "numeric_code_zero_means_quantized_zero_not_raw_zero",
        "retained_history_code_zero_can_coexist_with_retained_magnitude_up_to_31250_q",
        "quantization_discards_sub_quantum_differences",
        "one_code_difference_can_be_quantization_boundary_without_special_semantic_significance",
        "synthetic_qualification_does_not_establish_arbitrary_camera_or_model_understanding",
        "projection_distinguishability_does_not_establish_downstream_model_usefulness",
    ],
    "canonical_projection_field_specification": [
        "schema_id",
        "projection_id",
        "operator_id",
        "current_activity_code",
        "retained_history_code",
        "present_history_relation_code",
        "trajectory_code",
        "open_event_class",
        "recurrence_code",
    ],
    "field_specs": {
        "current_activity_code": {
            "classification": "quantized_unsigned_integer",
            "domain": [0, PROJECTION_STEPS],
            "source": "max(abs(f_eff_1_q),abs(f_eff_2_q));f_eff=pure_as_of_evolved_F",
        },
        "open_event_class": {
            "classification": "structural_phase_2_token_or_null",
            "source": "R.open_semantic_event_class",
        },
        "present_history_relation_code": {
            "classification": "quantized_signed_integer",
            "domain": [-PROJECTION_STEPS, PROJECTION_STEPS],
            "source": "signed_code(clamp(mul_q(f_eff_1_q,S.luminance_q)+mul_q(f_eff_2_q,S.contrast_q),-Q,Q))",
        },
        "recurrence_code": {
            "classification": "categorical_integer",
            "domain": [0, 2],
            "source": "0=no_open;1=open_count_eq_1;2=open_count_ge_2",
        },
        "retained_history_code": {
            "classification": "quantized_unsigned_integer",
            "domain": [0, PROJECTION_STEPS],
            "source": "max(abs(S.luminance_q),abs(S.contrast_q),abs(S.orientation_q))",
        },
        "trajectory_code": {
            "classification": "quantized_signed_integer",
            "domain": [-PROJECTION_STEPS, PROJECTION_STEPS],
            "source": "signed_code(S.orientation_q)",
        },
    },
    "fixture_expectations": {
        "order": {
            "o1_trajectory_code": 5,
            "o2_trajectory_code": -5,
            "trajectory_separation": 10,
        },
        "present_history_relation": {
            "aligned": {"code": 8, "raw_relation_q": 500_000},
            "no_current": {"code": 0, "raw_relation_q": 0},
            "opposed": {"code": -3, "raw_relation_q": -187_500},
            "orthogonal": {"code": 0, "raw_relation_q": 0},
        },
        "retained": {
            "h0": {"current_activity_code": 0, "retained_history_code": 0},
            "h1": {"current_activity_code": 0, "retained_history_code": 8},
            "minimum_separation": 2,
            "separation": 8,
        },
        "semantic_recurrence": {
            "first": {
                "open_event_class": "detector:scene_change",
                "recurrence_code": 1,
            },
            "fresh": {"open_event_class": None, "recurrence_code": 0},
            "initial_state": "fresh/reset neutral VHE",
            "new": {"open_event_class": "detector:motion", "recurrence_code": 1},
            "repeat": {
                "open_event_class": "detector:scene_change",
                "recurrence_code": 2,
            },
            "transitions": "d0-only semantic observations",
            "under_that_fixture": "W=0;F/S unchanged",
        },
    },
    "operator_id": OPERATOR_ID,
    "pure_read": {
        "as_of": "evolve_vhe_state_as_of",
        "input": "committed VheState + elapsed_active_time_ns",
        "mutates_clock": False,
        "mutates_committed_vhe": False,
        "persistence_side_effect": False,
        "recursive_state": "none",
    },
    "projection_schema_id": PROJECTION_SCHEMA_ID,
    "quantization": {
        "half_quantum_q": PROJECTION_HALF_QUANTUM_Q,
        "q": Q,
        "quantum_q": PROJECTION_QUANTUM_Q,
        "rounding_algorithm_id": RNE_ALGORITHM_ID,
        "rounding": "phase_4_signed_round_half_even",
        "signed": "RNE(PROJECTION_STEPS*q/Q),q_in[-Q,Q],output_in[-16,16]",
        "steps": PROJECTION_STEPS,
        "unsigned": "RNE(PROJECTION_STEPS*q/Q),q_in[0,Q],output_in[0,16]",
        "zero_bins": {"signed": [-31_250, 31_250], "unsigned": [0, 31_250]},
    },
    "role_bindings": {name: list(fields) for name, fields in ROLE_BINDINGS.items()},
    "within_projection_quantum": "exact_equality_of_every_canonical_encoded_value_in_named_relevant_field_set",
}

PROJECTION_MANIFEST_CORE_CANONICAL_BYTES: Final = _canonical_json_bytes(
    _PROJECTION_MANIFEST_CORE_DATA
)
PROJECTION_MANIFEST_CORE_SHA256: Final = sha256(
    PROJECTION_MANIFEST_CORE_CANONICAL_BYTES
).hexdigest()
PROJECTION_ID: Final = PROJECTION_ID_PREFIX + PROJECTION_MANIFEST_CORE_SHA256


def projection_manifest_core() -> dict[str, object]:
    """Return a fresh decoded object view of the frozen manifest core bytes."""
    return json.loads(PROJECTION_MANIFEST_CORE_CANONICAL_BYTES.decode("ascii"))


def projection_manifest() -> dict[str, object]:
    """Return a fresh full manifest view; canonical core bytes remain authoritative."""
    manifest = projection_manifest_core()
    manifest["projection_id"] = PROJECTION_ID
    return manifest


__all__ = (
    "ACCEPTANCE_RELEVANT_FIELD_SETS",
    "BrainvisionProjectionV1",
    "CURRENT_ACTIVITY_ROLE",
    "OPEN_EVENT_ROLE",
    "OPERATOR_ID",
    "PRESENT_HISTORY_RELATION_ROLE",
    "PROJECTION_ALGORITHM_ID",
    "PROJECTION_HALF_QUANTUM_Q",
    "PROJECTION_ID",
    "PROJECTION_MANIFEST_CORE_CANONICAL_BYTES",
    "PROJECTION_MANIFEST_CORE_SHA256",
    "PROJECTION_QUANTUM_Q",
    "PROJECTION_SCHEMA_ID",
    "PROJECTION_STEPS",
    "ProjectionValidationError",
    "RECURRENCE_ROLE",
    "RETAINED_HISTORY_ROLE",
    "ROLE_BINDINGS",
    "TRAJECTORY_ROLE",
    "project_vhe_state",
    "projection_manifest",
    "projection_manifest_core",
    "signed_code",
    "unsigned_code",
    "within_projection_quantum",
)
