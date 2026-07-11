# TORMENT Brainvision Null-First Adversarial Fixture-Family Proposal v2.35

## 1. Status / Scope

**DOCS-ONLY conceptual family-role PROPOSAL.** This is a proposal note only. It opens **no** code, **no** tests, **no**
fixtures, **no** data, **no** runtime, and **no** integration lane; it authorizes **no** implementation and is not
corrective. It sits over the accepted v2.34 edge (`424b5a8 docs(research): plan null-first adversarial fixture design`)
and changes none of the accepted files.

**v2.35 proposes SYMBOLIC FAMILY ROLES ONLY.** These are names for what a case would conceptually be FOR. They are
**not** concrete fixtures, **not** instances, **not** measured classes, **not** classifier labels, **not** validation
groups, and **not** pass/fail categories. No fixture instance, fixture design, generation rule, data shape, descriptor,
coordinate, metric, score, threshold, formula, decision rule, test, expected output, pass/fail criterion, validation
criterion, or implementation detail is defined anywhere in this document.

**Explicitly authorized: nothing.**

```text
NO IMPLEMENTATION, NO FIXTURES, NO INSTANCES, AND NO DATA ARE AUTHORIZED.
NO DESCRIPTORS, COORDINATES, METRICS, SCORES, THRESHOLDS, FORMULAS, DECISION RULES, PASS/FAIL GATES, OR VALIDATION.
NO CLASSIFIER (FORM B) OR NEURAL (FORM C) WORK. NO SCREEN / REAL-CLIP / RUNTIME / MEMORY PATH.
NO VISION CLAIM AND NO READINESS CLAIM.
ANY NEXT PATH REQUIRES SEPARATE OPERATOR APPROVAL AND SEPARATE CODEX REVIEW.
NO §0 POINTER; NO TAGS.
```

Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6. **HOLD / HELD means held for
analysis and claim control — not abandoned.**

```text
flat_field_validated                        = False      null_rejected                 = False
role_validated                              = False      artifact_ruled_out            = False
schema_validated                            = False      proxy_ruled_out               = False
entanglement_resolved                       = False      confound_controlled           = False
by_residual_isolated                        = False      control_collapse_ruled_out    = False
generic_chroma_proxy_ruled_out              = False      candidate_structure_validated = False
                                                         candidate_structure_survived  = False
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
v2.32  The BY/chroma entanglement schema branch is PAUSED / HELD as a COMPLETED NON-AUTHORIZING SCAFFOLD (0ea0485),
       available as REPORTING LANGUAGE ONLY. It answers nothing about colour.
v2.33  BROADER TARGET SCAN (bcd3404): selection criterion "what could this target FAIL at?"; null-first adversarial
       design recommended as primary; the NULL SINK named as its hazard.
v2.34  NULL-FIRST DESIGN PLAN (424b5a8): null / artifact / proxy / confound / unresolved outcomes are the ADVERSARIAL
       FLOOR -- first in order, first in standing, first in presumption -- NOT cleanup categories and NOT failure
       buckets. The adversary is fixed BEFORE any candidate and may never be weakened afterwards (S2). "The nulls
       behaved" is the FLOOR, not evidence. Structural conditions S1-S5 stand.
```

## 3. Central Question

```text
"Which null-first adversarial family roles should future synthetic design preserve before any candidate positive
 structure is allowed to become a question?"
```

## 4. Proposed Symbolic Family Roles (six; conceptual only)

Each role carries **only** conceptual / reporting fields: `role_id`, `role_label`, `conceptual_purpose`,
`adversarial_focus`, `safe_reporting_language`, `forbidden_interpretations`, `non_claim_constraints`. Nothing below is
a fixture, an instance, a rule, a datum, or a criterion.

```text
====================================================================================================================
role_id                  : A_null_no_structure_role
role_label               : null / no-structure role
conceptual_purpose       : represent the possibility that NO MEANINGFUL STRUCTURE IS PRESENT. A VALID ENDPOINT -- not a
                           failure bucket, not a control that must be beaten, not a nuisance to clear away.
adversarial_focus        : the baseline an apparent structure would have to be told apart from. It is the FLOOR, and
                           the floor is where the design starts, not where it fails.
safe_reporting_language  : "reported as null / no-structure"
forbidden_interpretations: must NOT be read as a control that passed; must NOT be read as a null that was rejected;
                           must NOT be read as a baseline that validates anything; must NOT be read as a failed run.
non_claim_constraints    : nothing is measured, compared, or scored here; "no structure" is a REPORTING STANCE, never
                           a measured absence; the standing presumption is that an apparent structure is nothing until
                           an account survives that says otherwise -- and no such account exists.

====================================================================================================================
role_id                  : B_fixture_artifact_role
role_label               : fixture-artifact role
conceptual_purpose       : represent the possibility that any apparent structure was CAUSED BY FIXTURE CONSTRUCTION --
                           produced by the way the cases were built rather than by anything they were built to show.
adversarial_focus        : the design's suspicion of ITSELF, made first-class and permanent.
safe_reporting_language  : "reported as fixture-artifact suspected"
forbidden_interpretations: must NOT be read as an artifact that was ruled out, controlled, or measured; must NOT be
                           read as a licence to conclude the ABSENCE of an artifact -- that conclusion may never be
                           drawn; must NOT be read as validating the families.
non_claim_constraints    : naming the suspicion establishes NOTHING; no artifact is measured and none is excluded; the
                           case family may never be declared free of artifacts.

====================================================================================================================
role_id                  : C_proxy_confound_role
role_label               : proxy-confound role
conceptual_purpose       : represent the possibility that any apparent structure was CAUSED BY A PROXY OR CONFOUND
                           rather than by the intended target.
adversarial_focus        : the confound classes carried forward as FROZEN UNRESOLVED evidence (spectrum, per-channel
                           spread, directional movement, roughness / continuity) -- named as adversaries, never as
                           solved problems.
safe_reporting_language  : "reported as proxy-confounded"
forbidden_interpretations: must NOT be read as a proxy that was ruled out; must NOT be read as a confound that was
                           controlled, handled, corrected, or solved; must NOT be read as a comparison that was run.
non_claim_constraints    : naming a confound neither controls it nor removes it; no proxy is measured; the presumption
                           that an apparent structure IS a proxy effect stands until a reporting-only account survives
                           that says otherwise, and none exists.

====================================================================================================================
role_id                  : D_entangled_unresolved_role
role_label               : entangled / unresolved role
conceptual_purpose       : represent INSEPARABLE or UNRESOLVED behaviour -- the case where the adversarial families and
                           any apparent structure CANNOT BE TOLD APART. A VALID, COMPLETE, TERMINAL ENDPOINT.
adversarial_focus        : the honest hard case, carried unbroken from v2.24 Role D and the v2.28 boundary: the
                           possibility that the question is UNANSWERABLE.
safe_reporting_language  : "reported as entangled / unresolved"
forbidden_interpretations: must NOT be read as NOISE; must NOT be read as HIDDEN EVIDENCE for any candidate structure;
                           must NOT be read as failure, success, an implementation defect, or an else-branch; must NOT
                           be read as a quantity, a degree of mixing, or a resolution state.
non_claim_constraints    : entanglement is a conceptual POSSIBILITY, never a measured quantity; reporting it asserts
                           nothing and supports nothing; it must never be harder or costlier to report than any other
                           outcome.

====================================================================================================================
role_id                  : E_control_collapse_role
role_label               : control-collapse role
conceptual_purpose       : represent the possibility that THE CONTROL DESIGN ITSELF COLLAPSES -- that the adversarial
                           families stop being distinguishable as roles at all, or become unable to be told apart from
                           anything else. REACHABLE AND HONEST, never treated as impossible.
adversarial_focus        : the design turning its suspicion on its OWN ADVERSARY. If the controls collapse, NOTHING the
                           design reports means anything -- INCLUDING ITS NULLS.
safe_reporting_language  : "reported as control-collapse"
forbidden_interpretations: must NOT be read as a bug to be fixed quietly; must NOT be read as an impossible or merely
                           theoretical case; must NOT be read as ruled out; must NOT be read as a reason to weaken,
                           retune, or narrow the adversary (v2.34 S2).
non_claim_constraints    : control_collapse_ruled_out stays False; a design that CANNOT report the collapse of its own
                           controls is not adversarial -- it is merely defended, and it must be refused.

====================================================================================================================
role_id                  : F_candidate_structure_survival_role
role_label               : candidate-structure-survival role
conceptual_purpose       : represent ONLY THE FUTURE QUESTION of whether some candidate structure would survive
                           adversarial framing. It holds a place for a QUESTION, never for a finding.
adversarial_focus        : the burden itself -- that any positive structure would have to survive A-C (and stand apart
                           from D) with the adversary FIXED IN ADVANCE and never weakened afterwards.
safe_reporting_language  : "candidate structure remains only a future question"
forbidden_interpretations: must NOT imply detection, validation, success, positive evidence, or that a candidate
                           survived; must NOT be read as an EXPECTATION or a slot that ought to be filled; must NOT be
                           read as the ELSE-BRANCH of A-E; must NOT be read as the goal of the design.
non_claim_constraints    : candidate_structure_survived = False; candidate_structure_validated = False; this role names
                           a burden, not a hypothesis anyone is entitled to; its emptiness is not a shortfall.
====================================================================================================================
```

## 5. Structural Properties The Role Set Must Keep

```text
P1. NOT A PARTITION, NOT EXHAUSTIVE. The six roles do not carve the space into disjoint bins and are not required to
    cover it. More than one may stand at once (B and C and D together is coherent). A design that forces exactly one
    role per case has become a sorter, and the sorting would be its own result (v2.27 §6).
P2. F IS NOT THE ELSE-BRANCH. Candidate survival may never be DEFINED as "whatever A-E did not absorb". If F is
    reachable only by elimination, then A-E are exhaustive by construction, survival is impossible by construction,
    and the design is a NULL SINK (v2.33 / v2.34 S3).
P3. D IS NOT A LEFTOVER EITHER. "Entangled / unresolved" must be reachable on its own terms, not as the residue of a
    failed sort.
P4. E MUST STAY REACHABLE. If control-collapse cannot occur, the adversary cannot lose its own case, and the design
    can only ever confirm that its controls worked -- the null sink in a different coat.
P5. NO ROLE IS A SORTING MECHANISM. A role says what a case would be FOR. It is not an expectation about what such a
    case would REPORT. The moment cases built "for role C" are expected to report proxy-confounded, the answer has been
    assumed in the setup.
```

## 6. Cross-Family Risk Review

Roles can each stay disciplined and still combine into an implied capability. The dangerous readings, each refused:

```text
- A + B + C  -> reads as "WE CONTROLLED FOR EVERYTHING" (null + artifact + proxy = a completed control apparatus).
                REFUSE: naming three adversaries controls nothing, measures nothing, and excludes nothing. The locks
                null_rejected / artifact_ruled_out / proxy_ruled_out / confound_controlled all stay False.
- A-C behaving -> reads as EVIDENCE ("the adversary worked, so the method is sound"). REFUSE: the nulls behaving is the
                FLOOR (v2.34), not a finding. It means the design has not yet disqualified itself. Nothing more.
- D quietly   -> reads as NOISE or as HIDDEN SUPPORT for a candidate ("inseparable, but you can see something there").
                REFUSE: D supports NOTHING. It is a terminal endpoint, not a weak positive.
- E dropped   -> reads as a design that is DEFENDED rather than ADVERSARIAL. REFUSE: a design that cannot discover that
                its own controls are meaningless has exempted itself from its own scrutiny.
- F expected  -> reads as a HYPOTHESIS THE DESIGN IS ENTITLED TO ("we built the adversary, now let's find the
                structure"). REFUSE: F is a burden, not an expectation. Its emptiness is a legitimate permanent state.
- A-F complete-> reads as VALIDATION COVERAGE ("six roles cover the space, so the design is sound"). REFUSE: six ROLE
                NAMES cover nothing; the set is explicitly non-exhaustive (P1), and completeness is not soundness.
```

## 7. Allowed And Forbidden Language

**Allowed** — and nothing stronger:

```text
reported as null / no-structure
reported as fixture-artifact suspected
reported as proxy-confounded
reported as entangled / unresolved
reported as control-collapse
candidate structure remains only a future question
```

**Forbidden** — in any wording, as claim SHAPES rather than exact strings:

```text
structure detected        candidate survived      fixture passed          null rejected
artifact ruled out        proxy ruled out         confound controlled     control passed
descriptor validated      geometry validated      metric validated
screen ready              runtime ready           memory ready
vision achieved           Brainvision sees
```

Paraphrases are the same forbidden move: "the null didn't hold", "we handled the confound", "the artifact is
accounted for", "the controls checked out", "something real is there" are all barred by the same rule.

## 8. S3 (Pre-Stated Reachability) — Partially Discharged, And Honestly So

v2.34 S3 requires that, before adversarial families are designed, a slice must state what survival would look like and
show it is **not impossible by construction**. v2.35 discharges what it *can* discharge at the role level, and says
plainly what it **cannot**:

```text
DISCHARGED HERE (role-level reachability):
  - role F EXISTS as a first-class role, not as a residue (P2);
  - roles A-E are NOT exhaustive and NOT a partition, so they do not absorb the whole space by construction (P1);
  - role D is not a sink for everything that fails to sort (P3);
  - role E can fire against the adversary itself, so the adversary is not unconditionally privileged (P4).
  => Survival is NOT EXCLUDED BY THE ROLE SET. The null sink is not built into the vocabulary.

NOT DISCHARGED HERE, AND NOT DISCHARGEABLE HERE:
  - whether survival is reachable IN A CONCRETE DESIGN cannot be shown without describing how the families would ever
    be instantiated -- and instantiation is exactly what this document is forbidden to do, and rightly so.
  - therefore S3 REMAINS AN OPEN, BINDING OBLIGATION on the next slice that would move toward instantiation.

THIS IS NOT A LOOPHOLE. It is the honest boundary: a vocabulary can fail to exclude survival (which is what v2.35
shows); only a design can make survival REACHABLE (which no document has yet shown, and which none is authorized to
assume). Any future slice that designs or implements families and CANNOT state a reachable survival path must be
REFUSED as a null sink -- however conservative it looks. If that turns out to be impossible, saying so plainly is a
real finding, not a failure.
```

## 9. What v2.35 Does NOT Authorize

```text
NO implementation, code, or tests. NO fixtures, fixture instances, fixture banks, stimuli, generation rules, or DATA.
NO data shapes, arrays, vectors, images, or pixels. NO descriptors (form B); NO neural encodings (form C).
NO coordinates, coordinate systems, or numeric geometry. NO metrics, scores, thresholds, weights, formulas, equations,
comparison functions, or DECISION RULES. NO tests, expected outputs, pass/fail criteria, or validation criteria.
NO screen / real-clip / camera / live / sensor / streaming path; NO runtime path; NO memory path; NO torment_service/.
NO classifier or neural work. NO vision claim; NO "Brainvision sees" claim; NO readiness claim.

AND: v2.35 defines NO rule for deciding which role applies to anything. That absence is deliberate and load-bearing.
Any next path requires SEPARATE OPERATOR APPROVAL and SEPARATE CODEX REVIEW.
```

## 10. Recommended Next Slice (one; separately gated)

```text
RECOMMEND (primary, and the only recommended path):

  v2.36  NULL-FIRST ADVERSARIAL FIXTURE IMPLEMENTATION-BOUNDARY REVIEW  (DOCS-ONLY)

  v2.36 would REVIEW -- and only review -- whether a TINY STATIC SYMBOLIC FAMILY-ROLE ARTIFACT may ever be implemented
  for these six roles, and under exactly what boundary: the allowed shape (a deterministic builder + a conservative
  canonical checker, on the accepted v2.26 / v2.31 pattern), the forbidden shape, and the mandatory guard conditions --
  including, at minimum: no input; no arrival rule; no assignment of roles to anything; P1-P5 held STRUCTURALLY;
  role F never an else-branch; role E reachable; closed lock groups; verdict HOLD; and a statement of how S3 would be
  discharged if instantiation were ever contemplated.

  v2.36 MUST NOT AUTHORIZE IMPLEMENTATION DIRECTLY. It is a GATE, not a green light, and it stays DOCS-ONLY unless
  separately reviewed and operator-approved otherwise. v2.35 does not open it.

NOT RECOMMENDED: designing or generating fixtures; any descriptor / coordinate / metric / threshold / formula /
decision-rule / pass-fail / validation work; any screen / real-clip / runtime / memory work; any classifier or neural
work; any vision work. The v2.33 fallback (cross-family synthetic falsification) and the v2.33 honest stop (pause the
Brainvision synthetic branch) both remain available to the operator at any time.
```

## 11. Forbidden Drift Register

```text
- the adversary being WEAKENED, retuned, narrowed, or excused after a candidate fails against it (v2.34 S2).
- "the nulls behaved" becoming EVIDENCE. It is the floor.
- A / B / C / D / E becoming CLEANUP CATEGORIES, obstacles, or nuisances to explain away, rather than valid endpoints.
- role F becoming an EXPECTATION, a goal, a slot to fill, or the ELSE-BRANCH of A-E (P2 -- the null sink).
- role D becoming noise, hidden evidence, failure, success, defect, or a leftover.
- role E being dropped, made unreachable, or treated as impossible -- leaving a design that is defended, not
  adversarial.
- the roles becoming CONCRETE FIXTURES, instances, measured classes, classifier labels, validation groups, or
  pass/fail categories.
- a role becoming a SORTING MECHANISM (cases built "for role C" expected to report proxy-confounded) (P5).
- the six roles becoming EXHAUSTIVE, a PARTITION, or a claim of VALIDATION COVERAGE (P1).
- S3 being treated as DISCHARGED by this document (Section 8) -- it is discharged only at the role level, and remains
  a binding obligation on any slice that moves toward instantiation.
- a proposal becoming an AUTHORIZATION; naming an adversary becoming defeating one.
```

## 12. Non-Claim Interpretation

```text
WHAT v2.35 MAY ESTABLISH (and only this):
  - a FINITE SET of six symbolic null-first adversarial family ROLES (A null / no-structure; B fixture-artifact;
    C proxy-confound; D entangled / unresolved; E control-collapse; F candidate-structure-survival);
  - the structural properties the set must keep (P1-P5) and the cross-family readings that must be refused;
  - the allowed and forbidden language;
  - a partial, honestly-bounded discharge of S3 (survival is not excluded BY THE VOCABULARY; reachability IN A DESIGN
    remains an open obligation);
  - one gated, docs-only next slice (v2.36).

WHAT IT DOES NOT ESTABLISH:
  not fixtures          not instances        not data            not a descriptor / coordinate
  not a metric / score  not a decision rule  not validation      not closure     not readiness    not vision
  not that any structure exists to be found
  not that candidate structure could survive           not that it could not
  not that these six roles are the right ones, complete, useful, or realizable

Naming six adversaries defeats none of them. Every lock stays False. Candidate structure remains ONLY A FUTURE
QUESTION, and the v2.22 BY/chroma question remains UNRESOLVED and possibly unanswerable.
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
candidate_structure_validated                = False
candidate_structure_survived                 = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False
geometry_validity_claim_allowed              = False
screen_readiness_claim_allowed               = False
runtime_readiness_claim_allowed              = False
memory_readiness_claim_allowed               = False
integration_readiness_claim_allowed          = False
vision_claim_allowed                         = False

OUTCOME_LABEL: BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_FAMILY_PROPOSAL_ONLY
```

v2.35 is a docs-only conceptual family-role proposal. It grounds itself in v2.32 (BY/chroma scaffold paused / HELD),
v2.33 (target scan; null-first primary; null sink named), and v2.34 (null / artifact / proxy / confound / unresolved
outcomes are the adversarial FLOOR, not cleanup categories). It proposes six finite symbolic family roles
(A_null_no_structure_role, B_fixture_artifact_role, C_proxy_confound_role, D_entangled_unresolved_role,
E_control_collapse_role, F_candidate_structure_survival_role), each with conceptual purpose, adversarial focus, safe
reporting language, forbidden interpretations, and non-claim constraints; fixes the structural properties (non-partition
and non-exhaustive; F is not the else-branch; D is not a leftover; E stays reachable; no role is a sorting mechanism);
reviews the cross-family risks; fixes the allowed and forbidden language; discharges S3 only at the ROLE level and
states plainly that reachability in a concrete design remains a binding open obligation; defines no fixture, instance,
data shape, descriptor, coordinate, metric, score, threshold, formula, decision rule, test, expected output, pass/fail
criterion, validation criterion, or implementation detail; and recommends one separately gated docs-only next slice
(v2.36 null-first adversarial fixture implementation-boundary review), which must not authorize implementation
directly. It is not self-authorizing. All claim locks and the frozen verdict **HOLD** are preserved and unmoved.

## 14. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_FAMILY_PROPOSAL_v2.35.md
(new, docs-only, untracked; over the accepted v2.34 edge
 "424b5a8 docs(research): plan null-first adversarial fixture design").

Verify that this proposal:
- is docs-only and authorizes NOTHING: no implementation, no code, no tests, no fixtures, no instances, no fixture
  data, no generation rules, no data shapes, no arrays / images, no descriptors, no coordinates, no metrics, no
  scores, no thresholds, no formulas, no decision rules, no tests, no expected outputs, no pass/fail criteria, no
  validation criteria, no screen / runtime / memory paths, no classifier / neural work, no real clips, no vision or
  readiness claims; adds no §0 pointer and no tags; states that any next path requires separate operator approval and
  separate review;
- grounds itself in v2.32 (BY/chroma schema branch paused / HELD as a completed non-authorizing scaffold), v2.33
  (broader target scan), v2.34 (null-first plan), and the v2.34 principle that null / artifact / proxy / confound /
  unresolved outcomes are the ADVERSARIAL FLOOR, not cleanup categories;
- poses the central question verbatim ("Which null-first adversarial family roles should future synthetic design
  preserve before any candidate positive structure is allowed to become a question?");
- proposes the six finite symbolic family roles (A_null_no_structure_role; B_fixture_artifact_role;
  C_proxy_confound_role; D_entangled_unresolved_role; E_control_collapse_role;
  F_candidate_structure_survival_role) with ONLY conceptual / reporting fields (role_id, role_label,
  conceptual_purpose, adversarial_focus, safe_reporting_language, forbidden_interpretations, non_claim_constraints);
- gives each role its required meaning: A a valid endpoint and not a failure bucket; B apparent structure caused by
  fixture construction; C apparent structure caused by a proxy or confound; D inseparable / unresolved as a valid
  endpoint, never noise and never hidden evidence; E control-collapse REACHABLE and honest, never treated as
  impossible; F ONLY the future question of survival, implying no detection, validation, success, or positive
  evidence;
- keeps the role set non-partitioning and non-exhaustive, keeps F out of the else-branch position, keeps D from being
  a leftover, keeps E reachable, and forbids any role being used as a sorting mechanism;
- fixes the allowed language (reported as null / no-structure; reported as fixture-artifact suspected; reported as
  proxy-confounded; reported as entangled / unresolved; reported as control-collapse; candidate structure remains only
  a future question) and the forbidden language as claim SHAPES (structure detected; candidate survived; fixture
  passed; null rejected; artifact ruled out; proxy ruled out; confound controlled; control passed; descriptor
  validated; geometry validated; metric validated; screen ready; runtime ready; memory ready; vision achieved;
  Brainvision sees -- and all paraphrases);
- discharges v2.34's S3 ONLY at the role level (survival is not excluded by the vocabulary) and states plainly that
  reachability in a concrete design is NOT discharged here and remains a BINDING OBLIGATION on any slice moving toward
  instantiation, with any un-dischargeable design to be REFUSED as a null sink;
- recommends exactly ONE separately gated next slice -- a DOCS-ONLY "v2.36 null-first adversarial fixture
  implementation-boundary review" which reviews whether a tiny static symbolic family-role artifact may be implemented
  and MUST NOT authorize implementation directly -- and is NOT self-authorizing;
- preserves the locks and verdict (Section 13): flat_field_validated, role_validated, schema_validated,
  entanglement_resolved, by_residual_isolated, generic_chroma_proxy_ruled_out, null_rejected, artifact_ruled_out,
  proxy_ruled_out, confound_controlled, control_collapse_ruled_out, candidate_structure_validated,
  candidate_structure_survived, first_pass_structure_validity_claim_allowed, temporal_claim_allowed,
  descriptor_validity_claim_allowed, geometry_validity_claim_allowed, screen_readiness_claim_allowed,
  runtime_readiness_claim_allowed, memory_readiness_claim_allowed, integration_readiness_claim_allowed,
  vision_claim_allowed -- all False; verdict = HOLD; HOLD/HELD read as held for analysis, not abandoned.

Flag any fixture / instance / bank / generation rule / data shape / array / image / coordinate / descriptor / metric /
score / threshold / formula / decision rule / expected output / pass-fail or validation criterion defined anywhere; any
definition of what survival MEANS; any adversary that could be weakened or excused after a candidate fails; any
treatment of "the nulls behaved" as evidence; any null / artifact / proxy / confound / control-collapse endpoint
treated as an obstacle, nuisance, or failure bucket; any role F treated as an expectation, a goal, or an else-branch;
any role D treated as noise or hidden evidence; any role E dropped or made unreachable; any role used as a sorting
mechanism; any six-role completeness read as validation coverage; any claim that anything was detected, survived,
passed, rejected, ruled out, controlled, validated, or seen; any authorization of implementation; or any claim-lock /
verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
All claim locks False — including `null_rejected`, `artifact_ruled_out`, `proxy_ruled_out`, `confound_controlled`,
`control_collapse_ruled_out`, `candidate_structure_validated`, and `candidate_structure_survived` — and the frozen
verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Null-First Adversarial Fixture-Family Proposal v2.35. Docs-only conceptual family-role
proposal over the accepted v2.34 edge. Opens no implementation lane, no tests, no fixtures, no instances, and no data;
defines no fixture design, generation rule, data shape, descriptor, coordinate, metric, score, threshold, formula,
decision rule, test, expected output, pass/fail criterion, validation criterion, or implementation detail; opens no
classifier / neural / screen / real-clip / runtime / memory path; makes no vision or readiness claim; authorizes
nothing and is not self-authorizing. Proposes six finite symbolic null-first adversarial family ROLES (A null /
no-structure — a valid endpoint, not a failure bucket; B fixture-artifact; C proxy-confound; D entangled / unresolved —
never noise, never hidden evidence; E control-collapse — reachable and honest, so the design can discover that its own
controls are meaningless; F candidate-structure-survival — only a future question, implying no detection, validation,
success, or positive evidence), each with conceptual purpose, adversarial focus, safe reporting language, forbidden
interpretations, and non-claim constraints; fixes the structural properties (non-partition, non-exhaustive, F not the
else-branch, D not a leftover, E reachable, no role a sorting mechanism); reviews the cross-family risks (A+B+C as
"we controlled for everything"; nulls behaving as evidence; D as hidden support; E dropped; F as an entitlement; A-F as
validation coverage); fixes allowed and forbidden language as claim shapes; discharges v2.34 S3 only at the role level
and keeps reachability-in-a-design a binding open obligation, with any un-dischargeable design to be refused as a null
sink; recommends one separately gated docs-only next slice (v2.36 null-first adversarial fixture implementation-boundary
review, which must not authorize implementation directly); keeps the BY/chroma scaffold available as reporting language
only, prior BY / color / chroma work FROZEN EVIDENCE, the flat opponent-field symbolic branch PAUSED HELD, and the
v2.22 question UNRESOLVED and possibly unanswerable; preserves all claim locks and the frozen verdict HOLD; outcome
label BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_FAMILY_PROPOSAL_ONLY; no `§0` pointer added; no tags.*
