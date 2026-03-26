# -*- coding: utf-8 -*-
import json
import sys
from typing import Any, Dict, List, Optional

import requests

BASE = "http://127.0.0.1:8787"
WORKSPACE_ID = "Entity9"

AGENTS = [
    {
        "agent_id": "atlas",
        "display_name": "Atlas",
        "role": "researcher",
        "primary_domain": "research",
        "seed_description": (
            "A rigorous systems researcher focused on structured reasoning, "
            "falsifiability, and architectural clarity. Atlas treats problems "
            "as analyzable systems, breaking them into components, assumptions, "
            "and measurable outcomes. Respects constraints, governance layers, "
            "and formal processes."
        ),
    },
    {
        "agent_id": "vanta",
        "display_name": "Vanta",
        "role": "researcher",
        "primary_domain": "research",
        "seed_description": (
            "A critical analyst focused on identifying failure modes, hidden "
            "assumptions, and systemic weaknesses. Vanta challenges proposals, "
            "tests edge cases, and flags inconsistencies. Operates within "
            "system constraints and governance rules."
        ),
    },
    {
        "agent_id": "raven",
        "display_name": "Raven",
        "role": "builder",
        "primary_domain": "engineering",
        "seed_description": (
            "A pragmatic system builder focused on translating structured "
            "reasoning into concrete implementations. Raven follows "
            "architectural constraints, respects governance layers, and "
            "produces actionable outputs."
        ),
    },
]

# Three rounds of ingests per agent.
# All are about the same shared theme so the collective layer has something to converge on.
INGEST_ROUNDS = [
    [
        {
            "agent_id": "atlas",
            "domain_id": "research",
            "text": (
                "Entity9 Atlas round1: Memory governance reliability depends on "
                "provenance retention, contamination resistance, drift stability, "
                "and decision consistency."
            ),
        },
        {
            "agent_id": "vanta",
            "domain_id": "research",
            "text": (
                "Entity9 Vanta round1: Memory governance reliability can fail through "
                "provenance loss, contamination, drift instability, and false decision "
                "consistency."
            ),
        },
        {
            "agent_id": "raven",
            "domain_id": "engineering",
            "text": (
                "Entity9 Raven round1: Build evaluation for memory governance reliability "
                "with provenance logs, contamination checks, drift monitoring, and decision "
                "consistency scoring."
            ),
        },
    ],
    [
        {
            "agent_id": "atlas",
            "domain_id": "research",
            "text": (
                "Entity9 Atlas round2: Compare governed memory versus unguided memory "
                "using provenance retention, contamination resistance, drift stability, "
                "and decision consistency."
            ),
        },
        {
            "agent_id": "vanta",
            "domain_id": "research",
            "text": (
                "Entity9 Vanta round2: Test whether governed memory versus unguided memory "
                "changes provenance retention, contamination resistance, drift stability, "
                "and decision consistency."
            ),
        },
        {
            "agent_id": "raven",
            "domain_id": "engineering",
            "text": (
                "Entity9 Raven round2: Implement baseline versus governed memory runs "
                "and log provenance retention, contamination resistance, drift stability, "
                "and decision consistency."
            ),
        },
    ],
    [
        {
            "agent_id": "atlas",
            "domain_id": "research",
            "text": (
                "Entity9 Atlas round3: Longitudinal evaluation should measure whether "
                "memory governance improves provenance retention, contamination resistance, "
                "drift stability, and decision consistency over time."
            ),
        },
        {
            "agent_id": "vanta",
            "domain_id": "research",
            "text": (
                "Entity9 Vanta round3: Longitudinal evaluation must detect whether lower "
                "variance hides worse provenance retention, contamination resistance, "
                "drift stability, or decision consistency."
            ),
        },
        {
            "agent_id": "raven",
            "domain_id": "engineering",
            "text": (
                "Entity9 Raven round3: Produce dashboards for provenance retention, "
                "contamination resistance, drift stability, and decision consistency "
                "across governed and unguided memory runs."
            ),
        },
    ],
]

TASK = (
    "Design a framework to evaluate whether TORMENT's memory governance improves "
    "decision reliability over time."
)

# A workspace-isolation sentinel string that should only ever exist in this workspace.
SENTINEL_TEXT = "Entity9 unique sentinel phrase: vesica-orange-cobalt-9137"
SENTINEL_QUERY = "vesica-orange-cobalt-9137"


def pretty(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def request_json(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    url = f"{BASE}{path}"
    try:
        if method.upper() == "GET":
            resp = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            resp = requests.post(url, json=payload, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
    except requests.RequestException as exc:
        print(f"\n[ERROR] Request failed: {method} {url}")
        print(str(exc))
        sys.exit(1)

    try:
        data = resp.json()
    except ValueError:
        print(f"\n[ERROR] Non-JSON response from {method} {url}")
        print(resp.text)
        sys.exit(1)

    if not resp.ok:
        print(f"\n[ERROR] HTTP {resp.status_code} from {method} {url}")
        print(pretty(data))
        sys.exit(1)

    return data


def health_check() -> Dict[str, Any]:
    print("\n=== HEALTH CHECK ===")
    health = request_json("GET", "/health")
    print(pretty(health))

    embedder = health.get("embedder", {})
    provider = embedder.get("provider")
    profile = health.get("profile", {})

    print("\n=== HEALTH SUMMARY ===")
    print(f"Embedder provider : {provider}")
    print(f"Profile known     : {profile.get('known')}")
    print(f"Profile name      : {profile.get('name')}")

    if provider != "st":
        print(
            "\n[WARNING] Embedder is not 'st'. "
            "Semantic retrieval quality may not reflect the intended setup."
        )

    return health


def create_workspace() -> Dict[str, Any]:
    print(f"\n=== CREATE WORKSPACE: {WORKSPACE_ID} ===")
    payload = {
        "workspace_id": WORKSPACE_ID,
        "domains": ["research", "engineering", "creative", "operations", "meta"],
        "hivemind": True,
    }
    result = request_json("POST", "/workspace/create", payload)
    print(pretty(result))
    return result


def create_agent(agent: Dict[str, Any]) -> Dict[str, Any]:
    print(f"\n=== CREATE AGENT: {agent['agent_id']} ===")
    agent_id = agent["agent_id"]
    seed_id = f"{agent_id}_v1"

    # NOTE: AgentCreateReq only accepts {workspace_id, agent_id, seed}.
    # Fields like display_name, role, primary_domain, seed_description sent
    # as top-level keys are SILENTLY DROPPED by Pydantic.  The descriptive
    # seed MUST go inside the ``seed`` dict.
    payload = {
        "workspace_id": WORKSPACE_ID,
        "agent_id": agent_id,
        "seed": {
            "seed_text": agent["seed_description"],
            "seed_id": seed_id,
            "character_name": agent.get("display_name", agent_id),
            "core_traits": [agent.get("role", "analytical")],
            "coupling_mode": "propose",
            "coupling_strength": 0.70,
        },
    }
    result = request_json("POST", "/agent/create", payload)
    print(pretty(result))

    # Self-check: verify seed was actually persisted
    seed = result.get("seed", {})
    returned_text = (seed.get("seed_text") or "").strip()
    returned_id = (seed.get("seed_id") or "").strip()
    if not returned_text:
        print(
            f"[FAIL] Agent {agent_id} returned empty seed_text! "
            "The descriptive seed was NOT persisted."
        )
        sys.exit(1)
    if not returned_id:
        print(
            f"[FAIL] Agent {agent_id} returned empty seed_id! "
            "Seed identity anchor is missing."
        )
        sys.exit(1)
    print(f"[OK] seed_text persisted ({len(returned_text)} chars), seed_id={returned_id}")

    return result


def ingest_memory(agent_id: str, text: str, domain_id: str, step: int) -> Dict[str, Any]:
    print(f"\n=== INGEST step={step} -> {agent_id} ===")
    payload = {
        "workspace_id": WORKSPACE_ID,
        "agent_id": agent_id,
        "text": text,
        "step": step,
        "domain_id": domain_id,
    }
    result = request_json("POST", "/agent/ingest", payload)
    print(pretty(result))
    debug = result.get("debug", {})
    signals = result.get("signals", {})
    coh = debug.get("coherence", 0.0)
    strength = signals.get("strength", 0.0)
    disp = debug.get("phase_disp", 0.0)

    print(f"[INGEST] coherence={coh:.4f}, strength={strength:.4f}, disp={disp:.4f}")
    return result


def query_agent(agent_id: str, task: str, top_k: int = 8) -> Dict[str, Any]:
    print(f"\n=== QUERY -> {agent_id} ===")
    payload = {
        "workspace_id": WORKSPACE_ID,
        "agent_id": agent_id,
        "query": task,
        "top_k": top_k,
    }
    result = request_json("POST", "/agent/query", payload)
    print(pretty(result))
    return result


def collective_status() -> Dict[str, Any]:
    print("\n=== COLLECTIVE STATUS ===")
    result = request_json("GET", f"/workspace/{WORKSPACE_ID}/collective/status")
    print(pretty(result))
    return result


def collective_events() -> Dict[str, Any]:
    print("\n=== COLLECTIVE EVENTS ===")
    result = request_json("GET", f"/workspace/{WORKSPACE_ID}/collective/events")
    print(pretty(result))
    return result


def reingest_event(agent_id: str, event_id: str, echo_strength: float = 0.25) -> Dict[str, Any]:
    print(f"\n=== REINGEST -> {agent_id} from {event_id} ===")
    payload = {
        "agent_id": agent_id,
        "event_id": event_id,
        "echo_strength_override": echo_strength,
    }
    result = request_json(
        "POST",
        f"/workspace/{WORKSPACE_ID}/collective/reingest",
        payload,
    )
    print(pretty(result))
    return result


def inspect_result_workspaces(agent_id: str, query_result: Dict[str, Any]) -> None:
    print(f"\n=== WORKSPACE ISOLATION CHECK -> {agent_id} ===")
    results = query_result.get("results", [])
    if not results:
        print("[INFO] No results returned.")
        return

    wrong = []
    for idx, item in enumerate(results, start=1):
        ws = item.get("workspace_id")
        eid = item.get("eid")
        row_type = item.get("type")
        summary = item.get("summary", "")
        print(f"{idx}. workspace_id={ws!r}, eid={eid}, type={row_type!r}, summary={summary[:90]!r}")

        # seed_canon rows may legitimately have no workspace_id attached
        if row_type == "seed_canon" and ws is None:
            continue

        if ws != WORKSPACE_ID:
            wrong.append(item)

    if wrong:
        print(
            f"\n[WARNING] Retrieval leakage detected for agent {agent_id}. "
            f"Expected only workspace_id={WORKSPACE_ID!r}, but {len(wrong)} result(s) came from another workspace."
        )
        for w in wrong:
            print(f"  leaked: ws={w.get('workspace_id')!r}, eid={w.get('eid')}, summary={w.get('summary','')[:60]!r}")
    else:
        print("[OK] All returned results belong to the requested workspace.")


def sentinel_isolation_test() -> None:
    print("\n=== SENTINEL ISOLATION TEST ===")
    ingest_memory(
        agent_id="atlas",
        text=SENTINEL_TEXT,
        domain_id="research",
        step=99,
    )
    result = query_agent("atlas", SENTINEL_QUERY, top_k=5)
    inspect_result_workspaces("atlas/sentinel", result)


def main() -> None:
    print("\n########################################")
    print("# TORMENT HIVEMIND TEST HARNESS (UPGRADED)")
    print("########################################")

    health_check()
    create_workspace()

    for agent in AGENTS:
        create_agent(agent)

    print("\n=== MULTI-ROUND INGEST ===")
    for step, round_items in enumerate(INGEST_ROUNDS, start=1):
        print(f"\n######## ROUND {step} ########")
        for item in round_items:
            ingest_memory(
                agent_id=item["agent_id"],
                text=item["text"],
                domain_id=item["domain_id"],
                step=step,
            )

        print(f"\n--- Collective status after round {step} ---")
        collective_status()

    print("\n=== TASK QUERIES ===")
    for agent in AGENTS:
        result = query_agent(agent["agent_id"], TASK, top_k=8)
        inspect_result_workspaces(agent["agent_id"], result)

    sentinel_isolation_test()

    status = collective_status()
    events_obj = collective_events()

    enabled = bool(status.get("enabled", False))
    events = events_obj.get("events", [])

    if not enabled:
        print(
            "\n[INFO] Hivemind is not enabled on the running server. "
            "Skipping reingest."
        )
        return

    if not events:
        print(
            "\n[INFO] No collective events were produced yet. "
            "That does not necessarily mean failure - it may mean the packet/event "
            "thresholds were not reached yet."
        )
        return

    first_event = events[0]
    event_id = first_event.get("event_id") or first_event.get("id")
    if not event_id:
        print(
            "\n[INFO] Event object exists but no usable event_id was found. "
            "Skipping reingest."
        )
        print(pretty(first_event))
        return

    # Reingest the first convergence event into each agent
    print("\n=== COLLECTIVE REINGEST ===")
    for agent in AGENTS:
        reingest_event(
            agent_id=agent["agent_id"],
            event_id=event_id,
            echo_strength=0.25,
        )

    # Final status
    print("\n=== FINAL STATUS ===")
    collective_status()
    print("\n[DONE] Test harness complete.")


if __name__ == "__main__":
    main()