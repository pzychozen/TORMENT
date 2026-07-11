# TORMENT Brainvision Control-Collapse Reachability Question Plan v2.39

## 1. Status / Scope

**DOCS-ONLY question PLAN.** This is a plan note only. It opens **no** code, **no** tests, **no** artifact, **no**
fixtures, **no** data, **no** runtime, and **no** integration lane. It sits over the accepted v2.38 edge (`d73d9ca
docs(research): synthesize null-first adversarial role scaffold`) and changes none of the accepted files.

**v2.39 plans a QUESTION — and pre-registers its own negative answer.** v2.38 recommended this slice only on one
condition: that it state **in advance** what would count as *"control-collapse is NOT reachable"*, and be genuinely
willing to conclude it. Section 6 discharges that condition. If the answer turns out to be no, the null-first direction
is weakened at its root, and this plan says so before knowing.

**Explicitly authorized: nothing.**

```text
NO FIXTURE DESIGN, NO IMPLEMENTATION, AND NO TESTS ARE AUTHORIZED.
NO METRICS, DESCRIPTORS, COORDINATES, THRESHOLDS, FORMULAS, SCORES, GENERATION RULES, SCHEMAS, DATA SHAPES,
  DECISION RULES, ARRIVAL RULES, PASS/FAIL GATES, OR VALIDATION ARE AUTHORIZED.
NO CLASSIFIER (FORM B) OR NEURAL (FORM C) WORK. NO SCREEN / REAL-CLIP / RUNTIME / MEMORY PATH.
NO VISION CLAIM AND NO READINESS CLAIM.
ANY NEXT PATH REQUIRES SEPARATE OPERATOR APPROVAL AND SEPARATE CODEX REVIEW.
NO §0 POINTER; NO TAGS.
```

Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6. **HOLD / HELD means held for
analysis and claim control — not abandoned.**

```text
flat_field_validated                        = False      null_rejected                           = False
role_validated                              = False      artifact_ruled_out                      = False
schema_validated                            = False      proxy_ruled_out                         = False
entanglement_resolved                       = False      confound_controlled                     = False
by_residual_isolated                        = False      control_collapse_ruled_out              = False
generic_chroma_proxy_ruled_out              = False      control_collapse_detected               = False
                                                         control_collapse_reachability_validated = False
first_pass_structure_validity_claim_allowed = False      candidate_structure_validated            = False
temporal_claim_allowed                      = False      candidate_structure_survived             = False
descriptor_validity_claim_allowed           = False      candidate_structure_detected             = False
geometry_validity_claim_allowed             = False
screen_readiness_claim_allowed              = False
runtime_readiness_claim_allowed             = False
memory_readiness_claim_allowed              = False
integration_readiness_claim_allowed         = False
vision_claim_allowed                        = False
verdict                                      = HOLD
```

## 2. Grounding

```text
v2.33  TARGET SCAN (bcd3404): null-first adversarial fixture design selected as PRIMARY, on the criterion "what could
       this target FAIL at?"; the NULL SINK named as its hazard.
v2.34  NULL-FIRST PLAN (424b5a8): the adversarial FLOOR; adversary fixed before any candidate and never weakened (S2);
       S3 (a pre-stated, REACHABLE survival path) binding; S5 (the adversary can lose its own case).
v2.35  SIX SYMBOLIC ROLES (537ee8b), including E_control_collapse_role.
v2.36  IMPLEMENTATION-BOUNDARY REVIEW (582a972): W1 -- E is reachable in LANGUAGE ONLY.
v2.37  STATIC SYMBOLIC ROLE ARTIFACT (bfaa828): E generated, never tested / detected / ruled out / avoided / handled;
       S3 advanced by exactly nothing.
v2.38  SYNTHESIS (d73d9ca): scaffold PAUSED / HELD as complete vocabulary; CONTROL-COLLAPSE REACHABILITY named as the
       real pressure point; this plan recommended -- conditional on pre-stating its own failure condition.
```

## 3. Central Question

```text
"Can future null-first synthetic design preserve control-collapse as a genuinely reachable unresolved endpoint, rather
 than making candidate-structure survival structurally inevitable?"
```

## 4. What Control-Collapse Means, And What It Must Remain

```text
CONTROL-COLLAPSE means: the future design may become UNABLE TO DISTINGUISH the null / artifact / proxy / confound /
unresolved / candidate-structure possibilities in a non-claim-safe way. The design turns its suspicion on its own
adversary and finds that the adversary does not hold apart.

IT MUST REMAIN:
    reachable        -- a design in which it cannot occur is not adversarial;
    honest           -- it says something true about the design, not about the world;
    non-punitive     -- reporting it costs nothing and blames no one;
    non-success      -- it is not a finding, and nothing is learned about colour or structure;
    non-failure      -- the work did not fail; the controls did not hold apart;
    non-validation   -- it validates nothing, including itself;
    non-closure      -- it closes no question.

IT MUST NOT BE TREATED AS:
    an implementation bug        a test failure           noise                    operator error
    candidate survival           hidden positive evidence  control passed          null rejected
    artifact ruled out           proxy ruled out           confound controlled

EVERY ONE OF THOSE READINGS IS A CLAIM, and every one of them is barred. The most dangerous is the first: the moment
control-collapse is filed as a BUG, someone will fix it -- and "fixing" it means adjusting the adversary until it holds
apart, which is v2.34 S2 violated, and the whole null-first stance lost in a maintenance commit.

SAYABLE IS NOT REACHABLE. v2.37 proved that a design can SAY "control-collapse" -- it is a noun in a frozen artifact.
Saying it costs nothing precisely because nothing is real. The question this plan opens is whether a CONCRETE design
can leave a real path by which the collapse actually occurs and is reported. That is a different property, and nothing
established so far bears on it.
```

## 5. The Reachability Obligation

```text
R1. FUTURE NULL-FIRST DESIGNS ARE ONLY HONEST IF CONTROL-COLLAPSE REMAINS A POSSIBLE REPORTING ENDPOINT.
    Not a theoretical concession in a doc. A reachable endpoint in the design as built.

R2. REACHABLE MEANS NEITHER OUTCOME IS GUARANTEED BY CONSTRUCTION. There are TWO ways to fail this, and they are
    symmetric:
      - FORCED SURVIVAL: candidate-structure survival is structurally inevitable; every path leads to "something is
        there". This is POSITIVE FORCING (the BY/chroma trap).
      - FORCED COLLAPSE: collapse is structurally inevitable; nothing could ever hold apart. This is the NULL SINK,
        and it is not rigour -- it is inertness.
    A design in which control-collapse is UNREACHABLE is defended, not adversarial. A design in which it is
    UNAVOIDABLE reports nothing. Reachability means it CAN happen and is not FORCED to.

R3. IT MUST BE AS CHEAP TO REPORT AS ANY OTHER ENDPOINT. If collapse is the outcome that costs the most to write up,
    it will not get written up. Cost asymmetry is how honest endpoints quietly disappear.

R4. THE DESIGN MUST BE ABLE TO SAY IT ABOUT ITSELF. Control-collapse is the only endpoint whose subject is the
    adversary rather than the object of study. A design that can report every failure except its own is not
    self-suspicious; it is self-exempt.
```

## 6. Pre-Stated Failure Condition (the v2.38 condition, discharged)

**v2.38 required this plan to say, in advance, what would count as *control-collapse is NOT reachable* — and to be
willing to conclude it. Here it is. If any of the following holds of a future design, and cannot be removed without
introducing metrics, thresholds, decision rules, or validation criteria, then CONTROL-COLLAPSE IS NOT REACHABLE in
that design.**

```text
U1. CANDIDATE-STRUCTURE SURVIVAL IS THE ONLY NON-NULL ENDPOINT. Every path that is not "nothing" leads to "something
    survived". Collapse has nowhere to land.
U2. THE NULL / ARTIFACT / PROXY / CONFOUND ROLES ARE DECORATIVE ONLY. They are named in the write-up but nothing in
    the design turns on them; they could be deleted without changing any outcome.
U3. THE CONTROLS ARE ASSUMED VALID BY CONSTRUCTION. Their distinctness is a premise of the design rather than
    something the design could discover to be false.
U4. UNRESOLVED OUTCOMES ARE TREATED AS FAILURES TO BE FIXED. Collapse and entanglement are handled as defects, and the
    remedy is to adjust the design until they stop occurring (v2.34 S2 violated).
U5. THE DESIGN CANNOT REPORT THAT ITS CONTROLS FAILED TO DISTINGUISH ANYTHING. There is no place, no vocabulary, and
    no permitted outcome in which the adversary loses its own case.

IF THE ANSWER TO THE CENTRAL QUESTION IS NO -- if control-collapse cannot be kept reachable without smuggling in a
metric, a threshold, a decision rule, or a validation criterion -- THEN THE NULL-FIRST DIRECTION IS WEAKENED AT ITS
ROOT, AND THAT MUST BE SAID PLAINLY. It would mean the direction chosen in v2.33 cannot deliver the one property that
justified choosing it (that it could come out WRONG). That is a real negative result about the project's own chosen
path, and it is a legitimate, publishable-internally outcome of this line of work. This plan does not predict which way
it goes, and does not prefer either answer.
```

## 7. Allowed Reporting Language

A future report **MAY** say, and nothing stronger:

```text
control-collapse remains reachable
future design may report control-collapse
future design may fail to distinguish adversarial families
unresolved control behavior remains an honest endpoint
candidate structure remains only a future question
```

Note the modality. Every allowed line is about what a design **may** do or what **remains** possible. None asserts that
anything happened.

## 8. Forbidden Reporting Language

A future report **MUST NOT** say, in any wording, hedged or unhedged:

```text
control-collapse detected       control-collapse ruled out      controls passed
candidate survived              structure detected              null rejected
artifact ruled out              proxy ruled out                 confound controlled
descriptor validated            geometry validated              metric validated
screen ready                    runtime ready                   memory ready
vision achieved                 Brainvision sees
```

These are claim **shapes**, not exact strings. "The controls held up", "we ruled out the artifact", "the collapse case
didn't arise", "nothing collapsed, so the design is sound", "the adversary is in place" are all the same forbidden move
in other words. In particular, **"control-collapse did not occur" is a forbidden claim**: not observing a collapse is
not evidence that the controls are sound — it is the floor, and the floor is not a finding (v2.34).

## 9. What v2.39 Does NOT Authorize

```text
v2.39 authorizes NO fixture design, NO implementation, NO tests, NO artifacts, NO fixture data, NO arrays or images,
NO descriptors, NO coordinates, NO metrics, NO scores, NO thresholds, NO formulas, NO generation rules, NO schemas or
data shapes, NO decision rules, NO arrival rules, NO evidence / confidence / classification / validation / pass-fail /
survival / positive-structure fields, NO screen / runtime / memory paths, NO classifier (form B) or neural (form C)
work, NO real clips, and NO vision or readiness claims.

AND: v2.39 defines NO way of deciding whether control-collapse has occurred. It plans a QUESTION. Any such rule would
be a metric, and a metric is exactly what the question is asking whether we can avoid.

Any next path requires SEPARATE OPERATOR APPROVAL and SEPARATE CODEX REVIEW.
```

## 10. Recommended Next Slice (one; separately gated)

```text
RECOMMEND (primary, and the only recommended path):

  v2.40  CONTROL-COLLAPSE BOUNDARY SCAN  (DOCS-ONLY)

  v2.40 MAY: compare possible ways of PRESERVING control-collapse reachability before any future fixture design --
  conceptual approaches only, weighed against U1-U5 (Section 6) and R1-R4 (Section 5), each with an honest assessment
  of whether it would keep collapse reachable without smuggling in a metric, threshold, decision rule, or validation
  criterion.

  v2.40 MUST NOT: design fixtures; design tests; define fixture data, arrays, images, generation rules, schemas, data
  shapes, descriptors, coordinates, metrics, scores, thresholds, formulas, decision rules, or validation criteria;
  define how a collapse would be recognised; open any screen / real-clip / runtime / memory / classifier / neural /
  vision path; or implement anything.

  v2.40 MUST ALSO be willing to conclude that NO approach preserves reachability -- and to say so. If every candidate
  approach requires a metric to keep collapse reachable, that IS the answer to Section 3, and it is a negative one.

  v2.40 STAYS DOCS-ONLY unless separately reviewed and operator-approved otherwise. v2.39 does not open it.

NOT RECOMMENDED: fixture design; any descriptor / coordinate / metric / threshold / formula / decision-rule /
pass-fail / validation work; any screen / real-clip / runtime / memory work; classifier or neural work; any vision
work. The v2.38 fallback (return to broader Brainvision falsification search) and the v2.38 honest stop (pause
Brainvision synthetic work) both remain available to the operator at any time.
```

## 11. Forbidden Drift Register

```text
- SAYABLE becoming REACHABLE. v2.37 made control-collapse sayable. Nothing has made it reachable.
- control-collapse being filed as an IMPLEMENTATION BUG, a TEST FAILURE, NOISE, or OPERATOR ERROR -- and then "fixed",
  which means adjusting the adversary until it holds apart (v2.34 S2 violated).
- "no collapse occurred" becoming EVIDENCE that the controls are sound. It is the floor.
- collapse being treated as CANDIDATE SURVIVAL, hidden positive evidence, or a passed control.
- collapse becoming UNAVOIDABLE -- the null sink, in which the design reports nothing whatever is true.
- candidate-structure survival becoming STRUCTURALLY INEVITABLE -- positive forcing, the BY/chroma trap.
- collapse becoming EXPENSIVE to report, so that it silently never gets reported (R3).
- the reachability QUESTION becoming a reachability CLAIM. control_collapse_reachability_validated stays False.
- a question plan becoming an AUTHORIZATION; a pre-stated failure condition becoming a prediction.
```

## 12. Non-Claim Interpretation

```text
WHAT v2.39 MAY ESTABLISH (and only this):
  - the CENTRAL QUESTION, posed;
  - the REACHABILITY OBLIGATION (R1-R4), including that neither outcome may be guaranteed by construction;
  - the PRE-STATED FAILURE CONDITION (U1-U5) -- what would count as "not reachable", stated before the answer is
    known, and accepted as a legitimate outcome;
  - the allowed and forbidden reporting language;
  - one gated, docs-only next slice (v2.40).

WHAT IT DOES NOT ESTABLISH:
  not fixtures / data      not a descriptor / coordinate / metric      not a decision rule
  not validation           not closure          not readiness          not vision
  not that control-collapse IS reachable        not that it is NOT
  not that any control-collapse occurred, was detected, was ruled out, or was avoided
  not that candidate structure survived, was detected, or is expected
  not that the null-first direction is sound    not that it is unsound

Posing a question answers nothing. control_collapse_reachability_validated = False. S3 remains binding and
undischarged. The v2.22 BY/chroma question remains UNRESOLVED and possibly unanswerable.
```

## 13. Verdict

```text
verdict                                      = HOLD
flat_field_validated                         = False
role_validated                               = False
schema_validated                             = False
entanglement_resolved                        = False
by_residual_isolated                         = False
generic_chroma_proxy_ruled_out               = False
null_rejected                                = False
artifact_ruled_out                           = False
proxy_ruled_out                              = False
confound_controlled                          = False
control_collapse_ruled_out                   = False
control_collapse_detected                    = False
control_collapse_reachability_validated      = False
candidate_structure_validated                = False
candidate_structure_survived                 = False
candidate_structure_detected                 = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False
geometry_validity_claim_allowed              = False
screen_readiness_claim_allowed               = False
runtime_readiness_claim_allowed              = False
memory_readiness_claim_allowed               = False
integration_readiness_claim_allowed          = False
vision_claim_allowed                         = False

OUTCOME_LABEL: BRAINVISION_CONTROL_COLLAPSE_REACHABILITY_QUESTION_PLAN_ONLY
```

v2.39 is a docs-only question plan. It grounds itself in v2.33–v2.38 and poses the central question of whether future
null-first synthetic design can preserve control-collapse as a genuinely reachable unresolved endpoint rather than
making candidate-structure survival structurally inevitable. It states the reachability obligation (future null-first
designs are honest only if control-collapse remains a possible reporting endpoint; neither outcome may be guaranteed by
construction; collapse must be as cheap to report as any other endpoint; the design must be able to say it about
itself); distinguishes SAYABLE from REACHABLE; **pre-states the failure condition** (U1–U5) and accepts a negative
answer as a legitimate outcome that would weaken the null-first direction at its root; fixes the allowed and forbidden
reporting language, including that *"control-collapse did not occur"* is itself a forbidden claim; authorizes no
fixture design, implementation, tests, metrics, descriptors, coordinates, thresholds, formulas, validation, classifier
/ neural paths, screen / runtime / memory paths, real clips, or vision claims; defines no way of deciding whether a
collapse occurred; and recommends one separately gated docs-only next slice (v2.40 control-collapse boundary scan),
which must itself be willing to conclude that no approach preserves reachability. It is not self-authorizing. All claim
locks and the frozen verdict **HOLD** are preserved and unmoved.

## 14. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_CONTROL_COLLAPSE_REACHABILITY_QUESTION_PLAN_v2.39.md
(new, docs-only, untracked; over the accepted v2.38 edge
 "d73d9ca docs(research): synthesize null-first adversarial role scaffold").

Verify that this plan:
- is docs-only and authorizes NOTHING: no fixture design, no implementation, no tests, no artifacts, no fixture data,
  no arrays / images, no descriptors, no coordinates, no metrics, no scores, no thresholds, no formulas, no generation
  rules, no schemas / data shapes, no decision rules, no arrival rules, no evidence / confidence / classification /
  validation / pass-fail / survival / positive-structure fields, no screen / runtime / memory paths, no classifier
  (form B) / neural (form C) work, no real clips, no vision or readiness claims; adds no §0 pointer and no tags; and
  states that any next path requires separate operator approval and separate review;
- grounds itself in v2.33 (target scan), v2.34 (null-first plan), v2.35 (symbolic family proposal), v2.36
  (implementation-boundary review), v2.37 (static symbolic role artifact), and v2.38 (scaffold paused as complete
  vocabulary; control-collapse reachability named as the next pressure point);
- poses the central question verbatim ("Can future null-first synthetic design preserve control-collapse as a
  genuinely reachable unresolved endpoint, rather than making candidate-structure survival structurally inevitable?");
- frames control-collapse as the future design becoming unable to distinguish null / artifact / proxy / confound /
  unresolved / candidate-structure possibilities in a non-claim-safe way, and requires it remain reachable, honest,
  non-punitive, non-success, non-failure, non-validation, and non-closure -- and never treated as an implementation
  bug, test failure, noise, operator error, candidate survival, hidden positive evidence, control passed, null
  rejected, artifact ruled out, proxy ruled out, or confound controlled;
- states the reachability obligation (future null-first designs are only honest if control-collapse remains a possible
  reporting endpoint), distinguishes SAYABLE from REACHABLE, and requires that NEITHER forced survival NOR forced
  collapse be guaranteed by construction;
- PRE-STATES the failure condition (U1 candidate-structure survival the only non-null endpoint; U2 null / artifact /
  proxy / confound roles decorative only; U3 controls assumed valid by construction; U4 unresolved outcomes treated as
  failures to be fixed; U5 the design cannot report that its controls failed to distinguish anything) and accepts a
  NEGATIVE answer as a legitimate outcome that would weaken the null-first direction at its root;
- fixes the allowed reporting language (control-collapse remains reachable; future design may report control-collapse;
  future design may fail to distinguish adversarial families; unresolved control behavior remains an honest endpoint;
  candidate structure remains only a future question) and the forbidden reporting language as claim SHAPES
  (control-collapse detected; control-collapse ruled out; controls passed; candidate survived; structure detected;
  null rejected; artifact ruled out; proxy ruled out; confound controlled; descriptor validated; geometry validated;
  metric validated; screen ready; runtime ready; memory ready; vision achieved; Brainvision sees -- and paraphrases,
  including that "control-collapse did not occur" is itself forbidden);
- defines NO rule for deciding whether a collapse occurred;
- recommends exactly ONE separately gated next slice -- a DOCS-ONLY "v2.40 control-collapse boundary scan" that may
  compare ways of preserving reachability but must not design fixtures or tests, and must be willing to conclude that
  no approach preserves reachability -- and is NOT self-authorizing;
- preserves the locks and verdict (Section 13), including control_collapse_reachability_validated = False and
  verdict = HOLD; HOLD/HELD read as held for analysis, not abandoned.

Flag any fixture / test / artifact / data / metric / descriptor / coordinate / threshold / formula / generation rule /
schema / decision rule / validation criterion defined anywhere; any rule for recognising a collapse; any treatment of
control-collapse as a bug, failure, noise, or operator error; any treatment of "no collapse occurred" as evidence; any
design in which collapse is unreachable OR unavoidable; any claim that control-collapse was detected, ruled out, or
avoided; any claim that candidate structure survived, was detected, or is expected; any reachability CLAIM; any
authorization of implementation; or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
All claim locks False — including `control_collapse_ruled_out`, `control_collapse_detected`, and
`control_collapse_reachability_validated` — and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Control-Collapse Reachability Question Plan v2.39. Docs-only question plan over the accepted
v2.38 edge. Opens no implementation lane, no tests, no artifact, no fixture design, and no data; adopts no descriptor /
coordinate / metric / score / threshold / formula / generation rule / schema / data shape / decision rule / arrival
rule / pass-fail gate / validation; opens no classifier / neural / screen / real-clip / runtime / memory path; makes no
vision or readiness claim; authorizes nothing and is not self-authorizing. Poses the central question of whether future
null-first synthetic design can preserve control-collapse as a GENUINELY REACHABLE unresolved endpoint rather than
making candidate-structure survival structurally inevitable; frames control-collapse as the design becoming unable to
distinguish null / artifact / proxy / confound / unresolved / candidate-structure possibilities in a non-claim-safe
way, to remain reachable, honest, non-punitive, non-success, non-failure, non-validation, and non-closure, and never to
be treated as an implementation bug, test failure, noise, operator error, candidate survival, hidden positive evidence,
control passed, null rejected, artifact ruled out, proxy ruled out, or confound controlled; distinguishes SAYABLE from
REACHABLE and requires that neither forced survival nor forced collapse be guaranteed by construction; PRE-STATES the
failure condition (U1–U5) as v2.38 required, and accepts a negative answer as a legitimate outcome that would weaken
the null-first direction at its root; fixes allowed and forbidden reporting language as claim shapes, including that
"control-collapse did not occur" is itself forbidden; defines no rule for recognising a collapse; recommends one
separately gated docs-only next slice (v2.40 control-collapse boundary scan, which must itself be willing to return a
negative answer); keeps prior BY / color / chroma work FROZEN EVIDENCE, the BY/chroma scaffold REPORTING LANGUAGE ONLY,
the null-first role scaffold PAUSED HELD as complete vocabulary, S3 BINDING AND UNDISCHARGED, and the v2.22 question
UNRESOLVED and possibly unanswerable; preserves all claim locks and the frozen verdict HOLD; outcome label
BRAINVISION_CONTROL_COLLAPSE_REACHABILITY_QUESTION_PLAN_ONLY; no `§0` pointer added; no tags.*
