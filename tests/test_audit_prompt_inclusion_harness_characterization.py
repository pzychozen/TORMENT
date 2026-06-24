"""Prompt-inclusion harness characterization (tests-only / source-only).

Demonstrates the EXECUTABLE PROOF SHAPE a future model-visible context owner
would have to satisfy — without live provenance, production wiring, or any
AgentRunner involvement.

Why not ``AgentRunner.run_turn`` for the positive proof: today ``run_turn``
cannot accept a caller-rendered model-visible context (its prompt path is system
prompt + ``frame.raw_input`` only), so passing ``audit_admitted_context_items``
into it would recreate structural CO-LOCATION, not provenance. So the positive
proof uses a TEST-LOCAL fake generation boundary that captures the EXACT rendered
prompt/messages, and proves selected item-text inclusion in that captured
context before any packet is composed.

Proof shape:
  1. build a real ``AssembledContext`` via ``assemble_context``;
  2. extract ``selected_admitted_items(...)`` from the same object;
  3. render a test-local candidate model-visible context from ``assembled_text``
     + user input;
  4. hand that EXACT rendered text to a fake boundary that records it;
  5. prove every selected item text is in the captured context (else REFUSE);
  6. only then compose the packet from the selected item dicts;
  7. packet snippets are audit representation, NOT prompt material.

Boundaries: no production code, no wiring, no endpoint/schema/API, no AgentRunner
change, no prompt/model/provider/evaluator production behavior, no persistence/
memory-write/output-control, no authority/provenance/truth/``same_turn_verified``
flag, no ``AssembledContext`` into AgentRunner, no live same-turn provenance
claim. Packet absence remains non-evidence of dishonesty/unsupportedness.
"""

import ast
import os
import unittest

from torment_service.retrieval_assembler import assemble_context
from torment_service.audit_evidence_context import selected_admitted_items
from torment_service.audit_evidence_sidecar import build_audit_evidence_sidecar_from_items


_ORD = "ZZORD ordinary relational fact"
_CANON = "ZZCANON canon identity material"


def _core_hit(eid, text, *, tier="", half_life=30.0, mtype="memory", canon=False):
    return {"eid": eid, "text": text, "type": mtype, "character_tier": tier,
            "half_life": half_life, "canon": canon, "final_score": 1.0}


def _mixed_assembled():
    return assemble_context(
        core_hits=[
            _core_hit(1, _ORD, tier="relational"),
            _core_hit(2, _CANON, mtype="seed_canon", canon=True),
        ],
        token_budget=4000,
    )


# --- test-local harness (stand-in for a FUTURE owner; touches no production) ---

class _FakeLLMBoundary:
    """Records the EXACT rendered prompt/messages it receives. Performs no real
    generation and calls no provider."""

    def __init__(self):
        self.calls = []

    def complete(self, *, system_prompt, messages):
        self.calls.append({
            "system_prompt": str(system_prompt),
            "messages": [dict(m) for m in messages],
        })
        return "stub response (no real generation)"

    @property
    def captured_model_visible_text(self):
        if not self.calls:
            return ""
        c = self.calls[-1]
        return "\n".join([c["system_prompt"]] + [str(m.get("content", "")) for m in c["messages"]])


def _render_candidate_model_visible_context(assembled_text, user_input, *, include_memory=True):
    """A future owner renders the model-visible context here. ``include_memory``
    True actually places the candidate memory material (assembled_text) into the
    model-visible context; False omits it (mirroring today's AgentRunner prompt
    path: system + user only)."""
    system_prompt = "You are an agent."
    if include_memory:
        system_prompt += "\n[Memory Context]\n" + assembled_text
    messages = [{"role": "user", "content": user_input}]
    return system_prompt, messages


def _selected_item_texts_in_context(items, captured_context):
    return all(it.get("text", "") in captured_context for it in items)


class _PromptInclusionError(AssertionError):
    pass


def _require_inclusion_or_refuse(items, captured_context):
    """The owner's obligation gate: every selected item text MUST be present in
    the captured model-visible context, else REFUSE (raise). Checks inclusion
    only; claims no provenance."""
    missing = [it.get("text", "") for it in items
               if it.get("text", "") not in captured_context]
    if missing:
        raise _PromptInclusionError(f"selected item text(s) absent from captured context: {missing}")
    return True


class TestProofShape(unittest.TestCase):

    def test_inclusion_proven_then_packet_composed(self):
        assembled = _mixed_assembled()
        items = selected_admitted_items(assembled)
        self.assertTrue(items)

        boundary = _FakeLLMBoundary()
        sp, msgs = _render_candidate_model_visible_context(
            assembled.assembled_text, "what is the plan?", include_memory=True,
        )
        response = boundary.complete(system_prompt=sp, messages=msgs)
        captured = boundary.captured_model_visible_text

        # Inclusion proven in the EXACT captured model-visible context.
        self.assertTrue(_require_inclusion_or_refuse(items, captured))

        # Only now compose the packet from the selected item dicts.
        packet = build_audit_evidence_sidecar_from_items(response, items)
        self.assertIn("evidence_items", packet)
        # Packet is NOT prompt material: its structure never entered the captured
        # context, and it carries no assembled_text.
        self.assertNotIn("assembled_text", packet)
        self.assertNotIn("evidence_items", captured)
        for e in packet["evidence_items"]:
            if "snippet" in e:
                self.assertLessEqual(len(e["snippet"]), 240)

    def test_no_live_provenance_flag_on_packet(self):
        assembled = _mixed_assembled()
        items = selected_admitted_items(assembled)
        packet = build_audit_evidence_sidecar_from_items("stub", items)
        for bad in ("same_turn_verified", "verified", "provenance", "truth", "authority"):
            self.assertNotIn(bad, packet)


class TestNegative(unittest.TestCase):

    def test_harness_refuses_when_item_absent_from_captured_context(self):
        assembled = _mixed_assembled()
        items = selected_admitted_items(assembled)
        boundary = _FakeLLMBoundary()
        # Owner did NOT render the memory material into the model-visible context.
        sp, msgs = _render_candidate_model_visible_context(
            assembled.assembled_text, "what is the plan?", include_memory=False,
        )
        boundary.complete(system_prompt=sp, messages=msgs)
        captured = boundary.captured_model_visible_text
        with self.assertRaises(_PromptInclusionError):
            _require_inclusion_or_refuse(items, captured)

    def test_passing_items_without_rendering_is_insufficient(self):
        # A packet can be composed (co-location), but inclusion is NOT proven
        # because the items were never rendered into the captured context.
        assembled = _mixed_assembled()
        items = selected_admitted_items(assembled)
        boundary = _FakeLLMBoundary()
        sp, msgs = _render_candidate_model_visible_context(
            assembled.assembled_text, "q", include_memory=False,
        )
        boundary.complete(system_prompt=sp, messages=msgs)
        captured = boundary.captured_model_visible_text
        _ = build_audit_evidence_sidecar_from_items("stub", items)   # co-location only
        self.assertFalse(_selected_item_texts_in_context(items, captured))

    def test_budget_skipped_candidates_absent_from_selected_admitted_items(self):
        kept = _core_hit(1, "ZZKEPT small relational", tier="relational")
        big = _core_hit(2, "ZZSKIPPED " + ("filler " * 120), half_life=1.0)
        a = assemble_context(core_hits=[kept, big], token_budget=80, profile="balanced")
        eids = {it.get("eid") for it in selected_admitted_items(a)}
        self.assertIn(1, eids)
        self.assertNotIn(2, eids)

    def test_packet_excluded_identity_not_admitted_even_if_in_prompt_material(self):
        assembled = _mixed_assembled()
        items = selected_admitted_items(assembled)
        boundary = _FakeLLMBoundary()
        sp, msgs = _render_candidate_model_visible_context(
            assembled.assembled_text, "q", include_memory=True,
        )
        boundary.complete(system_prompt=sp, messages=msgs)
        captured = boundary.captured_model_visible_text
        # Identity/canon material is in the candidate prompt material...
        self.assertIn(_CANON, captured)
        # ...but is NOT admitted as packet evidence (audit boundary, not prompt rule).
        packet = build_audit_evidence_sidecar_from_items("stub", items)
        joined = " ".join(e.get("snippet", "") for e in packet["evidence_items"])
        self.assertIn("ZZORD", joined)
        self.assertNotIn("ZZCANON", joined)


class TestHarnessIntroducesNoForbiddenSurface(unittest.TestCase):
    """AST self-scan: the harness references no AgentRunner / run_turn / app /
    endpoint / provenance-flag surface."""

    _FORBIDDEN = {
        "AgentRunner", "run_turn", "app",
        "same_turn_verified", "verified_same_turn", "provenance_verified",
        "truth_verified", "authority_verified",
    }

    def test_no_forbidden_references(self):
        with open(os.path.abspath(__file__), "rb") as fh:
            tree = ast.parse(fh.read().replace(b"\x00", b""))
        idents = set()
        import_leaves = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Name):
                idents.add(n.id)
            elif isinstance(n, ast.Attribute):
                idents.add(n.attr)
            elif isinstance(n, ast.Import):
                for x in n.names:
                    import_leaves.add(x.name.split(".")[-1])
            elif isinstance(n, ast.ImportFrom):
                if n.module:
                    import_leaves.add(n.module.split(".")[-1])
        self.assertEqual(idents & self._FORBIDDEN, set(),
                         msg=f"harness references forbidden surface: {sorted(idents & self._FORBIDDEN)}")
        for bad in ("app", "agent_loop"):
            self.assertNotIn(bad, import_leaves, msg=f"harness imports {bad}")


if __name__ == "__main__":
    unittest.main()
