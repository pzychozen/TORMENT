# Hivemind Implementation Plan — Claude's Working Phases

TORMENT v2.2 → v2.3+

Based on the hivemind.md roadmap (ChatGPT) grounded in the actual codebase.

---

## Architecture Assessment

After reading the full codebase, here's what I found at each insertion point:

**Ready to use immediately:**
- `self.collective_state: Dict[str, Any] = {}` — placeholder in Fabric already exists, workspace-scoped
- `CharacterState` dataclass already has drift_score, drift_direction, distance_to_seed, seed_basin_phi/kappa/tension/role, tier counts — everything needed for self-state API
- `CharacterSeed` has seed_id, seed_motif_id, seed_eids — complete seed metadata
- `ProposalRegistry` and `BridgeRegistry` demonstrate the exact JSONL persistence pattern to follow
- `fabric.ingest()` has all signals post-enrichment: kernel signals, tri_mod, motifs, symbols, resonance score, loop_type, phase/corridor durations, SRG state, affect tags
- `app.py` has clear route patterns with workspace_id extraction

**Gaps to fill:**
- No collective module exists yet
- No agent-to-agent resonance representation
- Character self-state is computed internally but not exposed via API
- `collective_state` is empty dict — needs real initialization

---

## My Phases

I'm splitting the work into 4 phases (A through D). Each phase produces a tagged, testable, fully backward-compatible release. Each phase maps to roughly 1-2 of the roadmap's 8 phases, prioritized by dependency order.

---

## Phase A — Foundation Layer

*Maps to: Roadmap Phase 0 + Phase 1 + Phase 2 (data contracts only)*

### What gets built

1. **`torment_service/collective_models.py`** — All data contracts
   - `ResonancePacket` dataclass with serialization
   - `ConvergenceEvent` dataclass with serialization
   - `CharacterSelfState` dataclass (clean API view of existing CharacterState + seed + phase data)
   - `MemoryGovernanceFlags` dataclass (shape only — not wired yet)
   - All with `to_dict()` / `from_dict()` round-trip methods

2. **Character self-state API endpoints** in `app.py`
   - `GET /agent/{agent_id}/character/state?workspace_id=...` — returns CharacterSelfState
   - `GET /agent/{agent_id}/character/seed?workspace_id=...` — returns seed metadata
   - Both reuse existing `CharacterStore.load_seed()` and `CharacterStore.load_state()` plus phase timer data from Fabric

3. **Helper in `character.py`**
   - `build_self_state(workspace_id, agent_id, fabric) -> CharacterSelfState` — assembles from existing computed data
   - No restructuring of character logic

4. **Unit tests**
   - `tests/test_collective_models.py` — serialization round-trips, field validation
   - `tests/test_character_selfstate.py` — self-state assembly, seeded vs non-seeded agents

### Why this order

The roadmap says "transparency before agency" — and it's right. Before agents can participate in a collective field, they need to know themselves. The self-state endpoint also validates that we can extract all the signals the ResonancePacket will need later.

### Feature flag

`TORMENT_HIVEMIND_ENABLE` env var (default: 0). Self-state endpoints work regardless of flag. Collective features require flag ON.

### Files touched
- **New:** `torment_service/collective_models.py`, `tests/test_collective_models.py`, `tests/test_character_selfstate.py`
- **Modified:** `app.py` (2 new routes), `character.py` (1 helper method), `fabric.py` (flag init only)

### Acceptance criteria
- Self-state API returns meaningful JSON for seeded agents
- Non-seeded agents return graceful empty fields
- All data contracts serialize/deserialize cleanly
- No existing tests regress

---

## Phase B — Collective Field + Packet Emission

*Maps to: Roadmap Phase 2 (emission) + Phase 3 (persistence)*

### What gets built

1. **`torment_service/collective_field.py`** — Workspace-level collective store
   - `CollectiveField` class, one per workspace
   - Append-only JSONL persistence at `data/workspaces/{ws}/collective/packets.jsonl`
   - Methods: `append_packet()`, `recent_packets()`, `packets_by_domain()`, `packets_by_agent()`, `status()`
   - Small in-memory cache (last N packets) for convergence detection window

2. **Packet emission in `fabric.ingest()`**
   - After motif + symbol + resonance enrichment (the roadmap's exact insertion point)
   - Build `ResonancePacket` from available signals:
     - `signals.strength`, `signals.stability_delta` from kernel
     - `tri_mod["cycle_stage"]`, `tri_mod["identity_state"]` from debug dict
     - Motif IDs from attachment
     - Symbol state from `_sym_update`
     - Resonance score/loop_type from `_res_summary`
     - Phase/corridor durations from `_pt_durations`
     - Drift score from character state (if seeded)
   - Gating: only emit if memory was actually stored AND coherence >= threshold
   - Append to workspace's CollectiveField

3. **Initialize CollectiveField in Fabric**
   - Replace empty `self.collective_state` with proper `CollectiveField` instance per workspace
   - Lazy initialization on first access

4. **Tests**
   - `tests/test_collective_field.py` — persistence round-trip, filtering, status
   - Integration: ingest with flag on → packet appears in field

### Files touched
- **New:** `torment_service/collective_field.py`, `tests/test_collective_field.py`
- **Modified:** `fabric.py` (field init + packet emission block in ingest), `app.py` (none yet — APIs come in Phase C)

### Acceptance criteria
- Ingest with HIVEMIND_ENABLE=1 produces persisted packets
- Ingest with HIVEMIND_ENABLE=0 produces no packets, zero overhead
- Packets survive server restart
- Packet contains all enriched signals from the ingest pipeline
- Existing ingest behavior unchanged

---

## Phase C — Convergence Detection + Collective API

*Maps to: Roadmap Phase 4 + Phase 5*

### What gets built

1. **Convergence detection in `collective_field.py`**
   - `detect_convergence(new_packet) -> Optional[ConvergenceEvent]`
   - Algorithm:
     - Scan recent packets in temporal window (configurable, default ~50 steps)
     - Filter: same workspace, same domain, different agent
     - Compute semantic overlap via embedding cosine similarity
     - Check phase/cycle alignment
     - Check motif/symbol overlap bonus
     - If composite confidence >= threshold AND >= 2 distinct agents → create event
   - Deduplication: don't re-fire for same agent pair + domain within cooldown window
   - Persist events to `data/workspaces/{ws}/collective/events.jsonl`

2. **Collective API endpoints** in `app.py`
   - `GET /workspace/{workspace_id}/collective/status` — packet count, event count, active agents, domains
   - `GET /workspace/{workspace_id}/collective/packets?domain=&agent=&limit=` — filtered packet list
   - `GET /workspace/{workspace_id}/collective/events?limit=` — recent convergence events
   - `GET /workspace/{workspace_id}/collective/events/{event_id}` — single event detail

3. **Optional collective_context in query**
   - Add `collective_context` field to query response (behind flag + debug mode initially)
   - Contains: recent relevant events for the queried domain
   - Does NOT influence scoring yet — informational only

4. **Tests**
   - `tests/test_convergence.py` — detection logic, dedup, threshold behavior
   - `tests/test_collective_api.py` — endpoint responses, filtering
   - Integration: 2 agents, same domain, similar content → event detected

### Files touched
- **Modified:** `collective_field.py` (detection logic), `app.py` (4 new routes), `fabric.py` (call detection after packet emission, optional collective_context in query)
- **New:** `tests/test_convergence.py`, `tests/test_collective_api.py`

### Acceptance criteria
- Two agents ingesting similar content in same domain produces a convergence event
- Two agents ingesting unrelated content produces no event
- Single agent alone never produces multi-agent event
- All endpoints return well-structured JSON
- Collective context appears in query response when enabled

---

## Phase D — Re-Ingestion + Governance

*Maps to: Roadmap Phase 6 + Phase 7 (+ Phase 8 lightly)*

### What gets built

1. **`torment_service/collective_policy.py`** — Policy engine
   - `CollectivePolicy` class with configurable rules
   - Reingest eligibility: confidence threshold, domain scope, agent opt-out, dedup
   - Export eligibility: governance flag checks
   - Rate limiting: max reingests per agent per window

2. **Controlled re-ingestion in `fabric.py`**
   - `Fabric.reingest_convergence(workspace_id, agent_id, event_id)` method
   - Synthesizes compact summary from convergence event
   - Ingests with reduced strength (e.g., 0.4x normal)
   - Marks payload with `provenance: "collective"`, source event_id, source agents
   - Deduplicates against previously reingested events

3. **Memory governance flags**
   - Wire `MemoryGovernanceFlags` into memory payloads
   - Respect `non_shareable` in packet emission
   - Respect `collective_reingest_blocked` in re-ingestion path
   - API: `POST /memory/governance/set` to update flags on existing memories

4. **Light proposal bridge** (from roadmap Phase 8)
   - High-confidence convergence events optionally generate draft share proposals
   - Uses existing ProposalRegistry — no new governance needed

5. **Tests**
   - `tests/test_collective_policy.py` — policy rules, opt-out, dedup
   - `tests/test_reingest.py` — provenance marking, strength reduction, dedup
   - Integration: full cycle — 2 agents ingest → convergence → reingest → verify provenance + identity intact

### Files touched
- **New:** `torment_service/collective_policy.py`, `tests/test_collective_policy.py`, `tests/test_reingest.py`
- **Modified:** `fabric.py` (reingest method), `app.py` (reingest + governance routes), `collective_field.py` (governance checks)

### Acceptance criteria
- Reingested collective echoes carry provenance markers
- Same event cannot be reingested twice into same agent
- Governance flags block sharing/reingestion when set
- Agent identity (drift score, crystal state) remains stable after reingest
- Existing proposal/bridge systems not broken

---

## What I'm NOT Doing

Following the roadmap's "do not touch" list:

- **Not rewriting kernel physics** — model_core.py, memory_kernel.py stay untouched
- **Not replacing proposals/bridges** — collective sits above them, optionally feeding into them
- **Not overloading resonance.py** — all collective logic goes in new collective_* modules
- **Not unifying archive with identity** — archive path stays separate
- **Not making collective context mandatory** — always behind flag, always optional in query

---

## SRG Integration Points

The Crystal Attunement system we just built has natural hivemind connections:

- **Band-aware coupling** — agents on the same golden tower band could have stronger collective resonance (Phase C scoring bonus)
- **Crystal identity in packets** — crystal memories could be marked as `non_shareable` by default (they ARE the private identity core)
- **Collision physics across agents** — SRG collision could extend to cross-agent memory overlap (later work, not in these phases)
- **Breathing synchronization** — agents in convergence could have their breathing phases sync (speculative, Phase D at earliest)

These are noted but deferred. Get the field working first.

---

## Version Targets

| Phase | Version | Tag |
|-------|---------|-----|
| A | 2.3.0 | Foundation — self-state API + data contracts |
| B | 2.3.1 | Collective field + packet emission |
| C | 2.4.0 | Convergence detection + collective API |
| D | 2.5.0 | Re-ingestion + governance |

---

## Estimated Scope

| Phase | New files | Modified files | New tests | Approx lines |
|-------|-----------|----------------|-----------|---------------|
| A | 3 | 3 | ~40 | ~400 |
| B | 2 | 1 | ~35 | ~500 |
| C | 2 | 3 | ~50 | ~600 |
| D | 2 | 3 | ~45 | ~500 |

Total: ~2000 new lines across 4 phases, fully tested.
