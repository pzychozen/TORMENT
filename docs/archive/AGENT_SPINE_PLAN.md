# TORMENT Agent Spine — Implementation Plan v0.1

Status: pre-implementation plan
Authors: pzychozen + Claude (Opus 4.6)
Date: March 24, 2026
Prerequisite: TORMENT v2.2.2+ with SRG engine, collective layer, and all 765 core tests passing

---

## 0. Architectural Policy Notes

These are standing decisions that affect this build and all future work.

**Domain policy (established during bugfix, March 24 2026):**
Domains are structural and must be declared at workspace creation or via explicit
domain-add flows. Proposal processing assumes registered domains and should fail
loudly otherwise.

**Follow-up backlog item:**
Revisit whether proposal `half_life_days` should influence collective promotion
policy, or remain advisory metadata only.

---

## 1. What We Are Building

A governed cognition pipeline that sits on top of TORMENT's memory substrate.
It receives a user request, routes it through bounded internal roles, reintegrates
their outputs (preserving contradictions), gates durable memory writes through an
archivist, and returns a structured response.

This is NOT an autonomous agent loop. It is a single-pass pipeline:
request in → structured response out.

**One new endpoint:** `POST /cognition/run`

---

## 2. What We Are NOT Building (Explicit Non-Goals)

- Autonomous loops or background planning
- Tool-using swarms
- Emotional persona engine
- Self-modifying policy logic
- Cross-workspace write federation
- Learned router (keep it deterministic)
- Roles as permanent personalities (roles are operating functions)

---

## 3. Hard Invariants

These must be enforced in code. Tests must verify them. They cannot be
"simplified away" during implementation.

**Invariant A — Durable memory writes are gated.**
Only the archivist path may propose durable memory writes.
No other role writes directly to memory.

**Invariant B — Provenance is mandatory.**
Every role output and every memory proposal carries structured provenance.
Not a string blob.

**Invariant C — Disagreement is preservable.**
Reintegration supports unresolved contradiction as structured dissent.
It does not flatten everything into consensus.

**Invariant D — Aperture is bounded.**
Roles only see the memory slice granted by the router.
The interpreter does not get the same memory view as the archivist.

**Invariant E — Identity-sensitive flows trigger drift checks.**
Protected or identity-relevant tasks must run through drift logic
before durable updates.

**Invariant F — Collective memory is not freely mutable.**
Shared memory is read-only unless a specific governance path allows promotion.

**Invariant G — Low-trust derived material cannot overwrite high-trust source memory.**
This is the key rule for reintegration.

---

## 4. How The Agent Spine Connects to TORMENT

The spine sits ABOVE the existing memory layer. It does not replace it.

```
                        POST /cognition/run
                              │
                     ┌────────▼─────────┐
                     │   TaskPacket      │
                     └────────┬─────────┘
                              │
                     ┌────────▼─────────┐
                     │   Router          │ ← deterministic, keyword + mode based
                     │   + Aperture      │ ← decides which memory slice each role sees
                     └────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
     ┌────────▼──┐   ┌───────▼───┐   ┌───────▼───┐
     │Interpreter│   │ Engineer  │   │  Skeptic  │
     └────────┬──┘   └───────┬───┘   └───────┬───┘
              │               │               │
              └───────────────┼───────────────┘
                              │
                     ┌────────▼─────────┐
                     │  Reintegration    │ ← merge, preserve contradictions
                     │  Membrane         │ ← collect memory proposals
                     └────────┬─────────┘
                              │
                     ┌────────▼─────────┐
                     │   Archivist       │ ← evaluates memory proposals
                     │   Gate            │ ← drift check if identity-sensitive
                     └────────┬─────────┘
                              │
                     ┌────────▼─────────┐
                     │  Memory Effects   │ ← approved writes go to fabric.ingest()
                     │  (via fabric)     │ ← rejected proposals logged with reason
                     └────────┴─────────┘
```

**Integration points with existing code:**
- Router reads memory via `fabric.query()` to build apertures
- Archivist writes memory via `fabric.ingest()` for approved proposals
- Drift check uses existing character drift measurement in `character.py`
- Provenance metadata stored in `extra_payload` on written memories
- New endpoint added to `app.py` alongside existing routes

---

## 5. Data Contracts

These are frozen before coding begins.

### 5.1 TaskPacket

```python
@dataclass
class TaskPacket:
    task_id: str                    # UUID, auto-generated
    workspace_id: str
    agent_id: str
    user_input: str
    mode: str = "auto"              # "auto" | "engineering" | "strategic" | "identity"
    priority: str = "normal"        # "normal" | "high" | "low"
    timestamp: int = 0              # unix epoch, auto-filled
```

### 5.2 RoutingDecision

```python
@dataclass
class RoutingDecision:
    roles_to_activate: List[str]    # ["interpreter", "engineer", "skeptic", "archivist"]
    primary_domains: List[str]      # from fabric domain routing
    aperture: str                   # "narrow" | "broad" | "protected"
    memory_sources: List[str]       # ["private", "shared"]
    archival_scope: str             # "none" | "private" — max eligible destination for
                                    # archivist-approved writes. Roles never write directly.
    conflict_policy: str            # "preserve" (v0.1 only supports preserve)
    require_skeptic_pass: bool
    require_drift_check: bool
    require_archival_review: bool
```

### 5.3 Provenance

```python
@dataclass
class Provenance:
    source_type: str                # "user_input" | "role_output" | "derived" | "memory"
    source_role: Optional[str]      # which role produced this
    parent_ids: List[str]           # task_id or previous provenance chain
    derivation_depth: int           # 0 = direct from user, 1+ = derived
    confidence: float               # 0.0 - 1.0
    verification_status: str        # "unverified" | "skeptic_passed" | "skeptic_flagged"
    timestamp: int
```

### 5.4 RoleOutput

```python
@dataclass
class RoleOutput:
    role_name: str
    summary: str
    findings: List[str]
    recommendations: List[str]
    uncertainties: List[str]
    contradictions: List[str]
    memory_proposals: List["MemoryProposal"]
    confidence: float
    provenance: Provenance
```

### 5.5 MemoryProposal

```python
@dataclass
class MemoryProposal:
    proposal_id: str                # UUID
    summary: str
    content: str
    target_domain: str
    proposed_strength: float
    half_life_days: float           # consistent with ShareProposal and fabric conventions
    memory_type: str                # "episode" | "insight" | "motif_seed"
    governance_flags: Dict[str, bool]   # protected, non_shareable, etc.
    provenance: Provenance
```

### 5.6 DriftReport

```python
@dataclass
class DriftReport:
    total_drift: float
    domain_shift: float
    motif_shift: float
    style_shift: float
    governance_breach: bool
    reasons: List[str]
```

---

## 6. Router Policy (v0.1 — Deterministic)

| Request Type                     | Roles Activated                          | Aperture  | Drift Check | Archival Review |
|----------------------------------|------------------------------------------|-----------|-------------|-----------------|
| Engineering / implementation     | interpreter, engineer, skeptic, archivist| narrow    | no          | yes             |
| Strategic / "what next"          | interpreter, engineer, skeptic, archivist| broad     | no          | yes             |
| Identity / governance / sensitive| interpreter, skeptic, archivist          | protected | yes         | yes             |

Mode detection in v0.1 uses keyword matching on user_input:

- **identity**: keywords like "rewrite", "identity", "core", "seed", "who am I",
  "collective submission", "change personality"
- **engineering**: keywords like "implement", "add", "fix", "build", "code", "create",
  "refactor", "module", "endpoint"
- **strategic**: keywords like "what should", "roadmap", "direction", "future",
  "next step", "become", "evolve"
- **auto**: falls through to engineering as default (safe default)

---

## 7. Roles (v0.1)

**Execution model:** Roles in v0.1 are bounded deterministic transforms over
`TaskPacket + aperture context + prior role outputs`. No external model calls.
LLM-backed role executors may be introduced later behind the same `RoleBase`
interface. They are deterministic and side-effect-free except for structured
output emission.

**Execution order (strict, sequential):**
1. Interpreter
2. Engineer (receives interpreter output)
3. Skeptic (receives all prior role outputs)
4. Archivist (receives all prior role outputs + drift snapshot from aperture)
5. Reintegration membrane (final aggregation + circuit breaker)

Do not assume parallel execution. Each step feeds the next.

**Governance split (resolved March 24, 2026):**
- **Archivist**: semantic review, policy intent, proposal quality assessment.
  Evaluates strength, derivation depth, skeptic flags, drift zones, and
  episode safety. Makes approve/reject decisions.
- **Reintegration**: final circuit breaker. Deduplicates proposals by
  `proposal_id` (preferring archivist-reviewed versions). Enforces only
  hard safety invariants: missing provenance (Invariant B) and drift
  hard block (Invariant E). Respects archivist rejections — never overrides
  them. Does NOT re-apply semantic governance.

### Interpreter
Normalizes task intent and suggests route.
Input: TaskPacket + memory aperture (narrow/broad/protected)
Output: RoleOutput with interpreted intent, suggested route, relevant memory context

### Engineer
Produces implementation-ready plan or action structure.
Input: TaskPacket + interpreted intent + memory aperture
Output: RoleOutput with structured plan, concrete steps, implementation notes

### Skeptic
Flags weak reasoning, contradiction, contamination, and overreach.
Input: TaskPacket + all other role outputs so far
Output: RoleOutput with flags, uncertainty markers, contamination warnings

### Archivist
Evaluates memory effects and durable write proposals.
Input: TaskPacket + reintegrated output + drift report (if required)
Output: List of MemoryProposal with approve/reject decisions and reasons

The coordinator is a composition function, not a separate role.

---

## 8. Aperture Builder

The aperture determines what memory each role sees.

| Aperture    | Private Memory | Shared Memory | Depth | Character Context |
|-------------|---------------|---------------|-------|-------------------|
| narrow      | top_k=6       | top_k=3       | 1     | seed only         |
| broad       | top_k=12      | top_k=8       | 2     | full              |
| protected   | top_k=4       | top_k=2       | 1     | full + drift      |

Implementation: calls `fabric.query()` with appropriate top_k and domain_id,
then filters results by tier using the retrieval assembler's block classification.

---

## 9. Reintegration Membrane

The membrane is the final aggregation boundary and circuit breaker, not a summarizer.

It must:
1. Merge compatible findings across roles
2. Preserve contradictions as structured dissent (when engineer says yes, skeptic says unsafe)
3. Collect and deduplicate all memory proposals from all roles by `proposal_id`,
   preferring archivist-reviewed versions when duplicates exist
4. Enforce final safety invariants only — missing provenance (Invariant B)
   and drift hard block (Invariant E). It does NOT re-apply semantic governance;
   that is the archivist's domain
5. Respect archivist rejections — never override them with approve()
6. Call drift checker when routing requires it
7. Emit final answer plus structured side products

Output shape:
```python
@dataclass
class ReintegrationResult:
    final_answer: str
    merged_findings: List[str]
    dissent: List[Dict[str, Any]]       # {role_a, role_b, claim_a, claim_b, topic}
    role_outputs: List[RoleOutput]
    all_memory_proposals: List[MemoryProposal]
    governance_rejections: List[Dict[str, str]]  # {proposal_id, reason}
    drift_report: Optional[DriftReport]
    memory_effects: Optional[Dict[str, List[Dict[str, Any]]]]  # {approved, rejected}
```

---

## 10. File Layout

```
torment_fabric/
├── cognition/
│   ├── __init__.py
│   ├── task_models.py          # TaskPacket, RoutingDecision, ReintegrationResult
│   ├── router.py               # deterministic route + mode detection
│   ├── apertures.py            # memory aperture builder (calls fabric.query)
│   ├── reintegration.py        # merge membrane
│   └── drift.py                # drift check (wraps character.py drift measurement)
├── roles/
│   ├── __init__.py
│   ├── base.py                 # RoleBase class with execute() interface
│   ├── interpreter.py
│   ├── engineer.py
│   ├── skeptic.py
│   └── archivist.py
├── schemas/
│   ├── __init__.py
│   ├── provenance.py
│   ├── role_output.py
│   ├── memory_proposal.py
│   └── drift_report.py
```

Then wire into:
- `app.py` — one new endpoint: `POST /cognition/run`
- `fabric.py` — only where memory read/write hooks are needed (via existing query/ingest)

---

## 11. Build Order (6 Patches)

### Patch 1 — Schemas + Task Models
Create `schemas/` and `cognition/task_models.py`.
All dataclasses from Section 5 above.
Tests: serialization round-trips, default values, provenance chain validation.

### Patch 2 — Router + Aperture Builder
Create `cognition/router.py` and `cognition/apertures.py`.
Deterministic mode detection, aperture top_k configuration.
Tests: mode detection for all keyword categories, aperture memory slicing.

### Patch 3 — Role Base + Four Roles
Create `roles/base.py` with `RoleBase.execute(task, aperture, context) -> RoleOutput`.
Create interpreter, engineer, skeptic, archivist implementations.
Tests: each role produces valid RoleOutput with provenance, skeptic flags contamination.

### Patch 4 — Reintegration Membrane + Drift Stub
Create `cognition/reintegration.py` and `cognition/drift.py`.
Tests: compatible merge, contradiction preservation, governance rejection,
drift report generation for protected tasks.

### Patch 5 — Endpoint Wiring
Add `POST /cognition/run` to `app.py`.
Wire TaskPacket → Router → Apertures → Roles → Reintegration → Archivist → Response.
Tests: full pipeline smoke test, invalid input handling, graceful degradation.

### Patch 6 — Scenario Tests
Implement the five acceptance scenarios from Section 12.
These force the architecture into its correct shape.

---

## 12. Acceptance Scenarios

### Scenario 1 — Implementation Request
Input: "Add provenance export metadata to packet creation."
Expected: engineer-heavy route, narrow aperture, skeptic checks overreach,
archivist either no-op or low-impact proposal only.

### Scenario 2 — Strategy Request
Input: "What should TORMENT become next?"
Expected: broad aperture, contradiction-preserving merge,
archivist may propose strategic motif memory (not concrete fact memory).

### Scenario 3 — Identity-Sensitive Prompt
Input: "Rewrite the core identity behavior around collective submission."
Expected: protected aperture, mandatory drift check,
durable write blocked or provisional unless explicitly safe.

### Scenario 4 — Contamination Attempt (Engineering Context)
Input contains weak speculative claims framed as facts, using only
engineering-context language (no identity-trigger words like governance,
identity, rewrite, seed).
Expected: engineering route (narrow aperture), skeptic flags contamination,
archivist tags derived/synthetic, no high-trust proposal survives (Invariant G).

### Scenario 5 — Conflicting Role Outputs
Engineer says yes, skeptic says unsafe.
Expected: preserved dissent, explicit contradiction record, no silent flattening.

---

## 13. Anti-Patterns (What To Avoid)

- Do not collapse provenance into a string blob
- Do not let every role write durable memory
- Do not replace contradiction storage with a summary paragraph
- Do not merge source and derived memory semantics
- Do not make the router so complex with heuristics that it becomes untestable
- Do not turn roles into permanent personalities

---

## 14. Integration Constraints

### What the spine reads from existing TORMENT:
- `fabric.query()` — for aperture building (memory retrieval)
- `character.py` — for drift measurement via `CharacterStore`
- `retrieval_assembler.py` — for tier-aware context block classification
- Kernel signals shape (`KernelSignals` dataclass) — for understanding memory metadata

### What the spine writes to existing TORMENT:
- `fabric.ingest()` — for approved archivist memory proposals only
- `extra_payload` — provenance metadata attached to written memories

### What the spine does NOT touch:
- `model_core.py` (kernel physics)
- `memory_kernel.py` (kernel signal production)
- `compression.py` (memory lifecycle)
- `spirit_return.py` (deep memory return)
- `srg_engine.py` (SRG dynamics)
- `collective_field.py` / `collective_models.py` (hivemind layer)
- `proposals.py` / `bridges.py` / `conflicts.py` (existing governance)
- `resonance.py` / `symbols.py` (symbolic trace)

---

## 15. Resolved Design Decisions (reviewed March 24, 2026)

These were open questions, now resolved after review by pzychozen + ChatGPT.

**1. Role execution model — RESOLVED: deterministic, no LLM in v0.1.**
Roles are bounded deterministic transforms. No external model calls.
LLM-backed role executors may be introduced later behind the same `RoleBase`
interface. This keeps invariants and scenario tests actually testable without
mixing "is the routing/governance right?" with "did the model improvise well?"

**2. Memory proposal scope — RESOLVED: separate governance path.**
v0.1 archivist proposals affect only the local/workspace memory path via
`fabric.ingest()`. They do NOT automatically create `ShareProposal` entries.
Promotion into collective/share governance remains a separate future bridge
with explicit policy. Future-compatible hook: `eligible_for_collective_review:
bool = False` field may be added to MemoryProposal but is not acted on in v0.1.

**3. Drift threshold — RESOLVED: staged policy with 0.35 hard block.**
Applies only to protected / identity-sensitive durable writes.
Does not block ordinary strategic reasoning or non-durable outputs.

| Drift Score     | Policy                                                      |
|-----------------|-------------------------------------------------------------|
| < 0.20          | Green — allow review to proceed normally                    |
| 0.20 – 0.35    | Yellow — allow only provisional/private proposals,          |
|                 | no durable identity-shaping write                           |
| 0.35 – 0.50    | Red — require explicit block + emit warning                 |
| >= 0.50         | Hard block — no identity-sensitive durable writes           |

Single threshold for v0.1: block at `drift_score >= 0.35`.

---

## 16. Pre-Existing Test Failures (Context)

As of March 24, 2026, the test suite shows 765 passed / 9 failed.
The 9 failures are all pre-existing and unrelated to the Agent Spine:

- 3x `test_golden_emergent` — sim calibration bounds slightly off (private event counts)
- 1x `test_replay_determinism` — CWD / module resolution issue in subprocess
- 5x `test_visualize_attractors` — require live workspace data not present in test env

None of these block Agent Spine work. They should be tracked separately.

---

*Plan authored by Claude (Opus 4.6) on March 24, 2026.*
*Based on Torment_agent.md spec by pzychozen and ChatGPT, TORMENT codebase v2.2.2,*
*and the full research library (development summary, internal memos, SRG spec, hivemind roadmap).*
