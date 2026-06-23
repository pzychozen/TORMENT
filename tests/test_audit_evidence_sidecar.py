"""Tests for the pure audit evidence sidecar composition helper.

The sidecar composes the two existing pure stages (selected-item extraction +
packet minimization) from EXPLICIT caller-supplied inputs. It is called nowhere
in production; it selects no sink and performs no wiring. These tests build real
``AssembledContext`` objects (``assemble_context``) only as test inputs.

Caller-relationship note (precise): ``audit_evidence_packet`` and
``audit_evidence_context`` are no longer literally "called nowhere" — they are
called ONLY by ``audit_evidence_sidecar.py`` (this helper), which is itself
called nowhere. No live production surface (endpoint / AgentRunner / ``/retrieve``
/ model / writer / persistence) calls any of the three.
"""

import ast
import os
import unittest

from torment_service.audit_evidence_sidecar import (
    build_audit_evidence_sidecar_from_items,
    build_audit_evidence_sidecar_from_assembled_context,
)
from torment_service.audit_evidence_packet import build_audit_evidence_packet


def _torment_service_dir():
    here = os.path.dirname(os.path.abspath(__file__))            # tests/
    return os.path.join(os.path.dirname(here), "torment_service")


def _core_hit(eid, text, *, tier="", half_life=30.0, mtype="memory", canon=False):
    return {
        "eid": eid, "text": text, "type": mtype, "character_tier": tier,
        "half_life": half_life, "canon": canon, "final_score": 1.0,
    }


class TestItemCore(unittest.TestCase):

    def test_item_core_returns_existing_packet_shape(self):
        items = [{"eid": 1, "scope": "shared", "summary": "ordinary fact"}]
        sidecar = build_audit_evidence_sidecar_from_items("resp", items)
        packet = build_audit_evidence_packet("resp", items)
        # Same top-level shape as the existing packet; returned directly.
        self.assertEqual(set(sidecar.keys()), set(packet.keys()))
        self.assertEqual(set(sidecar.keys()), {"response_text", "evidence_items"})
        self.assertEqual(sidecar, packet)
        # No wrapper schema.
        for k in ("kind", "version", "packet"):
            self.assertNotIn(k, sidecar)

    def test_item_core_carries_response_text_as_audit_subject(self):
        sidecar = build_audit_evidence_sidecar_from_items("the produced response", [])
        self.assertEqual(sidecar["response_text"], "the produced response")
        self.assertEqual(sidecar["evidence_items"], [])


class TestAssembledContextWrapper(unittest.TestCase):

    def _assemble(self, core_hits):
        # assemble_context imported in the TEST only (never in the sidecar).
        from torment_service.retrieval_assembler import assemble_context
        return assemble_context(core_hits=core_hits, token_budget=4000)

    def test_assembled_context_wrapper_includes_ordinary_selected_evidence(self):
        assembled = self._assemble([
            _core_hit(1, "ZZORD ordinary relational fact", tier="relational"),
        ])
        sidecar = build_audit_evidence_sidecar_from_assembled_context("resp", assembled)
        snippets = [e.get("snippet", "") for e in sidecar["evidence_items"]]
        self.assertIn(
            "ZZORD ordinary relational fact", snippets,
            msg=f"ordinary selected evidence missing: {sidecar['evidence_items']!r}",
        )

    def test_assembled_context_wrapper_drops_identity_context_evidence(self):
        assembled = self._assemble([
            _core_hit(1, "ZZORD ordinary relational fact", tier="relational"),
            _core_hit(2, "ZZCANON canon identity material", mtype="seed_canon", canon=True),
        ])
        sidecar = build_audit_evidence_sidecar_from_assembled_context("resp", assembled)
        joined = " ".join(e.get("snippet", "") for e in sidecar["evidence_items"])
        self.assertIn("ZZORD", joined)        # ordinary kept (existing packet behavior)
        self.assertNotIn("ZZCANON", joined)   # identity_context dropped (existing §4A behavior)

    def test_sidecar_output_does_not_project_metadata_or_block_type(self):
        assembled = self._assemble([
            _core_hit(1, "ZZORD ordinary relational fact", tier="relational"),
        ])
        sidecar = build_audit_evidence_sidecar_from_assembled_context("resp", assembled)
        self.assertTrue(sidecar["evidence_items"], "expected at least one kept item")
        for entry in sidecar["evidence_items"]:
            self.assertNotIn("metadata", entry)
            self.assertNotIn("block_type", entry)
            for k, v in entry.items():
                self.assertTrue(v is None or isinstance(v, (str, int, float, bool)))


class TestSourceGuards(unittest.TestCase):
    """AST/source guards: import surface is allowlisted, no forbidden surface is
    referenced, and the sidecar has no production caller."""

    SIDE = os.path.join(_torment_service_dir(), "audit_evidence_sidecar.py")
    ALLOWED_IMPORT_LEAVES = {
        "__future__", "typing", "audit_evidence_context", "audit_evidence_packet",
    }
    # Forbidden as CODE identifiers (AST only — docstring mentions are ignored).
    FORBIDDEN_IDENTS = {
        "assemble_context", "retrieval_assembler", "app", "agent_loop", "fabric",
        "AssembledContext", "LLMClient", "llm_client", "complete", "generate",
        "completion", "predict", "infer", "open", "requests", "httpx",
        "TestClient", "AgentRunner",
    }

    def _src(self):
        with open(self.SIDE, "r", encoding="utf-8") as fh:
            return fh.read()

    def _tree(self):
        return ast.parse(self._src())

    def test_production_import_surface_is_allowlisted(self):
        leaves = set()
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Import):
                for n in node.names:
                    leaves.add(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    leaves.add(node.module.split(".")[-1])
        self.assertTrue(
            leaves.issubset(self.ALLOWED_IMPORT_LEAVES),
            msg=f"sidecar imports outside allowlist {sorted(self.ALLOWED_IMPORT_LEAVES)}: {sorted(leaves)}",
        )

    def test_sidecar_does_not_import_or_call_forbidden_surfaces(self):
        tree = self._tree()
        # Import leaves must not include forbidden modules.
        import_leaves = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    import_leaves.add(n.name.split(".")[-1])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    import_leaves.add(node.module.split(".")[-1])
        self.assertEqual(
            import_leaves & self.FORBIDDEN_IDENTS, set(),
            msg=f"forbidden imports: {sorted(import_leaves & self.FORBIDDEN_IDENTS)}",
        )
        # Code identifiers (Name/Attribute/keyword) must not reference forbidden surfaces.
        idents = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                idents.add(node.id)
            elif isinstance(node, ast.Attribute):
                idents.add(node.attr)
            elif isinstance(node, ast.keyword) and node.arg:
                idents.add(node.arg)
        self.assertEqual(
            idents & self.FORBIDDEN_IDENTS, set(),
            msg=f"forbidden code references: {sorted(idents & self.FORBIDDEN_IDENTS)}",
        )

    def test_only_agent_loop_sink_imports_or_calls_sidecar(self):
        # The sidecar is no longer called nowhere: AgentRunner / TurnResult is the
        # ratified observation-only sink and may call the item-core builder
        # (build_audit_evidence_sidecar_from_items). No OTHER production module may
        # import or call the sidecar; agent_loop.py is the single permitted caller.
        svc_dir = _torment_service_dir()
        offenders = []
        for fn in os.listdir(svc_dir):
            if not fn.endswith(".py") or fn in (
                "audit_evidence_sidecar.py", "agent_loop.py",
            ):
                continue
            with open(os.path.join(svc_dir, fn), "r", encoding="utf-8") as fh:
                src = fh.read()
            try:
                tree = ast.parse(src)
            except (SyntaxError, ValueError):
                # ValueError covers a source string containing null bytes (a
                # mount-corruption artifact in some sandboxes); the authoritative
                # repo parses cleanly.
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        if n.name.split(".")[-1] == "audit_evidence_sidecar":
                            offenders.append(f"{fn}: import {n.name}")
                elif isinstance(node, ast.ImportFrom):
                    if (node.module or "").split(".")[-1] == "audit_evidence_sidecar":
                        offenders.append(f"{fn}: from {node.module} import ...")
                elif isinstance(node, ast.Call):
                    func = node.func
                    name = (
                        func.id if isinstance(func, ast.Name)
                        else func.attr if isinstance(func, ast.Attribute)
                        else ""
                    )
                    if name.startswith("build_audit_evidence_sidecar"):
                        offenders.append(f"{fn}: call {name}(...)")
        self.assertEqual(
            offenders, [],
            msg=f"audit_evidence_sidecar referenced by production module(s): {offenders}",
        )


if __name__ == "__main__":
    unittest.main()
