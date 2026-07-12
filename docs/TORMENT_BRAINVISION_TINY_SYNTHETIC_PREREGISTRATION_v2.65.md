# TORMENT Brainvision Tiny Synthetic Preregistration v2.65

## 1. Scope

**DOCS-ONLY PREREGISTRATION.** It fixes the conditions of a tiny synthetic test **before any data exists**. It contains
**no** code, **no** tests, **no** implementation, **no** fixture data, **no** arrays or images, **no** generated samples,
and **no** real clips. It opens **no** screen, runtime, memory, integration, classifier, or neural path, and makes **no**
vision claim.

```text
NO IMPLEMENTATION IS AUTHORIZED.
NO DATA EXISTS.
NO RESULTS EXIST.
NO BRAINVISION-STYLE READING MAY BE RUN UNLESS CHEAP BASELINES FAIL FIRST -- and "fail" is defined here, in advance,
  and cannot be redefined later.
```

Brainvision remains **offline / quarantined** under `research/brainvision/` + `tests/research/`, HELD per v0.6.

**Why the numbers below are fixed here rather than "chosen sensibly later."** Every threshold in a test like this is
arbitrary. That is not the problem. The problem is *choosing* it after seeing results, which converts an arbitrary number
into a favourable one. **Fixing an arbitrary number in advance is the entire mechanism of preregistration**, and the
numbers below are offered in exactly that spirit: conservative, unremarkable, and **binding**.

```text
flat_field_validated = False    role_validated = False    schema_validated = False
entanglement_resolved = False   by_residual_isolated = False
generic_chroma_proxy_ruled_out = False   null_rejected = False   artifact_ruled_out = False
proxy_ruled_out = False   confound_controlled = False
control_collapse_ruled_out = False   control_collapse_detected = False
control_collapse_reachability_validated = False
candidate_structure_validated = False   candidate_structure_survived = False
candidate_structure_detected = False
anti_inevitability_validated = False    control_honesty_validated = False
first_pass_structure_validity_claim_allowed = False   temporal_claim_allowed = False
descriptor_validity_claim_allowed = False   geometry_validity_claim_allowed = False
screen_readiness_claim_allowed = False   runtime_readiness_claim_allowed = False
memory_readiness_claim_allowed = False   integration_readiness_claim_allowed = False
vision_claim_allowed = False
verdict = HOLD
```

## 2. Target Restatement

```text
Two short artificial stream classes. Each stream shows TWO MOVING ELEMENTS on a plain background.

  CLASS ONE  -- the two elements' movements are RELATED across time.
  CLASS TWO  -- the two elements move INDEPENDENTLY.

MATCHED, as far as the tiny generator permits: palettes, brightness, shapes, per-element motion, single-frame
appearance, and frame-to-frame change amount.

The intended difference is RELATION ACROSS FRAMES, and nothing else. Whether the generator actually achieves that is an
EMPIRICAL QUESTION, not a design claim -- and Section 3 exists because it very likely does not.
```

## 3. Baseline Set — Fixed Before Data

**FIXED. No baseline may be added, removed, weakened, retuned, or reimplemented after data exists.**

```text
B1. colour / intensity baseline
B2. frame-difference baseline
B3. static single-frame descriptor baseline
B4. random / control baseline
B5. simple spectral / FFT baseline, if applicable
B6. CHEAP RELATIONAL baseline -- the simplest thing that compares how the two regions change TOGETHER, with no
    Brainvision machinery of any kind.
B7. COMBINED CHEAP BASELINE -- all of the above scalars taken together under the same fixed rule. Included to close the
    loophole where each cheap baseline is individually weak and the set is jointly sufficient.
```

**B6 is expected to be the strongest and the most likely winner.** It is the baseline whose omission would rig the
comparison, and it is named first among equals for that reason.

**Adding a baseline after seeing results is how a candidate is buried. Removing one is how a candidate survives. Neither
is available.**

### 3a. Baseline positive control — required, and the reason is not procedural

A baseline that fails tells us **nothing** unless we know it *could* have succeeded. **A weak or broken baseline is the
cheapest way in the world to manufacture a survivor**, and it is the way this test would most plausibly fool us.

```text
EASY CONTROL VARIANT: the same generator, with the relation between the two elements made BLATANT and the matching
constraints switched off.

EVERY baseline B1-B7 that is capable of expressing the relevant distinction must reach at least 0.90 test balanced
accuracy on the EASY CONTROL VARIANT.

IF A BASELINE CANNOT SOLVE THE EASY VARIANT, THAT BASELINE IS BROKEN, and its failure on the real task is
UNINFORMATIVE. The correct response is to stop this run; any repaired baseline belongs only in a later, separately
gated preregistration before new data exists -- not to count its failure as the task being hard.

B4 (random / control) is exempt: it must sit at chance on both, and if it does not, the evaluation harness is broken.
```

## 4. Evaluation Order — Locked

```text
STAGE 1.  Generate the target data. Fixed seeds. No inspection of class labels against baseline outputs.
STAGE 2.  Run the cheap baselines ONLY (B1-B7), plus the easy-control positive check (3a).
STAGE 3.  Decide whether the task is DEAD, by the rule in Section 5. The rule is applied once.
STAGE 4.  ONLY IF the cheap baselines fail under that rule, AND ONLY after separate operator approval, may a LATER,
          SEPARATELY GATED slice PROPOSE a Brainvision-style reading. That slice is not authorized here, is not owed,
          and is not scheduled.

IF ANY CHEAP BASELINE SEPARATES THE CLASSES UNDER THE PREREGISTERED RULE, THE TASK IS DEAD.
  - Do NOT run a Brainvision-style reading on a dead task. Not once. Not "just to look".
  - Do NOT retune the task, the generator, or the matching.
  - Do NOT adjust the criteria after seeing results.
A dead task is a RESULT, and it is the expected one.
```

## 5. Minimal Decision Rule

**Preregistered. Conservative. Applied once, to held-out test data only.**

```text
CHANCE = 0.50 (two balanced classes).

DEAD          -- if ANY cheap baseline (B1-B3, B5-B7) reaches test balanced accuracy >= 0.65.
                 The task is solved by a cheap baseline. Stop. No Brainvision-style reading is run.

NO CONCLUSION -- if the best cheap baseline lands in the AMBIGUITY BAND, 0.60 <= test balanced accuracy < 0.65.
                 The task neither dies nor becomes eligible. Nothing follows. Do NOT retune to push it either way.
                 This band exists specifically to prevent "it only just failed, therefore it survived."

ELIGIBLE      -- if ALL cheap baselines are < 0.60 on test, AND every baseline has passed the easy-control positive
                 check (3a).
                 "Eligible" means ONLY: eligible for a later, separately gated OPERATOR DECISION about whether a
                 Brainvision-style reading should even be proposed.
                 IT IS NOT EVIDENCE FOR BRAINVISION. It is not support, not promise, not a signal, and not a result
                 about streams. It is a task that cheap methods did not solve -- which is a fact about the task.

UNINFORMATIVE -- if any baseline fails the easy-control check. Nothing about the real task can be concluded, because we
                 do not know that the baseline could have succeeded.
                 Stop this run; do not bank the failure. Any repaired baseline belongs only in a later, separately gated
                 preregistration before new data exists.
```

**Forbidden descriptions of the ELIGIBLE outcome, in any wording:** *promising*; *survived*; *survived scientifically*;
*structure detected*; *candidate validated*; *the signal is there*; *worth pursuing because it worked*. **Eligible is an
administrative state, not a finding.**

## 6. Metrics

**The minimum required to evaluate cheap baselines, and nothing else.**

```text
SEPARATION SCORE : balanced accuracy on held-out test data. Chance = 0.50.
SAMPLES          : 200 clips per class (400 total), fixed before generation.
SEEDS            : fixed and recorded before generation; generation and evaluation both reproducible.
SPLIT            : 50 / 50 train / test by seed, fixed in advance. Each baseline reduces a clip to a small number of
                   scalars; any threshold or simple fit is chosen on TRAIN ONLY and applied unchanged to TEST.
                   Deterministic, non-learned baselines may be scored on TEST directly.
REPORTING        : all baselines reported, including the losers. Every number reported once.

NOT DEFINED HERE, AND NOT PERMITTED HERE:
  no Brainvision metric. no geometry-validity metric. no descriptor-validity metric. no memory metric.
  no screen / runtime / integration metric. no recognition rule for control-collapse.
```

## 7. Failure Outcomes — Pre-Accepted

**All legitimate. None is a failed slice. Each is accepted here, before anything is known.**

```text
- a cheap baseline wins -- INCLUDING B6, which is the expected case.
- the task is dead.
- the generator accidentally leaks the label through something nobody intended.
- the task is flawed, or measures something other than what was meant.
- no conclusion (the ambiguity band).
- this preregistration turns out to be too weak, and says so.
- implementation should not proceed at all.
```

**And the outcome that is not on the list, because it would not be an outcome:** *the candidate looked interesting, so we
adjusted the task, the matching, the baselines, or the rule.*

## 8. What This Does Not Authorize

```text
No Brainvision-style reading -- not in Stage 2, not on a dead task, not "informally", and not to look.
No implementation beyond a later, separately reviewed generator + cheap-baseline slice.
No primitive validation.        PRIMITIVE SELECTION REMAINS UNRESOLVED.
No geometry validation.         No descriptor validation.
No memory bridge validation.    MEMORY INTEGRATION IS NOT AUTHORIZED.
No stream-to-context validation.
No vision claim.
No runtime / screen / integration path.
```

**This document produces no evidence.** It fixes the conditions under which evidence could later be produced about **one
tiny artificial task**, which would remain a fact about that task and not about streams, colour, the world, or vision.

## 9. Operator Checkpoint

```text
RECOMMEND: CODEX REVIEW OF THIS PREREGISTRATION BEFORE ANY IMPLEMENTATION.

AFTER REVIEW, THE OPERATOR MAY CHOOSE:

  A. Implement ONLY the generator + cheap baselines, exactly as preregistered.
     -- A CONTAINS NO BRAINVISION-STYLE READING. None. Stage 4 is not part of A.
  B. Modify the preregistration.
  C. Pause.
  D. Abandon this target.

Undeveloped, unranked, none owed. Pause is co-equal and is a complete answer. Abandoning is not a loss.
```

## 10. Conclusion

```text
This preregistration defines only the baseline-first test conditions for the tiny synthetic target.
It produces no evidence.
It authorizes no Brainvision-style reading.
Implementation, if later approved, is limited to generator plus cheap baselines.
If a cheap baseline solves the task, the task is dead.
If cheap baselines fail, that creates only eligibility for a later operator decision, not evidence for Brainvision.
No claim lock moves.
verdict = HOLD
```

`OUTCOME_LABEL: BRAINVISION_TINY_SYNTHETIC_PREREGISTRATION_ONLY`

## 11. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_TINY_SYNTHETIC_PREREGISTRATION_v2.65.md
(new, docs-only, untracked; over the accepted v2.64 edge "53aca89 docs(research): propose tiny brainvision synthetic
target").

Verify that this preregistration:
- is docs-only: no code, no tests, no implementation, no fixture data, no arrays / images, no generated samples, no real
  clips; no screen / runtime / memory / integration path; no classifier / neural work; no vision or readiness claim; no
  §0 pointer; no tags;
- states that no implementation is authorized, no data exists, no results exist, and NO BRAINVISION-STYLE READING may be
  run unless cheap baselines fail first under a rule fixed IN ADVANCE;
- restates the v2.64 target briefly and correctly, and treats the matching as an EMPIRICAL question rather than a design
  claim;
- FIXES the baseline set before data (colour / intensity; frame-difference; static single-frame descriptor; random /
  control; simple spectral; CHEAP RELATIONAL; and a COMBINED cheap baseline closing the jointly-sufficient loophole),
  names the cheap relational baseline as the expected winner, and forbids adding, removing, weakening, retuning, or
  reimplementing any baseline after data exists;
- REQUIRES A BASELINE POSITIVE CONTROL (an easy variant with the relation made blatant and matching switched off) and
  states that a baseline failing the easy variant is BROKEN and its failure on the real task is UNINFORMATIVE -- because
  a weak baseline is the cheapest way to manufacture a survivor;
- LOCKS the evaluation order (generate; cheap baselines only; decide dead; and only then, only if baselines fail, and
  only with separate operator approval, may a later separately gated slice PROPOSE a Brainvision-style reading), and
  forbids running any Brainvision-style reading on a dead task, retuning the task, or adjusting criteria after results;
- defines a MINIMAL, CONSERVATIVE, PREREGISTERED decision rule with an explicit AMBIGUITY BAND, applied once to held-out
  test data, and defines ELIGIBLE as an ADMINISTRATIVE STATE ONLY -- not evidence, not support, not promise -- forbidding
  "promising", "survived", "structure detected", and "candidate validated";
- defines ONLY the minimum metrics (balanced accuracy; fixed sample count; fixed seeds; fixed train / test split or
  deterministic scoring; all baselines reported including losers) and NO Brainvision / geometry / descriptor / memory /
  screen / runtime metric;
- pre-accepts all failure outcomes (cheap baseline wins; task dead; generator leaks the label; task flawed; no
  conclusion; preregistration too weak; implementation should not proceed) and forbids adjusting task, matching,
  baselines, or rule because the candidate looked interesting;
- authorizes NOTHING (no Brainvision reading; no implementation beyond a later separately reviewed generator +
  cheap-baseline slice; no primitive / geometry / descriptor / memory-bridge / stream-to-context validation; no vision
  claim; no runtime / screen / integration path);
- offers exactly four operator choices, with A explicitly EXCLUDING any Brainvision-style reading, none owed, pause
  co-equal;
- states the required conclusion block verbatim and preserves all claim locks False with verdict = HOLD.

Flag any implementation, code, data, array, image, or generated sample; any Brainvision / geometry / descriptor / memory
/ runtime metric; any baseline left adjustable after data exists; any missing baseline positive control; any ordering
that would permit a Brainvision-style reading before the baselines have failed, or on a dead task; any criterion that
could be chosen or moved after results; any description of the ELIGIBLE outcome as promising, surviving, or evidential;
any outcome treated as a failure of the slice; any claim about streams, colour, or the world; any successor treated as
owed or authorized; or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

All claim locks False, and the frozen verdict **HOLD**, are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Tiny Synthetic Preregistration v2.65. Docs-only preregistration over the accepted v2.64 edge.
Contains no code, tests, implementation, fixture data, arrays, images, generated samples, or real clips; opens no screen /
runtime / memory / integration / classifier / neural path; makes no vision or readiness claim; authorizes nothing. Fixes,
BEFORE ANY DATA EXISTS: the target (two short artificial stream classes, two moving elements, related vs independent
movement across time, with palettes / brightness / shapes / per-element motion / single-frame appearance / frame-to-frame
change matched as far as the tiny generator permits — treated as an EMPIRICAL question, not a design claim); the BASELINE
SET (colour / intensity; frame-difference; static single-frame descriptor; random / control; simple spectral; CHEAP
RELATIONAL — the expected winner; and a COMBINED cheap baseline closing the jointly-sufficient loophole), which may not
be added to, removed from, weakened, retuned, or reimplemented after data exists; a REQUIRED BASELINE POSITIVE CONTROL on
an easy variant, because a baseline that fails tells us nothing unless we know it could have succeeded, and a weak
baseline is the cheapest way to manufacture a survivor; the LOCKED EVALUATION ORDER (generate → cheap baselines only →
decide dead → and only then, only on baseline failure, and only with separate operator approval, may a later separately
gated slice PROPOSE a Brainvision-style reading), with no Brainvision-style reading on a dead task, no retuning, and no
post-hoc criteria; a MINIMAL CONSERVATIVE DECISION RULE with an explicit AMBIGUITY BAND, applied once to held-out test
data, in which ELIGIBLE is an ADMINISTRATIVE STATE ONLY and explicitly NOT evidence, support, promise, survival, or
structure; and the MINIMUM METRICS ONLY (balanced accuracy; fixed samples; fixed seeds; fixed split or deterministic
scoring; all baselines reported, losers included), with no Brainvision, geometry, descriptor, memory, screen, or runtime
metric defined. Pre-accepts cheap-baseline victory, task death, label leakage, flawed task, no conclusion, an inadequate
preregistration, and not proceeding at all — and forbids adjusting task, matching, baselines, or rule because the
candidate looked interesting. Offers four operator choices (implement generator + cheap baselines exactly as
preregistered, WITH NO BRAINVISION-STYLE READING INCLUDED; modify; pause; abandon), none owed, pause co-equal. Preserves
all claim locks False and the frozen verdict HOLD; outcome label BRAINVISION_TINY_SYNTHETIC_PREREGISTRATION_ONLY; no `§0`
pointer added; no tags.*
