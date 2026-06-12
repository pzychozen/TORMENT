"""
tests/test_assembly_audit.py — build_assembly_audit helper unit tests.

Direct unit tests on torment_service.assembly_audit.build_assembly_audit
per docs/MEMORY_TO_PROMPT_AUTOMATION_v0.2.md §4 and Slice S4 plan §2.

unittest.TestCase classes, pytest-runnable. Fixtures hand-constructed
per S4 Trio decision 3 (isolation; no real fabric/character setup).

The helper is tested in isolation. No FILTER-A call, no /retrieve
call, no LLM call, no I/O. End-to-end coverage (operator-run live
verification) lives in Slice S6.
"""
from __future__ import annotations

import builtins
import copy
import inspect
import os
import sys
import unittest
from typing import Any, Dict, List
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.assembly_audit import (
    build_assembly_audit,
    _classification_basis,
    _spirit_return_summary,
    _tool_result_summary,
    _request_record,
    _embedder_snapshot,
    _character_summary,
)
from torment_service.governance import SURFACE_LLM_CONTEXT
from torment_service.retrieval_assembler import (
    AssembledContext,
    BLOCK_IDENTITY,
    BLOCK_REFERENCE,
    BLOCK_RELATIONAL,
    BLOCK_SITUATIONAL,
    BLOCK_ARCHIVE,
)


# ---------------------------------------------------------------------------
# Fixture builders (hand-constructed per S4 Trio decision 3)
# ---------------------------------------------------------------------------

def _minimal_request_meta() -> Dict[str, Any]:
    return {
        "workspace_id": "ws1",
        "agent_id": "ag1",
        "query": "hello",
        "profile": "companion",
        "top_k": 6,
        "token_budget": 2000,
    }


def _empty_core_query_result() -> Dict[str, Any]:
    return {
        "results": [],
        "character_context": None,
        "embed_context": None,
        "filter_excluded": [],
    }


def _empty_blocks() -> Dict[str, List[Dict[str, Any]]]:
    return {
        BLOCK_IDENTITY: [],
        BLOCK_REFERENCE: [],
        BLOCK_RELATIONAL: [],
        BLOCK_SITUATIONAL: [],
        BLOCK_ARCHIVE: [],
    }


def _empty_assembled() -> AssembledContext:
    return AssembledContext(
        profile="companion",
        token_budget=2000,
        tokens_used=0,
        blocks=_empty_blocks(),
        assembled_text="",
        block_token_counts={k: 0 for k in _empty_blocks().keys()},
        selection_log=[],
    )


def _block(
    *,
    eid=None,
    chunk_id=None,
    block_type=BLOCK_RELATIONAL,
    score=0.5,
    token_count=5,
    metadata: Dict[str, Any] = None,
    text: str = "text",
    source: str = "core",
) -> Dict[str, Any]:
    """Hand-construct a block dict (post-asdict shape)."""
    return {
        "block_type": block_type,
        "eid": eid,
        "chunk_id": chunk_id,
        "text": text,
        "token_count": token_count,
        "score": score,
        "reason": "test reason",
        "source": source,
        "metadata": dict(metadata) if metadata else {},
    }


def _select_log(
    *,
    block_type: str,
    eid=None,
    chunk_id=None,
    action: str = "selected",
    score: float = 0.5,
    token_count: int = 5,
    reason: str = "test reason",
) -> Dict[str, Any]:
    """Hand-construct a selection_log entry."""
    entry: Dict[str, Any] = {
        "block_type": block_type,
        "eid": eid,
        "chunk_id": chunk_id,
        "action": action,
        "reason": reason,
    }
    if action == "selected":
        entry["score"] = score
        entry["token_count"] = token_count
    return entry


def _minimal_kwargs() -> Dict[str, Any]:
    return {
        "request_meta": _minimal_request_meta(),
        "core_query_result": _empty_core_query_result(),
        "archive_hits": [],
        "assembled": _empty_assembled(),
    }


# ---------------------------------------------------------------------------
# 1. HelperContract — required kwargs, return type, version constant
# ---------------------------------------------------------------------------

class TestBuildAssemblyAudit_HelperContract(unittest.TestCase):
    def test_returns_dict(self):
        out = build_assembly_audit(**_minimal_kwargs())
        self.assertIsInstance(out, dict)

    def test_requires_kwargs_only(self):
        # Positional call must fail.
        with self.assertRaises(TypeError):
            build_assembly_audit(
                _minimal_request_meta(),  # type: ignore[misc]
                _empty_core_query_result(),
                [],
                _empty_assembled(),
            )

    def test_lane_version_is_v0_2(self):
        out = build_assembly_audit(**_minimal_kwargs())
        self.assertEqual(
            out["lane_version"], "memory_to_prompt_observability_v0.2"
        )

    def test_timestamp_is_int_seconds(self):
        out = build_assembly_audit(**_minimal_kwargs())
        self.assertIsInstance(out["timestamp"], int)
        # Plausible-recent epoch second (since 2020-01-01).
        self.assertGreater(out["timestamp"], 1577836800)


# ---------------------------------------------------------------------------
# 2. NoMutation — deepcopy inputs, compare after call
# ---------------------------------------------------------------------------

class TestBuildAssemblyAudit_NoMutation(unittest.TestCase):
    def test_request_meta_not_mutated(self):
        rm = _minimal_request_meta()
        rm_copy = copy.deepcopy(rm)
        build_assembly_audit(
            request_meta=rm,
            core_query_result=_empty_core_query_result(),
            archive_hits=[],
            assembled=_empty_assembled(),
        )
        self.assertEqual(rm, rm_copy)

    def test_core_query_result_not_mutated(self):
        cqr = _empty_core_query_result()
        cqr["filter_excluded"] = [{"eid": 7, "excluded_reason": "non_shareable"}]
        cqr_copy = copy.deepcopy(cqr)
        out = build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=cqr,
            archive_hits=[],
            assembled=_empty_assembled(),
        )
        # Even after we mutate the audit return, original must be unchanged.
        out["filter_a"]["excluded"].clear()
        self.assertEqual(cqr, cqr_copy)

    def test_archive_hits_list_not_mutated(self):
        ah = [{"chunk_id": "c1", "score": 0.5}]
        ah_copy = copy.deepcopy(ah)
        build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=_empty_core_query_result(),
            archive_hits=ah,
            assembled=_empty_assembled(),
        )
        self.assertEqual(ah, ah_copy)

    def test_assembled_blocks_not_mutated(self):
        asm = _empty_assembled()
        asm.blocks[BLOCK_IDENTITY].append(
            _block(eid=1, block_type=BLOCK_IDENTITY,
                   metadata={"type": "seed_canon", "canon": True})
        )
        snap = copy.deepcopy(asm.blocks)
        build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=_empty_core_query_result(),
            archive_hits=[],
            assembled=asm,
        )
        self.assertEqual(asm.blocks, snap)

    def test_assembled_selection_log_not_mutated(self):
        asm = _empty_assembled()
        asm.selection_log.append(
            _select_log(block_type=BLOCK_IDENTITY, eid=1, action="selected")
        )
        asm.blocks[BLOCK_IDENTITY].append(
            _block(eid=1, block_type=BLOCK_IDENTITY,
                   metadata={"type": "seed_canon", "canon": True})
        )
        snap = copy.deepcopy(asm.selection_log)
        build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=_empty_core_query_result(),
            archive_hits=[],
            assembled=asm,
        )
        self.assertEqual(asm.selection_log, snap)


# ---------------------------------------------------------------------------
# 3. NoIO — no file / network / fsync; module-level import audit
# ---------------------------------------------------------------------------

class TestBuildAssemblyAudit_NoIO(unittest.TestCase):
    def test_helper_does_not_open_files(self):
        def _no_open(*a, **kw):
            raise AssertionError("build_assembly_audit must not open files")
        with patch.object(builtins, "open", side_effect=_no_open):
            out = build_assembly_audit(**_minimal_kwargs())
            self.assertIsInstance(out, dict)

    def test_helper_does_not_call_os_fsync(self):
        def _no_fsync(*a, **kw):
            raise AssertionError("build_assembly_audit must not call fsync")
        with patch("os.fsync", side_effect=_no_fsync, create=True):
            out = build_assembly_audit(**_minimal_kwargs())
            self.assertIsInstance(out, dict)

    def test_helper_does_not_create_sockets(self):
        import socket
        def _no_socket(*a, **kw):
            raise AssertionError("build_assembly_audit must not open sockets")
        with patch.object(socket, "socket", side_effect=_no_socket):
            out = build_assembly_audit(**_minimal_kwargs())
            self.assertIsInstance(out, dict)

    def test_helper_does_not_write_files_via_pathlib(self):
        import pathlib
        def _no_write_text(self, *a, **kw):
            raise AssertionError(
                "build_assembly_audit must not write files via pathlib"
            )
        with patch.object(pathlib.Path, "write_text", _no_write_text):
            out = build_assembly_audit(**_minimal_kwargs())
            self.assertIsInstance(out, dict)

    def test_helper_does_not_write_bytes_via_pathlib(self):
        import pathlib
        def _no_write_bytes(self, *a, **kw):
            raise AssertionError(
                "build_assembly_audit must not write bytes via pathlib"
            )
        with patch.object(pathlib.Path, "write_bytes", _no_write_bytes):
            out = build_assembly_audit(**_minimal_kwargs())
            self.assertIsInstance(out, dict)

    def test_module_source_does_not_import_io_libs(self):
        """Static check: assembly_audit.py must not import IO-actuating
        libraries. `import os` is allowed (for utility access) but
        specific IO-actuating symbols must not appear.
        """
        import torment_service.assembly_audit as mod
        src = inspect.getsource(mod)
        forbidden_substrings = [
            "import requests",
            "import socket",
            "from socket",
            "import pathlib",
            "from pathlib",
            "urllib.",
            "open(",          # any open(...) call
            ".write_text",
            ".write_bytes",
            "os.fsync",
        ]
        for token in forbidden_substrings:
            self.assertNotIn(
                token, src,
                f"forbidden token {token!r} found in assembly_audit.py",
            )


# ---------------------------------------------------------------------------
# 4. Pure — repeatable; timestamp is the only differ
# ---------------------------------------------------------------------------

class TestBuildAssemblyAudit_Pure(unittest.TestCase):
    def test_two_calls_match_modulo_timestamp(self):
        r1 = build_assembly_audit(**_minimal_kwargs())
        r2 = build_assembly_audit(**_minimal_kwargs())
        r1.pop("timestamp")
        r2.pop("timestamp")
        self.assertEqual(r1, r2)

    def test_timestamp_monotonic_across_calls(self):
        # Even back-to-back, timestamps should not go backwards.
        r1 = build_assembly_audit(**_minimal_kwargs())
        r2 = build_assembly_audit(**_minimal_kwargs())
        self.assertGreaterEqual(r2["timestamp"], r1["timestamp"])


# ---------------------------------------------------------------------------
# 5. GracefulDefaults — missing optional fields handled
# ---------------------------------------------------------------------------

class TestBuildAssemblyAudit_GracefulDefaults(unittest.TestCase):
    def test_empty_request_meta(self):
        out = build_assembly_audit(
            request_meta={},
            core_query_result=_empty_core_query_result(),
            archive_hits=[],
            assembled=_empty_assembled(),
        )
        req = out["request"]
        self.assertEqual(req["workspace_id"], "")
        self.assertEqual(req["agent_id"], "")
        self.assertEqual(req["top_k"], 0)
        self.assertEqual(req["token_budget"], 0)
        self.assertEqual(req["surface"], SURFACE_LLM_CONTEXT)

    def test_missing_character_context(self):
        out = build_assembly_audit(**_minimal_kwargs())
        char = out["character"]
        self.assertEqual(char["character_name"], "")
        self.assertEqual(char["seed_basin_role"], "")
        self.assertEqual(char["drift_score"], 0.0)
        self.assertEqual(char["drift_direction"], "")
        self.assertEqual(char["relational_count"], 0)

    def test_missing_embed_context(self):
        out = build_assembly_audit(**_minimal_kwargs())
        emb = out["embedder"]
        self.assertEqual(emb["provider"], "")
        self.assertEqual(emb["model"], "")
        self.assertEqual(emb["dim"], 0)

    def test_assembled_dict_accepted_in_place_of_dataclass(self):
        # Per Trio decision 3: graceful handling for both shapes.
        assembled_as_dict = {
            "profile": "companion",
            "token_budget": 2000,
            "tokens_used": 0,
            "blocks": _empty_blocks(),
            "assembled_text": "",
            "block_token_counts": {k: 0 for k in _empty_blocks().keys()},
            "selection_log": [],
        }
        out = build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=_empty_core_query_result(),
            archive_hits=[],
            assembled=assembled_as_dict,
        )
        self.assertEqual(out["assembly"]["profile_used"], "companion")


# ---------------------------------------------------------------------------
# 6. FilterARecord — exclusions propagation, archive_filter_applied=false
# ---------------------------------------------------------------------------

class TestBuildAssemblyAudit_FilterARecord(unittest.TestCase):
    # -------- legacy path: archive_filter_excluded omitted --------
    # The original v0.2 first-revision contract: archive_filter_applied
    # reports False and archive_excluded is absent from filter_a. This
    # preserves backward compat for every caller that has not yet wired
    # the v0.2.4-A1 archive filter (i.e., test fixtures and any code
    # that builds an audit without going through the /retrieve handler).
    def test_archive_filter_applied_is_false_when_param_omitted(self):
        out = build_assembly_audit(**_minimal_kwargs())
        self.assertFalse(out["filter_a"]["archive_filter_applied"])

    def test_archive_excluded_absent_when_param_omitted(self):
        out = build_assembly_audit(**_minimal_kwargs())
        self.assertNotIn("archive_excluded", out["filter_a"])

    # -------- v0.2.4-A1 path: archive_filter_excluded is a list --------
    # Presence of the param (even an empty list) is the signal that the
    # upstream archive FILTER-A ran. archive_filter_applied flips to True
    # and archive_excluded surfaces as a defensively-copied list.
    def test_archive_filter_applied_is_true_when_empty_list_passed(self):
        out = build_assembly_audit(
            **_minimal_kwargs(),
            archive_filter_excluded=[],
        )
        self.assertTrue(out["filter_a"]["archive_filter_applied"])

    def test_archive_filter_applied_is_true_when_nonempty_list_passed(self):
        out = build_assembly_audit(
            **_minimal_kwargs(),
            archive_filter_excluded=[
                {
                    "chunk_id": "ch_1",
                    "doc_id": "doc_a",
                    "excluded_reason": "non_shareable",
                },
            ],
        )
        self.assertTrue(out["filter_a"]["archive_filter_applied"])

    def test_archive_excluded_present_as_empty_list_when_empty_list_passed(self):
        out = build_assembly_audit(
            **_minimal_kwargs(),
            archive_filter_excluded=[],
        )
        self.assertIn("archive_excluded", out["filter_a"])
        self.assertEqual(out["filter_a"]["archive_excluded"], [])

    def test_archive_excluded_propagates_records(self):
        excl = [
            {
                "chunk_id": "ch_1",
                "doc_id": "doc_a",
                "excluded_reason": "non_shareable",
            },
            {
                "chunk_id": "ch_2",
                "doc_id": "doc_b",
                "excluded_reason": "non_shareable",
            },
        ]
        out = build_assembly_audit(
            **_minimal_kwargs(),
            archive_filter_excluded=excl,
        )
        self.assertEqual(len(out["filter_a"]["archive_excluded"]), 2)
        self.assertEqual(
            out["filter_a"]["archive_excluded"][0]["chunk_id"],
            "ch_1",
        )

    def test_archive_excluded_record_keys_preserved(self):
        excl = [{
            "chunk_id": "ch_x",
            "doc_id": "doc_x",
            "excluded_reason": "non_shareable",
        }]
        out = build_assembly_audit(
            **_minimal_kwargs(),
            archive_filter_excluded=excl,
        )
        rec = out["filter_a"]["archive_excluded"][0]
        self.assertEqual(rec["chunk_id"], "ch_x")
        self.assertEqual(rec["doc_id"], "doc_x")
        self.assertEqual(rec["excluded_reason"], "non_shareable")

    def test_core_excluded_unaffected_by_archive_filter(self):
        """LOAD-BEARING: archive exclusions must NOT bleed into the core
        ``excluded`` list. Archive hits key on chunk_id; core hits key
        on eid. Mixing would create type confusion downstream. The
        v0.2.4-A1 ratified shape keeps the two surfaces separate.
        """
        cqr = _empty_core_query_result()
        cqr["filter_excluded"] = [
            {"eid": 7, "excluded_reason": "non_shareable"},
        ]
        archive_excl = [
            {
                "chunk_id": "ch_archive",
                "doc_id": "doc_archive",
                "excluded_reason": "non_shareable",
            },
        ]
        out = build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=cqr,
            archive_hits=[],
            assembled=_empty_assembled(),
            archive_filter_excluded=archive_excl,
        )
        # Core excluded carries only the eid-shaped record.
        self.assertEqual(len(out["filter_a"]["excluded"]), 1)
        self.assertEqual(out["filter_a"]["excluded"][0]["eid"], 7)
        self.assertNotIn("chunk_id", out["filter_a"]["excluded"][0])
        # Archive excluded carries only the chunk_id-shaped record.
        self.assertEqual(len(out["filter_a"]["archive_excluded"]), 1)
        self.assertEqual(
            out["filter_a"]["archive_excluded"][0]["chunk_id"],
            "ch_archive",
        )
        self.assertNotIn(
            "eid", out["filter_a"]["archive_excluded"][0]
        )

    def test_archive_filter_excluded_input_mutation_does_not_affect_audit(self):
        """Defensive copy invariant: mutating the input list AND its
        record dicts after build_assembly_audit returns must not affect
        the audit payload. Mirrors the existing filter_excluded copy
        pattern.
        """
        excl_input = [{
            "chunk_id": "ch_orig",
            "doc_id": "doc_orig",
            "excluded_reason": "non_shareable",
        }]
        out = build_assembly_audit(
            **_minimal_kwargs(),
            archive_filter_excluded=excl_input,
        )
        # Mutate the input list (add an element) and the inner dict.
        excl_input.append({
            "chunk_id": "ch_extra",
            "doc_id": "doc_extra",
            "excluded_reason": "non_shareable",
        })
        excl_input[0]["chunk_id"] = "ch_leaked"
        excl_input[0]["leaked_key"] = "should_not_appear"

        # Audit payload must remain unchanged: one record with the
        # original chunk_id, no leaked_key.
        self.assertEqual(len(out["filter_a"]["archive_excluded"]), 1)
        self.assertEqual(
            out["filter_a"]["archive_excluded"][0]["chunk_id"],
            "ch_orig",
        )
        self.assertNotIn(
            "leaked_key", out["filter_a"]["archive_excluded"][0]
        )

    # -------- existing FilterARecord coverage (unchanged) --------

    def test_archive_hits_count_matches_len(self):
        ah = [
            {"chunk_id": "c1", "score": 0.5},
            {"chunk_id": "c2", "score": 0.4},
            {"chunk_id": "c3", "score": 0.3},
        ]
        out = build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=_empty_core_query_result(),
            archive_hits=ah,
            assembled=_empty_assembled(),
        )
        self.assertEqual(out["filter_a"]["archive_hits_count"], 3)

    def test_filter_excluded_propagated(self):
        cqr = _empty_core_query_result()
        cqr["filter_excluded"] = [
            {"eid": 7, "excluded_reason": "non_shareable"},
            {"eid": 11, "excluded_reason": "non_shareable"},
        ]
        out = build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=cqr,
            archive_hits=[],
            assembled=_empty_assembled(),
        )
        self.assertEqual(len(out["filter_a"]["excluded"]), 2)
        self.assertEqual(out["filter_a"]["excluded"][0]["eid"], 7)

    def test_core_hits_in_count_inferred_from_excluded_when_missing(self):
        cqr = _empty_core_query_result()
        cqr["results"] = [{"eid": 1}, {"eid": 2}, {"eid": 3}]  # 3 survived
        cqr["filter_excluded"] = [
            {"eid": 4, "excluded_reason": "non_shareable"},
            {"eid": 5, "excluded_reason": "non_shareable"},
        ]
        # No _core_hits_in_count → inferred = out + excluded = 5
        out = build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=cqr,
            archive_hits=[],
            assembled=_empty_assembled(),
        )
        self.assertEqual(out["filter_a"]["core_hits_in_count"], 5)
        self.assertEqual(out["filter_a"]["core_hits_out_count"], 3)

    def test_core_hits_in_count_uses_s5_key_when_present(self):
        cqr = _empty_core_query_result()
        cqr["results"] = [{"eid": 1}, {"eid": 2}]
        cqr["filter_excluded"] = [{"eid": 3, "excluded_reason": "non_shareable"}]
        cqr["_core_hits_in_count"] = 10  # S5 propagation overrides inference
        out = build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=cqr,
            archive_hits=[],
            assembled=_empty_assembled(),
        )
        self.assertEqual(out["filter_a"]["core_hits_in_count"], 10)

    def test_authority_guard_rejected_default_zero(self):
        out = build_assembly_audit(**_minimal_kwargs())
        self.assertEqual(out["filter_a"]["authority_guard_rejected"], 0)

    def test_excluded_is_defensive_copy(self):
        cqr = _empty_core_query_result()
        cqr["filter_excluded"] = [{"eid": 7, "excluded_reason": "non_shareable"}]
        out = build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=cqr,
            archive_hits=[],
            assembled=_empty_assembled(),
        )
        # Mutate audit return; original input must be unchanged.
        out["filter_a"]["excluded"].clear()
        self.assertEqual(len(cqr["filter_excluded"]), 1)


# ---------------------------------------------------------------------------
# 7. AssemblySummary — profile_used, weights, tokens, block summaries
# ---------------------------------------------------------------------------

class TestBuildAssemblyAudit_AssemblySummary(unittest.TestCase):
    def test_profile_used_surfaced(self):
        asm = _empty_assembled()
        asm.profile = "research"
        out = build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=_empty_core_query_result(),
            archive_hits=[],
            assembled=asm,
        )
        self.assertEqual(out["assembly"]["profile_used"], "research")

    def test_block_token_counts_preserved(self):
        asm = _empty_assembled()
        asm.block_token_counts = {
            BLOCK_IDENTITY: 500,
            BLOCK_RELATIONAL: 800,
            BLOCK_SITUATIONAL: 300,
        }
        asm.tokens_used = 1600
        out = build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=_empty_core_query_result(),
            archive_hits=[],
            assembled=asm,
        )
        self.assertEqual(out["assembly"]["tokens_used"], 1600)
        self.assertEqual(
            out["assembly"]["block_token_counts"][BLOCK_RELATIONAL], 800
        )

    def test_blocks_summary_per_block_type(self):
        asm = _empty_assembled()
        asm.blocks[BLOCK_IDENTITY].append(
            _block(eid=1, block_type=BLOCK_IDENTITY,
                   metadata={"type": "seed_canon", "canon": True})
        )
        asm.blocks[BLOCK_RELATIONAL].append(
            _block(eid=2, block_type=BLOCK_RELATIONAL,
                   metadata={"character_tier": "relational", "half_life": 30.0})
        )
        asm.selection_log.append(
            _select_log(block_type=BLOCK_IDENTITY, eid=1, action="selected")
        )
        asm.selection_log.append(
            _select_log(block_type=BLOCK_RELATIONAL, eid=2, action="selected")
        )
        out = build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=_empty_core_query_result(),
            archive_hits=[],
            assembled=asm,
        )
        b_id = out["assembly"]["blocks"][BLOCK_IDENTITY]
        b_rel = out["assembly"]["blocks"][BLOCK_RELATIONAL]
        self.assertEqual(b_id["selected_count"], 1)
        self.assertEqual(b_id["selected_eids"], [1])
        self.assertEqual(b_rel["selected_count"], 1)
        self.assertEqual(b_rel["selected_eids"], [2])

    def test_selection_log_enriched_with_classification_basis_selected(self):
        asm = _empty_assembled()
        asm.blocks[BLOCK_IDENTITY].append(
            _block(eid=1, block_type=BLOCK_IDENTITY,
                   metadata={"type": "seed_canon", "canon": True})
        )
        asm.selection_log.append(
            _select_log(block_type=BLOCK_IDENTITY, eid=1, action="selected")
        )
        out = build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=_empty_core_query_result(),
            archive_hits=[],
            assembled=asm,
        )
        log = out["assembly"]["selection_log_enriched"]
        self.assertEqual(len(log), 1)
        self.assertEqual(
            log[0]["classification_basis"]["primary"], "mtype=seed_canon"
        )

    def test_selection_log_enriched_skipped_has_empty_basis(self):
        asm = _empty_assembled()
        asm.selection_log.append(
            _select_log(block_type=BLOCK_ARCHIVE, eid=None, chunk_id="c1",
                        action="skipped_archive_budget")
        )
        out = build_assembly_audit(
            request_meta=_minimal_request_meta(),
            core_query_result=_empty_core_query_result(),
            archive_hits=[],
            assembled=asm,
        )
        log = out["assembly"]["selection_log_enriched"]
        self.assertEqual(len(log), 1)
        # Skipped entries don't carry metadata → empty basis.
        self.assertEqual(log[0]["classification_basis"]["primary"], "")
        self.assertEqual(log[0]["classification_basis"]["secondary"], [])


# ---------------------------------------------------------------------------
# 8. ClassificationBasis — one test per rule (mirror of _classify_core_hit)
# ---------------------------------------------------------------------------

class TestBuildAssemblyAudit_ClassificationBasis(unittest.TestCase):
    def test_basis_seed_canon(self):
        b = _classification_basis(
            {"type": "seed_canon", "canon": True, "half_life": 3650.0}
        )
        self.assertEqual(b, {"primary": "mtype=seed_canon", "secondary": []})

    def test_basis_drift_correction(self):
        b = _classification_basis(
            {"type": "drift_correction", "canon": True, "half_life": 3650.0}
        )
        self.assertEqual(
            b, {"primary": "mtype=drift_correction", "secondary": []}
        )

    def test_basis_identity_anchor_canon_true(self):
        b = _classification_basis(
            {"type": "identity_anchor", "canon": True}
        )
        self.assertEqual(
            b,
            {"primary": "mtype=identity_anchor", "secondary": ["canon=true"]},
        )

    def test_basis_canon_only(self):
        b = _classification_basis(
            {"type": "memory", "canon": True}
        )
        self.assertEqual(b, {"primary": "canon=true", "secondary": []})

    def test_basis_spirit_return_resonance_high_warmth(self):
        b = _classification_basis({
            "type": "memory",
            "from_spirit_return": True,
            "spirit_return_mode": "resonance",
            "warmth_score": 0.72,
        })
        self.assertEqual(b["primary"], "spirit_return_mode=resonance")
        self.assertEqual(b["secondary"], ["warmth_score=0.72"])

    def test_basis_spirit_return_surfacing_moderate_warmth(self):
        b = _classification_basis({
            "type": "memory",
            "from_spirit_return": True,
            "spirit_return_mode": "surfacing",
            "warmth_score": 0.35,
        })
        self.assertEqual(b["primary"], "spirit_return_mode=surfacing")
        self.assertEqual(b["secondary"], ["warmth_score=0.35"])

    def test_basis_spirit_return_recollection_default(self):
        b = _classification_basis({
            "type": "memory",
            "from_spirit_return": True,
            "spirit_return_mode": "recollection",
            "warmth_score": 0.1,
        })
        self.assertEqual(b["primary"], "spirit_return_mode=recollection")
        self.assertEqual(b["secondary"], ["warmth_score=0.10"])

    def test_basis_tier_core_identity(self):
        b = _classification_basis(
            {"type": "memory", "character_tier": "core_identity"}
        )
        self.assertEqual(
            b, {"primary": "tier=core_identity", "secondary": []}
        )

    def test_basis_tier_derived_identity(self):
        b = _classification_basis(
            {"type": "memory", "character_tier": "derived_identity"}
        )
        self.assertEqual(
            b, {"primary": "tier=derived_identity", "secondary": []}
        )

    def test_basis_half_life_above_365(self):
        b = _classification_basis(
            {"type": "memory", "character_tier": "", "half_life": 400.0}
        )
        self.assertEqual(b, {"primary": "half_life>=365", "secondary": []})

    def test_basis_tier_relational(self):
        b = _classification_basis(
            {"type": "memory", "character_tier": "relational", "half_life": 30.0}
        )
        self.assertEqual(b, {"primary": "tier=relational", "secondary": []})

    def test_basis_half_life_above_7(self):
        b = _classification_basis(
            {"type": "memory", "character_tier": "", "half_life": 14.0}
        )
        self.assertEqual(b, {"primary": "half_life>=7", "secondary": []})

    def test_basis_default_situational(self):
        b = _classification_basis(
            {"type": "memory", "character_tier": "", "half_life": 3.0}
        )
        self.assertEqual(
            b, {"primary": "default_situational", "secondary": []}
        )

    def test_basis_handles_empty_metadata(self):
        b = _classification_basis({})
        # Empty metadata: not seed/drift/anchor/canon; not spirit; no
        # tier; half_life defaults to 30 → default_situational.
        self.assertEqual(
            b, {"primary": "default_situational", "secondary": []}
        )

    def test_basis_handles_none_metadata(self):
        b = _classification_basis(None)
        self.assertEqual(
            b, {"primary": "default_situational", "secondary": []}
        )


# ---------------------------------------------------------------------------
# 9. SpiritReturnSummary
# ---------------------------------------------------------------------------

class TestBuildAssemblyAudit_SpiritReturnSummary(unittest.TestCase):
    def test_empty_blocks_zero_total(self):
        s = _spirit_return_summary({})
        self.assertEqual(s["total"], 0)
        self.assertEqual(s["by_mode"], {"resonance": 0, "surfacing": 0, "recollection": 0})
        self.assertEqual(s["avg_warmth"], 0.0)
        self.assertFalse(s["any_entered_prompt"])

    def test_one_resonance_hit(self):
        blocks = _empty_blocks()
        blocks[BLOCK_IDENTITY].append(_block(
            eid=1, block_type=BLOCK_IDENTITY,
            metadata={"from_spirit_return": True,
                      "spirit_return_mode": "resonance",
                      "warmth_score": 0.72},
        ))
        s = _spirit_return_summary(blocks)
        self.assertEqual(s["total"], 1)
        self.assertEqual(s["by_mode"]["resonance"], 1)
        self.assertAlmostEqual(s["avg_warmth"], 0.72, places=2)
        self.assertTrue(s["any_entered_prompt"])

    def test_mixed_modes(self):
        blocks = _empty_blocks()
        blocks[BLOCK_IDENTITY].append(_block(
            eid=1, metadata={"from_spirit_return": True,
                             "spirit_return_mode": "resonance",
                             "warmth_score": 0.7},
        ))
        blocks[BLOCK_RELATIONAL].append(_block(
            eid=2, metadata={"from_spirit_return": True,
                             "spirit_return_mode": "surfacing",
                             "warmth_score": 0.4},
        ))
        blocks[BLOCK_SITUATIONAL].append(_block(
            eid=3, metadata={"from_spirit_return": True,
                             "spirit_return_mode": "recollection",
                             "warmth_score": 0.1},
        ))
        s = _spirit_return_summary(blocks)
        self.assertEqual(s["total"], 3)
        self.assertEqual(s["by_mode"],
                         {"resonance": 1, "surfacing": 1, "recollection": 1})
        self.assertAlmostEqual(s["avg_warmth"], 0.4, places=2)
        self.assertTrue(s["any_entered_prompt"])

    def test_non_spirit_hits_not_counted(self):
        blocks = _empty_blocks()
        blocks[BLOCK_IDENTITY].append(_block(
            eid=1, metadata={"type": "seed_canon", "canon": True,
                             "from_spirit_return": False},
        ))
        s = _spirit_return_summary(blocks)
        self.assertEqual(s["total"], 0)
        self.assertFalse(s["any_entered_prompt"])

    def test_unknown_mode_counted_in_total_not_by_mode(self):
        blocks = _empty_blocks()
        blocks[BLOCK_RELATIONAL].append(_block(
            eid=1, metadata={"from_spirit_return": True,
                             "spirit_return_mode": "unknown_mode",
                             "warmth_score": 0.5},
        ))
        s = _spirit_return_summary(blocks)
        self.assertEqual(s["total"], 1)
        # Unknown mode is not added to any by_mode bucket.
        self.assertEqual(s["by_mode"],
                         {"resonance": 0, "surfacing": 0, "recollection": 0})


# ---------------------------------------------------------------------------
# 10. ToolResultSummary
# ---------------------------------------------------------------------------

class TestBuildAssemblyAudit_ToolResultSummary(unittest.TestCase):
    def test_no_tool_result_hits(self):
        s = _tool_result_summary(_empty_blocks())
        self.assertEqual(s["count_in_prompt"], 0)
        self.assertEqual(
            s["three_modifier"],
            "(low-authority, decay-bounded, tool_result)",
        )
        self.assertEqual(s["tool_names"], [])
        self.assertEqual(s["per_hit"], [])

    def test_one_tool_result_hit(self):
        blocks = _empty_blocks()
        blocks[BLOCK_SITUATIONAL].append(_block(
            eid=42, block_type=BLOCK_SITUATIONAL, score=0.7,
            metadata={"provenance_type": "tool_result",
                      "provenance_tool_name": "weather:current"},
        ))
        s = _tool_result_summary(blocks)
        self.assertEqual(s["count_in_prompt"], 1)
        self.assertEqual(s["tool_names"], ["weather:current"])
        self.assertEqual(len(s["per_hit"]), 1)
        self.assertEqual(s["per_hit"][0]["eid"], 42)
        self.assertEqual(s["per_hit"][0]["tool_name"], "weather:current")
        self.assertEqual(s["per_hit"][0]["block_type"], BLOCK_SITUATIONAL)
        self.assertAlmostEqual(s["per_hit"][0]["score"], 0.7, places=2)

    def test_three_modifier_is_cluster_2_default_verbatim(self):
        s = _tool_result_summary(_empty_blocks())
        self.assertEqual(
            s["three_modifier"],
            "(low-authority, decay-bounded, tool_result)",
        )

    def test_tool_names_deduped_and_sorted(self):
        blocks = _empty_blocks()
        blocks[BLOCK_SITUATIONAL].append(_block(
            eid=1, metadata={"provenance_type": "tool_result",
                             "provenance_tool_name": "weather:current"},
        ))
        blocks[BLOCK_SITUATIONAL].append(_block(
            eid=2, metadata={"provenance_type": "tool_result",
                             "provenance_tool_name": "weather:current"},
        ))
        blocks[BLOCK_ARCHIVE].append(_block(
            eid=3, metadata={"provenance_type": "tool_result",
                             "provenance_tool_name": "clock:probe"},
        ))
        s = _tool_result_summary(blocks)
        self.assertEqual(s["count_in_prompt"], 3)
        # Sorted, deduped.
        self.assertEqual(s["tool_names"], ["clock:probe", "weather:current"])

    def test_tool_result_missing_tool_name(self):
        blocks = _empty_blocks()
        blocks[BLOCK_SITUATIONAL].append(_block(
            eid=1, metadata={"provenance_type": "tool_result"},
        ))
        s = _tool_result_summary(blocks)
        self.assertEqual(s["count_in_prompt"], 1)
        self.assertEqual(s["tool_names"], [])  # empty string not added
        self.assertEqual(s["per_hit"][0]["tool_name"], "")


# ---------------------------------------------------------------------------
# 11. ResponseShape — top-level keys, no surprise keys, no raw_*
# ---------------------------------------------------------------------------

_EXPECTED_TOP_LEVEL_KEYS = frozenset({
    "lane_version",
    "timestamp",
    "request",
    "embedder",
    "filter_a",
    "assembly",
    "character",
    "spirit_return_summary",
    "tool_result_summary",
})


class TestBuildAssemblyAudit_ResponseShape(unittest.TestCase):
    def test_top_level_keys_exactly_expected(self):
        out = build_assembly_audit(**_minimal_kwargs())
        self.assertEqual(set(out.keys()), _EXPECTED_TOP_LEVEL_KEYS)

    def test_no_raw_keys_anywhere_top_level(self):
        out = build_assembly_audit(**_minimal_kwargs())
        for k in out.keys():
            self.assertFalse(
                k.startswith("raw_"),
                f"top-level raw_* key {k!r} must not appear in audit",
            )

    def test_filter_a_block_keys_stable(self):
        """Legacy path: archive_filter_excluded omitted → 6-key filter_a
        shape per v0.2 first revision.
        """
        out = build_assembly_audit(**_minimal_kwargs())
        expected = {
            "core_hits_in_count",
            "core_hits_out_count",
            "excluded",
            "authority_guard_rejected",
            "archive_hits_count",
            "archive_filter_applied",
        }
        self.assertEqual(set(out["filter_a"].keys()), expected)

    def test_filter_a_block_keys_when_archive_param_passed(self):
        """v0.2.4-A1 path: archive_filter_excluded supplied → 7-key
        filter_a shape (legacy 6 + archive_excluded). The archive_excluded
        key appears IFF the upstream filter ran, even when the list is
        empty — its presence is the structural signal.
        """
        out = build_assembly_audit(
            **_minimal_kwargs(),
            archive_filter_excluded=[],
        )
        expected = {
            "core_hits_in_count",
            "core_hits_out_count",
            "excluded",
            "authority_guard_rejected",
            "archive_hits_count",
            "archive_filter_applied",
            "archive_excluded",
        }
        self.assertEqual(set(out["filter_a"].keys()), expected)

    def test_request_block_keys_stable(self):
        out = build_assembly_audit(**_minimal_kwargs())
        expected = {
            "workspace_id", "agent_id", "query", "profile",
            "top_k", "token_budget", "surface",
        }
        self.assertEqual(set(out["request"].keys()), expected)


# ---------------------------------------------------------------------------
# Helper-level coverage (private helpers tested directly for symmetry)
# ---------------------------------------------------------------------------

class TestPrivateHelpers_RequestRecord(unittest.TestCase):
    def test_surface_hardcoded(self):
        r = _request_record({"workspace_id": "x"})
        self.assertEqual(r["surface"], SURFACE_LLM_CONTEXT)

    def test_none_request_meta_graceful(self):
        r = _request_record(None)
        self.assertEqual(r["workspace_id"], "")


class TestPrivateHelpers_EmbedderSnapshot(unittest.TestCase):
    def test_extracts_from_embed_context(self):
        cqr = {
            "embed_context": {
                "embedder": {
                    "provider": "st",
                    "model": "BAAI/bge-small-en-v1.5",
                    "dim": 384,
                },
                "workspace_lock": {},
            }
        }
        e = _embedder_snapshot(cqr)
        self.assertEqual(e["provider"], "st")
        self.assertEqual(e["dim"], 384)

    def test_missing_embed_context(self):
        e = _embedder_snapshot({})
        self.assertEqual(e, {"provider": "", "model": "", "dim": 0})


class TestPrivateHelpers_CharacterSummary(unittest.TestCase):
    def test_extracts_subset(self):
        cqr = {
            "character_context": {
                "character_name": "Ryuki",
                "seed_basin_role": "anchor",
                "drift_score": 0.12,
                "drift_direction": "toward_seed",
                "relational_count": 7,
                # Extra keys must be ignored.
                "seed_preamble": "extra text not surfaced",
            }
        }
        c = _character_summary(cqr)
        self.assertEqual(c["character_name"], "Ryuki")
        self.assertEqual(c["relational_count"], 7)
        self.assertAlmostEqual(c["drift_score"], 0.12, places=2)
        # Extra fields not present in surfaced subset.
        self.assertNotIn("seed_preamble", c)


if __name__ == "__main__":
    unittest.main()
