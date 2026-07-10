# TORMENT Brainvision BY Opponent-Axis Closure Audit Synthesis v0.9c

## 1. Status / non-claims

**DOCS-ONLY synthesis / next-decision note. Non-authorizing, non-implementing. Opens no code, no tests, no
runtime, no integration lane.** It records what the v0.9b BY opponent-axis closure visibility audit means and
what research question comes next. It **authorizes no code and no tests**, invents no threshold, **redefines no
`TOL`**, adopts **no new closure metric**, proposes no pass/fail rule change, changes no formula / §7 anti-proxy
logic / §8 verdict logic, deletes or weakens no control, redesigns no descriptor, reopens no spectral group,
expands no generator family, and opens **no classifier (form B) and no neural encoder (form C)**. It does **not**
pivot to flat / screen geometry and opens **no flat-geometry implementation and no screen-analysis
implementation**. Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. A synthesis alone moves nothing: **no
claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v0.8a / v0.8b / v0.9 / v0.9a / v0.9b

```text
v0.8a (8977248)  BY-channel metric anatomy -> BY_axis_asymmetry (systematic opponent-axis offset).
v0.8b (ea20804)  synthesis: sharpened the wall; flat geometry only a future framing.
v0.9  (6485e55)  BY opponent-axis closure PROPOSAL: candidate visibility requirements A-F, adopting none.
v0.9a (3aba63d)  BY opponent-axis closure AUDIT PLAN: reporting-only panels A-F over existing records.
v0.9b (11a1997)  IMPLEMENTED and ran the panels (form A, non-learning, reporting-only) -> BY_visibility_confirmed.
v0.9c (this doc) synthesizes v0.9b and recommends the next research question.
```

v0.9b is reporting-only: it makes the wall **visible**, it does not close it, prove Brainvision, validate the
descriptor, or select flat / screen geometry. This note changes nothing v0.4b/v0.4c/v0.7a froze or v0.7b/v0.8a
produced.

## 3. Windows repo truth

Windows pytest is the source of truth. Recorded verbatim:

```text
python -m pytest tests/research/test_brainvision_by_opponent_axis_closure_audit_v0_9b.py -q
  12 passed in 3.84s

python research/brainvision/run_by_opponent_axis_closure_audit_v0_9b.py
  OUTCOME_LABEL: BY_visibility_confirmed   verdict: HOLD   locks: False False False   protocol_ok: True
  A signed-offset:  by_std +0.04505 (0.95)  by_centroid -0.03393 (0.90)  by_spread -0.02935 (0.84)
  B BY-vs-RG dominance = True
  C binding: by_centroid 1, by_spread 1, by_std 10  | by_binding_fraction 0.6316
  D region: speed 0.75, phase 1.0, radius 1.0 | family {segment_paired_canceller: 19} | single_family_caveat True
  E coupling 0.0315 | amplitude {chroma_mag 0.2916, rg_std 0.1832} | dominant_mechanism BY_axis_asymmetry
  F aggregation_warning = True
  new_closure_metric_adopted = False  |  pass_fail_gate_introduced = False

python -m pytest tests/research -q
  312 passed in 58.54s
```

(The one `spectral_centroid` Linux/Windows knife-edge test that fails in the Linux sandbox passes on Windows,
hence 312 passed here.)

## 4. v0.9b result summary

v0.9b was **protocol-clean** (`protocol_ok = True`). It **reused the v0.8a / v0.7b records by identity** (via the
v0.8a anatomy, which reproduces the v0.7b sealed matching), **implemented panels A-F as reporting-only visibility
panels**, **adopted no new closure metric**, **introduced no pass/fail gate**, and **changed no `TOL`,
thresholds, descriptor, `GROUPS`, evaluator, spectral status, families, samples, or claim locks**. Outcome:
**`BY_visibility_confirmed`**. Verdict **HOLD**; claim locks all False.

## 5. Meaning of BY_visibility_confirmed

```text
BY_visibility_confirmed means the panels make the systematic blue-yellow opponent-axis offset EXPLICITLY VISIBLE
in one place. It CONFIRMS VISIBILITY of the wall -- NOT CLOSURE of the wall.
```

The systematic BY offset still **survives** the per-pair residual / `TOL` match exactly as before; v0.9b did not
close it, weaken it, or change any decision about it. What changed is that the offset — its signs, its
BY-dominance, its binding frequency, its coexistence with the passing closure — is now **surfaced in a dedicated
panel layer** rather than compressed inside the group-level L-inf / `TOL` summary. This is a **reporting-layer
improvement**; it establishes **no** vision, descriptor validity, closure, or real-world property (§10), and it
moves no claim lock and no verdict.

## 6. What v0.9b makes visible

```text
A. Signed offsets       by_centroid -0.034 (0.90), by_spread -0.029 (0.84), by_std +0.045 (0.95) -- systematically signed.
B. BY dominance         BY effects (46-71% of TOL) dominate RG (0-4%) and directional (6%).
C. BY binding           BY stats bind the L-inf in 12/19 pairs (by_std 10); BY-binding fraction 0.63 > share 0.30.
D. Region visibility     BY persists across phase / radius (BA 1.0), weaker in speed (0.75); single-family caveat surfaced.
E. Coupling/leakage sep  coupling 0.03 and amplitude 0.29/0.18 stay weak; BY_axis_asymmetry the dominant mechanism.
F. Aggregation warning   per-pair TOL closure COEXISTS with a systematic BY signed ordering (the compression is flagged).
```

Together the panels make explicit the exact structure the current closure hides: a directional, consistently-
signed, BY-dominant, often-binding class-level offset that a per-pair L-inf `<= TOL` match passes.

## 7. What remains unresolved

```text
- WHAT a future closure STRUCTURE would need to REPRESENT so a systematic BY offset cannot hide inside per-pair
  residual / TOL matching -- without adopting a metric here.
- WHETHER that is a within-descriptor closure change, a flat opponent-plane / spatial-field geometry pivot, or a
  new-math framing -- an operator / design question, not settled by these records.
- WHETHER the single-matching-family (segment_paired_canceller) limitation hides any cross-family BY structure.
- (spectral stays audit-note-only and is not implicated.)
```

None of these is resolved by v0.9b, and none is resolved by this synthesis.

## 8. Candidate next branches

```text
A. BY-aware closure STRUCTURE proposal
   Docs-first. Ask what a future closure structure would need to INCLUDE so a systematic BY offset cannot hide,
   WITHOUT adopting the metric yet. No threshold, no metric adoption, no descriptor redesign.
B. Flat opponent-plane / spatial FIELD proposal
   Docs-first. Explore whether a screen-oriented Brainvision should move toward 2D opponent-field geometry --
   CONCEPTUAL and non-authorizing; no screen / flat-geometry implementation.
C. Operator / new-math NOTE
   Docs-first. Invite operator intuition now that the BY wall is visible and localized.
D. Pause Brainvision and return to TORMENT memory / kernel work.
```

## 9. Recommended next step

**Recommend Branch A (BY-aware closure structure proposal) first, docs-first, after Codex accepts this
synthesis.** v0.9b made the BY wall **visible** but did not **close** it. The next evidence-based step is to
propose what a future closure structure would need to **represent** — *before* any metric adoption, flat-geometry
pivot (B), or new-math injection (C). A keeps the work grounded in the closure problem the audit surfaced; B and
C are best informed once A articulates what closure would need. D (pause) remains a legitimate operator call.

```text
1. Codex review THIS synthesis (docs-only; over committed edge 11a1997).
2. If accepted, commit this synthesis doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first proposal (requirements-
   defining only; no metric adopted, no threshold, no descriptor change). This synthesis opens no code and
   authorizes no implementation (and no screen / flat-geometry work).
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

## 10. What would still not be proven

Even a completed Branch-A proposal (or a future closure structure) would leave all of the following
**unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

Making the BY-axis offset visible, and proposing what a closure would need to represent, are in-vitro,
metric-level reporting / design steps within the same family set; they say nothing about real clips or screens
and do not validate the descriptor. The proof route remains **HELD / HOLD**. The claim locks
(`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`, `descriptor_validity_claim_allowed`)
and `verdict = HOLD` remain in force.

## 11. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_OPPONENT_AXIS_CLOSURE_AUDIT_SYNTHESIS_v0.9c.md
(new, docs-only, untracked; over committed edge 11a1997, synthesizing the v0.9b BY closure visibility audit).

Verify that this synthesis:
- is docs-only and opens no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED; and
  authorizes NO flat-geometry and NO screen-analysis implementation;
- records Windows repo truth faithfully (12 passed; BY_visibility_confirmed; panels A-F values; new_closure_metric
  and pass_fail_gate False; protocol_ok True; verdict HOLD; locks False; full suite 312 passed on Windows);
- states that v0.9b was protocol-clean, reused v0.8a / v0.7b records by identity, implemented panels A-F as
  reporting-only, adopted no new closure metric, introduced no pass/fail gate, and changed no TOL / thresholds /
  descriptor / GROUPS / evaluator / spectral status / families / samples / claim locks;
- makes the key distinction: BY_visibility_confirmed CONFIRMS VISIBILITY of the wall, NOT CLOSURE -- the offset
  still survives the residual/TOL match; only its surfacing changed (reporting-layer improvement);
- lists what v0.9b makes visible (signed offsets, BY dominance, BY binding, region visibility, coupling/leakage
  separation, aggregation warning), with the single-matching-family caveat;
- recommends Branch A (BY-aware closure structure proposal) first, docs-first, and lists A/B/C/D; reasons that the
  wall is visible but not closed, so the next step is to propose what a closure would need to represent BEFORE any
  metric adoption, flat-geometry pivot, or new-math injection; adopts no metric / threshold / TOL change;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any claim that the wall is CLOSED (vs merely visible), any adopted metric / threshold / pass-fail change, any
TOL redefinition, any flat-geometry / screen-analysis authorization, any descriptor-validity / vision claim, any
claim-lock/verdict movement, or any misrecording of the Windows truth.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY Opponent-Axis Closure Audit Synthesis v0.9c. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural / screen / flat-geometry work; changes no frozen formula,
gate, evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no threshold;
redefines no TOL; adopts no closure metric; confirms visibility not closure; makes no vision /
descriptor-validity / temporal-order / memory / runtime / integration claim; no `§0` pointer added; no tags.*
