# Checkpoint — Q2-D Tool-Result Doctrine Arc

**Date:** 2026-05-24
**Status:** Closed / Ratified
**Cluster:** 5 § 9.3 Path C (Q2 lifecycle envelope)
**Commit range:** `6e8d537` (Q2-D Slice 5-c) .. `8733662` (canon-suppression doctrine)

---

## Summary

This checkpoint closes a multi-slice arc spanning the Q2-D lifecycle-envelope
soft migration, the external-inference operator-bridge slices, the live
verification of those slices on real provider APIs, and the live-evidence
ratification of a previously-undocumented contract mismatch in
`_fast_tool_result_ingest`.

The mismatch (external tool-result rows being auto-canonized by the kernel's
coherence score, despite the handler's docstring promising they are "NOT
identity-canonical") was caught by the lifecycle inspector during routine
post-ingest verification. The fix was ratified as **Interpretation 1**:
external tool-result rows must not become identity-canonical through
automatic promotion. Enforcement was added via a `suppress_canon` keyword on
`fabric.ingest`, used only by `_fast_tool_result_ingest`. Live A/B evidence
confirms the patch behaves as intended.

No retroactive migration was performed. The pre-fix rows on disk (eid=1,
eid=2 in `default/external_inference_smoke`) are preserved as historical
evidence of the prior behavior.

---

## Arc — chronological

### 1. Q2-D soft migration (background)

The Q2 lifecycle envelope (Shape D) was migrated across three protected-status
reader sites (governance, retention-tier derivation, compression-scorer) via
a lifecycle-first / legacy-fallback / warning-on-disagreement pattern. The
H1c stamp at `memory_graph._ensure_lifecycle_envelope` produces a canonical
envelope on every spawn; `read_lifecycle_envelope`,
`detect_lifecycle_legacy_marker_disagreement`, and
`assert_lifecycle_row_authoritative` are the read-side primitives.

The arc closed with `6e8d537` (Slice 5-c) and the character/agent regression
pack at `f509ce6`. No deprecation of legacy markers, no hard migration.

### 2. External inference smoke — Phase 1 (print-only)

`tests/run_external_inference_smoke.py` was added as an operator-run script
(not pytest) that validates the external-inference operational path using
the existing `.env`. One CLI invocation → one provider call → one printed
response. No memory ingest, no TORMENT-server dependency.

Live results (`189fff0`):
- OpenRouter / `google/gemini-2.5-flash` — PASS
- Anthropic / `claude-sonnet-4-5` — PASS

### 3. External inference smoke — Phase 2 (`--ingest`)

The same script gained an opt-in `--ingest` flag that POSTs the provider
response through the existing sanctioned write path: `POST /tool/ingest` →
Spine `tool_result_ingest` → `_fast_tool_result_ingest` → `fabric.ingest`.
No new write path was invented. Health-checks `GET /health` before posting,
exits 1 on any failure. Committed at `132c96b`; default base URL aligned to
`http://127.0.0.1:8787` at `87b4796`.

Live Phase-2 results — both runs returned an `eid` with `stored=True`.

### 4. Lifecycle inspector

`tools/inspect_lifecycle.py` was added (`912c385`) as a read-only operator
script that walks a private agent's `nodes.jsonl`, applies last-record-wins
semantics per eid, and prints `lifecycle_status` + `lifecycle_disagreement`
for each requested eid via the canonical helpers
`read_lifecycle_envelope` and `detect_lifecycle_legacy_marker_disagreement`.

Stdlib only, no fabric boot, no MCP wiring required, safe to run while the
server is up (jsonl is append-only).

### 5. Inspector finding — doctrine mismatch

Running the inspector on the two Phase-2 rows (eid=1, eid=2) surfaced an
unexpected envelope:

```
state                    = protected
set_by.actor             = system
set_by.via               = canon_set
lifecycle_disagreement   = null
```

Expected (per the original Q2-D plan documentation) was
`unset / system / ingest_unmarked`.

Trace:
- `_fast_tool_result_ingest` (`spine.py:895`) delegates to `fabric.ingest`.
- `fabric.ingest` (`fabric.py:2733` pre-fix) auto-canonized based on the
  kernel's coherence-driven `promotion_score >= 0.78`, with no check on
  `source_type`.
- Q2-D's H1c stamp correctly mirrored `canon=True` into the envelope.
- The "Q2-D bug" was not in Q2-D at all. Q2-D was reporting truthfully what
  the older `fabric.ingest` behavior actually did.
- The mismatch was between `_fast_tool_result_ingest`'s docstring promise
  ("NOT identity-canonical") and `fabric.ingest`'s coherence-driven canon
  stamp.

### 6. Doctrine ratification — Interpretation 1

Three readings were on the table:
- **Interpretation 1:** docstring is right; tool-result rows should not
  auto-canonize. Patch `fabric.ingest` to honor a suppression flag, passed
  by `_fast_tool_result_ingest`.
- **Interpretation 2:** docstring is stale; coherent tool answers deserve
  canon. Update the docstring.
- **Interpretation 3:** doctrine refinement larger than a slice.

**Ratified:** Interpretation 1. External tool-result content is
external/advisory origin; canonical/protected status should require an
explicit later promotion path, not automatic kernel-driven inference.

### 7. Doctrine patch (`8733662`)

Three files touched:

- **`torment_service/fabric.py`** — added keyword-only `suppress_canon: bool
  = False` to `ingest()`. Wrapped the canon expression as
  `canon=(False if suppress_canon else _auto_canon)`. Default behavior
  preserved for every existing caller.
- **`torment_service/spine.py`** — `_fast_tool_result_ingest` now passes
  `suppress_canon=True`. Docstring updated from aspirational to enforced.
- **`tests/test_tool_result_ingest.py`** — new `TestToolResultCanonSuppression`
  class with four tests:
  - tool_result via `submit_task` does not auto-canonize
  - tool_result lifecycle envelope is `UNSET / SYSTEM / INGEST_UNMARKED`
  - `fabric.ingest(..., suppress_canon=True)` forces `canon=False`
  - branch logic verified deterministically by monkeypatching
    `kernel.process` to force `promotion_score=1.0` and asserting both arms
    of the ternary

Focused test result: **45 passed in 2.48s**.

### 8. Live A/B evidence

Inspector output captured 2026-05-24 on
`workspace_id=default, agent_id=external_inference_smoke`:

| eid | written | provider/model | state | via | lifecycle_disagreement |
|---|---|---|---|---|---|
| 1 | pre-fix | openrouter / gemini-2.5-flash | `protected` | `canon_set` | null |
| 2 | pre-fix | anthropic / claude-sonnet-4-5 | `protected` | `canon_set` | null |
| 3 | post-fix | openrouter / gemini-2.5-flash | `unset` | `ingest_unmarked` | null |
| 4 | post-fix | openrouter / gemini-2.5-flash | `unset` | `ingest_unmarked` | null |

Decisive proof: the post-fix smoke that produced eid=4 logged
`promotion_score = 0.910...` in its raw response (`signals` block). That is
well above the 0.78 auto-canon threshold, so pre-patch the row would have
been stamped `PROTECTED / CANON_SET`. After the patch, with
`suppress_canon=True` flowing through `_fast_tool_result_ingest`, the row
landed as `UNSET / INGEST_UNMARKED`. The kernel's auto-canon decision was
correctly overridden.

`lifecycle_disagreement = null` on all four rows — including the pre-fix
ones — because the envelope correctly mirrored what the legacy markers
would have derived. Q2-D itself was never the bug.

---

## Commits in scope (this arc)

```
6e8d537  feat(cluster-5/q2): soft-migrate CompressionScorer._is_protected to lifecycle-first (Q2-D Slice 5-c)
f509ce6  test(cluster-5/q2): add character/agent Q2-D regression pack (post-soft-migration)
189fff0  test(external): add print-only inference smoke script
132c96b  test(external): add optional tool-result ingest smoke
912c385  tools: add read-only lifecycle inspector for memory rows
87b4796  test(external): align inference smoke default URL with TORMENT service
8733662  feat(spine): suppress auto-canon for tool_result_ingest (Q2-D doctrine)
```

---

## Ratified decisions

1. **Q2-D soft migration is operationally proven.** Lifecycle envelope reads
   correctly on real on-disk rows; disagreement detection returns expected
   results on both pre- and post-fix rows.
2. **External tool-result rows are not identity-canonical by automatic
   promotion.** `_fast_tool_result_ingest` enforces this via
   `suppress_canon=True`. Any future canonization of tool-result content
   must come from an explicit operator/review path.
3. **The lifecycle inspector is the read-only verification surface for live
   memory rows.** It uses canonical helpers, requires no MCP wiring, is safe
   to run while the TORMENT server is up.
4. **Pre-fix rows are preserved as historical evidence.** No retroactive
   migration; no raw file editing; no cleanup script. The pre-fix
   `PROTECTED / CANON_SET` rows in `default/external_inference_smoke` are
   intentional artifacts.

---

## Intentionally deferred (not part of this arc)

| Item | Status |
|---|---|
| Level 3 ST retrieval-quality smoke (`TORMENT_EMBED_PROVIDER=st`) | Available to run; left for a separate slice |
| HTTP lifecycle inspection parity (`/debug/provenance` extension) | Deferred; MCP `resource_provenance` is currently the only HTTP-adjacent inspection surface |
| Q2-D Slice 6 / hard migration of legacy protected markers | Deferred; operational evidence still being gathered under the soft-migration regime |
| Retroactive migration of eid=1, eid=2 | Deliberately not done — historical evidence of pre-fix behavior |
| Half-life cap / compression tier / reinforcement guard for tool-result rows | Proposed in `docs/TOOL_RESULT_LIFECYCLE_POLICY.md` §3 but not implemented in this arc |
| Phase 2b: extend `--ingest` to also fetch the resulting envelope | Deferred; would couple Phase 2 to envelope-inspection surface |

---

## References

- `docs/TOOL_RESULT_LIFECYCLE_POLICY.md` — updated in the same commit with a
  present-tense doctrine section documenting the canon-suppression rule
- `torment_service/fabric.py` — `ingest()` signature + canon ternary
- `torment_service/spine.py` — `_fast_tool_result_ingest` handler + docstring
- `torment_service/lifecycle.py` — Q2 envelope vocabulary, validator, H1c
  stamp, derivation, disagreement detector
- `torment_service/memory_graph.py` — `_ensure_lifecycle_envelope` H1c stamp
- `tools/inspect_lifecycle.py` — read-only operator inspector
- `tests/run_external_inference_smoke.py` — Phase 1 + Phase 2 smoke
- `tests/test_tool_result_ingest.py` — full test surface including
  `TestToolResultCanonSuppression`
