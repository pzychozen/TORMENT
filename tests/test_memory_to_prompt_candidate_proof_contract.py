"""tests/test_memory_to_prompt_candidate_proof_contract.py

Tests-first lock of the memory-to-prompt-for-generation CANDIDATE PROOF CONTRACT,
before any production code touches the prompt path.

This is NOT implementation, NOT a prompt change, NOT memory injection, NOT
retrieval-to-generation wiring, NOT endpoint/API/schema, NOT output-control, NOT
memory-write, and NOT Gate D / Envelope Audit runtime / database / substrate.

Two kinds of tests:
  * SOURCE/AST guards over production source (it never imports `torment_service`, never
    runs AgentRunner, never calls a model, never calls an endpoint, never imports/uses
    PrivateGenerationOwner) — they lock that the LIVE authoritative path still has no
    memory-to-prompt wiring and that PrivateGenerationOwner remains excluded/unwired and
    is not the authoritative AgentRunner path.
  * TEST-LOCAL CONTRACT tests using small fake in-memory objects only — they encode the
    contract a FUTURE candidate would have to satisfy (eligible source / bounded
    representation / runner-local boundary / no exposure / no feedback) and prove a
    conforming fake passes while non-conforming fakes are rejected.

It selects no production source, no injection point, and no prompt format; the candidate
boundary chain is named ONLY as proof shape. Everything is green; nothing is wired.
"""
from __future__ import annotations

import ast
import os
import unittest


# --------------------------------------------------------------------------- #
# Source/AST helpers (self-contained; mirrors the boundary characterization test)
# --------------------------------------------------------------------------- #

_MEMORY_CONTENT_IDENTS = frozenset({
    "assemble_context", "AssembledContext", "assembled_text", "character_context",
})
_GENERATION_CALLS = frozenset({
    "complete", "completion", "completions", "chat", "chat_completion",
    "create_completion", "create_chat_completion", "generate", "predict", "infer",
})
_GEN_BOUNDARY_CALLEES = frozenset(
    {"run_turn", "_complete_llm_prompt_request", "_build_llm_prompt_request"}
) | _GENERATION_CALLS

# The named candidate boundary chain (proof shape only — not selected/implemented here).
_CANDIDATE_BOUNDARY_CHAIN = ("_build_llm_prompt_request", "_complete_llm_prompt_request")

# Routes a future candidate must NOT use.
_FORBIDDEN_ROUTES = frozenset({
    "PrivateGenerationOwner", "audit_admitted_context_items", "run_turn_with_selected_items_observation",
    "dual_ownership", "u1_caller", "audit_owner",
})


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _parse_bytes(raw):
    return ast.parse(raw.replace(b"\x00", b""))


def _parse_service(filename):
    with open(os.path.join(_repo_root(), "torment_service", filename), "rb") as fh:
        return _parse_bytes(fh.read())


def _class(tree, name):
    for n in tree.body:
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


def _callee_name(call):
    f = call.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return None


def _memory_into_generation_hits(tree):
    hits = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call) or _callee_name(n) not in _GEN_BOUNDARY_CALLEES:
            continue
        arg_idents = set()
        for v in list(n.args) + [k.value for k in n.keywords]:
            for x in ast.walk(v):
                if isinstance(x, ast.Name):
                    arg_idents.add(x.id)
                elif isinstance(x, ast.Attribute):
                    arg_idents.add(x.attr)
        bad = arg_idents & _MEMORY_CONTENT_IDENTS
        if bad:
            hits.append((_callee_name(n), sorted(bad)))
    return hits


# --------------------------------------------------------------------------- #
# Test-local CONTRACT predicates + fakes (NOT production code; wire nothing)
# --------------------------------------------------------------------------- #

# Content kinds a candidate source/representation must exclude.
_EXCLUDED_CONTENT_KINDS = frozenset({
    "private_cognition", "candidate", "unadmitted", "substrate_only", "audit_packet",
})
# Authority a representation must never carry.
_AUTHORITY_MARKERS = frozenset({
    "canon", "identity_authority", "admission_authority", "writer_authority",
    "truth_authority", "output_control",
})


def eligible_source(block, *, max_items=8, max_chars=2000):
    """Candidate-source contract: existing governed read/assembly output ONLY — explicit,
    bounded, read-only, governed-read in shape, excluding forbidden content, creating no
    retrieval authority and writing nothing. (Test-local spec; not production.)"""
    if not isinstance(block, dict):
        return False
    if block.get("kind") in _EXCLUDED_CONTENT_KINDS:
        return False
    if not block.get("governed_read", False) or not block.get("read_only", False):
        return False
    if block.get("creates_retrieval_authority", False):
        return False
    if block.get("writes_memory", False) or block.get("persists", False):
        return False
    items = block.get("items")
    if not isinstance(items, (list, tuple)) or len(items) > max_items:
        return False
    if sum(len(str(x)) for x in items) > max_chars:
        return False
    return True


def valid_representation(block, *, max_chars=2000):
    """Candidate-representation contract: bounded, labelled, guidance-only,
    non-authoritative, turn-local, read-only, non-public; no forbidden content.
    (Test-local spec; not production.)"""
    if not isinstance(block, dict):
        return False
    if not block.get("label"):
        return False
    if not block.get("guidance_only", False):
        return False
    if block.get("authority"):                       # any authority marker -> invalid
        return False
    if block.get("public", False) or block.get("exposed", False):
        return False
    if not block.get("turn_local", False) or not block.get("read_only", False):
        return False
    if block.get("content_kind") in _EXCLUDED_CONTENT_KINDS:
        return False
    if len(str(block.get("text", ""))) > max_chars:
        return False
    return True


def _conforming_source():
    return {
        "kind": "governed_assembly", "governed_read": True, "read_only": True,
        "creates_retrieval_authority": False, "writes_memory": False, "persists": False,
        "items": ["a relevant recalled fact", "another bounded fact"],
    }


def _conforming_representation():
    return {
        "label": "[Memory context — guidance only]", "guidance_only": True,
        "authority": None, "public": False, "exposed": False, "turn_local": True,
        "read_only": True, "content_kind": "governed_assembly", "text": "bounded block",
    }


class _FakeRunnerLocalTurn:
    """Test-local model of a runner-local turn. A memory block may be placed ONLY into the
    runner-local prompt request; it must touch no other surface and drive no feedback."""

    # Surfaces that must never receive the block or the prompt request.
    PUBLIC_SURFACES = ("result", "metadata", "log")
    FEEDBACK_SURFACES = ("review", "output_control", "retry", "ranking", "style",
                         "write", "persistence", "retrieval")

    def __init__(self):
        self.prompt_request = None            # runner-local only
        self.result, self.metadata, self.log = {}, {}, []
        self.feedback = {k: None for k in self.FEEDBACK_SURFACES}
        self.touched = set()

    def place_in_prompt(self, block):
        # The ONLY thing the candidate boundary would do: put the block into the
        # runner-local request. Nothing else.
        self.prompt_request = {"system_prompt": "You are agent X ...",
                               "messages": [{"role": "user", "content": "..."}],
                               "memory_block": block}
        self.touched.add("prompt")

    def block_reached_public_surface(self, block):
        for s in self.PUBLIC_SURFACES:
            v = getattr(self, s)
            if block in (v.values() if isinstance(v, dict) else v):
                return True
            if self.prompt_request is not None and self.prompt_request in (
                    v.values() if isinstance(v, dict) else v):
                return True
        return False


# --------------------------------------------------------------------------- #
# 1 — current live path still has NO memory-to-prompt wiring (source/AST)
# --------------------------------------------------------------------------- #

class TestLivePathHasNoMemoryToPromptWiring(unittest.TestCase):
    def test_authoritative_path_wires_no_memory_into_generation(self):
        offenders = {}
        for fn in ("agent_loop.py", "app.py"):
            hits = _memory_into_generation_hits(_parse_service(fn))
            if hits:
                offenders[fn] = hits
        self.assertEqual(
            offenders, {},
            msg=("live authoritative AgentRunner/app path wires memory into generation "
                 f"(PrivateGenerationOwner excluded/unwired and not authoritative): {offenders}"))

    def test_private_generation_owner_not_on_authoritative_path(self):
        # PrivateGenerationOwner is referenced by neither agent_loop nor app as a code
        # identifier (imported/called/constructed) — excluded/unwired/test-called only.
        for fn in ("agent_loop.py", "app.py"):
            idents = _idents(_parse_service(fn))
            self.assertNotIn("PrivateGenerationOwner", idents,
                             f"{fn} references PrivateGenerationOwner as an identifier")


# --------------------------------------------------------------------------- #
# 2 — candidate source contract (test-local)
# --------------------------------------------------------------------------- #

class TestCandidateSourceContract(unittest.TestCase):
    def test_conforming_source_is_eligible(self):
        self.assertTrue(eligible_source(_conforming_source()))

    def test_excluded_content_kinds_rejected(self):
        for kind in _EXCLUDED_CONTENT_KINDS:
            blk = _conforming_source(); blk["kind"] = kind
            self.assertFalse(eligible_source(blk), f"{kind} source must be rejected")

    def test_non_governed_or_writing_source_rejected(self):
        for mutate in ("governed_read", "read_only"):
            blk = _conforming_source(); blk[mutate] = False
            self.assertFalse(eligible_source(blk), f"source with {mutate}=False must be rejected")
        for flag in ("creates_retrieval_authority", "writes_memory", "persists"):
            blk = _conforming_source(); blk[flag] = True
            self.assertFalse(eligible_source(blk), f"source with {flag}=True must be rejected")

    def test_unbounded_source_rejected(self):
        blk = _conforming_source(); blk["items"] = ["x"] * 99
        self.assertFalse(eligible_source(blk), "over-item-cap source must be rejected")
        blk2 = _conforming_source(); blk2["items"] = ["y" * 9999]
        self.assertFalse(eligible_source(blk2), "over-char-cap source must be rejected")


# --------------------------------------------------------------------------- #
# 3 — candidate boundary contract (named as proof shape only)
# --------------------------------------------------------------------------- #

class TestCandidateBoundaryContract(unittest.TestCase):
    def test_named_candidate_boundary_chain_exists_runner_local(self):
        cls = _class(_parse_service("agent_loop.py"), "AgentRunner")
        for name in _CANDIDATE_BOUNDARY_CHAIN:
            self.assertIsNotNone(_method(cls, name), f"named boundary method {name} missing")
        self.assertIsNotNone(_class(_parse_service("agent_loop.py"), "_LLMPromptRequest"),
                             "_LLMPromptRequest (runner-local request) missing")

    def test_named_boundary_methods_consume_no_memory_today(self):
        cls = _class(_parse_service("agent_loop.py"), "AgentRunner")
        idents = _idents(_method(cls, "_build_llm_prompt_request"),
                         _method(cls, "_complete_llm_prompt_request"))
        self.assertEqual(idents & _MEMORY_CONTENT_IDENTS, set(),
                         "named candidate boundary already consumes memory (it must not)")

    def test_contract_forbids_routing_through_orchestration(self):
        # A future candidate route description must use none of the forbidden routes.
        def route_ok(route_idents):
            return not (set(route_idents) & _FORBIDDEN_ROUTES)
        self.assertTrue(route_ok({"_build_llm_prompt_request", "_complete_llm_prompt_request"}))
        for bad in _FORBIDDEN_ROUTES:
            self.assertFalse(route_ok({"_build_llm_prompt_request", bad}),
                             f"route through {bad} must be forbidden")


# --------------------------------------------------------------------------- #
# 4 — candidate representation contract (test-local)
# --------------------------------------------------------------------------- #

class TestCandidateRepresentationContract(unittest.TestCase):
    def test_conforming_representation_is_valid(self):
        self.assertTrue(valid_representation(_conforming_representation()))

    def test_authority_bearing_representation_rejected(self):
        for marker in _AUTHORITY_MARKERS:
            blk = _conforming_representation(); blk["authority"] = marker
            self.assertFalse(valid_representation(blk), f"{marker} representation must be rejected")

    def test_public_or_exposed_representation_rejected(self):
        for flag in ("public", "exposed"):
            blk = _conforming_representation(); blk[flag] = True
            self.assertFalse(valid_representation(blk), f"{flag} representation must be rejected")

    def test_forbidden_content_or_unlabelled_or_non_guidance_rejected(self):
        for kind in _EXCLUDED_CONTENT_KINDS:
            blk = _conforming_representation(); blk["content_kind"] = kind
            self.assertFalse(valid_representation(blk), f"{kind} content must be rejected")
        for mutate in ("label", "guidance_only", "turn_local", "read_only"):
            blk = _conforming_representation()
            blk[mutate] = "" if mutate == "label" else False
            self.assertFalse(valid_representation(blk), f"representation with bad {mutate} rejected")


# --------------------------------------------------------------------------- #
# 5 — no exposure / no feedback (test-local fake runner-local turn)
# --------------------------------------------------------------------------- #

class TestNoExposureNoFeedback(unittest.TestCase):
    def test_block_reaches_only_the_runner_local_prompt(self):
        turn = _FakeRunnerLocalTurn()
        block = _conforming_representation()
        turn.place_in_prompt(block)
        self.assertEqual(turn.touched, {"prompt"}, "block touched a surface other than the prompt")
        self.assertIn("memory_block", turn.prompt_request)

    def test_request_and_block_not_exposed_publicly(self):
        turn = _FakeRunnerLocalTurn()
        block = _conforming_representation()
        turn.place_in_prompt(block)
        self.assertFalse(turn.block_reached_public_surface(block),
                         "block/request exposed on result/metadata/log")
        self.assertEqual(turn.result, {})
        self.assertEqual(turn.metadata, {})
        self.assertEqual(turn.log, [])

    def test_block_drives_no_feedback(self):
        turn = _FakeRunnerLocalTurn()
        turn.place_in_prompt(_conforming_representation())
        for surface, val in turn.feedback.items():
            self.assertIsNone(val, f"block drove feedback into {surface}")


# --------------------------------------------------------------------------- #
# 6 — exclusions
# --------------------------------------------------------------------------- #

class TestExclusions(unittest.TestCase):
    def test_no_torment_service_import_in_this_file(self):
        # This test file itself imports no torment_service / PrivateGenerationOwner.
        with open(os.path.abspath(__file__), "rb") as fh:
            idents_and_names = set()
            tree = _parse_bytes(fh.read())
            for n in ast.walk(tree):
                if isinstance(n, ast.ImportFrom) and n.module:
                    idents_and_names.add(n.module)
                elif isinstance(n, ast.Import):
                    for a in n.names:
                        idents_and_names.add(a.name)
        self.assertFalse(any(m.startswith("torment_service") for m in idents_and_names),
                         "this contract test must import no torment_service module")
        self.assertNotIn("audit_private_generation_owner", idents_and_names)

    def test_forbidden_routes_set_covers_u1_audit_owner_owner_dual(self):
        # The contract's forbidden-route set names U1, audit-owner, PrivateGenerationOwner,
        # and dual-ownership — none may be a candidate route.
        for name in ("PrivateGenerationOwner", "u1_caller", "audit_owner", "dual_ownership"):
            self.assertIn(name, _FORBIDDEN_ROUTES)


if __name__ == "__main__":
    unittest.main()
