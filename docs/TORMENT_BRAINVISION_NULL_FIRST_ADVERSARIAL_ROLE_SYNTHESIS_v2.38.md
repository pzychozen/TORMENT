# TORMENT Brainvision Null-First Adversarial Role Scaffold Synthesis & Closure Decision v2.38

## 1. Status / Scope

**DOCS-ONLY synthesis and CLOSURE DECISION.** This is a synthesis note only. It opens **no** code, **no** tests, **no**
artifact, **no** fixtures, **no** data, **no** runtime, and **no** integration lane. It sits over the accepted v2.37
edge (`bfaa828 research(brainvision): add null-first adversarial role reporting`) and changes none of the accepted
files.

**This document closes a scaffold. It does not open the next one.** v2.37 was the third artifact of the same shape
(v2.26 roles → v2.31 schema → v2.37 roles). Each was safe, each was green, and none could have been wrong. That is the
signature of vocabulary work, and vocabulary work is now **done**. v2.38 hands the decision back and deliberately does
not schedule a v2.39.

**Explicitly authorized: nothing.**

```text
NO §0 POINTER IS AUTHORIZED.
NO IMPLEMENTATION IS AUTHORIZED.
NO FIXTURE DESIGN IS AUTHORIZED.
NO VALIDATION IS AUTHORIZED.
NO VISION CLAIM AND NO READINESS CLAIM IS AUTHORIZED.
ANY FUTURE CONTINUATION REQUIRES SEPARATE OPERATOR APPROVAL AND SEPARATE CODEX REVIEW.
```

No fixtures, fixture instances, fixture data, generation rules, schemas, data shapes, arrays, images, descriptors,
coordinates, metrics, scores, thresholds, formulas, decision rules, arrival rules, evidence / confidence /
classification / validation / pass-fail / survival / positive-structure fields, screen / runtime / memory paths,
classifier (form B) or neural (form C) work, real clips, or vision claims are introduced, opened, or brought nearer by
this note. Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

```text
flat_field_validated                        = False      null_rejected                 = False
role_validated                              = False      artifact_ruled_out            = False
schema_validated                            = False      proxy_ruled_out               = False
entanglement_resolved                       = False      confound_controlled           = False
by_residual_isolated                        = False      control_collapse_ruled_out    = False
generic_chroma_proxy_ruled_out              = False      control_collapse_detected     = False
                                                         candidate_structure_validated = False
first_pass_structure_validity_claim_allowed = False      candidate_structure_survived  = False
temporal_claim_allowed                      = False      candidate_structure_detected  = False
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

## 2. The Arc, v2.33 → v2.37

```text
v2.33  TARGET SCAN (bcd3404). Criterion adopted: WHAT COULD THIS TARGET FAIL AT? Null-first adversarial fixture design
       selected as the PRIMARY direction; the NULL SINK named as its hazard.
v2.34  NULL-FIRST PLAN (424b5a8). Null / artifact / proxy / confound / unresolved outcomes are the ADVERSARIAL FLOOR --
       first in order, first in standing, first in presumption. Adversary fixed BEFORE any candidate and never
       weakened (S2). "The nulls behaved" is the FLOOR, not evidence. S1-S5 fixed; S3 (a pre-stated, REACHABLE
       survival path) binding.
v2.35  SIX SYMBOLIC ADVERSARIAL ROLES (537ee8b): A null / no-structure; B fixture-artifact; C proxy-confound;
       D entangled / unresolved; E control-collapse; F candidate-structure-survival. S3 discharged only at the ROLE
       level; concrete reachability left as a BINDING OBLIGATION.
v2.36  IMPLEMENTATION-BOUNDARY REVIEW (582a972). Conditionally safe; W1-W4 fixed; role F kept (dropping it would make
       A-E exhaustive and recreate the null sink); SAFE separated from WORTH BUILDING.
v2.37  STATIC SYMBOLIC ROLE-REPORTING ARTIFACT (bfaa828). Zero-parameter builder; six roles as nouns; closed lock /
       flag / guard groups; 122 tests; role_validated = False; verdict HOLD. And, stated in its own findings:
       S3 ADVANCED BY EXACTLY NOTHING beyond symbolic vocabulary.
```

## 3. Conclusions

```text
C1. v2.37 SUCCEEDED at what it set out to do. It created a SAFE STATIC SYMBOLIC null-first role-reporting artifact:
    deterministic, offline, stdlib-only, no input, no generation, no assignment, no decision path, closed guard
    groups, and a conservative canonical checker that is green only for the canonical report.

C2. v2.37 CREATED NONE OF THE FOLLOWING, and opened no path to any of them: fixtures; fixture instances; fixture data;
    generation rules; schemas or data shapes; metrics; descriptors; coordinates; thresholds; formulas; decision rules;
    validation; classifier (form B) or neural (form C) paths; screen / runtime / memory paths; real clips; vision
    claims.

C3. v2.37 DID NOT TEST OR ESTABLISH CONTROL-COLLAPSE REACHABILITY. E_control_collapse_role remains reachable IN
    LANGUAGE ONLY. Control-collapse was not tested, not detected, not ruled out, not avoided, and not handled.
    control_collapse_ruled_out = False AND control_collapse_detected = False. Naming the way the controls could fail
    is not checking whether they did -- and no check exists.

C4. v2.37 DID NOT ESTABLISH CANDIDATE-STRUCTURE SURVIVAL. F_candidate_structure_survival_role remains ONLY A FUTURE
    QUESTION. Nothing survived, nothing was detected, nothing was validated, and nothing is expected.
    candidate_structure_survived / _detected / _validated all stay False.

C5. THE NULL-FIRST ROLE SCAFFOLD IS COMPLETE AS A NON-AUTHORIZING VOCABULARY LAYER -- unless the operator explicitly
    chooses a new falsification-facing target. The vocabulary layer was: name the adversaries, bound the language,
    review the boundary, freeze the nouns in code. All four are done. There is no fifth vocabulary step that would add
    anything.
```

## 4. What The Arc Bought — And What It Did Not

```text
BOUGHT:  six adversarial NOUNS, frozen canonically in code, so no later design can quietly redefine them;
         a null-first STANCE in which null / artifact / proxy / confound / unresolved outcomes are valid endpoints
         rather than cleanup categories;
         an explicit refusal of the two symmetric traps (positive forcing; the null sink);
         a first-class place (E) for the design to discover that its own controls are meaningless -- IN LANGUAGE.

NOT BOUGHT:  one fixture. One datum. One test of anything.
             Any evidence that control-collapse can remain reachable once designs get concrete.
             Any evidence that candidate structure could survive -- or that it could not.
             Any movement on S3, the binding obligation the whole direction rests on.

The arc improved the VOCABULARY the project would use IF it ever ran a null-first study. It did not bring that study
one step closer to being runnable, and this document will not pretend otherwise.
```

## 5. The Real Pressure Point

This is the finding that should drive the next decision:

```text
THE STRONGEST UNRESOLVED OBLIGATION FROM v2.35-v2.37 IS NOT "BUILD MORE SYMBOLIC ROLE ARTIFACTS".

It is this: CAN CONTROL-COLLAPSE REMAIN GENUINELY REACHABLE ONCE FUTURE SYNTHETIC DESIGN BECOMES MORE CONCRETE?

Right now E is reachable because nothing is real. In a language-only artifact, every role is trivially "reachable" --
you can always write a noun. The moment a design becomes concrete, E has to be reachable IN THAT DESIGN: there must be
a way for the adversarial families to actually fail to be distinct, and for the design to say so about ITSELF.

IF CONTROL-COLLAPSE BECOMES IMPOSSIBLE OR MERELY DECORATIVE, THE NULL-FIRST FRAMING WEAKENS -- badly. A null-first
design whose controls cannot be discovered to be meaningless is not adversarial. It is DEFENDED: it can only ever
report that its adversary worked, which is the NULL SINK wearing the armour of rigour. The entire reason v2.33
preferred null-first over the alternatives was that it could come out WRONG. E is the mechanism by which it can come
out wrong ABOUT ITSELF. Lose E's reachability and the direction quietly loses the property that justified choosing it.

So the next real question is not about colour, and not about structure. It is about whether the adversary can be built
such that it remains capable of losing its own case.
```

## 6. Recommended Branch State

```text
PAUSE / HELD as a completed non-authorizing null-first adversarial role scaffold.

HELD in the ANALYSIS sense: held for analysis and future reference -- NOT abandoned, NOT failed, NOT deprecated. The
v2.34 stance, the v2.35 roles, and the v2.37 artifact stand, and remain the governing vocabulary for any future
null-first work. Nothing is discarded. The branch is simply not where the next real question gets asked.
```

## 7. Allowed Future Continuations (all separately gated; none opened here)

```text
====================================================================================================================
A -- CONTROL-COLLAPSE REACHABILITY QUESTION PLAN  (docs-only)  [RECOMMENDED]
  Asks: what would it MEAN for control-collapse to remain reachable in future synthetic designs -- without defining
        fixtures, tests, metrics, data shapes, or validation criteria?
  Could fail at: YES, and this is the point. A can conclude that control-collapse CANNOT remain reachable once design
        becomes concrete -- and that conclusion would falsify the null-first framing itself, which the project chose
        precisely because it could be wrong. A docs slice that can reach a negative result about its own direction is
        not scaffolding.
  CONDITION (mandatory, or A becomes the seventh vocabulary layer): A must state, IN ADVANCE, what would count as
        "control-collapse is NOT reachable", and must be genuinely willing to conclude it. If A can only produce
        conditions under which E remains nominally sayable, it has written more vocabulary and should be refused.

====================================================================================================================
B -- NULL-FIRST STATIC FIXTURE-BOUNDARY SCAN  (docs-only)
  Asks: can concrete fixture design EVER be introduced without smuggling in metrics, data shapes, or validation
        criteria?
  Assessment: this is the necessary eventual step -- and it is PREMATURE. B designs the adversary's body before the
        project knows whether the adversary can lose its own case. If A concludes that E cannot stay reachable, then
        every fixture B contemplates would be a defended fixture, and B would have spent its effort building the null
        sink carefully. A first, then B.

====================================================================================================================
C -- RETURN TO BROADER BRAINVISION FALSIFICATION SEARCH  (docs-only)  [FALLBACK]
  Asks: is there a target more directly falsification-facing than symbolic role scaffolds?
  Assessment: the right move IF control-collapse reachability turns out to be too vague to frame safely -- i.e. if A
        cannot state its own failure condition. Choosing C then is not a retreat; it is refusing to write a seventh
        vocabulary layer under a scientific-sounding name.

====================================================================================================================
D -- PAUSE BRAINVISION SYNTHETIC WORK
  Hold this branch and redirect to another TORMENT layer.
  Assessment: LEGITIMATE AND NOT A DEFEAT. If no concrete falsification-facing target is ready -- if A cannot state a
        failure condition and C cannot name a better target -- then stopping is the honest move, and a more honest one
        than manufacturing another docs slice to maintain motion. Brainvision has produced real frozen evidence and
        real boundary discipline. It does not owe anyone continuous output.
====================================================================================================================
```

## 8. Recommendation

```text
PRIMARY:  A -- CONTROL-COLLAPSE REACHABILITY QUESTION PLAN (docs-only)
FALLBACK: C -- RETURN TO BROADER BRAINVISION FALSIFICATION SEARCH, if control-collapse reachability remains too vague
          to frame safely.

REASON: the strongest unresolved obligation from v2.35-v2.37 is not "build more symbolic role artifacts". It is
whether control-collapse can remain genuinely reachable once future synthetic design becomes more concrete. If
control-collapse becomes impossible or merely decorative, the null-first adversarial framing WEAKENS -- because the
design can then only ever confirm its own adversary, which is the null sink. A goes straight at that, and it is the
only candidate that can produce a negative result about the direction the project has chosen.

THIS RECOMMENDATION IS NOT SELF-EXECUTING. v2.38 opens no v2.39, drafts no A plan, and schedules nothing. If the
operator chooses A, it must be separately bounded, Codex-reviewed, and operator-approved, and it must carry the
Section-7 condition: state the failure condition in advance, and be willing to conclude it.

D remains available and honest at any point, including immediately.
```

## 9. Forbidden Drift Register

```text
- E's LANGUAGE-ONLY reachability being read as REACHABILITY. In v2.37, E is reachable because nothing is real.
- "the artifact has a control-collapse role" becoming "the design has a control-collapse check".
- F's presence becoming an EXPECTATION that candidate structure will eventually be found.
- the six roles becoming fixture classes, measured classes, classifier labels, validation groups, pass/fail
  categories, or visual categories; or becoming a partition or an exhaustive taxonomy.
- v2.37's protocol greenness becoming scientific validity, control quality, detection, survival, or "the adversary is
  in place".
- "the nulls behaved" being asserted. No null has behaved; no null exists.
- "the scaffold is complete" becoming "the direction is validated". The direction is UNTESTED.
- PAUSE / HELD becoming ABANDONED, FAILED, or DEPRECATED.
- scaffolding momentum becoming implicit authorization ("five slices were approved, so the sixth is routine"). Each
  slice needs its own approval, and this one recommends a slice that can FAIL, not another that cannot.
- a synthesis becoming an AUTHORIZATION; a recommendation becoming a schedule.
```

## 10. Non-Claim Interpretation

```text
WHAT v2.38 MAY ESTABLISH (and only this):
  - a SYNTHESIS of what v2.33-v2.37 did and did not establish;
  - a BRANCH STATE: PAUSE / HELD as a completed non-authorizing null-first adversarial role scaffold;
  - the identification of CONTROL-COLLAPSE REACHABILITY as the real pressure point;
  - four separately gated continuation options, with an honest assessment of each;
  - a RECOMMENDATION (A primary, C fallback), which is a recommendation and nothing more.

WHAT IT DOES NOT ESTABLISH:
  not an implementation    not fixtures / data       not a descriptor / coordinate / metric
  not a decision rule      not validation            not closure       not readiness       not vision
  not that control-collapse IS reachable             not that it is NOT
  not that candidate structure could survive         not that it could not
  not that the null-first direction is right         not that it is wrong
  not authorization of anything

Six adversarial nouns test nothing. S3 remains binding and undischarged. The v2.22 BY/chroma question remains
UNRESOLVED and possibly unanswerable, and nothing in the null-first arc has touched it.
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
control_collapse_ruled_out                   = False
control_collapse_detected                    = False
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

BRANCH STATE: PAUSE / HELD as completed non-authorizing null-first adversarial role scaffold
OUTCOME_LABEL: BRAINVISION_NULL_FIRST_ADVERSARIAL_ROLE_SYNTHESIS_ONLY
```

v2.38 is a docs-only synthesis and closure decision. It states that v2.37 successfully created a safe static symbolic
null-first role-reporting artifact; that v2.37 created no fixtures, fixture instances, fixture data, generation rules,
schemas / data shapes, metrics, descriptors, coordinates, thresholds, formulas, decision rules, validation, classifier
/ neural paths, screen / runtime / memory paths, real clips, or vision claims; that v2.37 did **not** test or establish
control-collapse reachability (E remains reachable **in language only**); that v2.37 did **not** establish
candidate-structure survival (F remains **only a future question**); and that the null-first role scaffold is complete
as a non-authorizing vocabulary layer unless the operator explicitly chooses a new falsification-facing target. It sets
the branch state to **PAUSE / HELD** (analysis sense — held for analysis and future reference, not abandoned);
identifies **control-collapse reachability** as the real pressure point, because a null-first design whose controls
cannot be discovered to be meaningless is not adversarial but merely defended; lists four separately gated
continuations (A control-collapse reachability question plan; B null-first static fixture-boundary scan; C return to
broader falsification search; D pause Brainvision synthetic work); and recommends **A as primary** and **C as
fallback**. It authorizes no §0 pointer, no implementation, no fixture design, no validation, and no vision or
readiness claim; any continuation requires separate operator approval and separate review. All claim locks and the
frozen verdict **HOLD** are preserved and unmoved.

## 12. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_NULL_FIRST_ADVERSARIAL_ROLE_SYNTHESIS_v2.38.md
(new, docs-only, untracked; over the accepted v2.37 edge
 "bfaa828 research(brainvision): add null-first adversarial role reporting").

Verify that this synthesis:
- is docs-only and authorizes NOTHING: no §0 pointer, no implementation, no fixture design, no validation, no vision
  or readiness claim; no code, no tests, no artifact, no fixtures, no fixture data, no generation rules, no schemas /
  data shapes, no arrays / images, no descriptors, no coordinates, no metrics, no scores, no thresholds, no formulas,
  no decision rules, no arrival rules, no evidence / confidence / classification / validation / pass-fail / survival /
  positive-structure fields, no screen / runtime / memory paths, no classifier / neural work, no real clips; adds no
  tags; and states explicitly that any future continuation requires separate operator approval and separate review;
- grounds itself in v2.33 (target scan selecting null-first as primary), v2.34 (null-first design plan), v2.35 (six
  symbolic adversarial family roles), v2.36 (implementation-boundary review), v2.37 (static symbolic role-reporting
  artifact), and v2.37's finding that S3 advanced by exactly nothing beyond symbolic vocabulary;
- states the five required conclusions: (1) v2.37 successfully created a safe static symbolic null-first
  role-reporting artifact; (2) v2.37 created no fixtures / instances / data / generation rules / schemas / data shapes
  / metrics / descriptors / coordinates / thresholds / formulas / decision rules / validation / classifier-neural
  paths / screen-runtime-memory paths / real clips / vision claims; (3) v2.37 did NOT test or establish
  control-collapse reachability -- E remains reachable in LANGUAGE ONLY; (4) v2.37 did NOT establish
  candidate-structure survival -- F remains ONLY a future question; (5) the null-first role scaffold is complete as a
  non-authorizing vocabulary layer unless the operator explicitly chooses a new falsification-facing target;
- sets the branch state to PAUSE / HELD as a completed non-authorizing null-first adversarial role scaffold, using
  HELD in the analysis sense (held for analysis and future reference, not abandoned);
- identifies CONTROL-COLLAPSE REACHABILITY as the strongest unresolved obligation, and explains that if
  control-collapse becomes impossible or merely decorative, the null-first framing weakens (a design whose controls
  cannot be discovered to be meaningless is defended, not adversarial -- the null sink);
- lists the four separately gated continuations (A control-collapse reachability question plan; B null-first static
  fixture-boundary scan; C return to broader Brainvision falsification search; D pause Brainvision synthetic work),
  opens none of them, RECOMMENDS A as primary and C as fallback (if control-collapse reachability remains too vague to
  frame safely), and requires that any A state IN ADVANCE what would count as "control-collapse is NOT reachable";
- preserves the locks and verdict (Section 11): flat_field_validated, role_validated, schema_validated,
  entanglement_resolved, by_residual_isolated, generic_chroma_proxy_ruled_out, null_rejected, artifact_ruled_out,
  proxy_ruled_out, confound_controlled, control_collapse_ruled_out, control_collapse_detected,
  candidate_structure_validated, candidate_structure_survived, candidate_structure_detected,
  first_pass_structure_validity_claim_allowed, temporal_claim_allowed, descriptor_validity_claim_allowed,
  geometry_validity_claim_allowed, screen_readiness_claim_allowed, runtime_readiness_claim_allowed,
  memory_readiness_claim_allowed, integration_readiness_claim_allowed, vision_claim_allowed -- all False;
  verdict = HOLD; HOLD/HELD read as held for analysis, not abandoned.

Flag any implementation / artifact / fixture / data / code / test; any authorization or scheduling of a next slice;
any treatment of E's language-only reachability as actual reachability; any treatment of F as an expectation; any
treatment of the scaffold as evidence, as validation of the direction, or as progress on S3; any claim that anything
was tested, detected, ruled out, controlled, survived, validated, or seen; any §0 pointer; or any claim-lock / verdict
movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
All claim locks False — including `control_collapse_ruled_out`, `control_collapse_detected`,
`candidate_structure_validated`, `candidate_structure_survived`, and `candidate_structure_detected` — and the frozen
verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Null-First Adversarial Role Scaffold Synthesis & Closure Decision v2.38. Docs-only synthesis
and closure decision over the accepted v2.37 edge. Opens no implementation lane, no tests, no artifact, no fixtures,
and no data; opens no classifier / neural / screen / real-clip / runtime / memory work; adopts no descriptor /
coordinate / metric / score / threshold / formula / generation rule / schema / data shape / decision rule / arrival
rule / pass-fail gate / validation; authorizes no §0 pointer, no implementation, no fixture design, no validation, and
no vision or readiness claim. Synthesizes v2.33 through v2.37; concludes that v2.37 built a safe static symbolic
null-first role-reporting artifact and created no fixtures, data, metrics, descriptors, coordinates, thresholds,
formulas, decision rules, validation, classifier / neural paths, screen / runtime / memory paths, real clips, or vision
claims; that v2.37 did not test or establish control-collapse reachability (E remains reachable in LANGUAGE ONLY,
control_collapse_ruled_out = False and control_collapse_detected = False); that v2.37 did not establish
candidate-structure survival (F remains ONLY A FUTURE QUESTION); and that the null-first role scaffold is complete as a
non-authorizing vocabulary layer. Sets the branch state to PAUSE / HELD (analysis sense — held for analysis and future
reference, not abandoned); identifies CONTROL-COLLAPSE REACHABILITY as the real pressure point, since a design whose
controls cannot be discovered to be meaningless is defended rather than adversarial and collapses into the null sink;
lists four separately gated continuations (A control-collapse reachability question plan; B null-first static
fixture-boundary scan; C return to broader falsification search; D pause Brainvision synthetic work); recommends A as
primary with a mandatory pre-stated failure condition, and C as fallback; opens none of them and schedules no v2.39;
requires separate operator approval and separate review for any continuation; keeps prior BY / color / chroma work
FROZEN EVIDENCE, the BY/chroma scaffold REPORTING LANGUAGE ONLY, the flat opponent-field symbolic branch PAUSED HELD,
S3 BINDING AND UNDISCHARGED, and the v2.22 question UNRESOLVED and possibly unanswerable; preserves all claim locks and
the frozen verdict HOLD; outcome label BRAINVISION_NULL_FIRST_ADVERSARIAL_ROLE_SYNTHESIS_ONLY; no `§0` pointer added;
no tags.*
