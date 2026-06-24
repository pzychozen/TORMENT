"""Private, internal generation owner for the model-API evidence audit lane.

This is the first tiny PRODUCTION owner for design shape A
(`docs/TORMENT_AUDIT_PRIVATE_GENERATION_OWNER_PATH_DESIGN_v0.1.md`). It mirrors
the prior test-local harness in
`tests/test_audit_private_generation_owner_shape_characterization.py`.

It is PRIVATE / INTERNAL and called NOWHERE in production: it is exercised by
tests only. It is NOT wired into `app.py`, `agent_loop.py`, any endpoint, the
runtime, public schema/API, or persistence, and it does NOT expand
`AgentRunner`'s ownership.

What it does, in one frame it owns:
    1. Holds ONE explicit, caller-supplied `AssembledContext`.
    2. Extracts selected item dicts from that SAME object via the existing pure
       `selected_admitted_items` extractor.
    3. Renders and CAPTURES the exact model-visible prompt/messages it will send
       to generation (held locally in `self._captured`).
    4. Sends EXACTLY the captured prompt/messages to a caller-supplied generation
       boundary (`generation_boundary.complete(system_prompt=..., messages=...)`).
    5. After a final response exists, composes the observation-only packet via the
       existing inert `observe_prompt_inclusion_packet(...)` — which checks each
       selected item's text is present in the captured prompt/messages and returns
       the packet, or `None` when inclusion is not observed.

What it never does (by construction):
    * never passes the `AssembledContext` to the generation boundary or to
      `AgentRunner` — only selected item dicts feed the observer;
    * never returns, stores, logs, exposes, or places the captured prompt/messages
      in metadata — they stay local to the call frame;
    * never branches on the packet; packet presence/absence drives nothing and the
      response text is finalized before the packet is composed;
    * no persistence, no memory write, no writer path, no retrieval feedback, no
      ranking/suppression/retry/style steering, no review/output/ingest/fabric
      feedback, no database/substrate, no durable private cognition, no dream
      runtime, no Gate D, no Envelope Audit runtime, no endpoint/schema/API, no
      autonomy, and no audit-to-control feedback.

Import surface is closed: only `__future__` / `typing` / `dataclasses`, the pure
extractor (`audit_evidence_context.selected_admitted_items`), and the inert
observer (`audit_prompt_inclusion_observation.observe_prompt_inclusion_packet`).
The `generation_boundary` is duck-typed (any object exposing a compatible
`complete(*, system_prompt, messages)`); this module imports no model / provider /
endpoint / `agent_loop` / `retrieval_assembler` / writer / persistence code.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .audit_evidence_context import selected_admitted_items
from .audit_prompt_inclusion_observation import observe_prompt_inclusion_packet


@dataclass
class PrivateGenerationOwnerResult:
    """The owner's output. Exactly two fields — never the captured prompt/messages,
    never metadata."""
    response_text: str
    audit_evidence_packet: Optional[Dict[str, Any]]


class PrivateGenerationOwner:
    """Private generation owner. Holds one explicit `AssembledContext`, owns the
    exact model-visible prompt/messages it sends to a caller-supplied generation
    boundary, and composes an observation-only packet after generation. The
    captured prompt/messages stay local (`self._captured`) and are never returned,
    stored, logged, exposed, or placed in metadata. Called by tests only."""

    def __init__(self, assembled_context: Any, generation_boundary: Any):
        self._assembled = assembled_context      # one explicit context, in-frame
        self._gen = generation_boundary
        self._captured: Optional[Dict[str, Any]] = None   # private; never exposed

    def run(self, user_input: str) -> PrivateGenerationOwnerResult:
        # Extract selected item dicts from the SAME assembled context.
        selected = selected_admitted_items(self._assembled)
        # Render + capture the EXACT prompt/messages before generation.
        system_prompt = self._render_system_prompt(selected)
        messages = [{"role": "user", "content": user_input}]
        self._captured = {"system_prompt": system_prompt, "messages": messages}
        # Send EXACTLY the captured prompt/messages to generation.
        response_text = self._gen.complete(
            system_prompt=self._captured["system_prompt"],
            messages=self._captured["messages"],
        )
        # Compose the observation-only packet ONLY after a final response exists,
        # and ONLY when selected item text is present in the captured prompt.
        audit_packet = None
        if response_text:
            audit_packet = observe_prompt_inclusion_packet(
                system_prompt=self._captured["system_prompt"],
                messages=self._captured["messages"],
                admitted_context_items=selected,
                response_text=response_text,
            )
        # Return ONLY the response text + observation packet. Never the captured
        # prompt/messages; no metadata.
        return PrivateGenerationOwnerResult(
            response_text=response_text,
            audit_evidence_packet=audit_packet,
        )

    def _render_system_prompt(self, selected: List[Dict[str, Any]]) -> str:
        """Render the model-visible system prompt the owner sends to generation,
        including the selected item texts (the owner owns this context)."""
        lines = ["You are an agent."]
        for item in selected:
            text = item.get("text")
            if isinstance(text, str) and text:
                lines.append(text)
        return "\n".join(lines)
