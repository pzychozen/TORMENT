# TORMENT Brainvision Post-Symbolic Branch Direction Scan v2.19

## 1. Status / Scope

**DOCS-ONLY direction SCAN.** This is a comparison note only. It opens **no** code, **no** tests, **no** runtime, and
**no** integration lane; it authorizes **no** implementation, **no** validation, **no** readiness claim, and **no**
capability claim, and it is not corrective. It sits over the accepted v2.18 edge (`e3b6bd6`) and changes none of the
accepted files.

**v2.18 paused the flat opponent-field symbolic branch as scaffold / review work only** — not a claim closure, not a
validation. **v2.19 compares next directions only.** It helps the operator choose what to do next *without*
automatically continuing the paused symbolic branch and *without* opening validation, descriptor, coordinate, metric,
screen, real-clip, runtime, memory, classifier, neural, or vision claims. It compares options; it selects no work and
starts none.

**v2.19 authorizes no implementation, expansion, validation, readiness, or capability claim.** It introduces and
authorizes **no** descriptor, coordinate system, numeric geometry, metric, null/control metric, equation, threshold,
control metric, pass/fail gate, validation, screen analysis, real clip, camera / live / sensor / streaming path,
runtime path, memory path, prompt / context / action / render-body / autonomy contact, classifier (form B), or neural
encoder (form C), and it authorizes **no** family or vocabulary expansion. It makes **no** production vision claim,
**no** "Brainvision sees" claim, **no** temporal-order claim, and **no** descriptor-validity / geometry-validity /
screen-readiness / memory-readiness / runtime-readiness / integration-readiness claim. The flat opponent-field
symbolic branch stays **HELD** unless the operator explicitly chooses a separately bounded continuation path.
Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6. **HOLD / HELD means held for
analysis and claim control — not abandoned.**

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

## 2. Current Branch State

```text
ESTABLISHED (v2.6-v2.18), scaffold / boundary / guard only -- NOT validation or capability:
  a generated/reporting-only A-F fixture-description layer (v2.6); a representation plan (v2.7); a boundary review
  (v2.8); a minimal guarded static symbolic representation artifact (v2.9); exact A-F family coverage; a canonical
  component/relation vocabulary; a conservative boundary-compliance check_protocol; seven boundary-hardening reviews
  (v2.10-v2.17: stress synthesis, vocabulary drift, null/control, mutation, protocol semantics, family identity,
  non-claim invariants, wording); generated-vs-validated separation; negative claim-lock preservation; and a pause
  synthesis (v2.18).

NOT ESTABLISHED (unproven): flat-field validation; geometry / descriptor / coordinate / metric / visual-structure
  validity; visual completeness; screen / real-clip / runtime / memory / integration readiness; classifier / neural
  readiness; temporal-order evidence; pass/fail validation; null/control success; production vision; "Brainvision
  sees".

The branch is a paused, non-authorizing symbolic scaffold with a fully documented non-claim wall. This scan chooses
nothing about it; it compares where to go next.
```

## 3. Direction Comparison

Each path is evaluated across the required dimensions: what it would do; what it would not do; primary benefit;
primary risk; boundary risk; required guardrails; recommend now?; operator approval required before follow-up?

```text
====================================================================================================================
PATH A -- SYMBOLIC ARTIFACT IMPLEMENTATION HARDENING PLAN (docs-only plan for a future hardening-only pass)
  would do        : plan a FUTURE hardening-only pass for the v2.9 artifact -- strengthen existing guards, check
                    canonical strings more strictly, improve breach reporting -- preserving the same A-F families, the
                    same vocabulary, and all locks.
  would NOT do     : expand representation; add families or vocabulary; add descriptors / coordinates / metrics /
                    validation; open screen / real-clip / runtime / memory / classifier / neural / vision.
  primary benefit  : marginally tightens the guard surface against the v2.13 mutation classes; low conceptual risk.
  primary risk     : LOOKS like progress toward capability even though it is only guard hardening.
  boundary risk    : MEDIUM -- "hardening the artifact" can be misread as "improving the capability".
  guardrails       : hardening-only; no semantic change; all locks preserved; separate docs-first plan + Codex +
                    operator approval before any code; wording per v2.17 (no "success/ready/validated").
  recommend now?   : NO (secondary only) -- useful but not the highest-value next move; the guard surface is already
                    assessed conceptually sufficient (v2.13 §5).
  approval req'd?  : YES -- any follow-up (even a plan that leads to code) requires explicit operator approval.

====================================================================================================================
PATH B -- REPRESENTATION EXPANSION READINESS HOLD REVIEW (docs-only decision review)
  would do        : review whether richer symbolic representation should remain BLOCKED; identify why expansion is
                    unsafe; define what would have to be true before expansion could even be planned; preserve HOLD.
  would NOT do     : actually expand representation; authorize implementation; add descriptors / coordinates / metrics
                    / validation; open screen / runtime / memory / vision.
  primary benefit  : makes the expansion-block criteria explicit, so a future expansion decision is principled.
  primary risk     : the word "expansion" itself creates PRESSURE toward hidden geometry / descriptor semantics.
  boundary risk    : MEDIUM-HIGH -- framing a review around "expansion readiness" invites drift toward the very thing
                    it is meant to gate.
  guardrails       : decision-review only; preserve HOLD; no expansion; treat "readiness" as claim-control language,
                    not capability; per-v2.16/v2.17 invariants and wording.
  recommend now?   : NO -- largely restates v2.10/v2.16/v2.18 (expansion is blocked, and why); low marginal value now.
  approval req'd?  : YES -- any move it recommends requires separate operator approval.

====================================================================================================================
PATH C -- BROADER BRAINVISION RESEARCH DIRECTION SCAN (docs-only, step back from the flat-field branch)  [PREFERRED]
  would do        : step back from the flat-field symbolic branch and compare broader Brainvision research LAYERS as
                    FROZEN EVIDENCE -- BY/color/chroma residual questions, prior fixture-metric failures, the
                    flat opponent-field scaffold, symbolic-representation limits, and whether a different non-runtime
                    offline layer is more useful next.
  would NOT do     : implement anything; touch real clips / descriptors / screen / runtime / memory; revive a failed
                    path as if solved; make a vision claim.
  primary benefit  : HIGHEST-VALUE next move -- decides WHERE Brainvision should go after a clean pause, rather than
                    reflexively continuing guard/hardening docs; treats prior work as frozen evidence, not resumed
                    claims.
  primary risk     : too broad a scan becomes unfocused, or tries to REVIVE failed paths without clear boundaries.
  boundary risk    : LOW-MEDIUM -- it is a comparison of directions, not a step into any of them; the risk is scope,
                    not claim leakage, and is controllable.
  guardrails       : docs-only; each area handled as FROZEN EVIDENCE with explicit boundaries; no path revived as
                    solved; no implementation / real-clip / screen / runtime / memory / vision; preserve all locks.
  recommend now?   : YES (PREFERRED) -- the clean pause makes a broad direction scan the most useful next docs step.
  approval req'd?  : YES -- the scan RECOMMENDS; the operator chooses the actual next slice.

====================================================================================================================
PATH D -- PAUSE FLAT-FIELD BRANCH AND CHOOSE ANOTHER BRAINVISION LAYER (deliberate layer move)
  would do        : treat the v2.6-v2.18 flat-field symbolic branch as SEALED SCAFFOLD EVIDENCE and deliberately move
                    to another layer -- return to BY/chroma/residual evidence, identify a new docs-first offline
                    falsification question, or decide whether Brainvision should stay in scaffold work or return to
                    empirical synthetic tests.
  would NOT do     : treat prior failures as solved; treat the symbolic branch as validation; jump to screen /
                    real-clip / runtime / memory / vision.
  primary benefit  : commits to a concrete other layer, giving forward motion.
  primary risk     : moving layers TOO SOON can lose the useful scaffold boundary just built, or pick a layer before
                    the trade-offs are compared.
  boundary risk    : MEDIUM -- committing to a layer before a comparison (Path C) risks a premature or unbounded move.
  guardrails       : prior work stays FROZEN EVIDENCE (not resumed claims); new question is docs-first with explicit
                    boundaries; no implementation / real-clip / screen / runtime / memory / vision; preserve all locks.
  recommend now?   : NO -- Path D is a good move AFTER Path C's comparison, not before it; choosing a layer without the
                    scan risks a premature commitment.
  approval req'd?  : YES -- a layer move is an operator decision.
====================================================================================================================
```

## 4. Cross-Path Risks

Risks that span the options, each to be refused regardless of which path is chosen:

```text
- SYMBOLIC SCAFFOLD MISTAKEN FOR VALIDATION: none of A-D validates the flat opponent-field; the scaffold stays a
  non-authorizing claim-discipline layer (v2.18 wall W1). No path may be read as "the branch was validated".
- HARDENING MISTAKEN FOR PROGRESS TOWARD CAPABILITY: Path A tightens guards only; a tighter guard is not a better
  capability. Guard hardening must never be written up as "the artifact is more capable / closer to vision".
- EXPANSION LANGUAGE CREATING GEOMETRY/DESCRIPTOR PRESSURE: Path B's "expansion readiness" framing can invite drift
  toward measured geometry or descriptors; "readiness" stays claim-control language, and expansion stays blocked.
- BROAD SCANS REVIVING OLD FAILED PATHS WITHOUT BOUNDARIES: Path C/D must treat BY/color/chroma/residual and
  fixture-metric failures as FROZEN EVIDENCE, never as solved or auto-resumable; any revisit needs its own explicit
  boundary and gating.
- MOVING LAYERS BEFORE PRESERVING CURRENT LESSONS: Path D risks discarding the just-built scaffold boundary; the
  v2.18 synthesis and the non-claim wall must remain the resumable record before any layer move.
```

## 5. Recommendation

```text
RECOMMEND: PATH C -- broader Brainvision research direction scan (docs-only).

Reason: the flat opponent-field symbolic branch is now paused CLEANLY (v2.18), with a complete non-claim wall and a
resumable synthesis. The next highest-value move is NOT another automatic guard/hardening doc (Path A) and NOT a
restatement of the expansion block (Path B), and NOT a premature layer commitment (Path D) -- it is a broader,
docs-only scan that compares where Brainvision should go next, treating all prior work (flat-field scaffold,
BY/color/chroma/residual, fixture-metric failures) as FROZEN EVIDENCE. Path C decides direction before spending effort,
and its boundary risk is scope (controllable) rather than claim leakage.

SECONDARY (bounded) option: PATH A -- a single small hardening-only pass on the existing v2.9 artifact -- but ONLY if
the operator explicitly wants it, and ONLY as guard hardening with no semantic change, all locks preserved, and
separate docs-first planning + Codex review + operator approval before any code.

NOT recommended now: Path B (low marginal value; restates the block) and Path D (better after Path C's comparison than
before it). No descriptor / coordinate / metric / validation / screen / real-clip / runtime / memory / classifier (B) /
neural (C) / vision work is recommended or authorized by this scan.
```

## 6. Operator Decision Needed

```text
The next ACTUAL slice must be chosen by the OPERATOR. This scan makes a clear recommendation (Path C, with Path A as a
bounded secondary) but is NOT self-authorizing: it starts no work and commits to no path. Whichever path the operator
picks becomes a SEPARATE, docs-first slice with its own boundary, Codex review, and (for anything beyond docs)
explicit operator approval. Until then, the flat opponent-field symbolic branch stays HELD, and Brainvision stays
offline / quarantined.
```

## 7. Verdict

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

OUTCOME_LABEL: BRAINVISION_POST_SYMBOLIC_BRANCH_DIRECTION_SCAN_ONLY
```

v2.19 is a docs-only post-symbolic branch direction scan. It summarizes the paused flat opponent-field symbolic branch
state (scaffold / boundary / guard only; nothing validated), compares four next directions (A hardening plan, B
expansion-readiness HOLD review, C broader Brainvision direction scan, D layer move) across what each would and would
not do, its benefit, primary and boundary risks, required guardrails, whether to recommend now, and whether operator
approval is required, addresses the cross-path risks, and recommends **Path C** (with Path A as a bounded secondary
only on explicit operator approval). It selects no work, starts none, and is not self-authorizing. All claim locks and
the frozen verdict **HOLD** are preserved and unmoved.

## 8. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_POST_SYMBOLIC_BRANCH_DIRECTION_SCAN_v2.19.md
(new, docs-only, untracked; over the accepted v2.18 edge e3b6bd6).

Verify that this scan:
- is docs-only and authorizes NO implementation, NO test expansion, NO family / vocabulary expansion, NO validation,
  NO readiness claim, and NO capability claim (no code / tests / schema, no torment_service/, no runtime, no memory, no
  camera / live / sensor / screen-capture / streaming, no real clips, no pixels / images); keeps form B (classifier)
  and form C (neural) CLOSED; opens no screen-analysis / numeric-geometry; changes no field / value / family / lock;
- frames the central question as WHICH next Brainvision direction is safest and most useful after the v2.18 pause, and
  keeps the flat opponent-field symbolic branch HELD unless the operator explicitly chooses a separately bounded path;
- summarizes the current branch state (established scaffold/boundary/guard only; not-established validation/geometry/
  descriptor/coordinate/metric/visual/readiness/temporal/vision);
- compares the four required paths (A symbolic artifact implementation hardening plan; B representation expansion
  readiness HOLD review; C broader Brainvision research direction scan; D pause flat-field branch and choose another
  Brainvision layer) across ALL required dimensions (what it would do; what it would not do; primary benefit; primary
  risk; boundary risk; required guardrails; whether to recommend now; whether operator approval is required before any
  follow-up), with each path's allowed/forbidden scope respected;
- addresses the cross-path risks (symbolic scaffold mistaken for validation; hardening mistaken for progress toward
  capability; expansion language creating geometry/descriptor pressure; broad scans reviving old failed paths without
  boundaries; moving layers before preserving current lessons);
- RECOMMENDS Path C unless a stronger reason is found, explains why, and mentions Path A as a bounded secondary option
  ONLY after explicit operator approval; recommends NO descriptor / coordinate / metric / validation / screen /
  real-clip / runtime / memory / neural / classifier / vision work;
- states that the next actual slice must be chosen by the OPERATOR and that the scan is not self-authorizing;
- preserves the locks and verdict (Section 7): flat_field_validated = False; first_pass_structure_validity_claim_allowed
  = False; temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed =
  False; screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False; memory_readiness_claim_allowed
  = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False; verdict = HOLD; outcome label
  BRAINVISION_POST_SYMBOLIC_BRANCH_DIRECTION_SCAN_ONLY; interprets HOLD/HELD as held for analysis, not abandoned;
- adds NO §0 pointer and NO tags, and makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
  temporal-order / readiness claim.

Flag any path recommended in a way that authorizes work without separate operator approval, any prior failed path
treated as solved / auto-resumable, any adopted descriptor / coordinate / metric / validation / pass-fail rule, any
screen / real-clip / camera / live / runtime / memory authorization, any classifier (B) / neural (C) opening, any
"Brainvision sees" / vision / descriptor-validity / geometry-validity / temporal-order / readiness / capability claim,
or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Post-Symbolic Branch Direction Scan v2.19. Docs-only direction scan. Opens no implementation
lane, no test expansion, and no family / vocabulary expansion; opens no classifier / neural / screen / real-clip /
runtime / memory work; adopts no descriptor / coordinate system / numeric geometry / metric / equation / threshold /
control metric / pass-fail rule; changes no field / value / family / lock; compares four next Brainvision directions
(A hardening plan, B expansion-readiness HOLD review, C broader direction scan, D layer move) across what each would
and would not do, its benefit, primary and boundary risks, guardrails, recommend-now, and approval-required;
recommends Path C (Path A a bounded secondary only on explicit operator approval); keeps the flat opponent-field
symbolic branch HELD; is not self-authorizing and leaves the next slice to the operator; preserves all claim locks and
the frozen verdict HOLD; makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
temporal-order / readiness claim; outcome label BRAINVISION_POST_SYMBOLIC_BRANCH_DIRECTION_SCAN_ONLY; no `§0` pointer
added; no tags.*
