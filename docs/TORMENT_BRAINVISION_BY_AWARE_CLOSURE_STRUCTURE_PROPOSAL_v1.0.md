# TORMENT Brainvision BY-Aware Closure Structure Proposal v1.0

## 1. Status / non-claims

**DOCS-ONLY proposal. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration
lane.** It proposes — for future, separately-gated consideration only — the candidate *requirements* a future
BY-aware closure structure would need to represent, so that a systematic blue-yellow opponent-axis offset
(`BY_axis_asymmetry`) cannot hide inside residual / `TOL` matching. It proposes **requirements only — it adopts
none**, defines no final pass/fail rules, and implements nothing. It **authorizes no code and no tests**,
invents no threshold, **redefines no `TOL`**, adopts **no new closure metric**, proposes no pass/fail rule
change, changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no control, redesigns no
descriptor, reopens no spectral group, expands no generator family, and opens **no classifier (form B) and no
neural encoder (form C)**. It does **not** pivot to flat / screen geometry and opens **no flat-geometry
implementation and no screen-analysis implementation**. Everything stays offline under `research/brainvision/`
+ `tests/research/`, HELD per v0.6.

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

## 2. Relation to v0.8a / v0.9 / v0.9b / v0.9c

```text
v0.8a (8977248)  BY-channel metric anatomy -> BY_axis_asymmetry (systematic opponent-axis offset).
v0.9  (6485e55)  BY opponent-axis closure PROPOSAL: candidate visibility requirements A-F, adopting none.
v0.9b (11a1997)  BY closure visibility AUDIT -> BY_visibility_confirmed (panels A-F make the offset visible).
v0.9c (c17ec74)  synthesis: visibility CONFIRMED, NOT closure; recommended a BY-aware closure structure proposal.
v1.0  (this doc) proposes the candidate BY-aware closure-STRUCTURE requirements, docs-only, adopting none.
```

This proposal is requirements-defining only. It does not prove Brainvision, validate the descriptor, invalidate
prior work, adopt a metric, or select flat / screen geometry. It changes nothing v0.4b/v0.4c/v0.7a froze or
v0.7b/v0.8a/v0.9b produced.

## 3. Closure-structure problem statement

```text
v0.9b made BY_axis_asymmetry EXPLICITLY VISIBLE via reporting panels layered ON TOP of the existing closure.
But the closure DECISION itself (per-pair L-inf over the ten matched stats <= TOL) still ignores the sign,
the across-pair consistency, and the binding role of the BY offset. So the offset is visible AFTER THE FACT yet
NOT REPRESENTED IN the closure structure. The problem this proposal addresses: what would a future closure /
audit DESIGN need to REPRESENT so that a systematic BY-axis offset is a first-class element of the design --
not a post-hoc panel -- and therefore cannot hide inside residual / TOL matching by construction?
```

## 4. Why visibility alone is insufficient

```text
- The v0.9b panels are a REPORTING layer over the SAME closure; they surface the offset but change no decision.
- The per-pair L-inf <= TOL closure is sign-blind and cross-pair-blind: a consistently-signed, BY-dominant,
  often-binding class-level offset can pass every pair while the classes stay ordered (v0.6a/v0.7b/v0.8a).
- Visibility (v0.9b) confirms the offset is there and surfaced; it does NOT make the offset a represented
  quantity in any closure/audit design that follows.
- Therefore the current proof route remains HELD: the BY-axis offset is VISIBLE but NOT CLOSED, and a future
  closure structure would need to REPRESENT the offset explicitly (this doc says WHAT, not HOW, and adopts nothing).
```

## 5. Candidate BY-aware closure requirements

Proposed for future consideration; **NONE adopted here**. Each says only what a future closure / audit *design*
should *represent*, not what decision it should make:

```text
A. Signed-offset representation
   A future closure / audit design SHOULD represent whether by_centroid, by_spread, and by_std retain systematic
   SIGNED offsets across matched pairs (sign + across-pair consistency, not just |residual|).
B. Opponent-axis dominance representation
   It SHOULD represent the comparison of BY magnitude against the RG and directional comparison features.
C. Binding-stat representation
   It SHOULD expose how often BY stats bind the residual match, especially by_std.
D. Aggregation-warning representation
   It SHOULD flag when group-level residual / TOL matching COEXISTS with a systematic BY ordering.
E. Coupling / leakage separation
   It SHOULD keep BY_axis_asymmetry SEPARATE from centroid/spread coupling and amplitude / channel-energy leakage.
F. Region / family caveat representation
   It SHOULD report whether BY persistence is region-specific or family-specific, INCLUDING the current
   single-matching-family (segment_paired_canceller) caveat.
G. Non-authorizing closure visibility
   It SHOULD keep BY visibility as evidence FOR DIAGNOSIS -- never as automatic descriptor validity or an
   automatic pass/fail authorization.
```

Each requirement is a **representational obligation** on a future design. Adopting any of them as a metric, a
pass/fail gate, or a threshold is explicitly **out of scope here** and would need a separate, separately-gated
decision.

## 6. What must remain frozen

```text
- TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30; CHANCE_BAND = 0.60 (referenced frozen; not re-thresholded).
- the frozen evaluator (structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR).
- the frozen descriptor / _stats / GROUPS / best-threshold BA / robustness lens.
- proxy_match_residual (L-inf over the ten matched stats, spectral excluded) and PSC < PSC_FLOOR feasibility.
- the closed F1-F5 family set; the v0.7b samples; spectral audit-note-only.
- claim locks and verdict HOLD.
This proposal freezes ALL of the above and only proposes representational REQUIREMENTS on a future design.
```

## 7. What a future audit may report

```text
- signed offsets + sign consistency (per BY feature); BY-vs-RG / directional dominance;
- BY-binding frequency (by_std / by_spread / by_centroid separated);
- an aggregation warning when per-pair TOL closure coexists with a systematic BY ordering;
- coupling / leakage separation (BY_axis_asymmetry vs coupling vs amplitude);
- region / family concentration, WITH the single-matching-family caveat;
- protocol_ok and a claim-lock summary (locks False; verdict HOLD).
```

All such reporting is diagnostic (per requirement G); it decides nothing and moves no claim lock or verdict.

## 8. Forbidden interpretations

```text
- SAY: the current proof route remains HELD because the BY-axis offset is VISIBLE but NOT CLOSED.
- Do NOT say Brainvision failed or Brainvision succeeded.
- Do NOT say the descriptor is valid or that vision is proven.
- Do NOT say flat geometry is selected or that screen analysis is opened.
- This is NOT a new closure metric; it changes NO pass/fail rule; it invents NO threshold; it redefines NO TOL;
  it redesigns NO descriptor; it expands NO family; it reopens NO spectral group.
- It does NOT bring memory / runtime / integration closer and moves NO claim lock or verdict.
```

## 9. What would count as useful evidence

The evidence a future BY-aware closure structure would provide is that the BY-axis offset is **represented
explicitly in the design** — **not** a pass, a new threshold, or a validity statement:

```text
- If the requirements (A-G) are representable and testable over the existing records, a future closure / audit
  DESIGN could make the systematic BY offset a first-class, diagnosable element rather than a post-hoc panel --
  so BY_axis_asymmetry could not hide inside residual / TOL matching by construction.
- Requirement G ensures any such visibility stays diagnostic and never becomes automatic validity or pass/fail.
```

Representing the offset is a design-layer improvement; it upgrades no claim and moves no verdict (§10).

## 10. What would still not be proven

Even a future BY-aware closure structure that represents all of these requirements would leave all of the
following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

Representing a synthetic BY-axis offset in a closure design is an in-vitro, metric-level design step within the
same family set; it says nothing about real clips or screens and does not validate the descriptor. The proof
route remains **HELD / HOLD** because the offset is visible but not closed. The claim locks
(`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`, `descriptor_validity_claim_allowed`)
and `verdict = HOLD` remain in force.

## 11. Candidate next branches

```text
A. BY-aware closure AUDIT PLAN
   Docs-first. Turn these requirements into a concrete audit plan over the existing records, still WITHOUT
   adopting a metric.
B. BY-aware closure metric PRE-REGISTRATION
   Docs-first. ONLY later, if needed, propose candidate metric components / reporting structure before any code.
C. Flat opponent-plane / spatial FIELD proposal
   Docs-first. Still a candidate, but only AFTER the BY closure-structure requirements are clear. Conceptual;
   no screen / flat-geometry implementation.
D. Operator / new-math NOTE
   Docs-first. Ask the operator to propose intuition / math only AFTER the closure requirements are written clearly.
E. Pause Brainvision and return to TORMENT memory / kernel work.
```

## 12. Recommended next step

**Recommend Branch A (BY-aware closure audit plan) first, docs-first, after Codex accepts this proposal.** v0.9b
made `BY_axis_asymmetry` visible; v1.0 defines what a closure structure must **represent**. The next clean move
after v1.0 is to **plan an audit around those requirements** — not to adopt a metric (B), pivot geometry (C), or
inject new math (D) yet. A keeps the work grounded in the closure requirements this proposal defines; B / C / D
are best taken only once A has turned the requirements into a concrete audit. E (pause) remains a legitimate
operator call.

```text
1. Codex review THIS proposal (docs-only; over committed edge c17ec74).
2. If accepted, commit this proposal doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first audit PLAN (reporting-only;
   no metric adopted, no threshold, no descriptor change). This proposal opens no code and authorizes no
   implementation (and no screen / flat-geometry work).
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_AWARE_CLOSURE_STRUCTURE_PROPOSAL_v1.0.md
(new, docs-only, untracked; over committed edge c17ec74, proposing BY-aware closure-structure requirements from v0.9c).

Verify that this proposal:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED; and
  authorizes NO flat-geometry and NO screen-analysis implementation;
- proposes candidate BY-aware closure REQUIREMENTS ONLY and ADOPTS NONE -- it defines no final pass/fail rules,
  invents no threshold, redefines no TOL, adopts no new closure metric, redesigns no descriptor, expands no family,
  and reopens no spectral group;
- states the problem correctly: v0.9b made the offset VISIBLE via panels layered on the SAME closure, but the
  closure decision is sign-blind / cross-pair-blind, so a future closure DESIGN would need to REPRESENT the BY
  offset explicitly (WHAT, not HOW);
- lists requirements A-G (signed-offset / opponent-axis dominance / binding-stat / aggregation-warning / coupling-
  leakage separation / region-family caveat / non-authorizing closure visibility) as representational obligations,
  not decisions, and keeps everything in §6 frozen;
- frames it correctly: the proof route remains HELD because the BY offset is VISIBLE but NOT CLOSED; it does NOT
  say Brainvision failed / succeeded / descriptor valid / vision proven / flat geometry selected / screen analysis opened;
- recommends Branch A (BY-aware closure audit plan) first, docs-first, and lists A/B/C/D/E; reasons that v1.0 defines
  what a closure must represent and the next move is to plan an audit around it, not adopt a metric or pivot geometry;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any adopted metric / threshold / pass-fail rule, any TOL redefinition, any descriptor redesign, any family
expansion, any flat-geometry / screen-analysis authorization, any claim that the wall is CLOSED (vs visible), any
descriptor-validity / vision claim, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY-Aware Closure Structure Proposal v1.0. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural / screen / flat-geometry work; changes no frozen formula,
gate, evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no threshold;
redefines no TOL; adopts no closure metric; proposes requirements only, adopting none; keeps the wall visible not
closed; makes no vision / descriptor-validity / temporal-order / memory / runtime / integration claim; no `§0`
pointer added; no tags.*
