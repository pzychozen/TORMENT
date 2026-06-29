"""tests/manual/non_spine_llm_anthropic_provider_harness.py

Operator / manual harness for the gated Anthropic non-Spine real-provider adapter
(``AnthropicNonSpineLLMProviderAdapter``). It reaches a REAL provider ONLY when the explicit
env gate + credentials are set AND it is run as an operator CLI -- never under pytest. It is
not production-wired: no app / spine / mcp / cognition / role surface, no endpoint, no
memory write, no file output, no transcript, no log. It imports only stdlib plus
``torment_service.non_spine_llm_runtime`` and NEVER prints, stores, echoes, or returns the
API key.

Helper:
    run_non_spine_anthropic_provider_harness(...) builds
        AnthropicNonSpineLLMProviderAdapter(env=, sdk_factory=)
        -> FakeNonSpineLLMCompletionAdapter(provider_adapter=...)
        -> NonSpineLLMRuntime(adapter=...)
    -> runtime.run(request) -> NonSpineLLMRuntimeResult.

The real env gate / key / model / timeout are validated inside the adapter (fail-closed);
this harness only wires and runs. ``env`` and ``sdk_factory`` exist so tests can inject a
fake env + fake SDK and reach no real env / SDK / network.

CLI (main): argparse; refuses under pytest before constructing the adapter / contacting a
provider; prints only non-secret result text; exit codes 0 (success) / 2 (refused or
closed gate or provider failure) / 1 (malformed CLI args or unexpected error).

Run (operator, gated):
    set TORMENT_NON_SPINE_LLM_REAL_PROVIDER=1
    set ANTHROPIC_API_KEY=...            (local environment only)
    set TORMENT_NON_SPINE_ANTHROPIC_MODEL=claude-...
    python tests/manual/non_spine_llm_anthropic_provider_harness.py --user-input "hello"
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional, Tuple

from torment_service.non_spine_llm_runtime import (
    AnthropicNonSpineLLMProviderAdapter,
    FakeNonSpineLLMCompletionAdapter,
    NonSpineLLMRuntime,
    NonSpineLLMRuntimeRequest,
    NonSpineLLMRuntimeResult,
    NonSpineLLMRealProviderError,
)


def run_non_spine_anthropic_provider_harness(
    *,
    agent_id: str = "",
    user_input: str = "",
    system_text: str = "",
    memory_context_text: str = "",
    extra_messages: Tuple[str, ...] = (),
    env=None,
    sdk_factory=None,
) -> "NonSpineLLMRuntimeResult":
    """Build the gated Anthropic adapter stack and run one turn; return the result.

    Operator-/test-called only. ``env`` / ``sdk_factory`` default to ``None`` (the real
    adapter then resolves ``os.environ`` and lazily imports the real SDK only after its own
    gate / key / model / timeout validation). Tests pass a fake env mapping and a fake
    sdk_factory so no real env / SDK / network is touched. No file output, no transcript,
    no memory write; the API key is never printed or returned by this harness.
    """
    provider_adapter = AnthropicNonSpineLLMProviderAdapter(env=env, sdk_factory=sdk_factory)
    completion_adapter = FakeNonSpineLLMCompletionAdapter(
        provider_adapter=provider_adapter
    )
    runtime = NonSpineLLMRuntime(adapter=completion_adapter)
    request = NonSpineLLMRuntimeRequest(
        agent_id=agent_id,
        user_input=user_input,
        system_text=system_text,
        memory_context_text=memory_context_text,
        extra_messages=tuple(extra_messages),
    )
    return runtime.run(request)


def _pytest_active() -> bool:
    return "pytest" in sys.modules


def main(argv: Optional[list] = None) -> int:
    """Operator CLI. Exit 0 on success; 2 on refused / closed gate / provider failure;
    1 on malformed CLI args or unexpected error. Prints only non-secret text."""
    if _pytest_active():
        # Defensive refusal: never reach the real adapter / provider under pytest.
        print("refused: pytest detected; manual harness will not contact a provider")
        return 2

    parser = argparse.ArgumentParser(
        description="Manual operator harness for the gated Anthropic non-Spine adapter."
    )
    parser.add_argument("--agent-id", default="")
    parser.add_argument("--user-input", default="")
    parser.add_argument("--system-text", default="")
    parser.add_argument("--memory-context-text", default="")
    parser.add_argument("--extra-message", action="append", default=[])
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits 2 on bad args (normalize to 1); 0 on --help (preserve).
        return 1 if (exc.code or 0) != 0 else 0

    try:
        result = run_non_spine_anthropic_provider_harness(
            agent_id=args.agent_id,
            user_input=args.user_input,
            system_text=args.system_text,
            memory_context_text=args.memory_context_text,
            extra_messages=tuple(args.extra_message),
        )
    except NonSpineLLMRealProviderError as exc:
        # gate unset / missing key/model / bad timeout / SDK unavailable / provider error /
        # empty or malformed response. Fail closed. The adapter's message names env-var
        # KEYS only, never the secret value.
        print("refused / closed: %s" % exc)
        return 2
    except Exception:
        print("unexpected harness error")
        return 1

    # Print only the non-secret result text.
    print(result.response_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
