"""Gate A Layer 4 — second containment brick: MemoryGraph.spawn_memory refusal.

The node-creation primitive ``MemoryGraph.spawn_memory`` refuses a candidate-shaped
value passed as the ordinary-memory ``summary``, as its FIRST executable statement
(after the docstring), before payload construction, ``world.spawn``, embedding
writes, logging, JSONL writes, or any ``self`` mutation. Because ``add_memory``
delegates to ``spawn_memory`` and every MemoryGraph creation caller (ordinary
ingest, identity anchors, shared writes, promotion-beneath, character seeding)
funnels through it, this one type-only guard covers the whole creation axis.

Runtime proof strategy uses ``self`` sentinels so no real graph (and no embedding /
file IO) is constructed:
  * ``_TripSelf`` raises on ANY attribute access — a candidate ``summary`` must
    raise ``TypeError`` (the guard) WITHOUT touching it; an ordinary string must
    flow past the guard and trip the sentinel at the first real ``self`` access
    (``self._vec3``).
  * ``_DelegateSpawnSelf`` permits only ``self.spawn_memory`` (the real primitive)
    so ``add_memory`` is shown to raise THROUGH ``spawn_memory``.

SCOPE / UNRESOLVED (deliberately preserved, NOT bugs): this brick guards only the
``summary`` parameter of ``spawn_memory``. ``update_payload``, ``extra_payload``,
``links``, ReferenceStore, EnvironmentStore, ArchiveStore, the other direct-writer
bypasses, and the parked writer non-conformances remain unresolved and out of
scope. This is NOT wall completion.
"""

import ast
import os
import unittest

from torment_service.candidate_types import CandidateShapedValue
from torment_service.memory_graph import MemoryGraph


_SECRET = "SUPER_SECRET_SEALED_SUMMARY_DO_NOT_LEAK"


def _service_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "torment_service")


def _tree(filename):
    with open(os.path.join(_service_dir(), filename), "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))


def _read(filename):
    with open(os.path.join(_service_dir(), filename), "rb") as fh:
        return fh.read().replace(b"\x00", b"").decode("utf-8", "replace")


def _method(tree, cls, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == name:
                    return m
    return None


def _first_non_docstring(func):
    body = func.body
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(getattr(body[0], "value", None), ast.Constant)
            and isinstance(body[0].value.value, str)):
        return body[1]
    return body[0]


class _TripSelf:
    """`self` stand-in that raises on ANY attribute access."""

    def __getattribute__(self, name):
        raise AssertionError(
            f"spawn_memory accessed self.{name} before refusing candidate summary")


class _DelegateSpawnSelf:
    """`self` stand-in that permits ONLY self.spawn_memory (the real primitive)."""

    def __getattribute__(self, name):
        if name == "spawn_memory":
            return lambda *a, **k: MemoryGraph.spawn_memory(self, *a, **k)
        raise AssertionError(
            f"add_memory accessed self.{name} before delegating to spawn_memory")


def _call_spawn(self_obj, summary):
    return MemoryGraph.spawn_memory(
        self_obj, summary=summary, embedding=None, mtype="episode",
        strength=0.5, confidence=0.5, half_life_days=1.0,
    )


def _call_add(self_obj, summary):
    return MemoryGraph.add_memory(
        self_obj, summary=summary, embedding=None, mtype="episode",
        strength=0.5, confidence=0.5, half_life_days=1.0,
    )


# --------------------------------------------------------------------------- #
# Runtime: pre-side-effect refusal
# --------------------------------------------------------------------------- #

class TestSpawnMemoryRefusal(unittest.TestCase):

    def test_candidate_summary_refused_before_any_self_access(self):
        # TypeError from the guard; _TripSelf is never touched (no payload build,
        # world.spawn, embedding write, logging, or JSONL write).
        with self.assertRaises(TypeError) as ctx:
            _call_spawn(_TripSelf(), CandidateShapedValue(_SECRET))
        self.assertIs(type(ctx.exception), TypeError)

    def test_error_message_is_contents_free(self):
        with self.assertRaises(TypeError) as ctx:
            _call_spawn(_TripSelf(), CandidateShapedValue(_SECRET))
        self.assertNotIn(_SECRET, str(ctx.exception))

    def test_add_memory_raises_through_spawn_memory(self):
        # add_memory's first action is self.spawn_memory(...); the candidate is
        # refused there -> TypeError (not AssertionError).
        with self.assertRaises(TypeError) as ctx:
            _call_add(_DelegateSpawnSelf(), CandidateShapedValue(_SECRET))
        self.assertIs(type(ctx.exception), TypeError)

    def test_ordinary_string_passes_guard_to_first_real_statement(self):
        # An ordinary string is NOT refused; it flows past the guard to the first
        # real self access (self._vec3) and trips the sentinel there. Proves the
        # guard is a no-op for ordinary summaries and sits before _vec3.
        with self.assertRaises(AssertionError) as ctx:
            _call_spawn(_TripSelf(), "an ordinary memory summary")
        self.assertIn("_vec3", str(ctx.exception))


# --------------------------------------------------------------------------- #
# Source / AST: placement, shape, content-blindness
# --------------------------------------------------------------------------- #

class TestGuardPlacementAndShape(unittest.TestCase):

    def setUp(self):
        self.func = _method(_tree("memory_graph.py"), "MemoryGraph", "spawn_memory")
        self.assertIsNotNone(self.func, "MemoryGraph.spawn_memory not found")
        self.guard = _first_non_docstring(self.func)

    def test_first_non_docstring_statement_is_type_only_isinstance(self):
        self.assertIsInstance(self.guard, ast.If)
        test = self.guard.test
        self.assertIsInstance(test, ast.Call)
        self.assertIsInstance(test.func, ast.Name)
        self.assertEqual(test.func.id, "isinstance")
        self.assertEqual(len(test.args), 2)
        self.assertIsInstance(test.args[0], ast.Name)
        self.assertEqual(test.args[0].id, "summary")
        self.assertIsInstance(test.args[1], ast.Name)
        self.assertEqual(test.args[1].id, "CandidateShapedValue")

    def test_guard_body_is_single_raise_typeerror(self):
        self.assertEqual(len(self.guard.body), 1)
        raise_node = self.guard.body[0]
        self.assertIsInstance(raise_node, ast.Raise)
        self.assertIsInstance(raise_node.exc, ast.Call)
        self.assertIsInstance(raise_node.exc.func, ast.Name)
        self.assertEqual(raise_node.exc.func.id, "TypeError")

    def test_guard_does_not_touch_self(self):
        names = {n.id for n in ast.walk(self.guard) if isinstance(n, ast.Name)}
        self.assertNotIn("self", names)

    def test_guard_calls_only_isinstance_and_typeerror(self):
        calls = {n.func.id for n in ast.walk(self.guard)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertEqual(calls, {"isinstance", "TypeError"},
                         msg=f"unexpected calls in guard: {sorted(calls)}")

    def test_guard_is_content_blind(self):
        # No attribute access, no subscript -> no contents/keys/tags/provenance/
        # metadata/links/extra_payload/nested inspection.
        for n in ast.walk(self.guard):
            if isinstance(n, ast.Attribute):
                self.fail(f"guard performs attribute access: .{n.attr}")
            if isinstance(n, ast.Subscript):
                self.fail("guard performs item/subscript access")

    def test_raise_message_does_not_interpolate_summary(self):
        raise_node = self.guard.body[0]
        for n in ast.walk(raise_node):
            self.assertNotIsInstance(n, ast.JoinedStr,
                                     msg="raise message must not be an f-string")
            if isinstance(n, ast.Name):
                self.assertNotEqual(n.id, "summary",
                                    msg="raise message must not reference `summary`")

    def test_guard_references_only_summary_not_other_params(self):
        names = {n.id for n in ast.walk(self.guard) if isinstance(n, ast.Name)}
        for other in ("extra_payload", "links", "embedding", "memory_class",
                      "mtype", "user_id", "canon"):
            self.assertNotIn(other, names,
                             msg=f"guard unexpectedly references {other}")


# --------------------------------------------------------------------------- #
# Source: delegation + promotion-beneath + unresolved gaps
# --------------------------------------------------------------------------- #

class TestDelegationAndScope(unittest.TestCase):

    def test_add_memory_delegates_to_spawn_memory(self):
        add = _method(_tree("memory_graph.py"), "MemoryGraph", "add_memory")
        self.assertIsNotNone(add)
        calls = {n.func.attr for n in ast.walk(add)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertIn("spawn_memory", calls,
                      msg="add_memory no longer delegates to spawn_memory")

    def test_promotion_not_edited_coverage_is_beneath(self):
        # promotion.py must still call spawn_memory (so the guard sits beneath it)
        # and must NOT have gained its own candidate guard (not a promotion fix).
        psrc = _read("promotion.py")
        self.assertIn("spawn_memory", psrc)
        self.assertNotIn("CandidateShapedValue", psrc)
        self.assertNotIn("candidate_types", psrc)

    def test_fabric_unchanged_by_this_brick(self):
        # This brick touches memory_graph.py only; fabric.py keeps its own
        # brick-1 text guard and gains nothing here.
        fsrc = _read("fabric.py")
        self.assertEqual(fsrc.count("isinstance(text, CandidateShapedValue)"), 1)
        self.assertNotIn("isinstance(summary, CandidateShapedValue)", fsrc)

    def test_unresolved_gaps_remain_present(self):
        # Named, deliberately-unresolved surfaces still exist (NOT contained):
        gsrc = _read("memory_graph.py")
        self.assertIn("def update_payload", gsrc)   # mutation axis: unresolved
        fsrc = _read("fabric.py")
        self.assertIn("_get_reference_store", fsrc)      # ReferenceStore: unresolved
        self.assertIn("_get_environment_store", fsrc)    # EnvironmentStore: unresolved
        self.assertIn("_maybe_emit_identity_anchor", fsrc)  # parked non-conformance


class TestImportIsDependencyFree(unittest.TestCase):

    def test_candidate_types_imports_nothing_from_package(self):
        tree = ast.parse(_read("candidate_types.py"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0)
                self.assertNotIn("torment_service", node.module or "")
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn("torment_service", a.name)


if __name__ == "__main__":
    unittest.main()
