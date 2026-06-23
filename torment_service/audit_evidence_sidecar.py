"""Pure composition helper for the model-API truthfulness/evidence audit lane.

This module composes the two already-proven pure stages of the audit-evidence
path into a single bounded packet, from EXPLICIT caller-supplied inputs only:

    selected admitted items   -> audit_evidence_context.selected_admitted_items
    admissible evidence packet -> audit_evidence_packet.build_audit_evidence_packet

Scope honesty (read carefully):
    * Pure composition helper. It is CALLED NOWHERE in production.
    * No sink is selected. There is no endpoint, AgentRunner, TurnResult, or
      ``/retrieve`` wiring here.
    * No model / evaluator / provider / prompt is invoked.
    * No persistence, no output control, no memory write.
    * It composes EXPLICIT caller-supplied halves only: a ``response_text`` (the
      audit subject) and either pre-extracted admitted items or an
      already-built ``AssembledContext``-like object the caller supplies. It
      performs NO retrieval and never calls ``assemble_context`` — the assembled
      context must be explicit caller-supplied input.
    * It does NOT prove that any live same-turn response was generated against
      the supplied assembled context; that response-generation / output-sink
      link remains a separate, unopened gate.

Caller-relationship note: once this module exists, ``audit_evidence_packet`` and
``audit_evidence_context`` are no longer literally "called nowhere" — they are
called ONLY by this pure composition helper, which is itself called nowhere. No
endpoint / AgentRunner / ``/retrieve`` / model / writer / persistence path calls
any of the three.

By construction this module imports only ``audit_evidence_context`` and
``audit_evidence_packet`` (plus ``__future__`` / ``typing``); it imports no
retrieval / assembler / fabric / app / agent_loop / model / provider / writer /
persistence / endpoint module.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .audit_evidence_context import selected_admitted_items
from .audit_evidence_packet import build_audit_evidence_packet


def build_audit_evidence_sidecar_from_items(
    response_text: str,
    admitted_context_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build the audit evidence packet from explicit caller-supplied items.

    Thin pure composition over ``build_audit_evidence_packet``. Returns the
    existing packet directly (no wrapper schema; no ``kind`` / ``version`` /
    ``packet`` keys). Performs no retrieval, no model call, no persistence;
    called nowhere in production.
    """
    return build_audit_evidence_packet(response_text, admitted_context_items)


def build_audit_evidence_sidecar_from_assembled_context(
    response_text: str,
    assembled_context: Any,
) -> Dict[str, Any]:
    """Build the audit evidence packet from an explicit caller-supplied
    ``AssembledContext`` (or AssembledContext-like) object.

    Extracts the assembler-SELECTED block dicts via ``selected_admitted_items``
    (no retrieval, no ``assemble_context`` call), then composes them through the
    item-based core. Returns the existing packet directly.

    The caller owns the §2/§5 same-turn obligation — that the supplied assembled
    context is the turn's admitted context. This helper makes no such claim,
    performs no wiring, and does not prove live same-turn response generation.
    """
    items = selected_admitted_items(assembled_context)
    return build_audit_evidence_sidecar_from_items(response_text, items)
