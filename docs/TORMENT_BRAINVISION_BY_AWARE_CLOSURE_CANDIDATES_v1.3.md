# TORMENT Brainvision BY-Aware Closure Candidates v1.3

## 1. Status / non-claims

**DOCS-ONLY candidate design. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no
integration lane.** It describes — for future, separately-gated consideration only — candidate *shapes* a future
BY-aware closure could take to address the persisting blue-yellow opponent-axis gap (`BY_axis_asymmetry`, shown
in v1.2 to remain visible under the preregistered A-G reporting). It **compares candidate ideas and adopts
none**. It defines **no final metric, no equation, no threshold, no decision rule**, and implements nothing. It
**authorizes no code and no tests**, invents no threshold, **redefines no `TOL`**, adopts **no new closure
metric**, proposes no pass/fail rule change, changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes
or weakens no control, redesigns no descriptor, reopens no spectral group as a closure group, expands no
generator family, and opens **no classifier (form B) and no neural encoder (form C)**. It does **not** pivot to
flat / screen geometry and opens **no flat-geometry / screen-analysis implementation**. Everything stays offline
under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. A candidate design alone moves nothing:
**no claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v1.1 / v1.1a / v1.2

```text
v1.1  (45be17d)  BY-aware closure PREREGISTRATION proposal: what a future prereg must CONTAIN (components A-G).
v1.1a (f6cf3c5)  BY-aware closure PREREGISTRATION plan: what a future reporting-only audit must REPORT.
v1.2  (b8062c4)  BY-aware closure audit HARNESS: generated the preregistered obligations A-G as diagnostic output.
v1.2f (72293cc)  BY-aware closure FINDINGS: result BY_aware_closure_gap_visible; closure_achieved False; HOLD.
v1.3  (this doc) candidate DESIGN: possible closure candidates A-E against the persisting gap, adopting none.
```

The chain to date has NAMED the offset (v0.8a), made it VISIBLE (v0.9b), guarded that visibility as
non-authorizing (v1.0b), PREREGISTERED what a closure must contain / report (v1.1 / v1.1a), and GENERATED that
reporting to show the gap PERSISTS (v1.2). This document is the first step of the v1.2-recommended Branch A: it
enumerates candidate closure *shapes* so a later, separate decision can select and specify one. It proves nothing,
validates nothing, and adopts nothing.

## 3. Current problem statement

```text
Under the preregistered A-G reporting (v1.2), the systematic BY opponent-axis offset SURVIVES the per-pair
residual / TOL match: it is signed and sign-consistent (by_std +0.04505 @0.95, by_centroid -0.03393 @0.90,
by_spread -0.02935 @0.84), BY-dominant over RG and directional features, often-binding (by_std binds 10/19;
BY-binding fraction 0.6316 > share 0.30), and coexists with a passing per-pair closure (aggregation_warning
True) -- on a SINGLE matching family (segment_paired_canceller), with coupling and amplitude weak.

The reporting makes this gap VISIBLE but decides nothing (closure_achieved False, HOLD). CLOSURE would require a
REPRESENTED DECISION under which a systematic, signed, BY-dominant, often-binding offset could NOT pass while the
classes stay ordered. No such decision exists yet. The design question this document opens: what SHAPES could
such a decision take -- described, compared, and left unadopted -- so the offset cannot hide inside residual/TOL
matching by construction?
```

## 4. Candidate design constraints

Every candidate below is bound by the same constraints; a candidate that violates any of these is out of scope
by definition:

```text
- DESCRIBE a decision SHAPE only; adopt NO metric, NO equation, NO threshold, NO pass/fail rule.
- Operate over the FROZEN records (v0.7b / v0.8a / v0.9b / v1.0b reused by identity); NO new data / seeds /
  families / candidate generation; NO descriptor / _stats / GROUPS redesign.
- Keep TOL = 0.0634, the floors (0.30), CHANCE_BAND (0.60), and the evaluator FROZEN; redefine NOTHING.
- Keep spectral audit-note-only (NOT a closure group); keep the single-family caveat (segment_paired_canceller).
- Stay NON-AUTHORIZING (v1.0b / v1.1a guard G, nine flags False): no candidate authorizes descriptor validity,
  temporal order, pass/fail, closure, runtime, memory, integration, live / screen use, or vision.
- Reporting-only lineage: a candidate is a possible FUTURE decision shape, not something this doc turns on.
```

## 5. Candidate A: signed BY offset closure component

```text
IDEA (shape only): a closure would REPRESENT the signed, across-pair-consistent BY offset (per by_centroid /
by_spread / by_std) as a first-class quantity in the decision -- not just |residual| -- so that a consistently
signed, systematic offset is something the closure can SEE and refuse, rather than average away.

WHAT IT WOULD TRY TO PREVENT: a consistently-signed class-level offset passing because the per-pair L-inf residual
stays within TOL (sign-blindness of the current match).

WHAT IT WOULD NOT DO (here): it fixes NO sign-consistency cutoff, NO offset magnitude threshold, NO equation
combining sign with residual. It names a REPRESENTED INPUT (signed offset + consistency), not a decision rule.

OPEN QUESTIONS: how sign-consistency would relate to a decision without a new threshold; whether "signed and
systematic" can be expressed via already-frozen references (e.g. the chance level 0.5) rather than a new cutoff.
```

## 6. Candidate B: BY/RG opponent-balance closure component

```text
IDEA (shape only): a closure would REPRESENT the BALANCE between the BY opponent axis and the RG (and directional)
comparison features -- i.e. that BY effects are large RELATIVE TO RG -- so opponent-axis dominance is part of the
decision rather than an after-the-fact panel.

WHAT IT WOULD TRY TO PREVENT: a BY-dominant offset hiding because the aggregate residual treats BY and RG
symmetrically even though the discrepancy is concentrated on the BY axis.

WHAT IT WOULD NOT DO (here): it fixes NO dominance ratio, NO BY-vs-RG threshold, NO weighting scheme. It names a
REPRESENTED RELATION (BY vs RG / directional), not a decision rule.

OPEN QUESTIONS: whether "BY-dominant" can be a represented comparison without inventing a dominance cutoff; how
this interacts with Candidate A (a signed AND dominant offset vs either alone).
```

## 7. Candidate C: BY binding-aware residual partition

```text
IDEA (shape only): a closure would be AWARE of WHICH stat binds the per-pair residual -- partitioning or annotating
the residual by its binding stat -- so that residual matches BOUND BY BY stats (especially by_std) are
distinguishable from residual matches bound by neutral stats.

WHAT IT WOULD TRY TO PREVENT: the residual/TOL match being read as evidence of similarity when the binding stat is
itself the BY axis (i.e. the match is "held together" by the very axis under suspicion).

WHAT IT WOULD NOT DO (here): it fixes NO binding-fraction gate, NO per-stat threshold, NO re-weighted residual. It
names a REPRESENTED PARTITION (residual annotated by binding stat), not a decision rule; TOL and the residual
definition stay frozen.

OPEN QUESTIONS: whether a binding-aware VIEW can inform a decision without becoming a binding gate; how a partition
avoids re-defining proxy_match_residual.
```

## 8. Candidate D: aggregation anti-hiding rule

```text
IDEA (shape only): a closure would carry an explicit ANTI-HIDING representation: when group-level residual/TOL
matching COEXISTS with a systematic BY signed ordering (the v1.2 aggregation_warning), the decision must not treat
the group-level match as similarity WITHOUT accounting for the coexisting ordering.

WHAT IT WOULD TRY TO PREVENT: hidden closure -- a passing per-pair / group residual being silently re-described as
closure of the BY offset when a systematic ordering coexists.

WHAT IT WOULD NOT DO (here): it fixes NO rule text, NO threshold on the warning, NO pass/fail. It names a
REPRESENTED OBLIGATION (coexistence must be accounted for), building on the v1.1a "no hidden closure" annotation,
not a decision rule.

OPEN QUESTIONS: what "accounted for" would concretely require of a decision without instantiating a pass/fail;
whether this is a meta-constraint over A-C rather than a standalone candidate.
```

## 9. Candidate E: region/family stratified reporting

```text
IDEA (shape only): a closure would STRATIFY its reporting by region and by matching family, so the offset's
persistence is always read WITH the single-matching-family caveat (segment_paired_canceller) and per-region BY
visibility, never pooled into a single family-blind statement.

WHAT IT WOULD TRY TO PREVENT: a closure (or a false closure) resting on a single family or a single region while
appearing general; and, conversely, a real offset being masked by pooling across regions.

WHAT IT WOULD NOT DO (here): it EXPANDS NO generator family and adds NO region. It names a REPRESENTED
STRATIFICATION over the EXISTING single family and frozen regions, preserving the caveat, not engineering it away.

OPEN QUESTIONS: how stratified reporting informs a decision when only one matching family exists; whether E is a
reporting discipline that must accompany A-D rather than a closure component on its own.
```

## 10. Why none are adopted yet

```text
- Each candidate is a SHAPE, not a decision: none fixes an equation, a threshold, a ratio, or a pass/fail rule,
  and none has been shown to catch the offset WITHOUT such an instantiation. Adopting one now would smuggle in a
  threshold / metric this document is forbidden to create.
- The evidence base is a SINGLE matching family (segment_paired_canceller), in-vitro, on frozen synthetic records.
  A candidate selected against one family risks being fitted to it (the exact failure v1.1 preregistration exists
  to prevent). Selection needs the discipline of a separate plan, not an inline choice.
- Candidates A-E are not mutually exclusive and partly compose (D and E read as meta-constraints over A-C). Which
  combination -- if any -- is even representable without a new threshold is an OPEN question, not a settled one.
- Verdict is HOLD and the offset is visible-not-closed; nothing here changes that. A candidate design is a menu,
  not a meal: it enables a later, separate SELECTION, and adopts nothing.
```

## 11. What would be needed before implementation

```text
Before ANY candidate could move toward implementation (all SEPARATE, later, gated; none opened here):
1. A docs-first v1.3a FINITE candidate-SELECTION plan: pick at most one candidate (or one composition) and state,
   in advance, what it would represent and what would count as it catching the offset -- still WITHOUT adopting a
   metric / equation / threshold (a preregistration in the v1.1 spirit).
2. Codex + operator explicit approval of the selected candidate as docs-only-first.
3. Only THEN a separate reporting-only implementation gate (form A, non-learning), reusing the frozen records by
   identity, with the v1.0b/v1.1a non-authorizing guard intact.
4. TOL, floors, evaluator, descriptor, GROUPS, family set, spectral role, and claim locks remain FROZEN throughout;
   verdict stays HOLD unless and until a separately-gated, preregistered decision earns a change.
No step above is authorized here. This document produces the menu for step 1 only.
```

## 12. Risks / ambiguity notes

```text
- THRESHOLD CREEP: every candidate is one careless sentence away from implying a cutoff. The mitigation is that
  selection (v1.3a) must state represented inputs and anti-hiding obligations BEFORE any scoring, and Codex must
  flag any candidate that only "works" via an invented threshold.
- SINGLE-FAMILY FIT: with one matching family, any candidate can look decisive by fitting that family. Candidate E
  (stratification) and the single-family caveat are the guardrails; a candidate that needs family expansion to work
  is out of scope (that would be Branch B territory, not A).
- COMPOSITION AMBIGUITY: A/B/C are candidate INPUTS; D/E read more as meta-constraints. v1.3a must decide whether
  it is selecting a component, a composition, or a discipline -- this is genuinely unresolved here.
- GEOMETRY RISK: if NO A-E composition can represent a decision that catches the offset without a new threshold or
  family, that is the signal that the FIXTURE GEOMETRY itself may be the wrong abstraction -- i.e. escalate to the
  flat opponent-plane / spatial-field proposal (Branch B), not force a metric.
- NON-AUTHORIZATION: none of these candidates, even if later selected, would authorize descriptor validity,
  temporal order, vision, runtime, memory, integration, or live / screen use.
```

## 13. Candidate next branches

Docs-first candidates only; **none opened or authorized here**:

```text
A. v1.3a FINITE candidate-SELECTION plan (docs-only)
   Pick at most one candidate / composition from A-E and preregister what it would represent and what would count
   as catching the offset -- adopting NO metric / equation / threshold. (Recommended next.)
B. FLAT OPPONENT-PLANE / SPATIAL-FIELD proposal (docs-only)
   If no A-E composition is representable without a new threshold or family, question the fixture geometry instead.
   Conceptual only; NO flat-geometry / screen-analysis implementation.
C. Operator / new-math NOTE (docs-only).
D. Pause Brainvision and return to TORMENT memory / kernel work.
```

## 14. Recommended next step

**Recommend Branch A (v1.3a finite candidate-selection plan, docs-only) next.** v1.3 lays out the menu; the clean
move is to preregister a single selection (or one composition) and what would count as it catching the offset —
docs-only, adopting nothing — before any implementation. **Do not jump directly to code** unless Codex and the
operator explicitly approve a selected candidate. If v1.3a finds no A-E composition representable without an
invented threshold or a family expansion, that is the signal to escalate to Branch B (flat opponent-plane /
spatial-field) rather than force a metric.

```text
1. Codex review THIS candidate design (docs-only; over committed edge 72293cc).
2. If accepted, the operator commits this doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first v1.3a candidate-SELECTION
   plan (preregistration-style; no metric / equation / threshold / pass-fail / descriptor / family / spectral /
   flat / screen / runtime / memory adopted). Code only AFTER Codex + operator explicitly approve a selection.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 15. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_AWARE_CLOSURE_CANDIDATES_v1.3.md
(new, docs-only, untracked; over committed edge 72293cc, designing candidate BY-aware closure shapes A-E against
the persisting gap from v1.2, adopting none).

Verify that this candidate design:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED; and
  authorizes NO flat-geometry and NO screen-analysis implementation;
- describes candidate closure SHAPES ONLY and ADOPTS NONE -- it defines no metric, no equation, no final pass/fail
  rule, invents no threshold, redefines no TOL, redesigns no descriptor, expands no family, and reopens no spectral
  group (incl. not as a closure group);
- states the problem correctly: under the preregistered A-G reporting the BY offset SURVIVES residual/TOL matching
  (signed, BY-dominant, often-binding, aggregation-coexistent, single family), so a closure would need a REPRESENTED
  DECISION -- and this doc only enumerates possible decision SHAPES, choosing none;
- presents candidates A-E (signed offset / BY-RG opponent balance / binding-aware residual partition / aggregation
  anti-hiding / region-family stratification) each as a SHAPE with what it would try to PREVENT and what it would NOT
  do, with no adopted cutoff or equation, and keeps everything in §4/§11 frozen;
- explains why none are adopted (§10), what must precede implementation (§11: v1.3a selection plan + Codex/operator
  approval before any code), and the risks (§12: threshold creep, single-family fit, composition ambiguity, geometry
  escalation, non-authorization);
- recommends Branch A (v1.3a finite candidate-selection plan, docs-only) next, does NOT jump to code, and escalates
  to Branch B (flat opponent-plane / spatial-field) only if no A-E composition is representable without a new
  threshold / family; lists C/D;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any adopted metric / equation / threshold / pass-fail rule, any TOL redefinition, any descriptor redesign, any
family expansion, any spectral reopening as a closure group, any flat-geometry / screen-analysis / runtime / memory /
real-clip authorization, any claim that closure is ACHIEVED (vs the gap being visible), any descriptor-validity /
vision / temporal-order claim, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY-Aware Closure Candidates v1.3. Docs-only candidate design, non-authorizing. Opens no
implementation lane; opens no classifier / neural / screen / flat-geometry work; changes no frozen formula, gate,
evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no threshold; redefines no
TOL; adopts no closure metric; defines no equation; compares candidate closure shapes only, adopting none; keeps
the gap visible not closed; makes no vision / descriptor-validity / temporal-order / memory / runtime / integration
claim; no `§0` pointer added; no tags.*
