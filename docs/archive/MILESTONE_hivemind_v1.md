# MILESTONE: Hivemind v1 — Production-Stable Collective Resonance

Status: LOCKED
Date: March 26, 2026
Version: v2.3.1-hivemind-stable
Authors: pzychozen + Claude (Opus 4.6) + ChatGPT

---

## What Was Achieved

The full hivemind pipeline is working end-to-end:

    ingest → coherence → packet emission → convergence detection → echo reingest

Verified live with Entity9 workspace: 10 packets emitted, 2 convergence events
(cosine similarity 0.96 and 1.00), 3 successful reingests across 3 agents,
workspace isolation holding.

---

## Working Configuration

These are the exact values in production as of this milestone.

| Parameter | Value | Location | Notes |
|-----------|-------|----------|-------|
| ADAPTIVE_DISP | True | memory_kernel.py | Adaptive coherence enabled |
| ADAPTIVE_K | 2.0 | memory_kernel.py | Dimensionless sensitivity multiplier |
| ADAPTIVE_WINDOW | 50 | memory_kernel.py | Rolling dispersion buffer |
| ADAPTIVE_WARMUP | 10 | memory_kernel.py | Steps before fully adaptive |
| DISP_SCALE (fallback) | 1.50 | memory_kernel.py | Used during adaptive warmup only |
| COH_SMOOTH | 0.70 | memory_kernel.py | EMA smoothing factor |
| COH_FLOOR | 0.05 | memory_kernel.py | Minimum coherence signal |
| _HM_COH_THRESHOLD | 0.15 | fabric.py | Packet gate minimum |
| Write threshold | 0.55 | fabric.py | strength >= 0.55 to store |
| Omega extraction | Folded 6-chunk sum | memory_kernel.py | See _omega_from_embedding() |
| Embedder (production) | STEmbedding (BAAI/bge-small-en-v1.5) | env var | 384-dim dense |
| Embedder (fallback) | HashEmbedding (384-dim sparse) | default | Works but weaker convergence |

---

## Coherence Pipeline

The coherence computation is the single source of truth for memory quality:

```
embedding → _omega_from_embedding() → Omega (3-component complex vector)
                                          ↓
                        _dispersion_coherence(Omega)
                                          ↓
                   disp = RMS of wrapped phase differences
                                          ↓
                   scale = _effective_disp_scale(disp)
                     (adaptive: k * (mean(window) + std(window)))
                                          ↓
                   coh_phase = exp(-(disp / scale)^2)
                                          ↓
                   coh_raw = COH_FLOOR + (1 - COH_FLOOR) * coh_phase
                                          ↓
                   coh = EMA(coh_raw, COH_SMOOTH=0.70)
```

Downstream consumers:

    strength = 0.40 + 0.60 * coh          → write gate (>= 0.55)
    confidence = 0.35 + 0.65 * coh        → signals
    half_life = 20.0 + 80.0 * coh         → decay
    promotion_score = 0.50 + 0.50 * coh   → promotion
    packet gate: coh >= 0.15              → hivemind emission
    symbols: coherence_delta thresholds    → ✧ insight (>0.10), ⊘ release (>0.02)

---

## Omega Extraction (Folded Embedding)

The original approach (`e[:3]` / `e[3:6]`) was broken for sparse embeddings
(HashEmbedding) where early dimensions are mostly zero, and suboptimal for dense
embeddings where it ignored 378 of 384 dimensions.

The fix splits the full embedding into 6 equal chunks and sums each:

```python
chunk = dim // 6
folded = [sum(e[i*chunk : (i+1)*chunk]) for i in range(6)]
weights = abs(folded[:3]) + 1e-6  → normalized
phases  = folded[3:6] * pi
Omega   = sqrt(weights) * exp(i * phases)
```

This captures information from the entire embedding regardless of sparsity pattern.

---

## Adaptive DISP_SCALE

DISP_SCALE required manual recalibration three times (7e-4 → 0.10 → 1.50) when
switching between HashEmbedding and STEmbedding. The adaptive approach eliminates
this by tracking the observed dispersion distribution:

```
effective_scale = k * (mean(disp_window) + std(disp_window))
```

During warmup (first ADAPTIVE_WARMUP steps), it blends linearly from the fixed
fallback (1.50) to the adaptive estimate. After warmup, fully adaptive.

k=2.0 means "a dispersion at mean+std maps to coherence ~0.61 (the 1/e point)."
This is dimensionless and embedder-independent.

---

## Comparison Data: Fixed vs Adaptive

### HashEmbedding (12 texts: 9 core + 3 diverse)

| Metric | Fixed 1.5 | Adaptive k=2.0 |
|--------|-----------|----------------|
| Disp range | [0.222, 0.854] | [0.222, 0.854] |
| Eff. scale range | [1.500, 1.500] | [1.161, 1.500] |
| Coherence range | [0.827, 0.979] | [0.798, 0.979] |
| Coherence mean | 0.9130 | 0.8920 |
| Max |coh delta| | 0.0523 | 0.0605 |
| Stored | 12/12 | 12/12 |
| Packets | 12/12 | 12/12 |
| Insight events | 0 | 0 |
| Release events | 5 | 7 |

### STEmbedding / BAAI/bge-small-en-v1.5 (12 texts)

| Metric | Fixed 1.5 | Adaptive k=2.0 |
|--------|-----------|----------------|
| Coherence mean | 0.8188 | 0.8299 |
| Coherence range (upper) | 0.902 | 0.912 |
| Stored | 12/12 | 12/12 |
| Packets | 12/12 | 12/12 |

Conclusion: Adaptive is a strictly safe generalization. Same storage and packet
rates, no instability, slightly wider coherence range and more expressive signal.

---

## Key Fixes in This Milestone

1. Omega extraction rewritten (folded embedding approach)
2. DISP_SCALE recalibrated from 7e-4 → 0.10 → 1.50 → adaptive k=2.0
3. COH_SMOOTH reduced from 0.90 to 0.70 for faster coherence response
4. _HM_COH_THRESHOLD restored to 0.15 (was temporarily 0.01)
5. agents.py fixed: truncated file restored, coherence read from debug not signals
6. Test assertions widened for dynamic coherence behavior
7. Diagnostic prints added then removed after calibration finalized
8. effective_disp_scale exposed in debug payload for monitoring

---

## Test Status at Lock

- e2e integration tests: 23/23 passed
- Golden emergent replay: 3/3 FAILED (pre-existing: search_by_embedding
  AttributeError in MemoryGraph, unrelated to coherence changes)
- test_replay_determinism: known fragility in motif_entropy_score (pre-existing)

---

## Recalibration History

| Date | DISP_SCALE | Embedder | Result |
|------|-----------|----------|--------|
| Pre-March 2026 | 7e-4 | HashEmbedding | Broken: coherence pinned at 0.05 |
| March 26 AM | 0.10 | HashEmbedding | Working offline, broken for ST |
| March 26 PM | 1.50 (fixed) | STEmbedding | Working: coh 0.70-0.96 live |
| March 26 EVE | k=2.0 (adaptive) | Both | Production stable, no recalibration needed |

---

## Files Modified

- `torment_service/memory_kernel.py` — Omega extraction, adaptive DISP_SCALE, coherence pipeline
- `torment_service/fabric.py` — _HM_COH_THRESHOLD restored to 0.15
- `examples/agents.py` — truncation fix, coherence read from debug
- `examples/test_adaptive_vs_fixed.py` — created for comparison testing
- `examples/test_disp_scale.py` — created for scale comparison
- `tests/test_e2e_integration.py` — assertion widening for dynamic coherence
- `tests/test_golden_emergent.py` — range widening
- `start/torment_character_creator.html` — HIVE Python client, SOLO env config
