"""torment_service/non_spine_llm_runtime.py

Dormant, internal, NON-Spine LLM runtime SKELETON (test-callable only).

This module is the named owner shape selected ON PAPER by the separate-LLM-runtime
direction-selection frame (docs-only). It is INERT: nothing in production instantiates
or calls it. It exists so a future, separately-authorized step has a concrete, fenced
skeleton to build against.

What it is:
  - a stdlib-only owner object (``NonSpineLLMRuntime``) plus an explicit input object
    (``NonSpineLLMRuntimeRequest``) and an explicit result object
    (``NonSpineLLMRuntimeResult``);
  - ``run(...)`` follows a FAKE, no-provider path only: it may render the intended
    prompt-shaped data into an in-memory string for tests, and it returns a fixed,
    no-op result object. There is no model/provider call.

What it is NOT (by construction):
  - not on the live Spine path; it references no Spine, cognition, or role surface;
  - no model/provider call of any kind; no external call; no network;
  - no retrieval; no assembly; no memory side effects; no persistence; no log output;
  - no endpoint, no MCP registration, no startup hook, no background loop;
  - inert at import time (no import-time side effects).

Live integration is a SEPARATE, separately-authorized gate and is not done here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class NonSpineLLMRuntimeRequest:
    """Explicit, primitive-only input object for the dormant runtime skeleton.

    Every field is a plain string or a tuple of strings. No repo object dependency.
    """

    agent_id: str = ""
    user_input: str = ""
    system_text: str = ""
    memory_context_text: str = ""
    extra_messages: Tuple[str, ...] = ()


@dataclass(frozen=True)
class NonSpineLLMRuntimeResult:
    """Explicit, fake / no-op result object.

    ``is_fake`` and ``provider_called`` make the dormant posture explicit and assertable.
    ``rendered_prompt`` holds the in-memory, prompt-shaped rendering used by tests only;
    it is never emitted anywhere.
    """

    response_text: str
    is_fake: bool
    provider_called: bool
    rendered_prompt: str


# Fixed, recognizable fake response. No model produced this string.
_FAKE_RESPONSE_TEXT = "[non_spine_llm_runtime: dormant fake no-op result]"


class NonSpineLLMRuntime:
    """Named internal owner of the dormant, non-Spine LLM runtime skeleton.

    Inert unless a test directly instantiates and calls it. Holds no resources, opens
    no connections, imports no provider SDK, and touches no repo runtime surface.
    """

    def __init__(self) -> None:
        # No resources, no connections, no side effects.
        self._fake_response_text: str = _FAKE_RESPONSE_TEXT

    @staticmethod
    def _render_prompt(request: "NonSpineLLMRuntimeRequest") -> str:
        """Render the intended prompt-shaped data into an in-memory string (tests only).

        Pure string composition. It performs no external call and produces no durable
        side effect; the rendered text exists only inside the returned result object.
        """
        parts: List[str] = []
        if request.system_text:
            parts.append("SYSTEM: " + request.system_text)
        if request.memory_context_text:
            parts.append(
                "MEMORY-CONTEXT (read-only guidance): " + request.memory_context_text
            )
        for message in request.extra_messages:
            parts.append("MSG: " + str(message))
        parts.append("USER: " + request.user_input)
        return "\n".join(parts)

    def run(self, request: "NonSpineLLMRuntimeRequest") -> "NonSpineLLMRuntimeResult":
        """Fake, no-provider execution path (test-callable only).

        Renders the intended prompt-shaped data in memory and returns a fixed no-op
        result. No model/provider is contacted; nothing is persisted.
        """
        rendered = self._render_prompt(request)
        return NonSpineLLMRuntimeResult(
            response_text=self._fake_response_text,
            is_fake=True,
            provider_called=False,
            rendered_prompt=rendered,
        )
