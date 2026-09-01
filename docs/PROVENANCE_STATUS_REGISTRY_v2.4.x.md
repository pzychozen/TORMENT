# PROVENANCE STATUS REGISTRY — v2.4.x

**Status:** step 3 of the v2.4.x tactical provenance pass.
**Landed after:** steps 1 and 2 (docstring rule pin fix, `legacy_string` elimination).
**Precedes:** step 4 (`SOURCE_COLLECTIVE_ECHO` safe-parent asymmetry decision),
step 5 (graph-walk recursion guard rewrite), step 6 (migration tooling),
step 7 (chain-vs-replace reintegration decision).

## 1. Purpose

This document is an audit artifact, not a design document. It answers a single
question for every declared provenance constant: **is there code that produces
this, is there code that expects to produce it, or is it neither?** Every row
is pinned to a live producer call site or to the absence of one.

The registry pattern is borrowed from the December 2025 trigger registry memo
in `pdfs/Trigger_Registry.pdf`, which codified the rule:
"Dynamics → Observables → Triggers → Diagnostics / Labels. Reverse influence
forbidden by default." Applied to provenance, the analogous rule is:
**write paths produce source types; source types influence writeback gates;
writeback gates must not silently widen based on reader-side normalization.**

**See also:** `PROVENANCE_DOCTRINE_v2.4.x.md` — compact derivation helpers,
read-surface invariants, truth table, and surface map. That document covers
*how provenance is derived and presented*; this registry covers *what each
declared constant means and which write paths produce it*.

## 2. Doctrine and recursion-safety anchors

This registry is governed by the following invariants. Every row below is
readable through these lenses.

- **Doctrine rule #5 (`DOCTRINE_v2.4.x.md`)** — *Provenance is a hard boundary.
  Anything that writes back into memory from cognition, tools, or derived
  processes must carry real provenance through ingest. No provenance,
  no self-writing.*
- **Doctrine rule #2** — *Memory is the epistemic core. Improve memory
  selection before redesigning memory itself.* (Applied below to block
  activation of `SOURCE_DERIVED` until the chain-vs-replace decision.)
- **RSP Rule B (`RECURSION_SAFETY_POLICY_v2.4.x.md`)** — safe parent
  source_type set is `{user_input, tool_result, memory (migrated/imported)}`.
- **RSP Rule A / E** — archivist-origin parents are blocked from writeback.
- **RSP Rule F** — no laundering through ancestor chains. Not currently
  enforceable by the one-hop guard; step 5 scope.
- **Invariant G (`AGENT_SPINE_PLAN.md`)** — low-trust derived material cannot
  overwrite high-trust source memory.

## 3. Two layers, two vocabularies

There are two provenance classes in this codebase. They are at different
abstraction levels and must not be confused:

- **Spine layer** — `schemas/provenance.py::Provenance`. Attached to role
  outputs and proposals flowing through the cognition pipeline. Tracks
  `confidence`, `derivation_depth`, `verification_status`,
  `parent_ids: List[str]` (task IDs).
- **Storage layer** — `torment_service/provenance_v1.py::ProvenanceV1`.
  Attached to every memory on ingest. Tracks `source_type`, `source_role`,
  `write_path`, `parent_eids: List[int]` (memory EIDs).

The writeback path at `cognition/pipeline.py::_write_back_approved`
deliberately does not propagate spine `parent_ids` into storage `parent_eids`
— it builds storage-level parents from the run's retrieval context
(`_context_eids`). This is intentional composition, not field-copy.
Any future bridge between the layers must be an explicit design decision
(see §8, step 7 — chain-vs-replace).

## 4. Source type registry — storage layer (`ProvenanceV1`)

| Constant | Status | Producer call site | RSP parent? | Notes |
|---|---|---|---|---|
| `SOURCE_USER_INPUT` | **Active** | `for_user_ingest()` → `torment_service/fabric.py:2250` | Yes (Rule B allowed) | Default when `ingest()` is called without explicit provenance. Also synthesized when caller passes a dict through `from_dict()` validation at `fabric.py:2247`. |
| `SOURCE_ROLE_OUTPUT` | **Active** (gated) | `for_cognition_writeback()` → `cognition/pipeline.py:318` | No (Rule A / E blocks when `source_role` contains `archivist`) | Only reachable when `TORMENT_ARCHIVIST_WRITEBACK=1`. Gate is off by default. |
| `SOURCE_DERIVED` | **Deferred** | Zero producers (storage layer) | Rule B: *not allowed unless reviewed* | No factory emits this. Activation blocked on the chain-vs-replace architectural decision (step 7). Pinned to doctrine rule #2 — do not add this producer until memory-selection improvements make chained derivation useful. |
| `SOURCE_MEMORY` | **Reserved (migration trio)** | Zero producers | Yes (Rule B allowed — *migrated/imported*) | Reserved for the migration trio: paired with `WRITE_MIGRATION` or `WRITE_SYSTEM_IMPORT`. Commit history (`406d4f1` vs `a583d50`) shows this reservation is author intent, not leftover scaffolding. Also used as the normalization target for legacy bare strings on three read-side surfaces: `/debug/provenance` (§7.1), `resource_provenance` (§7.1), and the retrieval badge at `fabric.py:3475` and `:4394` (§7.2, resolved in step 4). None of these normalization targets propagate to the writeback path. |
| `SOURCE_TOOL_RESULT` | **Active** | `for_tool_result()` → `torment_service/spine.py:873` | Yes (Rule B allowed) | Can also enter via `ingest()` dict round-trip at `fabric.py:2247`. |
| `SOURCE_COLLECTIVE_ECHO` | **Active (write) / Excluded (parent)** | `for_collective_echo()` → `torment_service/fabric.py:2181` | **NO** — explicitly excluded from `_SAFE_PARENT_SOURCE_TYPES`; exclusion documented in RSP §"Collective Echo Exclusion" | Writable via `WRITE_COLLECTIVE_REINGEST` but deliberately not admissible as a writeback parent. Allowing echoes to chain would let upstream-agent cognition launder into the current agent's self-write ancestry (Rule F in spirit). Revising requires either a new Rule G bounding collective generations or a separate write-back channel for collective-informed proposals — out of scope for v2.4.x. The collective retrieval discount at `fabric.py:3425` is a separate concern (scoring, not writeback gating). Resolved in step 4. |
| `SOURCE_SHARE_PROPOSAL` | **Staging foundation (not yet wired)** | `for_share_proposal_quorum()` / `for_share_proposal_operator()` | **NO** — absent from `cognition/recursion_guard.py::_SAFE_SOURCE_TYPES_IN_WALK` | Typed storage origin for shared memory that resulted from an already-authorized TORMENT `ShareProposal`. It records neither quorum nor operator authority itself: `WRITE_SHARE_PROPOSAL_QUORUM` and `WRITE_SHARE_PROPOSAL_OPERATOR` retain that distinction. No Fabric or native proposal writer calls these factories in this commit. |
| `SOURCE_GATE1_UNRECOVERABLE` | **Storage sentinel** (step 6 commit A) | `WRITE_MIGRATION` writer only (commit B) | **NO** — rejected at any walk depth by `cognition/recursion_guard.py::_REJECTED_SOURCE_TYPES_IN_WALK`; the recursion guard additionally short-circuits any row carrying `admission_refused=True` with `REASON_MIGRATION_REFUSED` ahead of the source_type check | **Not an admissible origin class.** This is a storage sentinel applied by `WRITE_MIGRATION` to rows that gate 1 could not honestly recover. Live ingest paths (`direct_ingest`, `cognition_writeback`, `tool_ingest`, `collective_reingest`) MUST NEVER emit it. `ProvenanceV1.__post_init__` enforces that `source_type == SOURCE_GATE1_UNRECOVERABLE` requires `admission_refused=True`, so a malformed row claiming the sentinel without the refusal flag cannot be constructed. See `docs/ADMISSION_POLICY_v2.4.x.md § Storage sentinel` and `torment_service/migration/constants.py` for the full invariant list. |

### 4.1 Consumer-only references

The following read-path consumers check `source_type` values for routing or
scoring. They are not producers and do not affect the registry rows above, but
they constrain any future renaming:

- `fabric.py:2400` — tool-result dedup guard
- `fabric.py:2431` — existing-entity tool-result guard
- `fabric.py:2453` — direct-ingest write_path check
- `fabric.py:2694` — hivemind collective check
- `fabric.py:3317` — tool-result retrieval routing
- `fabric.py:3426` — collective retrieval discount (with legacy bare-string fallback — see §7.2)
- `fabric.py:4285` / `4289` — cross-workspace tool/collective filters
- `compression.py:285` / `291` — compression classifier for collective / tool results

## 5. Write path registry — storage layer (`ProvenanceV1`)

| Constant | Status | Producer call site | Notes |
|---|---|---|---|
| `WRITE_DIRECT_INGEST` | **Active** | `for_user_ingest()` → `torment_service/fabric.py:2250` | Paired with `SOURCE_USER_INPUT`. |
| `WRITE_COGNITION_WRITEBACK` | **Active (gated)** | `for_cognition_writeback()` → `cognition/pipeline.py:318` | Gated by `TORMENT_ARCHIVIST_WRITEBACK=0`. This is the entire target of the step 5 graph-walk recursion guard rewrite. |
| `WRITE_REFLECTION_WRITEBACK` | **Deferred** | Zero producers | `torment_service/spirit_reflection.py` stores reflections to `data/agents/{agent_id}/spirit_reflections/reflections.jsonl` — a parallel store that never touches `deep_memory/` or invokes `ProvenanceV1`. Until there is an explicit design decision to fold spirit reflections into governed memory, this write path has no intended producer. Pinned to doctrine rule #3 ("Spirit return is special — do not flatten spirit return into generic retrieval"). |
| `WRITE_TOOL_INGEST` | **Active** | `for_tool_result()` → `torment_service/spine.py:873` | Paired with `SOURCE_TOOL_RESULT`. |
| `WRITE_MIGRATION` | **Active (read-only in commit A)** | `torment_service/migration/` — commit A ships dry-run + status only; commit B adds the writer | Step 6 commit A activates the `WRITE_MIGRATION` surface in read-only form: the two-gate decision pipeline, cursor, review queue, dry-run report, and recursion-guard refusal path are live and tested, but no actual corpus row is ever written. The no-corpus-write invariant is enforced at test time by an AST import inspection in `tests/test_migration_dry_run.py`. Commit B lifts the read-only restriction by adding the row-rewrite path. See `docs/ADMISSION_POLICY_v2.4.x.md` and `docs/WRITE_MIGRATION_IMPLEMENTATION_PLAN_v2.4.x.md` for the commit A / commit B split. |
| `WRITE_SYSTEM_IMPORT` | **Reserved (pending adapter spec)** | Zero producers | Kept reserved in step 6 commit A. Unlike `WRITE_MIGRATION`, this write path has **no ratified adapter spec** — an import channel would need its own trust-tier rules, source provenance, and refusal discipline distinct from the migration's two-gate model. Activation is blocked on that spec, not on implementation work. Do not reuse the migration pipeline as a stand-in: the two use the same source_type (`SOURCE_MEMORY` on admit) but have different authorization semantics, and conflating them would silently widen the migration's admission surface. |
| `WRITE_COLLECTIVE_REINGEST` | **Active** | `for_collective_echo()` → `torment_service/fabric.py:2181` | Paired with `SOURCE_COLLECTIVE_ECHO`. |
| `WRITE_SHARE_PROPOSAL_QUORUM` | **Staging foundation (not yet wired)** | `for_share_proposal_quorum()` | Records that `process_proposals` had already authorized materialization. The factory derives `created_at_ts` from the maximum contributing durable proposal timestamp; it does not record processing or commit time. |
| `WRITE_SHARE_PROPOSAL_OPERATOR` | **Staging foundation (not yet wired)** | `for_share_proposal_operator()` | Records that `decide_proposal` had already authorized materialization. The factory derives `created_at_ts` from the approved proposal's durable creation timestamp; it does not record operator-click or commit time. |

## 6. Source type registry — spine layer (`schemas/provenance.py`)

The spine layer has its own, smaller `VALID_SOURCE_TYPES` set. It is not the
same vocabulary as the storage layer, and the two must not be conflated.

| Constant | Status in production | Producer | Notes |
|---|---|---|---|
| `SOURCE_USER_INPUT` (spine) | **Dead in production** | `Provenance.from_user()` — **zero production callers** (tests only) | The spine never materializes user_input provenance at runtime. Tasks carry their own `task_id` and roles wrap role output via `from_role`; the user side of the graph is represented by the task object, not a `Provenance`. |
| `SOURCE_ROLE_OUTPUT` (spine) | **Active** | `Provenance.from_role()` — `roles/interpreter.py:88`, `roles/skeptic.py:121`, `roles/engineer.py:85` & `:111`, `roles/base.py:51`, `roles/archivist.py:104` | The only spine source_type actively instantiated in production. |
| `SOURCE_DERIVED` (spine) | **Dead in production** | `Provenance.derive()` — **zero production callers** (tests only, `test_cognition_schemas.py:88`/`:95`/`:103`) | Because nothing calls `derive()` in production, `derivation_depth` never exceeds 1 in any running pipeline. This is the empirical counterpart to the reintegration replace-semantics discovery (see step 7). |
| `SOURCE_MEMORY` (spine) | **Dead** | Zero producers anywhere | Declared in `VALID_SOURCE_TYPES` but never instantiated — not by a factory, not by direct construction, not even by tests. Pure schema state. |

### 6.1 Spine-layer observations

- Only one of four declared spine source_types is actually produced in
  production. This is not a problem; it is honest documentation of how the
  cognition pipeline actually works today.
- `derivation_depth` is a field that mathematically could go above 1, but
  the production code path (`cognition/reintegration.py:196+`) uses
  proposal-id-keyed replace semantics, so every role handoff creates a fresh
  `from_role()` provenance at depth 1. Chained derivation would require an
  explicit architectural decision (step 7).

## 7. Undeclared vocabulary findings

Undeclared vocabulary is any string emitted as a `source_type` (or equivalent
badge field) that is not in `VALID_SOURCE_TYPES`. These are where schema and
runtime disagree.

### 7.1 `legacy_string` pseudo-type — **ELIMINATED** (step 2, this pass)

- **Was:** Read-path display normalizers at `app.py:2818` and `mcp_server.py:787`
  wrapped legacy bare-string provenance as
  `{"source_type": "legacy_string", "raw": str(prov)}`. The `legacy_string`
  source_type is not declared in `VALID_SOURCE_TYPES`, so these dicts could
  never round-trip through `ProvenanceV1(...)`.
- **Now:** Both sites normalize to
  `{"source_type": "memory", "notes": f"legacy_bare_string={raw!r}"}`.
  The normalized dict uses only declared fields from the dataclass and
  round-trips cleanly through `ProvenanceV1(source_type="memory", notes=...)`.
- **Safety note:** Both sites are strictly read-path debug surfaces
  (`/debug/provenance` HTTP endpoint and `resource_provenance` MCP resource).
  They are never invoked by the writeback path, which uses `lookup_fn` to read
  stored provenance directly. Changing the display target from the pseudo-type
  to `SOURCE_MEMORY` therefore cannot widen the safe-parent set.
- **Regression tests updated:** `tests/test_agent_key_regression.py` and
  `tests/test_mcp_key_feedback_regression.py` now assert the new shape and
  explicitly lock in `source_type != "legacy_string"` and `"raw" not in prov`.

### 7.2 `fabric.py` retrieval-badge passthrough — **RESOLVED** (step 4)

- **Was:** In the retrieval scoring loop, two symmetric sites leaked legacy
  bare-string provenance into the retrieval badge surface:
  - `fabric.py:3475` — top-level badge on every returned hit.
  - `fabric.py:4394` — `explain` block badge on the same hit shape.
  Both sites did `hh["provenance_type"] = _h_prov_raw` (or `str(_h_prov_raw)`)
  when the raw value was a string, letting an arbitrary legacy bare string
  leak into the retrieval badge as `provenance_type`. Downstream consumers
  of the badge read `hh["provenance_type"]` expecting a value from
  `VALID_SOURCE_TYPES` or `None`; a legacy bare string is neither.
- **Now:** Both sites normalize legacy bare strings to `"memory"`
  (`SOURCE_MEMORY`), with inline comments pointing back to this section.
  The badge surface now always carries a value from `VALID_SOURCE_TYPES`
  or `None`. `docs/TOOL_RESULT_RETRIEVAL_SEMANTICS.md` §Patch 2 updated to
  mirror the new pattern.
- **Neighboring semantic check preserved untouched:** The check
  `_h_prov_raw == "collective"` at `fabric.py:3425` is a *different* kind
  of handling — it preserves one known historical value so pre-ProvenanceV1
  collective memories still receive the collective retrieval discount
  (`TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT`, default 0.50). That check
  operates on the raw value before badge normalization runs, so the two
  paths are independent. The scoring semantics are unchanged; only the
  display/badge surface is affected.
- **Safety note:** As with §7.1, the retrieval badge is a read-side
  observable. It is not consumed by `cognition/pipeline.py::_write_back_approved`,
  which uses its own `lookup_fn` against stored payloads. This normalization
  cannot widen the writeback safe-parent set.
- **Impact on `test_tool_result_ingest.py:442`:** The `user_hits` filter
  there includes `"collective"` in its exclusion list as defensive guard
  for legacy bare-string data. The test uses a freshly-created fabric
  that never produces legacy bare-string provenance, so the defensive
  branch is dead code in that test's context and was deliberately left
  unchanged to keep step 4 scope narrow.

### 7.3 `check_recursion_safe()` and `is_archivist_writeback()` — **REMOVED (step 5 commit B)**

Both methods have been deleted from `torment_service/provenance_v1.py`.
This section is retained for historical context so the reasoning behind
the deletion, and the safety asymmetry the old code encoded, is not lost.

**Pre-deletion state (as observed during the step-3 and step-5 review
passes):**

- `provenance_v1.py` — `check_recursion_safe()` had zero production
  callers. It was only invoked from its own module context (dead code
  path).
- `provenance_v1.py` — `is_archivist_writeback()` had zero production
  callers other than `check_recursion_safe()` itself. Dead via transitive
  closure.

**Safety asymmetry (historical, preserved for future reference):** The
removed `is_archivist_writeback()` method required BOTH
`write_path == WRITE_COGNITION_WRITEBACK` AND `"archivist" in source_role`
to identify an archivist writeback. The live inline enforcement in place
before step 5 commit A only checked `"archivist" in source_role`, and the
step-5 guard in `cognition/recursion_guard.py` continues that stance —
archivist `source_role` at any depth rejects regardless of `write_path`.
The old removed method was stricter in shape but weaker in coverage — it
would have missed an archivist role that slipped into a non-cognition
write path. The live guard does not miss that case, which is the correct
direction for a safety check. If a future surface ever needs a predicate
that asks "is this specific provenance shape an archivist writeback",
it should re-derive the predicate from the guard's rules, not from the
removed helper's signature.

**Why removed, not kept as "dead but harmless":** After step 5 commit A
both methods described a one-hop check that was neither the live
enforcement shape nor the policy shape. Keeping them would have been
actively misleading to any future reader trying to understand the
enforcement lineage — they would have looked like the canonical rule
while the real rule lived in a different module. Deletion was the
maintenance-safe choice.

### 7.4 Latent `AttributeError` at `cognition/pipeline.py:275` — **RESOLVED (step 5)**

Fixed by routing parent provenance inspection through
`ProvenanceV1.normalize_parent()` inside `cognition.recursion_guard`. A
raw bare-string parent provenance now becomes `{"source_type": "memory",
"notes": "legacy_bare_string=..."}` before any `.get()` is attempted on
it, and the guard admits it as a safe parent. Regression test:
`tests/test_writeback_recursion_guard.py::TestRecursionGuardRejections::test_legacy_bare_string_parent_does_not_crash`.

The original vulnerability analysis is preserved below for historical
context.

#### Original analysis (pre-step-5)


- At line 266, `parent_prov = parent_payload.get("provenance")` can return a
  bare string (e.g. `"collective"`) for any legacy memory. Line 268
  (`if not parent_prov`) treats a non-empty string as truthy and falls
  through. Line 275 (`parent_prov.get("source_role")`) then calls `.get()`
  on a string and raises `AttributeError`.
- **Why it never fires in production:** The entire `_write_back_approved`
  path is gated off by `TORMENT_ARCHIVIST_WRITEBACK=0`.
- **Why it matters:** The moment anyone lifts the gate against a workspace
  that has any pre-ProvenanceV1 legacy memories, this crashes. It is
  additional justification for the step 5 graph-walk rewrite: the new guard
  should handle bare-string, dict, and `ProvenanceV1` parent shapes uniformly
  rather than assume dict.
- **Scope:** Do not patch in isolation. Fix as part of step 5.

## 8. Consolidated sequencing (post-step-4)

The v2.4.x tactical provenance pass as currently sequenced:

1. **Done (step 1).** Docstring drift fix — `provenance_v1.py:5` now pins
   to doctrine rule #5.
2. **Done (step 2).** `legacy_string` pseudo-type eliminated at both
   read-path normalizers (`app.py:2814` and `mcp_server.py:785`);
   regression tests updated; round-trips through the dataclass validator.
3. **Done (step 3).** Status registry with producer pointers,
   doctrine pins, and undeclared-vocabulary findings codified in this
   document.
4. **Done (step 4).** Two items landed together:
   - **Retrieval-badge normalization.** Both leak sites
     (`fabric.py:3475` and `fabric.py:4394`) now normalize legacy
     bare-string provenance to `SOURCE_MEMORY`, symmetric with §7.1.
     See §7.2 for full detail.
   - **Collective-echo exclusion documented.** `SOURCE_COLLECTIVE_ECHO`
     is now explicitly listed in the Not-allowed safe-parent class list
     in `RECURSION_SAFETY_POLICY_v2.4.x.md`, with a dedicated
     "Collective Echo Exclusion" subsection explaining the reasoning
     (echoes chaining would launder upstream-agent cognition into the
     current agent's self-write ancestry, violating Rule F in spirit).
     The `_SAFE_PARENT_SOURCE_TYPES` constant was left unchanged —
     this is a documentation-only resolution of the asymmetry,
     codifying the existing exclusion rather than widening the set.
5. **Done (step 5, commit A).** Bounded-DFS recursion guard landed as
   `cognition/recursion_guard.py`. Replaces the one-hop parent inspection
   in `_write_back_approved` with a depth-3 ancestry walk that enforces
   Rule F end-to-end, rejects `collective_echo` / `derived` at any depth,
   and is fail-closed on unknown, malformed, or cap-exceeded ancestry.
   Includes:
   - `ProvenanceV1.normalize_parent()` as the single source of truth for
     parent-provenance shape (absorbs §7.4).
   - 26 unit tests in `tests/test_writeback_recursion_guard.py` exercising
     the normalization contract, clean chains, rejection cases, cycle
     handling, and depth-cap boundary conditions.
   - New `docs/RECURSION_GUARD_TUNING_v2.4.x.md` pinning the depth cap
     (3), the admissible source_type set, and the per-run cap as policy
     choices with a three-gate tuning discipline (corpus analysis,
     rejection-rate diagnosis, doctrine review).
   - `docs/RECURSION_SAFETY_POLICY_v2.4.x.md` updated to reference the
     new guard, the new rejection-reason vocabulary, and the
     one-hop-vs-bounded-window policy/guard split.
   - Dead helpers (`check_recursion_safe`, `is_archivist_writeback`) are
     **left in place** in commit A to preserve a clean rollback path.
     Their removal is the separate commit B of the step-5 landing.
6. **Done (step 5, commit B).** `ProvenanceV1.check_recursion_safe()` and
   `ProvenanceV1.is_archivist_writeback()` removed from
   `torment_service/provenance_v1.py`. The "Safety checks" section of the
   class is now a short comment pointing at the live guard module. The
   26-test suite still passes unchanged; no production caller was
   affected (both methods were dead before removal). See §7.3 for the
   removal rationale and the preserved historical safety-asymmetry note.
7. **Gated on step 5 commit B — step 6.** Migration tooling for the
   reserved trio (`SOURCE_MEMORY` + `WRITE_MIGRATION` +
   `WRITE_SYSTEM_IMPORT`). Only useful once the bounded-DFS guard is
   live and the dead helpers are gone.
8. **Gated on explicit design decision — step 7.** Chain-vs-replace
   reintegration decision. Prerequisite to any future activation of
   `SOURCE_DERIVED` or allowing `derivation_depth > 1`. Note that any
   activation of `SOURCE_DERIVED` also has to revise
   `cognition/recursion_guard.py::_REJECTED_SOURCE_TYPES_IN_WALK` — see
   `docs/RECURSION_GUARD_TUNING_v2.4.x.md §3`.

## 9. Process — how to change this registry

- **Never silently add a new source_type or write_path constant.** Any new
  constant requires a producer call site in the same commit, or an explicit
  "Reserved" row in this registry with a justification paragraph referencing
  commit history discipline (the `406d4f1` vs `a583d50` pattern).
- **Never widen the guard's `_SAFE_SOURCE_TYPES_IN_WALK` or narrow its
  `_REJECTED_SOURCE_TYPES_IN_WALK` without updating §4, RSP, and
  `docs/RECURSION_GUARD_TUNING_v2.4.x.md`.** These constants live in
  `cognition/recursion_guard.py` and are policy, not configuration. Any
  change must clear the three-gate discipline in the tuning doc (corpus
  analysis, rejection-rate diagnosis, doctrine review).
- **Never let undeclared vocabulary leak through a read path.** The two
  surfaces that have already leaked (`/debug/provenance` and
  `resource_provenance`, now fixed in §7.1, plus the retrieval badge in §7.2,
  still open) are the canonical examples. A new read path that surfaces
  `source_type`-shaped data must normalize to `VALID_SOURCE_TYPES` or `None`.
- **Revisit this registry whenever `TORMENT_ARCHIVIST_WRITEBACK` gate
  state changes.** The status column for `WRITE_COGNITION_WRITEBACK` and
  `SOURCE_ROLE_OUTPUT` is written against the current "gated off" state.
- **When deleting a deferred or reserved constant, the commit message must
  reference this document and explain why the reservation is no longer
  needed.** Git history evidence is how author intent is preserved when
  reservation status changes.
