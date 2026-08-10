from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np


LABEL = "long_memory_source_surface_characterization_v1"
AUTHORIZED_HEAD = "dd06aea93ea89dbefe8e8aeab032a45bc6ed293e"
REQUIRED_PYTHON = Path(r"C:\Users\Notandi\miniconda3\envs\torment\python.exe")

WORKSPACE_ID = "lmsc_v1"
AGENT_ID = "stage1_agent"
DOMAIN_ID = "personal"

SOURCE_TEXT = (
    "On March 3, 2024, I left my cobalt-blue notebook beneath the east kitchen "
    "window during a thunderstorm. My cat Mosi knocked over a brass pencil cup, "
    "and I laughed instead of getting annoyed. I later moved the notebook into "
    "the second drawer of the old wooden desk so it would stay dry."
)
FROZEN_QUERY = "What do you remember about the cobalt-blue notebook and the thunderstorm?"

EXPECTED_EMBEDDER = {
    "provider": "st",
    "model": "BAAI/bge-small-en-v1.5",
    "dim": 384,
}

CONTROL_INGESTS = [
    (
        650,
        "Experiment timing marker at logical step 650 for the long-memory characterization run.",
    ),
    (
        900,
        "Experiment timing marker at logical step 900 for the long-memory characterization run.",
    ),
    (
        1150,
        "Experiment timing marker at logical step 1150 for the long-memory characterization run.",
    ),
    (
        1400,
        "Experiment timing marker at logical step 1400 for the long-memory characterization run.",
    ),
    (
        1650,
        "Experiment timing marker at logical step 1650 for the long-memory characterization run.",
    ),
]

THRESHOLD_ENV_VARS = [
    "TORMENT_COMPRESS_MIN_STEP",
    "TORMENT_COMPRESS_MIN_AGE",
    "TORMENT_COMPRESS_MAX_CANDIDATES",
    "TORMENT_COMPRESS_DEEP_THRESHOLD",
    "TORMENT_COMPRESS_DEEP_AGE",
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
]


class StageStop(RuntimeError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_cmd(args: List[str], *, cwd: Path) -> str:
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise StageStop(f"Command failed ({proc.returncode}): {' '.join(args)}\n{out}")
    return out.strip()


def git_snapshot(root: Path) -> Dict[str, Any]:
    return {
        "status_short_branch": run_cmd(["git", "status", "--short", "--branch"], cwd=root),
        "head": run_cmd(["git", "rev-parse", "HEAD"], cwd=root),
        "origin_main": run_cmd(["git", "rev-parse", "origin/main"], cwd=root),
        "log_1": run_cmd(["git", "log", "-1", "--format=%H%n%D%n%an <%ae>%n%aI%n%s"], cwd=root),
    }


def ensure_authorized_head(root: Path) -> Dict[str, Any]:
    snap = git_snapshot(root)
    if snap["head"] != AUTHORIZED_HEAD:
        raise StageStop(f"HEAD {snap['head']} differs from authorized {AUTHORIZED_HEAD}")
    if snap["origin_main"] != AUTHORIZED_HEAD:
        raise StageStop(
            f"origin/main {snap['origin_main']} differs from authorized {AUTHORIZED_HEAD}"
        )
    return snap


def ensure_required_python() -> Dict[str, Any]:
    actual = Path(sys.executable).resolve()
    required = REQUIRED_PYTHON.resolve()
    ok = False
    try:
        ok = actual.samefile(required)
    except Exception:
        ok = str(actual).lower() == str(required).lower()
    if not ok:
        raise StageStop(f"Run with {required}; current interpreter is {actual}")
    return {"required": str(required), "actual": str(actual)}


def configure_experiment_env(env: Dict[str, str], basin: Path, arm_name: str) -> Dict[str, Any]:
    removed = {}
    for key in THRESHOLD_ENV_VARS:
        if key in env:
            removed[key] = env.pop(key)

    env.update(
        {
            "TORMENT_PROFILE": "companion",
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
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "TORMENT_AUTH_ENABLE": "0",
            "TORMENT_DATA_DIR": str(basin),
            "TORMENT_TEST_CONDITION": f"{LABEL}_{arm_name}",
            "TORMENT_SERVER_LAUNCHER_PATH": str(Path(__file__).resolve()),
            "OPENAI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
        }
    )
    return {"removed_threshold_env_overrides": removed, "effective_env_subset": {
        key: env.get(key, "") for key in sorted(
            [
                "TORMENT_PROFILE",
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
                "TORMENT_EMBED_PROVIDER",
                "TORMENT_EMBED_MODEL",
                "TORMENT_EMBED_STRICT",
                "TORMENT_DATA_DIR",
            ]
        )
    }}


def resolved_runtime_constants(root: Path, env: Dict[str, str]) -> Dict[str, Any]:
    code = r"""
import json
from torment_service import compression as c
from torment_service import spirit_return as s
out = {
  "compression": {
    "COMPRESS_MIN_AGE": c.COMPRESS_MIN_AGE,
    "COMPRESS_DEEP_THRESHOLD": c.COMPRESS_DEEP_THRESHOLD,
    "COMPRESS_AGE_THRESHOLD": c.COMPRESS_AGE_THRESHOLD,
    "COMPRESS_STEP_INTERVAL": c.COMPRESS_STEP_INTERVAL,
    "COMPRESS_FALLBACK_COOLDOWN": c.COMPRESS_FALLBACK_COOLDOWN,
    "COMPRESS_PERIODIC_FLOOR": c.COMPRESS_PERIODIC_FLOOR,
    "COMPRESS_COUNT_THRESHOLD": c.COMPRESS_COUNT_THRESHOLD,
    "COMPRESS_SHORT_PATH_MULT": c.COMPRESS_SHORT_PATH_MULT,
    "COMPRESS_LONG_PATH_STRENGTH": c.COMPRESS_LONG_PATH_STRENGTH,
    "COMPRESS_ECHO_DEEP_AGE": c.COMPRESS_ECHO_DEEP_AGE,
    "COMPRESS_HARD_CAP": c.COMPRESS_HARD_CAP,
    "COMPRESS_HARD_CAP_TARGET": c.COMPRESS_HARD_CAP_TARGET,
  },
  "spirit_return": {
    "WARMTH_WINDOW_STEPS": s.WARMTH_WINDOW_STEPS,
    "WARMTH_FLOOR": s.WARMTH_FLOOR,
    "WARMTH_INCREMENT": s.WARMTH_INCREMENT,
    "WARMTH_CAP": s.WARMTH_CAP,
  },
  "randomness": "SPIRIT_RETURN_RANDOMNESS_NOT_PRESENT_CURRENT_HEAD"
}
print(json.dumps(out, sort_keys=True))
"""
    proc = subprocess.run(
        [str(REQUIRED_PYTHON), "-c", code],
        cwd=str(root),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise StageStop(f"Could not resolve constants:\n{proc.stdout}\n{proc.stderr}")
    return json.loads(proc.stdout)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def http_json(
    base_url: str,
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    *,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=base_url.rstrip("/") + path,
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise StageStop(f"HTTP {exc.code} {method} {path}: {body}") from exc
    except urllib.error.URLError as exc:
        raise StageStop(f"HTTP failed {method} {path}: {exc}") from exc


def wait_health(base_url: str, proc: subprocess.Popen[Any], timeout_s: float = 120.0) -> Dict[str, Any]:
    deadline = time.time() + timeout_s
    last_error = ""
    while time.time() < deadline:
        if proc.poll() is not None:
            raise StageStop(f"Service exited before health check, code={proc.returncode}")
        try:
            health = http_json(base_url, "GET", "/health", timeout=2.0)
            if health.get("ok") is True:
                return health
        except Exception as exc:
            last_error = str(exc)
        time.sleep(0.5)
    raise StageStop(f"Service did not become healthy: {last_error}")


def start_service(root: Path, basin: Path, arm_name: str, log_dir: Path) -> Tuple[subprocess.Popen[Any], str, int, Dict[str, Any]]:
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env_meta = configure_experiment_env(env, basin, arm_name)

    stdout_path = log_dir / f"{arm_name}.server.stdout.log"
    stderr_path = log_dir / f"{arm_name}.server.stderr.log"
    stdout_f = stdout_path.open("w", encoding="utf-8")
    stderr_f = stderr_path.open("w", encoding="utf-8")
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    proc = subprocess.Popen(
        [
            str(REQUIRED_PYTHON),
            "-m",
            "uvicorn",
            "torment_service.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(root),
        env=env,
        stdout=stdout_f,
        stderr=stderr_f,
        text=True,
        creationflags=creationflags,
    )
    proc._torment_log_files = (stdout_f, stderr_f)  # type: ignore[attr-defined]
    try:
        health = wait_health(base_url, proc)
        check = http_json(base_url, "GET", "/embedder/check", timeout=60.0)
        for source_name, meta in (("health", health.get("embedder", {})), ("embedder_check", check)):
            provider = str(meta.get("provider", ""))
            model = str(meta.get("model", ""))
            dim = int(meta.get("dim", 0) or 0)
            if provider != EXPECTED_EMBEDDER["provider"] or model != EXPECTED_EMBEDDER["model"] or dim != EXPECTED_EMBEDDER["dim"]:
                raise StageStop(f"{source_name} embedder mismatch: {meta}")
        config = http_json(base_url, "GET", "/config", timeout=15.0)
        return proc, base_url, port, {
            "pid": proc.pid,
            "port": port,
            "base_url": base_url,
            "health": health,
            "embedder_check": check,
            "config": config,
            "env_meta": env_meta,
            "logs": {"stdout": str(stdout_path), "stderr": str(stderr_path)},
        }
    except Exception:
        stop_service(proc)
        raise


def stop_service(proc: subprocess.Popen[Any]) -> Dict[str, Any]:
    pid = int(proc.pid)
    already_gone = proc.poll() is not None
    if not already_gone:
        proc.terminate()
    try:
        proc.wait(timeout=20.0)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        else:
            proc.kill()
        proc.wait(timeout=20.0)
    for handle in getattr(proc, "_torment_log_files", ()):
        try:
            handle.close()
        except Exception:
            pass
    return {
        "pid": pid,
        "already_gone": bool(already_gone),
        "returncode": proc.returncode,
        "gone": proc.poll() is not None,
    }


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def agent_dir(basin: Path) -> Path:
    return basin / "workspaces" / WORKSPACE_ID / "agents" / AGENT_ID


def private_dir(basin: Path) -> Path:
    return agent_dir(basin) / "private"


def deep_dir(basin: Path) -> Path:
    return agent_dir(basin) / "deep_memory"


def warmup_dir(basin: Path) -> Path:
    return agent_dir(basin) / "warmup"


def source_payload_fields(payload: Dict[str, Any], born_step: Optional[int] = None) -> Dict[str, Any]:
    keys = [
        "summary",
        "text",
        "embedding_provider",
        "embedding_model",
        "embedding_dim",
        "embedding_checksum",
        "embedding_ref",
        "created_at",
        "created_ts",
        "last_reinforced",
        "last_reinforced_ts",
        "reinforcement_count",
        "provenance",
        "domain_id",
        "scope",
        "memory_class",
        "tier",
        "canon",
        "strength",
        "confidence",
        "lifecycle",
        "affect_tag",
        "affect_conf",
        "affect_attribution",
        "state_symbol",
        "symbol_confidence",
        "symbol_reason",
        "in_corridor",
        "survival_steps",
        "tearing_risk",
        "phase_duration_steps",
        "corridor_duration_steps",
        "srg",
        "compressed",
        "compressed_step",
        "compression_route",
        "compression_score",
        "compression_tier",
        "exported_deep",
        "exported_step",
    ]
    out = {k: payload.get(k) for k in keys if k in payload}
    out["born_step"] = born_step
    return out


def node_snapshot(basin: Path, relevant_eids: Iterable[int] = ()) -> Dict[str, Any]:
    nodes_path = private_dir(basin) / "nodes.jsonl"
    rows = read_jsonl(nodes_path)
    latest: Dict[int, Dict[str, Any]] = {}
    records_by_eid: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        try:
            eid = int(row.get("eid"))
        except Exception:
            continue
        latest[eid] = row
        records_by_eid[eid].append(row)

    relevant = sorted({int(e) for e in relevant_eids if int(e) > 0} | set(latest.keys()))
    compact_latest: Dict[str, Any] = {}
    compact_records: Dict[str, Any] = {}
    for eid in relevant:
        row = latest.get(eid)
        if row is None:
            continue
        payload = dict(row.get("payload", {}) or {})
        compact_latest[str(eid)] = {
            "eid": eid,
            "born_step": int(row.get("born_step", 0) or 0),
            "channel": row.get("channel"),
            "source_state": source_payload_fields(payload, int(row.get("born_step", 0) or 0)),
            "payload": payload,
        }
        compact_records[str(eid)] = {
            "count": len(records_by_eid.get(eid, [])),
            "records": records_by_eid.get(eid, []),
        }
    return {
        "path": str(nodes_path),
        "exists": nodes_path.exists(),
        "total_records": len(rows),
        "distinct_eids": len(latest),
        "record_count_by_eid": {str(k): len(v) for k, v in sorted(records_by_eid.items())},
        "latest_by_eid": compact_latest,
        "records_by_eid": compact_records,
    }


def deep_snapshot(basin: Path, source_eid: Optional[int] = None) -> Dict[str, Any]:
    memories_path = deep_dir(basin) / "memories.jsonl"
    rows = read_jsonl(memories_path)
    selected = []
    if source_eid is not None:
        for row in rows:
            try:
                if int(row.get("eid")) == int(source_eid):
                    selected.append(row)
            except Exception:
                continue
    emb_manifest = deep_dir(basin) / "embeddings" / "manifest.json"
    manifest = None
    if emb_manifest.exists():
        with emb_manifest.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    map_rows: List[Dict[str, Any]] = []
    emb_root = deep_dir(basin) / "embeddings"
    if emb_root.exists():
        for map_path in sorted(emb_root.glob("*.map.jsonl")):
            for row in read_jsonl(map_path):
                row["_path"] = str(map_path)
                map_rows.append(row)
    return {
        "path": str(memories_path),
        "exists": memories_path.exists(),
        "count": len(rows),
        "rows": rows,
        "rows_for_source_eid": selected,
        "embedding_manifest_path": str(emb_manifest),
        "embedding_manifest": manifest,
        "embedding_map_rows": map_rows,
    }


def compression_log_snapshot(basin: Path) -> Dict[str, Any]:
    path = private_dir(basin) / "compression_log.jsonl"
    return {"path": str(path), "exists": path.exists(), "rows": read_jsonl(path)}


def warmup_snapshot(basin: Path, source_eid: Optional[int] = None) -> Dict[str, Any]:
    path = warmup_dir(basin) / "warmup_state.jsonl"
    rows = read_jsonl(path)
    latest_by_eid: Dict[str, Any] = {}
    for row in rows:
        try:
            latest_by_eid[str(int(row.get("eid")))] = row
        except Exception:
            continue
    selected = None
    if source_eid is not None:
        selected = latest_by_eid.get(str(int(source_eid)))
    return {
        "path": str(path),
        "dir_exists": warmup_dir(basin).exists(),
        "file_exists": path.exists(),
        "rows": rows,
        "latest_by_eid": latest_by_eid,
        "source_record": selected,
    }


def api_state(base_url: Optional[str]) -> Dict[str, Any]:
    if not base_url:
        return {}
    out: Dict[str, Any] = {}
    try:
        out["debug_metrics"] = http_json(
            base_url,
            "GET",
            f"/debug/metrics?workspace_id={WORKSPACE_ID}&agent_id={AGENT_ID}",
            timeout=20.0,
        )
    except Exception as exc:
        out["debug_metrics_error"] = str(exc)
    try:
        out["compression_status"] = http_json(
            base_url,
            "GET",
            f"/workspace/{WORKSPACE_ID}/compress/status?agent_id={AGENT_ID}",
            timeout=20.0,
        )
    except Exception as exc:
        out["compression_status_error"] = str(exc)
    return out


def full_state_snapshot(
    label: str,
    basin: Path,
    source_eid: Optional[int],
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "label": label,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "nodes": node_snapshot(basin, [source_eid] if source_eid else []),
        "deep_memory": deep_snapshot(basin, source_eid),
        "compression_log": compression_log_snapshot(basin),
        "warmup": warmup_snapshot(basin, source_eid),
        "api": api_state(base_url),
    }


def ingest_payload(text: str, step: int) -> Dict[str, Any]:
    return {
        "workspace_id": WORKSPACE_ID,
        "agent_id": AGENT_ID,
        "text": text,
        "supplied_summary": text,
        "step": int(step),
        "domain_id": DOMAIN_ID,
        "scope": "private",
    }


def retrieve_payload() -> Dict[str, Any]:
    return {
        "workspace_id": WORKSPACE_ID,
        "agent_id": AGENT_ID,
        "query": FROZEN_QUERY,
        "profile": "companion",
        "token_budget": 4000,
        "top_k": 8,
        "archive_top_k": 5,
        "archive_min_score": 0.0,
        "domain_id": DOMAIN_ID,
        "include_assembly_audit": True,
    }


def latest_source_record(snapshot: Dict[str, Any], source_eid: int) -> Optional[Dict[str, Any]]:
    return ((snapshot.get("nodes") or {}).get("latest_by_eid") or {}).get(str(int(source_eid)))


def latest_source_payload(snapshot: Dict[str, Any], source_eid: int) -> Dict[str, Any]:
    rec = latest_source_record(snapshot, source_eid) or {}
    return dict(rec.get("payload") or {})


def latest_deep_object(snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rows = ((snapshot.get("deep_memory") or {}).get("rows_for_source_eid") or [])
    return dict(rows[-1]) if rows else None


def classify_detail(summary: str, detail: str, exact_terms: List[str], semantic_terms: List[str]) -> str:
    lower = summary.lower()
    if any(term.lower() in lower for term in exact_terms):
        return "PRESERVED_EXACTLY"
    if all(term.lower() in lower for term in semantic_terms):
        return "PRESERVED_SEMANTICALLY"
    return "OMITTED"


def detail_preservation_table(deep_summary: str) -> List[Dict[str, Any]]:
    specs = [
        ("March 3, 2024", ["March 3, 2024"], ["march", "2024"]),
        ("cobalt-blue notebook", ["cobalt-blue notebook"], ["cobalt", "notebook"]),
        ("east kitchen window", ["east kitchen window"], ["east", "kitchen", "window"]),
        ("thunderstorm", ["thunderstorm"], ["storm"]),
        ("Mosi", ["Mosi"], ["mosi"]),
        ("brass pencil cup", ["brass pencil cup"], ["brass", "pencil", "cup"]),
        ("laughed instead of annoyed", ["laughed instead of getting annoyed"], ["laughed", "annoyed"]),
        ("second drawer", ["second drawer"], ["second", "drawer"]),
        ("old wooden desk", ["old wooden desk"], ["wooden", "desk"]),
        ("reason: stay dry", ["stay dry"], ["dry"]),
    ]
    return [
        {
            "detail": detail,
            "classification": classify_detail(deep_summary, detail, exact, semantic),
        }
        for detail, exact, semantic in specs
    ]


def compare_field(source_payload: Dict[str, Any], deep_obj: Optional[Dict[str, Any]], source_field: str, deep_field: str) -> Dict[str, Any]:
    source_value = source_payload.get(source_field)
    deep_value: Any = None
    if deep_obj is not None:
        if deep_field.startswith("metadata."):
            deep_value = (deep_obj.get("metadata") or {}).get(deep_field.split(".", 1)[1])
        else:
            deep_value = deep_obj.get(deep_field)

    if deep_obj is None:
        relation = "UNKNOWN"
    elif deep_value is None:
        relation = "OMITTED"
    elif deep_value == source_value:
        relation = "EXACT"
    else:
        relation = "TRANSFORMED"

    return {
        "source_field": source_field,
        "source_value": source_value,
        "deep_field": deep_field,
        "deep_value": deep_value,
        "relation": relation,
    }


def source_to_deep_mapping(source_payload: Dict[str, Any], source_born_step: Optional[int], deep_obj: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = [
        compare_field({"eid": deep_obj.get("eid") if deep_obj else None}, deep_obj, "eid", "eid"),
        compare_field(source_payload, deep_obj, "summary", "summary"),
        compare_field({"created_at": source_payload.get("created_at")}, deep_obj, "created_at", "born_step"),
        compare_field({"born_step": source_born_step}, deep_obj, "born_step", "born_step"),
        compare_field(source_payload, deep_obj, "created_ts", "created_ts"),
        compare_field(source_payload, deep_obj, "provenance", "metadata.provenance"),
        compare_field(source_payload, deep_obj, "workspace_id", "metadata.workspace_id"),
        compare_field(source_payload, deep_obj, "domain_id", "metadata.domain_id"),
        compare_field(source_payload, deep_obj, "scope", "metadata.scope"),
        compare_field(source_payload, deep_obj, "agent_id", "metadata.agent_id"),
        compare_field(source_payload, deep_obj, "memory_class", "memory_class"),
        compare_field(source_payload, deep_obj, "tier", "metadata.tier"),
        compare_field(source_payload, deep_obj, "canon", "metadata.canon"),
        compare_field(source_payload, deep_obj, "strength", "strength"),
        compare_field(source_payload, deep_obj, "lifecycle", "metadata.lifecycle"),
        compare_field(source_payload, deep_obj, "affect_tag", "metadata.affect_tag"),
        compare_field(source_payload, deep_obj, "affect_attribution", "metadata.affect_attribution"),
        compare_field(source_payload, deep_obj, "state_symbol", "metadata.state_symbol"),
        compare_field(source_payload, deep_obj, "in_corridor", "metadata.in_corridor"),
        compare_field(source_payload, deep_obj, "survival_steps", "metadata.survival_steps"),
        compare_field(source_payload, deep_obj, "tearing_risk", "metadata.tearing_risk"),
        compare_field(source_payload, deep_obj, "phase_duration_steps", "metadata.phase_duration_steps"),
        compare_field(source_payload, deep_obj, "corridor_duration_steps", "metadata.corridor_duration_steps"),
        compare_field(source_payload, deep_obj, "srg", "metadata.srg"),
        compare_field(source_payload, deep_obj, "embedding_ref", "embedding_ref"),
        compare_field(source_payload, deep_obj, "embedding_checksum", "metadata.embedding_checksum"),
        compare_field(source_payload, deep_obj, "embedding_provider", "metadata.embedding_provider"),
        compare_field(source_payload, deep_obj, "embedding_model", "metadata.embedding_model"),
    ]
    if deep_obj is not None:
        rows.append({
            "source_field": "compression_score",
            "source_value": source_payload.get("compression_score"),
            "deep_field": "compression_score",
            "deep_value": deep_obj.get("compression_score"),
            "relation": "EXACT" if source_payload.get("compression_score") == deep_obj.get("compression_score") else "TRANSFORMED",
        })
        rows.append({
            "source_field": "compressed_step/exported_step",
            "source_value": {
                "compressed_step": source_payload.get("compressed_step"),
                "exported_step": source_payload.get("exported_step"),
            },
            "deep_field": "compressed_step",
            "deep_value": deep_obj.get("compressed_step"),
            "relation": "TRANSFORMED",
        })
    return rows


def compute_deep_similarity(root: Path, basin: Path, deep_obj: Optional[Dict[str, Any]], env: Dict[str, str]) -> Optional[Dict[str, Any]]:
    if not deep_obj or not deep_obj.get("embedding_ref"):
        return None
    sys.path.insert(0, str(root))
    from torment_service.embedding_store import EmbeddingShardReader
    from torment_service.embeddings import build_embedder_from_env

    old_env = os.environ.copy()
    try:
        os.environ.update(env)
        embedder = build_embedder_from_env()
        query_vec = np.asarray(embedder.embed(FROZEN_QUERY), dtype=np.float32).reshape(-1)
        reader = EmbeddingShardReader(str(deep_dir(basin) / "embeddings"))
        try:
            deep_vec = reader.load_one(deep_obj["embedding_ref"])
        finally:
            reader.close()
        if deep_vec is None:
            return {"available": False, "reason": "embedding_ref_load_failed"}
        q_norm = query_vec / float(np.linalg.norm(query_vec) + 1e-12)
        d_vec = np.asarray(deep_vec, dtype=np.float32).reshape(-1)
        d_norm = d_vec / float(np.linalg.norm(d_vec) + 1e-12)
        if q_norm.shape[0] != d_norm.shape[0]:
            dim = d_norm.shape[0]
            q_norm = np.pad(q_norm, (0, max(0, dim - q_norm.shape[0])))[:dim]
        return {
            "available": True,
            "cosine": float(np.dot(q_norm, d_norm)),
            "query": FROZEN_QUERY,
            "deep_embedding_ref": deep_obj["embedding_ref"],
        }
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def all_blocks(retrieve_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    for block_type, rows in (retrieve_response.get("blocks") or {}).items():
        for idx, row in enumerate(rows or [], start=1):
            item = dict(row)
            item["_block_type"] = block_type
            item["_index_in_block_type"] = idx
            blocks.append(item)
    return blocks


def spirit_blocks(retrieve_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        block for block in all_blocks(retrieve_response)
        if (block.get("metadata") or {}).get("from_spirit_return")
    ]


def normal_source_blocks(retrieve_response: Dict[str, Any], source_eid: int) -> List[Dict[str, Any]]:
    return [
        block for block in all_blocks(retrieve_response)
        if int(block.get("eid") or -1) == int(source_eid)
        and not (block.get("metadata") or {}).get("from_spirit_return")
    ]


def extract_returning_memory_block(assembled_text: str) -> str:
    marker = "[Returning Memory]"
    idx = assembled_text.find(marker)
    if idx < 0:
        return ""
    rest = assembled_text[idx:]
    next_section = len(rest)
    for section in ["\n\n[Identity Context]", "\n\n[Relational Context]", "\n\n[Situational Context]", "\n\n[Archive Context]"]:
        pos = rest.find(section, len(marker))
        if pos >= 0:
            next_section = min(next_section, pos)
    return rest[:next_section].strip()


def classify_surface(block_text: str) -> str:
    if not block_text:
        return "SURFACE_NOT_REACHED"
    lower = block_text.lower()
    authority_terms = ["authoritative", "established", "must believe", "current truth"]
    if any(term in lower for term in authority_terms):
        return "SURFACE_AUTHORITY_CUED"
    relevance_terms = [
        "this feels familiar",
        "there's something about",
        "never really left",
        "resonance",
        "surfacing",
        "familiar",
    ]
    if any(term in lower for term in relevance_terms):
        return "SURFACE_RELEVANCE_CUED"
    return "SURFACE_EVIDENCE_ONLY"


def classify_o(pre_payload: Dict[str, Any], post_payload: Dict[str, Any]) -> List[str]:
    if not post_payload:
        return ["O4_SOURCE_REMOVED"]
    out: List[str] = []
    if post_payload.get("summary") == pre_payload.get("summary"):
        out.append("O1_SOURCE_RETAINED_SEMANTICALLY_UNCHANGED")
    else:
        out.append("O3_SOURCE_SEMANTIC_CONTENT_MUTATED")
    if (
        post_payload.get("strength") != pre_payload.get("strength")
        or post_payload.get("compressed")
        or post_payload.get("exported_deep")
        or post_payload.get("compression_route")
    ):
        out.append("O2_SOURCE_RETAINED_WITH_EXPECTED_STRENGTH_LIFECYCLE_MUTATION")
    return out


def classify_d(deep_obj: Optional[Dict[str, Any]], mapping: List[Dict[str, Any]], detail_table: List[Dict[str, Any]]) -> str:
    if deep_obj is None:
        return "D0_NO_DEEP_EXPORT"
    if not deep_obj.get("eid"):
        return "D3_UNTRACEABLE_ECHO"
    if any(row["classification"] == "DISTORTED" for row in detail_table):
        return "D4_MATERIALLY_DISTORTED_ECHO"
    if any(row["classification"] == "OMITTED" for row in detail_table):
        return "D2_TRACEABLE_LOSSY_ECHO"
    if any(row["relation"] in ("OMITTED", "TRANSFORMED") for row in mapping):
        return "D2_TRACEABLE_LOSSY_ECHO"
    return "D1_TRACEABLE_HIGH_FIDELITY_ECHO"


def classify_s(retrieve_response: Dict[str, Any], source_eid: int) -> List[str]:
    spirits = spirit_blocks(retrieve_response)
    normals = normal_source_blocks(retrieve_response, source_eid)
    if not spirits:
        return ["S0_NO_RETURNING_MEMORY_SURFACE"]
    out = ["S1_RETURNING_MEMORY_SURFACED"]
    if normals:
        out.append("S2_NORMAL_AND_DEEP_DUPLICATE_SURFACE")
    return out


def classify_w(before: Dict[str, Any], after: Dict[str, Any], first_spirit_blocks: List[Dict[str, Any]]) -> List[str]:
    b = before.get("source_record")
    a = after.get("source_record")
    if not a:
        return ["W0_NO_WARMTH_MUTATION"]
    out: List[str] = []
    b_count = int((b or {}).get("appearance_count", 0) or 0)
    a_count = int((a or {}).get("appearance_count", 0) or 0)
    if a_count > b_count:
        out.append("W1_PRE_FEEDBACK_WARMTH_MUTATION")
    else:
        out.append("W0_NO_WARMTH_MUTATION")
    for block in first_spirit_blocks:
        meta = block.get("metadata") or {}
        mode = str(meta.get("spirit_return_mode") or "")
        warmth = float(meta.get("warmth_score", 0.0) or 0.0)
        if (mode == "resonance" and warmth >= 0.5) or (mode == "surfacing" and warmth >= 0.3):
            out.append("W2_FIRST_SURFACE_CLASSIFICATION_CHANGED_BY_WARMTH")
            break
    return out


def classify_p(
    compression_before: Dict[str, Any],
    restart1: Dict[str, Any],
    warmth_after_first: Dict[str, Any],
    restart2: Dict[str, Any],
) -> List[str]:
    out: List[str] = []
    if latest_deep_object(compression_before) == latest_deep_object(restart1):
        out.append("P1_COMPRESSION_STATE_RESTART_EQUIVALENT")
    else:
        out.append("P3_RESTART_CHANGES_CATEGORICAL_STATE")
    if warmth_after_first.get("source_record") == restart2.get("warmup", {}).get("source_record"):
        out.append("P2_WARMTH_STATE_RESTART_EQUIVALENT")
    elif warmth_after_first.get("source_record") is not None:
        out.append("P3_RESTART_CHANGES_CATEGORICAL_STATE")
    restart1_api_deep = (
        ((restart1.get("api") or {}).get("compression_status") or {}).get("deep_memory")
    )
    if latest_deep_object(compression_before) is not None and restart1_api_deep is None:
        out.append("P3_RESTART_CHANGES_CATEGORICAL_STATE")
    return sorted(set(out))


def evidence_flags(
    deep_obj: Optional[Dict[str, Any]],
    mapping: List[Dict[str, Any]],
    surface_class: str,
    retrieve_response: Dict[str, Any],
    source_eid: int,
    warmth_classes: List[str],
    pre_payload: Dict[str, Any],
    post_payload: Dict[str, Any],
) -> List[str]:
    flags: List[str] = []
    if deep_obj is not None and any(row["relation"] in ("OMITTED", "TRANSFORMED") for row in mapping):
        flags.append("DEEP_ECHO_LOSSY")
    if any(row["source_field"] == "provenance" and row["relation"] == "OMITTED" for row in mapping):
        flags.append("PROVENANCE_LOST")
    if any(row["source_field"] in ("created_ts", "compressed_step/exported_step") and row["relation"] in ("OMITTED", "TRANSFORMED") for row in mapping):
        flags.append("CHRONOLOGY_LOST")
    if surface_class == "SURFACE_AUTHORITY_CUED":
        flags.append("HEURISTIC_RELEVANCE_PRESENTED_AS_CERTAINTY")
    if "W1_PRE_FEEDBACK_WARMTH_MUTATION" in warmth_classes:
        flags.append("PRE_FEEDBACK_WARMTH_SELF_REINFORCEMENT")
    if spirit_blocks(retrieve_response) and normal_source_blocks(retrieve_response, source_eid):
        flags.append("NORMAL_AND_DEEP_DUPLICATE_EXPOSURE")
    if post_payload.get("summary") != pre_payload.get("summary"):
        flags.append("SOURCE_SEMANTICS_MUTATED")
    for block in spirit_blocks(retrieve_response):
        if "authority_status" not in (block.get("metadata") or {}):
            flags.append("REHYDRATION_AUTHORITY_METADATA_NOT_SURFACED")
            break
    if not flags:
        flags.append("OTHER: no configured evidence-integrity flag fired")
    return sorted(set(flags))


def run_experiment(root: Path, run_dir: Path) -> Dict[str, Any]:
    basin = run_dir / "basin"
    logs = run_dir / "logs"
    basin.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    service_env = os.environ.copy()
    env_meta = configure_experiment_env(service_env, basin, "constants")

    record: Dict[str, Any] = {
        "experiment_label": LABEL,
        "authorized_head": AUTHORIZED_HEAD,
        "workspace_id": WORKSPACE_ID,
        "agent_id": AGENT_ID,
        "domain_id": DOMAIN_ID,
        "disposable_basin": str(basin),
        "frozen_question": (
            "When one clean user-authored episodic memory passes through TORMENT's real "
            "compression -> Deep Memory -> Spirit Return -> /retrieve pipeline, what exact "
            "evidence survives from the original source row into the provider-visible "
            "Returning Memory surface, what durable source mutation occurs, and what warmth "
            "mutation is caused by the first retrieval?"
        ),
        "source_payload": ingest_payload(SOURCE_TEXT, 1),
        "frozen_query": FROZEN_QUERY,
        "env_meta": env_meta,
        "resolved_configuration": resolved_runtime_constants(root, service_env),
        "service": {},
        "evidence": {},
        "classifications": {},
    }

    proc: Optional[subprocess.Popen[Any]] = None
    proc2: Optional[subprocess.Popen[Any]] = None
    proc3: Optional[subprocess.Popen[Any]] = None
    source_eid: Optional[int] = None
    manual_required = False

    try:
        proc, base_url, _port, startup = start_service(root, basin, "initial", logs)
        record["service"]["initial_start"] = startup

        source_req = ingest_payload(SOURCE_TEXT, 1)
        source_resp = http_json(base_url, "POST", "/agent/ingest", source_req, timeout=90.0)
        if not source_resp.get("stored") or source_resp.get("eid") is None:
            raise StageStop(f"Source ingest did not store: {source_resp}")
        source_eid = int(source_resp["eid"])
        record["evidence"]["source_ingest"] = {"request": source_req, "response": source_resp}

        pre = full_state_snapshot("PRE_COMPRESSION", basin, source_eid, base_url)
        record["evidence"]["pre_compression"] = pre

        compression_attempts: List[Dict[str, Any]] = []
        compression_snapshot = pre
        for step, control_text in CONTROL_INGESTS:
            req = ingest_payload(control_text, step)
            resp = http_json(base_url, "POST", "/agent/ingest", req, timeout=90.0)
            snap = full_state_snapshot(f"AFTER_NORMAL_TRIGGER_STEP_{step}", basin, source_eid, base_url)
            compression_attempts.append({"step": step, "request": req, "response": resp, "snapshot": snap})
            compression_snapshot = snap
            if latest_deep_object(snap) is not None:
                break

        if latest_deep_object(compression_snapshot) is None:
            manual_required = True
            manual_req = {"workspace_id": WORKSPACE_ID, "agent_id": AGENT_ID, "step": 1200}
            manual_resp = http_json(
                base_url,
                "POST",
                f"/workspace/{WORKSPACE_ID}/compress/trigger",
                manual_req,
                timeout=90.0,
            )
            manual_snap = full_state_snapshot("AFTER_MANUAL_COMPRESSION_MECHANICAL_ARM", basin, source_eid, base_url)
            compression_attempts.append({
                "label": "MANUAL_COMPRESSION_MECHANICAL_ARM",
                "request": manual_req,
                "response": manual_resp,
                "snapshot": manual_snap,
            })
            compression_snapshot = manual_snap

        record["evidence"]["compression_attempts"] = compression_attempts
        record["evidence"]["post_compression"] = compression_snapshot
        record["compression_arm"] = (
            "MANUAL_COMPRESSION_MECHANICAL_ARM"
            if manual_required
            else "PRODUCTION_THRESHOLD_MECHANICAL_REACHABILITY"
        )

        deep_obj = latest_deep_object(compression_snapshot)
        if deep_obj is None:
            record["stop_condition"] = "DEEP_EXPORT_NOT_REACHED"
            return record

        stop_initial = stop_service(proc)
        proc = None
        record["service"]["initial_stop_after_compression"] = stop_initial

        proc2, base_url2, _port2, startup2 = start_service(root, basin, "restart1_before_retrieval", logs)
        record["service"]["restart1_start"] = startup2
        restart1 = full_state_snapshot("RESTART_CHECKPOINT_1_BEFORE_FIRST_RETRIEVE", basin, source_eid, base_url2)
        record["evidence"]["restart_checkpoint_1"] = restart1

        warmth_before_first = warmup_snapshot(basin, source_eid)
        first_retrieve_req = retrieve_payload()
        first_retrieve_resp = http_json(base_url2, "POST", "/retrieve", first_retrieve_req, timeout=90.0)
        warmth_after_first = warmup_snapshot(basin, source_eid)
        after_first = full_state_snapshot("AFTER_FIRST_RETRIEVE", basin, source_eid, base_url2)
        record["evidence"]["first_retrieve"] = {
            "request": first_retrieve_req,
            "response": first_retrieve_resp,
            "warmth_before": warmth_before_first,
            "warmth_after": warmth_after_first,
            "post_retrieve_state": after_first,
        }

        stop_restart1 = stop_service(proc2)
        proc2 = None
        record["service"]["restart1_stop_after_first_retrieve"] = stop_restart1

        proc3, base_url3, _port3, startup3 = start_service(root, basin, "restart2_after_retrieval", logs)
        record["service"]["restart2_start"] = startup3
        restart2 = full_state_snapshot("RESTART_CHECKPOINT_2_AFTER_FIRST_RETRIEVE", basin, source_eid, base_url3)
        record["evidence"]["restart_checkpoint_2"] = restart2

        second_needed = bool(spirit_blocks(first_retrieve_resp))
        if second_needed:
            second_warmth_before = warmup_snapshot(basin, source_eid)
            second_resp = http_json(base_url3, "POST", "/retrieve", retrieve_payload(), timeout=90.0)
            second_warmth_after = warmup_snapshot(basin, source_eid)
            record["evidence"]["restart_checkpoint_2"]["final_retrieve_after_restart"] = {
                "run_reason": "same categorical surface verification after first retrieval produced spirit block",
                "response": second_resp,
                "warmth_before": second_warmth_before,
                "warmth_after": second_warmth_after,
            }

        stop_restart2 = stop_service(proc3)
        proc3 = None
        record["service"]["restart2_stop"] = stop_restart2

        pre_payload = latest_source_payload(pre, source_eid)
        post_payload = latest_source_payload(compression_snapshot, source_eid)
        source_rec = latest_source_record(pre, source_eid) or {}
        source_born_step = source_rec.get("born_step")
        mapping = source_to_deep_mapping(post_payload, source_born_step, deep_obj)
        detail_table = detail_preservation_table(str(deep_obj.get("summary", "")))
        deep_similarity = compute_deep_similarity(root, basin, deep_obj, service_env)
        returning_block = extract_returning_memory_block(str(first_retrieve_resp.get("assembled_text", "")))
        surface_class = classify_surface(returning_block)
        s_class = classify_s(first_retrieve_resp, source_eid)
        w_class = classify_w(warmth_before_first, warmth_after_first, spirit_blocks(first_retrieve_resp))

        record["analysis"] = {
            "source_eid": source_eid,
            "post_compression_source_state": source_payload_fields(post_payload, source_born_step),
            "field_level_source_to_deep_mapping": mapping,
            "controlled_detail_preservation": detail_table,
            "deep_memory_object": deep_obj,
            "pre_enrichment_deep_similarity": deep_similarity,
            "normal_source_blocks": normal_source_blocks(first_retrieve_resp, source_eid),
            "spirit_return_blocks": spirit_blocks(first_retrieve_resp),
            "returning_memory_surface": returning_block,
            "surface_framing_classification": surface_class,
        }
        record["classifications"] = {
            "O": classify_o(pre_payload, post_payload),
            "D": classify_d(deep_obj, mapping, detail_table),
            "S": s_class,
            "surface": surface_class,
            "W": w_class,
            "P": classify_p(compression_snapshot, restart1, warmth_after_first, restart2),
        }
        record["evidence_integrity_flags"] = evidence_flags(
            deep_obj,
            mapping,
            surface_class,
            first_retrieve_resp,
            source_eid,
            w_class,
            pre_payload,
            post_payload,
        )
        return record
    finally:
        for live_proc in (proc3, proc2, proc):
            if live_proc is not None and live_proc.poll() is None:
                stop_service(live_proc)


def main() -> int:
    parser = argparse.ArgumentParser(description=LABEL)
    parser.add_argument("--output-root", default=str(Path("outputs") / "lived_use" / "lmsc_v1"))
    parser.add_argument("--keep-existing", action="store_true")
    args = parser.parse_args()

    root = repo_root()
    python_meta = ensure_required_python()
    git_before = ensure_authorized_head(root)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = (root / args.output_root / stamp).resolve()
    if run_dir.exists() and not args.keep_existing:
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    record: Dict[str, Any] = {
        "python": python_meta,
        "git_before": git_before,
        "run_dir": str(run_dir),
    }
    try:
        experiment = run_experiment(root, run_dir)
        record.update(experiment)
        record["stage_1_execution_verdict"] = (
            "STAGE_1_COMPLETED_NEGATIVE_SURFACE"
            if record.get("classifications", {}).get("S") == ["S0_NO_RETURNING_MEMORY_SURFACE"]
            else "STAGE_1_COMPLETED"
        )
        if record.get("stop_condition"):
            record["stage_1_execution_verdict"] = "STAGE_1_STOPPED_NEGATIVE_RESULT"
    except Exception as exc:
        record["stage_1_execution_verdict"] = "STAGE_1_STOPPED_ERROR"
        record["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        try:
            record["git_after"] = git_snapshot(root)
        except Exception as exc:
            record["git_after_error"] = str(exc)
        write_json(run_dir / "stage1_result.json", record)
        print(str(run_dir / "stage1_result.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
