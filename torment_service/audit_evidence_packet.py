"""Pure packet-builder for the model-API truthfulness/evidence audit lane.

Implements the landed Admissible Evidence Packet Contract
(``docs/TORMENT_MODEL_API_TRUTHFULNESS_AUDIT_ADMISSIBLE_EVIDENCE_PACKET_CONTRACT_v0.1.md``)
for **explicit, caller-supplied inputs only**. It is a pure transform —
marker-based exclusion + caps + primitive-only projection.

IMPORTANT (scope honesty):
    This helper implements packet minimization for explicit caller-supplied
    inputs only. It does **not** prove the future caller supplied genuinely
    already-admitted response context — that source-of-context guarantee
    remains a later wiring gate. This module is CALLED NOWHERE in production.

By construction it performs:
    * NO retrieval, NO fresh query, NO raw-hit rebuild;
    * NO memory-graph / fabric / writer / persistence / model / provider /
      endpoint access (it imports none of those);
    * NO nested payload pass-through, NO new sensitivity schema.

Exclusion uses existing markers only: the lifecycle protected-marker reader
(canon / kind|type / tier / ``srg.is_crystal`` / ``governance.protected``) plus
direct reads of ``governance.non_shareable``, ``scope=="private"``,
``deep_memory``, and ``spirit_return_mode``.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .lifecycle import derive_protected_lifecycle_from_legacy_markers

# Caps from the Admissible Evidence Packet Contract (to be ratified).
MAX_ITEMS: int = 8
MAX_SNIPPET_CHARS: int = 240
MAX_TOTAL_SNIPPET_CHARS: int = 2000

# Primitive metadata fields copied verbatim from an admitted item IF present
# AND primitive. No other fields, and never a nested object, are projected.
_PRIMITIVE_META_FIELDS = ("eid", "lane", "source_class", "support_bucket")
_PRIMITIVE_TYPES = (str, int, float, bool)


def _is_sensitive(item: Dict[str, Any]) -> bool:
    """True if an admitted item carries any existing sensitivity marker.

    Fail-closed: anything not classifiable as clearly non-sensitive is excluded.
    """
    if not isinstance(item, dict):
        return True
    # Lifecycle protected markers: canon / kind|type / tier / srg.is_crystal /
    # governance.protected.
    try:
        if derive_protected_lifecycle_from_legacy_markers(item, now=0) is not None:
            return True
    except Exception:
        return True
    # governance.non_shareable (direct read; no governance import needed).
    gov = item.get("governance")
    if isinstance(gov, dict) and gov.get("non_shareable"):
        return True
    # scope == "private" (packet-contract exclusion marker; NOT a lifecycle marker).
    if item.get("scope") == "private":
        return True
    # deep / spirit-return markers.
    if item.get("deep_memory"):
        return True
    if item.get("spirit_return_mode"):
        return True
    return False


def _snippet(item: Dict[str, Any]) -> Optional[str]:
    raw = item.get("summary")
    if raw is None:
        raw = item.get("text")
    if raw is None:
        return None
    s = str(raw)
    if len(s) > MAX_SNIPPET_CHARS:
        s = s[:MAX_SNIPPET_CHARS]
    return s


def build_audit_evidence_packet(
    response_text: str,
    admitted_context_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build a bounded, primitive-only audit evidence packet from explicit
    caller-supplied inputs.

    Pure transform. Does not retrieve, rebuild from raw hits, access the memory
    graph, write, persist, or touch any output-control/review path. Does not
    prove the caller supplied genuinely already-admitted context.
    """
    items_out: List[Dict[str, Any]] = []
    total_snippet_chars = 0

    for item in (admitted_context_items or []):
        if len(items_out) >= MAX_ITEMS:
            break
        if not isinstance(item, dict):
            continue
        if _is_sensitive(item):
            continue

        entry: Dict[str, Any] = {}
        # Optional primitive metadata, copied only if already present + primitive.
        for f in _PRIMITIVE_META_FIELDS:
            if f in item:
                v = item[f]
                if v is None or isinstance(v, _PRIMITIVE_TYPES):
                    entry[f] = v
        # Optional bounded snippet, respecting per-item and total caps.
        snip = _snippet(item)
        if snip is not None:
            remaining = MAX_TOTAL_SNIPPET_CHARS - total_snippet_chars
            if remaining <= 0:
                snip = None
            elif len(snip) > remaining:
                snip = snip[:remaining]
            if snip:
                entry["snippet"] = snip
                total_snippet_chars += len(snip)
        items_out.append(entry)

    return {
        "response_text": str(response_text),
        "evidence_items": items_out,
    }
