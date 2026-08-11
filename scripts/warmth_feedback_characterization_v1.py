from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from torment_service.compression import (  # noqa: E402
    COMPRESS_LONG_PATH_STRENGTH,
    CompressionExecutor,
    CompressionRouter,
    CompressionScorer,
)
from torment_service.deep_memory import DeepMemoryStore  # noqa: E402
from torment_service.embedding_store import load_embedding  # noqa: E402
from torment_service.fabric import TormentFabric  # noqa: E402
from torment_service.memory_graph import MemoryGraph  # noqa: E402
from torment_service.retrieval_assembler import FILL_ORDER, assemble_context  # noqa: E402


LABEL = "warmth_feedback_characterization_v1"
EXPERIMENT_LABEL = "WARMTH_FEEDBACK_CHARACTERIZATION_V1"
EXPERIMENT_SUBTYPE = "POST_ELIGIBILITY_WARMTH_STATE_AND_COMPETITION_CHARACTERIZATION"
AUTHORIZED_HEAD = "872d95d2e30928e45bcc7dce598df3ec8758140a"
AUTHORIZED_SUBJECT = "test(lived-use): preserve duplicate surface characterization"

AGENT_ID = "warmth_feedback_agent"
SOURCE_BORN_STEP = 0
COMPRESSION_STEP = 1000
DEEP_MIN_SIMILARITY = 0.4
TARGET_QUERY = "copper locket pine clock before sunrise"
HASH_DIM = 384
WARMUP_PRE_CALLS_FOR_WARM_PROBE = 4


class StageStop(RuntimeError):
    pass


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
        "log_1_oneline": run_cmd(["git", "log", "-1", "--oneline"], cwd=root),
        "production_status": run_cmd(
            ["git", "status", "--short", "--", "torment_service"], cwd=root
        ),
    }


def ensure_authorized_baseline(root: Path) -> Dict[str, Any]:
    snap = git_snapshot(root)
    if snap["head"] != AUTHORIZED_HEAD:
        raise StageStop(f"HEAD {snap['head']} differs from authorized {AUTHORIZED_HEAD}")
    if snap["origin_main"] != AUTHORIZED_HEAD:
        raise StageStop(
            f"origin/main {snap['origin_main']} differs from authorized {AUTHORIZED_HEAD}"
        )
    if AUTHORIZED_SUBJECT not in snap["log_1_oneline"]:
        raise StageStop(
            f"HEAD subject differs from authorized subject: {snap['log_1_oneline']}"
        )
    if snap["production_status"].strip():
        raise StageStop(f"Production files modified before run:\n{snap['production_status']}")
    return snap


@contextmanager
def scoped_env(updates: Dict[str, str]) -> Iterable[None]:
    old: Dict[str, Optional[str]] = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def pad_words(prefix: str, target_words: int) -> str:
    words = prefix.split()
    fillers = [
        "lantern", "cedar", "archive", "morning", "quiet", "ledger", "silver",
        "harbor", "stone", "paper", "north", "garden", "amber", "table",
        "thread", "window", "river", "canvas", "field", "marker",
    ]
    idx = 0
    while len(words) < target_words:
        words.append(f"{fillers[idx % len(fillers)]}_{idx}")
        idx += 1
    return " ".join(words) + "."


def target_source_summary() -> str:
    prefix = (
        "Warmth target episode: "
        + ((TARGET_QUERY + " ") * 35)
        + "Mira wrote the placement into the local memory ledger."
    )
    return pad_words(prefix, 320)


def layer_ab_source_summary() -> str:
    prefix = (
        "Warmth recurrence episode: the copper locket was left beneath the pine clock "
        "before sunrise. The detail is intentionally stable for repeated production "
        "retrieval through the deep lane."
    )
    return pad_words(prefix, 90)


def source_payload_extra(workspace_id: str, *, role: str, fixed_ts: int) -> Dict[str, Any]:
    return {
        "workspace_id": workspace_id,
        "agent_id": AGENT_ID,
        "scope": "private",
        "domain_id": "personal",
        "created_ts": int(fixed_ts),
        "experiment_label": EXPERIMENT_LABEL,
        "fixture_role": role,
    }


def norm_cosine(a: Any, b: Any) -> Optional[float]:
    if a is None or b is None:
        return None
    av = np.asarray(a, dtype=np.float32).reshape(-1)
    bv = np.asarray(b, dtype=np.float32).reshape(-1)
    if av.shape[0] != bv.shape[0]:
        return None
    denom = float(np.linalg.norm(av) * np.linalg.norm(bv) + 1e-12)
    return float(np.dot(av, bv) / denom)


def vector_digest(vec: Any) -> Optional[str]:
    if vec is None:
        return None
    arr = np.asarray(vec, dtype=np.float32).reshape(-1)
    return hashlib.sha256(arr.tobytes()).hexdigest()


def warmup_path(data_root: Path, workspace_id: str, agent_id: str) -> Path:
    return (
        data_root
        / "workspaces"
        / workspace_id
        / "agents"
        / agent_id
        / "warmup"
        / "warmup_state.jsonl"
    )


def read_warmup_state(
    data_root: Path, workspace_id: str, agent_id: str, eid: int
) -> Dict[str, Any]:
    path = warmup_path(data_root, workspace_id, agent_id)
    records: List[Dict[str, Any]] = []
    latest_by_eid: Dict[int, Dict[str, Any]] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                item["_line_number"] = line_number
                records.append(item)
                latest_by_eid[int(item.get("eid", -1))] = item
    latest = latest_by_eid.get(int(eid))
    return {
        "reader_boundary": "direct_jsonl_non_mutating_reader",
        "warmup_file": str(path.resolve()),
        "file_exists": path.exists(),
        "records_total": len(records),
        "records_for_eid": [r for r in records if int(r.get("eid", -1)) == int(eid)],
        "exists_for_eid": latest is not None,
        "latest_for_eid": latest,
        "appearance_count": (
            int(latest.get("appearance_count", 0)) if latest is not None else None
        ),
        "current_warmth": (
            float(latest.get("current_warmth", 0.0)) if latest is not None else None
        ),
        "first_appearance_step": (
            int(latest.get("first_appearance_step", 0)) if latest is not None else None
        ),
        "last_retrieved_step": (
            int(latest.get("last_retrieved_step", 0)) if latest is not None else None
        ),
        "max_warmth": (
            float(latest.get("max_warmth", 0.0)) if latest is not None else None
        ),
    }


def comparable_warmth(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    keys = [
        "exists_for_eid",
        "appearance_count",
        "current_warmth",
        "first_appearance_step",
        "last_retrieved_step",
        "max_warmth",
        "records_total",
    ]
    return {k: a.get(k) for k in keys} == {k: b.get(k) for k in keys}


def spawn_private_memory(
    *,
    fabric: TormentFabric,
    workspace_id: str,
    summary: str,
    strength: float,
    role: str,
    fixed_ts: int,
    step: int = SOURCE_BORN_STEP,
    memory_class: str = "core",
) -> Tuple[int, str]:
    fabric.create_agent(workspace_id, AGENT_ID)
    ak = fabric._agent_key(workspace_id, AGENT_ID)
    graph = fabric.private_graphs[ak]
    embedding = fabric.kernel.embedder.embed(summary)
    eid = graph.spawn_memory(
        summary=summary,
        embedding=embedding,
        mtype="episode",
        strength=float(strength),
        confidence=0.9,
        half_life_days=1.0,
        links=[],
        canon=False,
        user_id=AGENT_ID,
        step=int(step),
        memory_class=memory_class,
        extra_payload=source_payload_extra(workspace_id, role=role, fixed_ts=fixed_ts),
    )
    graph.flush_node(eid)
    private_dir = str(Path(graph.data_dir).resolve())
    fabric.private_graphs[ak] = MemoryGraph(private_dir, embedder=fabric.kernel.embedder)
    return int(eid), private_dir


def create_source_and_deep_state(
    *,
    fabric: TormentFabric,
    data_root: Path,
    workspace_id: str,
    summary: str,
    fixed_ts: int,
    source_strength: float = 0.05,
) -> Dict[str, Any]:
    eid, private_dir = spawn_private_memory(
        fabric=fabric,
        workspace_id=workspace_id,
        summary=summary,
        strength=source_strength,
        role="target_source_for_deep_export",
        fixed_ts=fixed_ts,
        memory_class="core",
    )
    ak = fabric._agent_key(workspace_id, AGENT_ID)
    graph = fabric.private_graphs[ak]
    ent = graph.entities.get(int(eid))
    if ent is None:
        raise StageStop(f"{workspace_id}: source disappeared before compression")
    payload = dict(ent.payload or {})
    if str(payload.get("summary", "")) != summary:
        raise StageStop(f"{workspace_id}: source summary changed before compression")

    node = {
        "eid": int(eid),
        "born_step": int(getattr(ent, "born_step", 0) or 0),
        "payload": payload,
    }
    candidate = CompressionScorer().score(node, COMPRESSION_STEP, coherence_field=None)
    if candidate is None:
        raise StageStop(f"{workspace_id}: compression candidate is None")
    route = CompressionRouter().route(candidate, COMPRESSION_STEP)
    candidate.route = route
    if route != "long_path":
        raise StageStop(f"{workspace_id}: intended long_path fixture routed {route!r}")

    deep_dir = (
        data_root / "workspaces" / workspace_id / "agents" / AGENT_ID / "deep_memory"
    ).resolve()
    deep_store = DeepMemoryStore(str(deep_dir), trusted_root=str(data_root.resolve()))
    executor = CompressionExecutor(graph, deep_store)
    event = executor.execute([candidate], COMPRESSION_STEP, LABEL)
    try:
        deep_store.close()
    except Exception:
        pass
    if event.exported_deep != 1:
        raise StageStop(f"{workspace_id}: expected one deep export, got {event.exported_deep}")

    fabric.private_graphs[ak] = MemoryGraph(private_dir, embedder=fabric.kernel.embedder)
    graph = fabric.private_graphs[ak]
    ent = graph.entities.get(int(eid))
    if ent is None:
        raise StageStop(f"{workspace_id}: source disappeared after compression")
    post_payload = dict(ent.payload or {})
    if str(post_payload.get("summary", "")) != summary:
        raise StageStop(f"{workspace_id}: source summary unexpectedly changed")
    if not post_payload.get("exported_deep"):
        raise StageStop(f"{workspace_id}: source lacks exported_deep marker")
    if abs(float(post_payload.get("strength", -1.0)) - float(COMPRESS_LONG_PATH_STRENGTH)) > 1e-9:
        raise StageStop(f"{workspace_id}: long_path source strength changed unexpectedly")

    fresh_deep = DeepMemoryStore(str(deep_dir), trusted_root=str(data_root.resolve()))
    deep_record = fresh_deep.recall(eid)
    if deep_record is None:
        raise StageStop(f"{workspace_id}: deep persistence cannot be reloaded")
    deep_dict = deep_record.to_dict()
    try:
        fresh_deep.close()
    except Exception:
        pass

    return {
        "workspace_id": workspace_id,
        "agent_id": AGENT_ID,
        "ak": ak,
        "source_eid": int(eid),
        "private_dir": private_dir,
        "deep_dir": str(deep_dir),
        "source_summary": summary,
        "source_summary_length": len(summary),
        "compression_candidate": {**asdict(candidate), "summary_length": len(candidate.summary)},
        "router_result": route,
        "compression_event": event.to_dict(),
        "source_after_long_path": source_snapshot(
            data_root=data_root,
            workspace_id=workspace_id,
            eid=int(eid),
        ),
        "deep_record": deep_dict,
    }


def add_competitor_memory(
    *,
    fabric: TormentFabric,
    data_root: Path,
    workspace_id: str,
    summary: str,
    strength: float,
    fixed_ts: int,
) -> Dict[str, Any]:
    eid, _private_dir = spawn_private_memory(
        fabric=fabric,
        workspace_id=workspace_id,
        summary=summary,
        strength=float(strength),
        role="layer_c_competitor",
        fixed_ts=fixed_ts,
        memory_class="core",
    )
    return source_snapshot(data_root=data_root, workspace_id=workspace_id, eid=int(eid))


def source_snapshot(*, data_root: Path, workspace_id: str, eid: int) -> Dict[str, Any]:
    fabric = TormentFabric(str(data_root))
    try:
        fabric.create_agent(workspace_id, AGENT_ID)
        ak = fabric._agent_key(workspace_id, AGENT_ID)
        graph = fabric.private_graphs[ak]
        ent = graph.entities.get(int(eid))
        if ent is None:
            raise StageStop(f"{workspace_id}: source eid={eid} missing")
        payload = dict(ent.payload or {})
        emb = load_embedding(eid, payload, graph._shard_reader, graph.data_dir)
        return {
            "eid": int(eid),
            "born_step": int(getattr(ent, "born_step", 0) or 0),
            "payload": payload,
            "summary": str(payload.get("summary", "")),
            "summary_length": len(str(payload.get("summary", ""))),
            "strength": float(payload.get("strength", 0.0) or 0.0),
            "created_ts": int(payload.get("created_ts", 0) or 0),
            "last_reinforced": int(payload.get("last_reinforced", 0) or 0),
            "embedding_digest": vector_digest(emb),
            "compression_metadata": {
                "exported_deep": bool(payload.get("exported_deep", False)),
                "exported_step": payload.get("exported_step"),
                "compression_route": payload.get("compression_route"),
                "compression_score": payload.get("compression_score"),
                "compression_tier": payload.get("compression_tier"),
            },
        }
    finally:
        try:
            fabric.close()
        except Exception:
            pass


def source_comparable_subset(snap: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(snap.get("payload") or {})
    return {
        "summary": snap.get("summary"),
        "strength": snap.get("strength"),
        "created_ts": snap.get("created_ts"),
        "last_reinforced": snap.get("last_reinforced"),
        "embedding_digest": snap.get("embedding_digest"),
        "compression_metadata": snap.get("compression_metadata"),
        "type": payload.get("type"),
        "memory_class": payload.get("memory_class"),
        "confidence": payload.get("confidence"),
        "half_life": payload.get("half_life"),
        "user_id": payload.get("user_id"),
        "fixture_role": payload.get("fixture_role"),
    }


def compute_deep_diagnostics(
    *,
    fabric: TormentFabric,
    data_root: Path,
    workspace_id: str,
    query: str,
    top_k: int,
    target_eid: int,
) -> Dict[str, Any]:
    ak = fabric._agent_key(workspace_id, AGENT_ID)
    fabric.create_agent(workspace_id, AGENT_ID)
    graph = fabric.private_graphs[ak]
    qemb = fabric.kernel.embedder.embed(query)
    private_hits = graph.search(query, top_k=top_k, user_id=AGENT_ID)
    private_count = len(private_hits)
    shared_count = 0
    deep_headroom = max(0, int(top_k) - private_count - shared_count)

    deep_dir = data_root / "workspaces" / workspace_id / "agents" / AGENT_ID / "deep_memory"
    deep_store = DeepMemoryStore(str(deep_dir.resolve()), trusted_root=str(data_root.resolve()))
    try:
        deep_record = deep_store.recall(target_eid)
        if deep_record is None:
            raise StageStop(f"{workspace_id}: deep record missing during diagnostics")
        deep_emb = None
        if deep_record.embedding_ref is not None and deep_store._shard_reader is not None:
            deep_emb = deep_store._shard_reader.load_one(deep_record.embedding_ref)
        deep_similarity = norm_cosine(deep_emb, qemb)
        direct_results = []
        if deep_headroom > 0:
            for dm in deep_store.query(
                np.asarray(qemb, dtype=np.float32).reshape(-1),
                top_k=max(1, deep_headroom),
                min_similarity=DEEP_MIN_SIMILARITY,
            ):
                direct_results.append(int(dm.eid))
    finally:
        try:
            deep_store.close()
        except Exception:
            pass

    source_present = int(target_eid) in graph.entities
    deep_similarity_passes = (
        deep_similarity is not None and float(deep_similarity) >= DEEP_MIN_SIMILARITY
    )
    return {
        "diagnostic_boundary": (
            "manual cosine plus DeepMemoryStore.query only; does not call "
            "TormentFabric._query_deep_lane and does not mutate warmth"
        ),
        "query": query,
        "top_k": int(top_k),
        "private_raw_hit_count": private_count,
        "shared_raw_hit_count": shared_count,
        "deep_headroom": deep_headroom,
        "deep_similarity": deep_similarity,
        "deep_min_similarity": DEEP_MIN_SIMILARITY,
        "deep_similarity_passes_min": bool(deep_similarity_passes),
        "source_beta_filter_status": "PASS" if source_present else "FAIL_SOURCE_ABSENT",
        "direct_deep_store_query_eids": direct_results,
        "target_in_direct_deep_query": int(target_eid) in direct_results,
        "deep_eligible": bool(
            deep_headroom > 0 and deep_similarity_passes and source_present
        ),
        "private_raw_hits": [
            {
                "eid": h.get("eid"),
                "score": h.get("score"),
                "raw_score": h.get("raw_score"),
                "summary": h.get("summary"),
                "strength": h.get("strength"),
                "fixture_role": h.get("fixture_role"),
            }
            for h in private_hits
        ],
    }


def classify_hit_kind(hit: Dict[str, Any], target_eid: int, competitor_eid: Optional[int]) -> str:
    eid = int(hit.get("eid", -1))
    is_deep = bool(hit.get("from_spirit_return") or hit.get("deep_memory"))
    if eid == int(target_eid) and is_deep:
        return "target_deep"
    if eid == int(target_eid):
        return "target_source"
    if competitor_eid is not None and eid == int(competitor_eid):
        return "competitor_source"
    return "other"


def project_hit(
    hit: Dict[str, Any],
    *,
    target_eid: int,
    competitor_eid: Optional[int],
    order_index: int,
) -> Dict[str, Any]:
    return {
        "order_index": int(order_index),
        "rank_1_based": int(order_index) + 1,
        "hit_kind": classify_hit_kind(hit, target_eid, competitor_eid),
        "eid": hit.get("eid"),
        "scope": hit.get("scope", "private"),
        "type": hit.get("type"),
        "memory_class": hit.get("memory_class"),
        "fixture_role": hit.get("fixture_role"),
        "summary": hit.get("summary"),
        "score": hit.get("score"),
        "raw_score": hit.get("raw_score"),
        "final_score": hit.get("final_score"),
        "strength": hit.get("strength"),
        "confidence": hit.get("confidence"),
        "from_spirit_return": bool(hit.get("from_spirit_return")),
        "deep_memory": bool(hit.get("deep_memory")),
        "spirit_return_mode": hit.get("spirit_return_mode"),
        "spirit_return_flavor": hit.get("spirit_return_flavor"),
        "warmth_score": hit.get("warmth_score"),
        "authority_status": hit.get("authority_status"),
        "provenance_type": hit.get("provenance_type"),
        "explain": hit.get("explain"),
    }


def flatten_blocks(
    assembled_dict: Dict[str, Any],
    *,
    target_eid: int,
    competitor_eid: Optional[int],
) -> List[Dict[str, Any]]:
    blocks = assembled_dict.get("blocks") or {}
    flat: List[Dict[str, Any]] = []
    order_keys = list(FILL_ORDER) + [k for k in blocks.keys() if k not in FILL_ORDER]
    order_index = 0
    for block_type in order_keys:
        for block in blocks.get(block_type, []) or []:
            metadata = block.get("metadata") or {}
            pseudo_hit = {
                "eid": block.get("eid"),
                "from_spirit_return": metadata.get("from_spirit_return"),
                "deep_memory": metadata.get("from_spirit_return"),
            }
            flat.append(
                {
                    "order_index": order_index,
                    "rank_1_based": order_index + 1,
                    "block_kind": classify_hit_kind(pseudo_hit, target_eid, competitor_eid),
                    "block_type": block.get("block_type"),
                    "eid": block.get("eid"),
                    "score": block.get("score"),
                    "token_count": block.get("token_count"),
                    "reason": block.get("reason"),
                    "text": block.get("text"),
                    "metadata": metadata,
                    "from_spirit_return": bool(metadata.get("from_spirit_return")),
                    "warmth_score": metadata.get("warmth_score"),
                    "spirit_return_mode": metadata.get("spirit_return_mode"),
                }
            )
            order_index += 1
    return flat


def run_authoritative_observation(
    *,
    fabric: TormentFabric,
    data_root: Path,
    workspace_id: str,
    observation_id: str,
    query: str,
    top_k: int,
    token_budget: int,
    target_eid: int,
    competitor_eid: Optional[int] = None,
) -> Dict[str, Any]:
    pre_warmth = read_warmup_state(data_root, workspace_id, AGENT_ID, target_eid)
    diagnostics = compute_deep_diagnostics(
        fabric=fabric,
        data_root=data_root,
        workspace_id=workspace_id,
        query=query,
        top_k=top_k,
        target_eid=target_eid,
    )
    after_diag_warmth = read_warmup_state(data_root, workspace_id, AGENT_ID, target_eid)
    if not comparable_warmth(pre_warmth, after_diag_warmth):
        raise StageStop(f"{observation_id}: diagnostic inspection mutated warmth")

    fabric_result = fabric.query(
        workspace_id=workspace_id,
        agent_id=AGENT_ID,
        query_text=query,
        top_k=int(top_k),
        domain_id=None,
        peek_bridges=False,
        explain=True,
        continuity_debug=False,
        memory_plan=None,
    )
    core_hits = list(fabric_result.get("results") or [])
    assembled = assemble_context(
        core_hits=core_hits,
        archive_hits=[],
        profile="companion",
        token_budget=int(token_budget),
        seed_text="",
        character_name="",
        drift_info=None,
        custom_weights=None,
    )
    assembled_dict = assembled.to_dict()
    post_warmth = read_warmup_state(data_root, workspace_id, AGENT_ID, target_eid)

    projected_hits = [
        project_hit(
            hit,
            target_eid=target_eid,
            competitor_eid=competitor_eid,
            order_index=idx,
        )
        for idx, hit in enumerate(core_hits)
    ]
    projected_blocks = flatten_blocks(
        assembled_dict,
        target_eid=target_eid,
        competitor_eid=competitor_eid,
    )
    rendered_context = str(assembled_dict.get("assembled_text") or "")
    deep_hits = [h for h in projected_hits if h["hit_kind"] == "target_deep"]
    deep_blocks = [b for b in projected_blocks if b["block_kind"] == "target_deep"]
    deep_rendered = any(
        str(b.get("text") or "") and str(b.get("text") or "") in rendered_context
        for b in deep_blocks
    )
    pre_count = pre_warmth.get("appearance_count")
    post_count = post_warmth.get("appearance_count")
    warmed = (
        post_warmth.get("exists_for_eid")
        and (
            pre_count is None
            or post_count is None
            or int(post_count) > int(pre_count)
        )
    )
    return {
        "observation_id": observation_id,
        "workspace_id": workspace_id,
        "agent_id": AGENT_ID,
        "query": query,
        "top_k": int(top_k),
        "token_budget": int(token_budget),
        "pre_warmth": pre_warmth,
        "deep_eligibility_diagnostics": diagnostics,
        "post_diagnostic_warmth": after_diag_warmth,
        "fabric_final_hits": projected_hits,
        "fabric_excluded": fabric_result.get("excluded"),
        "fabric_filter_excluded": fabric_result.get("filter_excluded"),
        "assembled_structured_blocks": projected_blocks,
        "assembler_selection_log": assembled_dict.get("selection_log"),
        "rendered_context": rendered_context,
        "post_warmth": post_warmth,
        "stage_flags": {
            "DEEP_ELIGIBLE": bool(diagnostics.get("deep_eligible")),
            "DEEP_WARMED": bool(warmed),
            "DEEP_FINAL_HIT": bool(deep_hits),
            "DEEP_STRUCTURED_BLOCK": bool(deep_blocks),
            "DEEP_RENDERED_CONTEXT": bool(deep_rendered),
        },
        "deep_observation": deep_hits[0] if deep_hits else None,
        "competitor_observation": next(
            (h for h in projected_hits if h["hit_kind"] == "competitor_source"),
            None,
        ),
    }


def build_fabric(data_root: Path) -> TormentFabric:
    return TormentFabric(str(data_root.resolve()))


def run_layer_a(run_dir: Path, fixed_ts: int) -> Dict[str, Any]:
    workspace_id = "layer_a_warmth_state_machine"
    data_root = (run_dir / "layer_a" / "data").resolve()
    data_root.mkdir(parents=True, exist_ok=True)
    fabric = build_fabric(data_root)
    reconstructed_after_call = 3
    observations: List[Dict[str, Any]] = []
    reconstruction_events: List[Dict[str, Any]] = []
    try:
        state = create_source_and_deep_state(
            fabric=fabric,
            data_root=data_root,
            workspace_id=workspace_id,
            summary=layer_ab_source_summary(),
            fixed_ts=fixed_ts,
        )
        source_eid = int(state["source_eid"])
        fresh_warmth = read_warmup_state(data_root, workspace_id, AGENT_ID, source_eid)
        if fresh_warmth["exists_for_eid"]:
            raise StageStop("Layer A fresh condition already has warmth")

        for call_index in range(1, 9):
            if call_index == reconstructed_after_call + 1:
                before = read_warmup_state(data_root, workspace_id, AGENT_ID, source_eid)
                try:
                    fabric.close()
                except Exception:
                    pass
                fabric = build_fabric(data_root)
                after_construct = read_warmup_state(data_root, workspace_id, AGENT_ID, source_eid)
                reconstruction_events.append(
                    {
                        "after_completed_call": reconstructed_after_call,
                        "reconstruction_type": "same_python_process_object_reconstruction",
                        "true_fresh_process_restart": False,
                        "warmth_before_reconstruction": before,
                        "warmth_after_object_reconstruction_before_query": after_construct,
                    }
                )
                if not comparable_warmth(before, after_construct):
                    raise StageStop("Layer A reconstruction changed persisted warmth state")

            observations.append(
                run_authoritative_observation(
                    fabric=fabric,
                    data_root=data_root,
                    workspace_id=workspace_id,
                    observation_id=f"A{call_index:02d}",
                    query=str(state["source_summary"]),
                    top_k=2,
                    token_budget=4000,
                    target_eid=source_eid,
                )
            )
    finally:
        try:
            fabric.close()
        except Exception:
            pass

    sequence = [
        {
            "call": idx + 1,
            "appearance_count": obs["post_warmth"].get("appearance_count"),
            "current_warmth": obs["post_warmth"].get("current_warmth"),
            "first_appearance_step": obs["post_warmth"].get("first_appearance_step"),
            "last_retrieved_step": obs["post_warmth"].get("last_retrieved_step"),
            "spirit_return_mode": (
                obs.get("deep_observation") or {}
            ).get("spirit_return_mode"),
            "spirit_return_strength": (obs.get("deep_observation") or {}).get("strength"),
            "warmth_score": (obs.get("deep_observation") or {}).get("warmth_score"),
            "deep_final_score": (obs.get("deep_observation") or {}).get("final_score"),
            "deep_final_rank": (obs.get("deep_observation") or {}).get("rank_1_based"),
            "deep_rendered": obs["stage_flags"]["DEEP_RENDERED_CONTEXT"],
        }
        for idx, obs in enumerate(observations)
    ]
    expected_first_seven = [0.2, 0.35, 0.5, 0.65, 0.8, 0.95, 1.0]
    actual_first_seven = [round(float(r["current_warmth"]), 10) for r in sequence[:7]]
    recurrence_demo = actual_first_seven == expected_first_seven
    cap_demo = (
        len(sequence) >= 8
        and round(float(sequence[6]["current_warmth"]), 10) == 1.0
        and round(float(sequence[7]["current_warmth"]), 10) == 1.0
    )
    persistence_demo = bool(
        reconstruction_events
        and sequence[2]["appearance_count"] == 3
        and sequence[3]["appearance_count"] == 4
    )
    return {
        "layer": "A_WARMTH_STATE_MACHINE",
        "workspace_id": workspace_id,
        "data_root": str(data_root),
        "source_and_deep_state": state,
        "observations": observations,
        "recurrence_table": sequence,
        "restart_reconstruction_observations": reconstruction_events,
        "window_reset_observation": {
            "WINDOW_RESET_BEHAVIOR": "CODE_TRACED_NOT_EXPERIMENTALLY_CHARACTERIZED",
            "reason": (
                "No bounded production-compatible step advancement was used; the "
                "harness did not edit first_appearance_step, last_retrieved_step, "
                "current_warmth, or canonical step state."
            ),
        },
        "layer_taxonomy": {
            "WARMTH_RECURRENCE": "DEMONSTRATED" if recurrence_demo else "NOT_DEMONSTRATED",
            "WARMTH_CAP_AT_1_0": "DEMONSTRATED" if cap_demo else "NOT_DEMONSTRATED",
            "WARMTH_PERSISTS_ACROSS_RECONSTRUCTION": (
                "DEMONSTRATED" if persistence_demo else "NOT_DEMONSTRATED"
            ),
            "WINDOW_RESET_BEHAVIOR": "CODE_TRACED_NOT_EXPERIMENTALLY_CHARACTERIZED",
            "FIRST_CALL_WARMTH_AFFECTS_SAME_CALL_POST_ELIGIBILITY_STATE": (
                "DEMONSTRATED"
                if observations
                and observations[0]["stage_flags"]["DEEP_WARMED"]
                and observations[0].get("deep_observation") is not None
                else "NOT_DEMONSTRATED"
            ),
        },
    }


def run_layer_b(run_dir: Path, fixed_ts: int) -> Dict[str, Any]:
    workspace_id = "layer_b_pre_final_mutation"
    data_root = (run_dir / "layer_b" / "data").resolve()
    data_root.mkdir(parents=True, exist_ok=True)
    fabric = build_fabric(data_root)
    try:
        state = create_source_and_deep_state(
            fabric=fabric,
            data_root=data_root,
            workspace_id=workspace_id,
            summary=layer_ab_source_summary(),
            fixed_ts=fixed_ts,
        )
        source_eid = int(state["source_eid"])
        fresh_warmth = read_warmup_state(data_root, workspace_id, AGENT_ID, source_eid)
        if fresh_warmth["exists_for_eid"]:
            raise StageStop("Layer B fresh condition already has warmth")
        obs = run_authoritative_observation(
            fabric=fabric,
            data_root=data_root,
            workspace_id=workspace_id,
            observation_id="B01_TINY_CONTEXT_BUDGET",
            query=str(state["source_summary"]),
            top_k=2,
            token_budget=1,
            target_eid=source_eid,
        )
    finally:
        try:
            fabric.close()
        except Exception:
            pass
    warmed = obs["stage_flags"]["DEEP_WARMED"]
    rendered = obs["stage_flags"]["DEEP_RENDERED_CONTEXT"]
    requires_rendered = (
        "CONTRADICTED"
        if warmed and not rendered
        else ("DEMONSTRATED" if warmed and rendered else "NOT_DEMONSTRATED")
    )
    appearance_equals_rendered = (
        "CONTRADICTED"
        if warmed and not rendered
        else ("DEMONSTRATED" if warmed and rendered else "NOT_DEMONSTRATED")
    )
    return {
        "layer": "B_PRE_FINAL_WARMTH_MUTATION_SEMANTICS",
        "workspace_id": workspace_id,
        "data_root": str(data_root),
        "source_and_deep_state": state,
        "observation": obs,
        "classification": {
            "PRE_FINAL_MUTATION_SEMANTICS": "EXPERIMENTALLY_ISOLATED",
            "WARMTH_MUTATION_REQUIRES_RENDERED_SURFACE": requires_rendered,
            "APPEARANCE_COUNT_EQUALS_RENDERED_APPEARANCE_COUNT": appearance_equals_rendered,
        },
    }


def competitor_candidates() -> List[Dict[str, Any]]:
    base = TARGET_QUERY
    candidates: List[Dict[str, Any]] = []
    strengths = [0.0, 0.025, 0.05, 0.075, 0.1, 0.15]
    for filler_count in range(4, 15):
        filler = " ".join(f"calib{filler_count}_{i}" for i in range(filler_count))
        summary = f"{base} {filler}."
        for strength in strengths:
            candidates.append(
                {
                    "candidate_id": f"F{filler_count:02d}_S{str(strength).replace('.', 'p')}",
                    "summary": summary,
                    "strength": float(strength),
                    "filler_count": filler_count,
                }
            )
    return candidates


def choose_context_budget(cold_obs: Dict[str, Any], warm_obs: Dict[str, Any]) -> int:
    token_counts: Dict[str, int] = {}
    for obs in (cold_obs, warm_obs):
        for block in obs.get("assembled_structured_blocks") or []:
            if block.get("block_kind") in ("target_deep", "competitor_source"):
                token_counts[str(block.get("block_kind"))] = max(
                    int(block.get("token_count") or 0),
                    token_counts.get(str(block.get("block_kind")), 0),
                )
    deep_tokens = max(1, token_counts.get("target_deep", 1))
    comp_tokens = max(1, token_counts.get("competitor_source", 1))
    desired_cap = max(deep_tokens, comp_tokens)
    if desired_cap >= deep_tokens + comp_tokens:
        desired_cap = max(deep_tokens, comp_tokens)
    # For companion profile, situational hard cap is 2 * int(token_budget * 0.20).
    # Pick the smallest budget whose cap admits either block alone.
    budget = max(20, int(np.ceil((desired_cap + 1) / 0.4)))
    return int(budget)


def run_layer_c_workspace(
    *,
    root_dir: Path,
    workspace_id: str,
    competitor: Dict[str, Any],
    fixed_ts: int,
    warmup_pre_calls: int,
    token_budget: int,
    observation_prefix: str,
) -> Dict[str, Any]:
    data_root = (root_dir / workspace_id / "d").resolve()
    data_root.mkdir(parents=True, exist_ok=True)
    fabric = build_fabric(data_root)
    warmup_observations: List[Dict[str, Any]] = []
    try:
        state = create_source_and_deep_state(
            fabric=fabric,
            data_root=data_root,
            workspace_id=workspace_id,
            summary=target_source_summary(),
            fixed_ts=fixed_ts,
        )
        target_eid = int(state["source_eid"])
        competitor_state = add_competitor_memory(
            fabric=fabric,
            data_root=data_root,
            workspace_id=workspace_id,
            summary=str(competitor["summary"]),
            strength=float(competitor["strength"]),
            fixed_ts=fixed_ts,
        )
        competitor_eid = int(competitor_state["eid"])
        fresh_warmth = read_warmup_state(data_root, workspace_id, AGENT_ID, target_eid)
        if fresh_warmth["exists_for_eid"]:
            raise StageStop(f"{workspace_id}: supposed fresh condition already has warmth")

        for idx in range(1, warmup_pre_calls + 1):
            warmup_observations.append(
                run_authoritative_observation(
                    fabric=fabric,
                    data_root=data_root,
                    workspace_id=workspace_id,
                    observation_id=f"{observation_prefix}_WARMUP_{idx:02d}",
                    query=TARGET_QUERY,
                    top_k=3,
                    token_budget=4000,
                    target_eid=target_eid,
                    competitor_eid=competitor_eid,
                )
            )

        source_before_probe = source_snapshot(
            data_root=data_root, workspace_id=workspace_id, eid=target_eid
        )
        competitor_before_probe = source_snapshot(
            data_root=data_root, workspace_id=workspace_id, eid=competitor_eid
        )
        probe = run_authoritative_observation(
            fabric=fabric,
            data_root=data_root,
            workspace_id=workspace_id,
            observation_id=f"{observation_prefix}_AUTHORITATIVE_PROBE",
            query=TARGET_QUERY,
            top_k=3,
            token_budget=int(token_budget),
            target_eid=target_eid,
            competitor_eid=competitor_eid,
        )
    finally:
        try:
            fabric.close()
        except Exception:
            pass

    return {
        "workspace_id": workspace_id,
        "data_root": str(data_root),
        "source_and_deep_state": state,
        "competitor_state": competitor_state,
        "warmup_pre_call_count": int(warmup_pre_calls),
        "warmup_observations": warmup_observations,
        "source_before_authoritative_probe": source_before_probe,
        "competitor_before_authoritative_probe": competitor_before_probe,
        "authoritative_probe": probe,
    }


def score_boundary_metric(cold_obs: Dict[str, Any], warm_obs: Dict[str, Any]) -> Tuple[int, float]:
    cold_deep = cold_obs.get("deep_observation") or {}
    warm_deep = warm_obs.get("deep_observation") or {}
    cold_comp = cold_obs.get("competitor_observation") or {}
    warm_comp = warm_obs.get("competitor_observation") or {}
    cold_gap = float(cold_comp.get("final_score", -999.0)) - float(
        cold_deep.get("final_score", -999.0)
    )
    warm_gap = float(warm_deep.get("final_score", -999.0)) - float(
        warm_comp.get("final_score", -999.0)
    )
    flip = int(cold_gap >= 0.0 and warm_gap > 0.0)
    return flip, abs(cold_gap) + abs(warm_gap)


def run_layer_c_calibration(run_dir: Path, fixed_ts: int) -> Dict[str, Any]:
    calibration_dir = run_dir / "c" / "cal"
    trial_summaries: List[Dict[str, Any]] = []
    best: Optional[Dict[str, Any]] = None
    candidates = competitor_candidates()
    # Bounded calibration: enough grid points to find a near boundary without
    # adapting the authoritative matched workspaces after their outcome.
    for idx, candidate in enumerate(candidates[:66], 1):
        trial_dir = calibration_dir / f"t{idx:03d}"
        cold = run_layer_c_workspace(
            root_dir=trial_dir,
            workspace_id="cc",
            competitor=candidate,
            fixed_ts=fixed_ts,
            warmup_pre_calls=0,
            token_budget=4000,
            observation_prefix="C_CAL_COLD",
        )
        warm = run_layer_c_workspace(
            root_dir=trial_dir,
            workspace_id="cw",
            competitor=candidate,
            fixed_ts=fixed_ts,
            warmup_pre_calls=WARMUP_PRE_CALLS_FOR_WARM_PROBE,
            token_budget=4000,
            observation_prefix="C_CAL_WARM",
        )
        cold_obs = cold["authoritative_probe"]
        warm_obs = warm["authoritative_probe"]
        flip, metric = score_boundary_metric(cold_obs, warm_obs)
        summary = {
            "candidate": candidate,
            "cold_deep_score": (cold_obs.get("deep_observation") or {}).get("final_score"),
            "warm_deep_score": (warm_obs.get("deep_observation") or {}).get("final_score"),
            "cold_competitor_score": (
                cold_obs.get("competitor_observation") or {}
            ).get("final_score"),
            "warm_competitor_score": (
                warm_obs.get("competitor_observation") or {}
            ).get("final_score"),
            "cold_deep_rank": (cold_obs.get("deep_observation") or {}).get("rank_1_based"),
            "warm_deep_rank": (warm_obs.get("deep_observation") or {}).get("rank_1_based"),
            "flip_boundary_metric": metric,
            "score_order_flip_candidate": bool(flip),
            "cold_warmth": cold_obs["post_warmth"].get("current_warmth"),
            "warm_warmth": warm_obs["post_warmth"].get("current_warmth"),
            "trial_dir": str(trial_dir.resolve()),
        }
        trial_summaries.append(summary)
        key = (0 if flip else 1, metric)
        if best is None or key < best["selection_key"]:
            best = {"selection_key": key, "summary": summary, "candidate": candidate}

    if best is None:
        raise StageStop("Layer C calibration produced no candidate")
    selected = dict(best["candidate"])
    return {
        "calibration_boundary": "bounded_hash_mechanical_candidate_grid",
        "candidate_count_considered": len(trial_summaries),
        "selection_rule": (
            "prefer score-order flip boundary; otherwise smallest sum of cold/warm score gaps"
        ),
        "selected_competitor": selected,
        "selected_summary": best["summary"],
        "trial_summaries": trial_summaries,
    }


def run_layer_c(run_dir: Path, fixed_ts: int) -> Dict[str, Any]:
    calibration = run_layer_c_calibration(run_dir, fixed_ts)
    selected = calibration["selected_competitor"]

    # First run with a generous budget to get block token counts for a fixed
    # budget choice. This remains calibration, not authoritative.
    budget_probe_dir = run_dir / "c" / "bp"
    cold_budget_probe = run_layer_c_workspace(
        root_dir=budget_probe_dir,
        workspace_id="cb",
        competitor=selected,
        fixed_ts=fixed_ts,
        warmup_pre_calls=0,
        token_budget=4000,
        observation_prefix="C_BUDGET_COLD",
    )
    warm_budget_probe = run_layer_c_workspace(
        root_dir=budget_probe_dir,
        workspace_id="wb",
        competitor=selected,
        fixed_ts=fixed_ts,
        warmup_pre_calls=WARMUP_PRE_CALLS_FOR_WARM_PROBE,
        token_budget=4000,
        observation_prefix="C_BUDGET_WARM",
    )
    frozen_token_budget = choose_context_budget(
        cold_budget_probe["authoritative_probe"],
        warm_budget_probe["authoritative_probe"],
    )

    authoritative_dir = run_dir / "c" / "auth"
    cold = run_layer_c_workspace(
        root_dir=authoritative_dir,
        workspace_id="ca",
        competitor=selected,
        fixed_ts=fixed_ts,
        warmup_pre_calls=0,
        token_budget=frozen_token_budget,
        observation_prefix="C_COLD",
    )
    warm = run_layer_c_workspace(
        root_dir=authoritative_dir,
        workspace_id="wa",
        competitor=selected,
        fixed_ts=fixed_ts,
        warmup_pre_calls=WARMUP_PRE_CALLS_FOR_WARM_PROBE,
        token_budget=frozen_token_budget,
        observation_prefix="C_WARM",
    )

    cold_source = source_comparable_subset(cold["source_before_authoritative_probe"])
    warm_source = source_comparable_subset(warm["source_before_authoritative_probe"])
    cold_comp = source_comparable_subset(cold["competitor_before_authoritative_probe"])
    warm_comp = source_comparable_subset(warm["competitor_before_authoritative_probe"])
    if cold_source != warm_source:
        raise StageStop("Layer C matched cold/warm target source states differ unexpectedly")
    if cold_comp != warm_comp:
        raise StageStop("Layer C matched cold/warm competitor source states differ unexpectedly")

    cold_obs = cold["authoritative_probe"]
    warm_obs = warm["authoritative_probe"]
    cold_deep = cold_obs.get("deep_observation") or {}
    warm_deep = warm_obs.get("deep_observation") or {}
    cold_comp_hit = cold_obs.get("competitor_observation") or {}
    warm_comp_hit = warm_obs.get("competitor_observation") or {}

    score_changed = (
        cold_deep.get("final_score") is not None
        and warm_deep.get("final_score") is not None
        and float(cold_deep["final_score"]) != float(warm_deep["final_score"])
    )
    rank_changed = cold_deep.get("rank_1_based") != warm_deep.get("rank_1_based")
    surface_flipped = (
        bool(cold_obs["stage_flags"]["DEEP_RENDERED_CONTEXT"])
        != bool(warm_obs["stage_flags"]["DEEP_RENDERED_CONTEXT"])
    )
    initial_same = (
        cold_obs["deep_eligibility_diagnostics"].get("deep_eligible")
        == warm_obs["deep_eligibility_diagnostics"].get("deep_eligible")
        and round(
            float(cold_obs["deep_eligibility_diagnostics"].get("deep_similarity") or 0.0),
            10,
        )
        == round(
            float(warm_obs["deep_eligibility_diagnostics"].get("deep_similarity") or 0.0),
            10,
        )
    )

    return {
        "layer": "C_WARMTH_COMPETITION",
        "embedder_boundary": "HASH_MECHANICAL_HARNESS_SUBSTITUTE",
        "semantic_query_interpretation": "PROHIBITED",
        "calibration": calibration,
        "budget_probe": {
            "cold": cold_budget_probe,
            "warm": warm_budget_probe,
            "frozen_authoritative_token_budget": frozen_token_budget,
        },
        "authoritative_matched": {
            "cold": cold,
            "warm": warm,
            "source_state_comparison": {
                "target_source_comparable_equal": cold_source == warm_source,
                "competitor_source_comparable_equal": cold_comp == warm_comp,
                "target_source_comparable_subset": cold_source,
                "competitor_source_comparable_subset": cold_comp,
            },
            "comparison": {
                "cold_deep_warmth": cold_obs["post_warmth"].get("current_warmth"),
                "warm_deep_warmth": warm_obs["post_warmth"].get("current_warmth"),
                "cold_deep_initial_eligibility": cold_obs[
                    "deep_eligibility_diagnostics"
                ].get("deep_eligible"),
                "warm_deep_initial_eligibility": warm_obs[
                    "deep_eligibility_diagnostics"
                ].get("deep_eligible"),
                "cold_deep_initial_similarity": cold_obs[
                    "deep_eligibility_diagnostics"
                ].get("deep_similarity"),
                "warm_deep_initial_similarity": warm_obs[
                    "deep_eligibility_diagnostics"
                ].get("deep_similarity"),
                "competitor_initial_eligibility": {
                    "cold_final_hit": cold_comp_hit is not None,
                    "warm_final_hit": warm_comp_hit is not None,
                },
                "cold_final_deep_score": cold_deep.get("final_score"),
                "warm_final_deep_score": warm_deep.get("final_score"),
                "cold_competitor_final_score": cold_comp_hit.get("final_score"),
                "warm_competitor_final_score": warm_comp_hit.get("final_score"),
                "cold_final_deep_rank": cold_deep.get("rank_1_based"),
                "warm_final_deep_rank": warm_deep.get("rank_1_based"),
                "cold_rendered_presence": cold_obs["stage_flags"][
                    "DEEP_RENDERED_CONTEXT"
                ],
                "warm_rendered_presence": warm_obs["stage_flags"][
                    "DEEP_RENDERED_CONTEXT"
                ],
            },
        },
        "layer_taxonomy": {
            "WARMTH_CHANGES_FINAL_SCORE": (
                "DEMONSTRATED" if score_changed else "NOT_DEMONSTRATED"
            ),
            "WARMTH_CHANGES_FINAL_RANK": (
                "DEMONSTRATED" if rank_changed else "NOT_DEMONSTRATED"
            ),
            "WARMTH_FLIPS_FINAL_SURFACE_OUTCOME": (
                "DEMONSTRATED" if surface_flipped else "NOT_DEMONSTRATED"
            ),
            "WARMTH_AFFECTS_INITIAL_DEEP_ELIGIBILITY": (
                "CONTRADICTED" if initial_same else "DEMONSTRATED"
            ),
        },
    }


def final_taxonomy(layer_a: Dict[str, Any], layer_b: Dict[str, Any], layer_c: Dict[str, Any]) -> Dict[str, str]:
    a_tax = layer_a.get("layer_taxonomy", {})
    b_tax = layer_b.get("classification", {})
    c_tax = layer_c.get("layer_taxonomy", {})
    return {
        "WARMTH_RECURRENCE": a_tax.get("WARMTH_RECURRENCE", "NOT_DEMONSTRATED"),
        "WARMTH_CAP_AT_1_0": a_tax.get("WARMTH_CAP_AT_1_0", "NOT_DEMONSTRATED"),
        "WARMTH_PERSISTS_ACROSS_RECONSTRUCTION": a_tax.get(
            "WARMTH_PERSISTS_ACROSS_RECONSTRUCTION", "NOT_DEMONSTRATED"
        ),
        "WINDOW_RESET_BEHAVIOR": a_tax.get(
            "WINDOW_RESET_BEHAVIOR", "CODE_TRACED_NOT_EXPERIMENTALLY_CHARACTERIZED"
        ),
        "WARMTH_AFFECTS_INITIAL_DEEP_ELIGIBILITY": c_tax.get(
            "WARMTH_AFFECTS_INITIAL_DEEP_ELIGIBILITY", "CONTRADICTED"
        ),
        "FIRST_CALL_WARMTH_AFFECTS_SAME_CALL_POST_ELIGIBILITY_STATE": a_tax.get(
            "FIRST_CALL_WARMTH_AFFECTS_SAME_CALL_POST_ELIGIBILITY_STATE",
            "NOT_DEMONSTRATED",
        ),
        "WARMTH_MUTATION_REQUIRES_RENDERED_SURFACE": b_tax.get(
            "WARMTH_MUTATION_REQUIRES_RENDERED_SURFACE", "NOT_DEMONSTRATED"
        ),
        "APPEARANCE_COUNT_EQUALS_RENDERED_APPEARANCE_COUNT": b_tax.get(
            "APPEARANCE_COUNT_EQUALS_RENDERED_APPEARANCE_COUNT", "NOT_DEMONSTRATED"
        ),
        "WARMTH_CHANGES_FINAL_SCORE": c_tax.get(
            "WARMTH_CHANGES_FINAL_SCORE", "NOT_DEMONSTRATED"
        ),
        "WARMTH_CHANGES_FINAL_RANK": c_tax.get(
            "WARMTH_CHANGES_FINAL_RANK", "NOT_DEMONSTRATED"
        ),
        "WARMTH_FLIPS_FINAL_SURFACE_OUTCOME": c_tax.get(
            "WARMTH_FLIPS_FINAL_SURFACE_OUTCOME", "NOT_DEMONSTRATED"
        ),
        "FUTURE_SURFACING_PROBABILITY_INCREASE": "NOT_MEASURED",
        "PROVIDER_BEHAVIOR": "NOT_TESTED",
        "DEEP_MEMORY_USEFULNESS": "NOT_TESTED",
        "DEEP_MEMORY_HARMFULNESS": "NOT_TESTED",
        "NATURAL_PREVALENCE": "NOT_MEASURED",
    }


def print_summary(result: Dict[str, Any]) -> None:
    print(f"label: {EXPERIMENT_LABEL}")
    print(f"artifact: {result['artifact_path']}")
    print("")
    print("Layer A recurrence:")
    print("call | appearance_count | warmth | mode | strength | final_score | rendered")
    print("---: | ---: | ---: | --- | ---: | ---: | ---")
    for row in result["layers"]["A"]["recurrence_table"]:
        print(
            " | ".join(
                [
                    str(row["call"]),
                    str(row["appearance_count"]),
                    str(row["current_warmth"]),
                    str(row["spirit_return_mode"]),
                    str(row["spirit_return_strength"]),
                    str(row["deep_final_score"]),
                    "Y" if row["deep_rendered"] else "N",
                ]
            )
        )
    print("")
    print("Layer B:")
    print(json.dumps(result["layers"]["B"]["classification"], indent=2, sort_keys=True))
    print("")
    print("Layer C comparison:")
    print(
        json.dumps(
            result["layers"]["C"]["authoritative_matched"]["comparison"],
            indent=2,
            sort_keys=True,
        )
    )
    print("")
    print("Final taxonomy:")
    print(json.dumps(result["final_taxonomy"], indent=2, sort_keys=True))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=EXPERIMENT_LABEL)
    parser.add_argument(
        "--output-root",
        default=str(Path("outputs") / "experiments" / LABEL),
    )
    parser.add_argument("--run-id", default="")
    args = parser.parse_args(argv)

    root = REPO_ROOT
    initial_git = ensure_authorized_baseline(root)
    stamp = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = (root / args.output_root / stamp).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    fixed_ts = int(time.time())

    env_updates = {
        "TORMENT_COMPRESS_ENABLE": "1",
        "TORMENT_EMBED_PROVIDER": "hash",
        "TORMENT_HASH_DIM": str(HASH_DIM),
        "TORMENT_HASH_SALT": LABEL,
        "TORMENT_HIVEMIND_ENABLE": "0",
        "TORMENT_SRG_ENABLE": "0",
        "TORMENT_CHARACTER_ENABLE": "0",
        "TORMENT_AFFECT_ENABLE": "0",
        "TORMENT_MOOD_DRIFT_ENABLE": "0",
        "TORMENT_MOOD_SPIRAL_ENABLE": "0",
    }

    with scoped_env(env_updates):
        layer_a = run_layer_a(run_dir, fixed_ts)
        layer_b = run_layer_b(run_dir, fixed_ts)
        layer_c = run_layer_c(run_dir, fixed_ts)

    final_git = git_snapshot(root)
    if final_git["production_status"].strip():
        raise StageStop(f"Production files modified after run:\n{final_git['production_status']}")

    result: Dict[str, Any] = {
        "label": EXPERIMENT_LABEL,
        "script_label": LABEL,
        "experiment_subtype": EXPERIMENT_SUBTYPE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "baseline": {
            "authorized_head": AUTHORIZED_HEAD,
            "authorized_subject": AUTHORIZED_SUBJECT,
            "initial_git": initial_git,
            "final_git": final_git,
        },
        "configuration": {
            "configuration_boundary": "NON_DEFAULT_COMPRESSION_ENABLED",
            "production_default_note": "TORMENT_COMPRESS_ENABLE=0 remains production default.",
            "env_overrides_for_harness_process": env_updates,
            "provider_invocation": "NOT_INVOKED",
            "embedder": "HASH_MECHANICAL_HARNESS_SUBSTITUTE",
            "hash_dim": HASH_DIM,
            "hash_salt": LABEL,
            "compression_step": COMPRESSION_STEP,
            "source_born_step": SOURCE_BORN_STEP,
            "deep_min_similarity": DEEP_MIN_SIMILARITY,
            "retrieval_path": "TormentFabric.query -> assemble_context",
            "manual_warmth_assignment": "PROHIBITED_AND_NOT_USED",
            "manual_rank_or_score_assignment": "PROHIBITED_AND_NOT_USED",
        },
        "workspace_identities": {
            "agent_id": AGENT_ID,
            "run_dir": str(run_dir),
        },
        "layers": {
            "A": layer_a,
            "B": layer_b,
            "C": layer_c,
        },
        "final_taxonomy": final_taxonomy(layer_a, layer_b, layer_c),
        "interpretive_boundary": {
            "mechanical_feedback_path_if_demonstrated": (
                "eligible deep processing -> warmth -> stronger downstream score "
                "-> changed downstream retrieval/context outcome"
            ),
            "not_demonstrated_by_this_experiment": [
                "warmth -> easier initial deep eligibility",
                "provider behavior",
                "natural prevalence",
                "deep memory usefulness",
                "deep memory harmfulness",
                "global retrieval attractor",
            ],
            "preferred_label_for_demonstrated_outcome": (
                "POST_ELIGIBILITY_RETRIEVAL_FEEDBACK"
            ),
        },
        "run_dir": str(run_dir),
    }
    artifact_path = run_dir / f"{LABEL}_result.json"
    result["artifact_path"] = str(artifact_path)
    write_json(artifact_path, result)
    print_summary(result)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StageStop as exc:
        print(json.dumps({"ok": False, "stop_condition": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(2)
