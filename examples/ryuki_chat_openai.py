#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
examples/ryuki_chat_openai.py — Ryuki Nox chat client (OpenAI-compatible backends)

Connects TORMENT (local memory service) to any OpenAI-compatible chat-completions
endpoint to create a persistent Ryuki-specific runtime.

Supported backends include:
- Ollama
- LM Studio
- OpenAI
- any local or remote endpoint exposing an OpenAI-compatible /chat/completions API

This example is:
- a real single-character chat client
- Ryuki-specific on purpose
- backed by TORMENT memory retrieval and ingest
- vendor-flexible on the LLM side

This example is NOT:
- a generic chat client
- an MCP client
- a multi-agent collective client

Requirements:
    pip install requests openai

Typical setups:

1) Ollama (default-friendly)
    - Start Ollama and pull a model:
        ollama pull llama3.1
    - Start TORMENT:
        python -m torment_service.app
    - Run:
        python examples/ryuki_chat_openai.py

2) LM Studio
    - Start your local server
    - Set:
        set OPENAI_BASE_URL=http://localhost:1234/v1
        set OPENAI_MODEL=your-loaded-model
    - Run:
        python examples/ryuki_chat_openai.py

3) OpenAI
    - Set:
        set OPENAI_API_KEY=sk-...
        set OPENAI_BASE_URL=https://api.openai.com/v1
        set OPENAI_MODEL=gpt-4o
    - Run:
        python examples/ryuki_chat_openai.py

Useful env overrides:
    TORMENT_URL=http://127.0.0.1:8787
    TORMENT_WORKSPACE=ryuki
    TORMENT_AGENT=ryuki_nox
    TORMENT_TOP_K=8

Commands:
    Type your message to talk with Ryuki.
    'quit' or 'exit' to leave.

    /status              — show runtime settings
    /identity            — show current agent identity
    /debug               — show last raw query result
    /memories <query>    — peek at what TORMENT would retrieve
    /clear               — clear local chat history only (memories persist)

Notes:
- For Ollama, a placeholder OPENAI_API_KEY is fine; many local servers ignore it.
- This client assumes a chat-completions compatible endpoint.
- NEVER hardcode secrets in files.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import textwrap
import time
from typing import Any, Dict, List, Optional

import requests

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Env helpers / config
# ---------------------------------------------------------------------------

def _env(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value if value else default


TORMENT_URL = _env("TORMENT_URL", "http://127.0.0.1:8787").rstrip("/")
WORKSPACE_ID = _env("TORMENT_WORKSPACE", "ryuki")
AGENT_ID = _env("TORMENT_AGENT", "ryuki_nox")
TOP_K = int(_env("TORMENT_TOP_K", "8"))

OPENAI_BASE_URL = _env("OPENAI_BASE_URL", "http://localhost:11434/v1").rstrip("/")
OPENAI_API_KEY = _env("OPENAI_API_KEY", "ollama")
OPENAI_MODEL = _env("OPENAI_MODEL", "llama3.1")

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
# OpenAI-compatible client
# ---------------------------------------------------------------------------

class OpenAICompatClient:
    """
    Talks to any OpenAI-compatible /chat/completions endpoint.
    Uses the OpenAI SDK if available, otherwise falls back to raw requests.
    """

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._sdk = None

        try:
            from openai import OpenAI
            self._sdk = OpenAI(base_url=self.base_url, api_key=self.api_key)
        except ImportError as e:
            log.debug("OpenAI SDK import failed; using raw requests fallback: %s", e)

    def message(self, system: str, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        all_messages = [{"role": "system", "content": system}] + messages

        if self._sdk:
            resp = self._sdk.chat.completions.create(
                model=self.model,
                messages=all_messages,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""

        response = requests.post(
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
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_memories(hits: List[Dict[str, Any]]) -> str:
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


def build_summary(user_msg: str, reply: str) -> str:
    user_short = user_msg[:200].strip()
    reply_short = reply[:300].strip()
    reply_short = reply_short.replace("\n\n", "\n").strip()

    return (
        f"Zen said: {user_short}\n"
        f"Ryuki responded: {reply_short}"
    )


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def ensure_setup(torment: TormentClient) -> None:
    section("Initializing Ryuki Nox (OpenAI-compatible backend)")

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
    print("  Ryuki Nox — Live Chat (OpenAI-compatible backend)")
    print("=" * 72)
    print(f"  Workspace:      {WORKSPACE_ID}")
    print(f"  Agent:          {AGENT_ID}")
    print(f"  LLM endpoint:   {OPENAI_BASE_URL}")
    print(f"  LLM model:      {OPENAI_MODEL}")
    print(f"  Top-K:          {TOP_K}")
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


def chat_loop(torment: TormentClient, llm: OpenAICompatClient) -> None:
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

        if lower == "/status":
            section("Runtime status")
            info(f"TORMENT_URL:      {TORMENT_URL}")
            info(f"WORKSPACE_ID:     {WORKSPACE_ID}")
            info(f"AGENT_ID:         {AGENT_ID}")
            info(f"OPENAI_BASE_URL:  {OPENAI_BASE_URL}")
            info(f"OPENAI_MODEL:     {OPENAI_MODEL}")
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

        # 3) Call OpenAI-compatible backend
        conversation.append({"role": "user", "content": user_input})
        if len(conversation) > 40:
            conversation = conversation[-40:]

        try:
            reply = llm.message(
                system=system_prompt,
                messages=conversation,
                max_tokens=1024,
            )
        except Exception as e:
            print(f"  [LLM error: {e}]\n")
            conversation.pop()
            continue

        conversation.append({"role": "assistant", "content": reply})

        # 4) Show reply
        print(f"\nRyuki > {reply}\n")

        # 5) Ingest compact summary
        step += 1
        try:
            torment.ingest(WORKSPACE_ID, AGENT_ID, build_summary(user_input, reply), step=step)
        except Exception as e:
            print(f"  [TORMENT ingest failed: {e}]\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("\n  Preparing OpenAI-compatible Ryuki runtime...\n")

    torment = TormentClient(TORMENT_URL)
    llm = OpenAICompatClient(
        base_url=OPENAI_BASE_URL,
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
    )

    ensure_setup(torment)
    chat_loop(torment, llm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())