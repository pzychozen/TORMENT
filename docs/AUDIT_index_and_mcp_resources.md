# TORMENT Audit: Index Endpoints & MCP Resources

**Date:** 2026-04-12
**Scope:** Index endpoints (`/index/*`) and MCP resources (non-tool read surfaces)
**Precondition:** `/retrieve` provenance preservation and cognition aperture classification patched

---

## 1. Executive Conclusion

**Partially aligned with meaningful bypasses.**

Index endpoints are provenance-blind because the SQLite schema was never designed to carry provenance. The problem is at the schema level, not the route level — the data simply isn't there to return. These endpoints function as structural/cache views and do not pretend to be governed retrieval, but they do return memory-like content (summaries, motif membership, event references) without any classification signal. A caller cannot distinguish a collective echo from an organic memory through any index endpoint.

MCP resources present a split trust model: tools go through Spine with trust enforcement and exposure-tier gating; resources bypass both entirely. All four audited resources read fabric internals directly. This is architecturally intentional (resources are read-only projections) but creates a concrete gap where the same MCP client sees governed results from tools and ungoverned results from resources. The provenance resource exposes truncated memory text from all private entities without Spine mediation.

---

## 2. Index Endpoint Table

| Endpoint | Backing Store | Memory-like Content? | Provenance Present? | Hydration Source | Risk |
|----------|--------------|---------------------|--------------------|--------------------|------|
| `GET /index/*/recent` | SQLite `core_nodes` | **Yes**: 500-char summary, strength, coherence | **No** | SQLite cache only | **HIGH** — returns memory summaries without classification |
| `GET /index/*/motif/{id}` | SQLite `core_nodes` JOIN `core_motifs` | **Yes**: summary + motif weight | **No** | SQLite cache only | **HIGH** — collective echoes with motif membership indistinguishable |
| `GET /index/*/events` | SQLite `core_events` | **Indirect**: event_type, eid reference, drift_score | **No** | SQLite cache only | **MEDIUM** — references entities but no text; eid alone insufficient |
| `GET /index/*/trajectory` | SQLite `trajectory_index` | **No**: geometric coordinates only | **No** | SQLite cache only | **LOW** — structural/geometric, no memory text |
| `GET /index/*/stats` | SQLite (all tables) | **No**: row counts only | **N/A** | COUNT(*) queries | **None** — aggregate statistics |

### Root Cause

The SQLite index schema (`sqlite_index.py` lines 46-91) was designed as a denormalized cache mirror with no provenance columns. The `index_node()` method (line 221) receives the full entity payload but never extracts provenance:

```
core_nodes columns: eid, kind, tier, memory_class, step, created_at,
                    half_life_days, coherence, strength, confidence,
                    summary, shard, row_idx
```

No `provenance_type`, `source_type`, or `write_path` column exists. The fix must happen at the schema level — routes cannot return what the backing store doesn't have.

### Classification

- **`/recent` and `/motif/*`**: These return memory-like content (summaries, scores) and are the most likely to be mistaken for a retrieval surface. They are effectively provenance-blind side doors to memory content.
- **`/events`**: Returns event metadata that references entities by eid. Less dangerous because it doesn't include text, but still cannot distinguish collective-triggered events.
- **`/trajectory`**: Purely geometric. Safe as-is. No fix needed.
- **`/stats`**: Aggregate counts. Safe as-is. No fix needed.

---

## 3. MCP Resource Table

| Surface | Tool or Resource | Spine-mediated? | Reads Raw Internals? | Category | Risk |
|---------|-----------------|----------------|---------------------|----------|------|
| `torment_query_memory` | **Tool** | **Yes** (submit_task) | No — through fabric.query() | Normal retrieval | **None** |
| `torment_query_state` | **Tool** | **Yes** (submit_task) | No — through Spine helpers | State read | **None** |
| `torment://admin/status` | **Resource** | **No** | **Yes**: agent_states, character_store, private_graphs | Admin telemetry | **MEDIUM** |
| `torment://…/provenance` | **Resource** | **No** | **Yes**: private_graphs, entities, entity.payload | Debug/audit | **MEDIUM-HIGH** |
| `torment://…/collective/status` | **Resource** | **No** | **Yes**: shared_graphs, agent_states, _collective_fields | Collective telemetry | **LOW** |
| `torment://…/memory-summary` | **Resource** | **Hybrid** | **Partial**: Spine for state, direct for motif_regs | Summary/observability | **LOW** |

### Exposure Control Gap

Tools are gated by `TORMENT_MCP_EXPOSURE_TIER` (line 231 of `mcp_server.py`): only operations in the configured tier are registered. Resources are registered unconditionally — all five `@mcp.resource` decorators fire regardless of tier setting. There is no trust check, no exposure filter, and no conditional registration for any resource.

---

## 4. Verified Acceptable Surfaces

**`/index/*/trajectory`** — Returns purely geometric data (step, eid, coherence, phi_index, corridor angles, xyz position). No memory text, no summaries, no provenance to worry about. This is structural telemetry and is correctly scoped.

**`/index/*/stats`** — Returns `COUNT(*)` per table plus db_path and db_size_bytes. No entity-level data. Safe as aggregate statistics.

**`torment://…/collective/status`** — Returns workspace-level collective metadata: shared domain list, agent count, bridge counts, convergence event count. No memory text. Clearly labeled "collective" in URI. Cross-agent but only at the metadata level (agent ID list). Acceptable as collective telemetry.

**`torment://…/memory-summary`** — Returns memory count, character metadata, compression status (via Spine), and active motifs (direct). Motifs are abstract pattern identifiers, not memory text. No entity payloads exposed. Partial Spine mediation is the right tradeoff for a summary view. Acceptable with minor label improvement.

---

## 5. Ambiguous or Risky Surfaces

### RISK 1: `/index/*/recent` returns memory summaries without provenance (HIGH)

- **File:** `torment_service/app.py` line 1406; `torment_service/sqlite_index.py` line 367
- **Route:** `GET /index/{workspace_id}/{agent_id}/recent`
- **Exact issue:** Returns up to 500-char `summary` text per memory from `core_nodes` table. The table has no provenance column (schema at line 46). A collective echo's index entry is identical to an organic memory's entry.
- **Why it matters:** This is the most natural "what happened recently" surface. A caller browsing recent memories sees collective echoes mixed with autobiographical memories with no way to tell them apart.
- **Minimal fix direction:** Add `provenance_type TEXT` column to `core_nodes` schema. Extract from `payload.get("provenance")` in `index_node()` (line 221). Return in query results. Migration: rebuild index (already supported via `/index/rebuild`).

### RISK 2: `/index/*/motif/{id}` returns motif-linked memories without provenance (HIGH)

- **File:** `torment_service/app.py` line 1416; `torment_service/sqlite_index.py` line 383
- **Route:** `GET /index/{workspace_id}/{agent_id}/motif/{motif_id}`
- **Exact issue:** Same as `/recent` — joins core_nodes with core_motifs, returns memory summaries + motif weight. No provenance signal. A collective echo attached to a motif looks identical to an organic memory attached to the same motif.
- **Why it matters:** Motif-based browsing is a likely investigative surface. If an operator is auditing why a motif grew, they cannot distinguish collective influence from organic growth.
- **Minimal fix direction:** Same schema fix as RISK 1 — `provenance_type` column on `core_nodes` covers both endpoints since `/motif/*` joins on `core_nodes`.

### RISK 3: `torment://…/provenance` exposes memory text without Spine mediation (MEDIUM-HIGH)

- **File:** `torment_service/mcp_server.py` line 761, function `resource_provenance()`
- **Resource:** `torment://workspace/{workspace_id}/agent/{agent_id}/provenance`
- **Exact issue:** Iterates `graph.entities.items()` directly (line 782), reading `entity.payload` for up to 50 most recent entities. Returns 120-char truncated memory text in `summary` field (line 801). Bypasses Spine entirely. No exposure-tier gating.
- **Why it matters:** This is the only bulk memory-content-exposing MCP surface. While labeled as a verification/debug resource, it reads the same private graph that the governed `torment_query_memory` tool accesses through Spine. The split creates an inconsistency: tools require trust; this resource does not.
- **Minimal fix direction:** Either (a) gate the resource behind exposure tier `"guarded"` or higher, or (b) route it through a Spine helper that enforces at least `TRUST_READ_ONLY`, or (c) strip memory text from the response and return only provenance metadata (source_type, write_path, has_provenance) without summaries.

### RISK 4: `torment://admin/status` exposes cross-agent data without Spine (MEDIUM)

- **File:** `torment_service/mcp_server.py` line 636, function `resource_admin_status()`
- **Resource:** `torment://admin/status`
- **Exact issue:** Iterates over ALL entries in `fabric.agent_states` (line 668), reads `character_store.load_state()` and `private_graphs` entity counts for every agent. Returns a flat list of all agents with drift scores. Bypasses Spine. No exposure-tier gating.
- **Why it matters:** This is the only surface that aggregates data across all workspaces and agents in a single response. While it exposes metadata (counts, drift) not text, the cross-agent aggregation is more permissive than anything the governed tool path allows.
- **Minimal fix direction:** Gate behind exposure tier `"guarded"`. The resource is correctly labeled as admin and its data is metadata-only, so the main fix is exposure control, not content stripping.

### RISK 5: `/index/*/events` references entities without classification (MEDIUM)

- **File:** `torment_service/app.py` line 1439; `torment_service/sqlite_index.py` line 412
- **Route:** `GET /index/{workspace_id}/{agent_id}/events`
- **Exact issue:** Returns `core_events` rows with `event_type`, `eid`, `drift_score`, `coherence`. No provenance signal. Events triggered by collective echoes are indistinguishable from events triggered by organic memories.
- **Why it matters:** An operator investigating drift or coherence changes cannot tell whether the triggering memory was collective or organic.
- **Minimal fix direction:** Add `provenance_type TEXT` column to `core_events` table. Extract from the originating memory's provenance during `index_event()`. Lower priority than the `core_nodes` fix because events are metadata-oriented and don't include text.

---

## 6. Tools vs Resources Comparison

| Dimension | MCP Tools | MCP Resources |
|-----------|----------|---------------|
| Spine mediation | **Yes** — all go through `submit_task()` | **No** — all bypass Spine (memory-summary is hybrid) |
| Trust enforcement | **Yes** — minimum trust tier per operation | **No** — no trust check on any resource |
| Exposure tier gating | **Yes** — filtered by `TORMENT_MCP_EXPOSURE_TIER` | **No** — all registered unconditionally |
| Auto-escalation | **Yes** — identity-sensitive queries escalate to full path | **No** — no escalation mechanism |
| Audit logging | **Yes** — Spine logs decisions to incident log | **No** — no audit trail for resource reads |
| Memory text exposure | Governed — through `fabric.query()` scoring | Mixed — `/provenance` exposes 120-char text directly |
| Cross-agent scope | Single agent per tool call | `/admin/status` aggregates all agents |

**Verdict:** There is a clear split model. Tools are governed; resources are raw. This is architecturally intentional (resources are designed as lightweight observability projections) but the gap is under-documented and under-controlled. The exposure tier that gates tools should also gate resources, at minimum for the two surfaces that expose memory content or cross-agent data.

---

## 7. Single Highest-Value Next Fix

**Add `provenance_type` column to `core_nodes` in the SQLite index schema.**

This is the single fix that closes the most gaps with the least effort:

- **Where:** `torment_service/sqlite_index.py`
- **Schema change:** Add `provenance_type TEXT` to `core_nodes` table definition (line 46)
- **Index-time extraction:** In `index_node()` (line 221), extract provenance_type from `payload.get("provenance")` using the same derivation logic as `_stamp_provenance_type` in `apertures.py`
- **Query change:** None needed — `SELECT *` already returns all columns
- **Migration:** The existing `/index/rebuild` endpoint (line 1476) repopulates from canonical JSONL, so no manual migration is needed — rebuild picks up the new column
- **Coverage:** Fixes `/recent` and `/motif/*` in one change (both query `core_nodes`). Events and trajectory are lower priority and can follow separately.

This fix directly answers the audit's core question: "Can these index endpoints distinguish collective echoes from ordinary memory today?" After this fix, the two highest-traffic index endpoints can.
