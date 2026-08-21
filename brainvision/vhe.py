"""Frozen Phase-4 fixed-point Brainvision visual-history operator.

The operator is intentionally isolated from clocks, persistence, lifecycle,
ingress, projections, and all existing TORMENT runtime subsystems.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Final

from brainvision.fixtures import D0_SHA256, DA_SHA256, DB_SHA256
from brainvision.observation import (
    DESCRIPTOR_COORDINATE_ORDER,
    DESCRIPTOR_SCHEMA_ID,
    LowLevelVisualDescriptorV1,
)
from brainvision.clock import T_PRODUCT_V1_NS, VISUAL_TIME_NS_PER_SECOND


Q: Final = 1_000_000
FAST_HORIZON_NS: Final = 5_000_000_000
CONTEXT_BLEND_Q: Final = 500_000
R_CAPACITY: Final = 8
MAX_OCCURRENCE_COUNT: Final = (2**63) - 1

RETAINED_HISTORY_INTERNAL_MARGIN_Q: Final = 500_000
ORDER_ORIENTATION_INTERNAL_MARGIN_Q: Final = 500_000

OPERATOR_SCHEMA_ID: Final = "brainvision.vhe.operator.v1"
ALGORITHM_ID: Final = "fixedpoint-context-a-double-star.v1"
RNE_ALGORITHM_ID: Final = "signed-quotient-remainder-half-even.v1"
OPERATOR_ID_PREFIX: Final = "bvheop1_"

_SEMANTIC_EVENT_CLASS_PATTERN = re.compile(
    r"[a-z][a-z0-9_-]{0,31}:[a-z][a-z0-9._-]{0,63}"
)


class VheValidationError(ValueError):
    """A frozen VHE contract input or state invariant was violated."""

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
        raise VheValidationError(field, "must_be_exact_int")
    return value


def _require_nonnegative_exact_int(value: object, field: str) -> int:
    value = _require_exact_int(value, field)
    if value < 0:
        raise VheValidationError(field, "must_be_nonnegative")
    return value


def _require_range(value: object, field: str, minimum: int, maximum: int) -> int:
    value = _require_exact_int(value, field)
    if not minimum <= value <= maximum:
        raise VheValidationError(field, "out_of_range", f"expected {minimum}..{maximum}")
    return value


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return min(max(value, minimum), maximum)


def _require_semantic_event_class(value: object) -> str:
    if type(value) is not str:
        raise VheValidationError("semantic_event_class", "must_be_null_or_namespaced_token")
    if _SEMANTIC_EVENT_CLASS_PATTERN.fullmatch(value) is None:
        raise VheValidationError("semantic_event_class", "invalid_namespaced_token")
    return value


def round_half_even_division(numerator: int, positive_denominator: int) -> int:
    """Round an exact signed rational with the frozen quotient/remainder rule."""
    numerator = _require_exact_int(numerator, "numerator")
    positive_denominator = _require_exact_int(
        positive_denominator,
        "positive_denominator",
    )
    if positive_denominator <= 0:
        raise VheValidationError("positive_denominator", "must_be_positive")

    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), positive_denominator)
    if 2 * remainder > positive_denominator:
        quotient += 1
    elif 2 * remainder == positive_denominator and quotient % 2 == 1:
        quotient += 1
    return sign * quotient


def mul_q(a: int, b: int) -> int:
    """Multiply Q-scaled integers with exactly one frozen rounding operation."""
    a = _require_exact_int(a, "a")
    b = _require_exact_int(b, "b")
    return round_half_even_division(a * b, Q)


@dataclass(frozen=True, kw_only=True)
class FastTrace:
    """A bounded linear effective trace with an exact finite interaction window."""

    amplitude_1_q: int
    amplitude_2_q: int
    remaining_ns: int

    def __post_init__(self) -> None:
        _require_range(self.amplitude_1_q, "amplitude_1_q", -Q, Q)
        _require_range(self.amplitude_2_q, "amplitude_2_q", 0, Q)
        _require_range(self.remaining_ns, "remaining_ns", 0, FAST_HORIZON_NS)
        amplitudes_are_zero = self.amplitude_1_q == 0 and self.amplitude_2_q == 0
        if (self.remaining_ns == 0) != amplitudes_are_zero:
            raise VheValidationError("fast_trace", "noncanonical_zero_duration_or_amplitude")


@dataclass(frozen=True, kw_only=True)
class PersistentContext:
    """The bounded non-decaying non-semantic context state."""

    luminance_q: int
    contrast_q: int
    orientation_q: int

    def __post_init__(self) -> None:
        _require_range(self.luminance_q, "luminance_q", -Q, Q)
        _require_range(self.contrast_q, "contrast_q", -Q, Q)
        _require_range(self.orientation_q, "orientation_q", -Q, Q)


@dataclass(frozen=True, kw_only=True)
class SemanticRegisterEntry:
    """One bounded-window opaque semantic recurrence record."""

    semantic_event_class: str
    first_seen_active_time_ns: int
    last_seen_active_time_ns: int
    occurrence_count: int

    def __post_init__(self) -> None:
        _require_semantic_event_class(self.semantic_event_class)
        _require_nonnegative_exact_int(
            self.first_seen_active_time_ns,
            "first_seen_active_time_ns",
        )
        _require_nonnegative_exact_int(
            self.last_seen_active_time_ns,
            "last_seen_active_time_ns",
        )
        if self.last_seen_active_time_ns < self.first_seen_active_time_ns:
            raise VheValidationError("last_seen_active_time_ns", "before_first_seen")
        _require_range(
            self.occurrence_count,
            "occurrence_count",
            1,
            MAX_OCCURRENCE_COUNT,
        )


@dataclass(frozen=True, kw_only=True)
class SemanticRegister:
    """A fixed-capacity register with one structural open semantic token."""

    entries: tuple[SemanticRegisterEntry, ...]
    open_semantic_event_class: str | None

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple:
            raise VheValidationError("entries", "must_be_tuple")
        if len(self.entries) > R_CAPACITY:
            raise VheValidationError("entries", "capacity_exceeded")
        if any(type(entry) is not SemanticRegisterEntry for entry in self.entries):
            raise VheValidationError("entries", "must_contain_semantic_register_entries")

        tokens = tuple(entry.semantic_event_class for entry in self.entries)
        if len(set(tokens)) != len(tokens):
            raise VheValidationError("entries", "duplicate_semantic_event_class")
        if self.entries != tuple(sorted(self.entries, key=lambda entry: entry.semantic_event_class)):
            raise VheValidationError("entries", "must_be_lexicographically_sorted")

        if not self.entries:
            if self.open_semantic_event_class is not None:
                raise VheValidationError("open_semantic_event_class", "must_be_null_when_empty")
            return

        if self.open_semantic_event_class is None:
            raise VheValidationError("open_semantic_event_class", "must_exist_when_nonempty")
        _require_semantic_event_class(self.open_semantic_event_class)
        if self.open_semantic_event_class not in tokens:
            raise VheValidationError("open_semantic_event_class", "must_reference_entry")


@dataclass(frozen=True, kw_only=True)
class VheState:
    """The complete recursive VHE state; it intentionally stores no time epoch."""

    fast_trace: FastTrace
    persistent_context: PersistentContext
    semantic_register: SemanticRegister

    def __post_init__(self) -> None:
        if type(self.fast_trace) is not FastTrace:
            raise VheValidationError("fast_trace", "must_be_fast_trace")
        if type(self.persistent_context) is not PersistentContext:
            raise VheValidationError("persistent_context", "must_be_persistent_context")
        if type(self.semantic_register) is not SemanticRegister:
            raise VheValidationError("semantic_register", "must_be_semantic_register")


@dataclass(frozen=True, kw_only=True)
class VheUpdateResult:
    """Recursive successor state plus non-persisted update diagnostics."""

    state: VheState
    write_gate_q: int
    clamped_orientation_q: int
    event_active_time_ns: int

    def __post_init__(self) -> None:
        if type(self.state) is not VheState:
            raise VheValidationError("state", "must_be_vhe_state")
        _require_range(self.write_gate_q, "write_gate_q", 0, Q)
        _require_range(self.clamped_orientation_q, "clamped_orientation_q", -Q, Q)
        _require_nonnegative_exact_int(self.event_active_time_ns, "event_active_time_ns")


def fresh_vhe_state() -> VheState:
    """Return the exact fresh/reset VHE state."""
    return VheState(
        fast_trace=FastTrace(amplitude_1_q=0, amplitude_2_q=0, remaining_ns=0),
        persistent_context=PersistentContext(luminance_q=0, contrast_q=0, orientation_q=0),
        semantic_register=SemanticRegister(entries=(), open_semantic_event_class=None),
    )


def normalize_descriptor(descriptor: LowLevelVisualDescriptorV1) -> tuple[int, int]:
    """Map the frozen descriptor coordinates into the frozen A** input domain."""
    if type(descriptor) is not LowLevelVisualDescriptorV1:
        raise VheValidationError("descriptor", "must_be_low_level_visual_descriptor_v1")
    return (
        _clamp(4 * (descriptor.mean_luminance_q - 500_000), -Q, Q),
        _clamp(4 * descriptor.mean_adjacent_luminance_difference_q, 0, Q),
    )


def evolve_fast_trace(fast_trace: FastTrace, elapsed_active_time_ns: int) -> FastTrace:
    """Pure exact free evolution of the finite fast-trace duration."""
    if type(fast_trace) is not FastTrace:
        raise VheValidationError("fast_trace", "must_be_fast_trace")
    elapsed_active_time_ns = _require_nonnegative_exact_int(
        elapsed_active_time_ns,
        "elapsed_active_time_ns",
    )
    remaining_ns = max(0, fast_trace.remaining_ns - elapsed_active_time_ns)
    if remaining_ns == 0:
        return FastTrace(amplitude_1_q=0, amplitude_2_q=0, remaining_ns=0)
    return FastTrace(
        amplitude_1_q=fast_trace.amplitude_1_q,
        amplitude_2_q=fast_trace.amplitude_2_q,
        remaining_ns=remaining_ns,
    )


def effective_fast_trace(fast_trace: FastTrace) -> tuple[int, int]:
    """Return the frozen linearly decayed effective trace after evolution."""
    if type(fast_trace) is not FastTrace:
        raise VheValidationError("fast_trace", "must_be_fast_trace")
    return (
        round_half_even_division(
            fast_trace.amplitude_1_q * fast_trace.remaining_ns,
            FAST_HORIZON_NS,
        ),
        round_half_even_division(
            fast_trace.amplitude_2_q * fast_trace.remaining_ns,
            FAST_HORIZON_NS,
        ),
    )


def evolve_vhe_state_as_of(
    state: VheState,
    elapsed_active_time_ns: int,
) -> VheState:
    """Pure as-of evolution: only F changes on the returned immutable state."""
    if type(state) is not VheState:
        raise VheValidationError("state", "must_be_vhe_state")
    return VheState(
        fast_trace=evolve_fast_trace(state.fast_trace, elapsed_active_time_ns),
        persistent_context=state.persistent_context,
        semantic_register=state.semantic_register,
    )


def _context_coordinate_update(current_q: int, target_q: int, gain_q: int) -> int:
    """Apply the fixed-point convex context update without clipping."""
    updated_q = current_q + mul_q(gain_q, target_q - current_q)
    if not -Q <= updated_q <= Q:
        raise VheValidationError("persistent_context", "cube_invariance_violation")
    return updated_q


def _overwrite_fast_trace(u1_q: int, u2_q: int) -> FastTrace:
    if (u1_q, u2_q) == (0, 0):
        return FastTrace(amplitude_1_q=0, amplitude_2_q=0, remaining_ns=0)
    return FastTrace(
        amplitude_1_q=u1_q,
        amplitude_2_q=u2_q,
        remaining_ns=FAST_HORIZON_NS,
    )


def _update_semantic_register(
    semantic_register: SemanticRegister,
    semantic_event_class: str | None,
    event_active_time_ns: int,
) -> SemanticRegister:
    if semantic_event_class is None:
        return semantic_register
    semantic_event_class = _require_semantic_event_class(semantic_event_class)
    event_active_time_ns = _require_nonnegative_exact_int(
        event_active_time_ns,
        "event_active_time_ns",
    )

    entries = list(semantic_register.entries)
    for index, entry in enumerate(entries):
        if entry.semantic_event_class == semantic_event_class:
            entries[index] = SemanticRegisterEntry(
                semantic_event_class=entry.semantic_event_class,
                first_seen_active_time_ns=entry.first_seen_active_time_ns,
                last_seen_active_time_ns=event_active_time_ns,
                occurrence_count=min(MAX_OCCURRENCE_COUNT, entry.occurrence_count + 1),
            )
            return SemanticRegister(
                entries=tuple(sorted(entries, key=lambda item: item.semantic_event_class)),
                open_semantic_event_class=semantic_event_class,
            )

    if len(entries) == R_CAPACITY:
        closed_entries = [
            entry
            for entry in entries
            if entry.semantic_event_class != semantic_register.open_semantic_event_class
        ]
        if not closed_entries:
            raise VheValidationError("semantic_register", "no_closed_entry_for_eviction")
        evicted_entry = min(
            closed_entries,
            key=lambda entry: (
                entry.last_seen_active_time_ns,
                entry.first_seen_active_time_ns,
                entry.semantic_event_class,
            ),
        )
        entries.remove(evicted_entry)

    entries.append(
        SemanticRegisterEntry(
            semantic_event_class=semantic_event_class,
            first_seen_active_time_ns=event_active_time_ns,
            last_seen_active_time_ns=event_active_time_ns,
            occurrence_count=1,
        )
    )
    return SemanticRegister(
        entries=tuple(sorted(entries, key=lambda item: item.semantic_event_class)),
        open_semantic_event_class=semantic_event_class,
    )


def _update_vhe_state(
    *,
    state: VheState,
    descriptor: LowLevelVisualDescriptorV1,
    semantic_event_class: str | None,
    prior_committed_active_time_ns: int,
    elapsed_active_time_ns: int,
    orientation_override_q: int | None = None,
) -> VheUpdateResult:
    if type(state) is not VheState:
        raise VheValidationError("state", "must_be_vhe_state")
    prior_committed_active_time_ns = _require_nonnegative_exact_int(
        prior_committed_active_time_ns,
        "prior_committed_active_time_ns",
    )
    elapsed_active_time_ns = _require_nonnegative_exact_int(
        elapsed_active_time_ns,
        "elapsed_active_time_ns",
    )
    if semantic_event_class is not None:
        _require_semantic_event_class(semantic_event_class)
    event_active_time_ns = prior_committed_active_time_ns + elapsed_active_time_ns

    evolved_fast_trace = evolve_fast_trace(state.fast_trace, elapsed_active_time_ns)
    f_eff_1_q, f_eff_2_q = effective_fast_trace(evolved_fast_trace)
    u1_q, u2_q = normalize_descriptor(descriptor)
    write_gate_q = min(Q, abs(u1_q) + abs(u2_q))
    c_raw_q = mul_q(f_eff_1_q, u2_q) - mul_q(f_eff_2_q, u1_q)
    clamped_orientation_q = _clamp(c_raw_q, -Q, Q)
    if orientation_override_q is not None:
        clamped_orientation_q = _require_range(
            orientation_override_q,
            "orientation_override_q",
            -Q,
            Q,
        )

    base_gain_q = mul_q(write_gate_q, CONTEXT_BLEND_Q)
    gain_1_q = mul_q(base_gain_q, abs(u1_q))
    gain_2_q = mul_q(base_gain_q, abs(u2_q))
    gain_3_q = mul_q(base_gain_q, abs(clamped_orientation_q))
    context = state.persistent_context
    next_context = PersistentContext(
        luminance_q=_context_coordinate_update(context.luminance_q, u1_q, gain_1_q),
        contrast_q=_context_coordinate_update(context.contrast_q, u2_q, gain_2_q),
        orientation_q=_context_coordinate_update(
            context.orientation_q,
            clamped_orientation_q,
            gain_3_q,
        ),
    )
    next_fast_trace = _overwrite_fast_trace(u1_q, u2_q)
    next_register = _update_semantic_register(
        state.semantic_register,
        semantic_event_class,
        event_active_time_ns,
    )
    return VheUpdateResult(
        state=VheState(
            fast_trace=next_fast_trace,
            persistent_context=next_context,
            semantic_register=next_register,
        ),
        write_gate_q=write_gate_q,
        clamped_orientation_q=clamped_orientation_q,
        event_active_time_ns=event_active_time_ns,
    )


def update_vhe_state(
    *,
    state: VheState,
    descriptor: LowLevelVisualDescriptorV1,
    semantic_event_class: str | None,
    prior_committed_active_time_ns: int,
    elapsed_active_time_ns: int,
) -> VheUpdateResult:
    """Apply the frozen A** observation update in its exact contract order."""
    return _update_vhe_state(
        state=state,
        descriptor=descriptor,
        semantic_event_class=semantic_event_class,
        prior_committed_active_time_ns=prior_committed_active_time_ns,
        elapsed_active_time_ns=elapsed_active_time_ns,
    )


def _update_vhe_state_with_c_zero_for_test(
    *,
    state: VheState,
    descriptor: LowLevelVisualDescriptorV1,
    semantic_event_class: str | None,
    prior_committed_active_time_ns: int,
    elapsed_active_time_ns: int,
) -> VheUpdateResult:
    """Test-only reference evaluation with c replaced by zero after c derivation."""
    return _update_vhe_state(
        state=state,
        descriptor=descriptor,
        semantic_event_class=semantic_event_class,
        prior_committed_active_time_ns=prior_committed_active_time_ns,
        elapsed_active_time_ns=elapsed_active_time_ns,
        orientation_override_q=0,
    )


_OPERATOR_MANIFEST_CORE_DATA: Final[dict[str, object]] = {
    "algorithm_id": ALGORITHM_ID,
    "c_clamp_q": [-Q, Q],
    "claim_ceiling": [
        "w_has_no_claimed_nonzero_dead_zone_width",
        "fixed_point_rounding_can_zero_small_writes",
        "s_has_no_elapsed_time_decay",
        "retained_300_seconds_is_minimum_survival_not_half_life",
        "subsequent_relevant_observations_can_revise_context",
        "zero_descriptor_coordinate_has_zero_direct_context_gain",
        "orientation_memory_is_limited_by_fast_horizon",
        "c_clamping_has_real_saturation_region",
        "recurrence_is_register_window_relative",
        "synthetic_qualification_does_not_prove_arbitrary_camera_behavior",
        "phase_5_must_bind_order_role_to_orientation_q",
        "phase_5_quantization_requires_independent_freeze",
        "phase_4_margins_do_not_prove_projection_distinguishability",
    ],
    "context_blend_q": CONTEXT_BLEND_Q,
    "descriptor_coordinate_order": list(DESCRIPTOR_COORDINATE_ORDER),
    "descriptor_schema_id": DESCRIPTOR_SCHEMA_ID,
    "equations": {
        "c": {
            "clamp": "c=clamp(c_raw,-Q,Q)",
            "raw": "c_raw=mul_q(f_eff_1,u2)-mul_q(f_eff_2,u1)",
        },
        "f": {
            "effective_trace": "f_eff_i=RNE(amplitude_i*remaining/FAST_HORIZON_NS)",
            "expiry_canonicalization": "remaining==0->F=(0,0,0)",
            "free_evolution": "remaining'=max(0,remaining-delta)",
            "observation_overwrite": "u==(0,0)->F=(0,0,0);else->F=(u1,u2,FAST_HORIZON_NS)",
        },
        "pure_as_of": "elapsed_time_evolves_F_only;S_and_R_unchanged",
        "rne_mul_q": "mul_q(a,b)=exactly_one_RNE(exact_a_times_b_over_Q)",
        "s": {
            "base_gain": "base_g=mul_q(W,CONTEXT_BLEND_Q)",
            "coordinate_gains": [
                "g1=mul_q(base_g,abs(u1))",
                "g2=mul_q(base_g,abs(u2))",
                "g3=mul_q(base_g,abs(c))",
            ],
            "no_post_update_clipping": True,
            "target": "target=(u1,u2,c)",
            "update": "S_i'=S_i+mul_q(g_i,target_i-S_i)",
        },
        "time": "event_active_time_ns=prior_committed_active_time_ns+elapsed_active_time_ns",
        "w": "W=min(Q,abs(u1)+abs(u2))",
    },
    "fixture_sha256": {"d0": D0_SHA256, "dA": DA_SHA256, "dB": DB_SHA256},
    "fast_horizon_ns": FAST_HORIZON_NS,
    "input_normalization": {
        "u1": "clamp(4*(mean_luminance_q-500000),-Q,Q)",
        "u2": "clamp(4*mean_adjacent_luminance_difference_q,0,Q)",
    },
    "internal_margins_q": {
        "order_orientation": ORDER_ORIENTATION_INTERNAL_MARGIN_Q,
        "retained_history": RETAINED_HISTORY_INTERNAL_MARGIN_Q,
    },
    "numerical_representation": "bounded_exact_python_integers",
    "operator_schema_id": OPERATOR_SCHEMA_ID,
    "phase_0_authority": "docs/TORMENT_BRAINVISION_PHASE_0_PRODUCTION_SPECIFICATION_v1.0.md",
    "phase_3_time": {
        "product_horizon_ns": T_PRODUCT_V1_NS,
        "visual_time_ns_per_second": VISUAL_TIME_NS_PER_SECOND,
    },
    "q": Q,
    "r_capacity": R_CAPACITY,
    "r_rules": {
        "entry_order": "lexicographically_ascending_semantic_event_class",
        "existing_token": "saturating_increment_update_last_seen_set_open",
        "eviction": "closed_min(last_seen_active_time_ns,first_seen_active_time_ns,semantic_event_class)",
        "new_token": "insert_count_one_set_open",
        "null_semantic_event_class": "unchanged",
        "open": "most_recent_admitted_non_null_semantic_token",
        "open_token_never_evictable": True,
        "recurrence": "register_window_relative",
    },
    "rne": {
        "algorithm_id": RNE_ALGORITHM_ID,
        "rule": "signed_quotient_remainder_half_even",
    },
    "state_schema": {
        "fast_trace": {
            "amplitude_1_q": [-Q, Q],
            "amplitude_2_q": [0, Q],
            "remaining_ns": [0, FAST_HORIZON_NS],
        },
        "persistent_context": {
            "contrast_q": [-Q, Q],
            "luminance_q": [-Q, Q],
            "orientation_q": [-Q, Q],
        },
        "semantic_register": {
            "capacity": R_CAPACITY,
            "max_occurrence_count": MAX_OCCURRENCE_COUNT,
        },
    },
    "update_order": [
        "evolve_f",
        "canonicalize_expired_f",
        "derive_f_eff",
        "derive_u",
        "derive_w",
        "derive_c_raw_and_clamped_c",
        "derive_gains",
        "update_s",
        "overwrite_or_canonicalize_f",
        "update_r",
    ],
    "w": "min(Q,abs(u1)+abs(u2))",
}

OPERATOR_MANIFEST_CORE_CANONICAL_BYTES: Final = json.dumps(
    _OPERATOR_MANIFEST_CORE_DATA,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=True,
    allow_nan=False,
).encode("ascii")
OPERATOR_MANIFEST_CORE_SHA256: Final = sha256(OPERATOR_MANIFEST_CORE_CANONICAL_BYTES).hexdigest()
OPERATOR_ID: Final = OPERATOR_ID_PREFIX + OPERATOR_MANIFEST_CORE_SHA256


def operator_manifest_core() -> dict[str, object]:
    """Return a fresh decoded object view of the frozen core bytes."""
    return json.loads(OPERATOR_MANIFEST_CORE_CANONICAL_BYTES.decode("ascii"))


def operator_manifest() -> dict[str, object]:
    """Return a fresh full manifest view; canonical bytes remain authoritative."""
    manifest = operator_manifest_core()
    manifest["operator_id"] = OPERATOR_ID
    return manifest


__all__ = (
    "ALGORITHM_ID",
    "CONTEXT_BLEND_Q",
    "FAST_HORIZON_NS",
    "MAX_OCCURRENCE_COUNT",
    "OPERATOR_ID",
    "OPERATOR_MANIFEST_CORE_CANONICAL_BYTES",
    "OPERATOR_MANIFEST_CORE_SHA256",
    "OPERATOR_SCHEMA_ID",
    "ORDER_ORIENTATION_INTERNAL_MARGIN_Q",
    "PersistentContext",
    "Q",
    "R_CAPACITY",
    "RETAINED_HISTORY_INTERNAL_MARGIN_Q",
    "RNE_ALGORITHM_ID",
    "SemanticRegister",
    "SemanticRegisterEntry",
    "VheState",
    "VheUpdateResult",
    "VheValidationError",
    "FastTrace",
    "effective_fast_trace",
    "evolve_fast_trace",
    "evolve_vhe_state_as_of",
    "fresh_vhe_state",
    "mul_q",
    "normalize_descriptor",
    "operator_manifest",
    "operator_manifest_core",
    "round_half_even_division",
    "update_vhe_state",
)
