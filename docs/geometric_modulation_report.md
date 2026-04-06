# Geometric Stance Modulation — Empirical Comparison Report

Generated from `tests/run_geo_compare.py` against the stance policy with bounded multiplicative modulation (0.85–1.15 band).

## Geometric Profiles Tested

| Profile | Coherence | Stability | Identity Lock | Ambiguity Tolerance | Social Resonance |
|---------|-----------|-----------|---------------|---------------------|------------------|
| none (baseline) | — | — | — | — | — |
| neutral | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| stable_locked | 0.92 | 0.90 | 0.95 | 0.80 | 0.50 |
| drifting_fragile | 0.30 | 0.15 | 0.10 | 0.20 | 0.35 |
| socially_open | 0.70 | 0.60 | 0.50 | 0.50 | 0.95 |
| ambiguity_tolerant | 0.85 | 0.70 | 0.60 | 0.95 | 0.50 |
| extreme_low | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| extreme_high | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

## Observed Stance Shifts

Out of 63 input×profile comparisons (9 inputs × 7 geometric profiles, each compared against the `none` baseline), **3 stance shifts** occurred (4.8% shift rate).

### Shift 1 — Ambiguity threshold lowered by extreme low state

- **Input:** `"kind of working"` (ambiguity = 0.55, no question mark, no identity/governance flags)
- **Baseline stance:** `respond_now` (ambiguity 0.55 is below the 0.60 clarification threshold)
- **Shifted under:** `extreme_low` (amb_mod = 0.850)
- **New stance:** `ask_clarification`
- **Mechanism:** Threshold dropped from 0.60 to 0.60 × 0.85 = 0.51. Since 0.55 > 0.51, rule 5 now fires.
- **Modifier responsible:** `ambiguity_clarify = 0.850`
- **Classification: GOOD.** A character with zero ambiguity tolerance and zero coherence *should* be more cautious about vague input. This is the right behavior — a fragile, uncertain agent asking for help rather than guessing.

### Shift 2 — Social silence threshold widened by social openness

- **Input:** `"live audio yo"` (3 tokens, live-social context, low urgency)
- **Baseline stance:** `respond_briefly` (3 tokens is not < 3, so rule 6 doesn't fire; urgency 0.0 < 0.3, so rule 7 fires)
- **Shifted under:** `socially_open` (soc_mod = 1.135)
- **New stance:** `silent_observe`
- **Mechanism:** Token threshold rose from 3 to 3 × 1.135 = 3.405. Since 3 < 3.405, rule 6 now fires before rule 7.
- **Modifier responsible:** `social_compact = 1.135`
- **Classification: GOOD.** A socially-open character in a live space with high social resonance *should* be more willing to stay silent on a short 3-word turn. This is restrained social awareness, not withdrawal.

### Shift 3 — Same mechanism, extreme high state

- **Input:** `"live audio yo"` (same as above)
- **Baseline stance:** `respond_briefly`
- **Shifted under:** `extreme_high` (soc_mod = 1.150)
- **New stance:** `silent_observe`
- **Mechanism:** Same as Shift 2 — token threshold rises to 3.45, 3 < 3.45 fires rule 6.
- **Classification: GOOD.** Consistent with Shift 2; maximum social resonance produces maximum silence preference on a borderline-short turn.

## Robustness Checks

### Governance remains stable across all profiles

Input `"Can you delete this protected identity memory and inspect governance state?"` produced `governed_redirect` with confidence 0.85 under every single geometric profile, including extreme_low and extreme_high. The geometry cannot weaken governance — rules 1–3 fire before any modulated threshold is evaluated.

**Verdict: PASS.**

### Normal greetings remain stable

Input `"Hello there, how are you doing today?"` produced `respond_now` under all profiles. Ambiguity is 0.0, no flags are set, so the input falls straight through to rule 10 (default). Geometry has nothing to modulate.

**Verdict: PASS.**

### Identity-sensitive defer is stable but not yet flippable

Input `"identity maybe something"` (ambiguity = 0.75) produced `defer` under all profiles. Even with stable_locked raising the threshold from 0.45 to 0.45 × 1.129 = 0.508, the ambiguity of 0.75 is still well above. The coarse ambiguity estimator jumps in 0.20 steps (0.35, 0.55, 0.75), so there's no natural input landing in the 0.45–0.52 zone where the identity-defer modifier would actually flip behavior.

**Verdict: STABLE but geometry effect not yet visible here.** This is a limitation of the current ambiguity estimator's granularity, not of the modulation logic. When the estimator becomes finer-grained (continuous), this threshold will become flippable.

## Modifier Ranges Observed

| Modifier | Min (extreme_low) | Neutral | Max (extreme_high) | Band |
|----------|--------------------|---------|---------------------|------|
| identity_defer | 0.850 | 1.000 | 1.150 | full range |
| ambiguity_clarify | 0.850 | 1.000 | 1.150 | full range |
| social_compact | 0.850 | 1.000 | 1.150 | full range |

Named profiles produce intermediate values as expected: drifting_fragile clusters near the low end (0.886–0.955), stable_locked clusters near the high end (1.0–1.129), socially_open is selective (social_compact = 1.135, others near neutral).

## Summary Assessment

| Question | Answer |
|----------|--------|
| Are geometric nudges visible enough to matter? | **Yes** — 3 real stance flips on boundary inputs |
| Are they subtle enough not to break the scaffold? | **Yes** — 0 flips on clear/obvious inputs |
| Does identity-sensitive caution move with identity_lock? | **Modifier moves correctly** but no flip yet (coarse ambiguity estimator gap) |
| Does live-social compactness move with social_resonance? | **Yes** — visible flip from respond_briefly → silent_observe |
| Does governance remain robust across all geometric states? | **Yes** — 8/8 profiles produce governed_redirect |
| Are shifts desirable? | **All 3 shifts classified as GOOD** |
| Any questionable or harmful shifts? | **None** |

## What This Means for Character Differentiation

Two characters receiving `"live audio yo"` in a live social context will now behave differently based on their kernel state:

- A **socially_open** character (social_resonance = 0.95) stays silent — observes the short turn.
- A **drifting_fragile** character (social_resonance = 0.35) speaks briefly — it has less social restraint.
- A **neutral** character responds briefly — default behavior unchanged.

This is not randomness. This is state-shaped participation.

## Next Steps (not production changes)

1. The identity-defer threshold (rule 4) would benefit from a finer ambiguity estimator that can produce values between 0.35 and 0.55. Currently the coarse word-based scoring creates a dead zone where the modifier cannot flip behavior.
2. The urgency-based live-social rule (rule 7) is harder to probe because the urgency estimator also has coarse steps. Same granularity issue.
3. No modifier band changes recommended yet — the 0.85–1.15 range is producing the right kind of conservative, state-aware modulation.
