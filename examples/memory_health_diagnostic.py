#!/usr/bin/env python
"""
Memory Health Diagnostic — Phase 2.1

Runs 200+ ingests across 3 agents, then analyzes:
  - Private memory growth rate per agent
  - Shared (collective) memory growth per convergence
  - Duplication between private stores and between private/shared
  - Echo chain lengths and redundancy
  - Compression event count and deep store population
  - Write gate hit/miss ratio
  - Motif accumulation and entropy drift

Usage:
    python examples/memory_health_diagnostic.py [--steps 250] [--agents 3]

Outputs a JSON report to stdout and optionally to a file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
# NOTE: torment_service.app import is deferred to run_diagnostic() so that
# env vars (COMPRESS_ENABLE, etc.) are set before the TormentFabric instance
# is created at module level in app.py.
DEFAULT_DOMAINS = None  # loaded lazily

# ---------------------------------------------------------------------------
# Test data generator — varied domain content with repeats for duplication test
# ---------------------------------------------------------------------------

RESEARCH_TOPICS = [
    "phase-lock synchronization in coupled oscillators",
    "coherence decay under high-entropy embedding regimes",
    "folded embedding extraction and TriOcta weight stability",
    "adaptive dispersion scaling convergence properties",
    "memory graph cosine similarity search accuracy",
    "embedding shard compaction and read performance",
    "convergence detection via rolling similarity windows",
    "cross-agent coherence alignment in hivemind mode",
]

OPS_TASKS = [
    "rotate agent credentials and update identity store",
    "backup workspace JSONL files to cold storage",
    "audit feedback event log for anomalous overlay drift",
    "verify compression triggers fire at corridor exit",
    "check motif registry for orphaned centroids",
    "validate embedding checksums against stored vectors",
    "monitor memory growth rate across overnight run",
    "test graceful degradation when embedder is unavailable",
]

CREATIVE_IDEAS = [
    "what if memories could dream — replay old corridors at low amplitude",
    "a character whose identity is defined entirely by contradictions",
    "memory as music — each coherence value is a note in a sequence",
    "the archivist who refuses to forget anything, even noise",
    "collective consciousness emerging from three distinct viewpoints",
    "a dialogue between the skeptic and the interpreter about trust",
    "imagining memory decay as autumn leaves falling from a tree",
    "what happens when two echoes of the same event reinforce each other",
]


def generate_text(step: int, domain_hint: str) -> str:
    """Generate varied but deterministic test content."""
    idx = step % 8
    if domain_hint == "research":
        return f"[Research log #{step}] Investigating {RESEARCH_TOPICS[idx]}. Found interesting pattern in latest data — coherence shifted unexpectedly. Recording observations for further analysis."
    elif domain_hint == "operations":
        return f"[Ops #{step}] Task: {OPS_TASKS[idx]}. Started at checkpoint, verifying all subsystems. Outcome pending review by operator."
    elif domain_hint == "creative":
        return f"[Creative #{step}] Idea: {CREATIVE_IDEAS[idx]}. This sparked a chain of associations about memory persistence and identity formation."
    else:
        # Mixed — rotate
        pools = [RESEARCH_TOPICS, OPS_TASKS, CREATIVE_IDEAS]
        pool = pools[step % 3]
        return f"[Mixed #{step}] Exploring: {pool[idx]}. Cross-domain insight connecting multiple threads."


# Intentional duplicate generator for duplication testing
def generate_duplicate_text(original_step: int) -> str:
    """Generate near-exact duplicate of a previous step's content."""
    return generate_text(original_step, "research")


# ---------------------------------------------------------------------------
# Diagnostic data collectors
# ---------------------------------------------------------------------------

@dataclass
class AgentStats:
    agent_id: str
    ingests_attempted: int = 0
    ingests_stored: int = 0
    ingests_skipped: int = 0
    feedback_events: int = 0
    write_gate_hits: List[float] = field(default_factory=list)   # strengths that passed
    write_gate_misses: List[float] = field(default_factory=list)  # strengths that failed
    domain_distribution: Dict[str, int] = field(default_factory=lambda: Counter())
    motifs_attached: int = 0
    motifs_created: int = 0
    echo_count: int = 0
    memory_eids: List[int] = field(default_factory=list)
    summary_hashes: List[str] = field(default_factory=list)


@dataclass
class DiagnosticReport:
    config: Dict[str, Any] = field(default_factory=dict)
    agent_stats: Dict[str, Any] = field(default_factory=dict)
    growth_curve: List[Dict[str, Any]] = field(default_factory=list)
    duplication: Dict[str, Any] = field(default_factory=dict)
    compression: Dict[str, Any] = field(default_factory=dict)
    shared_memory: Dict[str, Any] = field(default_factory=dict)
    motif_health: Dict[str, Any] = field(default_factory=dict)
    write_gate: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


def _hash_summary(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Main diagnostic
# ---------------------------------------------------------------------------

def run_diagnostic(n_steps: int = 250, n_agents: int = 3, data_dir: Optional[str] = None) -> DiagnosticReport:
    report = DiagnosticReport()

    # Setup — env vars MUST be set before importing app (fabric reads them in __init__)
    tmp = tempfile.mkdtemp(prefix="torment_health_") if data_dir is None else data_dir
    os.environ["TORMENT_DATA_DIR"] = tmp
    os.environ["TORMENT_COMPRESS_ENABLE"] = "1"
    os.environ["TORMENT_COMPRESS_MIN_STEP"] = "30"  # Lower for testing
    os.environ["TORMENT_COMPRESS_STEP_INTERVAL"] = "100"  # Fire periodic sooner for diagnostic

    from torment_service.app import app  # deferred import — after env vars are set
    from torment_service.router import DEFAULT_DOMAINS

    client = TestClient(app)
    workspace_id = "health_diag"

    report.config = {
        "n_steps": n_steps,
        "n_agents": n_agents,
        "data_dir": tmp,
        "workspace_id": workspace_id,
        "compress_enabled": True,
        "compress_min_step": 30,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    # Create workspace
    ws_resp = client.post("/workspace/create", json={
        "workspace_id": workspace_id,
        "domains": DEFAULT_DOMAINS,
    })
    assert ws_resp.status_code == 200, f"Workspace creation failed: {ws_resp.text}"

    # Create agents
    agent_ids = [f"diag-agent-{i:03d}" for i in range(n_agents)]
    agents: Dict[str, AgentStats] = {}
    domain_cycle = ["research", "operations", "creative"]

    for i, aid in enumerate(agent_ids):
        seed = {
            "agent_id": aid,
            "workspace_id": workspace_id,
            "core_traits": ["analytical", "curious"],
            "priority_weights": {"accuracy": 0.7, "novelty": 0.5, "efficiency": 0.6},
            "decay_bias": 0.3,
            "promotion_bias": 0.6,
            "coupling_mode": "propose",
            "coupling_strength": 0.5,
            "domain_preferences": {d: (0.8 if d == domain_cycle[i % 3] else 0.3) for d in DEFAULT_DOMAINS},
        }
        r = client.post("/agent/create", json={"workspace_id": workspace_id, "agent_id": aid, "seed": seed})
        assert r.status_code == 200, f"Agent {aid} registration failed: {r.text}"
        agents[aid] = AgentStats(agent_id=aid)

    # ---------------------------------------------------------------------------
    # Main loop: ingest + feedback + periodic proposal processing
    # ---------------------------------------------------------------------------
    growth_snapshots = []
    total_stored = 0
    reinforced_count = 0
    duplicate_steps = set()

    # Mark some steps as intentional duplicates
    import random
    rng = random.Random(42)
    for _ in range(n_steps // 10):  # ~10% duplicates
        dup_of = rng.randint(0, max(1, n_steps // 2))
        duplicate_steps.add(dup_of + n_steps // 2)  # duplicate appears in second half

    for step in range(n_steps):
        agent_idx = step % n_agents
        aid = agent_ids[agent_idx]
        ast = agents[aid]
        domain = domain_cycle[step % 3]

        # Generate text — sometimes duplicate
        if step in duplicate_steps:
            orig = step - n_steps // 2
            text = generate_duplicate_text(orig)
        else:
            text = generate_text(step, domain)

        ast.ingests_attempted += 1

        # Ingest
        resp = client.post("/agent/ingest", json={
            "workspace_id": workspace_id,
            "agent_id": aid,
            "text": text,
            "step": step,
            "domain_id": domain,
        })
        assert resp.status_code == 200, f"Ingest failed at step {step}: {resp.text}"
        data = resp.json()

        if data.get("stored"):
            ast.ingests_stored += 1
            total_stored += 1
            if data.get("reinforced"):
                reinforced_count += 1
            eid = data.get("eid")
            if eid:
                ast.memory_eids.append(eid)
            summary = data.get("signals", {}).get("summary", text[:80])
            ast.summary_hashes.append(_hash_summary(summary))
            ast.write_gate_hits.append(data.get("signals", {}).get("strength", 0.0))
        else:
            ast.ingests_skipped += 1
            ast.write_gate_misses.append(data.get("signals", {}).get("strength", 0.0))

        domain_chosen = data.get("domain_chosen", domain)
        ast.domain_distribution[domain_chosen] += 1

        motifs = data.get("motifs", [])
        ast.motifs_attached += len(motifs)
        if data.get("created_motif"):
            ast.motifs_created += 1

        # Feedback every 3rd step
        if step % 3 == 0:
            retrieved = ast.memory_eids[-3:] if len(ast.memory_eids) >= 3 else ast.memory_eids
            fb = {
                "workspace_id": workspace_id,
                "agent_id": aid,
                "retrieved_ids": retrieved,
                "used_successfully": rng.random() < 0.7,
                "user_confirmed": rng.random() < 0.5,
                "contradiction_detected": rng.random() < 0.05,
            }
            fr = client.post("/agent/feedback", json=fb)
            if fr.status_code == 200:
                ast.feedback_events += 1

        # Process proposals every 20 steps
        if step > 0 and step % 20 == 0:
            for d in DEFAULT_DOMAINS:
                client.post("/workspace/process_proposals", json={
                    "workspace_id": workspace_id,
                    "domain_id": d,
                    "step": step,
                })

        # Growth snapshot every 25 steps
        if step % 25 == 0 or step == n_steps - 1:
            snapshot = {
                "step": step,
                "total_stored": total_stored,
                "per_agent": {aid: a.ingests_stored for aid, a in agents.items()},
            }
            growth_snapshots.append(snapshot)

    report.growth_curve = growth_snapshots

    # ---------------------------------------------------------------------------
    # Post-run analysis
    # ---------------------------------------------------------------------------

    # 1. Per-agent stats
    for aid, ast in agents.items():
        hit_strengths = ast.write_gate_hits
        miss_strengths = ast.write_gate_misses
        report.agent_stats[aid] = {
            "ingests_attempted": ast.ingests_attempted,
            "ingests_stored": ast.ingests_stored,
            "ingests_skipped": ast.ingests_skipped,
            "store_rate": round(ast.ingests_stored / max(1, ast.ingests_attempted), 3),
            "feedback_events": ast.feedback_events,
            "domain_distribution": dict(ast.domain_distribution),
            "motifs_attached": ast.motifs_attached,
            "motifs_created": ast.motifs_created,
            "avg_stored_strength": round(sum(hit_strengths) / max(1, len(hit_strengths)), 4) if hit_strengths else 0.0,
            "avg_skipped_strength": round(sum(miss_strengths) / max(1, len(miss_strengths)), 4) if miss_strengths else 0.0,
            "memory_count": len(ast.memory_eids),
        }

    # 2. Write gate analysis
    all_hits = []
    all_misses = []
    for ast in agents.values():
        all_hits.extend(ast.write_gate_hits)
        all_misses.extend(ast.write_gate_misses)

    report.write_gate = {
        "total_attempts": len(all_hits) + len(all_misses),
        "total_stored": len(all_hits),
        "total_skipped": len(all_misses),
        "store_rate": round(len(all_hits) / max(1, len(all_hits) + len(all_misses)), 3),
        "avg_stored_strength": round(sum(all_hits) / max(1, len(all_hits)), 4) if all_hits else 0.0,
        "avg_skipped_strength": round(sum(all_misses) / max(1, len(all_misses)), 4) if all_misses else 0.0,
        "min_stored_strength": round(min(all_hits), 4) if all_hits else 0.0,
        "max_skipped_strength": round(max(all_misses), 4) if all_misses else 0.0,
    }

    # 3. Duplication analysis
    all_hashes: Dict[str, List[str]] = defaultdict(list)  # hash -> [agent_ids]
    for aid, ast in agents.items():
        for h in ast.summary_hashes:
            all_hashes[h].append(aid)

    intra_dupes = 0  # Same hash within one agent
    inter_dupes = 0  # Same hash across agents
    for h, owners in all_hashes.items():
        if len(owners) > 1:
            agent_set = set(owners)
            if len(agent_set) == 1:
                intra_dupes += len(owners) - 1
            else:
                inter_dupes += len(owners) - 1

    report.duplication = {
        "unique_summaries": len(all_hashes),
        "total_stored": sum(len(v) for v in all_hashes.values()),
        "intra_agent_duplicates": intra_dupes,
        "inter_agent_duplicates": inter_dupes,
        "duplication_rate": round((intra_dupes + inter_dupes) / max(1, sum(len(v) for v in all_hashes.values())), 4),
        "reinforced_instead_of_created": reinforced_count,
    }

    # 4. File-system analysis — read JSONL files for deeper stats
    ws_root = os.path.join(tmp, "workspaces", workspace_id)

    # Private memory file sizes
    private_records: Dict[str, int] = {}
    echo_records: Dict[str, int] = {}
    for aid in agent_ids:
        nodes_path = os.path.join(ws_root, "agents", aid, "private", "nodes.jsonl")
        count = 0
        echoes = 0
        if os.path.exists(nodes_path):
            with open(nodes_path, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    count += 1
                    try:
                        rec = json.loads(line)
                        if rec.get("payload", {}).get("provenance") == "collective":
                            echoes += 1
                    except json.JSONDecodeError:
                        pass
        private_records[aid] = count
        echo_records[aid] = echoes

    # Shared memory counts per domain
    shared_counts: Dict[str, int] = {}
    for d in DEFAULT_DOMAINS:
        shared_path = os.path.join(ws_root, "domains", d, "shared", "memory_events.jsonl")
        shared_counts[d] = 0
        if os.path.exists(shared_path):
            with open(shared_path, "r") as f:
                for line in f:
                    if line.strip():
                        shared_counts[d] += 1

    report.shared_memory = {
        "per_domain": shared_counts,
        "total": sum(shared_counts.values()),
    }

    # Echo analysis
    total_echoes = sum(echo_records.values())
    report.duplication["echo_records_per_agent"] = echo_records
    report.duplication["total_echoes"] = total_echoes

    # 5. Compression analysis
    compression_events: Dict[str, List[Dict]] = {}
    for aid in agent_ids:
        events_path = os.path.join(ws_root, "agents", aid, "private", "memory_events.jsonl")
        comp_evts = []
        if os.path.exists(events_path):
            with open(events_path, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        evt = json.loads(line)
                        if evt.get("type") in ("COMPRESSION", "COMPRESS_EVENT", "MEMORY_COMPRESS"):
                            comp_evts.append(evt)
                    except json.JSONDecodeError:
                        pass
        compression_events[aid] = comp_evts

    report.compression = {
        "per_agent": {aid: len(evts) for aid, evts in compression_events.items()},
        "total_events": sum(len(v) for v in compression_events.values()),
        "detail": {aid: evts[:3] for aid, evts in compression_events.items() if evts},  # sample
    }

    # 6. Motif health
    motif_stats: Dict[str, Any] = {}
    for d in DEFAULT_DOMAINS:
        motifs_path = os.path.join(ws_root, "domains", d, "motifs.json")
        if os.path.exists(motifs_path):
            try:
                with open(motifs_path, "r") as f:
                    mdata = json.load(f)
                motifs = mdata.get("motifs", {})
                strengths = [float(m.get("strength", 0)) for m in motifs.values()]
                motif_stats[d] = {
                    "count": len(motifs),
                    "avg_strength": round(sum(strengths) / max(1, len(strengths)), 4) if strengths else 0.0,
                    "max_strength": round(max(strengths), 4) if strengths else 0.0,
                    "min_strength": round(min(strengths), 4) if strengths else 0.0,
                }
            except Exception:
                motif_stats[d] = {"count": 0, "error": "parse_failed"}
        else:
            motif_stats[d] = {"count": 0}

    report.motif_health = motif_stats

    # ---------------------------------------------------------------------------
    # Warnings and recommendations
    # ---------------------------------------------------------------------------

    # Growth rate check
    if n_steps > 0:
        rate = total_stored / n_steps
        if rate > 0.9:
            report.warnings.append(f"High store rate ({rate:.2f}) — write gate may be too permissive")
        elif rate < 0.2:
            report.warnings.append(f"Low store rate ({rate:.2f}) — write gate may be too restrictive")

    # Duplication check
    dup_rate = report.duplication["duplication_rate"]
    if dup_rate > 0.15:
        report.warnings.append(f"High duplication rate ({dup_rate:.2%}) — dedup or similarity check needed")
        report.recommendations.append("Consider adding pre-ingest similarity check against recent memories")

    # Compression check
    comp_total = report.compression["total_events"]
    if comp_total == 0 and n_steps >= 100:
        report.warnings.append("No compression events fired — verify TORMENT_COMPRESS_ENABLE=1 and corridor transitions")
        report.recommendations.append("Check tri_mod corridor transitions — compression needs corridor_exit triggers")

    # Motif fragmentation
    for d, ms in motif_stats.items():
        if isinstance(ms, dict) and ms.get("count", 0) > 30:
            report.warnings.append(f"Domain '{d}' has {ms['count']} motifs — may need merge/prune")
            report.recommendations.append(f"Run motif entropy check for domain '{d}' and consider auto-merge")

    # Echo accumulation
    if total_echoes > total_stored * 0.3:
        report.warnings.append(f"Echoes are {total_echoes}/{total_stored} ({total_echoes/max(1,total_stored):.0%}) of stored memories — may be redundant")
        report.recommendations.append("Review echo strength cap and reingest policy gating")

    # Private record file sizes vs in-memory count
    for aid in agent_ids:
        file_count = private_records.get(aid, 0)
        mem_count = agents[aid].ingests_stored
        if file_count > mem_count * 1.5:
            report.warnings.append(
                f"Agent {aid}: {file_count} JSONL records but only {mem_count} ingests stored — "
                f"possible duplicate writes or update-after-write pattern"
            )

    if not report.warnings:
        report.recommendations.append("Memory health looks good — no immediate action needed")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="TORMENT Memory Health Diagnostic")
    parser.add_argument("--steps", type=int, default=250, help="Number of ingest steps")
    parser.add_argument("--agents", type=int, default=3, help="Number of agents")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file path")
    args = parser.parse_args()

    print(f"Running memory health diagnostic: {args.steps} steps, {args.agents} agents...", file=sys.stderr)
    t0 = time.time()

    report = run_diagnostic(n_steps=args.steps, n_agents=args.agents)

    elapsed = time.time() - t0
    report.config["elapsed_seconds"] = round(elapsed, 2)

    out = json.dumps(asdict(report), indent=2, default=str)

    if args.output:
        with open(args.output, "w") as f:
            f.write(out)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(out)

    print(f"Done in {elapsed:.1f}s", file=sys.stderr)

    # Print summary to stderr
    print("\n=== Quick Summary ===", file=sys.stderr)
    print(f"  Steps: {args.steps}, Agents: {args.agents}", file=sys.stderr)
    print(f"  Store rate: {report.write_gate.get('store_rate', 'N/A')}", file=sys.stderr)
    print(f"  Duplication rate: {report.duplication.get('duplication_rate', 'N/A')}", file=sys.stderr)
    print(f"  Compression events: {report.compression.get('total_events', 0)}", file=sys.stderr)
    print(f"  Shared memories: {report.shared_memory.get('total', 0)}", file=sys.stderr)
    if report.warnings:
        print(f"  Warnings: {len(report.warnings)}", file=sys.stderr)
        for w in report.warnings:
            print(f"    - {w}", file=sys.stderr)
    else:
        print("  No warnings", file=sys.stderr)


if __name__ == "__main__":
    main()
