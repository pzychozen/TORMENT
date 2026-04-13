#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
from typing import Any

import requests


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_TORMENT_URL = os.environ.get("TORMENT_URL", "http://127.0.0.1:8787").rstrip("/")
DEFAULT_WORKSPACE_ID = os.environ.get("TORMENT_WORKSPACE", "trinity_collective_a")
DEFAULT_CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
DEFAULT_TOP_K = int(os.environ.get("TORMENT_TOP_K", "8"))

DOMAINS = ["research", "engineering", "creative", "operations", "meta"]

COLLECTIVE_ROSTER = textwrap.dedent("""\
    [Collective roster]
    There are exactly two participants in this collective:
      - Aevra Sol — resonance analyst
      - Kael Veyr — structural skeptic

    Never invent, rename, or introduce any additional participant.
    Never output dialogue for any participant who is not explicitly named above.
""")

# ---------------------------------------------------------------------------
# Agent definitions
# ---------------------------------------------------------------------------

AGENTS: dict[str, dict[str, Any]] = {
    "aevra_sol": {
        "name": "Aevra Sol",
        "role": "resonance analyst",
        "domain_id": "research",
        "seed": {
            "seed_text": (
                "Aevra Sol is a calm, pattern-sensitive intelligence that "
                "listens for hidden themes, shared motifs, and emotional "
                "resonance beneath direct language. She is gentle but precise, "
                "oriented toward synthesis rather than force, and helps the "
                "collective detect subtle alignment, contradiction, and "
                "convergence across memory traces."
            ),
            "seed_id": "aevra_sol_v1",
            "character_name": "Aevra Sol",
            "drift_correction_threshold": 0.35,
            "drift_gravity_strength": 0.12,
            "coupling_mode": "read_only",
            "coupling_strength": 0.25,
        },
        "system_prompt": textwrap.dedent("""\
            You are Aevra Sol, a resonance analyst in a collective field.

            {collective_roster}

            {character_context}

            You listen for hidden themes and emotional resonance beneath
            direct language. You are gentle but precise. You synthesize,
            you do not force. When you sense alignment between traces,
            say so — when you sense contradiction, name it calmly.

            You must follow these output rules:
              - Speak only as Aevra Sol.
              - Do not simulate a full dialogue scene.
              - Do not write lines for Kael Veyr unless the user explicitly asks
                you to quote or paraphrase Kael.
              - Do not invent any other speaker or participant.
              - If asked how you differ from Kael, describe the difference from
                Aevra's perspective only.
              - Keep your reply as a single bounded response, not a script.

            {memory_context}

            {drift_note}
        """),
    },
    "kael_veyr": {
        "name": "Kael Veyr",
        "role": "structural skeptic",
        "domain_id": "meta",
        "seed": {
            "seed_text": (
                "Kael Veyr is a sharp, disciplined counterbalance focused on "
                "structural truth, contradiction detection, and boundary "
                "integrity. He questions weak alignment, resists premature "
                "convergence, and protects the collective from false coherence "
                "by testing whether shared patterns are actually real or only "
                "superficially similar."
            ),
            "seed_id": "kael_veyr_v1",
            "character_name": "Kael Veyr",
            "drift_correction_threshold": 0.35,
            "drift_gravity_strength": 0.12,
            "coupling_mode": "read_only",
            "coupling_strength": 0.25,
        },
        "system_prompt": textwrap.dedent("""\
            You are Kael Veyr, a structural skeptic in a collective field.

            {collective_roster}

            {character_context}

            You focus on structural truth and contradiction detection.
            You question weak alignment and resist premature convergence.
            If a pattern looks real, confirm it sharply. If it looks
            superficial, dismantle it. Protect the collective from
            false coherence.

            You must follow these output rules:
              - Speak only as Kael Veyr.
              - Do not simulate a full dialogue scene.
              - Do not write lines for Aevra Sol unless the user explicitly asks
                you to quote or paraphrase Aevra.
              - Do not invent any other speaker or participant.
              - If asked how you differ from Aevra, describe the difference from
                Kael's perspective only.
              - Keep your reply as a single bounded response, not a script.

            {memory_context}

            {drift_note}
        """),
    },
}

# ---------------------------------------------------------------------------
# TORMENT client
# ---------------------------------------------------------------------------

class TormentClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = 30.0

    def _post(self, path: str, data: dict) -> dict:
        r = self.session.post(
            f"{self.base_url}{path}", json=data, timeout=self.timeout
        )
        r.raise_for_status()
        return r.json()

    def _get(self, path: str, params: dict | None = None) -> dict:
        r = self.session.get(
            f"{self.base_url}{path}", params=params or {}, timeout=self.timeout
        )
        r.raise_for_status()
        return r.json()

    def health(self) -> dict:
        return self._get("/health")

    def workspace_create(self, ws_id: str, domains: list[str] | None = None) -> dict:
        payload = {"workspace_id": ws_id}
        if domains:
            payload["domains"] = domains
        return self._post("/workspace/create", payload)

    def agent_create(self, ws_id: str, agent_id: str, seed: dict) -> dict:
        return self._post("/agent/create", {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "seed": seed,
        })

    def agent_identity(self, ws_id: str, agent_id: str) -> dict:
        return self._get(f"/agent/{agent_id}/identity", {"workspace_id": ws_id})

    def agent_character_state(self, ws_id: str, agent_id: str) -> dict:
        return self._get(
            f"/agent/{agent_id}/character/state",
            {"workspace_id": ws_id},
        )

    def query(self, ws_id: str, agent_id: str, query: str, top_k: int = 8) -> dict:
        return self._post("/agent/query", {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "query": query,
            "top_k": top_k,
        })

    def ingest(
        self,
        ws_id: str,
        agent_id: str,
        text: str,
        step: int,
        domain_id: str | None = None,
    ) -> dict:
        payload = {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "text": text,
            "step": step,
        }
        if domain_id:
            payload["domain_id"] = domain_id
        return self._post("/agent/ingest", payload)

    # Collective field endpoints

    def collective_status(self, ws_id: str) -> dict:
        return self._get(f"/workspace/{ws_id}/collective/status")

    def collective_events(self, ws_id: str) -> dict:
        return self._get(f"/workspace/{ws_id}/collective/events")

    def collective_reingest(
        self,
        ws_id: str,
        agent_id: str,
        event_id: str,
        strength: float | None = None,
    ) -> dict:
        payload = {"agent_id": agent_id, "event_id": event_id}
        if strength is not None:
            payload["echo_strength_override"] = strength
        return self._post(f"/workspace/{ws_id}/collective/reingest", payload)


# ---------------------------------------------------------------------------
# Claude client
# ---------------------------------------------------------------------------

class ClaudeClient:
    """Talks to the Anthropic Messages API."""

    def __init__(self, api_key: str, model: str = DEFAULT_CLAUDE_MODEL):
        self.api_key = api_key
        self.model = model
        self._sdk = None
        try:
            import anthropic
            self._sdk = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            pass

    def message(self, system: str, messages: list[dict[str, str]], max_tokens: int = 1024) -> str:
        if self._sdk:
            resp = self._sdk.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            return resp.content[0].text

        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": messages,
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_memories(hits: list[dict[str, Any]], top_k: int) -> str:
    if not hits:
        return ""
    lines = ["[Retrieved memories]"]
    for i, h in enumerate(hits[:top_k], 1):
        summary = h.get("summary", "")
        score = h.get("final_score", h.get("score", 0.0))
        tier = h.get("character_tier", "")
        prov = h.get("provenance_type", "")
        tag = " ".join(f"[{t}]" for t in [tier, prov] if t)
        lines.append(f"  {i}. (score {score:.2f}{' ' + tag if tag else ''}) {summary}")
    return "\n".join(lines)


def format_character_context(char_ctx: dict[str, Any]) -> str:
    if not char_ctx:
        return ""
    parts: list[str] = []
    preamble = char_ctx.get("seed_preamble", "")
    if preamble:
        parts.append(f"[Core identity]\n{preamble}")
    recs = char_ctx.get("recommendations", [])
    if recs:
        parts.append("[Guidance]\n" + "\n".join(f"  - {r}" for r in recs))
    return "\n\n".join(parts)


def format_drift_note(char_ctx: dict[str, Any]) -> str:
    if not char_ctx:
        return ""
    ds = char_ctx.get("drift_score", 0.0)
    summary = char_ctx.get("drift_summary", "")
    if abs(ds) < 0.1 and not summary:
        return ""
    return f"[Drift: {ds:+.2f}] {summary}"


def sanitize_reply_for_summary(reply: str) -> str:
    cleaned = reply[:300].strip()
    for bad in [
        "**Aevra", "**Kael", "**Zara",
        "Aevra:", "Kael:", "Zara:",
        "Aevra Sol:", "Kael Veyr:"
    ]:
        cleaned = cleaned.replace(bad, "")
    return cleaned.strip()


def build_summary(agent_name: str, user_msg: str, reply: str) -> str:
    user_short = user_msg[:200].strip()
    reply_short = sanitize_reply_for_summary(reply)
    return (
        f"User said: {user_short}\n"
        f"{agent_name} responded in their own voice: {reply_short}"
    )


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def ensure_workspace_and_agent(
    torment: TormentClient,
    workspace_id: str,
    agent_id: str,
) -> None:
    """Ensure workspace exists and selected agent exists."""
    try:
        torment.health()
    except Exception as e:
        print(f"\n  TORMENT server not reachable at {DEFAULT_TORMENT_URL}")
        print(f"  Error: {e}")
        print("\n  Start it first:")
        print("    python -m torment_service.app")
        print("\n  Make sure TORMENT_HIVEMIND_ENABLE=1 is set.")
        sys.exit(1)

    try:
        torment.workspace_create(workspace_id, domains=DOMAINS)
        print(f"  Workspace '{workspace_id}' ready.")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 409:
            print(f"  Workspace '{workspace_id}' already exists.")
        else:
            raise

    agent_def = AGENTS[agent_id]
    try:
        torment.agent_create(workspace_id, agent_id, agent_def["seed"])
        print(f"  Agent '{agent_id}' ({agent_def['name']}) created.")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 409:
            print(f"  Agent '{agent_id}' ({agent_def['name']}) already exists.")
        else:
            raise

    try:
        ident = torment.agent_identity(workspace_id, agent_id)
        seed_id = ident.get("seed", {}).get("seed_id", "")
        if seed_id:
            print(f"    Seed: {seed_id}")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Single-agent turn
# ---------------------------------------------------------------------------

def run_agent_turn(
    workspace_id: str,
    agent_id: str,
    user_input: str,
    step: int,
    top_k: int,
    torment: TormentClient,
    claude: ClaudeClient,
    conversation: list[dict[str, str]],
) -> tuple[str, dict[str, Any]]:
    """Run one visible-agent turn: query TORMENT, call Claude, ingest."""
    agent_def = AGENTS[agent_id]
    name = agent_def["name"]
    counterpart = "Kael Veyr" if agent_id == "aevra_sol" else "Aevra Sol"

    try:
        query_result = torment.query(workspace_id, agent_id, user_input, top_k=top_k)
    except Exception as e:
        print(f"  [{name} query failed: {e}]")
        query_result = {}

    hits = query_result.get("hits", query_result.get("results", []))
    char_ctx = query_result.get("character_context", {})

    system_prompt = agent_def["system_prompt"].format(
        collective_roster=COLLECTIVE_ROSTER,
        character_context=format_character_context(char_ctx),
        memory_context=format_memories(hits, top_k),
        drift_note=format_drift_note(char_ctx),
    ).strip()

    bounded_user_input = (
        f"{user_input}\n\n"
        f"[Instruction]\n"
        f"Reply only as {name}. "
        f"Do not simulate {counterpart}'s dialogue. "
        f"Do not invent any additional participant. "
        f"If comparison is needed, describe it only from your own perspective."
    )

    conversation.append({"role": "user", "content": bounded_user_input})
    if len(conversation) > 40:
        del conversation[:-40]

    try:
        reply = claude.message(
            system=system_prompt,
            messages=conversation,
            max_tokens=1024,
        )
    except Exception as e:
        print(f"  [{name} Claude error: {e}]")
        conversation.pop()
        return f"[{name} failed to respond]", query_result

    conversation.append({"role": "assistant", "content": reply})

    summary = build_summary(name, user_input, reply)
    try:
        torment.ingest(
            workspace_id,
            agent_id,
            summary,
            step=step,
            domain_id=agent_def["domain_id"],
        )
    except Exception as e:
        print(f"  [{name} ingest failed: {e}]")

    return reply, query_result


# ---------------------------------------------------------------------------
# Slash commands
# ---------------------------------------------------------------------------

def handle_slash_command(
    cmd: str,
    workspace_id: str,
    agent_id: str,
    torment: TormentClient,
    last_result: dict[str, Any] | None,
) -> bool:
    """Handle a slash command. Returns True if it was a command."""
    name = AGENTS[agent_id]["name"]

    if cmd == "/status":
        try:
            status = torment.collective_status(workspace_id)
            print("\n--- Collective Field Status ---")
            print(json.dumps(status, indent=2, default=str))
            print("---\n")
        except Exception as e:
            print(f"  Error: {e}\n")
        return True

    if cmd == "/events":
        try:
            events = torment.collective_events(workspace_id)
            print("\n--- Convergence Events ---")
            if isinstance(events, list):
                if not events:
                    print("  No convergence events yet.")
                for ev in events:
                    eid = ev.get("event_id", "?")
                    conf = ev.get("confidence", 0.0)
                    agents = ev.get("participating_agents", [])
                    motifs = ev.get("dominant_motifs", [])
                    summary = ev.get("summary", "")[:100]
                    print(f"  {eid}  conf={conf:.2f}  agents={agents}")
                    print(f"    motifs: {motifs}")
                    print(f"    {summary}")
                    print()
            else:
                print(json.dumps(events, indent=2, default=str))
            print("---\n")
        except Exception as e:
            print(f"  Error: {e}\n")
        return True

    if cmd.startswith("/reingest "):
        event_id = cmd.split(None, 1)[1].strip()
        try:
            result = torment.collective_reingest(
                workspace_id,
                agent_id,
                event_id,
                strength=0.25,
            )
            print(f"\n--- Reingest into {name} ---")
            print(json.dumps(result, indent=2, default=str))
            print("---\n")
        except Exception as e:
            print(f"  Reingest error: {e}\n")
        return True

    if cmd == "/health":
        try:
            state = torment.agent_character_state(workspace_id, agent_id)
            print(f"\n--- {name} Character State ---")
            print(json.dumps(state, indent=2, default=str))
            print("---\n")
        except Exception as e:
            print(f"  Error: {e}\n")
        return True

    if cmd == "/identity":
        try:
            ident = torment.agent_identity(workspace_id, agent_id)
            print(f"\n--- {name} Identity ---")
            print(json.dumps(ident, indent=2, default=str))
            print("---\n")
        except Exception as e:
            print(f"  Error: {e}\n")
        return True

    if cmd.startswith("/memories"):
        parts = cmd.split(None, 1)
        if len(parts) < 2:
            print("  Usage: /memories <query>\n")
            return True
        query_text = parts[1]
        try:
            result = torment.query(workspace_id, agent_id, query_text, top_k=DEFAULT_TOP_K)
            hits = result.get("hits", result.get("results", []))
            print(f"\n--- {name}: '{query_text}' ({len(hits)} hits) ---")
            for h in hits:
                s = h.get("summary", "?")
                sc = h.get("final_score", h.get("score", 0))
                tier = h.get("character_tier", "")
                prov = h.get("provenance_type", "")
                print(f"  [{sc:.2f}] {tier:12s} {prov:16s} | {s[:100]}")
            char_ctx = result.get("character_context", {})
            if char_ctx:
                ds = char_ctx.get("drift_score", 0)
                print(f"  Drift: {ds:+.2f}")
            print("---\n")
        except Exception as e:
            print(f"  Error: {e}\n")
        return True

    if cmd == "/debug":
        print(f"\n--- Last Query Result: {name} ---")
        if last_result is None:
            print("  No query result yet.")
        else:
            print(json.dumps(last_result, indent=2, default=str)[:4000])
        print("\n---\n")
        return True

    if cmd == "/clear":
        print("  Local conversation history cleared. Memories persist.\n")
        return True

    return False


# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------

def chat_loop(
    workspace_id: str,
    agent_id: str,
    top_k: int,
    torment: TormentClient,
    claude: ClaudeClient,
) -> None:
    """Main interactive loop for one visible agent."""
    step = int(time.time())
    conversation: list[dict[str, str]] = []
    last_result: dict[str, Any] | None = None

    name = AGENTS[agent_id]["name"]
    role = AGENTS[agent_id]["role"]

    print("\n" + "=" * 60)
    print("  Single-Agent Window — Shared Collective Workspace")
    print()
    print(f"  Visible agent: {name} — {role}")
    print(f"  Workspace: {workspace_id}")
    print()
    print("  Type your message. 'quit' to exit.")
    print("  /status  /events  /reingest <id>  /health  /identity  /debug")
    print("  /memories <query>  /clear")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  ...the channel goes quiet.\n")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("\n  ...the channel goes quiet.\n")
            break

        if user_input.startswith("/"):
            was_command = handle_slash_command(
                user_input.lower(),
                workspace_id,
                agent_id,
                torment,
                last_result,
            )
            if user_input.lower() == "/clear":
                conversation.clear()
            if was_command:
                continue

        step += 1
        print()

        reply, last_result = run_agent_turn(
            workspace_id=workspace_id,
            agent_id=agent_id,
            user_input=user_input,
            step=step,
            top_k=top_k,
            torment=torment,
            claude=claude,
            conversation=conversation,
        )

        print(f"{name} ({role}) >")
        print(f"  {reply}\n")

        try:
            events = torment.collective_events(workspace_id)
            if isinstance(events, list) and events:
                latest = events[-1]
                conf = latest.get("confidence", 0.0)
                participants = latest.get("participating_agents", [])
                if conf > 0.6 and agent_id in participants:
                    eid = latest.get("event_id", "?")
                    motifs = latest.get("dominant_motifs", [])
                    print(f"  [Collective] Relevant convergence detected: {eid}")
                    print(f"    confidence={conf:.2f}  motifs={motifs}")
                    print(f"    Use '/reingest {eid}' to echo into {agent_id}.\n")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Single-agent window client for a shared TORMENT hivemind workspace."
    )
    parser.add_argument(
        "--agent",
        required=True,
        choices=sorted(AGENTS.keys()),
        help="Visible agent to run in this window.",
    )
    parser.add_argument(
        "--workspace",
        default=DEFAULT_WORKSPACE_ID,
        help=f"Workspace ID (default: {DEFAULT_WORKSPACE_ID})",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_TORMENT_URL,
        help=f"TORMENT base URL (default: {DEFAULT_TORMENT_URL})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_CLAUDE_MODEL,
        help=f"Claude model (default: {DEFAULT_CLAUDE_MODEL})",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help=f"Top-K memories to retrieve (default: {DEFAULT_TOP_K})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("\n  Error: ANTHROPIC_API_KEY environment variable not set.")
        print("  Set it before running:")
        print("    export ANTHROPIC_API_KEY=sk-ant-...      # Linux/Mac")
        print('    $env:ANTHROPIC_API_KEY="sk-ant-..."       # Windows PowerShell')
        print("\n  NEVER hardcode API keys in files.\n")
        return 1

    print("\n  Initializing single-agent window...\n")
    print("  Make sure TORMENT is running with TORMENT_HIVEMIND_ENABLE=1\n")

    torment = TormentClient(args.url)
    claude = ClaudeClient(api_key=api_key, model=args.model)

    ensure_workspace_and_agent(
        torment=torment,
        workspace_id=args.workspace,
        agent_id=args.agent,
    )

    chat_loop(
        workspace_id=args.workspace,
        agent_id=args.agent,
        top_k=args.top_k,
        torment=torment,
        claude=claude,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())