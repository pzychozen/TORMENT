"""Characterization: the assembler same-turn prompt-context invariant.

SCOPE (read carefully — this proves an assembler invariant, NOT live response
generation):
    * It proves that ``retrieval_assembler.assemble_context(...)`` builds
      ``assembled_text`` *exactly* from its selected blocks — every selected
      block's text is in the assembler prompt context, and the assembler prompt
      context carries no block evidence beyond the selected blocks (only section
      headers / blank lines are added).
    * It proves that ``audit_evidence_context.selected_admitted_items(...)``
      extracts those same selected block dicts from a real ``AssembledContext``.

    Together these establish the **assembler same-turn prompt-context invariant**:
    the evidence an audit packet would draw from the selected blocks is exactly
    the evidence composed into the assembler prompt context for that turn — not
    raw hits, not fresh retrieval, not re-filtered / audit-expanded context.

    This is explicitly **not** a proof that any live model response was generated
    against that context. The response-generation / output-sink link is a
    separate, still-parked gate. There is **no production wiring** here: this file
    only calls the pure ``assemble_context`` builder and the pure
    ``selected_admitted_items`` extractor, plus an optional read-only AST
    inspection of the ``/retrieve`` handler source.

It adds no production code, no audit packet builder change, no evaluator, no
model / provider / prompt, no endpoint, no persistence, no database / substrate,
no dream / private cognition, no Gate D / Envelope Audit.
"""

import ast
import os
import unittest

from torment_service import retrieval_assembler as ra
from torment_service.audit_evidence_context import selected_admitted_items


# Section headers literally emitted by assemble_context Step 6. Removing these is
# the only "assembler formatting" normalization allowed by this characterization.
_SECTION_HEADERS = (
    "[Identity Context]",
    "[Relational Context]",
    "[Situational Context]",
    "[Archive Context]",
    "[{}]".format(ra.BLOCK_REFERENCE),  # reference uses the f"[{bt}]" fallback
)


def _core_hit(eid, text, *, tier="", half_life=30.0, mtype="memory", canon=False):
    """A minimal core hit dict accepted by assemble_context / _hit_to_block.

    ``final_score`` is set so the block sorts with a positive score. For
    non-spirit hits ``_hit_to_block`` leaves the text verbatim, so ``text`` is
    exactly the block text that flows into the assembler prompt context.
    """
    return {
        "eid": eid,
        "text": text,
        "type": mtype,
        "character_tier": tier,
        "half_life": half_life,
        "canon": canon,
        "final_score": 1.0,
    }


class TestSelectedBlocksTextPresentInAssembledText(unittest.TestCase):
    """Every selected block's text appears in the assembler prompt context."""

    def test_selected_blocks_text_present_in_assembled_text(self):
        hits = [
            _core_hit(1, "ZZRELONE unique relational evidence alpha", tier="relational"),
            _core_hit(2, "ZZSITTWO unique situational evidence beta", half_life=1.0),
            _core_hit(3, "ZZIDNTHREE unique identity evidence gamma", canon=True),
        ]
        assembled = ra.assemble_context(core_hits=hits, token_budget=4000)

        items = selected_admitted_items(assembled)
        self.assertTrue(items, "expected at least one selected block")
        for item in items:
            self.assertIn(
                item["text"], assembled.assembled_text,
                msg=f"selected block text missing from assembler prompt context: {item['text']!r}",
            )


class TestNoEvidenceBeyondSelectedBlocks(unittest.TestCase):
    """The assembler prompt context contains no block evidence beyond the
    selected blocks (only section headers / blank lines are added)."""

    def test_assembled_text_has_no_evidence_beyond_selected_blocks(self):
        hits = [
            _core_hit(1, "ZZALPHA relational evidence words", tier="relational"),
            _core_hit(2, "ZZBETA situational evidence words", half_life=1.0),
        ]
        assembled = ra.assemble_context(core_hits=hits, token_budget=4000)

        # Normalize ONLY assembler formatting: strip section headers, then remove
        # each selected block's verbatim text. What remains must carry no further
        # evidence — i.e. no alphabetic content, only whitespace / blank lines.
        remainder = assembled.assembled_text
        for header in _SECTION_HEADERS:
            remainder = remainder.replace(header, "")
        for item in selected_admitted_items(assembled):
            remainder = remainder.replace(item["text"], "", 1)

        leftover_alpha = [ch for ch in remainder if ch.isalpha()]
        self.assertEqual(
            leftover_alpha, [],
            msg=(
                "assembler prompt context carried evidence beyond the selected "
                f"blocks (residual after header/block removal): {remainder!r}"
            ),
        )


class TestBudgetSkippedCandidateAbsent(unittest.TestCase):
    """A candidate skipped by the assembler budget is in neither the assembler
    prompt context nor the extractor output."""

    def test_budget_skipped_candidate_absent_from_prompt_and_extractor(self):
        kept = _core_hit(1, "ZZKEPT small relational evidence", tier="relational")
        # A large situational candidate (~160 tokens) that exceeds the global
        # token budget after the small relational block is placed, so the
        # assembler records it as skipped rather than selected.
        big_text = "ZZSKIPPED " + ("filler " * 120)
        skipped = _core_hit(2, big_text, half_life=1.0)

        assembled = ra.assemble_context(
            core_hits=[kept, skipped], token_budget=80, profile="balanced",
        )

        # Sanity: the assembler actually skipped eid 2 (did not select it).
        selected_log_eids = {
            e.get("eid")
            for e in assembled.selection_log
            if e.get("action") == "selected"
        }
        self.assertIn(1, selected_log_eids)
        self.assertNotIn(2, selected_log_eids)

        # The skipped sentinel is absent from the assembler prompt context.
        self.assertIn("ZZKEPT", assembled.assembled_text)
        self.assertNotIn("ZZSKIPPED", assembled.assembled_text)

        # The skipped candidate is absent from the extractor output.
        items = selected_admitted_items(assembled)
        extracted_eids = {it.get("eid") for it in items}
        self.assertIn(1, extracted_eids)
        self.assertNotIn(2, extracted_eids)
        for it in items:
            self.assertNotIn("ZZSKIPPED", it.get("text", ""))


class TestExtractorJoinsAgainstRealAssembleContextOutput(unittest.TestCase):
    """selected_admitted_items works against a real AssembledContext object
    (not only hand-built dicts), joining by (block_type, eid, chunk_id)."""

    def test_extractor_joins_against_real_assemble_context_output(self):
        hits = [
            _core_hit(11, "ZZJOINREL relational join evidence", tier="relational"),
            _core_hit(12, "ZZJOINIDN identity join evidence", canon=True),
        ]
        assembled = ra.assemble_context(core_hits=hits, token_budget=4000)

        # Keys the assembler marked selected, by (block_type, eid, chunk_id).
        selected_keys = {
            (e.get("block_type"), e.get("eid"), e.get("chunk_id"))
            for e in assembled.selection_log
            if e.get("action") == "selected"
        }
        self.assertTrue(selected_keys, "expected the assembler to select blocks")

        # Pass the real AssembledContext OBJECT (duck-typed), not a dict.
        items = selected_admitted_items(assembled)
        self.assertTrue(items)
        got_keys = {
            (it.get("block_type"), it.get("eid"), it.get("chunk_id"))
            for it in items
        }
        self.assertEqual(got_keys, selected_keys)
        # Returned values are the selected block dicts.
        for it in items:
            self.assertIsInstance(it, dict)
            self.assertIn("text", it)
            self.assertIn(it.get("block_type"), {
                ra.BLOCK_IDENTITY, ra.BLOCK_REFERENCE, ra.BLOCK_RELATIONAL,
                ra.BLOCK_SITUATIONAL, ra.BLOCK_ARCHIVE,
            })


class TestRetrievePathMakesNoModelCall(unittest.TestCase):
    """Negative overclaim guard (read-only AST, narrowly scoped to the
    ``retrieve_assembled`` handler): ``/retrieve`` performs retrieval + assembly
    and returns the assembler prompt context — it does not perform live model
    response generation. This does NOT execute the handler or any server/client
    wiring; it only inspects the handler's source."""

    GENERATION_CALL_NAMES = {
        "generate", "complete", "completion", "completions",
        "chat", "chat_completion", "create_completion",
        "create_chat_completion", "predict", "infer",
    }

    def _retrieve_handler_node(self):
        app_py = os.path.join(
            os.path.dirname(os.path.abspath(ra.__file__)), "app.py"
        )
        with open(app_py, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "retrieve_assembled":
                return node
        return None

    def _call_names(self, func_node):
        names = set()
        for n in ast.walk(func_node):
            if isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Name):
                    names.add(f.id)
                elif isinstance(f, ast.Attribute):
                    names.add(f.attr)
        return names

    def test_retrieve_path_makes_no_model_call(self):
        node = self._retrieve_handler_node()
        self.assertIsNotNone(node, "retrieve_assembled handler not found in app.py")
        names = self._call_names(node)
        # Positive: the handler does assembly.
        self.assertIn(
            "assemble_context", names,
            msg="retrieve_assembled should call assemble_context (assembly, not generation)",
        )
        # Negative: no generation-style call appears in the handler.
        offenders = names & self.GENERATION_CALL_NAMES
        self.assertEqual(
            offenders, set(),
            msg=f"retrieve_assembled appears to call generation: {sorted(offenders)}",
        )


if __name__ == "__main__":
    unittest.main()
