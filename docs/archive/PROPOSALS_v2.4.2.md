# TORMENT v2.4.2 — Improvement & Extension Proposals

Prepared by Claude for pzychozen + GPT review
Date: April 4, 2026

These proposals are ordered by impact and feasibility. Each one is scoped small enough to be a single PR. Nothing here redesigns the system — everything builds on what exists.

---

## Tier 1 — Wire What's Already Built (highest value, lowest risk)

### 1A. Memory Plan → Real Query Integration

**Status:** The thinking controller builds a detailed MemoryPlan (lane-specific top_k, weights, token budget, safety constraints) but it's advisory-only. The actual /agent/query endpoint ignores it.

**Proposal:** When TORMENT_THINKING_ADVISORY=1, pass the MemoryPlan into fabric.query() so it uses the lane-specific top_k and weight values instead of flat top_k=8 for everything. This means retrieval-mode queries pull more from core+relational, identity-sensitive queries pull from deep store, live-social queries stay lean.

**Why this matters:** Right now every query gets the same memory shape regardless of what's being asked. A live space quip and an identity question both get 8 flat results. The thinking layer already knows the difference — it just can't act on it.

**Risk:** Low. The memory plan is already being computed. Wiring it in is plumbing, not architecture. Fall back to flat top_k when thinking is off.

**Test:** Same 5 scenarios from Torment_agent.md. Verify lane distribution changes per scenario.

### 1B. Archivist Write-Back Loop

**Status:** The cognition pipeline's Archivist role generates memory proposals (MemoryProposal with summary, content, target_domain, proposed_strength, half_life, governance_flags, provenance). But approved proposals are returned in the API response and then... nothing happens. They don't get ingested into the fabric.

**Proposal:** After reintegration, approved proposals that pass governance checks should be ingested into the fabric via the existing ingest path. Rejected proposals should be logged with rejection reason (already in the schema). This closes the cognition→memory loop.

**Why this matters:** This is literally the point of the Archivist role. Without write-back, the entire cognition pipeline is a fancy read-only analyzer. With write-back, the system learns from its own reasoning.

**Risk:** Medium. Need to enforce Invariant A (only Archivist writes), ensure provenance tagging, and prevent feedback loops (Archivist output shouldn't trigger another Archivist run). The invariants are already defined — this is enforcement, not invention.

**Test:** Scenario 2 from Torment_agent.md (strategy request). Verify archivist proposals become real memories with correct provenance and governance flags.

### 1C. Geometric Context Harvester

**Status:** GeometricStanceContext has 5 normalized signals (coherence, stability, identity_lock, ambiguity_tolerance, social_resonance) but they default to 0.5 because nothing harvests them from real kernel state.

**Proposal:** Build a harvester function that reads the actual kernel state (coh_ema, drift_score, drift_direction, seed_basin_phi, corridor survival) and maps them into the GeometricStanceContext. Call it at query time when stance policy is active.

**Why this matters:** The stance policy was carefully designed with geometric modulation bands. But without real data it's running on flat 0.5 across the board, which means all the modulation logic is dead code. One function turns it live.

**Risk:** Low. Pure read-only derivation from existing state. The ±15% modulation bands were specifically designed to be safe even with noisy inputs.

**Test:** Feed known kernel states, verify context values are in expected ranges. Run stance policy with real vs default context, verify threshold modulation.

---

## Tier 2 — Small Extensions with Clear Value

### 2A. Spirit Return Status Endpoint

**Status:** Referenced in docs as `/workspace/{ws}/spirit-return/status` but never implemented. The architectural audit flagged this as the best next step for spirit return.

**Proposal:** Pure read-only diagnostics endpoint returning: deep memory count per agent, warmup state stats (total tracked, warmth distribution, resonance-ready count), recent spirit return events with mode breakdown. No production logic changes.

**Why this matters:** Spirit return is one of the most distinctive features of TORMENT and there's zero visibility into it at runtime. You can't tune what you can't see.

**Risk:** Zero. Read-only, no state changes.

### 2B. Alignment Endpoint

**Status:** The thinking advisory sidecar tracks alignment between Spine routing and thinking recommendations in a ring buffer. But there's no API endpoint to read it.

**Proposal:** Add `GET /spine/alignment?last_n=50` that returns the alignment summary (total, aligned, misaligned, thinking_heavier_than_spine, spine_heavier_than_thinking, recent records). The function `get_alignment_summary()` already exists — just needs an HTTP route.

**Why this matters:** The whole point of running thinking as a sidecar is to detect when the Spine's operation-type routing disagrees with content-heuristic routing. If you can't see the data, the sidecar is wasted work.

**Risk:** Zero. The function exists, just needs a route.

### 2C. Live Agent Memory Feedback Loop

**Status:** chat_limn.py and chat_bibs.py ingest turn summaries ("User: X. Bibs responded about the topic.") and run spirit reflection. But there's no feedback mechanism — the system never learns which memories were actually useful for a response.

**Proposal:** After generating a response, call `/agent/feedback` with the retrieved memory block IDs and a simple relevance signal (was the memory used in the response or not). This feeds into the existing reinforcement mechanism — useful memories get reinforced, irrelevant ones decay faster.

**Why this matters:** Right now memory retrieval is a one-way street. The system retrieves but never learns what helped. Even a crude binary signal (used/not-used) would dramatically improve retrieval quality over time, especially for characters that run for hours in live spaces.

**Risk:** Low. The feedback endpoint already exists. The reinforcement mechanism is already built. This is just calling it.

### 2D. WarmupTracker Compaction

**Status:** The architectural audit flagged that WarmupTracker uses append-only JSONL without compaction. Long-running agents accumulate large warmup state files.

**Proposal:** Add a compaction step that runs on startup or periodically: read all entries, keep only the latest state per EID, rewrite the file. Simple, safe, bounded.

**Risk:** Low. Read-compact-write with fsync. Worst case: compaction fails, you keep the uncompacted file.

---

## Tier 3 — Bigger Extensions (need GPT validation)

### 3A. Thinking Layer → Live Agent Integration

**Status:** The live agent (chat_limn.py, chat_bibs.py) calls `/agent/query` directly. The thinking layer exists inside the Spine (`/spine/submit_task`). They don't talk to each other.

**Proposal:** Route live agent queries through the Spine instead of direct fabric query. This means live conversation gets the benefit of cognitive mode selection, memory planning, and stance policy. In live-social mode, the thinking layer already has a LIVE_SOCIAL cognitive mode with compact token budget (900) and low confidence floor (0.55) — perfectly tuned for X Spaces.

**Why this matters:** This is the bridge between "the memory system has a thinking layer" and "the live character actually thinks before it speaks." Right now Limn and Bibs are memory-backed but not cognition-backed.

**Question for GPT:** Does routing live voice through the full Spine add too much latency? The thinking controller is deterministic heuristics (microseconds), but the Spine's trust/locking/audit overhead might matter at voice-conversation speed. Should live-social get a dedicated fast-path that skips locking but still runs thinking?

### 3B. Cross-Character Memory (Limn ↔ Bibs)

**Status:** Limn and Bibs are in separate workspaces with no shared memory. They can't refer to each other or build on each other's conversations.

**Proposal:** Put both characters in the same workspace with separate agent IDs. The hivemind collective field would then detect convergence between them. If both characters hear the same X Space conversation and form similar memories, convergence events fire and echo re-ingestion could give each character awareness of the other's perspective.

**Question for GPT:** Does this violate the character isolation principle? The governance system (7-gate policy) should prevent identity contamination, but two characters in the same Space hearing the same audio is a novel situation. Is echo re-ingestion the right mechanism, or should there be a lighter "awareness" channel?

### 3C. Stance-Driven Response Shaping for Live Social

**Status:** The stance policy can produce participation decisions (engage fully, engage cautiously, defer, observe) but the live agent doesn't read them.

**Proposal:** When routing through the Spine, the stance decision influences response behavior: "observe" means Limn/Bibs stays silent for that turn, "engage cautiously" means shorter response + higher confidence floor, "defer" means "interesting but I'll let someone else take this one." This would make the characters feel more socially intelligent in live spaces — not just responding to everything mechanically.

**Question for GPT:** The stance policy currently has no "interesting enough to respond to" threshold for live social. Should social_resonance from the geometric context influence this? High coherence + high social_resonance = eager to engage, low coherence = more selective?

### 3D. Conversation Rhythm Detection

**Status:** The space mode uses a fixed 10-second listen window. Whether there's a heated debate or a quiet moment, Bibs listens for exactly 10 seconds then processes.

**Proposal:** Use simple audio energy analysis (already available via RMS in the loopback capture) to detect conversation rhythm: rapid back-and-forth (shorten window to 5s, respond faster), monologue (extend window to 15s, let them finish), silence (skip processing). This is not semantic understanding — just energy envelope timing.

**Why this matters:** Fixed-window capture makes the character feel robotic. Humans adjust their listening based on conversational energy. Even crude rhythm detection would make Bibs feel more naturally timed.

**Risk:** Medium. Audio energy is noisy. Need hysteresis to avoid jitter. But it's entirely client-side (live_agent only) and doesn't touch the memory system.

---

## What I Think Matters Most

If I had to pick three, in order:

1. **1A (Memory Plan wiring)** — the thinking layer is already doing the work, just can't influence retrieval. One integration turns the entire thinking pipeline from advisory to functional.

2. **1B (Archivist write-back)** — closes the cognition→memory loop. Without it the Agent Spine is an expensive read-only layer.

3. **2C (Live agent feedback)** — makes the live characters actually learn from conversation. The difference between "memory-backed" and "memory-learning" agent.

Everything else is valuable but these three turn existing dead code into live functionality.

---

## Non-Goals (explicitly NOT proposing)

- Autonomous loops or background planning
- Self-modifying policy logic
- Cross-workspace write federation
- Learned router (keep it deterministic for now)
- Replacing the local LLM with an API model
- Building a web UI

These are all out of scope for the same reasons stated in Torment_agent.md.
