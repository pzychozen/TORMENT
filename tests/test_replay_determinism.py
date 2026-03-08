import os, json, subprocess, sys
from pathlib import Path

def _run(cmd, env=None):
    p = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert p.returncode == 0, p.stdout
    return p.stdout

def test_sim_record_replay_determinism(tmp_path: Path):
    data_dir = tmp_path / "data"
    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    rec = tmp_path / "replay.jsonl"

    env = os.environ.copy()

    # record run
    _run([sys.executable, "-m", "sim.run_sim",
          "--workspace", "ws",
          "--agents", "6",
          "--steps", "40",
          "--scenario", "mixed",
          "--seed", "123",
          "--out", str(out1),
          "--data-dir", str(data_dir),
          "--record", str(rec),
          "--process-proposals-every", "10"], env)

    s1 = json.loads((out1 / "summary.json").read_text(encoding="utf-8"))

    # replay into a fresh data dir to ensure determinism is driven by the replay log
    data_dir2 = tmp_path / "data2"
    env2 = os.environ.copy()

    _run([sys.executable, "-m", "sim.run_sim",
          "--workspace", "ws",
          "--agents", "6",
          "--steps", "40",
          "--scenario", "mixed",
          "--seed", "999",   # ignored in replay mode; replay log drives behavior
          "--out", str(out2),
          "--data-dir", str(data_dir2),
          "--replay-from", str(rec),
          "--process-proposals-every", "10"], env2)

    s2 = json.loads((out2 / "summary.json").read_text(encoding="utf-8"))

    assert s1 == s2
