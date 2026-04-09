"""
Replay determinism tests — 3-tier structure.

Tier 1: Strict deterministic replay
    Private memory events, feedback events, bridge counts, and structural fields
    MUST be bit-exact between record and replay runs.

Tier 2: Collective replay tolerance
    Proposals, shared memory events, motif counts, and motif entropy are sensitive
    to wall-clock timing and adaptive coherence dynamics. These are checked with
    tolerances rather than strict equality.

Tier 3: Collective-disabled replay
    Proves that the core ingest/motif pipeline is deterministic when the proposal
    processing layer is removed from the equation.
"""
import os, json, subprocess, sys
from pathlib import Path


def _run(cmd, env=None):
    p = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert p.returncode == 0, p.stdout
    return p.stdout


def _record_and_replay(tmp_path, process_proposals_every: int):
    """Run record + replay and return both summaries."""
    data_dir = tmp_path / "data"
    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    rec = tmp_path / "replay.jsonl"
    env = os.environ.copy()

    _run([sys.executable, "-m", "sim.run_sim",
          "--workspace", "ws",
          "--agents", "6",
          "--steps", "40",
          "--scenario", "mixed",
          "--seed", "123",
          "--out", str(out1),
          "--data-dir", str(data_dir),
          "--record", str(rec),
          "--process-proposals-every", str(process_proposals_every)], env)

    s1 = json.loads((out1 / "summary.json").read_text(encoding="utf-8"))

    data_dir2 = tmp_path / "data2"
    env2 = os.environ.copy()

    _run([sys.executable, "-m", "sim.run_sim",
          "--workspace", "ws",
          "--agents", "6",
          "--steps", "40",
          "--scenario", "mixed",
          "--seed", "999",
          "--out", str(out2),
          "--data-dir", str(data_dir2),
          "--replay-from", str(rec),
          "--process-proposals-every", str(process_proposals_every)], env2)

    s2 = json.loads((out2 / "summary.json").read_text(encoding="utf-8"))
    return s1, s2


# ── Tier 1: Strict deterministic replay (core pipeline) ──

def test_strict_replay_determinism(tmp_path: Path):
    """
    The private agent pipeline (ingest → coherence → write-gate → motif)
    must produce identical results between record and replay.
    """
    s1, s2 = _record_and_replay(tmp_path, process_proposals_every=10)

    # Structure
    assert s1["n_agents"] == s2["n_agents"]
    assert s1["domains"] == s2["domains"]
    assert s1["n_bridges"] == s2["n_bridges"]
    assert s1["bridge_events"] == s2["bridge_events"]

    # Per-agent private counts must be identical
    a1 = sorted(s1["agents"], key=lambda a: a["agent_id"])
    a2 = sorted(s2["agents"], key=lambda a: a["agent_id"])
    assert len(a1) == len(a2)
    for ag1, ag2 in zip(a1, a2):
        assert ag1["agent_id"] == ag2["agent_id"]
        assert ag1["private_memory_events"] == ag2["private_memory_events"], (
            f"Agent {ag1['agent_id']}: private events {ag1['private_memory_events']} vs {ag2['private_memory_events']}"
        )
        assert ag1["feedback_events"] == ag2["feedback_events"], (
            f"Agent {ag1['agent_id']}: feedback events {ag1['feedback_events']} vs {ag2['feedback_events']}"
        )


# ── Tier 2: Collective replay tolerance ──

def test_collective_replay_tolerance(tmp_path: Path):
    """
    The collective pipeline (proposals → shared memories → motif enrichment)
    involves timing-sensitive dynamics. Check with tolerances.
    """
    s1, s2 = _record_and_replay(tmp_path, process_proposals_every=10)

    d1 = {d["domain"]: d for d in s1["domains_stats"]}
    d2 = {d["domain"]: d for d in s2["domains_stats"]}

    for domain in d1:
        ds1 = d1[domain]
        ds2 = d2[domain]

        # Motif count should be identical (motif discovery is deterministic)
        assert ds1["motif_count"] == ds2["motif_count"], (
            f"Domain {domain}: motif_count {ds1['motif_count']} vs {ds2['motif_count']}"
        )

        # Motif entropy: allow ±0.05 tolerance
        e1 = ds1["motif_entropy_score"]
        e2 = ds2["motif_entropy_score"]
        assert abs(e1 - e2) < 0.05, (
            f"Domain {domain}: entropy {e1:.4f} vs {e2:.4f} (diff={abs(e1-e2):.4f}, tolerance=0.05)"
        )

        # Motif events: allow ±10% or ±5 absolute, whichever is larger
        m1 = ds1["motif_events"]
        m2 = ds2["motif_events"]
        tol = max(5, int(0.1 * max(m1, m2, 1)))
        assert abs(m1 - m2) <= tol, (
            f"Domain {domain}: motif_events {m1} vs {m2} (diff={abs(m1-m2)}, tolerance={tol})"
        )

        # Shared memory events: allow ±3
        sh1 = ds1["shared_memory_events"]
        sh2 = ds2["shared_memory_events"]
        assert abs(sh1 - sh2) <= 3, (
            f"Domain {domain}: shared_memory_events {sh1} vs {sh2}"
        )

        # Proposals: allow ±5
        p1 = ds1["proposals_events"]
        p2 = ds2["proposals_events"]
        assert abs(p1 - p2) <= 5, (
            f"Domain {domain}: proposals_events {p1} vs {p2}"
        )


# ── Tier 3: Collective-disabled replay (pure core determinism) ──

def test_collective_disabled_replay_determinism(tmp_path: Path):
    """
    With proposal processing disabled, the core pipeline summary should be
    identical between record and replay.

    Proposal *drafting* (via CollectiveProposalBridge during convergence) is
    still timing-sensitive even when processing is off, so we strip
    proposals_events and timestamps before comparison.
    """
    s1, s2 = _record_and_replay(tmp_path, process_proposals_every=0)

    # Strip wall-clock timestamps and timing-sensitive proposal drafting counts
    for s in (s1, s2):
        meta = s.get("workspace_meta", {})
        meta.pop("created_ts", None)
        meta.pop("updated_ts", None)
        for ds in s.get("domains_stats", []):
            ds.pop("proposals_events", None)

    assert s1 == s2
