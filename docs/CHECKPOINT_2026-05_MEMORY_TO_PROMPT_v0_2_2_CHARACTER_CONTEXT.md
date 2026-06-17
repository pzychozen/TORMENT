# Checkpoint — Memory-to-Prompt v0.2.2 Candidate A (character_context surfacing)

**Date:** 2026-05-25
**Status:** Closed / Ratified — PASS
**Cluster:** Memory-to-Prompt Automation v0.2.x — character-context
surfacing sub-revision (first v0.2.x extension of the observability
lane)
**Commit range:** `7955652` (v0.2.2 Candidate A implementation) +
`2bfb7f0` (test-isolation cleanup that unblocked full-suite green)
**Framing:** *v0.2.2 first revision closed — character_context surfacing
on /retrieve, default-on stable ten-field subset, no prompt-text
change. Latent test-isolation bug discovered en route and fixed in the
same session.*

---

## Summary

This checkpoint closes the first v0.2.x extension of the
Memory-to-Prompt observability lane: **surface a stable ten-field
character_context subset on the `/retrieve` response**. Pure-additive
to the response shape — no change to `assembled_text`, `blocks`,
retrieval scoring, profile selection, or any prompt-facing behavior.
Default-on because the data is already computed in `fabric.query()`;
v0.2.2 just stops dropping it at the `/retrieve` handler boundary.

The arc spanned five conversation gates (planning → implementation →
test failures → investigation → cleanup) executed in a single working
session on 2026-05-25. The implementation commit landed cleanly
(`7955652`). Verification surfaced a latent test-isolation bug — two
unrelated test files (`test_e2e_integration.py`,
`test_workspace_isolation.py`) were mutating `os.environ["TORMENT_CHARACTER_ENABLE"]=0`
at module-import time without restoration, leaking the character-disabled
env into subsequent test modules. The bug pre-dated v0.2.2 (latent
through S4 / S5 / S6 / S7 commits) but was exposed by v0.2.2's
full-suite verification. Both polluter files were patched with the
same defer-to-setUpModule + capture-and-restore pattern; fix committed
as `2bfb7f0`. Final full-suite result: **3,513 passed / 1 skipped / 22
subtests passed**.

What this revision proves, narrowly stated: **`/retrieve` can surface
a stable subset of `character_context` (recommendations, tier
breakdown, spirit-return summary, drift state, character identity)
without changing the prompt the LLM sees, while preserving character
seed activation and the existing FILTER-A / Q2-D / assembly invariants.**
Nothing broader is claimed.

Per v0.2 §S3 Decision 1 (Option C — response-only), no disk-persistent
ledger is written. Per v0.2 §6 non-goals, no other extension lanes
were opened. The seven parked items inherited from the v0.2 closure
remain parked; two newly-parked items are recorded below (FastAPI stub
explicit-order artifact; `do_not_touch_torment_test_rig` repo-root
discovery risk).

---

## Arc — chronological (2026-05-25)

The work split into five gates with explicit operator authorization
between each:

### Gate 1 — v0.2.2 planning (Candidate A)

Reviewed the existing `character_context` production path
(`character.py:834` `assemble_character_context`), the `/retrieve`
handler (`app.py:1322`), and the assembler (`retrieval_assembler.py`).
Discovered that `character_context` already contains useful
character-shaping payload (`recommendations`, `tier_breakdown`,
`spirit_return_summary`) that the `/retrieve` handler was extracting
only three fields from (seed_text, character_name, drift_info), then
dropping the rest. Trio ratified Candidate A: surface a stable
ten-field subset on the response without changing assembled_text or
blocks. Default-on. No new opt-in flag.

### Gate 2 — Implementation

Three additive edits + one new test file:

- `torment_service/character.py:949–958` — pass-through three drift_info
  fields (`drift_direction`, `seed_basin_role`, `relational_count`)
  that were previously consumed by the recommendations logic but
  dropped from the return dict.
- `torment_service/app.py:1393–1421` — `/retrieve` handler surfaces a
  stable ten-field `character_context` subset on the response when
  `core_result["character_context"]` is non-None. Stable subset only;
  raw internal dict is NOT exposed. Omitted entirely when fabric
  didn't build one (no seed / character disabled).
- `tests/test_character_context_surfacing.py` *(new)* — 14 tests
  across `TestCharacterContextPassThrough` (5),
  `TestRetrieveResponseSurfacing` (6), `TestRetrieveBackwardCompat` (3).
  TestClient-based wiring tests; hand-constructed fixtures; no LLM,
  no API keys.

Targeted-test result: 14/14 passed. Committed as `7955652`.

### Gate 3 — Full-suite verification (initial)

Full-suite run revealed nine failures across `test_authority_lane_matrix.py`
(TestCharacterProvenanceBadge tests) and `test_character_context_surfacing.py`.
All nine had the same shape: character mode appeared to be off when
tests required it on. Failure assertion: `None != 'ryuki_v1'`
(character_id missing); v0.2.2 failures: `character_context` key
missing from `/retrieve` response.

### Gate 4 — Investigation

A wandering investigation that took longer than it should have. The
final correct analysis (after operator pushback):

- `ryuki_v1` is a **test seed_id string** that becomes an actual
  character only when `plant_seed()` runs during `create_agent` and
  writes a minimal CharacterState via the activation bridge at
  `fabric.py:2058`.
- The entire planting + activation block at `fabric.py:2017–2067` is
  gated by `if self._character_enable:`.
- `self._character_enable` is set once at `TormentFabric.__init__`
  (`fabric.py:626`) by reading `os.environ.get("TORMENT_CHARACTER_ENABLE", "1")`.
- Two test files were mutating that env var at **module import time**
  with no restoration:
  - `tests/test_e2e_integration.py:38–49` — `_setenv()` called at
    module top.
  - `tests/test_workspace_isolation.py:44–54` — identical broken
    pattern.
- Pytest collection imports test modules before any test runs. Once
  either polluter file was collected, `TORMENT_CHARACTER_ENABLE=0`
  persisted in `os.environ` for the entire pytest session, including
  the execution of alphabetically-earlier tests
  (`test_authority_lane_matrix.py`,
  `test_character_context_surfacing.py`).
- v0.2.2 was provably innocent: the implementation itself was correct,
  but it surfaced this latent test-isolation bug because v0.2.2
  required full-suite green by Path A discipline.

### Gate 5 — Test-isolation cleanup

Applied the same defer-to-setUpModule pattern to both polluter files:

- Captured original env values at module import time.
- Moved `_setenv()` from module-level execution into `setUpModule()`,
  which runs at test execution time (not collection).
- Added `tearDownModule()` to restore originals after each module's
  tests complete.

Both files patched. Targeted four-file run (e2e + workspace_isolation
+ authority_lane + character_context_surfacing): 51/51 passed. Full
suite: **3,513 passed / 1 skipped / 22 subtests passed**. Fix
committed as `2bfb7f0`.

---

## Commits in scope

```
7955652  feat(memory-to-prompt): surface character_context on /retrieve (v0.2.2 Candidate A)
2bfb7f0  test(isolation): scope env mutations in e2e and workspace isolation tests
```

`7955652` is the v0.2.2 implementation. `2bfb7f0` is the test-isolation
fix that landed alongside; it is not v0.2.2 work per se (the bug
pre-dated v0.2.2), but it is recorded here because v0.2.2's
full-suite verification surfaced it and v0.2.2 closure depends on it.

The parent observability lane doctrine (`b455ae1`), the v0.2 helper
implementation (`214c9f7`), the S5 wiring (`bda3652`), the S6 smoke
(`39ca46e` + `eecae5d`), and the v0.2 closure checkpoint (`0787723`)
remain the load-bearing references for the observability lane as a
whole; v0.2.2 is a sub-revision extending it.

---

## Test evidence

| Layer | Result |
|---|---|
| v0.2.2 targeted unit + wiring (`tests/test_character_context_surfacing.py`) | 14 passed |
| Authority-lane regression (`tests/test_authority_lane_matrix.py`) | 17 passed |
| Targeted 4-file (e2e + workspace_isolation + authority_lane + character_context_surfacing) | 51 passed |
| **Full suite (`pytest tests/`)** | **3,513 passed / 1 skipped / 22 subtests passed** |

The full-suite green-check is the load-bearing v0.2.2 evidence. The
test-isolation fix is what makes that claim honest; without it, the
suite was red with 9 failures from the latent pollution bug.

---

## What is now proven (load-bearing)

Five concrete claims, each with the anchor evidence:

1. **`/retrieve` surfaces a stable ten-field `character_context`
   subset** when `fabric.query()` produces one. Verified by
   `TestRetrieveResponseSurfacing` (6 tests). Fields:
   `seed_id`, `character_name`, `tier_breakdown`, `drift_score`,
   `drift_direction`, `drift_summary`, `recommendations`,
   `seed_basin_role`, `relational_count`, plus optional
   `spirit_return_summary` when spirit-return hits fired.
2. **`/retrieve` omits `character_context` cleanly when no seed is
   present** (character disabled / no seed planted). Verified by
   `test_character_context_omitted_when_no_seed`.
3. **`assembled_text` and `blocks` are NOT modified by v0.2.2.**
   Verified by `TestRetrieveBackwardCompat` (3 tests), including
   explicit assertions that recommendation strings do not leak into
   `assembled_text` and that the five FILL_ORDER block types are
   preserved.
4. **Character seed activation remains intact under test isolation.**
   After the test-isolation fix, `create_agent(seed_id="ryuki_v1")`
   reliably writes a minimal CharacterState; ingest reliably badges
   provenance with `character_id="ryuki_v1"`. Verified by
   `test_authority_lane_matrix.py::TestCharacterProvenanceBadge` (8
   tests, including `test_create_agent_with_seed_writes_minimal_character_state`).
5. **`TORMENT_CHARACTER_ENABLE=0` no longer leaks across test
   modules.** Verified by full-suite green (3,513 passed). The
   `_setenv()`-at-module-import pattern in e2e and workspace_isolation
   tests is replaced with `setUpModule()`-deferred mutation +
   `tearDownModule()` restoration.

What is **not** claimed:

- This revision does NOT introduce a voice-guidance block in
  `assembled_text` (Candidate B). That's a separate ratifiable slice;
  v0.2.2 explicitly stayed at Candidate A.
- This revision does NOT verify under ST embedder. Hash only.
- This revision does NOT exercise the surfacing path against a real
  character workspace (Ryuki etc.). The new tests use fresh disposable
  workspaces with synthetic seed text.
- This revision does NOT fix the FastAPI stub explicit-order artifact
  (see parked items below).
- This revision does NOT modify any production code beyond the
  three-field pass-through in `character.py` and the response-shape
  surfacing in `app.py`.

---

## Ratified decisions (inherited from v0.2.2 planning)

All seven Candidate A decisions from the v0.2.2 planning sequence are
installed:

1. **Candidate A only** — surface character_context on response;
   no voice-guidance block; no assembled_text change.
2. **Stable ten-field subset** — no raw internal dict exposure.
3. **Default-on** — data is already computed; no opt-in flag needed.
4. **`character.py` pass-through** for `drift_direction`,
   `seed_basin_role`, `relational_count` — pure additive to the
   returned dict.
5. **Conditional surfacing** — `character_context` key omitted
   entirely when fabric didn't build one.
6. **`spirit_return_summary` sub-key conditional on presence** —
   matches existing `assemble_character_context` pattern.
7. **Option β commit shape** — atomic implementation commit, then
   separate checkpoint commit.

---

## Intentionally deferred

### New deferred items (specific to this session's investigation)

| # | Item | Deferred to |
|---|---|---|
| A | **FastAPI stub explicit-order artifact.** `test_e2e_integration.py` and `test_workspace_isolation.py` install a minimal `fastapi` stub via `_ensure_fastapi_stub()` if `"fastapi" not in sys.modules`. When pytest is run with explicit file order that puts those files before `test_character_context_surfacing.py`, the stub shadows the real `fastapi` package and breaks `from fastapi.testclient import TestClient`. Does NOT trigger in alphabetical full-suite collection (where `c` < `e`, so real fastapi is imported first and the stub-install guard skips). | Separate small slice: either tighten the stub installer (verify fastapi is genuinely missing as a package, not just absent from sys.modules) or remove the stub entirely if fastapi is a hard test dependency. Not blocking. |
| B | **`do_not_touch_torment_test_rig/` repo-root discovery risk.** The rig is a sibling directory to `torment_fabric/`. `pytest tests/` run from `torment_fabric/` cannot recurse into it (confirmed: rig is OUTSIDE collection root). However, no `pytest.ini` / `pyproject.toml` / `setup.cfg` explicitly excludes the rig if anyone ever runs `pytest` from the repo root. | Separate small slice: add `pytest.ini` with `testpaths = tests` to `torment_fabric/` for belt-and-suspenders protection. Not blocking. |

### Inherited parked items (from v0.2 closure, all still parked)

1. v0.1 block-count cleanup (4-block → 5-block; `BLOCK_REFERENCE`).
2. v0.2 §4.3 `/agent/query` doctrine-vs-reality correction (Option A wired only `/retrieve`). **(2026-06-17: parked shorthand refined by read-only trace — when character_context is built, both endpoints surface it in different shapes (`/agent/query` raw `fabric.query` dict; `/retrieve` curated subset); API-response observability only; no parity/surfacing-policy decision. See `docs/PROJECT_ORIENTATION_MAP.md` §6.)**
3. `excluded` vs `filter_excluded` naming duplication on `Workspace.query()` return shape.
4. Archive-FILTER-A gap fix. **(CLOSED 2026-05-27 by v0.2.4-A1 — no longer parked; see `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_4_ARCHIVE_FILTER_A.md`.)**
5. `live_agent/` repo-root duplicate cleanup.
6. Ledger persistence (Option A vs Option B vs stay Option C).
7. Ryuki / real character workspace live check.

---

## Non-goals preserved through this checkpoint

- No production code change beyond the v0.2.2 surfacing edits.
- No test edits beyond the v0.2.2 new file and the two test-isolation
  patches.
- No doctrine amendment (v0.1, v0.2, Track A, Cluster 2, Track B,
  Cluster 5, MCP boundary, Agent Doctrine all unamended).
- No FastAPI stub cleanup (parked item A).
- No `do_not_touch_torment_test_rig/` modification (parked item B).
- No resolution of any of the seven inherited v0.2 parked items.
- No opening of any next v0.2.x or v0.3 candidate gate.
- No ledger persistence (Option C remains the ratified posture).
- No archive-FILTER-A fix.
- No `/agent/query` wiring.
- No env var introduction beyond what `_setenv()` in the two e2e/iso
  test files already sets (and now properly restores).
- No new MCP surface.
- No scheduler / daemon / wall-clock trigger.
- No new tool family.
- No character workspace touched.
- No long-iteration tier opened.

---

## Recommendation: pause here

The v0.2.2 first revision is closed with full-suite green evidence
and a clean test-isolation foundation. The disciplined move is to
lock it in and decide the next move with a fresh head.

Concretely:

- **Do not** auto-open the next v0.2.x gate (v0.2.3 spirit-return
  voice-cue verification, v0.2.4 archive-FILTER-A application, etc.).
- **Do not** bundle the FastAPI stub or rig-discovery cleanup into
  this commit.
- **Do not** auto-extend to ST embedder or Ryuki workspace.
- **Do not** open Candidate B (voice-guidance block in
  `assembled_text`) without a separate ratification cycle.

The next decision belongs to a separate planning moment when the trio
is ready.

---

## References

- **Parent observability lane doctrine:**
  `docs/MEMORY_TO_PROMPT_AUTOMATION_v0.2.md` (`b455ae1`).
- **Pre-autonomy spine anchors:** Track A v0.1, Cluster 2 v0.1,
  Track B v0.1, Cluster 5 v0.1, MCP_CAPABILITY_BOUNDARY,
  TORMENT_AGENT_DOCTRINE_v0.1.
- **Sibling closure checkpoint (v0.2 first revision):**
  `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_OBSERVABILITY_v0.2.md`
  (`0787723`). v0.2.2 inherits its seven parked items and its
  character-first hierarchy.
- **Implementation surfaces touched by v0.2.2:**
  - `torment_service/character.py:949–958` (three-field pass-through).
  - `torment_service/app.py:1393–1421` (response-shape surfacing).
  - `tests/test_character_context_surfacing.py` (14 tests).
- **Test-isolation cleanup (committed alongside):**
  - `tests/test_e2e_integration.py:38–80` (defer-to-setUpModule + restore).
  - `tests/test_workspace_isolation.py:44–94` (same pattern).
- **Read sites consulted during investigation:**
  - `torment_service/fabric.py:626` (`_character_enable` read).
  - `torment_service/fabric.py:1969–2069` (`create_agent` activation
    bridge — the GATE B at line 2017 is load-bearing).
  - `torment_service/fabric.py:4232+` (character_context production
    gate in `Workspace.query`).
  - `torment_service/character.py:834–953` (`assemble_character_context`
    return shape).
  - `torment_service/character.py:288+` (`plant_seed` — where seeds
    become characters).
- **Orientation:** `docs/PROJECT_ORIENTATION_MAP.md` §2 closed-arcs
  table updated to include this revision.
