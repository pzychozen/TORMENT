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
    4. USE_TOOL path (stubbed executor) — expects narrowing to code_exec.
    5. Pack-enabled debugging turn — pack's aperture recipe active.

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
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

# Ensure the project root is importable when run from examples/.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from torment_service.agent_loop import (  # noqa: E402
    AgentRunner,
    Observation,
    TurnResult,
)
from torment_service.behavior_packs import DEBUGGING_SESSION_PACK  # noqa: E402
from torment_service.thinking_controller import ThinkingController  # noqa: E402
from torment_service.thinking_models import ActionType  # noqa: E402


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_TORMENT_URL = os.environ.get("TORMENT_URL", "http://127.0.0.1:8787").rstrip("/")
DEFAULT_WORKSPACE = os.environ.get("TORMENT_WORKSPACE", "ws_agent_runner_demo")
DEFAULT_AGENT = os.environ.get("TORMENT_AGENT", "agent_demo")
DEFAULT_CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")


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
    ) -> str:
        call_record = {
            "tools_count": len(tools) if tools else 0,
            "tool_names": [t.get("name") for t in tools] if tools else [],
            "system_chars": len(system_prompt),
            "messages_count": len(messages),
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

        try:
            resp = self._client.messages.create(**kwargs)
        except Exception as e:
            return f"[LLM call failed: {e}]"

        # Extract text content. Tool calls are recorded but not
        # executed by the demo — the ToolExecutor stub handles that
        # side.
        text_parts = []
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(block.text)
            elif getattr(block, "type", None) == "tool_use":
                text_parts.append(
                    f"[tool_use: name={block.name} input={block.input}]"
                )
        return "\n".join(text_parts) if text_parts else ""


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
    except Exception:
        pass

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
    except Exception:
        pass


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
        title="USE_TOOL path (narrowing + stub executor)",
        observation_text="Find the relevant documentation for phase 5 narrowing.",
        expected_notes=(
            "Expected: if Phase 4 picks USE_TOOL, Phase 5 narrows to "
            "code_exec (one signature passed to LLM), StubToolExecutor "
            "called with canned args/defaults. Ingest attempted."
        ),
    ),
    Scenario(
        number=5,
        title="Pack-enabled debugging turn",
        observation_text=(
            "Analyze why this recursive pattern keeps appearing in the "
            "code. What could be causing it?"
        ),
        expected_notes=(
            "Expected: memory_plan is the debugging pack's aperture "
            "recipe (top_k_by_lane={core:8, relational:4, deep:3}). "
            "Mode is likely REFLECTIVE. LLM called for ANSWER."
        ),
    ),
]


def run_scenario(
    scenario: Scenario,
    runner: AgentRunner,
    fabric: HTTPFabricAdapter,
    llm: AnthropicLLMAdapter,
    step: int,
    workspace_id: str,
    agent_id: str,
) -> TurnResult:
    """Run one scenario and print its full phase breakdown."""
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
    if scenario.number == 3:
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

    # Clear the drift override so it doesn't leak into the next scenario.
    fabric.drift_override = None

    print()
    print(summarize_turn(result, llm))
    print()
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
        choices=[1, 2, 3, 4, 5],
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
        "--model",
        default=DEFAULT_CLAUDE_MODEL,
        help=f"Claude model (default: {DEFAULT_CLAUDE_MODEL}).",
    )
    p.add_argument(
        "--no-pack",
        action="store_true",
        help="Run without DEBUGGING_SESSION_PACK active (bare runner).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        return 1

    print()
    print("TORMENT Agent Runner — Validation Pass")
    print(f"  TORMENT URL:  {args.url}")
    print(f"  Workspace:    {args.workspace}")
    print(f"  Agent:        {args.agent}")
    print(f"  LLM model:    {args.model}")
    print(f"  Pack active:  {not args.no_pack}")
    print()

    if not health_check(args.url):
        print("Start TORMENT first: py -3 -m torment_service")
        return 1

    ensure_workspace_and_agent(args.url, args.workspace, args.agent)

    fabric = HTTPFabricAdapter(base_url=args.url)
    llm = AnthropicLLMAdapter(api_key=api_key, model=args.model)
    executor = StubToolExecutor()

    runner = AgentRunner(
        controller=ThinkingController(),
        fabric=fabric,
        llm_client=llm,
        pack=None if args.no_pack else DEBUGGING_SESSION_PACK,
        tool_executor=executor,
    )

    step = int(time.time())

    if args.scenario is not None:
        target = next((s for s in SCENARIOS if s.number == args.scenario), None)
        if target is None:
            print(f"Unknown scenario: {args.scenario}")
            return 1
        run_scenario(target, runner, fabric, llm, step, args.workspace, args.agent)
    else:
        for scenario in SCENARIOS:
            step += 1
            run_scenario(scenario, runner, fabric, llm, step, args.workspace, args.agent)

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
