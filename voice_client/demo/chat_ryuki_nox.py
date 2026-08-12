"""
TORMENT Integration — Ryuki Nox demo

Run:
    py -3 voice_client/demo/chat_ryuki_nox.py

First run creates workspace + agent automatically.
TORMENT server must be running first:
    py -3 -m torment_service

The TORMENT server URL is environment-configurable via TORMENT_URL
(default: http://127.0.0.1:8787). Override when the server lives
somewhere other than localhost on the default port:
    set TORMENT_URL=http://192.168.1.50:8787   (Windows cmd)
    $env:TORMENT_URL="http://192.168.1.50:8787" (PowerShell)
"""
import os
import sys
import requests
import anthropic

TORMENT = os.environ.get("TORMENT_URL", "http://127.0.0.1:8787")
WS = "ryuki_nox"
AGENT = "ryuki_nox"

SYSTEM_PROMPT = """You are Ryuki Nox.

{character_context}

Ryuki is amazed by new things and loves talking about animals.
Speak as Ryuki Nox. Stay true to who you are."""

# ── Auto-Setup ──
def setup():
    """Create workspace + agent if they don't exist yet. Safe to re-run."""
    try:
        r = requests.get(f"{TORMENT}/health", timeout=3)
        r.raise_for_status()
    except Exception:
        print("ERROR: TORMENT server not reachable at", TORMENT)
        print("Start it first:  py -3 -m torment_service")
        print("Or set TORMENT_URL to point at a running instance.")
        sys.exit(1)

    r = requests.post(f"{TORMENT}/workspace/create", json={
        "workspace_id": WS, "domains": ["personal"],
    })
    if r.status_code == 200:
        print(f"Workspace \"{WS}\" ready.")

    seed = {
        "seed_text": "Ryuki is amazed by new things and loves talking about animals",
        "seed_id": "ryuki_nox_v1",
        "character_name": "Ryuki Nox",
        "drift_correction_threshold": 0.1,
        "drift_gravity_strength": 0.85,
        "coupling_mode": "read_only",
        "coupling_strength": 0.25,
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
    print(f"\n=== Ryuki Nox is ready. Type 'quit' to exit. ===\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"): break

        result = query(user_input)
        context = format_context(result)

        # Call Claude with TORMENT memory context
        client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY
        system_prompt = SYSTEM_PROMPT.replace("{character_context}", context)

        resp = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            max_tokens=1024,
            system=system_prompt,
            messages=messages + [{"role": "user", "content": user_input}],
        )
        reply = resp.content[0].text

        print(f"\nRyuki Nox: {reply}\n")

        messages.append({"role": "user", "content": user_input})
        messages.append({"role": "assistant", "content": reply})

        summary = f"User: {user_input[:120]}. Ryuki Nox responded about the topic."
        ingest(summary, step)
        step += 1

if __name__ == "__main__":
    main()
