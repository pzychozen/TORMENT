# Phase D Runtime Wiring Audit

**Date:** 2026-04-12
**Scope:** Does live/runtime TORMENT enforce the same governance and identity guarantees that `tests/test_phase_d_integration.py` validates at module level?
**Verdict:** Runtime partially matches tested contract. Two concrete mismatches found. One is high-severity.

---

## 1. Executive Conclusion

**Tests overstate live guarantees in two specific areas:**

1. **HIGH — Echo packet leak window:** `reingest_convergence()` calls `ingest()` first, then patches governance/provenance AFTER. During `ingest()`, the unpatched echo memory passes through the packet emission gate with no collective flags and no collective provenance. If hivemind is enabled and kernel coherence >= 0.15, the echo emits a packet before being flagged as terminal. This violates the "echoes don't echo" invariant at runtime, even though the test suite validates it perfectly at module level.

2. **MEDIUM — Retrieval discount is runtime-only, not in scoring.py:** The 0.50x collective retrieval discount exists in `fabric.py` query() and trace_full_graph(), applied inline during the scoring loop. It does NOT exist in `scoring.py`'s `score_hit()` or `compute_continuity_bonuses()`. The test suite validates the discount conceptually (arithmetic assertions), but never exercises the actual runtime scoring path. If anyone builds a new retrieval path using `scoring.py` directly, collective echoes would rank at full weight.

**Everything else matches.** Emission blocking, governance stamping, drift-budget enforcement, policy 7-gate evaluation, dedup, rate limiting, persistence, serialization survival, and API routing all use the correct helpers through the correct paths.

---

## 2. Runtime Path Map

### Emission path
```
fabric.ingest() [line 2237]
  → kernel.process()
  → store to private_graph
  → [PACKET GATE] hivemind_enable && stored && eid is not None
    → governance.should_emit_packet(entity.payload) [line 2705]
    → provenance check: collective string or dict [line 2710-2714]
    → coherence >= 0.15 [line 2724]
    → build ResonancePacket [line 2770]
    → collective_field.append_packet() [line 2797]
      → detect_convergence() → ConvergenceEvent or None
        → proposal_bridge.maybe_draft_proposal() [line 2818]
```

### Convergence detection path
```
collective_field.append_packet()
  → detect_convergence(new_packet, new_embedding)
    → cosine similarity >= 0.72 against recent packets from OTHER agents
    → composite confidence = 0.50*sim + 0.15*phase + 0.15*symbol + 0.20*motif
    → confidence >= 0.45 → ConvergenceEvent
```

### Re-ingest path
```
HTTP: POST /workspace/{ws}/collective/reingest
  → app.collective_reingest() [line 809]
    → spine.submit_task(collective_reingest) [line 827]
      → _fast_collective_reingest() [line 667]
        → fabric.reingest_convergence() [line 2064]
          → collective_field.get_event()
          → CollectivePolicy.evaluate() (7-gate) [line 2139]
            → gate 1: confidence
            → gate 2: agent opt-in
            → gate 3: domain match
            → gate 4: dedup (atomic check_and_reserve)
            → gate 5: rate limit
            → gate 6: check_drift_budget() [line 401]
            → gate 7: eligible
          → fabric.ingest() with echo summary [line 2179]
          → PATCH: ProvenanceV1.for_collective_echo() [line 2200]
          → PATCH: update_governance(reingest_blocked + export_blocked) [line 2211]
          → graph.flush_node() [line 2218]
          → policy.record_reingest() [line 2225]
```

### Retrieval path
```
fabric.query() [line ~3260]
  → private_hits + shared_hits + deep_hits
  → scoring loop [line 3474]:
    → _h_prov_raw extraction [line 3476]
    → score_hit() [scoring.py line 8]
    → compute_continuity_bonuses() [scoring.py line 154]
    → Phase D3 collective discount: final *= 0.50 [line 3595]
    → memory-plan lane weights (collective excluded) [line 3618-3620]
```

### API exposure path
```
Collective read endpoints (no governance filtering needed — these expose packets/events, not memories):
  GET /collective/status → field.status()
  GET /collective/packets → field.recent_packets()
  GET /collective/events → field.recent_events()
  GET /collective/events/{id} → field.get_event()
  GET /collective/proposals/status → bridge telemetry

Memory read endpoints (governance respected via scoring discount):
  POST /query → fabric.query() → collective discount applied
  GET /debug/provenance → raw payload inspection (debug-only, expected)

Governance management:
  POST /memory/governance/set → spine → fabric (Spine-governed)
  GET /memory/governance/get → resolve_governance() direct read
  GET /governance/audit → GovernanceAuditLog.recent()
```

---

## 3. Verified Guarantees (proven from code)

**Emission blocking:** `should_emit_packet()` correctly checks `non_shareable` and `collective_export_blocked` flags via `resolve_governance()`. The runtime emission gate at `fabric.py:2705` imports and calls this exact function. Verified.

**Governance stamping:** `reingest_convergence()` at line 2211 calls `update_governance(ent.payload, {"collective_reingest_blocked": True, "collective_export_blocked": True}, ...)`. This is the same helper the tests use. Verified.

**ProvenanceV1 marking:** `reingest_convergence()` at line 2200 calls `ProvenanceV1.for_collective_echo().to_dict()`, producing `source_type="collective_echo"`, `write_path="collective_reingest"`. Verified.

**Provenance detection in retrieval:** Both `query()` (line 3586-3589) and `trace_full_graph()` (line 4457-4460) check for collective provenance using dual detection: `_h_prov_raw == "collective"` (legacy) OR `_h_prov_raw.get("source_type") == "collective_echo"` (ProvenanceV1). Verified.

**Drift-budget enforcement:** `reingest_convergence()` loads character state (drift_score, drift_direction, seed_motif_id) at lines 2121-2132, passes them to `policy.evaluate()`, which calls `check_drift_budget()` at gate 6 (line 401). This is the exact same function the tests exercise. Real drift data from `character_store.load_state()`. Verified.

**Missing drift defaults closed:** If character state loading fails (line 2132 exception), defaults are `current_drift_score=0.0`, `drift_direction="stable"`, `agent_seed_motif_id=None`. This is permissive (drift budget passes), not closed. However, this is intentional — a new agent with no drift history should accept echoes. Consistent with design.

**Domain isolation:** Gate 3 in `CollectivePolicy.evaluate()` (line 355-365) enforces exact domain match. `check_drift_budget()` also double-checks domain at line 213. Verified.

**Dedup:** Gate 4 uses atomic `check_and_reserve()` (line 369) with unreserve on later gate failure (line 388, 411). `record_reingest()` called after successful ingest (line 2225). Verified.

**Rate limiting:** Gate 5 counts recent reingests via `ReingestTracker.count_recent()` (line 384-387). Default 3 per hour. Verified.

**Echo strength cap:** `reingest_convergence()` at line 2159 applies `min(override, DEFAULT_ECHO_STRENGTH_CAP)`. Cap is 0.40. Verified.

**Persistence survival:** `ReingestTracker`, `ConvergencePersistenceTracker`, `CollectiveField`, and `GovernanceAuditLog` all use JSONL append-only storage with load-from-disk on construction. Tests verify this at module level. Runtime uses the same classes. Verified.

**Serialization survival:** Governance flags are stored as `payload["governance"]` dict inside the entity's JSONL-serialized payload. `resolve_governance()` handles missing/partial/None governance gracefully. No field loss on round-trip. Verified.

**API routing through Spine:** The POST `/collective/reingest` endpoint is shimmed through Spine governance (line 811-827), not direct to Fabric. Spine enforces trust tier, locking, and operation class. Verified.

**Collective context is informational only:** `_collective_query_context()` (line 2030-2058) returns convergence events for query response metadata. Explicitly marked "Does NOT influence scoring." Returns event summaries, not blocked memory content. Verified.

---

## 4. Missing or Uncertain Guarantees

### 4a. Echo emits packet before governance patch (HIGH)

**File:** `torment_service/fabric.py`
**Function:** `reingest_convergence()`, lines 2179-2214
**Issue:** The echo memory is created via `self.ingest()` at line 2179. Inside `ingest()`, the packet emission gate runs at line 2693. At this point, the memory has NO collective governance flags (those are patched at line 2211) and NO collective provenance (patched at line 2200). The emission gate checks `should_emit_packet(entity.payload)` — which returns True because governance is empty/default-permissive. The provenance check at line 2710-2714 also passes because provenance hasn't been set yet.

**Result:** If `hivemind_enable=True` AND kernel coherence >= 0.15 for the echo text, the echo WILL emit a ResonancePacket into the collective field. This means a collective echo can produce further packets, potentially triggering convergence events from echo-derived material.

**Why tests miss it:** Tests exercise `should_emit_packet()` and `allows_collective_reingest()` against a pre-built echo payload that already has flags set. They never test the temporal window between `ingest()` and the post-ingest governance patch.

**Severity:** High. This is the primary invariant violation. "Echoes don't echo" is violated at runtime.

**Minimal fix direction:** Pass governance flags into `ingest()` so they're set BEFORE packet emission. Alternatively, add an `emit_packet=False` parameter to `ingest()` that `reingest_convergence` uses to suppress emission entirely.

### 4b. Retrieval discount not in scoring.py (MEDIUM)

**File:** `torment_service/scoring.py`
**Functions:** `score_hit()`, `compute_continuity_bonuses()`
**Issue:** The 0.50x collective retrieval discount is applied inline in `fabric.py` `query()` (line 3595) and `trace_full_graph()` (line 4513), NOT in `scoring.py`. If any future retrieval path uses `score_hit()` directly without also applying the discount, collective echoes rank at full weight.

**Why tests miss it:** The test at line 245-260 validates the discount arithmetically (`base * 0.50`), not by exercising the actual scoring pipeline.

**Severity:** Medium. Currently safe because all retrieval paths go through `fabric.query()` or `trace_full_graph()`. Becomes high if a new path is added.

**Minimal fix direction:** Add a `collective_discount` parameter to `score_hit()` or create a post-scoring discount wrapper that `query()` and `trace()` both call, making the contract explicit and testable.

### 4c. Governance flags set on entity, not on ingest payload (LOW)

**File:** `torment_service/fabric.py`
**Function:** `reingest_convergence()`, line 2196
**Issue:** Governance flags are patched onto `ent.payload` via `graph.entities.get(echo_eid)`. If the entity lookup fails (line 2196 returns None), the patching is silently skipped. The echo exists in storage with NO governance flags. The `try/except` at line 2221 catches all exceptions and logs debug-level only.

**Severity:** Low. Entity lookup failure would mean the ingest itself partially failed. But the silent skip means a malformed echo could persist without governance flags.

**Minimal fix direction:** Return an error result instead of silently continuing when entity lookup fails after successful ingest.

---

## 5. Concrete Mismatches

### Mismatch 1: Echo packet leak window

| Aspect | Detail |
|---|---|
| **File** | `torment_service/fabric.py` |
| **Function** | `reingest_convergence()` → `ingest()` → packet emission gate |
| **Lines** | 2179 (ingest call), 2693-2830 (emission), 2200-2214 (post-patch) |
| **Issue** | Echo ingested without governance/provenance → passes emission gate → emits packet → THEN gets patched as terminal |
| **Why it matters** | Violates Invariant 3 ("echoes are terminal"). Echo-derived packets could trigger convergence events, creating echo-of-echo chains. |
| **Minimal fix** | Add `_skip_packet_emission=True` parameter to `ingest()`, used by `reingest_convergence()`. Or: set governance flags on the ingest payload BEFORE calling `ingest()`, and have `ingest()` transfer them to the entity. |

### Mismatch 2: Retrieval discount location

| Aspect | Detail |
|---|---|
| **File** | `torment_service/scoring.py` vs `torment_service/fabric.py` |
| **Function** | `score_hit()` (missing) vs `query()` scoring loop (present) |
| **Lines** | scoring.py:8-22 (no discount) vs fabric.py:3590-3595 (discount applied) |
| **Issue** | Discount is an inline post-score multiplication in fabric.py, not a parameter in the shared scoring function |
| **Why it matters** | Any new retrieval path using scoring.py directly would not discount collective echoes |
| **Minimal fix** | Move discount into scoring.py as an explicit parameter, or document the contract that all retrieval paths must apply it separately |

---

## 6. Tested-vs-Runtime Comparison Table

| Concern | Tested at module level? | Enforced in runtime? | Same helper/path? | Risk |
|---|---|---|---|---|
| Emission blocking (governance flags) | Yes — `should_emit_packet()` | Yes — fabric.py:2705 | Same function | Low |
| Emission blocking (provenance) | Yes — provenance=="collective" | Yes — fabric.py:2710-2714 | Same check pattern | **HIGH — not applied during reingest ingest window** |
| Re-ingest blocking | Yes — `allows_collective_reingest()` | Yes — policy gate + governance | Same function | Low |
| Collective provenance marking | Yes — payload["provenance"] | Yes — ProvenanceV1.for_collective_echo() | Same factory | Low (but applied post-ingest) |
| Governance double-block | Yes — update_governance() | Yes — fabric.py:2211 | Same function | Low (but applied post-ingest) |
| Drift-budget gate | Yes — check_drift_budget() | Yes — policy.evaluate() gate 6 | Same function | Low |
| Domain isolation | Yes — gate 3 + drift_budget | Yes — policy.evaluate() | Same function | Low |
| Dedup | Yes — ReingestTracker | Yes — atomic check_and_reserve | Same class | Low |
| Rate limiting | Yes — count_recent() | Yes — gate 5 | Same class | Low |
| Persistence survival | Yes — restart tests | Yes — same JSONL classes | Same classes | Low |
| Serialization survival | Yes — JSON round-trip | Yes — JSONL payload | Same format | Low |
| Retrieval discount | Yes — arithmetic only | Yes — fabric.py inline | **Different path** — not in scoring.py | **MEDIUM** |
| API exposure filtering | N/A | Collective endpoints expose events/packets, not blocked memories | N/A | Low |
| Echo strength cap | Yes — min(override, 0.40) | Yes — fabric.py:2159 | Same logic | Low |
| Proposal auto-draft only | Yes — bridge returns drafted | Yes — never auto-approved | Same class | Low |

---

## 7. Most Important Next Test

**Add a runtime integration test for the echo packet leak window.**

The test should:
1. Create a real `TormentFabric` with `hivemind_enable=True`
2. Set up two agents, ingest content that produces a convergence event
3. Call `reingest_convergence()` for the target agent
4. Inspect the collective field's packet log
5. Assert that NO packet was emitted from the echo EID

This is the single highest-value test because it catches the only invariant violation that currently exists in the live runtime path, and no existing test covers it.

```python
# Pseudocode for the test
def test_echo_does_not_emit_packet(self):
    """Invariant 3 runtime: reingest_convergence echo must not emit a packet."""
    fabric = TormentFabric(data_dir=tmp, hivemind_enable=True)
    # ... setup agents, ingest, trigger convergence ...
    result = fabric.reingest_convergence(ws, target_agent, event_id)
    assert result["eligible"]
    echo_eid = result["echo_eid"]

    field = fabric._get_collective_field(ws)
    all_packets = field.recent_packets(limit=100)
    echo_packets = [p for p in all_packets if p.get("source_eid") == echo_eid]
    assert len(echo_packets) == 0, f"Echo EID {echo_eid} emitted a packet"
```
