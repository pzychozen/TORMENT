# Validation Report — TORMENT v2.4.2 Changes

Date: 2026-04-04
Validated by: Claude (code-level behavioral review, not runtime testing)

---

## 1. Memory Plan → Real Query Integration

**Risk level: HIGH**
**Status: BUGS FOUND AND FIXED — recommend KEEP, gated behind existing flag**

### What it does
When `TORMENT_THINKING_ADVISORY=1`, the ThinkingController produces a MemoryPlan with lane-specific top_k and weight values. These now feed into `fabric.query()` to adjust per-source retrieval counts and score multipliers.

### Bugs found and fixed

**Bug 1 — top_k=0 still returned 1 hit.**
`memory_graph.py:search()` uses `k = max(1, top_k)`, so passing `top_k=0` (when plan says "don't retrieve from this lane") still returned 1 result.
*Fix:* Skip the search call entirely when lane top_k is 0.

**Bug 2 — Collective double-discount.**
Collective-provenance hits get Phase D3 discount (0.50x) and then lane weight (0.35x) = 0.175x total. Effectively invisible.
*Fix:* Lane weight skips collective hits (Phase D3 discount is sufficient).

**Bug 3 — Deep memory unconditionally queried.**
When plan sets deep_k > 0, deep store was queried regardless of whether core+shared already filled the budget. This promoted deep memories alongside full results instead of the intended gap-filler behavior.
*Fix:* Deep budget is now `min(deep_k, remaining_headroom)`. Still a gap-filler, but plan can raise the ceiling.

**Bug 4 — Archive lane weight never applied.**
The plan produces an "archive" lane weight, but no hit is classified as archive lane. Dead code — noted but not harmful.

### Behavioral analysis

- **Fallback when flag=0:** Clean. `memory_plan=None` → `_mp={}` → all lane top_k default to caller's top_k, weights empty → no multipliers applied. Identical to pre-change behavior. ✓
- **Identity starvation risk:** ThinkingController always sets core=6 (vs default top_k=8). Identity anchors get large type_bonus (+0.22 cumulative), so they dominate top-k even with fewer candidates. Low risk, but monitor.
- **Core lane weight:** Always 1.0 in current ThinkingController. Core memories are never down-weighted. ✓
- **Relational when disabled:** Plan sets relational top_k=0, weight=0.0. Search is now skipped entirely (Bug 1 fix). ✓

### How to disable
Set `TORMENT_THINKING_ADVISORY=0` (the default). All memory plan wiring is gated behind this single flag. Query behavior reverts to pre-change.

### Recommendation
**KEEP — already gated behind TORMENT_THINKING_ADVISORY=0 (off by default).** No behavioral change unless explicitly enabled.

---

## 2. Archivist Write-Back Loop

**Risk level: CRITICAL**
**Status: DISABLED BY DEFAULT — serious issues found**

### What it does
After the cognition pipeline runs, approved memory proposals from the Archivist are ingested back into the fabric via `fabric.ingest()`.

### Critical issues found

**Issue 1 — Recursion guard was broken.**
The anti-recursion check looked for `p.provenance.source` — a field that doesn't exist on the Provenance dataclass. The check never fired.
*Fix:* Changed to check `p.provenance.source_role == 'archivist_writeback'`. However...

**Issue 2 — Ingested memories have NO provenance.**
`fabric.ingest()` does not accept a provenance parameter. Written memories enter the fabric indistinguishable from user ingest. This means:
- Next pipeline run retrieves them
- They can generate more proposals → approved → written back
- Recursive self-reinforcement is possible over multiple pipeline runs

**Issue 3 — No disable switch existed.**
Added `TORMENT_ARCHIVIST_WRITEBACK` env var gate. Defaults to `0` (disabled).

### What was done
- Disabled by default behind `TORMENT_ARCHIVIST_WRITEBACK=1`
- Fixed recursion guard to use correct field name
- Cap of 5 proposals per run is in place
- Logging is in place for audit

### What remains to fix before enabling
1. `fabric.ingest()` needs a `provenance` parameter so written memories are tagged
2. Written memories need a queryable flag (e.g., `extra_payload.provenance_source = "archivist_writeback"`)
3. The recursion guard needs to check the INGESTED memory's provenance, not the proposal's — because proposal provenance is set by the role that created it, not by the write-back
4. Integration test: run pipeline twice, verify no self-reinforcement

### How to disable
`TORMENT_ARCHIVIST_WRITEBACK=0` (the default). Or remove `ingest_fn=fabric.ingest` from app.py's `/cognition/run` endpoint.

### Recommendation
**KEEP DISABLED until provenance tagging is plumbed through fabric.ingest().** The feature is structurally in place but not safe to enable.

---

## 3. Live Agent Memory Feedback Loop

**Risk level: LOW**
**Status: SAFE — one overcounting bug fixed, behavioral limitations noted**

### What it does
After generating a response, the live agent calls `/agent/feedback` with the EIDs of retrieved memory blocks and a used/not-used signal.

### Bug found and fixed

**Overcounting bug:** `blocks` captured all query results (up to top_k=8), but `format_context()` only injects the top 6 into the prompt. Feedback was reporting blocks 7-8 as "retrieved" when they were never in the prompt.
*Fix:* `blocks = result.get("results", [])[:6]` — now matches the prompt slice.

### Behavioral analysis

**The feedback is asymmetric and mostly inert.** The fabric's reinforcement signals require BOTH `used_successfully` AND `user_confirmed` for E_success. Since live agents always send `user_confirmed=False`:
- E_success is always 0 (no positive reinforcement, ever)
- E_noise fires only when NO blocks matched the response
- All other signals are 0

This means the feedback loop can only penalize bad retrieval (when nothing matches), never reward good retrieval. This is **safe against self-reinforcement** by design, though also not very useful.

**Heuristic accuracy:** The word-overlap heuristic (≥3 words or ≥20% overlap, words >4 chars) will overfire on common vocabulary. Since overfiring prevents E_noise from triggering, this makes the entire feedback loop even more inert. Not harmful, just not doing much.

**Rate limiting:** 2s cooldown is appropriate for voice turns (3-5s each). In text mode, rapid-fire input could exceed this, but the cooldown just skips feedback — no harm.

### How to disable
Remove the `torment_feedback(blocks, reply)` calls from the loops. Or the feedback endpoint itself is fail-soft (try/except swallows all errors).

### Recommendation
**KEEP — safe and non-distorting.** Consider adding `user_confirmed=True` in the future when there's an actual confirmation signal, but for now the asymmetric design prevents harm.

---

## 4. Geometric Context Harvester Wiring

**Risk level: LOW**
**Status: CORRECT — clean fallback, proper clamping**

### What it does
Reads real kernel state (`coh_ema`, `tear_score_ema`, `surv_ema`) and character state (`drift_score`, `seed_basin_phi`, `seed_basin_role`) and maps them into GeometricStanceContext's 5 normalized signals.

### Behavioral analysis

- **Fallback chain:** If kernel has no state (coh_ema=0.0): coherence=0.0 (very conservative). If character store has no state: identity_lock=0.5, ambiguity_tolerance depends on coherence. If both missing: returns None, stance policy uses pure deterministic scaffold. All fallbacks are safe and explicit. ✓
- **Clamping:** All values pass through `_clamp(v, 0.0, 1.0)`. No out-of-range risk. ✓
- **Read-only:** `_harvest_geometric_context` only reads from `fabric.kernel.mon` (persistent attributes) and `character_store.load_state()`. No mutations. ✓
- **Gate:** Only runs when `TORMENT_THINKING_ADVISORY=1`. ✓
- **Thread safety:** `kernel.mon` attributes are simple floats. `character_store.load_state()` does a file read. No locks needed for read-only access.

### How to disable
Set `TORMENT_THINKING_ADVISORY=0`. Harvester only runs inside `_advisory_thinking` and `/agent/query` advisory path, both gated.

### Recommendation
**KEEP — clean, read-only, properly gated.**

---

## 5. WarmupTracker Compaction

**Risk level: LOW**
**Status: CORRECT — no data loss risk**

### What it does
On first load, the WarmupTracker compacts its append-only JSONL file: reads all entries, deduplicates by EID (already done by `_ensure_loaded`), rewrites the file atomically.

### Behavioral analysis

- **No infinite recursion:** `_ensure_loaded()` → `self.compact()` → `self._ensure_loaded()` → guard returns immediately (self._states is not None). ✓
- **Atomic write:** Uses temp file + `Path.replace()`. If the write fails, the original file is unchanged. ✓
- **No thrashing:** Compaction threshold requires ≥20% savings AND ≥10 saved lines. A file with only unique entries (no duplicates) never compacts. ✓
- **Correctness:** `self._states` already holds the deduplicated latest state per EID from `_ensure_loaded`. Rewriting this dict to file preserves all current state. No data loss. ✓
- **Per-query creation:** WarmupTracker is instantiated fresh in each `fabric.query()` deep fallback. `_ensure_loaded()` runs once per instance. Compaction thus runs at most once per query that triggers deep fallback. In practice, this is rare. ✓

### How to disable
Remove the `self.compact()` call from `_ensure_loaded()`. Or set `self._compress_enable = False` on the fabric to disable deep memory entirely.

### Recommendation
**KEEP — low risk, correct behavior.**

---

## 6. Alignment Endpoint Alias

**Risk level: NONE**
**Status: TRIVIAL — just a route alias**

Added `@app.get("/spine/alignment")` as alias for existing `/spine/thinking_alignment/recent`. No behavioral change.

### Recommendation
**KEEP.**

---

## 7. Spirit Return Status Enhancement

**Risk level: NONE**
**Status: TRIVIAL — additional read-only stats**

Added warmth distribution buckets (cold/cool/warm/hot) to the existing `/workspace/{ws}/spirit-return/status` endpoint. Pure read, no mutations.

### Recommendation
**KEEP.**

---

## Summary: What to Enable by Default

| Change | Default State | Risk | Recommendation |
|--------|--------------|------|----------------|
| Memory Plan wiring | OFF (TORMENT_THINKING_ADVISORY=0) | Medium | KEEP gated, enable when ready to test |
| Archivist write-back | OFF (TORMENT_ARCHIVIST_WRITEBACK=0) | Critical | KEEP DISABLED until provenance fixed |
| Live agent feedback | ON (always runs) | Low | KEEP — safe due to asymmetric signals |
| Geometric harvester | OFF (TORMENT_THINKING_ADVISORY=0) | Low | KEEP gated with memory plan |
| Warmup compaction | ON (auto on load) | Low | KEEP |
| Alignment alias | ON | None | KEEP |
| Spirit return stats | ON | None | KEEP |

### Quick Rollback Paths

**Emergency — revert everything:**
```bash
git stash  # or git checkout -- .
```

**Disable memory plan + geometric harvester:**
```bash
export TORMENT_THINKING_ADVISORY=0  # default is now 1 (flipped 2026-04-16); set =0 to disable
```

**Disable archivist write-back:**
```bash
export TORMENT_ARCHIVIST_WRITEBACK=0  # already the default
```

**Disable live agent feedback:**
Remove `torment_feedback(blocks, reply)` calls from chat_limn.py and chat_bibs.py (4 locations each, grep for `torment_feedback`).

---

## Files Modified

### torment_fabric/torment_service/
- `fabric.py` — memory_plan parameter, lane-aware retrieval+scoring
- `spine.py` — geometric harvester, advisory thinking wiring
- `app.py` — /agent/query advisory path, alignment alias, spirit return stats
- `spirit_return.py` — WarmupTracker.compact()

### torment_fabric/cognition/
- `pipeline.py` — archivist write-back (disabled by default)

### live_agent/
- `chat_limn.py` — feedback loop, blocks slice fix
- `chat_bibs.py` — feedback loop, blocks slice fix
