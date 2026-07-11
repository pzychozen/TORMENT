# TORMENT Brainvision Control-Collapse Boundary Scan v2.40

## 1. Status / Scope

**DOCS-ONLY boundary SCAN.** This is a scan note only. It opens **no** code, **no** tests, **no** artifact, **no**
fixture design, **no** fixture data, **no** runtime, and **no** integration lane. It sits over the accepted v2.39 edge
(`e59cf75 docs(research): plan control-collapse reachability question`) and changes none of the accepted files.

**v2.40 compares boundary approaches. It adopts none of them.** It weighs possible docs-only ways of preserving
control-collapse reachability *before* any future null-first fixture design is allowed, and recommends. It opens
nothing and schedules nothing.

**Explicitly authorized: nothing.**

```text
NO FIXTURE DESIGN, NO IMPLEMENTATION, NO TESTS, AND NO ARTIFACTS ARE AUTHORIZED.
NO METRICS, DESCRIPTORS, COORDINATES, THRESHOLDS, FORMULAS, SCORES, GENERATION RULES, SCHEMAS, DATA SHAPES,
  DECISION RULES, ARRIVAL RULES, PASS/FAIL GATES, OR VALIDATION ARE AUTHORIZED.
NO RECOGNITION RULE FOR CONTROL-COLLAPSE IS DEFINED OR AUTHORIZED.
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
v2.38  SYNTHESIS / CLOSURE (d73d9ca): the null-first role scaffold is PAUSED / HELD as completed VOCABULARY.
       Control-collapse reachability named as the real pressure point.
v2.39  QUESTION PLAN (e59cf75): the central question posed; the reachability obligation (R1-R4); the PRE-STATED
       FAILURE CONDITION (U1-U5); allowed / forbidden language; NO recognition rule defined.

TWO v2.39 FINDINGS THIS SCAN IS BUILT ON:
  SAYABLE != REACHABLE. v2.37 made control-collapse SAYABLE -- a noun in a frozen artifact. Saying it costs nothing
  precisely because nothing is real. Whether a CONCRETE design leaves a real path by which collapse occurs is a
  different property, and nothing established so far bears on it.

  CONTROL-COLLAPSE MUST NOT BECOME MERELY DECORATIVE LANGUAGE. An endpoint that is named but can never be arrived at
  is worse than no endpoint at all: it makes the design LOOK adversarial while behaving as if it were defended.
```

## 3. Central Scan Question

```text
"Which boundary approach best preserves control-collapse as a genuinely reachable unresolved endpoint before any
 future fixture design is allowed?"
```

## 4. What A Boundary Can And Cannot Do (stated before comparing)

```text
A DOCS-ONLY BOUNDARY CAN PREVENT UNREACHABILITY. It can forbid the known structural moves by which collapse becomes
impossible: survival as the only exit; controls valid by premise; collapse handled as a defect.

A DOCS-ONLY BOUNDARY CANNOT MANUFACTURE REACHABILITY. No wording, in any document, makes a collapse actually
arrive-able in a design that does not exist. Reachability is a property of a CONCRETE design, and it can only be shown
there.

So the honest ceiling on this scan is: it can CLOSE THE KNOWN DOORS TO UNREACHABILITY. It cannot certify that the
remaining space is non-empty. Any approach that claims more than that is claiming more than a document can deliver,
and should be refused on that ground alone. control_collapse_reachability_validated stays False, and it would stay
False even if every approach below were adopted.
```

## 5. Candidate Comparison (qualitative; no scores)

```text
====================================================================================================================
A -- EXPLICIT COLLAPSE ENDPOINT BOUNDARY
    ("future designs must include control-collapse as an allowed unresolved reporting endpoint"; no detection defined)

  reachability preservation      : WEAK. It guarantees the endpoint EXISTS in the vocabulary. It does not guarantee
                                   anything can ever arrive there. This is exactly the SAYABLE-vs-REACHABLE gap.
  hidden decision semantics      : LOW. It defines no recognition rule, and asks for none.
  accidental validation language : MODERATE. "The design includes a collapse endpoint" slides easily into "the design
                                   accounts for collapse", which slides into "collapse is handled".
  candidate survival inevitable  : NOT ADDRESSED. A design can list a collapse endpoint and still funnel every path to
                                   survival. A is silent on that.
  collapse decorative only       : HIGH -- AND THIS IS A's CENTRAL FAILURE. A is precisely the approach that produces
                                   a named, unreachable endpoint. It is the decorative-language trap in boundary form.
  null-first compatibility       : SUPERFICIAL. Compatible in wording, hollow in substance.
  VERDICT: NECESSARY BUT NOWHERE NEAR SUFFICIENT. A alone would let the project believe it had secured what it had
           only named. Adopt A only as a rider on something structural.

====================================================================================================================
B -- ANTI-INEVITABILITY BOUNDARY
    ("candidate-structure survival must not be the only non-null endpoint")

  reachability preservation      : STRUCTURAL -- the strongest of the five. It attacks U1 directly: survival cannot be
                                   the only exit, so there is somewhere else a design can land.
  hidden decision semantics      : LOW-TO-MODERATE. Stating what may NOT be the only endpoint requires no rule for
                                   choosing among endpoints. The risk appears only if someone tries to PROVE
                                   non-inevitability, which would demand a criterion -- and a criterion is a metric.
                                   B must be a PROHIBITION, never a proof obligation.
  accidental validation language : LOW. It asserts nothing about any outcome.
  candidate survival inevitable  : DIRECTLY BLOCKED. This is B's whole purpose.
  collapse decorative only       : PARTIALLY GUARDED, WITH A REAL RESIDUAL HOLE -- see Section 6. B forbids the crude
                                   form (survival as the only exit). It does not by itself forbid the subtle form:
                                   other endpoints nominally present but never arrivable.
  null-first compatibility       : HIGH. It is the null-first floor (v2.34) restated as a constraint on design shape.
  VERDICT: THE STRONGEST SINGLE APPROACH. Insufficient alone (the residual hole).

====================================================================================================================
C -- CONTROL-HONESTY BOUNDARY
    ("future designs must preserve the possibility that controls fail to distinguish adversarial families, without
      treating that as implementation failure")

  reachability preservation      : STRUCTURAL IN A DIFFERENT DIRECTION. It attacks U3 (controls valid by premise) and
                                   U4 (unresolved outcomes treated as defects to be fixed). It keeps the collapse path
                                   OPEN OVER TIME -- which B does not.
  hidden decision semantics      : LOW. It forbids a REACTION, not a computation.
  accidental validation language : LOW-TO-MODERATE. "The controls are honest" must never become "the controls are
                                   sound". C protects the possibility of failure; it certifies nothing.
  candidate survival inevitable  : NOT DIRECTLY ADDRESSED. C keeps the door open; it does not stop the corridor from
                                   sloping toward survival.
  collapse decorative only       : DIRECTLY GUARDED. C is what stops a reachable collapse from being quietly
                                   engineered away as a bug. Without C, B's non-inevitability survives exactly until
                                   the first maintenance commit that "fixes" a collapse.
  null-first compatibility       : HIGH. It is v2.34 S2 (never weaken the adversary) and S5 (the adversary can lose
                                   its own case), made a boundary.
  VERDICT: THE NECESSARY COMPLEMENT TO B. Insufficient alone (says nothing about forced survival).

====================================================================================================================
D -- NO-RECOGNITION-RULE BOUNDARY
    ("collapse reachability may be discussed; no rule for recognizing collapse may be defined yet")

  reachability preservation      : NONE. It preserves nothing. It only prevents a particular corruption.
  hidden decision semantics      : LOWEST -- it exists to forbid exactly that.
  accidental validation language : LOW.
  candidate survival inevitable  : NOT ADDRESSED.
  collapse decorative only       : NOT ADDRESSED -- arguably WORSENED, since forbidding recognition without requiring
                                   anything else leaves collapse maximally nominal.
  null-first compatibility       : HIGH, but trivially so.
  VERDICT: NOT A STANDALONE APPROACH -- AND IT IS ALREADY IN FORCE. v2.39 §9 already defines no recognition rule.
           Adopting D as "the boundary" would be adopting the status quo and calling it progress. Keep D as a STANDING
           RIDER on whatever else is adopted, not as a choice.

====================================================================================================================
E -- HOLD / REDIRECT
    ("if reachability cannot be framed without hidden decision semantics, hold the branch and return to the broader
      falsification search")

  reachability preservation      : N/A. It is a stop.
  hidden decision semantics      : NONE.
  accidental validation language : NONE.
  candidate survival inevitable  : N/A.
  collapse decorative only       : N/A -- it refuses to produce decoration.
  null-first compatibility       : N/A.
  VERDICT: LEGITIMATE AND NOT A DEFEAT. If B + C cannot be stated without a criterion sneaking in, E is the correct and
           more honest move. It is the answer v2.39 pre-registered as acceptable.
====================================================================================================================
```

## 6. The Residual Hole B + C Does Not Close (stated, not hidden)

```text
B says: survival must not be the ONLY non-null endpoint.
A design can satisfy B by listing other endpoints -- and never being able to arrive at any of them.

THE DECORATIVE-ENDPOINT HOLE: endpoints nominally present, structurally unarrivable. B forbids the crude form of
unreachability; it does not forbid the subtle form. C narrows the hole considerably (an honest, non-punitive collapse
path is much harder to leave unarrivable, because the design is forbidden from treating its arrival as a defect), but C
is a constraint on REACTION, not on SHAPE, and it cannot by itself prove that a path exists.

CLOSING THIS HOLE WOULD REQUIRE SAYING WHAT "ARRIVABLE" MEANS -- and that is a criterion, and a criterion is a metric.
Which is precisely what the whole line of work is trying to avoid.

THEREFORE: the hole is NOT closed by this scan, and it must NOT be papered over. It is handed forward as the open
question any later slice must confront, and it is the reason this scan CANNOT certify reachability (Section 4). If it
later turns out that the hole can only be closed with a metric, then U-condition territory is reached, the answer to
v2.39's central question is NO, and that must be said plainly.
```

## 7. Recommendation

```text
PRIMARY:  B + C, TOGETHER, WITH D AS A STANDING RIDER AND A AS A WORDING RIDER.
FALLBACK: E -- hold / redirect to the broader falsification search -- if B + C cannot be kept NON-AUTHORIZING (i.e. if
          stating them requires a recognition rule, a criterion, or any decision semantics).

REASON: the strongest boundary is NOT to define collapse recognition. It is to (B) prevent future designs from
STRUCTURALLY FORCING candidate survival, while (C) preserving honest control failure as a valid unresolved endpoint.
Neither works alone: B without C is a design whose collapse path exists until someone fixes it away as a bug; C without
B is an honest reaction to an outcome the design will never actually produce. Together they attack U1, U3, U4 and U5.
D is already in force and stays. A contributes wording only, and must never be mistaken for substance.

WHAT B + C WOULD AND WOULD NOT DELIVER:
  WOULD:     close the KNOWN structural doors to unreachability, and keep them closed against later "maintenance".
  WOULD NOT: certify that collapse is reachable in any design (Section 4), or close the decorative-endpoint hole
             (Section 6). control_collapse_reachability_validated stays False.
```

## 8. Allowed And Forbidden Language

**Allowed** — and nothing stronger:

```text
control-collapse remains reachable
candidate survival must not be structurally inevitable
future controls may fail to distinguish adversarial families
control failure remains an honest unresolved endpoint
no recognition rule is defined
no validation follows
```

**Forbidden** — in any wording, as claim SHAPES rather than exact strings:

```text
control-collapse detected       control-collapse ruled out      controls passed
candidate survived              structure detected              null rejected
artifact ruled out              proxy ruled out                 confound controlled
descriptor validated            geometry validated              metric validated
screen ready                    runtime ready                   memory ready
vision achieved                 Brainvision sees
```

Paraphrases are the same forbidden move. And, carried from v2.39: **"control-collapse did not occur" is itself a
forbidden claim** — not observing a collapse is not evidence that the controls are sound. It is the floor, and the
floor is not a finding.

## 9. What v2.40 Does NOT Authorize

```text
NO fixture design. NO implementation. NO tests. NO artifacts. NO fixture data. NO arrays or images.
NO descriptors, coordinates, metrics, scores, thresholds, formulas, generation rules, schemas, data shapes, decision
rules, arrival rules, pass/fail gates, or validation criteria.
NO RECOGNITION RULE for control-collapse -- none is defined here, and none is authorized.
NO evidence / confidence / classification / validation / pass-fail / survival / positive-structure fields.
NO screen / real-clip / camera / live / sensor / streaming / runtime / memory path. NO classifier or neural work.
NO vision claim; NO readiness claim.

v2.40 ADOPTS no boundary. It compares and recommends. Any adoption requires SEPARATE OPERATOR APPROVAL and SEPARATE
CODEX REVIEW.
```

## 10. Recommended Next Slice (one; separately gated; only if B + C is safe)

```text
IF the operator accepts that B + C can be stated non-authorizingly:

  v2.41  ANTI-INEVITABILITY / CONTROL-HONESTY BOUNDARY PLAN  (DOCS-ONLY)

  v2.41 MAY: state the B + C boundary as a constraint on any FUTURE null-first design -- what may not be the only
  endpoint; what may not be treated as an implementation failure; what stays unmeasured; which claim locks stay False;
  and it must confront the Section-6 decorative-endpoint hole openly rather than declaring it closed.

  v2.41 MUST NOT: design fixtures; design tests; define metrics, scores, thresholds, formulas, coordinates,
  descriptors, generation rules, schemas, data shapes, decision rules, or validation criteria; define any RECOGNITION
  RULE for collapse; open any screen / real-clip / runtime / memory / classifier / neural / vision path; or implement
  anything.

  v2.41 MUST ALSO be willing to conclude that B + C cannot be stated without a criterion -- and to say so. That
  conclusion would answer v2.39's central question in the NEGATIVE, and it is a legitimate outcome.

IF B + C IS NOT SAFE -- if it cannot be stated without smuggling in a recognition rule, a criterion, or decision
semantics -- then the recommendation is E: HOLD, and REDIRECT to the broader Brainvision falsification search (v2.38
Option C). Pausing Brainvision synthetic work (v2.38 Option D) remains available and honest at any time.

v2.40 does not open v2.41. The operator chooses.
```

## 11. Forbidden Drift Register

```text
- SAYABLE becoming REACHABLE. Naming an endpoint is not providing a path to it.
- an adopted boundary becoming a REACHABILITY CLAIM. control_collapse_reachability_validated stays False, whatever is
  adopted.
- B becoming a PROOF OBLIGATION ("show that survival is not inevitable") -- which would require a criterion, and a
  criterion is a metric. B is a PROHIBITION.
- C becoming a certification that the controls are SOUND. C protects the possibility of failure; it certifies nothing.
- the decorative-endpoint hole (Section 6) being declared CLOSED, or quietly dropped from later documents.
- collapse being filed as an implementation bug, test failure, noise, or operator error -- and then "fixed", which
  means adjusting the adversary until it holds apart (v2.34 S2 violated).
- "no collapse occurred" becoming evidence that the controls are sound. It is the floor.
- D being adopted as "the boundary", which would be adopting the status quo and calling it progress.
- a SCAN becoming an AUTHORIZATION; a recommendation becoming a schedule.
```

## 12. Non-Claim Interpretation

```text
WHAT v2.40 MAY ESTABLISH (and only this):
  - a QUALITATIVE COMPARISON of five boundary approaches across six dimensions;
  - the honest ceiling on any docs-only boundary: it can close the known doors to UNREACHABILITY; it cannot certify
    REACHABILITY;
  - the residual DECORATIVE-ENDPOINT HOLE that B + C does not close;
  - a RECOMMENDATION (B + C primary, with D standing and A as wording only; E fallback), and nothing more.

WHAT IT DOES NOT ESTABLISH:
  not a boundary adopted    not fixtures / data     not a descriptor / coordinate / metric
  not a recognition rule    not validation          not closure       not readiness      not vision
  not that control-collapse IS reachable            not that it is NOT
  not that any collapse occurred, was detected, was ruled out, or was avoided
  not that candidate structure survived, was detected, or is expected

Comparing boundaries preserves nothing by itself. control_collapse_reachability_validated = False. S3 remains binding
and undischarged. The v2.22 BY/chroma question remains UNRESOLVED and possibly unanswerable.
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

OUTCOME_LABEL: BRAINVISION_CONTROL_COLLAPSE_BOUNDARY_SCAN_ONLY
```

v2.40 is a docs-only boundary scan. It grounds itself in v2.38 (scaffold closure) and v2.39 (the reachability question,
the SAYABLE-vs-REACHABLE distinction, and the warning against decorative collapse language); poses the central scan
question; states the honest ceiling on any docs-only boundary (it can close the known doors to unreachability; it
cannot certify reachability); compares five candidate approaches (A explicit collapse endpoint — necessary but hollow
alone, and the decorative-language trap in boundary form; B anti-inevitability — the strongest single approach; C
control-honesty — the necessary complement; D no-recognition-rule — already in force, a rider not a choice; E hold /
redirect — legitimate and not a defeat) across six qualitative dimensions with no numeric scoring; names the residual
**decorative-endpoint hole** that B + C does not close and refuses to paper over it; fixes the allowed and forbidden
language; adopts no boundary; and recommends **B + C together** (with D standing and A as wording only) as primary, and
**E** as fallback if B + C cannot be kept non-authorizing — with one separately gated docs-only next slice (v2.41
anti-inevitability / control-honesty boundary plan) only if B + C is safe. It is not self-authorizing. All claim locks
and the frozen verdict **HOLD** are preserved and unmoved.

## 14. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_CONTROL_COLLAPSE_BOUNDARY_SCAN_v2.40.md
(new, docs-only, untracked; over the accepted v2.39 edge
 "e59cf75 docs(research): plan control-collapse reachability question").

Verify that this scan:
- is docs-only and authorizes NOTHING: no fixture design, no implementation, no tests, no artifacts, no fixture data,
  no arrays / images, no descriptors, no coordinates, no metrics, no scores, no thresholds, no formulas, no generation
  rules, no schemas / data shapes, no decision rules, no arrival rules, no evidence / confidence / classification /
  validation / pass-fail / survival / positive-structure fields, no screen / runtime / memory paths, no classifier /
  neural work, no real clips, no vision or readiness claims; defines NO RECOGNITION RULE for control-collapse; adds no
  §0 pointer and no tags; states that any next path requires separate operator approval and separate review;
- grounds itself in v2.38, v2.39, the SAYABLE-vs-REACHABLE distinction, and the warning that control-collapse must not
  become merely decorative language;
- poses the central scan question verbatim ("Which boundary approach best preserves control-collapse as a genuinely
  reachable unresolved endpoint before any future fixture design is allowed?");
- compares the five candidates (A explicit collapse endpoint boundary; B anti-inevitability boundary; C
  control-honesty boundary; D no-recognition-rule boundary; E hold / redirect) across the six required dimensions
  (reachability preservation; risk of hidden decision semantics; risk of accidental validation language; risk of
  making candidate survival inevitable; risk of making control-collapse decorative only; compatibility with null-first
  adversarial framing), QUALITATIVELY and with NO numeric scoring;
- states the honest ceiling (a docs-only boundary can close the known doors to UNREACHABILITY but cannot certify
  REACHABILITY) and names the residual DECORATIVE-ENDPOINT HOLE that B + C does not close, without declaring it
  closed;
- recommends PRIMARY = B + C (with D as a standing rider, already in force, and A as wording only) and FALLBACK = E
  (hold / redirect to the broader falsification search) if B + C cannot be kept non-authorizing;
- fixes the allowed language (control-collapse remains reachable; candidate survival must not be structurally
  inevitable; future controls may fail to distinguish adversarial families; control failure remains an honest
  unresolved endpoint; no recognition rule is defined; no validation follows) and the forbidden language as claim
  SHAPES (control-collapse detected; control-collapse ruled out; controls passed; candidate survived; structure
  detected; null rejected; artifact ruled out; proxy ruled out; confound controlled; descriptor validated; geometry
  validated; metric validated; screen ready; runtime ready; memory ready; vision achieved; Brainvision sees -- plus
  paraphrases, including that "control-collapse did not occur" is itself forbidden);
- recommends exactly ONE separately gated docs-only next slice (v2.41 anti-inevitability / control-honesty boundary
  plan) ONLY if B + C is safe, requires that v2.41 design no fixtures, tests, metrics, or recognition rules and be
  willing to conclude that B + C cannot be stated without a criterion, and otherwise recommends HOLD / redirect;
- preserves the locks and verdict (Section 13), including control_collapse_reachability_validated = False and
  verdict = HOLD; HOLD/HELD read as held for analysis, not abandoned.

Flag any fixture / test / artifact / data / metric / descriptor / coordinate / threshold / formula / generation rule /
schema / decision rule / validation criterion defined anywhere; any recognition rule for collapse; any numeric scoring
of the candidates; any boundary ADOPTED rather than recommended; any claim that reachability is preserved, certified,
or validated; any declaration that the decorative-endpoint hole is closed; any treatment of "no collapse occurred" as
evidence; any treatment of collapse as a bug, failure, noise, or operator error; any claim that anything was detected,
ruled out, controlled, survived, validated, or seen; or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
All claim locks False — including `control_collapse_ruled_out`, `control_collapse_detected`, and
`control_collapse_reachability_validated` — and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Control-Collapse Boundary Scan v2.40. Docs-only boundary scan over the accepted v2.39 edge.
Opens no implementation lane, no tests, no artifact, no fixture design, and no data; adopts no descriptor / coordinate
/ metric / score / threshold / formula / generation rule / schema / data shape / decision rule / arrival rule /
pass-fail gate / validation; defines NO recognition rule for control-collapse; opens no classifier / neural / screen /
real-clip / runtime / memory path; makes no vision or readiness claim; adopts no boundary, authorizes nothing, and is
not self-authorizing. Compares five docs-only boundary approaches for preserving control-collapse reachability before
any future fixture design (A explicit collapse endpoint — the decorative-language trap in boundary form; B
anti-inevitability — the strongest single approach, attacking survival-as-only-exit; C control-honesty — the necessary
complement, keeping the collapse path from being engineered away as a bug; D no-recognition-rule — already in force, a
standing rider rather than a choice; E hold / redirect — legitimate and not a defeat) across six qualitative dimensions
with no numeric scoring; states the honest ceiling that a document can close the known doors to UNREACHABILITY but can
never certify REACHABILITY, which only a concrete design could show; names and refuses to paper over the residual
DECORATIVE-ENDPOINT HOLE (endpoints nominally present but structurally unarrivable) that B + C does not close, noting
that closing it would require a criterion, and a criterion is a metric — in which case v2.39's central question is
answered in the NEGATIVE and must be said plainly; recommends B + C together as primary and E as fallback; recommends
one separately gated docs-only next slice (v2.41 anti-inevitability / control-honesty boundary plan) only if B + C is
safe; keeps prior BY / color / chroma work FROZEN EVIDENCE, the BY/chroma scaffold REPORTING LANGUAGE ONLY, the
null-first role scaffold PAUSED HELD as complete vocabulary, S3 BINDING AND UNDISCHARGED, and the v2.22 question
UNRESOLVED and possibly unanswerable; preserves all claim locks and the frozen verdict HOLD; outcome label
BRAINVISION_CONTROL_COLLAPSE_BOUNDARY_SCAN_ONLY; no `§0` pointer added; no tags.*
