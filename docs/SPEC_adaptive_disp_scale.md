# SPEC: Adaptive DISP_SCALE (Self-Calibrating Coherence Sensitivity)

**Author**: Claude (for ChatGPT review)
**Date**: 2026-03-26
**Status**: Implemented — merged into memory_kernel.py (March 26, 2026). See MILESTONE_hivemind_v1.md.

---

## 1. Problem Statement

`DISP_SCALE` controls how phase dispersion maps to coherence via a Gaussian:

```
coh_phase = exp(-(disp / DISP_SCALE)^2)
```

The optimal value depends entirely on the embedding distribution:

| Embedder        | Typical disp range | Optimal DISP_SCALE |
|-----------------|--------------------|--------------------|
| HashEmbedding   | 0.00 – 0.23        | ~0.10              |
| ST (bge-small)  | 0.23 – 0.93        | ~1.50              |
| Future model X  | ???                 | ???                |

Every time the embedder changes, `DISP_SCALE` must be manually recalibrated.
We just went through three rounds of this (7e-4 → 0.10 → 1.50).

**Goal**: Make the kernel self-calibrating so `DISP_SCALE` automatically adapts
to whatever embedding distribution it encounters.

---

## 2. Current Architecture

### 2a. Where dispersion is computed

**File**: `torment_service/memory_kernel.py`, class `TriOctaMemoryKernel`

```python
# Line 136-144
def _dispersion_coherence(self, Omega):
    ph = np.angle(Omega)
    d01 = _wrap_pi(ph[0] - ph[1])
    d12 = _wrap_pi(ph[1] - ph[2])
    d20 = _wrap_pi(ph[2] - ph[0])
    disp = sqrt(mean([d01^2, d12^2, d20^2]))   # RMS of wrapped phase diffs
    coh_phase = exp(-(disp / DISP_SCALE)^2)     # Gaussian mapping
    return disp, coh_phase
```

### 2b. Where coherence is assembled

**File**: `memory_kernel.py`, `process()` method (lines 183-194)

```python
disp, coh_phase = self._dispersion_coherence(state.Omega)
coh_raw = COH_FLOOR + (1 - COH_FLOOR) * clip(coh_phase, 0, 0.9999)
coh = coh_raw

# EMA smoothing (COH_SMOOTH = 0.70)
if COH_SMOOTH > 0:
    coh_ema = COH_SMOOTH * coh_ema_prev + (1 - COH_SMOOTH) * coh
    coh = coh_ema
```

### 2c. Current tunables (line 61-68)

```python
COH_FLOOR  = 0.05    # minimum coherence
DISP_SCALE = 1.50    # << THIS IS WHAT WE'RE REPLACING
COH_SMOOTH = 0.70    # EMA factor
```

### 2d. State holder

`CorridorMonitor` dataclass (line 36-43) holds `coh_ema`. This is per-kernel
instance (one per agent). It already persists across steps within a session.

---

## 3. All Downstream Consumers of Coherence

Coherence flows through the system in several places. The adaptive mechanism
must produce values in the same range (0.0 – 1.0) to avoid breaking any of them.

### 3a. Kernel signals (memory_kernel.py, lines 323-326)

```python
strength        = clip(0.40 + 0.60 * coh, 0, 1)   # write-gate input
confidence      = clip(0.35 + 0.65 * coh, 0, 1)
half_life       = 20.0 + 80.0 * coh                # memory decay rate
promotion_score = clip(0.50 + 0.50 * coh, 0, 1)
```

These are linear in `coh`. If adaptive DISP_SCALE produces the same [0.05, 1.0]
range, these work unchanged.

### 3b. Write gate (fabric.py, lines 2182-2203)

```python
write_threshold = 0.55 (default)
allow_write = (strength >= write_threshold)
# plus probabilistic band [wt-0.08, wt]
```

With `strength = 0.40 + 0.60 * coh`, the gate opens when `coh >= 0.25`.
Currently ST produces coh ~0.70–0.92, so everything passes easily.
If adaptive DISP_SCALE produces more variation, some low-coherence ingests
will correctly fail the write gate — this is DESIRED behavior.

### 3c. Packet emission (fabric.py, lines 2456-2464)

```python
_HM_COH_THRESHOLD = 0.15
if coherence >= _HM_COH_THRESHOLD:
    emit_packet()
```

Coherence must sometimes exceed 0.15 for hivemind to work.

### 3d. Symbol transitions (symbols.py, lines 111-141)

```python
if coherence_delta > 0.10:   # insight (✧)
if coherence_delta > 0.02:   # release (⊘)
if abs(coherence_delta) < 0.06:  # continuity (⋮)
```

These depend on coherence DELTA, not absolute value. Adaptive DISP_SCALE should
produce more varied coherence → larger deltas → symbols finally fire properly.

### 3e. SRG engine (srg_engine.py, lines 176-232)

```python
stability = 0.6 * clip(coherence, 0, 1) + 0.4 * clip(duration, 0, 1)
# Used for band assignment (lower band = more stable memory)
amplitude = 0.3 + 0.4 * clip(coherence, 0, 1)  # seed band
amplitude = 0.1 + 0.2 * clip(coherence, 0, 1)  # non-seed band
```

Linear in coherence, clipped to [0,1]. Works with any coherence in that range.

### 3f. SQLite storage (sqlite_index.py, line 235)

```python
float(payload.get("coherence", 0.0))  # stored as-is, no gating
```

Pure storage, no behavioral dependency.

### 3g. Seed motion (memory_kernel.py, line 309)

```python
speed = 0.05 + 0.25 * coh
```

Linear, works with any coh in [0, 1].

**CONCLUSION**: All consumers expect coherence in [0.0, 1.0] and use it linearly.
As long as adaptive DISP_SCALE produces values in that range with meaningful
variation, everything works without modification.

---

## 4. Proposed Design: Adaptive DISP_SCALE

### 4a. Core idea

Instead of a fixed `DISP_SCALE`, track a rolling window of recent dispersion
values and set the scale relative to the observed distribution:

```
DISP_SCALE_effective = k * (mean(disp_window) + std(disp_window))
```

Where:
- `disp_window` = circular buffer of last N dispersion values
- `k` = sensitivity multiplier (the ONE tunable that replaces DISP_SCALE)
- `k = 1.0` means: dispersion at 1 standard deviation above mean → coh_phase ≈ 0.37
- `k > 1.0` means: more permissive (higher coherence for same dispersion)
- `k < 1.0` means: more selective (lower coherence, more packets blocked)

### 4b. Why mean + std?

Using just the mean would center the Gaussian at the typical dispersion, giving
coh_phase ≈ 0.37 for an average ingest. That's too aggressive — most memories
should pass the 0.15 threshold.

`mean + std` sets the Gaussian shoulder at the upper end of the typical range.
This means:
- Low dispersion → high coherence (~0.6 – 0.95) → stored, packet emitted
- Typical dispersion → moderate coherence (~0.3 – 0.6) → stored, packet emitted
- High dispersion (unusual) → low coherence (~0.05 – 0.2) → may fail gates

This matches the DESIRED behavior: the kernel should be generous with normal
observations and skeptical of outliers.

### 4c. Warmup handling

During the first N ingests, we don't have enough data to compute meaningful
statistics. Options:

**Option A: Use a fixed fallback during warmup**
```python
if len(disp_window) < WARMUP_N:
    effective_scale = FALLBACK_SCALE  # e.g., 1.5
else:
    effective_scale = k * (mean(disp_window) + std(disp_window))
```
Pro: Simple, predictable. Con: Discontinuity when warmup ends.

**Option B: Blend from fallback to adaptive**
```python
alpha = min(1.0, len(disp_window) / WARMUP_N)
adaptive_scale = k * (mean(disp_window) + std(disp_window))
effective_scale = (1 - alpha) * FALLBACK_SCALE + alpha * adaptive_scale
```
Pro: Smooth transition. Con: Slightly more complex.

**Option C: Use expanding window from step 1**
```python
# No fallback — just compute from whatever data we have
effective_scale = k * (mean(disp_window) + std(disp_window) + epsilon)
# epsilon prevents division by zero when window is empty
```
Pro: No discontinuity, simplest code. Con: Noisy early estimates.

**Recommendation**: Option B with `WARMUP_N = 10`. The current DISP_SCALE=1.5
serves as the fallback, providing continuity.

### 4d. Window size

**Recommendation**: `WINDOW_SIZE = 50` (per agent, since each agent has its own
kernel instance).

At 50, the statistics are stable enough to not jitter on individual ingests,
but responsive enough to adapt if the embedding distribution shifts (e.g.,
agent starts discussing a very different topic domain).

### 4e. The sensitivity multiplier `k`

This is the ONE number that replaces `DISP_SCALE` as a tunable. Unlike
`DISP_SCALE`, `k` is dimensionless and embedder-independent.

Interpretation of `k`:
```
k = 0.5  → very selective:  mean disp → coh ≈ 0.05 (floor)
k = 1.0  → moderate:        mean disp → coh ≈ 0.37
k = 1.5  → permissive:      mean disp → coh ≈ 0.64
k = 2.0  → very permissive: mean disp → coh ≈ 0.78
k = 3.0  → almost flat:     mean disp → coh ≈ 0.90
```

**Recommended default**: `k = 2.0`

Rationale: With the current Entity9 ST data (disp ~0.3–0.9), `k = 2.0` would
produce coherence similar to the current DISP_SCALE=1.5 behavior (~0.7–0.9),
maintaining the working pipeline while being embedder-adaptive.

### 4f. Slider candidate

If `k` gets exposed as a UI slider:

```
Label:          "Coherence Sensitivity"
Range:          0.5 – 3.0
Default:        2.0
Low end label:  "selective"     (fewer packets, more filtering)
High end label: "permissive"    (more packets, less filtering)
```

This would go in the "04 — Collective Policy Tuning" panel alongside the
existing 6 sliders, as slider #7.

---

## 5. Implementation Plan

### 5a. Add dispersion buffer to CorridorMonitor

**File**: `memory_kernel.py`, line 36

```python
@dataclass
class CorridorMonitor:
    prev_xy: Optional[np.ndarray] = None
    prev_uxy: Optional[np.ndarray] = None
    tear_score_ema: float = 0.0
    align_ema: float = 0.0
    prox_ema: float = 0.0
    surv_ema: float = 0.0
    coh_ema: float = 0.0
    # NEW: adaptive DISP_SCALE state
    disp_buffer: List[float] = field(default_factory=list)  # rolling window
    disp_buffer_max: int = 50                               # window size
```

### 5b. Replace DISP_SCALE tunable with adaptive parameters

**File**: `memory_kernel.py`, line 61-68

```python
# REMOVE:
# self.DISP_SCALE = 1.50

# ADD:
self.DISP_SENSITIVITY = 2.0        # k multiplier (dimensionless)
self.DISP_WINDOW = 50              # rolling window size
self.DISP_WARMUP = 10              # steps before adaptive kicks in
self.DISP_FALLBACK = 1.50          # fixed scale during warmup
```

### 5c. New method: compute effective scale

**File**: `memory_kernel.py`, new method after `_dispersion_coherence`

```python
def _effective_disp_scale(self, disp: float) -> float:
    """Compute adaptive DISP_SCALE from dispersion history."""
    buf = self.mon.disp_buffer

    # Append current observation
    buf.append(disp)
    if len(buf) > self.DISP_WINDOW:
        buf.pop(0)  # or use collections.deque for O(1)

    n = len(buf)
    if n < 2:
        return self.DISP_FALLBACK

    # Blend from fallback to adaptive
    mu = float(np.mean(buf))
    sigma = float(np.std(buf))
    adaptive = self.DISP_SENSITIVITY * (mu + sigma)

    alpha = min(1.0, n / self.DISP_WARMUP)
    effective = (1.0 - alpha) * self.DISP_FALLBACK + alpha * adaptive

    return max(effective, 1e-6)  # never zero
```

### 5d. Modify _dispersion_coherence to use adaptive scale

**File**: `memory_kernel.py`, line 136-144

```python
def _dispersion_coherence(self, Omega):
    ph = np.angle(Omega)
    d01 = _wrap_pi(float(ph[0] - ph[1]))
    d12 = _wrap_pi(float(ph[1] - ph[2]))
    d20 = _wrap_pi(float(ph[2] - ph[0]))
    disp = float(np.sqrt(np.mean(np.square([d01, d12, d20]))))

    # CHANGED: use adaptive scale instead of fixed
    scale = self._effective_disp_scale(disp)
    coh_phase = float(np.exp(-((disp / max(scale, 1e-12)) ** 2)))
    return disp, coh_phase
```

### 5e. Update debug payload

**File**: `memory_kernel.py`, debug dict (~line 345)

Add to debug output so we can monitor the adaptation:

```python
debug["disp_scale_effective"] = float(scale)        # what scale was used
debug["disp_window_n"] = len(self.mon.disp_buffer)  # how many samples
debug["disp_window_mean"] = float(np.mean(self.mon.disp_buffer)) if self.mon.disp_buffer else 0.0
```

---

## 6. Mathematical Analysis

### 6a. Behavior at steady state

After warmup, with ST embedder (observed disp ~0.3–0.9):

```
mean(disp) ≈ 0.55
std(disp)  ≈ 0.20

effective_scale = k * (0.55 + 0.20) = k * 0.75

For k = 2.0: scale = 1.50  (matches current working value!)
For k = 1.5: scale = 1.125
For k = 1.0: scale = 0.75
```

So `k = 2.0` recovers the current behavior by construction.

### 6b. Behavior with HashEmbedding

With HashEmbedding (observed disp ~0.0–0.23):

```
mean(disp) ≈ 0.02
std(disp)  ≈ 0.06

effective_scale = k * (0.02 + 0.06) = k * 0.08

For k = 2.0: scale = 0.16  (close to the optimal 0.10 we found!)
```

The adaptive system automatically selects an appropriate scale for both
embedders without any manual intervention.

### 6c. Coherence distribution at steady state (k = 2.0)

For a given ingest with dispersion `d` and steady-state scale `s`:

```
coh_phase = exp(-(d/s)^2)
coh_raw   = 0.05 + 0.95 * coh_phase
```

With ST embedder (s ≈ 1.50):
```
d = 0.30 → coh_phase = 0.96 → coh_raw = 0.96
d = 0.55 → coh_phase = 0.87 → coh_raw = 0.88  (mean disp)
d = 0.75 → coh_phase = 0.75 → coh_raw = 0.76  (mean + std)
d = 0.90 → coh_phase = 0.64 → coh_raw = 0.66
```

This gives a healthy spread for symbols (deltas up to ~0.30) and
selective packet gating.

### 6d. Edge cases

**Empty agent (first ingest)**: Falls back to `DISP_FALLBACK = 1.50`.
Coherence is reasonable from step 1.

**Agent with very uniform inputs**: All disp values similar → std ≈ 0
→ scale ≈ k * mean → coherence clusters near 0.37 (at 1σ). Symbols
would get small deltas. This is CORRECT — uniform inputs should produce
stable, unremarkable coherence.

**Agent with wildly varied inputs**: Large std → larger scale → more
permissive. This is also CORRECT — the system recognizes high variance
as normal for this agent and doesn't penalize it.

**Sudden topic shift**: Large disp spike → initially low coherence (before
window adapts) → window mean/std shift within ~10 steps. The warmup blend
prevents violent jumps.

---

## 7. What NOT to Change

- `COH_FLOOR` (0.05): still needed as minimum signal
- `COH_SMOOTH` (0.70): EMA smoothing is orthogonal to the scale
- `_HM_COH_THRESHOLD` (0.15): policy gate stays fixed
- Symbol delta thresholds (0.10, 0.02, 0.06): these work once coherence varies
- All 6 existing collective policy sliders: completely separate system

---

## 8. Testing Strategy

1. **Unit test**: Feed known dispersion sequences, verify effective_scale
   converges to expected values for both Hash and ST distributions.

2. **Regression**: Run existing test_compression.py, test_e2e_integration.py,
   test_golden_emergent.py with adaptive enabled. May need range adjustments
   since coherence distribution changes.

3. **Offline comparison**: Extend `test_disp_scale.py` to include an
   "adaptive" column alongside the fixed scales.

4. **Live validation**: Run Entity10 workspace with adaptive enabled,
   compare coherence distribution to Entity9 (fixed DISP_SCALE=1.5).

---

## 9. Questions for ChatGPT

1. **Is `mean + std` the right statistic, or would `median + MAD` be more
   robust to outliers?** Median is more resistant to occasional extreme
   dispersion spikes.

2. **Should the buffer be per-agent (current proposal) or per-workspace?**
   Per-agent means each agent calibrates independently. Per-workspace would
   share calibration across agents (faster warmup, less independence).

3. **Should `k` be fixed or should we expose it as a slider?** The whole
   point of adaptive is to remove manual tuning. But a sensitivity slider
   could still be useful for users who want more/less selective hivemind.

4. **Is there a risk of feedback loops?** Coherence affects strength →
   affects which ingests are stored → affects which dispersion values
   enter the buffer → affects the scale. Could this create oscillation?
   I think the EMA smoothing and large window (50) prevent this, but
   worth analyzing.

5. **Should we clamp the adaptive scale to a sane range?** E.g.,
   `effective_scale = clip(adaptive, 0.05, 5.0)` to prevent pathological
   behavior if the buffer fills with zeros or extreme values.
