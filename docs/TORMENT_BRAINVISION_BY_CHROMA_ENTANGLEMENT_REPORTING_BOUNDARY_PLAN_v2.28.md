# TORMENT Brainvision BY/Chroma Entanglement-Aware Reporting-Boundary Plan v2.28

## 1. Status / Scope

**DOCS-ONLY reporting-boundary PLAN.** This is a plan note only. It opens **no** code, **no** tests, **no** runtime,
and **no** integration lane; it authorizes **no** implementation, and it is not corrective. It sits over the accepted
v2.27 edge (`f0e8177 docs(research): synthesize by chroma symbolic role boundary`) and changes none of the accepted
files.

**v2.28 plans a REPORTING BOUNDARY, not a measurement.** It asks how BY/chroma residual behavior could ever be reported
so that **entanglement survives as a first-class non-claim outcome** instead of being crushed into a BY-vs-generic-chroma
bucket. It defines conceptual reporting outcomes and the language that may and may not be used around them. It defines
no fixtures, no data, and no way of deciding which outcome applies to anything — because deciding that would be
measurement, and v2.28 measures nothing.

**v2.28 authorizes nothing.** It introduces and authorizes **no** implementation, tests, concrete fixtures, fixture
data, arrays, images, descriptor, coordinate system, numeric geometry, metric, equation, threshold, scoring, pass/fail
gate, validation, closure, real clip, screen / camera / live / sensor / streaming path, runtime path, memory path,
prompt / context / action / render-body / autonomy contact, classifier (form B), or neural encoder (form C). It makes
**no** production vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, and **no**
descriptor-validity / geometry-validity / screen-readiness / memory-readiness / runtime-readiness /
integration-readiness claim. Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.
**HOLD / HELD means held for analysis and claim control — not abandoned.**

```text
flat_field_validated                        = False
role_validated                              = False
entanglement_resolved                       = False
by_residual_isolated                        = False
generic_chroma_proxy_ruled_out              = False
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
geometry_validity_claim_allowed             = False
screen_readiness_claim_allowed              = False
runtime_readiness_claim_allowed             = False
memory_readiness_claim_allowed              = False
integration_readiness_claim_allowed         = False
vision_claim_allowed                        = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Grounding

```text
v2.22  THE QUESTION (in force):
       "Can future synthetic design distinguish BY-axis residual behavior from generic chroma proxy effects without
        adopting metrics or closure claims?"
       And the mandatory constraint: "Residual localization must not imply descriptor validity."

v2.24  SIX SYMBOLIC ROLE FAMILIES (conceptual; no fixtures): A BY-dominant chroma residual; B generic chroma proxy;
       C matched non-BY chroma; D BY/CHROMA ENTANGLED; E fixture-family artifact; F null / reporting-boundary.
       Role D encodes that the two pressures MAY NOT BE SEPARABLE AT ALL.

v2.26  STATIC SYMBOLIC ROLE-REPORTING ARTIFACT ONLY (committed 35d3707): roles are GENERATED, not VALIDATED. It
       measured nothing, separated nothing, validated nothing, and produced no evidence about colour.

v2.27  SYNTHESIS (committed f0e8177): v2.26 is useful because it EXPOSED THE DECISION POINT. Role D is a CENTRAL
       WARNING and a POSSIBLE HONEST OUTCOME -- not noise, not failure, not success, not a defect. Concrete fixture
       implementation is NOT the next safe direction until the project can report entanglement without pretending
       separation.
```

## 3. Central Question

```text
"Can BY/chroma residual behavior be reported in a way that preserves entanglement as a first-class outcome, rather than
 forcing separation into BY vs generic chroma buckets?"
```

v2.28 does not answer this question. It plans the **boundary** inside which a future answer could be attempted without
the answer being manufactured by the vocabulary used to state it. The failure mode being guarded against is precise: a
reporting frame that can only emit "BY-dominant" or "generic proxy" will emit one of them **whatever is true**, and the
resulting separation will be a fact about the frame, not about colour.

## 4. Allowed Reporting Outcomes (conceptual categories only)

These are **things a future report may SAY**. They are not measured classes, not classifier labels, not fixture
classes, not metric bins, not validation groups, and not visual categories. Nothing here says how an outcome would ever
be arrived at — that is deliberately absent, because any such rule would be a metric.

```text
====================================================================================================================
OUTCOME                              WHAT IT WOULD MEAN (reporting only)
--------------------------------------------------------------------------------------------------------------------
BY-leaning unresolved                the report NAMES a BY-leaning reading as one it cannot exclude -- and does not
                                     claim it. "Leaning" is a REPORTING STANCE, not a degree, a weight, a score, a
                                     probability, a confidence, or a direction of any measured quantity. It is
                                     STILL UNRESOLVED; that word is part of the outcome, not a caveat on it.

generic-chroma-leaning unresolved    the report NAMES a generic-chroma-proxy reading as one it cannot exclude -- and
                                     does not claim it, and does not thereby weaken the standing presumption that an
                                     apparent residual IS a generic proxy effect until shown otherwise. STILL
                                     UNRESOLVED.

matched-non-BY unresolved            the report NAMES a non-BY chroma reading as one it cannot exclude, so that "BY"
                                     does not silently become a synonym for "any colour effect". No colour space, no
                                     channel, no axis. STILL UNRESOLVED.

entangled / inseparable              the report states that BY residual pressure and generic chroma proxy pressure
                                     CANNOT BE TOLD APART here -- and stops. This is a COMPLETE, TERMINAL, HONEST
                                     outcome. See Section 6.

fixture-artifact suspected           the report states that any apparent distinction may have been PRODUCED BY the way
                                     the cases were constructed. It suspects; it does not measure an artifact, does
                                     not control for one, and may never conclude "not an artifact".

null / reporting-boundary            the report states where reporting stops and validation would impermissibly begin.
                                     An ANTI-CLAIM SCAFFOLD (v2.12 N1-N6). Never a baseline, never a control that
                                     passed, never evidence.
====================================================================================================================
```

**Three properties this set must have, and which any future frame must preserve:**

```text
P1. NOT A PARTITION. These outcomes do not carve a space into disjoint bins, and are not required to be exhaustive or
    mutually exclusive. More than one may apply at once ("entangled / inseparable" AND "fixture-artifact suspected" is
    a coherent thing to report). A frame that forces exactly one outcome per case has become a bucket sorter.
P2. "ENTANGLED" IS NOT THE ELSE-BRANCH. It may not be defined as "whatever did not sort cleanly into BY-leaning or
    generic-chroma-leaning". It is a POSITIVE STATEMENT that the distinction could not be made -- reachable on its own
    terms, not as a leftover. A frame in which "entangled" is only reachable by elimination has already made
    separation the default and entanglement the failure.
P3. "UNRESOLVED" IS LOAD-BEARING. It is part of three outcome NAMES, not a hedge appended to them. "BY-leaning
    unresolved" may never be shortened, in any report, to "BY-leaning" -- and certainly never to "BY".
```

**Outcomes are not roles.** The v2.24 roles say what a conceptual CASE would be FOR. These outcomes say what a future
REPORT may SAY. They are different axes and must never be collapsed into a one-to-one mapping: the moment a case in
"role A" is expected to yield the "BY-leaning" outcome, the roles have become a sorting mechanism and the answer has
been assumed by the setup (v2.27 §6).

## 5. Mandatory Non-Claim Language

A future report **MAY** say — and may say nothing stronger:

```text
reported as BY-leaning unresolved
reported as generic-chroma-leaning unresolved
reported as matched-non-BY unresolved
reported as entangled / inseparable
reported as fixture-artifact suspected
reported as null / reporting-boundary
```

The form matters. **"reported as X"** is a statement about the REPORT. **"is X"** would be a statement about the WORLD,
and no work in this branch licenses one.

A future report **MUST NOT** say — in any wording, hedged or unhedged:

```text
BY residual isolated
generic chroma proxy ruled out
entanglement resolved
descriptor validated
geometry validated
visual structure detected
fixture passed
screen ready
runtime ready
memory ready
vision achieved
Brainvision sees
```

Nor any paraphrase of these. The forbidden list is a list of **claim SHAPES**, not of exact strings: "the proxy is
controlled", "the residual is distinct", "the null passed", "not an artifact", "we can now separate them", "this
confirms the descriptor" are all the same forbidden move under different words. A frame that avoids the listed phrases
while asserting their content has not complied with anything.

## 6. Role D Preserved As A First-Class Endpoint

```text
"entangled / inseparable" IS:
  - a COMPLETE reporting outcome; a report may terminate here and be finished, not deficient;
  - an HONEST statement that the distinction could not be drawn;
  - reachable ON ITS OWN TERMS, not by elimination (P2);
  - permanently available -- it may never be deprecated, retired, or made harder to reach than the other outcomes.

"entangled / inseparable" IS NOT:
  - a FAILURE bucket        (the work did not fail; the distinction did not appear)
  - a SUCCESS bucket        (nothing was discovered about colour; entanglement is not a finding about the world)
  - NOISE                   (not an error term, not variance, not something to be reduced away)
  - an IMPLEMENTATION DEFECT (not a sign the cases were sloppy and need tightening until they separate -- tightening
                              cases until they separate IS the manufacturing hazard, v2.24 Role E)
  - HIDDEN EVIDENCE FOR BY SPECIFICITY (it is not "BY is real but subtle"; it is not weak support for anything; it
                              supports NOTHING)
  - PROVISIONAL             (not a placeholder awaiting the real answer)

IT IS AN ALLOWED UNRESOLVED REPORTING ENDPOINT. If the honest answer is that BY residual and generic chroma proxy
cannot be told apart, the correct behavior of the project is to SAY SO AND STOP -- and that must remain the cheapest,
most available thing to say, never the most expensive.
```

The asymmetry is the whole point. In most designs, "we could not tell" is the outcome that costs the most to report and
gets rewritten until it goes away. Here it must cost the least.

## 7. What v2.28 Does NOT Authorize

```text
v2.28 authorizes NONE of the following, and nothing in it may be read as opening any of them:

  - concrete fixtures, fixture instances, fixture banks, generated stimuli, fixture data;
  - implementation of any kind; any code; any test;
  - data structures carrying values: arrays, vectors, matrices, images, pixel data;
  - descriptors, feature vectors (form B), neural encodings / embeddings (form C);
  - coordinates, coordinate systems, numeric geometry, positions, distances, angles, magnitudes, gradients;
  - metrics, scores, thresholds, weights, ratios, margins, equations, comparison functions, decision rules;
  - pass/fail gates, acceptance criteria, expected outputs, validation, closure;
  - screen / real-clip / camera / live / sensor / streaming paths; runtime paths; memory paths; torment_service/ touch;
  - prompt / context / action / render-body / autonomy contact;
  - any vision claim, any "Brainvision sees" claim, any readiness or capability claim.

In particular, v2.28 defines NO RULE for deciding which outcome applies to anything. That absence is deliberate and
load-bearing: a decision rule over these outcomes would be a metric wearing reporting language, and it is out of bounds
here.
```

## 8. Recommended Next Step (one; separately gated)

```text
RECOMMEND (primary, and the only recommended path):

  v2.29  STATIC ENTANGLEMENT-AWARE REPORTING SCHEMA PROPOSAL  (DOCS-ONLY)

  v2.29 MAY define a SYMBOLIC SCHEMA SHAPE for future reporting -- the static symbolic form a report could take, what
  fields it would carry as NAMES, how the six outcomes of Section 4 would sit inside it, how P1-P3 (not a partition;
  entangled is not the else-branch; unresolved is load-bearing) would be structurally guaranteed rather than merely
  promised, and which claim locks stay False.

  v2.29 MUST NOT:
    - implement the schema; write code; write tests;
    - define fixtures, data, arrays, images, descriptors, coordinates, metrics, scores, thresholds, formulas,
      pass/fail gates, decision rules, or expected outputs;
    - define how an outcome is ARRIVED AT (that is measurement, not schema);
    - make any validation, closure, readiness, or vision claim.

  v2.29 STAYS DOCS-ONLY unless separately reviewed and operator-approved otherwise. v2.28 does not open it: the
  operator chooses whether v2.29 opens at all, and any v2.29 must be separately bounded, Codex-reviewed, and
  operator-approved.

NOT RECOMMENDED (explicitly): concrete fixture implementation; descriptor / coordinate / numeric-geometry / metric /
threshold / scoring / pass-fail work; validation or closure work; screen / real-clip / runtime / memory work;
classifier (B) or neural (C) work; any vision work.
```

## 9. Forbidden Drift Register

```text
- "BY-leaning unresolved" becoming "BY-leaning", then "BY" -- the outcome name silently shedding "unresolved".
- "leaning" becoming a DEGREE, weight, score, confidence, probability, or measured direction.
- the six outcomes becoming CLASSIFIER LABELS, fixture classes, metric bins, validation groups, or visual categories.
- the six outcomes becoming a PARTITION (exactly one per case), or becoming EXHAUSTIVE by assumption.
- "entangled / inseparable" becoming the ELSE-BRANCH, a failure bucket, a success bucket, noise, a defect, or weak
  evidence for BY specificity.
- "fixture-artifact suspected" becoming "artifact controlled" or licensing a "not an artifact" conclusion.
- "null / reporting-boundary" becoming a baseline, a negative control, or a passed null.
- the v2.24 roles becoming a SORTING MECHANISM by being mapped one-to-one onto these outcomes.
- a reporting frame becoming a DECISION RULE by acquiring any way of choosing among outcomes.
- a plan becoming an AUTHORIZATION; a schema becoming an IMPLEMENTATION.
- residual localization becoming DESCRIPTOR VALIDITY; isolation becoming CLOSURE; falsification becoming VALIDATION.
```

## 10. Non-Claim Interpretation

```text
WHAT v2.28 MAY ESTABLISH (and only this):
  - a CONCEPTUAL OUTCOME VOCABULARY in which entanglement is first-class and unresolved is load-bearing;
  - the MANDATORY non-claim language (what a future report may and may not say);
  - the STANDING of "entangled / inseparable" as an allowed terminal endpoint;
  - a single gated, docs-only next path (v2.29).

WHAT IT DOES NOT ESTABLISH:
  not fixtures            not implementation        not a schema        not a descriptor / coordinate
  not a metric / score    not a decision rule       not validation      not closure
  not readiness           not vision                not that the residual IS distinguishable
  not that the residual IS indistinguishable        not that entanglement IS the answer

Naming an outcome vocabulary measures nothing. The v2.22 question REMAINS UNRESOLVED. v2.28 moves the programme forward
by making an honest unresolved answer SAYABLE -- not by loosening any boundary, and not by getting closer to a claim.
```

## 11. Verdict

```text
verdict                                      = HOLD
flat_field_validated                         = False
role_validated                               = False
entanglement_resolved                        = False
by_residual_isolated                         = False
generic_chroma_proxy_ruled_out               = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False
geometry_validity_claim_allowed              = False
screen_readiness_claim_allowed               = False
runtime_readiness_claim_allowed              = False
memory_readiness_claim_allowed               = False
integration_readiness_claim_allowed          = False
vision_claim_allowed                         = False

OUTCOME_LABEL: BRAINVISION_BY_CHROMA_ENTANGLEMENT_REPORTING_BOUNDARY_PLAN_ONLY
```

v2.28 is a docs-only reporting-boundary plan. It grounds itself in v2.22 (the question), v2.24 (six symbolic roles,
especially Role D), v2.26 (static symbolic role reporting; generated, not validated), and v2.27 (the exposed decision
point; Role D as central warning and possible honest outcome); poses the central question of whether BY/chroma residual
behavior can be reported while preserving entanglement as a first-class outcome; defines six conceptual reporting
outcomes (BY-leaning unresolved; generic-chroma-leaning unresolved; matched-non-BY unresolved; entangled / inseparable;
fixture-artifact suspected; null / reporting-boundary) as reporting categories only, never as measured classes,
classifier labels, fixture classes, metric bins, validation groups, or visual categories; fixes the mandatory non-claim
language (what may be said; what may never be said); preserves "entangled / inseparable" as a first-class, terminal,
non-deficient endpoint that is not a failure bucket, not a success bucket, not noise, not an implementation defect, and
not hidden evidence for BY specificity; authorizes no fixtures, implementation, metrics, scoring, thresholds,
validation, descriptors, coordinates, real clips, screen / runtime / memory paths, classifier / neural work, or vision
claims; defines no rule for deciding which outcome applies; and recommends a single separately gated docs-only next
slice (v2.29 static entanglement-aware reporting schema proposal). It is not self-authorizing. All claim locks and the
frozen verdict **HOLD** are preserved and unmoved.

## 12. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_CHROMA_ENTANGLEMENT_REPORTING_BOUNDARY_PLAN_v2.28.md
(new, docs-only, untracked; over the accepted v2.27 edge
 "f0e8177 docs(research): synthesize by chroma symbolic role boundary").

Verify that this plan:
- is docs-only and authorizes NOTHING (no code / tests / schema implementation; no torment_service/; no fixtures or
  fixture data; no arrays / images / pixels; no descriptors / coordinates / numeric geometry; no metrics / scores /
  thresholds / formulas / decision rules; no pass-fail gates; no validation / closure; no screen / real-clip / camera /
  live / sensor / streaming / runtime / memory paths; no classifier (form B) / neural (form C); no vision); adds no §0
  pointer and no tags;
- grounds itself in v2.22 (the question, and the descriptor-validity constraint), v2.24 (six symbolic role families,
  especially Role D BY/chroma entangled), v2.26 (static symbolic role-reporting artifact only; roles GENERATED, not
  VALIDATED), and v2.27 (v2.26 exposed the decision point; Role D is a central warning and a possible honest outcome);
- poses the central question verbatim: "Can BY/chroma residual behavior be reported in a way that preserves
  entanglement as a first-class outcome, rather than forcing separation into BY vs generic chroma buckets?";
- defines the allowed reporting outcomes as CONCEPTUAL CATEGORIES ONLY -- BY-leaning unresolved; generic-chroma-leaning
  unresolved; matched-non-BY unresolved; entangled / inseparable; fixture-artifact suspected; null /
  reporting-boundary -- and states they are NOT classifier labels, fixture classes, metrics, validation groups, or
  visual categories; and that they are not a partition, that "entangled" is not an else-branch, and that "unresolved"
  is part of the outcome name;
- fixes the mandatory non-claim language: reports MAY say "reported as <outcome>"; reports MUST NOT say "BY residual
  isolated", "generic chroma proxy ruled out", "entanglement resolved", "descriptor validated", "geometry validated",
  "visual structure detected", "fixture passed", "screen ready", "runtime ready", "memory ready", "vision achieved",
  "Brainvision sees", or any paraphrase of these claim shapes;
- preserves Role D as a FIRST-CLASS ENDPOINT: "entangled / inseparable" is not a failure bucket, not a success bucket,
  not noise, not an implementation defect, and not hidden evidence for BY specificity -- it is an allowed unresolved
  reporting endpoint that a report may terminate on without being deficient;
- states what v2.28 does NOT authorize (concrete fixtures, implementation, metrics, scoring, thresholds, validation,
  descriptors, coordinates, real clips, screen / runtime / memory paths, classifier / neural work, vision claims), and
  defines NO rule for deciding which outcome applies;
- recommends exactly ONE separately gated next slice -- a DOCS-ONLY "v2.29 static entanglement-aware reporting schema
  proposal" that may define a symbolic schema SHAPE but must not implement it -- and is NOT self-authorizing;
- preserves the locks and verdict (Section 11): flat_field_validated = False; role_validated = False;
  entanglement_resolved = False; by_residual_isolated = False; generic_chroma_proxy_ruled_out = False;
  first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed = False;
  screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False;
  memory_readiness_claim_allowed = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False;
  verdict = HOLD; interprets HOLD/HELD as held for analysis, not abandoned.

Flag any fixture / instance / bank / data structure / array / image / coordinate / descriptor / metric / score /
threshold / formula / decision rule / expected output / pass-fail criterion defined anywhere; any outcome treated as a
measured class, classifier label, or fixture class; any "leaning" used as a degree, weight, score, or confidence; any
outcome set treated as a partition or as exhaustive; any treatment of "entangled / inseparable" as failure, success,
noise, defect, else-branch, or weak evidence for BY; any one-to-one mapping of the v2.24 roles onto these outcomes; any
"unresolved" dropped from an outcome name; any implication that anything was isolated, ruled out, resolved, validated,
detected, or seen; any authorization of implementation; or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, `role_validated = False`, `entanglement_resolved = False`, `by_residual_isolated =
False`, `generic_chroma_proxy_ruled_out = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY/Chroma Entanglement-Aware Reporting-Boundary Plan v2.28. Docs-only reporting-boundary
plan over the accepted v2.27 edge. Opens no implementation lane, no tests, and no fixture generation; opens no
classifier / neural / screen / real-clip / runtime / memory work; adopts no descriptor / coordinate system / numeric
geometry / metric / equation / threshold / scoring / pass-fail rule; defines no fixture, data structure, array, image,
formula, numeric parameter, score, threshold, decision rule, or expected output; grounds itself in v2.22 / v2.24 /
v2.26 / v2.27; poses the central question of whether BY/chroma residual behavior can be reported while preserving
entanglement as a first-class outcome rather than forcing separation into BY vs generic chroma buckets; defines six
conceptual reporting outcomes (BY-leaning unresolved; generic-chroma-leaning unresolved; matched-non-BY unresolved;
entangled / inseparable; fixture-artifact suspected; null / reporting-boundary) as reporting language only; fixes the
mandatory non-claim language; preserves "entangled / inseparable" as a first-class, terminal, non-deficient unresolved
endpoint; defines no rule for deciding which outcome applies; recommends one separately gated docs-only next slice
(v2.29 static entanglement-aware reporting schema proposal, schema shape only, not implemented); keeps prior BY / color
/ chroma work FROZEN EVIDENCE, the flat opponent-field symbolic branch PAUSED HELD, and the v2.22 question UNRESOLVED
and possibly unanswerable; is not self-authorizing; preserves all claim locks and the frozen verdict HOLD; makes no
vision / "Brainvision sees" / descriptor-validity / geometry-validity / temporal-order / readiness claim; outcome label
BRAINVISION_BY_CHROMA_ENTANGLEMENT_REPORTING_BOUNDARY_PLAN_ONLY; no `§0` pointer added; no tags.*
