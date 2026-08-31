"""Legacy-only subprocess worker for the future CORE_ONLY formal run.

This module must run under ``torment``.  Its only write route is the ordinary
local ``python -m torment_service`` HTTP ingest surface.  The qualified native
substrate is intentionally neither imported nor opened here.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any, Mapping

import numpy as np

from torment_service.motif_decision import _unit
from torment_service.motif_geometry import motif_radius_from_member_vectors

from .legacy_fixture_capture import (
    _SERVICE_ENV,
    _embedding_rows,
    _http_post,
    _latest_nodes,
    _read_json,
    _require_port_available,
    _start_service,
    _stop_service,
    _wait_for_service,
)
from .manifest import fingerprint_legacy_baseline, verify_legacy_baseline
from .protocol import D1ProtocolError, sha256_value
from .side_store_observation import (
    CORE_CHARACTER_FREE_L0_FINGERPRINT,
    CORE_SIDE_STORE_OBSERVATION_DIGEST,
    verify_frozen_d1_core_retained_side_stores,
)


def _tree_state(root: Path) -> dict[str, Any]:
    """Read-only durable-state characterization for the same legacy root."""
    rows: list[tuple[str, str]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        rows.append((relative, hashlib.sha256(path.read_bytes()).hexdigest()))
    return {"file_count": len(rows), "sha256": sha256_value(rows)}


def _legacy_motif_geometry(private_root: Path, motif_path: Path, motif_ids: object) -> list[dict[str, Any]]:
    nodes = _latest_nodes(private_root / "nodes.jsonl")
    vectors = _embedding_rows(private_root, nodes)
    document = _read_json(motif_path, {"motifs": {}})
    motifs = document.get("motifs", {}) if isinstance(document, dict) else {}
    result: list[dict[str, Any]] = []
    for motif_id in motif_ids if isinstance(motif_ids, list) else ():
        motif = motifs.get(motif_id) if isinstance(motifs, dict) else None
        if not isinstance(motif, dict):
            raise D1ProtocolError("legacy HTTP response references a missing current motif")
        centroid = motif.get("centroid")
        members = motif.get("members")
        if not isinstance(centroid, list) or not isinstance(members, list):
            raise D1ProtocolError("legacy motif has no current centroid/member inventory")
        result.append({
            "runtime_motif_id": str(motif_id),
            "radius": motif_radius_from_member_vectors(
                centroid,
                (_unit(vectors[eid]) if isinstance(eid, int) and eid in vectors else None for eid in members),
            ),
            "member_count": len(members),
        })
    return result


def _post_write_intent(response: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "qualified_post_write_outputs": {"proposal_id": response.get("proposal_id")},
        "deterministic_runtime_ordering": ["contradiction", "srg", "hivemind", "derived", "world", "proposal"],
    }


def _legacy_evidence(
    *, request: Mapping[str, Any], response: Mapping[str, Any], private_root: Path, motif_path: Path,
) -> dict[str, Any]:
    stored, reinforced = bool(response.get("stored")), bool(response.get("reinforced"))
    eid = response.get("eid")
    node = _latest_nodes(private_root / "nodes.jsonl").get(eid) if isinstance(eid, int) else None
    payload = dict((node or {}).get("payload", {}) or {})
    signals = dict(response.get("signals", {}) or {})
    motifs = list(response.get("motifs", []) or [])
    supplied = request.get("supplied_embedding_base64")
    if not isinstance(supplied, str):
        raise D1ProtocolError("legacy formal request has no frozen raw embedding")
    vector = np.frombuffer(base64.b64decode(supplied), dtype=np.float32)
    lifecycle = None if not stored else {
        "state": str(payload.get("lifecycle_state", "ACTIVE")),
        "authoritative": bool(payload.get("lifecycle_authoritative", False)),
    }
    return {
        "storage": {
            "stored": stored,
            "reinforced": reinforced,
            "compatible_eid": stored,
            "summary": str(payload.get("summary", request.get("supplied_summary", ""))),
            "memory_type": str(signals.get("memory_type", "episode")),
            "memory_class": str(payload.get("memory_class", "core")),
            "lifecycle": lifecycle,
            "governance": {"state": str(payload.get("governance_state", "UNKNOWN"))},
            "provenance": dict(payload.get("provenance", {}) or {}) or None,
            "raw_representation_bytes": supplied,
            "raw_representation_vector": vector.tolist(),
            "motif_membership": motifs,
            "motif_geometry": _legacy_motif_geometry(private_root, motif_path, motifs),
            "conflict": response.get("conflict"),
            "strength": float(signals.get("strength", 0.0)),
            "confidence": float(signals.get("confidence", 0.0)),
            "half_life_days": float(signals.get("half_life", 0.0)),
            "reinforcement_count": int(payload.get("reinforcement_count", 0) or 0),
        },
        "post_write": _post_write_intent(response),
        "optional_feature_divergences": [],
    }


class _LegacyWorkerSession:
    def __init__(self) -> None:
        self._root: Path | None = None
        self._workspace_id = self._agent_id = self._domain_id = ""
        self._service = None

    def open(self, value: Mapping[str, Any]) -> dict[str, Any]:
        source = Path(str(value.get("source_l0_root", ""))).resolve()
        root = Path(str(value.get("arm_root", ""))).resolve()
        if self._root is not None or not source.is_dir() or root.exists():
            raise D1ProtocolError("legacy formal worker requires one new mutable clone root")
        workspace, agent, domain = (str(value.get(name, "")) for name in ("workspace_id", "agent_id", "domain_id"))
        if not all((workspace, agent, domain)):
            raise D1ProtocolError("legacy formal worker requires explicit core scope facts")
        shutil.copytree(source, root)
        self._root, self._workspace_id, self._agent_id, self._domain_id = root, workspace, agent, domain
        self._start()
        return {"legacy_environment": "torment", "service_command": "python -m torment_service"}

    def replay_http(self, value: Mapping[str, Any]) -> dict[str, Any]:
        root = self._require_open()
        request = value.get("request")
        if not isinstance(request, dict):
            raise D1ProtocolError("legacy formal worker received a malformed HTTP request")
        required = {"text", "supplied_summary", "supplied_embedding_base64", "supplied_embedding_encoding", "step", "scope", "domain_id"}
        if not required.issubset(request):
            raise D1ProtocolError("legacy formal worker received incomplete frozen HTTP facts")
        encoded = request["supplied_embedding_base64"]
        if request["supplied_embedding_encoding"] != "float32-le-c-384" or not isinstance(encoded, str):
            raise D1ProtocolError("legacy formal worker received a non-frozen embedding transport")
        vector = np.frombuffer(base64.b64decode(encoded), dtype=np.float32)
        if vector.shape != (384,) or not np.isfinite(vector).all():
            raise D1ProtocolError("legacy formal worker received an invalid embedding vector")
        payload = {
            "workspace_id": self._workspace_id, "agent_id": self._agent_id,
            "text": request["text"], "supplied_summary": request["supplied_summary"],
            "supplied_embedding": vector.tolist(), "step": request["step"],
            "scope": request["scope"], "domain_id": request["domain_id"],
        }
        response = _http_post(payload)
        private = root / "workspaces" / self._workspace_id / "agents" / self._agent_id / "private"
        motif = root / "workspaces" / self._workspace_id / "domains" / self._domain_id / "motifs.json"
        return _legacy_evidence(request=request, response=response, private_root=private, motif_path=motif)

    def capture_durable_state(self) -> dict[str, Any]:
        return _tree_state(self._require_open())

    def restart_cleanly(self) -> dict[str, Any]:
        root = self._require_open()
        self._stop()
        if not root.is_dir():
            raise D1ProtocolError("legacy formal restart lost its original arm root")
        self._start()
        return {"restarted_same_root": True}

    def search_by_embedding(self, value: Mapping[str, Any]) -> dict[str, Any]:
        root = self._require_open()
        encoded = value.get("vector_base64")
        if not isinstance(encoded, str):
            raise D1ProtocolError("legacy retrieval received no vector")
        vector = np.frombuffer(base64.b64decode(encoded), dtype=np.float32)
        if vector.shape != (384,) or not np.isfinite(vector).all():
            raise D1ProtocolError("legacy retrieval vector is invalid")
        private = root / "workspaces" / self._workspace_id / "agents" / self._agent_id / "private"
        rows = _embedding_rows(private, _latest_nodes(private / "nodes.jsonl"))
        query = _unit(vector)
        ranking = sorted(
            ((str(eid), float(np.dot(query, _unit(candidate)))) for eid, candidate in rows.items()),
            key=lambda item: (-item[1], int(item[0])),
        )[:8]
        return {"ranking": [[identity, score] for identity, score in ranking]}

    def close(self) -> dict[str, Any]:
        self._stop()
        return {"closed": True}

    def _require_open(self) -> Path:
        if self._root is None or self._service is None:
            raise D1ProtocolError("legacy formal worker is not open")
        if self._service.poll() is not None:
            raise D1ProtocolError("legacy torment_service exited unexpectedly")
        return self._root

    def _start(self) -> None:
        if self._root is None:
            raise D1ProtocolError("legacy formal worker has no arm root")
        _require_port_available()
        self._service = _start_service(self._root, {"TORMENT_CHARACTER_ENABLE": "0"})
        _wait_for_service(self._service)

    def _stop(self) -> None:
        if self._service is not None:
            _stop_service(self._service)
            if self._service.poll() is None:
                raise D1ProtocolError("legacy torment_service did not terminate cleanly")
            self._service = None


def _verify_source(l0_root: str | Path) -> dict[str, Any]:
    root = Path(l0_root).resolve()
    baseline = fingerprint_legacy_baseline(
        root=root, workspace_id="d1core20260831", agent_id="d1coreagent",
        domain_id="research", character_seed_required=False,
    )
    verify_legacy_baseline(baseline)
    observation = verify_frozen_d1_core_retained_side_stores(
        root=root, workspace_id="d1core20260831", agent_id="d1coreagent", domain_id="research",
    )
    return {
        "l0_fingerprint_sha256": baseline.digest,
        "side_store_observation_digest": observation.digest,
        "character_arm_absent": baseline.character_seed is None and baseline.character_state is None,
        "native_formal_event_count": 0,
    }


def _serve() -> int:
    session = _LegacyWorkerSession()
    handlers = {
        "open": session.open,
        "replay_http": session.replay_http,
        "capture_durable_state": lambda _value: session.capture_durable_state(),
        "restart_cleanly": lambda _value: session.restart_cleanly(),
        "search_by_embedding": session.search_by_embedding,
        "close": lambda _value: session.close(),
    }
    for line in sys.stdin:
        try:
            message = json.loads(line)
            if not isinstance(message, dict) or not isinstance(message.get("command"), str):
                raise D1ProtocolError("legacy formal IPC request is malformed")
            command = message.pop("command")
            handler = handlers.get(command)
            if handler is None:
                raise D1ProtocolError("legacy formal IPC command is unknown")
            result = handler(message)
            print(json.dumps({"ok": True, "value": result}, sort_keys=True), flush=True)
            if command == "close":
                return 0
        except Exception as exc:
            print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, sort_keys=True), flush=True)
            return 1
    session.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="legacy-only worker for CORE_ONLY D1")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--verify-source", action="store_true")
    parser.add_argument("--l0-root")
    args = parser.parse_args(argv)
    if args.serve:
        return _serve()
    if args.verify_source:
        print(json.dumps(_verify_source(args.l0_root), sort_keys=True))
        return 0
    parser.error("select --serve or --verify-source")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
