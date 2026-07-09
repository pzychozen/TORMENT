# TORMENT Brainvision Matched Generative Search Pre-Registration v0.4b

## 1. Status / non-claims

**DOCS-ONLY pre-registration. Non-authorizing, non-implementing. Opens no code, no tests, no generator, no
runtime, no integration lane.** It freezes the tolerance policy and the protocol rules a *future* Direction-B
matched-generative-search implementation must obey, so that if such a slice is ever separately gated it cannot
be tuned toward a win. It does **not** close the exact numeric enumeration (per-family grid / ranges /
enumerated seeds + development-vs-held-out split); that remaining numeric layer is a **later docs-only,
Codex-reviewed enumeration appendix/amendment** to be frozen before any code (§2, §8, §14). Pre-registering
rules is **not** authorizing implementation: no code is authorized by this document; any implementation still
requires separate explicit operator instruction (§14). It **authorizes no code and no
tests**, invents no threshold, changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens
no control, redesigns no descriptor, and opens **no classifier (form B) and no neural encoder (form C)**.
Everything discussed stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. Brainvision Path B remains **not
proven vision** and **not a functioning vision layer for TORMENT memory**. A pre-registration alone moves
nothing: **no claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v0.4 and v0.4a

```text
v0.4  (54daf01)  accepted Direction B (matched generative search) but opened no implementation.
v0.4a (80a6242)  demoted B to a META-PLAN: fixed the rules/shape, deferred the concrete numbers to v0.4b.
v0.4b (this doc) closes TOL and the protocol rules; the remaining numeric enumeration is closed by a later
                 reviewed enumeration appendix/amendment (§8, §14) before any code.
```

v0.4a fixed the *shape*: closed proxy set, `proxy_match_residual` objective, `PSC < PSC_FLOOR` feasibility,
forbidden objectives, single-shot held-out, honest reporting; it deferred the concrete numbers to v0.4b.

**Scope of v0.4b — what it DOES close** (by reference to frozen v0.3 sources, inventing no new constants):

```text
- the tolerance policy: TOL (§7);
- the closed proxy set (§4), feasibility constraint (§5), and proxy-match residual definition (§6);
- the protocol rules: closed non-winder FAMILY SET + bounded axes (§8), single-shot held-out RULE (§9),
  forbidden objectives / tuning (§10), reporting outcomes (§11).
```

**What it does NOT close (deferred, honestly):** the exact numeric ENUMERATION — the per-family grid / ranges /
enumerated seeds and the concrete development-vs-held-out split. Four of the five families (§8) have no frozen
numeric grounding, so fixing those numbers here would mean inventing constants, which the boundaries forbid.
They are therefore closed by a **later docs-only, Codex-reviewed enumeration appendix/amendment**, frozen and
reviewed before any code (§8, §14). Where v0.4b is more specific than v0.4a it only tightens; it relaxes no
v0.4/v0.4a safeguard.

## 3. Frozen source anchors

All machinery is **reused by identity** from frozen, committed code; this document authors no new descriptor,
generator, or constant. Anchors:

```text
research/brainvision/run_all_shortcuts_closed_synthetic_v0_3.py
    GROUPS               (the frozen cheap-shortcut mapping; see §4)
    ALL_PROXIES          (dedup union of all GROUPS stats, incl. spectral)
    _linf_residual(a,b)  = max(|a[s]-b[s]| for s in ALL_PROXIES)   -- raw absolute deltas, L-inf, no rescale
    _feat(gen)           (descriptor+stats feature dict; incl. PSC/AIC/S and _chroma_constant flag)
    CHANCE_BAND = 0.60   (reporting-only shortcut-audit band)
run_color_structure_v0_8.py            structure_score, _stats, PSC_FLOOR = 0.30, AIC_FLOOR = 0.30, T
run_color_structure_spectral_std_blocker_v1_9.py   winder / outback / arc / collinear generators (v9)
run_color_structure_by_std_residual_v2_0.py        winder(radius) generator (v20)

Frozen evaluator (UNCHANGED):   structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR
Frozen v0.3 residual convention: best-effort matched family achieved L-inf proxy residual 0.0404-0.0634
                                 (reported in the committed v0.3 findings; see §7)
```

No numeric value in this document is invented: `PSC_FLOOR` / `AIC_FLOOR` (0.30), `CHANCE_BAND` (0.60), the
`GROUPS` membership, and the residual band (0.0404-0.0634) are all referenced from frozen code / committed
findings.

## 4. Closed proxy GROUPS mapping

The proxy set is **exactly** the frozen v0.3 `GROUPS` mapping (transcribed from
`run_all_shortcuts_closed_synthetic_v0_3.py`, line 48; reused by identity, not re-authored):

```text
movement_channel_energy : rg_std, by_std, chroma_mag, delta_rms
directional             : u_directional_delta_rms, angular_increment_mag
spectral                : spectral_centroid, spectral_spread        # AUDIT-NOTE-ONLY (see below)
per_channel             : rg_centroid, by_centroid, rg_spread, by_spread
frame_diff              : delta_rms
```

Note (matching v0.3 exactly): `rg_std` / `by_std` belong to `movement_channel_energy`, **not** to
`per_channel`; `per_channel` is the centroid / spread statistics only.

**Matched groups (the search must match these four):** `movement_channel_energy`, `directional`,
`per_channel`, `frame_diff`. **`spectral` is AUDIT-NOTE-ONLY**: on the constant-chroma family its
`spectral_centroid` / `spectral_spread` are FFT-of-a-constant numerical noise (v0.3 §6), so spectral is
**never a match requirement and never a closure criterion**, reported transparently as not-a-usable-shortcut.

**The proxy set is CLOSED.** Adding, removing, substituting, or re-weighting any group or statistic requires a
new docs-only, Codex-reviewed amendment before implementation — never at implementation time, never after
seeing results.

## 5. Search feasibility constraint

```text
A candidate non-winder is FEASIBLE (admissible as non-structure) iff:   PSC(candidate) < PSC_FLOOR
```

`PSC` is computed by the frozen `structure_score` (reused by identity). This is the **sole** non-structure
feasibility constraint. **No AIC constraint is added.** Justification (no new logic): the frozen evaluator
labels "structure" only when `PSC >= PSC_FLOOR` **and** `AIC >= AIC_FLOOR`; therefore `PSC < PSC_FLOOR` is
already sufficient for the evaluator to return non-structure, regardless of `AIC`. Adding an `AIC` condition
would invent a constraint not required by the frozen rule, so it is **not** added.

Candidates with `PSC >= PSC_FLOOR` are rejected as invalid (they would be structure) and are not counted toward
feasibility or infeasibility.

## 6. Proxy-match residual definition

```text
MATCHED_STATS = dedup union of the four MATCHED groups' statistics (spectral excluded):
  rg_std, by_std, chroma_mag, delta_rms,
  u_directional_delta_rms, angular_increment_mag,
  rg_centroid, by_centroid, rg_spread, by_spread
  (delta_rms is shared by movement_channel_energy and frame_diff -> counted once; 10 unique statistics)

proxy_match_residual(candidate, target_winder)
    = max over s in MATCHED_STATS of | feat(candidate)[s] - feat(target_winder)[s] |
```

This reuses the frozen v0.3 `_linf_residual` convention **exactly** — raw absolute per-statistic deltas,
L-inf (worst-stat max), no per-statistic rescaling — **restricted to `MATCHED_STATS`**. The only difference
from v0.3's `_linf_residual` (which ranges over `ALL_PROXIES`) is the **declared exclusion of the two spectral
statistics**, because spectral is audit-note-only on the constant-chroma family (§4). This is a scoping of the
match target, **not** a descriptor change and **not** a control weakening: spectral is still computed and
reported as an audit note; it is only removed from the *match objective*, where FFT-of-a-constant noise would
otherwise be matched as if meaningful.

`feat(...)` is the frozen v0.3 `_feat` (descriptor + stats), reused by identity. The worst-stat (L-inf) form is
retained deliberately so one statistic cannot hide behind an average.

## 7. Tolerance policy

Tolerance is closed here by **reference to the frozen v0.3 residual convention** (Option A) — no magic number
is invented:

```text
Match criterion:
    a candidate MATCHES its target winder iff  proxy_match_residual(candidate, target) <= TOL

TOL (referenced, not invented):
    TOL := the frozen v0.3 best-effort L-inf residual CEILING = 0.0634
           (the upper end of v0.3's reported achieved band 0.0404-0.0634, committed in the v0.3 findings).
    Meaning: the search must match AT LEAST as tightly as v0.3's best hand-built attempt did.

Conservativeness note:
    v0.3's band was measured over ALL_PROXIES (incl. spectral); MATCHED_STATS is a subset, so the matched-stat
    residual is <= the ALL_PROXIES residual for the same fixtures. Hence 0.0634 is a conservative UPPER
    reference for the matched-stat residual, not a loosening.

Necessary-not-sufficient:
    matching at TOL is NECESSARY to call a fixture "matched" but is NOT the success criterion. v0.3 already
    achieved residuals <= 0.0634 and the cheap baselines STILL separated; the actual evidence is the held-out
    baseline audit (§9). TOL only defines "matched," it does not declare victory.

Guardrails:
    - TOL is frozen BEFORE any code and is NEVER loosened post-hoc.
    - a fixture that only "matches" after TOL is widened is reported as NOT matched.
    - a stricter TOL may be set only by a reviewed docs-only amendment before code; it may never be loosened.
```

The tolerance policy is thereby **closed before code** and is explicitly not derived from seeing any future
search result.

## 8. Non-winder parameter-space boundaries

The candidate non-winder generator space is a **closed set of families**. The future implementation may
sample / search **only inside** this declared space.

```text
Closed family set (conceptual; CLOSED):
  F1  full-circle incoherent traversal        (full channel coverage, phase incoherent -> PSC low)
  F2  rosette / multi-lobe traversal          (multi-lobe coverage without net winding)
  F3  segment-paired cancellers               (paired out/back segments; net turn cancels; cf. v0.3 outback)
  F4  phase-scrambled full-coverage trajectories (coverage preserved, per-step phase scrambled)
  F5  hybrid coverage-preserving cancellers    (declared combinations of F1-F4)

Per-family parameter AXES (the KIND of knobs; CLOSED):
  angular schedule / increment, lobe count, segment pairing, phase-scramble structure + seed, radius/amplitude.

Bounding rule (no unbounded ranges, no invented magic numbers):
  - each axis is BOUNDED; where a family overlaps a frozen v0.3/v9/v20 generator (e.g. F3 vs the frozen outback
    increments), its numeric range is REUSED from that frozen generator by reference;
  - any axis endpoint not grounded in a frozen generator must be written down in a PRE-COMMIT enumeration
    (below) and Codex-reviewed before code; it is never invented silently in implementation.

Numeric enumeration (DEFERRED -- NOT closed in this v0.4b doc):
  - the exact per-family grid / ranges / enumerated seeds AND the concrete development-vs-held-out split are
    closed by a LATER docs-only, Codex-reviewed enumeration appendix/amendment, frozen before any code;
  - the search samples ONLY from that committed enumeration; no code runs until it is frozen and reviewed.

Immutability:
  - NO narrowing of the space after results.
  - NO adding a new family after seeing failures/successes.
  - any change to the family set, axes, bounds, or enumeration requires a NEW docs-only amendment reviewed
    BEFORE re-running.
```

Every sampled candidate must additionally pass the §5 feasibility constraint (`PSC < PSC_FLOOR`); candidates
that are actually winding are discarded, not counted.

## 9. Held-out evaluation rule

```text
- Search / development families and HELD-OUT evaluation families are SEPARATE and declared before running.
- The search / matching runs ONLY on development families.
- The frozen evaluator (§3) AND the cheap-baseline audit run on HELD-OUT families the search never saw
  (held-out winder seeds / parameter regions, produced by the same frozen winder generators).
- Cheap-baseline audit: per_channel, movement_channel_energy, directional, frame_diff run as best-threshold
  separators; a group is "closed" only if its best cheap baseline CANNOT separate (best-threshold BA <=
  CHANCE_BAND = 0.60, reused reporting-only). spectral is audit-note-only. Every group's BA is reported,
  including OPEN ones; no group hidden, no OPEN group rounded up.
- Held-out evaluation is SINGLE-SHOT: no tuning, no re-selection, no parameter-space edit, no TOL change
  after seeing held-out results.
- If held-out fails, report failure / partial (§11); do NOT iterate invisibly.
```

The development/held-out split (which seeds / parameter regions fall in each) is part of the §8 pre-commit
enumeration, fixed before running so held-out families cannot be reassigned to flatter the outcome.

## 10. Forbidden objectives and forbidden tuning

The generator's **only** objective is `proxy_match_residual` (§6) under the §5 feasibility constraint. The
generator must NOT optimize, target, or use as a stopping criterion any of:

```text
- the final fixed-rule decision score
- PSC/AIC balanced accuracy
- any classifier score
- S_best_threshold
- label accuracy
- held-out performance (of the evaluator or the baselines)
- any post-hoc shortcut metric chosen AFTER seeing results
- "tuning until cheap baselines look chance-like" (baseline collapse is an EVALUATED consequence on held-out,
  never a search target)
```

Forbidden tuning (protocol breaches, §11):

```text
- loosening TOL, narrowing the parameter space, dropping an adversarial baseline, or re-selecting proxies to
  force a pass;
- adding a family or editing the enumeration after seeing results;
- iterating on held-out families;
- feeding evaluator / baseline outcomes back into the generator objective.
```

The generator is **blind** to the frozen evaluator's decision and to the baselines' accuracy while it searches;
those are measured only afterward, on held-out.

## 11. Reporting outcomes

All outcomes are reported honestly; under every outcome the claim locks and verdict are **unchanged**.

```text
Match-feasible
  admissible non-winders (PSC < PSC_FLOOR) match every MATCHED group within TOL AND, on HELD-OUT families,
  drive each adversarial baseline's best-threshold BA into CHANCE_BAND, while the frozen evaluator still
  separates above the baselines.

Match-infeasible
  the committed parameter-space enumeration is exhausted with NO all-groups-matched admissible candidate;
  residuals bounded away from TOL in a stable statistic (e.g. the BY statistics implicated at v0.3).

Partial
  some groups close on held-out, others stay open; reported per-group, never rounded up to "closed."

Invalid / protocol breach
  any §10 forbidden objective or forbidden tuning occurred, or a candidate failed §5 feasibility, or the
  held-out single-shot rule was violated -> the run is INVALID and reported as such; its numbers carry no
  evidential weight and move no claim.
```

## 12. What would count as useful evidence

The evidence is the search's **matching success/failure** plus the **held-out baseline behaviour** — **not**
any decision score, classifier accuracy, or label accuracy.

```text
Match-feasible reading (research-only):
  the proxy wall is NOT fundamental to the winder/canceller family -- a matched family is constructible and the
  frozen evaluator retains separation the closed cheap proxies lack. Establishes NO vision / validity / real-
  world property (§13).

Match-infeasible reading (research-only):
  Outcome-4-style evidence that the obstruction is structural for this fixture family -- the proxy wall is a
  property of the construction, not fixable by search within the committed space.
```

A partial result is itself informative and reported as partial (§11). An invalid run is evidence of nothing.

## 13. What would still not be proven

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
construction route cannot close the shortcuts within the committed space. The claim locks
(`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`, `descriptor_validity_claim_allowed`)
and `verdict = HOLD` remain in force under every §11 outcome.

## 14. Recommended next step

```text
1. Codex review THIS pre-registration (docs-only; over committed edge 80a6242).
2. If accepted, commit this pre-registration doc. No §0 pointer; no tags.
3. Produce the deferred numeric ENUMERATION appendix/amendment (exact per-family grid / ranges / seeds +
   concrete development/held-out split) as a docs-only, Codex-reviewed step, frozen before any code.
4. Only THEN, and only on explicit operator instruction, may a SINGLE offline implementation slice implement
   EXACTLY this pre-registration + the committed enumeration -- form A, non-learning, frozen descriptor /
   generators / constants reused by identity, delivered UNCOMMITTED for review, Windows the source of truth.
   Neither this doc nor the enumeration authorizes code by itself.
5. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 15. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_MATCHED_GENERATIVE_SEARCH_PREREG_v0.4b.md
(new, docs-only, untracked; over committed edge 80a6242). This doc closes TOL and the protocol rules; the
remaining numeric enumeration (per-family grid/ranges/seeds + concrete development/held-out split) is
explicitly DEFERRED to a later docs-only Codex-reviewed enumeration appendix/amendment before any code.

Verify that this pre-registration:
- is docs-only and authorizes no implementation (no code/tests/generator, no torment_service/, no runtime,
  no memory, no camera/live/sensor/screen/streaming, no real clips); pre-registration is NOT authorization;
- keeps form B (classifier) and form C (neural encoder) CLOSED; describes only a form-A, non-learning,
  baseline-gated, offline generator/probe over fixture PARAMETERS;
- transcribes the frozen v0.3 GROUPS mapping correctly (rg_std/by_std under movement_channel_energy; per_channel
  = rg_centroid/by_centroid/rg_spread/by_spread; directional = u_directional_delta_rms/angular_increment_mag;
  frame_diff = delta_rms; spectral = spectral_centroid/spectral_spread) and keeps the proxy set CLOSED, with
  spectral audit-note-only (never a match requirement, never a closure claim on constant-chroma FFT noise);
- sets the SOLE non-structure feasibility constraint to PSC < PSC_FLOOR (no AIC constraint added), and keeps
  the frozen evaluator (structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR) unchanged;
- defines proxy_match_residual as the L-inf max over MATCHED_STATS reusing v0.3's raw-delta _linf_residual
  convention, restricted to the matched groups (spectral excluded as a declared scoping, not a descriptor
  change);
- closes the tolerance policy by REFERENCE (TOL = frozen v0.3 residual ceiling 0.0634, necessary-not-sufficient,
  frozen before code, never loosened) and invents NO threshold (PSC_FLOOR/AIC_FLOOR 0.30, CHANCE_BAND 0.60
  referenced frozen);
- declares a CLOSED non-winder family set with bounded axes HERE, and honestly DEFERS the exact grid / ranges /
  seeds + concrete development/held-out split to a later Codex-reviewed enumeration appendix/amendment frozen
  before code, forbidding post-hoc narrowing / family-adding / TOL-loosening / baseline-dropping;
- does NOT overclaim: §2 states plainly that v0.4b closes TOL + protocol rules only and does not close the
  numeric enumeration, consistent with §8/§9;
- makes held-out evaluation single-shot with honest match-feasible / match-infeasible / partial / invalid
  reporting, and FORBIDS optimizing the decision score, PSC/AIC BA, any classifier score, S_best_threshold,
  label accuracy, held-out performance, any post-hoc shortcut metric, or tuning-until-baselines-look-chance;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed =
  False; descriptor_validity_claim_allowed = False) and verdict = HOLD under every outcome;
- makes no vision / "Brainvision sees" / temporal-order / descriptor-validity / memory-readiness /
  runtime-readiness / integration-readiness claim; adds no §0 pointer and no tags.

Flag any invented threshold, any AIC feasibility constraint, any objective that would let the generator
optimize a decision/baseline/label score, any post-hoc goalpost movement, any GROUPS mistranscription, any
weakening of a v0.4/v0.4a safeguard, any implicit opening of B/C or runtime/memory/real-clips, or any
claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Matched Generative Search Pre-Registration v0.4b. Docs-only, non-authorizing. Opens
no implementation lane; opens no classifier / neural work; changes no frozen formula, gate, or verdict; deletes
or weakens no control; redesigns no descriptor; invents no threshold; makes no vision / descriptor-validity /
temporal-order / memory / runtime / integration claim; no `§0` pointer added; no tags.*
