# TORMENT Memory Fabric — v2.4.0

A dynamical **memory substrate** for AI agents, built around a TriOcta coupled-oscillator kernel that stabilizes memory formation, prevents drift, and maintains identity over long horizons.

Designed for local AI companions, multi-agent hive-minds (200+ bots), persistent identity experiments, and research environments.

TORMENT does not control personality. It stores and retrieves context in a stable way — and provides a living character identity layer that lets personality emerge from memory rather than static prompts, with a complete memory lifecycle through event-gated compression, spirit return, and collective resonance coupling.

---

## What's New in v2.4.0 — Memory Lifecycle & Agent Spine

This release closes the gap between "the hive mind works" and "the memory system is production-healthy." Extensive stress testing revealed that memories grew without bound under steady-state operation — compression never fired because the geometric triggers (corridor exits, cycle stage changes) require phase dynamics that don't occur during calm input streams. v2.4.0 fixes this with a complete memory lifecycle overhaul, formalizes the Agent Spine cognition pipeline, and adds unified observability.

**Adaptive Coherence** — replaced fixed DISP_SCALE with a self-tuning system. `effective_scale = k * (mean + std)` over a rolling window, with k=2.0 as the dimensionless sensitivity multiplier. Works identically across HashEmbedding and STEmbedding with no per-embedder tuning. The old fixed values (7e-4, 0.10) are gone.

**Duplicate Suppression** (`fabric.py`) — pre-ingest similarity check (cosine ≥ 0.92, same-agent only) prevents redundant memories from accumulating. Duplicates are reinforced instead of duplicated: `min(0.98, old_strength + (1 - old_strength) * 0.3)`. Diagnostic showed 19% dedup rate across 300 ingests.

**Half-Life Decay** — exponential decay `2^(-age/half_life)` applied at query time. Memories naturally fade unless reinforced. Full clock reset on reinforcement via `last_reinforced_ts`. Ranking floor of 0.03 prevents ghost memories from polluting results.

**Fallback Compression Triggers** (`compression.py`) — two new triggers supplement the geometric ones: count-overflow fires when an agent exceeds 400 memories, periodic fires every 200 steps. Both respect a 50-step cooldown. Verified: 30 compression events across 120 single-agent steps in isolation testing.

**Retention Tiers** — five-tier classification (Protected → Identity → Relational → Situational → Echo) with tier-specific scoring multipliers, routing decisions, and execution behavior. Protected memories are never compressed. Identity tier always exports to deep store. Echo tier gets aggressive 0.4x fade. Classification is derived at runtime from existing payload fields — no migration required.

**Hard Memory Cap** — last-resort safety net at 10,000 memories per agent, force-compressing down to 8,000. Overrides minimum age requirements in emergency mode.

**Agent Spine Documentation** — the cognition pipeline (`cognition/`, `roles/`, `schemas/`) was found to be fully implemented: 4 deterministic roles (Interpreter, Engineer, Skeptic, Archivist), 3 aperture types, 7 hard invariants (A–G), 2,844 lines of test coverage, and a working `POST /cognition/run` endpoint. Comprehensive architecture overview written in `docs/AGENT_SPINE_OVERVIEW.md`, including the Spine ↔ Hive Mind interaction contract.

**Unified Observability** (`GET /debug/metrics`) — single endpoint aggregating feature flags, per-agent memory/compression/character state, per-domain motif/coherence/proposal stats, and collective packet/convergence counts. Reads only RAM — cheap to poll. All existing per-component debug endpoints preserved.

**1,027 Tests** — up from 663. Full coverage of decay, dedup, fallback triggers, retention tiers, hard cap, Agent Spine acceptance scenarios, and observability.

---

## What's New in v2.3.0 — Hivemind Phase D (Collective Governance)

**Memory Governance System** (`governance.py`) — centralized resolver for per-memory consent and sharing flags. Source protection flags (protected, non_shareable, collective_export_blocked) control what leaves private memory. Derived handling flags (collective_reingest_blocked, decay_accelerated) govern synthetic material after arrival. Partial updates with full audit trail, workspace-level JSONL audit log.

**7-Gate Collective Policy Engine** (`collective_policy.py`) — gatekeeper between convergence detection and echo re-ingestion. Gates: confidence threshold (0.60), agent opt-in, domain exact match, deduplication, rate limiting (3/hour), drift budget / identity compatibility, eligible. Conservative by design — slightly annoying to trigger is a feature.

**Echo Re-Ingestion** (`fabric.reingest_convergence()`) — bridges detection and influence. Loads convergence events, runs them through the policy engine, synthesizes compact echo summaries, and ingests them as low-amplitude memories (0.25x strength, 0.40x hard cap). Echoes are terminal: double-blocked governance (can't re-emit or re-echo), provenance-marked, and retrieval-discounted (0.5x weight).

**Collective Proposal Bridge** (`collective_proposals.py`) — automatically drafts share proposals when convergence events are persistent and high-confidence. Tracks domain+motif patterns over time, requires persistence (2+ events in 2 hours) before proposing. Proposals are always pending for operator review — never auto-approved.

**5 Design Invariants** enforced across all modules: (1) Protected memories never weakened automatically, (2) Non-shareable/export-blocked memories never emit, (3) Collective echoes are terminal by default, (4) Echoes are influences not autobiography, (5) Collective provenance cannot outrank seed/canon identity.

**663 Tests** — 194 new tests across governance, policy, reingest, proposals, and cross-phase integration. Full 5-invariant verification suite.

---

## What's New in v2.2.0 — Crystal Attunement (SRG)

**Symbolic Resonant Geometry** (`srg_engine.py`) — living memory geometry derived from the SRG paper's recursive operator mathematics. Each memory carries a dual-field state: Resonance R (what it IS — golden-tower frequency bands) and Compression L (WHO it is — breathing oscillation). The coupling constant `gamma_srg = zeta(3)/(pi*e*phi) ~ 0.08699` emerges from the math and governs all SRG dynamics.

**Golden Frequency Tower** — memories occupy phi-spaced frequency bands (`omega_n = omega_0 * phi^n`) with 100% band survival. Same-band memories get 8% retrieval boost. Memories naturally cluster by resonant similarity.

**Heartbeat Classes** — discrete symmetry breaking produces Class A (slow, deep) and Class B (fast, active) breathing. Class A memories get a 3% stability bonus. The heartbeat classification persists through the memory lifecycle.

**Center Crystals** — when a memory's breathing compression locks to the SRG coupling frequency, it becomes a "crystal" — a maximally stable identity anchor. Crystal memories get 5% retrieval boost and resist compression.

**Collision Physics** — when similar memories merge (cosine similarity >= 0.75), SRG collision dynamics fire: rhythm synchronizes, amplitude preserves identity, merger timing determines equilibrium. Breathing evolution occurs on retrieval — active memories are living fields.

**Feature-flag gated** — `TORMENT_SRG_ENABLE=1` activates the layer. Zero overhead when off.

---

## What's New in v2.2.1 — Hivemind Foundation (Phases A-C)

**Collective Data Contracts** (`collective_models.py`) — ResonancePacket (per-ingest snapshot for the collective field), ConvergenceEvent (multi-agent alignment record), CharacterSelfState (agent identity health view), MemoryGovernanceFlags (per-memory consent controls).

**Character Self-Awareness API** — `GET /agent/{id}/self-state` returns drift score, seed basin geometry, memory tier counts, phase timing, and SRG attunement at a glance.

**Collective Field** (`collective_field.py`) — workspace-level packet store with convergence detection. Cosine similarity >= 0.72 triggers events, composite confidence from semantic (50%) + phase (15%) + symbol (15%) + motif (20%). JSONL persistence, cooldown dedup.

**Packet Emission** — every ingest above coherence 0.15 emits a ResonancePacket into the workspace collective field. Feature-flag gated: `TORMENT_HIVEMIND_ENABLE=1`.

---

## What's New in v2.1.1

**Character Forge** (`start/torment_character_creator.html`) — a zero-code HTML tool that walks new users through creating a TORMENT character. Generates all setup commands, env config (Linux + Windows), a complete Python chat script with auto-setup, and a system prompt template. Supports Claude, OpenAI, Ollama, and custom LLM endpoints.

**Single-Agent Domain Fix** — new workspaces now default to a single `personal` domain instead of creating all 5 hive-mind domains. Companion characters no longer waste 4x storage on unused domain infrastructure. Multi-agent setups can still request specific domains explicitly.

**Personal Domain Policy** — relaxed governance for single-agent use: `shared_min_distinct_agents: 1`, higher proposal rates, auto-merge motifs enabled. No multi-agent approval overhead when running a solo companion.

---

## What's New in v2.1

**Event-Gated Memory Compression** — memories compress at discrete corridor transitions (not continuously). J→Z two-channel scoring (relational 60%, geometric 40%) with two-path routing: short-path fades, long-path exports to deep store. Protected classes (canon, identity, seeds) are never touched. Memories born during sustained corridors resist compression. See `docs/PROJECT_OVERVIEW.md` §6.

**Spirit Return with Symbolic Resonance** — compressed memories return through a 19-rule symbol interaction matrix with three modes: resonance (rare, vivid), surfacing (gentle, present-tense), and recollection (past-tense, distilled). Warmup mechanics prevent cold returns — warmth accumulates gradually with repeated retrieval. See `docs/PROJECT_OVERVIEW.md` §7.

**Character Prompt Layer** — spirit return hits flow into the character context with voice cues, flavor text, and tier classification. The character doesn't just recall memories — it recognizes them. See `docs/CHARACTER_SYSTEM.md`.

**Phase-Cycle Time** — explicit duration tracking of phases and corridors feeds into compression resistance and warmth boost. Sustained experience is structurally protected.

**185 Tests** — full coverage from unit through integration. The e2e suite walks a synthetic conversation through the entire pipeline: ingest → kernel → compression → deep memory → spirit return → character prompt.

## What Was New in v2.0

**Living Character System** — characters are gravitational basins in memory space. A minimal seed establishes the deepest attractor. Memory does the work. Drift protection keeps the character centered.

**Kernel-Character Unification** — character seeds modulate TriOcta oscillator physics. Different characters produce different memory dynamics from the same input.

**Symbolic Code Overhaul** — symbols.py and resonance.py rewritten with geometric projection and cycle detection.

---

## Docs

| Document | Description |
|----------|-------------|
| `start/torment_character_creator.html` | **Character Forge** — zero-code character setup tool |
| `docs/QUICKSTART.md` | 5-minute setup guide |
| `docs/GUIDE.md` | Detailed system guide |
| `docs/CHARACTER_SYSTEM.md` | Living character identity + spirit return voice layer |
| `docs/HIVEMIND_GUIDE.md` | Multi-agent hivemind setup, convergence, echo re-ingestion |
| `docs/COMPANION_CONTRACT.md` | Philosophy — what TORMENT does and does not do |
| `docs/TUNING.md` | Configuration tuning (includes compression + spirit return) |
| `docs/TROUBLESHOOTING.md` | Operational fixes (includes compression + spirit return) |
| `docs/MEMORY_KERNEL_ARCHITECTURE.md` | Internal kernel design + compression gating + warmup mechanics |
| `docs/AGENT_SPINE_OVERVIEW.md` | Agent Spine cognition pipeline — architecture, invariants, data contracts |
| `docs/MEMORY_HEALTH_REPORT.md` | Memory growth analysis and lifecycle tuning findings |
| `docs/ROADMAP_post_hivemind_milestone.md` | Post-hivemind development roadmap and priorities |
| `docs/PROJECT_OVERVIEW.md` | Comprehensive architecture reference |

---

## Run

```bash
python -m pip install -r requirements.txt
bash run.sh
```

Service: `http://127.0.0.1:8787`

## Tests

```bash
python -m pip install -r requirements.txt
make test

# Or run directly with unittest (no pytest required):
python -m unittest discover -s tests -v

# Ship gate (compile + tests + deterministic sim replay)
make verify
```

---

## Architecture

TORMENT has five layers:

**Layer 1 — The Kernel** (`torment_service/kernel/`): a TriOcta phase-lock model (three coupled oscillators on Mexican-hat potentials with D24 phase scaffold). Produces stability signals — coherence, corridor alignment, identity state — that govern memory behavior. Accepts per-character modulation of coupling strength and phase angles.

**Layer 2 — The Fabric** (`torment_service/fabric.py` + modules): governance and orchestration. Routes observations through the kernel, manages memory graphs, motif registries, coherence fields, proposals, bridges, phase-cycle timing, and the character identity layer.

**Layer 3 — Compression + Spirit Return** (`compression.py`, `deep_memory.py`, `spirit_return.py`, `phase_timer.py`, `retrieval_assembler.py`): event-gated memory lifecycle. Compression fires at corridor transitions, deep memories return through symbolic resonance with warmth and voice cues.

**Layer 4 — Collective Hivemind** (`collective_field.py`, `collective_policy.py`, `collective_proposals.py`, `governance.py`): workspace-level resonance coupling between agents. Convergence detection, 7-gate policy engine, echo re-ingestion with terminal governance, and a proposal bridge for persistent patterns. SRG Crystal Attunement (`srg_engine.py`) adds living memory geometry with golden-tower bands, heartbeats, breathing compression, and collision physics.

**Layer 5 — Interfaces** (`app.py`, `sim/`, `tests/`): FastAPI REST service, simulation harness, stress tests, 1,027-test suite.

---

## Key Endpoints

**Health & config:**
- `GET /health`
- `GET /profiles` — preset definitions
- `GET /config` — effective configuration view
- `GET /embedder/check` — embedding diagnostic

**Workspace:**
- `POST /workspace/create` `{ workspace_id, domains? }` — defaults to `["personal"]`; pass explicit list for multi-agent
- `GET /workspace/{workspace_id}/domains`
- `POST /workspace/clone` `{ source_workspace_id, target_workspace_id, reembed?, reembed_mode? }`
- `POST /workspace/maintenance` `{ workspace_id, mode }` — scan/repair/compact

**Agents:**
- `POST /agent/create` `{ workspace_id, agent_id, seed? }` — seed can include `seed_text` and `seed_id` for character layer
- `GET /agent/{agent_id}/identity?workspace_id=...`
- `GET /agent/{agent_id}/roles?workspace_id=...`
- `POST /agent/ingest` `{ workspace_id, agent_id, text, step, domain_id?, scope? }`
- `POST /agent/query` `{ workspace_id, agent_id, query, top_k, continuity_debug? }` — returns `character_context` when character is active
- `POST /agent/feedback` `{ workspace_id, agent_id, retrieved_ids, ... }`

**Compression & spirit return (v2.1):**
- `GET /workspace/{workspace_id}/spirit-return/status` — spirit return status

**Proposals & governance:**
- `GET /workspace/{workspace_id}/domain/{domain_id}/proposals`
- `POST /workspace/domain/proposals/decide`

**Memory governance (v2.3):**
- `POST /memory/governance/set` `{ workspace_id, agent_id, eid, flags, actor?, source? }` — partial flag update with audit
- `GET /memory/governance/get` `{ workspace_id, agent_id, eid }` — read current governance flags
- `GET /workspace/{workspace_id}/governance/audit` — workspace-level governance audit log

**Observability (v2.4):**
- `GET /debug/metrics?workspace_id=...&agent_id=...` — unified metrics (flags, agents, domains, collective)

**Collective hivemind (v2.2.1+):**
- `GET /workspace/{workspace_id}/collective/status` — field summary (packets, events, agents, domains)
- `GET /workspace/{workspace_id}/collective/packets` — recent resonance packets (filterable by agent/domain)
- `GET /workspace/{workspace_id}/collective/events` — convergence events
- `GET /workspace/{workspace_id}/collective/events/{event_id}` — single event detail
- `POST /workspace/{workspace_id}/collective/reingest` `{ agent_id, event_id, echo_strength_override? }` — manual echo re-ingestion through 7-gate policy
- `GET /workspace/{workspace_id}/collective/proposals/status` — proposal bridge telemetry

---

## Embeddings

TORMENT defaults to deterministic hash embeddings for replay and testing. For production, enable real embeddings:

**SentenceTransformers (recommended):**
```bash
pip install sentence-transformers
export TORMENT_EMBED_PROVIDER=st
export TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
export TORMENT_EMBED_DEVICE=cpu
```

**Ollama:**
```bash
export TORMENT_EMBED_PROVIDER=ollama
export TORMENT_EMBED_MODEL=nomic-embed-text
export TORMENT_OLLAMA_URL=http://127.0.0.1:11434
```

Each workspace locks its embedding dimension. Switching embedders requires cloning to a new workspace.

---

## Enable Feature Flags

```bash
# Compression (v2.1) — event-gated memory lifecycle
export TORMENT_COMPRESS_ENABLE=1

# SRG Crystal Attunement (v2.2) — living memory geometry
export TORMENT_SRG_ENABLE=1

# Hivemind (v2.2.1+) — collective resonance coupling
export TORMENT_HIVEMIND_ENABLE=1
```

Each layer is independently flag-gated. Zero overhead when off. They compose naturally: compression provides the memory lifecycle, SRG adds geometric memory physics, and hivemind enables multi-agent resonance coupling on top.

---

## Character System

Create agents with a character seed to activate living identity:

```bash
curl -X POST http://127.0.0.1:8787/agent/create \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "ws1",
    "agent_id": "aria",
    "seed": {
      "seed_text": "Aria is warm and curious, with a deep bond to her companion. She approaches problems with playful enthusiasm and genuine empathy.",
      "seed_id": "aria_v1"
    }
  }'
```

This automatically plants seed memories, establishes a gravitational basin, and tunes the kernel physics to match the character. See `docs/CHARACTER_SYSTEM.md` for the full guide.

---

## Simulation

```bash
python -m sim.run_sim --workspace sim-ws --agents 50 --steps 400 --scenario mixed --out sim_out
```

Scenarios: `research`, `ops`, `creative`, `mixed`, `collaborative_mixed_200`.

---

## Defaults

- New workspaces default to a single `personal` domain (companion use). For multi-agent hive-mind, pass `"domains": ["research", "engineering", "operations", "creative", "meta"]` to workspace creation.
- Agents: private-write, shared-read (shared-write requires proposal/governance)
- Character layer: enabled by default when `seed_text` is provided
- Compression: disabled by default (`TORMENT_COMPRESS_ENABLE=0`), enable for full lifecycle
- SRG Crystal Attunement: disabled by default (`TORMENT_SRG_ENABLE=0`), enable for living memory geometry
- Hivemind: disabled by default (`TORMENT_HIVEMIND_ENABLE=0`), enable for multi-agent resonance coupling
- Collective echoes: 0.25x strength (0.40x hard cap), 0.5x retrieval weight, terminal by default
- Kernel modulation: automatic when character is active

---

## Notes

- If you have a real summarizer/embedder, pass `supplied_summary` and/or `supplied_embedding` to `/agent/ingest`
- Otherwise TORMENT uses deterministic placeholders (hash-embed + simple summary fallback)
- Character seeds work best with real embeddings — hash embeddings produce orthogonal vectors so seed concepts don't cluster naturally, but the system still functions correctly
- The `data/` directory contains workspace state and should not be committed to version control
