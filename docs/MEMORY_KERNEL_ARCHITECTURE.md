# Memory Kernel Architecture

TORMENT v2.1

---

## Overview

TORMENT uses a dynamical system to stabilize memory behavior. The kernel is implemented as `TriOctaMemoryKernel`, which integrates a phase-coupled dynamical model with memory graph updates.

In v2.0, the kernel accepts per-character modulation so that different characters produce different memory dynamics from the same input.

---

## Motivation

Traditional AI memory systems rely on vector databases, heuristic scoring, and time decay. These systems suffer from memory drift, context fragmentation, and unstable retrieval weighting over time.

TORMENT instead uses a **dynamical attractor system** to stabilize memory formation. The kernel ensures memory behavior remains bounded and self-regulating over long horizons.

---

## Core Model

The kernel operates on a triad of coupled oscillatory nodes.

State variable: **Omega** — three complex amplitudes representing the oscillator triad.

Each step evolves according to:

Omega_next = Omega + nonlinear + coupling + delta

Where nonlinear = eps * Omega * (k - |Omega|^2) is a Mexican-hat potential, coupling = g * L * Omega is Laplacian coupling between all three nodes, and delta comes from external observation forcing.

An optional **phase-triad synchronization operator** stabilizes phase alignment.

---

## Character Modulation (v2.0)

When an agent has a character seed, the kernel's behavior is modulated:

**Omega initialization**: the seed text is embedded and converted directly into the oscillator's initial state (3 complex amplitudes). Different characters start in different regions of phase space.

**Coupling strength (g)**: modulated ±15% based on the character's warmth score. Warm characters couple tighter, producing stronger coherence signals and more confident memory formation.

**Phase lock angle (theta_lock)**: shifted ±0.1 rad based on the character's structure score. This alters which identity states the kernel naturally gravitates toward.

The modulation is applied per-step via temporary parameter override with restore-after, so the global model parameters remain unchanged.

---

## Observables

The kernel produces stability metrics:

| Metric | Meaning |
|--------|---------|
| coh | Dispersion-based phase coherence (smoothed) |
| disp | Phase dispersion between oscillator nodes |
| coh_phase | Raw phase coherence before smoothing |
| z | Chiral Z-field projection |
| tear | Corridor tearing risk (misalignment EMA) |
| surv | Survival memory (decaying corridor trace) |

These metrics regulate memory writes, detect instability, and maintain corridor integrity.

---

## Memory Formation Signals

The kernel emits `KernelSignals` to the fabric. All driven by coherence — higher coherence produces stronger, longer-lived, more promotable memories:

| Signal | Formula |
|--------|---------|
| strength | 0.40 + 0.60 * coh |
| confidence | 0.35 + 0.65 * coh |
| half_life | 20 + 80 * coh |
| promotion_score | 0.50 + 0.50 * coh |

With character modulation, warm characters (higher g) tend toward slightly higher coherence, matching the intuition that emotionally bonded interactions create stronger memories.

---

## Multipliers (tri_mod)

| Key | Range | Controls |
|-----|-------|----------|
| write_mult | 0.90 - 1.10 | Memory write strength scaling |
| proposal_mult | 0.90 - 1.10 | Shared proposal threshold scaling |
| bridge_p | 0.03 - 0.20 | Cross-domain bridge probability |
| bridge_sim | 0.84 - 0.90 | Bridge similarity threshold |

Corridor alignment provides additional nudges via survival memory and proximity scaling.

---

## Corridor Concept

The system maintains stability corridors. Tangent alignment between torus XY motion and SU(3) uxy jumps determines whether the system is "in corridor" (aligned, memory formation boosted) or "tearing" (misaligned, dampened).

If the kernel approaches tearing thresholds, multipliers and gating rules dampen memory formation. This prevents runaway memory accumulation.

---

## Event-Gated Compression (v2.1)

The kernel's corridor transitions serve double duty: they govern memory formation quality and they gate memory compression. Compression fires at discrete corridor events rather than continuously, preserving the dynamical meaning of corridor states.

**Event detection**: an `EventDetector` monitors tri_mod observables at each ingest step and fires on three transitions: corridor exit (in_corridor True→False), cycle stage change, and emergency tear (tearing_risk exceeds threshold while in corridor). The detector is stateful and requires a priming step before it can fire.

**Scoring (J→Z)**: compression scoring follows the same J→Z temporal ordering as the kernel's own processing. J-score (relational importance, 60% weight) evaluates strength, retrieval count, and motif basin membership. Z-score (geometric organization, 40% weight) evaluates coherence field alignment and age. The combined score determines compressibility — higher means more compressible.

**Duration resistance**: the `PhaseTimer` (one per agent) tracks how long the system stays in a given phase or corridor. When a memory was born during a sustained corridor (≥10 steps), its j_score is reduced by 0.15, making it harder to compress. The intuition: long corridors represent deep, stable processing states — memories formed there are structurally valuable.

**Routing**: low-scoring and young candidates take the short path (strength reduction in the core graph). High-scoring old candidates take the long path (export to DeepMemoryStore for potential spirit return).

**Key design constraint**: compression is a downstream consumer of kernel observables, never an upstream influence. The trigger registry compliance is strict: Dynamics → Observables → Triggers → Diagnostics. Compression reads kernel state; it never modifies it.

---

## Spirit Return and Warmup Mechanics (v2.1)

When compressed memories are retrieved from the deep store during a sparse query, they pass through a warmup pipeline before reaching the character layer.

**Warmth accumulation**: each deep memory starts at warmth 0.2 on first retrieval. Each subsequent retrieval within a 200-step window adds 0.15, capping at 1.0. This prevents compressed memories from returning at full intensity immediately — they warm up gradually as the system retrieves them repeatedly.

**Sustained warmth boost**: memories born during sustained corridors (phase_duration_steps or corridor_duration_steps ≥ 10) receive a warmth floor of 0.3 instead of 0.2. This connects Phase-Cycle Time to spirit return: sustained experience warms faster.

**Symbol interaction**: each deep memory carries its birth symbol (from the coherence field geometry at creation). On return, the birth symbol is compared against the current kernel symbol via a 19-rule interaction matrix. The interaction type (e.g., "fulfilled", "disrupted", "integration") and human-readable flavor text are injected into the returning memory's metadata.

**Return modes**: based on warmth, symbol match, and compression path, each returning memory is classified as resonance (rare, vivid, déjà vu), surfacing (moderate, gentle, present-tense), or recollection (default, past-tense, distilled). The mode determines the strength multiplier and voice cue that reaches the character layer.

---

## Result

The TriOcta kernel creates a **bounded dynamical memory attractor** rather than an unregulated storage system. In v2.0, this attractor is uniquely shaped by each character's seed — the physics of memory formation inherently reflects who the character is. In v2.1, the attractor now includes compression gating (memories are released at corridor transitions), deep memory return (compressed memories resurface through symbolic resonance), and duration awareness (sustained corridor states protect structurally valuable memories).
