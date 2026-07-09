# TORMENT Brainvision BY-Channel Metric Anatomy Synthesis v0.8b

## 1. Status / non-claims

**DOCS-ONLY synthesis / next-decision note. Non-authorizing, non-implementing. Opens no code, no tests, no
runtime, no integration lane.** It records what the v0.8a BY-channel metric anatomy means and what research
question comes next. It **authorizes no code and no tests**, invents no threshold, **redefines no `TOL`**,
adopts **no new closure metric**, proposes no pass/fail rule change, changes no formula / §7 anti-proxy logic /
§8 verdict logic, deletes or weakens no control, redesigns no descriptor, reopens no spectral group, expands no
generator family, and opens **no classifier (form B) and no neural encoder (form C)**. In particular it
authorizes **no screen-analysis implementation and no flat-geometry implementation** — the screen-oriented
direction discussed in §7 is a *possible future research framing only*, not a build. Everything stays offline
under `research/brainvision/` + `tests/research/`, HELD per v0.6.

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

## 2. Relation to v0.7b / v0.7c / v0.8 / v0.8a

```text
v0.7b (978bb36)  larger-N replication -> BY_persistence_metric_insufficiency: BY-channel persists substantial.
v0.7c (ca3a95f)  synthesis: localized the wall to BY-channel opponent-axis geometry; recommended Branch A.
v0.8  (c0c5040)  BY-channel metric anatomy PLAN.
v0.8a (8977248)  IMPLEMENTED and ran it (form A, non-learning, explanatory-only) -> BY_axis_asymmetry.
v0.8b (this doc) synthesizes v0.8a and recommends the next research question.
```

v0.8a is explanatory: it characterizes the localized wall, it does not prove Brainvision, validate the
descriptor, or invalidate prior work. This note changes nothing v0.4b/v0.4c/v0.7a froze or v0.7b/v0.8a produced.

## 3. Windows repo truth

Windows pytest is the source of truth. Recorded verbatim:

```text
python -m pytest tests/research/test_brainvision_by_channel_metric_anatomy_v0_8a.py -q
  11 passed in 3.49s

python research/brainvision/run_by_channel_metric_anatomy_v0_8a.py
  OUTCOME_LABEL: BY_axis_asymmetry   protocol_ok: True   verdict: HOLD   locks: False False False
  replication evals 1056 | matched 19 | unmatched 5 | reproduces v0.7b: True | BY_dominant: True
  effect (|smd|/TOL): by_std 71%  by_centroid 54%  by_spread 46%  >>  rg_centroid 0%  rg_spread 4%  directional 6%
  BY sign consistency mean 0.895: by_centroid 0.90 (median -0.03393), by_spread 0.84 (median -0.02935),
                                  by_std 0.95 (median +0.04505)
  centroid/spread coupling Spearman 0.0315 | by_std ~ amplitude Spearman {chroma_mag 0.2916, rg_std 0.1832}
  matched family distribution {segment_paired_canceller: 19} | BY-binding L-inf fraction 0.6316
  mechanism scores: BY_axis_asymmetry 0.7893 > BY_metric_compression 0.3316 > BY_amplitude_leakage 0.2916
                    > BY_centroid_spread_coupling 0.0315

python -m pytest tests/research -q
  300 passed in 55.77s
```

(The one `spectral_centroid` Linux/Windows knife-edge test that fails in the Linux sandbox passes on Windows,
hence 300 passed here.)

## 4. v0.8a result summary

v0.8a was **protocol-clean** (`protocol_ok = True`) and **reproduced v0.7b exactly** (19 matched, 5 unmatched;
`reproduces_v0_7b = True`). It **preserved `TOL`, thresholds, the descriptor, `GROUPS`, the evaluator, spectral
audit-note-only, the F1-F5 families, the v0.7b samples, and the claim locks** — it reran nothing with new
parameters and replaced no sample. Outcome: **`BY_axis_asymmetry`**. Verdict **HOLD**; claim locks all False.

## 5. Meaning of BY_axis_asymmetry

The surviving BY separability is a **systematic blue-yellow opponent-axis offset** under the existing
residual / `TOL` metric:

```text
- BY-channel effects DOMINATE the RG and directional comparison features (by_std 71% / by_centroid 54% /
  by_spread 46% of TOL, vs rg 0-4% and directional 6%).
- BY differences are SYSTEMATICALLY SIGNED: winders are consistently LOWER on by_centroid / by_spread
  (sign-consistency 0.90 / 0.84, median diffs -0.034 / -0.029) and consistently HIGHER on by_std
  (sign-consistency 0.95, median diff +0.045) than their matched cancellers -- even though every pair matches
  within TOL.
- BY statistics OFTEN BIND the residual match: the BY-binding L-inf fraction is 0.63 (by_std is the binding stat
  in 10 of 19 pairs), so the per-pair L-inf leaves the class-level BY offset unclosed.
```

So the persisting wall is a **consistent, directional (static) offset on the blue-yellow opponent axis** that a
per-pair L-inf `<= TOL` match does not close. This is a research-only characterization; it establishes **no**
vision, descriptor validity, or real-world property (§12).

## 6. What v0.8a ruled down

```text
- centroid/spread COUPLING: WEAK (Spearman 0.0315) -> the persistence is NOT a coupled by_centroid/by_spread
  geometry the metric fails to separate.
- by_std AMPLITUDE / channel-energy LEAKAGE: WEAK-to-MODERATE (Spearman chroma_mag 0.29 / rg_std 0.18) -> by_std
  behaves more geometrically than as an amplitude proxy; amplitude leakage is NOT the dominant explanation.
- FAMILY artifact: NOT assessable -- all 19 matches are segment_paired_canceller, so BY persistence cannot be
  compared across matching families (single matching family); family comparison remains limited.
- (v0.7b already ruled the earlier perfect BA = 1.0 saturation as small-N; that is not the BY story.)
```

By comparative argmax of the [0,1] mechanism scores, `BY_axis_asymmetry` (0.79) dominates the alternatives
(compression 0.33, amplitude 0.29, coupling 0.03), so the axis-offset reading is the best-supported.

## 7. Screen-oriented flat-geometry implication

**Possible future research direction only — NOT a claim and NOT an implementation authorization.** The
persisting residual is a *static, systematic offset* on the blue-yellow opponent axis — precisely the kind of
structure a **chroma-trajectory / winding** descriptor is built *not* to represent (winding measures rotational
path structure, not a flat directional field offset). This *may* suggest that a future, screen-oriented
Brainvision direction should consider **flat opponent-plane / spatial field geometry** (2D opponent-field
structure) rather than only chroma-trajectory / winding geometry. This is recorded strictly as a **possibility
to be framed later, docs-first** — it opens **no** screen-analysis work, **no** flat-geometry implementation,
**no** camera / screen / streaming path, and moves no claim or verdict. The proof route remains HELD / HOLD.

## 8. What v0.8a newly teaches

```text
v0.7c said:  the wall is localized to BY-channel opponent-axis geometry.
v0.8a says:  that wall is specifically a SYSTEMATIC, CONSISTENTLY-SIGNED, STATIC blue-yellow axis OFFSET that
             often binds the per-pair L-inf match yet is not closed by it -- and it is NOT coupling and NOT
             amplitude leakage.
```

So the wall is now **characterized**, not just localized: a directional opponent-axis offset the winding-based
residual/TOL metric structurally leaves open. That characterization is what motivates the §7 possibility (a flat
opponent-field geometry may be the right frame for a future screen-oriented target) and the §10 branches. It is a
genuinely new, honest characterization — and it upgrades **no** claim (§12).

## 9. What remains unresolved

```text
- WHAT a closure structure would need to represent so that a systematic BY-axis offset is not hidden by the
  per-pair residual / TOL match (deferred; no metric adopted here).
- WHETHER the eventual screen-oriented target is flat opponent-FIELD geometry, local patches, opponent-axis
  gradients, or chroma-trajectory structure -- an operator / new-math question, not settled by these records.
- WHETHER the single-matching-family (segment_paired_canceller) limitation hides any cross-family BY structure.
- (spectral stays audit-note-only and is not implicated.)
```

None of these is resolved by v0.8a, and none is resolved by this synthesis.

## 10. Candidate next branches

```text
A. BY opponent-axis closure PROPOSAL
   Docs-first. Ask what a closure would need to represent so a systematic BY-axis offset is not hidden by
   residual / TOL matching. No threshold adoption; no metric adopted.
B. Flat opponent-plane / spatial FIELD geometry PROPOSAL
   Docs-first. Ask whether a screen-oriented Brainvision should pivot from chroma-trajectory / winding fixtures
   toward 2D opponent-field geometry. FRAMING ONLY; no screen / flat-geometry implementation.
C. Operator / new-math intuition NOTE
   Docs-first. Ask the operator to describe the intended screen-analysis geometry -- flat field structure, local
   patches, opponent-axis gradients, or something else. Captures intent before any framing / math.
D. Pause Brainvision and return to TORMENT memory / kernel work
   Accept the characterized wall as a clean stopping point and redirect effort to another TORMENT layer.
```

## 11. Recommended next step

**Recommend B or C next — docs-first, not immediate code.** The wall is now characterized enough that the
useful next move is to frame the geometry question, not run another diagnostic on the same records. If choosing
one:

```text
- Recommend C FIRST if the operator wants to inject intuition / new math now (capture the intended screen-
  analysis geometry before Claude/Codex frame a proposal).
- Recommend B FIRST if we want Claude / Codex to frame a formal flat-opponent-field proposal before operator math.
- A remains available (BY closure proposal) and D (pause) remains a legitimate operator call.

1. Codex review THIS synthesis (docs-only; over committed edge 8977248).
2. If accepted, commit this synthesis doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open B or C as a SEPARATE, future, docs-first note. This synthesis opens
   no code and authorizes no implementation (and no screen / flat-geometry work).
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, §0, or tag work is recommended or authorized here.
```

## 12. What would still not be proven

Even a completed B / C framing (or a future closure proposal) would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

Characterizing the BY persistence as an opponent-axis offset is an in-vitro synthetic, metric-level description
within the same family set; it says nothing about real clips or screens and does not validate the descriptor.
The proof route remains **HELD / HOLD**. The claim locks (`first_pass_structure_validity_claim_allowed`,
`temporal_claim_allowed`, `descriptor_validity_claim_allowed`) and `verdict = HOLD` remain in force.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_CHANNEL_METRIC_ANATOMY_SYNTHESIS_v0.8b.md
(new, docs-only, untracked; over committed edge 8977248, synthesizing the v0.8a BY-channel anatomy).

Verify that this synthesis:
- is docs-only and opens no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED; and
  authorizes NO screen-analysis and NO flat-geometry implementation;
- records Windows repo truth faithfully (11 passed; BY_axis_asymmetry; reproduces v0.7b; BY_dominant; effect
  sizes; sign consistencies; coupling 0.0315; by_std amplitude 0.29/0.18; single matching family; BY-binding
  0.6316; mechanism scores; protocol_ok True; verdict HOLD; locks False; full suite 300 passed on Windows);
- states that v0.8a was protocol-clean, reproduced v0.7b exactly, and preserved TOL / thresholds / descriptor /
  GROUPS / evaluator / spectral-audit-note-only / families / samples / claim locks;
- describes the outcome as a SYSTEMATIC blue-yellow opponent-axis OFFSET (BY dominates RG/directional; winders
  lower by_centroid/by_spread, higher by_std; BY often binds the L-inf), and RULES DOWN coupling (weak 0.03) and
  amplitude leakage (weak-moderate 0.29/0.18) as the dominant explanation, noting the single-family limitation;
- frames the screen-oriented flat opponent-plane / spatial field geometry idea STRICTLY as a possible future
  research direction -- NOT a claim, NOT an implementation authorization, and opens no screen / flat-geometry work;
- recommends B or C docs-first next (C first if operator injects math; B first for a formal proposal), lists
  A/B/C/D, and opens no code, invents no threshold, adopts no closure metric, redefines no TOL;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any descriptor-validity / vision claim, any screen or flat-geometry implementation authorization, any
threshold invention, any TOL redefinition, any closure-metric adoption, any claim-lock/verdict movement, or any
misrecording of the Windows truth.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY-Channel Metric Anatomy Synthesis v0.8b. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural / screen / flat-geometry work; changes no frozen formula,
gate, evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no threshold;
redefines no TOL; adopts no closure metric; makes no vision / descriptor-validity / temporal-order / memory /
runtime / integration claim; no `§0` pointer added; no tags.*
