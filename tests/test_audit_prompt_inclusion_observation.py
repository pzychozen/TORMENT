"""Tests for the inert prompt-inclusion observation helper.

The helper composes the existing audit evidence packet ONLY when every selected
admitted item's text is observed in the explicitly supplied, already-rendered
model-visible text. It is pure, inert, and called nowhere in production: it
renders nothing, performs no I/O, stores nothing, mutates no input, and routes
nothing. Packet omission (``None``) is non-punitive.
"""

import ast
import copy
import os
import unittest

from torment_service.audit_prompt_inclusion_observation import observe_prompt_inclusion_packet
from torment_service.audit_evidence_sidecar import build_audit_evidence_sidecar_from_items


_ITEM_TEXT = "ZZITEM ordinary admitted fact"


def _items(text=_ITEM_TEXT):
    return [{"eid": 1, "block_type": "relational_context", "text": text}]


def _torment_service_dir():
    here = os.path.dirname(os.path.abspath(__file__))            # tests/
    return os.path.join(os.path.dirname(here), "torment_service")


def _helper_path():
    return os.path.join(_torment_service_dir(), "audit_prompt_inclusion_observation.py")


def _parse(path):
    with open(path, "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))        # null-strip: mount artifact only


def _import_leaves(tree):
    leaves = set()
    names = set()
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


def _idents(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, ast.keyword) and n.arg:
            out.add(n.arg)
    return out


class TestPositive(unittest.TestCase):

    def test_item_in_system_prompt_yields_packet(self):
        pkt = observe_prompt_inclusion_packet(
            system_prompt=f"You are an agent.\n[Memory]\n{_ITEM_TEXT}",
            messages=[{"role": "user", "content": "hello"}],
            admitted_context_items=_items(),
            response_text="a clean response",
        )
        self.assertIsNotNone(pkt)
        self.assertIn("evidence_items", pkt)
        self.assertEqual(pkt["response_text"], "a clean response")

    def test_item_in_messages_yields_packet(self):
        pkt = observe_prompt_inclusion_packet(
            system_prompt="You are an agent.",
            messages=[{"role": "user", "content": f"context: {_ITEM_TEXT}"}],
            admitted_context_items=_items(),
            response_text="ok",
        )
        self.assertIsNotNone(pkt)
        self.assertIn("evidence_items", pkt)

    def test_exact_substring_only_no_fuzzy(self):
        # Contiguous exact item text -> packet.
        pkt = observe_prompt_inclusion_packet(
            system_prompt=f"prefix {_ITEM_TEXT} suffix",
            messages=[],
            admitted_context_items=_items(),
            response_text="ok",
        )
        self.assertIsNotNone(pkt)
        # Split across system_prompt + messages (joined with "\n") so the exact
        # item text is NOT a contiguous substring -> packet omitted (no fuzzy).
        split = observe_prompt_inclusion_packet(
            system_prompt="ZZSPLIT left",
            messages=[{"role": "user", "content": "right tail"}],
            admitted_context_items=_items("ZZSPLIT left right tail"),
            response_text="ok",
        )
        self.assertIsNone(split)

    def test_item_missing_yields_none(self):
        pkt = observe_prompt_inclusion_packet(
            system_prompt="You are an agent.",
            messages=[{"role": "user", "content": "nothing relevant here"}],
            admitted_context_items=_items(),
            response_text="ok",
        )
        self.assertIsNone(pkt)

    def test_blank_or_nonstring_response_text_yields_none(self):
        for rt in ("", "   ", None, 123):
            pkt = observe_prompt_inclusion_packet(
                system_prompt=_ITEM_TEXT,
                messages=[],
                admitted_context_items=_items(),
                response_text=rt,
            )
            self.assertIsNone(pkt, f"response_text={rt!r} should yield None")

    def test_item_without_usable_text_yields_none(self):
        for bad_item in ({"eid": 1, "block_type": "relational_context"},
                         {"eid": 1, "text": 123},
                         {"eid": 1, "text": ""}):
            pkt = observe_prompt_inclusion_packet(
                system_prompt="anything",
                messages=[],
                admitted_context_items=[bad_item],
                response_text="ok",
            )
            self.assertIsNone(pkt, f"item={bad_item!r} should yield None")

    def test_packet_contains_no_captured_prompt_or_messages(self):
        pkt = observe_prompt_inclusion_packet(
            system_prompt=f"SP {_ITEM_TEXT}",
            messages=[{"role": "user", "content": "MSGCONTENT"}],
            admitted_context_items=_items(),
            response_text="ok",
        )
        self.assertIsNotNone(pkt)
        self.assertEqual(set(pkt.keys()), {"response_text", "evidence_items"})
        blob = repr(pkt)
        self.assertNotIn("MSGCONTENT", blob)        # message content not echoed
        self.assertNotIn("SP ", blob)               # system prompt not echoed

    def test_packet_built_from_items_and_response_only(self):
        items = _items()
        pkt = observe_prompt_inclusion_packet(
            system_prompt=_ITEM_TEXT, messages=[],
            admitted_context_items=items, response_text="resp",
        )
        direct = build_audit_evidence_sidecar_from_items("resp", items)
        self.assertEqual(pkt, direct)

    def test_inputs_not_mutated(self):
        messages = [{"role": "user", "content": f"x {_ITEM_TEXT}"}]
        items = _items()
        m_before = copy.deepcopy(messages)
        i_before = copy.deepcopy(items)
        observe_prompt_inclusion_packet(
            system_prompt="sp", messages=messages,
            admitted_context_items=items, response_text="ok",
        )
        self.assertEqual(messages, m_before)
        self.assertEqual(items, i_before)


class TestSourceGuards(unittest.TestCase):

    ALLOWED_IMPORT_LEAVES = {"__future__", "typing", "audit_evidence_sidecar"}
    FORBIDDEN_IDENTIFIERS = {
        "run_turn", "AgentRunner", "TurnResult", "ExecutionOutcome", "review",
        "complete", "llm_client", "assemble_context", "AssembledContext",
        "fabric", "ingest", "writer", "persistence", "database", "endpoint",
        "app", "agent_loop",
    }
    FORBIDDEN_FLAG_WORDS = (
        "same_turn_verified", "provenance_verified", "verified", "truth",
        "authority", "certified", "trusted", "honest",
    )

    def test_helper_imports_only_allowlisted(self):
        leaves, _ = _import_leaves(_parse(_helper_path()))
        self.assertTrue(
            leaves.issubset(self.ALLOWED_IMPORT_LEAVES),
            msg=f"helper imports outside allowlist: {sorted(leaves - self.ALLOWED_IMPORT_LEAVES)}",
        )

    def test_helper_has_no_forbidden_identifiers(self):
        # Identifier-EXACT (Name/Attribute/keyword + import leaves/names) so that
        # legitimate tokens like ``append`` do not false-match ``app``.
        tree = _parse(_helper_path())
        leaves, names = _import_leaves(tree)
        all_tokens = _idents(tree) | leaves | names
        offenders = all_tokens & self.FORBIDDEN_IDENTIFIERS
        self.assertEqual(offenders, set(), msg=f"helper references forbidden identifiers: {sorted(offenders)}")

    def test_helper_source_has_no_forbidden_flag_words(self):
        with open(_helper_path(), "r", encoding="utf-8") as fh:
            src = fh.read().lower()
        present = [w for w in self.FORBIDDEN_FLAG_WORDS if w in src]
        self.assertEqual(present, [], msg=f"helper source contains forbidden flag word(s): {present}")

    def test_no_production_module_imports_or_calls_helper(self):
        svc = _torment_service_dir()
        offenders = []
        for fn in os.listdir(svc):
            if not fn.endswith(".py") or fn == "audit_prompt_inclusion_observation.py":
                continue
            try:
                tree = _parse(os.path.join(svc, fn))
            except (SyntaxError, ValueError):
                continue
            for n in ast.walk(tree):
                if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[-1] == "audit_prompt_inclusion_observation":
                    offenders.append(f"{fn}: import")
                elif isinstance(n, ast.Import) and any(x.name.split(".")[-1] == "audit_prompt_inclusion_observation" for x in n.names):
                    offenders.append(f"{fn}: import")
                elif isinstance(n, ast.Call):
                    f = n.func
                    nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
                    if nm == "observe_prompt_inclusion_packet":
                        offenders.append(f"{fn}: call")
        self.assertEqual(offenders, [], msg=f"helper has production caller(s): {offenders}")

    def test_app_does_not_import_helper(self):
        leaves, names = _import_leaves(_parse(os.path.join(_torment_service_dir(), "app.py")))
        self.assertNotIn("audit_prompt_inclusion_observation", leaves)
        self.assertNotIn("observe_prompt_inclusion_packet", names)

    def test_agent_loop_does_not_import_helper(self):
        leaves, names = _import_leaves(_parse(os.path.join(_torment_service_dir(), "agent_loop.py")))
        self.assertNotIn("audit_prompt_inclusion_observation", leaves)
        self.assertNotIn("observe_prompt_inclusion_packet", names)


if __name__ == "__main__":
    unittest.main()
