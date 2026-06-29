"""tests/manual/non_spine_llm_callable_adapter_harness.py

Test-only / operator-called MANUAL harness for exercising the callable non-Spine
provider adapter. It is NOT a production helper, NOT live-wired, and reads no SDK, env,
network, or secret. It imports ONLY the dormant non-Spine runtime; it touches no
production endpoint, governed Spine path, MCP, cognition, or role surface, and persists
nothing.

As of this slice the harness DELEGATES to the production-internal helper
``run_non_spine_callable_provider_manual(...)`` rather than duplicating the wiring; it
remains a test/operator harness, not production behavior.
"""
from __future__ import annotations

from typing import Callable, Tuple

from torment_service.non_spine_llm_runtime import (
    NonSpineLLMRuntimeResult,
    run_non_spine_callable_provider_manual,
)


def run_non_spine_callable_provider_harness(
    completion_callable: "Callable",
    *,
    agent_id: str = "",
    user_input: str = "",
    system_text: str = "",
    memory_context_text: str = "",
    extra_messages: Tuple[str, ...] = (),
) -> "NonSpineLLMRuntimeResult":
    """Delegate to the production-internal manual helper and return its result.

    Operator-/test-called only. The wiring (request -> callable provider adapter ->
    fake completion adapter -> runtime -> run) lives in
    ``run_non_spine_callable_provider_manual``; this harness just forwards primitive
    inputs and the injected callable. No provider SDK, network, env, or secret; nothing
    persisted.
    """
    return run_non_spine_callable_provider_manual(
        completion_callable,
        agent_id=agent_id,
        user_input=user_input,
        system_text=system_text,
        memory_context_text=memory_context_text,
        extra_messages=tuple(extra_messages),
    )
