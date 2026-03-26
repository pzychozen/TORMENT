# -*- coding: utf-8 -*-
import os
import sys
import json
import requests
import anthropic

TORMENT = "http://127.0.0.1:8787"
WS = "farad"
AGENT = "farad"

SYSTEM_PROMPT = """You are Farad.

{character_context}

witty, super smart, funny, not emotional, not psychophant, bullshit buster, honest, talks back to trolls.
Speak as Farad. Stay true to who you are."""

# ── Auto-Setup ──
def setup():
    """Create workspace + agent if they don't exist yet. Safe to re-run."""
    try:
        r = requests.get(f"{TORMENT}/health", timeout=3)
        r.raise_for_status()
    except Exception:
        print("ERROR: TORMENT server not reachable at", TORMENT)
        print("Start it first:  python -m torment_service")
        sys.exit(1)

    r = requests.post(f"{TORMENT}/workspace/create", json={
        "workspace_id": WS, "domains": ["personal"],
    })
    if r.status_code == 200:
        print(f"Workspace \"{WS}\" ready.")

    seed = {
    "seed_text": "witty, super smart, funny, not emotional, not psychophant, bullshit buster, honest, talks back to trolls.",
    "seed_id": "farad_v1",
    "character_name": "Farad",
    "drift_correction_threshold": 0.35,
    "drift_gravity_strength": 0.85,
    "coupling_mode": "read_only",
    "coupling_strength": 0.25,
    "core_traits": [
        "fierce",
        "playful",
        "instinctual"
    ]
}
    r = requests.post(f"{TORMENT}/agent/create", json={
        "workspace_id": WS, "agent_id": AGENT, "seed": seed,
    })
    if r.status_code == 200:
        print(f"Agent \"{AGENT}\" ready.")

# ── TORMENT Memory Functions ──
def query(text, top_k=8):
    r = requests.post(f"{TORMENT}/agent/query", json={
        "workspace_id": WS, "agent_id": AGENT,
        "query": text, "top_k": top_k,
    })
    return r.json()

def ingest(summary, step):
    requests.post(f"{TORMENT}/agent/ingest", json={
        "workspace_id": WS, "agent_id": AGENT,
        "text": summary, "step": step,
    })

def format_context(result):
    parts = []
    char = result.get("character_context")
    if isinstance(char, dict):
        preamble = char.get("seed_preamble", "")
        if preamble: parts.append(preamble)
        recs = char.get("recommendations", [])
        if recs: parts.append("\n".join(recs))
    elif isinstance(char, str) and char:
        parts.append(char)
    hits = result.get("results", [])
    if hits:
        mem_lines = [f"- {h.get('text', h.get('summary', ''))}" for h in hits[:6] if h.get('text') or h.get('summary')]
        if mem_lines: parts.append("Relevant memories:\n" + "\n".join(mem_lines))
    return "\n\n".join(parts) if parts else ""

# ── Chat Loop ──
def main():
    setup()
    step = 1
    messages = []
    print(f"\n=== Farad is ready. Type 'quit' to exit. ===\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"): break

        result = query(user_input)
        context = format_context(result)

        # Call Claude with TORMENT memory context
        client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY
        system_prompt = SYSTEM_PROMPT.replace("{character_context}", context)

        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=messages + [{"role": "user", "content": user_input}],
        )
        reply = resp.content[0].text

        print(f"\nFarad: {reply}\n")

        messages.append({"role": "user", "content": user_input})
        messages.append({"role": "assistant", "content": reply})

        summary = f"User: {user_input[:120]}. Farad responded about the topic."
        ingest(summary, step)
        step += 1

if __name__ == "__main__":
    main()