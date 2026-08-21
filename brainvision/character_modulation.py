"""Frozen Phase-7 CONTEXT_INTEGRATION character-modulation mechanism.

This isolated engine module owns no configuration, persistence, lifecycle,
ingress, sinks, or consumer integration.  The neutral profile dispatches
directly to the frozen Phase-4 update path.  Non-neutral profiles replace only
the authorized persistent-context gain stage while retaining every other
Phase-4 result.
"""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Final

from brainvision.projection import PROJECTION_ID
from brainvision.vhe import (
    CONTEXT_BLEND_Q,
    OPERATOR_ID,
    PersistentContext,
    VheState,
    VheUpdateResult,
    mul_q,
    normalize_descriptor,
    update_vhe_state,
)


MODULATION_SCHEMA_ID: Final = "brainvision.character_modulation.v1"
MODULATION_PROFILE_SCHEMA_ID: Final = "brainvision.character_modulation.profile.v1"
MODULATION_MAPPING_ID_PREFIX: Final = "bvmodmap1_"
MODULATION_PROFILE_ID_PREFIX: Final = "bvmodprof1_"

THETA_V1: Final[tuple[int, int, int]] = (-1, 0, 1)
THETA_0: Final = 0
Q: Final = 1_000_000

BASE_OPERATOR_ID: Final = OPERATOR_ID
BASE_PROJECTION_ID: Final = PROJECTION_ID


class CharacterModulationValidationError(ValueError):
    """A Phase-7 theta/profile contract input was invalid."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def validate_theta(theta: object) -> int:
    """Validate the exact finite Phase-7 theta domain without coercion."""
    if type(theta) is not int:
        raise CharacterModulationValidationError("theta", "must_be_exact_int")
    if theta not in THETA_V1:
        raise CharacterModulationValidationError("theta", "outside_theta_v1")
    return theta


def effective_context_blend_q(theta: int) -> int:
    """Return the exact authorized effective context blend for theta."""
    theta = validate_theta(theta)
    return 500_000 + 125_000 * theta


def _build_modulation_mapping_core_data() -> dict[str, object]:
    """Build a fresh copy of the exact Phase-7 mapping-identity preimage."""
    return {
        "algorithm_id": "brainvision.context_integration.fixed3.v1",
        "axis": "CONTEXT_INTEGRATION",
        "base_operator_context_blend_q": CONTEXT_BLEND_Q,
        "base_operator_id": BASE_OPERATOR_ID,
        "base_projection_id": BASE_PROJECTION_ID,
        "boundedness": {
            "admitted_max_c_q": 625_000,
            "admitted_min_c_q": 375_000,
            "headroom_to_q_q": 375_000,
            "sufficient_bound": (
                "C(theta)_less_than_or_equal_to_Q_preserves_S_cube_under_"
                "frozen_integer_RNE_arithmetic"
            ),
        },
        "c_theta": {
            "effective_blend_q_by_theta": {"-1": 375_000, "0": 500_000, "+1": 625_000},
            "expression": "C(theta)=500000+125000*theta",
        },
        "claim_ceiling": [
            "fixture_direction_not_global_monotonicity",
            "no_memory_duration_modulation",
            "no_emotion_or_attention_interpretation",
            "no_arbitrary_camera_or_semantic_understanding",
            "no_downstream_LLM_usefulness",
            "no_physical_world_visual_accuracy",
            "no_new_frame_rate_invariance",
            "no_phase_8_configuration_correctness",
            "no_phase_9_persistence_correctness",
            "no_fabric_lifecycle_correctness",
            "no_v1b_integration_correctness",
        ],
        "continuation_profile_immutability": {
            "active_or_suspended_continuation": (
                "requires_matching_mapping_and_profile_identities"
            ),
            "incompatible_profile": "hard_continuation_failure",
            "resume_reload": "validates_mapping_profile_identity",
            "rule": "existing_F_S_R_may_not_continue_across_profiles",
        },
        "effective_identity_components": [
            "base_operator_id",
            "base_projection_id",
            "modulation_mapping_id",
            "modulation_profile_id",
        ],
        "exact_theta_rule": {
            "allowed_values": [-1, 0, 1],
            "automatic_coercion": False,
            "floats_valid": False,
            "python_type": "int",
            "python_type_exact": True,
        },
        "frozen_components_unchanged": [
            "descriptor_normalization",
            "W",
            "c_raw",
            "c_clamp",
            "target",
            "F_overwrite",
            "F_free_evolution",
            "R_update",
            "R_capacity",
            "FAST_HORIZON_NS",
            "projection_equations",
            "quantization",
            "role_bindings",
        ],
        "insertion_point": {
            "base_gain": "mul_q(W,C(theta))",
            "coordinate_gains": [
                "g1=mul_q(base_g,abs(u1))",
                "g2=mul_q(base_g,abs(u2))",
                "g3=mul_q(base_g,abs(c))",
            ],
            "s_update": "S_i_prime_equals_S_i_plus_mul_q(g_i,target_i_minus_S_i)",
            "target": "target=(u1,u2,c)",
        },
        "mapping_version": "v1",
        "minimum_effect": {
            "acceptance_margin_above_minimum_codes": 0,
            "baseline_theta": THETA_0,
            "field": "retained_history_code",
            "fixture_direction": [-1, 0, 1],
            "minimum_absolute_codes": 2,
            "predicted_delta_codes_by_theta": {"-1": -2, "+1": 2},
        },
        "neutral_direct_dispatch": {
            "required": "theta_zero_direct_frozen_phase_4_path_bit_identical_baseline",
            "theta_0": THETA_0,
        },
        "phase_4_internal_margins_q": {
            "order_orientation": 500_000,
            "retained_history": 500_000,
            "scope": "baseline_operator_constants_not_universal_phase_7_cross_profile_thresholds",
        },
        "product_horizon": {
            "active_visual_seconds_after_dA_onset": 300,
            "domain_wide_h0_retained_history_code": 0,
            "domain_wide_h1_retained_history_code_by_theta": {
                "-1": 6,
                "0": 8,
                "+1": 10,
            },
            "margin_codes": 4,
            "minimum_h0_h1_separation_codes": 6,
            "persistence_basis": "S_no_elapsed_time_decay_post_event_d0_W_zero_no_S_revision_on_fixture",
            "required_minimum_separation_codes": 2,
        },
        "q": Q,
        "qualification_fixture": {
            "fixture_id": "brainvision.phase7.h1.context-integration.300s.v1",
            "history": "t=0:d0;t=1:dA;t=2:d0;t=301:pure_projection_read",
            "same_across_theta": [
                "firsthand_history",
                "current_observation",
                "active_visual_time",
                "descriptor_schema",
                "VHE_dimensions",
                "projection",
            ],
        },
        "qualification_predictions": {
            "h1_current_activity_code": 0,
            "h1_persistent_context_by_theta": {
                "-1": [375_000, 0, 0],
                "0": [500_000, 0, 0],
                "+1": [625_000, 0, 0],
            },
            "h1_retained_history_code_by_theta": {"-1": 6, "0": 8, "+1": 10},
            "order_orientation_q_by_theta": {
                "-1": {"O1": 240_000, "O2": -240_000},
                "0": {"O1": 320_000, "O2": -320_000},
                "+1": {"O1": 400_000, "O2": -400_000},
            },
            "order_trajectory_code_by_theta": {
                "-1": {"O1": 4, "O2": -4},
                "0": {"O1": 5, "O2": -5},
                "+1": {"O1": 6, "O2": -6},
            },
        },
        "schema_id": MODULATION_SCHEMA_ID,
        "state_ownership": (
            "per_agent_configuration_only_not_recursive_VHE_state_no_process_wide_flag"
        ),
        "theta_provenance": {
            "allowed": "authoritative_per_agent_Brainvision_configuration_profile_only",
            "automatic_derivation_excluded": [
                "CharacterSeed",
                "CharacterState",
                "MemoryGraph",
                "memory",
                "CognitiveCore",
                "native_kernel",
                "SRG",
                "Hivermind",
                "model_output",
                "prompt_content",
                "user_language",
                "semantic_event_class",
            ],
        },
    }


MODULATION_MAPPING_CORE_CANONICAL_BYTES: Final = _canonical_json_bytes(
    _build_modulation_mapping_core_data()
)
MODULATION_MAPPING_CORE_SHA256: Final = sha256(
    MODULATION_MAPPING_CORE_CANONICAL_BYTES
).hexdigest()
MODULATION_MAPPING_ID: Final = MODULATION_MAPPING_ID_PREFIX + MODULATION_MAPPING_CORE_SHA256


def modulation_mapping_core() -> dict[str, object]:
    """Return a fresh decoded view of the frozen mapping-identity core."""
    return json.loads(MODULATION_MAPPING_CORE_CANONICAL_BYTES.decode("ascii"))


def modulation_mapping_manifest() -> dict[str, object]:
    """Return a fresh mapping manifest view; canonical bytes remain authoritative."""
    manifest = modulation_mapping_core()
    manifest["modulation_mapping_id"] = MODULATION_MAPPING_ID
    return manifest


def modulation_profile_core(theta: int) -> dict[str, object]:
    """Return a fresh canonical profile-core value for one admitted theta."""
    theta = validate_theta(theta)
    return {
        "mapping_id": MODULATION_MAPPING_ID,
        "schema_id": MODULATION_PROFILE_SCHEMA_ID,
        "theta": theta,
    }


def modulation_profile_canonical_bytes(theta: int) -> bytes:
    """Return the authoritative canonical bytes for one admitted profile."""
    return _canonical_json_bytes(modulation_profile_core(theta))


def modulation_profile_id(theta: int) -> str:
    """Derive the deterministic frozen profile identity for one admitted theta."""
    return MODULATION_PROFILE_ID_PREFIX + sha256(
        modulation_profile_canonical_bytes(theta)
    ).hexdigest()


def modulation_profile_manifest(theta: int) -> dict[str, object]:
    """Return a fresh profile manifest view; canonical bytes remain authoritative."""
    manifest = modulation_profile_core(theta)
    manifest["modulation_profile_id"] = modulation_profile_id(theta)
    return manifest


def update_vhe_state_with_character_modulation(
    *,
    state: VheState,
    descriptor: object,
    semantic_event_class: str | None,
    prior_committed_active_time_ns: int,
    elapsed_active_time_ns: int,
    theta: int,
) -> VheUpdateResult:
    """Apply the Phase-7 profile while preserving all baseline-owned outputs."""
    theta = validate_theta(theta)
    if theta == THETA_0:
        return update_vhe_state(
            state=state,
            descriptor=descriptor,
            semantic_event_class=semantic_event_class,
            prior_committed_active_time_ns=prior_committed_active_time_ns,
            elapsed_active_time_ns=elapsed_active_time_ns,
        )

    baseline_result = update_vhe_state(
        state=state,
        descriptor=descriptor,
        semantic_event_class=semantic_event_class,
        prior_committed_active_time_ns=prior_committed_active_time_ns,
        elapsed_active_time_ns=elapsed_active_time_ns,
    )
    u1_q, u2_q = normalize_descriptor(descriptor)
    base_gain_q = mul_q(
        baseline_result.write_gate_q,
        effective_context_blend_q(theta),
    )
    gain_1_q = mul_q(base_gain_q, abs(u1_q))
    gain_2_q = mul_q(base_gain_q, abs(u2_q))
    gain_3_q = mul_q(base_gain_q, abs(baseline_result.clamped_orientation_q))
    context = state.persistent_context
    next_context = PersistentContext(
        luminance_q=context.luminance_q
        + mul_q(gain_1_q, u1_q - context.luminance_q),
        contrast_q=context.contrast_q
        + mul_q(gain_2_q, u2_q - context.contrast_q),
        orientation_q=context.orientation_q
        + mul_q(
            gain_3_q,
            baseline_result.clamped_orientation_q - context.orientation_q,
        ),
    )
    return VheUpdateResult(
        state=VheState(
            fast_trace=baseline_result.state.fast_trace,
            persistent_context=next_context,
            semantic_register=baseline_result.state.semantic_register,
        ),
        write_gate_q=baseline_result.write_gate_q,
        clamped_orientation_q=baseline_result.clamped_orientation_q,
        event_active_time_ns=baseline_result.event_active_time_ns,
    )


__all__ = (
    "BASE_OPERATOR_ID",
    "BASE_PROJECTION_ID",
    "CharacterModulationValidationError",
    "MODULATION_MAPPING_CORE_CANONICAL_BYTES",
    "MODULATION_MAPPING_CORE_SHA256",
    "MODULATION_MAPPING_ID",
    "MODULATION_PROFILE_ID_PREFIX",
    "MODULATION_PROFILE_SCHEMA_ID",
    "MODULATION_SCHEMA_ID",
    "Q",
    "THETA_0",
    "THETA_V1",
    "effective_context_blend_q",
    "modulation_mapping_core",
    "modulation_mapping_manifest",
    "modulation_profile_canonical_bytes",
    "modulation_profile_core",
    "modulation_profile_id",
    "modulation_profile_manifest",
    "update_vhe_state_with_character_modulation",
    "validate_theta",
)
