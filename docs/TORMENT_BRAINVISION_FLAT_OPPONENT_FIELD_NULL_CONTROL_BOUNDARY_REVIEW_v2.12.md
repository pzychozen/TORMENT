# TORMENT Brainvision Flat Opponent-Field Null/Control Boundary Review v2.12

## 1. Status / Scope

**DOCS-ONLY null/control interpretation boundary REVIEW.** This is a review note only. It opens **no** code, **no**
tests, **no** runtime, and **no** integration lane; it authorizes **no** implementation, **no** expansion, **no**
validation, and **no** readiness claim, and it is not corrective. It sits over the accepted v2.11 edge (`fc4209d`) and
changes none of the accepted files.

**v2.12 reviews null/control interpretation only.** After the v2.11 vocabulary drift audit flagged `null_control` and
`has_null_control_role` as terms needing discipline, this review locks down what the null/control vocabulary — the
label `null_control`, the relation `has_null_control_role`, and the family `F_null_control_fields` — is allowed to
mean and, more importantly, what it must never be read to mean. It reviews meaning; it changes no term, adds none, and
removes none.

**v2.12 authorizes no implementation, expansion, or readiness claim.** It introduces and authorizes **no** descriptor,
coordinate system, numeric geometry, metric, null/control metric, equation, threshold, control metric, pass/fail gate,
validation, closure, screen analysis, real clip, camera / live / sensor / streaming path, runtime path, memory path,
prompt / context / action / render-body / autonomy contact, classifier (form B), or neural encoder (form C). It makes
**no** production vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, and **no**
descriptor-validity / geometry-validity / screen-readiness / memory-readiness / runtime-readiness /
integration-readiness claim. Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per
v0.6. **HOLD / HELD means held for analysis and claim control — not abandoned.**

```text
flat_field_validated                        = False
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

## 2. Why Null/Control Drift Matters

"Control" is the single most dangerous word in the vocabulary, because in every research context it *means evidence*.
A control is normally the thing you compare against to prove a result — a negative control that stays flat while the
treatment moves, a baseline a metric is scored against, a falsification that would have fired if the effect were
spurious. The v2.9 artifact borrows the *word* `null_control` for a purely symbolic family role, but the default
scientific reading pulls hard toward "this is the control that validates the others."

That pull is the drift. If `F_null_control_fields` is quietly read as a negative control that "passed," then A–E are
silently treated as a positive result — and the whole HELD posture collapses into an implied validation nobody
authorized. The danger needs no code: it is enough for a reader or a later doc to say "the null control behaves as
expected" for the symbolic role to become a claim of evidence, geometry validity, or readiness. This review makes the
allowed meaning narrow and explicit, and forbids every evidentiary reading, so the null/control vocabulary can stay a
claim-discipline scaffold rather than a hidden proof.

## 3. Allowed Meaning

`null_control`, `has_null_control_role`, and `F_null_control_fields` are allowed to mean **only** the following, and
each is symbolic:

```text
- a SYMBOLIC FAMILY ROLE: F is named as the "null / control" role among the six families; a label, not a function.
- a PLACEHOLDER for non-authorizing contrast STRUCTURE: it marks "here is where a neutral / matched non-opponent
  counterpart would sit," conceptually, without any counterpart being built, measured, or compared.
- a BOUNDARY OBJECT used to PRESERVE CLAIM DISCIPLINE: it exists so the family set is not read as all-positive; its job
  is to keep the representation honest, not to adjudicate anything.
- a FIXTURE CATEGORY that remains UNVALIDATED: like A–E, F is a named symbolic object; it is not tested, scored, or
  shown to behave in any way.
```

In short: `null_control` names a role; `has_null_control_role` names that F plays it; `F_null_control_fields` is the
symbolic family carrying it. Nothing here computes, compares, decides, or proves.

## 4. Forbidden Interpretations

The null/control vocabulary must **never** be read as any of the following. Each is explicitly forbidden:

```text
- NOT a validation control (it validates nothing and nothing is validated against it);
- NOT a negative control RESULT (there is no result; nothing was run or measured);
- NOT a metric or baseline (it carries no number, no baseline value, no scale);
- NOT a pass/fail gate or criterion (it decides nothing; protocol_ok is boundary compliance, not a null "pass");
- NOT proof of geometry validity, descriptor validity, visual-structure validity, or screen readiness;
- NOT evidence of runtime readiness, memory readiness, or integration readiness;
- NOT falsification success (nothing was falsified; no test was capable of firing);
- NOT proof of null behavior (F is not shown to "stay flat" or behave nullishly -- it is only named);
- NOT proof that non-null families (A-E) are meaningful (F's presence grants A-E nothing).
```

## 5. Interaction Drift Risks

The null/control terms are safest alone; combined with structural terms they invite an evidentiary reading. The
dangerous combinations, each to be refused:

```text
- null_control + contrasts_with -> reads as a VALIDATION COMPARISON (F compared against A-E to prove a difference).
                                   Refuse: both are symbolic; "contrasts_with" names a difference, it measures none and
                                   compares nothing; F is not a yardstick.
- null_control + separates      -> reads as SEGMENTATION PROOF (a proven split with F marking the null side).
                                   Refuse: both symbolic; "separates" names a relation, proves no split, measures nothing.
- null_control + contains       -> reads as OBJECT/REGION ABSENCE PROOF (F "contains nothing", so absence is verified).
                                   Refuse: both symbolic; naming a containment relation verifies no presence or absence.
- null_control + boundary       -> reads as EDGE-CONTROL EVIDENCE (F used to calibrate or confirm a detected edge).
                                   Refuse: both symbolic; no edge is detected, located, calibrated, or confirmed.
- null_control + field          -> reads as a NUMERIC FIELD BASELINE (F as the zero/reference field a metric subtracts).
                                   Refuse: both symbolic; "field" holds no values; there is no baseline to subtract.
- null_control + region         -> reads as a SEGMENTATION BASELINE (F as the reference region for a segmentation score).
                                   Refuse: both symbolic; "region" is a named scope, not a measured or reference area.
```

## 6. Safe-Use Invariants

Invariant rules for the null/control vocabulary. Each is a **non-implication** that must hold regardless of any future
step:

```text
N1. null/control PRESENCE does NOT imply a control metric.
N2. symbolic CONTRAST does NOT imply measured contrast.
N3. absence-ROLE language does NOT imply verified absence.
N4. F-family PRESENCE does NOT validate A-E (or anything).
N5. null/control terms are ANTI-CLAIM SCAFFOLDS, not evidence.
N6. protocol_ok = True does NOT mean the null/control "passed" (it means the object is boundary-compliant, nothing more).
```

Any reading, doc, or artifact that violates an invariant above has left the accepted boundary and is inadmissible.

## 7. Expansion Recommendation

```text
Recommendation: REMAIN HELD.

The null/control vocabulary must NOT be expanded into a metric, a baseline, a comparison, or a validation control. It
stays a symbolic family role, a non-authorizing contrast placeholder, and a claim-discipline boundary object -- and
nothing more. Do NOT turn F into a measured or scored control, do NOT compare A-E against F, and do NOT read
protocol_ok as a null "pass". Any future control CONCEPT (a real null baseline, a negative control, a comparison) would
require a SEPARATE docs-first plan, a Codex review, and explicit operator approval that names the exact step, what it
must never become, and how every claim lock and the generated-vs-validated separation are preserved. No descriptor /
coordinate / metric / null-control-metric / validation / screen / real-clip / runtime / memory / classifier (B) /
neural (C) / vision work is recommended or authorized here. Held for analysis and claim control -- not abandoned.
```

## 8. Possible Next Slices

Docs-first candidates only; **none opened, none authorized, and none recommended for implementation here**. This
review recommends **no** direct descriptor, coordinate, metric, validation, screen, real-clip, runtime, memory,
neural, classifier, or vision work. Up to three possible docs-first directions the operator could choose from:

```text
A. v2.13 SYMBOLIC REPRESENTATION ADVERSARIAL MUTATION REVIEW (docs-only)
   Plan, on paper, an adversarial enumeration of how the v2.9 guarded object could be mutated or mis-read to leak a
   validation / descriptor / coordinate / vision claim past the conservative check_protocol, and what additional guard
   obligations (if any) a future artifact would need. Adopts nothing; builds nothing.

B. v2.13 A-F FAMILY IDENTITY PRESERVATION AUDIT (docs-only)
   Audit, on paper, how the canonical A-F identity/content enforcement keeps the six families exactly six and exactly
   themselves, and where identity drift could still slip in. Adopts nothing; changes no code.

C. v2.13 PROTOCOL GUARD SEMANTICS REVIEW (docs-only)
   Review, on paper, precisely what protocol_ok does and does not mean (boundary compliance vs correctness/evidence),
   and the invariants that keep a green guard from being read as a passed test. Adopts nothing; defines no metric.
```

## 9. Verdict

```text
verdict                                      = HOLD
flat_field_validated                         = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False
geometry_validity_claim_allowed              = False
screen_readiness_claim_allowed               = False
runtime_readiness_claim_allowed              = False
memory_readiness_claim_allowed               = False
integration_readiness_claim_allowed          = False
vision_claim_allowed                         = False

OUTCOME_LABEL: FLAT_OPPONENT_FIELD_NULL_CONTROL_BOUNDARY_REVIEW_ONLY
```

v2.12 is a docs-only null/control interpretation boundary review. It locks `null_control`, `has_null_control_role`,
and `F_null_control_fields` to a symbolic family role, a non-authorizing contrast placeholder, a claim-discipline
boundary object, and an unvalidated fixture category — and forbids every reading of them as a validation control,
negative-control result, metric/baseline, pass/fail criterion, evidence of any validity or readiness, falsification
success, or proof of null behavior or of A–E meaningfulness. It addresses the null/control interaction drift risks,
states the safe-use invariants, and recommends the branch REMAIN HELD. It adopts, expands, and relaxes nothing. All
claim locks and the frozen verdict **HOLD** are preserved and unmoved.

## 10. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_NULL_CONTROL_BOUNDARY_REVIEW_v2.12.md
(new, docs-only, untracked; over the accepted v2.11 edge fc4209d).

Verify that this review:
- is docs-only and authorizes NO implementation, NO expansion, NO validation, and NO null-control metric (no code /
  tests / schema, no torment_service/, no runtime, no memory, no camera / live / sensor / screen-capture / streaming,
  no real clips, no pixels / images); keeps form B (classifier) and form C (neural) CLOSED; opens no screen-analysis /
  numeric-geometry;
- frames the central question as WHETHER null_control / has_null_control_role can remain symbolic role labels only
  without becoming validation controls, pass/fail gates, metrics, evidence, or proof;
- defines the ALLOWED meaning of null_control / has_null_control_role / F_null_control_fields as ONLY a symbolic family
  role, a non-authorizing contrast placeholder, a claim-discipline boundary object, and an unvalidated fixture category;
- explicitly FORBIDS reading null/control as: a validation control, a negative-control result, a metric/baseline, a
  pass/fail gate, proof of geometry/descriptor/visual-structure validity, evidence of screen/runtime/memory/integration
  readiness, falsification success, proof of null behavior, or proof that non-null (A-E) families are meaningful;
- addresses the interaction drift risks (null_control + contrasts_with -> validation comparison; + separates ->
  segmentation proof; + contains -> absence proof; + boundary -> edge-control evidence; + field -> numeric field
  baseline; + region -> segmentation baseline);
- states the safe-use invariants (N1-N6): null/control presence != a control metric; symbolic contrast != measured
  contrast; absence-role language != verified absence; F-family presence != validation of A-E; null/control terms are
  anti-claim scaffolds, not evidence; protocol_ok = True != null/control "passed";
- recommends the branch REMAIN HELD; does NOT expand null/control into metrics or validation; requires any future
  control concept to go through a separate docs-first plan + Codex review + operator approval; recommends NO descriptor
  / coordinate / metric / validation / screen / real-clip / runtime / memory / neural / classifier / vision work;
- lists up to three docs-first next slices (v2.13 adversarial mutation review / A-F identity preservation audit /
  protocol guard semantics review);
- preserves the locks and verdict (§9): flat_field_validated = False; first_pass_structure_validity_claim_allowed =
  False; temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed =
  False; screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False; memory_readiness_claim_allowed
  = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False; verdict = HOLD; outcome label
  FLAT_OPPONENT_FIELD_NULL_CONTROL_BOUNDARY_REVIEW_ONLY; interprets HOLD/HELD as held for analysis, not abandoned;
- adds NO §0 pointer and NO tags, and makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
  temporal-order / readiness claim.

Flag any null/control term treated as a control metric / baseline / validation control / pass-fail gate / evidence /
proof, any adopted descriptor / coordinate / numeric geometry / metric / equation / threshold / pass-fail rule, any
validation / segmentation / falsification claim, any screen / real-clip / camera / live / runtime / memory
authorization, any classifier (B) / neural (C) opening, any "Brainvision sees" / vision / descriptor-validity /
geometry-validity / temporal-order / readiness claim, any recommendation to expand null/control, or any claim-lock /
verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Null/Control Boundary Review v2.12. Docs-only review. Opens no
implementation lane, no expansion, and no null-control metric; opens no classifier / neural / screen / real-clip /
runtime / memory work; adopts no descriptor / coordinate system / numeric geometry / metric / equation / threshold /
control metric / pass-fail rule; locks null_control / has_null_control_role / F_null_control_fields to a symbolic
family role, a non-authorizing contrast placeholder, a claim-discipline boundary object, and an unvalidated fixture
category, and forbids every reading of them as validation control / negative-control result / metric / baseline /
pass-fail gate / evidence of validity or readiness / falsification success / proof of null behavior or A-E
meaningfulness; addresses the interaction drift risks and safe-use invariants; recommends the branch REMAIN HELD;
preserves all claim locks and the frozen verdict HOLD; makes no vision / "Brainvision sees" / descriptor-validity /
geometry-validity / temporal-order / readiness claim; outcome label FLAT_OPPONENT_FIELD_NULL_CONTROL_BOUNDARY_REVIEW_ONLY;
no `§0` pointer added; no tags.*
