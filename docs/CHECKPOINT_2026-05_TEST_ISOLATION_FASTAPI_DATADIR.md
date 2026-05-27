# Checkpoint — Test Isolation Cleanup: FastAPI Stub + DATA_DIR Leak

**Date:** 2026-05-27
**Status:** Closed / Ratified — PASS
**Cluster:** Test-isolation hardening (sibling to v0.2.2 closure;
no doctrine change, no runtime logic change)
**Commit range:** `506bc4b` (FastAPI stub removal) + `8d925f2`
(DATA_DIR restoration). Parent: `c7dc915`. Prior load-bearing
checkpoint: `102c425` (v0.2.2 Candidate A closure).
**Framing:** *First v0.2.2 parked-item closure (parked item A:
FastAPI stub explicit-order artifact) plus a newly-discovered
class-of-bug fix (DATA_DIR app-reload fixture leak) repaired
across three identical fixtures. Test isolation only — no
runtime logic, no doctrine, no memory-to-prompt behavior, no
character_context behavior touched. `do_not_touch_torment_test_rig`
not touched, not inspected, not depended on.*

---

## Summary

Two test-isolation issues closed in one session:

1. **Parked item A from the v0.2.2 closure — closed.** The FastAPI
   stub installer in `tests/test_e2e_integration.py` and
   `tests/test_workspace_isolation.py` (named in the v0.2.2
   checkpoint as the unfixed half of the latent-bug pair) is
   removed entirely. Shape 1 from the audit: not tightened to
   `find_spec`, not extended — removed. `fastapi` is declared as a
   core required dependency in `requirements.txt`, and production
   modules (`app.py`, `auth.py`, `fabric.py`) hard-import it; the
   stub only supported an unsupported environment and could poison
   `sys.modules` with a partial `fastapi` lacking `fastapi.testclient`
   under explicit pytest file order.

2. **DATA_DIR app-reload fixture leak — discovered en route, fixed
   across the class.** The targeted four-file verification run for
   the FastAPI stub removal surfaced an unrelated failure in
   `test_app_security_hardening.py::TestSafeJoinDataDir::test_valid_path_stays_inside_data_dir`.
   Diagnosis: `torment_service/app.py` reads `TORMENT_DATA_DIR` at
   module-import time and binds both `DATA_DIR` and module-level
   `fabric` to it. Three test fixtures (`client(tmp_path,
   monkeypatch)`) followed the same broken pattern: `monkeypatch.setenv`
   + `importlib.reload(appmod)` + return TestClient with no
   `yield`/cleanup. After teardown, `monkeypatch` restored the env
   var but `appmod.DATA_DIR` and `appmod.fabric` stayed bound to
   the (now-deleted) tmp dir, leaking into any later test that
   read those globals. Fixed with Pattern A (manual env
   save/restore + try/yield/finally + post-restore reload) in all
   three fixtures.

The v0.2.2 closure's `3,513 passed` was therefore *also* order-luck
for the DATA_DIR class of bug. Alphabetical full-suite collection
ran the dependent (`test_app_security_hardening.py` — `app_` < `assembly_`)
before any of the three polluters (`assembly_`, `character_`,
`smoke_`), so the leak was invisible. GPT's targeted run with explicit
file order — `test_character_context_surfacing.py` before
`test_app_security_hardening.py` — is what exposed it.

Per the closure discipline of the session, no rig commands were
proposed, no repo-root pytest was used, no production code was
modified, and `_safe_join_data_dir` (the function whose assertion
failed) was not patched. The fix is in the polluter fixtures, not
in the security assertion.

---

## Arc — chronological (2026-05-27)

The work split into six explicit operator-authorized gates:

### Gate 1 — Audit-only pass for parked item A

Trio-ratified read-only audit answering four questions:
(1) where `_ensure_fastapi_stub()` is defined and installed;
(2) whether `fastapi` is a real dependency; (3) which tests need
the stubbed surface vs real `fastapi.testclient.TestClient`;
(4) whether `importlib.util.find_spec("fastapi") is None` is
materially safer than `"fastapi" not in sys.modules`. No edits.
Findings: stub installed at module level in two files, fastapi
is a core required dep, seven test files import the real
`TestClient` (stub does not provide it; partial-stub poisoning
under explicit order was the mechanism), `find_spec` is materially
safer but the stub serves no supported environment.

### Gate 2 — Shape 1 ratified (remove the stub entirely)

Trio ratified Shape 1 over Shape 2 (`find_spec` tightening) and
Shape 3 (extend the stub). Reasoning: core dep missing → tests
should fail clearly; do not silently fake framework modules.

### Gate 3 — FastAPI stub removal patched

Three removals per file × two files:
- `_ensure_fastapi_stub()` function definition deleted.
- Module-level `_ensure_fastapi_stub()` call deleted.
- Now-unused `import types` deleted.

Env-mutation deferral pattern (the *other* half of the v0.2.2
latent-bug pair, fixed at `2bfb7f0`) preserved verbatim. All
other code untouched.

### Gate 4 — Targeted verification surfaces DATA_DIR leak

Operator ran the GPT-ratified verification command from inside
`torment_fabric/`:

```
python -m pytest tests\test_e2e_integration.py tests\test_workspace_isolation.py tests\test_character_context_surfacing.py tests\test_app_security_hardening.py -q
```

Result: `1 failed, 63 passed`. The failure was in
`TestSafeJoinDataDir.test_valid_path_stays_inside_data_dir`, not
in any FastAPI-touching surface. Failure assertion: the path
returned by `_safe_join_data_dir()` started with a pytest tmp dir
(`C:\...\Temp\pytest-of-Notandi\pytest-34\test_blocks_unchanged_by_v0_2_0\data\...`),
not the repo `DATA_DIR`.

### Gate 5 — Audit for DATA_DIR leak

Trio-ratified read-only audit confirmed the mechanism: env-var-
based `DATA_DIR` + module reload at fixture setup + no cleanup =
permanent leak of `appmod.DATA_DIR` and `appmod.fabric` to the
tmp dir for the rest of the pytest session. Audit also found
that the same broken fixture shape exists in **three files**, not
one (copy-pasted verbatim):

- `tests/test_character_context_surfacing.py`
- `tests/test_smoke_api.py`
- `tests/test_assembly_audit_wiring.py`

Class-of-bug, not instance. Trio ratified Pattern A (manual env
save/restore + try/yield/finally + post-restore reload) across
all three. No `conftest.py` centralization in this gate (named
as a possible separately-ratifiable follow-up).

### Gate 6 — DATA_DIR fix patched and re-verified

All three fixtures restructured:

```python
@pytest.fixture()
def client(tmp_path):
    ...
    original_env = os.environ.get("TORMENT_DATA_DIR")
    os.environ["TORMENT_DATA_DIR"] = str(data_dir)

    import torment_service.app as appmod
    appmod = importlib.reload(appmod)
    try:
        yield TestClient(appmod.app)
    finally:
        if original_env is None:
            os.environ.pop("TORMENT_DATA_DIR", None)
        else:
            os.environ["TORMENT_DATA_DIR"] = original_env
        importlib.reload(appmod)
```

`monkeypatch` removed from the fixture signature in all three
(the only use was `setenv`). `import os` added to `test_smoke_api.py`
(the only file that didn't already have it). Verbose explanatory
docstring added so the pattern's reasoning survives readers who
might try to "simplify it back" to monkeypatch.

Three rounds of operator verification, all green: round 1
(same targeted four-file command, `64 passed`), round 2 (the
two newly-patched polluters paired with the dependent in
explicit order, `33 passed`), round 3 (full suite, `3,513
passed / 1 skipped / 22 subtests passed`).

---

## Commits in scope

```
506bc4b  test(isolation): remove FastAPI stub from integration fixtures
8d925f2  test(isolation): restore DATA_DIR after app reload fixtures
```

`506bc4b` closes parked item A from the v0.2.2 closure
(`docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_2_CHARACTER_CONTEXT.md`,
"Intentionally deferred" §A).

`8d925f2` is class-of-bug fix work that was not in the v0.2.2
parked-items list — surfaced en route during the gate 4
verification of `506bc4b`.

Parent of `506bc4b`: `c7dc915 docs(readme): add author voice
line at top reworded` (a small post-v0.2.2 README touch landed
on `origin/main`). Prior load-bearing checkpoint commit:
`102c425` (v0.2.2 Candidate A closure).

---

## Test evidence

| Round | Command | Result |
|---|---|---|
| Round 1 — targeted former-failure | `pytest tests\test_e2e_integration.py tests\test_workspace_isolation.py tests\test_character_context_surfacing.py tests\test_app_security_hardening.py -q` | 64 passed in 10.96s |
| Round 2 — proactive class-of-bug proof | `pytest tests\test_smoke_api.py tests\test_assembly_audit_wiring.py tests\test_app_security_hardening.py -q` | 33 passed in 5.39s |
| Round 3 — full suite | `pytest tests\ -q --ignore=tests\test_visualize_attractors.py` | 3,513 passed / 1 skipped / 22 subtests passed in 74.70s |

Round 3 result matches the v0.2.2 closure baseline exactly. Zero
drift, zero regression. The `--ignore=tests\test_visualize_attractors.py`
flag is the operator-established convention for full-suite runs;
that file is a separately-tracked unresolved item, not in scope
for this gate.

`git status --short` after both commits: empty (clean working
tree).

---

## What is now proven (load-bearing)

Five concrete claims:

1. **The FastAPI stub no longer exists in the test surface.** No
   file under `tests/` contains `_ensure_fastapi_stub`, `import
   types` for the purpose of building a stub, or `types.ModuleType`
   for that purpose. Verified by repo-wide grep returning zero
   matches. Tests now fail clearly with `ModuleNotFoundError:
   fastapi` if requirements aren't installed — which is the
   correct user-facing behavior given fastapi's core-dependency
   status.

2. **No DATA_DIR leak under any of the three formerly-broken
   fixtures.** Each `client` fixture now saves `TORMENT_DATA_DIR`,
   sets it to the tmp path, reloads `torment_service.app`, yields
   the TestClient, and in the `finally` block restores the env var
   and reloads again so `appmod.DATA_DIR` and `appmod.fabric`
   revert to their pre-fixture values. Verified by round 2 (the
   smoke_api + assembly_audit_wiring + app_security_hardening
   explicit-order run that would have failed before the fix).

3. **`_safe_join_data_dir()` and `test_app_security_hardening.py`
   are unchanged.** The security assertion was not weakened; the
   helper was not patched. The fix is in the polluters, not in the
   dependent.

4. **`appmod.DATA_DIR` and `appmod.fabric` revert correctly across
   fixture teardown.** The post-restore reload in the `finally`
   block is what makes this true. monkeypatch's env restoration
   alone would not have been sufficient because its timing runs
   after the fixture's own cleanup, so a reload-in-finally that
   relied on monkeypatch would still see the tmp env at reload
   time. The manual save/restore pattern is the load-bearing piece.

5. **The full suite is no longer order-luck for this class of bug.**
   Verified by the round-2 explicit-order proof. Future contributors
   can run pytest with explicit file ordering without re-discovering
   either of the two issues closed in this checkpoint.

---

## Ratified decisions

Six decisions reached and recorded across the session:

1. **Shape 1 (remove the stub) over Shape 2 (`find_spec` tightening)
   and Shape 3 (extend the stub).** Reasoning: core dep missing →
   tests should fail clearly; do not silently fake framework
   modules.
2. **Pattern A (manual env save/restore + reload-in-finally) over
   Pattern B (monkeypatch + `monkeypatch.undo()` + reload-in-finally).**
   Reasoning: explicit, no timing tricks, matches the project's
   lesson from the v0.2.2 env-mutation fix.
3. **Fix all three DATA_DIR fixture polluters, not just the one
   that surfaced.** Reasoning: class-of-bug, not instance. Fixing
   one would leave two known timebombs.
4. **No `conftest.py` centralization in this gate.** Reasoning:
   wider fixture-surface change; separately ratifiable later if
   wanted. Three identical patches now keeps the diff bounded.
5. **Two commits, not one.** Reasoning: separate logical changes
   deserve separate trace. Mirrors the v0.2.2 pattern of `7955652`
   (feature) + `2bfb7f0` (test isolation cleanup).
6. **New checkpoint doc, not in-place edit of the v0.2.2
   checkpoint.** Reasoning: v0.2.2 closed; heavy rewrite would
   blur its closure. This sibling doc records the parked-item-A
   closure and the new class-of-bug fix.

---

## Intentionally deferred

| # | Item | Deferred to |
|---|---|---|
| A | **`conftest.py` centralization of the three duplicate `client` fixtures.** They are byte-identical after this gate's patches. A shared `client` fixture in `tests/conftest.py` would deduplicate. Out of scope here because conftest changes affect collection-wide behavior. | Separate ratifiable slice if the trio wants it; not blocking. |
| B | **`do_not_touch_torment_test_rig/` repo-root discovery guard** (parked item B from the v0.2.2 closure). Not touched at any point this session per the explicit boundary; the rig is a thin lab table that must not become load-bearing for core TORMENT tests. | Inherited parked; status unchanged from v0.2.2 closure. |
| C | **`tests/test_visualize_attractors.py` ignore convention.** Pre-existing operator convention requires `--ignore=tests\test_visualize_attractors.py` on full-suite runs. Not addressed this session; recorded here so the next session knows it's an open item, not a quirk. | Separate slice. |
| D | **The seven inherited v0.2 parked items.** Block-count cleanup, `/agent/query` doctrine-vs-reality, `excluded` vs `filter_excluded` naming, archive-FILTER-A gap, `live_agent/` repo-root duplicate, ledger persistence, Ryuki real character workspace live check. All still parked. | Inherited parked; status unchanged from v0.2.2 closure. |

---

## Non-goals preserved through this checkpoint

- No production code change (zero edits to `torment_service/` or
  any non-test file).
- No doctrine amendment (Track A, Cluster 2, Track B, Cluster 5,
  MCP boundary, Agent Doctrine all unamended).
- No memory-to-prompt behavior change. `assembled_text`, `blocks`,
  `character_context`, FILTER-A, Q2-D, retrieval scoring, profile
  selection — all untouched.
- No character_context behavior change beyond fixture cleanup.
- No `do_not_touch_torment_test_rig/` usage, inspection, edit, or
  cleanup. Not touched at any point.
- No `_safe_join_data_dir()` patch and no weakening of
  `test_app_security_hardening.py` assertions.
- No `conftest.py` centralization.
- No use of `monkeypatch.undo()`.
- No new MCP surface.
- No scheduler / daemon / wall-clock trigger.
- No new tool family.
- No character workspace touched.
- No long-iteration tier opened.
- No env var introduction.
- No new top-level dependency.
- No commit to non-test files.

---

## Lesson recorded

Two classes of latent test-isolation bug were sitting in the suite
under alphabetical-collection-order luck:

1. **Module-import-time env mutation without restoration** (closed
   in v0.2.2 at `2bfb7f0` for `TORMENT_CHARACTER_ENABLE`). The
   pattern was: top-level `_setenv()` call at module load. Fix
   pattern: defer to `setUpModule()` + restore in `tearDownModule()`.
2. **Module-import-time globals re-bound via reload, not restored
   at fixture teardown** (closed in this checkpoint at `8d925f2`
   for `TORMENT_DATA_DIR` → `appmod.DATA_DIR` + `appmod.fabric`).
   The pattern was: monkeypatch env var + reload module + return
   without yield. Fix pattern: manual env save/restore +
   try/yield/finally + post-restore reload.

Both classes were invisible under default alphabetical pytest
collection because the dependent assertion happened to run before
the polluters. Both surfaced only under explicit pytest file
ordering. Future test additions that mutate module-level globals
should be reviewed against both patterns *before* landing; the
suite cannot lean on alphabetical luck to remain green.

The full-suite count `3,513 passed / 1 skipped / 22 subtests
passed` is preserved as the post-fix baseline. Any future
deviation from that count under the
`--ignore=tests\test_visualize_attractors.py` convention is a
signal.

---

## References

- **Prior closure checkpoint:** `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_2_CHARACTER_CONTEXT.md`
  (`102c425`). Named the FastAPI stub explicit-order artifact
  (parked item A); did not anticipate the DATA_DIR fixture leak.
- **Audit findings (FastAPI stub, this session):** rendered
  inline during gate 1, not filed as a separate doc per the
  audit-only discipline.
- **Audit findings (DATA_DIR leak, this session):** rendered
  inline during gate 5, not filed as a separate doc.
- **Patched files (FastAPI stub removal, `506bc4b`):**
  - `tests/test_e2e_integration.py` — stub function, install
    call, and unused `import types` removed.
  - `tests/test_workspace_isolation.py` — same three removals.
- **Patched files (DATA_DIR restoration, `8d925f2`):**
  - `tests/test_character_context_surfacing.py:145+` — fixture
    restructured to Pattern A.
  - `tests/test_smoke_api.py` — fixture restructured + `import os`
    added.
  - `tests/test_assembly_audit_wiring.py:49+` — fixture
    restructured to Pattern A.
- **Production surfaces referenced but not modified:**
  - `torment_service/app.py:30-31` — `DATA_DIR` read site.
  - `torment_service/app.py:35` — `_safe_join_data_dir` definition.
  - `torment_service/app.py:65` — `fabric = TormentFabric(data_dir=DATA_DIR)`.
  - `torment_service/spine.py:46-49` — already-tolerant
    `try/except ImportError` for fastapi.
  - `requirements.txt:3` — `fastapi>=0.115.0,<1.0.0` core dep
    declaration (the load-bearing fact for the Shape 1 decision).
