# TORMENT Brainvision ΨTRS Real-Video Findings v0.1

**Status:** DOCS-ONLY research findings note. **Non-authorizing, non-implementing. Opens no implementation
lane and no service integration.** Records the offline Brainvision ΨTRS arc (v0.4–v0.5.1). All work is in
`research/brainvision/` + `tests/research/`; nothing is wired to `torment_service/`, no camera/runtime/
sensor capture, no memory/prompt/action/render-body/autonomy contact. This note adds **no** `§0` pointer
and does not edit `PROJECT_ORIENTATION_MAP.md`.

## 1. Headline (narrow, defensible)

> State-dependent internal time adds structured signal against ablated / time-shuffled controls and can
> produce symmetry amplification in the offline Brainvision descriptor field.

This is the **only** claim the evidence supports. It is **not** a claim that ΨTRS is a superior classifier,
nor that Brainvision is a working vision system, nor that anything transfers to a live runtime.

## 2. Synthetic controls (v0.4–v0.4.2)

The offline falsifier first removed the trivial shortcuts (v0.1 coarse → v0.2 marginal-matched → v0.3
spectrum-matched), so `descriptor_only` and `plain_fft` cannot win by amplitude or power-spectrum alone.
On that controlled substrate:

- **v0.4 — BV-ΨTRS classification (spectrum-matched fixtures):** the state-dependent internal clock beat
  its own ablation and the time-shuffle control — `psi_trs = 0.750` vs `psi_trs_k0 = 0.325`, time-shuffle
  `= 0.200` (chance 0.20). (Honest caveat: `random_mapping` still led the table; classification alone did
  not establish superiority.)
- **v0.4.1 — BV-ΨTRS-SAG symmetry amplification:** a fixed clock (κ=0) kept mirror-perturbed paired
  trajectories coherent (G ≈ 1.000), while a state-dependent clock (κ>0) amplified above threshold
  (G rising with κ). This is the papers' own symmetry diagnostic, isolating the recursive-time mechanism
  from classification confounds.
- **v0.4.2 — golden-point calibration:** a **side-check only**. Old raw-kernel golden points
  (`stable_core / near_knee / edge_band / expected_fail`) were mapped cautiously to ΨTRS priors. Under the
  natural `k3_scale→κ` mapping the regime *ordering* lined up (stable coherent, edge amplifying,
  expected_fail a fail-control), but the alignment was fragile and mapping-dependent; the alternative
  `g→warp-sharpness` mapping collapsed it. **No clean constant transfer.** Treated as a closed calibration
  fixture, not a foundation.

## 3. Real prerecorded video (v0.5–v0.5.1)

v0.5 added a dependency-light real-video route (`.npz` frame stacks → low-level, label-free descriptor
field) and v0.5.1 made SAG multi-window (evaluated over every descriptor window, not just the first).

**First real prerecorded clip — `clip1`** (8 windows, descriptor_dim 9):

- **Classification is saturated and therefore secondary.** On true-order vs time-shuffled,
  `frame_diff`, `plain_fft`, `psi`, `psi_trs`, and `psi_trs_k0` all reached **1.000** — so classification
  does **not** prove ΨTRS superiority here (fixed-clock and recursive-time both max out). `descriptor_only`
  was 0.000 (order-invariant, as expected).
- **Multi-window SAG (the meaningful signal):**
  - `G(k=0)`: mean / median / min / max = **1.000** (fixed clock stayed coherent in every window).
  - `G(k>0)`: mean = **14.887**, median = **13.999**, min = **2.394**, max = **33.318**.
  - **windows amplifying: 8 / 8.**
- **Interpretation:** the recursive-time channel **survived real descriptor messiness on this first clip** —
  every window amplified under κ>0 while κ=0 stayed coherent. This is the strongest evidence in the arc.

## 4. Caveats

- **One clip is not validation.** A single real prerecorded clip is a promising first data point, not a
  result.
- **Classification is saturated** on this clip and does not discriminate ΨTRS from fixed-clock or simple
  baselines; do not cite it as ΨTRS superiority.
- **Random / simple baselines remain important.** `random_mapping` led on synthetic classification and
  must stay in every comparison; the recursive-time claim rests on SAG (mechanism), not classifier rank.
- **SAG is the strongest evidence so far, but it needs more varied real prerecorded clips** (different
  content, motion, cuts, lengths) before "survives" generalizes beyond `clip1`.
- **No runtime, camera, sensor, or service integration is authorized.** Everything here is offline research
  on prerecorded `.npz`; the boundary from `TORMENT_BRAINVISION_OFFLINE_FALSIFIER_BOUNDARY_FRAME_v0.md`
  holds.

## 5. Next recommendation

- Run **2–3 more real prerecorded local clips** (converted to `.npz` outside the harness, kept under the
  gitignored `research/brainvision/local_inputs/`).
- Keep evaluating **κ=0 vs κ>0 SAG across all windows** (per-window + summary + amplifying-window count).
- **Only if the survival pattern repeats** across those clips should Brainvision move toward a broader
  offline descriptor study. Until then this remains a promising-but-unvalidated offline research signal,
  not a method and not a product.

*End — TORMENT Brainvision ΨTRS Real-Video Findings v0.1. Docs-only, non-authorizing. Opens no
implementation lane; no §0 pointer added.*
