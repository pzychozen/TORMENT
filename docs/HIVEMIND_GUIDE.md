# Hivemind Usage Guide

How to run multiple AI agents as a collective — with shared resonance, convergence detection, and echo re-ingestion — while each agent keeps its own identity, memory, and character.

---

## Quickstart (copy-paste)

```bash
# 1. Install
pip install -r requirements.txt
pip install sentence-transformers

# 2. Configure (Linux/Mac)
export TORMENT_EMBED_PROVIDER=st
export TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
export TORMENT_EMBED_DEVICE=cpu
export TORMENT_HIVEMIND_ENABLE=1

# 3. Start
python -m torment_service

# 4. Verify
curl http://127.0.0.1:8787/health
```

Windows CMD:
```cmd
set TORMENT_EMBED_PROVIDER=st
set TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
set TORMENT_EMBED_DEVICE=cpu
set TORMENT_HIVEMIND_ENABLE=1
python -m torment_service
```

Or use the Character Forge (`start/torment_character_creator.html`) to generate a complete setup with agents, seeds, and a runnable Python client.

---

## Prerequisites

TORMENT service running at `http://127.0.0.1:8787`. Real embeddings recommended (hash embeddings work but convergence detection is weaker because hash vectors are near-orthogonal).

```bash
# Recommended: SentenceTransformers
pip install sentence-transformers
export TORMENT_EMBED_PROVIDER=st
export TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
export TORMENT_EMBED_DEVICE=cpu
```

---

## 1. Enable the Hivemind

Three feature flags control the memory lifecycle layers. Each is independent:

```bash
# Memory compression — event-gated lifecycle (v2.1)
export TORMENT_COMPRESS_ENABLE=1

# SRG Crystal Attunement — living memory geometry (v2.2)
export TORMENT_SRG_ENABLE=1

# Hivemind — collective resonance coupling (v2.2.1+)
export TORMENT_HIVEMIND_ENABLE=1
```

You can run hivemind without compression or SRG. They compose naturally but don't depend on each other.

Start the service:

```bash
python -m torment_service
```

---

## 2. Create a Workspace with Domains

Solo companions use a single `personal` domain. For a multi-agent team, create a workspace with explicit domains that map to your team's specializations:

```bash
curl -X POST http://127.0.0.1:8787/workspace/create \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "team-alpha",
    "domains": ["research", "engineering", "creative", "operations", "meta"]
  }'
```

Domains are where memory lives. An agent writing to `research` only shares resonance packets within `research`. Convergence detection is domain-scoped — two agents converging in `research` won't trigger events in `creative`.

Choose domains that reflect how your team thinks, not how many agents you have. Five agents can all write to `research` if they're all researching. An agent can write to different domains on different ingests.

---

## 3. Create Agents with Character Seeds

Each agent gets its own identity through a character seed. The seed is a gravitational basin — memory does the rest.

### Example: 5-Agent Specialized Team

**Research Agent** — deep analysis, paper reading, knowledge synthesis:

```bash
curl -X POST http://127.0.0.1:8787/agent/create \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "team-alpha",
    "agent_id": "researcher",
    "seed": {
      "seed_text": "A methodical analyst who reads deeply, connects ideas across fields, and values evidence over opinion. Asks precise questions. Comfortable with uncertainty.",
      "seed_id": "researcher_v1"
    }
  }'
```

**Builder Agent** — code, architecture, implementation:

```bash
curl -X POST http://127.0.0.1:8787/agent/create \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "team-alpha",
    "agent_id": "builder",
    "seed": {
      "seed_text": "A pragmatic engineer who builds working systems. Prefers clean interfaces, testable code, and incremental progress over grand redesigns. Ships early, iterates fast.",
      "seed_id": "builder_v1"
    }
  }'
```

**Creative Agent** — content, video, visual, narrative:

```bash
curl -X POST http://127.0.0.1:8787/agent/create \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "team-alpha",
    "agent_id": "creative",
    "seed": {
      "seed_text": "A visual storyteller who thinks in images, metaphors, and emotional arcs. Finds the human angle in technical topics. Turns complexity into clarity.",
      "seed_id": "creative_v1"
    }
  }'
```

**Planner Agent** — strategy, coordination, oversight:

```bash
curl -X POST http://127.0.0.1:8787/agent/create \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "team-alpha",
    "agent_id": "planner",
    "seed": {
      "seed_text": "A strategic coordinator who sees the whole board. Tracks dependencies, identifies bottlenecks, and keeps the team aligned on shared goals. Thinks in timelines and trade-offs.",
      "seed_id": "planner_v1"
    }
  }'
```

**Marketing Agent** — audience, positioning, communication:

```bash
curl -X POST http://127.0.0.1:8787/agent/create \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "team-alpha",
    "agent_id": "marketer",
    "seed": {
      "seed_text": "An audience-first communicator who understands what people care about and why. Translates features into benefits, complexity into narrative, and ideas into campaigns.",
      "seed_id": "marketer_v1"
    }
  }'
```

Each agent now has its own kernel state, memory graph, drift tracker, and character basin — completely independent.

---

## 4. Feed the Agents

Ingest observations for each agent. The `domain_id` parameter controls which domain the memory lands in and which collective field it emits packets to.

```bash
# Researcher finds something interesting
curl -X POST http://127.0.0.1:8787/agent/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "team-alpha",
    "agent_id": "researcher",
    "text": "Found a paper showing transformer attention patterns mirror oscillator coupling dynamics. The math maps directly to our kernel architecture.",
    "step": 1,
    "domain_id": "research"
  }'

# Builder is working on something related
curl -X POST http://127.0.0.1:8787/agent/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "team-alpha",
    "agent_id": "builder",
    "text": "Implementing the new oscillator coupling module. Noticed the attention weight matrix looks structurally identical to our phase-lock computation.",
    "step": 1,
    "domain_id": "research"
  }'
```

When hivemind is enabled, every ingest above coherence 0.15 automatically emits a `ResonancePacket` into the workspace collective field. You don't call anything extra — it happens inside `ingest()`.

### Coherence and Adaptive Scaling

Coherence is computed from the TriOcta kernel's phase dispersion. As of v2.3.1, the kernel uses **adaptive DISP_SCALE** — the sensitivity parameter self-calibrates to the embedding distribution, so it works identically with HashEmbedding, SentenceTransformers, or any future embedder without manual tuning.

The coherence pipeline: `disp → adaptive_scale → coh_phase → coh_raw → coh_ema`

The adaptive scale tracks a rolling window of dispersion values and computes `effective_scale = k * (mean + std)` with `k=2.0`. During the first 10 ingests (warmup), it blends from a fixed fallback (1.50) to the adaptive estimate.

You can inspect the current effective scale in any ingest response under `result["debug"]["effective_disp_scale"]`. The coherence value itself is at `result["debug"]["coherence"]`.

---

## 5. How Convergence Works

The collective field watches for similarity between packets from different agents in the same domain. When two packets have cosine similarity >= 0.72 and come from different agents, a `ConvergenceEvent` fires.

Confidence is a composite score:

| Component | Weight | What it measures |
|-----------|--------|------------------|
| Semantic similarity | 50% | Embedding cosine distance |
| Phase alignment | 15% | Same kernel cycle stage and identity state |
| Symbol alignment | 15% | Matching state symbols and loop types |
| Motif alignment | 20% | Overlapping motif patterns |

The event must reach confidence >= 0.45 to be recorded.

Check the field status:

```bash
curl http://127.0.0.1:8787/workspace/team-alpha/collective/status
```

View convergence events:

```bash
curl http://127.0.0.1:8787/workspace/team-alpha/collective/events
```

View a specific event:

```bash
curl http://127.0.0.1:8787/workspace/team-alpha/collective/events/cev_abc123
```

---

## 6. Echo Re-Ingestion

When agents converge, you can re-ingest the convergence event as a low-amplitude echo into a target agent. This is manual — you trigger it through the API:

```bash
curl -X POST http://127.0.0.1:8787/workspace/team-alpha/collective/reingest \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "creative",
    "event_id": "cev_abc123"
  }'
```

This tells the creative agent: "the researcher and builder both noticed something about oscillator coupling and attention patterns." The creative agent receives a thematic whisper, not a memory transplant.

### What happens inside

The request runs through the **7-gate policy engine** before anything is ingested:

1. **Confidence** — event confidence must be >= 0.60 (stricter than detection)
2. **Agent opt-in policy gate** — the policy has an opt-in/opt-out check, but
   agent-level collective re-ingestion opt-out is not currently exposed as a
   persistent production control
3. **Domain match** — event domain must match the target agent's domain exactly
4. **Deduplication** — same event+agent pair can never be reingested twice
5. **Rate limit** — max 3 reingests per agent per hour
6. **Drift budget** — target agent's identity drift must be within tolerance (< 0.30)
7. **Eligible** — all gates passed

If any gate fails, you get back which gate failed and why. The policy is conservative by design.

> **Gate 2 operational status:** Agent-level collective re-ingestion opt-out
> exists as an in-memory policy gate, but normal operators cannot maintain that
> state across production re-ingestion calls today. This is known bounded
> terrain, not a newly discovered security-boundary failure. For actual
> memory-level controls, use `non_shareable` and
> `collective_export_blocked`. Those flags control an individual memory's
> collective export and are not equivalent to agent-level opt-out.

### Echo properties

Echoes are structurally different from normal memories:

- **Low amplitude**: 0.25x default strength (configurable), 0.40x hard cap
- **Terminal**: double-blocked governance — `collective_reingest_blocked` and `collective_export_blocked` both true. An echo cannot re-emit packets or be re-echoed.
- **Provenance-marked**: tagged as `provenance: "collective"` with source event ID and contributing agents
- **Retrieval-discounted**: 0.5x weight during query scoring, so echoes never dominate retrieval results
- **Prefixed**: text starts with `[collective echo]` so the LLM knows this is a thematic influence, not autobiographical memory

You can override echo strength (up to the 0.40 cap):

```bash
curl -X POST http://127.0.0.1:8787/workspace/team-alpha/collective/reingest \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "creative",
    "event_id": "cev_abc123",
    "echo_strength_override": 0.35
  }'
```

---

## 7. Automatic Proposal Bridge

When convergence events are persistent — the same domain+motif pattern fires 2+ times in 2 hours — the proposal bridge automatically drafts a share proposal for operator review.

Proposals are **never auto-approved**. They go into the pending queue for the relevant domain:

```bash
# View pending proposals
curl http://127.0.0.1:8787/workspace/team-alpha/domain/research/proposals

# Approve a proposal
curl -X POST http://127.0.0.1:8787/workspace/domain/proposals/decide \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "team-alpha",
    "domain_id": "research",
    "proposal_id": "prop_xyz",
    "decision": "approve"
  }'
```

The bridge has its own gating separate from echo re-ingestion:

| Check | Threshold | Purpose |
|-------|-----------|---------|
| Confidence | >= 0.70 | Higher bar than detection or reingest |
| Persistence | >= 2 events in 2 hours | Pattern must recur before proposing |
| Event dedup | Event not already proposed | No duplicate proposals |
| Domain cooldown | 30 minutes between proposals | Prevents proposal spam |
| Max pending | 5 per domain | Caps unreviewed queue |

Check proposal bridge status:

```bash
curl http://127.0.0.1:8787/workspace/team-alpha/collective/proposals/status
```

---

## 8. Memory Governance

Every memory has governance flags that control what it can do in the collective:

**Source protection** (controls what leaves private memory):
- `protected` — immune to automated compression/decay
- `non_shareable` — excluded from collective packets entirely
- `collective_export_blocked` — won't emit to collective field

**Derived handling** (controls synthetic material after arrival):
- `collective_reingest_blocked` — won't accept echoes back from collective
- `decay_accelerated` — faster forgetting (ignored if `protected` is true)

Set governance flags on a specific memory:

```bash
curl -X POST http://127.0.0.1:8787/memory/governance/set \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "team-alpha",
    "agent_id": "researcher",
    "eid": 42,
    "flags": {
      "non_shareable": true
    },
    "actor": "operator",
    "source": "manual"
  }'
```

Read governance flags:

```bash
curl "http://127.0.0.1:8787/memory/governance/get?workspace_id=team-alpha&agent_id=researcher&eid=42"
```

View the audit trail:

```bash
curl http://127.0.0.1:8787/workspace/team-alpha/governance/audit
```

---

## 9. Monitoring Agent Health

Each agent exposes a self-state view showing identity health, drift, and collective participation:

```bash
curl "http://127.0.0.1:8787/agent/researcher/self-state?workspace_id=team-alpha"
```

Returns drift score, seed basin geometry, memory tier counts, phase timing, and SRG attunement. Use this to check whether an agent is drifting from its character seed after receiving collective echoes.

---

## 10. Querying with Collective Context

Normal queries already include collective echoes in results (at 0.5x retrieval weight):

```bash
curl -X POST http://127.0.0.1:8787/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "team-alpha",
    "agent_id": "creative",
    "query": "What ideas have been emerging about oscillator patterns?",
    "top_k": 10,
    "continuity_debug": true
  }'
```

The `character_context` in the response includes spirit return summaries and voice cues. Echoes show up naturally in results but ranked lower than the agent's own memories.

---

## 11. Domain Strategy

How you map domains to your team matters. Some patterns:

**By discipline** (recommended for specialized teams):
```json
["research", "engineering", "creative", "operations", "meta"]
```
Agents write to whichever domain fits what they're currently doing. A researcher writing code would ingest to `engineering`. Convergence happens within disciplines.

**By project**:
```json
["project-alpha", "project-beta", "infrastructure", "meta"]
```
Good when agents work on distinct projects but might find cross-project patterns.

**By information type**:
```json
["facts", "opinions", "decisions", "questions", "meta"]
```
Different structure. Good for separating what agents know from what they think.

`meta` is useful in all layouts — it's where agents can put coordination, reflection, and process observations.

---

## 12. Tuning the Collective

### Make convergence easier to trigger

Lower the similarity threshold (not recommended below 0.60):

In `collective_field.py`, adjust `CONVERGENCE_SIM_THRESHOLD` (default 0.72).

### Make echoes stronger

Set environment variable:

```bash
export TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT=0.70  # default 0.50
```

Or override per-reingest with `echo_strength_override` (max 0.40).

### Make proposals trigger faster

The proposal bridge defaults are conservative. For faster feedback loops in development, you can modify the bridge initialization in `fabric.py` or pass config when constructing `CollectiveProposalBridge`:

- Lower `persistence_min` from 2 to 1 (proposals on first convergence)
- Shrink `persistence_window` from 7200 to 3600
- Reduce `domain_cooldown` from 1800 to 600
- Raise `max_pending_per_domain` if needed

### Make the policy engine less strict

Lower `DEFAULT_CONFIDENCE_THRESHOLD` from 0.60 (not recommended below 0.45).
Raise `DEFAULT_DRIFT_BUDGET` from 0.30 (allows more identity drift before blocking).
Raise `DEFAULT_RATE_LIMIT_MAX` from 3 per hour.

These are all in `collective_policy.py`.

---

## 13. The Five Invariants

These hold true across all modules and cannot be broken by configuration:

1. **Protected memories are never weakened automatically.** The `protected` flag blocks all automated compression, decay, and strength reduction.

2. **Non-shareable or export-blocked memories never emit packets.** If a memory has `non_shareable` or `collective_export_blocked` set, it will never produce a ResonancePacket.

3. **Collective echoes are terminal by default.** Every echo gets `collective_reingest_blocked=True` and `collective_export_blocked=True`. Echoes cannot echo.

4. **Echoes are influences, not autobiography.** Echoes carry `provenance: "collective"`, get 0.5x retrieval weight, and are prefixed with `[collective echo]`. They're thematic whispers, not memory transplants.

5. **Collective provenance cannot outrank seed/canon identity.** The drift budget gate in the policy engine blocks reingest when an agent's identity is already drifting. Seed memories always outweigh collective echoes in retrieval.

---

## 14. Full Workflow Example

Here's the complete flow for a 3-agent team detecting and acting on convergence:

```bash
# 1. Setup
export TORMENT_HIVEMIND_ENABLE=1
export TORMENT_EMBED_PROVIDER=st
export TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5

# 2. Create workspace
curl -X POST http://127.0.0.1:8787/workspace/create \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "demo", "domains": ["research", "meta"]}'

# 3. Create agents
curl -X POST http://127.0.0.1:8787/agent/create \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "demo", "agent_id": "alice", "seed": {"seed_text": "Analytical. Connects patterns across domains.", "seed_id": "alice_v1"}}'

curl -X POST http://127.0.0.1:8787/agent/create \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "demo", "agent_id": "bob", "seed": {"seed_text": "Practical builder. Turns ideas into working systems.", "seed_id": "bob_v1"}}'

curl -X POST http://127.0.0.1:8787/agent/create \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "demo", "agent_id": "carol", "seed": {"seed_text": "Strategic thinker. Sees the big picture.", "seed_id": "carol_v1"}}'

# 4. Feed agents (both writing about similar themes in the same domain)
curl -X POST http://127.0.0.1:8787/agent/ingest \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "demo", "agent_id": "alice", "text": "The recursive structure in these oscillator networks suggests self-similar memory organization.", "step": 1, "domain_id": "research"}'

curl -X POST http://127.0.0.1:8787/agent/ingest \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "demo", "agent_id": "bob", "text": "Building the oscillator coupling module. The recursive pattern in the network topology matches memory graph structure.", "step": 1, "domain_id": "research"}'

# 5. Check for convergence
curl http://127.0.0.1:8787/workspace/demo/collective/events

# 6. If convergence detected, reingest into carol
curl -X POST http://127.0.0.1:8787/workspace/demo/collective/reingest \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "carol", "event_id": "cev_..."}'

# 7. Carol now has a thematic echo about oscillator-memory parallels
curl -X POST http://127.0.0.1:8787/agent/query \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "demo", "agent_id": "carol", "query": "What patterns are emerging in the research?", "top_k": 5}'

# 8. Monitor health
curl "http://127.0.0.1:8787/agent/carol/self-state?workspace_id=demo"
```

---

## 15. What Hivemind Is Not

The hivemind is a resonance field, not a shared database. A few things it does not do:

- **No shared memory**: Each agent has a private memory graph. Echoes are low-amplitude influences, not copies of other agents' memories.
- **No real-time dispatch**: When convergence fires, it doesn't push a notification to another agent. The operator (you or your orchestration layer) decides when to reingest.
- **No automatic personality merging**: Characters stay distinct. The drift budget gate blocks reingest if an agent's identity is already shifting.
- **No transitive echoes**: If Alice's echo enters Bob, Bob cannot re-emit it. Echoes are terminal.
- **No cross-domain convergence**: Convergence detection is scoped to a single domain. Two agents converging in `research` and `creative` independently won't trigger a combined event.

The system is conservative, asymmetric, and slightly annoying to trigger. That is a feature, not a flaw.

---

## Appendix: Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TORMENT_HIVEMIND_ENABLE` | `0` | Master switch for collective resonance |
| `TORMENT_SRG_ENABLE` | `0` | SRG Crystal Attunement layer |
| `TORMENT_COMPRESS_ENABLE` | `0` | Event-gated compression lifecycle |
| `TORMENT_EMBED_PROVIDER` | `hash` | Embedding provider (`hash`, `st`, `ollama`) |
| `TORMENT_EMBED_MODEL` | — | Model name for ST/Ollama |
| `TORMENT_EMBED_DEVICE` | `cpu` | Device for ST embeddings |
| `TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT` | `0.50` | Retrieval weight for collective-provenance memories |
| `TORMENT_CHARACTER_ENABLE` | `1` | Character identity layer |
| `TORMENT_CHARACTER_CORRECTION_THRESHOLD` | `0.35` | Drift threshold for gravity correction |
| `TORMENT_CHARACTER_GRAVITY_STRENGTH` | `0.12` | Correction memory strength |
| `TORMENT_CHARACTER_DRIFT_CHECK_EVERY` | `25` | Steps between drift checks |
| `TORMENT_CHARACTER_DRIFT_WINDOW_STEPS` | `500` | Lookback window for drift |

---

## Appendix: Key Thresholds

| Threshold | Value | Where |
|-----------|-------|-------|
| Adaptive DISP_SCALE (k) | 2.0 | `memory_kernel.py` |
| Adaptive warmup steps | 10 | `memory_kernel.py` |
| Adaptive window size | 50 | `memory_kernel.py` |
| DISP_SCALE fallback | 1.50 | `memory_kernel.py` |
| COH_SMOOTH (EMA factor) | 0.70 | `memory_kernel.py` |
| COH_FLOOR | 0.05 | `memory_kernel.py` |
| Write gate (strength) | >= 0.55 | `fabric.py` ingest |
| Packet emission coherence | >= 0.15 | `fabric.py` ingest |
| Convergence similarity | >= 0.72 | `collective_field.py` |
| Convergence min confidence | >= 0.45 | `collective_field.py` |
| Convergence min agents | 2 | `collective_field.py` |
| Convergence cooldown | 30s | `collective_field.py` |
| Policy confidence gate | >= 0.60 | `collective_policy.py` |
| Policy rate limit | 3/hour | `collective_policy.py` |
| Policy drift budget | < 0.30 | `collective_policy.py` |
| Echo strength default | 0.25x | `collective_policy.py` |
| Echo strength cap | 0.40x | `collective_policy.py` |
| Retrieval discount | 0.50x | `fabric.py` query |
| Proposal confidence | >= 0.70 | `collective_proposals.py` |
| Proposal persistence | 2+ in 2h | `collective_proposals.py` |
| Proposal domain cooldown | 30 min | `collective_proposals.py` |
| Max pending proposals/domain | 5 | `collective_proposals.py` |
