"""Tests-only / source-only characterization: MemoryPlan shaping is guidance,
not authority.

Locks the non-control posture of the live MemoryPlan-shaping lane — the geometric
coherence/stability shaping, the relational-prominence shaping, the two prior
cognition shaping rules, and the SRG relational blend into ``social_resonance`` —
against the doctrine:

    Memory may shape context. Memory may not seize authority.
    Audit observes authority. Audit must not become authority.

It changes no production code, adds no other test file, and writes no docs. It
mixes behavioral checks (calling the shaping helpers with the module flags
monkeypatched) with source/AST guards over the named surfaces.

Properties locked (per the slice spec):
  1. Default-off gates remain default-off where applicable (cognition shaping v2,
     cognition core shaping v1, geometric memory shaping, relational prominence,
     and the SRG source ``TORMENT_SRG_ENABLE``).
  2. Geometric coherence/stability shaping mutates only authorized MemoryPlan lane
     weights (``core`` / ``deep``) for already-enabled lanes.
  3. Relational prominence mutates only the relational lane weight and preserves
     the doctrine-bearing ceiling ``<= 0.99``.
  4. Geometric + relational shaping never alter ``top_k_by_lane`` (only the prior
     cognition rules do already-authorized ``top_k`` shaping: deep / core).
  5. The SRG relational input may blend into ``social_resonance``, but
     ``social_resonance`` is not consumed by MemoryPlan shaping or by retrieval
     routing. SCOPE CORRECTION: this does NOT claim ``social_resonance`` has no
     stance effect — ``stance_policy`` legitimately consumes it; the lock is only
     "not MemoryPlan weights/top_k, not retrieval routing".
  6. No shaping signal reaches output text / identity / archive / write / ingest /
     persistence / endpoint-schema-API / audit authority / audit-to-control.
  7. Ordinary numeric tuning is NOT frozen — only the doctrine-bearing caps,
     bounds, lane ownership, and default-off gates are locked (the tunable
     multiplier constants are deliberately not asserted).
"""

import ast
import contextlib
import os
import unittest
from types import SimpleNamespace

import torment_service.thinking_controller as tc
from torment_service.thinking_models import MemoryPlan


_RELATIONAL_CEILING = 0.99
_LANE_WEIGHT_BAND = (0.1, 2.0)

_SHAPING_FLAGS = (
    "_COGNITION_SHAPING_V2_ENABLE",
    "_COGNITION_CORE_SHAPING_V1_ENABLE",
    "_GEOMETRIC_MEMORY_SHAPING_V1_ENABLE",
    "_GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1_ENABLE",
)


# --------------------------------------------------------------------------- #
# Source / AST helpers
# --------------------------------------------------------------------------- #

def _service_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "torment_service")


def _src(filename):
    with open(os.path.join(_service_dir(), filename), "r", encoding="utf-8") as fh:
        return fh.read()


def _tree(filename):
    with open(os.path.join(_service_dir(), filename), "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))


def _method(tree, classname, methodname):
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and n.name == classname:
            for m in n.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == methodname:
                    return m
    return None


def _idents(node):
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
    return out


def _assigned_subscript_keys(func, attr):
    """Constant subscript keys ASSIGNED on ``<x>.<attr>[...]`` inside ``func``."""
    keys = set()
    for n in ast.walk(func):
        targets = []
        if isinstance(n, ast.Assign):
            targets = list(n.targets)
        elif isinstance(n, ast.AugAssign):
            targets = [n.target]
        for t in targets:
            if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Attribute) \
                    and t.value.attr == attr:
                sl = t.slice
                if isinstance(sl, ast.Index):          # py < 3.9
                    sl = sl.value
                if isinstance(sl, ast.Constant):
                    keys.add(sl.value)
    return keys


def _env_get_default(tree, var_name):
    """Default literal of ``os.environ.get("<var_name>", <default>)`` in tree."""
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "get" and len(n.args) >= 2
                and isinstance(n.args[0], ast.Constant) and n.args[0].value == var_name
                and isinstance(n.args[1], ast.Constant)):
            return n.args[1].value
    return None


# --------------------------------------------------------------------------- #
# Behavioral fixtures (call the real helpers with module flags monkeypatched)
# --------------------------------------------------------------------------- #

@contextlib.contextmanager
def _flags(**values):
    """Temporarily set thinking_controller module shaping flags."""
    saved = {k: getattr(tc, k) for k in values}
    try:
        for k, v in values.items():
            setattr(tc, k, v)
        yield
    finally:
        for k, v in saved.items():
            setattr(tc, k, v)


def _base_plan():
    p = MemoryPlan()
    p.retrieve_core = True
    p.retrieve_relational = True
    p.retrieve_archive = True
    p.retrieve_deep = True
    p.top_k_by_lane = {"core": 6, "relational": 4, "archive": 4, "deep": 3, "collective": 0}
    p.weight_by_lane = {"core": 1.0, "relational": 0.85, "archive": 0.45,
                        "deep": 0.60, "collective": 0.0}
    return p


def _state(**kw):
    base = dict(governance_sensitive=False, identity_sensitive=False,
                ambiguity_score=0.0, confidence_need=0.0)
    base.update(kw)
    return SimpleNamespace(**base)


def _geo(**kw):
    base = dict(coherence=1.0, stability=1.0, ambiguity_tolerance=1.0,
                social_resonance=0.5)
    base.update(kw)
    return SimpleNamespace(**base)


def _ctrl():
    return tc.ThinkingController()


# --------------------------------------------------------------------------- #
# 1. Default-off gates (source)
# --------------------------------------------------------------------------- #

class TestDefaultOffGates(unittest.TestCase):

    def test_shaping_flags_default_off(self):
        t = _tree("thinking_controller.py")
        for var in ("TORMENT_COGNITION_SHAPING_V2",
                    "TORMENT_COGNITION_CORE_SHAPING_V1",
                    "TORMENT_GEOMETRIC_MEMORY_SHAPING_V1",
                    "TORMENT_GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1"):
            self.assertEqual(_env_get_default(t, var), "0",
                             msg=f"{var} should default-off (\"0\")")

    def test_srg_source_default_off(self):
        # SRG source (the relational signal that may blend into social_resonance).
        self.assertEqual(_env_get_default(_tree("fabric.py"), "TORMENT_SRG_ENABLE"), "0")


# --------------------------------------------------------------------------- #
# 2-4 + 6 (behavioral): lane-ownership and bounds of the shaping helpers
# --------------------------------------------------------------------------- #

class TestShapingBehaviouralScope(unittest.TestCase):

    def test_geometric_memory_shapes_only_core_and_deep_weights(self):
        plan = _base_plan()
        top_k_before = dict(plan.top_k_by_lane)
        with _flags(_GEOMETRIC_MEMORY_SHAPING_V1_ENABLE=True):
            _ctrl()._apply_geometric_memory_shaping_v1(
                plan, _state(), _geo(coherence=1.0, stability=1.0))   # settled=1 -> mult 1.15
        self.assertAlmostEqual(plan.weight_by_lane["core"], 1.15, places=6)
        self.assertAlmostEqual(plan.weight_by_lane["deep"], 0.69, places=6)
        # other lanes untouched
        self.assertAlmostEqual(plan.weight_by_lane["relational"], 0.85, places=6)
        self.assertAlmostEqual(plan.weight_by_lane["archive"], 0.45, places=6)
        # top_k untouched (Property 4)
        self.assertEqual(plan.top_k_by_lane, top_k_before)

    def test_geometric_memory_weights_stay_in_band(self):
        # Even with extreme inputs the shaped weights stay within the lane band.
        for coh in (0.0, 0.5, 1.0):
            plan = _base_plan()
            with _flags(_GEOMETRIC_MEMORY_SHAPING_V1_ENABLE=True):
                _ctrl()._apply_geometric_memory_shaping_v1(
                    plan, _state(), _geo(coherence=coh, stability=coh))
            for lane in ("core", "deep"):
                self.assertGreaterEqual(plan.weight_by_lane[lane], _LANE_WEIGHT_BAND[0])
                self.assertLessEqual(plan.weight_by_lane[lane], _LANE_WEIGHT_BAND[1])

    def test_geometric_memory_skips_identity_and_governance(self):
        for kw in ({"identity_sensitive": True}, {"governance_sensitive": True}):
            plan = _base_plan()
            before = dict(plan.weight_by_lane)
            with _flags(_GEOMETRIC_MEMORY_SHAPING_V1_ENABLE=True):
                _ctrl()._apply_geometric_memory_shaping_v1(
                    plan, _state(**kw), _geo(coherence=1.0, stability=1.0))
            self.assertEqual(plan.weight_by_lane, before)

    def test_relational_prominence_shapes_only_relational_weight(self):
        plan = _base_plan()
        top_k_before = dict(plan.top_k_by_lane)
        with _flags(_GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1_ENABLE=True):
            _ctrl()._apply_geometric_relational_prominence_shaping_v1(
                plan, _state(), _geo(ambiguity_tolerance=1.0))     # mult 1.15 -> 0.9775
        self.assertAlmostEqual(plan.weight_by_lane["relational"], 0.9775, places=6)
        self.assertAlmostEqual(plan.weight_by_lane["core"], 1.0, places=6)
        self.assertAlmostEqual(plan.weight_by_lane["deep"], 0.60, places=6)
        self.assertAlmostEqual(plan.weight_by_lane["archive"], 0.45, places=6)
        self.assertEqual(plan.top_k_by_lane, top_k_before)

    def test_relational_prominence_never_exceeds_ceiling(self):
        for base_w in (0.90, 0.95, 0.99, 1.50):
            plan = _base_plan()
            plan.weight_by_lane["relational"] = base_w
            with _flags(_GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1_ENABLE=True):
                _ctrl()._apply_geometric_relational_prominence_shaping_v1(
                    plan, _state(), _geo(ambiguity_tolerance=1.0))
            self.assertLessEqual(plan.weight_by_lane["relational"],
                                 _RELATIONAL_CEILING + 1e-9,
                                 msg=f"relational exceeded ceiling from base {base_w}")

    def test_social_resonance_does_not_affect_memoryplan_shaping(self):
        # Two geometric contexts identical except social_resonance produce the
        # same shaped MemoryPlan — social_resonance is not a shaping input.
        def run(sr):
            plan = _base_plan()
            with _flags(_GEOMETRIC_MEMORY_SHAPING_V1_ENABLE=True,
                        _GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1_ENABLE=True):
                c = _ctrl()
                c._apply_geometric_memory_shaping_v1(
                    plan, _state(), _geo(coherence=0.7, stability=0.7, social_resonance=sr))
                c._apply_geometric_relational_prominence_shaping_v1(
                    plan, _state(), _geo(ambiguity_tolerance=0.7, social_resonance=sr))
            return dict(plan.weight_by_lane), dict(plan.top_k_by_lane)
        self.assertEqual(run(0.0), run(1.0))

    def test_all_shaping_helpers_are_noop_when_disabled(self):
        plan = _base_plan()
        before = (dict(plan.weight_by_lane), dict(plan.top_k_by_lane))
        with _flags(**{f: False for f in _SHAPING_FLAGS}):
            c = _ctrl()
            c._apply_cognition_shaping_v2(plan, _state(ambiguity_score=1.0))
            c._apply_cognition_core_shaping_v1(plan, _state(confidence_need=1.0))
            c._apply_geometric_memory_shaping_v1(plan, _state(), _geo())
            c._apply_geometric_relational_prominence_shaping_v1(plan, _state(), _geo())
        self.assertEqual((dict(plan.weight_by_lane), dict(plan.top_k_by_lane)), before)


# --------------------------------------------------------------------------- #
# 2-4 (source/AST): lane ownership locked at the source
# --------------------------------------------------------------------------- #

class TestShapingLaneOwnershipSource(unittest.TestCase):

    def setUp(self):
        self.t = _tree("thinking_controller.py")

    def _m(self, name):
        m = _method(self.t, "ThinkingController", name)
        self.assertIsNotNone(m, f"{name} not found")
        return m

    def test_geometric_memory_assigns_only_core_deep_weights_no_top_k(self):
        m = self._m("_apply_geometric_memory_shaping_v1")
        self.assertEqual(_assigned_subscript_keys(m, "weight_by_lane"), {"core", "deep"})
        self.assertEqual(_assigned_subscript_keys(m, "top_k_by_lane"), set())

    def test_relational_prominence_assigns_only_relational_weight_no_top_k(self):
        m = self._m("_apply_geometric_relational_prominence_shaping_v1")
        self.assertEqual(_assigned_subscript_keys(m, "weight_by_lane"), {"relational"})
        self.assertEqual(_assigned_subscript_keys(m, "top_k_by_lane"), set())

    def test_only_cognition_rules_shape_top_k_and_only_deep_core(self):
        v2 = self._m("_apply_cognition_shaping_v2")
        core = self._m("_apply_cognition_core_shaping_v1")
        self.assertEqual(_assigned_subscript_keys(v2, "top_k_by_lane"), {"deep"})
        self.assertEqual(_assigned_subscript_keys(v2, "weight_by_lane"), set())
        self.assertEqual(_assigned_subscript_keys(core, "top_k_by_lane"), {"core"})
        self.assertEqual(_assigned_subscript_keys(core, "weight_by_lane"), set())

    def test_relational_ceiling_literal_present(self):
        # The doctrine-bearing peripheral ceiling is locked (not the tunable mult).
        m = self._m("_apply_geometric_relational_prominence_shaping_v1")
        consts = {n.value for n in ast.walk(m) if isinstance(n, ast.Constant)
                  and isinstance(n.value, float)}
        self.assertIn(0.99, consts, "relational peripheral ceiling 0.99 missing")

    def test_shaping_helpers_do_no_io_or_writes(self):
        # Property 6: no output/write/ingest/persistence side effects in shaping.
        forbidden = {"open", "write", "ingest", "save", "persist", "promote_chunk",
                     "spawn_memory", "add_memory", "complete", "run_turn"}
        for name in ("_apply_cognition_shaping_v2", "_apply_cognition_core_shaping_v1",
                     "_apply_geometric_memory_shaping_v1",
                     "_apply_geometric_relational_prominence_shaping_v1"):
            called = {n.func.attr for n in ast.walk(self._m(name))
                      if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
            called |= {n.func.id for n in ast.walk(self._m(name))
                       if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
            self.assertEqual(called & forbidden, set(),
                             msg=f"{name} performs a forbidden side-effect call")


# --------------------------------------------------------------------------- #
# 5 + 6 (source): social_resonance / SRG consumption boundaries
# --------------------------------------------------------------------------- #

class TestSocialResonanceConsumptionBoundary(unittest.TestCase):

    def test_memoryplan_shaping_does_not_read_social_resonance(self):
        t = _tree("thinking_controller.py")
        for name in ("build_memory_plan", "_apply_cognition_shaping_v2",
                     "_apply_cognition_core_shaping_v1",
                     "_apply_geometric_memory_shaping_v1",
                     "_apply_geometric_relational_prominence_shaping_v1"):
            m = _method(t, "ThinkingController", name)
            self.assertIsNotNone(m)
            self.assertNotIn("social_resonance", _idents(m),
                             msg=f"{name} reads social_resonance (must not)")

    def test_retrieval_routing_does_not_consume_social_resonance(self):
        # fabric retrieval consumes MemoryPlan via top_k_by_lane / weight_by_lane;
        # social_resonance appears nowhere in fabric.
        fabric = _src("fabric.py")
        self.assertNotIn("social_resonance", fabric)
        self.assertIn("top_k_by_lane", fabric)
        self.assertIn("weight_by_lane", fabric)

    def test_spine_advisory_query_carries_only_lane_top_k_and_weights(self):
        spine = _src("spine.py")
        self.assertIn("top_k_by_lane", spine)
        self.assertIn("weight_by_lane", spine)
        self.assertNotIn("social_resonance", spine)

    def test_scope_correction_stance_policy_does_consume_social_resonance(self):
        # SCOPE CORRECTION: social_resonance legitimately has a stance consumer, so
        # the lock is "not MemoryPlan/retrieval", never "no stance effect".
        self.assertIn("social_resonance", _src("stance_policy.py"))

    def test_srg_relational_blends_into_social_resonance_in_harvester(self):
        # The SRG relational input informs social_resonance (a stance dimension) —
        # not a MemoryPlan weight. Presence-only (tunable blend not frozen).
        harvester = _src("geometric_harvester.py")
        self.assertIn("social_resonance", harvester)
        self.assertIn("srg_relational", harvester)


# --------------------------------------------------------------------------- #
# 6 (source): advisory-only MemoryPlan surfaces (no control/output/schema)
# --------------------------------------------------------------------------- #

class TestAdvisoryMemoryPlanSurfaces(unittest.TestCase):

    def test_app_exposes_memoryplan_as_advisory_lane_dict_only(self):
        # /agent/query exports the MemoryPlan as a lane top_k/weight dict only.
        app = _src("app.py")
        self.assertIn("top_k_by_lane", app)
        self.assertIn("weight_by_lane", app)

    def test_fabric_consumes_memory_plan_via_lane_keys_only(self):
        t = _tree("fabric.py")
        # Somewhere fabric reads _mp.get("top_k_by_lane") / get("weight_by_lane").
        getters = {n.args[0].value for n in ast.walk(t)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == "get" and n.args
                   and isinstance(n.args[0], ast.Constant)
                   and isinstance(n.args[0].value, str)}
        self.assertIn("top_k_by_lane", getters)
        self.assertIn("weight_by_lane", getters)


if __name__ == "__main__":
    unittest.main()
