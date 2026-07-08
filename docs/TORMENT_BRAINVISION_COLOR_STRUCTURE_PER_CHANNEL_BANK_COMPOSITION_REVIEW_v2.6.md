# TORMENT Brainvision Color Structure Per-Channel Bank-Composition Review v2.6

## 1. Status / quarantine and non-claims

**DOCS-ONLY bank-composition review. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** It scrutinizes, in docs only, whether the surviving **per-channel-spectral** residual is
a true descriptor proxy problem or mostly a null / control-bank composition artifact. It **authorizes no code
and no tests**, invents no threshold, defines no replacement acceptance criteria, changes no formula / §7
anti-proxy logic / §8 verdict logic, deletes or weakens no control, and implements no fixture. Everything
discussed stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains **False**.
It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture / streaming, or
prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip / local-clip move**
and **no memory-system integration**. Brainvision Path B is **not proven vision** and is **not a functioning
vision layer for TORMENT memory**. **No `§0` pointer; no tags.**

Scope of this review is the **per-channel-spectral axis only**:

```text
rg_centroid    by_centroid    rg_spread    by_spread
nr_rg_centroid nr_by_centroid nr_rg_spread nr_by_spread
```

The directional axis (v2.4 reading B) was handled by the v2.5 review and is **out of scope here**.

## 2. Accepted v2.4 per-channel facts

Carried forward by identity from the accepted v2.4 audit (findings receipt v2.4). The verdict **remains HOLD**.

Pooled per-channel-spectral stats fail under the frozen §7 gate (`|rho| >= 0.30` fails):

```text
nr_by_centroid   rho ~ -0.704   fail
by_centroid      rho ~ -0.703   fail
rg_centroid      rho ~ -0.702   fail
nr_rg_centroid   rho ~ -0.702   fail
by_spread        rho ~ -0.638   fail
nr_by_spread     rho ~ -0.635   fail
rg_spread        rho ~ -0.597   fail
nr_rg_spread     rho ~ -0.584   fail
```

Windows/Codex note: the Windows broad band for the per-channel drivers is approximately `0.563–0.704` (the
values above are the sandbox reconstruction; both platforms exceed the 0.30 ceiling — the wall is robust).

Matched-pair diagnostics (centroid / spread held fixed between a winder and a cancellation partner):

```text
rg_by_centroid family:  nonwinder_pick = collinear_1   mean|Δblocker| = 0.0000   ΔS = +1.000  ΔPSC = +1.000  separates = True
rg_by_spread   family:  nonwinder_pick = collinear_2   mean|Δblocker| = 0.0000   ΔS = +0.999  ΔPSC = +1.000  separates = True
```

Null-relative decomposition — the pooled association **collapses among the primaries** and is reintroduced by
the null / control geometry:

```text
nr_rg_centroid   full ~ -0.702   primaries_only ~ -0.059   source = null_bank_geometry
nr_by_centroid   full ~ -0.703   primaries_only ~ -0.076   source = null_bank_geometry
nr_rg_spread     full ~ -0.597   primaries_only ~ +0.137   source = null_bank_geometry
nr_by_spread     full ~ -0.638   primaries_only ~ +0.002   source = null_bank_geometry
```

Within-class / cross-group / pooled — the pooled failure is carried by the **cross-group** structure, not by
any within-winder association (winders are pinned, `within_winder = +0.000`):

```text
stat          pooled    within_winder   within_nonwinder   cross_group
rg_centroid   -0.702    +0.000          +0.886             -0.912
by_centroid   -0.703    +0.000          +0.807             -0.912
rg_spread     -0.597    +0.000          +0.993             -0.928
by_spread     -0.638    +0.000          +0.732             -0.928
```

v2.4 classified the per-channel-spectral axis as **C_bank_composition_artifact**; **A_descriptor_limitation was
NOT supported** because the matched pairs separate `S` / `PSC` at fixed blocker. That classification is
**reporting-only and cannot change the verdict**, which stays **HOLD**.

## 3. The bank-composition question

The per-channel RG/BY centroid / spread stats fail the pooled §7 gate strongly (`|rho|` up to ≈ 0.70), yet the
**primaries-only** associations collapse toward zero (`-0.076` to `+0.137`), while the null / control geometry
reintroduces the failure across the full bank (cross-group `|rho|` ≈ 0.91–0.93). The winders occupy a tight
per-channel-spectral region (e.g. `rg_centroid ∈ [0.0312, 0.0313]`, `rg_spread ≈ 0`) with `S` / `PSC` pinned
high, and the cancellation partners at matched centroid / spread still separate.

The question this review frames is therefore:

```text
Is the per-channel-spectral residual a true descriptor proxy problem,
or is it mostly a null / control-bank composition artifact?
```

As with the directional axis, this review only **frames** the question in docs; it proposes **no** control
change and **no** §7 change. In particular, collapsing the pooled failure by removing or re-weighting the
nulls / controls is a **forbidden move** (§4).

## 4. Distinguish descriptor confound from bank-composition artifact

Docs-only definitions to keep the question honest:

- **Descriptor confound** — `S` / `PSC` structurally tracks RG/BY centroid / spread **even within the primary
  target families and matched-pair decompositions**. Signature: primaries-only per-channel `|rho|` high, and
  matched pairs fail to separate when centroid / spread is held fixed (`S` collapses with the blocker). This
  would make the per-channel stats a genuine proxy the descriptor is riding.
- **Bank-composition artifact** — the pooled RG/BY centroid / spread failures emerge **mainly from how the
  nulls / controls occupy per-channel-spectral space**, while the primaries-only and matched-pair evidence do
  **not** support direct descriptor dependence. Signature: primaries-only per-channel `|rho|` near zero,
  matched pairs still separate at fixed blocker, and the pooled association carried by cross-group structure
  (the nulls / controls sit at different centroid / spread values from the pinned winders).
- **Forbidden move** — deleting or null-weakening controls **just to collapse the pooled failure**. The
  trajectory-order nulls and the structureless / continuity controls are load-bearing; a clean pooled number
  obtained by dropping them would be gate-gaming, not evidence, and is not authorized.

The discriminator is: **does the per-channel association exist among the primaries and survive matched-pair
control, or only across the composed bank?** If only across the composed bank, the residual is
composition-driven rather than a descriptor confound.

## 5. Evidence for C_bank_composition_artifact

The v2.4 facts point toward the per-channel-spectral residual being a bank-composition artifact rather than a
descriptor confound, **on the current synthetic evidence**:

- **Pooled per-channel stats fail strongly** (`|rho|` ≈ 0.58–0.70): the wall is real and per-channel-led on the
  full bank.
- **Primaries-only per-channel associations collapse near zero** (`-0.076`, `-0.059`, `+0.002`, `+0.137`):
  among the actual winders and nonwinders, `S` does **not** track centroid / spread — the failure is not
  reproduced within the primary families.
- **Matched centroid / spread pairs still separate `S` / `PSC` at fixed blocker** (mean `|Δblocker|` = 0.0000,
  `ΔS` ≈ +1.000, `ΔPSC` ≈ +1.000): when centroid / spread is held identical, the winding signal **still**
  separates coherent winding from cancellation — so centroid / spread is not doing the separating work in this
  matched-pair evidence.
- **Failures are reintroduced by null / control geometry**: the pooled association is carried by cross-group
  structure (`|rho|` ≈ 0.91–0.93), i.e. the pinned winders and the nulls / controls occupy different
  per-channel-spectral regions, which drives the pooled Spearman above the ceiling.
- **Therefore** the per-channel residual appears **bank-composition driven** in the current synthetic evidence,
  consistent with v2.4 reading C — the pooled §7 failure reflects how the bank is composed across groups, not a
  direct descriptor dependence on centroid / spread.

## 6. Evidence against over-reading C

Countervailing cautions, recorded so C is not over-read into a control-removal or validity move:

- **The pooled `rho` is real and must not be ignored.** A strong pooled association is exactly what a genuine
  per-channel proxy would also produce; "composition-driven" is a hypothesis about *where* the association
  lives, not a dismissal of the number.
- **Bank-composition artifact does not mean the controls are bad or removable.** The nulls / controls are
  load-bearing by design; that they drive the pooled association is a statement about the surface, not a
  license to delete or re-weight them.
- **The collinear matched-pair picks may be narrow.** `collinear_1` / `collinear_2` are RG==BY collinear
  cancellers chosen to match centroid / spread exactly; a single narrow family should not be over-generalized
  to all per-channel geometry.
- **Null / control geometry may reveal a real stress surface, not just noise.** That the failure lives in the
  cross-group structure could indicate a genuine sensitivity of the descriptor to how per-channel-spectral
  space is populated, worth understanding rather than assuming benign.
- **No control deletion is authorized.** Nothing here licenses removing, thinning, or re-weighting any control
  to collapse the pooled failure.
- **No descriptor-validity claim is allowed.** This review classifies the *residual*, not the descriptor; it
  makes no statement that `PSC` / `AIC` / `S` is a valid structure detector.

## 7. Decision outcome

The per-channel-spectral axis should be treated as a **bank-composition artifact candidate** — **not** a
descriptor limitation, and **not** a gate pass. The pooled §7 failure on the per-channel stats is best
explained, on the current synthetic evidence, as composition across groups (pinned winders vs nulls / controls
occupying different centroid / spread regions) rather than a direct descriptor confound; but this remains a
*candidate* reading pending broader (still docs-gated) scrutiny, and it changes nothing frozen.

Recorded outcome flags (reporting-only; none of these move the verdict or any gate):

```text
per_channel_bank_composition_artifact_candidate = True
per_channel_proxy_failure_resolved              = False
control_deletion_allowed                        = False
descriptor_validity_claim_allowed               = False
verdict                                          = HOLD
first_pass_structure_validity_claim_allowed      = False
temporal_claim_allowed                           = False
```

`per_channel_proxy_failure_resolved = False` is deliberate: the residual is **not** resolved, only better
characterized. The frozen §7 gate still HOLDs on the per-channel stats, and no control removal, threshold, or
descriptor claim follows from this review.

## 8. Recommended next step

After v2.6, the recommended next step is a **docs-only synthesis frame** that combines the v2.5 (directional)
and v2.6 (per-channel) reviews and decides what the next technical slice should be — **without opening it yet**.
Possible next file:

```text
docs/TORMENT_BRAINVISION_COLOR_STRUCTURE_RESIDUAL_SYNTHESIS_AND_NEXT_DECISION_v2.7.md
```

Purpose:

```text
Synthesize:
- directional axis = validity-surface mismatch candidate, unresolved (v2.5)
- per-channel axis = bank-composition artifact candidate, unresolved (v2.6)
- A_descriptor_limitation not supported by current matched-pair evidence
- verdict remains HOLD
Then decide whether the next branch should be:
  A. broader matched-pair diagnostic,
  B. validity-surface doctrine review,
  C. null / control-bank redesign plan,
  or HOLD.
```

The v2.7 synthesis is recorded as the next **possible** step; it is **not opened here**, and any technical
slice it might recommend stays disallowed until separately opened after review. Real clips / local-clip manifest
and memory-system integration stay disallowed, and no §7/§8/threshold/control/descriptor change may be made
without a fresh freeze and adversarial review.

- **Codex review** of this per-channel bank-composition review and of the recommendation to open the docs-only
  v2.7 synthesis-and-next-decision frame next, keeping the per-channel axis a bank-composition-artifact
  **candidate** (not resolved, not a validity claim, no control deletion), the verdict at HOLD, and all
  disallowed moves disallowed.
- **If the operator explicitly opens the next docs-only slice, it should be that v2.7 synthesis frame;
  otherwise HOLD.**

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Color Structure Per-Channel Bank-Composition Review v2.6. Docs-only, non-authorizing.
Opens no implementation lane; changes no frozen formula, gate, or verdict; deletes or weakens no control;
invents no threshold; makes no descriptor-validity claim; no `§0` pointer added; no tags.*
