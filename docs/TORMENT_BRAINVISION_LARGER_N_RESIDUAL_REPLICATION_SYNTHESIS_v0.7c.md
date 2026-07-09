# TORMENT Brainvision Larger-N Residual Replication Synthesis v0.7c

## 1. Status / non-claims

**DOCS-ONLY synthesis / next-decision note. Non-authorizing, non-implementing. Opens no code, no tests, no
runtime, no integration lane.** It records what the v0.7b larger-N residual replication means and what research
question comes next. It **authorizes no code and no tests**, invents no threshold, **redefines no `TOL`**,
adopts **no new closure metric**, proposes no pass/fail rule change, changes no formula / §7 anti-proxy logic /
§8 verdict logic, deletes or weakens no control, redesigns no descriptor, reopens no spectral group, expands no
generator family, and opens **no classifier (form B) and no neural encoder (form C)**. Everything stays offline
under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. It does **not** say v0.7b proves
Brainvision, does **not** say it validates the descriptor, and does **not** say it invalidates prior work. A
synthesis alone moves nothing: **no claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v0.6a / v0.6b / v0.7 / v0.7a / v0.7b

```text
v0.6a (910ab34)  residual sufficiency audit -> mixed_metric_and_small_n (on n = 3 vs 3 matched pairs).
v0.6b (2cf1b14)  synthesis: recommended Branch A (larger-N replication) FIRST, to separate metric insufficiency
                 from small-N optimism.
v0.7  (22c7488)  larger-N replication PLAN.
v0.7a (4beca76)  larger-N replication ENUMERATION (sealed 1278-evaluation budget).
v0.7b (978bb36)  IMPLEMENTED and ran it (form A, non-learning, reporting-only) -> BY_persistence_metric_insufficiency.
v0.7c (this doc) synthesizes v0.7b and recommends the next research question.
```

v0.7b does **not** prove Brainvision, validate the descriptor, or invalidate prior work. It **sharpened** the
wall by separating v0.6a's mixed result. This note changes nothing v0.4b/v0.4c/v0.7a froze.

## 3. Windows repo truth

Windows pytest is the source of truth. Recorded verbatim:

```text
python -m pytest tests/research/test_brainvision_larger_n_residual_replication_v0_7b.py -q
  14 passed in 4.56s

python research/brainvision/run_larger_n_residual_replication_v0_7b.py
  evaluations dev/replication/total: 222 1056 1278 (sealed 1278)   TOL 0.0634 (redefined=False)
  replication winders 24 -> matched 19, unmatched 5 (w_sp3.00, w_sp3.50, w_r0.4, w_r0.3, w_r0.2)
  residual closeness coexists with separability: True
  by_std      BA=0.921 smd=+0.04505 (71% TOL) -> persists_substantial
  by_centroid BA=0.921 smd=-0.03393 (54% TOL) -> persists_substantial
  by_spread   BA=0.921 smd=-0.02935 (46% TOL) -> persists_substantial
  u_directional_delta_rms BA=0.842 (6% TOL) -> weakens_negligible
  angular_increment_mag   BA=0.842 (6% TOL) -> weakens_negligible
  rg_spread   BA=0.895 ( 4% TOL) -> weakens_negligible
  rg_centroid BA=0.868 ( 0% TOL) -> weakens_negligible
  SUBSTANTIAL = {by_std, by_centroid, by_spread}   NEGLIGIBLE = {rg_centroid, rg_spread, directional pair}
  OUTCOME_LABEL: BY_persistence_metric_insufficiency   protocol_ok: True   verdict: HOLD   locks: False False False

python -m pytest tests/research -q
  289 passed in 51.04s
```

(The one `spectral_centroid` Linux/Windows knife-edge test that fails in the Linux sandbox passes on Windows,
hence 289 passed here.)

## 4. v0.7b result summary

v0.7b was **protocol-clean** (`protocol_ok = True`) and **preserved the sealed 1278-evaluation envelope** (222
development + 1056 replication). **No `TOL`, threshold, descriptor, `GROUPS`, evaluator, spectral, family, or
closure-metric change occurred** — it ran the sealed v0.7a enumeration verbatim, reusing every frozen surface by
identity. Of 24 replication winders, 19 matched within `TOL` (5 high-speed / low-radius winders unmatched, not
retried). **Residual closeness still coexists with feature-level separability.** Outcome:
**`BY_persistence_metric_insufficiency`**. Verdict **HOLD**; claim locks all False.

## 5. What persisted at larger N

```text
by_std       larger-n BA 0.921   signed median diff 71% of TOL   -> persists_substantial
by_centroid  larger-n BA 0.921   signed median diff 54% of TOL   -> persists_substantial
by_spread    larger-n BA 0.921   signed median diff 46% of TOL   -> persists_substantial
```

These are the **BY-channel geometry** statistics. They retain both a high best-threshold BA (~0.92) and a
substantial signed median difference (46-71% of `TOL`) at larger n. A threshold-free largest-gap partition of
the effect sizes (gap 0.41) isolates exactly these three as the substantive cluster. `by_std` — labelled
*fragile / small-N* at v0.6a (n = 3) — is at larger n the **largest** substantive effect (71% of `TOL`).

## 6. What weakened at larger N

```text
u_directional_delta_rms  larger-n BA 0.842   signed median diff 6% of TOL  -> weakens_negligible
angular_increment_mag    larger-n BA 0.842   signed median diff 6% of TOL  -> weakens_negligible
rg_spread                larger-n BA 0.895   signed median diff 4% of TOL  -> weakens_negligible
rg_centroid              larger-n BA 0.868   signed median diff 0% of TOL  -> weakens_negligible
```

The **perfect** rank-separation (BA = 1.0) that every effect had at n = 3 collapsed for **all** of them at
larger n — confirming the n = 3 vs 3 saturation was a pervasive **small-N** artifact. But the directional and
rg effects also have **negligible magnitude** (0-6% of `TOL`): their apparent separability was tiny-magnitude /
small-N, not a durable class difference.

## 7. Meaning of BY_persistence_metric_insufficiency

Larger-N sample support **separated** v0.6a's `mixed_metric_and_small_n`:

```text
- the SMALL-N component was real and pervasive: perfect BA saturation collapsed for every effect at larger n;
- the METRIC-INSUFFICIENCY component is durable and LOCALIZED: the BY-channel statistics (by_std / by_centroid /
  by_spread) retain a substantial class-level difference that the per-pair residual / TOL match does not close,
  while directional / rg weaken to negligible magnitude.
```

So at larger n the **BY-channel geometry remains a durable residual separability source under the existing
residual / `TOL` metric**, and the directional / rg / small-N effects reduce to artifacts. This is a research-
only characterization; it establishes **no** vision, descriptor validity, or real-world property (§12).

## 8. What v0.7b newly teaches

```text
v0.6b said:  the wall is a closure-metric sufficiency gap, part real (metric insufficiency) and part small-N.
v0.7b says:  larger-N sample support REDUCES the directional / RG / small-N artifacts, while BY-channel geometry
             remains a DURABLE residual separability source under the existing residual / TOL metric.
```

So the wall is now **sharpened and localized**: the substantive residual is BY-channel geometry, and the earlier
mixed picture resolves once sample support is large enough to dissolve the small-N saturation. The `by_std`
re-classification (v0.6a-fragile -> largest substantive effect at larger n) is the sharp signal that the small-N
regime, not a real difference, drove the earlier ambiguity there. This is a genuinely new, honest
characterization — and it upgrades **no** claim (§12).

## 9. What remains unresolved

```text
- WHY the BY-channel statistics (by_std / by_centroid / by_spread) persist despite per-pair residual / TOL
  matching -- what geometric property of the BY (blue-yellow) chroma axis the current residual metric fails to
  represent.
- WHETHER a stricter closure structure for BY-channel geometry is warranted -- deferred; no metric adopted here.
- WHETHER the BY-channel persistence reflects a deeper chroma-plane / opponent-axis geometry issue.
- (spectral stays audit-note-only and is not implicated.)
```

None of these is resolved by v0.7b, and none is resolved by this synthesis.

## 10. Candidate next branches

```text
A. BY-channel metric anatomy plan
   Inspect WHY by_centroid, by_spread, and by_std persist despite residual / TOL matching -- a docs-first plan
   for a reporting-only anatomy of the BY-channel persistence, inventing no threshold and adopting no metric.
   Pro: the wall is now localized; understand what BY-channel persistence means before any redesign.
   Con: must stay reporting-only; risks drifting toward metric design if not disciplined.

B. BY-channel closure metric proposal
   Propose a stricter future closure structure for BY-channel geometry, docs-first, WITHOUT adopting thresholds yet.
   Pro: could define a closure metric matching the durable BY-channel separation.
   Con: premature before A explains WHAT BY-channel persistence is; risks a metric fitted to a not-yet-understood effect.

C. Return to operator / new math intuition
   Ask whether the current BY-channel wall suggests a deeper chroma-plane / opponent-axis geometry issue.
   Pro: may reframe the problem at the right level.
   Con: open-ended; best informed by A's anatomy first.

D. Pause Brainvision and return to TORMENT memory / kernel work
   Accept the sharpened characterization as a clean stopping point and redirect effort to another TORMENT layer.
   Pro: reasonable if the operator wants to digest the localized wall before more diagnostics.
   Con: leaves the BY-channel question open.
```

## 11. Recommended next step

**Recommend Branch A (BY-channel metric anatomy plan) first, docs-first, after Codex accepts this synthesis.**
The wall is now localized to BY-channel geometry; before redesigning metrics (B) or injecting new math (C), the
clean next step is to inspect **what BY-channel persistence actually means**. A must precede B (so a future
metric is not fitted to a not-yet-understood effect) and C (which is best informed by A's anatomy). D (pause)
remains a legitimate operator call.

```text
1. Codex review THIS synthesis (docs-only; over committed edge 978bb36).
2. If accepted, commit this synthesis doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first plan (reporting-only
   anatomy; no threshold, no metric adoption). This synthesis opens no code and authorizes no implementation.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, §0, or tag work is recommended or authorized here.
```

## 12. What would still not be proven

Even a completed BY-channel anatomy would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

That the BY-channel effect survives larger n is an in-vitro synthetic, metric-level observation within the same
family set; it says nothing about real clips and does not validate the descriptor. The proof route remains
**HELD / HOLD**. The claim locks (`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`,
`descriptor_validity_claim_allowed`) and `verdict = HOLD` remain in force.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_LARGER_N_RESIDUAL_REPLICATION_SYNTHESIS_v0.7c.md
(new, docs-only, untracked; over committed edge 978bb36, synthesizing the v0.7b larger-N replication).

Verify that this synthesis:
- is docs-only and opens no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
- records Windows repo truth faithfully (14 passed; 222+1056=1278; 24->19 matched; BY_persistence_metric_insufficiency;
  per-effect BA / smd; substantial {by_std,by_centroid,by_spread} vs negligible {rg_centroid,rg_spread,directional};
  protocol_ok True; verdict HOLD; locks False; full suite 289 passed on Windows);
- states that v0.7b was protocol-clean, preserved the sealed 1278-evaluation envelope, and made NO TOL / threshold /
  descriptor / GROUPS / evaluator / spectral / family / closure-metric change;
- frames it correctly: v0.7b does NOT prove Brainvision, does NOT validate the descriptor, does NOT invalidate prior
  work; it SHARPENED the wall -- larger-N sample support reduces the directional / RG / small-N artifacts while
  BY-channel geometry remains a durable residual separability source under the existing residual / TOL metric;
- reports that BY-channel (by_centroid / by_spread / by_std) persisted substantial and directional / rg weakened to
  negligible, that perfect BA=1.0 saturation collapsed for ALL effects (small-N pervasive), and that by_std
  reclassified from v0.6a-fragile to the largest substantive effect;
- recommends Branch A (BY-channel metric anatomy plan) first, docs-first, and lists A/B/C/D WITHOUT opening code,
  inventing thresholds, adopting a closure metric, redefining TOL, or expanding families;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any claim that v0.7b proves Brainvision / validates the descriptor / invalidates prior work, any threshold
invention, any TOL redefinition, any closure-metric adoption, any implicit opening of B/C/runtime/memory/real-clips,
any claim-lock/verdict movement, or any misrecording of the Windows truth.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Larger-N Residual Replication Synthesis v0.7c. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural work; changes no frozen formula, gate, evaluator, or verdict;
deletes or weakens no control; redesigns no descriptor; invents no threshold; redefines no TOL; adopts no closure
metric; expands no generator family; makes no vision / descriptor-validity / temporal-order / memory / runtime /
integration claim; no `§0` pointer added; no tags.*
