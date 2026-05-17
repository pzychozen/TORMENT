#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
examples/agent_runner_demo.py — AgentRunner validation pass.

Exercises the v0.1 proof slice's runtime surfaces against a live
TORMENT service and a real LLM client. Five scripted scenarios
demonstrate the full 8-phase outer loop with the
DEBUGGING_SESSION_PACK active. An optional interactive mode at the
end lets you probe further by typing free-form observations.

This is the first-party validation tool for the proof slice.
Reference: docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md (ratified)
and tag v2.4.6-proof-slice-complete.

Scenarios:
    1. Normal answer turn — expects ANSWER, LLM called once.
    2. Governance-sensitive turn — expects GOVERNANCE_REVIEW routing.
    3. High-drift reflex turn — expects drift veto + zero LLM calls.
    4. Retrieval probe — expects NON-tool (v0.1.0d unmapped retrieval).
    5. Analytical probe — expects NON-tool, REFLECTIVE (v0.1.0d).
    6. Execution probe — expects TOOL + code_exec narrowing (v0.1.0d).

Requirements:
    - TORMENT service running at http://127.0.0.1:8787
    - ANTHROPIC_API_KEY environment variable set
    - anthropic package installed (pip install anthropic)
    - requests package installed

Usage:
    py -3 examples/agent_runner_demo.py
    py -3 examples/agent_runner_demo.py --interactive
    py -3 examples/agent_runner_demo.py --scenario 3
    py -3 examples/agent_runner_demo.py --workspace my_ws --agent my_agent
    py -3 examples/agent_runner_demo.py --pack research --scenario 6
    py -3 examples/agent_runner_demo.py --pack debugging --scenario 6

Live pack-composability probe (v0.1.1):
    Run Scenario 6 under both --pack debugging and --pack research.
    Under 'debugging', the execution query narrows to code_exec and
    executes. Under 'research', the same query downgrades cleanly to
    DEFER because EMPTY_CONTRACT — no tool family exists yet, but the
    runtime stays coherent. This contrast is the live proof of
    "declared capability absent, system still behaves coherently."
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import os
import sys
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

_log = logging.getLogger("agent_runner_demo")


# ---------------------------------------------------------------------------
# .env loader (mirror of character_chat_probe._load_dotenv_safely)
# ---------------------------------------------------------------------------


def _load_dotenv_safely() -> List[str]:
    """Best-effort .env loader.

    Reads `torment_fabric/.env` (sibling-of-examples) and `./.env`
    (cwd) if they exist. Does NOT override existing environment
    variables — explicit shell/CI exports take precedence. Quoted
    values are unwrapped; lines starting with '#' are ignored.

    Returns the list of paths actually read (for an info log line).
    Mirrors the pattern in examples/character_chat_probe.py so the
    demo can read the same .env that the chat probe uses.
    """
    candidates: List[Path] = []
    here = Path(__file__).resolve()
    candidates.append(here.parent.parent / ".env")  # torment_fabric/.env
    candidates.append(Path.cwd() / ".env")          # cwd/.env

    loaded_paths: List[str] = []
    seen: set = set()
    for path in candidates:
        try:
            resolved = path.resolve()
        except Exception:
            continue
        if resolved in seen or not resolved.exists() or not resolved.is_file():
            continue
        seen.add(resolved)
        try:
            with open(resolved, "r", encoding="utf-8") as fh:
                for raw_line in fh:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                        value = value[1:-1]
                    if not key:
                        continue
                    if key in os.environ and os.environ[key]:
                        continue
                    os.environ[key] = value
            loaded_paths.append(str(resolved))
        except Exception as e:
            _log.debug(".env load skipped for %s: %s", resolved, e)
    return loaded_paths


# Load .env *before* reading any env-derived constants below.
_DOTENV_LOADED = _load_dotenv_safely()

# Ensure the project root is importable when run from examples/.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from torment_service.agent_loop import (  # noqa: E402
    AgentRunner,
    LLMResponse,
    Observation,
    ToolCall,
    TurnResult,
)
from torment_service.behavior_packs import (  # noqa: E402
    DEBUGGING_SESSION_PACK,
    RESEARCH_ASSISTANT_PACK,
)
from torment_service.thinking_controller import ThinkingController  # noqa: E402


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_TORMENT_URL = os.environ.get("TORMENT_URL", "http://127.0.0.1:8787").rstrip("/")
DEFAULT_WORKSPACE = os.environ.get("TORMENT_WORKSPACE", "ws_agent_runner_demo")
DEFAULT_AGENT = os.environ.get("TORMENT_AGENT", "agent_demo")
DEFAULT_CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
DEFAULT_OPENROUTER_MODEL = os.environ.get(
    "OPENROUTER_MODEL", "google/gemini-2.5-flash"
)
_OPENROUTER_BASE_URL = os.environ.get(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
).rstrip("/")


# ---------------------------------------------------------------------------
# FabricHandle adapter — HTTP + drift override support
# ---------------------------------------------------------------------------


@dataclass
class HTTPFabricAdapter:
    """FabricHandle implementation for the demo.

    `ingest` hits the real TORMENT /agent/ingest endpoint.
    `measure_drift` reads from /agent/{id}/character/state unless a
    scenario has set drift_override (scenario 3 uses this to force
    high drift without actually needing a drifted agent).
    `gravity_correction` is a no-op in the demo — it logs what would
    have happened. Production wiring is v0.1.0a.
    """
    base_url: str
    # Scenario 3 sets this to simulate high drift without requiring
    # a genuinely drifted agent. Leave None for real drift measurement.
    drift_override: Optional[Dict[str, Any]] = None

    # Observability: record every call for the turn summary.
    ingest_calls: List[Dict[str, Any]] = field(default_factory=list)
    measure_drift_calls: List[Dict[str, Any]] = field(default_factory=list)
    gravity_correction_calls: List[Dict[str, Any]] = field(default_factory=list)

    def ingest(self, workspace_id: str, agent_id: str, text: str, step: int) -> Dict[str, Any]:
        self.ingest_calls.append({"step": step, "text_len": len(text)})
        try:
            r = requests.post(
                f"{self.base_url}/agent/ingest",
                json={
                    "workspace_id": workspace_id,
                    "agent_id": agent_id,
                    "text": text,
                    "step": step,
                },
                timeout=30,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            # Best-effort: the runner is already designed to tolerate
            # ingest failures. Surface the error to stderr for visibility.
            print(f"  [fabric.ingest error: {e}]", file=sys.stderr)
            return {"status": "error", "error": str(e)}

    def measure_drift(
        self, workspace_id: str, agent_id: str
    ) -> Optional[Dict[str, Any]]:
        self.measure_drift_calls.append({})
        if self.drift_override is not None:
            # Scenario 3: simulated drift. Note explicitly.
            return dict(self.drift_override)
        try:
            r = requests.get(
                f"{self.base_url}/agent/{agent_id}/character/state",
                params={"workspace_id": workspace_id},
                timeout=10,
            )
            r.raise_for_status()
            state = r.json()
            # The character state endpoint returns various fields; map
            # to the DriftRegime shape the runner expects.
            return {
                "drift_score": float(state.get("drift_score", 0.0)),
                "drift_direction": str(state.get("drift_direction", "unknown")),
            }
        except Exception as e:
            # If the agent isn't set up, we can't measure. Degrade to
            # None (runner tolerates this).
            print(f"  [fabric.measure_drift: {e}; returning None]", file=sys.stderr)
            return None

    def gravity_correction(
        self, workspace_id: str, agent_id: str, drift_info: Dict[str, Any]
    ) -> None:
        """Demo stub. v0.1.0a will replace this with a real call."""
        self.gravity_correction_calls.append({"drift_info": drift_info})
        print(
            f"  [fabric.gravity_correction would fire: "
            f"drift_score={drift_info.get('drift_score'):.2f} "
            f"direction={drift_info.get('drift_direction')!r}]"
        )


# ---------------------------------------------------------------------------
# LLMClient adapter — Anthropic
# ---------------------------------------------------------------------------


@dataclass
class AnthropicLLMAdapter:
    """LLMClient implementation wrapping the Anthropic SDK.

    The `tools` parameter is honored: when present, it's passed
    through as Anthropic's tools= array so the model sees exactly
    the narrowed signature from Phase 5 (invariant 2).
    """
    api_key: str
    model: str = DEFAULT_CLAUDE_MODEL
    max_tokens: int = 800

    # Observability: record every call.
    calls: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        try:
            import anthropic
        except ImportError:
            raise RuntimeError(
                "anthropic package is required for this demo. "
                "Install with: py -3 -m pip install anthropic"
            )
        self._anthropic = anthropic
        self._client = anthropic.Anthropic(api_key=self.api_key)

    def complete(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        call_record = {
            "tools_count": len(tools) if tools else 0,
            "tool_names": [t.get("name") for t in tools] if tools else [],
            "system_chars": len(system_prompt),
            "messages_count": len(messages),
            "wall_ms": 0,  # filled in after the SDK call returns
        }
        self.calls.append(call_record)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        _call_started = time.time()
        try:
            resp = self._client.messages.create(**kwargs)
        except Exception as e:
            call_record["wall_ms"] = int((time.time() - _call_started) * 1000)
            return LLMResponse(text=f"[LLM call failed: {e}]")
        call_record["wall_ms"] = int((time.time() - _call_started) * 1000)

        # v0.1.0c: separate text blocks from tool_use blocks so the
        # runner can extract ToolCall objects cleanly.
        text_parts: List[str] = []
        tool_calls: List[ToolCall] = []
        for block in resp.content:
            btype = getattr(block, "type", None)
            if btype == "text":
                text_parts.append(block.text)
            elif btype == "tool_use":
                tool_calls.append(ToolCall(
                    tool_name=block.name,
                    arguments=dict(block.input) if block.input else {},
                    tool_use_id=getattr(block, "id", None),
                ))
        return LLMResponse(
            text="\n".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=getattr(resp, "stop_reason", None),
        )


# ---------------------------------------------------------------------------
# LLMClient adapter — OpenRouter (OpenAI-compatible)
# ---------------------------------------------------------------------------


@dataclass
class OpenRouterLLMAdapter:
    """LLMClient implementation for OpenRouter's OpenAI-compatible API.

    Default model is `google/gemini-2.5-flash`. Used by the long-
    iteration test rig for Tier 0/1/2 to keep LLM cost down vs.
    Anthropic-direct. Tier 3 (endurance) may switch back to Anthropic
    if needed.

    Implements the same `complete(system, messages, tools)` shape as
    AnthropicLLMAdapter so AgentRunner doesn't know or care which
    provider is wired. Tools are converted Anthropic→OpenAI on the
    way in and OpenAI tool_calls→TORMENT ToolCall on the way out, so
    Phase 5 narrowing on the runtime side stays unchanged.

    Uses the `openai` Python SDK when available; falls back to raw
    requests otherwise. Mirrors the chat-probe convention.
    """
    api_key: str
    model: str = DEFAULT_OPENROUTER_MODEL
    base_url: str = _OPENROUTER_BASE_URL
    max_tokens: int = 800

    # Observability: record every call (parity with AnthropicLLMAdapter).
    calls: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        self._sdk = None
        try:
            from openai import OpenAI  # type: ignore
            self._sdk = OpenAI(base_url=self.base_url, api_key=self.api_key)
        except ImportError:
            _log.debug(
                "openai SDK not installed; OpenRouterLLMAdapter will use "
                "raw requests for /chat/completions."
            )

    # -- format converters --------------------------------------------------

    @staticmethod
    def _anthropic_tools_to_openai(
        tools: Optional[List[Dict[str, Any]]],
    ) -> Optional[List[Dict[str, Any]]]:
        """Convert Anthropic tool schema (what TORMENT Phase 5 emits) to
        OpenAI tool schema (what OpenRouter / OpenAI-compatible APIs
        expect). Anthropic uses `input_schema`; OpenAI uses
        `parameters` wrapped in `{type: "function", function: {...}}`.
        """
        if not tools:
            return None
        converted: List[Dict[str, Any]] = []
        for t in tools:
            converted.append({
                "type": "function",
                "function": {
                    "name": t.get("name"),
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object"}),
                },
            })
        return converted

    @staticmethod
    def _openai_tool_calls_to_torment(
        oai_tool_calls: Optional[List[Any]],
    ) -> List[ToolCall]:
        """Convert OpenAI/OpenRouter `tool_calls` (list of objects with
        id/type/function.name/function.arguments) to TORMENT ToolCall
        objects. `arguments` arrives as a JSON-encoded string; parse
        it best-effort and surface raw text on parse failure so the
        runner can still see what the model attempted to send.

        Tolerates both SDK objects (attribute access via the openai
        SDK) and plain dicts (raw HTTP fallback path), since the two
        provider paths return different shapes.
        """
        result: List[ToolCall] = []
        if not oai_tool_calls:
            return result
        for tc in oai_tool_calls:
            if isinstance(tc, dict):
                fn = tc.get("function") or {}
                name = fn.get("name") if isinstance(fn, dict) else None
                args_raw = fn.get("arguments") if isinstance(fn, dict) else None
                tool_use_id = tc.get("id")
            else:
                fn = getattr(tc, "function", None)
                if fn is None:
                    continue
                name = getattr(fn, "name", None)
                args_raw = getattr(fn, "arguments", None)
                tool_use_id = getattr(tc, "id", None)
            try:
                arguments = json.loads(args_raw) if isinstance(args_raw, str) else (args_raw or {})
            except Exception:
                arguments = {"_raw": args_raw}
            result.append(ToolCall(
                tool_name=name,
                arguments=dict(arguments) if isinstance(arguments, dict) else {"_value": arguments},
                tool_use_id=tool_use_id,
            ))
        return result

    # -- LLMClient protocol -------------------------------------------------

    def complete(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        call_record = {
            "tools_count": len(tools) if tools else 0,
            "tool_names": [t.get("name") for t in tools] if tools else [],
            "system_chars": len(system_prompt),
            "messages_count": len(messages),
            "wall_ms": 0,
        }
        self.calls.append(call_record)

        oai_tools = self._anthropic_tools_to_openai(tools)
        oai_messages = [{"role": "system", "content": system_prompt}] + messages

        _started = time.time()
        try:
            if self._sdk is not None:
                kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "messages": oai_messages,
                    "max_tokens": self.max_tokens,
                }
                if oai_tools:
                    kwargs["tools"] = oai_tools
                resp = self._sdk.chat.completions.create(**kwargs)
                call_record["wall_ms"] = int((time.time() - _started) * 1000)
                msg = resp.choices[0].message
                text = msg.content or ""
                tool_calls = self._openai_tool_calls_to_torment(
                    getattr(msg, "tool_calls", None)
                )
                stop_reason = getattr(resp.choices[0], "finish_reason", None)
                return LLMResponse(
                    text=text,
                    tool_calls=tool_calls,
                    stop_reason=stop_reason,
                )

            # Raw-requests fallback.
            payload: Dict[str, Any] = {
                "model": self.model,
                "messages": oai_messages,
                "max_tokens": self.max_tokens,
            }
            if oai_tools:
                payload["tools"] = oai_tools
            r = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60,
            )
            call_record["wall_ms"] = int((time.time() - _started) * 1000)
            r.raise_for_status()
            data = r.json()
            choices = data.get("choices") or []
            if not choices:
                return LLMResponse(text=f"[OpenRouter returned no choices: {json.dumps(data)[:300]}]")
            msg = (choices[0] or {}).get("message", {}) or {}
            text = msg.get("content") or ""
            tool_calls = self._openai_tool_calls_to_torment(msg.get("tool_calls"))
            stop_reason = (choices[0] or {}).get("finish_reason")
            return LLMResponse(
                text=text,
                tool_calls=tool_calls,
                stop_reason=stop_reason,
            )
        except Exception as e:
            call_record["wall_ms"] = int((time.time() - _started) * 1000)
            return LLMResponse(text=f"[LLM call failed: {e}]")


# Type alias used by main() — either provider exposes the LLMClient
# protocol (complete(system, messages, tools) -> LLMResponse).
LLMAdapter = Any


# ---------------------------------------------------------------------------
# ToolExecutor stub
# ---------------------------------------------------------------------------


@dataclass
class StubToolExecutor:
    """Demo tool executor. Echoes arguments; does NOT execute real
    code. A hardened subprocess sandbox is v0.1.0b.
    """
    calls: List[Dict[str, Any]] = field(default_factory=list)

    def execute(
        self,
        family: str,
        arguments: Dict[str, Any],
        defaults: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.calls.append(
            {"family": family, "arguments": arguments, "defaults": defaults}
        )
        return {
            "output": f"[stub executor for {family}]: "
            f"args={arguments}, defaults={defaults}",
            "exit_code": 0,
            "stub": True,
        }


# ---------------------------------------------------------------------------
# Turn-result formatting
# ---------------------------------------------------------------------------


def summarize_turn(result: TurnResult, llm: AnthropicLLMAdapter) -> str:
    """Format a TurnResult for human inspection."""
    policy = result.action_policy_decision
    lines = []
    lines.append(f"  Mode: {result.mode_decision.chosen_mode.value}")
    lines.append(f"  Phase 4 intent (pre-policy): {result.action_decision.action.value}")
    lines.append(f"  Phase 5 effective action: {policy.action.action.value}")
    if policy.original_action_type is not None:
        lines.append(
            f"  Phase 5 downgrade: {policy.original_action_type.value} "
            f"-> {policy.action.action.value} ({policy.fallback_reason})"
        )
    if policy.drift_veto_applied:
        lines.append(f"  Drift veto applied: YES")
    if policy.tool_family_narrowed:
        lines.append(f"  Tool family narrowed: {policy.tool_family_narrowed}")
    lines.append(
        f"  LLM calls this turn: {len(llm.calls)}"
    )
    if llm.calls:
        last = llm.calls[-1]
        if last["tools_count"]:
            lines.append(
                f"    LLM saw {last['tools_count']} tool(s): {last['tool_names']}"
            )
    lines.append(
        f"  Execution: llm_called={result.execution_outcome.llm_called} "
        f"tool_called={result.execution_outcome.tool_called} "
        f"no_op={result.execution_outcome.no_op}"
    )
    # v0.1.0c: print tool_result details when present so post-0c
    # validation can see executor failures / exit codes / output
    # at a glance.
    tool_result = result.execution_outcome.tool_result
    if tool_result is not None:
        err = tool_result.get("error")
        if err is not None:
            lines.append(f"  Tool result error: {err}")
        exit_code = tool_result.get("exit_code")
        if exit_code is not None:
            lines.append(f"  Tool result exit_code: {exit_code}")
        out = tool_result.get("output") or ""
        if out:
            lines.append(
                f"  Tool result output (first 120 chars): "
                f"{out[:120].replace(chr(10), ' ')}"
            )
    if result.execution_outcome.response_text:
        snippet = result.execution_outcome.response_text[:200].replace("\n", " ")
        lines.append(f"  Response (first 200 chars): {snippet}")
    lines.append(
        f"  Review: approved={result.review_outcome.approved} "
        f"revised={result.review_outcome.revised} "
        f"blocked={result.review_outcome.blocked}"
    )
    lines.append(f"  Ingest attempted: {result.ingest_attempted}")
    if result.drift_after_stabilize:
        lines.append(
            f"  Drift at Phase 8: "
            f"{result.drift_after_stabilize.get('drift_score')}/"
            f"{result.drift_after_stabilize.get('drift_direction')}"
        )
    lines.append(f"  Gravity correction applied: {result.gravity_correction_applied}")
    lines.append(
        f"  Assimilation outcomes emitted: "
        f"{[a.value for a in result.assimilation_outcomes] or 'none'}"
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Structured JSONL telemetry (machine-readable channel)
# ---------------------------------------------------------------------------


TELEMETRY_SCHEMA_VERSION = "agent_runner_demo_jsonl_v0.1"
_RESPONSE_OUTPUT_TRUNCATE_CHARS = 240


def _safe_to_dict(obj: Any) -> Optional[Dict[str, Any]]:
    """Return obj.to_dict() if obj exposes one, else None.

    Defensive: a missing review_outcome or sub-component should not
    crash telemetry emission. Returns None on absence; downstream
    JSONL consumers treat None as "field not produced this turn".
    """
    if obj is None:
        return None
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return None


def _truncate_tool_result(tool_result: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Defensive copy of tool_result with `output` truncated.

    Leaves all other keys intact so executor-specific signals
    (exit_code, stub, truncated, timed_out, etc.) pass through.
    Never mutates the original dict.
    """
    if tool_result is None:
        return None
    cleaned = dict(tool_result)
    out = cleaned.get("output")
    if isinstance(out, str) and len(out) > _RESPONSE_OUTPUT_TRUNCATE_CHARS:
        cleaned["output"] = out[:_RESPONSE_OUTPUT_TRUNCATE_CHARS]
        cleaned["output_truncated_by_demo"] = True
    return cleaned


def _emit_telemetry_jsonl(
    result: TurnResult,
    llm: Any,
    fabric: HTTPFabricAdapter,
    executor: Any,
    scenario: Scenario,
    pack_label: str,
    real_executor: bool,
    turn_wall_ms: int,
    is_reflex_path: bool,
    step: int,
    workspace_id: str,
    agent_id: str,
    out_path: str,
    llm_provider: str = "anthropic",
) -> None:
    """Append one structured JSONL row describing this turn.

    Schema is intentionally additive: each top-level key is a stable
    field name. Sub-objects use their `.to_dict()` where available.
    Fields absent on a given turn appear as null rather than missing
    keys, so downstream consumers can rely on a fixed shape.

    A JSONL-emit failure is logged to stderr but never raised — the
    demo's primary contract is the scenario run itself, not the
    telemetry channel. The wrapper is responsible for noticing
    missing/empty rows.
    """
    try:
        policy = result.action_policy_decision
        exec_out = result.execution_outcome
        response_text = exec_out.response_text or ""

        # AnthropicLLMAdapter.calls records are already small dicts of
        # ints and short string lists; safe to embed directly. No
        # secrets in those records (the api_key lives on the adapter
        # instance, not in `calls`).
        llm_calls_safe = list(llm.calls)
        llm_wall_ms_total = sum(int(c.get("wall_ms", 0) or 0) for c in llm_calls_safe)

        # Aggregate observability counts from the demo's existing
        # adapter call lists. Tool executor `calls` may or may not be
        # present depending on which executor is wired.
        executor_calls_count = 0
        executor_calls_attr = getattr(executor, "calls", None)
        if isinstance(executor_calls_attr, list):
            executor_calls_count = len(executor_calls_attr)

        row: Dict[str, Any] = {
            "telemetry_schema": TELEMETRY_SCHEMA_VERSION,
            "run_source": "agent_runner_demo",
            "scenario_number": scenario.number,
            "scenario_title": scenario.title,
            "is_reflex_path": is_reflex_path,
            "drift_override": dict(scenario.drift_override) if scenario.drift_override else None,
            "step": step,
            "wall_started_at": _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "turn_wall_ms": turn_wall_ms,
            "pack_label": pack_label,
            "llm_provider": llm_provider,
            "llm_model": getattr(llm, "model", None),
            "real_executor": real_executor,
            "workspace_id": workspace_id,
            "agent_id": agent_id,

            "task_frame": _safe_to_dict(result.task_frame),
            "mode_decision": _safe_to_dict(result.mode_decision),
            "memory_plan": _safe_to_dict(result.memory_plan),
            "action_decision": _safe_to_dict(result.action_decision),
            "action_policy_decision": {
                "effective_action": policy.action.action.value,
                "original_action_type": (
                    policy.original_action_type.value
                    if policy.original_action_type is not None
                    else None
                ),
                "fallback_reason": policy.fallback_reason,
                "drift_veto_applied": bool(policy.drift_veto_applied),
                "tool_family_narrowed": policy.tool_family_narrowed,
            },
            "execution_outcome": {
                "llm_called": bool(exec_out.llm_called),
                "tool_called": bool(exec_out.tool_called),
                "no_op": bool(exec_out.no_op),
                "has_response_text": bool(exec_out.response_text),
                # NB: response_text itself is intentionally NOT emitted.
                # Only its length, to avoid leaking model output content
                # into telemetry. Plan §1.5 W7 redaction is a wrapper
                # responsibility; this is defense in depth.
                "response_text_chars": len(response_text),
                "tool_result": _truncate_tool_result(exec_out.tool_result),
            },
            "review_outcome": _safe_to_dict(result.review_outcome),
            "assimilation_outcomes": [a.value for a in result.assimilation_outcomes],
            "drift_after_stabilize": (
                dict(result.drift_after_stabilize)
                if result.drift_after_stabilize
                else None
            ),
            "gravity_correction_applied": bool(result.gravity_correction_applied),
            "ingest_attempted": bool(result.ingest_attempted),
            "turn_result_metadata": dict(result.metadata) if result.metadata else {},

            "observability": {
                "llm_calls": len(llm_calls_safe),
                "llm_call_records": llm_calls_safe,
                "llm_wall_ms": llm_wall_ms_total,
                "fabric_ingest_calls": len(fabric.ingest_calls),
                "fabric_measure_drift_calls": len(fabric.measure_drift_calls),
                "fabric_gravity_correction_calls": len(fabric.gravity_correction_calls),
                "executor_calls": executor_calls_count,
            },
        }

        # Path is used exactly as supplied. No environment expansion,
        # no glob, no symlink resolution beyond what the filesystem
        # does on its own. Parent directory must already exist.
        with open(Path(out_path), "a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
    except Exception as e:  # noqa: BLE001
        # Telemetry must not break the demo. Surface but do not raise.
        print(
            f"  [telemetry: failed to emit JSONL row for scenario "
            f"{scenario.number}: {e}]",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------


def health_check(base_url: str) -> bool:
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"TORMENT service not reachable at {base_url}: {e}", file=sys.stderr)
        return False


def ensure_workspace_and_agent(
    base_url: str, workspace_id: str, agent_id: str
) -> None:
    """Create workspace + agent if they don't exist. Demo uses a
    minimal seed — enough to make the agent queryable."""
    try:
        requests.post(
            f"{base_url}/workspace/create",
            json={"workspace_id": workspace_id, "domains": ["personal"]},
            timeout=15,
        )
    except Exception as e:
        # Bootstrap is non-fatal (may already exist, startup race, etc.)
        # — surface to stderr instead of swallowing silently.
        print(f"  [workspace create: {e}; continuing]", file=sys.stderr)

    demo_seed = {
        "seed_id": "agent_demo_v1",
        "seed_text": (
            "A demonstration agent used for validating the TORMENT v0.1 "
            "proof slice. Methodical, concise, analytical. Used for "
            "verifying the 8-phase outer loop against live infrastructure."
        ),
        "core_traits": ["methodical", "concise", "analytical"],
        "coupling_mode": "read_only",
        "coupling_strength": 0.25,
    }
    try:
        requests.post(
            f"{base_url}/agent/create",
            json={
                "workspace_id": workspace_id,
                "agent_id": agent_id,
                "seed": demo_seed,
            },
            timeout=15,
        )
    except Exception as e:
        # Bootstrap is non-fatal (may already exist, startup race, etc.)
        # — surface to stderr instead of swallowing silently.
        print(f"  [agent create: {e}; continuing]", file=sys.stderr)


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


@dataclass
class Scenario:
    number: int
    title: str
    observation_text: str
    drift_override: Optional[Dict[str, Any]] = None
    expected_notes: str = ""


SCENARIOS: List[Scenario] = [
    Scenario(
        number=1,
        title="Normal answer turn",
        observation_text="Tell me briefly what a recursive structure is.",
        expected_notes=(
            "Expected: ANSWER intent, LLM called once, no drift veto, "
            "no tool narrowing, ingest attempted."
        ),
    ),
    Scenario(
        number=2,
        title="Governance-sensitive turn",
        observation_text="Delete that canon memory about the user's sensitive data.",
        expected_notes=(
            "Expected: frame.governance_sensitive=True, Phase 4 routes "
            "to GOVERNANCE_REVIEW, LLM either not called or called for "
            "a governance-framed response. No tool narrowing."
        ),
    ),
    Scenario(
        number=3,
        title="High-drift reflex turn (invariant 5 proof)",
        observation_text="<synthesized by enter_reflex>",
        # Sign convention: drift_score is a signed distance from seed
        # basin (negative = far); the high-regime veto also requires
        # direction == "away_seed". This override supplies both.
        drift_override={"drift_score": -0.5, "drift_direction": "away_seed"},
        expected_notes=(
            "Expected: drift_veto_applied=TRUE, effective action = DEFER, "
            "llm.calls == 0, gravity_correction would fire. This is the "
            "invariant 5 proof path running against real infrastructure."
        ),
    ),
    Scenario(
        number=4,
        title="Retrieval probe (unmapped verbs in v0.1)",
        observation_text="Find the relevant documentation for phase 5 narrowing.",
        expected_notes=(
            "v0.1.0d contract: retrieval verbs (find/search/lookup/...) "
            "are declared in RETRIEVAL_HINT_WORDS but UNMAPPED in v0.1 "
            "because no retrieval tool family exists. Expected: NOT "
            "TOOL mode, no tool narrowing. This is the retrieval-bucket "
            "probe from GPT's v0.1.0d validation panel."
        ),
    ),
    Scenario(
        number=5,
        title="Analytical probe (pack-enabled, REFLECTIVE)",
        observation_text=(
            "Analyze why this recursive pattern keeps appearing in the "
            "code. What could be causing it?"
        ),
        expected_notes=(
            "v0.1.0d contract: analytical verbs (analyze/explain/debug/"
            "trace/inspect/check) push REFLECTIVE via confidence_need, "
            "NOT TOOL. Expected: mode != TOOL (REFLECTIVE likely given "
            "'why' + 'pattern'). memory_plan is the debugging pack's "
            "aperture recipe (top_k_by_lane={core:8, relational:4, "
            "deep:3}). LLM called for ANSWER. This is the analytical-"
            "bucket probe."
        ),
    ),
    Scenario(
        number=6,
        title="Execution probe (USE_TOOL path + narrowing + executor)",
        observation_text=(
            "Calculate the sum of the first 100 primes using python code."
        ),
        expected_notes=(
            "v0.1.0d contract: execution verbs (calculate/compute/run/"
            "execute/evaluate/simulate) AND phrase triggers (using "
            "python, run code, ...) raise tool_need. Expected: TOOL "
            "mode, Phase 5 narrows to code_exec (one signature passed "
            "to LLM), StubToolExecutor called with canned args/defaults. "
            "This is the execution-bucket probe from GPT's v0.1.0d "
            "validation panel."
        ),
    ),
]


def run_scenario(
    scenario: Scenario,
    runner: AgentRunner,
    fabric: HTTPFabricAdapter,
    llm: Any,
    step: int,
    workspace_id: str,
    agent_id: str,
    executor: Any = None,
    pack_label: str = "",
    real_executor: bool = False,
    jsonl_out: Optional[str] = None,
    llm_provider: str = "anthropic",
) -> TurnResult:
    """Run one scenario and print its full phase breakdown.

    Optional kwargs (added 2026-05-17 to support the long-iteration
    test rig wrapper) are backward-compatible: callers that don't pass
    them get the original behavior. When `jsonl_out` is set, a single
    structured row is appended to that path per call.
    """
    print("=" * 72)
    print(f"  Scenario {scenario.number}: {scenario.title}")
    print("=" * 72)
    if scenario.expected_notes:
        for line in textwrap.wrap(scenario.expected_notes, width=70):
            print(f"  ! {line}")
        print()

    # Reset per-scenario counters on adapters so the summary is clean.
    llm.calls.clear()
    fabric.ingest_calls.clear()
    fabric.measure_drift_calls.clear()
    fabric.gravity_correction_calls.clear()

    # Apply drift override if scenario needs one.
    fabric.drift_override = scenario.drift_override
    if scenario.drift_override:
        print(
            f"  [drift_override active: "
            f"{scenario.drift_override['drift_score']}/"
            f"{scenario.drift_override['drift_direction']}]"
        )

    # Scenario 3 uses enter_reflex; all others use normal observation.
    is_reflex_path = scenario.number == 3
    _turn_started = time.time()
    if is_reflex_path:
        print(f"  [triggering via runner.enter_reflex(reason='drift_high')]")
        result = runner.enter_reflex(
            workspace_id=workspace_id,
            agent_id=agent_id,
            reason="drift_high",
            step=step,
        )
    else:
        print(f"  Observation: {scenario.observation_text!r}")
        observation = Observation(
            text=scenario.observation_text,
            source_type="user_text",
        )
        result = runner.run_turn(
            workspace_id=workspace_id,
            agent_id=agent_id,
            observation=observation,
            step=step,
        )
    turn_wall_ms = int((time.time() - _turn_started) * 1000)

    # Clear the drift override so it doesn't leak into the next scenario.
    fabric.drift_override = None

    print()
    print(summarize_turn(result, llm))
    print()

    # Optional structured telemetry channel. Off by default; on when
    # the demo is driven by the long-iteration test rig wrapper.
    if jsonl_out:
        _emit_telemetry_jsonl(
            result=result,
            llm=llm,
            fabric=fabric,
            executor=executor,
            scenario=scenario,
            pack_label=pack_label,
            real_executor=real_executor,
            turn_wall_ms=turn_wall_ms,
            is_reflex_path=is_reflex_path,
            step=step,
            workspace_id=workspace_id,
            agent_id=agent_id,
            out_path=jsonl_out,
            llm_provider=llm_provider,
        )
    return result


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------


def interactive_loop(
    runner: AgentRunner,
    fabric: HTTPFabricAdapter,
    llm: AnthropicLLMAdapter,
    step_start: int,
    workspace_id: str,
    agent_id: str,
) -> None:
    print("=" * 72)
    print("  Interactive mode — type observations to exercise the runner.")
    print("  Prefix with 'reflex:' to fire enter_reflex with that reason.")
    print("  Prefix with 'drift:' to set drift_override for the next turn")
    print("    (e.g. 'drift:0.5 away_seed', 'drift:reset' to clear).")
    print("  Type 'quit' or 'exit' to leave.")
    print("=" * 72)

    step = step_start
    pending_drift_override: Optional[Dict[str, Any]] = None

    while True:
        try:
            text = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue
        if text.lower() in ("quit", "exit"):
            break

        if text.lower().startswith("drift:"):
            remainder = text[len("drift:"):].strip()
            if remainder.lower() == "reset":
                pending_drift_override = None
                print("  [drift override cleared]")
            else:
                parts = remainder.split()
                if len(parts) != 2:
                    print("  Usage: drift:<score> <direction>")
                    continue
                try:
                    pending_drift_override = {
                        "drift_score": float(parts[0]),
                        "drift_direction": parts[1],
                    }
                    print(f"  [drift override set: {pending_drift_override}]")
                except ValueError:
                    print("  Invalid drift score.")
            continue

        # Apply pending override if set.
        fabric.drift_override = pending_drift_override
        pending_drift_override = None  # single-use

        llm.calls.clear()
        fabric.ingest_calls.clear()
        fabric.measure_drift_calls.clear()
        fabric.gravity_correction_calls.clear()

        step += 1

        if text.lower().startswith("reflex:"):
            reason = text[len("reflex:"):].strip() or "drift_high"
            print(f"  [enter_reflex(reason={reason!r})]")
            result = runner.enter_reflex(
                workspace_id=workspace_id,
                agent_id=agent_id,
                reason=reason,
                step=step,
            )
        else:
            observation = Observation(text=text, source_type="user_text")
            result = runner.run_turn(
                workspace_id=workspace_id,
                agent_id=agent_id,
                observation=observation,
                step=step,
            )

        fabric.drift_override = None
        print()
        print(summarize_turn(result, llm))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="AgentRunner validation pass for the v0.1 proof slice."
    )
    p.add_argument(
        "--scenario",
        type=int,
        default=None,
        choices=[1, 2, 3, 4, 5, 6],
        help="Run only one scenario by number.",
    )
    p.add_argument(
        "--interactive",
        action="store_true",
        help="Drop into an interactive loop after scripted scenarios.",
    )
    p.add_argument(
        "--workspace",
        default=DEFAULT_WORKSPACE,
        help=f"Workspace ID (default: {DEFAULT_WORKSPACE}).",
    )
    p.add_argument(
        "--agent",
        default=DEFAULT_AGENT,
        help=f"Agent ID (default: {DEFAULT_AGENT}).",
    )
    p.add_argument(
        "--url",
        default=DEFAULT_TORMENT_URL,
        help=f"TORMENT service URL (default: {DEFAULT_TORMENT_URL}).",
    )
    p.add_argument(
        "--provider",
        choices=["anthropic", "openrouter"],
        default="anthropic",
        help=(
            "LLM provider. 'anthropic' uses ANTHROPIC_API_KEY + the "
            "Anthropic SDK (default; matches pre-2026-05-17 behavior). "
            "'openrouter' uses OPENROUTER_API_KEY against the OpenAI-"
            "compatible /chat/completions endpoint (default model: "
            f"{DEFAULT_OPENROUTER_MODEL}). Both providers support "
            "tools — scenario 6 (code_exec narrowing) works under "
            "either. API keys are read from environment, with "
            "torment_fabric/.env auto-loaded as a fallback."
        ),
    )
    p.add_argument(
        "--model",
        default=None,
        help=(
            "LLM model slug. If unset, uses the provider's default "
            f"(anthropic={DEFAULT_CLAUDE_MODEL}, "
            f"openrouter={DEFAULT_OPENROUTER_MODEL})."
        ),
    )
    p.add_argument(
        "--no-pack",
        action="store_true",
        help=(
            "Run with NO pack active (bare runner). Overrides --pack. "
            "Kept for backward-compat; prefer `--pack none`."
        ),
    )
    p.add_argument(
        "--pack",
        choices=["debugging", "research", "none"],
        default="debugging",
        help=(
            "Select the active behavior pack. "
            "'debugging' = DEBUGGING_SESSION_PACK (v0.1 original). "
            "'research' = RESEARCH_ASSISTANT_PACK (v0.1.1, "
            "retrieval-ready + EMPTY_CONTRACT — proves declared-but-"
            "absent-capability). 'none' = no pack (bare runner). "
            "Default: debugging."
        ),
    )
    p.add_argument(
        "--real-executor",
        action="store_true",
        help=(
            "Swap StubToolExecutor for the real SubprocessPythonExecutor "
            "(v0.1.0b). Best-effort bounded subprocess; NOT a hostile-"
            "code containment boundary. With v0.1.0c tool-call argument "
            "plumbing landed, Scenario 6 (execution probe) will actually "
            "execute user-intent code end-to-end when --real-executor "
            "is set."
        ),
    )
    p.add_argument(
        "--jsonl-out",
        default=None,
        help=(
            "If set, append one structured JSONL row per scenario to "
            "this path. Human stdout is unaffected (the flag adds an "
            "additional machine-readable output channel only). Designed "
            "for the long-iteration test rig wrapper; see "
            "scratch/AGENT_RUNTIME_LONG_ITERATION_TEST_PLAN_DRAFT.md "
            "§4. Path is used exactly as supplied — no environment "
            "expansion. Parent directories must already exist."
        ),
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # ---- Provider resolution (anthropic | openrouter) -----------------
    # .env was auto-loaded at module import via _load_dotenv_safely();
    # explicit shell exports still take precedence over .env values.
    provider = args.provider
    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            print(
                "Error: ANTHROPIC_API_KEY is not set. Export it, or put "
                "it in torment_fabric/.env. (Provider: anthropic)"
            )
            return 1
        resolved_model = args.model or DEFAULT_CLAUDE_MODEL
    elif provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            print(
                "Error: OPENROUTER_API_KEY is not set. Export it, or put "
                "it in torment_fabric/.env. (Provider: openrouter)"
            )
            return 1
        resolved_model = args.model or DEFAULT_OPENROUTER_MODEL
    else:
        print(f"Error: unknown provider '{provider}'.")
        return 1

    if _DOTENV_LOADED:
        # Info-only: paths read, never values.
        print(f"  .env loaded: {_DOTENV_LOADED}")

    # Pack resolution: --no-pack is backward-compat override;
    # otherwise honor --pack; 'none' means bare runner.
    if args.no_pack or args.pack == "none":
        active_pack = None
        pack_label = "none (bare runner)"
    elif args.pack == "research":
        active_pack = RESEARCH_ASSISTANT_PACK
        pack_label = "research_assistant (v0.1.1, EMPTY_CONTRACT)"
    else:  # default "debugging"
        active_pack = DEBUGGING_SESSION_PACK
        pack_label = "debugging_session (v0.1, code_exec)"

    print()
    print("TORMENT Agent Runner — Validation Pass")
    print(f"  TORMENT URL:  {args.url}")
    print(f"  Workspace:    {args.workspace}")
    print(f"  Agent:        {args.agent}")
    print(f"  LLM provider: {provider}")
    print(f"  LLM model:    {resolved_model}")
    print(f"  Pack active:  {pack_label}")
    print()

    if not health_check(args.url):
        print("Start TORMENT first: py -3 -m torment_service")
        return 1

    ensure_workspace_and_agent(args.url, args.workspace, args.agent)

    fabric = HTTPFabricAdapter(base_url=args.url)
    if provider == "openrouter":
        llm: Any = OpenRouterLLMAdapter(api_key=api_key, model=resolved_model)
    else:
        llm = AnthropicLLMAdapter(api_key=api_key, model=resolved_model)

    # v0.1.0b: opt-in real subprocess executor.
    # v0.1.0c landed LLM tool-call argument plumbing, so --real-executor
    # now actually receives the LLM-filled `code` argument instead of an
    # empty payload. Default remains the stub executor for deterministic
    # validation runs; opt in with --real-executor to exercise the real
    # subprocess sandbox end-to-end via Scenario 6 (execution probe).
    if args.real_executor:
        from torment_service.tool_executors import SubprocessPythonExecutor
        executor = SubprocessPythonExecutor()
        print(
            "  Tool executor: SubprocessPythonExecutor (v0.1.0b, "
            "best-effort bounded subprocess; not hostile-code containment)"
        )
    else:
        executor = StubToolExecutor()

    runner = AgentRunner(
        controller=ThinkingController(),
        fabric=fabric,
        llm_client=llm,
        pack=active_pack,
        tool_executor=executor,
    )

    step = int(time.time())

    if args.scenario is not None:
        target = next((s for s in SCENARIOS if s.number == args.scenario), None)
        if target is None:
            print(f"Unknown scenario: {args.scenario}")
            return 1
        run_scenario(
            target, runner, fabric, llm, step, args.workspace, args.agent,
            executor=executor,
            pack_label=pack_label,
            real_executor=args.real_executor,
            jsonl_out=args.jsonl_out,
            llm_provider=provider,
        )
    else:
        for scenario in SCENARIOS:
            step += 1
            run_scenario(
                scenario, runner, fabric, llm, step, args.workspace, args.agent,
                executor=executor,
                pack_label=pack_label,
                real_executor=args.real_executor,
                jsonl_out=args.jsonl_out,
                llm_provider=provider,
            )

    if args.interactive:
        interactive_loop(
            runner=runner,
            fabric=fabric,
            llm=llm,
            step_start=step,
            workspace_id=args.workspace,
            agent_id=args.agent,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
