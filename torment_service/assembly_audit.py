# torment_service/assembly_audit.py
"""
Character-memory observability for memory-to-prompt automation
(Memory-to-Prompt v0.2 — observability lane, Slice S4).

Read-only helper that makes visible what memory shaped the character's
next response, so we can verify character continuity, voice, callbacks,
emotional recall, relationship memory, symbolic resonance, and
tool-aware dialogue before changing behavior.

DOCTRINE: `docs/MEMORY_TO_PROMPT_AUTOMATION_v0.2.md` §§1, 2, 4.
PARENT:   `docs/MEMORY_TO_PROMPT_AUTOMATION_v0.1.md`.

INVARIANTS (helper-level):
    - Read-only: inputs are never mutated.
    - No I/O: no file open, no socket, no network, no ledger writes.
      Per S3 Decision 1 (Option C — response-only), the helper does
      not persist any audit record. The audit payload exists only in
      memory and in the HTTP response.
    - No new schema fields on hits / blocks / AssembledContext. Every
      field surfaced by the helper is computed from existing inputs.
    - Response shape invariant under input shape variation. Missing
      inputs degrade to empty defaults; the helper does not raise on
      missing optional fields.
    - One canonical derivation (PROVENANCE_DOCTRINE Invariant C): the
      helper is the single place where assembly observability is
      produced. Inline parsing at call sites is forbidden.

S4 scope: this module + tests only. Endpoint wiring is Slice S5.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Set

from .governance import SURFACE_LLM_CONTEXT
from .retrieval_assembler import AssembledContext


# ---------------------------------------------------------------------------
# Constants (module-level, per S4 plan §1.1 and §6.1)
# ---------------------------------------------------------------------------

_LANE_VERSION = "memory_to_prompt_observability_v0.2"

# Cluster 2 v0.1 §11.3 three-modifier default for tool_result rows.
# Verbatim per v0.2 §2.6. Per-tool-family variants deferred to v0.3
# (Cluster 2 §11.7).
_TOOL_RESULT_THREE_MODIFIER = "(low-authority, decay-bounded, tool_result)"

# Archive hits do not pass FILTER-A today (S1 finding §3.2 / v0.2 §3.2).
# v0.2 observability *reports* the gap honestly; the fix is a separate
# ratifiable slice (v0.2.4 or v0.3). Per S3 Decision 5.
_ARCHIVE_FILTER_APPLIED_TODAY = False


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_assembly_audit(
    *,
    request_meta: Dict[str, Any],
    core_query_result: Dict[str, Any],
    archive_hits: List[Dict[str, Any]],
    assembled: Any,  # AssembledContext or dict; both accepted gracefully
) -> Dict[str, Any]:
    """Build the assembly_audit dict per v0.2 doctrine §4.2.

    Args:
        request_meta: Request shape — workspace_id, agent_id, query,
            profile, top_k, token_budget. Missing keys degrade to
            empty / zero defaults.
        core_query_result: Dict returned by fabric.query(). Helper
            reads (with graceful defaults): results, character_context,
            embed_context, filter_excluded (S5-propagated; defaults to
            []), _core_hits_in_count and _authority_guard_rejected
            (S5-propagated; default sensibly from len() / 0).
        archive_hits: List of chunk dicts from ArchiveStore.retrieve().
            Counted; not walked beyond len().
        assembled: AssembledContext dataclass instance, or a dict with
            the same fields. Both supported for test ergonomics.

    Returns:
        dict per v0.2 §4.2 with top-level keys: lane_version,
        timestamp, request, embedder, filter_a, assembly, character,
        spirit_return_summary, tool_result_summary.

    The helper does not mutate any input. The helper does no I/O. The
    helper does not raise on missing inputs (graceful empty defaults).
    """
    # Unpack assembled context. AssembledContext is preferred; dict is
    # accepted for test ergonomics (Trio decision 3 — hand-constructed
    # fixtures).
    if isinstance(assembled, AssembledContext):
        a_profile = str(assembled.profile)
        a_token_budget = int(assembled.token_budget)
        a_tokens_used = int(assembled.tokens_used)
        a_block_token_counts = dict(assembled.block_token_counts or {})
        a_blocks: Dict[str, List[Dict[str, Any]]] = (
            assembled.blocks or {}
        )
        a_selection_log: List[Dict[str, Any]] = (
            assembled.selection_log or []
        )
    elif isinstance(assembled, dict):
        a_profile = str(assembled.get("profile", ""))
        a_token_budget = _as_int(assembled.get("token_budget"), 0)
        a_tokens_used = _as_int(assembled.get("tokens_used"), 0)
        a_block_token_counts = dict(assembled.get("block_token_counts") or {})
        a_blocks = assembled.get("blocks") or {}
        a_selection_log = assembled.get("selection_log") or []
    else:
        a_profile = ""
        a_token_budget = 0
        a_tokens_used = 0
        a_block_token_counts = {}
        a_blocks = {}
        a_selection_log = []

    return {
        "lane_version": _LANE_VERSION,
        "timestamp": int(time.time()),
        "request": _request_record(request_meta),
        "embedder": _embedder_snapshot(core_query_result),
        "filter_a": _filter_a_record(core_query_result, archive_hits),
        "assembly": _assembly_summary(
            profile=a_profile,
            token_budget=a_token_budget,
            tokens_used=a_tokens_used,
            block_token_counts=a_block_token_counts,
            blocks=a_blocks,
            selection_log=a_selection_log,
        ),
        "character": _character_summary(core_query_result),
        "spirit_return_summary": _spirit_return_summary(a_blocks),
        "tool_result_summary": _tool_result_summary(a_blocks),
    }


# ---------------------------------------------------------------------------
# Private helpers — each produces one block of the §4.2 response shape
# ---------------------------------------------------------------------------

def _request_record(request_meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Build the request block. Surface is hardcoded to
    SURFACE_LLM_CONTEXT for v0.2 first revision; future revisions may
    extend.
    """
    rm = request_meta or {}
    return {
        "workspace_id": str(rm.get("workspace_id", "")),
        "agent_id": str(rm.get("agent_id", "")),
        "query": str(rm.get("query", "")),
        "profile": str(rm.get("profile", "")),
        "top_k": _as_int(rm.get("top_k"), 0),
        "token_budget": _as_int(rm.get("token_budget"), 0),
        "surface": SURFACE_LLM_CONTEXT,
    }


def _embedder_snapshot(
    core_query_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Extract embedder identity from embed_context. Graceful defaults
    if embed_context is absent (e.g., older code paths or test
    fixtures without embedder state).
    """
    cqr = core_query_result or {}
    embed_ctx = cqr.get("embed_context") or {}
    # The runtime stores it as {"embedder": {...}, "workspace_lock":
    # {...}}; we surface only the embedder identity.
    embedder = embed_ctx.get("embedder") or {}
    return {
        "provider": str(embedder.get("provider", "")),
        "model": str(embedder.get("model", "")),
        "dim": _as_int(embedder.get("dim"), 0),
    }


def _filter_a_record(
    core_query_result: Optional[Dict[str, Any]],
    archive_hits: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Build the FILTER-A record (v0.2 §2.2).

    Honestly reports archive_filter_applied=false until a future slice
    closes that gap (S3 Decision 5).

    Reads three S5-propagated keys with graceful fallbacks:
        - filter_excluded: list of {eid, excluded_reason}
        - _core_hits_in_count: int (falls back to len(results) +
          len(filter_excluded))
        - _authority_guard_rejected: int (falls back to 0)
    """
    cqr = core_query_result or {}
    # Defensive copy of the excluded list so callers can't see mutation
    # via the audit return (and so mutations on our return don't reach
    # the caller).
    filter_excluded = [dict(e) for e in (cqr.get("filter_excluded") or [])]
    results = cqr.get("results") or []
    core_hits_out = len(results)

    core_hits_in_raw = cqr.get("_core_hits_in_count")
    if core_hits_in_raw is None:
        core_hits_in = core_hits_out + len(filter_excluded)
    else:
        core_hits_in = _as_int(core_hits_in_raw, core_hits_out)

    return {
        "core_hits_in_count": int(core_hits_in),
        "core_hits_out_count": int(core_hits_out),
        "excluded": filter_excluded,
        "authority_guard_rejected": _as_int(
            cqr.get("_authority_guard_rejected"), 0
        ),
        "archive_hits_count": len(archive_hits or []),
        "archive_filter_applied": _ARCHIVE_FILTER_APPLIED_TODAY,
    }


def _character_summary(
    core_query_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Surface a small fixed subset of character_context for character
    legibility per v0.2 §2.7. No CharacterState write-site access.
    """
    cqr = core_query_result or {}
    char_ctx = cqr.get("character_context") or {}
    return {
        "character_name": str(char_ctx.get("character_name", "")),
        "seed_basin_role": str(char_ctx.get("seed_basin_role", "")),
        "drift_score": _as_float(char_ctx.get("drift_score"), 0.0),
        "drift_direction": str(char_ctx.get("drift_direction", "")),
        "relational_count": _as_int(char_ctx.get("relational_count"), 0),
    }


def _assembly_summary(
    *,
    profile: str,
    token_budget: int,
    tokens_used: int,
    block_token_counts: Dict[str, int],
    blocks: Dict[str, List[Dict[str, Any]]],
    selection_log: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build the assembly summary block per v0.2 §2.3 and §4.2.

    Includes per-block summary with structured classification_basis
    per selected hit (§2.4), plus an enriched selection_log where
    selected entries carry classification_basis derived from the
    block's metadata. Skipped entries default to empty basis (they
    don't carry metadata in selection_log; the basis would require
    upstream propagation that v0.2 first revision does not add).
    """
    # Import here to avoid any potential circular-import concern and
    # to keep module-level imports minimal.
    from .retrieval_assembler import PROFILES

    weights = dict(PROFILES.get(profile, {}))

    # Tally candidates_seen per block type from selection_log.
    candidates_per_bt: Dict[str, int] = {}
    for entry in selection_log:
        bt = entry.get("block_type")
        if bt:
            candidates_per_bt[bt] = candidates_per_bt.get(bt, 0) + 1

    # Per-block summary. Iterate the union of block-type keys so we
    # surface block types that had candidates but no selections (all
    # skipped) too.
    all_block_types: Set[str] = set(blocks.keys()) | set(
        candidates_per_bt.keys()
    )
    blocks_summary: Dict[str, Dict[str, Any]] = {}
    for bt in sorted(all_block_types):
        block_list = blocks.get(bt, []) or []
        selected_eids: List[int] = []
        selected_chunk_ids: List[str] = []
        classification_basis_list: List[Dict[str, Any]] = []
        for b in block_list:
            eid = b.get("eid")
            if eid is not None:
                selected_eids.append(int(eid))
            chunk_id = b.get("chunk_id")
            if chunk_id:
                selected_chunk_ids.append(str(chunk_id))
            meta = b.get("metadata") or {}
            basis = _classification_basis(meta)
            classification_basis_list.append({
                "eid": int(eid) if eid is not None else None,
                "primary": basis["primary"],
                "secondary": list(basis["secondary"]),
            })
        blocks_summary[bt] = {
            "candidates_seen": candidates_per_bt.get(bt, len(block_list)),
            "selected_count": len(block_list),
            "tokens_used": _as_int(block_token_counts.get(bt), 0),
            "selected_eids": selected_eids,
            "selected_chunk_ids": selected_chunk_ids,
            "classification_basis": classification_basis_list,
        }

    # Enriched selection log. For selected entries, look up metadata
    # from the corresponding block and compute basis. For skipped
    # entries, basis defaults to empty (selection_log doesn't carry
    # metadata for skipped candidates).
    enriched_log: List[Dict[str, Any]] = []
    for entry in selection_log:
        new_entry: Dict[str, Any] = dict(entry)
        new_entry.setdefault("score", 0.0)
        new_entry.setdefault("token_count", 0)
        new_entry.setdefault("reason", "")
        basis: Dict[str, Any] = {"primary": "", "secondary": []}
        if entry.get("action") == "selected":
            bt = entry.get("block_type")
            eid = entry.get("eid")
            chunk_id = entry.get("chunk_id")
            if bt and bt in blocks:
                for b in blocks.get(bt, []) or []:
                    if eid is not None and b.get("eid") == eid:
                        basis = _classification_basis(b.get("metadata") or {})
                        break
                    if chunk_id and b.get("chunk_id") == chunk_id:
                        basis = _classification_basis(b.get("metadata") or {})
                        break
        new_entry["classification_basis"] = {
            "primary": basis["primary"],
            "secondary": list(basis["secondary"]),
        }
        enriched_log.append(new_entry)

    return {
        "profile_used": str(profile),
        "profile_weights": weights,
        "tokens_used": int(tokens_used),
        "token_budget": int(token_budget),
        "block_token_counts": dict(block_token_counts),
        "blocks": blocks_summary,
        "selection_log_enriched": enriched_log,
    }


def _classification_basis(
    hit_metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute the structured classification basis per v0.2 §2.4.

    Mirror of `_classify_core_hit()` in retrieval_assembler.py
    (rules at retrieval_assembler.py:144–185). Returns the basis
    tuple {primary, secondary} the classifier would have used given
    these inputs.

    Missing / empty / None metadata returns the `default_situational`
    basis. Missing or absent `half_life` does NOT invent a relational
    or core-tier classification — observability reports honestly
    rather than fabricating a 30-day default that the upstream hit
    dict happens to set when present. This is one edge-case
    divergence from `_classify_core_hit`'s behavior on real hit dicts
    (which always carry `half_life`); observability is allowed (and
    expected) to report honestly when a field is absent.

    MIRROR: any change to retrieval_assembler._classify_core_hit must
    be reflected here. The two functions are paired by convention; a
    future v0.2.x or v0.3 may factor them into a shared return.
    """
    meta = hit_metadata or {}
    if not meta:
        return {"primary": "default_situational", "secondary": []}

    mtype = str(meta.get("type") or meta.get("mtype") or "")
    tier = str(meta.get("character_tier") or "")
    has_half_life = (
        "half_life" in meta and meta.get("half_life") is not None
    )
    half_life = _as_float(meta.get("half_life"), 0.0)
    canon = bool(meta.get("canon", False))
    from_spirit = bool(meta.get("from_spirit_return", False))

    if mtype == "seed_canon":
        return {"primary": "mtype=seed_canon", "secondary": []}
    if mtype == "drift_correction":
        return {"primary": "mtype=drift_correction", "secondary": []}
    if mtype == "identity_anchor" and canon:
        return {
            "primary": "mtype=identity_anchor",
            "secondary": ["canon=true"],
        }
    if canon:
        return {"primary": "canon=true", "secondary": []}

    if from_spirit:
        mode = str(meta.get("spirit_return_mode") or "recollection")
        warmth = _as_float(meta.get("warmth_score"), 0.2)
        warmth_token = f"warmth_score={warmth:.2f}"
        if mode == "resonance" and warmth >= 0.5:
            return {
                "primary": "spirit_return_mode=resonance",
                "secondary": [warmth_token],
            }
        if mode == "surfacing" and warmth >= 0.3:
            return {
                "primary": "spirit_return_mode=surfacing",
                "secondary": [warmth_token],
            }
        return {
            "primary": f"spirit_return_mode={mode}",
            "secondary": [warmth_token],
        }

    if tier in ("core_identity", "derived_identity"):
        return {"primary": f"tier={tier}", "secondary": []}
    if has_half_life and half_life >= 365.0:
        return {"primary": "half_life>=365", "secondary": []}
    if tier == "relational":
        return {"primary": "tier=relational", "secondary": []}
    if has_half_life and half_life >= 7.0:
        return {"primary": "half_life>=7", "secondary": []}

    return {"primary": "default_situational", "secondary": []}


def _spirit_return_summary(
    assembled_blocks: Optional[Dict[str, List[Dict[str, Any]]]],
) -> Dict[str, Any]:
    """Compute spirit-return summary from the assembled blocks dict
    per v0.2 §2.5. Reports what entered prompt context (not what was
    retrieved); these can differ when budget skips spirit-return hits.
    """
    total = 0
    by_mode: Dict[str, int] = {
        "resonance": 0,
        "surfacing": 0,
        "recollection": 0,
    }
    warmth_values: List[float] = []
    for _bt, blocks_list in (assembled_blocks or {}).items():
        for block in (blocks_list or []):
            meta = block.get("metadata") or {}
            if not meta.get("from_spirit_return"):
                continue
            total += 1
            mode = str(meta.get("spirit_return_mode") or "recollection")
            if mode in by_mode:
                by_mode[mode] += 1
            warmth_values.append(_as_float(meta.get("warmth_score"), 0.0))
    avg_warmth = (
        sum(warmth_values) / len(warmth_values) if warmth_values else 0.0
    )
    return {
        "total": total,
        "by_mode": by_mode,
        "avg_warmth": avg_warmth,
        "any_entered_prompt": total > 0,
    }


def _tool_result_summary(
    assembled_blocks: Optional[Dict[str, List[Dict[str, Any]]]],
) -> Dict[str, Any]:
    """Compute tool-result advisory summary per v0.2 §2.6.

    three_modifier is the Cluster 2 §11.3 ratified default verbatim;
    v0.2 does not introduce a per-tool-family variant (Cluster 2 §11.7
    defers that to v0.3).
    """
    count = 0
    tool_names_set: Set[str] = set()
    per_hit: List[Dict[str, Any]] = []
    for bt, blocks_list in (assembled_blocks or {}).items():
        for block in (blocks_list or []):
            meta = block.get("metadata") or {}
            if meta.get("provenance_type") != "tool_result":
                continue
            count += 1
            tname = str(meta.get("provenance_tool_name") or "")
            if tname:
                tool_names_set.add(tname)
            per_hit.append({
                "eid": block.get("eid"),
                "tool_name": tname,
                "block_type": bt,
                "score": _as_float(block.get("score"), 0.0),
            })
    return {
        "count_in_prompt": count,
        "three_modifier": _TOOL_RESULT_THREE_MODIFIER,
        "tool_names": sorted(tool_names_set),
        "per_hit": per_hit,
    }


# ---------------------------------------------------------------------------
# Small coercion helpers (graceful defaults; never raise on missing/bad input)
# ---------------------------------------------------------------------------

def _as_int(value: Any, default: int) -> int:
    """Coerce to int; return default on failure."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float) -> float:
    """Coerce to float; return default on failure."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
