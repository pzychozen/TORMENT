"""Frozen, structural B5 retained-side-store evidence for the real D1 core L0.

This is deliberately experiment-local.  It does not teach B5 how to crawl a
legacy filesystem: it reads only the known D1 core structures, re-verifies the
entire immutable L0 fingerprint, and hands B5 caller-owned typed observations.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from torment_service.kernel.trajectory_v2 import TrajectoryChunkReaderV2, TrajectoryV2Verifier
from torment_service.substrate.migration import (
    RetainedSideStoreEIDObservation,
    RetainedSideStoreEIDObservationState,
    RetainedSideStoreEIDReference,
)

from .manifest import fingerprint_legacy_baseline
from .protocol import D1ProtocolError, sha256_value


CORE_CHARACTER_FREE_L0_FINGERPRINT = (
    "f74fc5f104a71788f21f0f60ed753d35c029b1427f04e04d850e9c65f78fde63"
)
CORE_SIDE_STORE_OBSERVATION_SOURCE_NAMESPACE_ID = UUID("65ba4708-2ced-400c-a35b-0df589600642")
CORE_SIDE_STORE_OBSERVATION_DIGEST = (
    "ed86e486a94080671c7eb672bf21cab96ec383a944c13492acc4a9616d081a4c"
)


class D1ObservationLocatorState(StrEnum):
    ABSENT = "ABSENT"
    PRESENT = "PRESENT"


@dataclass(frozen=True)
class D1ObservationLocator:
    relative_path: str
    state: D1ObservationLocatorState
    sha256: str | None

    def intent(self) -> dict[str, str | None]:
        return {"relative_path": self.relative_path, "state": self.state.value, "sha256": self.sha256}


@dataclass(frozen=True)
class D1RetainedSideStoreObservationEvidence:
    side_store: str
    observation: RetainedSideStoreEIDObservation
    locators: tuple[D1ObservationLocator, ...]

    def intent(self) -> dict[str, Any]:
        return {
            "side_store": self.side_store,
            "observation_state": self.observation.state.value,
            "references": [
                {
                    "side_store": reference.side_store,
                    "legacy_source_namespace_id": str(reference.legacy_source_namespace_id),
                    "eid": reference.eid,
                }
                for reference in self.observation.references
            ],
            "locators": [locator.intent() for locator in self.locators],
        }


@dataclass(frozen=True)
class D1CoreSideStoreObservationArtifact:
    l0_fingerprint_sha256: str
    workspace_id: str
    agent_id: str
    domain_id: str
    legacy_source_namespace_id: UUID
    observations: tuple[RetainedSideStoreEIDObservation, ...]
    evidence: tuple[D1RetainedSideStoreObservationEvidence, ...]

    def intent(self) -> dict[str, Any]:
        return {
            "schema": "memory-substrate-d1-core-retained-side-store-observation-v1",
            "l0_fingerprint_sha256": self.l0_fingerprint_sha256,
            "workspace_id": self.workspace_id,
            "agent_id": self.agent_id,
            "domain_id": self.domain_id,
            "legacy_source_namespace_id": str(self.legacy_source_namespace_id),
            "evidence": [item.intent() for item in self.evidence],
        }

    @property
    def digest(self) -> str:
        return sha256_value(self.intent())


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    try:
        values = tuple(
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise D1ProtocolError(f"D1 retained-side-store JSONL is unreadable: {path}") from exc
    if any(not isinstance(value, dict) for value in values):
        raise D1ProtocolError(f"D1 retained-side-store JSONL is not object-only: {path}")
    return values


def _locator(root: Path, relative_path: str) -> D1ObservationLocator:
    path = root / relative_path
    if not path.exists():
        return D1ObservationLocator(relative_path, D1ObservationLocatorState.ABSENT, None)
    if not path.is_file():
        raise D1ProtocolError(f"D1 expected side-store locator is not a regular file: {relative_path}")
    return D1ObservationLocator(
        relative_path, D1ObservationLocatorState.PRESENT, hashlib.sha256(path.read_bytes()).hexdigest()
    )


def _require_absent_store(root: Path, side_store: str, locations: tuple[str, ...]) -> D1RetainedSideStoreObservationEvidence:
    locators = tuple(_locator(root, location) for location in locations)
    if any(locator.state is not D1ObservationLocatorState.ABSENT for locator in locators):
        raise D1ProtocolError(
            f"D1 frozen complete-absent side store unexpectedly has a locator: {side_store}"
        )
    observation = RetainedSideStoreEIDObservation(
        side_store, RetainedSideStoreEIDObservationState.COMPLETE_ABSENT
    )
    return D1RetainedSideStoreObservationEvidence(side_store, observation, locators)


def _require_private_eid_one(
    root: Path,
    *,
    workspace_id: str,
    agent_id: str,
    domain_id: str,
    legacy_source_namespace_id: UUID,
) -> D1RetainedSideStoreObservationEvidence:
    private = f"workspaces/{workspace_id}/agents/{agent_id}/private"
    trajectory = f"{private}/trajectories/v2"
    genesis = root / f"{trajectory}/entity_genesis.jsonl"
    nodes = root / f"{private}/nodes.jsonl"
    events = root / f"{private}/memory_events.jsonl"
    if not all(path.is_file() for path in (genesis, nodes, events)):
        raise D1ProtocolError("D1 trajectory evidence lacks its established private structural carriers")
    genesis_rows = _read_jsonl(genesis)
    node_rows = _read_jsonl(nodes)
    event_rows = _read_jsonl(events)
    if [row.get("eid") for row in genesis_rows] != [1] or any(
        row.get("type") != "ENTITY_GENESIS" for row in genesis_rows
    ):
        raise D1ProtocolError("D1 trajectory genesis is not exactly EID 1")
    if len(node_rows) != 1 or node_rows[0].get("eid") != 1 or node_rows[0].get("payload", {}).get("scope") != "private":
        raise D1ProtocolError("D1 private node carrier is not exactly private EID 1")
    if len(event_rows) != 1 or event_rows[0].get("eid") != 1 or event_rows[0].get("scope") != "private":
        raise D1ProtocolError("D1 private memory-event carrier is not exactly private EID 1")
    verifier = TrajectoryV2Verifier(str(root / private)).verify(mode="live")
    if not verifier.valid or verifier.checked_records != 1 or verifier.active_open_tails != 1:
        raise D1ProtocolError("D1 live trajectory verifier did not prove the frozen EID 1 tail")
    chunk_root = root / f"{trajectory}/chunks"
    partials = tuple(sorted(chunk_root.rglob("*.partial")))
    sealed = tuple(sorted(chunk_root.rglob("*.trj2")))
    if len(partials) != 1 or sealed:
        raise D1ProtocolError("D1 frozen trajectory chunk topology changed")
    frames = tuple(TrajectoryChunkReaderV2(partials[0]).iter_steps())
    if len(frames) != 1 or [record.eid for record in frames[0].records] != [1]:
        raise D1ProtocolError("D1 frozen trajectory dynamic carrier is not exactly EID 1")
    partial_relative = partials[0].relative_to(root).as_posix()
    observation = RetainedSideStoreEIDObservation(
        "trajectory_evidence",
        RetainedSideStoreEIDObservationState.COMPLETE_PRESENT_WITH_EIDS,
        (RetainedSideStoreEIDReference("trajectory_evidence", legacy_source_namespace_id, 1),),
    )
    return D1RetainedSideStoreObservationEvidence(
        "trajectory_evidence",
        observation,
        tuple(
            _locator(root, relative)
            for relative in (
                f"{private}/nodes.jsonl",
                f"{private}/memory_events.jsonl",
                f"{trajectory}/entity_genesis.jsonl",
                f"{trajectory}/boundaries.jsonl",
                partial_relative,
                f"workspaces/{workspace_id}/domains/{domain_id}/shared/trajectories/v2/boundaries.jsonl",
            )
        ),
    )


def observe_frozen_d1_core_retained_side_stores(
    *,
    root: str | Path,
    workspace_id: str,
    agent_id: str,
    domain_id: str,
    legacy_source_namespace_id: UUID,
    expected_l0_fingerprint_sha256: str = CORE_CHARACTER_FREE_L0_FINGERPRINT,
) -> D1CoreSideStoreObservationArtifact:
    """Return only the pre-established D1 core side-store witness.

    It deliberately contains no generic filesystem discovery or integer scan.
    The L0 recursive baseline manifest is first reverified, after which each
    evidence item is checked via its known owning structure.
    """
    if not isinstance(legacy_source_namespace_id, UUID):
        raise D1ProtocolError("D1 retained-side-store observation requires a source namespace UUID")
    if not all(isinstance(value, str) and value for value in (workspace_id, agent_id, domain_id)):
        raise D1ProtocolError("D1 retained-side-store observation requires workspace, agent, and domain")
    baseline = fingerprint_legacy_baseline(
        root=root,
        workspace_id=workspace_id,
        agent_id=agent_id,
        domain_id=domain_id,
        character_seed_required=False,
    )
    if baseline.digest != expected_l0_fingerprint_sha256:
        raise D1ProtocolError("D1 core L0 fingerprint differs from the frozen retained-side-store witness")
    base = Path(root).resolve()
    workspace = f"workspaces/{workspace_id}"
    agent = f"{workspace}/agents/{agent_id}"
    domain = f"{workspace}/domains/{domain_id}"
    evidence = (
        _require_absent_store(base, "conflicts", (f"{domain}/conflicts/events.jsonl",)),
        _require_absent_store(base, "anchors", (f"{agent}/anchors.json",)),
        _require_absent_store(base, "affect_history", (f"{agent}/affect_state.json",)),
        _require_absent_store(base, "character_store", (f"{agent}/character_state.json", f"{workspace}/seeds")),
        _require_absent_store(base, "hivemind_collective", (f"{workspace}/collective/packets/events.jsonl",)),
        _require_absent_store(base, "bridges", (f"{workspace}/bridges.json",)),
        _require_private_eid_one(
            base,
            workspace_id=workspace_id,
            agent_id=agent_id,
            domain_id=domain_id,
            legacy_source_namespace_id=legacy_source_namespace_id,
        ),
        _require_absent_store(base, "deep_memory", (f"{agent}/deep_memory/memories.jsonl",)),
    )
    observations = tuple(item.observation for item in evidence)
    return D1CoreSideStoreObservationArtifact(
        baseline.digest,
        workspace_id,
        agent_id,
        domain_id,
        legacy_source_namespace_id,
        observations,
        evidence,
    )


def verify_frozen_d1_core_retained_side_stores(
    *, root: str | Path, workspace_id: str, agent_id: str, domain_id: str,
) -> D1CoreSideStoreObservationArtifact:
    """Verify the one already-qualified core witness; never choose a replacement."""
    artifact = observe_frozen_d1_core_retained_side_stores(
        root=root,
        workspace_id=workspace_id,
        agent_id=agent_id,
        domain_id=domain_id,
        legacy_source_namespace_id=CORE_SIDE_STORE_OBSERVATION_SOURCE_NAMESPACE_ID,
    )
    if artifact.digest != CORE_SIDE_STORE_OBSERVATION_DIGEST:
        raise D1ProtocolError("D1 core side-store observation differs from the immutable qualified witness")
    return artifact


__all__ = [
    "CORE_CHARACTER_FREE_L0_FINGERPRINT",
    "CORE_SIDE_STORE_OBSERVATION_DIGEST",
    "CORE_SIDE_STORE_OBSERVATION_SOURCE_NAMESPACE_ID",
    "D1CoreSideStoreObservationArtifact",
    "D1ObservationLocator",
    "D1ObservationLocatorState",
    "D1RetainedSideStoreObservationEvidence",
    "observe_frozen_d1_core_retained_side_stores",
    "verify_frozen_d1_core_retained_side_stores",
]
