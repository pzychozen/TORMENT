# Tool-Result Retrieval Semantics — Audit & Policy Proposal

**Version:** Draft 1.0
**Date:** 2026-04-07
**Phase:** Post tool_result_ingest stabilization
**Scope:** Retrieval behavior only — no capability boundary changes

---

## 1. Audit: Current Retrieval Pipeline

The full scoring pipeline lives in `fabric.py` `query()` (lines ~3180–3562). Here is every phase, annotated with its relevance to tool-result memories:

### 1.1 Candidate Collection

| Source | Method | Tool-result behavior |
|---|---|---|
| Private graph | `private_graphs[ak].search()` | Tool-result memories **are found** here (they're stored as private-scope entities). No filtering by provenance at search time. |
| Shared graphs | `shared_graphs[d].search()` | Tool results default to `scope="private"`, so they don't appear here unless explicitly ingested as shared. |
| Deep memory | `_deep_store.query()` | Tool results could enter deep stores after compression. No special handling. |

**Finding:** Tool-result memories participate in candidate collection identically to user memories.

### 1.2 Base Scoring (`score_hit()`)

```
score_hit(sim, strength, recency_days, motif_alignment, contradiction_risk, type_bonus)
```

Weights: `alpha=0.35` (sim), `beta=0.10` (strength), `gamma=0.20` (recency), `delta=0.30` (motif).

**Finding:** No provenance awareness. Tool results scored identically to user memories.

### 1.3 Continuity Bonuses (lines 3230–3342)

| Bonus | Env var | Default | Tool-result behavior |
|---|---|---|---|
| Self-thread | `TORMENT_SELF_MEMORY_BONUS` | +0.06 | **Applies** to tool results (they're private, agent-owned) |
| Thread window | `TORMENT_THREAD_WINDOW_BONUS` | +0.08 | **Applies** (step-based recency, no provenance check) |
| Identity anchor | N/A | +0.12 | Does not apply (tool results have `type != "identity_anchor"`) |
| Affect match | `TORMENT_AFFECT_MATCH_BONUS` | +0.05 | Could apply if tool result happens to carry matching `affect_tag` |
| Mood drift | `TORMENT_MOOD_DRIFT_QUERY_BONUS` | +0.04 | Does not apply (tool results have `type != "mood_drift"`) |
| Mood spiral dampening | `TORMENT_MOOD_SPIRAL_PENALTY_MAX` | −0.08 max | Does not apply (requires `affect_tag` in negative set) |

**Finding:** Self-thread (+0.06) and thread-window (+0.08) bonuses fire for tool-result memories. This means a recently ingested tool result gets up to +0.14 bonus from continuity alone — the same boost as the agent's own experiential memories. This is the primary semantic concern.

### 1.4 SRG Bonuses (lines 3347–3381)

Tool results don't carry SRG payloads unless explicitly set. No impact.

### 1.5 Collective Discount (Phase D3, lines 3383–3396)

```python
_h_is_collective = (
    _h_prov_raw == "collective"
    or (isinstance(_h_prov_raw, dict) and _h_prov_raw.get("source_type") == "collective_echo")
)
if _h_is_collective:
    final *= _coll_discount  # default 0.50
```

**Finding:** This is the existing provenance-aware scoring pattern. Tool results are NOT matched here (their `source_type` is `"tool_result"`, not `"collective_echo"`). This is the natural insertion point for a tool-result discount.

### 1.6 Memory-Plan Lane Weights (lines 3398–3418)

Tool results land in the `"core"` lane (private scope, not deep, not collective). If a memory plan supplies a core weight, it applies uniformly to all core hits including tool results.

**Finding:** No tool-result-specific lane exists. This is acceptable for now — adding a lane is a larger change.

### 1.7 Output Assembly (lines 3420–3562)

The returned hit objects are `dict(h)` with added fields: `final_score`, `motifs`, `motif_alignment`, `conflict_*`, `explain`. Provenance stays buried inside `h["payload"]["provenance"]` — it is **not** surfaced as a top-level field on the hit.

**Finding:** Consumers (MCP clients, the thinking controller) cannot easily see that a hit originated from a tool result without digging into the payload. This makes provenance-aware downstream behavior impossible without extra parsing.

### 1.8 Debug Provenance Endpoint (`/debug/provenance`)

Already supports filtering by `source_role` and `write_path`. Can find tool-result memories with `?write_path=tool_ingest`. Also supports `source_type` in the provenance dict. No changes needed here.

---

## 2. Policy Proposal

### 2.1 Principle

Tool-result memories are external observations, not self-knowledge. They should be retrievable and useful, but should not compete equally with the agent's experiential and identity memories in scoring. The same epistemic logic that discounts collective echoes applies: tool results are *informational*, not *autobiographical*.

### 2.2 Proposed Changes (Minimal, Phase-Appropriate)

#### Change A: Tool-Result Retrieval Discount

Add a provenance-aware discount for tool-result memories, following the exact pattern of the collective discount at Phase D3.

- **Location:** After the collective discount block (line ~3396)
- **Default discount:** `0.85` (15% reduction)
- **Env override:** `TORMENT_TOOL_RESULT_RETRIEVAL_DISCOUNT`
- **Rationale:** Lighter than the collective discount (0.50) because tool results are agent-requested observations, not cross-agent echoes. But still discounted to prevent tool-result memories from outranking the agent's own experiential thread when similarity scores are close.

#### Change B: Provenance Badge on Retrieved Hits

Surface `source_type` as a top-level field on returned hit objects so downstream consumers can see provenance without payload parsing.

- **Location:** In the hit assembly block (line ~3420)
- **Field:** `"provenance_type"` — extracted from `payload.provenance.source_type` if present, else `null`
- **Rationale:** The thinking controller, MCP clients, and the continuity debug system all benefit from knowing a hit's provenance origin at a glance. This is a read-only annotation — no scoring change.

#### Change C: Exclude Tool Results from Continuity Bonuses

The self-thread and thread-window bonuses exist to maintain the agent's *conversational* continuity — the sense that it stays "in the conversation." Tool results are not conversation; they're ingested observations. They should not receive continuity bonuses.

- **Location:** Self-thread bonus (line ~3235) and thread-window bonus (line ~3251)
- **Condition:** Skip bonus if `source_type == "tool_result"`
- **Rationale:** Without this, a burst of tool-result ingests (e.g., 10 API results in one session) would each get +0.14 continuity bonus, potentially crowding out the agent's actual conversational memories in retrieval.

### 2.3 What NOT to Change

| Item | Reason to defer |
|---|---|
| Tool-result memory-plan lane | Adding a 4th lane ("tool") is a structural change. Not appropriate for this phase. |
| Tool-result affect tagging | Tool results don't naturally carry affect. No change needed. |
| Tool-result compression behavior | Compression should treat tool results as normal memories. Defer until compression audit. |
| Debug/provenance endpoint | Already works for tool results via `?write_path=tool_ingest`. |
| SRG interaction | Tool results don't carry SRG state. No change needed. |
| Retrieval filtering (exclude tool results) | Too aggressive. Tool results should be findable, just appropriately weighted. |

---

## 3. Patch Plan

### Patch 1: Tool-result retrieval discount

**File:** `torment_service/fabric.py`
**Location:** After the collective discount block (~line 3396), before memory-plan lane weights

```python
# Phase D3b: tool-result retrieval discount
# Tool results are external observations, not self-knowledge —
# discount so they don't outrank organic experiential memories.
_h_is_tool_result = (
    isinstance(_h_prov_raw, dict)
    and _h_prov_raw.get("source_type") == "tool_result"
)
if _h_is_tool_result:
    try:
        _tool_discount = float(os.getenv("TORMENT_TOOL_RESULT_RETRIEVAL_DISCOUNT", "0.85"))
    except Exception:
        _tool_discount = 0.85
    final *= _tool_discount
```

### Patch 2: Provenance badge on hits

**File:** `torment_service/fabric.py`
**Location:** In hit assembly, after `hh = dict(h)` (~line 3420)

```python
# Provenance badge: surface source_type for downstream consumers
# Legacy bare-string provenance (pre-ProvenanceV1 artifact) is normalized
# to SOURCE_MEMORY so the badge surface always carries a value from
# VALID_SOURCE_TYPES (or None). See PROVENANCE_STATUS_REGISTRY_v2.4.x.md §7.2.
_hh_prov = (h.get("payload") or h).get("provenance") or h.get("provenance")
if isinstance(_hh_prov, dict):
    hh["provenance_type"] = _hh_prov.get("source_type")
    hh["provenance_tool_name"] = _hh_prov.get("tool_name")
elif isinstance(_hh_prov, str):
    hh["provenance_type"] = "memory"  # SOURCE_MEMORY (legacy bare string normalized)
else:
    hh["provenance_type"] = None
```

### Patch 3: Skip continuity bonuses for tool results

**File:** `torment_service/fabric.py`

**3a — Self-thread bonus (line ~3235):**
Add provenance check to existing condition:

```python
# Before (current):
if str(h.get("scope", "")) == "private" and str(h.get("agent_id", "")) == str(agent_id):
    type_bonus += self_bonus

# After:
_is_tool_result_hit = (
    isinstance(_h_prov_raw, dict) and _h_prov_raw.get("source_type") == "tool_result"
) if "_h_prov_raw" not in dir() else False
# ... but _h_prov_raw is computed later in the loop.
```

**Issue:** `_h_prov_raw` is currently extracted at line 3386, *after* the continuity bonuses. The provenance extraction must be hoisted earlier in the loop to be available for the continuity bonus guard.

**Resolution:** Move provenance extraction to the top of the `for h in all_hits` loop (line ~3180), right after `h` is bound. Then use it in both the continuity bonus guard and the discount block.

Revised approach:

```python
# At top of scoring loop (after line 3180: for h in all_hits:)
# Extract provenance early so all scoring phases can use it
_h_prov_raw = (h.get("payload") or h).get("provenance") or h.get("provenance")
_h_is_tool_result = (
    isinstance(_h_prov_raw, dict)
    and _h_prov_raw.get("source_type") == "tool_result"
)

# Then at self-thread bonus:
if (str(h.get("scope", "")) == "private"
    and str(h.get("agent_id", "")) == str(agent_id)
    and not _h_is_tool_result):
    type_bonus += self_bonus

# And at thread-window bonus:
if (thread_window_steps > 0 and thread_window_bonus > 0.0
    and str(h.get("scope", "")) == "private"
    and str(h.get("agent_id", "")) == str(agent_id)
    and not _h_is_tool_result):
```

### Patch 4: Tests

**File:** `tests/test_tool_result_ingest.py` (extend existing)

New test class: `TestToolResultRetrievalScoring`

- `test_tool_result_retrieval_discount_applied` — verify tool-result hit gets lower `final_score` than identical user memory
- `test_tool_result_no_continuity_bonus` — verify self-thread and thread-window bonuses don't fire for tool results
- `test_provenance_badge_on_hit` — verify `provenance_type` and `provenance_tool_name` appear on returned hits
- `test_tool_result_discount_env_override` — verify `TORMENT_TOOL_RESULT_RETRIEVAL_DISCOUNT` env var works

---

## 4. Deferred Items

| Item | Why deferred | When to revisit |
|---|---|---|
| Memory-plan tool-result lane | Structural change to lane system | When memory-plan lanes are extended generally |
| Tool-result compression policy | Compression doesn't inspect provenance yet | During compression audit phase |
| Tool-result expiry / TTL | Some tool results are ephemeral (weather, prices) | When TTL system is designed |
| Cross-agent tool-result sharing | Tool results are private-scope by default | When collective tool-result use cases emerge |
| Tool-result deduplication | Multiple ingests of same tool output | When dedup system exists |
| Retrieval explain block enrichment | Add provenance info to `explain` dict | Low priority, can be added anytime |

---

## 5. Doctrine Compliance

All proposed changes respect:

- **No capability boundary crossing:** These are retrieval scoring changes. No tool execution, no automation, no scheduling.
- **Memory, not action:** Tool results remain passive memory. The discount and badge are epistemic annotations.
- **Provenance as hard boundary:** All changes use existing provenance data. No new provenance fields introduced.
- **Spine authority preserved:** Retrieval scoring lives in Fabric, which is correct — Spine governs writes, Fabric governs reads.
- **Backward compatible:** `_h_prov_raw` extraction already handles the legacy bare-string case. Tool-result discount only fires on `source_type == "tool_result"` which only exists from v2.4.3+.

---

## Summary

Three narrow changes, one code-path hoist, four new tests. No new dependencies, no new endpoints, no capability expansion. The retrieval pipeline gains provenance awareness for tool-result memories through the same pattern already established for collective echoes.
