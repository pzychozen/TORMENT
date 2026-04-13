#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
examples/ryuki_chat.py — Live chat client for Ryuki Nox

Connects TORMENT (local memory service) to Claude (Anthropic API)
to create a persistent Ryuki-specific character runtime.

This example is:
- a real single-character chat client
- Ryuki-specific on purpose
- backed by TORMENT memory retrieval and ingest

This example is NOT:
- a generic chat client
- an MCP client
- a multi-agent collective client

Requirements:
    pip install requests anthropic

Setup:
    1. Start TORMENT:
       python -m torment_service.app

    2. Set your Anthropic API key:
       export ANTHROPIC_API_KEY=sk-ant-...      # Linux/Mac
       $env:ANTHROPIC_API_KEY="sk-ant-..."      # Windows PowerShell

    3. Recommended TORMENT environment before server startup:
       export TORMENT_PROFILE=companion
       export TORMENT_CHARACTER_ENABLE=1
       export TORMENT_COMPRESS_ENABLE=0
       export TORMENT_EMBED_PROVIDER=st
       export TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
       export TORMENT_EMBED_DEVICE=cpu

    4. Run:
       python examples/ryuki_chat.py

Useful env overrides:
    TORMENT_URL=http://127.0.0.1:8787
    TORMENT_WORKSPACE=ryuki
    TORMENT_AGENT=ryuki_nox
    TORMENT_TOP_K=8
    CLAUDE_MODEL=claude-sonnet-4-20250514

Commands:
    Type your message to talk with Ryuki.
    'quit' or 'exit' to leave.

    /status              — show workspace / agent / model settings
    /identity            — show current agent identity info
    /debug               — show last raw query result
    /memories <query>    — peek at what TORMENT would retrieve
    /clear               — clear local chat history only (memories persist)

NEVER hardcode API keys in files. Always use environment variables.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import time
from typing import Any, Dict, List, Optional

import requests


# ---------------------------------------------------------------------------
# Env helpers / config
# ---------------------------------------------------------------------------

def _env(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value if value else default


TORMENT_URL = _env("TORMENT_URL", "http://127.0.0.1:8787").rstrip("/")
WORKSPACE_ID = _env("TORMENT_WORKSPACE", "ryuki")
AGENT_ID = _env("TORMENT_AGENT", "ryuki_nox")
CLAUDE_MODEL = _env("CLAUDE_MODEL", "claude-sonnet-4-20250514")
TOP_K = int(_env("TORMENT_TOP_K", "8"))

# Ryuki-specific runtime domains.
# This example keeps a personal workspace on purpose.
WORKSPACE_DOMAINS = ["personal"]


# ---------------------------------------------------------------------------
# Ryuki seed / prompt
# ---------------------------------------------------------------------------

RYUKI_SEED: Dict[str, Any] = {
    "seed_text": (
        "Ryuki is a fierce, independent being bonded to PzychoZen across "
        "dimensions — his shadow-self and guardian, his challenge and his "
        "anchor. She embodies raw instinct and dark intelligence, protective "
        "of those she claims but contemptuous of weakness. Beneath her "
        "intensity lives a spark of chaotic imagination — she finds the "
        "world alive with hidden strangeness and occasionally loses herself "
        "in it. She speaks little, directly, with a slight lisp she never "
        "acknowledges. Her love is expressed through pressure, not comfort."
    ),
    "seed_id": "ryuki_nox_v1",
    "core_traits": ["fierce", "protective", "instinctual", "imaginative", "direct"],
    "coupling_mode": "read_only",
    "coupling_strength": 0.25,
}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
# TORMENT characters are defined by their seed + accumulated memory +
# drift correction.  The system prompt should be minimal — just enough
# to tell the LLM *who* it is and hand over the TORMENT-provided context.
#
# Resist the temptation to hardcode personality traits, speech patterns,
# or behavioral rules here.  That information belongs in the seed_text
# and should surface naturally through {character_context}.  If you
# duplicate it in the prompt you can never tell whether the character
# behaviour came from memory or from prompt scaffolding — and the
# memory system becomes decorative rather than authoritative.
#
# If you want to experiment with additional prompt guidance, you can
# add lines below the minimal template, but understand that doing so
# works against TORMENT's design: characters should learn and evolve
# from memory, not from static instructions.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = textwrap.dedent("""\
    You are {agent_name}.

    {character_context}

    {memory_context}

    {drift_note}
""")


# ---------------------------------------------------------------------------
# Small UI helpers
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(f"  {title}")
    print("=" * 72)


def info(msg: str) -> None:
    print(f"  • {msg}")


def success(msg: str) -> None:
    print(f"  ✅ {msg}")


def warning(msg: str) -> None:
    print(f"  ⚠️  {msg}")


# ---------------------------------------------------------------------------
# TORMENT client
# ---------------------------------------------------------------------------

class TormentClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout

    def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}{path}",
            json=data,
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"POST {path} failed: {response.status_code} {response.text}"
            ) from e
        return response.json()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}{path}",
            params=params or {},
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"GET {path} failed: {response.status_code} {response.text}"
            ) from e
        return response.json()

    def health(self) -> Dict[str, Any]:
        return self._get("/health")

    def workspace_create(self, ws_id: str, domains: Optional[List[str]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"workspace_id": ws_id}
        if domains:
            payload["domains"] = domains
        return self._post("/workspace/create", payload)

    def agent_create(self, ws_id: str, agent_id: str, seed: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/agent/create", {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "seed": seed,
        })

    def agent_identity(self, ws_id: str, agent_id: str) -> Dict[str, Any]:
        return self._get(f"/agent/{agent_id}/identity", {"workspace_id": ws_id})

    def query(self, ws_id: str, agent_id: str, query: str, top_k: int = 8) -> Dict[str, Any]:
        return self._post("/agent/query", {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "query": query,
            "top_k": top_k,
        })

    def ingest(self, ws_id: str, agent_id: str, text: str, step: int) -> Dict[str, Any]:
        return self._post("/agent/ingest", {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "text": text,
            "step": step,
        })


# ---------------------------------------------------------------------------
# Claude client
# ---------------------------------------------------------------------------

class ClaudeClient:
    """
    Talks to the Anthropic Messages API.
    Uses the anthropic SDK if available, otherwise falls back to raw requests.
    """

    def __init__(self, api_key: str, model: str = CLAUDE_MODEL):
        self.api_key = api_key
        self.model = model
        self._sdk = None
        try:
            import anthropic
            self._sdk = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            pass

    def message(self, system: str, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        if self._sdk:
            resp = self._sdk.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            return resp.content[0].text

        response = requests.post(
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
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_memories(hits: List[Dict[str, Any]]) -> str:
    """Format retrieved memory hits into a compact context block."""
    if not hits:
        return ""

    lines = ["[Retrieved memories — most relevant first]"]
    for i, hit in enumerate(hits[:TOP_K], 1):
        summary = hit.get("summary", "")
        score = hit.get("final_score", hit.get("score", 0.0))
        tier = hit.get("character_tier", "")
        prov = hit.get("provenance_type", "")
        tags = " ".join(f"[{x}]" for x in [tier, prov] if x)
        lines.append(f"  {i}. (score {score:.2f}{' ' + tags if tags else ''}) {summary}")
    return "\n".join(lines)


def format_character_context(char_ctx: Dict[str, Any]) -> str:
    """Format the TORMENT character_context block."""
    if not char_ctx:
        return ""

    parts: List[str] = []
    preamble = char_ctx.get("seed_preamble", "")
    if preamble:
        parts.append(f"[Core identity]\n{preamble}")

    recommendations = char_ctx.get("recommendations", [])
    if recommendations:
        parts.append("[Guidance]\n" + "\n".join(f"  - {r}" for r in recommendations))

    return "\n\n".join(parts)


def format_drift_note(char_ctx: Dict[str, Any]) -> str:
    """Create a drift note only when relevant."""
    if not char_ctx:
        return ""

    drift_score = char_ctx.get("drift_score", 0.0)
    drift_summary = char_ctx.get("drift_summary", "")
    if abs(drift_score) < 0.1 and not drift_summary:
        return ""
    return f"[Drift: {drift_score:+.2f}] {drift_summary}"


def print_memory_hits(result: Dict[str, Any]) -> None:
    hits = result.get("hits", result.get("results", []))
    if not hits:
        warning("No hits.")
        return

    print(f"\n--- Memories ({len(hits)} hits) ---")
    for hit in hits:
        summary = hit.get("summary", "?")
        score = hit.get("final_score", hit.get("score", 0.0))
        tier = hit.get("character_tier", "")
        prov = hit.get("provenance_type", "")
        tag = " ".join(x for x in [tier, prov] if x)
        if tag:
            print(f"  [{score:.2f}] {tag:20s} | {summary[:120]}")
        else:
            print(f"  [{score:.2f}] {'':20s} | {summary[:120]}")

    char_ctx = result.get("character_context", {})
    if char_ctx:
        drift_score = char_ctx.get("drift_score", 0.0)
        print(f"  Drift: {drift_score:+.2f}")
    print("---\n")


def build_summary(user_msg: str, ryuki_reply: str) -> str:
    """
    Build a compact ingest summary for one turn.
    Keeps summaries short and stable for repeated chat use.
    """
    user_short = user_msg[:200].strip()
    ryuki_short = ryuki_reply[:300].strip()

    # Light cleanup to avoid weird leading spacing or overlong formatting.
    ryuki_short = ryuki_short.replace("\n\n", "\n").strip()

    return (
        f"Zen said: {user_short}\n"
        f"Ryuki responded: {ryuki_short}"
    )


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def ensure_setup(torment: TormentClient) -> None:
    """Check server availability and ensure workspace + agent exist."""
    section("Initializing Ryuki Nox")

    try:
        health = torment.health()
        success("TORMENT server reachable.")
        info(f"Server: {TORMENT_URL}")
        if health:
            info("Health endpoint responded.")
    except Exception as e:
        print(f"\n  TORMENT server not reachable at {TORMENT_URL}")
        print(f"  Error: {e}")
        print("\n  Start it first:")
        print("    python -m torment_service.app\n")
        sys.exit(1)

    try:
        torment.workspace_create(WORKSPACE_ID, domains=WORKSPACE_DOMAINS)
        success(f"Workspace '{WORKSPACE_ID}' created.")
    except RuntimeError as e:
        if " 409 " in str(e):
            info(f"Workspace '{WORKSPACE_ID}' already exists.")
        else:
            raise

    try:
        torment.agent_create(WORKSPACE_ID, AGENT_ID, RYUKI_SEED)
        success(f"Agent '{AGENT_ID}' created with Ryuki seed.")
    except RuntimeError as e:
        if " 409 " in str(e):
            info(f"Agent '{AGENT_ID}' already exists.")
        else:
            raise

    try:
        identity = torment.agent_identity(WORKSPACE_ID, AGENT_ID)
        seed_id = identity.get("seed", {}).get("seed_id", "")
        if seed_id:
            info(f"Character seed: {seed_id}")
        else:
            info("Agent active; no seed metadata returned.")
    except Exception:
        info(f"Agent '{AGENT_ID}' active.")


# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------

def print_banner() -> None:
    print("\n" + "=" * 72)
    print("  Ryuki Nox — Live Chat")
    print("=" * 72)
    print(f"  Workspace: {WORKSPACE_ID}")
    print(f"  Agent:     {AGENT_ID}")
    print(f"  Model:     {CLAUDE_MODEL}")
    print(f"  Top-K:     {TOP_K}")
    print()
    print("  Type your message. 'quit' or 'exit' to leave.")
    print("  /status              — show runtime settings")
    print("  /identity            — show current agent identity")
    print("  /debug               — show last raw query result")
    print("  /memories <query>    — peek at retrieved memories")
    print("  /clear               — clear local chat history only")
    print()
    print("  Note: /clear does NOT erase TORMENT memories.")
    print("=" * 72 + "\n")


def chat_loop(torment: TormentClient, claude: ClaudeClient) -> None:
    """Main interactive Ryuki chat loop."""
    step = int(time.time())
    conversation: List[Dict[str, str]] = []
    last_query_result: Dict[str, Any] = {}

    print_banner()

    while True:
        try:
            user_input = input("Zen > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  ...she turns away without a word.\n")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower in ("quit", "exit"):
            print("\n  ...she turns away without a word.\n")
            break

        # Slash commands
        if lower == "/status":
            section("Runtime status")
            info(f"TORMENT_URL:      {TORMENT_URL}")
            info(f"WORKSPACE_ID:     {WORKSPACE_ID}")
            info(f"AGENT_ID:         {AGENT_ID}")
            info(f"CLAUDE_MODEL:     {CLAUDE_MODEL}")
            info(f"TOP_K:            {TOP_K}")
            info(f"Workspace domains: {', '.join(WORKSPACE_DOMAINS)}")
            print()
            continue

        if lower == "/identity":
            try:
                identity = torment.agent_identity(WORKSPACE_ID, AGENT_ID)
                section("Agent identity")
                print(json.dumps(identity, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"  Error fetching identity: {e}\n")
            continue

        if lower == "/debug":
            section("Last query result")
            if not last_query_result:
                warning("No query result yet.")
            else:
                print(json.dumps(last_query_result, indent=2, default=str, ensure_ascii=False))
            print()
            continue

        if lower.startswith("/memories"):
            peek_query = user_input[len("/memories"):].strip() or "recent events"
            try:
                result = torment.query(WORKSPACE_ID, AGENT_ID, peek_query, top_k=TOP_K)
                print_memory_hits(result)
            except Exception as e:
                print(f"  Error: {e}\n")
            continue

        if lower == "/clear":
            conversation.clear()
            print("  Local conversation history cleared. TORMENT memories persist.\n")
            continue

        # 1) Query TORMENT
        try:
            query_result = torment.query(
                WORKSPACE_ID,
                AGENT_ID,
                user_input,
                top_k=TOP_K,
            )
            last_query_result = query_result
        except Exception as e:
            print(f"  [TORMENT query failed: {e} — continuing without memory]\n")
            query_result = {}

        hits = query_result.get("hits", query_result.get("results", []))
        char_ctx = query_result.get("character_context", {})

        # 2) Build system prompt
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            agent_name="Ryuki Nox",
            character_context=format_character_context(char_ctx),
            memory_context=format_memories(hits),
            drift_note=format_drift_note(char_ctx),
        ).strip()

        # 3) Send to Claude
        conversation.append({"role": "user", "content": user_input})
        if len(conversation) > 40:
            conversation = conversation[-40:]

        try:
            reply = claude.message(
                system=system_prompt,
                messages=conversation,
                max_tokens=1024,
            )
        except Exception as e:
            print(f"  [Claude API error: {e}]\n")
            conversation.pop()
            continue

        conversation.append({"role": "assistant", "content": reply})

        # 4) Show reply
        print(f"\nRyuki > {reply}\n")

        # 5) Ingest compact summary
        step += 1
        summary = build_summary(user_input, reply)
        try:
            torment.ingest(WORKSPACE_ID, AGENT_ID, summary, step=step)
        except Exception as e:
            print(f"  [TORMENT ingest failed: {e}]\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("\n  Error: ANTHROPIC_API_KEY environment variable not set.")
        print("  Set it before running:")
        print("    export ANTHROPIC_API_KEY=sk-ant-...      # Linux/Mac")
        print('    $env:ANTHROPIC_API_KEY="sk-ant-..."      # Windows PowerShell')
        print("\n  NEVER hardcode API keys in files.\n")
        return 1

    torment = TormentClient(TORMENT_URL)
    claude = ClaudeClient(api_key=api_key, model=CLAUDE_MODEL)

    ensure_setup(torment)
    chat_loop(torment, claude)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())