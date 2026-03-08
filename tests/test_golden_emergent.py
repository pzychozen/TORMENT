import os
import json
import subprocess
from pathlib import Path

import pytest


GOLDEN_DIR = Path(__file__).parent / "golden"

# These are intentionally "range" assertions: they catch regressions without freezing behavior forever.
EXPECTED = {
    "mixed_a10_s60_seed0.jsonl": {"agents": 10, "steps": 60, "min_priv": 40, "max_priv": 90, "fb_exact": 20, "min_motif": 40},
    "ops_a10_s60_seed0.jsonl": {"agents": 10, "steps": 60, "min_priv": 40, "max_priv": 95, "fb_exact": 20, "min_motif": 40},
    "creative_a10_s60_seed0.jsonl": {"agents": 10, "steps": 60, "min_priv": 40, "max_priv": 95, "fb_exact": 20, "min_motif": 40},
}

@pytest.mark.parametrize("replay_name", list(EXPECTED.keys()))
def test_golden_emergent_replay(replay_name, tmp_path, monkeypatch):
    """
    Replays a previously recorded run and asserts key emergent metrics are within sane bounds.
    This protects against 'the system silently stopped learning' regressions.
    """
    data_dir = tmp_path / "data"
    out_dir = tmp_path / "out"
    data_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    replay_path = GOLDEN_DIR / replay_name
    assert replay_path.exists(), f"Missing golden replay file: {replay_path}"

    exp = EXPECTED[replay_name]

    cmd = [
        "python", "-m", "sim.run_sim",
        "--workspace", "ws",
        "--agents", str(exp["agents"]),
        "--seed", "0",
        "--out", str(out_dir), "--data-dir", str(data_dir),
        "--replay-from", str(replay_path),
        "--process-proposals-every", "20",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).parents[1]))
    assert r.returncode == 0, f"sim replay failed:\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    summary_path = out_dir / "summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["n_agents"] == exp["agents"]

    total_private = sum(a.get("private_memory_events", 0) for a in summary.get("agents", []))
    total_fb = sum(a.get("feedback_events", 0) for a in summary.get("agents", []))
    total_motif = sum(d.get("motif_events", 0) for d in summary.get("domains_stats", []))

    assert exp["min_priv"] <= total_private <= exp["max_priv"], f"private events out of range: {total_private}"
    assert total_fb == exp["fb_exact"], f"feedback events changed unexpectedly: {total_fb}"
    assert total_motif >= exp["min_motif"], f"motif activity too low: {total_motif}"
