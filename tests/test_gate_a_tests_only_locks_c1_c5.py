"""
tests/test_gate_a_tests_only_locks_c1_c5.py — TORMENT Gate A tests-only
regression locks for candidates C1–C5.

Derived strictly from docs/TORMENT_GATE_A_TESTS_ONLY_LOCK_PROPOSAL_v0.1.md
(HEAD origin/main = 8e88d9c, Codex ACCEPT WITH CORRECTIONS carried). These
are CHARACTERIZATION / regression locks, not safety proofs.

What these locks deliberately DO NOT do (per the corrected proposal):
  - They do NOT claim any downstream safety.
  - They do NOT assert `fabric.query` is mutation-free / pure. `fabric.query`
    is treated as opaque and NOT mutation-free (retrieval-internal state
    effects exist).
  - They do NOT inspect, characterize, normalize, or bless the real
    `fabric.ingest` downstream fan-out.
  - They do NOT assert a broad "not candidate admission" runtime negative,
    and they do NOT freeze the absence of future governed Document B /
    private cognition / chamber / dream / candidate-store implementation.
  - C6 (absence of Document B / chamber / dream / candidate store / durable
    private state) is intentionally NOT tested here — testing that absence
    would create a tripwire against future governed implementation. The
    proposal rejects C6.

Boundaries used:
  - C1, C2 are static AST / resolved-call-name source locks (no import,
    no runtime, no substring matching).
  - C3 uses a fake/spy `fabric` boundary; the real `fabric.query` is never
    invoked.
  - C4 is a pure dataclass-shape lock.
  - C5 uses a fake-fabric spy plus controlled execute/review seams to
    characterize the *current* Phase-7 routing only.
"""
from __future__ import annotations

import ast
import dataclasses
import importlib
import os
from pathlib import Path

import pytest

# Project root (torment_fabric/) is placed on sys.path by tests/conftest.py.
_SERVICE_DIR = Path(__file__).resolve().parents[1] / "torment_service"


# ===========================================================================
# Shared AST helpers (resolved-call-name matching, NOT raw substring)
# ===========================================================================

# Forbidden direct-call names per proposal §3 (C1). Matched against the
# *resolved callee name* of an ast.Call — the Name id for `name(...)` or the
# Attribute attr for `x.y.name(...)`. This is exact-name matching: a call to
# `collective_reingest(...)` resolves to 'collective_reingest' and never to
# 'ingest'; a benign `reingest(...)` resolves to 'reingest' and is not in the
# set, so it is never flagged as an `ingest` call.
FORBIDDEN_CALL_NAMES = frozenset({
    "ingest",
    "spawn_memory",
    "add_memory",
    "update_payload",
    "flush_node",
    "save_state",
    "append_record",
    "reinforce",
    "promote_chunk",
    "promote_chunk_endpoint",
    "gravity_correction",
    "_maybe_emit_identity_anchor",
    "_maybe_emit_mood_drift",
    "process_proposals",
    "collective_reingest",
})

# Write/append modes that make a bare open(...) a write site.
_WRITE_MODE_CHARS = ("w", "a", "x", "+")


def _parse_module_source(filename: str) -> ast.AST:
    """Parse a torment_service source file into an AST. Source-only; the
    module is never imported, so this has no runtime/side effects."""
    path = _SERVICE_DIR / filename
    src = path.read_text(encoding="utf-8")
    return ast.parse(src, filename=str(path))


def _called_name(call_node: ast.Call):
    """Resolve the callee name of an ast.Call to a single identifier.

    Returns the attribute name for `x.y.name(...)`, the id for `name(...)`,
    or None when the callee is not a plain Name/Attribute. Pure resolved-name
    resolution — no string/substring search over source text.
    """
    func = call_node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _open_is_write(call_node: ast.Call) -> bool:
    """True if an `open(...)` call uses a write/append/exclusive mode given
    as a string literal (e.g. open(p, "w") / open(p, mode="a")). Non-literal
    modes are NOT flagged (conservative — avoids false positives)."""
    mode_node = None
    if len(call_node.args) >= 2:
        mode_node = call_node.args[1]
    for kw in call_node.keywords:
        if kw.arg == "mode":
            mode_node = kw.value
    if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
        return any(c in mode_node.value for c in _WRITE_MODE_CHARS)
    return False


def _forbidden_call_violations(tree: ast.AST):
    """Walk an AST and return [(lineno, name)] for every forbidden direct
    call: a forbidden callee name, any `.write(...)`, or a write-mode
    `open(...)`. Used by C1 only over advisory modules."""
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _called_name(node)
        if name in FORBIDDEN_CALL_NAMES:
            violations.append((getattr(node, "lineno", -1), name))
        elif name == "write":
            violations.append((getattr(node, "lineno", -1), ".write"))
        elif name == "open" and _open_is_write(node):
            violations.append((getattr(node, "lineno", -1), "open(write)"))
    return violations


def _find_route_handler(tree: ast.AST, method: str, path: str):
    """Return the module-level function decorated with `@<x>.<method>(path)`
    (e.g. @app.post("/agent/query")), or None."""
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if (
                isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Attribute)
                and dec.func.attr == method
                and dec.args
                and isinstance(dec.args[0], ast.Constant)
                and dec.args[0].value == path
            ):
                return node
    return None


# ===========================================================================
# C1 — advisory-module direct-call absence (AST / resolved-call-name)
# ===========================================================================
#
# Scope (explicitly named advisory/stance direct-call-absence lock):
#   thinking_controller.py, geometric_harvester.py, stance_policy.py.
# NOT in scope: app.py, agent_loop.py, fabric.py, spine.py.
# This asserts only that these advisory modules make no *direct* forbidden
# calls. It does NOT test stance behavior/correctness, downstream safety,
# `fabric.query`, or ingest internals.

ADVISORY_MODULES = (
    "thinking_controller.py",
    "geometric_harvester.py",
    "stance_policy.py",
)


class TestC1AdvisoryDirectCallAbsence:
    @pytest.mark.parametrize("module", ADVISORY_MODULES)
    def test_no_forbidden_direct_calls(self, module):
        tree = _parse_module_source(module)
        violations = _forbidden_call_violations(tree)
        assert violations == [], (
            f"{module}: forbidden direct call(s) found "
            f"(line, name): {violations!r}"
        )

    def test_resolved_name_matcher_does_not_flag_reingest_substring(self):
        """Regression guard for the matcher itself (proposal §3 warning).

        Locks two things at once:
          1. The matcher has teeth: a real `ingest(...)` / `collective_reingest(...)`
             call IS flagged (so a green run over real modules is meaningful).
          2. Raw-substring false positives are excluded: a benign `reingest(...)`
             resolves to 'reingest', which is NOT in FORBIDDEN_CALL_NAMES, and
             must NOT be flagged as an `ingest` call.
        """
        snippet = (
            "def f(x):\n"
            "    reingest(x)\n"               # benign: must NOT be flagged
            "    obj.collective_reingest(x)\n"  # forbidden (its own name)
            "    fabric.ingest(x)\n"          # forbidden
            "    note = 'reingest the data'\n"  # string literal: irrelevant
        )
        tree = ast.parse(snippet)
        flagged = {name for _, name in _forbidden_call_violations(tree)}
        assert "ingest" in flagged, "matcher failed to flag a real ingest() call"
        assert "collective_reingest" in flagged
        assert "reingest" not in flagged, (
            "matcher wrongly flagged the 'reingest' substring as an ingest call"
        )


# ===========================================================================
# C2 — /agent/query consumes only MemoryPlan (handler-shape lock, AST)
# ===========================================================================
#
# Current handler-shape lock only. Asserts the handler calls
# ThinkingController.think(), reads `_result.memory_plan`, exports only
# top_k_by_lane and weight_by_lane, and never references response_draft,
# review_result, or stance. It does NOT claim that discarding those fields
# is correct or permanent.

_C2_FORBIDDEN_RESULT_FIELDS = ("response_draft", "review_result", "stance")


class TestC2AgentQueryConsumesOnlyMemoryPlan:
    @pytest.fixture(scope="class")
    def handler(self):
        tree = _parse_module_source("app.py")
        node = _find_route_handler(tree, "post", "/agent/query")
        assert node is not None, "could not locate @app.post('/agent/query') handler"
        return node

    def test_calls_thinking_controller_think(self, handler):
        think_calls = [
            n for n in ast.walk(handler)
            if isinstance(n, ast.Call) and _called_name(n) == "think"
        ]
        assert think_calls, "handler does not call .think()"

    def test_reads_memory_plan_attribute(self, handler):
        reads = [
            n for n in ast.walk(handler)
            if isinstance(n, ast.Attribute) and n.attr == "memory_plan"
        ]
        assert reads, "handler does not read a .memory_plan attribute"

    def test_exports_only_top_k_and_weight_by_lane(self, handler):
        expected = {"top_k_by_lane", "weight_by_lane"}
        export_dicts = []
        for n in ast.walk(handler):
            if not isinstance(n, ast.Dict):
                continue
            keys = {
                k.value for k in n.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
            }
            if keys & expected:
                export_dicts.append(keys)
        assert export_dicts, "no MemoryPlan export dict literal found in handler"
        for keys in export_dicts:
            assert keys == expected, (
                f"handler export dict exposes more than the two lane fields: {keys!r}"
            )

    def test_does_not_consume_draft_review_or_stance(self, handler):
        leaked = sorted({
            n.attr for n in ast.walk(handler)
            if isinstance(n, ast.Attribute) and n.attr in _C2_FORBIDDEN_RESULT_FIELDS
        })
        assert leaked == [], (
            f"handler references ThinkingResult field(s) it must not consume: {leaked!r}"
        )


# ===========================================================================
# C3 — /agent/query no direct ingest/promote/gravity (fake/spy boundary)
# ===========================================================================
#
# Direct-call absence only, exercised through a fake/spy `fabric`. The real
# `fabric.query` is never invoked; it is treated as OPAQUE and NOT
# mutation-free. We assert the handler calls fabric.query exactly once and
# makes no direct call to ingest / promote_chunk / promote_chunk_endpoint /
# gravity_correction. We assert nothing about query's internals or purity.

_C3_FORBIDDEN_WRITERS = (
    "ingest",
    "promote_chunk",
    "promote_chunk_endpoint",
    "gravity_correction",
)


class _SpyFabric:
    """Minimal spy for the /agent/query boundary.

    Implements only what the handler legitimately reads (`query`,
    `get_kernel_runtime_context`); deliberately omits `character_store` so
    the handler's hasattr-guarded geometric branch is skipped. Forbidden
    writer methods are present purely so that a regression which *does* call
    them would be recorded — the current handler never calls them.
    """

    QUERY_SENTINEL = {"_spy": "opaque-query-result"}

    def __init__(self):
        self.calls = {}

    def _rec(self, name):
        self.calls[name] = self.calls.get(name, 0) + 1

    def get_kernel_runtime_context(self, *args, **kwargs):
        self._rec("get_kernel_runtime_context")
        return None

    def query(self, **kwargs):
        self._rec("query")
        return self.QUERY_SENTINEL

    def ingest(self, *args, **kwargs):
        self._rec("ingest")

    def promote_chunk(self, *args, **kwargs):
        self._rec("promote_chunk")

    def promote_chunk_endpoint(self, *args, **kwargs):
        self._rec("promote_chunk_endpoint")

    def gravity_correction(self, *args, **kwargs):
        self._rec("gravity_correction")


@pytest.fixture()
def appmod(tmp_path):
    """Isolated app module bound to a temp data dir (mirrors
    tests/test_smoke_api.py / test_assembly_audit_wiring.py). Manual env
    save/restore + reload-in-finally so later tests do not see a leaked
    TORMENT_DATA_DIR."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    original_env = os.environ.get("TORMENT_DATA_DIR")
    os.environ["TORMENT_DATA_DIR"] = str(data_dir)

    import torment_service.app as appmod
    appmod = importlib.reload(appmod)
    try:
        yield appmod
    finally:
        if original_env is None:
            os.environ.pop("TORMENT_DATA_DIR", None)
        else:
            os.environ["TORMENT_DATA_DIR"] = original_env
        importlib.reload(appmod)


class TestC3AgentQueryNoDirectWriters:
    def test_calls_query_and_no_direct_writers(self, appmod, monkeypatch):
        monkeypatch.setenv("TORMENT_THINKING_ADVISORY", "1")
        spy = _SpyFabric()
        monkeypatch.setattr(appmod, "fabric", spy)

        req = appmod.QueryReq(
            workspace_id="ws", agent_id="ag", query="hello", top_k=3,
        )
        out = appmod.query(req)

        # Retrieval boundary is reached exactly once.
        assert spy.calls.get("query", 0) == 1
        # No direct ingest/promote/gravity calls from the handler path.
        for name in _C3_FORBIDDEN_WRITERS:
            assert spy.calls.get(name, 0) == 0, (
                f"handler made a direct call to fabric.{name}()"
            )

    def test_query_result_is_opaque_passthrough(self, appmod, monkeypatch):
        """The handler returns whatever fabric.query returned, unchanged. We
        assert pass-through identity ONLY — never any property of query's
        internals, and never that query is mutation-free."""
        monkeypatch.setenv("TORMENT_THINKING_ADVISORY", "1")
        spy = _SpyFabric()
        monkeypatch.setattr(appmod, "fabric", spy)

        req = appmod.QueryReq(
            workspace_id="ws", agent_id="ag", query="hello", top_k=3,
        )
        out = appmod.query(req)
        assert out is spy.QUERY_SENTINEL


# ===========================================================================
# C4 — MemoryPlan shape only
# ===========================================================================
#
# Shape/construction lock only. Asserts the dataclass exposes the lane
# booleans, top_k_by_lane, weight_by_lane, and safety_constraints with the
# expected container types. It does NOT test fabric.query clamp behavior,
# authority/admission influence, retrieval/query mutation, or lane behavior
# inside fabric.query.

_LANE_BOOLEANS = (
    "retrieve_core",
    "retrieve_relational",
    "retrieve_archive",
    "retrieve_deep",
    "retrieve_collective",
    "retrieve_character_state",
    "retrieve_srg_state",
)


class TestC4MemoryPlanShape:
    def test_is_dataclass(self):
        from torment_service.thinking_models import MemoryPlan
        assert dataclasses.is_dataclass(MemoryPlan)

    def test_lane_booleans_present_and_bool(self):
        from torment_service.thinking_models import MemoryPlan
        field_names = {f.name for f in dataclasses.fields(MemoryPlan)}
        mp = MemoryPlan()
        for name in _LANE_BOOLEANS:
            assert name in field_names, f"missing lane boolean field {name!r}"
            assert isinstance(getattr(mp, name), bool), (
                f"lane field {name!r} is not a bool"
            )

    def test_top_k_and_weight_by_lane_are_dicts(self):
        from torment_service.thinking_models import MemoryPlan
        field_names = {f.name for f in dataclasses.fields(MemoryPlan)}
        mp = MemoryPlan()
        assert "top_k_by_lane" in field_names
        assert "weight_by_lane" in field_names
        assert isinstance(mp.top_k_by_lane, dict)
        assert isinstance(mp.weight_by_lane, dict)

    def test_safety_constraints_is_list(self):
        from torment_service.thinking_models import MemoryPlan
        field_names = {f.name for f in dataclasses.fields(MemoryPlan)}
        mp = MemoryPlan()
        assert "safety_constraints" in field_names
        assert isinstance(mp.safety_constraints, list)


# ===========================================================================
# C5 — Phase-7 ordinary-ingest routing characterization (fake-fabric spy)
# ===========================================================================
#
# Characterizes the CURRENT Phase-7 route in AgentRunner.run_turn only, via a
# fake fabric spy plus controlled execute/review seams (deliberate_only stays
# real). Asserts:
#   - a non-blocked / non-no-op / response-present turn calls fabric.ingest
#     exactly once, with text produced by _build_ingest_summary;
#   - blocked / no-op / no-response turns skip ingest;
#   - the Phase-7 path touches no candidate / admission / promotion-force API.
# The fake `ingest` records only; it has NO downstream fan-out, so this test
# neither inspects nor blesses the real fabric.ingest fan-out. It does NOT
# assert a broad "not candidate admission" negative and does NOT freeze any
# future governed Document B / private-cognition implementation.

# Forbidden non-ingest writer / promotion-force / candidate-admission names
# the Phase-7 route must not call.
_C5_FORBIDDEN_FABRIC_CALLS = (
    "promote_chunk",
    "promote_chunk_endpoint",
    "process_proposals",
    "collective_reingest",
    "spawn_memory",
    "add_memory",
    "reinforce",
)


class _C5SpyFabric:
    """Fake FabricHandle for the outer loop. Records ingest/measure_drift/
    gravity_correction (the only methods run_turn legitimately calls) plus a
    set of forbidden promotion/candidate/admission methods that must remain
    uncalled. `ingest` records only — no downstream fan-out is modeled."""

    def __init__(self, drift_return=None):
        self.drift_return = drift_return
        self.ingest_calls = []
        self.measure_drift_calls = []
        self.gravity_correction_calls = []
        self.forbidden = {name: 0 for name in _C5_FORBIDDEN_FABRIC_CALLS}

    def ingest(self, workspace_id, agent_id, text, step):
        self.ingest_calls.append(
            {"workspace_id": workspace_id, "agent_id": agent_id,
             "text": text, "step": step}
        )
        return {"status": "ok"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append(
            {"workspace_id": workspace_id, "agent_id": agent_id}
        )
        return self.drift_return

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append(
            {"workspace_id": workspace_id, "agent_id": agent_id,
             "drift_info": drift_info}
        )

    # Forbidden promotion/candidate/admission surfaces — present so a
    # regression that reaches them is recorded; never called today.
    def promote_chunk(self, *a, **k):
        self.forbidden["promote_chunk"] += 1

    def promote_chunk_endpoint(self, *a, **k):
        self.forbidden["promote_chunk_endpoint"] += 1

    def process_proposals(self, *a, **k):
        self.forbidden["process_proposals"] += 1

    def collective_reingest(self, *a, **k):
        self.forbidden["collective_reingest"] += 1

    def spawn_memory(self, *a, **k):
        self.forbidden["spawn_memory"] += 1

    def add_memory(self, *a, **k):
        self.forbidden["add_memory"] += 1

    def reinforce(self, *a, **k):
        self.forbidden["reinforce"] += 1

    def nonzero_forbidden(self):
        return {k: v for k, v in self.forbidden.items() if v}


class _C5FakeLLM:
    """Unused once _execute is stubbed; present to satisfy the constructor."""

    def complete(self, system_prompt, messages, tools=None):
        from torment_service.agent_loop import LLMResponse
        return LLMResponse(text="unused")


def _c5_make_runner(drift_return=None):
    from torment_service.agent_loop import AgentRunner
    from torment_service.thinking_controller import ThinkingController
    fabric = _C5SpyFabric(drift_return=drift_return)
    runner = AgentRunner(
        controller=ThinkingController(),
        fabric=fabric,
        llm_client=_C5FakeLLM(),
    )
    return runner, fabric


def _c5_stub_execute(runner, monkeypatch, *, response_text, no_op):
    from torment_service.agent_loop import ExecutionOutcome
    monkeypatch.setattr(
        runner, "_execute",
        lambda **kw: ExecutionOutcome(
            response_text=response_text, no_op=no_op, llm_called=True,
        ),
    )


def _c5_stub_review(runner, monkeypatch, *, blocked):
    from torment_service.thinking_models import ReviewResult
    monkeypatch.setattr(
        runner.controller, "review",
        lambda **kw: ReviewResult(approved=not blocked, blocked=blocked),
    )


class TestC5Phase7RoutingCharacterization:
    def test_content_turn_ingests_once_with_build_summary_text(self, monkeypatch):
        from torment_service.agent_loop import Observation
        runner, fabric = _c5_make_runner(drift_return=None)
        _c5_stub_execute(runner, monkeypatch, response_text="ANSWER-TEXT", no_op=False)
        _c5_stub_review(runner, monkeypatch, blocked=False)

        obs = Observation(text="tell me something")
        result = runner.run_turn(
            workspace_id="ws", agent_id="ag", observation=obs, step=7,
        )

        # Exactly one ingest, with the compact summary from _build_ingest_summary.
        assert len(fabric.ingest_calls) == 1
        expected_text = runner._build_ingest_summary(
            observation=obs, response_text="ANSWER-TEXT",
        )
        assert fabric.ingest_calls[0]["text"] == expected_text
        assert fabric.ingest_calls[0]["step"] == 7
        assert fabric.ingest_calls[0]["workspace_id"] == "ws"
        assert result.ingest_attempted is True

        # Phase-7 path touched no promotion/candidate/admission API.
        assert fabric.nonzero_forbidden() == {}

    def test_blocked_turn_skips_ingest(self, monkeypatch):
        from torment_service.agent_loop import Observation
        runner, fabric = _c5_make_runner(drift_return=None)
        # Execution produced a draft, but review vetoes Phase-7 advancement.
        _c5_stub_execute(runner, monkeypatch, response_text="DRAFT", no_op=False)
        _c5_stub_review(runner, monkeypatch, blocked=True)

        result = runner.run_turn(
            workspace_id="ws", agent_id="ag",
            observation=Observation(text="tell me something"), step=1,
        )
        assert len(fabric.ingest_calls) == 0
        assert result.ingest_attempted is False
        assert fabric.nonzero_forbidden() == {}

    def test_no_op_turn_skips_ingest(self, monkeypatch):
        from torment_service.agent_loop import Observation
        runner, fabric = _c5_make_runner(drift_return=None)
        _c5_stub_execute(runner, monkeypatch, response_text=None, no_op=True)
        _c5_stub_review(runner, monkeypatch, blocked=False)

        result = runner.run_turn(
            workspace_id="ws", agent_id="ag",
            observation=Observation(text="ok"), step=1,
        )
        assert len(fabric.ingest_calls) == 0
        assert result.ingest_attempted is False
        assert fabric.nonzero_forbidden() == {}

    def test_no_response_turn_skips_ingest(self, monkeypatch):
        from torment_service.agent_loop import Observation
        runner, fabric = _c5_make_runner(drift_return=None)
        # Not blocked, not no_op, but no response text → inner gate skips ingest.
        _c5_stub_execute(runner, monkeypatch, response_text=None, no_op=False)
        _c5_stub_review(runner, monkeypatch, blocked=False)

        result = runner.run_turn(
            workspace_id="ws", agent_id="ag",
            observation=Observation(text="ok"), step=1,
        )
        assert len(fabric.ingest_calls) == 0
        assert result.ingest_attempted is False
        assert fabric.nonzero_forbidden() == {}


# ===========================================================================
# C2 companion (minimal) — /agent/query does not wire review output-control
# fields (blocked / revised_text) into the live path
# ===========================================================================
#
# Live-advisory companion seam ONLY (NOT a Candidate Gate D invariant): proves
# the CURRENT /agent/query handler does not consume review output-control
# fields, i.e. review.blocked / review.revised_text are not turned into live
# output control on the query path. This complements C2 (which excludes
# response_draft / review_result / stance by name) and supports the
# ReflectionTrace non-reentry boundary: the live advisory seam exposes no
# output-control re-entry. Like C2, this is a CURRENT handler-shape
# characterization, NOT a claim that the seam is correct or permanent, and it
# does NOT freeze the absence of any future governed Document B / Envelope
# Audit implementation (a later authorized change would update it via review).

_REVIEW_OUTPUT_CONTROL_FIELDS = ("blocked", "revised_text")


class TestC2CompanionReviewFieldsNotLiveOutputControl:
    @pytest.fixture(scope="class")
    def handler(self):
        tree = _parse_module_source("app.py")
        node = _find_route_handler(tree, "post", "/agent/query")
        assert node is not None, "could not locate @app.post('/agent/query') handler"
        return node

    def test_handler_does_not_consume_review_output_control_fields(self, handler):
        leaked = sorted({
            n.attr for n in ast.walk(handler)
            if isinstance(n, ast.Attribute) and n.attr in _REVIEW_OUTPUT_CONTROL_FIELDS
        })
        assert leaked == [], (
            "/agent/query handler references review output-control field(s) "
            f"{leaked!r}; review.blocked / review.revised_text must not be wired "
            "into live output control (current-shape characterization, not a "
            "permanence claim)"
        )


# ===========================================================================
# Debug-endpoint read-only companion — POST /thinking/debug handler shape
# ===========================================================================
#
# Debug-endpoint read-only companion ONLY. This is NOT a C1–C5 expansion, NOT a
# Candidate Gate D invariant, and NOT an Envelope Audit / Layer-1 private
# thinking / Document B surface. The POST /thinking/debug handler runs the
# thinking controller and returns the FULL decision chain for inspection; that
# exposure is intentional. These tests lock ONLY that the handler is READ-ONLY:
# it calls thinking_controller.think(...), returns result.to_dict(), and makes
# no direct stateful retrieval / writer / mutation call.
#
# Deliberate non-goals: this does NOT assert /thinking/debug hides or redacts
# the decision chain (it legitimately exposes it), does NOT inspect/redact debug
# content, does NOT gate / disable / reframe the endpoint, and does NOT freeze
# the absence of any future governed Document B / Envelope Audit implementation.
# AST-only: app.py is parsed as source, never imported or served.
#
# `query` is intentionally in the forbidden set: repo history treats
# `fabric.query` as opaque and NOT mutation-free (Gate A C3 / reflection-trace
# non-reentry posture), so a read-only debug handler must not reach it.
# `measure_drift` is included for the same read-only reason.

_DEBUG_FORBIDDEN_CALL_NAMES = frozenset(
    FORBIDDEN_CALL_NAMES | {"query", "measure_drift"}
)


class TestDebugEndpointReadOnlyCompanion:
    @pytest.fixture(scope="class")
    def handler(self):
        tree = _parse_module_source("app.py")
        node = _find_route_handler(tree, "post", "/thinking/debug")
        assert node is not None, "could not locate @app.post('/thinking/debug') handler"
        return node

    def test_handler_calls_thinking_controller_think(self, handler):
        think_calls = [
            n for n in ast.walk(handler)
            if isinstance(n, ast.Call) and _called_name(n) == "think"
        ]
        assert think_calls, "/thinking/debug handler does not call .think()"

    def test_handler_returns_to_dict(self, handler):
        # The handler returns the full decision chain via result.to_dict();
        # assert a to_dict() call appears inside a return statement. This does
        # NOT constrain what to_dict() contains — only that the handler returns
        # the controller's own serialization rather than something else.
        returns_with_to_dict = []
        for n in ast.walk(handler):
            if not isinstance(n, ast.Return) or n.value is None:
                continue
            if any(
                isinstance(c, ast.Call) and _called_name(c) == "to_dict"
                for c in ast.walk(n.value)
            ):
                returns_with_to_dict.append(getattr(n, "lineno", -1))
        assert returns_with_to_dict, (
            "/thinking/debug handler does not return a result.to_dict() payload"
        )

    def test_handler_makes_no_stateful_retrieval_writer_or_mutation_calls(self, handler):
        violations = []
        for n in ast.walk(handler):
            if not isinstance(n, ast.Call):
                continue
            name = _called_name(n)
            if name in _DEBUG_FORBIDDEN_CALL_NAMES:
                violations.append((getattr(n, "lineno", -1), name))
            elif name == "write":
                violations.append((getattr(n, "lineno", -1), ".write"))
            elif name == "open" and _open_is_write(n):
                violations.append((getattr(n, "lineno", -1), "open(write)"))
        assert violations == [], (
            "/thinking/debug handler makes forbidden stateful retrieval/writer/"
            f"mutation call(s) (line, name): {violations!r}"
        )

    def test_debug_forbidden_set_is_broader_than_c1_writer_set(self):
        # Guard: keep the read-only intent explicit. The debug set is strictly
        # the C1 writer set PLUS `query` and `measure_drift`, so the intent
        # survives any future edit to FORBIDDEN_CALL_NAMES.
        assert "query" in _DEBUG_FORBIDDEN_CALL_NAMES
        assert "measure_drift" in _DEBUG_FORBIDDEN_CALL_NAMES
        assert FORBIDDEN_CALL_NAMES <= _DEBUG_FORBIDDEN_CALL_NAMES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
