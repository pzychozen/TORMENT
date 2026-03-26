# TODO: DISP_SCALE Recalibration in memory_kernel.py

**Status**: Open — follow-up to hivemind validation (Entity7 proof run)
**Priority**: High — affects coherence across the entire system, not just hivemind
**Filed**: 2026-03-26

## Problem

`DISP_SCALE` in `memory_kernel.py` line 64 is set to `7.0e-4` (0.0007).

This is the Gaussian width parameter for the dispersion-to-coherence mapping:

```python
coh_phase = exp(-(disp / DISP_SCALE)^2)
```

Real phase dispersion (`disp`) between the three TriOcta oscillators runs 0.5–2.0
radians for typical embeddings. With `DISP_SCALE = 7e-4`, the exponent becomes:

    (1.0 / 0.0007)^2 ≈ 2,000,000
    exp(-2,000,000) ≈ 0.0

So `coh_phase` is effectively always 0.0, and:

    coh_raw = COH_FLOOR + (1.0 - COH_FLOOR) * 0.0 = 0.05

Then the EMA smoothing (`COH_SMOOTH = 0.90`) locks it at 0.05 permanently:

    0.90 * 0.05 + 0.10 * 0.05 = 0.05

**Coherence has likely never been above 0.05 for any real agent.**

## What this breaks

1. **Hivemind packet gate** (fabric.py): threshold was 0.15, coherence is always 0.05.
   Packets never emitted. *Temporarily worked around by lowering threshold to 0.01.*

2. **Symbol transitions** (symbols.py): checks `coherence_delta > 0.10` and
   `coherence_delta > 0.02`. With coherence pinned at 0.05, delta is always ~0.
   Coherence-rising symbols (`◉`) never trigger.

3. **Compression scoring** (compression.py): uses `coherence_field` from motifs, which
   is a different computation — but `debug["coherence"]` is stored in memory payloads
   and may influence downstream analysis.

## Temporary workaround in place

In `fabric.py`, the packet coherence gate threshold has been lowered:

```python
# NOTE: threshold temporarily lowered from 0.15 to 0.01 for hivemind
# pipeline validation.  DISP_SCALE in memory_kernel.py (7e-4) causes
# coherence to pin at COH_FLOOR (0.05) for all real embeddings.
# TODO: restore to 0.15 after DISP_SCALE is recalibrated.
_HM_COH_THRESHOLD = 0.01
```

## Proposed recalibration plan

### Step 1: Measure real dispersion range

Add temporary logging in `_dispersion_coherence()` to capture the actual `disp`
distribution across a set of real agent runs. This tells us the natural range.

Expected: `disp` in [0.3, 2.5] for typical embeddings.

### Step 2: Choose DISP_SCALE so coherence has meaningful variation

The Gaussian `exp(-(disp/scale)^2)` produces useful output when `disp/scale` is
in the range [0.5, 3.0]. So:

- If median disp ≈ 1.0, then `DISP_SCALE ≈ 1.0` gives `coh_phase ≈ 0.37`
- If median disp ≈ 0.5, then `DISP_SCALE ≈ 0.7` gives `coh_phase ≈ 0.49`

**Recommended starting point**: `DISP_SCALE = 1.5`

This would give:
- disp=0.5 → coh_phase≈0.90 → coh_raw≈0.90
- disp=1.0 → coh_phase≈0.64 → coh_raw≈0.66
- disp=1.5 → coh_phase≈0.37 → coh_raw≈0.40
- disp=2.0 → coh_phase≈0.17 → coh_raw≈0.21
- disp=2.5 → coh_phase≈0.06 → coh_raw≈0.11

### Step 3: Test downstream effects

After changing DISP_SCALE, verify:

- [ ] Corridor detection still triggers normally (uses `in_corridor` from tangent
      alignment, not directly from coherence — but check)
- [ ] Compression triggers still fire on corridor exit (EventDetector)
- [ ] Symbol transitions in symbols.py fire when coherence actually changes
- [ ] Packet coherence gate can be restored to 0.15 (coherence now varies above it)
- [ ] EMA smoothing still behaves reasonably (COH_SMOOTH=0.90 may need adjustment
      if coherence now moves faster)
- [ ] Run full test suite: expect 1039+ passed

### Step 4: Restore packet threshold

Once coherence is calibrated, restore in fabric.py:

```python
_HM_COH_THRESHOLD = 0.15  # restored after DISP_SCALE recalibration
```

## Files involved

- `torment_service/memory_kernel.py` — DISP_SCALE, COH_FLOOR, COH_SMOOTH, _dispersion_coherence()
- `torment_service/fabric.py` — packet coherence gate (_HM_COH_THRESHOLD)
- `torment_service/symbols.py` — coherence_delta thresholds for symbol transitions

## Temporary debug prints to remove

After this task is complete, also remove the `print()` debug statements in
`fabric.py` around the packet emission block (lines ~2430-2570, marked with
"TEMPORARY PACKET DEBUG").
