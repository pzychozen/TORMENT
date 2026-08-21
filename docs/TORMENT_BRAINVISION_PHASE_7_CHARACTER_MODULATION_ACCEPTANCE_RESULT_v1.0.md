# TORMENT Brainvision Phase 7 Character Modulation Acceptance Result v1.0

## Status

**FIRST RECORDED FORMAL ADMINISTRATION: PASS**

Formal verdict:

~~~text
BRAINVISION_PHASE7_CHARACTER_MODULATION_ACCEPTANCE_PASS
~~~

This document records the already-completed first formal Phase-7
character-modulation acceptance administration. It does not modify the
implementation, specification, preregistration, manifest, formal instrument,
or any Phase-4 through Phase-6 authority.

## Authority chain

~~~text
Phase-7 specification freeze:
048a54140007e57df6a2f87da00d48ad6c7a3b5c

Phase-7 implementation:
4ae28a5930868dbe79b9d1c1ff0539fd9c2d712a

Phase-7 acceptance preregistration:
fb54a9a06050b11a16235447f87e796cc2856345
~~~

The frozen formal artifacts are:

~~~text
tests/fixtures/brainvision_phase7_character_modulation_acceptance_manifest.json
tests/test_brainvision_phase7_character_modulation_acceptance.py
docs/TORMENT_BRAINVISION_PHASE_7_CHARACTER_MODULATION_ACCEPTANCE_PREREGISTRATION_v1.0.md
~~~

No test, specification, manifest, or implementation modification occurred
between the preregistration freeze and this administration. No
post-administration change occurred before this result recording.

## First formal administration evidence

Preflight authority:

~~~text
HEAD:
fb54a9a06050b11a16235447f87e796cc2856345

origin/main:
fb54a9a06050b11a16235447f87e796cc2856345

worktree:
clean; no Git status entries

formal administration run count before execution:
0
~~~

Exact formal command executed:

~~~text
python -m pytest tests\test_brainvision_phase7_character_modulation_acceptance.py -q
~~~

Exact pytest outcome:

~~~text
.......                                                                  [100%]
============================== warnings summary ===============================
..\..\..\..\Users\Notandi\miniconda3\envs\torment\Lib\site-packages\_pytest\cacheprovider.py:475
  C:\Users\Notandi\miniconda3\envs\torment\Lib\site-packages\_pytest\cacheprovider.py:475: PytestCacheWarning: could not create cache path C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\.pytest_cache\v\cache\nodeids: [WinError 5] Access is denied: 'C:\\TORMENT\\TORMENT_repo\\TORMENT-fabric_v2\\torment_fabric\\.pytest_cache\\v\\cache'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
7 passed, 1 warning in 0.13s
~~~

Recorded exit code:

~~~text
PHASE7_EXIT_CODE=0
~~~

Post-run authority:

~~~text
HEAD:
fb54a9a06050b11a16235447f87e796cc2856345

origin/main:
fb54a9a06050b11a16235447f87e796cc2856345

worktree:
clean; no Git changes

formal administration run count:
1

confirmatory run:
NOT PERFORMED

rerun:
NOT PERFORMED

files modified after preregistration and before/during administration:
0
~~~

Pytest could not create or update its local `.pytest_cache` nodeids cache
because Windows returned Access Denied. The formal test execution itself
completed, all seven formal tests passed, exit code was zero, and no Git
worktree change resulted. This is recorded as a non-failing administration
warning.

## Formal qualification result summary

The frozen acceptance instrument passed all seven formal tests. The following
are formal conformance results for the preregistered matrix, not newly measured
exploratory discoveries.

### Primary same-experience character effect

At exactly 300 active visual seconds after dA onset:

| theta | PersistentContext | `current_activity_code` | `retained_history_code` |
| ---: | --- | ---: | ---: |
| -1 | (375000, 0, 0) | 0 | 6 |
| 0 | (500000, 0, 0) | 0 | 8 |
| +1 | (625000, 0, 0) | 0 | 10 |

The frozen direction, `6 < 8 < 10`, conformed. The non-neutral effects from
theta zero were -2 and +2 codes. The required minimum was 2 codes; the
observed formal effect was exactly 2 codes, with a frozen acceptance margin of
0 codes.

### Domain-wide product horizon

At the 300-active-second read:

| theta | H0 `retained_history_code` | H1 `retained_history_code` | H0/H1 separation |
| ---: | ---: | ---: | ---: |
| -1 | 0 | 6 | 6 |
| 0 | 0 | 8 | 8 |
| +1 | 0 | 10 | 10 |

Current activity was 0 for every H0/H1 profile. The domain minimum separation
was 6 codes, against the required product-horizon minimum of 2 codes, for a
domain-wide margin of 4 codes.

### Order regression

| theta | O1 orientation / trajectory | O2 orientation / trajectory |
| ---: | --- | --- |
| -1 | +240000 / +4 | -240000 / -4 |
| 0 | +320000 / +5 | -320000 / -5 |
| +1 | +400000 / +6 | -400000 / -6 |

The O1/O2 current-activity equality, opposite trajectory signs, and trajectory
distinction requirements passed across the full admitted theta domain.

### Neutral baseline

Theta zero direct baseline dispatch passed. Preregistered complete
`VheUpdateResult` equality against the direct Phase-4 baseline passed for the
retained-context, orientation/order, and semantic-register histories.

### Non-modulated dynamics isolation

The following exact Phase-4-owned outputs passed their required equality
checks: `FastTrace`, `SemanticRegister`, `write_gate_q`,
`clamped_orientation_q`, and `event_active_time_ns`. `PersistentContext` was
the only authorized modulated surface.

### Semantic dynamical isolation

Changing the semantic token could alter R while leaving F, S, W, and c
unchanged; this preregistered isolation requirement passed.

### Identity and schema guard

The frozen base operator identity, base projection identity, modulation mapping
identity, all three profile identities, theta domain, Phase-2 fixture hashes,
and unchanged Phase-5 projection payload all passed their required guards.

## Claim ceiling

This PASS establishes only that the frozen Phase-7 `CONTEXT_INTEGRATION`
implementation conforms to the preregistered deterministic v1a
character-modulation acceptance matrix across the complete admitted `THETA_V1`
domain.

It establishes neutral bit-identical baseline behavior, preregistered
same-experience character modulation, preservation of the 300-active-second
product horizon across admitted profiles, preservation of order-sensitive
trajectory behavior, isolation of non-modulated Phase-4 dynamics,
semantic/dynamical isolation, and frozen identity/schema conformance.

It does not establish global monotonicity across arbitrary visual histories,
memory-duration modulation, emotion, attention, semantic importance,
arbitrary camera understanding, physical-world vision accuracy, downstream LLM
usefulness, Phase-8 configuration correctness, Phase-9 persistence correctness,
Fabric lifecycle correctness, or v1b integration correctness.

## Reproduction boundary

This first formal administration is the authoritative Phase-7 acceptance
administration. Any later execution of:

~~~text
python -m pytest tests\test_brainvision_phase7_character_modulation_acceptance.py -q
~~~

is reproduction or regression only. A later run cannot replace this first
recorded result.

No Phase-7 formal test, confirmatory test, or other pytest command was run
while creating this result record.
