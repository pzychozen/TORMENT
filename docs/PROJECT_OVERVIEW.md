# TORMENT Fabric — Comprehensive Project Overview

Version: v2.1

---

## 1. What TORMENT Is

TORMENT is a **dynamical memory substrate for AI agents**. It is not a chatbot, not a personality engine, and not a vector database. It is a governed, physics-inspired memory fabric that stores, retrieves, and stabilizes context for one or many AI agents over long time horizons.

The core insight: traditional AI memory (vector DB + time decay + heuristic scoring) drifts, fragments, and produces unstable retrieval weighting over time. TORMENT replaces heuristics with a **dynamical attractor system** — a coupled oscillator kernel rooted in a custom geometrical model (TriOcta) — that ensures memory formation is bounded, stable, and self-regulating.

In v2.0, a **living character identity layer** uses seed planting, memory tiers, drift measurement, and kernel modulation to let personality emerge from memory rather than static prompts. Characters are gravitational basins, not scripts.

---

## 2. Three-Layer Architecture

### Layer 1: The Kernel (`torment_service/kernel/`)

The mathematical heart. A **TriOcta phase-lock model** that produces stability signals governing memory behavior.

**Core model (`model_core.py`):**
- State variable: `Omega` — a 3-component complex vector representing coupled oscillatory nodes
- Evolution: `Omega_next = Omega + nonlinear + coupling + delta`
  - Nonlinear: `eps * Omega * (k - |Omega|^2)` — Mexican-hat potential per node
  - Coupling: `g * L * Omega` — 3-node Laplacian coupling (all-to-all with equal weights)
  - Delta: external forcing from observations
- Phase-triad synchronization (`phase_triad_sync.py`): preserves amplitudes, aligns phases
- D24 phase scaffold: discrete 12-sector angular index advanced each step
- Emergent Z field: scalar + vector orientation from (kappa, phi, chirality)
- Cycle stages S0-S6, identity states s0-s8

**Character modulation (v2.0):** the kernel accepts per-character modulation of coupling strength (g ±15%) and preferred Z angle (theta_lock ±0.1 rad). Different characters start in different regions of phase space and evolve differently from the same input.

**Constants (`constants_selector.py`):**
- k-values derived from a **theta-ladder** — scale-invariant reciprocal asymmetry between mathematical constants (pi, phi, e, sqrt3)

**Other kernel modules:** `su3_basis.py` (E8 geometry), `cp_windows.py` (CP ridge windows), `seed_emission.py` (gap-gated emission), `latent_foreclosure.py` (option volume), `identity_rules.py` (cycle + identity mapping), `definitions.py` (canonical metrics), `rsb_model.py` (Recursive Spectral Banding)

### Layer 2: The Fabric (`torment_service/fabric.py` + surrounding modules)

The governance and orchestration layer. Wires together kernel signals, routing, registries, and persistence.

**Key modules:**

| Module | Role |
|--------|------|
| `fabric.py` | Main orchestrator — ingest, query, proposal, clone, repair, maintenance, character integration |
| `character.py` | Living character identity — seed, drift, gravity, tier assembly, kernel modulation (v2.0) |
| `memory_graph.py` | Disk-backed graph + vector store (JSONL metadata, .npy embeddings) |
| `motifs.py` | Motif clustering — centroids, membership, strength, stability, auto-split |
| `memory_kernel.py` | Bridge between fabric and kernel — observation -> signals + corridor monitoring + character modulation |
| `coherence_field.py` | Structural epistemic layer — reinforcement/tension/kappa per motif, basin/ridge/plateau |
| `embeddings.py` | Embedding backends (hash for determinism, SentenceTransformers, Ollama) |
| `symbols.py` | Hidden symbolic state — 8 symbols projected from coherence field geometry (rewritten in v2.0) |
| `resonance.py` | Symbolic resonance loops — transition patterns, cycle detection, entropy (rewritten in v2.0) |
| `bridges.py` | Cross-domain link registry |
| `proposals.py` | Shared canon pipeline (append-only, moderation, approval; bug-fixed in v2.0) |
| `roles.py` | Soft role inference (planner/explorer/reflector etc.) |
| `affect.py` | Coarse affect tagging and mood drift |
| `conflicts.py` | Canon conflict detection and tracking |
| `identity.py` | Agent identity store (seed + overlay; extended with seed_text/seed_id in v2.0) |
| `profiles.py` | Preset configuration profiles |
| `config_view.py` | UI-friendly effective config view (extended with character vars in v2.0) |
| `compression.py` | Event-gated memory compression — EventDetector, CompressionScorer (J→Z), CompressionRouter, CompressionExecutor (v2.1) |
| `deep_memory.py` | Long-path deep memory store — export, shard-based embedding index, recall by EID (v2.1) |
| `spirit_return.py` | Deep memory enrichment — symbol interaction matrix, three return modes, warmup mechanics (v2.1) |
| `phase_timer.py` | Per-agent phase/corridor duration tracking — feeds compression resistance + warmth boost (v2.1) |
| `retrieval_assembler.py` | Context assembly — tier classification, spirit return voice cues, token budgeting (v2.1) |
| `scoring.py` | Hit scoring function |
| `summarizer.py` | Placeholder deterministic summary |
| `consolidator.py` | Cold archive builder |
| `router.py` | Domain routing |

**Kernel runtime ownership (Track J):** `TriOctaMemoryKernel` remains a shared
math and configuration template. Observation-dependent runtime history is
per-agent through `KernelRuntimeContext`: `mon`, `disp_buffer`, and
`last_effective_scale`. Checkpoint schema v2 dual-writes the legacy
`corridor_monitor` field and the complete `kernel_runtime_context` field. G1
auto-canon governance and R1 live restore remain deferred.

**Core execution flows:**

1. **Ingest**: app.py -> fabric.ingest() -> kernel.process() (with character modulation) -> PhaseTimer.update() (duration tracking) -> router ranks domains -> motifs update -> memory_graph stores node (with phase/corridor durations in payload) -> optional drift check + gravity correction -> optional auto-proposal -> event-gated compression check (v2.1)
2. **Query**: app.py -> fabric.query() -> embed query -> search private + shared graphs -> deep memory fallback with spirit return enrichment (v2.1) -> score hits -> optional character context assembly (tier weighting + voice cues) -> optional bridge peeks
3. **Create Agent**: app.py -> fabric.create_agent() -> derive kernel modulation from seed -> init kernel state with character Omega -> plant character seed memories -> establish gravitational basin

### Layer 3: Interfaces (`app.py`, `sim/`, `tests/`)

- **FastAPI service** (`app.py`): REST API on port 8787
- **Simulation harness** (`sim/`): in-process multi-agent simulations, deterministic replay
- **Stress harness** (`torment_stress_harness/`): targeted stress tests
- **Tests** (`tests/`): smoke API, deterministic replay lock, emergent behavior regression

---

## 3. Character Identity System (v2.0)

The character system adds three capabilities to the existing fabric:

**Seed planting**: a natural-language character seed (3-5 sentences) is split into concept sentences, embedded, and stored as high-stability canon memories. These cluster into a seed motif — the deepest attractor basin in the character's memory landscape.

**Memory tiers**: memories are classified by half-life into core identity (365+ days, weight 1.43x), relational (7-364 days, weight 1.0x), and situational (under 7 days, weight 0.43x). Tier weights are applied during context assembly for queries.

**Drift protection**: periodic measurement of cosine distance between recent memory centroid and seed motif centroid. When sustained drift exceeds threshold, a gentle correction memory is emitted (purely additive). The coherence field's natural basin mechanics handle the rest.

**Kernel modulation**: `derive_kernel_modulation()` extracts warmth and structure scores from the seed text, computing per-character coupling strength (g), phase lock angle (theta_lock), and Omega initialization. This means different characters have genuinely different oscillator physics.

---

## 4. The Geometrical Model

The TriOcta kernel is built on several interconnected mathematical structures:

1. **Three coupled oscillators** on a Mexican-hat potential with Laplacian coupling
2. **D24 discrete phase scaffold** — 12-sector angular discretization
3. **Theta-ladder constants** — k-values from reciprocal asymmetry between pi, phi, e, sqrt3
4. **SU(3)-style basis** — (u, x, y) orthonormal basis from E8/TriOctagon geometry
5. **Chirality** — `J_eff = Im(O1 * conj(O2) * O3)` measures triad handedness
6. **Vesica compression** — `lambda_vp = 0.618` (golden ratio) as macro scaffold amplitude
7. **CP ridge windows** — angular windows in D24 space for emission/gating
8. **Corridor concept** — tangent alignment between torus XY motion and SU(3) uxy jumps
9. **Character modulation** (v2.0) — per-character g and theta_lock derived from seed text semantics

---

## 5. Memory System Design

**Workspaces** contain multiple agents' memories, separated by **domains** (research, engineering, operations, creative, meta).

**Agents** have private-write/shared-read access by default. Sharing requires proposals + governance.

**Character seeds** (v2.0) establish identity through memory basins rather than static prompts. Three tiers — core identity, relational, situational — emerge from half-life classification.

**Motifs** are embedding-space clusters (themes) that group related memories, control fragmentation, and provide stability scores.

**Identity anchors** are auto-generated when recurring motif involvement is detected — weighted in retrieval for continuity.

**Affect tagging** provides coarse emotional labels as tie-breakers on personal queries. **Mood drift** events capture affect changes over time.

**Coherence field** computes a structural map of motifs with reinforcement, tension, and curvature — classifying each motif as basin, ridge, or plateau.

**Symbolic state** layer assigns one of 8 symbols per memory event based on coherence field geometry — enabling resonance loop detection.

---

## 6. Event-Gated Memory Compression (v2.1)

Compression is the system's garbage collection — but it fires at discrete corridor transitions, not continuously. This preserves the dynamical meaning of memory formation.

**Trigger mechanism (`EventDetector`):** monitors tri_mod observables and fires on three events: `corridor_exit` (in_corridor True→False), `cycle_stage_change` (cycle stage transition), and `emergency_tear` (tearing_risk exceeds threshold while in corridor). The first call primes state and never triggers.

**Scoring (`CompressionScorer`):** two-channel scoring with J→Z temporal ordering.

- **J-score (60% weight)**: relational importance, inverted for compressibility. Uses strength, retrieval count (log-scale resistance capped at ~10 retrievals), and motif basin membership (basin members resist compression).
- **Z-score (40% weight)**: geometric organization. Uses coherence field alignment, motif stability, and memory age decay.
- **Duration resistance (v2.1)**: memories born during sustained corridors (phase_duration_steps or corridor_duration_steps ≥ 10) receive a 0.15 reduction to j_score, making them harder to compress. Sustained experience is structurally valuable.
- **Protected classes**: canon memories, core_identity tier, identity kind, and seed kind are never scored.

**Routing (`CompressionRouter`):** candidates are routed to one of two paths.

- **short_path**: default for low scores and young memories. Reduces strength in the core graph (fading).
- **long_path**: for high-scoring old memories. Exports to DeepMemoryStore for potential spirit return.
- **archive**: archive-class memories always go deep.

**Execution (`CompressionExecutor`):** walks the candidate list, executes short-path (strength reduction + `compressed` flag) or long-path (export to deep store + `exported` flag). Tracks history for debugging.

**Deep store (`DeepMemoryStore`):** JSONL-backed memory archive with shard-based embedding index. Supports export (from compression), recall by EID, and cosine-similarity query for spirit return retrieval. One store per agent.

**Configuration:**

| Variable | Default | Description |
|----------|---------|-------------|
| `TORMENT_COMPRESS_ENABLE` | 0 | Enable/disable compression |
| `TORMENT_COMPRESS_MIN_STEP` | 100 | Earliest step for compression |
| `TORMENT_COMPRESS_MIN_AGE` | 50 | Minimum memory age (steps) before eligible |
| `TORMENT_COMPRESS_DEEP_THRESHOLD` | 0.7 | Score threshold for long-path routing |
| `TORMENT_COMPRESS_TEAR_EMERGENCY` | 0.7 | Tearing risk threshold for emergency compression |

---

## 7. Spirit Return with Symbolic Resonance (v2.1)

When a query finds too few private hits, the system reaches into the deep memory store. But compressed memories don't simply reappear — they return through a symbolic resonance pipeline that gives them voice, warmth, and contextual meaning.

**Symbol interaction matrix:** 19 named rules mapping (birth_symbol, current_kernel_symbol) pairs to interaction types. Examples: `(◯, ◈) → "fulfilled"`, `(∿, ⊗) → "disrupted"`, `(◈, ⊘) → "letting_go"`. Unmapped same-symbol pairs → `"echo"`, different → `"contrast"`. Each rule carries a human-readable flavor text and a confidence boost.

**Three return modes:**

- **Resonance**: rarest mode. Fires when the deep memory's birth symbol matches the current kernel symbol and warmth is high. Present-tense, vivid, déjà vu quality. Strength = 0.6 × warmth.
- **Surfacing**: fires when the memory was compressed to core (short-path) and warmth is moderate. Present-tense, gentle. Strength = 0.4 × warmth.
- **Recollection**: default fallback. Past-tense, distilled. Strength = 0.1 × warmth.

**Warmup mechanics:** deep memories don't return at full intensity on first appearance. The WarmupTracker (JSONL-persisted per agent) manages warmth accumulation:

- **Warmth floor**: 0.2 (first appearance)
- **Increment**: +0.15 per retrieval within a 400-step window
- **Cap**: 1.0
- **Sustained warmth boost**: memories born during sustained corridors (≥10 steps) get a warmth floor of 0.3 instead of 0.2

**Enrichment pipeline:** `enrich_deep_memory_hit(deep_memory, current_symbol, warmup_state, compressed_in_core)` → `SpiritReturnMemory` → `inject_spirit_return_into_hit(spirit_mem)` → query hit dict with all spirit return fields.

**Character Prompt Layer integration:** spirit return hits flow into the retrieval assembler with voice cues:

- **Tier classification**: resonance + warm ≥ 0.5 → BLOCK_IDENTITY, surfacing + warm ≥ 0.3 → BLOCK_RELATIONAL, recollection → BLOCK_SITUATIONAL
- **Voice cues**: each return mode gets a voice marker in the assembled context (`[Voice: present-tense, vivid, déjà vu...]`, `[Voice: present-tense, gentle...]`, `[Voice: past-tense, distilled...]`)
- **Flavor text**: symbol interaction flavor injected as `[Flavor: ...]` marker
- **Warmth secondary sort**: within the same score, warmer spirit hits rank above cold ones
- **spirit_return_summary**: character context assembly includes a summary dict with total count, breakdown by mode, and average warmth

**Spirit reflection (Phase 7b):** after the LLM generates a response, the caller can invoke a post-response write-back loop that records which spirit return hits *actually influenced* the response. This creates a derived reflection artifact — NOT a copy of the original memory. Reflections record the *event of return* and its measured influence. See Section 7b below.

---

## 7b. Spirit Reflection — Post-Response Write-Back (v2.2)

When a spirit return memory *actually influences* a generated response, the system can record that event as a **derived reflection artifact**. This is the write-back half of the spirit return loop — Phase 7 reads from deep memory, Phase 7b records that the reading mattered.

**Core principle:** re-ingestion records the *event of return*, not the original memory again. Reflections are continuity artifacts, not resurrected originals.

**Four-stage pipeline (`spirit_reflection.py`):**

1. **Extract** (`extract_spirit_return_candidates`): pull spirit-return hits from assembled context blocks. Anything with `generation_depth >= 1` is excluded — reflections cannot spawn reflections.

2. **Score** (`score_spirit_return_influence`): conservative heuristic measuring how much the spirit return shaped the response. Weighted combination of lexical overlap (40%), concept alignment (30%), warmth bonus (15%), and resonance mode bonus (15%). Ultra-short candidates (< 5 tokens) are dampened to prevent false positives from incidental single-word matches.

3. **Build** (`build_spirit_reflection_event`): create a derived `SpiritReflectionEvent` that describes the return event. The summary says "A prior deep memory resurfaced in X mode via Y interaction and materially shaped the present reply" — never copies the original summary.

4. **Guard** (`should_store_reflection`): anti-echo checks in order: generation depth must be 1, influence must meet threshold (default 0.30), cooldown by `source_eid:mode:interaction` key (default 50 steps), duplicate suppression for same source + same step.

**Anti-echo protections (non-negotiable):**

- `eligible_for_spirit_return = False` — hardcoded in the dataclass, forced False on deserialization even if tampered on disk
- `generation_depth` capped at 1 — reflections cannot spawn reflections
- Cooldown by composite key — same return event cannot reflect again within 50 steps
- Influence threshold — weak influence is silently dropped
- Original deep memories are never mutated

**Storage:** `SpiritReflectionStore` persists to `data/agents/{agent_id}/spirit_reflections/reflections.jsonl`, completely separate from `deep_memory/`. Append-only JSONL with in-memory cache. Same CWE-22 path traversal guard as WarmupTracker.

**Wiring:** a dedicated `POST /workspace/{ws}/spirit-reflections/process` endpoint. The caller invokes it AFTER generating a response, passing the assembled context blocks and response text. If it fails, it returns `{"ok": false}` — never raises an HTTP exception, never affects the main response path.

**Diagnostics:** `GET /workspace/{ws}/spirit-reflections/status?agent_id=X` returns total count, unique sources, average influence, mode distribution, and last 10 reflections.

**Current limitations (v1):**

- Heuristic influence scoring is approximate — paraphrased influence is a known blind spot
- Reflections are pure observability artifacts — nothing reads them for decision-making yet
- No embedding index for reflections — they cannot be retrieved via vector similarity
- Cooldown is step-based, not time-based

**What reflections are NOT:** not identity mutation, not deep memory rewrite, not resurrection of originals, not a recursive feedback loop, not automatic. The caller explicitly invokes the endpoint; if they don't, nothing happens.

---

## 7c. Geometric Stance Modulation (v2.2)

The stance policy — which decides whether to respond, ask clarification, defer, or observe — can now be geometrically nudged by signals derived from the kernel's current state.

**GeometricStanceContext** (`thinking_models.py`): five normalized signals (0–1) harvested from kernel state:

| Signal | Source | Meaning |
|--------|--------|---------|
| coherence | phase coherence (coh) | how aligned the oscillator triad is |
| stability | 1 - tearing_risk | how stable the current corridor is |
| identity_lock | coherence × stability (clamped) | how firmly identity is held |
| ambiguity_tolerance | 1 - dispersion (clamped) | how much ambiguity the system can absorb |
| social_resonance | live social boost from retrieval | responsiveness to social context |

**Multiplicative modulation** (`stance_policy.py`): each geometric signal produces a bounded modifier in [0.85, 1.15] that scales specific stance thresholds:

- **Identity-defer modifier**: `0.85 + (0.6 × identity_lock + 0.4 × stability) × 0.30` — affects rule 4 (identity-sensitive defer threshold)
- **Ambiguity-clarify modifier**: `0.85 + (0.7 × ambiguity_tolerance + 0.3 × coherence) × 0.30` — affects rule 5 (clarification threshold)
- **Social-compactness modifier**: `0.85 + social_resonance × 0.30` — affects rules 6 and 7 (live-social silence and brevity thresholds)

**Key design property:** the modulation is *optional*. When `geometric_context` is None, all modifiers default to 1.0 and the stance policy behaves exactly as before. The modifiers *nudge* thresholds by at most ±15%, never override decisions.

**Empirical results:** out of 63 input×profile comparisons, 3 real stance shifts occurred (4.8% shift rate), all classified as GOOD. A fragile agent asks for clarification on vague input. A socially-open agent stays silent on ultra-short turns. Governance behavior was unchanged across all 8 profiles. See `docs/geometric_modulation_report.md` for the full analysis.

**Named profiles** for debug/testing: neutral, stable_locked, drifting_fragile, socially_open, ambiguity_tolerant (available via `GET /thinking/debug/geo_profiles`).

---

## 7d. Thinking Controller (v2.2)

The thinking controller (`thinking_controller.py`) provides a lightweight cognitive loop that sits between raw input and response generation. It is NOT the Agent Spine — it is a simpler, single-pass deliberation layer.

**Pipeline:** `think(workspace_id, agent_id, raw_input, ...)` →

1. **Frame** (`frame_task`): classify the input into a TaskFrame with mode, urgency, ambiguity, identity sensitivity, governance sensitivity
2. **Mode** (`choose_mode`): select cognitive mode — engineering, strategic, identity, live_social, or auto
3. **Memory plan** (`build_memory_plan`): decide what memory to retrieve and how
4. **Action** (`choose_action`): select action type — respond, ask clarification, use tool, governance review, propose share, archive, or no-op
5. **Draft** (`_draft_response`): generate a response draft based on mode and action
6. **Review** (`review`): self-review pass — softens identity overconfidence, trims live-social responses
7. **Stance** (`determine_stance`): optional stance policy with geometric modulation (see 7c above)

**Integration:** the thinking controller accepts `geometric_context: Optional[GeometricStanceContext]` and passes it through to the stance policy. ThinkingResult carries the full chain: frame → mode → plan → action → review → stance.

---

## 8. Phase-Cycle Time (v2.1)

Explicit step-counting of how long the system stays in a given phase or corridor. Lives in the fabric layer (not kernel) because `kernel.process()` doesn't take a step parameter.

**PhaseTimer** (one per agent): tracks `phase_entry_step`, `corridor_entry_step`, `current_cycle_stage`, and `current_in_corridor`. Updated on every ingest from tri_mod observables.

**Transitions detected:**

- **Phase change**: cycle_stage changes → resets phase_entry_step
- **Corridor entry**: in_corridor False→True → records corridor_entry_step
- **Corridor exit**: in_corridor True→False → clears corridor_entry_step, reports duration

**Duration outputs:** `phase_duration_steps` and `corridor_duration_steps` are injected into every memory's payload via extra_payload, making them available downstream to compression and spirit return.

**Downstream effects:**

1. **Compression resistance**: sustained memories (max duration ≥ 10) get j_score reduced by 0.15
2. **Spirit return warmth boost**: deep memories from sustained corridors get warmth floor 0.3 instead of 0.2
3. **Diagnostic visibility**: durations available in memory payloads for debugging and dashboards

---

## 9. Testing (v2.2)

The test suite covers 1725+ passing tests. Key suites by area:

| Suite | Tests | Scope |
|-------|-------|-------|
| `test_compression.py` | 42 | EventDetector, CompressionScorer, CompressionRouter, CompressionExecutor, DeepMemoryStore, try_compress integration |
| `test_spirit_return.py` | 53 | Symbol interaction matrix, return modes, warmth, WarmupTracker, enrichment pipeline, edge cases |
| `test_spirit_return_voice.py` | 34 | Tier classification, voice cues, block enrichment, sorting, character context assembly |
| `test_phase_timer.py` | 29 | PhaseTimer core, durations, transitions, serialization, compression resistance, warmth boost |
| `test_e2e_integration.py` | 23 | Full pipeline: ingest → kernel → PhaseTimer → compression → deep memory → spirit return → character prompt |
| `test_spirit_reflection.py` | 31 | Reflection pipeline: extraction, influence scoring, building, anti-echo guards, storage, end-to-end |
| `test_spirit_reflection_integration.py` | 12 | Fail-soft behavior, persistence + reload, tamper resistance, retrieval precedence unchanged |
| `test_stance_policy.py` | 15+ | Geometric modulation, modifier bounds, threshold shifts, no-geo baseline unchanged |
| `test_geometric_harvester.py` | 11 | GeometricStanceContext extraction from character state |
| `run_geo_compare.py` | (offline) | Comparison harness: 7 profiles × 9 inputs, shift detection, governance robustness check |
| Pre-existing (need fastapi/mcp) | 4 | Skipped in offline environments |

---

## 10. Stability Properties

The kernel demonstrates bounded attractor dynamics under periodic and random forcing. Z oscillates in [-0.21, +0.22], coherence in [0.75, 0.92]. Multipliers stay bounded (wm ~1.05-1.10, pm ~1.02-1.03). Corridor integrity maintained.

Character modulation (v2.0) operates within conservative bounds: g ±15% of 0.2, theta_lock ±0.1 rad of 0.244. All existing stability guarantees are preserved. Tested: warm characters (g=0.215) and analytical characters (g=0.185) both produce stable trajectories that diverge from each other as expected.

Compression (v2.1) preserves stability by design: it fires only at corridor transitions (never mid-corridor), protects canon/identity memories unconditionally, and routes long-lived memories to deep store rather than deleting them. Duration resistance ensures sustained corridor experience is structurally protected.

---

## 11. Configuration System

TORMENT is highly configurable via environment variables (`TORMENT_*` prefix). Key categories:

- **Embedding**: provider, model, device, dimension locking
- **Character** (v2.0): enable, drift window, correction threshold, gravity strength, check frequency
- **Continuity**: self-memory bonus, anchor bonus, thread window, affect matching
- **Mood**: drift detection, spiral dampening
- **Identity anchors**: count thresholds, gap requirements, quality refinement
- **Roles**: EMA update rate
- **Maintenance**: clone rate limiting, job retention, health audits
- **Profiles**: preset configurations via `/profiles` endpoint

---

## 12. Key Design Decisions

1. **Deterministic by default**: hash embeddings + fixed seeds enable exact replay for testing
2. **Bounded modulation**: all kernel multipliers are hard-clipped to narrow bands (0.90-1.10) — the kernel nudges, never overrides
3. **Separation of concerns**: kernel produces signals, fabric makes governance decisions — kernel never directly writes memory
4. **Domain isolation**: cross-domain contamination prevented by routing + bridge governance
5. **Canon governance**: shared memory requires proposal + multi-agent approval
6. **Corridor as metaphor**: tangent alignment maps geometric stability to memory formation quality
7. **Characters as attractors** (v2.0): identity emerges from memory landscape geometry, not hardcoded prompts
8. **Additive-only correction** (v2.0): gravity correction emits new memories, never rewrites existing ones
9. **Event-gated compression** (v2.1): compression fires at corridor transitions, never continuously — preserving the dynamical significance of corridor states
10. **Compression without deletion** (v2.1): short-path fades strength, long-path exports to deep store. No memory is ever truly deleted.
11. **Spirit return over retrieval** (v2.1): deep memories don't simply reappear — they return through a symbolic resonance pipeline with warmth, voice, and contextual meaning
12. **Trigger registry compliance** (v2.1): Dynamics → Observables → Triggers → Diagnostics. Reverse influence forbidden. Compression observes the kernel, never modifies it.
13. **Symbols stay hidden** (v2.1): raw symbol characters never reach the character layer — only interaction types and flavor text are exposed
14. **Reflections are derived, not duplicated** (v2.2): spirit reflection records the *event of return*, never copies the original memory. Reflections cannot feed back into spirit return (`eligible_for_spirit_return = False`, tamper-resistant on deserialization). Separate storage prevents contamination of deep memory.
15. **Geometric modulation nudges, never overrides** (v2.2): kernel-derived signals scale stance thresholds by at most ±15%. When geometric context is absent, behavior is identical to pre-modulation. The system is always safe to run without geometry.
16. **Post-response, not inline** (v2.2): spirit reflection runs as a separate endpoint after LLM response generation, not wired into the retrieval path. Fail-soft by design — if it breaks, the main path is unaffected.

---

## 13. File Quick Reference

```
torment_fabric/
  torment_service/
    app.py                  # FastAPI endpoints
    fabric.py               # Orchestrator/brainstem
    character.py            # Living character identity (v2.0) + spirit return summary (v2.1)
    memory_kernel.py        # Kernel bridge + character modulation
    memory_graph.py         # Persistence + vector search
    compression.py          # Event-gated compression — detector, scorer, router, executor (v2.1)
    deep_memory.py          # Long-path deep memory store + shard embeddings (v2.1)
    spirit_return.py        # Spirit return — symbol matrix, return modes, warmup (v2.1)
    spirit_reflection.py    # Spirit reflection — post-response write-back, anti-echo, derived artifacts (v2.2)
    phase_timer.py          # Phase/corridor duration tracking (v2.1)
    retrieval_assembler.py  # Context assembly — tiers, voice cues, token budgets (v2.1)
    thinking_controller.py  # Cognitive loop — framing, mode, memory plan, action, review, stance (v2.2)
    thinking_models.py      # Thinking data models — TaskFrame, GeometricStanceContext, ThinkingResult (v2.2)
    stance_policy.py        # Stance policy — geometric modulation of decision thresholds (v2.2)
    motifs.py               # Motif clustering
    coherence_field.py      # Structural epistemic layer
    embeddings.py           # Embedding backends
    symbols.py              # Hidden symbolic state (rewritten v2.0)
    resonance.py            # Symbolic resonance (rewritten v2.0)
    bridges.py              # Cross-domain links
    proposals.py            # Shared canon pipeline (fixed v2.0)
    roles.py                # Role inference
    affect.py               # Affect tagging
    conflicts.py            # Conflict detection
    identity.py             # Agent identity (extended v2.0)
    profiles.py             # Config profiles
    config_view.py          # Config UI view (extended v2.0)
    scoring.py              # Hit scoring
    summarizer.py           # Placeholder summarizer
    consolidator.py         # Memory consolidation
    router.py               # Domain routing
    domain_policies.py      # Per-domain knobs
    kernel/                 # Geometrical model engine
      model_core.py         # TriOcta phase-lock model
      definitions.py        # Canonical metric definitions
      phase_triad_sync.py   # Phase synchronization
      rsb_model.py          # Recursive Spectral Banding
      su3_basis.py          # SU(3) / E8 basis
      constants_selector.py # Theta-ladder constants
      identity_rules.py     # Cycle + identity mapping
      cp_windows.py         # CP ridge windows
      seed_emission.py      # Gap-gated emission
      latent_foreclosure.py # Option volume estimation
      diagnostics.py        # Diagnostic helpers
      physics_sampler.py    # Physics sampling
  sim/                      # Simulation harness
  tests/                    # Test suite (1725+ tests)
    test_compression.py     # Compression unit tests (42)
    test_spirit_return.py   # Spirit return unit tests (53)
    test_spirit_return_voice.py  # Voice cue / assembly tests (34)
    test_phase_timer.py     # Phase timer unit tests (29)
    test_e2e_integration.py # Full pipeline integration tests (23)
  torment_stress_harness/   # Stress tests
  docs/                     # Documentation
  tools/                    # Utility tools
```

---

## 14. Roadmap

### Completed (v2.1)

- ~~**Memory aging and compression**~~ ✓ — Event-gated compression with J→Z two-channel scoring (relational 60%, geometric 40%), two-path routing (short-path fade, long-path deep store export), protected classes (canon, identity, seeds never touched), duration resistance for sustained corridors, and spirit return with symbolic resonance (19-rule interaction matrix, three return modes, warmup mechanics, character voice cues). Full memory lifecycle from ingest → kernel → compression → deep memory → spirit return → character prompt.

### Completed (v2.2)

- ~~**Spirit reflection**~~ ✓ — Post-response write-back loop for spirit return. Records when returned deep memories actually influenced responses, as derived artifacts (not copies). Anti-echo protections: generation depth cap, cooldown by composite key, influence threshold, tamper-resistant `eligible_for_spirit_return = False`. Separate JSONL storage, fail-soft dedicated endpoint, read-only diagnostics. 43 tests (31 unit + 12 integration).

- ~~**Geometric stance modulation**~~ ✓ — Kernel-derived signals (coherence, stability, identity lock, ambiguity tolerance, social resonance) produce bounded modifiers [0.85, 1.15] that nudge stance policy thresholds. Optional layer — system behaves identically without it. Empirically validated: 3 real shifts out of 63 comparisons, all classified GOOD, governance unchanged. Named profiles for testing.

- ~~**Thinking controller**~~ ✓ — Lightweight cognitive loop: input framing → mode selection → memory plan → action decision → response draft → self-review → stance. Integrates geometric modulation when context is available.

### Next Up

- **Noise injection analysis** — Stress-testing kernel stability under adversarial/random forcing. The simulation harness (`sim/run_sim.py`) and stress-test infrastructure are already in place, so this plugs in naturally. The compression layer adds a new surface to test: how does noise affect compression decisions and spirit return quality? *Low-medium complexity.*

- ~~**Multi-agent coupling (hive-mind coordination)**~~ ✓ — Implemented: collective policy, shared memory governance, domain isolation, proposal/canon voting, agent coupling. 165 hivemind tests pass. See `HIVEMIND_GUIDE.md`.

- **Character seed evolution** — Migration between seed versions while preserving memory associations and deep memory references. The character layer (seed planting, drift protection, kernel modulation) is stable. The challenge is evolving a seed without breaking the gravitational basin or invalidating compressed memories that reference the old seed. *Medium complexity — touches character.py, deep_memory.py, needs backward compatibility handling.*

### Future

- **Distributed multi-node fabric** — Moving from a single FastAPI instance to networked nodes. Requires rethinking state sync (agent_states, motifs, phase timers, warmup trackers, deep stores), consistency guarantees, and latency. The compression/deep memory layer adds state that needs distributed coordination. *High complexity, significant restructuring.*

- **UI dashboard** — Pure addition, no restructuring. Could be a simple FastAPI static page reading from existing endpoints (`/health`, `/config`, `/workspace/{id}/spirit-return/status`). Now has richer data to display: compression activity, spirit return events, phase-cycle timing, warmth levels, deep memory counts. *Low complexity.*

- **Stronger contradiction detection** — Currently heuristic negation matching in `proposals.py`. Improving to embeddings-based semantic comparison. With real embeddings enabled, the infrastructure is already there — this is mostly scoring logic. *Low-medium complexity.*

- **Weight of authority for canon voting** — Small extension to existing voting logic in proposals. Could factor in agent identity state, corridor history, or compression survival as trust signals. *Low complexity.*
