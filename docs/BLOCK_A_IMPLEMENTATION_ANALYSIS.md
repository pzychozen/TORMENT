# Block A Implementation Analysis — Pre-Design Phase

**Status:** **RATIFIED 2026-04-19** by user + GPT. All sections accepted; D.1/D.2/D.3 resolved. Block A may now move to its design-doc phase using this analysis as the immediate starting point.
**Date:** 2026-04-19
**Scope:** Code-grounded analysis mapping Block A's ratified preconditions onto the current codebase, before the Block A design doc is written.
**Precedents:**
- `docs/PRE_BLOCK_A_PRECONDITIONS.md` (ratified 2026-04-19)
- `roadmap_tests/TORMENT_Memory_Roadmap_Regrouped.md`
- The ratified checklist from the user + GPT analysis-framing conversation on 2026-04-19.

> This document is an analysis, not a design. It inspects what the code already does, what it partially does, and what is missing — so the Block A design doc can declare its 3–5 acceptance criteria against code reality rather than hope. The rigidity sniff test is applied throughout: **good boundaries require provenance or lifecycle data alongside expression; bad boundaries restrict what the agent can express.** Findings are flagged accordingly.

---

## 1. Findings — memory substrate shape

### 1.1 — Existing memory entity

The current unit of memory lives in `torment_service/memory_graph.py::spawn_memory` (line 533). Payload shape:

```python
payload = {
    "summary": str,              # short text
    "type": str,                 # kernel-assigned mtype (e.g. "episode")
    "memory_class": str,         # "core" | "archive" (open field, not enum)
    "strength": float,
    "confidence": float,
    "canon": bool,
    "created_at": int,           # step
    "created_ts": int,           # unix ts
    "last_reinforced": int,
    "half_life": float,
    "user_id": str,
    # optional extras via extra_payload
    "provenance": ProvenanceV1-dict,
    "scope": "private" | "shared",
    "embedding_ref": shard-ref,
    "pos": [x, y, z],            # kernel physics
    "vel": [...],
}
```

`memory_class` is already a string field and not an enum. Adding a third value ("baton") would be additive, not disruptive.

### 1.2 — Provenance is a real structural support, not a cage

`ProvenanceV1` (`torment_service/provenance_v1.py`) is a validated dataclass with:

- Required fields: `source_type`, `write_path`, `parent_eids`, timestamps.
- Factory methods for every current write path: `for_user_ingest`, `for_cognition_writeback`, `for_tool_result`, `for_collective_echo`.
- Admission fields (`admission_refused`, `admission_reason`, `admission_policy_version`) from the WRITE_MIGRATION work, carrying gate-2 decisions separately from origin class.
- Normalization helper for legacy shapes (bare strings, malformed dicts) with fail-closed semantics.

**Rigidity sniff test: PASSED.** ProvenanceV1 guides by *requiring lineage metadata alongside expression*, not by restricting what the agent can write. It is the template Block A should follow — a new `for_baton_ingest` factory with lifecycle fields (owner, expires_when, resolution_condition) fits this pattern exactly.

### 1.3 — Reinforcement contract (closed 2026-04-16)

`fabric.ingest` contains an automatic reinforce-in-place path (line ~2495): when incoming content is ≥0.92 similar to an existing same-agent memory, reinforce the existing instead of creating new. Plus an explicit `fabric.reinforce(workspace_id, agent_id, retrieved_ids, used_successfully)` method (line 3982) that increments `reinforcement_count` with envelope `{ok, _reinforce_result_code, reinforced_eids, skipped}`. Private-scope only — shared/collective are governed skips with reason codes.

**Block A inherits this pattern:** narrow, explicit, scope-gated writers with named result codes. Baton resolution (soft-consume) should follow suit — a `resolve_baton(eid, outcome)` method with an envelope, not a generic update.

**No re-open risk.** Block A's substrate work does not need to touch reinforce. The pattern is the reference, not a dependency.

### 1.4 — Contradiction surfacing (partial)

`torment_service/conflicts.py::ConflictRegistry` is an append-only per-workspace/domain JSONL store with states `open` | `resolved` | `rejected` | `forked`. `fabric.py::_detect_canon_conflict` (line 130) is the heuristic detector. The registry is wired into the **shared/collective proposal commit path** at fabric.py line 4222, but is **not** wired into regular private `ingest()` (line 2301).

**Finding:** contradiction surfacing exists as infrastructure but is not fired on private ingest. Block A's acceptance criterion *"contradiction surfaced on write"* requires wiring the existing detector + registry into private ingest. This is substrate-shaping, not runtime-shaping. It is **Block A scope**.

**Rigidity sniff test: PASSED.** Surfacing records the conflict but does not block the write or auto-resolve it. Provenance is preserved; the agent's expression is not restricted.

### 1.5 — Writeback gate (ratified 2026-04-17, opt-in)

ProvenanceV1 exposes `WRITE_COGNITION_WRITEBACK` and `WRITE_REFLECTION_WRITEBACK` as validated write paths. The framing doc (`ARCHIVIST_WRITEBACK_GATE_FRAMING_v2.4.x.md`) established these are narrow, opt-in, reversible. Per preconditions §3, Block A must not widen these.

**Block A risk:** baton resolution might produce a durable output (promoted to core, for example). If that happens through a new, silent path, it re-opens the writeback gate.

**Guardrail for design:** baton → durable promotion, if supported at all, MUST flow through either `WRITE_DIRECT_INGEST` (with a clear provenance trail showing the baton resolution) or require a new, separately-ratified `WRITE_BATON_RESOLUTION` path. Block A's design doc must name this explicitly.

### 1.6 — §2A advisory and tool-result lifecycle

Both of these establish a precedent Block A inherits: memory behavior can be conditioned on `provenance.source_type` without adding a new memory_class. Example: `fabric.ingest` caps tool-result half-life at 7 days based on `source_type == "tool_result"` (line 2484). This is lifecycle-tuning by provenance, not by a separate storage lane.

**Block A implication:** baton-specific behavior (aging signal, expiry, exclusion from default retrieval) can similarly be driven by provenance fields and `memory_class`. No parallel storage system needed.

### 1.7 — RESEARCH_ASSISTANT_PACK substrate-side expectation

The pack's declared retrieval shape uses existing `MemoryPlan` lanes: `core`, `archive`, `deep`, `relational`, `collective`, `character_state`, `srg_state`. It privileges `archive` (weight 1.00) and `deep` (weight 0.90); explicitly sets `action_contract=EMPTY_CONTRACT` and notes that a future retrieval tool family is the one field that will change.

**Substrate-side expectation:** Block A must **preserve the lane-based MemoryPlan interface**. Any new "substrate" abstraction that breaks lane semantics would invalidate the pack's `EMPTY_CONTRACT → swap-one-field` promise.

**Good news:** nothing in the roadmap's Block A requires breaking lane semantics. Baton is a new memory_class consumed by a new (or opt-in-via-MemoryPlan) lane, not a replacement for the existing lane system.

### 1.8 — Soft-delete: GAP

Core memory (non-archive) has **no soft-delete mechanism**. `memory_graph.py` uses an append-only JSONL where "the last record per EID is canonical" — so revisions overwrite by appending, and that is the only form of lifecycle change. Archive has `delete_document` (a hard delete).

Baton's soft-consume requires new mechanics:
- A `status` field in the payload that baton-aware queries can filter on.
- Possibly a per-EID lifecycle event ledger (parallel to the conflict event ledger) so consume/resolve is audit-trailed.

**Rigidity sniff test: PASSED (if designed with expression-preserved).** Soft-delete preserves the original content; it only changes how it's retrieved. That's guided, not caged.

### 1.9 — Inheritance summary table

| Source | What it establishes | Block A inherits | Re-open risk |
|---|---|---|---|
| ProvenanceV1 | Required lineage metadata, factory methods per write path | Use wholesale; add `for_baton_ingest` factory | None |
| Reinforce contract | Narrow scope-gated writers with result-code envelopes | Follow the pattern for `resolve_baton` | None |
| ConflictRegistry | Contradiction surfacing infrastructure (shared path only) | Wire into private ingest (Block A scope) | None — additive |
| Writeback gate | Narrow, opt-in self-write paths | **Must not widen.** Baton resolution MUST flow through an explicit write path | **High if baton→durable promotion bypasses provenance** |
| tool_result_ingest | Lifecycle tuning via provenance `source_type` | Follow pattern: baton behavior via provenance + memory_class | None |
| RESEARCH_ASSISTANT_PACK | Retrieval shape via MemoryPlan lanes; `EMPTY_CONTRACT` | **Must preserve lane interface** | **Medium if lane semantics change** |
| §2A advisory | Advisory-lane retrieval works via existing lane dimensions | No direct inheritance; Block A is substrate, §2A is retrieval | None |

---

## 2. Findings — baton fit and lifecycle placement

### 2.1 — Nearest existing constructs

- `task_list` is **not** a first-class code construct. The user/agent-facing TaskList exists conceptually (doctrine mentions it) but there is no `torment_service/tasks.py` or equivalent. Baton does NOT need to disambiguate from it at the substrate level.
- `spirit_return.py` and `spirit_reflection.py` handle symbolic return-of-meaning flows; they write through the same ingest path with distinct provenance and do not own a separate data layer.
- `collective_proposals.py` handles a different kind of unresolved-until-attended state (shared-proposal decisions) but via its own `ProposalRegistry` append-only ledger — **which is the structural analogue for how baton should work** (append-only, soft-resolve via event ledger).

### 2.2 — Fit judgment

**Baton is a memory_class, not a parallel data structure.** Concretely:

- `memory_class="baton"` as a new value alongside "core" and "archive".
- Lifecycle fields in the provenance or in extra_payload: `owner` ∈ {user, next_ai, system}, `expires_when` (condition string), `resolution_condition`, `status` ∈ {active, consumed, expired}.
- Resolution path: `fabric.resolve_baton(eid, outcome)` emits a lifecycle event (append-only, audit-trailed) and updates payload `status="consumed"`. Original content preserved; retrieval filters exclude `status != active` by default.
- Default retrieval lanes (core, archive, deep, relational) MUST NOT return baton entries. A baton-aware query path is the only way to reach them.

### 2.3 — Discriminator between "preserve this fact" and "ensure attention soon"

- Preserve-primary → `memory_class="core"` via regular ingest.
- Attention-primary → `memory_class="baton"` with required `owner` and `expires_when`.

Write-time validation: ingesting `memory_class="baton"` without `owner` or `expires_when` → **rejected**, with a specific error message. This is the category-boundary enforcement.

**Rigidity sniff test: PASSED.** The rejection is based on *missing lifecycle data the agent should provide alongside expression*, not on restricting what the agent can say. If the agent wants to mark a thread as cross-session, it provides the lifecycle metadata; otherwise the write goes into core memory as normal.

### 2.4 — Silent durable promotion prevention

Three guards, all substrate-enforceable:

1. **Retrieval guard:** default MemoryPlan lanes exclude `memory_class == "baton"`. Baton entries never surface via core/archive/deep/relational queries.
2. **Resolution guard:** `resolve_baton(eid, outcome)` marks status, does NOT create a new core entry. Promoting baton content to durable requires an explicit separate ingest call with its own provenance (which carries `parent_eids` pointing back to the baton).
3. **Write-path guard:** ProvenanceV1's `write_path` field distinguishes baton writes from baton-derived-durable writes. Audit trail preserved.

### 2.5 — Aging / graveyard risk

Unresolved batons risk becoming ignored noise. The roadmap's remedy is a session-start aging signal. This depends on the runtime seam (§3 below). If the session-start hook is not in Block A scope, the aging signal ships as a no-op hook that Block A reserves but doesn't activate, with activation deferred to a runtime-doctrine increment.

---

## 3. Findings — runtime seam and session-start surface

### 3.1 — Runtime seam: already exists, no new phase needed

`torment_service/agent_loop.py::AgentRunner.run_turn` Phase 7 calls `self.fabric.ingest(workspace_id, agent_id, text, step)` (line 529). Baton writes use the same ingest with provenance carrying baton-specific fields. **No new runtime phase is needed. No scorecard test is affected by baton writes.**

The `FabricHandle` Protocol (line 191) is the abstraction — tests inject fakes; live wiring is v0.1.0a. Block A's ingest-side changes land in `fabric.py`, the Protocol signature is unchanged, and the runner is insulated.

### 3.2 — Observation.source_type carries the distinction if needed

`agent_loop.Observation` already supports `source_type ∈ {user_text, reflex, tool_result, file_event, scheduled}`. A "baton_resolution" source_type would be additive if Block A needs a baton-driven observation (e.g., a session-start resurfacing turn triggered by an expiring baton).

### 3.3 — Scorecard tests: which are affected vs insulated

| Test | Affected? | Rationale |
|---|---|---|
| `test_agent_loop_smoke.py` | No (smoke runs through ingest; no assertion on memory_class) | Baton writes pass through same path |
| `test_tool_surface_whitelist.py` (inv 1) | No | Tool surface is LLM-visible tools, not substrate |
| `test_tool_narrowing.py` (inv 2) | No | Tool policy, not substrate |
| `test_drift_veto.py` (inv 3) | No | Drift measurement unchanged |
| `test_assimilation_outcomes_not_deliberative.py` (inv 4) | No | Assimilation outcomes are Phase 7 emission; baton doesn't change the set |
| `test_reflex_no_llm.py` (inv 5) | No | Reflex path unchanged |
| `test_governance_narrowing.py` (inv 6) | No | Governance unchanged |
| `test_action_policy_legality.py` (inv 7) | No | Action policy unchanged |
| `test_review_no_loopback.py` (inv 8) | No | Review flow unchanged |
| `test_fallback_chain.py` (inv 9) | No | Fallback chain unchanged |

**All nine scorecard tests should remain green under Block A's substrate changes, assuming baton writes flow through `fabric.ingest` with baton provenance.** This is the preconditions §2 regression rule satisfied structurally.

### 3.4 — Session-start hook: CONFIRMED GAP

There is no session-start hook in the runtime. `AgentRunner.run_turn` and `AgentRunner.enter_reflex` are both per-turn entry points. There is no `begin_session`, no `session_start`, no hook the runtime fires when a session opens.

**Options for Block A:**

- (a) **Define the hook; defer implementation.** Block A adds a `SessionLifecycleHook` Protocol in `agent_loop.py` but does not wire it to a runner method. Aging-signal implementation becomes a post-slice increment (a plausible v0.1.0-sessions or similar). Activation requires a separately ratified runtime-doctrine amendment.
- (b) **Skip aging signal entirely.** Block A ships without baton aging. The graveyard-risk problem remains unsolved; acceptable only if baton usage stays low.
- (c) **Add a minimal session-start hook inside Block A scope.** Block A adds a one-call `AgentRunner.begin_session(workspace_id, agent_id)` that fires baton aging and nothing else. Small runtime-surface change — but a runtime change nonetheless. Requires a scorecard regression check.

**Recommended option:** (a). Naming the gap preserves the design intent without dragging Block A into a runtime-doctrine amendment. The aging signal becomes a **hook with no implementation** — an interface reserved for a follow-on increment. This matches the pattern RESEARCH_ASSISTANT_PACK already established (declare the capability; ship the field swap for the integration later).

### 3.5 — Session-start support: ambiguous → absent

Final verdict: **absent**. The runtime is per-turn. Block A's design doc should propose option (a) explicitly so the aging signal is architecturally visible but implementation is deferred.

---

## 4. Findings — test anchor points

### 4.1 — Mapping preconditions §5 to real locations

**Test 5.1 (negative persistence):** `tests/test_baton_not_in_default_lanes.py` (new).
- Pattern to copy: `tests/test_research_assistant_pack.py` (clean AgentRunner fixtures with fake fabric/LLM client).
- Helper to reuse: the fake fabric's ingest + query interface.
- Asserts: after ingesting `memory_class="baton"`, a `MemoryPlan(retrieve_core=True, retrieve_archive=True, retrieve_deep=True, retrieve_relational=True)` query returns no baton eids.

**Test 5.2 (category boundary):** `tests/test_baton_requires_lifecycle_fields.py` (new).
- Pattern to copy: `tests/test_provenance_v1_admission.py` (tests that invalid provenance is rejected at ingest).
- Helper to reuse: the ProvenanceV1 dataclass test harness.
- Asserts: `fabric.ingest(..., provenance=..., memory_class="baton")` without required lifecycle fields raises a specific error; no EID returned; no node written.

**Test 5.3 (Block-A-meets-runtime integration):** `tests/test_agent_loop_baton_present.py` (new).
- Pattern to copy: `tests/test_agent_loop_smoke.py` (the existing end-to-end smoke).
- Helper to reuse: `test_agent_loop_smoke.py`'s fixture setup.
- Asserts: `AgentRunner.run_turn` completes through all 8 phases with baton entries already present in the fake fabric; the smoke assertions still pass; at least one other scorecard invariant (e.g., `test_drift_veto`'s drift scenario) runs unchanged.

### 4.2 — Reuse inventory

| Existing test file | What Block A can reuse |
|---|---|
| `test_provenance_v1_admission.py` | ProvenanceV1 validation harness; factory test patterns |
| `test_research_assistant_pack.py` | AgentRunner fake fixtures; FakeFabric + FakeLLMClient; integration assertion style |
| `test_agent_loop_smoke.py` | End-to-end smoke harness; 8-phase traversal |
| `test_reinforce_contract_invariant.py` | Private-scope write assertions; envelope shape checks |
| `test_tool_result_ingest.py` | Provenance + memory_class interaction patterns |
| `test_index_provenance.py` | SQLite sidecar provenance shape |

### 4.3 — Writeback/closure fixture-entanglement check (per preconditions §7)

**Finding: no current entanglement.** The writeback tests (`test_writeback_recursion_guard.py`) use distinct fixtures from any closure-related code. There is no closure test suite yet (Block C is deferred). Block A can proceed without entanglement risk, and should not introduce any shared fixture between substrate tests and any future closure infrastructure.

### 4.4 — Cheapest high-confidence proofs

Each of the three required tests can be proven with under ~100 lines of test code using existing fake-fixture patterns. No new harness infrastructure is needed. Running costs: all three tests are unit-scope, expected to complete in under 2 seconds combined.

---

## A. Block A fit decision

**Block A extends the current memory model rather than building a new substrate layer.** The existing substrate already provides:

- Provenance-based guidance via ProvenanceV1 (required metadata, not restricted expression).
- Memory classification via `memory_class` (open string field, room for "baton").
- Scope dimension (`private` / `shared`).
- Explicit narrow writers with envelope result codes (reinforce pattern).
- Contradiction registry (wired to shared path only; private wiring is Block A scope).
- Lane-based retrieval preserving RESEARCH_ASSISTANT_PACK's substrate expectation.

**Block A's additions are additive, not disruptive:**

1. New `memory_class` value: `"baton"`.
2. New ProvenanceV1 factory: `for_baton_ingest(owner, expires_when, resolution_condition, ...)`.
3. Baton-aware lifecycle: `fabric.resolve_baton(eid, outcome)` with append-only event ledger.
4. Default retrieval lane exclusion: baton entries invisible to `retrieve_core/archive/deep/relational`.
5. Private-ingest contradiction wiring (additive to existing shared-path wiring).
6. Session-lifecycle hook **Protocol** (reserved but not wired; activation deferred to a post-slice runtime increment).

**What Block A does NOT need to build:**

- A new "semantic substrate" layer — fabric IS the substrate.
- New retrieval primitives — `MemoryPlan` lanes work and must be preserved.
- New runtime phases — Phase 7 ingest remains the seam.
- A new write authority model — ProvenanceV1 + scope + memory_class suffice.
- Soft-delete for non-baton memories — out of scope; baton's soft-consume is sufficient.

**Baton placement:** new `memory_class` value + lifecycle provenance factory. NOT a parallel data structure.

**Runtime seam:** Phase 7 `fabric.ingest`, unchanged.

**Rigidity sniff test throughout:** PASSED. All proposed Block A additions enforce boundaries by *requiring provenance/lifecycle data alongside expression*, not by restricting what the agent can express.

---

## B. Candidate acceptance criteria (3–5)

1. **Baton memory class is ingestable with required lifecycle provenance.** `fabric.ingest(..., memory_class="baton", provenance=baton_prov)` succeeds when `baton_prov` carries `owner`, `expires_when`, and `resolution_condition`. Missing any required field → ingest rejected with a specific error, no EID returned, no node written. *Test: 5.2 category boundary.*

2. **Baton resolution is explicit soft-consume with audit trail.** `fabric.resolve_baton(eid, outcome)` marks the entry's `status = consumed` and appends a lifecycle event (timestamp, outcome, resolver) to an append-only ledger. The underlying content is preserved; the entry remains inspectable via baton-aware queries. Resolution never creates a new core entry in a single call. *Test: new unit test for resolve_baton semantics.*

3. **Default retrieval lanes exclude baton entries.** A `MemoryPlan` query with any combination of `retrieve_core/archive/deep/relational` returns zero baton EIDs, even when the baton content matches the query embedding. Baton-aware retrieval requires an explicit baton-inclusive query path. *Test: 5.1 negative persistence.*

4. **Private-ingest contradiction surfacing.** When a private ingest's content is high-similarity-plus-contradictory to an existing same-agent entry, the existing `ConflictRegistry` records the conflict. Does not block the write; does not auto-resolve. *Test: new unit test wiring `_detect_canon_conflict` through private ingest path.*

5. **Runtime integration unchanged.** `AgentRunner.run_turn` completes end-to-end with baton entries present in the substrate; all nine scorecard invariant tests from the runtime slice plan continue to pass. Baton-specific behavior is driven entirely by provenance and memory_class fields; no runner branching is added. *Test: 5.3 Block-A-meets-runtime integration.*

---

## C. Candidate test plan

| # | File | Reuses fixtures from | Purpose |
|---|---|---|---|
| T1 | `tests/test_baton_requires_lifecycle_fields.py` | `test_provenance_v1_admission.py` | Category-boundary enforcement (§5.2) |
| T2 | `tests/test_baton_not_in_default_lanes.py` | `test_research_assistant_pack.py` | Negative-persistence assertion (§5.1) |
| T3 | `tests/test_agent_loop_baton_present.py` | `test_agent_loop_smoke.py` | Block-A-meets-runtime integration (§5.3) |
| T4 | `tests/test_resolve_baton_soft_consume.py` | `test_reinforce_contract_invariant.py` | Acceptance criterion 2 (soft-consume + audit trail) |
| T5 | `tests/test_private_ingest_contradiction_surface.py` | `tests/test_collective_reingest.py` (for ConflictRegistry patterns) | Acceptance criterion 4 (contradiction surfacing on private ingest) |

All five tests are unit-scope, ~100 LoC each, expected combined runtime <5s. No new harness infrastructure. No shared fixtures with writeback or closure (preconditions §7 preserved).

---

## D. Genuine design blockers

Only the questions that truly block design from starting, not ones that can be resolved during it.

### D.1 — Baton category placement

Two viable shapes:

- (α) `memory_class="baton"` (payload-visible, query-filter simple) **plus** `provenance.source_type="baton_ingest"` (audit-trail visible).
- (β) Provenance-only (no new `memory_class`): baton is identified entirely by `source_type`, filter happens via provenance inspection.

Recommendation: **(α)**. `memory_class` is already used for gross category gating in retrieval; adding "baton" there matches the existing architecture. Provenance-only would require retrieval lanes to inspect provenance dicts, which is possible but more expensive at query time.

**Needs explicit decision before design starts. Not obviously one-way-door.**

### D.2 — Session-start hook scope

Baton aging signal requires a session-start event. The runtime is per-turn. Three options (§3.4 above):

- (a) Define the hook Protocol in Block A but defer implementation — post-slice increment activates.
- (b) Skip aging entirely.
- (c) Add a minimal session-start hook inside Block A with small runtime-surface change.

Recommendation: **(a)**. Preserves design intent, avoids a runtime-doctrine amendment inside Block A, respects the preconditions §2 regression rule (no scorecard regression without separately-ratified runtime change).

**Needs ratification.** Option (c) is also defensible and would ship a more complete baton lifecycle inside Block A, but at the cost of a runtime-scope amendment Block A would otherwise not need.

### D.3 — Private-ingest contradiction wiring scope

Wiring the existing `ConflictRegistry` + `_detect_canon_conflict` into private ingest is a small change (~20 LoC). It is substrate-shaping (changes what private ingest does), not runtime-shaping (runner unchanged).

Recommendation: **Block A scope.** The change is additive to existing infrastructure and required by acceptance criterion 4.

**Needs confirmation, not deep ratification.** The answer is almost certainly yes; flagging only to make the scope decision explicit.

### D.4 — What is NOT a blocker (surfaced for the record)

These were considered and are NOT blockers:

- **Soft-delete for non-baton memory.** Out of Block A scope. Baton's soft-consume is sufficient; durable-memory revisions continue to use the existing append-then-canonical pattern.
- **RESEARCH_ASSISTANT_PACK compatibility.** The pack uses `MemoryPlan` lanes; Block A preserves lane semantics; no conflict.
- **Writeback gate re-opening.** Addressed by the D.1 recommendation: baton→durable promotion flows through an explicit named write path, not a silent one. Block A design doc must document the specific path; this is design work, not a blocker.
- **Fixture entanglement with closure.** No closure code exists yet (Block C deferred); nothing to entangle with.

---

## E. Boundary checks (required per ratified checklist §5)

Verified absent throughout this analysis:

- ✅ No re-opened closed gates. Writeback stays narrow. Reinforce is untouched. §2A advisory is untouched. tool_result_ingest is untouched. RESEARCH_ASSISTANT_PACK's substrate expectation is preserved.
- ✅ No adjacent architecture absorbed. Block B (reference, environment) and Block C (closure) are referenced only to note their separateness. Block A's own baton is the limit of lifecycle ownership here.
- ✅ No redesign for elegance. The existing memory model is reused as-is; baton is additive.
- ✅ Rigidity sniff test applied per-section. Every proposed Block A structure enforces boundaries by *requiring provenance or lifecycle metadata alongside expression*, not by restricting what the agent can express.

---

## F. Ratification record

**Ratification pass (2026-04-19, user + GPT):**

- [x] Section 1 (memory substrate inheritance) accepted as current-code findings
- [x] Section 2 (baton fit: memory_class + provenance, not parallel structure) accepted
- [x] Section 3 (runtime seam is Phase 7 ingest; session-start hook is a confirmed gap) accepted
- [x] Section 4 (test anchor points + reuse inventory) accepted
- [x] §A fit decision accepted
- [x] §B candidate acceptance criteria (all 5) accepted
- [x] §C candidate test plan accepted
- [x] §D blockers resolved:
    - **D.1 resolved as (α):** `memory_class="baton"` plus provenance source_type / factory. `memory_class` is the existing retrieval/category axis; baton is a category/lifecycle distinction that belongs visible there. Provenance-only would push too much category logic into provenance inspection.
    - **D.2 resolved as (a):** define the session-start hook Protocol in Block A; defer implementation to a post-slice runtime increment. Preserves intent without forcing a runtime-doctrine amendment inside Block A.
    - **D.3 confirmed as Block A scope:** private-ingest contradiction wiring is substrate-shaping (additive to existing ConflictRegistry), directly required by acceptance criterion 4.

**Status:** **RATIFIED 2026-04-19 by user + GPT.** Block A design-doc phase is unblocked. Block A design is bound by the decisions frozen in this analysis.

### Handoff notes for the Block A design doc

These are first-class design-doc requirements carried forward from the ratification discussion:

1. **`memory_class="baton"` is a retrieval/lifecycle aid, not a proxy for truth rank or ontology hierarchy.** Baton means "this needs attention across the gap." It does **not** mean "a lesser class of thought," "disallowed from meaning-making," or "a temporary bucket the system treats as inferior." The baton category must not, now or later, drift into an ontology rank. If the design ever needs to prevent a baton entry from carrying meaningful content, that is the signal that baton is being misused as a cage — stop and reconsider.

2. **First move of the Block A design doc:** state the 3–5 acceptance criteria (§B of this analysis is the starting point; the design doc may refine).

3. **Explicitly adopt the D.1, D.2, D.3 decisions** — cite this analysis's ratification record rather than re-litigating them.

4. **Keep lane compatibility intact.** `MemoryPlan` lane semantics remain the substrate's retrieval interface. RESEARCH_ASSISTANT_PACK's `EMPTY_CONTRACT → swap-one-field` promise depends on this.

5. **Avoid inventing a new substrate layer** unless code reality as encountered during design proves this analysis wrong. If that happens, surface the contradiction before proceeding — don't silently widen scope.

---

## Appendix — file inventory touched during analysis

Read in full:
- `docs/PRE_BLOCK_A_PRECONDITIONS.md` (ratified preconditions)
- `torment_service/provenance_v1.py` (371 LoC)
- `torment_service/conflicts.py` (129 LoC)
- `torment_service/behavior_packs.py` (383 LoC — both packs)
- `torment_service/agent_loop.py` (767 LoC)
- `torment_service/memory_kernel.py` (400 LoC)
- `torment_service/promotion.py` (370 LoC)
- `tests/test_research_assistant_pack.py` (partial)

Read strategically (targeted sections):
- `torment_service/fabric.py` (5045 LoC; read ingest path ~2301-2520, reinforce ~3982-4048, conflict-detection ~130-164, conflict commit ~4200-4232)
- `torment_service/memory_graph.py` (spawn_memory + flush_node ~533-687)

Inventory checked (listings, not full reads):
- `torment_service/` directory (full listing)
- `torment_service/behavior_packs/` (confirmed does NOT exist; `behavior_packs.py` is the module)
- `tests/` directory (filtered listings by topic)

No code modified. Analysis only.
