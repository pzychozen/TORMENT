# TORMENT Fabric — v2.1

TORMENT is a **dynamical memory substrate for AI agents**.

Unlike traditional memory systems built purely on vector databases, TORMENT uses a **TriOcta-coupled dynamical kernel** to stabilize memory formation, maintain continuity, and prevent memory drift. In v2.0, a **living character identity layer** lets personality emerge from memory rather than static prompts. In v2.1, **event-gated compression** and **spirit return** give the system a complete memory lifecycle — memories form, compress at corridor transitions, and resurface through symbolic resonance with warmth and voice.

The system is designed for local AI companions, multi-agent hive-minds (200+ bots), research environments, and persistent AI identity experiments.

TORMENT **does not control the personality of an AI**. It stores and retrieves context in a stable way, and provides the gravitational structure for identity to emerge.

---

## Core Capabilities

- Persistent long-term memory with embedding-backed retrieval
- Living character identity (seed + memory + drift protection) — v2.0
- Kernel-character unification (character seeds modulate oscillator physics) — v2.0
- Event-gated memory compression (corridor transitions trigger J→Z scoring + two-path routing) — v2.1
- Spirit return with symbolic resonance (three return modes, warmup mechanics, voice cues) — v2.1
- Phase-cycle time tracking (duration resistance for sustained memories) — v2.1
- Character prompt layer (voice cues, tier classification, spirit return summary) — v2.1
- Identity anchors for continuity
- Emotional continuity tagging and mood drift
- Motif clustering (theme grouping) with entropy control
- Domain isolation to prevent cross-topic contamination
- Multi-agent memory fabrics with proposal governance
- Embedding drift detection and repair
- Dynamical stability via TriOcta memory kernel
- Symbolic state watermarks and resonance loop detection
- Coherence field with basin/ridge/plateau classification

---

## Architecture

TORMENT consists of three layers.

### 1. Memory Graph Layer

Stores memories as JSONL metadata with .npy embeddings. Clusters them into motifs (themes). Handles domain separation, embedding retrieval, and agent scoping.

### 2. TriOcta Memory Kernel

Three coupled oscillators on Mexican-hat potentials with D24 phase scaffold. Produces stability signals (coherence, corridor alignment, identity state) that govern memory behavior. Accepts per-character modulation of coupling strength and phase angles so different characters produce different memory dynamics.

### 3. Character Identity Layer (v2.0)

Living identity through seed planting, memory accumulation across three tiers (core/relational/situational), drift measurement, and gentle gravity correction. Characters are gravitational basins, not scripts.

### 4. Compression + Spirit Return Layer (v2.1)

Event-gated compression fires at corridor transitions, routing memories to short-path (strength reduction) or long-path (deep store export). Deep memories return through a symbolic resonance pipeline with three modes (resonance, surfacing, recollection), warmup mechanics, and character voice cues. Phase-cycle time tracking provides duration resistance so memories born during sustained corridors resist compression.

---

## Documentation

| Document | Description |
|----------|-------------|
| QUICKSTART.md | 5-minute setup guide |
| GUIDE.md | Detailed system guide |
| CHARACTER_SYSTEM.md | Living character identity layer (new in v2.0) |
| COMPANION_CONTRACT.md | Philosophy of what TORMENT does and does not do |
| TUNING.md | Configuration tuning |
| TROUBLESHOOTING.md | Operational fixes |
| MEMORY_KERNEL_ARCHITECTURE.md | Internal kernel design |
| PROJECT_OVERVIEW.md | Comprehensive architecture reference |

---

## Stability

The kernel has undergone long-horizon dynamical validation including 5000-step simulations, seed variation tests, randomized forcing experiments, and corridor stress testing. Results show bounded attractor dynamics with no runaway states.

The character layer adds per-character kernel modulation within safe bounds (g ±15%, theta_lock ±0.1 rad), preserving all existing stability guarantees.

The compression layer (v2.1) is downstream-only — it reads kernel observables but never modifies them. Trigger registry compliance is strict: Dynamics → Observables → Triggers → Diagnostics. Protected classes (canon, core_identity, seeds) are never compressed. 185 tests cover the full pipeline from ingest through compression, spirit return, and character prompt assembly.
