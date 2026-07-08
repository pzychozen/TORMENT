# TORMENT Brainvision Color Structure Spectral/Std Blocker Findings v1.9

## 1. Status / quarantine and non-claims

**DOCS-ONLY findings receipt. Non-authorizing, non-implementing.** It records the v1.9 spectral/std blocker
diagnostic result. It **authorizes no code and no tests**, invents no threshold, defines no replacement
acceptance criteria, changes no formula / §7 gate / §8 verdict, and deletes or weakens no control. Everything
stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains
**False**. It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture /
streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip /
local-clip move** and **no memory-system integration**. **No `§0` pointer; no tags.**

## 2. What was run

- v1.9 files:
  - `research/brainvision/run_color_structure_spectral_std_blocker_v1_9.py`
  - `tests/research/test_brainvision_color_structure_spectral_std_blocker_v1_9.py`
- Validation: v1.9 tests **10 passed**; v1.8 regression **13 passed**; full Brainvision research suite
  **173 passed**.
- The diagnostic is **reporting-only**; the frozen §8 verdict over the v1.9 bank stays **HOLD**.

## 3. Core result

```text
S/PSC survived tight spectral/std blocker control.
Outcome: A_with_residual.
```

- The four v1.8 matched-subset blockers (`spectral_centroid`, `by_std`, `rg_spread`, `nr_rg_spread`) are
  **weakened as direct explanations** for `S`/`PSC`.
- Coherent winding **still separates from cancellation** when the spectral/std blocker axes are tightly
  controlled — including the phase-relative family where `by_std` / `rg_spread` / `nr_rg_spread` are made
  analytically identical between winder and non-winder (delta exactly 0), yet `S`/`PSC` still separates.

## 4. What this is not

- This is **not** descriptor validity.
- This is **not** temporal-order proof.
- This is **not** vision.
- This is **not** a functioning memory-system vision layer.
- Verdict remains **HOLD**.
- `first_pass_structure_validity_claim_allowed = False`.
- `temporal_claim_allowed = False`.

## 5. Residual (recorded, not hidden)

```text
by_std remains as a cross-family pool residual.
```

Framing:

```text
The blocker is weakened per-axis, but the bank still carries a by_std pool-composition residual.
```

This residual is **not solved** and is **not hidden**: `by_std` retains a weaker cross-family correlation
with `S` across the pooled v1.9 bank, even though it is neutralized (delta 0) within the phase-relative
matched pair. Whether that residual is a pool-composition artifact or a true descriptor limitation is left
open — it is the next diagnostic question, not a claim.

## 6. Recommended next implementation target

**`v2.0 by_std residual diagnostic`.**

Possible files:

```text
research/brainvision/run_color_structure_by_std_residual_v2_0.py
tests/research/test_brainvision_color_structure_by_std_residual_v2_0.py
```

Purpose:

```text
Test whether the remaining by_std cross-family residual is a pool-composition artifact or a true descriptor limitation.
```

Not:

```text
make the gate pass
delete controls
change §7
claim vision
move to real clips
integrate with memory
```

This is recorded as the next **possible** slice; it is **not opened here**. Any such slice must report
under the unchanged frozen §7 gate, preserve all controls, invent no threshold, define no replacement
acceptance criteria, and keep the verdict at HOLD unless the existing frozen gate actually passes. Real
clips / local-clip manifest and memory-system integration stay disallowed.

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

## 7. Recommended next

- **Codex review** of this findings receipt.
- **If the operator explicitly opens the next slice**, it should be the `v2.0 by_std residual diagnostic`;
  otherwise HOLD.

*End — TORMENT Brainvision Color Structure Spectral/Std Blocker Findings v1.9. Docs-only, non-authorizing.
Opens no implementation lane; changes no frozen formula, gate, or verdict; deletes no control; invents no
threshold; no `§0` pointer added; no tags.*
