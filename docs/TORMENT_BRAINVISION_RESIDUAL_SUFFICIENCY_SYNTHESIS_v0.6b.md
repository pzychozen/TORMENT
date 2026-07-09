# TORMENT Brainvision Residual Sufficiency Synthesis v0.6b

## 1. Status / non-claims

**DOCS-ONLY synthesis / next-decision note. Non-authorizing, non-implementing. Opens no code, no tests, no
runtime, no integration lane.** It records what the v0.6a residual-sufficiency audit means and what research
question comes next. It **authorizes no code and no tests**, invents no threshold, **redefines no `TOL`**,
proposes no pass/fail rule change, changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes or
weakens no control, redesigns no descriptor, reopens no spectral group, reruns / replaces no v0.4d sealed
candidate, adds no generator family, and opens **no classifier (form B) and no neural encoder (form C)**.
Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. It does **not** say v0.4d was invalid,
does **not** say Brainvision failed or succeeded. A synthesis alone moves nothing: **no claim lock and no
verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v0.4d / v0.5a / v0.5b / v0.6 / v0.6a

```text
v0.4d (77ed133)  Partial: 3/3 held-out matched within TOL (per-pair L-inf), yet the four matched cheap-baseline
                 groups still separated.
v0.5a (37a75f7)  baseline anatomy -> distributed_residual_geometry; protocol_metric_mismatch_flag = True.
v0.5b (b5d6676)  synthesis: v0.5a explains (not invalidates) v0.4d Partial; the wall is a closure-metric
                 sufficiency gap; recommended Branch A.
v0.6  (9c73799)  residual sufficiency audit PLAN.
v0.6a (910ab34)  IMPLEMENTED and ran the audit (form A, non-learning, explanatory-only) -> mixed_metric_and_small_n.
v0.6b (this doc) synthesizes v0.6a and recommends the next research question.
```

**v0.6a does NOT invalidate v0.4d.** v0.4d's residual / `TOL` match was real under the declared metric; v0.6a
shows that this metric was **insufficient** to close feature-level adversarial separability, while **also**
showing that some of the surviving separability is a small-N (n = 3 vs 3) artifact. This note changes nothing
v0.4b/v0.4c froze or v0.4d/v0.5a produced.

## 3. Windows repo truth

Windows pytest is the source of truth. Recorded verbatim:

```text
python -m pytest tests/research/test_brainvision_residual_sufficiency_v0_6a.py -q
  13 passed in 0.64s

python research/brainvision/run_residual_sufficiency_v0_6a.py
  OUTCOME_LABEL: mixed_metric_and_small_n   protocol_ok: True   verdict: HOLD   locks: False False False
  metric_insufficiency_features = [u_directional_delta_rms, angular_increment_mag, by_centroid, by_spread]
  small_n_optimism_features     = [by_std, rg_centroid, rg_spread]

python -m pytest tests/research -q
  275 passed in 48.20s
```

(The one `spectral_centroid` Linux/Windows knife-edge test that fails in the Linux sandbox passes on Windows,
hence 275 passed here.)

## 4. v0.6a result summary

v0.6a was **protocol-clean** (`protocol_ok = True`). It **reused the v0.4d / v0.5a records by identity** (the
exact sealed matched held-out pairs, reproducing residuals 0.045 / 0.036 / 0.060), **did not redefine `TOL`**,
**invented no threshold** (the metric-insufficiency vs small-N distinction uses a parameter-free robustness lens
— between-class rank gap vs within-class spread, boundary 1.0 — applied to no closure decision), kept
**spectral audit-note-only**, and **preserved the v0.4d candidates / pairs** (reran nothing with new
parameters, replaced no pair, changed no family / grid / seed). It answered the core audit question: **residual
closeness does coexist with feature-level separability.** Outcome: **`mixed_metric_and_small_n`**. Verdict
**HOLD**; claim locks all False.

## 5. Meaning of mixed_metric_and_small_n

Both mechanisms behind the surviving separability are present:

```text
- METRIC INSUFFICIENCY: robust class separation (between-class rank gap >= within-class spread) survived the
  per-pair L-inf <= TOL match. These are genuine class-level differences the closure metric did not close.
- SMALL-N OPTIMISM: other BA = 1.0 effects are fragile thin-margin separations (rank gap far below the
  within-class spread) that saturate best-threshold BA only because n = 3 vs 3.
```

So the surviving separability is **partly real (a metric-level gap) and partly a sample-size artifact.** The
v0.4d per-pair L-inf `<= TOL` match was real, but it was **not sufficient** to close robust class separation in
several feature dimensions; at the same time, some of the apparent separability is thin-margin small-N.

## 6. Metric-insufficiency features

```text
by_centroid   robust (rank gap ~6.6x within-class spread), signed median diff ~54% of TOL
by_spread     robust (rank gap ~7.3x within-class spread), signed median diff ~46% of TOL
u_directional_delta_rms   robust-constant (zero within-class spread) but NEGLIGIBLE magnitude (~6% of TOL)
angular_increment_mag     robust-constant but NEGLIGIBLE magnitude (~6% of TOL)
```

The **substantive** metric-insufficiency evidence is the **BY-channel** statistics (`by_centroid`,
`by_spread`): real class-level differences of ~50% of `TOL` that a per-pair L-inf `<= TOL` match let through.
The directional pair is robustly consistent but of negligible magnitude, so it should not be over-weighted.
This matches v0.5a's effect-size concentration in the BY-channel.

## 7. Small-N optimism features

```text
by_std        fragile (rank gap ~0.06x within-class spread) -> thin-margin BA saturation
rg_centroid   fragile (~0.004x) -> near-zero class gap yet BA at ceiling
rg_spread     fragile (~0.12x) -> thin-margin BA saturation
```

These reach best-threshold BA = 1.00 only because at n = 3 vs 3 the three winder values happen to fall on one
side of the three candidate values by a thin margin. Their apparent separability is not robust and is the
signature to test by increasing sample support.

## 8. What v0.6a newly teaches

```text
v0.5b said:  the wall is a closure-metric sufficiency gap.
v0.6a says:  that gap is PARTLY REAL -- robust BY-channel class separation the per-pair L-inf<=TOL did not close
             -- and PARTLY a small-N artifact (thin-margin BA saturation at n=3 vs 3). The two are separable by
             a parameter-free robustness lens.
```

So the research wall is now **better characterized**: it has two distinguishable components — a genuine
metric-sufficiency gap localized to BY-channel statistics, and a sample-size confound. This tells us the next
lever must **first** disentangle these (does the robust separability survive, and does the fragile separability
collapse, at larger n?) **before** changing the closure metric or expanding generator families. This is a
genuinely new, honest characterization — and it upgrades **no** claim (§12): it is an in-vitro synthetic,
metric-level observation within one sealed enumeration.

## 9. What remains unresolved

```text
- WHICH separability effects survive at larger n: do the robust BY-channel separations (by_centroid / by_spread)
  persist, and do the fragile ones (by_std / rg_centroid / rg_spread) collapse, when sample support increases?
- WHETHER a stricter closure metric is warranted -- deferred until the small-N confound is separated out.
- WHETHER the robust-but-negligible directional differences matter at all at larger n.
- (spectral stays audit-note-only and is not implicated.)
```

None of these is resolved by v0.6a, and none is resolved by this synthesis.

## 10. Candidate next branches

```text
A. Larger-N residual sufficiency replication plan
   Increase sample support to distinguish robust feature separability from tiny-n BA optimism. Docs-first; no
   immediate code; no new threshold; no descriptor redesign; no new generator families.
   Pro: directly separates the two mechanisms v0.6a found; the cleanest next question before any metric change.
   Con: needs a way to raise n while preserving the sealed enumeration's spirit and the claim locks.

B. Multi-feature closure metric proposal
   Propose a stricter future closure structure using feature anatomy, rank-order separation, signed median
   differences, and group residuals. Docs-first; NO threshold adoption yet.
   Pro: could define a closure metric matching what the baselines exploit.
   Con: premature before A separates real metric insufficiency from small-N; risks proposing a metric tuned to
        a small-N artifact.

C. Candidate-family expansion amendment
   A reviewed docs-only amendment adding non-winder families.
   Pro: could reduce the BY-channel effect-size residual.
   Con: NOT recommended yet -- adding families before resolving the metric / small-N question may just produce
        prettier Partial results.

D. Pause Brainvision and return to TORMENT memory / kernel work
   Accept the characterization as a clean stopping point and redirect effort to another TORMENT layer.
   Pro: reasonable if the operator wants to digest before more diagnostics.
   Con: leaves the larger-n question open.
```

## 11. Recommended next step

**Recommend Branch A (larger-N residual sufficiency replication plan) first, docs-first, after Codex accepts
this synthesis.** v0.6a found **both** robust metric insufficiency **and** small-N optimism; before changing the
metric (B) or expanding families (C), the clean next question is: **which separability effects survive when n is
larger?** A must precede B (so a future metric is not tuned to a small-N artifact) and C (so families are not
expanded against an unresolved confound). D (pause) remains a legitimate operator call.

```text
The future Branch-A plan (a SEPARATE, later docs-first step, not opened here) must NOT invent new pass
thresholds, must NOT redesign the descriptor, and must NOT expand generator families yet. It should only plan
HOW to increase n / sample support -- distinguishing robust feature separability from tiny-n BA optimism --
while preserving the existing claim locks and the offline quarantine.

1. Codex review THIS synthesis (docs-only; over committed edge 910ab34).
2. If accepted, commit this synthesis doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as that separate docs-first plan. This synthesis opens no
   code and authorizes no implementation.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, §0, or tag work is recommended or authorized here.
```

## 12. What would still not be proven

Even a completed larger-N replication would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

The current proof route remains **HELD / HOLD** because residual closure was insufficient and small-N effects
remain; the research wall is now better characterized, but that characterization is an in-vitro synthetic,
metric-level observation within one sealed enumeration. It says nothing about real clips and does not validate
the descriptor. The claim locks (`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`,
`descriptor_validity_claim_allowed`) and `verdict = HOLD` remain in force.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_RESIDUAL_SUFFICIENCY_SYNTHESIS_v0.6b.md
(new, docs-only, untracked; over committed edge 910ab34, synthesizing the v0.6a residual-sufficiency audit).

Verify that this synthesis:
- is docs-only and opens no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
- records Windows repo truth faithfully (13 passed; mixed_metric_and_small_n; protocol_ok True; verdict HOLD;
  locks False; metric-insufficiency and small-N feature lists; full suite 275 passed on Windows);
- states that v0.6a was protocol-clean, reused the v0.4d/v0.5a records by identity, did not redefine TOL,
  invented no threshold, kept spectral audit-note-only, preserved the v0.4d candidates/pairs, and found that
  residual closeness coexists with feature-level separability (outcome mixed_metric_and_small_n);
- frames it correctly: it does NOT say v0.4d was invalid (v0.4d's residual/TOL match was real under the declared
  metric, but v0.6a shows the metric was insufficient to close feature-level separability); it does NOT say
  Brainvision failed (the proof route remains HELD/HOLD because closure was insufficient and small-N effects
  remain); it does NOT say Brainvision succeeded (the wall is now better characterized);
- separates the substantive metric-insufficiency evidence (BY-channel by_centroid/by_spread, ~50% of TOL) from
  the robust-but-negligible directional pair and from the fragile small-N features (by_std/rg_centroid/rg_spread);
- recommends Branch A (larger-N residual sufficiency replication plan) first, docs-first, and lists A/B/C/D
  WITHOUT opening any code, inventing thresholds, redefining TOL, redesigning the descriptor, or expanding
  generator families; and requires the future Branch-A plan to preserve claim locks and offline quarantine;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD;
- makes no vision / "Brainvision sees" / temporal-order / descriptor-validity / memory-readiness /
  runtime-readiness / integration-readiness claim; adds no §0 pointer and no tags.

Flag any claim that v0.4d was invalid or that Brainvision failed/succeeded, any threshold invention, any TOL
redefinition, any implicit opening of B/C/runtime/memory/real-clips, any claim-lock/verdict movement, or any
misrecording of the Windows truth.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Residual Sufficiency Synthesis v0.6b. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural work; changes no frozen formula, gate, evaluator, or verdict;
deletes or weakens no control; redesigns no descriptor; invents no threshold; redefines no TOL; makes no vision
/ descriptor-validity / temporal-order / memory / runtime / integration claim; no `§0` pointer added; no tags.*
