# TORMENT Memory Fabric — v2.4.3 Release Notes

**Tag:** `v2.4.3`
**Branch:** `v2.4.3-consolidation`
**Headline:** Tool-Result Memory Lane — TORMENT can now remember externally obtained tool outputs as governed memory artifacts without crossing the boundary into tool execution or automation.

This release notes file consolidates everything that landed in the
`v2.4.3-consolidation` branch: the v2.4.3 feature work, the Claude Desktop
MCP integration hardening pass, the post-ship `tool_result_ingest` fix,
regression test coverage, and documentation hygiene.

For the narrative "what's new" version written for README readers, see
[`README.md`](../README.md) § "What's New in v2.4.3".
For the underlying architectural doctrine, see
[`DOCTRINE_v2.4.x.md`](DOCTRINE_v2.4.x.md).
For the capability boundary this feature operates under, see
[`MCP_CAPABILITY_BOUNDARY.md`](MCP_CAPABILITY_BOUNDARY.md).

---

## Headline feature: Tool-Result Memory Lane

### Tool-Result Ingest (`spine.py`, `app.py`, `mcp_server.py`)

New Spine-governed write operation `tool_result_ingest`:

- Dedicated HTTP endpoint: `POST /tool/ingest`
- Dedicated MCP tool: `torment_tool_result_ingest`
- Trust tier: `TRUST_INGEST` (0.6)
- Exposure tier: `guarded` (Tier 2)
- Path: fast path
- Provenance: stored via `ProvenanceV1.for_tool_result()` with
  `source_type="tool_result"` and `write_path="tool_ingest"`
- Scope: defaults to `private`

The Spine governs the write; no tool execution or dispatch occurs. External
tool outputs (API responses, search results, sensor readings) become
provenance-tagged memories that are visible in normal retrieval, visible in
`/debug/provenance`, and eligible as safe parents for archivist write-back
under the recursion safety policy.

### Tool-Result Retrieval Semantics (`fabric.py`)

Three provenance-aware changes in the retrieval pipeline:

1. **Retrieval discount.** Tool-result memories receive a configurable
   multiplier (default `0.85`, env `TORMENT_TOOL_RESULT_RETRIEVAL_DISCOUNT`)
   so external observations do not outrank the agent's experiential
   memories.
2. **Continuity bonus exclusion.** Self-thread and thread-window continuity
   bonuses are excluded for tool-result hits. Those bonuses exist for
   conversational continuity, not for ingested observations.
3. **Top-level provenance surfacing.** Every returned hit carries
   `provenance_type` and `provenance_tool_name` at the top level so
   downstream consumers can see provenance without payload parsing.

Full audit and rationale: [`TOOL_RESULT_RETRIEVAL_SEMANTICS.md`](TOOL_RESULT_RETRIEVAL_SEMANTICS.md).

### Provenance Normalization

Collective provenance writes now use `ProvenanceV1.for_collective_echo()`
instead of bare `"collective"` strings. All three comparison sites were
updated with backward-compatible checks that accept both legacy strings and
`ProvenanceV1` dicts:

- Hivemind gate
- Retrieval discount
- Compression classifier

The debug endpoint separator bug (`"::"` → `"/"` in agent key construction)
was fixed at the same time.

### Doctrine line

> *"TORMENT may remember what tools returned before it is ever allowed to
> decide what tools to run."*

---

## MCP client-integration hardening (Claude Desktop)

Four fixes that the cold-install and stdio-transport path required in
order for the MCP server to launch cleanly against Claude Desktop on a
fresh machine. None of these change feature surface; all of them change
what actually runs end-to-end.

### H1 — `mcp` dependency pinned in `requirements.txt`

Added:

```
# MCP surface (required for torment_service/mcp_server.py)
# Provides `mcp.server.fastmcp.FastMCP` — the stdio MCP server TORMENT exposes
# to Claude Desktop. Without this, cold install fails at import time.
mcp>=1.27.0,<2.0.0
```

Also annotated the Python floor: `# Python >= 3.10 required (MCP SDK floor)`.

Before this change, `requirements.txt` relied on an ambient install of the
`mcp` package, which cold installs on fresh machines did not provide. The
MCP server now installs correctly from a clean clone.

### H2 — hivemind debug prints redirected to `stderr`

The hivemind packet-emission path in `fabric.py` contained five debug
`print()` calls that wrote to `stdout`. Under the HTTP service this is
merely noisy, but under the stdio MCP transport it corrupts the JSON-RPC
framing because stdio uses `stdout` for protocol messages.

All five calls now write to `sys.stderr` via an explicit `file=_hm_sys.stderr`
argument. The `traceback.print_exc()` call in the same block now also takes
`file=_hm_sys.stderr`. No behavioral change for HTTP users; stdio MCP users
no longer see JSON-RPC frame corruption when the hivemind flag is enabled.

### H3 — `MCP_README.md` refreshed

Claude Desktop integration instructions updated to reflect the current
install path, environment variables, and verification steps.

### H4 — `MCP_SMOKE_TEST.md` added / refreshed

End-to-end smoke test procedure for verifying an MCP server install on a
fresh host: prerequisites, expected log lines, known failure modes.

---

## Post-ship fix: `tool_result_ingest` result_code (2026-04-11)

### Symptom

`tool_result_ingest` was returning `result_code="none"` on successful writes
instead of `result_code="stored"`. The memory was written correctly, the
provenance was correct, retrieval worked — only the response envelope
claimed nothing had happened.

### Root cause

Two-layer bug in `spine.py`:

1. `tool_result_ingest` was registered as an `OperationSpec` in
   `_ALWAYS_FAST` when the feature shipped, but the accompanying entry in
   `_OPERATION_RESULT_CODES` (the dict that maps operation names to the
   result code stamped on successful fast-path dispatch) was missing.
2. There was no consistency check to catch that class of drift at import
   time, so the bug shipped silently.

On a successful fast-path dispatch, `_OPERATION_RESULT_CODES.get(req.operation, RESULT_NONE)`
returned `RESULT_NONE` as the fallback, and `RESULT_NONE` got stamped on
the otherwise-successful response.

### Fix

Landed in `spine.py`:

1. Added the missing entry: `"tool_result_ingest": RESULT_STORED`.
2. Added an import-time consistency check that computes
   `{spec.name for spec in _ALWAYS_FAST} - set(_OPERATION_RESULT_CODES.keys())`
   and raises `RuntimeError` if the set is non-empty. This catches the
   class of bug — not just this instance — and forces the mapping to be
   updated at code-review time rather than failing silently at runtime.

Both parts of the fix are documented in-place with a comment referencing
the historical incident.

### Regression coverage

Three tests added to `tests/test_spine.py`:

- `TestDecisionResultCodes::test_tool_result_ingest_codes` — positive-path
  test that submits a `tool_result_ingest` request and asserts
  `result_code == RESULT_STORED`. This is the direct regression test: it
  would have failed under the original bug and passes now.
- `TestResultCodeMappingInvariant::test_every_fast_path_op_has_result_code` —
  same set-difference invariant that the startup check enforces, now run
  at test time so CI catches the class of regression before the code ever
  imports into a live MCP.
- `TestResultCodeMappingInvariant::test_result_code_mapping_has_no_orphan_entries` —
  reverse-direction drift detection: flags entries in
  `_OPERATION_RESULT_CODES` that no longer have a matching
  `OperationSpec`.

Full `tests/test_spine.py` run: **52 passed, 0 failures.**

### Live validation

Verified live against the MCP server via
`torment_tool_result_ingest` after the fix: the response envelope now
stamps `result_code: "stored"`, the memory persists with correct
provenance, and retrieval surfaces the memory with the 7-day half-life
cap and 0.85× retrieval discount applied as designed.

---

## Documentation updates

### Authoritative docs added in this branch

- [`WRITE_MIGRATION_FRAMING_v2.4.x.md`](WRITE_MIGRATION_FRAMING_v2.4.x.md) —
  step-6 framing doc for the memory-class / write-path provenance
  migration. Two-gate model (epistemic recovery + ancestry admission),
  six open decisions awaiting ratification, anchor: *"A migrated row is
  not merely rewritten metadata; it is a future-safe ancestor candidate."*
  Status: framing complete, decisions **not yet ratified** — no
  implementation work in v2.4.3.
- [`MCP_CROSS_HOST_FRAMING_v2.4.x.md`](MCP_CROSS_HOST_FRAMING_v2.4.x.md) —
  framing doc for eventual cross-host MCP expansion. Claude Desktop
  remains the active MCP host for v2.4.3; cross-host expansion is not in
  scope for this release.
- [`MCP_CROSS_HOST_RESEARCH_REQUEST.md`](MCP_CROSS_HOST_RESEARCH_REQUEST.md) —
  the research prompt that produced the cross-host findings referenced in
  the framing doc.
- `TORMENT MCP Cross-Host Research Findings.pdf` — research findings
  produced out-of-band, committed alongside the framing docs.

### Documentation hygiene updates

- [`TORMENT_ROADMAP_NOTES.md`](TORMENT_ROADMAP_NOTES.md) — marked the
  `tool_result_ingest` result_code bug as FIXED with full details;
  rewrote the "Outstanding small fix #2" item to point at
  [`PROVENANCE_STATUS_REGISTRY_v2.4.x.md`](PROVENANCE_STATUS_REGISTRY_v2.4.x.md)
  as canonical; replaced the "Next pick" section with the step-6 decision
  walk description and the doctrinal register.
- [`PROVENANCE_CONSTANTS_NOTES.md`](PROVENANCE_CONSTANTS_NOTES.md) —
  added a redirect block at the top pointing at the registry and framing
  doc as canonical. Original April-10 content is preserved below the
  redirect under the "understand and connect, do not delete" stance.

### Main README refresh

[`README.md`](../README.md) updated with:

- v2.4.3 section now includes MCP client-integration hardening and the
  post-ship result_code fix bullets.
- MCP server tool list now includes `torment_tool_result_ingest`.
- MCP server line now explicitly notes `mcp>=1.27.0` as pinned in
  `requirements.txt`.
- Docs table now references `MCP_SMOKE_TEST.md`, `DOCTRINE_v2.4.x.md`,
  `RECURSION_SAFETY_POLICY_v2.4.x.md`, `TOOL_RESULT_RETRIEVAL_SEMANTICS.md`,
  `TOOL_RESULT_LIFECYCLE_POLICY.md`, and `tools/README.md`.

### Tools directory discoverability

[`tools/README.md`](../tools/README.md) added with classification,
short descriptions, and example invocations for every tool in the
`tools/` directory:

- Maintenance: `compact_archive_memory.py`, `compact_core_memory.py`,
  `rebuild_sqlite_index.py`
- Migration: `migrate_embeddings_to_shards.py`
- Diagnostic: `verify_workspace_integrity.py`
- Ship gate: `verify.py`
- Visualization: `motif_field_viz.py`, `visualize_attractors.py`

`run_coherence_field.py` is explicitly marked as developer scratch with a
hardcoded stress-test path, **not** a supported general tool. Its fate
(fix, generalize, relocate under `examples/`, or delete) is deferred to
a later branch.

---

## Test coverage changes

- `tests/test_spine.py`: +3 tests (new `TestResultCodeMappingInvariant`
  class + 1 test in `TestDecisionResultCodes`).
  Full file: 52 passed.
- `tests/test_tool_result_ingest.py` — 41 tests (shipped in the v2.4.3
  feature work earlier in this branch, unchanged this session).

---

## Not in this release

Recorded here so nothing is accidentally assumed to have shipped:

- **Step 6 of the tactical provenance pass.** Steps 1–5 of the tactical
  provenance pass are closed at commit `9bb310c` (recursion guard +
  `normalize_parent` + working tree cleanup). Step 6 is the two-gate
  memory-class migration walk; it is framed but **not** ratified and
  **not** implemented. Six open decisions live in
  [`WRITE_MIGRATION_FRAMING_v2.4.x.md`](WRITE_MIGRATION_FRAMING_v2.4.x.md)
  and are the entry point for the next session.
- **`TORMENT_ARCHIVIST_WRITEBACK=1`.** Remains gated. The recursion guard
  has been live-validated against archivist-origin parents (step 5), but
  the archivist gate itself remains off. Re-verify the guard before
  flipping the flag.
- **Cross-host MCP expansion.** Claude Desktop remains the active MCP
  host. Framing doc landed in this branch, but no code paths for other
  hosts were added.
- **`run_coherence_field.py` repair.** Remains in-tree as dev scratch
  with its hardcoded path. Explicitly out of scope for v2.4.3 per the
  ratified tools/ folder branch-depth decision.
- **Line-ending policy.** The working tree contains CRLF/LF drift on
  roughly 83 files that is not reflected in any real content change.
  This branch deliberately does not renormalize, does not add
  `.gitattributes`, and does not make a repo-wide line-ending policy
  decision. Only files with real content changes were staged.

---

## Upgrade notes

No data migration required. Existing workspaces are compatible. If you
are cold-installing on a fresh host, `pip install -r requirements.txt`
will now pull `mcp>=1.27.0` which is required for the MCP server to
import. If you are running the stdio MCP server with hivemind enabled,
debug prints from packet emission now go to `stderr` as designed — any
log scraper that was reading them from `stdout` needs to be pointed at
`stderr` instead.
