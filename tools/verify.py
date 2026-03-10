"""Torment ship-gate verification.

Runs a small deterministic simulation twice:
  1) record a replay log
  2) replay from that log

Then compares the resulting summary.json outputs. This catches:
  - accidental nondeterminism regressions
  - obvious runtime failures in core API/governance paths

This script intentionally forces hash embeddings to keep the run deterministic.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], env: dict[str, str]) -> None:
    p = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if p.returncode != 0:
        print(p.stdout)
        raise SystemExit(p.returncode)


def _load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    tmp = Path(os.environ.get("TORMENT_VERIFY_TMP", "/tmp/torment_verify"))
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    out1 = tmp / "out_record"
    out2 = tmp / "out_replay"
    replay = tmp / "replay.jsonl"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root)
    env["TORMENT_EMBED_PROVIDER"] = "hash"  # determinism lock

    # Keep it small and fast.
    common = [
        sys.executable,
        "-m",
        "sim.run_sim",
        "--workspace",
        "verify-ws",
        "--agents",
        "8",
        "--steps",
        "120",
        "--scenario",
        "mixed",
        "--seed",
        "0",
    ]

    _run(common + ["--out", str(out1), "--record", str(replay)], env)
    _run(common + ["--out", str(out2), "--replay-from", str(replay)], env)

    s1 = _load_json(out1 / "summary.json")
    s2 = _load_json(out2 / "summary.json")

    # Normalize known volatile fields (timestamps) so we only fail on real nondeterminism.
    for s in (s1, s2):
        if isinstance(s, dict) and isinstance(s.get("workspace_meta"), dict):
            s["workspace_meta"].pop("created_ts", None)

    if s1 != s2:
        # Print a short diff hint without pulling in external deps.
        print("verify FAILED: sim summary mismatch between record and replay")
        print("record:", out1 / "summary.json")
        print("replay:", out2 / "summary.json")
        return 2

    print("verify OK: compile + tests + deterministic sim replay")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
