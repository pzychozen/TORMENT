# TORMENT Brainvision Baseline Anatomy Plan v0.5

## 1. Status / non-claims

**DOCS-ONLY plan. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration
lane.** It pre-registers a *future* baseline-anatomy diagnostic (Branch A of v0.4e) that would inspect which
individual features inside the four still-open matched baseline groups still separate the v0.4d matched
held-out pairs. It **authorizes no code and no tests**, invents no threshold, changes no formula / §7 anti-proxy
logic / §8 verdict logic, deletes or weakens no control, redesigns no descriptor, and opens **no classifier
(form B) and no neural encoder (form C)**. Everything stays offline under `research/brainvision/` +
`tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. Brainvision Path B remains **not
proven vision**. A plan alone moves nothing: **no claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v0.4d and v0.4e

```text
v0.4d (77ed133)  ran the sealed matched search -> Partial: 3/3 held-out targets matched within TOL, yet the four
                 matched cheap-baseline groups still separated (movement 1.0, directional 1.0, per_channel 1.0,
                 frame_diff 0.833; all_closed = False; evaluator separates).
v0.4e (3814d44)  synthesized: the obstruction moved from "could not hand-build candidates" to "matching the
                 declared proxy residuals does not close adversarial baseline separability"; recommended
                 Branch A (baseline anatomy) first.
v0.5  (this doc) pre-registers that Branch A diagnostic, docs-only, before any code.
```

This diagnostic is **explanatory, not corrective**: it is not trying to make Brainvision pass — it is trying to
explain **why v0.4d remained Partial**. It changes nothing v0.4b/v0.4c froze and nothing v0.4d produced.

## 3. Diagnostic question

```text
What exactly are the adversarial baselines SEEING that the declared per-pair proxy-residual match (L-inf over
the ten matched statistics <= TOL) did not close?
```

Concretely: decompose each still-open matched group's surviving best-threshold separability into **per-feature**
contributions, on the exact v0.4d matched held-out pairs, and describe where the separability lives.

## 4. Baseline groups to inspect

The four MATCHED groups, with their frozen v0.3 `GROUPS` feature membership (reused by identity; not
re-authored):

```text
movement_channel_energy : rg_std, by_std, chroma_mag, delta_rms      (4 features)
directional             : u_directional_delta_rms, angular_increment_mag   (2 features)
per_channel             : rg_centroid, by_centroid, rg_spread, by_spread   (4 features)
frame_diff              : delta_rms                                   (1 feature; shared with movement_channel_energy)

v0.4d group best-threshold BA to be decomposed: movement 1.0, directional 1.0, per_channel 1.0, frame_diff 0.833
```

**Spectral stays audit-note-only / ill-defined on constant chroma and is NOT reopened as a matched closure
group.** Note that `frame_diff` is a single-feature group (`delta_rms`), which also sits inside
`movement_channel_energy`; the anatomy should surface this sharing rather than double-count it.

## 5. Feature-level anatomy plan

The future diagnostic (a separate, later v0.5a code step — **not opened here**) would be **reporting-only** and
would:

```text
INPUT (reused by identity; NOT rerun, NOT replaced):
  - the EXACT v0.4d matched held-out pairs: the 3 held-out winders and their 3 matched
    segment_paired_canceller candidates from the committed v0.4d run (77ed133).
  - the frozen descriptor / stats / GROUPS / best-threshold-BA surfaces, reused by identity.

FOR EACH matched group, FOR EACH individual feature s in that group:
  - per-feature best-threshold balanced accuracy (the SAME frozen best-threshold BA the v0.4d audit already
    maxes over per group -- here reported per feature, not just the group max);
  - signed median difference by label (median over winders minus median over matched candidates) for s;
  - the per-feature contribution to the group max (which feature(s) achieve the group-level BA).

THEN describe (reporting-only):
  - rank ordering of the strongest separating features within and across groups;
  - whether separability is CONCENTRATED in a small subset of features or DISTRIBUTED weakly across many;
  - whether the per-pair L-inf <= TOL match HID multi-feature class-level separability under the group-level
    summary (i.e. each winder near its own partner, yet the winder-set and candidate-set still range-separable);
  - group-specific reads: whether frame_diff separation is magnitude / channel-asymmetry / temporal-edge;
    whether per_channel separation stays concentrated in BY statistics or moved; whether directional separation
    is still angular-increment magnitude/variance or the other directional statistic; whether
    movement_channel_energy is detecting coverage, amplitude, or channel-energy imbalance.
```

**No new machinery and no new threshold.** The frozen best-threshold BA computation is reused by identity, and
the frozen reporting-only band `CHANCE_BAND = 0.60` is reused **only** as a descriptive reference for calling a
feature "still separating" — it is not a gate, not an acceptance criterion, and cannot move the verdict. The
diagnostic reruns nothing, replaces no candidate, adds no generator family, and re-defines no `TOL`.

## 6. Allowed diagnostic outputs

```text
- per-feature balanced accuracy (best-threshold), within each of the four groups;
- signed median difference by label (winder vs matched candidate) per feature;
- rank ordering of the strongest separating features;
- concentration vs distribution summary (is the group BA carried by one feature or many);
- an explicit note of whether the v0.4d per-pair L-inf/TOL match hid multi-feature class-level separability;
- group-specific descriptive reads (frame_diff source; per_channel BY concentration; directional statistic;
  movement_channel_energy coverage/amplitude/imbalance) -- all descriptive, reporting-only.
```

## 7. Forbidden interpretations

```text
- NO new thresholds; NO redefining TOL; NO new acceptance gate.
- NO changing the v0.4d result; NO rerunning / replacing the v0.4d sealed candidates; NO new generator families.
- NO treating feature anatomy as descriptor validity.
- NO treating baseline anatomy as vision / "Brainvision sees" evidence.
- NO using the diagnostic to tune until baselines close (it explains Partial; it does not try to defeat it).
- NO temporal-order reading; spectral stays audit-note-only and is not reopened as a matched closure group.
```

## 8. What would count as useful evidence

The evidence is the **anatomy of the surviving separability** — a description of where it lives — **not** any
pass, decision score, or validity statement. Candidate future outcomes:

```text
A. Concentrated residual feature
   a small set of features (e.g. one or two per group) explains most of the surviving baseline separability.
   Reading: the residual is localized; a future targeted question could name the specific axis (still no claim).

B. Distributed residual geometry
   many features weakly separate, so group-level residual closure under a single L-inf/TOL summary was
   inherently insufficient. Reading: separability is diffuse; per-pair L-inf is the wrong sufficiency notion.

C. Protocol metric mismatch
   the declared proxy residual / TOL did not capture the same separability the baseline audit uses (per-pair
   match vs class-level best-threshold). Reading: the mismatch is structural, not a candidate deficiency.

D. Invalid / diagnostic breach
   the diagnostic accidentally tunes, reweights, reruns, or reopens the sealed protocol -> REJECTED, no
   evidential weight, moves no claim.
```

All of A / B / C are research-only descriptions and leave the claim locks and verdict unchanged.

## 9. What would still not be proven

Even a completed baseline-anatomy diagnostic would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

Naming which features still separate is an in-vitro synthetic description within one sealed enumeration; it says
nothing about real clips and does not validate the descriptor as measuring real visual structure. The claim
locks (`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`,
`descriptor_validity_claim_allowed`) and `verdict = HOLD` remain in force under every outcome.

## 10. Recommended next step

```text
1. Codex review THIS plan (docs-only; over committed edge 3814d44).
2. If accepted, commit this plan doc. No §0 pointer; no tags.
3. Only THEN, and only on explicit operator instruction, may a SEPARATE future v0.5a code diagnostic implement
   EXACTLY this reporting-only anatomy on the reused v0.4d matched pairs -- form A, non-learning, frozen surfaces
   reused by identity, delivered UNCOMMITTED for review, Windows the source of truth. This plan authorizes no
   such code by itself.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 11. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BASELINE_ANATOMY_PLAN_v0.5.md
(new, docs-only, untracked; over committed edge 3814d44, pre-registering Branch A from v0.4e).

Verify that this plan:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
- is explanatory not corrective: it explains WHY v0.4d remained Partial and does NOT try to make Brainvision
  pass, close the baselines, or defeat the Partial result;
- inspects only the four matched groups (movement_channel_energy, directional, per_channel, frame_diff) with the
  frozen v0.3 GROUPS membership reused by identity, notes frame_diff = delta_rms (single feature shared with
  movement_channel_energy), and keeps spectral audit-note-only (NOT reopened as a matched closure group);
- reuses the EXACT v0.4d matched held-out pairs and frozen best-threshold-BA surfaces by identity: it reruns
  nothing, replaces no sealed candidate, adds no generator family, invents no threshold, and does NOT redefine
  TOL (CHANCE_BAND = 0.60 reused only as a descriptive reporting reference, not a gate);
- limits outputs to reporting-only anatomy (per-feature BA, signed median difference by label, rank ordering,
  concentration-vs-distribution, whether per-pair L-inf/TOL hid multi-feature class-level separability, and the
  group-specific descriptive reads);
- lists candidate outcomes A concentrated / B distributed / C protocol-metric-mismatch / D invalid-breach, all
  leaving claim locks and verdict unchanged;
- forbids new thresholds, TOL redefinition, changing/rerunning/replacing v0.4d, new families, tuning-until-close,
  and treating anatomy as descriptor validity or vision evidence;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD;
- makes no vision / "Brainvision sees" / temporal-order / descriptor-validity / memory-readiness /
  runtime-readiness / integration-readiness claim; adds no §0 pointer and no tags.

Flag any threshold invention, any TOL redefinition, any implicit rerun/replacement of v0.4d, any new family, any
tuning-toward-closure, any implicit opening of B/C or runtime/memory/real-clips, any claim-lock/verdict movement,
or any overclaim of the future anatomy.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Baseline Anatomy Plan v0.5. Docs-only, non-authorizing. Opens no implementation lane;
opens no classifier / neural work; changes no frozen formula, gate, evaluator, or verdict; deletes or weakens no
control; redesigns no descriptor; invents no threshold; reruns / replaces no v0.4d candidate; makes no vision /
descriptor-validity / temporal-order / memory / runtime / integration claim; no `§0` pointer added; no tags.*
