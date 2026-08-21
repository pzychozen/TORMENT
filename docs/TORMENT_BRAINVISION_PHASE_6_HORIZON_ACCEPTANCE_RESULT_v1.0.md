# TORMENT Brainvision Phase-6 Horizon Acceptance Result v1.0

## Status

First recorded administration: **PASS**

`BRAINVISION_PHASE6_HORIZON_ACCEPTANCE_PASS`

- Administration guard: PASS
- Primary retained-horizon acceptance: PASS
- Formal `VHE_ACCEPTANCE_FAIL`: NOT TRIGGERED
- Mandatory qualifications: PASS
- Supporting present/history relation coverage: PASS

## Preregistration and first administration

The authoritative preregistration commit was:

```text
002823929f3bd12592b165cea8e1202affffe875
```

The first recorded administration used exactly:

```text
python -m pytest tests\test_brainvision_phase6_horizon_acceptance.py -q
```

Its recorded pytest result was:

```text
.......... [100%]
10 passed in 0.25s
```

```text
PHASE6_EXIT_CODE=0
```

No test, threshold, operator, or projection change occurred between the
preregistration freeze and this first administration.

No Phase-6 rerun was performed while creating this result record.

## Repository state

Before administration:

```text
HEAD:        002823929f3bd12592b165cea8e1202affffe875
origin/main: 002823929f3bd12592b165cea8e1202affffe875
worktree:    clean
```

After administration:

```text
HEAD:        002823929f3bd12592b165cea8e1202affffe875
origin/main: 002823929f3bd12592b165cea8e1202affffe875
worktree:    clean
```

## Frozen primary retained-horizon result

At exactly 300 active visual seconds after `dA` onset:

| History | `current_activity_code` | `retained_history_code` |
| --- | ---: | ---: |
| H0 | 0 | 0 |
| H1 | 0 | 8 |

- Current-activity equality: PASS.
- Retained-history distinction: PASS.
- Retained-history separation: 8 codes.
- Minimum required retained-history separation: 2 codes.
- Margin above the minimum required separation: 6 codes.

## Frozen order result

| Order history | `current_activity_code` | `trajectory_code` |
| --- | ---: | ---: |
| O1 | 0 | +5 |
| O2 | 0 | -5 |

- Current-activity equality: PASS.
- Trajectory distinction: PASS.
- Trajectory separation: 10 codes.

All mandatory qualifications passed. Supporting present/history relation
coverage also passed.

## Claim ceiling and reproduction boundary

This pass establishes only that the frozen deterministic synthetic Brainvision
operator/projection satisfies the preregistered v1a qualification matrix at the
frozen product horizon. It does not establish arbitrary camera or semantic
visual understanding, downstream LLM usefulness, physical-world vision
accuracy, universal frame-rate invariance, Phase-7 modulation validity,
lifecycle/persistence correctness, or full Brainvision product readiness.

Later Phase-6 runs are reproduction or verification only. They do not replace
this first recorded administration result.
