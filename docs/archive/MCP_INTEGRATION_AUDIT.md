# MCP Integration Audit — TORMENT Memory Fabric v2.4.0

**Date**: 2026-03-28
**Auditor**: Claude (codebase inspection)
**Purpose**: Answer three prerequisite questions before designing MCP surface

---

## Question 1: Is the Agent Spine a Mandatory Gateway?

**Answer: NO. The Spine is completely optional.**

Out of 58+ REST endpoints, exactly ONE goes through the cognition pipeline:

- `POST /cognition/run` — the only endpoint that invokes Router -> Apertures -> Roles -> Reintegration

Everything else bypasses the Spine entirely and hits the memory layer directly:

| Operation | Endpoint | Goes Through Spine? |
|-----------|----------|-------------------|
| Ingest memory | `POST /agent/ingest` | NO — calls `fabric.ingest()` directly |
| Query memory | `POST /agent/query` | NO — calls `fabric.query()` directly |
| Feedback/reinforce | `POST /agent/feedback` | NO — calls `fabric.feedback()` directly |
| Collective reingest | `POST /workspace/{id}/collective/reingest` | NO — calls `fabric.reingest_convergence()` directly |
| Compression | `POST /workspace/{id}/compress/trigger` | NO — calls CompressionScorer/Router/Executor directly |
| Deep memory query | `POST /workspace/{id}/deep-memory/query` | NO — calls deep_store.query() directly |
| Archive ingest | `POST /archive/ingest_document` | NO — calls ArchiveStore.ingest_document() directly |
| Unified retrieve | `POST /retrieve` | NO — calls fabric.query() + archive directly |

**The Spine wraps `fabric.query()` inside its aperture builder, but it has NO ingest, NO reinforce, NO compress capability.** It is a read-and-reason layer only. Memory writes happen outside the Spine's control.

### Implication for MCP

If we expose `spine.submit_task` as the MCP tool, we need to either:

1. **Extend the Spine** to handle ingest/reinforce/compress operations (make it a true gateway), or
2. **Accept that MCP will need both Spine tools AND governed direct-memory tools**, with the Spine intercepting where it can and governance flags protecting where it can't

Option 1 is architecturally cleaner but a significant refactor. Option 2 is pragmatic but requires the governance layer to compensate for what the Spine doesn't cover.

---

## Question 2: What Does Trust/Identity Resolution Look Like?

**Answer: There is NO trust system. Zero authentication. Zero authorization.**

### What exists

- **workspace_id**: A plain string label. Any client can pass any workspace_id. No ownership, no verification. Workspace isolation IS enforced (separate directories, composite keys) — but only if you know the ID.
- **agent_id**: A plain string label. No cryptographic binding to any client or session. Any caller can impersonate any agent.
- **Seed identity**: Persisted as `identity.json` (plaintext on disk). No encryption, no signing, no revocation.
- **Provenance**: Tracks `source_type`, `derivation_depth`, `confidence` (0.0-1.0). This is lineage tracking, not a trust tier. Invariant G prevents low-confidence overwriting high-confidence, but that's content precedence, not caller authorization.
- **Governance flags**: Per-memory flags (`protected`, `non_shareable`, `collective_export_blocked`, etc.). These control what MEMORY can do, not what CLIENTS can do.
- **No session concept**: No bearer tokens, no API keys, no auth middleware in FastAPI.

### Gap analysis for MCP

| Aspect | Current State | MCP Need | Gap |
|--------|--------------|----------|-----|
| Client authentication | None | Token/keypair per client | CRITICAL |
| Trust tiers | None (provenance only) | 3-4 tier system | CRITICAL |
| Workspace ownership | None | Client-to-workspace mapping | CRITICAL |
| Agent binding | String label | Cryptographic proof | CRITICAL |
| Per-client governance | None (per-memory only) | Client-scoped access control | HIGH |
| Session tracking | None | Client session lifecycle | MEDIUM |
| Audit trail | Basic timestamps only | Full caller-aware audit | HIGH |

### What CAN be reused

- Workspace isolation mechanism (solid, just needs auth on top)
- Memory governance flags (extend scope from per-memory to per-client)
- Provenance system (add client_id tracking)
- Collective policy engine (add client consent layer)

---

## Question 3: How Does Collective Topology Handle Concurrency?

**Answer: It doesn't. The system is NOT thread-safe for concurrent agent access.**

### Critical findings

**1. No locking on per-agent state** (fabric.py)

The ingest path does read-mutate-write on `self.agent_states[ak]` with zero locking:
```
state = self.agent_states[ak]           # READ
state, signals, debug = kernel.process(state, text)  # MUTATE
self.agent_states[ak] = state           # WRITE
```
Two concurrent ingests for the same agent will corrupt TriOcta kernel state (last writer wins, first writer's phase/cycle updates lost).

**2. No locking on private graphs** (fabric.py)

`self.private_graphs` dict access is unprotected. Lazy initialization has TOCTOU bugs — two threads can simultaneously construct duplicate MemoryGraph instances for the same agent.

**3. Collective field initialization not thread-safe** (fabric.py)

`_get_collective_field()` and `_get_proposal_bridge()` use check-then-write without locks. Race during initialization produces orphaned instances.

**4. Convergence detection has ordering assumptions** (collective_field.py)

`append_packet()` writes to disk outside the lock, adds to cache inside the lock, then detects convergence outside the lock again. Concurrent packets from different agents can produce non-deterministic convergence results.

**5. Reingest dedup has a race window** (collective_policy.py)

`is_duplicate()` check and `record()` write are separate transactions. Two threads can both pass the dedup check for the same event before either records, causing duplicate echo ingestion — violating the 7-gate guarantee.

**6. Character state load-modify-save not atomic** (fabric.py)

No lock protects the sequence. Concurrent operations on the same agent's character state will lose updates.

**7. Convergence cooldowns are in-memory only** (collective_field.py)

`_event_cooldowns` dict is not persisted. Service restart within cooldown window produces duplicate convergence events.

### What IS partially safe

- CollectiveField has a `_lock` around its `_recent_packets` cache (but detection happens outside the lock)
- Proposal bridge has a `_lock` around its persistence writes (but file writes aren't atomic)
- Different agents in different workspaces are isolated by key structure (safe if truly independent)

### Implication for MCP

A global MCP server multiplexing concurrent agent requests WILL cause data corruption unless we either:

1. **Serialize at the MCP layer** (queue requests per agent, only one in-flight operation per agent at a time)
2. **Add locking internally** (workspace-level mutex for shared state, per-agent mutex for private state, atomic lazy initialization)
3. **Use separate fabric instances per agent** (memory-inefficient but safe)

**Recommendation**: Option 1 (serialize at MCP) for the prototype, Option 2 (internal locking) before any production use.

---

## Endpoint Surface Map

### Read-only endpoints safe for MCP resources (34 total)

These can be exposed immediately as MCP resources with no risk:

**Agent state resources:**
- `GET /agent/{id}/identity` — seed, overlay, timestamps
- `GET /agent/{id}/character/state` — drift, basin, tiers, phase
- `GET /agent/{id}/character/seed` — seed metadata
- `GET /agent/{id}/roles` — soft role profile

**Memory inspection resources:**
- `POST /agent/query` — semantic search (read-only despite POST)
- `POST /agent/trace` — trace retrieval paths
- `POST /retrieve` — unified context assembly
- `POST /memory/chain` — causal chain lookup
- `POST /memory/trace_full` — full graph trace

**Workspace resources:**
- `GET /workspace/{id}/domains` — domain listing
- `GET /workspace/{id}/collective/status` — collective summary
- `GET /workspace/{id}/collective/packets` — recent packets
- `GET /workspace/{id}/collective/events` — convergence events
- `GET /workspace/{id}/compress/status` — compression state
- `GET /workspace/{id}/domain/{id}/motifs/active` — active motifs

**Observability resources:**
- `GET /debug/metrics` — unified metrics
- `GET /health` — system health
- `GET /config` — effective configuration

### Write endpoints that need governance gating for MCP tools

**Must go through Spine (or equivalent governance):**
- `POST /agent/ingest` — memory creation
- `POST /agent/feedback` — reinforcement
- `POST /workspace/{id}/collective/reingest` — echo ingestion (already has 7-gate policy)
- `POST /agent/propose_share` — shared memory proposals
- `POST /workspace/process_proposals` — proposal processing

**Operator-level decisions (human-in-the-loop for MCP):**
- `POST /workspace/domain/proposals/decide` — approve/reject proposals
- `POST /workspace/motif_merges/decide` — resolve merges
- `POST /workspace/bridges/decide` — approve cross-domain links
- `POST /workspace/conflicts/decide` — resolve conflicts
- `POST /memory/governance/set` — update governance flags

---

## Recommended Pre-MCP Work

### Phase 0: Shore up before wrapping

Before building any MCP surface, these issues should be addressed:

**P0 (Blockers):**
1. Add per-agent serialization for ingest operations (at minimum a per-agent-key lock around the read-mutate-write on agent_states)
2. Make lazy initialization atomic (double-checked locking for collective fields, proposal bridges, private graphs)
3. Make reingest dedup check-and-record atomic (single lock scope)

**P1 (Required for MCP):**
4. Add request context object: `{client_id, trust_tier, workspace_id, agent_id}`
5. Add FastAPI middleware for authentication (API key or token validation)
6. Add trust tier enforcement: map authenticated client to allowed operations
7. Extend audit trail with caller identity

**P2 (Strengthens architecture):**
8. Consider extending Spine to gate ingest/reinforce (not just query-and-reason)
9. Persist convergence cooldowns to disk
10. Add workspace ownership model

### Minimum viable MCP surface (after Phase 0)

1. **Tool: `spine.submit_task`** — wraps `/cognition/run` with MCP request context
2. **Resource: `workspace/{id}/agent/{id}/state`** — aggregates identity + character + memory health
3. **Resource: `workspace/{id}/collective/status`** — collective summary
4. **Prompt: `governed-memory-check`** — workflow template for safe identity-aware operations

Serialize all tool invocations per-agent at the MCP layer until internal locking is in place.

---

## Architecture Diagram

```
MCP Client (Claude / ChatGPT / IDE / Orchestrator)
    |
    | JSON-RPC (stdio or Streamable HTTP)
    v
MCP Server (new layer)
    |
    +-- Request Context: {client_id, trust_tier, workspace_id, agent_id}
    +-- Per-agent request serialization (queue)
    +-- Trust enforcement middleware
    |
    v
Agent Spine (cognition/pipeline.py)
    |
    +-- Router: intent -> mode (engineering/strategic/identity)
    +-- Apertures: constrained memory view
    +-- Roles: Interpreter -> Engineer -> Skeptic -> Archivist
    +-- Reintegration: merge role outputs
    |
    | Currently: Spine only does query+reason, not ingest/reinforce
    | Future: Extend Spine to gate ALL memory writes
    |
    v
TORMENT Memory (fabric.py)
    |
    +-- Kernel: TriOcta phase-lock processing
    +-- Private graphs: per-agent memory
    +-- Shared graphs: per-domain shared memory
    +-- Governance: per-memory protection flags
    +-- Collective field: convergence detection
    +-- Compression: retention tiers + decay
    +-- Deep store: long-term compressed memory
```

---

## For ChatGPT

The three key findings that should shape the MCP spec:

1. **The Spine is optional, not mandatory.** Any MCP design that assumes "Spine gates everything" is incorrect today. We either extend the Spine or accept a hybrid model where governance flags + MCP-layer serialization compensate for the Spine's limited scope.

2. **There is zero authentication/authorization.** The trust mapping must be built from scratch. The provenance system and governance flags provide a foundation, but client identity doesn't exist yet.

3. **The system is not thread-safe for concurrent access.** A global MCP server MUST serialize requests per-agent, or we need internal locking first. This is a Phase 0 blocker.

The question for the spec is: do we extend the Spine into a full gateway (cleaner, bigger refactor) or build MCP-layer governance that works with the Spine's current limited scope (pragmatic, faster, messier)?
