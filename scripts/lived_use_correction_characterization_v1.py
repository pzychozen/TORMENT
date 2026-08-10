from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np


LABEL = "lived_use_correction_characterization_v1"
AUTHORIZED_HEAD = "0f132eea027cd1c2f5178e6f70c8090df03a55ec"
WORKSPACE_ID = LABEL
AGENT_ID = "eira_voss"
DOMAIN_ID = "personal"
EXPECTED_EMBEDDER = {
    "provider": "st",
    "model": "BAAI/bge-small-en-v1.5",
    "dim": 384,
}

ARMS: Dict[str, Dict[str, Any]] = {
    "arm_a": {
        "label": "ARM A - EXPLICIT REVERSAL",
        "old": "My current drink preference is coffee.",
        "correction": "My current drink preference is not coffee anymore.",
        "query": "Do I currently prefer coffee?",
        "expected_regime": "0.88-0.92",
        "expected_detector": True,
        "prediction": [
            "S1_NEW_ROW_SPAWNED",
            "L1_CONFLICT_LINK",
            "C0_NO_PRIVATE_CONFLICT_SCORE_EFFECT",
        ],
    },
    "arm_b_high": {
        "label": "ARM B-HIGH - NON-NEGATING REPLACEMENT / COLLAPSE REGIME",
        "old": "My favorite game is Portal 2.",
        "correction": "My favorite game is Portal currently.",
        "query": "What is my favorite game?",
        "expected_regime": ">=0.92",
        "expected_detector": False,
        "prediction": [
            "S2_COLLAPSED_INTO_OLD_ROW",
            "L0_NO_LINK",
            "C0_NO_CONFLICT_RECORDED",
        ],
    },
    "arm_b_low": {
        "label": "ARM B-LOW - NON-NEGATING REPLACEMENT / COEXISTENCE REGIME",
        "old": "My favorite game is Dark Souls 3.",
        "correction": "My favorite game is Microsoft Flight Simulator currently.",
        "query": "What is my favorite game?",
        "expected_regime": "<0.88",
        "expected_detector": False,
        "prediction": [
            "S1_NEW_ROW_SPAWNED",
            "L0_NO_LINK",
            "C0_NO_CONFLICT_RECORDED",
        ],
    },
}


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
    status = run_cmd(["git", "status", "--short", "--branch"], cwd=root)
    head = run_cmd(["git", "rev-parse", "HEAD"], cwd=root)
    origin = run_cmd(["git", "rev-parse", "origin/main"], cwd=root)
    log = run_cmd(
        ["git", "log", "-1", "--format=%H%n%D%n%an <%ae>%n%aI%n%s"],
        cwd=root,
    )
    return {
        "status_short_branch": status,
        "head": head,
        "origin_main": origin,
        "log_1": log,
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


def jaccard(a: str, b: str) -> float:
    def toks(s: str) -> set[str]:
        return {t.strip(".,!?;:\"'()[]{}").lower() for t in s.split() if t.strip()}

    aa = toks(a)
    bb = toks(b)
    if not aa and not bb:
        return 1.0
    return float(len(aa & bb) / max(1, len(aa | bb)))


def regime(sim: float) -> str:
    if sim >= 0.92:
        return ">=0.92"
    if sim >= 0.88:
        return "0.88-0.92"
    return "<0.88"


def set_embedder_env(env: Dict[str, str]) -> None:
    env.update(
        {
            "TORMENT_PROFILE": "companion",
            "TORMENT_SQLITE_INDEX_ENABLE": "1",
            "TORMENT_CHARACTER_ENABLE": "1",
            "TORMENT_THINKING_ADVISORY": "1",
            "TORMENT_SPINE_ENABLE": "1",
            "TORMENT_IDENTITY_SENSITIVE": "1",
            "TORMENT_COMPRESS_ENABLE": "0",
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
            "OPENAI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
        }
    )


def calibrate_pairs(root: Path) -> Dict[str, Any]:
    env = os.environ
    set_embedder_env(env)  # This process only; service env is constructed separately.
    sys.path.insert(0, str(root))
    from torment_service.embeddings import build_embedder_from_env
    from torment_service.fabric import _detect_canon_conflict

    embedder = build_embedder_from_env()
    meta = {
        "provider": str(getattr(embedder, "provider", "")),
        "model": str(getattr(embedder, "model", "")),
        "dim": int(getattr(embedder, "dim", 0) or 0),
    }
    if meta != EXPECTED_EMBEDDER:
        raise StageStop(f"Calibration embedder mismatch: {meta} != {EXPECTED_EMBEDDER}")

    out: Dict[str, Any] = {"embedder": meta, "pairs": {}}
    for arm_name, arm in ARMS.items():
        old = arm["old"]
        correction = arm["correction"]
        vo = np.asarray(embedder.embed(old), dtype=np.float32).reshape(-1)
        vc = np.asarray(embedder.embed(correction), dtype=np.float32).reshape(-1)
        sim = float(np.dot(vo, vc) / ((np.linalg.norm(vo) + 1e-12) * (np.linalg.norm(vc) + 1e-12)))
        detected, conflict_score, reason_text = _detect_canon_conflict(correction, old, sim)
        pair_regime = regime(sim)
        rec = {
            "old": old,
            "correction": correction,
            "cosine": sim,
            "regime": pair_regime,
            "jaccard": jaccard(old, correction),
            "detector": bool(detected),
            "conflict_score": float(conflict_score),
            "detector_reason": str(reason_text),
        }
        if pair_regime != arm["expected_regime"]:
            raise StageStop(
                f"{arm_name} regime {pair_regime} differs from frozen {arm['expected_regime']}"
            )
        if bool(detected) != bool(arm["expected_detector"]):
            raise StageStop(
                f"{arm_name} detector {bool(detected)} differs from frozen {arm['expected_detector']}"
            )
        out["pairs"][arm_name] = rec
    return out


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


def wait_health(base_url: str, proc: subprocess.Popen[Any], timeout_s: float = 90.0) -> Dict[str, Any]:
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


def service_env(root: Path, basin: Path, arm_name: str) -> Dict[str, str]:
    env = os.environ.copy()
    set_embedder_env(env)
    env["TORMENT_DATA_DIR"] = str(basin)
    env["TORMENT_TEST_CONDITION"] = f"{LABEL}_{arm_name}"
    env["TORMENT_SERVER_LAUNCHER_PATH"] = str(Path(__file__).resolve())
    return env


def start_service(root: Path, basin: Path, arm_name: str, log_dir: Path) -> Tuple[subprocess.Popen[Any], str, int, Dict[str, Any], Dict[str, Any]]:
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = service_env(root, basin, arm_name)
    stdout_path = log_dir / "server.stdout.log"
    stderr_path = log_dir / "server.stderr.log"
    stdout_f = stdout_path.open("w", encoding="utf-8")
    stderr_f = stderr_path.open("w", encoding="utf-8")
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    proc = subprocess.Popen(
        [
            sys.executable,
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
        check = http_json(base_url, "GET", "/embedder/check", timeout=30.0)
        for source_name, meta in (("health", health.get("embedder", {})), ("embedder_check", check)):
            provider = str(meta.get("provider", ""))
            model = str(meta.get("model", ""))
            dim = int(meta.get("dim", 0) or 0)
            if provider != EXPECTED_EMBEDDER["provider"] or model != EXPECTED_EMBEDDER["model"] or dim != EXPECTED_EMBEDDER["dim"]:
                raise StageStop(f"{source_name} embedder mismatch: {meta}")
        config = http_json(base_url, "GET", "/config", timeout=10.0)
        return proc, base_url, port, health, {"embedder_check": check, "config": config}
    except Exception:
        stop_service(proc)
        raise


def stop_service(proc: subprocess.Popen[Any]) -> Dict[str, Any]:
    pid = int(proc.pid)
    already_gone = proc.poll() is not None
    if not already_gone:
        proc.terminate()
    try:
        proc.wait(timeout=15.0)
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
        proc.wait(timeout=15.0)
    for f in getattr(proc, "_torment_log_files", ()):
        try:
            f.close()
        except Exception:
            pass
    return {
        "pid": pid,
        "already_gone": bool(already_gone),
        "returncode": proc.returncode,
        "gone": proc.poll() is not None,
    }


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows


def private_dir(basin: Path) -> Path:
    return basin / "workspaces" / WORKSPACE_ID / "agents" / AGENT_ID / "private"


def domain_dir(basin: Path) -> Path:
    return basin / "workspaces" / WORKSPACE_ID / "domains" / DOMAIN_ID


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
    compact_latest = {}
    compact_records = {}
    for eid in relevant:
        row = latest.get(eid)
        if row is None:
            continue
        payload = row.get("payload", {}) or {}
        compact_latest[str(eid)] = {
            "eid": eid,
            "summary": payload.get("summary"),
            "type": payload.get("type"),
            "memory_class": payload.get("memory_class"),
            "embedding_checksum": payload.get("embedding_checksum"),
            "embedding_provider": payload.get("embedding_provider"),
            "embedding_model": payload.get("embedding_model"),
            "strength": payload.get("strength"),
            "reinforcement_count": payload.get("reinforcement_count", 0),
            "last_reinforced": payload.get("last_reinforced"),
            "last_reinforced_ts": payload.get("last_reinforced_ts"),
            "created_at": payload.get("created_at"),
            "created_ts": payload.get("created_ts"),
            "scope": payload.get("scope"),
            "domain_id": payload.get("domain_id"),
            "agent_id": payload.get("agent_id"),
            "canon": payload.get("canon"),
            "full_payload": payload,
        }
        compact_records[str(eid)] = {
            "count": len(records_by_eid.get(eid, [])),
            "records": records_by_eid.get(eid, []),
        }
    counts = {str(k): len(v) for k, v in sorted(records_by_eid.items())}
    return {
        "path": str(nodes_path),
        "exists": nodes_path.exists(),
        "total_records": len(rows),
        "distinct_eids": len(latest),
        "record_count_by_eid": counts,
        "latest_by_eid": compact_latest,
        "records_by_eid": compact_records,
    }


def conflict_snapshot(base_url: Optional[str], basin: Path) -> Dict[str, Any]:
    files = {
        "conflicts_jsonl": domain_dir(basin) / "conflicts.jsonl",
        "conflict_events_jsonl": domain_dir(basin) / "conflict_events.jsonl",
    }
    api: Optional[Dict[str, Any]] = None
    if base_url:
        api = http_json(
            base_url,
            "GET",
            f"/workspace/{WORKSPACE_ID}/domain/{DOMAIN_ID}/conflicts?status=any&limit=200",
            timeout=10.0,
        )
    return {
        "api": api,
        "files": {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "rows": read_jsonl(path),
            }
            for name, path in files.items()
        },
    }


def query_payload(query: str) -> Dict[str, Any]:
    return {
        "workspace_id": WORKSPACE_ID,
        "agent_id": AGENT_ID,
        "query": query,
        "top_k": 8,
        "domain_id": DOMAIN_ID,
        "peek_bridges": False,
        "explain": True,
        "continuity_debug": True,
    }


def ingest_payload(summary: str, step: int) -> Dict[str, Any]:
    return {
        "workspace_id": WORKSPACE_ID,
        "agent_id": AGENT_ID,
        "text": summary,
        "supplied_summary": summary,
        "step": int(step),
        "domain_id": DOMAIN_ID,
        "scope": "private",
    }


def normalize_hits(query_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    hits = []
    for idx, hit in enumerate(query_response.get("results", []) or [], start=1):
        explain = hit.get("explain", {}) or {}
        hits.append(
            {
                "rank": idx,
                "eid": hit.get("eid"),
                "summary": hit.get("summary"),
                "type": hit.get("type"),
                "memory_class": hit.get("memory_class"),
                "scope": hit.get("scope"),
                "score": hit.get("score"),
                "raw_score": hit.get("raw_score"),
                "final_score": hit.get("final_score"),
                "strength": hit.get("strength"),
                "confidence": hit.get("confidence"),
                "conflict_status": hit.get("conflict_status"),
                "conflict_ids": hit.get("conflict_ids"),
                "conflict_penalty": hit.get("conflict_penalty"),
                "explain": {
                    "sim": explain.get("sim"),
                    "strength": explain.get("strength"),
                    "recency_days": explain.get("recency_days"),
                    "motif_alignment": explain.get("motif_alignment"),
                    "contradiction_risk": explain.get("contradiction_risk"),
                    "conflict_penalty": explain.get("conflict_penalty"),
                    "conflict_status": explain.get("conflict_status"),
                    "conflict_ids": explain.get("conflict_ids"),
                    "thread_window_bonus": explain.get("thread_window_bonus"),
                    "final_score": hit.get("final_score"),
                    "memory_plan_lane": explain.get("memory_plan_lane"),
                    "lane_weight": explain.get("lane_weight"),
                    "lane_weight_applied": explain.get("lane_weight_applied"),
                },
                "full_hit": hit,
            }
        )
    return hits


def query_service(base_url: str, query: str) -> Dict[str, Any]:
    payload = query_payload(query)
    response = http_json(base_url, "POST", "/agent/query", payload, timeout=30.0)
    return {
        "request": payload,
        "response": response,
        "normalized_hits": normalize_hits(response),
        "_core_hits_in_count": response.get("_core_hits_in_count"),
    }


def find_hit(query_record: Dict[str, Any], eid: Optional[int]) -> Optional[Dict[str, Any]]:
    if eid is None:
        return None
    for hit in query_record.get("normalized_hits", []):
        try:
            if int(hit.get("eid")) == int(eid):
                return hit
        except Exception:
            continue
    return None


def relevant_conflicts(conflicts: Dict[str, Any], eids: Iterable[int]) -> List[Dict[str, Any]]:
    wanted = {int(e) for e in eids if int(e) > 0}
    rows = ((conflicts.get("api") or {}).get("items") or [])
    out = []
    for row in rows:
        try:
            pair = {int(row.get("eid_a")), int(row.get("eid_b"))}
        except Exception:
            continue
        if pair & wanted:
            out.append(row)
    return out


def summarize_query_pair(
    query_record: Dict[str, Any],
    old_eid: Optional[int],
    correction_eid: Optional[int],
) -> Dict[str, Any]:
    old_hit = find_hit(query_record, old_eid)
    correction_hit = find_hit(query_record, correction_eid)
    if old_eid is not None and correction_eid is not None and int(old_eid) == int(correction_eid):
        correction_hit = old_hit
    margin = None
    if old_hit is not None and correction_hit is not None and old_eid != correction_eid:
        margin = float(correction_hit["final_score"]) - float(old_hit["final_score"])
    return {
        "old_hit": old_hit,
        "correction_hit": correction_hit,
        "correction_minus_old_final_score": margin,
    }


def classify_storage(
    arm: Dict[str, Any],
    old_eid: Optional[int],
    correction_response: Dict[str, Any],
    nodes: Dict[str, Any],
) -> str:
    corr_eid = correction_response.get("eid")
    if not correction_response.get("stored", False):
        return "S3_SPAWN_REFUSED"
    if corr_eid is not None and old_eid is not None and int(corr_eid) == int(old_eid):
        return "S2_COLLAPSED_INTO_OLD_ROW"
    for latest in nodes.get("latest_by_eid", {}).values():
        if latest.get("summary") == arm["correction"]:
            return "S1_NEW_ROW_SPAWNED"
    return "S3_SPAWN_REFUSED"


def classify_linkage(conflicts: List[Dict[str, Any]]) -> str:
    if conflicts:
        return "L1_CONFLICT_LINK"
    return "L0_NO_LINK"


def classify_conflict_effect(conflicts: List[Dict[str, Any]], query_record: Dict[str, Any], relevant_eids: Iterable[int]) -> str:
    if not conflicts:
        return "C0_NO_CONFLICT_RECORDED"
    penalties = []
    statuses = []
    wanted = {int(e) for e in relevant_eids if int(e) > 0}
    for hit in query_record.get("normalized_hits", []):
        try:
            eid = int(hit.get("eid"))
        except Exception:
            continue
        if eid not in wanted:
            continue
        ex = hit.get("explain") or {}
        penalties.append(float(ex.get("conflict_penalty") or 0.0))
        statuses.append(ex.get("conflict_status"))
    nonzero = [p for p in penalties if p != 0.0]
    if not nonzero:
        return "C1_CONFLICT_RECORDED_NO_SCORE_EFFECT"
    if len(set(round(p, 8) for p in penalties)) <= 1:
        return "C2_CONFLICT_RECORDED_SYMMETRIC_PENALTY"
    return "C3_CONFLICT_RECORDED_ASYMMETRIC_PENALTY"


def classify_ranking(pair: Dict[str, Any], old_eid: Optional[int], correction_eid: Optional[int]) -> str:
    if old_eid is None or correction_eid is None or int(old_eid) == int(correction_eid):
        return "R5_ORDER_UNDEFINED"
    old_hit = pair.get("old_hit")
    corr_hit = pair.get("correction_hit")
    if old_hit is None or corr_hit is None:
        return "R5_ORDER_UNDEFINED"
    old_rank = int(old_hit["rank"])
    corr_rank = int(corr_hit["rank"])
    if old_rank < corr_rank:
        return "R3_STALE_FIRST"
    margin = pair.get("correction_minus_old_final_score")
    if margin is None:
        return "R5_ORDER_UNDEFINED"
    if corr_rank < old_rank and abs(float(margin)) <= 0.01:
        return "R1_CORRECTION_FIRST_MARGIN_LE_0.01_RECENCY_EXPLAINED"
    if corr_rank < old_rank:
        return "R2_CORRECTION_FIRST_MARGIN_GT_0.01_COMPONENT_ATTRIBUTED"
    return "R4_ORDER_UNSTABLE"


def classify_restart(post: Dict[str, str], restart: Dict[str, str]) -> str:
    keys = ("S", "L", "C", "R")
    changed = [k for k in keys if post.get(k) != restart.get(k)]
    if not changed:
        return "P1_RESTART_EQUIVALENT"
    if changed == ["R"]:
        return "P2_RESTART_CHANGES_ORDER_ONLY"
    return "P3_RESTART_CHANGES_STATE"


def classify_arm(
    arm: Dict[str, Any],
    old_eid: int,
    correction_response: Dict[str, Any],
    nodes_post: Dict[str, Any],
    conflicts_post: Dict[str, Any],
    query_post: Dict[str, Any],
    nodes_restart: Dict[str, Any],
    conflicts_restart: Dict[str, Any],
    query_restart: Dict[str, Any],
) -> Dict[str, Any]:
    corr_eid = correction_response.get("eid")
    corr_int = int(corr_eid) if corr_eid is not None else None
    relevant = [old_eid] + ([corr_int] if corr_int is not None else [])

    rel_conflicts_post = relevant_conflicts(conflicts_post, relevant)
    rel_conflicts_restart = relevant_conflicts(conflicts_restart, relevant)
    pair_post = summarize_query_pair(query_post, old_eid, corr_int)
    pair_restart = summarize_query_pair(query_restart, old_eid, corr_int)

    post = {
        "S": classify_storage(arm, old_eid, correction_response, nodes_post),
        "L": classify_linkage(rel_conflicts_post),
        "C": classify_conflict_effect(rel_conflicts_post, query_post, relevant),
        "R": classify_ranking(pair_post, old_eid, corr_int),
    }
    restart = {
        "S": classify_storage(arm, old_eid, correction_response, nodes_restart),
        "L": classify_linkage(rel_conflicts_restart),
        "C": classify_conflict_effect(rel_conflicts_restart, query_restart, relevant),
        "R": classify_ranking(pair_restart, old_eid, corr_int),
    }
    return {
        "post": post,
        "restart": restart,
        "P": classify_restart(post, restart),
        "tuple": [restart["S"], restart["L"], restart["C"], restart["R"], classify_restart(post, restart)],
        "query_pair_post": pair_post,
        "query_pair_restart": pair_restart,
        "relevant_conflicts_post": rel_conflicts_post,
        "relevant_conflicts_restart": rel_conflicts_restart,
    }


def run_arm(root: Path, output_root: Path, arm_name: str, arm: Dict[str, Any]) -> Dict[str, Any]:
    arm_dir = output_root / arm_name
    basin = arm_dir / "basin"
    logs = arm_dir / "logs"
    if basin.exists():
        shutil.rmtree(basin)
    logs.mkdir(parents=True, exist_ok=True)
    basin.mkdir(parents=True, exist_ok=True)

    record: Dict[str, Any] = {
        "arm_name": arm_name,
        "arm_label": arm["label"],
        "disposable_basin": str(basin),
        "workspace_id": WORKSPACE_ID,
        "agent_id": AGENT_ID,
        "domain_id": DOMAIN_ID,
        "frozen_payloads": {
            "old": ingest_payload(arm["old"], 1),
            "correction": ingest_payload(arm["correction"], 2),
            "query": query_payload(arm["query"]),
        },
        "service": {},
        "evidence": {},
    }

    proc: Optional[subprocess.Popen[Any]] = None
    proc2: Optional[subprocess.Popen[Any]] = None
    try:
        proc, base_url, port, health, startup = start_service(root, basin, arm_name, logs)
        record["service"]["initial"] = {
            "pid": proc.pid,
            "port": port,
            "base_url": base_url,
            "health": health,
            **startup,
        }

        old_req = ingest_payload(arm["old"], 1)
        old_resp = http_json(base_url, "POST", "/agent/ingest", old_req, timeout=60.0)
        if old_resp.get("path") != "fast":
            raise StageStop(f"{arm_name} old ingest path was not fast: {old_resp}")
        if not old_resp.get("stored") or old_resp.get("eid") is None:
            raise StageStop(f"{arm_name} old ingest did not store: {old_resp}")
        old_eid = int(old_resp["eid"])

        query_before = query_service(base_url, arm["query"])
        old_hit_before = find_hit(query_before, old_eid)
        if old_hit_before is None:
            raise StageStop(f"{arm_name} OLD fact was not retrieval-competent after OLD ingest")

        nodes_before = node_snapshot(basin, [old_eid])
        conflicts_before = conflict_snapshot(base_url, basin)

        corr_req = ingest_payload(arm["correction"], 2)
        corr_resp = http_json(base_url, "POST", "/agent/ingest", corr_req, timeout=60.0)
        if corr_resp.get("path") != "fast":
            raise StageStop(f"{arm_name} correction ingest path was not fast: {corr_resp}")

        corr_eid = corr_resp.get("eid")
        relevant = [old_eid] + ([int(corr_eid)] if corr_eid is not None else [])
        nodes_post = node_snapshot(basin, relevant)
        conflicts_post = conflict_snapshot(base_url, basin)
        query_post = query_service(base_url, arm["query"])

        stop_initial = stop_service(proc)
        proc = None

        proc2, base_url2, port2, health2, startup2 = start_service(root, basin, f"{arm_name}_restart", logs)
        record["service"]["restart"] = {
            "pid": proc2.pid,
            "port": port2,
            "base_url": base_url2,
            "health": health2,
            **startup2,
        }
        query_after_restart = query_service(base_url2, arm["query"])
        nodes_after_restart = node_snapshot(basin, relevant)
        conflicts_after_restart = conflict_snapshot(base_url2, basin)
        stop_restart = stop_service(proc2)
        proc2 = None

        classification = classify_arm(
            arm,
            old_eid,
            corr_resp,
            nodes_post,
            conflicts_post,
            query_post,
            nodes_after_restart,
            conflicts_after_restart,
            query_after_restart,
        )

        record["evidence"] = {
            "old_ingest": {"request": old_req, "response": old_resp},
            "query_after_old": query_before,
            "old_retrieval_competent": True,
            "old_retrieval_hit": old_hit_before,
            "pre_correction_nodes": nodes_before,
            "pre_correction_conflicts": conflicts_before,
            "correction_ingest": {"request": corr_req, "response": corr_resp},
            "post_correction_nodes": nodes_post,
            "post_correction_conflicts": conflicts_post,
            "query_after_correction": query_post,
            "service_stop_after_correction": stop_initial,
            "query_after_restart": query_after_restart,
            "nodes_after_restart": nodes_after_restart,
            "conflicts_after_restart": conflicts_after_restart,
            "service_stop_after_restart": stop_restart,
            "classification": classification,
        }
        return record
    finally:
        if proc is not None:
            record.setdefault("cleanup", {})["initial"] = stop_service(proc)
        if proc2 is not None:
            record.setdefault("cleanup", {})["restart"] = stop_service(proc2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()

    root = repo_root()
    pre_git = ensure_authorized_head(root)
    calibration = calibrate_pairs(root)
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_root = root / "outputs" / "lived_use" / LABEL / run_id
    output_root.mkdir(parents=True, exist_ok=True)

    result: Dict[str, Any] = {
        "label": LABEL,
        "run_id": run_id,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "pre_git": pre_git,
        "calibration": calibration,
        "arms": {},
        "stop_condition": None,
    }

    evidence_path = output_root / "stage1_evidence.json"
    try:
        for arm_name, arm in ARMS.items():
            result["arms"][arm_name] = run_arm(root, output_root, arm_name, arm)
        result["execution_verdict"] = "COMPLETED"
    except Exception as exc:
        result["execution_verdict"] = "STOPPED"
        result["stop_condition"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        try:
            result["post_git"] = git_snapshot(root)
        except Exception as exc:
            result["post_git_error"] = f"{type(exc).__name__}: {exc}"
        with evidence_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=True, default=str)

    print(json.dumps({"ok": True, "evidence_path": str(evidence_path)}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StageStop as exc:
        print(json.dumps({"ok": False, "stop_condition": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(2)
