#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
examples/trinity_field.py — Hivemind collective field test client

Runs two agents (Aevra Sol + Kael Veyr) in a shared workspace and
drives them through a multi-turn conversation to exercise:
  - per-agent ingest with domain routing
  - per-agent query with character context
  - collective field status monitoring
  - convergence event detection
  - echo re-ingestion through the 7-gate policy engine

Requirements:
    pip install requests anthropic

Setup:
    1. Set environment variables (see Environment section below).

    2. Start TORMENT server:
       python -m torment_service.app

    3. Set your Anthropic API key:
       export ANTHROPIC_API_KEY=sk-ant-...      # Linux/Mac
       $env:ANTHROPIC_API_KEY="sk-ant-..."       # Windows PowerShell

    4. Run this script:
       python examples/trinity_field.py

Environment (set before starting the TORMENT server):
    export TORMENT_PROFILE=companion
    export TORMENT_CHARACTER_ENABLE=1
    export TORMENT_COMPRESS_ENABLE=0
    export TORMENT_HIVEMIND_ENABLE=1
    export TORMENT_EMBED_PROVIDER=st
    export TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
    export TORMENT_EMBED_DEVICE=cpu
    export TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT=0.50

    Windows CMD:
    set TORMENT_PROFILE=companion
    set TORMENT_CHARACTER_ENABLE=1
    set TORMENT_COMPRESS_ENABLE=0
    set TORMENT_HIVEMIND_ENABLE=1
    set TORMENT_EMBED_PROVIDER=st
    set TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
    set TORMENT_EMBED_DEVICE=cpu
    set TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT=0.50

Commands:
    Type your message to address both agents.
    'quit' or 'exit' to leave.
    '/status'          — collective field status
    '/events'          — list convergence events
    '/reingest <id>'   — reingest a convergence event into Aevra Sol
    '/health <agent>'  — check agent character state
    '/memories <agent> <query>' — peek at stored memories
    '/debug'           — last raw query results for both agents
    '/clear'           — reset conversation (keeps memories)

NEVER hardcode API keys in files. Always use environment variables.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import time

import requests


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

TORMENT_URL = os.environ.get("TORMENT_URL", "http://127.0.0.1:8787").rstrip("/")
WORKSPACE_ID = os.environ.get("TORMENT_WORKSPACE", "trinity_collective_a")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
TOP_K = int(os.environ.get("TORMENT_TOP_K", "8"))

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

AGENTS = {
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

    def _get(self, path: str, params: dict = None) -> dict:
        r = self.session.get(
            f"{self.base_url}{path}", params=params or {}, timeout=self.timeout
        )
        r.raise_for_status()
        return r.json()

    def health(self) -> dict:
        return self._get("/health")

    def workspace_create(self, ws_id: str, domains: list = None) -> dict:
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

    def ingest(self, ws_id: str, agent_id: str, text: str,
               step: int, domain_id: str = None) -> dict:
        payload = {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "text": text,
            "step": step,
        }
        if domain_id:
            payload["domain_id"] = domain_id
        return self._post("/agent/ingest", payload)

    # -- Collective field endpoints --

    def collective_status(self, ws_id: str) -> dict:
        return self._get(f"/workspace/{ws_id}/collective/status")

    def collective_events(self, ws_id: str) -> dict:
        return self._get(f"/workspace/{ws_id}/collective/events")

    def collective_reingest(self, ws_id: str, agent_id: str,
                            event_id: str, strength: float = None) -> dict:
        payload = {"agent_id": agent_id, "event_id": event_id}
        if strength is not None:
            payload["echo_strength_override"] = strength
        return self._post(
            f"/workspace/{ws_id}/collective/reingest", payload
        )

    def collective_proposals_status(self, ws_id: str) -> dict:
        return self._get(f"/workspace/{ws_id}/collective/proposals/status")


# ---------------------------------------------------------------------------
# Claude client
# ---------------------------------------------------------------------------

class ClaudeClient:
    """Talks to the Anthropic Messages API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self._sdk = None
        try:
            import anthropic
            self._sdk = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            # Optional dependency: `anthropic` SDK is not required to run this
            # example — fall back to the HTTP path when it isn't installed.
            pass

    def message(self, system: str, messages: list, max_tokens: int = 1024) -> str:
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

def format_memories(hits: list) -> str:
    if not hits:
        return ""
    lines = ["[Retrieved memories]"]
    for i, h in enumerate(hits[:TOP_K], 1):
        summary = h.get("summary", "")
        score = h.get("final_score", h.get("score", 0.0))
        tier = h.get("character_tier", "")
        prov = h.get("provenance_type", "")
        tag = " ".join(f"[{t}]" for t in [tier, prov] if t)
        lines.append(f"  {i}. (score {score:.2f}{' ' + tag if tag else ''}) {summary}")
    return "\n".join(lines)


def format_character_context(char_ctx: dict) -> str:
    if not char_ctx:
        return ""
    parts = []
    preamble = char_ctx.get("seed_preamble", "")
    if preamble:
        parts.append(f"[Core identity]\n{preamble}")
    recs = char_ctx.get("recommendations", [])
    if recs:
        parts.append("[Guidance]\n" + "\n".join(f"  - {r}" for r in recs))
    return "\n\n".join(parts)


def format_drift_note(char_ctx: dict) -> str:
    if not char_ctx:
        return ""
    ds = char_ctx.get("drift_score", 0.0)
    summary = char_ctx.get("drift_summary", "")
    if abs(ds) < 0.1 and not summary:
        return ""
    return f"[Drift: {ds:+.2f}] {summary}"


def build_summary(agent_name: str, user_msg: str, reply: str) -> str:
    user_short = user_msg[:200].strip()
    reply_short = reply[:300].strip()

    # Strip obvious script-like speaker prefixes before storing summaries.
    for bad in [
        "**Aevra", "**Kael", "**Zara", "Aevra:", "Kael:", "Zara:",
        "Aevra Sol:", "Kael Veyr:"
    ]:
        reply_short = reply_short.replace(bad, "")

    return (
        f"User said: {user_short}\n"
        f"{agent_name} responded in their own voice: {reply_short.strip()}"
    )


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def ensure_setup(torment: TormentClient) -> None:
    """Create workspace and both agents if they don't exist yet."""
    try:
        torment.health()
    except Exception as e:
        print(f"\n  TORMENT server not reachable at {TORMENT_URL}")
        print(f"  Error: {e}")
        print(f"\n  Start it first:")
        print(f"    python -m torment_service.app")
        print(f"\n  Make sure TORMENT_HIVEMIND_ENABLE=1 is set.")
        sys.exit(1)

    # Create workspace
    try:
        torment.workspace_create(WORKSPACE_ID, domains=DOMAINS)
        print(f"  Workspace '{WORKSPACE_ID}' ready.")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 409:
            print(f"  Workspace '{WORKSPACE_ID}' already exists.")
        else:
            raise

    # Create both agents
    for agent_id, agent_def in AGENTS.items():
        try:
            torment.agent_create(WORKSPACE_ID, agent_id, agent_def["seed"])
            print(f"  Agent '{agent_id}' ({agent_def['name']}) created.")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 409:
                print(f"  Agent '{agent_id}' ({agent_def['name']}) already exists.")
            else:
                raise

        # Verify identity
        try:
            ident = torment.agent_identity(WORKSPACE_ID, agent_id)
            seed_id = ident.get("seed", {}).get("seed_id", "")
            if seed_id:
                print(f"    Seed: {seed_id}")
        except Exception:
            # Best-effort identity peek for display only; a missing or errored
            # identity endpoint should not break workspace bring-up.
            pass


# ---------------------------------------------------------------------------
# Agent turn — query + LLM + ingest
# ---------------------------------------------------------------------------

def run_agent_turn(
    agent_id: str,
    agent_def: dict,
    user_input: str,
    step: int,
    torment: TormentClient,
    claude: ClaudeClient,
    conversations: dict,
) -> str:
    """Run one turn for a single agent: query TORMENT, call Claude, ingest."""
    name = agent_def["name"]

    # 1. Query TORMENT for this agent's memories
    try:
        query_result = torment.query(
            WORKSPACE_ID, agent_id, user_input, top_k=TOP_K
        )
    except Exception as e:
        print(f"  [{name} query failed: {e}]")
        query_result = {}

    hits = query_result.get("hits", query_result.get("results", []))
    char_ctx = query_result.get("character_context", {})

    # 2. Build system prompt
    system_prompt = agent_def["system_prompt"].format(
        collective_roster=COLLECTIVE_ROSTER,
        character_context=format_character_context(char_ctx),
        memory_context=format_memories(hits),
        drift_note=format_drift_note(char_ctx),
    ).strip()

    # 3. Call Claude
    conv = conversations.setdefault(agent_id, [])
    if agent_id == "aevra_sol":
        counterpart = "Kael Veyr"
    else:
        counterpart = "Aevra Sol"

    bounded_user_input = (
        f"{user_input}\n\n"
        f"[Instruction]\n"
        f"Reply only as {name}. "
        f"Do not simulate {counterpart}'s dialogue. "
        f"Do not invent any additional participant. "
        f"If comparison is needed, describe it only from your own perspective."
    )

    conv.append({"role": "user", "content": bounded_user_input})

    if len(conv) > 40:
        conversations[agent_id] = conv[-40:]
        conv = conversations[agent_id]

    try:
        reply = claude.message(
            system=system_prompt,
            messages=conv,
            max_tokens=1024,
        )
    except Exception as e:
        print(f"  [{name} Claude error: {e}]")
        conv.pop()
        return f"[{name} failed to respond]"

    conv.append({"role": "assistant", "content": reply})

    # 4. Ingest the turn summary
    summary = build_summary(name, user_input, reply)
    try:
        torment.ingest(
            WORKSPACE_ID, agent_id, summary,
            step=step, domain_id=agent_def["domain_id"],
        )
    except Exception as e:
        print(f"  [{name} ingest failed: {e}]")

    return reply


# ---------------------------------------------------------------------------
# Slash commands
# ---------------------------------------------------------------------------

def handle_slash_command(
    cmd: str,
    torment: TormentClient,
    last_results: dict,
) -> bool:
    """Handle a slash command. Returns True if it was a command."""

    if cmd == "/status":
        try:
            status = torment.collective_status(WORKSPACE_ID)
            print("\n--- Collective Field Status ---")
            print(json.dumps(status, indent=2, default=str))
            print("---\n")
        except Exception as e:
            print(f"  Error: {e}\n")
        return True

    if cmd == "/events":
        try:
            events = torment.collective_events(WORKSPACE_ID)
            print("\n--- Convergence Events ---")
            if isinstance(events, list):
                if not events:
                    print("  No convergence events yet.")
                for ev in events:
                    eid = ev.get("event_id", "?")
                    conf = ev.get("confidence", 0)
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
        target = "aevra_sol"  # default target
        try:
            result = torment.collective_reingest(
                WORKSPACE_ID, target, event_id, strength=0.25
            )
            print(f"\n--- Reingest into {target} ---")
            print(json.dumps(result, indent=2, default=str))
            print("---\n")
        except Exception as e:
            print(f"  Reingest error: {e}\n")
        return True

    if cmd.startswith("/health"):
        parts = cmd.split()
        agent_id = parts[1] if len(parts) > 1 else None
        targets = [agent_id] if agent_id and agent_id in AGENTS else list(AGENTS.keys())
        for aid in targets:
            try:
                state = torment.agent_character_state(WORKSPACE_ID, aid)
                print(f"\n--- {AGENTS[aid]['name']} Character State ---")
                print(json.dumps(state, indent=2, default=str))
            except Exception as e:
                print(f"  {aid}: {e}")
        print("---\n")
        return True

    if cmd.startswith("/memories"):
        parts = cmd.split(None, 2)
        if len(parts) < 3:
            print("  Usage: /memories <agent_id> <query>")
            print(f"  Agents: {', '.join(AGENTS.keys())}\n")
            return True
        agent_id, query_text = parts[1], parts[2]
        if agent_id not in AGENTS:
            print(f"  Unknown agent: {agent_id}")
            print(f"  Agents: {', '.join(AGENTS.keys())}\n")
            return True
        try:
            result = torment.query(WORKSPACE_ID, agent_id, query_text, top_k=TOP_K)
            hits = result.get("hits", result.get("results", []))
            print(f"\n--- {AGENTS[agent_id]['name']}: '{query_text}' ({len(hits)} hits) ---")
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
        print("\n--- Last Query Results ---")
        for aid, result in last_results.items():
            print(f"\n  {AGENTS[aid]['name']}:")
            print(json.dumps(result, indent=2, default=str)[:2000])
        print("\n---\n")
        return True

    if cmd == "/clear":
        print("  Conversation history cleared for all agents. Memories persist.\n")
        return True  # caller handles the actual clear

    return False


# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------

def chat_loop(torment: TormentClient, claude: ClaudeClient) -> None:
    """Main interactive loop — drives both agents each turn."""
    step = int(time.time())
    conversations: dict = {}  # agent_id -> message list
    last_results: dict = {}

    print("\n" + "=" * 60)
    print("  Trinity Field — Hivemind Collective Chat")
    print("  Two agents respond to each message with bounded individual replies.")
    print()
    print("  Aevra Sol  — resonance analyst (synthesis)")
    print("  Kael Veyr  — structural skeptic (contradiction)")
    print()
    print("  Type your message. 'quit' to exit.")
    print("  /status  /events  /reingest <id>  /health  /debug")
    print("  /memories <agent> <query>  /clear")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  ...the field goes quiet.\n")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("\n  ...the field goes quiet.\n")
            break

        # Slash commands
        if user_input.startswith("/"):
            was_command = handle_slash_command(
                user_input.lower(), torment, last_results
            )
            if user_input.lower() == "/clear":
                conversations.clear()
            if was_command:
                continue

        # Run both agents
        step += 1
        print()

        for agent_id, agent_def in AGENTS.items():
            name = agent_def["name"]
            role = agent_def["role"]

            reply = run_agent_turn(
                agent_id, agent_def, user_input, step,
                torment, claude, conversations,
            )

            print(f"{name} ({role}) >")
            print(f"  {reply}\n")

        # Check collective field after both agents respond
        try:
            events = torment.collective_events(WORKSPACE_ID)
            if isinstance(events, list) and events:
                latest = events[-1]
                conf = latest.get("confidence", 0)
                if conf > 0.6:
                    eid = latest.get("event_id", "?")
                    motifs = latest.get("dominant_motifs", [])
                    print(f"  [Collective] Convergence detected: {eid}")
                    print(f"    confidence={conf:.2f}  motifs={motifs}")
                    print(f"    Use '/reingest {eid}' to echo into an agent.\n")
        except Exception:
            # Best-effort collective convergence poll; failure here is a
            # non-critical diagnostic path and must not interrupt the chat loop.
            pass  # collective monitoring is best-effort


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("\n  Error: ANTHROPIC_API_KEY environment variable not set.")
        print("  Set it before running:")
        print("    export ANTHROPIC_API_KEY=sk-ant-...      # Linux/Mac")
        print('    $env:ANTHROPIC_API_KEY="sk-ant-..."       # Windows PowerShell')
        print("\n  NEVER hardcode API keys in files.\n")
        return 1

    print("\n  Initializing Trinity Field...\n")
    print("  Make sure TORMENT is running with TORMENT_HIVEMIND_ENABLE=1\n")

    torment = TormentClient(TORMENT_URL)
    claude = ClaudeClient(api_key=api_key, model=CLAUDE_MODEL)

    ensure_setup(torment)
    chat_loop(torment, claude)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
