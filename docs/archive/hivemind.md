# TORMENT Hivemind Roadmap for Claude

Status: planning document grounded in the current `v2.2.2` code and docs  
Audience: Claude Code / implementation agent  
Goal: extend TORMENT from a stable single-agent dynamical memory system into a controlled multi-agent resonance fabric **without** damaging kernel stability, character continuity, or existing governance.

---

## 1. Executive Summary

TORMENT is already a strong single-agent memory substrate with:

- a real dynamical kernel (`model_core.py`, `memory_kernel.py`)
- a governed orchestration layer (`fabric.py`)
- a living character continuity system (`character.py`)
- workspace/domain separation, proposals, bridges, motifs, symbolic resonance, deep memory, and compression

This roadmap does **not** treat hivemind as “share all memories.”
It treats hivemind as **workspace-level resonance coupling between agents**.

That means the first real feature is **collective resonance events**, not raw memory merging.

The correct path is:

1. surface agent self-state clearly
2. emit portable resonance packets from ingest
3. maintain a workspace-level collective field
4. detect multi-agent convergence
5. optionally re-ingest collective echoes under policy
6. only later consider stronger shared-memory promotion

---

## 2. Ground Truth From Current Architecture

### 2.1 What already exists

The current system already has the right substrate:

- `TriOctaPhaseLockModel` in `model_core.py` is the bounded oscillator core.
- `memory_kernel.process()` converts observation text into kernel signals and tri-mod outputs.
- `fabric.ingest()` is the real orchestration hinge: it handles summary, embedding, kernel signals, phase timing, routing, memory storage, motifs, coherence field, symbol assignment, symbolic resonance enrichment, compression triggers, proposals, bridge suggestion, and drift/correction.
- `character.py` is not cosmetic. It already implements:
  - seed planting
  - seed basin formation
  - drift measurement
  - gravity correction
  - tier-aware context assembly
  - kernel modulation (`derive_kernel_modulation`)
- `app.py` already exposes a usable agent API for create/identity/roles/ingest/query/retrieve.

### 2.2 What already resembles hivemind

The code already contains several federation primitives:

- workspace separation
- shared domain graphs
- proposal workflow
- bridge workflow
- `self.collective_state` placeholder in `Fabric`
- shared motif registries per domain
- cross-domain bridge peeks

This means the architecture is **not** starting from zero.

### 2.3 What is missing

The actual missing layer is a formal **collective resonance representation**.

Right now TORMENT has:

- per-agent memory formation
- per-agent symbolic trace/resonance
- controlled shared canon proposals

But it does **not** yet have:

- a portable agent-to-agent resonance packet
- a workspace-level convergence engine
- a persistent collective event log
- a policy for controlled re-ingestion of collective echoes
- public self-awareness endpoints for the living character layer

---

## 3. Design Principle

### 3.1 The hivemind is a field, not a database

Do **not** implement hivemind as “copy private memories into a shared graph.”

Instead:

- each agent keeps its own center / seed basin / drift state
- agents publish selective resonance packets into a collective field
- the field detects overlap, synchrony, and convergence
- the system writes **collective events**, not raw foreign memories
- agents may later ingest a collective event if policy permits

This preserves identity and avoids memory contamination.

### 3.2 Preserve the two character systems

Do **not** merge the two character layers yet.

Keep them distinct:

1. **Operational identity layer**
   - identity store
   - overlay
   - role guidance
   - API-visible agent shell

2. **Living character continuity layer**
   - seed basin
   - planted canon memories
   - drift measurement
   - gravity correction
   - tier-aware context assembly
   - kernel modulation

The hivemind must sit **above** those, not replace them.

### 3.3 First-class transparency before first-class agency

Before giving agents curation powers like “forget this” or “do not share this,” first expose:

- current drift
- tier counts
- seed basin state
- corridor/phase signals
- recent symbolic / compression / collective activity

An agent cannot curate memory intelligently if its own state is opaque.

---

## 4. Non-Goals / Do Not Touch (Early Phases)

Claude should treat these as protected unless a tiny compatibility change is required:

### 4.1 Do not rewrite kernel physics

Avoid invasive edits to:

- `model_core.py`
- the main TriOcta dynamics
- D24 stepping logic
- cycle / identity mapping logic

Hive work should attach at the orchestration layer, not by changing the math.

### 4.2 Do not replace current proposals / bridges

The existing proposal and bridge workflows are valuable governance primitives.
Do not bypass or remove them.

### 4.3 Do not unify archive memory with identity memory

The archive path is intentionally distinct from character continuity.
Keep archive ingestion/query separate.

### 4.4 Do not overload `resonance.py`

`resonance.py` already has a specific meaning in TORMENT: symbolic resonance loops for per-agent symbol traces.

Do **not** cram collective hivemind logic into that module.
Create new files/modules using names like:

- `collective_field.py`
- `collective_models.py`
- `collective_policy.py`
- `collective_api.py`

or similar.

---

## 5. Target End State

The end state of this roadmap is:

- every agent retains private-write memory and living character continuity
- every workspace has a collective resonance field
- ingest emits compact resonance packets into that field
- the field detects convergence events across agents
- convergence events are queryable and inspectable
- optionally, collective echoes can re-enter an agent as controlled candidate memories
- self-awareness and memory-governance hooks are exposed through API

This should feel like **coordinated memory pressure** across agents, not like a generic shared notes app.

---

## 6. Recommended New Data Contracts

These can be implemented as dataclasses or Pydantic models. Keep them simple first.

### 6.1 `ResonancePacket`

Purpose: portable, lightweight representation of an ingest event at the collective layer.

Suggested fields:

```python
ResonancePacket:
    packet_id: str
    workspace_id: str
    agent_id: str
    domain_id: str
    source_eid: int | None
    ts: int

    summary: str
    embedding: list[float] | None     # or reference/hash if storage is a concern
    embedding_hash: str | None

    cycle_stage: str
    identity_state: str
    coherence: float
    stability_delta: float

    corridor_angle_deg: float | None
    corridor_duration_steps: int | None
    phase_duration_steps: int | None

    motifs: list[str]
    created_motif: str | None

    state_symbol: str | None
    resonance_score: float | None
    loop_type: str | None

    drift_score: float | None
    drift_direction: str | None
    seed_id: str | None

    permissions: dict[str, bool]
    tags: list[str]
```

Notes:
- Start permissive but minimal.
- `permissions` should support at least `shareable`, `reingestable`, `visible_to_workspace`.
- If full embeddings are expensive, store a centroid reference or short vector hash initially.

### 6.2 `ConvergenceEvent`

Purpose: normalized record of cross-agent alignment.

Suggested fields:

```python
ConvergenceEvent:
    event_id: str
    workspace_id: str
    domain_id: str
    ts_start: int
    ts_end: int

    participating_agents: list[str]
    source_packets: list[str]
    source_eids: list[int]

    confidence: float
    persistence: float
    semantic_overlap: float
    phase_alignment: float
    symbol_alignment: float

    dominant_motifs: list[str]
    dominant_symbol: str | None
    dominant_cycle_stage: str | None
    dominant_identity_state: str | None

    summary: str
    policy_flags: dict[str, bool]
```

### 6.3 `CharacterSelfState`

Purpose: clean API payload for self-awareness and monitoring.

Suggested fields:

```python
CharacterSelfState:
    workspace_id: str
    agent_id: str
    seed_id: str | None
    seed_motif_id: str | None

    drift_score: float
    drift_direction: str
    distance_to_seed: float

    seed_basin_role: str
    seed_basin_phi: float
    seed_basin_kappa: float
    seed_basin_tension: float

    core_count: int
    relational_count: int
    situational_count: int

    phase_duration_steps: int | None
    corridor_duration_steps: int | None
    last_cycle_stage: str | None
    last_identity_state: str | None

    recent_collective_events: int
    recent_compressions: int
    updated_ts: int
```

### 6.4 `MemoryGovernanceFlags`

Purpose: future-safe control surface for selective sharing / decay.

Suggested fields:

```python
MemoryGovernanceFlags:
    protected: bool = False
    non_shareable: bool = False
    decay_accelerated: bool = False
    collective_export_blocked: bool = False
    collective_reingest_blocked: bool = False
```

Do **not** wire all of these in phase 1. Just define a stable shape.

---

## 7. File and Module Plan

### 7.1 New modules to add

Recommended initial additions:

```text
torment_service/
  collective_models.py
  collective_field.py
  collective_policy.py
```

Optional later split:

```text
  collective_query.py
  collective_metrics.py
```

### 7.2 Existing files to modify

Primary modification targets:

- `fabric.py`
- `app.py`
- possibly `character.py` for helper serializers only

Secondary / optional:

- `retrieval_assembler.py` if collective echoes later become part of assembled context
- `tests/` for new API, persistence, and integration tests

### 7.3 Files to leave mostly untouched in early work

- `model_core.py`
- `memory_kernel.py`
- `symbols.py`
- `resonance.py`
- archive modules

---

## 8. Exact Insertion Points

### 8.1 `Fabric.__init__`

There is already a `self.collective_state` placeholder.
Use that as the starting anchor, but do not keep everything in RAM-only form forever.

Action:
- initialize a collective field/store object here
- make it workspace-aware
- keep a small in-memory cache if useful, but persist events to disk

### 8.2 `fabric.ingest()`

This is the most important insertion point.

Recommended placement:

1. complete normal memory write
2. attach motifs
3. compute coherence field and symbol state
4. enrich payload with symbolic resonance
5. **then emit a `ResonancePacket`**
6. **then update collective field and maybe detect a convergence event**
7. then continue existing compression / proposal / bridge behavior

This ordering matters because the packet should carry the enriched local meaning, not a pre-motif/pre-symbol raw event.

### 8.3 `fabric.query()`

Do not make collective context mandatory at first.

Add optional capability to:
- retrieve recent convergence events relevant to the query domain
- include them in debug or optional `collective_context`
- later allow them to influence scoring or retrieval assembly conservatively

### 8.4 `app.py`

Add explicit API endpoints for:

- character self-state
- collective field status
- recent convergence events
- optionally a manual “re-ingest collective event” route

### 8.5 `character.py`

Prefer helper methods only.
Do not restructure character logic early.

Useful additions:
- helper to serialize a self-state view
- helper to expose seed metadata cleanly

---

## 9. Roadmap by Phase

---

## Phase 0 — Documentation and Safety Rails

### Goal
Prevent accidental architecture damage while adding hivemind features.

### Tasks
- add this roadmap file
- add docstrings/comments in new collective modules stating that this is **not** a replacement for proposals/bridges
- keep changes small and additive

### Acceptance criteria
- roadmap exists
- new modules are named clearly
- no existing functionality regresses

---

## Phase 1 — Expose the Living Character Layer Publicly

### Goal
Make the existing self-state visible before adding collective coupling.

### Why first
The code already computes much more than the API exposes. Hivemind should not be built on opaque selfhood.

### Tasks
1. Add endpoint: `GET /agent/{agent_id}/character/state`
2. Add endpoint: `GET /agent/{agent_id}/character/seed`
3. Optionally add endpoint: `GET /agent/{agent_id}/character/self_awareness`

### Response contents
Return at minimum:
- `seed_id`
- `seed_motif_id`
- `seed_eids`
- `drift_score`
- `drift_direction`
- `distance_to_seed`
- `seed_basin_role`
- `core_count`
- `relational_count`
- `situational_count`
- most recent known phase/corridor duration data if available

### Implementation notes
- reuse `CharacterStore.load_seed()` and `CharacterStore.load_state()`
- reuse existing phase timer state in `Fabric`
- do not make this depend on query

### Acceptance criteria
- API can return meaningful character-state JSON for seeded agents
- no existing routes change behavior
- seeded and non-seeded agents both behave sensibly

### Suggested tests
- create agent with seed -> endpoint returns seed data
- ingest enough to create drift state -> endpoint returns drift fields
- agent without seed -> returns null/empty fields gracefully

---

## Phase 2 — Introduce `ResonancePacket`

### Goal
Create a portable collective-layer representation of an ingest event.

### Tasks
1. Add `collective_models.py`
2. Define `ResonancePacket`
3. Add helper in `fabric.py` to build packet from:
   - ingest result
   - current kernel signals
   - motif attachment result
   - symbol/resonance enrichment
   - optional character state

### Important rule
Do not emit packets for everything blindly.
Start with conservative gating, for example:
- memory was actually stored
- confidence/coherence above threshold
- not blocked by governance flag

### Acceptance criteria
- ingest can optionally emit a stable packet object
- packet structure is consistent and serializable
- packet creation does not break existing ingest behavior

### Suggested tests
- stored memory creates packet
- non-stored/no-write path does not create packet
- packet includes motif + symbol + cycle info when available

---

## Phase 3 — Workspace-Level Collective Field

### Goal
Persist and query collective packets/events per workspace.

### Tasks
1. Add `collective_field.py`
2. Implement a simple persistent store:
   - append-only JSONL is acceptable initially
   - per-workspace path under data dir
3. Support operations:
   - append packet
   - fetch recent packets
   - fetch packets by domain
   - fetch packets by agent
   - prune or compact old packets later

### Recommended storage layout

```text
workspaces/{workspace_id}/collective/
  packets.jsonl
  events.jsonl
  state.json
```

### Acceptance criteria
- packets persist across restart
- workspace scoping works
- domain filtering works

### Suggested tests
- append/load packets
- restart/read persisted packets
- packet filtering by domain and agent

---

## Phase 4 — Convergence Detection

### Goal
Turn many packets into meaningful collective events.

### Definition
A convergence event should represent significant overlap between multiple agents within a bounded time window.

### Initial detection criteria
Start simple:
- same workspace
- same domain
- >= 2 distinct agents
- packet timestamps within short window
- semantic similarity above threshold
- compatible phase/cycle state
- optional symbol or motif overlap bonus

### Output
Create and persist a `ConvergenceEvent`.

### Important rule
Do not try to solve full consensus or cognition here.
This is only event detection.

### Acceptance criteria
- when two or more agents align strongly, an event is created
- duplicate event spam is controlled
- confidence score is interpretable

### Suggested tests
- two agents, same domain, similar content -> event created
- two agents, unrelated content -> no event
- repeat packets from same agent alone -> no multi-agent event

---

## Phase 5 — Collective API Surface

### Goal
Make collective behavior inspectable.

### Add endpoints
Suggested endpoints:

- `GET /workspace/{workspace_id}/collective/status`
- `GET /workspace/{workspace_id}/collective/packets`
- `GET /workspace/{workspace_id}/collective/events`
- `GET /workspace/{workspace_id}/collective/events/{event_id}`

Optional later:
- `GET /agent/{agent_id}/collective/feed`

### Return fields
Status should expose at least:
- recent packet count
- recent event count
- active participating agents
- event counts by domain

### Acceptance criteria
- humans can inspect what the field is doing
- collective behavior can be debugged without reading raw files

---

## Phase 6 — Controlled Re-Ingestion of Collective Echoes

### Goal
Allow the collective field to influence local agents without collapsing private identity.

### Design
Do **not** write another agent’s raw memory directly into a private graph.

Instead:
- create a compact derived summary from a convergence event
- mark it as collective-origin
- ingest it through a controlled path
- gate by policy

### Suggested implementation
Add a method like:

```python
Fabric.ingest_collective_event(...)
```

or

```python
Fabric.reingest_convergence(...)
```

This should:
- synthesize a small summary
- use reduced write strength
- mark payload with provenance
- avoid looking like native personal memory

### Policy rules
At minimum:
- agent may opt out
- event must exceed confidence threshold
- re-ingestion should be domain-scoped
- repeated ingestion of the same event must be deduplicated

### Acceptance criteria
- collective echo can enrich an agent without polluting identity memory
- provenance is visible
- duplicate loops are blocked

---

## Phase 7 — Memory Governance / Consent Hooks

### Goal
Let agents or operators control sharing and release more explicitly.

### Additions
Memory-level or event-level controls such as:
- protect memory
- block collective export
- block collective re-ingest
- request accelerated decay / release

### Important warning
Do not implement hard delete first.
Prefer:
- accelerated decay
- retrieval suppression
- export block
- provenance-preserving soft release

### Acceptance criteria
- governance flags exist
- export/re-ingest path respects them
- behavior is auditable

---

## Phase 8 — Optional Promotion Into Existing Governance Systems

### Goal
Bridge collective convergence with current proposals/bridges only after the collective field works.

### Possibilities
- high-confidence convergence event generates a share proposal draft
- strong recurring cross-domain convergence suggests bridge candidates

### Important rule
This is later work.
Do not entangle phase 1-4 with proposal/bridge automation.

---

## 10. API Plan

Suggested first API additions:

### Character visibility

```text
GET /agent/{agent_id}/character/state
GET /agent/{agent_id}/character/seed
GET /agent/{agent_id}/character/self_awareness
```

### Collective visibility

```text
GET /workspace/{workspace_id}/collective/status
GET /workspace/{workspace_id}/collective/packets
GET /workspace/{workspace_id}/collective/events
GET /workspace/{workspace_id}/collective/events/{event_id}
```

### Optional control routes later

```text
POST /agent/collective/reingest
POST /memory/governance/set
POST /memory/release
```

Keep early payloads straightforward JSON. Avoid overengineering schemas in the first pass.

---

## 11. Query / Retrieval Strategy

Collective content should not dominate query results early.

Recommended first approach:

- leave normal query and retrieval mostly unchanged
- optionally include `collective_context` in debug mode or behind a flag
- if relevant convergence events exist, return them separately

Example return shape:

```json
{
  "results": [...],
  "character_context": {...},
  "collective_context": {
    "recent_events": [...],
    "relevant_events": [...]
  }
}
```

Only after validation should collective signals influence ranking.

---

## 12. Persistence Strategy

### Initial persistence
Use append-only JSONL for packets and events.
This matches the project’s existing file-oriented style and is easy to debug.

### Later improvements
Possible future upgrades:
- shard by date/domain
- compact old packet windows into summarized field state
- add embedding references instead of inline vectors

### Keep provenance explicit
Every collective artifact should retain:
- source agent ids
- source packet ids
- source eids if any
- timestamps
- domain

---

## 13. Testing Plan

Claude should add tests incrementally.

### 13.1 Unit tests
Add focused tests for:
- packet model serialization
- collective field append/load
- convergence detection logic
- policy gates

### 13.2 API tests
Add tests for:
- character state endpoints
- collective status/events endpoints
- non-seeded agents returning safe empty fields

### 13.3 Integration tests
Add one or more scenario tests:

1. create workspace
2. create two or three agents with different seeds
3. ingest semantically similar observations into same domain
4. verify collective packet emission
5. verify convergence event creation
6. optionally query and confirm collective context presence

### 13.4 Regression tests
Make sure the following still work after all changes:
- existing ingest/query flows
- proposal pipeline
- bridge pipeline
- character drift/correction
- archive routes
- symbolic resonance in local payloads

---

## 14. Manual Validation Checklist

Claude should be able to run these manually after implementation.

### Step A — create two seeded agents
Use existing `/agent/create` route.

### Step B — inspect character state
Call new character routes and verify:
- seed present
- counts sane
- drift available after some ingests

### Step C — create same-domain overlap
Ingest similar research or creative observations into two agents.

### Step D — inspect collective status
Verify packets are emitted and stored.

### Step E — inspect convergence events
Verify at least one event forms when overlap is strong enough.

### Step F — verify no contamination
Confirm private graphs still differ and identities remain distinct.

### Step G — optional re-ingestion
Re-ingest a collective event and confirm:
- provenance visible
- duplicate protection works
- character identity remains stable

---

## 15. Suggested Patch Sequence for Claude

This is the recommended implementation order.

### Patch 1
Expose character-state API endpoints.

### Patch 2
Add `collective_models.py` with `ResonancePacket`, `ConvergenceEvent`, and helper serializers.

### Patch 3
Add `collective_field.py` with append/load/status functions and simple persistence.

### Patch 4
Modify `fabric.ingest()` to build and append `ResonancePacket` after motif+symbol enrichment.

### Patch 5
Add convergence detection and `events.jsonl` persistence.

### Patch 6
Add collective inspection endpoints in `app.py`.

### Patch 7
Add optional query/debug `collective_context`.

### Patch 8
Add controlled re-ingestion of convergence events.

### Patch 9
Add governance flags and export/re-ingest policy checks.

Each patch should leave the system runnable and testable.
Do not submit one giant rewrite.

---

## 16. Risks and Failure Modes

### 16.1 Identity bleed
Cause:
- raw foreign memories entering private graphs directly

Prevention:
- collective events instead of raw copying
- provenance markers
- policy gating

### 16.2 Event spam
Cause:
- every similar packet creates a new convergence event

Prevention:
- temporal windows
- deduplication
- minimum distinct-agent count
- event persistence threshold

### 16.3 Collective dominance over local retrieval
Cause:
- query ranking starts favoring collective data too early

Prevention:
- return collective context separately at first
- keep private memory primary

### 16.4 Confusion with existing `resonance.py`
Cause:
- reusing symbolic resonance module for hivemind logic

Prevention:
- separate collective modules and naming

### 16.5 Character opacity
Cause:
- adding collective behavior before surfacing self-state

Prevention:
- phase 1 character endpoints first

---

## 17. Longer-Term Future Work (Not Phase 1)

These are later expansions, not immediate deliverables:

- band-aware multi-agent coupling using SRG band identity more directly
- collective bridge suggestion from repeated convergence patterns
- group-level corridor persistence metrics
- multi-workspace federation
- selective shared dream / symbolic field replay
- collective compression and long-horizon summarized field states
- operator dashboards for motif + collective topology visualization

---

## 18. Final Guidance to Claude

Implement this as a **careful extension**, not a replacement.

TORMENT already has:
- strong kernel math
- strong orchestration
- real living character continuity
- governance primitives

The hivemind layer should therefore be:
- additive
- inspectable
- reversible
- policy-gated
- provenance-rich

The first successful version is **not** “all agents think as one.”
The first successful version is:

> agents remain themselves, but the workspace can now detect and preserve moments when their memory fields genuinely converge.

That is the correct first hivemind.

---

## 19. Minimal Success Criteria

This roadmap is considered successfully implemented when all of the following are true:

1. seeded agents expose character self-state through API
2. ingest emits collective resonance packets for meaningful events
3. packets persist per workspace
4. multi-agent convergence events can be detected and listed
5. private memory remains primary and isolated
6. collective provenance is explicit
7. no regressions appear in core ingest/query/character behavior

---

## 20. Practical First Target

If implementation bandwidth is limited, do only this first slice:

- character-state endpoints
- `ResonancePacket`
- collective packet persistence
- simple convergence detection
- collective status/events endpoints

That slice alone will already make the hivemind real enough to inspect, test, and evolve.
