from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import os, json, glob
import pandas as pd

def _read_json(path: str, default: Any):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _count_jsonl(path: str) -> int:
    if not os.path.exists(path):
        return 0
    n = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def _motif_entropy(motifs_json_path: str, target_n: int = 24) -> Dict[str, float]:
    if not os.path.exists(motifs_json_path):
        return {"motif_count": 0, "entropy_score": 0.0}
    try:
        obj = _read_json(motifs_json_path, {})
        motifs = obj.get("motifs", {})
        strengths = []
        for mid, md in motifs.items():
            strengths.append(max(1e-6, float(md.get("strength", 0.1))))
        n = len(strengths)
        if n <= 1:
            return {"motif_count": n, "entropy_score": 0.0}
        import math
        S = sum(strengths) + 1e-12
        p = [s / S for s in strengths]
        sh = -sum(pi * math.log(pi + 1e-12) for pi in p) / (math.log(n + 1e-12))
        frag = min(1.0, n / float(max(1, target_n)))
        score = min(1.0, 0.55 * sh + 0.45 * frag)
        return {"motif_count": n, "entropy_score": float(score)}
    except Exception:
        return {"motif_count": 0, "entropy_score": 0.0}

def summarize_workspace(data_dir: str, workspace_id: str) -> Dict[str, Any]:
    ws_root = os.path.join(data_dir, "workspaces", workspace_id)
    # workspace embedding lock metadata (v1.10)
    ws_meta_path = os.path.join(ws_root, "workspace_meta.json")
    ws_meta = _read_json(ws_meta_path, {})

    domains_path = os.path.join(ws_root, "domains.json")
    domains = _read_json(domains_path, {}).get("domains", [])
    agents_root = os.path.join(ws_root, "agents")

    # agent stats
    agent_ids = []
    if os.path.isdir(agents_root):
        agent_ids = [d for d in os.listdir(agents_root) if os.path.isdir(os.path.join(agents_root, d))]
    agent_stats = []
    for aid in agent_ids:
        priv_root = os.path.join(agents_root, aid, "private")
        mem_jsonl = os.path.join(priv_root, "memory_events.jsonl")
        fb_jsonl = os.path.join(ws_root, "agents", aid, "feedback_events.jsonl")
        agent_stats.append({
            "agent_id": aid,
            "private_memory_events": _count_jsonl(mem_jsonl),
            "feedback_events": _count_jsonl(fb_jsonl),
        })

    # domain stats
    domain_stats = []
    for d in domains:
        shared_root = os.path.join(ws_root, "domains", d, "shared")
        shared_mem = os.path.join(shared_root, "memory_events.jsonl")
        proposals = os.path.join(ws_root, "domains", d, "proposals.jsonl")
        motif_events = os.path.join(ws_root, "domains", d, "motif_events.jsonl")
        motifs_json = os.path.join(ws_root, "domains", d, "motifs.json")
        ent = _motif_entropy(motifs_json, target_n=24)
        domain_stats.append({
            "domain": d,
            "shared_memory_events": _count_jsonl(shared_mem),
            "proposals_events": _count_jsonl(proposals),
            "motif_events": _count_jsonl(motif_events),
            "motif_count": ent.get("motif_count", 0),
            "motif_entropy_score": ent.get("entropy_score", 0.0),
        })

    # bridge stats
    bridges_path = os.path.join(ws_root, "bridges.json")
    bridges = _read_json(bridges_path, {}).get("bridges", [])
    bridge_events = os.path.join(ws_root, "bridge_events.jsonl")

    out = {
        "workspace_id": workspace_id,
        "workspace_meta": ws_meta,
        "n_agents": len(agent_ids),
        "domains": domains,
        "agents": agent_stats,
        "domains_stats": domain_stats,
        "n_bridges": len(bridges),
        "bridge_events": _count_jsonl(bridge_events),
    }
    return out

def write_reports(summary: Dict[str, Any], out_dir: str) -> Tuple[str,str,str]:
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    agents_df = pd.DataFrame(summary.get("agents", []))
    domains_df = pd.DataFrame(summary.get("domains_stats", []))
    agents_csv = os.path.join(out_dir, "agents.csv")
    domains_csv = os.path.join(out_dir, "domains.csv")
    agents_df.to_csv(agents_csv, index=False)
    domains_df.to_csv(domains_csv, index=False)
    return json_path, agents_csv, domains_csv
