# DISP_SCALE Recalibration — Full Data Package

**For**: ChatGPT permanent fix analysis
**Date**: 2026-03-26

---

## 1. Exact Coherence Computation Code

### 1a. Tunables (memory_kernel.py, TriOctaMemoryKernel.__init__)

```python
self.COH_FLOOR = 0.05         # minimum coherence floor
self.DISP_SCALE = 7.0e-4      # Gaussian width (THE PROBLEM)
self.COH_SMOOTH = 0.90        # EMA smoothing factor (0 disables)
```

### 1b. Phase wrapping helper

```python
def _wrap_pi(a: float) -> float:
    return float((a + np.pi) % (2 * np.pi) - np.pi)
```

### 1c. Dispersion-to-coherence mapping (_dispersion_coherence)

```python
def _dispersion_coherence(self, Omega: np.ndarray) -> Tuple[float, float]:
    ph = np.angle(Omega)                              # phases of 3 oscillators
    d01 = _wrap_pi(float(ph[0] - ph[1]))              # wrapped phase diff 0-1
    d12 = _wrap_pi(float(ph[1] - ph[2]))              # wrapped phase diff 1-2
    d20 = _wrap_pi(float(ph[2] - ph[0]))              # wrapped phase diff 2-0
    disp = float(np.sqrt(np.mean(np.square([d01, d12, d20]))))  # RMS dispersion
    scale = float(self.DISP_SCALE)
    coh_phase = float(np.exp(-((disp / max(scale, 1e-12)) ** 2)))  # Gaussian
    return disp, coh_phase
```

### 1d. Coherence pipeline in process()

```python
# Step 1: raw coherence from dispersion
disp, coh_phase = self._dispersion_coherence(state.Omega)
coh_raw = float(self.COH_FLOOR + (1.0 - self.COH_FLOOR) * np.clip(coh_phase, 0.0, 0.9999))
coh = coh_raw

# Step 2: EMA smoothing
a = float(self.COH_SMOOTH)   # 0.90
if a > 0.0:
    if float(self.mon.coh_ema) <= 0.0:
        self.mon.coh_ema = float(coh)           # initialize on first call
    else:
        self.mon.coh_ema = a * self.mon.coh_ema + (1.0 - a) * coh  # 90/10 EMA
    coh = float(self.mon.coh_ema)

# Step 3: coh is used for everything downstream (signals, debug payload)
debug["coherence"] = float(coh)
```

### 1e. Embedding → Omega conversion (_omega_from_embedding)

```python
def _omega_from_embedding(self, emb: np.ndarray) -> np.ndarray:
    e = np.asarray(emb, dtype=float).reshape(-1)
    if e.size < 6:
        e = np.pad(e, (0, 6 - e.size))
    w = np.abs(e[:3]) + 1e-6          # first 3 dims → weights
    w = w / np.sum(w)
    phases = (e[3:6] * np.pi)          # dims 3-5 → phases (multiplied by π)
    Omega = np.sqrt(w) * (np.cos(phases) + 1j * np.sin(phases))
    return Omega.astype(np.complex128)
```

### 1f. Omega blending per step

```python
# In process():
Omega_obs = self._omega_from_embedding(emb)
# tiny jitter based on text length
jit = float(np.clip((len(summary) - 40) / 400.0, 0.0, 1.0))
jphi = 0.03 * jit
rot = np.cos(jphi) + 1j * np.sin(jphi)
Omega_obs = Omega_obs * rot
# blend: 60% old state, 40% new observation
state.Omega = (0.60 * state.Omega + 0.40 * Omega_obs)
```

---

## 2. Real Dispersion Distribution (Measured)

### CRITICAL FINDING: HashEmbedding produces near-zero first 6 dims

The `HashEmbedding` (used offline/tests) produces embeddings where `e[:6]` are
mostly zeros. Since `_omega_from_embedding` uses `e[:3]` as weights and `e[3:6]`
as phases, this means **all 3 oscillators start with identical phases → disp ≈ 0**.

```
HashEmbedding e[:6] examples:
  "Memory governance reliability"              → [0, 0, 0, 0, 0, 0]
  "apple banana cherry"                        → [0, 0, 0, 0, 0, 0]
  "provenance retention contamination..."      → [0, 0, 0, 0, 0, 0.5]
  "vesica piscis sacred geometry..."           → [0, 0, 0, 0, 0, 0.447]
```

### Measured dispersion with HashEmbedding (15 diverse texts, cumulative state)

```
Text                                                  disp    coh_phase  coh_raw  coh_ema
Memory governance reliability depends on provenance   0.0006   0.4774    0.5035   0.5035
The quick brown fox jumps over the lazy dog           0.0002   0.9456    0.9483   0.5480
Longitudinal evaluation should measure...             0.0001   0.9922    0.9926   0.5924
Build evaluation for memory governance...             0.0000   0.9987    0.9988   0.6331
A rigorous systems researcher focused on...           0.0002   0.9463    0.9489   0.6647
Critical analyst identifying failure modes...         0.0003   0.8580    0.8651   0.6847
Pragmatic system builder translating...               0.0001   0.9880    0.9886   0.7151
Compare governed memory versus unguided...            0.0000   0.9997    0.9997   0.7436
Test whether governed memory changes...               0.1267   0.0000    0.0500   0.6742
Implement baseline versus governed memory...          0.0702   0.0000    0.0500   0.6118
Hello world this is a simple test string              0.0234   0.0000    0.0500   0.5556
Phase coherence in tri-oscillator systems...          0.0205   0.0000    0.0500   0.5050
The geometric kernel maps embeddings onto...          0.0067   0.0000    0.0500   0.4595
Workspace isolation ensures agents cannot...          0.0030   0.0000    0.0500   0.4186
Convergence detection requires cosine sim...          0.0016   0.0065    0.0562   0.3823
```

### Summary statistics

```
Dispersion range:  [0.0000, 0.2300]     (NOT 0.5–2.0 as originally estimated!)
Dispersion mean:   0.0169
Dispersion median: 0.0006
Dispersion std:    0.0344
Distribution:      bimodal — most near 0, occasional spikes to 0.05–0.23
```

### Fresh-state dispersion (20 texts, independent kernels)

With fresh state per text, 18/20 texts produce disp=0.0000.
Only 2 texts with non-zero e[5] produce disp ≈ 0.21–0.23.

---

## 3. Packet Threshold Code (fabric.py)

```python
# NOTE: threshold temporarily lowered from 0.15 to 0.01 for hivemind
# pipeline validation.  DISP_SCALE in memory_kernel.py (7e-4) causes
# coherence to pin at COH_FLOOR (0.05) for all real embeddings.
# TODO: restore to 0.15 after DISP_SCALE is recalibrated.
_HM_COH_THRESHOLD = 0.01

_hm_coherence = float(debug.get("coherence", 0.0) or 0.0)

if _hm_emit_ok and _hm_coherence >= _HM_COH_THRESHOLD:
    # emit packet...
```

Outer gate (before coherence check):
```python
if self._hivemind_enable and stored and eid is not None:
    # governance checks (non_shareable, export_blocked, collective provenance)
    # then coherence gate above
```

---

## 4. Downstream Coherence Checks (symbols.py)

```python
# ✧ "insight" — requires coherence_delta > 0.10
if coherence_delta > 0.10:
    return SymbolState(state_symbol="✧", ...)

# ⊘ "release" — requires coherence_delta > 0.02 AND tension_delta < -0.08
if coherence_delta > 0.02 and tension < 0.20 and tension_delta < -0.08:
    return SymbolState(state_symbol="⊘", ...)

# ⋮ "continuity" — requires abs(coherence_delta) < 0.06
if repeated_same_motif and abs(coherence_delta) < 0.06:
    return SymbolState(state_symbol="⋮", ...)
```

With coherence pinned at 0.05, `coherence_delta ≈ 0` always, so:
- ✧ (insight) NEVER fires (needs delta > 0.10)
- ⊘ (release) NEVER fires (needs delta > 0.02)
- ⋮ (continuity) always available (delta < 0.06 is trivially true)

---

## 5. What-If Analysis: coh_raw for Different DISP_SCALE Values

Given the REAL dispersion range [0, 0.23]:

```
    disp |  SC=7e-4 |  SC=0.05 |  SC=0.10 |  SC=0.15 |  SC=0.20
-----------------------------------------------------------------
  0.0000 |   1.0000 |   1.0000 |   1.0000 |   1.0000 |   1.0000
  0.0010 |   0.1734 |   0.9996 |   0.9999 |   1.0000 |   1.0000
  0.0050 |   0.0500 |   0.9905 |   0.9976 |   0.9989 |   0.9994
  0.0100 |   0.0500 |   0.9627 |   0.9905 |   0.9958 |   0.9976
  0.0200 |   0.0500 |   0.8595 |   0.9627 |   0.9833 |   0.9905
  0.0500 |   0.0500 |   0.3995 |   0.7899 |   0.9001 |   0.9424
  0.1000 |   0.0500 |   0.0674 |   0.3995 |   0.6591 |   0.7899
  0.1300 |   0.0500 |   0.0511 |   0.2253 |   0.4982 |   0.6726
  0.1500 |   0.0500 |   0.0501 |   0.1501 |   0.3995 |   0.5913
  0.1800 |   0.0500 |   0.0500 |   0.0872 |   0.2751 |   0.4726
  0.2300 |   0.0500 |   0.0500 |   0.0548 |   0.1405 |   0.3031
```

---

## 6. Key Observations & Recommendations

### The two-layer problem

1. **DISP_SCALE is too small** — even 0.001 disp kills coherence at 7e-4
2. **HashEmbedding produces near-zero dispersion** — most disp ≈ 0.0000

These compound: even after fixing DISP_SCALE, HashEmbedding may still produce
coherence that's mostly ~1.0 (because disp is mostly 0).

### Embedder dependency

- **HashEmbedding**: `e[:6]` mostly zeros → disp mostly 0 → coherence mostly 1.0
- **SentenceTransformer** (`st` provider): produces 384-dim dense embeddings where
  `e[:6]` will have varied values → `e[3:6] * π` produces real phase differences
  → disp will be larger and more varied

**The recalibration MUST be validated with the SentenceTransformer embedder** (the
production embedder), not just HashEmbedding.

### Suggested DISP_SCALE ranges

For HashEmbedding (disp in [0, 0.23]):
- `DISP_SCALE = 0.10` gives good spread: 0.40–1.00

For SentenceTransformer (disp likely in [0.3, 2.0] based on varied e[3:6]):
- `DISP_SCALE = 1.5` (as originally proposed in TODO) would be reasonable
- Need measured data from ST embedder to confirm

### Approach: adaptive or embedder-aware DISP_SCALE?

Options:
1. **Fixed value**: Pick one DISP_SCALE that works for both embedders (hard)
2. **Embedder-aware**: Set DISP_SCALE based on which embedder is active
3. **Adaptive**: Measure disp distribution at runtime, auto-calibrate
4. **Normalize disp**: Divide by running mean/std before the Gaussian

---

## 7. Files Involved

- `torment_service/memory_kernel.py` — DISP_SCALE, COH_FLOOR, COH_SMOOTH, _dispersion_coherence(), _omega_from_embedding()
- `torment_service/fabric.py` — _HM_COH_THRESHOLD (currently 0.01, needs restore to 0.15)
- `torment_service/symbols.py` — coherence_delta thresholds (0.10, 0.02, 0.06)
- `torment_service/embeddings.py` — HashEmbedding, SentenceTransformer embedder
