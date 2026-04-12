# TORMENT Read-Surface Classification Audit

**Date:** 2026-04-12
**Scope:** All runtime read/exposure paths — API, Spine, MCP, fabric methods
**Precondition:** Phase D echo packet leak fixed, collective retrieval discount centralized

---

## 1. Executive Conclusion

**Read surfaces are mostly consistent, with several concrete classification gaps.**

The primary retrieval path (`/agent/query` → `fabric.query()`) is well-classified: it applies collective discount via the centralized `scoring.py` contract, badges every hit with `provenance_type`, and clearly separates organic from collective material. The governance endpoints are cleanly separate. The collective telemetry endpoints are clearly labeled.

However, there are **five material classification gaps** where read surfaces either strip provenance, bypass the scoring contract, or blur the boundary between debug inspection and ordinary retrieval:

1. **`/retrieve` strips provenance** — the assembled-context endpoint drops `provenance_type` during ContextBlock conversion, making collective echoes indistinguishable from organic memory in the cognition pipeline's primary input
2. **Index endpoints bypass scoring entirely** — `/index/*/recent`, `/index/*/motif/*`, `/index/*/events`, `/index/*/trajectory` return raw SQLite metadata with no provenance badge and no collective discount
3. **Cognition apertures bypass unified rescore** — `build_memory_context()` calls lane functions directly, returning raw hits to roles without the collective discount pass that `query()` applies
4. **`/archive/query` and `/deep-memory/query` bypass all scoring** — raw cosine similarity, no provenance handling
5. **MCP resource `torment://…/provenance`** iterates all private graph entities, exposing truncated memory text without distinguishing collective from autobiographical

None of these are write-path vulnerabilities. All are read-classification issues where governed or collective material can appear without appropriate labeling.

---

## 2. Surface Inventory

### Normal Retrieval Surfaces

| Surface | Route / Function | Category | User-facing | Governance/Classification | Risk |
|---------|-----------------|----------|-------------|--------------------------|------|
| Primary query | `POST /agent/query` → `fabric.query()` | Normal retrieval | Yes | Full: collective discount, provenance badge, lane weights | **None** |
| Assembled retrieval | `POST /retrieve` → `assemble_context()` | Normal retrieval | Yes (cognition input) | **Broken**: provenance stripped in ContextBlock conversion | **HIGH** |
| Trace/explain | `POST /agent/trace` → `fabric.trace()` | Debug/explain | Semi | Full: same discount as query(), explain dict shows breakdown | **None** |
| Deep memory query | `POST /deep-memory/query` | Normal retrieval | Yes | **Missing**: raw cosine scores, no provenance, no discount | **MEDIUM** |
| Archive query | `POST /archive/query` | Normal retrieval | Yes | **Missing**: raw cosine, explicitly "no physics, no identity" | **LOW** (archive ≠ echo path) |

### Index / Convenience Surfaces

| Surface | Route / Function | Category | User-facing | Governance/Classification | Risk |
|---------|-----------------|----------|-------------|--------------------------|------|
| Recent memories | `GET /index/*/recent` | Mixed | Yes | **Missing**: SQLite metadata only, no provenance, no discount | **HIGH** |
| Memories by motif | `GET /index/*/motif/*` | Mixed | Yes | **Missing**: same as above | **HIGH** |
| Trajectory range | `GET /index/*/trajectory` | Debug | Semi | **Missing**: geometric only, no provenance | **LOW** |
| Events by type | `GET /index/*/events` | Debug | Semi | **Missing**: event metadata, no provenance | **MEDIUM** |
| Index stats | `GET /index/*/stats` | Debug | Yes | Clean: counts only | **None** |

### Collective Telemetry Surfaces

| Surface | Route / Function | Category | User-facing | Governance/Classification | Risk |
|---------|-----------------|----------|-------------|--------------------------|------|
| Collective status | `GET /collective/status` | Collective telemetry | Yes | Clean: metadata only, clearly labeled | **None** |
| Packets | `GET /collective/packets` | Collective telemetry | Yes | Clean: labeled collective, contains summary text by design | **None** |
| Events | `GET /collective/events` | Collective telemetry | Yes | Clean: labeled collective, contains summary text by design | **None** |
| Event detail | `GET /collective/events/{id}` | Collective telemetry | Yes | Clean: same as events | **None** |
| Proposals status | `GET /collective/proposals/status` | Collective telemetry | Yes | Clean: pattern metadata only | **None** |

### Governance / Audit Surfaces

| Surface | Route / Function | Category | User-facing | Governance/Classification | Risk |
|---------|-----------------|----------|-------------|--------------------------|------|
| Governance get | `GET /memory/governance/get` | Governance read | Yes | Clean: flags only, no memory text | **None** |
| Governance audit | `GET /governance/audit` | Governance audit | Yes | Clean: flag-change log, no memory text | **None** |
| Governance set | `POST /memory/governance/set` | Governance write | Yes | Clean: through Spine, audited | **None** |

### Debug / Inspection Surfaces

| Surface | Route / Function | Category | User-facing | Governance/Classification | Risk |
|---------|-----------------|----------|-------------|--------------------------|------|
| Debug metrics | `GET /debug/metrics` | Debug | No | Clean: counts/stats only | **None** |
| Debug provenance | `GET /debug/provenance` | Debug | No | **Ambiguous**: 120-char memory text, no collective badge | **MEDIUM** |
| Thinking debug | `POST /thinking/debug` | Debug | No | Clean: controller state, no memory content | **None** |
| Geo profiles | `GET /thinking/debug/geo_profiles` | Debug | No | Clean: hardcoded test profiles | **None** |
| Spine status | `GET /spine/status` | Operational | Semi | Clean: drift/counts only | **None** |
| Spine operations | `GET /spine/operations` | Operational | Semi | Clean: operation registry metadata | **None** |
| Spine alignment | `GET /spine/alignment` | Debug | No | Clean: alignment statistics only | **None** |
| Memory chain | `POST /memory/chain` | Debug | No | Raw event chain; events may include collective operations | **LOW** |
| Full graph trace | `POST /memory/trace_full` | Debug | No | Graph structure, no scores, clearly structural | **LOW** |
| Trace bundle | `POST /memory/trace_bundle` | Debug | No | Export package; narrative could surface collective items | **LOW** |

### MCP Surfaces

| Surface | Resource URI / Tool | Category | Governance/Classification | Risk |
|---------|-------------------|----------|--------------------------|------|
| MCP query_memory | `torment_query_memory` tool | Normal retrieval | Full: through Spine → fabric.query() | **None** |
| MCP query_state | `torment_query_state` tool | State read | Through Spine, no memory content | **None** |
| MCP agent state | `torment://…/state` | State read | Through Spine | **None** |
| MCP memory summary | `torment://…/memory-summary` | Summary | Partially Spine; motifs read directly from fabric | **LOW** |
| MCP admin status | `torment://admin/status` | Operational | **Bypasses Spine**: reads fabric.agent_states directly | **MEDIUM** |
| MCP collective status | `torment://…/collective/status` | Collective telemetry | **Bypasses Spine**: reads fabric directly | **LOW** |
| MCP provenance | `torment://…/provenance` | Debug | **Bypasses Spine**: iterates all private entities, 120-char text | **MEDIUM** |

### Cognition Internal Surfaces

| Surface | Function | Category | Governance/Classification | Risk |
|---------|----------|----------|--------------------------|------|
| Aperture lane retrieval | `build_memory_context()` via `LaneQueryProvider` | Internal | **Missing**: lane functions return raw hits without collective discount | **HIGH** |

---

## 3. Verified Good Boundaries

**Primary query path is well-armored.** `fabric.query()` (line 3304) → imports `is_collective_provenance` and `apply_collective_discount` from `scoring.py` → applies 0.50x discount to collective echoes (line 3618) → badges every hit with `provenance_type` (line 3664) → returns sorted by `final_score`. Proved by: `tests/test_phase_d_runtime_wiring.py` TestApplyCollectiveDiscount (17 tests pass), centralized in `scoring.py` lines 263-286.

**Trace path mirrors query scoring.** `fabric.trace()` (line 4351) imports the same `_is_coll_prov_t` / `_apply_coll_disc_t` aliases and applies identical discount (line 4528). Explain dict explicitly shows `collective_discount` field (line 4584).

**Collective telemetry is clearly separate.** All `/collective/*` endpoints return data with `enabled` flag, packets/events include agent_id and domain_id fields, and are mounted under a clearly collective path prefix. No collective telemetry endpoint pretends to be normal retrieval.

**Governance surfaces are read-only and audited.** `governance/get` returns only flags. `governance/audit` returns only change records. `governance/set` goes through Spine at `TRUST_OPERATOR` tier and writes an append-only audit log. No governance surface mutates while pretending to read.

**Spine mediates all MCP tools.** The two MCP tools (`torment_query_memory`, `torment_query_state`) both route through the Spine's `submit_task()` with trust enforcement and auto-escalation. The Spine dispatcher is the single governed entry point for tool calls.

**Debug endpoints are labeled.** All `/debug/*` and `/thinking/debug/*` endpoints use the debug path prefix. `debug/metrics` exposes only counts. `thinking/debug/geo_profiles` returns hardcoded test data.

---

## 4. Ambiguous or Risky Surfaces

### RISK 1: `/retrieve` strips provenance (HIGH)

- **File:** `torment_service/retrieval_assembler.py`, function `_hit_to_block()` (line 189)
- **Route:** `POST /retrieve` in `app.py` line 1321
- **Issue:** `_hit_to_block()` converts query hits to `ContextBlock` objects. The `ContextBlock` dataclass (line 57) has fields: `block_type, eid, chunk_id, text, token_count, score, reason, source, metadata`. The `metadata` dict (line 221) captures `type, half_life, strength, confidence` but **never extracts `provenance_type` or `provenance_tool_name`** from the hit. The `source` field is hardcoded to `"core"` or `"archive"`.
- **Why it matters:** `/retrieve` is the primary input to the cognition pipeline. If a collective echo passes through `/retrieve`, the consuming role (engineer, interpreter, skeptic, archivist) sees it as ordinary autobiographical memory. The collective discount was applied upstream in `query()` so the score is lower, but the provenance signal is gone.
- **Fix direction:** Add `provenance_type` to `ContextBlock.metadata` in `_hit_to_block()` — one line change. Downstream consumers can then inspect it.

### RISK 2: Index endpoints bypass scoring (HIGH)

- **File:** `torment_service/app.py`, lines 1406-1449
- **Routes:** `GET /index/*/recent`, `GET /index/*/motif/*`, `GET /index/*/events`, `GET /index/*/trajectory`
- **Issue:** All four read from SQLite `IndexManager` which has no provenance column. Returns raw metadata (eid, step, summary, coherence, strength) with no `provenance_type` field and no collective discount. The `core_nodes` table does not track provenance.
- **Why it matters:** A collective echo's index entry looks identical to an organic memory's index entry. The `/recent` endpoint in particular is a plausible "what happened lately" surface that could present echoes as autobiographical.
- **Fix direction:** Either (a) add a `provenance_type` column to `core_nodes` and populate during index rebuild, or (b) hydrate provenance from the entity payload post-fetch for these endpoints, or (c) document these as provenance-blind index views with a response-level warning field.

### RISK 3: Cognition apertures bypass unified rescore (HIGH)

- **File:** `cognition/apertures.py`, function `build_memory_context()` (line 197)
- **Issue:** When a `LaneQueryProvider` is supplied, `build_memory_context()` calls `lane_provider.private_fn()`, `shared_fn()`, `deep_fn()` directly. These wrap `_query_private_lane()`, `_query_shared_lane()`, `_query_deep_lane()` from `fabric.py`. These lane functions return raw search results without the unified rescore pass that `query()` performs — no collective discount, no provenance badge.
- **Why it matters:** The cognition pipeline's 4-role system receives memories without collective classification. An engineer role or skeptic role processing these hits cannot distinguish collective echoes from organic memories.
- **Fix direction:** Either (a) apply `apply_collective_discount` inside each lane function, or (b) add a post-lane rescore step in `build_memory_context()`, or (c) tag hits with provenance in the lane functions so roles can inspect them.

### RISK 4: `/debug/provenance` exposes memory text without collective badge (MEDIUM)

- **File:** `torment_service/app.py`, line 2780
- **Route:** `GET /debug/provenance`
- **Issue:** Iterates all private graph entities, returns 120-char truncated summary text + raw provenance dict. The response includes `provenance` per memory, which does contain `source_type`, but there is no top-level classification or filtering. A collective echo's provenance will say `source_type: "collective_echo"` if inspected, but the endpoint does not badge or flag it differently.
- **Why it matters:** The endpoint is labeled `/debug/` so it's nominally scoped, but it exposes real memory text and is the only bulk provenance inspector. A caller unfamiliar with the system could treat it as a content browser.
- **Fix direction:** Add a `classification` field per memory entry (`"organic"`, `"collective_echo"`, `"tool_result"`) derived from `is_collective_provenance()`. Low effort, high clarity.

### RISK 5: MCP resources bypass Spine (MEDIUM)

- **File:** `torment_service/mcp_server.py`
- **Resources:** `torment://admin/status` (line 636), `torment://…/provenance` (line 761), `torment://…/collective/status` (line 702)
- **Issue:** These MCP resources read from `fabric.agent_states`, `fabric.private_graphs`, and `fabric._collective_fields` directly, bypassing Spine trust enforcement. The admin status resource in particular reads all agents across workspaces without trust checks.
- **Why it matters:** MCP tools go through Spine; MCP resources partially don't. This creates an inconsistency where the same MCP client sees governed results from tools but ungoverned results from resources.
- **Fix direction:** Route resource reads through Spine helper functions, or document resources as debug/admin surfaces with explicit trust assumptions.

---

## 5. API vs Spine vs MCP Comparison

**API and Spine present the same conceptual model for core operations.** `/agent/query` calls `fabric.query()`, and the Spine's `query_memory` operation calls the same `fabric.query()`. Both see the same provenance badges and collective discount. `/memory/governance/set` and the Spine's `memory_governance_set` both go through the same Spine trust enforcement.

**MCP tools match Spine.** `torment_query_memory` and `torment_query_state` both route through `_spine_call()` → `submit_task()` → governed dispatch. Trust tiers and auto-escalation apply identically.

**MCP resources diverge from Spine.** The four MCP resources (`admin/status`, `memory-summary`, `collective/status`, `provenance`) partially or fully bypass Spine, reading from fabric internals directly. This creates a two-tier model: MCP tools are governed, MCP resources are not.

**API convenience endpoints (index/*) diverge from the main API path.** The index endpoints read from a SQLite cache that does not carry provenance data, while the main `/agent/query` endpoint uses the full scoring contract. These coexist under the same API but present different classification models.

**Cognition pipeline diverges from the API path.** `build_memory_context()` in `cognition/apertures.py` uses lane functions directly rather than `fabric.query()`, so the cognition pipeline's roles receive memories without the unified rescore pass. This is the most consequential divergence because it affects the primary reasoning path.

**Summary:** Core query paths (API, Spine, MCP tools) are consistent. Convenience paths (index endpoints, `/retrieve`, MCP resources, cognition apertures) each diverge in different ways.

---

## 6. Most Important Next Fix

**Fix `/retrieve` provenance stripping.**

This is the single highest-leverage fix because `/retrieve` feeds the cognition pipeline — it is the bridge between memory retrieval and AI reasoning. Every other surface is either debug-scoped, low-traffic, or informational. But `/retrieve` is on the critical path: memories retrieved here become the context that roles reason about.

The fix is minimal: in `retrieval_assembler.py`, function `_hit_to_block()`, add `provenance_type` to the metadata dict:

```python
meta: Dict[str, Any] = {
    "type": mtype,
    "half_life": float(hit.get("half_life", 0)),
    "strength": float(hit.get("strength", 0)),
    "confidence": float(hit.get("confidence", 0)),
    "provenance_type": hit.get("provenance_type"),  # <-- add this
}
```

This preserves the collective echo signal through the assembled context so downstream consumers (roles, Claude) can see what they're working with. The score discount from `query()` already lowers collective echoes in ranking; this addition lets consumers know *why* something ranked lower and what category it belongs to.

After this fix, the cognition aperture path (Risk 3) becomes the next priority — it's the other major path where collective material reaches reasoning without classification.
