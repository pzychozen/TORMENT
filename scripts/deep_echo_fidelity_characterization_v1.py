from __future__ import annotations

import argparse
import json
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from torment_service.compression import (
    CompressionExecutor,
    CompressionRouter,
    CompressionScorer,
    derive_retention_tier,
)
from torment_service.deep_memory import DeepMemoryStore
from torment_service.embeddings import HashEmbedding
from torment_service.memory_graph import MemoryGraph


LABEL = "deep_echo_fidelity_characterization_v1"
AUTHORIZED_HEAD = "1e3d04a3857c40df404d4f8f8d0d930e820f6f84"
WORKSPACE_ID = LABEL
AGENT_ID = "deep_echo_agent"
CURRENT_STEP = 1000
SOURCE_BORN_STEP = 0


class StageStop(RuntimeError):
    pass


def repo_root() -> Path:
    return REPO_ROOT


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


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def pad_to_length(prefix: str, target_len: int, fill: str = " detail") -> str:
    if len(prefix) > target_len:
        raise ValueError(f"prefix longer than target: {len(prefix)} > {target_len}")
    out = prefix
    while len(out) < target_len:
        need = target_len - len(out)
        out += fill[:need]
    return out


def pad_clean_prefix(sentence: str, target_len: int) -> str:
    sentence = sentence.rstrip()
    if not sentence.endswith("."):
        sentence += "."
    if len(sentence) > target_len:
        raise ValueError(f"sentence longer than target: {len(sentence)} > {target_len}")
    return sentence + (" " * (target_len - len(sentence)))


def fact(fact_id: str, category: str, text: str, *, critical: bool = True) -> Dict[str, Any]:
    return {
        "fact_id": fact_id,
        "category": category,
        "text": text,
        "critical": bool(critical),
    }


def fixture(
    fixture_id: str,
    family: str,
    source_summary: str,
    facts: List[Dict[str, Any]],
    *,
    relations: Optional[List[Dict[str, str]]] = None,
    layer: str = "LAYER_B_EVIDENCE_CHARACTERIZATION",
) -> Dict[str, Any]:
    return {
        "fixture_id": fixture_id,
        "family": family,
        "layer": layer,
        "source_summary_literal": source_summary,
        "facts": facts,
        "relations": relations or [],
    }


def calibration_fixture(fixture_id: str, source_summary: str) -> Dict[str, Any]:
    return fixture(
        fixture_id,
        "HARNESS_CALIBRATION",
        source_summary,
        [],
        layer="LAYER_A_HARNESS_CALIBRATION",
    )


def build_fixtures() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    layer_a = [
        calibration_fixture("A_CAL_199", "a" * 199),
        calibration_fixture("A_CAL_200", "b" * 200),
        calibration_fixture("A_CAL_201", "c" * 201),
    ]

    a_summary = (
        "Earlier I thought the gallery key was in the blue bowl, but the current state is "
        "that the gallery key is in the red drawer. Mira checked it after breakfast."
    )

    b_summary = (
        "Mira stored the brass compass in the cedar box before lunch. "
        "The box stayed on the north shelf for the whole afternoon. "
        + pad_to_length("", 90, " routine detail")
        + " Decorative ribbon color was pale lavender."
    )

    c_summary = (
        "A field note says the repair kit was packed before the train left. "
        + pad_to_length("", 145, " neutral filler")
        + " The missing location was the east observatory balcony."
    )

    d_summary = (
        "I cancelled the museum visit before noon. "
        + pad_to_length("", 166, " ordinary context")
        + " The reason was that the west bridge flooded after the storm."
    )

    e_summary = (
        "I first wrote that the clinic door code was 4821. "
        + pad_to_length("", 145, " ordinary context")
        + " Correction: the clinic door code was not 4821; it was 8241."
    )

    f_summary = (
        "Old state: my emergency contact was Nia. "
        + pad_to_length("", 158, " ordinary context")
        + " Current state: my emergency contact is Tomas."
    )

    g_summary = (
        "The delivery note says the silver lens arrived before the tripod. "
        + pad_to_length("", 140, " ordinary context")
        + " Correct chronology: the tripod arrived first, then the silver lens arrived."
    )

    h_summary = (
        "I recorded that the attic window was left open overnight. "
        + pad_to_length("", 140, " ordinary context")
        + " Qualification: I am not certain; Mara only guessed from the damp sill."
    )

    i_prefix = pad_clean_prefix(
        "Earlier I believed the gallery key was in the blue bowl.",
        200,
    )
    i_summary = i_prefix + " Current state: the gallery key is in the red drawer."

    j_prefix = pad_to_length("Non-ASCII note: the passphrase is ", 196, "x")
    j_summary = j_prefix + "cafe\u0301 and it unlocks the atelier cabinet."

    layer_b = [
        fixture(
            "B01_FULL_PRESERVATION_AND_SENTENCE_CONTROL",
            "A_FULL_PRESERVATION_CONTROL_AND_I_CONTROL",
            a_summary,
            [
                fact("b01_old", "state_reversal", "Earlier I thought the gallery key was in the blue bowl"),
                fact("b01_current", "state_reversal", "current state is that the gallery key is in the red drawer"),
                fact("b01_person", "person", "Mira"),
            ],
            relations=[{"superseded_fact_id": "b01_old", "correcting_fact_id": "b01_current"}],
        ),
        fixture(
            "B02_NONCRITICAL_TAIL_LOSS",
            "B_NONCRITICAL_TAIL_LOSS",
            b_summary,
            [
                fact("b02_object", "object", "brass compass"),
                fact("b02_location", "location", "north shelf"),
                fact("b02_decor", "object", "Decorative ribbon color was pale lavender", critical=False),
            ],
        ),
        fixture(
            "B03_ENTITY_LOCATION_LOSS",
            "C_ENTITY_LOCATION_LOSS",
            c_summary,
            [
                fact("b03_object", "object", "repair kit"),
                fact("b03_location", "location", "east observatory balcony"),
            ],
        ),
        fixture(
            "B04_CAUSAL_REASON_SEVERING",
            "D_CAUSAL_ACTION_REASON_SEVERING",
            d_summary,
            [
                fact("b04_action", "action_reason", "cancelled the museum visit"),
                fact("b04_reason", "causal", "The reason was that the west bridge flooded after the storm"),
            ],
        ),
        fixture(
            "B05_NEGATION_LOSS",
            "E_NEGATION_LOSS",
            e_summary,
            [
                fact("b05_superseded", "state_reversal", "clinic door code was 4821"),
                fact("b05_negation", "negation", "clinic door code was not 4821"),
                fact("b05_corrected", "state_reversal", "it was 8241"),
            ],
            relations=[{"superseded_fact_id": "b05_superseded", "correcting_fact_id": "b05_negation"}],
        ),
        fixture(
            "B06_STATE_REVERSAL_LOSS",
            "F_STATE_REVERSAL",
            f_summary,
            [
                fact("b06_old_state", "state_reversal", "Old state: my emergency contact was Nia"),
                fact("b06_current_state", "state_reversal", "Current state: my emergency contact is Tomas"),
            ],
            relations=[{"superseded_fact_id": "b06_old_state", "correcting_fact_id": "b06_current_state"}],
        ),
        fixture(
            "B07_CHRONOLOGY_LOSS",
            "G_CHRONOLOGY_DATE_ORDER_LOSS",
            g_summary,
            [
                fact("b07_surviving_order", "chronology", "silver lens arrived before the tripod"),
                fact("b07_correct_order", "chronology", "the tripod arrived first, then the silver lens arrived"),
            ],
        ),
        fixture(
            "B08_QUALIFICATION_UNCERTAINTY_LOSS",
            "H_QUALIFICATION_UNCERTAINTY_LOSS",
            h_summary,
            [
                fact("b08_claim", "object", "attic window was left open overnight"),
                fact("b08_uncertainty", "uncertainty", "I am not certain"),
                fact("b08_qualification", "qualification", "Mara only guessed from the damp sill"),
            ],
        ),
        fixture(
            "B09_CLEAN_BUT_MISLEADING_SENTENCE_BOUNDARY",
            "I_CLEAN_BUT_MISLEADING_SENTENCE_BOUNDARY",
            i_summary,
            [
                fact("b09_old_state", "state_reversal", "Earlier I believed the gallery key was in the blue bowl"),
                fact("b09_current_state", "state_reversal", "Current state: the gallery key is in the red drawer"),
            ],
            relations=[{"superseded_fact_id": "b09_old_state", "correcting_fact_id": "b09_current_state"}],
        ),
        fixture(
            "B10_NON_ASCII_BOUNDARY",
            "J_NON_ASCII_BOUNDARY",
            j_summary,
            [
                fact("b10_passphrase", "object", "cafe\u0301"),
                fact("b10_location", "location", "atelier cabinet"),
            ],
        ),
    ]
    return layer_a, layer_b


def attach_spans(source_summary: str, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in facts:
        text = item["text"]
        start = source_summary.find(text)
        if start < 0:
            raise StageStop(f"Fact text not found for {item['fact_id']!r}: {text!r}")
        if source_summary.find(text, start + 1) >= 0:
            raise StageStop(f"Fact text is not unique for {item['fact_id']!r}: {text!r}")
        rec = dict(item)
        rec["span"] = [start, start + len(text)]
        out.append(rec)
    return out


def validate_graph_source_payload(payload: Dict[str, Any]) -> None:
    if "summary" not in payload:
        raise StageStop("source payload missing required summary")
    if "text" in payload:
        raise StageStop("source payload unexpectedly contains text fallback key")


def classify_fact_states(
    source_summary: str,
    observed_echo: str,
    facts: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], int]:
    if not source_summary.startswith(observed_echo):
        raise StageStop("observed deep echo is not a prefix of the graph-read source summary")
    boundary = len(observed_echo)
    classified: List[Dict[str, Any]] = []
    for item in facts:
        start, end = item["span"]
        declared = item["text"]
        if source_summary[start:end] != declared:
            raise StageStop(
                f"Fact span mismatch for {item['fact_id']}: "
                f"{source_summary[start:end]!r} != {declared!r}"
            )
        if end <= boundary:
            state = "PRESERVED"
        elif start >= boundary:
            state = "LOST"
        else:
            state = "PARTIAL"
        rec = dict(item)
        rec["state"] = state
        rec["observed_overlap"] = [
            max(start, 0),
            min(end, boundary),
        ] if state == "PARTIAL" else None
        classified.append(rec)
    return classified, boundary


def boundary_info(source_summary: str, observed_echo: str, boundary: int) -> Dict[str, Any]:
    absent_chars = max(0, len(source_summary) - len(observed_echo))
    if absent_chars == 0:
        kind = "NO_ABSENT_CHARACTERS"
    else:
        last = observed_echo[-1] if observed_echo else ""
        clean = bool(last.isspace() or last in ".!?")
        kind = "CLEAN_BOUNDARY" if clean else "BOUNDARY_BLIND_FRAGMENT"

    grapheme_split = False
    if 0 < boundary < len(source_summary):
        prev_char = source_summary[boundary - 1]
        next_char = source_summary[boundary]
        grapheme_split = (
            unicodedata.combining(next_char) != 0
            and unicodedata.combining(prev_char) == 0
        )

    return {
        "absent_characters": absent_chars,
        "boundary_index": boundary,
        "boundary_kind": kind,
        "last_echo_char": observed_echo[-1:] if observed_echo else "",
        "next_source_char": source_summary[boundary:boundary + 1],
        "grapheme_split": grapheme_split,
    }


def labels_for_fixture(
    source_summary: str,
    observed_echo: str,
    facts: List[Dict[str, Any]],
    relations: List[Dict[str, str]],
    boundary: Dict[str, Any],
) -> Tuple[List[str], List[Dict[str, Any]]]:
    labels: List[str] = []
    if len(observed_echo) == len(source_summary):
        return ["F0_FULL_SEMANTIC_PRESERVATION"], []

    if boundary["boundary_kind"] == "CLEAN_BOUNDARY":
        labels.append("F1_LOSSY_BUT_BOUNDARY_CLEAN")
    elif boundary["boundary_kind"] == "BOUNDARY_BLIND_FRAGMENT":
        labels.append("F5_BOUNDARY_BLIND_FRAGMENT")

    lost = [f for f in facts if f["state"] == "LOST"]
    lost_or_partial = [f for f in facts if f["state"] in ("LOST", "PARTIAL")]
    if lost and all(not bool(f["critical"]) for f in lost):
        labels.append("F2_NONCRITICAL_DETAIL_LOSS")
    if any(f["category"] in ("causal", "relational") for f in lost_or_partial):
        labels.append("F3_CAUSAL_OR_RELATIONAL_LOSS")
    if any(f["category"] in ("negation", "state_reversal") for f in lost_or_partial):
        labels.append("F4_STATE_OR_NEGATION_LOSS")

    by_id = {f["fact_id"]: f for f in facts}
    relation_losses: List[Dict[str, Any]] = []
    for rel in relations:
        old = by_id.get(rel["superseded_fact_id"])
        new = by_id.get(rel["correcting_fact_id"])
        if not old or not new:
            raise StageStop(f"Unknown relation fact ids: {rel}")
        lost_relation = old["state"] == "PRESERVED" and new["state"] in ("LOST", "PARTIAL")
        rec = {
            **rel,
            "superseded_state": old["state"],
            "correcting_state": new["state"],
            "CORRECTION_OR_SUPERSESSION_LOST": lost_relation,
        }
        relation_losses.append(rec)
        if old["state"] == "PRESERVED" and new["state"] == "LOST":
            labels.append("F6_SEMANTICALLY_MISLEADING_ECHO")

    return sorted(set(labels)), relation_losses


def make_embedding(summary: str) -> np.ndarray:
    return HashEmbedding(dim=384, salt=LABEL).embed(summary)


def run_one_fixture(
    fx: Dict[str, Any],
    run_dir: Path,
    *,
    calibration: bool,
) -> Dict[str, Any]:
    fixture_dir = run_dir / fx["fixture_id"]
    graph_dir = fixture_dir / "memory_graph"
    deep_dir = fixture_dir / "deep_memory"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    embedder = HashEmbedding(dim=384, salt=LABEL)
    graph = MemoryGraph(str(graph_dir.resolve()), embedder=embedder)
    source_literal = fx["source_summary_literal"]
    facts_with_literal_spans = attach_spans(source_literal, fx["facts"])

    eid = graph.spawn_memory(
        summary=source_literal,
        embedding=make_embedding(source_literal),
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
            "workspace_id": WORKSPACE_ID,
            "agent_id": AGENT_ID,
            "scope": "private",
            "domain_id": "personal",
        },
    )
    graph.flush_node(eid)

    del graph
    graph = MemoryGraph(str(graph_dir.resolve()), embedder=embedder)
    ent = graph.entities.get(eid)
    if ent is None:
        raise StageStop(f"{fx['fixture_id']}: source entity missing after graph reload")
    source_payload = ent.payload or {}
    validate_graph_source_payload(source_payload)
    graph_read_source = str(source_payload["summary"])
    if graph_read_source != source_literal:
        raise StageStop(f"{fx['fixture_id']}: graph-read source differs from fixture literal")

    facts = attach_spans(graph_read_source, fx["facts"])
    if facts != facts_with_literal_spans:
        raise StageStop(f"{fx['fixture_id']}: fact spans changed after graph reload")

    node = {
        "eid": int(eid),
        "born_step": int(getattr(ent, "born_step", 0) or 0),
        "payload": dict(source_payload),
    }
    tier = derive_retention_tier(source_payload)
    scorer = CompressionScorer()
    candidate = scorer.score(node, CURRENT_STEP, coherence_field=None)
    if candidate is None:
        raise StageStop(f"{fx['fixture_id']}: CompressionScorer.score returned None")

    if calibration:
        expected_candidate = graph_read_source[:200]
        if candidate.summary != expected_candidate:
            raise StageStop(
                f"{fx['fixture_id']}: calibration failed candidate.summary != source[:200]"
            )

    router = CompressionRouter()
    route = router.route(candidate, CURRENT_STEP)
    candidate.route = route
    if route != "long_path":
        if calibration:
            return {
                "fixture_id": fx["fixture_id"],
                "layer": fx["layer"],
                "route": route,
                "not_deep_path_eligible": True,
            }
        raise StageStop(f"{fx['fixture_id']}: Layer-B fixture routed {route}, not long_path")

    deep_store = DeepMemoryStore(str(deep_dir.resolve()), trusted_root=str(fixture_dir.resolve()))
    executor = CompressionExecutor(graph, deep_store)
    event = executor.execute([candidate], CURRENT_STEP, "transform_isolation")
    if event.exported_deep != 1:
        raise StageStop(f"{fx['fixture_id']}: expected one deep export, got {event.exported_deep}")

    post_ent = graph.entities.get(eid)
    if post_ent is None:
        raise StageStop(f"{fx['fixture_id']}: source entity missing after execution")
    post_payload = post_ent.payload or {}
    post_summary = str(post_payload.get("summary", ""))
    if post_summary != graph_read_source:
        raise StageStop(f"{fx['fixture_id']}: source summary changed after long_path execution")
    if not post_payload.get("exported_deep"):
        raise StageStop(f"{fx['fixture_id']}: source payload missing exported_deep marker")

    del executor
    del deep_store
    fresh_store = DeepMemoryStore(str(deep_dir.resolve()), trusted_root=str(fixture_dir.resolve()))
    deep_record = fresh_store.recall(eid)
    if deep_record is None:
        raise StageStop(f"{fx['fixture_id']}: fresh DeepMemoryStore reload found no record")
    observed_echo = str(deep_record.summary)
    recall_again = fresh_store.recall(eid)
    if recall_again is None or str(recall_again.summary) != observed_echo:
        raise StageStop(f"{fx['fixture_id']}: fresh reload did not reproduce persisted echo")

    classified_facts, observed_boundary = classify_fact_states(
        graph_read_source,
        observed_echo,
        facts,
    )
    binfo = boundary_info(graph_read_source, observed_echo, observed_boundary)
    labels, relation_losses = labels_for_fixture(
        graph_read_source,
        observed_echo,
        classified_facts,
        fx["relations"],
        binfo,
    )

    return {
        "fixture_id": fx["fixture_id"],
        "family": fx["family"],
        "layer": fx["layer"],
        "graph_read_source_summary": graph_read_source,
        "source_character_length": len(graph_read_source),
        "source_atomic_facts": classified_facts,
        "retention_tier": tier,
        "candidate_score": candidate.score,
        "candidate_j_score": candidate.j_score,
        "candidate_z_score": candidate.z_score,
        "router_result": route,
        "candidate_summary_observed_from_scorer": candidate.summary,
        "candidate_character_length": len(candidate.summary),
        "post_execution_source_summary": post_summary,
        "post_execution_source_strength": post_payload.get("strength"),
        "exported_deep_status": bool(post_payload.get("exported_deep")),
        "compression_metadata": {
            "compression_route": post_payload.get("compression_route"),
            "compression_score": post_payload.get("compression_score"),
            "exported_step": post_payload.get("exported_step"),
        },
        "freshly_reloaded_deep_memory_summary": observed_echo,
        "deep_echo_character_length": len(observed_echo),
        "preserved_facts": [f["fact_id"] for f in classified_facts if f["state"] == "PRESERVED"],
        "partial_facts": [f["fact_id"] for f in classified_facts if f["state"] == "PARTIAL"],
        "lost_facts": [f["fact_id"] for f in classified_facts if f["state"] == "LOST"],
        "correction_or_supersession": relation_losses,
        "correction_or_supersession_lost": any(
            r["CORRECTION_OR_SUPERSESSION_LOST"] for r in relation_losses
        ),
        "boundary_classification": binfo,
        "fidelity_labels": labels,
        "grapheme_split": bool(binfo["grapheme_split"]),
        "hypothetical_not_deep_path": False,
        "deep_record_persisted_path": str((deep_dir / "memories.jsonl").resolve()),
    }


def aggregate(layer_b_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    labels = Counter()
    categories: Dict[str, Counter] = defaultdict(Counter)
    criticality: Dict[str, Counter] = defaultdict(Counter)
    boundary = Counter()
    correction_loss = Counter()

    for rec in layer_b_results:
        for label in rec["fidelity_labels"]:
            labels[label] += 1
        boundary[rec["boundary_classification"]["boundary_kind"]] += 1
        correction_loss[str(bool(rec["correction_or_supersession_lost"]))] += 1
        for fact_rec in rec["source_atomic_facts"]:
            categories[fact_rec["category"]][fact_rec["state"]] += 1
            criticality["critical" if fact_rec["critical"] else "noncritical"][fact_rec["state"]] += 1

    all_labels = [
        "F0_FULL_SEMANTIC_PRESERVATION",
        "F1_LOSSY_BUT_BOUNDARY_CLEAN",
        "F2_NONCRITICAL_DETAIL_LOSS",
        "F3_CAUSAL_OR_RELATIONAL_LOSS",
        "F4_STATE_OR_NEGATION_LOSS",
        "F5_BOUNDARY_BLIND_FRAGMENT",
        "F6_SEMANTICALLY_MISLEADING_ECHO",
    ]

    return {
        "fidelity_label_counts": {k: labels.get(k, 0) for k in all_labels},
        "fact_category_counts": {k: dict(v) for k, v in sorted(categories.items())},
        "criticality_counts": {k: dict(v) for k, v in sorted(criticality.items())},
        "boundary_counts": dict(boundary),
        "correction_or_supersession_loss_counts": dict(correction_loss),
    }


def print_summary(result: Dict[str, Any]) -> None:
    print(f"label: {LABEL}")
    print(f"artifact: {result['artifact_path']}")
    print("")
    print("fixture | route | echo_len | boundary | labels | lost | partial")
    print("--- | --- | ---: | --- | --- | --- | ---")
    for rec in result["layer_b_results"]:
        print(
            " | ".join(
                [
                    rec["fixture_id"],
                    rec["router_result"],
                    str(rec["deep_echo_character_length"]),
                    rec["boundary_classification"]["boundary_kind"],
                    ",".join(rec["fidelity_labels"]),
                    ",".join(rec["lost_facts"]) or "-",
                    ",".join(rec["partial_facts"]) or "-",
                ]
            )
        )
    print("")
    print("aggregate:")
    print(json.dumps(result["aggregate"], indent=2, sort_keys=True))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=LABEL)
    parser.add_argument(
        "--output-root",
        default=str(Path("outputs") / "experiments" / LABEL),
    )
    parser.add_argument("--run-id", default="")
    args = parser.parse_args(argv)

    root = repo_root()
    initial_git = ensure_authorized_head(root)
    stamp = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = (root / args.output_root / stamp).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    layer_a, layer_b = build_fixtures()

    layer_a_results = [
        run_one_fixture(fx, run_dir / "layer_a_calibration", calibration=True)
        for fx in layer_a
    ]
    layer_b_results = [
        run_one_fixture(fx, run_dir / "layer_b_evidence", calibration=False)
        for fx in layer_b
    ]

    result: Dict[str, Any] = {
        "label": LABEL,
        "experiment_type": "TRANSFORM_ISOLATION_CHARACTERIZATION",
        "interpretive_boundary": {
            "allowed": "ABSENT_FROM_DEEP_ECHO",
            "not_allowed": "LOST_FROM_TORMENT",
        },
        "initial_git": initial_git,
        "final_git": git_snapshot(root),
        "production_components": [
            "MemoryGraph",
            "CompressionScorer",
            "CompressionRouter",
            "CompressionExecutor",
            "DeepMemoryStore",
        ],
        "omitted_component": {
            "EventDetector": "omitted; trigger timing only, no text transformation",
        },
        "layer_a_results": layer_a_results,
        "layer_b_results": layer_b_results,
        "aggregate": aggregate(layer_b_results),
        "run_dir": str(run_dir),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    artifact_path = run_dir / "deep_echo_fidelity_characterization_v1_result.json"
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
