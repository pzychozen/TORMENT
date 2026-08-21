# TORMENT Brainvision Phase 7 Character Modulation Acceptance Preregistration v1.0

## Status and boundary

**FROZEN FORMAL QUALIFICATION PREREGISTRATION**

This document and its paired machine-readable matrix freeze the first formal
Phase-7 character-modulation qualification instrument. They do not modify the
Phase-7 implementation, do not reopen Phase 4, Phase 5, or Phase 6, and
authorize no Phase-8 work.

No formal Phase-7 administration has occurred. The frozen command below has
not yet been executed as the formal Phase-7 administration. Development tests
executed before this preregistration are implementation-development evidence
only; they are not this administration.

## Frozen administration identity

~~~text
manifest schema:
brainvision.phase7.character_modulation_acceptance_manifest.v1

Phase-7 specification:
docs/TORMENT_BRAINVISION_PHASE_7_CHARACTER_MODULATION_SPECIFICATION_v1.0.md

implementation commit:
4ae28a5930868dbe79b9d1c1ff0539fd9c2d712a

primary failure verdict:
BRAINVISION_PHASE7_CHARACTER_MODULATION_ACCEPTANCE_FAIL

later pass verdict, if earned:
BRAINVISION_PHASE7_CHARACTER_MODULATION_ACCEPTANCE_PASS

administration command:
python -m pytest tests\test_brainvision_phase7_character_modulation_acceptance.py -q
~~~

The authoritative formal matrix is:

~~~text
tests/fixtures/brainvision_phase7_character_modulation_acceptance_manifest.json
~~~

It binds the specification path, implementation commit, base operator and
projection identities, Phase-7 mapping and profile identities, theta domain,
300-second product horizon, Phase-2 fixture hashes, relevant projection
fields, histories, expected values, thresholds, and failure authority. It
contains no administration outcome.

## Identity and schema guard

Before every primary assertion, the formal instrument requires:

~~~text
BASE_OPERATOR_ID =
bvheop1_c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb

BASE_PROJECTION_ID =
bvproj1_c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f

MODULATION_MAPPING_CORE_SHA256 =
f8b41a1987437410613157ae403d10ac12fbce3b34cc760f0cc8376193206aeb

MODULATION_MAPPING_ID =
bvmodmap1_f8b41a1987437410613157ae403d10ac12fbce3b34cc760f0cc8376193206aeb

theta=-1:
bvmodprof1_95cf73f228a5c02a16e13b90cf17aa46d31bbc312643f7dbf374d33816d9ad49

theta=0:
bvmodprof1_9f65a350c2526bc63733e9267d7846ce4eace56a6c4ec3261bfc748a18287abc

theta=+1:
bvmodprof1_ceeb161b2dcb510601d85fc7b5a64eb023827bb044220b046b2c61b98be422f5
~~~

The guard also binds THETA_V1 = [-1, 0, +1], theta_0 = 0,
T_PRODUCT_V1_NS = 300000000000, the three frozen Phase-2 descriptor hashes,
and the exact Phase-5 projection payload field set. The projection payload
must contain neither theta nor a modulation-profile field.

## Qualification matrix

### Neutral baseline

Theta zero must dispatch directly to frozen Phase-4 update_vhe_state. A
structural sentinel guard freezes this requirement. The retained-context,
orientation/order, and semantic-register histories each require complete
VheUpdateResult equality against direct Phase-4 execution at every observation
step, including VheState, FastTrace, PersistentContext, SemanticRegister,
write_gate_q, clamped_orientation_q, and event_active_time_ns.

### Primary same-experience character effect

The sole primary history is:

~~~text
t=0   d0
t=1   dA
t=2   d0
t=301 pure projection read
~~~

At the 300-active-second read:

| theta | PersistentContext S | current_activity_code | retained_history_code |
| ---: | --- | ---: | ---: |
| -1 | (375000, 0, 0) | 0 | 6 |
| 0 | (500000, 0, 0) | 0 | 8 |
| +1 | (625000, 0, 0) | 0 | 10 |

The frozen direction is 6 < 8 < 10. The non-neutral deltas from theta zero
are -2 and +2. The minimum absolute effect is 2 codes and the acceptance
margin is 0 codes.

### Full-domain product horizon

At the same read:

| theta | H0 retained-history code | H1 retained-history code | H0/H1 separation |
| ---: | ---: | ---: | ---: |
| -1 | 0 | 6 | 6 |
| 0 | 0 | 8 | 8 |
| +1 | 0 | 10 | 10 |

Current activity is zero for H0 and H1 for every admitted theta. The frozen
domain minimum separation is 6 codes, against the frozen required product
horizon minimum of 2 codes, for a domain-wide margin of 4 codes.

### Order regression

The order histories are O1 = d0,dA,dB,d0 and O2 = d0,dB,dA,d0.

| theta | O1 orientation / trajectory | O2 orientation / trajectory |
| ---: | --- | --- |
| -1 | +240000 / +4 | -240000 / -4 |
| 0 | +320000 / +5 | -320000 / -5 |
| +1 | +400000 / +6 | -400000 / -6 |

For every admitted theta, O1/O2 current activity must agree; O1 trajectory
must be positive; O2 trajectory must be negative; and the two trajectory codes
must differ.

### Non-modulated dynamics and semantic isolation

For the preregistered representative non-neutral history, FastTrace,
SemanticRegister, write_gate_q, clamped_orientation_q, and event_active_time_ns
must exactly match direct Phase-4 execution. PersistentContext is the only
authorized differing output.

For each admitted theta, changing only a valid semantic token may alter the
semantic register but must leave FastTrace, PersistentContext, write_gate_q,
and clamped_orientation_q exactly unchanged.

## Administration boundary

No threshold, history, expected value, authority, or failure verdict may be
altered after the first formal administration. This preregistration does not
record an administration outcome and does not freeze a Phase-7 qualification
result.
