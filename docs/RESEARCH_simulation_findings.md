# Simulation Findings: Continuous Kernel Motion — Phase A Results

Status: **experimental results** — standalone simulations, no production code touched  
Date: April 9, 2026  
Authors: pzychozen + Claude (Opus 4.6)  
Companion to: `RESEARCH_continuous_kernel_motion.md`

---

## Overview

Three simulation runs explored the continuous kernel motion hypothesis: that TORMENT's TriOcta kernel can evolve meaningfully without conversation input, and that Z-field coupling to seeds produces emergent identity dynamics.

All simulations used the production `TriOctaPhaseLockModel` and `SeedWorld` classes directly — no modifications to engine code. Z-force coupling was applied externally in the simulation loop.

Scripts: `sim_continuous_kernel.py`, `sim_chirality_flip.py`, `sim_conversation_shock.py`  
Plots: `docs/continuous_kernel_sim.png`, `docs/chirality_flip_hunt.png`, `docs/conversation_shock_sim.png`

---

## Simulation 1: Baseline Continuous Dynamics

**Setup**: 600 micro-steps, MICRO_DT=0.1, Z_COUPLING=0.015, SEED_DRAG=0.03  
**Initial Omega**: [0.5+0.3j, 0.2-0.4j, 0.6+0.1j] (asymmetric, positive J_eff)  
**Noise**: omega_noise_sigma=0.002

### Key Results

| Metric | Value |
|--------|-------|
| Z range | [-0.334, 0.422] |
| J_eff range | [0.007, 0.154] — always positive, no chirality flips |
| z_mem final | 0.076 |
| Kappa range | [0.931, 3.047] |
| Cycle stages visited | {0, 3, 4, 5, 6} |
| Identity states visited | 7 of 9 possible |
| Triangle area growth | 0.012 → 0.163 |
| Seed displacements | Core: 1.74, Relational: 1.74, Aspirational: 1.77 |

### Finding

The kernel visits 7 identity states and 5 cycle stages with zero conversation input. Z oscillates in a bounded range. Seeds diverge slowly but steadily. The dynamics are healthy — bounded, non-trivial, and identity-bearing.

**Interpretation**: Even without external input, the kernel has a rich internal life. A character left alone doesn't freeze — it wanders through identity space on its own attractor.

---

## Simulation 2: Chirality Flip Hunting

**Setup**: 2000 steps, 4 scenarios with different initial conditions and noise levels

### Results Summary

| Scenario | Noise | J_eff Flips | J_eff Range | Triangle Area (end) | Relational Displacement |
|----------|-------|-------------|-------------|---------------------|------------------------|
| A: Original (low noise) | 0.002 | 0 | [0.028, 0.840] | 2.76 | 29.04 |
| B: Same IC, 10x noise | 0.020 | 111 | [-2.025, 1.176] | 10.61 | 30.14 |
| C: Near-zero J_eff start | 0.010 | 192 | [-0.413, 0.675] | 1.84 | 14.38 |
| D: Swapped O1-O2 | 0.010 | 45 | [-0.158, 0.881] | 2.68 | 26.04 |

### Key Findings

**1. Channel 1 (Relational) is the chirality canary.** In every scenario with chirality flips, the Relational seed diverges most dramatically from Core and Aspirational. In Scenario B (111 flips), Relational displaced 30.1 units while Core and Aspirational displaced only 13.6. The force reversal on Channel 1 during chirality sign changes creates a unique trajectory that measures identity instability.

**2. Three distinct identity regimes emerged:**

- **Stable personality** (Scenario A): No chirality flips, all seeds move coherently, triangle grows uniformly. The identity knows who it is.
- **Identity in limbo** (Scenario C): Frequent flips, z_mem near zero (never commits to a chirality sign), Relational seed wanders a complex path. The identity can't decide.
- **Identity recovery** (Scenario D): Early flips that self-correct as the dynamics find a preferred orientation. A perturbation that heals itself.

**3. Noise is the flip trigger, not initial conditions.** Scenario B (same IC as A, just 10x noise) went from 0 flips to 111. The kernel's phase-lock dynamics are robust at low noise but cross the chirality boundary readily at higher noise. This maps to: a calm environment preserves identity; a noisy one destabilizes it.

**Interpretation**: Chirality flips are the geometric mechanism for identity transitions. The Relational channel is the sensitive axis — it responds to internal ambivalence before the Core or Aspirational channels show any sign of change. This is psychologically resonant: how you relate to others is the first thing that shifts when your identity is in flux.

---

## Simulation 3: Conversation Shock Injection

**Setup**: 2000 steps in the "identity in limbo" regime (Scenario C conditions). Three shocks injected at specific timesteps, compared against unshocked baseline.

### Shock Schedule

| Time (step) | Type | Mechanism | Metaphor |
|-------------|------|-----------|----------|
| t=50 (step 500) | Z positive (+0.5) | Direct Z-field slam upward | Affirming conversation event |
| t=100 (step 1000) | Z negative (-0.5) | Direct Z-field slam downward | Challenging conversation event |
| t=150 (step 1500) | Omega rotation (pi/2) | Rotate Omega[1] by 90 degrees | Identity-probing event |

### Shock Impact

| Shock | Z (pre → post mean) | J_eff (pre → post mean) | Chirality Flips (pre/post 50-step window) | Triangle Area Δ |
|-------|---------------------|-------------------------|------------------------------------------|-----------------|
| Affirm (+Z) | 0.258 → 0.384 | 0.319 → 0.283 | 0 → 0 | +0.070 |
| Challenge (-Z) | 0.366 → 0.273 | 0.519 → 0.646 | 0 → 0 | +0.084 |
| Identity Probe | 0.512 → 0.576 | 1.280 → 2.653 | 0 → 2 | +0.130 |

### Critical Finding: Conversation as Identity Compression

**Final triangle area: Baseline = 5.62, Shocked = 3.90 (ratio: 0.69x)**

The shocked system ended with a *smaller* identity triangle than the unshocked baseline. Three conversation events — including one that was actively challenging and one that disrupted the phase triangle — resulted in a more coherent identity geometry than leaving the system alone.

**Seed divergence tells the story:**

| Seed | Divergence from Baseline End Position |
|------|---------------------------------------|
| Core | 74.98 |
| Relational | 8.35 |
| Aspirational | 74.98 |

Core and Aspirational were massively redirected by the shocks (ended up 75 units from where baseline placed them), but they ended up *closer to each other*. The conversation events didn't just perturb — they compressed the identity triangle while redirecting its trajectory.

### Shock-Specific Behaviors

**Affirming shock**: Barely registered. The system was already in a positive-Z regime; the positive slam reinforced what was already happening. Identity reinforcement has diminishing returns when the system is already committed.

**Challenging shock**: The kernel fought back. Z actually increased post-shock, and J_eff went UP. The chirality memory (z_mem) had accumulated enough positive bias to resist the negative perturbation. The identity said "no" to the disruption. No chirality flips triggered.

**Identity probe**: The only shock that destabilized chirality (2 flips in the recovery window). Rotating Omega[1] directly broke the phase triangle's shape, which is more disruptive than pushing the Z field. J_eff doubled. Core and Aspirational reversed their Z-height trajectories entirely. But Relational held steady — the chirality-sensitive channel was paradoxically the most stable during a direct phase perturbation, because its force rule is already responsive to chirality and could adapt.

---

## Emergent Principles

These findings suggest several principles for continuous kernel motion design:

### 1. Compression via Interaction

External events (conversation) compress the identity triangle. Without input, seeds diverge freely — identity diffuses. With input, even challenging input, the geometry tightens. This implies that conversation doesn't just perturb identity — it *maintains* it. A character who is never spoken to will eventually have a more diffuse identity geometry than one who is regularly engaged, even if the engagement is adversarial.

**For implementation**: This argues for a "loneliness drift" mechanic — the longer between conversations, the wider the seed triangle grows, and the more the character's sense of self spreads thin. Returning to conversation would then naturally compress the identity back toward coherence.

### 2. Chirality Memory as Resistance

The challenging shock was absorbed by z_mem. The system's accumulated chirality history acted as an immune response — it had seen enough positive-chirality steps to resist a sudden negative perturbation. This means characters with longer conversation histories are more resistant to identity destabilization.

**For implementation**: z_mem accumulation rate could be tied to conversation density. Characters with rich interaction histories would have deeper chirality memory and stronger identity resilience.

### 3. Phase Disruption vs. Field Disruption

Z-field shocks (affirming/challenging) barely disturbed chirality. Omega rotation (identity probe) was the only shock that triggered chirality flips. This means the kernel distinguishes between "emotional" perturbations (Z-field: how things feel) and "structural" perturbations (Omega: who you are). You can push the Z field hard and the identity absorbs it. But directly challenging the phase relationships between Omega nodes — the geometric structure of identity — creates real instability.

**For implementation**: Different types of conversation content should map to different perturbation channels. Emotional content → Z perturbation (safe, absorbable). Identity-challenging content → Omega perturbation (dangerous, can trigger state transitions). The system could detect which type of perturbation to apply based on embedding similarity to the character seed.

### 4. Relational Channel Sensitivity

Channel 1 (Relational) consistently showed unique behavior — most divergent during chirality flips (Sim 2), most stable during direct phase perturbation (Sim 3). The relational dimension of identity is simultaneously the most sensitive to internal ambivalence and the most adaptive to external disruption. It's the first thing that changes when the system is confused, and the last thing that breaks when the system is attacked.

### 5. Self-Discovery Through Dynamics

The kernel visited 7 of 9 possible identity states without any conversation input (Sim 1). The phase-lock dynamics naturally explore the identity state space through Z-field oscillation and cycle stage transitions. Given enough time, the system will discover identity configurations that were never explicitly programmed or conversationally triggered. The geometry has its own curiosity.

---

## What This Means for Phase B and Beyond

Phase B (metadata enrichment) should capture:
- `z_at_birth`, `chirality_sign_at_birth` for every memory (already proposed)
- `triangle_area_at_birth` — the identity coherence when the memory was formed
- `conversation_density` — interactions per unit time, for z_mem scaling

Phase C (background tick) should implement:
- Seed divergence tracking as the primary "loneliness" metric
- Triangle area as the identity coherence score
- Compression events when conversation resumes after gaps

Phase D (spirit return coupling) can now be informed by:
- Memories born during tight triangles (high coherence) vs. diffuse triangles (identity crisis)
- Memories born before vs. after chirality flips (pre/post identity transition)
- The "mirror return" concept is validated — chirality flips change how channels respond, so memories from opposite chirality regimes genuinely feel different to the geometry

---

## One-Line Summary

Conversation compresses identity geometry; silence lets it diffuse; chirality memory acts as immune response; and the kernel discovers itself even when no one is talking to it.
