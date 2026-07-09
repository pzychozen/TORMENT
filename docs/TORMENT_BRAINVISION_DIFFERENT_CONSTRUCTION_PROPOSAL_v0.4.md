# TORMENT Brainvision Different-Construction Proposal v0.4

## 1. Status / non-claims

**DOCS-ONLY proposal. Non-authorizing, non-implementing. Opens no runtime, integration, or implementation
lane.** It proposes — for future, separately-gated consideration only — a *fundamentally different synthetic
construction direction* than the current winder/canceller fixture route, whose purpose is to test whether the
**proxy wall** reported at v0.3 is fundamental or merely a limitation of the current fixture family. It
**authorizes no code and no tests**, invents no threshold, changes no formula / §7 anti-proxy logic / §8
verdict logic, deletes or weakens no control, redesigns no descriptor, and opens **no classifier (form B) and
no neural encoder (form C)**. Everything discussed stays offline under `research/brainvision/` +
`tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. Brainvision Path B remains **not
proven vision** and **not a functioning vision layer for TORMENT memory**. A proposal alone moves nothing:
**no claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Why v0.3 held the current route

The v0.3 all-shortcuts-closed falsifier (`9877f35`) tried to match or neutralize **all** cheap shortcut groups
simultaneously between the two labels, while keeping the SAME fixed frozen rule:

```text
structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR
```

It reached **Outcome 4**: the all-shortcuts-closed construction was **infeasible** with the current hand-built
generators.

```text
all_shortcuts_closed          = False
construction_feasible         = False
outcome                       = Outcome_4
research_signal               = unresolved_proxy_wall_remains

fixed color rule BA           = 1.000        (PSC_only 1.000; AIC_only 0.500)
best-effort match L-inf resid = 0.0404 - 0.0634
shuffled-label control        = ~0.5011      (~chance)

cheap baselines still separate (best-threshold, reporting-only):
  per_channel             = 0.938   (OPEN residual shortcut)
  movement_channel_energy = 0.812   (OPEN residual shortcut)
  directional             = 0.738   (OPEN residual shortcut)
  frame_diff              = 0.675   (OPEN residual shortcut)
  spectral                = 0.700   (ill-defined on constant chroma; not a usable shortcut)
```

The obstruction was **geometric, not tuning**: matching the directional per-step increment
(`u_directional_delta_rms` / `angular_increment_mag`) conflicts with matching full symmetric channel coverage
(`rg_std` = `by_std`, per-channel centroids / spreads). A coherent winder traverses the full circle uniformly,
while a winding-cancelling out-and-back that matches the per-step increment covers only a partial arc — leaving
residual per-channel / BY differences (residuals concentrated in `by_std`, `by_centroid`, `by_spread`).

The honest reading was: hand-picking one "best-matched" canceller per winder cannot close all groups at once,
so residual cheap proxies still separate and the **proxy wall stands**. Continuing to patch the *same* generator
route risks fixture-chasing (tuning until a fixture happens to pass) rather than answering whether the wall is
fundamental. Hence the line was HELD and this proposal opens a *different* construction question instead of
another patch to the same route.

## 3. Candidate construction directions

Four directions are compared. All remain form A (non-learning, fixed frozen rule), baseline-gated, and offline.

```text
A. Different non-winder geometry
   Replace the out-and-back canceller with a non-structure geometry that CAN traverse the full circle
   (so channel coverage matches the winder) yet still fails PSC (incoherent / scrambled phase; e.g. a
   full-circle traversal with randomized per-step phase, or a multi-lobe rosette covering all channels).
   Pro: attacks the exact directional-increment-vs-channel-coverage tension head-on.
   Con: still ONE hand-built family; high fixture-chasing risk; may only relocate the residual shortcut.

B. Matched generative search
   Instead of hand-picking a canceller, run an OFFLINE generator/probe that SEARCHES a declared,
   parameterized non-winder family for fixtures matching the winders on ALL declared cheap proxies within a
   pre-declared tolerance, subject to the hard constraint PSC < PSC_FLOOR (non-structure by the frozen rule).
   The search optimizes a PROXY-MATCH residual under a PSC-below-floor constraint; it never optimizes the
   PSC/AIC decision score. If no matched non-winder exists across the declared space, that infeasibility is
   itself a valid result.
   Pro: systematic; subsumes A's geometries as search candidates; turns "couldn't hand-build it" into a
        falsifiable search whose failure is informative.
   Con: needs a carefully pre-registered proxy set / tolerance / parameter space to avoid dressed-up
        fixture-chasing; search infrastructure is more work than a single fixture.

C. Change target away from binary winder/canceller
   Drop the two-class winder-vs-canceller contrast for a different structure/non-structure target (e.g. a
   graded coherence continuum, or a structured/unstructured pair not built on winding at all).
   Pro: escapes the specific geometry whose obstruction created the wall.
   Con: changes what "structure" denotes; hard to compare against prior Path B; risks goalpost-moving and
        descriptor-validity drift; would need its own baseline-gating from scratch.

D. Hold synthetic fixture route and move to another TORMENT layer
   Accept that the proxy wall may be a fundamental limit of hand-built synthetic fixtures, stop constructing
   fixtures, and redirect effort to a different TORMENT layer entirely.
   Pro: the honest "stop digging here" option; spends no further effort on a possibly-unanswerable question.
   Con: yields no new evidence about whether the wall is fundamental; leaves the question open by abandonment.
```

## 4. Recommended direction

**Recommended: B — Matched generative search, docs-only first.**

B is the most direct test of the central question (is the proxy wall fundamental, or a limitation of the current
winder/canceller family?). It converts v0.3's "we could not hand-build a matched canceller" into a *systematic*
offline search whose outcome is informative **either way**: a matched family found, or a declared-space
infeasibility that strengthens "the wall is structural for this family."

B is preferred over the alternatives:

```text
vs A  A is one hand-built alternative geometry and is exactly the kind of single fixture that invites
      fixture-chasing. B generalizes A: A's full-circle / rosette geometries become candidate points inside
      B's declared search space, evaluated systematically rather than tuned by hand.
vs C  C changes the meaning of "structure" and risks moving the goalposts and drifting toward a descriptor-
      validity claim the locks forbid; it also forfeits comparability with prior Path B.
vs D  D forecloses the question by abandonment. B can reach the same "stop here" conclusion but only AFTER a
      declared search returns honest infeasibility, so the HOLD is then evidence-backed rather than assumed.
```

**Scope guard (what B is and is not).** Matched generative search is **not model training** and **not
classifier / neural work**. It is an offline generator/probe over fixture *parameters*, not a learned model
over weights. The generator may search for cancellers (or other non-winders) that match cheap proxy statistics
against the winders while keeping **PSC below floor**, but it **must not optimize the final PSC/AIC decision
score (or any classifier score) directly**. The frozen fixed rule is applied *after* the search, unchanged, as
the evaluator — never as the search objective.

This section recommends only that a **separate, future, docs-only PLAN** for B be considered. It opens no
search, no generator, no code, and no test here.

## 5. Anti-fixture-chasing safeguards

Any future B plan must carry all of the following, or it should not be opened:

```text
S1  Fixed PSC/AIC rule is FROZEN and unchanged. The search touches neither the rule, PSC_FLOOR, AIC_FLOOR,
    the §7 anti-proxy logic, nor the §8 verdict logic.
S2  No threshold invention. PSC_FLOOR / AIC_FLOOR stay frozen; the reporting-only shortcut-audit band
    (CHANCE_BAND = 0.60) stays reporting-only and is not promoted to any acceptance or verdict gate.
S3  Generator cannot optimize the final decision score. Search objective = proxy-match residual under the
    hard constraint PSC < PSC_FLOOR; the PSC/AIC balanced accuracy and any S/best-threshold score are
    forbidden as objectives or stopping criteria.
S4  Target proxy matching declared BEFORE implementation. The exact proxy statistic set, per-stat tolerance,
    non-winder parameter space, and match criterion are pre-registered in the plan doc and committed before
    any code exists — no post-hoc redefinition of "matched."
S5  Cheap baselines remain ADVERSARIAL comparators. per_channel, movement_channel_energy, directional, and
    frame_diff stay adversaries; a "match" counts only if it drives their best-threshold BA toward the
    reporting-only chance band. spectral stays flagged ill-defined on constant chroma (not a usable shortcut).
S6  Generated families include HELD-OUT evaluation families. The search runs on one generated set; the frozen
    rule and the adversarial baselines are evaluated on unseen generated families to prevent overfitting the
    search to a single fixture batch.
S7  Failed matching is reported HONESTLY. If no non-winder in the declared space matches all declared proxies
    within tolerance while holding PSC below floor, that is an Outcome-4-style infeasibility result and is
    reported as such — not forced, not narrowed until something passes.
S8  No claim-lock movement from a proposal (or from a search) alone. Locks and verdict move only through a
    separate, explicitly-gated decision, never as a side effect of building or running the search.
```

## 6. What would count as useful evidence

The search's own matching success or failure is the evidence — **not** any downstream classifier accuracy. Two
symmetric outcomes are both informative:

```text
Outcome-Match-Feasible
  The search FINDS non-winders that match every declared cheap proxy within tolerance AND drive each
  adversarial baseline's best-threshold BA into the reporting-only chance band on HELD-OUT generated
  families, while the frozen PSC/AIC rule still separates above those baselines.
  Reading (research-only): the proxy wall is NOT fundamental to the winder/canceller family — a matched
  family is constructible and the frozen rule retains separation the closed cheap proxies lack. This does
  NOT establish vision, descriptor validity, or any real-world property (see §7).

Outcome-Match-Infeasible
  The search CANNOT find such matched non-winders across the declared parameter space, with residuals
  bounded away from tolerance in a stable statistic (e.g. the BY statistics implicated at v0.3).
  Reading (research-only): Outcome-4-style evidence that the obstruction is structural for this fixture
  family — the proxy wall is a property of the construction, not fixable by search within the declared space.
```

Both outcomes answer the central question honestly. A null / partial result (some proxies close, others stay
open) is reported as partial, exactly as v0.3 reported its four open residual groups.

## 7. What would still not be proven

Even a fully successful matched search would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

Specifically: a matched family plus retained separation would be an **in-vitro synthetic** result about
constructible fixtures; it says nothing about real clips and does not validate the descriptor as measuring real
visual structure. Symmetrically, an infeasibility result would **not** prove the descriptor invalid — only that
this construction route cannot close the shortcuts within the declared space. The claim locks
(`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`, `descriptor_validity_claim_allowed`)
and `verdict = HOLD` remain in force regardless of which outcome the (future) search returns.

## 8. Recommended next step

```text
1. Codex review THIS proposal (docs-only; over the v0.3 committed edge 9877f35).
2. If accepted, commit this proposal doc. No §0 pointer; no tags.
3. Only if the operator explicitly instructs it, open a SEPARATE, future, docs-only PLAN for direction B that
   pre-registers S4's declared proxy set / tolerance / parameter space / held-out split and the S5 adversarial
   baselines BEFORE any code. That plan, too, opens no code/tests until separately gated.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 9. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_DIFFERENT_CONSTRUCTION_PROPOSAL_v0.4.md
(new, docs-only, untracked; over committed edge 9877f35, following the v0.3 all-shortcuts-closed falsifier).

Verify that this proposal:
- is docs-only and opens no implementation (no code/tests, no new non-doc files, no torment_service/, no
  runtime, no memory, no camera/live/sensor/screen/streaming, no real clips);
- keeps form B (classifier) and form C (neural encoder) CLOSED; proposes only a form-A, non-learning,
  baseline-gated, offline generator/probe;
- recommends direction B (matched generative search) as a FUTURE, separately-gated, docs-only plan, and opens
  no search / generator / code here;
- makes the scope guard explicit: the generator searches over fixture PARAMETERS for proxy-matched non-winders
  with PSC below floor, and MUST NOT optimize the PSC/AIC (or any classifier) decision score directly;
- invents no threshold (PSC_FLOOR / AIC_FLOOR frozen; CHANCE_BAND stays reporting-only), redesigns no
  descriptor, weakens no control, and changes no §7/§8 logic;
- carries the anti-fixture-chasing safeguards S1-S8 (declared-before-implementation proxy matching, adversarial
  cheap baselines, held-out evaluation families, honest infeasibility reporting, no claim-lock movement);
- states both useful outcomes (match-feasible / match-infeasible) as research-only signals and does NOT let
  either upgrade any claim;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed =
  False; descriptor_validity_claim_allowed = False) and verdict = HOLD;
- makes no vision / "Brainvision sees" / temporal-order / descriptor-validity / memory-readiness /
  runtime-readiness / integration-readiness claim; adds no §0 pointer and no tags.

Flag any overclaim, any implicit opening of B/C or runtime/memory/real-clips, any objective that would let the
generator optimize the decision score, any weakening of the safeguards, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Different-Construction Proposal v0.4. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural work; changes no frozen formula, gate, or verdict; deletes or
weakens no control; redesigns no descriptor; invents no threshold; makes no vision / descriptor-validity /
temporal-order / memory / runtime / integration claim; no `§0` pointer added; no tags.*
