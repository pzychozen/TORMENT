"""
tests/test_spirit_return_summary_parity.py

Constructor-level locks for the sole production /retrieve composition seam
as of d47c76f:

    /retrieve -> assemble_context() -> build_assembly_audit()

`assemble_context()` and `build_assembly_audit()` each have exactly one
production caller at that commit, both in torment_service/app.py under
POST /retrieve. These tests deliberately avoid HTTP because existing
boundary tests cover /retrieve wiring; this slice locks the summary
relationship at the constructor seam.

Non-goals for this slice:
    - unknown-mode vocabulary asymmetry
    - synthetic warmth fallback asymmetry

All spirit-return fixtures below carry explicit warmth_score values and use
the real assembler bridge before the audit summary is built.
"""
from __future__ import annotations

import copy
import math
import os
import sys
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.assembly_audit import build_assembly_audit
from torment_service.character import CharacterSeed, assemble_character_context
from torment_service.retrieval_assembler import AssembledContext, assemble_context


_DOCUMENTED_MODES = ("resonance", "surfacing", "recollection")


def _seed() -> CharacterSeed:
    return CharacterSeed(
        seed_id="summary_parity_seed_v1",
        character_name="Parity",
        seed_text="Parity is steady and plainspoken.",
    )


def _spirit_hit(
    *,
    eid: int,
    mode: str,
    warmth: float,
    summary: str,
    score: float = 0.9,
) -> Dict[str, Any]:
    return {
        "eid": eid,
        "score": score,
        "final_score": score,
        "summary": summary,
        "type": "memory",
        "strength": 0.5,
        "confidence": 0.8,
        "step": eid,
        "memory_class": "core",
        "from_deep_memory": True,
        "from_spirit_return": True,
        "spirit_return_mode": mode,
        "spirit_return_flavor": "explicit test flavor",
        "symbol_interaction": "echo",
        "warmth_score": warmth,
    }


def _short_spirit_hits() -> List[Dict[str, Any]]:
    return [
        _spirit_hit(
            eid=1,
            mode="resonance",
            warmth=0.7,
            summary="short resonance memory",
        ),
        _spirit_hit(
            eid=2,
            mode="surfacing",
            warmth=0.4,
            summary="short surfacing memory",
        ),
        _spirit_hit(
            eid=3,
            mode="recollection",
            warmth=0.2,
            summary="short recollection memory",
        ),
    ]


def _compose_summaries(
    hits: List[Dict[str, Any]],
    *,
    token_budget: int,
) -> Tuple[Dict[str, Any], Dict[str, Any], AssembledContext]:
    """Mirror the production /retrieve constructor seam without HTTP."""
    query_hits = copy.deepcopy(hits)
    seed = _seed()
    character_context = assemble_character_context(
        graph=None,
        seed=seed,
        agent_id="summary_parity_agent",
        hits=query_hits,
    )
    assembled = assemble_context(
        core_hits=query_hits,
        archive_hits=[],
        profile="companion",
        token_budget=token_budget,
        seed_text=character_context["seed_preamble"],
        character_name=character_context["character_name"],
    )
    audit = build_assembly_audit(
        request_meta={
            "workspace_id": "summary_parity_workspace",
            "agent_id": "summary_parity_agent",
            "query": "what returned?",
            "profile": "companion",
            "top_k": 5,
            "token_budget": token_budget,
        },
        core_query_result={
            "results": query_hits,
            "character_context": character_context,
            "embed_context": None,
            "filter_excluded": [],
            "_core_hits_in_count": len(query_hits),
            "_authority_guard_rejected": 0,
        },
        archive_hits=[],
        assembled=assembled,
        archive_filter_excluded=[],
    )
    return (
        character_context["spirit_return_summary"],
        audit["spirit_return_summary"],
        assembled,
    )


def _assert_audit_is_character_subset(
    character_summary: Dict[str, Any],
    audit_summary: Dict[str, Any],
) -> None:
    assert audit_summary["total"] <= character_summary["total"]
    for mode in _DOCUMENTED_MODES:
        assert audit_summary["by_mode"][mode] <= character_summary["by_mode"][mode]


def test_ample_budget_shared_fields_match_character_summary() -> None:
    character_summary, audit_summary, assembled = _compose_summaries(
        _short_spirit_hits(),
        token_budget=2000,
    )

    assert character_summary["total"] == 3
    assert audit_summary["total"] == character_summary["total"]
    assert audit_summary["by_mode"] == character_summary["by_mode"]
    assert math.isclose(
        audit_summary["avg_warmth"],
        character_summary["avg_warmth"],
        rel_tol=1e-12,
    )
    assert audit_summary["any_entered_prompt"] is True
    assert sum(
        1
        for blocks in assembled.blocks.values()
        for block in blocks
        if block.get("metadata", {}).get("from_spirit_return")
    ) == character_summary["total"]


def test_audit_summary_counts_are_never_larger_than_character_counts() -> None:
    ample_character, ample_audit, _ = _compose_summaries(
        _short_spirit_hits(),
        token_budget=2000,
    )
    _assert_audit_is_character_subset(ample_character, ample_audit)

    constrained_hits = _short_spirit_hits()
    constrained_hits[-1]["summary"] = "oversized recollection memory " * 400
    constrained_character, constrained_audit, _ = _compose_summaries(
        constrained_hits,
        token_budget=80,
    )
    _assert_audit_is_character_subset(constrained_character, constrained_audit)


def test_constrained_budget_allows_audit_summary_to_be_lower() -> None:
    hits = _short_spirit_hits()
    hits[-1]["summary"] = "oversized recollection memory " * 400

    character_summary, audit_summary, assembled = _compose_summaries(
        hits,
        token_budget=80,
    )

    assert character_summary["total"] == 3
    assert audit_summary["total"] == 2
    assert audit_summary["by_mode"] == {
        "resonance": 1,
        "surfacing": 1,
        "recollection": 0,
    }
    assert math.isclose(audit_summary["avg_warmth"], (0.7 + 0.4) / 2)
    assert any(
        entry["action"] == "skipped_budget_exhausted"
        and entry["eid"] == 3
        for entry in assembled.selection_log
    )


def test_any_entered_prompt_is_audit_only_and_truthful() -> None:
    hits = [
        _spirit_hit(
            eid=9,
            mode="recollection",
            warmth=0.3,
            summary="oversized recollection memory " * 400,
        )
    ]

    character_summary, audit_summary, assembled = _compose_summaries(
        hits,
        token_budget=80,
    )

    assert "any_entered_prompt" not in character_summary
    assert character_summary["total"] == 1
    assert audit_summary == {
        "total": 0,
        "by_mode": {"resonance": 0, "surfacing": 0, "recollection": 0},
        "avg_warmth": 0.0,
        "any_entered_prompt": False,
    }
    assert not any(
        block.get("metadata", {}).get("from_spirit_return")
        for blocks in assembled.blocks.values()
        for block in blocks
    )
