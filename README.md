# TORMENT Memory Fabric — v2.4.3

**TORMENT** is a governed memory and identity engine for building persistent AI characters and agents.

Unlike typical agent stacks that rely on prompts, tool wrappers, and loose memory, TORMENT gives characters a structured internal life:
- **memory that persists** — geometric kernel with half-life decay, reinforcement, and event-gated compression
- **identity that resists drift** — character basins, seed gravity, and drift monitoring
- **governed decisions through the Agent Spine** — dual-lane trust enforcement, auto-escalation, and structured audit trails
- **multi-agent and hivemind support** — collective resonance, convergence detection, 7-gate policy engine
- **MCP integration for extension and tooling** — governed MCP server with exposure tiers and incident logging

Built for **modders, developers, and experimental character systems**, TORMENT is designed to be forked, extended, and shaped into companions, NPCs, worlds, and multi-agent projects.

If you want AI characters that feel more consistent, more alive, and more structurally grounded than standard prompt-based systems, this is the engine.

Built around a TriOcta coupled-oscillator kernel that stabilizes memory formation, prevents drift, and maintains identity over long horizons. Designed for local AI companions, multi-agent hive-minds (200+ bots), persistent identity experiments, and research environments.

The TriOctagon toy model at the heart of this system has its own standalone research archive with full mathematical diagnostics across 12 versioned releases — each version dives deep into the coupled-oscillator math, phase-space analysis, and stability proofs that underpin the kernel's behavior. The complete diagnostic series is available on Zenodo: [TriOctagon Toy Model — Full Diagnostics (12 versions)](https://zenodo.org/records/18215874).

---

## What's New in v2.4.3 — Tool-Result Memory Lane

TORMENT can now remember externally obtained tool outputs as governed memory artifacts without crossing into tool execution or automation.

**Tool-Result Ingest** (`spine.py`, `app.py`) — new Spine-governed write operation `tool_result_ingest` with dedicated `POST /tool/ingest` endpoint. External tool outputs (API responses, search results, sensor data) are stored as provenance-tagged private memories via `ProvenanceV1.for_tool_result()`. Routed through the fast path at trust tier 0.6, exposure tier guarded. The Spine governs the write; no tool execution or dispatch occurs.

**Tool-Result Retrieval Semantics** (`fabric.py`) — three provenance-aware scoring changes in the retrieval pipeline. (1) Tool-result memories receive a configurable retrieval discount (default 0.85x, env `TORMENT_TOOL_RESULT_RETRIEVAL_DISCOUNT`) so external observations don't outrank the agent's experiential memories. (2) Self-thread and thread-window continuity bonuses are excluded for tool-result hits — these bonuses exist for conversational continuity, not ingested observations. (3) Every returned hit now carries `provenance_type` and `provenance_tool_name` at top level so downstream consumers can see provenance without payload parsing.

**Provenance Normalization** — collective provenance writes now use `ProvenanceV1.for_collective_echo()` instead of bare `"collective"` strings. All three comparison sites (hivemind gate, retrieval discount, compression classifier) updated with backward-compatible checks that accept both legacy strings and ProvenanceV1 dicts. Debug endpoint separator bug fixed (`"::"` → `"/"` in agent key construction).

**Tests** — 41 tests in `test_tool_result_ingest.py` covering ingest governance, provenance round-trip, retrieval semantics (discount, continuity bonus exclusion, provenance badge), trust enforcement, malformed payloads, and provenance factory behavior.

**Docs** — `MCP_CAPABILITY_BOUNDARY.md` updated with tool-result ingest section and doctrine. `SPINE_CONTRACT.md` updated with operation table entry, exposure matrix row, result codes, and design rule 8. `TOOL_RESULT_RETRIEVAL_SEMANTICS.md` added with full audit of the retrieval pipeline and policy rationale.

**Doctrine line:** *"TORMENT may remember what tools returned before it is ever allowed to decide what tools to run."*

---

## What's New in v2.4.2 — Provenance, Recursion Safety & Capability Boundary

This release adds provenance tracking to every memory write, validates recursion safety for archivist write-back, fixes the cognition/drift path, and formally defines the MCP capability boundary.

**Provenance System** (`provenance_v1.py`) — every `fabric.ingest()` call now attaches structured provenance metadata: `schema_version`, `source_type`, `source_role`, `write_path`, `parent_eids`, `created_at_step`, `created_at_ts`. New debug endpoint `GET /debug/provenance` exposes stored provenance for inspection. This is the foundation for all future governance — the system can now distinguish user-origin memories from derived or archivist-generated material.

**Recursion Safety Policy** (`RECURSION_SAFETY_POLICY_v2.4.x.md`, implemented in `cognition/pipeline.py`) — six rules (A–F) that prevent archivist write-back from creating self-reinforcing loops. Live-validated: second-pass write-back is correctly blocked with `archivist_parent_blocked` when it detects archivist-origin parent memories. Safe parent classes defined: `user_input`, `tool_result`, `memory` (migrated). Archivist write-back remains gated behind `TORMENT_ARCHIVIST_WRITEBACK=0` but the recursion guard is now proven to work.

**Cognition/Drift Bugfixes** (`cognition/drift.py`) — two shape mismatches fixed in the live drift adapter. The drift check was accessing `ident.graph`, `ident.character_seed`, and `ident.character_state` on `AgentIdentity`, but `AgentIdentity` is a lightweight dataclass. Fixed to use `fabric_instance.private_graphs`, `character_store.load_seed()`, and `character_store.load_state()` — the same patterns used throughout `fabric.py`. Also fixed `ws.motif_registry` (doesn't exist) to `ws.motif_regs[domain]` (the actual per-domain dict). The `/cognition/run` endpoint now completes with a structured drift report instead of falling through to the error fallback.

**Memory Plan Validation** — A/B tested advisory ON vs OFF across 5 query types (identity, live/social, technical, provenance, stable design). Result: advisory does not break retrieval rankings or lose identity-anchor memories. Passes "do no harm" but not yet "earns influence." Memory Plan remains gated behind `TORMENT_THINKING_ADVISORY=0`.

**MCP Capability Boundary** (`docs/MCP_CAPABILITY_BOUNDARY.md`) — formal documentation of what TORMENT's MCP layer does and does not do. TORMENT MCP is a governed memory interface, not an action execution system. No tool dispatch, no autonomous loops, no external API calling. The boundary between epistemology (memory, reasoning, provenance) and capability (actions, tools, execution) is intentional and enforced.

**Doctrine** (`DOCTRINE_v2.4.x.md`) — 12 architectural principles codified. Key rules: "automatic is allowed before autonomous," "provenance is a hard boundary," "advisory logic must earn influence," "retrieval quality beats feature sprawl."

---

## What's New in v2.4.1 — Thinking Layer, Stance Policy & Live Agent

This release adds a pre-cognition thinking layer, a geometric stance policy, and the first working live agent deployment (voice-active characters on X Spaces).

**Thinking Controller** (`thinking_controller.py`) — first-pass cognition controller that runs before the Spine dispatches. Heuristic-first, deterministic, no ML calls. Five-stage pipeline: task framing (urgency, ambiguity, governance/identity sensitivity, tool needs, live-social context), cognitive mode selection (7 modes: Fast, Retrieval, Reflective, Tool, Governed, Identity-Sensitive, Live-Social), memory plan construction (lane-specific top_k, weights, token budgets, safety constraints), action routing (Answer, Governance Review, Use Tool, Ask Clarification, Propose Share, Create Archive Note, No-Op), and self-review (identity overconfidence softening, live-social trimming, governance mismatch blocking).

**Stance Policy** (`stance_policy.py`) — optional participation decision layer on top of thinking. Determines *whether and how* a character should engage. Advisory only — never blocks Spine execution. Only active when `TORMENT_CONTEXTUAL_ABSTENTION=1`. Geometric kernel state (coherence, stability, identity lock, ambiguity tolerance, social resonance) modulates thresholds within bounded ±15% bands.

**Geometric Stance Context** (`thinking_models.py`) — normalized 0–1 interface derived from raw kernel internals. Five signals: coherence (phase synchrony), stability (basin health vs tearing risk), identity_lock (drift distance from seed), ambiguity_tolerance (capacity to absorb uncertainty), social_resonance (willingness to engage socially). Designed so the stance layer never touches raw kernel variables directly.

**Thinking Advisory Sidecar** (in `spine.py`) — the thinking controller runs as a non-authoritative observer inside the Spine. Compares what the Spine routes (by operation type + trust) against what the thinking layer recommends (by content heuristics). Alignment records tracked in a ring buffer with divergence notes. Feature-gated: `TORMENT_THINKING_ADVISORY=1`.

**Live Agent Pipeline** (`live_agent/`) — first working deployment of TORMENT characters as live voice agents. Whisper STT → TORMENT memory retrieval → local Qwen 3.5 4B base model generation → Voicebox/edge-tts speech synthesis. Two characters deployed: Limn (curious, bold, roasts trolls) and Bibs (witty, sharp, BS-buster). Four modes: text, voice (mic), listen (system audio transcript), space (X Spaces with loopback capture + VB-CABLE routing). Turn-taking architecture for continuous audio environments. TTS benchmark tooling for engine comparison.

**Security Hardening** — 40+ CodeQL alerts resolved across the codebase. Path traversal protection (CWE-22) in checkpoint, deep_memory, compression, collective_field, collective_proposals, bridges, archive_memory, embedding_store, governance, memory_graph, motifs, spirit_return. Log injection prevention. Stack trace exposure fixes. Empty-except audit (debug logging added to all silent catches).

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

**1,266+ Tests** — up from 663. Full coverage of decay, dedup, fallback triggers, retention tiers, hard cap, Agent Spine acceptance scenarios, observability, incident log, MCP server, Spine governance, and real-host hardening (weird inputs, missing context, tier blocking).

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
| `docs/SPINE_CONTRACT.md` | Spine invariants, trust tiers, decision codes, exposure tiers |
| `docs/TORMENT_Architectural_Audit_Spirit_Return_Voice.docx` | Full architectural audit — spirit return, voice systems, identity persistence |
| `docs/MCP_README.md` | MCP server setup, configuration, and Claude Desktop integration |
| `docs/MCP_EXPANSION_GUIDE.md` | Adding new MCP tools — worked example, decision matrix, checklist |
| `docs/MCP_CAPABILITY_BOUNDARY.md` | MCP capability boundary — what TORMENT MCP does and does not do |
| `docs/MEMORY_HEALTH_REPORT.md` | Memory growth analysis and lifecycle tuning findings |
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

TORMENT has seven layers:

**Layer 1 — The Kernel** (`torment_service/kernel/`): a TriOcta phase-lock model (three coupled oscillators on Mexican-hat potentials with D24 phase scaffold). Produces stability signals — coherence, corridor alignment, identity state — that govern memory behavior. Accepts per-character modulation of coupling strength and phase angles.

**Layer 2 — The Fabric** (`torment_service/fabric.py` + modules): orchestration and state management. Routes observations through the kernel, manages memory graphs, motif registries, coherence fields, proposals, bridges, phase-cycle timing, and the character identity layer.

**Layer 3 — Compression + Spirit Return** (`compression.py`, `deep_memory.py`, `spirit_return.py`, `phase_timer.py`, `retrieval_assembler.py`): event-gated memory lifecycle. Compression fires at corridor transitions, deep memories return through symbolic resonance with warmth and voice cues.

**Layer 4 — Collective Hivemind** (`collective_field.py`, `collective_policy.py`, `collective_proposals.py`, `governance.py`): workspace-level resonance coupling between agents. Convergence detection, 7-gate policy engine, echo re-ingestion with terminal governance, and a proposal bridge for persistent patterns. SRG Crystal Attunement (`srg_engine.py`) adds living memory geometry with golden-tower bands, heartbeats, breathing compression, and collision physics.

**Layer 5 — The Agent Spine** (`spine.py`, `request_context.py`, `incident_log.py`): governed authority layer between external callers and the Fabric. Dual-lane routing (fast path for structured ops, full path for 4-role cognition pipeline). Trust-tier enforcement, auto-escalation from fast→full on identity-sensitive content, structured decision/result codes, and a ring-buffer incident log for observability. MCP and HTTP never touch Fabric directly — everything flows through the Spine.

**Layer 6 — Thinking + Stance** (`thinking_controller.py`, `thinking_models.py`, `stance_policy.py`): pre-cognition layer that runs as an advisory sidecar inside the Spine. Frames incoming input (urgency, ambiguity, governance/identity sensitivity), selects cognitive mode (7 modes), builds a lane-specific memory retrieval plan, chooses an action route, and self-reviews. The stance policy adds geometric modulation — kernel-derived signals (coherence, stability, identity lock) nudge participation thresholds within bounded ±15% bands. Purely observational: alignment between Spine routing and thinking recommendations is tracked but thinking never overrides execution.

**Layer 7 — Interfaces** (`app.py`, `mcp_server.py`, `sim/`, `tests/`, `../live_agent/`): FastAPI REST service, MCP stdio server with exposure-tier policy, simulation harness, stress tests, 1,200+ test suite, and a live voice agent pipeline (Whisper STT → TORMENT memory → local LLM → TTS) for deploying characters on X Spaces and other live audio environments.

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

**Agent Spine (v2.4):**
- `POST /spine/submit_task` `{ workspace_id, agent_id, operation, payload, mode? }` — governed entry point for all operations
- `GET /spine/status?workspace_id=...` — lightweight pulse check: active agents, recent decisions, blocks, escalations
- `GET /spine/operations` — list all registered operations with trust/tier metadata

**MCP Server (v2.4):**
- Run via `python -m torment_service.mcp_server` (stdio transport for Claude Desktop)
- Tools: `torment_submit_task`, `torment_ingest`, `torment_query_memory`, `torment_query_state`, `torment_feedback`, `torment_reinforce`
- Resources: `torment://admin/status`, `torment://workspace/{ws}/agent/{ag}/state`, `torment://workspace/{ws}/agent/{ag}/memory-summary`, `torment://workspace/{ws}/collective/status`

**Tool-result ingest (v2.4.3):**
- `POST /tool/ingest` `{ workspace_id, agent_id, tool_name, content, summary?, step?, domain_id?, session_id?, tool_metadata?, supplied_embedding? }` — governed ingest of externally obtained tool output as memory. This is a memory artifact operation, not tool execution. TORMENT remembers what tools returned; it does not decide what tools to run.

**Provenance (v2.4.2):**
- `GET /debug/provenance?workspace_id=...&agent_id=...` — inspect stored provenance metadata per memory

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

```bash
# MCP Server — expose governed operations to Claude Desktop
export TORMENT_MCP_WORKSPACE_ID=default
export TORMENT_MCP_AGENT_ID=atlas
export TORMENT_MCP_TRUST_TIER=0.6
# Optional: persist incident log to JSONL
export TORMENT_MCP_INCIDENT_LOG=./data/spine_incidents.jsonl
```

```bash
# Thinking Advisory (v2.4.1) — pre-cognition sidecar in the Spine
export TORMENT_THINKING_ADVISORY=1

# Contextual Abstention (v2.4.1) — stance policy geometric modulation
export TORMENT_CONTEXTUAL_ABSTENTION=1
```

Each layer is independently flag-gated. Zero overhead when off. They compose naturally: compression provides the memory lifecycle, SRG adds geometric memory physics, hivemind enables multi-agent resonance coupling, thinking adds pre-cognition routing, stance adds geometric participation modulation, and the MCP server exposes governed operations to external tools.

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

## Support This Project

If TORMENT Fabric is useful to you, consider supporting its development.

**Crypto**

- **BTC:** `bc1p8g9dd2y4fgnshdsvyq5ecu22mdr5kjfw8zdcptfdhghh4a0837ssjqzgka`
- **ETH:** `0x52a31b19bC79d412621aA898adCC2BDd3580fDf4`
- **SOL:** `2AmeJwpE68FbytofrUgrNtYwwtzLnjfDi1ACzkBDxBUj`

**Ko-fi**

- [ko-fi.com/hilmirhalldorsson](https://ko-fi.com/hilmirhalldorsson)

---

## Notes

- If you have a real summarizer/embedder, pass `supplied_summary` and/or `supplied_embedding` to `/agent/ingest`
- Otherwise TORMENT uses deterministic placeholders (hash-embed + simple summary fallback)
- Character seeds work best with real embeddings — hash embeddings produce orthogonal vectors so seed concepts don't cluster naturally, but the system still functions correctly
- The `data/` directory contains workspace state and should not be committed to version control
