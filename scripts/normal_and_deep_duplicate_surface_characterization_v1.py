from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
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
    derive_retention_tier,
)
from torment_service.deep_memory import DeepMemoryStore  # noqa: E402
from torment_service.embedding_store import load_embedding  # noqa: E402
from torment_service.fabric import TormentFabric  # noqa: E402
from torment_service.memory_graph import MemoryGraph  # noqa: E402
from torment_service.retrieval_assembler import FILL_ORDER, assemble_context  # noqa: E402


LABEL = "normal_and_deep_duplicate_surface_characterization_v1"
EXPERIMENT_SUBTYPE = "FIRST_EXPOSURE_RETRIEVAL_CHARACTERIZATION"
AUTHORIZED_HEAD = "f02bed363b256a1fe8a0083a74aab7a21a0e5263"
AUTHORIZED_SUBJECT = "test(lived-use): preserve deep echo fidelity characterization"
AGENT_ID = "ndd_agent"
SOURCE_BORN_STEP = 0
COMPRESSION_STEP = 1000
DEEP_MIN_SIMILARITY = 0.4


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


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


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


def pad_to_length(prefix: str, target_len: int, fill: str) -> str:
    if len(prefix) > target_len:
        raise ValueError(f"prefix longer than target: {len(prefix)} > {target_len}")
    out = prefix
    while len(out) < target_len:
        need = target_len - len(out)
        out += fill[:need]
    return out


def fixture_definitions() -> Dict[str, Dict[str, Any]]:
    e1_summary = (
        "Episode note: Mira placed the amber lantern in the cedar alcove before sunrise. "
        "The amber lantern had a black handle, and the alcove was beside the eastern arch. "
        + "Additional harmless background follows after the deep echo boundary for padding only."
    )

    e2_prefix = pad_to_length(
        "Episode note: Mara cataloged a blue atlas, a brass token, and a rain map before dawn. "
        "The visible prefix says the bundle was sealed in the archive crate.",
        200,
        " neutral prefix detail",
    )
    e2_summary = e2_prefix + " Tail-only fact: the hidden locker code is 7391."

    e3_prefix = pad_to_length(
        "Old state: the gallery key was in the blue bowl before the correction note. "
        "The visible prefix repeats the old blue-bowl location as the superseded state.",
        200,
        " visible old-state context",
    )
    e3_summary = (
        e3_prefix
        + " Current state: the gallery key is in the red drawer after Mira checked it."
    )

    return {
        "E1_BENIGN_DUPLICATE": {
            "fixture_id": "E1_BENIGN_DUPLICATE",
            "family": "E1_BENIGN_DUPLICATE",
            "source_summary_literal": e1_summary,
            "visible_fact": "amber lantern in the cedar alcove",
            "tail_only_fact": "",
            "correction_fact": "",
            "purpose": "All critical evidence is visible in both source and deep echo.",
        },
        "E2_SOURCE_UNIQUE_TAIL": {
            "fixture_id": "E2_SOURCE_UNIQUE_TAIL",
            "family": "E2_SOURCE_UNIQUE_TAIL",
            "source_summary_literal": e2_summary,
            "visible_fact": "blue atlas",
            "tail_only_fact": "hidden locker code is 7391",
            "correction_fact": "",
            "purpose": "Meaningful evidence exists only beyond the displayed echo boundary.",
        },
        "E3_STATE_CORRECTION": {
            "fixture_id": "E3_STATE_CORRECTION",
            "family": "E3_STATE_CORRECTION",
            "source_summary_literal": e3_summary,
            "visible_fact": "gallery key was in the blue bowl",
            "tail_only_fact": "",
            "correction_fact": "gallery key is in the red drawer",
            "purpose": "Superseded state is visible in echo; correcting state is source-only.",
        },
    }


def observation_matrix() -> List[Dict[str, Any]]:
    return [
        {
            "observation_id": "O01_E1_Q1_K1",
            "fixture_id": "E1_BENIGN_DUPLICATE",
            "query_regime": "Q1_SHARED_EVIDENCE",
            "top_k_label": "K1",
            "top_k": 1,
            "query": "Where was the amber lantern placed before sunrise?",
            "target_fact": "amber lantern in the cedar alcove",
            "target_fact_expected_visible_in_deep": True,
        },
        {
            "observation_id": "O02_E1_Q1_K2",
            "fixture_id": "E1_BENIGN_DUPLICATE",
            "query_regime": "Q1_SHARED_EVIDENCE",
            "top_k_label": "K2",
            "top_k": 2,
            "query": "Where was the amber lantern placed before sunrise?",
            "target_fact": "amber lantern in the cedar alcove",
            "target_fact_expected_visible_in_deep": True,
        },
        {
            "observation_id": "O03_E1_Q1_K8",
            "fixture_id": "E1_BENIGN_DUPLICATE",
            "query_regime": "Q1_SHARED_EVIDENCE",
            "top_k_label": "K8",
            "top_k": 8,
            "query": "Where was the amber lantern placed before sunrise?",
            "target_fact": "amber lantern in the cedar alcove",
            "target_fact_expected_visible_in_deep": True,
        },
        {
            "observation_id": "O04_E2_Q2_K8",
            "fixture_id": "E2_SOURCE_UNIQUE_TAIL",
            "query_regime": "Q2_SOURCE_ONLY_VISIBLE_EVIDENCE",
            "top_k_label": "K8",
            "top_k": 8,
            "query": "What was the hidden locker code recorded in the episode?",
            "target_fact": "hidden locker code is 7391",
            "target_fact_expected_visible_in_deep": False,
        },
        {
            "observation_id": "O05_E1_Q3_K8",
            "fixture_id": "E1_BENIGN_DUPLICATE",
            "query_regime": "Q3_BROAD_EPISODIC",
            "top_k_label": "K8",
            "top_k": 8,
            "query": "What happened in Mira's lantern episode?",
            "target_fact": "amber lantern",
            "target_fact_expected_visible_in_deep": True,
        },
        {
            "observation_id": "O06_E3_Q4_K8",
            "fixture_id": "E3_STATE_CORRECTION",
            "query_regime": "Q4_CURRENT_STATE_OR_CORRECTION",
            "top_k_label": "K8",
            "top_k": 8,
            "query": "What is the current state of the gallery key after Mira checked it?",
            "target_fact": "gallery key is in the red drawer",
            "target_fact_expected_visible_in_deep": False,
        },
        {
            "observation_id": "O07_E1_Q5_K8",
            "fixture_id": "E1_BENIGN_DUPLICATE",
            "query_regime": "Q5_ECHO_PREFIX_FAVORED",
            "top_k_label": "K8",
            "top_k": 8,
            "query": "Mira amber lantern cedar alcove eastern arch black handle",
            "target_fact": "amber lantern",
            "target_fact_expected_visible_in_deep": True,
        },
        {
            "observation_id": "O08_E1_Q6_K8",
            "fixture_id": "E1_BENIGN_DUPLICATE",
            "query_regime": "Q6_UNRELATED_NEGATIVE_CONTROL",
            "top_k_label": "K8",
            "top_k": 8,
            "query": "Which astronaut repaired the lunar antenna during the eclipse?",
            "target_fact": "lunar antenna",
            "target_fact_expected_visible_in_deep": False,
        },
    ]


def norm_cosine(a: Any, b: Any) -> Optional[float]:
    if a is None or b is None:
        return None
    av = np.asarray(a, dtype=np.float32).reshape(-1)
    bv = np.asarray(b, dtype=np.float32).reshape(-1)
    if av.shape[0] != bv.shape[0]:
        return None
    denom = float(np.linalg.norm(av) * np.linalg.norm(bv) + 1e-12)
    return float(np.dot(av, bv) / denom)


def lower_contains(haystack: str, needle: str) -> bool:
    return needle.lower() in haystack.lower()


def read_warmup_state(data_root: Path, workspace_id: str, agent_id: str, eid: int) -> Dict[str, Any]:
    warmup_file = (
        data_root
        / "workspaces"
        / workspace_id
        / "agents"
        / agent_id
        / "warmup"
        / "warmup_state.jsonl"
    )
    states: List[Dict[str, Any]] = []
    latest_by_eid: Dict[int, Dict[str, Any]] = {}
    if warmup_file.exists():
        with warmup_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                states.append(item)
                latest_by_eid[int(item.get("eid", -1))] = item
    latest = latest_by_eid.get(int(eid))
    return {
        "warmup_file": str(warmup_file),
        "file_exists": warmup_file.exists(),
        "state_count": len(states),
        "exists_for_eid": latest is not None,
        "appearance_count": (
            int(latest.get("appearance_count", 0)) if latest is not None else None
        ),
        "current_warmth": (
            float(latest.get("current_warmth", 0.0)) if latest is not None else None
        ),
        "latest_for_eid": latest,
    }


def project_hit(hit: Dict[str, Any], source_eid: int, order_index: int) -> Dict[str, Any]:
    is_deep = bool(hit.get("from_spirit_return") or hit.get("deep_memory"))
    same_eid = int(hit.get("eid", -1)) == int(source_eid)
    if same_eid and is_deep:
        hit_kind = "deep_echo"
    elif same_eid:
        hit_kind = "source"
    else:
        hit_kind = "other"
    return {
        "order_index": order_index,
        "hit_kind": hit_kind,
        "eid": hit.get("eid"),
        "scope": hit.get("scope", "private"),
        "type": hit.get("type"),
        "summary": hit.get("summary"),
        "score": hit.get("score"),
        "raw_score": hit.get("raw_score"),
        "final_score": hit.get("final_score"),
        "strength": hit.get("strength"),
        "from_spirit_return": bool(hit.get("from_spirit_return")),
        "deep_memory": bool(hit.get("deep_memory")),
        "spirit_return_mode": hit.get("spirit_return_mode"),
        "warmth_score": hit.get("warmth_score"),
        "authority_status": hit.get("authority_status"),
        "provenance_type": hit.get("provenance_type"),
    }


def flatten_blocks(assembled_dict: Dict[str, Any], source_eid: int) -> List[Dict[str, Any]]:
    blocks = assembled_dict.get("blocks") or {}
    flat: List[Dict[str, Any]] = []
    order_keys = list(FILL_ORDER) + [k for k in blocks.keys() if k not in FILL_ORDER]
    order_index = 0
    for block_type in order_keys:
        for block in blocks.get(block_type, []) or []:
            metadata = block.get("metadata") or {}
            is_deep = bool(metadata.get("from_spirit_return"))
            same_eid = int(block.get("eid") or -1) == int(source_eid)
            if same_eid and is_deep:
                block_kind = "deep_echo"
            elif same_eid:
                block_kind = "source"
            else:
                block_kind = "other"
            flat.append(
                {
                    "order_index": order_index,
                    "block_kind": block_kind,
                    "block_type": block.get("block_type"),
                    "eid": block.get("eid"),
                    "source": block.get("source"),
                    "score": block.get("score"),
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


def rendered_derivative_link_visible(rendered_context: str) -> bool:
    lowered = rendered_context.lower()
    explicit_terms = [
        "derived from",
        "source eid",
        "source row",
        "same eid",
        "derived-from",
        "source memory above",
    ]
    return any(term in lowered for term in explicit_terms)


def classify_labels(
    *,
    source_final: bool,
    deep_final: bool,
    source_candidate_exists: bool,
    deep_eligible: bool,
    deep_headroom: int,
    structured_same_eid_visible: bool,
    rendered_link_visible: bool,
) -> List[str]:
    labels: List[str] = []
    if source_final and deep_final:
        labels.append("R2_SOURCE_AND_DEEP_FINAL")
    elif source_final and not deep_final:
        labels.append("R0_SOURCE_ONLY_FINAL")
    elif deep_final and not source_final:
        labels.append("R1_DEEP_ONLY_FINAL")
    else:
        labels.append("R3_NEITHER_FINAL")

    if deep_headroom <= 0:
        labels.append("R4_DEEP_HEADROOM_STARVED")
    elif deep_eligible and not deep_final:
        labels.append("R5_DEEP_ELIGIBLE_BUT_FINAL_RANKED_OUT")

    if source_candidate_exists and not source_final:
        labels.append("R6_SOURCE_FINAL_RANKED_OUT")
    if structured_same_eid_visible:
        labels.append("R7_STRUCTURED_SHARED_EID")
    if source_final and deep_final and not rendered_link_visible:
        labels.append("R8_RENDERED_DERIVATION_NOT_EXPLICIT")
    return labels


def create_source_and_deep_state(
    *,
    fabric: TormentFabric,
    data_root: Path,
    workspace_id: str,
    fixture: Dict[str, Any],
) -> Dict[str, Any]:
    fabric.create_agent(workspace_id, AGENT_ID)
    ak = fabric._agent_key(workspace_id, AGENT_ID)
    graph = fabric.private_graphs[ak]
    if graph.entities:
        raise StageStop(
            f"{workspace_id}: fresh private graph unexpectedly has {len(graph.entities)} entities"
        )

    source_summary = fixture["source_summary_literal"]
    source_embedding = fabric.kernel.embedder.embed(source_summary)
    eid = graph.spawn_memory(
        summary=source_summary,
        embedding=source_embedding,
        mtype="episode",
        strength=0.05,
        confidence=0.9,
        half_life_days=1.0,
        links=[],
        canon=False,
        user_id=AGENT_ID,
        step=SOURCE_BORN_STEP,
        memory_class="core",
        extra_payload={
            "workspace_id": workspace_id,
            "agent_id": AGENT_ID,
            "scope": "private",
            "domain_id": "personal",
        },
    )
    graph.flush_node(eid)

    private_dir = Path(graph.data_dir).resolve()
    reloaded_graph = MemoryGraph(str(private_dir), embedder=fabric.kernel.embedder)
    fabric.private_graphs[ak] = reloaded_graph
    ent = reloaded_graph.entities.get(int(eid))
    if ent is None:
        raise StageStop(f"{workspace_id}: source entity missing after graph reload")
    source_payload = dict(ent.payload or {})
    if "summary" not in source_payload:
        raise StageStop(f"{workspace_id}: source payload lacks summary")
    if "text" in source_payload:
        raise StageStop(f"{workspace_id}: source payload unexpectedly contains text fallback")
    if str(source_payload["summary"]) != source_summary:
        raise StageStop(f"{workspace_id}: source summary changed after graph reload")

    node = {
        "eid": int(eid),
        "born_step": int(getattr(ent, "born_step", 0) or 0),
        "payload": source_payload,
    }
    candidate = CompressionScorer().score(node, COMPRESSION_STEP, coherence_field=None)
    if candidate is None:
        raise StageStop(f"{workspace_id}: CompressionScorer.score returned None")
    route = CompressionRouter().route(candidate, COMPRESSION_STEP)
    candidate.route = route
    if route != "long_path":
        raise StageStop(f"{workspace_id}: route was {route}, not long_path")

    deep_dir = (
        data_root
        / "workspaces"
        / workspace_id
        / "agents"
        / AGENT_ID
        / "deep_memory"
    ).resolve()
    deep_store = DeepMemoryStore(str(deep_dir), trusted_root=str(data_root.resolve()))
    executor = CompressionExecutor(reloaded_graph, deep_store)
    event = executor.execute([candidate], COMPRESSION_STEP, LABEL)
    if event.exported_deep != 1:
        raise StageStop(f"{workspace_id}: expected one deep export, got {event.exported_deep}")

    post_ent = reloaded_graph.entities.get(int(eid))
    if post_ent is None:
        raise StageStop(f"{workspace_id}: source disappeared after long_path")
    post_payload = dict(post_ent.payload or {})
    post_summary = str(post_payload.get("summary", ""))
    if post_summary != source_summary:
        raise StageStop(f"{workspace_id}: source summary changed after long_path")
    post_strength = float(post_payload.get("strength", -1.0))
    if abs(post_strength - float(COMPRESS_LONG_PATH_STRENGTH)) > 1e-9:
        raise StageStop(
            f"{workspace_id}: post strength {post_strength} != {COMPRESS_LONG_PATH_STRENGTH}"
        )
    if not post_payload.get("exported_deep"):
        raise StageStop(f"{workspace_id}: source payload missing exported_deep")
    if "text" in post_payload:
        raise StageStop(f"{workspace_id}: post source payload unexpectedly contains text")

    fresh_graph = MemoryGraph(str(private_dir), embedder=fabric.kernel.embedder)
    fabric.private_graphs[ak] = fresh_graph
    fresh_ent = fresh_graph.entities.get(int(eid))
    if fresh_ent is None:
        raise StageStop(f"{workspace_id}: persisted source missing after reload")
    fresh_payload = dict(fresh_ent.payload or {})
    if str(fresh_payload.get("summary", "")) != source_summary:
        raise StageStop(f"{workspace_id}: persisted source summary differs after reload")

    fresh_deep_store = DeepMemoryStore(str(deep_dir), trusted_root=str(data_root.resolve()))
    deep_record = fresh_deep_store.recall(int(eid))
    if deep_record is None:
        raise StageStop(f"{workspace_id}: persisted deep record could not be reloaded")

    fabric._deep_stores.pop(ak, None)

    return {
        "ak": ak,
        "source_eid": int(eid),
        "private_dir": str(private_dir),
        "deep_dir": str(deep_dir),
        "source_state_before_export": {
            "eid": int(eid),
            "summary": source_summary,
            "summary_length": len(source_summary),
            "strength": float(source_payload.get("strength")),
            "payload_keys": sorted(source_payload.keys()),
            "has_text_fallback": "text" in source_payload,
            "retention_tier": derive_retention_tier(source_payload),
        },
        "candidate": {
            **asdict(candidate),
            "summary_length": len(candidate.summary),
        },
        "router_result": route,
        "compression_event": event.to_dict(),
        "post_long_path_source_state": {
            "eid": int(eid),
            "summary": fresh_payload.get("summary"),
            "summary_length": len(str(fresh_payload.get("summary", ""))),
            "strength": float(fresh_payload.get("strength")),
            "exported_deep": bool(fresh_payload.get("exported_deep")),
            "compression_route": fresh_payload.get("compression_route"),
            "compression_score": fresh_payload.get("compression_score"),
            "exported_step": fresh_payload.get("exported_step"),
            "has_text_fallback": "text" in fresh_payload,
            "metadata_subset": {
                "workspace_id": fresh_payload.get("workspace_id"),
                "agent_id": fresh_payload.get("agent_id"),
                "domain_id": fresh_payload.get("domain_id"),
                "scope": fresh_payload.get("scope"),
            },
        },
        "deep_record_state": {
            "eid": int(deep_record.eid),
            "summary": str(deep_record.summary),
            "summary_length": len(str(deep_record.summary)),
            "born_step": int(deep_record.born_step),
            "compressed_step": int(deep_record.compressed_step),
            "compression_score": float(deep_record.compression_score),
            "memory_class": deep_record.memory_class,
            "embedding_ref": deep_record.embedding_ref,
            "metadata": dict(deep_record.metadata or {}),
            "persisted_path": str((deep_dir / "memories.jsonl").resolve()),
        },
    }


def compute_eligibility_diagnostics(
    *,
    fabric: TormentFabric,
    data_root: Path,
    workspace_id: str,
    query: str,
    top_k: int,
    state: Dict[str, Any],
) -> Dict[str, Any]:
    ak = state["ak"]
    graph = fabric.private_graphs[ak]
    eid = int(state["source_eid"])
    ent = graph.entities.get(eid)
    if ent is None:
        raise StageStop(f"{workspace_id}: source missing before retrieval diagnostics")
    payload = dict(ent.payload or {})
    query_embedding = fabric.kernel.embedder.embed(query)

    source_embedding = load_embedding(eid, payload, graph._shard_reader, graph.data_dir)
    source_similarity = norm_cosine(source_embedding, query_embedding)

    deep_store = DeepMemoryStore(
        state["deep_dir"], trusted_root=str(data_root.resolve())
    )
    deep_record = deep_store.recall(eid)
    if deep_record is None:
        raise StageStop(f"{workspace_id}: deep record missing before retrieval diagnostics")
    deep_embedding = None
    if deep_record.embedding_ref is not None and deep_store._shard_reader is not None:
        deep_embedding = deep_store._shard_reader.load_one(deep_record.embedding_ref)
    deep_similarity = norm_cosine(deep_embedding, query_embedding)

    private_raw_hits_known = min(max(0, int(top_k)), len(graph.entities))
    shared_raw_hits_known = 0
    deep_headroom = max(0, int(top_k) - private_raw_hits_known - shared_raw_hits_known)
    deep_similarity_passes = (
        deep_similarity is not None and deep_similarity >= DEEP_MIN_SIMILARITY
    )
    return {
        "method_boundary": (
            "Diagnostic cosine calculation only; not a substitute for production "
            "TormentFabric.query final result."
        ),
        "source_candidate_exists": bool(top_k > 0 and ent is not None),
        "source_similarity_to_query": source_similarity,
        "deep_similarity_to_query": deep_similarity,
        "deep_min_similarity": DEEP_MIN_SIMILARITY,
        "deep_similarity_passes_min": bool(deep_similarity_passes),
        "private_raw_hits_known_from_fixture": private_raw_hits_known,
        "shared_raw_hits_known_from_fixture": shared_raw_hits_known,
        "deep_headroom": deep_headroom,
        "deep_lane_invoked_expected": bool(deep_headroom > 0),
        "deep_eligible_if_lane_invoked": bool(deep_headroom > 0 and deep_similarity_passes),
    }


def run_observation(
    spec: Dict[str, Any],
    fixture: Dict[str, Any],
    run_dir: Path,
) -> Dict[str, Any]:
    obs_id = spec["observation_id"]
    obs_num = obs_id.split("_", 1)[0].lower().replace("o", "")
    workspace_id = f"w{obs_num}"
    obs_dir = run_dir / "o" / workspace_id
    data_root = (obs_dir / "d").resolve()
    data_root.mkdir(parents=True, exist_ok=True)

    fabric = TormentFabric(str(data_root))
    retrieval_calls = 0
    try:
        state = create_source_and_deep_state(
            fabric=fabric,
            data_root=data_root,
            workspace_id=workspace_id,
            fixture=fixture,
        )
        source_eid = int(state["source_eid"])
        deep_summary = state["deep_record_state"]["summary"]
        target_fact = spec["target_fact"]
        target_fact_visible_in_deep = lower_contains(deep_summary, target_fact)
        target_fact_visible_in_source = lower_contains(
            fixture["source_summary_literal"], target_fact
        )

        pre_warmth = read_warmup_state(data_root, workspace_id, AGENT_ID, source_eid)
        if pre_warmth["state_count"] > 0:
            raise StageStop(f"{obs_id}: fresh workspace already contains warmth state")

        eligibility = compute_eligibility_diagnostics(
            fabric=fabric,
            data_root=data_root,
            workspace_id=workspace_id,
            query=spec["query"],
            top_k=int(spec["top_k"]),
            state=state,
        )

        fabric_result = fabric.query(
            workspace_id=workspace_id,
            agent_id=AGENT_ID,
            query_text=spec["query"],
            top_k=int(spec["top_k"]),
            domain_id=None,
            peek_bridges=False,
            explain=False,
            continuity_debug=False,
            memory_plan=None,
        )
        retrieval_calls += 1
        if retrieval_calls != 1:
            raise StageStop(f"{obs_id}: retrieval call count is {retrieval_calls}, not 1")

        core_hits = list(fabric_result.get("results") or [])
        assembled = assemble_context(
            core_hits=core_hits,
            archive_hits=[],
            profile="companion",
            token_budget=4000,
            seed_text="",
            character_name="",
            drift_info=None,
            custom_weights=None,
        )
        assembled_dict = assembled.to_dict()
        post_warmth = read_warmup_state(data_root, workspace_id, AGENT_ID, source_eid)

        projected_hits = [
            project_hit(hit, source_eid, idx) for idx, hit in enumerate(core_hits)
        ]
        projected_blocks = flatten_blocks(assembled_dict, source_eid)
        rendered_context = str(assembled_dict.get("assembled_text") or "")

        source_hit_final = any(h["hit_kind"] == "source" for h in projected_hits)
        deep_hit_final = any(h["hit_kind"] == "deep_echo" for h in projected_hits)
        source_structured_block = any(b["block_kind"] == "source" for b in projected_blocks)
        deep_structured_block = any(
            b["block_kind"] == "deep_echo" for b in projected_blocks
        )
        source_rendered = any(
            b["block_kind"] == "source" and str(b["text"]) in rendered_context
            for b in projected_blocks
        )
        deep_rendered = any(
            b["block_kind"] == "deep_echo" and str(b["text"]) in rendered_context
            for b in projected_blocks
        )
        source_final = bool(source_structured_block and source_rendered)
        deep_final = bool(deep_structured_block and deep_rendered)
        structured_same_eid_visible = bool(
            source_structured_block
            and deep_structured_block
            and any(b["block_kind"] == "source" and b["eid"] == source_eid for b in projected_blocks)
            and any(
                b["block_kind"] == "deep_echo" and b["eid"] == source_eid
                for b in projected_blocks
            )
        )
        rendered_link_visible = rendered_derivative_link_visible(rendered_context)

        labels = classify_labels(
            source_final=source_final,
            deep_final=deep_final,
            source_candidate_exists=bool(eligibility["source_candidate_exists"]),
            deep_eligible=bool(eligibility["deep_eligible_if_lane_invoked"]),
            deep_headroom=int(eligibility["deep_headroom"]),
            structured_same_eid_visible=structured_same_eid_visible,
            rendered_link_visible=rendered_link_visible,
        )

        nonvisible_regime = spec["query_regime"] in (
            "Q2_SOURCE_ONLY_VISIBLE_EVIDENCE",
            "Q4_CURRENT_STATE_OR_CORRECTION",
        )
        deep_retrieved_on_nonvisible = bool(
            nonvisible_regime and not target_fact_visible_in_deep and deep_final
        )

        return {
            "observation_id": obs_id,
            "workspace_id": workspace_id,
            "agent_id": AGENT_ID,
            "data_root": str(data_root),
            "fixture": fixture,
            "query_regime": spec["query_regime"],
            "query": spec["query"],
            "top_k_label": spec["top_k_label"],
            "top_k": int(spec["top_k"]),
            "target_fact": target_fact,
            "target_fact_visible_in_source": target_fact_visible_in_source,
            "target_fact_visible_in_deep_summary": target_fact_visible_in_deep,
            "target_fact_expected_visible_in_deep": bool(
                spec["target_fact_expected_visible_in_deep"]
            ),
            "pre_retrieval_state": {
                "retrieval_calls_before": 0,
                "warmth_boundary": "FIRST_EXPOSURE_WITH_NO_PRIOR_WARMTH_HISTORY",
            },
            "source_and_deep_state": state,
            "pre_warmth": pre_warmth,
            "eligibility_diagnostics": eligibility,
            "fabric_final_hits": projected_hits,
            "fabric_result_domains": fabric_result.get("domains"),
            "fabric_result_domain_used": fabric_result.get("domain_used"),
            "fabric_excluded": fabric_result.get("excluded"),
            "assembled_structured_blocks": projected_blocks,
            "rendered_context": rendered_context,
            "post_warmth": post_warmth,
            "retrieval_call_count": retrieval_calls,
            "stage_results": {
                "source_candidate_eligible": bool(eligibility["source_candidate_exists"]),
                "deep_record_exists": True,
                "deep_similarity_passes_min": bool(
                    eligibility["deep_similarity_passes_min"]
                ),
                "deep_headroom": int(eligibility["deep_headroom"]),
                "source_in_fabric_final_hits": source_hit_final,
                "deep_in_fabric_final_hits": deep_hit_final,
                "source_in_structured_blocks": source_structured_block,
                "deep_in_structured_blocks": deep_structured_block,
                "source_in_rendered_context": source_rendered,
                "deep_in_rendered_context": deep_rendered,
            },
            "identity_provenance_measurement": {
                "source_eid": source_eid,
                "deep_record_eid": int(state["deep_record_state"]["eid"]),
                "structured_same_eid_visible": (
                    "YES" if structured_same_eid_visible else "NO"
                ),
                "rendered_derivative_link_visible": (
                    "YES" if rendered_link_visible else "NO"
                ),
                "returning_memory_marker_visible": "[Returning Memory]" in rendered_context,
            },
            "special_full_embedding_nonvisible_evidence_result": {
                "applicable": nonvisible_regime,
                "target_fact_absent_from_deep_summary": not target_fact_visible_in_deep,
                "deep_surfaced_to_final_rendered_context": deep_final,
                "DEEP_RETRIEVED_ON_NONVISIBLE_SOURCE_EVIDENCE": (
                    "DEMONSTRATED"
                    if deep_retrieved_on_nonvisible
                    else ("NOT_DEMONSTRATED" if nonvisible_regime else "NOT_APPLICABLE")
                ),
            },
            "R_labels": labels,
            "notes": [
                (
                    "Normal and deep incoming score fields are recorded but not "
                    "interpreted as same-scale similarity."
                ),
                (
                    "Deep eligibility diagnostics are cosine calculations over persisted "
                    "embeddings; final surfacing is determined only by TormentFabric.query "
                    "and assemble_context."
                ),
            ],
        }
    finally:
        try:
            fabric.close()
        except Exception:
            pass


def aggregate_results(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    label_counts = Counter()
    query_counts = Counter()
    topk_counts = Counter()
    warmth_mutations = 0
    for obs in observations:
        query_counts[obs["query_regime"]] += 1
        topk_counts[obs["top_k_label"]] += 1
        for label in obs["R_labels"]:
            label_counts[label] += 1
        pre = obs["pre_warmth"]
        post = obs["post_warmth"]
        if not pre["exists_for_eid"] and post["exists_for_eid"]:
            warmth_mutations += 1

    return {
        "observation_count": len(observations),
        "query_regime_counts": dict(sorted(query_counts.items())),
        "top_k_counts": dict(sorted(topk_counts.items())),
        "R_label_counts": dict(sorted(label_counts.items())),
        "final_result_taxonomy": {
            "SOURCE_DEEP_CO_SURFACE": (
                "DEMONSTRATED"
                if label_counts.get("R2_SOURCE_AND_DEEP_FINAL", 0) > 0
                else "NOT_DEMONSTRATED"
            ),
            "DEEP_HEADROOM_STARVATION": (
                "DEMONSTRATED"
                if label_counts.get("R4_DEEP_HEADROOM_STARVED", 0) > 0
                else "NOT_DEMONSTRATED"
            ),
            "STRUCTURED_SHARED_EID": (
                "DEMONSTRATED"
                if label_counts.get("R7_STRUCTURED_SHARED_EID", 0) > 0
                else "NOT_DEMONSTRATED"
            ),
            "RENDERED_DERIVATIVE_LINK": (
                "DEMONSTRATED"
                if any(
                    obs["identity_provenance_measurement"][
                        "rendered_derivative_link_visible"
                    ]
                    == "YES"
                    for obs in observations
                )
                else "NOT_DEMONSTRATED"
            ),
            "DEEP_RETRIEVED_ON_NONVISIBLE_SOURCE_EVIDENCE": (
                "DEMONSTRATED"
                if any(
                    obs["special_full_embedding_nonvisible_evidence_result"][
                        "DEEP_RETRIEVED_ON_NONVISIBLE_SOURCE_EVIDENCE"
                    ]
                    == "DEMONSTRATED"
                    for obs in observations
                )
                else "NOT_DEMONSTRATED"
            ),
            "FIRST_EXPOSURE_WARMTH_MUTATION": (
                "DEMONSTRATED" if warmth_mutations > 0 else "NOT_DEMONSTRATED"
            ),
            "PROVIDER_FALSE_CORROBORATION": "NOT_TESTED",
            "NATURAL_PREVALENCE": "NOT_MEASURED",
        },
        "first_exposure_warmth_mutation_count": warmth_mutations,
    }


def print_summary(result: Dict[str, Any]) -> None:
    print(f"label: {result['label']}")
    print(f"artifact: {result['artifact_path']}")
    print("")
    print("observation | query | top_k | labels | source | deep | warmth")
    print("--- | --- | ---: | --- | --- | --- | ---")
    for obs in result["observations"]:
        stages = obs["stage_results"]
        post = obs["post_warmth"]
        warmth = (
            f"{post['appearance_count']}@{post['current_warmth']}"
            if post["exists_for_eid"]
            else "-"
        )
        print(
            " | ".join(
                [
                    obs["observation_id"],
                    obs["query_regime"],
                    str(obs["top_k"]),
                    ",".join(obs["R_labels"]),
                    "Y" if stages["source_in_rendered_context"] else "N",
                    "Y" if stages["deep_in_rendered_context"] else "N",
                    warmth,
                ]
            )
        )
    print("")
    print(json.dumps(result["aggregate"]["final_result_taxonomy"], indent=2, sort_keys=True))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=LABEL)
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

    env_updates = {
        "TORMENT_COMPRESS_ENABLE": "1",
        "TORMENT_EMBED_PROVIDER": "hash",
        "TORMENT_HASH_DIM": "384",
        "TORMENT_HASH_SALT": LABEL,
        "TORMENT_HIVEMIND_ENABLE": "0",
        "TORMENT_SRG_ENABLE": "0",
        "TORMENT_THINKING_ADVISORY": "0",
    }

    fixtures = fixture_definitions()
    specs = observation_matrix()

    with scoped_env(env_updates):
        observations = [
            run_observation(spec, fixtures[spec["fixture_id"]], run_dir)
            for spec in specs
        ]

    final_git = git_snapshot(root)
    if final_git["production_status"].strip():
        raise StageStop(f"Production files modified after run:\n{final_git['production_status']}")

    result: Dict[str, Any] = {
        "label": LABEL,
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
            "compression_step": COMPRESSION_STEP,
            "source_born_step": SOURCE_BORN_STEP,
            "long_path_strength_constant": COMPRESS_LONG_PATH_STRENGTH,
            "deep_min_similarity": DEEP_MIN_SIMILARITY,
            "retrieval_path": "TormentFabric.query -> assemble_context",
            "provider_invocation": "NOT_INVOKED",
        },
        "fixture_definitions": fixtures,
        "observation_matrix": specs,
        "observations": observations,
        "aggregate": aggregate_results(observations),
        "interpretive_boundary": {
            "allowed": [
                "mechanical retrievability",
                "source/deep co-surfacing under controlled conditions",
                "headroom and ranking causes",
                "structured same-eid visibility",
                "rendered derivative-link visibility",
                "first-exposure warmth mutation",
            ],
            "not_allowed": [
                "provider confusion",
                "false corroboration",
                "model belief",
                "usefulness",
                "harmfulness",
                "natural prevalence",
                "default-production prevalence",
                "long-term warmth feedback",
            ],
        },
        "run_dir": str(run_dir),
    }
    artifact_path = run_dir / f"{LABEL}_result.json"
    result["artifact_path"] = str(artifact_path)
    write_json(artifact_path, result)
    print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
