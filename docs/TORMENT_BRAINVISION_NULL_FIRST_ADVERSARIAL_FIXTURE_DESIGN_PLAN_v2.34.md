# TORMENT Brainvision Null-First Adversarial Fixture Design Plan v2.34

## 1. Status / Scope

**DOCS-ONLY design-direction PLAN.** This is a plan note only. It opens **no** code, **no** tests, **no** fixtures,
**no** data, **no** runtime, and **no** integration lane. It sits over the accepted v2.33 edge (`bcd3404
docs(research): scan broader brainvision falsification targets`) and changes none of the accepted files.

**v2.34 plans a STANCE, not a study.** It sets out what it would mean to frame future synthetic design **null-first**:
artifact, proxy, confound, and unresolved outcomes are the PRIMARY adversarial baseline, and any later candidate
structure must survive **against** them. It names conceptual adversarial family ROLES. It designs no fixtures, defines
no data, and — deliberately — defines no way to decide whether anything survived.

**Explicitly authorized: nothing.**

```text
NO IMPLEMENTATION, NO FIXTURES, AND NO DATA ARE AUTHORIZED.
NO DESCRIPTORS, METRICS, SCORES, THRESHOLDS, FORMULAS, PASS/FAIL GATES, OR VALIDATION ARE AUTHORIZED.
NO CLASSIFIER (FORM B) OR NEURAL (FORM C) PATH IS AUTHORIZED.
NO SCREEN / CAMERA / LIVE / SENSOR / STREAMING / REAL-CLIP PATH, NO RUNTIME PATH, AND NO MEMORY PATH IS AUTHORIZED.
NO VISION CLAIM AND NO READINESS CLAIM IS AUTHORIZED.
ANY NEXT PATH REQUIRES SEPARATE OPERATOR APPROVAL AND SEPARATE CODEX REVIEW.
NO §0 POINTER; NO TAGS.
```

Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6. **HOLD / HELD means held for
analysis and claim control — not abandoned.**

```text
flat_field_validated                        = False
role_validated                              = False
schema_validated                            = False
entanglement_resolved                       = False
by_residual_isolated                        = False
generic_chroma_proxy_ruled_out              = False
null_rejected                               = False
artifact_ruled_out                          = False
proxy_ruled_out                             = False
confound_controlled                         = False
candidate_structure_validated               = False
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

## 2. Grounding

```text
v2.32  The BY/chroma entanglement schema branch is PAUSED / HELD as a COMPLETED NON-AUTHORIZING SCAFFOLD (0ea0485).
       It is sound, and it answers nothing about colour. It remains available as REPORTING LANGUAGE ONLY.

v2.33  BROADER TARGET SCAN (bcd3404). Selection criterion: WHAT COULD THIS TARGET FAIL AT? Recommended NULL-FIRST
       ADVERSARIAL FIXTURE DESIGN as primary, with CROSS-FAMILY SYNTHETIC FALSIFICATION as fallback -- and named the
       NULL SINK as the hazard that would make null-first work inert.

THE LESSON BEING ACTED ON: forcing positive separation creates conceptual traps. A design that must sort cases into
"BY-dominant" vs "generic proxy" will sort them WHATEVER IS TRUE, and the separation becomes a property of the design.
Null-first inverts the burden so that positive structure has no bucket waiting for it.
```

## 3. Central Question

```text
"Can future synthetic design be framed null-first, so that artifact/proxy/confound/unresolved outcomes are primary and
 any later positive structure must survive against them?"
```

v2.34 does not answer this. It plans the **stance** under which a future answer could be attempted without the answer
being handed to the design in advance — in either direction.

## 4. The Null-First Principle

```text
NULL, ARTIFACT, PROXY, AND CONFOUND OUTCOMES ARE NOT AFTERTHOUGHTS AND NOT FAILURE BUCKETS.
THEY ARE THE PRIMARY ADVERSARIAL BASELINE. THEY COME FIRST, IN EVERY SENSE:

  FIRST IN ORDER      -- the adversarial families are conceived, named, and fixed BEFORE any candidate structure is
                         entertained. Not alongside it. Before it.
  FIRST IN STANDING   -- "the outcome is a null / an artifact / a proxy / a confound / unresolved" is a COMPLETE,
                         TERMINAL, HONEST result. It is not a step on the way to a better result.
  FIRST IN PRESUMPTION-- an apparent structure IS an artifact, a proxy, or a confound until a reporting-only account
                         survives that says otherwise. There is no such account, and none is authorized here.

THE ASYMMETRY IS THE WHOLE DESIGN, AND IT MUST NOT BE SOFTENED:

  - the adversary is FIXED BEFORE the candidate. Once fixed, it may not be weakened, relaxed, retuned, narrowed, or
    "corrected" in the light of a candidate that failed against it. Adjusting the adversary after seeing the candidate
    is how a null-first design becomes a positive-forcing design wearing armour.
  - "the nulls behaved" IS NOT EVIDENCE. It is the FLOOR. A design whose nulls behave has not shown anything; it has
    merely not yet disqualified itself.
  - UNRESOLVED IS AN HONEST RESULT, always available, never deficient, and never more expensive to report than any
    other outcome.
  - candidate structure is a FUTURE QUESTION. It is not the goal of this plan, and its absence is not a shortfall.
```

## 5. Allowed Conceptual Adversarial Families (roles only)

Conceptual family ROLES — names for what a case would conceptually be FOR. **Not** concrete fixtures, **not** measured
classes, **not** classifier labels, **not** validation groups, **not** pass/fail categories. Nothing here is data, and
nothing here says how any of it would be decided.

```text
====================================================================================================================
null / no-structure role
    the case that is conceptually EMPTY of structure. Primary, not a control in the pass/fail sense. Its role is to
    be the thing an apparent structure must be told apart from -- and it never "passes" or "fails".

fixture-artifact role
    the case whose apparent structure was PRODUCED BY ITS OWN CONSTRUCTION. Permanent self-suspicion, first-class:
    the design must never be able to conclude the absence of an artifact.

proxy-confound role
    the case carrying generic confound character (the spectrum / spread / directional-movement / roughness classes
    inherited as FROZEN UNRESOLVED evidence). Naming a confound neither controls it nor removes it.

entangled / unresolved role
    the case in which the adversarial families and any apparent structure CANNOT BE TOLD APART. Carried over from
    v2.24 Role D and the v2.28 boundary: a first-class TERMINAL endpoint, never a leftover, never an else-branch.

control-collapse role
    the case in which THE ADVERSARY ITSELF FAILS -- the null, artifact, and proxy families do not behave as distinct
    conceptual roles at all, or behave indistinguishably from everything else. This is a role for the design turning
    its suspicion on ITSELF. If the controls collapse, the design is broken and NOTHING it reports means anything --
    including its nulls. This must be reportable, and it must be reachable.

candidate-structure-survival role
    the case in which some structure would have to survive against all of the above. It is named LAST, deliberately.
    CANDIDATE STRUCTURE REMAINS ONLY A FUTURE QUESTION: this role holds a place for a question, not for a finding,
    and it carries no expectation that anything will ever occupy it.
====================================================================================================================
```

**Note on `control-collapse`.** It is the one family that can disqualify the whole design, and it is included on
purpose. A null-first design without it can only ever report that its adversary worked — which is the null sink in
disguise. A design must be able to discover that **its own controls are meaningless**, or it is not adversarial; it is
merely defended.

## 6. The Survival Path — Described, Not Defined

This is the sharpest constraint in the plan, and the easiest place to cheat.

```text
A future candidate structure would have to SURVIVE AGAINST the null, artifact, proxy, and confound families before any
positive claim could even be POSED. That is the shape of the burden.

v2.34 DOES NOT DEFINE WHAT SURVIVAL MEANS. It defines no metric, threshold, score, formula, pass/fail gate,
acceptance criterion, descriptor, coordinate, comparison, or validation criterion -- because any of those WOULD BE the
definition, and defining it here would hand the answer to a design that does not exist yet.

WHAT v2.34 CAN FIX -- and does -- ARE THE STRUCTURAL CONDITIONS ANY FUTURE SURVIVAL ACCOUNT MUST MEET:

  S1. ADVERSARY FIRST. The adversarial families are fixed before any candidate is entertained, and may never be
      weakened afterwards.
  S2. NO POST-HOC RESCUE. A candidate that does not survive may not be rescued by adjusting, narrowing, or excusing
      the adversary. The adversary is not the obstacle to explain away; it is the point.
  S3. REACHABILITY, PRE-STATED (the v2.33 guardrail, made binding). Before any adversarial family is designed in a
      later slice, that slice must STATE WHAT SURVIVAL WOULD LOOK LIKE and show it is NOT IMPOSSIBLE BY CONSTRUCTION.
      If no honest reviewer can describe a way for structure to survive, the design is a NULL SINK -- guaranteed to
      report "nothing survived" whatever is true -- and it must be REFUSED, however conservative it looks.
  S4. UNRESOLVED STAYS FREE. Reporting "unresolved / entangled" must never be harder, costlier, or more apologetic
      than reporting anything else.
  S5. THE ADVERSARY CAN LOSE ITS OWN CASE. control-collapse must be reachable (Section 5).

A design meeting S1-S5 has not shown anything. It has merely earned the right to ask the question.
```

**Allowed language** (and nothing stronger):

```text
candidate structure remains only a future question
survival must be adversarially constrained before any positive claim
null/artifact/proxy/confound outcomes remain valid endpoints
unresolved is an honest result
```

**Forbidden language** — in any wording, hedged or unhedged, and as claim SHAPES rather than exact strings:

```text
structure detected          fixture passed           null rejected
artifact ruled out          proxy ruled out          confound controlled
descriptor validated        geometry validated       metric validated
screen ready                runtime ready            memory ready
vision achieved             Brainvision sees
```

Paraphrases are the same forbidden move: "the null didn't hold", "we controlled for the artifact", "the confound is
handled", "structure emerged", "this confirms real structure" are all barred by the same rule.

## 7. What v2.34 Does NOT Authorize

```text
NO implementation. NO code. NO tests.
NO fixtures, fixture instances, fixture banks, stimuli, or fixture DATA of any kind.
NO arrays, vectors, matrices, images, or pixel data.
NO descriptors (form B feature vectors); NO neural encodings (form C).
NO coordinates, coordinate systems, numeric geometry, distances, angles, magnitudes, or gradients.
NO metrics, scores, thresholds, weights, ratios, formulas, equations, comparison functions, or decision rules.
NO pass/fail gates, acceptance criteria, expected outputs, validation, or closure.
NO screen / real-clip / camera / live / sensor / streaming path; NO runtime path; NO memory path; NO torment_service/.
NO classifier (form B) work; NO neural (form C) work.
NO vision claim; NO "Brainvision sees" claim; NO readiness or capability claim.

AND: v2.34 defines NO fixture, NO adversarial instance, and NO rule for deciding any outcome. It plans a STANCE.
Any next path requires SEPARATE OPERATOR APPROVAL and SEPARATE CODEX REVIEW.
```

## 8. Recommended Next Slice (one; separately gated)

```text
RECOMMEND (primary, and the only recommended path):

  v2.35  NULL-FIRST ADVERSARIAL FIXTURE FAMILY PROPOSAL  (DOCS-ONLY)

  v2.35 MAY: propose SYMBOLIC FAMILY NAMES and their boundaries -- what each adversarial family would conceptually be
  FOR, what it must never be read as, the safe reporting language for it, and the claim locks that stay False. It must
  ALSO discharge S3: state what survival would look like and show it is reachable. If it cannot, it should say so
  plainly -- and that would be a real finding, not a failure.

  v2.35 MUST NOT: design concrete fixtures; define fixture data, arrays, images, or instances; define descriptors,
  coordinates, metrics, scores, thresholds, formulas, decision rules, pass/fail gates, or validation criteria; open
  any screen / real-clip / runtime / memory / classifier / neural / vision path; or implement anything.

  v2.35 STAYS DOCS-ONLY unless separately reviewed and operator-approved otherwise. v2.34 does not open it. The
  operator chooses whether v2.35 opens at all, and any v2.35 must be separately bounded, Codex-reviewed, and
  operator-approved.

NOT RECOMMENDED: proceeding to fixture implementation; any descriptor / coordinate / metric / threshold / formula /
scoring / pass-fail / validation work; any screen / real-clip / runtime / memory work; any classifier or neural work;
any vision work. The v2.33 fallback (cross-family synthetic falsification) and the v2.33 honest stop (pause the
Brainvision synthetic branch) both remain available to the operator at any time.
```

## 9. Forbidden Drift Register

```text
- the adversary being WEAKENED, retuned, or narrowed after a candidate fails against it (S2). This is the central
  drift, and it would silently convert null-first into positive-forcing.
- "the nulls behaved" becoming EVIDENCE. Nulls behaving is the floor, not a finding.
- the null / artifact / proxy / confound families becoming OBSTACLES TO EXPLAIN AWAY rather than valid endpoints.
- "unresolved" becoming a failure bucket, an else-branch, noise, or a defect.
- the design becoming a NULL SINK -- survival impossible by construction, so "nothing survived" is guaranteed and
  evidence-free (S3).
- control-collapse being dropped, made unreachable, or read as a bug rather than as a first-class reportable outcome.
- candidate-structure-survival being treated as the GOAL, the EXPECTATION, or a slot that ought to be filled.
- conceptual family roles becoming concrete fixtures, measured classes, classifier labels, validation groups, or
  pass/fail categories.
- a family ROLE becoming a SORTING MECHANISM (cases built "for the proxy role" expected to report proxy) -- the
  v2.27 §6 drift, on a new axis.
- a plan becoming an AUTHORIZATION; a stance becoming a study; "adversarial" becoming a synonym for "rigorous enough
  to make a claim now".
```

## 10. Non-Claim Interpretation

```text
WHAT v2.34 MAY ESTABLISH (and only this):
  - a NULL-FIRST STANCE: artifact / proxy / confound / unresolved outcomes are primary and terminal;
  - six conceptual adversarial family ROLES, including control-collapse (the design may disqualify itself) and
    candidate-structure-survival (a placeholder for a future question, not a finding);
  - the STRUCTURAL CONDITIONS (S1-S5) any future survival account must meet, WITHOUT defining survival;
  - the allowed and forbidden language;
  - one gated, docs-only next slice (v2.35).

WHAT IT DOES NOT ESTABLISH:
  not fixtures        not data            not a descriptor / coordinate    not a metric / score / threshold
  not a decision rule not validation      not closure                      not readiness            not vision
  not that any structure exists to be found
  not that any structure could survive    not that none could
  not that the BY/chroma question is closed (it is UNRESOLVED, not closed)

Nothing here measures anything. Making the positive path HARDER is not the same as making progress on it -- it is the
precondition for progress being worth anything at all.
```

## 11. Verdict

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
candidate_structure_validated                = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False
geometry_validity_claim_allowed              = False
screen_readiness_claim_allowed               = False
runtime_readiness_claim_allowed              = False
memory_readiness_claim_allowed               = False
integration_readiness_claim_allowed          = False
vision_claim_allowed                         = False

OUTCOME_LABEL: BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_DESIGN_PLAN_ONLY
```

v2.34 is a docs-only design-direction plan. It grounds itself in v2.32 (BY/chroma schema branch paused / HELD as a
completed non-authorizing scaffold), v2.33 (target scan; null-first recommended as primary, cross-family as fallback,
null sink named as the hazard), and the BY/chroma lesson that forcing positive separation creates conceptual traps.
It poses the central question; states the null-first principle (null / artifact / proxy / confound outcomes are the
primary adversarial baseline — first in order, first in standing, first in presumption — and never failure buckets);
names six conceptual adversarial family roles (null / no-structure, fixture-artifact, proxy-confound, entangled /
unresolved, control-collapse, candidate-structure-survival) as roles only; describes the survival path **without
defining survival**, fixing instead five structural conditions (S1 adversary first; S2 no post-hoc rescue; S3
pre-stated reachability, refusing any null sink; S4 unresolved stays free; S5 the adversary can lose its own case);
fixes the allowed and forbidden language; authorizes no implementation, fixtures, data, descriptors, metrics,
thresholds, validation, classifier / neural paths, screen / runtime / memory paths, real clips, or vision claims; and
recommends one separately gated docs-only next slice (v2.35 null-first adversarial fixture family proposal, symbolic
names and boundaries only, no concrete fixtures, no implementation). It is not self-authorizing. All claim locks and
the frozen verdict **HOLD** are preserved and unmoved.

## 12. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_DESIGN_PLAN_v2.34.md
(new, docs-only, untracked; over the accepted v2.33 edge
 "bcd3404 docs(research): scan broader brainvision falsification targets").

Verify that this plan:
- is docs-only and authorizes NOTHING: no implementation, no code, no tests, no fixtures, no fixture data, no arrays /
  images, no descriptors, no coordinates, no metrics, no scores, no thresholds, no formulas, no decision rules, no
  pass/fail gates, no validation, no screen / runtime / memory paths, no classifier (form B) / neural (form C) work,
  no real clips, no vision or readiness claims; adds no §0 pointer and no tags; and states explicitly that any next
  path requires separate operator approval and separate review;
- grounds itself in v2.32 (BY/chroma schema branch paused / HELD as a completed non-authorizing scaffold), v2.33 (the
  target scan and its null-first-primary / cross-family-fallback recommendation, and the NULL SINK hazard), and the
  BY/chroma lesson that forcing positive separation creates conceptual traps;
- poses the central question verbatim ("Can future synthetic design be framed null-first, so that
  artifact/proxy/confound/unresolved outcomes are primary and any later positive structure must survive against
  them?");
- states the NULL-FIRST PRINCIPLE: null / artifact / confound outcomes are NOT afterthoughts and NOT failure buckets;
  they are the PRIMARY adversarial baseline (first in order, first in standing, first in presumption); the adversary is
  fixed BEFORE any candidate and may never be weakened afterwards; "the nulls behaved" is the FLOOR, not evidence;
  unresolved is an honest result;
- names the conceptual adversarial family ROLES ONLY (null / no-structure; fixture-artifact; proxy-confound; entangled
  / unresolved; control-collapse; candidate-structure-survival) and states they are not concrete fixtures, measured
  classes, classifier labels, validation groups, or pass/fail categories;
- DESCRIBES the survival path WITHOUT DEFINING IT -- no metric, threshold, score, formula, pass/fail gate, descriptor,
  coordinate, or validation criterion anywhere -- and instead fixes the structural conditions S1-S5, including the
  binding v2.33 guardrail (S3: a later slice must PRE-STATE what survival would look like and show it is not
  impossible by construction; a null sink must be REFUSED) and S5 (control-collapse must be reachable: the design must
  be able to discover that its own controls are meaningless);
- fixes the allowed language (candidate structure remains only a future question; survival must be adversarially
  constrained before any positive claim; null/artifact/proxy/confound outcomes remain valid endpoints; unresolved is
  an honest result) and the forbidden language as claim SHAPES (structure detected; fixture passed; null rejected;
  artifact ruled out; proxy ruled out; confound controlled; descriptor validated; geometry validated; metric
  validated; screen ready; runtime ready; memory ready; vision achieved; Brainvision sees -- and all paraphrases);
- recommends exactly ONE separately gated next slice -- a DOCS-ONLY "v2.35 null-first adversarial fixture family
  proposal" that may propose symbolic family names and boundaries but must NOT design concrete fixtures or implement
  anything -- and is NOT self-authorizing;
- preserves the locks and verdict (Section 11): flat_field_validated = False; role_validated = False;
  schema_validated = False; entanglement_resolved = False; by_residual_isolated = False;
  generic_chroma_proxy_ruled_out = False; null_rejected = False; artifact_ruled_out = False; proxy_ruled_out = False;
  confound_controlled = False; candidate_structure_validated = False;
  first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed = False;
  screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False;
  memory_readiness_claim_allowed = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False;
  verdict = HOLD; interprets HOLD/HELD as held for analysis, not abandoned.

Flag any fixture / instance / bank / data / array / image / coordinate / descriptor / metric / score / threshold /
formula / decision rule / pass-fail criterion / validation criterion defined anywhere; any definition of what survival
MEANS; any null-first design in which survival is impossible by construction; any adversary that could be weakened,
retuned, or excused after a candidate fails; any treatment of "the nulls behaved" as evidence; any treatment of null /
artifact / proxy / confound endpoints as obstacles to explain away; any collapse of "unresolved" into failure, noise,
else-branch, or defect; any dropping or softening of control-collapse; any family role used as a sorting mechanism; any
claim that anything was detected, passed, rejected, ruled out, controlled, validated, or seen; any authorization of
implementation; or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
All claim locks False — including `null_rejected = False`, `artifact_ruled_out = False`, `proxy_ruled_out = False`,
`confound_controlled = False`, and `candidate_structure_validated = False` — and the frozen verdict **HOLD** are
unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Null-First Adversarial Fixture Design Plan v2.34. Docs-only design-direction plan over the
accepted v2.33 edge. Opens no implementation lane, no tests, no fixtures, and no data; opens no descriptor /
coordinate / numeric geometry / metric / score / threshold / formula / decision rule / pass-fail gate / validation;
opens no classifier / neural / screen / real-clip / camera / live / sensor / streaming / runtime / memory path; makes
no vision or readiness claim; authorizes nothing and is not self-authorizing. Plans a NULL-FIRST stance in which
artifact, proxy, confound, and unresolved outcomes are the PRIMARY adversarial baseline — first in order, first in
standing, first in presumption — never afterthoughts and never failure buckets; fixes the adversary BEFORE any
candidate and forbids weakening it afterwards; states that "the nulls behaved" is the floor and not evidence; names six
conceptual adversarial family ROLES (null / no-structure, fixture-artifact, proxy-confound, entangled / unresolved,
control-collapse, candidate-structure-survival), including a role by which the design may disqualify ITSELF; describes
the survival path WITHOUT defining survival, fixing instead five structural conditions (adversary first; no post-hoc
rescue; pre-stated reachability, refusing any null sink; unresolved stays free; the adversary can lose its own case);
fixes allowed and forbidden language as claim shapes; keeps candidate structure as ONLY A FUTURE QUESTION; recommends
one separately gated docs-only next slice (v2.35 null-first adversarial fixture family proposal — symbolic family names
and boundaries only, no concrete fixtures, no implementation); keeps the BY/chroma scaffold available as reporting
language only, prior BY / color / chroma work FROZEN EVIDENCE, the flat opponent-field symbolic branch PAUSED HELD, and
the v2.22 question UNRESOLVED and possibly unanswerable; preserves all claim locks and the frozen verdict HOLD; outcome
label BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_DESIGN_PLAN_ONLY; no `§0` pointer added; no tags.*
