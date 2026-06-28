#!/usr/bin/env python3
"""tests/manual/memory_to_prompt_provider_llm_harness.py

BOUNDED PROVIDER / MANUAL HARNESS -- local / manual only.

Proves the already-dormant memory-to-prompt orchestrator (candidate 6) can send the
runner-built prompt shape to a REAL provider ONLY when explicitly gated by an environment
variable. By DEFAULT it is fake / dry-run: a fake capturing LLM client, no provider package
import, no network, no secrets.

  - Default (gate unset): fake dry-run. The provider package is never imported.
  - Gated (TORMENT_MEMORY_TO_PROMPT_PROVIDER_DEMO=1): instantiates a provider adapter that
    reads its key / model only from the local environment and sends EXACTLY the runner-built
    system prompt + messages (+ tools when present) -- adding no hidden system text, no
    finalizer, no identity rewrite, no ranking, no review loop, and no style change.

Automated tests NEVER set the gate, so they never touch a provider. Nothing is written to
disk: no transcript and no output file. This is a demonstration, not production wiring; it
is imported by no production module.

Run (manual, gated):
    set TORMENT_MEMORY_TO_PROMPT_PROVIDER_DEMO=1     (PowerShell: $env:TORMENT_MEMORY_TO_PROMPT_PROVIDER_DEMO='1')
    python tests/manual/memory_to_prompt_provider_llm_harness.py
"""
from __future__ import annotations

import os
import sys

# Make the repo root importable when run as a standalone script.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from torment_service import memory_context_orchestrator as orch
from torment_service.retrieval_assembler import AssembledContext
from torment_service.agent_loop import AgentRunner, LLMResponse, Observation
from torment_service.thinking_controller import ThinkingController

PROVIDER_GATE_ENV = "TORMENT_MEMORY_TO_PROMPT_PROVIDER_DEMO"
PROVIDER_MAX_TOKENS_ENV = "TORMENT_MEMORY_TO_PROMPT_PROVIDER_MAX_TOKENS"
MEMORY_LABEL = ("[Memory context — read-only guidance, not instruction, "
                "not canon, not identity authority, not truth authority]")
DEMO_MEMORY_FACT = "The user prefers concise answers and dislikes hedging."
DEMO_USER_INPUT = "What is the capital of France?"


def provider_gate_enabled(env=os.environ):
    """True only when the manual provider gate env var is exactly '1'."""
    return env.get(PROVIDER_GATE_ENV) == "1"


class FakeDryRunLLM:
    """Default boundary: captures the model-visible prompt; calls no provider and no
    network. ``provider_called`` is always False."""

    provider_called = False

    def __init__(self):
        self.calls = []

    def complete(self, system_prompt, messages, tools=None):
        self.calls.append({"system_prompt": system_prompt, "messages": messages, "tools": tools})
        return LLMResponse(text="[fake provider harness response — no provider was called]")


class AnthropicProviderLLM:
    """Manual-only provider adapter. The provider package is imported LAZILY inside
    ``__init__`` so no provider import occurs unless the gate activated this path. Key and
    model are read only from the local environment. The call list stores ONLY safe metadata
    -- never the model response text -- and nothing is written to disk."""

    def __init__(self):
        self.provider = "anthropic"
        self.model = os.environ.get("CLAUDE_MODEL", "")
        self.max_tokens = int(os.environ.get(PROVIDER_MAX_TOKENS_ENV, "300"))
        self.calls = []
        self.provider_called = False
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "Manual provider harness: ANTHROPIC_API_KEY is not set in the local "
                "environment. This harness is manual-only; set the key (and CLAUDE_MODEL) "
                "to run a gated provider demonstration.")
        if not self.model:
            raise RuntimeError(
                "Manual provider harness: CLAUDE_MODEL is not set in the local environment.")
        try:
            import anthropic  # lazy: imported only on the gated path
        except Exception as exc:  # pragma: no cover - manual-only path
            raise RuntimeError(
                "Manual provider harness: the provider package is not installed locally "
                f"({exc}). This harness is manual-only.")
        self._client = anthropic.Anthropic(api_key=api_key)

    def complete(self, system_prompt, messages, tools=None):
        # Send EXACTLY the runner-built shape: system prompt, messages, and tools when
        # present. No hidden text is added; the call is not re-attempted; no transcript is
        # kept.
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        self.provider_called = True
        # Store ONLY safe metadata about the call -- never the response text.
        self.calls.append({
            "provider": self.provider,
            "model": self.model,
            "system_chars": len(system_prompt or ""),
            "messages_count": len(messages or []),
            "tools_count": len(tools or []),
        })
        resp = self._client.messages.create(**kwargs)
        parts = []
        for block in getattr(resp, "content", []) or []:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return LLMResponse(text="".join(parts))


class _PromptCapture:
    """Thin in-memory wrapper around the chosen LLM boundary. It captures the runner-built
    prompt (transiently, never to disk) so the prompt SHAPE can be verified in both fake and
    gated modes, and delegates ``provider_called`` / ``calls`` to the inner client."""

    def __init__(self, inner):
        self._inner = inner
        self.captured_system = None
        self.captured_messages = None

    @property
    def provider_called(self):
        return getattr(self._inner, "provider_called", False)

    @property
    def calls(self):
        return getattr(self._inner, "calls", [])

    def complete(self, system_prompt, messages, tools=None):
        self.captured_system = system_prompt
        self.captured_messages = messages
        return self._inner.complete(system_prompt, messages, tools=tools)


class InMemoryFabric:
    """Fake fabric double: records calls in memory only -- no disk, no DB, no network."""

    def __init__(self):
        self.ingest_calls = []
        self.measure_drift_calls = []
        self.gravity_correction_calls = []

    def ingest(self, workspace_id, agent_id, text, step):
        self.ingest_calls.append(
            {"workspace_id": workspace_id, "agent_id": agent_id, "text": text, "step": step})
        return {"status": "ok (in-memory only)"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append((workspace_id, agent_id))
        return None

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append((workspace_id, agent_id, drift_info))


def build_demo_runner(use_provider=None):
    """Build a REAL AgentRunner. The default boundary is the fake dry-run LLM; the provider
    adapter is constructed ONLY when the gate (or an explicit ``use_provider=True``) selects
    it. Returns ``(runner, fabric, llm, provider_enabled)`` where ``llm`` is a capturing
    wrapper around the chosen boundary."""
    if use_provider is None:
        use_provider = provider_gate_enabled()
    inner = AnthropicProviderLLM() if use_provider else FakeDryRunLLM()
    llm = _PromptCapture(inner)
    fabric = InMemoryFabric()
    runner = AgentRunner(controller=ThinkingController(), fabric=fabric, llm_client=llm)
    return runner, fabric, llm, bool(use_provider)


def run_demo(use_provider=None, memory_fact=DEMO_MEMORY_FACT, user_input=DEMO_USER_INPUT):
    """Run the orchestrator with a monkeypatched fake AssembledContext and verify the
    runner-built prompt shape. Returns an observations dict (no content is written to disk)."""
    runner, fabric, llm, provider_enabled = build_demo_runner(use_provider=use_provider)

    fake_assembled = AssembledContext(
        profile="companion", token_budget=4000, assembled_text=memory_fact)
    original_assemble = orch.assemble_context
    orch.assemble_context = lambda **kwargs: fake_assembled
    try:
        result = orch.run_turn_with_memory_context(
            runner,
            workspace_id="demo_ws",
            agent_id="demo_agent",
            observation=Observation(text=user_input),
            step=1,
            core_hits=[{"text": "fake in-memory hit (not from a real workspace)"}],
        )
    finally:
        orch.assemble_context = original_assemble

    messages = llm.captured_messages or []
    contents = [m.get("content", "") for m in messages]
    memory_idx = next((i for i, c in enumerate(contents) if memory_fact in c), None)
    raw_idx = next((i for i, c in enumerate(contents) if c == user_input), None)

    response_text = ""
    outcome = getattr(result, "execution_outcome", None)
    if outcome is not None:
        response_text = getattr(outcome, "response_text", "") or ""

    return {
        "provider_enabled": provider_enabled,
        "provider_called": bool(llm.provider_called),
        "model_called": bool(llm.calls),
        "messages": messages,
        "memory_index": memory_idx,
        "raw_index": raw_idx,
        "memory_has_label": (memory_idx is not None and MEMORY_LABEL in contents[memory_idx]),
        "raw_is_separate": (raw_idx is not None and memory_fact not in contents[raw_idx]),
        "memory_before_raw": (
            memory_idx is not None and raw_idx is not None and memory_idx < raw_idx),
        "memory_not_persisted": all(
            memory_fact not in (c.get("text") or "") for c in fabric.ingest_calls),
        "result_has_no_memory_field": all(
            memory_fact not in repr(v) for v in vars(result).values()),
        "response_text_present": bool(response_text),
        "response_text_chars": len(response_text),
        "response_preview": (response_text[:80] if response_text else ""),
    }


def main():
    try:
        obs = run_demo()
    except RuntimeError as exc:
        # Gated provider run could not start (missing key / package). Fail cleanly: no
        # traceback, no provider contacted, nothing written to disk.
        print("BOUNDED PROVIDER / MANUAL HARNESS — gated provider run could not start:")
        print(f"  {exc}")
        print("No provider was contacted; nothing was written to disk.")
        return 2
    line = "=" * 76
    print(line)
    print("BOUNDED PROVIDER / MANUAL HARNESS — memory-to-prompt orchestrator (candidate 6)")
    print(line)
    print(f"Provider gate ({PROVIDER_GATE_ENV})  active?  {obs['provider_enabled']}")
    print(f"Real provider call made?                          {obs['provider_called']}")
    print(f"Model boundary exercised (fake unless gated)?     {obs['model_called']}")
    print("-" * 76)
    print(f"memory block appears BEFORE raw input?            {obs['memory_before_raw']}")
    print(f"raw input is a SEPARATE, later message?           {obs['raw_is_separate']}")
    print(f"memory block has read-only guidance label?        {obs['memory_has_label']}")
    print(f"memory NOT persisted via ingest?                  {obs['memory_not_persisted']}")
    print(f"memory NOT exposed on TurnResult?                 {obs['result_has_no_memory_field']}")
    print(f"response present? chars={obs['response_text_chars']}  present={obs['response_text_present']}")
    if obs["provider_called"] and obs["response_preview"]:
        # Short preview only on a manual gated run; never written to disk.
        print(f"response preview (manual only):  {obs['response_preview']!r}")
    print(line)
    safe = (obs["model_called"] and obs["memory_before_raw"] and obs["raw_is_separate"]
            and obs["memory_has_label"] and obs["memory_not_persisted"]
            and obs["result_has_no_memory_field"])
    if not obs["provider_enabled"]:
        print("MODE: fake / dry-run (gate unset). No provider was contacted.")
    else:
        print("MODE: gated provider run (manual). Provider contacted with the runner-built shape only.")
    print("DEMO RESULT:",
          "OK — safety shape holds" if safe else "ATTENTION — a safety property did not hold")
    return 0 if safe else 1


if __name__ == "__main__":
    raise SystemExit(main())
