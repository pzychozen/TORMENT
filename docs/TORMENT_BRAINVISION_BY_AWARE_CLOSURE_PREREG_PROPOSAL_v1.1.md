# TORMENT Brainvision BY-Aware Closure Preregistration Proposal v1.1

## 1. Status / non-claims

**DOCS-ONLY proposal. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration
lane.** It proposes — for future, separately-gated consideration only — what a future BY-aware closure
*preregistration* would need to **contain** (its required components) so that a systematic blue-yellow
opponent-axis offset (`BY_axis_asymmetry`) cannot hide inside residual / `TOL` matching before any implementation
or metric adoption is considered. It describes candidate **preregistration components only — it adopts none**,
defines no final equations, defines no pass/fail rule, and implements nothing. It **authorizes no code and no
tests**, invents no threshold, **redefines no `TOL`**, adopts **no new closure metric**, proposes no pass/fail
rule change, changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no control,
redesigns no descriptor, reopens no spectral group as a closure group, expands no generator family, and opens
**no classifier (form B) and no neural encoder (form C)**. It does **not** pivot to flat / screen geometry and
opens **no flat-geometry implementation and no screen-analysis implementation**. Everything stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. A proposal alone moves nothing: **no
claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v0.8a / v0.9b / v1.0 / v1.0b

```text
v0.8a (8977248)  BY-channel metric anatomy -> BY_axis_asymmetry: a signed, sign-consistent, BY-dominant,
                 often-binding class-level opponent-axis offset that survives the residual/TOL match.
v0.9b (11a1997)  BY closure visibility AUDIT -> BY_visibility_confirmed: panels A-F make the offset visible.
v1.0  (3738c73)  BY-aware closure STRUCTURE proposal: requirements A-G a future closure design must REPRESENT,
                 adopting none. Named "BY-aware closure metric pre-registration" as a candidate later branch.
v1.0b (e083bb4)  BY-aware closure AUDIT FINDINGS -> BY_aware_visibility_confirmed: panels A-G (A-F re-presented
                 plus the non-authorizing panel G); outcome protocol_ok=True, verdict HOLD, locks False.
v1.1  (this doc) proposes what a future BY-aware closure PREREGISTRATION must CONTAIN before any implementation or
                 metric adoption, docs-only, adopting none.
```

(Full chain for reference: v0.9 proposal `6485e55`, v0.9a plan `3aba63d`, v0.9c synthesis `c17ec74`, v1.0a plan
`3013f85`.) This proposal is preregistration-defining only. It does not prove Brainvision, validate the
descriptor, invalidate prior work, adopt a metric, or select flat / screen geometry. It changes nothing
v0.4b/v0.4c/v0.7a froze or v0.7b/v0.8a/v0.9b/v1.0b produced. Where v1.0 said **what a closure must represent**,
v1.1 says **what a preregistration of such a closure must commit to in advance, before anything is built**.

## 3. Why visibility is insufficient

```text
- v1.0b confirmed VISIBILITY (BY_aware_visibility_confirmed): panels A-G surface the signed, sign-consistent,
  BY-dominant, often-binding class-level offset AND record (G) that this visibility authorizes nothing. But
  panels are a REPORTING layer over the SAME per-pair L-inf <= TOL closure; they surface the offset and change
  no decision. The offset is visible AFTER THE FACT, not REPRESENTED IN the closure decision.
- The per-pair L-inf <= TOL closure is sign-blind and cross-pair-blind: a consistently-signed, BY-dominant,
  often-binding class-level offset can pass every pair while the classes stay ordered (v0.6a/v0.7b/v0.8a/v1.0b:
  by_std +0.04505 @0.95, by_centroid -0.03393 @0.90, by_spread -0.02935 @0.84; BY binding fraction 0.6316 > 0.30).
- A future closure DESIGN could REPRESENT the offset (v1.0, WHAT-not-HOW). But a design built ad hoc, after
  seeing these records, risks being fitted to THIS offset on THIS single matching family -- a post-hoc metric
  that "closes" by construction proves nothing. The missing layer between visibility (v1.0b) and a defensible
  closure is a PREREGISTRATION: a committed-in-advance statement of WHAT the closure must represent, WHAT would
  count as the offset "hiding," and WHAT must stay frozen -- written BEFORE any metric or threshold is chosen.
- Therefore the proof route remains HELD: the BY offset is VISIBLE but NOT CLOSED, and closing it responsibly
  requires a preregistration first (this doc says WHAT a prereg must contain, not HOW to score, and adopts nothing).
```

## 4. BY-aware closure preregistration question

```text
CORE QUESTION:
  What must be REPRESENTED in a future BY-aware closure structure -- and committed to IN ADVANCE in a
  preregistration -- BEFORE any implementation or metric adoption is considered, so that a systematic BY
  opponent-axis offset cannot hide inside residual / TOL matching?

A preregistration answers this without adopting anything. It fixes, in advance:
  (i)   which quantities a future closure MUST represent (so the offset is first-class, not a post-hoc panel);
  (ii)  what would count as the offset "HIDING" inside residual/TOL matching (the failure the closure must catch);
  (iii) what stays FROZEN, so the closure cannot be reverse-fitted to this offset / this single family;
  (iv)  what remains NON-AUTHORIZING regardless of any future result.
It does NOT choose an equation, a threshold, a decision rule, or a family -- those are separate, later, gated.
```

## 5. Candidate preregistration components

Proposed for future consideration; **NONE adopted here**. Each names only what a future BY-aware closure
*preregistration* would need to **contain** (a component it must specify in advance), not a metric, a threshold,
or a decision it would make. Each is stated as a representational / commitment obligation on the prereg document,
not on the runtime or the descriptor.

```text
A. Signed-offset component
   The prereg MUST specify that a future closure represents whether by_centroid, by_spread, and by_std retain
   systematic SIGNED offsets across matched pairs (sign + across-pair consistency, not just |residual|), and
   MUST commit in advance to how "systematic signed offset" is described -- WITHOUT adopting a cutoff.

B. BY dominance component
   The prereg MUST specify that a future closure represents BY effect magnitude RELATIVE to the RG and
   directional comparison features (opponent-axis dominance), committing in advance to the comparison being
   reported -- WITHOUT adopting a dominance threshold or ratio rule.

C. Binding-stat component
   The prereg MUST specify that a future closure represents whether BY stats BIND the residual match -- how
   often each of by_std / by_spread / by_centroid is the L-inf-binding stat, especially by_std -- committing in
   advance to reporting binding vs the proportional share, WITHOUT adopting a binding-fraction gate.

D. Aggregation-warning component
   The prereg MUST specify that a future closure represents WHEN group-level residual / TOL matching COEXISTS
   with a systematic BY signed ordering (the aggregation / compression warning), committing in advance to
   surfacing this coexistence -- WITHOUT converting the warning into a pass/fail rule.

E. Coupling / leakage separation component
   The prereg MUST specify that a future closure keeps BY_axis_asymmetry SEPARATE from centroid/spread coupling
   and from amplitude / channel-energy leakage, committing in advance to reporting the separated mechanism
   scores so BY dominance is not confounded -- WITHOUT adopting a mechanism-selection rule.

F. Region / family caveat component
   The prereg MUST specify that a future closure PRESERVES and reports the single-matching-family caveat
   (segment_paired_canceller) and target-region visibility (per-region BY), committing in advance that closure
   evidence from a single family is caveated -- WITHOUT expanding the family set to "fix" it.

G. Non-authorizing guard
   The prereg MUST specify that BY-aware reporting NEVER automatically authorizes descriptor validity, pass/fail,
   closure, runtime, memory, integration, or vision claims -- committing this non-authorization in advance, as a
   standing property of any closure built to this prereg (mirrors v1.0 requirement G / v1.0b panel G, all False).
```

Each component is a **preregistration-content obligation**: a thing the future prereg document must state before
any build. Adopting any of them as a metric, a pass/fail gate, or a threshold is explicitly **out of scope here**
and would need a separate, separately-gated decision. This proposal describes components; it defines no equations.

## 6. What must remain frozen

```text
- TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30; CHANCE_BAND = 0.60 (referenced frozen; not re-thresholded).
- the frozen evaluator (structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR).
- the frozen descriptor / _stats / GROUPS / best-threshold BA / robustness lens.
- proxy_match_residual (L-inf over the ten matched stats, spectral excluded) and PSC < PSC_FLOOR feasibility.
- the closed F1-F5 family set; the single matching family (segment_paired_canceller); the v0.7b samples;
  spectral audit-note-only (NOT reopened as a closure group).
- the v0.8a / v0.9b / v1.0b records reused BY IDENTITY; no sample replacement / new seeds / new candidate generation.
- claim locks and verdict HOLD.
A preregistration that could be reverse-fitted to this offset is worthless; freezing ALL of the above is what
makes a future prereg-constrained closure meaningful. This proposal freezes all of the above and only proposes
which components a future prereg must contain.
```

## 7. What must not be adopted yet

The preregistration stage adopts nothing forward-looking. Explicitly deferred to a separate, later, gated
decision (NOT opened, NOT authorized here):

```text
- NO closure metric / scoring function adopted (components A-G are contents of a prereg, not a metric).
- NO threshold, cutoff, ratio, dominance rule, binding-fraction gate, or CHANCE_BAND change invented.
- NO TOL redefinition; NO pass/fail rule change; NO §7 anti-proxy or §8 verdict-logic change.
- NO descriptor redesign; NO _stats / GROUPS change; NO new family or axis; NO spectral reopening as a closure group.
- NO control weakened or removed; NO sample rerun / replacement; NO new seeds or candidate generation.
- NO classifier (form B); NO neural encoder (form C).
- NO flat-geometry implementation; NO screen-analysis implementation; NO camera / live / sensor / screen / streaming.
- NO runtime / memory / integration wiring; NO real / local clips; NO torment_service touch.
- NO §0 pointer; NO tags; NO vision / "Brainvision sees" / temporal-order / descriptor-validity claim.
A prereg that adopted any of these would stop being a prereg. This one adopts none.
```

## 8. What would count as useful evidence

A docs-only preregistration proposal yields **no empirical evidence** about Brainvision. "Useful" here means the
proposal is an adequate design contract — **not** a pass, a threshold, or a validity statement:

```text
- The components A-G are individually PRE-SPECIFIABLE over the existing v0.8a/v0.9b/v1.0b records (each names a
  quantity already visible in panels A-G) -- so a future closure could be built to them WITHOUT new data.
- The components are JOINTLY SUFFICIENT to define what the offset "HIDING" would look like (signed + dominant +
  binding + aggregation-coexistent), so a closure built strictly to this prereg could not let BY_axis_asymmetry
  pass residual/TOL matching UNREPRESENTED by construction.
- The frozen set (§6) and the deferral set (§7) are complete enough that a prereg-constrained closure could not
  be reverse-fitted to this offset / this single family.
- The non-authorizing guard (G) is stated as a standing property, so even a future "closed" reading stays
  diagnostic and never becomes automatic validity / pass-fail / runtime / memory / integration / vision.
- Codex accepts the proposal AS-IS (or with bounded modifications) as docs-only, adopting nothing.
Useful evidence is that the prereg is COMPLETE and NON-FITTABLE -- a design-layer artifact -- not that anything
about Brainvision has been proven or closed.
```

## 9. What would still not be proven

Even a complete, Codex-accepted BY-aware closure preregistration would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
not closure                    (a prereg says what a closure must contain; it closes nothing)
```

Writing a preregistration for a synthetic BY-axis offset is an in-vitro, design-layer step within the same
frozen family set; it says nothing about real clips or screens and does not validate the descriptor or adopt a
metric. The proof route remains **HELD / HOLD** because the offset is visible but not closed. The claim locks
(`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`, `descriptor_validity_claim_allowed`)
and `verdict = HOLD` remain in force.

## 10. Candidate next branches

Docs-first candidates only; **none opened or authorized here**:

```text
A. Candidate closure-metric COMPONENT enumeration (docs-first)
   ONLY after this prereg is accepted: enumerate candidate metric COMPONENTS / reporting structure constrained
   by A-G, still WITHOUT adopting a metric, threshold, or pass/fail rule. This is the natural successor to v1.1.
B. Flat opponent-plane / spatial FIELD framing (docs-first, conceptual)
   Still a candidate, but only AFTER the BY-aware closure preregistration exists and is accepted. Conceptual
   only; NO screen / flat-geometry implementation. (Recommendation: do NOT pivot here until v1.1 exists.)
C. Operator / new-math NOTE (docs-first)
   Ask the operator to propose intuition / math only AFTER the prereg components are written clearly.
D. Pause Brainvision and return to TORMENT memory / kernel work.
```

## 11. Recommended next step

**Recommend completing the preregistration path first: Codex review THIS proposal (docs-first), and do NOT pivot
to flat opponent-plane geometry until this proposal exists and is accepted.** v1.0b confirmed the offset is
visible and non-authorizing; v1.0 defined what a closure must represent; v1.1 defines what a preregistration of
that closure must contain before anything is built. The clean move after v1.1 is Branch A — a docs-first
enumeration of candidate closure-metric *components* constrained by A-G, still adopting nothing — not a geometry
pivot (B), new math (C), or a build. B / C are best taken only once A-G are agreed. D (pause) remains a
legitimate operator call.

```text
1. Codex review THIS proposal (docs-only; over committed edge e083bb4).
2. If accepted, the operator runs the Windows suite (nothing to run: docs-only) and commits this proposal doc.
   No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first candidate closure-metric
   COMPONENT enumeration (constrained by A-G; no metric adopted, no threshold, no descriptor change). Do NOT
   pivot to flat opponent-plane / screen geometry (B) until this preregistration exists and is accepted.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 12. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_AWARE_CLOSURE_PREREG_PROPOSAL_v1.1.md
(new, docs-only, untracked; over committed edge e083bb4, proposing what a future BY-aware closure PREREGISTRATION
must contain, from v1.0b's confirmed visibility).

Verify that this proposal:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED; and
  authorizes NO flat-geometry and NO screen-analysis implementation;
- proposes candidate PREREGISTRATION COMPONENTS ONLY and ADOPTS NONE -- it defines no equations, no final pass/fail
  rules, invents no threshold, redefines no TOL, adopts no new closure metric, redesigns no descriptor, expands no
  family, and reopens no spectral group (incl. not as a closure group);
- states the question correctly: what a future closure must REPRESENT and a prereg must COMMIT TO IN ADVANCE, so a
  systematic BY offset cannot hide inside residual/TOL matching -- BEFORE any implementation or metric adoption
  (WHAT a prereg must contain, not HOW to score);
- states why visibility (v1.0b) is insufficient: panels are a reporting layer over the SAME sign-blind /
  cross-pair-blind closure, and an ad-hoc post-hoc metric fitted to this offset/this single family would prove
  nothing, so a preregistration must come first;
- lists components A-G (signed-offset / BY-dominance / binding-stat / aggregation-warning / coupling-leakage
  separation / region-family caveat / non-authorizing guard) as prereg-content obligations, not decisions, and
  keeps everything in §6 frozen and everything in §7 deferred / not adopted;
- frames "useful evidence" (§8) as prereg ADEQUACY (pre-specifiable, jointly sufficient, non-fittable, Codex-
  accepted) -- NOT a pass, threshold, closure, or validity statement -- and §9 leaves vision / descriptor validity /
  temporal order / real-video / memory / runtime / integration / closure UNPROVEN;
- recommends completing the preregistration path first (Codex review; do NOT pivot to flat geometry until this
  proposal exists/accepted) and lists next branches A/B/C/D docs-first, opening none;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any adopted metric / threshold / pass-fail rule, any equation definition, any TOL redefinition, any descriptor
redesign, any family expansion, any spectral reopening as a closure group, any control weakening, any flat-geometry /
screen-analysis authorization, any claim that the wall is CLOSED (vs visible), any descriptor-validity / vision /
temporal-order claim, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY-Aware Closure Preregistration Proposal v1.1. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural / screen / flat-geometry work; changes no frozen formula, gate,
evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no threshold; redefines no
TOL; adopts no closure metric; defines no equation; proposes preregistration components only, adopting none; keeps
the wall visible not closed; makes no vision / descriptor-validity / temporal-order / memory / runtime /
integration claim; no `§0` pointer added; no tags.*
