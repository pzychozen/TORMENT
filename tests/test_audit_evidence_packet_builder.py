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


class TestExcludesSensitiveMarkerClassesInMetadata(unittest.TestCase):
    """Each existing sensitivity marker ALSO excludes when it lives one level
    inside ``metadata`` — the shape real ContextBlock dicts (asdict) carry."""

    def _excluded(self, metadata):
        item = {"eid": 1, "summary": "x", "metadata": metadata}
        pkt = build_audit_evidence_packet("resp", [item])
        self.assertEqual(_items(pkt), [], f"metadata marker should exclude: {metadata!r}")

    def test_canon(self):
        self._excluded({"canon": True})

    def test_kind_seed(self):
        self._excluded({"kind": "seed"})

    def test_kind_identity(self):
        self._excluded({"kind": "identity"})

    def test_tier_core_identity(self):
        self._excluded({"tier": "core_identity"})

    def test_type_fallback_seed(self):
        self._excluded({"type": "seed"})

    def test_governance_protected(self):
        self._excluded({"governance": {"protected": True}})

    def test_governance_non_shareable(self):
        self._excluded({"governance": {"non_shareable": True}})

    def test_scope_private(self):
        self._excluded({"scope": "private"})

    def test_srg_is_crystal(self):
        self._excluded({"srg": {"is_crystal": True}})

    def test_deep_memory(self):
        self._excluded({"deep_memory": True})

    def test_spirit_return_mode(self):
        self._excluded({"spirit_return_mode": "resonance"})

    def test_non_marker_metadata_does_not_exclude(self):
        # Negative control: ordinary metadata (no marker) is not sensitive.
        item = {
            "eid": 7, "scope": "shared", "summary": "ordinary",
            "metadata": {"type": "memory", "half_life": 30.0, "warmth_score": 0.4},
        }
        out = _items(build_audit_evidence_packet("resp", [item]))
        self.assertEqual({e.get("eid") for e in out}, {7})


class TestIsSeedMarker(unittest.TestCase):
    """``is_seed is True`` excludes at the top level and inside metadata."""

    def test_top_level_is_seed_excluded(self):
        pkt = build_audit_evidence_packet(
            "resp", [{"eid": 1, "is_seed": True, "summary": "x"}]
        )
        self.assertEqual(_items(pkt), [])

    def test_metadata_is_seed_excluded(self):
        # Mirrors retrieval_assembler._build_seed_block: metadata={"is_seed": True}.
        pkt = build_audit_evidence_packet(
            "resp", [{"eid": 1, "summary": "x", "metadata": {"is_seed": True}}]
        )
        self.assertEqual(_items(pkt), [])

    def test_is_seed_not_strictly_true_is_not_a_seed_marker(self):
        # Strict ``is True``: a falsey is_seed value is not a seed marker.
        item = {
            "eid": 2, "scope": "shared", "summary": "ordinary",
            "metadata": {"is_seed": False},
        }
        out = _items(build_audit_evidence_packet("resp", [item]))
        self.assertEqual({e.get("eid") for e in out}, {2})


class TestMetadataNeverCopiedIntoOutput(unittest.TestCase):
    """The metadata read is for exclusion only. No metadata key/value, and no
    nested payload inside metadata, is ever copied into the packet output."""

    def test_non_marker_metadata_not_copied(self):
        item = {
            "eid": 1, "scope": "shared", "lane": "core",
            "source_class": "memory", "support_bucket": "high",
            "summary": "ordinary fact",
            "metadata": {
                "half_life": 30.0, "warmth_score": 0.4, "doc_title": "D",
                "provenance_type": "collective_echo", "type": "memory",
            },
        }
        entry = _items(build_audit_evidence_packet("resp", [item]))[0]
        self.assertNotIn("metadata", entry)
        for leaked in ("half_life", "warmth_score", "doc_title",
                       "provenance_type", "type"):
            self.assertNotIn(leaked, entry)
        # Only the allowlisted primitives + snippet survive.
        self.assertEqual(entry.get("eid"), 1)
        self.assertEqual(entry.get("lane"), "core")
        self.assertEqual(entry.get("snippet"), "ordinary fact")

    def test_nested_metadata_payload_not_copied(self):
        item = {
            "eid": 1, "scope": "shared", "summary": "fact",
            "metadata": {"payload": {"secret": "nope"}, "srg": {"R": 0.1}},
        }
        entry = _items(build_audit_evidence_packet("resp", [item]))[0]
        self.assertNotIn("metadata", entry)
        self.assertNotIn("payload", entry)
        self.assertNotIn("srg", entry)
        for k, v in entry.items():
            self.assertIsInstance(k, str)
            self.assertTrue(v is None or isinstance(v, (str, int, float, bool)))


class TestStructuralBlockTypeExclusion(unittest.TestCase):
    """§4A coarse structural exclusion: items whose post-assembler block_type is
    ``identity_context`` are dropped even when no marker survives. block_type is
    read-only / exclusion-only and is never projected into packet output."""

    def test_identity_context_no_marker_excluded(self):
        item = {"eid": 1, "block_type": "identity_context", "summary": "x"}
        self.assertEqual(_items(build_audit_evidence_packet("resp", [item])), [])

    def test_identity_context_with_benign_metadata_excluded(self):
        # Marker-invisible identity hit: type=="seed_canon" is NOT in the lifecycle
        # exact-match set, half_life is not a marker, no is_seed — only block_type
        # identifies it.
        item = {
            "eid": 1, "block_type": "identity_context", "summary": "x",
            "metadata": {"type": "seed_canon", "half_life": 400.0},
        }
        self.assertEqual(_items(build_audit_evidence_packet("resp", [item])), [])

    def test_other_block_types_kept_when_non_sensitive(self):
        kept_types = (
            "reference_context", "relational_context",
            "situational_context", "archive_context",
        )
        items = [
            {"eid": i, "block_type": bt, "scope": "shared", "summary": "s"}
            for i, bt in enumerate(kept_types, start=1)
        ]
        out = _items(build_audit_evidence_packet("resp", items))
        self.assertEqual({e.get("eid") for e in out}, {1, 2, 3, 4})

    def test_block_type_not_projected_for_kept_items(self):
        item = {
            "eid": 9, "block_type": "relational_context", "scope": "shared",
            "lane": "relational", "summary": "ordinary fact",
        }
        entry = _items(build_audit_evidence_packet("resp", [item]))[0]
        self.assertNotIn("block_type", entry)
        self.assertEqual(entry.get("eid"), 9)
        self.assertEqual(entry.get("snippet"), "ordinary fact")

    def test_excluded_block_types_pins_assembler_constant(self):
        # Test-only drift-pin. The production builder does NOT import the
        # assembler; this asserts the literal mirrors the real constant so a
        # future rename of BLOCK_IDENTITY fails loud here.
        from torment_service import retrieval_assembler
        from torment_service.audit_evidence_packet import _EXCLUDED_BLOCK_TYPES
        self.assertEqual(
            _EXCLUDED_BLOCK_TYPES, (retrieval_assembler.BLOCK_IDENTITY,)
        )


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
        """Robust AST guard (not a substring scan): no production module IMPORTS
        the packet module / its public builder symbol, and none CALLS
        ``build_audit_evidence_packet``. Textual mentions in docstrings or
        comments (e.g. ``audit_evidence_context.py`` naming the builder to say it
        does NOT use it) are correctly not treated as callers — only real
        import/call AST nodes are. The guard still bites on any genuine wiring."""
        svc_dir = _torment_service_dir()
        offenders = []
        for fn in os.listdir(svc_dir):
            if not fn.endswith(".py") or fn == "audit_evidence_packet.py":
                continue
            with open(os.path.join(svc_dir, fn), "r", encoding="utf-8") as fh:
                src = fh.read()
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                # (a) import of the packet module or its public builder symbol
                if isinstance(node, ast.Import):
                    for n in node.names:
                        if n.name.split(".")[-1] == "audit_evidence_packet":
                            offenders.append(f"{fn}: import {n.name}")
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if mod.split(".")[-1] == "audit_evidence_packet":
                        offenders.append(f"{fn}: from {mod} import ...")
                    else:
                        for n in node.names:
                            if n.name == "build_audit_evidence_packet":
                                offenders.append(
                                    f"{fn}: from {mod} import build_audit_evidence_packet"
                                )
                # (b) call build_audit_evidence_packet(...) / *.build_audit_evidence_packet(...)
                elif isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id == "build_audit_evidence_packet":
                        offenders.append(f"{fn}: call build_audit_evidence_packet(...)")
                    elif isinstance(func, ast.Attribute) and func.attr == "build_audit_evidence_packet":
                        offenders.append(f"{fn}: call *.build_audit_evidence_packet(...)")
        self.assertEqual(
            offenders, [],
            msg=f"audit_evidence_packet has production caller(s): {offenders}",
        )


if __name__ == "__main__":
    unittest.main()
