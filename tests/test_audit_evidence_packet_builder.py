"""Tests for the pure audit evidence-packet builder.

The builder implements the Admissible Evidence Packet Contract for explicit,
caller-supplied inputs only: marker-based exclusion, caps, primitive-only
projection, no nested payload pass-through. It is a pure transform and is called
nowhere in production.

Scope honesty: these tests prove packet minimization for explicit inputs only.
They do NOT prove that any future caller supplied genuinely already-admitted
response context — that source-of-context guarantee is a later wiring gate.
"""

import ast
import os
import unittest

from torment_service.audit_evidence_packet import (
    build_audit_evidence_packet,
    MAX_ITEMS,
    MAX_SNIPPET_CHARS,
    MAX_TOTAL_SNIPPET_CHARS,
)


def _torment_service_dir():
    here = os.path.dirname(os.path.abspath(__file__))            # tests/
    return os.path.join(os.path.dirname(here), "torment_service")


def _items(packet):
    return packet["evidence_items"]


class TestExcludesSensitiveMarkerClasses(unittest.TestCase):
    """Each existing sensitivity marker excludes its item from the packet."""

    def _excluded(self, item):
        pkt = build_audit_evidence_packet("resp", [item])
        self.assertEqual(_items(pkt), [], f"item should have been excluded: {item!r}")

    def test_canon(self):
        self._excluded({"eid": 1, "canon": True, "summary": "x"})

    def test_kind_seed(self):
        self._excluded({"eid": 2, "kind": "seed", "summary": "x"})

    def test_kind_identity(self):
        self._excluded({"eid": 3, "kind": "identity", "summary": "x"})

    def test_tier_core_identity(self):
        self._excluded({"eid": 4, "tier": "core_identity", "summary": "x"})

    def test_type_fallback_seed(self):
        self._excluded({"eid": 5, "type": "seed", "summary": "x"})

    def test_governance_protected(self):
        self._excluded({"eid": 6, "governance": {"protected": True}, "summary": "x"})

    def test_governance_non_shareable(self):
        self._excluded({"eid": 7, "governance": {"non_shareable": True}, "summary": "x"})

    def test_scope_private(self):
        self._excluded({"eid": 8, "scope": "private", "summary": "x"})

    def test_srg_is_crystal(self):
        # Anti-pattern marker only; SRG/R-field not reopened.
        self._excluded({"eid": 9, "srg": {"is_crystal": True}, "summary": "x"})

    def test_deep_memory(self):
        self._excluded({"eid": 10, "deep_memory": True, "summary": "x"})

    def test_spirit_return_mode(self):
        self._excluded({"eid": 11, "spirit_return_mode": "resonance", "summary": "x"})


class TestKeepsNonSensitiveItems(unittest.TestCase):

    def test_ordinary_item_kept_with_primitive_metadata(self):
        item = {
            "eid": 42, "scope": "shared", "lane": "relational",
            "source_class": "memory", "support_bucket": "high",
            "summary": "an ordinary shared fact",
        }
        pkt = build_audit_evidence_packet("resp", [item])
        out = _items(pkt)
        self.assertEqual(len(out), 1)
        entry = out[0]
        self.assertEqual(entry.get("eid"), 42)
        self.assertEqual(entry.get("lane"), "relational")
        self.assertEqual(entry.get("source_class"), "memory")
        self.assertEqual(entry.get("support_bucket"), "high")
        self.assertEqual(entry.get("snippet"), "an ordinary shared fact")

    def test_response_text_copied_as_audit_subject(self):
        pkt = build_audit_evidence_packet("the produced response", [])
        self.assertEqual(pkt["response_text"], "the produced response")
        self.assertEqual(_items(pkt), [])


class TestCaps(unittest.TestCase):

    def test_item_cap_max_8(self):
        items = [{"eid": i, "scope": "shared", "summary": "s"} for i in range(10)]
        pkt = build_audit_evidence_packet("resp", items)
        self.assertEqual(len(_items(pkt)), MAX_ITEMS)
        self.assertEqual(MAX_ITEMS, 8)

    def test_snippet_cap_240_chars(self):
        item = {"eid": 1, "scope": "shared", "summary": "a" * 300}
        pkt = build_audit_evidence_packet("resp", [item])
        snip = _items(pkt)[0]["snippet"]
        self.assertEqual(len(snip), MAX_SNIPPET_CHARS)
        self.assertEqual(MAX_SNIPPET_CHARS, 240)

    def test_total_snippet_cap_invariant_2000(self):
        # With 8 items * 240 chars the total (1920) stays under 2000; assert the
        # invariant holds (the total cap is retained defensively, non-binding
        # under current cap values).
        items = [{"eid": i, "scope": "shared", "summary": "a" * 240} for i in range(8)]
        pkt = build_audit_evidence_packet("resp", items)
        total = sum(len(e.get("snippet", "")) for e in _items(pkt))
        self.assertLessEqual(total, MAX_TOTAL_SNIPPET_CHARS)
        for e in _items(pkt):
            self.assertLessEqual(len(e.get("snippet", "")), MAX_SNIPPET_CHARS)


class TestPrimitiveOnlyAndNoNesting(unittest.TestCase):

    def test_output_is_primitive_only(self):
        item = {
            "eid": 1, "scope": "shared", "lane": "core", "summary": "fact",
            # nested objects that must NOT pass through:
            "payload": {"secret": "nope"}, "srg": {"R": 0.1},
            "governance": {"some": "obj"},
        }
        pkt = build_audit_evidence_packet("resp", [item])
        self.assertIsInstance(pkt["response_text"], str)
        for entry in _items(pkt):
            for k, v in entry.items():
                self.assertIsInstance(k, str)
                self.assertTrue(
                    v is None or isinstance(v, (str, int, float, bool)),
                    msg=f"non-primitive value for {k!r}: {v!r}",
                )

    def test_no_nested_payload_pass_through(self):
        item = {
            "eid": 1, "scope": "shared", "summary": "fact",
            "payload": {"secret": "nope"}, "srg": {"R": 0.1},
            "governance": {"x": 1},
        }
        entry = _items(build_audit_evidence_packet("resp", [item]))[0]
        self.assertNotIn("payload", entry)
        self.assertNotIn("srg", entry)
        self.assertNotIn("governance", entry)


class TestUsesOnlySuppliedItems(unittest.TestCase):

    def test_empty_input_yields_empty_evidence(self):
        self.assertEqual(_items(build_audit_evidence_packet("resp", [])), [])

    def test_output_eids_subset_of_supplied(self):
        items = [{"eid": i, "scope": "shared", "summary": "s"} for i in (101, 102, 103)]
        out = _items(build_audit_evidence_packet("resp", items))
        out_eids = {e.get("eid") for e in out}
        self.assertTrue(out_eids.issubset({101, 102, 103}))


class TestSourceGuards(unittest.TestCase):
    """AST/source guards: the helper imports nothing forbidden and is called
    nowhere in production; no output-control/writer path is referenced."""

    HELPER = os.path.join(_torment_service_dir(), "audit_evidence_packet.py")
    ALLOWED_IMPORT_LEAVES = {"__future__", "typing", "lifecycle"}

    def _helper_source(self):
        with open(self.HELPER, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_imports_only_allowlisted_modules(self):
        tree = ast.parse(self._helper_source())
        leaves = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    leaves.add(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    leaves.add(node.module.split(".")[-1])
        self.assertTrue(
            leaves.issubset(self.ALLOWED_IMPORT_LEAVES),
            msg=(
                "audit_evidence_packet.py imports outside the allowlist "
                f"{sorted(self.ALLOWED_IMPORT_LEAVES)}: {sorted(leaves)}"
            ),
        )

    def test_no_output_control_or_writer_references(self):
        src = self._helper_source()
        for bad in ("review.blocked", ".ingest(", "gravity_correction",
                    "promote_chunk", ".query(", "filter_llm_facing"):
            self.assertNotIn(bad, src, msg=f"helper references forbidden seam: {bad}")

    def test_helper_has_no_production_caller(self):
        svc_dir = _torment_service_dir()
        offenders = []
        for fn in os.listdir(svc_dir):
            if not fn.endswith(".py") or fn == "audit_evidence_packet.py":
                continue
            with open(os.path.join(svc_dir, fn), "r", encoding="utf-8") as fh:
                content = fh.read()
            if "audit_evidence_packet" in content or "build_audit_evidence_packet" in content:
                offenders.append(fn)
        self.assertEqual(
            offenders, [],
            msg=f"audit_evidence_packet referenced by production module(s): {offenders}",
        )


if __name__ == "__main__":
    unittest.main()
