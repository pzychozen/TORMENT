# Block A Design — Semantic Substrate Core (Substrate + Baton)

**Status:** **RATIFIED 2026-04-19** by user + GPT. All §12 checklist items accepted. Block A implementation is unblocked — first move is test scaffolding (T1–T5), then behavior wiring, with the nine-invariant scorecard green throughout.
**Date:** 2026-04-19
**Scope:** Design for Block A of the regrouped memory roadmap: the agent-owned semantic memory substrate and baton as a transient continuity lifecycle class within it.

**Precedents (cited, not re-derived):**
- `docs/PRE_BLOCK_A_PRECONDITIONS.md` — ratified 2026-04-19. Gate on this work.
- `docs/BLOCK_A_IMPLEMENTATION_ANALYSIS.md` — ratified 2026-04-19. Code-grounded analysis; D.1/D.2/D.3 resolved.
- `roadmap_tests/TORMENT_Memory_Roadmap_Regrouped.md` — architecture freeze.
- `docs/TORMENT_AGENT_DOCTRINE_v0.1.md`, `docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` — runtime doctrine and scorecard.

> This document is the design for Block A. It commits to concrete field names, method signatures, and file-level changes. It does NOT re-derive the analysis: every architectural decision traces back to the ratified analysis or preconditions. If code reality during implementation contradicts a decision here, **surface the contradiction before proceeding** — do not silently widen scope.

---

## 1. Objective

Define the minimum additive extension of the existing memory model that gives the agent:

- a first-class way to mark cross-session attention-bounded intent (baton)
- lifecycle semantics that preserve provenance and prevent silent promotion to durable memory
- contradiction surfacing on private ingest (using infrastructure that already exists)
- a reserved hook interface for the session-lifecycle work that will activate baton aging in a later increment

Block A proves the substrate foundation under real code, so that Blocks B (reference + environment memory) and C (closure) later build on a substrate that is guiding rather than caging, with provenance/lifecycle metadata doing the boundary work.

---

## 2. Scope / Out of scope

### In scope

- **Substrate extension.** Add `"baton"` as an accepted value for `memory_class`. No new storage layer, no parallel data structure.
- **Baton lifecycle.** Required provenance fields, soft-consume resolution, append-only audit ledger, status semantics.
- **Retrieval behavior.** Default `MemoryPlan` lane filters exclude baton entries. Explicit baton-aware retrieval API.
- **Contradiction surfacing on private ingest.** Wire existing `ConflictRegistry` + `_detect_canon_conflict` into `fabric.ingest`'s private path.
- **SessionLifecycleHook Protocol** (declaration only, no runtime wiring).
- **Test harness** for the five acceptance criteria.

### Out of scope (explicit)

The following are not Block A's concern and must not be absorbed into this design:

- **Block B work** — loadable full-reference memory, environment memory. Referenced only to confirm no conflict.
- **Block C work** — closure / end-of-arc synthesis. No closure code touched.
- **EXTENSION_CONTRACT.md body.** The preconditions doc requires `EXTENSION_CONTRACT.md` at Block A close, but its full content is a separate deliverable drafted alongside (or after) this design doc. It does not live inside this design.
- **Broad MCP surface changes.** No new MCP tools. Existing surface already covers ingest.
- **Session-lifecycle runtime wiring.** Hook Protocol only. Activation is a post-slice runtime increment, separately ratified.
- **Writeback gate reopening.** Baton resolution must NOT widen writeback.
- **Soft-delete for non-baton memory.** Durable-memory revision continues to use the existing append-then-canonical pattern.
- **RESEARCH_ASSISTANT_PACK's action_contract.** Unchanged by this design; retrieval-family work remains a separate later increment.

### Carry-forward invariant — **baton is lifecycle, not ontology rank**

`memory_class="baton"` means "this needs attention across the session gap." It does NOT mean:

- a lesser class of thought
- disallowed from meaning-making
- a temporary bucket the system treats as inferior
- a proxy for truth rank, confidence rank, or ontology hierarchy

Baton entries **filter out of default retrieval lanes for lifecycle reasons** (they're attention-bounded, not durable). They are **not down-ranked in scoring** for quality reasons. If any code path in Block A ends up scoring baton entries as "worth less" rather than filtering them by lifecycle state, that is the signal baton is drifting into a cage — stop and reconsider.

---

## 3. Adopted ratified decisions

This section cites; it does not re-litigate. All three decisions below are frozen.

**D.1 — Baton category placement.** `memory_class="baton"` as a new value on the existing open string field, plus a new `ProvenanceV1` `source_type="baton_intent"` identifying the origin and a dedicated factory method. Lifecycle fields live in the memory entity's `extra_payload` under a namespaced `baton_lifecycle` sub-object. (Ratified `BLOCK_A_IMPLEMENTATION_ANALYSIS.md` §F, 2026-04-19.)

**D.2 — Session-start hook.** Block A defines a `SessionLifecycleHook` Protocol in `agent_loop.py`. Implementation is deferred to a post-slice runtime increment; Block A does not wire the hook into `AgentRunner`. (Ratified `BLOCK_A_IMPLEMENTATION_ANALYSIS.md` §F, 2026-04-19.)

**D.3 — Private-ingest contradiction wiring.** Wiring the existing `ConflictRegistry` + `_detect_canon_conflict` into `fabric.ingest`'s private path is Block A scope (substrate-shaping, additive, ~20 LoC). (Ratified `BLOCK_A_IMPLEMENTATION_ANALYSIS.md` §F, 2026-04-19.)

---

## 4. Acceptance criteria

Five criteria, carried forward verbatim from `BLOCK_A_IMPLEMENTATION_ANALYSIS.md` §B (accepted 2026-04-19). Each criterion names the test that proves it.

**AC-1.** Baton memory class is ingestable with required lifecycle metadata. `fabric.ingest(..., memory_class="baton", provenance=ProvenanceV1.for_baton_ingest(...).to_dict(), extra_payload={"baton_lifecycle": {...}})` succeeds when `extra_payload["baton_lifecycle"]` carries `owner`, `expires_when`, and `resolution_condition`. Missing any required field → ingest rejected with a specific error, no EID returned, no node written. Origin goes in provenance (`source_type="baton_intent"`); lifecycle state lives in the `baton_lifecycle` payload and mutates over the baton's life (§5.1–5.2). *Test: T1 `test_baton_requires_lifecycle_fields.py`.*

**AC-2.** Baton resolution is explicit soft-consume with audit trail. `fabric.resolve_baton(workspace_id, agent_id, eid, outcome)` marks the entry's `baton_lifecycle.status = "consumed"` and appends a lifecycle event to an append-only ledger. The underlying content is preserved; the entry remains inspectable via baton-aware queries. Resolution never creates a new core entry in a single call. *Test: T4 `test_resolve_baton_soft_consume.py`.*

**AC-3.** Default retrieval lanes exclude baton entries. A `MemoryPlan` query with any combination of `retrieve_core/archive/deep/relational` returns zero baton EIDs, even when content embeddings match. Baton-aware retrieval requires an explicit baton-inclusive query path. *Test: T2 `test_baton_not_in_default_lanes.py`.*

**AC-4.** Private-ingest contradiction surfacing. When a private ingest's content is high-similarity-plus-contradictory to an existing same-agent entry, the existing `ConflictRegistry` records the conflict. Does not block the write; does not auto-resolve. *Test: T5 `test_private_ingest_contradiction_surface.py`.*

**AC-5.** Runtime integration unchanged. `AgentRunner.run_turn` completes end-to-end with baton entries present in the substrate; all nine scorecard invariant tests from the runtime slice plan continue to pass. Baton-specific behavior is driven entirely by provenance and memory_class fields; no runner branching is added. *Test: T3 `test_agent_loop_baton_present.py` + the existing nine scorecard tests must remain green.*

---

## 5. Data model changes

### 5.1 — Provenance extension

**File:** `torment_service/provenance_v1.py`.

Add a new source_type constant:

```python
SOURCE_BATON_INTENT = "baton_intent"
```

Add to `VALID_SOURCE_TYPES`:

```python
VALID_SOURCE_TYPES = frozenset({
    SOURCE_USER_INPUT,
    SOURCE_ROLE_OUTPUT,
    SOURCE_DERIVED,
    SOURCE_MEMORY,
    SOURCE_TOOL_RESULT,
    SOURCE_COLLECTIVE_ECHO,
    SOURCE_GATE1_UNRECOVERABLE,
    SOURCE_BATON_INTENT,      # v2.4.x Block A
})
```

No new `write_path` value. Baton ingest uses `WRITE_DIRECT_INGEST` — the write is still a direct ingest from the agent/user; baton is *what it is*, not *how it got written*. Baton resolution also does not create a new write path; see §6.3 below.

Add a factory method on `ProvenanceV1`:

```python
@classmethod
def for_baton_ingest(
    cls,
    step: Optional[int] = None,
    session_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> "ProvenanceV1":
    """Provenance for a baton — cross-session attention-bounded intent.

    Baton lifecycle fields (owner, expires_when, resolution_condition,
    status) live in the memory entity's extra_payload under the
    'baton_lifecycle' key, not on ProvenanceV1. Provenance records
    origin/lineage only.
    """
    return cls(
        source_type=SOURCE_BATON_INTENT,
        source_role=None,
        write_path=WRITE_DIRECT_INGEST,
        parent_eids=[],
        created_at_step=step,
        session_id=session_id,
        notes=notes,
    )
```

**Rationale for keeping lifecycle fields off ProvenanceV1:** provenance is origin/lineage truth (what this memory is and where it came from). Baton lifecycle fields (owner, expires_when, resolution_condition, status) are state that changes over the baton's lifetime. Mixing them into provenance would violate the provenance-vs-state separation and pollute the ProvenanceV1 dataclass with fields meaningful only to one source_type.

### 5.2 — Baton lifecycle payload

**Location:** `extra_payload` on the memory entity, under a namespaced key.

Shape:

```python
baton_lifecycle = {
    "owner": "user" | "next_ai" | "system",        # REQUIRED at write
    "expires_when": str,                            # REQUIRED at write — human-readable condition
    "resolution_condition": str,                    # REQUIRED at write — what "done" looks like
    "status": "active" | "consumed" | "expired",   # defaults to "active" at write
    # Populated only on resolve_baton:
    "consumed_at": Optional[int],      # unix ts
    "consumed_by": Optional[str],       # who resolved (agent_id or "user" or "system")
    "consumed_outcome": Optional[str],  # free text: discarded | promoted | converted | acknowledged
}
```

Required field validation happens at ingest (see §6.1). Status defaults to `"active"`.

**Owner vocabulary.** Block A ships with exactly three valid values: `user`, `next_ai`, `system`. These match the regrouped roadmap's §item-2 owner types. Adding a new value in a later increment requires ratification (owner semantics affect who can resolve).

### 5.3 — Memory entity write — `memory_class` accepts `"baton"`

**File:** `torment_service/memory_graph.py`.

No code change is required for `spawn_memory` itself — `memory_class` is already an open string field. The change lives in `fabric.ingest` (§6.1) where the ingest-time validation adds the baton-specific required-field check.

**Storage identity preserved.** Baton entries go through the same `spawn_memory` → `flush_node` → `nodes.jsonl` + SQLite sidecar path as any other memory. The only payload-level distinctions are `memory_class="baton"` and the presence of `baton_lifecycle`. This keeps the substrate implementation uniform.

---

## 6. Baton lifecycle

### 6.1 — Write: `fabric.ingest` changes

**File:** `torment_service/fabric.py`, method `ingest` (line ~2301).

Add baton-specific validation early in ingest (after provenance is normalized, before `spawn_memory` is called):

```python
# Baton validation — if this ingest is tagged memory_class="baton",
# the lifecycle metadata is required. Missing fields → reject.
if memory_class == "baton":
    baton_lifecycle = (extra_payload or {}).get("baton_lifecycle")
    if not isinstance(baton_lifecycle, dict):
        raise ValueError(
            "memory_class='baton' requires extra_payload['baton_lifecycle'] dict"
        )
    for required in ("owner", "expires_when", "resolution_condition"):
        if not baton_lifecycle.get(required):
            raise ValueError(
                f"baton_lifecycle missing required field '{required}'"
            )
    valid_owners = {"user", "next_ai", "system"}
    if baton_lifecycle["owner"] not in valid_owners:
        raise ValueError(
            f"baton_lifecycle.owner must be one of {valid_owners}, "
            f"got {baton_lifecycle['owner']!r}"
        )
    # Default status to "active" if caller didn't set one
    baton_lifecycle.setdefault("status", "active")
```

**Method signature addition:** `fabric.ingest` already takes `memory_class` via the `extra_payload` path today through `graph.spawn_memory`. Surface `memory_class` as a direct parameter if it isn't already (confirm in implementation):

```python
def ingest(
    self,
    workspace_id: str,
    agent_id: str,
    text: str,
    step: int = 0,
    domain_id: Optional[str] = None,
    tri_mod: Optional[Dict[str, float]] = None,
    supplied_summary: Optional[str] = None,
    supplied_embedding: Optional[List[float]] = None,
    scope: str = "private",
    provenance: Optional[Dict[str, Any]] = None,
    memory_class: str = "core",        # NEW or surfaced
    extra_payload: Optional[Dict[str, Any]] = None,  # NEW or surfaced
    *,
    skip_packet_emission: bool = False,
) -> Dict[str, Any]:
    ...
```

**Reinforce-in-place interaction.** The existing duplicate-suppression logic (line ~2495) searches for similar existing entries and reinforces rather than creating new. Baton writes must not accidentally reinforce a non-baton entry, and non-baton writes must not accidentally reinforce a baton. Add a memory_class equality check to the similarity-match branch:

```python
# Existing code:
for _rh in _recent_hits:
    if float(_rh.get("raw_score", _rh.get("score", 0))) >= _reinforce_sim_threshold:
        _existing_eid = int(_rh["eid"])
        _existing_ent = graph.entities.get(_existing_eid)
        if _existing_ent is not None:
            # NEW: reinforce-in-place requires same memory_class
            _existing_class = (_existing_ent.payload or {}).get("memory_class", "core")
            if _existing_class != memory_class:
                continue  # skip — different class
            # ...existing reinforce logic...
```

### 6.2 — Query: `fabric.list_active_batons`

**File:** `torment_service/fabric.py`, new method.

```python
def list_active_batons(
    self,
    workspace_id: str,
    agent_id: str,
    owner: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """List active baton entries for an agent.

    Returns an envelope:
        {
            "ok": True,
            "result_code": "listed" | "no_active",
            "batons": [{"eid": int, "summary": str, "baton_lifecycle": {...},
                        "created_ts": int, "provenance": {...}}, ...],
        }

    Filter semantics:
        - agent-scoped (private only — baton is never shared)
        - active only (status == "active")
        - optional owner filter
        - sorted by created_ts ascending (oldest first — aging bias)
        - limit capped at 200 server-side
    """
```

**Why a new method, not a new `MemoryPlan` lane.** A `MemoryPlan` lane would be visible in every pack declaration. Baton is not retrieval shape — it's lifecycle state queried when the agent or a session-start hook explicitly asks about it. A method is the honest interface. If a future pack needs baton-aware retrieval, the pack's code can call `list_active_batons` directly.

### 6.3 — Resolve: `fabric.resolve_baton`

**File:** `torment_service/fabric.py`, new method.

```python
def resolve_baton(
    self,
    workspace_id: str,
    agent_id: str,
    eid: int,
    outcome: str,
    resolver: Optional[str] = None,
) -> Dict[str, Any]:
    """Mark a baton as consumed. Does NOT delete or auto-promote.

    Soft-consume semantics:
        - payload["baton_lifecycle"]["status"] = "consumed"
        - payload["baton_lifecycle"]["consumed_at"] = unix_ts
        - payload["baton_lifecycle"]["consumed_by"] = resolver or agent_id
        - payload["baton_lifecycle"]["consumed_outcome"] = outcome
        - A lifecycle event is appended to the audit ledger
          (see §6.4) via BatonLedger.add_event()

    The memory entry is NOT removed. Original content + provenance
    preserved. Resolution is visible via both the payload and the
    ledger. Resolution NEVER creates a new core entry — promoting
    baton content to durable is a separate, explicit ingest with
    parent_eids pointing back to the baton.

    Returns envelope:
        {
            "ok": True,
            "result_code": "resolved" | "already_consumed" | "not_found" | "not_a_baton",
            "eid": int,
            "outcome": str,
        }

    Error cases:
        - eid not in private graph → result_code="not_found", ok=True
        - memory_class != "baton" → result_code="not_a_baton", ok=True
        - status already "consumed" → result_code="already_consumed",
          ok=True (idempotent; no state change)
    """
```

**Idempotency.** Calling `resolve_baton` on an already-consumed baton is a no-op (returns "already_consumed", no state change, no duplicate ledger entry). Matches the reinforce contract's envelope pattern.

**Scope gating.** `resolve_baton` touches the private graph only — baton is private-scope by design (§5.2 owner vocabulary). If a future increment introduces shared batons, scope gating becomes a separate ratification.

### 6.4 — Audit ledger — `BatonLedger`

**File:** `torment_service/baton_ledger.py` (new, ~150 LoC).

Modeled on `ConflictRegistry` (`torment_service/conflicts.py`): per-workspace/per-agent append-only JSONL.

```python
@dataclass
class BatonEvent:
    event_id: str
    workspace_id: str
    agent_id: str
    eid: int
    kind: str           # "created" | "consumed" | "expired_notice"
    outcome: Optional[str]
    resolver: Optional[str]
    owner: str
    ts: int

class BatonLedger:
    """Append-only per-agent baton lifecycle event store."""
    def __init__(self, data_dir: str, workspace_id: str, agent_id: str) -> None: ...
    def add_event(self, event: BatonEvent) -> None: ...
    def list_events(self, eid: Optional[int] = None, limit: int = 500) -> List[BatonEvent]: ...
```

Path layout: `<data_dir>/workspaces/<ws>/agents/<agent>/baton_events.jsonl`.

The ledger's job is audit, not state. **The payload is the current-state source of truth; the ledger is the historical audit trail.** They must not be treated as competing state stores — if they ever appear to disagree in a future context, the payload wins and the ledger stays re-derivable from its append-only event history. The ledger is inspectable by future tooling (session-start hook, debugging) without needing to read all memory entries.

**Scope check.** The ledger is NEW infrastructure, but it is narrow and doctrine-aligned: append-only, provenance-preserved, no LLM involvement, no automation beyond what the caller requests. It matches `ConflictRegistry`'s pattern exactly.

---

## 7. Retrieval behavior

### 7.1 — Default lane exclusion

**Files:** `torment_service/retrieval_assembler.py`, `torment_service/memory_graph.py` (if lane filtering is graph-side).

Every path that resolves `MemoryPlan` lanes (`retrieve_core`, `retrieve_archive`, `retrieve_deep`, `retrieve_relational`, `retrieve_collective`, `retrieve_character_state`, `retrieve_srg_state`) must filter out entries where `payload.memory_class == "baton"`.

Concrete change: a shared helper in `retrieval_assembler.py`:

```python
def _excludes_baton(hit: Dict[str, Any]) -> bool:
    """True if this hit should be excluded because it's a baton entry.

    Default MemoryPlan lanes never return baton entries. Baton retrieval
    goes through fabric.list_active_batons. See BLOCK_A_DESIGN.md §7.
    """
    payload = hit.get("payload") or {}
    return payload.get("memory_class") == "baton"
```

Applied at every lane assembly point. Implementation-level detail: the cheapest place to filter is at the `search_by_embedding` result post-processing in each lane's branch of the assembler, not inside `search_by_embedding` itself (so non-lane queries remain unaffected).

### 7.2 — Explicit baton-aware retrieval

`fabric.list_active_batons` (§6.2) is the only way to retrieve baton entries through normal API. Any caller that wants baton content must use this method.

Future packs may use this; no pack in v0.1 does, and no pack-visible `MemoryPlan` field is added.

### 7.3 — Rigidity sniff test for retrieval

Filtering is **lifecycle-based exclusion** (`memory_class == "baton"`), not **quality-based down-ranking** (e.g., multiplying baton entries' scores by 0.5). This matters: if the score were merely de-weighted, baton content could still surface in core retrievals, carrying the implicit message "baton thoughts are worth less." The hard exclusion says "baton content is lifecycle-different, surface it via the baton-aware path." That is the guided-not-rigid form.

---

## 8. Private-ingest contradiction surfacing

**File:** `torment_service/fabric.py`, method `ingest` (line ~2301).

After the memory entry is written (after `flush_node`), perform a single heuristic contradiction check against existing same-agent entries. Model on the shared-commit path at line ~4222.

```python
# After spawn + flush:
# Private-scope contradiction surfacing (Block A).
# Shared-scope commits already do this at the proposal-commit path;
# private ingest now gets the same treatment.
if scope == "private" and eid is not None:
    try:
        # Re-use the existing _recent_hits already computed above
        # during duplicate suppression, rather than a second search.
        for _rh in _recent_hits:
            _old_eid = int(_rh.get("eid", 0))
            if _old_eid <= 0 or _old_eid == eid:
                continue
            sim = float(_rh.get("raw_score", _rh.get("score", 0)))
            _old_sum = str(_rh.get("summary", ""))
            is_conflict, cscore, reason = _detect_canon_conflict(
                summary, _old_sum, sim
            )
            if is_conflict:
                ws.conflicts[chosen_domain].add(
                    eid_a=int(_old_eid),
                    eid_b=int(eid),
                    sim=float(sim),
                    conflict_score=float(cscore),
                    reason=str(reason or "heuristic"),
                )
                break  # one conflict per ingest is enough
    except Exception as e:
        log.debug("private contradiction surface skipped: %s", e)
```

**Behavior guarantees:**

- Does not block the write. The ingest has already succeeded.
- Does not auto-resolve. `ConflictRegistry.add` creates a `status="open"` entry.
- Does not fire for shared writes (shared already has contradiction surfacing via the proposal-commit path).
- Does not fire for baton writes (baton is lifecycle, not claim — contradicting "remember to check X" against "X is done" is not a claim contradiction).

Explicit guard for the baton skip:

```python
if scope == "private" and memory_class == "core" and eid is not None:
    # ...contradiction check...
```

**Scope framing (v0.1).** Contradiction surfacing fires for private `memory_class=="core"` writes only. Baton is explicitly excluded because it is lifecycle state, not claim state — a baton saying "remember to check X" does not contradict an existing memory saying "X is true," and treating it that way would be a category mistake. `"core"` is **not doctrinally the eternal contradiction-bearing class**; it is the only class in v0.1 that carries claim-like semantics. Future memory classes introduced by Block B or later (reference, environment, closure objects) must make an **explicit design decision** here about whether they fire contradiction surfacing, rather than inheriting silence or inheriting fire by accident.

---

## 9. SessionLifecycleHook protocol

**File:** `torment_service/agent_loop.py`, new Protocol.

```python
from typing import Protocol


class SessionLifecycleHook(Protocol):
    """Hook interface for session-boundary events.

    Block A declares this Protocol but does NOT wire it into
    AgentRunner. Implementation is deferred to a post-slice runtime
    increment (provisionally v0.1.0-sessions). Activation will
    require a separately-ratified runtime-doctrine amendment, since
    adding a session-lifecycle call path is a runtime-surface change.

    The Protocol lives here so that Block A's baton lifecycle design
    is architecturally visible — the aging signal has a named home —
    without requiring Block A to ship the runtime wiring.

    See BLOCK_A_DESIGN.md §D.2 (adopted 2026-04-19) and
    BLOCK_A_IMPLEMENTATION_ANALYSIS.md §3.4 for the deferral rationale.
    """

    def on_session_start(
        self,
        workspace_id: str,
        agent_id: str,
        session_id: str,
    ) -> None:
        """Called once at the start of a session.

        Expected (post-activation) use: call fabric.list_active_batons,
        emit an aging signal for any baton older than a declared
        threshold, record session-start timestamp for later aging
        calculations. None of this is implemented in Block A.
        """
        ...

    def on_session_end(
        self,
        workspace_id: str,
        agent_id: str,
        session_id: str,
    ) -> None:
        """Called once at session close. Reserved for symmetry and
        for future use by baton-expiry heuristics that depend on
        session boundaries. Not implemented in Block A."""
        ...
```

**No wiring.** `AgentRunner.__init__` does not accept a hook. `run_turn` does not call the hook. The class is declared so the shape is discoverable and stable, nothing more.

**Test coverage for Block A:** a presence test that the Protocol class exists and has the expected methods, nothing more. No behavior test — there is no behavior.

---

## 10. Test plan

Five new tests. All unit-scope, expected combined runtime <5 s. No shared fixtures with writeback or any closure infrastructure (preconditions §7 preserved).

| # | File | Covers | Reuses fixtures from |
|---|---|---|---|
| T1 | `tests/test_baton_requires_lifecycle_fields.py` | AC-1 | `test_provenance_v1_admission.py` (validation rejection patterns) |
| T2 | `tests/test_baton_not_in_default_lanes.py` | AC-3 | `test_research_assistant_pack.py` (fake AgentRunner fixtures) |
| T3 | `tests/test_agent_loop_baton_present.py` | AC-5 | `test_agent_loop_smoke.py` (end-to-end smoke pattern) |
| T4 | `tests/test_resolve_baton_soft_consume.py` | AC-2 | `test_reinforce_contract_invariant.py` (envelope + private-scope patterns) |
| T5 | `tests/test_private_ingest_contradiction_surface.py` | AC-4 | `test_collective_reingest.py` (ConflictRegistry fixture patterns) |

Plus a minimal Protocol-presence check for `SessionLifecycleHook` in a pre-existing or new small test file.

**Scorecard regression requirement.** All nine existing scorecard invariant tests (from `TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` §7) must remain green when Block A lands. This is asserted by the CI run, not a new test. The preconditions §2 regression gate applies.

**Test-file-location discipline.** All five new tests live in `tests/`, naming follows the existing pattern. No tests in `tests/integration/` or separate directories — the scope is unit-level. No fixtures shared with writeback or closure (there is no closure code anyway).

---

## 11. Open questions

Only questions that truly remain open after ratification. Most of what was open at the analysis stage (D.1, D.2, D.3) is now closed.

### Q1 — Should `list_active_batons` paginate or cap?

Current design caps at 200 server-side and defaults to limit=50. For v0.1, per-agent baton counts are expected to be small (order 10-50). If usage grows, pagination becomes a concern. Not blocking for Block A — the cap is the safety valve.

### Q2 — Owner vocabulary extension

Owner values are `{user, next_ai, system}`. Is there a realistic v0.1 use case for any other owner class (e.g., `collective`, `shared_agent`)? Initial judgment: no — baton is private-scope by design. Adding an owner value in a later increment would be ratifiable but carries scope-widening risk (shared batons cross-agent).

### Q3 — Reinforce-in-place cross-class behavior

Current design says non-baton writes do not reinforce baton entries and vice versa (§6.1). Is this strict enough? Edge case: user ingests "remember to ask about the plan" as a baton, then a week later ingests "let's confirm the plan" as regular content. Similarity is high, memory_class differs, so no reinforcement. The baton stays active until resolved. Intended behavior, but flagging so reviewers can challenge.

### Q4 — `resolve_baton` failure modes

Envelope returns `result_code="not_found" | "not_a_baton" | "already_consumed"` with `ok=True` in all three cases. Is there a case where `ok=False` is the right response? Current thinking: no. These are legitimate "nothing to do" states, not errors. Spine envelope patterns from the reinforce contract suggest this is the right shape.

**None of Q1-Q4 blocks design ratification.** They can be refined during implementation review.

---

## 12. Ratification record

**Drafted:** 2026-04-19 by Claude, following ratified direction from user + GPT conversation 2026-04-19.

**Ratification pass (2026-04-19, user + GPT):**

- [x] §1 Objective accepted
- [x] §2 Scope/out-of-scope + carry-forward invariant accepted
- [x] §3 Adopted decisions (D.1, D.2, D.3 citations) accepted
- [x] §4 Acceptance criteria (AC-1 through AC-5) accepted — AC-1 corrected during review to put required lifecycle metadata on `extra_payload["baton_lifecycle"]` rather than on `ProvenanceV1`, matching the §5.1 separation of concerns.
- [x] §5 Data model changes (provenance extension, baton_lifecycle payload, memory_class value) accepted
- [x] §6 Baton lifecycle (ingest validation, list_active_batons, resolve_baton, BatonLedger) accepted — §6.4 tightened during review to name the payload as current-state source of truth and the ledger as historical audit trail, not competing state stores.
- [x] §7 Retrieval behavior (default lane exclusion, explicit baton-aware path, no down-ranking) accepted
- [x] §8 Private-ingest contradiction surfacing wiring accepted — §8 framing narrowed during review so `"core"` is not described as the eternal contradiction-bearing class; future memory classes must make an explicit design decision.
- [x] §9 SessionLifecycleHook Protocol (declaration only, no wiring) accepted
- [x] §10 Test plan (5 new tests + scorecard regression requirement) accepted
- [x] §11 Open questions — no blockers surfaced, accepted for refinement during implementation

**Status:** **RATIFIED 2026-04-19 by user + GPT.** Block A implementation is unblocked. Any change to the design after this point requires a separately ratified amendment.

### Handoff notes for implementation

1. **First move is test scaffolding.** Land T1–T5 stubs (failing tests per AC-1 through AC-5, plus the `SessionLifecycleHook` Protocol-presence check) before wiring behavior. Behavior proofs exist before behavior is written.
2. **Nine-invariant scorecard stays green throughout.** No PR merges if any scorecard test regresses without a separately ratified runtime-doctrine amendment (preconditions §2).
3. **Watch for drift toward subtle ranking behavior during code review.** The "baton is lifecycle, not ontology rank" invariant (§2) must be preserved *literally* in implementation, not just philosophically. Filter baton out of default lanes for lifecycle reasons; do not introduce score-weight penalties that would amount to "baton is worth less." This is the specific failure mode future review must guard against.
4. **AC-1, AC-2, AC-3 are load-bearing together.** AC-1 proves baton writes validate lifecycle metadata. AC-3 proves baton is invisible to default retrieval. AC-2 proves resolution preserves content. If any one of these softens during implementation, surface it before proceeding — softening any of them re-opens the silent-promotion failure mode the whole design is built to prevent.

---

## Appendix — files expected to change or be created

### New files

- `torment_service/baton_ledger.py` — append-only baton lifecycle event store.
- `tests/test_baton_requires_lifecycle_fields.py` — AC-1.
- `tests/test_baton_not_in_default_lanes.py` — AC-3.
- `tests/test_agent_loop_baton_present.py` — AC-5.
- `tests/test_resolve_baton_soft_consume.py` — AC-2.
- `tests/test_private_ingest_contradiction_surface.py` — AC-4.

### Modified files

- `torment_service/provenance_v1.py` — add `SOURCE_BATON_INTENT`, add to `VALID_SOURCE_TYPES`, add `for_baton_ingest` factory.
- `torment_service/fabric.py` — `ingest` validation for baton writes + memory_class-aware reinforce-in-place + private-ingest contradiction surfacing; new `list_active_batons` and `resolve_baton` methods.
- `torment_service/retrieval_assembler.py` — add `_excludes_baton` helper; apply at every lane assembly branch.
- `torment_service/agent_loop.py` — add `SessionLifecycleHook` Protocol declaration. No wiring to `AgentRunner`.

### Not changed (explicitly preserved)

- `torment_service/memory_graph.py` — `spawn_memory`/`flush_node` signature unchanged. `memory_class` is already open.
- `torment_service/memory_kernel.py` — kernel math untouched.
- `torment_service/conflicts.py` — ConflictRegistry interface unchanged; wiring to private ingest uses existing `.add()` method.
- `torment_service/thinking_controller.py` — controller unchanged; deliberation flow unaffected.
- `torment_service/behavior_packs.py` — packs unchanged. RESEARCH_ASSISTANT_PACK's `EMPTY_CONTRACT` still holds.
- `torment_service/mcp_server.py` — MCP surface unchanged (preconditions R5 preserved).
- All nine scorecard invariant test files — unchanged; must remain green.
