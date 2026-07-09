# TORMENT Brainvision Larger-N Residual Replication Findings v0.7b

## 1. Status / non-claims

**DOCS-ONLY findings receipt for a REPORTING-ONLY, NON-LEARNING, EXPLANATORY form-A replication.** It records
what the v0.7b larger-N replication found when it ran the sealed v0.7a enumeration. It **changes no formula /
§7 anti-proxy logic / §8 verdict logic / threshold / control**, **redefines no `TOL`**, adopts **no new closure
metric**, adds **no new family and no new axis**, trains no weights, reopens no spectral group, opens no
classifier (form B) and no neural encoder (form C).

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. It does **not** say v0.4d was invalid,
does **not** say Brainvision failed or succeeded. The frozen Brainvision §8 verdict is **HOLD** and untouched.

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Inputs and delivered files

```text
v0.6a (910ab34)  residual sufficiency audit -> mixed_metric_and_small_n (on n = 3 vs 3 matched pairs).
v0.6b (2cf1b14)  synthesis: recommended Branch A (larger-N replication) FIRST.
v0.7  (22c7488)  larger-N replication PLAN.
v0.7a (4beca76)  larger-N replication ENUMERATION (sealed).

Delivered UNCOMMITTED over HEAD 4beca76 (form A, non-learning, reporting-only; reuses frozen surfaces + the
v0.4d/v0.5a/v0.6a helpers by identity):
  research/brainvision/run_larger_n_residual_replication_v0_7b.py
  tests/research/test_brainvision_larger_n_residual_replication_v0_7b.py
```

## 3. What was implemented

A single reporting-only replication that runs the sealed v0.7a enumeration verbatim: 24 replication winders (and
6 development winders) from the **frozen winder generator** at more parameter points, matched against the
existing five families (F1-F5) at within-axis instances (F3 uses all eight frozen v0.3 outback increments), with
the disjoint sealed seeds. It reuses `proxy_match_residual`, the `PSC < PSC_FLOOR` feasibility, `TOL`, the
descriptor / `GROUPS`, and the v0.6a robustness lens by identity; it adds no family, no axis, no threshold, and
no closure metric. The larger-N audit runs on the replication matched pairs (single-shot). Non-finite / extreme
values are defensively excluded and can never become evidence.

## 4. Result — BY_persistence_metric_insufficiency (honest, NOT tuned)

```text
evaluations: development 222 + replication 1056 = 1278 (sealed)   protocol_ok = True
replication winders 24 -> matched 19, unmatched 5 (w_sp3.00, w_sp3.50, w_r0.4, w_r0.3, w_r0.2)
audit n = 19 vs 19   outcome = BY_persistence_metric_insufficiency

effect (v0.6a: all rank_sep, BA=1.0)   larger-n BA   signed_median_diff (% of TOL)   status
by_std                                  0.921         +0.0451 (71%)                   persists_substantial
by_centroid                             0.921         -0.0339 (54%)                   persists_substantial
by_spread                               0.921         -0.0294 (46%)                   persists_substantial
u_directional_delta_rms                 0.842         -0.0036 ( 6%)                   weakens_negligible
angular_increment_mag                   0.842         -0.0037 ( 6%)                   weakens_negligible
rg_spread                               0.895         -0.0028 ( 4%)                   weakens_negligible
rg_centroid                             0.868         -0.0001 ( 0%)                   weakens_negligible

magnitude clustering (largest-gap split = 0.41):
  SUBSTANTIAL = {by_std, by_centroid, by_spread}    NEGLIGIBLE = {rg_centroid, rg_spread, directional pair}
```

**Reading (research-only).** Two things happen at larger n:

1. **The perfect rank-separation (BA = 1.0) collapses for ALL seven effects** — none is perfectly
   rank-separated at n = 19 vs 19. This confirms that the n = 3 vs 3 best-threshold saturation was a **small-N**
   artifact and was pervasive.
2. **But the BY-channel effect SIZE persists substantially.** `by_std` (71% of `TOL`), `by_centroid` (54%),
   `by_spread` (46%) retain both a substantial signed median difference and a high BA (~0.92). A threshold-free
   largest-gap split of the effect sizes (gap 0.41) separates these three from the negligible group (directional
   and rg statistics, 0-6% of `TOL`). So the **metric-insufficiency component is real and persists, localized to
   the BY-channel statistics**, while the directional and rg effects weaken to negligible magnitude.

A notable re-classification: `by_std` was labelled *fragile / small-N* at v0.6a (n = 3), but at larger n it is
the **largest** substantive effect (71% of `TOL`). The larger-n replication thus resolves v0.6a's
`mixed_metric_and_small_n` into a clearer picture — the substantive residual is BY-channel (metric
insufficiency), and the directional / rg effects were tiny-magnitude / small-N.

## 5. Persistence / collapse per effect group

```text
A. BY-channel (by_centroid, by_spread):  PERSISTS substantial (real class difference survives larger n).
B. Directional (u_directional_delta_rms, angular_increment_mag): WEAKENS to negligible magnitude (~6% of TOL);
   perfect separation lost, effect always tiny -> tiny-magnitude / small-N.
C. Fragile v0.6a small-N (by_std, rg_centroid, rg_spread): SPLIT -- by_std reclassifies to SUBSTANTIAL (persists),
   rg_centroid / rg_spread WEAKEN to negligible (small-N confirmed for the genuine small-N ones).
```

None of the effects collapsed to the chance floor (all larger-n BA in 0.84-0.92, above `CHANCE_BAND = 0.60`);
what collapsed is the **perfect** rank-separation (BA = 1.0), for all of them.

## 6. Threshold-free classification and defensive handling

The substantive-vs-negligible split uses a **largest-gap partition** of the effect-size (`|signed median diff|`
/ `TOL`) ordering — a parameter-free 1-D clustering (split at the single largest gap, here 0.41), **not** a fixed
cutoff. The persistence status uses only the frozen `CHANCE_BAND` (0.60) as a separability floor and the frozen
robustness-lens rank-separation flag; no new threshold is adopted and `TOL` is unchanged. Non-finite / extreme
values are excluded via the frozen `_is_clean`; a non-finite value in a required metric forces
`invalid_protocol_breach` and carries no evidential weight.

## 7. Outcome taxonomy (all leave claim locks unchanged)

```text
BY_persistence_metric_insufficiency   BY-channel persists substantial; fragile rg/directional negligible  (THIS RUN)
directional_collapse_tiny_magnitude   directional negligible/collapsed
small_n_features_collapse             fragile small-N effects weaken/collapse; BY did not persist
mixed_effects_persist                 BY-channel AND some small-N both persist
replication_inconclusive              larger-N pattern does not cleanly resolve
invalid_protocol_breach               budget mismatch / non-finite / rerun -> no evidential weight
```

## 8. Tests run

```text
python -m pytest tests/research/test_brainvision_larger_n_residual_replication_v0_7b.py -q  -> 14 passed
python research/brainvision/run_larger_n_residual_replication_v0_7b.py                       -> ran clean (result above)
python -m pytest tests/research -q                                                           -> 288 passed, 1 failed (sandbox)
```

The single full-suite failure is the pre-existing, documented `spectral_centroid` Linux/Windows knife-edge in
`test_brainvision_color_structure_pooled_gate_audit_v1_8.py` (green on Windows; unrelated to v0.7b). The v0.7b
tests assert only platform-independent robust facts: the sealed budget 222 + 1056 = 1278; sealed seeds / counts
/ pairing; only the frozen winder + F1-F5 surfaces (no new family / axis); `TOL` / floors / `CHANCE_BAND`
unchanged; spectral audit-note-only; no while-loop (single deterministic pass, no search-until-pass); sealed
outcome labels; non-finite values cannot become evidence; and claim locks stay False with verdict HOLD. Windows
pytest is the source of truth.

## 9. Claim locks and verdict

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
frozen_brainvision_verdict                  = HOLD   (untouched)
vision_claim = False   memory_readiness_claim = False   runtime_readiness_claim = False
integration_readiness_claim = False
```

Establishing that the BY-channel effect survives larger n is an in-vitro synthetic, metric-level observation
within the same family set; it moves no lock and no verdict, and is not descriptor validity or vision evidence.
The proof route remains **HELD / HOLD**.

## 10. Recommended next (not opened here)

- **Codex review** this findings receipt + the harness / tests.
- **If accepted,** the operator runs the Windows suite and commits. The replication sharpens the wall: the
  substantive residual is **BY-channel metric insufficiency** (persists at larger n), while directional / rg are
  tiny-magnitude / small-N. The honest follow-ups remain **separate, future, docs-first** steps (not opened
  here): a Branch-B **multi-feature closure metric proposal** targeting the persisting BY-channel separation
  (`by_std` / `by_centroid` / `by_spread`) **without casually inventing pass thresholds**; or **HOLD**. No code,
  classifier (B), neural (C), real clips, runtime, memory, `§0`, or tags are recommended here.

## 11. Codex review prompt

```text
Please review the v0.7b larger-N residual replication:
  research/brainvision/run_larger_n_residual_replication_v0_7b.py
  tests/research/test_brainvision_larger_n_residual_replication_v0_7b.py
  docs/TORMENT_BRAINVISION_LARGER_N_RESIDUAL_REPLICATION_FINDINGS_v0.7b.md
(new, UNCOMMITTED, over committed edge 4beca76; implements the sealed v0.7a enumeration).

Verify that this slice:
- is offline research only (research/brainvision + tests/research + one findings doc); no torment_service, no
  runtime / memory / camera / sensor / streaming, no real clips; NO classifier (form B) / neural encoder (form C);
- runs EXACTLY the sealed v0.7a enumeration: 24 replication + 6 development winders from the frozen winder
  generator, F1-F5 within-axis candidate pool (F3 = all eight frozen v0.3 outback increments), disjoint sealed
  seeds, finite budget 222 + 1056 = 1278, single deterministic pass (no while-loop, no search-until-pass, no
  restarts/retries/redraws/replacements);
- reuses frozen surfaces BY IDENTITY (winder + F1-F5 generators, proxy_match_residual, PSC<PSC_FLOOR, TOL,
  descriptor/GROUPS, robustness lens); adds NO new family, NO new axis, NO new closure metric; invents NO
  threshold; REDEFINES NO TOL; keeps PSC_FLOOR/AIC_FLOOR/CHANCE_BAND unchanged; keeps spectral audit-note-only;
- classifies substantive-vs-negligible effects by a THRESHOLD-FREE largest-gap partition of the effect-size
  ordering (not a fixed cutoff) and persistence via the frozen CHANCE_BAND floor + robustness-lens rank flag;
- reports the honest result: at larger n the perfect BA=1.0 saturation collapses for ALL effects (small-N
  confirmed pervasive) while the BY-channel effect size persists substantial (by_std 71%, by_centroid 54%,
  by_spread 46% of TOL; by_std reclassified from v0.6a-fragile), directional/rg weaken to negligible ->
  outcome BY_persistence_metric_insufficiency; and does NOT overclaim (no descriptor validity / vision / pass);
- defensively excludes non-finite / extreme values (forces invalid_protocol_breach) so they never become evidence;
- does NOT say v0.4d was invalid, does NOT say Brainvision failed or succeeded, does NOT move claim locks or
  authorize runtime/memory/integration; preserves all claim locks
  (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; no §0; no tags.

Flag any new family / axis / closure metric / threshold / TOL change, any rerun/replacement/redraw or
search-until-pass path, any budget other than 1278, any non-finite value that could become evidence, any
claim-lock/verdict movement, or any overclaim of the persistence result.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Larger-N Residual Replication Findings v0.7b. Reporting-only, non-learning,
explanatory; offline research. Changes no frozen formula, gate, evaluator, or verdict; deletes or weakens no
control; redesigns no descriptor; invents no threshold; redefines no TOL; adds no new family, axis, or closure
metric; reopens no spectral group; opens no classifier / neural / runtime / memory / real-clip work; makes no
vision / descriptor-validity / temporal-order / memory / runtime / integration claim; no `§0` pointer; no tags.*
