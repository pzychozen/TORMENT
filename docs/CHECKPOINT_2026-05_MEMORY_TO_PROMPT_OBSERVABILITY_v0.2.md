# Checkpoint — Memory-to-Prompt Observability v0.2 (first revision)

**Date:** 2026-05-25
**Status:** Closed / Ratified — PASS
**Cluster:** Memory-to-Prompt Automation v0.2 — observability lane (first
revision)
**Commit range:** `ba1c9fa` (parent v0.1 doctrine) → `eecae5d` (S6
script fix)
**Framing:** *v0.2 first revision closed — observability lane PASS.*

---

## Summary

This checkpoint closes the first implementation revision of the
Memory-to-Prompt Automation v0.2 lane: read-only **character-memory
observability** for memory-to-prompt automation. The arc spanned six
slices (S1 read-only audit → S2 scratch framing draft → S3 promotion
to ratified doctrine → S4 helper + unit tests → S5 opt-in `/retrieve`
wiring → S6 operator-run live verification) executed in a single
working session on 2026-05-25. All evidence layers passed: 67/67 S4
helper unit tests; 15/15 S5 wiring tests (including the load-bearing
A/B byte-identity invariant); and 31 GREEN / 0 YELLOW / 0 RED on the
S6 operator-run live smoke against the real TORMENT service under the
hash embedder.

What this lane proves, narrowly stated: **TORMENT can expose
character-memory-to-prompt observability through the live service,
without changing normal retrieval output, while preserving provenance
and authority visibility for tool-result rows.** Nothing broader is
claimed by this closure — no other automation lane is opened, no
existing doctrine is amended, no behavior is changed on the
default-off path.

Per S3 Decision 1 (Option C — response-only), no disk-persistent
ledger is written by this revision; the `assembly_audit` payload
exists only in HTTP responses returned when the opt-in flag is set.
Ledger persistence and other v0.2.x extensions remain as named
seams; none is authorized by this checkpoint.

---

## Arc — chronological (S1 → S6, 2026-05-25)

The six slices ran in sequence with explicit trio ratification gates
between each. Every slice produced a stop-and-report before the next
was authorized.

### S1 — Read-only code-surface audit

Walked the end-to-end memory-to-prompt path: `live_agent/memory_bridge`
→ `POST /retrieve` → `fabric.query()` → `filter_llm_facing(SURFACE_LLM_CONTEXT)`
→ `ArchiveStore.retrieve()` → `assemble_context()` → returned blocks.
Five gaps surfaced that the v0.2 lane would address:

1. **Dropped FILTER-A exclusions.** `_filter_excluded` captured at
   `fabric.py:4158` but consumed only by continuity_debug locally;
   not propagated to `/retrieve` response.
2. **Archive hits do not pass FILTER-A.** `ArchiveStore.retrieve()`
   returns chunk dicts with no `governance` field; archive hits flow
   straight to `BLOCK_ARCHIVE` without surface filtering. (Reported
   honestly by v0.2; fix deferred to v0.2.4 / v0.3 per S3 Decision 5.)
3. **`selection_log` lacks structured classification rationale.** The
   classification basis lives in `_classify_core_hit()` but isn't
   surfaced as structured fields.
4. **Spirit-return summary separated from assembled output.** Lives
   on `character_context` from `fabric.query()`; not attached to
   `AssembledContext`.
5. **No assembled-output summary of `tool_result` advisory presence.**

Canonical `live_agent/memory_bridge.py` location confirmed as
`torment_fabric/live_agent/memory_bridge.py`; repo-root duplicate
cleanup deferred to a separate slice.

### S2 — Scratch framing draft

Scratch draft of `scratch/MEMORY_TO_PROMPT_AUTOMATION_v0.2_OBSERVABILITY_FRAMING_DRAFT_2026-05-25.md`.
Eight required sections including pros/cons on ledger location.
Three options surfaced (A: extend `memory_events.jsonl`; B: new
`assembly_audit.jsonl`; C: defer disk persistence entirely). Draft
intentionally did not pick.

### S3 — Promotion to ratified doctrine

Promoted scratch → `docs/MEMORY_TO_PROMPT_AUTOMATION_v0.2.md`
(committed `b455ae1`). Seven trio-ratified decisions installed:

1. **Option C** — response-only, no disk persistence in this revision.
2. **Helper module** — `torment_service/assembly_audit.py` (new,
   clean separation from FILTER-A).
3. **Helper name** — `build_assembly_audit`.
4. **Request flag** — `include_assembly_audit: bool = False`.
5. **Archive-FILTER-A fix deferred** — v0.2 reports honestly; fix is
   a separate ratifiable slice.
6. **v0.1 block-count correction parked** — future v0.1.1 cleanup.
7. **No-code S3** — promotion is doctrine-only.

Scratch S2 draft preserved as lineage.

### S4 — Helper + unit tests

Two new files (`torment_service/assembly_audit.py` +
`tests/test_assembly_audit.py`), committed `214c9f7`. Helper
implements `build_assembly_audit(...)` plus eight private helpers
(`_request_record`, `_embedder_snapshot`, `_filter_a_record`,
`_character_summary`, `_assembly_summary`, `_classification_basis`,
`_spirit_return_summary`, `_tool_result_summary`) producing the v0.2
§4.2 response shape from existing fabric / assembler / archive
inputs. 67 unit tests covering response shape, no-mutation, no-I/O
(monkeypatched `builtins.open` / `pathlib` / `socket`), graceful
defaults, classification basis per rule, spirit-return summary,
tool-result advisory summary.

One small bug surfaced and patched cleanly: `_classification_basis({})`
and `_classification_basis(None)` originally returned
`half_life>=7` because `half_life` defaulted to `30.0`. Fix: added
`has_half_life` explicit-presence guard; empty / None metadata now
returns `default_situational` (the honest "no metadata"
classification). Tests were unchanged; the patch aligned helper
behavior to the test expectations. Final: **67 passed in 0.25s**.

### S5 — Opt-in wiring at `/retrieve`

Three files modified, one created. Committed `bda3652`:

- `torment_service/fabric.py` — three additive keys on
  `Workspace.query()` return dict: `filter_excluded` (alias of
  existing `excluded` for S4-helper compatibility),
  `_core_hits_in_count`, `_authority_guard_rejected`.
- `torment_service/app.py` — `AssembleContextReq.include_assembly_audit`
  field (default False); `/retrieve` handler conditionally calls
  `build_assembly_audit` and adds `assembly_audit` to response.
- `live_agent/memory_bridge.py` — `MemoryBridge.retrieve()` gains
  optional `include_assembly_audit` kwarg.
- `tests/test_assembly_audit_wiring.py` (new) — 15 integration tests
  via FastAPI TestClient covering request model, audit-off-by-default,
  audit-on top-level shape, A/B byte-identity, fabric return shape,
  MemoryBridge kwarg propagation.

`/agent/query` deliberately left untouched (Option A — the endpoint
doesn't run `assemble_context()` so cannot produce a full audit
without behavior change; doctrinal §4.3 correction parked for v0.1.1).
Load-bearing A/B byte-identity invariant passed under TestClient
in-process: common response keys identical between audit-off and
audit-on; audit-on adds exactly `{"assembly_audit"}`.

### S6 — Operator-run live verification

One new file: `tests/run_assembly_audit_smoke.py` (committed
`39ca46e`, fix `eecae5d`). Operator-run smoke script (not pytest)
exercising the real HTTP path against a live TORMENT service under
the hash embedder. Hardcoded protected-workspace denylist
(`ryuki`, `default`, `default_st`, `external_inference_smoke_st`);
disposable workspace `audit_smoke_v0_2 / smoke_runner`; three-ingest
fixture; A/B `/retrieve` calls; 31 hard checks plus soft yellow
findings.

One script-side bug surfaced on first live run: `/tool/ingest`
endpoint expects `content` field, not `text` (field name diverges
from `/agent/ingest`). Patched in `eecae5d`; documented inline with a
comment so future readers don't trip on the same divergence. Tests
and service code unchanged.

Final operator-run result: **31 GREEN / 0 YELLOW / 0 RED**.

---

## Commits in scope

```
ba1c9fa  docs(memory-to-prompt): add v0.1 character-first boundary doctrine
b455ae1  docs(memory-to-prompt): add v0.2 observability lane doctrine
214c9f7  feat(memory-to-prompt): add assembly audit helper
bda3652  feat(memory-to-prompt): wire assembly_audit opt-in into /retrieve
39ca46e  test(memory-to-prompt): add operator-run assembly audit smoke
eecae5d  fix(memory-to-prompt): correct assembly audit smoke tool ingest payload
```

`ba1c9fa` is the parent v0.1 doctrine (character-first boundary).
`b455ae1` is the v0.2 observability lane doctrine that v0.1 anchors.
`214c9f7` / `bda3652` / `39ca46e` are the S4 / S5 / S6 implementation
commits. `eecae5d` is the S6 fix.

The v0.2 doctrine itself remains the load-bearing reference for the
observability lane; this checkpoint is the closure record, not a
replacement for it.

---

## Test evidence

| Layer | Result |
|---|---|
| S4 unit tests (`tests/test_assembly_audit.py`) | **67 passed in 0.25s** |
| S5 wiring file (`tests/test_assembly_audit_wiring.py`) | 15 tests green (operator confirmed) |
| S5 A/B byte-identity (`TestWiring_ResultsByteIdentityABTest`) | 1 passed (load-bearing) |
| S5 + S4 paired run | green |
| S5 full-suite green-check | green (operator confirmed) |
| S6 operator-run live smoke | **31 GREEN / 0 YELLOW / 0 RED** |

The A/B byte-identity invariant is proven at two layers:
in-process via FastAPI TestClient (S5) and live-service via the
operator-run smoke (S6). Both layers confirm audit-on does not
change the common response keys.

---

## What is now proven (load-bearing)

Six concrete claims, each with the anchor evidence:

1. **The v0.2 observability lane works end-to-end.** S6: 31 GREEN
   across the real HTTP path, real persistence, real embedder.
2. **Audit-on does NOT change normal `/retrieve` output.** A/B
   byte-identity proven twice — in-process (S5
   `TestWiring_ResultsByteIdentityABTest`) and live (S6
   `verify_ab_byte_identity`). Common keys `blocks`, `assembled_text`,
   `tokens_used`, `profile`, `block_token_counts`, `token_budget`,
   `selection_log` byte-identical between audit-off and audit-on.
3. **`assembly_audit` payload shape matches v0.2 §4.2 verbatim.**
   Top-level keys exactly `{lane_version, timestamp, request, embedder,
   filter_a, assembly, character, spirit_return_summary, tool_result_summary}`.
   Confirmed at both S5 and S6.
4. **Cluster 2 §11.3 three-modifier round-trips through the audit
   verbatim.** `tool_result_summary.three_modifier ==
   "(low-authority, decay-bounded, tool_result)"` — verified live in
   S6 with the tool-result row that entered prompt context carrying
   the verbatim string.
5. **Honest archive-FILTER-A gap reporting works.**
   `filter_a.archive_filter_applied == false` surfaces on the audit
   payload (v0.2 §3.2 commitment honored). S6 confirmed live.
6. **The embedder snapshot in the audit catches audit-vs-runtime
   drift.** S6 verified the audit's `embedder` block matches
   `/embedder/check` exactly (`provider="hash"`, `model`, `dim`).

Plus the operating posture: no disk persistence (Option C honored
throughout); no behavior change on the default-off path; character-first
framing held; *"Governance is subordinate in purpose, but load-bearing
in substrate-criticality"* canonical phrasing preserved.

What is **not** claimed:

- This checkpoint does NOT prove any future automation lane works.
- It does NOT prove the lane works under ST embedder (hash only; ST
  is an optional second-pass variant if the trio chooses).
- It does NOT exercise spirit-return surfacing meaningfully (zero
  spirit-return hits on the disposable workspace; that's an honest
  zero, not a failure).
- It does NOT exercise the archive-FILTER-A gap fix path (gap is
  reported, not fixed).
- It does NOT exercise any real character workspace (Ryuki etc.
  protected by hardcoded denylist).

---

## Ratified decisions

The seven S3 decisions are installed throughout the implementation
and are recorded here for traceability. None changed across S4 / S5
/ S6.

1. **Option C — response-only, no disk persistence** in v0.2 first
   revision. Audit payload exists only in HTTP responses.
2. **Helper module:** `torment_service/assembly_audit.py` (new;
   clean separation from FILTER-A in `governance.py`).
3. **Helper name:** `build_assembly_audit`.
4. **Request flag:** `include_assembly_audit: bool = False` (per-call
   opt-in; v0.1 Invariant 9 honored — no global env-var toggle).
5. **Archive-FILTER-A fix deferred** to v0.2.4 / v0.3. v0.2 reports
   the gap honestly via `archive_filter_applied=false`.
6. **v0.1 block-count miscount parked** for future v0.1.1 cleanup.
7. **Option A for `/agent/query`** (ratified at S5 planning): only
   `/retrieve` wired in v0.2 first revision. `/agent/query` unchanged.
   v0.2 §4.3 correction parked for v0.1.1.

---

## Intentionally deferred (the seven parked items)

Each item is named, anchored, and assigned to a future slice. v0.2
first revision closure does NOT resolve any of them.

| # | Item | Deferred to |
|---|---|---|
| 1 | v0.1 block-count cleanup (4-block → 5-block; `BLOCK_REFERENCE` is between identity and relational) | v0.1.1 cleanup pass (small docs slice; bundle candidate with #2) |
| 2 | v0.2 §4.3 `/agent/query` doctrine-vs-reality correction (doctrine says both endpoints get audit; only `/retrieve` is wired per Option A) | v0.1.1 cleanup pass |
| 3 | `excluded` vs `filter_excluded` naming duplication on `Workspace.query()` return shape (S5 added the alias for S4-helper compatibility; both carry the same list) | v0.2.x cleanup pass (pick canonical name and migrate the other) |
| 4 | Archive-FILTER-A gap fix (archive hits bypass FILTER-A; chunks lack governance metadata) | v0.2.4 or v0.3 (one of: governance-on-chunks + filter; new surface enum; or operator-only doctrinal stance) |
| 5 | `live_agent/` repo-root duplicate cleanup (canonical = `torment_fabric/live_agent/`) | Separate ratifiable slice |
| 6 | Ledger persistence (Option A `memory_events.jsonl` extension vs Option B new `assembly_audit.jsonl`) | v0.2.x or v0.3 after live audit-shape verification accumulates |
| 7 | Ryuki / real character workspace live check (S6 used disposable workspace only) | Separate explicit slice with explicit trio authorization |

Items #1 and #2 are bundle candidates — both are doc-only
corrections. v0.2.x cleanup could land both as `v0.1.1` if desired.

---

## Next candidate gates (descriptive only)

Per Memory-to-Prompt v0.2 §7.5. Listed as descriptive successor
options for the trio when the next gate is opened. **No sequencing
implied. None authorized by this checkpoint.**

- **v0.2.x ledger persistence** — Option A vs Option B (deferred
  parked item #6 above).
- **v0.2.1 profile-aware intent classification.**
- **v0.2.2 character-context block enrichment.**
- **v0.2.3 spirit-return voice-cue verification.**
- **v0.2.4 archive-FILTER-A application** (parked item #4).
- **v0.3 per-tool-family `tool_result` defaults** (Cluster 2 §11.7).
- **Archivist writeback gate-flip operational deliverables**
  (ARCHIVIST_WRITEBACK_GATE_FRAMING D2 / D4 / D5).
- **v0.1.1 cleanup pass** (parked items #1 + #2 bundled).
- **`live_agent/` cleanup** (parked item #5).
- **Ryuki live check** (parked item #7).
- Broader pre-autonomy spine extensions: **Cluster 2 v0.2 runtime
  Authority Gate**, **Track B v0.2 runtime contest ledger**, **Voice
  Test v0.3 / Phase 4b**, **Cluster 5 v0.2 storage survivability
  mechanisms**.

The next gate is the operator's call. This checkpoint is a save
point, not a launch point.

---

## Non-goals preserved through this checkpoint

- No code change.
- No test change.
- No doctrine amendment (Memory-to-Prompt v0.1 / v0.2 / Track A /
  Cluster 2 / Track B / Cluster 5 / MCP boundary / Agent Doctrine
  all unamended).
- No resolution of any of the seven parked items.
- No opening of any next-candidate gate.
- No ledger persistence (Option C remains the ratified posture).
- No archive-FILTER-A fix.
- No `/agent/query` wiring.
- No env var introduction.
- No new MCP surface.
- No scheduler / daemon / wall-clock trigger.
- No new tool family.
- No character workspace touched.
- No long-iteration tier opened.

---

## Recommendation: pause here

The v0.2 observability lane is closed with clean evidence. The
disciplined move is to lock it in and decide the next move with a
fresh head, per the same pattern as the Tier 2 closure
(`CHECKPOINT_2026-05_TIER_2_RUNTIME_EVIDENCE.md` §"Recommendation").

Concretely:

- **Do not** auto-open the next v0.2.x gate.
- **Do not** auto-bundle parked-item cleanups into this commit.
- **Do not** auto-extend to ST embedder or Ryuki workspace.
- **Do not** implement ledger persistence on the back of this run.

The next decision should be a separate planning moment when the trio
is ready.

---

## References

- **Parent doctrine:** `docs/MEMORY_TO_PROMPT_AUTOMATION_v0.1.md`
  (`ba1c9fa`).
- **Observability lane doctrine:**
  `docs/MEMORY_TO_PROMPT_AUTOMATION_v0.2.md` (`b455ae1`).
- **Pre-autonomy spine anchors:** Track A v0.1, Cluster 2 v0.1,
  Track B v0.1, Cluster 5 v0.1, MCP_CAPABILITY_BOUNDARY,
  TORMENT_AGENT_DOCTRINE_v0.1.
- **Implementation:**
  `torment_service/assembly_audit.py` (`214c9f7`);
  `torment_service/fabric.py` (`bda3652` — additive return-shape
  keys);
  `torment_service/app.py` (`bda3652` — request model + `/retrieve`
  wiring);
  `torment_fabric/live_agent/memory_bridge.py` (`bda3652` — kwarg).
- **Test surfaces:**
  `tests/test_assembly_audit.py` (`214c9f7`, 67 tests);
  `tests/test_assembly_audit_wiring.py` (`bda3652`, 15 tests);
  `tests/run_assembly_audit_smoke.py` (`39ca46e` + `eecae5d`,
  operator-run live smoke).
- **Lineage (scratch, preserved unchanged):**
  `scratch/MEMORY_TO_PROMPT_AUTOMATION_v0.2_OBSERVABILITY_FRAMING_DRAFT_2026-05-25.md`.
- **Pattern references (sibling checkpoints):**
  `docs/CHECKPOINT_2026-05_Q2D_TOOL_RESULT_DOCTRINE.md`,
  `docs/CHECKPOINT_2026-05_LEVEL_3_ST_RETRIEVAL.md`,
  `docs/CHECKPOINT_2026-05_TIER_2_RUNTIME_EVIDENCE.md`.
- **Orientation:** `docs/PROJECT_ORIENTATION_MAP.md` §2 (closed-arcs
  table updated to include this lane).
