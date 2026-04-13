# TORMENT Agent Spine — Architecture Overview

Status: implemented (v0.1 — deterministic, no LLM)
Date: March 26, 2026
Authors: pzychozen + Claude (Opus 4.6)

---

## What It Is

The Agent Spine is a governed single-pass cognition pipeline that sits above the TORMENT
memory fabric. It transforms a user request into a structured response by routing it
through bounded roles, each of which sees only an aperture-controlled slice of memory.
Durable writes are gated through an archivist authority. Contradictions between roles
are preserved as structured dissent, never silently flattened.

It is **not** an autonomous agent loop, a tool-calling swarm, or a learned router.
It is a deterministic pipeline with clear invariants — designed so that LLM backends
can be introduced later behind stable interfaces without changing the governance model.

---

## Pipeline Flow

```
User Request
    │
    ▼
┌─────────────────────────┐
│  TaskPacket              │  workspace_id, agent_id, user_input, mode, priority
│  (cognition/task_models) │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Router                  │  Detects mode → selects roles, aperture, constraints
│  (cognition/router)      │  Keyword-based in v0.1; LLM-upgradable
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Aperture Builder        │  Queries fabric for memory slice scoped to this request
│  (cognition/apertures)   │  narrow | broad | protected — each with fixed top_k
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Role Execution (sequential, deterministic)                  │
│                                                              │
│  Interpreter → Engineer → Skeptic → Archivist               │
│  (some roles skipped depending on mode)                      │
│                                                              │
│  Each role receives: task, memory_context, prior_outputs     │
│  Each role returns:  RoleOutput with provenance              │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Reintegration Membrane  │  Merges findings, detects dissent, collects proposals,
│  (cognition/reintegration│  enforces governance invariants, builds final answer
│   )                      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Response                │  final_answer, merged_findings, dissent,
│                          │  memory_effects, drift_report, governance_rejections
└─────────────────────────┘
```

---

## The Seven Hard Invariants

These are non-negotiable. They hold in v0.1 and must hold in every future version.

### A — Durable Writes Are Gated

Only the archivist role may propose durable memory writes. No other role writes
to fabric directly. The archivist evaluates proposal quality, skeptic verdict,
and drift state before approving or rejecting each proposal.

**Enforced in**: `roles/archivist.py` (only role that emits memory_proposals),
`reintegration.py` (_apply_governance filters proposals)

### B — Provenance Is Mandatory

Every RoleOutput and every MemoryProposal carries a structured Provenance record
tracking source_type, source_role, parent_ids, derivation_depth, confidence, and
verification_status. If a role forgets to attach provenance, RoleBase.run()
attaches it automatically. Proposals without provenance are rejected in reintegration.

**Enforced in**: `roles/base.py` (run() method), `reintegration.py` (_apply_governance)

### C — Disagreement Is Preserved

When roles contradict each other (e.g. engineer says "proceed", skeptic says "unsafe"),
both claims are recorded in the dissent field as structured objects. Reintegration
never silently flattens or majority-votes away contradictions.

**Enforced in**: `reintegration.py` (_detect_dissent), opposition pair detection

### D — Aperture Is Bounded

Each role sees only the memory slice granted by its aperture type. Narrow aperture
gets 6 private + 3 shared memories. Broad gets 12 + 8. Protected gets 4 + 2 plus
full drift snapshot. Roles cannot reach beyond their aperture.

**Enforced in**: `cognition/apertures.py` (ApertureConfig with fixed top_k values)

### E — Identity Routes Check Drift

Any identity-sensitive request (mode=identity) triggers a drift check. If drift
is in the red zone (≥0.35) or hard_block zone (≥0.50), reintegration blocks all
durable writes. This prevents identity contamination from accumulating in memory.

**Enforced in**: `cognition/router.py` (require_drift_check=True for identity mode),
`reintegration.py` (_apply_governance blocks on drift.requires_block)

### F — Shared Memory Is Read-Only

The aperture builder reads shared (collective) memories for context, but roles
have no mechanism to write to shared memory. Collective promotion is a separate
governance path through the hive mind bridge, not through the spine.

**Enforced in**: `cognition/apertures.py` (shared_memories are query-only)

### G — Low-Trust Cannot Overwrite High-Trust

Provenance tracks derivation_depth and confidence. A derived insight (depth=2,
confidence=0.4) cannot silently replace a direct user statement (depth=0,
confidence=0.9). The archivist reviews provenance before approving proposals,
and reintegration never promotes a low-trust output over a high-trust one.

**Enforced in**: `roles/archivist.py` (_review_proposal checks provenance),
`reintegration.py` (_apply_governance)

---

## Routing Table

The router classifies user input into a mode using keyword patterns, then
looks up the execution plan:

| Mode | Roles Activated | Aperture | Drift Check | Skeptic Pass Required |
|------|----------------|----------|-------------|----------------------|
| engineering | interpreter, engineer, skeptic, archivist | narrow | no | no |
| strategic | interpreter, engineer, skeptic, archivist | broad | no | no |
| identity | interpreter, skeptic, archivist | protected | **yes** | **yes** |
| auto | (resolved to one of the above via detect_mode) | — | — | — |

Mode detection priority: identity > strategic > engineering > auto.

Keyword banks:

- **Identity**: "identity", "rewrite", "core", "seed", "who am i", "collective submission",
  "change personality", "governance", "drift", "persona", "self-concept", "character seed"
- **Strategic**: "what should", "roadmap", "direction", "future", "next step", "become",
  "evolve", "strategy", "long-term", "prioritize", "what next", "planning"
- **Engineering**: "implement", "add", "fix", "build", "code", "create", "refactor",
  "module", "endpoint", "function", "method", "class", "test", "debug", "patch", "feature"

---

## The Four Roles

### Interpreter

Normalizes task intent and surfaces relevant memory context. Classifies intent as
question, action, reflection, or general. Extracts key phrases. Provides a routing
suggestion and memory context summary.

### Engineer

Produces implementation-ready plans. Assesses scope (small/medium/large based on
word count). Builds action steps from the task and relevant memories. Proposes
memory writes for substantial work (≥3 steps, scope medium or large).

### Skeptic

The adversarial reviewer. Runs six checks:

1. Low-confidence priors (< 0.5 from prior roles)
2. Cross-role contradictions (opposition pair detection)
3. Memory proposal overreach (proposals that seem too broad)
4. Identity contamination (for protected aperture only)
5. Drift awareness (flags if drift ≥ 0.35)
6. Missing context (gaps in memory coverage)

Returns a verdict: `skeptic_passed` or `skeptic_flagged`.

### Archivist

The write authority. Collects all memory proposals from prior roles, gets the
skeptic's verdict, reviews each proposal against governance rules (skeptic flags,
drift zone, domain compatibility), and approves or rejects with reasons.

The archivist handles semantic review. Reintegration handles only hard safety
invariants. This split is deliberate — it means governance logic lives in one
place (the archivist), while the reintegration membrane is a simple invariant
enforcer that never second-guesses semantic decisions.

---

## Aperture Configurations

| Aperture | Private top_k | Shared top_k | Depth | Character Mode |
|----------|--------------|-------------|-------|----------------|
| narrow | 6 | 3 | 1 | seed_only |
| broad | 12 | 8 | 2 | full |
| protected | 4 | 2 | 1 | full_drift |

- **seed_only**: loads character seed data only
- **full**: loads full character context (seed + state)
- **full_drift**: loads full character context plus drift snapshot

---

## Data Contracts (schemas/)

### Provenance
```
source_type:       "user_input" | "role_output" | "derived" | "memory"
source_role:       which role produced this (optional)
parent_ids:        [task_id or prior provenance chain]
derivation_depth:  0 = direct user input, 1+ = derived
confidence:        [0.0, 1.0]
verification_status: "unverified" | "skeptic_passed" | "skeptic_flagged"
```

### RoleOutput
```
role_name, summary, findings[], recommendations[], uncertainties[],
contradictions[], memory_proposals[], confidence, provenance
```

### MemoryProposal
```
proposal_id (UUID), summary, content, target_domain,
proposed_strength [0,1], half_life_days, memory_type,
governance_flags {protected, non_shareable, decay_accelerated,
                  collective_export_blocked, eligible_for_collective_review},
provenance, decision ("pending"|"approved"|"rejected"), rejection_reason
```

### DriftReport
```
total_drift, domain_shift, motif_shift, style_shift,
governance_breach (bool), reasons[]

Zones: green (<0.20), yellow (0.20-0.35), red (0.35-0.50), hard_block (≥0.50)
```

---

## Agent Spine ↔ Hive Mind Interaction

The spine and the hive mind are architecturally separate systems that compose
through well-defined touch points:

### Where They Touch

```
                    Agent Spine                        Hive Mind
                    ───────────                        ─────────
User request ──→ [TaskPacket → Router → Roles]
                         │
                         │ aperture queries
                         ▼
                    fabric.query()  ◄──── private + shared memories
                         │                     ▲
                         │                     │ echo reingest
                    [Reintegration]             │
                         │                     │
                    approved proposals         │
                         │                     │
                         ▼                     │
                    fabric.ingest() ────→ kernel coherence ────→ packet emission
                                                                      │
                                                                      ▼
                                                              convergence detection
                                                                      │
                                                                      ▼
                                                              echo reingest ───┘
```

### The Interaction Contract

1. **Spine reads memory via fabric.query()**: The aperture builder calls
   `fabric.query(workspace_id, agent_id, query_text, top_k, domain_id)`
   for both private and shared memories. This is a pure read — no side effects.

2. **Spine reads character state**: The aperture builder calls a character_fn
   to load the agent's seed and current drift state. This feeds into identity
   mode's drift checking.

3. **Spine proposes writes via fabric.ingest()**: Approved archivist proposals
   become ingest calls. Once ingested, the memory enters the normal fabric
   pipeline — kernel coherence scoring, potential packet emission, potential
   convergence with other agents.

4. **Hive mind echoes feed back as shared memory**: When convergence events
   produce echo reingests, those memories appear in the shared graph. The next
   time the spine runs an aperture query, it sees them in shared_memories.
   The spine does not control or trigger convergence — it's a natural consequence
   of the fabric's coherence dynamics.

5. **Collective promotion is NOT through the spine**: The spine writes to
   private memory only (archival_scope="private" in v0.1). Promotion to
   collective/shared is handled by the hive mind's convergence bridge and
   proposal processing — a separate governance path with its own policies.

### What the Spine Should Never Do

- Never write directly to shared memory (Invariant F)
- Never trigger packet emission explicitly (the fabric does this autonomously)
- Never bypass the coherence/strength gate (ingest goes through the normal write path)
- Never override convergence detection thresholds
- Never assume a specific embedder or coherence model

### Open Design Question

**Should archivist-approved writes bypass the fabric write gate?**

The write gate is a physics signal (coherence-based probability of storage). The
archivist is a semantic governor (proposal quality assessment). These are orthogonal
concerns. Current recommendation: archivist proposals go through the same ingest
pipeline including the write gate, because coherence is a structural property that
the archivist cannot evaluate. If this causes approved proposals to be dropped too
often, the write gate can grant a small boost to archivist-approved content rather
than bypassing it entirely.

---

## Implementation Status

### Fully Implemented (v0.1)

| Component | File | Lines |
|-----------|------|-------|
| TaskPacket, RoutingDecision, ReintegrationResult | cognition/task_models.py | 77 |
| Router (keyword-based mode detection) | cognition/router.py | 195 |
| Aperture builder (3 types, memory slicing) | cognition/apertures.py | 279 |
| Reintegration membrane (merge, dissent, governance) | cognition/reintegration.py | 399 |
| Drift check adapter (stub + live) | cognition/drift.py | 155 |
| Pipeline orchestrator | cognition/pipeline.py | 144 |
| RoleBase abstract class | roles/base.py | 80 |
| Interpreter role | roles/interpreter.py | ~150 |
| Engineer role | roles/engineer.py | ~150 |
| Skeptic role | roles/skeptic.py | ~150 |
| Archivist role | roles/archivist.py | ~150 |
| Provenance schema | schemas/provenance.py | 115 |
| RoleOutput schema | schemas/role_output.py | 66 |
| MemoryProposal schema | schemas/memory_proposal.py | 111 |
| DriftReport schema | schemas/drift_report.py | 81 |
| Test suite (5 files) | tests/test_cognition_*.py | 2,844 |
| API endpoint | torment_service/app.py | POST /cognition/run |

### What v0.1 Does NOT Have (by design)

- **No LLM calls**: Roles are deterministic keyword/heuristic transforms. The
  RoleBase interface is designed for LLM backends to be plugged in later.
- **No write-back loop**: Approved proposals are returned in the response but
  not yet auto-ingested into fabric. The endpoint caller is responsible for
  deciding whether to ingest them. (Wiring this is straightforward — call
  fabric.ingest() for each approved proposal.)
- **No collective promotion**: The `eligible_for_collective_review` governance
  flag exists on MemoryProposal but is unused. Collective promotion remains
  the hive mind's domain.
- **No streaming**: Single-pass synchronous only. Adding streaming would be
  a wrapper around the existing pipeline, not a restructuring.

---

## Next Steps Toward MCP Integration

The Agent Spine's clean interface — TaskPacket in, structured JSON out — maps
naturally to MCP tool exposure:

1. **`torment_cognition_run`**: Wraps `POST /cognition/run`. Input: user_input,
   agent_id, workspace_id, mode. Output: the full reintegration result.

2. **`torment_ingest`**: Wraps `POST /agent/ingest`. Direct memory write path.

3. **`torment_query`**: Wraps `POST /agent/query` (fabric.query). Memory retrieval.

4. **`torment_status`**: Wraps `GET /debug/status`. Observability endpoint.

The spine's provenance model and governance invariants carry through to MCP
unchanged — an MCP client receives the same structured dissent, drift reports,
and governance rejections that the REST API returns. The key preparation needed
before MCP exposure is wiring the write-back loop (auto-ingest approved proposals)
and deciding on the auth model (per-workspace tokens vs per-agent tokens).

---

## Reference

- **Design specification**: `docs/archive/AGENT_SPINE_PLAN.md` (526 lines, §0-§16)
- **Acceptance scenarios**: 5 scenarios tested in `test_acceptance_scenarios.py`
- **Roadmap context**: `docs/ROADMAP_post_hivemind_milestone.md` Phase 5
