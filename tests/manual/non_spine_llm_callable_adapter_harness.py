"""tests/manual/non_spine_llm_callable_adapter_harness.py

Test-only / operator-called MANUAL harness for exercising the callable non-Spine
provider adapter. It is NOT a production helper, NOT live-wired, and reads no SDK, env,
network, or secret. It imports ONLY the dormant non-Spine runtime classes; it touches no
production endpoint, governed Spine path, MCP, cognition, or role surface, and persists
nothing.

Wiring built by the helper:

    NonSpineLLMRuntimeRequest
        -> CallableNonSpineLLMProviderAdapter(completion_callable)
        -> FakeNonSpineLLMCompletionAdapter(provider_adapter=callable_adapter)
        -> NonSpineLLMRuntime(adapter=completion_adapter)
    -> runtime.run(request) -> NonSpineLLMRuntimeResult

The injected callable is operator-supplied; tests pass only fake / spy callables.
"""
from __future__ import annotations

from typing import Callable, Tuple

from torment_service.non_spine_llm_runtime import (
    NonSpineLLMRuntime,
    NonSpineLLMRuntimeRequest,
    NonSpineLLMRuntimeResult,
    CallableNonSpineLLMProviderAdapter,
    FakeNonSpineLLMCompletionAdapter,
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
    """Build the callable-adapter runtime stack from primitive inputs and run one turn.

    Operator-/test-called only. Builds a ``NonSpineLLMRuntimeRequest`` from the primitive
    inputs, wraps the injected callable in a ``CallableNonSpineLLMProviderAdapter``, hands
    that to a ``FakeNonSpineLLMCompletionAdapter`` as its provider adapter, drives a
    ``NonSpineLLMRuntime`` built on that completion adapter, and returns the runtime's
    ``NonSpineLLMRuntimeResult``. No provider SDK, network, env, or secret; nothing
    persisted.
    """
    request = NonSpineLLMRuntimeRequest(
        agent_id=agent_id,
        user_input=user_input,
        system_text=system_text,
        memory_context_text=memory_context_text,
        extra_messages=tuple(extra_messages),
    )
    callable_adapter = CallableNonSpineLLMProviderAdapter(completion_callable)
    completion_adapter = FakeNonSpineLLMCompletionAdapter(
        provider_adapter=callable_adapter
    )
    runtime = NonSpineLLMRuntime(adapter=completion_adapter)
    return runtime.run(request)
