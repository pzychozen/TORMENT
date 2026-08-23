"""Tests-only / source-only characterization of the PRIVATE GENERATION OWNER
shape (design: `docs/TORMENT_AUDIT_PRIVATE_GENERATION_OWNER_PATH_DESIGN_v0.1.md`,
commit `4bbfdcd`; Codex result on the owner-shape gate: PASS, A only).

This file implements NO production owner. It demonstrates the design shape with a
TEST-LOCAL fake generation boundary and a TEST-LOCAL owner harness that drive the
EXISTING pure helpers (`selected_admitted_items`, `observe_prompt_inclusion_packet`).
It creates no `torment_service/audit_private_generation_owner.py`, no endpoint /
`app.py` / `agent_loop.py` wiring, no public schema/API, no persistence, no memory
write, no writer path, no retrieval feedback, no ranking/suppression/retry/style
steering, no review/output/ingest/fabric feedback, no database/substrate, no
durable private cognition, and no prompt-request exposure.

It characterizes (and locks via behavioral + AST-self + source-guard tests):
  * the harness holds one explicit `AssembledContext` in its own frame;
  * it extracts selected item dicts from that SAME object;
  * it renders and captures the exact prompt/messages BEFORE generation;
  * generation receives EXACTLY the captured prompt/messages;
  * selected item text is checked against the captured prompt/messages;
  * missing selected text yields no packet and does not alter output;
  * the packet is composed only AFTER a final response text exists;
  * packet presence/absence drives no branch;
  * the captured prompt/messages are never returned, stored, logged, exposed, or
    placed in metadata;
  * the forbidden production surfaces remain absent / deferred (no owner module,
    no endpoint/app/runner wiring, no public schema/API, no `AgentRunner`
    retrieval/assembly/extraction ownership, and B remains deferred).

No authority wording is used.
"""

import ast
import os
import unittest
from dataclasses import dataclass, fields as dataclass_fields
from typing import Any, Dict, Optional

from torment_service.audit_evidence_context import selected_admitted_items
from torment_service.audit_prompt_inclusion_observation import (
    observe_prompt_inclusion_packet,
)
from torment_service.retrieval_assembler import AssembledContext


_OWNER_MODULE = "audit_private_generation_owner.py"   # NAME ONLY; must NOT exist
_MEMORY_TOKEN = "QZX_OWNER_SELECTED_MEMORY_TOKEN"
_USER_INPUT = "a benign question with nothing notable"


# --------------------------------------------------------------------------- #
# Source / AST helpers (no service import; mirrors sibling files' conventions)
# --------------------------------------------------------------------------- #

def _repo_root():
    here = os.path.dirname(os.path.abspath(__file__))   # tests/
    return os.path.dirname(here)                          # torment_fabric/


def _service_dir():
    return os.path.join(_repo_root(), "torment_service")


def _parse(path):
    with open(path, "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))


def _parse_service(filename):
    return _parse(os.path.join(_service_dir(), filename))


def _this_file_tree():
    return _parse(os.path.abspath(__file__))


def _idents(*nodes):
    out = set()
    for node in nodes:
        if node is None:
            continue
        for n in ast.walk(node):
            if isinstance(n, ast.Name):
                out.add(n.id)
            elif isinstance(n, ast.Attribute):
                out.add(n.attr)
            elif isinstance(n, ast.keyword) and n.arg:
                out.add(n.arg)
    return out


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
    """Records exactly the prompt/messages it is called with, returns a canned
    final response. Stands in for the model-completion boundary the owner owns."""

    def __init__(self, response="a final response"):
        self._response = response
        self.received = None   # {"system_prompt": ..., "messages": [...]}

    def complete(self, *, system_prompt, messages):
        self.received = {"system_prompt": system_prompt, "messages": list(messages)}
        return self._response


# --------------------------------------------------------------------------- #
# Test-local owner harness (NOT a production module)
# --------------------------------------------------------------------------- #

@dataclass
class _OwnerResult:
    """The owner's output. Exactly two fields — never the captured prompt/messages,
    never metadata."""
    response_text: str
    audit_evidence_packet: Optional[Dict[str, Any]]


class _PrivateGenerationOwnerHarness:
    """Test-local owner harness mirroring the design shape. Holds ONE explicit
    AssembledContext in its own frame, extracts selected item dicts from that same
    object, renders + captures the exact prompt/messages it sends to generation,
    checks selected item-text inclusion against the captured prompt, and composes
    an observation-only packet only after a final response exists. The captured
    prompt/messages stay local (`self._captured`) and are never returned, stored,
    logged, exposed, or placed in metadata."""

    def __init__(self, assembled_context, generation_boundary, *, include_memory):
        self._assembled = assembled_context        # one explicit context, in-frame
        self._gen = generation_boundary
        self._include_memory = include_memory
        self._captured = None                      # private; never exposed

    def run(self, user_input):
        # Extract selected item dicts from the SAME assembled context.
        selected = selected_admitted_items(self._assembled)
        # Render + capture the EXACT prompt/messages before generation.
        system_prompt = self._render_system_prompt(selected)
        messages = [{"role": "user", "content": user_input}]
        self._captured = {"system_prompt": system_prompt, "messages": messages}
        # Send EXACTLY the captured prompt/messages to generation.
        response_text = self._gen.complete(
            system_prompt=self._captured["system_prompt"],
            messages=self._captured["messages"],
        )
        # Compose the observation-only packet ONLY after a final response exists,
        # and ONLY when selected item text is present in the captured prompt.
        audit_packet = None
        if response_text:
            audit_packet = observe_prompt_inclusion_packet(
                system_prompt=self._captured["system_prompt"],
                messages=self._captured["messages"],
                admitted_context_items=selected,
                response_text=response_text,
            )
        # Return ONLY the response text + observation packet. Never the captured
        # prompt/messages; no metadata.
        return _OwnerResult(response_text=response_text,
                            audit_evidence_packet=audit_packet)

    def _render_system_prompt(self, selected):
        lines = ["You are an agent."]
        if self._include_memory:
            for item in selected:
                text = item.get("text")
                if isinstance(text, str) and text:
                    lines.append(text)
        return "\n".join(lines)


def _assembled(selected_text):
    """One explicit AssembledContext with a single SELECTED relational block."""
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
# Behavioral characterization
# --------------------------------------------------------------------------- #

class TestOwnerHarnessShape(unittest.TestCase):

    def test_extracts_selected_items_from_the_same_assembled_context(self):
        ac = _assembled(_MEMORY_TOKEN)
        gen = _FakeGenerationBoundary()
        owner = _PrivateGenerationOwnerHarness(ac, gen, include_memory=True)
        owner.run(_USER_INPUT)
        # The owner's extraction is exactly the pure extractor's output for THIS
        # object — same dict objects, sourced from the held context.
        expected = selected_admitted_items(ac)
        self.assertEqual(len(expected), 1)
        self.assertIs(expected[0], ac.blocks["relational_context"][0])

    def test_generation_receives_exactly_the_captured_prompt_messages(self):
        ac = _assembled(_MEMORY_TOKEN)
        gen = _FakeGenerationBoundary()
        owner = _PrivateGenerationOwnerHarness(ac, gen, include_memory=True)
        owner.run(_USER_INPUT)
        # What generation received is exactly what the owner captured.
        self.assertIsNotNone(gen.received)
        self.assertEqual(gen.received, owner._captured)
        # The owner passed strings/message-dicts, never the AssembledContext.
        self.assertIsInstance(gen.received["system_prompt"], str)
        self.assertNotIsInstance(gen.received["system_prompt"], AssembledContext)
        for m in gen.received["messages"]:
            self.assertIsInstance(m, dict)
            self.assertNotIsInstance(m, AssembledContext)

    def test_present_selected_text_yields_packet_after_response(self):
        ac = _assembled(_MEMORY_TOKEN)
        gen = _FakeGenerationBoundary(response="a final response")
        owner = _PrivateGenerationOwnerHarness(ac, gen, include_memory=True)
        result = owner.run(_USER_INPUT)
        # Inclusion holds -> observation packet exists and references the response.
        self.assertIsNotNone(result.audit_evidence_packet)
        self.assertEqual(result.audit_evidence_packet["response_text"],
                         "a final response")
        self.assertIn("evidence_items", result.audit_evidence_packet)

    def test_missing_selected_text_yields_no_packet_and_unchanged_output(self):
        ac = _assembled(_MEMORY_TOKEN)
        # include_memory=False -> the selected text is NOT in the captured prompt.
        gen_missing = _FakeGenerationBoundary(response="a final response")
        owner_missing = _PrivateGenerationOwnerHarness(ac, gen_missing,
                                                       include_memory=False)
        res_missing = owner_missing.run(_USER_INPUT)

        gen_present = _FakeGenerationBoundary(response="a final response")
        owner_present = _PrivateGenerationOwnerHarness(_assembled(_MEMORY_TOKEN),
                                                       gen_present,
                                                       include_memory=True)
        res_present = owner_present.run(_USER_INPUT)

        # Missing selected text -> no packet.
        self.assertIsNone(res_missing.audit_evidence_packet)
        # ...while the present run does produce one (the only difference).
        self.assertIsNotNone(res_present.audit_evidence_packet)
        # Output (response text) is identical regardless of packet presence.
        self.assertEqual(res_missing.response_text, res_present.response_text)

    def test_blank_response_yields_no_packet(self):
        ac = _assembled(_MEMORY_TOKEN)
        gen = _FakeGenerationBoundary(response="")
        owner = _PrivateGenerationOwnerHarness(ac, gen, include_memory=True)
        result = owner.run(_USER_INPUT)
        # No final response text -> no packet (packet only after a final response).
        self.assertEqual(result.response_text, "")
        self.assertIsNone(result.audit_evidence_packet)

    def test_owner_never_hands_assembled_context_to_generation(self):
        ac = _assembled(_MEMORY_TOKEN)
        gen = _FakeGenerationBoundary()
        owner = _PrivateGenerationOwnerHarness(ac, gen, include_memory=True)
        owner.run(_USER_INPUT)
        blob = repr(gen.received)
        # The AssembledContext object never reaches the generation boundary.
        self.assertNotIn("AssembledContext", blob)


# --------------------------------------------------------------------------- #
# Captured prompt/messages stay private (not returned / stored / logged / exposed)
# --------------------------------------------------------------------------- #

class TestCapturedPromptStaysPrivate(unittest.TestCase):

    def _run(self):
        ac = _assembled(_MEMORY_TOKEN)
        owner = _PrivateGenerationOwnerHarness(ac, _FakeGenerationBoundary(),
                                               include_memory=True)
        return owner.run(_USER_INPUT)

    def test_result_exposes_only_response_text_and_packet(self):
        result = self._run()
        names = {f.name for f in dataclass_fields(result)}
        self.assertEqual(names, {"response_text", "audit_evidence_packet"})
        # No captured prompt / messages / metadata fields anywhere on the result.
        for forbidden in ("system_prompt", "messages", "captured",
                          "_captured", "metadata", "prompt"):
            self.assertNotIn(forbidden, names)

    def test_packet_does_not_contain_raw_prompt_or_messages(self):
        result = self._run()
        pkt = result.audit_evidence_packet
        self.assertIsNotNone(pkt)
        # The observation packet carries only bounded evidence + response text —
        # not the system prompt scaffolding or the messages list.
        self.assertNotIn("system_prompt", pkt)
        self.assertNotIn("messages", pkt)
        self.assertEqual(set(pkt.keys()), {"response_text", "evidence_items"})

    def test_harness_run_does_not_log_store_or_write(self):
        # AST self-check: the owner's run() makes no print / logging / open / write
        # call (nothing logs or stores the captured prompt/messages).
        run = _method(_class(_this_file_tree(), "_PrivateGenerationOwnerHarness"),
                      "run")
        self.assertIsNotNone(run)
        called = _called_names(run)
        for forbidden in ("print", "open", "write", "log", "info", "debug",
                          "warning", "getLogger"):
            self.assertNotIn(forbidden, called,
                             msg=f"owner run() calls forbidden sink: {forbidden}")


# --------------------------------------------------------------------------- #
# Call order + packet drives no branch (AST self-inspection of the harness)
# --------------------------------------------------------------------------- #

class TestComposeOrderAndNoBranch(unittest.TestCase):

    def setUp(self):
        self.run = _method(
            _class(_this_file_tree(), "_PrivateGenerationOwnerHarness"), "run")
        self.assertIsNotNone(self.run)

    def _first_lineno(self, predicate):
        linenos = [getattr(n, "lineno", None) for n in ast.walk(self.run)
                   if predicate(n) and getattr(n, "lineno", None) is not None]
        return min(linenos) if linenos else None

    def test_capture_precedes_generation_precedes_compose(self):
        capture_ln = self._first_lineno(
            lambda n: isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Attribute) and t.attr == "_captured"
                for t in n.targets))
        generate_ln = self._first_lineno(
            lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "complete")
        compose_ln = self._first_lineno(
            lambda n: isinstance(n, ast.Call) and (
                (isinstance(n.func, ast.Name)
                 and n.func.id == "observe_prompt_inclusion_packet")
                or (isinstance(n.func, ast.Attribute)
                    and n.func.attr == "observe_prompt_inclusion_packet")))
        self.assertIsNotNone(capture_ln)
        self.assertIsNotNone(generate_ln)
        self.assertIsNotNone(compose_ln)
        self.assertLess(capture_ln, generate_ln,
                        "capture must precede generation")
        self.assertLess(generate_ln, compose_ln,
                        "generation (final response) must precede packet compose")

    def test_packet_variable_drives_no_branch(self):
        branch_uses = []
        for n in ast.walk(self.run):
            tests = []
            if isinstance(n, (ast.If, ast.While, ast.IfExp)):
                tests.append(n.test)
            for t in tests:
                for sub in ast.walk(t):
                    if isinstance(sub, ast.Name) and sub.id == "audit_packet":
                        branch_uses.append(getattr(n, "lineno", -1))
        self.assertEqual(branch_uses, [],
                         msg=f"packet used as a control branch at: {branch_uses}")


# --------------------------------------------------------------------------- #
# Source guards — forbidden production surfaces remain absent / deferred
# --------------------------------------------------------------------------- #

class TestForbiddenSurfacesAbsent(unittest.TestCase):

    def test_owner_module_exists_but_is_unwired(self):
        # Shape A landed: the module now EXISTS. It must remain unwired — no
        # service module references it (asserted by
        # test_no_service_module_references_the_owner_module below).
        self.assertTrue(
            os.path.exists(os.path.join(_service_dir(), _OWNER_MODULE)),
            msg="audit_private_generation_owner.py should exist after the owner slice")

    def test_no_service_module_references_the_owner_module(self):
        offenders = []
        for ab in _iter_service_files():
            try:
                leaves, names = _import_leaves_names(_parse(ab))
            except (SyntaxError, ValueError):
                continue
            if ("audit_private_generation_owner" in leaves
                    or "audit_private_generation_owner" in names):
                offenders.append(os.path.basename(ab))
        self.assertEqual(offenders, [],
                         msg=f"owner module referenced by: {offenders}")

    def test_app_has_no_runner_wiring(self):
        app = _parse_service("app.py")
        leaves, names = _import_leaves_names(app)
        self.assertNotIn("agent_loop", leaves)
        self.assertNotIn("AgentRunner", names)
        ids = _idents(app)
        self.assertNotIn("AgentRunner", ids)
        self.assertNotIn("run_turn", ids)
        self.assertNotIn("audit_private_generation_owner", ids)

    def test_agent_runner_ownership_not_expanded(self):
        al = _parse_service("agent_loop.py")
        leaves, names = _import_leaves_names(al)
        self.assertNotIn("retrieval_assembler", leaves)
        self.assertNotIn("audit_evidence_context", leaves)
        self.assertNotIn("AssembledContext", names)
        called = _called_names(al)
        self.assertNotIn("assemble_context", called)
        self.assertNotIn("selected_admitted_items", called)
        self.assertNotIn("AssembledContext", _idents(al))

    def test_bridge_remains_dead_end_and_b_deferred(self):
        # B (a private runner delegation seam) stays deferred: the selected-items
        # runner bridge is still called by no production service module.
        callers = []
        for ab in _iter_service_files():
            base = os.path.basename(ab)
            if base == "audit_selected_items_runner_bridge.py":
                continue
            try:
                tree = _parse(ab)
            except (SyntaxError, ValueError):
                continue
            if "run_turn_with_selected_items_observation" in _called_names(tree):
                callers.append(base)
        self.assertEqual(callers, [],
                         msg=f"bridge gained a production caller (B opened?): {callers}")


if __name__ == "__main__":
    unittest.main()
