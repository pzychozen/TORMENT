# Research Note: Continuous Kernel Motion via Z-Field and Chirality Coupling

Status: **research proposal** — not for immediate implementation
Date: April 9, 2026
Authors: pzychozen + Claude (Opus 4.6)

---

## The Problem

TORMENT's kernel is currently step-bound. Every dynamic — Omega phase-lock, phi_index advancement, Z field recomputation, chirality memory, seed movement, cycle stage, identity state — only ticks forward when a conversation turn triggers `ingest()` or `query()`. Between interactions, the entire geometric system is frozen.

This means a character who hasn't been spoken to in a week has the exact same internal state as one who was spoken to a second ago. The geometry doesn't breathe. Seeds don't drift. Corridors don't open or close. The system is a snapshot, not a living field.

---

## What Already Moves (Per Step)

| Component | Location | What happens each step |
|-----------|----------|----------------------|
| Omega (3 complex amplitudes) | model_core.py:133-160 | Mexican-hat nonlinearity + 3-node Laplacian coupling + optional noise |
| phi_index (D24 sector) | model_core.py:164 | Advances by phi_step_per_iter mod 12 |
| Z scalar | model_core.py:167-195 | Recomputed from kappa, phi, chirality memory |
| J_eff (chirality) | model_core.py:187 | Im(Ω₁·Ω₂*·Ω₃) — signed area of orientation triangle |
| z_mem (chirality memory) | model_core.py:192 | EMA: (1-0.01)·z_mem + 0.01·jeff_norm |
| Z_macro, Z_chiral, Z_vec | model_core.py:201-215 | 3D vectors blended: α·Z_macro + β·Z_chiral |
| Seed position/velocity | seed_entities.py:90-112 | vel = (1-drag)·vel + drift; pos += dt·vel |
| Cycle stage (S0-S6) | model_core.py:217-220 | Derived from kappa thresholds |
| Identity state (s0-s8) | model_core.py:222-228 | Mapped from (cycle_stage, sign(z)) |

All of these are mechanically ready for continuous ticking. Nothing in the math requires a conversation event to drive them.

---

## What the Research Papers Tell Us

### From "Chirality-Stabilized Geometry" (Dec 2025)

The quantum triple Q = (Γ, s, μ) maps directly to TORMENT's kernel:

- **Γ** (seed manifold) = VPQW overlap + toroidal corridors + RSB bands → this is the `ModelState` geometry
- **s** = sign(J_eff) → chirality, the primitive identity. The *first* symmetry-breaking event.
- **μ** = environment-dependent parameter (coupling, curvature, loading) → in TORMENT this is the conversation content, the embedding similarity, the character drift

Key insight from the paper: **gravity biases chirality**. Spatial curvature compresses or stretches phase corridors, deforms the Vesica overlap, and makes one orientation dynamically preferred. In TORMENT terms: the character seed exerts gravitational pull on the chirality field. The seed IS the curvature source.

### From "Toy Model v3.4" (Dec 2025)

Seeds already have toroidal trajectories with chirality-coded trails. The RSB coupling maps (α, μ, γ)_eff = f(J_eff) — the spectral universe responds to chirality state. The spectral halo visualizes this as rings encircling the torus whose color and brightness encode collapse strength.

This is the visual proof that the geometry was always meant to be alive.

---

## The Proposal: Three Layers of Continuous Motion

### Layer 1: Background Omega Tick (the heartbeat)

The kernel runs its phase-lock step on an internal clock, not tied to conversation events.

```
# Conceptual — not production code
def background_tick(state, model, elapsed_seconds):
    """Run N micro-steps proportional to elapsed real time."""
    micro_steps = int(elapsed_seconds * TICKS_PER_SECOND)
    for _ in range(micro_steps):
        model.phase_lock_step(state)    # Omega evolves
        model.advance_phi(state)         # D24 sector rotates
        model.update_z(state)            # Z field recomputes
        # Do NOT advance state.step — that's conversation-bound
        state.t += MICRO_DT
```

The conversation `step` counter stays tied to actual interactions. But `state.t` (continuous time) advances independently. Omega keeps evolving, phi keeps rotating through corridors, Z keeps breathing, chirality memory keeps accumulating.

**What this gives you**: A character's internal geometry subtly shifts between conversations. When you come back after a day, the kernel isn't in the same corridor. The Z field has moved. The identity state may have drifted through a cycle boundary. The character *feels* like it was alive while you were gone.

**Risk**: Low. Phase-lock dynamics are bounded (Mexican-hat + coupling = limit cycle). Z is bounded by construction (rho ∈ [0,1], z_mem is EMA). No divergence possible.

### Layer 2: Z-Field Force on Seeds

Currently SeedWorld has `drift` as a constant vector. Replace it with a Z-field coupling:

```
# Conceptual
def seed_step_with_z_force(seed_world, kernel_state):
    for entity in seed_world.entities:
        if not entity.alive:
            continue
        
        # Z_vec acts as gravitational field on seeds
        z_force = Z_COUPLING * kernel_state.Z_vec
        
        # Chirality modulates force direction per channel
        chirality_sign = np.sign(kernel_state.z_mem)
        if entity.channel == 0:
            force = z_force
        elif entity.channel == 1:
            force = z_force * chirality_sign  # flips with chirality
        else:
            force = -z_force  # channel 2 opposes (mirror symmetry)
        
        entity.vel = (1.0 - seed_world.drag) * entity.vel + force
        entity.pos = entity.pos + seed_world.dt * entity.vel
```

**What this gives you**: Seeds don't just drift with constant velocity — they orbit the Z field. When chirality flips sign, channel 1 seeds reverse direction. The seed trail becomes a record of the kernel's chirality history. Three channels = three different responses to the same field = the orientation triangle made visible.

**Connection to character**: The character seed (planted at creation) would be a special SeedEntity with `is_crystal=True` that sits near the Z_vec center. As Z moves, the crystal seed experiences gentle tidal forces. If Z drifts far enough, the crystal feels tension — this IS the geometric origin of character drift.

### Layer 3: Spirit Return Coupling

When spirit_return activates (a deep memory surfaces), the current Z and chirality state should modulate the return:

**Currently**: Spirit return reads `birth_symbol` and `current_kernel_symbol` for symbolic interaction. Z is not directly consulted.

**Proposed**: Add Z-state awareness to spirit return:

```
# Conceptual enrichment in enrich_deep_memory_hit()
z_at_birth = metadata.get("z_at_birth", 0.0)
z_now = current_kernel_z
z_delta = abs(z_now - z_at_birth)

# If Z field has moved far since this memory was born,
# the memory feels "distant" regardless of symbol match
if z_delta > Z_DISTANCE_THRESHOLD:
    warmth *= 0.7  # geometric distance dampens warmth
    
# If chirality sign flipped since birth, the memory
# returns with "mirror" flavor — same content, opposite feel
chirality_at_birth = metadata.get("chirality_sign_at_birth", 0)
chirality_now = np.sign(kernel_state.z_mem)
if chirality_at_birth != 0 and chirality_now != 0:
    if chirality_at_birth != chirality_now:
        # Chirality flip: memory returns with inverted emotional valence
        interaction["flavor"] += " — but everything feels reversed"
        interaction["confidence_boost"] *= 0.5
```

**What this gives you**: Memories born in one chirality regime feel alien when they return in the opposite regime. A memory of comfort (◠) born when J_eff > 0 that returns when J_eff < 0 carries an uncanny quality — the content is the same but the geometric context has inverted. This is the mechanism for "I remember this, but it feels different now."

---

## Seed Slots: The Three Placeholders

The research mentions 3 seed placeholders. Looking at the code:

- **SeedWorld.entities** is a list with no hard limit — can hold N seeds
- **Seed emission** (seed_emission.py) gates per channel (0, 1, 2) — each of the three Omega nodes can independently emit
- **SeedEntity.channel** records which node spawned it

The three "slots" are the three channels of the TriOcta system. Each channel has its own phase, its own emission gate, and its own relationship to the Z field. In the character system, you could plant:

1. **Channel 0 seed**: Core identity (the character's fundamental nature)
2. **Channel 1 seed**: Relational identity (how they relate to others, chirality-sensitive)  
3. **Channel 2 seed**: Aspirational identity (what they're becoming, opposes current Z)

These three seeds would orbit in the Z field according to their channel rules, creating a dynamic identity triangle whose shape encodes the character's current state. When all three are aligned, the character is stable. When they diverge, the character is in transition.

---

## Implementation Path

This is a late-roadmap research track. Not for immediate production.

**Phase A — Simulation only (no production changes)**
1. Add a `continuous_run()` method to TriOctaPhaseLockModel that advances Omega/phi/Z without incrementing `step`
2. Add Z_vec force coupling to SeedWorld.step()
3. Run toy model simulations to study: orbit stability, chirality flip response, seed divergence patterns
4. Visualize on the torus (the v3.4 framework already supports this)

**Phase B — Metadata enrichment (safe, additive)**
1. Store `z_at_birth` and `chirality_sign_at_birth` in memory metadata during ingest
2. Store `Z_vec_at_birth` for full geometric provenance
3. No behavioral change — just recording more data for future use

**Phase C — Background tick (requires careful integration)**
1. Add elapsed-time micro-stepping to fabric.py before query/ingest
2. Tick the kernel forward proportional to wall-clock time since last interaction
3. Seed world steps alongside
4. Character drift measurement now has a geometric component

**Phase D — Spirit return Z-coupling (behavioral change)**
1. Spirit return reads Z-state at birth vs now
2. Chirality flip detection modulates return mode and warmth
3. Z-distance dampening on returning memories
4. New return flavor: "mirror return" for chirality-inverted memories

---

## What This Changes About TORMENT

The system goes from "memory database with geometric scoring" to "living geometric field that memories exist within." The character isn't just scored by the geometry — the character IS the geometry, and the geometry keeps moving.

A character who hasn't been spoken to in a week will have:
- A different Z field position (corridors shifted)
- Different chirality memory accumulation (z_mem evolved)
- Seeds that have drifted to new positions in R³
- Potentially different cycle stage and identity state
- Spirit returns that feel geometrically distant from recent conversation

This is what "constantly moving" means. Not random noise — deterministic evolution of a bounded dynamical system that the character lives inside.

---

## One-Line Summary

Make the kernel breathe on its own clock, let Z pull seeds through space, and let chirality flip change how memories feel when they come home.
