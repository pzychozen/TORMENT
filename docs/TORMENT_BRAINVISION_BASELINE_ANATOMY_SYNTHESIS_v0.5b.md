# TORMENT Brainvision Baseline Anatomy Synthesis v0.5b

## 1. Status / non-claims

**DOCS-ONLY synthesis / next-decision note. Non-authorizing, non-implementing. Opens no code, no tests, no
runtime, no integration lane.** It records what the v0.5a baseline-anatomy diagnostic means and what research
question comes next. It **authorizes no code and no tests**, invents no threshold, changes no formula / §7
anti-proxy logic / §8 verdict logic, deletes or weakens no control, redesigns no descriptor, and opens **no
classifier (form B) and no neural encoder (form C)**. Everything stays offline under `research/brainvision/` +
`tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. Brainvision Path B remains **not
proven vision**. A synthesis alone moves nothing: **no claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v0.4d / v0.4e / v0.5 / v0.5a

```text
v0.4d (77ed133)  ran the sealed matched search -> Partial: 3/3 held-out matched within TOL, yet the four matched
                 cheap-baseline groups still separated.
v0.4e (3814d44)  synthesized: the obstruction moved from "could not hand-build candidates" to "matching the
                 declared proxy residuals does not close adversarial baseline separability"; recommended
                 Branch A (baseline anatomy).
v0.5  (1255be7)  pre-registered the baseline-anatomy diagnostic (docs-only plan).
v0.5a (37a75f7)  IMPLEMENTED and ran it (form A, non-learning, explanatory-only) -> distributed_residual_geometry.
v0.5b (this doc) synthesizes v0.5a and recommends the next research question.
```

**v0.5a does NOT invalidate v0.4d.** It *explains* why v0.4d stayed Partial: the declared residual match was real
under its own metric, but that metric did not close the feature-level separability the adversarial baselines can
exploit. This note changes nothing v0.4b/v0.4c froze and nothing v0.4d produced.

## 3. Windows repo truth

Windows pytest is the source of truth. Recorded verbatim:

```text
python -m pytest tests/research/test_brainvision_baseline_anatomy_v0_5a.py -q
  12 passed in 0.57s

python research/brainvision/run_baseline_anatomy_v0_5a.py
  outcome: distributed_residual_geometry   protocol_ok: True   verdict: HOLD   locks: False False False
  movement_channel_energy  group_max_BA = 1.0000   concentration = distributed
  directional              group_max_BA = 1.0000   concentration = distributed
  per_channel              group_max_BA = 1.0000   concentration = distributed
  frame_diff               group_max_BA = 0.8333   concentration = single_feature_group
  protocol_metric_mismatch_flag = True
  small_n_caveat: best-threshold BA saturates easily at n=3 vs 3
  multi-group concentration: distributed = 3   concentrated = 0
  top effect-size features: movement/chroma_mag, per_channel/by_centroid, per_channel/by_spread,
                            movement/rg_std, movement/by_std
  top BA features:          movement/by_std, directional/u_directional_delta_rms,
                            directional/angular_increment_mag, per_channel/rg_centroid, per_channel/by_centroid

python -m pytest tests/research -q
  262 passed in 41.93s
```

(The one `spectral_centroid` Linux/Windows knife-edge test that fails in the Linux sandbox passes on Windows,
hence 262 passed here.)

## 4. v0.5a result summary

v0.5a was **protocol-clean** (`protocol_ok = True`). It **preserved the v0.4d matched held-out pairs and
residuals** — it reused the exact sealed held-out search, reproduced the committed pairs (the three
`segment_paired_canceller` matches at residuals 0.045 / 0.036 / 0.060, all `<= TOL`), and changed no family /
grid / seed / envelope and no `TOL`. It **inspected only the four frozen matched groups**
(`movement_channel_energy`, `directional`, `per_channel`, `frame_diff`); **spectral remained audit-note-only**
and was not reopened as a closure group. It decomposed each group into per-feature best-threshold BA and signed
median difference on the 3 winders vs 3 matched candidates, and reported `distributed_residual_geometry` with
`protocol_metric_mismatch_flag = True`. Verdict **HOLD**; claim locks all False.

## 5. Why the outcome is distributed_residual_geometry

The surviving separability is **not one simple leftover feature** — it is spread across features. In every
multi-feature group more than one feature separates the classes above the reporting reference, so all three
multi-feature groups are `distributed` (distributed = 3, concentrated = 0):

```text
movement_channel_energy   by_std, rg_std, chroma_mag, delta_rms all separate (by_std perfect)
directional               both u_directional_delta_rms and angular_increment_mag separate
per_channel               all four (rg/by centroid, rg/by spread) separate
frame_diff                delta_rms only (single-feature group; shared with movement_channel_energy)
```

Two structural qualifiers sit alongside this (§6, §7): the effect-size residual is concentrated in the
BY-channel / amplitude statistics (`chroma_mag`, `by_centroid`, `by_spread`, `rg_std`, `by_std`), and much of
the BA = 1.0 saturation is small-N best-threshold optimism.

## 6. Meaning of protocol_metric_mismatch_flag

`protocol_metric_mismatch_flag = True` means: the per-pair declared residual match held for **all** matched
pairs (`proxy_match_residual` = L-inf over the ten matched statistics `<= TOL`), **yet** the class-level
best-threshold baseline audit still separates the winder-set from the matched-candidate-set on the same
features.

The two metrics measure different things. The declared match is a **per-pair, single-number L-inf summary**: is
each winder within `TOL` of *its own* matched candidate? The baseline audit is a **class-level, per-feature
best-threshold** quantity: can *some feature* separate the *group* of winders from the *group* of candidates? A
per-pair L-inf match within `TOL` does not force class-level overlap, so the baselines still separate. **The
v0.4d residual/TOL match was real under the declared metric — but that metric did not capture all the
feature-level separability the adversarial baselines can exploit.** That is the mismatch.

## 7. Small-N caveat

The held-out matched set is small: 3 winders vs 3 matched candidates. Best-threshold BA saturates trivially at
that N — a feature needs only the three winder values to fall on one side of the three candidate values (by any
margin) to score BA = 1.00. Seven of eleven features reach BA = 1.00 while their signed median differences are
tiny (down to ~0.0001). So the raw `distributed` picture partly reflects small-N optimism, and best-threshold BA
alone overstates the separability. The honest lens is the **signed median difference (effect size)**, which
localizes the genuine class-level gap to the BY / amplitude statistics. This caveat is a limitation to state, not
a threshold to change.

## 8. What v0.5a newly teaches

```text
v0.4e said:  the obstruction moved to "residual match does not close baseline separability".
v0.5a says:  that surviving separability is DISTRIBUTED across features (not one leftover feature) and is a
             PROTOCOL METRIC MISMATCH -- the per-pair L-inf/TOL closure metric is more compressed than the
             multi-feature, class-level separability the baselines exploit; the genuine effect-size residual
             sits in BY / amplitude statistics, and BA saturation is partly small-N optimism.
```

So the wall's location is now specific: it is a **closure-metric sufficiency gap**, not a missing candidate. The
next lever to examine is the closure metric itself (does a per-pair L-inf `<= TOL` summary adequately represent
feature-level, class-level separability?), not another round of candidate construction. This is a genuinely new,
honest research signal — and it upgrades **no** claim (§12): it is an in-vitro synthetic description within one
sealed enumeration.

## 9. What remains unresolved

```text
- WHETHER the v0.4d group-level residual/TOL closure metric is simply too compressed / too weak relative to
  feature-level class separability, or whether the surviving separability is dominated by the small-N regime.
- WHAT a sufficient closure metric would look like (comparing per-feature separability, signed median
  differences, and group-level residuals) WITHOUT casually inventing new pass thresholds.
- WHETHER a larger held-out set would collapse the BA saturation (small-N) or leave the BY/amplitude effect-size
  residual intact.
- (spectral stays audit-note-only and is not implicated.)
```

None of these is resolved by v0.5a, and none is resolved by this synthesis.

## 10. Candidate next branches

```text
A. Tolerance / residual sufficiency audit
   Ask whether the v0.4d group-level residual/TOL closure metric is too compressed or too weak compared to the
   feature-level baseline separability -- a docs-first analysis of the metric gap, inventing no new threshold.
   Pro: directly targets the §8 wall (the metric, not the candidates); smallest honest next step.
   Con: must stay reference-only; risks drifting toward threshold re-negotiation if not disciplined.

B. Multi-feature closure metric proposal
   Propose a stricter closure condition comparing per-feature separability, signed median differences, and
   group-level residuals -- WITHOUT inventing pass thresholds casually.
   Pro: could define a closure metric that matches what the baselines exploit.
   Con: premature before A establishes that the current metric is actually insufficient (not just small-N).

C. Candidate-family expansion amendment
   A reviewed docs-only amendment adding non-winder families (e.g. aimed at BY/amplitude).
   Pro: could reduce the effect-size residual.
   Con: RISKY -- adding families before fixing the metric may just produce more Partials; must not precede A/B.

D. Pause Brainvision and return to TORMENT memory / kernel work
   Accept the anatomy as a clean stopping point and redirect effort to another TORMENT layer.
   Pro: reasonable if the operator wants to digest the wall before more diagnostics.
   Con: leaves the closure-metric question open.
```

## 11. Recommended next step

**Recommend Branch A (tolerance / residual sufficiency audit) first, docs-first, after Codex accepts this
synthesis.** A targets the §8 wall directly — the closure metric — and must precede B (which would propose a new
metric) and C (which risks more Partials if the metric is the real problem). D (pause and return to memory /
kernel work) remains a legitimate operator call.

```text
1. Codex review THIS synthesis (docs-only; over committed edge 37a75f7).
2. If accepted, commit this synthesis doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first audit (analysis before
   any code, inventing no threshold). This synthesis opens no code and authorizes no implementation.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, §0, or tag work is recommended or authorized here.
```

## 12. What would still not be proven

Even a completed Branch-A audit would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

v0.5a's per-feature anatomy is an in-vitro synthetic description within one sealed enumeration; it says nothing
about real clips and does not validate the descriptor as measuring real visual structure. The claim locks
(`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`, `descriptor_validity_claim_allowed`)
and `verdict = HOLD` remain in force.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BASELINE_ANATOMY_SYNTHESIS_v0.5b.md
(new, docs-only, untracked; over committed edge 37a75f7, synthesizing the v0.5a baseline-anatomy run).

Verify that this synthesis:
- is docs-only and opens no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
- records Windows repo truth faithfully (12 passed; distributed_residual_geometry; group max BA 1.0/1.0/1.0/0.833;
  protocol_metric_mismatch_flag True; small-N caveat; distributed=3 concentrated=0; top effect-size and top BA
  features; full suite 262 passed on Windows; HOLD; locks False);
- states that v0.5a was protocol-clean, preserved the v0.4d matched pairs and residuals, inspected only the four
  matched groups, kept spectral audit-note-only, found distributed_residual_geometry (not one leftover feature),
  and found protocol_metric_mismatch_flag = True;
- frames the mismatch correctly: the v0.4d residual/TOL match was REAL under the declared per-pair metric, but
  that metric did not capture all feature-level, class-level separability the adversarial baselines can exploit;
- explicitly does NOT say v0.5a invalidates v0.4d -- it EXPLAINS why v0.4d stayed Partial;
- carries the small-N caveat honestly (BA saturates at n=3 vs 3; effect size, not raw BA, localizes the residual
  to BY/amplitude);
- recommends Branch A (tolerance / residual sufficiency audit) first, docs-first, and lists branches A/B/C/D
  WITHOUT opening any code or authorizing implementation, and without inventing thresholds;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD;
- makes no vision / "Brainvision sees" / temporal-order / descriptor-validity / memory-readiness /
  runtime-readiness / integration-readiness claim; adds no §0 pointer and no tags.

Flag any claim that v0.5a invalidates v0.4d, any overclaim of the anatomy, any threshold invention, any implicit
opening of B/C/runtime/memory/real-clips, any claim-lock/verdict movement, or any misrecording of the Windows truth.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Baseline Anatomy Synthesis v0.5b. Docs-only, non-authorizing. Opens no implementation
lane; opens no classifier / neural work; changes no frozen formula, gate, evaluator, or verdict; deletes or
weakens no control; redesigns no descriptor; invents no threshold; makes no vision / descriptor-validity /
temporal-order / memory / runtime / integration claim; no `§0` pointer added; no tags.*
