"""Pure source-extraction: selected admitted items from an AssembledContext.

Extracts ONLY the block items that the retrieval assembler marked
``action == "selected"`` in ``selection_log``, joined against the already-
selected ``blocks`` of a ``retrieval_assembler.AssembledContext`` (or an
AssembledContext-like dict), matched by ``(block_type, eid, chunk_id)``.

It is a pure transform over an EXPLICIT, caller-supplied AssembledContext. It
performs NO retrieval, NO ``fabric.query``, NO assembler call, and does NOT
parse ``assembled_text``. It is CALLED NOWHERE in production. It is duck-typed:
it reads ``.blocks`` / ``.selection_log`` (or the same dict keys) and imports no
assembler / fabric / retrieval / app / client / model / writer / persistence
module.

SCOPE / RISKS (load-bearing):
  * Source extraction here is a SEPARATE stage from packet filtering. The items
    returned are *candidate* ``admitted_context_items``; the existing packet
    builder (``audit_evidence_packet.build_audit_evidence_packet``) applies its
    own sensitivity exclusions downstream. This helper makes NO admissibility
    claim.
  * ``fabric.query``'s ``"character_context"`` and
    ``retrieval_assembler.AssembledContext`` are DIFFERENT surfaces unless proven
    identical. This helper consumes an AssembledContext (object or
    AssembledContext-like dict) ONLY — never a generic character_context.
  * ``selection_log`` "selected" entries carry IDs + ``block_type``, not full
    content; full content lives in ``blocks``. We JOIN selected keys to the
    already-selected block dicts — never to raw candidates.
  * ``assembled_text`` is too lossy (may include excluded identity material) and
    is NOT parsed or used as a source.
  * Identity / seed / drift blocks may be assembler-SELECTED; that does NOT make
    them packet-admissible. The packet builder excludes seed/identity later —
    BUT note: ``AssembledContext`` block dicts (``asdict(ContextBlock)``) keep
    source markers in ``metadata``, NOT at the top level the packet builder
    reads. So a later wiring stage must lift markers to the top level (or teach
    the builder to read them) before filtering is effective. That is a wiring
    obligation, not this helper's.
  * Later wiring must prove same-turn prompt inclusion, not merely "present in
    AssembledContext".
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _view(assembled: Any) -> Tuple[Dict[str, Any], List[Any]]:
    """Read ``blocks`` and ``selection_log`` from an AssembledContext object or
    AssembledContext-like dict, without importing the assembler."""
    if isinstance(assembled, dict):
        blocks = assembled.get("blocks")
        log = assembled.get("selection_log")
    else:
        blocks = getattr(assembled, "blocks", None)
        log = getattr(assembled, "selection_log", None)
    if not isinstance(blocks, dict):
        blocks = {}
    if not isinstance(log, list):
        log = []
    return blocks, log


def selected_admitted_items(assembled: Any) -> List[Dict[str, Any]]:
    """Return the selected block dicts (candidate ``admitted_context_items``).

    Joins ``selection_log`` entries with ``action == "selected"`` against the
    already-selected ``blocks``, by ``(block_type, eid, chunk_id)``. Returns the
    matched block dicts only. Pure: no retrieval, no assembler call, no
    ``assembled_text`` parsing, no admissibility claim.
    """
    blocks, selection_log = _view(assembled)

    # 1. Keys explicitly marked selected by the assembler.
    selected_keys = set()
    for entry in selection_log:
        if isinstance(entry, dict) and entry.get("action") == "selected":
            selected_keys.add(
                (entry.get("block_type"), entry.get("eid"), entry.get("chunk_id"))
            )

    # 2. Join against the ALREADY-SELECTED blocks; return only matching dicts.
    #    An item present in `blocks` but not marked selected is excluded; a
    #    selected key with no matching block dict yields nothing (we never
    #    fabricate an item from selection_log alone).
    out: List[Dict[str, Any]] = []
    for bt, items in blocks.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            key = (item.get("block_type", bt), item.get("eid"), item.get("chunk_id"))
            if key in selected_keys:
                out.append(item)
    return out
