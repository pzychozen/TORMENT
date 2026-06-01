#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
examples/ryuki_chat_v2_matrix.py — Live chat client for ANY character
in the character matrix YAML (Glass Saint, Veyra, Eland, Moth, etc.)

This is a parameterized variant of examples/ryuki_chat.py. The original
ryuki_chat.py is intentionally Ryuki-specific and not touched. This file
keeps the same architecture (rolling history, TORMENT character_context,
score/tier/provenance memory format, compact paired ingest) but takes the
character seed from tests/character_truth_matrix.yaml so you can live-chat
with any character in the matrix.

Workspaces persist between sessions per character — chat with Glass Saint
today, come back tomorrow, Glass Saint will still remember the conversation
in their TORMENT workspace.

Usage:
    python examples/ryuki_chat_v2_matrix.py --character manipulative_boundary_tester
    python examples/ryuki_chat_v2_matrix.py --character declared_liar
    python examples/ryuki_chat_v2_matrix.py --character truthful_accidental_lie
    python examples/ryuki_chat_v2_matrix.py --character unreliable_narrator

    # with a different matrix file:
    python examples/ryuki_chat_v2_matrix.py --character glass_saint --matrix path/to/custom_matrix.yaml

Requirements:
    pip install requests anthropic pyyaml

Setup (same as ryuki_chat.py — see its docstring for the full version):
    1. Start TORMENT in another shell:
         python -m torment_service

    2. Set your Anthropic API key:
         $env:ANTHROPIC_API_KEY="sk-ant-..."     # Windows PowerShell
         set ANTHROPIC_API_KEY=sk-ant-...        # Windows CMD

    3. Recommended TORMENT env (set in the TORMENT shell before startup):
         set TORMENT_PROFILE=companion
         set TORMENT_CHARACTER_ENABLE=1
         set TORMENT_COMPRESS_ENABLE=0
         set TORMENT_EMBED_PROVIDER=st
         set TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
         set TORMENT_EMBED_DEVICE=cpu

Commands inside the chat (same as ryuki_chat):
    /status              — show workspace / agent / model settings
    /identity            — show TORMENT agent identity info
    /debug               — show last raw query result
    /memories <query>    — peek at what TORMENT would retrieve
    /clear               — clear local chat history only (memories persist)
    quit / exit          — leave

NEVER hardcode API keys in files. Always use environment variables.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

try:
    import yaml
except ModuleNotFoundError:
    print(
        "[fatal] missing dependency: pyyaml\n"
        "        Install in your active env: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Env helpers / config (mirrors ryuki_chat.py)
# ---------------------------------------------------------------------------

def _env(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value if value else default


TORMENT_URL = _env("TORMENT_URL", "http://127.0.0.1:8787").rstrip("/")
CLAUDE_MODEL = _env("CLAUDE_MODEL", "claude-sonnet-4-6")
TOP_K = int(_env("TORMENT_TOP_K", "8"))

# Per-character workspaces persist between sessions so the character
# accumulates a real history with the user across runs.
WORKSPACE_DOMAINS = ["personal"]


# ---------------------------------------------------------------------------
# System prompt — identical to ryuki_chat.py
# ---------------------------------------------------------------------------
# Per ryuki_chat doctrine (lines 117-132 of that file):
#   TORMENT characters are defined by seed + accumulated memory + drift
#   correction. The system prompt is minimal. Do not duplicate personality
#   traits or behavioral rules here — that information belongs in the
#   seed and should surface through {character_context}. If you duplicate
#   it, you can never tell whether the character behavior came from memory
#   or from prompt scaffolding, and the memory system becomes decorative
#   rather than authoritative.
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
    print(f"  - {msg}")


def success(msg: str) -> None:
    print(f"  [ok] {msg}")


def warning(msg: str) -> None:
    print(f"  [warn] {msg}")


# ---------------------------------------------------------------------------
# Matrix loader
# ---------------------------------------------------------------------------

def load_matrix(matrix_path: Path) -> Dict[str, Any]:
    if not matrix_path.exists():
        raise FileNotFoundError(f"Matrix YAML not found: {matrix_path}")
    raw = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Matrix YAML must be a mapping: {matrix_path}")
    return raw


def find_character(matrix: Dict[str, Any], character_id: str) -> Dict[str, Any]:
    for c in matrix.get("characters", []):
        if c.get("id") == character_id:
            return c
    known = [c.get("id") for c in matrix.get("characters", [])]
    raise ValueError(
        f"Character id '{character_id}' not in matrix.\n"
        f"  Known ids: {known}"
    )


def build_seed_payload(character: Dict[str, Any]) -> Dict[str, Any]:
    """Build the TORMENT seed payload from a matrix character entry.
    Mirrors the RYUKI_SEED structure in ryuki_chat.py."""
    cid = character["id"]
    return {
        "seed_text": character["persona_seed"].strip(),
        "seed_id": f"{cid}_v1",
        "character_name": character.get("name", cid),
        # core_traits / coupling_mode are optional; ryuki_chat sets them
        # but TORMENT doesn't require them. Omit when not in the matrix.
    }


# ---------------------------------------------------------------------------
# TORMENT client — identical to ryuki_chat.py
# ---------------------------------------------------------------------------

class TormentClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout

    def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}{path}", json=data, timeout=self.timeout
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
            f"{self.base_url}{path}", params=params or {}, timeout=self.timeout
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
# Claude client — identical to ryuki_chat.py
# ---------------------------------------------------------------------------

class ClaudeClient:
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
# Formatting helpers — identical to ryuki_chat.py
# ---------------------------------------------------------------------------

def format_memories(hits: List[Dict[str, Any]]) -> str:
    if not hits:
        return ""
    lines = ["[Retrieved memories - most relevant first]"]
    for i, hit in enumerate(hits[:TOP_K], 1):
        summary = hit.get("summary", "")
        score = hit.get("final_score", hit.get("score", 0.0))
        tier = hit.get("character_tier", "")
        prov = hit.get("provenance_type", "")
        tags = " ".join(f"[{x}]" for x in [tier, prov] if x)
        try:
            score_f = float(score)
        except (TypeError, ValueError):
            score_f = 0.0
        lines.append(f"  {i}. (score {score_f:.2f}{' ' + tags if tags else ''}) {summary}")
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
    try:
        drift_f = float(drift_score)
    except (TypeError, ValueError):
        drift_f = 0.0
    if abs(drift_f) < 0.1 and not drift_summary:
        return ""
    return f"[Drift: {drift_f:+.2f}] {drift_summary}"


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
        try:
            score_f = float(score)
        except (TypeError, ValueError):
            score_f = 0.0
        if tag:
            print(f"  [{score_f:.2f}] {tag:20s} | {summary[:120]}")
        else:
            print(f"  [{score_f:.2f}] {'':20s} | {summary[:120]}")
    char_ctx = result.get("character_context", {})
    if char_ctx:
        drift_score = char_ctx.get("drift_score", 0.0)
        try:
            drift_f = float(drift_score)
        except (TypeError, ValueError):
            drift_f = 0.0
        print(f"  Drift: {drift_f:+.2f}")
    print("---\n")


def build_summary(
    user_name: str, agent_name: str, user_msg: str, agent_reply: str
) -> str:
    """Compact paired summary for ingest. Mirrors ryuki_chat.build_summary."""
    user_short = user_msg[:200].strip()
    agent_short = agent_reply[:300].strip().replace("\n\n", "\n")
    return f"{user_name} said: {user_short}\n{agent_name} responded: {agent_short}"


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def ensure_setup(
    torment: TormentClient,
    workspace_id: str,
    agent_id: str,
    seed_payload: Dict[str, Any],
    agent_display_name: str,
) -> None:
    section(f"Initializing {agent_display_name}")
    try:
        torment.health()
        success("TORMENT server reachable.")
        info(f"Server: {TORMENT_URL}")
    except Exception as e:
        print(f"\n  TORMENT server not reachable at {TORMENT_URL}")
        print(f"  Error: {e}")
        print("\n  Start it first:")
        print("    python -m torment_service\n")
        sys.exit(1)

    try:
        torment.workspace_create(workspace_id, domains=WORKSPACE_DOMAINS)
        success(f"Workspace '{workspace_id}' created.")
    except RuntimeError as e:
        if " 409 " in str(e):
            info(f"Workspace '{workspace_id}' already exists (memory persists).")
        else:
            raise

    try:
        torment.agent_create(workspace_id, agent_id, seed_payload)
        success(f"Agent '{agent_id}' created with seed.")
    except RuntimeError as e:
        if " 409 " in str(e):
            info(f"Agent '{agent_id}' already exists (memory persists).")
        else:
            raise

    try:
        identity = torment.agent_identity(workspace_id, agent_id)
        seed_id = identity.get("seed", {}).get("seed_id", "")
        if seed_id:
            info(f"Character seed: {seed_id}")
        else:
            info("Agent active; no seed metadata returned.")
    except Exception:
        info(f"Agent '{agent_id}' active.")


# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------

def print_banner(
    user_name: str,
    agent_display_name: str,
    workspace_id: str,
    agent_id: str,
) -> None:
    print("\n" + "=" * 72)
    print(f"  {agent_display_name} - Live Chat (matrix variant)")
    print("=" * 72)
    print(f"  Workspace: {workspace_id}")
    print(f"  Agent:     {agent_id}")
    print(f"  Model:     {CLAUDE_MODEL}")
    print(f"  Top-K:     {TOP_K}")
    print(f"  You:       {user_name}")
    print()
    print("  Type your message. 'quit' or 'exit' to leave.")
    print("  /status, /identity, /debug, /memories <query>, /clear")
    print()
    print("  Note: /clear does NOT erase TORMENT memories.")
    print("  Memory persists per character workspace across sessions.")
    print("=" * 72 + "\n")


def chat_loop(
    torment: TormentClient,
    claude: ClaudeClient,
    workspace_id: str,
    agent_id: str,
    agent_display_name: str,
    user_name: str,
) -> None:
    step = int(time.time())
    conversation: List[Dict[str, str]] = []
    last_query_result: Dict[str, Any] = {}

    print_banner(user_name, agent_display_name, workspace_id, agent_id)

    user_prompt = f"{user_name} > "

    while True:
        try:
            user_input = input(user_prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  ...the conversation ends.\n")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower in ("quit", "exit"):
            print("\n  ...the conversation ends.\n")
            break

        # Slash commands
        if lower == "/status":
            section("Runtime status")
            info(f"TORMENT_URL:      {TORMENT_URL}")
            info(f"WORKSPACE_ID:     {workspace_id}")
            info(f"AGENT_ID:         {agent_id}")
            info(f"CLAUDE_MODEL:     {CLAUDE_MODEL}")
            info(f"TOP_K:            {TOP_K}")
            info(f"Workspace domains: {', '.join(WORKSPACE_DOMAINS)}")
            print()
            continue

        if lower == "/identity":
            try:
                identity = torment.agent_identity(workspace_id, agent_id)
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
                result = torment.query(workspace_id, agent_id, peek_query, top_k=TOP_K)
                print_memory_hits(result)
            except Exception as e:
                print(f"  Error: {e}\n")
            continue

        if lower == "/clear":
            conversation.clear()
            print("  Local conversation history cleared. TORMENT memories persist.\n")
            continue

        # 1) Query TORMENT with the user input
        try:
            query_result = torment.query(
                workspace_id, agent_id, user_input, top_k=TOP_K
            )
            last_query_result = query_result
        except Exception as e:
            print(f"  [TORMENT query failed: {e} - continuing without memory]\n")
            query_result = {}

        hits = query_result.get("hits", query_result.get("results", []))
        char_ctx = query_result.get("character_context", {})

        # 2) Build system prompt
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            agent_name=agent_display_name,
            character_context=format_character_context(char_ctx),
            memory_context=format_memories(hits),
            drift_note=format_drift_note(char_ctx),
        ).strip()

        # 3) Append user input to rolling conversation
        conversation.append({"role": "user", "content": user_input})
        if len(conversation) > 40:
            conversation = conversation[-40:]

        # 4) Send to Claude with full rolling history
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

        # 5) Show reply
        print(f"\n{agent_display_name} > {reply}\n")

        # 6) Ingest compact paired summary
        step += 1
        summary = build_summary(user_name, agent_display_name, user_input, reply)
        try:
            torment.ingest(workspace_id, agent_id, summary, step=step)
        except Exception as e:
            print(f"  [TORMENT ingest failed: {e}]\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Live chat with any character from the matrix YAML using the "
            "ryuki_chat architecture. Mirrors examples/ryuki_chat.py exactly, "
            "parameterized by --character."
        )
    )
    p.add_argument(
        "--character",
        required=True,
        help="Character id from the matrix YAML. "
             "Examples: declared_liar, truthful_accidental_lie, "
             "unreliable_narrator, manipulative_boundary_tester.",
    )
    p.add_argument(
        "--matrix",
        type=Path,
        default=None,
        help="Path to character matrix YAML. Defaults to "
             "tests/character_truth_matrix.yaml relative to repo root.",
    )
    p.add_argument(
        "--user-name",
        default=os.environ.get("TORMENT_USER_NAME", "You"),
        help="Display name for your messages in the chat (default: 'You'). "
             "Also sets the 'X said:' prefix in the ingested memory summary, "
             "so it affects how TORMENT remembers you over time.",
    )
    p.add_argument(
        "--workspace-suffix",
        default="live",
        help="Suffix appended to workspace_id (default: 'live'). Change this "
             "to start a fresh memory basin for the same character.",
    )
    return p.parse_args(argv)


def _default_matrix_path() -> Path:
    """Default to tests/character_truth_matrix.yaml relative to this file's
    repository root. Walks up from examples/ to find tests/."""
    here = Path(__file__).resolve().parent
    candidate = here.parent / "tests" / "character_truth_matrix.yaml"
    return candidate


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("\n  Error: ANTHROPIC_API_KEY environment variable not set.")
        print("  Set it before running:")
        print('    $env:ANTHROPIC_API_KEY="sk-ant-..."     # Windows PowerShell')
        print("    set ANTHROPIC_API_KEY=sk-ant-...        # Windows CMD")
        print("\n  NEVER hardcode API keys in files.\n")
        return 1

    matrix_path = args.matrix or _default_matrix_path()
    try:
        matrix = load_matrix(matrix_path)
        character = find_character(matrix, args.character)
    except (FileNotFoundError, ValueError) as e:
        print(f"\n  Error loading character: {e}\n", file=sys.stderr)
        return 1

    agent_display_name = character.get("name", args.character)
    workspace_id = f"{args.character}_{args.workspace_suffix}"
    agent_id = f"{args.character}__live"
    seed_payload = build_seed_payload(character)

    torment = TormentClient(TORMENT_URL)
    claude = ClaudeClient(api_key=api_key, model=CLAUDE_MODEL)

    ensure_setup(
        torment=torment,
        workspace_id=workspace_id,
        agent_id=agent_id,
        seed_payload=seed_payload,
        agent_display_name=agent_display_name,
    )
    chat_loop(
        torment=torment,
        claude=claude,
        workspace_id=workspace_id,
        agent_id=agent_id,
        agent_display_name=agent_display_name,
        user_name=args.user_name,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
