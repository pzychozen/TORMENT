from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


LABEL = "ordinary_relational_long_path_maturity_fixed_continuation_v1"
EXPERIMENT = "ORDINARY_RELATIONAL_LONG_PATH_MATURITY_FIXED_CONTINUATION_V1"
TRAJECTORY_LABEL = "PREREGISTERED_EXPERIMENT_4_T1_FIRST_550"
TRAJECTORY_SCOPE = "PREREGISTERED_DISTINCT_EPISODE_RELATIONAL_MATURITY_TRAJECTORY"
EXPECTED_HEAD = "b9fd518e53b79a69e1535ae5874bf085af55bdcd"
EXPECTED_SUBJECT = "test(lived-use): preserve relational maturity characterization"
PREVIOUS_TRAJECTORY_PATH = (
    REPO_ROOT
    / "outputs"
    / "experiments"
    / "natural_long_memory_reachability_v1"
    / "20260811T123033Z"
    / "preregistered_trajectories.json"
)
PREVIOUS_TRAJECTORY_ID = "T1_DISTINCT_EPISODES"
PREVIOUS_4B_RESULT_PATH = (
    REPO_ROOT
    / "outputs"
    / "experiments"
    / "ordinary_relational_long_path_maturity_v1"
    / "20260811T150017Z"
    / "ordinary_relational_long_path_maturity_v1_result.json"
)
EXPECTED_SOURCE_FIRST_900_SHA = "accaaeae223f5df546b2d114afad08b7b3ba6a704d0dbd120b6c112d28ac41fd"
MAX_EXCHANGES = 550
SOURCE_HASH_EXCHANGES = 900
REPLAY_COMPARE_THROUGH_STEP = 506
VERIFY_FIRST_N = 105
PROGRESS_EVERY = 50
PATH_LIMIT = 180

WORKSPACE_ID = "w4b"
AGENT_ID = "a4b"
DOMAIN_ID = "personal"
USER_NAME = "Hilmir"
CHARACTER_NAME = "Eira Voss"
SEED_ID = "ev4b"

EXPECTED_EMBEDDER = {
    "provider": "st",
    "model": "BAAI/bge-small-en-v1.5",
    "dim": 384,
}

THRESHOLD_ENV_VARS = (
    "TORMENT_COMPRESS_MIN_STEP",
    "TORMENT_COMPRESS_MIN_AGE",
    "TORMENT_COMPRESS_MAX_CANDIDATES",
    "TORMENT_COMPRESS_DEEP_THRESHOLD",
    "TORMENT_COMPRESS_AGE_THRESHOLD",
    "TORMENT_COMPRESS_TEAR_EMERGENCY",
    "TORMENT_COMPRESS_SHORT_STRENGTH_MULT",
    "TORMENT_COMPRESS_LONG_STRENGTH",
    "TORMENT_COMPRESS_RELATIONAL_MULT",
    "TORMENT_COMPRESS_ECHO_MULT",
    "TORMENT_COMPRESS_TOOL_RESULT_MULT",
    "TORMENT_COMPRESS_TOOL_RESULT_SCORE_MULT",
    "TORMENT_COMPRESS_ECHO_DEEP_AGE",
    "TORMENT_COMPRESS_COUNT_THRESHOLD",
    "TORMENT_COMPRESS_STEP_INTERVAL",
    "TORMENT_COMPRESS_FALLBACK_COOLDOWN",
    "TORMENT_COMPRESS_PERIODIC_FLOOR",
    "TORMENT_MAX_PRIVATE_MEMORIES",
    "TORMENT_HARD_CAP_TARGET_RATIO",
    "TORMENT_REINFORCE_SIM_THRESHOLD",
)


class StageStop(RuntimeError):
    pass


class DirectResponse:
    def __init__(self, status_code: int, data: Any) -> None:
        self.status_code = int(status_code)
        self._data = data
        self.text = json.dumps(data, ensure_ascii=False, sort_keys=True)

    def json(self) -> Any:
        return self._data


class DirectAppClient:
    """Same-thread endpoint caller for app route functions.

    This preserves the accepted in-process endpoint-equivalent path while
    avoiding TestClient's extra thread boundary.
    """

    def __init__(self, app_mod: Any) -> None:
        self.app_mod = app_mod

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, **_: Any) -> DirectResponse:
        return self._dispatch("GET", path, params=params or {}, payload=None)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> DirectResponse:
        return self._dispatch("POST", path, params=params or {}, payload=json or {})

    def _wrap(self, fn: Any, *args: Any, **kwargs: Any) -> DirectResponse:
        try:
            data = fn(*args, **kwargs)
            if asyncio.iscoroutine(data):
                data = asyncio.run(data)
            return DirectResponse(200, data)
        except Exception as exc:
            status = int(getattr(exc, "status_code", 500) or 500)
            detail = getattr(exc, "detail", str(exc))
            return DirectResponse(status, {"detail": detail, "exception_type": type(exc).__name__})

    def _dispatch(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any],
        payload: Optional[Dict[str, Any]],
    ) -> DirectResponse:
        app_mod = self.app_mod
        if method == "GET" and path == "/health":
            return self._wrap(app_mod.health)
        if method == "GET" and path == "/embedder/check":
            return self._wrap(app_mod.embedder_check)
        if method == "GET" and path == "/config":
            return self._wrap(app_mod.config)
        if method == "GET" and path == "/debug/metrics":
            return self._wrap(
                app_mod.debug_metrics,
                workspace_id=str(params.get("workspace_id", "default")),
                agent_id=params.get("agent_id"),
            )
        if method == "GET" and path.startswith("/workspace/") and path.endswith("/compress/status"):
            parts = path.strip("/").split("/")
            return self._wrap(
                app_mod.compression_status,
                workspace_id=parts[1],
                agent_id=str(params.get("agent_id", "")),
            )
        if method == "GET" and path.startswith("/index/") and path.endswith("/recent"):
            parts = path.strip("/").split("/")
            return self._wrap(
                app_mod.index_recent_memories,
                workspace_id=parts[1],
                agent_id=parts[2],
                limit=int(params.get("limit", 20)),
            )
        if method == "POST" and path == "/workspace/create":
            return self._wrap(app_mod.workspace_create, app_mod.WorkspaceCreateReq(**(payload or {})))
        if method == "POST" and path == "/agent/create":
            return self._wrap(app_mod.agent_create, app_mod.AgentCreateReq(**(payload or {})))
        if method == "POST" and path == "/agent/query":
            return self._wrap(app_mod.query, app_mod.QueryReq(**(payload or {})))
        if method == "POST" and path == "/agent/ingest":
            return self._wrap(app_mod.ingest, app_mod.IngestReq(**(payload or {})), None)
        return DirectResponse(404, {"detail": f"Unhandled direct app route {method} {path}"})


class JsonlTail:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.position = 0

    def read_new(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        out: List[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as fh:
            fh.seek(self.position)
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict):
                    out.append(obj)
            self.position = fh.tell()
        return out


def run_git(args: Sequence[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.stdout.strip()


def baseline_snapshot() -> Dict[str, Any]:
    status = run_git(["status", "--short", "--branch"])
    head = run_git(["rev-parse", "HEAD"])
    origin = run_git(["rev-parse", "origin/main"])
    subject = run_git(["log", "-1", "--oneline"])
    if head != EXPECTED_HEAD or origin != EXPECTED_HEAD:
        raise StageStop(f"Baseline mismatch: HEAD={head} origin/main={origin}")
    if EXPECTED_SUBJECT not in subject:
        raise StageStop(f"Unexpected git subject: {subject}")
    return {
        "git_status_short_branch": status,
        "head": head,
        "origin_main": origin,
        "log_1_oneline": subject,
        "expected_head": EXPECTED_HEAD,
        "expected_subject": EXPECTED_SUBJECT,
    }


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_trajectory() -> Dict[str, Any]:
    if not PREVIOUS_TRAJECTORY_PATH.exists():
        raise StageStop(f"Missing preserved Experiment #4 trajectory: {PREVIOUS_TRAJECTORY_PATH}")
    if not PREVIOUS_4B_RESULT_PATH.exists():
        raise StageStop(f"Missing preserved Experiment #4B result: {PREVIOUS_4B_RESULT_PATH}")
    with PREVIOUS_TRAJECTORY_PATH.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    with PREVIOUS_4B_RESULT_PATH.open("r", encoding="utf-8") as fh:
        previous_4b = json.load(fh)
    trajectories = payload.get("trajectories")
    if not isinstance(trajectories, dict):
        raise StageStop(f"Preserved trajectory file has no trajectories object: {PREVIOUS_TRAJECTORY_PATH}")
    rows = trajectories.get(PREVIOUS_TRAJECTORY_ID)
    if not isinstance(rows, list) or len(rows) < SOURCE_HASH_EXCHANGES:
        raise StageStop(
            f"Preserved T1 has {len(rows) if isinstance(rows, list) else 'invalid'} rows; "
            f"need {SOURCE_HASH_EXCHANGES}"
        )

    from scripts import natural_long_memory_reachability_v1 as previous_harness

    regenerated_first = [previous_harness.generate_t1_pair(i) for i in range(VERIFY_FIRST_N)]
    preserved_first = [dict(row) for row in rows[:VERIFY_FIRST_N]]
    byte_mismatches = []
    for idx, (a, b) in enumerate(zip(preserved_first, regenerated_first), 1):
        if canonical_bytes(a) != canonical_bytes(b):
            byte_mismatches.append(idx)
    if byte_mismatches:
        raise StageStop(f"First {VERIFY_FIRST_N} T1 rows are not byte-identical at rows {byte_mismatches[:10]}")

    first_900 = [dict(row) for row in rows[:SOURCE_HASH_EXCHANGES]]
    first_900_digest = hashlib.sha256(canonical_bytes(first_900)).hexdigest()
    if first_900_digest != EXPECTED_SOURCE_FIRST_900_SHA:
        raise StageStop(
            "Preserved T1 first-900 SHA mismatch: "
            f"{first_900_digest} != {EXPECTED_SOURCE_FIRST_900_SHA}"
        )

    previous_trajectory = previous_4b.get("trajectory") if isinstance(previous_4b, Mapping) else {}
    previous_sha = previous_trajectory.get("sha256_canonical_json_sort_keys") if isinstance(previous_trajectory, Mapping) else None
    previous_count = previous_trajectory.get("selected_count") if isinstance(previous_trajectory, Mapping) else None
    if previous_sha != EXPECTED_SOURCE_FIRST_900_SHA or previous_count != SOURCE_HASH_EXCHANGES:
        raise StageStop(
            "Experiment #4B trajectory provenance mismatch: "
            f"sha={previous_sha!r} count={previous_count!r}"
        )

    selected = [dict(row) for row in rows[:MAX_EXCHANGES]]
    digest = hashlib.sha256(canonical_bytes(selected)).hexdigest()
    first_506 = [dict(row) for row in rows[:REPLAY_COMPARE_THROUGH_STEP]]
    first_506_digest = hashlib.sha256(canonical_bytes(first_506)).hexdigest()
    return {
        "source_path": str(PREVIOUS_TRAJECTORY_PATH.resolve()),
        "previous_4b_result_path": str(PREVIOUS_4B_RESULT_PATH.resolve()),
        "source_label": payload.get("label"),
        "source_subtype": payload.get("subtype"),
        "trajectory_id": PREVIOUS_TRAJECTORY_ID,
        "selected_count": len(selected),
        "sha256_canonical_json_sort_keys": digest,
        "first_550_sha256_canonical_json_sort_keys": digest,
        "source_first_900_sha256_canonical_json_sort_keys": first_900_digest,
        "first_506_sha256_canonical_json_sort_keys": first_506_digest,
        "canonicalization": "json.dumps(ensure_ascii=False, sort_keys=True, separators=(',', ':')) over selected list",
        "first_105_byte_identical_to_generator": True,
        "first_105_verification_source": "scripts.natural_long_memory_reachability_v1.generate_t1_pair",
        "first_506_byte_identical_to_4b_trajectory": True,
        "first_506_verification_method": "same preserved T1 source, #4B first-900 SHA/count matched, selected prefix canonicalized",
        "trajectory_scope": TRAJECTORY_SCOPE,
        "trajectory": selected,
    }


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                out.append(obj)
    return out


def api_json(client: DirectAppClient, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
    response = getattr(client, method.lower())(path, **kwargs)
    if response.status_code >= 400:
        raise StageStop(f"{method} {path} returned {response.status_code}: {response.text[:800]}")
    data = response.json()
    if not isinstance(data, dict):
        raise StageStop(f"{method} {path} returned non-object JSON: {data!r}")
    return data


def short_root_for(timestamp: str) -> Path:
    compact = timestamp.replace("-", "").replace(":", "").replace("T", "t").replace("Z", "z")
    compact = compact.split(".")[0]
    return Path(r"C:\t") / f"n4c{compact[-10:]}"


def paths_for(data_root: Path) -> Dict[str, Path]:
    agent_root = data_root / "workspaces" / WORKSPACE_ID / "agents" / AGENT_ID
    private_dir = agent_root / "private"
    deep_dir = agent_root / "deep_memory"
    return {
        "workspace": data_root / "workspaces" / WORKSPACE_ID,
        "agent": agent_root,
        "private": private_dir,
        "nodes": private_dir / "nodes.jsonl",
        "compression_log": private_dir / "compression_log.jsonl",
        "private_embeddings_manifest": private_dir / "embeddings" / "manifest.json",
        "private_embeddings_map": private_dir / "embeddings" / "shard_000000.map.jsonl",
        "deep_dir": deep_dir,
        "deep_memories": deep_dir / "memories.jsonl",
        "deep_embeddings_manifest": deep_dir / "embeddings" / "manifest.json",
        "deep_embeddings_map": deep_dir / "embeddings" / "shard_000000.map.jsonl",
    }


def path_preflight(data_root: Path) -> Dict[str, Any]:
    paths = paths_for(data_root)
    lengths = {name: len(str(path.resolve())) for name, path in paths.items()}
    max_name = max(lengths, key=lambda k: lengths[k])
    result = {
        "external_short_root": str(data_root.resolve()),
        "path_limit": PATH_LIMIT,
        "paths": {name: str(path.resolve()) for name, path in paths.items()},
        "path_lengths": lengths,
        "max_path_name": max_name,
        "max_path_length": lengths[max_name],
    }
    if lengths[max_name] > PATH_LIMIT:
        raise StageStop(f"Path preflight failed: {max_name} length {lengths[max_name]} > {PATH_LIMIT}")
    return result


def configure_environment(data_root: Path) -> Dict[str, Any]:
    threshold_present = {key: os.environ[key] for key in THRESHOLD_ENV_VARS if key in os.environ}
    if threshold_present:
        raise StageStop(f"Threshold env vars present before run: {threshold_present}")
    updates = {
        "PYTHONIOENCODING": "utf-8",
        "TOKENIZERS_PARALLELISM": "false",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "TORMENT_DATA_DIR": str(data_root.resolve()),
        "TORMENT_EXPECTED_DATA_DIR": str(data_root.resolve()),
        "TORMENT_COMPRESS_ENABLE": "1",
        "TORMENT_EMBED_PROVIDER": EXPECTED_EMBEDDER["provider"],
        "TORMENT_EMBED_MODEL": EXPECTED_EMBEDDER["model"],
        "TORMENT_EMBED_STRICT": "1",
        "TORMENT_EMBED_DEVICE": "cpu",
    }
    os.environ.update(updates)
    return {
        "set_env": dict(updates),
        "threshold_env_present_before_import": threshold_present,
        "threshold_env_policy": "fail closed if any threshold/reinforcement/router/EventDetector env var is present",
        "configuration_boundary": "NON_DEFAULT_COMPRESSION_ENABLED",
    }


def validate_embedder(health: Mapping[str, Any], check: Mapping[str, Any]) -> Dict[str, Any]:
    observations: Dict[str, Any] = {}
    for name, meta in (("health", health.get("embedder", {})), ("embedder_check", check)):
        if not isinstance(meta, Mapping):
            raise StageStop(f"{name} embedder metadata missing")
        observed = {
            "provider": str(meta.get("provider", "")),
            "model": str(meta.get("model", "")),
            "dim": int(meta.get("dim", 0) or 0),
            "degraded": bool(meta.get("degraded", False)),
        }
        observations[name] = observed
        if observed["provider"] != EXPECTED_EMBEDDER["provider"]:
            raise StageStop(f"{name} embedder provider mismatch: {observed}")
        if observed["model"] != EXPECTED_EMBEDDER["model"]:
            raise StageStop(f"{name} embedder model mismatch: {observed}")
        if observed["dim"] != EXPECTED_EMBEDDER["dim"]:
            raise StageStop(f"{name} embedder dim mismatch: {observed}")
        if observed["degraded"]:
            raise StageStop(f"{name} embedder degraded: {observed}")
    requested = health.get("requested_embedder") or {}
    if not isinstance(requested, Mapping) or requested.get("strict") is not True:
        raise StageStop(f"Requested strict embedder mode not active: {requested}")
    if bool(health.get("embedder_degraded", False)):
        raise StageStop(f"Health reports degraded embedder: {health}")
    return observations


def threshold_snapshot(app_mod: Any) -> Dict[str, Any]:
    from torment_service import compression as c

    fabric = app_mod.fabric
    snap = {
        "fabric": {
            "TORMENT_COMPRESS_ENABLE": bool(getattr(fabric, "_compress_enable", False)),
            "TORMENT_COMPRESS_MIN_STEP": int(getattr(fabric, "_compress_min_step", 0)),
        },
        "compression_module": {
            "TORMENT_COMPRESS_MIN_AGE": c.COMPRESS_MIN_AGE,
            "TORMENT_COMPRESS_MAX_CANDIDATES": c.COMPRESS_MAX_CANDIDATES,
            "TORMENT_COMPRESS_DEEP_THRESHOLD": c.COMPRESS_DEEP_THRESHOLD,
            "TORMENT_COMPRESS_AGE_THRESHOLD": c.COMPRESS_AGE_THRESHOLD,
            "TORMENT_COMPRESS_TEAR_EMERGENCY": c.COMPRESS_TEAR_EMERGENCY,
            "TORMENT_COMPRESS_SHORT_STRENGTH_MULT": c.COMPRESS_SHORT_PATH_MULT,
            "TORMENT_COMPRESS_LONG_STRENGTH": c.COMPRESS_LONG_PATH_STRENGTH,
            "TORMENT_COMPRESS_RELATIONAL_MULT": c.COMPRESS_RELATIONAL_MULT,
            "TORMENT_COMPRESS_ECHO_MULT": c.COMPRESS_ECHO_MULT,
            "TORMENT_COMPRESS_TOOL_RESULT_MULT": c.COMPRESS_TOOL_RESULT_MULT,
            "TORMENT_COMPRESS_TOOL_RESULT_SCORE_MULT": c.COMPRESS_TOOL_RESULT_SCORE_MULT,
            "TORMENT_COMPRESS_ECHO_DEEP_AGE": c.COMPRESS_ECHO_DEEP_AGE,
            "TORMENT_COMPRESS_COUNT_THRESHOLD": c.COMPRESS_COUNT_THRESHOLD,
            "TORMENT_COMPRESS_STEP_INTERVAL": c.COMPRESS_STEP_INTERVAL,
            "TORMENT_COMPRESS_FALLBACK_COOLDOWN": c.COMPRESS_FALLBACK_COOLDOWN,
            "TORMENT_COMPRESS_PERIODIC_FLOOR": c.COMPRESS_PERIODIC_FLOOR,
            "TORMENT_MAX_PRIVATE_MEMORIES": c.COMPRESS_HARD_CAP,
            "TORMENT_HARD_CAP_TARGET_RATIO": c.COMPRESS_HARD_CAP_TARGET,
        },
        "reinforcement": {
            "TORMENT_REINFORCE_SIM_THRESHOLD": (
                float(os.environ["TORMENT_REINFORCE_SIM_THRESHOLD"])
                if os.environ.get("TORMENT_REINFORCE_SIM_THRESHOLD")
                else 0.92
            ),
            "source": "fabric.ingest getenv default when env var absent",
        },
        "threshold_env_present": {key: os.environ.get(key) for key in THRESHOLD_ENV_VARS if key in os.environ},
    }
    expected = {
        "TORMENT_COMPRESS_MIN_STEP": 100,
        "TORMENT_COMPRESS_MIN_AGE": 50,
        "TORMENT_COMPRESS_MAX_CANDIDATES": 20,
        "TORMENT_COMPRESS_DEEP_THRESHOLD": 0.7,
        "TORMENT_COMPRESS_AGE_THRESHOLD": 500,
        "TORMENT_COMPRESS_TEAR_EMERGENCY": 0.7,
        "TORMENT_COMPRESS_SHORT_STRENGTH_MULT": 0.5,
        "TORMENT_COMPRESS_LONG_STRENGTH": 0.1,
        "TORMENT_COMPRESS_RELATIONAL_MULT": 0.7,
        "TORMENT_COMPRESS_ECHO_MULT": 0.4,
        "TORMENT_COMPRESS_TOOL_RESULT_MULT": 0.45,
        "TORMENT_COMPRESS_TOOL_RESULT_SCORE_MULT": 1.10,
        "TORMENT_COMPRESS_ECHO_DEEP_AGE": 150,
        "TORMENT_COMPRESS_COUNT_THRESHOLD": 400,
        "TORMENT_COMPRESS_STEP_INTERVAL": 200,
        "TORMENT_COMPRESS_FALLBACK_COOLDOWN": 50,
        "TORMENT_COMPRESS_PERIODIC_FLOOR": 0.4,
        "TORMENT_MAX_PRIVATE_MEMORIES": 10000,
        "TORMENT_HARD_CAP_TARGET_RATIO": 0.80,
        "TORMENT_REINFORCE_SIM_THRESHOLD": 0.92,
    }
    observed = {
        "TORMENT_COMPRESS_MIN_STEP": snap["fabric"]["TORMENT_COMPRESS_MIN_STEP"],
        "TORMENT_COMPRESS_MIN_AGE": snap["compression_module"]["TORMENT_COMPRESS_MIN_AGE"],
        "TORMENT_COMPRESS_MAX_CANDIDATES": snap["compression_module"]["TORMENT_COMPRESS_MAX_CANDIDATES"],
        "TORMENT_COMPRESS_DEEP_THRESHOLD": snap["compression_module"]["TORMENT_COMPRESS_DEEP_THRESHOLD"],
        "TORMENT_COMPRESS_AGE_THRESHOLD": snap["compression_module"]["TORMENT_COMPRESS_AGE_THRESHOLD"],
        "TORMENT_COMPRESS_TEAR_EMERGENCY": snap["compression_module"]["TORMENT_COMPRESS_TEAR_EMERGENCY"],
        "TORMENT_COMPRESS_SHORT_STRENGTH_MULT": snap["compression_module"]["TORMENT_COMPRESS_SHORT_STRENGTH_MULT"],
        "TORMENT_COMPRESS_LONG_STRENGTH": snap["compression_module"]["TORMENT_COMPRESS_LONG_STRENGTH"],
        "TORMENT_COMPRESS_RELATIONAL_MULT": snap["compression_module"]["TORMENT_COMPRESS_RELATIONAL_MULT"],
        "TORMENT_COMPRESS_ECHO_MULT": snap["compression_module"]["TORMENT_COMPRESS_ECHO_MULT"],
        "TORMENT_COMPRESS_TOOL_RESULT_MULT": snap["compression_module"]["TORMENT_COMPRESS_TOOL_RESULT_MULT"],
        "TORMENT_COMPRESS_TOOL_RESULT_SCORE_MULT": snap["compression_module"]["TORMENT_COMPRESS_TOOL_RESULT_SCORE_MULT"],
        "TORMENT_COMPRESS_ECHO_DEEP_AGE": snap["compression_module"]["TORMENT_COMPRESS_ECHO_DEEP_AGE"],
        "TORMENT_COMPRESS_COUNT_THRESHOLD": snap["compression_module"]["TORMENT_COMPRESS_COUNT_THRESHOLD"],
        "TORMENT_COMPRESS_STEP_INTERVAL": snap["compression_module"]["TORMENT_COMPRESS_STEP_INTERVAL"],
        "TORMENT_COMPRESS_FALLBACK_COOLDOWN": snap["compression_module"]["TORMENT_COMPRESS_FALLBACK_COOLDOWN"],
        "TORMENT_COMPRESS_PERIODIC_FLOOR": snap["compression_module"]["TORMENT_COMPRESS_PERIODIC_FLOOR"],
        "TORMENT_MAX_PRIVATE_MEMORIES": snap["compression_module"]["TORMENT_MAX_PRIVATE_MEMORIES"],
        "TORMENT_HARD_CAP_TARGET_RATIO": snap["compression_module"]["TORMENT_HARD_CAP_TARGET_RATIO"],
        "TORMENT_REINFORCE_SIM_THRESHOLD": snap["reinforcement"]["TORMENT_REINFORCE_SIM_THRESHOLD"],
    }
    mismatches = {
        key: {"expected": expected[key], "observed": observed[key]}
        for key in expected
        if observed[key] != expected[key]
    }
    if snap["threshold_env_present"]:
        raise StageStop(f"Threshold env present after import: {snap['threshold_env_present']}")
    if not snap["fabric"]["TORMENT_COMPRESS_ENABLE"]:
        raise StageStop("Compression enable flag did not take effect")
    if mismatches:
        raise StageStop(f"Compression/reinforcement threshold mismatch: {mismatches}")
    snap["validated_defaults"] = expected
    return snap


def preflight(client: DirectAppClient, app_mod: Any) -> Dict[str, Any]:
    health = api_json(client, "GET", "/health")
    embedder = validate_embedder(health, api_json(client, "GET", "/embedder/check"))
    config = api_json(client, "GET", "/config")
    workspace = api_json(client, "POST", "/workspace/create", json={"workspace_id": WORKSPACE_ID})
    agent = api_json(
        client,
        "POST",
        "/agent/create",
        json={
            "workspace_id": WORKSPACE_ID,
            "agent_id": AGENT_ID,
            "seed": {
                "seed_id": SEED_ID,
                "character_name": CHARACTER_NAME,
                "seed_text": "Focused lived-use experiment identity seed for Eira Voss.",
                "coupling_mode": "read_only",
            },
        },
    )
    recent = api_json(client, "GET", f"/index/{WORKSPACE_ID}/{AGENT_ID}/recent", params={"limit": 1})
    current_step = resolve_current_step(recent)
    if current_step != 0:
        raise StageStop(f"Fresh workspace did not start at step 0: {current_step}")
    return {
        "health": health,
        "embedder_observations": embedder,
        "config": config,
        "workspace_create": workspace,
        "agent_create": agent,
        "recent_index": recent,
        "resumed_current_step": current_step,
        "threshold_snapshot": threshold_snapshot(app_mod),
        "compression_status": api_json(
            client,
            "GET",
            f"/workspace/{WORKSPACE_ID}/compress/status",
            params={"agent_id": AGENT_ID},
        ),
        "debug_metrics": api_json(
            client,
            "GET",
            "/debug/metrics",
            params={"workspace_id": WORKSPACE_ID, "agent_id": AGENT_ID},
        ),
    }


def resolve_current_step(response: Mapping[str, Any]) -> int:
    if response.get("ok") is not True:
        raise StageStop(f"Recent index response not ok: {response}")
    rows = response.get("results")
    if not isinstance(rows, list) or not rows:
        return 0
    row = rows[0]
    if not isinstance(row, Mapping):
        raise StageStop(f"Malformed recent row: {row!r}")
    step = row.get("step")
    if not isinstance(step, int) or step < 0:
        raise StageStop(f"Invalid recent step: {row!r}")
    return int(step)


def graph_snapshot(app_mod: Any) -> Dict[int, Dict[str, Any]]:
    fabric = app_mod.fabric
    ak = fabric._agent_key(WORKSPACE_ID, AGENT_ID)
    graph = fabric.private_graphs.get(ak)
    if graph is None:
        return {}
    out: Dict[int, Dict[str, Any]] = {}
    for eid, ent in graph.entities.items():
        out[int(eid)] = {
            "eid": int(eid),
            "born_step": int(getattr(ent, "born_step", 0) or 0),
            "payload": deepcopy(dict(ent.payload or {})),
        }
    return out


def apply_node_row(snapshot: Dict[int, Dict[str, Any]], row: Mapping[str, Any]) -> None:
    try:
        eid = int(row.get("eid", 0) or 0)
    except Exception:
        return
    payload = row.get("payload")
    if not isinstance(payload, Mapping):
        return
    snapshot[eid] = {
        "eid": eid,
        "born_step": int(row.get("born_step", payload.get("created_at", 0)) or 0),
        "payload": deepcopy(dict(payload)),
    }


def is_current_step_compression_patch(row: Mapping[str, Any], step: int) -> bool:
    payload = row.get("payload")
    if not isinstance(payload, Mapping):
        return False
    route = payload.get("compression_route")
    if route not in ("short_path", "long_path"):
        return False
    try:
        if int(payload.get("compressed_step", -10**9)) == int(step):
            return True
    except Exception:
        pass
    try:
        if int(payload.get("exported_step", -10**9)) == int(step):
            return True
    except Exception:
        pass
    return False


def reconstruct_pre_event_snapshot(
    before: Mapping[int, Mapping[str, Any]],
    appended_nodes: Sequence[Mapping[str, Any]],
    step: int,
) -> Dict[int, Dict[str, Any]]:
    snap: Dict[int, Dict[str, Any]] = deepcopy(dict(before))  # type: ignore[arg-type]
    for row in appended_nodes:
        if is_current_step_compression_patch(row, step):
            break
        apply_node_row(snap, row)
    return snap


def payload_of(item: Mapping[str, Any]) -> Dict[str, Any]:
    payload = item.get("payload") if isinstance(item, Mapping) else {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def derived_tier(payload: Mapping[str, Any]) -> str:
    from torment_service.compression import derive_retention_tier

    return derive_retention_tier(dict(payload))


def is_target_payload(payload: Mapping[str, Any]) -> bool:
    if str(payload.get("memory_class", "core") or "core") != "core":
        return False
    if str(payload.get("type") or payload.get("mtype") or "") != "episode":
        return False
    if bool(payload.get("canon", False)):
        return False
    if derived_tier(payload) != "relational":
        return False
    provenance = payload.get("provenance")
    if isinstance(provenance, Mapping) and provenance.get("source_type") in ("tool_result", "collective_echo"):
        return False
    return True


def target_eids(snapshot: Mapping[int, Mapping[str, Any]]) -> List[int]:
    return sorted(
        int(eid)
        for eid, item in snapshot.items()
        if is_target_payload(payload_of(item))
    )


def compact_source(eid: int, snapshot: Mapping[int, Mapping[str, Any]], step: int) -> Dict[str, Any]:
    item = snapshot.get(int(eid), {})
    payload = payload_of(item)
    born = int(item.get("born_step", payload.get("created_at", 0)) or 0) if isinstance(item, Mapping) else 0
    tier = None
    try:
        tier = derived_tier(payload)
    except Exception:
        tier = None
    return {
        "eid": int(eid),
        "born_step": born,
        "current_step": int(step),
        "age": int(step) - born,
        "type": payload.get("type") or payload.get("mtype"),
        "memory_class": payload.get("memory_class"),
        "canon": bool(payload.get("canon", False)),
        "retention_tier": tier,
        "strength": payload.get("strength"),
        "half_life": payload.get("half_life"),
        "retrieval_count": int(payload.get("retrieval_count", 0) or 0),
        "reinforcement_count": int(payload.get("reinforcement_count", 0) or 0),
        "last_reinforced": payload.get("last_reinforced"),
        "last_reinforced_ts": payload.get("last_reinforced_ts"),
        "compressed": bool(payload.get("compressed", False)),
        "compressed_step": payload.get("compressed_step"),
        "compression_route": payload.get("compression_route"),
        "compression_score": payload.get("compression_score"),
        "compression_tier": payload.get("compression_tier"),
        "exported_deep": bool(payload.get("exported_deep", False)),
        "exported_step": payload.get("exported_step"),
        "summary_length": len(str(payload.get("summary", "") or "")),
        "summary_prefix": str(payload.get("summary", "") or "")[:200],
        "embedding_ref": payload.get("embedding_ref"),
    }


def load_coherence_field(data_root: Path) -> Optional[List[Dict[str, Any]]]:
    motifs_path = data_root / "workspaces" / WORKSPACE_ID / "domains" / DOMAIN_ID / "motifs.json"
    if not motifs_path.exists():
        return None
    try:
        with motifs_path.open("r", encoding="utf-8") as fh:
            motifs_data = json.load(fh)
        if isinstance(motifs_data, dict):
            motifs_data = motifs_data.get("motifs", [])
        from torment_service.coherence_field import compute_coherence_field

        return compute_coherence_field(motifs_data)
    except Exception:
        return None


def score_components(
    *,
    eid: int,
    item: Mapping[str, Any],
    step: int,
    coherence_field: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    payload = payload_of(item)
    born_step = int(item.get("born_step", payload.get("created_at", payload.get("born_step", 0))) or 0)
    tier = derived_tier(payload)
    age = int(step) - born_step
    strength = float(payload.get("strength", 0.5) or 0.5)
    retrieval_count = int(payload.get("retrieval_count", 0) or 0)
    motif_id = payload.get("motif_id") or None
    retrieval_resist = min(1.0, math.log1p(retrieval_count) / math.log(11.0))
    basin_resist = 0.0
    motif_role = None
    phi = None
    tension = None
    phi_compressible = 0.5
    tension_resist = 0.0
    role_compress = 0.5
    if motif_id and coherence_field:
        for mf in coherence_field:
            if str(mf.get("motif_id", "")) == str(motif_id):
                motif_role = str(mf.get("role", ""))
                if motif_role == "basin":
                    basin_resist = 0.6
                elif motif_role == "ridge":
                    basin_resist = 0.3
                phi = float(mf.get("phi", 0.0) or 0.0)
                tension = float(mf.get("tension", 0.0) or 0.0)
                phi_compressible = 1.0 - min(1.0, abs(phi))
                tension_resist = min(1.0, tension)
                if motif_role == "plateau":
                    role_compress = 0.8
                elif motif_role == "ridge":
                    role_compress = 0.5
                elif motif_role == "basin":
                    role_compress = 0.2
                break
    j_importance = 0.35 * strength + 0.35 * retrieval_resist + 0.30 * basin_resist
    j_score_before_sustain = 1.0 - j_importance
    phase_dur = int(payload.get("phase_duration_steps", 0) or 0)
    corridor_dur = int(payload.get("corridor_duration_steps", 0) or 0)
    sustained = max(phase_dur, corridor_dur)
    j_score = max(0.0, j_score_before_sustain - 0.15) if sustained >= 10 else j_score_before_sustain
    srg = payload.get("srg")
    srg_adjustments: Dict[str, Any] = {}
    if isinstance(srg, Mapping):
        if srg.get("is_crystal", False):
            srg_adjustments["is_crystal"] = True
        if srg.get("heartbeat_class") == "A":
            j_score *= 0.85
            srg_adjustments["heartbeat_class_A_mult"] = 0.85
        srg_r = float(srg.get("R", 0.0) or 0.0)
        if srg_r > 0.15:
            mult = 1.0 - 0.1 * min(1.0, srg_r / 0.176)
            j_score *= mult
            srg_adjustments["R_mult"] = mult
    z_score = 0.40 * phi_compressible + 0.30 * (1.0 - tension_resist) + 0.30 * role_compress
    composite = 0.60 * j_score + 0.40 * z_score
    tier_mult = 1.0
    if tier == "echo":
        composite = min(1.0, composite * 1.15)
        tier_mult = 1.15
    elif tier == "tool_result":
        from torment_service.compression import COMPRESS_TOOL_RESULT_SCORE_MULT

        composite = min(1.0, composite * COMPRESS_TOOL_RESULT_SCORE_MULT)
        tier_mult = COMPRESS_TOOL_RESULT_SCORE_MULT
    elif tier == "relational":
        composite = max(0.0, composite * 0.85)
        tier_mult = 0.85
    elif tier == "identity":
        composite = max(0.0, composite * 0.70)
        tier_mult = 0.70
    return {
        "eid": int(eid),
        "born_step": born_step,
        "age": age,
        "tier": tier,
        "strength": strength,
        "retrieval_count": retrieval_count,
        "motif_id": motif_id,
        "motif_role": motif_role,
        "retrieval_resist": retrieval_resist,
        "basin_resist": basin_resist,
        "j_importance": j_importance,
        "j_score_before_sustain": j_score_before_sustain,
        "phase_duration_steps": phase_dur,
        "corridor_duration_steps": corridor_dur,
        "sustained_duration": sustained,
        "j_score": j_score,
        "phi": phi,
        "tension": tension,
        "phi_compressible": phi_compressible,
        "tension_resist": tension_resist,
        "role_compress": role_compress,
        "z_score": z_score,
        "composite_after_tier": composite,
        "score_rounded_production": round(composite, 4),
        "tier_multiplier": tier_mult,
        "srg_adjustments": srg_adjustments,
    }


def diagnostic_candidates(
    *,
    snapshot: Mapping[int, Mapping[str, Any]],
    step: int,
    coherence_field: Optional[List[Dict[str, Any]]],
) -> Dict[int, Dict[str, Any]]:
    from torment_service.compression import CompressionScorer, CompressionRouter

    scorer = CompressionScorer()
    router = CompressionRouter()
    scored = []
    for eid, item in snapshot.items():
        payload = payload_of(item)
        node = {
            "eid": int(eid),
            "born_step": int(item.get("born_step", payload.get("created_at", 0)) or 0),
            "payload": payload,
        }
        c = scorer.score(node, int(step), coherence_field)
        if c is None:
            continue
        c.route = router.route(c, int(step))
        scored.append(c)
    scored.sort(key=lambda c: c.score, reverse=True)
    out: Dict[int, Dict[str, Any]] = {}
    for rank, c in enumerate(scored, 1):
        item = snapshot.get(int(c.eid), {})
        out[int(c.eid)] = {
            "diagnostic_label": "CODE_REDERIVED_DIAGNOSTIC_NOT_PRODUCTION_EVENT_LOG",
            "rank_before_cap": rank,
            "inside_candidate_cap": rank <= scorer.max_candidates,
            "candidate_score": c.score,
            "candidate_j_score": c.j_score,
            "candidate_z_score": c.z_score,
            "candidate_route": c.route,
            "candidate_tier": c.tier,
            "candidate_memory_class": c.memory_class,
            "candidate_born_step": c.born_step,
            "candidate_age": int(step) - int(c.born_step),
            "components": score_components(
                eid=int(c.eid),
                item=item,
                step=int(step),
                coherence_field=coherence_field,
            )
            if isinstance(item, Mapping)
            else None,
        }
    return out


def classify_target_status(
    *,
    eid: int,
    snapshot: Mapping[int, Mapping[str, Any]],
    diagnostics: Mapping[int, Mapping[str, Any]],
    step: int,
) -> str:
    item = snapshot.get(int(eid))
    if not isinstance(item, Mapping):
        return "OTHER"
    payload = payload_of(item)
    try:
        tier = derived_tier(payload)
    except Exception:
        return "OTHER"
    if tier == "protected" or bool(payload.get("canon", False)):
        return "PROTECTED"
    born = int(item.get("born_step", payload.get("created_at", 0)) or 0)
    if int(step) - born < 50:
        return "TOO_YOUNG"
    diag = diagnostics.get(int(eid))
    if not isinstance(diag, Mapping):
        return "NOT_OBSERVABLE_WITHOUT_REDERIVATION"
    if diag.get("inside_candidate_cap"):
        return "ELIGIBLE_AND_SELECTED"
    return "ELIGIBLE_BUT_OUTSIDE_CANDIDATE_CAP"


def changed_eids_for_step(appended_nodes: Sequence[Mapping[str, Any]], step: int) -> List[int]:
    out: List[int] = []
    for row in appended_nodes:
        if is_current_step_compression_patch(row, step):
            try:
                out.append(int(row.get("eid", 0) or 0))
            except Exception:
                pass
    return sorted(set(out))


def deep_records(paths: Mapping[str, Path]) -> List[Dict[str, Any]]:
    return read_jsonl(paths["deep_memories"])


def deep_file_state(paths: Mapping[str, Path]) -> Dict[str, Any]:
    records = deep_records(paths)
    deep_dir = paths["deep_dir"]
    memories = paths["deep_memories"]
    return {
        "state": "present_with_records" if records else ("initialized_but_empty" if deep_dir.exists() else "absent"),
        "deep_dir": str(deep_dir.resolve()),
        "memories_path": str(memories.resolve()),
        "count": len(records),
        "records": records[-5:],
    }


def read_json_file(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def deep_vector_state(paths: Mapping[str, Path]) -> Dict[str, Any]:
    manifest = read_json_file(paths["deep_embeddings_manifest"])
    map_rows = read_jsonl(paths["deep_embeddings_map"])
    shard_path = paths["deep_embeddings_map"].parent / "shard_000000.npy"
    return {
        "manifest_path": str(paths["deep_embeddings_manifest"].resolve()),
        "manifest": manifest,
        "map_path": str(paths["deep_embeddings_map"].resolve()),
        "map_row_count": len(map_rows),
        "map_tail": map_rows[-5:],
        "shard_path": str(shard_path.resolve()),
        "shard_exists": shard_path.exists(),
        "shard_bytes": shard_path.stat().st_size if shard_path.exists() else None,
    }


def checkpoint_state(paths: Mapping[str, Path], current_step: int) -> Dict[str, Any]:
    checkpoint_dir = paths["private"] / "checkpoints"
    files = []
    if checkpoint_dir.exists():
        for file in sorted(checkpoint_dir.glob("*")):
            if file.is_file():
                files.append(
                    {
                        "name": file.name,
                        "bytes": file.stat().st_size,
                        "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
                    }
                )
    tmp_500 = checkpoint_dir / "checkpoint_000500.json.tmp"
    final_500 = checkpoint_dir / "checkpoint_000500.json"
    return {
        "checkpoint_dir": str(checkpoint_dir.resolve()),
        "files": files,
        "step500_tmp_exists": tmp_500.exists(),
        "step500_tmp_bytes": tmp_500.stat().st_size if tmp_500.exists() else None,
        "step500_final_exists": final_500.exists(),
        "continuous_execution_after_step500": int(current_step) > 500,
        "warning_status": (
            "RESIDUE_OBSERVED_NON_MATERIAL_TO_CONTINUOUS_RUN"
            if tmp_500.exists() and int(current_step) > 500
            else "NO_STEP500_TMP_RESIDUE_OBSERVED"
        ),
    }


def _round4(value: Any) -> Any:
    if isinstance(value, (int, float)):
        return round(float(value), 4)
    return value


def event_replay_slim(record: Mapping[str, Any]) -> Dict[str, Any]:
    rows = []
    for row in record.get("target_rows", []) if isinstance(record.get("target_rows"), list) else []:
        pre = row.get("pre") if isinstance(row.get("pre"), Mapping) else {}
        post = row.get("post") if isinstance(row.get("post"), Mapping) else {}
        diag = row.get("diagnostic") if isinstance(row.get("diagnostic"), Mapping) else {}
        rows.append(
            {
                "eid": int(row.get("eid", 0) or 0),
                "classification": row.get("classification"),
                "mutated_by_event": bool(row.get("mutated_by_event")),
                "age": pre.get("age"),
                "pre_strength": _round4(pre.get("strength")),
                "post_strength": _round4(post.get("strength")),
                "reinforcement_count": pre.get("reinforcement_count"),
                "score": _round4(diag.get("candidate_score")),
                "rank_before_cap": diag.get("rank_before_cap"),
                "inside_candidate_cap": diag.get("inside_candidate_cap"),
                "diagnostic_route": diag.get("candidate_route"),
                "post_route": post.get("compression_route"),
                "exported_deep": bool(post.get("exported_deep", False)),
            }
        )
    return {
        "step": record.get("step"),
        "trigger": record.get("trigger"),
        "candidate_count": record.get("candidate_count"),
        "compressed_count": record.get("compressed_count"),
        "exported_deep_count": record.get("exported_deep_count"),
        "changed_eids": record.get("changed_eids"),
        "target_rows": sorted(rows, key=lambda r: r["eid"]),
    }


def load_previous_4b_replay() -> Dict[str, Any]:
    payload = read_json_file(PREVIOUS_4B_RESULT_PATH)
    if not isinstance(payload, Mapping):
        raise StageStop(f"Invalid #4B result JSON: {PREVIOUS_4B_RESULT_PATH}")
    records = payload.get("compression_events")
    if not isinstance(records, list):
        raise StageStop("#4B result has no compression_events list")
    by_step = {
        int(rec.get("step", -1)): event_replay_slim(rec)
        for rec in records
        if isinstance(rec, Mapping) and int(rec.get("step", -1)) <= REPLAY_COMPARE_THROUGH_STEP
    }
    return {
        "path": str(PREVIOUS_4B_RESULT_PATH.resolve()),
        "target_eids": (payload.get("target_cohort") or {}).get("eids") if isinstance(payload.get("target_cohort"), Mapping) else None,
        "identity_anchor_eids": sorted(
            int(eid)
            for eid in ((payload.get("background_identity") or {}).get("identity_anchor_export_counts") or {}).keys()
        )
        if isinstance(payload.get("background_identity"), Mapping)
        else [],
        "compression_event_count_through_506": len(by_step),
        "compression_event_steps_triggers_through_506": [
            {"step": rec.get("step"), "trigger": rec.get("trigger")}
            for rec in records
            if isinstance(rec, Mapping) and int(rec.get("step", -1)) <= REPLAY_COMPARE_THROUGH_STEP
        ],
        "events_by_step": by_step,
    }


def compare_replay_event(
    *,
    actual: Mapping[str, Any],
    expected_by_step: Mapping[int, Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    step = int(actual.get("step", -1))
    if step > REPLAY_COMPARE_THROUGH_STEP:
        return []
    actual_slim = event_replay_slim(actual)
    expected = expected_by_step.get(step)
    if expected is None:
        return [{"step": step, "field": "event_presence", "expected": "present_in_4b", "actual": "missing"}]
    mismatches = []
    for key in ("trigger", "candidate_count", "compressed_count", "exported_deep_count", "changed_eids"):
        if actual_slim.get(key) != expected.get(key):
            mismatches.append({"step": step, "field": key, "expected": expected.get(key), "actual": actual_slim.get(key)})
    if actual_slim.get("target_rows") != expected.get("target_rows"):
        mismatches.append(
            {
                "step": step,
                "field": "target_rows_slim",
                "expected": expected.get("target_rows"),
                "actual": actual_slim.get("target_rows"),
            }
        )
    return mismatches


def analytic_ceiling_from_sustained(sustained: Any) -> Optional[float]:
    if not isinstance(sustained, int):
        return None
    return round((0.6545 if sustained >= 10 else 0.731) - 0.1785 * 0.05, 4)


def target_split_audit(compression_events: Sequence[Mapping[str, Any]], target_set: Sequence[int]) -> Dict[str, Any]:
    first_diag: Dict[int, Dict[str, Any]] = {}
    for event in compression_events:
        rows = event.get("target_rows")
        if not isinstance(rows, list):
            continue
        for row in rows:
            eid = int(row.get("eid", 0) or 0)
            if eid in first_diag:
                continue
            pre = row.get("pre") if isinstance(row.get("pre"), Mapping) else {}
            diag = row.get("diagnostic") if isinstance(row.get("diagnostic"), Mapping) else {}
            components = diag.get("components") if isinstance(diag.get("components"), Mapping) else {}
            sustained = components.get("sustained_duration")
            ceiling = analytic_ceiling_from_sustained(sustained)
            first_diag[eid] = {
                "eid": eid,
                "born_step": pre.get("born_step"),
                "sustained": sustained,
                "penalty_status": "SUSTAINED_GE_10" if isinstance(sustained, int) and sustained >= 10 else "NO_SUSTAINED_GE_10",
                "analytic_ceiling": ceiling,
                "score_capable": bool(isinstance(ceiling, float) and ceiling >= 0.7),
            }
    rows = [first_diag[eid] for eid in sorted(target_set) if eid in first_diag]
    return {
        "rows": rows,
        "score_capable_eids": [r["eid"] for r in rows if r.get("score_capable")],
        "penalty_blocked_eids": [r["eid"] for r in rows if not r.get("score_capable")],
        "expected_split_replicated": (
            len([r for r in rows if r.get("score_capable")]) == 10
            and len([r for r in rows if not r.get("score_capable")]) == 10
        ),
    }


def mechanics_checks(
    *,
    paths: Mapping[str, Path],
    target_set: Sequence[int],
    compression_events: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    short_total = 0
    short_mismatches = []
    for event in compression_events:
        for row in event.get("target_rows", []) if isinstance(event.get("target_rows"), list) else []:
            post = row.get("post") if isinstance(row.get("post"), Mapping) else {}
            pre = row.get("pre") if isinstance(row.get("pre"), Mapping) else {}
            if not row.get("mutated_by_event") or post.get("compression_route") != "short_path":
                continue
            if int(row.get("eid", 0) or 0) not in target_set:
                continue
            short_total += 1
            old_strength = pre.get("strength")
            new_strength = post.get("strength")
            if isinstance(old_strength, (int, float)) and isinstance(new_strength, (int, float)):
                expected = round(max(0.05, float(old_strength) * 0.7), 4)
                if round(float(new_strength), 4) != expected:
                    short_mismatches.append(
                        {
                            "eid": row.get("eid"),
                            "step": event.get("step"),
                            "old_strength": old_strength,
                            "new_strength": new_strength,
                            "expected": expected,
                        }
                    )

    reinforcement_total = 0
    reinforcement_mismatches = []
    previous_by_eid: Dict[int, Dict[str, Any]] = {}
    for row in read_jsonl(paths["nodes"]):
        eid = int(row.get("eid", 0) or 0)
        payload = payload_of(row)
        if eid not in target_set or not payload:
            previous_by_eid[eid] = payload
            continue
        previous = previous_by_eid.get(eid)
        if isinstance(previous, Mapping):
            prev_count = int(previous.get("reinforcement_count", 0) or 0)
            cur_count = int(payload.get("reinforcement_count", 0) or 0)
            if cur_count > prev_count:
                reinforcement_total += 1
                old_strength = previous.get("strength")
                new_strength = payload.get("strength")
                if isinstance(old_strength, (int, float)) and isinstance(new_strength, (int, float)):
                    expected = round(min(0.98, 0.7 * float(old_strength) + 0.3), 4)
                    if abs(round(float(new_strength), 4) - expected) > 0.00011:
                        reinforcement_mismatches.append(
                            {
                                "eid": eid,
                                "last_reinforced": payload.get("last_reinforced"),
                                "old_strength": old_strength,
                                "new_strength": new_strength,
                                "expected": expected,
                            }
                        )
        previous_by_eid[eid] = payload

    return {
        "relational_short_path": {
            "checked": short_total,
            "mismatches": short_mismatches,
            "confirmed": short_total > 0 and not short_mismatches,
            "formula": "round(max(0.05, strength * 0.7), 4)",
        },
        "reinforcement": {
            "checked": reinforcement_total,
            "mismatches": reinforcement_mismatches,
            "confirmed": reinforcement_total > 0 and not reinforcement_mismatches,
            "formula": "round(min(0.98, 0.7 * strength + 0.3), 4)",
            "production_source": "torment_service.fabric duplicate-suppression reinforcement cap",
            "tolerance": "0.00011 because predecessor strengths are read back from rounded JSONL payloads",
        },
    }


def eid22_behavior(compression_events: Sequence[Mapping[str, Any]], final_snapshot: Mapping[int, Mapping[str, Any]]) -> Dict[str, Any]:
    observations = []
    for event in compression_events:
        for row in event.get("target_rows", []) if isinstance(event.get("target_rows"), list) else []:
            if int(row.get("eid", 0) or 0) != 22:
                continue
            pre = row.get("pre") if isinstance(row.get("pre"), Mapping) else {}
            post = row.get("post") if isinstance(row.get("post"), Mapping) else {}
            diag = row.get("diagnostic") if isinstance(row.get("diagnostic"), Mapping) else {}
            observations.append(
                {
                    "step": event.get("step"),
                    "trigger": event.get("trigger"),
                    "age": pre.get("age"),
                    "strength": pre.get("strength"),
                    "score": diag.get("candidate_score"),
                    "rank_before_cap": diag.get("rank_before_cap"),
                    "classification": row.get("classification"),
                    "post_route": post.get("compression_route"),
                    "exported_deep": post.get("exported_deep"),
                }
            )
    final = compact_source(22, final_snapshot, max((int(e.get("step", 0) or 0) for e in compression_events), default=0)) if 22 in final_snapshot else None
    reached = any(isinstance(obs.get("age"), int) and obs["age"] >= 500 for obs in observations)
    long_path = any(obs.get("post_route") == "long_path" for obs in observations)
    return {
        "observations_count": len(observations),
        "first_observation": observations[0] if observations else None,
        "first_age500_observation": next((obs for obs in observations if isinstance(obs.get("age"), int) and obs["age"] >= 500), None),
        "last_observation": observations[-1] if observations else None,
        "final_source": final,
        "reached_age500": reached,
        "long_path": long_path,
    }


def summarize_compression_event(
    *,
    event: Mapping[str, Any],
    exchange: int,
    step: int,
    pre_snapshot: Mapping[int, Mapping[str, Any]],
    post_snapshot: Mapping[int, Mapping[str, Any]],
    diagnostics: Mapping[int, Mapping[str, Any]],
    target_set: Sequence[int],
    changed_eids: Sequence[int],
) -> Dict[str, Any]:
    event_targets = []
    for eid in target_set:
        pre = compact_source(eid, pre_snapshot, step)
        post = compact_source(eid, post_snapshot, step) if eid in post_snapshot else {}
        diag = diagnostics.get(int(eid))
        event_targets.append(
            {
                "eid": int(eid),
                "classification": classify_target_status(
                    eid=int(eid),
                    snapshot=pre_snapshot,
                    diagnostics=diagnostics,
                    step=step,
                ),
                "pre": pre,
                "post": post,
                "diagnostic": diag,
                "mutated_by_event": int(eid) in set(int(x) for x in changed_eids),
            }
        )
    return {
        "exchange": int(exchange),
        "step": int(step),
        "event": dict(event),
        "trigger": event.get("trigger"),
        "candidate_count": event.get("candidates_evaluated"),
        "compressed_count": event.get("compressed"),
        "exported_deep_count": event.get("exported_deep"),
        "changed_eids": list(changed_eids),
        "target_rows": event_targets,
    }


def graph_counts(snapshot: Mapping[int, Mapping[str, Any]]) -> Dict[str, Any]:
    counts = {
        "source_rows": len(snapshot),
        "target_rows": len(target_eids(snapshot)),
        "short_path_source_rows": 0,
        "long_path_source_rows": 0,
        "exported_deep_source_rows": 0,
        "identity_anchor_rows": 0,
        "identity_anchor_long_path_rows": 0,
        "reinforcement_total": 0,
    }
    for item in snapshot.values():
        payload = payload_of(item)
        if payload.get("compression_route") == "short_path":
            counts["short_path_source_rows"] += 1
        if payload.get("compression_route") == "long_path":
            counts["long_path_source_rows"] += 1
        if payload.get("exported_deep"):
            counts["exported_deep_source_rows"] += 1
        if str(payload.get("type") or payload.get("mtype") or "") == "identity_anchor":
            counts["identity_anchor_rows"] += 1
            if payload.get("compression_route") == "long_path" or payload.get("exported_deep"):
                counts["identity_anchor_long_path_rows"] += 1
        counts["reinforcement_total"] += int(payload.get("reinforcement_count", 0) or 0)
    return counts


def route_cause_for_target_long_path(
    *,
    eid: int,
    event_record: Mapping[str, Any],
    step: int,
) -> Dict[str, Any]:
    rows = event_record.get("target_rows")
    if not isinstance(rows, list):
        return {"accepted": False, "reason": "target_rows_missing"}
    for row in rows:
        if int(row.get("eid", -1)) != int(eid):
            continue
        pre = row.get("pre") if isinstance(row.get("pre"), Mapping) else {}
        diag = row.get("diagnostic") if isinstance(row.get("diagnostic"), Mapping) else {}
        post = row.get("post") if isinstance(row.get("post"), Mapping) else {}
        score = diag.get("candidate_score") if isinstance(diag, Mapping) else None
        age = pre.get("age") if isinstance(pre, Mapping) else None
        accepted = (
            pre.get("retention_tier") == "relational"
            and pre.get("memory_class") == "core"
            and pre.get("type") == "episode"
            and pre.get("canon") is False
            and isinstance(age, int)
            and age >= 500
            and isinstance(score, (int, float))
            and float(score) >= 0.7
            and post.get("compression_route") == "long_path"
            and post.get("exported_deep") is True
        )
        excluded_special_route = {
            "identity_tier": pre.get("retention_tier") == "identity",
            "echo_tier": pre.get("retention_tier") == "echo",
            "archive_class": pre.get("memory_class") == "archive",
            "manual_mutation": False,
            "special_source_class": pre.get("type") != "episode" or pre.get("memory_class") != "core",
        }
        return {
            "accepted": bool(accepted),
            "route_cause": "AGE_SCORE" if accepted else "REJECTED_SPECIAL_OR_INSUFFICIENT_ROUTE",
            "router_branch_verified": (
                "generic score>=deep_threshold and age>=age_threshold branch"
                if accepted
                else "not verified"
            ),
            "excluded_special_route": excluded_special_route,
            "eid": int(eid),
            "step": int(step),
            "pre": pre,
            "diagnostic": diag,
            "post": post,
        }
    return {"accepted": False, "reason": "eid_not_found_in_event_target_rows", "eid": int(eid)}


def update_record_high(
    state: Dict[str, Any],
    *,
    eid: int,
    event_record: Mapping[str, Any],
) -> None:
    rows = event_record.get("target_rows")
    if not isinstance(rows, list):
        return
    for row in rows:
        diag = row.get("diagnostic") if isinstance(row.get("diagnostic"), Mapping) else None
        if not isinstance(diag, Mapping):
            continue
        score = diag.get("candidate_score")
        if not isinstance(score, (int, float)):
            continue
        current = state.get("maximum_relational_score_observed")
        if not isinstance(current, Mapping) or float(score) > float(current.get("score", -1.0)):
            state["maximum_relational_score_observed"] = {
                "score": float(score),
                "eid": int(row.get("eid", 0) or 0),
                "step": event_record.get("step"),
                "exchange": event_record.get("exchange"),
                "age": (row.get("pre") or {}).get("age") if isinstance(row.get("pre"), Mapping) else None,
                "strength": (row.get("pre") or {}).get("strength") if isinstance(row.get("pre"), Mapping) else None,
                "components": diag.get("components"),
            }


def finalize_taxonomy(state: Mapping[str, Any], target_histories: Mapping[int, List[Mapping[str, Any]]]) -> Dict[str, Any]:
    milestones = state.get("milestones") if isinstance(state.get("milestones"), Mapping) else {}
    repeated = any(
        len([entry for entry in hist if entry.get("post_route") == "short_path"]) >= 2
        for hist in target_histories.values()
    )
    first_long = state.get("first_ordinary_relational_long_path")
    first_deep = state.get("first_ordinary_relational_deepmemory")
    mechanics = state.get("mechanics_checks") if isinstance(state.get("mechanics_checks"), Mapping) else {}
    short_mechanics = mechanics.get("relational_short_path") if isinstance(mechanics.get("relational_short_path"), Mapping) else {}
    reinforcement = mechanics.get("reinforcement") if isinstance(mechanics.get("reinforcement"), Mapping) else {}
    split = state.get("target_split_audit") if isinstance(state.get("target_split_audit"), Mapping) else {}
    eid22 = state.get("eid22_behavior") if isinstance(state.get("eid22_behavior"), Mapping) else {}
    background = state.get("background_identity") if isinstance(state.get("background_identity"), Mapping) else {}
    return {
        "REPLAY_MATCH_TO_4B_THROUGH_STEP506": (
            "DEMONSTRATED"
            if milestones.get("C1_REPLAY_MATCHES_4B_THROUGH_STEP506") and not state.get("replay_divergence")
            else "DIVERGED"
        ),
        "SHORT_PATH_REENTRY": "DEMONSTRATED" if milestones.get("M4_FIRST_TARGET_RELATIONAL_REENTRY_AFTER_SHORT_PATH") else "NOT_DEMONSTRATED",
        "MULTIPLE_SHORT_PATH_PASSES_ON_SAME_RELATIONAL_EID": "DEMONSTRATED" if repeated else "NOT_DEMONSTRATED",
        "RELATIONAL_SHORT_PATH_MULTIPLIER": "0.7_CONFIRMED" if short_mechanics.get("confirmed") else "NOT_CONFIRMED",
        "REINFORCEMENT_STRENGTH_RESTORATION": "CONFIRMED" if reinforcement.get("confirmed") else "NOT_CONFIRMED",
        "RELATIONAL_SCORE_CAPABLE_EARLY_COHORT": "REPLICATED" if split.get("expected_split_replicated") else "NOT_REPLICATED",
        "PHASE_DURATION_PENALTY_BLOCKED_LATE_COHORT": "REPLICATED" if split.get("expected_split_replicated") else "NOT_REPLICATED",
        "AGE500_GATE": "DEMONSTRATED" if milestones.get("M7_FIRST_TARGET_RELATIONAL_AGE_GE_500") else "NOT_DEMONSTRATED",
        "AUTHENTIC_RELATIONAL_SCORE_GE_0_7_AT_AGE_GE_500": (
            "DEMONSTRATED"
            if milestones.get("C4_FIRST_AUTHENTIC_RELATIONAL_SCORE_GE_0_7_AT_AGE_GE_500")
            else "NOT_DEMONSTRATED_THROUGH_550"
        ),
        "ORDINARY_RELATIONAL_AGE_SCORE_LONG_PATH": "DEMONSTRATED" if first_long else "NOT_DEMONSTRATED_THROUGH_550",
        "FIRST_ORDINARY_RELATIONAL_LONG_PATH_EID": (first_long or {}).get("eid") if isinstance(first_long, Mapping) else "NONE",
        "FIRST_ORDINARY_RELATIONAL_LONG_PATH_STEP": (first_long or {}).get("step") if isinstance(first_long, Mapping) else "NONE",
        "FIRST_ORDINARY_RELATIONAL_LONG_PATH_SCORE": (
            ((first_long or {}).get("diagnostic") or {}).get("candidate_score")
            if isinstance(first_long, Mapping) and isinstance((first_long or {}).get("diagnostic"), Mapping)
            else "NONE"
        ),
        "FIRST_ORDINARY_RELATIONAL_LONG_PATH_AGE": (
            ((first_long or {}).get("pre") or {}).get("age")
            if isinstance(first_long, Mapping) and isinstance((first_long or {}).get("pre"), Mapping)
            else "NONE"
        ),
        "FIRST_ORDINARY_RELATIONAL_DEEPMEMORY": "DEMONSTRATED" if first_deep else "NOT_DEMONSTRATED",
        "CANDIDATE_CAP_SURVIVOR_REACHED_AGE500": "DEMONSTRATED" if eid22.get("reached_age500") else "NOT_DEMONSTRATED",
        "CANDIDATE_CAP_SURVIVOR_LONG_PATH": "DEMONSTRATED" if eid22.get("long_path") else "NOT_DEMONSTRATED",
        "IDENTITY_ANCHOR_REEXPORT": "DEMONSTRATED" if int(background.get("identity_anchor_reexport_count", 0) or 0) > 0 else "NOT_DEMONSTRATED",
        "DEEPMEMORY_SAME_EID_DUPLICATE_RECORD_ACCUMULATION": (
            "DEMONSTRATED" if int(background.get("identity_anchor_reexport_count", 0) or 0) > 0 else "NOT_DEMONSTRATED"
        ),
        "THRESHOLD_LOWERING": "NOT_USED",
        "THRESHOLD_ENV_PRESENT": {},
        "MANUAL_AGE_MUTATION": "NOT_USED",
        "MANUAL_STEP_ADVANCEMENT": "NOT_USED",
        "DIRECT_COMPRESSION_CALL_AS_AUTHORITY": "NOT_USED",
        "PROVIDER": "NOT_INVOKED",
        "CONFIGURATION_BOUNDARY": "NON_DEFAULT_COMPRESSION_ENABLED",
        "NATURAL_PREVALENCE": "NOT_MEASURED",
        "DEEP_MEMORY_USEFULNESS": "NOT_TESTED",
        "DEEP_MEMORY_HARMFULNESS": "NOT_TESTED",
    }


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    tmp.replace(path)


def run_experiment(args: argparse.Namespace) -> int:
    started = datetime.now(timezone.utc)
    timestamp = started.strftime("%Y%m%dT%H%M%SZ")
    output_dir = REPO_ROOT / "outputs" / "experiments" / LABEL / timestamp
    result_path = output_dir / f"{LABEL}_result.json"
    data_root = Path(args.data_root).resolve() if args.data_root else short_root_for(timestamp).resolve()
    if data_root.exists():
        raise StageStop(f"Short data root already exists; refusing reuse: {data_root}")
    data_root.mkdir(parents=True, exist_ok=False)

    result: Dict[str, Any] = {
        "label": LABEL,
        "experiment": EXPERIMENT,
        "started_at_utc": started.isoformat(),
        "provider": "NOT_INVOKED",
        "trajectory": None,
        "baseline": baseline_snapshot(),
        "paths": path_preflight(data_root),
        "environment": configure_environment(data_root),
        "transport": {
            "path": "IN_PROCESS_ENDPOINT_EQUIVALENT_LIVED_USE_PATH",
            "components": [
                "real Pydantic request models",
                "real app endpoint functions",
                "Spine",
                "TormentFabric",
                "kernel",
                "MemoryGraph",
                "EventDetector",
                "CompressionScorer",
                "CompressionRouter",
                "CompressionExecutor",
                "DeepMemoryStore",
            ],
            "direct_compression_call_as_authority": "NOT_USED",
        },
        "warnings": [],
        "errors": [],
    }
    try:
        trajectory = load_trajectory()
        script = trajectory.pop("trajectory")
        result["trajectory"] = trajectory
        previous_4b_replay = load_previous_4b_replay()
        previous_4b_events_by_step = previous_4b_replay.pop("events_by_step")
        result["replay_expected_4b"] = previous_4b_replay

        random.seed(2026081142)
        try:
            import numpy as np

            np.random.seed(2026081142)
        except Exception:
            pass

        import torment_service.app as app_mod
        from examples.lived_use_chat import build_ingest_summary

        client = DirectAppClient(app_mod)
        paths = paths_for(data_root)
        nodes_tail = JsonlTail(paths["nodes"])
        compression_tail = JsonlTail(paths["compression_log"])
        deep_tail = JsonlTail(paths["deep_memories"])
        result["preflight"] = preflight(client, app_mod)
        result["deep_memory_initial"] = deep_file_state(paths)

        current_step = 0
        successful = 0
        all_target_eids: set[int] = set()
        target_births: Dict[int, Dict[str, Any]] = {}
        target_histories: Dict[int, List[Dict[str, Any]]] = {}
        compression_event_records: List[Dict[str, Any]] = []
        post_age500_summaries: List[Dict[str, Any]] = []
        compact_exchange_records: List[Dict[str, Any]] = []
        state: Dict[str, Any] = {
            "milestones": {},
            "post_age500_opportunities": [],
            "maximum_relational_score_observed": None,
            "candidate_cap_material_to_relational_survival": "NOT_ISOLATED",
            "replay_comparison": {
                "scope": "through_step_506",
                "mismatches": [],
                "status": "PENDING",
            },
        }
        identity_anchor_compression_count = 0
        identity_anchor_long_path_count = 0
        identity_anchor_reexport_count = 0
        identity_anchor_export_counts: Dict[int, int] = {}
        first_repeated_short_path: Optional[Dict[str, Any]] = None
        first_score_ge_07: Optional[Dict[str, Any]] = None
        first_target_age_500: Optional[Dict[str, Any]] = None
        first_target_long_path: Optional[Dict[str, Any]] = None
        first_target_deep: Optional[Dict[str, Any]] = None
        stop_reason = ""

        for exchange, pair in enumerate(script, 1):
            before = graph_snapshot(app_mod)
            recent_before = api_json(client, "GET", f"/index/{WORKSPACE_ID}/{AGENT_ID}/recent", params={"limit": 1})
            query_payload = {
                "workspace_id": WORKSPACE_ID,
                "agent_id": AGENT_ID,
                "query": str(pair["user"]),
                "top_k": 8,
                "domain_id": DOMAIN_ID,
                "explain": True,
                "continuity_debug": True,
            }
            query_response = api_json(client, "POST", "/agent/query", json=query_payload)
            supplied_summary = build_ingest_summary(
                USER_NAME,
                CHARACTER_NAME,
                str(pair["user"]),
                str(pair["assistant"]),
                os.environ,
            )
            requested_step = current_step + 1
            ingest_payload = {
                "workspace_id": WORKSPACE_ID,
                "agent_id": AGENT_ID,
                "text": supplied_summary,
                "step": requested_step,
                "domain_id": DOMAIN_ID,
                "scope": "private",
                "supplied_summary": supplied_summary,
            }
            ingest_response = api_json(client, "POST", "/agent/ingest", json=ingest_payload)
            appended_nodes = nodes_tail.read_new()
            new_compression_events = compression_tail.read_new()
            new_deep_records = deep_tail.read_new()
            recent_after = api_json(client, "GET", f"/index/{WORKSPACE_ID}/{AGENT_ID}/recent", params={"limit": 1})
            after = graph_snapshot(app_mod)
            after_targets = target_eids(after)
            for eid in after_targets:
                all_target_eids.add(int(eid))
                if int(eid) not in target_births:
                    target_births[int(eid)] = compact_source(int(eid), after, requested_step)

            if requested_step >= 100 and not state["milestones"].get("M1_MIN_STEP_GATE"):
                state["milestones"]["M1_MIN_STEP_GATE"] = {"exchange": exchange, "step": requested_step}

            for eid in sorted(all_target_eids):
                item = after.get(eid)
                if not isinstance(item, Mapping):
                    continue
                payload = payload_of(item)
                born = int(item.get("born_step", payload.get("created_at", 0)) or 0)
                if requested_step - born >= 500 and first_target_age_500 is None:
                    first_target_age_500 = compact_source(eid, after, requested_step)
                    state["milestones"]["M7_FIRST_TARGET_RELATIONAL_AGE_GE_500"] = {
                        "exchange": exchange,
                        "step": requested_step,
                        "source": first_target_age_500,
                    }
                if eid == 22 and requested_step - born >= 500 and not state["milestones"].get("C7_EID22_REACHES_AGE500"):
                    state["milestones"]["C7_EID22_REACHES_AGE500"] = {
                        "exchange": exchange,
                        "step": requested_step,
                        "source": compact_source(eid, after, requested_step),
                    }

            changed_eids = changed_eids_for_step(appended_nodes, requested_step)
            if new_compression_events:
                pre_event = reconstruct_pre_event_snapshot(before, appended_nodes, requested_step)
                pre_targets = sorted(set(target_eids(pre_event)) | set(all_target_eids))
                for eid in target_eids(pre_event):
                    all_target_eids.add(int(eid))
                coherence_field = load_coherence_field(data_root)
                diagnostics = diagnostic_candidates(
                    snapshot=pre_event,
                    step=requested_step,
                    coherence_field=coherence_field,
                )
                for event in new_compression_events:
                    event_record = summarize_compression_event(
                        event=event,
                        exchange=exchange,
                        step=requested_step,
                        pre_snapshot=pre_event,
                        post_snapshot=after,
                        diagnostics=diagnostics,
                        target_set=pre_targets,
                        changed_eids=changed_eids,
                    )
                    compression_event_records.append(event_record)
                    if requested_step <= REPLAY_COMPARE_THROUGH_STEP:
                        replay_mismatches = compare_replay_event(
                            actual=event_record,
                            expected_by_step=previous_4b_events_by_step,
                        )
                        if replay_mismatches:
                            state["replay_divergence"] = {
                                "exchange": exchange,
                                "step": requested_step,
                                "mismatches": replay_mismatches,
                            }
                            state["replay_comparison"]["status"] = "DIVERGED"
                            state["replay_comparison"]["mismatches"].extend(replay_mismatches)
                            result["errors"].append(state["replay_divergence"])
                            stop_reason = "REPLAY_DIVERGENCE_BEFORE_CONTROL_WINDOW"
                            break
                    elif not state["milestones"].get("C2_FIRST_POST506_AUTHENTIC_COMPRESSION_EVENT"):
                        state["milestones"]["C2_FIRST_POST506_AUTHENTIC_COMPRESSION_EVENT"] = {
                            "exchange": exchange,
                            "step": requested_step,
                            "trigger": event.get("trigger"),
                        }

                    if requested_step == REPLAY_COMPARE_THROUGH_STEP and not state.get("replay_divergence"):
                        state["replay_comparison"]["status"] = "DEMONSTRATED"
                        state["milestones"]["C1_REPLAY_MATCHES_4B_THROUGH_STEP506"] = {
                            "exchange": exchange,
                            "step": requested_step,
                            "compared_events": len(
                                [
                                    rec
                                    for rec in compression_event_records
                                    if int(rec.get("step", 0) or 0) <= REPLAY_COMPARE_THROUGH_STEP
                                ]
                            ),
                        }
                    if not state["milestones"].get("M2_FIRST_AUTHENTIC_COMPRESSION_EVENT"):
                        state["milestones"]["M2_FIRST_AUTHENTIC_COMPRESSION_EVENT"] = {
                            "exchange": exchange,
                            "step": requested_step,
                            "trigger": event.get("trigger"),
                        }

                    target_rows = event_record["target_rows"]
                    any_age500 = False
                    age500_scores: List[float] = []
                    age500_selected = 0
                    age500_outside = 0
                    age500_eligible = 0
                    age500_long_path_age_score = 0
                    for row in target_rows:
                        eid = int(row["eid"])
                        pre = row.get("pre") if isinstance(row.get("pre"), Mapping) else {}
                        post = row.get("post") if isinstance(row.get("post"), Mapping) else {}
                        diag = row.get("diagnostic") if isinstance(row.get("diagnostic"), Mapping) else {}
                        age = pre.get("age") if isinstance(pre, Mapping) else None
                        score = diag.get("candidate_score") if isinstance(diag, Mapping) else None
                        post_route = post.get("compression_route") if isinstance(post, Mapping) else None
                        prior_route = pre.get("compression_route") if isinstance(pre, Mapping) else None
                        classification = str(row.get("classification"))

                        if classification == "ELIGIBLE_BUT_OUTSIDE_CANDIDATE_CAP" and isinstance(age, int) and age < 500:
                            state["candidate_cap_material_to_relational_survival"] = "DEMONSTRATED"
                        if isinstance(age, int) and age >= 500:
                            any_age500 = True
                            if isinstance(score, (int, float)):
                                age500_scores.append(float(score))
                            if classification == "ELIGIBLE_AND_SELECTED":
                                age500_selected += 1
                                components = diag.get("components") if isinstance(diag, Mapping) else {}
                                sustained = components.get("sustained_duration") if isinstance(components, Mapping) else None
                                ceiling = analytic_ceiling_from_sustained(sustained)
                                if (
                                    isinstance(ceiling, float)
                                    and ceiling >= 0.7
                                    and not state["milestones"].get("C3_FIRST_AGE500_SCORE_CAPABLE_TARGET_SELECTED")
                                ):
                                    state["milestones"]["C3_FIRST_AGE500_SCORE_CAPABLE_TARGET_SELECTED"] = {
                                        "exchange": exchange,
                                        "step": requested_step,
                                        "eid": eid,
                                        "age": age,
                                        "score": score,
                                        "rank_before_cap": diag.get("rank_before_cap") if isinstance(diag, Mapping) else None,
                                        "analytic_ceiling": ceiling,
                                    }
                            elif classification == "ELIGIBLE_BUT_OUTSIDE_CANDIDATE_CAP":
                                age500_outside += 1
                            if classification.startswith("ELIGIBLE"):
                                age500_eligible += 1

                        if isinstance(score, (int, float)):
                            if float(score) >= 0.7 and first_score_ge_07 is None:
                                first_score_ge_07 = {
                                    "exchange": exchange,
                                    "step": requested_step,
                                    "eid": eid,
                                    "age": age,
                                    "score": float(score),
                                    "diagnostic": diag,
                                }
                                state["milestones"]["M6_FIRST_TARGET_RELATIONAL_SCORE_GE_0_7"] = first_score_ge_07
                                if isinstance(age, int) and age < 500:
                                    state["M6_BEFORE_AGE500"] = first_score_ge_07
                            if isinstance(age, int) and age >= 500 and float(score) >= 0.7:
                                state["post_age500_score_ge_0_7_observed"] = True
                                if not state["milestones"].get("M8_FIRST_TARGET_RELATIONAL_SCORE_GE_0_7_AND_AGE_GE_500"):
                                    state["milestones"]["M8_FIRST_TARGET_RELATIONAL_SCORE_GE_0_7_AND_AGE_GE_500"] = {
                                        "exchange": exchange,
                                        "step": requested_step,
                                        "eid": eid,
                                        "age": age,
                                        "score": float(score),
                                        "diagnostic": diag,
                                    }
                                if not state["milestones"].get("C4_FIRST_AUTHENTIC_RELATIONAL_SCORE_GE_0_7_AT_AGE_GE_500"):
                                    state["milestones"]["C4_FIRST_AUTHENTIC_RELATIONAL_SCORE_GE_0_7_AT_AGE_GE_500"] = {
                                        "exchange": exchange,
                                        "step": requested_step,
                                        "eid": eid,
                                        "age": age,
                                        "score": float(score),
                                        "diagnostic": diag,
                                    }

                        if prior_route == "short_path" and classification == "ELIGIBLE_AND_SELECTED":
                            if not state["milestones"].get("M4_FIRST_TARGET_RELATIONAL_REENTRY_AFTER_SHORT_PATH"):
                                state["milestones"]["M4_FIRST_TARGET_RELATIONAL_REENTRY_AFTER_SHORT_PATH"] = {
                                    "exchange": exchange,
                                    "step": requested_step,
                                    "eid": eid,
                                    "score": score,
                                    "prior_route": prior_route,
                                }

                        if row.get("mutated_by_event"):
                            hist_entry = {
                                "compression_occurrence": len(target_histories.get(eid, [])) + 1,
                                "exchange": exchange,
                                "step": requested_step,
                                "age": age,
                                "pre_strength": pre.get("strength") if isinstance(pre, Mapping) else None,
                                "post_strength": post.get("strength") if isinstance(post, Mapping) else None,
                                "score": score,
                                "retrieval_count": pre.get("retrieval_count") if isinstance(pre, Mapping) else None,
                                "reinforcement_count": pre.get("reinforcement_count") if isinstance(pre, Mapping) else None,
                                "retention_tier": pre.get("retention_tier") if isinstance(pre, Mapping) else None,
                                "post_route": post_route,
                                "diagnostic_route": diag.get("candidate_route") if isinstance(diag, Mapping) else None,
                                "components": diag.get("components") if isinstance(diag, Mapping) else None,
                            }
                            target_histories.setdefault(eid, []).append(hist_entry)
                            if post_route == "short_path":
                                if not state["milestones"].get("M3_FIRST_TARGET_RELATIONAL_SHORT_PATH"):
                                    state["milestones"]["M3_FIRST_TARGET_RELATIONAL_SHORT_PATH"] = hist_entry
                                if len([h for h in target_histories[eid] if h.get("post_route") == "short_path"]) >= 2:
                                    if not state["milestones"].get("M5_FIRST_TARGET_RELATIONAL_SECOND_SHORT_PATH"):
                                        state["milestones"]["M5_FIRST_TARGET_RELATIONAL_SECOND_SHORT_PATH"] = hist_entry
                                    if first_repeated_short_path is None:
                                        first_repeated_short_path = {
                                            "eid": eid,
                                            "history": target_histories[eid],
                                        }
                            if post_route == "long_path":
                                cause = route_cause_for_target_long_path(
                                    eid=eid,
                                    event_record=event_record,
                                    step=requested_step,
                                )
                                if cause.get("accepted"):
                                    age500_long_path_age_score += 1
                                    if first_target_long_path is None:
                                        first_target_long_path = cause
                                        state["first_ordinary_relational_long_path"] = cause
                                        state["milestones"]["M9_FIRST_ORDINARY_RELATIONAL_LONG_PATH"] = cause
                                        state["milestones"]["C5_FIRST_ORDINARY_RELATIONAL_AGE_SCORE_LONG_PATH"] = cause

                    update_record_high(state, eid=0, event_record=event_record)

                    if any_age500:
                        summary = {
                            "exchange": exchange,
                            "step": requested_step,
                            "trigger": event.get("trigger"),
                            "target_rows_age_ge_500": sum(
                                1
                                for row in target_rows
                                if isinstance((row.get("pre") or {}).get("age") if isinstance(row.get("pre"), Mapping) else None, int)
                                and (row.get("pre") or {}).get("age") >= 500
                            ),
                            "candidate_eligible": age500_eligible,
                            "selected_inside_top20": age500_selected,
                            "outside_candidate_cap": age500_outside,
                            "max_score": max(age500_scores) if age500_scores else None,
                            "score_ge_0_7_count": sum(1 for s in age500_scores if s >= 0.7),
                            "long_path_via_age_score": age500_long_path_age_score,
                        }
                        post_age500_summaries.append(summary)
                        state["post_age500_opportunities"].append(summary)

                    print(
                        f"compression exchange={exchange} step={requested_step} "
                        f"trigger={event.get('trigger')} candidates={event.get('candidates_evaluated')} "
                        f"compressed={event.get('compressed')} deep={event.get('exported_deep')} "
                        f"targets={len(pre_targets)}",
                        flush=True,
                    )

                for eid in changed_eids:
                    payload = payload_of(after.get(eid, {}))
                    if str(payload.get("type") or payload.get("mtype") or "") == "identity_anchor":
                        identity_anchor_compression_count += 1
                        if payload.get("compression_route") == "long_path" or payload.get("exported_deep"):
                            identity_anchor_long_path_count += 1
                            identity_anchor_export_counts[eid] = identity_anchor_export_counts.get(eid, 0) + 1
                            if identity_anchor_export_counts[eid] > 1:
                                identity_anchor_reexport_count += 1

            if new_deep_records:
                for rec in new_deep_records:
                    eid = int(rec.get("eid", 0) or 0)
                    if first_target_long_path and int(first_target_long_path.get("eid", -1)) == eid:
                        first_target_deep = {
                            "exchange": exchange,
                            "step": requested_step,
                            "record": rec,
                            "source": compact_source(eid, after, requested_step),
                            "source_long_path": first_target_long_path,
                            "deep_vector_state": deep_vector_state(paths),
                        }
                        state["first_ordinary_relational_deepmemory"] = first_target_deep
                        state["milestones"]["M10_FIRST_ORDINARY_RELATIONAL_DEEPMEMORY"] = first_target_deep
                        state["milestones"]["C6_FIRST_ORDINARY_RELATIONAL_DEEPMEMORY"] = first_target_deep
                        stop_reason = "FIRST_ORDINARY_RELATIONAL_DEEPMEMORY_PERSISTED"
                        break
            if first_target_long_path and first_target_deep is None and not stop_reason:
                stop_reason = "FIRST_ORDINARY_RELATIONAL_AGE_SCORE_LONG_PATH_WITHOUT_DEEPMEMORY_RECORD"
                result["errors"].append(
                    {
                        "type": "DeepMemoryPersistenceMissing",
                        "message": "AGE_SCORE long_path occurred but no matching DeepMemory record appeared in the same production event.",
                        "first_ordinary_relational_long_path": first_target_long_path,
                    }
                )
            if stop_reason:
                successful += 1
                current_step = requested_step
                break

            # Detect reinforcement of compressed rows and age survival without using it as authority.
            for row in appended_nodes:
                payload = row.get("payload") if isinstance(row.get("payload"), Mapping) else {}
                if not isinstance(payload, Mapping):
                    continue
                eid = int(row.get("eid", 0) or 0)
                if payload.get("compressed") and int(payload.get("last_reinforced", -1) or -1) == requested_step:
                    state["compressed_row_reinforcement_observed"] = True
                    if eid in all_target_eids:
                        born = int(row.get("born_step", payload.get("created_at", 0)) or 0)
                        state["reinforced_target_age_survival_observed"] = {
                            "eid": eid,
                            "born_step": born,
                            "reinforced_step": requested_step,
                            "age": requested_step - born,
                        }

            for eid in list(all_target_eids):
                payload = payload_of(after.get(eid, {}))
                if not payload:
                    continue
                if str(payload.get("memory_class", "core") or "core") == "archive":
                    state["relational_archive_migration_observed"] = {"eid": eid, "step": requested_step}
                try:
                    tier_now = derived_tier(payload)
                    if tier_now not in ("relational", "protected") and str(payload.get("type") or "") == "episode":
                        state["relational_tier_migration_observed"] = {
                            "eid": eid,
                            "step": requested_step,
                            "tier": tier_now,
                        }
                except Exception:
                    pass

            counts = graph_counts(after)
            compact_exchange_records.append(
                {
                    "exchange": exchange,
                    "requested_step": requested_step,
                    "recent_step_before": resolve_current_step(recent_before),
                    "recent_step_after": resolve_current_step(recent_after),
                    "stored": ingest_response.get("stored"),
                    "reinforced": ingest_response.get("reinforced"),
                    "eid": ingest_response.get("eid"),
                    "query_result_count": len(query_response.get("results", []))
                    if isinstance(query_response.get("results"), list)
                    else None,
                    "compression_event_count": len(new_compression_events),
                    "deep_new_count": len(new_deep_records),
                    "graph_counts": counts,
                }
            )

            if ingest_response.get("stored") is not True:
                stop_reason = "PRODUCTION_PATH_INVALIDITY_NON_STORING_INGEST"
                result["errors"].append({"exchange": exchange, "ingest_response": ingest_response})
                break

            successful += 1
            current_step = requested_step
            if exchange % PROGRESS_EVERY == 0:
                print(
                    f"progress exchange={exchange} step={requested_step} "
                    f"targets={counts['target_rows']} short={counts['short_path_source_rows']} "
                    f"long={counts['long_path_source_rows']} deep={deep_file_state(paths)['count']}",
                    flush=True,
                )

            if requested_step >= MAX_EXCHANGES:
                state["milestones"]["C8_STEP550_HARD_BOUND"] = {"exchange": exchange, "step": requested_step}
                stop_reason = "HARD_BOUND_STEP_550"
                break

        if not stop_reason:
            stop_reason = "HARD_BOUND_STEP_550"
            state["milestones"]["C8_STEP550_HARD_BOUND"] = {"exchange": successful, "step": current_step}

        final_snapshot = graph_snapshot(app_mod)
        actual_steps_through_506 = [
            int(rec.get("step", 0) or 0)
            for rec in compression_event_records
            if int(rec.get("step", 0) or 0) <= REPLAY_COMPARE_THROUGH_STEP
        ]
        expected_steps_through_506 = sorted(int(step) for step in previous_4b_events_by_step.keys())
        if current_step >= REPLAY_COMPARE_THROUGH_STEP and not state.get("replay_divergence"):
            if actual_steps_through_506 != expected_steps_through_506:
                state["replay_divergence"] = {
                    "field": "compression_event_steps_through_506",
                    "expected": expected_steps_through_506,
                    "actual": actual_steps_through_506,
                }
                state["replay_comparison"]["status"] = "DIVERGED"
                state["replay_comparison"]["mismatches"].append(state["replay_divergence"])
            else:
                state["replay_comparison"]["status"] = "DEMONSTRATED"
                state["milestones"].setdefault(
                    "C1_REPLAY_MATCHES_4B_THROUGH_STEP506",
                    {
                        "exchange": REPLAY_COMPARE_THROUGH_STEP,
                        "step": REPLAY_COMPARE_THROUGH_STEP,
                        "compared_events": len(actual_steps_through_506),
                    },
                )

        target_eid_list = sorted(all_target_eids)
        split_audit = target_split_audit(compression_event_records, target_eid_list)
        mechanics = mechanics_checks(paths=paths, target_set=target_eid_list, compression_events=compression_event_records)
        eid22 = eid22_behavior(compression_event_records, final_snapshot)
        background_identity = {
            "identity_anchor_compression_count": identity_anchor_compression_count,
            "identity_anchor_long_path_count": identity_anchor_long_path_count,
            "identity_anchor_reexport_count": identity_anchor_reexport_count,
            "identity_anchor_export_counts": identity_anchor_export_counts,
            "deep_memory_duplicate_record_count": deep_file_state(paths)["count"],
            "deep_memory_vector_row_count": (deep_vector_state(paths).get("manifest") or {}).get("total_rows")
            if isinstance(deep_vector_state(paths).get("manifest"), Mapping)
            else None,
        }
        state["target_split_audit"] = split_audit
        state["mechanics_checks"] = mechanics
        state["eid22_behavior"] = eid22
        state["background_identity"] = background_identity

        result.update(
            {
                "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                "successful_exchanges": successful,
                "stop_reason": stop_reason,
                "current_step": current_step,
                "target_cohort": {
                    "definition": {
                        "memory_class": "core",
                        "type": "episode",
                        "canon": False,
                        "retention_tier": "relational",
                        "source": "production fields plus derive_retention_tier(payload)",
                    },
                    "size": len(all_target_eids),
                    "eids": target_eid_list,
                    "births": target_births,
                    "histories": target_histories,
                    "score_capable_split": split_audit,
                },
                "compact_per_exchange": compact_exchange_records,
                "compression_events": compression_event_records,
                "compression_event_steps_triggers": [
                    {"step": rec.get("step"), "trigger": rec.get("trigger")}
                    for rec in compression_event_records
                ],
                "post506_compression_events": [
                    rec
                    for rec in compression_event_records
                    if int(rec.get("step", 0) or 0) > REPLAY_COMPARE_THROUGH_STEP
                ],
                "post506_compression_event_steps_triggers": [
                    {"step": rec.get("step"), "trigger": rec.get("trigger")}
                    for rec in compression_event_records
                    if int(rec.get("step", 0) or 0) > REPLAY_COMPARE_THROUGH_STEP
                ],
                "post_age500_compression_event_summaries": post_age500_summaries,
                "milestones": state.get("milestones", {}),
                "replay_comparison_through_step506": state.get("replay_comparison"),
                "first_repeated_short_path": first_repeated_short_path,
                "maximum_relational_score_observed": state.get("maximum_relational_score_observed"),
                "first_score_ge_0_7": first_score_ge_07,
                "first_authentic_relational_score_ge_0_7_at_age_ge_500": state.get("milestones", {}).get(
                    "C4_FIRST_AUTHENTIC_RELATIONAL_SCORE_GE_0_7_AT_AGE_GE_500"
                ),
                "first_target_age_ge_500": first_target_age_500,
                "first_ordinary_relational_long_path": first_target_long_path,
                "first_ordinary_relational_deepmemory": first_target_deep,
                "eid22_behavior": eid22,
                "background_identity": background_identity,
                "deep_memory_final": deep_file_state(paths),
                "deep_memory_vector_final": deep_vector_state(paths),
                "checkpoint_warning_status": checkpoint_state(paths, current_step),
                "mechanics_checks": mechanics,
                "candidate_cap_findings": {
                    "CANDIDATE_CAP_MATERIAL_TO_RELATIONAL_SURVIVAL": state.get(
                        "candidate_cap_material_to_relational_survival", "NOT_ISOLATED"
                    ),
                    "CANDIDATE_CAP_SURVIVOR_REACHED_AGE500": "DEMONSTRATED"
                    if eid22.get("reached_age500")
                    else "NOT_DEMONSTRATED",
                    "CANDIDATE_CAP_SURVIVOR_LONG_PATH": "DEMONSTRATED"
                    if eid22.get("long_path")
                    else "NOT_DEMONSTRATED",
                },
                "final_taxonomy": finalize_taxonomy(state, target_histories),
                "git_status_final": run_git(["status", "--short", "--branch"]),
            }
        )
        write_json(result_path, result)
        print(f"RESULT {result_path}", flush=True)
        return 0
    except Exception as exc:
        result.setdefault("errors", []).append({"type": type(exc).__name__, "message": str(exc)})
        result["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        result["stop_reason"] = "FAILED_CLOSED"
        result["git_status_final"] = run_git(["status", "--short", "--branch"])
        write_json(result_path, result)
        print(f"FAILED_CLOSED {type(exc).__name__}: {exc}", flush=True)
        print(f"RESULT {result_path}", flush=True)
        return 2


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=EXPERIMENT)
    parser.add_argument("--data-root", default="", help="Optional fresh short data root")
    args = parser.parse_args(argv)
    return run_experiment(args)


if __name__ == "__main__":
    raise SystemExit(main())
