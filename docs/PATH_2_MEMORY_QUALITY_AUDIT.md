# Path 2 — Memory Quality Audit

**Version:** v2.4.3
**Scope:** Retrieval quality, compression behavior, deep-memory usefulness
**Method:** Static code audit of scoring pipeline, compression system, and spirit return logic
**Goal:** Identify where memory noise, poor retention, weak compression, or unhelpful resurfacing are happening — then propose minimal tuning, not new features

---

## Part A — Retrieval Quality Over Time

### What the pipeline does

Every query runs through: base scoring (embedding similarity × strength/recency/motif modulation) → continuity bonuses (self-thread, thread-window, identity anchor, affect matching, mood drift) → SRG resonance → collective discount → tool-result discount → memory-plan lane weights → sort → top-k.

### What's already working well

1. **Base scoring formula is sound.** The `score_hit()` function in `scoring.py` uses similarity as the foundation and modulates rather than overrides — strength, recency, and motifs are additive multipliers on similarity, not independent axes. This means a low-similarity hit can't dominate just by being recent or strong.

2. **Collective discount (0.50×) is correctly aggressive.** Echoes are influences, not autobiography. Halving them prevents collective echoes from outranking organic memory. This is the right call.

3. **Tool-result discount (0.85×) and continuity bonus exclusion are well-placed.** Added in v2.4.3, these prevent tool outputs from accumulating scoring advantages they don't deserve (recency window bonuses, self-thread bonuses). The 15% discount is mild enough that genuinely relevant tool results still appear.

4. **Identity anchor tiering is smart.** Top-3 anchors get full +0.12, the rest get 0.12 × 0.35 = +0.042. This prevents anchor flooding — a common failure mode where seed memories crowd out everything contextual.

5. **Mood spiral penalty is a genuine innovation.** Detecting negative mood drift accumulation and penalizing old negative memories prevents rumination loops. The age-gate (`TORMENT_MOOD_SPIRAL_OLDER_THAN_STEPS = 250`) means recent negative context isn't penalized, only old stale negativity.

### Where noise can build up

**Finding 1: Thread-window bonus has no ceiling on accumulation.**

The thread-window bonus (+0.08 max, linear taper over 50 steps) applies per hit independently. In a long session where the agent ingests many private memories in quick succession, every recent private memory gets the bonus. Over time, this creates a "recency wall" — recent memories systematically outscore older, semantically better matches because they all carry the thread-window bonus.

The self-thread bonus (+0.06) compounds this: any private memory from the querying agent gets +0.06 unconditionally (plus up to +0.08 if recent). That's up to +0.14 bonus on recent private memories before any content relevance is considered.

**Severity:** Medium. The thread-window bonus tapers linearly, so it's not a sharp cliff. But at 50+ ingests per session, the recency wall is real.

**Finding 2: Motif alignment scoring may be stale.**

The motif alignment component in `score_hit()` uses `gamma = 0.20` weight — the second-strongest modulator after strength. But motifs are only updated on ingest, not on query. If the active motif landscape has shifted (basins collapsed, ridges formed), the alignment values on stored memories are frozen at their creation-time motif state. This means old memories can carry high motif alignment to motifs that no longer exist.

**Severity:** Low-medium. The coherence field recomputes on ingest, but stored alignment values aren't refreshed retroactively. In practice this matters more for long-running agents with active motif turnover.

**Finding 3: Recency bonus in base scoring decays too fast for medium-term memory.**

The recency component `1.0 / (1.0 + recency_days)` drops to 0.5 at day 1, 0.09 at day 10, 0.01 at day 100. With `beta = 0.10` weight, the actual impact is small — but the shape means there's essentially no recency signal at all beyond a week. Memories from 7 days ago and 365 days ago score identically on recency.

**Severity:** Low. The half-life decay system handles long-term strength reduction separately, so this isn't a functional gap — it's just a dead parameter beyond ~3 days.

**Finding 4: No diversity enforcement in final output.**

The final top-k selection is pure score-sorted. If 6 out of 8 top hits are about the same topic (e.g., a heavily reinforced experience), there's no mechanism to inject variety. This can lead to "echo chamber" retrieval where the same memory cluster dominates every query.

**Severity:** Medium. This is a known pattern in embedding-based retrieval. It matters most when an agent has a dominant memory cluster (e.g., a traumatic event, a recurring topic) that embeds similarly to many queries.

### What's not a problem

- **SRG scoring influence is off by default** (`TORMENT_SRG_ENABLE=0`). When enabled, the bonuses are small (3-8% multiplicative) and well-gated. Not a noise source.
- **Affect matching bonus is small** (0.05 × min confidence, typically +0.02-0.03). Not enough to distort ranking.
- **Memory-plan lane weights are clamped** to [0.1, 2.0]. Can't create infinite amplification.

---

## Part B — Compression Quality

### What the system does

Event-gated compression with 5 trigger types (emergency tear, corridor exit, cycle stage change, count overflow, periodic), tier-based routing (short-path strength reduction vs. long-path deep export), and 6 retention tiers (protected → identity → echo → tool_result → relational → situational).

### What's already working well

1. **Event-gating is the right trigger model.** Compression fires at geometric event boundaries (corridor exit, phase change), not on every ingest. This means compression happens at natural transition points where the kernel signals "something changed." The fallback triggers (200 steps, 400 count) provide safety nets without dominating.

2. **Protected tier is robust.** Canon memories, seed, identity, core_identity, and SRG crystals are all immune. The classification checks are thorough (flag, kind, tier, SRG crystal). False positives in the protected tier would be catastrophic, and the current logic is conservative.

3. **J-score / Z-score composite is well-balanced.** The 60/40 split between relational importance (retrieval count, strength, motif basin) and geometric compressibility (phi proximity, tension, role) means compression considers both "is this used?" and "is this geometrically settled?" Neither dimension alone can force compression.

4. **Tier-specific short-path multipliers give appropriate graduation.** Relational (0.7) is gentle, echo (0.4) is aggressive, tool_result (0.45) is between them. This reflects the actual value hierarchy.

### Where compression may underperform

**Finding 5: Periodic trigger floor (0.50) may be too generous.**

The periodic trigger (every 200 steps) only compresses candidates with composite score ≥ 0.50. Given the scoring formula, a 0.50 composite requires moderate compressibility across both J and Z scores. Memories that are low-value but geometrically stable (low phi, low tension) may score below 0.50 and persist indefinitely — even though they're not useful.

Example: a situational memory with moderate retrieval count (resists J-score) but near-zero phi (helps Z-score) might score 0.48 and survive every periodic pass. It occupies core memory without contributing meaningfully.

**Severity:** Low-medium. The count overflow trigger (400) and hard cap (10,000) prevent unbounded growth, but the space between "too low for periodic compression" and "count overflow" is where clutter accumulates.

**Finding 6: No re-scoring of compressed memories.**

Short-path compressed memories stay in core with reduced strength but are never re-evaluated for long-path export. A memory compressed via short-path at step 100 (age 50, below the 500-step long-path threshold) might still be in core at step 2000 with 0.25 strength — technically present but adding noise. The only way it leaves core is if a future compression pass routes it to long-path, but the routing check uses `COMPRESS_AGE_THRESHOLD = 500` against original age, not current age.

**Severity:** Medium. Short-path compressed memories accumulate as low-strength noise in core. They're individually weak but collectively add up.

**Finding 7: Echo memories wait 150 steps for long-path, but situational memories wait 500.**

`COMPRESS_ECHO_DEEP_AGE = 150` sends collective echoes to deep memory relatively quickly. But plain situational memories need both `composite ≥ 0.70` AND `age ≥ 500` for long-path routing. Situational memories aged 150-499 with moderate compression scores stay in core even though they're low-value.

**Severity:** Low. The short-path multiplier (0.50) reduces their strength, but they're still searched and scored.

**Finding 8: Compression max candidates per trigger is 20.**

`COMPRESS_MAX_CANDIDATES = 20` means at most 20 memories are evaluated per compression event. If a corridor exit produces 50 eligible candidates, only the top 20 by composite score are processed. The rest wait for the next event. At busy phases (high ingest rate during a corridor), this can create a backlog.

**Severity:** Low. Events happen frequently enough to drain the backlog, and the periodic fallback catches stragglers.

### What's not a problem

- **Tier classification logic is correct.** Tested in v2.4.3 with 12 dedicated tests. Tool-result tier sits correctly between echo and relational.
- **Hard cap (10,000) is sufficiently aggressive.** The 80% target ratio means 2,000 memories compressed per hard-cap event.
- **Cooldown (50 steps) prevents thrashing.** No runaway compression loops.

---

## Part C — Deep Memory / Spirit Return Usefulness

### What the system does

Long-path compressed memories are exported to JSONL + embedding shards. On query, deep memory is searched by cosine similarity (min 0.30), enriched with symbol interaction and warmth tracking, and returned in one of three modes: resonance (rare, vivid, 0.6 × warmth), surfacing (present-tense, 0.4 × warmth), or recollection (default, 0.1 × warmth).

### What's already working well

1. **Deep memory is a secondary filler, not a competitor.** The budget is `min(deep_k, remaining_slots)` — deep results only appear when core and shared don't fill top-k. This is exactly right. Deep memory should complement, not crowd out current memory.

2. **Symbol interaction is a clever quality gate.** The 19-pair symbol matrix means deep memories don't just return by embedding similarity — they need symbolic coherence between their birth state and the current kernel state. A memory born during `⊗` (contradiction) returning during `⊘` (release) gets a "resolution" interaction (+0.25 confidence). This makes returns feel meaningful rather than random.

3. **Warmth accumulation prevents cold returns.** First appearance starts at warmth 0.2 — meaning first-time recollection strength is only 0.1 × 0.2 = 0.02. A memory has to appear multiple times within 200 steps to accumulate enough warmth for resonance mode. This prevents sudden, disorienting returns of ancient memories.

4. **Sustained phase/corridor duration boost is well-gated.** Memories that spent 10+ steps in sustained geometric states get a warmth floor of 0.3 — ensuring important memories that were geometrically stable return with enough strength to be noticed.

### Where deep memory may underperform

**Finding 9: Min similarity threshold (0.30) is very permissive.**

The cosine similarity floor for deep memory returns is 0.30. For normalized embeddings, 0.30 is a very weak match — it means the memory and query share only loose topical overlap. Combined with the low recollection strength (0.1 × warmth), these weak matches are individually low-impact. But they still occupy retrieval budget slots and add noise to results.

**Severity:** Low-medium. Each weak match is nearly invisible, but if 3 of 8 returned hits are weak deep matches, the effective retrieval quality drops.

**Finding 10: Warmth window (200 steps) may be too short for real sessions.**

`WARMTH_WINDOW_STEPS = 200` means if a deep memory doesn't reappear within 200 steps, warmth resets to floor (0.2). For agents in long sessions with varied topics, a memory that appeared at step 500 and becomes relevant again at step 800 has lost all accumulated warmth. This makes resonance mode extremely rare in practice — it requires 3+ appearances within 200 steps with the right symbol interaction.

**Severity:** Medium. Resonance is supposed to be rare, but 200 steps may be too restrictive for multi-topic conversations where themes recur at intervals.

**Finding 11: No quality signal feeds back from deep memory returns to future compression.**

When a deep memory returns and is useful (evidenced by subsequent reinforcement or continued relevance), that signal doesn't influence future compression decisions. The compression scorer operates independently of spirit return outcomes. A memory type that consistently produces useful deep returns isn't recognized or protected.

**Severity:** Low. This is an optimization opportunity, not a current failure. The system works without it.

**Finding 12: Deep memory metadata preservation is selective.**

The export preserves: type, kind, tier, affect_tag, state_symbol, resonance_score, half_life, phase_duration_steps, corridor_duration_steps, symbol_trace, loop_type, phase_shift. But it does NOT preserve: motif_id, retrieval_count, or the full embedding payload metadata. Motif_id is referenced in deep_memory.py but assigned from compression candidate — if the motif has been reassigned by the time the memory is queried, the stored motif_id is stale.

**Severity:** Low. Spirit return primarily uses symbol interaction and warmth, not motif state.

---

## Summary: Biggest Memory-Quality Pain Points

| # | Finding | Area | Severity | Tunable? |
|---|---------|------|----------|----------|
| 1 | Thread-window bonus creates recency wall | Retrieval | Medium | Yes — reduce bonus or add ceiling |
| 4 | No diversity in final top-k | Retrieval | Medium | Yes — MMR or topic dedup |
| 6 | Short-path compressed memories never re-evaluated for long-path | Compression | Medium | Yes — age-based re-routing |
| 10 | Warmth window too short for multi-topic sessions | Deep memory | Medium | Yes — extend window |
| 5 | Periodic compression floor too generous | Compression | Low-medium | Yes — lower floor |
| 9 | Deep memory min similarity too permissive | Deep memory | Low-medium | Yes — raise threshold |
| 2 | Motif alignment may be stale | Retrieval | Low-medium | Needs design thought |
| 7 | Situational memories wait too long for long-path | Compression | Low | Yes — lower age threshold |
| 3 | Recency bonus dead beyond ~3 days | Retrieval | Low | Leave alone |
| 8 | Max 20 candidates per compression event | Compression | Low | Yes — raise limit |
| 11 | No feedback loop from spirit return to compression | Deep memory | Low | Deferred |
| 12 | Selective metadata in deep memory | Deep memory | Low | Leave alone |

---

## What Should Explicitly Be Left Alone

1. **Base scoring formula in `score_hit()`.** The weights (α=0.35, β=0.10, γ=0.20, δ=0.30) are reasonable and well-tested. Changing them would ripple through every test and every agent's memory behavior.

2. **Collective discount (0.50×).** Correctly aggressive. Don't soften.

3. **Tool-result discount (0.85×) and lifecycle policy.** Just shipped in v2.4.3. Let it run before touching.

4. **Protected tier classification.** Robust and conservative. No changes.

5. **Event-gated compression triggers.** The geometric event boundaries are the right firing model. Don't add time-based or API-triggered compression.

6. **Spirit return mode selection logic.** The three modes (resonance/surfacing/recollection) are well-graduated. Don't add more modes.

7. **SRG scoring influence.** Off by default, small when on. Leave for when SRG is more mature.

---

## Minimal Tuning Opportunities (Proposal — Pending Architecture Review)

These are candidates for Phase 2A implementation, not decisions. Each should be reviewed by the architecture layer before code changes.

### Tune 1: Thread-window bonus ceiling

**Current:** Up to +0.14 combined (self-thread + thread-window) on recent private memories.
**Proposal:** Add a per-query ceiling on total continuity bonus. Something like `max(total_continuity_bonus, 0.10)`. Alternatively, reduce thread-window bonus from 0.08 to 0.05.
**Why:** Prevents recency wall without breaking continuity feel.
**Risk:** Low. The bonus values are already env-configurable.

### Tune 2: Periodic compression floor reduction

**Current:** `COMPRESS_PERIODIC_FLOOR = 0.50` — only compresses scores ≥ 0.50 on periodic trigger.
**Proposal:** Lower to 0.40.
**Why:** Catches the "moderate compressibility but not quite 0.50" memories that currently accumulate.
**Risk:** Low. Protected tier is immune. Identity tier's -30% adjustment makes it unlikely to hit 0.40.

### Tune 3: Short-path re-evaluation on subsequent compression events

**Current:** Short-path compressed memories are never re-routed to long-path.
**Proposal:** On each compression event, check whether previously short-path-compressed memories now meet long-path criteria (age ≥ 500 since compression, score ≥ 0.70). If yes, re-route to deep.
**Why:** Prevents stale short-path memories from accumulating in core indefinitely.
**Risk:** Medium. Needs careful implementation — the re-evaluation must not re-compress already-deep memories.

### Tune 4: Deep memory similarity threshold

**Current:** `min_similarity = 0.30`
**Proposal:** Raise to 0.40.
**Why:** Reduces weak matches that waste retrieval budget slots.
**Risk:** Low. Strong matches still return. Weak matches were barely visible anyway (strength 0.02).

### Tune 5: Warmth window extension

**Current:** `WARMTH_WINDOW_STEPS = 200`
**Proposal:** Extend to 400 or 500.
**Why:** Allows themes that recur at longer intervals to accumulate warmth toward resonance.
**Risk:** Low. Warmth still caps at 1.0 and requires incremental appearances.

---

## What Not to Do in Path 2

Per the guiding doctrine:

- No new MCP surface work
- No automation or scheduling
- No provenance redesign
- No tool-result redesign
- No new memory classes
- No theory sprawl

Path 2 is observation → measurement → selective tuning. The five proposals above are the complete candidate set. The architecture review decides which (if any) to implement.
