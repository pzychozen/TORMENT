"""Candidate model-visible context characterization (tests-only / source-only).

Green tests here identify OBLIGATIONS only; they authorize **no wiring** and make
no same-turn provenance claim. The point is to keep four meanings separate and
prove what an honest future model-visible context owner would still have to do.

Four layers, kept distinct:
  1. ``assembled_text`` — candidate FUTURE model-visible context *material*
     (what a renderer could draw on). It is NOT, by itself, the model-visible
     context AgentRunner uses today.
  2. ``selected_admitted_items(...)`` — the selected item dicts extracted from
     the same ``AssembledContext`` (a subset of its selected blocks).
  3. packet evidence snippets — a minimized / capped / marker-excluded audit
     representation. **NOT prompt material.**
  4. model-visible inclusion obligation — a future owner must prove selected
     admitted item text appears in the *actual* model-visible context used for
     generation. Co-location / assembler membership does NOT discharge this.

Important nuance: identity / private / canon / deep / spirit exclusions are
**packet / audit-evidence** boundaries. If such text appears in
``assembled_text`` that may reflect existing prompt-context behavior, but it must
**not** become admissible audit evidence. Prompt inclusion != admissible
evidence.

No production code, no wiring, no endpoint/schema/API, no AgentRunner change, no
prompt/model/provider/evaluator change, no persistence/output-control/authority/
provenance flag, no AssembledContext into AgentRunner, no fresh retrieval, no
stale/raw-hit reuse, no structural co-location claim.
"""

import ast
import os
import unittest

from torment_service.retrieval_assembler import assemble_context, AssembledContext
from torment_service.audit_evidence_context import selected_admitted_items
from torment_service.audit_evidence_sidecar import build_audit_evidence_sidecar_from_items


# --- source/AST helpers ----------------------------------------------------

def _torment_service_dir():
    here = os.path.dirname(os.path.abspath(__file__))            # tests/
    return os.path.join(os.path.dirname(here), "torment_service")


def _parse_service(filename):
    with open(os.path.join(_torment_service_dir(), filename), "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))        # null-strip: mount artifact only


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


# --- input helper ----------------------------------------------------------

def _core_hit(eid, text, *, tier="", half_life=30.0, mtype="memory", canon=False):
    return {
        "eid": eid, "text": text, "type": mtype, "character_tier": tier,
        "half_life": half_life, "canon": canon, "final_score": 1.0,
    }


# Layer-4 obligation predicate (the bar any future owner must meet).
def _proves_inclusion(selected_item_texts, model_visible_context_text):
    return all(t in model_visible_context_text for t in selected_item_texts)


_ORD = "ZZORD ordinary relational fact"
_CANON = "ZZCANON canon identity material"


def _mixed_assembled():
    return assemble_context(
        core_hits=[
            _core_hit(1, _ORD, tier="relational"),
            _core_hit(2, _CANON, mtype="seed_canon", canon=True),
        ],
        token_budget=4000,
    )


class TestAssemblerLayers(unittest.TestCase):
    """Layer 1 + 2 shape and correspondence."""

    def test_assemble_context_produces_assembled_text_blocks_selection_log(self):
        a = _mixed_assembled()
        self.assertIsInstance(a, AssembledContext)
        self.assertIsInstance(a.assembled_text, str)
        self.assertTrue(a.assembled_text)
        self.assertIsInstance(a.blocks, dict)
        self.assertIsInstance(a.selection_log, list)

    def test_selected_admitted_items_maps_selected_log_to_selected_blocks(self):
        a = _mixed_assembled()
        items = selected_admitted_items(a)
        got = {(it.get("block_type"), it.get("eid"), it.get("chunk_id")) for it in items}
        selected = {
            (e.get("block_type"), e.get("eid"), e.get("chunk_id"))
            for e in a.selection_log if e.get("action") == "selected"
        }
        self.assertEqual(got, selected)
        self.assertTrue(items)

    def test_budget_skipped_candidates_are_not_selected_admitted_items(self):
        kept = _core_hit(1, "ZZKEPT small relational", tier="relational")
        big = _core_hit(2, "ZZSKIPPED " + ("filler " * 120), half_life=1.0)  # situational, large
        a = assemble_context(core_hits=[kept, big], token_budget=80, profile="balanced")
        sel_eids = {e.get("eid") for e in a.selection_log if e.get("action") == "selected"}
        self.assertIn(1, sel_eids)
        self.assertNotIn(2, sel_eids)
        items = selected_admitted_items(a)
        self.assertNotIn(2, {it.get("eid") for it in items})
        for it in items:
            self.assertNotIn("ZZSKIPPED", it.get("text", ""))

    def test_selected_item_text_maps_into_assembled_text(self):
        # Layer 1 <-> 2: every selected admitted item's rendered block text is in
        # assembled_text (candidate material correspondence; not yet model-visible).
        a = _mixed_assembled()
        for it in selected_admitted_items(a):
            self.assertIn(it["text"], a.assembled_text)


class TestPacketIsNotPromptMaterial(unittest.TestCase):
    """Layer 3: packet snippets are a minimized/capped/marker-excluded audit
    representation — never prompt material; packet exclusion != prompt exclusion."""

    def test_packet_snippets_are_minimized_not_assembled_text(self):
        a = _mixed_assembled()
        packet = build_audit_evidence_sidecar_from_items("resp", selected_admitted_items(a))
        self.assertIn("evidence_items", packet)
        self.assertNotIn("assembled_text", packet)         # packet is not the prompt text
        for e in packet["evidence_items"]:
            if "snippet" in e:
                self.assertLessEqual(len(e["snippet"]), 240)   # capped/minimized

    def test_packet_exclusion_is_not_prompt_exclusion(self):
        # The canon/identity block IS in assembled_text (existing prompt-context
        # behavior) but is EXCLUDED from the packet (identity_context audit
        # boundary). Prompt inclusion != admissible evidence.
        a = _mixed_assembled()
        self.assertIn(_CANON, a.assembled_text)             # present in candidate material
        packet = build_audit_evidence_sidecar_from_items("resp", selected_admitted_items(a))
        joined = " ".join(e.get("snippet", "") for e in packet["evidence_items"])
        self.assertIn("ZZORD", joined)                      # ordinary kept as evidence
        self.assertNotIn("ZZCANON", joined)                 # identity excluded from evidence

    def test_identity_marker_exclusions_are_audit_boundaries_not_prompt_rules(self):
        # Generalization: marker/identity exclusions (identity/private/canon/deep/
        # spirit) govern admissible AUDIT EVIDENCE, not what is in the model-visible
        # prompt. An excluded item may still be present in assembled_text.
        a = _mixed_assembled()
        items = selected_admitted_items(a)
        excluded_from_packet = {
            it["text"] for it in items
            if it.get("block_type") == "identity_context"
        }
        self.assertTrue(excluded_from_packet)
        packet = build_audit_evidence_sidecar_from_items("resp", items)
        snip = " ".join(e.get("snippet", "") for e in packet["evidence_items"])
        for txt in excluded_from_packet:
            self.assertNotIn(txt, snip)                     # not admissible evidence
            self.assertIn(txt, a.assembled_text)            # but may be in prompt material


class TestModelVisibleInclusionObligation(unittest.TestCase):
    """Layer 4: assembler membership does not discharge the inclusion obligation.
    A future owner must prove selected item text is in the ACTUAL model-visible
    context — which today's prompt path does not render from assembled_text."""

    def test_assembler_membership_does_not_prove_model_visible_inclusion(self):
        a = _mixed_assembled()
        item_texts = [it["text"] for it in selected_admitted_items(a)]
        # Items are in assembled_text (candidate material)...
        self.assertTrue(_proves_inclusion(item_texts, a.assembled_text))
        # ...but the model-visible context AgentRunner builds today is system
        # prompt + user input (see A-prime characterization), NOT assembled_text.
        model_visible_today = "[system prompt from frame+mode]\nuser: what is the time?"
        self.assertFalse(
            _proves_inclusion(item_texts, model_visible_today),
            "obligation must NOT be satisfiable from assembler membership alone",
        )


class TestNoProductionConsumption(unittest.TestCase):
    """No current AgentRunner prompt path consumes assembled_text /
    selected_admitted_items, no AssembledContext enters AgentRunner, and no
    production prompt path treats packet snippets as prompt material."""

    _FORBIDDEN_IN_PROMPT_PATH = {
        "assemble_context", "AssembledContext", "assembled_text",
        "selected_admitted_items", "audit_evidence_packet", "evidence_items",
    }

    def test_agent_runner_prompt_path_does_not_consume_assembled_or_selected(self):
        cls = _class(_parse_service("agent_loop.py"), "AgentRunner")
        self.assertIsNotNone(cls)
        execute = _method(cls, "_execute")
        self.assertIsNotNone(execute, "AgentRunner._execute not found")
        # _build_system_prompt is checked when present (mount may truncate it in
        # some sandboxes; the authoritative repo has it).
        nodes = [execute, _method(cls, "_build_system_prompt")]
        idents = _idents(*nodes)
        leaked = idents & self._FORBIDDEN_IN_PROMPT_PATH
        self.assertEqual(
            leaked, set(),
            msg=f"AgentRunner prompt path consumes audit/assembler surface: {sorted(leaked)}",
        )

    def test_no_assembledcontext_or_retrieval_assembler_in_agent_runner(self):
        tree = _parse_service("agent_loop.py")
        leaves = set()
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module:
                leaves.add(n.module.split(".")[-1])
                for x in n.names:
                    names.add(x.name)
            elif isinstance(n, ast.Import):
                for x in n.names:
                    leaves.add(x.name.split(".")[-1])
        self.assertNotIn("retrieval_assembler", leaves)
        self.assertNotIn("AssembledContext", names)
        self.assertNotIn("AssembledContext", _idents(tree))

    def test_app_prompt_endpoints_do_not_treat_packet_as_prompt_material(self):
        # app.py builds no model-visible generation; it must not reference the
        # packet/evidence as prompt material or call run_turn.
        idents = _idents(_parse_service("app.py"))
        for bad in ("audit_evidence_packet", "evidence_items", "run_turn",
                    "AgentRunner", "audit_admitted_context_items"):
            self.assertNotIn(bad, idents, msg=f"app.py references {bad}")


if __name__ == "__main__":
    unittest.main()
