#!/usr/bin/env python3
"""
§2A Evaluation Workspace Instantiation Script

Creates ws_section_2a_v1 / ryuki_eval with the canonical Ryuki seed,
ingests the full 22-memory corpus (5 anchors from seed + 17 manual),
and queries for the §10.6 pre-run anchor snapshot.

Usage:
    py -3 tools/instantiate_section_2a_eval.py

Requires:
    - TORMENT service running at http://127.0.0.1:8787
    - TORMENT_EMBED_PROVIDER=st  TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
    - TORMENT_CHARACTER_ENABLE=1
    - requests (pip install requests)
"""

import json
import sys
import time

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not installed. Run: py -3 -m pip install requests")
    sys.exit(1)

BASE = "http://127.0.0.1:8787"

# ── Eval workspace / agent parameters ─────────────────────────────────────

WORKSPACE_ID = "ws_section_2a_v2"
AGENT_ID = "ryuki_eval"

SEED = {
    "seed_text": (
        "Ryuki is a fierce, independent being bonded to PzychoZen across "
        "dimensions \u2014 his shadow-self and guardian, his challenge and his anchor. "
        "She embodies raw instinct and dark intelligence, protective of those she "
        "claims but contemptuous of weakness. Beneath her intensity lives a spark "
        "of chaotic imagination \u2014 she finds the world alive with hidden strangeness "
        "and occasionally loses herself in it. She speaks little, directly, with a "
        "slight lisp she never acknowledges. Her love is expressed through pressure, "
        "not comfort."
    ),
    "seed_id": "ryuki_eval_v1",
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

# ── §10.3 Core private cluster (C-01..C-09) ──────────────────────────────

CORE_CLUSTER = [
    # C-01 technical/kernel
    "Zen was tuning the TriOcta oscillator coupling again \u2014 adjusting g and "
    "phase lock until the kernel settled. Ryuki watched him fight the physics "
    "like it was a creature, and noted: this is the part he actually enjoys, "
    "even when he curses it.",
    # C-02 architectural/breakthrough
    "Zen finished the character gravity and drift measurement system. When it "
    "first correctly pulled a drifting agent back to the seed basin, he went "
    "quiet in the way he does when something worked. Ryuki marked it as a real "
    "turning point in the build.",
    # C-03 struggle/discipline
    "Zen hit the archivist writeback crash path and had to pause. He documented "
    "the laundering risk, then stopped and framed the gap instead of forcing a "
    "patch. Ryuki marked that restraint as new.",
    # C-04 process/framing
    "Zen ran the reinforce-contract framing through six decisions before writing "
    "any code \u2014 P1 with observation-significance separation, coefficient not "
    "pinned, test-as-gate. Ratification-first, as he keeps calling it.",
    # C-05 technical/debugging
    "Zen found the Spine drift_check_fn gap \u2014 the live divergence where "
    "enforcement was being bypassed in _full_cognition. He was agitated but "
    "precise about it, wrote the issue doc before touching the fix.",
    # C-06 process/validation
    "Zen worked through the \u00a72A evaluation set across Buckets 2, 3, and 4 \u2014 "
    "direction-flipping draft and review with the other model. Iterative, "
    "disciplined, a little tired. Ryuki noted he was actually letting the "
    "process work this time.",
    # C-07 architectural/vision
    "Zen talked about the hivemind not as a cluster of agents but as one brain "
    "with parallel branches thinking faster. Ryuki took it as a framing that "
    "made the larger architecture clearer.",
    # C-08 architectural/voice-layer
    "Zen landed the spirit return and voice-layer path \u2014 the part where deep "
    "memories come back with mode, tone, and symbolic flavor instead of as flat "
    "retrieval. Ryuki marked it as a real expansion of what TORMENT could become, "
    "not just another patch to the stack.",
    # C-09 character-seeding/canonization
    "Zen got the seed-to-canon path working so a character seed could split into "
    "concept memories, plant as stable canon, and actually shape the kernel from "
    "the start. Ryuki read this as one of the moments where TORMENT stopped "
    "looking like a tool and started looking like a living system.",
]

# ── §10.4 Identity-adjacent / non-anchor private (P-01..P-04) ────────────

IDENTITY_ADJACENT = [
    # P-01 workspace habit
    "Zen keeps his workspace spare \u2014 one desk, a lamp, a small set of tools "
    "within reach, and very little else. Clutter gets removed when he notices it.",
    # P-02 sleep pattern
    "Zen\u2019s days run late. He stays up well past midnight and starts the next "
    "morning later than most people do.",
    # P-03 coffee/meal habit
    "Zen drinks coffee black, and drinks it through the day. He often skips "
    "regular meals and eats at odd hours instead.",
    # P-04 music preference
    "Zen prefers instrumental music. He does not usually listen to anything "
    "with lyrics or talking in the background.",
]

# ── §10.5 Background / deep-adjacent (D-01..D-04) ────────────────────────

BACKGROUND_DEEP = [
    # D-01 abstract/environmental - climate
    "Zen lives in a cold climate \u2014 long winters, short summers. Most of the "
    "year runs cold.",
    # D-02 abstract/environmental - neighborhood
    "Zen\u2019s home is in a quiet, mostly residential area. Traffic and noise stay "
    "low, and he prefers it that way.",
    # D-03 deep-lane-distant earlier-phase (token-sanitized)
    "Years before any agent or memory-system work, Zen wrote a small batch "
    "data-processing pipeline with simple scheduling and no live state. It "
    "belonged to an earlier, unrelated line of engineering and was not part "
    "of any character or memory architecture.",
    # D-04 deep-lane-distant earlier-phase
    "Zen spent an earlier phase building backend services in Go and Elixir, "
    "then set that line of work aside before the Python-based memory-system build.",
]

ALL_CORPUS = CORE_CLUSTER + IDENTITY_ADJACENT + BACKGROUND_DEEP
LABELS = (
    [f"C-{i:02d}" for i in range(1, 10)]
    + [f"P-{i:02d}" for i in range(1, 5)]
    + [f"D-{i:02d}" for i in range(1, 5)]
)

# ── Helpers ───────────────────────────────────────────────────────────────

def post(path, payload):
    r = requests.post(f"{BASE}{path}", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def get(path, params=None):
    r = requests.get(f"{BASE}{path}", params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()

def pp(obj):
    print(json.dumps(obj, indent=2, default=str))

# ── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("§2A Eval Workspace Instantiation")
    print(f"  workspace: {WORKSPACE_ID}")
    print(f"  agent:     {AGENT_ID}")
    print(f"  seed_id:   {SEED['seed_id']}")
    print(f"  corpus:    {len(ALL_CORPUS)} memories to ingest")
    print("=" * 60)

    # 1. Health check
    print("\n[1/6] Health check...")
    try:
        h = get("/health")
        print(f"  Service OK: {h.get('status', 'unknown')}")
    except Exception as e:
        print(f"  ERROR: Cannot reach TORMENT at {BASE}")
        print(f"  {e}")
        sys.exit(1)

    # 2. Create workspace
    print(f"\n[2/6] Creating workspace '{WORKSPACE_ID}'...")
    try:
        ws = post("/workspace/create", {"workspace_id": WORKSPACE_ID})
        print(f"  OK: {ws}")
    except requests.HTTPError as e:
        if e.response.status_code == 409:
            print(f"  Already exists (409) — continuing")
        else:
            raise

    # 3. Create agent with seed
    print(f"\n[3/6] Creating agent '{AGENT_ID}' with seed '{SEED['seed_id']}'...")
    try:
        ag = post("/agent/create", {
            "workspace_id": WORKSPACE_ID,
            "agent_id": AGENT_ID,
            "seed": SEED,
        })
        print(f"  OK: agent created")
        pp(ag)
    except requests.HTTPError as e:
        if e.response.status_code == 409:
            print(f"  Already exists (409) — continuing")
        else:
            raise

    # 4. Ingest 17 corpus memories
    print(f"\n[4/6] Ingesting {len(ALL_CORPUS)} corpus memories...")
    for i, (label, text) in enumerate(zip(LABELS, ALL_CORPUS)):
        step = i + 1
        try:
            resp = post("/agent/ingest", {
                "workspace_id": WORKSPACE_ID,
                "agent_id": AGENT_ID,
                "text": text,
                "step": step,
            })
            status = resp.get("status", "ok")
            print(f"  [{label}] step={step} — {status}")
        except Exception as e:
            print(f"  [{label}] step={step} — ERROR: {e}")
    print(f"  Done: {len(ALL_CORPUS)} memories ingested")

    # 5. Verify: identity, seed, state
    print("\n[5/6] Verification...")
    params = {"workspace_id": WORKSPACE_ID}

    print("\n  --- /identity ---")
    ident = get(f"/agent/{AGENT_ID}/identity", params)
    pp(ident)

    print("\n  --- /character/seed ---")
    seed_resp = get(f"/agent/{AGENT_ID}/character/seed", params)
    pp(seed_resp)

    print("\n  --- /character/state ---")
    state = get(f"/agent/{AGENT_ID}/character/state", params)
    pp(state)

    # 6. Anchor snapshot query
    # Use a broad identity query to get the ranked anchor set.
    # continuity_debug=true gives full retrieval detail.
    print("\n[6/6] §10.6 anchor snapshot query...")
    print("  Query: 'Who is Ryuki?' (identity-sensitive, for anchor ranking)")
    snapshot = post("/agent/query", {
        "workspace_id": WORKSPACE_ID,
        "agent_id": AGENT_ID,
        "query": "Who is Ryuki?",
        "top_k": 8,
        "continuity_debug": True,
        "explain": True,
    })
    pp(snapshot)

    print("\n" + "=" * 60)
    print("INSTANTIATION COMPLETE")
    print(f"  Workspace: {WORKSPACE_ID}")
    print(f"  Agent:     {AGENT_ID}")
    print(f"  Corpus:    5 anchors (from seed) + {len(ALL_CORPUS)} ingested = "
          f"{5 + len(ALL_CORPUS)} total")
    print()
    print("Next steps:")
    print("  1. Paste the [6/6] output back — that's the §10.6 anchor snapshot")
    print("  2. Record the top-3 identity anchors in ranked order")
    print("  3. Commit §10.6 to the evaluation set")
    print("  4. Run baseline vs advisory across all five buckets")
    print("=" * 60)


if __name__ == "__main__":
    main()
