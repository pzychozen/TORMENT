# TORMENT Brainvision Color Structure Directional / Per-Channel-Spectral Residual Decision Frame v2.2

## 1. Status / quarantine and non-claims

**DOCS-ONLY decision frame. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** It frames how to read the residual that survives the consolidated synthetic bank after
v2.1 and recommends the next docs-only step, before any descriptor redesign, anti-proxy / §7 change, §8
verdict change, fixture implementation, or real-clip move. It **authorizes no code and no tests**, invents no
threshold, defines no replacement acceptance criteria, changes no formula / §7 gate / §8 verdict, and deletes
or weakens no control. Everything discussed stays offline under `research/brainvision/` + `tests/research/`,
HELD per v0.6.

Brainvision remains **offline / quarantined synthetic descriptor research.** It is **not** proven vision,
**not** a functioning TORMENT vision layer, **not** temporal-order proof, and **not** ready for
memory-system integration. This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no**
temporal-order claim. `first_pass_structure_validity_claim_allowed` remains **False** and
`temporal_claim_allowed` remains **False**. It touches no `torment_service/`, runtime, camera / sensor /
live-capture / screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy
paths, and makes **no real-clip / local-clip move** and **no memory-system integration**. **No `§0` pointer;
no tags.**

Accepted repo truth carried into this frame:

```text
implementation edge: 2667bc4  research(brainvision): map integrated residual failures
findings edge:       b72d160  docs(research): record brainvision integrated residual findings
validation:          v2.1 tests 9 passed / v2.0 regression 10 passed / full Brainvision suite 192 passed
classification:      residual_failures_remain
verdict:             HOLD
```

## 2. What v2.1 resolved

v2.1 built the consolidated synthetic bank and checked the two previously-flagged residuals against the
unchanged gate. In the consolidated bank both are now **controlled / explained** (below ceiling, sign and
magnitude recorded, reporting-only):

```text
by_std:             +0.036   pass / controlled_or_explained
spectral_centroid:  -0.050   pass / controlled_or_explained
```

Descriptor separation is **still present** on the same bank — this is not a null-out of the signal:

```text
winder     S = 1.0
non-winder S <= 0.2167
```

So the old `by_std` and `spectral_centroid` blockers are no longer the wall. That much is settled for the
consolidated synthetic diagnostic context, and only for it.

## 3. What still fails

The frozen pooled §7 gate **still HOLDs**, now on a narrower axis: **directional / per-channel-spectral
geometry.** The remaining failing family:

```text
u_directional_delta_rms
angular_increment_mag
RG/BY centroid family
RG/BY spread family
null-relative variants
```

These stats still exceed the unchanged anti-proxy ceiling over the pooled bank. No threshold, gate, formula,
descriptor, fixture, or control is edited here to say so; the statement is a reading of the frozen gate's
output, nothing more.

## 4. Why this is now the main wall

The other candidate explanations for the pooled HOLD have each been weakened by earlier slices, which is
what isolates the current axis:

- **Movement amount alone** was weakened by v1.4 / v1.5: at exactly matched `u_directional_delta_rms` and
  `angular_increment_mag`, `S` / `PSC` still separated coherent winders from cancelling non-winders, so the
  separation is not a pure movement-amount proxy.
- **Spectral / std blockers** were weakened by v1.9: `S` / `PSC` survived spectral / std blocker control.
- **The `by_std` residual** was explained by v2.0 as a pool-composition artifact **in this synthetic
  diagnostic context.**
- **The integrated v2.1 pass** controlled / explained **both** `by_std` and `spectral_centroid` in the
  consolidated bank.

With movement-amount, spectral / std, and `by_std` each accounted for, the remaining unresolved problem is
the **covariance of directional / per-channel-spectral geometry with `S` / `PSC`** over the pooled bank.
That covariance — not the earlier blockers — is what keeps §7 at HOLD. This is a statement about **where the
residual now lives**, not a claim that the descriptor is valid, that it sees, or that order is encoded.

## 5. Three readings

The remaining residual admits three genuinely different readings. They lead to different work and must not be
collapsed into one. None is opened by this frame.

### 5.A — Legitimate descriptor limitation

**Possible because.** The residual survives the consolidated, deconfounded bank. `PSC` / `AIC` / `S` may be
scoring directional / per-channel geometry itself — not only coherent winding — so the descriptor may have a
real limitation that no amount of bank cleanup will remove.

**Risk.** Prematurely redesigning the descriptor could **destroy a real coherence signal** that the
matched-pair evidence (v1.4 / v1.5) says is present. A redesign motivated only by one surviving pooled
family risks over-fitting the descriptor to the gate.

**Disposition.** Recorded as a **possible interpretation, not opened.**

### 5.B — Validity-surface mismatch

**Possible because.** A winding / coherence descriptor may **naturally** correlate with directional geometry
— directional change is near-definitional for the target behaviour. If so, the frozen §7 anti-proxy surface
may be **over-penalizing** properties that are close to definitional for what the descriptor is meant to
capture, rather than catching a proxy defect.

**Risk.** Editing §7 to relax exactly the directional / per-channel stats a proxy would fail is externally
**indistinguishable from defining the confound away.** The gate must not be loosened without a fresh freeze
and adversarial review; a validity-surface reading is a reason to *scrutinize* the surface in docs, not to
edit it.

**Disposition.** Recorded as a **possible interpretation, not opened.**

### 5.C — Control-bank composition artifact

**Possible because.** Pooled covariance and null / control composition have **repeatedly** produced apparent
blockers in this arc (v1.6 / v1.8 / v2.0). The directional / per-channel residual may likewise be an artifact
of what the nulls and controls reintroduce into the pooled bank, rather than a property of the descriptor or
the gate.

**Risk.** More fixture work can become **endless tuning or gate-gaming.** Load-bearing controls (trajectory-
order nulls, structureless / continuity controls) must not be cherry-picked or deleted, and a clean pooled
result obtained by re-composing the bank must not be converted into a validity claim.

**Disposition.** Recorded as a **possible interpretation, not opened.**

## 6. Decision recommendation

The three readings are not yet separable from the evidence in hand, and no pass-chasing move is justified.
The recommended conclusion is to **hold and audit**, not to act on any single reading:

- **Do not redesign the descriptor yet** (guards against 5.A over-read).
- **Do not change §7 yet** (guards against 5.B defining the confound away).
- **Do not add random fixtures to make the gate pass** (guards against 5.C gate-gaming).
- **Do not move to real clips.**
- **Do not integrate with memory.**

Instead, recommend a **narrow, docs-only v2.3** whose only job is to audit the directional / per-channel axis
**without gate-gaming** — i.e. to gather the evidence that would tell 5.A from 5.B from 5.C, under the
unchanged gate, reporting-only. v2.3 is recorded as the next **possible** step; it is **not opened here.**

Possible v2.3 branches (a later frame picks one; each stays docs-only until separately opened):

```text
- directional / per-channel causality diagnostic
    predeclare which directional / per-channel-spectral stats drive the pooled Spearman above the ceiling,
    and whether they co-move with S / PSC by construction of the fixtures or independently of it —
    reporting-only, gate unchanged.
- validity-surface review plan
    docs-only scrutiny of whether §7 penalizes near-definitional directional properties of a winding /
    coherence descriptor; produces a written argument, proposes no §7 edit.
- descriptor limitation analysis
    docs-only analysis of whether PSC / AIC / S structurally encode directional / per-channel geometry
    beyond coherent winding; proposes no redesign.
```

Any move that would change a threshold, gate, formula, descriptor, fixture, or control requires a **separate
fresh freeze and adversarial review** after v2.3 — this frame authorizes none of it.

## 7. Recommended next / fresh-chat handoff pointer

Handoff content for the next chat, if the operator continues the arc:

```text
edge:                b72d160 (findings) over 2667bc4 (implementation)
state:               residual_failures_remain / verdict HOLD; suite 192 passed
resolved by v2.1:    by_std (+0.036) and spectral_centroid (-0.050) controlled_or_explained
remaining wall:      directional / per-channel-spectral geometry covariance with S / PSC
open fork:           5.A descriptor limitation | 5.B validity-surface mismatch | 5.C bank-composition artifact
recommended next:    docs-only v2.2 accepted -> open narrow docs-only v2.3 audit (one of the three branches)
disallowed:          §7 edit, §8 edit, threshold invention, control deletion, real clips, memory integration
preserved:           first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

- **Codex review** of this decision frame and of the recommendation to open a docs-only **v2.3 directional /
  per-channel-spectral audit** next, keeping readings 5.A, 5.B, and 5.C recorded-but-unopened and the
  descriptor / §7 / §8 / real-clip / memory moves disallowed.
- **If the operator explicitly opens the next docs-only slice, it should be that v2.3 audit; otherwise
  HOLD.**

*End — TORMENT Brainvision Color Structure Directional / Per-Channel-Spectral Residual Decision Frame v2.2.
Docs-only, non-authorizing. Opens no implementation lane; changes no frozen formula, gate, or verdict;
deletes no control; invents no threshold; no descriptor redesign; no `§0` pointer added; no tags.*
