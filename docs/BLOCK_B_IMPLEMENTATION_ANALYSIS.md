# Block B Implementation Analysis — Pre-Design Phase

**Status:** **RATIFIED 2026-04-21** by user + GPT. All sections accepted; D.1/D.2/D.3/D.4 resolved. Block B may now move to its design-doc phase using this analysis as the immediate starting point.
**Date:** 2026-04-21
**Scope:** Code-grounded analysis mapping Block B's ratified preconditions onto the current codebase, before Block B design doc(s) are written.
**Precedents:**
- `docs/PRE_BLOCK_B_PRECONDITIONS.md` — ratified 2026-04-21. Gate on this work.
- `docs/BLOCK_A_DESIGN.md` — ratified 2026-04-19, merged 2026-04-21. The substrate Block B attaches to.
- `roadmap_tests/TORMENT_Memory_Roadmap_Regrouped.md` — Items 3 (reference) and 5 (environment).

> This document is analysis, not design. It inspects what the code already does, what is partially present, what is missing, and what would tempt collapse of the `load` / `consult` distinction. Block B owns two categories with different risk profiles; findings are flagged for each independently. The two carry-forward concerns from ratification (§4 collapse temptation; environment as higher-risk) are surfaced throughout, not folded into one conclusion.

---

## 1. Findings — reference memory fit

### 1.1 — The closest existing code: `ArchiveStore`

`torment_service/archive_memory.py` (`ArchiveStore`, 532 LoC) is the nearest structural precedent. It is **explicitly the "second lane"** in current TORMENT, separate from core identity memory:

- Own folder (`memory_archive/`), own JSONL (`documents.jsonl`, `chunks.jsonl`, `events.jsonl`), own embedding shards.
- Own boundary rule ("*Archive memory is a library, not a person*"): never enters the kernel, never creates motifs, never affects drift.
- Retrieval is pure cosine — no motifs, no gravity, no kernel physics.
- Has its own `ARCHIVE_MEMORY_CLASS = "archive"` constant.
- `delete_document`, `list_documents`, `get_chunks_for_document` — narrow object-level operations.

**This is structurally close to reference memory.** Both are coherent-external-object storage. But the semantic shape differs in ways Block B design cannot paper over:

| Concern | ArchiveStore | Reference memory (per roadmap) |
|---|---|---|
| Unit of retrieval | chunk (segmented from document) | whole coherent object |
| Retrieval primitive | cosine similarity | `load` (intentional, sustained) |
| Active-context state | none | loaded / unloaded (tracked) |
| Staleness handling | none | checked on load |
| Source linkage | `doc_id` + `chunk_id` | repo file / URL / artifact / snapshot |
| Unload semantics | n/a | scope-based, with manual override |
| Reason for existence | searchable library | *"whole matters beyond distilled parts"* |

### 1.2 — The reference-object test from the roadmap (§item 3)

> If I summarized this into atomic facts, would I lose something important?

Current ArchiveStore already passes this test for some uses — ratified plans or architecture docs, if ingested, become recoverable chunks. But chunk retrieval *loses the whole*. Block B's reference memory needs to preserve the whole, and that is a different retrieval semantic from ArchiveStore's.

### 1.3 — Retrieval assembler: `BLOCK_ARCHIVE` is already a citizen

`retrieval_assembler.py` has `BLOCK_ARCHIVE` as one of four prompt-context block types (identity / relational / situational / archive) with hard precedence: *"Archive is a library. Identity is the person. A library card does not overwrite who you are."* Reference memory, when loaded, is the right kind of citizen for this assembler — `BLOCK_REFERENCE` fits naturally.

**Important implication:** reference memory's `load` output DOES belong in prompt context (that's the whole point — the agent thinks *with* it). But this confirms a hard asymmetry with environment memory, which (per R+4) must NOT flow through this assembler. See §3.

### 1.4 — Promotion path from archive → core exists

`promotion.py` implements archive-chunk-to-core promotion via `PromotionResult` (canon flag, retrieval count, motif alignment, emotional salience, user approval). This is **adjacent to but not the same as** reference memory's concerns. Block B's reference memory does not need a promotion path — loading a reference is temporary elevation into reasoning context, not durable promotion.

**Risk surfaced by R+3:** any future code path that treats a loaded reference as "promote-eligible" re-opens the Block A writeback narrowness gate. The fix is structural: loaded references stay `memory_class="reference"`; promotion requires a separate explicit ingest with its own provenance.

### 1.5 — Fit decision (reference)

Reference memory **cannot be implemented as a lane filter on ArchiveStore**. The retrieval semantic is different. Two viable shapes:

- **(α) New `ReferenceStore` class** — parallel to `ArchiveStore`, own folder, own retrieval path, own load/unload state tracking. Clean structural separation.
- **(β) Extended `ArchiveStore`** — add whole-object retrieval, load state, staleness tracking on top of existing archive storage.

**Recommendation: (α).** The roadmap explicitly distinguishes reference (whole-object load) from archive (searchable library), and the existing ArchiveStore boundary rule (*"Archive is a library, not a person"*) implies a separable layer. Keeping them separate prevents silent blur. This is D.1.

### 1.6 — Rigidity sniff test (reference)

Proposed reference boundaries are:
- Required `source_link` at ingest (what document/URL/artifact is this)
- Required `source_kind` (document / url / internal / generated)
- Staleness check on load (not a restriction on content; a metadata check)
- Load/unload state (lifecycle, not quality)

All are **metadata the agent provides alongside expression**, not restrictions on what the agent can say or load. ✅ Passed.

---

## 2. Findings — environment memory fit (HIGHER RISK)

### 2.1 — The headline: environment memory is net-new

`grep` across `torment_service/` for environment-memory-shaped code found no existing system. The closest things are:

- `config_view.py` — read-only introspection of env vars + profile defaults. NOT memory (not persisted, not learned, not per-agent).
- `profiles.py` — four hardcoded config presets (`companion`, `minimalist`, `assistant`, `hive`) that set env var defaults. NOT memory.
- Scattered `os.environ.get(...)` calls across fabric, kernel, MCP — ad-hoc config reads. NOT memory.
- `request_context.py` — caller identity + trust tier, NOT environmental state.

**No existing environment-memory system means Block B introduces the category fresh.** There is no collapse-with-existing-code risk for environment memory. But per GPT's carry-forward concern 2, this is exactly *why* environment memory is the higher-risk category — there's no precedent to inherit structural boundaries from, and all the design choices are load-bearing.

### 2.2 — R+5 evidence discipline is the load-bearing constraint

The regrouped roadmap names three ownership/evidence classes: agent-observed, system-probed, user-asserted. R+5 formalizes these as the **only** valid write paths:

- **User assertion** — explicit user statement converted to an environment entry.
- **Observable system/runtime evidence** — direct probe produced a concrete observation.
- **Ratified inference path** — marked `inferred=True` in provenance; the inference rule itself must be in-doctrine.

**Implication for design:** environment-memory ingest must validate `evidence_class` at write-time, same way baton validates `owner` / `expires_when` / `resolution_condition`. Missing or invalid → reject, same failure-mode pattern as baton validation (fabric.py pattern already established by Block A).

**Concrete risk:** the temptation during design will be to allow "inferred" as a soft default for things the system guesses from indirect signals. R+5 forbids this. The design doc must name the specific ratified inference rules (if any) and mark everything else as requiring user assertion or observable probing.

### 2.3 — Probe-on-fail pattern — where would it live?

The roadmap describes a self-healing pattern: action fails in a way consistent with an environment quirk → system probes relevant environment memory → if none exists, creates or updates one from the failure pattern. This is attractive but high-risk because it looks like automated memory writing.

**Observations from the current code:**
- `fabric.py::ingest` line 2487-2491 already has tool-result lifecycle capping (half-life capped at 7 days for `source_type=="tool_result"`) — this is a precedent for "tool-observable state as memory." But it's tool-observation, not environment-state probing.
- `incident_log.py` exists for recording incidents (not memory in the substrate sense, but an audit trail) — could be the insertion point where probe-on-fail triggers an environment write.
- The runtime slice's `enter_reflex` (agent_loop.py) is the existing pattern for "synthetic observation triggers a turn" — environment probe-on-fail could reuse this shape, but the turn it triggers must route environment writes through the three-evidence-class path, NOT through ordinary ingest.

**Recommendation for design:** probe-on-fail is a distinct write path in Block B, not ordinary ingest. The probe itself (what was observed when the action failed) becomes the observable evidence; the resulting environment entry is `evidence_class="system_probe"`. Do NOT let probe-on-fail become "LLM guesses what went wrong" — that's exactly the failure mode R+5 exists to prevent.

### 2.4 — Consult flow — where does it go?

R+4: environment memory must NOT auto-inject into LLM context. Environment is always consultable, never always loaded.

**Where can a consult result go instead?**
- **Action-policy gates** — if a consult reveals "the sandbox has no network," `action_policy.apply_tool_narrowing` could narrow away network-dependent tool families. This is how environment memory would actually *shape behavior* without being in the prompt.
- **Drift checks and stabilization** — environment context may inform drift thresholds or reflex triggers. Block A's stabilization program runs without LLM calls; environment memory could provide inputs.
- **Tool-executor defaults** — when a tool runs, environment memory could inform default arguments (timeout, sandbox scope, etc.) without the LLM seeing the full environment state.

**Open design question (D.3):** does Block B wire consult into any of these, or does consult just return a result and callers decide? Recommendation: **return-and-let-callers-decide**. Wiring consult into `action_policy` would touch the runtime seam Block A froze. Block B should add the consult primitive; later runtime increments can wire specific consult→policy paths if ratified.

### 2.5 — Fit decision (environment)

Environment memory is **net-new**, structurally distinct from everything in the current codebase. It needs:

- **New `EnvironmentStore` class** — per-workspace (not per-agent), own folder, own JSONL, own scope-tag vocabulary.
- **New write paths per evidence class** — three factories: `for_environment_user_assertion`, `for_environment_observed`, `for_environment_inferred`.
- **New `consult` method** — `consult(operation, scope)` returning relevance-filtered facts, NOT auto-injecting.
- **New scope-tag discipline** — `target_runtime`, `scope_tag`, `last_observed` required fields (per roadmap §item 5).
- **No integration with retrieval_assembler** — environment facts do not flow into prompt blocks.

**This is more surface than reference memory.** Expected; environment is the higher-risk category and needs more structural scaffolding per R+5.

### 2.6 — Rigidity sniff test (environment)

Proposed environment boundaries are:
- Required `target_runtime` / `scope_tag` / `last_observed` (scope metadata, not expression restriction)
- Required `evidence_class ∈ {user_assertion, observed, inferred}` with `inferred` requiring an explicit ratified rule
- `always consultable, never auto-injected` is retrieval behavior, not content restriction
- Probe-on-fail produces a new entry with explicit provenance, never overwrites silently

All boundaries are **required metadata alongside expression**, not restrictions on what operational facts can be recorded. ✅ Passed.

**Highest-risk watch-item for design review:** any path where "inferred" becomes a silent default, any scoring mechanism that makes inferred facts behave identically to observed facts, any LLM-call that returns "environment state" as a freeform string. All of these should be actively challenged during design.

---

## 3. Findings — retrieval primitive seam + collapse-temptation probe

Per GPT's carry-forward concern 1. The preconditions require `load` and `consult` to stay visibly distinct in code; this section names the specific **temptation points** where the current codebase could absorb them into a generic interface.

### 3.1 — Temptation point 1: `retrieval_assembler.py`

The assembler unifies four block types into a single `AssembledContext` object. Adding reference as `BLOCK_REFERENCE` is coherent because reference is prompt-bound when loaded.

**The collapse risk:** a future design iteration might also add `BLOCK_ENVIRONMENT`, making the assembler the single path for "all memory reaches the prompt." That would silently violate R+4. The Block B design doc must **explicitly exclude** environment memory from the assembler.

### 3.2 — Temptation point 2: `MemoryPlan` lanes

`MemoryPlan` currently exposes lane flags: `retrieve_core / retrieve_archive / retrieve_deep / retrieve_relational / retrieve_collective / retrieve_character_state / retrieve_srg_state`. A `retrieve_reference` lane is structurally tempting but problematic because:

- It implies reference is symmetric with core/archive (it isn't; it has load state).
- It pushes reference-memory activation into every pack declaration.
- It makes reference retrieval implicit — opposite to the *intentional, sustained, reasoning-oriented* semantics.

**Block B design should NOT add reference or environment as `MemoryPlan` lanes.** Both get explicit methods (`load`, `unload`, `consult`) accessed by the pack or caller when needed. This keeps the §4 non-substitutability commitment visible.

### 3.3 — Temptation point 3: `fabric.query`

`fabric.query` is the generic retrieval entry point for core + archive + deep. It has `memory_plan` as a parameter and returns a unified `results` list. A future temptation would be to add `include_reference=True` and `include_environment=True` as query parameters, merging Block B retrieval into `fabric.query`.

**Block B design should NOT extend `fabric.query` to include reference or environment.** Separate methods preserve the distinct retrieval primitives:
- `fabric.load_reference(ref_id, scope)` / `fabric.unload_reference(load_id)`
- `fabric.consult_environment(operation, scope)`

Each has its own envelope shape. None returns the same-shaped `results` list `fabric.query` returns.

### 3.4 — Temptation point 4: baton's `list_active_batons` pattern

Block A added `fabric.list_active_batons` as the explicit lifecycle-aware retrieval path. It's tempting to copy this directly for reference/environment: `list_active_references`, `list_environment_by_scope`. That's fine as a **pattern**, but must not become "baton, reference, and environment all work the same way" — they don't. Baton is per-agent lifecycle; reference is intentional-load; environment is action-site consult. Copying only the narrow-explicit-method shape from baton is in-bounds; copying the list semantics wholesale is not.

### 3.5 — Summary: the three retrieval primitives in Block B

| Primitive | Returns | Flows into | Triggered by |
|---|---|---|---|
| `load(ref_id, scope)` | a coherent reference object marked as loaded | `retrieval_assembler` as `BLOCK_REFERENCE` | agent / pack / user request |
| `unload(load_id)` | status envelope; object removed from active context | — (removes from assembler) | scope conclusion or explicit call |
| `consult(operation, scope)` | relevance-filtered environment facts for this operation | **nowhere automatically**; caller decides | action-site code, policy gates, failure-recovery code |

**The assembler sees `load` outputs. It never sees `consult` outputs.** This is the cleanest expression of the non-substitutability.

---

## 4. Findings — test anchor points

### 4.1 — Mapping §6 to real locations

**Test 6.1 (reference-memory boundary):** new — `tests/test_reference_load_boundary.py`.
- Pattern source: `test_baton_requires_lifecycle_fields.py` (validation-at-ingest pattern).
- Fixtures: real `TormentFabric` with tempdir + hash embedder.
- Asserts: `load` on non-reference entry returns mismatch result; loaded objects reachable via `load` path but not via Block A default lanes; reference content never silently becomes core/baton on subsequent write.

**Test 6.2 (environment-memory boundary):** new — `tests/test_environment_consult_boundary.py`.
- Pattern source: new ground; closest precedent is `test_baton_requires_lifecycle_fields.py` for write-validation and `test_reinforce_contract_invariant.py` for envelope pattern.
- Fixtures: real `TormentFabric` with tempdir + hash embedder; a small fake "environment probe" for observable-evidence path.
- Asserts: `consult` returns only relevance-filtered facts; write without one of R+5's three evidence classes is rejected; environment entries never surface in `fabric.query` results; environment facts never auto-inject into any assembler output.

**Test 6.3 (retrieval-primitive distinctness):** new — `tests/test_block_b_primitives_not_substitutable.py`.
- Pattern source: new; cleanest design is a directly-written test that invokes `load` on environment and `consult` on reference and asserts mismatch-result in both directions.
- Asserts: primitive-on-wrong-category produces a specific mismatch result (exception, `ok=False` envelope, or named result code — mechanism-neutral per §6.3 ratified wording).

**Test 6.4 (Block-B-meets-Block-A integration):** extend — reuses `test_agent_loop_baton_present.py` pattern.
- Pattern source: `test_agent_loop_baton_present.py`.
- Asserts: `AgentRunner.run_turn` still completes end-to-end with reference loads and environment entries present; baton retrieval unaffected; Block A substrate retrieval unaffected; nine-invariant scorecard stays green.

### 4.2 — Reuse inventory

| Existing test file | What Block B can reuse |
|---|---|
| `test_baton_requires_lifecycle_fields.py` | Validation-at-ingest pattern (missing-field → rejected) |
| `test_reinforce_contract_invariant.py` | Envelope shape (`ok` / `result_code` / data) |
| `test_baton_not_in_default_lanes.py` | Lane-exclusion assertion pattern (hard filter, not down-rank) |
| `test_resolve_baton_soft_consume.py` | Idempotency + audit-trail pattern (for reference load state and unload idempotency) |
| `test_agent_loop_baton_present.py` | FakeFabric + AgentRunner integration pattern |
| `test_provenance_v1_admission.py` | ProvenanceV1 factory + validation tests |

### 4.3 — Fixture entanglement check

No existing tests couple Block B material with writeback or closure code (there's no closure code yet). §7 of the preconditions stays clean. Block B tests should not introduce any fixture that would later be reused by closure tests.

### 4.4 — Harness cost

Expected test sizes, each ~100–150 LoC:
- 6.1 reference boundary: ~130 LoC
- 6.2 environment boundary: ~150 LoC (more cases due to three evidence classes)
- 6.3 primitive distinctness: ~80 LoC (tight, focused)
- 6.4 Block-B-meets-Block-A integration: ~120 LoC

Combined runtime expected < 5 seconds. No new harness infrastructure beyond a small "fake environment probe" helper for 6.2.

---

## 5. Findings — Block A inheritance + non-reopen check

### 5.1 — What Block B inherits wholesale

- **`ProvenanceV1`** — Block B adds new source types: `SOURCE_REFERENCE_LOAD` (for reference loads), `SOURCE_ENVIRONMENT_OBSERVED` / `SOURCE_ENVIRONMENT_USER_ASSERTED` / `SOURCE_ENVIRONMENT_INFERRED` (per R+5). All follow the `for_*` factory pattern established by Block A.
- **`memory_class`** — new values `"reference"` and `"environment"`. The open string field handles this cleanly; no enum to modify.
- **Scope dimension** — reference is likely private-scope (like baton); environment is per-workspace (shared across agents but not across workspaces). This is D.2.
- **`BatonLedger` pattern** — reference memory may want a `ReferenceLoadLedger` (load/unload audit). Environment memory probably wants an `EnvironmentEventLedger` (probe / assertion / inference audit).
- **Reinforce-style envelope** — `{ok, result_code, ...}` with named result codes for each operation.
- **Default-lane-exclusion pattern** — reference and environment entries must be filtered out of Block A default `MemoryPlan` lanes, same `memory_class != "..."` hard-filter approach.
- **Rigidity sniff test** — every Block B boundary is metadata-required, not expression-restricted.

### 5.2 — What Block B must not reopen

- **D.1 / D.2 / D.3 from Block A** — baton placement, SessionLifecycleHook deferral, private-ingest contradiction wiring. All frozen.
- **Baton semantics** — Block B does not add fields to baton entries, does not change baton retrieval, does not touch `resolve_baton`.
- **Substrate payload shape** — `memory_graph.spawn_memory` and its payload structure remain unchanged.
- **Runtime slice v0.1** — no new phases, no `AgentRunner.run_turn` changes, no `SessionLifecycleHook` wiring.
- **MCP surface** — no new MCP tools. Any admin/developer access to reference or environment memory goes through HTTP or internal APIs until a later increment ratifies MCP exposure.
- **Writeback gate narrowness** — especially important for reference memory (loading is not writeback; any path that looks like "loading to substrate" must be actively rejected).
- **Nine-invariant scorecard** — all tests stay green.

### 5.3 — RESEARCH_ASSISTANT_PACK's promise is preserved

The pack declares `action_contract=EMPTY_CONTRACT` with a comment: *"When a retrieval family lands in a later increment, ONLY this field needs to change."*

**Block B is not "the retrieval family" the pack was waiting for.** The pack expects a *tool family* for retrieval (e.g., `read_file`, `web_fetch`) that the LLM can invoke via the action contract. Block B's `load` / `consult` are **internal methods**, not tool families, not LLM-visible.

When a tool family eventually lands (v0.1.1+ or later), it might *use* Block B's load internally — but that's integration work for that future increment, not Block B's concern. The pack's swap-one-field promise continues to hold: when a retrieval tool family is declared, the pack swaps its `action_contract` field. Block B doesn't change that promise and doesn't substitute for it.

### 5.4 — Block A landed state verified (quick check)

- `memory_class` field is open string: ✓ (per `memory_graph.py::spawn_memory`)
- `ProvenanceV1` factory pattern extensible: ✓ (per Block A's `for_baton_ingest` addition)
- Baton lane-exclusion filter already in place at `fabric.query` merge point: ✓ (Block B adds reference/environment to the same filter)
- `BatonLedger` as per-agent JSONL audit: ✓ (Block B can model `ReferenceLoadLedger` / `EnvironmentEventLedger` on it)
- Runtime seam (Phase 7 ingest via 4-arg `FabricHandle.ingest`) unchanged: ✓ (Block B does not touch this)
- RESEARCH_ASSISTANT_PACK with EMPTY_CONTRACT still in `behavior_packs.py`: ✓ (Block B does not modify it)

---

## A. Block B fit decision

**Block B extends the current codebase with two net-new stored-but-not-foregrounded memory classes, each with its own retrieval primitive and its own storage structure. Block B does NOT extend `ArchiveStore`, does NOT add new MemoryPlan lanes, and does NOT touch `fabric.query`.**

### A.1 Reference memory

- New class: `ReferenceStore` (parallel to `ArchiveStore`, lives in own folder).
- New memory_class value: `"reference"`.
- New provenance source type: `SOURCE_REFERENCE_LOAD`.
- New factory: `ProvenanceV1.for_reference_load`.
- New retrieval primitive: `load(ref_id, scope) / unload(load_id)` — returns coherent reference objects with tracked load state.
- Integration: loaded references flow into `retrieval_assembler` as `BLOCK_REFERENCE` (new block type).
- Retrieval guard: reference entries filtered out of Block A default lanes same as baton.
- Audit ledger: new `ReferenceLoadLedger` per-agent (same JSONL pattern as `BatonLedger`).

### A.2 Environment memory

- New class: `EnvironmentStore` (net-new — no existing precedent in TORMENT).
- New memory_class value: `"environment"`.
- New provenance source types: `SOURCE_ENVIRONMENT_OBSERVED`, `SOURCE_ENVIRONMENT_USER_ASSERTED`, `SOURCE_ENVIRONMENT_INFERRED`.
- New factories, one per evidence class; `for_environment_inferred` requires an `inference_rule` field identifying the ratified rule that produced the entry.
- New retrieval primitive: `consult(operation, scope)` — returns relevance-filtered facts; does NOT flow through `retrieval_assembler`.
- Retrieval guard: environment entries NEVER appear in `retrieval_assembler` output, regardless of block budget.
- Audit ledger: new `EnvironmentEventLedger` per-workspace (broader scope than per-agent; environment is shared across agents in a workspace).
- Probe-on-fail: a distinct write path that routes through `for_environment_observed` only; never via LLM-guess.

### A.3 What Block B does NOT build

- No extension of `ArchiveStore` (reference is its own store).
- No new `MemoryPlan` lane flags (reference and environment have explicit methods instead).
- No changes to `fabric.query` (it remains core + archive + deep).
- No runtime phase additions (load/consult are called by packs/callers, not by `AgentRunner.run_turn`).
- No MCP tools for reference or environment (admin-only via HTTP for v0.1).
- No closure-related fields on reference entries.
- No changes to baton, core, or archive semantics.

---

## B. Candidate acceptance criteria

Per preconditions §5: 3–5 per category, not merged. These are drawn from the analysis findings above.

### B.1 — Reference memory (four criteria)

**B.1-AC1 — Reference load requires source linkage.**
`fabric.load_reference(ref_id, scope, source_link, source_kind)` succeeds when `source_link` and `source_kind` are supplied; missing either → mismatch result (§6.3-style envelope), no load created. *Test: T1 reference-boundary (§6.1).*

**B.1-AC2 — Staleness is checked on load, not on write.**
Loading a reference whose source has changed since last load → load succeeds but the envelope carries `stale=True`; loading a reference whose source is unchanged → `stale=False`. Staleness is not checked at arbitrary intervals. *Test: T1 reference-boundary.*

**B.1-AC3 — Loaded references never silently become durable.**
After a reference is loaded, no code path silently creates a `core` or `baton` substrate entry for its content. Promotion-to-durable requires a separate explicit ingest with `parent_eids` linking to the reference. *Test: T1 + T4 integration.*

**B.1-AC4 — Loaded references are invisible to Block A default lanes.**
A `fabric.query(...)` call with any combination of `retrieve_core / retrieve_archive / retrieve_deep / retrieve_relational` returns zero reference EIDs, even when content embeddings match. Reference content is only reachable via the `load` path. *Test: T1 + T4.*

### B.2 — Environment memory (five criteria)

**B.2-AC1 — Environment writes require one of three evidence classes.**
`fabric.write_environment(...)` without `evidence_class ∈ {user_asserted, observed, inferred}` → rejected; `evidence_class="inferred"` without a declared `inference_rule` → rejected. *Test: T2 environment-boundary (§6.2).*

**B.2-AC2 — Consult is relevance-filtered.**
`fabric.consult_environment(operation, scope)` returns only entries whose `scope_tag` matches the requested scope and whose content is relevant to the operation. Unrelated environment facts never appear in the result. *Test: T2.*

**B.2-AC3 — Environment facts never auto-inject into prompt context.**
Running `AgentRunner.run_turn` with environment entries present produces a `retrieval_assembler` output that contains no environment content, regardless of similarity, scope, or recency. *Test: T2 + T4.*

**B.2-AC4 — Probe-on-fail produces explicit observed provenance.**
The probe-on-fail path produces an environment entry with `evidence_class="observed"` and a populated `observation_source` field naming the system probe that produced the observation. No LLM-generated content reaches environment memory via probe-on-fail. *Test: T2.*

**B.2-AC5 — Inferred entries declare themselves.**
An entry with `evidence_class="inferred"` has `inferred=True` visibly in its payload and audit trail, so downstream code can filter/weight inferred vs observed differently. *Test: T2 + T4.*

### B.3 — Shared (both categories)

**B.3-AC1 — Primitive non-substitutability.**
`load(x)` on an environment memory entry and `consult(x)` on a reference entry each produce a specific mismatch result naming the primitive/category error. Neither call silently succeeds, silently returns empty, or coerces to the other primitive. *Test: T3 (§6.3).*

**B.3-AC2 — Block A invariants preserved.**
All nine scorecard invariant tests remain green with reference and environment entries present. Baton retrieval, core retrieval, and archive retrieval are unaffected. *Test: T4 + CI scorecard run.*

---

## C. Candidate test plan

Four new tests per preconditions §6, plus a shared distinctness test. All unit-scope, expected combined runtime < 5 seconds.

| # | File | Covers | Reuses fixtures from |
|---|---|---|---|
| T1 | `tests/test_reference_load_boundary.py` | B.1-AC1 through B.1-AC4 | `test_baton_requires_lifecycle_fields.py` |
| T2 | `tests/test_environment_consult_boundary.py` | B.2-AC1 through B.2-AC5 | `test_baton_requires_lifecycle_fields.py` + `test_reinforce_contract_invariant.py` |
| T3 | `tests/test_block_b_primitives_not_substitutable.py` | B.3-AC1 | new pattern, tightly-scoped |
| T4 | `tests/test_agent_loop_block_b_present.py` | B.3-AC2 + integration aspects of B.1/B.2 | `test_agent_loop_baton_present.py` |

No fixture sharing with writeback or closure. No new harness infrastructure needed beyond a small fake environment-probe helper for T2.

---

## D. Genuine design blockers

Only questions that truly block design-doc work from starting.

### D.1 — Reference memory: new `ReferenceStore` vs extended `ArchiveStore`?

**Recommendation: new `ReferenceStore`.** Separate class, own folder, own retrieval path. Rationale in §1.5. Keeping archive-chunks and reference-whole-objects in the same class would blur the "whole matters beyond distilled parts" property the roadmap specifically names.

**Alternative (β) — extending `ArchiveStore`** — technically viable, reuses more code. Reduces LOC. But risks gradual drift where reference operations borrow archive assumptions that don't fit (e.g., archive's delete semantics vs reference's unload semantics).

**Needs ratification before design starts.**

### D.2 — Environment memory scope: per-workspace or per-agent?

Environment memory describes operational context of the **machine / runtime / container** the agent is acting inside of. These facts are usually shared across agents in the same workspace (e.g., "this sandbox has no network," "the python version is 3.10"). Per-agent environment would silo these and require redundant re-probing.

**Recommendation: per-workspace.** Environment facts live at the workspace level, with each entry carrying `ownership ∈ {agent, system, user}`. An agent-observed fact still belongs in the workspace pool; its ownership field records who observed it.

**Alternative (β) — per-agent** — narrower, safer-by-default, but leads to redundant probing and doesn't match the real shape of environment context.

**Needs ratification before design starts.**

### D.3 — Consult output flow: wired into action_policy or return-only?

When `consult_environment(operation, scope)` returns "this sandbox has no network," something has to use that fact to actually narrow behavior. Two shapes:

- **(α) Return-only.** `consult` returns a result; the caller (pack, runner extension, policy gate) decides what to do with it. Block B adds no wiring to `action_policy`.
- **(β) Wire consult into action_policy.** During `apply_tool_narrowing`, the policy calls `consult_environment` and narrows tool families based on the result.

**Recommendation: (α).** Wiring `consult` into `action_policy` would modify the runtime seam Block A froze, and would require its own scorecard-regression check. Keeping consult as a return-only primitive preserves the Block-B-vs-runtime boundary; any later increment can ratify wiring specific consult paths into policy as a separate runtime-doctrine amendment.

**Needs ratification before design starts.**

### D.4 — Reference memory in `AgentRunner`: loaded before Phase 3 or not at all?

Reference memory, when loaded, belongs in prompt context. But *who loads it and when?*

- **(α) Load pre-Phase-3, at runner level.** A new runner hook loads references declared by the active pack before the controller's aperture runs. Substrate retrieval happens on top of already-loaded references.
- **(β) Load via explicit pack or external caller.** The runner doesn't know about references. Packs (or external callers) call `fabric.load_reference` explicitly and store the load handle; when `retrieval_assembler` assembles prompt context, it includes active loads via a new `BLOCK_REFERENCE` block.
- **(γ) Defer runner integration entirely.** Block B adds `load` / `unload` as fabric methods only; `retrieval_assembler` does not know about reference blocks. Prompt integration is a later increment.

**Recommendation: (β).** Packs are already the right place to declare "this situation wants reference X loaded," and `retrieval_assembler` already has a block-type abstraction. The runner stays untouched (frozen per Block A).

**(α) is tempting but touches the runner — same runtime-seam concern as D.3.
(γ) defers too much — reference memory without prompt integration is a half-feature.

**Needs ratification before design starts.**

### D.5 — NOT a blocker (surfaced for the record)

- **`memory_class` values for Block B.** `"reference"` and `"environment"` are the obvious choices; open string field handles them; no enum modification needed.
- **Provenance source types.** Four new constants (`SOURCE_REFERENCE_LOAD`, three environment variants). Purely additive; no Block A impact.
- **Ledger patterns.** `ReferenceLoadLedger` and `EnvironmentEventLedger` follow the `BatonLedger` template exactly; mechanical extension.
- **Default-lane exclusion.** The filter in `fabric.query` that excludes baton can be extended to also exclude `"reference"` and `"environment"` — one-line change per category.

These are design details to resolve during Block B design, but they don't block it from starting.

---

## E. Boundary checks (required per ratified preconditions §4 and preconditions §8)

Verified throughout this analysis:

- ✅ **No re-opened closed gates.** Writeback stays narrow (R+3 prevents reference load from widening it). Baton semantics untouched. Runtime seam frozen. RESEARCH_ASSISTANT_PACK promise preserved (§5.3).
- ✅ **No Block B absorbed into Block A or Block C.** Reference is not a substrate class; environment is not baton; neither is closure material.
- ✅ **No redesign of Block A.** Block A substrate continues to work as landed in main.
- ✅ **No `load` / `consult` collapse temptation ignored.** §3 names three specific temptation points and the design-level resolution for each.
- ✅ **Environment memory treated as higher-risk.** §2 is longer and more constraint-focused than §1, reflecting R+5's load-bearing role.
- ✅ **Rigidity sniff test applied per category.** Every proposed Block B boundary is required-metadata-alongside-expression, not expression-restriction.

---

## F. Ratification record

**Ratification pass (2026-04-21, user + GPT):**

- [x] §1 Reference memory findings accepted
- [x] §2 Environment memory findings (higher-risk pass) accepted
- [x] §3 Retrieval-primitive collapse-temptation probe accepted
- [x] §4 Test anchor points accepted
- [x] §5 Block A inheritance + non-reopen check accepted
- [x] §A Fit decision accepted
- [x] §B Candidate acceptance criteria (B.1 × 4, B.2 × 5, B.3 × 2) accepted
- [x] §C Candidate test plan (T1–T4) accepted
- [x] §D Blockers resolved:
    - **D.1 → (α):** new `ReferenceStore`. Archive is a searchable library; reference is a coherent object intentionally loaded as a whole. Extending `ArchiveStore` would almost certainly cause semantic blur later.
    - **D.2 → (α):** per-workspace environment memory, with ownership field. Environment context is mostly shared across agents in a workspace; per-agent would create unnecessary duplication and inconsistent operational truth. Ownership field preserves provenance differentiation.
    - **D.3 → (α):** return-only consult. Preserves the frozen runtime seam; keeps Block B storage/retrieval distinct from runtime-policy wiring; leaves later `consult`→policy integration as explicit future ratification.
    - **D.4 → (β):** pack-declared / external-caller load, `retrieval_assembler` includes active loads, runner untouched. Keeps the runner frozen while giving reference memory actual utility now.

**Status:** **RATIFIED 2026-04-21 by user + GPT.** Block B design-doc phase is unblocked. Block B design is bound by the decisions frozen in this analysis.

### Carry-forward design cautions

Two cautions surfaced during ratification for the design phase to preserve:

1. **Provenance must distinguish "reference object as stored" from "act of loading it."** Do not let *loadedness* become part of object identity. The stored reference has a durable identity; each load/unload is an event in its lifecycle, captured separately (likely via a load ledger). Design must not conflate the two.

2. **Environment: entry identity must stay separate from consult result shape.** An environment entry has its own persistent identity and provenance; a `consult` call returns a *view* over relevant entries, not the entries themselves. Design must not collapse these — the consult result shape should be explicitly different from the entry shape.

---

## Appendix — file inventory touched during analysis

Read in full:
- `docs/PRE_BLOCK_B_PRECONDITIONS.md` (ratified preconditions)
- `torment_service/archive_memory.py` (532 LoC — reference-memory precedent)
- `torment_service/request_context.py` (174 LoC — confirmed NOT environment-adjacent; it's auth)
- `torment_service/config_view.py` (132 LoC — confirmed read-only env introspection, NOT memory)
- `torment_service/profiles.py` (104 LoC — confirmed config presets, NOT memory)

Read strategically:
- `torment_service/retrieval_assembler.py` (552 LoC; read top ~150 lines for block types + precedence)

Inventory probed (greps):
- `environment|runtime_info|system_probe|probe_on_fail|operational_context` across `torment_service/` — confirmed no existing environment-memory system.
- `def load|def unload|def consult|staleness|source_link` — confirmed no existing load/consult/staleness patterns in TORMENT's memory layer.

No code modified. No files touched outside `docs/`. Analysis only.
