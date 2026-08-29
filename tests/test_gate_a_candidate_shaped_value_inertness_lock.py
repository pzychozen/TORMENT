"""Gate A — CandidateShapedValue inertness anti-drift lock (tests-only / source-only).

Tests-only/source-only inertness lock. This test protects the existing sentinel from
drifting into representation, carrier, producer, accessor, authority, admission, or
runtime machinery. It authorizes no production code and no new behavior. Passing it
does not claim Gate A wall completion or Tier-2 progress.

Codex-authorized as the single safe code-adjacent seam found by the first
code-adjacent seam survey (`docs/TORMENT_GATE_A_FORK3_FIRST_CODE_ADJACENT_SEAM_SURVEY_v0.1.md`):
a defensive regression guard that the Layer-4 inert sentinel `CandidateShapedValue`
STAYS inert. It selects no carrier / store / schema / field / enum / ID / API /
runtime / persistence / producer / admission / promotion / authority option; it does
NOT select `CandidateShapedValue` as a representation/carrier, and does NOT reopen
the Layer 4 brick series.

Exact question locked:
  Does `CandidateShapedValue` remain an inert, opaque, carrier-less sentinel used only
  by the classified Layer-4 negative-refusal perimeter, with no producer, no accessor,
  no serialization shape, no authority semantics, and no expansion into runtime /
  admission / carrier machinery?

Method: pure AST/source scanning (no production import, no production execution),
mirroring the established Gate A characterization style
(`tests/test_gate_a_seam_b_ingest_entry_characterization.py`,
`tests/test_gate_a_seam_c_writer_authority_ao2_characterization.py`). Structural
ABSENCE is asserted (the inert dunders / accessors / factories are simply not
defined), which is a stronger anti-drift guarantee than runtime probing.

If any guard here fails, do NOT patch production — return it as a gate decision.
"""

import ast
import os
import unittest


_CANDIDATE_MODULE = "candidate_types.py"
_CLASS = "CandidateShapedValue"
_TOKEN = "CandidateShapedValue"

# The ONLY service modules that may reference the inert sentinel: its definition +
# the six landed Layer-4 negative-refusal surfaces (memory_graph holds two;
# substrate compat adds a type-only create/patch refusal, not candidate storage).
_FOOTPRINT_MODULES = frozenset({
    "candidate_types.py",
    "fabric.py",
    "memory_graph.py",
    "environment_memory.py",
    "reference_memory.py",
    "compat.py",
})

# The class must define EXACTLY these methods — the inert minimal API.
_ALLOWED_METHODS = frozenset({"__init__", "__repr__"})

# Accessor / serialization / payload method names that must NOT be defined.
_FORBIDDEN_API_METHODS = frozenset({
    "value", "get", "to_dict", "to_json", "asdict", "dict", "json",
    "unwrap", "reveal", "serialize", "deserialize", "loads", "dumps",
    "keys", "values", "items",
    "__iter__", "__next__", "__getitem__", "__setitem__", "__len__", "__contains__",
    "__getstate__", "__setstate__", "__reduce__", "__reduce_ex__",
    "__getattr__", "__setattr__", "__delattr__", "__call__", "__eq__", "__hash__",
})

# Factory / producer name fragments a method must not carry.
_FACTORY_FRAGMENTS = ("for_", "from_", "create", "build", "make", "new", "produce",
                      "factory", "construct", "spawn", "of_")

# Authority / admission / promotion / carrier vocabulary that must not appear in
# CODE positions (identifiers, names, non-docstring string constants). Docstrings
# and comments are intentionally excluded — the module docstring legitimately uses
# these words in NEGATED form ("NO governed admission, NO promotion, ...").
_FORBIDDEN_VOCAB = (
    "authority", "admission", "admit", "promote", "promotion", "canon",
    "identity", "tier", "seed", "carrier", "schema", "serialize", "serialization",
    "persist", "persistence", "store", "registry", "ledger", "endpoint",
)


# --------------------------------------------------------------------------- #
# Source / AST helpers
# --------------------------------------------------------------------------- #

def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _service_dir():
    return os.path.join(_repo_root(), "torment_service")


def _docs_dir():
    return os.path.join(_repo_root(), "docs")


def _src(basename):
    with open(os.path.join(_service_dir(), basename), "rb") as fh:
        return fh.read().replace(b"\x00", b"").decode("utf-8", "replace")


def _tree(basename):
    return ast.parse(_src(basename))


def _read_doc(name):
    with open(os.path.join(_docs_dir(), name), "r", encoding="utf-8") as fh:
        return fh.read()


def _class(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and n.name == name:
            return n
    return None


def _methods(cls):
    return [m for m in cls.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _method(cls, name):
    for m in _methods(cls):
        if m.name == name:
            return m
    return None


def _iter_service():
    skip = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "node_modules"}
    for dp, dns, fns in os.walk(_service_dir()):
        dns[:] = [d for d in dns if d not in skip and not d.startswith("do_not_touch")]
        for fn in fns:
            if not fn.endswith(".py"):
                continue
            ab = os.path.join(dp, fn)
            try:
                with open(ab, "rb") as fh:
                    src = fh.read().replace(b"\x00", b"")
                tree = ast.parse(src)
            except (SyntaxError, ValueError, OSError):
                continue
            yield os.path.relpath(ab, _service_dir()).replace("\\", "/"), src.decode("utf-8", "replace"), tree


def _docstring_constant_ids(tree):
    """id() of every Constant node that is a docstring (first stmt of a module /
    class / function body)."""
    ids = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(n, "body", [])
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                ids.add(id(body[0].value))
    return ids


def _code_tokens(tree):
    """Identifiers + non-docstring string constants (lowercased) used in CODE
    positions. Excludes docstrings; comments are not in the AST at all."""
    doc_ids = _docstring_constant_ids(tree)
    toks = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            toks.add(n.id)
        elif isinstance(n, ast.Attribute):
            toks.add(n.attr)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            toks.add(n.name)
        elif isinstance(n, ast.arg):
            toks.add(n.arg)
        elif isinstance(n, ast.keyword) and n.arg:
            toks.add(n.arg)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            if id(n) not in doc_ids:
                toks.add(n.value)
    return {t.lower() for t in toks}


def _calls_constructing(tree, name):
    """Call nodes whose func is a bare Name == `name` (i.e. construction)."""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == name:
            out.append(getattr(n, "lineno", -1))
    return out


# --------------------------------------------------------------------------- #
# 1. Minimal inert API (the anti-drift whitelist)
# --------------------------------------------------------------------------- #

class TestMinimalInertAPI(unittest.TestCase):

    def setUp(self):
        self.cls = _class(_tree(_CANDIDATE_MODULE), _CLASS)
        self.assertIsNotNone(self.cls, f"{_CLASS} not found in {_CANDIDATE_MODULE}")

    def test_no_base_classes(self):
        # No parent => cannot inherit payload / accessor / serialization behavior.
        self.assertEqual(self.cls.bases, [], "CandidateShapedValue grew a base class")
        self.assertEqual(self.cls.keywords, [], "CandidateShapedValue grew a class keyword (e.g. metaclass)")

    def test_slots_is_exactly_one_private_sealed_slot(self):
        slots_assign = None
        for stmt in self.cls.body:
            if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                    and stmt.targets[0].id == "__slots__"):
                slots_assign = stmt
        self.assertIsNotNone(slots_assign, "__slots__ missing (no __dict__ guarantee lost)")
        seq = slots_assign.value
        self.assertIsInstance(seq, (ast.Tuple, ast.List), "__slots__ is not a literal tuple/list")
        names = [e.value for e in seq.elts if isinstance(e, ast.Constant)]
        self.assertEqual(names, ["_sealed"], f"__slots__ changed from ('_sealed',): {names}")

    def test_methods_are_exactly_init_and_repr(self):
        names = {m.name for m in _methods(self.cls)}
        self.assertEqual(
            names, set(_ALLOWED_METHODS),
            msg=f"CandidateShapedValue method set drifted from {sorted(_ALLOWED_METHODS)}: {sorted(names)}")

    def test_no_forbidden_accessor_or_serialization_methods(self):
        names = {m.name for m in _methods(self.cls)}
        bad = names & _FORBIDDEN_API_METHODS
        self.assertEqual(bad, set(), msg=f"forbidden accessor/serialization method(s): {sorted(bad)}")

    def test_no_factory_classmethod_staticmethod_or_property(self):
        for m in _methods(self.cls):
            for d in m.decorator_list:
                dname = d.id if isinstance(d, ast.Name) else getattr(d, "attr", "")
                self.assertNotIn(dname, {"classmethod", "staticmethod", "property"},
                                 msg=f"{m.name} carries a {dname} decorator (factory/accessor drift)")
            low = m.name.lower()
            self.assertFalse(any(frag in low for frag in _FACTORY_FRAGMENTS),
                             msg=f"{m.name} looks like a factory/producer method")

    def test_no_public_class_level_fields(self):
        targets = []
        for stmt in self.cls.body:
            if isinstance(stmt, ast.Assign):
                targets += [t.id for t in stmt.targets if isinstance(t, ast.Name)]
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                targets.append(stmt.target.id)
        self.assertEqual(set(targets), {"__slots__"},
                         msg=f"class-level field(s) beyond __slots__: {sorted(set(targets))}")


# --------------------------------------------------------------------------- #
# 2. No serialization / iteration / payload behavior
# --------------------------------------------------------------------------- #

class TestNoSerializationOrPayloadShape(unittest.TestCase):

    def setUp(self):
        self.cls = _class(_tree(_CANDIDATE_MODULE), _CLASS)

    def test_no_iteration_item_or_len_dunders(self):
        names = {m.name for m in _methods(self.cls)}
        for dunder in ("__iter__", "__next__", "__getitem__", "__setitem__",
                       "__len__", "__contains__"):
            self.assertNotIn(dunder, names, msg=f"{dunder} defined (iteration/item access drift)")

    def test_no_dict_and_no_pickle_serialization_hooks(self):
        names = {m.name for m in _methods(self.cls)}
        for dunder in ("__getstate__", "__setstate__", "__reduce__", "__reduce_ex__"):
            self.assertNotIn(dunder, names, msg=f"{dunder} defined (serialization shape drift)")
        # __slots__ without __dict__ entry => no instance __dict__ for generic serializers.
        slots_tokens = _code_tokens(_tree(_CANDIDATE_MODULE))
        self.assertNotIn("__dict__", slots_tokens, "candidate_types references __dict__")

    def test_repr_is_contents_free_constant(self):
        rep = _method(self.cls, "__repr__")
        self.assertIsNotNone(rep, "__repr__ missing")
        returns = [n for n in ast.walk(rep) if isinstance(n, ast.Return)]
        self.assertEqual(len(returns), 1, "__repr__ has more than one return")
        self.assertIsInstance(returns[0].value, ast.Constant, "__repr__ does not return a plain constant")
        self.assertIsInstance(returns[0].value.value, str)
        for n in ast.walk(rep):
            self.assertNotIsInstance(n, ast.JoinedStr, "__repr__ uses an f-string (could leak contents)")
            if isinstance(n, ast.Name):
                self.assertNotIn(n.id, {"value", "_sealed"},
                                 msg="__repr__ references the sealed value (contents leak)")

    def test_init_only_seals_the_value(self):
        init = _method(self.cls, "__init__")
        self.assertIsNotNone(init, "__init__ missing")
        # No calls (no super(), no factory, no side effects).
        self.assertEqual([n for n in ast.walk(init) if isinstance(n, ast.Call)], [],
                         msg="__init__ performs a call (side effect / factory drift)")
        # Every assignment targets exactly self._sealed.
        for stmt in init.body:
            if isinstance(stmt, ast.Assign):
                for t in stmt.targets:
                    self.assertTrue(
                        isinstance(t, ast.Attribute) and t.attr == "_sealed"
                        and isinstance(t.value, ast.Name) and t.value.id == "self",
                        msg="__init__ assigns something other than self._sealed")
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.fail("__init__ defines a nested function/class")


# --------------------------------------------------------------------------- #
# 3. No authority / admission / promotion / carrier vocabulary (code positions)
# --------------------------------------------------------------------------- #

class TestNoAuthorityVocabulary(unittest.TestCase):

    def test_no_forbidden_vocab_in_code_positions(self):
        # Docstrings/comments excluded: the module docstring legitimately negates these
        # words. Any forbidden token in an identifier / name / non-docstring string is drift.
        tokens = _code_tokens(_tree(_CANDIDATE_MODULE))
        offenders = sorted({t for t in tokens
                            if any(v in t for v in _FORBIDDEN_VOCAB)})
        self.assertEqual(offenders, [],
                         msg=f"authority/admission/carrier vocabulary in code position(s): {offenders}")

    def test_module_exports_only_the_sentinel(self):
        tree = _tree(_CANDIDATE_MODULE)
        all_assign = None
        for stmt in tree.body:
            if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                    and stmt.targets[0].id == "__all__"):
                all_assign = stmt
        self.assertIsNotNone(all_assign, "__all__ missing")
        exported = [e.value for e in all_assign.value.elts if isinstance(e, ast.Constant)]
        self.assertEqual(exported, [_CLASS], f"__all__ exports more than the sentinel: {exported}")

    def test_module_is_dependency_free_of_package(self):
        tree = _tree(_CANDIDATE_MODULE)
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom):
                self.assertEqual(n.level, 0, "candidate_types uses a relative import (package coupling)")
                self.assertNotIn("torment_service", (n.module or ""),
                                 "candidate_types imports from torment_service")
            if isinstance(n, ast.Import):
                for a in n.names:
                    self.assertNotIn("torment_service", a.name,
                                     "candidate_types imports from torment_service")


# --------------------------------------------------------------------------- #
# 4. No producer in production; perimeter footprint; no app exposure
# --------------------------------------------------------------------------- #

class TestNoProducerAndPerimeterFootprint(unittest.TestCase):

    def test_no_production_construction_of_the_sentinel(self):
        # Production references the sentinel ONLY via isinstance(x, CandidateShapedValue)
        # (the type as a Name argument), never by constructing it. Construction lives only
        # in tests/guards-by-test. A production construction would be a producer/factory path.
        offenders = {}
        for rel, _src_text, tree in _iter_service():
            calls = _calls_constructing(tree, _CLASS)
            if calls:
                offenders[rel] = calls
        self.assertEqual(offenders, {},
                         msg=f"production constructs CandidateShapedValue (producer drift): {offenders}")

    def test_footprint_is_exactly_the_classified_negative_refusal_perimeter(self):
        bearing = {os.path.basename(rel) for rel, src_text, _t in _iter_service()
                   if _TOKEN in src_text}
        new = bearing - _FOOTPRINT_MODULES
        self.assertEqual(new, set(),
                         msg=f"NEW module references CandidateShapedValue (perimeter drift): {sorted(new)}")
        missing = _FOOTPRINT_MODULES - bearing
        self.assertEqual(missing, set(),
                         msg=f"classified perimeter module no longer references the sentinel: {sorted(missing)}")

    def test_no_app_endpoint_or_api_exposure(self):
        app_src = _src("app.py")
        self.assertNotIn(_TOKEN, app_src, "app.py references CandidateShapedValue (endpoint/API exposure)")
        self.assertNotIn("candidate_types", app_src, "app.py imports candidate_types (endpoint/API exposure)")


# --------------------------------------------------------------------------- #
# 5. Framing — lock does not claim completion / Tier-2 progress
# --------------------------------------------------------------------------- #

class TestScopeFraming(unittest.TestCase):

    def test_layer4_closure_still_frames_the_sentinel_as_inert_not_completion(self):
        doc = _read_doc("TORMENT_GATE_A_LAYER4_CONTAINMENT_BRICK_SERIES_CLOSURE_v0.1.md")
        self.assertIn("CandidateShapedValue", doc)
        self.assertIn("NOT Gate A wall completion", doc)

    def test_seam_survey_named_this_lock_as_the_only_safe_seam(self):
        doc = _read_doc("TORMENT_GATE_A_FORK3_FIRST_CODE_ADJACENT_SEAM_SURVEY_v0.1.md").lower()
        self.assertIn("anti-drift", doc)
        self.assertIn("candidateshapedvalue", doc)


if __name__ == "__main__":
    unittest.main()
