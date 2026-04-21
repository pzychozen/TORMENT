# Block C Implementation Analysis — Pre-Design Phase

**Status:** **RATIFIED 2026-04-21** by user + GPT. All sections accepted; D.1–D.5 resolved. Block C may now move to its design-doc phase using this analysis as the immediate starting point.
**Date:** 2026-04-21
**Scope:** Code-grounded analysis mapping Block C's ratified preconditions onto the current codebase (Blocks A + B landed), before the Block C design doc is written.

**Precedents:**
- `docs/PRE_BLOCK_C_PRECONDITIONS.md` — ratified 2026-04-21. Gate on this work.
- `docs/BLOCK_A_DESIGN.md` — ratified 2026-04-19, merged 2026-04-21.
- `docs/BLOCK_B_DESIGN.md` — ratified 2026-04-21.
- `roadmap_tests/TORMENT_Memory_Roadmap_Regrouped.md` §7 (Item 4 — Closure).

> This document is analysis, not design. Two carry-forward concerns from preconditions ratification are load-bearing throughout: (1) resist collapsing closure into an upgraded writeback path — if analysis finds an "easy" way to reuse writeback plumbing, that is the danger signal, not the solution; (2) open-items honesty (§8.4) must be grounded in concrete evidence sources, not hand-wavy intention — the analysis must map exactly where unresolvedness lives.

---

## 1. Findings — closure fit decision (clause 1 is open)

Preconditions clause 1 allows two shapes: closure objects as Block B reference citizens, OR a stricter alternative that does not reopen Block A substrate semantics. This section evaluates the fit from code.

### 1.1 — What Block B's `ReferenceStore` already provides

From `torment_service/reference_memory.py`:

- Per-workspace whole-object storage.
- `ReferenceEntry` shape: `ref_id`, `title`, `body`, `source_link`, `source_kind`, `source_hash`, `provenance`, `created_ts`, `metadata`.
- Load / unload lifecycle with `ActiveLoad` kept structurally separate from the entry.
- Flows into `retrieval_assembler` as `BLOCK_REFERENCE` when loaded.
- Staleness-on-load.

### 1.2 — What closure objects require that reference does not currently provide

Closure object minimum shape (preconditions §5):

| Field | ReferenceEntry has it? | Fit as-is? |
|---|---|---|
| `arc_name` | No (title is closest) | Needs distinct field |
| `scope` | No | New; describes which substrate entries / batons / references belong to the arc |
| `what_it_was` / `what_worked` / `what_surprised` / `what_to_carry_forward` | No | Structured body, not free `body` |
| `deferred_or_open_items` | No | Required, never optional (R+10) |
| `authorship_provenance` | `provenance` is generic | Closure-specific authorship distinct from storage event (§4) |
| `version_history` | No | Required, never optional (R+8) |

Plus: closure is **synthesized from scope** (not ingested from external source). `source_link` / `source_kind` don't apply in the usual sense — the "source" is the arc's internal material, not an external document.

### 1.3 — Fit judgment

**Forcing closure onto the current `ReferenceEntry` shape is wrong.** The fields don't line up, and the semantic asymmetry (closure = synthesized-from-scope vs reference = linked-to-source) would muddle both categories.

Two viable shapes:

**(α) Extended-reference model:** `ReferenceEntry` gains optional closure-specific fields (or a nested `closure: Optional[ClosureFields]` sub-object). Closure objects are reference entries with their closure fields populated; reference-only objects have them null. Reuses ReferenceStore + ReferenceLoadLedger + BLOCK_REFERENCE integration. **Risk:** violates the Block-B-vs-Block-C guardrail (§10 of preconditions) by adding closure fields to `ReferenceEntry`.

**(β) New `ClosureStore` parallel to `ReferenceStore`:** own folder, own JSONL, own dataclass shape with full closure fields as first-class. Separate from reference entirely. **Risk:** more code, plus retrieval_assembler doesn't get closure objects into prompt context unless a new `BLOCK_CLOSURE` is added.

**(γ) Hybrid — new `ClosureStore`, but closures are loadable via a reference-style path for prompt context:** Closure lives in `ClosureStore` with its own shape. When the agent wants to think with a past closure, a load-path serves it into `retrieval_assembler` as a `BLOCK_REFERENCE` block (or a new `BLOCK_CLOSURE` block). This preserves the category distinction while giving closures a way into prompt context when needed.

**Recommendation: (β) or (γ).** Clause 1 allows a stricter alternative if it doesn't reopen Block A semantics, and both (β) and (γ) honor that. Option (α) violates §10's explicit "do NOT add closure-related fields to `ReferenceEntry`" guardrail and should be rejected.

Between (β) and (γ): (γ) is richer but adds a new block type to the assembler, which needs explicit ratification per the "no drift into Block B retrieval mechanics" rule. (β) is simpler and safer for v0.1; (γ) can be a post-slice increment.

**This is D.1. Needs ratification before design starts.**

---

## 2. Findings — writeback-vs-closure separation probe (carry-forward concern 1)

This is the load-bearing section per the user's explicit guidance. If analysis finds a tempting collapse into writeback, that is the danger signal.

### 2.1 — Where writeback currently lives

From `torment_service/provenance_v1.py`:

```python
WRITE_COGNITION_WRITEBACK = "cognition_writeback"
WRITE_REFLECTION_WRITEBACK = "reflection_writeback"
```

Plus the factory:

```python
for_cognition_writeback(source_role, parent_eids, step, session_id, notes)
```

This is the archivist / cognition-pipeline write-back path. Role-output memory written back to the substrate carries this write_path.

The writeback gate framing (`docs/ARCHIVIST_WRITEBACK_GATE_FRAMING_v2.4.x.md` per memory) established that writeback stays narrow, opt-in, reversible.

### 2.2 — Temptation points for closure → writeback collapse

**Temptation 1: "Closure is synthesized content; writeback is the existing synthesized-content path."**

If closure commits used `WRITE_COGNITION_WRITEBACK` as their `write_path`, the two concerns would share a provenance track. This is EXACTLY the failure mode the preconditions §10 guardrail protects against.

**Resistance:** Block C gets its own `WRITE_CLOSURE_COMMIT` write_path constant. Its own factory method. Its own ledger. The provenance layer must make it structurally impossible to confuse closure commits with writeback.

**Temptation 2: "Closure objects could reuse the writeback audit trail."**

Writeback audit lives in the existing archivist logs. If closure commits went through the same audit path, audit tooling would conflate them.

**Resistance:** `ClosureLedger` is its own file. Never shares events.jsonl or audit structure with writeback.

**Temptation 3: "Closure's `authorship_provenance` field could reuse the archivist authorship pattern."**

The archivist produces role-output memory with `source_role` recording the role that wrote it. A naive implementation might set `authorship_provenance={"source_role": "archivist"}` for closure commits.

**Resistance:** Closure authorship records agent / user / dual ratifier identity, NOT the archivist role that may have helped draft. R+9 distinguishes model-assisted drafting from model-authored commitment. Closure authorship fields must be structurally different from archivist provenance.

**Temptation 4: "Closure could commit via `fabric.ingest` with parent_eids."**

`fabric.ingest` is the substrate write path. If closure commits went through it, they'd become `memory_class="core"` entries with closure-like payload. This would make closure-as-substrate-entry the implicit shape — the failure mode R+3 (no silent load→durable) and the Block-A-substrate-untouched invariant both forbid.

**Resistance:** Closure commits MUST NOT go through `fabric.ingest`. They go through a dedicated `fabric.commit_closure` (or similar) that writes to the closure-specific store.

### 2.3 — Writeback separation checklist (for the design doc)

The Block C design doc must pass all five:

1. **Separate write_path constant.** New `WRITE_CLOSURE_COMMIT` (or equivalent name), distinct from `WRITE_COGNITION_WRITEBACK` and `WRITE_REFLECTION_WRITEBACK`.
2. **Separate provenance factory.** `ProvenanceV1.for_closure_commit` (and `for_closure_ratification` for the ratification event) — distinct from `for_cognition_writeback`.
3. **Separate ledger.** `ClosureLedger` is its own JSONL file. Never shares events.jsonl with writeback or any other audit trail.
4. **Separate store.** Closure objects live in `ClosureStore` (per §1.3 recommendation); never in `memory_graph` as core entries and never in `ReferenceStore` as entries with closure fields.
5. **Separate test harness.** Per preconditions §10, closure tests never import writeback fixtures, and writeback tests never import closure fixtures.

### 2.4 — Summary for this section

No existing code path is the right collapse target for closure. Every temptation above leads to failure-mode drift. The writeback-vs-closure guardrail is honored by *structural separation at every layer*, not by runtime-time filtering.

---

## 3. Findings — open-items honesty mapping (carry-forward concern 2)

This is the concrete evidence-source mapping the preconditions §8.4 test needs. Unresolvedness currently lives in four places in the code.

### 3.1 — Evidence source 1: `ConflictRegistry` (open conflicts)

From `torment_service/conflicts.py`:
- `CanonConflict.status` takes values `{"open", "resolved", "rejected", "forked"}`.
- `ConflictRegistry.list(status="open", limit=500)` returns open conflicts.
- Block A wired private-ingest contradiction surfacing to this registry (fabric.py contradiction-surface block).

**Closure scope evidence:** For any arc, `ConflictRegistry.list(status="open")` filtered to conflicts whose `eid_a` or `eid_b` is in the arc's scope gives the *claim-level unresolvedness* in that arc. If the arc contains open conflicts, the closure's `deferred_or_open_items` MUST acknowledge them.

### 3.2 — Evidence source 2: Active batons (attention-bounded unresolvedness)

From Block A:
- `baton_lifecycle.status == "active"` identifies unresolved attention-bounded intent.
- `fabric.list_active_batons(workspace_id, agent_id)` returns them.

**Closure scope evidence:** Any active baton whose creation or attention scope falls within the closure's arc scope is lifecycle unresolvedness. If the arc contains active batons, closure's `deferred_or_open_items` MUST include them (or document why they're considered resolved by the closure itself).

### 3.3 — Evidence source 3: Reference active loads (not typically closure-relevant)

From Block B:
- `ActiveLoad.status == "active"` identifies reference material currently loaded.
- `fabric.list_active_loads(workspace_id, agent_id)` returns them.

**Closure scope evidence:** Usually not relevant to closure unresolvedness — an active load means "currently being thought with," not "unresolved." But if closure is proposed for an arc that includes research references still in active load at commit time, that's a signal the arc may not be genuinely ready to close. Worth surfacing in the 8.4 mismatch-detection check as a **soft** signal.

### 3.4 — Evidence source 4: Environment entries (not typically closure-relevant)

From Block B:
- `EnvironmentEntry.evidence_class == "inferred"` with `inferred=True` in consult views identifies tentative operational knowledge.
- Environment is per-workspace, not per-arc; typically not load-bearing for arc closure.

**Closure scope evidence:** Mostly out of scope for closure honesty. Environment changes may have occurred during the arc but aren't "unresolved" in the same sense. Include only if the design doc finds a specific case where environment state IS arc-scoped (e.g., "this arc depends on a user-asserted environment fact that's since been contradicted").

### 3.5 — Evidence source 5: Task residue (GAP — no first-class concept)

The roadmap §7 names "task residues" as arc-scope material, but TORMENT doesn't have a first-class TaskList structure that distinguishes "completed" from "residue." The closest existing constructs:

- Batons (for cross-session attention) — already covered in §3.2.
- Assimilation outcomes (Phase 7 dispatch) — Block A's stub; v0.1 doesn't emit concrete outcomes.
- No explicit task queue or residue tracker.

**Implication:** Block C's 8.4 open-items honesty test uses ConflictRegistry + active batons as its primary signals. Task residue signals require either (a) Block C design adds a new signal source, or (b) closure arc scope is interpreted as covering only memory-substrate material, not workflow state.

**Recommendation: (b) for v0.1.** Closure operates on memory-substrate material (core + baton + possibly reference). Task residue as a first-class signal is a later increment — Block C should name the gap but not try to close it in v0.1. **This is D.5.**

### 3.6 — The concrete 8.4 mismatch-detection algorithm

For a closure proposal with arc scope `S`:

1. Collect `open_conflicts = ConflictRegistry.list(status="open")` filtered to conflicts where `eid_a ∈ S` or `eid_b ∈ S`.
2. Collect `active_batons = fabric.list_active_batons(...)` filtered to batons created during the arc time window or scoped to the arc.
3. `known_unresolved = union(open_conflicts, active_batons)`.
4. If `known_unresolved` is non-empty AND `closure.deferred_or_open_items` is empty → **flag mismatch**. Reject the commit, or mark the proposal for ratification review.
5. If `known_unresolved` is empty → no mismatch (8.4 passes trivially).
6. If `known_unresolved` is non-empty AND `closure.deferred_or_open_items` acknowledges at least some (not necessarily all) — v0.1 accepts. Full coverage check is a later increment.

This is implementable in v0.1 with existing Block A / B infrastructure. No new signal sources needed.

---

## 4. Findings — ratification structural seam

Preconditions §4 says closure ratification is a separate recorded action, not a metadata flag. This section maps where ratification-like patterns already exist.

### 4.1 — Existing ratification-like patterns

**`ConflictRegistry.decide(conflict_id, decision, note)`** — per-conflict ratification. Decision is a recorded event (`decide` appends to `conflict_events.jsonl`). `apply_events` replays events to derive current status. This is a clean "structural ratification" pattern.

**Reinforce contract** — each `fabric.reinforce` call is a recorded action with an envelope. Not quite ratification, but the same narrow-explicit-writer-with-envelope pattern.

**Baton `resolve_baton`** — soft-consume with an explicit action and ledger event. Again, the same narrow-explicit-writer pattern.

**`BridgeRegistry.decide`** — bridge decisions are per-bridge recorded events.

### 4.2 — What closure ratification needs

From preconditions §4:

- Its own provenance factory (distinct from `for_cognition_writeback`).
- Its own ledger event.
- Its own explicit ratifier identity (user / agent / dual).
- Its own timestamp distinct from draft / proposal.

**Recommended pattern:** follow `ConflictRegistry.decide` — a separate `ratify_closure(closure_id, ratifier, note)` method that appends a ratification event to the closure's event ledger. The closure object in storage carries a state field (`proposal` / `ratified` / `committed` / `revised`) that's derived from the event stream, not set directly.

**Key design decision (D.2):** is `ratify_closure` a fabric method or a store method? `ConflictRegistry.decide` is a registry method. `fabric.resolve_baton` is a fabric method. For v0.1, either works — but fabric-level is more consistent with Block A / B's method placement (baton and reference operations are fabric methods).

**Recommendation:** `fabric.propose_closure`, `fabric.ratify_closure`, `fabric.revise_closure` as fabric-level methods. ClosureStore handles persistence; ClosureLedger handles audit.

---

## 5. Findings — audience-ordering in code

Preconditions §6 says closure's primary audience is agent's future self > next AI > user. This is mostly a design/wording concern, not a code enforcement concern — but there are two code touchpoints:

### 5.1 — Default closure view

When a closure is retrieved (via `load_closure` or equivalent), what's the default view? If closure objects get integrated into `retrieval_assembler` (option γ from §1.3), the prompt-context insertion is implicitly future-self-oriented (the agent reads its own past closure to reason with).

For user-facing views (HTTP endpoints, future MCP tool if any), the default format should NOT re-order or omit fields based on "what the user wants." Fields stay in the order the closure object defines; omissions require explicit user action (and are logged).

### 5.2 — Revision review flow

When a closure is revised, the design must NOT privilege user-readability over future-self honesty. If revising for clarity also reduces future-self-relevant structural detail, the revision is refused (or requires explicit separate ratification).

### 5.3 — Summary

Audience-ordering is not strongly code-enforceable in v0.1 beyond "don't re-order fields on user-facing views" and "don't privilege user-facing readability in revision review." The invariant lives more in design discipline than in runtime checks. The implementation analysis has noted the concern; the Block C design doc must preserve it in its prose.

---

## 6. Findings — test anchor points

### 6.1 — Mapping §8 to real locations

**Test 8.1 — Closure-object-shape.** `tests/test_closure_shape_boundary.py` (new).
- Pattern source: `test_baton_requires_lifecycle_fields.py`, `test_reference_load_boundary.py`.
- Asserts: commit missing any required §5 field is rejected; `deferred_or_open_items` specifically must exist (empty OK, absent rejected).

**Test 8.2 — Ratification-required.** `tests/test_closure_ratification_required.py` (new).
- Pattern source: `test_reinforce_contract_invariant.py` (envelope shape).
- Asserts: commit without ratification event → rejected with named result code.

**Test 8.3 — Version-not-overwrite.** `tests/test_closure_versioning_honest.py` (new).
- Pattern source: `test_resolve_baton_soft_consume.py` (audit-trail discipline).
- Asserts: revision produces new version; original readable; `version_history` record links them.

**Test 8.4 — Open-items-honesty.** `tests/test_closure_open_items_honesty.py` (new).
- Pattern source: `test_private_ingest_contradiction_surface.py` (ConflictRegistry integration).
- Uses the algorithm from §3.6.
- Asserts: closure commit whose scope has open conflicts + active batons but `deferred_or_open_items=[]` is rejected or flagged.

**Test 8.5 — Block-C-meets-Blocks-A-and-B integration.** `tests/test_closure_preserves_blocks_a_and_b.py` (new).
- Pattern source: `test_agent_loop_baton_present.py`, `test_agent_loop_block_b_present.py`.
- Asserts: closure operations don't modify baton lifecycle, reference load state, environment consult behavior, or core retrieval. Scorecard stays green.

### 6.2 — Reuse inventory

| Existing test file | Reusable pattern |
|---|---|
| `test_baton_requires_lifecycle_fields.py` | Shape validation at commit (required-field rejection) |
| `test_resolve_baton_soft_consume.py` | Audit-trail pattern (event ledger + state derivation) |
| `test_private_ingest_contradiction_surface.py` | ConflictRegistry integration in tests |
| `test_reference_load_boundary.py` | Whole-object commit + staleness-on-read |
| `test_environment_consult_boundary.py` | Evidence-class discipline (relevant for ratification class vocabulary) |
| `test_agent_loop_baton_present.py` / `test_agent_loop_block_b_present.py` | Runner-integration scaffolding |

No fixture entanglement with writeback tests (preconditions §10 preserved).

### 6.3 — Harness cost

Five tests, each ~130–180 LoC. Test 8.4 is the largest because it exercises the cross-signal mismatch-detection algorithm. Total estimated harness cost: ~750 LoC. Runtime under 5 seconds combined.

---

## 7. Findings — Block A + B inheritance + non-reopen check

### 7.1 — What Block C inherits wholesale

- `ProvenanceV1` with factory pattern — Block C adds `SOURCE_CLOSURE_COMMIT` (maybe `SOURCE_CLOSURE_RATIFICATION`), new factories.
- Open `memory_class` string field — might add `"closure"` if option (β) needs filtering, or stay clean if option (γ) uses ReferenceEntry's existing filter.
- `scope` dimension — closure is per-workspace (arcs span a workspace's work), probably not per-agent.
- Append-only ledger pattern (BatonLedger / ReferenceLoadLedger / EnvironmentEventLedger) — `ClosureLedger` is the natural extension.
- Narrow explicit writer pattern with envelope result codes.
- Default-lane exclusion pattern — `"closure"` extends the frozen set if needed.
- Rigidity sniff test.
- Nine-invariant scorecard regression rule.

### 7.2 — What Block C must not reopen

- **Block A decisions D.1, D.2, D.3** — baton placement, SessionLifecycleHook deferral, private-ingest contradiction wiring.
- **Block B decisions D.1, D.2, D.3, D.4** — new ReferenceStore, per-workspace environment, return-only consult, pack-declared loads.
- **Baton semantics, substrate payload shape, runtime slice v0.1** — unchanged.
- **`fabric.query` signature** — unchanged.
- **Writeback gate narrowness** — load-bearing per §2 of this analysis.
- **Nine-invariant scorecard** — stays green.
- **MCP surface** — no new tools for v0.1.
- **RESEARCH_ASSISTANT_PACK's `EMPTY_CONTRACT`** — untouched.

### 7.3 — RESEARCH_ASSISTANT_PACK promise preserved

The pack's `EMPTY_CONTRACT → swap-one-field` promise is about retrieval tool families, not about Block C. Closure commits don't touch the pack's contract field. The promise continues to hold.

---

## A. Block C fit decision

**Block C introduces a new memory class for closure objects, stored in a new `ClosureStore` (per-workspace), with its own ledger and its own provenance track. Block C does NOT extend `ReferenceStore`, does NOT reuse writeback paths, and does NOT modify Block A substrate or Block B retrieval.**

### A.1 Storage

- **New class:** `ClosureStore`, per-workspace, parallel to `ReferenceStore` and `EnvironmentStore`.
- **New `memory_class` value:** `"closure"`.
- **New provenance source types:** `SOURCE_CLOSURE_COMMIT` for commits; `SOURCE_CLOSURE_RATIFICATION` for ratification events; `SOURCE_CLOSURE_REVISION` for revisions.
- **New write_path:** `WRITE_CLOSURE_COMMIT` — structurally distinct from every existing writeback path.
- **New factories:** `for_closure_commit`, `for_closure_ratification`, `for_closure_revision` on `ProvenanceV1`.

### A.2 Lifecycle

- **`fabric.propose_closure(workspace_id, arc_name, scope, body_fields, metadata)`** — creates a proposal entity (not yet committed).
- **`fabric.ratify_closure(workspace_id, closure_id, ratifier)`** — appends a ratification event. Closure state derived from event stream.
- **`fabric.commit_closure(workspace_id, closure_id)`** — finalizes after ratification; produces durable versioned object.
- **`fabric.revise_closure(workspace_id, closure_id, revised_fields, ratifier)`** — produces new version; original preserved.
- **`ClosureLedger`** — per-workspace append-only JSONL. Event kinds: `proposed` / `ratified` / `committed` / `revised`.

### A.3 Integration surface

- **Default lanes:** `"closure"` added to the `memory_class` exclusion set at `fabric.query` merge point. Closure never appears in default retrieval.
- **`retrieval_assembler`:** No new block type in v0.1 (deferred to post-slice increment per option γ in §1.3). Closure is accessed via explicit `fabric.load_closure` (if/when added) or `fabric.list_closures` for admin purposes.
- **Runner:** unchanged. `AgentRunner.run_turn` does not know about closure.

### A.4 What Block C does NOT build

- No extension of `ReferenceStore` with closure fields (§10 guardrail).
- No reuse of `WRITE_COGNITION_WRITEBACK` or any writeback-adjacent path (§2 analysis).
- No closure-into-prompt via `retrieval_assembler` (deferred).
- No new `MemoryPlan` lane for closure.
- No runtime phase additions.
- No MCP tools.
- No task-residue first-class concept (D.5 — deferred to a later increment).
- No automated closure proposals from structural signals alone (R+7).
- No inferred / model-authored commits (R+9).

---

## B. Candidate acceptance criteria

Per preconditions §7: 3–5 concrete testable criteria. Single category (not a pair).

**AC-1 — Closure shape validation.** `fabric.propose_closure(...)` succeeds only when all §5-required fields are supplied. `deferred_or_open_items` missing → rejected specifically; empty list accepted. Missing any other required field → rejected with named result code. No partial-shape commits. *Test: 8.1.*

**AC-2 — Ratification is structural.** `fabric.commit_closure(...)` without a prior `fabric.ratify_closure(...)` ratification event in the ledger → rejected. Commit state is derivable from event stream; cannot be forged by setting a ratified flag directly on the object. *Test: 8.2.*

**AC-3 — Versioning is honest.** `fabric.revise_closure(...)` produces a new version (new `version_id`), stored alongside the original. Original closure reads as-before-revision. `version_history` list grows on each revision. No code path silently overwrites a prior version. *Test: 8.3.*

**AC-4 — Open-items honesty.** `fabric.commit_closure(...)` on a closure whose scope contains open `ConflictRegistry` conflicts or active batons, while `deferred_or_open_items` is empty → rejected or flagged for ratification review (design doc chooses the exact mechanism). *Test: 8.4.*

**AC-5 — Block A + B invariants preserved.** Closure operations do not modify baton lifecycle, reference load state, environment consult behavior, or core retrieval. Nine scorecard invariant tests remain green. `RESEARCH_ASSISTANT_PACK`'s `EMPTY_CONTRACT` untouched. *Test: 8.5 + CI scorecard run.*

---

## C. Candidate test plan

Five new test files. Unit-scope, expected combined runtime <6 seconds. No fixture entanglement with writeback.

| # | File | Covers | Reuses fixtures from |
|---|---|---|---|
| T1 | `tests/test_closure_shape_boundary.py` | AC-1 | `test_baton_requires_lifecycle_fields.py` |
| T2 | `tests/test_closure_ratification_required.py` | AC-2 | `test_reinforce_contract_invariant.py` |
| T3 | `tests/test_closure_versioning_honest.py` | AC-3 | `test_resolve_baton_soft_consume.py` |
| T4 | `tests/test_closure_open_items_honesty.py` | AC-4 | `test_private_ingest_contradiction_surface.py` |
| T5 | `tests/test_closure_preserves_blocks_a_and_b.py` | AC-5 | `test_agent_loop_block_b_present.py` |

**Scorecard regression requirement:** all nine scorecard invariants remain green. Same rule as Blocks A and B.

**No shared fixtures with writeback.** Explicitly verified per preconditions §10. Block C tests never import `test_writeback_recursion_guard.py` fixtures or any writeback-adjacent helpers.

---

## D. Genuine design blockers

Only questions that block design from starting.

### D.1 — Storage: option (β) vs (γ)

- **(β) New `ClosureStore`, no assembler integration in v0.1.** Closure is admin-accessible via `list_closures`, not prompt-context-integrable. Simplest.
- **(γ) New `ClosureStore` + new `BLOCK_CLOSURE` in retrieval_assembler.** Richer — the agent can load a past closure into prompt context — but adds a runtime-adjacent surface that needs its own review.

**Recommendation: (β).** (γ) can be a post-slice increment if needed. Keeping v0.1 out of assembler means no new block-type wiring, no profile percentages to rebalance, no additional runtime test coverage. The agent can still inspect closures via explicit admin/HTTP paths.

**Needs ratification before design starts.**

### D.2 — Ratification method placement: fabric or store?

- **(α) Fabric-level methods** — `fabric.propose_closure`, `fabric.ratify_closure`, `fabric.commit_closure`, `fabric.revise_closure`. Consistent with Block A / B method placement.
- **(β) Store methods called from thin fabric wrappers** — `ClosureStore.propose`, `ClosureStore.ratify`, etc. Mirrors `ConflictRegistry.decide` pattern.

**Recommendation: (α) fabric-level, with store methods called from them.** That matches the Block A / B pattern (baton fabric methods → graph store; reference fabric methods → ReferenceStore).

**Needs confirmation, not deep ratification.**

### D.3 — Arc scope definition

How does the caller declare which entries belong to an arc? Options:

- **(α) Explicit list of `eid`s** — caller provides the scope at propose time.
- **(β) Time-window + agent filter** — caller provides start / end timestamps; the system collects scope automatically.
- **(γ) Hybrid** — caller provides named arc identifier, system maintains arc-to-entries mapping over time (requires new tracking infrastructure).

**Recommendation: (α) for v0.1.** Explicit eid list puts the scope burden on the caller but avoids the need for arc-tracking infrastructure. Heuristic arc detection is a post-slice increment.

**Needs ratification before design starts.** This shapes the `propose_closure` signature.

### D.4 — Multi-scale support in v0.1

The roadmap §7 names four scales: cleanup arc / feature arc / stability window / release-level arc. Does v0.1 support all four, or start with one?

- **(α) All four at v0.1** — single `arc_kind` enum with four values. Implementation cost small; design cost small; but semantic clarity requires naming what differs between scales.
- **(β) One generic `arc_kind` field with free-form value in v0.1** — no enforced vocabulary. Design doc names the four kinds as recommended but doesn't constrain.
- **(γ) Only one scale in v0.1** (e.g., "feature_arc"), others deferred — narrower but cleaner proof of the pattern.

**Recommendation: (β).** Free-form `arc_kind` field (string) lets the four kinds exist as convention without being enforced vocabulary. This is the non-rigidification answer that matches the preconditions spirit (guide via required metadata, don't cage via closed enum). Adding a `VALID_ARC_KINDS` frozenset is a later ratification if the free-form value drifts.

**Needs ratification before design starts.**

### D.5 — Task residue: GAP named, not closed in v0.1

The roadmap §7 names task residues as arc-scope material. TORMENT currently has no first-class TaskList structure. Options:

- **(α) Block C adds a minimal TaskList primitive** — out of v0.1 scope per the preconditions "avoid adjacent architecture" discipline.
- **(β) Block C names the gap explicitly** — closure arc scope for v0.1 covers `ConflictRegistry` + active batons only; task residue acknowledged as a signal source that requires a future increment.

**Recommendation: (β).** Per §3.5 analysis. Name the gap, don't close it in v0.1.

**Needs confirmation, not deep ratification.**

### D.6 — NOT a blocker (surfaced for the record)

- **`memory_class="closure"` vs something else** — mechanical; "closure" is the obvious value.
- **Provenance source type names** — mechanical; pattern follows Block A / B extensions.
- **Ledger file path layout** — mechanical; follows Block A / B conventions.
- **Default-lane-exclusion filter extension** — one-line change.

---

## E. Boundary checks (required per preconditions)

Verified throughout this analysis:

- ✅ **No writeback collapse.** §2 analysis explicitly names and resists four collapse temptations. The design doc must pass the §2.3 five-point checklist.
- ✅ **No Block A substrate reopening.** Closure does not touch `fabric.ingest`, `memory_graph`, baton lifecycle, or substrate payload shape.
- ✅ **No Block B retrieval reopening.** Closure does not modify `ReferenceStore`, `EnvironmentStore`, `load`/`consult` primitives, or `retrieval_assembler` (in v0.1 per D.1 recommendation).
- ✅ **No runtime seam modification.** `AgentRunner` untouched; `FabricHandle` Protocol unchanged.
- ✅ **No automatic closure enactment.** R+7 honored by making ratification a separate recorded action.
- ✅ **No silent retrospective editing.** R+8 honored by version-not-overwrite discipline.
- ✅ **No LLM-authored commits.** R+9 honored by explicit ratifier identity; model assistance legitimate only in drafting.
- ✅ **`deferred_or_open_items` required.** R+10 honored at the shape-validation level.
- ✅ **No silent unresolved → canon.** R+11 honored by not auto-promoting contradiction-free scope material to canon as a closure side effect.

---

## F. Ratification record

**Ratification pass (2026-04-21, user + GPT):**

- [x] §1 Closure fit decision findings accepted (option (α) explicitly rejected; ClosureStore direction confirmed)
- [x] §2 Writeback-vs-closure separation probe accepted (five-point checklist for design doc)
- [x] §3 Open-items honesty mapping accepted (concrete evidence sources named)
- [x] §4 Ratification structural seam findings accepted
- [x] §5 Audience-ordering in code findings accepted
- [x] §6 Test anchor points accepted
- [x] §7 Block A + B inheritance + non-reopen check accepted
- [x] §A Fit decision accepted
- [x] §B Candidate acceptance criteria (AC-1 through AC-5) accepted
- [x] §C Candidate test plan (T1 – T5) accepted
- [x] §D Blockers resolved:
    - **D.1 → (β):** new `ClosureStore`, no `retrieval_assembler` integration in v0.1. Keeps Block C out of Block B retrieval mechanics; avoids prematurely inventing `BLOCK_CLOSURE`; keeps writeback-vs-closure guardrail sharper. Closure-loading can be added later as a separately ratified increment.
    - **D.2 → (α):** fabric-level methods (`propose_closure`, `ratify_closure`, `commit_closure`, `revise_closure`), backed by store/ledger helpers. Consistent with Blocks A and B.
    - **D.3 → (α):** explicit `eid` list for v0.1. Avoids hidden arc-detection machinery; makes closure scope auditable; keeps open-items honesty concrete; avoids time-window ambiguity and hybrid infrastructure creep.
    - **D.4 → (β):** free-form `arc_kind` in v0.1. Matches the guided-not-rigid discipline; avoids premature ontology cages; still allows the four roadmap scales to exist as convention.
    - **D.5 → (β):** task residue named gap, deferred. Trying to invent first-class task residue now would be adjacent-architecture creep. ConflictRegistry + active batons are sufficient for §8.4 in v0.1.

**Status:** **RATIFIED 2026-04-21 by user + GPT.** Block C design-doc phase is unblocked. Block C design is bound by the decisions frozen in this analysis.

### Carry-forward watch-item for Block C design phase

**Proposal / ratification / commit / revision are lifecycle stages, not four separate object ontologies.**

The analysis correctly keeps ratification structural, but the design must not accidentally create an overgrown taxonomy where each stage becomes a different incompatible object family. Keep one closure domain with:

- stored closure objects
- event-derived lifecycle state (derived from the ledger, not set as a direct field)
- version history
- separate ledger for the event stream

A single `ClosureEntry` class whose state field is event-derived is the right shape — **not** a `ClosureProposal` class, a `RatifiedClosure` class, a `CommittedClosure` class, and a `RevisedClosure` class all separately. The stages live in the ledger; the entry is one thing with a derived state.

If the design doc ever starts sprouting sibling classes for each stage, that is the drift this watch-item exists to catch.

---

## Appendix — file inventory touched during analysis

Read / re-read:
- `docs/PRE_BLOCK_C_PRECONDITIONS.md` (ratified preconditions — primary frame)
- `torment_service/provenance_v1.py` (existing writeback paths, factory patterns)
- `torment_service/reference_memory.py` (existing whole-object precedent)
- `torment_service/conflicts.py` (ratification-like pattern + open-items evidence)
- `torment_service/environment_memory.py` (evidence-class discipline pattern)

Grep-inventoried:
- Writeback-adjacent files: `WRITE_COGNITION_WRITEBACK` / `archivist_writeback` usage across `torment_service/`.
- "arc" / "closure" tokens across `torment_service/` — confirmed no pre-existing closure infrastructure.

Not touched (per preconditions §11):
- `docs/BLOCK_A_DESIGN.md`, `docs/BLOCK_B_DESIGN.md` — referenced, not re-analyzed.
- `torment_service/agent_loop.py`, `fabric.query`, `action_policy.py` — respected as frozen.
- `torment_service/mcp_server.py` — no MCP surface analysis.
