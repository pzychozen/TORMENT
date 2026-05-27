# Checkpoint — Memory-to-Prompt v0.2.4 Archive-FILTER-A Application

**Date:** 2026-05-27
**Status:** Closed / Ratified — PASS
**Cluster:** Memory-to-Prompt Automation v0.2.x — archive-FILTER-A
application (Option A, defense-in-depth). Closes the honestly-reported
gap that v0.2 first revision named under §S3 Decision 5.
**Commit chain:** `ea8b488` → `ac326bd` → `8538800` → `8459b08` →
`2415b93`. Parent v0.2.x closures: `102c425` (v0.2.2), `9203297`
(v0.2.3), `0787723` (v0.2 observability), `b455ae1` (v0.2 doctrine).
**Framing:** *v0.2.4 closes the archive-FILTER-A gap by adding
per-chunk governance metadata to archive memory and applying
`filter_llm_facing` unconditionally at `/retrieve` before
`assemble_context()`. Filter runs independent of
`include_assembly_audit`; the audit flag controls only whether the
audit payload is returned, never whether archive content is filtered.
Existing governance-less archive chunks remain backward-compatible
and pass by default. No migration. No assembler-level filtering. No
`/agent/query` wiring. No new surface enum. No new governance flags.*

---

## Summary

The v0.2 first revision honestly reported the archive-FILTER-A gap via
the `assembly_audit.filter_a.archive_filter_applied=false` field but
deferred the fix per §S3 Decision 5. v0.2.4-A1 closes that gap with
Option A: per-chunk governance metadata on archive chunks +
unconditional `filter_llm_facing` application at the `/retrieve`
chokepoint. Archive content that enters `BLOCK_ARCHIVE` and
`assembled_text` is now subject to the same universal `non_shareable`
exclusion that protects core memory at `fabric.py:4156`.

The arc spanned two ratification slices (A0 design-posture, A1
implementation plan) followed by five implementation commits, each
gated by targeted pytest + (at Commit 4) a full-suite green check
and (at Commit 5a) an operator-run live smoke against the real
TORMENT service under the hash embedder.

What this slice proves, narrowly stated: **a non-shareable archive
chunk that is retrieved by similarity at `/retrieve` is filtered out
of the assembled output before any LLM-facing surface sees it,
unconditionally, with honest visibility into the exclusion via the
audit payload when the audit is requested.** Nothing broader is
claimed. ST/BGE embedder behavior, Ryuki live verification, and
`/agent/query` archive surfacing are explicitly out of scope.

Per A1 ratification: no archive migration, no JSONL rewrite, no
schema-version bump, no doctrine amendment beyond closure
annotations.

---

## Arc — chronological (2026-05-27)

The work executed in two ratification gates followed by five
implementation commits, each with explicit operator authorization
between commits.

### A0 — Design-posture ratification

Trio survey of the three doctrine-framed options from v0.2 §3.2:

- **Option A** — add governance metadata to archive chunks and apply
  FILTER-A before archive hits enter prompt assembly.
- **Option B** — extend FILTER-A with an archive-specific surface
  enum value (`SURFACE_ARCHIVE_CONTEXT`).
- **Option C** — declare archive operator-curated content
  doctrinally; FILTER-A does not apply.

Audit found Option B is subsumed by Option A (the surface enum adds
naming without behavior at the current flag set, because
`non_shareable` is universal per FILTER-A §7). The real choice was
A vs C. Trio ratified **Option A** anchored on the v0.1 doctrinal
kernel — *"Memory may shape context. Memory may not seize authority"*
— and the observation that archive content enters LLM-facing
context once `assemble_context()` runs, so defense-in-depth applies
regardless of the operator-curated assumption.

Seven A0 sub-decisions installed: per-chunk governance only (per-doc
inheritance deferred); default-pass for governance-less chunks
(backward compat); filter site at `/retrieve` between
`ArchiveStore.retrieve()` and `assemble_context()`; no `/agent/query`
wiring; no migration; no assembler-level filtering; no new
`SURFACE_ARCHIVE_CONTEXT` enum value.

### A1 — Implementation plan ratification

Translated A0 into five precise commits with named files, exact
test additions, response-shape delta, and operator commands per
commit. Surfaced one structural decision point: how to make
`filter_llm_facing` emit archive-shaped exclusion records when
archive hits carry `chunk_id` rather than `eid`. Three options
proposed; trio ratified **shape (ii)**: add a keyword-only
`id_field: str = "eid"` parameter to `filter_llm_facing` with the
default preserving the legacy contract.

Doctrine sequencing: code-first, closure docs at the end (matching
the v0.2.2 and v0.2.3 cadence). `_ARCHIVE_FILTER_APPLIED_TODAY`
constant retained as legacy fallback. Existing `archive_filter_applied=False`
assertions split into both-mode coverage (omitted param → False;
empty-list param → True).

### Commit 1 — `feat(archive): add per-chunk governance field`

Hash `ea8b488`. Two files:

- `torment_service\archive_memory.py` — seven additive edits:
  `ArchiveChunk` dataclass gains optional `governance` field;
  defensive `obj.get("governance")` loader for legacy
  `chunks.jsonl` rows; `ingest_document` accepts keyword-only
  `governance` parameter that's shallow-copied into every produced
  chunk; both `retrieve()` and `retrieve_by_embedding()` include
  `"governance": dict(chunk.governance or {})` in returned hits
  (None on dataclass materializes as `{}` at API boundary).
- `tests\test_archive_memory.py` *(new)* — 12 tests across 6
  classes: default-no-governance (2), with-governance propagation
  (3), retrieve-surfaces-governance (4), backward-compat legacy
  chunk load (1), deep-copy invariant (2).

Targeted-test result: **12 passed**. Regression sweep on
`test_sqlite_index.py` + `test_closure_preserves_blocks_a_and_b.py`:
**34 passed**.

### Commit 2 — `feat(governance): add id_field parameter to filter_llm_facing`

Hash `ac326bd`. Two files:

- `torment_service\governance.py` — three additive edits to
  `filter_llm_facing`: keyword-only `id_field: str = "eid"`
  parameter at end of signature; docstring updated with Args entry
  and Returns shape note ("the key used for the identity slot in
  `excluded` records is the value of the `id_field` parameter");
  body replaces hardcoded `"eid"` lookup and emit-key with the
  parameterized `id_field`. Default preserves the sole existing
  call site at `fabric.py:4156`; no behavior change to core memory.
- `tests\test_filter_llm_facing.py` — appended one new test class
  `TestFilterLLMFacing_IdFieldParam` with 8 tests covering default
  preservation, chunk_id mode emit-key, surface-conditional rule
  under chunk_id, default-pass behavior under chunk_id, mixed-batch
  partition under chunk_id, missing-id None handling, generic
  `id_field` (custom string), results-shape-unchanged invariant.

Targeted-test result: **32 passed** in `test_filter_llm_facing.py`
(24 pre-existing + 8 new); **5 passed** in
`test_filter_llm_facing_authority_guard.py` (unchanged — Path C
Q1 guard runs before the body edit).

### Commit 3 — `feat(assembly_audit): accept optional archive_filter_excluded`

Hash `8538800`. Two files:

- `torment_service\assembly_audit.py` — four additive edits:
  `build_assembly_audit` signature gains keyword-only
  `archive_filter_excluded: Optional[List[Dict[str, Any]]] = None`;
  docstring adds Args entry explaining the legacy-omitted vs
  v0.2.4-A1-present contract and the explicit "archive exclusions
  NEVER mixed into core `excluded`" invariant; the helper's call
  to `_filter_a_record` now passes the new param through;
  `_filter_a_record` branch-logic: `None` → legacy path
  (`archive_filter_applied=False`, key omitted); list → new path
  (`archive_filter_applied=True`, defensively-copied
  `archive_excluded` key). `_ARCHIVE_FILTER_APPLIED_TODAY` constant
  retained as legacy-path fallback with inline comment explaining
  its preserved role.
- `tests\test_assembly_audit.py` — split `test_archive_filter_applied_is_false`
  into both-mode coverage (`test_archive_filter_applied_is_false_when_param_omitted`
  + `test_archive_filter_applied_is_true_when_empty_list_passed` +
  `test_archive_filter_applied_is_true_when_nonempty_list_passed`);
  added 6 more tests for archive_excluded presence/shape/record-key
  preservation, core-vs-archive isolation (load-bearing — core
  `excluded` not mixed with archive_excluded), deep-copy invariant
  (input mutation does not affect audit), plus sibling 7-key
  `filter_a` shape assertion for the v0.2.4-A1 path.

Targeted-test result: **76 passed** in `test_assembly_audit.py`
(previous baseline 67 + 9 net new). Regression sweep on
`test_assembly_audit_wiring.py`: **15 passed** (unchanged — Commit 3
left production wiring untouched).

### Commit 4 — `feat(retrieve): apply FILTER-A to archive hits (v0.2.4)`

Hash `8459b08`. The hinge commit. Two files:

- `torment_service\app.py` — three additive edits: top-level
  import `from .governance import filter_llm_facing, SURFACE_LLM_CONTEXT`
  (redundant with the transitive import via `.fabric` but explicit
  at the call site); new section "3b" inserted in `/retrieve`
  handler between drift loading (§3) and assemble_context call
  (§4) — declares `archive_filter_excluded: List[Dict[str, Any]] = []`
  at function scope, then `if archive_hits:` builds a
  `chunk_id → doc_id` map BEFORE filtering (because
  `filter_llm_facing` only knows the `id_field` it was given;
  doc_id is archive-surface-specific provenance and must be
  augmented at the call site), calls
  `filter_llm_facing(archive_hits, surface=SURFACE_LLM_CONTEXT, id_field="chunk_id")`,
  augments excluded records with doc_id, and replaces `archive_hits`
  with the filtered list; the `build_assembly_audit` call inside
  the existing `if req.include_assembly_audit:` block gains the
  `archive_filter_excluded=archive_filter_excluded` kwarg. The
  filter runs **unconditionally** — independent of
  `include_assembly_audit`; the audit flag controls only whether
  the audit payload is returned, never whether content is filtered.
- `tests\test_assembly_audit_wiring.py` — rename + flip of
  `test_audit_filter_a_archive_filter_applied_false` →
  `test_audit_filter_a_archive_filter_applied_true_in_production`;
  appended new test class `TestWiring_ArchiveFilterA` with 6 tests
  covering empty-list audit shape when no archive ingested,
  load-bearing record-shape preservation of non_shareable archive
  exclusion, the actual privacy invariant (non-shareable chunk
  absent from `blocks[archive_context]`), text-level companion
  invariant (sentinel marker absent from `assembled_text`), the
  critical unconditional-filter invariant (filter runs even when
  `include_assembly_audit=False`), and the audit-off response
  cleanliness (no audit-only keys leak when flag is off). Added
  `_ingest_archive_with_governance` helper that bypasses the
  `/archive/ingest_document` HTTP endpoint by calling
  `appmod._get_archive_store(...).ingest_document(...
  governance=...)` directly — the endpoint's request model does
  not yet accept governance (extension is a separate ratifiable
  slice).

Targeted-test result: **21 passed** in `test_assembly_audit_wiring.py`
(15 pre-existing + 6 new). Full-suite green check: **3,570 passed
/ 5 skipped / 22 subtests passed** under
`python -m pytest tests\ -q`.

A note on the transient A/B regression: the first pytest run
surfaced a divergence in `blocks` for the
`TestWiring_ResultsByteIdentityABTest.test_common_keys_byte_identical_with_vs_without_audit`
test. Per discipline, no patch was made; a temporary diagnostic
file (`tests\test_v0_2_4_diagnose_ab.py`) was added to surface the
actual differing fields under four controlled experiments. On
re-run after the diagnostic exercise, the original test passed
cleanly, the suite was green, and the diagnostic file was
deleted before commit. The transient signal was not reproduced;
the root cause remained unidentified but the post-Commit-4
baseline is stable (verified at full-suite level + at S6 live-smoke
level in Commit 5a).

### Commit 5a — `test(smoke): verify v0.2.4 archive-FILTER-A live`

Hash `2415b93`. One file:

- `tests\run_assembly_audit_smoke.py` — single block-edit inside
  `verify_audit()`: flipped the `archive_filter_applied is False`
  assertion to `is True` with rewritten v0.2.4-A1-aware green and
  red messages (the old red message contained a forward-looking
  warning "*if True, archive-FILTER-A fix landed without v0.2
  doctrine update*" — the forecast came true; the new red message
  is now a post-v0.2.4 regression warning); added one adjacent
  combined check asserting `archive_excluded == []` (key presence
  + empty value, since the smoke fixture ingests only core memory
  via `/agent/ingest` and `/tool/ingest`).

Live-smoke result on the real TORMENT service under the hash
embedder, against the disposable `audit_smoke_v0_2 / smoke_runner`
workspace: **32 GREEN / 0 YELLOW / 0 RED**. Previous v0.2 baseline
was 31 GREEN; the count grew by one (the new `archive_excluded`
check). All A/B byte-identity common keys verified identical
between audit-off and audit-on at the live service layer: `blocks`,
`assembled_text`, `tokens_used`, `profile`, `block_token_counts`,
`token_budget`, `selection_log`.

---

## Commits in scope

```
ea8b488  feat(archive): add per-chunk governance field
ac326bd  feat(governance): add id_field parameter to filter_llm_facing
8538800  feat(assembly_audit): accept optional archive_filter_excluded
8459b08  feat(retrieve): apply FILTER-A to archive hits (v0.2.4)
2415b93  test(smoke): verify v0.2.4 archive-FILTER-A live
```

The v0.2 doctrine (`b455ae1`) and the v0.2 / v0.2.2 / v0.2.3 closure
checkpoints (`0787723`, `102c425`, `9203297`) remain the load-bearing
historical references; this checkpoint is the closure record for
the archive-FILTER-A gap they collectively named as deferred.

---

## Test evidence

| Layer | Result |
|---|---|
| Commit 1 — `test_archive_memory.py` *(new)* | **12 passed** |
| Commit 1 — regression sweep (`test_sqlite_index.py` + `test_closure_preserves_blocks_a_and_b.py`) | **34 passed** |
| Commit 2 — `test_filter_llm_facing.py` | **32 passed** (24 + 8 new) |
| Commit 2 — `test_filter_llm_facing_authority_guard.py` | **5 passed** (unchanged) |
| Commit 3 — `test_assembly_audit.py` | **76 passed** (67 + 9 net new) |
| Commit 3 — regression sweep (`test_assembly_audit_wiring.py`) | **15 passed** (unchanged) |
| Commit 4 — `test_assembly_audit_wiring.py` | **21 passed** (15 + 6 new) |
| **Commit 4 — full-suite green** | **3,570 passed / 5 skipped / 22 subtests passed** |
| Commit 5a — operator-run live smoke (hash embedder) | **32 GREEN / 0 YELLOW / 0 RED** |

Post-v0.2.4 full-suite baseline is `3,570 passed / 5 skipped / 22
subtests` under `python -m pytest tests\ -q` (no `--ignore` flags).
Any future deviation from that count under that invocation is a
signal.

---

## What is now proven (load-bearing)

Six concrete claims, each with anchor evidence:

1. **Non-shareable archive chunks do NOT reach LLM-facing surfaces.**
   Verified at three layers: pytest in-process integration
   (`test_non_shareable_archive_chunk_absent_from_blocks` and
   `test_non_shareable_archive_chunk_absent_from_assembled_text`
   in `TestWiring_ArchiveFilterA`); pytest exclusion-record
   verification (`test_archive_excluded_records_non_shareable_chunk`);
   live smoke (with no archive content in fixture, archive_excluded
   is honestly `[]` and the audit reports `archive_filter_applied=True`,
   confirming the production filter is active).

2. **The filter runs UNCONDITIONALLY — independent of `include_assembly_audit`.**
   The audit flag controls only whether the audit payload is
   returned in the response, never whether archive content is
   filtered. Verified by `test_filter_runs_when_audit_off`:
   sentinel marker in a non-shareable archive chunk is absent from
   `blocks` and `assembled_text` in both audit-off and audit-on
   responses. Verified again at the live-smoke layer via the A/B
   byte-identity check.

3. **A/B byte-identity invariant preserved.** Audit-off vs audit-on
   `/retrieve` responses are byte-identical on the seven shared
   keys (`blocks`, `assembled_text`, `tokens_used`, `profile`,
   `block_token_counts`, `token_budget`, `selection_log`).
   Audit-on adds exactly one extra top-level key (`assembly_audit`)
   and modifies nothing else. Verified in-process
   (`test_common_keys_byte_identical_with_vs_without_audit` in
   `TestWiring_ResultsByteIdentityABTest`) and live (Commit 5a
   `verify_ab_byte_identity` — 7 GREEN common-key identity checks
   among the 32 total).

4. **Backward compatibility holds for existing on-disk archive
   chunks.** Legacy `chunks.jsonl` rows written before the
   v0.2.4-A1 schema gained the `governance` field load cleanly via
   defensive `obj.get("governance")`, becoming chunks with
   `governance=None`; these flow through the filter as
   default-pass and are NOT excluded. No migration, no JSONL
   rewrite, no schema-version bump required. Verified by
   `test_load_legacy_chunks_jsonl_without_governance_field`.

5. **Production audits report archive filtering honestly with full
   exclusion provenance.** `filter_a.archive_filter_applied=True`
   in every production `/retrieve` audit response after v0.2.4-A1.
   When non-shareable archive chunks are present in the candidate
   set, `filter_a.archive_excluded` carries archive-shaped records:
   `{"chunk_id": str, "doc_id": str, "excluded_reason": str}`. When
   no exclusions occur, `archive_excluded=[]` (key present is the
   structural signal that the filter ran). Verified live in
   Commit 5a smoke; verified in-process at pytest wiring layer.

6. **Core memory and archive memory exclusion surfaces remain
   isolated.** `filter_a.excluded` continues to carry only
   core-memory eid-shaped records (`{"eid": int|None, "excluded_reason": str}`);
   archive exclusions never mix into that list. Archive
   exclusions live exclusively in `filter_a.archive_excluded`
   with chunk_id-shaped records. Verified by
   `test_core_excluded_unaffected_by_archive_filter`.

Plus the operating posture: no archive migration; no
assembler-level filtering; no new `SURFACE_ARCHIVE_CONTEXT` enum
value; no new governance flags; no env var introduction; no
ledger writes (Option C from v0.2 still honored); no character
workspace touched; live verification under hash embedder only
(ST/BGE and Ryuki explicitly out of scope).

What is **not** claimed:

- This checkpoint does NOT prove `/agent/query` archive surfacing
  is filtered. `/agent/query` does not surface archive content at
  all (per v0.2 first-revision posture and per `9a3c0f3` docs
  correction), so the question doesn't arise.
- It does NOT prove correctness under ST or BGE embedders. Hash
  embedder only.
- It does NOT exercise a real character workspace (Ryuki etc.
  remain protected by the hardcoded denylist in the smoke).
- It does NOT extend the `/archive/ingest_document` HTTP endpoint
  to accept governance (the request-model extension is a
  separately ratifiable slice; pytest helper bypasses HTTP for
  test ergonomics).
- It does NOT introduce ingest-time auto-detection or redaction
  heuristics for archive content.
- It does NOT migrate any existing archive data on disk.

---

## Ratified decisions

The A0 design-posture decisions and A1 implementation-plan decisions
are installed throughout the implementation and recorded here for
traceability. None changed across the five commits.

**A0 design-posture decisions:**

1. **Option A** ratified over Option C. Option B subsumed by A
   (the `SURFACE_ARCHIVE_CONTEXT` enum value adds naming without
   behavior at the current flag set).
2. **Per-chunk governance only** for v0.2.4. Per-document
   inheritance deferred to a future composition slice.
3. **Default-pass for governance-less chunks.** Backward-compat
   choice; existing on-disk chunks continue to load and surface
   unchanged.
4. **Filter site at `/retrieve`** between `ArchiveStore.retrieve()`
   and `assemble_context()`. Assembler stays content-agnostic;
   `_archive_hit_to_block` untouched.
5. **No `/agent/query` wiring.** That endpoint does not surface
   archive content; no work required.
6. **No archive migration.** Defensive `.get()` loader handles
   legacy rows; no on-disk rewrite.
7. **No assembler-level filtering.** Filter site is the
   `/retrieve` handler, not inside `assemble_context()`.

**A1 implementation-plan decisions:**

8. **Exclusion-record shape (ii):** `filter_llm_facing` gains a
   keyword-only `id_field: str = "eid"` parameter with the default
   preserving the legacy contract for the existing call site at
   `fabric.py:4156`.
9. **`_ARCHIVE_FILTER_APPLIED_TODAY` constant retained** as legacy
   fallback with an inline comment explaining its preserved role.
10. **Test split into both-mode coverage:**
    `test_archive_filter_applied_is_false_when_param_omitted`
    (legacy path) AND
    `test_archive_filter_applied_is_true_when_empty_list_passed`
    (new path). Three pre-existing locked assertions were flipped
    in coordinated commits (Commit 3 in `test_assembly_audit.py`,
    Commit 4 in `test_assembly_audit_wiring.py`, Commit 5a in
    `run_assembly_audit_smoke.py`).
11. **Code-first commit cadence:** helper → param → audit-helper →
    wiring → smoke. Each commit independently reviewable with a
    targeted gate; full-suite green check at the integrating
    commit (Commit 4).
12. **Docs-at-closure sequencing:** doctrine and orientation map
    edits land in a single closure commit (this commit), not
    interleaved with code commits. Matches the v0.2.2 and v0.2.3
    cadence.

---

## Intentionally deferred

Each item named, anchored, and assigned to a future slice. v0.2.4
closure does NOT resolve any of them.

| # | Item | Notes |
|---|---|---|
| 1 | **Per-document governance inheritance at ingest** | Natural shape: `ingest_document` accepts optional `doc_governance` and fills each new chunk's `governance` from it unless explicitly overridden. Moves inheritance into ingest, preserves single canonical retrieval shape. Out of scope here; named for the future. |
| 2 | **`/archive/ingest_document` request-model extension** | The HTTP endpoint's `IngestDocumentReq` does not currently accept `governance`. Extending it would let live HTTP callers (and the live smoke) ingest governance-tagged archive content. Separate small ratifiable slice; pytest already covers the exclusion path via the `_ingest_archive_with_governance` helper that bypasses HTTP. |
| 3 | **Archive-side autotagging / redaction heuristics** | Inferring `non_shareable` from chunk content (PII detection, etc.) at ingest time. Operator-only authorship vs autotag is a doctrinal question; deferred. |
| 4 | **ST / BGE embedder live verification of v0.2.4** | Live smoke covers hash embedder only. A future verification slice could re-run the smoke under `TORMENT_EMBED_PROVIDER=st` (or bge) to confirm embedder-agnostic behavior, paralleling the v0.2 S6 ST follow-up pattern. |
| 5 | **Ryuki / real character workspace live check** | Inherited from v0.2 closure parked item #7. Still parked. Smoke continues to use the disposable `audit_smoke_v0_2` workspace; Ryuki remains in the hardcoded denylist. Separate explicit slice with explicit trio authorization. |
| 6 | **`_ARCHIVE_FILTER_APPLIED_TODAY` constant removal** | The constant is retained as a legacy fallback per A1 §3 ratification. Future cleanup may remove it if the legacy path is deemed no longer needed. Cosmetic; non-blocking. |
| 7 | **Transient A/B regression root-cause investigation** | The Commit 4 first pytest run surfaced an A/B byte-identity divergence that did not reproduce on the second run after the diagnostic exercise. Root cause was not identified. Post-v0.2.4 baseline is stable (full-suite + live-smoke both green), but if the signal recurs in a future slice, the diagnostic shape from `test_v0_2_4_diagnose_ab.py` (deleted) is the right starting point. |

---

## Non-goals preserved through this checkpoint

- No production code change beyond the five commits in scope.
- No test change beyond the new file (`test_archive_memory.py`) and
  the assertion-flip / class-addition edits at the named test
  files in Commits 2, 3, 4, and 5a.
- No doctrine amendment beyond the closure annotations applied to
  the v0.2 doctrine and the three sibling checkpoints in this
  commit. The historical text of v0.2 first revision (and its
  closure checkpoint, and the v0.2.2 / v0.2.3 closure checkpoints)
  remains unchanged in substance.
- No new MCP surface, no new MCP tool, no new exposure tier.
- No env var introduction.
- No scheduler / daemon / wall-clock trigger.
- No new tool family.
- No `/agent/query` wiring (archive content does not flow through
  that endpoint; no work required).
- No assembler-level filtering. `_archive_hit_to_block` and
  `assemble_context()` are untouched.
- No new `SURFACE_ARCHIVE_CONTEXT` enum value. The existing
  `SURFACE_LLM_CONTEXT` is reused.
- No new governance flags. Existing `non_shareable` and
  `collective_export_blocked` are the only flags consumed.
- No archive migration. No JSONL rewrite. No schema-version bump.
- No retroactive governance flag-setting on existing chunks.
- No ingest-time auto-detection or redaction.
- No character workspace touched. Ryuki, `default`, `default_st`,
  and `external_inference_smoke_st` remain in the smoke's
  hardcoded denylist.
- No long-iteration tier opened.
- No ledger persistence in this revision. v0.2 §S3 Decision 1
  (Option C — response-only) remains in force for v0.2.4 as well;
  the `archive_excluded` list lives only in the HTTP response when
  the audit flag is set.
- No live Ryuki dependency.
- No automation. No autonomous behavior. No new authority surface.

---

## Recommendation: pause here

v0.2.4 is closed with full-suite green + live-smoke green evidence.
The disciplined move is to lock it in and decide the next move
with a fresh head, per the same pattern as the v0.2 / v0.2.2 /
v0.2.3 closures.

Concretely:

- **Do not** auto-open the next v0.2.x gate (per-doc inheritance,
  ingest-API extension, ST/BGE verification, Ryuki live check, or
  any other named-deferred item).
- **Do not** auto-bundle parked-item cleanups into this commit.
- **Do not** auto-extend to ST or BGE embedder or Ryuki workspace.
- **Do not** open new behavior of any kind.

The next decision belongs to a separate planning moment when the
trio is ready.

---

## References

- **Parent doctrine:** `docs/MEMORY_TO_PROMPT_AUTOMATION_v0.1.md`
  (`ba1c9fa`). Character-first boundary doctrine; parent to v0.2.
- **v0.2 observability lane doctrine:**
  `docs/MEMORY_TO_PROMPT_AUTOMATION_v0.2.md` (`b455ae1` plus the
  closure annotations applied in this commit). v0.2.4 inherits
  the character-first hierarchy and the *"Governance is
  subordinate in purpose, but load-bearing in
  substrate-criticality"* canonical phrasing verbatim.
- **Pre-autonomy spine anchors:** Track A v0.1, Cluster 2 v0.1,
  Track B v0.1, Cluster 5 v0.1, `MCP_CAPABILITY_BOUNDARY`,
  `TORMENT_AGENT_DOCTRINE_v0.1`. None amended by v0.2.4.
- **Sibling closure checkpoints in the v0.2.x extension chain:**
  - `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_OBSERVABILITY_v0.2.md`
    (`0787723`). Parent v0.2 first revision closure; item #4 of
    its parked-items table is closed by this checkpoint.
  - `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_2_CHARACTER_CONTEXT.md`
    (`102c425`). v0.2.2 Candidate A closure; inherited parked
    item #4 closed by this checkpoint.
  - `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_3_SPIRIT_RETURN.md`
    (`9203297`). v0.2.3 spirit-return surfacing verification;
    non-goal "archive-FILTER-A change" annotated with closure
    note.
- **Implementation surfaces touched (file:approximate-section):**
  - `torment_service\archive_memory.py` — `ArchiveChunk`
    dataclass; `_load()` chunks loader; `ingest_document`;
    `retrieve()`; `retrieve_by_embedding()`.
  - `torment_service\governance.py` — `filter_llm_facing`
    signature + body. Surface enum unchanged.
  - `torment_service\assembly_audit.py` — `build_assembly_audit`
    public entry; `_filter_a_record` helper.
  - `torment_service\app.py` — `/retrieve` handler section "3b"
    (new) + `build_assembly_audit` call (kwarg added).
- **Test surfaces:**
  - `tests\test_archive_memory.py` *(new)* — 12 tests.
  - `tests\test_filter_llm_facing.py` — 8 new tests in
    `TestFilterLLMFacing_IdFieldParam`.
  - `tests\test_assembly_audit.py` — split + 9 net new tests in
    `TestBuildAssemblyAudit_FilterARecord` and sibling 7-key
    `filter_a` shape test.
  - `tests\test_assembly_audit_wiring.py` — rename + flip + 6
    new tests in `TestWiring_ArchiveFilterA`.
  - `tests\run_assembly_audit_smoke.py` — assertion flip +
    `archive_excluded` check.
- **Orientation:** `docs\PROJECT_ORIENTATION_MAP.md` §2
  closed-arcs table updated to include this slice; §6
  parked-items entry removed; §7 reset to candidate-list
  framing without auto-opening a next gate.
