# TORMENT Fabric — Post-Hivemind Milestone Roadmap

Status: active
Version: v2.3.0 → v2.4.0
Date: March 26, 2026
Authors: pzychozen + Claude (Opus 4.6)

---

## Milestone Summary

The Hive Mind is working end-to-end. Adaptive coherence (k=2.0) is production-stable
with both HashEmbedding and STEmbedding. The full pipeline — ingest → coherence →
packet emission → convergence detection → echo reingest — is verified live with
Entity9 producing 10 packets, 2 convergence events (sim=0.96 and 1.00), and
successful reingests across 3 agents.

This roadmap covers everything between "it works" and "it ships clean."

---

## Phase 1 — Lock & Document (priority: immediate)

### 1.1 Lock the Hive Mind milestone

Record the working configuration so it can never be lost to drift.

**Working config (March 26, 2026):**

| Parameter | Value | Notes |
|-----------|-------|-------|
| DISP_SCALE (fallback) | 1.50 | Used during adaptive warmup |
| ADAPTIVE_DISP | True | Adaptive coherence enabled |
| ADAPTIVE_K | 2.0 | Dimensionless sensitivity multiplier |
| ADAPTIVE_WINDOW | 50 | Rolling dispersion buffer |
| ADAPTIVE_WARMUP | 10 | Steps before fully adaptive |
| COH_SMOOTH | 0.70 | EMA smoothing (down from 0.90) |
| COH_FLOOR | 0.05 | Minimum coherence signal |
| _HM_COH_THRESHOLD | 0.15 | Packet gate minimum |
| WRITE_THRESHOLD | 0.55 | strength >= 0.55 to store |
| Omega extraction | Folded embedding (6-chunk sum) | Replaced broken e[:3]/e[3:6] |
| Embedder (production) | STEmbedding (BAAI/bge-small-en-v1.5) | 384-dim dense |
| Embedder (fallback) | HashEmbedding (384-dim sparse) | Works but weaker convergence |

**Deliverables:**
- [ ] Tag git: `v2.3.1-hivemind-stable`
- [ ] Write `docs/MILESTONE_hivemind_v1.md` with the config table above, test results,
      and the adaptive vs fixed comparison data (Hash + ST)
- [ ] Archive `docs/TODO_disp_scale_recalibration.md` — superseded by adaptive implementation
- [ ] Archive `docs/DISP_SCALE_data_for_recalibration.md` — data captured, problem solved
- [ ] Update `docs/SPEC_adaptive_disp_scale.md` status from "proposed" to "implemented"

### 1.2 Update the Hive Mind setup guide

`docs/HIVEMIND_GUIDE.md` needs to reflect the current reality.

**Changes needed:**
- [ ] Add adaptive DISP_SCALE to the configuration section (mention it's automatic,
      no per-embedder tuning required)
- [ ] Add `effective_disp_scale` to the debug payload documentation
- [ ] Verify all env var names match current code
      (`TORMENT_HIVEMIND_ENABLE`, `TORMENT_COMPRESS_ENABLE`, `TORMENT_SRG_ENABLE`,
       `TORMENT_EMBED_PROVIDER`, `TORMENT_EMBED_MODEL`, `TORMENT_EMBED_DEVICE`)
- [ ] Add a "copy-paste quickstart" block that a new user can run in 5 lines
- [ ] Document the coherence pipeline: `disp → adaptive_scale → coh_phase → coh_raw → coh_ema`
- [ ] Remove or update any references to fixed DISP_SCALE values (7e-4, 0.10)

---

## Phase 2 — Memory Health Review (priority: high)

### 2.1 Private/shared memory growth analysis

The system stores memories but we haven't verified that growth patterns are healthy
over extended runs.

**Questions to answer:**
- How fast does private memory grow per agent per 100 ingests?
- How fast does shared (collective) memory grow per convergence event?
- Is there duplication between private and shared stores?
- Are echoes (reingested convergence events) accumulating redundantly?
- What's the compression ratio after event-gated compression fires?

**Approach:**
- [x] Write a diagnostic script that runs 200+ ingests across 3 agents, then dumps:
      private memory count per agent, shared memory count, duplicate content hashes,
      echo chain lengths, compression event count, deep store size
      → `examples/memory_health_diagnostic.py`
- [x] Identify if retention/compression policy needs tuning
      → Compression is dormant (no corridor exits in 250 steps). Needs fallback trigger.
      → Write gate passes 100% of inputs (min strength 0.78 >> threshold 0.55).
- [x] Document findings in `docs/MEMORY_HEALTH_REPORT.md`
      → Key finding: linear unbounded growth; compression never fires under steady state.

### 2.2 Retention and compression policy review

Related to 2.1 but focused on the policy side:
- [x] Verify event-gated compression fires at the right thresholds
      → Proposal A: Added count_overflow (>400) and periodic (every 200 steps) fallback triggers
      → Geometric triggers (corridor_exit, cycle_stage_change) still have priority
      → Verified: 30 compression events across 120 single-agent steps in isolation test
- [x] Check that half_life decay is working (memories should age out)
      → Proposal B: Exponential decay 2^(-age/half_life) at query time, ranking floor 0.03
      → Full clock reset on reinforcement via last_reinforced_ts
- [x] Duplicate suppression implemented
      → Proposal C: Pre-ingest similarity check (threshold 0.92), same-agent only
      → Asymptotic reinforcement: min(0.98, old + (1-old)*0.3)
      → 58/300 ingests reinforced in diagnostic (19% dedup rate)
- [x] Retention tiers formalized
      → Proposal D: Protected/Identity/Relational/Situational/Echo tiers
      → Tier-specific scoring, routing, and execution multipliers
- [x] Hard cap safety net: 10000 memories force-compress to 8000
- [ ] Confirm spirit return retrieval isn't pulling stale compressed memories
      that should have been pruned
- [ ] Review the J→Z scoring path for edge cases

---

## Phase 3 — Character Creation & Generation Flow (priority: high)

### 3.1 Inspect character creator HTML

`start/torment_character_creator.html` is the zero-code Character Forge.

**Tasks:**
- [ ] Open and test the HTML in a browser — does it load, do all panels render?
- [ ] Verify the `setup()` / `set()` functions exist and work (user reports missing behavior)
- [ ] Check API key input flow — does it connect to the server correctly?
- [ ] Verify SRG crystal character generation produces valid character JSON
- [ ] Test that generated Python scripts actually run against the live server
- [ ] Document any broken paths or missing features

### 3.2 Verify generated Hive Mind agents

When the Character Forge generates multi-agent configs:
- [ ] Do they produce valid workspace + agent_id + seed combinations?
- [ ] Can they be copy-pasted into the agents.py harness and run?
- [ ] Are the env vars correct (especially the new adaptive config)?
- [ ] Test: generate 3 agents, run them, confirm packets + convergence

---

## Phase 4 — Golden Test Failures (priority: high)

### 4.1 Investigate golden replay failures

All 3 golden emergent replay tests fail with:
```
AttributeError: 'MemoryGraph' object has no attribute 'search_by_embedding'
```
at `fabric.py:3600` in `process_proposals()`.

**Tasks:**
- [ ] Determine if `search_by_embedding` was renamed, removed, or never implemented
      on MemoryGraph
- [ ] Check if this is a missing method that needs to be added, or if the call site
      should use a different API (e.g., `search()` or `query()`)
- [ ] Fix the AttributeError
- [ ] Re-run golden replays and verify they pass within the widened bounds
- [ ] Investigate whether the proposal pipeline has numerical edge cases
      (NaN, inf, division by zero) that could cause spikes
- [ ] Add guards if needed: `np.isnan()` / `np.isinf()` checks on coherence,
      dispersion, and strength before they reach downstream consumers

### 4.2 Test determinism review

`test_replay_determinism` has a known fragility where `motif_entropy_score` differs
between runs (0.6778 vs 0.6892) due to probabilistic write-band interacting with
adaptive coherence dynamics.

- [ ] Decide: is replay determinism a hard requirement or soft goal?
- [ ] If hard: seed all random sources (numpy, python random) and pin write-band
- [ ] If soft: widen the tolerance or convert to a statistical test

---

## Phase 5 — Agent Spine (priority: medium) ✓ COMPLETE

### 5.1 Write Agent Spine overview ✓

The Agent Spine is **fully implemented** (not partially as originally assumed).
All 7 invariants enforced, 4 deterministic roles, 3 aperture types, comprehensive
schemas, 2,844 lines of test coverage, and a working `/cognition/run` endpoint.

**Deliverable:** `docs/AGENT_SPINE_OVERVIEW.md` — comprehensive overview covering:
- [x] What it is: a governed single-pass cognition pipeline (NOT an autonomous loop)
- [x] Architecture: TaskPacket → Router → Apertures → Roles → Reintegration → Response
- [x] The 7 hard invariants (A through G) and why they matter
- [x] What's implemented (everything) vs what's deferred (LLM backends, write-back loop)
- [x] Data contracts, routing table, aperture configs, role descriptions

### 5.2 Clarify Agent Spine ↔ Hive Mind interaction ✓

- [x] Documented where they touch: Spine reads via fabric.query() → approved proposals
      go to fabric.ingest() → kernel coherence → packet emission → convergence → echo
      reingest → appears in shared_memories on next spine query
- [x] Pipeline runs per-agent (TaskPacket carries agent_id)
- [x] Recommendation: archivist writes go through normal ingest (coherence gate is
      orthogonal to semantic quality). If drop rate is too high, add a write-gate
      boost for archivist-approved content rather than bypassing.
- [x] Interaction contract written in AGENT_SPINE_OVERVIEW.md §"Agent Spine ↔ Hive Mind"

---

## Phase 6 — Observability (priority: medium) ✓ COMPLETE

### 6.1 Production observability endpoint

Unified `GET /debug/metrics` endpoint aggregates all in-memory stats into one call.
Reads only RAM state — no disk scans, cheap to poll.

**Exposed metrics:**
- [x] Feature flags: compress, hivemind, srg, character, checkpoint enable states
- [x] Per-agent: memory_count, compression state (last_step, events_total, warning),
      last 5 compression events, deep memory stats, character drift
- [x] Per-domain: motif_count/avg/max strength, coherence field role counts
      (basin/ridge/plateau), shared_memory_count, proposal totals
- [x] Collective: packet_count, convergence_events
- [ ] Coherence: coh_ema, coh_raw per agent (requires kernel state exposure — future)
- [ ] Effective DISP_SCALE per agent (requires kernel state exposure — future)
- [ ] Packet gate stats: emitted vs blocked counts (would need counters in fabric)

**Existing endpoints preserved (per-component detail):**
- `GET /workspace/{ws}/compress/status` — full compression history per agent
- `GET /workspace/{ws}/collective/status` — collective field detail
- `GET /workspace/{ws}/spirit-return/status` — warmup tracker per agent
- `GET /workspace/{ws}/domain/{dom}/motif_entropy` — motif entropy detail
- `GET /health` — system health + embedder info

### 6.2 Adaptive coherence long-run monitoring

The adaptive k=2.0 is stable over 12 ingests. We need to verify over longer runs.

- [ ] Run a 500+ ingest simulation and track effective_scale drift
- [ ] Verify the rolling window doesn't cause scale oscillation under rapid topic switching
- [ ] Check for edge cases: all-identical inputs (scale → 0?), all-random inputs
- [ ] Add a clamp floor log: if effective_scale hits the 1e-6 floor, warn

---

## Phase 7 — MCP Compatibility (priority: exploratory)

### 7.1 MCP exposure assessment

Evaluate what it would take to expose TORMENT as an MCP server.

**Questions:**
- [ ] Which TORMENT operations map to MCP tools? (ingest, query, status, character)
- [ ] What's the auth model? (per-workspace API keys? per-agent tokens?)
- [ ] Can the collective layer be safely exposed, or is it internal-only?
- [ ] What MCP resource types would TORMENT expose? (memories as resources?
      coherence state as context?)
- [ ] Write `docs/MCP_COMPATIBILITY_ASSESSMENT.md` with findings

### 7.2 MCP prototype (if assessment is positive)

- [ ] Build a minimal MCP server wrapper around the existing FastAPI endpoints
- [ ] Expose: `torment_ingest`, `torment_query`, `torment_status` as MCP tools
- [ ] Test with Claude Code / Cowork as the MCP client

---

## Phase 8 — Demo Path (priority: low, but high impact)

### 8.1 End-to-end polished demo

One clean path from zero to convergence that anyone can follow.

**Flow:**
1. Open Character Forge HTML → create 3 characters
2. Start server with correct env vars
3. Run generated agent scripts
4. Watch coherence rise, packets emit, convergence fire
5. See reingest propagate the collective insight
6. Query each agent and see the shared memory reflected

**Deliverables:**
- [ ] A single `examples/demo_hivemind.py` that does steps 3-6 automatically
- [ ] A `docs/DEMO_WALKTHROUGH.md` with screenshots/expected output
- [ ] Verify it works on a fresh machine with only `pip install` dependencies

---

## Priority Order (updated March 26, 2026)

| Priority | Phase | Effort | Status |
|----------|-------|--------|--------|
| ~~1~~ | ~~1.1 Lock milestone~~ | Small | Pending |
| ~~2~~ | ~~1.2 Update setup guide~~ | Small | Pending |
| ~~3~~ | ~~2.1-2.2 Memory health~~ | Medium | **✓ DONE** — decay, dedup, fallback triggers, tiers, hard cap |
| ~~4~~ | ~~3.1-3.2 Character/generation~~ | Medium | Deferred (expected to work) |
| ~~5~~ | ~~4.1-4.2 Golden failures~~ | Medium | **✓ DONE** — search_by_embedding fix, 3-tier determinism |
| ~~6~~ | ~~5.1-5.2 Agent Spine docs~~ | Medium | **✓ DONE** — AGENT_SPINE_OVERVIEW.md |
| ~~7~~ | ~~6.1-6.2 Observability~~ | Medium | **✓ DONE** — /debug/metrics endpoint + existing per-component endpoints |
| 8 (next) | 7.1-7.2 MCP | Large | Depends on 5.1 (done), needs deep planning |
| 9 (after) | 8.1 Demo path | Medium | Capstone — after MCP |

Phase 7 (MCP) and Phase 5 (Spine) are the foundation pair for making TORMENT
externally usable. With Phase 5 complete, MCP exposure is the next major milestone.
Phase 8 (demo) follows naturally once MCP tools exist.

---

## Open Questions for ChatGPT

1. ~~**Memory growth bounds:**~~ → **RESOLVED**: Hard cap at 10000 as last-resort safety net.
   Primary growth control is: half-life decay + duplicate reinforcement + fallback
   compression triggers (count_overflow at 400, periodic at 200 steps) + retention tiers.

2. ~~**Agent Spine write gate:**~~ → **RESOLVED**: Archivist proposals go through normal
   ingest including write gate. If approved proposals get dropped too often, add a
   write-gate strength boost for archivist-approved content rather than bypass.

3. **MCP auth model:** Per-workspace tokens, per-agent tokens, or something else?
   → Still open. Needs design before Phase 7 implementation.

4. **Adaptive k as a slider:** Should k=2.0 be exposed as a UI slider (7th collective
   policy knob), or kept as a server-side config?

5. ~~**Golden replay determinism:**~~ → **RESOLVED**: Soft goal. 3-tier test structure:
   strict for private, tolerance for collective, exact for collective-disabled.
