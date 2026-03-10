#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
examples/ryuki_chat_openai.py — Ryuki Nox chat client (OpenAI-compatible APIs)

Works with any OpenAI-compatible API:
  - Ollama (default)
  - LM Studio
  - OpenAI
  - Any local model with OpenAI-compatible endpoint

Requirements:
    pip install requests openai

Setup for Ollama (default — no API key needed):
    1. Install Ollama and pull a model:  ollama pull llama3.1
    2. Start TORMENT server:             python -m torment_service
    3. Run:                              python examples/ryuki_chat_openai.py

Setup for LM Studio:
    set OPENAI_BASE_URL=http://localhost:1234/v1
    set OPENAI_MODEL=your-loaded-model
    python examples/ryuki_chat_openai.py

Setup for OpenAI:
    set OPENAI_API_KEY=sk-...
    set OPENAI_BASE_URL=https://api.openai.com/v1
    set OPENAI_MODEL=gpt-4o
    python examples/ryuki_chat_openai.py

Type your messages. 'quit' to exit.
'/debug' for last memory state, '/memories <query>' to peek.
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
# Config
# ---------------------------------------------------------------------------

TORMENT_URL = os.environ.get("TORMENT_URL", "http://127.0.0.1:8787").rstrip("/")
WORKSPACE_ID = os.environ.get("TORMENT_WORKSPACE", "ryuki")
AGENT_ID = os.environ.get("TORMENT_AGENT", "ryuki_nox")
TOP_K = int(os.environ.get("TORMENT_TOP_K", "8"))

# OpenAI-compatible settings (defaults to Ollama local)
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1").rstrip("/")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "ollama")  # Ollama doesn't need a real key
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "llama3.1")

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
    "coupling_mode": "read_only",
    "coupling_strength": 0.25,
}

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
# TORMENT client
# ---------------------------------------------------------------------------

class TormentClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.s = requests.Session()

    def _post(self, path, data):
        r = self.s.post(f"{self.base_url}{path}", json=data, timeout=30)
        r.raise_for_status()
        return r.json()

    def _get(self, path, params=None):
        r = self.s.get(f"{self.base_url}{path}", params=params or {}, timeout=30)
        r.raise_for_status()
        return r.json()

    def health(self):
        return self._get("/health")

    def workspace_create(self, ws_id, domains=None):
        payload = {"workspace_id": ws_id}
        if domains:
            payload["domains"] = domains
        return self._post("/workspace/create", payload)

    def agent_create(self, ws_id, agent_id, seed):
        return self._post("/agent/create", {"workspace_id": ws_id, "agent_id": agent_id, "seed": seed})

    def agent_identity(self, ws_id, agent_id):
        return self._get(f"/agent/{agent_id}/identity", {"workspace_id": ws_id})

    def query(self, ws_id, agent_id, query, top_k=8):
        return self._post("/agent/query", {"workspace_id": ws_id, "agent_id": agent_id, "query": query, "top_k": top_k})

    def ingest(self, ws_id, agent_id, text, step):
        return self._post("/agent/ingest", {"workspace_id": ws_id, "agent_id": agent_id, "text": text, "step": step})


# ---------------------------------------------------------------------------
# OpenAI-compatible client (works with Ollama, LM Studio, OpenAI, etc.)
# ---------------------------------------------------------------------------

class OpenAICompatClient:
    """Talks to any OpenAI-compatible chat completions endpoint."""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self._sdk = None
        try:
            from openai import OpenAI
            self._sdk = OpenAI(base_url=base_url, api_key=api_key)
        except ImportError:
            pass

    def message(self, system: str, messages: list, max_tokens: int = 1024) -> str:
        all_messages = [{"role": "system", "content": system}] + messages

        if self._sdk:
            resp = self._sdk.chat.completions.create(
                model=self.model,
                messages=all_messages,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content

        # Raw requests fallback
        r = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": all_messages,
                "max_tokens": max_tokens,
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Helpers (same as ryuki_chat.py)
# ---------------------------------------------------------------------------

def format_memories(hits):
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


def format_character_context(char_ctx):
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


def format_drift_note(char_ctx):
    if not char_ctx:
        return ""
    ds = char_ctx.get("drift_score", 0.0)
    summary = char_ctx.get("drift_summary", "")
    if abs(ds) < 0.1 and not summary:
        return ""
    return f"[Drift: {ds:+.2f}] {summary}"


def build_summary(user_msg, reply):
    return f"Zen said: {user_msg[:200].strip()}\nRyuki responded: {reply[:300].strip()}"


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def ensure_setup(torment):
    try:
        torment.health()
    except Exception as e:
        print(f"\n  TORMENT server not reachable at {TORMENT_URL}")
        print(f"  Start it first: python -m torment_service")
        sys.exit(1)

    try:
        torment.workspace_create(WORKSPACE_ID, domains=["personal"])
        print(f"  Workspace '{WORKSPACE_ID}' ready.")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 409:
            print(f"  Workspace '{WORKSPACE_ID}' exists.")
        else:
            raise

    try:
        torment.agent_create(WORKSPACE_ID, AGENT_ID, RYUKI_SEED)
        print(f"  Agent '{AGENT_ID}' created with character seed.")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 409:
            print(f"  Agent '{AGENT_ID}' exists.")
        else:
            raise


# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------

def chat_loop(torment, llm):
    step = int(time.time())
    conversation = []
    last_query_result = {}

    print(f"\n{'=' * 60}")
    print(f"  Ryuki Nox — Live Chat ({OPENAI_MODEL} via {OPENAI_BASE_URL})")
    print(f"  Type your message. 'quit' to exit.")
    print(f"  '/debug' for last memory state")
    print(f"  '/memories <query>' to peek at stored memories")
    print(f"  '/clear' to reset conversation")
    print(f"{'=' * 60}\n")

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

        if user_input.lower() == "/debug":
            print("\n--- Last Query State ---")
            print(json.dumps(last_query_result, indent=2, default=str))
            print("---\n")
            continue

        if user_input.lower().startswith("/memories"):
            peek_q = user_input[9:].strip() or "recent events"
            try:
                result = torment.query(WORKSPACE_ID, AGENT_ID, peek_q, top_k=TOP_K)
                hits = result.get("hits", result.get("results", []))
                print(f"\n--- Memories for '{peek_q}' ({len(hits)} hits) ---")
                for h in hits:
                    s = h.get("summary", "?")
                    sc = h.get("final_score", h.get("score", 0))
                    tier = h.get("character_tier", "")
                    print(f"  [{sc:.2f}] {tier:12s} | {s[:100]}")
                print("---\n")
            except Exception as e:
                print(f"  Error: {e}\n")
            continue

        if user_input.lower() == "/clear":
            conversation.clear()
            print("  Conversation cleared. Memories persist.\n")
            continue

        # Query TORMENT
        try:
            query_result = torment.query(WORKSPACE_ID, AGENT_ID, user_input, top_k=TOP_K)
            last_query_result = query_result
        except Exception as e:
            print(f"  [TORMENT query failed: {e}]\n")
            query_result = {}

        hits = query_result.get("hits", query_result.get("results", []))
        char_ctx = query_result.get("character_context", {})

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            character_context=format_character_context(char_ctx),
            memory_context=format_memories(hits),
            drift_note=format_drift_note(char_ctx),
        ).strip()

        conversation.append({"role": "user", "content": user_input})
        if len(conversation) > 40:
            conversation = conversation[-40:]

        try:
            reply = llm.message(system=system_prompt, messages=conversation, max_tokens=1024)
        except Exception as e:
            print(f"  [LLM error: {e}]\n")
            conversation.pop()
            continue

        conversation.append({"role": "assistant", "content": reply})
        print(f"\nRyuki > {reply}\n")

        step += 1
        try:
            torment.ingest(WORKSPACE_ID, AGENT_ID, build_summary(user_input, reply), step=step)
        except Exception as e:
            print(f"  [TORMENT ingest failed: {e}]\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"\n  Initializing Ryuki Nox...")
    print(f"  LLM: {OPENAI_MODEL} @ {OPENAI_BASE_URL}")
    print()

    torment = TormentClient(TORMENT_URL)
    llm = OpenAICompatClient(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY, model=OPENAI_MODEL)

    ensure_setup(torment)
    chat_loop(torment, llm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
