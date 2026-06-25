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


def _call_spawn_ep(self_obj, extra_payload, summary="an ordinary memory summary"):
    # Ordinary string summary so the candidate (if any) is carried by
    # extra_payload, not summary — exercising the brick-3 guard specifically.
    return MemoryGraph.spawn_memory(
        self_obj, summary=summary, embedding=None, mtype="episode",
        strength=0.5, confidence=0.5, half_life_days=1.0,
        extra_payload=extra_payload,
    )


def _call_add_ep(self_obj, extra_payload, summary="an ordinary memory summary"):
    return MemoryGraph.add_memory(
        self_obj, summary=summary, embedding=None, mtype="episode",
        strength=0.5, confidence=0.5, half_life_days=1.0,
        extra_payload=extra_payload,
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

    def test_summary_guard_references_only_summary_not_other_params(self):
        # Scoped to the SUMMARY guard (first non-docstring statement). The
        # sibling extra_payload guard is checked in TestExtraPayloadGuardShape;
        # this assertion is deliberately NOT broadened to the whole function.
        names = {n.id for n in ast.walk(self.guard) if isinstance(n, ast.Name)}
        for other in ("extra_payload", "links", "embedding", "memory_class",
                      "mtype", "user_id", "canon"):
            self.assertNotIn(other, names,
                             msg=f"summary guard unexpectedly references {other}")


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


def _nondoc_body(func):
    body = func.body
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(getattr(body[0], "value", None), ast.Constant)
            and isinstance(body[0].value.value, str)):
        return body[1:]
    return body


# --------------------------------------------------------------------------- #
# Brick #3 — runtime: extra_payload candidate refusal before side effects
# --------------------------------------------------------------------------- #

class TestExtraPayloadRefusal(unittest.TestCase):

    def test_extra_payload_object_refused_before_any_self_access(self):
        # extra_payload IS a candidate -> TypeError; _TripSelf never touched.
        with self.assertRaises(TypeError) as ctx:
            _call_spawn_ep(_TripSelf(), CandidateShapedValue(_SECRET))
        self.assertIs(type(ctx.exception), TypeError)

    def test_extra_payload_value_refused_before_any_self_access(self):
        # A candidate carried as an immediate extra_payload value -> TypeError,
        # before world.spawn / payload mutation (no self access on _TripSelf).
        with self.assertRaises(TypeError) as ctx:
            _call_spawn_ep(_TripSelf(), {"x": CandidateShapedValue(_SECRET)})
        self.assertIs(type(ctx.exception), TypeError)

    def test_extra_payload_error_messages_are_contents_free(self):
        for ep in (CandidateShapedValue(_SECRET), {"x": CandidateShapedValue(_SECRET)}):
            with self.assertRaises(TypeError) as ctx:
                _call_spawn_ep(_TripSelf(), ep)
            self.assertNotIn(_SECRET, str(ctx.exception))

    def test_ordinary_extra_payload_passes_guard_to_first_real_statement(self):
        # An ordinary dict is NOT refused; with an ordinary string summary it
        # flows past both candidate guards to the first real self access
        # (self._vec3) and trips the sentinel there. Proves the brick-3 guard is
        # a no-op for ordinary extra_payload.
        with self.assertRaises(AssertionError) as ctx:
            _call_spawn_ep(_TripSelf(), {"x": 1, "y": "ok"})
        self.assertIn("_vec3", str(ctx.exception))

    def test_add_memory_refuses_extra_payload_through_spawn_memory(self):
        # add_memory's first action is self.spawn_memory(...); the candidate
        # extra_payload value is refused there -> TypeError (not AssertionError).
        with self.assertRaises(TypeError) as ctx:
            _call_add_ep(_DelegateSpawnSelf(), {"x": CandidateShapedValue(_SECRET)})
        self.assertIs(type(ctx.exception), TypeError)


# --------------------------------------------------------------------------- #
# Brick #3 — source/AST: placement, key-blindness, non-recursion, type-only
# --------------------------------------------------------------------------- #

class TestExtraPayloadGuardShape(unittest.TestCase):

    def setUp(self):
        self.func = _method(_tree("memory_graph.py"), "MemoryGraph", "spawn_memory")
        self.assertIsNotNone(self.func, "MemoryGraph.spawn_memory not found")
        self.body = _nondoc_body(self.func)
        self.assertGreaterEqual(len(self.body), 4,
                                "spawn_memory body shorter than expected")
        self.summary_guard = self.body[0]
        self.ep_obj_guard = self.body[1]
        self.ep_val_guard = self.body[2]

    def test_summary_guard_is_still_first_nondoc_statement(self):
        g = self.summary_guard
        self.assertIsInstance(g, ast.If)
        self.assertIsInstance(g.test, ast.Call)
        self.assertEqual(g.test.func.id, "isinstance")
        self.assertEqual(g.test.args[0].id, "summary")
        self.assertEqual(g.test.args[1].id, "CandidateShapedValue")

    def test_extra_payload_object_guard_is_second(self):
        g = self.ep_obj_guard
        self.assertIsInstance(g, ast.If)
        self.assertIsInstance(g.test, ast.Call)
        self.assertEqual(g.test.func.id, "isinstance")
        self.assertEqual(g.test.args[0].id, "extra_payload")
        self.assertEqual(g.test.args[1].id, "CandidateShapedValue")
        self.assertEqual(len(g.body), 1)
        self.assertIsInstance(g.body[0], ast.Raise)
        self.assertEqual(g.body[0].exc.func.id, "TypeError")

    def test_extra_payload_value_guard_is_third(self):
        g = self.ep_val_guard
        # `if extra_payload:` wrapping a single for-loop over .values()
        self.assertIsInstance(g, ast.If)
        self.assertIsInstance(g.test, ast.Name)
        self.assertEqual(g.test.id, "extra_payload")
        self.assertEqual(len(g.body), 1)
        self.assertIsInstance(g.body[0], ast.For)

    def test_value_guard_iterates_values_only(self):
        forloop = self.ep_val_guard.body[0]
        self.assertIsInstance(forloop, ast.For)
        it = forloop.iter
        self.assertIsInstance(it, ast.Call)
        self.assertIsInstance(it.func, ast.Attribute)
        self.assertEqual(it.func.attr, "values")           # not keys/items/get
        self.assertIsInstance(it.func.value, ast.Name)
        self.assertEqual(it.func.value.id, "extra_payload")
        self.assertEqual(it.args, [])                       # values() takes no args
        self.assertEqual(len(forloop.body), 1)
        inner = forloop.body[0]
        self.assertIsInstance(inner, ast.If)
        self.assertIsInstance(inner.test, ast.Call)
        self.assertEqual(inner.test.func.id, "isinstance")  # type-only
        self.assertIsInstance(inner.test.args[0], ast.Name)  # the loop var, by type
        self.assertEqual(inner.test.args[1].id, "CandidateShapedValue")
        self.assertEqual(len(inner.body), 1)
        self.assertIsInstance(inner.body[0], ast.Raise)
        self.assertEqual(inner.body[0].exc.func.id, "TypeError")

    def test_value_guard_has_no_nested_iteration_or_recursion(self):
        region = (self.ep_obj_guard, self.ep_val_guard)
        fors = [n for stmt in region for n in ast.walk(stmt) if isinstance(n, ast.For)]
        self.assertEqual(len(fors), 1, "exactly one loop expected in extra_payload guard")
        for n in ast.walk(fors[0]):
            self.assertNotIsInstance(
                n, (ast.While, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp),
                msg="no nested/comprehension iteration allowed")
            if isinstance(n, ast.Call):
                name = (n.func.attr if isinstance(n.func, ast.Attribute)
                        else getattr(n.func, "id", None))
                self.assertNotIn(name, {"spawn_memory", "add_memory", "update_payload"})

    def test_guard_has_no_subscript_or_comparison(self):
        for stmt in (self.ep_obj_guard, self.ep_val_guard):
            for n in ast.walk(stmt):
                self.assertNotIsInstance(n, ast.Subscript,
                                         msg="guard must not subscript/index")
                self.assertNotIsInstance(n, ast.Compare,
                                         msg="guard must not compare (no key/content match)")

    def test_guard_only_attribute_is_values_on_extra_payload(self):
        attrs = [n for stmt in (self.ep_obj_guard, self.ep_val_guard)
                 for n in ast.walk(stmt) if isinstance(n, ast.Attribute)]
        self.assertTrue(attrs, "expected the .values() attribute access")
        for a in attrs:
            self.assertEqual(a.attr, "values", msg=f"unexpected attribute .{a.attr}")
            self.assertIsInstance(a.value, ast.Name)
            self.assertEqual(a.value.id, "extra_payload")

    def test_guard_messages_are_contents_free_constants(self):
        raises = [n for stmt in (self.ep_obj_guard, self.ep_val_guard)
                  for n in ast.walk(stmt) if isinstance(n, ast.Raise)]
        self.assertEqual(len(raises), 2)
        for r in raises:
            for n in ast.walk(r):
                self.assertNotIsInstance(n, ast.JoinedStr,
                                         msg="raise message must not be an f-string")
            self.assertIsInstance(r.exc, ast.Call)
            self.assertEqual(r.exc.func.id, "TypeError")
            self.assertIsInstance(r.exc.args[0], ast.Constant)
            self.assertIsInstance(r.exc.args[0].value, str)
            ref_names = {n.id for n in ast.walk(r) if isinstance(n, ast.Name)}
            self.assertEqual(ref_names, {"TypeError"},
                             msg=f"raise references unexpected names: {ref_names}")

    def test_extra_payload_guards_do_not_touch_self(self):
        for stmt in (self.ep_obj_guard, self.ep_val_guard):
            names = {n.id for n in ast.walk(stmt) if isinstance(n, ast.Name)}
            self.assertNotIn("self", names)

    def test_guard_region_has_no_side_effecting_calls(self):
        forbidden = {"spawn", "update", "append", "_log_event", "_append_jsonl",
                     "_register_embedding", "save", "index_node", "flush_node"}
        for stmt in (self.summary_guard, self.ep_obj_guard, self.ep_val_guard):
            for n in ast.walk(stmt):
                if isinstance(n, ast.Call):
                    name = (n.func.attr if isinstance(n.func, ast.Attribute)
                            else getattr(n.func, "id", None))
                    self.assertNotIn(name, forbidden,
                                     msg=f"side-effecting call {name} inside guard region")

    def test_links_remains_unguarded_by_this_brick(self):
        # No candidate guard references `links`; the link edge-write loop is
        # still present and unmodified. links stays UNRESOLVED for this brick.
        for n in ast.walk(self.func):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id == "isinstance" and len(n.args) == 2
                    and isinstance(n.args[1], ast.Name)
                    and n.args[1].id == "CandidateShapedValue"):
                self.assertIsInstance(n.args[0], ast.Name)
                self.assertNotEqual(n.args[0].id, "links",
                                    msg="links must remain unguarded by this brick")
        self.assertIn("for tgt in links:", _read("memory_graph.py"))


if __name__ == "__main__":
    unittest.main()
