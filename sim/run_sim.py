from __future__ import annotations
import argparse, os, json, time, random
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Iterable
from fastapi.testclient import TestClient

from sim.scenarios import SCENARIOS, DEFAULT_DOMAINS
from sim.metrics import summarize_workspace, write_reports

@dataclass
class RecordedStep:
    step: int
    agent_id: str
    text: str
    domain_hint: Optional[str]
    did_query: bool
    query: Optional[str]
    used_successfully: bool
    user_confirmed: bool
    contradiction_detected: bool
    process_proposals: bool

def make_agent(client: TestClient, workspace_id: str, agent_id: str, coupling_mode: str, coupling_strength: float, domain_pref: Dict[str,float]) -> Dict[str, Any]:
    seed = {
        "agent_id": agent_id,
        "workspace_id": workspace_id,
        "core_traits": ["synthetic"],
        "priority_weights": {"facts": 0.8, "projects": 0.7, "preferences": 0.4, "motifs": 0.7},
        "decay_bias": 0.8,
        "promotion_bias": 0.6,
        "coupling_mode": coupling_mode,
        "coupling_strength": coupling_strength,
        "domain_preferences": domain_pref,
    }
    r = client.post("/agent/create", json={"workspace_id": workspace_id, "agent_id": agent_id, "seed": seed})
    r.raise_for_status()
    return r.json()

def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows

def main():
    p = argparse.ArgumentParser(description="Torment Fabric Simulation Harness (deterministic record/replay)")
    p.add_argument("--workspace", default="sim-ws", help="workspace_id")
    p.add_argument("--data-dir", default=None, help="Data directory for TormentFabric (default: <out>/data)")
    p.add_argument("--agents", type=int, default=25, help="number of agents")
    p.add_argument("--steps", type=int, default=200, help="number of events to generate")
    p.add_argument("--scenario", choices=list(SCENARIOS.keys()), default="mixed")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--adversarial-frac", type=float, default=0.0,
            help="Fraction of agents acting adversarial (0.0-1.0)")
    p.add_argument("--out", default="sim_out", help="output dir (relative or absolute)")
    p.add_argument("--process-proposals-every", type=int, default=20, help="process proposals every N steps per domain")
    p.add_argument("--record", default=None, help="write full deterministic replay log to this jsonl file")
    p.add_argument("--replay-from", dest="replay_from", default=None, help="replay from a previously recorded jsonl log")
    args = p.parse_args()

    # Resolve and lock the data directory BEFORE importing the FastAPI app,
    # because torment_service.app binds DATA_DIR at import time.
    data_dir = args.data_dir or os.path.join(args.out, "data")
    os.makedirs(data_dir, exist_ok=True)
    os.environ["TORMENT_DATA_DIR"] = data_dir

    from torment_service.app import app  # noqa: E402
    client = TestClient(app)

    # create workspace
    r = client.post("/workspace/create", json={"workspace_id": args.workspace})
    r.raise_for_status()

    # build agents deterministically
    rng = random.Random(args.seed)
    agent_ids = []
    agent_modes: Dict[str,str] = {}
    for i in range(args.agents):
        aid = f"agent-{i:03d}"
        agent_ids.append(aid)
        mode = rng.choices(["read_only","propose","sync"], weights=[0.55,0.30,0.15] if args.scenario=="collaborative_mixed_200" else [0.65,0.25,0.10])[0]
        strength = 0.15 if mode=="read_only" else (0.35 if mode=="propose" else 0.55)
        prefs = {d: rng.random() for d in DEFAULT_DOMAINS}
        s = sum(prefs.values())
        prefs = {k: v/s for k,v in prefs.items()}
        make_agent(client, args.workspace, aid, mode, strength, prefs)
        agent_modes[aid] = mode

    # Select adversarial agents deterministically
    n_adv = int(args.agents * args.adversarial_frac)
    adversarial_agents = set(agent_ids[:n_adv])  # first N agents for determinism

    # Prepare replay steps
    recorded_steps: List[Dict[str, Any]] = []
    if args.replay_from:
        recorded_steps = _read_jsonl(args.replay_from)
        steps_iter = recorded_steps
        if args.steps and args.steps != len(recorded_steps):
            # if user specified steps, we respect recorded length
            args.steps = len(recorded_steps)
    else:
        scenario = SCENARIOS[args.scenario](seed=args.seed)
        events = list(scenario.stream(args.steps))

        steps_iter = []
        for step, ev in enumerate(events):
            aid = rng.choice(agent_ids)
            did_query = (step % (2 if args.scenario=="collaborative_mixed_200" else 3) == 0)
            q = f"recall: {ev.text.split(']')[-1].strip()[:80]}" if did_query else None
            # Deterministic feedback outcomes based on rng
            # (Note: retrieved ids are computed during runtime; we record the booleans only)
            # If nothing retrieved, used_successfully may be false.
            user_confirmed = rng.random() < (0.6 if did_query else 0.2)
            used_successfully = rng.random() < 0.7
            contradiction_detected = rng.random() < 0.05
            process_proposals = (args.process_proposals_every > 0 and step % args.process_proposals_every == 0 and step > 0)
            # For collaborative scenario, explicitly propose some memories into shared governance
            did_propose = (args.scenario=="collaborative_mixed_200" and rng.random() < 0.35)

            steps_iter.append({
                "step": step,
                "agent_id": aid,
                "text": ev.text,
                "domain_hint": ev.domain_hint,
                "did_query": did_query,
                "query": q,
                "used_successfully": used_successfully,
                "user_confirmed": user_confirmed,
                "contradiction_detected": contradiction_detected,
                "process_proposals": process_proposals,
                "did_propose": did_propose if args.scenario=="collaborative_mixed_200" else False,
            })

        if args.record:
            _write_jsonl(args.record, steps_iter)

    # Run
    for row in steps_iter:
        step = int(row["step"])
        aid = str(row["agent_id"])
        text = str(row["text"])
        domain_hint = row.get("domain_hint", None)

        rr = client.post("/agent/ingest", json={
            "workspace_id": args.workspace,
            "agent_id": aid,
            "text": text,
            "domain_hint": domain_hint,
            "step": step,
        })
        rr.raise_for_status()

        if bool(row.get("did_propose", False)) and agent_modes.get(aid,"read_only") != "read_only":

            summary_text = text[:220]

            # Adversarial agents flip polarity on some proposals
            if aid in adversarial_agents and rng.random() < 0.5:
                summary_text = "NOT TRUE: " + summary_text

            pr = client.post("/agent/propose_share", json={
                "workspace_id": args.workspace,
                "agent_id": aid,
                "summary": summary_text,
                "domain_id": (domain_hint or "research"),
                "mtype": "episode",
                "confidence": 0.7,
                "strength": 0.75,
            })
            pr.raise_for_status()

        if bool(row.get("did_query", False)):
            q = str(row.get("query") or "recall")
            qr = client.post("/agent/query", json={
                "workspace_id": args.workspace,
                "agent_id": aid,
                "query": q,
                "top_k": 6,
                "peek_bridges": True,
                "explain": False
            })
            qr.raise_for_status()
            qout = qr.json()
            ids = [int(x.get("eid")) for x in qout.get("results", []) if x.get("eid") is not None]
            used = bool(ids)
            fb = {
                "workspace_id": args.workspace,
                "agent_id": aid,
                "retrieved_ids": ids,
                "used_successfully": used and bool(row.get("used_successfully", False)),
                "user_confirmed": used and bool(row.get("user_confirmed", False)),
                "contradiction_detected": used and bool(row.get("contradiction_detected", False)),
                "shared_memory_used": any(x.get("scope") == "shared" for x in qout.get("results", [])),
                "bridges_used": [{k: str(v) for k, v in b.items()} for b in (qout.get("bridges") or [])],
            }
            fr = client.post("/agent/feedback", json=fb)
            fr.raise_for_status()

        if bool(row.get("process_proposals", False)):
            # process proposals for all domains
            for domain_id in DEFAULT_DOMAINS:
                pr = client.post("/workspace/process_proposals", json={"workspace_id": args.workspace, "domain_id": domain_id})
                pr.raise_for_status()

    outdir = args.out
    os.makedirs(outdir, exist_ok=True)
    summary = summarize_workspace(data_dir, args.workspace)
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    write_reports(summary, outdir)

    print("Done.")
    print(f"Wrote: {os.path.join(outdir, 'summary.json')}")

if __name__ == "__main__":
    main()