"""Tests for the pure AssembledContext selected-item source extractor.

Source extraction (this helper) and packet filtering (the packet builder) are
SEPARATE stages. This helper returns the assembler-SELECTED block dicts as
candidate admitted_context_items; it makes no admissibility claim. The packet
builder applies its own sensitivity exclusions downstream.

Called nowhere in production. No retrieval, no assembler call, no fabric.query,
no assembled_text parsing.
"""

import ast
import os
import unittest

from torment_service.audit_evidence_context import selected_admitted_items


def _torment_service_dir():
    here = os.path.dirname(os.path.abspath(__file__))            # tests/
    return os.path.join(os.path.dirname(here), "torment_service")


def _ctx(blocks, selection_log, assembled_text=None):
    """An AssembledContext-LIKE dict (mirrors retrieval_assembler shape)."""
    d = {"blocks": blocks, "selection_log": selection_log}
    if assembled_text is not None:
        d["assembled_text"] = assembled_text
    return d


def _sel(block_type, eid=None, chunk_id=None, action="selected"):
    return {"block_type": block_type, "eid": eid, "chunk_id": chunk_id, "action": action}


def _block(block_type, eid=None, chunk_id=None, **extra):
    d = {"block_type": block_type, "eid": eid, "chunk_id": chunk_id, "text": "t"}
    d.update(extra)
    return d


class TestSelectionJoin(unittest.TestCase):

    def test_selected_entries_included(self):
        ctx = _ctx(
            blocks={"relational": [_block("relational", eid=2)]},
            selection_log=[_sel("relational", eid=2, action="selected")],
        )
        out = selected_admitted_items(ctx)
        self.assertEqual([e.get("eid") for e in out], [2])

    def test_skipped_entries_excluded(self):
        # eid 2 sits in blocks but selection_log marks it skipped → excluded.
        ctx = _ctx(
            blocks={
                "relational": [_block("relational", eid=1), _block("relational", eid=2)],
            },
            selection_log=[
                _sel("relational", eid=1, action="selected"),
                _sel("relational", eid=2, action="skipped_budget_exhausted"),
            ],
        )
        out = selected_admitted_items(ctx)
        self.assertEqual({e.get("eid") for e in out}, {1})

    def test_join_only_against_blocks_not_raw_candidates(self):
        # A selected key with NO matching block dict yields nothing — we never
        # fabricate an item from selection_log alone.
        ctx = _ctx(
            blocks={"relational": [_block("relational", eid=1)]},
            selection_log=[
                _sel("relational", eid=1, action="selected"),
                _sel("relational", eid=99, action="selected"),  # not in blocks
            ],
        )
        out = selected_admitted_items(ctx)
        self.assertEqual({e.get("eid") for e in out}, {1})

    def test_archive_chunk_id_match(self):
        ctx = _ctx(
            blocks={"archive": [_block("archive", chunk_id="c1")]},
            selection_log=[_sel("archive", chunk_id="c1", action="selected")],
        )
        out = selected_admitted_items(ctx)
        self.assertEqual([e.get("chunk_id") for e in out], ["c1"])

    def test_accepts_duck_typed_object(self):
        class _Obj:
            blocks = {"relational": [_block("relational", eid=7)]}
            selection_log = [_sel("relational", eid=7, action="selected")]
        out = selected_admitted_items(_Obj())
        self.assertEqual([e.get("eid") for e in out], [7])

    def test_empty_or_missing_yields_empty(self):
        self.assertEqual(selected_admitted_items({}), [])
        self.assertEqual(selected_admitted_items({"blocks": {}, "selection_log": []}), [])


class TestIdentitySourceSelectedNoAdmissibilityClaim(unittest.TestCase):

    def test_selected_identity_block_is_source_selected_only(self):
        # An identity block the assembler selected IS returned here (source-
        # selection). This makes NO claim that it is packet-admissible; the
        # packet builder is a separate downstream stage.
        ctx = _ctx(
            blocks={"identity": [_block("identity", eid=5, metadata={"canon": True})]},
            selection_log=[_sel("identity", eid=5, action="selected")],
        )
        out = selected_admitted_items(ctx)
        self.assertEqual([e.get("eid") for e in out], [5])
        # Note: markers live in `metadata`, not top level — see helper docstring.


class TestAssembledTextNotUsed(unittest.TestCase):

    def test_assembled_text_is_not_parsed_or_required(self):
        # Misleading assembled_text mentioning a non-selected id must not change
        # the result; absence of assembled_text must not break extraction.
        ctx = _ctx(
            blocks={"relational": [_block("relational", eid=1)]},
            selection_log=[_sel("relational", eid=1, action="selected")],
            assembled_text="[Relational Context]\nmentions eid 2 and eid 99 too",
        )
        out = selected_admitted_items(ctx)
        self.assertEqual({e.get("eid") for e in out}, {1})
        # And with no assembled_text key at all:
        ctx2 = _ctx(
            blocks={"relational": [_block("relational", eid=1)]},
            selection_log=[_sel("relational", eid=1, action="selected")],
        )
        self.assertEqual({e.get("eid") for e in selected_admitted_items(ctx2)}, {1})


class TestSourceGuards(unittest.TestCase):
    """AST/source guards. The import allowlist is airtight: importing only
    ``typing`` / ``__future__`` means the helper cannot reach fabric / retrieval /
    assembler / query / writer / persistence / endpoint at all (no import = no
    call). A separate guard proves no production caller.
    (A substring scan is intentionally NOT used — the helper docstring honestly
    names ``fabric`` / ``retrieval_assembler`` to say it does not use them.)"""

    HELPER = os.path.join(_torment_service_dir(), "audit_evidence_context.py")
    ALLOWED_IMPORT_LEAVES = {"__future__", "typing"}

    def _src(self):
        with open(self.HELPER, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_imports_only_allowlisted_modules(self):
        tree = ast.parse(self._src())
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
            msg=f"unexpected imports: {sorted(leaves)}",
        )

    def test_only_sanctioned_modules_reference_the_helper(self):
        # Historical fact: before the approved bridge (ec17d2e) the pure-composition
        # sidecar was the ONLY permitted internal caller of selected_admitted_items,
        # and it is itself called nowhere (proven in tests/test_audit_evidence_sidecar.py).
        # New invariant: selected_admitted_items / audit_evidence_context may be
        # referenced ONLY by sanctioned, observation-only modules:
        #   * audit_evidence_sidecar.py            — pure packet composition, called nowhere
        #   * audit_selected_items_runner_bridge.py — the approved private selected-items
        #     runner bridge: the single bridge that feeds the observation-only audit
        #     seam, itself called nowhere else.
        # No live production surface (endpoint / AgentRunner self-call / /retrieve /
        # model / writer / persistence) may reference it.
        svc_dir = _torment_service_dir()
        sanctioned = {
            "audit_evidence_context.py",
            "audit_evidence_sidecar.py",
            "audit_selected_items_runner_bridge.py",
        }
        offenders = []
        for fn in os.listdir(svc_dir):
            if not fn.endswith(".py") or fn in sanctioned:
                continue
            with open(os.path.join(svc_dir, fn), "r", encoding="utf-8") as fh:
                content = fh.read()
            if "audit_evidence_context" in content or "selected_admitted_items" in content:
                offenders.append(fn)
        self.assertEqual(offenders, [],
                         msg=f"referenced by non-sanctioned production: {offenders}")


class TestPacketBuilderCompatibilitySeparateStages(unittest.TestCase):
    """Optional: extracted selected items can feed the packet builder, and the
    two stages stay separate. The builder's marker filter applies ONLY to markers
    present at the TOP LEVEL of an item — real ContextBlock dicts keep markers in
    `metadata`, so the wiring stage must lift them. This test uses top-level
    markers to demonstrate the builder stage works when they are present."""

    def test_extraction_then_packet_build_filters_top_level_markers(self):
        from torment_service.audit_evidence_packet import build_audit_evidence_packet

        ctx = _ctx(
            blocks={
                "relational": [
                    _block("relational", eid=1, scope="shared", summary="ordinary fact"),
                    _block("relational", eid=2, scope="private", summary="private note"),
                ],
            },
            selection_log=[
                _sel("relational", eid=1, action="selected"),
                _sel("relational", eid=2, action="selected"),
            ],
        )
        items = selected_admitted_items(ctx)
        self.assertEqual({e.get("eid") for e in items}, {1, 2})  # both source-selected

        packet = build_audit_evidence_packet("resp", items)
        kept_eids = {e.get("eid") for e in packet["evidence_items"]}
        # Stage 2 (packet builder) drops the top-level scope=="private" item.
        self.assertIn(1, kept_eids)
        self.assertNotIn(2, kept_eids)

    def test_selected_seed_block_excluded_by_builder_metadata_read(self):
        # A seed block as retrieval_assembler._build_seed_block emits it:
        # identity block_type, eid/chunk_id None, marker in metadata={"is_seed": True}.
        # Stage 1 (extractor) returns it (source-selection, no admissibility claim);
        # Stage 2 (builder) now reads the metadata marker and excludes it.
        from torment_service.audit_evidence_packet import build_audit_evidence_packet

        ctx = _ctx(
            blocks={
                "identity": [
                    _block("identity", eid=None, chunk_id=None,
                           metadata={"is_seed": True}, summary="seed identity text"),
                ],
                "relational": [
                    _block("relational", eid=1, summary="ordinary shared fact"),
                ],
            },
            selection_log=[
                _sel("identity", eid=None, chunk_id=None, action="selected"),
                _sel("relational", eid=1, action="selected"),
            ],
        )
        items = selected_admitted_items(ctx)
        # Stage 1: both source-selected; the seed block carries its metadata marker.
        self.assertEqual(len(items), 2)
        self.assertTrue(
            any(i.get("metadata", {}).get("is_seed") is True for i in items)
        )

        # Stage 2: builder drops the seed block, keeps the ordinary fact.
        packet = build_audit_evidence_packet("resp", items)
        kept = packet["evidence_items"]
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].get("snippet"), "ordinary shared fact")

    def test_marker_invisible_identity_context_dropped_by_block_type(self):
        # §4A end-to-end: a selected identity hit that is marker-invisible after
        # assembly (no is_seed; type=="seed_canon" not in the lifecycle set;
        # half_life not a marker) is returned by the extractor (stage 1) but
        # dropped by the builder (stage 2) via its post-assembler block_type.
        from torment_service.audit_evidence_packet import build_audit_evidence_packet

        ctx = _ctx(
            blocks={
                "identity_context": [
                    _block("identity_context", eid=7,
                           metadata={"type": "seed_canon", "half_life": 400.0},
                           summary="canon-ish identity text"),
                ],
                "relational_context": [
                    _block("relational_context", eid=1, summary="ordinary fact"),
                ],
            },
            selection_log=[
                _sel("identity_context", eid=7, action="selected"),
                _sel("relational_context", eid=1, action="selected"),
            ],
        )
        items = selected_admitted_items(ctx)
        # Stage 1: both source-selected; the identity item carries NO surviving marker.
        self.assertEqual({e.get("eid") for e in items}, {1, 7})
        identity_item = next(e for e in items if e.get("eid") == 7)
        self.assertNotIn("is_seed", identity_item)
        self.assertNotIn("is_seed", identity_item.get("metadata", {}))

        # Stage 2: builder drops the identity_context item, keeps the relational fact.
        packet = build_audit_evidence_packet("resp", items)
        self.assertEqual({e.get("eid") for e in packet["evidence_items"]}, {1})


if __name__ == "__main__":
    unittest.main()
