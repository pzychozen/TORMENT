# Checkpoint — CodeQL non-C1 maintenance closure (2026-06)

**Date:** 2026-06-12
**Repo HEAD at closure:** `fc69c3c` (`test(codeql): align assembly-audit source inspection`)
**Nature:** docs-only closure record. This checkpoint documents a completed
CodeQL maintenance lane. It is **not** a design gate, **not** a doctrine
change, and **not** authorization for any new work.

This file exists so that the seams touched (or deliberately *not* touched)
during CodeQL cleanup are remembered and not "tidied up" casually later.

---

## 1. Operator-confirmed dashboard state

The operator confirmed the GitHub CodeQL dashboard reads **0 open alerts**
after the final intentional dismissals and the pushed fixes recorded below.
The dashboard remains the authoritative count.

---

## 2. Non-C1 closure scope (nine query families)

This lane addressed the following Python CodeQL families. Each alert was
traced individually (read-only archaeology first), then either resolved by a
narrow fix or preserved with an intentional dismissal rationale:

- `py/unused-import`
- `py/ineffectual-statement`
- `py/call/wrong-arguments`
- `py/print-during-import`
- `py/empty-except`
- `py/procedure-return-value-used`
- `py/catch-base-exception`
- `py/import-and-import-from`
- `py/should-use-with`

Every resolution was bounded to test/example/harness code. No production
module behavior was altered.

---

## 3. Landed commits (fixes and documentation)

| Commit | Subject | Family / site |
|---|---|---|
| `2225e65` | make observability MCP module dependency explicit | `py/unused-import` — `tests/test_observability_endpoints.py` (`_mcp_server_prime` made load-bearing at the `sys.modules` lookup site) |
| `92960b2` | remove redundant protocol stub ellipsis | `py/ineffectual-statement` — `tools/bench_adapters/__init__.py` (`ProviderAdapter.chat` docstring-only body) |
| `cebd5d7` | restore bounded-loop dotenv debug breadcrumb | `py/empty-except` — `character_memory_harness/run_bounded_loop.py::_load_dotenv_safely` (DEBUG breadcrumb, fail-open preserved) |
| `adedb71` | log archive teardown close failures at debug | `py/empty-except` — `tests/test_archive_memory.py` teardown `ArchiveStore.close()` (DEBUG breadcrumb; cleanup-race handler left documented) |
| `ff1a021` | document optional anthropic fallback in matrix chat | `py/empty-except` — `examples/ryuki_chat_v2_matrix.py` (`ImportError` handler comment for parity with `examples/ryuki_chat.py`) |
| `ddaeea1` | document dialogue-bench heuristic skips | `py/empty-except` — `tools/run_character_dialogue_bench.py::_detect_interesting_moments` (two narrow `(TypeError, ValueError)` handlers documented) |
| `fc69c3c` | align assembly-audit source inspection | `py/import-and-import-from` — `tests/test_assembly_audit.py` (whole-module source inspection moved to the repo-standard `sys.modules[...]` idiom) |

The `py/unused-import` family was closed across the maintenance lane,
culminating in `2225e65` (the final residue site); earlier ordinary
unused-import trims preceded it on the same lane.

---

## 4. Intentional dismissals (no code change)

Each of the following is a deliberate, correct construct that CodeQL flags as
a pattern but which is load-bearing or idiomatic. They were dismissed on the
dashboard with site-specific rationale, not edited:

- **Negative keyword-only test — #969** (`tests/test_assembly_audit.py`):
  positional call asserting `TypeError` locks the keyword-only contract of
  `build_assembly_audit`; the "wrong arguments" *is* the test.
- **Fatal PyYAML stderr breadcrumb** (`character_memory_harness/run_bounded_loop.py:74`):
  module-level `except ImportError` prints an actionable message to
  `sys.stderr` and immediately re-raises; intentional fail-fast in a script
  harness imported by nothing.
- **Lifecycle guard exact-None assertions — #940–#943**
  (`tests/test_lifecycle_authority_guard.py`):
  `assert_lifecycle_row_authoritative` is typed `-> None`; the tests bind and
  assert the `None` return to lock that contract and catch a future
  accidental non-None return.
- **BaseException worker transport — #974**
  (`tests/test_memory_kernel_runtime_isolation.py`):
  a daemon worker captures any failure into `errors[label]` for a parent
  `errors == {}` assertion; `BaseException` is deliberate so a non-Exception
  worker death (e.g. `SystemExit`, which threading otherwise swallows)
  surfaces rather than passing falsely. Transports, does not mask.
- **`unittest` + `mock` dual import — #988**
  (`tests/test_affect_attribution_ingest.py`):
  `import unittest` (for `TestCase`/`main`) and `from unittest import mock`
  (for `mock.patch`) are both independently used; canonical stdlib idiom.
- **Track-J object-form monkeypatch imports — #982, #983**
  (`tests/test_kernel_runtime_context_isolation.py`):
  `import torment_service.fabric as fabric_module` is the module-object
  patch target for the module-level `save_checkpoint`; `TormentFabric` is
  separately from-imported as the subject. Matches this file's own
  `import … as X_module` monkeypatch idiom; normalizing would break intra-file
  consistency.
- **TormentFabric explicit lifecycle alerts — #984, #985, and #975–#981**
  (`tests/test_checkpoint_runtime_context_compatibility.py`,
  `tests/test_g1_fail_closed_auto_canon.py`,
  `tests/test_kernel_runtime_context_isolation.py`):
  explicit construct + `try/finally: close()` is the unanimous suite
  convention (no `with TormentFabric` exists anywhere). `__exit__` is a pure
  `close()` delegate, so a `with` form is behavior-equivalent and would only
  create a lone style outlier. #976 additionally asserts post-close state
  clearance, where the explicit close is the behavior under observation.

---

## 5. Explicit non-effects

This closure changed none of the following:

- No production refactor.
- No schema change.
- No reader / projection change.
- No cognition-eligibility change.
- No authority-boundary change.
- No path-integrity change.
- No continuity-posture change.
- No database-doctrine change.
- No Memory Engine doctrine change.
- No character-freedom change.
- No recursive-temporal-semantics change.
- No new architecture gate opened.

The Memory Engine decision registry was **not** amended; nothing in it
changed.

---

## 6. Parked hygiene items (separate from CodeQL closure)

These are latent test-hygiene improvements surfaced during archaeology. They
are **not** CodeQL resolutions (try-widening does not clear `py/should-use-with`),
and they remain parked — to be picked up only as deliberate, convention-preserving
test maintenance, never as a side effect of an unrelated change:

- Widen the `try/finally` in the
  `tests/test_g1_fail_closed_auto_canon.py` `fabric()` fixture so
  `get_workspace`/`create_agent` run inside the `try` (setup-failure also
  closes).
- Add helper-local close-on-setup-failure protection inside
  `tests/test_kernel_runtime_context_isolation.py::_new_fabric` (its
  `get_workspace` runs after construction with no guard).
- Consider widening `try/finally` around the `monkeypatch.setattr` setup in
  the Track-J tests (`#977`–`#981` construct-then-setup-then-`try`).
- Retain the recursive temporal-domain contract as a separate future design
  item; it was not in scope here and must be designed deliberately, not
  back-doored through cleanup.

The Track-J parked gaps were assessed **low-risk** in their current file:
`_new_fabric()` sets `TORMENT_SQLITE_INDEX_ENABLE=0`, so no SQLite index
handles are opened there, and `:memory:` temp dirs retain
`TemporaryDirectory` cleanup backstops. The G1 fixture gap is parked
separately: it does not disable SQLite indexing, so this checkpoint makes no
no-handle-leak claim for that setup-failure path. No production defect was
established.

---

## 7. Database-design return note

CodeQL closure must **not** be read as permission to redesign storage. The
existing custom-database and Memory Engine doctrine stands unchanged. SQLite
remains a **sidecar / non-authoritative** index, exactly as before. Stage B
mechanics and database design remain **unopened** until separately authorized
in their own gate.

---

## 8. Validation evidence

- **Latest full Windows suite:** 3867 passed, 5 skipped, 22 subtests passed,
  79.27 seconds (`python -m pytest tests\ -q`, authoritative Windows run).
- **Focused assembly-audit suite after `fc69c3c`:** 76 passed in 0.25 seconds.

These counts are point-in-time evidence for this closure, not a permanent
baseline; re-establish before any future code-bearing slice.
