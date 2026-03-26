# Design: Retention & Compression Policy — Phase 2.2

Status: **awaiting review** — please analyze and reply with approved/modified design
Date: March 26, 2026
Authors: pzychozen + Claude (Opus 4.6)

---

## Context

Phase 2.1 revealed three structural issues:

1. **Compression never fires** — event-gated triggers require corridor exits, but steady-state input keeps the kernel in-corridor indefinitely. 250 ingests, zero compression events.
2. **Half-life is metadata-only** — `half_life_days` is stored in each memory's payload and used for retrieval classification (identity vs relational vs situational), but is never applied as actual time-based strength decay. Strength stays at whatever value it was stored with, forever.
3. **No duplicate suppression** — near-identical text ingested multiple times creates separate memory records. Each gets a fresh embedding, fresh EID, fresh strength. There's no "reinforce existing instead of creating new."

This design proposes four policy additions. Each is independent and can be approved/rejected individually.

---

## Proposal A: Fallback Compression Triggers

**Problem:** Compression only fires on corridor exit, cycle stage change, or emergency tearing. If the kernel stays in-corridor (which it does under consistent input), compression never runs.

**Proposed solution:** Add two fallback triggers to `EventDetector.check()`, evaluated AFTER the existing geometric triggers (which remain preferred):

### A1. Count-based trigger
```
if memory_count(agent) > COMPRESS_COUNT_THRESHOLD:
    trigger = "count_overflow"
```
- `COMPRESS_COUNT_THRESHOLD` = 500 (env: `TORMENT_COMPRESS_COUNT_THRESHOLD`)
- Fires when private memory count exceeds threshold
- After firing, resets by compressing top candidates until count drops below 80% of threshold
- Geometric triggers still take priority

### A2. Step-based trigger
```
if (step - last_compression_step) > COMPRESS_STEP_INTERVAL:
    trigger = "periodic"
```
- `COMPRESS_STEP_INTERVAL` = 200 (env: `TORMENT_COMPRESS_STEP_INTERVAL`)
- Fires when N steps have passed since last compression (or since agent creation)
- Evaluates all eligible candidates but only compresses those scoring above 0.5 (don't force-compress good memories just because time passed)
- Geometric triggers still take priority

### Trigger priority order (unchanged for existing, extended for fallback):
1. emergency_tear (existing)
2. corridor_exit (existing)
3. cycle_stage_change (existing)
4. count_overflow (new — hard safety rail)
5. periodic (new — soft maintenance)

### Questions for review:
- Are 500 and 200 reasonable starting values?
- Should count_overflow be harder (compress down to 50%? 70%?) or softer (just compress top 20)?
- Should periodic trigger skip if no candidates score above the 0.5 floor? Or always compress at least 1?

---

## Proposal B: Half-Life Strength Decay

**Problem:** `half_life_days` is stored but never applied. Memories retain their original strength forever.

**Proposed solution:** Apply exponential decay at **query time**, not at write time. This keeps the stored data immutable (append-only JSONL) while making old memories naturally weaker in retrieval ranking.

### Formula:
```python
age_days = (now_ts - created_ts) / 86400.0
decay_factor = 2.0 ** (-age_days / half_life_days)
effective_strength = stored_strength * decay_factor
```

### Where to apply:
- In `MemoryGraph.search()` and `search_by_embedding()`: multiply the cosine similarity score by `decay_factor` before ranking
- In `retrieval_assembler.py`: use `effective_strength` for tier classification

### Properties:
- Half-life 1 day → 50% strength after 1 day, 25% after 2 days
- Half-life 7 days (relational) → 50% after 1 week
- Half-life 30 days (shared/default) → 50% after 1 month
- Half-life 365+ days (identity) → effectively permanent
- `last_reinforced` timestamp resets the clock when feedback confirms a memory's value

### Interaction with compression:
- Decayed memories naturally score higher in compression (lower effective strength → lower j_importance → higher j_score → more compressible)
- This creates a self-regulating cycle: unused old memories decay → become compression candidates → get compressed or exported to deep store

### Questions for review:
- Should decay multiply the cosine score (affects ranking order) or the strength field (affects write-gate comparison)?
- Should `last_reinforced` fully reset the decay clock, or partially (e.g., reset to 70% of fresh)?
- Is exponential decay the right model, or should there be a floor (e.g., `max(0.05, decayed_strength)`)?

---

## Proposal C: Duplicate Suppression via Reinforcement

**Problem:** Near-identical text creates new memories instead of strengthening existing ones.

**Proposed solution:** Pre-ingest similarity check. If the new embedding is very similar to a recent memory, reinforce that memory instead of creating a new one.

### Algorithm (in `fabric.ingest()`, before `spawn_memory()`):
```python
REINFORCE_SIM_THRESHOLD = 0.92  # env: TORMENT_REINFORCE_SIM_THRESHOLD
REINFORCE_RECENCY_WINDOW = 50   # only check last N memories

# Search recent memories for near-duplicates
recent_hits = graph.search_by_embedding(emb, top_k=3)
for hit in recent_hits:
    if hit["score"] >= REINFORCE_SIM_THRESHOLD:
        # Reinforce instead of creating new
        _reinforce_existing(graph, hit["eid"], new_strength=signals.strength, step=step)
        return {"stored": True, "reinforced": True, "eid": hit["eid"], ...}

# No match → create new memory as normal
```

### Reinforcement mechanics:
```python
def _reinforce_existing(graph, eid, new_strength, step):
    ent = graph.entities[eid]
    old_strength = ent.payload["strength"]
    # Asymptotic reinforcement: diminishing returns, cap at 0.98
    reinforced = min(0.98, old_strength + (1.0 - old_strength) * 0.3)
    graph.update_payload(eid, {
        "strength": reinforced,
        "last_reinforced": step,
        "reinforce_count": ent.payload.get("reinforce_count", 0) + 1,
    })
```

### Properties:
- 0.92 similarity threshold is high enough to only catch near-exact duplicates, not "similar topics"
- Reinforcement is asymptotic: 0.50 → 0.65 → 0.76 → 0.83 → ... never exceeds 0.98
- `reinforce_count` tracks how many times a memory was reinforced (diagnostic value)
- `last_reinforced` updates the decay clock (interacts with Proposal B)

### Questions for review:
- Is 0.92 the right threshold? Too low catches topically related but distinct memories. Too high misses paraphrases.
- Should reinforcement also update the summary (to the newer, potentially richer text)?
- Should reinforcement only apply within the same agent, or also cross-agent for shared memories?
- Should there be a recency window (only check last N memories) or check all?

---

## Proposal D: Retention Tiers

**Problem:** All memories are treated equally by compression. Identity-forming memories (high half-life, canon, seed) should be treated differently from ephemeral situational ones.

**Proposed solution:** Formalize the existing implicit tiers into explicit compression policy.

### Tier definitions:
| Tier | Criteria | Compression Policy |
|------|----------|--------------------|
| **Protected** | canon=True, kind∈{seed, identity, core_identity}, SRG crystal | Never compressed |
| **Identity** | half_life ≥ 365 days, tier="core_identity" | Only long-path (deep export), never short-path weakened |
| **Relational** | half_life ≥ 7 days, tier="relational" | Short-path at 0.7x (gentler than default 0.5x) |
| **Situational** | Everything else | Normal compression (0.5x short, full deep export) |
| **Echo** | provenance="collective" | Aggressive compression (0.3x short, deep export after 100 steps) |

### Where to apply:
- In `CompressionScorer._is_protected()`: already handles Protected tier
- In `CompressionScorer.score()`: adjust j_score based on tier
- In `CompressionRouter.route()`: tier-specific routing rules
- In `CompressionExecutor._execute_short_path()`: tier-specific strength multiplier

### Properties:
- Existing protection logic is unchanged (Protected tier already works)
- Identity memories get one-way deep export, never weakened in core
- Echoes are explicitly managed: they're low-amplitude by design and should be first candidates for compression
- Tier is derived at scoring time from payload fields, not stored separately (no migration needed)

### Questions for review:
- Should echo tier be even more aggressive (0.2x)?
- Should relational memories resist periodic compression entirely?
- Is the half_life boundary (7 days, 365 days) the right dividing line, or should it be based on canon/type fields only?

---

## Implementation Order

If all proposals are approved:

1. **B (decay)** first — it's read-path only, lowest risk, no stored data changes
2. **C (dedup/reinforce)** second — it's write-path, changes ingest behavior, most impactful for growth control
3. **A (fallback triggers)** third — depends on compression infrastructure already existing and working
4. **D (tiers)** fourth — refines compression scoring, depends on A being active

Each proposal can be implemented and tested independently. If only one is approved, the priority is **A** (fallback triggers) since it directly addresses the primary finding: compression never fires.

---

## Safety Rails (regardless of which proposals are approved)

These should be added regardless:
- **Hard memory cap**: `TORMENT_MAX_PRIVATE_MEMORIES=10000` — if count exceeds this, force-compress down to 8000. This is the last-resort safety net, not the primary mechanism.
- **Compression metrics in debug payload**: Add `compression_events_total`, `last_compression_step`, `memory_count` to the agent status endpoint so operators can monitor.

---

## Interaction Matrix

| | Decay (B) | Dedup (C) | Fallback triggers (A) | Tiers (D) |
|---|---|---|---|---|
| **Decay (B)** | — | Reinforcement resets decay clock | Decayed memories score higher for compression | Tier determines half_life which feeds decay |
| **Dedup (C)** | — | — | Fewer memories → less need for compression | N/A |
| **Triggers (A)** | — | — | — | Tier affects routing during triggered compression |
| **Tiers (D)** | — | — | — | — |

All interactions are synergistic, no conflicts. Each proposal independently improves the situation. Together they form a complete retention policy.
