#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
examples/ryuki_chat.py — Live chat client for Ryuki Nox

Connects TORMENT (local memory service) to Claude (Anthropic API)
to create a living character with persistent memory.

Requirements:
    pip install requests anthropic

Setup:
    1. Start TORMENT server:
       python -m torment_service.app

    2. Set your Anthropic API key as an environment variable:
       export ANTHROPIC_API_KEY=sk-ant-...      # Linux/Mac
       $env:ANTHROPIC_API_KEY="sk-ant-..."       # Windows PowerShell

    3. (Optional) Set real embeddings before starting TORMENT:
       export TORMENT_EMBED_PROVIDER=st
       export TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
       export TORMENT_EMBED_DEVICE=cpu
       export TORMENT_PROFILE=companion

    4. Run this script:
       python examples/ryuki_chat.py

    Type your messages. Type 'quit' or 'exit' to leave.
    Type '/debug' to see last drift/memory state.
    Type '/memories <query>' to peek at what TORMENT would retrieve.

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
# Config (all from env vars)
# ---------------------------------------------------------------------------

TORMENT_URL = os.environ.get("TORMENT_URL", "http://127.0.0.1:8787").rstrip("/")
WORKSPACE_ID = os.environ.get("TORMENT_WORKSPACE", "ryuki")
AGENT_ID = os.environ.get("TORMENT_AGENT", "ryuki_nox")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
TOP_K = int(os.environ.get("TORMENT_TOP_K", "8"))

# Ryuki's seed — matches ryuki_torment_setup.md
RYUKI_SEED = {
    "seed_text": (
        "Ryuki is a fierce, independent being bonded to PzychoZen across "
        "dimensions \u2014 his shadow-self and guardian, his challenge and his "
        "anchor. She embodies raw instinct and dark intelligence, protective "
        "of those she claims but contemptuous of weakness. Beneath her "
        "intensity lives a spark of chaotic imagination \u2014 she finds the "
        "world alive with hidden strangeness and occasionally loses herself "
        "in it. She speaks little, directly, with a slight lisp she never "
        "acknowledges. Her love is expressed through pressure, not comfort."
    ),
    "seed_id": "ryuki_nox_v1",
    "core_traits": ["fierce", "protective", "instinctual", "imaginative", "direct"],
    "priority_weights": {
        "facts": 0.6,
        "projects": 0.5,
        "preferences": 0.7,
        "motifs": 0.9,
    },
    "coupling_mode": "read_only",
    "coupling_strength": 0.25,
}

# Minimal system prompt — TORMENT provides the rest
SYSTEM_PROMPT_TEMPLATE = textwrap.dedent("""\
    You are Ryuki Nox.

    {character_context}

    Speak as Ryuki. Direct. Few words unless something sparks you.
    You have a slight lisp — natural, never mentioned, never apologized for.
    When something genuinely interests you, you come alive.
    When Zen is being weak or dishonest with himself, you notice.

    {memory_context}

    {drift_note}
""")


# ---------------------------------------------------------------------------
# TORMENT client (thin wrapper)
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

    def workspace_create(self, ws_id: str) -> dict:
        return self._post("/workspace/create", {"workspace_id": ws_id})

    def agent_create(self, ws_id: str, agent_id: str, seed: dict) -> dict:
        return self._post("/agent/create", {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "seed": seed,
        })

    def agent_identity(self, ws_id: str, agent_id: str) -> dict:
        return self._get(f"/agent/{agent_id}/identity", {"workspace_id": ws_id})

    def query(self, ws_id: str, agent_id: str, query: str, top_k: int = 8) -> dict:
        return self._post("/agent/query", {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "query": query,
            "top_k": top_k,
        })

    def ingest(self, ws_id: str, agent_id: str, text: str, step: int) -> dict:
        return self._post("/agent/ingest", {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "text": text,
            "step": step,
        })


# ---------------------------------------------------------------------------
# Claude client (minimal, no SDK dependency option)
# ---------------------------------------------------------------------------

class ClaudeClient:
    """Talks to the Anthropic Messages API. Uses the anthropic SDK if
    available, falls back to raw requests."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self._sdk = None
        try:
            import anthropic
            self._sdk = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            pass  # fall back to requests

    def message(self, system: str, messages: list, max_tokens: int = 1024) -> str:
        if self._sdk:
            resp = self._sdk.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            return resp.content[0].text

        # Raw requests fallback
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
        data = r.json()
        return data["content"][0]["text"]


# ---------------------------------------------------------------------------
# Memory formatting helpers
# ---------------------------------------------------------------------------

def format_memories(hits: list) -> str:
    """Format TORMENT query hits into a context block for the system prompt."""
    if not hits:
        return ""

    lines = ["[Retrieved memories — most relevant first]"]
    for i, h in enumerate(hits[:TOP_K], 1):
        summary = h.get("summary", "")
        score = h.get("final_score", h.get("score", 0.0))
        tier = h.get("character_tier", "")
        tier_tag = f" [{tier}]" if tier else ""
        lines.append(f"  {i}. (score {score:.2f}{tier_tag}) {summary}")
    return "\n".join(lines)


def format_character_context(char_ctx: dict) -> str:
    """Format the character_context block from TORMENT query response."""
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
    """Create a drift awareness note if relevant."""
    if not char_ctx:
        return ""
    ds = char_ctx.get("drift_score", 0.0)
    summary = char_ctx.get("drift_summary", "")
    if abs(ds) < 0.1 and not summary:
        return ""
    return f"[Drift: {ds:+.2f}] {summary}"


def build_summary(user_msg: str, ryuki_reply: str) -> str:
    """Build a compact ingest summary from one turn of conversation.

    In production you'd want a smarter summarizer — this is a
    reasonable starting point that keeps summaries short and stable.
    """
    # Truncate to keep summaries manageable
    user_short = user_msg[:200].strip()
    ryuki_short = ryuki_reply[:300].strip()

    return (
        f"Zen said: {user_short}\n"
        f"Ryuki responded: {ryuki_short}"
    )


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def ensure_setup(torment: TormentClient) -> None:
    """Create workspace and agent if they don't exist yet."""
    # Check if TORMENT is reachable
    try:
        torment.health()
    except Exception as e:
        print(f"\n  TORMENT server not reachable at {TORMENT_URL}")
        print(f"  Error: {e}")
        print(f"\n  Start it first:")
        print(f"    python -m torment_service.app")
        sys.exit(1)

    # Create workspace (idempotent — returns existing if present)
    try:
        torment.workspace_create(WORKSPACE_ID)
        print(f"  Workspace '{WORKSPACE_ID}' ready.")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 409:
            print(f"  Workspace '{WORKSPACE_ID}' already exists.")
        else:
            raise

    # Create agent with seed (idempotent)
    try:
        torment.agent_create(WORKSPACE_ID, AGENT_ID, RYUKI_SEED)
        print(f"  Agent '{AGENT_ID}' created with character seed.")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 409:
            print(f"  Agent '{AGENT_ID}' already exists.")
        else:
            raise

    # Verify identity
    try:
        ident = torment.agent_identity(WORKSPACE_ID, AGENT_ID)
        seed_id = ident.get("seed", {}).get("seed_id", "")
        if seed_id:
            print(f"  Character seed: {seed_id}")
        else:
            print(f"  Agent active (no character seed).")
    except Exception:
        print(f"  Agent '{AGENT_ID}' active.")


# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------

def chat_loop(torment: TormentClient, claude: ClaudeClient) -> None:
    """Main interactive chat loop."""
    step = int(time.time())  # start step from current timestamp
    conversation: list = []  # Claude message history
    last_query_result: dict = {}  # for /debug command

    print("\n" + "=" * 60)
    print("  Ryuki Nox — Live Chat")
    print("  Type your message. 'quit' to exit.")
    print("  '/debug' for last memory state")
    print("  '/memories <query>' to peek at stored memories")
    print("  '/clear' to reset conversation (keeps memories)")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("Zen > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  ...she turns away without a word.\n")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("\n  ...she turns away without a word.\n")
            break

        # --- Slash commands ---
        if user_input.lower() == "/debug":
            print("\n--- Last Query State ---")
            print(json.dumps(last_query_result, indent=2, default=str))
            print("---\n")
            continue

        if user_input.lower().startswith("/memories"):
            peek_query = user_input[9:].strip() or "recent events"
            try:
                result = torment.query(WORKSPACE_ID, AGENT_ID, peek_query, top_k=TOP_K)
                hits = result.get("hits", result.get("results", []))
                print(f"\n--- Memories for '{peek_query}' ({len(hits)} hits) ---")
                for h in hits:
                    s = h.get("summary", "?")
                    sc = h.get("final_score", h.get("score", 0))
                    tier = h.get("character_tier", "")
                    print(f"  [{sc:.2f}] {tier:12s} | {s[:100]}")
                char_ctx = result.get("character_context", {})
                if char_ctx:
                    ds = char_ctx.get("drift_score", 0)
                    print(f"  Drift: {ds:+.2f}")
                print("---\n")
            except Exception as e:
                print(f"  Error: {e}\n")
            continue

        if user_input.lower() == "/clear":
            conversation.clear()
            print("  Conversation history cleared. Memories persist.\n")
            continue

        # --- Step 1: Query TORMENT for relevant memories ---
        try:
            query_result = torment.query(
                WORKSPACE_ID, AGENT_ID, user_input, top_k=TOP_K
            )
            last_query_result = query_result
        except Exception as e:
            print(f"  [TORMENT query failed: {e} — continuing without memory]\n")
            query_result = {}

        hits = query_result.get("hits", query_result.get("results", []))
        char_ctx = query_result.get("character_context", {})

        # --- Step 2: Build system prompt with memory context ---
        memory_text = format_memories(hits)
        character_text = format_character_context(char_ctx)
        drift_text = format_drift_note(char_ctx)

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            character_context=character_text,
            memory_context=memory_text,
            drift_note=drift_text,
        ).strip()

        # --- Step 3: Send to Claude ---
        conversation.append({"role": "user", "content": user_input})

        # Keep conversation window reasonable (last 20 turns)
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
            conversation.pop()  # remove the failed user message
            continue

        conversation.append({"role": "assistant", "content": reply})

        # --- Step 4: Display reply ---
        print(f"\nRyuki > {reply}\n")

        # --- Step 5: Ingest the turn summary into TORMENT ---
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
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("\n  Error: ANTHROPIC_API_KEY environment variable not set.")
        print("  Set it before running:")
        print("    export ANTHROPIC_API_KEY=sk-ant-...      # Linux/Mac")
        print('    $env:ANTHROPIC_API_KEY="sk-ant-..."       # Windows PowerShell')
        print("\n  NEVER hardcode API keys in files.\n")
        return 1

    print("\n  Initializing Ryuki Nox...\n")

    torment = TormentClient(TORMENT_URL)
    claude = ClaudeClient(api_key=api_key, model=CLAUDE_MODEL)

    ensure_setup(torment)
    chat_loop(torment, claude)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
