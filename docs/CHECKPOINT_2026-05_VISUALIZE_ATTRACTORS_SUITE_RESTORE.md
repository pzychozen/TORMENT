# Checkpoint — Visualize Attractors Suite Restore

**Date:** 2026-05-27
**Status:** Closed / Ratified — PASS (suite hygiene only, *not* a
visualization-science claim)
**Cluster:** Test-isolation hardening (sibling to the FastAPI stub +
DATA_DIR closure at `393c09c`; no doctrine change, no runtime logic
change, no visualization-algorithm change)
**Commit range:** `6c96f8d` (tools path fix) + `e0789d9` (live-data
skip guards). Parent: `393c09c` (prior test-isolation checkpoint).
**Framing:** *Removed the last "full suite has an asterisk"
artifact. `tests/test_visualize_attractors.py` no longer needs to
be excluded from `pytest tests\` runs. This restored the suite. It
did NOT complete the visualization science — the live-data tests
are honestly classified as live-data-dependent, but the deeper
question of what attractor visualization should scientifically
prove remains future work.*

---

## Summary

The previous operator convention for full-suite runs was:

```cmd
python -m pytest tests\ -q --ignore=tests\test_visualize_attractors.py
```

That `--ignore` flag was load-bearing: without it, the suite
collapsed at collection time on a `ModuleNotFoundError`. This gate
removes the asterisk.

The work split into two stages, each opened only after evidence:

1. **Stage 1 — Import path fix.** `tests/test_visualize_attractors.py`
   was failing at *collection*, not at any assertion. Root cause:
   `tools/visualize_attractors.py:51` did `from _viz_common import
   MotifInfo, ...` — a bare absolute import. Under direct script
   execution (`python tools/visualize_attractors.py ...`), `sys.path[0]`
   becomes `tools/`, so the bare import resolves. Under pytest
   collection from `torment_fabric/`, `sys.path` includes the project
   root but *not* `tools/`, so the import fails. Same pattern existed
   in `tools/motif_field_viz.py:43` — class-of-bug parity, latent
   because no test currently exercises it. Both files were patched
   with the same shape: a named-path setup block that adds `tools/`
   and `tools/..` to `sys.path` idempotently before the helper
   import. Direct script mode remained supported by keeping the
   bare `from _viz_common import ...` after the path setup.

2. **Stage 2 — Live-data skip guards.** After the import fix,
   collection succeeded and the file ran: `19 passed, 4 failed`.
   The four failures were all in `TestDataLoading._live` tests
   (motifs, character_state, trajectory_index, member_embeddings),
   each failing because the operator's local
   `data/workspaces/ryuki/agents/ryuki_nox/` was unpopulated. The
   `data/` directory is `.gitignored`, so fresh checkouts have
   nothing there; the live tests were never designed to pass on
   anything but a populated workspace. Fix: added a
   `_has_live_ryuki_workspace()` presence-check helper and a
   `LIVE_RYUKI_REQUIRED = pytest.mark.skipif(not
   _has_live_ryuki_workspace(), ...)` marker, applied to exactly
   the four proven-failing tests. Other tests in the same class —
   `test_load_motifs_missing`, `test_load_character_state_missing`,
   `test_load_core_events_live`, and the three `TestEndToEnd`
   tests — were left undecorated because the operator's run showed
   them passing.

The two-stage shape was disciplined: stage 2 was opened only after
stage 1's evidence (`19 passed, 4 failed`) confirmed that the
remaining failures had a distinct cause from the import bug. The
audit had predicted 8 live-data tests might fail; the operator's
actual run showed only 4. The smaller real number was the right
guide for the patch scope.

---

## Arc — chronological (2026-05-27)

### Gate 1 — Audit-only inspection of `test_visualize_attractors.py`

Read the file in full plus the `tools/visualize_attractors.py`
module it imports. Findings: 23 tests split into a portable
population (15 — `TestPCA`, `TestPlotRendering`, `TestHelpers`,
the `_missing` branches of `TestDataLoading`) and a live-data
population (8 named `_live` plus `TestEndToEnd`). The file's
`run_viz_tests()` standalone runner + `if __name__ == "__main__"`
block flagged it as a hybrid (pytest-compatible *and* standalone-
runnable). Loaders in `tools/visualize_attractors.py` confirmed
to use the current `data_dir/workspaces/<ws>/agents/<agent>/...`
layout — no layout drift. Suspected import-time `_viz_common`
failure flagged as the likely collection-time cause but could not
be confirmed without operator pytest output.

### Gate 2 — Operator-confirmed import failure

Operator ran `pytest tests\test_visualize_attractors.py -q`.
Failure: `ModuleNotFoundError: No module named '_viz_common'`,
exactly the import-time hypothesis from Gate 1. The collection
chain: `tests/test_visualize_attractors.py` → `tools.visualize_attractors`
→ `from _viz_common import ...` (bare, line 51) → resolution
fails because `tools/` is not on `sys.path`.

### Gate 3 — Audit of the import pattern across `tools/`

Grep for `_viz_common` returned three sites:
`tools/visualize_attractors.py:51`, `tools/motif_field_viz.py:43`,
and the helper module itself at `tools/_viz_common.py`. The two
viz scripts had byte-identical broken import shape. `tools/__init__.py`
was minimal (`# Tools package`). Documentation in
`docs/TOOLS_CORRECTNESS_AUDIT_v2.4.4.md:55` recorded the original
helper extraction recommendation; the import statement chosen at
that time worked under direct script mode but not under pytest
collection. Both viz scripts had argparse + `main()` + `__main__`
blocks documenting direct CLI usage, so any fix had to preserve
that mode.

### Gate 4 — Shape decision (Shape α vs Shape β) + scope decision

Two viable fix shapes:

- **Shape α — guarded `try/except`:** `try: from tools._viz_common
  import ... except ModuleNotFoundError: from _viz_common import ...`.
  Explicit, works in both modes.
- **Shape β — self-add `sys.path`:** add `tools/` to `sys.path` in
  a small named-path block at the top of each viz script, keep the
  bare `from _viz_common import ...`. Smaller diff, extends the
  pattern the files were already using.

Trio ratified Shape β + class-of-bug parity (patch both viz
scripts, not just the failing one). Reasoning: the files already
do `sys.path` manipulation, so adding `tools/` is a consistent
one-line extension; fixing only the failing file would leave
`motif_field_viz.py` as a known timebomb in the same shape.

### Gate 5 — Path fix patched

Two files patched with the same named-path block, idempotent
(skips entries already on `sys.path`):

```python
TOOLS_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.join(TOOLS_DIR, "..")

for path in (ROOT_DIR, TOOLS_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)
```

Bare `from _viz_common import ...` retained after the block.
Direct script mode preserved.

### Gate 6 — Stage-2 evidence + scope correction

Operator ran `pytest tests\test_visualize_attractors.py -q` again.
Result: `19 passed, 4 failed`. The four failures were
`test_load_motifs_live`, `test_load_character_state_live`,
`test_load_trajectory_index_live`, `test_load_member_embeddings_live`
— all in `TestDataLoading`, each failing with the same shape
(`motifs = {}`, `state = None`, `rows = []`, `dim = 0`) consistent
with missing local Ryuki workspace data.

Notable scope correction from the Gate 1 audit: the audit had
predicted 8 live-data-dependent tests (the 5 `_live` plus 3
`TestEndToEnd`). The operator's actual run showed only 4 failures.
The other 4 either pass (`test_load_core_events_live`) or
gracefully degrade through the visualization pipeline (the 3
`TestEndToEnd` cases, which assert PNG existence + size > 10KB —
the pipeline apparently writes a minimal "sparse" PNG even with
empty data). Patch scope was corrected to the four proven failures
only, per evidence over prediction.

### Gate 7 — Live-data skip guards patched

Added to `tests/test_visualize_attractors.py`:
- `import pytest`.
- `_has_live_ryuki_workspace()` presence-check helper using
  `character_state.json` + `index/memory_index.sqlite` as a coarse
  populated-workspace proxy.
- `LIVE_RYUKI_REQUIRED = pytest.mark.skipif(...)` module-level
  marker.
- `@LIVE_RYUKI_REQUIRED` decorator on exactly the four proven
  failures.

The portable 15 tests remain untouched. `test_load_core_events_live`
remained undecorated per operator evidence. `TestEndToEnd` tests
remained undecorated per operator evidence. No assertion was
weakened; no visualization logic was changed.

### Gate 8 — Final verification + commit

Operator ran the file in isolation:

```cmd
python -m pytest tests\test_visualize_attractors.py -q
```

Result: `19 passed, 4 skipped`. Operator then ran the full suite
*without* the historical ignore flag:

```cmd
python -m pytest tests\ -q
```

Result: `3,532 passed, 5 skipped, 22 subtests passed`. The
arithmetic checks out: prior baseline `3,513 passed / 1 skipped /
22 subtests` + the 19 newly-runnable portable tests = `3,532
passed`; prior `1 skipped` + 4 newly-skipped live-data tests = `5
skipped`. The full-suite asterisk is gone.

Two commits landed: `6c96f8d` (tools path fix) and `e0789d9`
(live-data skip guards). Working tree clean after both.

---

## Commits in scope

```
6c96f8d  tools(viz): add tools path for shared viz helpers
e0789d9  test(viz): skip live Ryuki data tests when workspace absent
```

`6c96f8d` is the class-of-bug fix across `tools/visualize_attractors.py`
and `tools/motif_field_viz.py`. `e0789d9` is the live-data skip
guard in `tests/test_visualize_attractors.py`.

Parent: `393c09c docs(checkpoint): test isolation FastAPI stub +
DATA_DIR leak closure`. Prior load-bearing context: `8d925f2` +
`506bc4b` (the test-isolation hardening this checkpoint extends).

---

## Test evidence

| Round | Command | Result |
|---|---|---|
| Pre-fix targeted | `pytest tests\test_visualize_attractors.py -q` | Collection failure (`ModuleNotFoundError: _viz_common`) |
| Post-import-fix targeted | `pytest tests\test_visualize_attractors.py -q` | 19 passed, 4 failed |
| Post-skip-guard targeted | `pytest tests\test_visualize_attractors.py -q` | 19 passed, 4 skipped |
| Full suite without `--ignore` | `pytest tests\ -q` | 3,532 passed, 5 skipped, 22 subtests passed |

The full-suite count exceeds the prior baseline by exactly the 19
newly-runnable portable tests in this file. The skip count
increased by exactly the 4 live-data tests now properly guarded.
No previously-passing test changed state.

`git status --short` after both commits: empty (clean working
tree).

---

## What is now proven (load-bearing)

Five concrete claims:

1. **`tests/test_visualize_attractors.py` collects under pytest
   without `--ignore`.** Verified by the post-import-fix run.
   The `tools/` directory is now on `sys.path` during pytest
   collection, allowing `_viz_common` to resolve.
2. **Direct script execution of `tools/visualize_attractors.py`
   and `tools/motif_field_viz.py` is preserved.** Both files
   retain the bare `from _viz_common import ...`; the new
   path-setup block is idempotent and runs in both contexts. Not
   re-verified live in this gate; the static argument is that
   `sys.path[0]` is `tools/` under direct-script mode regardless
   of the new block, so the bare import continues to resolve.
3. **`motif_field_viz.py` is no longer a latent timebomb for the
   same `_viz_common` import bug.** Patched in parity with
   `visualize_attractors.py`. No test currently exercises it, so
   this is class-of-bug hygiene rather than a green-test claim.
4. **The four live-Ryuki-data tests skip cleanly when no local
   workspace is present.** Verified by `19 passed, 4 skipped` on
   a checkout without populated `data/workspaces/ryuki/agents/ryuki_nox/`.
   The skip reason cites the exact path required, so the next
   reader knows what's missing.
5. **The full suite is no longer asterisked.** Verified by the
   final `3,532 passed, 5 skipped, 22 subtests passed` run with
   no `--ignore` flag. The operator-established `--ignore=tests\test_visualize_attractors.py`
   convention can be retired.

---

## Ratified decisions

Five decisions reached and recorded this session:

1. **Shape β (sys.path self-add) over Shape α (guarded `try/except`
   import).** Reasoning: the files already do `sys.path`
   manipulation; adding `tools/` is a consistent one-line
   extension; single bare import retained.
2. **Class-of-bug parity: fix both `visualize_attractors.py` and
   `motif_field_viz.py`.** Reasoning: same broken import pattern
   in both; fixing only the failing file leaves a known timebomb
   in the parity-shape.
3. **Skip exactly the four proven-failing tests, not the eight
   the audit predicted.** Reasoning: evidence over prediction.
   `test_load_core_events_live` and `TestEndToEnd` tests pass in
   the operator's current state for reasons not fully diagnosed
   (likely: sparse-data graceful degradation in the visualization
   pipeline, plus possible operator-local partial data). They
   stay undecorated until evidence says otherwise.
4. **Coarse two-file presence check for `_has_live_ryuki_workspace()`
   (character_state.json + memory_index.sqlite).** Reasoning:
   simpler than per-file checks; both files exist together in any
   meaningfully populated workspace; if either is missing the
   workspace isn't ready.
5. **Two commits, not one.** Reasoning: separate logical changes
   (path fix vs skip guards). Mirrors the project's pattern from
   the v0.2.2 + test-isolation gates.

---

## Intentionally deferred / Future work

This is the most important section of this checkpoint — it
records what we **did not** do, so the next visualization-related
session knows the starting state.

| # | Item | Notes |
|---|---|---|
| A | **Deterministic synthetic visualization fixture.** Build a small fixed-content `data/workspaces/synthetic_viz_test/...` (or in-test mock workspace builder) so the visualization tests can prove scientific correctness without depending on private/local Ryuki data. Closes the gap between "tests skip" and "tests prove the science." | Out of scope for this gate; named so future work can pick it up. |
| B | **Live-Ryuki-data tier decision.** The four guarded live tests should either remain optional local integration tests (current state) or move into a separate live-data/manual test tier with explicit invocation. The trio should decide whether `pytest -m live_data` or similar makes sense. | Out of scope; not blocking. |
| C | **Artifact-quality assertions for `TestEndToEnd`.** Today the end-to-end tests assert `os.path.exists(png_path)` and `os.path.getsize(png_path) > 10_000`. That's a "PNG was written" check, not "PNG is meaningful." Real artifact-quality validation (e.g., expected motif positions, expected basin shapes, expected color distributions on synthetic data) is unbuilt. | Future work; pairs with item A. |
| D | **`motif_field_viz.py` dedicated tests.** No `test_motif_field_viz.py` exists. The class-of-bug fix in this gate is parity-only; if the tool becomes load-bearing for science work it deserves its own test surface. | Future work; not blocking. |
| E | **Define "good attractor science."** What should visualization correctness *mean*? Candidate axes: stable PCA behavior across runs, motif geometry reproducibility, trajectory coherence, character-state overlay correctness, drift/field interpretability. Today the file proves none of these — it proves the tools don't crash. | Future work; the largest of the deferred items. |

---

## Non-goals preserved through this checkpoint

- No visualization algorithm change.
- No loader or data-layout change in `tools/visualize_attractors.py`,
  `tools/motif_field_viz.py`, or `tools/_viz_common.py`.
- No `_safe_join_data_dir` or other security-helper modification.
- No assertion weakening anywhere — the four guarded tests still
  assert `len > 0` / `is not None`; they just don't *run* without
  data.
- No deletion of the test file.
- No move or rename of the test file.
- No `conftest.py` modification.
- No production code change (`torment_service/` untouched).
- No doctrine amendment (Track A, Cluster 2, Track B, Cluster 5,
  MCP boundary, Agent Doctrine all unamended).
- No memory-to-prompt behavior change.
- No character_context behavior change.
- No `do_not_touch_torment_test_rig/` usage, inspection, edit, or
  cleanup.
- No automation work.
- No new MCP surface.
- No scheduler / daemon / wall-clock trigger.
- No new tool family.
- No character workspace touched.
- No long-iteration tier opened.
- No env var introduction.
- No new top-level dependency.

---

## Lesson recorded

The framing that matters most for the next reader:

> **This restored the full suite. It did not complete the
> visualization science.**

Three latent test-isolation bug classes have now been closed
across the v0.2.2 → test-isolation → visualize-attractors arc:

1. Module-import-time env mutation without restoration (closed in
   v0.2.2 at `2bfb7f0`).
2. Module-import-time globals re-bound via reload, not restored
   at fixture teardown (closed at `8d925f2`).
3. Bare absolute imports for sibling helpers in `tools/` modules
   that work under direct script mode but fail under pytest
   collection (closed at `6c96f8d`).

All three were invisible under default alphabetical pytest
collection / standard invocation paths. All three surfaced only
when the test surface was exercised differently (explicit file
order, fresh checkout, full-suite without ignore). The pattern
worth carrying forward: **the suite cannot lean on environmental
luck to remain green**. Future test additions that import from
`tools/`, mutate module-level globals, or depend on local
workspace data should be reviewed against these three patterns
before landing.

The post-fix baseline is now `3,532 passed / 5 skipped / 22
subtests passed` with no `--ignore` flag. Any future deviation
from that count is a signal.

---

## References

- **Prior closure checkpoint:** `docs/CHECKPOINT_2026-05_TEST_ISOLATION_FASTAPI_DATADIR.md`
  (`393c09c`). Closed parked item A (FastAPI stub) and the
  DATA_DIR class-of-bug. This gate closes the third latent
  test-isolation class.
- **v0.2.2 closure:** `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_2_CHARACTER_CONTEXT.md`
  (`102c425`). The original parked-items source.
- **Tools audit (v2.4.4):** `docs/TOOLS_CORRECTNESS_AUDIT_v2.4.4.md`.
  Recorded the original `_viz_common.py` extraction recommendation
  at §3; this gate's path fix is a follow-up to that extraction.
- **Patched files (path fix, `6c96f8d`):**
  - `tools/visualize_attractors.py` — sys.path block at line 48
    expanded to add `tools/` itself before the bare `_viz_common`
    import.
  - `tools/motif_field_viz.py` — same expansion at line 41 for
    parity.
- **Patched files (skip guards, `e0789d9`):**
  - `tests/test_visualize_attractors.py:10-17` — added `import
    pytest`.
  - `tests/test_visualize_attractors.py:34-58` — added
    `_has_live_ryuki_workspace()` helper and `LIVE_RYUKI_REQUIRED`
    marker after `DATA_DIR`.
  - `tests/test_visualize_attractors.py:127, 141, 153, 169` —
    `@LIVE_RYUKI_REQUIRED` decorator added to the four proven-
    failing live tests.
- **Production surfaces referenced but not modified:**
  - `tools/_viz_common.py` — shared helpers module (unchanged).
  - `tools/__init__.py` — `# Tools package` (unchanged).
  - The five other `tools/*.py` files that retain the
    single-line `sys.path.insert` (they don't import `_viz_common`
    so they don't need the `tools/` path entry).
