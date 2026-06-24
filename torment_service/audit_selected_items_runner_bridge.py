"""Private, observation-only caller bridge: selected admitted items -> runner.

This is the FIRST authorized private bridge that forwards the assembler-SELECTED
admitted item dicts of an EXPLICIT, caller-supplied ``AssembledContext`` into
``AgentRunner.run_turn(..., audit_admitted_context_items=...)`` -- the existing
observation-only audit seam. Until this slice, no ``torment_service`` module
passed ``audit_admitted_context_items`` into ``run_turn`` (topology characterized
at ec17d2e: "none exist"). This module is the single, narrowly-scoped exception;
its sole new edge is selected-items -> the inert observation seam.

Doctrine it preserves (verbatim):
    Memory may shape context. Memory may not seize authority.
    Audit observes authority. Audit must not become authority.

What it does -- and ONLY this:
    1. Reads the assembler-SELECTED block dicts from the SAME caller-supplied
       ``assembled_context`` via the pure ``selected_admitted_items`` extractor
       (no retrieval, no ``assemble_context`` call, no ``assembled_text`` parse,
       no mutation of the input).
    2. Forwards ONLY those extracted selected item dicts as
       ``audit_admitted_context_items`` -- never the whole ``AssembledContext``.
    3. Returns ``run_turn``'s ``TurnResult`` unchanged.

What it MUST NOT do -- by construction:
    * No retrieval / ranking / scoring; it consumes a context the caller already
      assembled and for which the caller owns the same-turn obligation.
    * No prompt-path injection: forwarded items reach ONLY the inert observation
      seam; ``run_turn`` itself keeps them out of cognition / prompt / review /
      ingest / fabric / writer / model-visible context.
    * No read-back of the result's audit evidence packet, and no feeding of
      packet presence or absence into retrieval / ranking / output / review /
      retry / style / control. The bridge returns the result and inspects
      nothing on it.
    * No packet build, no persistence, no memory write, no endpoint, no schema,
      no public API, no new ``TurnResult`` field, no captured-prompt exposure.
    * No claim that the supplied context is the turn's admitted context -- the
      caller owns that obligation; this bridge makes no such claim and confers
      no control.

Import surface is closed: only ``__future__`` / ``typing`` and the pure
``audit_evidence_context.selected_admitted_items`` extractor. It imports no
assembler / fabric / app / agent_loop / model / provider / writer / persistence /
endpoint / schema module, and duck-types ``runner`` (any object exposing a
compatible ``run_turn``). It is called nowhere in production (observation-only).
"""
from __future__ import annotations

from typing import Any

from .audit_evidence_context import selected_admitted_items


def run_turn_with_selected_items_observation(
    runner: Any,
    assembled_context: Any,
    *,
    workspace_id: str,
    agent_id: str,
    observation: Any,
    step: int,
) -> Any:
    """Forward the SELECTED admitted item dicts of ``assembled_context`` into the
    runner's observation-only audit seam and return its ``TurnResult``.

    Pure adapter. Extracts the assembler-SELECTED block dicts from the SAME
    caller-supplied ``assembled_context`` (no retrieval, no mutation) and passes
    ONLY those dicts as ``audit_admitted_context_items`` -- never the whole
    ``AssembledContext``. Reads nothing back off the result and routes nothing
    anywhere. The caller owns the same-turn obligation for ``assembled_context``;
    this bridge makes no such claim and confers no control.
    """
    selected_items = selected_admitted_items(assembled_context)
    return runner.run_turn(
        workspace_id=workspace_id,
        agent_id=agent_id,
        observation=observation,
        step=step,
        audit_admitted_context_items=selected_items,
    )
