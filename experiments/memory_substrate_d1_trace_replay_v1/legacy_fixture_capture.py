"""Real HTTP-only L0 clone qualification for the still-legacy D1 fixtures.

This operator helper deliberately runs only in ``torment``.  It never opens a
native core, imports a native router, or records a native outcome.  The output
is a new immutable JSON capture that later qualified-environment code seals
into the concrete D1 fixture artifact.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from typing import Any
from urllib.request import Request, urlopen

import numpy as np

from torment_service.fabric import _detect_canon_conflict
from torment_service.governance import resolve_governance
from torment_service.lifecycle import validate_lifecycle_envelope
from torment_service.motif_decision import (
    CURRENT_MOTIF_DECISION_POLICY,
    MotifReadModel,
    _unit,
    cosine,
    motif_density,
    motif_gravity_bonus,
)

from .baseline import LegacyBaselineBuilder, LegacyBaselineSpec, UrllibHttpTransport
from .manifest import fingerprint_legacy_baseline, verify_legacy_baseline
from .protocol import D1ProtocolError, sha256_value


_SERVICE_ENV = {
    "TORMENT_EMBED_PROVIDER": "hash",
    "TORMENT_HASH_DIM": "384",
    "TORMENT_HIVEMIND_ENABLE": "0",
    "TORMENT_CHECKPOINT_ENABLE": "0",
    "TORMENT_COMPRESS_ENABLE": "0",
    "TORMENT_SRG_ENABLE": "0",
    "TORMENT_AFFECT_ENABLE": "0",
    "TORMENT_REINFORCE_SIM_THRESHOLD": "0.92",
}
_WORKSPACE_DOMAIN = "research"
_REINFORCE_THRESHOLD = 0.92
_ATTACH_THRESHOLD = 0.76


def _vector(index: int) -> np.ndarray:
    values = np.zeros(384, dtype=np.float32)
    values[index] = np.float32(1.0)
    return values


def _event(
    fixture_id: str, text: str, vector_index: int, step: int, *, kind: str, expected: str,
) -> dict[str, Any]:
    vector = _vector(vector_index)
    request = {
        "text": text,
        "supplied_summary": text,
        "supplied_embedding_base64": base64.b64encode(vector.tobytes(order="C")).decode("ascii"),
        "supplied_embedding_sha256": hashlib.sha256(vector.tobytes(order="C")).hexdigest(),
        "supplied_embedding_encoding": "float32-le-c-384",
        "step": step,
        "scope": "private",
        "domain_id": _WORKSPACE_DOMAIN,
    }
    return {
        "fixture_id": fixture_id,
        "kind": kind,
        "expected_duplicate_path": expected,
        "request": request,
        "request_sha256": sha256_value(request),
    }


def canonical_trace_specs() -> dict[str, tuple[dict[str, Any], ...]]:
    """The fixed Stage-1 event order, with no results prefilled."""
    stable_m2 = "M2 calibration claim is stable and verified."
    stable_m4 = "M4 calibration claim is stable and verified."
    stable_seq = "Sequential calibration claim is stable and verified."
    return {
        "M1_CREATE": (_event("M1-create", "M1 calibration claim is stable and verified.", 0, 1, kind="M1_CREATE", expected="CREATE_NO_CANDIDATE"),),
        "M2_REINFORCE": (
            _event("M2-create", stable_m2, 0, 1, kind="M2_REINFORCE", expected="CREATE_NO_CANDIDATE"),
            _event("M2-reinforce", stable_m2, 0, 2, kind="M2_REINFORCE", expected="REINFORCE_MATCH"),
        ),
        "M3_DISTINCT": (
            _event("M3-create", "M3 calibration claim is stable and verified.", 0, 1, kind="M3_DISTINCT", expected="CREATE_NO_CANDIDATE"),
            _event("M3-distinct", "Independent measurement three is verified separately.", 1, 2, kind="M3_DISTINCT", expected="CREATE_DISTINCT_BELOW_THRESHOLD"),
        ),
        "M4_CONTRADICTION": (
            _event("M4-create", stable_m4, 0, 1, kind="M4_CONTRADICTION", expected="CREATE_NO_CANDIDATE"),
            _event("M4-contradiction", "M4 calibration claim is not stable and verified.", 0, 2, kind="M4_CONTRADICTION", expected="CREATE_CONTRADICTION_GUARD"),
        ),
        "M5_NO_WRITE": (_event("M5-no-write", "", 1, 1, kind="M5_NO_WRITE", expected="NOT_APPLICABLE"),),
        "SEQUENTIAL": (
            _event("S-create", stable_seq, 0, 1, kind="SEQUENTIAL", expected="CREATE_NO_CANDIDATE"),
            _event("S-reinforce", stable_seq, 0, 2, kind="SEQUENTIAL", expected="REINFORCE_MATCH"),
            _event("S-distinct", "Sequential independent measurement is verified separately.", 1, 3, kind="SEQUENTIAL", expected="CREATE_DISTINCT_BELOW_THRESHOLD"),
            _event("S-contradiction", "Sequential calibration claim is not stable and verified.", 0, 4, kind="SEQUENTIAL", expected="CREATE_CONTRADICTION_GUARD"),
        ),
        "CHARACTER_SUBARM": (
            _event("C-prep-22", "Character preparation observation alpha is stable.", 1, 22, kind="CHARACTER_SUBARM", expected="CREATE_NO_CANDIDATE"),
            _event("C-prep-23", "Character preparation observation beta is stable.", 2, 23, kind="CHARACTER_SUBARM", expected="CREATE_NO_CANDIDATE"),
            _event("C-prep-24", "Character preparation observation gamma is stable.", 3, 24, kind="CHARACTER_SUBARM", expected="CREATE_NO_CANDIDATE"),
            _event("C-admin-25", "Character administration observation delta is stable.", 4, 25, kind="CHARACTER_SUBARM", expected="CREATE_NO_CANDIDATE"),
        ),
    }


def core_only_trace_specs() -> dict[str, tuple[dict[str, Any], ...]]:
    """Fresh core-L0 requests; these intentionally do not reuse the Character fixture bytes."""
    stable_m2 = "Core-only M2 calibration claim is stable and independently verified."
    stable_m4 = "Core-only M4 calibration claim is stable and verified; independently evidenced."
    stable_seq = "Core-only sequential calibration claim is stable and verified; independently evidenced."
    return {
        "M1_CREATE": (_event("CORE-M1-create", "Core-only M1 calibration claim is stable and independently verified.", 10, 101, kind="M1_CREATE", expected="CREATE_NO_CANDIDATE"),),
        "M2_REINFORCE": (
            _event("CORE-M2-create", stable_m2, 10, 101, kind="M2_REINFORCE", expected="CREATE_NO_CANDIDATE"),
            _event("CORE-M2-reinforce", stable_m2, 10, 102, kind="M2_REINFORCE", expected="REINFORCE_MATCH"),
        ),
        "M3_DISTINCT": (
            _event("CORE-M3-create", "Core-only M3 calibration claim is stable and independently verified.", 10, 101, kind="M3_DISTINCT", expected="CREATE_NO_CANDIDATE"),
            _event("CORE-M3-distinct", "Core-only independent measurement three is verified separately.", 11, 102, kind="M3_DISTINCT", expected="CREATE_DISTINCT_BELOW_THRESHOLD"),
        ),
        "M4_CONTRADICTION": (
            _event("CORE-M4-create", stable_m4, 10, 101, kind="M4_CONTRADICTION", expected="CREATE_NO_CANDIDATE"),
            _event("CORE-M4-contradiction", "Core-only M4 calibration claim is not stable and verified; independently evidenced.", 10, 102, kind="M4_CONTRADICTION", expected="CREATE_CONTRADICTION_GUARD"),
        ),
        "M5_NO_WRITE": (_event("CORE-M5-no-write", "", 11, 101, kind="M5_NO_WRITE", expected="NOT_APPLICABLE"),),
        "SEQUENTIAL": (
            _event("CORE-S-create", stable_seq, 10, 101, kind="SEQUENTIAL", expected="CREATE_NO_CANDIDATE"),
            _event("CORE-S-reinforce", stable_seq, 10, 102, kind="SEQUENTIAL", expected="REINFORCE_MATCH"),
            _event("CORE-S-distinct", "Core-only sequential independent measurement is verified separately.", 11, 103, kind="SEQUENTIAL", expected="CREATE_DISTINCT_BELOW_THRESHOLD"),
            _event("CORE-S-contradiction", "Core-only sequential calibration claim is not stable and verified; independently evidenced.", 10, 104, kind="SEQUENTIAL", expected="CREATE_CONTRADICTION_GUARD"),
        ),
    }


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    value = json.loads(path.read_text(encoding="utf-8"))
    return value


def _latest_nodes(path: Path) -> dict[int, dict[str, Any]]:
    values: dict[int, dict[str, Any]] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict) and isinstance(row.get("eid"), int):
            values[int(row["eid"])] = row
    return values


def _embedding_rows(private_root: Path, nodes: dict[int, dict[str, Any]]) -> dict[int, np.ndarray]:
    """Read only captured legacy float32 rows, using the persisted shard maps."""
    embeddings = private_root / "embeddings"
    result: dict[int, np.ndarray] = {}
    for map_path in sorted(embeddings.glob("*.map.jsonl")):
        shard_path = map_path.with_name(map_path.name.replace(".map.jsonl", ".npy"))
        if not shard_path.is_file():
            continue
        matrix = np.load(shard_path, mmap_mode="r")
        for line in map_path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            eid = value.get("eid")
            row = value.get("row")
            if not isinstance(eid, int) or eid not in nodes or not isinstance(row, int):
                continue
            result[eid] = np.asarray(matrix[row], dtype=np.float32).reshape(-1).copy()
    return result


def _symbol_state(agent_root: Path) -> dict[str, Any]:
    value = _read_json(agent_root / "symbol_state.json", {})
    if not isinstance(value, dict):
        value = {}
    return {
        "prior_symbol": str(value.get("last_symbol", "") or ""),
        "prior_symbol_trace": list(value.get("symbol_trace", []) or []),
        "prior_motif_id": str(value.get("last_motif_id", "") or ""),
        "prior_tension": float(value.get("last_tension", 0.0) or 0.0),
    }


def _motif_diagnostics(motif_path: Path, embedding: np.ndarray) -> dict[str, Any]:
    raw = _read_json(motif_path, {"motifs": {}})
    motifs = raw.get("motifs", {}) if isinstance(raw, dict) else {}
    candidate = _unit(embedding)
    best: tuple[float, float, float, MotifReadModel] | None = None
    max_member_count = 0
    for value in motifs.values() if isinstance(motifs, dict) else ():
        if not isinstance(value, dict):
            continue
        centroid = tuple(float(item) for item in value.get("centroid", []))
        if len(centroid) != candidate.size:
            continue
        state = MotifReadModel(
            runtime_motif_id=str(value.get("motif_id", "")), domain_id=str(value.get("domain_id", "")),
            label=str(value.get("label", "")), centroid=centroid,
            strength=float(value.get("strength", 0.0) or 0.0),
            member_count=len(value.get("members", []) or []),
            contributing_agents=tuple(str(item) for item in value.get("contributing_agents", []) or []),
            stability_score=float(value.get("stability_score", 0.0) or 0.0),
            created_ts=int(value.get("created_ts", 0) or 0), last_active_ts=int(value.get("last_active_ts", 0) or 0),
        )
        max_member_count = max(max_member_count, state.member_count)
        raw_similarity = cosine(candidate, state.centroid_np())
        score = float(raw_similarity + motif_gravity_bonus(state, CURRENT_MOTIF_DECISION_POLICY))
        effective = float(max(0.62, _ATTACH_THRESHOLD - (0.04 * motif_density(state.member_count) + 0.03 * np.clip(state.strength, 0.0, 1.0))))
        if best is None or score > best[0]:
            best = (score, raw_similarity, effective, state)
    if best is None:
        return {"attach_score": -1.0, "raw_similarity": None, "effective_attach_threshold": _ATTACH_THRESHOLD, "pre_event_motif_member_count": max_member_count}
    return {
        "attach_score": best[0], "raw_similarity": best[1],
        "effective_attach_threshold": best[2], "pre_event_motif_member_count": max_member_count,
        "selected_motif_id": best[3].runtime_motif_id,
    }


def _http_post(payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        "http://127.0.0.1:8787/agent/ingest", data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=30.0) as response:  # nosec B310 -- hard-coded local service
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise D1ProtocolError("legacy qualification service returned a non-object")
    return value


def _wait_for_service(process: subprocess.Popen[bytes]) -> None:
    for _ in range(60):
        if process.poll() is not None:
            raise D1ProtocolError("legacy qualification service exited before becoming ready")
        try:
            with urlopen("http://127.0.0.1:8787/openapi.json", timeout=0.5):  # nosec B310 -- hard-coded local service
                return
        except Exception:
            time.sleep(0.25)
    raise D1ProtocolError("legacy qualification service did not become ready")


def _start_service(
    data_root: Path,
    extra_environment: dict[str, str] | None = None,
) -> subprocess.Popen[bytes]:
    env = dict(os.environ)
    env.update(_SERVICE_ENV)
    if extra_environment:
        env.update(extra_environment)
    env["TORMENT_DATA_DIR"] = str(data_root)
    return subprocess.Popen(
        [sys.executable, "-m", "torment_service"], env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _require_port_available() -> None:
    try:
        with socket.create_connection(("127.0.0.1", 8787), timeout=0.2):
            raise D1ProtocolError("legacy fixture capture requires an otherwise unused local service port")
    except ConnectionRefusedError:
        return
    except OSError:
        return


def _stop_service(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=15)


def create_character_free_core_l0(
    *, l0_root: str | Path, workspace_id: str, agent_id: str,
) -> dict[str, Any]:
    """Build one disposable, Character-free core L0 through real legacy HTTP.

    This is a preflight construction only.  It starts no native service and
    writes no formal result.  A fresh data root and a currently unused local
    port are required so it cannot overlap a real legacy instance.
    """
    root = Path(l0_root).resolve()
    if root.exists():
        raise D1ProtocolError("Character-free core L0 destination must be new")
    _require_port_available()
    process = _start_service(root, {"TORMENT_CHARACTER_ENABLE": "0"})
    transport = UrllibHttpTransport("http://127.0.0.1:8787")
    builder = LegacyBaselineBuilder(
        transport,
        LegacyBaselineSpec(root, workspace_id, agent_id, None),
    )
    try:
        _wait_for_service(process)
        builder.create_l0()
        vector = np.zeros(384, dtype=np.float32)
        vector[0] = np.float32(1.0)
        response = transport.request("POST", "/agent/ingest", {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "text": "Core migration baseline evidence is deterministically stored.",
            "supplied_summary": "Core migration baseline evidence is deterministically stored.",
            "supplied_embedding": vector.tolist(),
            "step": 1,
            "scope": "private",
            "domain_id": _WORKSPACE_DOMAIN,
        })
        if response.get("stored") is not True or response.get("reinforced") is True:
            raise D1ProtocolError("Character-free core baseline ingest was not one ordinary stored memory")
    finally:
        _stop_service(process)
    baseline = builder.freeze_after_clean_shutdown(service_has_stopped=True)
    private = root / "workspaces" / workspace_id / "agents" / agent_id / "private"
    nodes = _latest_nodes(private / "nodes.jsonl")
    if len(nodes) != 1:
        raise D1ProtocolError("Character-free core L0 must contain exactly one ordinary memory")
    row = next(iter(nodes.values()))
    payload = row.get("payload")
    if not isinstance(payload, dict):
        raise D1ProtocolError("Character-free core L0 memory has no payload")
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        raise D1ProtocolError("Character-free core L0 memory lacks exact ProvenanceV1 evidence")
    try:
        from torment_service.provenance_v1 import ProvenanceV1
        if ProvenanceV1.from_dict(provenance).to_dict() != provenance:
            raise ValueError("non-canonical")
        lifecycle = validate_lifecycle_envelope(payload.get("lifecycle_status"))
        if not lifecycle.is_authoritative_on_row:
            raise ValueError("not row-authoritative")
    except (TypeError, ValueError) as exc:
        raise D1ProtocolError("Character-free core L0 semantic evidence is not exact") from exc
    if "governance" not in payload and resolve_governance(payload).to_dict() != resolve_governance({}).to_dict():
        raise D1ProtocolError("Character-free core L0 does not meet absent-governance legacy semantics")
    reference = payload.get("embedding_ref")
    if not isinstance(reference, dict) or set(reference) != {"shard", "row", "dim"}:
        raise D1ProtocolError("Character-free core L0 lacks the current compact embedding reference")
    if any(
        not isinstance(reference[name], int) or isinstance(reference[name], bool)
        for name in ("shard", "row", "dim")
    ) or reference["shard"] < 0 or reference["row"] < 0 or reference["dim"] <= 0:
        raise D1ProtocolError("Character-free core L0 compact embedding reference is invalid")
    return {
        "schema": "memory-substrate-d1-character-free-core-l0-v1",
        "l0_root": str(root),
        "l0_fingerprint_sha256": baseline.digest,
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "stored_eid": row.get("eid"),
        "governance_evidence": "EXPLICIT" if "governance" in payload else "LEGACY_ABSENT_GOVERNANCE_DEFAULT_V1",
        "embedding_reference": dict(reference),
        "character_seed_planting": False,
        "native_formal_event_count": 0,
    }


def _storage_facts(
    *, event: dict[str, Any], response: dict[str, Any], node: dict[str, Any] | None,
    identity: dict[str, Any], pre_symbols: dict[str, Any], workspace_id: str, agent_id: str,
) -> dict[str, Any]:
    payload = dict((node or {}).get("payload", {}) or {})
    signals = dict(response.get("signals", {}) or {})
    tri = dict(response.get("tri_mod", {}) or {})
    debug = dict(response.get("debug", {}) or {})
    created_ts = int(payload.get("created_ts", payload.get("created_at", 0)) or 0)
    last_reinforced_ts = int(payload.get("last_reinforced_ts", created_ts) or created_ts)
    phase = {
        "phase_duration_steps": int(payload.get("phase_duration_steps", 0) or 0),
        "corridor_duration_steps": int(payload.get("corridor_duration_steps", 0) or 0),
    }
    return {
        "workspace_id": workspace_id, "agent_id": agent_id, "scope": "private", "domain_id": _WORKSPACE_DOMAIN,
        "native_operation_key": f"D1:REPLAY:{event['fixture_id']}:0:{event['request_sha256'][:24]}",
        "text": event["request"]["text"], "summary": event["request"]["supplied_summary"],
        "embedding": {"encoding": event["request"]["supplied_embedding_encoding"], "base64": event["request"]["supplied_embedding_base64"], "sha256": event["request"]["supplied_embedding_sha256"]},
        "embedder_lane": {"provider": "hash", "model": "hash:384:torment", "dimension": 384, "representation_class": "COMPAT_EMBEDDING", "generation": 1, "derivation_contract_version": "compat-embedding-v1", "encoding_id": "RAW_VECTOR", "dtype": "float32"},
        "memory_type": str(signals.get("memory_type", "episode")), "memory_class": str(payload.get("memory_class", "core")),
        "strength": float(signals.get("strength", 0.0)), "confidence": float(signals.get("confidence", 0.0)),
        "promotion_score": float(signals.get("promotion_score", 0.0)), "half_life_days": float(signals.get("half_life", 0.0)),
        "logical_step": int(event["request"]["step"]), "created_ts": created_ts, "last_active_ts": int(payload.get("last_active_ts", created_ts) or created_ts), "last_reinforced_ts": last_reinforced_ts,
        "provenance": dict(payload.get("provenance", {}) or {}),
        "governance": {"protected": False, "non_shareable": False, "decay_accelerated": False, "collective_export_blocked": False, "collective_reingest_blocked": False},
        "flexible_payload": {"links": []}, "attach_threshold": _ATTACH_THRESHOLD,
        "stability_delta": float(signals.get("stability_delta", 0.0)), **pre_symbols,
        "last_tool_refresh_ts": payload.get("last_tool_refresh_ts"), "tri_mod": tri, "debug": debug,
        "srg_state": None, "phase_durations": phase, "affect_tag": None, "affect_conf": None,
        "skip_packet_emission": False,
    }


def _qualify_event(
    *, event: dict[str, Any], response: dict[str, Any], pre_motif: dict[str, Any], pre_nodes: dict[int, dict[str, Any]], pre_embeddings: dict[int, np.ndarray],
) -> dict[str, Any]:
    expected = str(event["expected_duplicate_path"])
    raw_similarity: float | None = None
    contradiction: bool | None = None
    if expected in {"REINFORCE_MATCH", "CREATE_DISTINCT_BELOW_THRESHOLD", "CREATE_CONTRADICTION_GUARD"}:
        candidate = np.frombuffer(base64.b64decode(event["request"]["supplied_embedding_base64"]), dtype=np.float32)
        prior = next((row for row in pre_nodes.values() if str((row.get("payload") or {}).get("summary", "")) == event["request"]["supplied_summary"]), None)
        if expected == "CREATE_CONTRADICTION_GUARD":
            prior = next((row for row in pre_nodes.values() if "stable and verified" in str((row.get("payload") or {}).get("summary", ""))), prior)
        if expected == "CREATE_DISTINCT_BELOW_THRESHOLD":
            raw_similarity = max(
                (float(np.dot(_unit(candidate), _unit(vector))) for vector in pre_embeddings.values()),
                default=-1.0,
            )
        elif prior is not None:
            prior_vector = pre_embeddings.get(int(prior["eid"]))
            if prior_vector is not None:
                raw_similarity = float(np.dot(_unit(candidate), _unit(prior_vector)))
                contradiction = bool(_detect_canon_conflict(event["request"]["supplied_summary"], str((prior.get("payload") or {}).get("summary", "")), raw_similarity)[0])
        if raw_similarity is None:
            raise D1ProtocolError(f"{event['fixture_id']} lacked the required legacy duplicate candidate")
    signals = dict(response.get("signals", {}) or {})
    tri = dict(response.get("tri_mod", {}) or {})
    effective_write_threshold = 0.45 * float(tri.get("write_mult", 1.0))
    result = {
        "duplicate_decision": expected,
        "raw_similarity": raw_similarity,
        "reinforce_threshold": _REINFORCE_THRESHOLD if raw_similarity is not None else None,
        "contradiction_guard_observed": contradiction,
        "expected_reinforced": bool(response.get("reinforced")) if raw_similarity is not None else (False if expected == "CREATE_NO_CANDIDATE" else None),
        "write_gate": {"write_intent": bool(signals.get("write_intent")), "strength": float(signals.get("strength", 0.0)), "effective_write_threshold": effective_write_threshold, "write_band": 0.08},
        "motif": pre_motif,
        "links": list(signals.get("links", []) or []),
    }
    if expected == "REINFORCE_MATCH" and not (raw_similarity >= _REINFORCE_THRESHOLD + 0.02 and not contradiction and response.get("reinforced") is True):
        raise D1ProtocolError("M2 legacy reinforcement did not meet its frozen high-similarity qualification")
    if expected == "CREATE_DISTINCT_BELOW_THRESHOLD" and not (raw_similarity <= _REINFORCE_THRESHOLD - 0.02 and response.get("reinforced") is False and response.get("stored") is True):
        raise D1ProtocolError("M3 legacy distinct result did not meet its frozen low-similarity qualification")
    if expected == "CREATE_CONTRADICTION_GUARD" and not (raw_similarity >= _REINFORCE_THRESHOLD + 0.02 and contradiction is True and response.get("reinforced") is False and response.get("stored") is True):
        raise D1ProtocolError("M4 legacy contradiction did not meet its frozen high-similarity qualification")
    return result


def _capture_legacy_only_fixture_set(
    *, l0_root: str | Path, clone_root: str | Path, destination: str | Path,
    workspace_id: str, agent_id: str, profile: str,
    character_seed_required: bool, specs: dict[str, tuple[dict[str, Any], ...]],
) -> dict[str, Any]:
    """Run the fixed trace suite against fresh L0 clones and seal legacy evidence.

    The caller must execute this helper under the unchanged ``torment``
    environment.  It refuses an occupied local service port, pre-existing
    clone destinations, or a pre-existing capture destination.
    """
    l0 = Path(l0_root).resolve()
    clones = Path(clone_root).resolve()
    output = Path(destination).resolve()
    if output.exists() or clones.exists():
        raise D1ProtocolError("legacy D1 capture destinations must be new")
    baseline = fingerprint_legacy_baseline(
        root=l0, workspace_id=workspace_id, agent_id=agent_id,
        character_seed_required=character_seed_required,
    )
    verify_legacy_baseline(baseline)
    captures: list[dict[str, Any]] = []
    for arm_id, events in specs.items():
        clone = clones / arm_id
        shutil.copytree(l0, clone)
        _require_port_available()
        service = _start_service(
            clone, {"TORMENT_CHARACTER_ENABLE": "0"} if not character_seed_required else None,
        )
        try:
            _wait_for_service(service)
            workspace = clone / "workspaces" / workspace_id
            agent_root = workspace / "agents" / agent_id
            private = agent_root / "private"
            identity = _read_json(agent_root / "identity.json", {})
            for event in events:
                request = event["request"]
                vector = np.frombuffer(base64.b64decode(request["supplied_embedding_base64"]), dtype=np.float32).copy()
                pre_nodes = _latest_nodes(private / "nodes.jsonl")
                pre_embeddings = _embedding_rows(private, pre_nodes)
                pre_symbols = _symbol_state(agent_root)
                pre_motif = _motif_diagnostics(workspace / "domains" / _WORKSPACE_DOMAIN / "motifs.json", vector)
                payload = {
                    "workspace_id": workspace_id, "agent_id": agent_id, "text": request["text"],
                    "supplied_summary": request["supplied_summary"], "supplied_embedding": vector.tolist(),
                    "step": request["step"], "scope": request["scope"], "domain_id": request["domain_id"],
                }
                response = _http_post(payload)
                node = _latest_nodes(private / "nodes.jsonl").get(response.get("eid")) if response.get("eid") is not None else None
                captures.append({
                    "arm_id": arm_id, **event, "legacy_response": response,
                    "storage_facts": _storage_facts(event=event, response=response, node=node, identity=identity, pre_symbols=pre_symbols, workspace_id=workspace_id, agent_id=agent_id),
                    "qualification": _qualify_event(event=event, response=response, pre_motif=pre_motif, pre_nodes=pre_nodes, pre_embeddings=pre_embeddings),
                })
            if arm_id == "CHARACTER_SUBARM":
                captures[-1]["character_state_after"] = _read_json(agent_root / "character_state.json", {})
                captures[-1]["character_memory_count_after"] = len(_latest_nodes(private / "nodes.jsonl"))
        finally:
            _stop_service(service)
    verify_legacy_baseline(baseline)
    document = {
        "schema": "memory-substrate-d1-legacy-only-http-capture-v1",
        "l0_fingerprint_sha256": baseline.digest,
        "l0_root": str(l0), "workspace_id": workspace_id, "agent_id": agent_id,
        "profile": profile,
        "service_environment": dict(sorted(_SERVICE_ENV.items())),
        "workspace_domains": [_WORKSPACE_DOMAIN],
        "captures": captures,
        "native_outcomes_inspected": False,
        "native_formal_event_count": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(str(output), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    return document


def capture_legacy_only_fixture_set(
    *, l0_root: str | Path, clone_root: str | Path, destination: str | Path,
    workspace_id: str, agent_id: str,
) -> dict[str, Any]:
    """Capture the original Character-extended preflight shape."""
    return _capture_legacy_only_fixture_set(
        l0_root=l0_root, clone_root=clone_root, destination=destination,
        workspace_id=workspace_id, agent_id=agent_id,
        profile="CHARACTER_EXTENDED", character_seed_required=True,
        specs=canonical_trace_specs(),
    )


def capture_core_only_legacy_fixture_set(
    *, l0_root: str | Path, clone_root: str | Path, destination: str | Path,
    workspace_id: str, agent_id: str,
) -> dict[str, Any]:
    """Capture only M1--M5 and sequential qualification from a Character-free core L0."""
    return _capture_legacy_only_fixture_set(
        l0_root=l0_root, clone_root=clone_root, destination=destination,
        workspace_id=workspace_id, agent_id=agent_id,
        profile="CORE_ONLY", character_seed_required=False,
        specs=core_only_trace_specs(),
    )


__all__ = [
    "canonical_trace_specs",
    "core_only_trace_specs",
    "capture_core_only_legacy_fixture_set",
    "capture_legacy_only_fixture_set",
    "create_character_free_core_l0",
]
