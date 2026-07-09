# TORMENT Brainvision Matched Generative Search Plan v0.4a

## 1. Status / non-claims

**DOCS-ONLY plan. Non-authorizing, non-implementing. Opens no code, no tests, no generator, no runtime,
no integration lane.** It pre-registers the constraints a *future* Direction-B matched-generative-search
implementation would be **allowed** and **forbidden** to use, so that if such a slice is ever separately gated
it cannot be tuned toward a win.

**This is a META-PLAN / pre-registration framework, not the final numeric pre-registration.** It fixes the
*rules and shape* of the future search (proxy set, tolerance policy, objective, forbidden objectives, audit and
reporting rules). It deliberately does **not** fix the exact numeric parameter grid / ranges / enumerated
seeds, the concrete generation-vs-evaluation split, or the `TOL` constant. Those are a required **later
docs-only, Codex-reviewed numeric pre-registration (v0.4b)** that must be frozen and reviewed before any
implementation exists (§6, §8, §13). This document authorizes no implementation on its own.

It **authorizes no code and no tests**, invents no threshold, changes no
formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no control, redesigns no descriptor, and
opens **no classifier (form B) and no neural encoder (form C)**. Everything discussed stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. Brainvision Path B remains **not
proven vision** and **not a functioning vision layer for TORMENT memory**. A plan alone moves nothing:
**no claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v0.4

The v0.4 different-construction proposal (`54daf01`) compared four directions and **accepted Direction B
(matched generative search)** but **opened no implementation**. It recorded (v0.4 §8) that a future B plan may
be opened only on explicit operator instruction and must pre-register S4's declared proxy set / tolerance /
parameter space / held-out split and the S5 adversarial baselines **before any code**.

This v0.4a plan is the **framework layer** of that S4 pre-registration: it carries v0.4's safeguards S1–S8
forward and makes the *rules* concrete, without authorizing the slice they would govern. The remaining
**numeric** layer of S4 — the exact parameter grid / ranges / seeds, the concrete generation-vs-evaluation
split, and the `TOL` constant — is deferred to a required later docs-only, Codex-reviewed pre-registration
(v0.4b) that must be frozen before any code (§6, §8, §13). Nothing here relaxes any v0.4 safeguard; where this
plan is more specific than v0.4, it only tightens.

## 3. Search question

```text
Within a declared, pre-registered non-winder parameter space, does there EXIST at least one non-winder fixture
(PSC < PSC_FLOOR) that matches a target coherent winder on ALL declared cheap proxy statistics within a frozen
tolerance -- and does such a matched family, evaluated on HELD-OUT generated families, drive the adversarial
cheap baselines toward the reporting-only chance band while the frozen fixed rule still separates?
```

Answering "yes" is research-only evidence that the proxy wall is **not fundamental** to the winder/canceller
family; answering "no across the declared space" is Outcome-4-style evidence that the obstruction is
**structural** for this family. Both are informative (§11). The question is about *existence and matching*, not
about any decision score (§7).

## 4. Pre-registered proxy set

The declared proxy set the search must match is **exactly the four v0.3 cheap-shortcut groups that stayed OPEN
at v0.3 — no more, no fewer**:

```text
per_channel               (the residual-BY-implicated group v0.3 could least close)
movement_channel_energy
directional
frame_diff
```

**Adding, removing, or substituting any proxy group or statistic requires a NEW pre-registered,
Codex-reviewed plan revision before implementation. The set may not be extended, trimmed, or re-weighted at
implementation time or after seeing results.**

**Exact per-statistic membership is REUSED BY IDENTITY from the frozen v0.3 `GROUPS` mapping in
`research/brainvision/run_all_shortcuts_closed_synthetic_v0_3.py`, not re-authored here** (transcribed for
reference only; the implementation imports it by identity and must not restate or edit it):

```text
movement_channel_energy : rg_std, by_std, chroma_mag, delta_rms
directional             : u_directional_delta_rms, angular_increment_mag
per_channel             : rg_centroid, by_centroid, rg_spread, by_spread
frame_diff              : delta_rms
(spectral               : spectral_centroid, spectral_spread)   # present in frozen GROUPS but AUDIT-NOTE-ONLY here
```

Note that `rg_std` / `by_std` belong to `movement_channel_energy` (channel energy), **not** to `per_channel`;
`per_channel` is the centroid / spread statistics only. The four matched groups are the non-spectral groups
above.

**Spectral is an AUDIT NOTE ONLY, never a match requirement and never a closure criterion.** On the
constant-chroma family the chroma `spectral_centroid` / `spectral_spread` are FFT-of-a-constant numerical noise
(v0.3 §6). Therefore: the search does **not** target spectral matching; spectral is **not** counted toward
"all proxies matched"; and no spectral "closure" may be claimed on ill-defined constant-chroma values. If
spectral is reported at all, it is reported transparently as not-a-usable-shortcut, exactly as v0.3 did.

## 5. Tolerance policy

Tolerance is pre-registered as a **requirement and a shape**, but its exact numeric constant is deliberately
**not invented here**:

```text
Match criterion (shape, frozen before search):
  a candidate non-winder MATCHES its target winder iff, for EVERY declared proxy statistic simultaneously,
  the per-statistic absolute delta is <= TOL   (an L-inf / worst-stat criterion, matching v0.3's L-inf
  matching convention -- NOT an average that lets one stat hide behind others).

Per-statistic normalization:
  the scaling used to compare deltas across heterogeneous statistics is REUSED from the frozen v0.3
  shortcut-audit / matching convention; this plan does not author a new normalization.

TOL constant (NOT invented in this plan):
  TOL must be either
    (a) extracted from the frozen v0.3 residual convention -- v0.3's best-effort matched family achieved an
        L-inf proxy residual of 0.0404-0.0634, which is a REFERENCE for what "matched" empirically meant on
        the prior route (an upper reference, not an authorization to loosen); or
    (b) explicitly pre-registered and Codex-reviewed BEFORE any generator code exists.
  In neither case is TOL a magic number introduced by fiat here.

Frozen-before-run / no post-hoc loosening:
  once TOL is fixed (via (a) or (b)) it is frozen before the search runs and is NEVER relaxed to admit a
  fixture. A family that only "matches" after TOL is widened is reported as NOT matched.
```

This keeps the plan honest about a genuine gap: there is no pre-existing frozen `TOL` constant to reuse, so the
plan requires it to be derived or reviewed first rather than smuggling in an arbitrary value.

## 6. Non-winder parameter space

The search space of candidate non-winder generators is declared **conceptually and up front**. It is a space of
generator *parameters*, not of descriptor internals (which stay frozen). Candidate families:

```text
- full-circle incoherent traversal       (covers all channels, phase incoherent -> PSC low)
- rosette / multi-lobe traversal          (multi-lobe coverage without net winding)
- segment-paired cancellers               (paired out/back segments that cancel net turn)
- phase-scrambled full-coverage trajectories (channel coverage preserved, per-step phase scrambled)
- hybrid coverage-preserving cancellers    (combinations of the above to raise channel coverage while
                                            keeping net winding cancelled)
```

Parameterization is over generator knobs only (e.g. angular schedules, lobe counts, segment pairings,
phase-scramble structure / seed, radius / amplitude). **This meta-plan fixes the family list and the KIND of
knobs; it does NOT fix the exact grid, ranges, or enumerated seeds.** Those exact values are part of the v0.4b
numeric pre-registration and must be frozen and Codex-reviewed before any implementation.

```text
The FAMILY LIST above is fixed by this meta-plan and may only change via a NEW reviewed plan revision.
The exact parameter grid / ranges / seeds are frozen LATER (v0.4b) -- but once frozen there, the space
CANNOT be narrowed post-hoc until something passes. Removing a family, shrinking a range, or adding a family
AFTER seeing results is forbidden; any such change requires a new pre-registered revision reviewed before
running. No implementation may begin until the v0.4b grid/ranges/seeds are frozen.
```

**Feasibility gate on every candidate.** A candidate is admissible only if it is genuinely non-structure by the
frozen rule: `PSC < PSC_FLOOR` (verified via the frozen `c(t)` / PSC computation, reused by identity).
Candidates that are actually winding (`PSC >= PSC_FLOOR`) are rejected as invalid — they are not "matched
non-winders" and are not counted toward feasibility or infeasibility.

## 7. Search objective and forbidden objectives

**Allowed objective (the only one):**

```text
minimize   proxy_match_residual(candidate, target_winder)          # L-inf over the §4 declared proxy stats
subject to feasibility:
             PSC(candidate) < PSC_FLOOR                            # the ONLY feasibility condition (non-structure)
```

`PSC < PSC_FLOOR` is the **sole** feasibility condition on the search. No other frozen-descriptor behaviour is
promoted into the objective.

**Descriptor-sanity note (NOT part of the search).** The frozen descriptor already returns NEUTRAL / ill-defined
outputs on degenerate inputs (e.g. sub-gate low-chroma trajectories); such inputs are simply ill-posed fixtures,
handled exactly as the frozen descriptor already handles them. This is descriptor input-hygiene, **not** a
search objective, **not** the match criterion, **not** a stopping criterion, and **not** an extra pass/fail
gate — it adds nothing to the feasibility constraint, which remains `PSC < PSC_FLOOR` only.

The frozen fixed rule is **unchanged** and is applied only *after* the search, as the evaluator:

```text
structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR
```

**Forbidden objectives (the generator must NOT optimize, target, or use as a stopping criterion):**

```text
- PSC/AIC balanced accuracy
- the final fixed-rule decision score
- any classifier score
- S_best_threshold
- AIC, S, or the winder-vs-nonwinder separation margin
- the adversarial cheap-baseline BA (its collapse is an EVALUATED consequence on held-out, never a target)
- any post-hoc shortcut metric chosen AFTER seeing results
```

The clean separation: the search matches **raw proxy statistics** (objective); whether that matching actually
collapses the cheap-baseline BA and whether the frozen rule still separates are **measured afterward on
held-out families** (§8, §9) — never fed back into the objective. The generator is blind to the frozen rule's
decision and to the baselines' accuracy while it searches.

## 8. Held-out evaluation split

```text
- Search-GENERATION families and EVALUATION families are separated and declared before running.
- The search / matching runs ONLY on generation families (generation winder seeds / parameter regions).
- The frozen fixed rule AND the cheap-baseline audit are evaluated on HELD-OUT generated families that the
  search never saw (held-out winder seeds / parameter regions, produced by the same frozen winder generator).
- Held-out evaluation is SINGLE-SHOT: no tuning, no re-selection, no parameter-space edit after seeing
  held-out results. A held-out failure is reported as a failure (§10), not repaired.
```

This meta-plan fixes the *rule* (a declared-before-running, single-shot generation/held-out separation). The
**concrete split — exactly which seeds / parameter regions are generation vs held-out — is part of the v0.4b
numeric pre-registration**, frozen and Codex-reviewed before any implementation. Once frozen there, held-out
families cannot be reassigned to flatter the outcome, and no code may run before that split is frozen.

## 9. Cheap-baseline audit rules

```text
- Adversarial cheap baselines = per_channel, movement_channel_energy, directional, frame_diff (§4 groups),
  run as best-threshold separators over the matched family on HELD-OUT evaluation families.
- A group counts as "closed" only if its best cheap baseline CANNOT separate the classes:
  best-threshold BA <= CHANCE_BAND, where CHANCE_BAND = 0.60 is REUSED from v0.3 as a reporting-only
  shortcut-audit closure band -- it is NOT a §7/§8 threshold, NOT an acceptance criterion, NOT verdict-moving.
- spectral is audit-note-only: never counted as closed on constant-chroma FFT noise, never a match requirement.
- Every group's BA is reported transparently, including OPEN groups, exactly as v0.3 reported its four open
  residual groups. No group is hidden; no OPEN group is rounded up to closed.
- Baseline-BA collapse is an OUTCOME being measured, never a search objective (§7).
```

## 10. Infeasibility / partial-result reporting

```text
- INFEASIBLE (primary honest outcome): if no admissible candidate (PSC < PSC_FLOOR) matches ALL declared
  proxies within the frozen TOL anywhere in the declared space, report Outcome-4-style infeasibility --
  which statistics stayed out of tolerance, the residual magnitudes, and which groups stayed OPEN.
- PARTIAL: if some groups close and others stay open, report per-group, never rounded up to "closed."
- No rescue by moving goalposts: no widening TOL, no narrowing the parameter space, no dropping an
  adversarial baseline, and no post-hoc proxy reselection to force a pass.
- Infeasibility is a VALID result, not a plan failure. Reporting it honestly is the success condition of the
  plan, symmetric with reporting a genuine match.
```

## 11. What would count as useful evidence

The evidence is the search's **matching success or failure** plus the **held-out baseline behaviour** — **not**
any classifier accuracy or decision score.

```text
Match-Feasible
  The search FINDS admissible non-winders (PSC < PSC_FLOOR) that match every declared proxy within frozen TOL
  AND drive each adversarial baseline's best-threshold BA into the CHANCE_BAND on HELD-OUT families, while the
  frozen fixed rule still separates above those baselines.
  Reading (research-only): the proxy wall is NOT fundamental to the winder/canceller family -- a matched family
  is constructible and the frozen rule retains separation the closed cheap proxies lack. Establishes NO vision,
  descriptor validity, or real-world property (see §12).

Match-Infeasible
  The declared space is exhausted with NO all-proxies-matched admissible candidate, residuals bounded away from
  TOL in a stable statistic (e.g. the BY statistics implicated at v0.3).
  Reading (research-only): Outcome-4-style evidence that the obstruction is structural for this fixture family --
  the proxy wall is a property of the construction, not fixable by search within the declared space.
```

A partial result (some proxies close on held-out, others stay open) is itself informative and reported as
partial (§10).

## 12. What would still not be proven

Even a fully successful matched search would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

A matched family plus retained separation would be an **in-vitro synthetic** result about constructible
fixtures; it says nothing about real clips and does not validate the descriptor as measuring real visual
structure. Symmetrically, an infeasibility result would **not** prove the descriptor invalid — only that this
construction route cannot close the shortcuts within the declared space. The claim locks
(`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`, `descriptor_validity_claim_allowed`)
and `verdict = HOLD` remain in force regardless of which outcome a future search returns.

## 13. Recommended next step

```text
1. Codex review THIS meta-plan (docs-only; over committed edge 54daf01).
2. If accepted, commit this meta-plan doc. No §0 pointer; no tags.
3. Before any code, produce the v0.4b NUMERIC PRE-REGISTRATION (separate docs-only, Codex-reviewed) that
   freezes: the TOL constant (§5: extracted from the frozen v0.3 residual convention or explicitly reviewed),
   the exact non-winder parameter grid / ranges / enumerated seeds (§6), and the concrete generation-vs-
   held-out split (§8). No generator may be written until v0.4b is frozen and reviewed.
4. Only THEN, and only on explicit operator instruction, may a SINGLE offline implementation slice implement
   EXACTLY this meta-plan plus the frozen v0.4b numbers -- form A, non-learning, frozen descriptor reused by
   identity, constants reused frozen, delivered UNCOMMITTED for review, Windows the source of truth. Neither
   this meta-plan nor v0.4b authorizes code by itself.
5. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 14. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_MATCHED_GENERATIVE_SEARCH_PLAN_v0.4a.md
(new, docs-only, untracked; over committed edge 54daf01). This is a META-PLAN pre-registering the RULES of
Direction B accepted at v0.4; the numeric pre-registration (TOL, parameter grid/ranges/seeds, gen/eval split)
is explicitly deferred to a later docs-only Codex-reviewed v0.4b before any code.

Verify that this plan:
- is docs-only and authorizes no implementation (no code/tests/generator, no torment_service/, no runtime,
  no memory, no camera/live/sensor/screen/streaming, no real clips);
- is honest about being a META-PLAN: it fixes rules/shape only and requires a separate v0.4b numeric
  pre-registration (TOL + exact parameter grid/ranges/seeds + concrete generation/held-out split) to be frozen
  and reviewed before any implementation; no code is authorized by this doc or by v0.4b alone;
- keeps form B (classifier) and form C (neural encoder) CLOSED; describes only a form-A, non-learning,
  baseline-gated, offline generator/probe over fixture PARAMETERS;
- pre-registers the proxy set as EXACTLY the four v0.3 OPEN groups (per_channel, movement_channel_energy,
  directional, frame_diff) -- a CLOSED set, additions/removals require a new reviewed revision -- with per-stat
  membership REUSED BY IDENTITY from the frozen v0.3 GROUPS mapping and transcribed correctly (rg_std/by_std
  under movement_channel_energy; per_channel = rg_centroid/by_centroid/rg_spread/by_spread; directional =
  u_directional_delta_rms/angular_increment_mag; frame_diff = delta_rms); and treats spectral as audit-note-
  only (never a match requirement, never a closure claim on constant-chroma FFT noise);
- sets the search objective to proxy_match_residual under the SOLE feasibility constraint PSC < PSC_FLOOR (no
  other frozen-descriptor gating folded into the objective; the neutral/validity behaviour is a non-gating
  descriptor-sanity note only), and FORBIDS optimizing PSC/AIC balanced accuracy, the fixed-rule decision
  score, any classifier score, S_best_threshold, the separation margin, the adversarial cheap-baseline BA, or
  any post-hoc shortcut metric;
- invents NO numeric threshold: PSC_FLOOR/AIC_FLOOR (0.30) and CHANCE_BAND (0.60) are referenced as frozen,
  and TOL is explicitly deferred to extraction from the frozen v0.3 residual convention or to a pre-registered
  Codex-reviewed constant -- never fixed by fiat here;
- defers the exact non-winder parameter grid/ranges/seeds and the concrete held-out split to v0.4b, while
  fixing the family list and the single-shot generation/held-out RULE here, and forbids post-hoc narrowing /
  goalpost-moving / TOL-loosening / baseline-dropping to force a pass;
- makes held-out evaluation single-shot and requires honest infeasibility / partial-result reporting as a
  valid outcome;
- states both useful outcomes (match-feasible / match-infeasible) as research-only signals that upgrade no
  claim, and preserves all claim locks (first_pass_structure_validity_claim_allowed = False;
  temporal_claim_allowed = False; descriptor_validity_claim_allowed = False) and verdict = HOLD;
- makes no vision / "Brainvision sees" / temporal-order / descriptor-validity / memory-readiness /
  runtime-readiness / integration-readiness claim; adds no §0 pointer and no tags.

Flag any invented threshold, any objective that would let the generator optimize a decision/baseline score,
any post-hoc goalpost movement, any weakening of a v0.4 safeguard, any implicit opening of B/C or
runtime/memory/real-clips, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Matched Generative Search Plan v0.4a. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural work; changes no frozen formula, gate, or verdict; deletes or
weakens no control; redesigns no descriptor; invents no threshold; makes no vision / descriptor-validity /
temporal-order / memory / runtime / integration claim; no `§0` pointer added; no tags.*
