"""Gate A Layer 4 — brick #4: EnvironmentStore.write value candidate refusal.

EnvironmentStore.write refuses a candidate-shaped `value` AFTER evidence-class
and required-field validation (envelope rejections preserved) and BEFORE env_id
allocation, EnvironmentEntry construction, self._entries mutation, _append_jsonl,
and event writes. `value` is the one caller-forwarded Any sink validate_evidence
does not cover and that consult projects back via EnvironmentFactView.value.

Single named-field, type-only, non-recursive, contents-free. NOT wall completion;
target_runtime/scope_tag/key/metadata/provenance and the other stores remain
unguarded by this brick.
"""
import ast
import os
import tempfile
import unittest

from torment_service.candidate_types import CandidateShapedValue
from torment_service.environment_memory import EnvironmentStore


_SECRET = "SUPER_SECRET_SEALED_ENV_VALUE_DO_NOT_LEAK"


def _service_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "torment_service")


def _read(filename):
    with open(os.path.join(_service_dir(), filename), "rb") as fh:
        return fh.read().replace(b"\x00", b"").decode("utf-8", "replace")


def _tree(filename):
    return ast.parse(_read(filename))


def _method(tree, cls, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == name:
                    return m
    return None


def _valid_kwargs(value):
    # A valid user_asserted envelope so the candidate guard (placed AFTER
    # validation) is what fires — not an evidence/required-field rejection.
    return dict(
        target_runtime="python3.10",
        scope_tag="proc",
        key="net",
        value=value,
        evidence_class="user_asserted",
        ownership="user",
        provenance={},
        asserted_by="operator",
    )


# --------------------------------------------------------------------------- #
# Runtime: pre-side-effect refusal + consult non-exposure
# --------------------------------------------------------------------------- #

class TestEnvironmentValueRefusalRuntime(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store = EnvironmentStore(data_dir=self.tmp, workspace_id="ws1")

    def test_candidate_value_raises_before_entries_change(self):
        before = dict(self.store._entries)
        with self.assertRaises(TypeError) as ctx:
            self.store.write(**_valid_kwargs(CandidateShapedValue(_SECRET)))
        self.assertIs(type(ctx.exception), TypeError)
        self.assertEqual(self.store._entries, before)              # no RAM ghost
        self.assertFalse(os.path.exists(self.store.entries_path))  # no persistence

    def test_refused_candidate_value_never_appears_in_consult(self):
        with self.assertRaises(TypeError):
            self.store.write(**_valid_kwargs(CandidateShapedValue(_SECRET)))
        res = self.store.consult(operation="probe", scope="proc")
        self.assertEqual(res.facts, [])

    def test_error_message_is_contents_free(self):
        with self.assertRaises(TypeError) as ctx:
            self.store.write(**_valid_kwargs(CandidateShapedValue(_SECRET)))
        self.assertNotIn(_SECRET, str(ctx.exception))

    def test_ordinary_value_still_writes_and_consults(self):
        res = self.store.write(**_valid_kwargs("no-network"))
        self.assertTrue(res["ok"])
        self.assertTrue(res["env_id"])
        facts = self.store.consult(operation="probe", scope="proc").facts
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].value, "no-network")

    def test_invalid_evidence_class_still_envelope_rejects_not_candidate_guard(self):
        kw = _valid_kwargs(CandidateShapedValue(_SECRET))
        kw["evidence_class"] = "bogus"
        res = self.store.write(**kw)               # must NOT raise
        self.assertFalse(res["ok"])
        self.assertEqual(res["result_code"], "missing_evidence_class")
        self.assertEqual(self.store._entries, {})

    def test_invalid_ownership_still_envelope_rejects_not_candidate_guard(self):
        kw = _valid_kwargs(CandidateShapedValue(_SECRET))
        kw["ownership"] = "bogus"
        res = self.store.write(**kw)               # must NOT raise
        self.assertFalse(res["ok"])
        self.assertEqual(res["result_code"], "missing_evidence_field")
        self.assertEqual(self.store._entries, {})


# --------------------------------------------------------------------------- #
# Source/AST: type-only, named-field-only, non-recursive, contents-free
# --------------------------------------------------------------------------- #

class TestEnvironmentValueGuardShape(unittest.TestCase):

    def setUp(self):
        self.write = _method(_tree("environment_memory.py"), "EnvironmentStore", "write")
        self.assertIsNotNone(self.write, "EnvironmentStore.write not found")
        self.body = self.write.body
        self.guard, self.guard_idx = self._find_guard()

    def _find_guard(self):
        for i, stmt in enumerate(self.body):
            if (isinstance(stmt, ast.If) and isinstance(stmt.test, ast.Call)
                    and isinstance(stmt.test.func, ast.Name)
                    and stmt.test.func.id == "isinstance"
                    and len(stmt.test.args) == 2
                    and isinstance(stmt.test.args[0], ast.Name)
                    and stmt.test.args[0].id == "value"
                    and isinstance(stmt.test.args[1], ast.Name)
                    and stmt.test.args[1].id == "CandidateShapedValue"):
                return stmt, i
        self.fail("value candidate guard not found in EnvironmentStore.write")

    def _index_where(self, predicate):
        for i, stmt in enumerate(self.body):
            if predicate(stmt):
                return i
        return None

    def test_guard_is_type_only_isinstance_on_named_value(self):
        # already matched in _find_guard; assert the raise shape too
        self.assertEqual(len(self.guard.body), 1)
        raise_node = self.guard.body[0]
        self.assertIsInstance(raise_node, ast.Raise)
        self.assertIsInstance(raise_node.exc, ast.Call)
        self.assertIsInstance(raise_node.exc.func, ast.Name)
        self.assertEqual(raise_node.exc.func.id, "TypeError")

    def test_guard_runs_after_validation_before_side_effects(self):
        idx_validate = self._index_where(
            lambda s: any(isinstance(n, ast.Attribute) and n.attr == "validate_evidence"
                          for n in ast.walk(s)))
        idx_env_id = self._index_where(
            lambda s: isinstance(s, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "env_id" for t in s.targets))
        idx_append = self._index_where(
            lambda s: any(isinstance(n, ast.Attribute) and n.attr == "_append_jsonl"
                          for n in ast.walk(s)))
        self.assertIsNotNone(idx_validate)
        self.assertIsNotNone(idx_env_id)
        self.assertIsNotNone(idx_append)
        self.assertLess(idx_validate, self.guard_idx)            # validation preserved
        self.assertLess(self.guard_idx, idx_env_id)              # before allocation
        self.assertLess(self.guard_idx, idx_append)              # before persistence

    def test_guard_has_no_loop_or_comprehension(self):
        for n in ast.walk(self.guard):
            self.assertNotIsInstance(
                n, (ast.For, ast.While, ast.ListComp, ast.SetComp,
                    ast.DictComp, ast.GeneratorExp),
                msg="guard must not iterate")

    def test_guard_has_no_values_call_or_attribute_access(self):
        for n in ast.walk(self.guard):
            self.assertNotIsInstance(n, ast.Attribute,
                                     msg="guard must not access any attribute (.values etc.)")

    def test_guard_has_no_subscript_or_comparison(self):
        for n in ast.walk(self.guard):
            self.assertNotIsInstance(n, ast.Subscript, msg="no subscript/key indexing")
            self.assertNotIsInstance(n, ast.Compare, msg="no comparison/key matching")

    def test_guard_calls_only_isinstance_and_typeerror(self):
        calls = {n.func.id for n in ast.walk(self.guard)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertEqual(calls, {"isinstance", "TypeError"})

    def test_guard_message_is_contents_free_constant(self):
        raise_node = self.guard.body[0]
        for n in ast.walk(raise_node):
            self.assertNotIsInstance(n, ast.JoinedStr, msg="no f-string")
        self.assertIsInstance(raise_node.exc.args[0], ast.Constant)
        self.assertIsInstance(raise_node.exc.args[0].value, str)
        ref_names = {n.id for n in ast.walk(raise_node) if isinstance(n, ast.Name)}
        self.assertEqual(ref_names, {"TypeError"})              # no value/field interpolation

    def test_guard_references_only_value_not_other_fields(self):
        names = {n.id for n in ast.walk(self.guard) if isinstance(n, ast.Name)}
        for other in ("target_runtime", "scope_tag", "key", "metadata",
                      "provenance", "observation_source", "asserted_by",
                      "evidence_class", "ownership", "self"):
            self.assertNotIn(other, names, msg=f"guard unexpectedly references {other}")


if __name__ == "__main__":
    unittest.main()
