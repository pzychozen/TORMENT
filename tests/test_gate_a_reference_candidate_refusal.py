"""Gate A Layer 4 — brick #5: ReferenceStore.ingest candidate refusal.

ReferenceStore.ingest refuses a candidate-shaped value arriving as title / body /
source_link / source_kind, as the metadata object, or as an immediate metadata
value — as its FIRST executable statements, before ref_id allocation,
compute_source_hash, ReferenceEntry construction, self._entries mutation,
_append_jsonl, and event writes. Named fields are checked individually; metadata
is key-blind (.values()), non-recursive, immediate-value-only. `provenance` is
internally constructed by fabric.ingest_reference and is NOT inspected here.

NOT wall completion; ArchiveStore, links, update_payload remain unguarded.
"""
import ast
import os
import tempfile
import unittest

from torment_service.candidate_types import CandidateShapedValue
from torment_service.reference_memory import ReferenceStore


_SECRET = "SUPER_SECRET_SEALED_REFERENCE_FIELD_DO_NOT_LEAK"


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


# --------------------------------------------------------------------------- #
# Runtime: pre-side-effect refusal + ghost non-exposure
# --------------------------------------------------------------------------- #

class TestReferenceRefusalRuntime(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store = ReferenceStore(data_dir=self.tmp, workspace_id="ws1")

    def _ok_kwargs(self, **ov):
        kw = dict(title="t", body="b", source_link="http://x",
                  source_kind="url", provenance={}, metadata={"k": "v"})
        kw.update(ov)
        return kw

    def _assert_refused(self, **ov):
        before = dict(self.store._entries)
        with self.assertRaises(TypeError) as ctx:
            self.store.ingest(**self._ok_kwargs(**ov))
        self.assertIs(type(ctx.exception), TypeError)
        self.assertEqual(self.store._entries, before)                 # no RAM ghost
        self.assertFalse(os.path.exists(self.store.references_path))  # no persistence
        return ctx.exception

    def test_candidate_title_refused(self):
        self._assert_refused(title=CandidateShapedValue(_SECRET))

    def test_candidate_body_refused(self):
        self._assert_refused(body=CandidateShapedValue(_SECRET))

    def test_candidate_source_link_refused(self):
        self._assert_refused(source_link=CandidateShapedValue(_SECRET))

    def test_candidate_source_kind_refused(self):
        self._assert_refused(source_kind=CandidateShapedValue(_SECRET))

    def test_candidate_metadata_object_refused(self):
        self._assert_refused(metadata=CandidateShapedValue(_SECRET))

    def test_candidate_metadata_value_refused(self):
        self._assert_refused(metadata={"k": CandidateShapedValue(_SECRET)})

    def test_error_messages_are_contents_free(self):
        for ov in (
            dict(title=CandidateShapedValue(_SECRET)),
            dict(body=CandidateShapedValue(_SECRET)),
            dict(source_link=CandidateShapedValue(_SECRET)),
            dict(source_kind=CandidateShapedValue(_SECRET)),
            dict(metadata=CandidateShapedValue(_SECRET)),
            dict(metadata={"k": CandidateShapedValue(_SECRET)}),
        ):
            exc = self._assert_refused(**ov)
            self.assertNotIn(_SECRET, str(exc))

    def test_ordinary_reference_ingest_unchanged(self):
        entry = self.store.ingest(**self._ok_kwargs())
        self.assertEqual(entry.title, "t")
        self.assertEqual(entry.body, "b")
        self.assertEqual(self.store.reference_count, 1)
        self.assertEqual(len(self.store.list()), 1)

    def test_get_list_cannot_expose_refused_ghost(self):
        with self.assertRaises(TypeError):
            self.store.ingest(**self._ok_kwargs(body=CandidateShapedValue(_SECRET)))
        self.assertEqual(self.store._entries, {})
        self.assertEqual(self.store.list(), [])


# --------------------------------------------------------------------------- #
# Source/AST: type-only, key-blind, non-recursive, immediate-value-only
# --------------------------------------------------------------------------- #

class TestReferenceGuardShape(unittest.TestCase):

    def setUp(self):
        self.ingest = _method(_tree("reference_memory.py"), "ReferenceStore", "ingest")
        self.assertIsNotNone(self.ingest, "ReferenceStore.ingest not found")
        self.body = self.ingest.body
        self.named = self._isinstance_guards(self.body)
        self.meta_value_guard = self._find_meta_value_guard()

    @staticmethod
    def _isinstance_guards(body):
        out = {}
        for s in body:
            if (isinstance(s, ast.If) and isinstance(s.test, ast.Call)
                    and isinstance(s.test.func, ast.Name) and s.test.func.id == "isinstance"
                    and len(s.test.args) == 2
                    and isinstance(s.test.args[0], ast.Name)
                    and isinstance(s.test.args[1], ast.Name)
                    and s.test.args[1].id == "CandidateShapedValue"):
                out[s.test.args[0].id] = s
        return out

    def _find_meta_value_guard(self):
        for s in self.body:
            if (isinstance(s, ast.If) and isinstance(s.test, ast.Name)
                    and s.test.id == "metadata"
                    and len(s.body) == 1 and isinstance(s.body[0], ast.For)):
                return s
        return None

    def _guard_stmts(self):
        return [s for s in self.body
                if any(isinstance(n, ast.Name) and n.id == "CandidateShapedValue"
                       for n in ast.walk(s))]

    def test_named_field_guards_present_type_only_no_provenance(self):
        for f in ("title", "body", "source_link", "source_kind"):
            self.assertIn(f, self.named, msg=f"missing named guard for {f}")
            g = self.named[f]
            self.assertEqual(len(g.body), 1)
            self.assertIsInstance(g.body[0], ast.Raise)
            self.assertEqual(g.body[0].exc.func.id, "TypeError")
        self.assertIn("metadata", self.named)            # metadata object-level guard
        self.assertNotIn("provenance", self.named)       # provenance NOT inspected

    def test_metadata_value_guard_is_key_blind_values_only(self):
        self.assertIsNotNone(self.meta_value_guard)
        forloop = self.meta_value_guard.body[0]
        it = forloop.iter
        self.assertIsInstance(it, ast.Call)
        self.assertIsInstance(it.func, ast.Attribute)
        self.assertEqual(it.func.attr, "values")          # not keys/items/get
        self.assertIsInstance(it.func.value, ast.Name)
        self.assertEqual(it.func.value.id, "metadata")
        self.assertEqual(it.args, [])

    def test_metadata_value_guard_is_immediate_value_only(self):
        forloop = self.meta_value_guard.body[0]
        self.assertEqual(len(forloop.body), 1)
        inner = forloop.body[0]
        self.assertIsInstance(inner, ast.If)
        self.assertEqual(inner.test.func.id, "isinstance")
        self.assertIsInstance(inner.test.args[0], ast.Name)   # loop var, type-only
        self.assertEqual(inner.test.args[1].id, "CandidateShapedValue")
        self.assertEqual(len(inner.body), 1)
        self.assertIsInstance(inner.body[0], ast.Raise)

    def test_metadata_guard_has_no_nested_iteration(self):
        forloop = self.meta_value_guard.body[0]
        for n in ast.walk(forloop.body[0]):
            self.assertNotIsInstance(
                n, (ast.For, ast.While, ast.ListComp, ast.SetComp,
                    ast.DictComp, ast.GeneratorExp))

    def test_guards_have_no_subscript_compare_or_extra_attributes(self):
        for s in self._guard_stmts():
            for n in ast.walk(s):
                self.assertNotIsInstance(n, ast.Subscript, msg="no subscript/key indexing")
                self.assertNotIsInstance(n, ast.Compare, msg="no comparison/content matching")
                if isinstance(n, ast.Attribute):
                    self.assertEqual(n.attr, "values", msg=f"unexpected attribute .{n.attr}")
                    self.assertIsInstance(n.value, ast.Name)
                    self.assertEqual(n.value.id, "metadata")

    def test_guards_call_only_isinstance_and_typeerror(self):
        calls = set()
        for s in self._guard_stmts():
            for n in ast.walk(s):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                    calls.add(n.func.id)
        self.assertEqual(calls, {"isinstance", "TypeError"})

    def test_guard_messages_are_contents_free_constants(self):
        for s in self._guard_stmts():
            for r in [n for n in ast.walk(s) if isinstance(n, ast.Raise)]:
                for n in ast.walk(r):
                    self.assertNotIsInstance(n, ast.JoinedStr, msg="no f-string")
                self.assertIsInstance(r.exc.args[0], ast.Constant)
                ref_names = {n.id for n in ast.walk(r) if isinstance(n, ast.Name)}
                self.assertEqual(ref_names, {"TypeError"})

    def test_guards_do_not_reference_provenance_or_self(self):
        names = set()
        for s in self._guard_stmts():
            names |= {n.id for n in ast.walk(s) if isinstance(n, ast.Name)}
        self.assertNotIn("provenance", names)
        self.assertNotIn("self", names)

    def test_guards_precede_all_side_effects(self):
        guard_idx = [i for i, s in enumerate(self.body)
                     if any(isinstance(n, ast.Name) and n.id == "CandidateShapedValue"
                            for n in ast.walk(s))]
        self.assertTrue(guard_idx)

        def idx_where(pred):
            for i, s in enumerate(self.body):
                if pred(s):
                    return i
            return None

        idx_refid = idx_where(lambda s: isinstance(s, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "ref_id" for t in s.targets))
        idx_hash = idx_where(lambda s: any(isinstance(n, ast.Attribute)
            and n.attr == "compute_source_hash" for n in ast.walk(s)))
        idx_append = idx_where(lambda s: any(isinstance(n, ast.Attribute)
            and n.attr == "_append_jsonl" for n in ast.walk(s)))
        self.assertIsNotNone(idx_refid)
        self.assertIsNotNone(idx_hash)
        self.assertIsNotNone(idx_append)
        self.assertLess(max(guard_idx), idx_refid)        # before ref_id allocation
        self.assertLess(max(guard_idx), idx_hash)         # before compute_source_hash
        self.assertLess(max(guard_idx), idx_append)       # before persistence


if __name__ == "__main__":
    unittest.main()
