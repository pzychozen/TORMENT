"""Gate A Layer 4 — first ordinary-ingest containment brick: candidate refusal.

Covers the smallest text-boundary brick:

  * an inert ``CandidateShapedValue`` (constrained A+D representation) and
  * a content-blind, type-only deny check that is the FIRST executable statement
    of ``TormentFabric.ingest``, refusing a candidate-shaped ``text`` BEFORE
    ``_agent_key`` / ``create_agent`` / provenance / kernel processing / any
    fan-out or mutation.

Runtime proof strategy: call the (unbound) ``TormentFabric.ingest`` with a
``self`` sentinel whose ``__getattribute__`` raises on ANY attribute access. If
the refusal precedes everything, a candidate ``text`` raises ``TypeError`` WITHOUT
the sentinel ever being touched; an ordinary string ``text`` instead flows past
the guard and trips the sentinel at the first real statement (``self._agent_key``).
This proves pre-mutation refusal without constructing a real fabric.

SCOPE / UNRESOLVED (deliberately preserved, NOT bugs):
  * Text-only brick. Non-text ingest parameters (supplied_summary, extra_payload,
    supplied_embedding, provenance, ...) are NOT policed here and remain
    unresolved.
  * The known direct-writer bypasses (promotion spawn_memory, identity-anchor /
    mood-drift emitters, character seeding, shared-graph add_memory, _fast_feedback
    update_payload, ingest_reference / write_environment, ArchiveStore.ingest_document)
    remain unresolved and out of scope.
  * This is NOT wall completion.
"""

import ast
import os
import unittest

from torment_service.candidate_types import CandidateShapedValue
from torment_service.fabric import TormentFabric


_SECRET = "SUPER_SECRET_SENTINEL_CONTENTS_DO_NOT_LEAK"


def _service_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "torment_service")


def _tree(filename):
    with open(os.path.join(_service_dir(), filename), "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))


def _read(filename):
    with open(os.path.join(_service_dir(), filename), "rb") as fh:
        return fh.read().replace(b"\x00", b"").decode("utf-8", "replace")


def _ingest_func(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "TormentFabric":
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == "ingest":
                    return m
    return None


class _TripSelf:
    """A `self` stand-in that raises on ANY attribute access.

    If `ingest` touches `self` at all before refusing a candidate `text`, the
    refusal is not truly pre-mutation and the test fails loudly.
    """

    def __getattribute__(self, name):
        raise AssertionError(
            f"ingest accessed self.{name} before refusing candidate text")


# --------------------------------------------------------------------------- #
# The inert type itself
# --------------------------------------------------------------------------- #

class TestCandidateShapedValueIsInertAndOpaque(unittest.TestCase):

    def test_not_an_ordinary_type(self):
        c = CandidateShapedValue("x")
        self.assertNotIsInstance(c, str)
        self.assertNotIsInstance(c, bytes)
        self.assertNotIsInstance(c, dict)

    def test_repr_is_contents_free(self):
        self.assertNotIn(_SECRET, repr(CandidateShapedValue(_SECRET)))

    def test_sealed_no_dict_no_public_accessor(self):
        c = CandidateShapedValue(_SECRET)
        # Slotted: no __dict__, so generic serializers cannot walk it.
        self.assertFalse(hasattr(c, "__dict__"))
        # No public accessor / serialization helper exposed.
        for forbidden in ("value", "get", "to_dict", "unwrap", "reveal"):
            self.assertFalse(hasattr(c, forbidden),
                             msg=f"unexpected public accessor: {forbidden}")

    def test_not_iterable_no_item_access(self):
        c = CandidateShapedValue(_SECRET)
        with self.assertRaises(TypeError):
            iter(c)
        with self.assertRaises(TypeError):
            c[0]  # noqa: B018

    def test_module_is_dependency_free_of_package(self):
        src = _read("candidate_types.py")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                # No relative imports from the TORMENT package (avoids cycles).
                self.assertEqual(node.level, 0,
                                 msg="candidate_types.py must not import from the package")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                else:
                    names = [node.module or ""]
                for n in names:
                    self.assertNotIn("torment_service", n)


# --------------------------------------------------------------------------- #
# Runtime: pre-mutation refusal
# --------------------------------------------------------------------------- #

class TestPreMutationRefusal(unittest.TestCase):

    def test_candidate_text_refused_before_self_touched(self):
        # Candidate `text` -> TypeError, and the self sentinel is NEVER accessed
        # (no _agent_key, no create_agent, no kernel.process, no mutation).
        with self.assertRaises(TypeError) as ctx:
            TormentFabric.ingest(
                _TripSelf(), workspace_id="w", agent_id="a",
                text=CandidateShapedValue(_SECRET),
            )
        # If self had been touched, this would be AssertionError, not TypeError.
        self.assertIs(type(ctx.exception), TypeError)

    def test_error_is_contents_free(self):
        with self.assertRaises(TypeError) as ctx:
            TormentFabric.ingest(
                _TripSelf(), workspace_id="w", agent_id="a",
                text=CandidateShapedValue(_SECRET),
            )
        self.assertNotIn(_SECRET, str(ctx.exception))

    def test_ordinary_string_passes_guard_to_first_real_statement(self):
        # An ordinary string is NOT refused by the guard; it flows through to the
        # first real statement, which accesses self._agent_key -> trips sentinel.
        # This proves (a) ordinary string ingest is unchanged by the guard, and
        # (b) the refusal sits immediately before _agent_key.
        with self.assertRaises(AssertionError) as ctx:
            TormentFabric.ingest(
                _TripSelf(), workspace_id="w", agent_id="a", text="hello world",
            )
        self.assertIn("_agent_key", str(ctx.exception))


# --------------------------------------------------------------------------- #
# Source / AST: placement, content-blindness, text-only scope
# --------------------------------------------------------------------------- #

class TestRefusalPlacementAndShape(unittest.TestCase):

    def setUp(self):
        self.func = _ingest_func(_tree("fabric.py"))
        self.assertIsNotNone(self.func, "TormentFabric.ingest not found")
        self.guard = self.func.body[0]

    def test_guard_is_first_statement(self):
        self.assertIsInstance(self.guard, ast.If,
                              "first statement of ingest is not the refusal guard")

    def test_guard_test_is_type_only_isinstance(self):
        test = self.guard.test
        self.assertIsInstance(test, ast.Call)
        self.assertIsInstance(test.func, ast.Name)
        self.assertEqual(test.func.id, "isinstance")
        self.assertEqual(len(test.args), 2)
        self.assertIsInstance(test.args[0], ast.Name)
        self.assertEqual(test.args[0].id, "text")
        self.assertIsInstance(test.args[1], ast.Name)
        self.assertEqual(test.args[1].id, "CandidateShapedValue")

    def test_guard_body_is_single_raise_typeerror(self):
        self.assertEqual(len(self.guard.body), 1)
        raise_node = self.guard.body[0]
        self.assertIsInstance(raise_node, ast.Raise)
        self.assertIsInstance(raise_node.exc, ast.Call)
        self.assertIsInstance(raise_node.exc.func, ast.Name)
        self.assertEqual(raise_node.exc.func.id, "TypeError")

    def test_guard_does_not_touch_self_or_mutate(self):
        # No `self` reference anywhere in the guard => precedes any attribute
        # access, fan-out, or mutation.
        names = {n.id for n in ast.walk(self.guard) if isinstance(n, ast.Name)}
        self.assertNotIn("self", names)

    def test_guard_calls_only_isinstance_and_typeerror(self):
        calls = {n.func.id for n in ast.walk(self.guard)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertEqual(calls, {"isinstance", "TypeError"},
                         msg=f"unexpected calls in guard: {sorted(calls)}")

    def test_guard_is_content_blind(self):
        # No attribute access on `text`, no subscript, no .get — the guard never
        # reads contents/metadata/tags/payload keys/provenance/markers.
        for n in ast.walk(self.guard):
            if isinstance(n, ast.Attribute):
                self.fail(f"guard performs attribute access: .{n.attr}")
            if isinstance(n, ast.Subscript):
                self.fail("guard performs item/subscript access")

    def test_raise_message_does_not_interpolate_value(self):
        raise_node = self.guard.body[0]
        # The exception args must be plain constant strings (no Name 'text',
        # no f-string interpolating the value).
        for n in ast.walk(raise_node):
            self.assertNotIsInstance(n, ast.JoinedStr,
                                     msg="raise message must not be an f-string")
            if isinstance(n, ast.Name):
                self.assertNotEqual(n.id, "text",
                                    msg="raise message must not reference `text`")


class TestTextOnlyScopeAndUnresolvedGaps(unittest.TestCase):
    """Locks the text-only scope AND records the deliberately-unresolved gaps."""

    def setUp(self):
        self.guard = _ingest_func(_tree("fabric.py")).body[0]

    def test_guard_does_not_police_nontext_parameters(self):
        # The non-text ingest parameters are intentionally NOT inspected by this
        # first brick; their absence here is the preserved, unresolved gap.
        names = {n.id for n in ast.walk(self.guard) if isinstance(n, ast.Name)}
        for nontext in ("supplied_summary", "extra_payload", "supplied_embedding",
                        "provenance", "tri_mod", "domain_id", "memory_class", "scope"):
            self.assertNotIn(nontext, names,
                             msg=f"guard unexpectedly references non-text param {nontext}")

    def test_direct_writer_bypasses_remain_unresolved(self):
        # Documentation guard: this brick does not touch the direct-writer
        # bypasses. Asserting their continued existence keeps the incompleteness
        # explicit (this is NOT a claim they are contained).
        fabric_src = _read("fabric.py")
        promotion_src = _read("promotion.py")
        graph_src = _read("memory_graph.py")
        self.assertIn("def spawn_memory", graph_src)
        self.assertIn("spawn_memory", promotion_src)        # promotion bypass
        self.assertIn("_maybe_emit_identity_anchor", fabric_src)  # derived writer
        self.assertIn("def write_environment", fabric_src)        # writer bypass


class TestAppEndpointSchemaUntouched(unittest.TestCase):

    def test_app_does_not_reference_candidate_type(self):
        app_src = _read("app.py")
        self.assertNotIn("CandidateShapedValue", app_src)
        self.assertNotIn("candidate_types", app_src)

    def test_ingest_request_schema_unchanged(self):
        # IngestReq still declares a plain `text: str`; no new candidate field.
        at = _tree("app.py")
        ingest_req = None
        for node in ast.walk(at):
            if isinstance(node, ast.ClassDef) and node.name == "IngestReq":
                ingest_req = node
                break
        self.assertIsNotNone(ingest_req, "IngestReq not found")
        annotated = {}
        for stmt in ingest_req.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                ann = stmt.annotation
                annotated[stmt.target.id] = ann.id if isinstance(ann, ast.Name) else None
        self.assertEqual(annotated.get("text"), "str",
                         msg="IngestReq.text is no longer a plain str")


if __name__ == "__main__":
    unittest.main()
