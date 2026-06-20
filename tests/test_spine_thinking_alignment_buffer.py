"""
tests/test_spine_thinking_alignment_buffer.py — tests-only STRUCTURAL
characterization of the existing Spine <-> thinking-controller alignment
helper / ring buffer / read endpoint.

This is a tests-only structural characterization of CURRENT helpers and the
read endpoint. It is NOT Candidate Gate D, NOT Envelope Audit, NOT Layer-1
private thinking, NOT Document B runtime, NOT monitoring expansion, and NOT
database/substrate work.

Explicit scope notes (load-bearing):
  - ``_record_alignment`` is characterized as a helper / buffer path only.
  - These tests do NOT assert that the live Spine path currently populates the
    ring buffer (population is separately gated by TORMENT_THINKING_ADVISORY and
    is not proven here); the tests drive the helper directly.
  - They do NOT create or bless monitoring / autonomy semantics.
  - They do NOT create persistence or durable alignment state — the buffer is
    in-memory and bounded; these tests assert that boundary, they do not add to
    it.
  - They do NOT redact or gate endpoint content.
  - They do NOT freeze the exact note vocabulary or the exact summary schema —
    only a coarse documented subset and content-key ABSENCE are asserted.
  - They do NOT freeze the absence of any future governed Document B /
    Envelope Audit implementation.

Isolation: tests that mutate the shared module-level ``_alignment_buffer``
snapshot and restore it IN PLACE (preserving the list object identity the module
lock guards), so they do not leak state into other tests.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

import torment_service.spine as spine

_SERVICE_DIR = Path(__file__).resolve().parents[1] / "torment_service"

# Caller-supplied content key names that must never appear in a coarse
# alignment record / summary. (Names only — the schema itself is NOT frozen.)
_CONTENT_KEYS = frozenset({
    "raw_input", "prompt", "response_draft", "revised_text", "private_thought",
    "chain_of_thought", "rationale", "memory", "payload", "context", "blocks",
    "seed_text",
})

# Coarse primitive value types allowed in a content-free record.
_COARSE_PRIMS = (str, bool, int, float, type(None))


@pytest.fixture()
def isolated_buffer():
    """Snapshot and restore the shared ring buffer IN PLACE so buffer-mutating
    tests stay isolated and never leak alignment records into other tests."""
    with spine._alignment_lock:
        saved = list(spine._alignment_buffer)
        spine._alignment_buffer.clear()
    try:
        yield spine
    finally:
        with spine._alignment_lock:
            spine._alignment_buffer.clear()
            spine._alignment_buffer.extend(saved)


def _coarse_record(*, escalated=False, mode="fast", action="answer"):
    """Build one coarse alignment record via the real helper (no content)."""
    return spine._build_thinking_alignment(
        spine_path="memory.read",
        spine_op_class="read",
        spine_escalated=escalated,
        thinking_mode=mode,
        thinking_action=action,
    )


# ---------------------------------------------------------------------------
# 1. _record_alignment boundedness (helper / buffer path only)
# ---------------------------------------------------------------------------

class TestRecordAlignmentBounded:
    def test_buffer_max_is_positive_int(self):
        assert isinstance(spine._ALIGNMENT_BUFFER_MAX, int)
        assert spine._ALIGNMENT_BUFFER_MAX > 0

    def test_record_alignment_stays_within_bound(self, isolated_buffer):
        cap = spine._ALIGNMENT_BUFFER_MAX
        for i in range(cap + 75):
            spine._record_alignment({"spine_path": "p", "marker": i})
        assert len(spine._alignment_buffer) == cap

    def test_record_alignment_trims_oldest_keeps_recent(self, isolated_buffer):
        cap = spine._ALIGNMENT_BUFFER_MAX
        total = cap + 30
        for i in range(total):
            spine._record_alignment({"spine_path": "p", "marker": i})
        kept = [r.get("marker") for r in spine._alignment_buffer]
        # FIFO trim: the most recent `cap` markers survive; oldest are dropped.
        assert kept == list(range(total - cap, total))

    def test_record_alignment_stamps_ts_and_stays_content_free(self, isolated_buffer):
        spine._record_alignment(_coarse_record())
        rec = spine._alignment_buffer[-1]
        assert "ts" in rec and isinstance(rec["ts"], float)
        assert _CONTENT_KEYS.isdisjoint(rec.keys())


# ---------------------------------------------------------------------------
# 2. get_alignment_summary — bounded recent records + coarse summary counts
# ---------------------------------------------------------------------------

class TestGetAlignmentSummary:
    def test_empty_summary_is_zero_and_content_free(self, isolated_buffer):
        s = spine.get_alignment_summary(last_n=50)
        # coarse documented subset only — NOT an exact-schema assertion
        assert s["total"] == 0
        assert s["records"] == []
        assert _CONTENT_KEYS.isdisjoint(s.keys())

    def test_summary_bounds_records_to_last_n(self, isolated_buffer):
        for _ in range(12):
            spine._record_alignment(_coarse_record())
        s = spine.get_alignment_summary(last_n=5)
        assert s["total"] == 5
        assert isinstance(s["records"], list)
        assert len(s["records"]) == 5

    def test_summary_returns_all_when_last_n_exceeds_size(self, isolated_buffer):
        for _ in range(7):
            spine._record_alignment(_coarse_record())
        s = spine.get_alignment_summary(last_n=100)
        assert s["total"] == 7
        assert len(s["records"]) == 7

    def test_summary_counts_are_coarse_ints(self, isolated_buffer):
        for i in range(6):
            spine._record_alignment(_coarse_record(escalated=bool(i % 2)))
        s = spine.get_alignment_summary(last_n=50)
        assert isinstance(s["total"], int)
        assert isinstance(s["aligned"], int)
        assert isinstance(s["misaligned"], int)
        assert s["aligned"] + s["misaligned"] == s["total"]

    def test_summary_records_are_content_free_coarse_dicts(self, isolated_buffer):
        for i in range(4):
            spine._record_alignment(_coarse_record(escalated=bool(i % 2)))
        s = spine.get_alignment_summary(last_n=50)
        for rec in s["records"]:
            assert isinstance(rec, dict)
            assert _CONTENT_KEYS.isdisjoint(rec.keys())
            for v in rec.values():
                assert isinstance(v, _COARSE_PRIMS), (rec, v)


# ---------------------------------------------------------------------------
# 3. _build_thinking_alignment — coarse / content-free, note vocab NOT frozen
# ---------------------------------------------------------------------------

class TestBuildThinkingAlignmentContentFree:
    def test_record_has_no_content_keys(self):
        rec = _coarse_record(escalated=True, mode="deliberate", action="defer")
        assert isinstance(rec, dict)
        assert _CONTENT_KEYS.isdisjoint(rec.keys())

    def test_record_values_are_coarse_primitives(self):
        rec = _coarse_record(escalated=True)
        for k, v in rec.items():
            assert isinstance(v, _COARSE_PRIMS), (k, type(v))

    def test_aligned_is_bool_and_note_is_a_string(self):
        # `note` must be a coarse string field; its CONTENT is intentionally
        # NOT asserted — the divergence vocabulary may change.
        rec = _coarse_record(escalated=True, mode="fast")
        assert isinstance(rec.get("aligned"), bool)
        assert isinstance(rec.get("note"), str)

    def test_notes_across_varied_inputs_stay_string_and_noncontent(self):
        # Exercise several coarse input combinations; every note stays a plain
        # string (possibly empty) and never carries injected content. No exact
        # note text or vocabulary is asserted.
        for esc in (True, False):
            for mode in ("fast", "deliberate", "balanced", "reflective"):
                rec = _coarse_record(escalated=esc, mode=mode)
                assert isinstance(rec["note"], str)
                assert _CONTENT_KEYS.isdisjoint(rec.keys())


# ---------------------------------------------------------------------------
# 4. AST handler shape — /spine/thinking_alignment/recent and /spine/alignment
# ---------------------------------------------------------------------------
#
# Read-only handler-shape lock (AST-only; app.py is parsed as source, never
# imported or served). The two routes share one handler; it must call
# get_alignment_summary(...), clamp/bound last_n, and make no direct stateful
# retrieval / writer / mutation / persistence call. `query` and `measure_drift`
# are intentionally forbidden (read-only seam); persistence primitives
# (sqlite3.connect -> "connect", Path.write_text/write_bytes, json.dump) are
# forbidden so no durable alignment state is introduced.

_FORBIDDEN_HANDLER_CALLS = frozenset({
    "query", "ingest", "spawn_memory", "add_memory", "update_payload",
    "flush_node", "save_state", "append_record", "reinforce", "promote_chunk",
    "promote_chunk_endpoint", "gravity_correction", "measure_drift",
    "_maybe_emit_identity_anchor", "_maybe_emit_mood_drift", "process_proposals",
    "collective_reingest",
    # persistence primitives (durable-state guards)
    "connect", "write_text", "write_bytes", "dump",
})
_WRITE_MODE_CHARS = ("w", "a", "x", "+")


def _called_name(call):
    f = call.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return None


def _open_is_write(call):
    mode = call.args[1] if len(call.args) >= 2 else None
    for kw in call.keywords:
        if kw.arg == "mode":
            mode = kw.value
    if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
        return any(c in mode.value for c in _WRITE_MODE_CHARS)
    return False


def _find_get_handler(tree, path):
    """Return the module-level function carrying an `@<x>.get(path)` decorator
    (a function may carry several route decorators)."""
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if (
                isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Attribute)
                and dec.func.attr == "get"
                and dec.args
                and isinstance(dec.args[0], ast.Constant)
                and dec.args[0].value == path
            ):
                return node
    return None


class TestAlignmentReadEndpointHandlerShape:
    @pytest.fixture(scope="class")
    def app_tree(self):
        src = (_SERVICE_DIR / "app.py").read_text(encoding="utf-8")
        return ast.parse(src, filename="app.py")

    def test_both_routes_resolve_to_one_handler(self, app_tree):
        a = _find_get_handler(app_tree, "/spine/thinking_alignment/recent")
        b = _find_get_handler(app_tree, "/spine/alignment")
        assert a is not None, "missing /spine/thinking_alignment/recent handler"
        assert b is not None, "missing /spine/alignment handler"
        # both decorators are on the same function
        assert a is b

    def test_handler_calls_get_alignment_summary(self, app_tree):
        h = _find_get_handler(app_tree, "/spine/thinking_alignment/recent")
        calls = [
            n for n in ast.walk(h)
            if isinstance(n, ast.Call) and _called_name(n) == "get_alignment_summary"
        ]
        assert calls, "handler does not call get_alignment_summary(...)"

    def test_handler_clamps_last_n(self, app_tree):
        # last_n is bounded before use; assert both bounding primitives appear
        # in the handler body. (Shape proxy for clamping; the exact expression
        # is not frozen.)
        h = _find_get_handler(app_tree, "/spine/thinking_alignment/recent")
        names = {
            _called_name(n) for n in ast.walk(h) if isinstance(n, ast.Call)
        }
        assert "min" in names and "max" in names, (
            "handler does not clamp/bound last_n via min()/max()"
        )

    def test_handler_makes_no_stateful_or_persistence_calls(self, app_tree):
        h = _find_get_handler(app_tree, "/spine/thinking_alignment/recent")
        violations = []
        for n in ast.walk(h):
            if not isinstance(n, ast.Call):
                continue
            name = _called_name(n)
            if name in _FORBIDDEN_HANDLER_CALLS:
                violations.append((getattr(n, "lineno", -1), name))
            elif name == "write":
                violations.append((getattr(n, "lineno", -1), ".write"))
            elif name == "open" and _open_is_write(n):
                violations.append((getattr(n, "lineno", -1), "open(write)"))
        assert violations == [], (
            "alignment read handler makes forbidden stateful/persistence "
            f"call(s) (line, name): {violations!r}"
        )

    def test_forbidden_set_includes_read_only_and_persistence_guards(self):
        # Keep intent explicit: `query` / `measure_drift` (read-only seam) and
        # the persistence primitives are part of the forbidden set.
        for name in ("query", "measure_drift", "connect", "write_text",
                     "write_bytes", "dump"):
            assert name in _FORBIDDEN_HANDLER_CALLS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
