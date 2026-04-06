# Geometric Stance Modulation — Design Document

TORMENT v2.2

---

## What This Is

Geometric modulation lets the kernel's dynamical state influence how a character decides to participate in a conversation. Instead of fixed decision thresholds, the thresholds are nudged by signals derived from the kernel's current phase coherence, stability, and social context.

This is a bounded, optional, non-destructive modulation. It shifts thresholds by at most +/- 15%. It never overrides the deterministic rule scaffold. It activates only when geometric context is explicitly provided.

---

## GeometricStanceContext

Five normalized signals (all 0 to 1) harvested from the kernel's current state:

| Signal | Derived from | What it means |
|--------|-------------|---------------|
| coherence | kernel phase coherence (coh) | how aligned the oscillator triad is — high coherence = confident, stable processing |
| stability | 1 - tearing_risk | how stable the current corridor is — low stability = fragile, at risk of losing coherence |
| identity_lock | coherence x stability (clamped) | how firmly identity is anchored — composite of both signals |
| ambiguity_tolerance | 1 - dispersion (clamped) | how much ambiguity the system can absorb before needing clarification |
| social_resonance | live social boost from retrieval context | responsiveness to social context — high in active conversational settings |

These signals are read-only. Computing them does not modify kernel state.

---

## What It Modulates

Three bounded modifiers are computed from the geometric context:

**Identity-defer modifier** — affects the identity-sensitive deferral threshold (stance rule 4)

```
composite = 0.6 * identity_lock + 0.4 * stability
modifier  = clamp(0.85 + composite * 0.30, 0.85, 1.15)
```

High identity lock + high stability = modifier near 1.15, loosening the defer threshold (character is confident enough to not defer). Low values = modifier near 0.85, tightening the threshold (character defers more readily).

**Ambiguity-clarify modifier** — affects the clarification threshold (stance rule 5)

```
composite = 0.7 * ambiguity_tolerance + 0.3 * coherence
modifier  = clamp(0.85 + composite * 0.30, 0.85, 1.15)
```

High ambiguity tolerance + high coherence = modifier near 1.15, loosening the threshold (character can handle vague input). Low values = modifier near 0.85, tightening the threshold (character asks for clarification sooner).

**Social-compactness modifier** — affects live-social silence and brevity thresholds (stance rules 6 and 7)

```
modifier = clamp(0.85 + social_resonance * 0.30, 0.85, 1.15)
```

High social resonance = modifier near 1.15, widening the silence/brevity thresholds (character is more willing to stay quiet or be brief in social contexts).

---

## Why Bounded

The modifiers are hard-clamped to [0.85, 1.15]. This is a deliberate design choice:

1. The rule scaffold is the authority. Geometry only nudges.
2. A 15% shift is enough to differentiate characters without producing unpredictable behavior.
3. Governance rules (rule 1, rule 2) are never modulated. Safety decisions are geometry-independent.
4. If geometry is absent, all modifiers default to 1.0 — the system is always safe to run without it.

---

## Empirical Results

Tested with 7 geometric profiles across 9 inputs (63 comparisons). Results:

- **3 real stance shifts** (4.8% shift rate) — all classified GOOD
- **Shift 1:** extreme-low state + ambiguous input → character asks for clarification instead of responding (correct — a fragile agent should be more cautious)
- **Shift 2:** socially-open state + ultra-short turn → character stays silent instead of responding briefly (correct — a socially-aware agent should be more willing to observe)
- **Shift 3:** same mechanism as shift 2 under extreme-high profile
- **Governance:** unchanged across all profiles (rule 1 and 2 are never modulated)
- **Identity-defer:** modifier moves correctly but no flip observed with current thresholds (the coarse ambiguity estimator creates large steps between threshold regions)

Full data in `docs/geometric_modulation_report.md`.

---

## How to Test

**Comparison harness:** `python tests/run_geo_compare.py` runs all profiles against all inputs, reports shifts. Supports `--json` output.

**Debug endpoint:** `POST /thinking/debug` with `geometric_profile: "stable_locked"` (or any named profile) to test a specific geometric context against arbitrary input.

**Named profiles:** `GET /thinking/debug/geo_profiles` returns the 5 built-in profiles.

---

## What This Does NOT Do

- Does not modify kernel state (read-only)
- Does not affect memory writes (advisory only)
- Does not touch governance decisions (rules 1-2 are unmodulated)
- Does not replace the deterministic scaffold (modifiers are multipliers on existing thresholds)
- Does not require geometry to be present (all modifiers default to 1.0 when absent)
