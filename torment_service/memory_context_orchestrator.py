"""torment_service/memory_context_orchestrator.py

Internal, non-endpoint, DORMANT / test-called memory-to-prompt-for-generation
orchestrator (candidate 6).

This module is the OWNER OF ASSEMBLY for the same-turn memory-to-prompt path. In one
turn it:

  1. calls ``assemble_context(...)`` from ``retrieval_assembler`` as a FUNCTION (never via
     the ``/retrieve`` endpoint) to build a governed ``AssembledContext``;
  2. derives a BOUNDED, read-only memory-context string from the governed
     ``AssembledContext.assembled_text`` (``None`` when empty -> the runner stays
     memory-blind);
  3. invokes the authoritative ``AgentRunner.run_turn(..., memory_context_text=<text>)``.

``AgentRunner`` stays runner-local and owns NO assembly: THIS module -- not the runner --
imports/uses the assembler. The runner merely CONSUMES the optional bounded string through
its existing runner-local seam (``_execute_with_prompt_request`` ->
``_build_llm_prompt_request`` -> ``_build_memory_context_message``), which remains the
final owner of the cap (<=1200 chars) and the read-only guidance label.

Boundaries (deliberately narrow):
  - imports/uses ONLY ``retrieval_assembler`` (``assemble_context`` / ``AssembledContext``);
  - imports/calls NO ``app`` endpoints, NO ``PrivateGenerationOwner``, NO
    ``audit_selected_items_runner_bridge`` / ``selected_admitted_items`` / U1 / audit-owner
    route;
  - passes ONLY ``memory_context_text`` into ``run_turn`` -- NEVER
    ``audit_admitted_context_items`` -- so the memory lane stays disjoint from the audit
    lane (the approved selected-items bridge remains the only ``run_turn`` caller that
    passes audit items);
  - writes/persists NO memory and creates NO retrieval authority;
  - performs NO output-control / review / suppression / retry / ranking / style steering;
  - exposes the memory context on NO public surface (it is a local string only);
  - is CALLED NOWHERE in production (dormant / test-called only). Wiring a live production
    entrypoint is a SEPARATE, separately-authorized gate.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .retrieval_assembler import assemble_context, AssembledContext


def _memory_context_text_from_assembled_context(
    assembled_context: AssembledContext,
) -> Optional[str]:
    """Derive a bounded, read-only memory-context string from a governed
    ``AssembledContext``.

    The source is ONLY ``assembled_context.assembled_text`` (governed assembled context) --
    never raw hits, audit packets, private/unadmitted, or substrate-only content. The text
    is stripped; an empty result returns ``None`` so the runner stays memory-blind. The
    final cap and read-only label remain owned by the runner-local
    ``_build_memory_context_message``; this helper only strips and forwards governed text.
    """
    text = getattr(assembled_context, "assembled_text", "") or ""
    stripped = text.strip()
    if not stripped:
        return None
    return stripped


def run_turn_with_memory_context(
    runner: Any,
    *,
    workspace_id: str,
    agent_id: str,
    observation: Any,
    step: int,
    core_hits: List[Dict[str, Any]],
    archive_hits: Optional[List[Dict[str, Any]]] = None,
    profile: str = "companion",
    token_budget: int = 4000,
    seed_text: str = "",
    character_name: str = "",
    drift_info: Optional[Dict[str, Any]] = None,
    custom_weights: Optional[Dict[str, float]] = None,
):
    """Owner-of-assembly same-turn memory-to-prompt orchestrator (DORMANT / test-called).

    In ONE turn: (1) owns assembly by calling ``assemble_context(...)`` as a function to
    build a governed ``AssembledContext`` from the supplied retrieval inputs; (2) derives a
    bounded, read-only memory-context string from ``AssembledContext.assembled_text``
    (``None`` when empty -> memory-blind); (3) invokes the authoritative
    ``runner.run_turn(..., memory_context_text=<text>)``.

    Passes ONLY ``memory_context_text`` into ``run_turn`` -- never audit items. Returns the
    runner's ``TurnResult`` unchanged. Called nowhere in production.
    """
    assembled_context = assemble_context(
        core_hits=core_hits,
        archive_hits=archive_hits,
        profile=profile,
        token_budget=token_budget,
        seed_text=seed_text,
        character_name=character_name,
        drift_info=drift_info,
        custom_weights=custom_weights,
    )
    memory_context_text = _memory_context_text_from_assembled_context(assembled_context)
    return runner.run_turn(
        workspace_id=workspace_id,
        agent_id=agent_id,
        observation=observation,
        step=step,
        memory_context_text=memory_context_text,
    )
