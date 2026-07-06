# TORMENT Brainvision SAG Redesign Proposal v0.9

## 1. Status

**DOCS-ONLY proposal. Non-authorizing, non-implementing. Opens no runtime, integration, or implementation
lane.** This note **predeclares candidate redesign directions and acceptance tests before any tuning or
math is written**, so a later diagnostic is judged against criteria fixed in advance. It implements no
code, changes no tests, and touches no `torment_service/`, runtime, camera/sensor/live-capture, prompt/
context/memory/action/render-body/autonomy paths. **No `§0` pointer; no tags.** Everything stays offline
under `research/brainvision/` + `tests/research/`, HELD per v0.6. Nothing here is an accepted fix.

## 2. Failure modes from v0.4–v0.8

The controls, anatomy, and parameter sweeps established (offline, characterization not proof):

- current SAG is **not temporal-order-specific**;
- **shuffled / reversed / shifted controls amplify like true windows** (time_shuffled median ≥ true median
  on 9/9 real clips);
- **κ=0 coherence is not universal** (k0_coherent_rate ≈ 0.536 in the v0.8 sweep);
- **low-amplitude fields break the baseline** (no eps rescued scale-0.01 fields);
- **gain is scale-sensitive** (only partly tracks eps/energy, corr ≈ 0.443);
- **spike-injected fields amplify more than smooth ones**;
- the **κ response rose sharply across the tested range** (no smooth/bounded regime observed).

## 3. Candidate redesign directions

Framed as **candidates to evaluate, not accepted fixes**:

- **scale-normalized perturbation** — set the mirror-perturbation eps relative to field energy or a robust
  norm, so gain does not move with raw amplitude;
- **low-energy floor / skip / neutral handling** — flat and tiny-amplitude fields should not produce fake
  giant gain; below a floor, report neutral / non-amplifying under a predeclared rule;
- **bounded or regularized κ response** — prevent the unbounded-looking gain growth across κ;
- **robust gain statistic** — use a median or trimmed statistic rather than mean/max, so a single window
  cannot carry the result;
- **temporal-control score** — a diagnostic in which true windows must **beat shuffle / reverse / circular
  controls by robust statistics**, as a first-class part of the score rather than an afterthought.

## 4. Acceptance tests before any temporal-order claim can resume

A future diagnostic must, predeclared:

- keep **κ=0 coherent** across the intended field / amplitude ranges;
- **avoid giant low-energy artifacts**;
- **reduce scale sensitivity** across amplitude multipliers;
- **avoid spike-only wins**;
- show **true windows exceed shuffled / reversed / circular controls by median or a robust score**;
- **pass across heterogeneous prerecorded clips and synthetic controls**, not one favorable case;
- keep **classification secondary / non-authorizing**.

## 5. Failure criteria (reject or pause)

Reject or pause any redesign if:

- **shuffled / reversed controls still match or beat true**;
- **low-energy fields still break κ=0**;
- **gain still mostly follows amplitude scale or κ explosion**;
- **success depends on spike-heavy means / maxima**;
- **parameters are tuned after looking at real-clip outcomes** (post-hoc tuning invalidates the result).

## 6. Forbidden moves

No runtime integration; no live capture; no service / camera / sensor contact; no prompt / context /
memory / action / render-body / autonomy contact; **no `§0` pointer; no tags;** no theory inflation; and no
"Brainvision works" or classifier-superiority claim.

## 7. Recommended next

**Codex reviews this proposal.** Only after a PASS should an offline research slice be considered —
likely a **v1.0 candidate diagnostic harness under `research/brainvision/` only**, built against the §4
acceptance tests and §5 failure criteria, with controls first-class and parameters fixed before real-clip
inspection. Until that review passes, no tuning or math is written.

*End — TORMENT Brainvision SAG Redesign Proposal v0.9. Docs-only, non-authorizing. Opens no implementation
lane; no `§0` pointer added; no tags.*
