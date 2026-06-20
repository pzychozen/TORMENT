"""
tests/test_reflection_trace.py — ReflectionTrace v0.1 conformance.

ReflectionTrace v0.1 is an ephemeral, in-memory, per-turn observation surface
for the CURRENT deterministic decision-shape of the thinking layer. These tests
lock the v0.1 guarantees:

  - frozen, shape-only dataclass (no raw text / content fields);
  - pure builder;
  - think() populates it from already-computed locals;
  - it serializes only through ThinkingResult.to_dict() (the /thinking/debug
    inspection shape), NOT through /agent/query, fabric.query, prompt assembly,
    character_context, blocks, or assembled_text (non-reentry);
  - no durable state / module-level accumulation;
  - reflection_trace.py is structurally writer-free / storage-free (AST lock).

Companion: the Gate A C2 lock (test_gate_a_tests_only_locks_c1_c5.py) still
proves /agent/query exports only top_k_by_lane/weight_by_lane; this patch does
not touch that handler, so C2 must remain green.
"""
from __future__ import annotations

import ast
import dataclasses
import importlib
import json
import os
from pathlib import Path

import pytest

from torment_service.reflection_trace import ReflectionTrace, build_reflection_trace
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import ThinkingResult

_SERVICE_DIR = Path(__file__).resolve().parents[1] / "torment_service"

_EXPECTED_FIELDS = {
    "chosen_mode",
    "action",
    "stance",
    "review_status_flags",
    "active_lanes",
    "lane_budget_shape",
    "geometric_context_present",
    # v0.2 coarse additions
    "allowed_depth",
    "requires_self_review",
    "may_escalate",
    "confidence_floor",
    "requires_execution",
    "source_type",
    "action_need",
    "memory_need",
    "tool_need",
    "governance_sensitive",
    "identity_sensitive",
    "live_social",
    "urgency",
    "ambiguity_score",
    "confidence_need",
    "scope",
}

# v0.2 coarse fields and their required primitive types.
_V02_COARSE_TYPES = {
    "allowed_depth": int,
    "requires_self_review": bool,
    "may_escalate": bool,
    "confidence_floor": float,
    "requires_execution": bool,
    "source_type": str,
    "action_need": bool,
    "memory_need": bool,
    "tool_need": bool,
    "governance_sensitive": bool,
    "identity_sensitive": bool,
    "live_social": bool,
    "urgency": float,
    "ambiguity_score": float,
    "confidence_need": float,
}

# Field names that would imply raw reasoning / content leaked into the trace.
_FORBIDDEN_CONTENT_FIELDS = {
    "raw_input",
    "normalized_input",
    "response_draft",
    "draft",
    "revised_text",
    "reason",
    "review_notes",
    "notes",
    "rationale",
    "payload",
    "tone_hints",
    "prompt",
    "assembled_text",
    "memory",
    "summary",
    "seed_text",
    "context",
    "blocks",
    "kappa",
    "phi",
    "omega",
    "drift_score",
    "srg",
    "embedding",
}


def _sample_trace() -> ReflectionTrace:
    return build_reflection_trace(
        chosen_mode="fast",
        action="answer",
        stance=None,
        review_status_flags={"approved": True, "blocked": False},
        top_k_by_lane={"core": 5, "relational": 0, "deep": 2},
        geometric_context_present=False,
    )


# ---------------------------------------------------------------------------
# 1. Frozen, shape-only dataclass
# ---------------------------------------------------------------------------

class TestFrozenShapeOnly:
    def test_is_frozen_dataclass(self):
        assert dataclasses.is_dataclass(ReflectionTrace)
        t = _sample_trace()
        with pytest.raises(dataclasses.FrozenInstanceError):
            t.chosen_mode = "mutated"  # type: ignore[misc]

    def test_field_set_is_exactly_the_shape_fields(self):
        names = {f.name for f in dataclasses.fields(ReflectionTrace)}
        assert names == _EXPECTED_FIELDS

    def test_no_raw_content_fields(self):
        names = {f.name for f in dataclasses.fields(ReflectionTrace)}
        leaked = names & _FORBIDDEN_CONTENT_FIELDS
        assert leaked == set(), f"ReflectionTrace exposes content-bearing field(s): {leaked!r}"

    def test_to_dict_keys_are_coarse_only(self):
        d = _sample_trace().to_dict()
        assert set(d.keys()) == _EXPECTED_FIELDS
        # values are primitives / containers of primitives only
        assert isinstance(d["chosen_mode"], str)
        assert isinstance(d["action"], str)
        assert d["stance"] is None or isinstance(d["stance"], str)
        assert isinstance(d["review_status_flags"], dict)
        assert all(isinstance(v, bool) for v in d["review_status_flags"].values())
        assert isinstance(d["active_lanes"], list)
        assert isinstance(d["lane_budget_shape"], dict)
        assert all(isinstance(v, int) for v in d["lane_budget_shape"].values())
        assert isinstance(d["geometric_context_present"], bool)
        assert d["scope"] == "per_turn_ephemeral"


# ---------------------------------------------------------------------------
# 1b. Inner containers are read-only after construction (immutability hardening)
# ---------------------------------------------------------------------------

class TestInnerContainersReadOnly:
    """`frozen=True` blocks field *reassignment*, but the inner mapping fields
    must also be genuinely read-only after construction — mutating a constructed
    trace's containers must raise. `active_lanes` is already a tuple."""

    def test_review_status_flags_cannot_be_mutated(self):
        t = _sample_trace()
        with pytest.raises(TypeError):
            t.review_status_flags["approved"] = False  # type: ignore[index]
        with pytest.raises(TypeError):
            t.review_status_flags["new_key"] = True  # type: ignore[index]

    def test_lane_budget_shape_cannot_be_mutated(self):
        t = _sample_trace()
        with pytest.raises(TypeError):
            t.lane_budget_shape["core"] = 999  # type: ignore[index]

    def test_active_lanes_is_immutable_tuple(self):
        t = _sample_trace()
        assert isinstance(t.active_lanes, tuple)
        with pytest.raises(TypeError):
            t.active_lanes[0] = "mutated"  # type: ignore[index]

    def test_default_constructed_trace_is_also_read_only(self):
        # The hardening lives in __post_init__, not the builder, so the
        # bare-defaults construction path must be read-only too.
        t = ReflectionTrace(chosen_mode="fast", action="answer")
        with pytest.raises(TypeError):
            t.review_status_flags["x"] = True  # type: ignore[index]
        with pytest.raises(TypeError):
            t.lane_budget_shape["x"] = 1  # type: ignore[index]

    def test_direct_construction_copies_source_mapping(self):
        # __post_init__ wraps a *private copy*: a dict passed straight to the
        # constructor cannot be mutated through after the fact.
        src = {"approved": True}
        t = ReflectionTrace(
            chosen_mode="fast", action="answer", review_status_flags=src,
        )
        src["approved"] = False
        src["injected"] = True
        assert dict(t.review_status_flags) == {"approved": True}

    def test_to_dict_still_returns_mutable_plain_copies(self):
        # The read-only guarantee is on the trace's own containers; to_dict()
        # must still yield plain, mutable, JSON-safe primitives (copies).
        d = _sample_trace().to_dict()
        d["review_status_flags"]["approved"] = False  # must NOT raise
        d["lane_budget_shape"]["core"] = 0  # must NOT raise
        d["active_lanes"].append("x")  # must NOT raise
        assert type(d["review_status_flags"]) is dict
        assert type(d["lane_budget_shape"]) is dict
        assert type(d["active_lanes"]) is list


# ---------------------------------------------------------------------------
# 2. Builder purity
# ---------------------------------------------------------------------------

class TestBuilderPurity:
    def test_equal_inputs_equal_output(self):
        a = _sample_trace()
        b = _sample_trace()
        assert a == b

    def test_active_lanes_are_nonzero_topk_only(self):
        t = build_reflection_trace(
            chosen_mode="retrieval",
            action="answer",
            stance="respond_now",
            review_status_flags={"approved": True},
            top_k_by_lane={"core": 4, "relational": 0, "deep": 1, "archive": 0},
            geometric_context_present=True,
        )
        assert t.active_lanes == ("core", "deep")
        assert t.lane_budget_shape == {"core": 4, "relational": 0, "deep": 1, "archive": 0}

    def test_repeated_calls_independent_objects(self):
        traces = [_sample_trace() for _ in range(50)]
        # value-equal but not the same identity (no shared/global instance)
        assert all(t == traces[0] for t in traces)
        assert len({id(t) for t in traces}) == 50


# ---------------------------------------------------------------------------
# 3. think() populates reflection_trace
# ---------------------------------------------------------------------------

class TestThinkPopulatesTrace:
    def test_think_attaches_trace(self):
        result = ThinkingController().think(
            workspace_id="ws", agent_id="ag", raw_input="What time is it?",
        )
        assert isinstance(result, ThinkingResult)
        assert isinstance(result.reflection_trace, ReflectionTrace)
        rt = result.reflection_trace
        assert rt.scope == "per_turn_ephemeral"
        # shape labels match the result's own decisions
        assert rt.chosen_mode == result.mode_decision.chosen_mode.value
        assert rt.action == result.action_decision.action.value
        assert rt.geometric_context_present is (result.geometric_context is not None)

    def test_new_coarse_fields_match_locals(self):
        result = ThinkingController().think(
            workspace_id="ws", agent_id="ag", raw_input="Please run a quick search",
        )
        rt = result.reflection_trace
        mode = result.mode_decision
        action = result.action_decision
        frame = result.task_frame
        # mode shape
        assert rt.allowed_depth == mode.allowed_depth
        assert rt.requires_self_review == mode.requires_self_review
        assert rt.may_escalate == mode.may_escalate
        assert rt.confidence_floor == mode.confidence_floor
        # action shape
        assert rt.requires_execution == action.requires_execution
        # frame shape
        assert rt.source_type == frame.source_type
        assert rt.action_need == frame.action_need
        assert rt.memory_need == frame.memory_need
        assert rt.tool_need == frame.tool_need
        assert rt.governance_sensitive == frame.governance_sensitive
        assert rt.identity_sensitive == frame.identity_sensitive
        assert rt.live_social == frame.live_social
        assert rt.urgency == frame.urgency
        assert rt.ambiguity_score == frame.ambiguity_score
        assert rt.confidence_need == frame.confidence_need

    def test_new_coarse_fields_are_primitive(self):
        d = ThinkingController().think(
            workspace_id="ws", agent_id="ag", raw_input="hello",
        ).reflection_trace.to_dict()
        for name, typ in _V02_COARSE_TYPES.items():
            # bool is a subclass of int; require exact-type match to avoid a
            # bool slipping in where a float/int is expected and vice versa.
            assert type(d[name]) is typ, f"{name} is {type(d[name])}, expected {typ}"

    def test_to_dict_surfaces_trace_like_thinking_debug(self):
        # /thinking/debug returns result.to_dict(); this mirrors that surface.
        result = ThinkingController().think(
            workspace_id="ws", agent_id="ag", raw_input="hello",
        )
        d = result.to_dict()
        assert "reflection_trace" in d
        assert d["reflection_trace"]["scope"] == "per_turn_ephemeral"

    def test_to_dict_trace_is_none_when_absent(self):
        # A bare ThinkingResult (no trace) serializes reflection_trace as None.
        result = ThinkingController().think(
            workspace_id="ws", agent_id="ag", raw_input="hello",
        )
        # ThinkingResult is a (non-frozen) dataclass; clearing the field is a
        # plain attribute set. to_dict() must then serialize None, not error.
        result.reflection_trace = None
        assert result.to_dict()["reflection_trace"] is None


# ---------------------------------------------------------------------------
# 4/5. Non-reentry — fake/spy fabric boundary on the /agent/query handler
# ---------------------------------------------------------------------------

class _SpyFabric:
    QUERY_SENTINEL = {"_spy": "opaque-query-result"}

    def __init__(self):
        self.calls = {}
        self.last_query_kwargs = None

    def _rec(self, name):
        self.calls[name] = self.calls.get(name, 0) + 1

    def get_kernel_runtime_context(self, *a, **k):
        self._rec("get_kernel_runtime_context")
        return None

    def query(self, **kwargs):
        self._rec("query")
        self.last_query_kwargs = kwargs
        return self.QUERY_SENTINEL


@pytest.fixture()
def appmod(tmp_path):
    """Isolated app module bound to a temp data dir (mirrors the Gate A /
    smoke-API fixture). Manual env save/restore + reload-in-finally."""
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


class TestAgentQueryNonReentry:
    def test_trace_not_passed_to_fabric_query(self, appmod, monkeypatch):
        monkeypatch.setenv("TORMENT_THINKING_ADVISORY", "1")
        spy = _SpyFabric()
        monkeypatch.setattr(appmod, "fabric", spy)

        req = appmod.QueryReq(workspace_id="ws", agent_id="ag", query="hello", top_k=3)
        out = appmod.query(req)

        assert spy.calls.get("query", 0) == 1
        # The MemoryPlan handed to fabric.query is exactly the two lane dicts —
        # ReflectionTrace must never appear in the retrieval path.
        mp = spy.last_query_kwargs.get("memory_plan")
        if mp is not None:  # advisory may no-op to None on error; never a trace
            assert set(mp.keys()) == {"top_k_by_lane", "weight_by_lane"}
        assert out is spy.QUERY_SENTINEL


# ---------------------------------------------------------------------------
# 6. Trace absent from model-visible surfaces (/agent/query, /retrieve)
# ---------------------------------------------------------------------------

def _unit_vec(dim=384, seed=0):
    import numpy as np
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(dim,)).astype("float32")
    v /= (np.linalg.norm(v) + 1e-12)
    return v.tolist()


class TestTraceAbsentFromModelVisibleSurfaces:
    _MARKERS = ("reflection_trace", "per_turn_ephemeral")

    def test_markers_absent_from_query_and_retrieve(self, appmod):
        from fastapi.testclient import TestClient
        client = TestClient(appmod.app)

        r = client.post("/workspace/create", json={"workspace_id": "wsrt"})
        assert r.status_code == 200, r.text
        r = client.post("/agent/create", json={
            "workspace_id": "wsrt", "agent_id": "agrt",
            "seed": {"coupling_mode": "read_only", "coupling_strength": 0.2},
        })
        assert r.status_code == 200, r.text
        r = client.post("/agent/ingest", json={
            "workspace_id": "wsrt", "agent_id": "agrt",
            "text": "We chose summaries plus embeddings for storage.",
            "step": 1, "supplied_summary": "storage decision",
            "supplied_embedding": _unit_vec(seed=1), "scope": "private",
        })
        assert r.status_code == 200, r.text

        q = client.post("/agent/query", json={
            "workspace_id": "wsrt", "agent_id": "agrt",
            "query": "What did we decide about storage?", "top_k": 5,
        })
        assert q.status_code == 200, q.text
        for m in self._MARKERS:
            assert m not in q.text, f"/agent/query response leaked {m!r}"

        rr = client.post("/retrieve", json={
            "workspace_id": "wsrt", "agent_id": "agrt",
            "query": "What did we decide about storage?",
            "profile": "companion", "token_budget": 1500, "top_k": 5,
        })
        assert rr.status_code == 200, rr.text
        body = rr.json()
        for key in ("blocks", "assembled_text", "character_context"):
            assert self._MARKERS[0] not in json.dumps(body.get(key, "")), (
                f"/retrieve {key} leaked reflection_trace"
            )
        for m in self._MARKERS:
            assert m not in rr.text, f"/retrieve response leaked {m!r}"


# ---------------------------------------------------------------------------
# 7. No durable state / module-level accumulation
# ---------------------------------------------------------------------------

class TestNoDurableState:
    def test_no_module_level_accumulator_grows(self):
        import torment_service.reflection_trace as rtmod
        before = {
            k: (len(v) if isinstance(v, (list, dict, set)) else None)
            for k, v in vars(rtmod).items()
            if isinstance(v, (list, dict, set))
        }
        for i in range(25):
            build_reflection_trace(
                chosen_mode="fast", action="answer", stance=None,
                review_status_flags={"approved": True},
                top_k_by_lane={"core": i % 3}, geometric_context_present=False,
            )
        after = {
            k: (len(v) if isinstance(v, (list, dict, set)) else None)
            for k, v in vars(rtmod).items()
            if isinstance(v, (list, dict, set))
        }
        assert before == after, "reflection_trace module gained/grew a container"

    def test_two_think_calls_do_not_share_trace(self):
        a = ThinkingController().think(workspace_id="ws", agent_id="ag", raw_input="hi one")
        b = ThinkingController().think(workspace_id="ws", agent_id="ag", raw_input="hi two")
        assert a.reflection_trace is not b.reflection_trace


# ---------------------------------------------------------------------------
# 8. AST/source lock — reflection_trace.py is writer-free and storage-free
# ---------------------------------------------------------------------------

_ALLOWED_IMPORT_ROOTS = {"__future__", "dataclasses", "types", "typing"}

_FORBIDDEN_CALL_NAMES = frozenset({
    "ingest", "spawn_memory", "add_memory", "update_payload", "flush_node",
    "save_state", "append_record", "reinforce", "promote_chunk",
    "promote_chunk_endpoint", "gravity_correction", "process_proposals",
    "collective_reingest", "_maybe_emit_identity_anchor", "_maybe_emit_mood_drift",
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


class TestReflectionTraceModuleIsInert:
    @pytest.fixture(scope="class")
    def tree(self):
        src = (_SERVICE_DIR / "reflection_trace.py").read_text(encoding="utf-8")
        return ast.parse(src, filename="reflection_trace.py")

    def test_imports_stdlib_only(self, tree):
        roots = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                roots.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                # relative import (level>0) means a torment_service sibling — forbidden
                assert n.level == 0, f"relative import of {n.module!r} is forbidden"
                if n.module:
                    roots.add(n.module.split(".")[0])
        illegal = roots - _ALLOWED_IMPORT_ROOTS
        assert illegal == set(), f"reflection_trace.py imports non-stdlib roots: {illegal!r}"

    def test_no_writer_or_storage_calls(self, tree):
        violations = []
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            name = _called_name(n)
            if name in _FORBIDDEN_CALL_NAMES:
                violations.append((getattr(n, "lineno", -1), name))
            elif name == "write":
                violations.append((getattr(n, "lineno", -1), ".write"))
            elif name == "open" and _open_is_write(n):
                violations.append((getattr(n, "lineno", -1), "open(write)"))
        assert violations == [], f"reflection_trace.py has writer/storage calls: {violations!r}"

    def test_matcher_has_teeth(self):
        # guard: the matcher actually flags a real writer call
        snippet = "def f(x):\n    fabric.ingest(x)\n    obj.write(x)\n"
        flagged = set()
        for n in ast.walk(ast.parse(snippet)):
            if isinstance(n, ast.Call):
                nm = _called_name(n)
                if nm in _FORBIDDEN_CALL_NAMES or nm == "write":
                    flagged.add(nm)
        assert "ingest" in flagged and "write" in flagged


class TestNonReentryProductionScan:
    """Strengthened non-reentry lock: no production torment_service module may
    READ `.reflection_trace`. Only ThinkingResult.to_dict() (thinking_models.py)
    serializes it; /agent/query, fabric, prompt assembly, blocks, etc. must not
    consume it. thinking_controller only *writes* it as a constructor keyword
    (an ast.keyword, not an attribute read), so it is not flagged.
    """

    def test_no_production_module_reads_reflection_trace(self):
        offenders = {}
        for py in sorted(_SERVICE_DIR.glob("*.py")):
            tree = ast.parse(py.read_text(encoding="utf-8"), filename=py.name)
            reads = sorted(
                n.lineno for n in ast.walk(tree)
                if isinstance(n, ast.Attribute) and n.attr == "reflection_trace"
            )
            if reads and py.name != "thinking_models.py":
                offenders[py.name] = reads
        assert offenders == {}, (
            f".reflection_trace is read outside ThinkingResult.to_dict(): {offenders!r}"
        )

    def test_thinking_models_only_reads_it_in_to_dict(self):
        # Positive anchor: thinking_models.py is the single allowed reader, and
        # only inside to_dict() (guarded serialization). Confirms the allow-list
        # entry is real, so the scan above is not vacuously passing.
        tree = ast.parse(
            (_SERVICE_DIR / "thinking_models.py").read_text(encoding="utf-8"),
            filename="thinking_models.py",
        )
        reader_funcs = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(
                    isinstance(a, ast.Attribute) and a.attr == "reflection_trace"
                    for a in ast.walk(node)
                ):
                    reader_funcs.add(node.name)
        assert reader_funcs == {"to_dict"}, (
            f"reflection_trace read in unexpected thinking_models functions: {reader_funcs!r}"
        )


# ---------------------------------------------------------------------------
# 9. Content-leak value guard on the think() controller path (gap-level)
# ---------------------------------------------------------------------------
#
# Companion to the name-based content-field denylist (TestFrozenShapeOnly) and
# to the runner-path value-level secret test
# (test_reflection_trace_runner_parity.py::test_no_review_text_notes_or_draft_in_trace):
# a distinctive token placed in the controller's caller-supplied content
# (raw_input / metadata) must never surface anywhere in the trace's serialized
# shape. This locks content-freeness at the VALUE level on the think() path,
# symmetric to the runner path. It is NOT a label-vocabulary freeze — only the
# injected markers are checked — and it neither names nor freezes any future
# governed Document B / Envelope Audit / private-cognition surface.

class TestThinkPathContentLeakGuard:
    def test_raw_input_token_absent_from_think_trace(self):
        token = "ZZQ_RAWINPUT_MARKER_7F3A"
        result = ThinkingController().think(
            workspace_id="ws", agent_id="ag",
            raw_input=f"please remember {token} for later",
        )
        blob = json.dumps(result.reflection_trace.to_dict())
        assert token not in blob, (
            "raw_input content leaked into the think()-path ReflectionTrace"
        )

    def test_metadata_token_absent_from_think_trace(self):
        token = "ZZQ_METADATA_MARKER_91C2"
        result = ThinkingController().think(
            workspace_id="ws", agent_id="ag", raw_input="hello",
            metadata={"note": token},
        )
        blob = json.dumps(result.reflection_trace.to_dict())
        assert token not in blob, (
            "metadata content leaked into the think()-path ReflectionTrace"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
