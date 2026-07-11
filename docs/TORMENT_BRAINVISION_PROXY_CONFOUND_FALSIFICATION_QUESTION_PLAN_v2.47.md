# TORMENT Brainvision Proxy / Confound Falsification Question Plan v2.47

## 1. Status / Scope

**DOCS-ONLY question PLAN.** This is a plan note only. It opens **no** code, **no** tests, **no** artifact, **no**
fixture design, **no** fixture data, **no** runtime, and **no** integration lane. **It proposes no implementation, no
new fixtures, no new metrics, no new descriptors, no new controls, and no artifact structures.** It sits over the
accepted v2.46 edge (`2e6769f docs(research): scan broader falsification directions`) and changes none of the accepted
files.

**v2.47 plans a question whose honest answer could be that there is nothing left to explain.** That is the point of it.
After twenty-odd slices of boundary language, the proxy / confound route is the first direction in a long while that
can return a result the project would not enjoy — and this plan is written to make that result *easier* to reach, not
harder.

**Explicitly authorized: nothing.**

```text
NO IMPLEMENTATION. NO ARTIFACT. NO FIXTURE DESIGN. NO NEW FIXTURES. NO TESTS. NO FIXTURE DATA. NO ARRAYS / IMAGES.
NO NEW DESCRIPTORS, COORDINATES, METRICS, SCORES, THRESHOLDS, FORMULAS, GENERATION RULES, SCHEMAS, DATA SHAPES,
  DECISION RULES, ARRIVAL RULES, PASS/FAIL GATES, CONTROLS, OR VALIDATION.
NO RECOGNITION RULE FOR CONTROL-COLLAPSE IS DEFINED OR AUTHORIZED.
NO CLASSIFIER (FORM B) / NEURAL (FORM C) WORK. NO SCREEN / REAL-CLIP / RUNTIME / MEMORY PATH.
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
geometry_validity_claim_allowed             = False      anti_inevitability_validated             = False
screen_readiness_claim_allowed              = False      control_honesty_validated                = False
runtime_readiness_claim_allowed             = False
memory_readiness_claim_allowed              = False
integration_readiness_claim_allowed         = False
vision_claim_allowed                        = False
verdict                                      = HOLD
```

## 2. Grounding

```text
v2.38       Null-first role scaffold PAUSED / HELD as completed vocabulary.
v2.39-v2.45 Control-collapse / anti-inevitability / control-honesty branch: CLOSED as NON-AUTHORIZING REVIEW WORK. It
            produced no evidence and could not have been wrong about anything.
v2.46       DIRECTION SCAN: PROXY / CONFOUND ROUTE selected as PRIMARY -- bounded to FROZEN-EVIDENCE REREADING, with
            "what survives the proxies?" FORBIDDEN as a framing, and with the standing trigger: if the question cannot
            be posed without new machinery, THAT IS THE FINDING and the honest response is a pause.

STILL LIVE, AND UNTOUCHED BY THIS PLAN:
    null remains live                     artifact remains live
    proxy / confound remains live         generic chroma proxy remains live
    BY residual remains UNRESOLVED        candidate structure NOT detected, NOT validated, NOT survived
    NO descriptor, geometry, metric, temporal, screen, runtime, memory, integration, or vision claim is allowed.
```

## 3. Central Question

```text
"Could apparent Brainvision structure in the frozen research record be explainable by generic proxy / confound routes,
 without needing to invent new structures, metrics, descriptors, fixtures, or positive-survival framing?"
```

## 4. Framing — What This Is Not, And What It Is

```text
THIS IS NOT ASKING:
    What survives proxy/confound pressure?          <- FORBIDDEN FRAMING (v2.46). Candidate-positive routing in a
                                                       proxy coat. Refused on sight, including if we propose it.
    How do we rule out proxies?                     <- proxy_ruled_out stays False. Ruling out is not the goal and is
                                                       not permitted.
    How do we prove candidate structure?            <- nothing here proves anything.
    Which metric detects real structure?            <- no metric is adopted, invented, or applied.
    What should be implemented next?                <- nothing.

IT IS ASKING:
    Where could proxy / confound explanations ALREADY account for the apparent-structure LANGUAGE in the frozen record?
    Where should the project be MOST SUSPICIOUS of generic chroma, intensity, roughness, spectral richness, motion,
    fixture artifact, role-language, or unresolved-entanglement explanations?

NOTE THE OBJECT OF THE QUESTION, BECAUSE IT IS EASY TO MISREAD: the target is the APPARENT STRUCTURE IN THE RECORD --
what the project has WRITTEN and CONCLUDED -- not structure in the world. This is an audit of our own claims-language
against the cheapest available explanations. It examines the frozen record; it does not examine colour.
```

## 5. Proxy / Confound Families (question targets only; not fixtures, not classes, not measured categories)

```text
====================================================================================================================
P1  GENERIC CHROMA PROXY
    Apparent BY/chroma structure may reflect GENERIC CHROMA HANDLING rather than a BY-specific residual.
    Suspicion: the entire BY line rests on a distinction the frozen evidence never established.
    generic_chroma_proxy_ruled_out = False. by_residual_isolated = False.

P2  INTENSITY / CONTRAST PROXY
    Apparent structure may reflect INTENSITY, CONTRAST, BRIGHTNESS, or LUMINANCE DISTRIBUTION rather than anything
    Brainvision-specific.
    Suspicion: the least glamorous explanation, and therefore the least examined.

P3  ROUGHNESS / SPECTRAL-RICHNESS PROXY
    Apparent structure may reflect ROUGHNESS, SPECTRAL RICHNESS, SPREAD, or FREQUENCY CONTENT.
    Suspicion: the frozen record already recorded roughness / continuity entanglement as an UNRESOLVED confound. This
    family is not hypothetical -- it is documented, and it was never dissolved.

P4  MOTION / TEMPORAL-DISCONTINUITY PROXY
    Apparent structure may reflect MOTION MAGNITUDE, DISCONTINUITY, CUTS, SHIFTS, or TEMPORAL ARTIFACTS rather than
    order-specific structure.
    Suspicion: temporal_claim_allowed = False for exactly this reason, and the prior order/recurrence work returned a
    NEGATIVE result on its own prerequisite. That negative result is the most honest thing in the record and should
    be read as pressure, not as a setback to be recovered from.

P5  FIXTURE / ARTIFACT PROXY
    Apparent structure may arise from FIXTURE CONSTRUCTION, SYMBOLIC ROLE DESIGN, SYNTHETIC CONSTRAINTS, or REPORTING
    SCAFFOLD CHOICES.
    Suspicion: matched-pair and movement-matched work already showed separations that tracked construction. artifact
    _ruled_out = False and may never be concluded.

P6  VOCABULARY / SCHEMA PROXY  -- THE REFLEXIVE ONE, AND THE MOST UNCOMFORTABLE
    Apparent structure may arise BECAUSE THE VOCABULARY MAKES UNRESOLVED STATES LOOK ORGANIZED.
    Suspicion: this programme has spent many slices building role vocabularies, reporting schemas, adversarial family
    names, and boundary language. All of it was careful. NONE of it examined anything. An unresolved state that has
    been given six named roles, a canonical schema, a checker, and a boundary review LOOKS more structured than an
    unresolved state that has not -- and it is not. This family points at v2.24-v2.45, which is to say at us.

P7  ENTANGLEMENT PROXY
    Apparent structure may reflect UNRESOLVED MIXED EFFECTS rather than isolated candidate structure.
    Suspicion: entanglement_resolved = False, and the frozen record repeatedly reached entanglement and stopped. That
    is the honest endpoint -- and an honest endpoint is not a residual waiting to be extracted.
====================================================================================================================

THESE ARE QUESTION TARGETS. They are not fixtures, not classes, not labels, not measured categories, and nothing is
sorted into them. No family is ruled out by naming it; naming a proxy neither controls it nor removes it (v2.34).
```

## 6. Review Questions (question wording only)

```text
Q-A  Which prior claims or branch summaries in the frozen record are most vulnerable to generic-proxy
     reinterpretation -- i.e. where would a hostile reader say "that is just chroma / intensity / roughness / motion"?

Q-B  Which unresolved locks are directly implicated by a proxy / confound rereading -- and which of them would the
     rereading leave exactly where it found them?

Q-C  Which branches produced VOCABULARY that may ORGANIZE uncertainty without REDUCING confounding? (P6. This question
     is asked of our own work first, not last.)

Q-D  Which apparent-"structure" descriptions in the record can be accounted for WITHOUT any Brainvision-specific
     assumption -- using only explanations that were already available and already recorded?

Q-E  Which proxy / confound routes should REMAIN LIVE before any future artifact or fixture is even considered -- and
     is there any route that a future design could not honestly claim to have addressed?

These are QUESTIONS. They are not criteria, not tests, not gates, not checks, and not a rubric. They are answered by
reading and judgment. Nothing is scored, nothing passes, and a rereading may honestly conclude that it cannot tell.
```

## 7. The Boundary On The Rereading (binding; carried from v2.46)

```text
ALLOWED      : reading what the FROZEN, UNRESOLVED record ALREADY REPORTS, and asking whether the proxy routes recorded
               there already suffice to account for the apparent-structure language.
NOT ALLOWED  : adopting, inventing, or applying ANY new metric, threshold, descriptor, coordinate, formula, control,
               comparison, or recognition rule in order to ask it. Re-reading what an old result reports is not
               adopting a metric. RE-COMPUTING ANYTHING IS.
NOT ALLOWED  : treating the frozen record as unfrozen, revisable, or re-runnable.
NOT ALLOWED  : concluding that any proxy is RULED OUT, CONTROLLED, or DISSOLVED. That direction is barred: the locks
               proxy_ruled_out, confound_controlled, generic_chroma_proxy_ruled_out, artifact_ruled_out and
               null_rejected all stay False, and a rereading cannot move them.
NOT ALLOWED  : rescuing a residual. If a proxy explanation suffices, the honest response is to say so.

PRE-STATED TRIGGER: IF THE QUESTION CANNOT BE POSED OR PURSUED WITHOUT NEW MACHINERY, THAT IS THE FINDING, and the
honest response is C (HOLD / pause) -- not the machinery.

PRE-STATED NEGATIVE ANSWER, ACCEPTED IN ADVANCE: if the rereading finds that the proxy / confound routes ALREADY
ACCOUNT for the apparent-structure language in the record, then THERE IS NOTHING LEFT OVER TO EXPLAIN, and the honest
consequence is that no fixture programme is warranted -- which argues for pausing or closing Brainvision synthetic
work, NOT for building something to look again. This plan does not predict that outcome, does not prefer it, and will
not treat it as a failure if it arrives.
```

## 8. Allowed Conclusion Types And Recommendation

```text
ALLOWED CONCLUSION TYPES:
  A. Safe to perform a docs-only frozen-evidence proxy / confound rereading scan.
  B. Safe to perform a docs-only artifact-route falsification question plan instead.
  C. Not safe to continue; HOLD / pause the Brainvision falsification branch.

PRIMARY:    A -- DOCS-ONLY FROZEN-EVIDENCE PROXY / CONFOUND REREADING SCAN, under the Section-7 boundary.
SECONDARY:  B -- ARTIFACT-ROUTE FALSIFICATION QUESTION PLAN (v2.46's secondary; natively self-suspicious, and it also
            requires no new machinery to be asked).
FALLBACK:   C -- HOLD / PAUSE. Correct and honest if the Section-7 trigger fires, and available at the operator's
            discretion at any time.

REASON: the proxy / confound families are not hypothetical. P3 (roughness / spectral) and P4 (motion / temporal) are
ALREADY RECORDED as unresolved confounds in the frozen material; P5 (fixture / artifact) already showed separations
that tracked construction; P1 (generic chroma) is the standing presumption the BY line never displaced. A rereading
does not need to invent anything to apply pressure -- the pressure is already written down, and the project has been
building vocabulary around it rather than reading it.

IF A IS SELECTED:

  v2.48  FROZEN-EVIDENCE PROXY / CONFOUND REREADING SCAN  (DOCS-ONLY)

  v2.48 MUST: reread EXISTING branch conclusions and frozen-evidence LANGUAGE only, under the Section-7 boundary, and
  report where proxy / confound explanations already suffice, where they do not, and where it cannot tell.

  v2.48 MUST NOT: define new data structures, fixtures, metrics, tests, descriptors, thresholds, coordinates,
  formulas, controls, recognition rules, implementation, or validation language; re-compute anything; rule any proxy
  out; or rescue any residual.

v2.47 opens nothing. The operator chooses. Pausing remains available and honest, including instead of v2.48.
```

## 9. Allowed And Forbidden Language

**Allowed** — and nothing stronger:

```text
null remains live
artifact remains live
proxy/confound remains live
generic chroma proxy remains live
BY residual remains unresolved
candidate survival must not be structurally inevitable
no recognition rule is defined
no validation follows
no artifact is authorized
no implementation is authorized
frozen evidence is reread only as suspicion pressure
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

Paraphrases are the same forbidden move. Standing and restated: **"what survives the proxies"** is forbidden as a
FRAMING, not merely as a claim; **"the proxies explain it, therefore the method works"** is forbidden (a proxy
explanation validates nothing); **"the proxy is addressed"** and **"the confound is handled"** are forbidden; and
**"the boundary work is done, so we may now build"** remains forbidden.

## 10. Forbidden Drift Register

```text
- the rereading being re-phrased as "WHAT SURVIVES THE PROXIES?" -- candidate-positive routing in a proxy coat.
- the rereading being used to RULE OUT, CONTROL, or DISSOLVE any proxy. It cannot. The locks stay False.
- RE-COMPUTING anything, or treating the frozen record as revisable or re-runnable.
- NEW metrics, thresholds, descriptors, coordinates, controls, or recognition rules being adopted "just to ask the
  question". If the question needs them, the answer is C.
- a residual being RESCUED -- an apparent structure defended after a proxy explanation was found sufficient.
- P6 (vocabulary / schema proxy) being quietly skipped because it implicates this programme's own output. It is the
  family most likely to be true and least likely to be examined, and it must be asked FIRST.
- a proxy explanation's INSUFFICIENCY being read as EVIDENCE FOR structure. "The proxies do not fully account for it"
  means the record is unresolved -- it does not mean something is there.
- Q-A..Q-E becoming criteria, tests, gates, checks, or a rubric.
- the pre-stated negative answer ("nothing left over to explain") being treated as a FAILURE rather than as a result.
- a PLAN becoming an AUTHORIZATION; v2.48 being treated as inevitable; continuing because continuing is what we have
  been doing.
```

## 11. Non-Claim Interpretation

```text
WHAT v2.47 MAY ESTABLISH (and only this):
  - a BOUNDED QUESTION about whether proxy / confound routes already account for the apparent-structure language in
    the frozen record;
  - seven proxy / confound FAMILIES as question targets -- including the reflexive one (P6), which implicates this
    programme's own vocabulary;
  - five REVIEW QUESTIONS, in question wording only;
  - the binding boundary on any rereading (no new machinery; no re-computation; no ruling-out; no rescuing), with a
    pre-stated trigger and a pre-stated, accepted NEGATIVE answer;
  - a RECOMMENDATION (A primary; B secondary; C fallback), and nothing more.

WHAT IT DOES NOT ESTABLISH:
  not a rereading performed   not fixtures / data     not a descriptor / coordinate / metric
  not a recognition rule      not validation          not closure      not readiness      not vision
  not that proxies CAN account for the record         not that they CANNOT
  not that anything survives anything                 not that anything was detected, ruled out, or seen
  not that BY residual exists                         not that it does not

Planning a question examines nothing. Every lock stays False. Frozen evidence is reread only as SUSPICION PRESSURE,
never as support. The v2.22 BY/chroma question remains UNRESOLVED and possibly unanswerable.
```

## 12. Verdict

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
anti_inevitability_validated                 = False
control_honesty_validated                    = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False
geometry_validity_claim_allowed              = False
screen_readiness_claim_allowed               = False
runtime_readiness_claim_allowed              = False
memory_readiness_claim_allowed               = False
integration_readiness_claim_allowed          = False
vision_claim_allowed                         = False

RECOMMENDATION: A primary (docs-only frozen-evidence rereading scan, under the Section-7 boundary); B secondary;
                C fallback
OUTCOME_LABEL: BRAINVISION_PROXY_CONFOUND_FALSIFICATION_QUESTION_PLAN_ONLY
```

v2.47 is a docs-only question plan. It grounds itself in v2.38, the v2.39–v2.45 branch (closed as non-authorizing
review work), and v2.46 (proxy / confound route selected as primary; bounded to frozen-evidence rereading; *"what
survives the proxies"* forbidden as a framing). It poses the central question — could apparent Brainvision structure in
the frozen record be explainable by generic proxy / confound routes, without inventing new structures, metrics,
descriptors, fixtures, or positive-survival framing — and states plainly what it is **not** asking. It names seven
proxy / confound families as **question targets only** (generic chroma; intensity / contrast; roughness / spectral
richness; motion / temporal discontinuity; fixture / artifact; **vocabulary / schema — the reflexive family, which
implicates this programme's own scaffolds**; and entanglement), five review questions in question wording only, and a
binding boundary on any rereading: **no new machinery, no re-computation, no ruling-out of any proxy, no rescuing of
any residual** — with a pre-stated trigger (if new machinery is needed, that is the finding, and the answer is a pause)
and a **pre-stated, accepted negative answer** (if the proxies already account for the record, there is nothing left
over to explain, and no fixture programme is warranted). It recommends **A** (docs-only frozen-evidence proxy /
confound rereading scan) as primary, **B** (artifact-route question plan) as secondary, and **C** (HOLD / pause) as
fallback, and suggests one separately gated docs-only successor (v2.48), which it does not open. All claim locks and
the frozen verdict **HOLD** are preserved and unmoved.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_PROXY_CONFOUND_FALSIFICATION_QUESTION_PLAN_v2.47.md
(new, docs-only, untracked; over the accepted v2.46 edge "2e6769f docs(research): scan broader falsification
directions").

Verify that this plan:
- is docs-only and authorizes NOTHING: no implementation, no artifact, no fixture design, no new fixtures, no tests,
  no fixture data, no arrays / images, no new descriptors, coordinates, metrics, scores, thresholds, formulas,
  generation rules, schemas / data shapes, decision rules, arrival rules, pass/fail gates, controls, or validation; NO
  RECOGNITION RULE; no screen / runtime / memory paths; no classifier / neural work; no real clips; no vision or
  readiness claims; adds no §0 pointer and no tags;
- grounds itself in v2.38, v2.39-v2.45, and v2.46 (proxy / confound route selected as PRIMARY; bounded to
  frozen-evidence rereading; "what survives the proxies" FORBIDDEN as a framing), and in the standing unresolved locks;
- poses the central question verbatim, and states plainly what it is NOT asking (what survives proxy/confound pressure;
  how do we rule out proxies; how do we prove candidate structure; which metric detects real structure; what should be
  implemented next);
- names the seven proxy / confound families as QUESTION TARGETS ONLY -- generic chroma; intensity / contrast;
  roughness / spectral richness; motion / temporal discontinuity; fixture / artifact; vocabulary / schema (apparent
  structure arising because vocabulary makes unresolved states look organized -- asked of this programme's own output);
  entanglement -- and states they are not fixtures, classes, labels, or measured categories;
- states the review questions in QUESTION WORDING ONLY (not criteria, tests, gates, or checks);
- states the binding boundary on any rereading (read what the frozen record already reports; adopt NO new metric /
  threshold / descriptor / coordinate / formula / control / comparison / recognition rule; RE-COMPUTE NOTHING; treat
  the record as frozen; rule NO proxy out; rescue NO residual), with the PRE-STATED TRIGGER (if new machinery is
  needed, that is the finding, and the answer is C) and the PRE-STATED, ACCEPTED NEGATIVE ANSWER (if the proxies
  already account for the record, there is nothing left over to explain, and no fixture programme is warranted);
- recommends A (docs-only frozen-evidence proxy / confound rereading scan) as primary, B (artifact-route falsification
  question plan) as secondary, and C (HOLD / pause) as fallback; and, if A is selected, recommends exactly ONE
  separately gated docs-only next slice (v2.48 frozen-evidence proxy/confound rereading scan) which must reread
  existing branch conclusions and frozen-evidence language only and must define no new data structures, fixtures,
  metrics, tests, descriptors, thresholds, recognition rules, implementation, or validation language;
- fixes the allowed language (null remains live; artifact remains live; proxy/confound remains live; generic chroma
  proxy remains live; BY residual remains unresolved; candidate survival must not be structurally inevitable; no
  recognition rule is defined; no validation follows; no artifact is authorized; no implementation is authorized;
  frozen evidence is reread only as suspicion pressure) and the forbidden language as claim SHAPES;
- preserves the locks and verdict (Section 12), including verdict = HOLD.

Flag any new fixture / test / artifact / data / metric / descriptor / coordinate / threshold / formula / control /
recognition rule / validation criterion defined anywhere; any re-computation or treatment of the frozen record as
revisable; any proxy treated as ruled out, controlled, or dissolved; any residual rescued; any "what survives the
proxies" framing; any proxy insufficiency read as evidence FOR structure; any review question converted into a
criterion, test, gate, or check; any skipping of the reflexive vocabulary/schema family; any treatment of the
pre-stated negative answer as a failure; any claim that anything was detected, ruled out, controlled, survived,
validated, or seen; or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
All claim locks False, and the frozen verdict **HOLD**, are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Proxy / Confound Falsification Question Plan v2.47. Docs-only question plan over the
accepted v2.46 edge. Opens no implementation lane, no tests, no artifact, no fixture design, and no data; adopts,
invents, and applies no new descriptor / coordinate / metric / score / threshold / formula / generation rule / schema /
data shape / decision rule / control / recognition rule / validation criterion; opens no classifier / neural / screen /
real-clip / runtime / memory path; makes no vision or readiness claim; authorizes nothing and is not self-authorizing.
Poses the bounded question of whether apparent Brainvision structure IN THE FROZEN RECORD could be explainable by
generic proxy / confound routes without inventing new structures, metrics, descriptors, fixtures, or positive-survival
framing; states what it is NOT asking (never "what survives the proxies", never "how do we rule out proxies", never
"how do we prove candidate structure", never "which metric detects structure", never "what should be implemented");
names seven proxy / confound families as QUESTION TARGETS ONLY (generic chroma; intensity / contrast; roughness /
spectral richness; motion / temporal discontinuity; fixture / artifact; VOCABULARY / SCHEMA — the reflexive family,
which implicates this programme's own role vocabularies, reporting schemas, and boundary language, and which must be
asked FIRST; and entanglement); states five review questions in question wording only; binds any rereading to the
frozen record with NO new machinery, NO re-computation, NO ruling-out of any proxy, and NO rescuing of any residual;
pre-states the trigger (if new machinery is needed, that is the finding, and the honest response is a pause) and
pre-states an ACCEPTED NEGATIVE ANSWER (if the proxies already account for the record, there is nothing left over to
explain, no fixture programme is warranted, and that is a result rather than a failure); recommends A (docs-only
frozen-evidence proxy / confound rereading scan) primary, B (artifact-route question plan) secondary, C (HOLD / pause)
fallback; suggests one docs-only successor label (v2.48 frozen-evidence proxy/confound rereading scan) and opens it
not. Keeps prior BY / color / chroma work FROZEN EVIDENCE, the BY/chroma scaffold REPORTING LANGUAGE ONLY, the
null-first role scaffold PAUSED HELD, the anti-inevitability branch CLOSED as non-authorizing review work, S3 BINDING
AND UNDISCHARGED, and the v2.22 question UNRESOLVED and possibly unanswerable; preserves all claim locks and the frozen
verdict HOLD; outcome label BRAINVISION_PROXY_CONFOUND_FALSIFICATION_QUESTION_PLAN_ONLY; no `§0` pointer added; no
tags.*
