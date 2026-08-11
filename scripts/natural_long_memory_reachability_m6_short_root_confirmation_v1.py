from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import inspect
import json
import logging
import os
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LABEL = "natural_long_memory_reachability_m6_short_root_confirmation_v1"
SUBTYPE = "BOUNDED_M6_SHORT_ROOT_CONFIRMATION"
AUTHORIZED_HEAD = "26be69c896560b85b6af870652bad96ff455c336"
EXPECTED_SUBJECT = "test(lived-use): preserve natural long-memory reachability"
REQUIRED_PYTHON = Path(r"C:\Users\Notandi\miniconda3\envs\torment\python.exe")

PREVIOUS_HARNESS_REL = Path("scripts") / "natural_long_memory_reachability_v1.py"
SCRIPT_REL = Path("scripts") / f"{LABEL}.py"
OUTPUT_REL_PREFIX = Path("outputs") / "experiments" / LABEL

SHORT_ROOT_BASE = Path(r"C:\t\n4m6")
SHORT_PATH_MAX_ALLOWED = 180

AGENT_ID = "eira_voss"
DOMAIN_ID = "personal"
USER_NAME = "Hilmir"
CHARACTER_NAME = "Eira Voss"
WORKSPACE_ID = "n4m6_t3"
TRAJECTORY_ID = "T3_MIXED_CHARACTER_CONVERSATION"
MAX_EXCHANGES = 150
PROGRESS_EVERY = 25
RNG_SEED = 2026081103

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

ENV_SUBSET_KEYS = (
    "TORMENT_PROFILE",
    "TORMENT_DATA_DIR",
    "TORMENT_TEST_CONDITION",
    "TORMENT_SQLITE_INDEX_ENABLE",
    "TORMENT_CHARACTER_ENABLE",
    "TORMENT_THINKING_ADVISORY",
    "TORMENT_SPINE_ENABLE",
    "TORMENT_IDENTITY_SENSITIVE",
    "TORMENT_COMPRESS_ENABLE",
    "TORMENT_ARCHIVE_RECALL",
    "TORMENT_LIVE_SOCIAL",
    "TORMENT_CONTEXTUAL_ABSTENTION",
    "TORMENT_SRG_ENABLE",
    "TORMENT_SRG_COGNITION",
    "TORMENT_HIVEMIND_ENABLE",
    "TORMENT_ARCHIVIST_WRITEBACK",
    "TORMENT_COGNITION_SHAPING_V2",
    "TORMENT_COGNITION_CORE_SHAPING_V1",
    "TORMENT_GEOMETRIC_MEMORY_SHAPING_V1",
    "TORMENT_GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1",
    "TORMENT_RELATIONAL_AMBIGUITY_PROMINENCE_V1",
    "TORMENT_AMBIGUITY_CONTEXT_DIVERSITY_V1",
    "TORMENT_PARTICIPATION_GUIDANCE_V1",
    "TORMENT_EMBED_PROVIDER",
    "TORMENT_EMBED_MODEL",
    "TORMENT_EMBED_DEVICE",
    "TORMENT_EMBED_STRICT",
    "TORMENT_AUTH_ENABLE",
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
    """Same-thread endpoint caller preserving request-model validation."""

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
        rows: List[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            handle.seek(self.position)
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
            self.position = handle.tell()
        return rows


class CapturingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.records: List[Dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()
        except Exception:
            message = str(record.msg)
        self.records.append(
            {
                "level": record.levelname,
                "logger": record.name,
                "message": message,
            }
        )


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(args: List[str], *, cwd: Path) -> Dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "args": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def git_snapshot(root: Path) -> Dict[str, Any]:
    return {
        "status_short_branch": run_cmd(["git", "status", "--short", "--branch"], cwd=root),
        "status_porcelain": run_cmd(["git", "status", "--porcelain=v1"], cwd=root),
        "head": run_cmd(["git", "rev-parse", "HEAD"], cwd=root),
        "origin_main": run_cmd(["git", "rev-parse", "origin/main"], cwd=root),
        "log_1_oneline": run_cmd(["git", "log", "-1", "--oneline"], cwd=root),
    }


def _status_path(line: str) -> str:
    path = line[3:] if len(line) > 3 else ""
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.strip().strip('"').replace("\\", "/")


def _allowed_dirty_path(path: str) -> bool:
    script = str(SCRIPT_REL).replace("\\", "/")
    output_prefix = str(OUTPUT_REL_PREFIX).replace("\\", "/")
    return path == script or path == "outputs/" or path.startswith(output_prefix + "/")


def ensure_baseline(root: Path) -> Dict[str, Any]:
    snap = git_snapshot(root)
    if snap["head"]["returncode"] != 0 or snap["head"]["stdout"] != AUTHORIZED_HEAD:
        raise StageStop(f"HEAD mismatch: {snap['head']}")
    if snap["origin_main"]["returncode"] != 0 or snap["origin_main"]["stdout"] != AUTHORIZED_HEAD:
        raise StageStop(f"origin/main mismatch: {snap['origin_main']}")
    if EXPECTED_SUBJECT not in str(snap["log_1_oneline"]["stdout"]):
        raise StageStop(f"Unexpected subject: {snap['log_1_oneline']}")

    disallowed: List[str] = []
    porcelain = str(snap["status_porcelain"]["stdout"] or "")
    for line in porcelain.splitlines():
        if not line.strip():
            continue
        path = _status_path(line)
        if not _allowed_dirty_path(path):
            disallowed.append(line)
    if disallowed:
        raise StageStop(
            "Production or unrelated files are modified; refusing to run: "
            + json.dumps(disallowed, ensure_ascii=False)
        )
    return snap


def ensure_required_python(*, worker: bool = False) -> Dict[str, Any]:
    actual = Path(sys.executable).resolve()
    required = REQUIRED_PYTHON.resolve()
    try:
        ok = actual.samefile(required)
    except Exception:
        ok = str(actual).lower() == str(required).lower()
    if not ok:
        role = "worker" if worker else "harness"
        raise StageStop(f"Run the {role} with {required}; current interpreter is {actual}")
    return {"required": str(required), "actual": str(actual)}


def load_previous_harness() -> Any:
    path = (REPO_ROOT / PREVIOUS_HARNESS_REL).resolve()
    spec = importlib.util.spec_from_file_location("natural_long_memory_reachability_v1_prev", path)
    if spec is None or spec.loader is None:
        raise StageStop(f"Could not load previous harness spec from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[str(spec.name)] = module
    spec.loader.exec_module(module)
    return module


def api_json(client: Any, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
    response = getattr(client, method.lower())(path, **kwargs)
    if response.status_code >= 400:
        raise StageStop(f"{method} {path} returned {response.status_code}: {response.text[:500]}")
    data = response.json()
    if not isinstance(data, dict):
        raise StageStop(f"{method} {path} returned non-object JSON: {data!r}")
    return data


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
            raise StageStop(f"{name} embedder reports degraded state: {observed}")
    if bool(health.get("embedder_degraded", False)):
        raise StageStop(f"Health reports degraded embedder: {health}")
    requested = health.get("requested_embedder") or {}
    if not isinstance(requested, Mapping) or requested.get("strict") is not True:
        raise StageStop(f"Requested embedder strict mode not active: {requested}")
    return observations


def configure_worker_env(base_env: Mapping[str, str], *, data_root: Path) -> Tuple[Dict[str, str], Dict[str, Any]]:
    env = dict(base_env)
    removed_threshold_overrides = {key: env.pop(key) for key in THRESHOLD_ENV_VARS if key in env}
    removed_external_model_flags = {}
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"):
        if key in env:
            removed_external_model_flags[key] = env.pop(key)
    env.update(
        {
            "PYTHONIOENCODING": "utf-8",
            "TOKENIZERS_PARALLELISM": "false",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TORMENT_PROFILE": "companion",
            "TORMENT_DATA_DIR": str(data_root.resolve()),
            "TORMENT_EXPECTED_DATA_DIR": str(data_root.resolve()),
            "TORMENT_TEST_CONDITION": LABEL,
            "TORMENT_SERVER_LAUNCHER_PATH": str(Path(__file__).resolve()),
            "TORMENT_SQLITE_INDEX_ENABLE": "1",
            "TORMENT_CHARACTER_ENABLE": "1",
            "TORMENT_THINKING_ADVISORY": "1",
            "TORMENT_SPINE_ENABLE": "1",
            "TORMENT_IDENTITY_SENSITIVE": "1",
            "TORMENT_COMPRESS_ENABLE": "1",
            "TORMENT_ARCHIVE_RECALL": "0",
            "TORMENT_LIVE_SOCIAL": "0",
            "TORMENT_CONTEXTUAL_ABSTENTION": "0",
            "TORMENT_SRG_ENABLE": "0",
            "TORMENT_SRG_COGNITION": "0",
            "TORMENT_HIVEMIND_ENABLE": "0",
            "TORMENT_ARCHIVIST_WRITEBACK": "0",
            "TORMENT_COGNITION_SHAPING_V2": "0",
            "TORMENT_COGNITION_CORE_SHAPING_V1": "0",
            "TORMENT_GEOMETRIC_MEMORY_SHAPING_V1": "0",
            "TORMENT_GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1": "0",
            "TORMENT_RELATIONAL_AMBIGUITY_PROMINENCE_V1": "0",
            "TORMENT_AMBIGUITY_CONTEXT_DIVERSITY_V1": "0",
            "TORMENT_PARTICIPATION_GUIDANCE_V1": "0",
            "TORMENT_EMBED_PROVIDER": EXPECTED_EMBEDDER["provider"],
            "TORMENT_EMBED_MODEL": EXPECTED_EMBEDDER["model"],
            "TORMENT_EMBED_DEVICE": "cpu",
            "TORMENT_EMBED_STRICT": "1",
            "TORMENT_AUTH_ENABLE": "0",
        }
    )
    return env, {
        "removed_threshold_env_overrides": removed_threshold_overrides,
        "removed_external_model_flags": removed_external_model_flags,
        "effective_env_subset": {key: env.get(key, "") for key in ENV_SUBSET_KEYS},
    }


def path_inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def agent_paths(data_root: Path, workspace_id: str = WORKSPACE_ID) -> Dict[str, Path]:
    agent_root = data_root / "workspaces" / workspace_id / "agents" / AGENT_ID
    private_dir = agent_root / "private"
    deep_dir = agent_root / "deep_memory"
    return {
        "agent_root": agent_root,
        "private_dir": private_dir,
        "private_embeddings_dir": private_dir / "embeddings",
        "nodes": private_dir / "nodes.jsonl",
        "compression_log": private_dir / "compression_log.jsonl",
        "deep_dir": deep_dir,
        "deep_memories": deep_dir / "memories.jsonl",
        "deep_embeddings_dir": deep_dir / "embeddings",
    }


def predicted_deep_embedding_paths(data_root: Path, workspace_id: str = WORKSPACE_ID) -> Dict[str, Any]:
    emb_dir = agent_paths(data_root, workspace_id)["deep_embeddings_dir"]
    paths = {
        "embeddings_manifest_json": emb_dir / "manifest.json",
        "embeddings_manifest_json_tmp": emb_dir / "manifest.json.tmp",
        "embeddings_shard_000000_npy": emb_dir / "shard_000000.npy",
        "embeddings_shard_000000_map_jsonl": emb_dir / "shard_000000.map.jsonl",
    }
    items = {
        name: {"path": str(path.resolve()), "length": len(str(path.resolve()))}
        for name, path in paths.items()
    }
    max_item = max(items.items(), key=lambda kv: int(kv[1]["length"]))
    return {
        "workspace_id": workspace_id,
        "agent_id": AGENT_ID,
        "paths": items,
        "max_path_name": max_item[0],
        "max_path_length": int(max_item[1]["length"]),
        "required_max_path_length": SHORT_PATH_MAX_ALLOWED,
    }


def validate_short_data_root(data_root: Path, output_dir: Path) -> Dict[str, Any]:
    resolved = data_root.resolve()
    output_resolved = output_dir.resolve()
    repo_resolved = REPO_ROOT.resolve()
    if path_inside(resolved, repo_resolved):
        raise StageStop(f"Short data root is inside the repository: {resolved}")
    if path_inside(resolved, output_resolved):
        raise StageStop(f"Short data root is inside the artifact output dir: {resolved}")
    if resolved.exists() and any(resolved.iterdir()):
        raise StageStop(f"Short data root is not empty; refusing to reuse state: {resolved}")
    predicted = predicted_deep_embedding_paths(resolved)
    if int(predicted["max_path_length"]) > SHORT_PATH_MAX_ALLOWED:
        raise StageStop(f"Predicted deep embedding path is too long: {predicted}")
    resolved.mkdir(parents=True, exist_ok=True)
    return {
        "short_external_data_root": str(resolved),
        "root_length": len(str(resolved)),
        "repo_root": str(repo_resolved),
        "artifact_output_dir": str(output_resolved),
        "outside_repo": not path_inside(resolved, repo_resolved),
        "outside_artifact_output": not path_inside(resolved, output_resolved),
        "was_empty_before_run": True,
        "predicted_deep_embedding_paths": predicted,
        "legacy_windows_limit_reference": {
            "usable_traditional_max_path": 259,
            "experiment_4_largest_success": 257,
            "experiment_4_smallest_failure": 262,
        },
    }


def generate_preregistered_trajectory(previous_harness: Any) -> Dict[str, Any]:
    return {
        "label": LABEL,
        "direct_sequel_to": "NATURAL_LONG_MEMORY_REACHABILITY_V1",
        "trajectory_id": TRAJECTORY_ID,
        "max_exchanges": MAX_EXCHANGES,
        "rng_seed_reference": RNG_SEED,
        "generation": {
            "source_harness": str((REPO_ROOT / PREVIOUS_HARNESS_REL).resolve()),
            "function": "generate_t3_pair(index)",
            "rule": "deterministic mixed companion-style ten-pattern cycle from Experiment #4",
            "adaptive_changes": "NONE",
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "trajectory": [previous_harness.generate_t3_pair(i) for i in range(MAX_EXCHANGES)],
    }


def load_preregistered_trajectory(path: Path) -> List[Dict[str, Any]]:
    payload = read_json(path)
    items = payload.get("trajectory")
    if not isinstance(items, list) or len(items) < MAX_EXCHANGES:
        raise StageStop(f"Preregistered trajectory invalid: {path}")
    return [dict(row) for row in items[:MAX_EXCHANGES]]


def resolve_resumed_step_from_recent(response: Mapping[str, Any]) -> int:
    if response.get("ok") is not True:
        raise StageStop(f"Recent index response is not ok=true: {response}")
    results = response.get("results")
    if not isinstance(results, list):
        raise StageStop(f"Recent index response missing results list: {response}")
    if not results:
        return 0
    first = results[0]
    if not isinstance(first, Mapping):
        raise StageStop(f"Recent index first row malformed: {first!r}")
    step = first.get("step")
    if not isinstance(step, int) or step < 0:
        raise StageStop(f"Recent index first row invalid step: {first!r}")
    return int(step)


def top_recent_step(response: Mapping[str, Any]) -> Optional[int]:
    results = response.get("results")
    if not isinstance(results, list) or not results:
        return None
    first = results[0]
    if not isinstance(first, Mapping):
        return None
    try:
        return int(first.get("step"))
    except Exception:
        return None


def preflight(client: Any, app_mod: Any, workspace_id: str) -> Dict[str, Any]:
    health = api_json(client, "GET", "/health")
    embedder_observations = validate_embedder(health, api_json(client, "GET", "/embedder/check"))
    config = api_json(client, "GET", "/config")
    workspace = api_json(client, "POST", "/workspace/create", json={"workspace_id": workspace_id})
    agent = api_json(
        client,
        "POST",
        "/agent/create",
        json={
            "workspace_id": workspace_id,
            "agent_id": AGENT_ID,
            "seed": {
                "seed_id": "eira_voss_lived_use_v1",
                "character_name": CHARACTER_NAME,
                "seed_text": "Focused lived-use experiment identity seed for Eira Voss.",
                "coupling_mode": "read_only",
            },
        },
    )
    recent = api_json(client, "GET", f"/index/{workspace_id}/{AGENT_ID}/recent", params={"limit": 1})
    current_step = resolve_resumed_step_from_recent(recent)
    thresholds = threshold_snapshot(app_mod)
    metrics = api_json(client, "GET", "/debug/metrics", params={"workspace_id": workspace_id, "agent_id": AGENT_ID})
    compression_status = api_json(
        client,
        "GET",
        f"/workspace/{workspace_id}/compress/status",
        params={"agent_id": AGENT_ID},
    )
    return {
        "health": health,
        "embedder_observations": embedder_observations,
        "config": config,
        "workspace_create": workspace,
        "agent_create": agent,
        "recent_index": recent,
        "resumed_current_step": current_step,
        "threshold_snapshot": thresholds,
        "debug_metrics": metrics,
        "compression_status": compression_status,
    }


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
        "TORMENT_MAX_PRIVATE_MEMORIES": 10000,
        "TORMENT_REINFORCE_SIM_THRESHOLD": 0.92,
        "TORMENT_COMPRESS_DEEP_THRESHOLD": 0.7,
        "TORMENT_COMPRESS_AGE_THRESHOLD": 500,
        "TORMENT_COMPRESS_STEP_INTERVAL": 200,
        "TORMENT_COMPRESS_FALLBACK_COOLDOWN": 50,
        "TORMENT_COMPRESS_PERIODIC_FLOOR": 0.4,
        "TORMENT_COMPRESS_COUNT_THRESHOLD": 400,
    }
    observed = {
        "TORMENT_COMPRESS_MIN_STEP": snap["fabric"]["TORMENT_COMPRESS_MIN_STEP"],
        "TORMENT_COMPRESS_MIN_AGE": snap["compression_module"]["TORMENT_COMPRESS_MIN_AGE"],
        "TORMENT_MAX_PRIVATE_MEMORIES": snap["compression_module"]["TORMENT_MAX_PRIVATE_MEMORIES"],
        "TORMENT_REINFORCE_SIM_THRESHOLD": snap["reinforcement"]["TORMENT_REINFORCE_SIM_THRESHOLD"],
        "TORMENT_COMPRESS_DEEP_THRESHOLD": snap["compression_module"]["TORMENT_COMPRESS_DEEP_THRESHOLD"],
        "TORMENT_COMPRESS_AGE_THRESHOLD": snap["compression_module"]["TORMENT_COMPRESS_AGE_THRESHOLD"],
        "TORMENT_COMPRESS_STEP_INTERVAL": snap["compression_module"]["TORMENT_COMPRESS_STEP_INTERVAL"],
        "TORMENT_COMPRESS_FALLBACK_COOLDOWN": snap["compression_module"]["TORMENT_COMPRESS_FALLBACK_COOLDOWN"],
        "TORMENT_COMPRESS_PERIODIC_FLOOR": snap["compression_module"]["TORMENT_COMPRESS_PERIODIC_FLOOR"],
        "TORMENT_COMPRESS_COUNT_THRESHOLD": snap["compression_module"]["TORMENT_COMPRESS_COUNT_THRESHOLD"],
    }
    mismatches = {
        key: {"expected": expected[key], "observed": observed[key]}
        for key in expected
        if observed[key] != expected[key]
    }
    if mismatches:
        raise StageStop(f"Compression/reinforcement threshold mismatch: {mismatches}")
    snap["validated_defaults"] = expected
    return snap


def graph_snapshot(app_mod: Any, workspace_id: str) -> Dict[int, Dict[str, Any]]:
    fabric = app_mod.fabric
    ak = fabric._agent_key(workspace_id, AGENT_ID)
    graph = fabric.private_graphs.get(ak)
    if graph is None:
        return {}
    out: Dict[int, Dict[str, Any]] = {}
    for eid, ent in graph.entities.items():
        payload = dict(ent.payload or {})
        out[int(eid)] = {
            "eid": int(eid),
            "born_step": int(getattr(ent, "born_step", 0) or 0),
            "payload": payload,
        }
    return out


def graph_counts(snapshot: Mapping[int, Mapping[str, Any]]) -> Dict[str, Any]:
    compressed = 0
    short_path = 0
    long_path = 0
    exported = 0
    reinforcement_total = 0
    for item in snapshot.values():
        payload = item.get("payload") if isinstance(item, Mapping) else {}
        if not isinstance(payload, Mapping):
            continue
        if payload.get("compressed"):
            compressed += 1
        if payload.get("compression_route") == "short_path":
            short_path += 1
        if payload.get("compression_route") == "long_path":
            long_path += 1
        if payload.get("exported_deep"):
            exported += 1
        reinforcement_total += int(payload.get("reinforcement_count", 0) or 0)
    return {
        "source_rows": len(snapshot),
        "compressed_source_rows": compressed,
        "short_path_source_rows": short_path,
        "long_path_source_rows": long_path,
        "exported_deep_source_rows": exported,
        "reinforcement_total": reinforcement_total,
    }


def kernel_step(app_mod: Any, workspace_id: str) -> Optional[int]:
    fabric = app_mod.fabric
    ak = fabric._agent_key(workspace_id, AGENT_ID)
    state = fabric.agent_states.get(ak)
    if state is None:
        return None
    try:
        return int(getattr(state, "step", 0) or 0)
    except Exception:
        return None


def changed_compression_sources(
    before: Mapping[int, Mapping[str, Any]],
    after: Mapping[int, Mapping[str, Any]],
) -> Dict[str, List[int]]:
    newly_short: List[int] = []
    newly_long: List[int] = []
    changed: List[int] = []
    for eid, item_after in after.items():
        payload_after = item_after.get("payload") if isinstance(item_after, Mapping) else {}
        if not isinstance(payload_after, Mapping):
            continue
        item_before = before.get(eid, {})
        payload_before = item_before.get("payload") if isinstance(item_before, Mapping) else {}
        if not isinstance(payload_before, Mapping):
            payload_before = {}
        route_after = payload_after.get("compression_route")
        route_before = payload_before.get("compression_route")
        compressed_now = bool(payload_after.get("compressed", False))
        compressed_before = bool(payload_before.get("compressed", False))
        exported_now = bool(payload_after.get("exported_deep", False))
        exported_before = bool(payload_before.get("exported_deep", False))
        if (compressed_now and not compressed_before) or (exported_now and not exported_before) or (
            route_after and route_after != route_before
        ):
            changed.append(int(eid))
        if route_after == "short_path" and route_before != "short_path":
            newly_short.append(int(eid))
        if (route_after == "long_path" and route_before != "long_path") or (
            exported_now and not exported_before
        ):
            newly_long.append(int(eid))
    return {
        "newly_changed": sorted(set(changed)),
        "newly_short_path": sorted(set(newly_short)),
        "newly_long_path": sorted(set(newly_long)),
    }


def infer_outcome(
    ingest: Mapping[str, Any],
    before: Mapping[int, Mapping[str, Any]],
    after: Mapping[int, Mapping[str, Any]],
) -> str:
    if ingest.get("reinforced") is True:
        return "REINFORCEMENT_OF_EXISTING_ROW"
    if ingest.get("stored") is True:
        eid = ingest.get("eid")
        try:
            eid_int = int(eid)
        except Exception:
            return "STORED_WITHOUT_PARSEABLE_EID"
        if eid_int not in before and eid_int in after:
            return "NEW_SOURCE_ROW"
        return "STORED_EXISTING_ROW_WITHOUT_REINFORCED_FLAG"
    if ingest.get("stored") is False and ingest.get("reinforced") is False:
        return "NOT_STORED"
    return "UNKNOWN_PRODUCTION_OUTCOME"


def verify_persisted_exchange(
    *,
    outcome: str,
    eid: int,
    requested_step: int,
    appended_nodes: List[Mapping[str, Any]],
) -> Dict[str, Any]:
    matching = []
    for row in appended_nodes:
        try:
            row_eid = int(row.get("eid", -1))
        except Exception:
            continue
        if row_eid != int(eid):
            continue
        payload = row.get("payload") or {}
        if isinstance(payload, Mapping):
            matching.append(payload)
    proof = {
        "matched_appended_rows": len(matching),
        "created_at_requested_step": False,
        "last_reinforced_requested_step": False,
        "accepted": False,
    }
    for payload in matching:
        try:
            proof["created_at_requested_step"] = proof["created_at_requested_step"] or (
                int(payload.get("created_at", -1)) == int(requested_step)
            )
        except Exception:
            pass
        try:
            proof["last_reinforced_requested_step"] = proof["last_reinforced_requested_step"] or (
                int(payload.get("last_reinforced", -1)) == int(requested_step)
            )
        except Exception:
            pass
    if outcome == "NEW_SOURCE_ROW":
        proof["accepted"] = bool(proof["created_at_requested_step"])
    elif outcome == "REINFORCEMENT_OF_EXISTING_ROW":
        proof["accepted"] = bool(proof["last_reinforced_requested_step"])
    return proof


def source_detail(
    *,
    eid: int,
    before: Mapping[int, Mapping[str, Any]],
    after: Mapping[int, Mapping[str, Any]],
    current_step: int,
) -> Dict[str, Any]:
    item_after = after.get(int(eid), {})
    item_before = before.get(int(eid), {})
    payload_after = item_after.get("payload") if isinstance(item_after, Mapping) else {}
    payload_before = item_before.get("payload") if isinstance(item_before, Mapping) else {}
    if not isinstance(payload_after, Mapping):
        payload_after = {}
    if not isinstance(payload_before, Mapping):
        payload_before = {}
    born_step = int(item_after.get("born_step", payload_after.get("created_at", 0)) or 0)
    try:
        from torment_service.compression import derive_retention_tier

        retention_tier = derive_retention_tier(dict(payload_after))
    except Exception as exc:
        retention_tier = f"UNAVAILABLE: {exc}"
    return {
        "eid": int(eid),
        "born_step": born_step,
        "current_step": int(current_step),
        "age": int(current_step) - born_step,
        "summary_length": len(str(payload_after.get("summary", "") or "")),
        "summary": str(payload_after.get("summary", "") or "")[:1200],
        "memory_class": payload_after.get("memory_class"),
        "type": payload_after.get("type"),
        "retention_tier": retention_tier,
        "strength_before": payload_before.get("strength"),
        "strength_after": payload_after.get("strength"),
        "half_life": payload_after.get("half_life"),
        "reinforcement_count": int(payload_after.get("reinforcement_count", 0) or 0),
        "compression_score": payload_after.get("compression_score"),
        "compression_route": payload_after.get("compression_route"),
        "compressed": bool(payload_after.get("compressed", False)),
        "compressed_step": payload_after.get("compressed_step"),
        "exported_deep": bool(payload_after.get("exported_deep", False)),
        "exported_step": payload_after.get("exported_step"),
        "embedding_ref": payload_after.get("embedding_ref"),
    }


def update_milestones(
    milestones: Dict[str, Any],
    *,
    exchange: int,
    step: int,
    compression_changes: Mapping[str, List[int]],
    deep_new_records: List[Mapping[str, Any]],
    m6: Optional[Mapping[str, Any]] = None,
) -> None:
    if step >= 100 and not milestones.get("M1_MIN_STEP_GATE_CROSSED"):
        milestones["M1_MIN_STEP_GATE_CROSSED"] = {"exchange": exchange, "step": step}
    if compression_changes.get("newly_changed") and not milestones.get("M2_FIRST_COMPRESSION_EFFECT"):
        milestones["M2_FIRST_COMPRESSION_EFFECT"] = {
            "exchange": exchange,
            "step": step,
            "eids": compression_changes.get("newly_changed"),
        }
    if compression_changes.get("newly_short_path") and not milestones.get("M3_FIRST_SHORT_PATH"):
        milestones["M3_FIRST_SHORT_PATH"] = {
            "exchange": exchange,
            "step": step,
            "eids": compression_changes.get("newly_short_path"),
        }
    if compression_changes.get("newly_long_path") and not milestones.get("M4_FIRST_LONG_PATH"):
        milestones["M4_FIRST_LONG_PATH"] = {
            "exchange": exchange,
            "step": step,
            "eids": compression_changes.get("newly_long_path"),
        }
    if deep_new_records and not milestones.get("M5_FIRST_DEEP_TEXT_RECORD"):
        milestones["M5_FIRST_DEEP_TEXT_RECORD"] = {
            "exchange": exchange,
            "step": step,
            "eids": [int(row.get("eid", 0) or 0) for row in deep_new_records],
            "count": len(deep_new_records),
        }
    if m6 and m6.get("m6_success") and not milestones.get("M6_FIRST_VECTOR_INDEXED_RETRIEVABLE_DEEP_MEMORY"):
        milestones["M6_FIRST_VECTOR_INDEXED_RETRIEVABLE_DEEP_MEMORY"] = {
            "exchange": exchange,
            "step": step,
            "eid": m6.get("eid"),
        }


def compact_file_state(path: Path, *, json_file: bool = False, jsonl_file: bool = False) -> Dict[str, Any]:
    resolved = path.resolve()
    out: Dict[str, Any] = {
        "path": str(resolved),
        "length": len(str(resolved)),
        "exists": resolved.exists(),
        "is_file": resolved.is_file(),
        "size_bytes": resolved.stat().st_size if resolved.exists() else None,
        "readable": False,
    }
    if not resolved.exists() or not resolved.is_file():
        return out
    try:
        if json_file:
            with resolved.open("r", encoding="utf-8") as handle:
                out["json"] = json.load(handle)
        elif jsonl_file:
            out["jsonl_rows"] = read_jsonl(resolved)
        else:
            with resolved.open("rb") as handle:
                handle.read(1)
        out["readable"] = True
    except Exception as exc:
        out["read_error"] = str(exc)
    return out


def deep_storage_state(paths: Mapping[str, Path], embedding_ref: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    emb_dir = paths["deep_embeddings_dir"]
    shard_idx = int((embedding_ref or {}).get("shard", 0) or 0)
    state = {
        "deep_dir": str(paths["deep_dir"].resolve()),
        "deep_dir_exists": paths["deep_dir"].exists(),
        "deep_memories": compact_file_state(paths["deep_memories"], jsonl_file=True),
        "embeddings_dir": str(emb_dir.resolve()),
        "embeddings_dir_exists": emb_dir.exists(),
        "manifest_json": compact_file_state(emb_dir / "manifest.json", json_file=True),
        "manifest_json_tmp": compact_file_state(emb_dir / "manifest.json.tmp", json_file=True),
        "shard_000000_npy": compact_file_state(emb_dir / "shard_000000.npy"),
        "shard_000000_map_jsonl": compact_file_state(emb_dir / "shard_000000.map.jsonl", jsonl_file=True),
    }
    if shard_idx != 0:
        state["referenced_shard_npy"] = compact_file_state(emb_dir / f"shard_{shard_idx:06d}.npy")
        state["referenced_shard_map_jsonl"] = compact_file_state(
            emb_dir / f"shard_{shard_idx:06d}.map.jsonl",
            jsonl_file=True,
        )
    return state


def vector_digest(vec: Any) -> Optional[Dict[str, Any]]:
    if vec is None:
        return None
    import numpy as np

    arr = np.asarray(vec, dtype=np.float32).reshape(-1)
    return {
        "dim": int(arr.shape[0]),
        "sha256_float32": hashlib.sha256(arr.tobytes()).hexdigest(),
        "norm": float(np.linalg.norm(arr)),
    }


def source_vector_observation(app_mod: Any, workspace_id: str, eid: int) -> Tuple[Dict[str, Any], Any]:
    fabric = app_mod.fabric
    ak = fabric._agent_key(workspace_id, AGENT_ID)
    graph = fabric.private_graphs.get(ak)
    if graph is None:
        return {"eid": int(eid), "present": False, "reason": "no private graph"}, None
    ent = graph.entities.get(int(eid))
    if ent is None:
        return {"eid": int(eid), "present": False, "reason": "source eid absent from graph"}, None
    payload = dict(ent.payload or {})
    try:
        from torment_service.embedding_store import load_embedding

        vec = load_embedding(int(eid), payload, graph._shard_reader, graph.data_dir)
    except Exception as exc:
        return {
            "eid": int(eid),
            "present": True,
            "embedding_ref": payload.get("embedding_ref"),
            "load_error": str(exc),
        }, None
    return {
        "eid": int(eid),
        "present": True,
        "born_step": int(getattr(ent, "born_step", 0) or 0),
        "embedding_ref": payload.get("embedding_ref"),
        "summary": str(payload.get("summary", "") or "")[:1200],
        "summary_length": len(str(payload.get("summary", "") or "")),
        "vector": vector_digest(vec),
    }, vec


def measure_m6(
    *,
    app_mod: Any,
    data_root: Path,
    paths: Mapping[str, Path],
    deep_record: Mapping[str, Any],
    workspace_id: str,
) -> Dict[str, Any]:
    import numpy as np

    from torment_service.deep_memory import DeepMemoryStore

    eid = int(deep_record.get("eid", 0) or 0)
    embedding_ref = deep_record.get("embedding_ref")
    pre_fresh_file_state = deep_storage_state(
        paths,
        embedding_ref if isinstance(embedding_ref, Mapping) else None,
    )
    source_obs, source_vec = source_vector_observation(app_mod, workspace_id, eid)

    default_query_threshold = inspect.signature(DeepMemoryStore.query).parameters["min_similarity"].default
    measurement: Dict[str, Any] = {
        "eid": eid,
        "m6_definition": {
            "A_textual_record_exists": False,
            "B_embedding_ref_non_null": False,
            "C_referenced_files_exist_and_readable": False,
            "D_fresh_matrix_non_empty_and_contains_eid": False,
            "E_fresh_query_returns_eid_above_production_threshold": False,
        },
        "production_query_threshold": default_query_threshold,
        "deep_record": dict(deep_record),
        "deep_summary": str(deep_record.get("summary", "") or ""),
        "deep_summary_length": len(str(deep_record.get("summary", "") or "")),
        "embedding_ref": embedding_ref,
        "source_vector": source_obs,
        "pre_fresh_store_file_state": pre_fresh_file_state,
    }

    matching_text_records = [row for row in read_jsonl(paths["deep_memories"]) if int(row.get("eid", 0) or 0) == eid]
    measurement["matching_text_record_count"] = len(matching_text_records)
    measurement["m6_definition"]["A_textual_record_exists"] = bool(matching_text_records)
    measurement["m6_definition"]["B_embedding_ref_non_null"] = isinstance(embedding_ref, Mapping)

    referenced_ok = False
    deep_vec = None
    fresh_store_details: Dict[str, Any] = {}
    query_hits: List[Any] = []
    store = DeepMemoryStore(paths["deep_dir"].resolve(), trusted_root=str(data_root.resolve()))
    try:
        store._ensure_loaded()
        recalled = store.recall(eid)
        fresh_store_details["recalled_record"] = recalled.to_dict() if recalled is not None else None

        if isinstance(embedding_ref, Mapping):
            shard_idx = int(embedding_ref.get("shard", 0) or 0)
            reader = getattr(store, "_shard_reader", None)
            if reader is not None:
                try:
                    deep_vec = reader.load_one(dict(embedding_ref))
                    map_entries = reader._load_map(shard_idx)
                    fresh_store_details["production_reader_map_entry_count"] = len(map_entries)
                    fresh_store_details["production_reader_map_contains_eid_row"] = any(
                        int(entry.get("eid", -1)) == eid
                        and int(entry.get("row", -1)) == int(embedding_ref.get("row", -2))
                        for entry in map_entries
                    )
                except Exception as exc:
                    fresh_store_details["production_reader_error"] = str(exc)
            file_state = pre_fresh_file_state
            map_state = file_state.get("shard_000000_map_jsonl", {})
            npy_state = file_state.get("shard_000000_npy", {})
            manifest_state = file_state.get("manifest_json", {})
            if shard_idx != 0:
                map_state = file_state.get("referenced_shard_map_jsonl", map_state)
                npy_state = file_state.get("referenced_shard_npy", npy_state)
            referenced_ok = bool(
                manifest_state.get("exists")
                and manifest_state.get("readable")
                and npy_state.get("exists")
                and npy_state.get("readable")
                and map_state.get("exists")
                and map_state.get("readable")
                and deep_vec is not None
            )

        store._build_emb_matrix()
        emb_mat = getattr(store, "_emb_mat", None)
        emb_eids = list(getattr(store, "_emb_eid_list", []) or [])
        fresh_store_details["embedding_matrix_shape"] = (
            list(emb_mat.shape) if emb_mat is not None else None
        )
        fresh_store_details["embedding_eid_list"] = [int(x) for x in emb_eids]
        matrix_ok = bool(emb_mat is not None and emb_mat.shape[0] > 0 and eid in emb_eids)

        score_by_eid: Dict[str, float] = {}
        if source_vec is not None and emb_mat is not None and emb_mat.shape[0] > 0:
            qv = np.asarray(source_vec, dtype=np.float32).reshape(-1)
            if qv.shape[0] != emb_mat.shape[1]:
                if qv.shape[0] < emb_mat.shape[1]:
                    qv = np.pad(qv, (0, emb_mat.shape[1] - qv.shape[0]))
                else:
                    qv = qv[: emb_mat.shape[1]]
            qv = qv / float(np.linalg.norm(qv) + 1e-12)
            scores = emb_mat @ qv
            score_by_eid = {str(int(deid)): float(scores[i]) for i, deid in enumerate(emb_eids)}
            query_hits = store.query(np.asarray(source_vec, dtype=np.float32).reshape(-1), top_k=5)
        fresh_store_details["similarity_by_eid_for_source_vector"] = score_by_eid
        fresh_store_details["query_hits"] = [hit.to_dict() for hit in query_hits]
        query_returned_eid = any(int(hit.eid) == eid for hit in query_hits)
        score_for_eid = score_by_eid.get(str(eid))
        above_threshold = score_for_eid is not None and score_for_eid >= float(default_query_threshold)

        measurement["m6_definition"]["C_referenced_files_exist_and_readable"] = referenced_ok
        measurement["m6_definition"]["D_fresh_matrix_non_empty_and_contains_eid"] = matrix_ok
        measurement["m6_definition"]["E_fresh_query_returns_eid_above_production_threshold"] = bool(
            query_returned_eid and above_threshold
        )
        measurement["fresh_store"] = fresh_store_details
    finally:
        store.close()

    measurement["deep_loaded_vector"] = vector_digest(deep_vec)
    if source_vec is not None and deep_vec is not None:
        source_arr = np.asarray(source_vec, dtype=np.float32).reshape(-1)
        deep_arr = np.asarray(deep_vec, dtype=np.float32).reshape(-1)
        if source_arr.shape == deep_arr.shape:
            diff = np.abs(source_arr - deep_arr)
            measurement["source_deep_vector_comparison"] = {
                "exact_numpy_array_equal": bool(np.array_equal(source_arr, deep_arr)),
                "max_abs_diff": float(diff.max()) if diff.size else 0.0,
                "source_sha256_float32": hashlib.sha256(source_arr.tobytes()).hexdigest(),
                "deep_sha256_float32": hashlib.sha256(deep_arr.tobytes()).hexdigest(),
            }
        else:
            measurement["source_deep_vector_comparison"] = {
                "exact_numpy_array_equal": False,
                "shape_mismatch": {"source": list(source_arr.shape), "deep": list(deep_arr.shape)},
            }
    else:
        measurement["source_deep_vector_comparison"] = {
            "exact_numpy_array_equal": False,
            "reason": "source or deep vector unavailable",
        }

    measurement["m6_success"] = all(bool(v) for v in measurement["m6_definition"].values())
    return measurement


def optional_fabric_retrieval(
    *,
    app_mod: Any,
    workspace_id: str,
    query_text: str,
    target_eid: int,
) -> Dict[str, Any]:
    try:
        response = app_mod.fabric.query(
            workspace_id=workspace_id,
            agent_id=AGENT_ID,
            query_text=query_text,
            top_k=80,
            domain_id=DOMAIN_ID,
            peek_bridges=False,
            explain=True,
            continuity_debug=True,
            memory_plan={
                "top_k_by_lane": {"core": 1, "relational": 1, "deep": 80},
                "weight_by_lane": {"core": 1.0, "relational": 1.0, "deep": 1.0},
            },
        )
        results = response.get("results") if isinstance(response.get("results"), list) else []
        deep_like = [
            hit
            for hit in results
            if isinstance(hit, Mapping)
            and (
                hit.get("from_deep_memory")
                or hit.get("deep_memory")
                or hit.get("spirit_return_mode")
                or hit.get("scope") == "deep"
            )
        ]
        return {
            "performed": True,
            "method": "TormentFabric.query(memory_plan with deep lane headroom)",
            "top_k": 80,
            "target_eid": int(target_eid),
            "target_eid_in_deep_like_results": any(int(hit.get("eid", -1)) == int(target_eid) for hit in deep_like),
            "deep_like_result_count": len(deep_like),
            "deep_like_results": deep_like[:10],
            "response_keys": sorted(response.keys()),
            "result_count": len(results),
        }
    except Exception as exc:
        return {
            "performed": True,
            "method": "TormentFabric.query(memory_plan with deep lane headroom)",
            "error": str(exc),
        }


def derive_taxonomy(output: Mapping[str, Any]) -> Dict[str, Any]:
    milestones = output.get("milestones") if isinstance(output.get("milestones"), Mapping) else {}
    first_long = output.get("first_long_path_details") or {}
    source = first_long.get("source") if isinstance(first_long, Mapping) else {}
    m6 = output.get("m6_measurement") if isinstance(output.get("m6_measurement"), Mapping) else {}
    m6_success = bool(m6.get("m6_success"))
    m5 = bool(milestones.get("M5_FIRST_DEEP_TEXT_RECORD"))
    embedding_ref_non_null = bool(m6.get("m6_definition", {}).get("B_embedding_ref_non_null")) if isinstance(m6.get("m6_definition"), Mapping) else False
    referenced_ok = bool(m6.get("m6_definition", {}).get("C_referenced_files_exist_and_readable")) if isinstance(m6.get("m6_definition"), Mapping) else False
    fresh_query_ok = bool(m6.get("m6_definition", {}).get("E_fresh_query_returns_eid_above_production_threshold")) if isinstance(m6.get("m6_definition"), Mapping) else False
    vector_cmp = m6.get("source_deep_vector_comparison") if isinstance(m6.get("source_deep_vector_comparison"), Mapping) else {}
    warnings = output.get("warnings_errors") if isinstance(output.get("warnings_errors"), Mapping) else {}
    warning_messages = " ".join(str(item.get("message", "")) for item in warnings.get("captured_warning_error_records", []) if isinstance(item, Mapping))
    path_warning = (
        "deep memory shard init failed" in warning_messages
        or "deep memory embedding write failed" in warning_messages
    )
    return {
        "SHORT_ROOT_PATH_CONFUND_REMOVED": (
            "DEMONSTRATED"
            if bool((output.get("short_root_preflight") or {}).get("outside_repo"))
            and int(((output.get("short_root_preflight") or {}).get("predicted_deep_embedding_paths") or {}).get("max_path_length", 9999)) <= SHORT_PATH_MAX_ALLOWED
            else "NOT_DEMONSTRATED"
        ),
        "IDENTITY_ANCHOR_LONG_PATH_REPLICATED": (
            "DEMONSTRATED"
            if isinstance(source, Mapping)
            and source.get("type") == "identity_anchor"
            and source.get("compression_route") == "long_path"
            else "NOT_DEMONSTRATED"
        ),
        "M5_DEEP_TEXT_RECORD": "DEMONSTRATED" if m5 else "NOT_DEMONSTRATED",
        "DEEPMEMORY_VECTOR_PERSISTENCE": "DEMONSTRATED" if embedding_ref_non_null and referenced_ok else "FAILED",
        "EMBEDDING_REF_NON_NULL": "DEMONSTRATED" if embedding_ref_non_null else "NOT_DEMONSTRATED",
        "M6_VECTOR_INDEXED_RETRIEVABLE_DEEPMEMORY": (
            "DEMONSTRATED" if m6_success else ("CONTRADICTED" if m5 else "NOT_DEMONSTRATED")
        ),
        "FRESH_STORE_DEEP_QUERY_RETURNS_NEW_EID": "DEMONSTRATED" if fresh_query_ok else "NOT_DEMONSTRATED",
        "DEEP_VECTOR_MATCHES_SOURCE_VECTOR": (
            "DEMONSTRATED" if bool(vector_cmp.get("exact_numpy_array_equal")) else "NOT_DEMONSTRATED"
        ),
        "WINDOWS_MAX_PATH_FAILURE_RECURS": "YES" if path_warning else "NO",
        "PROVIDER_FREE_RETRIEVABLE_DEEP_MEMORY_FORMATION": (
            "DEMONSTRATED" if m6_success else ("CONTRADICTED" if m5 else "NOT_DEMONSTRATED")
        ),
        "ORDINARY_RELATIONAL_LONG_PATH_REACHABILITY": "NOT_TESTED_IN_THIS_SEQUEL",
        "THRESHOLD_LOWERING": "NOT_USED",
        "MANUAL_STEP_ADVANCEMENT": "NOT_USED",
        "DIRECT_COMPRESSION_CALL_AS_AUTHORITY": "NOT_USED",
        "PROVIDER": "NOT_INVOKED",
        "CONFIGURATION_BOUNDARY": "NON_DEFAULT_COMPRESSION_ENABLED",
        "NATURAL_PREVALENCE": "NOT_MEASURED",
    }


def run_worker(args: argparse.Namespace) -> int:
    ensure_required_python(worker=True)
    baseline_start = ensure_baseline(REPO_ROOT)
    data_root = Path(args.data_root).resolve()
    result_path = Path(args.result_path).resolve()
    preregistered_path = Path(args.preregistered).resolve()
    script = load_preregistered_trajectory(preregistered_path)

    if not data_root.exists():
        data_root.mkdir(parents=True, exist_ok=True)
    if any(data_root.iterdir()):
        raise StageStop(f"Worker data root already contains state before app import: {data_root}")

    random.seed(RNG_SEED)
    try:
        import numpy as np

        np.random.seed(RNG_SEED)
    except Exception:
        pass

    capture = CapturingHandler()
    logging.getLogger().addHandler(capture)
    try:
        from examples.lived_use_chat import build_ingest_summary
        import torment_service.app as app_mod

        client = DirectAppClient(app_mod)
        paths = agent_paths(data_root)
        nodes_tail = JsonlTail(paths["nodes"])
        compression_tail = JsonlTail(paths["compression_log"])
        deep_tail = JsonlTail(paths["deep_memories"])

        preflight_result = preflight(client, app_mod, WORKSPACE_ID)
        current_step = int(preflight_result["resumed_current_step"])
        if current_step != 0:
            raise StageStop(f"Fresh isolated trajectory did not start at step 0: {current_step}")

        output: Dict[str, Any] = {
            "label": LABEL,
            "subtype": SUBTYPE,
            "direct_sequel_to": "NATURAL_LONG_MEMORY_REACHABILITY_V1",
            "scope": "IN_PROCESS_ENDPOINT_EQUIVALENT_LIVED_USE_PATH",
            "provider": "NOT_INVOKED",
            "workspace_id": WORKSPACE_ID,
            "agent_id": AGENT_ID,
            "domain_id": DOMAIN_ID,
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "rng_seed": RNG_SEED,
            "baseline_start": baseline_start,
            "python": ensure_required_python(worker=True),
            "short_external_data_root": str(data_root),
            "trajectory_identity": {
                "trajectory_id": TRAJECTORY_ID,
                "max_exchanges": MAX_EXCHANGES,
                "preregistered_path": str(preregistered_path),
                "preregistered_sha256": sha256_file(preregistered_path),
                "previous_harness": str((REPO_ROOT / PREVIOUS_HARNESS_REL).resolve()),
                "previous_harness_sha256": sha256_file((REPO_ROOT / PREVIOUS_HARNESS_REL).resolve()),
                "adaptive_changes": "NONE",
            },
            "authoritative_path": {
                "query": "same-thread call to torment_service.app.query endpoint function for /agent/query",
                "ingest": "same-thread call to torment_service.app.ingest endpoint function for /agent/ingest",
                "spine": "app.ingest shim through SpineRequest and submit_task",
                "compression": "Fabric ingest production hook only",
                "transport_boundary": "FastAPI HTTP/network transport not exercised",
                "direct_compression_call_as_authority": "NOT_USED",
                "direct_deep_memory_export": "NOT_USED",
                "manual_step_advancement": "NOT_USED",
                "threshold_lowering": "NOT_USED",
                "hash_embedding": "NOT_USED",
            },
            "configuration": {
                "TORMENT_COMPRESS_ENABLE": "1",
                "embedder": EXPECTED_EMBEDDER,
                "compression_thresholds": preflight_result["threshold_snapshot"],
            },
            "preflight": preflight_result,
            "path_lengths": predicted_deep_embedding_paths(data_root),
            "per_exchange": [],
            "production_compression_logs": [],
            "milestones": {},
            "first_compression_details": None,
            "first_short_path_details": None,
            "first_long_path_details": None,
            "first_deep_text_record": None,
            "m6_measurement": None,
            "optional_fabric_retrieval": {"performed": False},
            "stop_reason": "",
            "path_invalidity": None,
        }

        successful_ingests = 0
        new_source_rows = 0
        reinforcement_rows = 0
        unexpected_outcome_count = 0

        for index, pair in enumerate(script, 1):
            before = graph_snapshot(app_mod, WORKSPACE_ID)
            before_counts = graph_counts(before)
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
            deep_new_records = deep_tail.read_new()
            recent_after = api_json(client, "GET", f"/index/{WORKSPACE_ID}/{AGENT_ID}/recent", params={"limit": 1})
            after = graph_snapshot(app_mod, WORKSPACE_ID)
            after_counts = graph_counts(after)
            compression_changes = changed_compression_sources(before, after)
            output["production_compression_logs"].extend(new_compression_events)

            outcome = infer_outcome(ingest_response, before, after)
            try:
                eid = int(ingest_response.get("eid", -1))
            except Exception:
                eid = -1
            persisted_proof = verify_persisted_exchange(
                outcome=outcome,
                eid=eid,
                requested_step=requested_step,
                appended_nodes=appended_nodes,
            )
            k_step = kernel_step(app_mod, WORKSPACE_ID)
            query_results = query_response.get("results") if isinstance(query_response.get("results"), list) else []
            record = {
                "exchange": index,
                "current_step_before": current_step,
                "requested_ingest_step": requested_step,
                "persisted_durable_step_evidence": persisted_proof,
                "recent_index_top_step_before": top_recent_step(recent_before),
                "recent_index_top_step_after": top_recent_step(recent_after),
                "kernel_model_step": k_step,
                "outcome": outcome,
                "eid": eid,
                "query_result_count": len(query_results),
                "ingest_path": ingest_response.get("path"),
                "ingest_result_code": ingest_response.get("result_code"),
                "ingest_decision_code": ingest_response.get("decision_code"),
                "graph_source_rows_before": before_counts["source_rows"],
                "graph_source_rows_after": after_counts["source_rows"],
                "successful_ingests_after_exchange": successful_ingests + 1,
                "new_source_rows_total_after_exchange": new_source_rows + (1 if outcome == "NEW_SOURCE_ROW" else 0),
                "reinforcement_total_after_exchange": after_counts["reinforcement_total"],
                "compressed_source_rows": after_counts["compressed_source_rows"],
                "short_path_source_rows": after_counts["short_path_source_rows"],
                "long_path_source_rows": after_counts["long_path_source_rows"],
                "exported_deep_source_rows": after_counts["exported_deep_source_rows"],
                "deep_memory_count": len(read_jsonl(paths["deep_memories"])),
                "compression_changes": compression_changes,
                "compression_events": new_compression_events,
                "deep_new_record_eids": [int(row.get("eid", 0) or 0) for row in deep_new_records],
                "appended_node_count": len(appended_nodes),
                "appended_node_eids": [int(row.get("eid", -1)) for row in appended_nodes if isinstance(row, Mapping)],
            }
            output["per_exchange"].append(record)

            if outcome == "NEW_SOURCE_ROW":
                new_source_rows += 1
            elif outcome == "REINFORCEMENT_OF_EXISTING_ROW":
                reinforcement_rows += 1
            else:
                unexpected_outcome_count += 1

            if ingest_response.get("stored") is not True:
                output["stop_reason"] = "HARNESS/PATH_INVALID"
                output["path_invalidity"] = {"exchange": index, "reason": "non-storing ingest", "ingest_response": ingest_response}
                break
            if not persisted_proof["accepted"]:
                output["stop_reason"] = "HARNESS/PATH_INVALID"
                output["path_invalidity"] = {
                    "exchange": index,
                    "reason": "persisted step evidence missing",
                    "outcome": outcome,
                    "eid": eid,
                    "requested_step": requested_step,
                    "persisted_proof": persisted_proof,
                }
                break
            if k_step != requested_step:
                output["stop_reason"] = "HARNESS/PATH_INVALID"
                output["path_invalidity"] = {
                    "exchange": index,
                    "reason": "kernel step mismatch",
                    "requested_step": requested_step,
                    "kernel_step": k_step,
                }
                break

            update_milestones(
                output["milestones"],
                exchange=index,
                step=requested_step,
                compression_changes=compression_changes,
                deep_new_records=deep_new_records,
            )

            if compression_changes["newly_changed"] and output["first_compression_details"] is None:
                first_eid = int(compression_changes["newly_changed"][0])
                output["first_compression_details"] = {
                    "exchange": index,
                    "step": requested_step,
                    "source": source_detail(eid=first_eid, before=before, after=after, current_step=requested_step),
                    "all_changed_eids": compression_changes["newly_changed"],
                    "compression_events": new_compression_events,
                    "trigger_observation": (
                        "compression_log.jsonl"
                        if new_compression_events
                        else "INFERRED_FROM_DURABLE_SOURCE_PAYLOAD_MUTATION"
                    ),
                }
            if compression_changes["newly_short_path"] and output["first_short_path_details"] is None:
                first_eid = int(compression_changes["newly_short_path"][0])
                output["first_short_path_details"] = {
                    "exchange": index,
                    "step": requested_step,
                    "source": source_detail(eid=first_eid, before=before, after=after, current_step=requested_step),
                    "all_short_path_eids": compression_changes["newly_short_path"],
                }
            if compression_changes["newly_long_path"] and output["first_long_path_details"] is None:
                first_eid = int(compression_changes["newly_long_path"][0])
                output["first_long_path_details"] = {
                    "exchange": index,
                    "step": requested_step,
                    "source": source_detail(eid=first_eid, before=before, after=after, current_step=requested_step),
                    "all_long_path_eids": compression_changes["newly_long_path"],
                }

            if deep_new_records:
                if not compression_changes["newly_long_path"]:
                    output["stop_reason"] = "HARNESS/PATH_INVALID"
                    output["path_invalidity"] = {
                        "exchange": index,
                        "reason": "deep text record appeared without same-exchange long_path source",
                        "deep_new_records": deep_new_records,
                        "compression_changes": compression_changes,
                    }
                    current_step = requested_step
                    successful_ingests += 1
                    break
                first_deep = dict(deep_new_records[0])
                m6 = measure_m6(
                    app_mod=app_mod,
                    data_root=data_root,
                    paths=paths,
                    deep_record=first_deep,
                    workspace_id=WORKSPACE_ID,
                )
                update_milestones(
                    output["milestones"],
                    exchange=index,
                    step=requested_step,
                    compression_changes=compression_changes,
                    deep_new_records=deep_new_records,
                    m6=m6,
                )
                output["first_deep_text_record"] = {
                    "exchange": index,
                    "step": requested_step,
                    "deep_records_created_this_exchange": deep_new_records,
                    "first_record": first_deep,
                    "first_record_summary_length": len(str(first_deep.get("summary", "") or "")),
                    "first_record_embedding_ref": first_deep.get("embedding_ref"),
                    "storage_state_before_fresh_store_query": m6.get("pre_fresh_store_file_state"),
                }
                output["m6_measurement"] = m6
                if m6.get("m6_success"):
                    output["optional_fabric_retrieval"] = optional_fabric_retrieval(
                        app_mod=app_mod,
                        workspace_id=WORKSPACE_ID,
                        query_text=str(first_deep.get("summary", "") or ""),
                        target_eid=int(first_deep.get("eid", 0) or 0),
                    )
                    output["stop_reason"] = "M6_RETRIEVABLE_DEEP_MEMORY_CONFIRMED"
                else:
                    output["stop_reason"] = "M5_DEEP_TEXT_RECORD_FORMED_BUT_M6_FAILED"
                current_step = requested_step
                successful_ingests += 1
                print(
                    f"M5/M6 stop exchange={index} step={requested_step} "
                    f"m6_success={bool(m6.get('m6_success'))}",
                    flush=True,
                )
                break

            current_step = requested_step
            successful_ingests += 1
            if index % int(args.progress_every) == 0:
                print(
                    f"exchange={index} step={requested_step} "
                    f"graph_rows={after_counts['source_rows']} "
                    f"short_path={after_counts['short_path_source_rows']} "
                    f"long_path={after_counts['long_path_source_rows']} "
                    f"deep={record['deep_memory_count']}",
                    flush=True,
                )

        if not output["stop_reason"]:
            output["stop_reason"] = "MAX_150_EXCHANGES_WITHOUT_M5"

        final_snapshot = graph_snapshot(app_mod, WORKSPACE_ID)
        final_counts = graph_counts(final_snapshot)
        output["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
        output["exchange_count"] = len(output["per_exchange"])
        output["successful_ingests"] = successful_ingests
        output["outcome_counts"] = {
            "NEW_SOURCE_ROW": new_source_rows,
            "REINFORCEMENT_OF_EXISTING_ROW": reinforcement_rows,
            "OTHER": unexpected_outcome_count,
        }
        output["final_graph_counts"] = final_counts
        output["deep_memory_final"] = deep_storage_state(paths, None)
        output["source_paths"] = {key: str(value.resolve()) for key, value in paths.items()}
        output["warnings_errors"] = {
            "captured_warning_error_records": capture.records,
            "deep_memory_shard_init_failed_present": any(
                "deep memory shard init failed" in str(record.get("message", ""))
                for record in capture.records
            ),
            "deep_memory_embedding_write_failed_present": any(
                "deep memory embedding write failed" in str(record.get("message", ""))
                for record in capture.records
            ),
        }
        output["final_taxonomy"] = derive_taxonomy(output)
        output["baseline_end"] = ensure_baseline(REPO_ROOT)
        output["final_git_status"] = git_snapshot(REPO_ROOT)
        write_json(result_path, output)
        print(f"AUTHORITATIVE_RESULT_PATH={result_path}", flush=True)
        print("FINAL_TAXONOMY=" + json.dumps(output["final_taxonomy"], sort_keys=True), flush=True)
        return 0
    finally:
        logging.getLogger().removeHandler(capture)


def run_worker_subprocess(
    *,
    output_dir: Path,
    data_root: Path,
    env: Dict[str, str],
    preregistered_path: Path,
    progress_every: int,
) -> Dict[str, Any]:
    worker_dir = output_dir / "worker"
    worker_dir.mkdir(parents=True, exist_ok=True)
    result_path = worker_dir / "worker_result.json"
    log_path = worker_dir / "worker.stdout.log"
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--data-root",
        str(data_root),
        "--result-path",
        str(result_path),
        "--preregistered",
        str(preregistered_path),
        "--progress-every",
        str(progress_every),
    ]
    started = datetime.now(timezone.utc).isoformat()
    with log_path.open("w", encoding="utf-8", newline="\n") as log_handle:
        proc = subprocess.Popen(
            command,
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="", flush=True)
            log_handle.write(line)
        rc = proc.wait()
    completed = datetime.now(timezone.utc).isoformat()
    record = {
        "command": command,
        "returncode": rc,
        "started_at_utc": started,
        "completed_at_utc": completed,
        "data_root": str(data_root.resolve()),
        "worker_result_path": str(result_path.resolve()),
        "worker_log_path": str(log_path.resolve()),
    }
    if rc != 0:
        raise StageStop(f"Worker failed with return code {rc}; see {log_path}")
    if not result_path.exists():
        raise StageStop(f"Worker did not write result {result_path}")
    record["result"] = read_json(result_path)
    return record


def run_main(args: argparse.Namespace) -> int:
    ensure_required_python(worker=False)
    baseline_start = ensure_baseline(REPO_ROOT)
    previous_harness = load_previous_harness()

    timestamp = args.timestamp or utc_stamp()
    output_dir = (REPO_ROOT / OUTPUT_REL_PREFIX / timestamp).resolve()
    if output_dir.exists():
        raise StageStop(f"Output directory already exists: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=False)

    short_root_base = Path(args.short_root_base).resolve()
    data_root = (short_root_base / timestamp).resolve()
    short_root_preflight = validate_short_data_root(data_root, output_dir)

    preregistered = generate_preregistered_trajectory(previous_harness)
    preregistered_path = output_dir / "preregistered_t3_mixed_trajectory.json"
    write_json(preregistered_path, preregistered)

    env, env_meta = configure_worker_env(os.environ, data_root=data_root)
    write_json(output_dir / "env_meta.json", env_meta)
    write_json(output_dir / "short_root_preflight.json", short_root_preflight)

    worker_record = run_worker_subprocess(
        output_dir=output_dir,
        data_root=data_root,
        env=env,
        preregistered_path=preregistered_path,
        progress_every=int(args.progress_every),
    )
    worker_result = dict(worker_record["result"])
    worker_result["baseline_start_main"] = baseline_start
    worker_result["baseline_end_main"] = ensure_baseline(REPO_ROOT)
    worker_result["output_dir"] = str(output_dir)
    worker_result["result_path"] = str((output_dir / f"{LABEL}_result.json").resolve())
    worker_result["commands"] = {
        "py_compile": f"python -m py_compile {SCRIPT_REL}",
        "harness": " ".join(worker_record["command"]),
    }
    worker_result["short_root_preflight"] = short_root_preflight
    worker_result["final_taxonomy"] = derive_taxonomy(worker_result)
    worker_result["worker_record"] = {
        key: value for key, value in worker_record.items() if key != "result"
    }
    worker_result["final_git_status"] = git_snapshot(REPO_ROOT)

    final_path = output_dir / f"{LABEL}_result.json"
    write_json(final_path, worker_result)
    print(f"AUTHORITATIVE_RESULT_PATH={final_path}", flush=True)
    print("FINAL_TAXONOMY=" + json.dumps(worker_result["final_taxonomy"], sort_keys=True), flush=True)
    return 0


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=LABEL)
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--short-root-base", default=str(SHORT_ROOT_BASE))
    parser.add_argument("--progress-every", type=int, default=PROGRESS_EVERY)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--data-root", default="")
    parser.add_argument("--result-path", default="")
    parser.add_argument("--preregistered", default="")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        if args.worker:
            return run_worker(args)
        return run_main(args)
    except StageStop as exc:
        print(f"STAGE_STOP: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
