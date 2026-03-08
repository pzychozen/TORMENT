# TORMENT — Detailed Guide

v2.1

## Concepts

### Workspaces
A workspace is the container for memory graphs, domains, and policies. Most users use one workspace per "life context" or per companion.

### Agents
An agent is a persona/client identity within a workspace. Default pattern is **private-write / shared-read**.

### Domains
Domains separate memory to prevent contamination: `research`, `engineering`, `operations`, `creative`, `meta`.

### Character Seeds (v2.0)
A character seed is a short natural-language description (3-5 sentences) of who the character is at the core. When provided during agent creation, TORMENT plants the seed as high-stability canon memories, establishes a gravitational basin, and tunes the kernel physics to match the character. See `docs/CHARACTER_SYSTEM.md` for the full guide.

### Memory Tiers (v2.0)
Memories are classified into three tiers by half-life: core identity (365+ days), relational (7-364 days), and situational (under 7 days). During queries, tier weights adjust context scoring so core identity memories carry more weight than situational ones.

### Motifs
Motifs are clusters (themes). They stabilize long-term memory by grouping related entries and controlling fragmentation.

### Identity Anchors (auto)
When TORMENT detects repeated motif involvement for an agent, it can create `identity_anchor` memories. Anchors are retrieval-weighted to preserve continuity, with guardrails to avoid turning temporary moods into identity.

### Emotional Continuity (lightweight)
TORMENT can tag coarse affect on memories and create `mood_drift` events when affect changes over time. This is used only as a **tie-break** on personal queries.

### Roles (soft inference)
TORMENT can infer a coarse interaction style (planner/explorer/reflector/etc.) and use it to gently tune continuity behavior. Roles do not override persona or prompts.

### Symbolic State (v2.0 — rewritten)
Each memory event receives one of 8 hidden symbols projected from coherence field geometry. These enable resonance loop detection — recurring symbolic patterns that indicate stable or unstable dynamics.

### Coherence Field
A structural map of motifs computed from reinforcement, tension, and curvature. Each motif is classified as basin (stable), ridge (unstable), or plateau (neutral). The character seed aims to occupy the deepest basin.

### Event-Gated Compression (v2.1)
Memory compression fires at discrete corridor transitions (corridor exit, cycle stage change, emergency tear) — never continuously. The scoring uses a J→Z two-channel model (relational importance 60%, geometric organization 40%). Low-scoring candidates fade in the core graph (short-path); high-scoring old candidates export to a deep memory store (long-path). Protected classes (canon, core_identity, seeds) are never compressed. Memories born during sustained corridors (≥10 steps) resist compression via duration resistance.

### Spirit Return (v2.1)
When queries find too few private hits, compressed memories can return from the deep store through a symbolic resonance pipeline. Each returning memory is classified into one of three modes — resonance (rare, vivid), surfacing (moderate, gentle), or recollection (default, past-tense) — based on symbol interaction, warmth level, and compression path. Warmth accumulates gradually with repeated retrieval (floor 0.2, +0.15 per retrieval, cap 1.0). Voice cues are injected into the assembled context to guide the LLM's tone.

### Phase-Cycle Time (v2.1)
Explicit step-counting of phase and corridor durations per agent. Durations are stored in memory payloads and feed into compression resistance (sustained memories are harder to compress) and spirit return warmth boost (sustained memories warm up faster).

### Deep Memory Store (v2.1)
JSONL-backed archive with shard-based embedding index for long-path compressed memories. Supports cosine-similarity query for spirit return retrieval, export from compression, and recall by EID.

---

## Key Endpoints

### Health and config
- `GET /health` — service status + embedder info
- `GET /profiles` — preset definitions + active profile
- `GET /config` — effective configuration (defaults vs profile vs env overrides)
- `GET /embedder/check` — one-shot embed test + timing

### Workspace
- `POST /workspace/create`
- `GET /workspace/{workspace_id}/domains`
- `GET /workspaces/meta` — workspace embed lock metadata
- `POST /workspace/clone` — migration with selective re-embed
- `POST /workspace/maintenance` — scan/repair/compact

### Agent
- `POST /agent/create` — include `seed_text` and `seed_id` in the seed dict for character layer
- `GET /agent/{agent_id}/identity?workspace_id=...`
- `GET /agent/{agent_id}/roles?workspace_id=...`
- `POST /agent/ingest`
- `POST /agent/query` — returns `character_context` when character is active
- `POST /agent/feedback`

### Compression & Spirit Return (v2.1)
- `GET /workspace/{workspace_id}/spirit-return/status` — spirit return status for the workspace

Note: Compression is triggered automatically during ingest when `TORMENT_COMPRESS_ENABLE=1`. It fires at corridor transitions detected by the EventDetector. No manual trigger endpoint is needed — compression is event-gated by design.

### Trace export (advanced)
- `POST /memory/trace_full`
- `POST /memory/trace_bundle`
- `POST /memory/trace_view`
- `POST /memory/chain`

### Maintenance
- `POST /workspace/maintenance` with `mode=scan_embeddings|repair_embeddings|compact_indexes`
- `POST /workspace/maintenance/job` for async operations
- `POST /workspace/repair_embeddings/job` — async scan/repair (returns job_id)
- `GET /workspace/repair_embeddings/jobs`
- `GET /workspace/repair_embeddings/job/{job_id}`
- `POST /workspace/repair_embeddings/job/{job_id}/cancel`
- `POST /workspace/clone` — migration/clone with selective re-embed
- `GET /workspace/clone/jobs`

---

## Simulation and verification
- `python -m sim.run_sim ...`
- `make test`
- `make verify` — compile + tests + deterministic sim check
