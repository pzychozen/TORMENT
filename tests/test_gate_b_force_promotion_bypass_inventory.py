"""Gate B / H3 force-promotion bypass inventory — tests-only, source/AST, NON-AUTHORIZING.

WHAT THIS GUARDS
----------------
``/promote`` (``torment_service/app.py``) accepts ``PromoteReq.force``, threads it into
``evaluate_promotion(is_canon=..., user_approved=...)``, and then promotes on
``if result.promote or req.force`` — i.e. a caller can SKIP THE EVALUATOR. This is the
**parked H3 / Gate B writer-authority non-conformance**: recorded as classified-not-solved by the
Gate A wall inventory ("/promote force-bypass surface (parked non-conformance)").

WHAT THIS TEST DOES **NOT** DO
------------------------------
It does **not** fix the bypass. It does **not** resolve Gate B writer authority. It changes no
production code, authorizes no writer-authority mechanism, no carrier/substrate, and no endpoint
behaviour. The bypass remains exactly as parked.

WHAT IT DOES
------------
It prevents the parked bypass from **silently growing**, by pinning today's shape:
  * no NEW production caller of ``promote_chunk`` / ``evaluate_promotion`` -- INCLUDING VIA ALIAS
    (``from .promotion import promote_chunk as pc; pc(...)``) or rebinding (``pc = promote_chunk``);
  * no NEW owner of a ``force`` field, anywhere under ``torment_service/`` (only ``PromoteReq``);
  * no HARD-CODED SELF-APPROVAL (a truthy literal passed to ``is_canon`` / ``user_approved``);
  * no OPAQUE ``**kwargs`` at either promotion call site (a dict could hide ``user_approved=True``);
  * no UNRECORDED forced promotion: the force-provenance keys must be present AND must still DERIVE
    FROM the real values (``req.force`` / ``result.promote``) -- a constant or swapped value would
    keep the label while hollowing out the record.

Source + ``ast`` only: no service import, no execution, no network, no data.

FAIL-CLOSED NOTES
-----------------
* ALIASES: target detection resolves, per module, every local name bound to the target function --
  ``from .promotion import promote_chunk as pc``, ``pc = promote_chunk``, and transitive rebindings --
  to a fixpoint, plus attribute calls (``promotion.promote_chunk(...)``). A module that merely BINDS
  an alias without calling it is also reported: holding a reference to the writer is enough to grow
  the bypass later.
* PATHS: modules are reported by SERVICE-RELATIVE PATH (e.g. ``migration/app.py``), never by bare
  basename, so a future ``torment_service/<subdir>/app.py`` cannot collapse into the allowed
  top-level ``app.py`` entry.
* ``user_approved=False`` (self-approval test): a *falsy* literal is the CLOSED direction -- it can
  only withhold approval, never grant it. Only TRUTHY literals are rejected, because the hazard is
  self-approval, not self-denial. ``promotion.py`` legitimately passes ``user_approved=False`` today.
"""
from __future__ import annotations

import ast
import os
import unittest


_SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "node_modules"}

_TARGETS = ("promote_chunk", "evaluate_promotion")

# Service-relative paths (NOT basenames): today's single writer call site and the evaluator's two.
_PROMOTE_CHUNK_CALLERS = {"app.py"}
_EVALUATE_PROMOTION_CALLERS = {"app.py", "promotion.py"}

# Modules allowed to BIND (import/alias/rebind) the targets at all: the definition site plus the
# known callers. Binding without calling is still a growth surface.
_PROMOTE_CHUNK_BINDERS = {"promotion.py", "app.py"}
_EVALUATE_PROMOTION_BINDERS = {"promotion.py", "app.py"}

# Only this class, in this module, may declare a force field.
_FORCE_FIELD_OWNERS = {"app.py::PromoteReq"}

# The force route must stay recorded on the promoted node -- key AND value provenance.
#   provenance key -> (source object, source attribute)
_FORCE_PROVENANCE = {
    "promotion_force_requested": ("req", "force"),
    "promotion_evaluator_promote": ("result", "promote"),
}

# Approval-bearing keywords of evaluate_promotion(...).
_APPROVAL_KWARGS = ("is_canon", "user_approved")


# --------------------------------------------------------------------------- #
# Source / AST helpers
# --------------------------------------------------------------------------- #

def _service_dir():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "torment_service")


def _parse(path):
    with open(path, "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))


def _iter_service_modules():
    """Yield (service_relative_path, tree) for every production module under torment_service/.

    Paths -- not basenames -- so a future ``torment_service/<subdir>/app.py`` cannot collapse into
    the allowed top-level ``app.py`` inventory entry.
    """
    base = _service_dir()
    for dp, dns, fns in os.walk(base):
        dns[:] = [d for d in dns
                  if d not in _SKIP_DIRS and not d.startswith("do_not_touch")]
        for fn in sorted(fns):
            if not fn.endswith(".py"):
                continue
            ab = os.path.join(dp, fn)
            rel = os.path.relpath(ab, base).replace("\\", "/")
            try:
                yield rel, _parse(ab)
            except (SyntaxError, ValueError):
                continue


def _local_aliases(tree, target):
    """Every local NAME in ``tree`` bound to ``target`` (fixpoint over aliases).

    Covers ``def target``, ``from .promotion import target``, ``... import target as pc``, and
    ``pc = target`` / ``pc2 = pc`` rebindings, transitively.
    """
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == target:
            names.add(target)
        elif isinstance(n, ast.ImportFrom):
            for a in n.names:
                if a.name == target:
                    names.add(a.asname or a.name)
    changed = True
    while changed:
        changed = False
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Name) \
                    and n.value.id in names:
                for t in n.targets:
                    if isinstance(t, ast.Name) and t.id not in names:
                        names.add(t.id)
                        changed = True
    return names


def _calls_to(tree, target):
    """Every ast.Call whose callee resolves to ``target`` -- alias-aware."""
    aliases = _local_aliases(tree, target) | {target}
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if isinstance(f, ast.Name) and f.id in aliases:
            out.append(n)
        elif isinstance(f, ast.Attribute) and f.attr == target:
            out.append(n)
    return out


def _service_callers_of(target):
    return {rel for rel, tree in _iter_service_modules() if _calls_to(tree, target)}


def _service_binders_of(target):
    """Modules that import / alias / rebind ``target`` at all, whether or not they call it."""
    binders = set()
    for rel, tree in _iter_service_modules():
        if _local_aliases(tree, target):
            binders.add(rel)
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute) and n.attr == target:
                binders.add(rel)
                break
    return binders


def _app_tree():
    return _parse(os.path.join(_service_dir(), "app.py"))


def _declared_field_names(class_node):
    names = set()
    for stmt in class_node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            names.add(stmt.target.id)
        elif isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return names


def _force_field_owners():
    """``path/to/file.py::ClassName`` for EVERY production class declaring a ``force`` field."""
    owners = set()
    for rel, tree in _iter_service_modules():
        for n in ast.walk(tree):
            if isinstance(n, ast.ClassDef) and "force" in _declared_field_names(n):
                owners.add(f"{rel}::{n.name}")
    return owners


def _is_source_attribute(node, obj, attr):
    """True iff ``node`` IS exactly ``obj.attr`` (e.g. ``req.force``) -- not merely contains it."""
    return (isinstance(node, ast.Attribute) and node.attr == attr
            and isinstance(node.value, ast.Name) and node.value.id == obj)


def _derives_from(node, obj, attr):
    """STRICT: ``node`` must be ``obj.attr`` or ``bool(obj.attr)`` -- and nothing else.

    A containment check ("mentions req.force somewhere") is NOT enough: ``not req.force``,
    ``req.force and False``, ``result.promote or True``, and ``req.force == 0`` all mention the
    source while destroying the record. Unary ops, boolean ops, comparisons, constants, ternaries,
    f-strings, and every other expression shape are REJECTED.
    """
    if _is_source_attribute(node, obj, attr):
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "bool" \
            and len(node.args) == 1 and not node.keywords \
            and _is_source_attribute(node.args[0], obj, attr):
        return True
    return False


def _truthy_constant(node):
    """True iff ``node`` is a literal constant whose truth value is True."""
    return isinstance(node, ast.Constant) and bool(node.value) is True


def _has_opaque_kwargs(call_node):
    return any(k.arg is None for k in call_node.keywords)


# --------------------------------------------------------------------------- #
# 1-2. Caller inventories (no new callers -- and no new binders -- of the bypass surfaces)
# --------------------------------------------------------------------------- #

class TestPromotionCallerInventory(unittest.TestCase):

    def test_promote_chunk_caller_inventory_is_exact(self):
        callers = _service_callers_of("promote_chunk")
        self.assertEqual(
            callers, _PROMOTE_CHUNK_CALLERS,
            "the promotion WRITER must keep exactly one production caller (the /promote endpoint "
            f"in app.py), aliases and subpackages included: {callers}")
        binders = _service_binders_of("promote_chunk")
        self.assertEqual(
            binders, _PROMOTE_CHUNK_BINDERS,
            "no production module may even BIND / alias promote_chunk beyond the definition site "
            f"and the known caller: {binders}")

    def test_evaluate_promotion_caller_inventory_is_exact(self):
        callers = _service_callers_of("evaluate_promotion")
        self.assertEqual(
            callers, _EVALUATE_PROMOTION_CALLERS,
            "the promotion EVALUATOR must keep exactly its two production callers (app.py /promote; "
            f"promotion.py suggest_promotions), aliases and subpackages included: {callers}")
        binders = _service_binders_of("evaluate_promotion")
        self.assertEqual(
            binders, _EVALUATE_PROMOTION_BINDERS,
            f"no production module may even BIND / alias evaluate_promotion beyond these: {binders}")


# --------------------------------------------------------------------------- #
# 3. Force-field ownership (service-wide, all classes, path-qualified)
# --------------------------------------------------------------------------- #

class TestForceFieldOwnership(unittest.TestCase):

    def test_force_field_is_owned_only_by_promote_req(self):
        owners = _force_field_owners()
        self.assertEqual(
            owners, _FORCE_FIELD_OWNERS,
            "only app.py::PromoteReq may declare a `force` field anywhere under torment_service/; "
            f"a second force-bearing class would open a new evaluator-bypass surface: {owners}")


# --------------------------------------------------------------------------- #
# 4. No hard-coded self-approval
# --------------------------------------------------------------------------- #

class TestNoHardcodedSelfApproval(unittest.TestCase):

    def test_no_hardcoded_self_approval_at_evaluate_promotion(self):
        offenders = []
        for rel, tree in _iter_service_modules():
            for call in _calls_to(tree, "evaluate_promotion"):
                for kw in call.keywords:
                    if kw.arg in _APPROVAL_KWARGS and _truthy_constant(kw.value):
                        offenders.append(
                            f"{rel}:{getattr(call, 'lineno', '?')} {kw.arg}=<truthy literal>")
        self.assertEqual(
            offenders, [],
            "no evaluate_promotion(...) call may hard-code approval: is_canon / user_approved must "
            "derive from a request or document value, never from a literal True (falsy literals are "
            f"the closed direction and are permitted): {offenders}")


# --------------------------------------------------------------------------- #
# 5. The force route stays recorded -- KEYS **AND** VALUE PROVENANCE
# --------------------------------------------------------------------------- #

class TestForceRouteStaysRecorded(unittest.TestCase):

    def test_force_route_stays_recorded_on_promotion(self):
        calls = _calls_to(_app_tree(), "promote_chunk")
        self.assertEqual(len(calls), 1, "app.py must hold exactly one promote_chunk call site")
        payloads = [kw.value for kw in calls[0].keywords if kw.arg == "extra_payload"]
        self.assertEqual(len(payloads), 1,
                         "the promote_chunk call must pass extra_payload (force provenance)")
        payload = payloads[0]
        self.assertIsInstance(payload, ast.Dict,
                              "extra_payload must be a literal dict so its provenance keys and "
                              "values are statically checkable")
        entries = {k.value: v for k, v in zip(payload.keys, payload.values)
                   if isinstance(k, ast.Constant) and isinstance(k.value, str)}

        for key, (obj, attr) in _FORCE_PROVENANCE.items():
            self.assertIn(
                key, entries,
                f"extra_payload must still record `{key}`: a FORCED promotion must remain "
                "distinguishable from an EVALUATED one, or the parked bypass becomes invisible")
            self.assertTrue(
                _derives_from(entries[key], obj, attr),
                f"`{key}` must be EXACTLY `{obj}.{attr}` or `bool({obj}.{attr})`; a constant, a "
                f"swapped value, or any transformed shape (`not {obj}.{attr}`, "
                f"`{obj}.{attr} and False`, `... or True`, a comparison) would keep the label while "
                "hollowing out the record -- the forced route would look evaluated")


# --------------------------------------------------------------------------- #
# 6. No opaque **kwargs at the promotion call sites
# --------------------------------------------------------------------------- #

class TestNoOpaqueKwargsAtPromotionCallSites(unittest.TestCase):

    def test_no_opaque_kwargs_at_promotion_call_sites(self):
        offenders = []
        for rel, tree in _iter_service_modules():
            for target in _TARGETS:
                for call in _calls_to(tree, target):
                    if _has_opaque_kwargs(call):
                        offenders.append(f"{rel}:{getattr(call, 'lineno', '?')} {target}(**kwargs)")
        self.assertEqual(
            offenders, [],
            "no promote_chunk / evaluate_promotion call may use **kwargs expansion: an opaque dict "
            f"could hide user_approved=True or a missing force provenance key: {offenders}")


if __name__ == "__main__":
    unittest.main()
