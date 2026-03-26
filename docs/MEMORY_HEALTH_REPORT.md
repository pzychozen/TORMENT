# Memory Health Report — Phase 2.1

Status: completed
Date: March 26, 2026
Authors: pzychozen + Claude (Opus 4.6)
Diagnostic script: `examples/memory_health_diagnostic.py`

---

## Test Parameters

| Parameter | Value |
|-----------|-------|
| Ingest steps | 250 |
| Agents | 3 |
| Embedder | HashEmbedding (384-dim) |
| Adaptive DISP_SCALE | Enabled (k=2.0) |
| Compression | Enabled (min_step=30) |
| Hivemind | Disabled (isolated agent test) |
| Duplicate injection | ~10% intentional near-duplicates |
| Elapsed time | ~102s |

---

## Findings

### 1. Write Gate: 100% pass-through

Every single ingest (250/250) was stored. The write threshold is 0.55, but the minimum observed strength was 0.78 — a wide margin. Average strength was 0.94.

**Why:** The adaptive coherence pipeline + HashEmbedding produces consistently high-strength signals for well-formed text. The write gate effectively rubber-stamps everything with this embedder and text quality.

**Risk level:** Low for now. With real-world messy input (short fragments, noise, repeated filler), the gate will engage. The probabilistic soft-band (`write_band=0.08`) exists but never activates because all strengths clear the hard threshold easily.

**Recommendation:** No action needed. If strength inflation becomes an issue under STEmbedding, consider raising `write_threshold` from 0.55 to 0.65, or making it adaptive like DISP_SCALE.

### 2. Growth: Linear and unbounded

Memory count grows 1:1 with ingests — perfectly linear, no tapering. After 250 steps, each agent holds ~84 private memories. Extrapolating: 1000 ingests → 1000 memories per agent, 10000 → 10000.

**Why:** Nothing prunes memories. Half-life decay reduces strength over time but doesn't delete records. Compression is the intended pruning mechanism, but it isn't firing (see below).

**Risk level:** Medium. For development and demos (hundreds of ingests), this is fine. For production-scale agents running thousands of conversations, unbounded growth will degrade search performance (cosine similarity is O(n) with in-memory index) and bloat JSONL files.

**Recommendation:** Either (a) get compression firing reliably (see Finding 4), or (b) add a memory count cap per agent with LRU eviction as a safety net. The cap could be a config like `MAX_PRIVATE_MEMORIES=5000` that triggers forced compression when exceeded.

### 3. Duplication: 2.8% — healthy

7 inter-agent duplicates out of 250 stored memories (2.8%), all from the intentional duplicate injection. Zero intra-agent duplicates — the same agent never stored the same content twice.

**Why:** The system doesn't do pre-ingest dedup. The 2.8% rate comes from different agents independently ingesting the same text (a realistic hivemind scenario). Each agent correctly stores their own copy since they have independent memory spaces.

**Risk level:** Low. Inter-agent duplication is by design in the architecture (each agent has a private view). Shared memory consolidation happens via the proposal/convergence pipeline, not via dedup.

**Recommendation:** No action needed for private stores. For shared stores, the `search_by_embedding` canon conflict detection (which we just fixed in Phase 4.1) will catch high-similarity duplicates during proposal processing.

### 4. Compression: Zero events — dormant

Not a single compression event fired in 250 steps despite `TORMENT_COMPRESS_ENABLE=1`.

**Why:** Compression requires corridor exit transitions in the `tri_mod` signal (specifically: `in_corridor` going from True → False, `cycle_stage` changing, or `tearing_risk` exceeding 0.7). The TriOcta kernel's corridor dynamics depend on the phase evolution of the oscillator state. With 250 steps of consistently high-coherence input, the kernel stayed in-corridor the entire time — it never exited.

**Risk level:** Medium-high. This means compression is architecturally correct but operationally inactive for typical usage patterns. It only fires during phase transitions, which require topic shifts dramatic enough to break the coherence corridor.

**Recommendation:** Two options:

1. **Time-based fallback trigger**: Add a compression trigger that fires after N steps without a corridor exit (e.g., every 200 steps). This ensures compression eventually runs even under steady-state conditions.

2. **Memory count trigger**: Fire compression when private memory count exceeds a threshold (e.g., 500). This provides a growth safety valve independent of corridor dynamics.

Both can coexist with the existing event-gated triggers. This is the single most important finding — without one of these, memory grows without bound.

### 5. Motifs: Working correctly

Each ingest attaches to a domain motif (84 attachments for agent-000 in the research domain). New motifs are created on first ingest per domain, and subsequent ingests attach to existing motifs when embedding similarity exceeds the attach threshold.

Motif strength accumulates normally. No orphaned centroids or fragmentation issues observed at this scale.

**Recommendation:** No action needed. Will need to re-evaluate at 500+ motifs per domain.

### 6. Shared memory: N/A (hivemind disabled)

No shared memories or echoes were generated because `TORMENT_HIVEMIND_ENABLE` was not set. The packet gate correctly blocked all emission attempts. This is expected behavior for the isolated-agent test configuration.

The shared memory path should be tested separately with hivemind enabled (Phase 3.2 or a dedicated hivemind health diagnostic).

### 7. Domain routing: Correctly follows preferences

Each agent only stored memories in their preferred domain (agent-000 → research, 001 → operations, 002 → creative). This is because the diagnostic explicitly sets `domain_id` per ingest. When `domain_id` is omitted, the router's `rank_domains()` function scores embeddings against domain centroids.

**Recommendation:** Test with `domain_id=None` to verify the router distributes across domains naturally.

---

## Growth Curve

```
step   0: total=  1
step  25: total= 26
step  50: total= 51
step  75: total= 76
step 100: total=101
step 125: total=126
step 150: total=151
step 175: total=176
step 200: total=201
step 225: total=226
step 249: total=250
```

Slope: exactly 1.0 memories per ingest. No compression, no pruning, no dedup — pure accumulation.

---

## Summary

| Area | Status | Action Needed |
|------|--------|---------------|
| Write gate | Healthy (passes all well-formed input) | Monitor under STEmbedding |
| Growth rate | Linear, unbounded | Add fallback compression trigger |
| Duplication | 2.8% (all inter-agent, by design) | None |
| Compression | Dormant (no corridor exits) | Add time/count-based trigger |
| Motifs | Working | None at current scale |
| Shared memory | N/A (hivemind off) | Test separately |
| Domain routing | Deterministic when domain_id given | Test auto-routing |

**Top priority:** Add a fallback compression trigger (time-based or count-based) so that memory growth has a natural ceiling even when corridor dynamics don't produce exit events.

---

## Open Questions for ChatGPT

1. **Memory cap**: Should there be a hard cap on private memories per agent (e.g., 5000), or should compression + half_life be the only growth control? The current data shows neither fires during normal operation.

2. **Compression trigger**: Is a time-based fallback (every N steps) or a count-based fallback (every M memories) more aligned with the TriOcta physics? Or should both exist as independent triggers?

3. **Write gate sensitivity**: With adaptive k=2.0, all strengths are > 0.78. Should the write threshold be raised to create more selectivity, or is "store everything" the correct behavior for a memory system?
