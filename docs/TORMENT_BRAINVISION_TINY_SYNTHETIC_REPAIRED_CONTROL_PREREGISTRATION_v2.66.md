# TORMENT Brainvision Tiny Synthetic — Repaired-Control Preregistration v2.66

## 1. Scope

**DOCS-ONLY PREREGISTRATION.** It repairs the **positive-control design** that v2.65 found to be too weak, **before any
new data exists**. It contains **no** code, **no** tests, **no** implementation, **no** fixture data, **no** arrays or
images, **no** generated samples, and **no** real clips.

```text
NO IMPLEMENTATION IS AUTHORIZED.
NO DATA EXISTS FOR THE REPAIRED CONTROL.
NO BRAINVISION-STYLE READING IS AUTHORIZED -- and none was implemented or run in v2.65.
```

Brainvision remains **offline / quarantined** under `research/brainvision/` + `tests/research/`, HELD per v0.6.

**Standing framing, carried in force:**

```text
- The v2.65 run was UNINFORMATIVE. That is NOT a failure, and it is NOT support.
- NO Brainvision-style reading was implemented or run at any point.
- The v2.65 near-chance target-task cheap-baseline scores CANNOT BE BANKED. They mean nothing, because the harness was
  not shown to be capable of detecting what it was there to detect.
- The positive-control DESIGN was too weak.
- Any repaired run requires a NEW PREREGISTRATION BEFORE NEW DATA. This is that preregistration.
```

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

## 2. What v2.65 Showed

```text
- B5 (simple spectral) did not reach the preregistered easy-control bar.
- THEREFORE the run was UNINFORMATIVE by the preregistered rule. The rule was applied unchanged, and the bar was not
  relaxed to accommodate the number we happened to see.
- The LOCKSTEP easy control did not exercise the capability the target actually demands: keeping the two elements
  DISTINCT while comparing their trajectories. In lockstep, a relational baseline can see the relation without ever
  telling the two elements apart. On the target, where the relation is a constant angular offset, it cannot.
- The cheap relational baseline PASSED that control and sat at chance on the target -- which means a baseline could
  pass this positive control and still be incapable on the task it exists to police.
- THIS IS A HARNESS / CONTROL DEFECT. IT IS NOT A BRAINVISION RESULT, and it is not a result about streams.
```

**Consequence, stated once and plainly:** the v2.65 run could not have been informative even if B5 had cleared its bar.
Nothing about the target task was learned, and nothing about it may be carried forward.

## 3. Repaired Positive-Control Requirement

**The repaired easy control must exercise the same capability the target demands.** In plain language:

```text
R1. The two elements must remain DISTINCT throughout. The control may not collapse them into a single effective object.
R2. The relation must NOT be lockstep, and must not be any relation that survives confusing the two elements for each
    other. A relation that reads the same after the two elements are swapped tests nothing about telling them apart.
R3. The relation must be BLATANT -- easy to see -- while still requiring the two separately moving elements to be
    TRACKED AND COMPARED as two.
R4. The cheap relational baseline must have to compare the two element trajectories DISTINCTLY in order to succeed.
    If it can succeed without doing so, the control is void.
```

**And the rule that generalizes the v2.65 defect, which is the substantive content of this preregistration:**

> **MATCHING MAY BE SWITCHED OFF ONLY ON AXES IRRELEVANT TO THE CAPABILITY BEING CERTIFIED.**
>
> An easy control is allowed to be easy — that is its purpose — but **only along dimensions the target does not test**.
> Brightness, speed, and background contrast may be made obvious, so that the non-relational baselines have something to
> find. **The relational geometry and the distinctness of the two elements may not be eased**, because those are exactly
> what the control exists to certify.
>
> **A control that makes the tested capability easier certifies nothing.** That is what happened in v2.65, and it is the
> failure this document exists to prevent from recurring one level down.

**No data, no arrays, and no generation parameters are fixed here.** They belong to the implementation slice, and they
are not authorized.

## 4. Baseline Set

**B1–B7 remain the baseline set. B6 (cheap relational) remains the expected strongest and most likely winner. B7
(combined cheap baseline) remains required.**

**Two modifications are declared here, BEFORE any new data exists, and justified:**

```text
M1. B6 (cheap relational) -- REPAIR its element identity handling. As implemented it cannot distinguish a relation from
    its swapped counterpart, which is a CAPABILITY DEFECT, not a tuning choice. Repairing it makes the cheap relational
    baseline STRONGER.

M2. B5 (simple spectral) -- REPAIR its capability so it can express the distinction the easy control presents. The
    0.90 bar is NOT moved. The baseline is strengthened to meet the bar; the bar is not lowered to meet the baseline.
```

**THE DIRECTION RULE, which governs both and any future modification:**

> **A cheap baseline may only ever be made STRONGER. Never weaker, never narrower, never removed.**
>
> Strengthening a cheap baseline makes it *harder* for the task to reach eligibility — it works against the candidate,
> and against us. Weakening one works *for* the candidate, and is the cheapest way in the world to manufacture a
> survivor. **Changes in the conservative direction are permitted and must be declared before data; changes in the other
> direction are not available at any price.**

**Not modified, and not modifiable:** the decision rule, the thresholds (0.65 / 0.60 / 0.90), the chance band
(0.40–0.60), the sample count, the train/test fraction, and the requirement that all baselines be reported including
losers.

**Fresh seeds are required.** The v2.65 target-task scores have been *seen*. Reusing that data would evaluate
strengthened baselines on samples whose results are already known, which is a soft form of choosing after seeing. **New
seeds for both variants, fixed in the implementation slice before generation, and recorded.**

## 5. Evaluation Rule

**The spirit and the letter of v2.65 are preserved. Nothing is loosened.**

```text
- THE POSITIVE CONTROL MUST PASS before any target-task baseline failure may be interpreted. Every cheap baseline
  capable of expressing the distinction must clear the 0.90 bar on the repaired easy control.
- THE RANDOM CONTROL MUST SIT AT CHANCE ON BOTH VARIANTS -- inside the fixed two-sided band, neither above nor below.
  Off chance on either variant, on either side, means the harness is broken.
- IF ANY REQUIRED POSITIVE-CONTROL CHECK FAILS, THE VERDICT IS UNINFORMATIVE. Stop the run. Do not bank the failure. Any
  further repair belongs in yet another preregistration, before yet more data.
- IF ANY CHEAP BASELINE SOLVES THE TARGET TASK (>= 0.65), THE TASK IS DEAD. Do not run a Brainvision-style reading on a
  dead task. Do not retune the task. Do not adjust criteria after results.
- IF THE CHEAP BASELINES FAIL ON THE TARGET (all < 0.60) AND THE POSITIVE CONTROL PASSED, that creates ONLY
  ADMINISTRATIVE ELIGIBILITY for a later, separately gated OPERATOR DECISION about whether a Brainvision-style reading
  should even be proposed. IT IS NOT EVIDENCE FOR BRAINVISION. Not support, not promise, not a signal, not a finding.
- THE AMBIGUITY BAND REMAINS (0.60 <= best < 0.65 => NO CONCLUSION), and it may not be pushed either way by retuning.

NO BRAINVISION-STYLE READING IS AUTHORIZED BY THIS DOCUMENT, UNDER ANY OUTCOME.
```

## 6. Failure Outcomes — Pre-Accepted

**All legitimate. None is a failed slice. Accepted here, before anything is known.**

```text
- the repaired control STILL fails -- and note that this is a LIKELY outcome: if B6's identity handling is not fully
  repaired, a control built under R1-R4 is designed to catch exactly that, and would return UNINFORMATIVE again. THE
  CONTROL WORKING CORRECTLY LOOKS LIKE THE RUN FAILING.
- the cheap relational baseline wins -- the expected case.
- the combined cheap baseline wins.
- the target task is dead.
- the run is uninformative.
- this preregistration is still too weak, and says so.
- the target is abandoned.
```

**And the outcome that is not on the list, because it would not be an outcome:** *the repaired control was hard, so we
made it easier.*

## 7. Operator Checkpoint

```text
RECOMMEND: CODEX REVIEW OF THIS PREREGISTRATION BEFORE ANY IMPLEMENTATION.

AFTER REVIEW, THE OPERATOR MAY CHOOSE:

  A. Implement the repaired generator / control + cheap baselines only.
     -- A EXCLUDES ANY BRAINVISION-STYLE READING. None. Not to look.
  B. Modify this preregistration.
  C. Pause.
  D. Abandon the target.

Undeveloped, unranked, none owed. Pause is co-equal. Abandoning is not a loss, and after two harness defects it is a
reasonable reading of the evidence about our own harness -- which is the only thing this line has produced so far.
```

## 8. Conclusion

```text
This preregistration repairs only the positive-control weakness found in v2.65.
It produces no evidence.
It authorizes no Brainvision-style reading.
It does not bank any v2.65 target-task failure.
Implementation, if later approved, is limited to repaired generator/control plus cheap baselines.
No claim lock moves.
verdict = HOLD
```

`OUTCOME_LABEL: BRAINVISION_TINY_SYNTHETIC_REPAIRED_CONTROL_PREREGISTRATION_ONLY`

## 9. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_TINY_SYNTHETIC_REPAIRED_CONTROL_PREREGISTRATION_v2.66.md
(new, docs-only, untracked; over the accepted v2.65 run edge "bb9f6bf research(brainvision): run tiny synthetic cheap
baseline gate").

Verify that this preregistration:
- is docs-only: no code, no tests, no implementation, no fixture data, no arrays / images, no generated samples, no real
  clips; no Brainvision-style reading; no screen / runtime / memory / integration path; no classifier / neural work; no
  vision claim; no §0 pointer; no tags;
- frames v2.65 correctly: the run was UNINFORMATIVE -- not failure and not support; no Brainvision-style reading was
  implemented or run; the near-chance target-task scores CANNOT BE BANKED; the positive-control DESIGN was too weak; and
  any repaired run requires a new preregistration before new data;
- states what v2.65 showed and no more (B5 missed the bar; the rule therefore returned UNINFORMATIVE; the lockstep easy
  control did not exercise the distinct-element relational capability the target demands; a baseline could pass that
  control and still be incapable on the target; this is a HARNESS / CONTROL DEFECT, not a Brainvision result);
- defines the REPAIRED POSITIVE-CONTROL REQUIREMENT in plain language (elements remain distinct; the relation is not
  lockstep and does not survive swapping the two elements; the relation is blatant but still requires tracking two
  separately moving elements; the cheap relational baseline must compare the two trajectories distinctly), with NO data,
  arrays, or generation parameters;
- states the generalizing rule: MATCHING MAY BE SWITCHED OFF ONLY ON AXES IRRELEVANT TO THE CAPABILITY BEING CERTIFIED --
  a control that eases the tested capability certifies nothing;
- keeps B1-B7 fixed, keeps B6 as expected strongest and B7 as required, and declares any modification BEFORE data with
  justification -- verifying that the declared modifications (B6 identity-handling repair; B5 capability repair) only
  make cheap baselines STRONGER, that the 0.90 bar is NOT lowered, and that the DIRECTION RULE (a cheap baseline may
  only ever be made stronger) is stated;
- leaves the decision rule, thresholds, chance band, sample count, split, and full-reporting requirement UNCHANGED, and
  requires FRESH SEEDS because the v2.65 target scores have been seen;
- preserves the evaluation rule (positive control must pass first; random control at chance on both variants, two-sided;
  any failed check => UNINFORMATIVE; any cheap baseline solving the target => DEAD; target failure => ADMINISTRATIVE
  ELIGIBILITY ONLY, never evidence; ambiguity band retained) and authorizes NO Brainvision-style reading under any
  outcome;
- pre-accepts all failure outcomes, including that the repaired control still fails -- explicitly noting that a correctly
  working control LOOKS LIKE the run failing -- and forbids making the control easier;
- offers exactly four operator choices with A excluding any Brainvision-style reading, none owed, pause co-equal;
- states the required conclusion block verbatim and preserves all claim locks False with verdict = HOLD.

Flag any implementation, code, data, array, image, or generated sample; any Brainvision-style reading authorized or
assumed; any banking of the v2.65 target-task scores; any threshold, chance band, sample count, split, seed policy, or
decision rule loosened; any baseline weakened, narrowed, or removed; any easy control that eases the capability under
test; any outcome treated as a failure of the slice; any eligibility described as evidence, support, or promise; any
successor treated as owed; or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

All claim locks False, and the frozen verdict **HOLD**, are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Tiny Synthetic Repaired-Control Preregistration v2.66. Docs-only preregistration over the
accepted v2.65 run edge. No code, tests, implementation, fixture data, arrays, images, generated samples, or real clips;
no Brainvision-style reading; no screen / runtime / memory / integration path; no classifier / neural work; no vision or
readiness claim; authorizes nothing. Responds to the v2.65 UNINFORMATIVE run — NOT a failure and NOT support — in which
NO Brainvision-style reading was implemented or run, whose near-chance target-task cheap-baseline scores CANNOT BE
BANKED, and whose positive-control DESIGN was too weak: the lockstep easy control did not exercise the distinct-element
relational capability the target demands, so a baseline could pass it and still be incapable on the target — A HARNESS /
CONTROL DEFECT, NOT A BRAINVISION RESULT. Defines the repaired positive-control requirement in plain language (elements
remain distinct; the relation is not lockstep and does not survive swapping the elements; blatant but still requiring two
separately moving elements to be tracked and compared; the cheap relational baseline must compare the trajectories
distinctly), and states the generalizing rule: MATCHING MAY BE SWITCHED OFF ONLY ON AXES IRRELEVANT TO THE CAPABILITY
BEING CERTIFIED — a control that eases the tested capability certifies nothing. Keeps B1–B7 fixed with B6 expected
strongest and B7 required; declares two modifications BEFORE data (B6 identity-handling repair; B5 capability repair),
both of which only make cheap baselines STRONGER, under the DIRECTION RULE that a cheap baseline may only ever be
strengthened, never weakened, narrowed, or removed — the 0.90 bar is not lowered to meet a baseline. Leaves the decision
rule, thresholds, two-sided chance band, sample count, split, and full-reporting requirement UNCHANGED, and requires
FRESH SEEDS because the v2.65 target scores have been seen. Preserves the evaluation rule (positive control must pass
first; random control at chance on both variants; any failed check ⇒ UNINFORMATIVE; any cheap baseline solving the target
⇒ DEAD; target failure ⇒ ADMINISTRATIVE ELIGIBILITY ONLY, never evidence; ambiguity band retained), and authorizes NO
Brainvision-style reading under any outcome. Pre-accepts every failure outcome, including that the repaired control still
fails — noting that a correctly working control LOOKS LIKE the run failing — and forbids making the control easier.
Offers four operator choices (implement repaired generator / control + cheap baselines only, EXCLUDING any
Brainvision-style reading; modify; pause; abandon), none owed, pause co-equal. Preserves all claim locks False and the
frozen verdict HOLD; outcome label BRAINVISION_TINY_SYNTHETIC_REPAIRED_CONTROL_PREREGISTRATION_ONLY; no `§0` pointer
added; no tags.*
