"""Direct tests for the PRODUCTION private generation owner module
(`torment_service/audit_private_generation_owner.py`, design shape A).

The owner is exercised here with a TEST-LOCAL fake generation boundary only. It
is unwired in production (called by tests only). These tests lock the required
guards behaviorally and by AST/source inspection of the production module:
  * captured prompt/messages never appear on the result, in metadata, logs, or
    storage;
  * the packet variable drives no branch; the response is final before the packet
    is composed;
  * missing selected text yields no packet and an unchanged response;
  * no `AssembledContext` reaches generation; only selected item dicts feed the
    observer;
  * the owner module has no service caller outside tests, and is not wired into
    `app.py` / `agent_loop.py`.

No authority wording is used.
"""

import ast
import os
import unittest
from dataclasses import fields as dataclass_fields

import torment_service.audit_private_generation_owner as owner_mod
from torment_service.audit_private_generation_owner import (
    PrivateGenerationOwner,
    PrivateGenerationOwnerResult,
)
from torment_service.audit_evidence_context import selected_admitted_items
from torment_service.retrieval_assembler import AssembledContext


_MEMORY_TOKEN = "QZX_OWNER_SELECTED_MEMORY_TOKEN"
_USER_INPUT = "a benign question with nothing notable"
_OWNER_MODULE = "audit_private_generation_owner.py"
_ALLOWED_IMPORT_LEAVES = {
    "__future__", "typing", "dataclasses",
    "audit_evidence_context", "audit_prompt_inclusion_observation",
}


# --------------------------------------------------------------------------- #
# Source / AST helpers
# --------------------------------------------------------------------------- #

def _repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


def _service_dir():
    return os.path.join(_repo_root(), "torment_service")


def _parse(path):
    with open(path, "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))


def _parse_service(filename):
    return _parse(os.path.join(_service_dir(), filename))


def _import_leaves_names(tree):
    leaves, names = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for x in n.names:
                leaves.add(x.name.split(".")[-1])
                names.add(x.name.split(".")[-1])
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                leaves.add(n.module.split(".")[-1])
            for x in n.names:
                names.add(x.name)
    return leaves, names


def _class(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and n.name == name:
            return n
    return None


def _method(cls, name):
    if cls is None:
        return None
    for n in cls.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def _called_names(node):
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                out.add(f.id)
            elif isinstance(f, ast.Attribute):
                out.add(f.attr)
    return out


def _owner_run_method():
    return _method(_class(_parse_service(_OWNER_MODULE), "PrivateGenerationOwner"),
                   "run")


def _iter_service_files():
    for dp, dns, fns in os.walk(_service_dir()):
        dns[:] = [d for d in dns
                  if d not in {".git", "__pycache__", ".mypy_cache",
                               ".pytest_cache", ".venv", "node_modules"}
                  and not d.startswith("do_not_touch")]
        for fn in fns:
            if fn.endswith(".py"):
                yield os.path.join(dp, fn)


# --------------------------------------------------------------------------- #
# Test-local fake generation boundary (NOT the real model / AgentRunner)
# --------------------------------------------------------------------------- #

class _FakeGenerationBoundary:
    def __init__(self, response="a final response"):
        self._response = response
        self.received = None

    def complete(self, *, system_prompt, messages):
        self.received = {"system_prompt": system_prompt, "messages": list(messages)}
        return self._response


class _BareRenderOwner(PrivateGenerationOwner):
    """Owner whose render omits the selected memory, so the inclusion check fails
    (exercises the missing-selected-text branch against the real owner)."""

    def _render_system_prompt(self, selected):
        return "You are an agent."


def _assembled(selected_text):
    ac = AssembledContext(profile="default", token_budget=1000)
    ac.blocks = {
        "relational_context": [
            {"block_type": "relational_context", "eid": 1, "chunk_id": None,
             "text": selected_text},
        ],
    }
    ac.selection_log = [
        {"action": "selected", "block_type": "relational_context",
         "eid": 1, "chunk_id": None},
    ]
    return ac


# --------------------------------------------------------------------------- #
# Behavioral characterization of the production owner
# --------------------------------------------------------------------------- #

class TestOwnerBehaviour(unittest.TestCase):

    def test_extracts_selected_items_from_same_context(self):
        ac = _assembled(_MEMORY_TOKEN)
        owner = PrivateGenerationOwner(ac, _FakeGenerationBoundary())
        owner.run(_USER_INPUT)
        expected = selected_admitted_items(ac)
        self.assertEqual(len(expected), 1)
        self.assertIs(expected[0], ac.blocks["relational_context"][0])

    def test_generation_receives_exactly_captured_prompt_messages(self):
        ac = _assembled(_MEMORY_TOKEN)
        gen = _FakeGenerationBoundary()
        owner = PrivateGenerationOwner(ac, gen)
        owner.run(_USER_INPUT)
        self.assertIsNotNone(gen.received)
        self.assertEqual(gen.received, owner._captured)
        self.assertIsInstance(gen.received["system_prompt"], str)
        self.assertNotIn("AssembledContext", repr(gen.received))

    def test_present_text_yields_packet_after_response(self):
        ac = _assembled(_MEMORY_TOKEN)
        owner = PrivateGenerationOwner(ac, _FakeGenerationBoundary("a final response"))
        result = owner.run(_USER_INPUT)
        self.assertIsInstance(result, PrivateGenerationOwnerResult)
        self.assertIsNotNone(result.audit_evidence_packet)
        self.assertEqual(result.audit_evidence_packet["response_text"],
                         "a final response")
        self.assertIn("evidence_items", result.audit_evidence_packet)

    def test_missing_text_yields_no_packet_and_unchanged_output(self):
        ac = _assembled(_MEMORY_TOKEN)
        res_missing = _BareRenderOwner(
            ac, _FakeGenerationBoundary("a final response")).run(_USER_INPUT)
        res_present = PrivateGenerationOwner(
            _assembled(_MEMORY_TOKEN),
            _FakeGenerationBoundary("a final response")).run(_USER_INPUT)
        self.assertIsNone(res_missing.audit_evidence_packet)
        self.assertIsNotNone(res_present.audit_evidence_packet)
        self.assertEqual(res_missing.response_text, res_present.response_text)

    def test_blank_response_yields_no_packet(self):
        ac = _assembled(_MEMORY_TOKEN)
        result = PrivateGenerationOwner(ac, _FakeGenerationBoundary("")).run(_USER_INPUT)
        self.assertEqual(result.response_text, "")
        self.assertIsNone(result.audit_evidence_packet)

    def test_only_selected_item_dicts_feed_the_observer(self):
        # Intercept the observer to prove the owner feeds it exactly the selected
        # item dicts — never the AssembledContext.
        ac = _assembled(_MEMORY_TOKEN)
        seen = {}
        original = owner_mod.observe_prompt_inclusion_packet

        def _spy(*, system_prompt, messages, admitted_context_items, response_text):
            seen["items"] = admitted_context_items
            return original(system_prompt=system_prompt, messages=messages,
                            admitted_context_items=admitted_context_items,
                            response_text=response_text)

        owner_mod.observe_prompt_inclusion_packet = _spy
        try:
            PrivateGenerationOwner(ac, _FakeGenerationBoundary()).run(_USER_INPUT)
        finally:
            owner_mod.observe_prompt_inclusion_packet = original
        self.assertIn("items", seen)
        self.assertEqual(seen["items"], selected_admitted_items(ac))
        self.assertNotIsInstance(seen["items"], AssembledContext)
        self.assertTrue(all(isinstance(x, dict) for x in seen["items"]))


# --------------------------------------------------------------------------- #
# Captured prompt/messages stay private; packet is not exposed
# --------------------------------------------------------------------------- #

class TestResultPrivacy(unittest.TestCase):

    def _result(self):
        ac = _assembled(_MEMORY_TOKEN)
        return PrivateGenerationOwner(ac, _FakeGenerationBoundary()).run(_USER_INPUT)

    def test_result_exposes_only_response_text_and_packet(self):
        names = {f.name for f in dataclass_fields(self._result())}
        self.assertEqual(names, {"response_text", "audit_evidence_packet"})
        for forbidden in ("system_prompt", "messages", "captured",
                          "_captured", "metadata", "prompt"):
            self.assertNotIn(forbidden, names)

    def test_packet_does_not_contain_raw_prompt_or_messages(self):
        pkt = self._result().audit_evidence_packet
        self.assertIsNotNone(pkt)
        self.assertEqual(set(pkt.keys()), {"response_text", "evidence_items"})


# --------------------------------------------------------------------------- #
# AST guards on the PRODUCTION module
# --------------------------------------------------------------------------- #

class TestProductionModuleShape(unittest.TestCase):

    def test_run_does_not_log_store_or_write(self):
        run = _owner_run_method()
        self.assertIsNotNone(run)
        called = _called_names(run)
        for forbidden in ("print", "open", "write", "log", "info", "debug",
                          "warning", "getLogger"):
            self.assertNotIn(forbidden, called,
                             msg=f"owner run() calls forbidden sink: {forbidden}")

    def test_capture_precedes_generation_precedes_compose(self):
        run = _owner_run_method()

        def first(pred):
            lns = [getattr(n, "lineno", None) for n in ast.walk(run)
                   if pred(n) and getattr(n, "lineno", None) is not None]
            return min(lns) if lns else None

        capture_ln = first(lambda n: isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Attribute) and t.attr == "_captured"
            for t in n.targets))
        generate_ln = first(
            lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "complete")
        compose_ln = first(
            lambda n: isinstance(n, ast.Call) and (
                (isinstance(n.func, ast.Name)
                 and n.func.id == "observe_prompt_inclusion_packet")
                or (isinstance(n.func, ast.Attribute)
                    and n.func.attr == "observe_prompt_inclusion_packet")))
        self.assertIsNotNone(capture_ln)
        self.assertIsNotNone(generate_ln)
        self.assertIsNotNone(compose_ln)
        self.assertLess(capture_ln, generate_ln)
        self.assertLess(generate_ln, compose_ln)

    def test_packet_variable_drives_no_branch(self):
        run = _owner_run_method()
        branch_uses = []
        for n in ast.walk(run):
            tests = []
            if isinstance(n, (ast.If, ast.While, ast.IfExp)):
                tests.append(n.test)
            for t in tests:
                for sub in ast.walk(t):
                    if isinstance(sub, ast.Name) and sub.id == "audit_packet":
                        branch_uses.append(getattr(n, "lineno", -1))
        self.assertEqual(branch_uses, [],
                         msg=f"packet used as a control branch at: {branch_uses}")

    def test_closed_import_surface(self):
        leaves, _ = _import_leaves_names(_parse_service(_OWNER_MODULE))
        extra = leaves - _ALLOWED_IMPORT_LEAVES
        self.assertEqual(extra, set(),
                         msg=f"owner imports outside the allowed surface: {sorted(extra)}")
        # Specifically not the runner / assembler / endpoint / writer / persistence.
        for forbidden in ("agent_loop", "retrieval_assembler", "app"):
            self.assertNotIn(forbidden, leaves)


# --------------------------------------------------------------------------- #
# Owner stays unwired (no service caller; not in app.py / agent_loop.py)
# --------------------------------------------------------------------------- #

class TestOwnerUnwired(unittest.TestCase):

    def test_owner_module_exists(self):
        self.assertTrue(
            os.path.exists(os.path.join(_service_dir(), _OWNER_MODULE)))

    def test_no_service_module_imports_the_owner(self):
        importers = []
        for ab in _iter_service_files():
            if os.path.basename(ab) == _OWNER_MODULE:
                continue
            try:
                leaves, names = _import_leaves_names(_parse(ab))
            except (SyntaxError, ValueError):
                continue
            if ("audit_private_generation_owner" in leaves
                    or "PrivateGenerationOwner" in names
                    or "PrivateGenerationOwnerResult" in names):
                importers.append(os.path.basename(ab))
        self.assertEqual(importers, [],
                         msg=f"owner module wired into: {importers}")

    def test_not_wired_into_app_or_agent_loop(self):
        for fname in ("app.py", "agent_loop.py"):
            leaves, names = _import_leaves_names(_parse_service(fname))
            self.assertNotIn("audit_private_generation_owner", leaves,
                             msg=f"{fname} imports the owner module")
            self.assertNotIn("PrivateGenerationOwner", names,
                             msg=f"{fname} imports the owner class")


if __name__ == "__main__":
    unittest.main()
