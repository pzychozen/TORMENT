# Block C Design — Arc Closure / End-of-Arc Synthesis

**Status:** **RATIFIED 2026-04-21** by user + GPT. All §12 checklist items accepted as-is. Block C implementation is unblocked — first move is T1–T5 test scaffolding, then phased implementation, with the nine-invariant scorecard green throughout.
**Date:** 2026-04-21
**Scope:** Design for Block C of the regrouped memory roadmap: arc-level closure / end-of-arc synthesis. The third and final memory-roadmap block and the most ethically load-bearing.

**Precedents (cited, not re-derived):**
- `docs/PRE_BLOCK_C_PRECONDITIONS.md` — ratified 2026-04-21. Gate on this work.
- `docs/BLOCK_C_IMPLEMENTATION_ANALYSIS.md` — ratified 2026-04-21. D.1–D.5 resolved.
- `docs/BLOCK_A_DESIGN.md` + `docs/BLOCK_B_DESIGN.md` — substrate + stored-but-not-foregrounded that Block C sits alongside.
- `roadmap_tests/TORMENT_Memory_Roadmap_Regrouped.md` §7 (Item 4 — Closure).

> This document is the design for Block C. It commits to concrete class names, field names, method signatures, and file-level changes for arc-level closure. It does NOT re-derive the analysis: every architectural decision traces back to the ratified analysis or preconditions. If code reality during implementation contradicts a decision here, **surface the contradiction before proceeding** — do not silently widen scope. Block C's writeback-vs-closure guardrail (§10 of preconditions) is the sharpest invariant in this block — every implementation choice is challenged against it.

---

## 1. Objective

Add arc-level closure to TORMENT: a **ratified synthesis operation** that metabolizes coherent work sequences into durable, versioned closure objects for the agent's future self.

Closure is NOT:
- a new substrate class (Block A owns substrate)
- an extension of reference memory (Block B's `ReferenceEntry` shape does not fit)
- a writeback path (structurally separated at every layer)
- an automatic operation (ratification is explicit)
- an LLM-authored commitment (model may assist drafting, cannot author commits)
- a silent canonizer (unresolved material does not become canon as a side effect)

Closure IS:
- a new `memory_class="closure"` category with its own `ClosureStore`
- a lifecycle domain where proposal / ratification / commit / revision are **stages of one object**, derived from an append-only event ledger
- required to carry `deferred_or_open_items` as a structural field, never optional
- required to version, never silently overwrite
- audience-ordered toward the agent's future self first

Block C proves the closure foundation under real code, so the Block C design chain closes the three-block regrouped memory roadmap.

---

## 2. Scope / Out of scope

### In scope

- **New `ClosureStore` class** — per-workspace closure-object storage, parallel to `ReferenceStore` and `EnvironmentStore`.
- **New `ClosureLedger` class** — per-workspace append-only event ledger. Lifecycle state derived from events.
- **Single `ClosureEntry` dataclass** — one object shape per the watch-item; lifecycle stages are NOT separate classes.
- **Fabric methods:** `propose_closure`, `ratify_closure`, `commit_closure`, `revise_closure`, plus administrative reads (`get_closure`, `list_closures`).
- **ProvenanceV1 extensions:** three new `SOURCE_*` source types, one new `WRITE_CLOSURE_COMMIT` write path, three new factory methods.
- **Default-lane guard extension:** add `"closure"` to the `_NON_DEFAULT_CLASSES` frozenset at `fabric.query` merge point.
- **Open-items honesty mismatch detector** — shared helper, callable from `commit_closure`, reads concrete v0.1 signals (`ConflictRegistry` open conflicts + active batons filtered to arc scope).
- **Test harness** — five new test files covering AC-1 through AC-5.

### Out of scope (explicit)

- **Any change to `AgentRunner.run_turn`.** Runner stays frozen.
- **Any change to `fabric.query` signature.** Only the internal filter frozenset is extended.
- **Any change to `retrieval_assembler`.** Per D.1, no `BLOCK_CLOSURE` block type in v0.1. Closure is not prompt-context-integrable in v0.1.
- **Any reuse of writeback paths.** `WRITE_COGNITION_WRITEBACK` is never touched. `for_cognition_writeback` is never called by closure code. Writeback tests never import closure fixtures, and vice versa.
- **Any reuse of `fabric.ingest`.** Closure commits never produce `memory_class="core"` substrate entries.
- **Any extension of `ReferenceEntry`.** Per preconditions §10, no closure fields on reference entries.
- **Arc detection / auto-discovery.** Arc scope is an explicit `eid` list from the caller per D.3.
- **Closed `arc_kind` enum.** Free-form string per D.4.
- **Task-residue first-class concept.** Named gap per D.5; not solved in v0.1.
- **Automated closure proposals from structural signals.** R+7 — heuristics may surface proposals but cannot enact them.
- **LLM-authored commits.** R+9 — model assistance in drafting is legitimate; model-authored commits are refused.
- **MCP surface additions.** No new MCP tools in v0.1.
- **`retrieval_assembler` integration of closure.** Explicitly deferred to a post-slice increment.

### Carry-forward invariants

1. **Writeback-vs-closure guardrail (analysis §2.3 five-point checklist).** Every one of the five points must hold:
    - Separate `WRITE_CLOSURE_COMMIT` write_path constant.
    - Separate `ProvenanceV1.for_closure_commit` (and ratification / revision) factories.
    - Separate `ClosureLedger` JSONL file.
    - Separate `ClosureStore` persistence.
    - Separate test harness (no shared fixtures with writeback tests).
2. **Lifecycle stages are not object ontologies.** One `ClosureEntry` class; state derived from the ledger. Never `ClosureProposal` / `RatifiedClosure` / `CommittedClosure` / `RevisedClosure` as separate classes.
3. **`deferred_or_open_items` required, not optional (R+10).** Even when empty, the field exists.
4. **No retrospective editing without versioning (R+8).** Revisions produce new versions; originals preserved.
5. **No automatic closure enactment (R+7).** Ratification is a separate recorded action.
6. **No model-authored commits (R+9).** Authorship must be explicit, attributable, separately recorded.
7. **No silent unresolved → canon (R+11).** Closure commits do not auto-promote arc-scope material to durable canon.
8. **Audience ordering — future self first (preconditions §6).** Default views and revision flows preserve future-self honesty over user-readability.

---

## 3. Adopted ratified decisions

Cite, do not re-litigate. All five are frozen.

**D.1 — Storage (β).** New `ClosureStore` class, per-workspace, parallel to `ReferenceStore` and `EnvironmentStore`. NO `retrieval_assembler` integration in v0.1; closure is not prompt-context-integrable. (Ratified 2026-04-21.)

**D.2 — Ratification method placement (α).** Fabric-level methods (`propose_closure`, `ratify_closure`, `commit_closure`, `revise_closure`), backed by `ClosureStore` + `ClosureLedger` helpers. Consistent with Blocks A and B. (Ratified 2026-04-21.)

**D.3 — Arc scope definition (α).** Explicit `eid` list supplied by the caller at `propose_closure` time. No hidden arc-detection machinery. Auditable, concrete, keeps open-items honesty real. (Ratified 2026-04-21.)

**D.4 — Multi-scale support (β).** Free-form `arc_kind` string field on `ClosureEntry`. No closed enum. The four roadmap scales (cleanup / feature / stability / release) exist as convention, not vocabulary. (Ratified 2026-04-21.)

**D.5 — Task residue (β).** Named gap in v0.1. Closure arc scope covers memory-substrate material (open `ConflictRegistry` conflicts + active batons filtered to scope). Task residue as a first-class signal is a later increment. (Ratified 2026-04-21.)

### Watch-item carried forward

**Proposal / ratification / commit / revision are lifecycle stages, not separate object ontologies.** One `ClosureEntry` class with event-derived state. If this design ever starts sprouting sibling classes per stage, that is drift. The entry is one thing; the stages live in the ledger.

---

## 4. Acceptance criteria

Five criteria carried forward from analysis §B (ratified 2026-04-21). Each names the test that proves it.

**AC-1 — Closure shape validation.** `fabric.propose_closure(...)` succeeds only when every §5-required field is supplied. `deferred_or_open_items` specifically must exist (empty allowed; absent rejected). Missing any other required field → rejected with a named `result_code`. *Test: T1 `test_closure_shape_boundary.py`.*

**AC-2 — Ratification is structural.** `fabric.commit_closure(...)` without a prior `fabric.ratify_closure(...)` ratification event in the ledger → rejected. State is derivable from event stream only; cannot be forged by setting a direct bool field. *Test: T2 `test_closure_ratification_required.py`.*

**AC-3 — Versioning is honest.** `fabric.revise_closure(...)` produces a new version (new `version_id`), stored alongside the original. Original closure reads unchanged. `version_history` grows on each revision. No code path silently overwrites a prior version. *Test: T3 `test_closure_versioning_honest.py`.*

**AC-4 — Open-items honesty.** `fabric.commit_closure(...)` on a closure whose scope contains open `ConflictRegistry` conflicts or active batons, while `deferred_or_open_items` is empty → rejected with a specific mismatch result. The detector runs over concrete v0.1 signals per analysis §3.6. *Test: T4 `test_closure_open_items_honesty.py`.*

**AC-5 — Block A + B invariants preserved.** Closure operations do not modify baton lifecycle, reference load state, environment consult behavior, or core retrieval. All nine scorecard invariant tests remain green. `RESEARCH_ASSISTANT_PACK`'s `EMPTY_CONTRACT` untouched. *Test: T5 `test_closure_preserves_blocks_a_and_b.py` + CI scorecard run.*

---

## 5. Data model changes

### 5.1 — Provenance extensions (`torment_service/provenance_v1.py`)

Add three new `source_type` constants:

```python
# Block C — closure synthesis
SOURCE_CLOSURE_COMMIT       = "closure_commit"
SOURCE_CLOSURE_RATIFICATION = "closure_ratification"
SOURCE_CLOSURE_REVISION     = "closure_revision"
```

Add to `VALID_SOURCE_TYPES` frozenset.

Add one new `write_path` constant:

```python
WRITE_CLOSURE_COMMIT = "closure_commit"
```

Add to `VALID_WRITE_PATHS` frozenset. **This is structurally distinct from `WRITE_COGNITION_WRITEBACK` and `WRITE_REFLECTION_WRITEBACK`** per the writeback-vs-closure guardrail.

Add three factory methods:

- **`for_closure_commit(arc_name, ratifier, step=None, session_id=None, notes=None)`** — produces the commit-time provenance. `ratifier` records who ratified this commit (agent / user / dual). Distinct from archivist authorship. Uses `WRITE_CLOSURE_COMMIT`.
- **`for_closure_ratification(arc_name, ratifier, step=None, session_id=None, notes=None)`** — produces the ratification-event provenance (separate from commit; a proposal can be ratified without being committed yet). Uses `WRITE_DIRECT_INGEST` since the ratification record itself is just a lifecycle event.
- **`for_closure_revision(arc_name, ratifier, parent_closure_id, step=None, session_id=None, notes=None)`** — produces the revision provenance. `parent_closure_id` links to the closure being revised. Uses `WRITE_CLOSURE_COMMIT`.

### 5.2 — Single `ClosureEntry` dataclass

Per the watch-item: ONE class, not four. Lifecycle state is derived from the ledger.

```python
@dataclass
class ClosureEntry:
    closure_id: str                     # stable id; never echoed in load/ratify events
    version_id: str                     # stable id for THIS version
    workspace_id: str
    arc_name: str                       # REQUIRED
    arc_kind: str                       # REQUIRED (free-form per D.4)
    scope: List[int]                    # REQUIRED — explicit eid list per D.3
    what_it_was: str                    # REQUIRED
    what_worked: str                    # REQUIRED
    what_surprised: str                 # REQUIRED
    what_to_carry_forward: str          # REQUIRED
    deferred_or_open_items: List[str]   # REQUIRED (empty OK; absent rejected — R+10)
    authorship_provenance: Dict[str, Any]  # REQUIRED — ProvenanceV1.for_closure_commit dict
    version_history: List[Dict[str, Any]]   # REQUIRED (empty on first version; R+8)
    created_ts: int                     # when this version was created
    parent_version_id: Optional[str]    # present on revisions, linking to prior version
    metadata: Dict[str, Any] = field(default_factory=dict)
```

No `state` field on the entry. Lifecycle state (`proposed` / `ratified` / `committed` / `revised`) is **derived from `ClosureLedger` events** for this `closure_id`. This is the watch-item honored literally.

### 5.3 — Single `ClosureEvent` dataclass

```python
@dataclass
class ClosureEvent:
    event_id: str
    workspace_id: str
    closure_id: str               # which closure this event is about
    version_id: Optional[str]     # populated for committed / revised events
    kind: str                     # "proposed" | "ratified" | "committed" | "revised"
    ts: int
    ratifier: Optional[str]       # populated for ratified / committed / revised
    provenance: Dict[str, Any]    # ProvenanceV1 dict for this event
    notes: Optional[str]
```

Event kinds:
- `proposed` — `propose_closure` fires; creates the initial entry (not yet committed).
- `ratified` — `ratify_closure` fires; records that a ratifier approved the proposal. A proposal can be ratified but not yet committed.
- `committed` — `commit_closure` fires after ratification. Makes the closure durable.
- `revised` — `revise_closure` fires; produces a new `version_id` entry.

### 5.4 — Lifecycle-state derivation from events

A closure's current lifecycle state is the **last event's kind** for that `closure_id`:

- no events → closure doesn't exist.
- `proposed` is the last event → state is `proposed`.
- `proposed` then `ratified` → state is `ratified` (ratified but not committed).
- then `committed` → state is `committed`.
- then `revised` (one or more) → state is `revised` (current); the last `committed`-or-`revised` version is the current canonical version.

No field on `ClosureEntry` holds state directly. Queries like "is this closure committed" are answered by reading the ledger.

---

## 6. Closure lifecycle

Four fabric methods implement the four lifecycle operations. Each appends exactly one event to the ledger.

### 6.1 — `fabric.propose_closure`

```python
def propose_closure(
    self,
    workspace_id: str,
    arc_name: str,
    arc_kind: str,
    scope: List[int],                       # explicit eid list (D.3)
    what_it_was: str,
    what_worked: str,
    what_surprised: str,
    what_to_carry_forward: str,
    deferred_or_open_items: List[str],      # REQUIRED (empty OK; absent rejected)
    metadata: Optional[Dict[str, Any]] = None,
    step: int = 0,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a closure proposal (Block C §6.1).

    Validates required fields. Writes the ClosureEntry to the store.
    Appends a "proposed" event to the ledger. The proposal is NOT
    yet committed — a separate ratify_closure + commit_closure pair
    is required (R+7).

    Returns envelope:
        {"ok": True, "result_code": "proposed", "closure_id": str,
         "version_id": str}
        or on missing required field:
        {"ok": False, "result_code": "missing_required_field",
         "missing_field": str, "closure_id": "", "version_id": ""}
    """
```

Validation list (all rejected → `missing_required_field` with the specific field name):
- `arc_name`, `arc_kind`, `what_it_was`, `what_worked`, `what_surprised`, `what_to_carry_forward` — all non-empty strings required.
- `scope` — must be a non-empty list.
- `deferred_or_open_items` — must be a list (empty OK; `None` or absent rejected).

### 6.2 — `fabric.ratify_closure`

```python
def ratify_closure(
    self,
    workspace_id: str,
    closure_id: str,
    ratifier: str,                          # agent_id, "user", or dual identifier
    notes: Optional[str] = None,
    step: int = 0,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record ratification of a closure proposal (Block C §6.2).

    Appends a "ratified" event to the ledger. Does NOT commit; a
    separate commit_closure is required. This preserves the
    ratification-is-structural rule from preconditions §4.

    Returns envelope:
        {"ok": True, "result_code": "ratified", "closure_id": str}
        or on error:
        {"ok": False,
         "result_code": "not_found" | "already_committed" | "empty_ratifier",
         "closure_id": str}
    """
```

Rejects empty ratifier (model synthesis alone is not valid per R+9 — a closure ratification with `ratifier=""` or `ratifier="llm"` alone is insufficient; design-doc note: the Block C design deliberately leaves `ratifier` as a free string; external policy can add a vocabulary check later).

### 6.3 — `fabric.commit_closure`

```python
def commit_closure(
    self,
    workspace_id: str,
    closure_id: str,
    ratifier: str,
    step: int = 0,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Commit a ratified closure — the transition to durable.

    Requires a prior "ratified" event for this closure_id in the
    ledger (AC-2). Runs the open-items honesty check (AC-4) before
    committing: if the closure's scope contains open
    ConflictRegistry conflicts or active batons whose ids fall in
    scope AND deferred_or_open_items is empty → rejected.

    Appends a "committed" event to the ledger on success.

    Returns envelope:
        {"ok": True, "result_code": "committed", "closure_id": str,
         "version_id": str}
        or on reject:
        {"ok": False,
         "result_code": "not_found" | "not_ratified" | "already_committed"
                      | "open_items_mismatch",
         "closure_id": str,
         "unresolved": Optional[Dict[str, Any]]}
    """
```

`open_items_mismatch` carries the unresolved signals (open conflicts + active batons) so the caller knows what to declare.

### 6.4 — `fabric.revise_closure`

```python
def revise_closure(
    self,
    workspace_id: str,
    closure_id: str,
    revised_fields: Dict[str, Any],         # fields to change in the new version
    ratifier: str,
    step: int = 0,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Produce a new version of a committed closure (R+8).

    Creates a new ClosureEntry with a new version_id. The original
    version_id remains in the store — never overwritten. The new
    version's `version_history` gets an entry linking it to the
    prior version_id. A "revised" event is appended to the ledger
    with ratifier and authorship recorded.

    Only committed closures can be revised (you don't revise a
    proposal; you revise the proposal itself by creating a new
    proposal).

    Returns envelope:
        {"ok": True, "result_code": "revised", "closure_id": str,
         "version_id": str, "parent_version_id": str}
        or on reject:
        {"ok": False,
         "result_code": "not_found" | "not_committed"
                      | "missing_ratifier" | "open_items_mismatch",
         "closure_id": str}
    """
```

Revisions also go through open-items honesty check — a revision that would set `deferred_or_open_items=[]` while the scope still has open conflicts / active batons is rejected.

### 6.5 — `ClosureStore` (persistence)

**File:** `torment_service/closure_memory.py` (new, est. ~400 LoC).

Per-workspace. Own folder layout:

```
<data_dir>/workspaces/<ws>/closure_memory/
  closures.jsonl        (append-only; each line is one ClosureEntry version)
  events.jsonl          (ClosureStore internal events — proposal/delete)
```

Methods:

- `__init__(data_dir, workspace_id)` — same pattern as `ReferenceStore`.
- `add_version(entry: ClosureEntry)` — appends new version to closures.jsonl.
- `get_version(closure_id, version_id) -> Optional[ClosureEntry]`.
- `get_latest_version(closure_id) -> Optional[ClosureEntry]` — returns the most recent version.
- `list_versions(closure_id) -> List[ClosureEntry]` — all versions of one closure.
- `list_closures(workspace_id) -> List[str]` — list of closure_ids.

No delete method in v0.1. Closure objects are durable by design.

### 6.6 — `ClosureLedger` (audit + lifecycle derivation)

**File:** `torment_service/closure_ledger.py` (new, est. ~150 LoC).

Per-workspace. Own JSONL:

```
<data_dir>/workspaces/<ws>/closure_memory/closure_events.jsonl
```

(Same directory as the store, but a distinct file — NEVER shares with the ingest events.jsonl or with any other audit trail per §7.)

Methods:

- `__init__(data_dir, workspace_id)`.
- `add_event(event: ClosureEvent)`.
- `list_events(closure_id=None, kind=None, limit=500) -> List[ClosureEvent]`.
- `get_latest_event_kind(closure_id) -> Optional[str]` — derives lifecycle state.
- `has_ratification(closure_id) -> bool` — helper for AC-2 precondition.
- Build-helpers: `build_proposed_event`, `build_ratified_event`, `build_committed_event`, `build_revised_event` — same pattern as `BatonLedger` and `ReferenceLoadLedger`.

---

## 7. Writeback-vs-closure structural separation (five-point checklist)

Per analysis §2.3 — every point must hold. This section pins each one against a concrete design commitment.

### 7.1 — Separate `WRITE_CLOSURE_COMMIT` write_path

✓ `WRITE_CLOSURE_COMMIT = "closure_commit"` is a new constant in `provenance_v1.py`, distinct from `WRITE_COGNITION_WRITEBACK` and `WRITE_REFLECTION_WRITEBACK`. Registered in `VALID_WRITE_PATHS`.

### 7.2 — Separate provenance factories

✓ Three new factories: `for_closure_commit`, `for_closure_ratification`, `for_closure_revision`. None of them calls or reuses `for_cognition_writeback`. The factories produce distinct `source_type` values and (for commit / revision) the distinct `WRITE_CLOSURE_COMMIT` path.

### 7.3 — Separate `ClosureLedger` JSONL file

✓ `closure_events.jsonl` lives in `<ws>/closure_memory/`. Never shares with `<ws>/agents/<agent>/baton_events.jsonl`, `<ws>/agents/<agent>/reference_load_events.jsonl`, `<ws>/environment_memory/events.jsonl`, or any archivist/writeback audit file.

### 7.4 — Separate `ClosureStore` persistence

✓ `closures.jsonl` and `closure_events.jsonl` live under `<ws>/closure_memory/`. No shared storage with `ReferenceStore` (`<ws>/reference_memory/`), `EnvironmentStore` (`<ws>/environment_memory/`), archive (`<ws>/...`), or core substrate.

### 7.5 — Separate test harness

✓ Five new test files under `tests/test_closure_*.py`. Explicitly verified: Block C tests do NOT import `test_writeback_recursion_guard.py` fixtures or any writeback-adjacent helpers. No `from torment_service.migration` imports in closure tests.

### 7.6 — The temptation patterns resisted

For future code review: if any PR introduces any of the following, it is the collapse failure mode:

- Calling `ProvenanceV1.for_cognition_writeback` from a closure method.
- Setting `write_path="cognition_writeback"` on a closure entry's provenance.
- A `ClosureLedger.add_event` call that also writes to `archivist_log` or similar.
- A closure code path that calls `fabric.ingest` or that creates a `memory_class="core"` entry as a side effect.
- Shared test fixtures between `test_closure_*.py` and `test_writeback_recursion_guard.py`.

Reviewers: challenge before merge. This is the load-bearing invariant.

---

## 8. Open-items honesty — mismatch detection

Per AC-4 + analysis §3.6. This is §8.4's concrete algorithm, implemented as a shared helper.

### 8.1 — The helper

**File:** `torment_service/closure_memory.py` (helper function, not a method — it's pure over its inputs).

```python
def detect_open_items_mismatch(
    fabric: TormentFabric,
    workspace_id: str,
    scope: List[int],
    declared_open_items: List[str],
) -> Dict[str, Any]:
    """Detect mismatch between known-unresolved signals in scope and
    declared open items.

    Signals (v0.1):
        - ConflictRegistry.list(status="open") filtered to conflicts
          with eid_a ∈ scope OR eid_b ∈ scope
        - fabric.list_active_batons(...) filtered to active batons
          whose eid ∈ scope

    Returns:
        {"mismatch": bool,
         "unresolved_conflicts": [{"conflict_id", "eid_a", "eid_b"}],
         "unresolved_batons": [{"eid", "summary"}],
         "declared": [...],
         "reason": Optional[str]}

    Mismatch fires when:
        - (unresolved_conflicts + unresolved_batons) is non-empty AND
          declared_open_items is empty.

    A non-empty declared_open_items list satisfies the check even if
    it doesn't literally enumerate every unresolved item (full
    coverage is a later increment; v0.1 is anti-false-finality, not
    full-truth-check).
    """
```

### 8.2 — Where it's called

- From `fabric.commit_closure` — before appending the `committed` event. If mismatch → reject with `open_items_mismatch` result_code.
- From `fabric.revise_closure` — before appending the `revised` event. Same rejection.

### 8.3 — Task residue gap (D.5 honored)

The helper uses ONLY the two v0.1-supported signals. It does NOT check task residues (that's the named gap). A future increment can add a third signal source; doing so is an additive change.

### 8.4 — Rigidity sniff test

Mismatch rejection is **lifecycle-required-metadata enforcement** (the caller must declare open items when evidence says some exist), NOT restricting what the closure can claim. The caller remains free to close the arc; they just must acknowledge what's unresolved. This passes the rigidity sniff test the same way Block A's baton validation did.

---

## 9. Test plan

Five new test files. Unit-scope. Expected combined runtime <6 seconds. No fixture entanglement with writeback.

| # | File | Covers | Reuses fixtures from |
|---|---|---|---|
| T1 | `tests/test_closure_shape_boundary.py` | AC-1 | `test_baton_requires_lifecycle_fields.py` |
| T2 | `tests/test_closure_ratification_required.py` | AC-2 | `test_reinforce_contract_invariant.py` |
| T3 | `tests/test_closure_versioning_honest.py` | AC-3 | `test_resolve_baton_soft_consume.py` |
| T4 | `tests/test_closure_open_items_honesty.py` | AC-4 | `test_private_ingest_contradiction_surface.py` (ConflictRegistry pattern) + baton-active fixtures |
| T5 | `tests/test_closure_preserves_blocks_a_and_b.py` | AC-5 | `test_agent_loop_block_b_present.py` |

**Scorecard regression requirement.** All nine scorecard invariants green. Same rule as Blocks A and B.

**Explicit no-shared-fixtures check.** T1–T5 must not import anything from `test_writeback_recursion_guard.py` or any migration/writeback test. Reviewer's checklist item per §7.5.

---

## 10. Non-runtime-touching guarantees

Per preconditions §11 and analysis §7.2, Block C makes specific *absence* commitments:

- **`AgentRunner.__init__` signature unchanged.** No new parameters.
- **`AgentRunner.run_turn` body unchanged.** No new phases, no new calls.
- **`FabricHandle` Protocol unchanged.** Still three methods (`ingest`, `measure_drift`, `gravity_correction`).
- **`fabric.query` signature unchanged.** Only the internal `_NON_DEFAULT_CLASSES` frozenset is extended from `{baton, reference, environment}` to `{baton, reference, environment, closure}`.
- **`action_policy` module unchanged.**
- **`retrieval_assembler` unchanged.** No `BLOCK_CLOSURE`, no new profile percentages, no new FILL_ORDER entry. (Deferred per D.1.)
- **`SessionLifecycleHook` still declaration-only.**
- **`mcp_server.py` unchanged.** No new MCP tools.
- **`memory_graph.spawn_memory` signature unchanged.** Closure never touches the memory graph.
- **`behavior_packs.py` unchanged.** RESEARCH_ASSISTANT_PACK's EMPTY_CONTRACT preserved.
- **All nine scorecard invariant test files unchanged.**
- **`archive_memory.py` / `reference_memory.py` / `environment_memory.py` unchanged.** Closure does not extend, wrap, or modify them.

These absences are load-bearing. Any PR touching them during Block C implementation must surface and justify — no silent scope widening.

---

## 11. Open questions

Only questions that genuinely remain after ratification.

**Q1 — `ratifier` vocabulary.** Design leaves `ratifier` as a free string (agent_id, "user", or a dual identifier). Should a future increment add a vocabulary check (like `VALID_EVIDENCE_CLASSES`)? Recommendation: no — `ratifier` is attribution metadata, not gated vocabulary. External policy (e.g., an identity check in HTTP endpoint) can layer on if needed.

**Q2 — `arc_kind` naming convention.** Free-form per D.4, but the four roadmap scales exist as convention (`cleanup` / `feature` / `stability_window` / `release`). Should the design doc pre-declare these names as documented-but-not-enforced? Recommendation: name them in design comments for discoverability; do NOT enforce. This preserves D.4 while giving integrators a starting vocabulary.

**Q3 — Open-items honesty — partial coverage.** v0.1 accepts any non-empty `deferred_or_open_items` as passing the check. A malicious or careless caller could declare `["something"]` without meaningful detail. Full-coverage enforcement (every unresolved signal must be literally enumerated) is a later increment. For v0.1, the anti-false-finality guard is the commit gate's presence, not its depth.

**Q4 — Closure retrieval via `load`.** v0.1 has no `fabric.load_closure` method. Admin / test code reads via `get_closure` or `list_closures`. A future increment may add a load path that integrates into `retrieval_assembler` as `BLOCK_CLOSURE` (the (γ) option rejected from v0.1). Flagging so the analysis's recommended deferral is remembered.

**None of Q1–Q4 blocks design ratification.** They can be refined during implementation or in post-slice increments.

---

## 12. Ratification record

**Drafted:** 2026-04-21 by Claude, following ratified analysis 2026-04-21.

**Ratification pass (2026-04-21, user + GPT):**

- [x] §1 Objective accepted
- [x] §2 Scope / out-of-scope + carry-forward invariants accepted
- [x] §3 Adopted D.1–D.5 decisions (citations) accepted
- [x] §4 Acceptance criteria (AC-1 through AC-5) accepted
- [x] §5 Data model (provenance extensions, single `ClosureEntry`, single `ClosureEvent`, event-derived state) accepted
- [x] §6 Closure lifecycle (four fabric methods, ClosureStore, ClosureLedger) accepted
- [x] §7 Writeback-vs-closure five-point checklist accepted
- [x] §8 Open-items honesty mismatch detection (concrete algorithm) accepted
- [x] §9 Test plan (T1 – T5) accepted
- [x] §10 Non-runtime-touching guarantees accepted
- [x] §11 Open questions — no blockers, accepted for implementation-time resolution

**Status:** **RATIFIED 2026-04-21 by user + GPT.** Block C implementation is unblocked. Any change to the design after this point requires a separately ratified amendment.

### Handoff notes for implementation

1. **First move is test scaffolding.** Land T1–T5 stubs (failing tests per AC-1–AC-5) before wiring any behavior.
2. **Nine-invariant scorecard stays green throughout.** No merges if any scorecard test regresses.
3. **Lifecycle stages are not object ontologies.** `ClosureEntry` is ONE class. State derived from `ClosureLedger` events. Any PR that introduces `ClosureProposal`, `RatifiedClosure`, `CommittedClosure`, or `RevisedClosure` as separate classes is drift — reject.
4. **Writeback-vs-closure structural separation is the sharpest invariant.** The §7.6 "temptation patterns resisted" list is the reviewer's checklist.
5. **Open-items honesty uses only v0.1 signals.** `ConflictRegistry` open conflicts + active batons filtered to arc scope. Task-residue signal is a named gap — do not add it in v0.1.
6. **`deferred_or_open_items` is required, never optional.** Reject the shape if it's absent; empty list is accepted.
7. **Versions are new, never overwrites.** `revise_closure` always creates a new `version_id`. Original readable.
8. **Ratifier attribution is explicit.** Model assistance in drafting is legitimate; model-authored commits (ratifier empty or model-only) are rejected.
9. **Event-derived lifecycle stays explicit, deterministic, auditable.** Added during ratification as the sharpest implementation caution. Allowed: a `proposed` event exists → state is `proposed`; a `ratified` event after a `proposed` → state is `ratified`; `commit_closure` rejects unless a `ratified` event exists for that `closure_id`; `revise_closure` always creates a new `version_id` entry. **Not allowed:** inferring lifecycle from loose combinations of events, heuristic interpretation layers, ambiguous state reconstruction, "smart" lifecycle detection. The derivation rule is literal event-kind lookup in the ledger — nothing fancier.

---

## Appendix — files expected to change or be created

### New files

- `torment_service/closure_memory.py` — `ClosureStore` + `ClosureEntry` + `detect_open_items_mismatch` helper (~400 LoC).
- `torment_service/closure_ledger.py` — `ClosureLedger` + `ClosureEvent` (~150 LoC).
- `tests/test_closure_shape_boundary.py` — T1 (AC-1).
- `tests/test_closure_ratification_required.py` — T2 (AC-2).
- `tests/test_closure_versioning_honest.py` — T3 (AC-3).
- `tests/test_closure_open_items_honesty.py` — T4 (AC-4).
- `tests/test_closure_preserves_blocks_a_and_b.py` — T5 (AC-5).

### Modified files

- `torment_service/provenance_v1.py` — three new `SOURCE_*` constants, one new `WRITE_CLOSURE_COMMIT` constant, three new factory methods.
- `torment_service/fabric.py` — four new public methods (`propose_closure`, `ratify_closure`, `commit_closure`, `revise_closure`), two administrative reads (`get_closure`, `list_closures`), plus private helpers (`_get_closure_store`, `_get_closure_ledger`). Default-lane filter frozenset extended from `{baton, reference, environment}` to `{baton, reference, environment, closure}`.

### Not changed (explicitly preserved per §10)

- `torment_service/agent_loop.py` — runner untouched.
- `torment_service/thinking_controller.py` — controller unchanged.
- `torment_service/memory_graph.py` — `spawn_memory` signature unchanged.
- `torment_service/action_policy.py` — no wiring.
- `torment_service/retrieval_assembler.py` — no `BLOCK_CLOSURE`, FILL_ORDER unchanged.
- `torment_service/archive_memory.py`, `torment_service/reference_memory.py`, `torment_service/environment_memory.py` — untouched.
- `torment_service/reference_load_ledger.py`, `torment_service/environment_event_ledger.py`, `torment_service/baton_ledger.py` — untouched.
- `torment_service/behavior_packs.py` — packs unchanged; RESEARCH_ASSISTANT_PACK still EMPTY_CONTRACT.
- `torment_service/mcp_server.py` — MCP surface unchanged.
- `torment_service/conflicts.py` — `ConflictRegistry` unchanged (closure reads from it, doesn't modify).
- All nine scorecard invariant test files — unchanged.
