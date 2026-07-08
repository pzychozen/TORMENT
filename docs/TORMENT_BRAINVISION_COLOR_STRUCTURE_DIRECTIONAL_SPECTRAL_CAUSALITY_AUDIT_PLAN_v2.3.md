# TORMENT Brainvision Color Structure Directional / Per-Channel-Spectral Causality Audit Plan v2.3

## 1. Status / quarantine and non-claims

**DOCS-ONLY audit plan. Non-authorizing, non-implementing. Opens no runtime, integration, or implementation
lane.** It plans *what a later audit would inspect* to distinguish why the directional / per-channel-spectral
residual survives the consolidated bank, under the **unchanged** frozen §7 gate. It **authorizes no code and
no tests**, invents no threshold, proposes no replacement acceptance criteria, changes no formula / §7 gate /
§8 verdict, deletes no control, and implements no fixture. Everything discussed stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains
**False**. It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture /
streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip /
local-clip move** and **no memory-system integration**. **No `§0` pointer; no tags.**

**Memory-system pointer (explicit):**

```text
Brainvision Path B is not proven vision and is not a functioning vision layer for TORMENT memory.
It remains offline/quarantined descriptor research and has no memory/context/runtime authority.
```

## 2. Accepted premise from v2.2

v2.2 (edge `ed47a58`, `docs(research): frame brainvision directional spectral residual`) localized the
surviving wall and left the verdict at HOLD. The premise this plan inherits, unchanged:

- **Movement amount alone** was weakened by v1.4 / v1.5: at exactly matched `u_directional_delta_rms` and
  `angular_increment_mag`, `S` / `PSC` still separated coherent winders from cancelling non-winders.
- **Spectral / std blockers** were weakened by v1.9: `S` / `PSC` survived spectral / std blocker control.
- **The `by_std` residual** was explained by v2.0 as a pool-composition artifact in this synthetic
  diagnostic context.
- **Integrated v2.1** controlled / explained **both** `by_std` and `spectral_centroid` in the consolidated
  bank (values below), with descriptor separation preserved.
- **v2.2** localized the remaining wall to **directional / per-channel-spectral geometry covariance with
  `S` / `PSC`**, and recorded three unopened readings (descriptor limitation / validity-surface mismatch /
  bank-composition artifact).
- **The verdict remains HOLD.**

Accepted current truth carried into this plan:

```text
accepted edge:      ed47a58  (v2.2 decision frame accepted docs-only over b72d160)
classification:     residual_failures_remain
verdict:            HOLD
by_std:             +0.036   pass / controlled_or_explained
spectral_centroid:  -0.050   pass / controlled_or_explained
winder     S = 1.0
non-winder S <= 0.2167
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed = False
```

Remaining failing family (the audit target):

```text
u_directional_delta_rms
angular_increment_mag
RG/BY centroid family
RG/BY spread family
null-relative variants
```

## 3. Audit objective

v2.3 **does not try to pass the gate.** It predeclares how a later reporting-only implementation could
distinguish which of the three v2.2 readings the surviving residual actually supports:

```text
A. legitimate descriptor limitation
B. validity-surface mismatch
C. control-bank composition artifact
```

The objective is *attribution under the unchanged frozen §7 gate* — to gather the evidence that separates
A / B / C, not to re-grade the verdict. No output of the later audit can move the verdict; a residual
classified "artifact" or "mismatch" still leaves the frozen gate at HOLD.

## 4. Proposed audit questions

Predeclared questions the later diagnostic would answer, all read off the existing pooled result and
predeclared decompositions under the unchanged gate:

1. **Which directional / per-channel stats drive the pooled Spearman failures?** Rank
   `u_directional_delta_rms`, `angular_increment_mag`, the RG/BY centroid family, the RG/BY spread family,
   and the null-relative (`nr_`) variants by their contribution to the pooled association that exceeds the
   ceiling.
2. **Do those stats co-move with `S` / `PSC` by construction, or only because of bank composition?** Separate
   covariance that is intrinsic to the descriptor from covariance introduced by what the bank contains.
3. **Can matched-pair families vary `S` / `PSC` while holding the directional / per-channel stats fixed?**
   If `S` / `PSC` moves at fixed blocker value, the blocker is not the whole story.
4. **Can matched-pair families vary the directional / per-channel stats while holding the `S` / `PSC` target
   class fixed?** If the blocker moves at fixed target class, the association is at least partly separable.
5. **Are the RG/BY centroid and spread failures separable from the winding / cancellation distinction?**
   Determine whether per-channel-spectral geometry fails independently of coherent-vs-cancelling motion.
6. **Are the null-relative variants revealing a true confound or a null-bank geometry artifact?** Attribute
   `nr_` failures to a genuine descriptor confound versus the geometry of the null bank itself.

## 5. Predeclared later diagnostic shape (docs-only; no code yet)

A *possible* later v2.4 implementation is described here **for predeclaration only** — nothing is built or
authorized by this note. If it is ever opened (separately, after review + operator approval), it would be
**reporting-only** and would produce:

- **Exact-matched pairs for `u_directional_delta_rms` and `angular_increment_mag`** — vary `S` / `PSC` target
  class at matched directional magnitude.
- **RG/BY centroid-matched pairs** — hold RG/BY centroid fixed across target classes.
- **RG/BY spread-matched pairs** — hold RG/BY spread fixed across target classes.
- **Null-relative decomposition** — attribute `nr_` failures to descriptor confound vs null-bank geometry.
- **Within-family and cross-family Spearman tables** — the existing pooled Spearman decomposed within each
  stat family and across families, reported under the frozen gate.
- **Pairwise deltas for `S` / `PSC` vs each blocker** — per-pair movement of the target signal against each
  directional / per-channel stat.

With the following held invariant:

```text
no pass/fail threshold changes
no descriptor changes
no control deletion
report under the unchanged frozen §7 gate; verdict cannot move
all outputs offline under research/brainvision/ + tests/research/
```

## 6. Interpretation rules (predeclared)

What outcome would support each reading — declared **before** any implementation so the result cannot be
fitted to a preferred conclusion:

- **A — legitimate descriptor limitation** if `S` / `PSC` remains **tightly correlated** with the
  directional / per-channel stats **even under exact matching and within-family decomposition** — i.e. the
  association does not separate when the blocker is held fixed.
- **B — validity-surface mismatch** if the failing stats are **unavoidable or near-definitional** for
  coherent winding (they move with the target by construction) **while cancellation controls still separate
  cleanly** — i.e. the gate penalizes a property that is close to the definition of the target.
- **C — control-bank composition artifact** if the **pooled failures collapse under the predeclared balanced
  decomposition** while the **within-family / matched-pair evidence stays clean** — i.e. the failure lives in
  what the pooled bank contains, not in the descriptor or the gate.
- **Unresolved** if the evidence stays **mixed** across these views — recorded as unresolved / needs
  adversarial review, not forced into A, B, or C.

This classification is **reporting-only** and **cannot change the verdict.** It is a hypothesis to review,
not a re-grade.

## 7. Guardrails against gate-gaming

The audit (and any later implementation of it) explicitly must not:

- **chase random fixtures** to move the pooled number;
- **delete any hard control** (trajectory-order nulls, structureless / continuity controls are load-bearing);
- **edit §7 or §8**;
- **invent any new threshold** or replacement acceptance criteria;
- **convert a clean diagnostic into a validity claim** — a clean decomposition is evidence about A/B/C, not
  proof of descriptor validity, vision, or temporal order;
- **move to real clips or memory integration after a clean result** — a clean audit does not unlock those;
- proceed without separate opening: **any technical implementation must be separately opened and reviewed**,
  with a fresh freeze, before code is written.

## 8. Recommendation

If this plan is accepted, the next technical slice **may** be a narrow **v2.4 reporting-only diagnostic**
that implements the predeclared audit of §4–§6 under the unchanged frozen §7 gate. It would be framed as:

```text
decompose the directional / per-channel-spectral pooled HOLD causes under unchanged §7
```

and **not** as:

```text
make the pooled gate pass
```

The v2.4 slice is recorded as the next **possible** step; it is **not opened here**, and it must not begin
until it is separately opened after review and explicit operator approval. Readings A, B, and C remain
recorded-but-unopened; the real-clip / local-clip move and any memory-system integration stay disallowed.

- **Codex review first** — of this audit plan and of whether it stays diagnostic (attribution under the
  unchanged gate) rather than becoming a route to loosening the gate or a validity claim.
- **If accepted**, the next *possible* slice is the narrow v2.4 reporting-only diagnostic above; **otherwise
  HOLD.**

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Color Structure Directional / Per-Channel-Spectral Causality Audit Plan v2.3.
Docs-only, non-authorizing. Opens no implementation lane; changes no frozen formula, gate, or verdict;
deletes no control; invents no threshold; implements no fixture; no descriptor redesign; no `§0` pointer
added; no tags.*
