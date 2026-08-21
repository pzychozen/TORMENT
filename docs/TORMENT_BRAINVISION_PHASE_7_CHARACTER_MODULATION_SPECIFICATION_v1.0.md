# TORMENT Brainvision Phase 7 Character Modulation Specification v1.0

## Status and authority

**FROZEN PRE-IMPLEMENTATION PHASE-7 SPECIFICATION**

This document freezes the Phase-7 modulation mathematics and contract. It
authorizes no Phase-8 work and does not itself constitute Phase-7 runtime
implementation. It does not reopen the frozen Phase-4 operator, does not
reopen the frozen Phase-5 projection, and does not replace the frozen Phase-6
result.

Phase 7 defines one bounded transformation around the frozen base operator. It
creates no new recursive VHE field or dimension and does not change the base
operator or projection identities.

## 1. Accepted modulation family

The only admitted Phase-7 v1.0 modulation axis is:

~~~text
CONTEXT_INTEGRATION
~~~

It changes how strongly a relevant firsthand visual observation is integrated
into persistent Brainvision context, and correspondingly how strongly later
relevant observations can revise that context. The persistence law itself,
including the absence of elapsed-time decay in S, is unchanged at every
admitted profile.

This is a bounded integration/revision-strength modulation of existing
Brainvision dynamics. No other modulation family is admitted in v1.0.

## 2. Exact theta domain and mapping

~~~text
THETA_V1 = {-1, 0, +1}
theta_0  = 0
Q        = 1_000_000
~~~

The exact type rule is:

~~~text
type(theta) is int
~~~

Only the three exact integers -1, 0, and +1 are valid. Floats, continuous
values, and automatic coercion are invalid.

The effective context-integration mapping is:

~~~text
C(theta) = 500000 + 125000 * theta
~~~

| theta | C(theta) |
| ---: | ---: |
| -1 | 375000 |
| 0 | 500000 |
| +1 | 625000 |

The frozen Phase-4 constant remains:

~~~text
CONTEXT_BLEND_Q = 500000
~~~

Phase 7 does not modify that constant or the Phase-4 operator identity.

## 3. Exact insertion point and unchanged base behavior

The frozen baseline context-gain stage is:

~~~text
base_g = mul_q(W, CONTEXT_BLEND_Q)

g1 = mul_q(base_g, abs(u1))
g2 = mul_q(base_g, abs(u2))
g3 = mul_q(base_g, abs(c))

target = (u1, u2, c)
S_i' = S_i + mul_q(g_i, target_i - S_i)
~~~

For a non-neutral admitted Phase-7 profile only, the authorized substitution
is:

~~~text
base_g(theta) = mul_q(W, C(theta))
~~~

followed by the same frozen gain equations, target, and S update above. The
authorized substitution applies to both integration and later revision through
the existing gain pathway.

Phase 7 must not modify descriptor normalization, W, c_raw, the c clamp, the
target, Fast Trace overwrite or free evolution, semantic-register update or
capacity, FAST_HORIZON_NS, projection equations, quantization, or Phase-5 role
bindings.

## 4. Neutral direct-dispatch invariant

For theta == theta_0, an implementation must dispatch directly to the existing
frozen Phase-4 baseline update path. It must not run a new generalized Phase-7
update merely because C(0) == CONTEXT_BLEND_Q.

The required structural invariant is:

~~~text
theta_0
-> exact frozen Phase-4 baseline path
-> BIT_IDENTICAL baseline behavior
~~~

This applies to every baseline-observable/state surface, including VheState,
FastTrace, PersistentContext, SemanticRegister, VheUpdateResult, write_gate_q,
clamped_orientation_q, event_active_time_ns, canonical persisted recursive
state, and baseline validation/rejection behavior.

Phase-7 mapping/profile data is configuration-owned. It must not be inserted
into recursive VHE state merely to implement this modulation.

## 5. Ownership, provenance, and continuation

Theta is per-agent Brainvision configuration. It may come only from the
authoritative Brainvision configuration/profile selected for that agent.

v1a has no automatic derivation from CharacterSeed, CharacterState, MemoryGraph,
memory, CognitiveCore, native kernel state, SRG, Hivermind, model output, prompt
content, user language, or semantic event class. There is no process-wide
Phase-7 modulation flag.

While recursive VHE state is allocated or preserved, theta is
continuation-immutable:

~~~text
existing F/S/R generated under profile A
MUST NOT
continue under profile B
~~~

A change of theta requires a fresh VHE recursive-state boundary. This
specification does not choose the later configuration or lifecycle transaction
that creates that boundary.

Resume or reload of an active or suspended continuation must validate the
required Phase-7 mapping/profile identity alongside every other
continuation-relevant identity. An incompatible modulation identity is a hard
continuation failure.

## 6. Layered identity model

The frozen base identities remain:

~~~text
BASE_OPERATOR_ID =
bvheop1_c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb

BASE_PROJECTION_ID =
bvproj1_c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f
~~~

Phase 7 defines:

~~~text
MODULATION_SCHEMA_ID = brainvision.character_modulation.v1
MODULATION_MAPPING_ID_PREFIX = bvmodmap1_
MODULATION_PROFILE_SCHEMA_ID = brainvision.character_modulation.profile.v1
MODULATION_PROFILE_ID_PREFIX = bvmodprof1_
~~~

The complete effective Brainvision identity after Phase 7 is conceptually:

~~~text
(
    BASE_OPERATOR_ID,
    BASE_PROJECTION_ID,
    MODULATION_MAPPING_ID,
    MODULATION_PROFILE_ID,
)
~~~

BASE_OPERATOR_ID continues to identify the frozen Phase-4 A** base operator.
BASE_PROJECTION_ID continues to identify the frozen Phase-5
projection/quantizer. Neither is a per-profile identity.

### 6.1 Canonical mapping core

The Phase-7 mapping core is the following exact JSON data value. Its
authoritative bytes are its canonical ASCII JSON serialization using:

~~~text
sort_keys=True
separators=(",", ":")
ensure_ascii=True
allow_nan=False
~~~

Arrays retain the order shown. The derived hash is not included in this core.

~~~json
{
  "algorithm_id": "brainvision.context_integration.fixed3.v1",
  "axis": "CONTEXT_INTEGRATION",
  "base_operator_context_blend_q": 500000,
  "base_operator_id": "bvheop1_c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb",
  "base_projection_id": "bvproj1_c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f",
  "boundedness": {
    "admitted_max_c_q": 625000,
    "admitted_min_c_q": 375000,
    "headroom_to_q_q": 375000,
    "sufficient_bound": "C(theta)_less_than_or_equal_to_Q_preserves_S_cube_under_frozen_integer_RNE_arithmetic"
  },
  "c_theta": {
    "effective_blend_q_by_theta": {
      "-1": 375000,
      "0": 500000,
      "+1": 625000
    },
    "expression": "C(theta)=500000+125000*theta"
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
    "no_v1b_integration_correctness"
  ],
  "continuation_profile_immutability": {
    "active_or_suspended_continuation": "requires_matching_mapping_and_profile_identities",
    "incompatible_profile": "hard_continuation_failure",
    "resume_reload": "validates_mapping_profile_identity",
    "rule": "existing_F_S_R_may_not_continue_across_profiles"
  },
  "effective_identity_components": [
    "base_operator_id",
    "base_projection_id",
    "modulation_mapping_id",
    "modulation_profile_id"
  ],
  "exact_theta_rule": {
    "allowed_values": [
      -1,
      0,
      1
    ],
    "automatic_coercion": false,
    "floats_valid": false,
    "python_type": "int",
    "python_type_exact": true
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
    "role_bindings"
  ],
  "insertion_point": {
    "base_gain": "mul_q(W,C(theta))",
    "coordinate_gains": [
      "g1=mul_q(base_g,abs(u1))",
      "g2=mul_q(base_g,abs(u2))",
      "g3=mul_q(base_g,abs(c))"
    ],
    "s_update": "S_i_prime_equals_S_i_plus_mul_q(g_i,target_i_minus_S_i)",
    "target": "target=(u1,u2,c)"
  },
  "mapping_version": "v1",
  "minimum_effect": {
    "acceptance_margin_above_minimum_codes": 0,
    "baseline_theta": 0,
    "field": "retained_history_code",
    "fixture_direction": [
      -1,
      0,
      1
    ],
    "minimum_absolute_codes": 2,
    "predicted_delta_codes_by_theta": {
      "-1": -2,
      "+1": 2
    }
  },
  "neutral_direct_dispatch": {
    "required": "theta_zero_direct_frozen_phase_4_path_bit_identical_baseline",
    "theta_0": 0
  },
  "phase_4_internal_margins_q": {
    "order_orientation": 500000,
    "retained_history": 500000,
    "scope": "baseline_operator_constants_not_universal_phase_7_cross_profile_thresholds"
  },
  "product_horizon": {
    "active_visual_seconds_after_dA_onset": 300,
    "domain_wide_h0_retained_history_code": 0,
    "domain_wide_h1_retained_history_code_by_theta": {
      "-1": 6,
      "0": 8,
      "+1": 10
    },
    "margin_codes": 4,
    "minimum_h0_h1_separation_codes": 6,
    "persistence_basis": "S_no_elapsed_time_decay_post_event_d0_W_zero_no_S_revision_on_fixture",
    "required_minimum_separation_codes": 2
  },
  "q": 1000000,
  "qualification_fixture": {
    "fixture_id": "brainvision.phase7.h1.context-integration.300s.v1",
    "history": "t=0:d0;t=1:dA;t=2:d0;t=301:pure_projection_read",
    "same_across_theta": [
      "firsthand_history",
      "current_observation",
      "active_visual_time",
      "descriptor_schema",
      "VHE_dimensions",
      "projection"
    ]
  },
  "qualification_predictions": {
    "h1_current_activity_code": 0,
    "h1_persistent_context_by_theta": {
      "-1": [
        375000,
        0,
        0
      ],
      "0": [
        500000,
        0,
        0
      ],
      "+1": [
        625000,
        0,
        0
      ]
    },
    "h1_retained_history_code_by_theta": {
      "-1": 6,
      "0": 8,
      "+1": 10
    },
    "order_orientation_q_by_theta": {
      "-1": {
        "O1": 240000,
        "O2": -240000
      },
      "0": {
        "O1": 320000,
        "O2": -320000
      },
      "+1": {
        "O1": 400000,
        "O2": -400000
      }
    },
    "order_trajectory_code_by_theta": {
      "-1": {
        "O1": 4,
        "O2": -4
      },
      "0": {
        "O1": 5,
        "O2": -5
      },
      "+1": {
        "O1": 6,
        "O2": -6
      }
    }
  },
  "schema_id": "brainvision.character_modulation.v1",
  "state_ownership": "per_agent_configuration_only_not_recursive_VHE_state_no_process_wide_flag",
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
      "semantic_event_class"
    ]
  }
}
~~~

The canonical mapping core SHA-256 and derived mapping identity are:

~~~text
MODULATION_MAPPING_CORE_SHA256 =
f8b41a1987437410613157ae403d10ac12fbce3b34cc760f0cc8376193206aeb

MODULATION_MAPPING_ID =
bvmodmap1_f8b41a1987437410613157ae403d10ac12fbce3b34cc760f0cc8376193206aeb
~~~

### 6.2 Canonical profile identities

For each admitted profile, the canonical profile core is formed from this
exact template:

~~~json
{
  "mapping_id": "<MODULATION_MAPPING_ID>",
  "schema_id": "brainvision.character_modulation.profile.v1",
  "theta": "<the exact admitted integer>"
}
~~~

The same canonical ASCII JSON rules apply. The literal mapping identity replaces
<MODULATION_MAPPING_ID> and theta is an exact JSON integer, not a string. The
derived profile hash is not included in its own core.

| theta | MODULATION_PROFILE_ID |
| ---: | --- |
| -1 | bvmodprof1_95cf73f228a5c02a16e13b90cf17aa46d31bbc312643f7dbf374d33816d9ad49 |
| 0 | bvmodprof1_9f65a350c2526bc63733e9267d7846ce4eace56a6c4ec3261bfc748a18287abc |
| +1 | bvmodprof1_ceeb161b2dcb510601d85fc7b5a64eb023827bb044220b046b2c61b98be422f5 |

## 7. Projection provenance boundary

operator_id inside brainvision.projection.v1 continues to identify the frozen
Phase-4 base A** operator. The Phase-5 projection payload does not indicate
whether a non-neutral Phase-7 mapping was in effect.

Complete effective-dynamics provenance for a non-neutral profile therefore
requires the authoritative Phase-7 modulation mapping/profile identity
associated with Brainvision configuration. A standalone v1a Phase-5 projection
payload is not a complete provenance record for non-neutral Phase-7
modulation. This is a claim ceiling, not a Phase-5 defect. The Phase-5 DTO is
unchanged.

## 8. Primary qualification fixture and analytic predictions

The preregistered Phase-7 primary fixture is the existing fresh-state H1
history:

~~~text
t=0   d0
t=1   dA
t=2   d0
t=301 pure projection read
~~~

The pure read occurs exactly 300 active visual seconds after dA onset. The
firsthand history, current observation, active visual time, descriptor schema,
VHE dimensions, and projection are the same for all three profiles. Only theta
differs.

At dA from fresh H1 state:

~~~text
u = (Q, 0)
W = Q
c = 0

base_g(theta) = C(theta)
g1 = C(theta)

S.luminance_q'
= 0 + mul_q(C(theta), Q)
= C(theta)
~~~

Thus:

| theta | H1 S after dA | H1 retained-history code at 300 seconds |
| ---: | --- | ---: |
| -1 | (375000, 0, 0) | 6 |
| 0 | (500000, 0, 0) | 8 |
| +1 | (625000, 0, 0) | 10 |

The following d0 has u = (0, 0) and W = 0, so it does not revise S on this
fixture. S has no elapsed-time decay. The table therefore remains the
prediction at the 300-second read. current_activity_code = 0 for every
admitted profile at that read.

The directional prediction:

~~~text
6 < 8 < 10
~~~

is fixture-scoped. CONTEXT_INTEGRATION does not imply monotonic retained
projection over arbitrary legal visual histories.

## 9. Phase-7 acceptance and domain-wide horizon proof

The Phase-7 primary acceptance criterion is:

~~~text
abs(
    retained_history_code(theta_non_neutral)
    - retained_history_code(theta_0)
) >= 2
~~~

on the H1 fixture and in the preregistered direction. The exact effects are:

~~~text
theta = -1: 6 - 8 = -2
theta = +1: 10 - 8 = +2
~~~

~~~text
required minimum effect = 2 codes
predicted effect        = exactly 2 codes
acceptance margin above the Phase-7 minimum = 0 codes
~~~

The zero margin is accepted because all three values are exact integer
projection lattice points:

~~~text
375000 = 6 * 62500
500000 = 8 * 62500
625000 = 10 * 62500
~~~

No half-quantum tie or floating-point tolerance is involved. This criterion
has no headroom above its required minimum.

For the same H0 fixture, retained_history_code = 0 at every admitted theta.
The H1 codes are 6, 8, and 10; therefore the minimum H0/H1 retained separation
across the complete THETA_V1 domain is six codes.

~~~text
domain-wide minimum H0/H1 separation = 6 codes
frozen product-horizon minimum       = 2 codes
domain-wide horizon margin           = 4 codes
~~~

This is a domain-wide analytic result for the admitted finite domain because S
has no elapsed-time decay and the post-event d0 does not revise S on this
fixture.

## 10. Boundedness and relevant-observation scope

For legal input:

~~~text
0 <= W <= Q
0 <= abs(u_i) <= Q
0 <= abs(c) <= Q
0 <= C(theta) <= 625000 < Q
~~~

Therefore:

~~~text
base_g(theta) <= C(theta)
g_i <= base_g(theta) <= C(theta) < Q
~~~

The S update remains a rounded convex update between bounded prior state and
bounded target. The stronger sufficient bound:

~~~text
C(theta) <= Q
~~~

preserves the S cube under the frozen exact integer/RNE arithmetic. The
admitted maximum of 625000 has 375000 q headroom to that mathematical upper
bound. This specification does not claim that C(theta) > Q is safe.

An observation is relevant to a particular persistent-context coordinate only
when the frozen Phase-4 gain pathway yields a nonzero/effective gain for that
coordinate. A zero descriptor coordinate has zero direct gain for its matching
S coordinate. This definition is entirely mechanical and does not add a new
semantic interpretation.

## 11. Phase-4 internal margin scope

The frozen Phase-4 constants:

~~~text
RETAINED_HISTORY_INTERNAL_MARGIN_Q = 500000
ORDER_ORIENTATION_INTERNAL_MARGIN_Q = 500000
~~~

remain baseline operator-qualification constants. They are not universal
Phase-7 cross-profile acceptance thresholds. Phase-7 cross-domain retention is
governed by the explicit Phase-0 product-horizon requirement through the
frozen Phase-5/6 representation.

## 12. Mandatory order-sensitivity regression

For O1 = d0,dA,dB,d0 and O2 = d0,dB,dA,d0, the mandatory domain-wide
regression predictions are:

| theta | O1 S.orientation_q | O2 S.orientation_q | O1/O2 trajectory_code |
| ---: | ---: | ---: | --- |
| -1 | +240000 | -240000 | +4 / -4 |
| 0 | +320000 | -320000 | +5 / -5 |
| +1 | +400000 | -400000 | +6 / -6 |

Every admitted profile must preserve:

~~~text
O1 current_activity_code == O2 current_activity_code
O1 trajectory_code > 0
O2 trajectory_code < 0
O1 trajectory_code != O2 trajectory_code
~~~

This order regression is mandatory qualification, but it is not the primary
modulation-effect criterion.

## 13. No new state or architectural leakage

Phase 7 adds no new recursive field, VHE dimension, semantic content in W or
S, memory input, kernel input, CognitiveCore input, SRG input, Hivermind input,
CharacterSeed derivation, hidden recursive modulation accumulator, process-wide
theta, projection quantizer modification, Phase-5 role, S elapsed-time decay,
or FAST_HORIZON_NS modification.

This specification authorizes no Phase-8 configuration implementation,
Phase-9 persistence implementation, Fabric lifecycle implementation, direct
visual ingress implementation, sink/integration work, or consumer/model work.

TEMPORAL_INTERACTION_SENSITIVITY was a rejected/not-required fallback design
candidate. It is not part of the Phase-7 v1.0 admitted domain.

## 14. Claim ceiling and implementation boundary

Phase 7 establishes only the frozen bounded modulation mechanism and its
preregistered/domain-wide mathematical qualifications. It does not establish:

- global monotonicity in theta over arbitrary histories;
- modulation of memory duration;
- emotion;
- attention;
- semantic importance;
- arbitrary camera understanding;
- downstream LLM usefulness;
- physical-world visual accuracy;
- new frame-rate invariance;
- Phase-8 configuration correctness;
- Phase-9 persistence correctness;
- Fabric lifecycle correctness; or
- v1b integration correctness.

This document is a specification, not a Phase-7 result. It does not claim that
production Phase-7 code exists, has passed, or has been administered against a
frozen Phase-7 qualification suite. The analytic values in this document are
frozen predictions and proofs only.
