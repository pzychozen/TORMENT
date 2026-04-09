# Spirit Return and Reflection — Complete Design Document

TORMENT v2.2

---

## 1. What This System Does

Spirit return is how compressed memories come back to life. Spirit reflection is how the system remembers that they came back and mattered.

Together, they form a closed loop: deep memories return through symbolic resonance (Phase 7), and when those returns actually shape a response, the system records the event as a derived artifact (Phase 7b). The original memory is never touched. The reflection is never eligible to become a spirit return itself. The hierarchy is preserved.

This is the first system in TORMENT that records temporal continuity — the fact that "a memory came back and changed something" — without duplicating, mutating, or inflating the original memory.

---

## 2. Architecture Overview

```
Deep Memory Store                    Spirit Return (Phase 7)
┌─────────────┐                     ┌───────────────────────┐
│ memories.jsonl│ ──── query ──────▶│ Symbol Interaction    │
│ embeddings/  │                    │ Matrix (19 rules)     │
│ (per agent)  │                    │         │             │
└─────────────┘                     │    Return Mode        │
       ▲                            │  resonance/surfacing/ │
       │ never mutated              │  recollection         │
       │                            │         │             │
       │                            │    Warmup Tracker     │
       │                            │  (warmth accumulation)│
       │                            │         │             │
       │                            │    Enrichment         │
       │                            │  → SpiritReturnMemory │
       │                            │  → query hit dict     │
       │                            └─────────┬─────────────┘
       │                                      │
       │                            ┌─────────▼─────────────┐
       │                            │ Retrieval Assembler    │
       │                            │  - tier classification │
       │                            │  - voice cues          │
       │                            │  - token budgeting     │
       │                            └─────────┬─────────────┘
       │                                      │
       │                             assembled context
       │                                      │
       │                                      ▼
       │                            ┌─────────────────────┐
       │                            │   LLM Response      │
       │                            │   (external)        │
       │                            └─────────┬───────────┘
       │                                      │
       │                            ┌─────────▼───────────┐
       │                            │ Spirit Reflection    │
       │                            │ (Phase 7b)           │
       │                            │  1. Extract hits     │
       │                            │  2. Score influence   │
       │                            │  3. Build reflection  │
       │                            │  4. Anti-echo guard   │
       │                            └─────────┬───────────┘
       │                                      │
       │                            ┌─────────▼───────────┐
       │     separate storage ─────▶│ spirit_reflections/  │
       │     (never contaminates)   │   reflections.jsonl  │
       │                            └─────────────────────┘
       │
  no backflow ──── reflections CANNOT become spirit returns
```

---

## 3. Spirit Return (Phase 7) — How Memories Come Back

### 3.1 When It Fires

During `fabric.query()`, when private + shared graph hits are insufficient, the system reaches into the deep memory store. These deep hits are not returned raw — they pass through the spirit return enrichment pipeline.

### 3.2 Symbol Interaction Matrix

Every deep memory carries a `birth_symbol` — the kernel's coherence field symbol at the moment the memory was created. When the memory returns, its birth symbol interacts with the kernel's `current_symbol` through a 19-rule interaction matrix.

Each rule maps a `(birth_symbol, current_symbol)` pair to an interaction type, a human-readable flavor text, and a confidence boost:

| Birth | Current | Interaction | Flavor | Boost |
|-------|---------|-------------|--------|-------|
| ⊗ | ⊘ | resolution | a difficult memory dissolves into clarity | 0.25 |
| ⊗ | ◠ | integration | old tension finds a place to rest | 0.20 |
| ◠ | ⊗ | nostalgia_under_stress | a warm memory returns but the present is harsh | 0.10 |
| ✧ | ✧ | deepening | an old insight deepens into something richer | 0.25 |
| ◯ | ◈ | fulfilled | something that was once only potential has crystallized | 0.20 |
| ⊘ | ⊗ | resurgence | something released returns with new friction | 0.05 |
| ◠ | ∿ | outgrown | a place of comfort has become too small | 0.10 |
| ✧ | ◈ | crystallized | an old flash of understanding has become solid ground | 0.20 |
| ∿ | ◠ | found_home | wandering led somewhere that feels like belonging | 0.20 |
| ⋮ | ✧ | breakthrough | something familiar suddenly reveals a new angle | 0.20 |
| ◈ | ⊗ | disrupted | something once stable has been shaken | 0.05 |
| ⊘ | ◠ | peace | what was let go has become a source of quiet warmth | 0.20 |
| ◯ | ∿ | unfolding | something new has begun to spread out and wander | 0.15 |
| ⋮ | ⊗ | grinding | familiar ground has turned rough | 0.05 |
| ∿ | ✧ | discovery | wandering has led to a moment of clarity | 0.20 |
| ◈ | ⊘ | letting_go | something once held together has been gently released | 0.15 |
| ⊗ | ◯ | reset | tension has broken and something new begins | 0.15 |
| ◠ | ✧ | illumination | deep comfort gives rise to understanding | 0.20 |
| ⋮ | ◈ | rooted | familiar ground settles into something more solid | 0.15 |

Unmapped pairs: same symbol → `echo` (boost 0.15), different symbol → `contrast` (boost 0.0).

### 3.3 Return Modes

How the character experiences the returning memory:

**Resonance** — rarest mode. The birth symbol's interaction is a resonance candidate (confidence boost ≥ 0.20) AND warmth ≥ 0.5. Present-tense, vivid, déjà vu quality. Hit strength = 0.6 × warmth. SRG crystal memories always force resonance.

**Surfacing** — the memory was compressed to core (short-path) and warmth ≥ 0.3. Present-tense, gentle emergence. Hit strength = 0.4 × warmth.

**Recollection** — default fallback. Past-tense, distilled. Hit strength = 0.1 × warmth.

### 3.4 Warmup Mechanics

Deep memories don't return at full intensity on first appearance.

| Parameter | Value |
|-----------|-------|
| Warmth floor (first appearance) | 0.2 |
| Increment per subsequent retrieval | +0.15 |
| Warmup window | 400 steps |
| Warmth cap | 1.0 |
| Sustained corridor warmth floor | 0.3 (if phase/corridor duration ≥ 10 steps) |
| SRG heartbeat class A boost | +0.15 floor |

The `WarmupTracker` persists warmup state per EID to `warmup_state.jsonl` (append-only, JSONL, per agent).

### 3.5 Enrichment Pipeline

```
deep_memory + current_kernel_symbol + warmup_state + compressed_in_core
    │
    ▼
enrich_deep_memory_hit()
    │ → extract birth_symbol from metadata
    │ → compute_symbol_interaction(birth, current)
    │ → compute warmth (with sustained corridor boost + SRG boost)
    │ → select_return_mode()
    │ → compute resonance confidence
    │
    ▼
SpiritReturnMemory dataclass
    │
    ▼
inject_spirit_return_into_hit()
    │ → convert to query hit dict with all spirit return fields
    │
    ▼
query hit dict (compatible with existing merge pipeline)
```

### 3.6 Tier Classification in Retrieval Assembler

Spirit return hits are classified into context tiers:

| Return mode | Warmth | Tier |
|-------------|--------|------|
| resonance | ≥ 0.5 | identity_context |
| surfacing | ≥ 0.3 | relational_context |
| recollection | any | situational_context |

Voice cues are injected as text annotations: `[Voice: present-tense, vivid, déjà vu...]` for resonance, `[Voice: present-tense, gentle...]` for surfacing, `[Voice: past-tense, distilled...]` for recollection. Symbol interaction flavor is injected as `[Flavor: ...]`.

---

## 4. Spirit Reflection (Phase 7b) — Recording That Return Mattered

### 4.1 Why This Exists

Spirit return (Phase 7) reads from deep memory and enriches retrieval. But it has no write-back — the system cannot record that a returning memory *actually influenced* the conversation. Without this, temporal continuity is invisible: the system can bring back memories but cannot learn from the fact that they came back and shaped something.

Spirit reflection closes this gap. It records the *event of return*, not the original memory again.

### 4.2 Design Principles

These are non-negotiable constraints:

1. **Do not mutate original deep memories.** Deep memory is source-of-truth for compressed experience. Reflections never touch it.
2. **Do not automatically re-ingest every returned memory.** Most returns are incidental — only returns that demonstrably influenced the response qualify.
3. **Do not duplicate raw summaries back into memory.** The reflection summary describes the event ("A prior deep memory resurfaced in resonance mode..."), never copies the original content.
4. **Do not let derived reflections become top-tier spirit-return sources.** `eligible_for_spirit_return = False`, enforced at deserialization.
5. **Do not break current retrieval precedence.** Reflections are in separate storage, not in the query path. Identity → relational → situational → archive ordering is unchanged.

### 4.3 Four-Stage Pipeline

**Stage 1 — Extract** (`extract_spirit_return_candidates`):

Pull hits with `from_spirit_return: True` from assembled context blocks. Anything with `generation_depth >= 1` is excluded — reflections cannot spawn reflections.

**Stage 2 — Score** (`score_spirit_return_influence`):

Conservative heuristic measuring how much the spirit return shaped the response:

| Component | Weight | What it measures |
|-----------|--------|------------------|
| Lexical overlap | 40% | Recall: what fraction of candidate summary tokens appear in the response. Ultra-short candidates (< 5 tokens) are dampened proportionally. |
| Concept alignment | 30% | Whether spirit return flavor words or mode-related vocabulary appear in the response. |
| Warmth bonus | 15% | Warmer memories are more likely to have been influential (max 0.2 contribution). |
| Resonance mode bonus | 15% | Resonance returns are vivid and more likely to shape responses (+0.15). |

Default threshold: 0.30. Designed to prefer false negatives over false positives. A healthy v1 should reject most candidates.

**Stage 3 — Build** (`build_spirit_reflection_event`):

Create a `SpiritReflectionEvent` with a derived summary, truncated response excerpt, cooldown key, and all spirit return metadata. The summary is always a new sentence describing the event, never a copy of the original.

**Stage 4 — Guard** (`should_store_reflection`):

Anti-echo checks in order:

1. Generation depth must be exactly 1 (reflections of reflections blocked)
2. Influence score must meet threshold (default 0.30)
3. Cooldown: same `source_eid:mode:interaction` key must not appear within cooldown window (default 50 steps)
4. Duplicate suppression: same source_eid + same step = blocked

### 4.4 Data Model

```
SpiritReflectionEvent:
    eid                         — unique ID for this reflection (hash-derived)
    source_eid                  — original deep memory that returned
    derived_from_spirit_return  — always True
    generation_depth            — always 1
    created_step                — when this reflection was created
    created_at                  — timestamp
    query_text                  — user query that triggered the return
    response_excerpt            — truncated trace (≤ 200 chars)
    return_mode                 — resonance / surfacing / recollection
    warmth_score                — warmth at time of return
    symbol_interaction          — interaction type from the matrix
    spirit_return_flavor        — human-readable flavor
    influence_score             — 0–1, how much it shaped the response
    influence_reason_tags       — why: lexical_overlap, concept_alignment, etc.
    summary                     — derived description of the return event
    cooldown_key                — dedup: "source_eid:mode:interaction"
    eligible_for_spirit_return  — always False (tamper-resistant)
```

### 4.5 Storage

Reflections are stored in `data/agents/{agent_id}/spirit_reflections/reflections.jsonl` — completely separate from `deep_memory/`. The `SpiritReflectionStore` provides:

- `store(event)` — append to JSONL
- `recent(n)` — last N events
- `all_events()` — full history
- `stats()` — total count, unique sources, average influence, mode distribution

CWE-22 path traversal guard on initialization.

### 4.6 API Endpoints

**Process reflections (post-response):**

```
POST /workspace/{ws}/spirit-reflections/process
Body: {
    workspace_id, agent_id, query_text, response_text,
    blocks: [...],      // assembled context blocks from /retrieve
    current_step: int,
    influence_threshold: float (optional, default 0.30),
    cooldown_steps: int (optional, default 50)
}
Response: {
    ok: bool,
    reflections_stored: int,
    reflections: [...],
    store_stats: {...}
}
```

Fail-soft: never raises HTTP exceptions. Returns `{"ok": false, "error": "..."}` on any failure.

**Diagnostics (read-only):**

```
GET /workspace/{ws}/spirit-reflections/status?agent_id=X
Response: {
    ok: bool,
    stats: { total_reflections, unique_sources, avg_influence, mode_counts },
    recent: [last 10 events]
}
```

---

## 5. Anti-Echo Protection Summary

The reflection system has multiple independent protections against memory loops:

| Protection | Mechanism | Where enforced |
|------------|-----------|----------------|
| No spirit return eligibility | `eligible_for_spirit_return = False` | Dataclass default + `from_dict()` forces False |
| No recursive reflections | `generation_depth` capped at 1 | `extract_spirit_return_candidates` filters `depth >= 1` |
| Influence threshold | Score must reach 0.30 | `should_store_reflection` rule 2 |
| Cooldown window | Same cooldown_key blocked for 50 steps | `should_store_reflection` rule 3 |
| Duplicate suppression | Same source + same step blocked | `should_store_reflection` rule 4 |
| Separate storage | Reflections in own JSONL, not deep_memory | `SpiritReflectionStore` path isolation |
| Short-candidate dampening | Candidates < 5 tokens get reduced overlap score | `_lexical_overlap` dampener |
| No deep memory mutation | Original memories never modified | By design — reflections are append-only separate artifacts |
| Fail-soft endpoint | If anything breaks, main path unaffected | `try/except` in process endpoint |

---

## 6. What This System Does NOT Do

Explicitly held back in v1:

- **No identity mutation.** Reflections do not alter character seeds, drift vectors, or gravity correction.
- **No deep memory rewrite.** The original compressed memory is never modified by a reflection.
- **No embedding index.** Reflections cannot be retrieved via vector similarity — they are structured logs, not query targets.
- **No reflection-aware retrieval.** Nothing in the query/retrieve pipeline reads reflections for scoring or ranking.
- **No recursive reflection.** Reflections cannot spawn further reflections. Generation depth is hard-capped at 1.
- **No automatic invocation.** The caller must explicitly hit the `/spirit-reflections/process` endpoint after generating a response.

These are future possibilities that should only be considered after v1 has been observed with real traffic and acceptance/rejection rates are understood.

---

## 7. Test Coverage

| Test file | Count | What it covers |
|-----------|-------|----------------|
| `test_spirit_return.py` | 53 | Full spirit return pipeline: symbol matrix, modes, warmth, WarmupTracker, enrichment |
| `test_spirit_return_voice.py` | 34 | Tier classification, voice cues, block enrichment, character context assembly |
| `test_spirit_reflection.py` | 31 | Extraction, influence scoring, building, anti-echo guards, storage, end-to-end |
| `test_spirit_reflection_integration.py` | 12 | Fail-soft, persistence + reload, tamper resistance, retrieval precedence unchanged |

Total: 130 tests covering the complete spirit return + reflection pipeline.

---

## 8. File Reference

```
torment_service/
    spirit_return.py          # Phase 7: symbol matrix, return modes, warmup, enrichment
    spirit_reflection.py      # Phase 7b: post-response write-back, influence scoring, anti-echo
    deep_memory.py            # Deep memory store: compression target, spirit return source
    retrieval_assembler.py    # Context assembly: tier classification, voice cues
    character.py              # Character context: spirit_return_summary generation
    fabric.py                 # Orchestrator: deep memory fallback with spirit return injection

data/agents/{agent_id}/
    deep_memory/
        memories.jsonl        # Compressed deep memories (source-of-truth)
        embeddings/           # Shard-based embedding index
    warmup/
        warmup_state.jsonl    # WarmupTracker: per-EID warmth accumulation
    spirit_reflections/
        reflections.jsonl     # Spirit reflection events (derived artifacts, separate storage)
```
